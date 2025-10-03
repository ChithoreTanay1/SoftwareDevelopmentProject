"""
WebSocket connection manager for the Kahoot-style quiz application.
Manages active connections and room state.
"""


import logging
import json
from typing import Dict, List, Optional, Tuple
from fastapi import WebSocket
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for hosts and players."""
    
    def __init__(self):
        # Room code -> host WebSocket
        self.host_connections: Dict[str, WebSocket] = {}
        # Room code -> {player_id: (WebSocket, nickname)}
        self.player_connections: Dict[str, Dict[str, Tuple[WebSocket, str]]] = defaultdict(dict)
    
    async def connect_host(self, websocket: WebSocket, room_code: str, host_id: str):
        """Connect a host to a room."""
        await websocket.accept()
        self.host_connections[room_code] = websocket
        logger.info(f"Host {host_id} connected to room {room_code}")
    
    async def connect_player(self, websocket: WebSocket, room_code: str, player_id: str, nickname: str):
        """Connect a player to a room."""
        await websocket.accept()
        self.player_connections[room_code][player_id] = (websocket, nickname)
        logger.info(f"Player {nickname} ({player_id}) connected to room {room_code}")
    
    def disconnect_host(self, room_code: str) -> Optional[str]:
        """Disconnect host from room."""
        if room_code in self.host_connections:
            del self.host_connections[room_code]
            return room_code
        return None
    
    def disconnect_player(self, room_code: str, player_id: str) -> Optional[str]:
        """Disconnect player from room and return nickname."""
        if room_code in self.player_connections and player_id in self.player_connections[room_code]:
            nickname = self.player_connections[room_code][player_id][1]
            del self.player_connections[room_code][player_id]
            return nickname
        return None
    
    async def send_to_host(self, room_code: str, message):
        """Send message to host of a room."""
        if room_code in self.host_connections:
            try:
                await self.host_connections[room_code].send_json(message.dict() if hasattr(message, 'dict') else message)
            except Exception as e:
                logger.error(f"Failed to send to host in room {room_code}: {e}")
    
    async def send_to_player(self, room_code: str, player_id: str, message):
        """Send message to specific player."""
        if (room_code in self.player_connections and
            player_id in self.player_connections[room_code]):
            try:
                websocket, _ = self.player_connections[room_code][player_id]
                await websocket.send_json(message.dict() if hasattr(message, 'dict') else message)
            except Exception as e:
                logger.error(f"Failed to send to player {player_id} in room {room_code}: {e}")
    
    async def broadcast_to_room(self, room_code: str, message):
        """Broadcast message to all players in a room."""
        if room_code in self.player_connections:
            disconnected_players = []
            for player_id, (websocket, nickname) in self.player_connections[room_code].items():
                try:
                    await websocket.send_json(message.dict() if hasattr(message, 'dict') else message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to player {player_id}: {e}")
                    disconnected_players.append(player_id)
            
            # Clean up disconnected players
            for player_id in disconnected_players:
                self.disconnect_player(room_code, player_id)
    
    async def broadcast_to_all(self, room_code: str, message):
        """Broadcast message to all connections in a room (host and players)."""
        await self.send_to_host(room_code, message)
        await self.broadcast_to_room(room_code, message)
    
    def get_room_info(self, room_code: str) -> dict:
        """Get information about connections in a room."""
        host_connected = room_code in self.host_connections
        player_count = len(self.player_connections.get(room_code, {}))
        
        players_info = []
        if room_code in self.player_connections:
            for player_id, (websocket, nickname) in self.player_connections[room_code].items():
                players_info.append({
                    "player_id": player_id,
                    "nickname": nickname,
                    "connected": True
                })
        
        return {
            "host_connected": host_connected,
            "player_count": player_count,
            "players": players_info
        }
    
    def get_active_rooms(self) -> List[str]:
        """Get list of all active rooms."""
        rooms = set(self.host_connections.keys()) | set(self.player_connections.keys())
        return list(rooms)
    
    async def notify_player_joined(self, room_code: str, player_id: str, nickname: str):
        """Notify room about new player joining."""
        player_count = len(self.player_connections.get(room_code, {}))
        
        await self.broadcast_to_all(room_code, {
            "type": "player_joined",
            "data": {
                "player_id": player_id,
                "nickname": nickname,
                "player_count": player_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    async def notify_player_left(self, room_code: str, player_id: str, nickname: str):
        """Notify room about player leaving."""
        player_count = len(self.player_connections.get(room_code, {}))
        
        await self.broadcast_to_all(room_code, {
            "type": "player_left", 
            "data": {
                "player_id": player_id,
                "nickname": nickname,
                "player_count": player_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        })


# Global connection manager instance
connection_manager = ConnectionManager()


def get_connection_stats() -> dict:
    """Get connection statistics."""
    total_players = sum(len(players) for players in connection_manager.player_connections.values())
    
    return {
        "total_rooms": len(connection_manager.host_connections),
        "total_players": total_players,
        "active_rooms": connection_manager.get_active_rooms(),
        "timestamp": datetime.utcnow().isoformat()
    }