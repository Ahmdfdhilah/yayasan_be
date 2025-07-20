"""Period validation utilities."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.period import PeriodRepository
from src.core.exceptions import PeriodInactiveError, PeriodNotFoundError


class PeriodValidator:
    """Utility class for period validation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.period_repo = PeriodRepository(session)
    
    async def validate_period_is_active(self, period_id: int) -> None:
        """
        Validate that a period exists and is active.
        
        Args:
            period_id: The period ID to validate
            
        Raises:
            PeriodNotFoundError: If period doesn't exist
            PeriodInactiveError: If period exists but is not active
        """
        period = await self.period_repo.get_by_id(period_id)
        
        if not period:
            raise PeriodNotFoundError(period_id)
        
        if not period.is_active:
            raise PeriodInactiveError(
                period_id, 
                f"Period '{period.academic_year} - {period.semester}' is not active. "
                f"Operations are only allowed on active periods."
            )
    
    async def get_active_period_or_raise(self, period_id: int):
        """
        Get period if it exists and is active, otherwise raise exception.
        
        Args:
            period_id: The period ID to get
            
        Returns:
            Period object if active
            
        Raises:
            PeriodNotFoundError: If period doesn't exist
            PeriodInactiveError: If period exists but is not active
        """
        await self.validate_period_is_active(period_id)
        return await self.period_repo.get_by_id(period_id)


async def validate_period_is_active(session: AsyncSession, period_id: int) -> None:
    """
    Standalone function to validate period is active.
    
    Args:
        session: Database session
        period_id: The period ID to validate
        
    Raises:
        PeriodNotFoundError: If period doesn't exist
        PeriodInactiveError: If period exists but is not active
    """
    validator = PeriodValidator(session)
    await validator.validate_period_is_active(period_id)


async def get_active_period_or_raise(session: AsyncSession, period_id: int):
    """
    Standalone function to get active period or raise exception.
    
    Args:
        session: Database session
        period_id: The period ID to get
        
    Returns:
        Period object if active
        
    Raises:
        PeriodNotFoundError: If period doesn't exist
        PeriodInactiveError: If period exists but is not active
    """
    validator = PeriodValidator(session)
    return await validator.get_active_period_or_raise(period_id)