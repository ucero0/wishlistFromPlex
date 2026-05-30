"""Blacklist torrents API: list, get, add, remove by Prowlarr GUID."""
from fastapi import APIRouter, Depends, HTTPException

from app.adapters.http.schemas.blacklist_torrent import (
    AddToBlacklistRequest,
    AddToBlacklistByHashRequest,
    AddToBlacklistResponse,
    BlacklistTorrentItem,
    BlacklistTorrentListResponse,
)
from app.factories.blacklist_torrent import (
    create_add_torrent_to_blacklist_use_case,
    create_add_torrent_to_blacklist_by_hash_use_case,
    create_list_blacklist_torrents_query,
    create_get_blacklist_torrent_by_guid_query,
    create_remove_torrent_from_blacklist_use_case,
)
from app.application.blacklist_torrent.use_cases import (
    AddTorrentToBlacklistUseCase,
    AddTorrentToBlacklistByHashUseCase,
    RemoveTorrentFromBlacklistUseCase,
)
from app.application.blacklist_torrent.queries import (
    ListBlacklistTorrentsQuery,
    GetBlacklistTorrentByGuidQuery,
)

blacklist_torrent_routes = APIRouter(prefix="/blacklist-torrents", tags=["blacklist-torrents"])


@blacklist_torrent_routes.get("", response_model=BlacklistTorrentListResponse)
async def list_blacklist_torrents(
    query: ListBlacklistTorrentsQuery = Depends(create_list_blacklist_torrents_query),
):
    """List all blacklisted torrents (newest first)."""
    items = await query.execute()
    return BlacklistTorrentListResponse(
        items=[
            BlacklistTorrentItem(
                id=e.id,
                guid_prowlarr=e.guid_prowlarr,
                reason=e.reason,
                name=e.name,
                year=e.year,
                type=e.type,
                created_at=e.created_at,
            )
            for e in items
        ],
        total=len(items),
    )


@blacklist_torrent_routes.get("/{guid_prowlarr}", response_model=BlacklistTorrentItem)
async def get_blacklist_torrent_by_guid(
    guid_prowlarr: str,
    query: GetBlacklistTorrentByGuidQuery = Depends(create_get_blacklist_torrent_by_guid_query),
):
    """Get a single blacklist entry by Prowlarr GUID."""
    entry = await query.execute(guid_prowlarr)
    if entry is None:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")
    return BlacklistTorrentItem(
        id=entry.id,
        guid_prowlarr=entry.guid_prowlarr,
        reason=entry.reason,
        name=entry.name,
        year=entry.year,
        type=entry.type,
        created_at=entry.created_at,
    )


@blacklist_torrent_routes.post("/by-hash", response_model=AddToBlacklistResponse)
async def add_torrent_to_blacklist_by_hash(
    request: AddToBlacklistByHashRequest,
    use_case: AddTorrentToBlacklistByHashUseCase = Depends(
        create_add_torrent_to_blacklist_by_hash_use_case
    ),
):
    """
    Add a torrent to the blacklist by its hash (uid). Looks up the torrent in the DB to get
    Prowlarr GUID and title/year/type, then adds to blacklist. Use when you have the Deluge/torrent
    hash but not the GUID. Returns 404 if no torrent download is found for the hash.
    """
    result = await use_case.execute(request.torrent_hash, request.reason)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No torrent download found for hash '{request.torrent_hash}'",
        )
    return AddToBlacklistResponse(
        guid_prowlarr=result.guid_prowlarr,
        reason=result.reason,
        id=result.id,
        name=result.name,
        year=result.year,
        type=result.type,
    )


@blacklist_torrent_routes.post("", response_model=AddToBlacklistResponse)
async def add_torrent_to_blacklist(
    request: AddToBlacklistRequest,
    use_case: AddTorrentToBlacklistUseCase = Depends(create_add_torrent_to_blacklist_use_case),
):
    """
    Add a torrent (by Prowlarr GUID) to the blacklist so it is not sent to Deluge again.
    reason: e.g. "infected", "unhealthy"
    """
    result = await use_case.execute(
        request.guid_prowlarr,
        request.reason,
        name=request.name,
        year=request.year,
        media_type=request.type,
    )
    return AddToBlacklistResponse(
        guid_prowlarr=result.guid_prowlarr,
        reason=result.reason,
        id=result.id,
        name=result.name,
        year=result.year,
        type=result.type,
    )


@blacklist_torrent_routes.delete("/{guid_prowlarr}")
async def remove_torrent_from_blacklist(
    guid_prowlarr: str,
    use_case: RemoveTorrentFromBlacklistUseCase = Depends(create_remove_torrent_from_blacklist_use_case),
):
    """Remove a torrent from the blacklist by Prowlarr GUID."""
    removed = await use_case.execute(guid_prowlarr)
    if not removed:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")
    return {"message": "Removed from blacklist", "guid_prowlarr": guid_prowlarr}
