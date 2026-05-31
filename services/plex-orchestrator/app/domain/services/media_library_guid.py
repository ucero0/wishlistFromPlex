"""Choose which guid to use for Plex server library lookups."""
from app.domain.models.active_download import ActiveDownload
from app.domain.models.media import MediaItem


def library_guid_for_media(item: MediaItem) -> str:
    return item.plex_library_guid or item.guid


def library_guid_for_download(download: ActiveDownload) -> str:
    return download.plex_library_guid or download.plex_guid
