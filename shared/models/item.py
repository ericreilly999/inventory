"""Item models for parent items, child items, and item types."""

import enum

from sqlalchemy import Column, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import GUID, AuditMixin, Base, TimestampMixin, UUIDMixin


class ItemCategory(enum.Enum):
    """Enumeration for item categories."""

    PARENT = "parent"
    CHILD = "child"


class ItemType(Base, UUIDMixin, TimestampMixin):
    """Item type model for categorizing items."""

    __tablename__ = "item_types"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(Enum(ItemCategory), nullable=False, index=True)

    # Relationships
    parent_items = relationship("ParentItem", back_populates="item_type")
    child_items = relationship("ChildItem", back_populates="item_type")

    def __repr__(self) -> str:
        return f"<ItemType(id={self.id}, name='{self.name}', category='{self.category.value}')>"


class ParentItem(Base, UUIDMixin, TimestampMixin):
    """Parent item model for movable inventory items."""

    __tablename__ = "parent_items"

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Foreign keys
    item_type_id = Column(
        GUID(),
        ForeignKey("item_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    current_location_id = Column(
        GUID(),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by = Column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    item_type = relationship("ItemType", back_populates="parent_items")
    current_location = relationship(
        "Location",
        back_populates="parent_items",
        foreign_keys=[current_location_id],
    )
    child_items = relationship(
        "ChildItem", back_populates="parent_item", cascade="all, delete-orphan"
    )
    move_history = relationship(
        "MoveHistory",
        back_populates="parent_item",
        cascade="all, delete-orphan",
    )
    assignment_history_from = relationship(
        "AssignmentHistory",
        back_populates="from_parent_item",
        foreign_keys="AssignmentHistory.from_parent_item_id",
    )
    assignment_history_to = relationship(
        "AssignmentHistory",
        back_populates="to_parent_item",
        foreign_keys="AssignmentHistory.to_parent_item_id",
    )
    creator = relationship(
        "User",
        back_populates="created_parent_items",
        primaryjoin="ParentItem.created_by == User.id",
    )

    def __repr__(self) -> str:
        return f"<ParentItem(id={self.id}, name='{self.name}', location='{self.current_location.name if self.current_location else None}')>"


class ChildItem(Base, UUIDMixin, TimestampMixin):
    """Child item model for items assigned to parent items."""

    __tablename__ = "child_items"

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Foreign keys
    item_type_id = Column(
        GUID(),
        ForeignKey("item_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    parent_item_id = Column(
        GUID(),
        ForeignKey("parent_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by = Column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    item_type = relationship("ItemType", back_populates="child_items")
    parent_item = relationship("ParentItem", back_populates="child_items")
    assignment_history = relationship(
        "AssignmentHistory",
        back_populates="child_item",
        cascade="all, delete-orphan",
    )
    creator = relationship(
        "User",
        back_populates="created_child_items",
        primaryjoin="ChildItem.created_by == User.id",
    )

    def __repr__(self) -> str:
        return f"<ChildItem(id={self.id}, name='{self.name}', parent='{self.parent_item.name if self.parent_item else None}')>"
