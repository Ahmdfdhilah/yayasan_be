"""Teacher Evaluation model for PKG System - Refactored."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import Enum as SQLAlchemyEnum

from .base import BaseModel
from .enums import EvaluationGrade

if TYPE_CHECKING:
    from .user import User
    from .evaluation_aspect import EvaluationAspect
    from .period import Period


class TeacherEvaluation(BaseModel, SQLModel, table=True):
    """Refactored teacher evaluation model with grade-based scoring."""
    
    __tablename__ = "teacher_evaluations"
    
    id: int = Field(primary_key=True)
    teacher_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    evaluator_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    aspect_id: int = Field(foreign_key="evaluation_aspects.id", nullable=False, index=True)
    period_id: int = Field(foreign_key="periods.id", nullable=False, index=True)
    
    # Grade-based scoring (A=4, B=3, C=2, D=1)
    grade: EvaluationGrade = Field(
        sa_column=Column(SQLAlchemyEnum(EvaluationGrade, name="evaluation_grade"), nullable=False)
    )
    
    # Computed score based on grade (stored for performance)
    score: int = Field(nullable=False)
    
    notes: Optional[str] = Field(default=None)
    evaluation_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships - with explicit foreign_keys for SQLAlchemy
    evaluator: "User" = Relationship(
        back_populates="conducted_evaluations",
        sa_relationship_kwargs={"foreign_keys": "TeacherEvaluation.evaluator_id"}
    )
    teacher: "User" = Relationship(
        back_populates="received_evaluations",
        sa_relationship_kwargs={"foreign_keys": "TeacherEvaluation.teacher_id"}
    )
    aspect: "EvaluationAspect" = Relationship(back_populates="teacher_evaluations")
    period: "Period" = Relationship(back_populates="teacher_evaluations")
    
    # Unique constraint: one evaluation per teacher-aspect-period combination
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<TeacherEvaluation(id={self.id}, teacher_id={self.teacher_id}, aspect_id={self.aspect_id}, grade={self.grade})>"
    
    def __init__(self, **data):
        """Initialize with auto-calculated score from grade."""
        if "grade" in data and "score" not in data:
            data["score"] = EvaluationGrade.get_score(data["grade"])
        super().__init__(**data)
    
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
        self.evaluation_date = datetime.utcnow()
    
    def add_notes(self, notes: str) -> None:
        """Add or update evaluation notes."""
        self.notes = notes