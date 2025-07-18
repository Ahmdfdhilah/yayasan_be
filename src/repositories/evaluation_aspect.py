"""EvaluationAspect repository for PKG system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.evaluation_aspect import EvaluationAspect
from src.models.teacher_evaluation import TeacherEvaluation
from src.schemas.evaluation_aspect import EvaluationAspectCreate, EvaluationAspectUpdate
from src.schemas.filters import EvaluationAspectFilterParams


class EvaluationAspectRepository:
    """Repository for evaluation aspect operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, aspect_data: EvaluationAspectCreate) -> EvaluationAspect:
        """Create new evaluation aspect."""
        aspect = EvaluationAspect(
            aspect_name=aspect_data.aspect_name,
            category=getattr(aspect_data, 'category', 'General'),
            description=aspect_data.description,
            weight=aspect_data.weight,
            min_score=getattr(aspect_data, 'min_score', 1),
            max_score=aspect_data.max_score,
            is_active=aspect_data.is_active
        )
        
        self.session.add(aspect)
        await self.session.commit()
        await self.session.refresh(aspect)
        return aspect
    
    async def get_by_id(self, aspect_id: int) -> Optional[EvaluationAspect]:
        """Get evaluation aspect by ID with relationships."""
        query = select(EvaluationAspect).options(
            selectinload(EvaluationAspect.teacher_evaluations)
        ).where(
            and_(EvaluationAspect.id == aspect_id, EvaluationAspect.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, aspect_id: int, aspect_data: EvaluationAspectUpdate) -> Optional[EvaluationAspect]:
        """Update evaluation aspect."""
        aspect = await self.get_by_id(aspect_id)
        if not aspect:
            return None
        
        # Update fields
        update_data = aspect_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(aspect, key, value)
        
        aspect.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(aspect)
        return aspect
    
    async def soft_delete(self, aspect_id: int) -> bool:
        """Soft delete evaluation aspect."""
        query = (
            update(EvaluationAspect)
            .where(EvaluationAspect.id == aspect_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def activate(self, aspect_id: int) -> bool:
        """Activate evaluation aspect."""
        query = (
            update(EvaluationAspect)
            .where(EvaluationAspect.id == aspect_id)
            .values(
                is_active=True,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def deactivate(self, aspect_id: int) -> bool:
        """Deactivate evaluation aspect."""
        query = (
            update(EvaluationAspect)
            .where(EvaluationAspect.id == aspect_id)
            .values(
                is_active=False,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== LISTING AND FILTERING =====
    
    async def get_all_aspects_filtered(self, filters: EvaluationAspectFilterParams) -> Tuple[List[EvaluationAspect], int]:
        """Get evaluation aspects with filters and pagination."""
        # Base query with eager loading
        query = select(EvaluationAspect).where(EvaluationAspect.deleted_at.is_(None))
        count_query = select(func.count(EvaluationAspect.id)).where(EvaluationAspect.deleted_at.is_(None))
        
        # Apply filters
        if filters.q:
            search_filter = or_(
                EvaluationAspect.aspect_name.ilike(f"%{filters.q}%"),
                EvaluationAspect.description.ilike(f"%{filters.q}%"),
                EvaluationAspect.category.ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Note: organization_id filter removed - aspects are now universal
        
        if filters.is_active is not None:
            query = query.where(EvaluationAspect.is_active == filters.is_active)
            count_query = count_query.where(EvaluationAspect.is_active == filters.is_active)
        
        if filters.min_weight is not None:
            query = query.where(EvaluationAspect.weight >= filters.min_weight)
            count_query = count_query.where(EvaluationAspect.weight >= filters.min_weight)
        
        if filters.max_weight is not None:
            query = query.where(EvaluationAspect.weight <= filters.max_weight)
            count_query = count_query.where(EvaluationAspect.weight <= filters.max_weight)
        
        if filters.min_score is not None:
            query = query.where(EvaluationAspect.max_score >= filters.min_score)
            count_query = count_query.where(EvaluationAspect.max_score >= filters.min_score)
        
        if filters.max_score is not None:
            query = query.where(EvaluationAspect.max_score <= filters.max_score)
            count_query = count_query.where(EvaluationAspect.max_score <= filters.max_score)
        
        if filters.created_after:
            query = query.where(EvaluationAspect.created_at >= filters.created_after)
            count_query = count_query.where(EvaluationAspect.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(EvaluationAspect.created_at <= filters.created_before)
            count_query = count_query.where(EvaluationAspect.created_at <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "aspect_name":
            sort_column = EvaluationAspect.aspect_name
        elif filters.sort_by == "weight":
            sort_column = EvaluationAspect.weight
        elif filters.sort_by == "max_score":
            sort_column = EvaluationAspect.max_score
        elif filters.sort_by == "is_active":
            sort_column = EvaluationAspect.is_active
        elif filters.sort_by == "created_at":
            sort_column = EvaluationAspect.created_at
        elif filters.sort_by == "updated_at":
            sort_column = EvaluationAspect.updated_at
        else:
            sort_column = EvaluationAspect.aspect_name
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        aspects = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(aspects), total
    
    async def get_active_aspects(self) -> List[EvaluationAspect]:
        """Get all active evaluation aspects."""
        query = select(EvaluationAspect).where(
            and_(
                EvaluationAspect.is_active == True,
                EvaluationAspect.deleted_at.is_(None)
            )
        ).order_by(EvaluationAspect.aspect_name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_aspects_by_category(self, category: str) -> List[EvaluationAspect]:
        """Get aspects by category."""
        query = select(EvaluationAspect).where(
            and_(
                EvaluationAspect.category == category,
                EvaluationAspect.is_active == True,
                EvaluationAspect.deleted_at.is_(None)
            )
        ).order_by(EvaluationAspect.aspect_name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_create(self, aspects_data: List[EvaluationAspectCreate]) -> List[EvaluationAspect]:
        """Bulk create evaluation aspects."""
        aspects = []
        for aspect_data in aspects_data:
            aspect = EvaluationAspect(
                aspect_name=aspect_data.aspect_name,
                category=getattr(aspect_data, 'category', 'General'),
                description=aspect_data.description,
                weight=aspect_data.weight,
                min_score=getattr(aspect_data, 'min_score', 1),
                max_score=aspect_data.max_score,
                is_active=aspect_data.is_active
            )
            aspects.append(aspect)
            self.session.add(aspect)
        
        await self.session.commit()
        
        # Refresh all aspects
        for aspect in aspects:
            await self.session.refresh(aspect)
        
        return aspects
    
    async def bulk_update_status(self, aspect_ids: List[int], is_active: bool) -> int:
        """Bulk update aspect status."""
        query = (
            update(EvaluationAspect)
            .where(EvaluationAspect.id.in_(aspect_ids))
            .values(
                is_active=is_active,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    # ===== ANALYTICS AND STATISTICS =====
    
    async def get_aspect_statistics(self, aspect_id: int) -> Dict[str, Any]:
        """Get statistics for a specific aspect."""
        # Count evaluations using this aspect
        eval_count_query = select(func.count(TeacherEvaluation.id)).where(
            and_(
                TeacherEvaluation.aspect_id == aspect_id,
                TeacherEvaluation.deleted_at.is_(None)
            )
        )
        eval_count_result = await self.session.execute(eval_count_query)
        evaluation_count = eval_count_result.scalar()
        
        # Calculate average score
        avg_score_query = select(func.avg(TeacherEvaluation.score)).where(
            and_(
                TeacherEvaluation.aspect_id == aspect_id,
                TeacherEvaluation.deleted_at.is_(None)
            )
        )
        avg_score_result = await self.session.execute(avg_score_query)
        avg_score = avg_score_result.scalar()
        
        # Get score distribution
        score_dist_query = (
            select(TeacherEvaluation.score, func.count(TeacherEvaluation.id))
            .where(
                and_(
                    TeacherEvaluation.aspect_id == aspect_id,
                    TeacherEvaluation.deleted_at.is_(None)
                )
            )
            .group_by(TeacherEvaluation.score)
            .order_by(TeacherEvaluation.score)
        )
        score_dist_result = await self.session.execute(score_dist_query)
        score_distribution = dict(score_dist_result.fetchall())
        
        return {
            "evaluation_count": evaluation_count,
            "avg_score": float(avg_score) if avg_score else 0.0,
            "score_distribution": score_distribution
        }
    
    async def get_aspects_analytics(self) -> Dict[str, Any]:
        """Get comprehensive aspects analytics."""
        base_filter = EvaluationAspect.deleted_at.is_(None)
        
        # Total counts
        total_query = select(func.count(EvaluationAspect.id)).where(base_filter)
        total_result = await self.session.execute(total_query)
        total_aspects = total_result.scalar()
        
        # Active counts
        active_query = select(func.count(EvaluationAspect.id)).where(
            and_(base_filter, EvaluationAspect.is_active == True)
        )
        active_result = await self.session.execute(active_query)
        active_aspects = active_result.scalar()
        
        # Weight distribution
        weight_query = (
            select(EvaluationAspect.aspect_name, EvaluationAspect.weight)
            .where(and_(base_filter, EvaluationAspect.is_active == True))
            .order_by(EvaluationAspect.weight.desc())
        )
        weight_result = await self.session.execute(weight_query)
        weight_data = weight_result.fetchall()
        
        total_weight = sum(weight for _, weight in weight_data)
        weight_distribution = {name: float(weight) for name, weight in weight_data}
        
        return {
            "total_aspects": total_aspects,
            "active_aspects": active_aspects,
            "inactive_aspects": total_aspects - active_aspects,
            "total_weight": float(total_weight),
            "weight_distribution": weight_distribution
        }
    
    async def validate_aspect_weights(self) -> Dict[str, Any]:
        """Validate that aspect weights are properly balanced."""
        active_aspects = await self.get_active_aspects()
        
        total_weight = sum(aspect.weight for aspect in active_aspects)
        expected_weight = Decimal("100.00")
        
        is_valid = total_weight == expected_weight
        errors = []
        warnings = []
        
        if total_weight > expected_weight:
            errors.append(f"Total weight ({total_weight}%) exceeds 100%")
        elif total_weight < expected_weight:
            warnings.append(f"Total weight ({total_weight}%) is less than 100%")
        
        # Check for zero weights
        zero_weight_aspects = [a for a in active_aspects if a.weight == 0]
        if zero_weight_aspects:
            warnings.append(f"{len(zero_weight_aspects)} aspects have zero weight")
        
        return {
            "is_valid": is_valid,
            "total_weight": float(total_weight),
            "errors": errors,
            "warnings": warnings
        }
    
    # ===== HELPER METHODS =====
    
    async def aspect_exists(self, aspect_name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if aspect name already exists."""
        query = select(EvaluationAspect).where(
            and_(
                EvaluationAspect.aspect_name.ilike(aspect_name),
                EvaluationAspect.deleted_at.is_(None)
            )
        )
        
        if exclude_id:
            query = query.where(EvaluationAspect.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def has_evaluations(self, aspect_id: int) -> bool:
        """Check if aspect has any evaluations."""
        query = select(func.count(TeacherEvaluation.id)).where(
            and_(
                TeacherEvaluation.aspect_id == aspect_id,
                TeacherEvaluation.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0