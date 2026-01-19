"""User and Role models."""

from sqlalchemy import Boolean, Column, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin, GUID


class Role(Base, UUIDMixin, TimestampMixin):
    """Role model for user permissions."""
    
    __tablename__ = "roles"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Foreign keys
    role_id = Column(
        GUID(),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Relationships
    role = relationship("Role", back_populates="users")
    created_parent_items = relationship(
        "ParentItem", 
        back_populates="creator",
        primaryjoin="User.id == ParentItem.created_by"
    )
    created_child_items = relationship(
        "ChildItem", 
        back_populates="creator",
        primaryjoin="User.id == ChildItem.created_by"
    )
    performed_moves = relationship(
        "MoveHistory", 
        back_populates="moved_by_user",
        primaryjoin="User.id == MoveHistory.moved_by"
    )
    performed_assignments = relationship(
        "AssignmentHistory", 
        back_populates="assigned_by_user",
        primaryjoin="User.id == AssignmentHistory.assigned_by"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"