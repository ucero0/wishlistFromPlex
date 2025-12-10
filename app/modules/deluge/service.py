"""Deluge module service - handles Deluge daemon interactions."""
import logging
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session
from deluge_web_client import DelugeWebClient

from app.core.config import settings
from app.modules.deluge.models import TorrentItem, TorrentStatus
from app.modules.deluge.schemas import TorrentInfoResponse

logger = logging.getLogger(__name__)


# =============================================================================
# Deluge Client Connection
# =============================================================================

class DelugeClientWrapper:
    """Wrapper around DelugeWebClient to provide a call() method compatible with deluge-client API."""
    
    def __init__(self, client: DelugeWebClient):
        self.client = client
    
    def _extract_result(self, response):
        """Extract actual result from Response object or return as-is."""
        if hasattr(response, 'result'):
            return response.result
        elif hasattr(response, 'data'):
            return response.data
        else:
            return response
    
    def call(self, method: str, *args):
        """
        Call a Deluge RPC method by mapping to deluge-web-client specific methods.
        
        Args:
            method: RPC method name (e.g., "core.add_torrent_magnet", "core.get_torrent_status")
            *args: Arguments to pass to the method
            
        Returns:
            Method result
        """
        # Map RPC methods to deluge-web-client specific methods
        if method == "core.add_torrent_magnet":
            # add_torrent_magnet(uri: str, torrent_options: TorrentOptions) -> Response
            magnet_link = args[0] if args else ""
            options = args[1] if len(args) > 1 else {}
            from deluge_web_client.schema import TorrentOptions
            
            # Create TorrentOptions from options dict or use defaults
            if options:
                torrent_options = TorrentOptions(**options)
            else:
                torrent_options = TorrentOptions()
            
            result = self.client.add_torrent_magnet(magnet_link, torrent_options)
            return self._extract_result(result)
        
        elif method == "core.add_torrent_url":
            # add_torrent_url(url: str, torrent_options: TorrentOptions) -> Response
            url = args[0] if args else ""
            options = args[1] if len(args) > 1 else {}
            from deluge_web_client.schema import TorrentOptions
            
            # Create TorrentOptions from options dict or use defaults
            if options:
                torrent_options = TorrentOptions(**options)
            else:
                torrent_options = TorrentOptions()
            
            result = self.client.add_torrent_url(url, torrent_options)
            return self._extract_result(result)
        
        elif method == "core.add_torrent_file":
            # upload_torrent(torrent_path: str, torrent_options: TorrentOptions) -> Response
            filename = args[0] if args else "torrent.torrent"
            torrent_data = args[1] if len(args) > 1 else ""
            options = args[2] if len(args) > 2 else {}
            # Convert base64 string back to bytes if needed
            import base64
            import tempfile
            import os
            from deluge_web_client.schema import TorrentOptions
            
            if isinstance(torrent_data, str):
                torrent_bytes = base64.b64decode(torrent_data)
            else:
                torrent_bytes = torrent_data
            
            # Write torrent data to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.torrent') as tmp_file:
                tmp_file.write(torrent_bytes)
                tmp_path = tmp_file.name
            
            try:
                # Create TorrentOptions from options dict or use defaults
                if options:
                    torrent_options = TorrentOptions(**options)
                else:
                    torrent_options = TorrentOptions()
                
                result = self.client.upload_torrent(tmp_path, torrent_options)
                return self._extract_result(result)
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        
        elif method == "core.get_torrent_status":
            # get_torrent_status(torrent_hash: str, fields: list) -> dict
            torrent_hash = args[0] if args else ""
            fields = args[1] if len(args) > 1 else []
            status = self.client.get_torrent_status(torrent_hash, fields)
            return self._extract_result(status)
        
        elif method == "core.get_torrents_status":
            # get_torrents_status(filters: dict, fields: list) -> dict
            filters = args[0] if args else {}
            fields = args[1] if len(args) > 1 else []
            result = self.client.get_torrents_status(filters, fields)
            return self._extract_result(result)
        
        elif method == "core.remove_torrent":
            # remove_torrent(torrent_hash: str, remove_data: bool) -> None
            torrent_hash = args[0] if args else ""
            remove_data = args[1] if len(args) > 1 else False
            self.client.remove_torrent(torrent_hash, remove_data)
            return True
        
        elif method == "daemon.info":
            # Try to get libtorrent version as a proxy for daemon info
            version_response = self.client.get_libtorrent_version()
            return self._extract_result(version_response)
        
        else:
            # Fallback: try execute_call for unknown methods
            payload = {
                "method": method,
                "params": list(args)
            }
            try:
                response = self.client.execute_call(payload)
                if hasattr(response, 'result'):
                    return response.result
                elif hasattr(response, 'data'):
                    return response.data
                else:
                    return response
            except Exception as e:
                logger.error(f"Unknown method {method} and execute_call failed: {e}")
                raise


