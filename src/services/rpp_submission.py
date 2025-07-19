"""RPPSubmission service for PKG system."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.user import UserRepository
from src.repositories.media_file import MediaFileRepository
from src.schemas.rpp_submission import (
    RPPSubmissionCreate,
    RPPSubmissionUpdate,
    RPPSubmissionResponse,
    RPPSubmissionListResponse,
    RPPSubmissionSummary,
    RPPSubmissionReview,
    RPPSubmissionResubmit,
    RPPSubmissionBulkReview,
    RPPSubmissionBulkAssignReviewer,
    RPPSubmissionAnalytics,
    TeacherRPPProgress,
    RPPSubmissionStats
)
from src.schemas.rpp_submission import RPPSubmissionFilterParams
from src.models.enums import RPPStatus


class RPPSubmissionService:
    """Service for RPP submission operations."""
    
    def __init__(
        self,
        submission_repo: RPPSubmissionRepository,
        user_repo: UserRepository,
        media_repo: MediaFileRepository
    ):
        self.submission_repo = submission_repo
        self.user_repo = user_repo
        self.media_repo = media_repo
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create_submission(self, submission_data: RPPSubmissionCreate, created_by: Optional[int] = None) -> RPPSubmissionResponse:
        """Create new RPP submission."""
        # Validate teacher exists
        teacher = await self.user_repo.get_by_id(submission_data.teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Validate file exists
        file = await self.media_repo.get_by_id(submission_data.file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Create submission (period-based, no need to check academic_year/semester)
        submission = await self.submission_repo.create(submission_data, created_by)
        return RPPSubmissionResponse.from_rpp_submission_model(
            submission, include_relations=True
        )
    
    async def get_submission_by_id(self, submission_id: int, current_user: dict = None) -> RPPSubmissionResponse:
        """Get RPP submission by ID."""
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RPP submission not found"
            )
        
        return RPPSubmissionResponse.from_rpp_submission_model(
            submission, include_relations=True
        )
    
    async def update_submission(
        self, 
        submission_id: int, 
        submission_data: RPPSubmissionUpdate
    ) -> RPPSubmissionResponse:
        """Update RPP submission."""
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RPP submission not found"
            )
        
        # Check if submission can be updated (only pending submissions)
        if submission.status != RPPStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending submissions can be updated"
            )
        
        # Validate new file if provided
        if submission_data.file_id:
            file = await self.media_repo.get_by_id(submission_data.file_id)
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
        
        updated_submission = await self.submission_repo.update(submission_id, submission_data)
        return RPPSubmissionResponse.from_rpp_submission_model(
            updated_submission, include_relations=True
        )
    
    async def delete_submission(self, submission_id: int) -> Dict[str, str]:
        """Delete RPP submission."""
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RPP submission not found"
            )
        
        # Check if submission can be deleted (only pending or rejected)
        if submission.status not in [RPPStatus.PENDING, RPPStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending or rejected submissions can be deleted"
            )
        
        success = await self.submission_repo.soft_delete(submission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete RPP submission"
            )
        
        return {"message": "RPP submission deleted successfully"}
    
    # ===== REVIEW OPERATIONS =====
    
    async def review_submission(
        self, 
        submission_id: int, 
        reviewer_id: int, 
        review_data: RPPSubmissionReview
    ) -> RPPSubmissionResponse:
        """Review RPP submission."""
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RPP submission not found"
            )
        
        # Check if submission is pending
        if submission.status != RPPStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending submissions can be reviewed"
            )
        
        # Validate reviewer exists
        reviewer = await self.user_repo.get_by_id(reviewer_id)
        if not reviewer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reviewer not found"
            )
        
        # Perform review action
        if review_data.action == "approve":
            updated_submission = await self.submission_repo.approve_submission(
                submission_id, reviewer_id, review_data.review_notes
            )
        elif review_data.action == "reject":
            if not review_data.review_notes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Review notes are required for rejection"
                )
            updated_submission = await self.submission_repo.reject_submission(
                submission_id, reviewer_id, review_data.review_notes
            )
        elif review_data.action == "revision":
            if not review_data.review_notes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Review notes are required for revision request"
                )
            updated_submission = await self.submission_repo.request_revision(
                submission_id, reviewer_id, review_data.review_notes
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid review action"
            )
        
        return RPPSubmissionResponse.from_rpp_submission_model(
            updated_submission, include_relations=True
        )
    
    async def resubmit_submission(
        self, 
        submission_id: int, 
        resubmit_data: RPPSubmissionResubmit
    ) -> RPPSubmissionResponse:
        """Resubmit RPP submission with new file."""
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RPP submission not found"
            )
        
        # Check if submission can be resubmitted
        if submission.status not in [RPPStatus.REJECTED, RPPStatus.REVISION_NEEDED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only rejected or revision-needed submissions can be resubmitted"
            )
        
        # Validate new file
        file = await self.media_repo.get_by_id(resubmit_data.file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        updated_submission = await self.submission_repo.resubmit(
            submission_id, resubmit_data.file_id
        )
        
        return RPPSubmissionResponse.from_rpp_submission_model(
            updated_submission, include_relations=True
        )
    
    async def assign_reviewer(
        self, 
        submission_id: int, 
        reviewer_id: int
    ) -> RPPSubmissionResponse:
        """Assign reviewer to submission."""
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RPP submission not found"
            )
        
        # Validate reviewer exists
        reviewer = await self.user_repo.get_by_id(reviewer_id)
        if not reviewer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reviewer not found"
            )
        
        updated_submission = await self.submission_repo.assign_reviewer(
            submission_id, reviewer_id
        )
        
        return RPPSubmissionResponse.from_rpp_submission_model(
            updated_submission, include_relations=True
        )
    
    # ===== LISTING AND FILTERING =====
    
    async def get_submissions(self, filters: RPPSubmissionFilterParams, current_user: dict = None) -> RPPSubmissionListResponse:
        """Get RPP submissions with filters and pagination."""
        submissions, total = await self.submission_repo.get_all_submissions_filtered(filters)
        
        submission_responses = [
            RPPSubmissionResponse.from_rpp_submission_model(
                submission, include_relations=True
            )
            for submission in submissions
        ]
        
        return RPPSubmissionListResponse(
            items=submission_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size
        )
    
    async def get_teacher_submissions(
        self, 
        teacher_id: int, 
        academic_year: Optional[str] = None,
        current_user: dict = None
    ) -> List[RPPSubmissionResponse]:
        """Get all submissions for a specific teacher."""
        # Validate teacher exists
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        submissions = await self.submission_repo.get_teacher_submissions(teacher_id, academic_year)
        
        return [
            RPPSubmissionResponse.from_rpp_submission_model(
                submission, include_relations=True
            )
            for submission in submissions
        ]
    
    async def get_pending_reviews(self, reviewer_id: Optional[int] = None, current_user: dict = None) -> List[RPPSubmissionResponse]:
        """Get all pending review submissions."""
        if reviewer_id:
            # Validate reviewer exists
            reviewer = await self.user_repo.get_by_id(reviewer_id)
            if not reviewer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reviewer not found"
                )
        
        submissions = await self.submission_repo.get_pending_reviews(reviewer_id)
        
        return [
            RPPSubmissionResponse.from_rpp_submission_model(
                submission, include_relations=True
            )
            for submission in submissions
        ]
    
    async def get_submissions_by_period(self, period_id: int, current_user: dict = None) -> List[RPPSubmissionResponse]:
        """Get all submissions for a specific period."""
        submissions = await self.submission_repo.get_submissions_by_period(period_id)
        
        return [
            RPPSubmissionResponse.from_rpp_submission_model(
                submission, include_relations=True
            )
            for submission in submissions
        ]
    
    async def get_overdue_reviews(self, days_threshold: int = 7, current_user: dict = None) -> List[RPPSubmissionResponse]:
        """Get submissions that are overdue for review."""
        submissions = await self.submission_repo.get_overdue_reviews(days_threshold)
        
        return [
            RPPSubmissionResponse.from_rpp_submission_model(
                submission, include_relations=True
            )
            for submission in submissions
        ]
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_review_submissions(self, bulk_data: RPPSubmissionBulkReview, current_user_id: int) -> Dict[str, Any]:
        """Bulk review submissions."""
        # Validate all submission IDs exist and are pending
        for submission_id in bulk_data.submission_ids:
            submission = await self.submission_repo.get_by_id(submission_id)
            if not submission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"RPP submission with ID {submission_id} not found"
                )
            
            if submission.status != RPPStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Submission {submission_id} is not pending review"
                )
        
        reviewed_count = 0
        
        if bulk_data.action == "approve":
            reviewed_count = await self.submission_repo.bulk_approve(
                bulk_data.submission_ids,
                current_user_id,
                bulk_data.review_notes
            )
        elif bulk_data.action == "reject":
            if not bulk_data.review_notes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Review notes are required for bulk rejection"
                )
            reviewed_count = await self.submission_repo.bulk_reject(
                bulk_data.submission_ids,
                current_user_id,
                bulk_data.review_notes
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bulk review action"
            )
        
        return {
            "message": f"Successfully {bulk_data.action}d {reviewed_count} submissions",
            "reviewed_count": reviewed_count
        }
    
    async def bulk_assign_reviewer(self, bulk_data: RPPSubmissionBulkAssignReviewer) -> Dict[str, Any]:
        """Bulk assign reviewer to submissions."""
        # Validate reviewer exists
        reviewer = await self.user_repo.get_by_id(bulk_data.reviewer_id)
        if not reviewer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reviewer not found"
            )
        
        # Validate submission IDs exist
        for submission_id in bulk_data.submission_ids:
            submission = await self.submission_repo.get_by_id(submission_id)
            if not submission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"RPP submission with ID {submission_id} not found"
                )
        
        assigned_count = await self.submission_repo.bulk_assign_reviewer(
            bulk_data.submission_ids,
            bulk_data.reviewer_id
        )
        
        return {
            "message": f"Successfully assigned reviewer to {assigned_count} submissions",
            "assigned_count": assigned_count
        }
    
    # ===== ANALYTICS AND STATISTICS =====
    
    async def get_submissions_analytics(self, organization_id: Optional[int] = None, current_user: dict = None) -> RPPSubmissionAnalytics:
        """Get comprehensive submissions analytics."""
        analytics_data = await self.submission_repo.get_submissions_analytics(organization_id)
        
        return RPPSubmissionAnalytics(
            total_submissions=analytics_data["total_submissions"],
            by_status=analytics_data["by_status"],
            by_academic_year=analytics_data["by_academic_year"],
            by_semester=analytics_data["by_semester"],
            by_rpp_type=analytics_data["by_rpp_type"],
            avg_review_time_hours=analytics_data["avg_review_time_hours"],
            avg_revision_count=analytics_data["avg_revision_count"],
            pending_reviews=analytics_data["pending_reviews"],
            overdue_reviews=analytics_data["overdue_reviews"]
        )
    
    async def get_teacher_progress(self, teacher_id: int, current_user: dict = None) -> TeacherRPPProgress:
        """Get progress statistics for a specific teacher."""
        # Validate teacher exists
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        progress_data = await self.submission_repo.get_teacher_progress(teacher_id)
        
        return TeacherRPPProgress(
            teacher_id=teacher_id,
            teacher_name=teacher.display_name,
            teacher_email=teacher.email,
            total_submitted=progress_data["total_submitted"],
            approved=progress_data["approved"],
            rejected=progress_data["rejected"],
            pending=progress_data["pending"],
            revision_needed=progress_data["revision_needed"],
            completion_rate=progress_data["completion_rate"],
            avg_revision_count=progress_data["avg_revision_count"],
            last_submission=progress_data["last_submission"]
        )
    
    async def get_reviewer_workload(self, reviewer_id: int, current_user: dict = None) -> Dict[str, Any]:
        """Get workload statistics for a reviewer."""
        # Validate reviewer exists
        reviewer = await self.user_repo.get_by_id(reviewer_id)
        if not reviewer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reviewer not found"
            )
        
        workload_data = await self.submission_repo.get_reviewer_workload(reviewer_id)
        
        return {
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer.display_name,
            "total_assigned": workload_data["total_assigned"],
            "pending_reviews": workload_data["pending_reviews"],
            "completed_reviews": workload_data["completed_reviews"],
            "avg_review_time_hours": workload_data["avg_review_time_hours"]
        }
    
    async def get_comprehensive_stats(self, organization_id: Optional[int] = None, current_user: dict = None) -> RPPSubmissionStats:
        """Get comprehensive RPP submission statistics."""
        # Get main analytics
        analytics = await self.get_submissions_analytics(organization_id)
        
        # Get teacher progress for all teachers with submissions
        # This is a simplified version - in production, you'd want pagination
        teacher_progress = []
        
        # Get recent activity (submissions in last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # This would need additional repository methods for time-based queries
        recent_activity = {
            "submissions_last_30_days": 0,
            "reviews_last_30_days": 0,
            "new_teachers": 0
        }
        
        # Submission trends would need historical data
        submission_trends = {
            "monthly_submissions": [],
            "monthly_approvals": [],
            "monthly_rejections": []
        }
        
        return RPPSubmissionStats(
            summary=analytics,
            teacher_progress=teacher_progress,
            recent_activity=recent_activity,
            submission_trends=submission_trends
        )