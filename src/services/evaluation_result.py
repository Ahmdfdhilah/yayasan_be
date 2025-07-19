"""EvaluationResult service for PKG system."""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.evaluation_result import EvaluationResultRepository
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.user import UserRepository
from src.schemas.evaluation_result import (
    EvaluationResultCreate,
    EvaluationResultUpdate,
    EvaluationResultResponse,
    EvaluationResultListResponse,
    EvaluationResultSummary,
    EvaluationResultCalculateFromEvaluations,
    EvaluationResultBulkUpdate,
    EvaluationResultBulkRecalculate,
    TeacherPerformanceComparison,
    OrganizationPerformanceOverview,
    EvaluationResultAnalytics,
    PerformanceTrendAnalysis,
    SystemPerformanceReport
)
from src.schemas.filters import EvaluationResultFilterParams


class EvaluationResultService:
    """Service for evaluation result operations."""
    
    def __init__(
        self,
        result_repo: EvaluationResultRepository,
        evaluation_repo: TeacherEvaluationRepository,
        user_repo: UserRepository
    ):
        self.result_repo = result_repo
        self.evaluation_repo = evaluation_repo
        self.user_repo = user_repo
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create_result(self, result_data: EvaluationResultCreate) -> EvaluationResultResponse:
        """Create new evaluation result."""
        # Validate teacher and evaluator exist
        teacher = await self.user_repo.get_by_id(result_data.teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        evaluator = await self.user_repo.get_by_id(result_data.evaluator_id)
        if not evaluator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluator not found"
            )
        
        # Check if result already exists for this period
        existing_result = await self.result_repo.find_existing_result(
            result_data.teacher_id,
            result_data.academic_year,
            result_data.semester
        )
        
        if existing_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Evaluation result already exists for teacher in {result_data.academic_year} - {result_data.semester}"
            )
        
        result = await self.result_repo.create(result_data)
        return EvaluationResultResponse.from_evaluation_result_model(
            result, include_relations=True
        )
    
    async def create_result_from_evaluations(
        self, 
        calculation_data: EvaluationResultCalculateFromEvaluations
    ) -> EvaluationResultResponse:
        """Create evaluation result calculated from individual evaluations."""
        # Validate teacher and evaluator exist
        teacher = await self.user_repo.get_by_id(calculation_data.teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        evaluator = await self.user_repo.get_by_id(calculation_data.evaluator_id)
        if not evaluator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluator not found"
            )
        
        # Check if result already exists
        existing_result = await self.result_repo.find_existing_result(
            calculation_data.teacher_id,
            calculation_data.academic_year,
            calculation_data.semester
        )
        
        if existing_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Evaluation result already exists for teacher in {calculation_data.academic_year} - {calculation_data.semester}"
            )
        
        # Validate evaluations exist and belong to the teacher/period
        for eval_id in calculation_data.evaluation_ids:
            evaluation = await self.evaluation_repo.get_by_id(eval_id)
            if not evaluation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evaluation with ID {eval_id} not found"
                )
            
            if (evaluation.teacher_id != calculation_data.teacher_id or
                evaluation.academic_year != calculation_data.academic_year or
                evaluation.semester != calculation_data.semester):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Evaluation {eval_id} does not match teacher/period criteria"
                )
        
        result = await self.result_repo.create_from_evaluations(
            calculation_data.teacher_id,
            calculation_data.evaluator_id,
            calculation_data.academic_year,
            calculation_data.semester,
            calculation_data.evaluation_ids,
            calculation_data.recommendations
        )
        
        return EvaluationResultResponse.from_evaluation_result_model(
            result, include_relations=True
        )
    
    async def get_result_by_id(self, result_id: int) -> EvaluationResultResponse:
        """Get evaluation result by ID."""
        result = await self.result_repo.get_by_id(result_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation result not found"
            )
        
        return EvaluationResultResponse.from_evaluation_result_model(
            result, include_relations=True
        )
    
    async def update_result(
        self, 
        result_id: int, 
        result_data: EvaluationResultUpdate
    ) -> EvaluationResultResponse:
        """Update evaluation result."""
        result = await self.result_repo.get_by_id(result_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation result not found"
            )
        
        updated_result = await self.result_repo.update(result_id, result_data)
        return EvaluationResultResponse.from_evaluation_result_model(
            updated_result, include_relations=True
        )
    
    async def delete_result(self, result_id: int) -> Dict[str, str]:
        """Delete evaluation result."""
        result = await self.result_repo.get_by_id(result_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation result not found"
            )
        
        success = await self.result_repo.soft_delete(result_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete evaluation result"
            )
        
        return {"message": "Evaluation result deleted successfully"}
    
    # ===== LISTING AND FILTERING =====
    
    async def get_results(self, filters: EvaluationResultFilterParams) -> EvaluationResultListResponse:
        """Get evaluation results with filters and pagination."""
        results, total = await self.result_repo.get_all_results_filtered(filters)
        
        result_responses = [
            EvaluationResultResponse.from_evaluation_result_model(
                result, include_relations=True
            )
            for result in results
        ]
        
        return EvaluationResultListResponse(
            items=result_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size
        )
    
    async def get_teacher_results(
        self, 
        teacher_id: int, 
        academic_year: Optional[str] = None
    ) -> List[EvaluationResultResponse]:
        """Get all results for a specific teacher."""
        # Validate teacher exists
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        results = await self.result_repo.get_teacher_results(teacher_id, academic_year)
        
        return [
            EvaluationResultResponse.from_evaluation_result_model(
                result, include_relations=True
            )
            for result in results
        ]
    
    async def get_results_by_period(
        self, 
        academic_year: str, 
        semester: str
    ) -> List[EvaluationResultResponse]:
        """Get all results for a specific academic period."""
        results = await self.result_repo.get_results_by_period(academic_year, semester)
        
        return [
            EvaluationResultResponse.from_evaluation_result_model(
                result, include_relations=True
            )
            for result in results
        ]
    
    async def get_latest_result_for_teacher(self, teacher_id: int) -> EvaluationResultResponse:
        """Get the most recent evaluation result for a teacher."""
        # Validate teacher exists
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        result = await self.result_repo.get_latest_result_for_teacher(teacher_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No evaluation results found for teacher"
            )
        
        return EvaluationResultResponse.from_evaluation_result_model(
            result, include_relations=True
        )
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_update_recommendations(self, bulk_data: EvaluationResultBulkUpdate) -> Dict[str, Any]:
        """Bulk update recommendations for multiple results."""
        # Validate result IDs exist
        for result_id in bulk_data.result_ids:
            result = await self.result_repo.get_by_id(result_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evaluation result with ID {result_id} not found"
                )
        
        if bulk_data.recommendations is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recommendations field is required for bulk update"
            )
        
        updated_count = await self.result_repo.bulk_update_recommendations(
            bulk_data.result_ids,
            bulk_data.recommendations
        )
        
        return {
            "message": f"Successfully updated recommendations for {updated_count} results",
            "updated_count": updated_count
        }
    
    async def bulk_recalculate_results(self, bulk_data: EvaluationResultBulkRecalculate) -> Dict[str, Any]:
        """Bulk recalculate evaluation results."""
        recalculated_count = 0
        errors = []
        
        for result_id in bulk_data.result_ids:
            try:
                result = await self.result_repo.get_by_id(result_id)
                if not result:
                    errors.append(f"Result {result_id} not found")
                    continue
                
                if bulk_data.use_latest_evaluations:
                    recalculated_result = await self.result_repo.recalculate_result(result_id)
                    if recalculated_result:
                        recalculated_count += 1
                    else:
                        errors.append(f"Failed to recalculate result {result_id}")
                        
            except Exception as e:
                errors.append(f"Error recalculating result {result_id}: {str(e)}")
        
        return {
            "message": f"Recalculated {recalculated_count} results",
            "recalculated_count": recalculated_count,
            "errors": errors
        }
    
    # ===== PERFORMANCE ANALYSIS =====
    
    async def get_teacher_performance_comparison(
        self, 
        teacher_id: int, 
        current_year: str, 
        current_semester: str
    ) -> TeacherPerformanceComparison:
        """Get performance comparison for a teacher."""
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Get current period result
        current_result = await self.result_repo.find_existing_result(
            teacher_id, current_year, current_semester
        )
        
        if not current_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No evaluation result found for {current_year} - {current_semester}"
            )
        
        # Get performance trend to find previous period
        trend_data = await self.result_repo.get_teacher_performance_trend(teacher_id, 2)
        previous_result = None
        
        if len(trend_data) > 1:
            previous_result = trend_data[1]  # Second most recent
        
        # Calculate performance change
        performance_change = None
        trend = "stable"
        
        if previous_result:
            performance_change = current_result.performance_value - previous_result.performance_value
            if performance_change > 5:
                trend = "improvement"
            elif performance_change < -5:
                trend = "decline"
        
        current_summary = EvaluationResultSummary.from_evaluation_result_model(current_result)
        previous_summary = None
        if previous_result:
            previous_summary = EvaluationResultSummary.from_evaluation_result_model(previous_result)
        
        return TeacherPerformanceComparison(
            teacher_id=teacher_id,
            teacher_name=teacher.display_name,
            current_period=current_summary,
            previous_period=previous_summary,
            performance_change=performance_change,
            trend=trend,
            rank_in_organization=None,  # Would need additional calculation
            percentile=None  # Would need additional calculation
        )
    
    async def get_organization_performance_overview(
        self, 
        academic_year: str, 
        semester: str,
        organization_id: Optional[int] = None
    ) -> OrganizationPerformanceOverview:
        """Get organization-wide performance overview."""
        results = await self.result_repo.get_results_by_period(academic_year, semester)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No evaluation results found for {academic_year} - {semester}"
            )
        
        # Filter by organization if specified
        if organization_id:
            # This would need to join with user organization data
            # For now, we'll work with all results
            pass
        
        total_teachers = len(set(result.teacher_id for result in results))
        evaluated_teachers = len(results)
        completion_rate = (evaluated_teachers / total_teachers * 100) if total_teachers > 0 else 0
        
        # Calculate performance metrics
        performance_values = [float(result.performance_value) for result in results]
        avg_performance = sum(performance_values) / len(performance_values) if performance_values else 0
        median_performance = sorted(performance_values)[len(performance_values) // 2] if performance_values else 0
        
        # Grade distribution
        grade_distribution = {}
        for result in results:
            grade = result.grade_category
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        # Get top/bottom performers (simplified)
        sorted_results = sorted(results, key=lambda r: r.performance_value, reverse=True)
        
        top_performers = []
        for result in sorted_results[:5]:
            comparison = await self.get_teacher_performance_comparison(
                result.teacher_id, academic_year, semester
            )
            top_performers.append(comparison)
        
        bottom_performers = []
        for result in sorted_results[-5:]:
            comparison = await self.get_teacher_performance_comparison(
                result.teacher_id, academic_year, semester
            )
            bottom_performers.append(comparison)
        
        return OrganizationPerformanceOverview(
            organization_id=organization_id,
            organization_name=None,  # Would need organization lookup
            academic_year=academic_year,
            semester=semester,
            total_teachers=total_teachers,
            evaluated_teachers=evaluated_teachers,
            completion_rate=Decimal(str(completion_rate)),
            avg_performance_value=Decimal(str(avg_performance)),
            median_performance_value=Decimal(str(median_performance)),
            grade_distribution=grade_distribution,
            top_performers=top_performers,
            bottom_performers=bottom_performers,
            most_improved=[],  # Would need historical comparison
            most_declined=[]   # Would need historical comparison
        )
    
    # ===== ANALYTICS =====
    
    async def get_results_analytics(self, organization_id: Optional[int] = None) -> EvaluationResultAnalytics:
        """Get comprehensive results analytics."""
        analytics_data = await self.result_repo.get_results_analytics(organization_id)
        
        return EvaluationResultAnalytics(
            total_results=analytics_data["total_results"],
            unique_teachers=analytics_data["unique_teachers"],
            unique_evaluators=analytics_data["unique_evaluators"],
            avg_performance_value=Decimal(str(analytics_data["avg_performance_value"])),
            performance_distribution=analytics_data["performance_distribution"],
            grade_distribution=analytics_data["grade_distribution"],
            results_by_period=analytics_data["results_by_period"],
            score_trends={},  # Would need time-series calculation
            improvement_rate=Decimal("0.0")  # Would need historical comparison
        )
    
    async def get_teacher_performance_trend(self, teacher_id: int, limit: int = 10) -> PerformanceTrendAnalysis:
        """Get performance trend analysis for a teacher."""
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        trend_results = await self.result_repo.get_teacher_performance_trend(teacher_id, limit)
        
        if not trend_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No evaluation results found for teacher"
            )
        
        # Convert to summaries
        historical_results = [
            EvaluationResultSummary.from_evaluation_result_model(result)
            for result in trend_results
        ]
        
        # Calculate trend metrics (simplified)
        performance_values = [float(result.performance_value) for result in trend_results]
        
        if len(performance_values) >= 2:
            # Simple trend calculation
            first_half_avg = sum(performance_values[:len(performance_values)//2]) / (len(performance_values)//2)
            second_half_avg = sum(performance_values[len(performance_values)//2:]) / (len(performance_values) - len(performance_values)//2)
            
            if second_half_avg > first_half_avg + 5:
                trend_direction = "improving"
            elif second_half_avg < first_half_avg - 5:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"
        
        # Calculate consistency (standard deviation)
        if len(performance_values) > 1:
            mean_val = sum(performance_values) / len(performance_values)
            variance = sum((x - mean_val) ** 2 for x in performance_values) / len(performance_values)
            std_dev = variance ** 0.5
            consistency_score = max(0, 100 - (std_dev * 10))  # Normalize to 0-100
        else:
            consistency_score = 100
        
        return PerformanceTrendAnalysis(
            teacher_id=teacher_id,
            teacher_name=teacher.display_name,
            historical_results=historical_results,
            trend_direction=trend_direction,
            trend_strength=Decimal("0.5"),  # Would need proper correlation calculation
            projected_next_performance=None,  # Would need prediction model
            consistency_score=Decimal(str(consistency_score)),
            volatility=Decimal(str(std_dev if len(performance_values) > 1 else 0))
        )
    
    async def get_top_performers(
        self, 
        academic_year: str, 
        semester: str, 
        limit: int = 10
    ) -> List[EvaluationResultResponse]:
        """Get top performing teachers for a period."""
        top_results = await self.result_repo.get_top_performers(academic_year, semester, limit)
        
        return [
            EvaluationResultResponse.from_evaluation_result_model(
                result, include_relations=True
            )
            for result in top_results
        ]
    
    async def get_improvement_needed(
        self, 
        academic_year: str, 
        semester: str, 
        threshold: float = 70.0
    ) -> List[EvaluationResultResponse]:
        """Get teachers who need improvement."""
        improvement_results = await self.result_repo.get_improvement_needed(
            academic_year, semester, threshold
        )
        
        return [
            EvaluationResultResponse.from_evaluation_result_model(
                result, include_relations=True
            )
            for result in improvement_results
        ]