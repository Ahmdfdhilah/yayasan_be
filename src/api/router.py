"""Updated API router configuration dengan evaluasi endpoints."""

from fastapi import APIRouter

# Existing imports
from src.api.endpoints import auth, users, organizations, user_roles

# Create main API router
api_router = APIRouter()

# ===== EXISTING ENDPOINTS =====

# Include existing endpoint routers dengan proper tags dan descriptions
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        422: {"description": "Validation Error"},
    }
)

api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["User Management"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "User not found"},
        422: {"description": "Validation Error"},
    }
)
api_router.include_router(
    user_roles.router, 
    prefix="/user-roles", 
    tags=["User Roles"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        422: {"description": "Validation Error"},
    }
)

api_router.include_router(
    organizations.router, 
    prefix="/organizations", 
    tags=["Organizations"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        422: {"description": "Validation Error"},
    }
)


# Export untuk main.py
def get_api_router():
    """Get configured API router dengan semua endpoints."""
    return api_router