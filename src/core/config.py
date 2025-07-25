"""Application settings and configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, field_validator
from typing import Any, ClassVar, Dict, Optional, List


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # API settings
    PROJECT_NAME: str
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_ORIGINS: str = "*"
    CORS_HEADERS: str = "*"
    CORS_METHODS: str = "*"

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DATABASE_URI: Optional[PostgresDsn] = None
    SQL_ECHO: bool = False

    # Database connection pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # JWT Settings
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis (optional)
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_TTL: int = 3600

    # File handling
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILENAME_LENGTH: int = 50
    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,image/gif,application/pdf,text/plain"
    
    # Storage Configuration
    STORAGE_PROVIDER: str = "local"  # Options: local, aws_s3, gcp, azure_blob
    STATIC_FILES_PATH: str = "static"
    UPLOADS_PATH: str = "static/uploads"
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    
    # Google Cloud Storage Configuration
    GCP_PROJECT_ID: Optional[str] = None
    GCP_STORAGE_BUCKET: Optional[str] = None
    GCP_SERVICE_ACCOUNT_KEY_PATH: Optional[str] = None
    
    # Azure Blob Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER: Optional[str] = None

    # Logging
    LOG_DIRECTORY: str = "logs"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    SERVICE_NAME: str

    # Password Security Settings (Step 1)
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_MAX_LENGTH: int = 128
    PASSWORD_HISTORY_COUNT: int = 5
    PASSWORD_MAX_AGE_DAYS: int = 90
    ACCOUNT_LOCKOUT_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 15
    
    # Rate Limiting Settings (Step 2)
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    AUTH_RATE_LIMIT_CALLS: int = 5
    AUTH_RATE_LIMIT_PERIOD: int = 300
    
    # Session Management Settings
    MAX_SESSIONS_PER_USER: int = 5
    SESSION_EXPIRE_MINUTES: int = 1440  # 24 hours
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24

    # Email Configuration (Gmail SMTP)
    EMAIL_SMTP_HOST: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USERNAME: Optional[str] = None
    EMAIL_SMTP_PASSWORD: Optional[str] = None
    EMAIL_SENDER_EMAIL: str = "noreply@yourapp.com"
    EMAIL_SENDER_NAME: str = "Government Auth System"
    EMAIL_RESET_URL_BASE: str = "http://localhost:5173/reset-password"

       # Configure bleach for HTML sanitization
    ALLOWED_TAGS: ClassVar[list[str]] = [
        # Existing tags
        "a", "abbr", "acronym", "b", "blockquote", "br", "code", "div", 
        "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", 
        "li", "ol", "p", "pre", "span", "strong", "table", "tbody", 
        "td", "th", "thead", "tr", "ul",
        # Additional ReactQuill tags
        "sub", "sup", "video", "iframe",  # for subscript, superscript, video
    ]

    ALLOWED_ATTRIBUTES: ClassVar[dict[str, list[str]]] = {
        # Existing attributes
        "a": ["href", "title", "target", "rel"],
        "abbr": ["title"],
        "acronym": ["title"],
        "img": ["src", "alt", "title", "width", "height", "loading"],
        "div": ["class", "id", "style"],
        "span": ["class", "id", "style"],
        "table": ["class", "id", "border", "style"],
        "td": ["colspan", "rowspan", "style"],
        "th": ["colspan", "rowspan", "scope", "style"],
        "p": ["style", "class"],
        "h1": ["style", "class"],
        "h2": ["style", "class"],
        "h3": ["style", "class"],
        "h4": ["style", "class"],
        "h5": ["style", "class"],
        "h6": ["style", "class"],
        "blockquote": ["style", "class"],
        "li": ["style", "class"],
        "ol": ["style", "class", "type"],
        "ul": ["style", "class", "type"],
        # Additional ReactQuill attributes
        "video": ["src", "controls", "width", "height", "style", "class"],
        "iframe": ["src", "width", "height", "frameborder", "allowfullscreen", "style", "class"],
        "code": ["class", "style"],
        "pre": ["class", "style"],
        "sup": ["style", "class"],
        "sub": ["style", "class"],
        "br": ["clear"],
    }

    ALLOWED_CSS_PROPERTIES: ClassVar[list[str]] = [
        # Existing properties
        "text-align", "text-decoration", "text-transform", "color",
        "font-family", "font-size", "font-weight", "font-style",
        "margin", "margin-top", "margin-right", "margin-bottom", "margin-left", 
        "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
        "background-color", "background",
        "border", "border-style", "border-width", "border-color", "border-radius",
        "border-top", "border-right", "border-bottom", "border-left",
        "width", "height", "min-width", "max-width", "min-height", "max-height",
        "position", "top", "right", "bottom", "left", "float",
        "display", "visibility", "opacity",
        "flex", "flex-direction", "justify-content", "align-items",
        "grid-template-columns", "grid-gap",
        "line-height", "white-space", "cursor",
        # Additional ReactQuill properties
        "text-indent", "vertical-align", "letter-spacing", "word-spacing",
        "list-style", "list-style-type", "list-style-position",
        "overflow", "overflow-x", "overflow-y", "z-index",
        "transition", "transform", "box-shadow",
    ]
    
    # Allowed protocols for links
    ALLOWED_PROTOCOLS: ClassVar[list[str]] = ["http", "https", "mailto", "tel"]

    # Password Reset Settings
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    PASSWORD_RESET_TOKEN_LENGTH: int = 32

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        """Build PostgreSQL connection string from components."""
        if isinstance(v, str):
            return v

        values = info.data
        user = values.get("POSTGRES_USER", "")
        password = values.get("POSTGRES_PASSWORD", "")
        host = values.get("POSTGRES_SERVER", "")
        port = values.get("POSTGRES_PORT", "5432")
        db = values.get("POSTGRES_DB", "")

        auth = f"{user}:{password}" if password else user
        return f"postgresql://{auth}@{host}:{port}/{db}"

    @field_validator("API_V1_STR")
    def ensure_api_prefix_has_slash(cls, v: str) -> str:
        """Ensure API prefix starts with a slash."""
        if not v.startswith("/"):
            return f"/{v}"
        return v

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def CORS_METHODS_LIST(self) -> List[str]:
        """Convert CORS_METHODS string to list."""
        if self.CORS_METHODS == "*":
            return ["*"]
        return [method.strip() for method in self.CORS_METHODS.split(",")]

    @property
    def CORS_HEADERS_LIST(self) -> List[str]:
        """Convert CORS_HEADERS string to list."""
        if self.CORS_HEADERS == "*":
            return ["*"]
        return [header.strip() for header in self.CORS_HEADERS.split(",")]

    @property
    def ALLOWED_FILE_TYPES_LIST(self) -> List[str]:
        """Convert ALLOWED_FILE_TYPES string to list."""
        return [file_type.strip() for file_type in self.ALLOWED_FILE_TYPES.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


# Create global settings instance
settings = Settings()
