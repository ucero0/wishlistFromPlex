from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str

    # API Security
    api_key: str

    # Sync Configuration
    plex_sync_interval_hours: int = 6
    plex_library_paths_sync_interval_hours: int = 6
    plex_server_url: str = "http://localhost:32400"
    # Owner/admin X-Plex-Token for local Plex Media Server API (library paths, scans, in-library checks)
    plex_server_admin_token: Optional[str] = None
    # Deluge Configuration
    deluge_host: str = "deluge"
    deluge_port: int = 58846  # Deluge daemon port (for RPC)
    deluge_username: str = "deluge"
    deluge_password: str = "deluge"  # Read from auth file or set via env

    # Scanner Configuration
    antivirus_host: str = "antivirus"
    antivirus_port: int = 3311  # HTTP scan service port (antivirus daemon is on 3310)
    
    # Prowlarr Configuration
    prowlarr_host: str = "prowlarr"
    prowlarr_port: int = 9696
    prowlarr_api_key: Optional[str] = None
    
    # TMDB Configuration
    tmdb_api_key: Optional[str] = None  # Set via TMDB_API_KEY environment variable
    tmdb_access_token: Optional[str] = None  # TMDB v4 read access token (watchlist)
    tmdb_user_name: str = "default"
    tmdb_account_id: Optional[int] = None
    
    # Deluge quarantine (shared with antivirus container for scans/moves)
    container_deluge_quarantine_path: str = "/downloads/quarantine"
    # Reserve this much free space on the download volume before adding torrents
    download_min_free_buffer_gb: float = 10.0
    # When Prowlarr size is unknown, assume a large release needs this much space
    download_default_required_gb: float = 50.0
    deferred_download_process_interval_minutes: int = 15
    ingest_poll_interval_minutes: int = 5
    torrent_unhealthy_min_availability: float = 1.0
    torrent_unhealthy_min_availability_active_days: int = 1
    torrent_unhealthy_no_transfer_days: int = 5
    # Keep this many unwatched episodes downloaded ahead of any user's progress
    tv_watchlist_ahead_episodes: int = 10
    # Use DB free_bytes for ingest when disk_stats_synced_at is newer than this (hours)
    plex_library_disk_stats_max_age_hours: int = 6
    # Docker: host paths are visible under this prefix (e.g. /host/mnt/media -> Plex path /mnt/media)
    container_host_fs_prefix: str = ""

    # Logging
    log_level: str = "INFO"

    @field_validator("tmdb_account_id", mode="before")
    @classmethod
    def _empty_optional_int(cls, value):
        if value == "" or value is None:
            return None
        return value

    @field_validator("tmdb_access_token", mode="before")
    @classmethod
    def _empty_optional_str(cls, value):
        if value == "":
            return None
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars like POSTGRES_USER, POSTGRES_PASSWORD, etc.
    )


settings = Settings()



