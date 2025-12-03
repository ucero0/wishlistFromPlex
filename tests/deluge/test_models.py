"""Tests for Deluge SQLAlchemy models."""
import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.modules.deluge.models import TorrentItem, TorrentStatus


class TestTorrentItemModel:
    """Tests for TorrentItem model."""

    def test_create_torrent_item_minimal(self, db_session):
        """Test creating a torrent item with minimal fields."""
        item = TorrentItem(
            rating_key="abc123",
            torrent_hash="a" * 40,  # 40 char hex hash
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.rating_key == "abc123"
        assert item.torrent_hash == "a" * 40
        assert item.status == TorrentStatus.QUEUED
        assert item.progress == 0.0
        assert item.added_at is not None

    def test_create_torrent_item_full(self, db_session):
        """Test creating a torrent item with all fields."""
        item = TorrentItem(
            rating_key="movie123",
            torrent_hash="b" * 40,
            magnet_link="magnet:?xt=urn:btih:" + "b" * 40,
            name="Test.Movie.2024.1080p.BluRay.x264",
            status=TorrentStatus.DOWNLOADING,
            progress=45.5,
            total_size=2147483648,  # 2GB
            downloaded=976744448,
            uploaded=104857600,
            download_speed=5242880,  # 5MB/s
            upload_speed=1048576,  # 1MB/s
            save_path="/downloads/movies",
            num_seeds=15,
            num_peers=3,
            ratio=0.1,
            eta=3600,
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.name == "Test.Movie.2024.1080p.BluRay.x264"
        assert item.status == TorrentStatus.DOWNLOADING
        assert item.progress == 45.5
        assert item.total_size == 2147483648
        assert item.save_path == "/downloads/movies"

    def test_torrent_hash_unique(self, db_session):
        """Test that torrent hash must be unique."""
        hash_value = "c" * 40
        item1 = TorrentItem(rating_key="key1", torrent_hash=hash_value)
        item2 = TorrentItem(rating_key="key2", torrent_hash=hash_value)
        
        db_session.add(item1)
        db_session.commit()
        
        db_session.add(item2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_same_rating_key_different_hashes(self, db_session):
        """Test that same rating_key can have multiple torrents (different formats)."""
        item1 = TorrentItem(
            rating_key="movie123",
            torrent_hash="d" * 40,
            name="Movie.2024.720p",
        )
        item2 = TorrentItem(
            rating_key="movie123",
            torrent_hash="e" * 40,
            name="Movie.2024.1080p",
        )
        
        db_session.add_all([item1, item2])
        db_session.commit()
        
        # Both should exist with same rating_key
        items = db_session.query(TorrentItem).filter(
            TorrentItem.rating_key == "movie123"
        ).all()
        assert len(items) == 2

    def test_torrent_status_transitions(self, db_session):
        """Test updating torrent status."""
        item = TorrentItem(
            rating_key="test",
            torrent_hash="f" * 40,
            status=TorrentStatus.QUEUED,
        )
        db_session.add(item)
        db_session.commit()
        
        # Update status
        item.status = TorrentStatus.DOWNLOADING
        item.progress = 10.0
        db_session.commit()
        
        db_session.refresh(item)
        assert item.status == TorrentStatus.DOWNLOADING
        assert item.progress == 10.0
        
        # Mark completed
        item.status = TorrentStatus.COMPLETED
        item.progress = 100.0
        item.completed_at = datetime.now(timezone.utc)
        db_session.commit()
        
        db_session.refresh(item)
        assert item.status == TorrentStatus.COMPLETED
        assert item.completed_at is not None

    def test_query_by_status(self, db_session):
        """Test querying torrents by status."""
        items = [
            TorrentItem(rating_key="1", torrent_hash="1" * 40, status=TorrentStatus.DOWNLOADING),
            TorrentItem(rating_key="2", torrent_hash="2" * 40, status=TorrentStatus.DOWNLOADING),
            TorrentItem(rating_key="3", torrent_hash="3" * 40, status=TorrentStatus.SEEDING),
            TorrentItem(rating_key="4", torrent_hash="4" * 40, status=TorrentStatus.COMPLETED),
        ]
        db_session.add_all(items)
        db_session.commit()
        
        downloading = db_session.query(TorrentItem).filter(
            TorrentItem.status == TorrentStatus.DOWNLOADING
        ).all()
        assert len(downloading) == 2
        
        seeding = db_session.query(TorrentItem).filter(
            TorrentItem.status == TorrentStatus.SEEDING
        ).all()
        assert len(seeding) == 1

    def test_query_exclude_removed(self, db_session):
        """Test excluding removed torrents from queries."""
        items = [
            TorrentItem(rating_key="active", torrent_hash="a1" + "0" * 38, status=TorrentStatus.DOWNLOADING),
            TorrentItem(rating_key="removed", torrent_hash="r1" + "0" * 38, status=TorrentStatus.REMOVED),
        ]
        db_session.add_all(items)
        db_session.commit()
        
        active = db_session.query(TorrentItem).filter(
            TorrentItem.status != TorrentStatus.REMOVED
        ).all()
        assert len(active) == 1
        assert active[0].rating_key == "active"


class TestTorrentStatusEnum:
    """Tests for TorrentStatus enum."""

    def test_status_values(self):
        """Test TorrentStatus enum values."""
        assert TorrentStatus.QUEUED.value == "queued"
        assert TorrentStatus.DOWNLOADING.value == "downloading"
        assert TorrentStatus.SEEDING.value == "seeding"
        assert TorrentStatus.PAUSED.value == "paused"
        assert TorrentStatus.CHECKING.value == "checking"
        assert TorrentStatus.ERROR.value == "error"
        assert TorrentStatus.COMPLETED.value == "completed"
        assert TorrentStatus.REMOVED.value == "removed"

    def test_status_from_string(self, db_session):
        """Test creating status from string value."""
        status = TorrentStatus("downloading")
        assert status == TorrentStatus.DOWNLOADING
        
        status = TorrentStatus("seeding")
        assert status == TorrentStatus.SEEDING

    def test_status_comparison(self, db_session):
        """Test comparing status in queries."""
        item = TorrentItem(
            rating_key="compare",
            torrent_hash="cc" + "0" * 38,
            status=TorrentStatus.SEEDING,
        )
        db_session.add(item)
        db_session.commit()
        
        result = db_session.query(TorrentItem).filter(
            TorrentItem.status == TorrentStatus.SEEDING
        ).first()
        
        assert result is not None
        assert result.status == TorrentStatus.SEEDING

