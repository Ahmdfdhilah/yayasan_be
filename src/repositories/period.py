"""Period repository for universal period management."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.period import Period
from src.schemas.period import PeriodCreate, PeriodUpdate, PeriodFilter


class PeriodRepository:
    """Period repository for universal period management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, period_data: PeriodCreate, created_by: Optional[int] = None) -> Period:
        """Create a new period."""
        period = Period(
            academic_year=period_data.academic_year,
            semester=period_data.semester,
            start_date=period_data.start_date,
            end_date=period_data.end_date,
            description=period_data.description,
            is_active=False,  # Default to inactive
            created_by=created_by
        )
        
        self.session.add(period)
        await self.session.commit()
        await self.session.refresh(period)
        return period
    
    async def get_by_id(self, period_id: int) -> Optional[Period]:
        """Get period by ID."""
        query = select(Period).where(Period.id == period_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id_with_relations(self, period_id: int) -> Optional[Period]:
        """Get period by ID with relationships loaded."""
        query = select(Period).options(
            selectinload(Period.teacher_evaluations),
            selectinload(Period.rpp_submissions)
        ).where(Period.id == period_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_filtered(
        self,
        filter_params: Optional[PeriodFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Period], int]:
        """Get filtered periods with pagination."""
        query = select(Period)
        
        if filter_params:
            conditions = []
            
            if filter_params.academic_year:
                conditions.append(Period.academic_year == filter_params.academic_year)
            
            if filter_params.semester:
                conditions.append(Period.semester == filter_params.semester)
            
            
            if filter_params.is_active is not None:
                conditions.append(Period.is_active == filter_params.is_active)
            
            if filter_params.start_date_from:
                conditions.append(Period.start_date >= filter_params.start_date_from)
            
            if filter_params.start_date_to:
                conditions.append(Period.start_date <= filter_params.start_date_to)
            
            if filter_params.end_date_from:
                conditions.append(Period.end_date >= filter_params.end_date_from)
            
            if filter_params.end_date_to:
                conditions.append(Period.end_date <= filter_params.end_date_to)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.order_by(Period.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        periods = result.scalars().all()
        
        return list(periods), total
    
    async def get_active_period(self) -> Optional[Period]:
        """Get the single active period. Business rule: only one period can be active at a time."""
        query = select(Period).where(Period.is_active == True)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def has_active_period(self) -> bool:
        """Check if there is any active period."""
        query = select(func.count(Period.id)).where(Period.is_active == True)
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0
    
    async def deactivate_all_periods(self, updated_by: Optional[int] = None) -> int:
        """Deactivate all currently active periods. Returns count of deactivated periods."""
        update_query = (
            update(Period)
            .where(Period.is_active == True)
            .values(is_active=False, updated_by=updated_by)
        )
        
        result = await self.session.execute(update_query)
        await self.session.commit()
        return result.rowcount
    
    async def get_current_periods(self) -> List[Period]:
        """Get periods that are currently active based on dates."""
        today = date.today()
        query = select(Period).where(
            and_(
                Period.start_date <= today,
                Period.end_date >= today
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, period_id: int, period_data: PeriodUpdate, updated_by: Optional[int] = None) -> Optional[Period]:
        """Update an existing period."""
        period = await self.get_by_id(period_id)
        if not period:
            return None
        
        update_data = period_data.dict(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
        
        for field, value in update_data.items():
            setattr(period, field, value)
        
        await self.session.commit()
        await self.session.refresh(period)
        return period
    
    async def can_activate_period(self, period_id: int) -> Tuple[bool, str]:
        """Check if period can be activated. Returns (can_activate, reason)."""
        period = await self.get_by_id(period_id)
        if not period:
            return False, "Period not found"
        
        if period.is_active:
            return True, "Period is already active"
        
        has_active = await self.has_active_period()
        if has_active:
            active_period = await self.get_active_period()
            return False, f"Another period is already active: {active_period.period_name if active_period else 'Unknown'}"
        
        return True, "Can activate"
    
    async def activate(self, period_id: int, updated_by: Optional[int] = None) -> Optional[Period]:
        """Activate a period. Business rule: only one period can be active at a time."""
        period = await self.get_by_id(period_id)
        if not period:
            return None
        
        # Check if period is already active
        if period.is_active:
            return period
        
        # Business rule: Check if there's already an active period
        has_active = await self.has_active_period()
        if has_active:
            # Return None to indicate business rule violation
            return None
        
        # Activate the requested period
        period.is_active = True
        if updated_by:
            period.updated_by = updated_by
        
        await self.session.commit()
        await self.session.refresh(period)
        return period
    
    async def deactivate(self, period_id: int, updated_by: Optional[int] = None) -> Optional[Period]:
        """Deactivate a period."""
        period = await self.get_by_id(period_id)
        if not period:
            return None
        
        period.is_active = False
        if updated_by:
            period.updated_by = updated_by
        
        await self.session.commit()
        await self.session.refresh(period)
        return period
    
    async def delete(self, period_id: int) -> bool:
        """Delete a period if it has no associated data."""
        period = await self.get_by_id_with_relations(period_id)
        if not period:
            return False
        
        # Check if period has any associated evaluations or submissions
        if period.teacher_evaluations or period.rpp_submissions:
            return False  # Cannot delete period with associated data
        
        await self.session.delete(period)
        await self.session.commit()
        return True
    
    async def exists_by_academic_period(self, academic_year: str, semester: str) -> bool:
        """Check if a period exists for given academic year and semester."""
        query = select(Period).where(
            and_(
                Period.academic_year == academic_year,
                Period.semester == semester
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_period_stats(self, period_id: int) -> Dict[str, int]:
        """Get statistics for a period."""
        period = await self.get_by_id_with_relations(period_id)
        if not period:
            return {}
        
        return {
            "total_evaluations": len(period.teacher_evaluations),
            "total_rpp_submissions": len(period.rpp_submissions),
            "total_teachers": len(set(
                eval.teacher_id for eval in period.teacher_evaluations
            )) if period.teacher_evaluations else 0
        }
    
    async def is_period_active(self, period_id: int) -> bool:
        """Check if a period is active."""
        period = await self.get_by_id(period_id)
        return period.is_active if period else False
    
    async def get_period_if_active(self, period_id: int) -> Optional[Period]:
        """Get period only if it's active."""
        period = await self.get_by_id(period_id)
        return period if period and period.is_active else None