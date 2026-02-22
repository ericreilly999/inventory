"""Check database constraints directly to understand deletion issues."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment or use staging default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inventory_user:inventory_pass@staging-inventory-db.c9kqx8y7z8y7.us-east-1.rds.amazonaws.com:5432/inventory_db"
)

def check_constraints():
    """Check database constraints and data."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("=" * 70)
    print("Database Constraint Check")
    print("=" * 70)
    
    # Check foreign key constraints on parent_items table
    print("\n1. Foreign key constraints on parent_items:")
    result = session.execute(text("""
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        JOIN information_schema.referential_constraints AS rc
            ON rc.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'parent_items'
            AND ccu.table_name = 'locations';
    """))
    
    for row in result:
        print(f"  Constraint: {row.constraint_name}")
        print(f"  Column: {row.column_name} -> {row.foreign_table_name}.{row.foreign_column_name}")
        print(f"  Delete rule: {row.delete_rule}")
        print()
    
    # Check foreign key constraints on move_history table
    print("2. Foreign key constraints on move_history:")
    result = session.execute(text("""
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        JOIN information_schema.referential_constraints AS rc
            ON rc.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'move_history'
            AND ccu.table_name = 'locations';
    """))
    
    for row in result:
        print(f"  Constraint: {row.constraint_name}")
        print(f"  Column: {row.column_name} -> {row.foreign_table_name}.{row.foreign_column_name}")
        print(f"  Delete rule: {row.delete_rule}")
        print()
    
    # Check specific locations that can't be deleted
    problem_locations = [
        ('dc40a9df-c188-4960-8305-d1dc39125ff2', 'Corporate Office'),
        ('4ec6964e-a4d5-42fe-80a4-17118eed3d14', 'IT Storage'),
        ('5571f3c9-48c6-4df6-bc2f-ce3955fa5957', 'Damage Quarantine'),
        ('a31276ca-b2aa-41e6-b1c8-0f71a7ecf868', 'Repair Quarantine'),
        ('1bde865e-56c9-488f-be7c-8a5227420df6', 'Cleaning Quarantine'),
    ]
    
    print("3. Checking specific locations:")
    for location_id, location_name in problem_locations:
        print(f"\n  {location_name} ({location_id}):")
        
        # Check parent_items
        result = session.execute(
            text("SELECT COUNT(*) FROM parent_items WHERE current_location_id = :loc_id"),
            {"loc_id": location_id}
        )
        count = result.scalar()
        print(f"    Parent items with current_location_id: {count}")
        
        # Check move_history from_location
        result = session.execute(
            text("SELECT COUNT(*) FROM move_history WHERE from_location_id = :loc_id"),
            {"loc_id": location_id}
        )
        count = result.scalar()
        print(f"    Move history with from_location_id: {count}")
        
        # Check move_history to_location
        result = session.execute(
            text("SELECT COUNT(*) FROM move_history WHERE to_location_id = :loc_id"),
            {"loc_id": location_id}
        )
        count = result.scalar()
        print(f"    Move history with to_location_id: {count}")
        
        # Check assignment_history
        result = session.execute(
            text("SELECT COUNT(*) FROM assignment_history WHERE location_id = :loc_id"),
            {"loc_id": location_id}
        )
        count = result.scalar()
        print(f"    Assignment history with location_id: {count}")
    
    session.close()
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        check_constraints()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
