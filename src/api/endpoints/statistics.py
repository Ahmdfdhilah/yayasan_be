"""Statistics API endpoints."""

from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.statistic import StatisticService
from src.schemas.statistic import (
    StatisticCreate,
    StatisticUpdate, 
    StatisticResponse,
    StatisticListResponse,
    StatisticFilterParams
)
from src.auth import get_current_user
from src.models.user import User
from src.utils.direct_file_upload import (
    DirectFileUploader,
    get_statistic_multipart,
    get_statistic_multipart_update,
    process_image_upload,
    merge_data_with_image_url
)

router = APIRouter()


def get_statistic_service(session: AsyncSession = Depends(get_db)) -> StatisticService:
    """Get statistic service dependency."""
    return StatisticService(session)


@router.post("/", response_model=StatisticResponse, status_code=status.HTTP_201_CREATED)
async def create_statistic(
    form_data: Tuple[Dict[str, Any], Optional[UploadFile]] = Depends(get_statistic_multipart()),
    current_user: User = Depends(get_current_user),
    statistic_service: StatisticService = Depends(get_statistic_service)
):
    """Create a new statistic with multipart form data.
    
    Requires authentication. Auto-handles display_order shifting.
    
    **Form Data:**
    - data: JSON string containing statistic data
    - image: Icon image file for statistic (optional)
    
    **JSON Data Fields:**
    - title: Statistic title (required)
    - description: Statistic description (optional)
    - stats: Statistics value with suffix like "20%", "1,250", "50km" (required)
    - display_order: Display order for sorting (optional, auto-assigned if not provided)
    """
    json_data, image = form_data
    
    # Handle image upload if provided
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "statistics", uploader)
    
    # Merge image URL with JSON data
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Create statistic data object
    statistic_data = StatisticCreate(**complete_data)
    
    return await statistic_service.create_statistic(statistic_data)


@router.get("/", response_model=StatisticListResponse)
async def get_statistics(
    search: str = Query(None, description="Search term for title, description, or stats"),
    sort_by: str = Query("display_order", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    statistic_service: StatisticService = Depends(get_statistic_service)
):
    """Get statistics with filters and pagination.
    
    Public endpoint - no authentication required.
    """
    filters = StatisticFilterParams(
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size
    )
    return await statistic_service.get_statistics(filters)




@router.get("/{statistic_id}", response_model=StatisticResponse)
async def get_statistic(
    statistic_id: int,
    statistic_service: StatisticService = Depends(get_statistic_service)
):
    """Get a specific statistic by ID.
    
    Public endpoint - no authentication required.
    """
    return await statistic_service.get_statistic(statistic_id)


@router.put("/{statistic_id}", response_model=StatisticResponse)
async def update_statistic(
    statistic_id: int,
    form_data: Tuple[Dict[str, Any], Optional[UploadFile]] = Depends(get_statistic_multipart_update()),
    current_user: User = Depends(get_current_user),
    statistic_service: StatisticService = Depends(get_statistic_service)
):
    """Update a statistic with multipart form data.
    
    Requires authentication. Auto-handles display_order shifting if changed.
    
    **Form Data:**
    - data: JSON string containing statistic update data
    - image: New icon image file for statistic (optional)
    
    **JSON Data Fields (all optional):**
    - title: Statistic title
    - description: Statistic description
    - stats: Statistics value with suffix like "20%", "1,250", "50km"
    - display_order: Display order for sorting (triggers auto-shift if changed)
    """
    json_data, image = form_data
    
    # Handle image upload if provided
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "statistics", uploader)
    
    # Merge image URL with JSON data
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Create statistic update data object
    update_data = StatisticUpdate(**complete_data)
    
    return await statistic_service.update_statistic(statistic_id, update_data)


@router.delete("/{statistic_id}")
async def delete_statistic(
    statistic_id: int,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    current_user: User = Depends(get_current_user),
    statistic_service: StatisticService = Depends(get_statistic_service)
):
    """Delete a statistic.
    
    Requires authentication. 
    - Soft delete by default (sets deleted_at)
    - Use hard_delete=true for permanent deletion
    Auto-handles display_order shifting for remaining statistics.
    """
    return await statistic_service.delete_statistic(statistic_id, hard_delete)


