# Testing Guide

This guide explains how to run the test suite for the Plex Wishlist Service.

## Prerequisites

Before running tests, ensure you have:
- Python 3.11+ installed
- All dependencies installed (see below)

## Setup

### 1. Install Dependencies

**Option A: Local Python Environment**
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Option B: Using Docker**
```bash
# Build the Docker image first
docker compose build
```

## Running Tests

### Quick Start

**Run all tests:**
```bash
pytest
```

This will:
- Run all tests in the `tests/` directory
- Show verbose output (`-v` flag)
- Generate coverage reports
- Use SQLite in-memory database (no setup needed)

### Common Test Commands

**Run with detailed output:**
```bash
pytest -v
```

**Run with coverage report:**
```bash
pytest --cov=app --cov-report=term-missing
```

**Generate HTML coverage report:**
```bash
pytest --cov=app --cov-report=html
# Then open htmlcov/index.html in your browser
```

**Run specific test file:**
```bash
pytest tests/test_security.py
pytest tests/test_models.py
pytest tests/test_api_routes_tokens.py
```

**Run specific test class:**
```bash
pytest tests/test_security.py::TestMaskToken
```

**Run specific test function:**
```bash
pytest tests/test_security.py::TestMaskToken::test_mask_token_normal
```

**Run tests matching a pattern:**
```bash
pytest -k "token"  # Runs all tests with "token" in the name
pytest -k "api"    # Runs all API-related tests
```

**Stop on first failure:**
```bash
pytest -x
```

**Show print statements:**
```bash
pytest -s
```

## Running Tests in Docker

If you prefer to run tests in the Docker container:

```bash
# Start services (if not already running)
docker compose up -d

# Run tests in the FastAPI container
docker compose exec fastapi pytest

# Run with coverage
docker compose exec fastapi pytest --cov=app --cov-report=term-missing

# Run specific test file
docker compose exec fastapi pytest tests/test_security.py
```

## Test Output Examples

### Successful Test Run
```
============================= test session starts ==============================
platform win32 -- Python 3.11.0, pytest-7.4.3, pytest-asyncio-0.21.1
collected 45 items

tests/test_security.py ................                                    [ 35%]
tests/test_models.py .........                                            [ 60%]
tests/test_plex_client.py ........                                        [ 77%]
tests/test_sync_service.py ......                                         [ 91%]
tests/test_api_routes_tokens.py .....                                     [100%]

============================= 45 passed in 2.34s ==============================
```

### With Coverage
```
============================= test session starts ==============================
platform win32 -- Python 3.11.0, pytest-7.4.3, pytest-asyncio-0.21.1
collected 45 items

tests/test_security.py ................                                    [ 35%]
...

---------- coverage: platform win32, python 3.11.0 -----------
Name                          Stmts   Miss  Cover   Missing
-------------------------------------------------------------
app/__init__.py                  0      0   100%
app/core/config.py              12      0   100%
app/core/db.py                  18      1    94%   28
app/core/security.py            15      0   100%
...
-------------------------------------------------------------
TOTAL                           450     45    90%
============================= 45 passed in 3.12s ==============================
```

## Test Categories

### 1. Security Tests (`test_security.py`)
Tests token masking and API key verification:
```bash
pytest tests/test_security.py -v
```

### 2. Model Tests (`test_models.py`)
Tests database models and relationships:
```bash
pytest tests/test_models.py -v
```

### 3. Plex Client Tests (`test_plex_client.py`)
Tests Plex API integration (with mocked responses):
```bash
pytest tests/test_plex_client.py -v
```

### 4. Sync Service Tests (`test_sync_service.py`)
Tests the sync logic and merging:
```bash
pytest tests/test_sync_service.py -v
```

### 5. API Route Tests
Tests all API endpoints:
```bash
# User/token management
pytest tests/test_api_routes_tokens.py -v

# Wishlist queries
pytest tests/test_api_routes_wishlist.py -v

# Sync endpoints
pytest tests/test_api_routes_sync.py -v
```

### 6. Main App Tests (`test_main.py`)
Tests root and health endpoints:
```bash
pytest tests/test_main.py -v
```

## Troubleshooting

### Issue: ModuleNotFoundError

**Problem:** Tests can't find the `app` module.

**Solution:**
```bash
# Make sure you're in the project root directory
cd /path/to/plex-wishlist-service

# Install in development mode
pip install -e .
```

### Issue: Database errors

**Problem:** Tests fail with database connection errors.

**Solution:** Tests use SQLite in-memory database automatically. No setup needed. If you see errors, check that `conftest.py` is in the `tests/` directory.

### Issue: Import errors with async

**Problem:** `pytest-asyncio` not working.

**Solution:**
```bash
# Reinstall pytest-asyncio
pip install pytest-asyncio

# Check pytest.ini has asyncio_mode = auto
```

### Issue: Coverage not showing

**Problem:** Coverage report is empty.

**Solution:**
```bash
# Install pytest-cov
pip install pytest-cov

# Run with explicit coverage
pytest --cov=app --cov-report=html
```

## Continuous Integration

To run tests in CI/CD, use:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=app --cov-report=xml

# Or in Docker
docker compose run --rm fastapi pytest
```

## Writing New Tests

When adding new features, follow these patterns:

1. **Test file naming:** `test_<module_name>.py`
2. **Test class naming:** `Test<ClassName>`
3. **Test function naming:** `test_<description>`
4. **Use fixtures:** Leverage `conftest.py` fixtures
5. **Mock external APIs:** Use `responses` library for HTTP mocking
6. **Isolate tests:** Each test gets a fresh database

Example:
```python
def test_new_feature(client, db_session):
    """Test description."""
    # Arrange
    # Act
    response = client.get("/api/endpoint")
    # Assert
    assert response.status_code == 200
```

## Test Coverage Goals

- **Minimum:** 80% coverage
- **Target:** 90%+ coverage
- **Critical paths:** 100% coverage (security, sync logic)

View coverage report:
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

## Next Steps

After running tests successfully:
1. Review coverage report
2. Add tests for any missing functionality
3. Fix any failing tests
4. Run tests before committing code

