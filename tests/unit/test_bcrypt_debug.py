"""Debug test for bcrypt hash/verify cycle."""

import bcrypt as bcrypt_lib

from shared.auth.utils import hash_password, verify_password


def test_bcrypt_direct():
    """Test bcrypt directly without any wrappers."""
    password = "admin"
    password_bytes = password.encode("utf-8")
    
    # Hash directly
    salt = bcrypt_lib.gensalt(rounds=12)
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    hashed_str = hashed.decode("utf-8")
    
    print(f"\nPassword: {password}")
    print(f"Hash: {hashed_str}")
    print(f"Hash length: {len(hashed_str)}")
    
    # Verify directly
    result = bcrypt_lib.checkpw(password_bytes, hashed)
    print(f"Direct verify result: {result}")
    
    assert result is True


def test_hash_password_function():
    """Test our hash_password function."""
    password = "admin"
    hashed = hash_password(password)
    
    print(f"\nPassword: {password}")
    print(f"Hash from function: {hashed}")
    print(f"Hash length: {len(hashed)}")
    print(f"Hash starts with: {hashed[:7]}")
    
    # Verify the hash is valid bcrypt format
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")
    assert len(hashed) == 60  # Standard bcrypt hash length


def test_verify_password_function():
    """Test our verify_password function."""
    password = "admin"
    hashed = hash_password(password)
    
    print(f"\nPassword: {password}")
    print(f"Hash: {hashed}")
    
    # Verify with correct password
    result = verify_password(password, hashed)
    print(f"Verify result: {result}")
    
    assert result is True


def test_hash_and_verify_cycle():
    """Test complete hash and verify cycle."""
    password = "admin"
    
    # Hash the password
    hashed = hash_password(password)
    print(f"\nOriginal password: {password}")
    print(f"Hashed: {hashed}")
    
    # Verify with correct password
    result_correct = verify_password(password, hashed)
    print(f"Verify with correct password: {result_correct}")
    assert result_correct is True
    
    # Verify with incorrect password
    result_incorrect = verify_password("wrong", hashed)
    print(f"Verify with incorrect password: {result_incorrect}")
    assert result_incorrect is False


def test_multiple_hashes():
    """Test that multiple hashes of same password all verify correctly."""
    password = "admin"
    
    # Create 3 different hashes
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    hash3 = hash_password(password)
    
    print(f"\nPassword: {password}")
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")
    
    # All should be different (different salts)
    assert hash1 != hash2
    assert hash2 != hash3
    assert hash1 != hash3
    
    # But all should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
    assert verify_password(password, hash3) is True


def test_known_hash():
    """Test with the known hash from seed script."""
    password = "admin"
    # This is the hash from scripts/seed_admin_user.sql
    known_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2xN7qhV/7e"
    
    print(f"\nPassword: {password}")
    print(f"Known hash: {known_hash}")
    
    # Verify with known hash
    result = verify_password(password, known_hash)
    print(f"Verify result: {result}")
    
    assert result is True
