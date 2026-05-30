"""Integration tests for PlexLibraryPathRepository."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.composition.persistence import build_plex_library_path_repository
from app.domain.models.plex_library_path import PlexLibraryPath


@pytest.mark.asyncio
async def test_sync_from_server_and_list_active(db_session: AsyncSession):
    repo = build_plex_library_path_repository(db_session)
    active_count = await repo.sync_from_server(
        [
            PlexLibraryPath(
                section_id="1",
                section_title="Movies",
                media_type="movie",
                path="/media/movies",
            ),
            PlexLibraryPath(
                section_id="2",
                section_title="TV",
                media_type="tvshow",
                path="/media/tv",
            ),
        ]
    )
    await db_session.commit()

    movies = await repo.list_active_by_media_type("movie")

    assert active_count == 2
    assert len(movies) == 1
    assert movies[0].path == "/media/movies"
    assert movies[0].section_title == "Movies"
