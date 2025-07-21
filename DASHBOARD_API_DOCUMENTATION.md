# Dashboard API Documentation

## Overview
Dashboard API menyediakan data statistik dan ringkasan untuk sistem PKG (Penilaian Kinerja Guru) berdasarkan role pengguna yang berbeda. Setiap role memiliki akses dan tampilan data yang berbeda.

## Base URL
```
/api/v1/dashboard
```

## Authentication
Semua endpoint memerlukan autentikasi JWT token dengan role yang sesuai.

## Roles & Access Levels

| Role | Akses Data | Fitur Khusus |
|------|------------|--------------|
| **guru** (Teacher) | Data personal & organisasi | RPP submission status, evaluasi personal |
| **kepala_sekolah** (Principal) | Data organisasi | Review pending, teacher summaries |
| **admin** | Data sistem/organisasi | System overview, all organizations |

---

## Endpoints

### 1. General Dashboard

#### `GET /dashboard/`

**Deskripsi:** Endpoint utama untuk mendapatkan data dashboard berdasarkan role pengguna yang login.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period_id` | integer | ✅ | ID periode evaluasi |
| `organization_id` | integer | ❌ | Filter by organization (admin only) |
| `include_inactive` | boolean | ❌ | Include inactive periods/organizations (default: false) |

**Response:** Berbeda berdasarkan role user (TeacherDashboard/PrincipalDashboard/AdminDashboard)

**Example Request:**
```bash
curl -X GET \
  "/api/v1/dashboard/?period_id=1&include_inactive=false" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

### 2. Teacher Dashboard

#### `GET /dashboard/teacher`

**Deskripsi:** Dashboard khusus untuk guru dengan statistik personal.

**Access:** Hanya untuk role `guru`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period_id` | integer | ✅ | ID periode evaluasi |

**Response Schema:** `TeacherDashboard`

**Example Response:**
```json
{
  "period": {
    "period_id": 1,
    "period_name": "Semester Genap 2024/2025",
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2025-06-30T23:59:59",
    "is_active": true
  },
  "rpp_stats": {
    "total_submissions": 5,
    "pending_submissions": 1,
    "approved_submissions": 3,
    "rejected_submissions": 1,
    "pending_reviews": 0,
    "avg_review_time_hours": null,
    "submission_rate": 60.0
  },
  "evaluation_stats": {
    "total_evaluations": 8,
    "completed_evaluations": 6,
    "pending_evaluations": 2,
    "completion_rate": 75.0,
    "avg_score": 85.5,
    "grade_distribution": {
      "A": 4,
      "B": 2,
      "C": 0,
      "D": 0
    },
    "total_teachers": 1,
    "total_aspects": 4
  },
  "organizations": [
    {
      "organization_id": 1,
      "organization_name": "SMA Negeri 1 Jakarta",
      "total_teachers": 25,
      "rpp_stats": { /* organization RPP stats */ },
      "evaluation_stats": { /* organization evaluation stats */ }
    }
  ],
  "user_role": "guru",
  "organization_name": "SMA Negeri 1 Jakarta",
  "last_updated": "2025-07-21T10:30:00",
  "quick_stats": {
    "my_pending_rpps": 1,
    "my_pending_reviews": 0,
    "my_pending_evaluations": 2,
    "recent_activities": [
      {
        "type": "rpp_submission",
        "count": 1
      },
      {
        "type": "evaluations",
        "count": 2
      }
    ]
  },
  "my_rpp_stats": {
    "total_submissions": 3,
    "pending_submissions": 1,
    "approved_submissions": 2,
    "rejected_submissions": 0,
    "pending_reviews": 0,
    "avg_review_time_hours": null,
    "submission_rate": 66.7
  },
  "my_evaluation_stats": {
    "total_evaluations": 4,
    "completed_evaluations": 3,
    "pending_evaluations": 1,
    "completion_rate": 75.0,
    "avg_score": 88.0,
    "grade_distribution": {
      "A": 2,
      "B": 1,
      "C": 0,
      "D": 0
    },
    "total_teachers": 1,
    "total_aspects": 4
  }
}
```

---

### 3. Principal Dashboard

#### `GET /dashboard/principal`

**Deskripsi:** Dashboard khusus untuk kepala sekolah dengan statistik organisasi.

**Access:** Hanya untuk role `kepala_sekolah`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period_id` | integer | ✅ | ID periode evaluasi |

**Response Schema:** `PrincipalDashboard`

