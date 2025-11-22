# Test Suite

This directory contains comprehensive tests for the Plex Wishlist Service.

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_security.py
```

### Run specific test:
```bash
pytest tests/test_security.py::TestMaskToken::test_mask_token_normal
```

### Run with verbose output:
```bash
pytest -v
```

## Test Structure

- `conftest.py` - Shared fixtures and test configuration
- `test_security.py` - Security function tests (token masking, API key verification)
- `test_models.py` - Database model tests
- `test_plex_client.py` - Plex API client tests (with mocked HTTP responses)
- `test_sync_service.py` - Sync service tests
- `test_api_routes_tokens.py` - User/token management API route tests
- `test_api_routes_wishlist.py` - Wishlist query API route tests
- `test_api_routes_sync.py` - Sync API route tests
- `test_main.py` - Main application endpoint tests

## Test Fixtures

- `db_session` - Fresh database session for each test (SQLite in-memory)
- `client` - FastAPI test client with database override
- `test_settings` - Test configuration settings
- `sample_plex_token` - Sample Plex token for testing
- `sample_plex_user_data` - Sample user data for testing
- `sample_wishlist_item_data` - Sample wishlist item data for testing

## Test Coverage

The test suite covers:
- ✅ Security functions (token masking, API key verification)
- ✅ Database models (CRUD operations, relationships)
- ✅ Plex API client (with mocked responses)
- ✅ Sync service (merging, deduplication, error handling)
- ✅ All API endpoints (GET, POST, PATCH, DELETE)
- ✅ Error handling and edge cases
- ✅ Authentication and authorization

## Notes

- Tests use SQLite in-memory database for speed
- HTTP requests to Plex API are mocked using `responses` library
- Async functions are tested using `pytest-asyncio`
- Each test gets a fresh database session

