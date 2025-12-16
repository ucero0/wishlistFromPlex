from app.domain.ports.external.deluge.delugeProvider import DelugeProvider
from app.domain.models.torrent import ListTorrents

class GetTorrentStatusQuery:
    """Query to get the status of a torrent."""
    def __init__(self, provider: DelugeProvider):
        self.provider = provider

    async def execute(self) -> ListTorrents:
        """Execute the query to get the status of a torrent."""
        torrents = await self.provider.get_torrents()
        return torrents
