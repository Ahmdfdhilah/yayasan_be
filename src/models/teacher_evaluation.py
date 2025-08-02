"""Teacher Evaluation model - Parent/Summary model for teacher evaluations."""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
from sqlalchemy import event
from pydantic import validator

from .base import BaseModel
from .enums import EvaluationGrade
from ..utils.sanitize_html import sanitize_html_content

if TYPE_CHECKING:
    from .user import User
    from .period import Period
    from .teacher_evaluation_item import TeacherEvaluationItem


class TeacherEvaluation(BaseModel, SQLModel, table=True):
    """Parent teacher evaluation model with auto-calculated aggregate data."""
    
    __tablename__ = "teacher_evaluations"
    __table_args__ = (
        UniqueConstraint('teacher_id', 'period_id', 'evaluator_id', name='uq_teacher_period_evaluator'),
        {"sqlite_autoincrement": True}
    )
    
    id: int = Field(primary_key=True)
    teacher_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    evaluator_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    period_id: int = Field(foreign_key="periods.id", nullable=False, index=True)
    
    # Auto-calculated aggregate fields - nullable until evaluated
    total_score: Optional[int] = Field(default=None, description="Sum of all aspect scores")
    average_score: Optional[float] = Field(default=None, description="Average score across all aspects")
    final_grade: Optional[float] = Field(default=None, description="Final grade calculated as total_score * 1.25")
    
    # Summary notes from evaluator
    final_notes: Optional[str] = Field(default=None, max_length=1000, description="Final evaluation summary")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Relationships
    teacher: "User" = Relationship(
        back_populates="received_evaluations",
        sa_relationship_kwargs={"foreign_keys": "TeacherEvaluation.teacher_id"}
    )
    evaluator: "User" = Relationship(
        back_populates="conducted_evaluations",
        sa_relationship_kwargs={"foreign_keys": "TeacherEvaluation.evaluator_id"}
    )
    period: "Period" = Relationship(back_populates="teacher_evaluations")
    items: List["TeacherEvaluationItem"] = Relationship(
        back_populates="teacher_evaluation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    def __repr__(self) -> str:
        return f"<TeacherEvaluation(id={self.id}, teacher_id={self.teacher_id}, period_id={self.period_id}, final_grade={self.final_grade})>"
    
    @property
    def item_count(self) -> int:
        """Get count of evaluation items."""
        try:
            return len(self.items) if self.items else 0
        except Exception:
            # Return 0 if items can't be loaded (e.g., in async context without proper session)
            return 0
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage of evaluation aspects."""
        if not self.items:
            return 0.0
        evaluated_items = len([item for item in self.items if item.grade is not None])
        return (evaluated_items / len(self.items)) * 100.0
    
    @property
    def final_grade_description(self) -> str:
        """Get description for the final grade."""
        if self.final_grade is None:
            return "Belum dinilai"
        if self.final_grade >= 87.5:  # 70 * 1.25 = 87.5 (equivalent to A grade)
            return "Excellent (A)"
        elif self.final_grade >= 62.5:  # 50 * 1.25 = 62.5 (equivalent to B grade)
            return "Good (B)"
        elif self.final_grade >= 37.5:  # 30 * 1.25 = 37.5 (equivalent to C grade)
            return "Satisfactory (C)"
        else:
            return "Needs Improvement (D)"
    
    def recalculate_aggregates(self) -> None:
        """Recalculate total_score, average_score, and final_grade from items."""
        if not self.items:
            self.total_score = None
            self.average_score = None
            self.final_grade = None
            return
        
        # Only calculate from items that have been evaluated (have score)
        evaluated_items = [item for item in self.items if item.score is not None]
        
        if not evaluated_items:
            self.total_score = None
            self.average_score = None
            self.final_grade = None
            return
        
        # Calculate totals from evaluated items only
        self.total_score = sum(item.score for item in evaluated_items)
        self.average_score = self.total_score / len(evaluated_items)
        
        # Calculate final grade as total_score * 1.25
        self.final_grade = self.total_score * 1.25
        
        self.last_updated = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @validator('final_notes')
    def sanitize_final_notes(cls, v):
        """Sanitize HTML content in final_notes field."""
        if v:
            return sanitize_html_content(v)
        return v
    
    def update_final_notes(self, notes: Optional[str]) -> None:
        """Update final evaluation notes."""
        self.final_notes = notes
        self.last_updated = datetime.utcnow()
        self.updated_at = datetime.utcnow()


# Event listeners for auto-calculation
@event.listens_for(TeacherEvaluation.items, 'append')
def receive_append(target, value, initiator):
    """Recalculate when item is added."""
    target.recalculate_aggregates()


@event.listens_for(TeacherEvaluation.items, 'remove')
def receive_remove(target, value, initiator):
    """Recalculate when item is removed."""
    target.recalculate_aggregates()