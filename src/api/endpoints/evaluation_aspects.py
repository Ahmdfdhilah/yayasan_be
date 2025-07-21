"""Evaluation Aspect API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.auth.permissions import get_current_active_user, admin_required
from src.repositories.evaluation_aspect import EvaluationAspectRepository
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
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
    EvaluationAspectStats,
    AspectOrderUpdate,
    CategoryAspectsReorder,
    CategoryWithAspectsResponse
)
from src.schemas.evaluation_category import (
    EvaluationCategoryCreate,
    EvaluationCategoryResponse,
    EvaluationCategorySummary,
    CategoryOrderUpdate,
    EvaluationCategoryListResponse
)
from src.schemas.evaluation_aspect import EvaluationAspectFilterParams
from src.schemas.shared import MessageResponse

router = APIRouter(prefix="/evaluation-aspects", tags=["Evaluation Aspects"])


def get_aspect_service(db: AsyncSession = Depends(get_db)) -> EvaluationAspectService:
    """Get evaluation aspect service with auto-sync functionality."""
    aspect_repo = EvaluationAspectRepository(db)
    evaluation_repo = TeacherEvaluationRepository(db)
    return EvaluationAspectService(aspect_repo, evaluation_repo, db)


# ===== SPECIFIC ENDPOINTS (Must come before generic {id} routes) =====

@router.get(
    "/active/list",
    response_model=List[EvaluationAspectSummary],
    summary="Get active evaluation aspects"
)
async def get_active_aspects(
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get all active evaluation aspects."""
    return await aspect_service.get_active_aspects()


@router.get(
    "/analytics",
    response_model=EvaluationAspectStats,
    summary="Get comprehensive analytics and statistics"
)
async def get_comprehensive_analytics(
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get comprehensive evaluation aspect analytics, statistics and recommendations."""
    return await aspect_service.get_comprehensive_stats()


# ===== CATEGORY MANAGEMENT =====

@router.post(
    "/categories",
    response_model=EvaluationCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evaluation category"
)
async def create_category(
    category_data: EvaluationCategoryCreate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Create a new evaluation category. Requires admin role."""
    return await aspect_service.create_category(category_data, current_user.get("id"))


@router.get(
    "/categories",
    response_model=List[EvaluationCategoryResponse],
    summary="Get all categories"
)
async def get_categories(
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get all categories with order information and aspect counts."""
    return await aspect_service.get_categories_with_order()


@router.get(
    "/categories/{category_id}/aspects",
    response_model=List[EvaluationAspectResponse],
    summary="Get aspects by category with proper ordering"
)
async def get_aspects_by_category_ordered(
    category_id: int,
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get evaluation aspects by category ID with proper ordering."""
    return await aspect_service.get_aspects_by_category_ordered(category_id)


@router.get(
    "/categories/{category_id}/with-aspects",
    response_model=CategoryWithAspectsResponse,
    summary="Get category with all its aspects"
)
async def get_category_with_aspects(
    category_id: int,
    current_user: dict = Depends(get_current_active_user),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Get category with all its aspects ordered properly."""
    return await aspect_service.get_category_with_aspects(category_id)


# ===== ORDERING ENDPOINTS =====

@router.put(
    "/ordering/category",
    response_model=MessageResponse,
    summary="Update category display order"
)
async def update_category_order(
    order_data: CategoryOrderUpdate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Update the display order of a category. Requires admin role."""
    return await aspect_service.update_category_order(order_data)


@router.put(
    "/ordering/aspect",
    response_model=MessageResponse,
    summary="Update aspect display order"
)
async def update_aspect_order(
    order_data: AspectOrderUpdate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Update the display order of a specific aspect within its category. Requires admin role."""
    return await aspect_service.update_aspect_order(order_data)


@router.put(
    "/ordering/category/reorder",
    response_model=MessageResponse,
    summary="Reorder aspects within a category"
)
async def reorder_aspects_in_category(
    reorder_data: CategoryAspectsReorder,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Reorder multiple aspects within a category by providing new display orders. Requires admin role."""
    return await aspect_service.reorder_aspects_in_category(reorder_data)


@router.post(
    "/ordering/auto-assign",
    response_model=MessageResponse,
    summary="Auto-assign orders to categories and aspects"
)
async def auto_assign_orders(
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Automatically assign display orders to categories and aspects. Requires admin role."""
    return await aspect_service.auto_assign_orders()




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
    """Bulk create evaluation aspects. Requires admin role."""
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
    """Bulk update evaluation aspects. Requires admin role."""
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
    """Bulk delete evaluation aspects. Requires admin role."""
    return await aspect_service.bulk_delete_aspects(bulk_data)


@router.post(
    "/sync/manual",
    response_model=MessageResponse,
    summary="Manual sync all active aspects to teacher evaluations"
)
async def manual_sync_aspects(
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Manually synchronize all active evaluation aspects to all existing teacher evaluations. Requires admin role."""
    return await aspect_service.sync_all_active_aspects()


# ===== BASIC CRUD OPERATIONS (Generic {id} routes must come LAST) =====

@router.post(
    "/",
    response_model=EvaluationAspectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evaluation aspect with auto-sync"
)
async def create_aspect(
    aspect_data: EvaluationAspectCreate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Create a new evaluation aspect with automatic sync to existing teacher evaluations. Requires admin role."""
    return await aspect_service.create_aspect(aspect_data, current_user.get("id"))


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
    summary="Update evaluation aspect with auto-sync"
)
async def update_aspect(
    aspect_id: int,
    aspect_data: EvaluationAspectUpdate,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Update evaluation aspect with automatic sync to teacher evaluations. Requires admin role."""
    return await aspect_service.update_aspect(aspect_id, aspect_data, current_user.get("id"))


@router.delete(
    "/{aspect_id}",
    response_model=MessageResponse,
    summary="Delete evaluation aspect with auto-sync"
)
async def delete_aspect(
    aspect_id: int,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Delete evaluation aspect and automatically remove from all teacher evaluations. Requires admin role."""
    return await aspect_service.delete_aspect(aspect_id)


@router.patch(
    "/{aspect_id}/activate",
    response_model=EvaluationAspectResponse,
    summary="Activate evaluation aspect with auto-sync"
)
async def activate_aspect(
    aspect_id: int,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Activate evaluation aspect and automatically add to all existing teacher evaluations. Requires admin role."""
    return await aspect_service.activate_aspect(aspect_id, current_user.get("id"))


@router.patch(
    "/{aspect_id}/deactivate",
    response_model=EvaluationAspectResponse,
    summary="Deactivate evaluation aspect with auto-sync"
)
async def deactivate_aspect(
    aspect_id: int,
    current_user: dict = Depends(admin_required),
    aspect_service: EvaluationAspectService = Depends(get_aspect_service)
):
    """Deactivate evaluation aspect and automatically remove from all teacher evaluations. Requires admin role."""
    return await aspect_service.deactivate_aspect(aspect_id, current_user.get("id"))