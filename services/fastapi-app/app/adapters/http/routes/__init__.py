from fastapi import APIRouter
from app.adapters.http.routes.plex.plexServerRoutes import plexServerRoutes
from app.adapters.http.routes.plex.plexUserRoutes import plexUserRoutes
from app.adapters.http.routes.plex.plexWatchListRoutes import plexWatchlistRoutes
from app.adapters.http.routes.deluge.delugeRoutes import torrentsRoutes
from app.adapters.http.routes.prowlarr.prowlarrRoutes import prowlarrRoutes

plexRoutes = APIRouter(prefix="/plex", tags=["plex"])
plexRoutes.include_router(plexServerRoutes)
plexRoutes.include_router(plexUserRoutes)
plexRoutes.include_router(plexWatchlistRoutes)

delugeRoutes = APIRouter(prefix="/deluge", tags=["deluge"])
delugeRoutes.include_router(torrentsRoutes)
