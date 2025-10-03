"""
Pydantic schemas for request/response validation in the quiz application.
Defines data structures for API communication.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class WSMessageType(str, Enum):
    """WebSocket message types."""
    # Host messages
    START_GAME = "start_game"
    NEXT_QUESTION = "next_question" 
    END_GAME = "end_game"
    
    # Player messages
    ANSWER_SUBMITTED = "answer_submitted"
    
    # Broadcast messages
    QUESTION_STARTED = "question_started"
    QUESTION_ENDED = "question_ended"
    GAME_ENDED = "game_ended"
    LEADERBOARD_UPDATE = "leaderboard_update"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"

    # System messages
    ERROR = "error"
    CONNECTION_STATUS = "connection_status"


class GameStatus(str, Enum):
    """Game status options."""
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QuestionType(str, Enum):
    """Question type options."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool = True
    message: str = "Success"
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


class WSMessage(BaseModel):
    """WebSocket message format."""
    type: WSMessageType
    data: Dict[str, Any] = {}
    timestamp: Optional[datetime] = None


# ============================================================================
# CHOICE SCHEMAS
# ============================================================================

class ChoiceBase(BaseModel):
    """Base choice schema."""
    choice_text: str = Field(..., min_length=1, max_length=500)
    order_index: int = Field(..., ge=0)


class ChoiceCreate(ChoiceBase):
    """Schema for creating choices."""
    is_correct: bool = False


class ChoiceResponse(ChoiceBase):
    """Schema for choice responses (without correct answer info)."""
    id: str
    
    model_config = ConfigDict(from_attributes=True)


class ChoiceWithAnswer(ChoiceResponse):
    """Schema for choices with correct answer info."""
    is_correct: bool
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# QUESTION SCHEMAS
# ============================================================================

class QuestionBase(BaseModel):
    """Base question schema."""
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    time_limit: int = Field(default=30, ge=5, le=300)  # 5 seconds to 5 minutes
    points: int = Field(default=100, ge=10, le=1000)
    order_index: int = Field(..., ge=0)


class QuestionCreate(QuestionBase):
    """Schema for creating questions."""
    choices: List[ChoiceCreate] = Field(..., min_items=2, max_items=4)


class QuestionResponse(QuestionBase):
    """Schema for question responses (for players)."""
    id: str
    choices: List[ChoiceResponse]
    
    model_config = ConfigDict(from_attributes=True)


class QuestionWithAnswers(QuestionBase):
    """Schema for questions with answer info (for hosts)."""
    id: str
    choices: List[ChoiceWithAnswer]
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# QUIZ SCHEMAS
# ============================================================================

class QuizBase(BaseModel):
    """Base quiz schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class QuizCreate(QuizBase):
    """Schema for creating quizzes."""
    created_by: str = Field(..., min_length=1, max_length=100)
    questions: List[QuestionCreate] = Field(..., min_items=1, max_items=50)


class QuizResponse(QuizBase):
    """Schema for quiz responses."""
    id: str
    created_by: str
    created_at: datetime
    is_active: bool
    questions: List[QuestionResponse]
    
    model_config = ConfigDict(from_attributes=True)


class QuizSummary(QuizBase):
    """Schema for quiz summaries (without questions)."""
    id: str
    created_by: str
    created_at: datetime
    is_active: bool
    question_count: int
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ROOM SCHEMAS  
# ============================================================================

class RoomCreate(BaseModel):
    """Schema for creating rooms."""
    quiz_id: str
    host_name: str = Field(..., min_length=1, max_length=100)
    max_players: int = Field(default=50, ge=2, le=100)


class RoomResponse(BaseModel):
    """Schema for room responses."""
    id: str
    room_code: str
    quiz_id: str
    host_id: str
    host_name: str
    status: GameStatus
    current_question: int
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    max_players: int
    player_count: int
    
    model_config = ConfigDict(from_attributes=True)


class RoomJoin(BaseModel):
    """Schema for joining rooms."""
    nickname: str = Field(..., min_length=1, max_length=100)


# ============================================================================
# PLAYER SCHEMAS
# ============================================================================

class PlayerBase(BaseModel):
    """Base player schema."""
    nickname: str = Field(..., min_length=1, max_length=100)


class PlayerResponse(PlayerBase):
    """Schema for player responses."""
    id: str
    player_id: str
    joined_at: datetime
    is_connected: bool
    total_score: int
    
    model_config = ConfigDict(from_attributes=True)


class PlayerSummary(BaseModel):
    """Schema for player summaries."""
    player_id: str
    nickname: str
    total_score: int
    is_connected: bool


# ============================================================================
# ANSWER SCHEMAS
# ============================================================================

class PlayerAnswer(BaseModel):
    """Schema for player answer submission."""
    question_id: str
    choice_id: str
    response_time: Optional[float] = Field(None, ge=0)


class AnswerResponse(BaseModel):
    """Schema for answer feedback."""
    is_correct: bool
    points_earned: int
    correct_choice_id: Optional[str] = None
    response_time: Optional[float] = None


class AnswerResult(BaseModel):
    """Schema for detailed answer results."""
    question_id: str
    player_id: str
    choice_id: str
    is_correct: bool
    points_earned: int
    response_time: Optional[float]
    answered_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCORING SCHEMAS
# ============================================================================

class PlayerScore(BaseModel):
    """Schema for individual player scores."""
    player_id: str
    nickname: str
    total_score: int
    rank: int
    is_connected: bool


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard data."""
    players: List[PlayerScore]
    total_players: int
    last_updated: datetime


class QuestionStats(BaseModel):
    """Schema for question statistics."""
    question_id: str
    total_answers: int
    correct_answers: int
    average_response_time: Optional[float]
    choice_distribution: Dict[str, int]  # choice_id -> count


class GameStats(BaseModel):
    """Schema for game statistics."""
    room_code: str
    total_players: int
    total_questions: int
    questions_completed: int
    average_score: float
    game_duration: Optional[float]  # minutes
    question_stats: List[QuestionStats]


# ============================================================================
# WEBSOCKET EVENT SCHEMAS
# ============================================================================

class PlayerJoinedEvent(BaseModel):
    """Schema for player joined event."""
    player_id: str
    nickname: str
    player_count: int


class PlayerLeftEvent(BaseModel):
    """Schema for player left event."""
    player_id: str
    nickname: str
    player_count: int


class QuestionStartedEvent(BaseModel):
    """Schema for question started event."""
    question: QuestionResponse
    question_number: int
    total_questions: int
    time_limit: int


class QuestionEndedEvent(BaseModel):
    """Schema for question ended event."""
    question_id: str
    results: QuestionStats
    correct_choice_id: str
    leaderboard: LeaderboardResponse


class GameEndedEvent(BaseModel):
    """Schema for game ended event."""
    final_leaderboard: LeaderboardResponse
    game_stats: GameStats
    message: str


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    success: bool = False
    message: str
    error_code: str
    details: Optional[Dict[str, Any]] = None


class ValidationError(BaseModel):
    """Schema for validation errors."""
    field: str
    message: str
    invalid_value: Any


class ValidationErrorResponse(ErrorResponse):
    """Schema for validation error responses."""
    error_code: str = "validation_error"
    validation_errors: List[ValidationError]