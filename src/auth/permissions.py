"""PKG (Penilaian Kinerja Guru) Authorization and Permission System."""

from typing import List, Dict, Optional, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import verify_token
from src.core.database import get_db


class JWTBearer(HTTPBearer):
    """Custom JWT handler for PKG system - supports only cookie-based authentication."""
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        # Get token from HttpOnly cookie only
        access_token = request.cookies.get("access_token")
        
        if access_token:
            return access_token
            
        # If auto_error is True and no token found, raise exception
        if self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please login.",
            )
        
        return None


jwt_bearer = JWTBearer()


async def get_current_user(
    token: str = Depends(jwt_bearer), 
    session: AsyncSession = Depends(get_db)
) -> Dict:
    """Get the current authenticated user from JWT token - PKG Multi-Role System."""
    # Import here to avoid circular import
    from src.repositories.user import UserRepository
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify and decode JWT token
        payload = verify_token(token)
        
        # Extract user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception

        # Convert user_id to integer
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            raise credentials_exception

        # Get user from database
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)

        if not user:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        # Get user role (single role system)
        user_role = user.role
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "role": user_role,              # Single role string
            "organization_id": user.organization_id,
            "is_active": user.is_active,
            "profile": user.profile or {}
        }

        return user_data

    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception
    except Exception as e:
        # Add logging for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception


async def get_current_active_user(
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    """Ensure the current user is active."""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User account is deactivated"
        )
    return current_user


def require_roles(required_roles: List[str]):
    """
    Dependency factory to require specific roles - PKG Multi-Role System.
    
    Args:
        required_roles: List of role names that are allowed access
        
    Returns:
        Dependency function that checks user roles
    """
    async def _check_roles(
        current_user: Dict = Depends(get_current_active_user),
    ) -> Dict:
        user_role = current_user.get("role")
        
        # Check if user has any of the required roles
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}. Your role: {user_role}",
            )
        
        return current_user
    
    return _check_roles


# ===== PKG ROLE-BASED DEPENDENCIES =====

# Admin - Administrative functions (includes SUPER_ADMIN)
admin_required = require_roles(["SUPER_ADMIN", "ADMIN"])

# Kepala Sekolah - School principal, primary evaluator and RPP reviewer
kepala_sekolah_required = require_roles(["KEPALA_SEKOLAH"])

# Guru - Teachers who submit RPPs and receive evaluations
guru_required = require_roles(["GURU"])

# Combined role dependencies for common access patterns
management_roles_required = require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH"])
evaluator_roles_required = require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH"])
media_manager_roles_required = require_roles(["SUPER_ADMIN", "ADMIN"])

# RPP Submission specific dependencies
guru_or_kepala_sekolah = require_roles(["GURU", "KEPALA_SEKOLAH"])
admin_or_kepala_sekolah = require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH"])
any_authorized_user = require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH", "GURU"])


# ===== PKG BUSINESS PROCESS PERMISSIONS =====

def require_rpp_submission_access():
    """Require access to submit RPP (only Guru)."""
    return require_roles(["GURU"])


def require_rpp_review_access():
    """Require access to review RPP (Kepala Sekolah, Admin, Super Admin)."""
    return require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH"])


def require_evaluation_create_access():
    """Require access to create teacher evaluations (evaluators)."""
    return require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH"])


def require_evaluation_view_access():
    """Require access to view evaluation results."""
    return require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH", "GURU"])


def require_evaluation_aspect_management():
    """Require access to manage evaluation aspects."""
    return require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH"])


def require_user_management_access():
    """Require access to manage users."""
    return require_roles(["SUPER_ADMIN", "ADMIN"])


def require_organization_management_access():
    """Require access to manage organizations."""
    return require_roles(["SUPER_ADMIN", "ADMIN"])


def require_media_management_access():
    """Require access to manage media files."""
    return require_roles(["SUPER_ADMIN", "ADMIN"])


def require_analytics_access():
    """Require access to view analytics and reports."""
    return require_roles(["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH"])


# ===== PKG UTILITY FUNCTIONS =====

