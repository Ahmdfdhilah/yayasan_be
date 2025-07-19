"""Dashboard service for PKG system overview."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.evaluation_result import EvaluationResultRepository
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.schemas.dashboard import (
    DashboardOverview, UserDashboard, OrganizationDashboard, AdminDashboard,
    RPPStats, EvaluationStats, PerformanceStats, RecentActivity
)
from src.models.enums import  UserRole


class DashboardService:
    """Service for dashboard functionality."""
    
    def __init__(
        self,
        rpp_repo: RPPSubmissionRepository,
        evaluation_repo: TeacherEvaluationRepository,
        result_repo: EvaluationResultRepository,
        user_repo: UserRepository,
        org_repo: OrganizationRepository
    ):
        self.rpp_repo = rpp_repo
        self.evaluation_repo = evaluation_repo
        self.result_repo = result_repo
        self.user_repo = user_repo
        self.org_repo = org_repo
    
    async def get_dashboard_overview(
        self,
        user_id: int,
        user_roles: List[str],
        organization_id: Optional[int] = None,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> DashboardOverview:
        """Get comprehensive dashboard overview."""
        
        # Get user info
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_info = {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "roles": user_roles,
            "organization_id": organization_id
        }
        
        # Get current academic period if not specified
        if not academic_year or not semester:
            current_date = datetime.now()
            academic_year = f"{current_date.year}/{current_date.year + 1}"
            semester = "Ganjil" if current_date.month >= 7 else "Genap"
        
        academic_period = {
            "academic_year": academic_year,
            "semester": semester
        }
        
        # Get statistics based on user role and organization
        rpp_stats = await self._get_rpp_stats(organization_id, academic_year, semester)
        evaluation_stats = await self._get_evaluation_stats(organization_id, academic_year, semester)
        performance_stats = await self._get_performance_stats(organization_id, academic_year, semester)
        
        # Get recent activities
        recent_activities = await self._get_recent_activities(organization_id, limit=10)
        
        # Get pending tasks for user
        pending_tasks = await self._get_pending_tasks(user_id, user_roles, organization_id)
        
        return DashboardOverview(
            user_info=user_info,
            rpp_stats=rpp_stats,
            evaluation_stats=evaluation_stats,
            performance_stats=performance_stats,
            recent_activities=recent_activities,
            pending_tasks=pending_tasks,
            academic_period=academic_period
        )
    
    async def get_user_dashboard(
        self,
        user_id: int,
        requestor_id: int,
        requestor_roles: List[str],
        academic_year: Optional[str] = None
    ) -> UserDashboard:
        """Get user-specific dashboard (guru perspective)."""
        
        # Check permissions
        if user_id != requestor_id and not any(role in ["super_admin", "admin", "kepala_sekolah"] for role in requestor_roles):
            raise HTTPException(status_code=403, detail="Access denied")
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_info = {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "organization_id": user.organization_id
        }
        
        # Get user's RPP submissions
        my_rpp_submissions = await self._get_user_rpp_submissions(user_id, academic_year)
        
        # Get user's evaluations
        my_evaluations = await self._get_user_evaluations(user_id, academic_year)
        
        # Get performance summary
        performance_summary = await self._get_user_performance_summary(user_id, academic_year)
        
        # Get improvement areas and achievements
        improvement_areas = await self._get_improvement_areas(user_id)
        achievements = await self._get_achievements(user_id)
        
        # Get upcoming deadlines
        upcoming_deadlines = await self._get_upcoming_deadlines(user_id)
        
        return UserDashboard(
            user_info=user_info,
            my_rpp_submissions=my_rpp_submissions,
            my_evaluations=my_evaluations,
            performance_summary=performance_summary,
            improvement_areas=improvement_areas,
            achievements=achievements,
            upcoming_deadlines=upcoming_deadlines
        )
    
    async def get_organization_dashboard(
        self,
        organization_id: int,
        requestor_id: int,
        requestor_roles: List[str],
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> OrganizationDashboard:
        """Get organization dashboard (kepala sekolah perspective)."""
        
        # Check permissions
        if not any(role in ["super_admin", "admin", "kepala_sekolah"] for role in requestor_roles):
            raise HTTPException(status_code=403, detail="Access denied")
        
        org = await self.org_repo.get_by_id(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        organization_info = {
            "id": org.id,
            "name": org.name,
            "type": org.organization_type,
            "created_at": org.created_at
        }
        
        # Get teacher summary
        teacher_summary = await self._get_teacher_summary(organization_id)
        
        # Get organization statistics
        rpp_overview = await self._get_rpp_stats(organization_id, academic_year, semester)
        evaluation_overview = await self._get_evaluation_stats(organization_id, academic_year, semester)
        performance_overview = await self._get_performance_stats(organization_id, academic_year, semester)
        
        # Get top performers and improvement needed
        top_performers = await self._get_organization_top_performers(organization_id, academic_year, semester)
        improvement_needed = await self._get_organization_improvement_needed(organization_id, academic_year, semester)
        
        # Get pending reviews
        pending_reviews = await self._get_organization_pending_reviews(organization_id)
        
        # Get completion trends
        completion_trends = await self._get_completion_trends(organization_id, academic_year)
        
        return OrganizationDashboard(
            organization_info=organization_info,
            teacher_summary=teacher_summary,
            rpp_overview=rpp_overview,
            evaluation_overview=evaluation_overview,
            performance_overview=performance_overview,
            top_performers=top_performers,
            improvement_needed=improvement_needed,
            pending_reviews=pending_reviews,
            completion_trends=completion_trends
        )
    
    async def get_admin_dashboard(
        self,
        requestor_id: int,
        requestor_roles: List[str],
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> AdminDashboard:
        """Get system-wide admin dashboard."""
        
        # Check permissions
        if not any(role in ["super_admin", "admin"] for role in requestor_roles):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get system overview
        system_overview = await self._get_system_overview(academic_year, semester)
        
        # Get organization statistics
        organization_stats = await self._get_organization_stats(academic_year, semester)
        
        # Get user activity
        user_activity = await self._get_user_activity()
        
        # Get system health
        system_health = await self._get_system_health()
        
        # Get recent system activities
        recent_system_activities = await self._get_recent_activities(None, limit=20)
        
        # Get performance trends
        performance_trends = await self._get_system_performance_trends(academic_year)
        
        # Get alerts
        alerts = await self._get_system_alerts()
        
        return AdminDashboard(
            system_overview=system_overview,
            organization_stats=organization_stats,
            user_activity=user_activity,
            system_health=system_health,
            recent_system_activities=recent_system_activities,
            performance_trends=performance_trends,
            alerts=alerts
        )
    
    async def get_quick_stats(
        self,
        user_id: int,
        user_roles: List[str],
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get quick statistics for current user."""
        
        pending_count = 0
        completed_today = 0
        overdue_count = 0
        
        # Calculate based on user role
        if "guru" in user_roles:
            # For teachers: pending RPP submissions, evaluations completed today, overdue submissions
            pending_count = await self._count_user_pending_rpps(user_id)
            completed_today = await self._count_user_completed_today(user_id)
            overdue_count = await self._count_user_overdue_items(user_id)
        
        elif any(role in ["kepala_sekolah", "admin", "super_admin"] for role in user_roles):
            # For management: pending reviews, completed reviews today, overdue reviews
            pending_count = await self._count_pending_reviews(organization_id)
            completed_today = await self._count_completed_reviews_today(organization_id)
            overdue_count = await self._count_overdue_reviews(organization_id)
        
        return {
            "pending_count": pending_count,
            "completed_today": completed_today,
            "overdue_count": overdue_count,
            "notification_count": 0  # Placeholder for notification system
        }
    
    # Helper methods
    async def _get_rpp_stats(
        self,
        organization_id: Optional[int],
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> RPPStats:
        """Get RPP submission statistics."""
        # Implementation would query RPP submissions with filters
        # This is a placeholder implementation
        total = 100
        pending = 20
        approved = 60
        rejected = 15
        revision_needed = 5
        
        return RPPStats(
            total_submissions=total,
            pending_submissions=pending,
            approved_submissions=approved,
            rejected_submissions=rejected,
            revision_needed=revision_needed,
            approval_rate=round((approved / total) * 100, 2) if total > 0 else 0.0
        )
    
    async def _get_evaluation_stats(
        self,
        organization_id: Optional[int],
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> EvaluationStats:
        """Get evaluation statistics."""
        # Placeholder implementation
        total = 150
        completed = 120
        pending = 30
        
        return EvaluationStats(
            total_evaluations=total,
            completed_evaluations=completed,
            pending_evaluations=pending,
            average_score=85.5,
            completion_rate=round((completed / total) * 100, 2) if total > 0 else 0.0
        )
    
    async def _get_performance_stats(
        self,
        organization_id: Optional[int],
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> PerformanceStats:
        """Get performance statistics."""
        # Placeholder implementation
        total_teachers = 50
        evaluated = 40
        top_performers = 10
        need_improvement = 5
        
        return PerformanceStats(
            total_teachers=total_teachers,
            evaluated_teachers=evaluated,
            top_performers=top_performers,
            need_improvement=need_improvement,
            average_performance=82.3
        )
    
    async def _get_recent_activities(
        self,
        organization_id: Optional[int],
        limit: int = 10
    ) -> List[RecentActivity]:
        """Get recent activities."""
        # Placeholder implementation
        return [
            RecentActivity(
                id=1,
                type="rpp_submission",
                description="RPP submission approved",
                user_name="John Doe",
                timestamp=datetime.now() - timedelta(hours=2)
            ),
            RecentActivity(
                id=2,
                type="evaluation_completed",
                description="Teacher evaluation completed",
                user_name="Jane Smith",
                timestamp=datetime.now() - timedelta(hours=5)
            )
        ]
    
    async def _get_pending_tasks(
        self,
        user_id: int,
        user_roles: List[str],
        organization_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Get pending tasks for user."""
        # Placeholder implementation
        return [
            {"type": "rpp_review", "count": 5, "description": "RPP submissions to review"},
            {"type": "evaluation_due", "count": 3, "description": "Evaluations due this week"}
        ]
    
    # Additional helper methods would be implemented here...
    async def _get_user_rpp_submissions(self, user_id: int, academic_year: Optional[str]) -> List[Dict[str, Any]]:
        """Get user's RPP submissions."""
        return []
    
    async def _get_user_evaluations(self, user_id: int, academic_year: Optional[str]) -> List[Dict[str, Any]]:
        """Get user's evaluations."""
        return []
    
    async def _get_user_performance_summary(self, user_id: int, academic_year: Optional[str]) -> Dict[str, Any]:
        """Get user performance summary."""
        return {"average_score": 85.0, "rank": 10, "total_teachers": 50}
    
    async def _get_improvement_areas(self, user_id: int) -> List[str]:
        """Get improvement areas for user."""
        return ["Classroom management", "Student engagement"]
    
    async def _get_achievements(self, user_id: int) -> List[str]:
        """Get achievements for user."""
        return ["Top performer Q1 2024", "Perfect attendance"]
    
    async def _get_upcoming_deadlines(self, user_id: int) -> List[Dict[str, Any]]:
        """Get upcoming deadlines for user."""
        return []
    
    async def _get_teacher_summary(self, organization_id: int) -> Dict[str, Any]:
        """Get teacher summary for organization."""
        return {"total": 50, "active": 48, "on_leave": 2}
    
    async def _get_organization_top_performers(
        self, organization_id: int, academic_year: Optional[str], semester: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get top performers for organization."""
        return []
    
    async def _get_organization_improvement_needed(
        self, organization_id: int, academic_year: Optional[str], semester: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get teachers needing improvement."""
        return []
    
    async def _get_organization_pending_reviews(self, organization_id: int) -> List[Dict[str, Any]]:
        """Get pending reviews for organization."""
        return []
    
    async def _get_completion_trends(
        self, organization_id: int, academic_year: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get completion trends."""
        return []
    
    async def _get_system_overview(
        self, academic_year: Optional[str], semester: Optional[str]
    ) -> Dict[str, Any]:
        """Get system overview."""
        return {"total_users": 500, "total_organizations": 10, "total_submissions": 1000}
    
    async def _get_organization_stats(
        self, academic_year: Optional[str], semester: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get organization statistics."""
        return []
    
    async def _get_user_activity(self) -> Dict[str, Any]:
        """Get user activity statistics."""
        return {"active_users": 450, "new_users_this_month": 25}
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health indicators."""
        return {"status": "healthy", "uptime": "99.9%", "response_time": "150ms"}
    
    async def _get_system_performance_trends(self, academic_year: Optional[str]) -> List[Dict[str, Any]]:
        """Get system performance trends."""
        return []
    
    async def _get_system_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts."""
        return []
    
    async def _count_user_pending_rpps(self, user_id: int) -> int:
        """Count user's pending RPP submissions."""
        return 0
    
    async def _count_user_completed_today(self, user_id: int) -> int:
        """Count user's items completed today."""
        return 0
    
    async def _count_user_overdue_items(self, user_id: int) -> int:
        """Count user's overdue items."""
        return 0
    
    async def _count_pending_reviews(self, organization_id: Optional[int]) -> int:
        """Count pending reviews."""
        return 0
    
    async def _count_completed_reviews_today(self, organization_id: Optional[int]) -> int:
        """Count reviews completed today."""
        return 0
    
    async def _count_overdue_reviews(self, organization_id: Optional[int]) -> int:
        """Count overdue reviews."""
        return 0