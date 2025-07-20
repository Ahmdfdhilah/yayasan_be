"""Add RPP submission tables

Revision ID: 001
Revises: 
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create rpp_submissions table
    op.create_table('rpp_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'REVISION_NEEDED', name='rppsubmissionstatus'), nullable=False, server_default='DRAFT'),
        sa.Column('reviewer_id', sa.Integer(), nullable=True),
        sa.Column('review_notes', sa.String(length=1000), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['period_id'], ['periods.id'], ),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('teacher_id', 'period_id', name='uq_teacher_period_submission')
    )
    op.create_index(op.f('ix_rpp_submissions_period_id'), 'rpp_submissions', ['period_id'], unique=False)
    op.create_index(op.f('ix_rpp_submissions_teacher_id'), 'rpp_submissions', ['teacher_id'], unique=False)

    # Create rpp_submission_items table
    op.create_table('rpp_submission_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('rpp_type', sa.Enum('RENCANA_PROGRAM_HARIAN', 'RENCANA_PROGRAM_SEMESTER', 'RENCANA_PROGRAM_TAHUNAN', name='rpptype'), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['media_files.id'], ),
        sa.ForeignKeyConstraint(['period_id'], ['periods.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('teacher_id', 'period_id', 'rpp_type', name='uq_teacher_period_rpp_type')
    )
    op.create_index(op.f('ix_rpp_submission_items_period_id'), 'rpp_submission_items', ['period_id'], unique=False)
    op.create_index(op.f('ix_rpp_submission_items_teacher_id'), 'rpp_submission_items', ['teacher_id'], unique=False)


def downgrade() -> None:
    # Drop rpp_submission_items table
    op.drop_index(op.f('ix_rpp_submission_items_teacher_id'), table_name='rpp_submission_items')
    op.drop_index(op.f('ix_rpp_submission_items_period_id'), table_name='rpp_submission_items')
    op.drop_table('rpp_submission_items')

    # Drop rpp_submissions table
    op.drop_index(op.f('ix_rpp_submissions_teacher_id'), table_name='rpp_submissions')
    op.drop_index(op.f('ix_rpp_submissions_period_id'), table_name='rpp_submissions')
    op.drop_table('rpp_submissions')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS rppsubmissionstatus')
    op.execute('DROP TYPE IF EXISTS rpptype')