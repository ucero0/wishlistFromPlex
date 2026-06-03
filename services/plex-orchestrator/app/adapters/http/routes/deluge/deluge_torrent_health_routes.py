"""Deluge torrent unhealthy-removal policy (database-backed, hot-reloadable)."""
from fastapi import APIRouter, Depends

from app.adapters.http.security.dependencies import APIKey
from app.adapters.http.schemas.settings.torrent_health_config_schemas import (
    TorrentHealthConfigResponse,
    UpdateTorrentHealthConfigRequest,
)
from app.application.settings.services.torrent_health_config_service import (
    torrent_health_config_service,
)
from app.domain.models.torrent_health_config import TorrentHealthConfigUpdate

deluge_torrent_health_routes = APIRouter()


@deluge_torrent_health_routes.get(
    "/torrent-health",
    response_model=TorrentHealthConfigResponse,
    summary="Get unhealthy torrent removal policy",
)
async def get_deluge_torrent_health_policy(_api_key: APIKey):
    """
    Active policy from PostgreSQL (grace timers, availability threshold, VPN skip, strict mode).

    Applies on the next Deluge maintenance poll — no app restart.
    """
    config = await torrent_health_config_service.get_config()
    return TorrentHealthConfigResponse.from_domain(config)


@deluge_torrent_health_routes.put(
    "/torrent-health",
    response_model=TorrentHealthConfigResponse,
    summary="Update unhealthy torrent removal policy",
)
async def update_deluge_torrent_health_policy(
    request: UpdateTorrentHealthConfigRequest,
    _api_key: APIKey,
):
    """Patch any subset of fields; omitted fields stay unchanged."""
    config = await torrent_health_config_service.update_config(
        TorrentHealthConfigUpdate.model_validate(
            request.model_dump(exclude_unset=True)
        )
    )
    return TorrentHealthConfigResponse.from_domain(config)
