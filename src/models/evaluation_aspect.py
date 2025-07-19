"""Evaluation Aspect model for PKG System."""

from typing import List, Optional, TYPE_CHECKING
from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .teacher_evaluation import TeacherEvaluation


class EvaluationAspect(BaseModel, SQLModel, table=True):
    """Evaluation aspect model for teacher performance assessments (Universal across all organizations)."""
    
    __tablename__ = "evaluation_aspects"
    
    id: int = Field(primary_key=True)
    aspect_name: str = Field(max_length=255, nullable=False, index=True)
    category: str = Field(max_length=100, nullable=False, index=True)
    description: Optional[str] = Field(default=None)
    
    # Scoring configuration
    weight: Decimal = Field(default=Decimal("1.00"), max_digits=5, decimal_places=2)
    min_score: int = Field(default=1)
    max_score: int = Field(default=4)
    
    # Status (Universal - no organization filtering)
    is_active: bool = Field(default=True, index=True)
    
    # Relationships
    teacher_evaluations: List["TeacherEvaluation"] = Relationship(back_populates="aspect")
    
    def __repr__(self) -> str:
        return f"<EvaluationAspect(id={self.id}, name={self.aspect_name}, category={self.category})>"
    
    @property
    def score_range(self) -> str:
        """Get score range as string."""
        return f"{self.min_score}-{self.max_score}"
    
    def is_score_valid(self, score: int) -> bool:
        """Check if score is within valid range."""
        return self.min_score <= score <= self.max_score
    
    def calculate_weighted_score(self, score: int) -> Decimal:
        """Calculate weighted score for this aspect."""
        if not self.is_score_valid(score):
            raise ValueError(f"Score {score} is not within valid range {self.score_range}")
        return Decimal(str(score)) * self.weight
    
    def get_score_description(self, score: int) -> str:
        """Get description for score value."""
        if not self.is_score_valid(score):
            return "Invalid Score"
        
        # Standard 4-point scale descriptions
        descriptions = {
            1: "Needs Improvement",
            2: "Developing", 
            3: "Proficient",
            4: "Exemplary"
        }
        
        # Adjust for custom ranges
        if self.max_score == 4:
            return descriptions.get(score, "Unknown")
        else:
            # For custom ranges, calculate equivalent
            percentage = (score - self.min_score) / (self.max_score - self.min_score)
            if percentage <= 0.25:
                return "Needs Improvement"
            elif percentage <= 0.50:
                return "Developing"
            elif percentage <= 0.75:
                return "Proficient"
            else:
                return "Exemplary"
    
    def activate(self) -> None:
        """Activate this evaluation aspect."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate this evaluation aspect."""
        self.is_active = False