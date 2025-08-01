"""RPP Submission service for business logic handling."""

from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status

from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.user import UserRepository
from src.repositories.period import PeriodRepository
from src.repositories.media_file import MediaFileRepository
from src.schemas.rpp_submission import (
    RPPSubmissionCreate, RPPSubmissionUpdate, RPPSubmissionResponse,
    RPPSubmissionItemCreate, RPPSubmissionItemUpdate, RPPSubmissionItemResponse,
    RPPSubmissionFilter, RPPSubmissionItemFilter,
    RPPSubmissionSubmitRequest, RPPSubmissionReviewRequest,
    GenerateRPPSubmissionsRequest, GenerateRPPSubmissionsResponse,
    RPPSubmissionListResponse, RPPSubmissionItemListResponse,
    RPPSubmissionStats, RPPSubmissionDashboard
)
from src.schemas.shared import MessageResponse
from src.models.enums import RPPType, RPPSubmissionStatus
from src.models.rpp_submission import RPPSubmission
from src.models.rpp_submission_item import RPPSubmissionItem
from src.utils.messages import get_message


class RPPSubmissionService:
    """Service for RPP Submission business logic."""
    
    def __init__(
        self, 
        rpp_repo: RPPSubmissionRepository,
        user_repo: UserRepository,
        period_repo: PeriodRepository,
        media_repo: MediaFileRepository
    ):
        self.rpp_repo = rpp_repo
        self.user_repo = user_repo
        self.period_repo = period_repo
        self.media_repo = media_repo
    
    # ===== HELPER METHODS =====
    
    def _convert_submission_to_response(self, submission: RPPSubmission) -> RPPSubmissionResponse:
        """Convert submission model to response schema."""
        return RPPSubmissionResponse(
            id=submission.id,
            teacher_id=submission.teacher_id,
            period_id=submission.period_id,
            status=submission.status,
            reviewer_id=submission.reviewer_id,
            review_notes=submission.review_notes,
            submitted_at=submission.submitted_at,
            reviewed_at=submission.reviewed_at,
            completion_percentage=submission.completion_percentage,
            can_be_submitted=submission.can_be_submitted,
            teacher_name=submission.teacher.display_name if submission.teacher else None,
            teacher_position=submission.teacher.profile.get('position') if submission.teacher and submission.teacher.profile else None,
            organization_name=submission.teacher.organization.name if submission.teacher and submission.teacher.organization else None,
            reviewer_name=submission.reviewer.display_name if submission.reviewer else None,
            period_name=submission.period.period_name if submission.period else None,
            items=[self._convert_item_to_response(item) for item in submission.items],
            created_at=submission.created_at,
            updated_at=submission.updated_at
        )
    
    def _convert_item_to_response(self, item: RPPSubmissionItem) -> RPPSubmissionItemResponse:
        """Convert submission item model to response schema."""
        return RPPSubmissionItemResponse(
            id=item.id,
            teacher_id=item.teacher_id,
            period_id=item.period_id,
            rpp_type=item.rpp_type,
            file_id=item.file_id,
            uploaded_at=item.uploaded_at,
            is_uploaded=item.is_uploaded,
            rpp_type_display_name=item.rpp_type_display_name,
            teacher_name=item.teacher.display_name if item.teacher else None,
            period_name=item.period.period_name if item.period else None,
            file_name=item.file.file_name if item.file else None,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
    
    async def _validate_teacher_exists(self, teacher_id: int) -> None:
        """Validate that teacher exists and has guru or kepala_sekolah role, excluding admin users."""
        user = await self.user_repo.get_by_id(teacher_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("user", "not_found")
            )
        
        # Check if user has admin role - reject if they do
        if user.has_role("admin"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak dapat membuat submission RPP untuk pengguna admin"
            )
        
        # Check if user has guru or kepala_sekolah role
        if not (user.has_role("guru") or user.has_role("kepala_sekolah")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pengguna bukan seorang guru atau kepala sekolah"
            )
    
    async def _validate_period_exists(self, period_id: int):
        """Validate that period exists and return period object."""
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("period", "not_found")
            )
        return period
    
    async def _validate_file_exists(self, file_id: int) -> None:
        """Validate that file exists."""
        file = await self.media_repo.get_by_id(file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("file", "file_not_found")
            )
    
    async def _validate_reviewer_exists(self, reviewer_id: int, submitter_role: str = None) -> None:
        """Validate that reviewer exists and has appropriate role based on submitter."""
        user = await self.user_repo.get_by_id(reviewer_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("user", "not_found")
            )
        
        # Check reviewer role based on submitter role
        if submitter_role == "guru":
            # Guru's RPP should be reviewed by kepala sekolah
            if not user.has_role("kepala_sekolah"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RPP guru harus ditinjau oleh kepala sekolah"
                )
        elif submitter_role == "kepala_sekolah":
            # Kepala sekolah's RPP should be reviewed by admin
            if not user.has_role("admin"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RPP kepala sekolah harus ditinjau oleh admin"
                )
        else:
            # Default: require admin or kepala sekolah
            if not (user.has_role("admin") or user.has_role("kepala_sekolah")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reviewer harus admin atau kepala sekolah"
                )
    
    # ===== SUBMISSION OPERATIONS =====
    
    async def create_submission(self, submission_data: RPPSubmissionCreate) -> RPPSubmissionResponse:
        """Create new RPP submission."""
        # Validate inputs
        await self._validate_teacher_exists(submission_data.teacher_id)
        await self._validate_period_exists(submission_data.period_id)
        
        # Check if submission already exists
        existing = await self.rpp_repo.get_submission_by_teacher_period(
            submission_data.teacher_id, submission_data.period_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_message("submission", "submission_exists")
            )
        
        # Create submission
        submission = await self.rpp_repo.create_submission(submission_data)
        
        # Create items for all 3 RPP types
        for rpp_type in RPPType.get_all_values():
            item_data = RPPSubmissionItemCreate(
                teacher_id=submission_data.teacher_id,
                period_id=submission_data.period_id,
                rpp_type=RPPType(rpp_type),
                file_id=None
            )
            await self.rpp_repo.create_submission_item(item_data)
        
        # Refresh to get items
        submission = await self.rpp_repo.get_submission_by_id(submission.id)
        return self._convert_submission_to_response(submission)
    
    async def get_submission(self, submission_id: int) -> RPPSubmissionResponse:
        """Get submission by ID."""
        submission = await self.rpp_repo.get_submission_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("submission", "submission_not_found")
            )
        
        return self._convert_submission_to_response(submission)
    
    async def get_submission_by_teacher_period(
        self, teacher_id: int, period_id: int
    ) -> RPPSubmissionResponse:
        """Get submission by teacher and period."""
        submission = await self.rpp_repo.get_submission_by_teacher_period(teacher_id, period_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pengajuan tidak ditemukan untuk guru dan periode ini"
            )
        
        return self._convert_submission_to_response(submission)
    
    async def submit_for_review(
        self, submission_id: int, teacher_id: int, submit_data: RPPSubmissionSubmitRequest
    ) -> MessageResponse:
        """Submit RPP for review."""
        # Get submission
        submission = await self.rpp_repo.get_submission_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("submission", "submission_not_found")
            )
        
        # Validate ownership
        if submission.teacher_id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_message("submission", "own_submissions_only")
            )
        
        # Check if can be submitted
        can_submit = await self.rpp_repo.can_submission_be_submitted(submission_id)
        if not can_submit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak dapat mengajukan: pastikan semua 3 jenis RPP telah diunggah dan pengajuan dalam status draft"
            )
        
        # Submit for review
        success = await self.rpp_repo.submit_for_review(submission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gagal mengajukan untuk ditinjau"
            )
        
        return MessageResponse(message="Submission successfully submitted for review")
    
    async def review_submission(
        self, submission_id: int, reviewer_id: int, review_data: RPPSubmissionReviewRequest
    ) -> MessageResponse:
        """Review RPP submission."""
        # Get submission first to determine submitter role
        submission = await self.rpp_repo.get_submission_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("submission", "submission_not_found")
            )
        
        # Get submitter's role
        submitter = await self.user_repo.get_by_id(submission.teacher_id)
        if not submitter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submitter tidak ditemukan"
            )
        
        submitter_roles = submitter.get_roles()
        submitter_role = None
        if "guru" in submitter_roles:
            submitter_role = "guru"
        elif "kepala_sekolah" in submitter_roles:
            submitter_role = "kepala_sekolah"
        
        # Validate reviewer based on submitter role
        await self._validate_reviewer_exists(reviewer_id, submitter_role)
        
        # Validate submission is pending
        if submission.status != RPPSubmissionStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pengajuan tidak dalam status menunggu tinjauan"
            )
        
        # Review submission
        success = await self.rpp_repo.review_submission(
            submission_id, reviewer_id, review_data.status, review_data.review_notes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to review submission"
            )
        
        action_map = {
            RPPSubmissionStatus.APPROVED: "approved",
            RPPSubmissionStatus.REJECTED: "rejected"
        }
        action = action_map.get(review_data.status, "reviewed")
        
        return MessageResponse(message=f"Submission successfully {action}")
    
    # ===== SUBMISSION ITEM OPERATIONS =====
    
    async def upload_rpp_file(
        self, teacher_id: int, period_id: int, rpp_type: RPPType, file_id: int
    ) -> RPPSubmissionItemResponse:
        """Upload file for specific RPP type."""
        # Validate inputs
        await self._validate_teacher_exists(teacher_id)
        await self._validate_period_exists(period_id)
        await self._validate_file_exists(file_id)
        
        # Get submission item
        item = await self.rpp_repo.get_submission_item_by_teacher_period_type(
            teacher_id, period_id, rpp_type
        )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission item not found. Please ensure submission exists for this period."
            )
        
        # Update file
        updated_item = await self.rpp_repo.update_submission_item_file(item.id, file_id)
        if not updated_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to upload file"
            )
        
        # Get full item with relationships
        item = await self.rpp_repo.get_submission_item_by_id(updated_item.id)
        return self._convert_item_to_response(item)
    
    # ===== QUERY OPERATIONS =====
    
    async def get_submissions(
        self, filters: RPPSubmissionFilter, limit: int = 100, offset: int = 0
    ) -> RPPSubmissionListResponse:
        """Get submissions with filtering and pagination."""
        submissions, total = await self.rpp_repo.get_submissions_by_filter(filters, limit, offset)
        
        pages = (total + limit - 1) // limit if limit > 0 else 1
        page = (offset // limit) + 1 if limit > 0 else 1
        
        return RPPSubmissionListResponse(
            items=[self._convert_submission_to_response(sub) for sub in submissions],
            total=total,
            page=page,
            size=limit,
            pages=pages
        )
    
    async def get_submission_items(
        self, filters: RPPSubmissionItemFilter, limit: int = 100, offset: int = 0
    ) -> RPPSubmissionItemListResponse:
        """Get submission items with filtering and pagination."""
        items, total = await self.rpp_repo.get_submission_items_by_filter(filters, limit, offset)
        
        pages = (total + limit - 1) // limit if limit > 0 else 1
        page = (offset // limit) + 1 if limit > 0 else 1
        
        return RPPSubmissionItemListResponse(
            items=[self._convert_item_to_response(item) for item in items],
            total=total,
            page=page,
            size=limit,
            pages=pages
        )
    
    # ===== ADMIN OPERATIONS =====
    
    async def generate_submissions_for_period(
        self, generate_data: GenerateRPPSubmissionsRequest
    ) -> GenerateRPPSubmissionsResponse:
        """Generate submissions for all teachers in a period."""
        # Validate period and get period info
        period = await self._validate_period_exists(generate_data.period_id)
        
        # Generate submissions
        generated, skipped, total = await self.rpp_repo.generate_submissions_for_period(
            generate_data.period_id
        )
        
        # Calculate total items created (3 items per submission)
        items_per_submission = 3
        total_items_created = generated * items_per_submission
        
        success = True
        if generated == 0 and skipped == 0:
            message = f"No teachers found for period '{period.period_name}'"
            success = False
        elif generated == 0:
            message = f"All {skipped} teachers already have submissions for period '{period.period_name}'"
        else:
            message = f"Successfully generated {generated} submissions for {generated} teachers"
            if skipped > 0:
                message += f", skipped {skipped} existing submissions"
        
        return GenerateRPPSubmissionsResponse(
            success=success,
            message=message,
            period_id=generate_data.period_id,
            period_name=period.period_name,
            generated_count=generated,
            skipped_count=skipped,
            total_teachers=total,
            items_per_submission=items_per_submission,
            total_items_created=total_items_created
        )
    
    # ===== STATISTICS OPERATIONS =====
    
    async def get_submission_statistics(
        self, period_id: Optional[int] = None, organization_id: Optional[int] = None
    ) -> RPPSubmissionStats:
        """Get submission statistics."""
        stats_data = await self.rpp_repo.get_submission_stats(period_id, organization_id)
        
        return RPPSubmissionStats(
            total_submissions=stats_data['total_submissions'],
            draft_count=stats_data['draft_count'],
            pending_count=stats_data['pending_count'],
            approved_count=stats_data['approved_count'],
            rejected_count=stats_data['rejected_count'],
            completion_rate=stats_data['completion_rate']
        )
    
    async def get_dashboard_data(
        self, user_id: int, organization_id: Optional[int] = None
    ) -> RPPSubmissionDashboard:
        """Get dashboard data for user."""
        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get overall stats
        overall_stats = await self.get_submission_statistics(organization_id=organization_id)
        
        # Get current period
        current_period = await self.period_repo.get_active_period()
        current_period_stats = None
        if current_period:
            current_period_stats = await self.get_submission_statistics(
                period_id=current_period.id, organization_id=organization_id
            )
        
        # Get recent submissions
        recent_filter = RPPSubmissionFilter(organization_id=organization_id)
        recent_submissions_response = await self.get_submissions(recent_filter, limit=10)
        recent_submissions = recent_submissions_response.data
        
        # Get pending reviews (for admin and kepala sekolah)
        pending_reviews = []
        if user.has_role("admin"):
            # Admin can see all pending submissions (especially kepala sekolah submissions)
            pending_filter = RPPSubmissionFilter(
                status=RPPSubmissionStatus.PENDING
            )
            pending_response = await self.get_submissions(pending_filter, limit=20)
            pending_reviews = pending_response.data
        elif user.has_role("kepala_sekolah"):
            # Kepala sekolah can see guru submissions from their organization  
            pending_filter = RPPSubmissionFilter(
                status=RPPSubmissionStatus.PENDING,
                organization_id=organization_id,
                submitter_role="guru"  # Only show guru submissions for kepala sekolah to review
            )
            pending_response = await self.get_submissions(pending_filter, limit=20)
            pending_reviews = pending_response.data
        
        # Get my submissions (for teachers and kepala sekolah)
        my_submissions = []
        if user.has_role("guru") or user.has_role("kepala_sekolah"):
            my_filter = RPPSubmissionFilter(teacher_id=user_id)
            my_response = await self.get_submissions(my_filter, limit=10)
            my_submissions = my_response.data
        
        return RPPSubmissionDashboard(
            current_period_stats=current_period_stats,
            recent_submissions=recent_submissions,
            pending_reviews=pending_reviews,
            my_submissions=my_submissions,
            overall_stats=overall_stats
        )