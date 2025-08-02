"""Program schemas for request/response validation."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from src.schemas.shared import BaseListResponse


class ProgramBase(BaseModel):
    """Base schema for Program."""
    title: str = Field(..., min_length=1, max_length=255, description="Program title")
    excerpt: Optional[str] = Field(None, max_length=500, description="Short program summary")
    description: Optional[str] = Field(None, description="Full program description")
    img_url: Optional[str] = Field(None, max_length=500, description="Program image URL")


class ProgramCreate(ProgramBase):
    """Schema for creating a new Program."""
    pass


class ProgramUpdate(BaseModel):
    """Schema for updating a Program."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    excerpt: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    img_url: Optional[str] = Field(None, max_length=500)


class ProgramResponse(BaseModel):
    """Schema for Program response."""
    id: int
    title: str
    excerpt: Optional[str] = None
    description: Optional[str] = None
    img_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProgramListResponse(BaseListResponse[ProgramResponse]):
    """Standardized program list response."""
    pass


class ProgramFilterParams(BaseModel):
    """Filter parameters for program listing."""
    
    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Number of items to return")
    
    # Search
    search: Optional[str] = Field(default=None, description="Search in title, excerpt, or description")