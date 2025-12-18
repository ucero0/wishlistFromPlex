"""Mapper for converting between Prowlarr external schemas and domain models."""
from typing import List
from app.infrastructure.externalApis.prowlarr.schemas import ProwlarrRawResult
from app.domain.models.torrent_search import TorrentSearchResult, QualityInfo


def to_domain(raw_result: ProwlarrRawResult) -> TorrentSearchResult:
    """
    Map ProwlarrRawResult (infrastructure DTO) to TorrentSearchResult (domain model).
    
    Args:
        raw_result: ProwlarrRawResult from infrastructure layer
        
    Returns:
        TorrentSearchResult domain model with default quality_score and quality_info
    """
    return TorrentSearchResult(
        title=raw_result.title,
        indexer=raw_result.indexer,
        size=raw_result.size,
        seeders=raw_result.seeders,
        leechers=raw_result.leechers,
        magnetUrl=raw_result.magnetUrl,
        downloadUrl=raw_result.downloadUrl,
        infoUrl=raw_result.infoUrl,
        publishDate=raw_result.publishDate,
        guid=raw_result.guid,
        indexerId=raw_result.indexerId,
        protocol=raw_result.protocol,
        quality_score=0,  # Will be calculated later by quality service
        quality_info=QualityInfo(),  # Will be parsed later by quality service
    )


def to_domain_list(raw_results: List[ProwlarrRawResult]) -> List[TorrentSearchResult]:
    """
    Map a list of ProwlarrRawResult to a list of TorrentSearchResult.
    
    Args:
        raw_results: List of ProwlarrRawResult from infrastructure layer
        
    Returns:
        List of TorrentSearchResult domain models
    """
    return [to_domain(raw_result) for raw_result in raw_results]

