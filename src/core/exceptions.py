"""Custom exceptions for the application."""

from fastapi import HTTPException, status
from ..utils.messages import get_message


class PeriodInactiveError(HTTPException):
    """Exception raised when trying to perform operations on inactive periods."""
    
    def __init__(self, period_id: int = None, message: str = None):
        if message is None:
            if period_id:
                message = get_message("period", "not_active_with_id", period_id=period_id)
            else:
                message = get_message("period", "not_active")
        
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )


class PeriodNotFoundError(HTTPException):
    """Exception raised when period is not found."""
    
    def __init__(self, period_id: int = None):
        message = get_message("period", "not_found_with_id", period_id=period_id) if period_id else get_message("period", "not_found")
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class BusinessLogicError(HTTPException):
    """Exception for business logic violations."""
    
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )