"""Mapper for converting between Deluge external schemas and domain models."""
from typing import Dict, List
from app.domain.models.torrent import Torrent, ListTorrents
from app.infrastructure.externalApis.deluge.schemas import ExternalDelugeTorrentStatusResponse


def to_domain(rawTorrentsStatus: List[ExternalDelugeTorrentStatusResponse]) -> ListTorrents:
    """Map Deluge RPC response to domain Torrent model."""
    domain_torrents = []
    for rawTorrent in rawTorrentsStatus:
        domain_torrent = Torrent(
            torrent_hash=rawTorrent.hash,
            name=rawTorrent.name,
            state=rawTorrent.state,
            progress=rawTorrent.progress,
            total_size=rawTorrent.total_done,
            download_speed=rawTorrent.download_payload_rate,
            eta=rawTorrent.eta,
        )
        domain_torrents.append(domain_torrent)
    return domain_torrents


