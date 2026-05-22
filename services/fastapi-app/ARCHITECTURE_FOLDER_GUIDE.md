# FastAPI Folder Structure Guide (Hexagonal + Scalable)

This guide explains the current folder structure in `services/fastapi-app/app`, what each folder is responsible for, and how to decide where new code should go.

The goal is to keep the codebase scalable, testable, and aligned with Hexagonal Architecture (Ports and Adapters).

---

## 1) Architecture in one sentence

The **domain** defines business rules and contracts, the **application** orchestrates use cases, **adapters** translate boundaries (HTTP/external), **infrastructure** implements technical details, and **composition/factories** wire everything together.

---

## 2) Current top-level folders and responsibilities

Inside `services/fastapi-app/app`:

- `domain/`
  - Pure business core.
  - No FastAPI, no SQLAlchemy ORM, no HTTP clients.
  - Contains:
    - `models/`: business entities/value objects (`PlexUser`, `MediaItem`, `TorrentDownload`, etc.).
    - `ports/`: interfaces/protocols for repositories and external providers.
    - `services/`: domain-level service contracts or domain policies.

- `application/`
  - Use cases and queries (application orchestration).
  - Calls domain ports, not infrastructure implementations directly.
  - Organized by bounded context (`plex`, `prowlarr`, `antivirus`, `deluge`, `torrentDownload`, `orchestrators`, `tmdb`).

- `adapters/`
  - Boundary translators.
  - `adapters/http/`: FastAPI routes and HTTP schemas (request/response models).
  - `adapters/external/`: maps raw external DTOs into domain-safe models and implements provider behavior expected by ports.

- `infrastructure/`
  - Technical details and IO implementations.
  - `persistence/`: DB session, ORM models, repository implementations.
  - `externalApis/`: low-level external clients and raw external schemas.
  - `services/`: technical service implementations (for example filesystem implementation).
  - `scheduler/`: scheduled tasks entrypoints.

- `composition/`
  - Framework-agnostic dependency assembly for complex use cases.
  - Should be the main place for object graph construction (composition root style).

- `factories/`
  - FastAPI dependency wrappers (`Depends`) and constructor helpers.
  - Thin layer preferred: call composition builders when possible.

- `core/`
  - Cross-cutting technical setup: config, constants, logging, shared app setup concerns.

---

## 3) Dependency direction (critical rule)

Allowed direction (inner to outer dependency rule):

1. `domain` -> depends on nothing application-specific or infrastructure-specific.
2. `application` -> can depend on `domain`.
3. `adapters` -> can depend on `application` and `domain`.
4. `infrastructure` -> can depend on `domain` contracts and technical libraries.
5. `composition/factories` -> can depend on all layers for wiring.

Practical rule:

- Never import from `infrastructure` inside `domain`.
- Avoid importing `adapters` from `application`.
- Keep `Depends(...)` in HTTP/factory entrypoints, not in domain logic.

---

## 4) How to decide where new code goes

Use this decision flow:

1. Is it business data or business rule without IO?
   - Put in `domain/models` or `domain/services`.
2. Is it a use case/query that orchestrates behavior?
   - Put in `application/<context>/useCases` or `application/<context>/queries`.
3. Is it HTTP input/output or route handling?
   - Put in `adapters/http/schemas` or `adapters/http/routes`.
4. Is it a raw API client call or DB repository implementation?
   - Put in `infrastructure/externalApis` or `infrastructure/persistence`.
5. Is it translating external/raw model <-> domain model?
   - Put in `adapters/external/<context>/mapper.py` (or adapter module).
6. Is it wiring dependencies for runtime?
   - Put in `composition/` (preferred) and expose via `factories/` wrappers for FastAPI.

---

## 5) What to place in each layer (examples)

### Example A: Add new endpoint "Get Plex libraries"

- HTTP request/response models:
  - `adapters/http/schemas/plex/...`
- Route handler:
  - `adapters/http/routes/plex/...`
- Application query/use case:
  - `application/plex/queries/...`
- Domain port (if new behavior contract is needed):
  - `domain/ports/external/plex/...`
- External raw API call:
  - `infrastructure/externalApis/plex/plexServer/client.py`
- External -> domain mapping:
  - `adapters/external/plexServer/adapter.py`
- Wiring:
  - `composition/...` and thin `factories/...` wrapper

### Example B: Add persistence for a new entity

- Domain model:
  - `domain/models/<entity>.py`
- Repository port:
  - `domain/ports/repositories/<context>/...`
- Application use cases/queries:
  - `application/<context>/...`
- ORM model + repo implementation:
  - `infrastructure/persistence/<context>/model/...`
  - `infrastructure/persistence/<context>/repo/...`
- Factory/composition wiring:
  - `composition/...` and/or `factories/<context>/...`

