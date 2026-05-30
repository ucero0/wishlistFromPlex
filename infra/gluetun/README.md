# Gluetun (VPN tunnel)

Gluetun routes Deluge, Prowlarr, and FlareSolverr through NordVPN on the default stack.

## In Git

| File | Purpose |
|------|---------|
| `entrypoint-wrapper.sh` | Starts health monitor, then runs Gluetun's default entrypoint |
| `health-monitor-wrapper.sh` | In-container monitor; exits gluetun after repeated VPN failures (Docker `restart: unless-stopped`) |
| `monitor-health.sh` | Optional host-side monitor (uses `docker inspect`; not mounted in compose) |

**Autoheal:** `docker-compose.yml` includes a [willfarrell/autoheal](https://hub.docker.com/r/willfarrell/autoheal) service. Gluetun is labeled `autoheal=true` so Docker restarts it when the healthcheck reports `unhealthy` (in addition to the in-container monitor).

## Not in Git (runtime)

| Path | Why ignored |
|------|-------------|
| `servers.json` | Large VPN server list downloaded by Gluetun |

## Compose wiring

`docker-compose.yml` mounts:

- `./infra/gluetun:/gluetun` — persistent Gluetun state
- `./infra/gluetun/entrypoint-wrapper.sh` — custom entrypoint
- `./infra/gluetun/health-monitor-wrapper.sh` — in-container health monitor

Deluge/Prowlarr/FlareSolverr use `network_mode: service:gluetun`. FastAPI reaches them via `DELUGE_HOST=gluetun` and `PROWLARR_HOST=gluetun` in `.env`.

For local dev without VPN, use [docker-compose.no-vpn.yml](../../docker-compose.no-vpn.yml) instead.