def get_deluge_client() -> DelugeClientWrapper:
    """
    Create and return a Deluge Web API client connection.
    
    Uses HTTP-based Web API which is compatible with Deluge 2.x.
    Uses WebUI port (8112) for HTTP communication.
    
    Returns:
        DelugeClientWrapper: Wrapped client with call() method
        
    Raises:
        Exception: If connection fails
    """
    # Build WebUI URL
    webui_url = f"http://{settings.deluge_host}:{settings.deluge_webui_port}"
    
    # DelugeWebClient API: __init__(url: str, password: str, daemon_port: int = 58846)
    # Note: Even though it's called "web-client", it may still use daemon_port for RPC calls
    # We'll try setting daemon_port to None or 0 to force HTTP-only if possible
    client = DelugeWebClient(
        url=webui_url,
        password=settings.deluge_password,
        daemon_port=settings.deluge_port,  # Still needed for some operations
    )
    
    # Login/connect if needed
    try:
        if hasattr(client, 'login'):
            client.login()
        elif hasattr(client, 'connect_to_host'):
            # May need to connect to a host first
            hosts = client.get_hosts()
            if hosts:
                host_id = hosts[0].get('id') if isinstance(hosts[0], dict) else hosts[0].id
                client.connect_to_host(host_id)
    except Exception as e:
        logger.warning(f"Could not login/connect to Deluge (may be automatic): {e}")
    
    return DelugeClientWrapper(client)


def test_connection() -> tuple[bool, Optional[str], Optional[str]]:
    """
    Test connection to Deluge daemon.
    
    Returns:
        Tuple of (success, daemon_version, error_message)
    """
    try:
        client = get_deluge_client()
        # Try to get daemon info using execute_call
        try:
            version = client.call("daemon.info")
            return True, str(version), None
        except Exception:
            # Fallback: try to get libtorrent version as a connection test
            version = client.client.get_libtorrent_version()
            return True, f"libtorrent-{version}", None
    except Exception as e:
        logger.error(f"Failed to connect to Deluge: {e}")
        return False, None, str(e)


# =============================================================================
# Extract Torrent Data
# =============================================================================

def extract_torrent_data(torrent_hash: str) -> Optional[TorrentInfoResponse]:
    """
    Extract detailed data for a specific torrent from Deluge daemon.
    
    Args:
        torrent_hash: The torrent hash to query
        
    Returns:
        TorrentInfoResponse with torrent details, or None if not found
    """
    try:
        client = get_deluge_client()
        
        # Fields to request from Deluge
        fields = [
            "name", "state", "progress", "total_size", "total_done",
            "total_uploaded", "download_payload_rate", "upload_payload_rate",
            "save_path", "num_seeds", "num_peers", "ratio", "eta",
            "is_finished", "paused"
        ]
        
        result = client.call("core.get_torrent_status", torrent_hash, fields)
        
        if not result:
            logger.warning(f"Torrent {torrent_hash} not found in Deluge")
            return None
        
        return TorrentInfoResponse(
            torrent_hash=torrent_hash,
            name=result.get(b"name", b"").decode("utf-8") if isinstance(result.get(b"name"), bytes) else result.get("name", ""),
            state=result.get(b"state", b"").decode("utf-8") if isinstance(result.get(b"state"), bytes) else result.get("state", ""),
            progress=float(result.get(b"progress", 0) or result.get("progress", 0)),
            total_size=int(result.get(b"total_size", 0) or result.get("total_size", 0)),
            downloaded=int(result.get(b"total_done", 0) or result.get("total_done", 0)),
            uploaded=int(result.get(b"total_uploaded", 0) or result.get("total_uploaded", 0)),
            download_speed=int(result.get(b"download_payload_rate", 0) or result.get("download_payload_rate", 0)),
            upload_speed=int(result.get(b"upload_payload_rate", 0) or result.get("upload_payload_rate", 0)),
            save_path=result.get(b"save_path", b"").decode("utf-8") if isinstance(result.get(b"save_path"), bytes) else result.get("save_path", ""),
            num_seeds=int(result.get(b"num_seeds", 0) or result.get("num_seeds", 0)),
            num_peers=int(result.get(b"num_peers", 0) or result.get("num_peers", 0)),
            ratio=float(result.get(b"ratio", 0) or result.get("ratio", 0)),
            eta=int(result.get(b"eta", -1) if result.get(b"eta") is not None else result.get("eta", -1)),
            is_finished=bool(result.get(b"is_finished", False) or result.get("is_finished", False)),
            paused=bool(result.get(b"paused", False) or result.get("paused", False)),
        )
        
    except Exception as e:
        logger.error(f"Error extracting torrent data for {torrent_hash}: {e}")
        return None


