# Database Delete Cascade Mitigation Plan
## PKG (Penilaian Kinerja Guru) System

### Executive Summary

Analisis terhadap sistem PKG menunjukkan **belum ada implementasi delete cascade yang proper** pada foreign key relationships. Hal ini menyebabkan masalah operasional ketika:

1. **Organizations dihapus** → Tidak bisa dihapus jika memiliki users (guru/kepala sekolah)
2. **Users dihapus** → Tidak bisa dihapus jika memiliki data RPP submissions atau teacher evaluations
3. **Data integrity issues** → Kesulitan dalam manajemen data dan arsip

### Analisis Masalah Saat Ini

#### 1. Skenario: Organization Dihapus
**Status Saat Ini: ❌ BLOCKED**

Ketika organization dihapus yang memiliki:
- **Guru-guru**: `User.organization_id` → `Organization.id` (RESTRICT)
- **Kepala Sekolah**: `Organization.head_id` → `User.id` (RESTRICT)
- **Media Files**: `MediaFile.organization_id` → `Organization.id` (RESTRICT)
- **User Roles**: `UserRole.organization_id` → `Organization.id` (RESTRICT)

**Akibat:**
```sql
-- Error yang akan muncul:
ERROR: update or delete on table "organizations" violates foreign key constraint
DETAIL: Key (id)=(1) is still referenced from table "users"
```

**Data yang Terpengaruh:**
- ✅ **RPP Submissions** tetap ada (melalui teacher_id)
- ✅ **Teacher Evaluations** tetap ada (melalui teacher_id)
- ❌ **Users menjadi orphaned** jika paksa dihapus
- ❌ **Media Files menjadi orphaned**

#### 2. Skenario: User (Guru/Kepala Sekolah) Dihapus
**Status Saat Ini: ❌ BLOCKED**

Ketika user dihapus yang memiliki:
- **RPP Submissions sebagai teacher**: `RPPSubmission.teacher_id` → `User.id` (RESTRICT)
- **RPP Submissions sebagai reviewer**: `RPPSubmission.reviewer_id` → `User.id` (RESTRICT)
- **Teacher Evaluations sebagai teacher**: `TeacherEvaluation.teacher_id` → `User.id` (RESTRICT)
- **Teacher Evaluations sebagai evaluator**: `TeacherEvaluation.evaluator_id` → `User.id` (RESTRICT)
- **User Roles**: `UserRole.user_id` → `User.id` (RESTRICT)
- **Media Files**: `MediaFile.uploader_id` → `User.id` (RESTRICT)
- **Organization Head**: `Organization.head_id` → `User.id` (RESTRICT)

**Akibat:**
```sql
-- Error yang akan muncul:
ERROR: update or delete on table "users" violates foreign key constraint
DETAIL: Key (id)=(5) is still referenced from table "rpp_submissions"
```

**Data yang Hilang Jika Dipaksa:**
- ❌ **Histori evaluasi kinerja guru**
- ❌ **Histori pengajuan RPP**
- ❌ **Konteks organisasi dan kepemimpinan**

### Rekomendasi Strategi Cascade

#### 1. Organizations → Users
```sql
-- RECOMMENDED: SET NULL
ALTER TABLE users 
DROP CONSTRAINT IF EXISTS users_organization_id_fkey,
ADD CONSTRAINT users_organization_id_fkey 
    FOREIGN KEY (organization_id) 
    REFERENCES organizations(id) 
    ON DELETE SET NULL;
```

**Alasan:** Users dapat exist tanpa organization (untuk maintenance/transition)

#### 2. Organizations → Organization Head
```sql
-- RECOMMENDED: SET NULL
ALTER TABLE organizations 
DROP CONSTRAINT IF EXISTS organizations_head_id_fkey,
ADD CONSTRAINT organizations_head_id_fkey 
    FOREIGN KEY (head_id) 
    REFERENCES users(id) 
    ON DELETE SET NULL;
```

