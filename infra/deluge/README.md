# Deluge Configuration

This folder contains Deluge torrent client configuration for the media automation service.

## Architecture

- **Deluge** runs through **Gluetun** VPN container (`network_mode: "service:gluetun"`)
- All torrent traffic is routed through the VPN tunnel
- The FastAPI service connects to Deluge daemon via `gluetun:58846`

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

### 2. Add API User

Add a line to `config/auth`:
```
deluge:deluge:10
```

Format: `username:password:level` (level 10 = admin)

### 3. Restart Deluge

```bash
docker-compose restart deluge
```

## Environment Variables

Set these in your `.env` file:

```env
DELUGE_HOST=gluetun
DELUGE_PORT=58846
DELUGE_USERNAME=deluge
DELUGE_PASSWORD=deluge
```

## Web UI Access

The Deluge Web UI is available at `http://localhost:8112`

Default password: `deluge`

## Troubleshooting

### Connection Refused
- Ensure `allow_remote: true` in `config/core.conf`
- Ensure the `99-fix-daemon-interface` script is present
- Check that Gluetun is healthy: `docker-compose ps`

### VPN Not Working
- Check Gluetun logs: `docker logs gluetun`
- Verify VPN credentials in `.env`
- Look for `on_alert_external_ip` in Deluge logs - should show VPN IP, not your real IP

