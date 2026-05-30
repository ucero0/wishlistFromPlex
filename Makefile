.DEFAULT_GOAL := help

.PHONY: help dev prod down logs-fastapi shell-fastapi test test-plex rebuild-fastapi

help:
	@echo "Available commands:"
	@echo "  make dev            Run local development stack (hot reload + dev deps)"
	@echo "  make prod           Run production-like stack (runtime deps, no code mounts)"
	@echo "  make down           Stop and remove containers"
	@echo "  make logs-fastapi   Tail FastAPI logs"
	@echo "  make shell-fastapi  Open shell inside FastAPI container"
	@echo "  make test           Run all tests inside FastAPI dev container"
	@echo "  make test-plex      Run only Plex external API tests"
	@echo "  make rebuild-fastapi Rebuild FastAPI image only"

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod:
	docker compose -f docker-compose.yml up --build

down:
	docker compose down

logs-fastapi:
	docker compose logs -f fastapi

shell-fastapi:
	docker compose exec fastapi sh

test:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm fastapi pytest -q

test-plex:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm fastapi pytest tests/infrastructure/externalApis/plex/plexServer/test_client.py -q

rebuild-fastapi:
	docker compose build --no-cache fastapi
