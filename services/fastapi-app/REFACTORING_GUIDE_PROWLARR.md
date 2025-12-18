# Prowlarr Service Refactoring Guide

Based on the Hexagonal Architecture principles, here's where each function from `prowlarr_service.py` should be moved:

## Current Location
`infrastructure/externalApis/prowlarr/prowlarr_service.py`

## Target Architecture

### 1. **Domain Layer** (`domain/`)
**Pure business logic - NO IO, NO dependencies on infrastructure**

#### `domain/services/torrent_quality_service.py` (NEW)
- `_parse_quality_from_title()` → `parse_quality_from_title()` (public)
- `_calculate_quality_score()` → `calculate_quality_score()` (public)
- Quality scoring constants:
  - `RESOLUTION_SCORES`
  - `AUDIO_SCORES`
  - `HDR_SCORES`
  - `VIDEO_CODEC_SCORES`
  - `SOURCE_SCORES`
  - `MIN_SEEDERS`

**Why**: These are pure business rules for quality assessment. No external dependencies.

---

### 2. **Domain Ports** (`domain/ports/external/prowlarr/`)
**Contracts/Protocols - Define WHAT, not HOW**

#### `domain/ports/external/prowlarr/torrent_search_provider.py` (NEW)
```python
from typing import Protocol, List, Optional
from app.domain.models.torrent_search import TorrentResult

class TorrentSearchProvider(Protocol):
    """Protocol for torrent search operations."""
    
    async def search_torrents(
        self, 
        query: str, 
        media_type: str = "movie"
    ) -> List[TorrentResult]:
        """Search for torrents and return domain models."""
        ...
    
    async def send_to_download_client(
        self, 
        guid: str, 
        indexer_id: int
    ) -> bool:
        """Send torrent to download client."""
        ...
    
    async def test_connection(self) -> tuple[bool, Optional[str], Optional[str]]:
        """Test connection to search provider."""
        ...
    
    async def get_indexer_count(self) -> int:
        """Get number of configured indexers."""
        ...
```

**Why**: Defines the contract that adapters must implement. Domain doesn't know about Prowlarr.

---

### 3. **Infrastructure Layer** (`infrastructure/externalApis/prowlarr/`)
**Raw API clients - Technical implementation details**

#### `infrastructure/externalApis/prowlarr/prowlarr_client.py` (KEEP AS IS)
- `test_connection()` ✅ Already here
- `get_indexer_count()` ✅ Already here
- `search()` ✅ Already here
- `send_to_download_client()` ✅ Already here

**Why**: This is the raw HTTP client. It should stay in infrastructure.

---

### 4. **Adapters Layer** (`adapters/external/prowlarr/`)
**Boundary translators - Convert between infrastructure and domain**

#### `adapters/external/prowlarr/adapter.py` (NEW)
```python
from app.domain.ports.external.prowlarr.torrent_search_provider import TorrentSearchProvider
from app.infrastructure.externalApis.prowlarr.prowlarr_client import ProwlarrClient
from app.infrastructure.externalApis.prowlarr.schemas import ProwlarrRawResult
from app.domain.models.torrent_search import TorrentResult, QualityInfo
from app.domain.services.torrent_quality_service import TorrentQualityService

class ProwlarrAdapter(TorrentSearchProvider):
    """Adapter that converts Prowlarr infrastructure to domain models."""
    
    def __init__(self, client: ProwlarrClient, quality_service: TorrentQualityService):
        self.client = client
        self.quality_service = quality_service
    
    async def search_torrents(self, query: str, media_type: str = "movie") -> List[TorrentResult]:
        """Search and return domain TorrentResult objects."""
        categories = "2000" if media_type == "movie" else "5000"
        raw_results = await self.client.search(query, categories)
        
        results = []
        for result_data in raw_results:
            try:
                raw_result = ProwlarrRawResult(**result_data)
                # Convert to domain model
                results.append(TorrentResult(
                    **raw_result.model_dump(),
                    quality_score=0,
                    quality_info=QualityInfo()
                ))
            except Exception as e:
                logger.warning(f"Failed to parse Prowlarr result: {e}")
                continue
        
        return results
    
    async def send_to_download_client(self, guid: str, indexer_id: int) -> bool:
        return await self.client.send_to_download_client(guid, indexer_id)
    
    async def test_connection(self) -> tuple[bool, Optional[str], Optional[str]]:
        return await self.client.test_connection()
    
    async def get_indexer_count(self) -> int:
        return await self.client.get_indexer_count()
```

