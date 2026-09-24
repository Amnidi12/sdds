"""
Reports service — CSV export and data aggregation for reports.
"""

import csv
import io
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.donations.models import Donation, DonationCategory, DonationStatus
from app.warehouses.models import Warehouse


async def generate_donations_csv(
    db: AsyncSession,
    organization_id: uuid.UUID | None = None,
    status_filter: DonationStatus | None = None,
) -> str:
    """Generate a CSV string of donations, optionally filtered by org and status.

    If organization_id is None (super admin), all donations are included.
    """
    query = (
        select(
            Donation.tracking_id,
            Donation.title,
            Donation.quantity,
            Donation.unit,
            Donation.status,
            Donation.condition,
            Donation.pickup_required,
            Donation.created_at,
            Donation.updated_at,
            DonationCategory.name.label("category_name"),
        )
        .outerjoin(DonationCategory, Donation.category_id == DonationCategory.id)
    )

    if organization_id:
        query = query.where(Donation.organization_id == organization_id)
    if status_filter:
        query = query.where(Donation.status == status_filter)

    query = query.order_by(Donation.created_at.desc())
    result = await db.execute(query)
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Tracking ID",
        "Title",
        "Category",
        "Quantity",
        "Unit",
        "Condition",
        "Status",
        "Pickup Required",
        "Created At",
        "Updated At",
    ])

    # Data rows
    for row in rows:
        writer.writerow([
            row.tracking_id,
            row.title,
            row.category_name or "Uncategorized",
            row.quantity,
            row.unit,
            row.condition.value if hasattr(row.condition, "value") else str(row.condition),
            row.status.value if hasattr(row.status, "value") else str(row.status),
            "Yes" if row.pickup_required else "No",
            row.created_at.isoformat() if row.created_at else "",
            row.updated_at.isoformat() if row.updated_at else "",
        ])

    return output.getvalue()
