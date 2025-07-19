"""Schemas initialization."""

# Shared schemas
from .shared import (
    BaseListResponse,
    MessageResponse,
    ErrorResponse,
    SuccessResponse,
    StatusResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)

# User schemas
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserChangePassword,
    UserResponse,
    UserListResponse,
    UserSummary,
    UserLogin,
    Token,
    TokenRefresh,
    PasswordReset,
    PasswordResetConfirm,
    UserRoleCreate,
    UserRoleUpdate,
    UserRoleResponse,
)

# Filter schemas moved to individual schema files
from .user import (
    UserFilterParams,
    UsernameGenerationPreview,
    UsernameGenerationResponse,
    PaginationParams,
    SearchParams,
    DateRangeFilter,
)

# Common schemas
from .common import *

__all__ = [
    # Shared
    "BaseListResponse",
    "MessageResponse",
    "ErrorResponse",
    "SuccessResponse",
    "StatusResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserChangePassword",
    "UserResponse",
    "UserListResponse",
    "UserSummary",
    "UserLogin",
    "Token",
    "TokenRefresh",
    "PasswordReset",
    "PasswordResetConfirm",
    "UserRoleCreate",
    "UserRoleUpdate",
    "UserRoleResponse",
    
    # Filters (now from individual schema files)
    "UserFilterParams",
    "UsernameGenerationPreview", 
    "UsernameGenerationResponse",
    "PaginationParams",
    "SearchParams",
    "DateRangeFilter",
]