#### `adapters/external/prowlarr/mapper.py` (NEW - if needed)
- Conversion functions between infrastructure DTOs and domain models

**Why**: Adapters translate between external systems (Prowlarr) and domain models. They implement domain ports.

---

### 5. **Application Layer** (`application/prowlarr/`)
**Orchestration - Use cases and queries**

#### `application/prowlarr/useCases/searchTorrentsByQuery.py` (NEW)
```python
from app.domain.ports.external.prowlarr.torrent_search_provider import TorrentSearchProvider
from app.domain.services.torrent_quality_service import TorrentQualityService
from app.domain.models.torrent_search import TorrentResult
from typing import Optional, List

class SearchTorrentsByQueryUseCase:
    """Use case for searching torrents by query."""
    
    def __init__(
        self, 
        search_provider: TorrentSearchProvider,
        quality_service: TorrentQualityService
    ):
        self.search_provider = search_provider
        self.quality_service = quality_service
    
    async def execute(
        self,
        query: str,
        media_type: str = "movie",
        auto_add_to_deluge: bool = True,
    ) -> Optional[List[TorrentResult]]:
        """Search for torrents, process, and optionally send to download client."""
        # 1. Search via adapter
        results = await self.search_provider.search_torrents(query, media_type)
        if not results:
            return None
        
        # 2. Process and score (orchestration)
        processed_results = self._process_search_results(results)
        if not processed_results:
            return []
        
        # 3. Get best result
        best_result = processed_results[0]
        
        # 4. Optionally send to download client
        if auto_add_to_deluge:
            await self.search_provider.send_to_download_client(
                best_result.guid, 
                best_result.indexerId
            )
        
        return [best_result]
    
    def _process_search_results(self, results: List[TorrentResult]) -> List[TorrentResult]:
        """Process and score TorrentResult objects."""
        processed_results = []
        
        for result in results:
            if result.seeders and result.seeders < MIN_SEEDERS:
                continue
            
            # Use domain service for quality parsing/scoring
            quality_info = self.quality_service.parse_quality_from_title(result.title)
            quality_score = self.quality_service.calculate_quality_score(
                result.title, 
                quality_info, 
                result.seeders or 0
            )
            
            result.quality_info = quality_info
            result.quality_score = quality_score
            processed_results.append(result)
        
        # Sort by quality score
        processed_results.sort(key=lambda x: x.quality_score, reverse=True)
        return processed_results
```

#### `application/prowlarr/queries/testProwlarrConnection.py` (NEW - if needed)
- Query for testing connection
- Query for getting indexer count

**Why**: Use cases orchestrate the flow. They depend on ports (interfaces), not concrete implementations.

---

## Summary

| Current Function | Target Location | New Name/Structure |
|-----------------|----------------|-------------------|
| `_parse_quality_from_title()` | `domain/services/torrent_quality_service.py` | `parse_quality_from_title()` |
| `_calculate_quality_score()` | `domain/services/torrent_quality_service.py` | `calculate_quality_score()` |
| Quality constants | `domain/services/torrent_quality_service.py` | Keep as constants |
| `search_prowlarr()` | `adapters/external/prowlarr/adapter.py` | `search_torrents()` (implements port) |
| `_process_search_results()` | `application/prowlarr/useCases/searchTorrentsByQuery.py` | `_process_search_results()` (private method) |
| `search_by_query()` | `application/prowlarr/useCases/searchTorrentsByQuery.py` | `execute()` (use case method) |
| `test_connection()` | `adapters/external/prowlarr/adapter.py` | `test_connection()` (implements port) |
| `get_indexer_count()` | `adapters/external/prowlarr/adapter.py` | `get_indexer_count()` (implements port) |

## Key Principles Applied

1. **Domain Layer**: Pure business logic, no dependencies on infrastructure
2. **Ports**: Define contracts (Protocols) that adapters implement
3. **Adapters**: Translate between infrastructure and domain
4. **Application Layer**: Orchestrates use cases using ports
5. **Infrastructure**: Raw technical implementations (HTTP clients, etc.)

## Benefits

- ✅ Domain logic is testable without external dependencies
- ✅ Easy to swap Prowlarr for another provider (just implement the port)
- ✅ Clear separation of concerns
- ✅ Follows dependency inversion principle
- ✅ Business rules are isolated and reusable

