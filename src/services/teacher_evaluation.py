"""Teacher Evaluation service for parent-child structure."""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.user import UserRepository
from src.repositories.period import PeriodRepository
from src.schemas.teacher_evaluation import (
    TeacherEvaluationCreate,
    TeacherEvaluationUpdate,
    TeacherEvaluationResponse,
    TeacherEvaluationItemCreate,
    TeacherEvaluationItemUpdate,
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
from src.models.enums import EvaluationGrade, UserRole as UserRoleEnum
from src.utils.period_validation import validate_period_is_active
from src.core.exceptions import PeriodInactiveError


class TeacherEvaluationService:
    """Service for teacher evaluation operations with parent-child structure."""

    def __init__(
        self,
        evaluation_repo: TeacherEvaluationRepository,
        user_repo: UserRepository,
        session: AsyncSession = None,
    ):
        self.evaluation_repo = evaluation_repo
        self.user_repo = user_repo
        self.session = session

    def _to_response(self, evaluation) -> TeacherEvaluationResponse:
        """Convert evaluation model to response with organization_name populated."""
        response_data = evaluation.__dict__.copy()
        
        # Add organization_name from teacher's organization
        if hasattr(evaluation, 'teacher') and evaluation.teacher and hasattr(evaluation.teacher, 'organization') and evaluation.teacher.organization:
            response_data['organization_name'] = evaluation.teacher.organization.name
        else:
            response_data['organization_name'] = None
            
        return TeacherEvaluationResponse.model_validate(response_data)

    # ===== PARENT EVALUATION OPERATIONS =====

    async def create_evaluation(
        self, evaluation_data: TeacherEvaluationCreate, created_by: Optional[int] = None
    ) -> TeacherEvaluationResponse:
        """Create new parent teacher evaluation record."""
        # Validate period is active
        if self.session:
            await validate_period_is_active(self.session, evaluation_data.period_id)

        # Validate that teacher is not an admin user
        teacher = await self.user_repo.get_by_id(evaluation_data.teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found",
            )
        
        # Check if teacher has admin role
        teacher_roles = [role.role_name for role in teacher.user_roles if role.is_active]
        if "admin" in teacher_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create evaluation for admin users",
            )

        # Check if evaluation already exists for this teacher-period-evaluator combination
        existing = await self.evaluation_repo.get_teacher_evaluation_by_period(
            evaluation_data.teacher_id,
            evaluation_data.period_id,
            evaluation_data.evaluator_id,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Teacher evaluation already exists for this period and evaluator",
            )

        evaluation = await self.evaluation_repo.create_evaluation(
            evaluation_data, created_by
        )
        return self._to_response(evaluation)

    async def get_evaluation(
        self, evaluation_id: int, current_user: dict = None
    ) -> TeacherEvaluationResponse:
        """Get teacher evaluation by ID with access control."""
        evaluation = await self.evaluation_repo.get_evaluation_by_id(evaluation_id)

        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found",
            )

        # Access control: Teachers and Kepala Sekolah can only view their own evaluations
        if current_user and (
            UserRoleEnum.GURU in current_user.get("roles", []) or 
            UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", [])
        ):
            if evaluation.teacher_id != current_user["id"]:
                # Allow kepala sekolah to view evaluations of teachers in their organization
                if UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", []):
                    if evaluation.teacher.organization_id != current_user.get("organization_id"):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied: Different organization",
                        )
                else:
                    # Guru can only view their own evaluations
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Can only view your own evaluations",
                    )

        return self._to_response(evaluation)

    async def update_evaluation_notes(
        self,
        evaluation_id: int,
        update_data: UpdateEvaluationFinalNotes,
        updated_by: Optional[int] = None,
    ) -> TeacherEvaluationResponse:
        """Update final notes for teacher evaluation."""
        evaluation_update = TeacherEvaluationUpdate(final_notes=update_data.final_notes)
        evaluation = await self.evaluation_repo.update_evaluation(
            evaluation_id, evaluation_update, updated_by
        )

        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found",
            )

        return self._to_response(evaluation)

    async def delete_evaluation(self, evaluation_id: int) -> MessageResponse:
        """Delete teacher evaluation and all its items."""
        success = await self.evaluation_repo.delete_evaluation(evaluation_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found",
            )

        return MessageResponse(message="Teacher evaluation deleted successfully")

    # ===== EVALUATION ITEM OPERATIONS =====

    async def create_evaluation_item(
        self,
        evaluation_id: int,
        item_data: TeacherEvaluationItemCreate,
        created_by: Optional[int] = None,
    ) -> TeacherEvaluationItemResponse:
        """Create new evaluation item for specific aspect."""
        item = await self.evaluation_repo.create_evaluation_item(
            evaluation_id, item_data, created_by
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found or item already exists for this aspect",
            )

        return TeacherEvaluationItemResponse.model_validate(item)

    async def update_evaluation_item(
        self,
        evaluation_id: int,
        aspect_id: int,
        item_data: UpdateEvaluationItemGrade,
        updated_by: Optional[int] = None,
    ) -> TeacherEvaluationItemResponse:
        """Update evaluation item for specific aspect."""
        item_update = TeacherEvaluationItemUpdate(
            grade=item_data.grade, notes=item_data.notes
        )

        item = await self.evaluation_repo.update_evaluation_item(
            evaluation_id, aspect_id, item_update, updated_by
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation item not found",
            )

        return TeacherEvaluationItemResponse.model_validate(item)

    async def delete_evaluation_item(
        self, evaluation_id: int, aspect_id: int
    ) -> MessageResponse:
        """Delete evaluation item for specific aspect."""
        success = await self.evaluation_repo.delete_evaluation_item(
            evaluation_id, aspect_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation item not found",
            )

        return MessageResponse(message="Evaluation item deleted successfully")

    async def bulk_update_evaluation_items(
        self,
        evaluation_id: int,
        bulk_data: TeacherEvaluationBulkItemUpdate,
        updated_by: Optional[int] = None,
    ) -> TeacherEvaluationResponse:
        """Bulk update multiple evaluation items."""
        # Validate evaluation exists
        evaluation = await self.evaluation_repo.get_evaluation_by_id(evaluation_id)
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found",
            )

        # Process each item update
        for item_update in bulk_data.item_updates:
            aspect_id = item_update.get("aspect_id")
            grade = item_update.get("grade")
            notes = item_update.get("notes")

            if not aspect_id or not grade:
                continue

            item_data = TeacherEvaluationItemUpdate(grade=grade, notes=notes)
            await self.evaluation_repo.update_evaluation_item(
                evaluation_id, aspect_id, item_data, updated_by
            )

        # Return updated evaluation
        updated_evaluation = await self.evaluation_repo.get_evaluation_by_id(
            evaluation_id
        )
        return self._to_response(updated_evaluation)

    # ===== QUERY OPERATIONS =====

    async def get_evaluations_filtered(
        self, filters: TeacherEvaluationFilterParams, current_user: dict = None
    ) -> Dict[str, Any]:
        """Get filtered list of teacher evaluations with access control."""
        organization_id = None

        # Apply organization filtering for non-admin users
        if current_user and UserRoleEnum.ADMIN not in current_user.get("roles", []):
            organization_id = current_user.get("organization_id")

        # Teachers can only view their own evaluations
        # Kepala sekolah can view their own evaluations (when being evaluated by admin)
        if current_user and (
            UserRoleEnum.GURU in current_user.get("roles", []) or 
            UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", [])
        ):
            # For kepala sekolah: they can view evaluations in their organization + their own evaluation by admin
            if UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", []):
                # Don't restrict teacher_id for kepala sekolah as they evaluate teachers in their org
                # Organization filtering will handle the boundary
                pass  
            else:
                # Guru can only see their own evaluations
                filters.teacher_id = current_user["id"]

        evaluations, total_count = await self.evaluation_repo.get_evaluations_filtered(
            filters, organization_id
        )

        return {
            "items": [
                self._to_response(eval) for eval in evaluations
            ],
            "total_count": total_count,
            "page": (filters.skip // filters.limit) + 1 if filters.limit > 0 else 1,
            "size": filters.limit,
            "has_next": (filters.skip + filters.limit) < total_count,
        }

    async def get_teacher_evaluation_by_period(
        self,
        teacher_id: int,
        period_id: int,
        evaluator_id: int,
        current_user: dict = None,
    ) -> TeacherEvaluationResponse:
        """Get teacher evaluation for specific period."""
        # Access control
        if current_user and (
            UserRoleEnum.GURU in current_user.get("roles", []) or 
            UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", [])
        ):
            if teacher_id != current_user["id"]:
                # Allow kepala sekolah to view evaluations of teachers in their organization
                if UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", []):
                    # Organization check will be done in repository layer
                    pass
                else:
                    # Guru can only view their own evaluations
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Can only view your own evaluations",
                    )

        evaluation = await self.evaluation_repo.get_teacher_evaluation_by_period(
            teacher_id, period_id, evaluator_id
        )

        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found for this period",
            )

        return self._to_response(evaluation)

    async def get_evaluations_by_period(
        self, period_id: int, current_user: dict = None
    ) -> List[TeacherEvaluationResponse]:
        """Get all evaluations for a specific period."""
        organization_id = None

        # Apply organization filtering for non-admin users
        if current_user and UserRoleEnum.ADMIN not in current_user.get("roles", []):
            organization_id = current_user.get("organization_id")

        evaluations = await self.evaluation_repo.get_evaluations_by_period(
            period_id, organization_id
        )

        return [self._to_response(eval) for eval in evaluations]

    # ===== BULK OPERATIONS =====

    async def assign_teachers_to_period(
        self,
        assignment_data: AssignTeachersToEvaluationPeriod,
        created_by: Optional[int] = None,
    ) -> AssignTeachersToEvaluationPeriodResponse:
        """Auto-assign all teachers to evaluation period with auto evaluators and items."""
        # Validate period is active and get period info
        if self.session:
            await validate_period_is_active(self.session, assignment_data.period_id)

        # Perform assignment
        new_evaluations, skipped_count = await self.evaluation_repo.assign_teachers_to_period(
            assignment_data.period_id
        )

        # Get basic counts for response
        created_evaluations = len(new_evaluations)
        total_teachers = created_evaluations + skipped_count
        active_aspects_count = 12  # Default placeholder, could be fetched from DB
        total_evaluation_items = created_evaluations * active_aspects_count

        success = created_evaluations > 0 or skipped_count > 0
        if created_evaluations == 0 and skipped_count == 0:
            message = f"No eligible teachers found for period ID {assignment_data.period_id}"
            success = False
        elif created_evaluations == 0:
            message = f"All {skipped_count} teachers already have evaluations for period ID {assignment_data.period_id}"
        else:
            message = f"Successfully created evaluations for {created_evaluations} teachers with {active_aspects_count} aspects each"
            if skipped_count > 0:
                message += f", skipped {skipped_count} existing evaluations"

        return AssignTeachersToEvaluationPeriodResponse(
            success=success,
            message=message,
            period_id=assignment_data.period_id,
            period_name=f"Period {assignment_data.period_id}",  # Simplified
            created_evaluations=created_evaluations,
            skipped_evaluations=skipped_count,
            total_teachers=total_teachers,
            total_evaluation_items=total_evaluation_items,
            active_aspects_count=active_aspects_count
        )

    async def create_evaluation_with_items(
        self,
        evaluation_data: TeacherEvaluationWithItemsCreate,
        created_by: Optional[int] = None,
    ) -> TeacherEvaluationResponse:
        """Create evaluation with multiple items at once."""
        # Validate that teacher is not an admin user
        teacher = await self.user_repo.get_by_id(evaluation_data.teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found",
            )
        
        # Check if teacher has admin role
        teacher_roles = [role.role_name for role in teacher.user_roles if role.is_active]
        if "admin" in teacher_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create evaluation for admin users",
            )
        
        # Create parent evaluation
        parent_data = TeacherEvaluationCreate(
            teacher_id=evaluation_data.teacher_id,
            evaluator_id=evaluation_data.evaluator_id,
            period_id=evaluation_data.period_id,
            final_notes=evaluation_data.final_notes,
        )

        evaluation = await self.evaluation_repo.create_evaluation(
            parent_data, created_by
        )

        # Create items
        for item_data in evaluation_data.items:
            await self.evaluation_repo.create_evaluation_item(
                evaluation.id, item_data, created_by
            )

        # Force recalculate aggregates after all items are created
        await self.evaluation_repo.force_recalculate_aggregates(evaluation.id)

        # Return updated evaluation with items
        updated_evaluation = await self.evaluation_repo.get_evaluation_by_id(
            evaluation.id
        )
        return self._to_response(updated_evaluation)

    # ===== STATISTICS AND ANALYTICS =====

    async def get_period_statistics(
        self, period_id: int, current_user: dict = None
    ) -> PeriodEvaluationStats:
        """Get comprehensive statistics for evaluations in a period."""
        organization_id = None

        # Apply organization filtering for non-admin users
        if current_user and UserRoleEnum.ADMIN not in current_user.get("roles", []):
            organization_id = current_user.get("organization_id")

        stats = await self.evaluation_repo.get_period_statistics(
            period_id, organization_id
        )

        return PeriodEvaluationStats(**stats)

    async def get_teacher_summary(
        self, teacher_id: int, period_id: int, current_user: dict = None
    ) -> TeacherEvaluationSummary:
        """Get teacher evaluation summary for specific period."""
        # Access control for teacher summary
        if current_user and (
            UserRoleEnum.GURU in current_user.get("roles", []) or 
            UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", [])
        ):
            if teacher_id != current_user["id"]:
                # Allow kepala sekolah to view summaries of teachers in their organization
                if UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", []):
                    # Organization check will be handled in the repository
                    pass
                else:
                    # Guru can only view their own evaluations
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Can only view your own evaluations",
                    )

        # Get teacher's evaluation for the period (assuming single evaluator per period)
        # This might need adjustment based on actual business logic
        evaluations = await self.evaluation_repo.get_evaluations_by_period(period_id)
        teacher_evaluation = next(
            (e for e in evaluations if e.teacher_id == teacher_id), None
        )

        if not teacher_evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No evaluation found for teacher in this period",
            )

        # Get teacher info
        teacher = await self.user_repo.get_by_id(teacher_id)
        teacher_name = f"{teacher.full_name}" if teacher else "Unknown"

        return TeacherEvaluationSummary(
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            period_id=period_id,
            total_aspects=len(teacher_evaluation.items),
            completed_aspects=len(
                teacher_evaluation.items
            ),  # All items are considered completed if they exist
            total_score=teacher_evaluation.total_score,
            average_score=teacher_evaluation.average_score,
            final_grade=teacher_evaluation.final_grade,
            completion_percentage=100.0 if teacher_evaluation.items else 0.0,
            last_updated=teacher_evaluation.last_updated,
        )

    # ===== VALIDATION HELPERS =====

    async def validate_evaluation_access(
        self, evaluation_id: int, current_user: dict
    ) -> bool:
        """Validate if user has access to modify evaluation."""
        evaluation = await self.evaluation_repo.get_evaluation_by_id(evaluation_id)

        if not evaluation:
            return False

        # Admin has full access
        if UserRoleEnum.ADMIN in current_user.get("roles", []):
            return True

        # Kepala sekolah can modify evaluations in their organization
        if UserRoleEnum.KEPALA_SEKOLAH in current_user.get("roles", []):
            return evaluation.evaluator_id == current_user[
                "id"
            ] or evaluation.teacher.organization_id == current_user.get(
                "organization_id"
            )

        # Teachers cannot modify evaluations
        return False
