"""Teacher Evaluation API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.auth.permissions import get_current_active_user, admin_required, evaluator_roles_required
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.evaluation_aspect import EvaluationAspectRepository
from src.repositories.user import UserRepository
from src.services.teacher_evaluation import TeacherEvaluationService
from src.schemas.teacher_evaluation import (
    TeacherEvaluationCreate,
    TeacherEvaluationUpdate,
    TeacherEvaluationResponse,
    TeacherEvaluationListResponse,
    TeacherEvaluationBulkCreate,
    TeacherEvaluationBulkUpdate,
    TeacherEvaluationBulkDelete,
    TeacherEvaluationAggregated,
    EvaluationPeriodSummary,
    TeacherEvaluationAnalytics,
    TeacherPerformanceReport
)
from src.schemas.filters import TeacherEvaluationFilterParams
from src.schemas.shared import MessageResponse

router = APIRouter(prefix="/teacher-evaluations", tags=["Teacher Evaluations"])


def get_evaluation_service(db: AsyncSession = Depends(get_db)) -> TeacherEvaluationService:
    """Get teacher evaluation service."""
    evaluation_repo = TeacherEvaluationRepository(db)
    aspect_repo = EvaluationAspectRepository(db)
    user_repo = UserRepository(db)
    return TeacherEvaluationService(evaluation_repo, aspect_repo, user_repo)


# ===== BASIC CRUD OPERATIONS =====

@router.post(
    "/",
    response_model=TeacherEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create teacher evaluation"
)
async def create_evaluation(
    evaluation_data: TeacherEvaluationCreate,
    current_user: dict = Depends(evaluator_roles_required),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """
    Create a new teacher evaluation.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await evaluation_service.create_evaluation(evaluation_data)


