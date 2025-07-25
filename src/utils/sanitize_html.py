from bleach.css_sanitizer import CSSSanitizer
import bleach

from src.core.config import settings
def sanitize_html_content(html: str) -> str:
    """Sanitize HTML content with whitelisted CSS properties"""
    css_sanitizer = CSSSanitizer(allowed_css_properties=settings.ALLOWED_CSS_PROPERTIES)
    
    return bleach.clean(
        html,
        tags=settings.ALLOWED_TAGS,
        attributes=settings.ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True,
        strip_comments=True
    )