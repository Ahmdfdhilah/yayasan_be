"""RPP Submission schemas for request/response handling."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

from src.models.enums import RPPType, RPPSubmissionStatus
from src.schemas.shared import BaseListResponse, MessageResponse


# ===== RPP SUBMISSION ITEM SCHEMAS =====

class RPPSubmissionItemBase(BaseModel):
    """Base schema for RPP submission item."""
    teacher_id: int = Field(..., description="Teacher user ID")
    period_id: int = Field(..., description="Period ID")
    rpp_type: RPPType = Field(..., description="Type of RPP")
    file_id: Optional[int] = Field(None, description="Uploaded file ID")
    

class RPPSubmissionItemCreate(RPPSubmissionItemBase):
    """Schema for creating RPP submission item."""
    pass


class RPPSubmissionItemUpdate(BaseModel):
    """Schema for updating RPP submission item (file upload)."""
    file_id: int = Field(..., description="Uploaded file ID")


class RPPSubmissionItemResponse(RPPSubmissionItemBase):
    """Schema for RPP submission item response."""
    id: int
    uploaded_at: Optional[datetime] = None
    is_uploaded: bool = Field(..., description="Whether file has been uploaded")
    rpp_type_display_name: str = Field(..., description="Display name for RPP type")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Nested data
    teacher_name: Optional[str] = Field(None, description="Teacher name")
    period_name: Optional[str] = Field(None, description="Period name")
    file_name: Optional[str] = Field(None, description="Uploaded file name")
    
    model_config = ConfigDict(from_attributes=True)


# ===== RPP SUBMISSION SCHEMAS =====

class RPPSubmissionBase(BaseModel):
    """Base schema for RPP submission."""
    teacher_id: int = Field(..., description="Teacher user ID")
    period_id: int = Field(..., description="Period ID")
    

class RPPSubmissionCreate(RPPSubmissionBase):
    """Schema for creating RPP submission."""
    pass


class RPPSubmissionUpdate(BaseModel):
    """Schema for updating RPP submission status."""
    status: RPPSubmissionStatus = Field(..., description="Submission status")
    review_notes: Optional[str] = Field(None, max_length=1000, description="Review notes")


class RPPSubmissionSubmitRequest(BaseModel):
    """Schema for submitting RPP for approval."""
    pass  # No additional fields needed


class RPPSubmissionReviewRequest(BaseModel):
    """Schema for reviewing RPP submission."""
    status: RPPSubmissionStatus = Field(..., description="Review decision")
    review_notes: Optional[str] = Field(None, max_length=1000, description="Review notes")
    
    @field_validator('status')
    @classmethod
    def validate_review_status(cls, status: RPPSubmissionStatus) -> RPPSubmissionStatus:
        """Validate that status is a valid review decision."""
        valid_statuses = [
            RPPSubmissionStatus.APPROVED,
            RPPSubmissionStatus.REJECTED,
            RPPSubmissionStatus.REVISION_NEEDED
        ]
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {[s.value for s in valid_statuses]}")
        return status


class RPPSubmissionResponse(RPPSubmissionBase):
    """Schema for RPP submission response."""
    id: int
    status: RPPSubmissionStatus
    reviewer_id: Optional[int] = None
    review_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    completion_percentage: float = Field(..., description="Completion percentage (0-100)")
    can_be_submitted: bool = Field(..., description="Whether submission can be submitted for approval")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Nested data
    teacher_name: Optional[str] = Field(None, description="Teacher name")
    reviewer_name: Optional[str] = Field(None, description="Reviewer name")
    period_name: Optional[str] = Field(None, description="Period name")
    items: List[RPPSubmissionItemResponse] = Field(default_factory=list, description="RPP submission items")
    
    model_config = ConfigDict(from_attributes=True)


class RPPSubmissionDetailResponse(RPPSubmissionResponse):
    """Detailed schema for RPP submission with full item details."""
    pass  # Already includes items


# ===== ADMIN SCHEMAS =====

class GenerateRPPSubmissionsRequest(BaseModel):
    """Schema for admin request to generate RPP submissions."""
    period_id: int = Field(..., description="Period ID to generate submissions for")


class GenerateRPPSubmissionsResponse(MessageResponse):
    """Schema for admin generation response."""
    generated_count: int = Field(..., description="Number of submissions generated")
    skipped_count: int = Field(..., description="Number of submissions skipped (already exist)")
    total_teachers: int = Field(..., description="Total number of teachers processed")


# ===== LIST RESPONSES =====

class RPPSubmissionItemListResponse(BaseListResponse):
    """List response for RPP submission items."""
    data: List[RPPSubmissionItemResponse]


class RPPSubmissionListResponse(BaseListResponse):
    """List response for RPP submissions."""
    data: List[RPPSubmissionResponse]


# ===== FILTER AND QUERY SCHEMAS =====

class RPPSubmissionFilter(BaseModel):
    """Filter schema for RPP submissions."""
    teacher_id: Optional[int] = None
    period_id: Optional[int] = None
    status: Optional[RPPSubmissionStatus] = None
    reviewer_id: Optional[int] = None
    organization_id: Optional[int] = None  # For filtering by organization
    
    # Date filters
    submitted_after: Optional[datetime] = None
    submitted_before: Optional[datetime] = None
    reviewed_after: Optional[datetime] = None
    reviewed_before: Optional[datetime] = None


class RPPSubmissionItemFilter(BaseModel):
    """Filter schema for RPP submission items."""
    teacher_id: Optional[int] = None
    period_id: Optional[int] = None
    rpp_type: Optional[RPPType] = None
    is_uploaded: Optional[bool] = None
    organization_id: Optional[int] = None  # For filtering by organization


# ===== STATISTICS SCHEMAS =====

class RPPSubmissionStats(BaseModel):
    """Statistics schema for RPP submissions."""
    total_submissions: int = Field(..., description="Total number of submissions")
    draft_count: int = Field(..., description="Number of draft submissions")
    pending_count: int = Field(..., description="Number of pending submissions")
    approved_count: int = Field(..., description="Number of approved submissions")
    rejected_count: int = Field(..., description="Number of rejected submissions")
    revision_needed_count: int = Field(..., description="Number of submissions needing revision")
    completion_rate: float = Field(..., description="Overall completion rate percentage")


class RPPSubmissionPeriodStats(BaseModel):
    """Period-specific statistics for RPP submissions."""
    period_id: int
    period_name: str
    stats: RPPSubmissionStats


class RPPSubmissionOrganizationStats(BaseModel):
    """Organization-specific statistics for RPP submissions."""
    organization_id: int
    organization_name: str
    stats: RPPSubmissionStats
    periods: List[RPPSubmissionPeriodStats] = Field(default_factory=list)


# ===== DASHBOARD SCHEMAS =====

class RPPSubmissionDashboard(BaseModel):
    """Dashboard data for RPP submissions."""
    current_period_stats: Optional[RPPSubmissionPeriodStats] = None
    recent_submissions: List[RPPSubmissionResponse] = Field(default_factory=list)
    pending_reviews: List[RPPSubmissionResponse] = Field(default_factory=list)
    my_submissions: List[RPPSubmissionResponse] = Field(default_factory=list)  # For teachers
    overall_stats: RPPSubmissionStats