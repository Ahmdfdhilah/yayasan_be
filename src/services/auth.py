"""Authentication service for unified schema system."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status

from src.repositories.user import UserRepository
from src.services.user import UserService
from src.schemas.user import (
    UserLogin, Token, PasswordReset, PasswordResetConfirm, 
    UserResponse
)
from src.schemas.shared import MessageResponse
from src.auth.jwt import create_access_token, create_refresh_token, verify_token
from src.services.email import EmailService
from src.utils.password import generate_password_reset_token, mask_email
from src.core.config import settings
from src.utils.messages import get_message


class AuthService:
    """Authentication service for unified schema system."""
    
    def __init__(self, user_service: UserService, user_repo: UserRepository):
        self.user_service = user_service
        self.user_repo = user_repo
        self.email_service = EmailService()
    
    async def login(self, login_data: UserLogin) -> Token:
        """Login user with email and password."""
        # Authenticate user
        user = await self.user_service.authenticate_user(
            login_data.email,
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("auth", "invalid_credentials"),
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token data with user roles
        user_roles_entities = await self.user_repo.get_user_roles(user.id)
        user_roles = [role.role_name for role in user_roles_entities if role.is_active]
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.full_name,
            "roles": user_roles,
            "organization_id": user.organization_id,
            "type": "access"
        }
        
        refresh_token_data = {
            "sub": str(user.id),
            "type": "refresh"
        }
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(data=refresh_token_data)
        
        # Build user response
        user_response = UserResponse.from_user_model(user, user_roles)
        
        # Return token response
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        try:
            # Verify refresh token
            payload = verify_token(refresh_token)
            
            # Check token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=get_message("auth", "invalid_token")
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=get_message("auth", "invalid_token")
                )
            
            # Get user
            user = await self.user_repo.get_by_id(int(user_id))
            if not user or not user.is_active():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=get_message("user", "not_found")
                )
            
            # Get user roles
            user_roles_entities = await self.user_repo.get_user_roles(user.id)
            user_roles = [role.role_name for role in user_roles_entities if role.is_active]
            
            # Create new access token
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "name": user.full_name,
                "roles": user_roles,
                "organization_id": user.organization_id,
                "type": "access"
            }
            
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data=token_data,
                expires_delta=access_token_expires
            )
            
            user_response = UserResponse.from_user_model(user, user_roles)
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,  # Keep the same refresh token
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=user_response
            )
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("auth", "refresh_token_expired")
            )
    
    async def request_password_reset(self, reset_data: PasswordReset) -> MessageResponse:
        """Request password reset token with email validation."""
        import logging
        logger = logging.getLogger(__name__)
        
        user = await self.user_repo.get_by_email(reset_data.email)
        
        # Always return success message to prevent email enumeration
        success_message = "If the email exists and is associated with an account, a password reset link has been sent"
        
        # Case 1: Email not found
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {mask_email(reset_data.email)}")
            return MessageResponse(message=success_message)
        
        # Case 2: User not active
        if not user.is_active():
            logger.warning(f"Password reset requested for inactive user: {user.full_name} ({mask_email(reset_data.email)})")
            return MessageResponse(message=success_message)
        
        # Case 3: User active but no email (edge case)
        if not user.email:
            logger.warning(f"Password reset requested for user without email: {user.full_name}")
            return MessageResponse(
                message="User account does not have email configured. Please contact administrator."
            )
        
        # Case 4: All validation passed - process reset
        logger.info(f"Processing password reset for user: {user.full_name} ({mask_email(user.email)})")
        
        # Generate reset token
        token = generate_password_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        
        # Save token to database
        try:
            await self.user_repo.create_password_reset_token(
                user.id,
                token,
                expires_at
            )
            logger.info(f"Password reset token created for user: {user.full_name}")
        except Exception as e:
            logger.error(f"Failed to create password reset token for {mask_email(user.email)}: {str(e)}")
            return MessageResponse(
                message="Failed to process password reset request. Please try again later.",
                success=False
            )
        
        # Send email with reset link
        try:
            email_sent = await self.email_service.send_password_reset_email(
                user_email=user.email,
                user_nama=user.full_name,
                reset_token=token
            )
            
            if email_sent:
                logger.info(f"Password reset email sent successfully to {mask_email(user.email)}")
            else:
                logger.error(f"Failed to send password reset email to {mask_email(user.email)}")
                
        except Exception as e:
            logger.error(f"Exception while sending password reset email to {mask_email(user.email)}: {str(e)}")
        
        return MessageResponse(message=success_message)
    
    async def confirm_password_reset(self, reset_data: PasswordResetConfirm) -> MessageResponse:
        """Confirm password reset with token and send success email."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Get and validate token
        reset_token = await self.user_repo.get_password_reset_token(reset_data.token)
        
        if not reset_token or not reset_token.is_valid():
            logger.warning(f"Invalid or expired reset token used: {reset_data.token[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Get user
        user = await self.user_repo.get_by_id(reset_token.user_id)
        if not user:
            logger.error(f"User not found for reset token: {reset_token.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if new password is different from current
        from src.auth.jwt import verify_password, get_password_hash
        if verify_password(reset_data.new_password, user.password):
            logger.warning(f"User {user.full_name} tried to reset password with same password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        # Update password
        new_hashed_password = get_password_hash(reset_data.new_password)
        
        try:
            await self.user_repo.update_password(user.id, new_hashed_password)
            logger.info(f"Password updated successfully for user: {user.full_name} ({mask_email(user.email)})")
        except Exception as e:
            logger.error(f"Failed to update password for user {user.full_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password. Please try again."
            )
        
        # Mark token as used
        try:
            await self.user_repo.use_password_reset_token(reset_data.token)
            logger.info(f"Reset token marked as used: {reset_data.token[:8]}...")
        except Exception as e:
            logger.error(f"Failed to mark reset token as used: {str(e)}")
        
        # Send success confirmation email
        if user.email:
            try:
                email_sent = await self.email_service.send_password_reset_success_email(
                    user_email=user.email,
                    user_nama=user.full_name
                )
                
                if email_sent:
                    logger.info(f"Password reset success email sent to {mask_email(user.email)}")
                else:
                    logger.error(f"Failed to send success email to {mask_email(user.email)}")
                    
            except Exception as e:
                logger.error(f"Exception while sending success email to {mask_email(user.email)}: {str(e)}")
        
        return MessageResponse(message="Password reset successful")
    
    async def logout(self) -> MessageResponse:
        """Logout user (simple version without session management)."""
        # In a simple JWT implementation, logout is handled client-side
        # by discarding the token. In more advanced implementations,
        # you might want to blacklist the token.
        return MessageResponse(message="Logged out successfully")
    
    async def get_current_user_info(self, user_id: int) -> UserResponse:
        """Get current user information."""
        user = await self.user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    async def validate_user_access(self, user_id: int, required_roles: Optional[list] = None) -> bool:
        """Validate if user has required access."""
        user = await self.user_repo.get_by_id(user_id)
        
        if not user or not user.is_active():
            return False
        
        if required_roles:
            user_roles = user.get_roles()
            return any(role in user_roles for role in required_roles)
        
        return True
    
    async def check_password_reset_eligibility(self, user_id: int) -> dict:
        """Check if user is eligible for password reset."""
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        has_email = bool(user.email)
        
        return {
            "eligible": has_email,
            "has_email": has_email,
            "email": user.email if has_email else None,
            "message": "User can request password reset" if has_email else "User must set email first before requesting password reset"
        }
    
    async def get_default_password_info(self) -> dict:
        """Get information about default password (for admin reference)."""
        return {
            "default_password": "@Kemendag123",
            "description": "Default password for all new users",
            "recommendation": "Users should change this password after first login",
            "policy": "Password must be changed if user wants to use password reset feature"
        }