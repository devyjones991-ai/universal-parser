#!/usr/bin/env python3
"""
FastAPI version of Universal Parser
"""
import asyncio
import logging
from app.main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Main function for FastAPI application"""
    logger.info("🚀 Universal Parser FastAPI starting...")
    
    try:
        # Import uvicorn here to avoid issues
        import uvicorn
        
        # Run the FastAPI application
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal...")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
    finally:
        logger.info("✅ Application stopped")

if __name__ == "__main__":
    asyncio.run(main())
