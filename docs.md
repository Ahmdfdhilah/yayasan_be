# TAFATUR Backend API Documentation

## Overview
Backend API untuk sistem evaluasi guru dan manajemen RPP. API ini menggunakan FastAPI dengan arsitektur modular yang mendukung autentikasi JWT, role-based authorization, dan operasi CRUD lengkap.

**Base URL**: `/api/v1`

## Authentication
Semua endpoint (kecuali login) memerlukan autentikasi dengan JWT token di header:
```
Authorization: Bearer {access_token}
```

## Response Format
Semua response menggunakan format JSON dengan struktur standar:

### Success Response
```json
{
  "data": {...},
  "message": "Success",
  "status": "success"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status": "error"
}
```

### Paginated Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

## User Roles
- **admin**: Full system access
- **kepala_sekolah**: School principal, can manage their organization
- **guru**: Teacher, can view own evaluations and submit RPP

---

# Authentication Endpoints

## POST /auth/login
Login user dengan email dan password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "display_name": "John Doe",
    "roles": ["guru"],
    "organization_id": 1,
    "status": "ACTIVE"
  }
}
```

## POST /auth/refresh
Refresh access token menggunakan refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ..."
}
```

## GET /auth/me
Mendapatkan informasi user yang sedang login.

**Response:** UserResponse object

## POST /auth/logout
Logout user (client-side token removal).

## POST /auth/password-reset
Request password reset via email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

## POST /auth/password-reset/confirm
Konfirmasi reset password dengan token.

**Request Body:**
```json
{
  "token": "reset_token",
  "new_password": "newpassword123"
}
```

## POST /auth/change-password
Ganti password user yang sedang login.

**Request Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

---

# User Management Endpoints

## GET /users/me
Mendapatkan profil user sendiri.

**Response:** UserResponse object

## PUT /users/me
Update profil user sendiri.

**Request Body:**
```json
{
  "profile": {
    "name": "John Doe Updated",
    "phone": "+62812345678"
  }
}
```

## POST /users/me/change-password
Ganti password user sendiri.

## GET /users
**[Admin/Manager Only]** List semua users dengan filtering.

**Query Parameters:**
- `page`: Page number (default: 1)
- `size`: Items per page (default: 10)
- `search`: Search dalam nama/email
- `role`: Filter by role
- `status`: Filter by status
- `organization_id`: Filter by organization
- `sort_by`: Sort field (default: created_at)
- `sort_order`: asc/desc (default: desc)

## POST /users
**[Admin Only]** Buat user baru.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "profile": {
    "name": "New User",
    "phone": "+62812345678"
  },
  "organization_id": 1,
  "password": "password123"
}
```

## GET /users/{user_id}
**[Admin/Manager Only]** Get user by ID.

## PUT /users/{user_id}
**[Admin Only]** Update user.

## DELETE /users/{user_id}
**[Admin Only]** Soft delete user.

## POST /users/{user_id}/reset-password
**[Admin Only]** Reset user password ke default.

## POST /users/{user_id}/activate
**[Admin Only]** Aktivasi user.

## POST /users/{user_id}/deactivate
**[Admin Only]** Deaktivasi user.

---

# Organization Management Endpoints

## GET /organizations
List organizations dengan filtering dan pagination.

**Query Parameters:**
- `page`, `size`: Pagination
- `q`: Search query
- `has_users`: Filter orgs dengan/tanpa users
- `has_head`: Filter orgs dengan/tanpa kepala
- `sort_by`, `sort_order`: Sorting

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "SD Negeri 1",
      "description": "Sekolah Dasar",
      "head_id": 2,
      "head_name": "Kepala Sekolah",
      "user_count": 15,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

## POST /organizations
**[Admin Only]** Buat organization baru.

**Request Body:**
```json
{
  "name": "SD Negeri 2",
  "description": "Sekolah Dasar Negeri 2",
  "head_id": 3
}
```

## GET /organizations/{org_id}
Get organization by ID.

## PUT /organizations/{org_id}
**[Admin/Manager Only]** Update organization.

## DELETE /organizations/{org_id}
**[Admin Only]** Delete organization.

## POST /organizations/{org_id}/assign-head
**[Admin/Manager Only]** Assign kepala sekolah.

**Request Body:**
```json
{
  "user_id": 3,
  "confirmation": true
}
```

## POST /organizations/{org_id}/remove-head
**[Admin/Manager Only]** Remove kepala sekolah.

---

# Period Management Endpoints

## GET /periods
Get periods dengan filtering.

**Query Parameters:**
- `academic_year`: Filter by tahun ajaran
- `semester`: Filter by semester
- `period_type`: Filter by tipe periode
- `is_active`: Filter by status aktif
- `skip`, `limit`: Pagination

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "academic_year": "2024/2025",
      "semester": "Ganjil",
      "period_type": "EVALUATION",
      "start_date": "2024-08-01",
      "end_date": "2024-12-31",
      "is_active": true,
      "description": "Periode evaluasi semester ganjil"
    }
  ]
}
```

