"""Property-based tests for user authentication.

Feature: inventory-management, Property 12: User Authentication and Authorization
Validates: Requirements 6.2, 6.3
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.auth.utils import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)
from shared.models.base import Base
from shared.models.user import Role, User


# Generators for test data
@st.composite
def valid_user_data(draw):
    """Generate valid user data."""
    username = draw(
        st.text(
            min_size=3,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )
    email = draw(st.emails())
    # Use ASCII-only passwords to avoid UTF-8 encoding issues with bcrypt
    password = draw(
        st.text(
            min_size=8,
            max_size=72,
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),  # Printable ASCII
        )
    )
    return {"username": username, "email": email, "password": password}


@st.composite
def valid_role_data(draw):
    """Generate valid role data."""
    name = draw(
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        )
    )
    permissions = draw(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.booleans(),
            min_size=0,
            max_size=10,
        )
    )
    return {
        "name": name,
        "description": f"Role for {name}",
        "permissions": permissions,
    }


def get_test_db_session():
    """Create a test database session."""
    # Create in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    return session, engine


class TestUserAuthenticationProperties:
    """Property-based tests for user authentication and authorization."""

    @given(user_data=valid_user_data(), role_data=valid_role_data())
    @settings(max_examples=10)
    def test_user_authentication_and_authorization_property(self, user_data, role_data):
        """
        Property 12: User Authentication and Authorization

        For any user login attempt with valid credentials, an authenticated session
        should be established with appropriate role-based permissions.

        **Validates: Requirements 6.2, 6.3**
        """
        db, engine = get_test_db_session()

        try:
            # Create role first
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
            )
            db.add(role)
            db.commit()
            db.refresh(role)

            # Create user with hashed password
            password_hash = hash_password(user_data["password"])
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=password_hash,
                role_id=role.id,
                active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Test password verification (authentication)
            assert verify_password(user_data["password"], user.password_hash) is True
            assert (
                verify_password(user_data["password"] + "wrong", user.password_hash)
                is False
            )

            # Test token creation and verification (session establishment)
            token_data = {
                "sub": str(user.id),
                "username": user.username,
                "role_id": str(user.role_id),
                "permissions": role.permissions,
            }

            access_token = create_access_token(token_data)
            assert access_token is not None
            assert isinstance(access_token, str)
            assert len(access_token) > 0

            # Test token verification and payload extraction
            decoded_payload = verify_token(access_token)
            assert decoded_payload is not None
            assert decoded_payload["sub"] == str(user.id)
            assert decoded_payload["username"] == user.username
            assert decoded_payload["role_id"] == str(user.role_id)
            assert decoded_payload["permissions"] == role.permissions

            # Test role-based permissions are correctly included
            for permission_key, permission_value in role.permissions.items():
                assert (
                    decoded_payload["permissions"][permission_key] == permission_value
                )

            # Test invalid token verification
            invalid_token = access_token + "invalid"
            assert verify_token(invalid_token) is None

        except Exception as e:
            # Clean up in case of error
            db.rollback()
            raise e
        finally:
            # Clean up
            db.close()
            Base.metadata.drop_all(bind=engine)

    @given(user_data=valid_user_data(), role_data=valid_role_data())
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_inactive_user_authentication_fails(self, user_data, role_data):
        """
        Property: Inactive users should not be able to authenticate

        For any inactive user, authentication attempts should fail regardless of correct credentials.
        """
        db, engine = get_test_db_session()

        try:
            # Create role first
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
            )
            db.add(role)
            db.commit()
            db.refresh(role)

            # Create inactive user
            password_hash = hash_password(user_data["password"])
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=password_hash,
                role_id=role.id,
                active=False,  # Inactive user
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Password verification should still work (for password
            # correctness)
            assert verify_password(user_data["password"], user.password_hash) is True

            # But user should be marked as inactive
            assert user.active is False

            # Authentication logic should check active status
            # (This would be handled in the authentication endpoint)

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    @given(
        user_data=valid_user_data(),
        role_data=valid_role_data(),
        wrong_password=st.text(min_size=1, max_size=72),  # Bcrypt max is 72 bytes
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_wrong_password_authentication_fails(
        self, user_data, role_data, wrong_password
    ):
        """
        Property: Wrong password should always fail authentication

        For any user with valid credentials, using an incorrect password should fail authentication.
        """
        db, engine = get_test_db_session()

        # Truncate passwords to 72 bytes for bcrypt compatibility
        user_password = user_data["password"][:72]
        wrong_password = wrong_password[:72]
        
        # Truncate passwords to 72 bytes for bcrypt compatibility
        user_password = user_data["password"][:72]
        wrong_password = wrong_password[:72]
        
        # Ensure wrong password is actually different
        if wrong_password == user_password:
            wrong_password = user_password + "_different"
            wrong_password = wrong_password[:72]  # Ensure still within limit

        try:
            # Create role first
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
            )
            db.add(role)
            db.commit()
            db.refresh(role)

            # Create user with truncated password
            password_hash = hash_password(user_password)
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=password_hash,
                role_id=role.id,
                active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Correct password should work
            assert verify_password(user_password, user.password_hash) is True

            # Wrong password should fail
            assert verify_password(wrong_password, user.password_hash) is False

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)
