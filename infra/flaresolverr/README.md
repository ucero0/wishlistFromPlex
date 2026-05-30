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

**Prowlarr connection** (stored in `infra/prowlarr/config/prowlarr.db`, not `.env`):

| Setting | Value |
|---------|-------|
| FlareSolverr URL | `http://127.0.0.1:8191` |
| Request timeout | `60` s |

Prowlarr shares Gluetun’s network with FlareSolverr, so the URL uses `127.0.0.1:8191`.

## Not in Git

- No `/config` volume — nothing under `infra/flaresolverr/` except this README.
- Session/state is ephemeral inside the container.

The Prowlarr → FlareSolverr proxy is pre-configured in the committed `prowlarr.db`.