def get_all_torrents_info() -> list[TorrentInfoResponse]:
    """
    Get info for all torrents from Deluge daemon.
    
    Returns:
        List of TorrentInfoResponse for all torrents
    """
    try:
        client = get_deluge_client()
        
        fields = [
            "name", "state", "progress", "total_size", "total_done",
            "total_uploaded", "download_payload_rate", "upload_payload_rate",
            "save_path", "num_seeds", "num_peers", "ratio", "eta",
            "is_finished", "paused"
        ]
        
        # Get all torrents
        result = client.call("core.get_torrents_status", {}, fields)
        
        torrents = []
        for hash_bytes, data in result.items():
            torrent_hash = hash_bytes.decode("utf-8") if isinstance(hash_bytes, bytes) else hash_bytes
            
            torrents.append(TorrentInfoResponse(
                torrent_hash=torrent_hash,
                name=data.get(b"name", b"").decode("utf-8") if isinstance(data.get(b"name"), bytes) else data.get("name", ""),
                state=data.get(b"state", b"").decode("utf-8") if isinstance(data.get(b"state"), bytes) else data.get("state", ""),
                progress=float(data.get(b"progress", 0) or data.get("progress", 0)),
                total_size=int(data.get(b"total_size", 0) or data.get("total_size", 0)),
                downloaded=int(data.get(b"total_done", 0) or data.get("total_done", 0)),
                uploaded=int(data.get(b"total_uploaded", 0) or data.get("total_uploaded", 0)),
                download_speed=int(data.get(b"download_payload_rate", 0) or data.get("download_payload_rate", 0)),
                upload_speed=int(data.get(b"upload_payload_rate", 0) or data.get("upload_payload_rate", 0)),
                save_path=data.get(b"save_path", b"").decode("utf-8") if isinstance(data.get(b"save_path"), bytes) else data.get("save_path", ""),
                num_seeds=int(data.get(b"num_seeds", 0) or data.get("num_seeds", 0)),
                num_peers=int(data.get(b"num_peers", 0) or data.get("num_peers", 0)),
                ratio=float(data.get(b"ratio", 0) or data.get("ratio", 0)),
                eta=int(data.get(b"eta", -1) if data.get(b"eta") is not None else data.get("eta", -1)),
                is_finished=bool(data.get(b"is_finished", False) or data.get("is_finished", False)),
                paused=bool(data.get(b"paused", False) or data.get("paused", False)),
            ))
        
        return torrents
        
    except Exception as e:
        logger.error(f"Error getting all torrents: {e}")
        return []


# =============================================================================
# Add Torrent
# =============================================================================

