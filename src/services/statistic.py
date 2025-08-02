"""Statistic service for business logic."""

from typing import List, Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.statistic import StatisticRepository
from src.schemas.statistic import (
    StatisticCreate, 
    StatisticUpdate, 
    StatisticResponse, 
    StatisticFilterParams,
    StatisticListResponse
)
from src.models.statistic import Statistic


class StatisticService:
    """Service class for statistic operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.statistic_repo = StatisticRepository(session)

    async def create_statistic(self, statistic_data: StatisticCreate) -> StatisticResponse:
        """Create a new statistic."""
        try:
            # Convert to dict and handle None values
            data = statistic_data.model_dump(exclude_unset=True)
            
            # Create the statistic
            statistic = await self.statistic_repo.create(data)
            return StatisticResponse.model_validate(statistic)
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create statistic: {str(e)}"
            )

    async def get_statistic(self, statistic_id: int) -> StatisticResponse:
        """Get a statistic by ID."""
        statistic = await self.statistic_repo.get_by_id(statistic_id)
        if not statistic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Statistic not found"
            )
        return StatisticResponse.model_validate(statistic)

    async def update_statistic(self, statistic_id: int, update_data: StatisticUpdate) -> StatisticResponse:
        """Update a statistic."""
        # Check if statistic exists
        existing_statistic = await self.statistic_repo.get_by_id(statistic_id)
        if not existing_statistic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Statistic not found"
            )

        try:
            # Convert to dict and exclude unset values
            data = update_data.model_dump(exclude_unset=True)
            
            # Update the statistic
            updated_statistic = await self.statistic_repo.update(statistic_id, data)
            if not updated_statistic:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update statistic"
                )
            
            return StatisticResponse.model_validate(updated_statistic)
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update statistic: {str(e)}"
            )

    async def delete_statistic(self, statistic_id: int, hard_delete: bool = False) -> dict:
        """Delete a statistic (soft delete by default)."""
        # Check if statistic exists
        existing_statistic = await self.statistic_repo.get_by_id(statistic_id)
        if not existing_statistic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Statistic not found"
            )

        try:
            if hard_delete:
                success = await self.statistic_repo.hard_delete(statistic_id)
            else:
                success = await self.statistic_repo.soft_delete(statistic_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete statistic"
                )
            
            return {
                "message": f"Statistic {'permanently deleted' if hard_delete else 'deleted'} successfully",
                "deleted_id": statistic_id
            }
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete statistic: {str(e)}"
            )

    async def get_statistics(self, filters: StatisticFilterParams) -> StatisticListResponse:
        """Get statistics with filters and pagination."""
        try:
            statistics, total = await self.statistic_repo.get_all_filtered(filters)
            
            statistic_responses = [
                StatisticResponse.model_validate(statistic) for statistic in statistics
            ]
            
            return StatisticListResponse(
                items=statistic_responses,
                total=total,
                page=filters.page,
                size=filters.size,
                pages=(total + filters.size - 1) // filters.size if filters.size > 0 else 0
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve statistics: {str(e)}"
            )


    async def validate_display_order(self, display_order: int, exclude_id: Optional[int] = None) -> bool:
        """Validate if display_order is valid."""
        if display_order < 1:
            return False
            
        # Additional validation logic can be added here
        return True