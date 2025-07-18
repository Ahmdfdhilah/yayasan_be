# ===== src/models/__init__.py (UPDATE EXISTING) =====
"""Models initialization - Updated dengan penilaian risiko models."""

# ===== EXISTING MODELS =====
from .base import BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin
from .enums import UserRole
from .user import User, PasswordResetToken

__all__ = [
    # Base classes
    "BaseModel",
    "TimestampMixin", 
    "SoftDeleteMixin",
    "AuditMixin",
    
    # Existing models
    "UserRole",
    "User",
    "PasswordResetToken", 
]