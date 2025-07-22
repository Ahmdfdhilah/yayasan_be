"""RPP Submission endpoints for submission management."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.user import UserRepository
from src.repositories.period import PeriodRepository
from src.repositories.media_file import MediaFileRepository
from src.services.rpp_submission import RPPSubmissionService
from src.schemas.rpp_submission import (
    RPPSubmissionCreate,
    RPPSubmissionUpdate,
    RPPSubmissionResponse,
    RPPSubmissionItemResponse,
    RPPSubmissionItemUpdate,
    RPPSubmissionSubmitRequest,
    RPPSubmissionReviewRequest,
    GenerateRPPSubmissionsRequest,
    GenerateRPPSubmissionsResponse,
    RPPSubmissionListResponse,
    RPPSubmissionItemListResponse,
    RPPSubmissionFilter,
    RPPSubmissionItemFilter,
    RPPSubmissionStats,
    RPPSubmissionDashboard,
)
from src.schemas.shared import MessageResponse
from src.models.enums import RPPType, RPPSubmissionStatus
from src.auth.permissions import get_current_active_user, require_roles
from src.utils.messages import get_message

router = APIRouter()

# Permission dependencies
admin_required = require_roles(["admin"])
kepala_sekolah_required = require_roles(["kepala_sekolah"])
guru_required = require_roles(["guru"])
guru_or_kepala_sekolah = require_roles(["guru", "kepala_sekolah"])
admin_or_kepala_sekolah = require_roles(["admin", "kepala_sekolah"])
any_authorized_user = require_roles(["admin", "kepala_sekolah", "guru"])


async def get_rpp_submission_service(
    session: AsyncSession = Depends(get_db),
) -> RPPSubmissionService:
    """Get RPP submission service dependency."""
    rpp_repo = RPPSubmissionRepository(session)
    user_repo = UserRepository(session)
    period_repo = PeriodRepository(session)
    media_repo = MediaFileRepository(session)
    return RPPSubmissionService(rpp_repo, user_repo, period_repo, media_repo)


# ===== ADMIN ENDPOINTS =====


@router.post(
    "/admin/generate-for-period",
    response_model=GenerateRPPSubmissionsResponse,
    summary="Generate RPP submissions for all teachers in a period",
    dependencies=[Depends(admin_required)],
)
async def generate_submissions_for_period(
    generate_data: GenerateRPPSubmissionsRequest,
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Generate RPP submissions and items for all active teachers in the specified period.

    This endpoint creates:
    - One submission record per teacher (status: draft)
    - Three submission items per teacher (one for each RPP type, file_id: NULL)

    Skips existing submissions for teacher+period combinations.
    """
    return await rpp_service.generate_submissions_for_period(generate_data)


# ===== TEACHER ENDPOINTS =====


