"""Composition helpers for download queue deduplication."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pipelines.watchlist.queries.is_media_already_queued_query import (
    IsMediaAlreadyQueuedQuery,
)
from app.composition.persistence import (
    build_deferred_download_repository,
    build_active_download_repository,
)


def build_is_media_already_queued_query(
    session: AsyncSession,
) -> IsMediaAlreadyQueuedQuery:
    return IsMediaAlreadyQueuedQuery(
        build_active_download_repository(session),
        build_deferred_download_repository(session),
    )
