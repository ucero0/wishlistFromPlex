from app.domain.ports.external.deluge.delugeProvider import DelugeProvider

class RemoveTorrentUseCase:
    def __init__(self, adapter: DelugeProvider):
        self.adapter = adapter

    async def execute(self, hash: str, remove_data: bool = False) -> bool:
        return await self.adapter.remove_torrent(hash, remove_data)