"""Map TMDB watchlist payloads to domain media items."""
from app.domain.models.media import MediaItem, MediaType
from app.domain.services.tmdb_guid import build_tmdb_movie_guid, build_tmdb_tv_guid
from app.infrastructure.external_apis.tmdb.schemas import TMDBWatchlistItem


def _year_from_date(value: str | None) -> int | None:
    if not value or len(value) < 4:
        return None
    year_part = value[:4]
    return int(year_part) if year_part.isdigit() else None


def watchlist_item_to_media(item: TMDBWatchlistItem) -> MediaItem | None:
    media_type = (item.media_type or "").lower()
    if media_type == "movie":
        return MediaItem(
            guid=build_tmdb_movie_guid(item.id),
            rating_key=str(item.id),
            title=item.title,
            year=_year_from_date(item.release_date),
            type=MediaType.MOVIE,
        )
    if media_type == "tv":
        return MediaItem(
            guid=build_tmdb_tv_guid(item.id),
            rating_key=str(item.id),
            title=item.name,
            year=_year_from_date(item.first_air_date),
            type=MediaType.SHOW,
        )
    return None