## POST /periods
**[Admin/Manager Only]** Buat periode baru.

**Request Body:**
```json
{
  "academic_year": "2024/2025",
  "semester": "Genap",
  "period_type": "EVALUATION",
  "start_date": "2025-01-01",
  "end_date": "2025-06-30",
  "description": "Periode evaluasi semester genap"
}
```

## GET /periods/active
Get semua periode yang aktif.

## GET /periods/current
Get periode yang sedang berjalan berdasarkan tanggal.

## GET /periods/{period_id}
Get periode by ID.

## GET /periods/{period_id}/stats
**[Admin/Manager Only]** Get periode dengan statistik.

## PUT /periods/{period_id}
**[Admin/Manager Only]** Update periode.

## PATCH /periods/{period_id}/activate
**[Admin/Manager Only]** Aktivasi periode.

## PATCH /periods/{period_id}/deactivate
**[Admin/Manager Only]** Deaktivasi periode.

## DELETE /periods/{period_id}
**[Admin Only]** Delete periode.

---

# Evaluation Aspects Endpoints

## GET /evaluation-aspects
List aspek evaluasi dengan filtering.

**Query Parameters:**
- `page`, `size`: Pagination
- `q`: Search query
- `category`: Filter by kategori
- `is_active`: Filter by status aktif
- `sort_by`, `sort_order`: Sorting

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Pedagogik",
      "description": "Kemampuan mengelola pembelajaran",
      "category": "CORE",
      "weight": 0.3,
      "is_active": true,
      "evaluation_criteria": {
        "A": "Sangat Baik (90-100)",
        "B": "Baik (80-89)",
        "C": "Cukup (70-79)",
        "D": "Kurang (<70)"
      }
    }
  ]
}
```

## POST /evaluation-aspects
**[Admin Only]** Buat aspek evaluasi baru.

**Request Body:**
```json
{
  "name": "Kepribadian",
  "description": "Kepribadian yang mantap dan stabil",
  "category": "CORE",
  "weight": 0.25,
  "evaluation_criteria": {
    "A": "Sangat Baik",
    "B": "Baik", 
    "C": "Cukup",
    "D": "Kurang"
  }
}
```

## GET /evaluation-aspects/{aspect_id}
Get aspek evaluasi by ID.

## PUT /evaluation-aspects/{aspect_id}
**[Admin Only]** Update aspek evaluasi.

## DELETE /evaluation-aspects/{aspect_id}
**[Admin Only]** Delete aspek evaluasi.

## GET /evaluation-aspects/active/list
Get semua aspek evaluasi yang aktif.

## GET /evaluation-aspects/category/{category}
Get aspek evaluasi by kategori.

## POST /evaluation-aspects/bulk/create
**[Admin Only]** Bulk create aspek evaluasi.

---

# Teacher Evaluations Endpoints

## POST /teacher-evaluations/assign-teachers-to-period
**[Admin/Manager Only]** Auto-assign semua guru ke periode evaluasi.

**Request Body:**
```json
{
  "period_id": 1,
  "organization_id": 1
}
```

## GET /teacher-evaluations/period/{period_id}
Get evaluasi by periode. Teachers hanya bisa lihat evaluasi sendiri.

## GET /teacher-evaluations/teacher/{teacher_id}/period/{period_id}
Get evaluasi teacher tertentu di periode tertentu.

## PUT /teacher-evaluations/{evaluation_id}/grade
**[Manager Only]** Update grade evaluasi.

**Request Body:**
```json
{
  "grade": "A",
  "notes": "Excellent performance",
  "evaluation_date": "2024-12-01"
}
```

## PATCH /teacher-evaluations/bulk-grade
**[Manager Only]** Bulk update grades.

**Request Body:**
```json
{
  "updates": [
    {
      "evaluation_id": 1,
      "grade": "A",
      "notes": "Excellent"
    },
    {
      "evaluation_id": 2, 
      "grade": "B",
      "notes": "Good"
    }
  ]
}
```

## POST /teacher-evaluations/complete-teacher-evaluation
**[Manager Only]** Complete semua evaluasi untuk seorang guru.

**Request Body:**
```json
{
  "teacher_id": 5,
  "period_id": 1,
  "overall_notes": "Good overall performance"
}
```

## GET /teacher-evaluations/period/{period_id}/stats
**[Admin/Manager Only]** Get statistik evaluasi periode.

**Response:**
```json
{
  "period_id": 1,
  "total_teachers": 20,
  "total_evaluations": 80,
  "completed_evaluations": 60,
  "completion_rate": 0.75,
  "grade_distribution": {
    "A": 15,
    "B": 30,
    "C": 12,
    "D": 3
  },
  "teachers_summary": [
    {
      "teacher_id": 5,
      "teacher_name": "John Teacher",
      "total_aspects": 4,
      "completed_aspects": 4,
      "average_grade": "B"
    }
  ]
}
```

---

# RPP Submissions Endpoints

## POST /rpp-submissions
**[Teachers Only]** Submit RPP baru.

**Request Body:**
```json
{
  "period_id": 1,
  "title": "RPP Matematika Kelas 5",
  "subject": "Matematika",
  "grade_level": "5",
  "file_id": 123,
  "description": "RPP untuk materi pecahan"
}
```

## GET /rpp-submissions
List RPP submissions dengan filtering.

**Query Parameters:**
- `page`, `size`: Pagination
- `period_id`: Filter by periode
- `teacher_id`: Filter by teacher
- `status`: Filter by status
- `subject`: Filter by mata pelajaran
- `grade_level`: Filter by tingkat kelas

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "RPP Matematika Kelas 5",
      "subject": "Matematika", 
      "grade_level": "5",
      "status": "PENDING",
      "teacher_id": 5,
      "teacher_name": "John Teacher",
      "period_id": 1,
      "file_id": 123,
      "submitted_at": "2024-12-01T10:00:00Z",
      "reviewed_at": null,
      "reviewer_id": null
    }
  ]
}
```

