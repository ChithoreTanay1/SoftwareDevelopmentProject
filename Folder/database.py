# database.py
# Async SQLAlchemy setup for PostgreSQL + helpers (health, init, optional seed).

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, func, text

from config import settings, DATABASE_CONFIG
from utils import generate_unique_id  # remove if you won't seed sample data

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Engine & Session
# ------------------------------------------------------------------------------
# Uses the URL from your .env via config.Settings (settings.database_url)
engine = create_async_engine(
    settings.database_url,
    **DATABASE_CONFIG,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ------------------------------------------------------------------------------
# Base for models (import this in your models as: from database import Base)
# ------------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

# ------------------------------------------------------------------------------
# FastAPI dependency for DB sessions
# ------------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session with proper rollback/cleanup semantics."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise

# ------------------------------------------------------------------------------
# Init / Close
# ------------------------------------------------------------------------------
async def init_db() -> None:
    """Create all tables (ensure models subclass Base and are imported)."""
    try:
        # Import models so they register with Base.metadata
        from models import Room, Quiz, Question, Choice, Player, Answer, Score  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database initialized successfully")

        # Optional seeding when settings.debug = True
        if getattr(settings, "debug", False):
            await create_sample_data()

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

async def close_db() -> None:
    """Dispose engine/pools."""
    try:
        await engine.dispose()
        logger.info("🔌 Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

# ------------------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------------------
async def check_db_health() -> bool:
    """Return True if a simple query succeeds."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(select(func.now()))  # execute a selectable
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# ------------------------------------------------------------------------------
# Sample Data (optional for development)
# ------------------------------------------------------------------------------
async def create_sample_data() -> None:
    """Create a small sample quiz with a few questions & choices."""
    try:
        from models import Quiz, Question, Choice  # ensure these subclass Base

        async with AsyncSessionLocal() as db:
            exists = await db.execute(select(Quiz.id).limit(1))
            if exists.first():
                logger.info("Sample data already exists")
                return

            sample_quiz = Quiz(
                id=generate_unique_id(),
                title="Sample Geography Quiz",
                description="Test your knowledge of world geography!",
                created_by="system",
                is_active=True,
            )
            db.add(sample_quiz)
            await db.flush()  # ensures sample_quiz.id is available

            questions_data = [
                {
                    "question_text": "What is the capital of France?",
                    "choices": [
                        {"text": "London", "correct": False},
                        {"text": "Berlin", "correct": False},
                        {"text": "Paris", "correct": True},
                        {"text": "Madrid", "correct": False},
                    ],
                },
                {
                    "question_text": "Which continent is Brazil located in?",
                    "choices": [
                        {"text": "North America", "correct": False},
                        {"text": "South America", "correct": True},
                        {"text": "Europe", "correct": False},
                        {"text": "Asia", "correct": False},
                    ],
                },
                {
                    "question_text": "What is the largest ocean on Earth?",
                    "choices": [
                        {"text": "Atlantic Ocean", "correct": False},
                        {"text": "Indian Ocean", "correct": False},
                        {"text": "Arctic Ocean", "correct": False},
                        {"text": "Pacific Ocean", "correct": True},
                    ],
                },
            ]

            for i, q in enumerate(questions_data):
                question = Question(
                    id=generate_unique_id(),
                    quiz_id=sample_quiz.id,
                    question_text=q["question_text"],
                    question_type="multiple_choice",
                    time_limit=30,
                    points=100,
                    order_index=i,
                )
                db.add(question)
                await db.flush()  # ensure question.id

                for j, c in enumerate(q["choices"]):
                    choice = Choice(
                        id=generate_unique_id(),
                        question_id=question.id,
                        choice_text=c["text"],
                        is_correct=c["correct"],
                        order_index=j,
                    )
                    db.add(choice)

            await db.commit()
            logger.info("🎯 Sample quiz data created successfully")

    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")

# ------------------------------------------------------------------------------
# One-off connectivity test (manual run)
# ------------------------------------------------------------------------------
async def test_connection() -> None:
    """Manual connectivity test: SELECT 1."""
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    print("✅ Connected successfully!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())
