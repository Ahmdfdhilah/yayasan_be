"""Period service for universal period management."""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from src.repositories.period import PeriodRepository
from src.schemas.period import (
    PeriodCreate, PeriodUpdate, PeriodResponse, PeriodWithStats,
    PeriodFilter, PeriodActivate, PeriodListResponse
)
from src.schemas.shared import MessageResponse


class PeriodService:
    """Period service for universal period management."""
    
    def __init__(self, period_repo: PeriodRepository):
        self.period_repo = period_repo
    
    async def create_period(self, period_data: PeriodCreate, created_by: Optional[int] = None) -> PeriodResponse:
        """Create a new period."""
        # Validate that period doesn't already exist
        exists = await self.period_repo.exists_by_academic_period(
            period_data.academic_year,
            period_data.semester
        )
        
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Period already exists for {period_data.academic_year} - {period_data.semester}"
            )
        
        # Create period
        period = await self.period_repo.create(period_data, created_by)
        return PeriodResponse.from_orm(period)
    
    async def get_period(self, period_id: int) -> PeriodResponse:
        """Get period by ID."""
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Period not found"
            )
        
        return PeriodResponse.from_orm(period)
    
    async def get_period_with_stats(self, period_id: int) -> PeriodWithStats:
        """Get period with statistics."""
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Period not found"
            )
        
        # Get statistics
        stats = await self.period_repo.get_period_stats(period_id)
        
        # Convert to response with stats
        period_response = PeriodResponse.from_orm(period)
        return PeriodWithStats(
            **period_response.dict(),
            total_teachers=stats.get("total_teachers", 0),
            total_evaluations=stats.get("total_evaluations", 0),
            total_rpp_submissions=stats.get("total_rpp_submissions", 0)
        )
    
    async def get_periods(
        self,
        filter_params: Optional[PeriodFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> PeriodListResponse:
        """Get filtered periods with pagination."""
        periods, total = await self.period_repo.get_filtered(filter_params, skip, limit)
        
        period_responses = [PeriodResponse.from_orm(period) for period in periods]
        
        return PeriodListResponse(
            items=period_responses,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    
    async def get_active_period(self) -> PeriodResponse:
        """Get all active periods."""
        period = await self.period_repo.get_active_period()
        return [PeriodResponse.from_orm(period)]
    
    async def get_current_periods(self) -> List[PeriodResponse]:
        """Get periods that are currently active based on dates."""
        periods = await self.period_repo.get_current_periods()
        return [PeriodResponse.from_orm(period) for period in periods]
    
    async def update_period(
        self,
        period_id: int,
        period_data: PeriodUpdate,
        updated_by: Optional[int] = None
    ) -> PeriodResponse:
        """Update an existing period."""
        period = await self.period_repo.update(period_id, period_data, updated_by)
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Period not found"
            )
        
        return PeriodResponse.from_orm(period)
    
    async def activate_period(self, period_id: int, updated_by: Optional[int] = None) -> PeriodResponse:
        """Activate a period. Business rule: only one period can be active at a time."""
        # Check if activation is allowed
        can_activate, reason = await self.period_repo.can_activate_period(period_id)
        
        if not can_activate:
            if "not found" in reason.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=reason
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=reason
                )
        
        # If already active, just return the period
        if "already active" in reason.lower():
            period = await self.period_repo.get_by_id(period_id)
            return PeriodResponse.from_orm(period)
        
        # Activate the period
        period = await self.period_repo.activate(period_id, updated_by)
        if not period:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate period"
            )
        
        return PeriodResponse.from_orm(period)
    
    async def get_active_period(self) -> Optional[PeriodResponse]:
        """Get the currently active period."""
        period = await self.period_repo.get_active_period()
        if not period:
            return None
        
        return PeriodResponse.from_orm(period)
    
    async def deactivate_period(self, period_id: int, updated_by: Optional[int] = None) -> PeriodResponse:
        """Deactivate a period."""
        period = await self.period_repo.deactivate(period_id, updated_by)
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Period not found"
            )
        
        return PeriodResponse.from_orm(period)
    
    async def toggle_period_status(
        self,
        period_id: int,
        activation_data: PeriodActivate,
        updated_by: Optional[int] = None
    ) -> PeriodResponse:
        """Toggle period activation status."""
        if activation_data.is_active:
            return await self.activate_period(period_id, updated_by)
        else:
            return await self.deactivate_period(period_id, updated_by)
    
    async def delete_period(self, period_id: int) -> MessageResponse:
        """Delete a period if it has no associated data."""
        success = await self.period_repo.delete(period_id)
        
        if not success:
            # Try to get the period to check if it exists
            period = await self.period_repo.get_by_id(period_id)
            if not period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Period not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete period with associated evaluations or submissions"
                )
        
        return MessageResponse(message="Period deleted successfully")
    
    async def validate_period_dates(self, start_date, end_date) -> bool:
        """Validate period dates."""
        return start_date < end_date