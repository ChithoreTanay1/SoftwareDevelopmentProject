

import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import AsyncSessionLocal
from models import Room, Player
from schemas import (
    WSMessage, WSMessageType, PlayerAnswer, QuestionResponse, 
    ChoiceResponse, PlayerAnswer
)
from services import RoomService, PlayerService, ScoreService
from websocket_manager import connection_manager
from exceptions import (
    GameStateException, PlayerNotFoundException, DuplicateAnswerException
)

logger = logging.getLogger(__name__)


class WebSocketMessageHandler:
    """Handles WebSocket messages for the quiz game."""
    
    @staticmethod
    async def handle_host_message(room_code: str, host_id: str, message: WSMessage):
        """Handle messages from game host."""
        async with AsyncSessionLocal() as db:
            try:
                room = await RoomService.get_room_by_code(db, room_code)
                if not room or room.host_id != host_id:
                    logger.warning(f"Unauthorized host message from {host_id} in room {room_code}")
                    return
                
                handler_map = {
                    WSMessageType.START_GAME: WebSocketMessageHandler._handle_start_game,
                    WSMessageType.NEXT_QUESTION: WebSocketMessageHandler._handle_next_question,
                    WSMessageType.END_GAME: WebSocketMessageHandler._handle_end_game
                }
                
                handler = handler_map.get(message.type)
                if handler:
                    await handler(db, room, room_code, message.data)
                else:
                    logger.warning(f"Unknown host message type: {message.type}")
                    
            except Exception as e:
                logger.error(f"Error handling host message: {e}")
                await connection_manager.send_to_host(room_code, WSMessage(
                    type=WSMessageType.ERROR,
                    data={"message": "Failed to process host message"}
                ))
    
    @staticmethod
    async def handle_player_message(room_code: str, player_id: str, message: WSMessage):
        """Handle messages from players."""
        async with AsyncSessionLocal() as db:
            try:
                room = await RoomService.get_room_by_code(db, room_code)
                if not room:
                    logger.warning(f"Message from player {player_id} in non-existent room {room_code}")
                    return
                
                player = await PlayerService.get_player_in_room(db, room.id, player_id)
                if not player:
                    logger.warning(f"Message from unknown player {player_id} in room {room_code}")
                    return
                
                handler_map = {
                    WSMessageType.ANSWER_SUBMITTED: WebSocketMessageHandler._handle_player_answer
                }
                
                handler = handler_map.get(message.type)
                if handler:
                    await handler(db, room, player, room_code, message.data)
                else:
                    logger.warning(f"Unknown player message type: {message.type}")
                    
            except Exception as e:
                logger.error(f"Error handling player message: {e}")
                await connection_manager.send_to_player(room_code, player_id, WSMessage(
                    type=WSMessageType.ERROR,
                    data={"message": "Failed to process player message"}
                ))
    
    @staticmethod
    async def _handle_start_game(db: AsyncSession, room: Room, room_code: str, data: dict):
        """Handle game start from host."""
        if room.status != "waiting":
            raise GameStateException("start game", room.status, "waiting")
        
        success = await RoomService.start_game(db, room.id)
        if not success:
            logger.error(f"Failed to start game in room {room_code}")
            return
        
        # Get updated room with first question
        updated_room = await RoomService.get_room(db, room.id)
        first_question = updated_room.quiz.questions[0]
        
        # Prepare question data for players (without correct answers)
        question_data = QuestionResponse(
            id=first_question.id,
            question_text=first_question.question_text,
            question_type=first_question.question_type,
            time_limit=first_question.time_limit,
            points=first_question.points,
            order_index=first_question.order_index,
            choices=[
                ChoiceResponse(
                    id=choice.id,
                    choice_text=choice.choice_text,
                    order_index=choice.order_index
                )
                for choice in first_question.choices
            ]
        )
        
        # Broadcast game start to all connections
        await connection_manager.broadcast_to_all(room_code, WSMessage(
            type=WSMessageType.QUESTION_STARTED,
            data={
                "question": question_data.dict(),
                "question_number": 1,
                "total_questions": len(updated_room.quiz.questions)
            }
        ))
        
        logger.info(f"Game started in room {room_code}")
    
    @staticmethod
    async def _handle_next_question(db: AsyncSession, room: Room, room_code: str, data: dict):
        """Handle moving to next question."""
        if room.status != "active":
            raise GameStateException("advance question", room.status, "active")
        
        # Get current question results first
        current_question = room.quiz.questions[room.current_question]
        question_results = await ScoreService.get_question_results(db, room.id, current_question.id)
        
        # Broadcast question results to all players
        await connection_manager.broadcast_to_all(room_code, WSMessage(
            type=WSMessageType.QUESTION_ENDED,
            data={
                "question_id": current_question.id,
                "results": question_results,
                "correct_choice": next(
                    (choice.id for choice in current_question.choices if choice.is_correct), 
                    None
                )
            }
        ))
        
        # Move to next question
        success = await RoomService.next_question(db, room.id)
        if not success:
            logger.error(f"Failed to advance question in room {room_code}")
            return
        
        # Get updated room
        updated_room = await RoomService.get_room(db, room.id)
        
        if updated_room.status == "completed":
            # Game ended
            await WebSocketMessageHandler._handle_game_completed(db, updated_room, room_code)
        else:
            # Send next question
            next_question = updated_room.quiz.questions[updated_room.current_question]
            question_data = QuestionResponse(
                id=next_question.id,
                question_text=next_question.question_text,
                question_type=next_question.question_type,
                time_limit=next_question.time_limit,
                points=next_question.points,
                order_index=next_question.order_index,
                choices=[
                    ChoiceResponse(
                        id=choice.id,
                        choice_text=choice.choice_text,
                        order_index=choice.order_index
                    )
                    for choice in next_question.choices
                ]
            )
            
            await connection_manager.broadcast_to_all(room_code, WSMessage(
                type=WSMessageType.QUESTION_STARTED,
                data={
                    "question": question_data.dict(),
                    "question_number": updated_room.current_question + 1,
                    "total_questions": len(updated_room.quiz.questions)
                }
            ))
            
        logger.info(f"Advanced to next question in room {room_code}")
    
    @staticmethod
    async def _handle_end_game(db: AsyncSession, room: Room, room_code: str, data: dict):
        """Handle manual game end from host."""
        if room.status not in ["active", "waiting"]:
            raise GameStateException("end game", room.status, "active or waiting")
        
        await RoomService.end_game(db, room.id)
        await WebSocketMessageHandler._handle_game_completed(db, room, room_code)
        
        logger.info(f"Game manually ended in room {room_code}")
    
    @staticmethod
    async def _handle_player_answer(db: AsyncSession, room: Room, player: Player, 
                                  room_code: str, data: dict):
        """Handle player answer submission."""
        if room.status != "active":
            await connection_manager.send_to_player(room_code, player.player_id, WSMessage(
                type=WSMessageType.ERROR,
                data={"message": "Game is not active"}
            ))
            return
        
        try:
            answer = PlayerAnswer(**data)
            
            # Validate answer is for current question
            current_question = room.quiz.questions[room.current_question]
            if current_question.id != answer.question_id:
                await connection_manager.send_to_player(room_code, player.player_id, WSMessage(
                    type=WSMessageType.ERROR,
                    data={"message": "Invalid question for current state"}
                ))
                return
            
            # Submit answer and get result
            result = await ScoreService.submit_answer(db, room.id, player.id, answer)
            
            if result:
                # Send answer result to player
                await connection_manager.send_to_player(room_code, player.player_id, WSMessage(
                    type=WSMessageType.ANSWER_SUBMITTED,
                    data=result
                ))
                
                # Update leaderboard
                leaderboard = await ScoreService.get_leaderboard(db, room.id)
                await connection_manager.broadcast_to_all(room_code, WSMessage(
                    type=WSMessageType.LEADERBOARD_UPDATE,
                    data={"leaderboard": leaderboard.dict()}
                ))
                
                # Notify host about answer submission
                await connection_manager.send_to_host(room_code, WSMessage(
                    type=WSMessageType.ANSWER_SUBMITTED,
                    data={
                        "player_id": player.player_id,
                        "player_nickname": player.nickname,
                        "question_id": answer.question_id,
                        "is_correct": result["is_correct"],
                        "points_earned": result["points_earned"]
                    }
                ))
                
            else:
                # Answer submission failed (likely duplicate)
                await connection_manager.send_to_player(room_code, player.player_id, WSMessage(
                    type=WSMessageType.ERROR,
                    data={"message": "Answer could not be submitted"}
                ))
                
        except Exception as e:
            logger.error(f"Error handling player answer: {e}")
            await connection_manager.send_to_player(room_code, player.player_id, WSMessage(
                type=WSMessageType.ERROR,
                data={"message": "Failed to process answer"}
            ))
    
    @staticmethod
    async def _handle_game_completed(db: AsyncSession, room: Room, room_code: str):
        """Handle game completion."""
        # Get final leaderboard
        leaderboard = await ScoreService.get_leaderboard(db, room.id)
        
        # Calculate game statistics
        total_questions = len(room.quiz.questions)
        total_players = len(room.players)
        
        game_stats = {
            "total_questions": total_questions,
            "total_players": total_players,
            "quiz_title": room.quiz.title,
            "game_duration": None  # Could calculate from start/end times
        }
        
        # Broadcast game end
        await connection_manager.broadcast_to_all(room_code, WSMessage(
            type=WSMessageType.GAME_ENDED,
            data={
                "final_leaderboard": leaderboard.dict(),
                "game_stats": game_stats,
                "message": "Game completed! Thanks for playing!"
            }
        ))
        
        logger.info(f"Game completed in room {room_code} with {total_players} players")


