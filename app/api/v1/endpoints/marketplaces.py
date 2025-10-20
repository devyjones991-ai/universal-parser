"""
API endpoints for marketplace management
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import parsing_profiles
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_supported_marketplaces():
    """Get list of supported marketplaces"""
    try:
        marketplaces = []
        
        for key, config in parsing_profiles.items():
            # Skip test profiles
            if 'test' in key.lower() or 'webscraper' in key.lower():
                continue
                
            marketplace_info = {
                "id": key,
                "name": config.get("name", key.title()),
                "base_url": config.get("base_url", ""),
                "method": config.get("method", "html"),
                "use_browser": config.get("use_browser", False),
                "timeout": config.get("timeout", 15),
                "supported_features": {
                    "search": "search_url" in config,
                    "item_parsing": "item_url" in config,
                    "price_tracking": "price" in config.get("selectors", {}),
                    "rating_tracking": "rating" in config.get("selectors", {}),
                    "stock_tracking": "stock" in config.get("selectors", {}),
                    "image_extraction": "images" in config.get("selectors", {})
                }
            }
            marketplaces.append(marketplace_info)
        
        return marketplaces
        
    except Exception as e:
        logger.error(f"Error getting marketplaces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get marketplaces: {str(e)}")


@router.get("/{marketplace_id}", response_model=Dict[str, Any])
async def get_marketplace_details(marketplace_id: str):
    """Get detailed information about a specific marketplace"""
    try:
        if marketplace_id not in parsing_profiles:
            raise HTTPException(status_code=404, detail="Marketplace not found")
        
        config = parsing_profiles[marketplace_id]
        
        # Skip test profiles
        if 'test' in marketplace_id.lower() or 'webscraper' in marketplace_id.lower():
            raise HTTPException(status_code=404, detail="Marketplace not found")
        
        details = {
            "id": marketplace_id,
            "name": config.get("name", marketplace_id.title()),
            "base_url": config.get("base_url", ""),
            "search_url": config.get("search_url", ""),
            "item_url": config.get("item_url", ""),
            "method": config.get("method", "html"),
            "use_browser": config.get("use_browser", False),
            "timeout": config.get("timeout", 15),
            "headers": config.get("headers", {}),
            "selectors": config.get("selectors", {}),
            "supported_features": {
                "search": "search_url" in config,
                "item_parsing": "item_url" in config,
                "price_tracking": "price" in config.get("selectors", {}),
                "rating_tracking": "rating" in config.get("selectors", {}),
                "stock_tracking": "stock" in config.get("selectors", {}),
                "image_extraction": "images" in config.get("selectors", {}),
                "description_extraction": "description" in config.get("selectors", {}),
                "specifications_extraction": "specifications" in config.get("selectors", {})
            }
        }
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting marketplace details for {marketplace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get marketplace details: {str(e)}")


@router.get("/{marketplace_id}/test")
async def test_marketplace_connection(marketplace_id: str):
    """Test connection to a specific marketplace"""
    try:
        if marketplace_id not in parsing_profiles:
            raise HTTPException(status_code=404, detail="Marketplace not found")
        
        config = parsing_profiles[marketplace_id]
        
        # Skip test profiles
        if 'test' in marketplace_id.lower() or 'webscraper' in marketplace_id.lower():
            raise HTTPException(status_code=404, detail="Marketplace not found")
        
        # Test basic connectivity
        import httpx
        
        base_url = config.get("base_url", "")
        if not base_url:
            return {"status": "error", "message": "No base URL configured"}
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(base_url)
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": f"Successfully connected to {config.get('name', marketplace_id)}",
                        "response_time": response.elapsed.total_seconds(),
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "status": "warning",
                        "message": f"Connected but got status code {response.status_code}",
                        "response_time": response.elapsed.total_seconds(),
                        "status_code": response.status_code
                    }
            except httpx.TimeoutException:
                return {
                    "status": "error",
                    "message": "Connection timeout"
                }
            except httpx.ConnectError:
                return {
                    "status": "error",
                    "message": "Connection failed"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Connection error: {str(e)}"
                }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing marketplace connection for {marketplace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test marketplace connection: {str(e)}")


@router.get("/{marketplace_id}/stats")
async def get_marketplace_stats(marketplace_id: str):
    """Get statistics for a specific marketplace"""
    try:
        if marketplace_id not in parsing_profiles:
            raise HTTPException(status_code=404, detail="Marketplace not found")
        
        # Skip test profiles
        if 'test' in marketplace_id.lower() or 'webscraper' in marketplace_id.lower():
            raise HTTPException(status_code=404, detail="Marketplace not found")
        
        # Mock statistics - in real implementation, this would come from database
        stats = {
            "marketplace_id": marketplace_id,
            "total_items_tracked": 0,  # Would be calculated from database
            "successful_parses": 0,
            "failed_parses": 0,
            "average_response_time": 0.0,
            "last_successful_parse": None,
            "last_failed_parse": None,
            "success_rate": 0.0
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting marketplace stats for {marketplace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get marketplace stats: {str(e)}")


@router.get("/health/overview")
async def get_marketplaces_health():
    """Get health overview of all marketplaces"""
    try:
        health_data = []
        
        for key, config in parsing_profiles.items():
            # Skip test profiles
            if 'test' in key.lower() or 'webscraper' in key.lower():
                continue
            
            health_info = {
                "marketplace_id": key,
                "name": config.get("name", key.title()),
                "status": "unknown",  # Would be determined by actual health checks
                "last_check": None,
                "response_time": None,
                "error_rate": 0.0
            }
            health_data.append(health_info)
        
        return {
            "total_marketplaces": len(health_data),
            "healthy": len([m for m in health_data if m["status"] == "healthy"]),
            "unhealthy": len([m for m in health_data if m["status"] == "unhealthy"]),
            "unknown": len([m for m in health_data if m["status"] == "unknown"]),
            "marketplaces": health_data
        }
        
    except Exception as e:
        logger.error(f"Error getting marketplaces health overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health overview: {str(e)}")


