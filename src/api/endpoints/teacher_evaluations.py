"""Teacher Evaluations endpoints - Refactored for parent-child structure."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.user import UserRepository
from src.services.teacher_evaluation import TeacherEvaluationService
from src.schemas.teacher_evaluation import (
    TeacherEvaluationCreate,
    TeacherEvaluationUpdate,
    TeacherEvaluationResponse,
    TeacherEvaluationItemCreate,
    TeacherEvaluationItemResponse,
    TeacherEvaluationWithItemsCreate,
    TeacherEvaluationBulkItemUpdate,
    AssignTeachersToEvaluationPeriod,
    AssignTeachersToEvaluationPeriodResponse,
    TeacherEvaluationSummary,
    PeriodEvaluationStats,
    TeacherEvaluationFilterParams,
    UpdateEvaluationItemGrade,
    UpdateEvaluationFinalNotes,
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import (
    get_current_active_user,
    require_roles,
    require_teacher_evaluation_view_permission,
    require_teacher_evaluation_update_permission,
)
from src.models.enums import EvaluationGrade

router = APIRouter()

# Role-based permissions
admin_required = require_roles(["admin"])
admin_or_manager = require_roles(["admin", "kepala_sekolah"])


async def get_teacher_evaluation_service(
    session: AsyncSession = Depends(get_db),
) -> TeacherEvaluationService:
    """Get teacher evaluation service dependency."""
    evaluation_repo = TeacherEvaluationRepository(session)
    user_repo = UserRepository(session)
    return TeacherEvaluationService(evaluation_repo, user_repo, session)


# ===== PARENT EVALUATION ENDPOINTS =====


@router.post(
    "/", response_model=TeacherEvaluationResponse, summary="Create teacher evaluation"
)
async def create_teacher_evaluation(
    evaluation_data: TeacherEvaluationCreate,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Create a new teacher evaluation record.

    - **teacher_id**: ID of teacher to evaluate
    - **evaluator_id**: ID of evaluator (usually kepala sekolah)
    - **period_id**: Evaluation period
    - **final_notes**: Optional final notes
    """
    return await service.create_evaluation(evaluation_data, current_user["id"])


