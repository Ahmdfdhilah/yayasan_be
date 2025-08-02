"""RPP Submission model for main submission approval process."""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
from sqlalchemy import Enum as SQLEnum, Column
from pydantic import validator

from .base import BaseModel
from .enums import RPPSubmissionStatus, RPPType
from ..utils.sanitize_html import sanitize_html_content

if TYPE_CHECKING:
    from .user import User
    from .period import Period
    from .rpp_submission_item import RPPSubmissionItem


class RPPSubmission(BaseModel, SQLModel, table=True):
    """RPP Submission model for main submission approval process."""
    
    __tablename__ = "rpp_submissions"
    __table_args__ = (
        UniqueConstraint('teacher_id', 'period_id', name='uq_teacher_period_submission'),
    )
    
    id: int = Field(primary_key=True)
    teacher_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    period_id: int = Field(foreign_key="periods.id", index=True, nullable=False)
    status: RPPSubmissionStatus = Field(
        sa_column=Column(SQLEnum(RPPSubmissionStatus), nullable=False, default=RPPSubmissionStatus.DRAFT),
        description="Submission status: draft, pending, approved, rejected"
    )
    reviewer_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        description="User ID of reviewer (kepala sekolah)"
    )
    review_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Review notes from kepala sekolah"
    )
    submitted_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when submitted for approval"
    )
    reviewed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when reviewed"
    )
    
    # Relationships
    teacher: "User" = Relationship(
        back_populates="submitted_rpps",
        sa_relationship_kwargs={"foreign_keys": "RPPSubmission.teacher_id"}
    )
    reviewer: Optional["User"] = Relationship(
        back_populates="reviewed_rpps",
        sa_relationship_kwargs={"foreign_keys": "RPPSubmission.reviewer_id"}
    )
    period: "Period" = Relationship(
        back_populates="rpp_submissions"
    )
    items: List["RPPSubmissionItem"] = Relationship(
        back_populates="rpp_submission"
    )
    
    def __repr__(self) -> str:
        return f"<RPPSubmission(id={self.id}, teacher_id={self.teacher_id}, period_id={self.period_id}, status={self.status.value})>"
    
    @property
    def is_draft(self) -> bool:
        """Check if submission is in draft status."""
        return self.status == RPPSubmissionStatus.DRAFT
    
    @property
    def is_pending(self) -> bool:
        """Check if submission is pending review."""
        return self.status == RPPSubmissionStatus.PENDING
    
    @property
    def is_approved(self) -> bool:
        """Check if submission is approved."""
        return self.status == RPPSubmissionStatus.APPROVED
    
    @property
    def is_rejected(self) -> bool:
        """Check if submission is rejected."""
        return self.status == RPPSubmissionStatus.REJECTED
    
    @property
    def can_be_submitted(self) -> bool:
        """Check if submission can be submitted for approval."""
        if self.status not in [RPPSubmissionStatus.DRAFT, RPPSubmissionStatus.REJECTED]:
            return False
        
        # Check if all 3 RPP types have been uploaded
        uploaded_types = {item.rpp_type for item in self.items if item.is_uploaded}
        required_types = set(RPPType.get_all_values())
        return uploaded_types == required_types
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage based on uploaded items."""
        if not self.items:
            return 0.0
        
        uploaded_count = sum(1 for item in self.items if item.is_uploaded)
        total_count = len(self.items)
        return (uploaded_count / total_count) * 100 if total_count > 0 else 0.0
    
    def submit_for_review(self) -> bool:
        """Submit for review if all requirements are met."""
        if not self.can_be_submitted:
            return False
        
        self.status = RPPSubmissionStatus.PENDING
        self.submitted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True
    
    @validator('review_notes')
    def sanitize_review_notes(cls, v):
        """Sanitize HTML content in review_notes field."""
        if v:
            return sanitize_html_content(v)
        return v
    
    def approve(self, reviewer_id: int, notes: Optional[str] = None) -> None:
        """Approve submission."""
        self.status = RPPSubmissionStatus.APPROVED
        self.reviewer_id = reviewer_id
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def reject(self, reviewer_id: int, notes: str) -> None:
        """Reject submission."""
        self.status = RPPSubmissionStatus.REJECTED
        self.reviewer_id = reviewer_id
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def reset_to_draft(self) -> None:
        """Reset submission back to draft for revision."""
        self.status = RPPSubmissionStatus.DRAFT
        self.submitted_at = None
        self.updated_at = datetime.utcnow()