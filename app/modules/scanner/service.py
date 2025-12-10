"""Scanner service for virus scanning and file organization."""
import os
import re
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

import pyclamd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.scanner.models import ScanResult, ScanStatus
from app.modules.deluge.models import TorrentItem
from app.modules.plex.models import WishlistItem, MediaType

logger = logging.getLogger(__name__)


class ScannerService:
    """Service for scanning files and organizing media."""

    def __init__(self, db: Session):
        self.db = db
        self._clamav: Optional[pyclamd.ClamdNetworkSocket] = None
        self._yara_rules = None

    @property
    def clamav(self) -> pyclamd.ClamdNetworkSocket:
        """Get ClamAV client connection."""
        if self._clamav is None:
            self._clamav = pyclamd.ClamdNetworkSocket(
                host=settings.clamav_host,
                port=settings.clamav_port
            )
        return self._clamav

    @property
    def yara_rules(self):
        """Load YARA rules lazily."""
        if self._yara_rules is None:
            self._yara_rules = self._load_yara_rules()
        return self._yara_rules

    def _load_yara_rules(self):
        """Load YARA rules from the rules directory."""
        try:
            import yara
            rules_path = Path(settings.yara_rules_path)
            if not rules_path.exists():
                logger.warning(f"YARA rules path does not exist: {rules_path}")
                return None
            
            # Find all .yar and .yara files
            rule_files = {}
            for ext in ['*.yar', '*.yara']:
                for rule_file in rules_path.glob(f'**/{ext}'):
                    rule_files[str(rule_file)] = str(rule_file)
            
            if not rule_files:
                logger.warning("No YARA rules found")
                return None
            
            return yara.compile(filepaths=rule_files)
        except Exception as e:
            logger.error(f"Failed to load YARA rules: {e}")
            return None

    def scan_with_clamav(self, file_path: str) -> Dict[str, Any]:
        """Scan a file with ClamAV."""
        try:
            if not self.clamav.ping():
                return {"status": "error", "error": "ClamAV not available"}
            
            result = self.clamav.scan_file(file_path)
            
            if result is None:
                return {"status": "clean"}
            
            # ClamAV returns dict: {filepath: ('FOUND', 'VirusName')} or None
            if file_path in result:
                status, virus_name = result[file_path]
                if status == 'FOUND':
                    return {"status": "infected", "virus_name": virus_name}
            
            return {"status": "clean"}
        except Exception as e:
            logger.error(f"ClamAV scan error: {e}")
            return {"status": "error", "error": str(e)}

    def scan_with_yara(self, file_path: str) -> Dict[str, Any]:
        """Scan a file with YARA rules."""
        try:
            if self.yara_rules is None:
                return {"status": "skipped", "reason": "No YARA rules loaded"}
            
            matches = self.yara_rules.match(file_path)
            
            if matches:
                matched_rules = [match.rule for match in matches]
                return {
                    "status": "infected",
                    "matched_rules": matched_rules
                }
            
            return {"status": "clean"}
        except Exception as e:
            logger.error(f"YARA scan error: {e}")
            return {"status": "error", "error": str(e)}

    def parse_episode_info(self, filename: str) -> Optional[Tuple[int, List[int]]]:
        """
        Parse season and episode numbers from filename.
        Returns (season, [episodes]) or None if not found.
        
        Supports formats:
        - S01E05, S01E05E06 (multi-episode)
        - 1x05, 1x05-06
        - Season 1 Episode 5
        """
        filename_lower = filename.lower()
        
        # Pattern: S01E05 or S01E05E06
        match = re.search(r's(\d{1,2})e(\d{1,2})(?:e(\d{1,2}))?', filename_lower)
        if match:
            season = int(match.group(1))
            episodes = [int(match.group(2))]
            if match.group(3):
                episodes.append(int(match.group(3)))
            return season, episodes
        
        # Pattern: 1x05 or 1x05-06
        match = re.search(r'(\d{1,2})x(\d{1,2})(?:-(\d{1,2}))?', filename_lower)
        if match:
            season = int(match.group(1))
            episodes = [int(match.group(2))]
            if match.group(3):
                # Range: add all episodes in range
                end_ep = int(match.group(3))
                episodes = list(range(episodes[0], end_ep + 1))
            return season, episodes
        
        # Pattern: Season 1 Episode 5
        match = re.search(r'season\s*(\d{1,2}).*episode\s*(\d{1,2})', filename_lower)
        if match:
            return int(match.group(1)), [int(match.group(2))]
        
        return None

    def sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '')
        # Remove leading/trailing spaces and dots
        return name.strip(' .')

    def organize_movie(self, file_path: str, title: str, year: Optional[int]) -> str:
        """
        Organize a movie file into Plex-compatible structure.
        Format: /media/movies/{Title} ({Year})/{Title} ({Year}).ext
        """
        file_ext = Path(file_path).suffix
        
        if year:
            folder_name = f"{self.sanitize_filename(title)} ({year})"
        else:
            folder_name = self.sanitize_filename(title)
        
        dest_dir = Path(settings.media_movies_path) / folder_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_file = dest_dir / f"{folder_name}{file_ext}"
        
        shutil.move(file_path, dest_file)
        logger.info(f"Moved movie: {file_path} -> {dest_file}")
        
        return str(dest_file)

    def organize_tvshow(
        self, 
        file_path: str, 
        title: str, 
        year: Optional[int],
        season: int,
        episodes: List[int]
    ) -> str:
        """
        Organize a TV show file into Plex-compatible structure.
        Format: /media/tvshows/{Show Name} ({Year})/Season {XX}/{Show Name} - s{XX}e{XX}.ext
        
        Reference: https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/
        """
        file_ext = Path(file_path).suffix
        
        if year:
            show_folder = f"{self.sanitize_filename(title)} ({year})"
        else:
            show_folder = self.sanitize_filename(title)
        
        season_folder = f"Season {season:02d}"
        
        # Build episode string (e.g., s01e05 or s01e05e06 for multi-episode)
        episode_str = ''.join([f"e{ep:02d}" for ep in episodes])
        filename = f"{show_folder} - s{season:02d}{episode_str}{file_ext}"
        
        dest_dir = Path(settings.media_tvshows_path) / show_folder / season_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_file = dest_dir / filename
        
        shutil.move(file_path, dest_file)
        logger.info(f"Moved TV show: {file_path} -> {dest_file}")
        
        return str(dest_file)

    def quarantine_file(self, file_path: str, threat_name: str) -> str:
        """Move an infected file to quarantine."""
        quarantine_dir = Path(settings.media_quarantine_path)
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        filename = Path(file_path).name
        # Add timestamp to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_file = quarantine_dir / f"{timestamp}_{filename}"
        
        shutil.move(file_path, dest_file)
        logger.warning(f"Quarantined infected file: {file_path} -> {dest_file} (threat: {threat_name})")
        
        return str(dest_file)

    def get_torrent_files(self, save_path: str, torrent_name: str) -> List[str]:
        """Get all media files from a torrent download."""
        media_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.webm'}
        
        torrent_path = Path(save_path) / torrent_name
        
        if torrent_path.is_file():
            return [str(torrent_path)] if torrent_path.suffix.lower() in media_extensions else []
        
        if torrent_path.is_dir():
            files = []
            for file in torrent_path.rglob('*'):
                if file.is_file() and file.suffix.lower() in media_extensions:
                    files.append(str(file))
            return files
        
        # Try just the save_path
        save_dir = Path(save_path)
        if save_dir.is_dir():
            files = []
            for file in save_dir.rglob('*'):
                if file.is_file() and file.suffix.lower() in media_extensions:
                    files.append(str(file))
            return files
        
        return []

    async def scan_torrent(self, torrent_hash: str) -> ScanResult:
        """
        Scan all files from a completed torrent.
        
        Pipeline:
        1. Get torrent info from database
        2. Scan with ClamAV (antivirus)
        3. Scan with YARA (pattern-based malware detection)
        4. If clean: organize files based on media type
        5. If infected: quarantine
        """
        # Get or create scan result
        scan_result = self.db.query(ScanResult).filter(
            ScanResult.torrent_hash == torrent_hash
        ).first()
        
        if not scan_result:
            scan_result = ScanResult(torrent_hash=torrent_hash)
            self.db.add(scan_result)
        
        scan_result.status = ScanStatus.SCANNING
        scan_result.scan_started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Get torrent info
            torrent = self.db.query(TorrentItem).filter(
                TorrentItem.torrent_hash == torrent_hash
            ).first()
            
            if not torrent:
                scan_result.status = ScanStatus.ERROR
                scan_result.clamav_result = {"error": "Torrent not found in database"}
                self.db.commit()
                return scan_result
            
            # Get wishlist item for media type
            wishlist_item = self.db.query(WishlistItem).filter(
                WishlistItem.rating_key == torrent.rating_key
            ).first()
            
            if not wishlist_item:
                scan_result.status = ScanStatus.ERROR
                scan_result.clamav_result = {"error": "Wishlist item not found"}
                self.db.commit()
                return scan_result
            
            # Get files to scan
            files = self.get_torrent_files(torrent.save_path or settings.downloads_path, torrent.name or "")
            
            if not files:
                scan_result.status = ScanStatus.ERROR
                scan_result.clamav_result = {"error": "No media files found"}
                self.db.commit()
                return scan_result
            
            scan_result.original_path = files[0] if len(files) == 1 else str(Path(files[0]).parent)
            
            # Scan each file
            all_clean = True
            threat_names = []
            
            for file_path in files:
                # Layer 1: ClamAV
                clamav_result = self.scan_with_clamav(file_path)
                scan_result.clamav_result = clamav_result
                
                if clamav_result.get("status") == "infected":
                    all_clean = False
                    threat_names.append(f"ClamAV: {clamav_result.get('virus_name', 'Unknown')}")
                
                # Layer 2: YARA
                yara_result = self.scan_with_yara(file_path)
                scan_result.yara_result = yara_result
                
                if yara_result.get("status") == "infected":
                    all_clean = False
                    rules = yara_result.get('matched_rules', [])
                    threat_names.append(f"YARA: {', '.join(rules)}")
            
            # Process results
            if all_clean:
                scan_result.status = ScanStatus.CLEAN
                
                # Organize files based on media type
                for file_path in files:
                    if wishlist_item.media_type in [MediaType.MOVIE]:
                        dest = self.organize_movie(
                            file_path,
                            wishlist_item.title,
                            wishlist_item.year
                        )
                    elif wishlist_item.media_type in [MediaType.SHOW, MediaType.SEASON, MediaType.EPISODE]:
                        # Parse episode info from filename
                        episode_info = self.parse_episode_info(Path(file_path).name)
                        
                        if episode_info:
                            season, episodes = episode_info
                        else:
                            # Default to Season 1 Episode 1 if parsing fails
                            season, episodes = 1, [1]
                            logger.warning(f"Could not parse episode info from {file_path}, using defaults")
                        
                        dest = self.organize_tvshow(
                            file_path,
                            wishlist_item.title,
                            wishlist_item.year,
                            season,
                            episodes
                        )
                    else:
                        # Unknown type - move to movies as fallback
                        dest = self.organize_movie(
                            file_path,
                            wishlist_item.title,
                            wishlist_item.year
                        )
                    
                    scan_result.destination_path = dest
            else:
                scan_result.status = ScanStatus.INFECTED
                scan_result.threat_name = "; ".join(threat_names)
                
                # Quarantine infected files
                for file_path in files:
                    if os.path.exists(file_path):
                        dest = self.quarantine_file(file_path, scan_result.threat_name)
                        scan_result.destination_path = dest
            
            scan_result.scan_completed_at = datetime.utcnow()
            self.db.commit()
            
            return scan_result
            
        except Exception as e:
            logger.exception(f"Error scanning torrent {torrent_hash}")
            scan_result.status = ScanStatus.ERROR
            scan_result.clamav_result = {"error": str(e)}
            scan_result.scan_completed_at = datetime.utcnow()
            self.db.commit()
            return scan_result

    def get_scan_result(self, torrent_hash: str) -> Optional[ScanResult]:
        """Get scan result by torrent hash."""
        return self.db.query(ScanResult).filter(
            ScanResult.torrent_hash == torrent_hash
        ).first()

    def get_scan_stats(self) -> Dict[str, int]:
        """Get scanner statistics."""
        from sqlalchemy import func
        
        stats = self.db.query(
            ScanResult.status,
            func.count(ScanResult.id)
        ).group_by(ScanResult.status).all()
        
        result = {
            "total_scans": 0,
            "clean": 0,
            "infected": 0,
            "errors": 0,
            "pending": 0
        }
        
        for status, count in stats:
            result["total_scans"] += count
            if status == ScanStatus.CLEAN:
                result["clean"] = count
            elif status == ScanStatus.INFECTED:
                result["infected"] = count
            elif status == ScanStatus.ERROR:
                result["errors"] = count
            elif status in [ScanStatus.PENDING, ScanStatus.SCANNING]:
                result["pending"] += count
        
        return result

