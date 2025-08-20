"""Authentication endpoints for unified schema system."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.config import settings
from src.repositories.user import UserRepository
from src.services.user import UserService
from src.services.auth import AuthService
from src.schemas.user import (
    UserLogin, Token, TokenRefresh, PasswordReset, PasswordResetConfirm,
    UserResponse, UserChangePassword
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import get_current_active_user
from src.utils.messages import get_message

router = APIRouter()


async def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Get auth service dependency."""
    user_repo = UserRepository(session)
    user_service = UserService(user_repo)
    return AuthService(user_service, user_repo)


@router.post("/login", response_model=Token, summary="Login user")
async def login(
    login_data: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login user with email and password.
    
    Returns access token, refresh token, and user information.
    Sets tokens as HttpOnly, Secure cookies.
    """
    token_response = await auth_service.login(login_data)
    
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=token_response.access_token,
        max_age=token_response.expires_in,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN
    )
    
    # Set refresh token cookie (longer expiration)
    response.set_cookie(
        key="refresh_token", 
        value=token_response.refresh_token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN
    )
    
    return token_response


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token from cookie.
    
    Returns new access token with updated user information.
    """
    # Get refresh token from cookie only
    refresh_token_str = request.cookies.get("refresh_token")
    
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found. Please login again."
        )
    
    token_response = await auth_service.refresh_token(refresh_token_str)
    
    # Update access token cookie
    response.set_cookie(
        key="access_token",
        value=token_response.access_token,
        max_age=token_response.expires_in,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN
    )
    
    return token_response


@router.post("/logout", response_model=MessageResponse, summary="Logout user")
async def logout(
    response: Response,
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current user.
    
    Clears authentication cookies.
    """
    # Clear cookies
    response.delete_cookie(
        key="access_token", 
        httponly=True, 
        secure=settings.COOKIE_SECURE, 
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN
    )
    response.delete_cookie(
        key="refresh_token", 
        httponly=True, 
        secure=settings.COOKIE_SECURE, 
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN
    )
    
    return await auth_service.logout()


@router.get("/me", response_model=UserResponse, summary="Get current user info")
async def get_current_user(
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current authenticated user information.
    
    Returns detailed user profile including roles and organization.
    """
    return await auth_service.get_current_user_info(current_user["id"])


@router.post("/password-reset", response_model=MessageResponse, summary="Request password reset")
async def request_password_reset(
    reset_data: PasswordReset,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset via email.
    
    Sends password reset link to user's email if account exists.
    Always returns success message to prevent email enumeration.
    """
    return await auth_service.request_password_reset(reset_data)


@router.post("/password-reset/confirm", response_model=MessageResponse, summary="Confirm password reset")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Confirm password reset with token.
    
    Validates reset token and updates user password.
    """
    return await auth_service.confirm_password_reset(reset_data)


@router.post("/change-password", response_model=MessageResponse, summary="Change current user password")
async def change_password(
    password_data: UserChangePassword,
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password.
    
    Requires current password verification.
    """
    user_service = UserService(UserRepository(db))
    return await user_service.change_password(current_user["id"], password_data)


@router.get("/password-reset/eligibility/{user_id}", summary="Check password reset eligibility")
async def check_password_reset_eligibility(
    user_id: int,
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Check if user is eligible for password reset.
    
    Requires admin role or user checking their own eligibility.
    """
    # Check if user is admin or checking their own eligibility
    if current_user["id"] != user_id and current_user.get("role") not in ["SUPER_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_message("auth", "not_authorized_check_password_reset")
        )
    
    return await auth_service.check_password_reset_eligibility(user_id)


@router.get("/default-password-info", summary="Get default password info")
async def get_default_password_info(
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get information about default password.
    
    Requires admin role.
    """
    if current_user.get("role") not in ["SUPER_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_message("auth", "admin_role_required")
        )
    
    return await auth_service.get_default_password_info()


@router.post("/validate-access", summary="Validate user access")
async def validate_user_access(
    required_roles: list[str] = None,
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Validate if current user has required access.
    
    Optionally check for specific roles.
    """
    has_access = await auth_service.validate_user_access(
        current_user["id"], 
        required_roles
    )
    
    return {
        "user_id": current_user["id"],
        "has_access": has_access,
        "required_roles": required_roles,
        "user_role": current_user.get("role", "")
    }