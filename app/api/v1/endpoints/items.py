"""
API endpoints for item management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.item import TrackedItem, PriceHistory
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate, PriceHistoryResponse
from app.services.item_service import ItemService

router = APIRouter()


@router.get("/", response_model=List[ItemResponse])
async def get_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    marketplace: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get list of tracked items"""
    service = ItemService(db)
    return await service.get_items(
        skip=skip, 
        limit=limit, 
        marketplace=marketplace, 
        is_active=is_active
    )


@router.post("/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db)
):
    """Create new tracked item"""
    service = ItemService(db)
    return await service.create_item(item)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get specific tracked item"""
    service = ItemService(db)
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    db: Session = Depends(get_db)
):
    """Update tracked item"""
    service = ItemService(db)
    item = await service.update_item(item_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Delete tracked item"""
    service = ItemService(db)
    success = await service.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}


@router.get("/{item_id}/history", response_model=List[PriceHistoryResponse])
async def get_item_history(
    item_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get price history for specific item"""
    service = ItemService(db)
    return await service.get_item_history(item_id, skip=skip, limit=limit)


@router.post("/{item_id}/refresh")
async def refresh_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Manually refresh item data"""
    service = ItemService(db)
    success = await service.refresh_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item refresh initiated"}
