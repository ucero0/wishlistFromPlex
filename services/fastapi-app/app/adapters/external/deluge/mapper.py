"""Mapper for converting between Deluge external schemas and domain models."""
from typing import Dict, List
from app.domain.models.torrent import Torrent, ListTorrents
from app.infrastructure.externalApis.deluge.schemas import ExternalDelugeTorrentStatusResponse

def to_domain_torrent(rawTorrent: ExternalDelugeTorrentStatusResponse) -> Torrent:
    """Map Deluge RPC response to domain Torrent model."""
    return Torrent(
            hash=rawTorrent.hash,
            fileName=rawTorrent.name,  # Translate external "name" to internal "fileName"
            state=rawTorrent.state,
            progress=rawTorrent.progress,
            total_size=rawTorrent.total_done,
            download_speed=rawTorrent.download_payload_rate,
            eta=rawTorrent.eta,
            time_added=rawTorrent.time_added,
        )

def to_domain_list_torrents(rawTorrentsStatus: List[ExternalDelugeTorrentStatusResponse]) -> ListTorrents:
    """Map Deluge RPC response to domain Torrent model."""
    domain_torrents = []
    for rawTorrent in rawTorrentsStatus:
        domain_torrent = to_domain_torrent(rawTorrent)
        domain_torrents.append(domain_torrent)
    return domain_torrents


