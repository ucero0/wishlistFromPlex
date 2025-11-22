# Plex Wishlist Service

A Dockerized FastAPI + PostgreSQL service that syncs Plex user watchlists into a shared database and exposes a REST API for management and querying.

## Features

- **Multi-User Support**: Store and manage multiple Plex user tokens
- **Automatic Syncing**: Periodically syncs watchlists from all active users
- **Shared Wishlist**: Merges all users' watchlists into a single database
- **REST API**: Full API for managing users and querying the wishlist
- **Dockerized**: Easy deployment with Docker Compose
- **Secure**: Token masking and API key protection

## Architecture

- **FastAPI**: Modern Python web framework for the API
- **PostgreSQL**: Relational database for storing users and wishlist items
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations
- **APScheduler**: Background scheduler for automatic syncing
- **Docker Compose**: Orchestration for services

## Project Structure

```
plex-wishlist-service/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/                    # API routes
│   │   ├── routes_tokens.py   # User/token management
│   │   ├── routes_wishlist.py # Wishlist queries
│   │   └── routes_sync.py     # Sync operations
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Configuration
│   │   ├── db.py              # Database setup
│   │   ├── security.py        # Security utilities
│   │   └── scheduler.py       # Background scheduler
│   ├── models/                 # Database models
│   │   ├── plex_user.py
│   │   └── wishlist_item.py
│   └── services/               # Business logic
│       ├── plex_client.py     # Plex API client
│       └── sync_service.py    # Sync logic
├── alembic/                    # Database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Plex user tokens (see [Getting Plex Tokens](#getting-plex-tokens))

### Local Setup

1. **Clone or download this repository**

2. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env`** with your configuration:
   ```env
   DATABASE_URL=postgresql://plex_wishlist_user:plex_wishlist_pass@db:5432/plex_wishlist
   API_KEY=your-secret-api-key-change-this
   PLEX_SYNC_INTERVAL_HOURS=6
   LOG_LEVEL=INFO
   POSTGRES_USER=plex_wishlist_user
   POSTGRES_PASSWORD=plex_wishlist_pass
   POSTGRES_DB=plex_wishlist
   ```

4. **Build and start services**:
   ```bash
   docker compose up --build -d
   ```

5. **Run database migrations**:
   ```bash
   docker compose exec fastapi alembic upgrade head
   ```

6. **Access the API**:
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Synology Deployment

1. **Copy project to Synology**:
   ```bash
   # On your Synology, create directory
   mkdir -p /volume1/docker/plex-wishlist
   # Copy all project files to this directory
   ```

2. **Create `.env` file** on Synology with your settings

3. **Start services**:
   ```bash
   cd /volume1/docker/plex-wishlist
   docker compose up -d
   ```

4. **Run migrations**:
   ```bash
   docker compose exec fastapi alembic upgrade head
   ```

5. **Optional: Set up reverse proxy** in Synology DSM:
   - Control Panel → Application Portal → Reverse Proxy
   - Add rule pointing to `http://localhost:8000`
   - Access via `http://nas.local/plex-wishlist`

## Getting Plex Tokens

To get a Plex user token:

1. **Method 1: Using Plex Web App**
   - Log in to https://app.plex.tv
   - Open browser developer tools (F12)
   - Go to Network tab
   - Look for requests to `plex.tv` and find the `X-Plex-Token` header

2. **Method 2: Using Plex API**
   - Visit: `https://plex.tv/api/v2/user?X-Plex-Product=Plex%20Web&X-Plex-Client-Identifier=<random-uuid>`
   - You'll need to authenticate and extract the token from the response

3. **Method 3: Third-party tools**
   - Use tools like `plex-token` npm package or browser extensions

## API Usage

### Authentication

All write operations (POST, PATCH, DELETE) require an API key in the header:
```
X-API-Key: your-secret-api-key
```

### Managing Users

**Create a new Plex user:**
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{
    "name": "John Doe",
    "token": "plex-token-here"
  }'
```

**List all users:**
```bash
curl http://localhost:8000/api/users
```

**Update a user:**
```bash
curl -X PATCH http://localhost:8000/api/users/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{
    "active": false
  }'
```

**Delete a user (soft delete):**
```bash
curl -X DELETE http://localhost:8000/api/users/1 \
  -H "X-API-Key: your-secret-api-key"
