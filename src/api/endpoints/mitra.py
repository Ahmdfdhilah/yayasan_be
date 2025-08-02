"""Mitra endpoints for partnership management."""

from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.mitra import MitraRepository
from src.services.mitra import MitraService
from src.schemas.mitra import MitraCreate, MitraUpdate, MitraResponse, MitraListResponse, MitraFilterParams
from src.schemas.shared import MessageResponse
from src.auth.permissions import require_roles
from src.utils.direct_file_upload import (
    DirectFileUploader,
    get_mitra_multipart,
    get_mitra_multipart_update,
    process_image_upload,
    merge_data_with_image_url
)

router = APIRouter()
admin_required = require_roles(["admin"])


# ===== DEPENDENCIES =====

async def get_mitra_service(session: AsyncSession = Depends(get_db)) -> MitraService:
    """Get mitra service dependency."""
    mitra_repo = MitraRepository(session)
    return MitraService(mitra_repo)


# ===== MITRA ENDPOINTS =====

@router.post("", response_model=MitraResponse)
async def create_mitra(
    form_data: Tuple[Dict[str, Any], Optional[Any]] = Depends(get_mitra_multipart()),
    current_user: dict = Depends(admin_required),
    mitra_service: MitraService = Depends(get_mitra_service)
):
    """Create a new mitra."""
    json_data, image = form_data
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "mitra", uploader)
    complete_data = merge_data_with_image_url(json_data, image_url)
    mitra_data = MitraCreate(**complete_data)
    return await mitra_service.create_mitra(mitra_data)


@router.get("", response_model=MitraListResponse)
async def get_mitras(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Search term"),
    mitra_service: MitraService = Depends(get_mitra_service)
):
    """Get all mitras with pagination and search."""
    filters = MitraFilterParams(skip=skip, limit=limit, search=search)
    return await mitra_service.get_all_mitras(filters)


@router.get("/{mitra_id}", response_model=MitraResponse)
async def get_mitra(
    mitra_id: int,
    mitra_service: MitraService = Depends(get_mitra_service)
):
    """Get mitra by ID."""
    return await mitra_service.get_mitra(mitra_id)


@router.put("/{mitra_id}", response_model=MitraResponse)
async def update_mitra(
    mitra_id: int,
    form_data: Tuple[Dict[str, Any], Optional[Any]] = Depends(get_mitra_multipart_update()),
    current_user: dict = Depends(admin_required),
    mitra_service: MitraService = Depends(get_mitra_service)
):
    """Update mitra."""
    json_data, image = form_data
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "mitra", uploader)
    complete_data = merge_data_with_image_url(json_data, image_url)
    update_data = MitraUpdate(**complete_data)
    return await mitra_service.update_mitra(mitra_id, update_data)


@router.delete("/{mitra_id}", response_model=MessageResponse)
async def delete_mitra(
    mitra_id: int,
    current_user: dict = Depends(admin_required),
    mitra_service: MitraService = Depends(get_mitra_service)
):
    """Delete mitra."""
    return await mitra_service.delete_mitra(mitra_id)