## GET /rpp-submissions/{submission_id}
Get RPP submission by ID. Access control berdasarkan role.

## PUT /rpp-submissions/{submission_id}
**[Teachers Only]** Update RPP submission (hanya yang PENDING).

## DELETE /rpp-submissions/{submission_id}
**[Teachers Only]** Delete RPP submission (hanya PENDING/REJECTED).

## POST /rpp-submissions/{submission_id}/review
**[Principals Only]** Review RPP submission.

**Request Body:**
```json
{
  "action": "APPROVED",
  "notes": "RPP sudah sesuai standar",
  "feedback": "Good job on the lesson structure"
}
```

**Action values:** `APPROVED`, `REJECTED`, `REVISION_NEEDED`

## POST /rpp-submissions/{submission_id}/resubmit
**[Teachers Only]** Resubmit RPP yang direject.

**Request Body:**
```json
{
  "file_id": 124,
  "revision_notes": "Fixed issues mentioned in review"
}
```

## GET /rpp-submissions/pending-reviews
Get RPP yang pending review untuk current user.

## GET /rpp-submissions/period/{period_id}
Get RPP submissions by periode.

## GET /rpp-submissions/teacher/{teacher_id}
Get RPP submissions by teacher (requires period_id).

---

# Media Files Endpoints

## POST /media-files/upload
Upload file media.

**Request Body (multipart/form-data):**
- `file`: File to upload
- `is_public`: Boolean (optional, default: false)

**Response:**
```json
{
  "id": 123,
  "filename": "rpp_matematika.pdf",
  "original_filename": "RPP Matematika Kelas 5.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "file_path": "uploads/2024/12/rpp_matematika.pdf",
  "download_url": "/api/v1/media-files/123/download",
  "is_public": false,
  "uploader_id": 5
}
```

## GET /media-files
List media files dengan filtering.

