# Wishlist from Plex

Automated media pipeline: Plex watchlists → torrent search (Prowlarr) → Deluge over VPN (Gluetun) → virus scan → Plex library organization.

## Quick start

1. **First-time Docker setup** → follow **[docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md)** (copy `.env`, configure services, start stack, verify health endpoints).
2. **Plex libraries** → add movie/TV folders in the Plex UI, then mount those same paths in `docker-compose.yml` for both `plex` and `fastapi` (not in `.env`). Run `POST /plex/servers/library/locations-by-media/sync` so ingest knows where to move files.
3. Start development stack:
   ```powershell
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```
4. API: http://localhost:8000/docs (use `X-API-Key` from `.env`).

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) | **Step-by-step** initial Docker / `.env` configuration |
| [infra/deluge/README.md](infra/deluge/README.md) | Deluge RPC auth & VPN networking |
| [services/fastapi-app/ARCHITECTURE_FOLDER_GUIDE.md](services/fastapi-app/ARCHITECTURE_FOLDER_GUIDE.md) | FastAPI hexagonal architecture |
| [docs/README.md](docs/README.md) | Antivirus service docs |

## Health checks (after setup)

```powershell
curl http://localhost:8000/gluetun/health
curl http://localhost:8000/deluge/test-connection
curl http://localhost:8000/prowlarr/test-connection
```

`deluge/test-connection` includes a `vpn` field so you can see whether the problem is Gluetun or Deluge RPC.
