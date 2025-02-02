from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiohttp
import time

from ....core.database import get_db
from ....models import dcim, netbox
from ....schemas import netbox as schemas

router = APIRouter()

@router.post("/connections/", response_model=schemas.NetBoxConnection)
async def create_netbox_connection(
    connection: schemas.NetBoxConnectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new NetBox connection"""
    db_connection = netbox.NetBoxConnection(
        name=connection.name,
        url=str(connection.url),
        api_key=connection.api_key,
        ssl_verify=connection.ssl_verify,
        custom_fields=connection.custom_fields
    )
    db.add(db_connection)
    await db.commit()
    await db.refresh(db_connection)
    return db_connection

@router.get("/connections/", response_model=List[schemas.NetBoxConnection])
async def list_netbox_connections(db: AsyncSession = Depends(get_db)):
    """List all NetBox connections"""
    stmt = select(netbox.NetBoxConnection)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/import/device-types/", response_model=schemas.NetBoxImportStatus)
async def import_device_types(
    request: schemas.NetBoxImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Import device types from NetBox"""
    stmt = select(netbox.NetBoxConnection).where(netbox.NetBoxConnection.id == request.connection_id)
    result = await db.execute(stmt)
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="NetBox connection not found")

    try:
        # Create import log entry
        import_log = netbox.NetBoxImportLog(
            connection_id=connection.id,
            timestamp=int(time.time()),
            operation='import_device_types',
            status='processing',
            details={}
        )
        db.add(import_log)
        await db.commit()

        # Get device types from NetBox
        headers = connection.get_headers()
        device_types_url = connection.get_device_types_url()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                device_types_url,
                headers=headers,
                ssl=bool(connection.ssl_verify)
            ) as response:
                response.raise_for_status()
                device_types_data = await response.json()

            imported_count = 0
            errors = []

            for device_type in device_types_data['results']:
                try:
                    # Skip if not in requested device_type_ids
                    if (request.device_type_ids and 
                        device_type['id'] not in request.device_type_ids):
                        continue

                    # Get interface templates if requested
                    interfaces = []
                    if request.include_interfaces:
                        async with session.get(
                            connection.get_interface_templates_url(device_type['id']),
                            headers=headers,
                            ssl=bool(connection.ssl_verify)
                        ) as interface_response:
                            interface_response.raise_for_status()
                            interfaces = (await interface_response.json())['results']

                    # Create or update device type
                    stmt = select(dcim.DeviceType).where(
                        dcim.DeviceType.netbox_id == device_type['id']
                    )
                    result = await db.execute(stmt)
                    db_device_type = result.scalar_one_or_none()

                    if not db_device_type:
                        db_device_type = dcim.DeviceType(
                            netbox_id=device_type['id'],
                            name=device_type['display'],
                            manufacturer=device_type['manufacturer']['name'],
                            model=device_type['model'],
                            part_number=device_type.get('part_number'),
                            u_height=device_type.get('u_height', 1),
                            is_full_depth=1 if device_type.get('is_full_depth') else 0
                        )
                        db.add(db_device_type)
                    else:
                        db_device_type.name = device_type['display']
                        db_device_type.manufacturer = device_type['manufacturer']['name']
                        db_device_type.model = device_type['model']
                        db_device_type.part_number = device_type.get('part_number')
                        db_device_type.u_height = device_type.get('u_height', 1)
                        db_device_type.is_full_depth = 1 if device_type.get('is_full_depth') else 0

                    # Create or update interface types
                    if request.include_interfaces:
                        for interface in interfaces:
                            stmt = select(dcim.InterfaceType).where(
                                dcim.InterfaceType.name == interface['type']['name']
                            )
                            result = await db.execute(stmt)
                            interface_type = result.scalar_one_or_none()

                            if not interface_type:
                                interface_type = dcim.InterfaceType(
                                    name=interface['type']['name'],
                                    connector_type=interface['type'].get('connector'),
                                    media_type=interface['type'].get('media_type')
                                )
                                db.add(interface_type)
                                await db.flush()  # Get ID for relationship

                            if interface_type not in db_device_type.interface_types:
                                db_device_type.interface_types.append(interface_type)

                    imported_count += 1

                except Exception as e:
                    errors.append(f"Error importing device type {device_type['id']}: {str(e)}")

            await db.commit()

            # Update import log
            import_log.status = 'success' if not errors else 'partial'
            import_log.details = {
                'imported_count': imported_count,
                'errors': errors
            }
            await db.commit()

            return schemas.NetBoxImportStatus(
                success=True,
                message="Device types import completed",
                imported_count=imported_count,
                errors=errors if errors else None
            )

    except Exception as e:
        # Update import log on error
        if import_log:
            import_log.status = 'error'
            import_log.details = {'error': str(e)}
            await db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to import device types: {str(e)}"
        )

@router.get("/sync/status/{sync_id}", response_model=schemas.NetBoxSyncStatus)
async def get_sync_status(sync_id: int, db: AsyncSession = Depends(get_db)):
    """Get status of a sync operation"""
    stmt = select(netbox.NetBoxSyncQueue).where(netbox.NetBoxSyncQueue.id == sync_id)
    result = await db.execute(stmt)
    sync_task = result.scalar_one_or_none()
    if not sync_task:
        raise HTTPException(status_code=404, detail="Sync task not found")

    return schemas.NetBoxSyncStatus(
        success=True,
        sync_id=sync_task.id,
        status=sync_task.status,
        details=sync_task.result
    )
