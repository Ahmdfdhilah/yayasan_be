"""Teacher Evaluation repository for parent-child structure."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, desc, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.teacher_evaluation import TeacherEvaluation
from src.models.teacher_evaluation_item import TeacherEvaluationItem
from src.models.evaluation_aspect import EvaluationAspect
from src.models.period import Period
from src.models.user import User
from src.models.user_role import UserRole
from src.models.organization import Organization
from src.models.enums import EvaluationGrade, UserRole as UserRoleEnum
from src.schemas.teacher_evaluation import (
    TeacherEvaluationCreate, TeacherEvaluationUpdate, TeacherEvaluationFilterParams,
    TeacherEvaluationItemCreate, TeacherEvaluationItemUpdate
)


class TeacherEvaluationRepository:
    """Repository for teacher evaluation operations with parent-child structure."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _get_grade_letter(self, final_grade: float) -> str:
        """Convert float final_grade to letter grade."""
        if final_grade >= 87.5:
            return "A"
        elif final_grade >= 62.5:
            return "B"
        elif final_grade >= 37.5:
            return "C"
        else:
            return "D"
    
    # ===== PARENT EVALUATION CRUD =====
    
    async def create_evaluation(self, evaluation_data: TeacherEvaluationCreate, created_by: Optional[int] = None) -> TeacherEvaluation:
        """Create new parent teacher evaluation record."""
        evaluation = TeacherEvaluation(
            teacher_id=evaluation_data.teacher_id,
            evaluator_id=evaluation_data.evaluator_id,
            period_id=evaluation_data.period_id,
            final_notes=evaluation_data.final_notes,
            created_by=created_by
        )
        evaluation.updated_at = datetime.utcnow()
        
        self.session.add(evaluation)
        await self.session.commit()
        await self.session.refresh(evaluation)
        return evaluation
    
    async def get_evaluation_by_id(self, evaluation_id: int) -> Optional[TeacherEvaluation]:
        """Get teacher evaluation by ID with all relationships."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.teacher).selectinload(User.organization),
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.period),
            selectinload(TeacherEvaluation.items).selectinload(TeacherEvaluationItem.aspect)
        ).where(TeacherEvaluation.id == evaluation_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_evaluation(self, evaluation_id: int, update_data: TeacherEvaluationUpdate, updated_by: Optional[int] = None) -> Optional[TeacherEvaluation]:
        """Update parent teacher evaluation record."""
        evaluation = await self.get_evaluation_by_id(evaluation_id)
        if not evaluation:
            return None
        
        if update_data.final_notes is not None:
            evaluation.final_notes = update_data.final_notes
        
        evaluation.updated_by = updated_by
        evaluation.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(evaluation)
        return evaluation
    
    async def delete_evaluation(self, evaluation_id: int) -> bool:
        """Delete teacher evaluation and all its items."""
        evaluation = await self.get_evaluation_by_id(evaluation_id)
        if not evaluation:
            return False
        
        await self.session.delete(evaluation)
        await self.session.commit()
        return True
    
    # ===== EVALUATION ITEM CRUD =====
    
    async def create_evaluation_item(self, evaluation_id: int, item_data: TeacherEvaluationItemCreate, created_by: Optional[int] = None) -> Optional[TeacherEvaluationItem]:
        """Create new evaluation item for specific aspect."""
        # Check if evaluation exists
        evaluation = await self.get_evaluation_by_id(evaluation_id)
        if not evaluation:
            return None
        
        # Check if item already exists for this aspect
        existing_item = await self.get_evaluation_item_by_aspect(evaluation_id, item_data.aspect_id)
        if existing_item:
            return None  # Item already exists
        
        item = TeacherEvaluationItem(
            teacher_evaluation_id=evaluation_id,
            aspect_id=item_data.aspect_id,
            grade=item_data.grade,
            notes=item_data.notes,
            created_by=created_by
        )
        
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        
        # Recalculate parent aggregates
        await self._recalculate_evaluation_aggregates(evaluation_id)
        
        return item
    
    async def get_evaluation_item_by_aspect(self, evaluation_id: int, aspect_id: int) -> Optional[TeacherEvaluationItem]:
        """Get evaluation item by evaluation ID and aspect ID."""
        query = select(TeacherEvaluationItem).options(
            selectinload(TeacherEvaluationItem.aspect)
        ).where(
            and_(
                TeacherEvaluationItem.teacher_evaluation_id == evaluation_id,
                TeacherEvaluationItem.aspect_id == aspect_id
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_evaluation_item(self, evaluation_id: int, aspect_id: int, item_data: TeacherEvaluationItemUpdate, updated_by: Optional[int] = None) -> Optional[TeacherEvaluationItem]:
        """Update evaluation item for specific aspect."""
        item = await self.get_evaluation_item_by_aspect(evaluation_id, aspect_id)
        if not item:
            return None
        
        if item_data.grade is not None:
            item.update_grade(item_data.grade, item_data.notes)
        elif item_data.notes is not None:
            item.notes = item_data.notes
            item.evaluated_at = datetime.utcnow()
        
        item.updated_by = updated_by
        item.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        # Recalculate parent aggregates
        await self._recalculate_evaluation_aggregates(evaluation_id)
        
        await self.session.refresh(item)
        return item
    
    async def delete_evaluation_item(self, evaluation_id: int, aspect_id: int) -> bool:
        """Delete evaluation item for specific aspect."""
        item = await self.get_evaluation_item_by_aspect(evaluation_id, aspect_id)
        if not item:
            return False
        
        await self.session.delete(item)
        await self.session.commit()
        
        # Recalculate parent aggregates
        await self._recalculate_evaluation_aggregates(evaluation_id)
        
        return True
    
    # ===== QUERY METHODS =====
    
    async def get_evaluations_filtered(self, filters: TeacherEvaluationFilterParams, organization_id: Optional[int] = None) -> Tuple[List[TeacherEvaluation], int]:
        """Get filtered list of teacher evaluations with pagination."""
        base_query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.teacher).selectinload(User.organization),
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.period),
        )
        
        conditions = []
        
        # Organization filter - from passed parameter or from filters
        if organization_id:
            conditions.append(
                TeacherEvaluation.teacher.has(User.organization_id == organization_id)
            )
        elif filters.organization_id:
            conditions.append(
                TeacherEvaluation.teacher.has(User.organization_id == filters.organization_id)
            )
        
        # Apply filters
        if filters.teacher_id:
            conditions.append(TeacherEvaluation.teacher_id == filters.teacher_id)
        
        if filters.evaluator_id:
            conditions.append(TeacherEvaluation.evaluator_id == filters.evaluator_id)
        
        if filters.period_id:
            conditions.append(TeacherEvaluation.period_id == filters.period_id)
        
        # Search by teacher name
        if filters.search:
            search_term = f"%{filters.search.lower()}%"
            conditions.append(
                TeacherEvaluation.teacher.has(
                    or_(
                        func.lower(func.cast(User.profile.op('->')('name'), String)).like(search_term),
                        func.lower(User.email).like(search_term)
                    )
                )
            )
        
        if filters.final_grade:
            conditions.append(TeacherEvaluation.final_grade == filters.final_grade)
        
        if filters.min_average_score is not None:
            conditions.append(TeacherEvaluation.average_score >= filters.min_average_score)
        
        if filters.max_average_score is not None:
            conditions.append(TeacherEvaluation.average_score <= filters.max_average_score)
        
        if filters.has_final_notes is not None:
            if filters.has_final_notes:
                conditions.append(TeacherEvaluation.final_notes.isnot(None))
            else:
                conditions.append(TeacherEvaluation.final_notes.is_(None))
        
        if filters.from_date:
            conditions.append(TeacherEvaluation.last_updated >= filters.from_date)
        
        if filters.to_date:
            conditions.append(TeacherEvaluation.last_updated <= filters.to_date)
        
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # Count total (need to join User for search functionality)
        count_query = select(func.count(TeacherEvaluation.id))
        if filters.search:
            count_query = count_query.join(User, TeacherEvaluation.teacher_id == User.id)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()
        
        # Apply pagination and ordering
        query = base_query.order_by(desc(TeacherEvaluation.last_updated))
        query = query.offset(filters.skip).limit(filters.limit)
        
        result = await self.session.execute(query)
        evaluations = result.scalars().all()
        
        return list(evaluations), total_count
    
    async def get_teacher_evaluation_by_period(self, teacher_id: int, period_id: int) -> Optional[TeacherEvaluation]:
        """Get teacher evaluation for specific period."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.teacher).selectinload(User.organization),
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.period),
            selectinload(TeacherEvaluation.items).selectinload(TeacherEvaluationItem.aspect)
        ).where(
            and_(
                TeacherEvaluation.teacher_id == teacher_id,
                TeacherEvaluation.period_id == period_id
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_evaluations_by_period(self, period_id: int, organization_id: Optional[int] = None) -> List[TeacherEvaluation]:
        """Get all evaluations for a specific period."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.teacher).selectinload(User.organization),
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.period),
            selectinload(TeacherEvaluation.items).selectinload(TeacherEvaluationItem.aspect)
        ).where(TeacherEvaluation.period_id == period_id)
        
        if organization_id:
            query = query.join(TeacherEvaluation.teacher).where(User.organization_id == organization_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_evaluations_by_teacher_and_period(self, teacher_id: int, period_id: Optional[int] = None) -> List[TeacherEvaluation]:
        """Get all evaluations for a specific teacher and optionally period."""
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.teacher).selectinload(User.organization),
            selectinload(TeacherEvaluation.evaluator),
            selectinload(TeacherEvaluation.period),
            selectinload(TeacherEvaluation.items).selectinload(TeacherEvaluationItem.aspect)
        ).where(TeacherEvaluation.teacher_id == teacher_id)
        
        if period_id:
            query = query.where(TeacherEvaluation.period_id == period_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== BULK OPERATIONS =====
    
    async def assign_teachers_to_period(self, period_id: int) -> Tuple[List[TeacherEvaluation], int]:
        """Auto-assign all teachers and kepala sekolah to evaluation period.
        
        Logic matches RPP generation exactly:
        - Get ALL teachers (guru) and kepala sekolah, excluding admin users
        - Assign appropriate evaluators based on role and organization
        
        Returns:
        - Tuple[List[newly created evaluations], count of skipped existing evaluations]
        """
        new_evaluations = []
        skipped_count = 0
        
        # Get all active teachers (guru) and kepala sekolah, excluding admin users
        # This matches the exact logic from RPP generation
        admin_users_subquery = (
            select(UserRole.user_id)
            .where(
                and_(
                    UserRole.role_name == UserRoleEnum.ADMIN.value,
                    UserRole.is_active == True,
                    UserRole.deleted_at.is_(None)
                )
            )
        )
        
        teachers_query = select(User).options(
            selectinload(User.user_roles)
        ).join(
            User.user_roles.and_(
                UserRole.role_name.in_([UserRoleEnum.GURU.value, UserRoleEnum.KEPALA_SEKOLAH.value]), 
                UserRole.is_active == True
            )
        ).where(
            User.status == "active", 
            User.deleted_at.is_(None),
            # Exclude users who have admin role
            ~User.id.in_(admin_users_subquery)
        )
        
        teachers_result = await self.session.execute(teachers_query)
        teachers = teachers_result.scalars().all()
        
        # Get first admin as default evaluator
        admin_query = select(User).join(User.user_roles).where(
            User.user_roles.any(UserRole.role_name == UserRoleEnum.ADMIN.value)
        ).limit(1)
        
        admin_result = await self.session.execute(admin_query)
        default_admin_evaluator = admin_result.scalar_one_or_none()
        
        for teacher in teachers:
            # Check if evaluation already exists for this teacher in this period
            existing = await self.get_teacher_evaluation_by_period(teacher.id, period_id)
            if existing:
                skipped_count += 1
                continue
            
            # Determine evaluator based on teacher role and organization
            evaluator_id = None
            
            # Check teacher's roles
            teacher_roles = [role.role_name for role in teacher.user_roles if role.is_active]
            
            if UserRoleEnum.GURU.value in teacher_roles:
                # Teachers (guru) are evaluated by their kepala sekolah if available
                if teacher.organization_id:
                    # Find kepala sekolah in same organization
                    ks_query = select(User).join(User.user_roles).where(
                        and_(
                            User.organization_id == teacher.organization_id,
                            User.user_roles.any(UserRole.role_name == UserRoleEnum.KEPALA_SEKOLAH.value),
                            User.status == "active",
                            User.deleted_at.is_(None)
                        )
                    ).limit(1)
                    
                    ks_result = await self.session.execute(ks_query)
                    kepala_sekolah = ks_result.scalar_one_or_none()
                    
                    if kepala_sekolah:
                        evaluator_id = kepala_sekolah.id
                
                # If no kepala sekolah found, use admin as evaluator
                if not evaluator_id and default_admin_evaluator:
                    evaluator_id = default_admin_evaluator.id
                    
            elif UserRoleEnum.KEPALA_SEKOLAH.value in teacher_roles:
                # Kepala sekolah are evaluated by admin
                if default_admin_evaluator:
                    evaluator_id = default_admin_evaluator.id
            
            # Skip if no evaluator found
            if not evaluator_id:
                continue
            
            # Create new evaluation
            evaluation_data = TeacherEvaluationCreate(
                teacher_id=teacher.id,
                evaluator_id=evaluator_id,
                period_id=period_id
            )
            
            evaluation = await self.create_evaluation(evaluation_data, created_by=evaluator_id)
            
            # Always create items for all active aspects
            await self._create_items_for_all_aspects(evaluation.id, created_by=evaluator_id)
            
            new_evaluations.append(evaluation)
        
        return new_evaluations, skipped_count
    
    # ===== STATISTICS AND ANALYTICS =====
    
    async def get_period_statistics(self, period_id: int, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive statistics for evaluations in a period."""
        base_query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.items).selectinload(TeacherEvaluationItem.aspect),
            selectinload(TeacherEvaluation.teacher).selectinload(User.organization)
        ).where(TeacherEvaluation.period_id == period_id)
        
        if organization_id:
            base_query = base_query.join(TeacherEvaluation.teacher).where(User.organization_id == organization_id)
        
        # Get all evaluations with items preloaded
        evaluations_result = await self.session.execute(base_query)
        evaluations = evaluations_result.scalars().all()
        
        total_evaluations = len(evaluations)
        completed_evaluations = len([e for e in evaluations if e.item_count > 0])
        
        # Calculate statistics - filter out null values
        if evaluations:
            # Only sum evaluations that have total_score (not null)
            evaluated_evaluations = [e for e in evaluations if e.total_score is not None]
            total_score = sum(e.total_score for e in evaluated_evaluations) if evaluated_evaluations else 0
            total_aspects = sum(e.item_count for e in evaluations)
            average_score = total_score / total_aspects if total_aspects > 0 else 0.0
            
            # Grade distribution
            grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "None": 0}
            for evaluation in evaluations:
                if evaluation.final_grade:
                    grade_letter = self._get_grade_letter(evaluation.final_grade)
                    grade_distribution[grade_letter] += 1
                else:
                    grade_distribution["None"] += 1
        else:
            average_score = 0.0
            grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "None": 0}
        
        # Get unique teachers count
        teacher_ids = set(e.teacher_id for e in evaluations)
        total_teachers = len(teacher_ids)
        
        completion_percentage = (completed_evaluations / total_evaluations * 100) if total_evaluations > 0 else 0.0
        
        # Get top performers (top 5 by average score) - only include those with scores
        top_performers = []
        if evaluations:
            # Filter out evaluations with null average_score
            evaluations_with_scores = [e for e in evaluations if e.average_score is not None]
            sorted_evaluations = sorted(evaluations_with_scores, key=lambda e: e.average_score, reverse=True)[:5]
            top_performers = [
                {
                    "teacher_id": e.teacher_id,
                    "teacher_name": e.teacher.display_name if e.teacher else "Unknown",
                    "total_score": e.total_score or 0,
                    "average_score": e.average_score or 0.0,
                    "final_grade": e.final_grade or 0.0,
                    "final_grade_letter": self._get_grade_letter(e.final_grade) if e.final_grade else "None",
                    "organization_name": e.teacher.organization.name if (e.teacher and e.teacher.organization) else "Unknown"
                }
                for e in sorted_evaluations
            ]
        
        # Get aspect performance
        aspect_performance = []
        if evaluations:
            aspect_scores = {}
            aspect_counts = {}
            
            for evaluation in evaluations:
                for item in evaluation.items:
                    # Only include items with non-null scores
                    if item.score is not None:
                        aspect_name = item.aspect.aspect_name if item.aspect else f"Aspect {item.aspect_id}"
                        if aspect_name not in aspect_scores:
                            aspect_scores[aspect_name] = 0
                            aspect_counts[aspect_name] = 0
                        aspect_scores[aspect_name] += item.score
                        aspect_counts[aspect_name] += 1
            
            aspect_performance = [
                {
                    "aspect_name": aspect_name,
                    "average_score": round(aspect_scores[aspect_name] / aspect_counts[aspect_name], 2),
                    "total_evaluations": aspect_counts[aspect_name]
                }
                for aspect_name in aspect_scores.keys()
            ]
        
        return {
            "period_id": period_id,
            "total_evaluations": total_evaluations,
            "total_teachers": total_teachers,
            "completed_evaluations": completed_evaluations,
            "total_aspects_evaluated": sum(e.item_count for e in evaluations),
            "average_score": round(average_score, 2),
            "final_grade_distribution": grade_distribution,
            "completion_percentage": round(completion_percentage, 2),
            "top_performers": top_performers,
            "aspect_performance": aspect_performance,
        }
    
    # ===== PRIVATE HELPER METHODS =====
    
    async def _recalculate_evaluation_aggregates(self, evaluation_id: int) -> None:
        """Recalculate aggregates for parent evaluation."""
        # First flush any pending changes to ensure we get the latest data
        await self.session.flush()
        
        # Get the evaluation with a fresh query to ensure we have all items
        query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.items)
        ).where(TeacherEvaluation.id == evaluation_id)
        
        result = await self.session.execute(query)
        evaluation = result.scalar_one_or_none()
        
        if evaluation and evaluation.items:
            # Filter out items with null scores and calculate aggregates
            evaluated_items = [item for item in evaluation.items if item.score is not None]
            
            if evaluated_items:
                # Calculate from evaluated items only
                total_score = sum(item.score for item in evaluated_items)
                average_score = total_score / len(evaluated_items)
                final_grade = total_score * 1.25
                
                # Update the evaluation directly
                evaluation.total_score = total_score
                evaluation.average_score = average_score
                evaluation.final_grade = final_grade
            else:
                # No items evaluated yet, set to null
                evaluation.total_score = None
                evaluation.average_score = None
                evaluation.final_grade = None
            
            evaluation.last_updated = datetime.utcnow()
            evaluation.updated_at = datetime.utcnow()
            
            await self.session.commit()
            
    async def force_recalculate_aggregates(self, evaluation_id: int) -> None:
        """Force recalculate aggregates using direct SQL update."""
        # Update aggregates using SQL - only calculate from non-null scores
        # Use CASE WHEN to set NULL if no non-null scores exist
        update_query = update(TeacherEvaluation).where(
            TeacherEvaluation.id == evaluation_id
        ).values(
            total_score=(
                select(
                    func.case(
                        (func.count(TeacherEvaluationItem.score) > 0, func.sum(TeacherEvaluationItem.score)),
                        else_=None
                    )
                )
                .where(
                    and_(
                        TeacherEvaluationItem.teacher_evaluation_id == evaluation_id,
                        TeacherEvaluationItem.score.is_not(None)
                    )
                )
            ),
            average_score=(
                select(
                    func.case(
                        (func.count(TeacherEvaluationItem.score) > 0, func.avg(TeacherEvaluationItem.score)),
                        else_=None
                    )
                )
                .where(
                    and_(
                        TeacherEvaluationItem.teacher_evaluation_id == evaluation_id,
                        TeacherEvaluationItem.score.is_not(None)
                    )
                )
            ),
            final_grade=(
                select(
                    func.case(
                        (func.count(TeacherEvaluationItem.score) > 0, func.sum(TeacherEvaluationItem.score) * 1.25),
                        else_=None
                    )
                )
                .where(
                    and_(
                        TeacherEvaluationItem.teacher_evaluation_id == evaluation_id,
                        TeacherEvaluationItem.score.is_not(None)
                    )
                )
            ),
            last_updated=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self.session.execute(update_query)
        await self.session.commit()
    
    async def _create_items_for_all_aspects(self, evaluation_id: int, created_by: Optional[int] = None) -> None:
        """Create evaluation items for all active aspects."""
        # Get all active aspects
        aspects_query = select(EvaluationAspect).where(EvaluationAspect.is_active == True)
        aspects_result = await self.session.execute(aspects_query)
        aspects = aspects_result.scalars().all()
        
        for aspect in aspects:
            # Check if item already exists
            existing_item = await self.get_evaluation_item_by_aspect(evaluation_id, aspect.id)
            if not existing_item:
                # Create item with default grade C
                item = TeacherEvaluationItem(
                    teacher_evaluation_id=evaluation_id,
                    aspect_id=aspect.id,
                    grade=None,  # No default grade - starts as null
                    score=None,  # No default score - starts as null
                    created_by=created_by
                )
                item.updated_at = datetime.utcnow()
                self.session.add(item)
        
        await self.session.commit()
        await self._recalculate_evaluation_aggregates(evaluation_id)
    
    async def recalculate_all_aggregates(self) -> int:
        """Recalculate aggregates for all teacher evaluations."""
        from sqlalchemy.orm import selectinload
        
        # Load evaluations with items using eager loading
        evaluations_query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.items)
        )
        evaluations_result = await self.session.execute(evaluations_query)
        evaluations = evaluations_result.scalars().all()
        
        for evaluation in evaluations:
            # Recalculate aggregates - items are already loaded
            evaluation.recalculate_aggregates()
        
        await self.session.commit()
        return len(evaluations)
    
