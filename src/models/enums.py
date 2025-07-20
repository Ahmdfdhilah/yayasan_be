"""Enums untuk database models - Updated to match DB.MD schema."""

from enum import Enum


class UserRole(str, Enum):
    """User role enum for role-based access control."""
    ADMIN = "admin"
    GURU = "guru"
    KEPALA_SEKOLAH = "kepala_sekolah"
    
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


class RPPType(str, Enum):
    """RPP type enum for the 3 required RPP types."""
    RENCANA_PROGRAM_HARIAN = "RENCANA_PROGRAM_HARIAN"
    RENCANA_PROGRAM_SEMESTER = "RENCANA_PROGRAM_SEMESTER"
    RENCANA_PROGRAM_TAHUNAN = "RENCANA_PROGRAM_TAHUNAN"
    
    @classmethod
    def get_all_values(cls):
        """Get all RPP type values as list."""
        return [rpp_type.value for rpp_type in cls]
    
    @classmethod
    def get_display_names(cls):
        """Get display names for RPP types."""
        return {
            cls.RENCANA_PROGRAM_HARIAN.value: "Rencana Program Harian",
            cls.RENCANA_PROGRAM_SEMESTER.value: "Rencana Program Semester", 
            cls.RENCANA_PROGRAM_TAHUNAN.value: "Rencana Program Tahunan"
        }


class RPPSubmissionStatus(str, Enum):
    """RPP submission status enum."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    @classmethod
    def get_all_values(cls):
        """Get all status values as list."""
        return [status.value for status in cls]


class EvaluationGrade(str, Enum):
    """Evaluation grade enum for simplified scoring system."""
    A = "A"  # Excellent - 4 points
    B = "B"  # Good - 3 points  
    C = "C"  # Satisfactory - 2 points
    D = "D"  # Needs Improvement - 1 point
    
    @classmethod
    def get_score(cls, grade: str) -> int:
        """Get numeric score for grade."""
        score_map = {
            cls.A.value: 4,
            cls.B.value: 3,
            cls.C.value: 2,
            cls.D.value: 1
        }
        return score_map.get(grade, 0)
    
    @classmethod
    def get_description(cls, grade: str) -> str:
        """Get description for grade."""
        desc_map = {
            cls.A.value: "Excellent",
            cls.B.value: "Good", 
            cls.C.value: "Satisfactory",
            cls.D.value: "Needs Improvement"
        }
        return desc_map.get(grade, "Unknown")



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