# Antivirus (ClamAV + YARA)

The **antivirus** container runs ClamAV (`clamd` on port 3310) plus a custom HTTP scan API (`http_scan_server.py` on port 3311) used by FastAPI.

## In Git

| Path | Purpose |
|------|---------|
| `scan-service/startup.sh` | Container entrypoint: installs deps, starts HTTP scan service, then ClamAV |
| `scan-service/http_scan_server.py` | HTTP API for path/torrent scanning (ClamAV + YARA) |
| `scan-service/yara-rules-custom/` | Project-specific YARA rules (always mounted) |
| `update-scripts/init-yara-rules.sh` | Clones community YARA rules on first start |
| `update-scripts/setup-cron.sh` | Daily cron for signature/rule updates |
| `update-scripts/update-antivirus.sh` | Runs `freshclam` + YARA git pull |

Compose mounts these into the `clamav/clamav` image — see `docker-compose.yml` → `antivirus` service.

## Not in Git (runtime, by design)

| Path | Why ignored | How it is created |
|------|-------------|-------------------|
| `data/` | Large ClamAV virus definition files | `freshclam` downloads on first container start (2–5 min) |
| `yara-rules/` | Large community rule set from GitHub | `init-yara-rules.sh` clones `Yara-Rules/rules` on first start |

A few small bootstrap files under `data/` (e.g. `bytecode.cvd`, `freshclam.dat`) may be committed to speed up first boot; full signature sets are not stored in Git.

## First start

1. `docker compose up -d antivirus`
2. Wait for healthcheck (can take several minutes while ClamAV downloads definitions)
3. Verify:
   ```powershell
   curl http://localhost:8000/antivirus/health
   docker compose logs antivirus --tail 30
   ```

YARA rules require network access on first run (git clone from GitHub). If clone fails, ClamAV scanning still works; YARA matches will be limited to `yara-rules-custom/`.

## Custom YARA rules

Add or edit rules under `scan-service/yara-rules-custom/` (tracked in Git). Restart after changes:

```powershell
docker compose restart antivirus
```

Community rules live in `yara-rules/` (runtime only). Do not commit that folder.

## Related docs

- [docs/ANTIVIRUS.md](../../docs/ANTIVIRUS.md) — scan flow and API usage
- [docs/DOCKER_SETUP.md](../../docs/DOCKER_SETUP.md) — Step 5.5 Antivirus
