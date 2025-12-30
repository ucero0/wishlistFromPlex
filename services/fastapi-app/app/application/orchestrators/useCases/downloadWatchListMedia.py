from app.application.orchestrators.queries.getPlexWatchlistsFromUsers import GetPlexWatchlistsFromUsers
from app.application.plex.queries.getPlexUsers import GetPlexUserQuery
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.application.prowlarr.useCases.downloadTorrent import DownloadTorrentUseCase
from app.application.prowlarr.queries.findBestTorrent import FindBestTorrentQuery
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
from app.domain.models.torrentDownload import TorrentDownload
logger = logging.getLogger(__name__)

class DownloadWatchListMediaUseCase:

    def __init__(self, 
    getPlexUserQuery: GetPlexUserQuery,
    getWatchListQuery: GetWatchListQuery,
    downloadTorrentUseCase: DownloadTorrentUseCase,
    findBestTorrentQuery: FindBestTorrentQuery, 
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
    
    async def execute(self):
        userToken, watchlists = await self.getPlexWatchlistsFromUsers.execute()
        #update the DownloadWatchListDb with deluge status,
        sync_result = await self.syncTorrentDownloadWithDelugeUseCase.execute()
        logger.info(f"Synced torrent download DB with Deluge: {sync_result['removed_count']} removed, {sync_result.get('updated_count', 0)} updated out of {sync_result['total_checked']} checked")
        
        watchlistsToRemove = []
        for watchlist in watchlists:
            serverItemInLibrary = await self.isItemInLibraryQuery.execute(userToken, watchlist)
            if serverItemInLibrary:
                #remove from watchlist
                watchlistsToRemove.append(watchlist)
                continue
            else:
                #check if the media is already in the torrent download db
                isTorrentAlreadyDownloading = await self.isGuidPlexDownloadingQuery.execute(watchlist.guid)
                if isTorrentAlreadyDownloading:
                    logger.error(f"Torrent {watchlist.title} is already downloading, skipping")
                    #add to watchlist to remove
                    watchlistsToRemove.append(watchlist)
                    continue
                query = await self._get_search_query(watchlist)
                #search if the media is in deluge 
                bestTorrentSearchResult = await self.findBestTorrentQuery.execute(query)
                if bestTorrentSearchResult == None:
                    logger.error(f"No found any torrent available for {query}")
                    continue
                elif await self.checkInfectedByGuidProwlarrQuery.execute(bestTorrentSearchResult.guid):
                    logger.error(f"Torrent {bestTorrentSearchResult.title} is infected, skipping")
                    continue
                #download the torrent
                downloadSuccess = await self.downloadTorrentUseCase.execute(bestTorrentSearchResult)
                #find the new torrent in deluge by the title of the search query
                newTorrent = await self.getTorrentByNameQuery.execute(bestTorrentSearchResult.title)
                if newTorrent == None:
                    logger.error(f" {bestTorrentSearchResult.title} is not added to deluge, download failed")
                    
                else:
                    logger.info(f" {bestTorrentSearchResult.title} is added to deluge successfully, download successful")
                    #add to torrent download
                    await self.createTorrentDownloadUseCase.execute(TorrentDownload(
                        guidPlex=watchlist.guid,
                        guidProwlarr=bestTorrentSearchResult.guid,
                        uid=newTorrent.hash,
                        title=watchlist.title,
                        fileName=newTorrent.fileName,
                        year=watchlist.year,
                        type=watchlist.type,
                    ))
                    #remove from watchlist
                    watchlistsToRemove.append(watchlist)
                    
        for watchlist in watchlistsToRemove:
            await self.removeWatchListItemUseCase.execute(watchlist.ratingKey, userToken)
        return None