@router.get(
    "/{evaluation_id}",
    response_model=TeacherEvaluationResponse,
    summary="Get teacher evaluation by ID"
)
async def get_evaluation(
    evaluation_id: int,
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """Get teacher evaluation by ID."""
    return await evaluation_service.get_evaluation_by_id(evaluation_id)


@router.put(
    "/{evaluation_id}",
    response_model=TeacherEvaluationResponse,
    summary="Update teacher evaluation"
)
async def update_evaluation(
    evaluation_id: int,
    evaluation_data: TeacherEvaluationUpdate,
    current_user: dict = Depends(evaluator_roles_required),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """
    Update teacher evaluation.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await evaluation_service.update_evaluation(evaluation_id, evaluation_data)


@router.delete(
    "/{evaluation_id}",
    response_model=MessageResponse,
    summary="Delete teacher evaluation"
)
async def delete_evaluation(
    evaluation_id: int,
    current_user: dict = Depends(admin_required),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """
    Delete teacher evaluation.
    
    Requires admin role.
    """
    return await evaluation_service.delete_evaluation(evaluation_id)


# ===== LISTING AND FILTERING =====

@router.get(
    "/",
    response_model=TeacherEvaluationListResponse,
    summary="List teacher evaluations"
)
async def list_evaluations(
    filters: TeacherEvaluationFilterParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """List teacher evaluations with filtering and pagination."""
    return await evaluation_service.get_evaluations(filters)


@router.get(
    "/teacher/{teacher_id}",
    response_model=List[TeacherEvaluationResponse],
    summary="Get teacher evaluations"
)
async def get_teacher_evaluations(
    teacher_id: int,
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """Get all evaluations for a specific teacher."""
    return await evaluation_service.get_teacher_evaluations(teacher_id, academic_year, semester)


@router.get(
    "/period/{academic_year}/{semester}",
    response_model=List[TeacherEvaluationResponse],
    summary="Get evaluations by period"
)
async def get_evaluations_by_period(
    academic_year: str,
    semester: str,
    evaluator_id: Optional[int] = Query(None, description="Filter by evaluator ID"),
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """Get all evaluations for a specific academic period."""
    return await evaluation_service.get_evaluations_by_period(
        academic_year, semester, evaluator_id
    )


@router.get(
    "/aspect/{aspect_id}",
    response_model=List[TeacherEvaluationResponse],
    summary="Get evaluations by aspect"
)
async def get_evaluations_by_aspect(
    aspect_id: int,
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """Get all evaluations for a specific aspect."""
    return await evaluation_service.get_evaluations_by_aspect(aspect_id)


# ===== BULK OPERATIONS =====

@router.post(
    "/bulk/create",
    response_model=List[TeacherEvaluationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create teacher evaluations"
)
async def bulk_create_evaluations(
    bulk_data: TeacherEvaluationBulkCreate,
    current_user: dict = Depends(evaluator_roles_required),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """
    Bulk create teacher evaluations for a specific teacher and period.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await evaluation_service.bulk_create_evaluations(bulk_data)


@router.post(
    "/evaluation-set",
    response_model=List[TeacherEvaluationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create evaluation set"
)
async def create_evaluation_set(
    evaluator_id: int = Query(..., description="Evaluator user ID"),
    teacher_id: int = Query(..., description="Teacher user ID"),
    academic_year: str = Query(..., description="Academic year"),
    semester: str = Query(..., description="Semester"),
    aspect_scores: Dict[int, Dict[str, Any]] = ...,
    current_user: dict = Depends(evaluator_roles_required),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """
    Create a complete set of evaluations for a teacher.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await evaluation_service.create_evaluation_set(
        evaluator_id, teacher_id, academic_year, semester, aspect_scores
    )


@router.patch(
    "/bulk/update",
    response_model=MessageResponse,
    summary="Bulk update teacher evaluations"
)
async def bulk_update_evaluations(
    bulk_data: TeacherEvaluationBulkUpdate,
    current_user: dict = Depends(evaluator_roles_required),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """
    Bulk update teacher evaluations.
    
    Requires evaluator role (super_admin, admin, or kepala_sekolah).
    """
    return await evaluation_service.bulk_update_evaluations(bulk_data)


@router.delete(
    "/bulk/delete",
    response_model=MessageResponse,
    summary="Bulk delete teacher evaluations"
)
async def bulk_delete_evaluations(
    bulk_data: TeacherEvaluationBulkDelete,
    current_user: dict = Depends(admin_required),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """
    Bulk delete teacher evaluations.
    
    Requires admin role.
    """
    return await evaluation_service.bulk_delete_evaluations(bulk_data)


# ===== AGGREGATION AND ANALYSIS =====

@router.get(
    "/teacher/{teacher_id}/summary/{academic_year}/{semester}",
    response_model=TeacherEvaluationAggregated,
    summary="Get teacher evaluation summary"
)
async def get_teacher_evaluation_summary(
    teacher_id: int,
    academic_year: str,
    semester: str,
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """Get comprehensive evaluation summary for a teacher in a specific period."""
    return await evaluation_service.get_teacher_evaluation_summary(
        teacher_id, academic_year, semester
    )


@router.get(
    "/period/{academic_year}/{semester}/summary",
    response_model=EvaluationPeriodSummary,
    summary="Get period summary"
)
async def get_period_summary(
    academic_year: str,
    semester: str,
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """Get evaluation period summary with completion statistics."""
    return await evaluation_service.get_period_summary(academic_year, semester)


@router.get(
    "/teacher/{teacher_id}/performance-report",
    response_model=TeacherPerformanceReport,
    summary="Get teacher performance report"
)
async def get_teacher_performance_report(
    teacher_id: int,
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """Get comprehensive performance report for a teacher with trends and recommendations."""
    return await evaluation_service.get_teacher_performance_report(teacher_id)


# ===== ANALYTICS =====

@router.get(
    "/analytics/overview",
    response_model=TeacherEvaluationAnalytics,
    summary="Get teacher evaluations analytics"
)
async def get_evaluations_analytics(
    current_user: dict = Depends(get_current_active_user),
    evaluation_service: TeacherEvaluationService = Depends(get_evaluation_service)
):
    """Get comprehensive teacher evaluations analytics."""
    return await evaluation_service.get_evaluations_analytics()