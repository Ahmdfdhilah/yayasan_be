"""Database models initialization - Updated to match DB.MD schema."""

# Base classes
from .base import BaseModel, TimestampMixin, AuditMixin, SoftDeleteMixin

# Core models
from .user import User, PasswordResetToken
from .organization import Organization
from .user_role import UserRole
from .media_file import MediaFile

# PKG System models
from .rpp_submission import RPPSubmission
from .evaluation_aspect import EvaluationAspect
from .teacher_evaluation import TeacherEvaluation
from .evaluation_result import EvaluationResult

# Enums
from .enums import (
    UserRole as UserRoleEnum,
    UserStatus,
    OrganizationType,
    RPPStatus,
    EvaluationGrade,
    ContentStatus,
    MessageStatus,
    MessagePriority,
    AuditAction,
    SystemSettingDataType,
)

__all__ = [
    # Base classes
    "BaseModel",
    "TimestampMixin", 
    "AuditMixin",
    "SoftDeleteMixin",
    
    # Core models
    "User",
    "PasswordResetToken",
    "Organization",
    "UserRole",
    "MediaFile",
    
    # PKG System models
    "RPPSubmission",
    "EvaluationAspect",
    "TeacherEvaluation",
    "EvaluationResult",
    
    # Enums
    "UserRoleEnum",
    "UserStatus",
    "OrganizationType",
    "RPPStatus",
    "EvaluationGrade",
    "ContentStatus",
    "MessageStatus",
    "MessagePriority",
    "AuditAction",
    "SystemSettingDataType",
]