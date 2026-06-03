"""Mapper for converting between Deluge external schemas and domain models."""
from typing import Dict, List
from app.domain.models.torrent import Torrent, ListTorrents
from app.infrastructure.external_apis.deluge.schemas import ExternalDelugeTorrentStatusResponse

def to_domain_torrent(rawTorrent: ExternalDelugeTorrentStatusResponse) -> Torrent:
    """Map Deluge RPC response to domain Torrent model."""
    return Torrent(
            hash=rawTorrent.hash,
            file_name=rawTorrent.name,  # Translate external "name" to internal file_name
            state=rawTorrent.state,
            progress=rawTorrent.progress,
            total_size=rawTorrent.total_done,
            download_speed=rawTorrent.download_payload_rate,
            eta=rawTorrent.eta,
            time_added=rawTorrent.time_added,
            availability=rawTorrent.distributed_copies,
            time_since_download=rawTorrent.time_since_download,
            time_since_upload=rawTorrent.time_since_upload,
            last_seen_complete=rawTorrent.last_seen_complete,
            num_peers=rawTorrent.num_peers,
            num_seeds=rawTorrent.num_seeds,
            tracker_status=rawTorrent.tracker_status,
            active_time=rawTorrent.active_time,
        )

def to_domain_list_torrents(rawTorrentsStatus: List[ExternalDelugeTorrentStatusResponse]) -> ListTorrents:
    """Map Deluge RPC responses to domain ListTorrents model."""
    domain_torrents = []
    for rawTorrent in rawTorrentsStatus:
        domain_torrent = to_domain_torrent(rawTorrent)
        domain_torrents.append(domain_torrent)
    return ListTorrents(torrents=domain_torrents)


