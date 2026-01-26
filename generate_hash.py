"""Generate a bcrypt hash for the admin password."""

import bcrypt as bcrypt_lib

password = "admin"
password_bytes = password.encode("utf-8")

# Use bcrypt directly with 12 rounds (same as our function)
salt = bcrypt_lib.gensalt(rounds=12)
hashed = bcrypt_lib.hashpw(password_bytes, salt)
hashed_str = hashed.decode("utf-8")

print(f"Password: {password}")
print(f"Hash: {hashed_str}")
print(f"\nUse this hash in scripts/seed_admin_user.sql")
