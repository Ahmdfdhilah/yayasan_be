"""Evaluation Result model for PKG System."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel
from .enums import EvaluationGrade

if TYPE_CHECKING:
    from .user import User


class EvaluationResult(BaseModel, SQLModel, table=True):
    """Evaluation result model for consolidated teacher performance."""
    
    __tablename__ = "evaluation_results"
    
    id: int = Field(primary_key=True)
    teacher_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    evaluator_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    
    # Academic period
    academic_year: str = Field(max_length=20, nullable=False, index=True)
    semester: str = Field(max_length=20, nullable=False, index=True)
    
    # Calculated scores
    total_score: int = Field(nullable=False)
    max_score: int = Field(nullable=False)
    performance_value: Decimal = Field(nullable=False, max_digits=5, decimal_places=2)
    grade_category: str = Field(max_length=50, nullable=False, index=True)
    
    # Additional information
    recommendations: Optional[str] = Field(default=None)
    evaluation_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships - with explicit foreign_keys for SQLAlchemy
    teacher: "User" = Relationship(
        back_populates="evaluation_results_received",
        sa_relationship_kwargs={"foreign_keys": "EvaluationResult.teacher_id"}
    )
    evaluator: "User" = Relationship(
        back_populates="evaluation_results_given",
        sa_relationship_kwargs={"foreign_keys": "EvaluationResult.evaluator_id"}
    )
    
    # Unique constraint defined at table level
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<EvaluationResult(id={self.id}, teacher_id={self.teacher_id}, grade={self.grade_category})>"
    
    @property
    def academic_period(self) -> str:
        """Get formatted academic period."""
        return f"{self.academic_year} - {self.semester}"
    
    @property
    def score_percentage(self) -> Decimal:
        """Get score as percentage."""
        if self.max_score == 0:
            return Decimal("0.00")
        return (Decimal(str(self.total_score)) / Decimal(str(self.max_score))) * Decimal("100")
    
    @property
    def performance_percentage(self) -> Decimal:
        """Get performance value as percentage (already calculated with 1.25 multiplier)."""
        return self.performance_value
    
    def calculate_grade_category(self) -> str:
        """Calculate grade category based on performance value."""
        if self.performance_value >= Decimal("90.00"):
            return EvaluationGrade.EXCELLENT.value
        elif self.performance_value >= Decimal("80.00"):
            return EvaluationGrade.GOOD.value
        elif self.performance_value >= Decimal("70.00"):
            return EvaluationGrade.SATISFACTORY.value
        else:
            return EvaluationGrade.NEEDS_IMPROVEMENT.value
    
    def update_grade_category(self) -> None:
        """Update grade category based on current performance value."""
        self.grade_category = self.calculate_grade_category()
    
    @classmethod
    def create_from_evaluations(
        cls,
        teacher_id: int,
        evaluator_id: int,
        academic_year: str,
        semester: str,
        total_score: int,
        max_score: int,
        recommendations: Optional[str] = None
    ) -> "EvaluationResult":
        """Create evaluation result from evaluation data."""
        # Calculate performance value (total score * 1.25 as per business rules)
        performance_value = Decimal(str(total_score)) * Decimal("1.25")
        
        # Create instance
        result = cls(
            teacher_id=teacher_id,
            evaluator_id=evaluator_id,
            academic_year=academic_year,
            semester=semester,
            total_score=total_score,
            max_score=max_score,
            performance_value=performance_value,
            grade_category="",  # Will be calculated
            recommendations=recommendations
        )
        
        # Calculate and set grade category
        result.update_grade_category()
        
        return result
    
    def update_scores(self, total_score: int, max_score: int) -> None:
        """Update scores and recalculate performance metrics."""
        self.total_score = total_score
        self.max_score = max_score
        self.performance_value = Decimal(str(total_score)) * Decimal("1.25")
        self.update_grade_category()
        self.evaluation_date = datetime.utcnow()
    
    def add_recommendations(self, recommendations: str) -> None:
        """Add or update recommendations."""
        self.recommendations = recommendations
    
    def get_grade_description(self) -> str:
        """Get detailed description for the grade category."""
        descriptions = {
            EvaluationGrade.EXCELLENT.value: "Excellent performance - Exceeds expectations in all areas",
            EvaluationGrade.GOOD.value: "Good performance - Meets and sometimes exceeds expectations",
            EvaluationGrade.SATISFACTORY.value: "Satisfactory performance - Meets basic expectations",
            EvaluationGrade.NEEDS_IMPROVEMENT.value: "Needs improvement - Below expectations, requires development"
        }
        return descriptions.get(self.grade_category, "Unknown grade category")