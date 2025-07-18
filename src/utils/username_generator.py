"""Username generation utilities."""

import re
import unicodedata
from typing import List, Callable, Dict, Any


def generate_username_from_name_and_inspektorat(nama: str, inspektorat: str) -> str:
    """Generate username from name and inspektorat."""
    # Normalize and clean nama
    nama_clean = normalize_text(nama)
    inspektorat_clean = normalize_text(inspektorat)
    
    # Take first part of name and first part of inspektorat
    nama_parts = nama_clean.split()
    inspektorat_parts = inspektorat_clean.split()
    
    if nama_parts and inspektorat_parts:
        username = f"{nama_parts[0]}_{inspektorat_parts[0]}"
    elif nama_parts:
        username = nama_parts[0]
    else:
        username = "user"
    
    return clean_username(username)


def normalize_text(text: str) -> str:
    """Normalize text by removing unicode and special characters."""
    # Remove unicode and normalize
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters but keep spaces and basic punctuation
    text = re.sub(r'[^\w\s\-]', '', text)
    
    return text.strip()


def clean_username(username: str) -> str:
    """Clean username to only contain valid characters."""
    # Remove all non-alphanumeric and underscore characters
    username = re.sub(r'[^a-z0-9_]', '', username.lower())
    
    # Ensure it doesn't start with a number
    if username and username[0].isdigit():
        username = f"user_{username}"
    
    # Limit length
    return username[:50] if username else "user"


async def generate_available_username(
    nama: str, 
    inspektorat: str, 
    role: str, 
    username_exists_func: Callable[[str], bool]
) -> Dict[str, Any]:
    """Generate an available username with fallback options."""
    
    # Generate base username
    base_username = generate_username_from_name_and_inspektorat(nama, inspektorat)
    
    # Check if base username is available
    if not await username_exists_func(base_username):
        return {
            "username": base_username,
            "is_original": True,
            "attempts": 1
        }
    
    # Try with conflict resolution
    conflict_username = generate_username_with_conflict_resolution(nama, inspektorat)
    if conflict_username != base_username and not await username_exists_func(conflict_username):
        return {
            "username": conflict_username,
            "is_original": False,
            "attempts": 2
        }
    
    # Try numbered alternatives
    for i in range(1, 100):
        numbered_username = f"{base_username}{i}"
        if not await username_exists_func(numbered_username):
            return {
                "username": numbered_username,
                "is_original": False,
                "attempts": i + 2
            }
    
    # Ultimate fallback with timestamp
    import time
    fallback_username = f"{base_username}_{int(time.time()) % 10000}"
    
    return {
        "username": fallback_username,
        "is_original": False,
        "attempts": 102
    }


def generate_username_with_conflict_resolution(nama: str, inspektorat: str) -> str:
    """Generate username with conflict resolution strategy."""
    nama_clean = normalize_text(nama)
    inspektorat_clean = normalize_text(inspektorat)
    
    # Try different combinations
    nama_parts = nama_clean.split()
    inspektorat_parts = inspektorat_clean.split()
    
    # Strategy 1: First two letters of each
    if len(nama_parts) > 0 and len(inspektorat_parts) > 0:
        username = f"{nama_parts[0][:2]}{inspektorat_parts[0][:2]}"
        if len(username) >= 4:
            return clean_username(username)
    
    # Strategy 2: First letter of name + full inspektorat
    if len(nama_parts) > 0 and len(inspektorat_parts) > 0:
        username = f"{nama_parts[0][0]}{inspektorat_parts[0]}"
        return clean_username(username)
    
    # Fallback
    return clean_username(f"{nama_clean[:3]}{inspektorat_clean[:3]}")


def generate_username_alternatives(base_username: str, count: int = 5) -> List[str]:
    """Generate alternative usernames based on base username."""
    alternatives = []
    
    # Numbered alternatives
    for i in range(1, count + 1):
        alternatives.append(f"{base_username}{i}")
    
    # Letter alternatives
    letters = ['a', 'b', 'c', 'd', 'e']
    for letter in letters[:count]:
        if len(alternatives) < count:
            alternatives.append(f"{base_username}{letter}")
    
    # Mixed alternatives
    if len(alternatives) < count:
        for i in range(len(alternatives), count):
            alternatives.append(f"{base_username}_alt{i}")
    
    return alternatives[:count]


def validate_username(username: str) -> Dict[str, Any]:
    """Validate username format and return validation result."""
    errors = []
    
    # Length check
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    if len(username) > 50:
        errors.append("Username must be no more than 50 characters long")
    
    # Character check
    if not re.match(r'^[a-z0-9_]+$', username):
        errors.append("Username can only contain lowercase letters, numbers, and underscores")
    
    # Start with letter check
    if username and username[0].isdigit():
        errors.append("Username cannot start with a number")
    
    # Reserved words check
    reserved_words = ['admin', 'root', 'system', 'api', 'www', 'mail', 'ftp']
    if username.lower() in reserved_words:
        errors.append("Username cannot be a reserved word")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "suggestions": generate_username_alternatives(username, 3) if errors else []
    }