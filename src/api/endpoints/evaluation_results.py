"""Evaluation Result API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.auth.permissions import get_current_active_user, admin_required, evaluator_roles_required
from src.repositories.evaluation_result import EvaluationResultRepository
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.user import UserRepository
from src.services.evaluation_result import EvaluationResultService
from src.schemas.evaluation_result import (
    EvaluationResultCreate,
    EvaluationResultUpdate,
    EvaluationResultResponse,
    EvaluationResultListResponse,
    EvaluationResultCalculateFromEvaluations,
    EvaluationResultBulkUpdate,
    EvaluationResultBulkRecalculate,
    TeacherPerformanceComparison,
    OrganizationPerformanceOverview,
    EvaluationResultAnalytics
)
from src.schemas.filters import EvaluationResultFilterParams
from src.schemas.shared import MessageResponse

router = APIRouter(prefix="/evaluation-results", tags=["Evaluation Results"])


def get_result_service(db: AsyncSession = Depends(get_db)) -> EvaluationResultService:
    """Get evaluation result service."""
    result_repo = EvaluationResultRepository(db)
    evaluation_repo = TeacherEvaluationRepository(db)
    user_repo = UserRepository(db)
    return EvaluationResultService(result_repo, evaluation_repo, user_repo)


# ===== BASIC CRUD OPERATIONS =====

@router.post(
    "/",
    response_model=EvaluationResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evaluation result"
)
async def create_result(
    result_data: EvaluationResultCreate,
    current_user: dict = Depends(evaluator_roles_required),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """
    Create a new evaluation result.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await result_service.create_result(result_data)


@router.post(
    "/calculate-from-evaluations",
    response_model=EvaluationResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create result from evaluations"
)
async def create_result_from_evaluations(
    calculation_data: EvaluationResultCalculateFromEvaluations,
    current_user: dict = Depends(evaluator_roles_required),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """
    Create evaluation result calculated from individual evaluations.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await result_service.create_result_from_evaluations(calculation_data)


@router.get(
    "/{result_id}",
    response_model=EvaluationResultResponse,
    summary="Get evaluation result by ID"
)
async def get_result(
    result_id: int,
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get evaluation result by ID."""
    return await result_service.get_result_by_id(result_id)


@router.put(
    "/{result_id}",
    response_model=EvaluationResultResponse,
    summary="Update evaluation result"
)
async def update_result(
    result_id: int,
    result_data: EvaluationResultUpdate,
    current_user: dict = Depends(evaluator_roles_required),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """
    Update evaluation result.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await result_service.update_result(result_id, result_data)


@router.delete(
    "/{result_id}",
    response_model=MessageResponse,
    summary="Delete evaluation result"
)
async def delete_result(
    result_id: int,
    current_user: dict = Depends(admin_required),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """
    Delete evaluation result.
    
    Requires admin role.
    """
    return await result_service.delete_result(result_id)


# ===== LISTING AND FILTERING =====

@router.get(
    "/",
    response_model=EvaluationResultListResponse,
    summary="List evaluation results"
)
async def list_results(
    filters: EvaluationResultFilterParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """List evaluation results with filtering and pagination."""
    return await result_service.get_results(filters)


@router.get(
    "/teacher/{teacher_id}",
    response_model=List[EvaluationResultResponse],
    summary="Get teacher results"
)
async def get_teacher_results(
    teacher_id: int,
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get all evaluation results for a specific teacher."""
    return await result_service.get_teacher_results(teacher_id, academic_year)


@router.get(
    "/teacher/{teacher_id}/latest",
    response_model=EvaluationResultResponse,
    summary="Get latest teacher result"
)
async def get_latest_teacher_result(
    teacher_id: int,
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get the most recent evaluation result for a teacher."""
    return await result_service.get_latest_result_for_teacher(teacher_id)


@router.get(
    "/period/{academic_year}/{semester}",
    response_model=List[EvaluationResultResponse],
    summary="Get results by period"
)
async def get_results_by_period(
    academic_year: str,
    semester: str,
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get all evaluation results for a specific academic period."""
    return await result_service.get_results_by_period(academic_year, semester)


@router.get(
    "/period/{academic_year}/{semester}/top-performers",
    response_model=List[EvaluationResultResponse],
    summary="Get top performers"
)
async def get_top_performers(
    academic_year: str,
    semester: str,
    limit: int = Query(10, ge=1, le=50, description="Number of top performers to return"),
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get top performing teachers for a specific period."""
    return await result_service.get_top_performers(academic_year, semester, limit)


@router.get(
    "/period/{academic_year}/{semester}/improvement-needed",
    response_model=List[EvaluationResultResponse],
    summary="Get teachers needing improvement"
)
async def get_improvement_needed(
    academic_year: str,
    semester: str,
    threshold: float = Query(70.0, ge=0, le=100, description="Performance threshold"),
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get teachers who need improvement (below threshold)."""
    return await result_service.get_improvement_needed(academic_year, semester, threshold)


# ===== BULK OPERATIONS =====

@router.patch(
    "/bulk/update-recommendations",
    response_model=MessageResponse,
    summary="Bulk update recommendations"
)
async def bulk_update_recommendations(
    bulk_data: EvaluationResultBulkUpdate,
    current_user: dict = Depends(evaluator_roles_required),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """
    Bulk update recommendations for multiple results.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await result_service.bulk_update_recommendations(bulk_data)


@router.post(
    "/bulk/recalculate",
    response_model=MessageResponse,
    summary="Bulk recalculate results"
)
async def bulk_recalculate_results(
    bulk_data: EvaluationResultBulkRecalculate,
    current_user: dict = Depends(admin_required),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """
    Bulk recalculate evaluation results.
    
    Requires admin role.
    """
    return await result_service.bulk_recalculate_results(bulk_data)


# ===== PERFORMANCE ANALYSIS =====

@router.get(
    "/teacher/{teacher_id}/performance-comparison",
    response_model=TeacherPerformanceComparison,
    summary="Get teacher performance comparison"
)
async def get_teacher_performance_comparison(
    teacher_id: int,
    current_year: str = Query(..., description="Current academic year"),
    current_semester: str = Query(..., description="Current semester"),
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get performance comparison for a teacher between current and previous period."""
    return await result_service.get_teacher_performance_comparison(
        teacher_id, current_year, current_semester
    )


@router.get(
    "/organization/performance-overview",
    response_model=OrganizationPerformanceOverview,
    summary="Get organization performance overview"
)
async def get_organization_performance_overview(
    academic_year: str = Query(..., description="Academic year"),
    semester: str = Query(..., description="Semester"),
    organization_id: Optional[int] = Query(None, description="Organization ID"),
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get organization-wide performance overview for a specific period."""
    return await result_service.get_organization_performance_overview(
        academic_year, semester, organization_id
    )


# ===== ANALYTICS =====

@router.get(
    "/analytics/overview",
    response_model=EvaluationResultAnalytics,
    summary="Get evaluation results analytics"
)
async def get_results_analytics(
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get comprehensive evaluation results analytics."""
    return await result_service.get_results_analytics(organization_id)


@router.get(
    "/teacher/{teacher_id}/performance-trend",
    response_model=dict,
    summary="Get teacher performance trend"
)
async def get_teacher_performance_trend(
    teacher_id: int,
    limit: int = Query(10, ge=1, le=20, description="Number of periods to analyze"),
    current_user: dict = Depends(get_current_active_user),
    result_service: EvaluationResultService = Depends(get_result_service)
):
    """Get performance trend analysis for a teacher over time."""
    return await result_service.get_teacher_performance_trend(teacher_id, limit)