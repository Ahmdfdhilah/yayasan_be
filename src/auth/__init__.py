"""PKG Auth module init."""

from .jwt import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from .permissions import (
    get_current_user, 
    get_current_active_user, 
    require_roles,
    # PKG Role dependencies
    admin_required,
    kepala_sekolah_required,
    guru_required,
    # Combined role dependencies
    management_roles_required,
    evaluator_roles_required,
    media_manager_roles_required,
    # Business process permissions
    require_rpp_submission_access,
    require_rpp_review_access,
    require_evaluation_create_access,
    require_evaluation_view_access,
    require_evaluation_aspect_management,
    require_user_management_access,
    require_organization_management_access,
    require_media_management_access,
    require_analytics_access
)

__all__ = [
    # JWT functions
    "verify_password",
    "get_password_hash", 
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    # Auth dependencies
    "get_current_user",
    "get_current_active_user",
    "require_roles",
    # PKG Role dependencies
    "admin_required",
    "kepala_sekolah_required",
    "guru_required",
    # Combined role dependencies
    "management_roles_required",
    "evaluator_roles_required",
    "media_manager_roles_required",
    # Business process permissions
    "require_rpp_submission_access",
    "require_rpp_review_access",
    "require_evaluation_create_access",
    "require_evaluation_view_access",
    "require_evaluation_aspect_management",
    "require_user_management_access",
    "require_organization_management_access",
    "require_media_management_access",
    "require_analytics_access"
]