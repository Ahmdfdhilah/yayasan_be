"""Unified User model based on DB.MD schema."""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import uuid as uuid_lib
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from sqlalchemy import Enum as SQLEnum

from .base import BaseModel
from .enums import UserStatus

if TYPE_CHECKING:
    from .organization import Organization
    from .user_role import UserRole
    from .media_file import MediaFile
    from .rpp_submission import RPPSubmission
    from .teacher_evaluation import TeacherEvaluation


class User(BaseModel, SQLModel, table=True):
    """Unified User model for all system users."""
    
    __tablename__ = "users"
    
    id: int = Field(primary_key=True)
    email: str = Field(max_length=255, unique=True, nullable=False, index=True)
    password: str = Field(nullable=False, description="Hashed password")
    
    # JSON profile data for flexible user information
    profile: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="User profile: name, phone, address, etc"
    )
    
    # Organization relationship
    organization_id: Optional[int] = Field(
        default=None, 
        foreign_key="organizations.id",
        index=True
    )
    
    # Status and authentication
    status: UserStatus = Field(
        sa_column=Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE),
        description="User status: active, inactive, or suspended"
    )
    email_verified_at: Optional[datetime] = Field(default=None)
    last_login_at: Optional[datetime] = Field(default=None)
    remember_token: Optional[str] = Field(default=None, max_length=100)
    
    # Relationships
    organization: Optional["Organization"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"foreign_keys": "User.organization_id"}
    )
    user_roles: List["UserRole"] = Relationship(back_populates="user")
    uploaded_files: List["MediaFile"] = Relationship(back_populates="uploader")
    
    # PKG System relationships - with explicit foreign_keys for SQLAlchemy
    submitted_rpps: List["RPPSubmission"] = Relationship(
        back_populates="teacher",
        sa_relationship_kwargs={"foreign_keys": "RPPSubmission.teacher_id"}
    )
    reviewed_rpps: List["RPPSubmission"] = Relationship(
        back_populates="reviewer",
        sa_relationship_kwargs={"foreign_keys": "RPPSubmission.reviewer_id"}
    )
    conducted_evaluations: List["TeacherEvaluation"] = Relationship(
        back_populates="evaluator",
        sa_relationship_kwargs={"foreign_keys": "TeacherEvaluation.evaluator_id"}
    )
    received_evaluations: List["TeacherEvaluation"] = Relationship(
        back_populates="teacher",
        sa_relationship_kwargs={"foreign_keys": "TeacherEvaluation.teacher_id"}
    )
  
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, status={self.status.value})>"
    
    @property
    def display_name(self) -> str:
        """Get display name from profile."""
        if self.profile and isinstance(self.profile, dict):
            return self.profile.get("name", self.email)
        return self.email
    
    @property
    def full_name(self) -> str:
        """Get full name from profile."""
        if self.profile and isinstance(self.profile, dict):
            return self.profile.get("name", "")
        return ""
    
    @property
    def phone(self) -> Optional[str]:
        """Get phone from profile."""
        if self.profile and isinstance(self.profile, dict):
            return self.profile.get("phone")
        return None
    
    @property
    def address(self) -> Optional[str]:
        """Get address from profile."""
        if self.profile and isinstance(self.profile, dict):
            return self.profile.get("address")
        return None
    
    def has_email_verified(self) -> bool:
        """Check if user has verified email."""
        return self.email_verified_at is not None
    
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE
    
    def is_suspended(self) -> bool:
        """Check if user is suspended."""
        return self.status == UserStatus.SUSPENDED
    
    def get_profile_field(self, key: str) -> Optional[str]:
        """Get specific profile field."""
        if self.profile and isinstance(self.profile, dict):
            return self.profile.get(key)
        return None
    
    def update_profile_field(self, key: str, value: str) -> None:
        """Update specific profile field."""
        if self.profile is None:
            self.profile = {}
        self.profile[key] = value
    
    def get_roles(self) -> List[str]:
        """Get all role names for this user."""
        return [role.role_name for role in self.user_roles if role.is_active]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role."""
        return role_name in self.get_roles()
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        for role in self.user_roles:
            if role.is_active and role.permissions and isinstance(role.permissions, dict):
                if permission in role.permissions:
                    return True
        return False


class PasswordResetToken(BaseModel, SQLModel, table=True):
    """Password reset token model for unified schema."""
    
    __tablename__ = "password_reset_tokens"
    
    id: str = Field(
        default_factory=lambda: str(uuid_lib.uuid4()),
        primary_key=True,
        max_length=36
    )
    user_id: int = Field(foreign_key="users.id", index=True)  # Changed to int
    token: str = Field(unique=True, index=True, max_length=255)
    expires_at: datetime
    used: bool = Field(default=False)
    used_at: Optional[datetime] = Field(default=None)
    
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self) -> None:
        """Mark token as used."""
        self.used = True
        self.used_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<PasswordResetToken(user_id={self.user_id}, used={self.used})>"