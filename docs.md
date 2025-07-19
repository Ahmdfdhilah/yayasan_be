# PKG (Penilaian Kinerja Guru) - Business Process Schema

## 1. System Overview

PKG adalah sistem penilaian kinerja guru yang mengelola seluruh siklus evaluasi guru mulai dari pengajuan RPP hingga hasil evaluasi akhir. Sistem ini mengimplementasikan kontrol akses berbasis peran dengan alur kerja yang jelas untuk setiap stakeholder.

## 2. Actor dan Peran

### Actor Utama:
- **Super Admin** (`super_admin`): Akses penuh sistem, manajemen multi-organisasi
- **Admin** (`admin`): Fungsi administratif, manajemen pengguna
- **Kepala Sekolah** (`kepala_sekolah`): Evaluator utama dan reviewer RPP
- **Guru** (`guru`): Mengajukan RPP dan menerima evaluasi
- **Content Manager** (`content_manager`): Manajemen konten website dan media

### Actor Pendukung:
- **Organisasi**: Sekolah, yayasan, atau departemen tempat guru bekerja
- **Sistem**: Kalkulasi otomatis dan notifikasi

## 3. Entitas Bisnis Utama

### Diagram Relasi:
```
Organisasi (1) ←→ (N) Pengguna
Pengguna (1) ←→ (N) Peran Pengguna
Pengguna (Guru) (1) ←→ (N) Pengajuan RPP
Pengguna (Reviewer) (1) ←→ (N) Pengajuan RPP (yang di-review)
Pengguna (Guru) (1) ←→ (N) Evaluasi Guru (yang dievaluasi)
Pengguna (Evaluator) (1) ←→ (N) Evaluasi Guru (yang melakukan)
Aspek Evaluasi (1) ←→ (N) Evaluasi Guru
Evaluasi Guru (N) ←→ (1) Hasil Evaluasi
```

## 4. Proses Bisnis Utama

### A. Proses Manajemen RPP

**Status Workflow**: `pending` → `approved` | `rejected` | `revision_needed`

#### 4.1 Alur Pengajuan RPP:

```mermaid
graph TD
    A[Guru Login] --> B[Akses Form RPP]
    B --> C[Isi Data RPP]
    C --> D[Upload File]
    D --> E[Validasi Sistem]
    E --> F[Submit RPP]
    F --> G[Status: Pending]
    G --> H[Notifikasi ke Kepala Sekolah]
```

**Langkah Detail:**
1. **Inisiasi Guru**: Guru login dan mengakses form pengajuan RPP
2. **Pengisian Form**:
   - Pilih tahun akademik dan semester
   - Tentukan jenis RPP (mata pelajaran/topik)
   - Upload file (PDF/DOC) ke sistem media
3. **Validasi**: Sistem validasi format file dan cek duplikasi
4. **Pengajuan**: Buat record dengan status `pending`, catat timestamp
5. **Notifikasi**: Kepala Sekolah menerima notifikasi review

#### 4.2 Alur Review RPP:

```mermaid
graph TD
    A[RPP Pending] --> B[Kepala Sekolah Review]
    B --> C{Keputusan}
    C -->|Approve| D[Status: Approved]
    C -->|Reject| E[Status: Rejected + Feedback]
    C -->|Revision| F[Status: Revision Needed]
    D --> G[Update Performance Record]
    E --> H[Notifikasi Guru]
    F --> H
    H --> I[Guru Dapat Resubmit]
```

**Langkah Detail:**
1. **Assignment Review**: Sistem otomatis assign atau admin manual assign reviewer
2. **Evaluasi Review**: Kepala Sekolah review konten dan berikan keputusan:
   - **Approve**: Status → `approved`, update performance record
   - **Reject**: Status → `rejected`, feedback detail diperlukan
   - **Minta Revisi**: Status → `revision_needed`, increment revision_count
3. **Delivery Feedback**: Guru menerima notifikasi dengan review_notes
4. **Resubmission**: Untuk kasus reject/revisi, guru dapat resubmit (buat versi baru)

#### 4.3 Aturan Bisnis RPP:
- Hanya satu RPP per guru per periode akademik per jenis RPP
- Hanya submission pending yang bisa diupdate
- Revision count dilacak untuk audit
- File versioning dipertahankan untuk referensi historis

### B. Proses Evaluasi Guru

