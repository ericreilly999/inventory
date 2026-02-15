"""Update admin email to valid domain

Revision ID: 20260215150000
Revises: 20260215144500
Create Date: 2026-02-15 15:00:00

"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = "20260215150000"
down_revision = "20260215144500"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update admin user email to use valid domain."""
    conn = op.get_bind()
    
    # Update admin user email from admin@inventory.local to admin@example.com
    # This fixes Pydantic EmailStr validation which rejects .local TLD
    conn.execute(
        sa.text("""
            UPDATE users 
            SET email = :new_email, updated_at = :updated_at
            WHERE username = 'admin' AND email = :old_email
        """),
        {
            "new_email": "admin@example.com",
            "old_email": "admin@inventory.local",
            "updated_at": datetime.now(timezone.utc),
        }
    )


def downgrade() -> None:
    """Revert admin user email back to .local domain."""
    conn = op.get_bind()
    
    conn.execute(
        sa.text("""
            UPDATE users 
            SET email = :old_email, updated_at = :updated_at
            WHERE username = 'admin' AND email = :new_email
        """),
        {
            "old_email": "admin@inventory.local",
            "new_email": "admin@example.com",
            "updated_at": datetime.now(timezone.utc),
        }
    )
