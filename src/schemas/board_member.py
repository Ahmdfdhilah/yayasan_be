"""Board member schemas for request/response."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.schemas.shared import BaseListResponse


# ===== BASE SCHEMAS =====

class BoardMemberBase(BaseModel):
    """Base board member schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Board member name")
    position: str = Field(..., min_length=1, max_length=255, description="Position/title in the board")
    img_url: Optional[str] = Field(None, max_length=500, description="Profile image URL")
    description: Optional[str] = Field(None, description="Bio or description")
    is_active: bool = Field(default=True, description="Active status")
    display_order: int = Field(default=0, ge=0, description="Order for display")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate and clean name."""
        return name.strip()
    
    @field_validator('position')
    @classmethod
    def validate_position(cls, position: str) -> str:
        """Validate and clean position."""
        return position.strip()


# ===== REQUEST SCHEMAS =====

class BoardMemberCreate(BoardMemberBase):
    """Schema for creating a board member."""
    pass


class BoardMemberUpdate(BaseModel):
    """Schema for updating a board member."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[str] = Field(None, min_length=1, max_length=255)
    img_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: Optional[str]) -> Optional[str]:
        """Validate and clean name if provided."""
        return name.strip() if name else None
    
    @field_validator('position')
    @classmethod
    def validate_position(cls, position: Optional[str]) -> Optional[str]:
        """Validate and clean position if provided."""
        return position.strip() if position else None


# ===== RESPONSE SCHEMAS =====

class BoardMemberResponse(BaseModel):
    """Schema for board member response."""
    id: int
    name: str
    position: str
    img_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    display_order: int
    created_at: str
    updated_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # Computed fields
    short_description: str = Field(..., description="Shortened description")
    
    @classmethod
    def from_board_member_model(cls, board_member) -> "BoardMemberResponse":
        """Create BoardMemberResponse from BoardMember model."""
        return cls(
            id=board_member.id,
            name=board_member.name,
            position=board_member.position,
            img_url=board_member.img_url,
            description=board_member.description,
            is_active=board_member.is_active,
            display_order=board_member.display_order,
            created_at=board_member.created_at.isoformat() if board_member.created_at else "",
            updated_at=board_member.updated_at.isoformat() if board_member.updated_at else None,
            created_by=board_member.created_by,
            updated_by=board_member.updated_by,
            short_description=board_member.short_description
        )
    
    model_config = ConfigDict(from_attributes=True)


class BoardMemberListResponse(BaseListResponse[BoardMemberResponse]):
    """Standardized board member list response."""
    pass


class BoardMemberSummary(BaseModel):
    """Schema for board member summary (lighter response)."""
    id: int
    name: str
    position: str
    img_url: Optional[str] = None
    is_active: bool
    display_order: int
    
    @classmethod
    def from_board_member_model(cls, board_member) -> "BoardMemberSummary":
        """Create BoardMemberSummary from BoardMember model."""
        return cls(
            id=board_member.id,
            name=board_member.name,
            position=board_member.position,
            img_url=board_member.img_url,
            is_active=board_member.is_active,
            display_order=board_member.display_order
        )
    
    model_config = ConfigDict(from_attributes=True)


# ===== FILTER SCHEMAS =====

class BoardMemberFilterParams(BaseModel):
    """Filter parameters for board member listing."""
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    # Search and filtering
    search: Optional[str] = Field(default=None, description="Search in name or position")
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")
    
    # Sorting
    sort_by: str = Field(default="display_order", description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")