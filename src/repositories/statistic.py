"""Statistic repository for database operations."""

from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, update, and_
from datetime import datetime

from src.models.statistic import Statistic
from src.schemas.statistic import StatisticFilterParams


class StatisticRepository:
    """Repository for statistic operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, statistic_data: dict) -> Statistic:
        """Create a new statistic."""
        display_order = statistic_data.get('display_order')
        
        if display_order:
            # Shift existing statistics with same or higher display_order
            await self._shift_display_orders(display_order, shift_up=True)
        else:
            # Auto-assign next available order
            max_order = await self._get_max_display_order()
            statistic_data['display_order'] = (max_order or 0) + 1
        
        statistic = Statistic(**statistic_data)
        self.session.add(statistic)
        await self.session.commit()
        await self.session.refresh(statistic)
        return statistic

    async def get_by_id(self, statistic_id: int) -> Optional[Statistic]:
        """Get statistic by ID."""
        query = select(Statistic).where(
            and_(Statistic.id == statistic_id, Statistic.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, statistic_id: int, update_data: dict) -> Optional[Statistic]:
        """Update statistic."""
        new_display_order = update_data.get('display_order')
        
        if new_display_order:
            # Get current display_order
            current_statistic = await self.get_by_id(statistic_id)
            current_display_order = current_statistic.display_order if current_statistic else None
            
            if current_display_order != new_display_order:
                # Shift existing statistics
                await self._shift_display_orders(new_display_order, shift_up=True, exclude_id=statistic_id)
        
        # Update the record
        update_data['updated_at'] = datetime.utcnow()
        stmt = (
            update(Statistic)
            .where(and_(Statistic.id == statistic_id, Statistic.deleted_at.is_(None)))
            .values(**update_data)
            .returning(Statistic)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def soft_delete(self, statistic_id: int) -> bool:
        """Soft delete statistic."""
        # Get current statistic to get its display_order
        current_statistic = await self.get_by_id(statistic_id)
        if not current_statistic:
            return False
        
        # Soft delete the statistic
        stmt = (
            update(Statistic)
            .where(Statistic.id == statistic_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        
        # Shift down all statistics with higher display_order
        await self._shift_display_orders(
            current_statistic.display_order + 1, 
            shift_up=False
        )
        
        await self.session.commit()
        return result.rowcount > 0

    async def hard_delete(self, statistic_id: int) -> bool:
        """Hard delete statistic."""
        # Get current statistic to get its display_order
        current_statistic = await self.get_by_id(statistic_id)
        if not current_statistic:
            return False
        
        # Hard delete the statistic
        stmt = delete(Statistic).where(Statistic.id == statistic_id)
        result = await self.session.execute(stmt)
        
        # Shift down all statistics with higher display_order
        await self._shift_display_orders(
            current_statistic.display_order + 1, 
            shift_up=False
        )
        
        await self.session.commit()
        return result.rowcount > 0

    async def get_all_filtered(
        self, 
        filters: StatisticFilterParams
    ) -> Tuple[List[Statistic], int]:
        """Get statistics with filters and pagination."""
        query = select(Statistic).where(Statistic.deleted_at.is_(None))
        count_query = select(func.count(Statistic.id)).where(Statistic.deleted_at.is_(None))

        # Apply search filter
        if filters.search:
            search_filter = or_(
                Statistic.title.ilike(f"%{filters.search}%"),
                Statistic.description.ilike(f"%{filters.search}%"),
                Statistic.stats.ilike(f"%{filters.search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)


        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if filters.sort_by == "title":
            sort_column = Statistic.title
        elif filters.sort_by == "stats":
            sort_column = Statistic.stats
        elif filters.sort_by == "created_at":
            sort_column = Statistic.created_at
        elif filters.sort_by == "updated_at":
            sort_column = Statistic.updated_at
        else:
            sort_column = Statistic.display_order

        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)

        # Execute query
        result = await self.session.execute(query)
        statistics = result.scalars().all()

        return list(statistics), total


    async def _get_max_display_order(self) -> Optional[int]:
        """Get the maximum display_order value."""
        query = select(func.max(Statistic.display_order)).where(Statistic.deleted_at.is_(None))
        result = await self.session.execute(query)
        return result.scalar()

    async def _shift_display_orders(
        self, 
        from_order: int, 
        shift_up: bool = True, 
        exclude_id: Optional[int] = None
    ) -> None:
        """Shift display orders to make room for new/updated statistic."""
        conditions = [
            Statistic.display_order >= from_order,
            Statistic.deleted_at.is_(None)
        ]
        if exclude_id:
            conditions.append(Statistic.id != exclude_id)
        
        # Shift all statistics at or after the target position
        if shift_up:
            stmt = (
                update(Statistic)
                .where(and_(*conditions))
                .values(
                    display_order=Statistic.display_order + 1,
                    updated_at=datetime.utcnow()
                )
            )
        else:
            stmt = (
                update(Statistic)
                .where(and_(*conditions))
                .values(
                    display_order=Statistic.display_order - 1,
                    updated_at=datetime.utcnow()
                )
            )
        
        await self.session.execute(stmt)
        await self.session.flush()  # Don't commit yet, let the main operation handle it