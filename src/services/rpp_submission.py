"""RPPSubmission service for PKG system."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.user import UserRepository
from src.repositories.media_file import MediaFileRepository
from src.repositories.organization import OrganizationRepository
from src.schemas.rpp_submission import (
    RPPSubmissionCreate,
    RPPSubmissionUpdate,
    RPPSubmissionResponse,
    RPPSubmissionListResponse,
    RPPSubmissionSummary,
    RPPSubmissionReview,
    RPPSubmissionResubmit,
    RPPSubmissionBulkReview
)
from src.schemas.rpp_submission import RPPSubmissionFilterParams
from src.models.enums import RPPStatus


class RPPSubmissionService:
    """Service for RPP submission operations."""
    
    def __init__(
        self,
        submission_repo: RPPSubmissionRepository,
        user_repo: UserRepository,
        media_repo: MediaFileRepository,
        org_repo: OrganizationRepository
    ):
        self.submission_repo = submission_repo
        self.user_repo = user_repo
        self.media_repo = media_repo
        self.org_repo = org_repo
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create_submission(self, submission_data: RPPSubmissionCreate, created_by: Optional[int] = None) -> RPPSubmissionResponse:
        """Create new RPP submission with automatic reviewer assignment."""
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
        
        # Get teacher's organization to find the head/principal
        if not teacher.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher must be assigned to an organization"
            )
        
        organization = await self.org_repo.get_by_id(teacher.organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher's organization not found"
            )
        
        # Automatically assign organization head as reviewer
        reviewer_id = None
        if organization.head_id:
            # Validate that the head exists and is active
            head = await self.user_repo.get_by_id(organization.head_id)
            if head and not head.deleted_at:
                reviewer_id = organization.head_id
        
        if not reviewer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active head/principal found for the teacher's organization to assign as reviewer"
            )
        
        # Create submission with automatic reviewer assignment
        submission = await self.submission_repo.create(submission_data, created_by, reviewer_id)
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
        review_data: RPPSubmissionReview,
        current_user: dict = None
    ) -> RPPSubmissionResponse:
        """Review RPP submission with organization-based access control."""
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
        
        # Organization-based access control for principals
        if current_user:
            # Get the teacher who submitted the RPP
            teacher = await self.user_repo.get_by_id(submission.teacher_id)
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher who submitted RPP not found"
                )
            
            # Check if current user is a principal (kepala_sekolah) and can only review RPPs from their organization
            current_user_obj = await self.user_repo.get_by_id(current_user["id"])
            if current_user_obj and current_user_obj.organization_id:
                # Principal can only review submissions from teachers in their organization
                if teacher.organization_id != current_user_obj.organization_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only review RPP submissions from teachers in your organization"
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
        """Get all pending review submissions with organization-based filtering."""
        if reviewer_id:
            # Validate reviewer exists
            reviewer = await self.user_repo.get_by_id(reviewer_id)
            if not reviewer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reviewer not found"
                )
        
        # Get submissions assigned to the reviewer
        submissions = await self.submission_repo.get_pending_reviews(reviewer_id)
        
        # Additional organization-based filtering for security
        filtered_submissions = []
        if current_user:
            current_user_obj = await self.user_repo.get_by_id(current_user["id"])
            if current_user_obj and current_user_obj.organization_id:
                # Only include submissions from teachers in the same organization
                for submission in submissions:
                    if submission.teacher and submission.teacher.organization_id == current_user_obj.organization_id:
                        filtered_submissions.append(submission)
                submissions = filtered_submissions
        
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
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_review_submissions(self, bulk_data: RPPSubmissionBulkReview, current_user_id: int, current_user: dict = None) -> Dict[str, Any]:
        """Bulk review submissions with organization-based access control."""
        # Get current user's organization for access control
        current_user_obj = None
        if current_user:
            current_user_obj = await self.user_repo.get_by_id(current_user["id"])
        
        # Validate all submission IDs exist and are pending, and check organization access
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
            
            # Organization-based access control
            if current_user_obj and current_user_obj.organization_id:
                # Get the teacher who submitted the RPP
                teacher = await self.user_repo.get_by_id(submission.teacher_id)
                if not teacher:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Teacher who submitted RPP {submission_id} not found"
                    )
                
                # Principal can only review submissions from teachers in their organization
                if teacher.organization_id != current_user_obj.organization_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You can only review RPP submissions from teachers in your organization. Submission {submission_id} is from a different organization."
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
    
