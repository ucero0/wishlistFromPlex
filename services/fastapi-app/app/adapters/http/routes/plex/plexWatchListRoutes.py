from fastapi import APIRouter, Depends
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.factories.plex.plexWatchListFactory import getPlexWatchlistAdapter
from app.adapters.http.schemas.plex.plexWatchListSchemas import GetItemsInWatchListResponse
from app.domain.models.plexUser import PlexUser

plexWatchlistRoutes = APIRouter(prefix="/watchlist", tags=["plex-watchlist"])

@plexWatchlistRoutes.get("/items", response_model=GetItemsInWatchListResponse)
async def getItemsInWatchList(userToken: str, query: GetWatchListQuery = Depends(getPlexWatchlistAdapter)):
    items = await query.execute(userToken)
    return GetItemsInWatchListResponse(items=items)