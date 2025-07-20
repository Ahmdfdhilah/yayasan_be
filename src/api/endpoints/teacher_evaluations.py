"""Teacher Evaluations endpoints - Refactored for grade-based system."""

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
    TeacherEvaluationBulkUpdate,
    AssignTeachersToPeriod,
    CompleteTeacherEvaluation,
    PeriodEvaluationStats
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import (
    get_current_active_user, 
    require_roles,
    require_teacher_evaluation_view_permission,
    require_teacher_evaluation_update_permission
)
from src.models.enums import EvaluationGrade

router = APIRouter()

# Role-based permissions
admin_required = require_roles(["admin"])
admin_or_manager = require_roles(["admin", "kepala_sekolah"])


async def get_teacher_evaluation_service(session: AsyncSession = Depends(get_db)) -> TeacherEvaluationService:
    """Get teacher evaluation service dependency."""
    evaluation_repo = TeacherEvaluationRepository(session)
    user_repo = UserRepository(session)
    return TeacherEvaluationService(evaluation_repo, user_repo, session)


@router.post("/assign-teachers-to-period", summary="Automatically assign all teachers to evaluation period")
async def assign_teachers_to_period(
    assignment_data: AssignTeachersToPeriod,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Automatically assign all teachers to evaluation period with all aspects.
    
    Creates evaluation records for all teacher-aspect combinations in the period.
    - Automatically assigns ALL users with GURU role
    - Automatically assigns ALL active evaluation aspects
    - Automatically assigns evaluators (KEPALA_SEKOLAH from same organization, fallback to admin)
    - Skips existing teacher-aspect combinations (safe to run multiple times for new teachers/aspects)
    """
    return await service.assign_teachers_to_period(assignment_data, current_user["id"])


@router.get("/period/{period_id}", response_model=List[TeacherEvaluationResponse], summary="Get evaluations by period")
async def get_evaluations_by_period(
    period_id: int,
    current_user: dict = Depends(require_teacher_evaluation_view_permission()),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Get all evaluations for a specific period.
    
    Teachers can only view their own evaluations. Principals can view evaluations for their organization.
    """
    return await service.get_evaluations_by_period(period_id, current_user)


@router.get("/teacher/{teacher_id}/period/{period_id}", response_model=List[TeacherEvaluationResponse], summary="Get teacher evaluations in period")
async def get_teacher_evaluations_in_period(
    teacher_id: int,
    period_id: int,
    current_user: dict = Depends(require_teacher_evaluation_view_permission()),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Get all evaluations for a teacher in a specific period.
    
    Teachers can only view their own evaluations. Principals can view evaluations for teachers in their organization.
    """
    return await service.get_teacher_evaluations_in_period(teacher_id, period_id, current_user)


@router.put("/{evaluation_id}/grade", response_model=TeacherEvaluationResponse, summary="Update evaluation grade")
async def update_evaluation_grade(
    evaluation_id: int,
    evaluation_data: TeacherEvaluationUpdate,
    current_user: dict = Depends(require_teacher_evaluation_update_permission()),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Update single evaluation grade.
    
    Only principals (kepala_sekolah) can update evaluations for teachers in their organization.
    """
    return await service.update_evaluation(evaluation_id, evaluation_data, current_user["id"], current_user)


@router.patch("/bulk-grade", summary="Bulk update evaluation grades")
async def bulk_update_grades(
    bulk_update_data: TeacherEvaluationBulkUpdate,
    current_user: dict = Depends(require_teacher_evaluation_update_permission()),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Bulk update evaluation grades.
    
    Only principals (kepala_sekolah) can update evaluations for teachers in their organization.
    """
    return await service.bulk_update_grades(bulk_update_data, current_user["id"], current_user)


@router.post("/complete-teacher-evaluation", summary="Complete all evaluations for a teacher")
async def complete_teacher_evaluation(
    completion_data: CompleteTeacherEvaluation,
    current_user: dict = Depends(require_teacher_evaluation_update_permission()),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Complete all evaluations for a teacher in a period.
    
    Only principals (kepala_sekolah) can complete evaluations for teachers in their organization.
    """
    return await service.complete_teacher_evaluation(completion_data, current_user["id"], current_user)


@router.get("/period/{period_id}/stats", response_model=PeriodEvaluationStats, summary="Get period evaluation statistics")
async def get_period_evaluation_stats(
    period_id: int,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Get comprehensive statistics for a period.
    
    Returns detailed statistics including:
    - Completion rates
    - Grade distributions
    - Teacher summaries
    - Overall performance metrics
    """
    return await service.get_period_evaluation_stats(period_id)


# ===== BASIC CRUD OPERATIONS =====

@router.post("/", response_model=TeacherEvaluationResponse, summary="Create teacher evaluation")
async def create_teacher_evaluation(
    evaluation_data: TeacherEvaluationCreate,
    current_user: dict = Depends(admin_or_manager),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Create new teacher evaluation.
    
    Creates a single evaluation record for a teacher-aspect-period combination.
    """
    return await service.create_evaluation(evaluation_data, current_user["id"])


@router.get("/{evaluation_id}", response_model=TeacherEvaluationResponse, summary="Get evaluation by ID")
async def get_teacher_evaluation(
    evaluation_id: int,
    current_user: dict = Depends(require_teacher_evaluation_view_permission()),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Get teacher evaluation by ID.
    
    Teachers can only view their own evaluations. Principals can view evaluations for their organization.
    """
    return await service.get_evaluation(evaluation_id, current_user)


@router.put("/{evaluation_id}", response_model=TeacherEvaluationResponse, summary="Update teacher evaluation")
async def update_teacher_evaluation(
    evaluation_id: int,
    evaluation_data: TeacherEvaluationUpdate,
    current_user: dict = Depends(require_teacher_evaluation_update_permission()),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Update teacher evaluation.
    
    Only principals (kepala_sekolah) can update evaluations for teachers in their organization.
    """
    return await service.update_evaluation(evaluation_id, evaluation_data, current_user["id"], current_user)


@router.delete("/{evaluation_id}", response_model=MessageResponse, summary="Delete teacher evaluation")
async def delete_teacher_evaluation(
    evaluation_id: int,
    current_user: dict = Depends(admin_required),
    service: TeacherEvaluationService = Depends(get_teacher_evaluation_service)
):
    """
    Delete teacher evaluation.
    
    Permanently removes an evaluation record.
    Only admins can delete evaluations.
    """
    return await service.delete_evaluation(evaluation_id)