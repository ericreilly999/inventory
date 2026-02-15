"""add unique constraint location name type

Revision ID: 20260201184930
Revises: 20260201181337
Create Date: 2026-02-01 18:49:30.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260201184930"
down_revision: Union[str, None] = "20260201181337"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint to location name + type."""
    op.create_unique_constraint(
        "uq_location_name_type", "locations", ["name", "location_type_id"]
    )


def downgrade() -> None:
    """Remove unique constraint from location name + type."""
    op.drop_constraint("uq_location_name_type", "locations", type_="unique")