class ConnectionEventHandler:
    """Handles WebSocket connection events."""
    
    @staticmethod
    async def handle_player_disconnect(room_code: str, player_id: str):
        """Handle player disconnection."""
        async with AsyncSessionLocal() as db:
            try:
                room = await RoomService.get_room_by_code(db, room_code)
                if room:
                    player = await PlayerService.get_player_in_room(db, room.id, player_id)
                    if player:
                        await PlayerService.update_player_connection(db, player.id, False)
                        
                        # Notify room about disconnection
                        await connection_manager.notify_player_left(
                            room_code, player_id, player.nickname
                        )
                        
                        logger.info(f"Player {player.nickname} disconnected from room {room_code}")
                        
            except Exception as e:
                logger.error(f"Error handling player disconnect: {e}")
    
    @staticmethod
    async def handle_host_disconnect(room_code: str, host_id: str):
        """Handle host disconnection."""
        async with AsyncSessionLocal() as db:
            try:
                room = await RoomService.get_room_by_code(db, room_code)
                if room and room.host_id == host_id:
                    # Notify all players that host disconnected
                    await connection_manager.broadcast_to_room(room_code, WSMessage(
                        type=WSMessageType.ERROR,
                        data={
                            "message": "Host disconnected. Game may be paused.",
                            "error_type": "host_disconnect"
                        }
                    ))
                    
                    logger.warning(f"Host {host_id} disconnected from room {room_code}")
                    
            except Exception as e:
                logger.error(f"Error handling host disconnect: {e}")


# Global handler instance
websocket_handler = WebSocketMessageHandler()
connection_event_handler = ConnectionEventHandler()
        
