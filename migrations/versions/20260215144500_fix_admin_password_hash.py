"""Fix admin password hash

Revision ID: 20260215144500
Revises: 20260201214107
Create Date: 2026-02-15 14:45:00

"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = "20260215144500"
down_revision = "20260201214107"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update admin user password hash to correct value."""
    conn = op.get_bind()

    # Update admin user password hash
    # Correct bcrypt hash for password 'admin'
    conn.execute(
        sa.text(
            """
            UPDATE users 
            SET password_hash = :password_hash,
                updated_at = :updated_at
            WHERE username = 'admin'
        """
        ),
        {
            "password_hash": "$2b$12$SD4NhDwd632jUZahyAguMu8BdxCXZGUhwbB.uWTln/KDFTsnYaXay",
            "updated_at": datetime.now(timezone.utc),
        },
    )


def downgrade() -> None:
    """Revert admin password hash (not recommended)."""
    # No downgrade - we don't want to revert to the broken hash
    pass
