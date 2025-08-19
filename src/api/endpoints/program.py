"""Program endpoints for educational programs management."""

from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.program import ProgramRepository
from src.services.program import ProgramService
from src.schemas.program import ProgramCreate, ProgramUpdate, ProgramResponse, ProgramListResponse, ProgramFilterParams
from src.schemas.shared import MessageResponse
from src.auth.permissions import admin_required
from src.utils.direct_file_upload import (
    DirectFileUploader,
    get_program_multipart,
    get_program_multipart_update,
    process_image_upload,
    merge_data_with_image_url
)

router = APIRouter()


# ===== DEPENDENCIES =====

async def get_program_service(session: AsyncSession = Depends(get_db)) -> ProgramService:
    """Get program service dependency."""
    program_repo = ProgramRepository(session)
    return ProgramService(program_repo)


# ===== PROGRAM ENDPOINTS =====

@router.post("", response_model=ProgramResponse)
async def create_program(
    form_data: Tuple[Dict[str, Any], Optional[Any]] = Depends(get_program_multipart()),
    current_user: dict = Depends(admin_required),
    program_service: ProgramService = Depends(get_program_service)
):
    """Create a new program."""
    json_data, image = form_data
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "programs", uploader)
    complete_data = merge_data_with_image_url(json_data, image_url)
    program_data = ProgramCreate(**complete_data)
    return await program_service.create_program(program_data)


@router.get("", response_model=ProgramListResponse)
async def get_programs(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Search term"),
    program_service: ProgramService = Depends(get_program_service)
):
    """Get all programs with pagination and search."""
    filters = ProgramFilterParams(skip=skip, limit=limit, search=search)
    return await program_service.get_all_programs(filters)


@router.get("/{program_id}", response_model=ProgramResponse)
async def get_program(
    program_id: int,
    program_service: ProgramService = Depends(get_program_service)
):
    """Get program by ID."""
    return await program_service.get_program(program_id)


@router.put("/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: int,
    form_data: Tuple[Dict[str, Any], Optional[Any]] = Depends(get_program_multipart_update()),
    current_user: dict = Depends(admin_required),
    program_service: ProgramService = Depends(get_program_service)
):
    """Update program."""
    json_data, image = form_data
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "programs", uploader)
    complete_data = merge_data_with_image_url(json_data, image_url)
    update_data = ProgramUpdate(**complete_data)
    return await program_service.update_program(program_id, update_data)


@router.delete("/{program_id}", response_model=MessageResponse)
async def delete_program(
    program_id: int,
    current_user: dict = Depends(admin_required),
    program_service: ProgramService = Depends(get_program_service)
):
    """Delete program."""
    return await program_service.delete_program(program_id)