**Query Parameters:**
- `page`, `size`: Pagination
- `q`: Search filenames
- `file_type`: Filter by type/extension
- `file_category`: Filter by category
- `uploader_id`: Filter by uploader
- `is_public`: Filter by public status
- `min_size`, `max_size`: Filter by file size
- `start_date`, `end_date`: Filter by upload date

## GET /media-files/{file_id}
Get media file details.

## GET /media-files/{file_id}/download
Download file content.

## PUT /media-files/{file_id}
Update media file metadata.

**Request Body:**
```json
{
  "file_metadata": {
    "title": "Updated Title",
    "description": "Updated description"
  },
  "is_public": true
}
```

## DELETE /media-files/{file_id}
Delete media file.

## GET /media-files/public/list
List public media files (no auth required).

---

# User Roles Endpoints

## GET /user-roles
**[Admin/Manager Only]** List user role assignments.

**Query Parameters:**
- `page`, `size`: Pagination
- `user_id`: Filter by user
- `role_name`: Filter by role
- `organization_id`: Filter by organization
- `is_active`: Filter by active status
- `expires_soon`: Filter roles expiring in N days

## POST /user-roles
**[Admin Only]** Create user role assignment.

**Request Body:**
```json
{
  "user_id": 5,
  "role_name": "guru",
  "organization_id": 1,
  "permissions": {
    "can_submit_rpp": true,
    "can_view_evaluations": true
  },
  "expires_at": "2025-12-31T23:59:59Z"
}
```

## GET /user-roles/{role_id}
Get user role by ID.

## PUT /user-roles/{role_id}
**[Admin Only]** Update user role.

## DELETE /user-roles/{role_id}
**[Admin Only]** Delete user role assignment.

## POST /user-roles/assign
**[Admin Only]** Assign role to user.

## POST /user-roles/revoke
**[Admin Only]** Revoke role from user.

## GET /user-roles/users/{user_id}/roles
Get all roles untuk user tertentu.

## GET /user-roles/roles/{role_name}/users
Get all users dengan role tertentu.

---

# Common Schemas

## UserResponse
```json
{
  "id": 1,
  "email": "user@example.com",
  "profile": {
    "name": "John Doe",
    "phone": "+62812345678"
  },
  "organization_id": 1,
  "status": "ACTIVE",
  "email_verified_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-12-01T10:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-12-01T10:00:00Z",
  "display_name": "John Doe",
  "full_name": "John Doe",
  "roles": ["guru"]
}
```

## MessageResponse
```json
{
  "message": "Operation completed successfully"
}
```

## Error Codes
- `400`: Bad Request - Invalid input
- `401`: Unauthorized - Authentication required
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `422`: Validation Error - Input validation failed
- `500`: Internal Server Error

## Rate Limiting
API menggunakan rate limiting untuk mencegah abuse:
- **Default**: 100 requests per minute per IP
- **Authentication endpoints**: 10 requests per minute per IP
- **File upload**: 20 requests per minute per user

## File Upload Limits
- **Max file size**: 10MB
- **Allowed types**: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, JPEG
- **Storage**: Local filesystem dengan path tracking di database

## Notes untuk Frontend Developer

### Authentication Flow
1. Login dengan POST /auth/login
2. Simpan access_token dan refresh_token
3. Gunakan access_token di header Authorization untuk semua requests
4. Refresh token otomatis sebelum expired dengan POST /auth/refresh
5. Logout dengan POST /auth/logout dan hapus tokens

### Role-based UI
- **Admin**: Akses semua fitur
- **Kepala Sekolah**: Manage organization sendiri, approve RPP, evaluate teachers
- **Guru**: View evaluations sendiri, submit RPP, update profile

### Error Handling
Selalu handle error responses dan tampilkan pesan yang user-friendly:
```javascript
try {
  const response = await fetch('/api/v1/users/me');
  if (!response.ok) {
    const error = await response.json();
    showError(error.detail || 'Something went wrong');
  }
} catch (error) {
  showError('Network error');
}
```

### Pagination
Gunakan query parameters untuk pagination:
```javascript
const params = new URLSearchParams({
  page: currentPage,
  size: itemsPerPage,
  search: searchQuery
});
fetch(`/api/v1/users?${params}`);
```

### File Upload
Gunakan FormData untuk upload:
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('is_public', false);

fetch('/api/v1/media-files/upload', {
  method: 'POST',
  body: formData,
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```