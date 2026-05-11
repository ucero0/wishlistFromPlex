from fastapi import APIRouter, Depends, Query, Response, status
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.factories.plex.plexWatchListFactory import createGetWatchListQuery
from app.adapters.http.schemas.plex.plexWatchListSchemas import GetItemsInWatchListResponse
from app.application.plex.useCases.removeWatchListItem import RemoveWatchListItemUseCase
from app.factories.plex.plexWatchListFactory import createRemoveWatchListItemUseCase


plexWatchlistRoutes = APIRouter(prefix="/watchlist", tags=["plex-watchlist"])

@plexWatchlistRoutes.get("/items", response_model=GetItemsInWatchListResponse)
async def get_items_in_watchlist(
    user_token: str = Query(alias="userToken"),
    query: GetWatchListQuery = Depends(createGetWatchListQuery),
):
    items = await query.execute(user_token)
    return GetItemsInWatchListResponse(items=items)
    
@plexWatchlistRoutes.delete("/items/{rating_key}", response_model=None, status_code=204)
async def delete_item_from_watchlist(
    rating_key: str,
    user_token: str = Query(alias="userToken"),
    use_case: RemoveWatchListItemUseCase = Depends(createRemoveWatchListItemUseCase),
):
    await use_case.execute(rating_key=rating_key, user_token=user_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
