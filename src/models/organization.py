"""Organization model based on DB.MD schema."""

from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from sqlalchemy import Enum as SQLEnum

from .base import BaseModel
from .enums import OrganizationType

if TYPE_CHECKING:
    from .user import User
    from .user_role import UserRole
    from .media_file import MediaFile


class Organization(BaseModel, SQLModel, table=True):
    """Organization model for schools, foundations, and departments."""
    
    __tablename__ = "organizations"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=255, nullable=False, index=True)
    slug: str = Field(max_length=255, unique=True, nullable=True, index=True)
    type: OrganizationType = Field(
        sa_column=Column(SQLEnum(OrganizationType), nullable=False, default=OrganizationType.SCHOOL),
        description="Type of organization: school, foundation, or department"
    )
    description: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None, max_length=255)
    website_url: Optional[str] = Field(default=None, max_length=255)
    
    # JSON fields for flexible data storage
    contact_info: Optional[dict] = Field(
        default=None, 
        sa_column=Column(JSON, comment="Contact details: phone, email, address, etc")
    )
    settings: Optional[dict] = Field(
        default=None, 
        sa_column=Column(JSON, comment="Organization-specific settings")
    )
    
    # Relationships (using TYPE_CHECKING for forward references)
    users: List["User"] = Relationship(back_populates="organization")
    user_roles: List["UserRole"] = Relationship(back_populates="organization")
    media_files: List["MediaFile"] = Relationship(back_populates="organization")
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, type={self.type.value})>"
    
    @property
    def display_name(self) -> str:
        """Get display name for the organization."""
        return self.name
    
    def get_contact_info(self, key: str) -> Optional[str]:
        """Get specific contact information."""
        if self.contact_info and isinstance(self.contact_info, dict):
            return self.contact_info.get(key)
        return None
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get specific organization setting."""
        if self.settings and isinstance(self.settings, dict):
            return self.settings.get(key)
        return None
    
    def update_contact_info(self, key: str, value: str) -> None:
        """Update contact information."""
        if self.contact_info is None:
            self.contact_info = {}
        self.contact_info[key] = value
    
    def update_setting(self, key: str, value: str) -> None:
        """Update organization setting."""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value