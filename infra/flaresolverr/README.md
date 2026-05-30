# FlareSolverr

FlareSolverr has **no config folder** in this project. Runtime settings come from `docker-compose.yml`.

## In Git

| What | Where |
|------|--------|
| Service definition | `docker-compose.yml` → `flaresolverr` service |
| Prowlarr link URL | `docker-compose.yml` → `prowlarr` service → `FLARESOLVERR_URL` |

## Environment variables (compose)

**FlareSolverr container:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `FLARESOLVERR_LOG_LEVEL` | `info` | Log verbosity (via `.env`) |
| `FLARESOLVERR_CAPTCHA_SOLVER` | `none` | External captcha solver (via `.env`) |

**Prowlarr connection** (synced by bootstrap from `FLARESOLVERR_URL` in compose):

| Setting | Value |
|---------|-------|
| FlareSolverr URL | `http://flaresolverr:8191` |
| Request timeout | `60` s |

**VPN stack:** FlareSolverr is **not** on Gluetun. Prowlarr (inside VPN) calls `http://flaresolverr:8191` over the Docker bridge (`DNS_ADDRESS=127.0.0.11` on Gluetun). Port `8191` is **not** published to the host by default (internal only).

**No-VPN overlay:** same URL; optional host port mapping in `docker-compose.no-vpn.yml` for debugging.

## Not in Git

- No `/config` volume — nothing under `infra/flaresolverr/` except this README.
- Session/state is ephemeral inside the container.

The Prowlarr → FlareSolverr proxy is pre-configured in the committed `prowlarr.db`.
