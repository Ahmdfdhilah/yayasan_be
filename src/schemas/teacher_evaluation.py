"""Teacher Evaluation schemas for PKG System API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal

from src.schemas.shared import BaseListResponse
from src.schemas.filters import PaginationParams, SearchParams, DateRangeFilter


# ===== BASE SCHEMAS =====

class TeacherEvaluationBase(BaseModel):
    """Base teacher evaluation schema."""
    teacher_id: int = Field(..., description="Teacher user ID being evaluated")
    aspect_id: int = Field(..., description="Evaluation aspect ID")
    academic_year: str = Field(..., min_length=1, max_length=20, description="Academic year")
    semester: str = Field(..., min_length=1, max_length=20, description="Semester")
    score: int = Field(..., ge=0, description="Score given for this aspect")
    notes: Optional[str] = Field(None, description="Evaluation notes or comments")
    
    @field_validator('academic_year')
    @classmethod
    def validate_academic_year(cls, year: str) -> str:
        """Validate academic year format."""
        return year.strip()
    
    @field_validator('semester')
    @classmethod
    def validate_semester(cls, semester: str) -> str:
        """Validate semester format."""
        return semester.strip()


# ===== REQUEST SCHEMAS =====

class TeacherEvaluationCreate(TeacherEvaluationBase):
    """Schema for creating a teacher evaluation."""
    evaluator_id: int = Field(..., description="Evaluator user ID")


class TeacherEvaluationUpdate(BaseModel):
    """Schema for updating a teacher evaluation."""
    score: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class TeacherEvaluationBulkCreate(BaseModel):
    """Schema for bulk creating teacher evaluations."""
    evaluator_id: int = Field(..., description="Evaluator user ID")
    teacher_id: int = Field(..., description="Teacher user ID")
    academic_year: str = Field(..., description="Academic year")
    semester: str = Field(..., description="Semester")
    evaluations: List[Dict[str, Any]] = Field(..., min_items=1, description="List of aspect evaluations")
    
    @field_validator('evaluations')
    @classmethod
    def validate_evaluations(cls, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate evaluation data structure."""
        required_fields = {'aspect_id', 'score'}
        for eval_data in evaluations:
            if not all(field in eval_data for field in required_fields):
                raise ValueError(f"Each evaluation must contain: {required_fields}")
            if not isinstance(eval_data['score'], int) or eval_data['score'] < 0:
                raise ValueError("Score must be a non-negative integer")
        return evaluations


# ===== RESPONSE SCHEMAS =====

class TeacherEvaluationResponse(BaseModel):
    """Schema for teacher evaluation response."""
    id: int
    evaluator_id: int
    teacher_id: int
    aspect_id: int
    academic_year: str
    semester: str
    score: int
    notes: Optional[str] = None
    evaluation_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    academic_period: str = Field(..., description="Formatted academic period")
    weighted_score: Decimal = Field(..., description="Score weighted by aspect weight")
    score_description: str = Field(..., description="Description of the score level")
    
    # Related data
    evaluator_name: Optional[str] = Field(None, description="Evaluator name")
    teacher_name: Optional[str] = Field(None, description="Teacher name")
    teacher_email: Optional[str] = Field(None, description="Teacher email")
    aspect_name: Optional[str] = Field(None, description="Evaluation aspect name")
    aspect_max_score: Optional[int] = Field(None, description="Maximum possible score for aspect")
    aspect_weight: Optional[Decimal] = Field(None, description="Aspect weight percentage")
    
    @classmethod
    def from_teacher_evaluation_model(cls, evaluation, include_relations: bool = False) -> "TeacherEvaluationResponse":
        """Create TeacherEvaluationResponse from TeacherEvaluation model."""
        data = {
            "id": evaluation.id,
            "evaluator_id": evaluation.evaluator_id,
            "teacher_id": evaluation.teacher_id,
            "aspect_id": evaluation.aspect_id,
            "academic_year": evaluation.academic_year,
            "semester": evaluation.semester,
            "score": evaluation.score,
            "notes": evaluation.notes,
            "evaluation_date": evaluation.evaluation_date,
            "created_at": evaluation.created_at,
            "updated_at": evaluation.updated_at,
            "academic_period": evaluation.academic_period,
            "weighted_score": Decimal(str(evaluation.get_weighted_score())),
            "score_description": evaluation.get_score_description()
        }
        
        if include_relations:
            data.update({
                "evaluator_name": evaluation.evaluator.display_name if hasattr(evaluation, 'evaluator') and evaluation.evaluator else None,
                "teacher_name": evaluation.teacher.display_name if hasattr(evaluation, 'teacher') and evaluation.teacher else None,
                "teacher_email": evaluation.teacher.email if hasattr(evaluation, 'teacher') and evaluation.teacher else None,
                "aspect_name": evaluation.aspect.aspect_name if hasattr(evaluation, 'aspect') and evaluation.aspect else None,
                "aspect_max_score": evaluation.aspect.max_score if hasattr(evaluation, 'aspect') and evaluation.aspect else None,
                "aspect_weight": evaluation.aspect.weight if hasattr(evaluation, 'aspect') and evaluation.aspect else None
            })
        
        return cls(**data)
    
    model_config = {"from_attributes": True}


class TeacherEvaluationListResponse(BaseListResponse[TeacherEvaluationResponse]):
    """Standardized teacher evaluation list response."""
    pass


