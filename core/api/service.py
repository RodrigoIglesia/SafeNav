"""
SafeNav Core - API Layer Service
--------------------------------
Initializes the FastAPI service and registers HTTP controllers
for SafeNav Core capabilities.
"""
# TODO: API must send the received city to Routing Engine.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Controllers
from api.controllers.route_controller import router as route_router

# Services
from routing_engine.service import RoutingEngine
from context_analyzer.service import ContextAnalyzer
from data_management.service import DataManagement
from interfaces.i_routing_service import IRoutingService
from interfaces.i_context_service import IContextService

def create_api_service() -> FastAPI:
    """
    Create and configure the FastAPI application for the SafeNav Core API.
    """

    app = FastAPI(
        title="SafeNav Core API",
        version="1.0",
        description="HTTP layer for SafeNav Core functionalities.",
        contact={
            "name": "Rodrigo de la Iglesia Sánchez",
            "url": "https://github.com/safenav",
        },
    )

    # =======================================================
    # CORS configuration (development setup)
    # =======================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # =======================================================
    # Dependency injection — internal services
    # =======================================================

    # Shared DataManagement instance
    data_management = DataManagement()

    # Call services interfaces
    routing_service: IRoutingService = RoutingEngine(data_management)
    context_service: IContextService = ContextAnalyzer(data_management)

    # Register services in application state
    app.state.routing_service = routing_service
    app.state.context_service = context_service

    # =======================================================
    # Register routers (separated by responsibility)
    # =======================================================
    app.include_router(route_router)

    # =======================================================
    # Health check endpoint
    # =======================================================
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "ok",
            "service": "SafeNav Core API"
        }

    return app


# ASGI entry point
app = create_api_service()
