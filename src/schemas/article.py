"""Article schemas for request/response."""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

from src.schemas.shared import BaseListResponse


# ===== BASE SCHEMAS =====

class ArticleBase(BaseModel):
    """Base article schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Article title")
    description: str = Field(..., min_length=1, description="Full article content")
    slug: str = Field(..., min_length=1, max_length=255, description="URL-friendly slug")
    excerpt: Optional[str] = Field(None, max_length=500, description="Short summary")
    img_url: Optional[str] = Field(None, max_length=500, description="Article image URL")
    category: str = Field(..., min_length=1, max_length=100, description="Article category")
    is_published: bool = Field(default=False, description="Publication status")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, slug: str) -> str:
        """Validate slug format."""
        import re
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return slug.lower().strip()
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, title: str) -> str:
        """Validate and clean title."""
        return title.strip()
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, category: str) -> str:
        """Validate and clean category."""
        return category.strip().lower()


# ===== REQUEST SCHEMAS =====

class ArticleCreate(ArticleBase):
    """Schema for creating an article."""
    pass


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    excerpt: Optional[str] = Field(None, max_length=500)
    img_url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, slug: Optional[str]) -> Optional[str]:
        """Validate slug format if provided."""
        if slug:
            import re
            if not re.match(r'^[a-z0-9-]+$', slug):
                raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
            return slug.lower().strip()
        return slug
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, title: Optional[str]) -> Optional[str]:
        """Validate and clean title if provided."""
        return title.strip() if title else None
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, category: Optional[str]) -> Optional[str]:
        """Validate and clean category if provided."""
        return category.strip().lower() if category else None


# ===== RESPONSE SCHEMAS =====

class ArticleResponse(BaseModel):
    """Schema for article response."""
    id: int
    title: str
    description: str
    slug: str
    excerpt: Optional[str] = None
    img_url: Optional[str] = None
    category: str
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # Computed fields
    is_draft: bool = Field(..., description="Whether article is a draft")
    display_excerpt: str = Field(..., description="Excerpt or truncated description")
    
    @classmethod
    def from_article_model(cls, article) -> "ArticleResponse":
        """Create ArticleResponse from Article model."""
        return cls(
            id=article.id,
            title=article.title,
            description=article.description,
            slug=article.slug,
            excerpt=article.excerpt,
            img_url=article.img_url,
            category=article.category,
            is_published=article.is_published,
            published_at=article.published_at,
            created_at=article.created_at,
            updated_at=article.updated_at,
            created_by=article.created_by,
            updated_by=article.updated_by,
            is_draft=article.is_draft,
            display_excerpt=article.get_excerpt()
        )
    
    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseListResponse[ArticleResponse]):
    """Standardized article list response."""
    pass


class ArticleSummary(BaseModel):
    """Schema for article summary (lighter response)."""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    img_url: Optional[str] = None
    category: str
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    
    @classmethod
    def from_article_model(cls, article) -> "ArticleSummary":
        """Create ArticleSummary from Article model."""
        return cls(
            id=article.id,
            title=article.title,
            slug=article.slug,
            excerpt=article.excerpt,
            img_url=article.img_url,
            category=article.category,
            is_published=article.is_published,
            published_at=article.published_at,
            created_at=article.created_at
        )
    
    model_config = ConfigDict(from_attributes=True)


# ===== FILTER SCHEMAS =====

class ArticleFilterParams(BaseModel):
    """Filter parameters for article listing."""
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    # Search and filtering
    search: Optional[str] = Field(default=None, description="Search in title, description, or category")
    category: Optional[str] = Field(default=None, description="Filter by category")
    is_published: Optional[bool] = Field(default=None, description="Filter by publication status")
    
    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
    
    # Date filtering
    published_after: Optional[datetime] = Field(default=None, description="Filter articles published after this date")
    published_before: Optional[datetime] = Field(default=None, description="Filter articles published before this date")


# ===== ACTION SCHEMAS =====

class ArticlePublish(BaseModel):
    """Schema for publishing/unpublishing an article."""
    is_published: bool = Field(..., description="Publication status")
    published_at: Optional[datetime] = Field(None, description="Custom publication date")


class CategoryListResponse(BaseModel):
    """Response schema for article categories."""
    categories: List[str] = Field(..., description="List of unique categories")
    total: int = Field(..., description="Total number of categories")