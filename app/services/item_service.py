"""
Service for item management
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.item import TrackedItem, PriceHistory
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse, PriceHistoryResponse
from app.core.config import settings
import asyncio
from datetime import datetime, timedelta


class ItemService:
    """Service for managing tracked items"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_items(
        self, 
        skip: int = 0, 
        limit: int = 100,
        marketplace: Optional[str] = None,
        is_active: Optional[bool] = None,
        user_id: Optional[int] = None
    ) -> List[ItemResponse]:
        """Get list of tracked items with filters"""
        query = self.db.query(TrackedItem)
        
        if user_id:
            query = query.filter(TrackedItem.user_id == user_id)
        if marketplace:
            query = query.filter(TrackedItem.marketplace == marketplace)
        if is_active is not None:
            query = query.filter(TrackedItem.is_active == is_active)
        
        items = query.offset(skip).limit(limit).all()
        return [ItemResponse.from_orm(item) for item in items]
    
    async def get_item(self, item_id: int, user_id: Optional[int] = None) -> Optional[ItemResponse]:
        """Get specific tracked item"""
        query = self.db.query(TrackedItem).filter(TrackedItem.id == item_id)
        
        if user_id:
            query = query.filter(TrackedItem.user_id == user_id)
        
        item = query.first()
        return ItemResponse.from_orm(item) if item else None
    
    async def create_item(self, item_data: ItemCreate, user_id: int) -> ItemResponse:
        """Create new tracked item"""
        # Check user limits
        user_items_count = self.db.query(TrackedItem).filter(
            and_(
                TrackedItem.user_id == user_id,
                TrackedItem.is_active == True
            )
        ).count()
        
        # Get user subscription tier (simplified)
        if user_items_count >= settings.free_items_limit:
            raise ValueError("Item limit exceeded for your subscription tier")
        
        # Check if item already exists
        existing_item = self.db.query(TrackedItem).filter(
            and_(
                TrackedItem.item_id == item_data.item_id,
                TrackedItem.marketplace == item_data.marketplace,
                TrackedItem.user_id == user_id
            )
        ).first()
        
        if existing_item:
            raise ValueError("Item already tracked")
        
        # Create new item
        db_item = TrackedItem(
            user_id=user_id,
            item_id=item_data.item_id,
            marketplace=item_data.marketplace,
            name=item_data.name,
            brand=item_data.brand,
            category=item_data.category,
            url=item_data.url,
            sku=item_data.sku,
            tracking_settings=item_data.tracking_settings or {}
        )
        
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        
        return ItemResponse.from_orm(db_item)
    
    async def update_item(self, item_id: int, item_update: ItemUpdate, user_id: Optional[int] = None) -> Optional[ItemResponse]:
        """Update tracked item"""
        query = self.db.query(TrackedItem).filter(TrackedItem.id == item_id)
        
        if user_id:
            query = query.filter(TrackedItem.user_id == user_id)
        
        db_item = query.first()
        if not db_item:
            return None
        
        # Update fields
        update_data = item_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        db_item.last_updated = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_item)
        
        return ItemResponse.from_orm(db_item)
    
    async def delete_item(self, item_id: int, user_id: Optional[int] = None) -> bool:
        """Delete tracked item"""
        query = self.db.query(TrackedItem).filter(TrackedItem.id == item_id)
        
        if user_id:
            query = query.filter(TrackedItem.user_id == user_id)
        
        db_item = query.first()
        if not db_item:
            return False
        
        self.db.delete(db_item)
        self.db.commit()
        
        return True
    
    async def get_item_history(
        self, 
        item_id: int, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None
    ) -> List[PriceHistoryResponse]:
        """Get price history for specific item"""
        query = self.db.query(PriceHistory).filter(PriceHistory.tracked_item_id == item_id)
        
        if user_id:
            query = query.filter(PriceHistory.user_id == user_id)
        
        history = query.order_by(desc(PriceHistory.timestamp)).offset(skip).limit(limit).all()
        return [PriceHistoryResponse.from_orm(record) for record in history]
    
    async def refresh_item(self, item_id: int, user_id: Optional[int] = None) -> bool:
        """Manually refresh item data"""
        query = self.db.query(TrackedItem).filter(TrackedItem.id == item_id)
        
        if user_id:
            query = query.filter(TrackedItem.user_id == user_id)
        
        db_item = query.first()
        if not db_item:
            return False
        
        # Update last_checked timestamp
        db_item.last_checked = datetime.utcnow()
        self.db.commit()
        
        # TODO: Trigger actual parsing job
        # This would typically add a job to a queue
        
        return True
    
    async def get_item_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get item statistics"""
        query = self.db.query(TrackedItem)
        
        if user_id:
            query = query.filter(TrackedItem.user_id == user_id)
        
        total_items = query.count()
        active_items = query.filter(TrackedItem.is_active == True).count()
        available_items = query.filter(TrackedItem.is_available == True).count()
        
        # Calculate average price
        avg_price = self.db.query(TrackedItem.current_price).filter(
            and_(
                TrackedItem.current_price.isnot(None),
                TrackedItem.is_active == True
            )
        ).scalar()
        
        if user_id:
            avg_price = self.db.query(TrackedItem.current_price).filter(
                and_(
                    TrackedItem.user_id == user_id,
                    TrackedItem.current_price.isnot(None),
                    TrackedItem.is_active == True
                )
            ).scalar()
        
        # Count price changes in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        price_changes_24h = self.db.query(PriceHistory).filter(
            PriceHistory.timestamp >= yesterday
        ).count()
        
        if user_id:
            price_changes_24h = self.db.query(PriceHistory).filter(
                and_(
                    PriceHistory.user_id == user_id,
                    PriceHistory.timestamp >= yesterday
                )
            ).count()
        
        # Count new items in last 24 hours
        new_items_24h = query.filter(TrackedItem.created_at >= yesterday).count()
        
        # Count by marketplace
        marketplaces = {}
        marketplace_counts = self.db.query(
            TrackedItem.marketplace, 
            self.db.func.count(TrackedItem.id)
        ).filter(TrackedItem.is_active == True).group_by(TrackedItem.marketplace).all()
        
        if user_id:
            marketplace_counts = self.db.query(
                TrackedItem.marketplace, 
                self.db.func.count(TrackedItem.id)
            ).filter(
                and_(
                    TrackedItem.user_id == user_id,
                    TrackedItem.is_active == True
                )
            ).group_by(TrackedItem.marketplace).all()
        
        for marketplace, count in marketplace_counts:
            marketplaces[marketplace] = count
        
        return {
            "total_items": total_items,
            "active_items": active_items,
            "available_items": available_items,
            "avg_price": float(avg_price) if avg_price else None,
            "price_changes_24h": price_changes_24h,
            "new_items_24h": new_items_24h,
            "marketplaces": marketplaces
        }
