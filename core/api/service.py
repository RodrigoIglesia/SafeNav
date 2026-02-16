"""
SafeNav Core - API Layer Service
--------------------------------
This module initialized the API service using FastAPI, which serves as the entry point
for the SafeNav Core. It is responsible for registering the controllers (routers) and
exposing the defined HTTP endpoints for route operations.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.controllers.route_controller import router
from routing_engine.service import RoutingEngine
from interfaces.i_routing_service import IRoutingService
from data_management.service import DataManagement
from interfaces.i_map_view import I_MapView

def create_api_service() -> FastAPI:
    """
    Create and configure the FastAPI application for the SafeNav Core API.

    Returns:
        FastAPI: Configured application instance.
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
    # Dependency injection — register internal service layers
    # =======================================================

    # Single shared DataManagement instance
    data_management = DataManagement()

    # Inject DataManagement into RoutingEngine
    routing_service: IRoutingService = RoutingEngine(data_management)

    # Register services in app state
    app.state.routing_service = routing_service
    app.state.map_view_service = data_management

    # =======================================================
    # Register routers
    # =======================================================
    app.include_router(router)

    # =======================================================
    # Health check endpoint
    # =======================================================
    @app.get("/health", tags=["System"])
    async def health_check():
        """
        Verify the health status of the API service.
        """
        return {
            "status": "ok",
            "service": "SafeNav Core API"
        }

    return app


# Main application instance (used by uvicorn ASGI server)
app = create_api_service()
