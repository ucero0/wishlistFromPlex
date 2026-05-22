"""Query for testing Deluge RPC connection."""
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider


class TestDelugeConnectionQuery:
    def __init__(self, provider: DelugeProvider):
        self.provider = provider

    async def execute(self) -> ExternalConnectionStatus:
        return await self.provider.test_connection()
