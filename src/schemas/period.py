"""Period schemas for API serialization."""

from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, validator, Field

from ..models.enums import PeriodType
from .shared import BaseListResponse


class PeriodBase(BaseModel):
    """Base period schema."""
    academic_year: str = Field(..., max_length=20, description="Academic year (e.g., '2023/2024')")
    semester: str = Field(..., max_length=20, description="Semester (e.g., 'Ganjil', 'Genap')")
    period_type: PeriodType = Field(..., description="Type of period")
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")
    description: Optional[str] = Field(None, description="Optional period description")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end_date is after start_date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class PeriodCreate(PeriodBase):
    """Schema for creating a new period."""
    pass


class PeriodUpdate(BaseModel):
    """Schema for updating an existing period."""
    academic_year: Optional[str] = Field(None, max_length=20)
    semester: Optional[str] = Field(None, max_length=20)
    period_type: Optional[PeriodType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end_date is after start_date if both are provided."""
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class PeriodResponse(PeriodBase):
    """Schema for period responses."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    class Config:
        from_attributes = True


class PeriodWithStats(PeriodResponse):
    """Period response with statistics."""
    total_teachers: int = Field(0, description="Total teachers in this period")
    total_evaluations: int = Field(0, description="Total evaluations in this period")
    total_rpp_submissions: int = Field(0, description="Total RPP submissions in this period")
    
    class Config:
        from_attributes = True


class PeriodActivate(BaseModel):
    """Schema for activating/deactivating periods."""
    is_active: bool = Field(..., description="Whether to activate or deactivate the period")


class PeriodFilter(BaseModel):
    """Schema for filtering periods."""
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    period_type: Optional[PeriodType] = None
    is_active: Optional[bool] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    end_date_from: Optional[date] = None
    end_date_to: Optional[date] = None


class PeriodListResponse(BaseListResponse[PeriodResponse]):
    """Standardized period list response."""
    pass