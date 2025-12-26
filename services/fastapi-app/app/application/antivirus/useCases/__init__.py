"""Antivirus use cases."""
from app.application.antivirus.useCases.createAntivirusScan import CreateAntivirusScanUseCase
from app.application.antivirus.useCases.updateAntivirusScan import UpdateAntivirusScanUseCase
from app.application.antivirus.useCases.deleteAntivirusScan import (
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

