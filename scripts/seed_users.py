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
                "name": "SMA Negeri 1 Jakarta",
                "description": "Sekolah Menengah Atas Negeri 1 Jakarta",
                "head_id": None
            },
            {
                "name": "SMA Negeri 2 Bandung", 
                "description": "Sekolah Menengah Atas Negeri 2 Bandung",
                "head_id": None
            },
            {
                "name": "SMA Negeri 3 Surabaya",
                "description": "Sekolah Menengah Atas Negeri 3 Surabaya",
                "head_id": None
            },
            {
                "name": "SMP Negeri 1 Yogyakarta",
                "description": "Sekolah Menengah Pertama Negeri 1 Yogyakarta",
                "head_id": None
            },
            {
                "name": "SMP Negeri 2 Semarang",
                "description": "Sekolah Menengah Pertama Negeri 2 Semarang",
                "head_id": None
            },
            {
                "name": "SMP Negeri 3 Medan", 
                "description": "Sekolah Menengah Pertama Negeri 3 Medan",
                "head_id": None
            },
            {
                "name": "SMP Negeri 4 Makassar",
                "description": "Sekolah Menengah Pertama Negeri 4 Makassar",
                "head_id": None
            },
            {
                "name": "SDN Cendekia Bogor",
                "description": "Sekolah Dasar Negeri Cendekia Bogor",
                "head_id": None
            },
            {
                "name": "SDN Harapan Depok",
                "description": "Sekolah Dasar Negeri Harapan Depok",
                "head_id": None
            },
            {
                "name": "SDN Maju Tangerang",
                "description": "Sekolah Dasar Negeri Maju Tangerang",
                "head_id": None
            },
            {
                "name": "SDN Cerdas Bekasi",
                "description": "Sekolah Dasar Negeri Cerdas Bekasi",
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
            {"type": "SMA", "location": "Jakarta", "domain": "sman1jakarta"},
            {"type": "SMA", "location": "Bandung", "domain": "sman2bandung"},
            {"type": "SMA", "location": "Surabaya", "domain": "sman3surabaya"},
            {"type": "SMP", "location": "Yogyakarta", "domain": "smpn1yogya"},
            {"type": "SMP", "location": "Semarang", "domain": "smpn2semarang"},
            {"type": "SMP", "location": "Medan", "domain": "smpn3medan"},
            {"type": "SMP", "location": "Makassar", "domain": "smpn4makassar"},
            {"type": "SD", "location": "Bogor", "domain": "sdncendekia"},
            {"type": "SD", "location": "Depok", "domain": "sdnharapan"},
            {"type": "SD", "location": "Tangerang", "domain": "sdnmaju"},
            {"type": "SD", "location": "Bekasi", "domain": "sdncerdas"}
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
            "Dr. Ahmad Susanto, M.Pd", "Dra. Sri Mulyani, M.M", "Prof. Bambang Wijayanto, M.Pd",
            "Dr. Siti Nurhaliza, M.Pd", "Drs. Rudi Setiawan, M.M", "Dr. Linda Sari, M.Pd",
            "Drs. Hendra Pratama, M.Pd", "Dr. Maya Indah, M.M", "Prof. Andi Gunawan, M.Pd",
            "Dra. Dewi Lestari, M.Pd", "Dr. Budi Santoso, M.M"
        ]
        
        phone_counter = 892
        nip_counter = 1001
        
        # Generate users for 11 organizations
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
    
    def generate_articles_data(self, count=15):
        """Generate article data using faker."""
        categories = ["Pengumuman", "Tutorial", "Update", "Event", "Tips", "Berita", "Panduan", "Info"]
        colors = ["4f46e5", "059669", "dc2626", "7c3aed", "ea580c", "10b981", "f59e0b", "8b5cf6"]
        
        articles_data = []
        for i in range(count):
            category = random.choice(categories)
            color = random.choice(colors)
            title = f"{category}: {self.fake.sentence(nb_words=6)}"
            
            articles_data.append({
                "title": title,
                "description": f"<p>{self.fake.paragraph(nb_sentences=3)}</p><p>{self.fake.paragraph(nb_sentences=2)}</p>",
                "slug": f"{title.lower().replace(' ', '-').replace(':', '')}-{i+1}",
                "excerpt": self.fake.sentence(nb_words=12),
                "img_url": f"https://via.placeholder.com/800x400/{color}/ffffff?text={category}+{i+1}",
                "category": category,
                "is_published": random.choice([True, True, False]),  # 2/3 published
                "published_at": self.fake.date_time_between(start_date='-2y', end_date='now')
            })
        
        return articles_data

    async def create_articles(self):
        """Create 15 sample articles."""
        print("Creating 15 articles...")
        
        articles_data = self.generate_articles_data(15)
        
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
    
    def generate_gallery_data(self, count=15):
        """Generate gallery data using faker."""
        activities = [
            "Kegiatan Pembelajaran", "Workshop PKG", "Evaluasi Guru", "Prestasi Siswa", 
            "Fasilitas Sekolah", "Ekstrakurikuler", "Upacara Bendera", "Olahraga",
            "Seni Budaya", "Kompetisi", "Seminar", "Pelatihan", "Kunjungan",
            "Lomba", "Festival"
        ]
        colors = ["4f46e5", "059669", "dc2626", "7c3aed", "ea580c", "10b981", "f59e0b", "8b5cf6"]
        
        gallery_data = []
        for i in range(count):
            activity = random.choice(activities)
            color = random.choice(colors)
            
            gallery_data.append({
                "img_url": f"https://via.placeholder.com/600x400/{color}/ffffff?text={activity.replace(' ', '+')}+{i+1}",
                "title": f"{activity} - {self.fake.company()}",
                "excerpt": self.fake.sentence(nb_words=10),
                "display_order": i + 1
            })
        
        return gallery_data

    async def create_gallery_items(self):
        """Create 15 gallery items."""
        print("Creating 15 gallery items...")
        
        gallery_data = self.generate_gallery_data(15)
        
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
    
    def generate_board_members_data(self, count=15):
        """Generate board member data using faker."""
        positions = [
            "Ketua Dewan", "Wakil Ketua", "Sekretaris", "Bendahara", "Anggota Dewan",
            "Komisaris", "Direktur", "Wakil Direktur", "Manajer", "Supervisor",
            "Koordinator", "Kepala Divisi", "Wakil Kepala", "Penasehat", "Auditor"
        ]
        colors = ["4f46e5", "059669", "dc2626", "7c3aed", "ea580c", "10b981", "f59e0b", "8b5cf6"]
        
        board_data = []
        for i in range(count):
            position = positions[i] if i < len(positions) else random.choice(positions)
            color = random.choice(colors)
            name = self.fake.name()
            
            board_data.append({
                "name": name,
                "position": position,
                "img_url": f"https://via.placeholder.com/300x300/{color}/ffffff?text={name.replace(' ', '+')[0:2]}",
                "description": self.fake.paragraph(nb_sentences=3),
                "display_order": i + 1
            })
        
        return board_data

    async def create_board_members(self):
        """Create 15 board members."""
        print("Creating 15 board members...")
        
        board_data = self.generate_board_members_data(15)
        
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
                print(f"Created board member: {board.name}")
                
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
            
            # Clear content tables
            await self.session.execute(text("DELETE FROM messages"))
            await self.session.execute(text("DELETE FROM articles"))
            await self.session.execute(text("DELETE FROM galleries"))
            await self.session.execute(text("DELETE FROM periods"))
            await self.session.execute(text("DELETE FROM board_members"))
            
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
            
            # Create board members
            board_members = await self.create_board_members()
            
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
            print(f"Board members created: {len(board_members)}")
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