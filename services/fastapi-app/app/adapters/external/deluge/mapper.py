"""Mapper for converting between Deluge external schemas and domain models."""
from typing import Dict, List
from app.infrastructure.deluge.schemas import RpcStatusResponse, TorrentStatusResponse
from app.domain.models.torrent import Torrent, TorrentStatus


def map_deluge_status_to_domain_status(state: str) -> TorrentStatus:
    """Map Deluge state string to domain TorrentStatus enum."""
    state_lower = state.lower()
    status_map = {
        "queued": TorrentStatus.QUEUED,
        "downloading": TorrentStatus.DOWNLOADING,
        "seeding": TorrentStatus.SEEDING,
        "paused": TorrentStatus.PAUSED,
        "checking": TorrentStatus.CHECKING,
        "error": TorrentStatus.ERROR,
        "completed": TorrentStatus.COMPLETED,
        "removed": TorrentStatus.REMOVED,
    }
    return status_map.get(state_lower, TorrentStatus.QUEUED)


def map_rpc_response_to_domain(
    torrent_id: str,
    rpc_data: Dict,
    guid_plex: str
) -> Torrent:
    """Map Deluge RPC response to domain Torrent model."""
    return Torrent(
        guid_plex=guid_plex,
        torrent_hash=torrent_id,
        name=rpc_data.get("name"),
        status=map_deluge_status_to_domain_status(rpc_data.get("state", "queued")),
        progress=rpc_data.get("progress", 0.0),
        total_size=rpc_data.get("total_done"),
        downloaded=rpc_data.get("total_done", 0),
        uploaded=rpc_data.get("total_uploaded", 0),
        download_speed=rpc_data.get("download_payload_rate", 0),
        upload_speed=rpc_data.get("upload_payload_rate", 0),
        num_seeds=rpc_data.get("num_seeds", 0),
        num_peers=rpc_data.get("num_peers", 0),
        eta=rpc_data.get("eta", -1),
    )


def map_torrent_status_response_to_domain(
    response: TorrentStatusResponse,
    guid_plex: str
) -> Torrent:
    """Map TorrentStatusResponse to domain Torrent model."""
    return Torrent(
        guid_plex=guid_plex,
        torrent_hash=response.uid,
        name=response.name,
        status=map_deluge_status_to_domain_status(response.state),
        progress=response.progress,
        eta=response.eta or -1,
    )

