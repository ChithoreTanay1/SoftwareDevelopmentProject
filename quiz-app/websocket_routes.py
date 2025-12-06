"""
WebSocket routes for the Kahoot-style quiz application.
Handles WebSocket connections for hosts and players.
"""

import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from websocket_manager import connection_manager
from websocket_handler import websocket_handler, connection_event_handler
from services import RoomService, PlayerService
from schemas import WSMessage

logger = logging.getLogger(__name__)

# Create WebSocket router
ws_router = APIRouter()


@ws_router.websocket("/ws/{room_code}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_id: str):
    """
    WebSocket endpoint for players to join a room and receive game updates.
    
    Path: /api/v1/ws/{room_code}/{player_id}
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"WebSocket connection attempt: room={room_code}, player={player_id}")
            
            # Validate room exists
            room = await RoomService.get_room_by_code(db, room_code)
            if not room:
                logger.warning(f"WebSocket rejected: room {room_code} not found")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Room not found")
                return
            
            logger.info(f"Room found: {room_code}")
            
            # Validate player exists in room
            player = await PlayerService.get_player_in_room(db, room.id, player_id)
            
            if not player:
                logger.warning(f"Player {player_id} not found in room {room_code}")
                logger.info(f"Attempting to find player by player_id in room {room.id}")
                
                # Debug: List all players in the room
                all_players = await PlayerService.get_players_in_room(db, room.id)
                logger.info(f"Players in room {room_code}: {[(p.player_id, p.nickname) for p in all_players]}")
                
                # For now, accept the connection anyway (DEBUG MODE)
                # TODO: Fix the player ID mismatch issue
                logger.warning(f"WARNING: Accepting player {player_id} despite not finding in DB - DEBUG MODE")
            
            logger.info(f"Player {player_id} accepted for room {room_code}")
            
            # Accept connection
            await connection_manager.connect_player(websocket, room_code, player_id, 
                                                   player.nickname if player else "Unknown")
            
            # Update player connection status if player exists
            if player:
                await PlayerService.update_player_connection(db, player.id, True)
                await db.commit()
            
            # Notify room about new player
            await connection_manager.notify_player_joined(room_code, player_id, 
                                                         player.nickname if player else "Unknown")
            
            try:
                while True:
                    # Receive message from player
                    data = await websocket.receive_json()
                    message = WSMessage(**data)
                    
                    logger.debug(f"Message from {player_id}: {message.type}")
                    
                    # Handle player message
                    await websocket_handler.handle_player_message(room_code, player_id, message)
                    
            except WebSocketDisconnect:
                logger.info(f"Player {player_id} disconnected from room {room_code}")
                connection_manager.disconnect_player(room_code, player_id)
                
                try:
                    await connection_event_handler.handle_player_disconnect(room_code, player_id)
                except asyncio.CancelledError:
                    logger.debug(f"Disconnect handler cancelled for {player_id}")
                except Exception as e:
                    logger.error(f"Error in disconnect handler: {e}")
                
            except asyncio.CancelledError:
                logger.debug(f"WebSocket task cancelled for {player_id}")
                connection_manager.disconnect_player(room_code, player_id)
                
            except Exception as e:
                logger.error(f"WebSocket error for {player_id}: {e}")
                connection_manager.disconnect_player(room_code, player_id)
                
        except Exception as e:
            logger.error(f"Error in WebSocket endpoint: {e}")
            try:
                await websocket.close(code=status.WS_1011_SERVER_ERROR)
            except Exception:
                pass


@ws_router.websocket("/ws/host/{room_code}/{host_id}")
async def websocket_host_endpoint(websocket: WebSocket, room_code: str, host_id: str):
    """
    WebSocket endpoint for game hosts.
    
    Path: /api/v1/ws/host/{room_code}/{host_id}
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"Host WebSocket connection: room={room_code}, host={host_id}")
            
            # Validate room exists and host is authorized
            room = await RoomService.get_room_by_code(db, room_code)
            if not room:
                logger.warning(f"Host connection rejected: room {room_code} not found")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Room not found")
                return
            
            if room.host_id != host_id:
                logger.warning(f"Host connection rejected: unauthorized {host_id} for room {room_code}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
                return
            
            # Accept connection
            await connection_manager.connect_host(websocket, room_code, host_id)
            logger.info(f"Host {host_id} connected to room {room_code}")
            
            try:
                while True:
                    data = await websocket.receive_json()
                    message = WSMessage(**data)
                    
                    logger.debug(f"Host message: {message.type}")
                    await websocket_handler.handle_host_message(room_code, host_id, message)
                    
            except WebSocketDisconnect:
                logger.info(f"Host {host_id} disconnected from room {room_code}")
                connection_manager.disconnect_host(room_code)
                await connection_event_handler.handle_host_disconnect(room_code, host_id)
                
            except Exception as e:
                logger.error(f"Host WebSocket error: {e}")
                connection_manager.disconnect_host(room_code)
                
        except Exception as e:
            logger.error(f"Error in host WebSocket: {e}")
            try:
                await websocket.close(code=status.WS_1011_SERVER_ERROR)
            except Exception:
                pass