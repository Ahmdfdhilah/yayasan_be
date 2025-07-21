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
from src.schemas.evaluation_aspect import EvaluationAspectFilterParams


class EvaluationAspectRepository:
    """Repository for evaluation aspect operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, aspect_data: EvaluationAspectCreate, created_by: Optional[int] = None) -> EvaluationAspect:
        """Create new evaluation aspect - simplified."""
        aspect = EvaluationAspect(
            aspect_name=aspect_data.aspect_name,
            category=aspect_data.category,
            description=aspect_data.description,
            is_active=aspect_data.is_active,
            created_by=created_by
        )
        
        self.session.add(aspect)
        await self.session.commit()
        await self.session.refresh(aspect)
        return aspect
    
    async def get_by_id(self, aspect_id: int) -> Optional[EvaluationAspect]:
        """Get evaluation aspect by ID with relationships."""
        query = select(EvaluationAspect).options(
            selectinload(EvaluationAspect.teacher_evaluation_items)
        ).where(
            and_(EvaluationAspect.id == aspect_id, EvaluationAspect.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, aspect_id: int, aspect_data: EvaluationAspectUpdate, updated_by: Optional[int] = None) -> Optional[EvaluationAspect]:
        """Update evaluation aspect."""
        aspect = await self.get_by_id(aspect_id)
        if not aspect:
            return None
        
        # Update fields
        update_data = aspect_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(aspect, key, value)
        
        if updated_by:
            aspect.updated_by = updated_by
        
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
        
        if filters.category:
            query = query.where(EvaluationAspect.category.ilike(f"%{filters.category}%"))
            count_query = count_query.where(EvaluationAspect.category.ilike(f"%{filters.category}%"))
        
        
        if filters.created_after:
            query = query.where(EvaluationAspect.created_at >= filters.created_after)
            count_query = count_query.where(EvaluationAspect.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(EvaluationAspect.created_at <= filters.created_before)
            count_query = count_query.where(EvaluationAspect.created_at <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "aspect_name":
            sort_column = EvaluationAspect.aspect_name
        elif filters.sort_by == "category":
            sort_column = EvaluationAspect.category
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
    
    async def bulk_create(self, aspects_data: List[EvaluationAspectCreate], created_by: Optional[int] = None) -> List[EvaluationAspect]:
        """Bulk create evaluation aspects."""
        aspects = []
        for aspect_data in aspects_data:
            aspect = EvaluationAspect(
                aspect_name=aspect_data.aspect_name,
                category=aspect_data.category,
                description=aspect_data.description,
                is_active=aspect_data.is_active,
                created_by=created_by
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
        from src.models.teacher_evaluation_item import TeacherEvaluationItem
        
        # Count evaluation items using this aspect
        eval_count_query = select(func.count(TeacherEvaluationItem.id)).where(
            TeacherEvaluationItem.aspect_id == aspect_id
        )
        eval_count_result = await self.session.execute(eval_count_query)
        evaluation_count = eval_count_result.scalar()
        
        # Calculate average score
        avg_score_query = select(func.avg(TeacherEvaluationItem.score)).where(
            TeacherEvaluationItem.aspect_id == aspect_id
        )
        avg_score_result = await self.session.execute(avg_score_query)
        avg_score = avg_score_result.scalar() or 0.0
        
        return {
            "evaluation_count": evaluation_count,
            "avg_score": round(float(avg_score), 2)
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
        
        return {
            "total_aspects": total_aspects,
            "active_aspects": active_aspects,
            "inactive_aspects": total_aspects - active_aspects
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
        """Check if aspect has any evaluation items."""
        from src.models.teacher_evaluation_item import TeacherEvaluationItem
        
        query = select(func.count(TeacherEvaluationItem.id)).where(
            TeacherEvaluationItem.aspect_id == aspect_id
        )
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0
    
    # ===== SYNC METHODS =====
    
    async def sync_aspect_to_all_evaluations(self, aspect_id: int, created_by: Optional[int] = None) -> int:
        """Add aspect to all existing teacher evaluations."""
        from src.models.teacher_evaluation import TeacherEvaluation
        from src.models.teacher_evaluation_item import TeacherEvaluationItem
        from src.models.enums import EvaluationGrade
        from sqlalchemy.orm import selectinload
        
        # Get all existing teacher evaluations with items preloaded
        evaluations_query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.items)
        )
        evaluations_result = await self.session.execute(evaluations_query)
        evaluations = evaluations_result.scalars().all()
        
        items_created = 0
        for evaluation in evaluations:
            # Check if item already exists for this aspect (using preloaded items)
            existing_item = None
            for item in evaluation.items:
                if item.aspect_id == aspect_id:
                    existing_item = item
                    break
            
            if not existing_item:
                # Create new item with default grade C
                new_item = TeacherEvaluationItem(
                    teacher_evaluation_id=evaluation.id,
                    aspect_id=aspect_id,
                    grade=EvaluationGrade.C,  # Default grade
                    created_by=created_by
                )
                from datetime import datetime
                new_item.updated_at = datetime.utcnow()
                self.session.add(new_item)
                items_created += 1
        
        if items_created > 0:
            await self.session.commit()
            
        return items_created
    
    async def remove_aspect_from_all_evaluations(self, aspect_id: int) -> int:
        """Remove aspect from all teacher evaluations."""
        from src.models.teacher_evaluation_item import TeacherEvaluationItem
        
        # Delete all items with this aspect_id
        delete_query = delete(TeacherEvaluationItem).where(
            TeacherEvaluationItem.aspect_id == aspect_id
        )
        result = await self.session.execute(delete_query)
        items_deleted = result.rowcount
        
        if items_deleted > 0:
            await self.session.commit()
            
        return items_deleted
    
    async def sync_all_active_aspects_to_evaluations(self) -> int:
        """Ensure all active aspects are in all evaluations."""
        from src.models.teacher_evaluation import TeacherEvaluation
        from src.models.teacher_evaluation_item import TeacherEvaluationItem
        from src.models.enums import EvaluationGrade
        from sqlalchemy.orm import selectinload
        
        # Get all active aspects
        active_aspects = await self.get_active_aspects()
        
        # Get all evaluations with items preloaded
        evaluations_query = select(TeacherEvaluation).options(
            selectinload(TeacherEvaluation.items)
        )
        evaluations_result = await self.session.execute(evaluations_query)
        evaluations = evaluations_result.scalars().all()
        
        total_items_created = 0
        
        for aspect in active_aspects:
            for evaluation in evaluations:
                # Check if item exists (using preloaded items)
                existing_item = None
                for item in evaluation.items:
                    if item.aspect_id == aspect.id:
                        existing_item = item
                        break
                
                if not existing_item:
                    # Create missing item
                    new_item = TeacherEvaluationItem(
                        teacher_evaluation_id=evaluation.id,
                        aspect_id=aspect.id,
                        grade=EvaluationGrade.C,
                        created_by=1  # System user
                    )
                    from datetime import datetime
                    new_item.updated_at = datetime.utcnow()
                    self.session.add(new_item)
                    total_items_created += 1
        
        if total_items_created > 0:
            await self.session.commit()
        
        return total_items_created