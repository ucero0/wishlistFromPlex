from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters.http.routes.deluge.helpers import (
    DETAIL_NO_COMPLETED_TORRENTS,
    DETAIL_NO_DOWNLOADING_TORRENTS,
    DETAIL_TORRENT_NAME_NOT_FOUND,
    DETAIL_TORRENT_NOT_FOUND,
    ensure_torrent_found,
    ensure_torrents_found,
    to_torrent_response,
    to_torrent_responses,
)
from app.domain.errors.deluge import DelugeTorrentNotFoundError
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
    return to_torrent_responses(
        ensure_torrents_found(torrents, detail=DETAIL_NO_COMPLETED_TORRENTS)
    )


@torrents_routes.get("/downloading", response_model=List[DelugeTorrentStatusResponse])
async def get_downloading_torrents(
    query: GetDownloadingTorrentsQuery = Depends(createGetDownloadingTorrentsQuery),
):
    """Get only downloading torrents from Deluge."""
    torrents = await query.execute()
    return to_torrent_responses(
        ensure_torrents_found(torrents, detail=DETAIL_NO_DOWNLOADING_TORRENTS)
    )


@torrents_routes.get("/by-hash/{hash}", response_model=DelugeTorrentStatusResponse)
async def get_torrent_by_hash(
    hash: str,
    query: GetTorrentStatusQuery = Depends(createGetTorrentStatusQuery),
):
    """Get the status of a torrent from Deluge by its hash."""
    try:
        torrent = await query.execute(hash)
    except DelugeTorrentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=DETAIL_TORRENT_NOT_FOUND,
        ) from exc
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