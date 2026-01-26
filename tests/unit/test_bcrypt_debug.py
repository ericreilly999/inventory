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


def test_database_round_trip():
    """Test hash storage and retrieval from database."""
    import uuid
    from datetime import datetime, timezone
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    
    from shared.models.base import Base
    from shared.models.user import Role, User
    
    # Create test database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create role
        admin_role = Role(
            id=uuid.uuid4(),
            name="admin",
            description="Administrator",
            permissions={"*": True},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(admin_role)
        db.commit()
        
        # Create user with hashed password
        password = "admin"
        hashed = hash_password(password)
        print(f"\nOriginal password: {password}")
        print(f"Hash before storing: {hashed}")
        print(f"Hash length: {len(hashed)}")
        
        admin = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            password_hash=hashed,
            active=True,
            role_id=admin_role.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        # Retrieve and verify
        retrieved_user = db.query(User).filter(User.username == "admin").first()
        print(f"Hash after retrieval: {retrieved_user.password_hash}")
        print(f"Hash length after retrieval: {len(retrieved_user.password_hash)}")
        print(f"Hashes match: {hashed == retrieved_user.password_hash}")
        
        # Verify password
        result = verify_password(password, retrieved_user.password_hash)
        print(f"Verify result: {result}")
        
        assert result is True
        
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
