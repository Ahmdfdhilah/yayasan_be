"""Database models initialization - Updated to match DB.MD schema."""

# Base classes
from .base import BaseModel, TimestampMixin, AuditMixin, SoftDeleteMixin

# Core models
from .user import User, PasswordResetToken
from .organization import Organization
from .user_role import UserRole
from .media_file import MediaFile

# PKG System models
from .period import Period
from .rpp_submission import RPPSubmission
from .rpp_submission_item import RPPSubmissionItem
from .evaluation_aspect import EvaluationAspect
from .teacher_evaluation import TeacherEvaluation

# Enums
from .enums import (
    UserRole as UserRoleEnum,
    UserStatus,
    RPPType,
    RPPSubmissionStatus,
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
    "Period",
    "RPPSubmission",
    "RPPSubmissionItem",
    "EvaluationAspect",
    "TeacherEvaluation",
    
    # Enums
    "UserRoleEnum",
    "UserStatus",
    "RPPType",
    "RPPSubmissionStatus",
    "EvaluationGrade",
    "ContentStatus",
    "MessageStatus",
    "MessagePriority",
    "AuditAction",
    "SystemSettingDataType",
]