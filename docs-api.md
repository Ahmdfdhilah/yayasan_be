# PKG System API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Data Types](#common-data-types)
4. [Enums](#enums)
5. [API Endpoints](#api-endpoints)
   - [Authentication API](#authentication-api)
   - [Users API](#users-api)
   - [Organizations API](#organizations-api)
   - [Periods API](#periods-api)
   - [Evaluation Aspects API](#evaluation-aspects-api)
   - [Teacher Evaluations API](#teacher-evaluations-api)
   - [RPP Submissions API](#rpp-submissions-api)
   - [Media Files API](#media-files-api)
   - [User Roles API](#user-roles-api)
   - [Dashboard API](#dashboard-api)
6. [Schemas](#schemas)
7. [Error Responses](#error-responses)

## Overview

The PKG (Penilaian Kinerja Guru - Teacher Performance Evaluation) system is a comprehensive API for managing teacher performance evaluations, RPP (Rencana Pelaksanaan Pembelajaran) submissions, and educational organization management.

**Base URL**: `/api`  
**API Version**: 1.0  
**Content Type**: `application/json`

## Authentication

All API endpoints require authentication except for public media files. The system uses JWT (JSON Web Tokens) for authentication.

### Auth Flow
1. **Login** with email/password → receive access token and refresh token
2. **Include** access token in Authorization header: `Bearer <token>`
3. **Refresh** tokens when access token expires
4. **Logout** to invalidate tokens

## Common Data Types

### Base Response Types
- **Paginated Lists**: All list endpoints return paginated results
- **Success Messages**: Standard success/error responses
- **Timestamps**: All dates/times in ISO 8601 format

### Pagination Parameters
- `page`: int (default: 1, min: 1) - Page number
- `size`: int (default: 10, min: 1, max: 100) - Items per page

### Search Parameters
- `q`: string - Search query
- `sort_by`: string (default: "created_at") - Sort field
- `sort_order`: string (default: "desc", enum: "asc"|"desc") - Sort order

## Enums

### UserRole
```typescript
enum UserRole {
  ADMIN = "admin"           // System administrator
  GURU = "guru"            // Teacher
  KEPALA_SEKOLAH = "kepala_sekolah"  // Principal/School head
}
```

### UserStatus
```typescript
enum UserStatus {
  ACTIVE = "active"        // Active user
  INACTIVE = "inactive"    // Inactive user
  SUSPENDED = "suspended"  // Suspended user
}
```

### RPPStatus
```typescript
enum RPPStatus {
  PENDING = "pending"               // Awaiting review
  APPROVED = "approved"             // Approved by reviewer
  REJECTED = "rejected"             // Rejected by reviewer
  REVISION_NEEDED = "revision_needed"  // Needs revision
}
```

### EvaluationGrade
```typescript
enum EvaluationGrade {
  A = "A"  // Excellent (4 points)
  B = "B"  // Good (3 points)
  C = "C"  // Satisfactory (2 points)
  D = "D"  // Needs Improvement (1 point)
}
```


## API Endpoints

---

## Authentication API

**Base Path**: `/auth`

### POST /auth/login
Login user with email and password.

**Request Body**:
```typescript
{
  email: string;           // Email address
  password: string;        // Password (min 1 char)
}
```

**Response**: `Token`
```typescript
{
  access_token: string;    // JWT access token
  refresh_token: string;   // JWT refresh token
  token_type: "bearer";    // Token type
  expires_in: number;      // Token expiry in seconds
  user: UserResponse;      // User information
}
```

### POST /auth/refresh
Refresh access token using refresh token.

**Request Body**:
```typescript
{
  refresh_token: string;   // Refresh token
}
```

**Response**: `Token`

### POST /auth/logout
Logout current user.

**Response**: `MessageResponse`
```typescript
{
  message: string;         // Success message
  success: boolean;        // Operation status
  data?: object;           // Additional data
}
```

### GET /auth/me
Get current authenticated user information.

**Response**: `UserResponse`

### POST /auth/password-reset
Request password reset via email.

**Request Body**:
```typescript
{
  email: string;           // Email for password reset
}
```

**Response**: `MessageResponse`

### POST /auth/password-reset/confirm
Confirm password reset with token.

**Request Body**:
```typescript
{
  token: string;           // Password reset token
  new_password: string;    // New password (min 6 chars)
}
```

**Response**: `MessageResponse`

### POST /auth/change-password
Change current user's password.

**Request Body**:
```typescript
{
  current_password: string;  // Current password
  new_password: string;      // New password (min 6 chars)
}
```

**Response**: `MessageResponse`

---

## Users API

**Base Path**: `/users`

### GET /users/me
Get current user's profile.

**Response**: `UserResponse`
```typescript
{
  id: number;
  email: string;
  profile: {               // User profile as JSON
    name: string;          // Required: User's full name
    [key: string]: any;    // Additional profile fields
  };
  organization_id?: number;
  status: UserStatus;
  email_verified_at?: string;
  last_login_at?: string;
  created_at: string;
  updated_at?: string;
  display_name: string;    // Computed from profile
  full_name: string;       // Computed from profile
  roles: string[];         // User roles
}
```

### PUT /users/me
Update current user's profile.

**Request Body**: `UserUpdate`
```typescript
{
  email?: string;          // Email (auto-normalized)
  profile?: {              // Profile updates
    [key: string]: any;
  };
  organization_id?: number;
  status?: UserStatus;
}
```

**Response**: `UserResponse`

### GET /users
List all users (Admin/Manager only).

**Query Parameters**:
- `page`: number (default: 1)
- `size`: number (default: 10, max: 100)
- `search`: string - Search in name, email
- `role`: UserRole - Filter by role
- `status`: UserStatus - Filter by status
- `organization_id`: number - Filter by organization
- `sort_by`: string (default: "created_at")
- `sort_order`: "asc"|"desc" (default: "desc")
- `created_after`: date - Filter by creation date
- `created_before`: date - Filter by creation date
- `is_active`: boolean - Filter by active status

**Response**: `UserListResponse`
```typescript
{
  items: UserResponse[];   // List of users
  total: number;           // Total count
  page: number;            // Current page
  size: number;            // Items per page
  pages: number;           // Total pages
}
```

### POST /users
Create new user (Admin only).

**Query Parameters**:
- `organization_id`: number - Organization for user

**Request Body**: `UserCreate`
```typescript
{
  email: string;           // User email
  profile: {               // User profile (must contain 'name')
    name: string;          // Required field
    [key: string]: any;
  };
  organization_id?: number;
  status?: UserStatus;     // Default: ACTIVE
  password?: string;       // Optional, uses default if not provided
}
```

**Response**: `UserResponse`

### GET /users/{user_id}
Get user by ID (Admin/Manager only).

**Response**: `UserResponse`

### PUT /users/{user_id}
Update user (Admin only).

**Request Body**: `UserUpdate`

**Response**: `UserResponse`

### DELETE /users/{user_id}
Soft delete user (Admin only).

**Response**: `MessageResponse`

---

## Organizations API

**Base Path**: `/organizations`

### GET /organizations
List organizations with filtering and pagination.

**Query Parameters**:
- `page`: number (default: 1)
- `size`: number (default: 10, max: 100)
- `q`: string - Search in name or description
- `has_users`: boolean - Filter orgs with/without users
- `has_head`: boolean - Filter orgs with/without head
- `sort_by`: string (default: "name")
- `sort_order`: "asc"|"desc" (default: "asc")

**Response**: `OrganizationListResponse`
```typescript
{
  items: OrganizationResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
```

### POST /organizations
Create organization (Admin only).

**Request Body**: `OrganizationCreate`
```typescript
{
  name: string;            // Organization name (1-255 chars)
  description?: string;    // Optional description
  head_id?: number;        // Optional head/principal ID
}
```

**Response**: `OrganizationResponse`
```typescript
{
  id: number;
  name: string;
  description?: string;
  head_id?: number;
  created_at: string;
  updated_at?: string;
  display_name: string;    // Computed display name
  user_count: number;      // Number of users in org
  head_name?: string;      // Head's name if assigned
}
```

### GET /organizations/{org_id}
Get organization by ID.

**Response**: `OrganizationResponse`

### PUT /organizations/{org_id}
Update organization (Admin/Manager only).

**Request Body**: `OrganizationUpdate`

**Response**: `OrganizationResponse`

### DELETE /organizations/{org_id}
Delete organization (Admin only).

**Response**: `MessageResponse`

---

## Periods API

**Base Path**: `/periods`

### GET /periods
Get periods with filters.

**Query Parameters**:
- `academic_year`: string - Filter by academic year
- `semester`: string - Filter by semester  
- `is_active`: boolean - Filter by active status
- `skip`: number (default: 0, min: 0) - Items to skip
- `limit`: number (default: 100, max: 1000) - Max items

**Response**: `PeriodListResponse`
```typescript
{
  items: PeriodResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
```

### POST /periods
Create new period (Admin/Manager only).

**Request Body**: `PeriodCreate`
```typescript
{
  academic_year: string;   // e.g., "2023/2024" (max 20 chars)
  semester: string;        // e.g., "Ganjil", "Genap" (max 20 chars)
  start_date: string;      // Period start date (YYYY-MM-DD)
  end_date: string;        // Period end date (must be after start_date)
  description?: string;    // Optional description
}
```

**Response**: `PeriodResponse`
```typescript
{
  id: number;
  academic_year: string;
  semester: string;
  start_date: string;
  end_date: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  created_by?: number;
  updated_by?: number;
}
```

### GET /periods/active
Get active periods.

**Response**: `PeriodResponse[]`

### GET /periods/current
Get current periods (active by date).

**Response**: `PeriodResponse[]`

### GET /periods/{period_id}
Get period by ID.

**Response**: `PeriodResponse`

### GET /periods/{period_id}/stats
Get period with statistics (Admin/Manager only).

**Response**: `PeriodWithStats`
```typescript
{
  // All PeriodResponse fields plus:
  total_teachers: number;
  total_evaluations: number;
  total_rpp_submissions: number;
}
```

### PUT /periods/{period_id}
Update period (Admin/Manager only).

**Request Body**: `PeriodUpdate`

**Response**: `PeriodResponse`

### PATCH /periods/{period_id}/activate
Activate period (Admin/Manager only).

**Response**: `PeriodResponse`

### PATCH /periods/{period_id}/deactivate
Deactivate period (Admin/Manager only).

**Response**: `PeriodResponse`

### DELETE /periods/{period_id}
Delete period (Admin only).

**Response**: `MessageResponse`

---

## Evaluation Aspects API

**Base Path**: `/evaluation-aspects`

### GET /evaluation-aspects
List evaluation aspects with filtering.

**Query Parameters**:
- `page`: number (default: 1)
- `size`: number (default: 10, max: 100)
- `q`: string - Search query
- `category`: string - Filter by category
- `is_active`: boolean - Filter by active status
- `has_evaluations`: boolean - Filter aspects with evaluations
- `created_after`: date
- `created_before`: date
- `sort_by`: string (default: "created_at")
- `sort_order`: "asc"|"desc" (default: "desc")

**Response**: `EvaluationAspectListResponse`

### POST /evaluation-aspects
Create evaluation aspect (Admin only).

**Request Body**: `EvaluationAspectCreate`
```typescript
{
  aspect_name: string;     // Name (1-255 chars)
  category: string;        // Category (1-100 chars)
  description?: string;    // Optional description
  is_active?: boolean;     // Default: true
}
```

**Response**: `EvaluationAspectResponse`
```typescript
{
  id: number;
  aspect_name: string;
  category: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  evaluation_count: number; // Computed statistics
}
```

### GET /evaluation-aspects/active/list
Get all active evaluation aspects.

**Response**: `EvaluationAspectSummary[]`

### GET /evaluation-aspects/category/{category}
Get aspects by category.

**Response**: `EvaluationAspectSummary[]`

### GET /evaluation-aspects/{aspect_id}
Get evaluation aspect by ID.

**Response**: `EvaluationAspectResponse`

### PUT /evaluation-aspects/{aspect_id}
Update evaluation aspect (Admin only).

**Request Body**: `EvaluationAspectUpdate`

**Response**: `EvaluationAspectResponse`

### DELETE /evaluation-aspects/{aspect_id}
Delete evaluation aspect (Admin only).

**Query Parameters**:
- `force`: boolean (default: false) - Force delete with evaluations

**Response**: `MessageResponse`

---

## Teacher Evaluations API

**Base Path**: `/teacher-evaluations`

### POST /teacher-evaluations
Create teacher evaluation (Admin/Manager only).

**Request Body**: `TeacherEvaluationCreate`
```typescript
{
  teacher_id: number;      // Teacher being evaluated
  aspect_id: number;       // Evaluation aspect
  period_id: number;       // Evaluation period
  grade: EvaluationGrade;  // Grade (A, B, C, D)
  notes?: string;          // Optional notes
  evaluator_id: number;    // Evaluator user ID
}
```

**Response**: `TeacherEvaluationResponse`
```typescript
{
  id: number;
  teacher_id: number;
  aspect_id: number;
  period_id: number;
  grade: EvaluationGrade;
  notes?: string;
  evaluator_id: number;
  score: number;           // Computed: A=4, B=3, C=2, D=1
  evaluation_date: string;
  created_at: string;
  updated_at?: string;
  grade_description: string; // Computed description
  // Related data:
  evaluator_name?: string;
  teacher_name?: string;
  aspect_name?: string;
  period_name?: string;
}
```

### GET /teacher-evaluations/period/{period_id}
Get evaluations by period.

**Response**: `TeacherEvaluationResponse[]`

### GET /teacher-evaluations/teacher/{teacher_id}/period/{period_id}
Get teacher evaluations in period.

**Response**: `TeacherEvaluationResponse[]`

### PUT /teacher-evaluations/{evaluation_id}/grade
Update evaluation grade.

**Request Body**: `TeacherEvaluationUpdate`
```typescript
{
  grade?: EvaluationGrade;
  notes?: string;
}
```

**Response**: `TeacherEvaluationResponse`

### PATCH /teacher-evaluations/bulk-grade
Bulk update evaluation grades.

**Request Body**: `TeacherEvaluationBulkUpdate`

**Response**: `MessageResponse`

### POST /teacher-evaluations/assign-teachers-to-period
Auto-assign teachers to evaluation period (Admin/Manager only).

**Request Body**: `AssignTeachersToPeriod`

**Response**: `MessageResponse`

---

## RPP Submissions API

**Base Path**: `/rpp-submissions`

### POST /rpp-submissions
Create RPP submission (Teachers only).

**Request Body**: `RPPSubmissionCreate`
```typescript
{
  period_id: number;       // Submission period
  rpp_type: string;        // Type of RPP (1-100 chars)
  file_id: number;         // Associated media file
  teacher_id: number;      // Submitting teacher
}
```

**Response**: `RPPSubmissionResponse`
```typescript
{
  id: number;
  teacher_id: number;
  period_id: number;
  rpp_type: string;
  file_id: number;
  status: RPPStatus;
  reviewer_id?: number;
  review_notes?: string;
  revision_count: number;
  submitted_at: string;
  reviewed_at?: string;
  created_at: string;
  updated_at?: string;
  // Status flags:
  is_pending: boolean;
  is_approved: boolean;
  is_rejected: boolean;
  needs_revision: boolean;
  // Related data:
  teacher_name?: string;
  reviewer_name?: string;
  file_name?: string;
  period_name?: string;
}
```

### GET /rpp-submissions
List RPP submissions with filtering.

**Query Parameters**:
- `page`: number (default: 1)
- `size`: number (default: 10, max: 100)
- `teacher_id`: number - Filter by teacher
- `reviewer_id`: number - Filter by reviewer
- `period_id`: number - Filter by period
- `rpp_type`: string - Filter by RPP type
- `status`: RPPStatus - Filter by status
- `has_reviewer`: boolean - Filter by reviewer assignment
- `needs_review`: boolean - Filter submissions needing review
- `submitted_after`: date - Filter by submission date
- `submitted_before`: date - Filter by submission date
- `reviewed_after`: date - Filter by review date
- `reviewed_before`: date - Filter by review date

**Response**: `RPPSubmissionListResponse`

### GET /rpp-submissions/{submission_id}
Get RPP submission by ID.

**Response**: `RPPSubmissionResponse`

### PUT /rpp-submissions/{submission_id}
Update RPP submission (Teachers only, pending submissions).

**Request Body**: `RPPSubmissionUpdate`

**Response**: `RPPSubmissionResponse`

### POST /rpp-submissions/{submission_id}/review
Review RPP submission (Principals only).

**Request Body**: `RPPSubmissionReview`
```typescript
{
  action: "approve" | "reject" | "revision"; // Review action
  review_notes?: string;                     // Optional review notes
}
```

**Response**: `RPPSubmissionResponse`

### POST /rpp-submissions/{submission_id}/resubmit
Resubmit RPP submission (Teachers only).

**Request Body**: `RPPSubmissionResubmit`
```typescript
{
  file_id: number;         // New file ID
  notes?: string;          // Optional resubmission notes
}
```

**Response**: `RPPSubmissionResponse`

---

## Media Files API

**Base Path**: `/media-files`

### POST /media-files/upload
Upload file.

**Content-Type**: `multipart/form-data`

**Request Body**:
- `file`: File (max 100MB)
- `is_public`: boolean (default: false) - Public accessibility

**Response**: `MediaFileUploadResponse`
```typescript
{
  file: MediaFileResponse;
  upload_url?: string;     // Direct upload URL if applicable
}
```

### GET /media-files
List media files.

**Query Parameters**:
- `page`: number (default: 1)
- `size`: number (default: 10, max: 100)
- `q`: string - Search in filename
- `file_type`: string - Filter by file type
- `file_category`: string - Filter by category
- `uploader_id`: number - Filter by uploader
- `organization_id`: number - Filter by organization
- `is_public`: boolean - Filter by public access
- `min_size`: number - Minimum file size
- `max_size`: number - Maximum file size

**Response**: `MediaFileListResponse`

### GET /media-files/{file_id}
Get media file details.

**Response**: `MediaFileResponse`
```typescript
{
  id: number;
  file_name: string;       // Original filename (1-255 chars)
  file_type: string;       // File extension (1-50 chars)
  mime_type: string;       // MIME type (max 100 chars)
  file_path: string;       // Storage path
  file_size: number;       // Size in bytes
  uploader_id?: number;    // Uploader user ID
  organization_id?: number;
  file_metadata?: object;  // File metadata as JSON
  is_public: boolean;      // Public accessibility
  created_at: string;
  updated_at?: string;
  // Computed fields:
  display_name: string;
  extension: string;
  file_size_formatted: string;
  file_category: string;
  can_preview: boolean;
  // Related data:
  uploader_name?: string;
  organization_name?: string;
}
```

### GET /media-files/{file_id}/download
Download media file.

**Response**: File content with download headers

### PUT /media-files/{file_id}
Update media file metadata.

**Request Body**: `MediaFileUpdate`

**Response**: `MediaFileResponse`

### DELETE /media-files/{file_id}
Delete media file.

**Response**: `MessageResponse`

---

## User Roles API

**Base Path**: `/user-roles`

### POST /user-roles
Create user role (Admin only).

**Request Body**: `UserRoleCreate`
```typescript
{
  user_id: number;
  role_name: string;       // Role name (1-50 chars)
  permissions?: object;    // Permissions as JSON
  organization_id?: number; // Organization context
  expires_at?: string;     // Role expiration
}
```

**Response**: `UserRoleResponse`
```typescript
{
  id: number;
  user_id: number;
  role_name: string;
  permissions?: object;
  organization_id?: number;
  is_active: boolean;
  expires_at?: string;
  created_at: string;
  updated_at?: string;
  // Related data:
  user_email?: string;
  user_name?: string;
  organization_name?: string;
}
```

### GET /user-roles
List user roles (Admin/Manager only).

**Query Parameters**:
- `page`: number (default: 1)
- `size`: number (default: 10, max: 100)
- `q`: string - Search query
- `user_id`: number - Filter by user
- `role_name`: string - Filter by role
- `organization_id`: number - Filter by organization
- `is_active`: boolean - Filter by status
- `expires_soon`: number (1-365) - Expiring within N days

**Response**: `UserRoleListResponse`

### GET /user-roles/users/{user_id}/roles
Get user's roles (Admin/Manager only).

**Query Parameters**:
- `active_only`: boolean (default: true)

**Response**: `UserRoleResponse[]`

### POST /user-roles/assign
Assign role to user (Admin only).

**Query Parameters**:
- `user_id`: number (required)
- `role_name`: string (required)
- `organization_id`: number (optional)
- `expires_at`: datetime (optional)

**Response**: `UserRoleResponse`

### POST /user-roles/revoke
Revoke role from user (Admin only).

**Query Parameters**:
- `user_id`: number (required)
- `role_name`: string (required)
- `organization_id`: number (optional)

**Response**: `MessageResponse`

---

## Dashboard API

**Base Path**: `/dashboard`

### GET /dashboard
Get dashboard data (role-based).

**Query Parameters**:
- `period_id`: number (required) - Period for dashboard data
- `organization_id`: number (optional, admin only) - Filter by organization
- `include_inactive`: boolean (default: false) - Include inactive data

**Response**: `DashboardResponse`
```typescript
{
  period?: {
    id: number;
    academic_year: string;
    semester: string;
    is_active: boolean;
  };
  rpp_stats: {
    total_submissions: number;
    pending_submissions: number;
    approved_submissions: number;
    rejected_submissions: number;
    revision_needed_submissions: number;
    avg_review_time_hours?: number;
    submission_rate: number;
  };
  evaluation_stats: {
    total_evaluations: number;
    completed_evaluations: number;
    pending_evaluations: number;
    completion_rate: number;
    avg_score?: number;
    grade_distribution: {
      A: number;
      B: number;
      C: number;
      D: number;
    };
    total_teachers: number;
    total_aspects: number;
  };
  organizations?: OrganizationSummary[];
  user_role: string;
  organization_name?: string;
  last_updated: string;
}
```

### GET /dashboard/teacher
Get teacher-specific dashboard.

**Query Parameters**:
- `period_id`: number (required)

**Response**: `TeacherDashboard`

### GET /dashboard/principal
Get principal-specific dashboard.

**Query Parameters**:
- `period_id`: number (required)

**Response**: `PrincipalDashboard`

### GET /dashboard/admin
Get admin-specific dashboard.

**Query Parameters**:
- `period_id`: number (required)
- `organization_id`: number (optional)

**Response**: `AdminDashboard`

---

## Error Responses

### Standard Error Response
```typescript
{
  error: string;           // Error message
  detail?: string;         // Detailed error description
  code?: string;           // Error code
}
```

### Validation Error Response
```typescript
{
  error: "Validation Error";
  details: [
    {
      field: string;       // Field with error
      message: string;     // Error message
      type: string;        // Error type
    }
  ];
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Permission Summary

### Admin (`admin`)
- Full system access
- Manage all entities
- View system-wide analytics
- User and role management

### Principal (`kepala_sekolah`)
- Organization-scoped access
- Approve RPP submissions
- Manage teacher evaluations
- View organization analytics

### Teacher (`guru`)
- Personal data access
- Submit RPP files
- View own evaluations
- Limited read permissions

### Authentication Requirements
- All endpoints require authentication except public media files
- Role-based access control applied automatically
- Organization context enforced for principals and teachers
- Token expiration and refresh handled automatically