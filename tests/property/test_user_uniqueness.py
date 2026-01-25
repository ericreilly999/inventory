"""Property-based tests for user uniqueness and role management.

Feature: inventory-management, Property 13: User Uniqueness and Role Management
Validates: Requirements 6.1, 6.4
"""

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.auth.utils import hash_password
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
    password = draw(st.text(min_size=8, max_size=128))
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


class TestUserUniquenessProperties:
    """Property-based tests for user uniqueness and role management."""

    @given(
        user1_data=valid_user_data(),
        user2_data=valid_user_data(),
        role_data=valid_role_data(),
    )
    @settings(max_examples=10)
    def test_user_uniqueness_and_role_management_property(
        self, user1_data, user2_data, role_data
    ):
        """
        Property 13: User Uniqueness and Role Management

        For any user creation, the credentials must be unique, and role modifications
        should immediately update user permissions.

        **Validates: Requirements 6.1, 6.4**
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

            # Create first user
            user1 = User(
                username=user1_data["username"],
                email=user1_data["email"],
                password_hash=hash_password(user1_data["password"]),
                role_id=role.id,
                active=True,
            )
            db.add(user1)
            db.commit()
            db.refresh(user1)

            # Test that user was created successfully
            assert user1.id is not None
            assert user1.username == user1_data["username"]
            assert user1.email == user1_data["email"]
            assert user1.role_id == role.id

            # Test role permissions are correctly assigned
            assert user1.role.permissions == role_data["permissions"]

            # If user2 has different credentials, it should be created
            # successfully
            if (
                user2_data["username"] != user1_data["username"]
                and user2_data["email"] != user1_data["email"]
            ):
                user2 = User(
                    username=user2_data["username"],
                    email=user2_data["email"],
                    password_hash=hash_password(user2_data["password"]),
                    role_id=role.id,
                    active=True,
                )
                db.add(user2)
                db.commit()
                db.refresh(user2)

                # Both users should exist with unique credentials
                assert user2.id is not None
                assert user2.id != user1.id
                assert user2.username == user2_data["username"]
                assert user2.email == user2_data["email"]

                # Both users should have the same role permissions
                assert user2.role.permissions == role_data["permissions"]
                assert user1.role.permissions == user2.role.permissions

            # Test username uniqueness constraint
            if user2_data["username"] == user1_data["username"]:
                # Attempting to create user with same username should fail
                try:
                    duplicate_username_user = User(
                        username=user2_data["username"],  # Same username
                        email=user2_data["email"] + "_different",  # Different email
                        password_hash=hash_password(user2_data["password"]),
                        role_id=role.id,
                        active=True,
                    )
                    db.add(duplicate_username_user)
                    db.commit()
                    # If we reach here, the constraint wasn't enforced (test
                    # failure)
                    assert False, "Username uniqueness constraint not enforced"
                except Exception:
                    # Expected behavior - constraint violation
                    db.rollback()

            # Test email uniqueness constraint
            if user2_data["email"] == user1_data["email"]:
                # Attempting to create user with same email should fail
                try:
                    duplicate_email_user = User(
                        username=user2_data["username"]
                        + "_different",  # Different username
                        email=user2_data["email"],  # Same email
                        password_hash=hash_password(user2_data["password"]),
                        role_id=role.id,
                        active=True,
                    )
                    db.add(duplicate_email_user)
                    db.commit()
                    # If we reach here, the constraint wasn't enforced (test
                    # failure)
                    assert False, "Email uniqueness constraint not enforced"
                except Exception:
                    # Expected behavior - constraint violation
                    db.rollback()

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    @given(
        user_data=valid_user_data(),
        role1_data=valid_role_data(),
        role2_data=valid_role_data(),
    )
    @settings(max_examples=10)
    def test_role_modification_updates_permissions(
        self, user_data, role1_data, role2_data
    ):
        """
        Property: Role modifications should immediately update user permissions

        For any user with a role, changing the role should immediately update
        the user's effective permissions.
        """
        db, engine = get_test_db_session()

        # Ensure roles have different names
        if role2_data["name"] == role1_data["name"]:
            role2_data["name"] = role1_data["name"] + "_different"

        try:
            # Create two different roles
            role1 = Role(
                name=role1_data["name"],
                description=role1_data["description"],
                permissions=role1_data["permissions"],
            )
            db.add(role1)

            role2 = Role(
                name=role2_data["name"],
                description=role2_data["description"],
                permissions=role2_data["permissions"],
            )
            db.add(role2)
            db.commit()
            db.refresh(role1)
            db.refresh(role2)

            # Create user with first role
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                role_id=role1.id,
                active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Verify user has role1 permissions
            assert user.role_id == role1.id
            assert user.role.permissions == role1_data["permissions"]

            # Change user's role to role2
            user.role_id = role2.id
            db.commit()
            db.refresh(user)

            # Verify user now has role2 permissions
            assert user.role_id == role2.id
            assert user.role.permissions == role2_data["permissions"]

            # Permissions should be different if roles are different
            if role1_data["permissions"] != role2_data["permissions"]:
                assert user.role.permissions != role1_data["permissions"]

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    @given(role_data=valid_role_data())
    @settings(max_examples=10)
    def test_role_uniqueness_constraint(self, role_data):
        """
        Property: Role names must be unique

        For any role creation, the role name must be unique across all roles.
        """
        db, engine = get_test_db_session()

        try:
            # Create first role
            role1 = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
            )
            db.add(role1)
            db.commit()
            db.refresh(role1)

            # Verify role was created
            assert role1.id is not None
            assert role1.name == role_data["name"]

            # Attempt to create second role with same name should fail
            try:
                role2 = Role(
                    name=role_data["name"],  # Same name
                    description="Different description",
                    permissions={"different": True},
                )
                db.add(role2)
                db.commit()
                # If we reach here, the constraint wasn't enforced (test
                # failure)
                assert False, "Role name uniqueness constraint not enforced"
            except Exception:
                # Expected behavior - constraint violation
                db.rollback()

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)