@router.get(
    "/my-submissions",
    response_model=RPPSubmissionListResponse,
    summary="Get current user's submissions",
    dependencies=[Depends(guru_or_kepala_sekolah)],
)
async def get_my_submissions(
    period_id: Optional[int] = Query(None, description="Filter by period ID"),
    status: Optional[RPPSubmissionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Get submissions for the current user.

    Teachers and kepala sekolah can only see their own submissions.
    """
    filters = RPPSubmissionFilter(
        teacher_id=current_user["id"], period_id=period_id, status=status
    )

    return await rpp_service.get_submissions(filters, limit, offset)


@router.get(
    "/my-submission/{period_id}",
    response_model=RPPSubmissionResponse,
    summary="Get my submission for specific period",
    dependencies=[Depends(guru_or_kepala_sekolah)],
)
async def get_my_submission_for_period(
    period_id: int = Path(..., description="Period ID"),
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Get submission for current teacher and specific period.

    Returns detailed submission with all items and upload status.
    """
    return await rpp_service.get_submission_by_teacher_period(
        current_user["id"], period_id
    )


@router.put(
    "/my-submission/{period_id}/upload/{rpp_type}",
    response_model=RPPSubmissionItemResponse,
    summary="Upload RPP file for specific type",
    dependencies=[Depends(guru_or_kepala_sekolah)],
)
async def upload_rpp_file(
    period_id: int = Path(..., description="Period ID"),
    rpp_type: RPPType = Path(..., description="RPP type to upload"),
    file_data: RPPSubmissionItemUpdate = ...,
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Upload file for specific RPP type.

    Teachers can upload files for their submission items.
    The file must be already uploaded to media_files table.
    """
    return await rpp_service.upload_rpp_file(
        teacher_id=current_user["id"],
        period_id=period_id,
        rpp_type=rpp_type,
        file_id=file_data.file_id,
    )


@router.post(
    "/my-submission/{submission_id}/submit",
    response_model=MessageResponse,
    summary="Submit RPP for approval",
    dependencies=[Depends(guru_or_kepala_sekolah)],
)
async def submit_for_approval(
    submission_id: int = Path(..., description="Submission ID"),
    submit_data: RPPSubmissionSubmitRequest = ...,
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Submit RPP for approval.

    Requires all 3 RPP types to be uploaded.
    Changes status from 'draft' to 'pending'.
    """
    return await rpp_service.submit_for_review(
        submission_id, current_user["id"], submit_data
    )


# ===== REVIEWER ENDPOINTS =====


@router.get(
    "/pending-reviews",
    response_model=RPPSubmissionListResponse,
    summary="Get submissions pending review",
    dependencies=[Depends(admin_or_kepala_sekolah)],
)
async def get_pending_reviews(
    period_id: Optional[int] = Query(None, description="Filter by period ID"),
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    limit: int = Query(100, ge=1, le=500, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Get submissions pending review.

    - Admin can review kepala sekolah submissions
    - Kepala sekolah can review guru submissions from their organization
    """
    user_roles = current_user.get("roles", [])
    
    filters = RPPSubmissionFilter(
        status=RPPSubmissionStatus.PENDING,
        period_id=period_id,
        teacher_id=teacher_id,
    )
    
    # Role-based filtering
    if "admin" in user_roles:
        # Admin can see all pending submissions (especially from kepala sekolah)
        pass
    elif "kepala_sekolah" in user_roles:
        # Kepala sekolah can only see guru submissions from their organization
        filters.organization_id = current_user.get("organization_id")
        filters.submitter_role = "guru"  # Only show guru submissions for kepala sekolah to review

    return await rpp_service.get_submissions(filters, limit, offset)


@router.post(
    "/review/{submission_id}",
    response_model=MessageResponse,
    summary="Review RPP submission",
    dependencies=[Depends(admin_or_kepala_sekolah)],
)
async def review_submission(
    submission_id: int = Path(..., description="Submission ID"),
    review_data: RPPSubmissionReviewRequest = ...,
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Review RPP submission.

    - Admin can approve/reject kepala sekolah submissions
    - Kepala sekolah can approve/reject guru submissions from their organization
    """
    return await rpp_service.review_submission(
        submission_id, current_user["id"], review_data
    )


# ===== GENERAL QUERY ENDPOINTS =====


@router.get(
    "/",
    response_model=RPPSubmissionListResponse,
    summary="Get RPP submissions with filtering",
    dependencies=[Depends(any_authorized_user)],
)
async def get_submissions(
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    period_id: Optional[int] = Query(None, description="Filter by period ID"),
    status: Optional[RPPSubmissionStatus] = Query(None, description="Filter by status"),
    reviewer_id: Optional[int] = Query(None, description="Filter by reviewer ID"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search by teacher name"),
    limit: int = Query(100, ge=1, le=500, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Get submissions with filtering.

    Access control:
    - Admin: Can see all submissions
    - Kepala Sekolah: Can see submissions in their organization
    - Guru: Can only see their own submissions
    """
    # Apply role-based filters
    filters = RPPSubmissionFilter(
        teacher_id=teacher_id,
        period_id=period_id,
        status=status,
        reviewer_id=reviewer_id,
        search=search,
    )

    # Role-based access control
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles:
        if "kepala_sekolah" in user_roles:
            # Kepala sekolah can see submissions in their organization
            filters.organization_id = current_user.get("organization_id")
        elif "guru" in user_roles:
            # Teachers can only see their own submissions
            filters.teacher_id = current_user["id"]

    return await rpp_service.get_submissions(filters, limit, offset)


@router.get(
    "/{submission_id}",
    response_model=RPPSubmissionResponse,
    summary="Get submission details",
    dependencies=[Depends(any_authorized_user)],
)
async def get_submission(
    submission_id: int = Path(..., description="Submission ID"),
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Get detailed submission information.

    Access control applies based on user role.
    """
    submission = await rpp_service.get_submission(submission_id)

    # Role-based access control
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles:
        if "guru" in user_roles:
            # Teachers can only see their own submissions
            if submission.teacher_id != current_user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=get_message("submission", "own_submissions_only"),
                )
        elif "kepala_sekolah" in user_roles:
            # Kepala sekolah can see submissions in their organization
            # This would require checking teacher's organization, implement if needed
            pass

    return submission


# ===== STATISTICS ENDPOINTS =====


@router.get(
    "/statistics/overview",
    response_model=RPPSubmissionStats,
    summary="Get submission statistics",
    dependencies=[Depends(admin_or_kepala_sekolah)],
)
async def get_submission_statistics(
    period_id: Optional[int] = Query(None, description="Filter by period ID"),
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Get submission statistics.

    - Admin: Can see all statistics
    - Kepala Sekolah: Can see statistics for their organization
    """
    organization_id = None
    if "admin" not in current_user.get("roles", []):
        organization_id = current_user.get("organization_id")

    return await rpp_service.get_submission_statistics(period_id, organization_id)


@router.get(
    "/dashboard/overview",
    response_model=RPPSubmissionDashboard,
    summary="Get dashboard data",
    dependencies=[Depends(any_authorized_user)],
)
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Get dashboard overview data.

    Returns different data based on user role:
    - Admin: System-wide data + pending reviews (kepala sekolah submissions)
    - Kepala Sekolah: Personal submissions + pending reviews (guru submissions) + organization data
    - Guru: Personal submissions + organization overview
    """
    organization_id = None
    if "admin" not in current_user.get("roles", []):
        organization_id = current_user.get("organization_id")

    return await rpp_service.get_dashboard_data(current_user["id"], organization_id)


# ===== SUBMISSION ITEMS ENDPOINTS =====


@router.get(
    "/items/",
    response_model=RPPSubmissionItemListResponse,
    summary="Get submission items with filtering",
    dependencies=[Depends(any_authorized_user)],
)
async def get_submission_items(
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    period_id: Optional[int] = Query(None, description="Filter by period ID"),
    rpp_type: Optional[RPPType] = Query(None, description="Filter by RPP type"),
    is_uploaded: Optional[bool] = Query(None, description="Filter by upload status"),
    limit: int = Query(100, ge=1, le=500, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_active_user),
    rpp_service: RPPSubmissionService = Depends(get_rpp_submission_service),
):
    """
    Get submission items with filtering.

    Useful for detailed tracking of individual RPP type uploads.
    """
    filters = RPPSubmissionItemFilter(
        teacher_id=teacher_id,
        period_id=period_id,
        rpp_type=rpp_type,
        is_uploaded=is_uploaded,
    )

    # Role-based access control
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles:
        if "kepala_sekolah" in user_roles:
            filters.organization_id = current_user.get("organization_id")
        elif "guru" in user_roles:
            filters.teacher_id = current_user["id"]

    return await rpp_service.get_submission_items(filters, limit, offset)
