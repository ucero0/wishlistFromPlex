"""Orchestration service for coordinating watchlist sync, torrent search, and downloads."""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.modules.plex.service import get_watchlist_items_not_in_plexLibrary
from app.modules.torrent_search.service import TorrentSearchService
from app.modules.plex.schemas import PlexItemData


logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Orchestration service that coordinates the full workflow:
    1. Sync Plex watchlists
    2. Find new items that need torrent searches
    3. Search for torrents via Prowlarr
    4. Automatically add best matches to Deluge
    """

    def __init__(self, db: Session):
        self.db = db
        self.torrent_search_service = TorrentSearchService(db)

    async def run_full_workflow(
        self,
        auto_search: bool = True,
        force_research: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete orchestration workflow.
        
        Args:
            auto_search: If True, automatically search for torrents for new items
            force_research: If True, re-search items that already have search results
        
        Returns:
            Dictionary with workflow execution summary
        """
        start_time = datetime.now(timezone.utc)
        errors: List[str] = []
        
        logger.info("Starting orchestration workflow")
        
        # Step 1: get all watchlists items that are not in the plexLibrary
        logger.info("Step 1: Getting all watchlists items that are not in the plexLibrary")

        watchlist_items: List[PlexItemData] = await get_watchlist_items_not_in_plexLibrary(db=self.db)
        logger.info(f"Found {len(watchlist_items)} watchlist items that are not in the plexLibrary")

        # Step 2: search for torrents via Prowlarr
        logger.info("Step 2: Searching for torrents via Prowlarr")
        for item in watchlist_items:
            search_result = await self.torrent_search_service.search_by_query(f"{item.title} {item.year}", item.type)
            logger.info(f"Search result: {search_result}")





 
