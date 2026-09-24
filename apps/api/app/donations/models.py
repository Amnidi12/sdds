import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, DateTime, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class DonationCategory(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "donation_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DonationStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PICKUP_SCHEDULED = "pickup_scheduled"
    PICKED_UP = "picked_up"
    RECEIVED_AT_WAREHOUSE = "received_at_warehouse"
    VERIFIED = "verified"
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    OUT_FOR_DISTRIBUTION = "out_for_distribution"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Explicit allowed state transitions - enforced in the service layer.
# This prevents arbitrary/invalid status jumps (requirement #11).
ALLOWED_DONATION_TRANSITIONS: dict[DonationStatus, set[DonationStatus]] = {
    DonationStatus.PENDING_REVIEW: {
        DonationStatus.APPROVED,
        DonationStatus.REJECTED,
        DonationStatus.CANCELLED,
    },
    DonationStatus.APPROVED: {DonationStatus.PICKUP_SCHEDULED, DonationStatus.CANCELLED},
    DonationStatus.PICKUP_SCHEDULED: {DonationStatus.PICKED_UP, DonationStatus.CANCELLED},
    DonationStatus.PICKED_UP: {DonationStatus.RECEIVED_AT_WAREHOUSE},
    DonationStatus.RECEIVED_AT_WAREHOUSE: {DonationStatus.VERIFIED},
    DonationStatus.VERIFIED: {DonationStatus.AVAILABLE},
    DonationStatus.AVAILABLE: {DonationStatus.ALLOCATED},
    DonationStatus.ALLOCATED: {DonationStatus.OUT_FOR_DISTRIBUTION, DonationStatus.AVAILABLE},
    DonationStatus.OUT_FOR_DISTRIBUTION: {DonationStatus.DELIVERED},
    DonationStatus.DELIVERED: {DonationStatus.COMPLETED},
    DonationStatus.COMPLETED: set(),
    DonationStatus.REJECTED: set(),
    DonationStatus.CANCELLED: set(),
}


class DonationCondition(str, enum.Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"


class Donation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "donations"

    tracking_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)

    donor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donation_categories.id"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="items")
    estimated_weight_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    condition: Mapped[DonationCondition] = mapped_column(
        Enum(DonationCondition, name="donation_condition", values_callable=lambda obj: [e.value for e in obj]), default=DonationCondition.GOOD
    )

    pickup_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pickup_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, name="donation_status", values_callable=lambda obj: [e.value for e in obj]),
        default=DonationStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped["DonationCategory"] = relationship()
    media: Mapped[list["DonationMedia"]] = relationship(
        back_populates="donation", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["DonationStatusHistory"]] = relationship(
        back_populates="donation", cascade="all, delete-orphan", order_by="DonationStatusHistory.created_at"
    )


class DonationMedia(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "donation_media"

    donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False
    )
    storage_key: Mapped[str] = mapped_column(
        String(500), nullable=False
    )  # randomized key, never original filename
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    donation: Mapped["Donation"] = relationship(back_populates="media")


class DonationStatusHistory(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "donation_status_history"

    donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[DonationStatus | None] = mapped_column(
        Enum(DonationStatus, name="donation_status", values_callable=lambda obj: [e.value for e in obj]), nullable=True
    )
    to_status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, name="donation_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    donation: Mapped["Donation"] = relationship(back_populates="status_history")
