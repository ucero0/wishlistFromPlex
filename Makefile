.DEFAULT_GOAL := help

.PHONY: help dev prod down logs-orchestrator shell-orchestrator test test-plex rebuild-orchestrator db-reset db-migrate

help:
	@echo "Available commands:"
	@echo "  make dev                  Run local development stack (hot reload + dev deps)"
	@echo "  make prod                 Run production-like stack (runtime deps, no code mounts)"
	@echo "  make down                 Stop and remove containers"
	@echo "  make logs-orchestrator    Tail Plex orchestrator API logs"
	@echo "  make shell-orchestrator   Open shell inside Plex orchestrator container"
	@echo "  make test                 Run all tests inside Plex orchestrator dev container"
	@echo "  make test-plex            Run only Plex external API tests"
	@echo "  make rebuild-orchestrator Rebuild Plex orchestrator image only"
	@echo "  make db-reset           Wipe Postgres volume and restart stack (dev)"
	@echo "  make db-migrate         Apply Alembic migrations (upgrade head)"

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod:
	docker compose -f docker-compose.yml up --build

down:
	docker compose down

logs-orchestrator:
	docker compose logs -f plex-orchestrator

shell-orchestrator:
	docker compose exec plex-orchestrator sh

test:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm plex-orchestrator pytest -q

test-plex:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm plex-orchestrator pytest tests/infrastructure/externalApis/plex/plexServer/test_client.py -q

rebuild-orchestrator:
	docker compose build --no-cache plex-orchestrator

db-reset:
	docker compose down
	powershell -Command "Remove-Item -Recurse -Force infra/postgres-data -ErrorAction SilentlyContinue"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

db-migrate:
	docker compose exec plex-orchestrator alembic upgrade head
