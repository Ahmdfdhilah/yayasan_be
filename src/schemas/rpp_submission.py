"""RPP Submission schemas for request/response handling."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

from src.models.enums import RPPSubmissionStatus
from src.schemas.shared import BaseListResponse, MessageResponse


# ===== RPP SUBMISSION ITEM SCHEMAS =====

class RPPSubmissionItemBase(BaseModel):
    """Base schema for RPP submission item."""
    teacher_id: int = Field(..., description="Teacher user ID")
    period_id: int = Field(..., description="Period ID")
    rpp_submission_id: Optional[int] = Field(None, description="RPP submission ID")
    name: str = Field(..., max_length=255, description="Name/title of the RPP item")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description for the RPP item")
    file_id: Optional[int] = Field(None, description="Uploaded file ID")
    

class RPPSubmissionItemCreate(RPPSubmissionItemBase):
    """Schema for creating RPP submission item."""
    pass


class RPPSubmissionItemCreateRequest(BaseModel):
    """Schema for creating RPP submission item via API."""
    name: str = Field(..., max_length=255, description="Name/title of the RPP item")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description for the RPP item")


class RPPSubmissionItemUpdateRequest(BaseModel):
    """Schema for updating RPP submission item details via API."""
    name: str = Field(..., max_length=255, description="Name/title of the RPP item")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description for the RPP item")


class RPPSubmissionItemUpdate(BaseModel):
    """Schema for updating RPP submission item (file upload)."""
    file_id: int = Field(..., description="Uploaded file ID")


class RPPSubmissionItemResponse(BaseModel):
    """Schema for RPP submission item response."""
    id: int
    teacher_id: int
    period_id: int
    rpp_submission_id: Optional[int] = None
    name: str = Field(..., description="Name/title of the RPP item")
    description: Optional[str] = Field(None, description="Description of the RPP item")
    file_id: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    is_uploaded: bool = Field(..., description="Whether file has been uploaded")
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
    teacher_position: Optional[str] = Field(None, description="Teacher position/job title")
    organization_name: Optional[str] = Field(None, description="Organization/school name")
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


class GenerateRPPSubmissionsResponse(BaseModel):
    """Schema for admin generation response."""
    success: bool = Field(..., description="Whether the generation was successful")
    message: str = Field(..., description="Summary message")
    period_id: int = Field(..., description="Period ID for which submissions were generated")
    period_name: str = Field(..., description="Period name")
    generated_count: int = Field(..., description="Number of new submissions created")
    skipped_count: int = Field(..., description="Number of submissions skipped (already exist)")
    total_teachers: int = Field(..., description="Total number of eligible teachers")
    items_per_submission: int = Field(default=0, description="Number of initial RPP items per submission")
    total_items_created: int = Field(..., description="Total number of submission items created")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully generated 15 submissions for 15 teachers",
                "period_id": 5,
                "period_name": "Semester 1 - 2024/2025",
                "generated_count": 15,
                "skipped_count": 0,
                "total_teachers": 15,
                "items_per_submission": 3,
                "total_items_created": 45
            }
        }


# ===== LIST RESPONSES =====

class RPPSubmissionItemListResponse(BaseListResponse[RPPSubmissionItemResponse]):
    """List response for RPP submission items."""
    pass


class RPPSubmissionListResponse(BaseListResponse[RPPSubmissionResponse]):
    """List response for RPP submissions."""
    pass


# ===== FILTER AND QUERY SCHEMAS =====

class RPPSubmissionFilter(BaseModel):
    """Filter schema for RPP submissions."""
    teacher_id: Optional[int] = None
    period_id: Optional[int] = None
    status: Optional[RPPSubmissionStatus] = None
    reviewer_id: Optional[int] = None
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search by teacher name")
    organization_id: Optional[int] = None  # For filtering by organization
    submitter_role: Optional[str] = None  # For filtering by submitter role (guru, kepala_sekolah)
    
    # Date filters
    submitted_after: Optional[datetime] = None
    submitted_before: Optional[datetime] = None
    reviewed_after: Optional[datetime] = None
    reviewed_before: Optional[datetime] = None


class RPPSubmissionItemFilter(BaseModel):
    """Filter schema for RPP submission items."""
    teacher_id: Optional[int] = None
    period_id: Optional[int] = None
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