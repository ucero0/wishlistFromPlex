from fastapi import APIRouter
from app.adapters.http.routes.plex.plex_connection_routes import plex_connection_routes
from app.adapters.http.routes.plex.plex_server_routes import plex_server_routes
from app.adapters.http.routes.plex.plex_library_path_routes import plex_library_path_routes
from app.adapters.http.routes.plex.plex_user_routes import plex_user_routes
from app.adapters.http.routes.plex.plex_watchlist_routes import plex_watchlist_routes
from app.adapters.http.routes.deluge.deluge_routes import torrents_routes
from app.adapters.http.routes.deluge.deluge_connection_routes import deluge_connection_routes
from app.adapters.http.routes.prowlarr.prowlarr_routes import prowlarr_routes
from app.adapters.http.routes.pipelines.pipeline_routes import pipeline_routes
from app.adapters.http.routes.antivirus.antivirus_routes import antivirus_routes
from app.adapters.http.routes.blacklist_torrent import blacklist_torrent_routes
from app.adapters.http.routes.tracking.tracking_routes import tracking_routes
from app.adapters.http.routes.scheduler.scheduler_routes import scheduler_routes

plexRoutes = APIRouter(prefix="/plex")
plexRoutes.include_router(plex_connection_routes)
plexRoutes.include_router(plex_server_routes)
plexRoutes.include_router(plex_library_path_routes)
plexRoutes.include_router(plex_user_routes)
plexRoutes.include_router(plex_watchlist_routes)

delugeRoutes = APIRouter(prefix="/deluge", tags=["deluge"])
delugeRoutes.include_router(deluge_connection_routes)
delugeRoutes.include_router(torrents_routes)

