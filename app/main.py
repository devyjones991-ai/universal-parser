"""
FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from app.core.config import settings
from app.core.database import init_db, init_async_db, close_db
from app.core.cache import cache_service
from app.api.v1.endpoints import items, parsing, ai, marketplaces, niche_analysis, automation, subscription, payment, russian_marketplaces, social, advanced_analytics, report_scheduler, international

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Universal Parser API...")
    
    # Initialize database
    init_db()
    await init_async_db()
    logger.info("✅ Database initialized")
    
    # Initialize Redis cache
    await cache_service.connect()
    logger.info("✅ Cache service initialized")
    
    # TODO: Start background tasks (scheduler, monitoring)
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Universal Parser API...")
    await cache_service.disconnect()
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Comprehensive marketplace monitoring platform",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure properly for production
)


# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": time.time()
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "docs": f"{settings.api_v1_prefix}/docs",
        "health": "/health"
    }


# Include API routers
app.include_router(
    items.router,
    prefix=f"{settings.api_v1_prefix}/items",
    tags=["items"]
)

app.include_router(
    parsing.router,
    prefix=f"{settings.api_v1_prefix}/parsing",
    tags=["parsing"]
)

app.include_router(
    ai.router,
    prefix=f"{settings.api_v1_prefix}/ai",
    tags=["ai"]
)

app.include_router(
    marketplaces.router,
    prefix=f"{settings.api_v1_prefix}/marketplaces",
    tags=["marketplaces"]
)

app.include_router(
    niche_analysis.router,
    prefix=f"{settings.api_v1_prefix}/niche-analysis",
    tags=["niche-analysis"]
)

app.include_router(
    automation.router,
    prefix=f"{settings.api_v1_prefix}/automation",
    tags=["automation"]
)

app.include_router(
    subscription.router,
    prefix=f"{settings.api_v1_prefix}/subscription",
    tags=["subscription"]
)

app.include_router(
    payment.router,
    prefix=f"{settings.api_v1_prefix}/payment",
    tags=["payment"]
)

app.include_router(
    russian_marketplaces.router,
    prefix=f"{settings.api_v1_prefix}/russian-marketplaces",
    tags=["russian-marketplaces"]
)

app.include_router(
    social.router,
    prefix=f"{settings.api_v1_prefix}/social",
    tags=["social"]
)

app.include_router(
    advanced_analytics.router,
    prefix=f"{settings.api_v1_prefix}/advanced-analytics",
    tags=["advanced-analytics"]
)

app.include_router(
    report_scheduler.router,
    prefix=f"{settings.api_v1_prefix}/report-scheduler",
    tags=["report-scheduler"]
)

app.include_router(
    international.router,
    prefix=f"{settings.api_v1_prefix}/international",
    tags=["international"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
