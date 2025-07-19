"""RPP Submission API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.auth.permissions import (
    get_current_active_user, 
    admin_required, 
    management_roles_required,
    require_rpp_submission_permission,
    require_rpp_approval_permission
)
from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.user import UserRepository
from src.repositories.media_file import MediaFileRepository
from src.services.rpp_submission import RPPSubmissionService
from src.schemas.rpp_submission import (
    RPPSubmissionCreate,
    RPPSubmissionUpdate,
    RPPSubmissionResponse,
    RPPSubmissionListResponse,
    RPPSubmissionReview,
    RPPSubmissionResubmit,
    RPPSubmissionBulkReview,
    RPPSubmissionBulkAssignReviewer,
    RPPSubmissionAnalytics,
    TeacherRPPProgress,
    RPPSubmissionStats
)
from src.schemas.rpp_submission import RPPSubmissionFilterParams
from src.schemas.shared import MessageResponse

router = APIRouter(prefix="/rpp-submissions", tags=["RPP Submissions"])


def get_submission_service(db: AsyncSession = Depends(get_db)) -> RPPSubmissionService:
    """Get RPP submission service."""
    submission_repo = RPPSubmissionRepository(db)
    user_repo = UserRepository(db)
    media_repo = MediaFileRepository(db)
    return RPPSubmissionService(submission_repo, user_repo, media_repo)


# ===== BASIC CRUD OPERATIONS =====

@router.post(
    "/",
    response_model=RPPSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create RPP submission"
)
async def create_submission(
    submission_data: RPPSubmissionCreate,
    current_user: dict = Depends(require_rpp_submission_permission()),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Create a new RPP submission. Only teachers (guru) can submit RPPs."""
    return await submission_service.create_submission(submission_data, current_user["id"])


# Move specific routes before parameterized routes to avoid conflicts

