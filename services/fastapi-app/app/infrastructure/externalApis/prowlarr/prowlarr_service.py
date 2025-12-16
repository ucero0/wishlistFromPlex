"""Torrent search service using Prowlarr."""
import re
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.infrastructure.prowlarr.prowlarr_client import ProwlarrClient
from app.infrastructure.prowlarr.schemas import ProwlarrRawResult
from app.domain.models.torrent_search import TorrentResult, QualityInfo

logger = logging.getLogger(__name__)

# Quality scoring constants - Higher is better
RESOLUTION_SCORES = {
    "2160p": 100, "4k": 100, "uhd": 100,
    "1080p": 70, "720p": 40, "480p": 10, "sd": 5,
}

AUDIO_SCORES = {
    "truehd": 100, "true-hd": 100, "true hd": 100,
    "dts-hd ma": 95, "dts-hd.ma": 95, "dts hd ma": 95,
    "dtshd": 90, "dts-hd": 90, "atmos": 95, "dolby atmos": 95,
    "lpcm": 85, "flac": 80, "dts": 60, "dts-x": 70,
    "dd+": 55, "ddp": 55, "eac3": 55, "ac3": 50, "dd5.1": 50,
    "aac": 40, "mp3": 20,
}

HDR_SCORES = {
    "dolby vision": 50, "dv": 50, "hdr10+": 45, "hdr10plus": 45,
    "hdr10": 40, "hdr": 35, "hlg": 30, "sdr": 0,
}

VIDEO_CODEC_SCORES = {
    "x265": 30, "hevc": 30, "h265": 30, "h.265": 30,
    "x264": 20, "h264": 20, "h.264": 20, "avc": 20,
    "av1": 35, "vp9": 25, "mpeg4": 5, "xvid": 5,
}

SOURCE_SCORES = {
    "remux": 50, "bluray": 45, "blu-ray": 45, "bdrip": 40, "brrip": 35,
    "web-dl": 30, "webdl": 30, "webrip": 25, "hdtv": 20, "hdrip": 15,
    "dvdrip": 10, "cam": 1, "ts": 1, "telesync": 1,
}

MIN_SEEDERS = 1


