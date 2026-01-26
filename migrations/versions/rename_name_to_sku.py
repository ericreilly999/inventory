"""rename name to sku in items

Revision ID: rename_name_to_sku
Revises: 
Create Date: 2026-01-26

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'rename_name_to_sku'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Rename name column to sku in parent_items and child_items tables."""
    # Rename column in parent_items table
    op.alter_column('parent_items', 'name', new_column_name='sku')
    
    # Rename column in child_items table
    op.alter_column('child_items', 'name', new_column_name='sku')


def downgrade():
    """Revert sku column back to name."""
    # Revert column in parent_items table
    op.alter_column('parent_items', 'sku', new_column_name='name')
    
    # Revert column in child_items table
    op.alter_column('child_items', 'sku', new_column_name='name')
