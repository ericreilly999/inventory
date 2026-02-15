#!/usr/bin/env python3
"""Test password hash verification."""

import bcrypt

# The hash from the migration
stored_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

# Test password
test_password = "admin"

print(f"Testing password: '{test_password}'")
print(f"Against hash: {stored_hash}")
print()

# Test with bcrypt directly
try:
    result = bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8'))
    print(f"✓ bcrypt.checkpw result: {result}")
except Exception as e:
    print(f"✗ bcrypt.checkpw error: {e}")

# Generate a new hash for comparison
print("\nGenerating new hash for 'admin':")
new_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
print(f"New hash: {new_hash.decode('utf-8')}")

# Test the new hash
result2 = bcrypt.checkpw(test_password.encode('utf-8'), new_hash)
print(f"New hash verification: {result2}")