def add_magnet(magnet_link: str, rating_key: str, db: Session) -> tuple[bool, Optional[str], Optional[TorrentItem]]:
    """
    Add a torrent to Deluge via magnet link and track it in database.
    
    Args:
        magnet_link: The magnet link to add
        rating_key: Plex rating_key to associate with this torrent
        db: Database session
        
    Returns:
        Tuple of (success, torrent_hash or error_message, TorrentItem or None)
    """
    try:
        client = get_deluge_client()
        
        # Add magnet to Deluge
        # Returns torrent_hash on success
        torrent_hash = client.call("core.add_torrent_magnet", magnet_link, {})
        
        if not torrent_hash:
            return False, "Failed to add magnet - Deluge returned no hash", None
        
        # Decode hash if bytes
        if isinstance(torrent_hash, bytes):
            torrent_hash = torrent_hash.decode("utf-8")
        
        logger.info(f"Added torrent {torrent_hash} for rating_key {rating_key}")
        
        # Get initial torrent info
        fields = ["name", "save_path", "total_size"]
        info = client.call("core.get_torrent_status", torrent_hash, fields)
        
        # Create database record
        torrent_item = TorrentItem(
            rating_key=rating_key,
            torrent_hash=torrent_hash,
            magnet_link=magnet_link,
            name=info.get(b"name", b"").decode("utf-8") if isinstance(info.get(b"name"), bytes) else info.get("name"),
            save_path=info.get(b"save_path", b"").decode("utf-8") if isinstance(info.get(b"save_path"), bytes) else info.get("save_path"),
            total_size=int(info.get(b"total_size", 0) or info.get("total_size", 0)),
            status=TorrentStatus.QUEUED,
        )
        
        db.add(torrent_item)
        db.commit()
        db.refresh(torrent_item)
        
        return True, torrent_hash, torrent_item
        
    except Exception as e:
        logger.error(f"Error adding magnet: {e}")
        db.rollback()
        return False, str(e), None


def add_torrent_url(download_url: str, rating_key: str, db: Session) -> tuple[bool, Optional[str], Optional[TorrentItem]]:
    """
    Add a torrent to Deluge via HTTP/HTTPS URL (downloads .torrent file) and track it in database.
    
    Args:
        download_url: The HTTP/HTTPS URL to download the torrent file from
        rating_key: Plex rating_key to associate with this torrent
        db: Database session
        
    Returns:
        Tuple of (success, torrent_hash or error_message, TorrentItem or None)
    """
    try:
        client = get_deluge_client()
        
        # Add torrent from URL - Deluge will download the .torrent file
        # Returns torrent_hash on success
        torrent_hash = client.call("core.add_torrent_url", download_url, {})
        
        if not torrent_hash:
            return False, "Failed to add torrent from URL - Deluge returned no hash", None
        
        # Decode hash if bytes
        if isinstance(torrent_hash, bytes):
            torrent_hash = torrent_hash.decode("utf-8")
        
        logger.info(f"Added torrent {torrent_hash} from URL for rating_key {rating_key}")
        
        # Get initial torrent info
        fields = ["name", "save_path", "total_size"]
        info = client.call("core.get_torrent_status", torrent_hash, fields)
        
        # Create database record
        torrent_item = TorrentItem(
            rating_key=rating_key,
            torrent_hash=torrent_hash,
            magnet_link=download_url,  # Store URL in magnet_link field for reference
            name=info.get(b"name", b"").decode("utf-8") if isinstance(info.get(b"name"), bytes) else info.get("name"),
            save_path=info.get(b"save_path", b"").decode("utf-8") if isinstance(info.get(b"save_path"), bytes) else info.get("save_path"),
            total_size=int(info.get(b"total_size", 0) or info.get("total_size", 0)),
            status=TorrentStatus.QUEUED,
        )
        
        db.add(torrent_item)
        db.commit()
        db.refresh(torrent_item)
        
        return True, torrent_hash, torrent_item
        
    except Exception as e:
        logger.error(f"Error adding torrent from URL: {e}")
        db.rollback()
        return False, str(e), None


