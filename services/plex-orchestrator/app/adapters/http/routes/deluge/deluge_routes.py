from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters.http.routes.deluge.helpers import (
    DETAIL_TORRENT_NAME_NOT_FOUND,
    DETAIL_TORRENT_NOT_FOUND,
    ensure_torrent_found,
    to_torrent_response,
    to_torrent_responses,
)
from app.domain.errors.deluge import DelugeTorrentNotFoundError
from app.adapters.http.schemas.deluge.deluge_schemas import (
    DelugeTorrentStatusResponse,
    DelugeRemoveRequest,
)
from app.application.deluge.queries.get_torrent_status_query import (
    GetTorrentsStatusQuery,
    GetTorrentStatusQuery,
    GetTorrentByNameQuery,
    GetCompletedTorrentsQuery,
    GetDownloadingTorrentsQuery,
)
from app.application.deluge.use_cases.remove_torrent_use_case import RemoveTorrentUseCase
from app.factories.deluge.deluge_factory import (
    create_get_torrents_status_query,
    create_get_torrent_status_query,
    create_remove_torrent_use_case,
    create_get_torrent_by_name_query,
    create_get_completed_torrents_query,
    create_get_downloading_torrents_query,
)

torrents_routes = APIRouter(prefix="/torrents", tags=["deluge"])


@torrents_routes.get("", response_model=List[DelugeTorrentStatusResponse])
async def get_torrents(
    query: GetTorrentsStatusQuery = Depends(create_get_torrents_status_query),
):
    """Get all torrents from Deluge."""
    torrents = await query.execute()
    return to_torrent_responses(torrents)


@torrents_routes.get("/completed", response_model=List[DelugeTorrentStatusResponse])
async def get_completed_torrents(
    query: GetCompletedTorrentsQuery = Depends(create_get_completed_torrents_query),
):
    """Get only completed torrents from Deluge."""
    torrents = await query.execute()
    return to_torrent_responses(torrents)


@torrents_routes.get("/downloading", response_model=List[DelugeTorrentStatusResponse])
async def get_downloading_torrents(
    query: GetDownloadingTorrentsQuery = Depends(create_get_downloading_torrents_query),
):
    """Get only downloading torrents from Deluge."""
    torrents = await query.execute()
    return to_torrent_responses(torrents)


@torrents_routes.get("/by-hash/{hash}", response_model=DelugeTorrentStatusResponse)
async def get_torrent_by_hash(
    hash: str,
    query: GetTorrentStatusQuery = Depends(create_get_torrent_status_query),
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
    query: GetTorrentByNameQuery = Depends(create_get_torrent_by_name_query),
):
    """Get a torrent by its name from Deluge."""
    torrent = await query.execute(name)
    found = ensure_torrent_found(torrent, detail=DETAIL_TORRENT_NAME_NOT_FOUND)
    return to_torrent_response(found)


@torrents_routes.delete("", response_model=bool)
async def remove_torrent(
    request: DelugeRemoveRequest,
    use_case: RemoveTorrentUseCase = Depends(create_remove_torrent_use_case),
):
    """Remove a torrent from Deluge."""
    return await use_case.execute(request.hash, request.remove_data)