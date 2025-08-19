"""Article management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File, Form
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.article import ArticleRepository
from src.services.article import ArticleService
from src.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleListResponse,
    ArticleSummary,
    ArticleFilterParams,
    ArticlePublish,
    CategoryListResponse
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import get_current_active_user, admin_required
from src.utils.direct_file_upload import (
    DirectFileUploader,
    get_article_multipart,
    get_article_multipart_update,
    process_image_upload,
    merge_data_with_image_url
)

router = APIRouter()


async def get_article_service(session: AsyncSession = Depends(get_db)) -> ArticleService:
    """Get article service dependency."""
    article_repo = ArticleRepository(session)
    return ArticleService(article_repo)


@router.post("/", response_model=ArticleResponse, summary="Create a new article")
async def create_article(
    form_data: Tuple[Dict[str, Any], UploadFile] = Depends(get_article_multipart()),
    current_user: dict = Depends(get_current_active_user),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Create a new article with multipart form data.
    
    Requires authentication. All users can create articles.
    
    **Form Data:**
    - data: JSON string containing article data
    - image: Image file for article (required)
    
    **JSON Data Fields:**
    - title: Article title (required)
    - description: Full article content (required)  
    - slug: URL-friendly slug (required)
    - excerpt: Short summary (optional)
    - category: Article category (required)
    - is_published: Publication status (optional, default: false)
    - published_at: Publication date (optional)
    """
    json_data, image = form_data
    
    # Handle image upload (required)
    uploader = DirectFileUploader()
    image_url = await uploader.upload_file(image, "articles")
    
    # Merge image URL with JSON data
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Create article data object
    article_data = ArticleCreate(**complete_data)
    
    return await article_service.create_article(article_data, current_user["id"])


