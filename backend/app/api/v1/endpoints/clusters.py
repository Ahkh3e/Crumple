from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from ....core.database import get_db
from ....models import dcim
from ....schemas import dcim as schemas

router = APIRouter()

def build_cluster_tree(clusters: List[dcim.Cluster], parent_id: Optional[int] = None) -> List[dict]:
    """Recursively build cluster hierarchy"""
    tree = []
    for cluster in clusters:
        if cluster.parent_id == parent_id:
            children = build_cluster_tree(clusters, cluster.id)
            cluster_dict = {
                'id': cluster.id,
                'name': cluster.name,
                'description': cluster.description,
                'site': cluster.site,
                'status': cluster.status,
                'custom_fields': cluster.custom_fields,
                'children': children,
                'devices': [
                    {
                        'id': device.id,
                        'name': device.name,
                        'device_type': {
                            'id': device.device_type.id,
                            'name': device.device_type.name
                        } if device.device_type else None
                    }
                    for device in cluster.devices
                ]
            }
            tree.append(cluster_dict)
    return tree

@router.post("/", response_model=schemas.Cluster)
async def create_cluster(
    cluster: schemas.ClusterCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new cluster"""
    # Validate parent cluster exists if specified
    if cluster.parent_id:
        stmt = select(dcim.Cluster).where(dcim.Cluster.id == cluster.parent_id)
        result = await db.execute(stmt)
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent cluster not found")

    db_cluster = dcim.Cluster(**cluster.dict())
    db.add(db_cluster)
    await db.commit()
    
    # Reload with relationships
    stmt = select(dcim.Cluster).options(
        selectinload(dcim.Cluster.devices).selectinload(dcim.Device.device_type),
        selectinload(dcim.Cluster.children)
    ).where(dcim.Cluster.id == db_cluster.id)
    result = await db.execute(stmt)
    return result.scalar_one()

@router.get("/", response_model=List[dict])
async def list_clusters(
    db: AsyncSession = Depends(get_db),
    parent_id: Optional[int] = None
):
    """List clusters in a tree structure"""
    stmt = select(dcim.Cluster).options(
        selectinload(dcim.Cluster.devices).selectinload(dcim.Device.device_type),
        selectinload(dcim.Cluster.children)
    )
    result = await db.execute(stmt)
    clusters = result.scalars().all()
    return build_cluster_tree(clusters, parent_id)

@router.get("/{cluster_id}", response_model=schemas.Cluster)
async def get_cluster(
    cluster_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific cluster"""
    stmt = select(dcim.Cluster).options(
        selectinload(dcim.Cluster.devices).selectinload(dcim.Device.device_type),
        selectinload(dcim.Cluster.children)
    ).where(dcim.Cluster.id == cluster_id)
    result = await db.execute(stmt)
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster

@router.put("/{cluster_id}", response_model=schemas.Cluster)
async def update_cluster(
    cluster_id: int,
    cluster: schemas.ClusterCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update a cluster"""
    stmt = select(dcim.Cluster).where(dcim.Cluster.id == cluster_id)
    result = await db.execute(stmt)
    db_cluster = result.scalar_one_or_none()
    if not db_cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Validate parent cluster exists and prevent circular references
    if cluster.parent_id:
        if cluster.parent_id == cluster_id:
            raise HTTPException(
                status_code=400,
                detail="Cluster cannot be its own parent"
            )
        
        stmt = select(dcim.Cluster).where(dcim.Cluster.id == cluster.parent_id)
        result = await db.execute(stmt)
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent cluster not found")
        
        # Check for circular references
        current_parent = parent
        while current_parent:
            if current_parent.id == cluster_id:
                raise HTTPException(
                    status_code=400,
                    detail="Circular reference detected in cluster hierarchy"
                )
            current_parent = current_parent.parent

    for key, value in cluster.dict().items():
        setattr(db_cluster, key, value)

    await db.commit()
    
    # Reload with relationships
    stmt = select(dcim.Cluster).options(
        selectinload(dcim.Cluster.devices).selectinload(dcim.Device.device_type),
        selectinload(dcim.Cluster.children)
    ).where(dcim.Cluster.id == cluster_id)
    result = await db.execute(stmt)
    return result.scalar_one()

@router.delete("/{cluster_id}")
async def delete_cluster(
    cluster_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a cluster and its children"""
    stmt = select(dcim.Cluster).where(dcim.Cluster.id == cluster_id)
    result = await db.execute(stmt)
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Delete child clusters recursively
    stmt = select(dcim.Cluster).where(dcim.Cluster.parent_id == cluster_id)
    result = await db.execute(stmt)
    children = result.scalars().all()
    for child in children:
        await delete_cluster(child.id, db)

    await db.delete(cluster)
    await db.commit()
    return {"message": "Cluster deleted"}

@router.get("/{cluster_id}/topology", response_model=dict)
async def get_cluster_topology(
    cluster_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get topology for a specific cluster"""
    # Get cluster with devices
    stmt = select(dcim.Cluster).options(
        selectinload(dcim.Cluster.devices).selectinload(dcim.Device.device_type)
    ).where(dcim.Cluster.id == cluster_id)
    result = await db.execute(stmt)
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Get all devices and their positions in this cluster
    devices = cluster.devices

    # Get all interfaces for these devices
    device_ids = [device.id for device in devices]
    stmt = select(dcim.Interface).options(
        selectinload(dcim.Interface.device_type)
    ).where(dcim.Interface.device_id.in_(device_ids))
    result = await db.execute(stmt)
    interfaces = result.scalars().all()

    # Get all cables between these interfaces
    interface_ids = [interface.id for interface in interfaces]
    stmt = select(dcim.Cable).options(
        selectinload(dcim.Cable.interface_a).selectinload(dcim.Interface.device),
        selectinload(dcim.Cable.interface_b).selectinload(dcim.Interface.device)
    ).where(and_(
        dcim.Cable.interface_a_id.in_(interface_ids),
        dcim.Cable.interface_b_id.in_(interface_ids)
    ))
    result = await db.execute(stmt)
    cables = result.scalars().all()

    # Build topology response
    topology = {
        "nodes": [
            {
                "id": str(device.id),
                "type": device.device_type.name.lower() if device.device_type else "unknown",
                "label": device.name,
                "position": {
                    "x": device.position_x or 100,
                    "y": device.position_y or 100
                }
            }
            for device in devices
        ],
        "edges": [
            {
                "id": str(cable.id),
                "source": str(cable.interface_a.device_id),
                "target": str(cable.interface_b.device_id),
                "type": cable.type
            }
            for cable in cables
        ]
    }

    return topology

@router.put("/{cluster_id}/topology")
async def update_cluster_topology(
    cluster_id: int,
    topology: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update topology for a specific cluster"""
    stmt = select(dcim.Cluster).where(dcim.Cluster.id == cluster_id)
    result = await db.execute(stmt)
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    try:
        # Update device positions
        for node in topology["nodes"]:
            stmt = select(dcim.Device).where(dcim.Device.id == int(node["id"]))
            result = await db.execute(stmt)
            device = result.scalar_one_or_none()
            if device and device.cluster_id == cluster_id:
                device.position_x = node["position"]["x"]
                device.position_y = node["position"]["y"]

        # Update cable connections
        # First, remove all existing cables
        stmt = select(dcim.Cable).where(
            dcim.Cable.interface_a.has(device_id=cluster_id) |
            dcim.Cable.interface_b.has(device_id=cluster_id)
        )
        result = await db.execute(stmt)
        cables = result.scalars().all()
        for cable in cables:
            await db.delete(cable)

        # Then create new cables
        for edge in topology["edges"]:
            cable = dcim.Cable(
                interface_a_id=int(edge["source"]),
                interface_b_id=int(edge["target"]),
                type=edge["type"]
            )
            db.add(cable)

        await db.commit()
        return {"message": "Topology updated successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating topology: {str(e)}"
        )
