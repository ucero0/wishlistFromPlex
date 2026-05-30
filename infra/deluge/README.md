# Deluge Configuration

This folder contains Deluge torrent client configuration for the media automation service.

**First-time stack setup:** see [docs/DOCKER_SETUP.md](../../docs/DOCKER_SETUP.md) (Steps 2.3, 5.2).  
**API usage:** [docs/USAGE.md](../../docs/USAGE.md) · [Documentation index](../../docs/README.md)

## Architecture

- **Deluge** runs through **Gluetun** on the default stack (`network_mode: "service:gluetun"`)
- Torrent traffic is routed through the VPN tunnel
- FastAPI connects via `DELUGE_HOST` / `DELUGE_PORT` from `.env` (use `gluetun:58846` on the VPN stack)
- For local dev without VPN, use `docker-compose.no-vpn.yml` and `DELUGE_HOST=deluge`

## Directory Structure

```
deluge/
├── config/           # Auto-generated at first run (gitignored)
│   ├── auth          # User authentication
│   ├── core.conf     # Deluge settings
│   ├── execute.conf  # Execute plugin hooks (auto-configured on start)
│   ├── ssl/          # Certificates
│   └── state/        # Session data
├── downloads/        # Downloaded files (gitignored except quarantine/.gitkeep)
├── custom-cont-init.d/
│   ├── 98-configure-deluge-downloads.sh  # Quarantine path, Execute plugin, complete hook
│   └── 99-configure-api-user.sh          # RPC + Web UI credentials from .env
├── scripts/
│   └── on-torrent-complete.sh            # Calls FastAPI scan-and-ingest on torrent complete
└── README.md         # This file
```

## Initial Setup

Before the **first** `docker compose up`, set a strong password in `.env`:

```env
DELUGE_USERNAME=deluge
DELUGE_PASSWORD=your-long-random-password
```

On container start, init scripts in `custom-cont-init.d/` automatically:

- Set `allow_remote: true` and quarantine `download_location` in `core.conf` (`98-configure-deluge-downloads.sh`)
- Enable the **Execute** plugin and register `/scripts/on-torrent-complete.sh` on torrent complete
- Apply RPC/Web UI credentials from `.env` (`99-configure-api-user.sh`)

When a download finishes, Deluge runs `scripts/on-torrent-complete.sh`, which calls `POST /pipelines/ingest/scan-and-ingest` on FastAPI (URL from `SCANFORVIRUS_API_URL` in `.env`).

After changing `.env` passwords later, restart Deluge:

```bash
docker compose restart deluge
```

Manual edit of `config/auth` is only needed if you skip the init scripts or change credentials outside `.env`.
## Environment Variables

Set these in your `.env` file:

```env
# VPN stack (default)
DELUGE_HOST=gluetun
DELUGE_PORT=58846
DELUGE_USERNAME=deluge
DELUGE_PASSWORD=your-long-random-password

# No-VPN standalone file — use DELUGE_HOST=deluge instead
```

## Web UI Access

The Deluge Web UI is available at `http://localhost:8112`

Default password: `deluge`

## Troubleshooting

### Connection Refused
- Init scripts in `custom-cont-init.d/` must be **executable** (`chmod +x`); they set `allow_remote: true` in `core.conf`
- `custom-services.d/ensure-remote-rpc` sets `allow_remote` once (marker: `/config/.deluge-remote-rpc-configured`); restarts the daemon only when that flag was just changed
- VPN stack: `DELUGE_HOST=gluetun`, port `58846` published on Gluetun; check `docker compose ps gluetun`
- No-VPN: `DELUGE_HOST=deluge`, check Deluge is running (`docker compose ps deluge`)
- From orchestrator: `docker exec plex-orchestrator python3 -c "from deluge_client import DelugeRPCClient; ..."` should connect

### VPN Not Working
- Check Gluetun logs: `docker logs gluetun`
- Verify VPN credentials in `.env`

