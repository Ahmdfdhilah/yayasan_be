"""RPP Submission repository for database operations."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, case, distinct, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.models.rpp_submission import RPPSubmission
from src.models.rpp_submission_item import RPPSubmissionItem
from src.models.user import User
from src.models.period import Period
from src.models.media_file import MediaFile
from src.models.enums import RPPSubmissionStatus
from src.schemas.rpp_submission import (
    RPPSubmissionCreate, RPPSubmissionUpdate, RPPSubmissionFilter,
    RPPSubmissionItemCreate, RPPSubmissionItemUpdate, RPPSubmissionItemFilter
)


class RPPSubmissionRepository:
    """Repository for RPP Submission operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== RPP SUBMISSION CRUD OPERATIONS =====
    
    async def create_submission(self, submission_data: RPPSubmissionCreate) -> RPPSubmission:
        """Create new RPP submission."""
        submission = RPPSubmission(
            teacher_id=submission_data.teacher_id,
            period_id=submission_data.period_id,
            status=RPPSubmissionStatus.DRAFT
        )
        
        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def get_submission_by_id(self, submission_id: int) -> Optional[RPPSubmission]:
        """Get submission by ID with related data."""
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.teacher).selectinload(User.organization),
            selectinload(RPPSubmission.reviewer),
            selectinload(RPPSubmission.period),
            selectinload(RPPSubmission.items).selectinload(RPPSubmissionItem.file)
        ).where(
            and_(RPPSubmission.id == submission_id, RPPSubmission.deleted_at.is_(None))
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_submission_by_teacher_period(
        self, teacher_id: int, period_id: int
    ) -> Optional[RPPSubmission]:
        """Get submission by teacher and period."""
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.teacher).selectinload(User.organization),
            selectinload(RPPSubmission.reviewer),
            selectinload(RPPSubmission.period),
            selectinload(RPPSubmission.items).selectinload(RPPSubmissionItem.file)
        ).where(
            and_(
                RPPSubmission.teacher_id == teacher_id,
                RPPSubmission.period_id == period_id,
                RPPSubmission.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_submission(
        self, submission_id: int, submission_data: RPPSubmissionUpdate
    ) -> Optional[RPPSubmission]:
        """Update submission."""
        query = (
            update(RPPSubmission)
            .where(
                and_(RPPSubmission.id == submission_id, RPPSubmission.deleted_at.is_(None))
            )
            .values(
                status=submission_data.status,
                review_notes=submission_data.review_notes,
                updated_at=datetime.utcnow()
            )
            .returning(RPPSubmission)
        )
        
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()
    
    async def submit_for_review(self, submission_id: int) -> bool:
        """Submit submission for review."""
        query = (
            update(RPPSubmission)
            .where(
                and_(
                    RPPSubmission.id == submission_id,
                    RPPSubmission.status.in_([RPPSubmissionStatus.DRAFT, RPPSubmissionStatus.REJECTED]),
                    RPPSubmission.deleted_at.is_(None)
                )
            )
            .values(
                status=RPPSubmissionStatus.PENDING,
                submitted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def review_submission(
        self, submission_id: int, reviewer_id: int, status: RPPSubmissionStatus, notes: Optional[str] = None
    ) -> bool:
        """Review submission (approve/reject/request revision)."""
        query = (
            update(RPPSubmission)
            .where(
                and_(
                    RPPSubmission.id == submission_id,
                    RPPSubmission.status == RPPSubmissionStatus.PENDING,
                    RPPSubmission.deleted_at.is_(None)
                )
            )
            .values(
                status=status,
                reviewer_id=reviewer_id,
                review_notes=notes,
                reviewed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def delete_submission(self, submission_id: int) -> bool:
        """Soft delete submission."""
        query = (
            update(RPPSubmission)
            .where(
                and_(RPPSubmission.id == submission_id, RPPSubmission.deleted_at.is_(None))
            )
            .values(deleted_at=datetime.utcnow())
        )
        
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== RPP SUBMISSION ITEM CRUD OPERATIONS =====
    
    async def create_submission_item(self, item_data: RPPSubmissionItemCreate) -> RPPSubmissionItem:
        """Create new RPP submission item."""
        item = RPPSubmissionItem(
            teacher_id=item_data.teacher_id,
            period_id=item_data.period_id,
            rpp_submission_id=item_data.rpp_submission_id,
            name=item_data.name,
            description=item_data.description,
            file_id=item_data.file_id
        )
        
        # Set uploaded_at if file_id is provided
        if item_data.file_id:
            item.uploaded_at = datetime.utcnow()
        
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item
    
    async def get_submission_item_by_id(self, item_id: int) -> Optional[RPPSubmissionItem]:
        """Get submission item by ID."""
        print(f"Repository: Looking for item_id: {item_id}")
        
        query = select(RPPSubmissionItem).options(
            selectinload(RPPSubmissionItem.teacher),
            selectinload(RPPSubmissionItem.period),
            selectinload(RPPSubmissionItem.file)
        ).where(
            and_(RPPSubmissionItem.id == item_id, RPPSubmissionItem.deleted_at.is_(None))
        )
        
        result = await self.session.execute(query)
        item = result.scalar_one_or_none()
        print(f"Repository: Found item: {item}")
        return item
    
    
    async def update_submission_item_file(
        self, item_id: int, file_id: int
    ) -> Optional[RPPSubmissionItem]:
        """Update submission item file."""
        query = (
            update(RPPSubmissionItem)
            .where(
                and_(RPPSubmissionItem.id == item_id, RPPSubmissionItem.deleted_at.is_(None))
            )
            .values(
                file_id=file_id,
                uploaded_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            .returning(RPPSubmissionItem)
        )
        
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()
    
    async def update_submission_item_details(
        self, item_id: int, name: str, description: Optional[str] = None
    ) -> Optional[RPPSubmissionItem]:
        """Update submission item name and description."""
        query = (
            update(RPPSubmissionItem)
            .where(
                and_(RPPSubmissionItem.id == item_id, RPPSubmissionItem.deleted_at.is_(None))
            )
            .values(
                name=name,
                description=description,
                updated_at=datetime.utcnow()
            )
            .returning(RPPSubmissionItem)
        )
        
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()
    
    async def delete_submission_item(self, item_id: int) -> bool:
        """Delete submission item (soft delete)."""
        query = (
            update(RPPSubmissionItem)
            .where(
                and_(RPPSubmissionItem.id == item_id, RPPSubmissionItem.deleted_at.is_(None))
            )
            .values(deleted_at=datetime.utcnow())
            .returning(RPPSubmissionItem.id)
        )
        
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none() is not None
    
    # ===== QUERY OPERATIONS =====
    
    async def get_submissions_by_filter(
        self, filters: RPPSubmissionFilter, limit: int = 100, offset: int = 0
    ) -> Tuple[List[RPPSubmission], int]:
        """Get submissions with filtering and pagination."""
        # Build base query
        query = select(RPPSubmission).options(
            selectinload(RPPSubmission.teacher).selectinload(User.organization),
            selectinload(RPPSubmission.reviewer),
            selectinload(RPPSubmission.period),
            selectinload(RPPSubmission.items).selectinload(RPPSubmissionItem.file)
        )
        
        # Build where conditions
        conditions = [RPPSubmission.deleted_at.is_(None)]
        
        if filters.teacher_id:
            conditions.append(RPPSubmission.teacher_id == filters.teacher_id)
        if filters.period_id:
            conditions.append(RPPSubmission.period_id == filters.period_id)
        if filters.status:
            conditions.append(RPPSubmission.status == filters.status)
        if filters.reviewer_id:
            conditions.append(RPPSubmission.reviewer_id == filters.reviewer_id)
        
        # Search by teacher name
        if filters.search:
            search_term = f"%{filters.search.lower()}%"
            # Make sure User is joined if search is provided
            query = query.join(User, RPPSubmission.teacher_id == User.id)
            conditions.append(
                or_(
                    func.lower(func.cast(User.profile.op('->')('name'), String)).like(search_term),
                    func.lower(User.email).like(search_term)
                )
            )
        
        if filters.submitted_after:
            conditions.append(RPPSubmission.submitted_at >= filters.submitted_after)
        if filters.submitted_before:
            conditions.append(RPPSubmission.submitted_at <= filters.submitted_before)
        if filters.reviewed_after:
            conditions.append(RPPSubmission.reviewed_at >= filters.reviewed_after)
        if filters.reviewed_before:
            conditions.append(RPPSubmission.reviewed_at <= filters.reviewed_before)
        
        # Organization filter via teacher
        if filters.organization_id:
            query = query.join(User, RPPSubmission.teacher_id == User.id)
            conditions.append(User.organization_id == filters.organization_id)
        
        # Submitter role filter via teacher role
        if filters.submitter_role:
            if User not in query.column_descriptions:
                query = query.join(User, RPPSubmission.teacher_id == User.id)
            conditions.append(User.role == filters.submitter_role)
        
        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(distinct(RPPSubmission.id))).where(and_(*conditions))
        if filters.organization_id or filters.submitter_role or filters.search:
            count_query = count_query.join(User, RPPSubmission.teacher_id == User.id)
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        submissions = result.scalars().all()
        
        return list(submissions), total
    
    async def get_submission_items_by_filter(
        self, filters: RPPSubmissionItemFilter, limit: int = 100, offset: int = 0
    ) -> Tuple[List[RPPSubmissionItem], int]:
        """Get submission items with filtering and pagination."""
        # Build base query
        query = select(RPPSubmissionItem).options(
            selectinload(RPPSubmissionItem.teacher),
            selectinload(RPPSubmissionItem.period),
            selectinload(RPPSubmissionItem.file)
        )
        
        # Build where conditions
        conditions = [RPPSubmissionItem.deleted_at.is_(None)]
        
        if filters.teacher_id:
            conditions.append(RPPSubmissionItem.teacher_id == filters.teacher_id)
        if filters.period_id:
            conditions.append(RPPSubmissionItem.period_id == filters.period_id)
        if filters.is_uploaded is not None:
            if filters.is_uploaded:
                conditions.append(RPPSubmissionItem.file_id.is_not(None))
            else:
                conditions.append(RPPSubmissionItem.file_id.is_(None))
        
        # Organization filter via teacher
        if filters.organization_id:
            query = query.join(User, RPPSubmissionItem.teacher_id == User.id)
            conditions.append(User.organization_id == filters.organization_id)
        
        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(distinct(RPPSubmissionItem.id))).where(and_(*conditions))
        if filters.organization_id:
            count_query = count_query.join(User, RPPSubmissionItem.teacher_id == User.id)
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    # ===== GENERATION OPERATIONS =====
    
    async def generate_submissions_for_period(self, period_id: int) -> Tuple[int, int, int]:
        """Generate submissions and items for all teachers in a period.
        
        Returns:
            Tuple of (generated_count, skipped_count, total_teachers)
        """
        # Get all active teachers (guru) and kepala sekolah, excluding admin users
        teachers_query = select(User).where(
            and_(
                User.status == "active", 
                User.deleted_at.is_(None),
                User.role.in_(["GURU", "KEPALA_SEKOLAH"])
            )
        )
        teachers_result = await self.session.execute(teachers_query)
        teachers = teachers_result.scalars().all()
        
        total_teachers = len(teachers)
        generated_count = 0
        skipped_count = 0
        
        for teacher in teachers:
            # Check if submission already exists
            existing_submission = await self.get_submission_by_teacher_period(teacher.id, period_id)
            
            if existing_submission:
                skipped_count += 1
                continue
            
            # Create submission
            submission = RPPSubmission(
                teacher_id=teacher.id,
                period_id=period_id,
                status=RPPSubmissionStatus.DRAFT
            )
            self.session.add(submission)
            await self.session.flush()  # Flush to get the submission.id
            
            # No initial items created - teachers will create items by uploading files
            
            generated_count += 1
        
        await self.session.commit()
        return generated_count, skipped_count, total_teachers
    
    # ===== STATISTICS OPERATIONS =====
    
    async def get_submission_stats(
        self, period_id: Optional[int] = None, organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get submission statistics."""
        query = select(
            func.count(RPPSubmission.id).label('total'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.DRAFT, 1), else_=0)).label('draft'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.PENDING, 1), else_=0)).label('pending'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.APPROVED, 1), else_=0)).label('approved'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.REJECTED, 1), else_=0)).label('rejected'),
        ).where(RPPSubmission.deleted_at.is_(None))
        
        if period_id:
            query = query.where(RPPSubmission.period_id == period_id)
        
        if organization_id:
            query = query.join(User, RPPSubmission.teacher_id == User.id).where(
                User.organization_id == organization_id
            )
        
        result = await self.session.execute(query)
        stats = result.one()
        
        # Calculate completion rate
        total = stats.total or 0
        completed = (stats.approved or 0) + (stats.rejected or 0)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            'total_submissions': total,
            'draft_count': stats.draft or 0,
            'pending_count': stats.pending or 0,
            'approved_count': stats.approved or 0,
            'rejected_count': stats.rejected or 0,
            'completion_rate': completion_rate
        }
    
    async def can_submission_be_submitted(self, submission_id: int) -> bool:
        """Check if submission can be submitted for approval."""
        # Get submission with items
        submission = await self.get_submission_by_id(submission_id)
        if not submission or submission.status not in [RPPSubmissionStatus.DRAFT, RPPSubmissionStatus.REJECTED]:
            return False
        
        # Check if at least one file has been uploaded
        uploaded_items = [item for item in submission.items if item.file_id is not None]
        return len(uploaded_items) > 0

    # Dashboard-specific methods
    
    async def get_teacher_progress(self, teacher_id: int) -> Dict[str, Any]:
        """Get RPP progress for a specific teacher."""
        query = select(
            func.count(RPPSubmission.id).label('total_submitted'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.PENDING, 1), else_=0)).label('pending'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.APPROVED, 1), else_=0)).label('approved'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.REJECTED, 1), else_=0)).label('rejected'),
        ).where(
            and_(
                RPPSubmission.teacher_id == teacher_id,
                RPPSubmission.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(query)
        stats = result.one()
        
        total = stats.total_submitted or 0
        approved = stats.approved or 0
        completion_rate = (approved / total * 100) if total > 0 else 0
        
        return {
            'total_submitted': total,
            'pending': stats.pending or 0,
            'approved': approved,
            'rejected': stats.rejected or 0,
            'completion_rate': completion_rate
        }
    
    async def get_submissions_analytics(self, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Get submissions analytics for organization or system-wide."""
        # Base query for submission counts
        query = select(
            func.count(RPPSubmission.id).label('total'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.PENDING, 1), else_=0)).label('pending'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.APPROVED, 1), else_=0)).label('approved'),
            func.sum(case((RPPSubmission.status == RPPSubmissionStatus.REJECTED, 1), else_=0)).label('rejected'),
        ).where(RPPSubmission.deleted_at.is_(None))
        
        if organization_id:
            query = query.join(User, RPPSubmission.teacher_id == User.id).where(
                User.organization_id == organization_id
            )
        
        result = await self.session.execute(query)
        stats = result.one()
        
        # Count pending reviews (submissions with PENDING status)
        pending_reviews_query = select(func.count(RPPSubmission.id)).where(
            and_(
                RPPSubmission.status == RPPSubmissionStatus.PENDING,
                RPPSubmission.deleted_at.is_(None)
            )
        )
        
        if organization_id:
            pending_reviews_query = pending_reviews_query.join(
                User, RPPSubmission.teacher_id == User.id
            ).where(User.organization_id == organization_id)
        
        pending_reviews_result = await self.session.execute(pending_reviews_query)
        pending_reviews = pending_reviews_result.scalar() or 0
        
        return {
            'total_submissions': stats.total or 0,
            'by_status': {
                'pending': stats.pending or 0,
                'approved': stats.approved or 0,
                'rejected': stats.rejected or 0
            },
            'pending_reviews': pending_reviews,
            'avg_review_time_hours': None  # Could be calculated if we track review timestamps
        }
    
    async def get_teacher_submissions(self, teacher_id: int, period_id: Optional[int] = None) -> List[RPPSubmission]:
        """Get all submissions for a teacher, optionally filtered by period."""
        query = select(RPPSubmission).where(
            and_(
                RPPSubmission.teacher_id == teacher_id,
                RPPSubmission.deleted_at.is_(None)
            )
        )
        
        if period_id:
            query = query.where(RPPSubmission.period_id == period_id)
        
        query = query.order_by(RPPSubmission.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_pending_reviews(self, reviewer_id: int) -> List[RPPSubmission]:
        """Get submissions pending review by a specific reviewer (principal)."""
        # Get submissions with PENDING status from teachers in the same organization as reviewer
        reviewer_query = select(User.organization_id).where(User.id == reviewer_id)
        reviewer_result = await self.session.execute(reviewer_query)
        reviewer_org_id = reviewer_result.scalar()
        
        if not reviewer_org_id:
            return []
        
        query = select(RPPSubmission).join(
            User, RPPSubmission.teacher_id == User.id
        ).where(
            and_(
                RPPSubmission.status == RPPSubmissionStatus.PENDING,
                User.organization_id == reviewer_org_id,
                RPPSubmission.deleted_at.is_(None)
            )
        ).order_by(RPPSubmission.created_at.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_submissions_by_period(self, period_id: int) -> List[RPPSubmission]:
        """Get all submissions for a specific period."""
        query = select(RPPSubmission).where(
            and_(
                RPPSubmission.period_id == period_id,
                RPPSubmission.deleted_at.is_(None)
            )
        ).order_by(RPPSubmission.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())