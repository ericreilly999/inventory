"""Test direct database deletion to see the actual error."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from uuid import UUID

# Use staging database
DATABASE_URL = "postgresql://inventory_user:inventory_pass@staging-inventory-db.c9kqx8y7z8y7.us-east-1.rds.amazonaws.com:5432/inventory_db"

def test_deletion():
    """Test deleting a location directly in the database."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("=" * 70)
    print("Direct Database Deletion Test")
    print("=" * 70)
    
    # Test with Corporate Office
    location_id = 'dc40a9df-c188-4960-8305-d1dc39125ff2'
    location_name = 'Corporate Office'
    
    print(f"\nTesting deletion of: {location_name}")
    print(f"ID: {location_id}")
    
    # First, check what references this location
    print("\nChecking references:")
    
    # Check parent_items
    result = session.execute(
        text("SELECT id, sku FROM parent_items WHERE current_location_id = :loc_id LIMIT 5"),
        {"loc_id": location_id}
    )
    items = result.fetchall()
    print(f"  Parent items: {len(items)}")
    for item in items:
        print(f"    - {item.sku} ({item.id})")
    
    # Check move_history
    result = session.execute(
        text("""
            SELECT id, moved_at 
            FROM move_history 
            WHERE from_location_id = :loc_id OR to_location_id = :loc_id 
            LIMIT 5
        """),
        {"loc_id": location_id}
    )
    moves = result.fetchall()
    print(f"  Move history records: {len(moves)}")
    for move in moves:
        print(f"    - {move.id} at {move.moved_at}")
    
    # Try to delete
    print(f"\nAttempting to delete location...")
    try:
        session.execute(
            text("DELETE FROM locations WHERE id = :loc_id"),
            {"loc_id": location_id}
        )
        session.commit()
        print("  ✓ Successfully deleted!")
    except Exception as e:
        session.rollback()
        print(f"  ✗ Failed with error:")
        print(f"    {type(e).__name__}: {e}")
        
        # Parse the error to understand which constraint failed
        error_str = str(e)
        if "violates foreign key constraint" in error_str:
            print("\n  This is a foreign key constraint violation.")
            print("  The constraint name should be in the error above.")
    
    session.close()
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        test_deletion()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
