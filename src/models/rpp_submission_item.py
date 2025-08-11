"""RPP Submission Item model for individual RPP uploads."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .period import Period
    from .media_file import MediaFile
    from .rpp_submission import RPPSubmission


class RPPSubmissionItem(BaseModel, SQLModel, table=True):
    """RPP Submission Item model for individual RPP uploads."""
    
    __tablename__ = "rpp_submission_items"
    
    id: int = Field(primary_key=True)
    teacher_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    period_id: int = Field(foreign_key="periods.id", index=True, nullable=False)
    rpp_submission_id: Optional[int] = Field(
        default=None,
        foreign_key="rpp_submissions.id",
        index=True,
        description="Reference to the main RPP submission"
    )
    file_id: Optional[int] = Field(
        default=None, 
        foreign_key="media_files.id",
        description="Media file ID - NULL until file is uploaded"
    )
    uploaded_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when file was uploaded"
    )
    
    # Relationships
    teacher: "User" = Relationship(
        back_populates="rpp_submission_items",
        sa_relationship_kwargs={"foreign_keys": "RPPSubmissionItem.teacher_id"}
    )
    period: "Period" = Relationship(
        back_populates="rpp_submission_items"
    )
    file: Optional["MediaFile"] = Relationship(
        back_populates="rpp_submission_items"
    )
    rpp_submission: Optional["RPPSubmission"] = Relationship(
        back_populates="items"
    )
    
    def __repr__(self) -> str:
        return f"<RPPSubmissionItem(id={self.id}, teacher_id={self.teacher_id}, period_id={self.period_id})>"
    
    @property
    def is_uploaded(self) -> bool:
        """Check if file has been uploaded."""
        return self.file_id is not None
    
    
    def mark_as_uploaded(self, file_id: int) -> None:
        """Mark item as uploaded with file ID."""
        self.file_id = file_id
        self.uploaded_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()