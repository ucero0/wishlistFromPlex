from typing import Protocol

from app.domain.models.media import MediaItem


class TmdbWatchlistProvider(Protocol):
    async def get_account_id(self, access_token: str) -> int: ...

    async def get_watchlist(self, account_id: int, access_token: str) -> list[MediaItem]: ...

    async def remove_from_watchlist(
        self,
        account_id: int,
        access_token: str,
        media_type: str,
        media_id: int,
    ) -> None: ...

    async def add_to_watchlist(
        self,
        account_id: int,
        access_token: str,
        media_type: str,
        media_id: int,
    ) -> None: ...
