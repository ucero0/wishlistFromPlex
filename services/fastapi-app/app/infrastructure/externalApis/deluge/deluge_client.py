"""Deluge RPC client - infrastructure layer."""
# Note: This file should be renamed to client.py to match the structure
import logging
from typing import Optional, List, Dict, Any
from deluge_client import DelugeRPCClient

from app.core.config import settings

logger = logging.getLogger(__name__)


def decode_rpc(obj):
    """
    Recursively converts bytes to strings inside any structure
    (dict, list, tuple, set, etc.) returned by Deluge RPC.
    This returns JSON-serializable data.
    """
    # Convert bytes -> str
    if isinstance(obj, bytes):
        return obj.decode(errors="ignore")

    # Convert dict keys + values
    if isinstance(obj, dict):
        return {
            decode_rpc(key): decode_rpc(value)
            for key, value in obj.items()
        }

    # Convert lists
    if isinstance(obj, list):
        return [decode_rpc(item) for item in obj]

    # Convert tuples
    if isinstance(obj, tuple):
        return tuple(decode_rpc(item) for item in obj)

    # Convert sets
    if isinstance(obj, set):
        return {decode_rpc(item) for item in obj}

    # Leave all other types unchanged (int, float, None, bool)
    return obj


class DelugeClient:
    """Infrastructure client for Deluge RPC communication."""
    
    def __init__(self):
        self.host = settings.deluge_host 
        self.port = settings.deluge_port
        self.username = settings.deluge_username
        self.password = settings.deluge_password
        self.client = DelugeRPCClient(self.host, self.port, self.username, self.password)
        self.is_connected = False

    def connect(self) -> bool:
        """Connect to the Deluge daemon."""
        if self.is_connected:
            return True
        try:
            self.client.connect()
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Error connecting to Deluge: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from the Deluge daemon."""
        if not self.is_connected:
            return True
        try:
            self.client.disconnect()
            self.is_connected = False
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Deluge: {e}")
            return False
    
    def get_torrents_status(self, fields: List[str]) -> Dict[str, Any]:
        """Get the status of all torrents from Deluge."""
        if not self.connect():
            return {}
        
        try:
            torrents = self.client.call("core.get_torrents_status", {}, fields)
            return decode_rpc(torrents)
        except Exception as e:
            logger.error(f"Error getting torrents status: {e}")
            return {}