class TeacherEvaluationSummary(BaseModel):
    """Schema for teacher evaluation summary (lighter response)."""
    id: int
    teacher_id: int
    aspect_id: int
    academic_year: str
    semester: str
    score: int
    evaluation_date: datetime
    
    # Related data
    teacher_name: Optional[str] = None
    aspect_name: Optional[str] = None
    
    @classmethod
    def from_teacher_evaluation_model(cls, evaluation) -> "TeacherEvaluationSummary":
        """Create TeacherEvaluationSummary from TeacherEvaluation model."""
        return cls(
            id=evaluation.id,
            teacher_id=evaluation.teacher_id,
            aspect_id=evaluation.aspect_id,
            academic_year=evaluation.academic_year,
            semester=evaluation.semester,
            score=evaluation.score,
            evaluation_date=evaluation.evaluation_date,
            teacher_name=evaluation.teacher.display_name if hasattr(evaluation, 'teacher') and evaluation.teacher else None,
            aspect_name=evaluation.aspect.aspect_name if hasattr(evaluation, 'aspect') and evaluation.aspect else None
        )
    
    model_config = {"from_attributes": True}


# ===== FILTER SCHEMAS =====

class TeacherEvaluationFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for teacher evaluation listing."""
    
    # Evaluation-specific filters
    evaluator_id: Optional[int] = Field(None, description="Filter by evaluator ID")
    teacher_id: Optional[int] = Field(None, description="Filter by teacher ID")
    aspect_id: Optional[int] = Field(None, description="Filter by evaluation aspect ID")
    academic_year: Optional[str] = Field(None, description="Filter by academic year")
    semester: Optional[str] = Field(None, description="Filter by semester")
    min_score: Optional[int] = Field(None, ge=0, description="Minimum score")
    max_score: Optional[int] = Field(None, description="Maximum score")
    has_notes: Optional[bool] = Field(None, description="Filter evaluations with/without notes")
    
    # Date filters
    evaluated_after: Optional[datetime] = Field(None, description="Filter evaluations after this date")
    evaluated_before: Optional[datetime] = Field(None, description="Filter evaluations before this date")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in teacher name, aspect name, or notes")
    
    # Override default sort
    sort_by: str = Field(default="evaluation_date", description="Sort field")


# ===== BULK OPERATIONS =====

class TeacherEvaluationBulkUpdate(BaseModel):
    """Schema for bulk teacher evaluation updates."""
    evaluation_ids: List[int] = Field(..., min_items=1, description="List of evaluation IDs to update")
    score: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class TeacherEvaluationBulkDelete(BaseModel):
    """Schema for bulk teacher evaluation deletion."""
    evaluation_ids: List[int] = Field(..., min_items=1, description="List of evaluation IDs to delete")
    force_delete: bool = Field(default=False, description="Force delete evaluations")


# ===== AGGREGATED EVALUATION SCHEMAS =====

class TeacherEvaluationAggregated(BaseModel):
    """Schema for aggregated teacher evaluation results."""
    teacher_id: int
    teacher_name: str
    teacher_email: str
    academic_year: str
    semester: str
    total_score: int
    max_possible_score: int
    weighted_total: Decimal
    performance_percentage: Decimal
    grade_category: str
    aspect_scores: List[Dict[str, Any]] = Field(description="Individual aspect scores")
    evaluator_name: Optional[str] = None
    evaluation_date: datetime
    
    # Computed metrics
    score_breakdown: Dict[str, Any] = Field(description="Detailed score breakdown")
    strengths: List[str] = Field(description="Areas of strength")
    improvements: List[str] = Field(description="Areas for improvement")


class EvaluationPeriodSummary(BaseModel):
    """Schema for evaluation period summary."""
    academic_year: str
    semester: str
    total_teachers: int
    evaluated_teachers: int
    pending_evaluations: int
    completion_rate: Decimal
    avg_performance_score: Decimal
    grade_distribution: Dict[str, int] = Field(description="Distribution of grades")
    top_performers: List[Dict[str, Any]] = Field(description="Top performing teachers")
    needs_improvement: List[Dict[str, Any]] = Field(description="Teachers needing improvement")


# ===== ANALYTICS SCHEMAS =====

class TeacherEvaluationAnalytics(BaseModel):
    """Schema for teacher evaluation analytics."""
    total_evaluations: int
    unique_teachers: int
    unique_evaluators: int
    avg_score_overall: Decimal
    score_distribution: Dict[str, int] = Field(description="Score distribution histogram")
    evaluations_by_period: Dict[str, int] = Field(description="Evaluations per academic period")
    evaluations_by_aspect: Dict[str, int] = Field(description="Evaluations per aspect")
    evaluator_activity: Dict[str, int] = Field(description="Evaluations per evaluator")
    recent_trends: Dict[str, List[int]] = Field(description="Recent evaluation trends")


class TeacherPerformanceReport(BaseModel):
    """Schema for individual teacher performance report."""
    teacher_id: int
    teacher_name: str
    teacher_email: str
    evaluation_history: List[TeacherEvaluationAggregated]
    performance_trends: Dict[str, List[Decimal]] = Field(description="Performance trends over time")
    aspect_strengths: List[str] = Field(description="Consistent strengths")
    aspect_weaknesses: List[str] = Field(description="Areas consistently needing improvement")
    improvement_trajectory: str = Field(description="Overall improvement trajectory")
    recommendations: List[str] = Field(description="Personalized recommendations")


class EvaluationSystemStats(BaseModel):
    """Schema for comprehensive evaluation system statistics."""
    overview: TeacherEvaluationAnalytics
    period_summaries: List[EvaluationPeriodSummary]
    teacher_reports: List[TeacherPerformanceReport]
    system_health: Dict[str, Any] = Field(description="System health metrics")
    usage_patterns: Dict[str, Any] = Field(description="System usage patterns")