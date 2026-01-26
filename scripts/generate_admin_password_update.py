#!/usr/bin/env python3
"""Generate SQL to update admin password with correct bcrypt hash."""

import bcrypt

password = "admin"
password_bytes = password.encode("utf-8")

# Use bcrypt directly with 12 rounds (same as our hash_password function)
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password_bytes, salt)
hashed_str = hashed.decode("utf-8")

print(f"-- Update admin user password with bcrypt hash")
print(f"-- Password: {password}")
print(f"-- Hash: {hashed_str}")
print(f"")
print(f"UPDATE users")
print(f"SET password_hash = '{hashed_str}',")
print(f"    updated_at = NOW()")
print(f"WHERE username = 'admin';")
print(f"")
print(f"SELECT 'Admin password updated successfully!' as message;")
print(f"SELECT 'Username: admin, Password: admin' as credentials;")
