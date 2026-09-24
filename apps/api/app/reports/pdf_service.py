"""
PDF donation receipt generation using fpdf2.

Generates a clean, professional PDF receipt for a single donation,
suitable for donors who want a record for their own files.
"""

import io
import uuid
from datetime import datetime, timezone

from fpdf import FPDF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.donations.models import Donation, DonationCategory


class DonationReceiptPDF(FPDF):
    """Custom PDF class for donation receipts."""

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Smart Donation Distribution Tracker", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, "Donation Receipt", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", align="C")


async def generate_donation_receipt_pdf(
    db: AsyncSession,
    donation_id: uuid.UUID,
) -> bytes:
    """Generate a PDF receipt for a specific donation.

    Returns the PDF as bytes ready to be sent as a StreamingResponse.
    """
    result = await db.execute(
        select(Donation)
        .options(selectinload(Donation.category))
        .where(Donation.id == donation_id)
    )
    donation = result.scalar_one_or_none()
    if not donation:
        raise ValueError("Donation not found")

    pdf = DonationReceiptPDF()
    pdf.add_page()

    # Tracking ID prominently
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Tracking ID: {donation.tracking_id}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Donation details
    pdf.set_font("Helvetica", "", 11)
    details = [
        ("Title", donation.title),
        ("Category", donation.category.name if donation.category else "N/A"),
        ("Quantity", f"{donation.quantity} {donation.unit}"),
        ("Condition", donation.condition.value if hasattr(donation.condition, "value") else str(donation.condition)),
        ("Status", donation.status.value if hasattr(donation.status, "value") else str(donation.status)),
        ("Pickup Required", "Yes" if donation.pickup_required else "No"),
        ("Date Created", donation.created_at.strftime("%Y-%m-%d %H:%M UTC") if donation.created_at else "N/A"),
    ]

    if donation.estimated_weight_kg:
        details.append(("Estimated Weight", f"{donation.estimated_weight_kg} kg"))
    if donation.expiry_date:
        details.append(("Expiry Date", str(donation.expiry_date)))
    if donation.description:
        details.append(("Description", donation.description))

    for label, value in details:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(55, 8, f"{label}:")
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 8, str(value), new_x="LMARGIN", new_y="NEXT")

    # Divider
    pdf.ln(6)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Thank you note
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(
        0, 6,
        "Thank you for your generous donation. This receipt confirms that your "
        "donation has been registered in the Smart Donation Distribution Tracker. "
        "You can track the journey of your donation using the tracking ID above "
        "at any time.",
    )

    # QR code placeholder text
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Track online: /track/{donation.tracking_id}", align="C")

    # Return as bytes
    return pdf.output()
