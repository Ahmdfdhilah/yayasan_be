"""Enums untuk database models - Updated to match DB.MD schema."""

from enum import Enum


class UserRole(str, Enum):
    """User role enum for role-based access control."""
    ADMIN = "admin"
    GURU = "guru"
    KEPALA_SEKOLAH = "kepala_sekolah"
    CONTENT_MANAGER = "content_manager"
    SUPER_ADMIN = "super_admin"
    
    @classmethod
    def get_all_values(cls):
        """Get all role values as list."""
        return [role.value for role in cls]
    
    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """Check if role is valid."""
        return role in cls.get_all_values()


class UserStatus(str, Enum):
    """User status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class OrganizationType(str, Enum):
    """Organization type enum."""
    SCHOOL = "school"
    FOUNDATION = "foundation"
    DEPARTMENT = "department"


class RPPStatus(str, Enum):
    """RPP submission status enum."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_NEEDED = "revision_needed"


class EvaluationGrade(str, Enum):
    """Evaluation grade category enum."""
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"


class ContentStatus(str, Enum):
    """Content status enum."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"


class MessageStatus(str, Enum):
    """Contact message status enum."""
    NEW = "new"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"
    SPAM = "spam"


class MessagePriority(str, Enum):
    """Contact message priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AuditAction(str, Enum):
    """Audit log action enum."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class SystemSettingDataType(str, Enum):
    """System setting data type enum."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"