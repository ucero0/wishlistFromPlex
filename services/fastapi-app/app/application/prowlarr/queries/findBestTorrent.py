"""Query for finding the best torrent from search results."""
import logging
from typing import Optional, List
from app.domain.ports.external.prowlarr.torrent_search_provider import TorrentSearchProvider
from app.domain.services.torrent_quality_service import TorrentQualityService, MIN_SEEDERS
from app.domain.models.torrent_search import TorrentSearchResult

logger = logging.getLogger(__name__)


class FindBestTorrentQuery:
    """Query for finding the best torrent from search results."""
    
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
    ) -> Optional[TorrentSearchResult]:
        """
        Search for torrents, process, score, and return the best match.
        
        Args:
            query: Search query string
            media_type: Type of media ('movie' or 'tv')
            
        Returns:
            The best TorrentSearchResult, or None if no results found
        """
        # 1. Search via adapter
        results = await self.search_provider.search_torrents(query, media_type)
        if not results:
            return None
        
        # 2. Process and score (orchestration)
        processed_results = self._process_search_results(results)
        if not processed_results:
            return None
        
        # 3. Get best result
        best_result = processed_results[0]
        return best_result
    
    def _process_search_results(self, results: List[TorrentSearchResult]) -> List[TorrentSearchResult]:
        """Process and score TorrentSearchResult objects with quality information."""
        processed_results = []
        skipped_no_seeders = 0
        
        logger.info(f"Processing {len(results)} validated search results")
        
        for result in results:
            try:
                title = result.title
                seeders = result.seeders or 0
                
                if seeders < MIN_SEEDERS:
                    skipped_no_seeders += 1
                    logger.debug(f"Skipping '{title[:50]}...' - seeders: {seeders}")
                    continue
                
                # Use domain service for quality parsing/scoring
                quality_info = self.quality_service.parse_quality_from_title(title)
                quality_score = self.quality_service.calculate_quality_score(
                    title, 
                    quality_info, 
                    seeders
                )
                
                result.quality_info = quality_info
                result.quality_score = quality_score
                processed_results.append(result)
            except Exception as e:
                logger.warning(f"Error processing search result: {e}")
                continue
        
        # Sort by quality score (highest first)
        processed_results.sort(key=lambda x: x.quality_score, reverse=True)
        
        if skipped_no_seeders > 0:
            logger.info(f"Skipped {skipped_no_seeders} results with seeders < {MIN_SEEDERS}")
        logger.info(f"Processed {len(processed_results)} valid results after filtering")
        
        return processed_results

