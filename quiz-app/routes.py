"""
API routes for the Kahoot-style quiz application.
RESTful endpoints for quiz and room management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from schemas import (
    APIResponse, QuizCreate, QuizResponse, QuizSummary, 
    RoomCreate, RoomResponse, RoomJoin, PlayerResponse,
    LeaderboardResponse
)
from services import QuizService, RoomService, PlayerService, ScoreService
from websocket_manager import connection_manager, get_connection_stats
from exceptions import (
    QuizGameException, get_http_status_code, format_error_response
)
from utils import generate_unique_id

logger = logging.getLogger(__name__)

# Create API router
api_router = APIRouter(prefix="/api/v1")


# ============================================================================
# ERROR HANDLER
# ============================================================================

async def handle_service_exceptions(func, *args, **kwargs):
    """Handle service layer exceptions and convert to HTTP responses."""
    try:
        return await func(*args, **kwargs)
    except QuizGameException as e:
        status_code = get_http_status_code(e)
        error_response = format_error_response(e)
        raise HTTPException(status_code=status_code, detail=error_response)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Internal server error", "error_code": "INTERNAL_ERROR"}
        )


# ============================================================================
# QUIZ ENDPOINTS
# ============================================================================

@api_router.post("/quizzes", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(quiz_data: QuizCreate, db: AsyncSession = Depends(get_db)):
    """Create a new quiz with questions."""
    quiz = await handle_service_exceptions(
        QuizService.create_quiz, db, quiz_data
    )
    
    return APIResponse(
        message="Quiz created successfully",
        data={"quiz_id": quiz.id, "title": quiz.title}
    )


@api_router.get("/quizzes/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: str, db: AsyncSession = Depends(get_db)):
    """Get quiz by ID with all questions and choices."""
    quiz = await handle_service_exceptions(
        QuizService.get_quiz, db, quiz_id
    )

    return quiz


@api_router.get("/quizzes", response_model=List[QuizSummary])
async def list_quizzes(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """List active quizzes."""
    quizzes = await handle_service_exceptions(
        QuizService.list_active_quizzes, db, limit
    )
    
    # Convert to summary format
    quiz_summaries = []
    for quiz in quizzes:
        summary = QuizSummary(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            created_by=quiz.created_by,
            created_at=quiz.created_at,
            is_active=quiz.is_active,
            question_count=len(quiz.questions) if hasattr(quiz, 'questions') else 0
        )
        quiz_summaries.append(summary)
    
    return quiz_summaries


# ============================================================================
# ROOM ENDPOINTS
# ============================================================================

@api_router.post("/rooms", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_room(room_data: RoomCreate, db: AsyncSession = Depends(get_db)):
    """Create a new game room."""
    host_id = generate_unique_id()  # In real app, get from authentication
    
    room = await handle_service_exceptions(
        RoomService.create_room, db, room_data, host_id
    )
    
    return APIResponse(
        message="Room created successfully",
        data={
            "room_id": room.id,
            "room_code": room.room_code,
            "host_id": host_id
        }
    )


@api_router.get("/rooms/{room_code}", response_model=RoomResponse)
async def get_room_info(room_code: str, db: AsyncSession = Depends(get_db)):
    """Get room information by code."""
    room = await handle_service_exceptions(
        RoomService.get_room_by_code, db, room_code
    )
    
    # Add connection info
    connection_info = connection_manager.get_room_info(room_code)
    
    return RoomResponse(
        id=room.id,
        room_code=room.room_code,
        quiz_id=room.quiz_id,
        host_id=room.host_id,
        host_name=room.host_name,
        status=room.status,
        current_question=room.current_question,
        created_at=room.created_at,
        started_at=room.started_at,
        ended_at=room.ended_at,
        max_players=room.max_players,
        player_count=len(room.players)
    )


@api_router.post("/rooms/{room_code}/join", response_model=APIResponse)
async def join_room(room_code: str, join_data: RoomJoin, db: AsyncSession = Depends(get_db)):
    """Join a room as a player."""
    player_id = generate_unique_id()  # In real app, get from authentication
    
    player = await handle_service_exceptions(
        PlayerService.join_room, db, room_code, player_id, join_data.nickname
    )
    
    return APIResponse(
        message="Joined room successfully",
        data={
            "player_id": player_id,
            "internal_player_id": player.id,
            "nickname": player.nickname
        }
    )


@api_router.get("/rooms/{room_code}/players", response_model=List[PlayerResponse])
async def get_room_players(room_code: str, db: AsyncSession = Depends(get_db)):
    """Get all players in a room."""
    room = await handle_service_exceptions(
        RoomService.get_room_by_code, db, room_code
    )
    
    return [PlayerResponse(
        id=player.id,
        player_id=player.player_id,
        nickname=player.nickname,
        joined_at=player.joined_at,
        is_connected=player.is_connected,
        total_score=player.total_score
    ) for player in room.players]


@api_router.get("/rooms/{room_code}/leaderboard", response_model=LeaderboardResponse)
async def get_room_leaderboard(room_code: str, db: AsyncSession = Depends(get_db)):
    """Get current leaderboard for a room."""
    room = await handle_service_exceptions(
        RoomService.get_room_by_code, db, room_code
    )
    
    leaderboard = await handle_service_exceptions(
        ScoreService.get_leaderboard, db, room.id
    )
    
    return leaderboard


# ============================================================================
# GAME CONTROL ENDPOINTS (for host)
# ============================================================================

@api_router.post("/rooms/{room_code}/start", response_model=APIResponse)
async def start_game(room_code: str, db: AsyncSession = Depends(get_db)):
    """Start the game in a room."""
    room = await handle_service_exceptions(
        RoomService.get_room_by_code, db, room_code
    )
    
    success = await handle_service_exceptions(
        RoomService.start_game, db, room.id
    )
    
    if success:
        # Get updated room with quiz data
        updated_room = await handle_service_exceptions(
            RoomService.get_room_by_code, db, room_code
        )
        
        # Prepare quiz data
        quiz_data = {
            "id": updated_room.quiz.id,
            "title": updated_room.quiz.title,
            "description": updated_room.quiz.description,
            "questions": []
        }
        
        for q in updated_room.quiz.questions:
            question_data = {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "time_limit": q.time_limit,
                "points": q.points,
                "order_index": q.order_index,
                "answers": []
            }
            
            for i, choice in enumerate(q.choices):
                question_data["answers"].append({
                    "id": choice.id,
                    "text": choice.choice_text,
                    "is_correct": choice.is_correct
                })
                
                if choice.is_correct:
                    question_data["correctAnswer"] = i
            
            quiz_data["questions"].append(question_data)
        
        # Send WebSocket message
        game_started_msg = {
            "type": "game_started",
            "data": {
                "quiz": quiz_data,
                "currentQuestionIndex": 0,
                "score": 0
            }
        }
        
        print("BROADCAST game_started", flush=True)
        await connection_manager.broadcast_to_all(room_code, game_started_msg)
        
        # Send first question
        first_question = updated_room.quiz.questions[0]
        question_response = {
            "id": first_question.id,
            "question_text": first_question.question_text,
            "question_type": first_question.question_type,
            "time_limit": first_question.time_limit,
            "points": first_question.points,
            "order_index": first_question.order_index,
            "choices": [
                {
                    "id": choice.id,
                    "choice_text": choice.choice_text,
                    "order_index": choice.order_index
                }
                for choice in first_question.choices
            ]
        }
        
        question_msg = {
            "type": "question",
            "data": {
                "question": question_response,
                "questionIndex": 0,
                "timeLimit": first_question.time_limit
            }
        }
        
        print("BROADCAST question", flush=True)
        await connection_manager.broadcast_to_all(room_code, question_msg)
        
        return APIResponse(message="Game started successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Failed to start game", "error_code": "GAME_START_FAILED"}
        )


@api_router.post("/rooms/{room_code}/next-question", response_model=APIResponse)
async def next_question(room_code: str, db: AsyncSession = Depends(get_db)):
    """Move to the next question."""
    room = await handle_service_exceptions(
        RoomService.get_room_by_code, db, room_code
    )
    
    success = await handle_service_exceptions(
        RoomService.next_question, db, room.id
    )
    
    if success:
        return APIResponse(message="Advanced to next question")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Failed to advance question", "error_code": "QUESTION_ADVANCE_FAILED"}
        )


@api_router.post("/rooms/{room_code}/end", response_model=APIResponse)
async def end_game(room_code: str, db: AsyncSession = Depends(get_db)):
    """End the game manually."""
    room = await handle_service_exceptions(
        RoomService.get_room_by_code, db, room_code
    )
    
    success = await handle_service_exceptions(
        RoomService.end_game, db, room.id
    )
    
    if success:
        return APIResponse(message="Game ended successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Failed to end game", "error_code": "GAME_END_FAILED"}
        )


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@api_router.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint."""
    return APIResponse(message="Service is healthy")