@router.get("/", response_model=ArticleListResponse, summary="Get articles with filters")
async def get_articles(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title, description, or category"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_published: Optional[bool] = Query(None, description="Filter by publication status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get articles with filters and pagination.
    
    Public endpoint - no authentication required.
    """
    filters = ArticleFilterParams(
        page=page,
        size=size,
        search=search,
        category=category,
        is_published=is_published,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await article_service.get_articles(filters)


@router.get("/published", response_model=List[ArticleResponse], summary="Get published articles")
async def get_published_articles(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get published articles only.
    
    Public endpoint - no authentication required.
    """
    return await article_service.get_published_articles(limit)


@router.get("/drafts", response_model=List[ArticleResponse], summary="Get draft articles")
async def get_draft_articles(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    current_user: dict = Depends(get_current_active_user),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get draft articles only.
    
    Requires authentication.
    """
    return await article_service.get_draft_articles(limit)


@router.get("/categories", response_model=CategoryListResponse, summary="Get all article categories")
async def get_categories(
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get all unique article categories.
    
    Public endpoint - no authentication required.
    """
    return await article_service.get_categories()


@router.get("/categories/{category}", response_model=List[ArticleResponse], summary="Get articles by category")
async def get_articles_by_category(
    category: str,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    published_only: bool = Query(True, description="Only return published articles"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get articles by category.
    
    Public endpoint - no authentication required.
    """
    return await article_service.get_articles_by_category(category, limit, published_only)


@router.get("/latest", response_model=List[ArticleResponse], summary="Get latest articles")
async def get_latest_articles(
    limit: int = Query(5, ge=1, le=50, description="Number of latest articles"),
    published_only: bool = Query(True, description="Only return published articles"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get latest articles.
    
    Public endpoint - no authentication required.
    """
    return await article_service.get_latest_articles(limit, published_only)


@router.get("/search", response_model=List[ArticleResponse], summary="Search articles")
async def search_articles(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    published_only: bool = Query(True, description="Only return published articles"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Search articles by title, description, or category.
    
    Public endpoint - no authentication required.
    """
    return await article_service.search_articles(q, published_only, limit)


@router.get("/statistics", summary="Get article statistics")
async def get_article_statistics(
    current_user: dict = Depends(admin_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get article statistics.
    
    Requires admin role.
    """
    return await article_service.get_article_statistics()


@router.get("/summaries", response_model=List[ArticleSummary], summary="Get article summaries")
async def get_article_summaries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_published: Optional[bool] = Query(None, description="Filter by publication status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get article summaries (lighter response).
    
    Public endpoint - no authentication required.
    """
    filters = ArticleFilterParams(
        page=page,
        size=size,
        search=search,
        category=category,
        is_published=is_published,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await article_service.get_article_summaries(filters)


@router.get("/{article_id}", response_model=ArticleResponse, summary="Get article by ID")
async def get_article(
    article_id: int,
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get article by ID.
    
    Public endpoint - no authentication required.
    """
    return await article_service.get_article(article_id)


@router.get("/slug/{slug}", response_model=ArticleResponse, summary="Get article by slug")
async def get_article_by_slug(
    slug: str,
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get article by slug.
    
    Public endpoint - no authentication required.
    """
    return await article_service.get_article_by_slug(slug)


@router.put("/{article_id}", response_model=ArticleResponse, summary="Update article")
async def update_article(
    article_id: int,
    form_data: Tuple[Dict[str, Any], Optional[UploadFile]] = Depends(get_article_multipart_update()),
    current_user: dict = Depends(get_current_active_user),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Update article with multipart form data.
    
    Requires authentication. Users can only update their own articles unless they are admin.
    
    **Form Data:**
    - data: JSON string containing article update data
    - image: New image file for article (optional for updates)
    
    **JSON Data Fields (all optional):**
    - title: Article title
    - description: Full article content
    - slug: URL-friendly slug
    - excerpt: Short summary
    - category: Article category
    - is_published: Publication status
    - published_at: Publication date
    """
    json_data, image = form_data
    
    # Handle image upload if provided
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "articles", uploader)
    
    # Merge image URL with JSON data
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Create article update data object
    article_data = ArticleUpdate(**complete_data)
    
    return await article_service.update_article(article_id, article_data, current_user["id"])


@router.delete("/{article_id}", response_model=MessageResponse, summary="Delete article")
async def delete_article(
    article_id: int,
    current_user: dict = Depends(get_current_active_user),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Delete article (soft delete).
    
    Requires authentication. Users can only delete their own articles unless they are admin.
    """
    return await article_service.delete_article(article_id, current_user["id"])


@router.post("/{article_id}/publish", response_model=ArticleResponse, summary="Publish/unpublish article")
async def publish_article(
    article_id: int,
    publish_data: ArticlePublish,
    current_user: dict = Depends(get_current_active_user),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Publish or unpublish an article.
    
    Requires authentication.
    """
    return await article_service.publish_article(article_id, publish_data)


@router.post("/{article_id}/duplicate", response_model=ArticleResponse, summary="Duplicate article")
async def duplicate_article(
    article_id: int,
    new_title: Optional[str] = Body(None, description="New title for duplicate"),
    new_slug: Optional[str] = Body(None, description="New slug for duplicate"),
    current_user: dict = Depends(get_current_active_user),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Duplicate an existing article.
    
    Creates a copy of the article as a draft.
    """
    return await article_service.duplicate_article(article_id, new_title, new_slug, current_user["id"])


@router.post("/bulk/publish", response_model=MessageResponse, summary="Bulk publish articles")
async def bulk_publish_articles(
    article_ids: List[int] = Body(..., description="List of article IDs to publish"),
    is_published: bool = Body(True, description="Publication status"),
    current_user: dict = Depends(admin_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Bulk publish or unpublish articles.
    
    Requires admin role.
    """
    return await article_service.bulk_publish(article_ids, is_published)


@router.post("/bulk/delete", response_model=MessageResponse, summary="Bulk delete articles")
async def bulk_delete_articles(
    article_ids: List[int] = Body(..., description="List of article IDs to delete"),
    current_user: dict = Depends(admin_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Bulk delete articles.
    
    Requires admin role.
    """
    return await article_service.bulk_delete(article_ids, current_user["id"])