@router.post(
    "/with-items",
    response_model=TeacherEvaluationResponse,
    summary="Create evaluation with items",
)
async def create_evaluation_with_items(
    evaluation_data: TeacherEvaluationWithItemsCreate,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Create teacher evaluation with multiple aspect items at once.

    - **teacher_id**: ID of teacher to evaluate
    - **evaluator_id**: ID of evaluator
    - **period_id**: Evaluation period
    - **items**: List of aspect evaluations to create
    - **final_notes**: Optional final notes
    """
    return await service.create_evaluation_with_items(
        evaluation_data, current_user["id"]
    )


@router.get(
    "/{evaluation_id}",
    response_model=TeacherEvaluationResponse,
    summary="Get teacher evaluation by ID",
)
async def get_teacher_evaluation(
    evaluation_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Get teacher evaluation by ID with all items and relationships.

    Access control:
    - Teachers can only view their own evaluations
    - Kepala sekolah can view evaluations in their organization
    - Admins can view all evaluations
    """
    return await service.get_evaluation(evaluation_id, current_user)


@router.put(
    "/{evaluation_id}/final-notes",
    response_model=TeacherEvaluationResponse,
    summary="Update final notes",
)
async def update_evaluation_final_notes(
    evaluation_id: int,
    update_data: UpdateEvaluationFinalNotes,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Update final notes for teacher evaluation.

    - **final_notes**: Final evaluation summary notes
    """
    return await service.update_evaluation_notes(
        evaluation_id, update_data, current_user["id"]
    )


@router.delete(
    "/{evaluation_id}",
    response_model=MessageResponse,
    summary="Delete teacher evaluation",
)
async def delete_teacher_evaluation(
    evaluation_id: int,
    current_user: dict = Depends(admin_required),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """Delete teacher evaluation and all its items (Admin only)."""
    return await service.delete_evaluation(evaluation_id)


# ===== EVALUATION ITEM ENDPOINTS =====


@router.post(
    "/{evaluation_id}/items",
    response_model=TeacherEvaluationItemResponse,
    summary="Create evaluation item",
)
async def create_evaluation_item(
    evaluation_id: int,
    item_data: TeacherEvaluationItemCreate,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Create new evaluation item for specific aspect.

    - **aspect_id**: ID of evaluation aspect
    - **grade**: Evaluation grade (A, B, C, D)
    - **notes**: Optional notes for this aspect
    """
    return await service.create_evaluation_item(
        evaluation_id, item_data, current_user["id"]
    )


@router.put(
    "/{evaluation_id}/items/{aspect_id}",
    response_model=TeacherEvaluationItemResponse,
    summary="Update evaluation item",
)
async def update_evaluation_item(
    evaluation_id: int,
    aspect_id: int,
    item_data: UpdateEvaluationItemGrade,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Update evaluation item for specific aspect.

    - **grade**: Updated evaluation grade
    - **notes**: Updated notes for this aspect
    """
    return await service.update_evaluation_item(
        evaluation_id, aspect_id, item_data, current_user["id"]
    )


@router.delete(
    "/{evaluation_id}/items/{aspect_id}",
    response_model=MessageResponse,
    summary="Delete evaluation item",
)
async def delete_evaluation_item(
    evaluation_id: int,
    aspect_id: int,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """Delete evaluation item for specific aspect."""
    return await service.delete_evaluation_item(evaluation_id, aspect_id)


@router.patch(
    "/{evaluation_id}/bulk-items",
    response_model=TeacherEvaluationResponse,
    summary="Bulk update items",
)
async def bulk_update_evaluation_items(
    evaluation_id: int,
    bulk_data: TeacherEvaluationBulkItemUpdate,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Bulk update multiple evaluation items.

    - **item_updates**: List of {aspect_id, grade, notes} updates
    """
    return await service.bulk_update_evaluation_items(
        evaluation_id, bulk_data, current_user["id"]
    )


# ===== QUERY ENDPOINTS =====


@router.get(
    "/", response_model=Dict[str, Any], summary="Get filtered teacher evaluations"
)
async def get_teacher_evaluations_filtered(
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    evaluator_id: Optional[int] = Query(None, description="Filter by evaluator ID"),
    period_id: Optional[int] = Query(None, description="Filter by period ID"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search by teacher name"),
    final_grade: Optional[float] = Query(
        None, description="Filter by final grade"
    ),
    min_average_score: Optional[float] = Query(
        None, ge=1.0, le=4.0, description="Minimum average score"
    ),
    max_average_score: Optional[float] = Query(
        None, ge=1.0, le=4.0, description="Maximum average score"
    ),
    has_final_notes: Optional[bool] = Query(
        None, description="Filter by presence of final notes"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    current_user: dict = Depends(get_current_active_user),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Get filtered list of teacher evaluations with pagination.

    Access control automatically applied based on user role:
    - Teachers see only their own evaluations
    - Kepala sekolah see evaluations in their organization
    - Admins see all evaluations
    """
    filters = TeacherEvaluationFilterParams(
        teacher_id=teacher_id,
        evaluator_id=evaluator_id,
        period_id=period_id,
        organization_id=organization_id,
        search=search,
        final_grade=final_grade,
        min_average_score=min_average_score,
        max_average_score=max_average_score,
        has_final_notes=has_final_notes,
        skip=skip,
        limit=limit,
    )

    return await service.get_evaluations_filtered(filters, current_user)


@router.get(
    "/teacher/{teacher_id}/period/{period_id}/evaluator/{evaluator_id}",
    response_model=TeacherEvaluationResponse,
    summary="Get teacher evaluation by period and evaluator",
)
async def get_teacher_evaluation_by_period(
    teacher_id: int,
    period_id: int,
    evaluator_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """Get teacher evaluation for specific period and evaluator."""
    return await service.get_teacher_evaluation_by_period(
        teacher_id, period_id, evaluator_id, current_user
    )


@router.get(
    "/period/{period_id}",
    response_model=List[TeacherEvaluationResponse],
    summary="Get evaluations by period",
)
async def get_evaluations_by_period(
    period_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """Get all teacher evaluations for a specific period."""
    return await service.get_evaluations_by_period(period_id, current_user)


# ===== BULK OPERATIONS =====


@router.post(
    "/assign-teachers-to-period",
    response_model=AssignTeachersToEvaluationPeriodResponse,
    summary="Assign teachers to period",
)
async def assign_teachers_to_period(
    assignment_data: AssignTeachersToEvaluationPeriod,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Auto-assign all teachers to evaluation period.
    
    Automatically creates evaluations for:
    - All teachers (GURU role) in all organizations
    - Auto-assigns kepala sekolah as evaluator per organization
    - Auto-creates evaluation items for all active aspects
    
    Only requires period_id - everything else is automated.
    """
    return await service.assign_teachers_to_period(
        assignment_data, current_user["id"]
    )


# ===== STATISTICS AND ANALYTICS =====


@router.get(
    "/period/{period_id}/stats",
    response_model=PeriodEvaluationStats,
    summary="Get period statistics",
)
async def get_period_statistics(
    period_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Get comprehensive statistics for evaluations in a period.

    Includes:
    - Total evaluations and teachers
    - Completion statistics
    - Grade distribution
    - Average scores
    """
    return await service.get_period_statistics(period_id, current_user)


@router.get(
    "/teacher/{teacher_id}/period/{period_id}/summary",
    response_model=TeacherEvaluationSummary,
    summary="Get teacher evaluation summary",
)
async def get_teacher_summary(
    teacher_id: int,
    period_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service),
):
    """
    Get teacher evaluation summary for specific period.

    Includes:
    - Total and completed aspects
    - Scores and final grade
    - Completion percentage
    """
    return await service.get_teacher_summary(teacher_id, period_id, current_user)
