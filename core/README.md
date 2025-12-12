Este es el repositorio del subsistema CORE de SafeNav.

## Configuración técnica
- Lenguaje de programación: Python3.12
- Entorno de ejecución
    - Docker
    - Python 3.12-slim (Ubuntu)
- Frameworks
    - API Layer: FastAPI - usando Pydantic para validación automática de datos usando Uvicorn como motor de la API

## Metodología de implementación
1. Definición de las DTOs: Estas son las estructuras de datos que intercambiará el sistema. Por ejemplo, map_data es la estructura de datos que devuelve DM al obtener datos de mapas del servicio externo.

2. Definición de interfaces: una vez definidas las interfaces lógicas por diseño. Por cada interfaz se define un fichero que implementa los contratos de dicha interfaz (por ejemplo, RouteRequest, implementado por la API). Las interfaces son los contratos que definen cómo se comunicarán los módulos internos y externos entre sí. La implementación de las interfaces sigue el diseño lógico del sistema. Esta implementación formal permite:
    - Los módulos no dependan directamente entre sí (solo de contratos).
    - Capacidad de reemplazar implementaciones (por ejemplo, cambiar un proveedor de datos) sin romper el sistema.
    - Capacidad de  mockear fácilmente los módulos en los tests.

Para implementar las interfaces se usa la librería Typing Protocol (+Python3.8).


## Estructura de Repositorio

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
