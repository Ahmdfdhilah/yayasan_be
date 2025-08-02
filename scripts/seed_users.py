"""Seeding script untuk membuat akun per role sesuai models."""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.core.database import get_db
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.user_role import UserRoleRepository
from src.services.user import UserService
from src.services.organization import OrganizationService
from src.services.user_role import UserRoleService
from src.schemas.user import UserCreate
from src.schemas.organization import OrganizationCreate, OrganizationUpdate
from src.schemas.user_role import UserRoleCreate
from src.models.enums import UserStatus, UserRole as UserRoleEnum
from src.models.article import Article
from src.models.gallery import Gallery
from src.models.message import Message, MessageStatus
from src.models.period import Period
from src.models.board_member import BoardMember
from src.models.board_group import BoardGroup
import hashlib
import random
from faker import Faker


class UserSeeder:
    """User seeding class for creating test accounts."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.org_repo = OrganizationRepository(session)
        self.role_repo = UserRoleRepository(session)
        self.user_service = UserService(self.user_repo)
        self.org_service = OrganizationService(self.org_repo)
        self.role_service = UserRoleService(self.role_repo, self.user_repo, self.org_repo)
        self.fake = Faker('id_ID')  # Indonesian faker
    
    async def create_organizations(self):
        """Create sample organizations."""
        print("Creating organizations...")
        
        organizations = [
            {
                "name": "SD Al-Hikmah Tafatur",
                "description": "<h2>Sekolah Dasar Al-Hikmah Tafatur</h2><p>Sekolah dasar yang berfokus pada pembentukan karakter islami dan prestasi akademik unggul. Kami mengintegrasikan kurikulum nasional dengan nilai-nilai keislaman untuk menciptakan generasi yang berakhlak mulia dan berprestasi.</p><h3>Visi Kami:</h3><p>Menjadi sekolah dasar terdepan dalam menghasilkan lulusan yang beriman, bertaqwa, berakhlak mulia, dan berprestasi akademik tinggi.</p><h3>Misi Kami:</h3><ul><li>Menyelenggarakan pendidikan berkualitas dengan pendekatan holistik</li><li>Mengembangkan potensi siswa secara optimal melalui pembelajaran inovatif</li><li>Menanamkan nilai-nilai islami dalam setiap aspek kehidupan</li><li>Membangun kemitraan yang kuat dengan orang tua dan masyarakat</li></ul>",
                "head_id": None
            },
            {
                "name": "SMP Al-Hikmah Tafatur",
                "description": "<h2>Sekolah Menengah Pertama Al-Hikmah Tafatur</h2><p>Sekolah menengah pertama yang mengembangkan potensi siswa melalui pendidikan berkualitas dengan landasan nilai-nilai islami. Kami mempersiapkan siswa untuk menghadapi tantangan pendidikan tingkat selanjutnya dengan bekal akademik dan spiritual yang kuat.</p><h3>Keunggulan Kami:</h3><ul><li>Program bilingual (Bahasa Indonesia dan Bahasa Inggris)</li><li>Laboratorium sains dan komputer yang lengkap</li><li>Ekstrakurikuler yang beragam dan berprestasi</li><li>Pembinaan karakter islami terintegrasi</li></ul><h3>Fasilitas:</h3><p>Gedung bertingkat dengan ruang kelas ber-AC, laboratorium IPA, laboratorium komputer, perpustakaan digital, masjid, lapangan olahraga, dan kantin sehat.</p>",
                "head_id": None
            },
            {
                "name": "SMA Al-Hikmah Tafatur",
                "description": "<h2>Sekolah Menengah Atas Al-Hikmah Tafatur</h2><p>Sekolah menengah atas unggulan yang mempersiapkan siswa untuk memasuki perguruan tinggi terbaik dengan bekal akademik, spiritual, dan kepemimpinan yang mumpuni. Kami menawarkan program IPA, IPS, dan Bahasa dengan standar internasional.</p><h3>Program Unggulan:</h3><ul><li>Kelas Akselerasi untuk siswa berprestasi</li><li>Program Tahfidz Al-Quran</li><li>Olimpiade Sains Nasional (OSN)</li><li>Program pertukaran pelajar internasional</li><li>Bimbingan SBMPTN dan ujian masuk PTN</li></ul><h3>Prestasi:</h3><p>Juara 1 Olimpiade Matematika Tingkat Provinsi 2023, Juara 2 Kompetisi Sains Nasional 2023, 95% lulusan diterima di PTN favorit.</p><h3>Alumni Terbaik:</h3><p>Banyak alumni yang berhasil meraih beasiswa di universitas dalam dan luar negeri, serta menjadi pemimpin di berbagai bidang.</p>",
                "head_id": None
            }
        ]
        
        created_orgs = {}
        for i, org_data in enumerate(organizations):
            try:
                # Check if organization already exists by name
                existing = await self.org_repo.get_by_name(org_data["name"])
                if existing:
                    print(f"Organization {org_data['name']} already exists")
                    created_orgs[i] = existing
                    continue
                
                org_create = OrganizationCreate(**org_data)
                organization = await self.org_service.create_organization(org_create)
                created_orgs[i] = organization
                print(f"Created organization: {organization.name}")
            except Exception as e:
                print(f"Error creating organization {org_data['name']}: {e}")
        
        return created_orgs
    
    async def create_users_by_role(self, organizations):
        """Create users for each role."""
        print("Creating users by role...")
        
        users_data = []
        
        # System Admin
        users_data.append({
            "email": "admin@tafatur.id",
            "password": "@Password123",
            "profile": {
                "name": "System Administrator",
                "phone": "081234567891",
                "address": "Jakarta, Indonesia",
                "position": "System Administrator"
            },
            "organization_id": None,
            "status": UserStatus.ACTIVE,
            "roles": ["admin"]
        })
        
        # School data for generating realistic names
        school_data = [
            {"type": "SD", "location": "Jakarta", "domain": "sd-alhikmah"},
            {"type": "SMP", "location": "Jakarta", "domain": "smp-alhikmah"},
            {"type": "SMA", "location": "Jakarta", "domain": "sma-alhikmah"}
        ]
        
        # Teacher names pool
        teacher_names = [
            "Ahmad Santoso, S.Pd", "Siti Rahayu, S.Pd", "Budi Prasetyo, S.Pd", "Dewi Kusuma, S.Pd",
            "Andi Wijaya, S.Pd", "Maya Sari, S.Pd", "Rudi Hartono, S.Pd", "Linda Puspita, S.Pd",
            "Hendra Gunawan, S.Pd", "Fitri Rahmawati, S.Pd", "Bambang Sutrisno, S.Pd", "Novi Anggraini, S.Pd",
            "Eko Wahyudi, S.Pd", "Wulan Sari, S.Pd", "Toni Setiawan, S.Pd", "Dina Marlina, S.Pd",
            "Riko Pratama, S.Ag", "Indra Wijaya, S.Pd", "Rina Handayani, S.Pd", "Agus Prasetyo, S.Si"
        ]
        
        # Principal names
        principal_names = [
            "Dr. Ahmad Taufiq, M.Pd.I",
            "Dra. Siti Khadijah, M.Pd", 
            "Prof. Dr. Abdullah Rahman, M.A"
        ]
        
        phone_counter = 892
        nip_counter = 1001
        
        # Generate users for 3 organizations
        for org_idx, org in organizations.items():
            school_info = school_data[org_idx]
            
            # Generate Kepala Sekolah
            users_data.append({
                "email": f"kepsek@{school_info['domain']}.sch.id",
                "password": "@Password123",
                "profile": {
                    "name": principal_names[org_idx],
                    "phone": f"08123456{phone_counter}",
                    "address": school_info['location'],
                    "position": "Kepala Sekolah",
                    "nip": f"19700101199003{nip_counter}"
                },
                "organization_id": org.id,
                "status": UserStatus.ACTIVE,
                "roles": ["kepala_sekolah"],
                "is_head": True
            })
            phone_counter += 1
            nip_counter += 1
            
            # Generate 10 teachers per school
            for i in range(10):
                teacher_name = teacher_names[(org_idx * 10 + i) % len(teacher_names)]
                if teacher_name in teacher_names[(org_idx * 10):((org_idx + 1) * 10)]:
                    teacher_name = f"{teacher_name.split(',')[0]} {chr(65 + i)}, S.Pd"
                
                # Different subjects based on school type
                if school_info['type'] == 'SMA':
                    subjects = ['Matematika', 'Bahasa Indonesia', 'Bahasa Inggris', 'Fisika', 'Kimia', 
                              'Biologi', 'Sejarah', 'Geografi', 'Ekonomi', 'Sosiologi']
                    classes = ['X IPA 1', 'X IPA 2', 'XI IPA 1', 'XI IPA 2', 'XII IPA 1', 
                              'X IPS 1', 'XI IPS 1', 'XII IPS 1', 'XI IPS 2', 'XII IPS 2']
                elif school_info['type'] == 'SMP':
                    subjects = ['Matematika', 'Bahasa Indonesia', 'Bahasa Inggris', 'IPA Terpadu', 'IPS Terpadu',
                              'PKN', 'Seni Budaya', 'Pendidikan Jasmani', 'Prakarya', 'Agama Islam']
                    classes = ['VII A', 'VII B', 'VIII A', 'VIII B', 'VIII C', 'IX A', 'IX B', 'IX C', 'VII C', 'VIII D']
                else:  # SD
                    subjects = ['Guru Kelas', 'Guru Kelas', 'Guru Kelas', 'Guru Kelas', 'Guru Kelas',
                              'Guru Kelas', 'Pendidikan Jasmani', 'Agama Islam', 'Bahasa Inggris', 'Seni Budaya']
                    classes = ['I-A', 'II-A', 'III-A', 'IV-A', 'V-A', 'VI-A', 'Semua Kelas', 'Semua Kelas', 'Semua Kelas', 'Semua Kelas']
                
                users_data.append({
                    "email": f"guru{i+1}@{school_info['domain']}.sch.id",
                    "password": "@Password123",
                    "profile": {
                        "name": teacher_name,
                        "phone": f"08123456{phone_counter}",
                        "address": school_info['location'],
                        "position": f"Guru {subjects[i]}",
                        "nip": f"19850515201001{nip_counter}",
                        "subject": subjects[i],
                        "class": classes[i]
                    },
                    "organization_id": org.id,
                    "status": UserStatus.ACTIVE,
                    "roles": ["guru"]
                })
                phone_counter += 1
                nip_counter += 1
        
        created_users = []
        for user_data in users_data:
            try:
                # Check if user already exists
                existing = await self.user_repo.get_by_email(user_data["email"])
                if existing:
                    print(f"User {user_data['email']} already exists")
                    created_users.append(existing)
                    continue
                
                # Create user
                user_create = UserCreate(
                    email=user_data["email"],
                    password=user_data["password"],
                    profile=user_data["profile"],
                    organization_id=user_data["organization_id"],
                    status=user_data["status"]
                )
                
                user = await self.user_service.create_user(user_create, user_data["organization_id"])
                created_users.append(user)
                print(f"Created user: {user.email} - {user.profile.get('name')}")
                
                # Assign roles
                for role_name in user_data["roles"]:
                    try:
                        role_create = UserRoleCreate(
                            user_id=user.id,
                            role_name=role_name,
                            organization_id=user_data["organization_id"],
                            is_active=True
                        )
                        
                        role = await self.role_service.create_user_role(role_create)
                        print(f"  -> Assigned role: {role_name}")
                    except Exception as e:
                        print(f"  -> Error assigning role {role_name}: {e}")
                
            except Exception as e:
                print(f"Error creating user {user_data['email']}: {e}")
        
        # After creating users, assign heads to organizations
        await self.assign_heads_to_organizations(created_users, organizations)
        
        return created_users
    
    async def assign_heads_to_organizations(self, users, organizations):
        """Assign heads to organizations after users are created."""
        print("Assigning heads to organizations...")
        
        # Find head users and assign them to organizations
        head_assignments = []
        for user in users:
            if hasattr(user, 'email') and user.email.startswith('kepsek@'):
                # Find the corresponding organization
                for org_idx, org in organizations.items():
                    if user.organization_id == org.id:
                        head_assignments.append((org, user.id))
                        break
        
        # Update organizations with head_id
        for org, head_id in head_assignments:
            if org and head_id:
                try:
                    update_data = OrganizationUpdate(head_id=head_id)
                    await self.org_repo.update(org.id, update_data)
                    print(f"  -> Assigned head {head_id} to organization {org.name}")
                except Exception as e:
                    print(f"  -> Error assigning head to {org.name}: {e}")
    
    async def create_sample_permissions(self):
        """Create sample permission templates for roles."""
        print("Setting up role permissions...")
        
        role_permissions = {
            "admin": {
                "users.create": True,
                "users.read": True,
                "users.update": True,
                "users.delete": False,
                "organizations.read": True,
                "organizations.update": True,
                "roles.create": True,
                "roles.read": True,
                "roles.update": True,
                "evaluations.read": True,
                "evaluations.update": True,
                "rpps.read": True,
                "rpps.update": True,
                "analytics.read": True
            },
            "kepala_sekolah": {
                "users.read": True,
                "users.update": False,
                "evaluations.create": True,
                "evaluations.read": True,
                "evaluations.update": True,
                "rpps.read": True,
                "rpps.review": True,
                "analytics.read": True,
                "school.manage": True
            },
            "guru": {
                "users.read": False,
                "evaluations.read": True,
                "rpps.create": True,
                "rpps.read": True,
                "rpps.update": True,
                "profile.update": True
            },
        }
        
        # Update role permissions
        for role_name, permissions in role_permissions.items():
            try:
                # Get all user roles with this role name
                user_roles = await self.role_repo.get_users_with_role(role_name, active_only=True)
                
                for user_role in user_roles:
                    await self.role_repo.update_permissions(user_role.id, permissions)
                    print(f"Updated permissions for role: {role_name}")
                    
            except Exception as e:
                print(f"Error updating permissions for {role_name}: {e}")
    
    async def create_periods(self):
        """Create 16 academic periods from 2022 to 2029."""
        print("Creating 16 academic periods...")
        
        from datetime import date
        
        periods_data = []
        
        # Generate periods from 2022 to 2029 (16 periods total)
        for year in range(2022, 2030):
            # Semester Ganjil (Odd) - July to December
            periods_data.append({
                "academic_year": f"{year}/{year+1}",
                "semester": "Ganjil",
                "start_date": date(year, 7, 15),
                "end_date": date(year, 12, 31),
                "is_active": year == 2024,  # Make 2024 active
                "description": f"Semester Ganjil Tahun Akademik {year}/{year+1}"
            })
            
            # Semester Genap (Even) - January to June  
            periods_data.append({
                "academic_year": f"{year}/{year+1}",
                "semester": "Genap", 
                "start_date": date(year+1, 1, 1),
                "end_date": date(year+1, 6, 30),
                "is_active": False,
                "description": f"Semester Genap Tahun Akademik {year}/{year+1}"
            })
            
            # Stop at 16 periods
            if len(periods_data) >= 16:
                break
        
        created_periods = []
        for period_data in periods_data:
            try:
                # Check if period already exists
                existing = await self.session.execute(
                    text("SELECT * FROM periods WHERE academic_year = :year AND semester = :semester"),
                    {"year": period_data["academic_year"], "semester": period_data["semester"]}
                )
                if existing.fetchone():
                    print(f"Period {period_data['academic_year']} {period_data['semester']} already exists")
                    continue
                
                period = Period(**period_data)
                self.session.add(period)
                await self.session.flush()
                created_periods.append(period)
                print(f"Created period: {period.academic_year} - {period.semester}")
                
            except Exception as e:
                print(f"Error creating period {period_data['academic_year']} {period_data['semester']}: {e}")
        
        await self.session.commit()
        return created_periods
    
    def generate_articles_data(self, count=10):
        """Generate article data using faker."""
        articles_data = [
            {
                "title": "Pengumuman Pendaftaran Siswa Baru Tahun Ajaran 2024/2025",
                "description": "<h2>Pendaftaran Siswa Baru T.A 2024/2025</h2><p>Yayasan Al-Hikmah Tafatur membuka pendaftaran siswa baru untuk tahun ajaran 2024/2025. Pendaftaran dibuka untuk semua jenjang mulai dari SD, SMP, hingga SMA.</p><h3>Persyaratan Umum:</h3><ul><li>Mengisi formulir pendaftaran online</li><li>Melampirkan foto copy ijazah dan SKHUN</li><li>Pas foto 3x4 sebanyak 4 lembar</li><li>Surat keterangan sehat dari dokter</li></ul><h3>Jadwal Pendaftaran:</h3><p><strong>Gelombang 1:</strong> 1 Januari - 28 Februari 2024<br><strong>Gelombang 2:</strong> 1 Maret - 30 April 2024</p><p>Untuk informasi lebih lanjut, silakan hubungi bagian admisi di setiap unit sekolah.</p>",
                "slug": "pengumuman-pendaftaran-siswa-baru-2024-2025",
                "excerpt": "Yayasan Al-Hikmah Tafatur membuka pendaftaran siswa baru untuk tahun ajaran 2024/2025 dengan berbagai program unggulan.",
                "img_url": "https://via.placeholder.com/800x400/4f46e5/ffffff?text=Pendaftaran+Siswa+Baru",
                "category": "Pengumuman",
                "is_published": True,
                "published_at": datetime(2024, 1, 15, 10, 0, 0)
            },
            {
                "title": "Prestasi Membanggakan: Juara 1 Olimpiade Sains Nasional",
                "description": "<h2>Prestasi Gemilang di Olimpiade Sains Nasional 2024</h2><p>Siswa SMA Al-Hikmah Tafatur berhasil meraih juara 1 pada Olimpiade Sains Nasional (OSN) bidang Matematika tingkat nasional. Ahmad Fadhil dari kelas XII IPA berhasil mengalahkan ratusan peserta dari seluruh Indonesia.</p><h3>Perjalanan Menuju Juara:</h3><p>Persiapan yang matang selama 8 bulan dengan bimbingan intensif dari guru pembina dan alumni yang berprestasi. Latihan soal dilakukan secara konsisten dengan materi yang mencakup tingkat nasional dan internasional.</p><blockquote><p>\"Ini adalah hasil kerja keras bersama. Dukungan sekolah, guru, dan keluarga sangat berarti dalam pencapaian ini.\" - Ahmad Fadhil</p></blockquote><p>Prestasi ini menambah deretan penghargaan yang telah diraih sekolah dan membuktikan kualitas pendidikan yang diberikan.</p>",
                "slug": "prestasi-juara-1-olimpiade-sains-nasional",
                "excerpt": "Siswa SMA Al-Hikmah Tafatur meraih juara 1 Olimpiade Sains Nasional bidang Matematika tingkat nasional.",
                "img_url": "https://via.placeholder.com/800x400/059669/ffffff?text=Juara+OSN+2024",
                "category": "Berita",
                "is_published": True,
                "published_at": datetime(2024, 3, 20, 14, 30, 0)
            },
            {
                "title": "Program Tahfidz Al-Quran: Mencetak Generasi Qur'ani",
                "description": "<h2>Program Tahfidz Al-Quran</h2><p>Program Tahfidz Al-Quran merupakan salah satu program unggulan di semua jenjang pendidikan Yayasan Al-Hikmah Tafatur. Program ini bertujuan untuk mencetak generasi yang hafal Al-Quran dengan pemahaman yang mendalam.</p><h3>Target Hafalan per Jenjang:</h3><ul><li><strong>SD:</strong> Juz 30 dan sebagian Juz 29</li><li><strong>SMP:</strong> 5 Juz (Juz 26-30)</li><li><strong>SMA:</strong> 10 Juz atau lebih</li></ul><h3>Metode Pembelajaran:</h3><p>Kami menggunakan metode <em>talaqqi</em> langsung dengan ustadz/ustadzah yang berpengalaman. Setiap siswa mendapat bimbingan personal untuk memastikan kualitas hafalan yang baik.</p><h3>Prestasi Program:</h3><p>Hingga tahun 2024, lebih dari 200 siswa telah menyelesaikan target hafalan dengan nilai excellent. Beberapa di antaranya bahkan berhasil menghafal 30 juz lengkap.</p>",
                "slug": "program-tahfidz-alquran-generasi-qurani",
                "excerpt": "Program Tahfidz Al-Quran sebagai program unggulan untuk mencetak generasi yang hafal Al-Quran dengan pemahaman mendalam.",
                "img_url": "https://via.placeholder.com/800x400/7c3aed/ffffff?text=Program+Tahfidz",
                "category": "Program",
                "is_published": True,
                "published_at": datetime(2024, 2, 10, 9, 15, 0)
            },
            {
                "title": "Workshop Peningkatan Kompetensi Guru: Teknologi dalam Pembelajaran",
                "description": "<h2>Workshop Teknologi dalam Pembelajaran</h2><p>Yayasan Al-Hikmah Tafatur mengadakan workshop peningkatan kompetensi guru dengan tema \"Integrasi Teknologi dalam Pembelajaran Modern\". Workshop ini diikuti oleh seluruh guru dari ketiga jenjang pendidikan.</p><h3>Materi Workshop:</h3><ul><li>Penggunaan platform pembelajaran digital</li><li>Pembuatan konten multimedia interaktif</li><li>Assessment online dan analisis hasil belajar</li><li>Gamifikasi dalam pembelajaran</li></ul><h3>Narasumber:</h3><p>Workshop dipimpin oleh Dr. Budi Santoso, M.Kom dari Institut Teknologi Bandung dan Dra. Siti Aminah, M.Pd dari Universitas Pendidikan Indonesia.</p><p>Diharapkan dengan workshop ini, guru-guru dapat lebih optimal dalam menggunakan teknologi untuk meningkatkan kualitas pembelajaran dan engagement siswa.</p>",
                "slug": "workshop-teknologi-pembelajaran-guru",
                "excerpt": "Workshop peningkatan kompetensi guru dalam mengintegrasikan teknologi untuk pembelajaran yang lebih efektif dan modern.",
                "img_url": "https://via.placeholder.com/800x400/ea580c/ffffff?text=Workshop+Guru",
                "category": "Event",
                "is_published": True,
                "published_at": datetime(2024, 4, 5, 8, 0, 0)
            },
            {
                "title": "Panduan Orang Tua: Mendampingi Belajar Anak di Rumah",
                "description": "<h2>Panduan Orang Tua dalam Mendampingi Belajar Anak</h2><p>Peran orang tua sangat penting dalam mendukung proses pembelajaran anak. Berikut adalah panduan praktis untuk orang tua dalam mendampingi belajar anak di rumah.</p><h3>Tips Efektif:</h3><ol><li><strong>Ciptakan Lingkungan Belajar yang Nyaman</strong><br>Siapkan ruang khusus untuk belajar dengan pencahayaan yang cukup dan minim gangguan.</li><li><strong>Atur Jadwal Belajar yang Konsisten</strong><br>Buatlah jadwal belajar harian yang konsisten dan sesuai dengan ritme belajar anak.</li><li><strong>Berikan Motivasi dan Dukungan</strong><br>Selalu berikan pujian atas usaha anak dan bantu mereka mengatasi kesulitan belajar.</li></ol><h3>Yang Harus Dihindari:</h3><ul><li>Membandingkan dengan anak lain</li><li>Memberikan tekanan berlebihan</li><li>Mengabaikan kesehatan mental anak</li></ul><p>Ingatlah bahwa setiap anak memiliki gaya belajar yang berbeda. Kenali karakteristik anak Anda dan sesuaikan pendekatan pembelajaran.</p>",
                "slug": "panduan-orang-tua-mendampingi-belajar-anak",
                "excerpt": "Panduan praktis untuk orang tua dalam mendampingi dan mendukung proses belajar anak di rumah dengan efektif.",
                "img_url": "https://via.placeholder.com/800x400/10b981/ffffff?text=Panduan+Orang+Tua",
                "category": "Panduan",
                "is_published": True,
                "published_at": datetime(2024, 3, 15, 16, 45, 0)
            },
            {
                "title": "Kegiatan Ekstrakurikuler: Mengembangkan Bakat dan Minat Siswa",
                "description": "<h2>Program Ekstrakurikuler Beragam</h2><p>Yayasan Al-Hikmah Tafatur menyediakan berbagai program ekstrakurikuler untuk mengembangkan bakat dan minat siswa di luar kegiatan akademik. Program ini dirancang untuk membentuk karakter dan soft skill siswa.</p><h3>Ekstrakurikuler yang Tersedia:</h3><h4>Bidang Olahraga:</h4><ul><li>Sepak Bola</li><li>Basket</li><li>Badminton</li><li>Tenis Meja</li><li>Karate</li></ul><h4>Bidang Seni dan Budaya:</h4><ul><li>Seni Qiro'ah</li><li>Kaligrafi</li><li>Teater</li><li>Musik</li><li>Tari Tradisional</li></ul><h4>Bidang Sains dan Teknologi:</h4><ul><li>Robotika</li><li>Coding Club</li><li>English Debate</li><li>Klub Sains</li></ul><p>Semua ekstrakurikuler dibimbing oleh instruktur berpengalaman dan alumni yang telah berprestasi di bidangnya masing-masing.</p>",
                "slug": "ekstrakurikuler-mengembangkan-bakat-minat-siswa",
                "excerpt": "Beragam program ekstrakurikuler untuk mengembangkan bakat, minat, dan soft skill siswa dalam berbagai bidang.",
                "img_url": "https://via.placeholder.com/800x400/f59e0b/ffffff?text=Ekstrakurikuler",
                "category": "Info",
                "is_published": True,
                "published_at": datetime(2024, 2, 28, 11, 20, 0)
            },
            {
                "title": "Fasilitas Terbaru: Laboratorium Sains dan Komputer Modern",
                "description": "<h2>Fasilitas Laboratorium Terbaru</h2><p>Sebagai komitmen dalam meningkatkan kualitas pendidikan, Yayasan Al-Hikmah Tafatur telah meresmikan laboratorium sains dan komputer dengan peralatan modern dan standar internasional.</p><h3>Laboratorium Sains:</h3><ul><li>Mikroskop digital dengan koneksi ke proyektor</li><li>Peralatan praktikum Fisika, Kimia, dan Biologi lengkap</li><li>Sistem ventilasi dan keamanan yang memadai</li><li>Kapasitas 30 siswa per sesi praktikum</li></ul><h3>Laboratorium Komputer:</h3><ul><li>40 unit komputer dengan spesifikasi terbaru</li><li>Software pembelajaran programming dan desain</li><li>Koneksi internet fiber optic berkecepatan tinggi</li><li>Sistem server untuk pembelajaran coding</li></ul><h3>Manfaat bagi Siswa:</h3><p>Dengan fasilitas ini, siswa dapat melakukan eksperimen dan praktikum dengan lebih optimal. Pembelajaran menjadi lebih interaktif dan siswa dapat langsung mengaplikasikan teori yang dipelajari.</p>",
                "slug": "fasilitas-laboratorium-sains-komputer-modern",
                "excerpt": "Fasilitas laboratorium sains dan komputer modern dengan peralatan terbaru untuk mendukung pembelajaran praktis siswa.",
                "img_url": "https://via.placeholder.com/800x400/8b5cf6/ffffff?text=Lab+Modern",
                "category": "Update",
                "is_published": True,
                "published_at": datetime(2024, 1, 30, 13, 10, 0)
            },
            {
                "title": "Kemitraan dengan Universitas Terkemuka untuk Program Dual Degree",
                "description": "<h2>Program Dual Degree dengan Universitas Partner</h2><p>SMA Al-Hikmah Tafatur menjalin kemitraan strategis dengan beberapa universitas terkemuka dalam dan luar negeri untuk program dual degree. Program ini memberikan kesempatan siswa untuk mendapatkan pengalaman pembelajaran tingkat universitas.</p><h3>Universitas Partner:</h3><ul><li>Universitas Indonesia (UI)</li><li>Institut Teknologi Bandung (ITB)</li><li>Universitas Gadjah Mada (UGM)</li><li>International Islamic University Malaysia (IIUM)</li><li>Al-Azhar University, Cairo</li></ul><h3>Keuntungan Program:</h3><ol><li>Mendapat kredit mata kuliah yang dapat diakui</li><li>Pengalaman pembelajaran dengan dosen universitas</li><li>Jalur masuk khusus ke universitas partner</li><li>Beasiswa untuk siswa berprestasi</li></ol><p>Program ini telah membantu banyak alumni untuk melanjutkan pendidikan ke jenjang yang lebih tinggi dengan persiapan yang matang.</p>",
                "slug": "kemitraan-universitas-program-dual-degree",
                "excerpt": "Program kemitraan dengan universitas terkemuka untuk memberikan pengalaman pembelajaran tingkat universitas kepada siswa SMA.",
                "img_url": "https://via.placeholder.com/800x400/dc2626/ffffff?text=Partnership+University",
                "category": "Program",
                "is_published": True,
                "published_at": datetime(2024, 4, 12, 15, 30, 0)
            },
            {
                "title": "Tips Menghadapi Ujian: Strategi Sukses untuk Siswa",
                "description": "<h2>Strategi Sukses Menghadapi Ujian</h2><p>Menghadapi ujian seringkali menjadi momen yang menegangkan bagi siswa. Berikut adalah tips dan strategi yang telah terbukti efektif untuk membantu siswa meraih hasil terbaik dalam ujian.</p><h3>Persiapan Jauh Hari:</h3><ol><li><strong>Buat Jadwal Belajar</strong><br>Susun jadwal belajar yang realistis, mulai dari 2-3 minggu sebelum ujian.</li><li><strong>Pahami Format Ujian</strong><br>Pelajari jenis soal, durasi, dan materi yang akan diujikan.</li><li><strong>Buat Ringkasan Materi</strong><br>Buat catatan ringkas dari setiap bab untuk memudahkan review.</li></ol><h3>Hari H Ujian:</h3><ul><li>Bangun lebih pagi dan sarapan bergizi</li><li>Baca doa dan tetap tenang</li><li>Baca instruksi soal dengan teliti</li><li>Mulai dari soal yang mudah terlebih dahulu</li><li>Manajemen waktu yang baik</li></ul><h3>Mindset yang Tepat:</h3><p>Ingatlah bahwa ujian adalah cara untuk mengukur pemahaman, bukan untuk menjatuhkan. Tetap percaya diri dan yakin dengan persiapan yang telah dilakukan.</p>",
                "slug": "tips-menghadapi-ujian-strategi-sukses-siswa",
                "excerpt": "Tips dan strategi praktis untuk membantu siswa mempersiapkan diri dan menghadapi ujian dengan lebih percaya diri dan sukses.",
                "img_url": "https://via.placeholder.com/800x400/4f46e5/ffffff?text=Tips+Ujian",
                "category": "Tips",
                "is_published": True,
                "published_at": datetime(2024, 3, 25, 7, 45, 0)
            },
            {
                "title": "Peringatan Hari Raya Idul Fitri: Jadwal Libur dan Kegiatan Sekolah",
                "description": "<h2>Peringatan Hari Raya Idul Fitri 1445 H</h2><p>Dalam rangka menyambut Hari Raya Idul Fitri 1445 H, Yayasan Al-Hikmah Tafatur mengucapkan Selamat Hari Raya Idul Fitri kepada seluruh civitas akademika. Mohon maaf lahir dan batin.</p><h3>Jadwal Libur:</h3><p><strong>Tanggal:</strong> 8 - 15 April 2024<br><strong>Masuk Kembali:</strong> Selasa, 16 April 2024</p><h3>Kegiatan Sebelum Libur:</h3><ul><li><strong>5 April 2024:</strong> Pengajian dan doa bersama</li><li><strong>6 April 2024:</strong> Pembagian THR untuk karyawan</li><li><strong>7 April 2024:</strong> Halal bi halal internal sekolah</li></ul><h3>Himbauan untuk Siswa dan Orang Tua:</h3><ol><li>Manfaatkan libur untuk quality time bersama keluarga</li><li>Tetap menjaga protokol kesehatan saat berkunjung</li><li>Jangan lupa untuk tetap membaca Al-Quran dan beribadah</li><li>Siapkan diri untuk masuk sekolah kembali</li></ol><p>Semoga Idul Fitri tahun ini membawa keberkahan dan kebahagiaan untuk kita semua. Taqabbalallahu minna wa minkum.</p>",
                "slug": "peringatan-idul-fitri-jadwal-libur-kegiatan",
                "excerpt": "Pengumuman jadwal libur Idul Fitri dan berbagai kegiatan peringatan yang akan dilaksanakan di lingkungan sekolah.",
                "img_url": "https://via.placeholder.com/800x400/059669/ffffff?text=Idul+Fitri+1445H",
                "category": "Pengumuman",
                "is_published": False,
                "published_at": datetime(2024, 4, 1, 12, 0, 0)
            }
        ]
        
        return articles_data

    async def create_articles(self):
        """Create 10 sample articles."""
        print("Creating 10 articles...")
        
        articles_data = self.generate_articles_data(10)
        
        created_articles = []
        for article_data in articles_data:
            try:
                # Check if article already exists
                existing = await self.session.execute(
                    text("SELECT * FROM articles WHERE slug = :slug"),
                    {"slug": article_data["slug"]}
                )
                if existing.fetchone():
                    print(f"Article with slug '{article_data['slug']}' already exists")
                    continue
                
                article = Article(**article_data)
                self.session.add(article)
                await self.session.flush()
                created_articles.append(article)
                print(f"Created article: {article.title}")
                
            except Exception as e:
                print(f"Error creating article '{article_data['title']}': {e}")
        
        await self.session.commit()
        return created_articles
    
    def generate_gallery_data(self, count=8):
        """Generate gallery data using faker with highlight system."""
        gallery_data = [
            {
                "img_url": "https://via.placeholder.com/600x400/4f46e5/ffffff?text=Gedung+Sekolah+Modern",
                "title": "Gedung Sekolah Modern dengan Fasilitas Lengkap",
                "excerpt": "Kompleks gedung sekolah Al-Hikmah Tafatur yang modern dengan fasilitas pembelajaran terdepan untuk mendukung aktivitas belajar mengajar.",
                "is_highlight": True
            },
            {
                "img_url": "https://via.placeholder.com/600x400/059669/ffffff?text=Kegiatan+Pembelajaran",
                "title": "Suasana Pembelajaran yang Kondusif dan Interaktif",
                "excerpt": "Aktivitas pembelajaran di kelas dengan metode interactive learning yang memungkinkan siswa aktif berpartisipasi dalam diskusi dan praktik.",
                "is_highlight": True
            },
            {
                "img_url": "https://via.placeholder.com/600x400/dc2626/ffffff?text=Prestasi+Siswa",
                "title": "Prestasi Membanggakan di Berbagai Kompetisi",
                "excerpt": "Para siswa Al-Hikmah Tafatur meraih berbagai prestasi di kompetisi akademik dan non-akademik tingkat regional maupun nasional.",
                "is_highlight": True
            },
            {
                "img_url": "https://via.placeholder.com/600x400/7c3aed/ffffff?text=Kegiatan+Ekstrakurikuler",
                "title": "Beragam Kegiatan Ekstrakurikuler yang Mengembangkan Bakat",
                "excerpt": "Siswa mengikuti berbagai kegiatan ekstrakurikuler mulai dari olahraga, seni, hingga teknologi untuk mengembangkan potensi diri.",
                "is_highlight": False
            },
            {
                "img_url": "https://via.placeholder.com/600x400/ea580c/ffffff?text=Program+Tahfidz",
                "title": "Program Tahfidz Al-Quran sebagai Keunggulan Sekolah",
                "excerpt": "Kegiatan program tahfidz Al-Quran yang menjadi ciri khas dan keunggulan sekolah dalam mencetak generasi Qur'ani yang berakhlak mulia.",
                "is_highlight": True
            },
            {
                "img_url": "https://via.placeholder.com/600x400/8b5cf6/ffffff?text=Laboratorium+Sains",
                "title": "Laboratorium Sains dan Komputer Terdepan",
                "excerpt": "Fasilitas laboratorium sains dan komputer dengan peralatan modern untuk mendukung pembelajaran praktis dan eksperimen siswa.",
                "is_highlight": False
            },
            {
                "img_url": "https://via.placeholder.com/600x400/10b981/ffffff?text=Perpustakaan+Digital",
                "title": "Perpustakaan Digital dengan Koleksi Lengkap",
                "excerpt": "Perpustakaan modern dengan koleksi buku fisik dan digital yang lengkap serta ruang baca yang nyaman untuk siswa.",
                "is_highlight": False
            },
            {
                "img_url": "https://via.placeholder.com/600x400/f59e0b/ffffff?text=Masjid+Sekolah",
                "title": "Masjid Sekolah sebagai Pusat Kegiatan Spiritual",
                "excerpt": "Masjid sekolah yang menjadi pusat kegiatan spiritual dan pembinaan akhlak siswa dengan arsitektur yang indah dan fasilitas lengkap.",
                "is_highlight": False
            }
        ]
        
        return gallery_data

    async def create_gallery_items(self):
        """Create 8 gallery items with highlight system."""
        print("Creating 8 gallery items...")
        
        gallery_data = self.generate_gallery_data(8)
        
        created_gallery = []
        for gallery_item in gallery_data:
            try:
                # Check if gallery item already exists
                existing = await self.session.execute(
                    text("SELECT * FROM galleries WHERE title = :title"),
                    {"title": gallery_item["title"]}
                )
                if existing.fetchone():
                    print(f"Gallery item '{gallery_item['title']}' already exists")
                    continue
                
                gallery = Gallery(**gallery_item)
                self.session.add(gallery)
                await self.session.flush()
                created_gallery.append(gallery)
                print(f"Created gallery item: {gallery.title}")
                
            except Exception as e:
                print(f"Error creating gallery item '{gallery_item['title']}': {e}")
        
        await self.session.commit()
        return created_gallery
    
    def generate_messages_data(self, count=15):
        """Generate message data using faker."""
        message_types = [
            "Pertanyaan tentang Sistem", "Kendala Upload", "Request Fitur", 
            "Pertanyaan Teknis", "Konsultasi", "Saran Perbaikan", "Laporan Bug",
            "Permintaan Demo", "Bantuan Login", "Update Password", "Training Request",
            "Feedback", "Komplain", "Apresiasi", "Info Maintenance"
        ]
        
        statuses = [MessageStatus.UNREAD, MessageStatus.READ, MessageStatus.ARCHIVED]
        
        messages_data = []
        for i in range(count):
            status = random.choice(statuses)
            msg_type = random.choice(message_types)
            
            message_data = {
                "email": self.fake.email(),
                "name": self.fake.name(),
                "title": f"{msg_type} - {self.fake.sentence(nb_words=4)}",
                "message": self.fake.paragraph(nb_sentences=random.randint(2, 5)),
                "status": status,
                "ip_address": self.fake.ipv4()
            }
            
            # Add read_at for READ and ARCHIVED messages
            if status in [MessageStatus.READ, MessageStatus.ARCHIVED]:
                message_data["read_at"] = self.fake.date_time_between(start_date='-30d', end_date='now')
            
            messages_data.append(message_data)
        
        return messages_data

    async def create_sample_messages(self):
        """Create 15 sample contact messages."""
        print("Creating 15 messages...")
        
        sample_messages = self.generate_messages_data(15)
        
        created_messages = []
        for msg_data in sample_messages:
            try:
                message = Message(**msg_data)
                self.session.add(message)
                await self.session.flush()
                created_messages.append(message)
                print(f"Created message from: {message.name}")
                
            except Exception as e:
                print(f"Error creating message from '{msg_data['name']}': {e}")
        
        await self.session.commit()
        return created_messages
    
    async def create_board_groups(self):
        """Create 3 board groups for foundation structure."""
        print("Creating 3 board groups...")
        
        groups_data = [
            {
                "title": "Pengurus Inti",
                "display_order": 1,
                "description": "Pengurus inti yayasan yang bertanggung jawab atas kebijakan strategis dan operasional utama"
            },
            {
                "title": "Jajaran Dewan",
                "display_order": 2,
                "description": "Anggota dewan pengurus yang berperan dalam pengawasan dan pembinaan institusi"
            },
            {
                "title": "Tim Ahli",
                "display_order": 3,
                "description": "Tim ahli dan konsultan yang memberikan masukan teknis dan akademis"
            }
        ]
        
        created_groups = {}
        for group_data in groups_data:
            try:
                # Check if group already exists
                existing = await self.session.execute(
                    text("SELECT * FROM board_groups WHERE title = :title"),
                    {"title": group_data["title"]}
                )
                existing_group = existing.fetchone()
                if existing_group:
                    print(f"Board group '{group_data['title']}' already exists")
                    # Convert to group object for consistency
                    group = BoardGroup(
                        id=existing_group[0],
                        title=existing_group[1],
                        display_order=existing_group[2],
                        description=existing_group[3]
                    )
                    created_groups[group_data["title"]] = group
                    continue
                
                group = BoardGroup(**group_data)
                self.session.add(group)
                await self.session.flush()
                created_groups[group_data["title"]] = group
                print(f"Created board group: {group.title}")
                
            except Exception as e:
                print(f"Error creating board group '{group_data['title']}': {e}")
        
        await self.session.commit()
        return created_groups

    def generate_board_members_data(self, groups):
        """Generate board member data using faker with board groups."""
        # Get group IDs
        pengurus_inti_id = groups["Pengurus Inti"].id
        jajaran_dewan_id = groups["Jajaran Dewan"].id
        tim_ahli_id = groups["Tim Ahli"].id
        
        board_data = [
            # Pengurus Inti
            {
                "name": "Dr. H. Muhammad Farid, M.A",
                "position": "Ketua Yayasan",
                "group_id": pengurus_inti_id,
                "member_order": 1,
                "img_url": "https://via.placeholder.com/300x300/4f46e5/ffffff?text=MF",
                "description": "<p>Dr. H. Muhammad Farid, M.A adalah seorang akademisi dan praktisi pendidikan dengan pengalaman lebih dari 20 tahun di bidang pendidikan Islam. Beliau meraih gelar doktor dari Universitas Al-Azhar, Mesir, dan memiliki visi untuk mengembangkan pendidikan Islam yang modern dan berkualitas.</p><p>Sebagai Ketua Yayasan Al-Hikmah Tafatur, beliau berkomitmen untuk memajukan pendidikan yang mengintegrasikan ilmu pengetahuan umum dengan nilai-nilai keislaman. Di bawah kepemimpinannya, yayasan telah berkembang pesat dan meraih berbagai prestasi.</p>"
            },
            {
                "name": "Dra. Hj. Aminah Syarifah, M.Pd",
                "position": "Wakil Ketua",
                "group_id": pengurus_inti_id,
                "member_order": 2,
                "img_url": "https://via.placeholder.com/300x300/059669/ffffff?text=AS",
                "description": "<p>Dra. Hj. Aminah Syarifah, M.Pd adalah seorang pendidik berpengalaman dengan latar belakang pendidikan dan manajemen. Beliau memiliki pengalaman mengajar selama 25 tahun dan telah menjabat sebagai kepala sekolah di beberapa institusi pendidikan terkemuka.</p><p>Sebagai Wakil Ketua, beliau fokus pada pengembangan kurikulum dan peningkatan kualitas pembelajaran. Beliau juga aktif dalam berbagai organisasi profesi guru dan sering menjadi narasumber dalam seminar pendidikan nasional.</p>"
            },
            {
                "name": "Ustadz Ahmad Zainuddin, Lc., M.A",
                "position": "Sekretaris Jenderal",
                "group_id": pengurus_inti_id,
                "member_order": 3,
                "img_url": "https://via.placeholder.com/300x300/dc2626/ffffff?text=AZ",
                "description": "<p>Ustadz Ahmad Zainuddin, Lc., M.A adalah lulusan Universitas Madinah, Arab Saudi, dengan spesialisasi dalam studi Islam dan manajemen pendidikan. Beliau memiliki kemampuan yang sangat baik dalam administrasi dan koordinasi program-program yayasan.</p><p>Sebagai Sekretaris Jenderal, beliau bertanggung jawab atas operasional harian yayasan dan koordinasi antar unit sekolah. Beliau juga aktif dalam pengembangan program tahfidz dan pembinaan spiritual siswa di semua jenjang pendidikan.</p>"
            },
            {
                "name": "Prof. Dr. H. Abdullah Rahman, M.A",
                "position": "Bendahara Umum",
                "group_id": pengurus_inti_id,
                "member_order": 4,
                "img_url": "https://via.placeholder.com/300x300/7c3aed/ffffff?text=AR",
                "description": "<p>Prof. Dr. H. Abdullah Rahman, M.A adalah seorang profesor di bidang ekonomi Islam dengan pengalaman lebih dari 15 tahun dalam manajemen keuangan pendidikan. Beliau meraih gelar profesor dari Universitas Indonesia dan memiliki keahlian dalam pengelolaan keuangan institusi pendidikan.</p><p>Sebagai Bendahara Umum, beliau bertanggung jawab atas perencanaan anggaran, pengelolaan keuangan, dan transparansi finansial yayasan. Beliau juga aktif dalam pengembangan program beasiswa untuk siswa berprestasi dari keluarga kurang mampu.</p>"
            },
            
            # Jajaran Dewan
            {
                "name": "Drs. H. Imam Nawawi, M.Si",
                "position": "Ketua Dewan Pengawas",
                "group_id": jajaran_dewan_id,
                "member_order": 1,
                "img_url": "https://via.placeholder.com/300x300/ea580c/ffffff?text=IN",
                "description": "<p>Drs. H. Imam Nawawi, M.Si adalah seorang praktisi manajemen dengan pengalaman lebih dari 18 tahun di berbagai institusi pendidikan. Beliau memiliki keahlian dalam bidang pengembangan SDM dan manajemen operasional.</p><p>Sebagai Ketua Dewan Pengawas, beliau fokus pada pengembangan kualitas tenaga pendidik dan peningkatan sistem manajemen sekolah. Beliau juga berperan dalam menjalin kemitraan dengan berbagai lembaga pendidikan dan industri.</p>"
            },
            {
                "name": "H. Ahmad Solichin, S.E., M.M",
                "position": "Anggota Dewan Pengawas",
                "group_id": jajaran_dewan_id,
                "member_order": 2,
                "img_url": "https://via.placeholder.com/300x300/f59e0b/ffffff?text=AS",
                "description": "<p>H. Ahmad Solichin, S.E., M.M adalah seorang pengusaha sukses dan praktisi manajemen bisnis dengan pengalaman lebih dari 20 tahun. Beliau memiliki keahlian dalam bidang keuangan dan strategi bisnis yang diterapkan untuk pengembangan yayasan.</p><p>Sebagai Anggota Dewan Pengawas, beliau memberikan masukan strategis dalam pengembangan infrastruktur dan sustainability finansial yayasan. Beliau juga aktif dalam program CSR untuk pendidikan.</p>"
            },
            {
                "name": "Dra. Hj. Fatimah Zahra, M.Pd.I",
                "position": "Anggota Dewan Pengawas",
                "group_id": jajaran_dewan_id,
                "member_order": 3,
                "img_url": "https://via.placeholder.com/300x300/10b981/ffffff?text=FZ",
                "description": "<p>Dra. Hj. Fatimah Zahra, M.Pd.I adalah seorang pendidik dan aktivis pendidikan Islam dengan pengalaman lebih dari 22 tahun. Beliau memiliki keahlian dalam pengembangan kurikulum Islamic studies dan pembinaan karakter siswa.</p><p>Sebagai Anggota Dewan Pengawas, beliau fokus pada pengawasan kualitas pendidikan Islam dan pembinaan akhlak siswa. Beliau juga berperan dalam pengembangan program tahfidz dan kegiatan spiritual.</p>"
            },
            
            # Tim Ahli
            {
                "name": "Prof. Dr. Ir. Bambang Sutrisno, M.T",
                "position": "Konsultan Teknologi Pendidikan",
                "group_id": tim_ahli_id,
                "member_order": 1,
                "img_url": "https://via.placeholder.com/300x300/8b5cf6/ffffff?text=BS",
                "description": "<p>Prof. Dr. Ir. Bambang Sutrisno, M.T adalah seorang profesor teknologi informasi dengan spesialisasi dalam teknologi pendidikan. Beliau memiliki pengalaman lebih dari 15 tahun dalam implementasi sistem informasi manajemen sekolah.</p><p>Sebagai Konsultan Teknologi Pendidikan, beliau berperan dalam pengembangan infrastruktur IT, sistem pembelajaran digital, dan modernisasi administrasi sekolah. Beliau juga memberikan training kepada guru dalam penggunaan teknologi pembelajaran.</p>"
            },
            {
                "name": "Dr. Hj. Siti Maryam, M.A",
                "position": "Konsultan Kurikulum",
                "group_id": tim_ahli_id,
                "member_order": 2,
                "img_url": "https://via.placeholder.com/300x300/ef4444/ffffff?text=SM",
                "description": "<p>Dr. Hj. Siti Maryam, M.A adalah seorang ahli kurikulum dengan pengalaman lebih dari 18 tahun dalam pengembangan kurikulum pendidikan Islam terpadu. Beliau meraih gelar doktor dari UIN Syarif Hidayatullah Jakarta.</p><p>Sebagai Konsultan Kurikulum, beliau berperan dalam merancang dan mengembangkan kurikulum yang mengintegrasikan ilmu umum dan agama. Beliau juga memberikan guidance dalam implementasi metode pembelajaran yang inovatif dan efektif.</p>"
            }
        ]
        
        return board_data

    async def create_board_members(self, groups):
        """Create board members with groups."""
        print("Creating board members with groups...")
        
        board_data = self.generate_board_members_data(groups)
        
        created_board = []
        for board_item in board_data:
            try:
                # Check if board member already exists
                existing = await self.session.execute(
                    text("SELECT * FROM board_members WHERE name = :name"),
                    {"name": board_item["name"]}
                )
                if existing.fetchone():
                    print(f"Board member '{board_item['name']}' already exists")
                    continue
                
                board = BoardMember(**board_item)
                self.session.add(board)
                await self.session.flush()
                created_board.append(board)
                print(f"Created board member: {board.name} ({board.position})")
                
            except Exception as e:
                print(f"Error creating board member '{board_item['name']}': {e}")
        
        await self.session.commit()
        return created_board
    
    async def verify_seeded_data(self):
        """Verify the seeded data."""
        print("\nVerifying seeded data...")
        
        # Count organizations
        org_count = await self.session.execute(text("SELECT COUNT(*) FROM organizations WHERE deleted_at IS NULL"))
        org_total = org_count.scalar()
        print(f"Total organizations: {org_total}")
        
        # Count users
        user_count = await self.session.execute(text("SELECT COUNT(*) FROM users WHERE deleted_at IS NULL"))
        user_total = user_count.scalar()
        print(f"Total users: {user_total}")
        
        # Count roles
        role_count = await self.session.execute(text("SELECT COUNT(*) FROM user_roles WHERE deleted_at IS NULL"))
        role_total = role_count.scalar()
        print(f"Total role assignments: {role_total}")
        
        # List users by role
        roles = ["admin", "kepala_sekolah", "guru"]
        for role_name in roles:
            users_with_role = await self.role_repo.get_users_with_role(role_name, active_only=True)
            print(f"{role_name}: {len(users_with_role)} users")
    
    async def clear_all_data(self):
        """Clear all seeded data."""
        print("Clearing all data...")
        
        try:
            # Clear in reverse order due to foreign key constraints
            # First, remove head references from organizations
            await self.session.execute(text("UPDATE organizations SET head_id = NULL WHERE head_id IS NOT NULL"))
            
            # Clear content tables (handle foreign key constraints)
            await self.session.execute(text("DELETE FROM messages"))
            await self.session.execute(text("DELETE FROM articles"))
            await self.session.execute(text("DELETE FROM galleries"))
            await self.session.execute(text("DELETE FROM board_members"))
            await self.session.execute(text("DELETE FROM board_groups"))
            
            # Clear RPP submissions first to avoid foreign key constraint
            await self.session.execute(text("DELETE FROM rpp_submissions"))
            await self.session.execute(text("DELETE FROM teacher_evaluations"))
            await self.session.execute(text("DELETE FROM periods"))
            
            # Clear user-related tables
            await self.session.execute(text("DELETE FROM user_roles"))
            await self.session.execute(text("DELETE FROM users"))
            await self.session.execute(text("DELETE FROM organizations"))
            
            await self.session.commit()
            print("All data cleared successfully!")
            
        except Exception as e:
            print(f"Error clearing data: {e}")
            await self.session.rollback()
            raise

    def simple_hash_password(self, password: str) -> str:
        """Simple password hashing for seeding (avoid bcrypt issues)."""
        return hashlib.sha256(password.encode()).hexdigest()

    async def run_seeding(self):
        """Run the complete seeding process."""
        print("Starting user seeding process...")
        print("=" * 50)
        
        try:
            # Create organizations
            organizations = await self.create_organizations()
            
            # Create users and assign roles
            users = await self.create_users_by_role(organizations)
            
            # Create sample permissions
            await self.create_sample_permissions()
            
            # Create academic periods
            periods = await self.create_periods()
            
            # Create sample articles
            articles = await self.create_articles()
            
            # Create gallery items
            gallery = await self.create_gallery_items()
            
            # Create sample messages
            messages = await self.create_sample_messages()
            
            # Create board groups
            board_groups = await self.create_board_groups()
            
            # Create board members
            board_members = await self.create_board_members(board_groups)
            
            # Verify data
            await self.verify_seeded_data()
            
            print("\n" + "=" * 50)
            print("Seeding completed successfully!")
            print("\nOrganizations created:")
            for org_key, org_data in organizations.items():
                org_name = org_data.name if hasattr(org_data, 'name') else str(org_data)
                print(f"  - {org_name}")
            
            print(f"\nUsers created: {len(users)}")
            print(f"Periods created: {len(periods)}")
            print(f"Articles created: {len(articles)}")
            print(f"Gallery items created: {len(gallery)}")
            print(f"Messages created: {len(messages)}")
            print(f"Board groups created: {len(board_groups)}")
            print(f"Board members created: {len(board_members)}")
            print("\nBoard Structure:")
            for group_name, group in board_groups.items():
                member_count = len([m for m in board_members if hasattr(m, 'group_id') and m.group_id == group.id])
                print(f"  - {group_name}: {member_count} members")
            print("\nLogin credentials:")
            print("Admin: admin@tafatur.id / @Password123")
            print("Kepala Sekolah: kepsek@[school-domain].sch.id / @Password123")
            print("Guru: guru[1-10]@[school-domain].sch.id / @Password123")
            
        except Exception as e:
            print(f"Error during seeding: {e}")
            raise


async def main():
    """Main seeding function."""
    parser = argparse.ArgumentParser(description='Database seeding script')
    parser.add_argument('action', choices=['up', 'down'], help='up: create data, down: clear data')
    args = parser.parse_args()
    
    try:
        # Get database session
        async for session in get_db():
            seeder = UserSeeder(session)
            
            if args.action == 'down':
                await seeder.clear_all_data()
            else:
                await seeder.run_seeding()
            break
            
    except Exception as e:
        print(f"Seeding failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)