"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- Enums ----
    role_name = pg.ENUM("super_admin", "ngo_admin", "donor", "volunteer", "beneficiary", name="role_name", create_type=False)
    donation_condition = pg.ENUM("new", "like_new", "good", "fair", name="donation_condition", create_type=False)
    donation_status = pg.ENUM(
        "pending_review", "approved", "rejected", "pickup_scheduled", "picked_up",
        "received_at_warehouse", "verified", "available", "allocated",
        "out_for_distribution", "delivered", "completed", "cancelled",
        name="donation_status", create_type=False,
    )
    inventory_movement_type = pg.ENUM("in", "reserve", "release", "out", "adjustment", name="inventory_movement_type", create_type=False)
    pickup_task_status = pg.ENUM("assigned", "accepted", "en_route", "arrived", "picked_up", "failed", "completed", name="pickup_task_status", create_type=False)
    distribution_status = pg.ENUM("created", "reserved", "dispatched", "delivered", "verified", "completed", "cancelled", name="distribution_status", create_type=False)
    request_status = pg.ENUM("submitted", "under_review", "approved", "fulfilled", "rejected", name="request_status", create_type=False)

    bind = op.get_bind()
    for enum in (role_name, donation_condition, donation_status, inventory_movement_type,
                 pickup_task_status, distribution_status, request_status):
        enum.create(bind, checkfirst=True)

    # ---- organizations ----
    op.create_table(
        "organizations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(220), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(320), nullable=True),
        sa.Column("contact_phone", sa.String(30), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("role", role_name, nullable=False),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ---- refresh_sessions / tokens ----
    op.create_table(
        "refresh_sessions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])

    for table_name in ("email_verification_tokens", "password_reset_tokens"):
        op.create_table(
            table_name,
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # ---- donation_categories ----
    op.create_table(
        "donation_categories",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ---- donations ----
    op.create_table(
        "donations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tracking_id", sa.String(30), nullable=False, unique=True),
        sa.Column("donor_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_id", pg.UUID(as_uuid=True), sa.ForeignKey("donation_categories.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(30), nullable=False, server_default="items"),
        sa.Column("estimated_weight_kg", sa.Numeric(10, 2), nullable=True),
        sa.Column("condition", donation_condition, nullable=False, server_default="good"),
        sa.Column("pickup_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("pickup_address", sa.Text(), nullable=True),
        sa.Column("preferred_pickup_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", donation_status, nullable=False, server_default="pending_review"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_donations_tracking_id", "donations", ["tracking_id"])
    op.create_index("ix_donations_donor_id", "donations", ["donor_id"])
    op.create_index("ix_donations_organization_id", "donations", ["organization_id"])
    op.create_index("ix_donations_status", "donations", ["status"])

    op.create_table(
        "donation_media",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("donation_id", pg.UUID(as_uuid=True), sa.ForeignKey("donations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "donation_status_history",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("donation_id", pg.UUID(as_uuid=True), sa.ForeignKey("donations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", donation_status, nullable=True),
        sa.Column("to_status", donation_status, nullable=False),
        sa.Column("actor_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_donation_status_history_donation_id", "donation_status_history", ["donation_id"])

    # ---- warehouses / inventory ----
    op.create_table(
        "warehouses",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_warehouses_organization_id", "warehouses", ["organization_id"])

    op.create_table(
        "inventory_batches",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("warehouse_id", pg.UUID(as_uuid=True), sa.ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("donation_id", pg.UUID(as_uuid=True), sa.ForeignKey("donations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", pg.UUID(as_uuid=True), sa.ForeignKey("donation_categories.id"), nullable=False),
        sa.Column("quantity_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_location", sa.String(100), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity_available >= 0", name="ck_inventory_qty_available_nonneg"),
        sa.CheckConstraint("quantity_reserved >= 0", name="ck_inventory_qty_reserved_nonneg"),
    )
    op.create_index("ix_inventory_batches_warehouse_id", "inventory_batches", ["warehouse_id"])
    op.create_index("ix_inventory_batches_donation_id", "inventory_batches", ["donation_id"])

    op.create_table(
        "inventory_movements",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", pg.UUID(as_uuid=True), sa.ForeignKey("inventory_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_type", inventory_movement_type, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("actor_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reference", sa.String(200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_inventory_movements_batch_id", "inventory_movements", ["batch_id"])

    # ---- beneficiaries ----
    op.create_table(
        "beneficiaries",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("household_size", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_beneficiaries_organization_id", "beneficiaries", ["organization_id"])

    op.create_table(
        "beneficiary_requests",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("beneficiary_id", pg.UUID(as_uuid=True), sa.ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", pg.UUID(as_uuid=True), sa.ForeignKey("donation_categories.id"), nullable=False),
        sa.Column("quantity_requested", sa.Integer(), nullable=False),
        sa.Column("status", request_status, nullable=False, server_default="submitted"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_beneficiary_requests_beneficiary_id", "beneficiary_requests", ["beneficiary_id"])

    # ---- pickup tasks ----
    op.create_table(
        "pickup_tasks",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("donation_id", pg.UUID(as_uuid=True), sa.ForeignKey("donations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("volunteer_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", pickup_task_status, nullable=False, server_default="assigned"),
        sa.Column("evidence_storage_key", sa.String(500), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pickup_tasks_donation_id", "pickup_tasks", ["donation_id"])
    op.create_index("ix_pickup_tasks_volunteer_id", "pickup_tasks", ["volunteer_id"])

    # ---- distributions ----
    op.create_table(
        "distributions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("beneficiary_id", pg.UUID(as_uuid=True), sa.ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_id", pg.UUID(as_uuid=True), sa.ForeignKey("beneficiary_requests.id"), nullable=True),
        sa.Column("volunteer_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", distribution_status, nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_distributions_organization_id", "distributions", ["organization_id"])
    op.create_index("ix_distributions_beneficiary_id", "distributions", ["beneficiary_id"])

    op.create_table(
        "distribution_items",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("distribution_id", pg.UUID(as_uuid=True), sa.ForeignKey("distributions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inventory_batch_id", pg.UUID(as_uuid=True), sa.ForeignKey("inventory_batches.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "delivery_proofs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("distribution_id", pg.UUID(as_uuid=True), sa.ForeignKey("distributions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("recipient_confirmation_name", sa.String(200), nullable=True),
        sa.Column("photo_storage_key", sa.String(500), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ---- audit / notifications ----
    op.create_table(
        "audit_logs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("metadata_json", sa.JSON().with_variant(pg.JSONB(), "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("link", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("delivery_proofs")
    op.drop_table("distribution_items")
    op.drop_table("distributions")
    op.drop_table("pickup_tasks")
    op.drop_table("beneficiary_requests")
    op.drop_table("beneficiaries")
    op.drop_table("inventory_movements")
    op.drop_table("inventory_batches")
    op.drop_table("warehouses")
    op.drop_table("donation_status_history")
    op.drop_table("donation_media")
    op.drop_table("donations")
    op.drop_table("donation_categories")
    op.drop_table("password_reset_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_table("refresh_sessions")
    op.drop_table("users")
    op.drop_table("organizations")

    bind = op.get_bind()
    for enum_name in ("request_status", "distribution_status", "pickup_task_status",
                       "inventory_movement_type", "donation_status", "donation_condition", "role_name"):
        pg.ENUM(name=enum_name).drop(bind, checkfirst=True)
