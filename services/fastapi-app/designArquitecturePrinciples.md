# Design Arquitecture Principles (Hexagonal Architecture)

- Clean Architecture (Hexagonal Architecture)
- Dependency Injection
- Separation of Concerns (SoC)
- Single Responsibility Principle (SRP)
- Open/Closed Principle (OCP)
- Liskov Substitution Principle (LSP)
- Interface Segregation Principle (ISP)
- Composition Over Inheritance (COI)
- Separation of Concerns (SoC)
- Don't Repeat Yourself (DRY)
- Keep It Simple Stupid (KISS)
- You Aren't Gonna Need It (YAGNI)
- Principle of Least Surprise (PoLS)
- Principle of Least Knowledge (PoLK)
- Principle of Least Privilege (PoLP)
- Principle of Least Authority (PoLA)
- Principle of Least Awareness (PoLA)

```
--------------------------------
# FastAPI App Architecture
--------------------------------
fastapi-app/
├── domain/                             # PURE BUSINESS (NO IO)
│   ├── models/                         # Domain entities & value objects
│   │   ├── plex_user.py
│   │   └── media_item.py
│   │
│   ├── ports/                          # Contracts (Protocols)
│   │   ├── repositories/
│   │   │   └── plex/
│   │   │       └── plex_user_repository.py
│   │   │
│   │   └── external/
│   │       ├── plex/
│   │       │   ├── plex_user_library.py
│   │       │   └── plex_server_library.py
│   │       └── deluge/
│   │           └── deluge_torrent_provider.py
│   │
│   ├── services/                       # (RARE) pure domain logic
│   │   └── plex_access_policy.py
│   │
│   └── errors/                         # Domain-level errors
│       └── plex_errors.py
│
├── application/                        # ORCHESTRATION
│   ├── plex/                           # BOUNDED CONTEXT FIRST
│   │   ├── use_cases/                  # Commands / workflows
│   │   │   └── sync_media_if_exists.py
│   │   │
│   │   ├── queries/                    # Read-only operations
│   │   │   └── is_item_in_library.py
│   │   │
│   │   ├── commands/                   # Input DTOs
│   │   │   └── plex_media_commands.py
│   │   │
│   │   └── errors.py
│   │
│   └── deluge/
│       ├── use_cases/
│       └── queries/
│
├── adapters/                           # BOUNDARY TRANSLATORS
│   ├── http/                           # DELIVERY ADAPTER (FastAPI)
│   │   ├── routes/
│   │   │   ├── plex/
│   │   │   │   ├── media.py
│   │   │   │   └── users.py
│   │   │   └── deluge/
│   │   │       └── torrents.py
│   │   │
│   │   ├── schemas/                    # HTTP request/response
│   │   │   ├── plex/
│   │   │   │   └── media.py
│   │   │   └── deluge/
│   │   │       └── torrent.py
│   │   │
│   │   └── security/                   # HTTP SECURITY (API KEY)
│   │       ├── api_key.py
│   │       └── dependencies.py
│   │
│   └── external/                       # EXTERNAL SYSTEM ADAPTERS
│       ├── plex/
│       │   ├── server_library_adapter.py
│       │   ├── user_library_adapter.py
│       │   └── mapper.py
│       │
│       └── deluge/
│           ├── torrent_adapter.py
│           └── mapper.py
│
├── infrastructure/                     # TECHNICAL IMPLEMENTATIONS
│   ├── persistence/                    # DATABASE (Postgres)
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   └── plex_user_orm.py
│   │   └── repositories/
│   │       └── sqlalchemy_plex_user_repository.py
│   │
│   └── external_apis/                  # RAW CLIENTS + DTOs
│       ├── plex/
│       │   ├── client.py
│       │   ├── schemas.py              # External API schemas (DTOs)
│       │   └── config.py
│       │
│       └── deluge/
│           ├── client.py
│           └── schemas.py
│
├── factories/                          # COMPOSITION ROOT
│   ├── plex_media_factory.py
│   ├── plex_user_factory.py
│   └── deluge_factory.py
│
├── core/                               # CROSS-CUTTING (NO HTTP)
│   ├── config.py
│   ├── logging.py
│   └── constants.py
│
├── main.py
└── tests/
