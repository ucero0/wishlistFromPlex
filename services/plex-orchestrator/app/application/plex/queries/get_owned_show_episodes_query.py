"""List TV episodes already present in the local Plex library."""
from app.domain.models.tv_episode import TvEpisode
from app.domain.ports.external.plex.plex_server_library_provider import (
    PlexServerLibraryProvider,
)
from app.domain.services.tmdb_guid import parse_tmdb_guid


class GetOwnedShowEpisodesQuery:
    def __init__(self, library_provider: PlexServerLibraryProvider):
        self._library_provider = library_provider

    async def execute(self, show_guid: str) -> list[TvEpisode]:
        resolved_guid = show_guid
        parsed = parse_tmdb_guid(show_guid)
        if parsed:
            _, tmdb_id = parsed
            plex_guid = await self._library_provider.resolve_show_guid_for_tmdb_id(
                tmdb_id
            )
            if not plex_guid:
                return []
            resolved_guid = plex_guid

        episodes = await self._library_provider.get_owned_show_episodes(resolved_guid)
        return sorted(episodes, key=lambda ep: (ep.season, ep.episode))
