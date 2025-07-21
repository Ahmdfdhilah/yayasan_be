"""User management endpoints for unified schema system."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.user import UserRepository
from src.services.user import UserService
from src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserSummary,
    UserChangePassword,
    UserRoleCreate,
    UserRoleUpdate,
    UserRoleResponse,
)
from src.schemas.shared import MessageResponse
from src.schemas.user import UserFilterParams
from src.auth.permissions import get_current_active_user, require_roles
from src.utils.messages import get_message

router = APIRouter()

# Dependency for admin-only endpoints
admin_required = require_roles(["admin"])

# Dependency for admin and manager endpoints
admin_or_manager = require_roles(["admin", "kepala_sekolah"])


async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service dependency."""
    user_repo = UserRepository(session)
    return UserService(user_repo)


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_my_profile(
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current user's own profile information.

    Returns detailed profile including roles and organization info.
    """
    return await user_service.get_user(current_user["id"])


@router.put("/me", response_model=UserResponse, summary="Update current user profile")
async def update_my_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update current user's own profile information.

    Users can only update their own profile data (not roles or organization).
    """
    # Users cannot change their own status or organization
    user_data.status = None
    user_data.organization_id = None

    return await user_service.update_user(current_user["id"], user_data)


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    summary="Change current user password",
)
async def change_my_password(
    password_data: UserChangePassword,
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Change current user's password.

    Requires current password for verification.
    """
    return await user_service.change_password(current_user["id"], password_data)


@router.get("/me/profile/{field_name}", summary="Get specific profile field")
async def get_my_profile_field(
    field_name: str,
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get specific field from current user's profile."""
    value = await user_service.get_user_profile_field(current_user["id"], field_name)
    return {"field_name": field_name, "value": value}


@router.put(
    "/me/profile/{field_name}",
    response_model=UserResponse,
    summary="Update specific profile field",
)
async def update_my_profile_field(
    field_name: str,
    field_value: dict,
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update specific field in current user's profile."""
    value = field_value.get("value", "")
    return await user_service.update_user_profile_field(
        current_user["id"], field_name, value
    )


# ===== ADMIN USER MANAGEMENT =====


@router.get(
    "",
    response_model=UserListResponse,
    dependencies=[Depends(admin_or_manager)],
    summary="List all users",
)
async def list_users(
    filters: UserFilterParams = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """
    List all users with filtering and pagination.

    Requires admin or manager role.
    """
    return await user_service.get_all_users_with_filters(filters)


@router.post(
    "",
    response_model=UserResponse,
    dependencies=[Depends(admin_required)],
    summary="Create new user",
)
async def create_user(
    user_data: UserCreate,
    organization_id: Optional[int] = Query(
        None, description="Organization ID for the user"
    ),
    user_service: UserService = Depends(get_user_service),
):
    """
    Create a new user.

    Requires admin role.
    """
    return await user_service.create_user(user_data, organization_id)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(get_current_active_user)],
    summary="Get user by ID",
)
async def get_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    """
    Get user by ID.

    Requires admin or manager role.
    """
    return await user_service.get_user(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(admin_required)],
    summary="Update user",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """
    Update user information.

    Requires admin role.
    """
    return await user_service.update_user(user_id, user_data)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    dependencies=[Depends(admin_required)],
    summary="Delete user",
)
async def delete_user(
    user_id: int, user_service: UserService = Depends(get_user_service)
):
    """
    Soft delete user.

    Requires admin role.
    """
    return await user_service.delete_user(user_id)


@router.post(
    "/{user_id}/reset-password",
    response_model=MessageResponse,
    dependencies=[Depends(admin_required)],
    summary="Reset user password",
)
async def reset_user_password(
    user_id: int, user_service: UserService = Depends(get_user_service)
):
    """
    Reset user password to default.

    Requires admin role.
    """
    return await user_service.reset_user_password(user_id)


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    dependencies=[Depends(admin_required)],
    summary="Activate user",
)
async def activate_user(
    user_id: int, user_service: UserService = Depends(get_user_service)
):
    """
    Activate user account.

    Requires admin role.
    """
    return await user_service.activate_user(user_id)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    dependencies=[Depends(admin_required)],
    summary="Deactivate user",
)
async def deactivate_user(
    user_id: int, user_service: UserService = Depends(get_user_service)
):
    """
    Deactivate user account.

    Requires admin role.
    """
    return await user_service.deactivate_user(user_id)


@router.post(
    "/{user_id}/suspend",
    response_model=UserResponse,
    dependencies=[Depends(admin_required)],
    summary="Suspend user",
)
async def suspend_user(
    user_id: int, user_service: UserService = Depends(get_user_service)
):
    """
    Suspend user account.

    Requires admin role.
    """
    return await user_service.suspend_user(user_id)


# ===== USER PROFILE MANAGEMENT =====


@router.put(
    "/{user_id}/profile",
    response_model=UserResponse,
    dependencies=[Depends(admin_required)],
    summary="Update user profile",
)
async def update_user_profile(
    user_id: int,
    profile_data: Dict[str, Any],
    user_service: UserService = Depends(get_user_service),
):
    """
    Update user profile data.

    Requires admin role.
    """
    return await user_service.update_user_profile(user_id, profile_data)


@router.get(
    "/{user_id}/profile/{field_name}",
    dependencies=[Depends(admin_or_manager)],
    summary="Get user profile field",
)
async def get_user_profile_field(
    user_id: int, field_name: str, user_service: UserService = Depends(get_user_service)
):
    """
    Get specific field from user profile.

    Requires admin or manager role.
    """
    value = await user_service.get_user_profile_field(user_id, field_name)
    return {"user_id": user_id, "field_name": field_name, "value": value}


@router.put(
    "/{user_id}/profile/{field_name}",
    response_model=UserResponse,
    dependencies=[Depends(admin_required)],
    summary="Update user profile field",
)
async def update_user_profile_field(
    user_id: int,
    field_name: str,
    field_value: dict,
    user_service: UserService = Depends(get_user_service),
):
    """
    Update specific field in user profile.

    Requires admin role.
    """
    value = field_value.get("value", "")
    return await user_service.update_user_profile_field(user_id, field_name, value)


# ===== USER STATISTICS =====


@router.get(
    "/statistics/overview",
    dependencies=[Depends(admin_or_manager)],
    summary="Get user statistics",
)
async def get_user_statistics(user_service: UserService = Depends(get_user_service)):
    """
    Get user statistics overview.

    Requires admin or manager role.
    """
    return await user_service.get_user_statistics()


@router.get(
    "/by-role/{role_name}",
    response_model=list[UserResponse],
    dependencies=[Depends(admin_or_manager)],
    summary="Get users by role",
)
async def get_users_by_role(
    role_name: str, user_service: UserService = Depends(get_user_service)
):
    """
    Get all users with specific role.

    Requires admin or manager role.
    """
    return await user_service.get_users_by_role(role_name)


# ===== EMAIL SEARCH =====


@router.get(
    "/search/by-email",
    response_model=UserResponse,
    dependencies=[Depends(admin_or_manager)],
    summary="Find user by email",
)
async def find_user_by_email(
    email: str = Query(..., description="Email address to search"),
    user_service: UserService = Depends(get_user_service),
):
    """
    Find user by email address.

    Requires admin or manager role.
    """
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=get_message("user", "not_found")
        )
    return user