### Example C: Integrate a new external provider

- Provider port:
  - `domain/ports/external/<provider>/...`
- Raw client + external DTOs:
  - `infrastructure/externalApis/<provider>/client.py`
  - `infrastructure/externalApis/<provider>/schemas.py`
- Adapter that maps to domain:
  - `adapters/external/<provider>/adapter.py`
  - `adapters/external/<provider>/mapper.py` (if needed)
- Use in application through port abstraction:
  - `application/<context>/...`

---

## 6) Naming convention guide (for scalability)

Recommended default:

- File/module names: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Keep external API field naming compatibility through aliases in schemas, while internal names remain `snake_case`.

For this repository specifically:

- Prefer new names like:
  - `use_cases` over `useCases`
  - `external_apis` over `externalApis`
  - `*_routes.py`, `*_factory.py`
- Do not do mass rename in one step; migrate incrementally with compatibility wrappers.

---

## 7) Composition and DI pattern to follow

Preferred scalable pattern:

- `composition/` builds object graphs (framework-agnostic).
- `factories/` are thin wrappers for FastAPI dependencies.
- `adapters/http/routes` depend on factory functions only for injection.

Why:

- Keeps framework concerns isolated.
- Makes scheduled tasks and tests reuse the same composition logic.
- Reduces coupling and duplicated wiring code.

---

## 8) Testing placement strategy

- Unit tests close to layer behavior:
  - `tests/domain/...`
  - `tests/application/...`
  - `tests/adapters/...`
  - `tests/infrastructure/...`
- Architecture guardrails:
  - `tests/architecture/...` (dependency direction, contract checks)
- Use external API client tests for raw clients and adapter tests for mapping behavior.

---

## 9) External API errors (shared pattern)

Use this pattern for **all** external integrations (Deluge, Prowlarr, Antivirus, Plex, TMDB):

| Layer | Responsibility |
|-------|----------------|
| `domain/errors/<service>.py` | Typed exceptions extending `ExternalServiceError` |
| `domain/models/external_connection.py` | Pydantic `ExternalConnectionStatus` for health probes |
| `infrastructure/externalApis/<service>/client.py` | Raise domain errors; never `HTTPException` or `[]` on failure |
| `infrastructure/http_errors.py` | Shared `raise_mapped_httpx_error()` for httpx → domain mapping |
| `adapters/external/<service>/adapter.py` | Map infra → domain; implement port |
| `application/.../queries/test*Connection.py` | Thin query wrapping `provider.test_connection()` |
| `adapters/http/exception_handlers.py` | Single `ExternalServiceError` handler → HTTP status |
| `adapters/http/schemas/common/` | Pydantic `ExternalServiceErrorResponse` for API error bodies |

HTTP mapping (all services via `external_service_error_handler`):

- `*ConnectionError`, `TMDBConfigurationError` → `503` (`connection`)
- `*OperationError`, `ProwlarrDownloadError` → `502` (`operation` / `download`)
- `DelugeTorrentNotFoundError`, `AntivirusPathNotFoundError` → `404` (`not_found`)
- `PlexAuthError` → `401` (`auth`)

Health / connectivity probes (non-throwing, return `ExternalConnectionStatus`):

| Service | Endpoint |
|---------|----------|
| Deluge | `GET /deluge/test-connection` |
| Prowlarr | `GET /prowlarr/test-connection` |
| Antivirus | `GET /antivirus/health` |
| Plex server | `GET /plex/test-connection` |
| TMDB | `GET /tmdb/test-connection` |
| Gluetun VPN | `GET /gluetun/health` |

`GET /deluge/test-connection` also includes a `vpn` object with Gluetun status (useful when Deluge fails because the VPN tunnel is down).

Gluetun requires `HEALTH_SERVER_ADDRESS=0.0.0.0:9999` and port `9999` in `FIREWALL_INPUT_PORTS` so FastAPI can reach the health server from `fastapi-network`.

Operational routes let domain errors propagate; the global handler converts them to structured JSON.

---

## 10) Anti-patterns to avoid

- Domain importing:
  - `fastapi`, `sqlalchemy`, `httpx`, infrastructure DTOs.
- Application importing concrete infrastructure repositories/clients directly.
- Route handlers containing business logic or direct database query code.
- Duplicating mapping logic in multiple layers.
- Creating new folders by technology first when bounded context placement is clearer.

---

## 11) Quick checklist before adding a new file

- Does this file belong to business core (`domain`) or technical boundary (`adapters`/`infrastructure`)?
- Am I introducing a new contract (port) before implementation?
- Is the use case in `application` independent from concrete technical implementations?
- Are names internal `snake_case` and external aliases handled at boundary schemas?
- Is dependency wiring in `composition`/`factories`, not in domain/application core?

If all are "yes", placement is likely correct.

