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
    TeacherDashboard,
    PrincipalDashboard,
    AdminDashboard
)
from src.models.enums import RPPSubmissionStatus, EvaluationGrade
from src.utils.messages import get_message


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
                detail=get_message("user", "not_found")
            )
        
        # Determine user role and organization - prioritize JWT roles
        user_role = "guru"  # default
        
        # First check JWT roles (most reliable since they come from authentication)
        if current_user.get("roles"):
            jwt_roles = current_user["roles"]
            if "admin" in jwt_roles:
                user_role = "admin"
            elif "kepala_sekolah" in jwt_roles:
                user_role = "kepala_sekolah"
            elif "guru" in jwt_roles:
                user_role = "guru"
        
        # Fallback to database role detection if JWT doesn't have roles
        if user_role == "guru" and not current_user.get("roles"):
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
        
        # Check user roles from UserRole relationship
        if hasattr(user_obj, 'user_roles') and user_obj.user_roles:
            active_roles = [ur.role_name for ur in user_obj.user_roles if ur.is_active]
            if "admin" in active_roles:
                return "admin"
            elif "kepala_sekolah" in active_roles:
                return "kepala_sekolah"
            elif "guru" in active_roles:
                return "guru"
        
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
        
        # Get organization-wide stats for context
        org_rpp_stats = await self._get_organization_rpp_stats(user_obj.organization_id, filters.period_id)
        org_eval_stats = await self._get_organization_evaluation_stats(user_obj.organization_id, filters.period_id)
        
        # Get organization name and create organization summary for teacher
        org_name = None
        org_summary = None
        if user_obj.organization_id:
            org = await self.org_repo.get_by_id(user_obj.organization_id)
            org_name = org.name if org else None
            
            # Create organization summary for teacher context
            if org:
                teacher_count = await self.user_repo.get_teachers_count_by_organization(org.id)
                org_summary = OrganizationSummary(
                    organization_id=org.id,
                    organization_name=org.name,
                    total_teachers=teacher_count,
                    rpp_stats=org_rpp_stats,
                    evaluation_stats=org_eval_stats
                )
        
        return TeacherDashboard(
            period=period,
            rpp_stats=org_rpp_stats,
            evaluation_stats=org_eval_stats,
            organizations=[org_summary] if org_summary else [],
            user_role="guru",
            organization_name=org_name,
            last_updated=datetime.utcnow(),
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
        
        # Get organization overview
        org_overview = await self._get_organization_overview(user_obj.organization_id, filters.period_id)
        
        # Get teacher summaries in organization
        teacher_summaries = await self._get_organization_teacher_summaries(user_obj.organization_id, filters.period_id)
        
        # Get organization name and create organization summary for principal
        org_name = None
        org_summary = None
        if user_obj.organization_id:
            org = await self.org_repo.get_by_id(user_obj.organization_id)
            org_name = org.name if org else None
            
            # Create organization summary for principal context
            if org:
                teacher_count = await self.user_repo.get_teachers_count_by_organization(org.id)
                org_summary = OrganizationSummary(
                    organization_id=org.id,
                    organization_name=org.name,
                    total_teachers=teacher_count,
                    rpp_stats=org_rpp_stats,
                    evaluation_stats=org_eval_stats
                )
        
        return PrincipalDashboard(
            period=period,
            rpp_stats=org_rpp_stats,
            evaluation_stats=org_eval_stats,
            organizations=[org_summary] if org_summary else [],
            user_role="kepala_sekolah",
            organization_name=org_name,
            last_updated=datetime.utcnow(),
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
        
        # Get organization distribution for admin
        organization_distribution = await self._get_organization_distribution(filters.period_id)
        
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
            organization_distribution=organization_distribution,
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
            pending_reviews=progress["pending"],
            avg_review_time_hours=None,  # Individual teacher doesn't need this
            submission_rate=progress["completion_rate"]
        )
    
    async def _get_teacher_evaluation_stats(self, teacher_id: int, period_id: Optional[int]) -> TeacherEvaluationDashboardStats:
        """Get evaluation statistics for a specific teacher."""
        from src.schemas.teacher_evaluation import TeacherEvaluationFilterParams
        
        # Get ALL teacher evaluations with pagination
        all_evaluations = []
        skip = 0
        limit = 100
        
        while True:
            filters = TeacherEvaluationFilterParams(
                teacher_id=teacher_id,
                period_id=period_id,
                skip=skip,
                limit=limit
            )
            
            evaluations, total = await self.evaluation_repo.get_evaluations_filtered(filters)
            all_evaluations.extend(evaluations)
            
            if len(evaluations) < limit or skip + limit >= total:
                break
            
            skip += limit
        
        evaluations = all_evaluations
        
        total = len(evaluations)
        
        # Calculate grade distribution and scores
        grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
        total_score = 0
        total_total_score = 0
        total_final_score = 0
        evaluated_count = 0
        final_score_count = 0
        
        for eval in evaluations:
            if eval.average_score is not None:
                total_score += eval.average_score
                evaluated_count += 1
            
            if eval.total_score is not None:
                total_total_score += eval.total_score
            
            if eval.final_grade is not None:
                total_final_score += eval.final_grade
                final_score_count += 1
                
                # Convert final_grade to letter grade
                if eval.final_grade >= 87.5:
                    grade_dist["A"] += 1
                elif eval.final_grade >= 62.5:
                    grade_dist["B"] += 1
                elif eval.final_grade >= 37.5:
                    grade_dist["C"] += 1
                else:
                    grade_dist["D"] += 1
        
        avg_score = total_score / evaluated_count if evaluated_count > 0 else 0
        avg_total_score = total_total_score / evaluated_count if evaluated_count > 0 else 0
        avg_final_score = total_final_score / final_score_count if final_score_count > 0 else 0
        
        # Count total aspects from all evaluations
        total_aspects = sum(e.item_count for e in evaluations) if evaluations else 0
        
        return TeacherEvaluationDashboardStats(
            total_evaluations=total,
            avg_score=avg_score,
            avg_total_score=avg_total_score,
            avg_final_score=avg_final_score,
            grade_distribution=grade_dist,
            total_teachers=1,  # Just this teacher
            total_aspects=total_aspects
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
            pending_reviews=analytics["pending_reviews"],
            avg_review_time_hours=analytics["avg_review_time_hours"],
            submission_rate=self._calculate_submission_rate(analytics)
        )
    
    async def _get_organization_evaluation_stats(self, org_id: Optional[int], period_id: Optional[int]) -> TeacherEvaluationDashboardStats:
        """Get evaluation statistics for an organization."""
        if period_id:
            stats = await self.evaluation_repo.get_period_statistics(period_id, org_id)
        else:
            # Get organization-wide stats (fallback)
            stats = {
                "total_teachers": 0,
                "total_aspects_evaluated": 0,
                "total_evaluations": 0,
                "completed_evaluations": 0,
                "completion_percentage": 0,
                "average_score": 0,
                "average_total_score": 0,
                "average_final_score": 0,
                "final_grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "None": 0}
            }
        
        # Exclude "None" grades from the grade distribution for dashboard
        grade_dist = {k: v for k, v in stats["final_grade_distribution"].items() if k != "None"}
        
        return TeacherEvaluationDashboardStats(
            total_evaluations=stats["total_evaluations"],
            avg_score=stats["average_score"],
            avg_total_score=stats.get("average_total_score", 0),
            avg_final_score=stats.get("average_final_score", 0),
            grade_distribution=grade_dist,
            total_teachers=stats["total_teachers"],
            total_aspects=stats["total_aspects_evaluated"]
        )
    
    async def _get_system_rpp_stats(self, period_id: Optional[int]) -> RPPDashboardStats:
        """Get system-wide RPP statistics."""
        analytics = await self.rpp_repo.get_submissions_analytics()
        
        return RPPDashboardStats(
            total_submissions=analytics["total_submissions"],
            pending_submissions=analytics["by_status"].get("pending", 0),
            approved_submissions=analytics["by_status"].get("approved", 0),
            rejected_submissions=analytics["by_status"].get("rejected", 0),
            pending_reviews=analytics["pending_reviews"],
            avg_review_time_hours=analytics["avg_review_time_hours"],
            submission_rate=self._calculate_submission_rate(analytics)
        )
    
    async def _get_system_evaluation_stats(self, period_id: Optional[int]) -> TeacherEvaluationDashboardStats:
        """Get system-wide evaluation statistics."""
        if period_id:
            stats = await self.evaluation_repo.get_period_statistics(period_id)
        else:
            # Get system-wide stats (fallback)
            stats = {
                "total_teachers": 0,
                "total_aspects_evaluated": 0,
                "total_evaluations": 0,
                "completed_evaluations": 0,
                "completion_percentage": 0,
                "average_score": 0,
                "average_total_score": 0,
                "average_final_score": 0,
                "final_grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "None": 0}
            }
        
        # Exclude "None" grades from the grade distribution for dashboard
        grade_dist = {k: v for k, v in stats["final_grade_distribution"].items() if k != "None"}
        
        return TeacherEvaluationDashboardStats(
            total_evaluations=stats["total_evaluations"],
            avg_score=stats["average_score"],
            avg_total_score=stats.get("average_total_score", 0),
            avg_final_score=stats.get("average_final_score", 0),
            grade_distribution=grade_dist,
            total_teachers=stats["total_teachers"],
            total_aspects=stats["total_aspects_evaluated"]
        )
    
    
    async def _get_all_organization_summaries(self, period_id: Optional[int]) -> List[OrganizationSummary]:
        """Get summaries for all organizations."""
        organizations = await self.org_repo.get_all()
        summaries = []
        
        for org in organizations:
            rpp_stats = await self._get_organization_rpp_stats(org.id, period_id)
            eval_stats = await self._get_organization_evaluation_stats(org.id, period_id)
            
            # Count teachers in organization using user repository
            teacher_count = await self.user_repo.get_teachers_count_by_organization(org.id)
            
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
        
        # Get teacher count using user repository
        teacher_count = await self.user_repo.get_teachers_count_by_organization(org_id)
        
        return {
            "organization_name": org.name,
            "total_teachers": teacher_count,
            "active_teachers": teacher_count,  # Simplified - assume all are active
            "head_name": org.head.profile.get('full_name') if org.head and org.head.profile else "No head assigned"
        }
    
    async def _get_organization_teacher_summaries(self, org_id: int, period_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get teacher summaries for an organization."""
        # Get all teachers in the organization
        teachers = await self.user_repo.get_teachers_by_organization(org_id)
        
        summaries = []
        for teacher in teachers[:10]:  # Limit to top 10 for performance
            try:
                rpp_progress = await self.rpp_repo.get_teacher_progress(teacher.id)
                
                summaries.append({
                    "teacher_id": teacher.id,
                    "teacher_name": teacher.profile.get('full_name', teacher.email) if teacher.profile else teacher.email,
                    "total_rpps": rpp_progress["total_submitted"],
                    "approved_rpps": rpp_progress["approved"],
                    "completion_rate": rpp_progress["completion_rate"]
                })
            except:
                # If we can't get RPP progress, still include the teacher with zero stats
                summaries.append({
                    "teacher_id": teacher.id,
                    "teacher_name": teacher.profile.get('full_name', teacher.email) if teacher.profile else teacher.email,
                    "total_rpps": 0,
                    "approved_rpps": 0,
                    "completion_rate": 0.0
                })
        
        return summaries
    
    async def _get_system_overview(self, period_id: Optional[int]) -> Dict[str, Any]:
        """Get system-wide overview."""
        # Get total counts using repository methods
        total_users = await self.user_repo.get_user_count()
        total_orgs = await self.org_repo.get_organization_count()
        
        return {
            "total_users": total_users,
            "total_organizations": total_orgs,
            "system_health": "good"  # This could be calculated based on various metrics
        }
    
    async def _get_recent_system_activities(self) -> List[Dict[str, Any]]:
        """Get recent system activities."""
        return [
            {"type": "system_overview", "message": "System running normally"},
            {"type": "data_summary", "message": "Dashboard data refreshed"}
        ]
    
    async def _get_organization_distribution(self, period_id: Optional[int]) -> Dict[str, Dict[str, int]]:
        """Get grade distribution per organization for admin dashboard."""
        organizations = await self.org_repo.get_all()
        distribution = {}
        
        for org in organizations:
            eval_stats = await self._get_organization_evaluation_stats(org.id, period_id)
            distribution[str(org.id)] = eval_stats.grade_distribution
        
        return distribution
    
    def _calculate_submission_rate(self, analytics: Dict[str, Any]) -> float:
        """Calculate submission completion rate."""
        total = analytics["total_submissions"]
        approved = analytics["by_status"].get("approved", 0)
        return (approved / total * 100) if total > 0 else 0