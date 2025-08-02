"""Teacher Evaluation Item model for individual aspect evaluations."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint, Column
from sqlalchemy import Enum as SQLAlchemyEnum, Integer, ForeignKey
from pydantic import validator

from .base import BaseModel
from .enums import EvaluationGrade
from ..utils.sanitize_html import sanitize_html_content

if TYPE_CHECKING:
    from .teacher_evaluation import TeacherEvaluation
    from .evaluation_aspect import EvaluationAspect


class TeacherEvaluationItem(BaseModel, SQLModel, table=True):
    """Individual aspect evaluation within a teacher evaluation."""
    
    __tablename__ = "teacher_evaluation_items"
    __table_args__ = (
        UniqueConstraint('teacher_evaluation_id', 'aspect_id', name='uq_teacher_evaluation_aspect'),
        {"sqlite_autoincrement": True}
    )
    
    id: int = Field(primary_key=True)
    teacher_evaluation_id: int = Field(
        description="Reference to parent teacher evaluation",
        sa_column=Column(
            Integer, 
            ForeignKey("teacher_evaluations.id", ondelete="CASCADE"), 
            nullable=False,
            index=True
        )
    )
    aspect_id: int = Field(
        foreign_key="evaluation_aspects.id", 
        nullable=False, 
        index=True,
        description="Evaluation aspect being assessed"
    )
    
    # Grade-based scoring (A=4, B=3, C=2, D=1)
    grade: EvaluationGrade = Field(
        sa_column=Column(SQLAlchemyEnum(EvaluationGrade, name="evaluation_grade"), nullable=False)
    )
    
    # Computed score based on grade (stored for performance)
    score: int = Field(nullable=False)
    
    notes: Optional[str] = Field(default=None, max_length=500, description="Notes for this specific aspect")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow, description="When this aspect was evaluated")
    
    # Relationships
    teacher_evaluation: "TeacherEvaluation" = Relationship(
        back_populates="items"
    )
    aspect: "EvaluationAspect" = Relationship(
        back_populates="teacher_evaluation_items"
    )
    
    def __repr__(self) -> str:
        return f"<TeacherEvaluationItem(id={self.id}, teacher_evaluation_id={self.teacher_evaluation_id}, aspect_id={self.aspect_id}, grade={self.grade})>"
    
    def __init__(self, **data):
        """Initialize with auto-calculated score from grade."""
        if "grade" in data and "score" not in data:
            data["score"] = EvaluationGrade.get_score(data["grade"])
        super().__init__(**data)
    
    @validator('notes')
    def sanitize_notes(cls, v):
        """Sanitize HTML content in notes field."""
        if v:
            return sanitize_html_content(v)
        return v
    
    @property
    def grade_description(self) -> str:
        """Get description for the grade."""
        return EvaluationGrade.get_description(self.grade)
    
    def update_grade(self, new_grade: EvaluationGrade, notes: Optional[str] = None) -> None:
        """Update the evaluation grade and auto-calculate score."""
        self.grade = new_grade
        self.score = EvaluationGrade.get_score(new_grade)
        if notes is not None:
            self.notes = notes
        self.evaluated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()