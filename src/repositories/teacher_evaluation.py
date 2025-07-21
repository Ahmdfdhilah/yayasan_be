"""TeacherEvaluation repository for PKG system - Refactored for grade-based system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.teacher_evaluation import TeacherEvaluation
from src.models.evaluation_aspect import EvaluationAspect
from src.models.period import Period
from src.models.user import User
from src.models.enums import EvaluationGrade
from src.utils.messages import get_message
from src.schemas.teacher_evaluation import (
    TeacherEvaluationCreate, TeacherEvaluationUpdate, TeacherEvaluationFilterParams
)


class TeacherEvaluationRepository:
    """Repository for teacher evaluation operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, evaluation_data: TeacherEvaluationCreate, created_by: Optional[int] = None) -> TeacherEvaluation:
        """Create new teacher evaluation - grade-based."""
        evaluation = TeacherEvaluation(
            evaluator_id=evaluation_data.evaluator_id,
            teacher_id=evaluation_data.teacher_id,
            aspect_id=evaluation_data.aspect_id,
            period_id=evaluation_data.period_id,
            grade=evaluation_data.grade,
            notes=evaluation_data.notes,
            created_by=created_by
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
            selectinload(TeacherEvaluation.aspect),
            selectinload(TeacherEvaluation.period)
        ).where(TeacherEvaluation.id == evaluation_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, evaluation_id: int, evaluation_data: TeacherEvaluationUpdate, updated_by: Optional[int] = None) -> Optional[TeacherEvaluation]:
        """Update teacher evaluation - grade-based."""
        evaluation = await self.get_by_id(evaluation_id)
        if not evaluation:
            return None
        
        # Update grade if provided
        if evaluation_data.grade is not None:
            evaluation.update_grade(evaluation_data.grade, evaluation_data.notes)
        elif evaluation_data.notes is not None:
            evaluation.add_notes(evaluation_data.notes)
        
        if updated_by:
            evaluation.updated_by = updated_by
        
        await self.session.commit()
        await self.session.refresh(evaluation)
        return evaluation
    
    async def delete(self, evaluation_id: int) -> bool:
        """Delete teacher evaluation."""
        evaluation = await self.get_by_id(evaluation_id)
        if not evaluation:
            return False
        
        await self.session.delete(evaluation)
        await self.session.commit()
        return True
    
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
    
    
    # ===== BULK ASSIGNMENT METHODS =====
    
    async def assign_teachers_to_period(
        self,
        period_id: int,
        teacher_ids: Optional[List[int]] = None,
        aspect_ids: Optional[List[int]] = None,
        created_by: Optional[int] = None
    ) -> Tuple[int, List[str]]:
        """Bulk assign teachers to evaluation period with all aspects."""
        from src.models.user_role import UserRole
        from src.models.enums import UserRole as UserRoleEnum
        
        errors = []
        created_count = 0
        
        # Get teachers if not specified
        if teacher_ids is None:
            # Get all active teachers (users with teacher role)
            teacher_query = select(User.id).join(
                UserRole, User.id == UserRole.user_id
            ).where(
                and_(
                    UserRole.role_name == UserRoleEnum.GURU,
                    UserRole.is_active == True,
                    User.status == "active"
                )
            )
            result = await self.session.execute(teacher_query)
            teacher_ids = [row[0] for row in result.fetchall()]
        
        # Get aspects if not specified
        if aspect_ids is None:
            # Get all active aspects
            aspect_query = select(EvaluationAspect.id).where(
                EvaluationAspect.is_active == True
            )
            result = await self.session.execute(aspect_query)
            aspect_ids = [row[0] for row in result.fetchall()]
        
        # Get all existing evaluations for this period to avoid duplicates
        existing_evaluations_query = select(
            TeacherEvaluation.teacher_id,
            TeacherEvaluation.aspect_id
        ).where(TeacherEvaluation.period_id == period_id)
        
        existing_result = await self.session.execute(existing_evaluations_query)
        existing_combinations = set(existing_result.fetchall())
        
        # Get teacher organizations in bulk for evaluator assignment
        teacher_orgs_query = select(User.id, User.organization_id).where(User.id.in_(teacher_ids))
        teacher_orgs_result = await self.session.execute(teacher_orgs_query)
        teacher_org_map = dict(teacher_orgs_result.fetchall())
        
        # Get all KEPALA_SEKOLAH by organization for evaluator assignment
        kepala_sekolah_query = select(User.id, User.organization_id).join(
            UserRole, User.id == UserRole.user_id
        ).where(
            and_(
                UserRole.role_name == UserRoleEnum.KEPALA_SEKOLAH,
                UserRole.is_active == True,
                User.status == "active"
            )
        )
        kepala_result = await self.session.execute(kepala_sekolah_query)
        org_evaluator_map = {org_id: user_id for user_id, org_id in kepala_result.fetchall()}
        
        # Create evaluations for each teacher-aspect combination
        skipped_count = 0
        for teacher_id in teacher_ids:
            # Get evaluator for this teacher
            teacher_org_id = teacher_org_map.get(teacher_id)
            evaluator_id = org_evaluator_map.get(teacher_org_id, created_by)  # Fallback to created_by
            
            for aspect_id in aspect_ids:
                # Skip if combination already exists
                if (teacher_id, aspect_id) in existing_combinations:
                    skipped_count += 1
                    continue
                
                # Create new evaluation record
                evaluation = TeacherEvaluation(
                    teacher_id=teacher_id,
                    evaluator_id=evaluator_id,  # Auto-assigned based on organization
                    aspect_id=aspect_id,
                    period_id=period_id,
                    grade=EvaluationGrade.D,  # Default grade, to be updated
                    notes="Auto-created - pending evaluation",
                    created_by=created_by
                )
                self.session.add(evaluation)
                created_count += 1
        
        # Add summary to errors if any were skipped
        if skipped_count > 0:
            errors.append(f"Skipped {skipped_count} existing teacher-aspect combinations")
        
        await self.session.commit()
        return created_count, errors
    
    async def get_evaluations_by_period(self, period_id: int) -> List[TeacherEvaluation]:
        """Get all evaluations for a specific period."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.teacher),
            selectinload(TeacherEvaluation.aspect),
            selectinload(TeacherEvaluation.period)
        ).where(TeacherEvaluation.period_id == period_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_teacher_evaluations_in_period(
        self, 
        teacher_id: int, 
        period_id: int
    ) -> List[TeacherEvaluation]:
        """Get all evaluations for a teacher in a specific period."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.teacher),
            selectinload(TeacherEvaluation.aspect),
            selectinload(TeacherEvaluation.period)
        ).where(
            and_(
                TeacherEvaluation.teacher_id == teacher_id,
                TeacherEvaluation.period_id == period_id
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def bulk_update_grades(
        self,
        evaluation_updates: List[Dict[str, Any]],
        updated_by: Optional[int] = None
    ) -> Tuple[int, List[str]]:
        """Bulk update evaluation grades."""
        updated_count = 0
        errors = []
        
        for update_data in evaluation_updates:
            evaluation_id = update_data.get('evaluation_id')
            grade = update_data.get('grade')
            notes = update_data.get('notes')
            
            evaluation = await self.get_by_id(evaluation_id)
            if not evaluation:
                errors.append(f"Evaluasi {evaluation_id} tidak ditemukan")
                continue
            
            try:
                evaluation.update_grade(EvaluationGrade(grade), notes)
                if updated_by:
                    evaluation.updated_by = updated_by
                updated_count += 1
            except Exception as e:
                errors.append(f"Gagal memperbarui evaluasi {evaluation_id}: {str(e)}")
        
        await self.session.commit()
        return updated_count, errors
    
    async def get_period_statistics(self, period_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a period."""
        # Get total teachers and aspects for the period
        teacher_count_query = select(func.count(func.distinct(TeacherEvaluation.teacher_id))).where(
            TeacherEvaluation.period_id == period_id
        )
        aspect_count_query = select(func.count(func.distinct(TeacherEvaluation.aspect_id))).where(
            TeacherEvaluation.period_id == period_id
        )
        
        teacher_count_result = await self.session.execute(teacher_count_query)
        aspect_count_result = await self.session.execute(aspect_count_query)
        
        total_teachers = teacher_count_result.scalar() or 0
        total_aspects = aspect_count_result.scalar() or 0
        
        # Get grade distribution
        grade_dist_query = select(
            TeacherEvaluation.grade,
            func.count(TeacherEvaluation.id)
        ).where(
            TeacherEvaluation.period_id == period_id
        ).group_by(TeacherEvaluation.grade)
        
        grade_dist_result = await self.session.execute(grade_dist_query)
        grade_distribution = {grade.value: count for grade, count in grade_dist_result.fetchall()}
        
        # Calculate completion percentage
        total_possible = total_teachers * total_aspects
        completed_evaluations = sum(grade_distribution.values())
        completion_percentage = (completed_evaluations / total_possible * 100) if total_possible > 0 else 0
        
        # Calculate average score
        total_score = sum(EvaluationGrade.get_score(grade) * count for grade, count in grade_distribution.items())
        average_score = total_score / completed_evaluations if completed_evaluations > 0 else 0
        
        return {
            "total_teachers": total_teachers,
            "total_aspects": total_aspects,
            "total_possible_evaluations": total_possible,
            "completed_evaluations": completed_evaluations,
            "completion_percentage": completion_percentage,
            "average_score": average_score,
            "grade_distribution": grade_distribution
        }