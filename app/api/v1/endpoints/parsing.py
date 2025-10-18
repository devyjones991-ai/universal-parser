"""
API endpoints for parsing operations
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.parsing_service import EnhancedParsingService
from app.schemas.parsing import ParsingRequest, ParsingResponse, ParsingStatsResponse
from app.core.cache import cache_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/parse", response_model=ParsingResponse)
async def parse_url(
    request: ParsingRequest,
    background_tasks: BackgroundTasks
):
    """Parse URL with specified method"""
    try:
        async with EnhancedParsingService() as parser:
            result = await parser.parse_url(
                url=request.url,
                method=request.method
            )
            
            return ParsingResponse(
                url=request.url,
                method=request.method,
                success=True,
                data=result,
                cached=False  # Will be determined by service
            )
            
    except Exception as e:
        logger.error(f"Parsing error for {request.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")


@router.get("/parse/marketplace/{marketplace}/{item_id}")
async def parse_marketplace_item(
    marketplace: str,
    item_id: str,
    background_tasks: BackgroundTasks
):
    """Parse specific marketplace item"""
    try:
        async with EnhancedParsingService() as parser:
            result = await parser.parse_marketplace_item(marketplace, item_id)
            
            if not result:
                raise HTTPException(status_code=404, detail="Item not found or parsing failed")
            
            return ParsingResponse(
                url=result.get("url", ""),
                method="browser",
                success=True,
                data=[result.get("data", {})],
                cached=False
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Marketplace parsing error for {marketplace}/{item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")


@router.get("/cache/stats", response_model=ParsingStatsResponse)
async def get_cache_stats():
    """Get parsing cache statistics"""
    try:
        stats = await cache_service.get_stats()
        return ParsingStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.delete("/cache")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Cache key pattern to clear")
):
    """Clear parsing cache"""
    try:
        if pattern:
            deleted_count = await cache_service.delete_pattern(pattern)
            return {"message": f"Cleared {deleted_count} cache entries matching pattern: {pattern}"}
        else:
            # Clear all parsing-related cache
            deleted_count = await cache_service.delete_pattern("parse:*")
            deleted_count += await cache_service.delete_pattern("marketplace:*")
            return {"message": f"Cleared {deleted_count} cache entries"}
            
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/health")
async def parsing_health_check():
    """Health check for parsing service"""
    try:
        # Test cache connection
        cache_stats = await cache_service.get_stats()
        
        return {
            "status": "healthy",
            "cache_status": cache_stats.get("status", "unknown"),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Parsing health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }
