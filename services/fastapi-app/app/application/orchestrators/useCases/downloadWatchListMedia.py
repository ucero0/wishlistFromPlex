from app.application.orchestrators.queries.getPlexWatchlistsFromUsers import GetPlexWatchlistsFromUsers
from app.application.plex.queries.getPlexUsers import GetPlexUserQuery
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.application.prowlarr.useCases.downloadTorrent import DownloadTorrentUseCase
from app.application.prowlarr.queries.findBestTorrent import GetBestTorrentsQuery
from app.application.plex.queries.getPlexServerItem import IsItemInLibraryQuery
from app.application.deluge.queries.getTorrentStatus import GetTorrentByNameQuery
from app.application.plex.useCases.removeWatchListItem import RemoveWatchListItemUseCase
from app.application.antivirus.queries.checkInfectedByGuidProwlarr import CheckInfectedByGuidProwlarrQuery
from app.application.torrentDownload.useCases.createTorrentDownload import CreateTorrentDownloadUseCase
from app.application.torrentDownload.queries.getTorrentDownload import IsGuidPlexDownloadingQuery
from app.application.orchestrators.useCases.syncTorrentDownloadWithDeluge import SyncTorrentDownloadWithDelugeUseCase
from app.application.tmdb.queries.getOriginalTitle import GetOriginalTitleFromTMDBQuery
import logging
import asyncio
import time
from typing import Optional, Tuple
from app.domain.models.torrentDownload import TorrentDownload
from app.domain.models.torrent_search import TorrentSearchResult
from app.domain.models.torrent import Torrent
logger = logging.getLogger(__name__)

