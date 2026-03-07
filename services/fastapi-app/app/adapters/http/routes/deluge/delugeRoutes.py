from typing import List

from fastapi import APIRouter, Depends

from app.adapters.http.routes.deluge.helpers import (
    DETAIL_TORRENT_NAME_NOT_FOUND,
    ensure_torrent_found,
    ensure_torrents_found,
    to_torrent_response,
    to_torrent_responses,
)
from app.adapters.http.schemas.deluge.delugeSchemas import (
    DelugeTorrentStatusResponse,
    DelugeRemoveRequest,
)
from app.application.deluge.queries.getTorrentStatus import (
    GetTorrentsStatusQuery,
    GetTorrentStatusQuery,
    GetTorrentByNameQuery,
    GetCompletedTorrentsQuery,
    GetDownloadingTorrentsQuery,
)
from app.application.deluge.useCases.removeTorrent import RemoveTorrentUseCase
from app.factories.deluge.delugeFactory import (
    createGetTorrentsStatusQuery,
    createGetTorrentStatusQuery,
    createRemoveTorrentUseCase,
    createGetTorrentByNameQuery,
    createGetCompletedTorrentsQuery,
    createGetDownloadingTorrentsQuery,
)

torrents_routes = APIRouter(prefix="/torrents", tags=["deluge"])


@torrents_routes.get("", response_model=List[DelugeTorrentStatusResponse])
async def get_torrents(
    query: GetTorrentsStatusQuery = Depends(createGetTorrentsStatusQuery),
):
    """Get all torrents from Deluge."""
    torrents = await query.execute()
    found = ensure_torrents_found(torrents)
    return to_torrent_responses(found)


@torrents_routes.get("/completed", response_model=List[DelugeTorrentStatusResponse])
async def get_completed_torrents(
    query: GetCompletedTorrentsQuery = Depends(createGetCompletedTorrentsQuery),
):
    """Get only completed torrents from Deluge."""
    torrents = await query.execute()
    found = ensure_torrents_found(torrents)
    return to_torrent_responses(found)


@torrents_routes.get("/downloading", response_model=List[DelugeTorrentStatusResponse])
async def get_downloading_torrents(
    query: GetDownloadingTorrentsQuery = Depends(createGetDownloadingTorrentsQuery),
):
    """Get only downloading torrents from Deluge."""
    torrents = await query.execute()
    found = ensure_torrents_found(torrents)
    return to_torrent_responses(found)


@torrents_routes.get("/by-hash/{hash}", response_model=DelugeTorrentStatusResponse)
async def get_torrent_by_hash(
    hash: str,
    query: GetTorrentStatusQuery = Depends(createGetTorrentStatusQuery),
):
    """Get the status of a torrent from Deluge by its hash."""
    torrent = await query.execute(hash)
    return to_torrent_response(torrent)


@torrents_routes.get("/by-name/{name}", response_model=DelugeTorrentStatusResponse)
async def get_torrent_by_name(
    name: str,
    query: GetTorrentByNameQuery = Depends(createGetTorrentByNameQuery),
):
    """Get a torrent by its name from Deluge."""
    torrent = await query.execute(name)
    found = ensure_torrent_found(torrent, detail=DETAIL_TORRENT_NAME_NOT_FOUND)
    return to_torrent_response(found)


@torrents_routes.delete("", response_model=bool)
async def remove_torrent(
    request: DelugeRemoveRequest,
    use_case: RemoveTorrentUseCase = Depends(createRemoveTorrentUseCase),
):
    """Remove a torrent from Deluge."""
    return await use_case.execute(request.hash, request.remove_data)