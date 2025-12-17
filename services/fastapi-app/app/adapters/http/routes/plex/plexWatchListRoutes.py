from fastapi import APIRouter, Depends, Response, status
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.factories.plex.plexWatchListFactory import createGetWatchListQuery
from app.adapters.http.schemas.plex.plexWatchListSchemas import GetItemsInWatchListResponse
from app.application.plex.useCases.removeWatchListItem import RemoveWatchListItemUseCase
from app.factories.plex.plexWatchListFactory import createRemoveWatchListItemUseCase
from app.domain.models.media import MediaItem


plexWatchlistRoutes = APIRouter(prefix="/watchlist", tags=["plex-watchlist"])

@plexWatchlistRoutes.get("/items", response_model=GetItemsInWatchListResponse)
async def getItemsInWatchList(userToken: str, query: GetWatchListQuery = Depends(createGetWatchListQuery)):
    items = await query.execute(userToken)
    return GetItemsInWatchListResponse(items=items)
    
@plexWatchlistRoutes.delete("/items/{guid}", response_model=None, status_code=204)
async def deleteItemFromWatchList(ratingKey: str, userToken: str, useCase: RemoveWatchListItemUseCase = Depends(createRemoveWatchListItemUseCase)):
    await useCase.execute(ratingKey=ratingKey, user_token=userToken)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
