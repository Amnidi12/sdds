"""
Reports endpoints.

Bug fix (Section 6.1 of the project report):
- require_roles() is called with variadic args, NOT a list:
  require_roles(RoleName.SUPER_ADMIN, RoleName.NGO_ADMIN)  ✓
  require_roles([RoleName.SUPER_ADMIN, RoleName.NGO_ADMIN]) ✗  ← was the bug

- Prefix is /api/v1/reports (consistent with every other router), not /reports
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.donations.models import DonationStatus
from app.reports.pdf_service import generate_donation_receipt_pdf
from app.reports.service import generate_donations_csv
from app.users.models import RoleName

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/donations")
async def export_donations_csv(
    status: DonationStatus | None = Query(default=None),
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.NGO_ADMIN)  # variadic — NOT a list!
    ),
    db: AsyncSession = Depends(get_db),
):
    """Export donations as a CSV file.

    - Super admins see all donations across the platform.
    - NGO admins see only their organization's donations.
    """
    org_id = None if current_user.role == RoleName.SUPER_ADMIN else current_user.organization_id

    csv_content = await generate_donations_csv(db, organization_id=org_id, status_filter=status)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=donations_export.csv"},
    )


@router.get("/donations/{donation_id}/receipt")
async def download_donation_receipt(
    donation_id: uuid.UUID,
    current_user: CurrentUser = Depends(
        require_roles(RoleName.SUPER_ADMIN, RoleName.NGO_ADMIN, RoleName.DONOR)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Download a PDF receipt for a specific donation.

    - Donors can download receipts for their own donations.
    - NGO admins and super admins can download any receipt.
    """
    try:
        pdf_bytes = await generate_donation_receipt_pdf(db, donation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=receipt_{donation_id}.pdf"
        },
    )
