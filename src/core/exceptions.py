"""Custom exceptions for the application."""

from fastapi import HTTPException, status


class PeriodInactiveError(HTTPException):
    """Exception raised when trying to perform operations on inactive periods."""
    
    def __init__(self, period_id: int = None, message: str = None):
        if message is None:
            if period_id:
                message = f"Period {period_id} is not active. Operations are only allowed on active periods."
            else:
                message = "Period is not active. Operations are only allowed on active periods."
        
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )


class PeriodNotFoundError(HTTPException):
    """Exception raised when period is not found."""
    
    def __init__(self, period_id: int = None):
        message = f"Period {period_id} not found." if period_id else "Period not found."
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