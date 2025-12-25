"""
SafeNav Core - API Layer Service
--------------------------------
This module initialized the API service using FastAPI, which serves as the entry point
for the SafeNav Core. It is responsible for registering the controllers (routers) and
exposing the defined HTTP endpoints for route operations.
"""

from fastapi import FastAPI
from api.controllers.route_controller import router
from routing_engine.service import RoutingEngine
from interfaces.i_routing_service import IRoutingService

def create_api_service() -> FastAPI:
    """
    Create and configure the FastAPI application for the SafeNav Core API.

    Returns:
        FastAPI: App configured instance
    """
    app = FastAPI(
        title="SafeNav Core API",
        version="1.0",
        description="HTTP layer for SafeNav Core functionalities.",
        contact={
            "name": "Rodrigo de la Iglesia Sáncehz",
            "url": "https://github.com/safenav",
        },
    )
    # =======================================================
    # Dependency injection — register internal service layers
    # =======================================================
    routing_service: IRoutingService = RoutingEngine()
    app.state.routing_service = routing_service

    # Register routers
    app.include_router(router)

    # Health check endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        """
        Verify the health status of the API service.
        """
        return {"status": "ok", "service": "SafeNav Core API"}

    return app


# Main application instance (used by uvicorn ASGI server)
app = create_api_service()
