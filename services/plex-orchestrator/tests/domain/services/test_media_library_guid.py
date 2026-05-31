from app.domain.models.media import MediaItem, MediaType
from app.domain.services.media_library_guid import library_guid_for_media


def test_library_guid_for_media_prefers_plex_library_guid():
    item = MediaItem(
        guid="tmdb://tv/1434",
        type=MediaType.SHOW,
        plex_library_guid="plex://show/abc123",
    )
    assert library_guid_for_media(item) == "plex://show/abc123"


def test_library_guid_for_media_falls_back_to_watchlist_guid():
    item = MediaItem(guid="tmdb://tv/1434", type=MediaType.SHOW)
    assert library_guid_for_media(item) == "tmdb://tv/1434"