```

### Querying Wishlist

**Get all wishlist items:**
```bash
curl http://localhost:8000/api/wishlist
```

**Search by title:**
```bash
curl "http://localhost:8000/api/wishlist?search=matrix"
```

**Filter by year:**
```bash
curl "http://localhost:8000/api/wishlist?year=2023"
```

**Pagination:**
```bash
curl "http://localhost:8000/api/wishlist?limit=50&offset=0"
```

**Get specific item:**
```bash
curl http://localhost:8000/api/wishlist/plex://movie/guid/...
```

**Get statistics:**
```bash
curl http://localhost:8000/api/wishlist/stats/summary
```

### Syncing

**Trigger manual sync:**
```bash
curl -X POST http://localhost:8000/api/sync \
  -H "X-API-Key: your-secret-api-key"
```

**Get sync status:**
```bash
curl http://localhost:8000/api/sync/status
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `API_KEY` | API key for write operations | Required |
| `PLEX_SYNC_INTERVAL_HOURS` | Hours between automatic syncs | `6` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `POSTGRES_USER` | PostgreSQL username | `plex_wishlist_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `plex_wishlist_pass` |
| `POSTGRES_DB` | PostgreSQL database name | `plex_wishlist` |

## Database Schema

### `plex_users`
- `id`: Primary key
- `name`: User identifier/label
- `plex_token`: Plex authentication token (encrypted in future versions)
- `active`: Whether user is active
- `created_at`, `updated_at`: Timestamps

### `wishlist_items`
- `id`: Primary key
- `uid`: Unique Plex GUID (e.g., `plex://movie/guid/...`)
- `title`: Movie/show title
- `year`: Release year (nullable)
- `added_at`, `last_seen_at`: Timestamps

### `wishlist_item_sources`
- `id`: Primary key
- `wishlist_item_id`: Foreign key to `wishlist_items`
- `plex_user_id`: Foreign key to `plex_users`
- `first_added_at`, `last_seen_at`: Timestamps

## Automatic Syncing

The service includes an internal scheduler (APScheduler) that automatically syncs watchlists at the configured interval. The scheduler:

- Runs in the background
- Syncs all active users
- Logs all operations
- Handles errors gracefully

You can also trigger manual syncs via the `/api/sync` endpoint.

## Docker Commands

**Start services:**
```bash
docker compose up -d
```

**Stop services:**
```bash
docker compose down
```

**View logs:**
```bash
docker compose logs -f fastapi
docker compose logs -f db
```

**Run migrations:**
```bash
docker compose exec fastapi alembic upgrade head
```

**Create new migration:**
```bash
docker compose exec fastapi alembic revision --autogenerate -m "Description"
```

**Access database:**
```bash
docker compose exec db psql -U plex_wishlist_user -d plex_wishlist
```

**Rebuild after code changes:**
```bash
docker compose up --build -d
```

## Testing

The project includes a comprehensive test suite using pytest.

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_security.py
```

**Run in Docker:**
```bash
docker compose exec fastapi pytest
```

### Test Coverage

The test suite covers:
- Security functions (token masking, API key verification)
- Database models (CRUD operations, relationships)
- Plex API client (with mocked HTTP responses)
- Sync service (merging, deduplication, error handling)
- All API endpoints (GET, POST, PATCH, DELETE)
- Error handling and edge cases

See `tests/README.md` for more details.

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL container is healthy: `docker compose ps`
- Check database credentials in `.env`
- Verify `DATABASE_URL` format: `postgresql://user:pass@db:5432/dbname`

### Sync Not Working

- Check logs: `docker compose logs fastapi`
- Verify Plex tokens are valid
- Test token manually with Plex API
- Check network connectivity from container

### API Key Not Working

- Verify `API_KEY` in `.env` matches the header value
- Check for typos or extra spaces
- Ensure header name is exactly `X-API-Key`

## Future Enhancements

- [ ] Token encryption at rest
- [ ] Web UI for viewing/managing wishlist
- [ ] Write back to Plex collection
- [ ] Remove items from Plex watchlists after sync
- [ ] Additional metadata (posters, genres, descriptions)
- [ ] Export wishlist to various formats
- [ ] Notification system for new items

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests for improvements.



