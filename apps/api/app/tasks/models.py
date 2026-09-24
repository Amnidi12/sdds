import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class PickupTaskStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    PICKED_UP = "picked_up"
    FAILED = "failed"
    COMPLETED = "completed"


ALLOWED_PICKUP_TRANSITIONS: dict[PickupTaskStatus, set[PickupTaskStatus]] = {
    PickupTaskStatus.ASSIGNED: {PickupTaskStatus.ACCEPTED, PickupTaskStatus.FAILED},
    PickupTaskStatus.ACCEPTED: {PickupTaskStatus.EN_ROUTE, PickupTaskStatus.FAILED},
    PickupTaskStatus.EN_ROUTE: {PickupTaskStatus.ARRIVED, PickupTaskStatus.FAILED},
    PickupTaskStatus.ARRIVED: {PickupTaskStatus.PICKED_UP, PickupTaskStatus.FAILED},
    PickupTaskStatus.PICKED_UP: {PickupTaskStatus.COMPLETED},
    PickupTaskStatus.COMPLETED: set(),
    PickupTaskStatus.FAILED: set(),
}


class PickupTask(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "pickup_tasks"

    donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    volunteer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PickupTaskStatus] = mapped_column(
        Enum(PickupTaskStatus, name="pickup_task_status", values_callable=lambda obj: [e.value for e in obj]), default=PickupTaskStatus.ASSIGNED, nullable=False
    )
    evidence_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class DistributionStatus(str, enum.Enum):
    CREATED = "created"
    RESERVED = "reserved"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    VERIFIED = "verified"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


ALLOWED_DISTRIBUTION_TRANSITIONS: dict[DistributionStatus, set[DistributionStatus]] = {
    DistributionStatus.CREATED: {DistributionStatus.RESERVED, DistributionStatus.CANCELLED},
    DistributionStatus.RESERVED: {DistributionStatus.DISPATCHED, DistributionStatus.CANCELLED},
    DistributionStatus.DISPATCHED: {DistributionStatus.DELIVERED},
    DistributionStatus.DELIVERED: {DistributionStatus.VERIFIED},
    DistributionStatus.VERIFIED: {DistributionStatus.COMPLETED},
    DistributionStatus.COMPLETED: set(),
    DistributionStatus.CANCELLED: set(),
}


class Distribution(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "distributions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    beneficiary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("beneficiary_requests.id"), nullable=True
    )
    volunteer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[DistributionStatus] = mapped_column(
        Enum(DistributionStatus, name="distribution_status", values_callable=lambda obj: [e.value for e in obj]),
        default=DistributionStatus.CREATED,
        nullable=False,
    )

    items: Mapped[list["DistributionItem"]] = relationship(
        back_populates="distribution", cascade="all, delete-orphan"
    )
    proof: Mapped["DeliveryProof"] = relationship(
        back_populates="distribution", uselist=False, cascade="all, delete-orphan"
    )


class DistributionItem(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "distribution_items"

    distribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("distributions.id", ondelete="CASCADE"), nullable=False
    )
    inventory_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_batches.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    distribution: Mapped["Distribution"] = relationship(back_populates="items")


class DeliveryProof(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "delivery_proofs"

    distribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("distributions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    recipient_confirmation_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    photo_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    distribution: Mapped["Distribution"] = relationship(back_populates="proof")
