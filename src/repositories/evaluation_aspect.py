"""EvaluationAspect repository for PKG system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.evaluation_aspect import EvaluationAspect
from src.models.evaluation_category import EvaluationCategory
from src.models.teacher_evaluation import TeacherEvaluation
from src.schemas.evaluation_aspect import EvaluationAspectCreate, EvaluationAspectUpdate
from src.schemas.evaluation_aspect import EvaluationAspectFilterParams


class EvaluationAspectRepository:
    """Repository for evaluation aspect operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, aspect_data: EvaluationAspectCreate, created_by: Optional[int] = None) -> EvaluationAspect:
        """Create new evaluation aspect."""
        # If no display_order provided, append to end of category
        display_order = aspect_data.display_order
        if display_order is None:
            max_order = await self.get_max_aspect_order_in_category(aspect_data.category_id)
            display_order = max_order + 1
        
        aspect = EvaluationAspect(
            aspect_name=aspect_data.aspect_name,
            category_id=aspect_data.category_id,
            description=aspect_data.description,
            display_order=display_order,
            is_active=aspect_data.is_active,
            created_by=created_by
        )
        
        self.session.add(aspect)
        await self.session.commit()
        await self.session.refresh(aspect)
        
        # Load aspect with category relationship
        query = select(EvaluationAspect).options(
            selectinload(EvaluationAspect.category)
        ).where(EvaluationAspect.id == aspect.id)
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def get_by_id(self, aspect_id: int) -> Optional[EvaluationAspect]:
        """Get evaluation aspect by ID with relationships."""
        query = select(EvaluationAspect).options(
            selectinload(EvaluationAspect.teacher_evaluation_items),
            selectinload(EvaluationAspect.category)
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
        query = select(EvaluationAspect).options(
            selectinload(EvaluationAspect.category)
        ).where(EvaluationAspect.deleted_at.is_(None))
        count_query = select(func.count(EvaluationAspect.id)).where(EvaluationAspect.deleted_at.is_(None))
        
        # Apply filters
        if filters.q:
            search_filter = or_(
                EvaluationAspect.aspect_name.ilike(f"%{filters.q}%"),
                EvaluationAspect.description.ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Note: organization_id filter removed - aspects are now universal
        
        if filters.is_active is not None:
            query = query.where(EvaluationAspect.is_active == filters.is_active)
            count_query = count_query.where(EvaluationAspect.is_active == filters.is_active)
        
        if filters.category_id:
            query = query.where(EvaluationAspect.category_id == filters.category_id)
            count_query = count_query.where(EvaluationAspect.category_id == filters.category_id)
        
        
        if filters.created_after:
            query = query.where(EvaluationAspect.created_at >= filters.created_after)
            count_query = count_query.where(EvaluationAspect.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(EvaluationAspect.created_at <= filters.created_before)
            count_query = count_query.where(EvaluationAspect.created_at <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "aspect_name":
            sort_column = EvaluationAspect.aspect_name
        elif filters.sort_by == "display_order":
            sort_column = EvaluationAspect.display_order
        elif filters.sort_by == "is_active":
            sort_column = EvaluationAspect.is_active
        elif filters.sort_by == "created_at":
            sort_column = EvaluationAspect.created_at
        elif filters.sort_by == "updated_at":
            sort_column = EvaluationAspect.updated_at
        else:
            # Default sorting: category display_order first, then aspect display_order, then aspect_name
            query = query.join(EvaluationCategory).order_by(
                EvaluationCategory.display_order.asc(),
                EvaluationAspect.display_order.asc(),
                EvaluationAspect.aspect_name.asc()
            )
            sort_column = None
        
        if sort_column is not None:
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
        query = select(EvaluationAspect).options(
            selectinload(EvaluationAspect.category)
        ).where(
            and_(
                EvaluationAspect.is_active == True,
                EvaluationAspect.deleted_at.is_(None)
            )
        ).join(EvaluationCategory).order_by(
            EvaluationCategory.display_order.asc(),
            EvaluationAspect.display_order.asc(),
            EvaluationAspect.aspect_name.asc()
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_aspects_by_category(self, category_id: int) -> List[EvaluationAspect]:
        """Get aspects by category ID."""
        query = select(EvaluationAspect).options(
            selectinload(EvaluationAspect.category)
        ).where(
            and_(
                EvaluationAspect.category_id == category_id,
                EvaluationAspect.is_active == True,
                EvaluationAspect.deleted_at.is_(None)
            )
        ).order_by(
            EvaluationAspect.display_order.asc(),
            EvaluationAspect.aspect_name.asc()
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_create(self, aspects_data: List[EvaluationAspectCreate], created_by: Optional[int] = None) -> List[EvaluationAspect]:
        """Bulk create evaluation aspects."""
        aspects = []
        for aspect_data in aspects_data:
            aspect = EvaluationAspect(
                aspect_name=aspect_data.aspect_name,
                category_id=aspect_data.category_id,
                description=aspect_data.description,
                display_order=aspect_data.display_order,
                is_active=aspect_data.is_active,
                created_by=created_by
            )
            aspects.append(aspect)
            self.session.add(aspect)
        
        await self.session.commit()
        
        # Refresh all aspects with eager loading of categories
        refreshed_aspects = []
        for aspect in aspects:
            await self.session.refresh(aspect)
            # Get aspect with category relationship loaded
            query = select(EvaluationAspect).options(
                selectinload(EvaluationAspect.category)
            ).where(EvaluationAspect.id == aspect.id)
            result = await self.session.execute(query)
            refreshed_aspect = result.scalar_one()
            refreshed_aspects.append(refreshed_aspect)
        
        return refreshed_aspects
    
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
                # Create new item with null values - no default grade
                new_item = TeacherEvaluationItem(
                    teacher_evaluation_id=evaluation.id,
                    aspect_id=aspect_id,
                    grade=None,  # No default grade - starts as null
                    score=None,  # No default score - starts as null
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
    
    # ===== CATEGORY MANAGEMENT METHODS =====
    
    async def create_category(self, name: str, description: Optional[str] = None, display_order: Optional[int] = None, created_by: Optional[int] = None) -> EvaluationCategory:
        """Create new evaluation category."""
        # If no display_order provided, append to end
        if display_order is None:
            max_order = await self.get_max_category_order()
            display_order = max_order + 1
        
        category = EvaluationCategory(
            name=name,
            description=description,
            display_order=display_order,
            created_by=created_by
        )
        
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def update_category(self, category_id: int, category_data, updated_by: int) -> Optional[EvaluationCategory]:
        """Update an evaluation category."""
        # Prepare update data
        update_data = {"updated_by": updated_by, "updated_at": datetime.utcnow()}
        
        if category_data.name is not None:
            update_data["name"] = category_data.name
        if category_data.description is not None:
            update_data["description"] = category_data.description
        if category_data.display_order is not None:
            update_data["display_order"] = category_data.display_order
        if category_data.is_active is not None:
            update_data["is_active"] = category_data.is_active
        
        # Update the category
        stmt = update(EvaluationCategory).where(
            and_(EvaluationCategory.id == category_id, EvaluationCategory.deleted_at.is_(None))
        ).values(**update_data)
        
        result = await self.session.execute(stmt)
        
        if result.rowcount == 0:
            return None
        
        await self.session.commit()
        
        # Return updated category
        return await self.get_category_by_id(category_id)
    
    async def get_category_by_id(self, category_id: int) -> Optional[EvaluationCategory]:
        """Get evaluation category by ID."""
        query = select(EvaluationCategory).where(
            and_(EvaluationCategory.id == category_id, EvaluationCategory.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_category_by_name(self, category_name: str) -> Optional[EvaluationCategory]:
        """Get evaluation category by ID."""
        query = select(EvaluationCategory).where(
            and_(EvaluationCategory.name == category_name, EvaluationCategory.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all_categories(self, include_inactive: bool = False) -> List[EvaluationCategory]:
        """Get all evaluation categories ordered by display_order."""
        query = select(EvaluationCategory).where(EvaluationCategory.deleted_at.is_(None))
        
        if not include_inactive:
            query = query.where(EvaluationCategory.is_active == True)
        
        query = query.order_by(EvaluationCategory.display_order.asc(), EvaluationCategory.name.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_category_order(self, category_id: int, new_order: int) -> bool:
        """Update category display order with auto-shifting."""
        try:
            # Get current category
            current_category = await self.get_category_by_id(category_id)
            if not current_category:
                return False
            
            current_order = current_category.display_order
            
            # If same order, no change needed
            if current_order == new_order:
                return True
            
            # If moving up (to lower number), shift others down
            if new_order < current_order:
                # Shift categories at new_order and above up by 1
                shift_query = (
                    update(EvaluationCategory)
                    .where(
                        and_(
                            EvaluationCategory.display_order >= new_order,
                            EvaluationCategory.display_order < current_order,
                            EvaluationCategory.deleted_at.is_(None)
                        )
                    )
                    .values(
                        display_order=EvaluationCategory.display_order + 1,
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.execute(shift_query)
            
            # If moving down (to higher number), shift others up
            elif new_order > current_order:
                # Shift categories between current and new down by 1
                shift_query = (
                    update(EvaluationCategory)
                    .where(
                        and_(
                            EvaluationCategory.display_order > current_order,
                            EvaluationCategory.display_order <= new_order,
                            EvaluationCategory.deleted_at.is_(None)
                        )
                    )
                    .values(
                        display_order=EvaluationCategory.display_order - 1,
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.execute(shift_query)
            
            # Update target category to new position
            update_query = (
                update(EvaluationCategory)
                .where(EvaluationCategory.id == category_id)
                .values(
                    display_order=new_order,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self.session.execute(update_query)
            
            await self.session.commit()
            return result.rowcount > 0
            
        except Exception:
            await self.session.rollback()
            return False
    
    async def update_aspect_order(self, aspect_id: int, new_order: int) -> bool:
        """Update aspect display order within its category with auto-shifting."""
        try:
            # Get current aspect
            current_aspect = await self.get_by_id(aspect_id)
            if not current_aspect:
                return False
            
            category_id = current_aspect.category_id
            current_order = current_aspect.display_order
            
            # If same order, no change needed
            if current_order == new_order:
                return True
            
            # If moving up (to lower number), shift others down
            if new_order < current_order:
                # Shift aspects in same category at new_order and above up by 1
                shift_query = (
                    update(EvaluationAspect)
                    .where(
                        and_(
                            EvaluationAspect.category_id == category_id,
                            EvaluationAspect.display_order >= new_order,
                            EvaluationAspect.display_order < current_order,
                            EvaluationAspect.deleted_at.is_(None)
                        )
                    )
                    .values(
                        display_order=EvaluationAspect.display_order + 1,
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.execute(shift_query)
            
            # If moving down (to higher number), shift others up
            elif new_order > current_order:
                # Shift aspects in same category between current and new down by 1
                shift_query = (
                    update(EvaluationAspect)
                    .where(
                        and_(
                            EvaluationAspect.category_id == category_id,
                            EvaluationAspect.display_order > current_order,
                            EvaluationAspect.display_order <= new_order,
                            EvaluationAspect.deleted_at.is_(None)
                        )
                    )
                    .values(
                        display_order=EvaluationAspect.display_order - 1,
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.execute(shift_query)
            
            # Update target aspect to new position
            update_query = (
                update(EvaluationAspect)
                .where(EvaluationAspect.id == aspect_id)
                .values(
                    display_order=new_order,
                    updated_at=datetime.utcnow()
                )
            )
            result = await self.session.execute(update_query)
            
            await self.session.commit()
            return result.rowcount > 0
            
        except Exception:
            await self.session.rollback()
            return False
    
    async def reorder_aspects_in_category(self, category_id: int, aspect_order_map: Dict[int, int]) -> bool:
        """Reorder multiple aspects within a category."""
        try:
            for aspect_id, new_order in aspect_order_map.items():
                query = (
                    update(EvaluationAspect)
                    .where(
                        and_(
                            EvaluationAspect.id == aspect_id,
                            EvaluationAspect.category_id == category_id,
                            EvaluationAspect.deleted_at.is_(None)
                        )
                    )
                    .values(
                        display_order=new_order,
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.execute(query)
            
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False
    
    async def get_categories_with_order(self) -> List[Dict[str, Any]]:
        """Get all categories with their order and aspect counts."""
        query = select(
            EvaluationCategory.id,
            EvaluationCategory.name,
            EvaluationCategory.display_order,
            EvaluationCategory.is_active,
            func.count(EvaluationAspect.id).label('aspect_count'),
            func.count(func.nullif(EvaluationAspect.is_active, False)).label('active_aspects_count')
        ).outerjoin(
            EvaluationAspect, 
            and_(
                EvaluationAspect.category_id == EvaluationCategory.id,
                EvaluationAspect.deleted_at.is_(None)
            )
        ).where(
            EvaluationCategory.deleted_at.is_(None)
        ).group_by(
            EvaluationCategory.id,
            EvaluationCategory.name,
            EvaluationCategory.display_order,
            EvaluationCategory.is_active
        ).order_by(
            EvaluationCategory.display_order.asc(),
            EvaluationCategory.name.asc()
        )
        
        result = await self.session.execute(query)
        categories = []
        for row in result.all():
            categories.append({
                'id': row.id,
                'name': row.name,
                'display_order': row.display_order,
                'is_active': row.is_active,
                'aspect_count': row.aspect_count,
                'active_aspects_count': row.active_aspects_count
            })
        
        return categories
    
    async def get_aspects_by_category_ordered(self, category_id: int) -> List[EvaluationAspect]:
        """Get aspects by category with proper ordering."""
        query = select(EvaluationAspect).options(
            selectinload(EvaluationAspect.category)
        ).where(
            and_(
                EvaluationAspect.category_id == category_id,
                EvaluationAspect.deleted_at.is_(None)
            )
        ).order_by(
            EvaluationAspect.display_order.asc(),
            EvaluationAspect.aspect_name.asc()
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def auto_assign_orders(self) -> bool:
        """Auto-assign orders to categories and aspects that don't have them."""
        try:
            # Get all categories and assign orders
            categories = await self.get_all_categories(include_inactive=True)
            
            # Assign category orders sequentially (simple update without shifting)
            for i, category in enumerate(categories, 1):
                simple_update = (
                    update(EvaluationCategory)
                    .where(EvaluationCategory.id == category.id)
                    .values(
                        display_order=i,
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.execute(simple_update)
            
            # Assign aspect orders within each category
            for category in categories:
                aspects_query = select(EvaluationAspect).where(
                    and_(
                        EvaluationAspect.category_id == category.id,
                        EvaluationAspect.deleted_at.is_(None)
                    )
                ).order_by(EvaluationAspect.aspect_name)
                
                aspects_result = await self.session.execute(aspects_query)
                aspects = aspects_result.scalars().all()
                
                # Simple sequential update for aspects in each category
                for i, aspect in enumerate(aspects, 1):
                    simple_update = (
                        update(EvaluationAspect)
                        .where(EvaluationAspect.id == aspect.id)
                        .values(
                            display_order=i,
                            updated_at=datetime.utcnow()
                        )
                    )
                    await self.session.execute(simple_update)
            
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False
    
    # ===== HELPER METHODS FOR ORDERING =====
    
    async def get_max_category_order(self) -> int:
        """Get maximum category display order."""
        query = select(func.max(EvaluationCategory.display_order)).where(
            EvaluationCategory.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        max_order = result.scalar() or 0
        return max_order
    
    async def get_max_aspect_order_in_category(self, category_id: int) -> int:
        """Get maximum aspect display order in a category."""
        query = select(func.max(EvaluationAspect.display_order)).where(
            and_(
                EvaluationAspect.category_id == category_id,
                EvaluationAspect.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        max_order = result.scalar() or 0
        return max_order
    
    async def fix_category_ordering_gaps(self) -> bool:
        """Fix any gaps in category ordering (e.g., 1,2,4,6 -> 1,2,3,4)."""
        try:
            categories_query = select(EvaluationCategory).where(
                EvaluationCategory.deleted_at.is_(None)
            ).order_by(EvaluationCategory.display_order.asc(), EvaluationCategory.name.asc())
            
            result = await self.session.execute(categories_query)
            categories = result.scalars().all()
            
            for i, category in enumerate(categories, 1):
                if category.display_order != i:
                    update_query = (
                        update(EvaluationCategory)
                        .where(EvaluationCategory.id == category.id)
                        .values(
                            display_order=i,
                            updated_at=datetime.utcnow()
                        )
                    )
                    await self.session.execute(update_query)
            
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False
    
    async def fix_aspect_ordering_gaps_in_category(self, category_id: int) -> bool:
        """Fix any gaps in aspect ordering within a category."""
        try:
            aspects_query = select(EvaluationAspect).where(
                and_(
                    EvaluationAspect.category_id == category_id,
                    EvaluationAspect.deleted_at.is_(None)
                )
            ).order_by(EvaluationAspect.display_order.asc(), EvaluationAspect.aspect_name.asc())
            
            result = await self.session.execute(aspects_query)
            aspects = result.scalars().all()
            
            for i, aspect in enumerate(aspects, 1):
                if aspect.display_order != i:
                    update_query = (
                        update(EvaluationAspect)
                        .where(EvaluationAspect.id == aspect.id)
                        .values(
                            display_order=i,
                            updated_at=datetime.utcnow()
                        )
                    )
                    await self.session.execute(update_query)
            
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def delete_category(self, category_id: int) -> bool:
        """Delete category with cascade deletion of all associated aspects."""
        try:
            # First, get all aspects in this category
            aspects_query = select(EvaluationAspect).where(
                and_(
                    EvaluationAspect.category_id == category_id,
                    EvaluationAspect.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(aspects_query)
            aspects = result.scalars().all()
            
            # Remove each aspect from all teacher evaluations first
            total_items_deleted = 0
            for aspect in aspects:
                items_deleted = await self.remove_aspect_from_all_evaluations(aspect.id)
                total_items_deleted += items_deleted
            
            # Soft delete all aspects in the category
            aspects_delete_query = (
                update(EvaluationAspect)
                .where(
                    and_(
                        EvaluationAspect.category_id == category_id,
                        EvaluationAspect.deleted_at.is_(None)
                    )
                )
                .values(
                    deleted_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await self.session.execute(aspects_delete_query)
            
            # Soft delete the category
            category_delete_query = (
                update(EvaluationCategory)
                .where(EvaluationCategory.id == category_id)
                .values(
                    deleted_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            result = await self.session.execute(category_delete_query)
            
            await self.session.commit()
            
            return result.rowcount > 0
            
        except Exception:
            await self.session.rollback()
            return False