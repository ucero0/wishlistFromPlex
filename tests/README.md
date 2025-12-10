# Test Suite Summary

This document provides a comprehensive overview of all tests in the project.

## Test Organization

```
tests/
├── common/              # Shared test utilities
│   └── test_security.py
├── deluge/              # Deluge module tests
│   ├── test_models.py
│   ├── test_routes.py
│   ├── test_schemas.py
│   ├── test_service.py
│   └── test_deluge_live.py  # Live integration tests
├── integration/         # End-to-end integration tests
│   ├── test_pipeline.py
│   └── test_prowlarr_deluge_integration.py
├── plex/               # Plex module tests
│   ├── test_models.py
│   ├── test_routes.py
│   ├── test_service.py
│   ├── manual_test_plex_connection.py
│   └── manual_test_watchlist_modify.py
├── scanner/            # Scanner module tests
│   ├── test_models.py
│   ├── test_routes.py
│   ├── test_schemas.py
│   └── test_service.py
├── torrent_search/     # Torrent search module tests
│   ├── test_models.py
│   ├── test_routes.py
│   ├── test_schemas.py
│   ├── test_service.py
│   └── test_live.py     # Live Prowlarr connection tests
└── conftest.py         # Pytest configuration and fixtures
```

## Test Types

### 1. Unit Tests (Mocked)
These tests use mocks and don't require external services:
- **Location**: `tests/{module}/test_*.py` (except `*_live.py`)
- **Run**: `pytest tests/{module}/`
- **Purpose**: Fast, isolated tests of individual components

### 2. Live Integration Tests
These tests connect to real services and require them to be running:
- **Location**: `tests/{module}/test_*_live.py`
- **Run**: `pytest tests/{module}/test_*_live.py` (or set `SKIP_LIVE_TESTS=0`)
- **Purpose**: Verify actual service connectivity and functionality

### 3. End-to-End Integration Tests
These tests verify the full pipeline:
- **Location**: `tests/integration/`
- **Run**: `pytest tests/integration/` or run scripts directly
- **Purpose**: Test complete workflows across multiple services

## Module Test Details

### Deluge Module (`tests/deluge/`)

#### Unit Tests
- **test_models.py**: Database models (TorrentItem, TorrentStatus)
- **test_routes.py**: API endpoints (status, add, remove, list torrents)
- **test_schemas.py**: Pydantic schemas validation
- **test_service.py**: Service layer logic (mocked Deluge client)

#### Live Tests
- **test_deluge_live.py**: Real Deluge daemon connection tests
  - Tests: Connection, daemon info, torrent retrieval
  - Requires: Deluge running, DELUGE_HOST, DELUGE_PORT, DELUGE_USERNAME, DELUGE_PASSWORD
  - Skip: Set `SKIP_LIVE_TESTS=1`

### Torrent Search Module (`tests/torrent_search/`)

#### Unit Tests
- **test_models.py**: Database models (TorrentSearchResult, SearchStatus)
- **test_routes.py**: API endpoints (search, status, stats)
- **test_schemas.py**: Pydantic schemas (TorrentResult, QualityInfo)
- **test_service.py**: Service layer (quality parsing, scoring, Prowlarr integration - mocked)

#### Live Tests
- **test_live.py**: Real Prowlarr connection tests
  - Tests: Prowlarr connection, indexer listing, search functionality
  - Requires: Prowlarr running, PROWLARR_API_KEY configured
  - Usage: `docker-compose exec fastapi python tests/torrent_search/test_live.py`

### Scanner Module (`tests/scanner/`)

#### Unit Tests
- **test_models.py**: Database models (ScanResult, ScanStatus)
- **test_routes.py**: API endpoints (scan, status, results)
- **test_schemas.py**: Pydantic schemas validation
- **test_service.py**: Service layer (ClamAV, YARA scanning - mocked)

### Plex Module (`tests/plex/`)

#### Unit Tests
- **test_models.py**: Database models (PlexUser, WishlistItem)
- **test_routes.py**: API endpoints (sync, wishlist management)
- **test_service.py**: Service layer (Plex API integration - mocked)

#### Manual Tests
- **manual_test_plex_connection.py**: Manual Plex connection verification
- **manual_test_watchlist_modify.py**: Manual watchlist modification tests

### Integration Tests (`tests/integration/`)

#### test_pipeline.py
**Full pipeline end-to-end test:**
1. Prowlarr connection check
2. Create test wishlist item
3. Search for torrents
4. Verify Deluge torrent status
5. Check scanner status