**Formula Inti**: `Nilai Kinerja = Total Skor × 1.25`

#### 4.4 Setup Evaluasi:

```mermaid
graph TD
    A[Definisi Periode Akademik] --> B[Load Aspek Evaluasi Aktif]
    B --> C[Pilih Guru untuk Evaluasi]
    C --> D[Generate Form Dinamis]
    D --> E[Mulai Evaluasi]
```

#### 4.5 Proses Penilaian:

```mermaid
graph TD
    A[Evaluasi Aspek Individual] --> B[Aplikasi Bobot]
    B --> C[Tambah Catatan]
    C --> D[Kalkulasi Real-time]
    D --> E[Validasi Score]
    E --> F[Simpan Evaluasi]
```

**Langkah Detail:**
1. **Scoring Aspek Individual**: Setiap aspek dinilai pada skala yang ditentukan (biasanya 1-4)
2. **Aplikasi Bobot**: Skor dikalikan dengan bobot aspek
3. **Penambahan Catatan**: Evaluator memberikan catatan justifikasi
4. **Kalkulasi Real-time**: Sistem menampilkan preview kinerja yang dihitung
5. **Validasi**: Pastikan skor dalam rentang valid untuk setiap aspek

#### 4.6 Kalkulasi Hasil:

```mermaid
graph TD
    A[Agregasi Skor] --> B[Kalkulasi Kinerja]
    B --> C[Tentukan Grade]
    C --> D[Simpan Hasil]
    
    E[Total Skor = Σ(Skor × Bobot)] --> A
    F[Nilai Kinerja = Total Skor × 1.25] --> B
    G[Grade berdasarkan Threshold] --> C
```

**Formula dan Grading:**
1. **Agregasi**: `Total Skor = Σ(Skor Individual × Bobot)`
2. **Kalkulasi Kinerja**: `Nilai Kinerja = Total Skor × 1.25`
3. **Penentuan Grade**:
   - **Sangat Baik** (≥90%): Melebihi ekspektasi
   - **Baik** (80-89%): Memenuhi dan kadang melebihi ekspektasi
   - **Cukup** (70-79%): Memenuhi ekspektasi dasar
   - **Perlu Perbaikan** (<70%): Di bawah ekspektasi

#### 4.7 Aturan Bisnis Evaluasi:
- Satu evaluasi per guru per aspek per periode akademik
- Aspek harus aktif untuk digunakan dalam evaluasi
- Skor harus dalam rentang min/max aspek
- Constraint unik mencegah evaluasi duplikat
- Weighted scoring memungkinkan assignment kepentingan fleksibel

### C. Manajemen Data dan Analytics

#### 4.8 Performance Tracking:
- **Progress Individual**: Tren kinerja guru dari waktu ke waktu
- **Analisis Komparatif**: Kinerja guru vs rata-rata organisasi
- **Ringkasan Periode**: Kinerja seluruh sekolah untuk periode tertentu
- **Top Performers**: Identifikasi guru teladan
- **Perlu Perbaikan**: Guru yang memerlukan dukungan pengembangan

#### 4.9 Audit dan Compliance:
- Audit trail lengkap untuk semua evaluasi
- Riwayat revisi untuk submission RPP
- Logging akses untuk monitoring keamanan
- Kontrol akses data berbasis permission

## 5. Aturan Bisnis dan Constraint Kunci

### Aturan Integritas Data:
1. **Constraint Keunikan**:
   - Satu submission RPP per guru/periode/jenis kombinasi
   - Satu evaluasi per guru/aspek/periode kombinasi
   - Satu hasil evaluasi per guru per periode akademik

2. **Aturan Validasi**:
   - Skor harus dalam rentang yang ditentukan aspek
   - File harus memenuhi requirement format
   - User harus punya peran yang sesuai untuk aksi
   - Periode akademik harus format valid

3. **Aturan Transisi State**:
   - Hanya RPP pending yang bisa diedit
   - Hanya aspek aktif yang bisa digunakan untuk evaluasi
   - Hasil evaluasi immutable setelah dibuat
   - Permission peran enforces action boundaries

### Constraint Logika Bisnis:
1. **Constraint Temporal**:
   - Tahun akademik mengikuti format standar (contoh: "2023/2024")
   - Semester distandarisasi ("Ganjil", "Genap")
   - Periode evaluasi punya window yang ditentukan

