"""
Pydantic schemas for parsing operations
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class ParsingRequest(BaseModel):
    """Request schema for URL parsing"""
    url: HttpUrl = Field(..., description="URL to parse")
    method: str = Field(default="http", description="Parsing method: http or browser")
    cache_ttl: Optional[int] = Field(default=300, description="Cache TTL in seconds")


class ParsingResponse(BaseModel):
    """Response schema for parsing results"""
    url: str = Field(..., description="Parsed URL")
    method: str = Field(..., description="Used parsing method")
    success: bool = Field(..., description="Whether parsing was successful")
    data: List[Dict[str, Any]] = Field(..., description="Parsed data")
    cached: bool = Field(default=False, description="Whether result was from cache")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ParsingStatsResponse(BaseModel):
    """Response schema for parsing statistics"""
    status: str = Field(..., description="Cache status")
    used_memory: Optional[str] = Field(None, description="Used memory")
    connected_clients: Optional[int] = Field(None, description="Connected clients")
    total_commands_processed: Optional[int] = Field(None, description="Total commands processed")
    keyspace_hits: Optional[int] = Field(None, description="Cache hits")
    keyspace_misses: Optional[int] = Field(None, description="Cache misses")


class MarketplaceItemRequest(BaseModel):
    """Request schema for marketplace item parsing"""
    marketplace: str = Field(..., description="Marketplace name")
    item_id: str = Field(..., description="Item ID on marketplace")
    force_refresh: bool = Field(default=False, description="Force refresh from source")


class MarketplaceItemResponse(BaseModel):
    """Response schema for marketplace item parsing"""
    marketplace: str = Field(..., description="Marketplace name")
    item_id: str = Field(..., description="Item ID")
    url: str = Field(..., description="Item URL")
    success: bool = Field(..., description="Whether parsing was successful")
    data: Dict[str, Any] = Field(..., description="Parsed item data")
    cached: bool = Field(default=False, description="Whether result was from cache")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
