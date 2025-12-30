from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str

    # API Security
    api_key: str

    # Sync Configuration
    plex_sync_interval_hours: int = 6
    plex_server_url: str = "http://localhost:32400"
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
    
    # Media paths
    container_plex_media_path: str = "/plex/media"
    container_deluge_quarantine_path: str = "/downloads/quarantine"  # Shared quarantine path between FastAPI and Antivirus containers
    
    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars like POSTGRES_USER, POSTGRES_PASSWORD, etc.
    )


settings = Settings()



