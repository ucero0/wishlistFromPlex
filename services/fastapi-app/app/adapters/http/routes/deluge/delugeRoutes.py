from fastapi import APIRouter, Depends, HTTPException
from app.application.deluge.queries.getTorrentStatus import GetTorrentsStatusQuery, GetTorrentStatusQuery, GetTorrentByNameQuery
from app.application.deluge.useCases.removeTorrent import RemoveTorrentUseCase
from app.factories.deluge.delugeFactory import createGetTorrentsStatusQuery, createGetTorrentStatusQuery, createRemoveTorrentUseCase, createGetTorrentByNameQuery
from typing import List
from app.adapters.http.schemas.deluge.delugeSchemas import DelugeTorrentStatusResponse, DelugeRemoveRequest

torrentsRoutes = APIRouter(prefix="/torrents", tags=["deluge"])
@torrentsRoutes.get("", response_model=List[DelugeTorrentStatusResponse])
async def get_torrents(query: GetTorrentsStatusQuery = Depends(createGetTorrentsStatusQuery)):
    """Get all torrents from Deluge."""
    torrents = await query.execute()
    return [DelugeTorrentStatusResponse(**torrent.model_dump()) for torrent in torrents]

@torrentsRoutes.get("/by-hash/{hash}", response_model=DelugeTorrentStatusResponse)
async def get_torrent(hash: str, query: GetTorrentStatusQuery = Depends(createGetTorrentStatusQuery)):
    """Get the status of a torrent from Deluge."""
    torrent = await query.execute(hash)
    return DelugeTorrentStatusResponse(**torrent.model_dump())

@torrentsRoutes.get("/by-name/{name}", response_model=DelugeTorrentStatusResponse)
async def get_torrents_by_name(name: str, query: GetTorrentByNameQuery = Depends(createGetTorrentByNameQuery)):
    """Get a torrent by its name from Deluge."""
    torrent = await query.execute(name)
    if not torrent:
        raise HTTPException(status_code=404, detail="Torrent name not found in deluge")
    return DelugeTorrentStatusResponse(**torrent.model_dump())

@torrentsRoutes.delete("", response_model=bool)
async def remove_torrent(
    request: DelugeRemoveRequest,
    useCase: RemoveTorrentUseCase = Depends(createRemoveTorrentUseCase)
):
    """Remove a torrent from Deluge."""
    return await useCase.execute(request.hash, request.remove_data)