"""
Business logic services for the Kahoot-style quiz application.
Contains the core game logic and data operations.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any

from models import Room, Quiz, Question, Choice, Player, Answer, Score
from schemas import (
    RoomCreate, QuizCreate, PlayerAnswer, AnswerResponse,
    PlayerScore, LeaderboardResponse, QuestionStats
)
from exceptions import (
    RoomNotFoundException, QuizNotFoundException, PlayerNotFoundException,
    QuestionNotFoundException, GameStateException, RoomFullException,
    DuplicatePlayerException, DuplicateAnswerException, InvalidAnswerException
)
from utils import generate_room_code, generate_unique_id, calculate_score, sanitize_nickname
from config import settings

logger = logging.getLogger(__name__)


class QuizService:
    """Service for quiz management operations."""
    
    @staticmethod
    async def create_quiz(db: AsyncSession, quiz_data: QuizCreate) -> Quiz:
        """Create a new quiz with questions and choices."""
        try:
            # Create quiz
            quiz = Quiz(
                id=generate_unique_id(),
                title=quiz_data.title,
                description=quiz_data.description,
                created_by=quiz_data.created_by,
                is_active=True
            )
            
            db.add(quiz)
            await db.flush()  # Get the quiz ID
            
            # Create questions and choices
            for q_data in quiz_data.questions:
                question = Question(
                    id=generate_unique_id(),
                    quiz_id=quiz.id,
                    question_text=q_data.question_text,
                    question_type=q_data.question_type,
                    time_limit=q_data.time_limit,
                    points=q_data.points,
                    order_index=q_data.order_index
                )
                
                db.add(question)
                await db.flush()
                
                # Validate choices
                correct_choices = [c for c in q_data.choices if c.is_correct]
                if not correct_choices:
                    raise InvalidAnswerException(
                        "At least one correct choice required",
                        "system",
                        question.id
                    )
                
                for c_data in q_data.choices:
                    choice = Choice(
                        id=generate_unique_id(),
                        question_id=question.id,
                        choice_text=c_data.choice_text,
                        is_correct=c_data.is_correct,
                        order_index=c_data.order_index
                    )
                    db.add(choice)
            
            await db.commit()
            
            # Return quiz with relationships loaded
            result = await db.execute(
                select(Quiz)
                .options(
                    selectinload(Quiz.questions).selectinload(Question.choices)
                )
                .where(Quiz.id == quiz.id)
            )
            return result.scalar_one()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create quiz: {e}")
            raise
    
    @staticmethod
    async def get_quiz(db: AsyncSession, quiz_id: str) -> Quiz:
        """Get quiz by ID with all related data."""
        result = await db.execute(
            select(Quiz)
            .options(
                selectinload(Quiz.questions).selectinload(Question.choices)
            )
            .where(Quiz.id == quiz_id)
        )
        
        quiz = result.scalar_one_or_none()
        if not quiz:
            raise QuizNotFoundException(quiz_id)
        
        return quiz
    
    @staticmethod
    async def list_active_quizzes(db: AsyncSession, limit: int = 50) -> List[Quiz]:
        """List active quizzes."""
        result = await db.execute(
            select(Quiz)
            .where(Quiz.is_active == True)
            .order_by(Quiz.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


class RoomService:
    """Service for room management operations."""
    
    @staticmethod
    async def create_room(db: AsyncSession, room_data: RoomCreate, host_id: str) -> Room:
        """Create a new game room."""
        try:
            # Verify quiz exists
            quiz = await QuizService.get_quiz(db, room_data.quiz_id)
            
            # Generate unique room code
            room_code = generate_room_code()
            
            # Check for code collision (very unlikely but possible)
            existing = await db.execute(
                select(Room).where(Room.room_code == room_code)
            )
            while existing.scalar_one_or_none():
                room_code = generate_room_code()
                existing = await db.execute(
                    select(Room).where(Room.room_code == room_code)
                )
            
            # Create room
            room = Room(
                id=generate_unique_id(),
                room_code=room_code,
                quiz_id=room_data.quiz_id,
                host_id=host_id,
                host_name=room_data.host_name,
                status="waiting",
                current_question=0,
                max_players=room_data.max_players
            )
            
            db.add(room)
            await db.commit()
            
            logger.info(f"Created room {room_code} for quiz {quiz.title}")
            return room
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create room: {e}")
            raise
    
    @staticmethod
    async def get_room(db: AsyncSession, room_id: str) -> Room:
        """Get room by ID with related data."""
        result = await db.execute(
            select(Room)
            .options(
                selectinload(Room.quiz).selectinload(Quiz.questions).selectinload(Question.choices),
                selectinload(Room.players)
            )
            .where(Room.id == room_id)
        )
        
        room = result.scalar_one_or_none()
        if not room:
            raise RoomNotFoundException(room_id)
        
        return room
    
    @staticmethod
    async def get_room_by_code(db: AsyncSession, room_code: str) -> Room:
        """Get room by code with related data."""
        result = await db.execute(
            select(Room)
            .options(
                selectinload(Room.quiz).selectinload(Quiz.questions).selectinload(Question.choices),
                selectinload(Room.players)
            )
            .where(Room.room_code == room_code)
        )
        
        room = result.scalar_one_or_none()
        if not room:
            raise RoomNotFoundException(room_code)
        
        return room
    
    @staticmethod
    async def start_game(db: AsyncSession, room_id: str) -> bool:
        """Start the game in a room."""
        room = await RoomService.get_room(db, room_id)
        
        if room.status != "waiting":
            raise GameStateException("start game", room.status, "waiting")
        
        # Update room status
        room.status = "active"
        room.started_at = datetime.utcnow()
        
        await db.commit()
        return True
    
    @staticmethod
    async def next_question(db: AsyncSession, room_id: str) -> bool:
        """Move to the next question in the room."""
        room = await RoomService.get_room(db, room_id)
        
        if room.status != "active":
            raise GameStateException("advance question", room.status, "active")
        
        # Check if there are more questions
        if room.current_question >= len(room.quiz.questions) - 1:
            # End game if no more questions
            room.status = "completed"
            room.ended_at = datetime.utcnow()
        else:
            # Move to next question
            room.current_question += 1
        
        await db.commit()
        return True
    
    @staticmethod
    async def end_game(db: AsyncSession, room_id: str) -> bool:
        """End the game manually."""
        room = await RoomService.get_room(db, room_id)
        
        if room.status not in ["waiting", "active"]:
            raise GameStateException("end game", room.status, "waiting or active")
        
        room.status = "completed"
        room.ended_at = datetime.utcnow()
        
        await db.commit()
        return True


class PlayerService:
    """Service for player management operations."""
    
    @staticmethod
    async def join_room(db: AsyncSession, room_code: str, player_id: str, nickname: str) -> Player:
        """Add a player to a room."""
        try:
            room = await RoomService.get_room_by_code(db, room_code)
            
            # Check if room is full
            current_players = len(room.players)
            if current_players >= room.max_players:
                raise RoomFullException(room_code, room.max_players)
            
            # Check for duplicate player
            existing_player = await PlayerService.get_player_in_room(db, room.id, player_id)
            if existing_player:
                raise DuplicatePlayerException(player_id, room_code)
            
            # Create player
            player = Player(
                id=generate_unique_id(),
                room_id=room.id,
                player_id=player_id,
                nickname=sanitize_nickname(nickname),
                is_connected=True,
                total_score=0
            )
            
            db.add(player)
            await db.commit()
            
            logger.info(f"Player {nickname} joined room {room_code}")
            return player
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to join room: {e}")
            raise
    
    @staticmethod
    async def get_player_in_room(db: AsyncSession, room_id: str, player_id: str) -> Optional[Player]:
        """Get a player in a specific room."""
        result = await db.execute(
            select(Player)
            .where(Player.room_id == room_id, Player.player_id == player_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_player_connection(db: AsyncSession, player_id: str, is_connected: bool):
        """Update player connection status."""
        await db.execute(
            update(Player)
            .where(Player.id == player_id)
            .values(is_connected=is_connected)
        )
        await db.commit()


class ScoreService:
    """Service for scoring operations."""
    
    @staticmethod
    async def submit_answer(db: AsyncSession, room_id: str, player_id: str, answer_data: PlayerAnswer) -> Dict[str, Any]:
        """Submit and score a player's answer."""
        try:
            # Get player and question
            player = await db.get(Player, player_id)
            if not player:
                raise PlayerNotFoundException(player_id)
            
            question = await db.get(Question, answer_data.question_id)
            if not question:
                raise QuestionNotFoundException(answer_data.question_id)
            
            # Check for duplicate answer
            existing_answer = await db.execute(
                select(Answer)
                .where(Answer.player_id == player_id, Answer.question_id == answer_data.question_id)
            )
            if existing_answer.scalar_one_or_none():
                raise DuplicateAnswerException(player_id, answer_data.question_id)
            
            # Get the selected choice
            choice = await db.get(Choice, answer_data.choice_id)
            if not choice or choice.question_id != question.id:
                raise InvalidAnswerException("Invalid choice", player_id, answer_data.question_id)
            
            # Calculate score
            is_correct = choice.is_correct
            points_earned = calculate_score(
                question.points, 
                is_correct, 
                answer_data.response_time, 
                question.time_limit
            )
            
            # Create answer record
            answer = Answer(
                id=generate_unique_id(),
                player_id=player_id,
                question_id=answer_data.question_id,
                choice_id=answer_data.choice_id,
                response_time=answer_data.response_time,
                is_correct=is_correct,
                points_earned=points_earned
            )
            
            # Update player's total score
            player.total_score += points_earned
            
            db.add(answer)
            await db.commit()
            
            return {
                "is_correct": is_correct,
                "points_earned": points_earned,
                "correct_choice_id": next((c.id for c in question.choices if c.is_correct), None)
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to submit answer: {e}")
            raise
    
    @staticmethod
    async def get_leaderboard(db: AsyncSession, room_id: str) -> LeaderboardResponse:
        """Get current leaderboard for a room."""
        result = await db.execute(
            select(Player)
            .where(Player.room_id == room_id)
            .order_by(Player.total_score.desc())
        )
        
        players = result.scalars().all()
        
        leaderboard_players = []
        for rank, player in enumerate(players, 1):
            leaderboard_players.append(PlayerScore(
                player_id=player.player_id,
                nickname=player.nickname,
                total_score=player.total_score,
                rank=rank,
                is_connected=player.is_connected
            ))
        
        return LeaderboardResponse(
            players=leaderboard_players,
            total_players=len(players),
            last_updated=datetime.utcnow()
        )

    @staticmethod
    async def get_question_results(db: AsyncSession, room_id: str, question_id: str) -> QuestionStats:
        """Get statistics for a specific question."""
        # This would implement detailed question analytics
        # For now, return basic stats
        return QuestionStats(
            question_id=question_id,
            total_answers=0,
            correct_answers=0,
            average_response_time=0.0,
            choice_distribution={}
        )