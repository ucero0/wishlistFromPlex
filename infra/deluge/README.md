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
│   ├── ssl/          # Certificates
│   └── state/        # Session data
├── downloads/        # Downloaded files (gitignored)
├── custom-cont-init.d/
│   └── 99-fix-daemon-interface  # Enables remote daemon connections
└── README.md         # This file
```

## Initial Setup (after first container start)

### 1. Enable Remote Connections

Edit `config/core.conf` and set:
```json
"allow_remote": true,
```

### 2. Set credentials in `.env` (recommended)

Before the **first** `docker compose up`, set a strong password in `.env`:

```env
DELUGE_USERNAME=deluge
DELUGE_PASSWORD=your-long-random-password
```

The init script (`custom-cont-init.d/99-configure-api-user.sh`) then:

- Removes the default RPC user `deluge:deluge`
- Configures RPC auth from `.env` (plain password in `config/auth`, format `user:password:level`)
- Sets the Web UI password (login **`admin`**) from `DELUGE_WEB_PASSWORD` or `DELUGE_PASSWORD`

Manual edit of `config/auth` is only needed if you skip the init script or change credentials outside `.env`.

### 3. Restart Deluge

```bash
docker-compose restart deluge
```

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
- Ensure `allow_remote: true` in `config/core.conf`
- Ensure the `99-fix-daemon-interface` script is present
- VPN stack: check Gluetun is healthy (`docker compose ps gluetun`)
- No-VPN: check Deluge is running (`docker compose ps deluge`)

### VPN Not Working
- Check Gluetun logs: `docker logs gluetun`
- Verify VPN credentials in `.env`

