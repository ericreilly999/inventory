"""Assignment history model for tracking child item assignments."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, GUID


class AssignmentHistory(Base, UUIDMixin, TimestampMixin):
    """Assignment history model for tracking child item assignments to parent items."""
    
    __tablename__ = "assignment_history"
    
    assigned_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    child_item_id = Column(
        GUID(),
        ForeignKey("child_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    from_parent_item_id = Column(
        GUID(),
        ForeignKey("parent_items.id", ondelete="RESTRICT"),
        nullable=True,  # Allow null for initial assignment
        index=True
    )
    to_parent_item_id = Column(
        GUID(),
        ForeignKey("parent_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    assigned_by = Column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Relationships
    child_item = relationship("ChildItem", back_populates="assignment_history")
    from_parent_item = relationship(
        "ParentItem", 
        back_populates="assignment_history_from",
        foreign_keys=[from_parent_item_id]
    )
    to_parent_item = relationship(
        "ParentItem", 
        back_populates="assignment_history_to",
        foreign_keys=[to_parent_item_id]
    )
    assigned_by_user = relationship(
        "User", 
        back_populates="performed_assignments",
        primaryjoin="AssignmentHistory.assigned_by == User.id"
    )
    
    def __repr__(self) -> str:
        return f"<AssignmentHistory(id={self.id}, child_item='{self.child_item.name if self.child_item else None}', from='{self.from_parent_item.name if self.from_parent_item else None}', to='{self.to_parent_item.name if self.to_parent_item else None}', at='{self.assigned_at}')>"