class TorrentSearchService:
    """Service for searching torrents via Prowlarr."""

    def __init__(self, db: Session):
        self.db = db
        self.client = ProwlarrClient()

    async def test_connection(self) -> tuple[bool, Optional[str], Optional[str]]:
        """Test connection to Prowlarr."""
        return await self.client.test_connection()

    async def get_indexer_count(self) -> int:
        """Get the number of configured indexers."""
        return await self.client.get_indexer_count()

    def _parse_quality_from_title(self, title: str) -> QualityInfo:
        """Parse quality information from torrent title."""
        title_lower = title.lower()
        
        # Resolution
        resolution = None
        for res in ["2160p", "4k", "uhd", "1080p", "720p", "480p"]:
            if res in title_lower:
                resolution = "2160p" if res in ["4k", "uhd"] else res
                break
        
        # Audio
        audio = None
        audio_patterns = [
            (r"true[\s\-]?hd", "TrueHD"), (r"dts[\s\-]?hd[\s\.]?ma", "DTS-HD MA"),
            (r"atmos", "Atmos"), (r"dts[\s\-]?x", "DTS-X"), (r"dts[\s\-]?hd", "DTS-HD"),
            (r"dts", "DTS"), (r"dd\+|ddp|eac3", "DD+"), (r"ac3|dd5\.?1", "DD5.1"),
            (r"lpcm", "LPCM"), (r"flac", "FLAC"), (r"aac", "AAC"),
        ]
        for pattern, audio_name in audio_patterns:
            if re.search(pattern, title_lower):
                audio = audio_name
                break
        
        # HDR
        hdr = None
        hdr_patterns = [
            (r"dolby[\s\.\-]?vision|[\s\.\-]dv[\s\.\-]", "Dolby Vision"),
            (r"hdr10\+|hdr10plus", "HDR10+"), (r"hdr10", "HDR10"),
            (r"[\s\.\-]hdr[\s\.\-]", "HDR"), (r"hlg", "HLG"),
        ]
        for pattern, hdr_name in hdr_patterns:
            if re.search(pattern, title_lower):
                hdr = hdr_name
                break
        
        # Video codec
        video_codec = None
        codec_patterns = [
            (r"x265|hevc|h\.?265", "HEVC"), (r"x264|h\.?264|avc", "x264"),
            (r"av1", "AV1"), (r"vp9", "VP9"),
        ]
        for pattern, codec_name in codec_patterns:
            if re.search(pattern, title_lower):
                video_codec = codec_name
                break
        
        # Source
        source = None
        source_patterns = [
            (r"remux", "Remux"), (r"blu[\s\-]?ray|bdrip|brrip", "BluRay"),
            (r"web[\s\-]?dl", "WEB-DL"), (r"webrip", "WEBRip"),
            (r"hdtv", "HDTV"), (r"dvdrip", "DVDRip"),
        ]
        for pattern, source_name in source_patterns:
            if re.search(pattern, title_lower):
                source = source_name
                break
        
        # Release group
        release_group = None
        group_match = re.search(r"-([a-zA-Z0-9]+)(?:\.[a-z]{2,4})?$", title)
        if group_match:
            release_group = group_match.group(1)
        
        return QualityInfo(
            resolution=resolution, audio=audio, video_codec=video_codec,
            hdr=hdr, source=source, release_group=release_group,
        )

    def _calculate_quality_score(self, title: str, quality_info: QualityInfo, seeders: int) -> int:
        """Calculate quality score based on parsed info."""
        score = 0
        title_lower = title.lower()
        
        # Resolution score
        if quality_info.resolution:
            res_lower = quality_info.resolution.lower()
            score += RESOLUTION_SCORES.get(res_lower, 0)
        
        # Audio score - HIGHEST PRIORITY
        if quality_info.audio:
            audio_lower = quality_info.audio.lower()
            for key, value in AUDIO_SCORES.items():
                if key in audio_lower or audio_lower in key:
                    score += value
                    break
        else:
            for key, value in AUDIO_SCORES.items():
                if key in title_lower:
                    score += value
                    break
        
        # HDR score
        if quality_info.hdr:
            hdr_lower = quality_info.hdr.lower()
            for key, value in HDR_SCORES.items():
                if key in hdr_lower:
                    score += value
                    break
        
        # Video codec score
        if quality_info.video_codec:
            codec_lower = quality_info.video_codec.lower()
            for key, value in VIDEO_CODEC_SCORES.items():
                if key in codec_lower:
                    score += value
                    break
        
        # Source score
        if quality_info.source:
            source_lower = quality_info.source.lower()
            for key, value in SOURCE_SCORES.items():
                if key in source_lower:
                    score += value
                    break
        
        # Seeder bonus
        if seeders >= 100:
            score += 20
        elif seeders >= 50:
            score += 15
        elif seeders >= 20:
            score += 10
        elif seeders >= 5:
            score += 5
        
        return score

    async def search_prowlarr(self, query: str, media_type: str = "movie") -> List[TorrentResult]:
        """Search Prowlarr for torrents and return validated TorrentResult objects."""
        categories = "2000" if media_type == "movie" else "5000"
        logger.info(f"Searching Prowlarr: '{query}', media_type: {media_type}")
        
        raw_results = await self.client.search(query, categories)
        
        results = []
        for result_data in raw_results:
            try:
                raw_result = ProwlarrRawResult(**result_data)
                results.append(TorrentResult(
                    **raw_result.model_dump(),
                    quality_score=0,
                    quality_info=QualityInfo()
                ))
            except Exception as e:
                logger.warning(f"Failed to parse Prowlarr result: {e}, skipping")
                continue
        
        logger.info(f"Prowlarr returned {len(results)} validated results")
        return results

    def _process_search_results(self, results: List[TorrentResult]) -> List[TorrentResult]:
        """Process and score TorrentResult objects with quality information."""
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
                
                quality_info = self._parse_quality_from_title(title)
                quality_score = self._calculate_quality_score(title, quality_info, seeders)
                
                result.quality_info = quality_info
                result.quality_score = quality_score
                processed_results.append(result)
            except Exception as e:
                logger.warning(f"Error processing search result: {e}")
                continue
        
        processed_results.sort(key=lambda x: x.quality_score, reverse=True)
        
        if skipped_no_seeders > 0:
            logger.info(f"Skipped {skipped_no_seeders} results with seeders < {MIN_SEEDERS}")
        logger.info(f"Processed {len(processed_results)} valid results after filtering")
        
        return processed_results

    async def search_by_query(
        self,
        query: str,
        media_type: str = "movie",
        auto_add_to_deluge: bool = True,
    ) -> Optional[List[TorrentResult]]:
        """Search for torrents by query and return the best result."""
        results = await self.search_prowlarr(query, media_type)
        if not results:
            return None
        
        results = self._process_search_results(results)
        if not results:
            return []
        
        best_result = results[0]

        if auto_add_to_deluge:
            send_result = await self.client.send_to_download_client(best_result.guid, best_result.indexerId)
            if not send_result:
                logger.error(f"Error sending torrent to client downloader")

        return [best_result]

