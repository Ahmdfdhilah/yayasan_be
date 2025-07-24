"""Gallery management endpoints with advanced ordering."""

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
    
    Requires admin role. If display_order is specified and position is occupied,
    existing items will be shifted down automatically.
    
    **Form Data:**
    - data: JSON string containing gallery item data
    - image: Image file for gallery (required)
    
    **JSON Data Fields:**
    - title: Image title (required)
    - excerpt: Short description (optional)
    - display_order: Display order (optional, default: 0)
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
    sort_by: str = Query("display_order", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
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
    Get all gallery items, ordered by display_order.
    
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
    Get gallery statistics including order conflicts.
    
    Requires admin role.
    """
    return await gallery_service.get_gallery_statistics()




@router.get("/summaries", response_model=List[GallerySummary], summary="Get gallery summaries")
async def get_gallery_summaries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: str = Query("display_order", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
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
    
    Requires admin role. If display_order is changed, positions will be automatically adjusted.
    
    **Form Data:**
    - data: JSON string containing gallery update data
    - image: New image file for gallery (optional for updates)
    
    **JSON Data Fields (all optional):**
    - title: Image title
    - excerpt: Short description
    - display_order: Display order
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
    
    Requires admin role. Items after deleted item will be shifted up to close gaps.
    """
    return await gallery_service.delete_gallery(gallery_id, current_user["id"])




# ===== ORDERING ENDPOINT =====

@router.patch("/{gallery_id}/order", response_model=GalleryResponse, summary="Update gallery display order")
async def update_gallery_order(
    gallery_id: int,
    new_order: int = Body(..., ge=0, description="New display order"),
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Update display order for a gallery item.
    
    Requires admin role. Other items will be automatically repositioned to accommodate the change.
    """
    return await gallery_service.update_single_order(gallery_id, new_order, current_user["id"])