"""Torrent search service using Prowlarr API."""
import re
import logging

from typing import Optional, Dict, Any, List, Tuple
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.modules.torrent_search.models import TorrentSearchResult
from app.modules.torrent_search.schemas import TorrentResult, QualityInfo, ProwlarrRawResult

logger = logging.getLogger(__name__)


# Quality scoring constants - Higher is better
RESOLUTION_SCORES = {
    "2160p": 100,
    "4k": 100,
    "uhd": 100,
    "1080p": 70,
    "720p": 40,
    "480p": 10,
    "sd": 5,
}

AUDIO_SCORES = {
    # Lossless / High-end (prioritized)
    "truehd": 100,
    "true-hd": 100,
    "true hd": 100,
    "dts-hd ma": 95,
    "dts-hd.ma": 95,
    "dts hd ma": 95,
    "dtshd": 90,
    "dts-hd": 90,
    "atmos": 95,
    "dolby atmos": 95,
    "lpcm": 85,
    "flac": 80,
    # Lossy but good
    "dts": 60,
    "dts-x": 70,
    "dd+": 55,
    "ddp": 55,
    "eac3": 55,
    "ac3": 50,
    "dd5.1": 50,
    "aac": 40,
    "mp3": 20,
}

HDR_SCORES = {
    "dolby vision": 50,
    "dv": 50,
    "hdr10+": 45,
    "hdr10plus": 45,
    "hdr10": 40,
    "hdr": 35,
    "hlg": 30,
    "sdr": 0,
}

VIDEO_CODEC_SCORES = {
    "x265": 30,
    "hevc": 30,
    "h265": 30,
    "h.265": 30,
    "x264": 20,
    "h264": 20,
    "h.264": 20,
    "avc": 20,
    "av1": 35,
    "vp9": 25,
    "mpeg4": 5,
    "xvid": 5,
}

SOURCE_SCORES = {
    "remux": 50,
    "bluray": 45,
    "blu-ray": 45,
    "bdrip": 40,
    "brrip": 35,
    "web-dl": 30,
    "webdl": 30,
    "webrip": 25,
    "hdtv": 20,
    "hdrip": 15,
    "dvdrip": 10,
    "cam": 1,
    "ts": 1,
    "telesync": 1,
}

# Minimum seeders for a valid torrent
MIN_SEEDERS = 1


