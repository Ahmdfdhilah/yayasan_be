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
    PerwadagSummary,
    PerwadagListResponse,
)

# Filter schemas
from .filters import (
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
    "PerwadagSummary",
    "PerwadagListResponse",
    
    # Filters
    "UserFilterParams",
    "UsernameGenerationPreview", 
    "UsernameGenerationResponse",
    "PaginationParams",
    "SearchParams",
    "DateRangeFilter",
]