**Example Response:**
```json
{
  "period": {
    "period_id": 1,
    "period_name": "Semester Genap 2024/2025",
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2025-06-30T23:59:59",
    "is_active": true
  },
  "rpp_stats": {
    "total_submissions": 75,
    "pending_submissions": 12,
    "approved_submissions": 55,
    "rejected_submissions": 8,
    "pending_reviews": 12,
    "avg_review_time_hours": 24.5,
    "submission_rate": 73.3
  },
  "evaluation_stats": {
    "total_evaluations": 100,
    "completed_evaluations": 82,
    "pending_evaluations": 18,
    "completion_rate": 82.0,
    "avg_score": 84.2,
    "grade_distribution": {
      "A": 35,
      "B": 32,
      "C": 12,
      "D": 3
    },
    "total_teachers": 25,
    "total_aspects": 4
  },
  "organizations": [
    {
      "organization_id": 1,
      "organization_name": "SMA Negeri 1 Jakarta",
      "total_teachers": 25,
      "rpp_stats": { /* same as above */ },
      "evaluation_stats": { /* same as above */ }
    }
  ],
  "user_role": "kepala_sekolah",
  "organization_name": "SMA Negeri 1 Jakarta",
  "last_updated": "2025-07-21T10:30:00",
  "quick_stats": {
    "my_pending_rpps": 0,
    "my_pending_reviews": 12,
    "my_pending_evaluations": 0,
    "recent_activities": [
      {
        "type": "pending_reviews",
        "count": 12
      },
      {
        "type": "organization_overview",
        "count": 1
      }
    ]
  },
  "organization_overview": {
    "organization_name": "SMA Negeri 1 Jakarta",
    "total_teachers": 25,
    "active_teachers": 25,
    "head_name": "Dr. Siti Nurhaliza, M.Pd"
  },
  "teacher_summaries": [
    {
      "teacher_id": 3,
      "teacher_name": "Siti Rahayu, S.Pd",
      "total_rpps": 3,
      "approved_rpps": 2,
      "completion_rate": 66.7
    },
    {
      "teacher_id": 5,
      "teacher_name": "Ahmad Fauzi, S.Pd",
      "total_rpps": 4,
      "approved_rpps": 4,
      "completion_rate": 100.0
    }
  ]
}
```

---

### 4. Admin Dashboard

#### `GET /dashboard/admin`

**Deskripsi:** Dashboard khusus untuk administrator dengan statistik sistem.

**Access:** Hanya untuk role `admin`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period_id` | integer | ✅ | ID periode evaluasi |
| `organization_id` | integer | ❌ | Filter by specific organization |

**Response Schema:** `AdminDashboard`

**Example Response:**
```json
{
  "period": {
    "period_id": 1,
    "period_name": "Semester Genap 2024/2025",
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2025-06-30T23:59:59",
    "is_active": true
  },
  "rpp_stats": {
    "total_submissions": 450,
    "pending_submissions": 65,
    "approved_submissions": 320,
    "rejected_submissions": 65,
    "pending_reviews": 65,
    "avg_review_time_hours": 18.2,
    "submission_rate": 71.1
  },
  "evaluation_stats": {
    "total_evaluations": 600,
    "completed_evaluations": 485,
    "pending_evaluations": 115,
    "completion_rate": 80.8,
    "avg_score": 83.5,
    "grade_distribution": {
      "A": 180,
      "B": 195,
      "C": 85,
      "D": 25
    },
    "total_teachers": 150,
    "total_aspects": 4
  },
  "organizations": [
    {
      "organization_id": 1,
      "organization_name": "SMA Negeri 1 Jakarta",
      "total_teachers": 25,
      "rpp_stats": { /* organization specific stats */ },
      "evaluation_stats": { /* organization specific stats */ }
    },
    {
      "organization_id": 2,
      "organization_name": "SMA Negeri 2 Jakarta",
      "total_teachers": 30,
      "rpp_stats": { /* organization specific stats */ },
      "evaluation_stats": { /* organization specific stats */ }
    }
  ],
  "user_role": "admin",
  "organization_name": null,
  "last_updated": "2025-07-21T10:30:00",
  "system_overview": {
    "total_users": 200,
    "total_organizations": 6,
    "system_health": "good"
  },
  "organization_summaries": [
    {
      "organization_id": 1,
      "organization_name": "SMA Negeri 1 Jakarta",
      "total_teachers": 25,
      "rpp_stats": { /* stats */ },
      "evaluation_stats": { /* stats */ }
    }
  ],
  "recent_system_activities": [
    {
      "type": "system_overview",
      "message": "System running normally"
    },
    {
      "type": "data_summary",
      "message": "Dashboard data refreshed"
    }
  ]
}
```

---

### 5. Quick Stats

#### `GET /dashboard/quick-stats`

**Deskripsi:** Mendapatkan statistik ringkas untuk dashboard cards.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period_id` | integer | ✅ | ID periode evaluasi |

