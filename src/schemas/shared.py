"""Shared schemas for API responses."""

from typing import List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseListResponse(BaseModel, Generic[T]):
    """Base list response with pagination."""
    
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


class MessageResponse(BaseModel):
    """Standard message response."""
    
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")
    data: Optional[dict] = Field(default=None, description="Additional response data")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error description")
    code: Optional[str] = Field(default=None, description="Error code")


class SuccessResponse(BaseModel):
    """Standard success response."""
    
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(default=None, description="Response data")


class StatusResponse(BaseModel):
    """Status check response."""
    
    status: str = Field(..., description="Service status")
    version: Optional[str] = Field(default=None, description="API version")
    timestamp: Optional[str] = Field(default=None, description="Response timestamp")


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    
    field: str = Field(..., description="Field name with error")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    
    error: str = Field(default="Validation Error", description="Error type")
    details: List[ValidationErrorDetail] = Field(..., description="Validation error details")