"""Period management endpoints for universal period system."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.period import PeriodRepository
from src.services.period import PeriodService
from src.schemas.period import (
    PeriodCreate, PeriodUpdate, PeriodResponse, PeriodWithStats,
    PeriodFilter, PeriodActivate, PeriodListResponse
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import get_current_active_user, require_roles

router = APIRouter()

# Role-based permissions
admin_required = require_roles(["admin"])
admin_or_manager = require_roles(["admin", "kepala_sekolah"])


async def get_period_service(session: AsyncSession = Depends(get_db)) -> PeriodService:
    """Get period service dependency."""
    period_repo = PeriodRepository(session)
    return PeriodService(period_repo)


@router.post("/", response_model=PeriodResponse, summary="Create new period")
async def create_period(
    period_data: PeriodCreate,
    current_user: dict = Depends(admin_or_manager),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Create a new academic/evaluation period.
    
    Only admins and kepala sekolah can create periods.
    """
    return await period_service.create_period(period_data, current_user["id"])


@router.get("/", response_model=PeriodListResponse, summary="Get periods with filters")
async def get_periods(
    filters: PeriodFilter = Depends(),
    current_user: dict = Depends(get_current_active_user),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Get periods with optional filtering and pagination.
    
    All authenticated users can view periods.
    """
    return await period_service.get_periods(filters)


@router.get("/active", response_model=PeriodResponse, summary="Get active period")
async def get_active_period(
    current_user: dict = Depends(get_current_active_user),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Get all active period.
    
    All authenticated users can view active period.
    """
    return await period_service.get_active_period()


@router.get("/current", response_model=List[PeriodResponse], summary="Get current periods")
async def get_current_periods(
    current_user: dict = Depends(get_current_active_user),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Get periods that are currently active based on dates.
    
    All authenticated users can view current periods.
    """
    return await period_service.get_current_periods()


@router.get("/{period_id}", response_model=PeriodResponse, summary="Get period by ID")
async def get_period(
    period_id: int,
    current_user: dict = Depends(get_current_active_user),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Get period details by ID.
    
    All authenticated users can view period details.
    """
    return await period_service.get_period(period_id)


@router.get("/{period_id}/stats", response_model=PeriodWithStats, summary="Get period with statistics")
async def get_period_with_stats(
    period_id: int,
    current_user: dict = Depends(admin_or_manager),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Get period details with statistics (evaluations, submissions, etc.).
    
    Only admins and kepala sekolah can view period statistics.
    """
    return await period_service.get_period_with_stats(period_id)


@router.put("/{period_id}", response_model=PeriodResponse, summary="Update period")
async def update_period(
    period_id: int,
    period_data: PeriodUpdate,
    current_user: dict = Depends(admin_or_manager),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Update an existing period.
    
    Only admins and kepala sekolah can update periods.
    """
    return await period_service.update_period(period_id, period_data, current_user["id"])


@router.patch("/{period_id}/activate", response_model=PeriodResponse, summary="Activate period")
async def activate_period(
    period_id: int,
    current_user: dict = Depends(admin_or_manager),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Activate a period.
    
    Only admins and kepala sekolah can activate periods.
    """
    return await period_service.activate_period(period_id, current_user["id"])


@router.patch("/{period_id}/deactivate", response_model=PeriodResponse, summary="Deactivate period")
async def deactivate_period(
    period_id: int,
    current_user: dict = Depends(admin_or_manager),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Deactivate a period.
    
    Only admins and kepala sekolah can deactivate periods.
    """
    return await period_service.deactivate_period(period_id, current_user["id"])


@router.patch("/{period_id}/toggle", response_model=PeriodResponse, summary="Toggle period status")
async def toggle_period_status(
    period_id: int,
    activation_data: PeriodActivate,
    current_user: dict = Depends(admin_or_manager),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Toggle period activation status.
    
    Only admins and kepala sekolah can toggle period status.
    """
    return await period_service.toggle_period_status(period_id, activation_data, current_user["id"])


@router.delete("/{period_id}", response_model=MessageResponse, summary="Delete period")
async def delete_period(
    period_id: int,
    current_user: dict = Depends(admin_required),
    period_service: PeriodService = Depends(get_period_service)
):
    """
    Delete a period.
    
    Only admins can delete periods. Period must not have any associated evaluations or submissions.
    """
    return await period_service.delete_period(period_id)