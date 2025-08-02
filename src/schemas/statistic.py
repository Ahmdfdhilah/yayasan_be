"""Statistic schemas for request/response validation."""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class StatisticBase(BaseModel):
    """Base statistic schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Statistic title")
    description: Optional[str] = Field(None, description="Statistic description")
    stats: str = Field(..., min_length=1, max_length=255, description="Statistics value with suffix")
    img_url: Optional[str] = Field(None, max_length=500, description="Icon image URL")
    display_order: Optional[int] = Field(None, ge=1, description="Display order for sorting")


class StatisticCreate(StatisticBase):
    """Schema for creating a new statistic."""
    pass


class StatisticUpdate(BaseModel):
    """Schema for updating a statistic."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Statistic title")
    description: Optional[str] = Field(None, description="Statistic description")
    stats: Optional[str] = Field(None, min_length=1, max_length=255, description="Statistics value with suffix")
    img_url: Optional[str] = Field(None, max_length=500, description="Icon image URL")
    display_order: Optional[int] = Field(None, ge=1, description="Display order for sorting")


class StatisticResponse(StatisticBase):
    """Schema for statistic response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatisticListResponse(BaseModel):
    """Schema for paginated statistic list response."""
    items: List[StatisticResponse]
    total: int
    page: int
    size: int
    pages: int

    @validator('pages', pre=False, always=True)
    def calculate_pages(cls, v, values):
        """Calculate pages based on total and size."""
        total = values.get('total', 0)
        size = values.get('size', 1)
        return (total + size - 1) // size if size > 0 else 0


class StatisticFilterParams(BaseModel):
    """Schema for statistic filtering parameters."""
    search: Optional[str] = Field(None, description="Search term for title, description, or stats")
    sort_by: str = Field("display_order", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        allowed_fields = ["title", "stats", "display_order", "created_at", "updated_at"]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of {allowed_fields}")
        return v