**Usage**: `docker-compose exec fastapi python tests/integration/test_pipeline.py`

#### test_prowlarr_deluge_integration.py
**Step-by-step integration test:**
1. Direct Prowlarr search
2. Quality scoring verification
3. Deluge connection test
4. Full integration (Prowlarr → Deluge)

**Usage**: `docker-compose exec fastapi python tests/integration/test_prowlarr_deluge_integration.py`

### Common Tests (`tests/common/`)

- **test_security.py**: API key authentication tests

## Running Tests

### Run All Unit Tests (Mocked)
```bash
docker-compose exec fastapi pytest tests/ -v
```

### Run Specific Module Tests
```bash
# Deluge tests
docker-compose exec fastapi pytest tests/deluge/ -v

# Torrent search tests
docker-compose exec fastapi pytest tests/torrent_search/ -v

# Scanner tests
docker-compose exec fastapi pytest tests/scanner/ -v
```

### Run Live Tests
```bash
# Enable live tests
export SKIP_LIVE_TESTS=0

# Run Deluge live tests
docker-compose exec fastapi pytest tests/deluge/test_deluge_live.py -v

# Run Prowlarr live test (script)
docker-compose exec fastapi python tests/torrent_search/test_live.py
```

### Run Integration Tests
```bash
# Full pipeline test
docker-compose exec fastapi python tests/integration/test_pipeline.py

# Prowlarr-Deluge integration
docker-compose exec fastapi python tests/integration/test_prowlarr_deluge_integration.py
```

### Run with Coverage
```bash
docker-compose exec fastapi pytest tests/ --cov=app --cov-report=html
```

## Test Coverage Summary

### Deluge Module
- ✅ Models: TorrentItem, TorrentStatus enum
- ✅ Routes: Status, add, remove, list, sync endpoints
- ✅ Service: Connection, torrent management, status sync
- ✅ Live: Real daemon connection and operations

### Torrent Search Module
- ✅ Models: TorrentSearchResult, SearchStatus enum
- ✅ Routes: Search, status, stats, result endpoints
- ✅ Service: Quality parsing, scoring, Prowlarr integration
- ✅ Live: Real Prowlarr connection and search

### Scanner Module
- ✅ Models: ScanResult, ScanStatus enum
- ✅ Routes: Scan, status, results endpoints
- ✅ Service: ClamAV, YARA scanning logic
- ⚠️  Live: Not yet implemented (requires test files)

### Plex Module
- ✅ Models: PlexUser, WishlistItem
- ✅ Routes: Sync, wishlist management
- ✅ Service: Plex API integration
- ⚠️  Live: Manual tests only

## Test Requirements

### Environment Variables
- `DATABASE_URL`: Database connection (tests use in-memory SQLite)
- `API_KEY`: API authentication key
- `DELUGE_HOST`, `DELUGE_PORT`, `DELUGE_USERNAME`, `DELUGE_PASSWORD`: For live Deluge tests
- `PROWLARR_HOST`, `PROWLARR_PORT`, `PROWLARR_API_KEY`: For live Prowlarr tests
- `SKIP_LIVE_TESTS`: Set to `1` to skip live tests (default: `0`)

### Service Dependencies
- **Unit Tests**: None (all mocked)
- **Live Tests**: Deluge daemon, Prowlarr service
- **Integration Tests**: All services (Prowlarr, Deluge, Scanner, Database)

## Test Best Practices

1. **Unit tests should be fast**: Use mocks, avoid external calls
2. **Live tests should be optional**: Use `SKIP_LIVE_TESTS` flag
3. **Integration tests should be comprehensive**: Test full workflows
4. **Use descriptive test names**: `test_<what>_<condition>_<expected_result>`
5. **Keep tests isolated**: Each test should be independent
6. **Clean up after tests**: Use fixtures for setup/teardown

## Troubleshooting

### Tests Fail with "Connection Refused"
- Check if required services are running: `docker-compose ps`
- Verify environment variables are set correctly
- Check service logs: `docker-compose logs <service>`

### Live Tests Skipped
- Set `SKIP_LIVE_TESTS=0` to enable
- Ensure required credentials are configured
- Verify services are accessible

### Import Errors
- Ensure running from within container: `docker-compose exec fastapi`
- Check Python path includes `/app`
- Verify all dependencies installed: `pip list`

## Future Improvements

- [ ] Add more live tests for Scanner module
- [ ] Add performance/load tests
- [ ] Add API contract tests
- [ ] Improve test coverage reporting
- [ ] Add CI/CD test automation



