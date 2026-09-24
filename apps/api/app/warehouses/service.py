"""
Inventory business logic. All quantity mutations happen inside a single DB
transaction using SELECT ... FOR UPDATE row locking, so concurrent requests
can never double-allocate the same stock (requirement #12).
"""

import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.core.deps import CurrentUser
from app.donations.models import Donation, DonationStatus
from app.donations.service import transition_donation_status
from app.warehouses.models import InventoryBatch, InventoryMovement, InventoryMovementType, Warehouse


async def receive_donation_into_inventory(
    db: AsyncSession,
    donation: Donation,
    warehouse_id: uuid.UUID,
    quantity: int,
    actor: CurrentUser,
    storage_location: str | None = None,
    expiry_date: date | None = None,
) -> InventoryBatch:
    """
    Called when warehouse staff verify a RECEIVED_AT_WAREHOUSE donation.
    Creates an inventory batch (IN movement) and transitions the donation
    through VERIFIED -> AVAILABLE.
    """
    if donation.status != DonationStatus.RECEIVED_AT_WAREHOUSE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Donation must be in 'received_at_warehouse' status to verify into inventory, currently '{donation.status.value}'",
        )

    warehouse = (await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    batch = InventoryBatch(
        warehouse_id=warehouse_id,
        donation_id=donation.id,
        category_id=donation.category_id,
        quantity_available=quantity,
        quantity_reserved=0,
        storage_location=storage_location,
        expiry_date=expiry_date,
    )
    db.add(batch)
    await db.flush()

    db.add(
        InventoryMovement(
            batch_id=batch.id,
            movement_type=InventoryMovementType.IN,
            quantity=quantity,
            actor_id=actor.id,
            reference=str(donation.id),
            note="Received and verified at warehouse",
        )
    )
    db.add(
        AuditLog(
            actor_id=actor.id,
            action="inventory.received",
            resource_type="inventory_batch",
            resource_id=str(batch.id),
            metadata_json={"donation_id": str(donation.id), "quantity": quantity},
        )
    )

    # Advance donation lifecycle: RECEIVED_AT_WAREHOUSE -> VERIFIED -> AVAILABLE
    await transition_donation_status(
        db, donation, DonationStatus.VERIFIED, actor, note="Verified at warehouse"
    )
    await transition_donation_status(
        db, donation, DonationStatus.AVAILABLE, actor, note="Added to available inventory"
    )

    await db.commit()
    await db.refresh(batch)
    return batch


async def reserve_stock(
    db: AsyncSession, batch_id: uuid.UUID, quantity: int, actor: CurrentUser, reference: str | None = None
) -> InventoryBatch:
    """Locks the batch row to prevent race conditions between concurrent reservations."""
    result = await db.execute(select(InventoryBatch).where(InventoryBatch.id == batch_id).with_for_update())
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")

    if batch.quantity_available < quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient stock: only {batch.quantity_available} available, requested {quantity}",
        )

    batch.quantity_available -= quantity
    batch.quantity_reserved += quantity

    db.add(
        InventoryMovement(
            batch_id=batch.id,
            movement_type=InventoryMovementType.RESERVE,
            quantity=quantity,
            actor_id=actor.id,
            reference=reference,
        )
    )
    await db.commit()
    await db.refresh(batch)
    return batch


async def release_stock(
    db: AsyncSession, batch_id: uuid.UUID, quantity: int, actor: CurrentUser, reference: str | None = None
) -> InventoryBatch:
    """Releases a reservation back to available (e.g. cancelled distribution)."""
    result = await db.execute(select(InventoryBatch).where(InventoryBatch.id == batch_id).with_for_update())
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")
    if batch.quantity_reserved < quantity:
        raise HTTPException(status_code=409, detail="Cannot release more than is currently reserved")

    batch.quantity_reserved -= quantity
    batch.quantity_available += quantity

    db.add(
        InventoryMovement(
            batch_id=batch.id,
            movement_type=InventoryMovementType.RELEASE,
            quantity=quantity,
            actor_id=actor.id,
            reference=reference,
        )
    )
    await db.commit()
    await db.refresh(batch)
    return batch


async def dispatch_stock(
    db: AsyncSession, batch_id: uuid.UUID, quantity: int, actor: CurrentUser, reference: str | None = None
) -> InventoryBatch:
    """Converts a reservation into a permanent OUT movement (goods have left the warehouse)."""
    result = await db.execute(select(InventoryBatch).where(InventoryBatch.id == batch_id).with_for_update())
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Inventory batch not found")
    if batch.quantity_reserved < quantity:
        raise HTTPException(status_code=409, detail="Cannot dispatch more than is currently reserved")

    batch.quantity_reserved -= quantity

    db.add(
        InventoryMovement(
            batch_id=batch.id,
            movement_type=InventoryMovementType.OUT,
            quantity=quantity,
            actor_id=actor.id,
            reference=reference,
        )
    )
    await db.commit()
    await db.refresh(batch)
    return batch


async def list_low_stock_batches(
    db: AsyncSession, organization_id: uuid.UUID, threshold: int = 5
) -> list[InventoryBatch]:
    result = await db.execute(
        select(InventoryBatch)
        .join(Warehouse, InventoryBatch.warehouse_id == Warehouse.id)
        .where(Warehouse.organization_id == organization_id, InventoryBatch.quantity_available <= threshold)
    )
    return list(result.scalars().all())


async def list_expiring_soon_batches(
    db: AsyncSession, organization_id: uuid.UUID, days: int = 7
) -> list[InventoryBatch]:
    cutoff = date.today() + timedelta(days=days)
    result = await db.execute(
        select(InventoryBatch)
        .join(Warehouse, InventoryBatch.warehouse_id == Warehouse.id)
        .where(
            Warehouse.organization_id == organization_id,
            InventoryBatch.expiry_date.is_not(None),
            InventoryBatch.expiry_date <= cutoff,
        )
    )
    return list(result.scalars().all())
