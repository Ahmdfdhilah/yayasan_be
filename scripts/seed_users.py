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
from src.schemas.organization import OrganizationCreate
from src.schemas.user_role import UserRoleCreate
from src.models.enums import UserStatus, UserRole as UserRoleEnum
import hashlib


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
    
    async def create_organizations(self):
        """Create sample organizations."""
        print("Creating organizations...")
        
        organizations = [
            {
                "name": "SMA Negeri 1 Jakarta",
                "description": "Sekolah Menengah Atas Negeri 1 Jakarta",
                "head_id": None  # Will be set after creating users
            },
            {
                "name": "SMP Negeri 5 Bandung", 
                "description": "Sekolah Menengah Pertama Negeri 5 Bandung",
                "head_id": None  # Will be set after creating users
            },
            {
                "name": "SDN Cendekia Bogor",
                "description": "Sekolah Dasar Negeri Cendekia Bogor",
                "head_id": None  # Will be set after creating users
            }
        ]
        
        created_orgs = {}
        for i, org_data in enumerate(organizations):
            try:
                # Check if organization already exists by name
                existing = await self.org_repo.get_by_name(org_data["name"])
                if existing:
                    print(f"Organization {org_data['name']} already exists")
                    created_orgs[f"org_{i+1}"] = existing
                    continue
                
                org_create = OrganizationCreate(**org_data)
                organization = await self.org_service.create_organization(org_create)
                created_orgs[f"org_{i+1}"] = organization
                print(f"Created organization: {organization.name}")
            except Exception as e:
                print(f"Error creating organization {org_data['name']}: {e}")
        
        return created_orgs
    
    async def create_users_by_role(self, organizations):
        """Create users for each role."""
        print("Creating users by role...")
        
        # Get organization IDs
        org1_id = organizations.get("org_1").id if organizations.get("org_1") else None
        org2_id = organizations.get("org_2").id if organizations.get("org_2") else None  
        org3_id = organizations.get("org_3").id if organizations.get("org_3") else None
        
        users_data = [
            # Super Admin
            {
                "email": "superadmin@tafatur.id",
                "password": "@SuperAdmin123",
                "profile": {
                    "name": "Super Administrator",
                    "phone": "081234567890",
                    "address": "Jakarta, Indonesia",
                    "position": "Super Administrator"
                },
                "organization_id": None,
                "status": UserStatus.ACTIVE,
                "roles": ["super_admin"]
            },
            
            # System Admin
            {
                "email": "admin@tafatur.id",
                "password": "@Admin123",
                "profile": {
                    "name": "System Administrator",
                    "phone": "081234567891",
                    "address": "Jakarta, Indonesia",
                    "position": "System Administrator"
                },
                "organization_id": None,
                "status": UserStatus.ACTIVE,
                "roles": ["admin"]
            },
            
            # Kepala Sekolah SMA Negeri 1 Jakarta
            {
                "email": "kepsek@sman1jakarta.sch.id",
                "password": "@KepSek123",
                "profile": {
                    "name": "Dr. Ahmad Susanto, M.Pd",
                    "phone": "081234567892",
                    "address": "Jakarta Pusat",
                    "position": "Kepala Sekolah",
                    "nip": "197001011990031001"
                },
                "organization_id": org1_id,
                "status": UserStatus.ACTIVE,
                "roles": ["kepala_sekolah"],
                "is_head": True
            },
            
            # Guru SMA Negeri 1 Jakarta
            {
                "email": "guru1@sman1jakarta.sch.id",
                "password": "@Guru123",
                "profile": {
                    "name": "Siti Rahayu, S.Pd",
                    "phone": "081234567893",
                    "address": "Jakarta Timur",
                    "position": "Guru Matematika",
                    "nip": "198505152010012001",
                    "subject": "Matematika",
                    "class": "X IPA 1"
                },
                "organization_id": org1_id,
                "status": UserStatus.ACTIVE,
                "roles": ["guru"]
            },
            
            {
                "email": "guru2@sman1jakarta.sch.id",
                "password": "@Guru123",
                "profile": {
                    "name": "Budi Santoso, S.Pd",
                    "phone": "081234567894",
                    "address": "Jakarta Selatan",
                    "position": "Guru Bahasa Indonesia",
                    "nip": "198203101999031002",
                    "subject": "Bahasa Indonesia",
                    "class": "XI IPS 2"
                },
                "organization_id": org1_id,
                "status": UserStatus.ACTIVE,
                "roles": ["guru"]
            },
            
            # Kepala Sekolah SMP Negeri 5 Bandung
            {
                "email": "kepsek@smpn5bandung.sch.id",
                "password": "@KepSek123",
                "profile": {
                    "name": "Dra. Sri Mulyani, M.M",
                    "phone": "081234567895",
                    "address": "Bandung",
                    "position": "Kepala Sekolah",
                    "nip": "196812121992032001"
                },
                "organization_id": org2_id,
                "status": UserStatus.ACTIVE,
                "roles": ["kepala_sekolah"],
                "is_head": True
            },
            
            # Guru SMP Negeri 5 Bandung
            {
                "email": "guru1@smpn5bandung.sch.id",
                "password": "@Guru123",
                "profile": {
                    "name": "Andi Wijaya, S.Pd",
                    "phone": "081234567896",
                    "address": "Bandung",
                    "position": "Guru IPA",
                    "nip": "199001011015021001",
                    "subject": "IPA Terpadu",
                    "class": "VIII A"
                },
                "organization_id": org2_id,
                "status": UserStatus.ACTIVE,
                "roles": ["guru"]
            },
            
            # Kepala Sekolah SDN Cendekia Bogor
            {
                "email": "kepsek@sdncendekia.sch.id",
                "password": "@KepSek123",
                "profile": {
                    "name": "Ir. Bambang Wijayanto, M.Pd",
                    "phone": "081234567897",
                    "address": "Bogor",
                    "position": "Kepala Sekolah",
                    "nip": "197505101998021001"
                },
                "organization_id": org3_id,
                "status": UserStatus.ACTIVE,
                "roles": ["kepala_sekolah"],
                "is_head": True
            },
            
            # Guru SDN Cendekia Bogor
            {
                "email": "guru1@sdncendekia.sch.id",
                "password": "@Guru123",
                "profile": {
                    "name": "Lestari Indah, S.Pd",
                    "phone": "081234567898",
                    "address": "Bogor",
                    "position": "Guru Kelas 5",
                    "nip": "199205152015022001",
                    "class": "V-A"
                },
                "organization_id": org3_id,
                "status": UserStatus.ACTIVE,
                "roles": ["guru"]
            }
        ]
        
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
            if hasattr(user, 'email'):
                if user.email == "kepsek@sman1jakarta.sch.id":
                    head_assignments.append((organizations.get("org_1"), user.id))
                elif user.email == "kepsek@smpn5bandung.sch.id":
                    head_assignments.append((organizations.get("org_2"), user.id))
                elif user.email == "kepsek@sdncendekia.sch.id":
                    head_assignments.append((organizations.get("org_3"), user.id))
        
        # Update organizations with head_id
        for org, head_id in head_assignments:
            if org and head_id:
                try:
                    await self.org_repo.update(org.id, {"head_id": head_id})
                    print(f"  -> Assigned head {head_id} to organization {org.name}")
                except Exception as e:
                    print(f"  -> Error assigning head to {org.name}: {e}")
    
    async def create_sample_permissions(self):
        """Create sample permission templates for roles."""
        print("Setting up role permissions...")
        
        role_permissions = {
            "super_admin": {
                "users.create": True,
                "users.read": True,
                "users.update": True,
                "users.delete": True,
                "organizations.create": True,
                "organizations.read": True,
                "organizations.update": True,
                "organizations.delete": True,
                "roles.create": True,
                "roles.read": True,
                "roles.update": True,
                "roles.delete": True,
                "evaluations.create": True,
                "evaluations.read": True,
                "evaluations.update": True,
                "evaluations.delete": True,
                "rpps.create": True,
                "rpps.read": True,
                "rpps.update": True,
                "rpps.delete": True,
                "analytics.read": True,
                "system.admin": True
            },
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
            "content_manager": {
                "content.create": True,
                "content.read": True,
                "content.update": True,
                "content.delete": True,
                "media.upload": True,
                "media.manage": True
            }
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
        roles = ["super_admin", "admin", "kepala_sekolah", "guru", "content_manager"]
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
            
            # Then clear the rest
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
            
            # Verify data
            await self.verify_seeded_data()
            
            print("\n" + "=" * 50)
            print("Seeding completed successfully!")
            print("\nOrganizations created:")
            for org_key, org_data in organizations.items():
                org_name = org_data.name if hasattr(org_data, 'name') else str(org_data)
                print(f"  - {org_name}")
            
            print(f"\nUsers created: {len(users)}")
            print("\nLogin credentials:")
            print("Super Admin: superadmin@tafatur.id / @SuperAdmin123")
            print("Admin: admin@tafatur.id / @Admin123")
            print("Kepala Sekolah: kepsek@[school-domain] / @KepSek123")
            print("Guru: guru1@[school-domain] / @Guru123")
            
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