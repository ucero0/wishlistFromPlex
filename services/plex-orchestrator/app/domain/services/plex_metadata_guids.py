"""Extract and match external ids from Plex metadata Guid entries."""
from app.domain.services.tmdb_guid import build_tmdb_movie_guid, build_tmdb_tv_guid


def guid_entries_from_metadata(metadata: dict) -> list[str]:
    guids: list[str] = []
    primary = metadata.get("guid")
    if primary:
        guids.append(str(primary))
    for entry in metadata.get("Guid") or []:
        if isinstance(entry, dict):
            guid = entry.get("id")
            if guid:
                guids.append(str(guid))
        elif entry:
            guids.append(str(entry))
    return guids


def metadata_matches_tmdb_id(
    metadata: dict, tmdb_id: int, media_type: str
) -> bool:
    expected = (
        build_tmdb_movie_guid(tmdb_id)
        if media_type == "movie"
        else build_tmdb_tv_guid(tmdb_id)
    )
    short_expected = f"tmdb://{tmdb_id}"
    for guid in guid_entries_from_metadata(metadata):
        if guid == expected or guid == short_expected:
            return True
    return False
