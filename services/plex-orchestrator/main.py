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
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi_swagger_ui_theme import setup_swagger_ui_theme

from app.core.config import settings
from app.adapters.http.routes import (
    plexRoutes,
    delugeRoutes,
    prowlarr_routes,
    pipeline_routes,
    scheduler_routes,
    antivirus_routes,
    blacklist_torrent_routes,
    tracking_routes,
)
from app.application.settings.services.runtime_settings_service import (
    runtime_settings_service,
)
from app.application.settings.services.torrent_health_config_service import (
    torrent_health_config_service,
)
from app.adapters.http.routes.tmdb.tmdb_routes import tmdbRoutes
from app.adapters.http.exception_handlers import external_service_error_handler
from app.domain.errors.external import ExternalServiceError
from app.composition.plex_library_paths import (
    build_sync_plex_library_paths_for_active_users_use_case,
)
from app.composition.tmdb_users import build_ensure_tmdb_user_from_env_use_case
from app.factories.scheduler.scheduler_factory import create_scheduler_service
from app.infrastructure.scheduler.access import bind_scheduler
from app.infrastructure.persistence.database import async_session_scope

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Initialize scheduler service using factory
scheduler_service = create_scheduler_service()
bind_scheduler(scheduler_service)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup and shutdown (replaces deprecated on_event hooks)."""
    logger.info("Starting up Media Automation Service")
    async with async_session_scope() as session:
        try:
            sync_result = await build_sync_plex_library_paths_for_active_users_use_case(
                session
            ).execute()
            logger.info(
                "Startup Plex library path sync: %s active paths (%s from server)",
                sync_result["active_in_database"],
                sync_result["synced_from_server"],
            )
        except Exception as exc:
            logger.warning("Startup Plex library path sync failed: %s", exc)
        try:
            tmdb_user = await build_ensure_tmdb_user_from_env_use_case(session).execute()
            if tmdb_user:
                logger.info(
                    "Startup TMDB user ready: name=%s account_id=%s",
                    tmdb_user.name,
                    tmdb_user.account_id,
                )
        except Exception as exc:
            logger.warning("Startup TMDB user bootstrap from env failed: %s", exc)
        try:
            health_cfg = await torrent_health_config_service.ensure_config_row()
            logger.info(
                "Torrent health policy ready (db id=%s, updated_at=%s)",
                health_cfg.id,
                health_cfg.updated_at,
            )
        except Exception as exc:
            logger.warning("Startup torrent health config ensure failed: %s", exc)
    try:
        runtime_cfg = await runtime_settings_service.ensure_loaded()
        runtime_settings_service.apply_scheduler_intervals(scheduler_service, runtime_cfg)
        logger.info(
            "Runtime settings ready (watchlist=%sm ingest=%sm updated_at=%s)",
            runtime_cfg.watchlist_download_interval_minutes,
            runtime_cfg.ingest_poll_interval_minutes,
            runtime_cfg.updated_at,
        )
    except Exception as exc:
        logger.warning("Startup runtime settings load failed: %s", exc)
    scheduler_service.start()
    logger.info("Startup complete")
    yield
    logger.info("Shutting down Media Automation Service")
    scheduler_service.shutdown()
    logger.info("Shutdown complete")


OPENAPI_TAGS = [
    {
        "name": "Plex Media HDD (DB)",
        "description": (
            "Plex library paths and media HDD/volumes stored in PostgreSQL (`plex_library_paths`). "
            "Syncs from Plex using PLEX_SERVER_ADMIN_TOKEN, measures disk on this host, returns human-readable sizes. "
            "**Main HDD list:** `GET /plex/library-paths/media-devices`."
        ),
    },
]

# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    title="Media Automation Service",
    description="""
    Automated media management service that:
    - Syncs Plex watchlists from multiple users
    - Auto-searches for torrents via Prowlarr (prioritizes TrueHD, 2160p)
    - Sends downloads to Deluge
    - Scans completed downloads for viruses (antivirus + YARA)
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
    - `GET /deluge/torrents` - List all torrents (read-only)
    - `GET /deluge/torrents/completed` - List only completed torrents
    - `GET /deluge/torrents/downloading` - List only downloading torrents
    """,
    version="2.0.0",
    docs_url=None,
)

setup_swagger_ui_theme(
    app,
    docs_path="/docs",
    title=f"{app.title} - API Docs",
    swagger_ui_parameters={
        "docExpansion": "list",
        "filter": True,
        "tryItOutEnabled": True,
    },
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

# Map domain external-service errors to HTTP (hexagonal delivery layer)
app.add_exception_handler(ExternalServiceError, external_service_error_handler)

# Include API routers (microservice structure)
app.include_router(pipeline_routes)
app.include_router(scheduler_routes)
app.include_router(blacklist_torrent_routes)
app.include_router(tracking_routes)
app.include_router(plexRoutes)
app.include_router(delugeRoutes)
app.include_router(prowlarr_routes)
app.include_router(antivirus_routes)
app.include_router(tmdbRoutes)


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
            "plex_media_hdd_db": "/plex/library-paths/media-devices",
            "deferred_downloads_process": "POST /tracking/deferred-downloads/process",
            "watchlist_downloads_run": "POST /scheduler/watchlist-downloads/run",
            "deluge_maintenance_run": "POST /scheduler/jobs/process_deluge_torrents/run",
            "deluge_torrent_health": "GET|PUT /deluge/torrent-health",
            "scheduler_settings": "GET|PUT /scheduler/settings",
            "scheduler_jobs": "GET /scheduler/jobs",
            "deluge": "active",
            "antivirus": "active",
            "torrent_search": "active",
            "orchestration": "active",
            "file_manager": "coming_soon",
        },
    }
