"""Repository for torrent persistence operations."""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.infrastructure.persistence.models.torrent import TorrentItem, TorrentStatus


class TorrentRepository:
    """Repository for TorrentItem ORM operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_hash(self, torrent_hash: str) -> Optional[TorrentItem]:
        """Get a torrent by its hash."""
        return self.db.query(TorrentItem).filter(
            TorrentItem.torrent_hash == torrent_hash
        ).first()
    
    def get_by_guid_plex(self, guid_plex: str) -> List[TorrentItem]:
        """Get all torrents for a Plex GUID."""
        return self.db.query(TorrentItem).filter(
            TorrentItem.guidPlex == guid_plex
        ).all()
    
    def get_by_status(self, status: TorrentStatus) -> List[TorrentItem]:
        """Get all torrents with a specific status."""
        return self.db.query(TorrentItem).filter(
            TorrentItem.status == status
        ).all()
    
    def create(self, torrent: TorrentItem) -> TorrentItem:
        """Create a new torrent."""
        self.db.add(torrent)
        self.db.commit()
        self.db.refresh(torrent)
        return torrent
    
    def update(self, torrent: TorrentItem) -> TorrentItem:
        """Update an existing torrent."""
        self.db.commit()
        self.db.refresh(torrent)
        return torrent
    
    def delete(self, torrent: TorrentItem) -> None:
        """Delete a torrent."""
        self.db.delete(torrent)
        self.db.commit()

