"""Updated API router configuration dengan evaluasi endpoints."""

from fastapi import APIRouter

# Existing imports
from src.api.endpoints import auth, users, organizations, user_roles

# Evaluation system imports
from src.api.endpoints import (
    periods,
    evaluation_aspects,
    teacher_evaluations,
    media_files,
    dashboard,
    rpp_submissions,
    articles,
    board_management,
    galleries,
    messages,
    mitra,
    program,
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
    },
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
    },
)
api_router.include_router(
    user_roles.router,
    prefix="/user-roles",
    tags=["User Roles"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        422: {"description": "Validation Error"},
    },
)

api_router.include_router(
    organizations.router,
    prefix="/organizations",
    tags=["Organizations"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        422: {"description": "Validation Error"},
    },
)

# ===== EVALUATION SYSTEM ENDPOINTS =====

# Periods - untuk mengelola periode evaluasi
api_router.include_router(
    periods.router,
    prefix="/periods",
    tags=["Period Management"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    },
)

# Evaluation Aspects - untuk mengelola aspek evaluasi
api_router.include_router(
    evaluation_aspects.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    },
)

# Teacher Evaluations - untuk evaluasi individual per aspek
api_router.include_router(
    teacher_evaluations.router,
    prefix="/teacher-evaluations",
    tags=["Teacher Evaluations"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    },
)


# Media Files - untuk manajemen file upload dan download
api_router.include_router(
    media_files.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    },
)

# Dashboard - untuk statistik dan overview sistem
api_router.include_router(
    dashboard.router,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    },
)

# RPP Submissions - untuk pengelolaan RPP submission
api_router.include_router(
    rpp_submissions.router,
    prefix="/rpp-submissions",
    tags=["RPP Submissions"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation Error"},
    },
)

# Articles - untuk pengelolaan artikel/konten
api_router.include_router(
    articles.router,
    prefix="/articles",
    tags=["Articles"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Article not found"},
        422: {"description": "Validation Error"},
    },
)

# Board Members - untuk pengelolaan anggota dewan
api_router.include_router(
    board_management.router,
    prefix="/board-members",
    tags=["Board Members"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Board member not found"},
        422: {"description": "Validation Error"},
    },
)

# Galleries - untuk pengelolaan galeri gambar dengan ordering
api_router.include_router(
    galleries.router,
    prefix="/galleries",
    tags=["Galleries"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Gallery item not found"},
        422: {"description": "Validation Error"},
    },
)

# Messages - untuk pesan dari public dengan sanitasi
api_router.include_router(
    messages.router,
    prefix="/messages",
    tags=["Messages"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Message not found"},
        422: {"description": "Validation Error"},
        429: {"description": "Too Many Requests"},
    },
)

# Mitra - untuk pengelolaan kemitraan
api_router.include_router(
    mitra.router,
    prefix="/mitra",
    tags=["Mitra"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Mitra not found"},
        422: {"description": "Validation Error"},
    },
)

# Program - untuk pengelolaan program pendidikan
api_router.include_router(
    program.router,
    prefix="/programs",
    tags=["Programs"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Program not found"},
        422: {"description": "Validation Error"},
    },
)


# Export untuk main.py
def get_api_router():
    """Get configured API router dengan semua endpoints."""
    return api_router
