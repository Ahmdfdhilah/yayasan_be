"""TeacherEvaluation service for PKG system."""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.evaluation_aspect import EvaluationAspectRepository
from src.repositories.user import UserRepository
from src.schemas.teacher_evaluation import (
    TeacherEvaluationCreate,
    TeacherEvaluationUpdate,
    TeacherEvaluationResponse,
    TeacherEvaluationListResponse,
    TeacherEvaluationSummary,
    TeacherEvaluationBulkCreate,
    TeacherEvaluationBulkUpdate,
    TeacherEvaluationBulkDelete,
    TeacherEvaluationAggregated,
    EvaluationPeriodSummary,
    TeacherEvaluationAnalytics,
    TeacherPerformanceReport,
    EvaluationSystemStats
)
from src.schemas.filters import TeacherEvaluationFilterParams


class TeacherEvaluationService:
    """Service for teacher evaluation operations."""
    
    def __init__(
        self,
        evaluation_repo: TeacherEvaluationRepository,
        aspect_repo: EvaluationAspectRepository,
        user_repo: UserRepository
    ):
        self.evaluation_repo = evaluation_repo
        self.aspect_repo = aspect_repo
        self.user_repo = user_repo
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create_evaluation(self, evaluation_data: TeacherEvaluationCreate) -> TeacherEvaluationResponse:
        """Create new teacher evaluation."""
        # Validate teacher exists
        teacher = await self.user_repo.get_by_id(evaluation_data.teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Validate evaluator exists
        evaluator = await self.user_repo.get_by_id(evaluation_data.evaluator_id)
        if not evaluator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluator not found"
            )
        
        # Validate aspect exists and is active
        aspect = await self.aspect_repo.get_by_id(evaluation_data.aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation aspect not found"
            )
        
        if not aspect.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot evaluate using inactive aspect"
            )
        
        # Validate score is within aspect range
        if not aspect.is_score_valid(evaluation_data.score):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Score {evaluation_data.score} is not valid for aspect '{aspect.aspect_name}'. Valid range: {aspect.score_range}"
            )
        
        # Check if evaluation already exists for this combination
        existing_evaluation = await self.evaluation_repo.find_existing_evaluation(
            evaluation_data.teacher_id,
            evaluation_data.aspect_id,
            evaluation_data.academic_year,
            evaluation_data.semester
        )
        
        if existing_evaluation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Evaluation already exists for this teacher-aspect-period combination"
            )
        
        evaluation = await self.evaluation_repo.create(evaluation_data)
        return TeacherEvaluationResponse.from_teacher_evaluation_model(
            evaluation, include_relations=True
        )
    
    async def get_evaluation_by_id(self, evaluation_id: int) -> TeacherEvaluationResponse:
        """Get teacher evaluation by ID."""
        evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found"
            )
        
        return TeacherEvaluationResponse.from_teacher_evaluation_model(
            evaluation, include_relations=True
        )
    
    async def update_evaluation(
        self, 
        evaluation_id: int, 
        evaluation_data: TeacherEvaluationUpdate
    ) -> TeacherEvaluationResponse:
        """Update teacher evaluation."""
        evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found"
            )
        
        # Validate new score if provided
        if evaluation_data.score is not None:
            aspect = await self.aspect_repo.get_by_id(evaluation.aspect_id)
            if aspect and not aspect.is_score_valid(evaluation_data.score):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Score {evaluation_data.score} is not valid for aspect '{aspect.aspect_name}'. Valid range: {aspect.score_range}"
                )
        
        updated_evaluation = await self.evaluation_repo.update(evaluation_id, evaluation_data)
        return TeacherEvaluationResponse.from_teacher_evaluation_model(
            updated_evaluation, include_relations=True
        )
    
    async def delete_evaluation(self, evaluation_id: int) -> Dict[str, str]:
        """Delete teacher evaluation."""
        evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher evaluation not found"
            )
        
        success = await self.evaluation_repo.soft_delete(evaluation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete teacher evaluation"
            )
        
        return {"message": "Teacher evaluation deleted successfully"}
    
    # ===== LISTING AND FILTERING =====
    
    async def get_evaluations(self, filters: TeacherEvaluationFilterParams) -> TeacherEvaluationListResponse:
        """Get teacher evaluations with filters and pagination."""
        evaluations, total = await self.evaluation_repo.get_all_evaluations_filtered(filters)
        
        evaluation_responses = [
            TeacherEvaluationResponse.from_teacher_evaluation_model(
                evaluation, include_relations=True
            )
            for evaluation in evaluations
        ]
        
        return TeacherEvaluationListResponse(
            items=evaluation_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size
        )
    
    async def get_teacher_evaluations(
        self, 
        teacher_id: int, 
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[TeacherEvaluationResponse]:
        """Get all evaluations for a specific teacher."""
        # Validate teacher exists
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        evaluations = await self.evaluation_repo.get_teacher_evaluations(
            teacher_id, academic_year, semester
        )
        
        return [
            TeacherEvaluationResponse.from_teacher_evaluation_model(
                evaluation, include_relations=True
            )
            for evaluation in evaluations
        ]
    
    async def get_evaluations_by_period(
        self, 
        academic_year: str, 
        semester: str,
        evaluator_id: Optional[int] = None
    ) -> List[TeacherEvaluationResponse]:
        """Get evaluations for a specific academic period."""
        if evaluator_id:
            # Validate evaluator exists
            evaluator = await self.user_repo.get_by_id(evaluator_id)
            if not evaluator:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Evaluator not found"
                )
        
        evaluations = await self.evaluation_repo.get_evaluations_by_period(
            academic_year, semester, evaluator_id
        )
        
        return [
            TeacherEvaluationResponse.from_teacher_evaluation_model(
                evaluation, include_relations=True
            )
            for evaluation in evaluations
        ]
    
    async def get_evaluations_by_aspect(self, aspect_id: int) -> List[TeacherEvaluationResponse]:
        """Get all evaluations for a specific aspect."""
        # Validate aspect exists
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation aspect not found"
            )
        
        evaluations = await self.evaluation_repo.get_evaluations_by_aspect(aspect_id)
        
        return [
            TeacherEvaluationResponse.from_teacher_evaluation_model(
                evaluation, include_relations=True
            )
            for evaluation in evaluations
        ]
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_create_evaluations(self, bulk_data: TeacherEvaluationBulkCreate) -> List[TeacherEvaluationResponse]:
        """Bulk create teacher evaluations."""
        # Validate teacher and evaluator exist
        teacher = await self.user_repo.get_by_id(bulk_data.teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        evaluator = await self.user_repo.get_by_id(bulk_data.evaluator_id)
        if not evaluator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluator not found"
            )
        
        # Validate aspects and scores
        evaluation_creates = []
        for eval_data in bulk_data.evaluations:
            aspect = await self.aspect_repo.get_by_id(eval_data['aspect_id'])
            if not aspect:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evaluation aspect with ID {eval_data['aspect_id']} not found"
                )
            
            if not aspect.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot evaluate using inactive aspect '{aspect.aspect_name}'"
                )
            
            if not aspect.is_score_valid(eval_data['score']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Score {eval_data['score']} is not valid for aspect '{aspect.aspect_name}'"
                )
            
            # Check for existing evaluation
            existing = await self.evaluation_repo.find_existing_evaluation(
                bulk_data.teacher_id,
                eval_data['aspect_id'],
                bulk_data.academic_year,
                bulk_data.semester
            )
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Evaluation already exists for aspect '{aspect.aspect_name}'"
                )
            
            evaluation_create = TeacherEvaluationCreate(
                evaluator_id=bulk_data.evaluator_id,
                teacher_id=bulk_data.teacher_id,
                aspect_id=eval_data['aspect_id'],
                academic_year=bulk_data.academic_year,
                semester=bulk_data.semester,
                score=eval_data['score'],
                notes=eval_data.get('notes')
            )
            evaluation_creates.append(evaluation_create)
        
        # Create evaluations
        evaluations = await self.evaluation_repo.bulk_create(evaluation_creates)
        
        return [
            TeacherEvaluationResponse.from_teacher_evaluation_model(
                evaluation, include_relations=True
            )
            for evaluation in evaluations
        ]
    
    async def create_evaluation_set(
        self,
        evaluator_id: int,
        teacher_id: int,
        academic_year: str,
        semester: str,
        aspect_scores: Dict[int, Dict[str, Any]]
    ) -> List[TeacherEvaluationResponse]:
        """Create a complete set of evaluations for a teacher."""
        # Validate teacher and evaluator
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        evaluator = await self.user_repo.get_by_id(evaluator_id)
        if not evaluator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluator not found"
            )
        
        # Validate aspects and scores
        validated_scores = {}
        for aspect_id, score_data in aspect_scores.items():
            aspect = await self.aspect_repo.get_by_id(aspect_id)
            if not aspect:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evaluation aspect with ID {aspect_id} not found"
                )
            
            if not aspect.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot evaluate using inactive aspect '{aspect.aspect_name}'"
                )
            
            if not aspect.is_score_valid(score_data['score']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Score {score_data['score']} is not valid for aspect '{aspect.aspect_name}'"
                )
            
            validated_scores[aspect_id] = score_data
        
        # Create evaluation set
        evaluations = await self.evaluation_repo.create_evaluation_set(
            evaluator_id, teacher_id, academic_year, semester, validated_scores
        )
        
        return [
            TeacherEvaluationResponse.from_teacher_evaluation_model(
                evaluation, include_relations=True
            )
            for evaluation in evaluations
        ]
    
    async def bulk_update_evaluations(self, bulk_data: TeacherEvaluationBulkUpdate) -> Dict[str, Any]:
        """Bulk update teacher evaluations."""
        # Validate evaluation IDs exist
        for evaluation_id in bulk_data.evaluation_ids:
            evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
            if not evaluation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Teacher evaluation with ID {evaluation_id} not found"
                )
        
        if bulk_data.score is None and bulk_data.notes is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either score or notes must be provided for bulk update"
            )
        
        # Validate score if provided
        if bulk_data.score is not None:
            for evaluation_id in bulk_data.evaluation_ids:
                evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
                aspect = await self.aspect_repo.get_by_id(evaluation.aspect_id)
                
                if aspect and not aspect.is_score_valid(bulk_data.score):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Score {bulk_data.score} is not valid for aspect '{aspect.aspect_name}'"
                    )
        
        updated_count = await self.evaluation_repo.bulk_update_scores(
            bulk_data.evaluation_ids,
            bulk_data.score,
            bulk_data.notes
        )
        
        return {
            "message": f"Successfully updated {updated_count} evaluations",
            "updated_count": updated_count
        }
    
    async def bulk_delete_evaluations(self, bulk_data: TeacherEvaluationBulkDelete) -> Dict[str, Any]:
        """Bulk delete teacher evaluations."""
        deleted_count = 0
        errors = []
        
        for evaluation_id in bulk_data.evaluation_ids:
            try:
                evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
                if not evaluation:
                    errors.append(f"Evaluation {evaluation_id} not found")
                    continue
                
                success = await self.evaluation_repo.soft_delete(evaluation_id)
                if success:
                    deleted_count += 1
                else:
                    errors.append(f"Failed to delete evaluation {evaluation_id}")
                    
            except Exception as e:
                errors.append(f"Error deleting evaluation {evaluation_id}: {str(e)}")
        
        return {
            "message": f"Deleted {deleted_count} evaluations",
            "deleted_count": deleted_count,
            "errors": errors
        }
    
    # ===== AGGREGATION AND ANALYSIS =====
    
    async def get_teacher_evaluation_summary(
        self,
        teacher_id: int,
        academic_year: str,
        semester: str
    ) -> TeacherEvaluationAggregated:
        """Get comprehensive evaluation summary for a teacher."""
        # Validate teacher exists
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        summary_data = await self.evaluation_repo.get_teacher_evaluation_summary(
            teacher_id, academic_year, semester
        )
        
        if summary_data["completion_status"] == "not_started":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No evaluations found for teacher in {academic_year} - {semester}"
            )
        
        # Calculate performance percentage (total_score / max_possible_score * 1.25)
        performance_percentage = Decimal("0.0")
        if summary_data["max_possible_score"] > 0:
            performance_percentage = (
                Decimal(str(summary_data["total_score"])) / 
                Decimal(str(summary_data["max_possible_score"])) * 
                Decimal("1.25")
            ) * Decimal("100")
        
        # Determine grade category
        if performance_percentage >= 90:
            grade_category = "Excellent"
        elif performance_percentage >= 80:
            grade_category = "Good"
        elif performance_percentage >= 70:
            grade_category = "Satisfactory"
        else:
            grade_category = "Needs Improvement"
        
        # Analyze strengths and improvements
        strengths = []
        improvements = []
        
        for aspect_score in summary_data["aspect_scores"]:
            score_percentage = (aspect_score["score"] / aspect_score["max_score"]) * 100
            if score_percentage >= 85:
                strengths.append(aspect_score["aspect_name"])
            elif score_percentage < 70:
                improvements.append(aspect_score["aspect_name"])
        
        return TeacherEvaluationAggregated(
            teacher_id=teacher_id,
            teacher_name=teacher.display_name,
            teacher_email=teacher.email,
            academic_year=academic_year,
            semester=semester,
            total_score=summary_data["total_score"],
            max_possible_score=summary_data["max_possible_score"],
            weighted_total=Decimal(str(summary_data["weighted_total"])),
            performance_percentage=performance_percentage,
            grade_category=grade_category,
            aspect_scores=summary_data["aspect_scores"],
            evaluator_name=None,  # Would need to get from evaluations
            evaluation_date=summary_data["aspect_scores"][0]["evaluation_date"] if summary_data["aspect_scores"] else None,
            score_breakdown={
                "total_score": summary_data["total_score"],
                "max_possible_score": summary_data["max_possible_score"],
                "percentage": float(performance_percentage)
            },
            strengths=strengths,
            improvements=improvements
        )
    
    async def get_period_summary(
        self,
        academic_year: str,
        semester: str
    ) -> EvaluationPeriodSummary:
        """Get evaluation period summary."""
        evaluations = await self.evaluation_repo.get_evaluations_by_period(
            academic_year, semester
        )
        
        if not evaluations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No evaluations found for {academic_year} - {semester}"
            )
        
        # Count unique teachers
        unique_teachers = set(eval.teacher_id for eval in evaluations)
        total_teachers = len(unique_teachers)
        
        # Calculate completion statistics
        teacher_evaluation_counts = {}
        for eval in evaluations:
            teacher_id = eval.teacher_id
            teacher_evaluation_counts[teacher_id] = teacher_evaluation_counts.get(teacher_id, 0) + 1
        
        # Assume we need evaluations for all active aspects
        active_aspects = await self.aspect_repo.get_active_aspects()
        required_evaluations_per_teacher = len(active_aspects)
        
        completed_teachers = sum(
            1 for count in teacher_evaluation_counts.values() 
            if count >= required_evaluations_per_teacher
        )
        
        pending_evaluations = (total_teachers * required_evaluations_per_teacher) - len(evaluations)
        completion_rate = (completed_teachers / total_teachers * 100) if total_teachers > 0 else 0
        
        # Calculate average performance (simplified)
        total_scores = []
        for teacher_id in unique_teachers:
            try:
                summary = await self.evaluation_repo.get_teacher_evaluation_summary(
                    teacher_id, academic_year, semester
                )
                if summary["max_possible_score"] > 0:
                    performance = (summary["total_score"] / summary["max_possible_score"]) * 125
                    total_scores.append(performance)
            except Exception:
                continue
        
        avg_performance = sum(total_scores) / len(total_scores) if total_scores else 0
        
        # Grade distribution (simplified)
        grade_distribution = {
            "Excellent": 0,
            "Good": 0,
            "Satisfactory": 0,
            "Needs Improvement": 0
        }
        
        for score in total_scores:
            if score >= 90:
                grade_distribution["Excellent"] += 1
            elif score >= 80:
                grade_distribution["Good"] += 1
            elif score >= 70:
                grade_distribution["Satisfactory"] += 1
            else:
                grade_distribution["Needs Improvement"] += 1
        
        return EvaluationPeriodSummary(
            academic_year=academic_year,
            semester=semester,
            total_teachers=total_teachers,
            evaluated_teachers=len(teacher_evaluation_counts),
            pending_evaluations=max(0, pending_evaluations),
            completion_rate=Decimal(str(completion_rate)),
            avg_performance_score=Decimal(str(avg_performance)),
            grade_distribution=grade_distribution,
            top_performers=[],  # Would need additional calculation
            needs_improvement=[]  # Would need additional calculation
        )
    
    # ===== ANALYTICS =====
    
    async def get_evaluations_analytics(self) -> TeacherEvaluationAnalytics:
        """Get comprehensive evaluations analytics."""
        analytics_data = await self.evaluation_repo.get_evaluations_analytics()
        
        return TeacherEvaluationAnalytics(
            total_evaluations=analytics_data["total_evaluations"],
            unique_teachers=analytics_data["unique_teachers"],
            unique_evaluators=analytics_data["unique_evaluators"],
            avg_score_overall=Decimal(str(analytics_data["avg_score_overall"])),
            score_distribution=analytics_data["score_distribution"],
            evaluations_by_period=analytics_data["evaluations_by_period"],
            evaluations_by_aspect=analytics_data["evaluations_by_aspect"],
            evaluator_activity=analytics_data["evaluator_activity"],
            recent_trends={}  # Would need time-series data
        )
    
    async def get_teacher_performance_report(self, teacher_id: int) -> TeacherPerformanceReport:
        """Get individual teacher performance report."""
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Get performance trend
        trend_data = await self.evaluation_repo.get_teacher_performance_trend(teacher_id)
        
        if not trend_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No evaluation history found for teacher"
            )
        
        # Build evaluation history
        evaluation_history = []
        for trend_item in trend_data:
            try:
                aggregated = await self.get_teacher_evaluation_summary(
                    teacher_id,
                    trend_item["academic_year"],
                    trend_item["semester"]
                )
                evaluation_history.append(aggregated)
            except Exception:
                continue
        
        # Analyze consistent strengths and weaknesses
        aspect_performance = {}
        for eval_history in evaluation_history:
            for aspect_score in eval_history.aspect_scores:
                aspect_name = aspect_score["aspect_name"]
                score_percentage = (aspect_score["score"] / aspect_score["max_score"]) * 100
                
                if aspect_name not in aspect_performance:
                    aspect_performance[aspect_name] = []
                aspect_performance[aspect_name].append(score_percentage)
        
        # Determine consistent strengths (consistently above 80%)
        aspect_strengths = []
        aspect_weaknesses = []
        
        for aspect_name, scores in aspect_performance.items():
            avg_score = sum(scores) / len(scores)
            if avg_score >= 80 and min(scores) >= 75:
                aspect_strengths.append(aspect_name)
            elif avg_score < 70 or max(scores) < 75:
                aspect_weaknesses.append(aspect_name)
        
        # Determine improvement trajectory
        if len(evaluation_history) >= 2:
            recent_avg = sum(
                float(eval.performance_percentage) 
                for eval in evaluation_history[:2]
            ) / 2
            older_avg = sum(
                float(eval.performance_percentage) 
                for eval in evaluation_history[-2:]
            ) / 2
            
            if recent_avg > older_avg + 5:
                improvement_trajectory = "Improving"
            elif recent_avg < older_avg - 5:
                improvement_trajectory = "Declining"
            else:
                improvement_trajectory = "Stable"
        else:
            improvement_trajectory = "Insufficient data"
        
        # Generate recommendations
        recommendations = []
        if aspect_weaknesses:
            recommendations.append(f"Focus on improving: {', '.join(aspect_weaknesses[:3])}")
        if len(aspect_strengths) > 0:
            recommendations.append(f"Continue excellence in: {', '.join(aspect_strengths[:3])}")
        if improvement_trajectory == "Declining":
            recommendations.append("Consider additional professional development")
        
        return TeacherPerformanceReport(
            teacher_id=teacher_id,
            teacher_name=teacher.display_name,
            teacher_email=teacher.email,
            evaluation_history=evaluation_history,
            performance_trends={},  # Would need time-series calculation
            aspect_strengths=aspect_strengths,
            aspect_weaknesses=aspect_weaknesses,
            improvement_trajectory=improvement_trajectory,
            recommendations=recommendations
        )