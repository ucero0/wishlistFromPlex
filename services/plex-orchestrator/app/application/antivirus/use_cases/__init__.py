"""Antivirus use cases: scan record CRUD only. Torrent scan/ingest lives in application/pipelines/ingest/."""
from app.application.antivirus.use_cases.create_antivirus_scan import (
    CreateAntivirusScanUseCase,
)
from app.application.antivirus.use_cases.update_antivirus_scan import (
    UpdateAntivirusScanUseCase,
)
from app.application.antivirus.use_cases.delete_antivirus_scan import (
    DeleteAntivirusScanUseCase,
    DeleteAntivirusScanByIdUseCase,
    DeleteAntivirusScansByGuidProwlarrUseCase,
)

__all__ = [
    "CreateAntivirusScanUseCase",
    "UpdateAntivirusScanUseCase",
    "DeleteAntivirusScanUseCase",
    "DeleteAntivirusScanByIdUseCase",
    "DeleteAntivirusScansByGuidProwlarrUseCase",
]
