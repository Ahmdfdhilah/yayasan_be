"""EvaluationResult repository for PKG system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, or_, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.evaluation_result import EvaluationResult
from src.models.user import User
from src.models.teacher_evaluation import TeacherEvaluation
from src.schemas.evaluation_result import EvaluationResultCreate, EvaluationResultUpdate
from src.schemas.filters import EvaluationResultFilterParams


class EvaluationResultRepository:
    """Repository for evaluation result operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, result_data: EvaluationResultCreate) -> EvaluationResult:
        """Create new evaluation result."""
        result = EvaluationResult(
            teacher_id=result_data.teacher_id,
            evaluator_id=result_data.evaluator_id,
            academic_year=result_data.academic_year,
            semester=result_data.semester,
            total_score=result_data.total_score,
            max_score=result_data.max_score,
            performance_value=result_data.performance_value,
            grade_category=result_data.grade_category,
            recommendations=result_data.recommendations
        )
        
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result
    
    async def create_from_evaluations(
        self,
        teacher_id: int,
        evaluator_id: int,
        academic_year: str,
        semester: str,
        evaluation_ids: List[int],
        recommendations: Optional[str] = None
    ) -> EvaluationResult:
        """Create evaluation result from individual evaluations."""
        # Get the evaluations with aspects
        evaluations_query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.aspect)
        ).where(
            and_(
                TeacherEvaluation.id.in_(evaluation_ids),
                TeacherEvaluation.teacher_id == teacher_id,
                TeacherEvaluation.academic_year == academic_year,
                TeacherEvaluation.semester == semester,
                TeacherEvaluation.deleted_at.is_(None)
            )
        )
        evaluations_result = await self.session.execute(evaluations_query)
        evaluations = evaluations_result.scalars().all()
        
        if not evaluations:
            raise ValueError("No valid evaluations found for the given parameters")
        
        # Calculate total scores
        total_score = sum(eval.score for eval in evaluations)
        max_score = sum(eval.aspect.max_score for eval in evaluations)
        
        # Create result using the factory method
        result = EvaluationResult.create_from_evaluations(
            teacher_id=teacher_id,
            evaluator_id=evaluator_id,
            academic_year=academic_year,
            semester=semester,
            total_score=total_score,
            max_score=max_score,
            recommendations=recommendations
        )
        
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result
    
    async def get_by_id(self, result_id: int) -> Optional[EvaluationResult]:
        """Get evaluation result by ID with relationships."""
        query = select(EvaluationResult).options(
            selectinload(EvaluationResult.teacher),
            selectinload(EvaluationResult.evaluator)
        ).where(
            and_(EvaluationResult.id == result_id, EvaluationResult.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, result_id: int, result_data: EvaluationResultUpdate) -> Optional[EvaluationResult]:
        """Update evaluation result."""
        result = await self.get_by_id(result_id)
        if not result:
            return None
        
        # Update scores if provided
        if result_data.total_score is not None and result_data.max_score is not None:
            result.update_scores(result_data.total_score, result_data.max_score)
        
        # Update recommendations if provided
        if result_data.recommendations is not None:
            result.add_recommendations(result_data.recommendations)
        
        result.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(result)
        return result
    
    async def soft_delete(self, result_id: int) -> bool:
        """Soft delete evaluation result."""
        query = (
            update(EvaluationResult)
            .where(EvaluationResult.id == result_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== LISTING AND FILTERING =====
    
    async def get_all_results_filtered(self, filters: EvaluationResultFilterParams) -> Tuple[List[EvaluationResult], int]:
        """Get evaluation results with filters and pagination."""
        # Base query with eager loading
        query = select(EvaluationResult).options(
            selectinload(EvaluationResult.teacher),
            selectinload(EvaluationResult.evaluator)
        ).where(EvaluationResult.deleted_at.is_(None))
        count_query = select(func.count(EvaluationResult.id)).where(EvaluationResult.deleted_at.is_(None))
        
        # Join with users for search if needed
        if filters.q:
            query = query.join(User, EvaluationResult.teacher_id == User.id, isouter=True)
            count_query = count_query.join(User, EvaluationResult.teacher_id == User.id, isouter=True)
            
            search_filter = or_(
                User.email.ilike(f"%{filters.q}%"),
                func.json_unquote(func.json_extract(User.profile, "$.name")).ilike(f"%{filters.q}%"),
                EvaluationResult.recommendations.ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Apply filters
        if filters.teacher_id:
            query = query.where(EvaluationResult.teacher_id == filters.teacher_id)
            count_query = count_query.where(EvaluationResult.teacher_id == filters.teacher_id)
        
        if filters.evaluator_id:
            query = query.where(EvaluationResult.evaluator_id == filters.evaluator_id)
            count_query = count_query.where(EvaluationResult.evaluator_id == filters.evaluator_id)
        
        if filters.academic_year:
            query = query.where(EvaluationResult.academic_year == filters.academic_year)
            count_query = count_query.where(EvaluationResult.academic_year == filters.academic_year)
        
        if filters.semester:
            query = query.where(EvaluationResult.semester == filters.semester)
            count_query = count_query.where(EvaluationResult.semester == filters.semester)
        
        if filters.grade_category:
            query = query.where(EvaluationResult.grade_category == filters.grade_category)
            count_query = count_query.where(EvaluationResult.grade_category == filters.grade_category)
        
        if filters.min_performance is not None:
            query = query.where(EvaluationResult.performance_value >= filters.min_performance)
            count_query = count_query.where(EvaluationResult.performance_value >= filters.min_performance)
        
        if filters.max_performance is not None:
            query = query.where(EvaluationResult.performance_value <= filters.max_performance)
            count_query = count_query.where(EvaluationResult.performance_value <= filters.max_performance)
        
        if filters.min_score_percentage is not None:
            # Calculate score percentage filter
            min_score_decimal = filters.min_score_percentage / 100
            query = query.where(
                (EvaluationResult.total_score.cast(Decimal) / EvaluationResult.max_score.cast(Decimal)) >= min_score_decimal
            )
            count_query = count_query.where(
                (EvaluationResult.total_score.cast(Decimal) / EvaluationResult.max_score.cast(Decimal)) >= min_score_decimal
            )
        
        if filters.has_recommendations is not None:
            if filters.has_recommendations:
                query = query.where(EvaluationResult.recommendations.is_not(None))
                count_query = count_query.where(EvaluationResult.recommendations.is_not(None))
            else:
                query = query.where(EvaluationResult.recommendations.is_(None))
                count_query = count_query.where(EvaluationResult.recommendations.is_(None))
        
        if filters.evaluated_after:
            query = query.where(EvaluationResult.evaluation_date >= filters.evaluated_after)
            count_query = count_query.where(EvaluationResult.evaluation_date >= filters.evaluated_after)
        
        if filters.evaluated_before:
            query = query.where(EvaluationResult.evaluation_date <= filters.evaluated_before)
            count_query = count_query.where(EvaluationResult.evaluation_date <= filters.evaluated_before)
        
        if filters.excellent_only:
            query = query.where(EvaluationResult.performance_value >= 90)
            count_query = count_query.where(EvaluationResult.performance_value >= 90)
        
        if filters.needs_improvement_only:
            query = query.where(EvaluationResult.performance_value < 70)
            count_query = count_query.where(EvaluationResult.performance_value < 70)
        
        if filters.created_after:
            query = query.where(EvaluationResult.created_at >= filters.created_after)
            count_query = count_query.where(EvaluationResult.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(EvaluationResult.created_at <= filters.created_before)
            count_query = count_query.where(EvaluationResult.created_at <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "teacher_name":
            query = query.join(User, EvaluationResult.teacher_id == User.id)
            sort_column = func.json_unquote(func.json_extract(User.profile, "$.name"))
        elif filters.sort_by == "academic_year":
            sort_column = EvaluationResult.academic_year
        elif filters.sort_by == "semester":
            sort_column = EvaluationResult.semester
        elif filters.sort_by == "performance_value":
            sort_column = EvaluationResult.performance_value
        elif filters.sort_by == "grade_category":
            sort_column = EvaluationResult.grade_category
        elif filters.sort_by == "evaluation_date":
            sort_column = EvaluationResult.evaluation_date
        elif filters.sort_by == "created_at":
            sort_column = EvaluationResult.created_at
        elif filters.sort_by == "updated_at":
            sort_column = EvaluationResult.updated_at
        else:
            sort_column = EvaluationResult.evaluation_date
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        results = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(results), total
    
    async def get_teacher_results(self, teacher_id: int, academic_year: Optional[str] = None) -> List[EvaluationResult]:
        """Get all results for a specific teacher."""
        query = select(EvaluationResult).options(
            selectinload(EvaluationResult.teacher),
            selectinload(EvaluationResult.evaluator)
        ).where(
            and_(
                EvaluationResult.teacher_id == teacher_id,
                EvaluationResult.deleted_at.is_(None)
            )
        )
        
        if academic_year:
            query = query.where(EvaluationResult.academic_year == academic_year)
        
        query = query.order_by(desc(EvaluationResult.evaluation_date))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_results_by_period(self, academic_year: str, semester: str) -> List[EvaluationResult]:
        """Get all results for a specific academic period."""
        query = select(EvaluationResult).options(
            selectinload(EvaluationResult.teacher),
            selectinload(EvaluationResult.evaluator)
        ).where(
            and_(
                EvaluationResult.academic_year == academic_year,
                EvaluationResult.semester == semester,
                EvaluationResult.deleted_at.is_(None)
            )
        ).order_by(EvaluationResult.performance_value.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== LOOKUP METHODS =====
    
    async def find_existing_result(
        self,
        teacher_id: int,
        academic_year: str,
        semester: str
    ) -> Optional[EvaluationResult]:
        """Find existing result for teacher in academic period."""
        query = select(EvaluationResult).where(
            and_(
                EvaluationResult.teacher_id == teacher_id,
                EvaluationResult.academic_year == academic_year,
                EvaluationResult.semester == semester,
                EvaluationResult.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_latest_result_for_teacher(self, teacher_id: int) -> Optional[EvaluationResult]:
        """Get the most recent evaluation result for a teacher."""
        query = select(EvaluationResult).options(
            selectinload(EvaluationResult.teacher),
            selectinload(EvaluationResult.evaluator)
        ).where(
            and_(
                EvaluationResult.teacher_id == teacher_id,
                EvaluationResult.deleted_at.is_(None)
            )
        ).order_by(desc(EvaluationResult.evaluation_date)).limit(1)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_update_recommendations(self, result_ids: List[int], recommendations: str) -> int:
        """Bulk update recommendations for multiple results."""
        query = (
            update(EvaluationResult)
            .where(EvaluationResult.id.in_(result_ids))
            .values(
                recommendations=recommendations,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def recalculate_result(self, result_id: int) -> Optional[EvaluationResult]:
        """Recalculate evaluation result based on latest evaluations."""
        result = await self.get_by_id(result_id)
        if not result:
            return None
        
        # Get all evaluations for this teacher in the same period
        evaluations_query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.aspect)
        ).where(
            and_(
                TeacherEvaluation.teacher_id == result.teacher_id,
                TeacherEvaluation.academic_year == result.academic_year,
                TeacherEvaluation.semester == result.semester,
                TeacherEvaluation.deleted_at.is_(None)
            )
        )
        evaluations_result = await self.session.execute(evaluations_query)
        evaluations = evaluations_result.scalars().all()
        
        if evaluations:
            # Recalculate scores
            total_score = sum(eval.score for eval in evaluations)
            max_score = sum(eval.aspect.max_score for eval in evaluations)
            result.update_scores(total_score, max_score)
            
            await self.session.commit()
            await self.session.refresh(result)
        
        return result
    
    # ===== ANALYTICS AND STATISTICS =====
    
    async def get_results_analytics(self) -> Dict[str, Any]:
        """Get comprehensive results analytics."""
        base_filter = EvaluationResult.deleted_at.is_(None)
        
        # Total results
        total_query = select(func.count(EvaluationResult.id)).where(base_filter)
        total_result = await self.session.execute(total_query)
        total_results = total_result.scalar()
        
        # Unique teachers and evaluators
        teachers_query = select(func.count(func.distinct(EvaluationResult.teacher_id))).where(base_filter)
        teachers_result = await self.session.execute(teachers_query)
        unique_teachers = teachers_result.scalar()
        
        evaluators_query = select(func.count(func.distinct(EvaluationResult.evaluator_id))).where(base_filter)
        evaluators_result = await self.session.execute(evaluators_query)
        unique_evaluators = evaluators_result.scalar()
        
        # Average performance
        avg_performance_query = select(func.avg(EvaluationResult.performance_value)).where(base_filter)
        avg_performance_result = await self.session.execute(avg_performance_query)
        avg_performance = avg_performance_result.scalar()
        
        # Grade distribution
        grade_dist_query = (
            select(EvaluationResult.grade_category, func.count(EvaluationResult.id))
            .where(base_filter)
            .group_by(EvaluationResult.grade_category)
        )
        grade_dist_result = await self.session.execute(grade_dist_query)
        grade_distribution = dict(grade_dist_result.fetchall())
        
        # Performance distribution (ranges)
        performance_ranges = {
            "90-100": 0,
            "80-89": 0, 
            "70-79": 0,
            "60-69": 0,
            "Below 60": 0
        }
        
        perf_dist_query = select(EvaluationResult.performance_value).where(base_filter)
        perf_dist_result = await self.session.execute(perf_dist_query)
        performance_values = perf_dist_result.scalars().all()
        
        for value in performance_values:
            value = float(value)
            if value >= 90:
                performance_ranges["90-100"] += 1
            elif value >= 80:
                performance_ranges["80-89"] += 1
            elif value >= 70:
                performance_ranges["70-79"] += 1
            elif value >= 60:
                performance_ranges["60-69"] += 1
            else:
                performance_ranges["Below 60"] += 1
        
        # Results by academic period
        period_query = (
            select(
                EvaluationResult.academic_year,
                EvaluationResult.semester,
                func.count(EvaluationResult.id)
            )
            .where(base_filter)
            .group_by(EvaluationResult.academic_year, EvaluationResult.semester)
            .order_by(EvaluationResult.academic_year.desc(), EvaluationResult.semester.desc())
        )
        period_result = await self.session.execute(period_query)
        results_by_period = {
            f"{year}-{semester}": count
            for year, semester, count in period_result.fetchall()
        }
        
        return {
            "total_results": total_results,
            "unique_teachers": unique_teachers,
            "unique_evaluators": unique_evaluators,
            "avg_performance_value": float(avg_performance) if avg_performance else 0.0,
            "performance_distribution": performance_ranges,
            "grade_distribution": grade_distribution,
            "results_by_period": results_by_period
        }
    
    async def get_teacher_performance_trend(self, teacher_id: int, limit: int = 10) -> List[EvaluationResult]:
        """Get performance trend for a teacher over time."""
        query = select(EvaluationResult).options(
            selectinload(EvaluationResult.evaluator)
        ).where(
            and_(
                EvaluationResult.teacher_id == teacher_id,
                EvaluationResult.deleted_at.is_(None)
            )
        ).order_by(desc(EvaluationResult.evaluation_date)).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_top_performers(self, academic_year: str, semester: str, limit: int = 10) -> List[EvaluationResult]:
        """Get top performing teachers for a period."""
        query = select(EvaluationResult).options(
            selectinload(EvaluationResult.teacher),
            selectinload(EvaluationResult.evaluator)
        ).where(
            and_(
                EvaluationResult.academic_year == academic_year,
                EvaluationResult.semester == semester,
                EvaluationResult.deleted_at.is_(None)
            )
        ).order_by(desc(EvaluationResult.performance_value)).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_improvement_needed(self, academic_year: str, semester: str, threshold: float = 70.0) -> List[EvaluationResult]:
        """Get teachers who need improvement (below threshold)."""
        query = select(EvaluationResult).options(
            selectinload(EvaluationResult.teacher),
            selectinload(EvaluationResult.evaluator)
        ).where(
            and_(
                EvaluationResult.academic_year == academic_year,
                EvaluationResult.semester == semester,
                EvaluationResult.performance_value < threshold,
                EvaluationResult.deleted_at.is_(None)
            )
        ).order_by(EvaluationResult.performance_value.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())