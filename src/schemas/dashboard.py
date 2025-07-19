"""Dashboard schema definitions."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RPPStats(BaseModel):
    """RPP submission statistics."""
    total_submissions: int = Field(..., description="Total RPP submissions")
    pending_submissions: int = Field(..., description="Pending submissions")
    approved_submissions: int = Field(..., description="Approved submissions")
    rejected_submissions: int = Field(..., description="Rejected submissions")
    revision_needed: int = Field(..., description="Submissions needing revision")
    approval_rate: float = Field(..., description="Approval rate percentage")


class EvaluationStats(BaseModel):
    """Teacher evaluation statistics."""
    total_evaluations: int = Field(..., description="Total evaluations")
    completed_evaluations: int = Field(..., description="Completed evaluations")
    pending_evaluations: int = Field(..., description="Pending evaluations")
    average_score: float = Field(..., description="Average evaluation score")
    completion_rate: float = Field(..., description="Completion rate percentage")


class PerformanceStats(BaseModel):
    """Performance statistics."""
    total_teachers: int = Field(..., description="Total teachers")
    evaluated_teachers: int = Field(..., description="Evaluated teachers")
    top_performers: int = Field(..., description="Top performing teachers")
    need_improvement: int = Field(..., description="Teachers needing improvement")
    average_performance: float = Field(..., description="Average performance score")


class RecentActivity(BaseModel):
    """Recent activity item."""
    id: int = Field(..., description="Activity ID")
    type: str = Field(..., description="Activity type")
    description: str = Field(..., description="Activity description")
    user_name: str = Field(..., description="User who performed activity")
    timestamp: datetime = Field(..., description="Activity timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DashboardOverview(BaseModel):
    """Main dashboard overview."""
    user_info: Dict[str, Any] = Field(..., description="Current user information")
    rpp_stats: RPPStats = Field(..., description="RPP statistics")
    evaluation_stats: EvaluationStats = Field(..., description="Evaluation statistics")
    performance_stats: PerformanceStats = Field(..., description="Performance statistics")
    recent_activities: List[RecentActivity] = Field(..., description="Recent activities")
    pending_tasks: List[Dict[str, Any]] = Field(..., description="Pending tasks for user")
    academic_period: Dict[str, str] = Field(..., description="Current academic period")


class UserDashboard(BaseModel):
    """User-specific dashboard (guru perspective)."""
    user_info: Dict[str, Any] = Field(..., description="User information")
    my_rpp_submissions: List[Dict[str, Any]] = Field(..., description="User's RPP submissions")
    my_evaluations: List[Dict[str, Any]] = Field(..., description="User's evaluations")
    performance_summary: Dict[str, Any] = Field(..., description="Performance summary")
    improvement_areas: List[str] = Field(..., description="Areas for improvement")
    achievements: List[str] = Field(..., description="Notable achievements")
    upcoming_deadlines: List[Dict[str, Any]] = Field(..., description="Upcoming deadlines")


class OrganizationDashboard(BaseModel):
    """Organization dashboard (kepala sekolah perspective)."""
    organization_info: Dict[str, Any] = Field(..., description="Organization information")
    teacher_summary: Dict[str, Any] = Field(..., description="Teacher summary statistics")
    rpp_overview: RPPStats = Field(..., description="Organization RPP statistics")
    evaluation_overview: EvaluationStats = Field(..., description="Organization evaluation statistics")
    performance_overview: PerformanceStats = Field(..., description="Organization performance statistics")
    top_performers: List[Dict[str, Any]] = Field(..., description="Top performing teachers")
    improvement_needed: List[Dict[str, Any]] = Field(..., description="Teachers needing improvement")
    pending_reviews: List[Dict[str, Any]] = Field(..., description="Pending reviews")
    completion_trends: List[Dict[str, Any]] = Field(..., description="Completion trends over time")


class AdminDashboard(BaseModel):
    """System-wide admin dashboard."""
    system_overview: Dict[str, Any] = Field(..., description="System-wide statistics")
    organization_stats: List[Dict[str, Any]] = Field(..., description="Per-organization statistics")
    user_activity: Dict[str, Any] = Field(..., description="User activity statistics")
    system_health: Dict[str, Any] = Field(..., description="System health indicators")
    recent_system_activities: List[RecentActivity] = Field(..., description="Recent system activities")
    performance_trends: List[Dict[str, Any]] = Field(..., description="System performance trends")
    alerts: List[Dict[str, Any]] = Field(..., description="System alerts and warnings")


class QuickStats(BaseModel):
    """Quick statistics for widgets."""
    pending_count: int = Field(..., description="Pending items count")
    completed_today: int = Field(..., description="Items completed today")
    overdue_count: int = Field(..., description="Overdue items count")
    notification_count: int = Field(..., description="Unread notifications")