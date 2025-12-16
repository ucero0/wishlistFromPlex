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
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.adapters.http.routes.plex import plexRoutes

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
    - Auto-searches for torrents via Prowlarr (prioritizes TrueHD, 2160p)
    - Sends downloads to Deluge through VPN
    - Scans completed downloads for viruses (ClamAV + YARA)
    - Organizes clean files into Plex library structure
    
    ## Authentication
    
    Most endpoints require API key authentication via the `X-API-Key` header.
    Set your API key in the `API_KEY` environment variable.
    
    Example:
    ```bash
    curl -H "X-API-Key: your-api-key-here" http://localhost:8000/api/endpoint
    ```
    
    Public endpoints (no authentication required):
    - `GET /health` - Health check
    - `GET /` - API information
    - `GET /deluge/status` - Deluge connection status
    - `GET /deluge/torrents` - List torrents (read-only)
    """,
    version="2.0.0",
)

# Request logging middleware for debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.debug(f"Query params: {dict(request.query_params)}")
    logger.debug(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for request validation errors (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors in detail for debugging."""
    logger.error(f"Validation error for {request.method} {request.url.path}")
    logger.error(f"Validation errors: {exc.errors()}")
    # Log the body from the exception if available
    if hasattr(exc, 'body'):
        logger.error(f"Request body: {exc.body}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# Include API routers (microservice structure)
app.include_router(plexRoutes)


@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler on startup."""
    logger.info("Starting up Media Automation Service")
    
    # Note: Database tables are created via Alembic migrations
    # which run automatically in the Docker entrypoint script.
    # No need to create tables here as we're using async engine.
    logger.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on shutdown."""
    logger.info("Shutting down Media Automation Service")
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
            "deluge": "active",
            "scanner": "active",
            "torrent_search": "active",
            "orchestration": "active",
            "file_manager": "coming_soon",
        },
    }
