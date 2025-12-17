from fastapi import APIRouter, Depends
from app.application.deluge.queries.getTorrentStatus import GetTorrentStatusQuery
from app.factories.deluge.delugeFactory import createGetTorrentStatusQuery
from typing import List
from app.adapters.http.schemas.deluge.delugeSchemas import DelugeTorrentStatusResponse

torrentsRoutes = APIRouter(prefix="/torrents", tags=["deluge"])
@torrentsRoutes.get("", response_model=List[DelugeTorrentStatusResponse])
async def get_torrents(query: GetTorrentStatusQuery = Depends(createGetTorrentStatusQuery)):
    """Get all torrents from Deluge."""
    torrents = await query.execute()
    return [DelugeTorrentStatusResponse(**torrent.model_dump()) for torrent in torrents]