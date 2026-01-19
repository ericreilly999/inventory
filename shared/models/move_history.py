"""Move history model for tracking item movements."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, GUID


class MoveHistory(Base, UUIDMixin):
    """Move history model for tracking parent item movements."""
    
    __tablename__ = "move_history"
    
    moved_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    parent_item_id = Column(
        GUID(),
        ForeignKey("parent_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    from_location_id = Column(
        GUID(),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=True,  # Allow null for initial placement
        index=True
    )
    to_location_id = Column(
        GUID(),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    moved_by = Column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Relationships
    parent_item = relationship("ParentItem", back_populates="move_history")
    from_location = relationship(
        "Location", 
        back_populates="move_history_from",
        foreign_keys=[from_location_id]
    )
    to_location = relationship(
        "Location", 
        back_populates="move_history_to",
        foreign_keys=[to_location_id]
    )
    moved_by_user = relationship(
        "User", 
        back_populates="performed_moves",
        primaryjoin="MoveHistory.moved_by == User.id"
    )
    
    def __repr__(self) -> str:
        return f"<MoveHistory(id={self.id}, item='{self.parent_item.name if self.parent_item else None}', from='{self.from_location.name if self.from_location else None}', to='{self.to_location.name if self.to_location else None}', at='{self.moved_at}')>"