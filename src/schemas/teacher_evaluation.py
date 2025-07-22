"""Teacher Evaluation schemas for refactored parent-child structure."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from .shared import BaseResponse, PaginationParams
from .user import UserResponse
from .evaluation_aspect import EvaluationAspectResponse
from .period import PeriodResponse
from ..models.enums import EvaluationGrade


# Base schemas for parent evaluation
class TeacherEvaluationBase(BaseModel):
    """Base teacher evaluation schema for parent record."""
    teacher_id: int = Field(..., description="ID of teacher being evaluated")
    evaluator_id: int = Field(..., description="ID of evaluator")
    period_id: int = Field(..., description="ID of evaluation period")
    final_notes: Optional[str] = Field(None, max_length=1000, description="Final evaluation summary notes")


# Base schemas for evaluation items
class TeacherEvaluationItemBase(BaseModel):
    """Base teacher evaluation item schema for individual aspects."""
    aspect_id: int = Field(..., description="ID of evaluation aspect")
    grade: EvaluationGrade = Field(..., description="Evaluation grade (A, B, C, D)")
    notes: Optional[str] = Field(None, max_length=500, description="Notes for this specific aspect")


# Create schemas
class TeacherEvaluationCreate(TeacherEvaluationBase):
    """Schema for creating parent teacher evaluation record."""
    pass


class TeacherEvaluationItemCreate(TeacherEvaluationItemBase):
    """Schema for creating individual evaluation item."""
    pass


class TeacherEvaluationWithItemsCreate(TeacherEvaluationBase):
    """Schema for creating evaluation with multiple aspects at once."""
    items: List[TeacherEvaluationItemCreate] = Field(..., description="List of aspect evaluations")


# Update schemas
class TeacherEvaluationUpdate(BaseModel):
    """Schema for updating parent teacher evaluation."""
    final_notes: Optional[str] = Field(None, max_length=1000, description="Updated final notes")


class TeacherEvaluationItemUpdate(BaseModel):
    """Schema for updating individual evaluation item."""
    grade: Optional[EvaluationGrade] = Field(None, description="Updated evaluation grade")
    notes: Optional[str] = Field(None, max_length=500, description="Updated aspect notes")


class TeacherEvaluationBulkItemUpdate(BaseModel):
    """Schema for bulk updating multiple aspect evaluations."""
    item_updates: List[dict] = Field(
        ..., 
        description="List of {aspect_id: int, grade: EvaluationGrade, notes: str} updates"
    )


# Response schemas
class TeacherEvaluationItemResponse(BaseResponse):
    """Schema for teacher evaluation item response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    teacher_evaluation_id: int
    aspect_id: int
    grade: EvaluationGrade
    score: int
    notes: Optional[str]
    evaluated_at: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relationships
    aspect: Optional[EvaluationAspectResponse] = None


class TeacherEvaluationResponse(BaseResponse):
    """Schema for parent teacher evaluation response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    teacher_id: int
    evaluator_id: int
    period_id: int
    total_score: int
    average_score: float
    final_grade: float
    final_notes: Optional[str]
    last_updated: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    organization_name: Optional[str] = None
    
    # Relationships
    teacher: Optional[UserResponse] = None
    evaluator: Optional[UserResponse] = None
    period: Optional[PeriodResponse] = None
    items: List[TeacherEvaluationItemResponse] = Field(default_factory=list)


class TeacherEvaluationSummary(BaseModel):
    """Summary schema for teacher evaluation performance across periods."""
    model_config = ConfigDict(from_attributes=True)
    
    teacher_id: int
    teacher_name: str
    period_id: int
    total_aspects: int
    completed_aspects: int
    total_score: int
    average_score: float
    final_grade: float
    completion_percentage: float
    last_updated: Optional[datetime] = None


class PeriodEvaluationStats(BaseModel):
    """Statistics for evaluations in a period."""
    model_config = ConfigDict(from_attributes=True)
    
    period_id: int
    total_evaluations: int
    total_teachers: int
    completed_evaluations: int
    total_aspects_evaluated: int
    average_score: float
    final_grade_distribution: dict  # {"A": count, "B": count, "C": count, "D": count}
    completion_percentage: float
    top_performers: List[dict]  # Top teachers by final grade and average, includes total_score and organization_name
    aspect_performance: List[dict]  # Average performance by aspect


# Filter and request schemas
class TeacherEvaluationFilterParams(PaginationParams):
    """Filter parameters for teacher evaluation queries."""
    teacher_id: Optional[int] = Field(None, description="Filter by teacher ID")
    evaluator_id: Optional[int] = Field(None, description="Filter by evaluator ID")
    period_id: Optional[int] = Field(None, description="Filter by period ID")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search by teacher name")
    final_grade: Optional[float] = Field(None, description="Filter by final grade")
    min_average_score: Optional[float] = Field(None, ge=1.0, le=4.0, description="Minimum average score")
    max_average_score: Optional[float] = Field(None, ge=1.0, le=4.0, description="Maximum average score")
    has_final_notes: Optional[bool] = Field(None, description="Filter by presence of final notes")
    from_date: Optional[datetime] = Field(None, description="Filter from last updated date")
    to_date: Optional[datetime] = Field(None, description="Filter to last updated date")


class AssignTeachersToEvaluationPeriod(BaseModel):
    """Schema for assigning teachers to evaluation period."""
    period_id: int = Field(..., description="Period to assign teachers to")


class AssignTeachersToEvaluationPeriodResponse(BaseModel):
    """Schema for response when assigning teachers to evaluation period."""
    success: bool = Field(..., description="Whether the assignment was successful")
    message: str = Field(..., description="Summary message")
    period_id: int = Field(..., description="Period ID for which evaluations were created")
    period_name: str = Field(..., description="Period name")
    created_evaluations: int = Field(..., description="Number of new evaluations created")
    skipped_evaluations: int = Field(..., description="Number of evaluations skipped (already exist)")
    total_teachers: int = Field(..., description="Total number of eligible teachers")
    total_evaluation_items: int = Field(..., description="Total number of evaluation items created")
    active_aspects_count: int = Field(..., description="Number of active evaluation aspects")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully created evaluations for 25 teachers with 12 aspects each",
                "period_id": 5,
                "period_name": "Semester 1 - 2024/2025", 
                "created_evaluations": 25,
                "skipped_evaluations": 0,
                "total_teachers": 25,
                "total_evaluation_items": 300,
                "active_aspects_count": 12
            }
        }


# Individual update schemas
class UpdateEvaluationItemGrade(BaseModel):
    """Schema for updating individual aspect evaluation grade."""
    grade: EvaluationGrade = Field(..., description="New evaluation grade")
    notes: Optional[str] = Field(None, max_length=500, description="Notes for this aspect")


class UpdateEvaluationFinalNotes(BaseModel):
    """Schema for updating final evaluation notes."""
    final_notes: Optional[str] = Field(None, max_length=1000, description="Final evaluation summary")