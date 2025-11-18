from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    Integer,
    Text,
    ForeignKey,
    Float,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base


# ----------------------------- QUIZ ---------------------------------
class Quiz(Base):
    """Quiz model - contains questions and metadata."""
    __tablename__ = "quizzes"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    questions: Mapped[List["Question"]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Question.order_index",
    )
    rooms: Mapped[List["Room"]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Quiz id={self.id!r} title={self.title!r}>"


# --------------------------- QUESTION --------------------------------
class Question(Base):
    """Question model - individual quiz questions."""
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    quiz_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), default="multiple_choice", nullable=False)
    time_limit: Mapped[int] = mapped_column(Integer, default=30, nullable=False)  # seconds
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    choices: Mapped[List["Choice"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Choice.order_index",
    )
    answers: Mapped[List["Answer"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # Ensure each question order is unique within a quiz
        UniqueConstraint("quiz_id", "order_index", name="uq_question_quiz_order"),
        Index("ix_question_quiz_points", "quiz_id", "points"),
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id!r} quiz_id={self.quiz_id!r}>"


# ----------------------------- CHOICE --------------------------------
class Choice(Base):
    """Choice model - answer options for questions."""
    __tablename__ = "choices"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    question_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    choice_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="choices")
    answers: Mapped[List["Answer"]] = relationship(
        back_populates="choice",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # Keep choice order unique per question
        UniqueConstraint("question_id", "order_index", name="uq_choice_question_order"),
    )

    def __repr__(self) -> str:
        return f"<Choice id={self.id!r} question_id={self.question_id!r}>"


# ------------------------------ ROOM ---------------------------------
class Room(Base):
    """Room model - game sessions."""
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    quiz_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    host_id: Mapped[str] = mapped_column(String(100), nullable=False)
    host_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="waiting", nullable=False)  # waiting, active, completed, cancelled
    current_question: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    max_players: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    # Relationships
    quiz: Mapped["Quiz"] = relationship(back_populates="rooms")
    players: Mapped[List["Player"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Player.joined_at",
    )
    scores: Mapped[List["Score"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Room code={self.room_code!r} quiz_id={self.quiz_id!r}>"


# ----------------------------- PLAYER --------------------------------
class Player(Base):
    """Player model - participants in game sessions."""
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[str] = mapped_column(String(100), nullable=False)  # External player identifier
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    room: Mapped["Room"] = relationship(back_populates="players")
    answers: Mapped[List["Answer"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    scores: Mapped[List["Score"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # Prevent the same logical player joining the same room twice
        UniqueConstraint("room_id", "player_id", name="uq_player_room_playerid"),
        # Optional: prevent same nickname twice in one room
        UniqueConstraint("room_id", "nickname", name="uq_player_room_nickname"),
    )

    def __repr__(self) -> str:
        return f"<Player id={self.id!r} room_id={self.room_id!r} nickname={self.nickname!r}>"


# ----------------------------- ANSWER --------------------------------
class Answer(Base):
    """Answer model - player responses to questions."""
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    player_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    choice_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("choices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # seconds
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    player: Mapped["Player"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship(back_populates="answers")
    choice: Mapped["Choice"] = relationship(back_populates="answers")

    __table_args__ = (
        # One answer per player per question
        UniqueConstraint("player_id", "question_id", name="uq_answer_player_question"),
    )

    def __repr__(self) -> str:
        return f"<Answer id={self.id!r} player_id={self.player_id!r} question_id={self.question_id!r}>"


# ------------------------------ SCORE --------------------------------
class Score(Base):
    """Score model - aggregated scoring data."""
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rank_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    room: Mapped["Room"] = relationship(back_populates="scores")
    player: Mapped["Player"] = relationship(back_populates="scores")
    question: Mapped["Question"] = relationship()  # single relationship is fine

    __table_args__ = (
        # Ensure a single score row per (room, player, question)
        UniqueConstraint("room_id", "player_id", "question_id", name="uq_score_room_player_question"),
        Index("ix_score_room_total", "room_id", "total_points"),
    )

    def __repr__(self) -> str:
        return f"<Score room_id={self.room_id!r} player_id={self.player_id!r} q={self.question_id!r} total={self.total_points}>"
