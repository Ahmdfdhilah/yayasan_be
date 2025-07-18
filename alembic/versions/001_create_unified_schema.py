"""Create unified schema based on DB.MD

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Organizations table
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=True),
        sa.Column('type', sa.Enum('school', 'foundation', 'department', name='organizationtype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('website_url', sa.String(length=255), nullable=True),
        sa.Column('contact_info', sa.JSON(), nullable=True, comment='Contact details: phone, email, address, etc'),
        sa.Column('settings', sa.JSON(), nullable=True, comment='Organization-specific settings'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.Column('deleted_by', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # Create indexes for organizations
    op.create_index('idx_org_type', 'organizations', ['type'])
    op.create_index('idx_org_slug', 'organizations', ['slug'])
    op.create_index('idx_org_name', 'organizations', ['name'])
    
    # Users table (unified)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('profile', sa.JSON(), nullable=False, comment='User profile: name, phone, address, etc'),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'suspended', name='userstatus'), nullable=False),
        sa.Column('email_verified_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('remember_token', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.Column('deleted_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes for users
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_org', 'users', ['organization_id'])
    op.create_index('idx_user_status', 'users', ['status'])
    
    # User roles table (RBAC)
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_name', sa.String(length=50), nullable=False, comment='admin, guru, kepala_sekolah, content_manager, etc'),
        sa.Column('permissions', sa.JSON(), nullable=True, comment='Specific permissions for the role'),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.Column('deleted_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_name', 'organization_id', name='unique_user_role_org')
    )
    
    # Create indexes for user_roles
    op.create_index('idx_role_user', 'user_roles', ['user_id'])
    op.create_index('idx_role_org', 'user_roles', ['organization_id'])
    op.create_index('idx_role_name', 'user_roles', ['role_name'])
    
    # Media files table
    op.create_table('media_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('uploader_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='File metadata: width, height, duration, etc'),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.Column('deleted_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for media_files
    op.create_index('idx_media_uploader', 'media_files', ['uploader_id'])
    op.create_index('idx_media_org', 'media_files', ['organization_id'])
    op.create_index('idx_media_type', 'media_files', ['file_type'])
    op.create_index('idx_media_public', 'media_files', ['is_public'])
    
    # Password reset tokens table
    op.create_table('password_reset_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.Column('deleted_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    # Create indexes for password_reset_tokens
    op.create_index('idx_token_user', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_token_token', 'password_reset_tokens', ['token'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('password_reset_tokens')
    op.drop_table('media_files')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('organizations')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS organizationtype')
    op.execute('DROP TYPE IF EXISTS userstatus')