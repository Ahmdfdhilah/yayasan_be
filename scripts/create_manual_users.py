"""Manual user creation script yang bypasses service layer async issues."""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.models.enums import UserStatus
from src.auth.jwt import get_password_hash


class ManualUserCreator:
    """Manual user creator using direct SQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return get_password_hash(password)

    async def get_organization_id(self, org_name: str) -> int:
        """Get organization ID by name."""
        query = text(
            "SELECT id FROM organizations WHERE name = :name AND deleted_at IS NULL"
        )
        result = await self.session.execute(query, {"name": org_name})
        org_id = result.scalar()
        if not org_id:
            raise ValueError(f"Organization '{org_name}' not found")
        return org_id

    async def create_user_direct(
        self, email: str, password: str, profile: dict, organization_name: str = None
    ) -> int:
        """Create user directly with SQL."""
        try:
            # Get organization ID if provided
            org_id = None
            if organization_name:
                org_id = await self.get_organization_id(organization_name)

            # Hash password
            hashed_password = self.hash_password(password)

            # Create user
            user_query = text(
                """
                INSERT INTO users (email, password, profile, organization_id, status, created_at, updated_at)
                VALUES (:email, :password, :profile, :org_id, :status, :created_at, :updated_at)
                RETURNING id
            """
            )

            result = await self.session.execute(
                user_query,
                {
                    "email": email,
                    "password": hashed_password,
                    "profile": json.dumps(profile),
                    "org_id": org_id,
                    "status": "ACTIVE",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )

            user_id = result.scalar()
            await self.session.commit()

            print(f"Created user: {email} (ID: {user_id})")
            return user_id

        except Exception as e:
            print(f"Error creating user {email}: {e}")
            await self.session.rollback()
            return None

    async def create_user_role_direct(
        self, user_id: int, role_name: str, organization_id: int = None
    ) -> int:
        """Create user role directly with SQL."""
        try:
            role_query = text(
                """
                INSERT INTO user_roles (user_id, role_name, organization_id, is_active, created_at, updated_at)
                VALUES (:user_id, :role_name, :org_id, :is_active, :created_at, :updated_at)
                RETURNING id
            """
            )

            result = await self.session.execute(
                role_query,
                {
                    "user_id": user_id,
                    "role_name": role_name,
                    "org_id": organization_id,
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )

            role_id = result.scalar()
            await self.session.commit()

            print(f"  -> Assigned role: {role_name} (ID: {role_id})")
            return role_id

        except Exception as e:
            print(f"  -> Error assigning role {role_name}: {e}")
            await self.session.rollback()
            return None

    async def create_all_users(self):
        """Create all test users."""
        print("Creating users manually...")

        users_data = [
            {
                "email": "admin@tafatur.id",
                "password": "@Admin123",
                "profile": {"name": "System Administrator", "phone": "081234567891"},
                "organization": None,
                "roles": ["admin"],
            },
            {
                "email": "kepsek@sman1jakarta.sch.id",
                "password": "@KepSek123",
                "profile": {
                    "name": "Dr. Ahmad Susanto, M.Pd",
                    "position": "Kepala Sekolah",
                },
                "organization": "SMA Negeri 1 Jakarta",
                "roles": ["kepala_sekolah"],
            },
            {
                "email": "guru1@sman1jakarta.sch.id",
                "password": "@Guru123",
                "profile": {"name": "Siti Rahayu, S.Pd", "subject": "Matematika"},
                "organization": "SMA Negeri 1 Jakarta",
                "roles": ["guru"],
            },
            {
                "email": "guru2@sman1jakarta.sch.id",
                "password": "@Guru123",
                "profile": {
                    "name": "Budi Santoso, S.Pd",
                    "subject": "Bahasa Indonesia",
                },
                "organization": "SMA Negeri 1 Jakarta",
                "roles": ["guru"],
            },
            {
                "email": "kepsek@smpn5bandung.sch.id",
                "password": "@KepSek123",
                "profile": {
                    "name": "Dra. Sri Mulyani, M.M",
                    "position": "Kepala Sekolah",
                },
                "organization": "SMP Negeri 5 Bandung",
                "roles": ["kepala_sekolah"],
            },
            {
                "email": "guru1@smpn5bandung.sch.id",
                "password": "@Guru123",
                "profile": {"name": "Andi Wijaya, S.Pd", "subject": "IPA Terpadu"},
                "organization": "SMP Negeri 5 Bandung",
                "roles": ["guru"],
            },
    ]

        for user_data in users_data:
            # Check if user already exists
            check_query = text(
                "SELECT id FROM users WHERE email = :email AND deleted_at IS NULL"
            )
            result = await self.session.execute(
                check_query, {"email": user_data["email"]}
            )
            if result.scalar():
                print(f"User {user_data['email']} already exists, skipping...")
                continue

            # Create user
            user_id = await self.create_user_direct(
                user_data["email"],
                user_data["password"],
                user_data["profile"],
                user_data["organization"],
            )

            if user_id:
                # Get organization ID for role assignment
                org_id = None
                if user_data["organization"]:
                    try:
                        org_id = await self.get_organization_id(
                            user_data["organization"]
                        )
                    except:
                        org_id = None

                # Assign roles
                for role_name in user_data["roles"]:
                    await self.create_user_role_direct(user_id, role_name, org_id)

    async def verify_users(self):
        """Verify created users."""
        print("\nVerifying created users...")

        # Count users
        user_count = await self.session.execute(
            text("SELECT COUNT(*) FROM users WHERE deleted_at IS NULL")
        )
        total_users = user_count.scalar()
        print(f"Total users: {total_users}")

        # Count roles
        role_count = await self.session.execute(
            text("SELECT COUNT(*) FROM user_roles WHERE deleted_at IS NULL")
        )
        total_roles = role_count.scalar()
        print(f"Total role assignments: {total_roles}")

        # List users with roles
        users_query = text(
            """
            SELECT u.email, ur.role_name, o.name as org_name
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id AND ur.deleted_at IS NULL
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE u.deleted_at IS NULL
            ORDER BY u.email
        """
        )

        result = await self.session.execute(users_query)
        users = result.all()

        print("\nUsers and roles:")
        for email, role, org in users:
            org_str = f" @ {org}" if org else ""
            print(f"  {email} -> {role}{org_str}")


async def main():
    """Main function."""
    try:
        async for session in get_db():
            creator = ManualUserCreator(session)
            await creator.create_all_users()
            await creator.verify_users()

            print("\n" + "=" * 50)
            print("Manual user creation completed!")
            print("\nDefault login credentials:")
            print("Admin: admin@tafatur.id / @Admin123")
            print("Kepala Sekolah SMAN1: kepsek@sman1jakarta.sch.id / @KepSek123")
            print("Guru SMAN1: guru1@sman1jakarta.sch.id / @Guru123")
            print("Content Manager: content@nusantara.org / @Content123")
            break

    except Exception as e:
        print(f"Manual user creation failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
