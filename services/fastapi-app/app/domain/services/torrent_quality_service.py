"""Domain service for parsing and scoring torrent quality information."""
import re
from typing import Optional
from app.domain.models.torrent_search import QualityInfo

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


class TorrentQualityService:
    """Domain service for parsing and scoring torrent quality information."""
    
    @staticmethod
    def parse_quality_from_title(title: str) -> QualityInfo:
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
    
    @staticmethod
    def calculate_quality_score(title: str, quality_info: QualityInfo, seeders: int) -> int:
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