@router.get(
    "/pending-reviews",
    response_model=List[RPPSubmissionResponse],
    summary="Get pending reviews"
)
async def get_pending_reviews(
    reviewer_id: Optional[int] = Query(None, description="Filter by reviewer ID"),
    current_user: dict = Depends(get_current_active_user),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Get all pending review submissions."""
    return await submission_service.get_pending_reviews(reviewer_id, current_user)


@router.get(
    "/overdue-reviews",
    response_model=List[RPPSubmissionResponse],
    summary="Get overdue reviews"
)
async def get_overdue_reviews(
    days_threshold: int = Query(7, ge=1, le=30, description="Days threshold for overdue"),
    current_user: dict = Depends(management_roles_required),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """
    Get submissions that are overdue for review.
    
    Requires management role (super_admin, admin, or kepala_sekolah).
    """
    return await submission_service.get_overdue_reviews(days_threshold, current_user)


@router.get(
    "/period/{period_id}",
    response_model=List[RPPSubmissionResponse],
    summary="Get submissions by period"
)
async def get_submissions_by_period(
    period_id: int,
    current_user: dict = Depends(get_current_active_user),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Get all RPP submissions for a specific academic period."""
    return await submission_service.get_submissions_by_period(period_id, current_user)


@router.get(
    "/teacher/{teacher_id}",
    response_model=List[RPPSubmissionResponse],
    summary="Get teacher submissions"
)
async def get_teacher_submissions(
    teacher_id: int,
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    current_user: dict = Depends(get_current_active_user),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Get all RPP submissions for a specific teacher."""
    return await submission_service.get_teacher_submissions(teacher_id, academic_year, current_user)


@router.get(
    "/{submission_id}",
    response_model=RPPSubmissionResponse,
    summary="Get RPP submission by ID"
)
async def get_submission(
    submission_id: int,
    current_user: dict = Depends(get_current_active_user),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Get RPP submission by ID."""
    return await submission_service.get_submission_by_id(submission_id, current_user)


@router.put(
    "/{submission_id}",
    response_model=RPPSubmissionResponse,
    summary="Update RPP submission"
)
async def update_submission(
    submission_id: int,
    submission_data: RPPSubmissionUpdate,
    current_user: dict = Depends(require_rpp_submission_permission()),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Update RPP submission (only pending submissions can be updated). Only teachers can update their own RPPs."""
    return await submission_service.update_submission(submission_id, submission_data)


@router.delete(
    "/{submission_id}",
    response_model=MessageResponse,
    summary="Delete RPP submission"
)
async def delete_submission(
    submission_id: int,
    current_user: dict = Depends(require_rpp_submission_permission()),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Delete RPP submission (only pending or rejected submissions can be deleted). Only teachers can delete their own RPPs."""
    return await submission_service.delete_submission(submission_id)


# ===== REVIEW OPERATIONS =====

@router.post(
    "/{submission_id}/review",
    response_model=RPPSubmissionResponse,
    summary="Review RPP submission"
)
async def review_submission(
    submission_id: int,
    review_data: RPPSubmissionReview,
    current_user: dict = Depends(require_rpp_approval_permission()),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """
    Review RPP submission (approve, reject, or request revision).
    
    Only school principals (kepala_sekolah) can approve RPPs for their organization.
    """
    return await submission_service.review_submission(
        submission_id, current_user["id"], review_data
    )


@router.post(
    "/{submission_id}/resubmit",
    response_model=RPPSubmissionResponse,
    summary="Resubmit RPP submission"
)
async def resubmit_submission(
    submission_id: int,
    resubmit_data: RPPSubmissionResubmit,
    current_user: dict = Depends(require_rpp_submission_permission()),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Resubmit RPP submission with new file (for rejected or revision-needed submissions). Only teachers can resubmit their own RPPs."""
    return await submission_service.resubmit_submission(submission_id, resubmit_data)


@router.patch(
    "/{submission_id}/assign-reviewer",
    response_model=RPPSubmissionResponse,
    summary="Assign reviewer to submission"
)
async def assign_reviewer(
    submission_id: int,
    reviewer_id: int = Query(..., description="Reviewer user ID"),
    current_user: dict = Depends(admin_required),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """
    Assign reviewer to RPP submission.
    
    Requires admin role.
    """
    return await submission_service.assign_reviewer(submission_id, reviewer_id)


# ===== LISTING AND FILTERING =====

@router.get(
    "/",
    response_model=RPPSubmissionListResponse,
    summary="List RPP submissions"
)
async def list_submissions(
    filters: RPPSubmissionFilterParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """List RPP submissions with filtering and pagination."""
    return await submission_service.get_submissions(filters, current_user)


# Duplicate routes removed - moved to above to fix routing conflicts


# ===== BULK OPERATIONS =====

@router.post(
    "/bulk/review",
    response_model=MessageResponse,
    summary="Bulk review submissions"
)
async def bulk_review_submissions(
    bulk_data: RPPSubmissionBulkReview,
    current_user: dict = Depends(require_rpp_approval_permission()),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """
    Bulk review RPP submissions (approve or reject multiple submissions).
    
    Only school principals (kepala_sekolah) can approve RPPs for their organization.
    """
    return await submission_service.bulk_review_submissions(bulk_data, current_user["id"])


@router.post(
    "/bulk/assign-reviewer",
    response_model=MessageResponse,
    summary="Bulk assign reviewer"
)
async def bulk_assign_reviewer(
    bulk_data: RPPSubmissionBulkAssignReviewer,
    current_user: dict = Depends(admin_required),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """
    Bulk assign reviewer to multiple submissions.
    
    Requires admin role.
    """
    return await submission_service.bulk_assign_reviewer(bulk_data)


# ===== ANALYTICS AND STATISTICS =====

@router.get(
    "/analytics/overview",
    response_model=RPPSubmissionAnalytics,
    summary="Get RPP submissions analytics"
)
async def get_submissions_analytics(
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    current_user: dict = Depends(get_current_active_user),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Get comprehensive RPP submissions analytics."""
    return await submission_service.get_submissions_analytics(organization_id, current_user)


@router.get(
    "/teacher/{teacher_id}/progress",
    response_model=TeacherRPPProgress,
    summary="Get teacher RPP progress"
)
async def get_teacher_progress(
    teacher_id: int,
    current_user: dict = Depends(get_current_active_user),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """Get progress statistics for a specific teacher."""
    return await submission_service.get_teacher_progress(teacher_id, current_user)


@router.get(
    "/reviewer/{reviewer_id}/workload",
    response_model=dict,
    summary="Get reviewer workload"
)
async def get_reviewer_workload(
    reviewer_id: int,
    current_user: dict = Depends(management_roles_required),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """
    Get workload statistics for a reviewer.
    
    Requires management role (super_admin, admin, or kepala_sekolah).
    """
    return await submission_service.get_reviewer_workload(reviewer_id, current_user)


@router.get(
    "/analytics/comprehensive",
    response_model=RPPSubmissionStats,
    summary="Get comprehensive submission statistics"
)
async def get_comprehensive_stats(
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    current_user: dict = Depends(management_roles_required),
    submission_service: RPPSubmissionService = Depends(get_submission_service)
):
    """
    Get comprehensive RPP submission statistics.
    
    Requires management role (super_admin, admin, or kepala_sekolah).
    """
    return await submission_service.get_comprehensive_stats(organization_id, current_user)