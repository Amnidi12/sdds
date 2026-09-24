import enum
import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.mixins import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Warehouse(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "warehouses"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class InventoryBatch(Base, UUIDPKMixin, TimestampMixin):
    """
    A batch of stock derived from one donation, stored at one warehouse.
    quantity_available and quantity_reserved are kept consistent via
    transactional service-layer logic + a CHECK constraint as a hard backstop.
    """

    __tablename__ = "inventory_batches"
    __table_args__ = (
        CheckConstraint("quantity_available >= 0", name="ck_inventory_qty_available_nonneg"),
        CheckConstraint("quantity_reserved >= 0", name="ck_inventory_qty_reserved_nonneg"),
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donation_categories.id"), nullable=False
    )

    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class InventoryMovementType(str, enum.Enum):
    IN = "in"
    RESERVE = "reserve"
    RELEASE = "release"
    OUT = "out"
    ADJUSTMENT = "adjustment"


class InventoryMovement(Base, UUIDPKMixin, TimestampMixin):
    """Immutable ledger of every inventory change. Never updated or deleted."""

    __tablename__ = "inventory_movements"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    movement_type: Mapped[InventoryMovementType] = mapped_column(
        Enum(InventoryMovementType, name="inventory_movement_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)  # e.g. distribution id
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
