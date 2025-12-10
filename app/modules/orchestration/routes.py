"""Orchestration module API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_api_key
from app.modules.orchestration.service import OrchestrationService
from app.modules.orchestration.schemas import (
    OrchestrationRunResponse,
    OrchestrationStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


@router.post("/run", response_model=OrchestrationRunResponse, dependencies=[Depends(get_api_key)])
async def run_orchestration(
    auto_search: bool = True,
    force_research: bool = False,
    db: Session = Depends(get_db)
):
    """
    Run the full orchestration workflow:
    1. Sync Plex watchlists
    2. Find items that need torrent searches
    3. Search for torrents and add to Deluge
    
    Args:
        auto_search: If True, automatically search for torrents
        force_research: If True, re-search items that already have results
    
    Returns:
        Orchestration run summary
    """
    try:
        service = OrchestrationService(db)
        result = await service.run_full_workflow(
            auto_search=auto_search,
            force_research=force_research
        )
        return OrchestrationRunResponse(**result)
    except Exception as e:
        logger.error(f"Error running orchestration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration failed: {str(e)}"
        )
