from app.application.orchestrators.queries.getPlexWatchlistsFromUsers import GetPlexWatchlistsFromUsers
from app.application.plex.queries.getPlexUsers import GetPlexUserQuery
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.application.torrentDownload.services.sendTorrentToDeluge import SendTorrentToDelugeService
from app.application.prowlarr.queries.findBestTorrent import GetBestTorrentsQuery
from app.application.plex.queries.getPlexServerItem import IsItemInLibraryQuery
from app.application.deluge.queries.getTorrentStatus import GetTorrentByNameQuery
from app.application.plex.useCases.removeWatchListItem import RemoveWatchListItemUseCase
from app.application.blacklist_torrent.queries import IsBlacklistedByGuidProwlarrQuery
from app.application.torrentDownload.useCases.createTorrentDownload import CreateTorrentDownloadUseCase
from app.application.orchestrators.useCases.syncTorrentDownloadWithDeluge import SyncTorrentDownloadWithDelugeUseCase
from app.application.tmdb.queries.getOriginalTitle import GetOriginalTitleFromTMDBQuery
from app.application.deferredTorrent.useCases.enqueueDeferredTorrentDownload import (
    EnqueueDeferredTorrentDownloadUseCase,
)
from app.application.deferredTorrent.useCases.processDeferredTorrentDownloads import (
    ProcessDeferredTorrentDownloadsUseCase,
)
from app.application.orchestrators.queries.isMediaAlreadyQueuedForDownload import (
    IsMediaAlreadyQueuedForDownloadQuery,
)
from app.domain.services.download_volume_space_checker import DownloadVolumeSpaceChecker
import logging
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
    findBestTorrentQuery: GetBestTorrentsQuery, 
    isItemInLibraryQuery: IsItemInLibraryQuery,
    getTorrentByNameQuery: GetTorrentByNameQuery,
    removeWatchListItemUseCase: RemoveWatchListItemUseCase,
    is_blacklisted_by_guid_prowlarr_query: IsBlacklistedByGuidProwlarrQuery,
    createTorrentDownloadUseCase: CreateTorrentDownloadUseCase,
    syncTorrentDownloadWithDelugeUseCase: SyncTorrentDownloadWithDelugeUseCase,
    getOriginalTitleFromTMDBQuery: GetOriginalTitleFromTMDBQuery,
    enqueueDeferredTorrentDownloadUseCase: EnqueueDeferredTorrentDownloadUseCase,
    isMediaAlreadyQueuedForDownloadQuery: IsMediaAlreadyQueuedForDownloadQuery,
    downloadVolumeSpaceChecker: DownloadVolumeSpaceChecker,
    processDeferredTorrentDownloadsUseCase: ProcessDeferredTorrentDownloadsUseCase,
    sendTorrentToDelugeService: SendTorrentToDelugeService,
):
        self.getPlexWatchlistsFromUsers = GetPlexWatchlistsFromUsers(getPlexUserQuery, getWatchListQuery)
        self.findBestTorrentQuery = findBestTorrentQuery
        self.isItemInLibraryQuery = isItemInLibraryQuery
        self.getTorrentByNameQuery = getTorrentByNameQuery
        self.removeWatchListItemUseCase = removeWatchListItemUseCase
        self.is_blacklisted_by_guid_prowlarr_query = is_blacklisted_by_guid_prowlarr_query
        self.createTorrentDownloadUseCase = createTorrentDownloadUseCase
        self.syncTorrentDownloadWithDelugeUseCase = syncTorrentDownloadWithDelugeUseCase
        self.getOriginalTitleFromTMDBQuery = getOriginalTitleFromTMDBQuery
        self.enqueueDeferredTorrentDownloadUseCase = enqueueDeferredTorrentDownloadUseCase
        self.isMediaAlreadyQueuedForDownloadQuery = isMediaAlreadyQueuedForDownloadQuery
        self.downloadVolumeSpaceChecker = downloadVolumeSpaceChecker
        self.processDeferredTorrentDownloadsUseCase = (
            processDeferredTorrentDownloadsUseCase
        )
        self.sendTorrentToDelugeService = sendTorrentToDelugeService
    
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

    @staticmethod
    def _watchlist_media_type(watchlist) -> str | None:
        if watchlist.type is None:
            return None
        if hasattr(watchlist.type, "value"):
            return str(watchlist.type.value)
        return str(watchlist.type)
    
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
            await self.removeWatchListItemUseCase.execute(watchlist.rating_key, user_token)
            return True, "already_in_library"
        
        queued, queue_reason = await self.isMediaAlreadyQueuedForDownloadQuery.execute(
            watchlist.guid,
            title=watchlist.title,
            year=watchlist.year,
            media_type=self._watchlist_media_type(watchlist),
        )
        if queued:
            logger.info(
                "Skipping '%s' — already handled for another user (%s)",
                watchlist.title,
                queue_reason,
            )
            if watchlist.rating_key:
                await self.removeWatchListItemUseCase.execute(
                    watchlist.rating_key, user_token
                )
            return True, queue_reason or "already_queued"
        
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
        search_query = await self._get_search_query(watchlist)
        torrent_search_results = await self.findBestTorrentQuery.execute(search_query)
        
        if not torrent_search_results:
            logger.error(f"No found any torrent available for {search_query}")
            return False
        
        # Try each torrent result in order (best to worst) until one succeeds
        return await self._try_download_torrents_until_success(
            watchlist,
            torrent_search_results,
            user_token,
            search_query,
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
            download_success, new_torrent, deferred = await self._try_download_torrent(
                torrent_result, watchlist, user_token, search_query
            )

            if deferred:
                logger.info(
                    "Deferred '%s' — watchlist item kept until download volume has space",
                    watchlist.title,
                )
                return True
            
            if download_success:
                # Successfully downloaded and found in Deluge
                await self._create_torrent_download_record(
                    watchlist, 
                    torrent_result, 
                    new_torrent, 
                    user_token
                )
                await self.removeWatchListItemUseCase.execute(watchlist.rating_key, user_token)
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
            plex_guid=watchlist.guid,
            watchlist_item_id=watchlist.rating_key,
            plex_user_token=user_token,
            prowlarr_guid=torrent_result.guid,
            uid=new_torrent.hash,
            title=watchlist.title,
            file_name=new_torrent.file_name,
            year=watchlist.year,
            type=watchlist.type,
        ))
    
    async def _try_download_torrent(
        self,
        torrent_result: TorrentSearchResult,
        watchlist,
        user_token: str,
        search_query: str,
    ) -> Tuple[bool, Optional[Torrent], bool]:
        """
        Try to download a torrent and verify it was added to Deluge.
        
        Returns:
            (success, torrent, deferred) — deferred=True means queued in DB, not sent to Deluge
        """
        # Check if torrent is blacklisted (e.g. infected, unhealthy)
        if await self.is_blacklisted_by_guid_prowlarr_query.execute(torrent_result.guid):
            logger.warning(f"Torrent '{torrent_result.title}' is blacklisted, skipping")
            return False, None, False

        if torrent_result.guid:
            queued, queue_reason = (
                await self.isMediaAlreadyQueuedForDownloadQuery.execute(
                    watchlist.guid,
                    guid_prowlarr=torrent_result.guid,
                    title=watchlist.title,
                    year=watchlist.year,
                    media_type=self._watchlist_media_type(watchlist),
                )
            )
            if queued:
                logger.info(
                    "Not sending '%s' to Deluge — same release already queued (%s)",
                    watchlist.title,
                    queue_reason,
                )
                if watchlist.rating_key:
                    await self.removeWatchListItemUseCase.execute(
                        watchlist.rating_key, user_token
                    )
                return False, None, True

        ok, _, required = self.downloadVolumeSpaceChecker.has_space_for_torrent(
            torrent_result.size
        )
        if not ok:
            await self.enqueueDeferredTorrentDownloadUseCase.execute(
                watchlist=watchlist,
                user_token=user_token,
                torrent_result=torrent_result,
                search_query=search_query,
            )
            return False, None, True
        
        new_torrent = await self.sendTorrentToDelugeService.execute(torrent_result)

        if new_torrent is None:
            logger.warning(f"Torrent '{torrent_result.title}' is not added to deluge, download failed")
            return False, None, False
        logger.info(
            f"Torrent '{torrent_result.title}' is added to deluge successfully, download successful"
        )
        return True, new_torrent, False

    async def execute(self):
        release_result = await self.processDeferredTorrentDownloadsUseCase.execute()
        if release_result.sent:
            logger.info(
                "Released %s deferred torrent(s) to Deluge (still pending: %s)",
                release_result.sent,
                release_result.still_pending,
            )

        userToken, watchlists = await self.getPlexWatchlistsFromUsers.execute()
        #update the DownloadWatchListDb with deluge status,
        sync_result = await self.syncTorrentDownloadWithDelugeUseCase.execute()
        if sync_result.get("skipped"):
            logger.warning(
                "Skipped torrent download DB sync with Deluge: reason=%s",
                sync_result.get("reason"),
            )
        else:
            logger.info(
                "Synced torrent download DB with Deluge: %s removed, %s updated out of %s checked",
                sync_result["removed_count"],
                sync_result.get("updated_count", 0),
                sync_result["total_checked"],
            )
        
        for watchlist in watchlists:
            # Check if item should be skipped (already in library or downloading)
            should_skip, _ = await self._should_skip_watchlist_item(watchlist, userToken)
            if should_skip:
                continue
            
            # Process the watchlist item (search, download, track)
            await self._process_watchlist_item(watchlist, userToken)
                    
        return None