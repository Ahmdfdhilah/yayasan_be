"""Filter schemas for API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from src.models.enums import UserRole, UserStatus, OrganizationType, RPPStatus


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


# ===== ORGANIZATION FILTERS =====

class OrganizationFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for organization listing."""
    
    # Organization-specific filters
    type: Optional[OrganizationType] = Field(None, description="Filter by organization type")
    has_users: Optional[bool] = Field(None, description="Filter organizations with/without users")


# ===== USER ROLE FILTERS =====

class UserRoleFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for user role listing."""
    
    # Role-specific filters
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    role_name: Optional[str] = Field(None, description="Filter by role name")
    organization_id: Optional[int] = Field(None, description="Filter by organization ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    has_permissions: Optional[bool] = Field(None, description="Filter roles with/without permissions")
    expires_soon: Optional[int] = Field(None, ge=1, le=365, description="Filter roles expiring within N days")


# ===== MEDIA FILE FILTERS =====

class MediaFileFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for media file listing."""
    
    # File-specific filters
    file_type: Optional[str] = Field(None, description="Filter by file type/extension")
    file_category: Optional[str] = Field(None, description="Filter by file category (image, document, etc.)")
    uploader_id: Optional[int] = Field(None, description="Filter by uploader user ID")
    organization_id: Optional[int] = Field(None, description="Filter by organization ID")
    is_public: Optional[bool] = Field(None, description="Filter by public/private status")
    min_size: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")


# ===== RPP SUBMISSION FILTERS =====

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
    high_revision_count: Optional[int] = Field(None, ge=1, description="Filter submissions with high revision count")
    submitted_after: Optional[datetime] = Field(None, description="Filter submissions after this date")
    submitted_before: Optional[datetime] = Field(None, description="Filter submissions before this date")
    reviewed_after: Optional[datetime] = Field(None, description="Filter submissions reviewed after this date")
    reviewed_before: Optional[datetime] = Field(None, description="Filter submissions reviewed before this date")


# ===== EVALUATION FILTERS =====

class EvaluationAspectFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for evaluation aspect listing."""
    
    # Aspect-specific filters
    organization_id: Optional[int] = Field(None, description="Filter by organization ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    has_evaluations: Optional[bool] = Field(None, description="Filter aspects with/without evaluations")
    min_weight: Optional[Decimal] = Field(None, ge=0, description="Minimum weight")
    max_weight: Optional[Decimal] = Field(None, ge=0, description="Maximum weight")
    min_score: Optional[int] = Field(None, ge=0, description="Minimum max score")
    max_score: Optional[int] = Field(None, description="Maximum max score")


class TeacherEvaluationFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for teacher evaluation listing."""
    
    # Evaluation-specific filters
    evaluator_id: Optional[int] = Field(None, description="Filter by evaluator ID")
    teacher_id: Optional[int] = Field(None, description="Filter by teacher ID")
    aspect_id: Optional[int] = Field(None, description="Filter by evaluation aspect ID")
    academic_year: Optional[str] = Field(None, description="Filter by academic year")
    semester: Optional[str] = Field(None, description="Filter by semester")
    min_score: Optional[int] = Field(None, ge=0, description="Minimum score")
    max_score: Optional[int] = Field(None, description="Maximum score")
    has_notes: Optional[bool] = Field(None, description="Filter evaluations with/without notes")
    evaluated_after: Optional[datetime] = Field(None, description="Filter evaluations after this date")
    evaluated_before: Optional[datetime] = Field(None, description="Filter evaluations before this date")


class EvaluationResultFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for evaluation result listing."""
    
    # Result-specific filters
    teacher_id: Optional[int] = Field(None, description="Filter by teacher ID")
    evaluator_id: Optional[int] = Field(None, description="Filter by evaluator ID")
    academic_year: Optional[str] = Field(None, description="Filter by academic year")
    semester: Optional[str] = Field(None, description="Filter by semester")
    grade_category: Optional[str] = Field(None, description="Filter by grade category")
    has_recommendations: Optional[bool] = Field(None, description="Filter results with/without recommendations")
    min_performance: Optional[Decimal] = Field(None, ge=0, le=100, description="Minimum performance score")
    max_performance: Optional[Decimal] = Field(None, ge=0, le=100, description="Maximum performance score")
    min_score_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Minimum score percentage")
    evaluated_after: Optional[datetime] = Field(None, description="Filter results evaluated after this date")
    evaluated_before: Optional[datetime] = Field(None, description="Filter results evaluated before this date")