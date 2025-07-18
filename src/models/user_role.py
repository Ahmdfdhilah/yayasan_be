"""UserRole model for Role-based Access Control (RBAC)."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, JSON, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .organization import Organization


class UserRole(BaseModel, SQLModel, table=True):
    """User Role model for role-based access control."""
    
    __tablename__ = "user_roles"
    
    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    role_name: str = Field(
        max_length=50, 
        nullable=False, 
        index=True,
        description="Role name: admin, guru, kepala_sekolah, content_manager, etc"
    )
    
    # JSON field for specific permissions
    permissions: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, comment="Specific permissions for the role")
    )
    
    # Organization context
    organization_id: Optional[int] = Field(
        default=None,
        foreign_key="organizations.id",
        index=True
    )
    
    # Role status and expiration
    is_active: bool = Field(default=True)
    expires_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    user: "User" = Relationship(back_populates="user_roles")
    organization: Optional["Organization"] = Relationship(back_populates="user_roles")
    
    def __repr__(self) -> str:
        return f"<UserRole(id={self.id}, user_id={self.user_id}, role={self.role_name})>"
    
    def is_expired(self) -> bool:
        """Check if role has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if role is valid (active and not expired)."""
        return self.is_active and not self.is_expired()
    
    def has_permission(self, permission: str) -> bool:
        """Check if this role has specific permission."""
        if not self.is_valid():
            return False
        
        if self.permissions and isinstance(self.permissions, dict):
            return permission in self.permissions
        return False
    
    def get_permission_value(self, permission: str) -> Optional[str]:
        """Get specific permission value."""
        if not self.is_valid():
            return None
        
        if self.permissions and isinstance(self.permissions, dict):
            return self.permissions.get(permission)
        return None
    
    def add_permission(self, permission: str, value: str = "allow") -> None:
        """Add permission to this role."""
        if self.permissions is None:
            self.permissions = {}
        self.permissions[permission] = value
    
    def remove_permission(self, permission: str) -> None:
        """Remove permission from this role."""
        if self.permissions and isinstance(self.permissions, dict):
            self.permissions.pop(permission, None)
    
    def get_all_permissions(self) -> dict:
        """Get all permissions for this role."""
        if self.permissions and isinstance(self.permissions, dict):
            return self.permissions.copy()
        return {}
    
    def set_permissions(self, permissions: dict) -> None:
        """Set all permissions for this role."""
        self.permissions = permissions
    
    def extend_expiration(self, days: int) -> None:
        """Extend role expiration by specified days."""
        from datetime import timedelta
        if self.expires_at is None:
            self.expires_at = datetime.utcnow()
        self.expires_at = self.expires_at + timedelta(days=days)
    
    def activate(self) -> None:
        """Activate this role."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate this role."""
        self.is_active = False