"""Database models initialization - Updated to match DB.MD schema."""

# Base classes
from .base import BaseModel, TimestampMixin, AuditMixin, SoftDeleteMixin

# Core models
from .user import User, PasswordResetToken
from .organization import Organization
from .user_role import UserRole
from .media_file import MediaFile

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