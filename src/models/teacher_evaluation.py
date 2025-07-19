"""Teacher Evaluation model for PKG System."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .evaluation_aspect import EvaluationAspect


class TeacherEvaluation(BaseModel, SQLModel, table=True):
    """Teacher evaluation model for individual aspect scoring."""
    
    __tablename__ = "teacher_evaluations"
    
    id: int = Field(primary_key=True)
    evaluator_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    teacher_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    aspect_id: int = Field(foreign_key="evaluation_aspects.id", nullable=False, index=True)
    
    # Academic period
    academic_year: str = Field(max_length=20, nullable=False, index=True)
    semester: str = Field(max_length=20, nullable=False, index=True)
    
    # Scoring
    score: int = Field(nullable=False)
    notes: Optional[str] = Field(default=None)
    
    # Evaluation timestamp
    evaluation_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    evaluator: "User" = Relationship(back_populates="conducted_evaluations")
    teacher: "User" = Relationship(back_populates="received_evaluations")
    aspect: "EvaluationAspect" = Relationship(back_populates="teacher_evaluations")
    
    # Unique constraint defined at table level
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<TeacherEvaluation(id={self.id}, teacher_id={self.teacher_id}, aspect_id={self.aspect_id}, score={self.score})>"
    
    @property
    def academic_period(self) -> str:
        """Get formatted academic period."""
        return f"{self.academic_year} - {self.semester}"
    
    def is_score_valid(self) -> bool:
        """Check if score is valid for the associated aspect."""
        if self.aspect:
            return self.aspect.is_score_valid(self.score)
        return True  # Cannot validate without aspect loaded
    
    def get_weighted_score(self) -> float:
        """Get weighted score based on aspect weight."""
        if self.aspect:
            return float(self.aspect.calculate_weighted_score(self.score))
        return float(self.score)  # Return raw score if aspect not loaded
    
    def get_score_description(self) -> str:
        """Get description for the score."""
        if self.aspect:
            return self.aspect.get_score_description(self.score)
        return "Unknown"
    
    def update_score(self, new_score: int, notes: Optional[str] = None) -> None:
        """Update the evaluation score."""
        if self.aspect and not self.aspect.is_score_valid(new_score):
            raise ValueError(f"Score {new_score} is not valid for aspect {self.aspect.aspect_name}")
        
        self.score = new_score
        if notes is not None:
            self.notes = notes
        self.evaluation_date = datetime.utcnow()
    
    def add_notes(self, notes: str) -> None:
        """Add or update evaluation notes."""
        self.notes = notes