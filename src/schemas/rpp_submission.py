"""RPP Submission schemas for PKG System API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from src.models.enums import RPPStatus
from src.schemas.shared import BaseListResponse
from src.schemas.filters import PaginationParams, SearchParams, DateRangeFilter


# ===== BASE SCHEMAS =====

class RPPSubmissionBase(BaseModel):
    """Base RPP submission schema."""
    academic_year: str = Field(..., min_length=1, max_length=20, description="Academic year (e.g., 2023/2024)")
    semester: str = Field(..., min_length=1, max_length=20, description="Semester (e.g., 1, 2, or Ganjil/Genap)")
    rpp_type: str = Field(..., min_length=1, max_length=100, description="Type of RPP")
    file_id: int = Field(..., description="Associated media file ID")
    
    @field_validator('academic_year')
    @classmethod
    def validate_academic_year(cls, year: str) -> str:
        """Validate academic year format."""
        return year.strip()
    
    @field_validator('semester')
    @classmethod
    def validate_semester(cls, semester: str) -> str:
        """Validate semester format."""
        return semester.strip()


# ===== REQUEST SCHEMAS =====

class RPPSubmissionCreate(RPPSubmissionBase):
    """Schema for creating an RPP submission."""
    teacher_id: int = Field(..., description="Teacher user ID")


class RPPSubmissionUpdate(BaseModel):
    """Schema for updating an RPP submission."""
    rpp_type: Optional[str] = Field(None, min_length=1, max_length=100)
    file_id: Optional[int] = None


class RPPSubmissionReview(BaseModel):
    """Schema for reviewing an RPP submission."""
    action: str = Field(..., pattern="^(approve|reject|revision)$", description="Review action")
    review_notes: Optional[str] = Field(None, description="Review notes/feedback")


class RPPSubmissionResubmit(BaseModel):
    """Schema for resubmitting an RPP."""
    file_id: int = Field(..., description="New file ID for resubmission")
    notes: Optional[str] = Field(None, description="Notes about the resubmission")


# ===== RESPONSE SCHEMAS =====

class RPPSubmissionResponse(BaseModel):
    """Schema for RPP submission response."""
    id: int
    teacher_id: int
    academic_year: str
    semester: str
    rpp_type: str
    file_id: int
    status: RPPStatus
    reviewer_id: Optional[int] = None
    review_notes: Optional[str] = None
    revision_count: int
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    academic_period: str = Field(..., description="Formatted academic period")
    is_pending: bool = Field(..., description="Whether submission is pending")
    is_approved: bool = Field(..., description="Whether submission is approved")
    is_rejected: bool = Field(..., description="Whether submission is rejected")
    needs_revision: bool = Field(..., description="Whether submission needs revision")
    
    # Related data
    teacher_name: Optional[str] = Field(None, description="Teacher name")
    teacher_email: Optional[str] = Field(None, description="Teacher email")
    reviewer_name: Optional[str] = Field(None, description="Reviewer name")
    file_name: Optional[str] = Field(None, description="Associated file name")
    file_url: Optional[str] = Field(None, description="File download URL")
    
    @classmethod
    def from_rpp_submission_model(cls, submission, include_relations: bool = False, base_url: str = "") -> "RPPSubmissionResponse":
        """Create RPPSubmissionResponse from RPPSubmission model."""
        data = {
            "id": submission.id,
            "teacher_id": submission.teacher_id,
            "academic_year": submission.academic_year,
            "semester": submission.semester,
            "rpp_type": submission.rpp_type,
            "file_id": submission.file_id,
            "status": submission.status,
            "reviewer_id": submission.reviewer_id,
            "review_notes": submission.review_notes,
            "revision_count": submission.revision_count,
            "submitted_at": submission.submitted_at,
            "reviewed_at": submission.reviewed_at,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
            "academic_period": f"{submission.academic_year} - {submission.semester}",
            "is_pending": submission.is_pending,
            "is_approved": submission.is_approved,
            "is_rejected": submission.is_rejected,
            "needs_revision": submission.needs_revision
        }
        
        if include_relations:
            data.update({
                "teacher_name": submission.teacher.display_name if hasattr(submission, 'teacher') and submission.teacher else None,
                "teacher_email": submission.teacher.email if hasattr(submission, 'teacher') and submission.teacher else None,
                "reviewer_name": submission.reviewer.display_name if hasattr(submission, 'reviewer') and submission.reviewer else None,
                "file_name": submission.file.file_name if hasattr(submission, 'file') and submission.file else None,
                "file_url": submission.file.get_url(base_url) if hasattr(submission, 'file') and submission.file else None
            })
        
        return cls(**data)
    
    model_config = {"from_attributes": True}


class RPPSubmissionListResponse(BaseListResponse[RPPSubmissionResponse]):
    """Standardized RPP submission list response."""
    pass


class RPPSubmissionSummary(BaseModel):
    """Schema for RPP submission summary (lighter response)."""
    id: int
    teacher_id: int
    academic_year: str
    semester: str
    rpp_type: str
    status: RPPStatus
    revision_count: int
    submitted_at: datetime
    
    # Related data
    teacher_name: Optional[str] = None
    
    @classmethod
    def from_rpp_submission_model(cls, submission) -> "RPPSubmissionSummary":
        """Create RPPSubmissionSummary from RPPSubmission model."""
        return cls(
            id=submission.id,
            teacher_id=submission.teacher_id,
            academic_year=submission.academic_year,
            semester=submission.semester,
            rpp_type=submission.rpp_type,
            status=submission.status,
            revision_count=submission.revision_count,
            submitted_at=submission.submitted_at,
            teacher_name=submission.teacher.display_name if hasattr(submission, 'teacher') and submission.teacher else None
        )
    
    model_config = {"from_attributes": True}


# ===== FILTER SCHEMAS =====

class RPPSubmissionFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for RPP submission listing."""
    
    # Submission-specific filters
    teacher_id: Optional[int] = Field(None, description="Filter by teacher ID")
    reviewer_id: Optional[int] = Field(None, description="Filter by reviewer ID")
    academic_year: Optional[str] = Field(None, description="Filter by academic year")
    semester: Optional[str] = Field(None, description="Filter by semester")
    rpp_type: Optional[str] = Field(None, description="Filter by RPP type")
    status: Optional[RPPStatus] = Field(None, description="Filter by submission status")
    has_reviewer: Optional[bool] = Field(None, description="Filter submissions with/without reviewer")
    needs_review: Optional[bool] = Field(None, description="Filter submissions needing review")
    high_revision_count: Optional[int] = Field(None, ge=1, description="Filter submissions with revision count >= N")
    
    # Date filters
    submitted_after: Optional[datetime] = Field(None, description="Filter submissions after this date")
    submitted_before: Optional[datetime] = Field(None, description="Filter submissions before this date")
    reviewed_after: Optional[datetime] = Field(None, description="Filter reviewed after this date")
    reviewed_before: Optional[datetime] = Field(None, description="Filter reviewed before this date")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in RPP type, teacher name, or review notes")
    
    # Override default sort
    sort_by: str = Field(default="submitted_at", description="Sort field")


