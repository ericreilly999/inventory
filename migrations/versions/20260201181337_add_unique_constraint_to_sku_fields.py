"""add unique constraint to sku fields

Revision ID: 20260201181337
Revises: 47871d03964a
Create Date: 2026-02-01 18:13:37.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260201181337'
down_revision: Union[str, None] = '49871d03964c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraints to SKU fields."""
    # Add unique constraint to parent_items.sku
    op.create_unique_constraint(
        'uq_parent_items_sku',
        'parent_items',
        ['sku']
    )
    
    # Add unique constraint to child_items.sku
    op.create_unique_constraint(
        'uq_child_items_sku',
        'child_items',
        ['sku']
    )


def downgrade() -> None:
    """Remove unique constraints from SKU fields."""
    # Remove unique constraint from child_items.sku
    op.drop_constraint(
        'uq_child_items_sku',
        'child_items',
        type_='unique'
    )
    
    # Remove unique constraint from parent_items.sku
    op.drop_constraint(
        'uq_parent_items_sku',
        'parent_items',
        type_='unique'
    )
