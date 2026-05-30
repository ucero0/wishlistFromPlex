from pydantic import BaseModel
from app.domain.models.media import MediaItem
from typing import List


class GetWatchlistItemsResponse(BaseModel):
    items: List[MediaItem]