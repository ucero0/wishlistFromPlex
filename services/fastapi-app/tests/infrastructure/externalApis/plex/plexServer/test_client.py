import logging

import httpx
import pytest
import respx

from app.infrastructure.externalApis.plex.plexServer.client import PlexServerLibraryApiClient
from app.infrastructure.externalApis.plex.plexServer.schemas import (
    PlexLibraryAllResponse,
    PlexLibraryLocationsByMediaResponse,
)


@pytest.fixture
def plex_server_url(monkeypatch: pytest.MonkeyPatch) -> str:
    url = "http://plex.local:32400"
    monkeypatch.setattr(
        "app.infrastructure.externalApis.plex.plexServer.client.settings.plex_server_url",
        url,
    )
    return url


@pytest.mark.asyncio
@respx.mock
async def test_get_library_items_raw_returns_typed_response(plex_server_url: str) -> None:
    route = respx.get(url__startswith=f"{plex_server_url}/library/all").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "size": 1,
                    "Metadata": [{"guid": "plex://movie/123"}],
                }
            },
        )
    )

    client = PlexServerLibraryApiClient(token="unused")
    result = await client.get_library_items_raw(
        user_token="user-token",
        guid="plex://movie/123",
        media_type=1,
    )

    assert route.called
    assert isinstance(result, PlexLibraryAllResponse)
    assert result.MediaContainer["size"] == 1
    assert result.MediaContainer["Metadata"][0]["guid"] == "plex://movie/123"


@pytest.mark.asyncio
@respx.mock
async def test_get_library_items_raw_sends_expected_query_params(
    plex_server_url: str,
) -> None:
    route = respx.get(url__startswith=f"{plex_server_url}/library/all").mock(
        return_value=httpx.Response(200, json={"MediaContainer": {"size": 0}})
    )

    client = PlexServerLibraryApiClient(token="unused")
    await client.get_library_items_raw(
        user_token="user-token",
        guid="plex://show/999",
        media_type=2,
    )

    request_url = str(route.calls[0].request.url)
    assert "guid=plex%3A%2F%2Fshow%2F999" in request_url
    assert "X-Plex-Token=user-token" in request_url
    assert "media_type" not in request_url
    assert "type=2" in request_url


@pytest.mark.asyncio
@respx.mock
async def test_get_library_items_raw_without_media_type_omits_type_param(
    plex_server_url: str,
) -> None:
    route = respx.get(url__startswith=f"{plex_server_url}/library/all").mock(
        return_value=httpx.Response(200, json={"MediaContainer": {"size": 0}})
    )

    client = PlexServerLibraryApiClient(token="unused")
    await client.get_library_items_raw(
        user_token="user-token",
        guid="plex://movie/abc",
    )

    request_url = str(route.calls[0].request.url)
    assert "guid=plex%3A%2F%2Fmovie%2Fabc" in request_url
    assert "X-Plex-Token=user-token" in request_url
    assert "type=" not in request_url


@pytest.mark.asyncio
@respx.mock
async def test_get_library_items_raw_raises_on_http_error(plex_server_url: str) -> None:
    respx.get(url__startswith=f"{plex_server_url}/library/all").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )

    client = PlexServerLibraryApiClient(token="unused")
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_library_items_raw(
            user_token="bad-token",
            guid="plex://movie/123",
            media_type=1,
        )


