"""Evaluation Aspect API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.auth.permissions import get_current_active_user, admin_required
from src.repositories.evaluation_aspect import EvaluationAspectRepository
from src.services.evaluation_aspect import EvaluationAspectService
from src.schemas.evaluation_aspect import (
    EvaluationAspectCreate,
    EvaluationAspectUpdate,
    EvaluationAspectResponse,
    EvaluationAspectListResponse,
    EvaluationAspectSummary,
    EvaluationAspectBulkCreate,
    EvaluationAspectBulkUpdate,
    EvaluationAspectBulkDelete,
    EvaluationAspectAnalytics,
    AspectPerformanceAnalysis,
    EvaluationAspectStats
)
from src.schemas.filters import EvaluationAspectFilterParams
from src.schemas.shared import MessageResponse

router = APIRouter(prefix="/evaluation-aspects", tags=["Evaluation Aspects"])


def get_aspect_service(db: AsyncSession = Depends(get_db)) -> EvaluationAspectService:
    """Get evaluation aspect service."""
    aspect_repo = EvaluationAspectRepository(db)
    return EvaluationAspectService(aspect_repo)


# ===== BASIC CRUD OPERATIONS =====

@router.post(
    "/",
    response_model=EvaluationAspectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evaluation aspect"
)
async def create_aspect(
    aspect_data: EvaluationAspectCreate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """
    Create a new evaluation aspect.
    
    Requires admin role.
    """
    return await aspect_service.create_aspect(aspect_data, current_user.get("user_id"))


@router.get(
    "/{aspect_id}",
    response_model=EvaluationAspectResponse,
    summary="Get evaluation aspect by ID"
)
async def get_aspect(
    aspect_id: int,
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get evaluation aspect by ID with statistics."""
    return await aspect_service.get_aspect_by_id(aspect_id)


@router.put(
    "/{aspect_id}",
    response_model=EvaluationAspectResponse,
    summary="Update evaluation aspect"
)
async def update_aspect(
    aspect_id: int,
    aspect_data: EvaluationAspectUpdate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """
    Update evaluation aspect.
    
    Requires admin role.
    """
    return await aspect_service.update_aspect(aspect_id, aspect_data)


@router.delete(
    "/{aspect_id}",
    response_model=MessageResponse,
    summary="Delete evaluation aspect"
)
async def delete_aspect(
    aspect_id: int,
    force: bool = Query(False, description="Force delete even if aspect has evaluations"),
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """
    Delete evaluation aspect.
    
    Requires admin role. Use force=true to delete aspects with existing evaluations.
    """
    return await aspect_service.delete_aspect(aspect_id, force)


@router.patch(
    "/{aspect_id}/activate",
    response_model=EvaluationAspectResponse,
    summary="Activate evaluation aspect"
)
async def activate_aspect(
    aspect_id: int,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """
    Activate evaluation aspect.
    
    Requires admin role.
    """
    return await aspect_service.activate_aspect(aspect_id)


@router.patch(
    "/{aspect_id}/deactivate",
    response_model=EvaluationAspectResponse,
    summary="Deactivate evaluation aspect"
)
async def deactivate_aspect(
    aspect_id: int,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """
    Deactivate evaluation aspect.
    
    Requires admin role.
    """
    return await aspect_service.deactivate_aspect(aspect_id)


# ===== LISTING AND FILTERING =====

@router.get(
    "/",
    response_model=EvaluationAspectListResponse,
    summary="List evaluation aspects"
)
async def list_aspects(
    filters: EvaluationAspectFilterParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """List evaluation aspects with filtering and pagination."""
    return await aspect_service.get_aspects(filters)


@router.get(
    "/active/list",
    response_model=List[EvaluationAspectSummary],
    summary="Get active evaluation aspects"
)
async def get_active_aspects(
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get all active evaluation aspects (universal across all organizations)."""
    return await aspect_service.get_active_aspects()


@router.get(
    "/category/{category}",
    response_model=List[EvaluationAspectSummary],
    summary="Get aspects by category"
)
async def get_aspects_by_category(
    category: str,
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get evaluation aspects by category."""
    return await aspect_service.get_aspects_by_category(category)


# ===== BULK OPERATIONS =====

@router.post(
    "/bulk/create",
    response_model=List[EvaluationAspectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create evaluation aspects"
)
async def bulk_create_aspects(
    bulk_data: EvaluationAspectBulkCreate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """
    Bulk create evaluation aspects.
    
    Requires admin role.
    """
    return await aspect_service.bulk_create_aspects(bulk_data, current_user.get("id"))


@router.patch(
    "/bulk/update",
    response_model=MessageResponse,
    summary="Bulk update evaluation aspects"
)
async def bulk_update_aspects(
    bulk_data: EvaluationAspectBulkUpdate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """
    Bulk update evaluation aspects.
    
    Requires admin role.
    """
    return await aspect_service.bulk_update_aspects(bulk_data)


@router.delete(
    "/bulk/delete",
    response_model=MessageResponse,
    summary="Bulk delete evaluation aspects"
)
async def bulk_delete_aspects(
    bulk_data: EvaluationAspectBulkDelete,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """
    Bulk delete evaluation aspects.
    
    Requires admin role.
    """
    return await aspect_service.bulk_delete_aspects(bulk_data)



# ===== ANALYTICS =====

@router.get(
    "/analytics/overview",
    response_model=EvaluationAspectAnalytics,
    summary="Get evaluation aspects analytics"
)
async def get_aspects_analytics(
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get comprehensive evaluation aspects analytics."""
    return await aspect_service.get_aspects_analytics()


@router.get(
    "/{aspect_id}/analytics/performance",
    response_model=AspectPerformanceAnalysis,
    summary="Get aspect performance analysis"
)
async def get_aspect_performance_analysis(
    aspect_id: int,
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get detailed performance analysis for a specific aspect."""
    return await aspect_service.get_aspect_performance_analysis(aspect_id)


@router.get(
    "/analytics/comprehensive",
    response_model=EvaluationAspectStats,
    summary="Get comprehensive aspect statistics"
)
async def get_comprehensive_stats(
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get comprehensive evaluation aspect statistics and recommendations."""
    return await aspect_service.get_comprehensive_stats()