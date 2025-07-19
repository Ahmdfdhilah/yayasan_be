"""Teacher Evaluation schemas for PKG System API endpoints - Refactored for grade-based system."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from src.schemas.shared import BaseListResponse
from src.schemas.filters import PaginationParams, SearchParams, DateRangeFilter
from src.models.enums import EvaluationGrade


# ===== BASE SCHEMAS =====

class TeacherEvaluationBase(BaseModel):
    """Base teacher evaluation schema - grade-based system."""
    teacher_id: int = Field(..., description="Teacher user ID being evaluated")
    aspect_id: int = Field(..., description="Evaluation aspect ID")
    period_id: int = Field(..., description="Period ID for this evaluation")
    grade: EvaluationGrade = Field(..., description="Grade (A, B, C, D)")
    notes: Optional[str] = Field(None, description="Evaluation notes or comments")


# ===== REQUEST SCHEMAS =====

class TeacherEvaluationCreate(TeacherEvaluationBase):
    """Schema for creating a teacher evaluation."""
    evaluator_id: int = Field(..., description="Evaluator user ID")


class TeacherEvaluationUpdate(BaseModel):
    """Schema for updating a teacher evaluation."""
    grade: Optional[EvaluationGrade] = None
    notes: Optional[str] = None


class TeacherEvaluationBulkCreate(BaseModel):
    """Schema for bulk creating teacher evaluations."""
    evaluator_id: int = Field(..., description="Evaluator user ID")
    teacher_id: int = Field(..., description="Teacher user ID")
    period_id: int = Field(..., description="Period ID")
    evaluations: List[Dict[str, Any]] = Field(..., min_items=1, description="List of aspect evaluations")
    
    @field_validator('evaluations')
    @classmethod
    def validate_evaluations(cls, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate evaluation data structure."""
        required_fields = {'aspect_id', 'grade'}
        for eval_data in evaluations:
            if not all(field in eval_data for field in required_fields):
                raise ValueError(f"Each evaluation must contain: {required_fields}")
            # Validate grade is valid
            if eval_data['grade'] not in [grade.value for grade in EvaluationGrade]:
                raise ValueError(f"Grade must be one of: {[grade.value for grade in EvaluationGrade]}")
        return evaluations


