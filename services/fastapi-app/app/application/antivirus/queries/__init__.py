"""Antivirus query classes."""
from app.application.antivirus.queries.checkInfectedByGuidProwlarr import (
    CheckInfectedByGuidProwlarrQuery,
    GetAntivirusScanByIdQuery,
    GetAntivirusScansByGuidProwlarrQuery,
    GetAntivirusScanByFilePathQuery,
    GetInfectedItemsQuery,
    GetCleanItemsQuery,
    GetAllAntivirusScansQuery,
)

__all__ = [
    "CheckInfectedByGuidProwlarrQuery",
    "GetAntivirusScanByIdQuery",
    "GetAntivirusScansByGuidProwlarrQuery",
    "GetAntivirusScanByFilePathQuery",
    "GetInfectedItemsQuery",
    "GetCleanItemsQuery",
    "GetAllAntivirusScansQuery",
]

