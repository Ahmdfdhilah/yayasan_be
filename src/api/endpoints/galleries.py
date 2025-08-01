"""Gallery management endpoints with highlight functionality."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File, Form
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.gallery import GalleryRepository
from src.services.gallery import GalleryService
from src.schemas.gallery import (
    GalleryCreate,
    GalleryUpdate,
    GalleryResponse,
    GalleryListResponse,
    GallerySummary,
    GalleryFilterParams
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import get_current_active_user, require_roles
from src.utils.direct_file_upload import (
    DirectFileUploader,
    get_gallery_multipart,
    get_article_multipart_update,
    process_image_upload,
    merge_data_with_image_url
)

router = APIRouter()

# Dependency for admin-only endpoints
admin_required = require_roles(["admin"])


async def get_gallery_service(session: AsyncSession = Depends(get_db)) -> GalleryService:
    """Get gallery service dependency."""
    gallery_repo = GalleryRepository(session)
    return GalleryService(gallery_repo)


@router.post("/", response_model=GalleryResponse, summary="Create a new gallery item")
async def create_gallery(
    form_data: Tuple[Dict[str, Any], UploadFile] = Depends(get_gallery_multipart()),
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Create a new gallery item with multipart form data.
    
    Requires admin role.
    
    **Form Data:**
    - data: JSON string containing gallery item data
    - image: Image file for gallery (required)
    
    **JSON Data Fields:**
    - title: Image title (required)
    - excerpt: Short description (optional)
    - is_highlight: Whether to highlight this gallery item (optional, default: false)
    """
    json_data, image = form_data
    
    # Handle image upload (required for gallery)
    uploader = DirectFileUploader()
    image_url = await uploader.upload_file(image, "galleries")
    
    # Merge image URL with JSON data
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Create gallery data object
    gallery_data = GalleryCreate(**complete_data)
    
    return await gallery_service.create_gallery(gallery_data, current_user["id"])


@router.get("/", response_model=GalleryListResponse, summary="Get galleries with filters")
async def get_galleries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title"),
    is_highlighted: Optional[bool] = Query(None, description="Filter by highlight status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get galleries with filters and pagination.
    
    Public endpoint - no authentication required.
    """
    filters = GalleryFilterParams(
        page=page,
        size=size,
        search=search,
        is_highlighted=is_highlighted,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await gallery_service.get_galleries(filters)


@router.get("/all", response_model=List[GalleryResponse], summary="Get all galleries")
async def get_all_galleries(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get all gallery items, ordered by highlight status then creation date.
    
    Public endpoint - no authentication required.
    """
    return await gallery_service.get_all_galleries(limit)


@router.get("/search", response_model=List[GalleryResponse], summary="Search galleries")
async def search_galleries(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Search gallery items by title.
    
    Public endpoint - no authentication required.
    """
    return await gallery_service.search_galleries(q, limit)


@router.get("/statistics", summary="Get gallery statistics")
async def get_gallery_statistics(
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get gallery statistics including highlight counts.
    
    Requires admin role.
    """
    return await gallery_service.get_gallery_statistics()




@router.get("/summaries", response_model=List[GallerySummary], summary="Get gallery summaries")
async def get_gallery_summaries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    is_highlighted: Optional[bool] = Query(None, description="Filter by highlight status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get gallery summaries (lighter response).
    
    Public endpoint - no authentication required.
    """
    filters = GalleryFilterParams(
        page=page,
        size=size,
        search=search,
        is_highlighted=is_highlighted,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await gallery_service.get_gallery_summaries(filters)


@router.get("/{gallery_id}", response_model=GalleryResponse, summary="Get gallery by ID")
async def get_gallery(
    gallery_id: int,
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get gallery item by ID.
    
    Public endpoint - no authentication required.
    """
    return await gallery_service.get_gallery(gallery_id)


@router.put("/{gallery_id}", response_model=GalleryResponse, summary="Update gallery")
async def update_gallery(
    gallery_id: int,
    form_data: Tuple[Dict[str, Any], Optional[UploadFile]] = Depends(get_article_multipart_update()),  # Use article multipart update for optional image
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Update gallery item with multipart form data.
    
    Requires admin role.
    
    **Form Data:**
    - data: JSON string containing gallery update data
    - image: New image file for gallery (optional for updates)
    
    **JSON Data Fields (all optional):**
    - title: Image title
    - excerpt: Short description
    - is_highlight: Whether to highlight this gallery item
    """
    json_data, image = form_data
    
    # Handle image upload if provided
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "galleries", uploader)
    
    # Merge image URL with JSON data
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Create gallery update data object
    gallery_data = GalleryUpdate(**complete_data)
    
    return await gallery_service.update_gallery(gallery_id, gallery_data, current_user["id"])


@router.delete("/{gallery_id}", response_model=MessageResponse, summary="Delete gallery")
async def delete_gallery(
    gallery_id: int,
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Delete gallery item (soft delete).
    
    Requires admin role.
    """
    return await gallery_service.delete_gallery(gallery_id, current_user["id"])




# ===== HIGHLIGHT ENDPOINTS =====

@router.get("/highlighted", response_model=List[GalleryResponse], summary="Get highlighted galleries")
async def get_highlighted_galleries(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get all highlighted gallery items.
    
    Public endpoint - no authentication required.
    """
    return await gallery_service.get_highlighted_galleries(limit)


@router.get("/non-highlighted", response_model=List[GalleryResponse], summary="Get non-highlighted galleries")
async def get_non_highlighted_galleries(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get all non-highlighted gallery items.
    
    Public endpoint - no authentication required.
    """
    return await gallery_service.get_non_highlighted_galleries(limit)


@router.patch("/{gallery_id}/highlight", response_model=GalleryResponse, summary="Toggle gallery highlight status")
async def toggle_gallery_highlight(
    gallery_id: int,
    is_highlight: bool = Body(..., description="Highlight status"),
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Toggle highlight status for a gallery item.
    
    Requires admin role.
    """
    gallery_data = GalleryUpdate(is_highlight=is_highlight)
    return await gallery_service.update_gallery(gallery_id, gallery_data, current_user["id"])