from fastapi import APIRouter, Depends, Query, Response, status
from app.application.plex.queries.get_watchlist_query import GetWatchlistQuery
from app.factories.plex.watchlist_factory import create_get_watchlist_query
from app.adapters.http.schemas.plex.plex_watchlist_schemas import GetWatchlistItemsResponse
from app.application.plex.use_cases.remove_watchlist_item_use_case import RemoveWatchlistItemUseCase
from app.factories.plex.watchlist_factory import create_remove_watchlist_item_use_case


plex_watchlist_routes = APIRouter(prefix="/watchlist", tags=["plex-watchlist"])

@plex_watchlist_routes.get("/items", response_model=GetWatchlistItemsResponse)
async def get_items_in_watchlist(
    user_token: str = Query(alias="userToken"),
    query: GetWatchlistQuery = Depends(create_get_watchlist_query),
):
    items = await query.execute(user_token)
    return GetWatchlistItemsResponse(items=items)
    
@plex_watchlist_routes.delete("/items/{rating_key}", response_model=None, status_code=204)
async def delete_item_from_watchlist(
    rating_key: str,
    user_token: str = Query(alias="userToken"),
    use_case: RemoveWatchlistItemUseCase = Depends(create_remove_watchlist_item_use_case),
):
    await use_case.execute(rating_key=rating_key, user_token=user_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
