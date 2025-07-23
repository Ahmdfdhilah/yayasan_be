"""Article service for business logic."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from src.repositories.article import ArticleRepository
from src.schemas.article import (
    ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListResponse,
    ArticleSummary, ArticleFilterParams, ArticlePublish, CategoryListResponse
)
from src.schemas.shared import MessageResponse
from src.utils.messages import get_message


class ArticleService:
    """Article service for business logic."""
    
    def __init__(self, article_repo: ArticleRepository):
        self.article_repo = article_repo
    
    async def create_article(self, article_data: ArticleCreate, created_by: Optional[int] = None) -> ArticleResponse:
        """Create a new article."""
        # Validate slug uniqueness
        if await self.article_repo.slug_exists(article_data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Article with this slug already exists"
            )
        
        # Create article in database
        article = await self.article_repo.create(article_data, created_by)
        
        return ArticleResponse.from_article_model(article)
    
    async def get_article(self, article_id: int) -> ArticleResponse:
        """Get article by ID."""
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        return ArticleResponse.from_article_model(article)
    
    async def get_article_by_slug(self, slug: str) -> ArticleResponse:
        """Get article by slug."""
        article = await self.article_repo.get_by_slug(slug)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        return ArticleResponse.from_article_model(article)
    
    async def update_article(self, article_id: int, article_data: ArticleUpdate, updated_by: Optional[int] = None) -> ArticleResponse:
        """Update article information."""
        # Check if article exists
        existing_article = await self.article_repo.get_by_id(article_id)
        if not existing_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Validate slug uniqueness if being updated
        if article_data.slug and await self.article_repo.slug_exists(article_data.slug, exclude_article_id=article_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Article with this slug already exists"
            )
        
        # Update article in database
        updated_article = await self.article_repo.update(article_id, article_data, updated_by)
        if not updated_article:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update article"
            )
        
        return ArticleResponse.from_article_model(updated_article)
    
    async def delete_article(self, article_id: int, deleted_by: Optional[int] = None) -> MessageResponse:
        """Delete article (soft delete)."""
        # Check if article exists
        existing_article = await self.article_repo.get_by_id(article_id)
        if not existing_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Soft delete article
        success = await self.article_repo.soft_delete(article_id, deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete article"
            )
        
        return MessageResponse(message="Article deleted successfully")
    
    async def get_articles(self, filters: ArticleFilterParams) -> ArticleListResponse:
        """Get articles with filters and pagination."""
        articles, total = await self.article_repo.get_all_filtered(filters)
        
        article_responses = [ArticleResponse.from_article_model(article) for article in articles]
        
        return ArticleListResponse(
            items=article_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size
        )
    
    async def get_published_articles(self, limit: Optional[int] = None) -> List[ArticleResponse]:
        """Get published articles only."""
        articles = await self.article_repo.get_published_articles(limit)
        return [ArticleResponse.from_article_model(article) for article in articles]
    
    async def get_draft_articles(self, limit: Optional[int] = None) -> List[ArticleResponse]:
        """Get draft articles only."""
        articles = await self.article_repo.get_draft_articles(limit)
        return [ArticleResponse.from_article_model(article) for article in articles]
    
    async def get_articles_by_category(self, category: str, limit: Optional[int] = None, published_only: bool = True) -> List[ArticleResponse]:
        """Get articles by category."""
        articles = await self.article_repo.get_articles_by_category(category, limit, published_only)
        return [ArticleResponse.from_article_model(article) for article in articles]
    
    async def publish_article(self, article_id: int, publish_data: ArticlePublish) -> ArticleResponse:
        """Publish or unpublish an article."""
        # Check if article exists
        existing_article = await self.article_repo.get_by_id(article_id)
        if not existing_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        if publish_data.is_published:
            # Publish article
            article = await self.article_repo.publish_article(article_id, publish_data.published_at)
        else:
            # Unpublish article
            article = await self.article_repo.unpublish_article(article_id)
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update article publication status"
            )
        
        return ArticleResponse.from_article_model(article)
    
    async def get_categories(self) -> CategoryListResponse:
        """Get all unique categories."""
        categories = await self.article_repo.get_categories()
        return CategoryListResponse(
            categories=categories,
            total=len(categories)
        )
    
    async def get_article_statistics(self) -> Dict[str, Any]:
        """Get article statistics."""
        return await self.article_repo.get_article_statistics()
    
    async def get_latest_articles(self, limit: int = 5, published_only: bool = True) -> List[ArticleResponse]:
        """Get latest articles."""
        articles = await self.article_repo.get_latest_articles(limit, published_only)
        return [ArticleResponse.from_article_model(article) for article in articles]
    
    async def search_articles(self, search_term: str, published_only: bool = True, limit: Optional[int] = None) -> List[ArticleResponse]:
        """Search articles by title, description, or category."""
        articles = await self.article_repo.search_articles(search_term, published_only, limit)
        return [ArticleResponse.from_article_model(article) for article in articles]
    
    async def get_article_summaries(self, filters: ArticleFilterParams) -> List[ArticleSummary]:
        """Get article summaries (lighter response)."""
        articles, _ = await self.article_repo.get_all_filtered(filters)
        return [ArticleSummary.from_article_model(article) for article in articles]
    
    async def duplicate_article(self, article_id: int, new_title: Optional[str] = None, new_slug: Optional[str] = None, created_by: Optional[int] = None) -> ArticleResponse:
        """Duplicate an existing article."""
        # Get original article
        original_article = await self.article_repo.get_by_id(article_id)
        if not original_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Prepare duplicate data
        title = new_title or f"{original_article.title} (Copy)"
        slug = new_slug or f"{original_article.slug}-copy"
        
        # Ensure slug is unique
        counter = 1
        base_slug = slug
        while await self.article_repo.slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create duplicate article data
        article_data = ArticleCreate(
            title=title,
            description=original_article.description,
            slug=slug,
            excerpt=original_article.excerpt,
            img_url=original_article.img_url,
            category=original_article.category,
            is_published=False,  # Duplicates start as drafts
            published_at=None
        )
        
        # Create duplicate
        duplicate_article = await self.article_repo.create(article_data, created_by)
        return ArticleResponse.from_article_model(duplicate_article)
    
    async def bulk_publish(self, article_ids: List[int], is_published: bool = True) -> MessageResponse:
        """Bulk publish/unpublish articles."""
        success_count = 0
        
        for article_id in article_ids:
            try:
                if is_published:
                    article = await self.article_repo.publish_article(article_id)
                else:
                    article = await self.article_repo.unpublish_article(article_id)
                
                if article:
                    success_count += 1
            except Exception:
                # Continue with other articles even if one fails
                continue
        
        if success_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No articles were updated"
            )
        
        action = "published" if is_published else "unpublished"
        return MessageResponse(
            message=f"{success_count} article(s) {action} successfully"
        )
    
    async def bulk_delete(self, article_ids: List[int], deleted_by: Optional[int] = None) -> MessageResponse:
        """Bulk delete articles."""
        success_count = 0
        
        for article_id in article_ids:
            try:
                success = await self.article_repo.soft_delete(article_id, deleted_by)
                if success:
                    success_count += 1
            except Exception:
                # Continue with other articles even if one fails
                continue
        
        if success_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No articles were deleted"
            )
        
        return MessageResponse(
            message=f"{success_count} article(s) deleted successfully"
        )