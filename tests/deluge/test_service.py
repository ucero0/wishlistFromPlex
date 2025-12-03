"""Tests for Deluge service layer with mocked daemon calls."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.modules.deluge.service import (
    test_connection,
    extract_torrent_data,
    get_all_torrents_info,
    remove_torrent,
    remove_torrent_by_rating_key,
    sync_torrent_status,
    get_torrents_by_rating_key,
    get_torrent_by_hash,
    get_all_tracked_torrents,
    _map_deluge_state,
)
from app.modules.deluge.models import TorrentItem, TorrentStatus
from app.modules.deluge.schemas import TorrentInfoResponse


class TestConnection:
    """Tests for Deluge connection."""

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_connection_success(self, mock_get_client):
        """Test successful connection to Deluge."""
        mock_client = MagicMock()
        mock_client.call.return_value = "2.1.1"
        mock_get_client.return_value = mock_client
        
        connected, version, error = test_connection()
        
        assert connected is True
        assert version == "2.1.1"
        assert error is None

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_connection_failure(self, mock_get_client):
        """Test failed connection to Deluge."""
        mock_get_client.side_effect = Exception("Connection refused")
        
        connected, version, error = test_connection()
        
        assert connected is False
        assert version is None
        assert "Connection refused" in error


class TestExtractTorrentData:
    """Tests for extracting torrent data."""

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_extract_success(self, mock_get_client):
        """Test extracting torrent data successfully."""
        mock_client = MagicMock()
        mock_client.call.return_value = {
            b"name": b"Test.Movie.2024",
            b"state": b"Downloading",
            b"progress": 45.5,
            b"total_size": 2147483648,
            b"total_done": 976744448,
            b"total_uploaded": 104857600,
            b"download_payload_rate": 5242880,
            b"upload_payload_rate": 1048576,
            b"save_path": b"/downloads",
            b"num_seeds": 15,
            b"num_peers": 3,
            b"ratio": 0.1,
            b"eta": 3600,
            b"is_finished": False,
            b"paused": False,
        }
        mock_get_client.return_value = mock_client
        
        result = extract_torrent_data("a" * 40)
        
        assert result is not None
        assert result.name == "Test.Movie.2024"
        assert result.state == "Downloading"
        assert result.progress == 45.5

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_extract_not_found(self, mock_get_client):
        """Test extracting data for non-existent torrent."""
        mock_client = MagicMock()
        mock_client.call.return_value = {}
        mock_get_client.return_value = mock_client
        
        result = extract_torrent_data("nonexistent" + "0" * 30)
        
        assert result is None

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_extract_error(self, mock_get_client):
        """Test handling error during extraction."""
        mock_get_client.side_effect = Exception("Connection error")
        
        result = extract_torrent_data("a" * 40)
        
        assert result is None


class TestGetAllTorrentsInfo:
    """Tests for getting all torrents info."""

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_get_all_success(self, mock_get_client):
        """Test getting all torrents successfully."""
        mock_client = MagicMock()
        mock_client.call.return_value = {
            b"aaaa": {
                b"name": b"Movie1",
                b"state": b"Downloading",
                b"progress": 50.0,
                b"total_size": 1000000,
                b"total_done": 500000,
                b"total_uploaded": 100000,
                b"download_payload_rate": 1000,
                b"upload_payload_rate": 500,
                b"save_path": b"/downloads",
                b"num_seeds": 10,
                b"num_peers": 5,
                b"ratio": 0.1,
                b"eta": 1800,
                b"is_finished": False,
                b"paused": False,
            },
            b"bbbb": {
                b"name": b"Movie2",
                b"state": b"Seeding",
                b"progress": 100.0,
                b"total_size": 2000000,
                b"total_done": 2000000,
                b"total_uploaded": 4000000,
                b"download_payload_rate": 0,
                b"upload_payload_rate": 2000,
                b"save_path": b"/downloads",
                b"num_seeds": 20,
                b"num_peers": 15,
                b"ratio": 2.0,
                b"eta": -1,
                b"is_finished": True,
                b"paused": False,
            },
        }
        mock_get_client.return_value = mock_client
        
        result = get_all_torrents_info()
        
        assert len(result) == 2
        assert result[0].name in ["Movie1", "Movie2"]

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_get_all_empty(self, mock_get_client):
        """Test getting empty torrent list."""
        mock_client = MagicMock()
        mock_client.call.return_value = {}
        mock_get_client.return_value = mock_client
        
        result = get_all_torrents_info()
        
        assert result == []


class TestRemoveTorrent:
    """Tests for removing torrents."""

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_remove_torrent_only(self, mock_get_client, db_session):
        """Test removing torrent without data."""
        # Create a torrent to remove
        item = TorrentItem(
            rating_key="remove_test",
            torrent_hash="r" * 40,
            status=TorrentStatus.DOWNLOADING,
        )
        db_session.add(item)
        db_session.commit()
        
        mock_client = MagicMock()
        mock_client.call.return_value = True
        mock_get_client.return_value = mock_client
        
        success, message = remove_torrent("r" * 40, False, db_session)
        
        assert success is True
        assert "removed" in message.lower()
        
        # Verify status updated
        db_session.refresh(item)
        assert item.status == TorrentStatus.REMOVED

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_remove_torrent_and_data(self, mock_get_client, db_session):
        """Test removing torrent with data."""
        item = TorrentItem(
            rating_key="remove_data_test",
            torrent_hash="s" * 40,
            status=TorrentStatus.SEEDING,
        )
        db_session.add(item)
        db_session.commit()
        
        mock_client = MagicMock()
        mock_client.call.return_value = True
        mock_get_client.return_value = mock_client
        
        success, message = remove_torrent("s" * 40, True, db_session)
        
        assert success is True
        assert "data" in message.lower()

    @patch("app.modules.deluge.service.get_deluge_client")
    def test_remove_failure(self, mock_get_client, db_session):
        """Test handling remove failure."""
        item = TorrentItem(
            rating_key="fail_test",
            torrent_hash="t" * 40,
            status=TorrentStatus.DOWNLOADING,
        )
        db_session.add(item)
        db_session.commit()
        
        mock_client = MagicMock()
        mock_client.call.return_value = False
        mock_get_client.return_value = mock_client
        
        success, message = remove_torrent("t" * 40, False, db_session)
        
        assert success is False


class TestRemoveTorrentByRatingKey:
    """Tests for removing torrents by rating_key."""

    @patch("app.modules.deluge.service.remove_torrent")
    def test_remove_multiple(self, mock_remove, db_session):
        """Test removing multiple torrents for same rating_key."""
        items = [
            TorrentItem(rating_key="multi", torrent_hash="m1" + "0" * 38, status=TorrentStatus.DOWNLOADING),
            TorrentItem(rating_key="multi", torrent_hash="m2" + "0" * 38, status=TorrentStatus.SEEDING),
        ]
        db_session.add_all(items)
        db_session.commit()
        
        mock_remove.return_value = (True, "Removed")
        
        success, message, hashes = remove_torrent_by_rating_key("multi", False, db_session)
        
        assert success is True
        assert len(hashes) == 2

    def test_remove_not_found(self, db_session):
        """Test removing non-existent rating_key."""
        success, message, hashes = remove_torrent_by_rating_key("nonexistent", False, db_session)
        
        assert success is False
        assert hashes == []


class TestSyncTorrentStatus:
    """Tests for syncing torrent status."""

    @patch("app.modules.deluge.service.get_all_torrents_info")
    def test_sync_updates_progress(self, mock_get_all, db_session):
        """Test sync updates torrent progress."""
        # Create a torrent
        item = TorrentItem(
            rating_key="sync_test",
            torrent_hash="sync" + "0" * 36,
            status=TorrentStatus.QUEUED,
            progress=0.0,
        )
        db_session.add(item)
        db_session.commit()
        
        # Mock daemon response
        mock_get_all.return_value = [
            TorrentInfoResponse(
                torrent_hash="sync" + "0" * 36,
                name="Synced.Movie",
                state="Downloading",
                progress=75.0,
                total_size=1000000,
                downloaded=750000,
                uploaded=100000,
                download_speed=10000,
                upload_speed=5000,
                save_path="/downloads",
                num_seeds=10,
                num_peers=5,
                ratio=0.1,
                eta=600,
                is_finished=False,
                paused=False,
            )
        ]
        
        synced, errors = sync_torrent_status(db_session)
        
        assert synced == 1
        assert errors == 0
        
        db_session.refresh(item)
        assert item.progress == 75.0
        assert item.status == TorrentStatus.DOWNLOADING

    @patch("app.modules.deluge.service.get_all_torrents_info")
    def test_sync_marks_completed(self, mock_get_all, db_session):
        """Test sync marks finished torrents as completed."""
        item = TorrentItem(
            rating_key="complete_test",
            torrent_hash="comp" + "0" * 36,
            status=TorrentStatus.DOWNLOADING,
            progress=99.0,
        )
        db_session.add(item)
        db_session.commit()
        
        mock_get_all.return_value = [
            TorrentInfoResponse(
                torrent_hash="comp" + "0" * 36,
                name="Complete.Movie",
                state="Seeding",
                progress=100.0,
                total_size=1000000,
                downloaded=1000000,
                uploaded=500000,
                download_speed=0,
                upload_speed=10000,
                save_path="/downloads",
                num_seeds=20,
                num_peers=10,
                ratio=0.5,
                eta=-1,
                is_finished=True,
                paused=False,
            )
        ]
        
        synced, errors = sync_torrent_status(db_session)
        
        db_session.refresh(item)
        assert item.status == TorrentStatus.COMPLETED
        assert item.completed_at is not None

    @patch("app.modules.deluge.service.get_all_torrents_info")
    def test_sync_marks_removed_if_not_in_daemon(self, mock_get_all, db_session):
        """Test sync marks torrents as removed if not in daemon."""
        item = TorrentItem(
            rating_key="gone_test",
            torrent_hash="gone" + "0" * 36,
            status=TorrentStatus.DOWNLOADING,
        )
        db_session.add(item)
        db_session.commit()
        
        mock_get_all.return_value = []  # Torrent not in daemon
        
        synced, errors = sync_torrent_status(db_session)
        
        db_session.refresh(item)
        assert item.status == TorrentStatus.REMOVED


class TestMapDelugeState:
    """Tests for mapping Deluge states."""

    def test_map_queued(self):
        """Test mapping Queued state."""
        assert _map_deluge_state("Queued") == TorrentStatus.QUEUED

    def test_map_downloading(self):
        """Test mapping Downloading state."""
        assert _map_deluge_state("Downloading") == TorrentStatus.DOWNLOADING

    def test_map_seeding(self):
        """Test mapping Seeding state."""
        assert _map_deluge_state("Seeding") == TorrentStatus.SEEDING

    def test_map_paused(self):
        """Test mapping Paused state."""
        assert _map_deluge_state("Paused") == TorrentStatus.PAUSED

    def test_map_checking(self):
        """Test mapping Checking state."""
        assert _map_deluge_state("Checking") == TorrentStatus.CHECKING

    def test_map_error(self):
        """Test mapping Error state."""
        assert _map_deluge_state("Error") == TorrentStatus.ERROR

    def test_map_unknown(self):
        """Test mapping unknown state defaults to QUEUED."""
        assert _map_deluge_state("Unknown") == TorrentStatus.QUEUED


class TestQueryFunctions:
    """Tests for query helper functions."""

    def test_get_torrents_by_rating_key(self, db_session):
        """Test getting torrents by rating_key."""
        items = [
            TorrentItem(rating_key="query_key", torrent_hash="q1" + "0" * 38),
            TorrentItem(rating_key="query_key", torrent_hash="q2" + "0" * 38),
            TorrentItem(rating_key="other_key", torrent_hash="q3" + "0" * 38),
        ]
        db_session.add_all(items)
        db_session.commit()
        
        result = get_torrents_by_rating_key("query_key", db_session)
        
        assert len(result) == 2

    def test_get_torrent_by_hash(self, db_session):
        """Test getting torrent by hash."""
        item = TorrentItem(rating_key="hash_test", torrent_hash="h" * 40)
        db_session.add(item)
        db_session.commit()
        
        result = get_torrent_by_hash("h" * 40, db_session)
        
        assert result is not None
        assert result.rating_key == "hash_test"

    def test_get_torrent_by_hash_not_found(self, db_session):
        """Test getting non-existent torrent by hash."""
        result = get_torrent_by_hash("nonexistent" + "0" * 30, db_session)
        
        assert result is None

    def test_get_all_tracked_torrents(self, db_session):
        """Test getting all tracked torrents."""
        items = [
            TorrentItem(rating_key="all1", torrent_hash="a1" + "0" * 38, status=TorrentStatus.DOWNLOADING),
            TorrentItem(rating_key="all2", torrent_hash="a2" + "0" * 38, status=TorrentStatus.SEEDING),
            TorrentItem(rating_key="all3", torrent_hash="a3" + "0" * 38, status=TorrentStatus.COMPLETED),
        ]
        db_session.add_all(items)
        db_session.commit()
        
        result, total = get_all_tracked_torrents(db_session)
        
        assert total == 3
        assert len(result) == 3

    def test_get_all_tracked_torrents_with_status_filter(self, db_session):
        """Test filtering torrents by status."""
        items = [
            TorrentItem(rating_key="f1", torrent_hash="f1" + "0" * 38, status=TorrentStatus.DOWNLOADING),
            TorrentItem(rating_key="f2", torrent_hash="f2" + "0" * 38, status=TorrentStatus.DOWNLOADING),
            TorrentItem(rating_key="f3", torrent_hash="f3" + "0" * 38, status=TorrentStatus.SEEDING),
        ]
        db_session.add_all(items)
        db_session.commit()
        
        result, total = get_all_tracked_torrents(db_session, status=TorrentStatus.DOWNLOADING)
        
        assert total == 2
        assert all(t.status == TorrentStatus.DOWNLOADING for t in result)

    def test_get_all_tracked_torrents_pagination(self, db_session):
        """Test pagination."""
        for i in range(10):
            item = TorrentItem(rating_key=f"page{i}", torrent_hash=f"p{i}" + "0" * 38)
            db_session.add(item)
        db_session.commit()
        
        result, total = get_all_tracked_torrents(db_session, limit=5, offset=0)
        
        assert total == 10
        assert len(result) == 5
        
        result2, total2 = get_all_tracked_torrents(db_session, limit=5, offset=5)
        
        assert total2 == 10
        assert len(result2) == 5

