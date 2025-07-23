"""Article repository for CRUD operations."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.article import Article
from src.schemas.article import ArticleCreate, ArticleUpdate, ArticleFilterParams


class ArticleRepository:
    """Article repository for CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, article_data: ArticleCreate, created_by: Optional[int] = None) -> Article:
        """Create a new article."""
        article = Article(
            title=article_data.title,
            description=article_data.description,
            slug=article_data.slug,
            excerpt=article_data.excerpt,
            img_url=article_data.img_url,
            category=article_data.category,
            is_published=article_data.is_published,
            published_at=article_data.published_at,
            created_by=created_by
        )
        
        # Auto-set published_at if is_published is True and published_at is None
        if article.is_published and article.published_at is None:
            article.published_at = datetime.utcnow()
        
        self.session.add(article)
        await self.session.commit()
        await self.session.refresh(article)
        return article
    
    async def get_by_id(self, article_id: int) -> Optional[Article]:
        """Get article by ID."""
        query = select(Article).where(
            and_(Article.id == article_id, Article.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Optional[Article]:
        """Get article by slug."""
        query = select(Article).where(
            and_(Article.slug == slug, Article.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, article_id: int, article_data: ArticleUpdate, updated_by: Optional[int] = None) -> Optional[Article]:
        """Update article information."""
        article = await self.get_by_id(article_id)
        if not article:
            return None
        
        # Update fields
        update_data = article_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(article, key, value)
        
        # Auto-set published_at if is_published is being set to True
        if article_data.is_published is True and article.published_at is None:
            article.published_at = datetime.utcnow()
        elif article_data.is_published is False:
            article.published_at = None
        
        article.updated_at = datetime.utcnow()
        article.updated_by = updated_by
        
        await self.session.commit()
        await self.session.refresh(article)
        return article
    
    async def soft_delete(self, article_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete article."""
        query = (
            update(Article)
            .where(Article.id == article_id)
            .values(
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def hard_delete(self, article_id: int) -> bool:
        """Permanently delete article."""
        query = delete(Article).where(Article.id == article_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def slug_exists(self, slug: str, exclude_article_id: Optional[int] = None) -> bool:
        """Check if slug already exists."""
        query = select(Article).where(
            and_(
                Article.slug == slug,
                Article.deleted_at.is_(None)
            )
        )
        
        if exclude_article_id:
            query = query.where(Article.id != exclude_article_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    # ===== FILTERING AND LISTING =====
    
    async def get_all_filtered(self, filters: ArticleFilterParams) -> Tuple[List[Article], int]:
        """Get articles with filters and pagination."""
        # Base query
        query = select(Article).where(Article.deleted_at.is_(None))
        count_query = select(func.count(Article.id)).where(Article.deleted_at.is_(None))
        
        # Apply filters
        if filters.search:
            search_filter = or_(
                Article.title.ilike(f"%{filters.search}%"),
                Article.description.ilike(f"%{filters.search}%"),
                Article.category.ilike(f"%{filters.search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if filters.category:
            query = query.where(Article.category == filters.category)
            count_query = count_query.where(Article.category == filters.category)
        
        if filters.is_published is not None:
            query = query.where(Article.is_published == filters.is_published)
            count_query = count_query.where(Article.is_published == filters.is_published)
        
        if filters.published_after:
            query = query.where(Article.published_at >= filters.published_after)
            count_query = count_query.where(Article.published_at >= filters.published_after)
        
        if filters.published_before:
            query = query.where(Article.published_at <= filters.published_before)
            count_query = count_query.where(Article.published_at <= filters.published_before)
        
        # Apply sorting
        if filters.sort_by == "title":
            sort_column = Article.title
        elif filters.sort_by == "category":
            sort_column = Article.category
        elif filters.sort_by == "published_at":
            sort_column = Article.published_at
        elif filters.sort_by == "updated_at":
            sort_column = Article.updated_at
        else:
            sort_column = Article.created_at
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        articles = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(articles), total
    
    async def get_published_articles(self, limit: Optional[int] = None) -> List[Article]:
        """Get published articles only."""
        query = select(Article).where(
            and_(
                Article.deleted_at.is_(None),
                Article.is_published == True,
                Article.published_at.is_not(None)
            )
        ).order_by(Article.published_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_draft_articles(self, limit: Optional[int] = None) -> List[Article]:
        """Get draft articles only."""
        query = select(Article).where(
            and_(
                Article.deleted_at.is_(None),
                Article.is_published == False
            )
        ).order_by(Article.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_articles_by_category(self, category: str, limit: Optional[int] = None, published_only: bool = True) -> List[Article]:
        """Get articles by category."""
        filters = [
            Article.deleted_at.is_(None),
            Article.category == category
        ]
        
        if published_only:
            filters.extend([
                Article.is_published == True,
                Article.published_at.is_not(None)
            ])
        
        query = select(Article).where(and_(*filters)).order_by(Article.published_at.desc() if published_only else Article.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== PUBLICATION MANAGEMENT =====
    
    async def publish_article(self, article_id: int, published_at: Optional[datetime] = None) -> Optional[Article]:
        """Publish an article."""
        article = await self.get_by_id(article_id)
        if not article:
            return None
        
        article.is_published = True
        article.published_at = published_at or datetime.utcnow()
        article.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(article)
        return article
    
    async def unpublish_article(self, article_id: int) -> Optional[Article]:
        """Unpublish an article."""
        article = await self.get_by_id(article_id)
        if not article:
            return None
        
        article.is_published = False
        article.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(article)
        return article
    
    # ===== STATISTICS AND METADATA =====
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories."""
        query = (
            select(Article.category)
            .where(Article.deleted_at.is_(None))
            .distinct()
            .order_by(Article.category)
        )
        result = await self.session.execute(query)
        return [category for category in result.scalars().all() if category]
    
    async def get_article_statistics(self) -> Dict[str, Any]:
        """Get article statistics."""
        # Total articles
        total_query = select(func.count(Article.id)).where(Article.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_articles = total_result.scalar()
        
        # Published articles
        published_query = select(func.count(Article.id)).where(
            and_(
                Article.deleted_at.is_(None),
                Article.is_published == True
            )
        )
        published_result = await self.session.execute(published_query)
        published_articles = published_result.scalar()
        
        # Draft articles
        draft_articles = total_articles - published_articles
        
        # Articles by category
        category_query = (
            select(Article.category, func.count(Article.id))
            .where(Article.deleted_at.is_(None))
            .group_by(Article.category)
        )
        category_result = await self.session.execute(category_query)
        category_counts = dict(category_result.fetchall())
        
        # Recent articles (last 30 days)
        thirty_days_ago = datetime.utcnow() - datetime.timedelta(days=30)
        recent_query = select(func.count(Article.id)).where(
            and_(
                Article.deleted_at.is_(None),
                Article.created_at >= thirty_days_ago
            )
        )
        recent_result = await self.session.execute(recent_query)
        recent_articles = recent_result.scalar()
        
        return {
            "total_articles": total_articles,
            "published_articles": published_articles,
            "draft_articles": draft_articles,
            "recent_articles": recent_articles,
            "category_distribution": category_counts,
            "total_categories": len(category_counts)
        }
    
    async def get_latest_articles(self, limit: int = 5, published_only: bool = True) -> List[Article]:
        """Get latest articles."""
        filters = [Article.deleted_at.is_(None)]
        
        if published_only:
            filters.extend([
                Article.is_published == True,
                Article.published_at.is_not(None)
            ])
        
        query = select(Article).where(and_(*filters))
        
        if published_only:
            query = query.order_by(Article.published_at.desc())
        else:
            query = query.order_by(Article.created_at.desc())
        
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_articles(self, search_term: str, published_only: bool = True, limit: Optional[int] = None) -> List[Article]:
        """Search articles by title, description, or category."""
        filters = [
            Article.deleted_at.is_(None),
            or_(
                Article.title.ilike(f"%{search_term}%"),
                Article.description.ilike(f"%{search_term}%"),
                Article.category.ilike(f"%{search_term}%")
            )
        ]
        
        if published_only:
            filters.extend([
                Article.is_published == True,
                Article.published_at.is_not(None)
            ])
        
        query = select(Article).where(and_(*filters))
        
        if published_only:
            query = query.order_by(Article.published_at.desc())
        else:
            query = query.order_by(Article.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())