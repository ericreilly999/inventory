"""fix_location_deletion_constraints

Revision ID: 20260222020000
Revises: 382574989839
Create Date: 2026-02-22 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260222020000"
down_revision = "382574989839"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Get connection to check existing constraints
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Get existing foreign keys on move_history table
    existing_fks = inspector.get_foreign_keys("move_history")
    
    # Find and drop the location foreign keys
    for fk in existing_fks:
        if fk['referred_table'] == 'locations':
            print(f"Dropping constraint: {fk['name']}")
            op.drop_constraint(fk['name'], "move_history", type_="foreignkey")
    
    # Recreate foreign key constraints with SET NULL on delete
    op.create_foreign_key(
        "fk_move_history_from_location_id_locations",
        "move_history",
        "locations",
        ["from_location_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_move_history_to_location_id_locations",
        "move_history",
        "locations",
        ["to_location_id"],
        ["id"],
        ondelete="SET NULL",
    )
    
    print("Successfully updated move_history foreign key constraints to SET NULL")


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop SET NULL constraints
    op.drop_constraint(
        "fk_move_history_from_location_id_locations",
        "move_history",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_move_history_to_location_id_locations",
        "move_history",
        type_="foreignkey",
    )

    # Recreate original RESTRICT constraints
    op.create_foreign_key(
        "fk_move_history_from_location_id_locations",
        "move_history",
        "locations",
        ["from_location_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_move_history_to_location_id_locations",
        "move_history",
        "locations",
        ["to_location_id"],
        ["id"],
        ondelete="RESTRICT",
    )
