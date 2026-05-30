"""FastAPI DI for Deluge reconciliation pipeline step."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
from app.composition.active_downloads import (
    build_reconcile_active_downloads_with_deluge_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_reconcile_active_downloads_with_deluge_use_case(
    session: AsyncSession = Depends(get_db),
) -> ReconcileActiveDownloadsWithDelugeUseCase:
    return build_reconcile_active_downloads_with_deluge_use_case(session)
