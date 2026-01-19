"""Initial migration: create all tables

Revision ID: 47871d03964a
Revises:
Create Date: 2026-01-18 20:24:30.620980

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "47871d03964a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
        sa.UniqueConstraint('name', name=op.f('uq_roles_name'))
    )
    op.create_index(op.f('ix_roles_created_at'), 'roles', ['created_at'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=False)
    op.create_index(op.f('ix_roles_updated_at'), 'roles', ['updated_at'], unique=False)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_users_role_id_roles'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
        sa.UniqueConstraint('username', name=op.f('uq_users_username'))
    )
    op.create_index(op.f('ix_users_active'), 'users', ['active'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_role_id'), 'users', ['role_id'], unique=False)
    op.create_index(op.f('ix_users_updated_at'), 'users', ['updated_at'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create location_types table
    op.create_table(
        'location_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_location_types')),
        sa.UniqueConstraint('name', name=op.f('uq_location_types_name'))
    )
    op.create_index(op.f('ix_location_types_created_at'), 'location_types', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_types_name'), 'location_types', ['name'], unique=False)
    op.create_index(op.f('ix_location_types_updated_at'), 'location_types', ['updated_at'], unique=False)

    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location_metadata', sa.JSON(), nullable=True),
        sa.Column('location_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['location_type_id'], ['location_types.id'], name=op.f('fk_locations_location_type_id_location_types'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_locations'))
    )
    op.create_index(op.f('ix_locations_created_at'), 'locations', ['created_at'], unique=False)
    op.create_index(op.f('ix_locations_location_type_id'), 'locations', ['location_type_id'], unique=False)
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)
    op.create_index(op.f('ix_locations_updated_at'), 'locations', ['updated_at'], unique=False)

    # Create item_types table
    op.create_table(
        'item_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Enum('PARENT', 'CHILD', name='itemcategory'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_item_types'))
    )
    op.create_index(op.f('ix_item_types_category'), 'item_types', ['category'], unique=False)
    op.create_index(op.f('ix_item_types_created_at'), 'item_types', ['created_at'], unique=False)
    op.create_index(op.f('ix_item_types_name'), 'item_types', ['name'], unique=False)
    op.create_index(op.f('ix_item_types_updated_at'), 'item_types', ['updated_at'], unique=False)

    # Create parent_items table
    op.create_table(
        'parent_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('item_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['current_location_id'], ['locations.id'], name=op.f('fk_parent_items_current_location_id_locations'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['item_type_id'], ['item_types.id'], name=op.f('fk_parent_items_item_type_id_item_types'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_parent_items'))
    )
    op.create_index(op.f('ix_parent_items_created_at'), 'parent_items', ['created_at'], unique=False)
    op.create_index(op.f('ix_parent_items_created_by'), 'parent_items', ['created_by'], unique=False)
    op.create_index(op.f('ix_parent_items_current_location_id'), 'parent_items', ['current_location_id'], unique=False)
    op.create_index(op.f('ix_parent_items_item_type_id'), 'parent_items', ['item_type_id'], unique=False)
    op.create_index(op.f('ix_parent_items_name'), 'parent_items', ['name'], unique=False)
    op.create_index(op.f('ix_parent_items_updated_at'), 'parent_items', ['updated_at'], unique=False)

    # Create child_items table
    op.create_table(
        'child_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('item_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['item_type_id'], ['item_types.id'], name=op.f('fk_child_items_item_type_id_item_types'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['parent_item_id'], ['parent_items.id'], name=op.f('fk_child_items_parent_item_id_parent_items'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_child_items'))
    )
    op.create_index(op.f('ix_child_items_created_at'), 'child_items', ['created_at'], unique=False)
    op.create_index(op.f('ix_child_items_created_by'), 'child_items', ['created_by'], unique=False)
    op.create_index(op.f('ix_child_items_item_type_id'), 'child_items', ['item_type_id'], unique=False)
    op.create_index(op.f('ix_child_items_name'), 'child_items', ['name'], unique=False)
    op.create_index(op.f('ix_child_items_parent_item_id'), 'child_items', ['parent_item_id'], unique=False)
    op.create_index(op.f('ix_child_items_updated_at'), 'child_items', ['updated_at'], unique=False)

    # Create move_history table
    op.create_table(
        'move_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('moved_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('parent_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('moved_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['from_location_id'], ['locations.id'], name=op.f('fk_move_history_from_location_id_locations'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['moved_by'], ['users.id'], name=op.f('fk_move_history_moved_by_users'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['parent_item_id'], ['parent_items.id'], name=op.f('fk_move_history_parent_item_id_parent_items'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_location_id'], ['locations.id'], name=op.f('fk_move_history_to_location_id_locations'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_move_history'))
    )
    op.create_index(op.f('ix_move_history_from_location_id'), 'move_history', ['from_location_id'], unique=False)
    op.create_index(op.f('ix_move_history_moved_at'), 'move_history', ['moved_at'], unique=False)
    op.create_index(op.f('ix_move_history_moved_by'), 'move_history', ['moved_by'], unique=False)
    op.create_index(op.f('ix_move_history_parent_item_id'), 'move_history', ['parent_item_id'], unique=False)
    op.create_index(op.f('ix_move_history_to_location_id'), 'move_history', ['to_location_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('move_history')
    op.drop_table('child_items')
    op.drop_table('parent_items')
    op.drop_table('item_types')
    op.drop_table('locations')
    op.drop_table('location_types')
    op.drop_table('users')
    op.drop_table('roles')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS itemcategory")
