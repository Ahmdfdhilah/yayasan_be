"""RPPSubmission repository for PKG system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.rpp_submission import RPPSubmission
from src.models.user import User
from src.models.media_file import MediaFile
from src.models.period import Period
from src.models.enums import RPPStatus
from src.schemas.rpp_submission import RPPSubmissionCreate, RPPSubmissionUpdate
from src.schemas.rpp_submission import RPPSubmissionFilterParams


class RPPSubmissionRepository:
    """Repository for RPP submission operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, submission_data: RPPSubmissionCreate, created_by: Optional[int] = None, reviewer_id: Optional[int] = None) -> RPPSubmission:
        """Create new RPP submission - updated for periods with automatic reviewer assignment."""
        submission = RPPSubmission(
            teacher_id=submission_data.teacher_id,
            period_id=submission_data.period_id,
            rpp_type=submission_data.rpp_type,
            file_id=submission_data.file_id,
            reviewer_id=reviewer_id,
            status=RPPStatus.PENDING,
            revision_count=0,
            created_by=created_by
        )
        
        self.session.add(submission)
        await self.session.commit()
        
        # Refresh with relationships loaded
        await self.session.refresh(
            submission,
            ["teacher", "reviewer", "file", "period"]
        )
        return submission
    
    async def get_by_id(self, submission_id: int) -> Optional[RPPSubmission]:
        """Get RPP submission by ID with relationships - updated for periods."""
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.teacher),
            selectinload(RPPSubmission.reviewer),
            selectinload(RPPSubmission.file),
            selectinload(RPPSubmission.period)
        ).where(RPPSubmission.id == submission_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, submission_id: int, submission_data: RPPSubmissionUpdate) -> Optional[RPPSubmission]:
        """Update RPP submission."""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        # Update fields
        update_data = submission_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(submission, key, value)
        
        submission.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def soft_delete(self, submission_id: int) -> bool:
        """Soft delete RPP submission."""
        query = (
            update(RPPSubmission)
            .where(RPPSubmission.id == submission_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== REVIEW OPERATIONS =====
    
    async def approve_submission(self, submission_id: int, reviewer_id: int, notes: Optional[str] = None) -> Optional[RPPSubmission]:
        """Approve RPP submission."""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        submission.approve(reviewer_id, notes)
        submission.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def reject_submission(self, submission_id: int, reviewer_id: int, notes: str) -> Optional[RPPSubmission]:
        """Reject RPP submission."""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        submission.reject(reviewer_id, notes)
        submission.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def request_revision(self, submission_id: int, reviewer_id: int, notes: str) -> Optional[RPPSubmission]:
        """Request revision for RPP submission."""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        submission.request_revision(reviewer_id, notes)
        submission.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def resubmit(self, submission_id: int, new_file_id: int) -> Optional[RPPSubmission]:
        """Resubmit RPP submission with new file."""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        submission.file_id = new_file_id
        submission.resubmit()
        submission.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def assign_reviewer(self, submission_id: int, reviewer_id: int) -> Optional[RPPSubmission]:
        """Assign reviewer to submission."""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        submission.reviewer_id = reviewer_id
        submission.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    # ===== LISTING AND FILTERING =====
    
    async def get_all_submissions_filtered(self, filters: RPPSubmissionFilterParams) -> Tuple[List[RPPSubmission], int]:
        """Get RPP submissions with filters and pagination."""
        # Base query with eager loading
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.teacher),
            selectinload(RPPSubmission.reviewer),
            selectinload(RPPSubmission.file),
            selectinload(RPPSubmission.period)
        ).where(RPPSubmission.deleted_at.is_(None))
        count_query = select(func.count(RPPSubmission.id)).where(RPPSubmission.deleted_at.is_(None))
        
        # Join with users for search if needed
        if filters.q:
            query = query.join(User, RPPSubmission.teacher_id == User.id, isouter=True)
            count_query = count_query.join(User, RPPSubmission.teacher_id == User.id, isouter=True)
            
            search_filter = or_(
                RPPSubmission.rpp_type.ilike(f"%{filters.q}%"),
                User.email.ilike(f"%{filters.q}%"),
                func.json_extract_path_text(User.profile, 'name').ilike(f"%{filters.q}%"),
                RPPSubmission.review_notes.ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Apply filters
        if filters.teacher_id:
            query = query.where(RPPSubmission.teacher_id == filters.teacher_id)
            count_query = count_query.where(RPPSubmission.teacher_id == filters.teacher_id)
        
        if filters.reviewer_id:
            query = query.where(RPPSubmission.reviewer_id == filters.reviewer_id)
            count_query = count_query.where(RPPSubmission.reviewer_id == filters.reviewer_id)
        
        if filters.period_id:
            query = query.where(RPPSubmission.period_id == filters.period_id)
            count_query = count_query.where(RPPSubmission.period_id == filters.period_id)
        
        if filters.rpp_type:
            query = query.where(RPPSubmission.rpp_type.ilike(f"%{filters.rpp_type}%"))
            count_query = count_query.where(RPPSubmission.rpp_type.ilike(f"%{filters.rpp_type}%"))
        
        if filters.status:
            query = query.where(RPPSubmission.status == filters.status)
            count_query = count_query.where(RPPSubmission.status == filters.status)
        
        if filters.has_reviewer is not None:
            if filters.has_reviewer:
                query = query.where(RPPSubmission.reviewer_id.is_not(None))
                count_query = count_query.where(RPPSubmission.reviewer_id.is_not(None))
            else:
                query = query.where(RPPSubmission.reviewer_id.is_(None))
                count_query = count_query.where(RPPSubmission.reviewer_id.is_(None))
        
        if filters.needs_review:
            query = query.where(RPPSubmission.status == RPPStatus.PENDING)
            count_query = count_query.where(RPPSubmission.status == RPPStatus.PENDING)
        
        if filters.high_revision_count:
            query = query.where(RPPSubmission.revision_count >= filters.high_revision_count)
            count_query = count_query.where(RPPSubmission.revision_count >= filters.high_revision_count)
        
        # Date filters
        if filters.submitted_after:
            query = query.where(RPPSubmission.submitted_at >= filters.submitted_after)
            count_query = count_query.where(RPPSubmission.submitted_at >= filters.submitted_after)
        
        if filters.submitted_before:
            query = query.where(RPPSubmission.submitted_at <= filters.submitted_before)
            count_query = count_query.where(RPPSubmission.submitted_at <= filters.submitted_before)
        
        if filters.reviewed_after:
            query = query.where(RPPSubmission.reviewed_at >= filters.reviewed_after)
            count_query = count_query.where(RPPSubmission.reviewed_at >= filters.reviewed_after)
        
        if filters.reviewed_before:
            query = query.where(RPPSubmission.reviewed_at <= filters.reviewed_before)
            count_query = count_query.where(RPPSubmission.reviewed_at <= filters.reviewed_before)
        
        if filters.created_after:
            query = query.where(RPPSubmission.created_at >= filters.created_after)
            count_query = count_query.where(RPPSubmission.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(RPPSubmission.created_at <= filters.created_before)
            count_query = count_query.where(RPPSubmission.created_at <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "teacher_name":
            query = query.join(User, RPPSubmission.teacher_id == User.id)
            sort_column = func.json_extract_path_text(User.profile, 'name')
        elif filters.sort_by == "period_id":
            sort_column = RPPSubmission.period_id
        elif filters.sort_by == "rpp_type":
            sort_column = RPPSubmission.rpp_type
        elif filters.sort_by == "status":
            sort_column = RPPSubmission.status
        elif filters.sort_by == "revision_count":
            sort_column = RPPSubmission.revision_count
        elif filters.sort_by == "submitted_at":
            sort_column = RPPSubmission.submitted_at
        elif filters.sort_by == "reviewed_at":
            sort_column = RPPSubmission.reviewed_at
        elif filters.sort_by == "created_at":
            sort_column = RPPSubmission.created_at
        elif filters.sort_by == "updated_at":
            sort_column = RPPSubmission.updated_at
        else:
            sort_column = RPPSubmission.submitted_at
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        submissions = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(submissions), total
    
    async def get_teacher_submissions(self, teacher_id: int, period_id: Optional[int] = None) -> List[RPPSubmission]:
        """Get all submissions for a specific teacher."""
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.reviewer),
            selectinload(RPPSubmission.file)
        ).where(
            and_(
                RPPSubmission.teacher_id == teacher_id,
                RPPSubmission.deleted_at.is_(None)
            )
        )
        
        if period_id:
            query = query.where(RPPSubmission.period_id == period_id)
        
        query = query.order_by(desc(RPPSubmission.submitted_at))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_pending_reviews(self, reviewer_id: Optional[int] = None) -> List[RPPSubmission]:
        """Get all pending review submissions."""
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.teacher),
            selectinload(RPPSubmission.file)
        ).where(
            and_(
                RPPSubmission.status == RPPStatus.PENDING,
                RPPSubmission.deleted_at.is_(None)
            )
        )
        
        if reviewer_id:
            query = query.where(RPPSubmission.reviewer_id == reviewer_id)
        
        query = query.order_by(RPPSubmission.submitted_at.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_submissions_by_period(self, period_id: int) -> List[RPPSubmission]:
        """Get all submissions for a specific academic period."""
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.teacher),
            selectinload(RPPSubmission.reviewer),
            selectinload(RPPSubmission.file)
        ).where(RPPSubmission.period_id == period_id).order_by(desc(RPPSubmission.submitted_at))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== LOOKUP METHODS =====
    
    async def find_existing_submission(
        self,
        teacher_id: int,
        academic_year: str,
        semester: str,
        rpp_type: str
    ) -> Optional[RPPSubmission]:
        """Find existing submission for teacher in academic period and type."""
        query = select(RPPSubmission).where(
            and_(
                RPPSubmission.teacher_id == teacher_id,
                RPPSubmission.academic_year == academic_year,
                RPPSubmission.semester == semester,
                RPPSubmission.rpp_type == rpp_type,
                RPPSubmission.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_overdue_reviews(self, days_threshold: int = 7) -> List[RPPSubmission]:
        """Get submissions that are overdue for review."""
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.teacher),
            selectinload(RPPSubmission.reviewer)
        ).where(
            and_(
                RPPSubmission.status == RPPStatus.PENDING,
                RPPSubmission.submitted_at <= threshold_date,
                RPPSubmission.deleted_at.is_(None)
            )
        ).order_by(RPPSubmission.submitted_at.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_approve(self, submission_ids: List[int], reviewer_id: int, notes: Optional[str] = None) -> int:
        """Bulk approve submissions."""
        query = (
            update(RPPSubmission)
            .where(
                and_(
                    RPPSubmission.id.in_(submission_ids),
                    RPPSubmission.status == RPPStatus.PENDING
                )
            )
            .values(
                status=RPPStatus.APPROVED,
                reviewer_id=reviewer_id,
                review_notes=notes,
                reviewed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_reject(self, submission_ids: List[int], reviewer_id: int, notes: Optional[str] = None) -> int:
        """Bulk reject submissions."""
        query = (
            update(RPPSubmission)
            .where(
                and_(
                    RPPSubmission.id.in_(submission_ids),
                    RPPSubmission.status == RPPStatus.PENDING
                )
            )
            .values(
                status=RPPStatus.REJECTED,
                reviewer_id=reviewer_id,
                review_notes=notes,
                reviewed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_assign_reviewer(self, submission_ids: List[int], reviewer_id: int) -> int:
        """Bulk assign reviewer to submissions."""
        query = (
            update(RPPSubmission)
            .where(RPPSubmission.id.in_(submission_ids))
            .values(
                reviewer_id=reviewer_id,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    # ===== ANALYTICS AND STATISTICS =====
    
    async def get_submissions_analytics(self, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive submissions analytics."""
        base_filter = RPPSubmission.deleted_at.is_(None)
        
        # Total submissions
        total_query = select(func.count(RPPSubmission.id)).where(base_filter)
        total_result = await self.session.execute(total_query)
        total_submissions = total_result.scalar()
        
        # Status distribution
        status_query = (
            select(RPPSubmission.status, func.count(RPPSubmission.id))
            .where(base_filter)
            .group_by(RPPSubmission.status)
        )
        status_result = await self.session.execute(status_query)
        by_status = {status.value: count for status, count in status_result.fetchall()}
        
        # Academic year distribution
        year_query = (
            select(RPPSubmission.academic_year, func.count(RPPSubmission.id))
            .where(base_filter)
            .group_by(RPPSubmission.academic_year)
            .order_by(RPPSubmission.academic_year.desc())
        )
        year_result = await self.session.execute(year_query)
        by_academic_year = dict(year_result.fetchall())
        
        # Semester distribution
        semester_query = (
            select(RPPSubmission.semester, func.count(RPPSubmission.id))
            .where(base_filter)
            .group_by(RPPSubmission.semester)
        )
        semester_result = await self.session.execute(semester_query)
        by_semester = dict(semester_result.fetchall())
        
        # RPP type distribution
        type_query = (
            select(RPPSubmission.rpp_type, func.count(RPPSubmission.id))
            .where(base_filter)
            .group_by(RPPSubmission.rpp_type)
            .order_by(func.count(RPPSubmission.id).desc())
        )
        type_result = await self.session.execute(type_query)
        by_rpp_type = dict(type_result.fetchall())
        
        # Average revision count
        avg_revision_query = select(func.avg(RPPSubmission.revision_count)).where(base_filter)
        avg_revision_result = await self.session.execute(avg_revision_query)
        avg_revision_count = avg_revision_result.scalar() or 0
        
        # Average review time (for reviewed submissions)
        avg_review_time = None
        reviewed_submissions = await self.session.execute(
            select(
                func.avg(
                    func.extract('epoch', RPPSubmission.reviewed_at - RPPSubmission.submitted_at) / 3600
                )
            ).where(
                and_(
                    base_filter,
                    RPPSubmission.reviewed_at.is_not(None)
                )
            )
        )
        avg_review_time_result = reviewed_submissions.scalar()
        if avg_review_time_result:
            avg_review_time = float(avg_review_time_result)
        
        # Pending and overdue counts
        pending_count = by_status.get(RPPStatus.PENDING.value, 0)
        
        overdue_threshold = datetime.utcnow() - timedelta(days=7)
        overdue_query = select(func.count(RPPSubmission.id)).where(
            and_(
                base_filter,
                RPPSubmission.status == RPPStatus.PENDING,
                RPPSubmission.submitted_at <= overdue_threshold
            )
        )
        overdue_result = await self.session.execute(overdue_query)
        overdue_count = overdue_result.scalar()
        
        return {
            "total_submissions": total_submissions,
            "by_status": by_status,
            "by_academic_year": by_academic_year,
            "by_semester": by_semester,
            "by_rpp_type": by_rpp_type,
            "avg_review_time_hours": avg_review_time,
            "avg_revision_count": float(avg_revision_count),
            "pending_reviews": pending_count,
            "overdue_reviews": overdue_count
        }
    
    async def get_teacher_progress(self, teacher_id: int) -> Dict[str, Any]:
        """Get progress statistics for a specific teacher."""
        base_filter = and_(
            RPPSubmission.teacher_id == teacher_id,
            RPPSubmission.deleted_at.is_(None)
        )
        
        # Total submitted
        total_query = select(func.count(RPPSubmission.id)).where(base_filter)
        total_result = await self.session.execute(total_query)
        total_submitted = total_result.scalar()
        
        # Status counts
        status_counts = {}
        for status in RPPStatus:
            status_query = select(func.count(RPPSubmission.id)).where(
                and_(base_filter, RPPSubmission.status == status)
            )
            status_result = await self.session.execute(status_query)
            status_counts[status.value.lower()] = status_result.scalar()
        
        # Completion rate (approved / total)
        completion_rate = 0.0
        if total_submitted > 0:
            completion_rate = (status_counts.get('approved', 0) / total_submitted) * 100
        
        # Average revision count
        avg_revision_query = select(func.avg(RPPSubmission.revision_count)).where(base_filter)
        avg_revision_result = await self.session.execute(avg_revision_query)
        avg_revision_count = avg_revision_result.scalar() or 0
        
        # Last submission date
        last_submission_query = select(func.max(RPPSubmission.submitted_at)).where(base_filter)
        last_submission_result = await self.session.execute(last_submission_query)
        last_submission = last_submission_result.scalar()
        
        return {
            "total_submitted": total_submitted,
            "approved": status_counts.get('approved', 0),
            "rejected": status_counts.get('rejected', 0),
            "pending": status_counts.get('pending', 0),
            "revision_needed": status_counts.get('revision_needed', 0),
            "completion_rate": completion_rate,
            "avg_revision_count": float(avg_revision_count),
            "last_submission": last_submission
        }
    
    async def get_reviewer_workload(self, reviewer_id: int) -> Dict[str, Any]:
        """Get workload statistics for a reviewer."""
        base_filter = and_(
            RPPSubmission.reviewer_id == reviewer_id,
            RPPSubmission.deleted_at.is_(None)
        )
        
        # Total assigned
        total_query = select(func.count(RPPSubmission.id)).where(base_filter)
        total_result = await self.session.execute(total_query)
        total_assigned = total_result.scalar()
        
        # Pending reviews
        pending_query = select(func.count(RPPSubmission.id)).where(
            and_(base_filter, RPPSubmission.status == RPPStatus.PENDING)
        )
        pending_result = await self.session.execute(pending_query)
        pending_reviews = pending_result.scalar()
        
        # Completed reviews
        completed_query = select(func.count(RPPSubmission.id)).where(
            and_(
                base_filter,
                RPPSubmission.status.in_([RPPStatus.APPROVED, RPPStatus.REJECTED, RPPStatus.REVISION_NEEDED])
            )
        )
        completed_result = await self.session.execute(completed_query)
        completed_reviews = completed_result.scalar()
        
        # Average review time
        avg_review_time_query = select(
            func.avg(
                func.extract('epoch', RPPSubmission.reviewed_at - RPPSubmission.submitted_at) / 3600
            )
        ).where(
            and_(base_filter, RPPSubmission.reviewed_at.is_not(None))
        )
        avg_review_time_result = await self.session.execute(avg_review_time_query)
        avg_review_time = avg_review_time_result.scalar()
        
        return {
            "total_assigned": total_assigned,
            "pending_reviews": pending_reviews,
            "completed_reviews": completed_reviews,
            "avg_review_time_hours": float(avg_review_time) if avg_review_time else 0.0
        }