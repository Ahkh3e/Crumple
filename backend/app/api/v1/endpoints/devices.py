from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.exc import SQLAlchemyError

from ....core.database import get_db
from ....models import dcim
from ....schemas import dcim as schemas
from ....core.exceptions import DatabaseError

router = APIRouter()

@router.post("/types/", response_model=schemas.DeviceType, status_code=status.HTTP_201_CREATED)
async def create_device_type(
    device_type: schemas.DeviceTypeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device type with interfaces"""
    try:
        # Create device type
        db_device_type = dcim.DeviceType(
            name=device_type.name,
            manufacturer=device_type.manufacturer,
            model=device_type.model,
            part_number=device_type.part_number,
            u_height=device_type.u_height,
            is_full_depth=device_type.is_full_depth
        )
        db.add(db_device_type)
        await db.flush()  # Get ID without committing

        # Create interface types if they don't exist
        interface_types = {}
        for interface in device_type.interfaces:
            if interface.type not in interface_types:
                stmt = select(dcim.InterfaceType).where(
                    dcim.InterfaceType.name == interface.type
                )
                result = await db.execute(stmt)
                db_interface_type = result.scalar_one_or_none()
                
                if not db_interface_type:
                    db_interface_type = dcim.InterfaceType(
                        name=interface.type,
                        speed=interface.speed,
                        connector_type=interface.type,
                        media_type='fiber' if interface.type in ['qsfp28', 'sfp_plus'] else 'copper'
                    )
                    db.add(db_interface_type)
                    await db.flush()
                
                interface_types[interface.type] = db_interface_type

            # Create interface
            db_interface = dcim.Interface(
                name=interface.name,
                device_type_id=db_device_type.id,
                interface_type_id=interface_types[interface.type].id,
                position=interface.position,
                enabled=1
            )
            db.add(db_interface)

        await db.commit()
        await db.refresh(db_device_type)
        return db_device_type
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/types/", response_model=List[schemas.DeviceType])
async def list_device_types(
    db: AsyncSession = Depends(get_db)
):
    """List all device types"""
    stmt = select(dcim.DeviceType)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/types/{device_type_id}", response_model=schemas.DeviceType)
async def get_device_type(
    device_type_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific device type"""
    stmt = select(dcim.DeviceType).where(dcim.DeviceType.id == device_type_id)
    result = await db.execute(stmt)
    device_type = result.scalar_one_or_none()
    if not device_type:
        raise HTTPException(status_code=404, detail="Device type not found")
    return device_type

@router.delete("/types/{device_type_id}")
async def delete_device_type(
    device_type_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a device type"""
    stmt = select(dcim.DeviceType).where(dcim.DeviceType.id == device_type_id)
    result = await db.execute(stmt)
    device_type = result.scalar_one_or_none()
    if not device_type:
        raise HTTPException(status_code=404, detail="Device type not found")
    
    # Delete associated interfaces
    stmt = select(dcim.Interface).where(dcim.Interface.device_type_id == device_type_id)
    result = await db.execute(stmt)
    interfaces = result.scalars().all()
    for interface in interfaces:
        await db.delete(interface)
    
    await db.delete(device_type)
    await db.commit()
    return {"message": "Device type deleted"}

@router.post("/", response_model=schemas.Device, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: schemas.DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device instance"""
    try:
        # Verify device type exists
        stmt = select(dcim.DeviceType).where(dcim.DeviceType.id == device.device_type_id)
        result = await db.execute(stmt)
        device_type = result.scalar_one_or_none()
        if not device_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device type not found"
            )

        # Create device
        db_device = dcim.Device(**device.dict())
        db.add(db_device)
        await db.flush()

        # Create interfaces based on device type
        for interface_type in device_type.interface_types:
            db_interface = dcim.Interface(
                name=f"{interface_type.name}0",
                device_id=db_device.id,
                interface_type_id=interface_type.id,
                enabled=1
            )
            db.add(db_interface)

        await db.commit()
        await db.refresh(db_device)
        return db_device
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/", response_model=List[schemas.Device])
async def list_devices(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all devices with optional filtering"""
    stmt = select(dcim.Device)
    
    if category:
        stmt = stmt.join(dcim.DeviceType).where(dcim.DeviceType.category == category)
    
    if search:
        search = f"%{search}%"
        stmt = stmt.join(dcim.DeviceType).where(
            or_(
                dcim.Device.name.ilike(search),
                dcim.DeviceType.name.ilike(search),
                dcim.DeviceType.manufacturer.ilike(search)
            )
        )
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/place", response_model=schemas.Device)
async def place_device(
    placement: schemas.DevicePlacement,
    db: AsyncSession = Depends(get_db)
):
    """Place a new device instance in a cluster"""
    # Verify device type exists
    stmt = select(dcim.DeviceType).where(dcim.DeviceType.id == placement.device_type_id)
    result = await db.execute(stmt)
    device_type = result.scalar_one_or_none()
    if not device_type:
        raise HTTPException(status_code=404, detail="Device type not found")
    
    # Generate device name if not provided
    if not placement.name:
        # Count existing devices of this type
        stmt = select(dcim.Device).join(dcim.DeviceType).where(
            dcim.DeviceType.category == device_type.category
        )
        result = await db.execute(stmt)
        count = len(result.scalars().all())
        placement.name = f"{device_type.category.upper()}{count + 1}"
    
    # Create device
    db_device = dcim.Device(
        name=placement.name,
        device_type_id=placement.device_type_id,
        position_x=placement.position_x,
        position_y=placement.position_y,
        cluster_id=placement.cluster_id
    )
    db.add(db_device)
    await db.flush()
    
    # Create interfaces based on device type
    for interface_type in device_type.interface_types:
        db_interface = dcim.Interface(
            name=f"{interface_type.name}0",
            device_id=db_device.id,
            interface_type_id=interface_type.id,
            enabled=1,
            position="front"  # Default position, can be updated later
        )
        db.add(db_interface)
    
    await db.commit()
    await db.refresh(db_device)
    return db_device

@router.get("/search", response_model=List[schemas.DeviceType])
async def search_device_types(
    query: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Search device types"""
    search = f"%{query}%"
    stmt = select(dcim.DeviceType).where(
        or_(
            dcim.DeviceType.name.ilike(search),
            dcim.DeviceType.manufacturer.ilike(search),
            dcim.DeviceType.model.ilike(search)
        )
    )
    
    if category:
        stmt = stmt.where(dcim.DeviceType.category == category)
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{device_id}", response_model=schemas.Device)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific device"""
    stmt = select(dcim.Device).where(dcim.Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a device"""
    stmt = select(dcim.Device).where(dcim.Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Delete associated interfaces
    stmt = select(dcim.Interface).where(dcim.Interface.device_id == device_id)
    result = await db.execute(stmt)
    interfaces = result.scalars().all()
    for interface in interfaces:
        await db.delete(interface)
    
    await db.delete(device)
    await db.commit()
    return {"message": "Device deleted"}
