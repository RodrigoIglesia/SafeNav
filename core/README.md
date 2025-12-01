Este es el repositorio del subsistema CORE de SafeNav.

## Configuración técnica
- Lenguaje de programación: Python3.12
- Entorno de ejecución
    - Docker
    - Python 3.12-slim (Ubuntu)
- Frameworks
    - API: FastAPI


The repository is composed of

safenav/
├── api/                     # API Layer - implements I_HTTP_Routes
│   ├── service.py           # Main API service (entry point)
│   └── ...                  # HTTP routes, controllers, serializers
│
├── context_analyzer/        # Context Analyzer (CA) - evaluates comfort/safety
│   ├── service.py           # Implements I_ContextService
│   ├── scorers/             # Scoring algorithms (shade, temperature, etc.)
│   ├── fusion/              # Data fusion logic
│   └── models.py            # Context-related models
│
├── routing_engine/          # Routing Engine (RE) - generates route candidates
│   ├── service.py           # Implements I_RoutingService
│   ├── algorithms/          # Pathfinding and optimization logic
│   ├── models.py            # Route and graph models
│   └── utils.py             # Helpers and metrics
│
├── data_management/         # Data Management (DM) - handles external data
│   ├── service.py           # Implements I_DataAccess
│   ├── datasources/         # Map, Meteo, and OpenData API clients
│   ├── cache/               # Local data cache or persistence layer
│   └── models.py            # Data schemas and parsing logic
│
├── interfaces/              # Interface contracts (system and external)
│   ├── i_http_routes.py
│   ├── i_routing_service.py
│   ├── i_context_service.py
│   ├── i_data_access.py
│   ├── i_map_data_access.py
│   ├── i_meteo_data_access.py
│   └── i_open_data_access.py
│
├── domain/                  # Domain and business concepts
│   ├── dto/                 # Data Transfer Objects (DTOs)
│   │   ├── route_request.py
│   │   ├── route_response.py
│   │   ├── route_candidates.py
│   │   └── route_scores.py
│   │
│   └── entities/            # Core domain entities
│       ├── map_data.py
│       ├── weather_data.py
│       ├── urban_data.py
│       └── route.py
│
├── common/                  # Shared utilities and configuration
│   ├── config.py
│   ├── logger.py
│   └── utils.py
│
└── main.py                  # Composition root / application entry point
