"""
Media Automation Service - Main Application Entry Point

This service provides:
- Plex watchlist sync and management
- (Future) Torrent search integration
- (Future) Deluge torrent client integration
- (Future) Virus scanning
- (Future) File management for Plex library
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import engine, Base
from app.core.scheduler import start_scheduler, stop_scheduler

# Import module routers
from app.modules.plex import router as plex_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Media Automation Service",
    description="""
    Automated media management service that:
    - Syncs Plex watchlists from multiple users
    - (Coming soon) Searches for torrent magnet links
    - (Coming soon) Sends downloads to Deluge
    - (Coming soon) Scans completed downloads for viruses
    - (Coming soon) Moves clean files to Plex library
    """,
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include module routers
app.include_router(plex_router)

# Future modules will be added here:
# app.include_router(torrent_search_router)
# app.include_router(deluge_router)
# app.include_router(scanner_router)
# app.include_router(file_manager_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler on startup."""
    logger.info("Starting up Media Automation Service")
    
    # Create database tables (if they don't exist)
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
    logger.info("Shutting down Media Automation Service")
    stop_scheduler()
    logger.info("Shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "media-automation-service"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Media Automation Service",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "modules": {
            "plex": "active",
            "torrent_search": "coming_soon",
            "deluge": "coming_soon",
            "scanner": "coming_soon",
            "file_manager": "coming_soon",
        },
    }
