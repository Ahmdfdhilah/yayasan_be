"""Organization model based on DB.MD schema."""

from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from sqlalchemy import Enum as SQLEnum

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .user_role import UserRole
    from .media_file import MediaFile


class Organization(BaseModel, SQLModel, table=True):
    """Organization model for schools."""
    
    __tablename__ = "organizations"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=255, nullable=False, index=True)
    description: Optional[str] = Field(default=None)
    
    # Head/Principal of the organization
    head_id: Optional[int] = Field(
        default=None, 
        foreign_key="users.id",
        index=True,
        description="The head/principal of the organization"
    )
    
    # Relationships (using TYPE_CHECKING for forward references)
    head: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Organization.head_id"}
    )
    users: List["User"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"foreign_keys": "User.organization_id"}
    )
    user_roles: List["UserRole"] = Relationship(back_populates="organization")
    media_files: List["MediaFile"] = Relationship(back_populates="organization")
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
    
    @property
    def display_name(self) -> str:
        """Get display name for the organization."""
        return self.name