@pytest.mark.asyncio
@respx.mock
async def test_get_library_locations_by_media_raw_filters_and_normalizes_media_types(
    plex_server_url: str,
) -> None:
    route = respx.get(url__startswith=f"{plex_server_url}/library/sections").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Directory": [
                        {
                            "key": "1",
                            "title": "Movies",
                            "type": "movie",
                            "Location": [{"path": "/data/movies"}],
                        },
                        {
                            "key": "2",
                            "title": "TV Shows",
                            "type": "show",
                            "Location": [{"path": "/data/tvshows"}],
                        },
                        {
                            "key": "3",
                            "title": "Music",
                            "type": "artist",
                            "Location": [{"path": "/data/music"}],
                        },
                    ]
                }
            },
        )
    )

    client = PlexServerLibraryApiClient(token="unused")
    result = await client.get_library_locations_by_media_raw(user_token="user-token")

    assert route.called
    assert isinstance(result, PlexLibraryLocationsByMediaResponse)
    assert len(result.items) == 3
    assert result.items[0].media_type == "movie"
    assert result.items[0].locations == ["/data/movies"]
    assert result.items[1].media_type == "tvshow"
    assert result.items[1].locations == ["/data/tvshows"]
    assert result.items[2].media_type == "other"
    assert result.items[2].locations == ["/data/music"]


@pytest.mark.asyncio
@respx.mock
async def test_get_library_locations_by_media_raw_ignores_empty_paths(
    plex_server_url: str,
) -> None:
    respx.get(url__startswith=f"{plex_server_url}/library/sections").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Directory": [
                        {
                            "key": "10",
                            "title": "Movies",
                            "type": "movie",
                            "Location": [{"path": "/ok/path"}, {"path": ""}, {}],
                        }
                    ]
                }
            },
        )
    )

    client = PlexServerLibraryApiClient(token="unused")
    result = await client.get_library_locations_by_media_raw(user_token="user-token")

    assert len(result.items) == 1
    assert result.items[0].locations == ["/ok/path"]


@pytest.mark.asyncio
@respx.mock
async def test_get_library_locations_by_media_raw_raises_on_http_error(
    plex_server_url: str,
) -> None:
    respx.get(url__startswith=f"{plex_server_url}/library/sections").mock(
        return_value=httpx.Response(500, json={"error": "server error"})
    )

    client = PlexServerLibraryApiClient(token="unused")
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_library_locations_by_media_raw(user_token="user-token")


@pytest.mark.asyncio
@respx.mock
async def test_partial_scan_library_raw_returns_true_on_success(
    plex_server_url: str,
) -> None:
    route = respx.get(url__startswith=f"{plex_server_url}/library/sections/2/refresh").mock(
        return_value=httpx.Response(200, json={})
    )

    client = PlexServerLibraryApiClient(token="unused")
    result = await client.partial_scan_library_raw(
        user_token="user-token",
        section_id=2,
        folder_path="/data/tvshows/Show A",
    )

    assert route.called
    assert result is True
    request_url = str(route.calls[0].request.url)
    assert "X-Plex-Token=user-token" in request_url
    assert "path=%2Fdata%2Ftvshows%2FShow%20A" in request_url


@pytest.mark.asyncio
@respx.mock
async def test_partial_scan_library_raw_raises_on_http_error(
    plex_server_url: str,
) -> None:
    respx.get(url__startswith=f"{plex_server_url}/library/sections/1/refresh").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )

    client = PlexServerLibraryApiClient(token="unused")
    with pytest.raises(httpx.HTTPStatusError):
        await client.partial_scan_library_raw(
            user_token="user-token",
            section_id=1,
            folder_path="/data/movies",
        )


@pytest.mark.asyncio
@respx.mock
async def test_logs_do_not_expose_plex_token(
    plex_server_url: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    respx.get(url__startswith=f"{plex_server_url}/library/all").mock(
        return_value=httpx.Response(200, json={"MediaContainer": {"size": 0}})
    )

    client = PlexServerLibraryApiClient(token="unused")
    with caplog.at_level(
        logging.DEBUG,
        logger="app.infrastructure.externalApis.plex.plexServer.client",
    ):
        await client.get_library_items_raw(
            user_token="super-secret-token",
            guid="plex://movie/abc",
            media_type=1,
        )

    scoped_records = [
        record.message
        for record in caplog.records
        if record.name == "app.infrastructure.externalApis.plex.plexServer.client"
    ]
    joined_logs = " ".join(scoped_records)
    assert "super-secret-token" not in joined_logs
    assert "X-Plex-Token" not in joined_logs
