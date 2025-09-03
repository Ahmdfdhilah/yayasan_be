"""Indonesian message mappings for API responses."""

class Messages:
    """Centralized Indonesian messages for API responses."""
    
    # Authentication messages
    AUTH = {
        "not_authorized_check_password_reset": "Tidak memiliki otorisasi untuk memeriksa kelayakan reset kata sandi pengguna lain",
        "admin_role_required": "Peran administrator diperlukan",
        "invalid_credentials": "Email atau kata sandi salah",
        "user_not_found": "Pengguna tidak ditemukan",
        "access_token_expired": "Token akses telah kedaluwarsa",
        "refresh_token_expired": "Token refresh telah kedaluwarsa",
        "invalid_token": "Token tidak valid",
    }
    
    # Access control messages
    ACCESS = {
        "teacher_only": "Akses ditolak. Endpoint ini hanya tersedia untuk guru.",
        "principal_only": "Akses ditolak. Endpoint ini hanya tersedia untuk kepala sekolah.",
        "admin_only": "Akses ditolak. Endpoint ini hanya tersedia untuk administrator.",
        "own_data_only": "Anda hanya dapat melihat data Anda sendiri",
        "not_authorized_view_files": "Tidak memiliki otorisasi untuk melihat file pengguna ini",
    }
    
    # Period messages
    PERIOD = {
        "not_active": "Periode tidak aktif. Operasi hanya diperbolehkan pada periode yang aktif.",
        "not_active_with_id": "Periode {period_id} tidak aktif. Operasi hanya diperbolehkan pada periode yang aktif.",
        "not_found": "Periode tidak ditemukan.",
        "not_found_with_id": "Periode {period_id} tidak ditemukan.",
    }
    
    # General CRUD messages
    CRUD = {
        "created": "Data berhasil dibuat",
        "updated": "Data berhasil diperbarui",
        "deleted": "Data berhasil dihapus",
        "not_found": "Data tidak ditemukan",
        "already_exists": "Data sudah ada",
        "operation_failed": "Operasi gagal",
    }
    
    # Organization messages
    ORGANIZATION = {
        "not_found": "Organisasi tidak ditemukan",
        "name_exists": "Nama organisasi sudah ada",
        "code_exists": "Kode organisasi sudah ada",
        "has_dependencies": "Organisasi tidak dapat dihapus karena masih memiliki dependensi",
    }
    
    # User messages
    USER = {
        "not_found": "Pengguna tidak ditemukan",
        "email_exists": "Email sudah terdaftar",
        "username_exists": "Username sudah ada",
        "invalid_role": "Peran pengguna tidak valid",
        "password_reset_sent": "Email reset kata sandi telah dikirim",
    }
    
    # File messages
    FILE = {
        "upload_failed": "Gagal mengunggah file",
        "invalid_format": "Format file tidak valid",
        "file_too_large": "Ukuran file terlalu besar",
        "file_not_found": "File tidak ditemukan",
        "file_uploaded": "File berhasil diunggah",
    }
    
    # Submission messages
    SUBMISSION = {
        "own_submissions_only": "Anda hanya dapat melihat pengajuan Anda sendiri",
        "submission_not_found": "Pengajuan tidak ditemukan",
        "submission_exists": "Pengajuan sudah ada untuk periode ini",
        "invalid_status": "Status pengajuan tidak valid",
        "submission_notes_must_have": "Harus mengisi notes jika penolakan"
    }
    
    # Evaluation messages
    EVALUATION = {
        "not_found": "Evaluasi tidak ditemukan",
        "already_evaluated": "Sudah pernah melakukan evaluasi untuk periode ini",
        "evaluation_period_ended": "Periode evaluasi telah berakhir",
        "invalid_score": "Nilai evaluasi tidak valid",
    }
    
    # Validation messages
    VALIDATION = {
        "required_field": "Field {field} wajib diisi",
        "invalid_email": "Format email tidak valid",
        "password_too_short": "Kata sandi minimal 8 karakter",
        "invalid_date_format": "Format tanggal tidak valid",
        "date_range_invalid": "Rentang tanggal tidak valid",
    }

def get_message(category: str, key: str, **kwargs) -> str:
    """Get a message from the specified category and format it with kwargs."""
    category_messages = getattr(Messages, category.upper(), {})
    message = category_messages.get(key, f"Message not found: {category}.{key}")
    return message.format(**kwargs) if kwargs else message