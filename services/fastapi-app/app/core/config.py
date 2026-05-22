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
    # Gluetun VPN (Deluge/Prowlarr run through this container)
    gluetun_host: str = "gluetun"
    gluetun_health_port: int = 9999

    # Deluge Configuration
    deluge_host: str = "gluetun"  # Container name when using docker-compose
    deluge_port: int = 58846  # Deluge daemon port (for RPC)
    deluge_username: str = "deluge"
    deluge_password: str = "deluge"  # Read from auth file or set via env

    # Scanner Configuration
    antivirus_host: str = "antivirus"
    antivirus_port: int = 3311  # HTTP scan service port (antivirus daemon is on 3310)
    
    # Prowlarr Configuration
    prowlarr_host: str = "gluetun"  # Prowlarr runs through gluetun VPN
    prowlarr_port: int = 9696
    prowlarr_api_key: Optional[str] = None
    
    # TMDB Configuration
    tmdb_api_key: Optional[str] = None  # Set via TMDB_API_KEY environment variable
    
    # Deluge quarantine (shared with antivirus container for scans/moves)
    container_deluge_quarantine_path: str = "/downloads/quarantine"
    # Reserve this much free space on the download volume before adding torrents
    download_min_free_buffer_gb: float = 10.0
    # When Prowlarr size is unknown, assume a large release needs this much space
    download_default_required_gb: float = 50.0
    deferred_download_process_interval_minutes: int = 15
    # Use DB free_bytes for ingest when disk_stats_synced_at is newer than this (hours)
    plex_library_disk_stats_max_age_hours: int = 6

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars like POSTGRES_USER, POSTGRES_PASSWORD, etc.
    )


settings = Settings()