def add_torrent_file(torrent_file_data: bytes, rating_key: str, db: Session) -> tuple[bool, Optional[str], Optional[TorrentItem]]:
    """
    Add a torrent to Deluge from torrent file binary data and track it in database.
    
    Args:
        torrent_file_data: Binary data of the .torrent file
        rating_key: Plex rating_key to associate with this torrent
        db: Database session
        
    Returns:
        Tuple of (success, torrent_hash or error_message, TorrentItem or None)
    """
    try:
        client = get_deluge_client()
        
        # Deluge Web API: core.add_torrent_file(filename, torrent_file_base64, options)
        # For HTTP API, we need to base64 encode the torrent file data
        import base64
        torrent_base64 = base64.b64encode(torrent_file_data).decode('utf-8')
        torrent_hash = client.call("core.add_torrent_file", f"{rating_key}.torrent", torrent_base64, {})
        
        if not torrent_hash:
            return False, "Failed to add torrent from file - Deluge returned no hash", None
        
        # Decode hash if bytes
        if isinstance(torrent_hash, bytes):
            torrent_hash = torrent_hash.decode("utf-8")
        
        logger.info(f"Added torrent {torrent_hash} from file data for rating_key {rating_key}")
        
        # Get initial torrent info
        fields = ["name", "save_path", "total_size"]
        info = client.call("core.get_torrent_status", torrent_hash, fields)
        
        # Create database record
        torrent_item = TorrentItem(
            rating_key=rating_key,
            torrent_hash=torrent_hash,
            magnet_link=None,  # No magnet link when adding from file
            name=info.get(b"name", b"").decode("utf-8") if isinstance(info.get(b"name"), bytes) else info.get("name"),
            save_path=info.get(b"save_path", b"").decode("utf-8") if isinstance(info.get(b"save_path"), bytes) else info.get("save_path"),
            total_size=int(info.get(b"total_size", 0) or info.get("total_size", 0)),
            status=TorrentStatus.QUEUED,
        )
        
        db.add(torrent_item)
        db.commit()
        db.refresh(torrent_item)
        
        return True, torrent_hash, torrent_item
        
    except Exception as e:
        logger.error(f"Error adding torrent from file: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        db.rollback()
        return False, str(e), None


# =============================================================================
# Remove Torrent
# =============================================================================

def remove_torrent(torrent_hash: str, remove_data: bool, db: Session) -> tuple[bool, str]:
    """
    Remove a torrent from Deluge.
    
    Args:
        torrent_hash: The torrent hash to remove
        remove_data: If True, also delete downloaded files
        db: Database session
        
    Returns:
        Tuple of (success, message)
    """
    try:
        client = get_deluge_client()
        
        # Remove from Deluge
        # remove_torrent(torrent_id, remove_data)
        result = client.call("core.remove_torrent", torrent_hash, remove_data)
        
        if result:
            # Update database record
            torrent_item = db.query(TorrentItem).filter(
                TorrentItem.torrent_hash == torrent_hash
            ).first()
            
            if torrent_item:
                torrent_item.status = TorrentStatus.REMOVED
                db.commit()
            
            action = "and data" if remove_data else "only (data kept)"
            logger.info(f"Removed torrent {torrent_hash} {action}")
            return True, f"Torrent removed {action}"
        else:
            return False, "Deluge failed to remove torrent"
            
    except Exception as e:
        logger.error(f"Error removing torrent {torrent_hash}: {e}")
        db.rollback()
        return False, str(e)


def remove_torrent_by_rating_key(rating_key: str, remove_data: bool, db: Session) -> tuple[bool, str, list[str]]:
    """
    Remove all torrents associated with a rating_key.
    
    Args:
        rating_key: Plex rating_key
        remove_data: If True, also delete downloaded files
        db: Database session
        
    Returns:
        Tuple of (success, message, list of removed hashes)
    """
    try:
        torrent_items = db.query(TorrentItem).filter(
            TorrentItem.rating_key == rating_key,
            TorrentItem.status != TorrentStatus.REMOVED
        ).all()
        
        if not torrent_items:
            return False, f"No active torrents found for rating_key {rating_key}", []
        
        removed_hashes = []
        errors = []
        
        for item in torrent_items:
            success, message = remove_torrent(item.torrent_hash, remove_data, db)
            if success:
                removed_hashes.append(item.torrent_hash)
            else:
                errors.append(f"{item.torrent_hash}: {message}")
        
        if removed_hashes:
            if errors:
                return True, f"Removed {len(removed_hashes)} torrents, {len(errors)} failed", removed_hashes
            return True, f"Removed {len(removed_hashes)} torrent(s)", removed_hashes
        else:
            return False, f"Failed to remove torrents: {'; '.join(errors)}", []
            
    except Exception as e:
        logger.error(f"Error removing torrents for rating_key {rating_key}: {e}")
        return False, str(e), []


# =============================================================================
# Sync Torrent Status
# =============================================================================

def _map_deluge_state(state: str) -> TorrentStatus:
    """Map Deluge state string to TorrentStatus enum."""
    state_map = {
        "Queued": TorrentStatus.QUEUED,
        "Downloading": TorrentStatus.DOWNLOADING,
        "Seeding": TorrentStatus.SEEDING,
        "Paused": TorrentStatus.PAUSED,
        "Checking": TorrentStatus.CHECKING,
        "Error": TorrentStatus.ERROR,
    }
    return state_map.get(state, TorrentStatus.QUEUED)


def sync_torrent_status(db: Session) -> tuple[int, int]:
    """
    Sync all tracked torrents with current Deluge status.
    
    Args:
        db: Database session
        
    Returns:
        Tuple of (synced_count, error_count)
    """
    try:
        # Get all active torrents from database
        torrent_items = db.query(TorrentItem).filter(
            TorrentItem.status.notin_([TorrentStatus.REMOVED, TorrentStatus.COMPLETED])
        ).all()
        
        if not torrent_items:
            return 0, 0
        
        # Get all torrents from Deluge
        all_daemon_torrents = get_all_torrents_info()
        daemon_map = {t.torrent_hash: t for t in all_daemon_torrents}
        
        synced = 0
        errors = 0
        
        for item in torrent_items:
            daemon_info = daemon_map.get(item.torrent_hash)
            
            if not daemon_info:
                # Torrent no longer in Deluge
                item.status = TorrentStatus.REMOVED
                synced += 1
                continue
            
            try:
                # Update from daemon
                item.name = daemon_info.name
                item.status = _map_deluge_state(daemon_info.state)
                item.progress = daemon_info.progress
                item.total_size = daemon_info.total_size
                item.downloaded = daemon_info.downloaded
                item.uploaded = daemon_info.uploaded
                item.download_speed = daemon_info.download_speed
                item.upload_speed = daemon_info.upload_speed
                item.save_path = daemon_info.save_path
                item.num_seeds = daemon_info.num_seeds
                item.num_peers = daemon_info.num_peers
                item.ratio = daemon_info.ratio
                item.eta = daemon_info.eta
                
                # Mark as completed if finished
                if daemon_info.is_finished and item.status != TorrentStatus.COMPLETED:
                    item.status = TorrentStatus.COMPLETED
                    item.completed_at = datetime.utcnow()
                
                synced += 1
                
            except Exception as e:
                logger.error(f"Error syncing torrent {item.torrent_hash}: {e}")
                errors += 1
        
        db.commit()
        logger.info(f"Synced {synced} torrents, {errors} errors")
        return synced, errors
        
    except Exception as e:
        logger.error(f"Error syncing torrent status: {e}")
        db.rollback()
        return 0, 1


# =============================================================================
# Query Functions
# =============================================================================

def get_torrents_by_rating_key(rating_key: str, db: Session) -> list[TorrentItem]:
    """Get all torrents associated with a rating_key."""
    return db.query(TorrentItem).filter(
        TorrentItem.rating_key == rating_key
    ).order_by(TorrentItem.added_at.desc()).all()


def get_torrent_by_hash(torrent_hash: str, db: Session) -> Optional[TorrentItem]:
    """Get a torrent by its hash."""
    return db.query(TorrentItem).filter(
        TorrentItem.torrent_hash == torrent_hash
    ).first()


def get_all_tracked_torrents(
    db: Session,
    status: Optional[TorrentStatus] = None,
    limit: int = 100,
    offset: int = 0
) -> tuple[list[TorrentItem], int]:
    """
    Get all tracked torrents with optional filtering.
    
    Returns:
        Tuple of (list of TorrentItems, total count)
    """
    query = db.query(TorrentItem)
    
    if status:
        query = query.filter(TorrentItem.status == status)
    
    total = query.count()
    items = query.order_by(TorrentItem.added_at.desc()).offset(offset).limit(limit).all()
    
    return items, total

