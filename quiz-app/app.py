"""
Main FastAPI application for Kahoot-style quiz game.
Combines all routes and WebSocket handlers into a single application.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from database import init_db, close_db
from routes import api_router
from websocket_routes import ws_router
from schemas import APIResponse
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Kahoot-style Quiz Game API")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down")
    await close_db()


# Initialize FastAPI app
app = FastAPI(
    title="Kahoot-Style Quiz Game API",
    description="Real-time multiplayer quiz game backend with WebSocket support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)  # api_router already has prefix="/api/v1"
app.include_router(ws_router, prefix="/api/v1")


# ROOT ENDPOINT

@app.get("/", response_model=APIResponse)
async def root():
    """Health check endpoint."""
    return APIResponse(message="Kahoot-Style Quiz Game API is running")


# ERROR HANDLERS

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": "Endpoint not found", "error_code": "404"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "error_code": "500"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )