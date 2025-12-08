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
from schemas import WSMessage, WSMessageType

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/ws/{room_code}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_id: str):
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"WebSocket connection attempt: room={room_code}, player={player_id}")

            # Validate room exists
            room = await RoomService.get_room_by_code(db, room_code)
            if not room:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Room not found")
                return

            # Validate player exists in room
            player = await PlayerService.get_player_in_room(db, room.id, player_id)
            if not player:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Player not found")
                return

            # Accept connection
            await connection_manager.connect_player(websocket, room_code, player_id, player.nickname)

            # Update connection status
            await PlayerService.update_player_connection(db, player.id, True)
            await db.commit()

            # Send current game state if reconnecting
            if room.status == "active":
                current_question = room.quiz.questions[room.current_question]
                await connection_manager.send_to_player(
                    room_code, player_id, WSMessage(
                        type=WSMessageType.QUESTION_STARTED,
                        data={
                            "question": {
                                "id": current_question.id,
                                "question_text": current_question.question_text,
                                "question_type": current_question.question_type,
                                "time_limit": current_question.time_limit,
                                "points": current_question.points,
                                "order_index": current_question.order_index,
                                "choices": [
                                    {"id": c.id, "choice_text": c.choice_text, "order_index": c.order_index}
                                    for c in current_question.choices
                                ]
                            },
                            "question_number": room.current_question + 1,
                            "total_questions": len(room.quiz.questions)
                        }
                    )
                )
            elif room.status == "completed":
    # Broadcast GAME_COMPLETED so reconnecting players move to results screen
                await connection_manager.broadcast(
                    room_code,
                    WSMessage(
                        type=WSMessageType.GAME_COMPLETED,
                        data={"room_code": room_code}
                )
            )
            

            # Notify room about joining
            await connection_manager.notify_player_joined(room_code, player_id, player.nickname)

            while True:
                data = await websocket.receive_json()
                message = WSMessage(**data)
                await websocket_handler.handle_player_message(room_code, player_id, message)

        except WebSocketDisconnect:
            connection_manager.disconnect_player(room_code, player_id)
            await connection_event_handler.handle_player_disconnect(room_code, player_id)

        except asyncio.CancelledError:
            connection_manager.disconnect_player(room_code, player_id)

        except Exception as e:
            logger.error(f"WebSocket error for player {player_id}: {e}")
            connection_manager.disconnect_player(room_code, player_id)
            try:
                await websocket.close(code=status.WS_1011_SERVER_ERROR)
            except Exception:
                pass


@ws_router.websocket("/ws/host/{room_code}/{host_id}")
async def websocket_host_endpoint(websocket: WebSocket, room_code: str, host_id: str):
    async with AsyncSessionLocal() as db:
        try:
            room = await RoomService.get_room_by_code(db, room_code)
            if not room or room.host_id != host_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized or room not found")
                return

            await connection_manager.connect_host(websocket, room_code, host_id)

            while True:
                data = await websocket.receive_json()
                message = WSMessage(**data)
                await websocket_handler.handle_host_message(room_code, host_id, message)

        except WebSocketDisconnect:
            connection_manager.disconnect_host(room_code)
            await connection_event_handler.handle_host_disconnect(room_code, host_id)

        except Exception as e:
            logger.error(f"Host WebSocket error: {e}")
            connection_manager.disconnect_host(room_code)
            try:
                await websocket.close(code=status.WS_1011_SERVER_ERROR)
            except Exception:
                pass
