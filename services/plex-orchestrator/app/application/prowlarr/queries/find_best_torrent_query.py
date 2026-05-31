"""Query for getting torrents from search results, ordered by score."""
import logging
from typing import List
from app.domain.ports.external.prowlarr.torrent_search_provider import TorrentSearchProvider
from app.domain.services.torrent_quality_service import TorrentQualityService, MIN_SEEDERS
from app.domain.services.tv_show_torrent_title_filter import (
    torrent_title_conflicts_with_show_year,
)
from app.domain.models.torrent_search import TorrentSearchResult

logger = logging.getLogger(__name__)


class GetBestTorrentsQuery:
    """Query for getting torrents from search results, ordered by score."""
    
    def __init__(
        self, 
        search_provider: TorrentSearchProvider,
        quality_service: TorrentQualityService
    ):
        self.search_provider = search_provider
        self.quality_service = quality_service
    
    async def execute(
        self,
        query: str,
        media_type: str = "movie",
        *,
        show_year: int | None = None,
    ) -> List[TorrentSearchResult]:
        """
        Search for torrents, process, score, and return all results ordered by score.
        
        Args:
            query: Search query string
            media_type: Type of media ('movie' or 'tv')
            
        Returns:
            List of TorrentSearchResult objects ordered by quality score (highest first),
            or empty list if no results found
        """
        results = await self.search_provider.search_torrents(query, media_type)
        if not results:
            return []
        return self._process_search_results(
            results, media_type=media_type, show_year=show_year
        )

    def _score_filtered_results(
        self,
        results: List[TorrentSearchResult],
        *,
        media_type: str,
        show_year: int | None,
        min_seeders: int,
    ) -> tuple[list[TorrentSearchResult], int, int]:
        processed_results: list[TorrentSearchResult] = []
        skipped_no_seeders = 0
        skipped_year_mismatch = 0

        for result in results:
            try:
                title = result.title
                seeders = result.seeders or 0

                if media_type == "tv" and torrent_title_conflicts_with_show_year(
                    title, show_year
                ):
                    skipped_year_mismatch += 1
                    logger.debug(
                        "Skipping '%s' — title year does not match show year %s",
                        title[:80],
                        show_year,
                    )
                    continue

                if seeders < min_seeders:
                    skipped_no_seeders += 1
                    logger.debug(
                        "Skipping '%s...' - seeders: %s (min %s)",
                        title[:50],
                        seeders,
                        min_seeders,
                    )
                    continue

                quality_info = self.quality_service.parse_quality_from_title(title)
                quality_score = self.quality_service.calculate_quality_score(
                    title,
                    quality_info,
                    seeders,
                )

                result.quality_info = quality_info
                result.quality_score = quality_score
                processed_results.append(result)
            except Exception as e:
                logger.warning(f"Error processing search result: {e}")
                continue

        processed_results.sort(key=lambda x: x.quality_score, reverse=True)
        return processed_results, skipped_no_seeders, skipped_year_mismatch

    def _process_search_results(
        self,
        results: List[TorrentSearchResult],
        *,
        media_type: str = "movie",
        show_year: int | None = None,
    ) -> List[TorrentSearchResult]:
        """Process and score TorrentSearchResult objects with quality information."""
        logger.info(f"Processing {len(results)} validated search results")

        processed_results, skipped_no_seeders, skipped_year_mismatch = (
            self._score_filtered_results(
                results,
                media_type=media_type,
                show_year=show_year,
                min_seeders=MIN_SEEDERS,
            )
        )

        if skipped_year_mismatch > 0:
            logger.info(
                "Skipped %s TV result(s) whose title year does not match show year %s",
                skipped_year_mismatch,
                show_year,
            )
        if skipped_no_seeders > 0:
            logger.info(
                "Skipped %s results with seeders below minimum (%s)",
                skipped_no_seeders,
                MIN_SEEDERS,
            )
        logger.info(f"Processed {len(processed_results)} valid results after filtering")

        return processed_results
