"""Location and LocationType models."""

from sqlalchemy import JSON, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import GUID, Base, TimestampMixin, UUIDMixin


class LocationType(Base, UUIDMixin, TimestampMixin):
    """Location type model for categorizing locations."""

    __tablename__ = "location_types"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Relationships
    locations = relationship("Location", back_populates="location_type")

    def __repr__(self) -> str:
        return f"<LocationType(id={self.id}, name='{self.name}')>"


class Location(Base, UUIDMixin, TimestampMixin):
    """Location model for physical storage places."""

    __tablename__ = "locations"

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location_metadata = Column(JSON, nullable=True, default=dict)

    # Foreign keys
    location_type_id = Column(
        GUID(),
        ForeignKey("location_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Relationships
    location_type = relationship("LocationType", back_populates="locations")
    parent_items = relationship(
        "ParentItem",
        back_populates="current_location",
        foreign_keys="ParentItem.current_location_id",
    )
    move_history_from = relationship(
        "MoveHistory",
        back_populates="from_location",
        foreign_keys="MoveHistory.from_location_id",
    )
    move_history_to = relationship(
        "MoveHistory",
        back_populates="to_location",
        foreign_keys="MoveHistory.to_location_id",
    )

    def __repr__(self) -> str:
        return f"<Location(id={
            self.id}, name='{
            self.name}', type='{
            self.location_type.name if self.location_type else None}')>"