2. **Constraint Organisasi**:
   - User belong ke organisasi spesifik
   - Evaluasi biasanya terjadi dalam organisasi sama
   - Permission peran respects organizational boundaries

3. **Constraint Performance**:
   - Skala evaluasi standar 4-point
   - Multiplier 1.25 untuk kalkulasi kinerja
   - Threshold grade distandarisasi across sistem

## 6. Flow Diagram Proses Utama

### 6.1 Complete RPP Workflow

```mermaid
stateDiagram-v2
    [*] --> Draft: Guru mulai buat RPP
    Draft --> Pending: Submit RPP
    Pending --> Approved: Kepala Sekolah approve
    Pending --> Rejected: Kepala Sekolah reject
    Pending --> RevisionNeeded: Kepala Sekolah minta revisi
    Rejected --> Draft: Guru buat RPP baru
    RevisionNeeded --> Draft: Guru revisi
    Approved --> [*]: Selesai
```

### 6.2 Complete Evaluation Workflow

```mermaid
stateDiagram-v2
    [*] --> Setup: Buat evaluasi baru
    Setup --> InProgress: Mulai evaluasi aspek
    InProgress --> InProgress: Evaluasi aspek selanjutnya
    InProgress --> Completed: Semua aspek selesai
    Completed --> ResultCalculated: Sistem hitung hasil
    ResultCalculated --> [*]: Selesai
```

## 7. Matriks Peran dan Akses

| Fungsi | Super Admin | Admin | Kepala Sekolah | Guru | Content Manager |
|--------|-------------|-------|----------------|------|-----------------|
| Manajemen User | ✓ | ✓ | ✓ (terbatas) | ✗ | ✗ |
| Submit RPP | ✗ | ✗ | ✗ | ✓ | ✗ |
| Review RPP | ✓ | ✓ | ✓ | ✗ | ✗ |
| Buat Evaluasi | ✓ | ✓ | ✓ | ✗ | ✗ |
| Lihat Hasil Evaluasi | ✓ | ✓ | ✓ | ✓ (sendiri) | ✗ |
| Manajemen Aspek | ✓ | ✓ | ✓ | ✗ | ✗ |
| Manajemen Media | ✓ | ✓ | ✗ | ✗ | ✓ |
| Analytics | ✓ | ✓ | ✓ | ✓ (terbatas) | ✗ |

## 8. Integrasi Sistem

### Dependency Eksternal:
- **File Storage**: Manajemen media file untuk dokumen RPP
- **Email System**: Notifikasi untuk submission dan evaluasi
- **Authentication**: Keamanan berbasis JWT dengan verifikasi peran
- **Database**: Integritas transaksional untuk data evaluasi

### Integrasi Internal:
- **User Management**: Kontrol akses berbasis peran
- **Organization Management**: Separasi data multi-tenant
- **Analytics Engine**: Kalkulasi kinerja dan reporting
- **Audit System**: Change tracking dan compliance monitoring

## 9. Faktor Kesuksesan Kritis

### Operational Excellence:
1. **Akurasi Data**: Scoring dan kalkulasi evaluasi yang presisi
2. **Efisiensi Proses**: Workflow submission dan review yang streamlined
3. **User Experience**: Interface intuitif untuk semua peran stakeholder
4. **System Reliability**: High availability untuk periode evaluasi kritis

### Compliance dan Governance:
1. **Audit Trail**: Tracking lengkap semua aktivitas sistem
2. **Access Control**: Permission berbasis peran yang ketat
3. **Data Privacy**: Handling aman data kinerja guru
4. **Regulatory Compliance**: Adherence ke standar kementerian pendidikan

---

## 10. API Endpoints dan Implementasi

### Endpoint yang Tersedia:

#### A. Authentication & User Management
- **`/auth`** - Autentikasi dan authorization
- **`/users`** - Manajemen pengguna 
- **`/user-roles`** - Manajemen peran pengguna
- **`/organizations`** - Manajemen organisasi

#### B. Core Evaluation System  
- **`/evaluation-aspects`** - Manajemen aspek evaluasi
  - CRUD operations untuk aspek evaluasi
  - Validasi bobot aspek
  - Analytics aspek performance
  - Bulk operations (create, update, delete)
  
- **`/teacher-evaluations`** - Evaluasi individual per aspek
  - Create/update evaluasi untuk setiap aspek
  - Bulk operations untuk multiple evaluations
  - Evaluation set creation (complete teacher evaluation)
  - Teacher performance analysis
  
