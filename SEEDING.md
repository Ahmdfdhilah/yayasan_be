# Database Seeding Guide

Script ini akan membuat data awal untuk sistem Tafatur PKG termasuk organisasi, user, dan role assignments.

## Yang Akan Dibuat

### 🏢 Organisasi
1. **SMA Negeri 1 Jakarta** (SCHOOL)
   - Email: info@sman1jakarta.sch.id
   - Phone: 021-12345678

2. **SMP Negeri 5 Bandung** (SCHOOL)
   - Email: info@smpn5bandung.sch.id
   - Phone: 022-87654321

3. **Yayasan Pendidikan Nusantara** (FOUNDATION)
   - Email: info@nusantara.org
   - Phone: 021-98765432

### 👥 User Accounts

#### Super Admin
- **Email**: `superadmin@tafatur.id`
- **Password**: `@SuperAdmin123`
- **Role**: super_admin
- **Access**: Full system access

#### System Admin
- **Email**: `admin@tafatur.id`
- **Password**: `@Admin123`
- **Role**: admin
- **Access**: Administrative functions

#### Kepala Sekolah SMAN 1
- **Email**: `kepsek@sman1jakarta.sch.id`
- **Password**: `@KepSek123`
- **Role**: kepala_sekolah
- **Name**: Dr. Ahmad Susanto, M.Pd
- **Organization**: SMA Negeri 1 Jakarta

#### Guru SMAN 1
- **Email**: `guru1@sman1jakarta.sch.id`
- **Password**: `@Guru123`
- **Role**: guru
- **Name**: Siti Rahayu, S.Pd
- **Subject**: Matematika
- **Organization**: SMA Negeri 1 Jakarta

- **Email**: `guru2@sman1jakarta.sch.id`
- **Password**: `@Guru123`
- **Role**: guru
- **Name**: Budi Santoso, S.Pd
- **Subject**: Bahasa Indonesia
- **Organization**: SMA Negeri 1 Jakarta

#### Kepala Sekolah SMPN 5
- **Email**: `kepsek@smpn5bandung.sch.id`
- **Password**: `@KepSek123`
- **Role**: kepala_sekolah
- **Name**: Dra. Sri Mulyani, M.M
- **Organization**: SMP Negeri 5 Bandung

#### Guru SMPN 5
- **Email**: `guru1@smpn5bandung.sch.id`
- **Password**: `@Guru123`
- **Role**: guru
- **Name**: Andi Wijaya, S.Pd
- **Subject**: IPA Terpadu
- **Organization**: SMP Negeri 5 Bandung

#### Content Manager
- **Email**: `content@nusantara.org`
- **Password**: `@Content123`
- **Role**: content_manager
- **Name**: Maya Sari, S.Kom
- **Organization**: Yayasan Pendidikan Nusantara

## Cara Menjalankan

### Prerequisites
1. Database sudah running (PostgreSQL/MySQL)
2. Environment variables sudah di-set
3. Database tables sudah dibuat (via alembic)

### Command
```bash
# Create organizations and seeding data
python seed.py up

# Clear all data
python seed.py down

# Create users manually (workaround for async issues)
python scripts/create_manual_users.py

# Direct script with arguments
python scripts/seed_users.py up
python scripts/seed_users.py down
```

## Role Permissions

### Super Admin
- Full access ke semua fitur sistem
- Manage users, organizations, roles
- System administration

### Admin
- User management (create, read, update)
- Organization management (read, update)
- Role management
- Analytics access

### Kepala Sekolah
- Evaluation management
- RPP review dan approval
- School analytics
- Teacher performance monitoring

### Guru
- RPP submission
- View own evaluations
- Profile management

### Content Manager
- Content creation dan management
- Media upload dan management
- CMS functions

## Troubleshooting

### Error: Import tidak ditemukan
```bash
# Pastikan PYTHONPATH benar
export PYTHONPATH="${PYTHONPATH}:/path/to/tafatur/backend"
```

### Error: Database connection
- Cek environment variables `DATABASE_URL`
- Pastikan database service running
- Verify credentials di `.env`

### Error: Tables not found
```bash
# Run alembic migration dulu
alembic upgrade head
```

### Error: Duplicate entries
Script sudah handle duplicate checking, tapi kalau ada error:
- Truncate tables dan run ulang
- Atau hapus user/org specific yang conflict

## Verifikasi

Setelah seeding berhasil, cek:
1. Login dengan credentials di atas
2. Verify role permissions
3. Check organization assignments
4. Test basic functionality per role

## File Structure
```
backend/
├── scripts/
│   └── seed_users.py          # Main seeding script
├── seed.py                    # Simple runner
└── SEEDING.md                 # Documentation ini
```

## Next Steps

Setelah seeding, Anda bisa:
1. Test login dengan berbagai role
2. Membuat evaluation aspects
3. Upload sample RPP files  
4. Test PKG evaluation workflow
5. Customize permissions sesuai kebutuhan