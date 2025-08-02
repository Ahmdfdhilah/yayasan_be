"""Mitra schemas for request/response validation."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from src.schemas.shared import BaseListResponse


class MitraBase(BaseModel):
    """Base schema for Mitra."""
    title: str = Field(..., min_length=1, max_length=255, description="Mitra title")
    description: Optional[str] = Field(None, description="Mitra description")
    img_url: Optional[str] = Field(None, max_length=500, description="Mitra image URL")


class MitraCreate(MitraBase):
    """Schema for creating a new Mitra."""
    pass


class MitraUpdate(BaseModel):
    """Schema for updating a Mitra."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    img_url: Optional[str] = Field(None, max_length=500)


class MitraResponse(BaseModel):
    """Schema for Mitra response."""
    id: int
    title: str
    description: Optional[str] = None
    img_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class MitraListResponse(BaseListResponse[MitraResponse]):
    """Standardized mitra list response."""
    pass


class MitraFilterParams(BaseModel):
    """Filter parameters for mitra listing."""
    
    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Number of items to return")
    
    # Search
    search: Optional[str] = Field(default=None, description="Search in title or description")