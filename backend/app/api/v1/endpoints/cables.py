from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from backend.app.core.database import get_db
from backend.app.models.dcim import Cable as CableModel
from backend.app.schemas.dcim import Cable, CableCreate, CableUpdate, CableList

router = APIRouter()

@router.post("/", response_model=Cable, status_code=status.HTTP_201_CREATED)
async def create_cable(
    cable: CableCreate,
    db: AsyncSession = Depends(get_db)
):
    db_cable = CableModel(**cable.dict())
    db.add(db_cable)
    await db.commit()
    await db.refresh(db_cable)
    return db_cable

@router.get("/", response_model=CableList)
async def read_cables(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CableModel).offset(skip).limit(limit)
    )
    cables = result.scalars().all()
    return CableList(total=len(cables), items=cables)

@router.get("/{cable_id}", response_model=Cable)
async def read_cable(
    cable_id: int,
    db: AsyncSession = Depends(get_db)
):
    cable = await db.get(CableModel, cable_id)
    if cable is None:
        raise HTTPException(status_code=404, detail="Cable not found")
    return cable

@router.put("/{cable_id}", response_model=Cable)
async def update_cable(
    cable_id: int,
    cable: CableUpdate,
    db: AsyncSession = Depends(get_db)
):
    db_cable = await db.get(CableModel, cable_id)
    if db_cable is None:
        raise HTTPException(status_code=404, detail="Cable not found")
    for key, value in cable.dict().items():
        setattr(db_cable, key, value)
    await db.commit()
    await db.refresh(db_cable)
    return db_cable

@router.delete("/{cable_id}", response_model=Cable)
async def delete_cable(
    cable_id: int,
    db: AsyncSession = Depends(get_db)
):
    db_cable = await db.get(CableModel, cable_id)
    if db_cable is None:
        raise HTTPException(status_code=404, detail="Cable not found")
    await db.delete(db_cable)
    await db.commit()
    return db_cable
