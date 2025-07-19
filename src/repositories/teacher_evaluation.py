"""TeacherEvaluation repository for PKG system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, or_, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.teacher_evaluation import TeacherEvaluation
from src.models.evaluation_aspect import EvaluationAspect
from src.models.user import User
from src.schemas.teacher_evaluation import TeacherEvaluationCreate, TeacherEvaluationUpdate
from src.schemas.filters import TeacherEvaluationFilterParams


class TeacherEvaluationRepository:
    """Repository for teacher evaluation operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, evaluation_data: TeacherEvaluationCreate) -> TeacherEvaluation:
        """Create new teacher evaluation."""
        evaluation = TeacherEvaluation(
            evaluator_id=evaluation_data.evaluator_id,
            teacher_id=evaluation_data.teacher_id,
            aspect_id=evaluation_data.aspect_id,
            academic_year=evaluation_data.academic_year,
            semester=evaluation_data.semester,
            score=evaluation_data.score,
            notes=evaluation_data.notes
        )
        
        self.session.add(evaluation)
        await self.session.commit()
        await self.session.refresh(evaluation)
        return evaluation
    
    async def get_by_id(self, evaluation_id: int) -> Optional[TeacherEvaluation]:
        """Get teacher evaluation by ID with relationships."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.teacher),
            selectinload(TeacherEvaluation.aspect)
        ).where(
            and_(TeacherEvaluation.id == evaluation_id, TeacherEvaluation.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, evaluation_id: int, evaluation_data: TeacherEvaluationUpdate) -> Optional[TeacherEvaluation]:
        """Update teacher evaluation."""
        evaluation = await self.get_by_id(evaluation_id)
        if not evaluation:
            return None
        
        # Update score if provided
        if evaluation_data.score is not None:
            evaluation.update_score(evaluation_data.score, evaluation_data.notes)
        elif evaluation_data.notes is not None:
            evaluation.add_notes(evaluation_data.notes)
        
        evaluation.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(evaluation)
        return evaluation
    
    async def soft_delete(self, evaluation_id: int) -> bool:
        """Soft delete teacher evaluation."""
        query = (
            update(TeacherEvaluation)
            .where(TeacherEvaluation.id == evaluation_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== LISTING AND FILTERING =====
    
    async def get_all_evaluations_filtered(self, filters: TeacherEvaluationFilterParams) -> Tuple[List[TeacherEvaluation], int]:
        """Get teacher evaluations with filters and pagination."""
        # Base query with eager loading
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.teacher),
            selectinload(TeacherEvaluation.aspect)
        ).where(TeacherEvaluation.deleted_at.is_(None))
        count_query = select(func.count(TeacherEvaluation.id)).where(TeacherEvaluation.deleted_at.is_(None))
        
        # Join with related tables for search if needed
        if filters.q:
            query = query.join(User, TeacherEvaluation.teacher_id == User.id, isouter=True)
            query = query.join(EvaluationAspect, TeacherEvaluation.aspect_id == EvaluationAspect.id, isouter=True)
            count_query = count_query.join(User, TeacherEvaluation.teacher_id == User.id, isouter=True)
            count_query = count_query.join(EvaluationAspect, TeacherEvaluation.aspect_id == EvaluationAspect.id, isouter=True)
            
            search_filter = or_(
                User.email.ilike(f"%{filters.q}%"),
                func.json_extract_path_text(User.profile, 'name').ilike(f"%{filters.q}%"),
                EvaluationAspect.aspect_name.ilike(f"%{filters.q}%"),
                TeacherEvaluation.notes.ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Apply filters
        if filters.evaluator_id:
            query = query.where(TeacherEvaluation.evaluator_id == filters.evaluator_id)
            count_query = count_query.where(TeacherEvaluation.evaluator_id == filters.evaluator_id)
        
        if filters.teacher_id:
            query = query.where(TeacherEvaluation.teacher_id == filters.teacher_id)
            count_query = count_query.where(TeacherEvaluation.teacher_id == filters.teacher_id)
        
        if filters.aspect_id:
            query = query.where(TeacherEvaluation.aspect_id == filters.aspect_id)
            count_query = count_query.where(TeacherEvaluation.aspect_id == filters.aspect_id)
        
        if filters.academic_year:
            query = query.where(TeacherEvaluation.academic_year == filters.academic_year)
            count_query = count_query.where(TeacherEvaluation.academic_year == filters.academic_year)
        
        if filters.semester:
            query = query.where(TeacherEvaluation.semester == filters.semester)
            count_query = count_query.where(TeacherEvaluation.semester == filters.semester)
        
        if filters.min_score is not None:
            query = query.where(TeacherEvaluation.score >= filters.min_score)
            count_query = count_query.where(TeacherEvaluation.score >= filters.min_score)
        
        if filters.max_score is not None:
            query = query.where(TeacherEvaluation.score <= filters.max_score)
            count_query = count_query.where(TeacherEvaluation.score <= filters.max_score)
        
        if filters.has_notes is not None:
            if filters.has_notes:
                query = query.where(TeacherEvaluation.notes.is_not(None))
                count_query = count_query.where(TeacherEvaluation.notes.is_not(None))
            else:
                query = query.where(TeacherEvaluation.notes.is_(None))
                count_query = count_query.where(TeacherEvaluation.notes.is_(None))
        
        if filters.evaluated_after:
            query = query.where(TeacherEvaluation.evaluation_date >= filters.evaluated_after)
            count_query = count_query.where(TeacherEvaluation.evaluation_date >= filters.evaluated_after)
        
        if filters.evaluated_before:
            query = query.where(TeacherEvaluation.evaluation_date <= filters.evaluated_before)
            count_query = count_query.where(TeacherEvaluation.evaluation_date <= filters.evaluated_before)
        
        if filters.created_after:
            query = query.where(TeacherEvaluation.created_at >= filters.created_after)
            count_query = count_query.where(TeacherEvaluation.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(TeacherEvaluation.created_at <= filters.created_before)
            count_query = count_query.where(TeacherEvaluation.created_at <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "teacher_name":
            query = query.join(User, TeacherEvaluation.teacher_id == User.id)
            sort_column = func.json_extract_path_text(User.profile, 'name')
        elif filters.sort_by == "aspect_name":
            query = query.join(EvaluationAspect, TeacherEvaluation.aspect_id == EvaluationAspect.id)
            sort_column = EvaluationAspect.aspect_name
        elif filters.sort_by == "academic_year":
            sort_column = TeacherEvaluation.academic_year
        elif filters.sort_by == "semester":
            sort_column = TeacherEvaluation.semester
        elif filters.sort_by == "score":
            sort_column = TeacherEvaluation.score
        elif filters.sort_by == "evaluation_date":
            sort_column = TeacherEvaluation.evaluation_date
        elif filters.sort_by == "created_at":
            sort_column = TeacherEvaluation.created_at
        elif filters.sort_by == "updated_at":
            sort_column = TeacherEvaluation.updated_at
        else:
            sort_column = TeacherEvaluation.evaluation_date
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        evaluations = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(evaluations), total
    
    async def get_teacher_evaluations(
        self,
        teacher_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[TeacherEvaluation]:
        """Get all evaluations for a specific teacher."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.aspect)
        ).where(
            and_(
                TeacherEvaluation.teacher_id == teacher_id,
                TeacherEvaluation.deleted_at.is_(None)
            )
        )
        
        if academic_year:
            query = query.where(TeacherEvaluation.academic_year == academic_year)
        
        if semester:
            query = query.where(TeacherEvaluation.semester == semester)
        
        query = query.order_by(desc(TeacherEvaluation.evaluation_date))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_evaluations_by_period(
        self,
        academic_year: str,
        semester: str,
        evaluator_id: Optional[int] = None
    ) -> List[TeacherEvaluation]:
        """Get evaluations for a specific academic period."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.teacher),
            selectinload(TeacherEvaluation.aspect)
        ).where(
            and_(
                TeacherEvaluation.academic_year == academic_year,
                TeacherEvaluation.semester == semester,
                TeacherEvaluation.deleted_at.is_(None)
            )
        )
        
        if evaluator_id:
            query = query.where(TeacherEvaluation.evaluator_id == evaluator_id)
        
        query = query.order_by(TeacherEvaluation.teacher_id, TeacherEvaluation.aspect_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_evaluations_by_aspect(self, aspect_id: int) -> List[TeacherEvaluation]:
        """Get all evaluations for a specific aspect."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.teacher),
            selectinload(TeacherEvaluation.aspect)
        ).where(
            and_(
                TeacherEvaluation.aspect_id == aspect_id,
                TeacherEvaluation.deleted_at.is_(None)
            )
        ).order_by(desc(TeacherEvaluation.evaluation_date))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== LOOKUP METHODS =====
    
    async def find_existing_evaluation(
        self,
        teacher_id: int,
        aspect_id: int,
        academic_year: str,
        semester: str
    ) -> Optional[TeacherEvaluation]:
        """Find existing evaluation for teacher-aspect-period combination."""
        query = select(TeacherEvaluation).where(
            and_(
                TeacherEvaluation.teacher_id == teacher_id,
                TeacherEvaluation.aspect_id == aspect_id,
                TeacherEvaluation.academic_year == academic_year,
                TeacherEvaluation.semester == semester,
                TeacherEvaluation.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_teacher_period_evaluations(
        self,
        teacher_id: int,
        academic_year: str,
        semester: str
    ) -> List[TeacherEvaluation]:
        """Get all evaluations for a teacher in a specific period."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.aspect)
        ).where(
            and_(
                TeacherEvaluation.teacher_id == teacher_id,
                TeacherEvaluation.academic_year == academic_year,
                TeacherEvaluation.semester == semester,
                TeacherEvaluation.deleted_at.is_(None)
            )
        ).order_by(TeacherEvaluation.aspect_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_create(self, evaluations_data: List[TeacherEvaluationCreate]) -> List[TeacherEvaluation]:
        """Bulk create teacher evaluations."""
        evaluations = []
        for eval_data in evaluations_data:
            evaluation = TeacherEvaluation(
                evaluator_id=eval_data.evaluator_id,
                teacher_id=eval_data.teacher_id,
                aspect_id=eval_data.aspect_id,
                academic_year=eval_data.academic_year,
                semester=eval_data.semester,
                score=eval_data.score,
                notes=eval_data.notes
            )
            evaluations.append(evaluation)
            self.session.add(evaluation)
        
        await self.session.commit()
        
        # Refresh all evaluations
        for evaluation in evaluations:
            await self.session.refresh(evaluation)
        
        # Eagerly load relationships for all evaluations
        evaluation_ids = [eval.id for eval in evaluations]
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.teacher),
            selectinload(TeacherEvaluation.aspect)
        ).where(TeacherEvaluation.id.in_(evaluation_ids))
        
        result = await self.session.execute(query)
        evaluations_with_relations = result.scalars().all()
        
        return evaluations_with_relations
    
    async def bulk_update_scores(self, evaluation_ids: List[int], score: int, notes: Optional[str] = None) -> int:
        """Bulk update evaluation scores."""
        query = (
            update(TeacherEvaluation)
            .where(TeacherEvaluation.id.in_(evaluation_ids))
            .values(
                score=score,
                notes=notes,
                evaluation_date=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def create_evaluation_set(
        self,
        evaluator_id: int,
        teacher_id: int,
        academic_year: str,
        semester: str,
        aspect_scores: Dict[int, Dict[str, Any]]
    ) -> List[TeacherEvaluation]:
        """Create a complete set of evaluations for a teacher."""
        evaluations = []
        
        for aspect_id, score_data in aspect_scores.items():
            # Check if evaluation already exists
            existing = await self.find_existing_evaluation(
                teacher_id, aspect_id, academic_year, semester
            )
            
            if existing:
                # Update existing evaluation
                existing.update_score(score_data['score'], score_data.get('notes'))
                existing.updated_at = datetime.utcnow()
                evaluations.append(existing)
            else:
                # Create new evaluation
                evaluation = TeacherEvaluation(
                    evaluator_id=evaluator_id,
                    teacher_id=teacher_id,
                    aspect_id=aspect_id,
                    academic_year=academic_year,
                    semester=semester,
                    score=score_data['score'],
                    notes=score_data.get('notes')
                )
                self.session.add(evaluation)
                evaluations.append(evaluation)
        
        await self.session.commit()
        
        # Refresh all evaluations
        for evaluation in evaluations:
            await self.session.refresh(evaluation)
        
        return evaluations
    
    # ===== ANALYTICS AND AGGREGATION =====
    
    async def get_teacher_evaluation_summary(
        self,
        teacher_id: int,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """Get comprehensive evaluation summary for a teacher."""
        evaluations = await self.get_teacher_period_evaluations(teacher_id, academic_year, semester)
        
        if not evaluations:
            return {
                "teacher_id": teacher_id,
                "academic_year": academic_year,
                "semester": semester,
                "total_score": 0,
                "max_possible_score": 0,
                "weighted_total": Decimal("0.00"),
                "aspect_count": 0,
                "completion_status": "not_started",
                "aspect_scores": []
            }
        
        total_score = sum(eval.score for eval in evaluations)
        max_possible_score = sum(eval.aspect.max_score for eval in evaluations)
        weighted_total = sum(eval.get_weighted_score() for eval in evaluations)
        
        aspect_scores = []
        for eval in evaluations:
            aspect_scores.append({
                "aspect_id": eval.aspect_id,
                "aspect_name": eval.aspect.aspect_name,
                "score": eval.score,
                "max_score": eval.aspect.max_score,
                "weight": float(eval.aspect.weight),
                "weighted_score": eval.get_weighted_score(),
                "notes": eval.notes,
                "evaluation_date": eval.evaluation_date
            })
        
        # Determine completion status
        completion_status = "completed"
        if len(evaluations) == 0:
            completion_status = "not_started"
        else:
            # Check if all required aspects are evaluated
            # This would need business logic to determine required aspects
            completion_status = "partial"  # Simplified for now
        
        return {
            "teacher_id": teacher_id,
            "academic_year": academic_year,
            "semester": semester,
            "total_score": total_score,
            "max_possible_score": max_possible_score,
            "weighted_total": float(weighted_total),
            "aspect_count": len(evaluations),
            "completion_status": completion_status,
            "aspect_scores": aspect_scores
        }
    
    async def get_evaluations_analytics(self) -> Dict[str, Any]:
        """Get comprehensive evaluations analytics."""
        base_filter = TeacherEvaluation.deleted_at.is_(None)
        
        # Total evaluations
        total_query = select(func.count(TeacherEvaluation.id)).where(base_filter)
        total_result = await self.session.execute(total_query)
        total_evaluations = total_result.scalar()
        
        # Unique teachers and evaluators
        teachers_query = select(func.count(func.distinct(TeacherEvaluation.teacher_id))).where(base_filter)
        teachers_result = await self.session.execute(teachers_query)
        unique_teachers = teachers_result.scalar()
        
        evaluators_query = select(func.count(func.distinct(TeacherEvaluation.evaluator_id))).where(base_filter)
        evaluators_result = await self.session.execute(evaluators_query)
        unique_evaluators = evaluators_result.scalar()
        
        # Average score
        avg_score_query = select(func.avg(TeacherEvaluation.score)).where(base_filter)
        avg_score_result = await self.session.execute(avg_score_query)
        avg_score = avg_score_result.scalar()
        
        # Score distribution
        score_dist_query = (
            select(TeacherEvaluation.score, func.count(TeacherEvaluation.id))
            .where(base_filter)
            .group_by(TeacherEvaluation.score)
            .order_by(TeacherEvaluation.score)
        )
        score_dist_result = await self.session.execute(score_dist_query)
        score_distribution = {str(score): count for score, count in score_dist_result.fetchall()}
        
        # Evaluations by period
        period_query = (
            select(
                TeacherEvaluation.academic_year,
                TeacherEvaluation.semester,
                func.count(TeacherEvaluation.id)
            )
            .where(base_filter)
            .group_by(TeacherEvaluation.academic_year, TeacherEvaluation.semester)
            .order_by(TeacherEvaluation.academic_year.desc(), TeacherEvaluation.semester.desc())
        )
        period_result = await self.session.execute(period_query)
        evaluations_by_period = {
            f"{year}-{semester}": count
            for year, semester, count in period_result.fetchall()
        }
        
        # Evaluations by aspect
        aspect_query = (
            select(EvaluationAspect.aspect_name, func.count(TeacherEvaluation.id))
            .join(EvaluationAspect, TeacherEvaluation.aspect_id == EvaluationAspect.id)
            .where(base_filter)
            .group_by(EvaluationAspect.aspect_name)
            .order_by(func.count(TeacherEvaluation.id).desc())
        )
        aspect_result = await self.session.execute(aspect_query)
        evaluations_by_aspect = dict(aspect_result.fetchall())
        
        # Evaluator activity - using subquery approach
        evaluator_counts_query = (
            select(
                TeacherEvaluation.evaluator_id,
                func.count(TeacherEvaluation.id).label("evaluation_count")
            )
            .where(base_filter)
            .group_by(TeacherEvaluation.evaluator_id)
            .order_by(func.count(TeacherEvaluation.id).desc())
        )
        evaluator_counts_result = await self.session.execute(evaluator_counts_query)
        evaluator_counts = evaluator_counts_result.fetchall()
        
        # Get evaluator names separately
        evaluator_activity = {}
        for evaluator_id, count in evaluator_counts:
            user_query = select(User.profile).where(User.id == evaluator_id)
            user_result = await self.session.execute(user_query)
            user_profile = user_result.scalar_one_or_none()
            evaluator_name = user_profile.get('name', 'Unknown') if user_profile else 'Unknown'
            evaluator_activity[evaluator_name] = count
        
        return {
            "total_evaluations": total_evaluations,
            "unique_teachers": unique_teachers,
            "unique_evaluators": unique_evaluators,
            "avg_score_overall": float(avg_score) if avg_score else 0.0,
            "score_distribution": score_distribution,
            "evaluations_by_period": evaluations_by_period,
            "evaluations_by_aspect": evaluations_by_aspect,
            "evaluator_activity": evaluator_activity
        }
    
    async def get_aspect_performance_analysis(self, aspect_id: int) -> Dict[str, Any]:
        """Get detailed performance analysis for a specific aspect."""
        evaluations = await self.get_evaluations_by_aspect(aspect_id)
        
        if not evaluations:
            return {
                "aspect_id": aspect_id,
                "total_evaluations": 0,
                "avg_score": 0.0,
                "min_score": 0,
                "max_score": 0,
                "score_distribution": {},
                "top_performers": [],
                "improvement_needed": []
            }
        
        scores = [eval.score for eval in evaluations]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        # Score distribution
        score_counts = {}
        for score in scores:
            score_counts[score] = score_counts.get(score, 0) + 1
        
        # Top performers (highest scores)
        top_evaluations = sorted(evaluations, key=lambda e: e.score, reverse=True)[:5]
        top_performers = [
            {
                "teacher_id": eval.teacher_id,
                "teacher_name": eval.teacher.display_name if eval.teacher else "Unknown",
                "score": eval.score,
                "evaluation_date": eval.evaluation_date
            }
            for eval in top_evaluations
        ]
        
        # Teachers needing improvement (lowest scores)
        bottom_evaluations = sorted(evaluations, key=lambda e: e.score)[:5]
        improvement_needed = [
            {
                "teacher_id": eval.teacher_id,
                "teacher_name": eval.teacher.display_name if eval.teacher else "Unknown",
                "score": eval.score,
                "evaluation_date": eval.evaluation_date,
                "notes": eval.notes
            }
            for eval in bottom_evaluations
        ]
        
        return {
            "aspect_id": aspect_id,
            "total_evaluations": len(evaluations),
            "avg_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "score_distribution": score_counts,
            "top_performers": top_performers,
            "improvement_needed": improvement_needed
        }
    
    async def get_teacher_performance_trend(self, teacher_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get performance trend for a teacher over time."""
        query = select(
            TeacherEvaluation.academic_year,
            TeacherEvaluation.semester,
            func.avg(TeacherEvaluation.score).label("avg_score"),
            func.count(TeacherEvaluation.id).label("evaluation_count"),
            func.max(TeacherEvaluation.evaluation_date).label("latest_evaluation")
        ).where(
            and_(
                TeacherEvaluation.teacher_id == teacher_id,
                TeacherEvaluation.deleted_at.is_(None)
            )
        ).group_by(
            TeacherEvaluation.academic_year,
            TeacherEvaluation.semester
        ).order_by(
            TeacherEvaluation.academic_year.desc(),
            TeacherEvaluation.semester.desc()
        ).limit(limit)
        
        result = await self.session.execute(query)
        trend_data = []
        
        for row in result.fetchall():
            trend_data.append({
                "academic_year": row.academic_year,
                "semester": row.semester,
                "avg_score": float(row.avg_score),
                "evaluation_count": row.evaluation_count,
                "latest_evaluation": row.latest_evaluation
            })
        
        return trend_data