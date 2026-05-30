"""Antivirus query classes."""
from app.application.antivirus.queries.check_infected_by_guid_prowlarr_query import (
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