class DownloadWatchListMediaUseCase:

    def __init__(self, 
    getPlexUserQuery: GetPlexUserQuery,
    getWatchListQuery: GetWatchListQuery,
    downloadTorrentUseCase: DownloadTorrentUseCase,
    findBestTorrentQuery: GetBestTorrentsQuery, 
    isItemInLibraryQuery: IsItemInLibraryQuery,
    getTorrentByNameQuery: GetTorrentByNameQuery,
    removeWatchListItemUseCase: RemoveWatchListItemUseCase,
    checkInfectedByGuidProwlarrQuery: CheckInfectedByGuidProwlarrQuery,
    createTorrentDownloadUseCase: CreateTorrentDownloadUseCase,
    isGuidPlexDownloadingQuery: IsGuidPlexDownloadingQuery,
    syncTorrentDownloadWithDelugeUseCase: SyncTorrentDownloadWithDelugeUseCase,
    getOriginalTitleFromTMDBQuery: GetOriginalTitleFromTMDBQuery):
        self.getPlexWatchlistsFromUsers = GetPlexWatchlistsFromUsers(getPlexUserQuery, getWatchListQuery)
        self.downloadTorrentUseCase = downloadTorrentUseCase
        self.findBestTorrentQuery = findBestTorrentQuery
        self.isItemInLibraryQuery = isItemInLibraryQuery
        self.getTorrentByNameQuery = getTorrentByNameQuery
        self.removeWatchListItemUseCase = removeWatchListItemUseCase
        self.checkInfectedByGuidProwlarrQuery = checkInfectedByGuidProwlarrQuery
        self.createTorrentDownloadUseCase = createTorrentDownloadUseCase
        self.isGuidPlexDownloadingQuery = isGuidPlexDownloadingQuery
        self.syncTorrentDownloadWithDelugeUseCase = syncTorrentDownloadWithDelugeUseCase
        self.getOriginalTitleFromTMDBQuery = getOriginalTitleFromTMDBQuery
    
    async def _get_search_query(self, watchlist) -> str:
        """Get the search query, using originalTitle from TMDB for Spanish movies."""
        # Try to get original title and language from TMDB
        tmdb_result = await self.getOriginalTitleFromTMDBQuery.execute(watchlist)
        
        if tmdb_result:
            original_title, original_language = tmdb_result
            # Check if it's a Spanish movie using original_language from TMDB
            if original_language == "es":
                logger.info(f"Using original title '{original_title}' for Spanish movie '{watchlist.title}' (original_language: {original_language})")
                return f"{original_title} {watchlist.year}"
        
        # Default to regular title
        return f"{watchlist.title} {watchlist.year}"
    
    async def _should_skip_watchlist_item(
        self, 
        watchlist, 
        user_token: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a watchlist item should be skipped and why.
        
        Args:
            watchlist: The watchlist item to check
            user_token: Plex user token
            
        Returns:
            Tuple of (should_skip: bool, reason: Optional[str])
            - should_skip: True if item should be skipped
            - reason: Reason for skipping (None if should not skip)
        """
        # Check if item is already in library
        if await self.isItemInLibraryQuery.execute(user_token, watchlist):
            logger.info(f"Removing {watchlist.title} from watchlist because it is already in the library")
            await self.removeWatchListItemUseCase.execute(watchlist.ratingKey, user_token)
            return True, "already_in_library"
        
        # Check if torrent is already downloading
        if await self.isGuidPlexDownloadingQuery.execute(watchlist.guid):
            logger.error(f"Torrent {watchlist.title} is already downloading, skipping")
            await self.removeWatchListItemUseCase.execute(watchlist.ratingKey, user_token)
            return True, "already_downloading"
        
        return False, None
    
    async def _process_watchlist_item(
        self, 
        watchlist, 
        user_token: str
    ) -> bool:
        """
        Process a single watchlist item: search, download, and track torrent.
        
        Args:
            watchlist: The watchlist item to process
            user_token: Plex user token
            
        Returns:
            True if successfully processed, False otherwise
        """
        query = await self._get_search_query(watchlist)
        torrent_search_results = await self.findBestTorrentQuery.execute(query)
        
        if not torrent_search_results:
            logger.error(f"No found any torrent available for {query}")
            return False
        
        # Try each torrent result in order (best to worst) until one succeeds
        return await self._try_download_torrents_until_success(
            watchlist, 
            torrent_search_results, 
            user_token
        )
    
    async def _try_download_torrents_until_success(
        self,
        watchlist,
        torrent_search_results: list,
        user_token: str
    ) -> bool:
        """
        Try downloading torrents from search results until one succeeds.
        
        Args:
            watchlist: The watchlist item being processed
            torrent_search_results: List of torrent search results ordered by score
            user_token: Plex user token
            
        Returns:
            True if a torrent was successfully downloaded and tracked, False otherwise
        """
        index = 0
        download_success = False
        while index < len(torrent_search_results) and not download_success:
            torrent_result = torrent_search_results[index]
            download_success, new_torrent = await self._try_download_torrent(torrent_result)
            
            if download_success:
                # Successfully downloaded and found in Deluge
                await self._create_torrent_download_record(
                    watchlist, 
                    torrent_result, 
                    new_torrent, 
                    user_token
                )
                await self.removeWatchListItemUseCase.execute(watchlist.ratingKey, user_token)
                return True
            
            # Try next result
            logger.info(f"Trying next torrent result for '{watchlist.title}' (attempt {index + 1}/{len(torrent_search_results)})")
            index += 1
        
        logger.error(f"Failed to download any torrent for '{watchlist.title}' after trying {len(torrent_search_results)} result(s)")
        return False
    
    async def _create_torrent_download_record(
        self,
        watchlist,
        torrent_result: TorrentSearchResult,
        new_torrent: Torrent,
        user_token: str
    ) -> None:
        """
        Create a torrent download record in the database.
        
        Args:
            watchlist: The watchlist item
            torrent_result: The torrent search result that was downloaded
            new_torrent: The torrent found in Deluge
            user_token: Plex user token
        """
        await self.createTorrentDownloadUseCase.execute(TorrentDownload(
            guidPlex=watchlist.guid,
            ratingKey=watchlist.ratingKey,
            plexUserToken=user_token,
            guidProwlarr=torrent_result.guid,
            uid=new_torrent.hash,
            title=watchlist.title,
            fileName=new_torrent.fileName,
            year=watchlist.year,
            type=watchlist.type,
        ))
    
    async def _try_download_torrent(
        self, 
        torrent_result: TorrentSearchResult
    ) -> Tuple[bool, Optional[Torrent]]:
        """
        Try to download a torrent and verify it was added to Deluge.
        
        Args:
            torrent_result: The torrent search result to download
            
        Returns:
            Tuple of (success: bool, torrent: Optional[Torrent])
            - success: True if torrent was successfully downloaded and found in Deluge
            - torrent: The Torrent object if found, None otherwise
        """
        # Check if torrent is infected
        if await self.checkInfectedByGuidProwlarrQuery.execute(torrent_result.guid):
            logger.warning(f"Torrent '{torrent_result.title}' is infected, skipping")
            return False, None
        
        # Download the torrent
        _ = await self.downloadTorrentUseCase.execute(torrent_result)
        
        # Wait for 2 seconds to ensure the torrent is added to deluge
        await asyncio.sleep(2)
        
        # Find the new torrent in deluge by time_added (within 3 seconds from now) or by name similarity
        new_torrent = await self.getTorrentByNameQuery.execute(
            torrent_result.title, 
            time_added_threshold=3.0
        )
        
        if new_torrent is None:
            logger.warning(f"Torrent '{torrent_result.title}' is not added to deluge, download failed")
            return False, None
        else:
            logger.info(f"Torrent '{torrent_result.title}' is added to deluge successfully, download successful")
            return True, new_torrent

    async def execute(self):
        userToken, watchlists = await self.getPlexWatchlistsFromUsers.execute()
        #update the DownloadWatchListDb with deluge status,
        sync_result = await self.syncTorrentDownloadWithDelugeUseCase.execute()
        logger.info(f"Synced torrent download DB with Deluge: {sync_result['removed_count']} removed, {sync_result.get('updated_count', 0)} updated out of {sync_result['total_checked']} checked")
        
        for watchlist in watchlists:
            # Check if item should be skipped (already in library or downloading)
            should_skip, _ = await self._should_skip_watchlist_item(watchlist, userToken)
            if should_skip:
                continue
            
            # Process the watchlist item (search, download, track)
            await self._process_watchlist_item(watchlist, userToken)
                    
        return None