"""RPP Submission model for PKG System."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, Relationship
from sqlalchemy import Enum as SQLEnum

from .base import BaseModel
from .enums import RPPStatus

if TYPE_CHECKING:
    from .user import User
    from .media_file import MediaFile


class RPPSubmission(BaseModel, SQLModel, table=True):
    """RPP Submission model for teacher evaluations."""
    
    __tablename__ = "rpp_submissions"
    
    id: int = Field(primary_key=True)
    teacher_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    academic_year: str = Field(max_length=20, nullable=False, index=True)
    semester: str = Field(max_length=20, nullable=False, index=True)
    rpp_type: str = Field(max_length=100, nullable=False)
    file_id: int = Field(foreign_key="media_files.id", nullable=False)
    
    # Status and review
    status: RPPStatus = Field(
        sa_column=Column(SQLEnum(RPPStatus), nullable=False, default=RPPStatus.PENDING),
        description="RPP submission status"
    )
    reviewer_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        index=True
    )
    review_notes: Optional[str] = Field(default=None)
    revision_count: int = Field(default=0)
    
    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    teacher: "User" = Relationship(back_populates="submitted_rpps")
    reviewer: Optional["User"] = Relationship(back_populates="reviewed_rpps")
    file: "MediaFile" = Relationship(back_populates="rpp_submissions")
    
    def __repr__(self) -> str:
        return f"<RPPSubmission(id={self.id}, teacher_id={self.teacher_id}, status={self.status.value})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if submission is pending review."""
        return self.status == RPPStatus.PENDING
    
    @property
    def is_approved(self) -> bool:
        """Check if submission is approved."""
        return self.status == RPPStatus.APPROVED
    
    @property
    def is_rejected(self) -> bool:
        """Check if submission is rejected."""
        return self.status == RPPStatus.REJECTED
    
    @property
    def needs_revision(self) -> bool:
        """Check if submission needs revision."""
        return self.status == RPPStatus.REVISION_NEEDED
    
    def approve(self, reviewer_id: int, notes: Optional[str] = None) -> None:
        """Approve the RPP submission."""
        self.status = RPPStatus.APPROVED
        self.reviewer_id = reviewer_id
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
    
    def reject(self, reviewer_id: int, notes: str) -> None:
        """Reject the RPP submission."""
        self.status = RPPStatus.REJECTED
        self.reviewer_id = reviewer_id
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
    
    def request_revision(self, reviewer_id: int, notes: str) -> None:
        """Request revision for the RPP submission."""
        self.status = RPPStatus.REVISION_NEEDED
        self.reviewer_id = reviewer_id
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
        self.revision_count += 1
    
    def resubmit(self) -> None:
        """Mark as resubmitted (back to pending)."""
        self.status = RPPStatus.PENDING
        self.submitted_at = datetime.utcnow()
        self.reviewed_at = None
        self.review_notes = None