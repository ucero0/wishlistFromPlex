from pydantic import BaseModel
from app.domain.models.media import MediaItem
from typing import List
class GetItemsInWatchListResponse(BaseModel):
    items: List[MediaItem]