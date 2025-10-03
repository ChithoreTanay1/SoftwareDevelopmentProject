"""
Main FastAPI application for Kahoot-style quiz game.
Combines all routes and WebSocket handlers into a single application.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import json


from database import init_db, close_db
from routes import api_router
from websocket_manager import connection_manager
from websocket_handler import websocket_handler, connection_event_handler  # Fixed import
from schemas import WSMessage, APIResponse
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

# Include API routes
app.include_router(api_router)



# ROOT ENDPOINTS


@app.get("/", response_model=APIResponse)
async def root():
    """Health check endpoint."""
    return APIResponse(message="Kahoot-Style Quiz Game API is running")



# WEBSOCKET ENDPOINTS


@app.websocket("/ws/host/{room_code}")
async def websocket_host(websocket: WebSocket, room_code: str):
    """WebSocket endpoint for quiz hosts."""
    # Get host_id from query parameters
    from fastapi import Query
    host_id = Query(...)
    
    await connection_manager.connect_host(websocket, room_code, host_id)
    
    try:
        while True:
            # Receive messages from host
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = WSMessage(**message_data)
            
            # Handle host commands
            await websocket_handler.handle_host_message(room_code, host_id, message)
            
    except WebSocketDisconnect:
        connection_manager.disconnect_host(room_code)
        await connection_event_handler.handle_host_disconnect(room_code, host_id)
        logger.info(f"Host {host_id} disconnected from room {room_code}")
    except Exception as e:
        logger.error(f"Host WebSocket error: {e}")
        connection_manager.disconnect_host(room_code)
        await connection_event_handler.handle_host_disconnect(room_code, host_id)


@app.websocket("/ws/player/{room_code}")
async def websocket_player(websocket: WebSocket, room_code: str):
    """WebSocket endpoint for quiz players."""
    # Get player_id and nickname from query parameters
    from fastapi import Query
    player_id = Query(...)
    nickname = Query(...)
    
    await connection_manager.connect_player(websocket, room_code, player_id, nickname)
    
    try:
        while True:
            # Receive messages from player
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = WSMessage(**message_data)
            
            # Handle player messages
            await websocket_handler.handle_player_message(room_code, player_id, message)
            
    except WebSocketDisconnect:
        nickname = connection_manager.disconnect_player(room_code, player_id)
        await connection_event_handler.handle_player_disconnect(room_code, player_id)
        logger.info(f"Player {nickname} ({player_id}) disconnected from room {room_code}")
                
    except Exception as e:
        logger.error(f"Player WebSocket error: {e}")
        connection_manager.disconnect_player(room_code, player_id)
        await connection_event_handler.handle_player_disconnect(room_code, player_id)



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
        "app:app",  # Fixed module reference
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )