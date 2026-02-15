"""allow_location_deletion_with_history

Revision ID: 382574989839
Revises: 20260215150000
Create Date: 2026-02-15 10:45:59.366770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "382574989839"
down_revision = "20260215150000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Drop existing foreign key constraints
    op.drop_constraint(
        "move_history_from_location_id_fkey", "move_history", type_="foreignkey"
    )
    op.drop_constraint(
        "move_history_to_location_id_fkey", "move_history", type_="foreignkey"
    )

    # Recreate foreign key constraints with SET NULL on delete
    op.create_foreign_key(
        "move_history_from_location_id_fkey",
        "move_history",
        "locations",
        ["from_location_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "move_history_to_location_id_fkey",
        "move_history",
        "locations",
        ["to_location_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop SET NULL constraints
    op.drop_constraint(
        "move_history_from_location_id_fkey", "move_history", type_="foreignkey"
    )
    op.drop_constraint(
        "move_history_to_location_id_fkey", "move_history", type_="foreignkey"
    )

    # Recreate original RESTRICT constraints
    op.create_foreign_key(
        "move_history_from_location_id_fkey",
        "move_history",
        "locations",
        ["from_location_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "move_history_to_location_id_fkey",
        "move_history",
        "locations",
        ["to_location_id"],
        ["id"],
        ondelete="RESTRICT",
    )
