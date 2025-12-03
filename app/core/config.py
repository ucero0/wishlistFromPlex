from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str

    # API Security
    api_key: str

    # Sync Configuration
    plex_sync_interval_hours: int = 6

    # Deluge Configuration
    deluge_host: str = "gluetun"  # Container name when using docker-compose
    deluge_port: int = 58846  # Deluge daemon port
    deluge_username: str = "localclient"
    deluge_password: str = ""  # Read from auth file or set via env

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars like POSTGRES_USER, POSTGRES_PASSWORD, etc.


settings = Settings()



