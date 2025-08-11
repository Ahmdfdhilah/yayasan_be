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

# RPP Submission schemas
from .rpp_submission import (
    RPPSubmissionBase,
    RPPSubmissionCreate,
    RPPSubmissionUpdate,
    RPPSubmissionResponse,
    RPPSubmissionItemBase,
    RPPSubmissionItemCreate,
    RPPSubmissionItemUpdate,
    RPPSubmissionItemResponse,
    RPPSubmissionSubmitRequest,
    RPPSubmissionReviewRequest,
    GenerateRPPSubmissionsRequest,
    GenerateRPPSubmissionsResponse,
    RPPSubmissionListResponse,
    RPPSubmissionItemListResponse,
    RPPSubmissionFilter,
    RPPSubmissionItemFilter,
    RPPSubmissionStats,
    RPPSubmissionDashboard,
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
    
    # Filters (now from individual schema files)
    "UserFilterParams",
    "UsernameGenerationPreview", 
    "UsernameGenerationResponse",
    "PaginationParams",
    "SearchParams",
    "DateRangeFilter",
    
    # RPP Submission
    "RPPSubmissionBase",
    "RPPSubmissionCreate",
    "RPPSubmissionUpdate",
    "RPPSubmissionResponse",
    "RPPSubmissionItemBase",
    "RPPSubmissionItemCreate",
    "RPPSubmissionItemUpdate",
    "RPPSubmissionItemResponse",
    "RPPSubmissionSubmitRequest",
    "RPPSubmissionReviewRequest",
    "GenerateRPPSubmissionsRequest",
    "GenerateRPPSubmissionsResponse",
    "RPPSubmissionListResponse",
    "RPPSubmissionItemListResponse",
    "RPPSubmissionFilter",
    "RPPSubmissionItemFilter",
    "RPPSubmissionStats",
    "RPPSubmissionDashboard",
]