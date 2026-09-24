import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.donations.service import get_donation_or_404
from app.organizations.models import Organization
from app.users.models import RoleName
from app.warehouses.models import InventoryBatch, Warehouse
from app.warehouses.schemas import (
    InventoryBatchOut,
    InventoryReceiveRequest,
    WarehouseCreate,
    WarehouseOut,
)
from app.warehouses.service import (
    dispatch_stock,
    list_expiring_soon_batches,
    list_low_stock_batches,
    receive_donation_into_inventory,
    release_stock,
    reserve_stock,
)

router = APIRouter(prefix="/api/v1/warehouses", tags=["warehouses"])
inventory_router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


@router.post("", response_model=WarehouseOut, status_code=201)
async def create_warehouse(
    payload: WarehouseCreate,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    if not org_id and current_user.role == RoleName.SUPER_ADMIN:
        org = await db.scalar(select(Organization).limit(1))
        if org:
            org_id = org.id
        else:
            raise HTTPException(
                status_code=400, detail="No organizations exist to assign this warehouse to"
            )
            
    if not org_id:
        raise HTTPException(
            status_code=400, detail="You must belong to an organization to create a warehouse"
        )
        
    warehouse = Warehouse(
        organization_id=org_id, name=payload.name, address=payload.address
    )
    db.add(warehouse)
    await db.commit()
    await db.refresh(warehouse)
    return warehouse


@router.get("", response_model=list[WarehouseOut])
async def list_warehouses(
    current_user: CurrentUser = Depends(
        require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN, RoleName.VOLUNTEER)
    ),
    db: AsyncSession = Depends(get_db),
):
    query = select(Warehouse)
    if current_user.role != RoleName.SUPER_ADMIN:
        query = query.where(Warehouse.organization_id == current_user.organization_id)
    result = await db.execute(query)
    return result.scalars().all()


@inventory_router.post("/receive/{donation_id}", response_model=InventoryBatchOut)
async def receive_donation(
    donation_id: uuid.UUID,
    payload: InventoryReceiveRequest,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    donation = await get_donation_or_404(db, donation_id)
    if current_user.role == RoleName.NGO_ADMIN and donation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Resource belongs to a different organization")

    return await receive_donation_into_inventory(
        db,
        donation,
        payload.warehouse_id,
        payload.quantity,
        current_user,
        storage_location=payload.storage_location,
        expiry_date=payload.expiry_date,
    )


@inventory_router.get("", response_model=list[InventoryBatchOut])
async def list_inventory(
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    query = select(InventoryBatch).join(Warehouse, InventoryBatch.warehouse_id == Warehouse.id)
    if current_user.role != RoleName.SUPER_ADMIN:
        query = query.where(Warehouse.organization_id == current_user.organization_id)
    result = await db.execute(query)
    return result.scalars().all()


@inventory_router.get("/alerts/low-stock", response_model=list[InventoryBatchOut])
async def low_stock_alerts(
    threshold: int = 5,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.organization_id:
        return []
    return await list_low_stock_batches(db, current_user.organization_id, threshold)


@inventory_router.get("/alerts/expiring-soon", response_model=list[InventoryBatchOut])
async def expiring_soon_alerts(
    days: int = 7,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.organization_id:
        return []
    return await list_expiring_soon_batches(db, current_user.organization_id, days)


@inventory_router.post("/{batch_id}/reserve", response_model=InventoryBatchOut)
async def reserve_inventory(
    batch_id: uuid.UUID,
    quantity: int,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await reserve_stock(db, batch_id, quantity, current_user)


@inventory_router.post("/{batch_id}/release", response_model=InventoryBatchOut)
async def release_inventory(
    batch_id: uuid.UUID,
    quantity: int,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await release_stock(db, batch_id, quantity, current_user)


@inventory_router.post("/{batch_id}/dispatch", response_model=InventoryBatchOut)
async def dispatch_inventory(
    batch_id: uuid.UUID,
    quantity: int,
    current_user: CurrentUser = Depends(require_roles(RoleName.NGO_ADMIN, RoleName.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await dispatch_stock(db, batch_id, quantity, current_user)