class TeacherEvaluationBulkUpdate(BaseModel):
    """Schema for bulk updating teacher evaluation grades."""
    evaluations: List[Dict[str, Any]] = Field(..., min_items=1, description="List of evaluation updates")
    
    @field_validator('evaluations')
    @classmethod
    def validate_evaluations(cls, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate evaluation update data structure."""
        required_fields = {'evaluation_id', 'grade'}
        for eval_data in evaluations:
            if not all(field in eval_data for field in required_fields):
                raise ValueError(f"Each evaluation update must contain: {required_fields}")
            # Validate grade is valid
            if eval_data['grade'] not in [grade.value for grade in EvaluationGrade]:
                raise ValueError(f"Grade must be one of: {[grade.value for grade in EvaluationGrade]}")
        return evaluations


class AssignTeachersToPerio(BaseModel):
    """Schema for assigning teachers to evaluation period."""
    period_id: int = Field(..., description="Period ID")
    teacher_ids: Optional[List[int]] = Field(None, description="Specific teacher IDs (if None, assign all teachers)")
    aspect_ids: Optional[List[int]] = Field(None, description="Specific aspect IDs (if None, assign all active aspects)")


class CompleteTeacherEvaluation(BaseModel):
    """Schema for completing all evaluations for a teacher in a period."""
    teacher_id: int = Field(..., description="Teacher ID")
    period_id: int = Field(..., description="Period ID")
    evaluations: Dict[int, EvaluationGrade] = Field(..., description="Aspect ID to grade mapping")


# ===== RESPONSE SCHEMAS =====

class TeacherEvaluationResponse(BaseModel):
    """Schema for teacher evaluation response - grade-based."""
    id: int
    evaluator_id: int
    teacher_id: int
    aspect_id: int
    period_id: int
    grade: EvaluationGrade
    score: int = Field(description="Computed score from grade (A=4, B=3, C=2, D=1)")
    notes: Optional[str] = None
    evaluation_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    grade_description: str = Field(..., description="Description of the grade")
    
    # Related data
    evaluator_name: Optional[str] = Field(None, description="Evaluator name")
    teacher_name: Optional[str] = Field(None, description="Teacher name")
    teacher_email: Optional[str] = Field(None, description="Teacher email")
    aspect_name: Optional[str] = Field(None, description="Evaluation aspect name")
    aspect_category: Optional[str] = Field(None, description="Aspect category")
    period_name: Optional[str] = Field(None, description="Period name")
    
    @classmethod
    def from_teacher_evaluation_model(cls, evaluation, include_relations: bool = False) -> "TeacherEvaluationResponse":
        """Create TeacherEvaluationResponse from TeacherEvaluation model."""
        data = {
            "id": evaluation.id,
            "evaluator_id": evaluation.evaluator_id,
            "teacher_id": evaluation.teacher_id,
            "aspect_id": evaluation.aspect_id,
            "period_id": evaluation.period_id,
            "grade": evaluation.grade,
            "score": evaluation.score,
            "notes": evaluation.notes,
            "evaluation_date": evaluation.evaluation_date,
            "created_at": evaluation.created_at,
            "updated_at": evaluation.updated_at,
            "grade_description": evaluation.grade_description,
        }
        
        if include_relations:
            # These would be populated by joins in the repository/service layer
            data.update({
                "evaluator_name": getattr(evaluation.evaluator, 'profile', {}).get('full_name') if hasattr(evaluation, 'evaluator') and evaluation.evaluator else None,
                "teacher_name": getattr(evaluation.teacher, 'profile', {}).get('full_name') if hasattr(evaluation, 'teacher') and evaluation.teacher else None,
                "teacher_email": getattr(evaluation.teacher, 'email') if hasattr(evaluation, 'teacher') and evaluation.teacher else None,
                "aspect_name": getattr(evaluation.aspect, 'aspect_name') if hasattr(evaluation, 'aspect') and evaluation.aspect else None,
                "aspect_category": getattr(evaluation.aspect, 'category') if hasattr(evaluation, 'aspect') and evaluation.aspect else None,
                "period_name": getattr(evaluation.period, 'period_name') if hasattr(evaluation, 'period') and evaluation.period else None,
            })
        
        return cls(**data)
    
    model_config = {"from_attributes": True}


class TeacherEvaluationListResponse(BaseListResponse[TeacherEvaluationResponse]):
    """Standardized teacher evaluation list response."""
    pass


class TeacherEvaluationSummary(BaseModel):
    """Schema for teacher evaluation summary."""
    teacher_id: int
    teacher_name: str
    teacher_email: str
    period_id: int
    period_name: str
    total_aspects: int
    completed_evaluations: int
    average_score: float = Field(description="Average score across all aspects")
    grade_distribution: Dict[str, int] = Field(description="Count of each grade (A, B, C, D)")
    completion_percentage: float = Field(description="Percentage of aspects evaluated")
    
    model_config = {"from_attributes": True}


class PeriodEvaluationStats(BaseModel):
    """Schema for period evaluation statistics."""
    period_id: int
    period_name: str
    total_teachers: int
    total_aspects: int
    total_possible_evaluations: int
    completed_evaluations: int
    completion_percentage: float
    average_score: float
    grade_distribution: Dict[str, int]
    teacher_summaries: List[TeacherEvaluationSummary]


# ===== FILTER SCHEMAS =====

class TeacherEvaluationFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for teacher evaluation listing."""
    
    # Evaluation-specific filters
    teacher_id: Optional[int] = Field(None, description="Filter by teacher ID")
    evaluator_id: Optional[int] = Field(None, description="Filter by evaluator ID")
    aspect_id: Optional[int] = Field(None, description="Filter by aspect ID")
    period_id: Optional[int] = Field(None, description="Filter by period ID")
    grade: Optional[EvaluationGrade] = Field(None, description="Filter by grade")
    min_score: Optional[int] = Field(None, ge=1, le=4, description="Minimum score")
    max_score: Optional[int] = Field(None, ge=1, le=4, description="Maximum score")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in notes or related names")
    
    # Override default sort
    sort_by: str = Field(default="evaluation_date", description="Sort field")


# ===== BULK OPERATIONS =====

class TeacherEvaluationBulkDelete(BaseModel):
    """Schema for bulk teacher evaluation deletion."""
    evaluation_ids: List[int] = Field(..., min_items=1, description="List of evaluation IDs to delete")


# ===== ANALYTICS SCHEMAS =====

class TeacherPerformanceAnalysis(BaseModel):
    """Schema for teacher performance analysis across periods."""
    teacher_id: int
    teacher_name: str
    periods_data: List[Dict[str, Any]] = Field(description="Performance data across periods")
    overall_average: float
    improvement_trend: str = Field(description="improving, declining, stable")
    strengths: List[str] = Field(description="Top performing aspects")
    areas_for_improvement: List[str] = Field(description="Aspects needing attention")


class AspectAnalytics(BaseModel):
    """Schema for aspect performance analytics."""
    aspect_id: int
    aspect_name: str
    total_evaluations: int
    average_grade: str
    grade_distribution: Dict[str, int]
    trend_analysis: Dict[str, Any]


class EvaluationSystemAnalytics(BaseModel):
    """Schema for comprehensive evaluation system analytics."""
    total_evaluations: int
    completion_rate: float
    average_performance: float
    grade_distribution: Dict[str, int]
    period_performance: List[Dict[str, Any]]
    teacher_performance: List[TeacherPerformanceAnalysis]
    aspect_performance: List[AspectAnalytics]
    recommendations: List[str]