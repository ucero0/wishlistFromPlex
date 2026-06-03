# Gluetun (VPN tunnel)

Gluetun routes **Deluge**, **Prowlarr**, and **FlareSolverr** through NordVPN on the default stack (`network_mode: service:gluetun`).

## In Git

| File | Purpose |
|------|---------|
| `entrypoint-wrapper.sh` | Starts health monitor, then runs Gluetun's default entrypoint |
| `health-monitor-wrapper.sh` | In-container monitor; exits gluetun after repeated VPN failures (Docker `restart: unless-stopped`) |
| `sync-vpn-dependents.sh` | Reconciles Deluge/Prowlarr/FlareSolverr with the current Gluetun container |
| `vpn-stack-sync.entrypoint.sh` | Entrypoint for the `vpn-stack-sync` compose service |
| `monitor-health.sh` | Optional host-side monitor (not mounted in compose) |

## VPN stack services

| Service | Role |
|---------|------|
| **gluetun** | NordVPN tunnel; publishes Deluge/Prowlarr ports |
| **autoheal** | Restarts Gluetun when Docker healthcheck is `unhealthy` |
| **vpn-stack-sync** | After every Gluetun **start** (autoheal, health monitor, manual recreate), restarts or recreates dependents so they share the same network namespace |
| **deluge / prowlarr / flaresolverr** | Share Gluetun's network namespace |

**Why `vpn-stack-sync` exists:** `network_mode: service:gluetun` pins containers to Gluetun's **container ID**. When Gluetun is recreated, dependents can stay attached to a dead namespace (FlareSolverr becomes unreachable at `127.0.0.1:8191`). Autoheal only restarts Gluetun — it does not fix dependents. `vpn-stack-sync` watches `docker events` and reconciles the stack automatically.

### Manual one-shot sync

```bash
docker compose run --rm --entrypoint sync-vpn-dependents vpn-stack-sync once
```

### Full manual recreate (still valid)

```bash
docker compose up -d --force-recreate gluetun deluge prowlarr flaresolverr
```

## Not in Git (runtime)

| Path | Why ignored |
|------|-------------|
| `servers.json` | Large VPN server list downloaded by Gluetun |

## Compose wiring

- `./infra/gluetun:/gluetun` — persistent Gluetun state
- `./infra/gluetun/entrypoint-wrapper.sh` — custom entrypoint
- `./infra/gluetun/health-monitor-wrapper.sh` — in-container health monitor

FastAPI reaches Deluge/Prowlarr via `DELUGE_HOST=gluetun` and `PROWLARR_HOST=gluetun` in `.env`. Prowlarr reaches FlareSolverr at `http://127.0.0.1:8191` inside the shared namespace.

For local dev without VPN, use [docker-compose.no-vpn.yml](../../docker-compose.no-vpn.yml) instead.
