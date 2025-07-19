"""Teacher Evaluation service for PKG system - Refactored for grade-based system."""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.schemas.teacher_evaluation import (
    TeacherEvaluationCreate,
    TeacherEvaluationUpdate,
    TeacherEvaluationResponse,
    TeacherEvaluationBulkCreate,
    TeacherEvaluationBulkUpdate,
    AssignTeachersToPeriod,
    CompleteTeacherEvaluation,
    TeacherEvaluationSummary,
    PeriodEvaluationStats,
    TeacherEvaluationFilterParams
)
from src.schemas.shared import MessageResponse
from src.models.enums import EvaluationGrade


class TeacherEvaluationService:
    """Service for teacher evaluation operations - grade-based system."""
    
    def __init__(self, evaluation_repo: TeacherEvaluationRepository):
        self.evaluation_repo = evaluation_repo
    
    async def create_evaluation(
        self, 
        evaluation_data: TeacherEvaluationCreate,
        created_by: Optional[int] = None
    ) -> TeacherEvaluationResponse:
        """Create new teacher evaluation."""
        evaluation = await self.evaluation_repo.create(evaluation_data, created_by)
        return TeacherEvaluationResponse.from_teacher_evaluation_model(evaluation, include_relations=True)
    
    async def get_evaluation(self, evaluation_id: int) -> TeacherEvaluationResponse:
        """Get teacher evaluation by ID."""
        evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found"
            )
        
        return TeacherEvaluationResponse.from_teacher_evaluation_model(evaluation, include_relations=True)
    
    async def update_evaluation(
        self,
        evaluation_id: int,
        evaluation_data: TeacherEvaluationUpdate,
        updated_by: Optional[int] = None
    ) -> TeacherEvaluationResponse:
        """Update teacher evaluation grade."""
        evaluation = await self.evaluation_repo.update(evaluation_id, evaluation_data, updated_by)
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found"
            )
        
        return TeacherEvaluationResponse.from_teacher_evaluation_model(evaluation, include_relations=True)
    
    async def delete_evaluation(self, evaluation_id: int) -> MessageResponse:
        """Delete teacher evaluation."""
        success = await self.evaluation_repo.delete(evaluation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found"
            )
        
        return MessageResponse(message="Teacher evaluation deleted successfully")
    
    # ===== BULK ASSIGNMENT METHODS =====
    
    async def assign_teachers_to_period(
        self,
        assignment_data: AssignTeachersToPeriod,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Bulk assign all teachers to evaluation period automatically."""
        created_count, errors = await self.evaluation_repo.assign_teachers_to_period(
            period_id=assignment_data.period_id,
            teacher_ids=None,  # Auto-assign all teachers with GURU role
            aspect_ids=None,   # Auto-assign all active aspects
            created_by=created_by
        )
        
        return {
            "created_count": created_count,
            "errors": errors,
            "message": f"Successfully assigned {created_count} evaluations"
        }
    
    async def get_evaluations_by_period(self, period_id: int) -> List[TeacherEvaluationResponse]:
        """Get all evaluations for a specific period."""
        evaluations = await self.evaluation_repo.get_evaluations_by_period(period_id)
        return [
            TeacherEvaluationResponse.from_teacher_evaluation_model(eval, include_relations=True)
            for eval in evaluations
        ]
    
    async def get_teacher_evaluations_in_period(
        self,
        teacher_id: int,
        period_id: int
    ) -> List[TeacherEvaluationResponse]:
        """Get all evaluations for a teacher in a specific period."""
        evaluations = await self.evaluation_repo.get_teacher_evaluations_in_period(teacher_id, period_id)
        return [
            TeacherEvaluationResponse.from_teacher_evaluation_model(eval, include_relations=True)
            for eval in evaluations
        ]
    
    async def bulk_update_grades(
        self,
        bulk_update_data: TeacherEvaluationBulkUpdate,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Bulk update evaluation grades."""
        updated_count, errors = await self.evaluation_repo.bulk_update_grades(
            bulk_update_data.evaluations,
            updated_by
        )
        
        return {
            "updated_count": updated_count,
            "errors": errors,
            "message": f"Successfully updated {updated_count} evaluations"
        }
    
    async def complete_teacher_evaluation(
        self,
        completion_data: CompleteTeacherEvaluation,
        evaluator_id: int
    ) -> Dict[str, Any]:
        """Complete all evaluations for a teacher in a period."""
        # Get existing evaluations for the teacher in the period
        evaluations = await self.evaluation_repo.get_teacher_evaluations_in_period(
            completion_data.teacher_id,
            completion_data.period_id
        )
        
        if not evaluations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No evaluations found for this teacher in the specified period"
            )
        
        # Update grades for each aspect
        updates = []
        for evaluation in evaluations:
            if evaluation.aspect_id in completion_data.evaluations:
                grade = completion_data.evaluations[evaluation.aspect_id]
                updates.append({
                    "evaluation_id": evaluation.id,
                    "grade": grade.value,
                    "notes": f"Completed by evaluator {evaluator_id}"
                })
        
        updated_count, errors = await self.evaluation_repo.bulk_update_grades(updates, evaluator_id)
        
        return {
            "updated_count": updated_count,
            "total_aspects": len(evaluations),
            "errors": errors,
            "message": f"Completed {updated_count} evaluations for teacher {completion_data.teacher_id}"
        }
    
    async def get_period_evaluation_stats(self, period_id: int) -> PeriodEvaluationStats:
        """Get comprehensive statistics for a period."""
        stats = await self.evaluation_repo.get_period_statistics(period_id)
        
        # Get teacher summaries
        evaluations = await self.evaluation_repo.get_evaluations_by_period(period_id)
        teacher_summaries = self._calculate_teacher_summaries(evaluations)
        
        return PeriodEvaluationStats(
            period_id=period_id,
            period_name=f"Period {period_id}",  # This should come from period data
            total_teachers=stats["total_teachers"],
            total_aspects=stats["total_aspects"],
            total_possible_evaluations=stats["total_possible_evaluations"],
            completed_evaluations=stats["completed_evaluations"],
            completion_percentage=stats["completion_percentage"],
            average_score=stats["average_score"],
            grade_distribution=stats["grade_distribution"],
            teacher_summaries=teacher_summaries
        )
    
    def _calculate_teacher_summaries(self, evaluations: List) -> List[TeacherEvaluationSummary]:
        """Calculate teacher evaluation summaries."""
        teacher_data = {}
        
        for eval in evaluations:
            teacher_id = eval.teacher_id
            if teacher_id not in teacher_data:
                teacher_data[teacher_id] = {
                    "teacher_id": teacher_id,
                    "teacher_name": eval.teacher.profile.get("full_name", "Unknown") if eval.teacher else "Unknown",
                    "teacher_email": eval.teacher.email if eval.teacher else "Unknown",
                    "period_id": eval.period_id,
                    "period_name": eval.period.period_name if eval.period else f"Period {eval.period_id}",
                    "evaluations": [],
                    "total_aspects": 0,
                    "completed_evaluations": 0,
                    "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0}
                }
            
            teacher_data[teacher_id]["evaluations"].append(eval)
            teacher_data[teacher_id]["total_aspects"] += 1
            
            if eval.grade:
                teacher_data[teacher_id]["completed_evaluations"] += 1
                teacher_data[teacher_id]["grade_distribution"][eval.grade.value] += 1
        
        summaries = []
        for data in teacher_data.values():
            total_score = sum(
                EvaluationGrade.get_score(grade) * count 
                for grade, count in data["grade_distribution"].items()
            )
            average_score = total_score / data["completed_evaluations"] if data["completed_evaluations"] > 0 else 0
            completion_percentage = (data["completed_evaluations"] / data["total_aspects"] * 100) if data["total_aspects"] > 0 else 0
            
            summaries.append(TeacherEvaluationSummary(
                teacher_id=data["teacher_id"],
                teacher_name=data["teacher_name"],
                teacher_email=data["teacher_email"],
                period_id=data["period_id"],
                period_name=data["period_name"],
                total_aspects=data["total_aspects"],
                completed_evaluations=data["completed_evaluations"],
                average_score=average_score,
                grade_distribution=data["grade_distribution"],
                completion_percentage=completion_percentage
            ))
        
        return summaries