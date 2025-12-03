"""Tests for Deluge Pydantic schemas."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.modules.deluge.schemas import (
    TorrentStatusEnum,
    AddTorrentRequest,
    RemoveTorrentRequest,
    TorrentItemResponse,
    TorrentInfoResponse,
    AddTorrentResponse,
    RemoveTorrentResponse,
    TorrentListResponse,
    DelugeStatusResponse,
)


class TestTorrentStatusEnum:
    """Tests for TorrentStatusEnum."""

    def test_status_values(self):
        """Test all status values."""
        assert TorrentStatusEnum.QUEUED == "queued"
        assert TorrentStatusEnum.DOWNLOADING == "downloading"
        assert TorrentStatusEnum.SEEDING == "seeding"
        assert TorrentStatusEnum.PAUSED == "paused"
        assert TorrentStatusEnum.CHECKING == "checking"
        assert TorrentStatusEnum.ERROR == "error"
        assert TorrentStatusEnum.COMPLETED == "completed"
        assert TorrentStatusEnum.REMOVED == "removed"


class TestAddTorrentRequest:
    """Tests for AddTorrentRequest schema."""

    def test_valid_request(self):
        """Test creating a valid add torrent request."""
        request = AddTorrentRequest(
            rating_key="5d776d1847dd6e001f6f002f",
            magnet_link="magnet:?xt=urn:btih:abc123&dn=test",
        )
        
        assert request.rating_key == "5d776d1847dd6e001f6f002f"
        assert request.magnet_link.startswith("magnet:")

    def test_missing_rating_key(self):
        """Test request without rating_key."""
        with pytest.raises(ValidationError) as exc_info:
            AddTorrentRequest(magnet_link="magnet:?xt=urn:btih:abc123")
        
        assert "rating_key" in str(exc_info.value)

    def test_missing_magnet_link(self):
        """Test request without magnet_link."""
        with pytest.raises(ValidationError) as exc_info:
            AddTorrentRequest(rating_key="abc123")
        
        assert "magnet_link" in str(exc_info.value)


class TestRemoveTorrentRequest:
    """Tests for RemoveTorrentRequest schema."""

    def test_default_remove_data_false(self):
        """Test default remove_data is False."""
        request = RemoveTorrentRequest()
        assert request.remove_data is False

    def test_remove_data_true(self):
        """Test setting remove_data to True."""
        request = RemoveTorrentRequest(remove_data=True)
        assert request.remove_data is True


class TestTorrentItemResponse:
    """Tests for TorrentItemResponse schema."""

    def test_full_response(self):
        """Test creating a full torrent item response."""
        now = datetime.now(timezone.utc)
        response = TorrentItemResponse(
            id=1,
            rating_key="movie123",
            torrent_hash="a" * 40,
            magnet_link="magnet:?xt=urn:btih:" + "a" * 40,
            name="Test.Movie.2024.1080p",
            status=TorrentStatusEnum.DOWNLOADING,
            progress=45.5,
            total_size=2147483648,
            downloaded=976744448,
            uploaded=104857600,
            download_speed=5242880,
            upload_speed=1048576,
            save_path="/downloads",
            num_seeds=15,
            num_peers=3,
            ratio=0.1,
            eta=3600,
            added_at=now,
            completed_at=None,
            last_updated=now,
        )
        
        assert response.id == 1
        assert response.status == TorrentStatusEnum.DOWNLOADING
        assert response.progress == 45.5

    def test_minimal_response(self):
        """Test creating a minimal torrent item response."""
        now = datetime.now(timezone.utc)
        response = TorrentItemResponse(
            id=1,
            rating_key="key",
            torrent_hash="b" * 40,
            status=TorrentStatusEnum.QUEUED,
            progress=0.0,
            added_at=now,
            last_updated=now,
        )
        
        assert response.id == 1
        assert response.name is None
        assert response.magnet_link is None


class TestTorrentInfoResponse:
    """Tests for TorrentInfoResponse schema."""

    def test_daemon_info_response(self):
        """Test creating torrent info from daemon."""
        response = TorrentInfoResponse(
            torrent_hash="c" * 40,
            name="Test.Movie",
            state="Downloading",
            progress=50.0,
            total_size=1073741824,
            downloaded=536870912,
            uploaded=107374182,
            download_speed=10485760,
            upload_speed=2097152,
            save_path="/downloads",
            num_seeds=20,
            num_peers=5,
            ratio=0.2,
            eta=1800,
            is_finished=False,
            paused=False,
        )
        
        assert response.state == "Downloading"
        assert response.is_finished is False
        assert response.paused is False


class TestAddTorrentResponse:
    """Tests for AddTorrentResponse schema."""

    def test_success_response(self):
        """Test successful add response."""
        response = AddTorrentResponse(
            success=True,
            message="Torrent added successfully",
            torrent_hash="d" * 40,
        )
        
        assert response.success is True
        assert "successfully" in response.message

    def test_failure_response(self):
        """Test failed add response."""
        response = AddTorrentResponse(
            success=False,
            message="Failed to add torrent: connection error",
        )
        
        assert response.success is False
        assert response.torrent_hash is None


class TestRemoveTorrentResponse:
    """Tests for RemoveTorrentResponse schema."""

    def test_remove_torrent_only(self):
        """Test removing torrent only."""
        response = RemoveTorrentResponse(
            success=True,
            message="Torrent removed",
            torrent_hash="e" * 40,
            data_removed=False,
        )
        
        assert response.data_removed is False

    def test_remove_torrent_and_data(self):
        """Test removing torrent and data."""
        response = RemoveTorrentResponse(
            success=True,
            message="Torrent and data removed",
            torrent_hash="f" * 40,
            data_removed=True,
        )
        
        assert response.data_removed is True


class TestTorrentListResponse:
    """Tests for TorrentListResponse schema."""

    def test_empty_list(self):
        """Test empty torrent list."""
        response = TorrentListResponse(total=0, torrents=[])
        
        assert response.total == 0
        assert response.torrents == []

    def test_with_torrents(self):
        """Test list with torrents."""
        now = datetime.now(timezone.utc)
        torrents = [
            TorrentItemResponse(
                id=1,
                rating_key="key1",
                torrent_hash="1" * 40,
                status=TorrentStatusEnum.DOWNLOADING,
                progress=50.0,
                added_at=now,
                last_updated=now,
            ),
            TorrentItemResponse(
                id=2,
                rating_key="key2",
                torrent_hash="2" * 40,
                status=TorrentStatusEnum.SEEDING,
                progress=100.0,
                added_at=now,
                last_updated=now,
            ),
        ]
        
        response = TorrentListResponse(total=2, torrents=torrents)
        
        assert response.total == 2
        assert len(response.torrents) == 2


class TestDelugeStatusResponse:
    """Tests for DelugeStatusResponse schema."""

    def test_connected_status(self):
        """Test connected daemon status."""
        response = DelugeStatusResponse(
            connected=True,
            daemon_version="2.1.1",
        )
        
        assert response.connected is True
        assert response.daemon_version == "2.1.1"
        assert response.error is None

    def test_disconnected_status(self):
        """Test disconnected daemon status."""
        response = DelugeStatusResponse(
            connected=False,
            error="Connection refused",
        )
        
        assert response.connected is False
        assert response.daemon_version is None
        assert "Connection" in response.error

