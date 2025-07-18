"""Filter schemas for API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date

from src.models.enums import UserRole, UserStatus


class UserFilterParams(BaseModel):
    """Filter parameters for user listing."""
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    # Search and filtering
    search: Optional[str] = Field(default=None, description="Search in name, email, or username")
    role: Optional[UserRole] = Field(default=None, description="Filter by user role")
    status: Optional[UserStatus] = Field(default=None, description="Filter by user status")
    organization_id: Optional[int] = Field(default=None, description="Filter by organization")
    
    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
    
    # Date filtering
    created_after: Optional[date] = Field(default=None, description="Filter users created after this date")
    created_before: Optional[date] = Field(default=None, description="Filter users created before this date")
    
    # Active/inactive filter
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")


class UsernameGenerationPreview(BaseModel):
    """Preview data for username generation."""
    
    nama: str = Field(..., min_length=1, max_length=200)
    role: UserRole = Field(...)
    inspektorat: Optional[str] = Field(default=None, max_length=100)


class UsernameGenerationResponse(BaseModel):
    """Response for username generation preview."""
    
    original_nama: str
    inspektorat: Optional[str]
    role: UserRole
    generated_username: str
    is_available: bool
    suggested_alternatives: list[str] = Field(default_factory=list)


class PaginationParams(BaseModel):
    """Base pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")


class SearchParams(BaseModel):
    """Base search parameters."""
    
    q: Optional[str] = Field(default=None, description="Search query")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class DateRangeFilter(BaseModel):
    """Date range filter parameters."""
    
    start_date: Optional[date] = Field(default=None, description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date")