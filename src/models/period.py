"""Period model for universal period management."""

from typing import List, Optional, TYPE_CHECKING
from datetime import date
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .teacher_evaluation import TeacherEvaluation
    from .rpp_submission import RPPSubmission


class Period(BaseModel, SQLModel, table=True):
    """Universal period model for evaluations and RPP submissions."""
    
    __tablename__ = "periods"
    
    id: int = Field(primary_key=True)
    academic_year: str = Field(max_length=20, nullable=False, index=True)
    semester: str = Field(max_length=20, nullable=False, index=True)
    start_date: date = Field(nullable=False)
    end_date: date = Field(nullable=False)
    is_active: bool = Field(default=False, index=True)
    description: Optional[str] = Field(default=None)
    
    # Relationships
    teacher_evaluations: List["TeacherEvaluation"] = Relationship(back_populates="period")
    rpp_submissions: List["RPPSubmission"] = Relationship(back_populates="period")
    
    # Unique constraint for academic_year + semester
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<Period(id={self.id}, {self.academic_year}-{self.semester})>"
    
    @property
    def period_name(self) -> str:
        """Get formatted period name."""
        return f"{self.academic_year} - {self.semester}"
    
    @property
    def is_current(self) -> bool:
        """Check if period is currently active based on dates."""
        from datetime import date
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    def activate(self) -> None:
        """Activate this period."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate this period."""
        self.is_active = False
    
    def is_date_in_period(self, check_date: date) -> bool:
        """Check if date falls within this period."""
        return self.start_date <= check_date <= self.end_date
    
    def get_duration_days(self) -> int:
        """Get period duration in days."""
        return (self.end_date - self.start_date).days + 1
    
    def validate_dates(self) -> bool:
        """Validate that start_date is before end_date."""
        return self.start_date < self.end_date