"""Check database constraints in staging."""

import psycopg2
import sys

# Staging database connection
DB_HOST = "staging-inventory-db.c47e2qi82sp6.us-east-1.rds.amazonaws.com"
DB_NAME = "inventory_management"
DB_USER = "inventory_user"
DB_PASSWORD = "InventoryDB2025!"

def check_constraints():
    """Check foreign key constraints on move_history table."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        print("=" * 70)
        print("Checking Foreign Key Constraints")
        print("=" * 70)
        
        # Check constraints on move_history table
        cursor.execute("""
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
                AND ccu.table_name = 'locations'
            ORDER BY tc.constraint_name;
        """)
        
        constraints = cursor.fetchall()
        
        if constraints:
            print("\nForeign key constraints on move_history -> locations:")
            print("-" * 70)
            for constraint in constraints:
                print(f"\nConstraint: {constraint[0]}")
                print(f"  Column: {constraint[2]}")
                print(f"  References: {constraint[3]}.{constraint[4]}")
                print(f"  On Delete: {constraint[5]}")
        else:
            print("\n✗ No foreign key constraints found!")
        
        # Check if there are any move_history records for Main Warehouse
        print("\n" + "=" * 70)
        print("Checking move_history records for 'Main Warehouse'")
        print("=" * 70)
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM move_history mh
            JOIN locations l ON (mh.from_location_id = l.id OR mh.to_location_id = l.id)
            WHERE l.name = 'Main Warehouse';
        """)
        
        count = cursor.fetchone()[0]
        print(f"\nMove history records referencing 'Main Warehouse': {count}")
        
        if count > 0:
            print("\n⚠ Location has historical movement data")
            print("With SET NULL constraints, these should not block deletion")
        else:
            print("\n✓ No movement history for this location")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    check_constraints()