class TorrentSearchService:
    """Service for searching torrents via Prowlarr."""

    def __init__(self, db: Session):
        self.db = db
        self.prowlarr_url = f"http://{settings.prowlarr_host}:{settings.prowlarr_port}"
        self.prowlarr_client_downloader_url = f"{self.prowlarr_url}/api/v1/search"
        self.prowlarr_client_downloader_headers = {
            "Content-Type": "application/json",
            "X-Api-Key": settings.prowlarr_api_key
        }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Prowlarr API requests."""
        return self.prowlarr_client_downloader_headers

    async def test_connection(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Test connection to Prowlarr."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.prowlarr_url}/api/v1/system/status",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return True, data.get("version"), None
                else:
                    return False, None, f"HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            return False, None, str(e)

    async def get_indexer_count(self) -> int:
        """Get the number of configured indexers."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.prowlarr_url}/api/v1/indexer",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    indexers = response.json()
                    return len([i for i in indexers if i.get("enable", False)])
                return 0
        except Exception:
            return 0

    async def get_indexer_by_id(self, indexer_id: int) -> Optional[Dict[str, Any]]:
        """Get indexer details by ID."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.prowlarr_url}/api/v1/indexer",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    indexers = response.json()
                    for indexer in indexers:
                        if indexer.get("id") == indexer_id:
                            return indexer
                return None
        except Exception:
            return None

    async def get_download_client_count(self) -> int:
        """Get the number of configured download clients."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.prowlarr_url}/api/v1/downloadclient",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    clients = response.json()
                    return len([c for c in clients if c.get("enable", False)])
                return 0
        except Exception:
            return 0

    async def get_download_clients(self) -> List[Dict[str, Any]]:
        """Get list of configured download clients."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.prowlarr_url}/api/v1/downloadclient",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    clients = response.json()
                    return [c for c in clients if c.get("enable", False)]
                return []
        except Exception:
            return []

    def _parse_quality_from_title(self, title: str) -> QualityInfo:
        """Parse quality information from torrent title."""
        title_lower = title.lower()
        
        # Resolution
        resolution = None
        for res in ["2160p", "4k", "uhd", "1080p", "720p", "480p"]:
            if res in title_lower:
                resolution = "2160p" if res in ["4k", "uhd"] else res
                break
        
        # Audio - check for TrueHD and other formats
        audio = None
        audio_patterns = [
            (r"true[\s\-]?hd", "TrueHD"),
            (r"dts[\s\-]?hd[\s\.]?ma", "DTS-HD MA"),
            (r"atmos", "Atmos"),
            (r"dts[\s\-]?x", "DTS-X"),
            (r"dts[\s\-]?hd", "DTS-HD"),
            (r"dts", "DTS"),
            (r"dd\+|ddp|eac3", "DD+"),
            (r"ac3|dd5\.?1", "DD5.1"),
            (r"lpcm", "LPCM"),
            (r"flac", "FLAC"),
            (r"aac", "AAC"),
        ]
        for pattern, audio_name in audio_patterns:
            if re.search(pattern, title_lower):
                audio = audio_name
                break
        
        # HDR
        hdr = None
        hdr_patterns = [
            (r"dolby[\s\.\-]?vision|[\s\.\-]dv[\s\.\-]", "Dolby Vision"),
            (r"hdr10\+|hdr10plus", "HDR10+"),
            (r"hdr10", "HDR10"),
            (r"[\s\.\-]hdr[\s\.\-]", "HDR"),
            (r"hlg", "HLG"),
        ]
        for pattern, hdr_name in hdr_patterns:
            if re.search(pattern, title_lower):
                hdr = hdr_name
                break
        
        # Video codec
        video_codec = None
        codec_patterns = [
            (r"x265|hevc|h\.?265", "HEVC"),
            (r"x264|h\.?264|avc", "x264"),
            (r"av1", "AV1"),
            (r"vp9", "VP9"),
        ]
        for pattern, codec_name in codec_patterns:
            if re.search(pattern, title_lower):
                video_codec = codec_name
                break
        
        # Source
        source = None
        source_patterns = [
            (r"remux", "Remux"),
            (r"blu[\s\-]?ray|bdrip|brrip", "BluRay"),
            (r"web[\s\-]?dl", "WEB-DL"),
            (r"webrip", "WEBRip"),
            (r"hdtv", "HDTV"),
            (r"dvdrip", "DVDRip"),
        ]
        for pattern, source_name in source_patterns:
            if re.search(pattern, title_lower):
                source = source_name
                break
        
        # Release group (usually at the end after a dash)
        release_group = None
        group_match = re.search(r"-([a-zA-Z0-9]+)(?:\.[a-z]{2,4})?$", title)
        if group_match:
            release_group = group_match.group(1)
        
        return QualityInfo(
            resolution=resolution,
            audio=audio,
            video_codec=video_codec,
            hdr=hdr,
            source=source,
            release_group=release_group,
        )

    def _calculate_quality_score(self, title: str, quality_info: QualityInfo, seeders: int) -> int:
        """
        Calculate quality score based on parsed info.
        
        Priority:
        1. TrueHD audio (highest priority)
        2. 2160p resolution
        3. HDR
        4. Source quality (Remux > BluRay > WEB-DL)
        5. Seeders (health)
        """
        score = 0
        title_lower = title.lower()
        
        # Resolution score (max 100)
        if quality_info.resolution:
            res_lower = quality_info.resolution.lower()
            score += RESOLUTION_SCORES.get(res_lower, 0)
        
        # Audio score (max 100) - HIGHEST PRIORITY
        if quality_info.audio:
            audio_lower = quality_info.audio.lower()
            for key, value in AUDIO_SCORES.items():
                if key in audio_lower or audio_lower in key:
                    score += value
                    break
        else:
            # Check title directly for audio
            for key, value in AUDIO_SCORES.items():
                if key in title_lower:
                    score += value
                    break
        
        # HDR score (max 50)
        if quality_info.hdr:
            hdr_lower = quality_info.hdr.lower()
            for key, value in HDR_SCORES.items():
                if key in hdr_lower:
                    score += value
                    break
        
        # Video codec score (max 35)
        if quality_info.video_codec:
            codec_lower = quality_info.video_codec.lower()
            for key, value in VIDEO_CODEC_SCORES.items():
                if key in codec_lower:
                    score += value
                    break
        
        # Source score (max 50)
        if quality_info.source:
            source_lower = quality_info.source.lower()
            for key, value in SOURCE_SCORES.items():
                if key in source_lower:
                    score += value
                    break
        
        # Seeder bonus (max 20)
        if seeders >= 100:
            score += 20
        elif seeders >= 50:
            score += 15
        elif seeders >= 20:
            score += 10
        elif seeders >= 5:
            score += 5
        
        return score

    def _build_search_query(self, title: str, year: Optional[int] = None) -> str:
        """Build search query from title and optional year."""
        query = title
        
        if year:
            query += f" {year}"
        
        return query

    async def search_prowlarr(self, query: str, media_type: str = "movie") -> List[TorrentResult]:
        """
        Search Prowlarr for torrents and return validated TorrentResult objects.
        
        Validates API response using ProwlarrRawResult schema, then creates TorrentResult objects.
        Quality scoring will be done in _process_search_results.
        
        Args:
            query: Search query string
            media_type: "movie" or "tv"
            
        Returns:
            List of validated TorrentResult objects (quality_score=0, will be calculated in _process_search_results)
        """
        try:
            categories = "2000" if media_type == "movie" else "5000"  # Movies: 2000, TV: 5000
            
            logger.info(f"Searching Prowlarr with query: '{query}', media_type: {media_type}, categories: {categories}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.prowlarr_url}/api/v1/search",
                    headers=self._get_headers(),
                    params={
                        "query": query,
                        "categories": categories,
                        "type": "search",
                    }
                )
                
                # Validate response status
                response.raise_for_status()
                
                # Parse JSON response
                api_response_data = response.json()
                
                # Validate and convert to TorrentResult objects directly
                if isinstance(api_response_data, list):
                    results = []
                    for result_data in api_response_data:
                        try:
                            # Validate structure using ProwlarrRawResult
                            raw_result = ProwlarrRawResult(**result_data)
                            
                            # Create TorrentResult with temporary values (will be recalculated in _process_search_results)
                            results.append(TorrentResult(
                                **raw_result.model_dump(),
                                quality_score=0,  # Will be recalculated in _process_search_results
                                quality_info=QualityInfo()  # Will be recalculated in _process_search_results
                            ))
                        except Exception as e:
                            logger.warning(f"Failed to parse Prowlarr result: {e}, skipping")
                            continue
                    
                    logger.info(f"Prowlarr returned {len(results)} validated results")
                    return results
                else:
                    logger.warning(f"Unexpected Prowlarr response format: {type(api_response_data)}")
                    return []
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Prowlarr API HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"Prowlarr search exception: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []


    def _process_search_results(self, results: List[TorrentResult]) -> List[TorrentResult]:
        """
        Process and score TorrentResult objects with quality information.
        
        Updates quality_score and quality_info for each result, filters by seeders,
        and sorts by quality score.
        
        Args:
            results: List of TorrentResult objects (from ProwlarrSearchResponse)
            
        Returns:
            List of processed and scored TorrentResult objects, sorted by quality score
        """
        processed_results = []
        skipped_no_seeders = 0
        
        logger.info(f"Processing {len(results)} validated search results")
        
        for result in results:
            try:
                title = result.title
                seeders = result.seeders or 0
                
                # Skip torrents with no seeders (but log for debugging)
                if seeders < MIN_SEEDERS:
                    skipped_no_seeders += 1
                    logger.debug(f"Skipping '{title[:50]}...' - seeders: {seeders} (min: {MIN_SEEDERS})")
                    continue
                
                # Parse quality info and calculate score
                quality_info = self._parse_quality_from_title(title)
                quality_score = self._calculate_quality_score(title, quality_info, seeders)
                
                # Update the result with calculated quality info
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

    async def send2ClientDownloader(self, guid: str, indexerId: int) -> bool:
        """call the client downloader to download the torrent
        urlPath2clienDowloader = http://<tu-prowlarr>:9696/api/v1/search
        {
            "guid": "magnet:?xt=urn:btih:XXXXX",
            "indexerId": 1
        }
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.prowlarr_client_downloader_url}",
                    headers=self._get_headers(),
                    json={"guid": guid, "indexerId": indexerId}
                )
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Error sending torrent to client downloader: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending torrent to client downloader: {e}")
            return False

    async def search_by_query(
        self,
        query: str,
        media_type: str = "movie",

        auto_add_to_deluge: bool = True,

    ) -> TorrentSearchResult:
        "search for torrents by query and return the best result"
        results = await self.search_prowlarr(query, media_type)
        if not results:
            return None
        results: List[TorrentResult] = self._process_search_results(results)
        best_result = results[0]
        if not best_result:
            return None
        if auto_add_to_deluge:
            send_result = await self.send2ClientDownloader(best_result.guid, best_result.indexerId)
            if not send_result:
                logger.error(f"Error sending torrent to client downloader: {send_result}")

        return results

