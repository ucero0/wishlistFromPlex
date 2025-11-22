from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.db import get_db
from app.core.security import get_api_key
from app.services.sync_service import sync_all_users
from app.api.schemas import SyncResponse

router = APIRouter(prefix="/api/sync", tags=["sync"])

# Store last sync status in memory (could be moved to DB later)
_last_sync_status = None


@router.post("", response_model=SyncResponse)
async def trigger_sync(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Trigger a manual sync of all active Plex users' watchlists."""
    global _last_sync_status
    
    try:
        result = await sync_all_users(db)
        _last_sync_status = result
        return SyncResponse(**result)
    except Exception as e:
        error_result = {
            "users_processed": 0,
            "items_fetched": 0,
            "new_items": 0,
            "updated_items": 0,
            "total_items": 0,
            "errors": [str(e)],
            "sync_time": datetime.now(timezone.utc).isoformat(),
        }
        _last_sync_status = error_result
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


@router.get("/status", response_model=SyncResponse)
async def get_sync_status():
    """Get the status of the last sync operation."""
    global _last_sync_status
    
    if _last_sync_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sync has been performed yet",
        )
    
    return SyncResponse(**_last_sync_status)

