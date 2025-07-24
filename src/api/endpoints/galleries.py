"""Gallery management endpoints with advanced ordering."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional
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
    GalleryFilterParams,
    GalleryBulkOrderUpdate,
    BulkOrderUpdateResponse
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import get_current_active_user, require_roles

router = APIRouter()

# Dependency for admin-only endpoints
admin_required = require_roles(["admin"])


async def get_gallery_service(session: AsyncSession = Depends(get_db)) -> GalleryService:
    """Get gallery service dependency."""
    gallery_repo = GalleryRepository(session)
    return GalleryService(gallery_repo)


@router.post("/", response_model=GalleryResponse, summary="Create a new gallery item")
async def create_gallery(
    gallery_data: GalleryCreate,
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Create a new gallery item.
    
    Requires admin role. If display_order is specified and position is occupied,
    existing items will be shifted down automatically.
    """
    return await gallery_service.create_gallery(gallery_data, current_user["id"])


@router.get("/", response_model=GalleryListResponse, summary="Get galleries with filters")
async def get_galleries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
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
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await gallery_service.get_galleries(filters)


@router.get("/active", response_model=List[GalleryResponse], summary="Get active galleries")
async def get_active_galleries(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get active gallery items only, ordered by display_order.
    
    Public endpoint - no authentication required.
    """
    return await gallery_service.get_active_galleries(limit)


@router.get("/search", response_model=List[GalleryResponse], summary="Search galleries")
async def search_galleries(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    active_only: bool = Query(True, description="Only return active items"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Search gallery items by title.
    
    Public endpoint - no authentication required.
    """
    return await gallery_service.search_galleries(q, active_only, limit)


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


@router.get("/order-conflicts", summary="Get gallery order conflicts")
async def get_order_conflicts(
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get gallery items that have conflicting display orders.
    
    Requires admin role.
    """
    return await gallery_service.get_order_conflicts()


@router.get("/summaries", response_model=List[GallerySummary], summary="Get gallery summaries")
async def get_gallery_summaries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
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
        is_active=is_active,
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
    gallery_data: GalleryUpdate,
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Update gallery item.
    
    Requires admin role. If display_order is changed, positions will be automatically adjusted.
    """
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


@router.patch("/{gallery_id}/toggle-active", response_model=GalleryResponse, summary="Toggle gallery active status")
async def toggle_active_status(
    gallery_id: int,
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Toggle active status of a gallery item.
    
    Requires admin role.
    """
    return await gallery_service.toggle_active_status(gallery_id, current_user["id"])


# ===== ORDERING ENDPOINTS =====

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


@router.post("/bulk-order", response_model=BulkOrderUpdateResponse, summary="Bulk update gallery orders")
async def bulk_update_gallery_order(
    bulk_order_data: GalleryBulkOrderUpdate,
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Bulk update display orders for multiple gallery items.
    
    Requires admin role. Allows you to reorder multiple items in a single operation.
    
    Example request body:
    ```json
    {
        "items": [
            {"gallery_id": 1, "new_order": 3},
            {"gallery_id": 2, "new_order": 1},
            {"gallery_id": 3, "new_order": 2}
        ]
    }
    ```
    """
    return await gallery_service.bulk_update_order(bulk_order_data, current_user["id"])


@router.post("/normalize-orders", response_model=MessageResponse, summary="Normalize gallery orders")
async def normalize_gallery_orders(
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Normalize all gallery display orders to remove gaps (1, 2, 3, ...).
    
    Requires admin role. Useful for cleaning up order conflicts or gaps in numbering.
    """
    return await gallery_service.normalize_gallery_orders()


# ===== UTILITY ENDPOINTS =====

@router.get("/export/ordered", response_model=List[GalleryResponse], summary="Export all galleries in order")
async def export_galleries_ordered(
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Export all active gallery items ordered by display_order.
    
    Requires admin role. Useful for backup or migration purposes.
    """
    return await gallery_service.get_active_galleries()


@router.post("/move-up/{gallery_id}", response_model=GalleryResponse, summary="Move gallery up one position")
async def move_gallery_up(
    gallery_id: int,
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Move gallery item up one position in display order.
    
    Requires admin role. Convenient shortcut for single-step reordering.
    """
    gallery = await gallery_service.get_gallery(gallery_id)
    new_order = max(1, gallery.display_order - 1)
    return await gallery_service.update_single_order(gallery_id, new_order, current_user["id"])


@router.post("/move-down/{gallery_id}", response_model=GalleryResponse, summary="Move gallery down one position")
async def move_gallery_down(
    gallery_id: int,
    current_user: dict = Depends(admin_required),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Move gallery item down one position in display order.
    
    Requires admin role. Convenient shortcut for single-step reordering.
    """
    gallery = await gallery_service.get_gallery(gallery_id)
    new_order = gallery.display_order + 1
    return await gallery_service.update_single_order(gallery_id, new_order, current_user["id"])