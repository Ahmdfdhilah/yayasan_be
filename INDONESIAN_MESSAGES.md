# Sistem Pesan Bahasa Indonesia

Sistem pesan terpusat untuk API responses dalam bahasa Indonesia.

## Struktur

### File Utama
- `src/utils/messages.py` - Mapping pesan dalam bahasa Indonesia
- Sudah diimplementasi di:
  - API endpoints: `auth.py`, `dashboard.py`, `media_files.py`, `rpp_submissions.py`, `users.py`
  - Services: `auth.py`, `organization.py`, `user.py`
  - Core exceptions: `exceptions.py`

## Cara Penggunaan

### 1. Import di file yang memerlukan
```python
from src.utils.messages import get_message
```

### 2. Mengganti hardcoded message
Dari:
```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found"
)
```

Menjadi:
```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=get_message("user", "not_found")
)
```

### 3. Untuk pesan dengan parameter
```python
# Untuk pesan dengan placeholder
get_message("period", "not_active_with_id", period_id=123)
# Hasil: "Periode 123 tidak aktif. Operasi hanya diperbolehkan pada periode yang aktif."
```

## Kategori Pesan

### AUTH (Autentikasi)
- `invalid_credentials` - "Email atau kata sandi salah"
- `admin_role_required` - "Peran administrator diperlukan"
- `not_authorized_check_password_reset` - "Tidak memiliki otorisasi untuk memeriksa kelayakan reset kata sandi pengguna lain"

### ACCESS (Kontrol Akses)
- `teacher_only` - "Akses ditolak. Endpoint ini hanya tersedia untuk guru."
- `principal_only` - "Akses ditolak. Endpoint ini hanya tersedia untuk kepala sekolah."
- `admin_only` - "Akses ditolak. Endpoint ini hanya tersedia untuk administrator."

### USER (Pengguna)
- `not_found` - "Pengguna tidak ditemukan"
- `email_exists` - "Email sudah terdaftar"

### ORGANIZATION (Organisasi)
- `not_found` - "Organisasi tidak ditemukan"
- `name_exists` - "Nama organisasi sudah ada"

### PERIOD (Periode)
- `not_active` - "Periode tidak aktif. Operasi hanya diperbolehkan pada periode yang aktif."
- `not_found` - "Periode tidak ditemukan."

### SUBMISSION (Pengajuan)
- `own_submissions_only` - "Anda hanya dapat melihat pengajuan Anda sendiri"

## Status Implementasi

✅ **Selesai:**
- Struktur pesan dasar
- Core exceptions
- **API Endpoints:**
  - Auth endpoints (`auth.py`)
  - Dashboard endpoints (`dashboard.py`)
  - Media files endpoints (`media_files.py`)
  - RPP submissions endpoints (`rpp_submissions.py`)
  - Users endpoints (`users.py`)
- **Service Layer:**
  - Auth service (`auth.py`)
  - Organization service (`organization.py`)
  - User service (`user.py`)
  - Media file service (`media_file.py`)
  - RPP submission service (`rpp_submission.py`)
  - Dashboard service (`dashboard.py`)
  - Period service (`period.py`)
  - Teacher evaluation service (`teacher_evaluation.py`)
  - Evaluation aspect service (`evaluation_aspect.py`)
  - User role service (`user_role.py`)
- **Repository Layer:**
  - Period repository (`period.py`) - Status aktivasi periode
  - Teacher evaluation repository (`teacher_evaluation.py`) - Error messages untuk bulk update

🔄 **Masih perlu diupdate:**
- Endpoint lainnya (organizations, periods, teacher_evaluations, user_roles, evaluation_aspects)

## Keuntungan Sistem Ini

1. **Konsistensi** - Semua pesan error menggunakan bahasa Indonesia
2. **Maintainability** - Pesan terpusat, mudah diubah
3. **Flexibility** - Mendukung parameter dinamis
4. **Standardization** - Format pesan yang konsisten di seluruh aplikasi