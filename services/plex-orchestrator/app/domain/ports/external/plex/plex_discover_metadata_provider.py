"""Port for Plex Discover show metadata (external guids)."""
from typing import Protocol


class PlexDiscoverMetadataProvider(Protocol):
    async def get_metadata_guids(
        self,
        rating_key: str,
        user_token: str,
    ) -> list[str]:
        """Return guid strings attached to a Discover show metadata item."""
        ...
