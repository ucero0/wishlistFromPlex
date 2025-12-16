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
    clamav_host: str = "clamav"
    clamav_port: int = 3310
    yara_rules_path: str = "/app/yara-rules"
    
    # Prowlarr Configuration
    prowlarr_host: str = "gluetun"  # Prowlarr runs through gluetun VPN
    prowlarr_port: int = 9696
    prowlarr_api_key: Optional[str] = None
    
    # Media paths
    downloads_path: str = "/downloads"
    media_movies_path: str = "/media/movies"
    media_tvshows_path: str = "/media/tvshows"
    media_quarantine_path: str = "/media/quarantine"

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars like POSTGRES_USER, POSTGRES_PASSWORD, etc.
    )


settings = Settings()



