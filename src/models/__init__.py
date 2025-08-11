"""Database models initialization - Updated to match DB.MD schema."""

# Base classes
from .base import BaseModel, TimestampMixin, AuditMixin, SoftDeleteMixin

# Core models
from .user import User, PasswordResetToken
from .organization import Organization
from .media_file import MediaFile
from .article import Article
from .board_member import BoardMember
from .board_group import BoardGroup
from .gallery import Gallery
from .message import Message, MessageStatus
from .mitra import Mitra
from .program import Program

# PKG System models
from .period import Period
from .rpp_submission import RPPSubmission
from .rpp_submission_item import RPPSubmissionItem
from .evaluation_category import EvaluationCategory
from .evaluation_aspect import EvaluationAspect
from .teacher_evaluation import TeacherEvaluation
from .teacher_evaluation_item import TeacherEvaluationItem

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
    "MediaFile",
    "Article",
    "BoardMember",
    "BoardGroup",
    "Gallery",
    "Message",
    "MessageStatus",
    "Mitra",
    "Program",
    
    # PKG System models
    "Period",
    "RPPSubmission",
    "RPPSubmissionItem",
    "EvaluationCategory",
    "EvaluationAspect",
    "TeacherEvaluation",
    "TeacherEvaluationItem",
    
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