# ===== BULK OPERATIONS =====

class RPPSubmissionBulkReview(BaseModel):
    """Schema for bulk RPP submission review."""
    submission_ids: List[int] = Field(..., min_items=1, description="List of submission IDs")
    action: str = Field(..., pattern="^(approve|reject)$", description="Bulk review action")
    review_notes: Optional[str] = Field(None, description="Bulk review notes")


class RPPSubmissionBulkAssignReviewer(BaseModel):
    """Schema for bulk reviewer assignment."""
    submission_ids: List[int] = Field(..., min_items=1, description="List of submission IDs")
    reviewer_id: int = Field(..., description="Reviewer user ID")


# ===== ANALYTICS SCHEMAS =====

class RPPSubmissionAnalytics(BaseModel):
    """Schema for RPP submission analytics."""
    total_submissions: int
    by_status: Dict[str, int] = Field(description="Submissions count by status")
    by_academic_year: Dict[str, int] = Field(description="Submissions count by academic year")
    by_semester: Dict[str, int] = Field(description="Submissions count by semester")
    by_rpp_type: Dict[str, int] = Field(description="Submissions count by RPP type")
    avg_review_time_hours: Optional[float] = Field(None, description="Average review time in hours")
    avg_revision_count: float = Field(description="Average revision count")
    pending_reviews: int = Field(description="Number of pending reviews")
    overdue_reviews: int = Field(description="Number of overdue reviews (>7 days)")


class TeacherRPPProgress(BaseModel):
    """Schema for individual teacher RPP progress."""
    teacher_id: int
    teacher_name: str
    teacher_email: str
    total_submitted: int
    approved: int
    rejected: int
    pending: int
    revision_needed: int
    completion_rate: float = Field(description="Completion rate as percentage")
    avg_revision_count: float
    last_submission: Optional[datetime] = None


class RPPSubmissionStats(BaseModel):
    """Schema for comprehensive RPP submission statistics."""
    summary: RPPSubmissionAnalytics
    teacher_progress: List[TeacherRPPProgress]
    recent_activity: Dict[str, int] = Field(description="Recent activity counts")
    submission_trends: Dict[str, List[int]] = Field(description="Submission trends over time")