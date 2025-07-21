"""add_order_fields_to_evaluation_aspects

Revision ID: e51f2dd57a0d
Revises: 
Create Date: 2025-07-22 02:20:27.989685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e51f2dd57a0d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add order fields to evaluation_aspects."""
    # Add order columns to evaluation_aspects table
    op.add_column('evaluation_aspects', sa.Column('category_order', sa.Integer(), nullable=True))
    op.add_column('evaluation_aspects', sa.Column('aspect_order', sa.Integer(), nullable=True))
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_evaluation_aspects_category_order'), 'evaluation_aspects', ['category_order'], unique=False)
    op.create_index(op.f('ix_evaluation_aspects_aspect_order'), 'evaluation_aspects', ['aspect_order'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove order fields from evaluation_aspects."""
    # Remove indexes
    op.drop_index(op.f('ix_evaluation_aspects_category_order'), table_name='evaluation_aspects')
    op.drop_index(op.f('ix_evaluation_aspects_aspect_order'), table_name='evaluation_aspects')
    
    # Remove columns
    op.drop_column('evaluation_aspects', 'aspect_order')
    op.drop_column('evaluation_aspects', 'category_order')