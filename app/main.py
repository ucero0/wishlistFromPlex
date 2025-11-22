import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import engine, Base
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api import routes_tokens, routes_wishlist, routes_sync

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Plex Wishlist Service",
    description="Service to sync Plex user watchlists into a shared database",
    version="1.0.0",
)

# CORS middleware (allow all origins - adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_tokens.router)
app.include_router(routes_wishlist.router)
app.include_router(routes_sync.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler on startup."""
    logger.info("Starting up Plex Wishlist Service")
    
    # Create database tables (if they don't exist)
    # In production, use Alembic migrations instead
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    # Start scheduler
    start_scheduler()
    logger.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on shutdown."""
    logger.info("Shutting down Plex Wishlist Service")
    stop_scheduler()
    logger.info("Shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "plex-wishlist-service"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Plex Wishlist Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }



