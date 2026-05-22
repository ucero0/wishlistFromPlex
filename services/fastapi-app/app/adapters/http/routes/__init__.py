from fastapi import APIRouter
from app.adapters.http.routes.plex.plexConnectionRoutes import plex_connection_routes
from app.adapters.http.routes.plex.plexServerRoutes import plexServerRoutes
from app.adapters.http.routes.plex.plexLibraryPathRoutes import plexLibraryPathRoutes
from app.adapters.http.routes.plex.plexUserRoutes import plexUserRoutes
from app.adapters.http.routes.plex.plexWatchListRoutes import plexWatchlistRoutes
from app.adapters.http.routes.deluge.delugeRoutes import torrents_routes
from app.adapters.http.routes.deluge.delugeConnectionRoutes import deluge_connection_routes
from app.adapters.http.routes.prowlarr.prowlarrRoutes import prowlarrRoutes
from app.adapters.http.routes.orchestrator.routes import orchestratorRoutes
from app.adapters.http.routes.antivirus.antivirusRoutes import antivirusRoutes
from app.adapters.http.routes.blacklist_torrent import blacklistTorrentRoutes
from app.adapters.http.routes.tracking.trackingRoutes import trackingRoutes

plexRoutes = APIRouter(prefix="/plex")
plexRoutes.include_router(plex_connection_routes)
plexRoutes.include_router(plexServerRoutes)
plexRoutes.include_router(plexLibraryPathRoutes)
plexRoutes.include_router(plexUserRoutes)
plexRoutes.include_router(plexWatchlistRoutes)

delugeRoutes = APIRouter(prefix="/deluge", tags=["deluge"])
delugeRoutes.include_router(deluge_connection_routes)
delugeRoutes.include_router(torrents_routes)

