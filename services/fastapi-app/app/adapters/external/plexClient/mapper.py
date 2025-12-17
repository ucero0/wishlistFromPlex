"""Mapper for converting between Plex external schemas and domain models."""
from app.infrastructure.externalApis.plex.plexClient.schemas import PlexWatchlistItemDTO
from app.domain.models.media import MediaItem

def to_external(media: MediaItem) -> PlexWatchlistItemDTO:
    """Map MediaItem to PlexWatchlistItemDTO external schema."""
    return PlexWatchlistItemDTO(
        guid=media.guid,
        ratingKey=media.ratingKey,
        title=media.title,
        type=media.type,
        year=media.year,
    )

def to_domain(dto: PlexWatchlistItemDTO) -> MediaItem:
    """Map PlexWatchlistItemDTO to MediaItem domain model."""

    return MediaItem(
        guid=dto.guid,
        ratingKey=dto.ratingKey,
        title=dto.title,
        type=dto.type,
        year=dto.year,
    )



