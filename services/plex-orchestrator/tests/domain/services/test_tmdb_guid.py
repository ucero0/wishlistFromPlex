from app.domain.services.tmdb_guid import (
    build_tmdb_movie_guid,
    build_tmdb_tv_guid,
    is_tmdb_guid,
    parse_agent_tmdb_id,
    parse_tmdb_guid,
    resolve_tmdb_tv_id_from_guid,
)


def test_parse_tmdb_guid():
    assert parse_tmdb_guid("tmdb://movie/550") == ("movie", 550)
    assert parse_tmdb_guid("tmdb://tv/1399") == ("tv", 1399)
    assert parse_tmdb_guid("plex://movie/1") is None


def test_build_and_is_tmdb_guid():
    guid = build_tmdb_movie_guid(42)
    assert guid == "tmdb://movie/42"
    assert is_tmdb_guid(guid) is True
    assert build_tmdb_tv_guid(7) == "tmdb://tv/7"


def test_parse_agent_tmdb_id():
    assert parse_agent_tmdb_id(
        "com.plexapp.agents.themoviedb://tv/1396?lang=en"
    ) == ("tv", 1396)
    assert parse_agent_tmdb_id("com.plexapp.agents.tmdb://movie/550") == (
        "movie",
        550,
    )
    assert resolve_tmdb_tv_id_from_guid("tmdb://tv/1399") == 1399
    assert (
        resolve_tmdb_tv_id_from_guid(
            "com.plexapp.agents.themoviedb://tv/456?lang=en"
        )
        == 456
    )
