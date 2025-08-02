"""Board management schemas for API request/response."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field

from .shared import BaseListResponse


# ===== BOARD GROUP SCHEMAS =====

class BoardGroupBase(BaseModel):
    """Base board group schema."""
    title: str = Field(..., max_length=255, description="Group title")
    display_order: int = Field(default=999, description="Display order")
    description: Optional[str] = Field(None, description="Group description")


class BoardGroupCreate(BoardGroupBase):
    """Board group creation schema."""
    pass


class BoardGroupUpdate(BaseModel):
    """Board group update schema."""
    title: Optional[str] = Field(None, max_length=255, description="Group title")
    display_order: Optional[int] = Field(None, description="Display order")
    description: Optional[str] = Field(None, description="Group description")


class BoardGroupResponse(BoardGroupBase):
    """Board group response schema."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BoardGroupFilterParams(BaseModel):
    """Board group filter parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in title or description")
    sort_by: str = Field("display_order", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class BoardGroupListResponse(BaseListResponse[BoardGroupResponse]):
    """Board group list response with pagination."""
    pass


# ===== BOARD MEMBER SCHEMAS =====

class BoardMemberBase(BaseModel):
    """Base board member schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Board member name")
    position: str = Field(..., min_length=1, max_length=255, description="Position/title in the board")
    group_id: Optional[int] = Field(None, description="Board group ID")
    member_order: int = Field(default=1, ge=1, description="Order within the group")
    img_url: Optional[str] = Field(None, max_length=500, description="Profile image URL")
    description: Optional[str] = Field(None, description="Bio or description")
    
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


class BoardMemberCreate(BoardMemberBase):
    """Schema for creating a board member."""
    pass


class BoardMemberUpdate(BaseModel):
    """Schema for updating a board member."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[str] = Field(None, min_length=1, max_length=255)
    group_id: Optional[int] = Field(None, description="Board group ID")
    member_order: Optional[int] = Field(None, ge=1, description="Order within the group")
    img_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    
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


class BoardMemberResponse(BaseModel):
    """Schema for board member response."""
    id: int
    name: str
    position: str
    group_id: Optional[int] = None
    member_order: int
    img_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    @computed_field
    @property
    def short_description(self) -> str:
        """Get shortened description."""
        if not self.description:
            return ""
        return (self.description[:100] + "...") if len(self.description) > 100 else self.description
    
    model_config = ConfigDict(from_attributes=True)


class BoardMemberListResponse(BaseListResponse[BoardMemberResponse]):
    """Board member list response with pagination."""
    pass


class BoardMemberFilterParams(BaseModel):
    """Filter parameters for board member listing."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search in name or position")
    sort_by: str = Field(default="member_order", description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")