**Alasan:** Organization dapat temporarily tidak memiliki head

#### 3. Users → RPP Submissions
```sql
-- Teacher: RESTRICT (preserve history)
ALTER TABLE rpp_submissions 
DROP CONSTRAINT IF EXISTS rpp_submissions_teacher_id_fkey,
ADD CONSTRAINT rpp_submissions_teacher_id_fkey 
    FOREIGN KEY (teacher_id) 
    REFERENCES users(id) 
    ON DELETE RESTRICT;

-- Reviewer: SET NULL (can continue without reviewer)
ALTER TABLE rpp_submissions 
DROP CONSTRAINT IF EXISTS rpp_submissions_reviewer_id_fkey,
ADD CONSTRAINT rpp_submissions_reviewer_id_fkey 
    FOREIGN KEY (reviewer_id) 
    REFERENCES users(id) 
    ON DELETE SET NULL;
```

**Alasan:** Preserve educational records, but allow reviewer changes

#### 4. Users → Teacher Evaluations
```sql
-- Both: RESTRICT (preserve evaluation history)
ALTER TABLE teacher_evaluations 
DROP CONSTRAINT IF EXISTS teacher_evaluations_teacher_id_fkey,
ADD CONSTRAINT teacher_evaluations_teacher_id_fkey 
    FOREIGN KEY (teacher_id) 
    REFERENCES users(id) 
    ON DELETE RESTRICT;

ALTER TABLE teacher_evaluations 
DROP CONSTRAINT IF EXISTS teacher_evaluations_evaluator_id_fkey,
ADD CONSTRAINT teacher_evaluations_evaluator_id_fkey 
    FOREIGN KEY (evaluator_id) 
    REFERENCES users(id) 
    ON DELETE RESTRICT;
```

**Alasan:** Evaluation history adalah data kritikal untuk audit

#### 5. Users → User Roles
```sql
-- CASCADE (roles meaningless without user)
ALTER TABLE user_roles 
DROP CONSTRAINT IF EXISTS user_roles_user_id_fkey,
ADD CONSTRAINT user_roles_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES users(id) 
    ON DELETE CASCADE;
```

**Alasan:** User roles tidak berguna tanpa user

#### 6. Media Files Relationships
```sql
-- Uploader: SET NULL (preserve file, lose uploader reference)
ALTER TABLE media_files 
DROP CONSTRAINT IF EXISTS media_files_uploader_id_fkey,
ADD CONSTRAINT media_files_uploader_id_fkey 
    FOREIGN KEY (uploader_id) 
    REFERENCES users(id) 
    ON DELETE SET NULL;

-- Organization: SET NULL (preserve file, lose org reference)
ALTER TABLE media_files 
DROP CONSTRAINT IF EXISTS media_files_organization_id_fkey,
ADD CONSTRAINT media_files_organization_id_fkey 
    FOREIGN KEY (organization_id) 
    REFERENCES organizations(id) 
    ON DELETE SET NULL;

-- RPP File: RESTRICT (preserve RPP integrity)
ALTER TABLE rpp_submissions 
DROP CONSTRAINT IF EXISTS rpp_submissions_file_id_fkey,
ADD CONSTRAINT rpp_submissions_file_id_fkey 
    FOREIGN KEY (file_id) 
    REFERENCES media_files(id) 
    ON DELETE RESTRICT;
```

### Implementation Plan

#### Phase 1: Critical Relationships (High Priority)
1. **User Roles CASCADE**
   - Low risk, high impact
   - Immediate operational improvement

2. **Organization Head SET NULL**
   - Allows organization management flexibility
   - Minimal data impact

3. **User Organization SET NULL**
   - Enables user transfers between organizations
   - Maintains user history

#### Phase 2: Media Files (Medium Priority)
4. **Media File Uploader/Organization SET NULL**
   - Preserves files while allowing user/org cleanup
   - Maintains RPP submission integrity

5. **RPP Reviewer SET NULL**
   - Allows reviewer changes
   - Maintains submission workflow