@api_router.get("/stats", response_model=APIResponse)
async def get_system_stats():
    """Get system statistics."""
    stats = get_connection_stats()
    
    return APIResponse(
        message="System statistics",
        data=stats
    )


@api_router.get("/rooms", response_model=APIResponse)
async def list_active_rooms():
    """List all active rooms with connection info."""
    rooms = connection_manager.get_active_rooms()
    
    room_data = {}
    for room_code in rooms:
        room_info = connection_manager.get_room_info(room_code)
        room_data[room_code] = room_info
    
    return APIResponse(
        message="Active rooms",
        data={
            "total_rooms": len(rooms),
            "rooms": room_data
        }
    )


# ============================================================================
# DEVELOPMENT/DEBUG ENDPOINTS (remove in production)
# ============================================================================

@api_router.post("/dev/create-sample-quiz", response_model=APIResponse)
async def create_sample_quiz(db: AsyncSession = Depends(get_db)):
    """Create a sample quiz for testing (development only)."""
    from schemas import QuestionCreate, ChoiceCreate
    
    sample_quiz = QuizCreate(
        title="Development Test Quiz",
        description="A simple test quiz for development",
        created_by="dev_system",
        questions=[
            QuestionCreate(
                question_text="What is 2 + 2?",
                question_type="multiple_choice",
                time_limit=30,
                points=100,
                order_index=0,
                choices=[
                    ChoiceCreate(choice_text="3", is_correct=False, order_index=0),
                    ChoiceCreate(choice_text="4", is_correct=True, order_index=1),
                    ChoiceCreate(choice_text="5", is_correct=False, order_index=2),
                    ChoiceCreate(choice_text="6", is_correct=False, order_index=3)
                ]
            ),
            QuestionCreate(
                question_text="What color is the sky?",
                question_type="multiple_choice", 
                time_limit=20,
                points=100,
                order_index=1,
                choices=[
                    ChoiceCreate(choice_text="Red", is_correct=False, order_index=0),
                    ChoiceCreate(choice_text="Blue", is_correct=True, order_index=1),
                    ChoiceCreate(choice_text="Green", is_correct=False, order_index=2),
                    ChoiceCreate(choice_text="Yellow", is_correct=False, order_index=3)
                ]
            )
        ]
    )
    
    quiz = await handle_service_exceptions(
        QuizService.create_quiz, db, sample_quiz
    )
    
    return APIResponse(
        message="Sample quiz created",
        data={"quiz_id": quiz.id, "title": quiz.title}
    )