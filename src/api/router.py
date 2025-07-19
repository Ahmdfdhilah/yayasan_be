"""Updated API router configuration dengan evaluasi endpoints."""

from fastapi import APIRouter

# Existing imports
from src.api.endpoints import auth, users, organizations, user_roles

# Evaluation system imports
from src.api.endpoints import (
    evaluation_aspects,
    evaluation_results,
    rpp_submissions,
    teacher_evaluations,
    media_files,
    dashboard
)

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

# ===== EVALUATION SYSTEM ENDPOINTS =====

# Evaluation Aspects - untuk mengelola aspek evaluasi
api_router.include_router(
    evaluation_aspects.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    }
)

# Teacher Evaluations - untuk evaluasi individual per aspek
api_router.include_router(
    teacher_evaluations.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    }
)

# Evaluation Results - untuk hasil evaluasi yang sudah di-aggregate
api_router.include_router(
    evaluation_results.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    }
)

# RPP Submissions - untuk pengumpulan dan review RPP
api_router.include_router(
    rpp_submissions.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    }
)

# Media Files - untuk manajemen file upload dan download
api_router.include_router(
    media_files.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    }
)

# Dashboard - untuk overview analytics dan monitoring
api_router.include_router(
    dashboard.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    }
)


# Export untuk main.py
def get_api_router():
    """Get configured API router dengan semua endpoints."""
    return api_router