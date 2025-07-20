"""Dashboard service for PKG system."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.period import PeriodRepository
from src.schemas.dashboard import (
    DashboardResponse,
    DashboardFilters,
    RPPDashboardStats,
    TeacherEvaluationDashboardStats,
    OrganizationSummary,
    PeriodSummary,
    QuickStats,
    TeacherDashboard,
    PrincipalDashboard,
    AdminDashboard
)
from src.models.enums import RPPStatus, EvaluationGrade


class DashboardService:
    """Service for dashboard operations."""
    
    def __init__(
        self,
        rpp_repo: RPPSubmissionRepository,
        evaluation_repo: TeacherEvaluationRepository,
        user_repo: UserRepository,
        org_repo: OrganizationRepository,
        period_repo: PeriodRepository
    ):
        self.rpp_repo = rpp_repo
        self.evaluation_repo = evaluation_repo
        self.user_repo = user_repo
        self.org_repo = org_repo
        self.period_repo = period_repo
    
    async def get_dashboard_data(
        self,
        current_user: dict,
        filters: DashboardFilters
    ) -> DashboardResponse:
        """Get dashboard data based on user role and filters."""
        # Get current user details
        user_obj = await self.user_repo.get_by_id(current_user["id"])
        if not user_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Determine user role and organization
        user_role = self._determine_user_role(user_obj)
        
        # Get period information
        period = None
        if filters.period_id:
            period_obj = await self.period_repo.get_by_id(filters.period_id)
            if period_obj:
                period = PeriodSummary(
                    period_id=period_obj.id,
                    period_name=period_obj.period_name,
                    start_date=period_obj.start_date,
                    end_date=period_obj.end_date,
                    is_active=period_obj.is_active
                )
        
        # Route to appropriate dashboard based on role
        if user_role == "admin":
            return await self._get_admin_dashboard(user_obj, filters, period)
        elif user_role == "kepala_sekolah":
            return await self._get_principal_dashboard(user_obj, filters, period)
        else:  # guru or other roles
            return await self._get_teacher_dashboard(user_obj, filters, period)
    
    def _determine_user_role(self, user_obj) -> str:
        """Determine user role based on user object."""
        # Check if user has no organization (likely admin)
        if not user_obj.organization_id:
            return "admin"
        
        # Check user role from profile or role field
        if hasattr(user_obj, 'role') and user_obj.role:
            return user_obj.role
        
        # Check from profile
        if user_obj.profile and user_obj.profile.get('role'):
            return user_obj.profile['role']
        
        # Default to teacher
        return "guru"
    
    async def _get_teacher_dashboard(
        self,
        user_obj,
        filters: DashboardFilters,
        period: Optional[PeriodSummary]
    ) -> TeacherDashboard:
        """Get dashboard data for teachers (guru)."""
        # Get personal RPP stats
        my_rpp_stats = await self._get_teacher_rpp_stats(user_obj.id, filters.period_id)
        
        # Get personal evaluation stats
        my_evaluation_stats = await self._get_teacher_evaluation_stats(user_obj.id, filters.period_id)
        
        # Get quick stats
        quick_stats = await self._get_teacher_quick_stats(user_obj.id, filters.period_id)
        
        # Get organization-wide stats for context
        org_rpp_stats = await self._get_organization_rpp_stats(user_obj.organization_id, filters.period_id)
        org_eval_stats = await self._get_organization_evaluation_stats(user_obj.organization_id, filters.period_id)
        
        # Get organization name
        org_name = None
        if user_obj.organization_id:
            org = await self.org_repo.get_by_id(user_obj.organization_id)
            org_name = org.name if org else None
        
        return TeacherDashboard(
            period=period,
            rpp_stats=org_rpp_stats,
            evaluation_stats=org_eval_stats,
            organizations=None,
            user_role="guru",
            organization_name=org_name,
            last_updated=datetime.utcnow(),
            quick_stats=quick_stats,
            my_rpp_stats=my_rpp_stats,
            my_evaluation_stats=my_evaluation_stats
        )
    
    async def _get_principal_dashboard(
        self,
        user_obj,
        filters: DashboardFilters,
        period: Optional[PeriodSummary]
    ) -> PrincipalDashboard:
        """Get dashboard data for principals (kepala_sekolah)."""
        # Get organization stats
        org_rpp_stats = await self._get_organization_rpp_stats(user_obj.organization_id, filters.period_id)
        org_eval_stats = await self._get_organization_evaluation_stats(user_obj.organization_id, filters.period_id)
        
        # Get quick stats for principal
        quick_stats = await self._get_principal_quick_stats(user_obj.id, user_obj.organization_id, filters.period_id)
        
        # Get organization overview
        org_overview = await self._get_organization_overview(user_obj.organization_id, filters.period_id)
        
        # Get teacher summaries in organization
        teacher_summaries = await self._get_organization_teacher_summaries(user_obj.organization_id, filters.period_id)
        
        # Get organization name
        org_name = None
        if user_obj.organization_id:
            org = await self.org_repo.get_by_id(user_obj.organization_id)
            org_name = org.name if org else None
        
        return PrincipalDashboard(
            period=period,
            rpp_stats=org_rpp_stats,
            evaluation_stats=org_eval_stats,
            organizations=None,
            user_role="kepala_sekolah",
            organization_name=org_name,
            last_updated=datetime.utcnow(),
            quick_stats=quick_stats,
            organization_overview=org_overview,
            teacher_summaries=teacher_summaries
        )
    
    async def _get_admin_dashboard(
        self,
        user_obj,
        filters: DashboardFilters,
        period: Optional[PeriodSummary]
    ) -> AdminDashboard:
        """Get dashboard data for admins."""
        # Get system-wide stats or filtered by organization
        if filters.organization_id:
            rpp_stats = await self._get_organization_rpp_stats(filters.organization_id, filters.period_id)
            eval_stats = await self._get_organization_evaluation_stats(filters.organization_id, filters.period_id)
        else:
            rpp_stats = await self._get_system_rpp_stats(filters.period_id)
            eval_stats = await self._get_system_evaluation_stats(filters.period_id)
        
        # Get all organization summaries
        org_summaries = await self._get_all_organization_summaries(filters.period_id)
        
        # Get system overview
        system_overview = await self._get_system_overview(filters.period_id)
        
        # Get recent system activities
        recent_activities = await self._get_recent_system_activities()
        
        return AdminDashboard(
            period=period,
            rpp_stats=rpp_stats,
            evaluation_stats=eval_stats,
            organizations=org_summaries,
            user_role="admin",
            organization_name=None,
            last_updated=datetime.utcnow(),
            system_overview=system_overview,
            organization_summaries=org_summaries,
            recent_system_activities=recent_activities
        )
    
    # Helper methods for statistics
    
    async def _get_teacher_rpp_stats(self, teacher_id: int, period_id: Optional[int]) -> RPPDashboardStats:
        """Get RPP statistics for a specific teacher."""
        progress = await self.rpp_repo.get_teacher_progress(teacher_id)
        
        return RPPDashboardStats(
            total_submissions=progress["total_submitted"],
            pending_submissions=progress["pending"],
            approved_submissions=progress["approved"],
            rejected_submissions=progress["rejected"],
            revision_needed_submissions=progress["revision_needed"],
            pending_reviews=progress["pending"],
            avg_review_time_hours=None,  # Individual teacher doesn't need this
            submission_rate=progress["completion_rate"]
        )
    
    async def _get_teacher_evaluation_stats(self, teacher_id: int, period_id: Optional[int]) -> TeacherEvaluationDashboardStats:
        """Get evaluation statistics for a specific teacher."""
        if period_id:
            evaluations = await self.evaluation_repo.get_teacher_evaluations_in_period(teacher_id, period_id)
        else:
            evaluations = await self.evaluation_repo.get_teacher_evaluations(teacher_id)
        
        total = len(evaluations)
        completed = len([e for e in evaluations if e.grade is not None])
        
        # Calculate grade distribution
        grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
        total_score = 0
        
        for eval in evaluations:
            if eval.grade:
                grade_dist[eval.grade.value] += 1
                total_score += EvaluationGrade.get_score(eval.grade.value)
        
        avg_score = total_score / completed if completed > 0 else 0
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        return TeacherEvaluationDashboardStats(
            total_evaluations=total,
            completed_evaluations=completed,
            pending_evaluations=total - completed,
            completion_rate=completion_rate,
            avg_score=avg_score,
            grade_distribution=grade_dist,
            total_teachers=1,  # Just this teacher
            total_aspects=len(set(e.aspect_id for e in evaluations))
        )
    
    async def _get_organization_rpp_stats(self, org_id: Optional[int], period_id: Optional[int]) -> RPPDashboardStats:
        """Get RPP statistics for an organization."""
        if not org_id:
            return await self._get_system_rpp_stats(period_id)
        
        analytics = await self.rpp_repo.get_submissions_analytics(org_id)
        
        return RPPDashboardStats(
            total_submissions=analytics["total_submissions"],
            pending_submissions=analytics["by_status"].get("pending", 0),
            approved_submissions=analytics["by_status"].get("approved", 0),
            rejected_submissions=analytics["by_status"].get("rejected", 0),
            revision_needed_submissions=analytics["by_status"].get("revision_needed", 0),
            pending_reviews=analytics["pending_reviews"],
            avg_review_time_hours=analytics["avg_review_time_hours"],
            submission_rate=self._calculate_submission_rate(analytics)
        )
    
    async def _get_organization_evaluation_stats(self, org_id: Optional[int], period_id: Optional[int]) -> TeacherEvaluationDashboardStats:
        """Get evaluation statistics for an organization."""
        if period_id:
            stats = await self.evaluation_repo.get_period_statistics(period_id)
        else:
            # Get organization-wide stats (this would need to be implemented in repo)
            stats = {
                "total_teachers": 0,
                "total_aspects": 0,
                "total_possible_evaluations": 0,
                "completed_evaluations": 0,
                "completion_percentage": 0,
                "average_score": 0,
                "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0}
            }
        
        return TeacherEvaluationDashboardStats(
            total_evaluations=stats["total_possible_evaluations"],
            completed_evaluations=stats["completed_evaluations"],
            pending_evaluations=stats["total_possible_evaluations"] - stats["completed_evaluations"],
            completion_rate=stats["completion_percentage"],
            avg_score=stats["average_score"],
            grade_distribution=stats["grade_distribution"],
            total_teachers=stats["total_teachers"],
            total_aspects=stats["total_aspects"]
        )
    
    async def _get_system_rpp_stats(self, period_id: Optional[int]) -> RPPDashboardStats:
        """Get system-wide RPP statistics."""
        analytics = await self.rpp_repo.get_submissions_analytics()
        
        return RPPDashboardStats(
            total_submissions=analytics["total_submissions"],
            pending_submissions=analytics["by_status"].get("pending", 0),
            approved_submissions=analytics["by_status"].get("approved", 0),
            rejected_submissions=analytics["by_status"].get("rejected", 0),
            revision_needed_submissions=analytics["by_status"].get("revision_needed", 0),
            pending_reviews=analytics["pending_reviews"],
            avg_review_time_hours=analytics["avg_review_time_hours"],
            submission_rate=self._calculate_submission_rate(analytics)
        )
    
    async def _get_system_evaluation_stats(self, period_id: Optional[int]) -> TeacherEvaluationDashboardStats:
        """Get system-wide evaluation statistics."""
        if period_id:
            stats = await self.evaluation_repo.get_period_statistics(period_id)
        else:
            # Get system-wide stats
            stats = {
                "total_teachers": 0,
                "total_aspects": 0,
                "total_possible_evaluations": 0,
                "completed_evaluations": 0,
                "completion_percentage": 0,
                "average_score": 0,
                "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0}
            }
        
        return TeacherEvaluationDashboardStats(
            total_evaluations=stats["total_possible_evaluations"],
            completed_evaluations=stats["completed_evaluations"],
            pending_evaluations=stats["total_possible_evaluations"] - stats["completed_evaluations"],
            completion_rate=stats["completion_percentage"],
            avg_score=stats["average_score"],
            grade_distribution=stats["grade_distribution"],
            total_teachers=stats["total_teachers"],
            total_aspects=stats["total_aspects"]
        )
    
    async def _get_teacher_quick_stats(self, teacher_id: int, period_id: Optional[int]) -> QuickStats:
        """Get quick statistics for a teacher."""
        # Get pending RPPs
        pending_rpps = await self.rpp_repo.get_teacher_submissions(teacher_id, period_id)
        my_pending_rpps = len([r for r in pending_rpps if r.status == RPPStatus.PENDING])
        
        # Teachers don't review, so pending reviews is 0
        my_pending_reviews = 0
        
        # Get pending evaluations
        if period_id:
            evaluations = await self.evaluation_repo.get_teacher_evaluations_in_period(teacher_id, period_id)
        else:
            evaluations = await self.evaluation_repo.get_teacher_evaluations(teacher_id)
        
        my_pending_evaluations = len([e for e in evaluations if e.grade is None])
        
        # Recent activities (simplified)
        recent_activities = [
            {"type": "rpp_submission", "count": len(pending_rpps[:5])},
            {"type": "evaluations", "count": len(evaluations[:5])}
        ]
        
        return QuickStats(
            my_pending_rpps=my_pending_rpps,
            my_pending_reviews=my_pending_reviews,
            my_pending_evaluations=my_pending_evaluations,
            recent_activities=recent_activities
        )
    
    async def _get_principal_quick_stats(self, principal_id: int, org_id: int, period_id: Optional[int]) -> QuickStats:
        """Get quick statistics for a principal."""
        # Principals don't submit RPPs
        my_pending_rpps = 0
        
        # Get pending reviews for principal
        pending_reviews = await self.rpp_repo.get_pending_reviews(principal_id)
        my_pending_reviews = len(pending_reviews)
        
        # Principals don't get evaluated typically
        my_pending_evaluations = 0
        
        # Recent activities
        recent_activities = [
            {"type": "pending_reviews", "count": my_pending_reviews},
            {"type": "organization_overview", "count": 1}
        ]
        
        return QuickStats(
            my_pending_rpps=my_pending_rpps,
            my_pending_reviews=my_pending_reviews,
            my_pending_evaluations=my_pending_evaluations,
            recent_activities=recent_activities
        )
    
    async def _get_all_organization_summaries(self, period_id: Optional[int]) -> List[OrganizationSummary]:
        """Get summaries for all organizations."""
        organizations = await self.org_repo.get_all()
        summaries = []
        
        for org in organizations:
            rpp_stats = await self._get_organization_rpp_stats(org.id, period_id)
            eval_stats = await self._get_organization_evaluation_stats(org.id, period_id)
            
            # Count teachers in organization - use organization repo method
            try:
                teacher_count = await self.org_repo.get_user_count(org.id)
            except:
                teacher_count = 0
            
            summaries.append(OrganizationSummary(
                organization_id=org.id,
                organization_name=org.name,
                total_teachers=teacher_count,
                rpp_stats=rpp_stats,
                evaluation_stats=eval_stats
            ))
        
        return summaries
    
    async def _get_organization_overview(self, org_id: int, period_id: Optional[int]) -> Dict[str, Any]:
        """Get detailed organization overview."""
        org = await self.org_repo.get_by_id(org_id)
        if not org:
            return {}
        
        # Get teacher count from organization repo
        try:
            teacher_count = await self.org_repo.get_user_count(org_id)
        except:
            teacher_count = 0
        
        return {
            "organization_name": org.name,
            "total_teachers": teacher_count,
            "active_teachers": teacher_count,  # Simplified - assume all are active
            "head_name": org.head.profile.get('full_name') if org.head and org.head.profile else "No head assigned"
        }
    
    async def _get_organization_teacher_summaries(self, org_id: int, period_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get teacher summaries for an organization."""
        # For now, return simplified summaries since we don't have the exact user repo method
        try:
            teacher_count = await self.org_repo.get_user_count(org_id)
            
            # Return a simplified summary
            return [{
                "teacher_id": 0,
                "teacher_name": f"Teachers in organization ({teacher_count} total)",
                "total_rpps": 0,
                "approved_rpps": 0,
                "completion_rate": 0.0
            }]
        except:
            return []
    
    async def _get_system_overview(self, period_id: Optional[int]) -> Dict[str, Any]:
        """Get system-wide overview."""
        # Get total counts - simplified since we don't have exact methods
        try:
            organizations = await self.org_repo.get_all()
            total_orgs = len(organizations)
        except:
            total_orgs = 0
        
        return {
            "total_users": 0,  # Simplified since we don't have the exact method
            "total_organizations": total_orgs,
            "system_health": "good"  # This could be calculated based on various metrics
        }
    
    async def _get_recent_system_activities(self) -> List[Dict[str, Any]]:
        """Get recent system activities."""
        return [
            {"type": "system_overview", "message": "System running normally"},
            {"type": "data_summary", "message": "Dashboard data refreshed"}
        ]
    
    def _calculate_submission_rate(self, analytics: Dict[str, Any]) -> float:
        """Calculate submission completion rate."""
        total = analytics["total_submissions"]
        approved = analytics["by_status"].get("approved", 0)
        return (approved / total * 100) if total > 0 else 0