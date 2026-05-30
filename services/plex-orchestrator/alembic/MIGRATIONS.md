# Database migrations

## Fresh install or full reset

```powershell
docker compose down
Remove-Item -Recurse -Force infra/postgres-data
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Revision `0001_initial_schema` is applied automatically on orchestrator startup.

## Commands (inside container)

```powershell
docker compose exec plex-orchestrator alembic current
docker compose exec plex-orchestrator alembic upgrade head
docker compose exec plex-orchestrator alembic history
```

## Add a new revision

1. Change ORM models under `app/infrastructure/persistence/`.
2. Generate (from repo root, with stack running and DB reachable):

```powershell
docker compose exec plex-orchestrator alembic revision --autogenerate -m "short description"
```

3. Review the new file under `alembic/versions/`.
4. Apply: `docker compose exec plex-orchestrator alembic upgrade head`