def has_role(user: Dict, role: str) -> bool:
    """Check if user has specific role."""
    user_role = user.get("role")
    return user_role == role


def has_any_role(user: Dict, roles: List[str]) -> bool:
    """Check if user has any of the specified roles."""
    user_role = user.get("role")
    return user_role in roles


def is_super_admin(user: Dict) -> bool:
    """Check if user is super admin."""
    return has_role(user, "SUPER_ADMIN")


def is_admin(user: Dict) -> bool:
    """Check if user is admin (includes super admin)."""
    return has_any_role(user, ["SUPER_ADMIN", "ADMIN"])


def is_kepala_sekolah(user: Dict) -> bool:
    """Check if user is kepala sekolah (school principal)."""
    return has_role(user, "KEPALA_SEKOLAH")


def is_guru(user: Dict) -> bool:
    """Check if user is guru (teacher)."""
    return has_role(user, "GURU")


def is_evaluator(user: Dict) -> bool:
    """Check if user can perform evaluations.
    
    - Super Admins can evaluate everyone
    - Admins can evaluate kepala sekolah
    - Kepala sekolah can evaluate teachers in their organization
    """
    return has_any_role(user, ["SUPER_ADMIN", "ADMIN", "KEPALA_SEKOLAH"])


def is_rpp_reviewer(user: Dict) -> bool:
    """Check if user can review RPP submissions."""
    return has_any_role(user, ["SUPER_ADMIN", "ADMIN"])


def can_manage_users(user: Dict) -> bool:
    """Check if user can manage other users."""
    return has_any_role(user, ["SUPER_ADMIN", "ADMIN"])


def can_manage_organization(user: Dict) -> bool:
    """Check if user can manage organization settings."""
    return has_any_role(user, ["SUPER_ADMIN", "ADMIN"])


def can_access_analytics(user: Dict) -> bool:
    """Check if user can access analytics and reports."""
    return has_any_role(user, ["SUPER_ADMIN", "ADMIN"])


# ===== ORGANIZATIONAL BOUNDARY CHECKS =====

def check_organization_access(current_user: Dict, target_organization_id: Optional[int]) -> bool:
    """
    Check if user has access to specific organization data.
    
    Rules:
    - Admin: Access to all organizations 
    - Others: Access only to their own organization
    """
    if is_admin(current_user):
        return True
    
    user_org_id = current_user.get("organization_id")
    return user_org_id == target_organization_id


def check_user_data_access(current_user: Dict, target_user_id: int, target_org_id: Optional[int] = None) -> bool:
    """
    Check if user has access to specific user data.
    
    Rules:
    - Kepala Sekolah: Access to users in same organization
    - Guru: Access only to own data
    """
    if is_admin(current_user):
        return True
    
    # Users can always access their own data
    if current_user.get("id") == target_user_id:
        return True
    
    # Kepala sekolah can access users in same organization
    if is_kepala_sekolah(current_user):
        return check_organization_access(current_user, target_org_id)
    
    return False


def check_rpp_access(current_user: Dict, rpp_teacher_id: int, rpp_org_id: Optional[int] = None) -> bool:
    """
    Check if user has access to specific RPP submission.
    
    Rules:
    - Kepala Sekolah: Access to RPPs in same organization
    - Guru: Access only to own RPPs
    """
    if  is_admin(current_user):
        return True
    
    # Teachers can access their own RPPs
    if is_guru(current_user) and current_user.get("id") == rpp_teacher_id:
        return True
    
    # Kepala sekolah can access RPPs in same organization
    if is_kepala_sekolah(current_user):
        return check_organization_access(current_user, rpp_org_id)
    
    return False


def check_evaluation_access(current_user: Dict, teacher_id: int, teacher_org_id: Optional[int] = None) -> bool:
    """
    Check if user has access to specific teacher evaluation.
    
    Rules:
    - Admin: Access to all evaluations (can evaluate kepala sekolah)
    - Kepala Sekolah: Access to evaluations in same organization + their own evaluation by admin
    - Guru: Access only to own evaluations
    """
    if is_admin(current_user):
        return True
    
    # Users can access their own evaluations (including kepala sekolah being evaluated by admin)
    if current_user.get("id") == teacher_id:
        return True
    
    # Kepala sekolah can access evaluations of teachers in same organization
    if is_kepala_sekolah(current_user):
        return check_organization_access(current_user, teacher_org_id)
    
    return False