- **`/evaluation-results`** - Hasil evaluasi teragregasi
  - Calculate results from individual evaluations
  - Performance comparison dan trend analysis
  - Top performers dan improvement needed
  - Organization-wide performance overview

#### C. RPP Management System
- **`/rpp-submissions`** - Pengajuan dan review RPP
  - Submit, update, delete RPP submissions
  - Review workflow (approve/reject/revision)
  - Resubmit capability untuk rejected submissions
  - Bulk operations untuk mass review
  - Analytics: submission stats, teacher progress, reviewer workload

#### D. Media File System
- **`/media-files`** - Manajemen file upload/download
  - File upload dengan access control
  - Download dengan permission checking
  - Public/private file management
  - File metadata management

#### E. Dashboard & Analytics
- **`/dashboard`** - Overview analytics dan monitoring
  - Dashboard overview untuk semua role
  - User-specific dashboard (guru perspective)
  - Organization dashboard (kepala sekolah perspective)
  - Admin dashboard (system-wide view)
  - Quick stats untuk widgets

### Proses Workflow yang Didukung:

#### 1. RPP Submission Workflow (Sesuai Docs):
```
POST /rpp-submissions/ → Create submission (status: pending)
GET /rpp-submissions/pending-reviews → List for review
POST /rpp-submissions/{id}/review → Approve/reject/request revision
POST /rpp-submissions/{id}/resubmit → Resubmit if needed
GET /rpp-submissions/analytics/overview → Track progress
```

#### 2. Teacher Evaluation Workflow (Sesuai Docs):
```
GET /evaluation-aspects/active/list → Load active aspects
POST /teacher-evaluations/evaluation-set → Create complete evaluation
GET /teacher-evaluations/teacher/{id}/summary/{year}/{semester} → Get results
POST /evaluation-results/calculate-from-evaluations → Generate final result
```

#### 3. Analytics dan Reporting (Mendukung Docs):
```
GET /rpp-submissions/analytics/comprehensive → RPP analytics
GET /teacher-evaluations/analytics/overview → Evaluation analytics  
GET /evaluation-results/analytics/overview → Results analytics
GET /evaluation-results/period/{year}/{semester}/top-performers → Performance ranking
```

#### 4. Dashboard dan Monitoring:
```
GET /dashboard/overview → Comprehensive dashboard untuk current user
GET /dashboard/user/{id} → User-specific dashboard (guru)
GET /dashboard/organization → Organization dashboard (kepala sekolah)
GET /dashboard/admin/overview → System-wide admin dashboard
GET /dashboard/quick-stats → Quick statistics untuk widgets
```

### Status Implementasi vs Business Process:

✅ **Implemented & Matching Docs:**
- Complete RPP workflow dengan review system
- Teacher evaluation dengan weighted scoring
- Performance calculation (Nilai Kinerja = Total Skor × 1.25)
- User role-based access control
- File upload/management untuk RPP documents
- Analytics untuk tracking progress
- Bulk operations untuk efficiency
- Dashboard system untuk monitoring dan overview

✅ **Business Rules Implemented:**
- Unique constraints (one RPP per teacher/period, one evaluation per teacher/aspect/period)
- Status workflow validation
- Permission-based access control
- Academic year/semester formatting
- Score validation dalam rentang yang ditentukan

⚠️ **Minor Gaps Remaining:**
- Notification system tidak ada explicit endpoints
- Email notification integration belum explicit di API
- Real-time updates/WebSocket tidak ada

### Rekomendasi Penambahan:

#### Optional Enhancement Endpoints:
1. **Notification System** (`/notifications`)  
   - In-app notifications
   - Notification preferences
   - Email notification triggers

2. **Reporting System** (`/reports`)
   - Comprehensive report generation
   - Export functionality (PDF, Excel)
   - Custom report templates

3. **Real-time Updates** (WebSocket)
   - Live updates untuk dashboard
   - Real-time notifications
   - Progress tracking updates

---

*Dokumen ini merepresentasikan skema proses bisnis lengkap untuk sistem PKG (Penilaian Kinerja Guru) yang mengelola evaluasi kinerja guru secara komprehensif. Semua endpoint utama telah diimplementasikan sesuai dengan business process yang didokumentasikan.*