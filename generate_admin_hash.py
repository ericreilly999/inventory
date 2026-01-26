#!/usr/bin/env python3
"""Generate bcrypt hash for admin password."""

import bcrypt

password = "admin"
password_bytes = password.encode("utf-8")

# Use bcrypt directly with 12 rounds (same as our hash_password function)
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password_bytes, salt)
hashed_str = hashed.decode("utf-8")

print(f"Password: {password}")
print(f"Bcrypt hash: {hashed_str}")
print(f"\nVerifying hash works:")
print(f"Verification result: {bcrypt.checkpw(password_bytes, hashed)}")
print(f"\nUpdate the seed script with this hash:")
print(f"'{hashed_str}'")
