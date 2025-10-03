"""
SQLAlchemy models for the Kahoot-style quiz application.
Defines database table structure and relationships.
"""

from sqlalchemy import String, DateTime, Boolean, Integer, Text, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Optional

from database import Base


class Quiz(Base):
    """Quiz model - contains questions and metadata."""
    __tablename__ = "quizzes"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    rooms: Mapped[List["Room"]] = relationship("Room", back_populates="quiz")


class Question(Base):
    """Question model - individual quiz questions."""
    __tablename__ = "questions"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    quiz_id: Mapped[str] = mapped_column(String(50), ForeignKey("quizzes.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), default="multiple_choice")  # multiple_choice, true_false, etc.
    time_limit: Mapped[int] = mapped_column(Integer, default=30)  # seconds
    points: Mapped[int] = mapped_column(Integer, default=100)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    choices: Mapped[List["Choice"]] = relationship("Choice", back_populates="question", cascade="all, delete-orphan")
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="question")


class Choice(Base):
    """Choice model - answer options for questions."""
    __tablename__ = "choices"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    question_id: Mapped[str] = mapped_column(String(50), ForeignKey("questions.id"), nullable=False)
    choice_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="choices")
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="choice")


class Room(Base):
    """Room model - game sessions."""
    __tablename__ = "rooms"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    quiz_id: Mapped[str] = mapped_column(String(50), ForeignKey("quizzes.id"), nullable=False)
    host_id: Mapped[str] = mapped_column(String(100), nullable=False)
    host_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="waiting")  # waiting, active, completed, cancelled
    current_question: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    max_players: Mapped[int] = mapped_column(Integer, default=50)
    
    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="rooms")
    players: Mapped[List["Player"]] = relationship("Player", back_populates="room", cascade="all, delete-orphan")
    scores: Mapped[List["Score"]] = relationship("Score", back_populates="room", cascade="all, delete-orphan")


class Player(Base):
    """Player model - participants in game sessions."""
    __tablename__ = "players"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_id: Mapped[str] = mapped_column(String(50), ForeignKey("rooms.id"), nullable=False)
    player_id: Mapped[str] = mapped_column(String(100), nullable=False)  # External player identifier
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="players")
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="player", cascade="all, delete-orphan")
    scores: Mapped[List["Score"]] = relationship("Score", back_populates="player", cascade="all, delete-orphan")


class Answer(Base):
    """Answer model - player responses to questions."""
    __tablename__ = "answers"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    player_id: Mapped[str] = mapped_column(String(50), ForeignKey("players.id"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(50), ForeignKey("questions.id"), nullable=False)
    choice_id: Mapped[str] = mapped_column(String(50), ForeignKey("choices.id"), nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # seconds
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")
    choice: Mapped["Choice"] = relationship("Choice", back_populates="answers")


# In the Score model, replace the entire class with:
class Score(Base):
    """Score model - aggregated scoring data."""
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_id: Mapped[str] = mapped_column(String(50), ForeignKey("rooms.id"), nullable=False)
    player_id: Mapped[str] = mapped_column(String(50), ForeignKey("players.id"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(50), ForeignKey("questions.id"), nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    rank_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="scores")
    player: Mapped["Player"] = relationship("Player", back_populates="scores")
    question: Mapped["Question"] = relationship("Question")  # Fixed: single relationship