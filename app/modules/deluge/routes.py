"""Deluge module API routes."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.security import get_api_key
from app.modules.deluge.schemas import TorrentStatus
from app.modules.deluge.service import DelugeService
from app.modules.deluge.constants import MODULE_PREFIX
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=MODULE_PREFIX, tags=[MODULE_PREFIX.strip("/")])

@router.on_event("startup")
async def startup_event():
    """Startup event for the Deluge module."""
    global delugeClient
    delugeClient = DelugeService()
    try:
        delugeClient.connect()
    except Exception as e:
        logger.error(f"Error connecting to Deluge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error connecting to Deluge: {e}")
    logger.info("Deluge module initialized")

def get_deluge_client() -> DelugeService:
    return delugeClient


@router.get("/status", response_model=List[TorrentStatus], dependencies=[Depends(get_api_key)])
async def get_deluge_status(client: DelugeService = Depends(get_deluge_client)):
    """Get the status of the Deluge daemon."""
    try:
        return client.get_torrentsStatus()
    except Exception as e:
        logger.error(f"Error getting the status of the Deluge daemon: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting the status of the Deluge daemon: {e}",
        )