**Response Schema:** `QuickStats`

**Example Response:**
```json
{
  "my_pending_rpps": 2,
  "my_pending_reviews": 5,
  "my_pending_evaluations": 3,
  "recent_activities": [
    {
      "type": "rpp_submission",
      "count": 2
    },
    {
      "type": "pending_reviews",
      "count": 5
    }
  ]
}
```

---

## Response Schemas Detail

### RPPDashboardStats
```typescript
interface RPPDashboardStats {
  total_submissions: number;        // Total RPP submissions
  pending_submissions: number;      // Submissions pending review
  approved_submissions: number;     // Approved submissions
  rejected_submissions: number;     // Rejected submissions
  pending_reviews: number;          // Reviews pending for user
  avg_review_time_hours: number | null;  // Average review time
  submission_rate: number;          // Completion rate percentage
}
```

### TeacherEvaluationDashboardStats
```typescript
interface TeacherEvaluationDashboardStats {
  total_evaluations: number;        // Total evaluations
  completed_evaluations: number;    // Completed evaluations
  pending_evaluations: number;      // Pending evaluations
  completion_rate: number;          // Completion percentage
  avg_score: number | null;         // Average score
  grade_distribution: {             // Grade distribution
    A: number;
    B: number;
    C: number;
    D: number;
  };
  total_teachers: number;           // Number of teachers
  total_aspects: number;            // Number of evaluation aspects
}
```

### OrganizationSummary
```typescript
interface OrganizationSummary {
  organization_id: number;
  organization_name: string;
  total_teachers: number;
  rpp_stats: RPPDashboardStats;
  evaluation_stats: TeacherEvaluationDashboardStats;
}
```

### PeriodSummary
```typescript
interface PeriodSummary {
  period_id: number;
  period_name: string;
  start_date: string | null;       // ISO date format
  end_date: string | null;         // ISO date format
  is_active: boolean;
}
```

### QuickStats
```typescript
interface QuickStats {
  my_pending_rpps: number;
  my_pending_reviews: number;
  my_pending_evaluations: number;
  recent_activities: Array<{
    type: string;
    count: number;
  }>;
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Period ID is required"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied. This endpoint is only available for teachers (guru)."
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Usage Examples

### 1. Get Teacher Dashboard
```bash
curl -X GET \
  "/api/v1/dashboard/teacher?period_id=1" \
  -H "Authorization: Bearer <teacher_jwt_token>"
```

### 2. Get Principal Dashboard
```bash
curl -X GET \
  "/api/v1/dashboard/principal?period_id=1" \
  -H "Authorization: Bearer <principal_jwt_token>"
```

### 3. Get Admin Dashboard for Specific Organization
```bash
curl -X GET \
  "/api/v1/dashboard/admin?period_id=1&organization_id=1" \
  -H "Authorization: Bearer <admin_jwt_token>"
```

### 4. Get Quick Stats
```bash
curl -X GET \
  "/api/v1/dashboard/quick-stats?period_id=1" \
  -H "Authorization: Bearer <jwt_token>"
```

---

## Notes

1. **Period ID Required:** Semua endpoint memerlukan `period_id` untuk memfilter data berdasarkan periode evaluasi.

2. **Role-Based Access:** Setiap endpoint memiliki pembatasan akses berdasarkan role pengguna:
   - `/teacher` - Hanya untuk guru
   - `/principal` - Hanya untuk kepala sekolah  
   - `/admin` - Hanya untuk administrator

3. **Data Filtering:** Admin dapat memfilter data berdasarkan organisasi tertentu dengan parameter `organization_id`.

4. **Response Format:** Response berbeda berdasarkan role, tapi semua memiliki struktur dasar yang sama dengan field tambahan sesuai role.

5. **Real-time Data:** Data dashboard bersifat real-time dan dihitung dari database saat request.

6. **Performance:** Untuk performa optimal, pertimbangkan untuk cache hasil dashboard jika data tidak berubah frequently.