# ===== RATE LIMITING BY ROLE =====

def get_rate_limit_by_role(user: Dict) -> int:
    """
    Get rate limit based on user role.
    """
    user_role = user.get("role")
    
    if user_role == "ADMIN":
        return 1000  # High limit for admins
    elif user_role == "KEPALA_SEKOLAH":
        return 500   # Medium limit for school principals
    elif user_role == "GURU":
        return 200   # Standard limit for teachers
    else:
        return 100   # Basic limit for other roles


# ===== SECURITY UTILITIES =====

async def log_access_attempt(user: Dict, resource: str, action: str = "access", success: bool = True):
    """
    Log access attempts for security monitoring.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    log_data = {
        "user_id": user.get("id"),
        "email": user.get("email"),
        "roles": user.get("roles", []),
        "organization_id": user.get("organization_id"),
        "resource": resource,
        "action": action,
        "success": success
    }
    
    if success:
        logger.info(f"PKG Access granted: {log_data}")
    else:
        logger.warning(f"PKG Access denied: {log_data}")


def require_rpp_submission_permission():
    """
    Require permission for RPP submission operations.
    Teachers can only submit/upload, principals can approve for their organization.
    """
    async def _check_rpp_permission(
        current_user: Dict = Depends(get_current_active_user),
    ) -> Dict:
        # Only teachers (guru) can submit RPPs
        if not is_guru(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers (guru) can submit RPP documents",
            )
        return current_user
    return _check_rpp_permission


def require_rpp_approval_permission():
    """
    Require permission for RPP approval operations.
    Only principals (kepala_sekolah) can approve RPPs for their organization.
    """
    async def _check_rpp_approval_permission(
        current_user: Dict = Depends(get_current_active_user),
    ) -> Dict:
        # admin can approve any RPP
        if is_admin(current_user):
            return current_user
        
        # Only kepala_sekolah can approve RPPs
        if not is_kepala_sekolah(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only school principals (kepala_sekolah) can approve RPP submissions",
            )
        return current_user
    return _check_rpp_approval_permission


def require_teacher_evaluation_view_permission():
    """
    Require permission for viewing teacher evaluations.
    Teachers can only view their own evaluations.
    """
    async def _check_evaluation_view_permission(
        current_user: Dict = Depends(get_current_active_user),
    ) -> Dict:
        # Everyone can view evaluations (access control handled at service level)
        return current_user
    return _check_evaluation_view_permission


def require_teacher_evaluation_update_permission():
    """
    Require permission for updating teacher evaluations.
    
    Rules:
    - Admin can update any evaluation (including kepala sekolah evaluations)
    - Kepala sekolah can update evaluations for teachers in their organization
    """
    async def _check_evaluation_update_permission(
        current_user: Dict = Depends(get_current_active_user),
    ) -> Dict:
        # Admin can update any evaluation (including kepala sekolah evaluations)
        if is_admin(current_user):
            return current_user
        
        # Kepala sekolah can update teacher evaluations in their organization
        if is_kepala_sekolah(current_user):
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or school principals can update teacher evaluations",
        )
    return _check_evaluation_update_permission


def get_user_permissions_summary(user: Dict) -> Dict[str, Any]:
    """
    Get a summary of user permissions for debugging/admin purposes.
    """
    roles = user.get("roles", [])
    
    return {
        "user_id": user.get("id"),
        "roles": roles,
        "organization_id": user.get("organization_id"),
        "can_submit_rpp": is_guru(user),
        "can_review_rpp": is_rpp_reviewer(user),
        "can_create_evaluations": is_evaluator(user),
        "can_manage_users": can_manage_users(user),
        "can_manage_organization": can_manage_organization(user),
        "can_manage_media": has_any_role(user, ["SUPER_ADMIN", "ADMIN"]),
        "can_access_analytics": can_access_analytics(user),
        "rate_limit": get_rate_limit_by_role(user)
    }


