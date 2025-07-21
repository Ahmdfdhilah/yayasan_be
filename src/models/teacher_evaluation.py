"""Teacher Evaluation model - Parent/Summary model for teacher evaluations."""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
from sqlalchemy import event

from .base import BaseModel
from .enums import EvaluationGrade

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
    
    # Auto-calculated aggregate fields
    total_score: int = Field(default=0, description="Sum of all aspect scores")
    average_score: float = Field(default=0.0, description="Average score across all aspects")
    final_grade: Optional[EvaluationGrade] = Field(default=None, description="Final grade based on average")
    
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
        back_populates="teacher_evaluation"
    )
    
    def __repr__(self) -> str:
        return f"<TeacherEvaluation(id={self.id}, teacher_id={self.teacher_id}, period_id={self.period_id}, final_grade={self.final_grade})>"
    
    @property
    def item_count(self) -> int:
        """Get count of evaluation items."""
        return len(self.items) if self.items else 0
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage of evaluation aspects."""
        if not self.items:
            return 0.0
        return 100.0  # All items are completed if they exist
    
    @property
    def final_grade_description(self) -> Optional[str]:
        """Get description for the final grade."""
        if self.final_grade:
            return EvaluationGrade.get_description(self.final_grade)
        return None
    
    def recalculate_aggregates(self) -> None:
        """Recalculate total_score, average_score, and final_grade from items."""
        if not self.items:
            self.total_score = 0
            self.average_score = 0.0
            self.final_grade = None
            return
        
        # Calculate totals
        self.total_score = sum(item.score for item in self.items)
        self.average_score = self.total_score / len(self.items)
        
        # Determine final grade based on average
        if self.average_score >= 3.5:
            self.final_grade = EvaluationGrade.A
        elif self.average_score >= 2.5:
            self.final_grade = EvaluationGrade.B
        elif self.average_score >= 1.5:
            self.final_grade = EvaluationGrade.C
        else:
            self.final_grade = EvaluationGrade.D
        
        self.last_updated = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
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