#### Phase 3: Business Decision Required (Careful Consideration)
6. **Evaluation and RPP Teacher Relationships**
   - **Option A**: Keep RESTRICT (preserve all history)
   - **Option B**: Add soft delete mechanism
   - **Option C**: Archive before delete process

### Migration Script Template

```sql
-- Phase 1: Critical Relationships
BEGIN;

-- 1. User Roles CASCADE
ALTER TABLE user_roles 
DROP CONSTRAINT IF EXISTS user_roles_user_id_fkey,
ADD CONSTRAINT user_roles_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES users(id) 
    ON DELETE CASCADE;

-- 2. Organization Head SET NULL
ALTER TABLE organizations 
DROP CONSTRAINT IF EXISTS organizations_head_id_fkey,
ADD CONSTRAINT organizations_head_id_fkey 
    FOREIGN KEY (head_id) 
    REFERENCES users(id) 
    ON DELETE SET NULL;

-- 3. User Organization SET NULL
ALTER TABLE users 
DROP CONSTRAINT IF EXISTS users_organization_id_fkey,
ADD CONSTRAINT users_organization_id_fkey 
    FOREIGN KEY (organization_id) 
    REFERENCES organizations(id) 
    ON DELETE SET NULL;

COMMIT;
```

### Skenario Setelah Implementasi

#### Skenario 1: Organization Dihapus (Setelah Mitigasi)
✅ **BERHASIL** dengan langkah berikut:

1. **Organization.head_id → SET NULL**
   - Organization head reference dihapus
   - Organization masih bisa dihapus

2. **Users.organization_id → SET NULL**
   - Semua users dalam organization menjadi `organization_id = NULL`
   - Users tetap exist dengan history RPP dan evaluasi utuh

3. **UserRoles.organization_id → CASCADE** (tambahan)
   - Role yang terkait organization otomatis terhapus
   - Users dapat diberi role baru di organization lain

4. **MediaFiles.organization_id → SET NULL**
   - Files tetap exist, hanya kehilangan organization reference

**Result:** Organization berhasil dihapus, data historis preserved

#### Skenario 2: User Dihapus (Setelah Mitigasi)
⚠️ **TERKONTROL** dengan validation:

**Users dengan RPP/Evaluation History:**
- ❌ **RESTRICT** - Tidak bisa dihapus langsung
- ✅ **Soft Delete** - Tandai sebagai inactive/deleted
- ✅ **Transfer Process** - Pindahkan ke organization lain dulu

**Users tanpa History:**
- ✅ **UserRoles CASCADE** - Roles otomatis terhapus
- ✅ **Organization head SET NULL** - Jika adalah head, organization head → NULL
- ✅ **MediaFiles uploader SET NULL** - Files preserved, uploader reference hilang

### Alternative: Soft Delete Strategy

Untuk users dengan history, implementasikan soft delete:

```python
# Add to User model
class User(SQLModel, table=True):
    # ... existing fields
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[int] = Field(default=None, foreign_key="users.id")

# Service layer
async def soft_delete_user(user_id: int, deleted_by: int):
    user = await get_user(user_id)
    
    # Check if user has critical history
    has_rpp = await check_user_rpp_submissions(user_id)
    has_evaluations = await check_user_evaluations(user_id)
    
    if has_rpp or has_evaluations:
        # Soft delete
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        user.deleted_by = deleted_by
        user.status = UserStatus.INACTIVE
        await session.commit()
    else:
        # Hard delete (with cascades)
        await session.delete(user)
        await session.commit()
```


### Kesimpulan

1. **Sistem saat ini BELUM AMAN** untuk delete operations
2. **Implementasi cascade yang tepat** diperlukan untuk operasional yang lancar
3. **Data preservation tetap menjadi prioritas** untuk audit trail
4. **Soft delete strategy** direkomendasikan untuk users dengan history


**Prioritas:** High - Implementasi segera direkomendasikan untuk menghindari operational issues.