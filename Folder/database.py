

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Boolean, Integer, Text, ForeignKey
from utils import generate_unique_id, generate_room_code
import logging
from typing import AsyncGenerator

from config import settings, DATABASE_CONFIG

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    **DATABASE_CONFIG
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI.
    Creates and manages database sessions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    try:
        # Import all models to ensure they're registered
        from models import Room, Quiz, Question, Choice, Player, Answer, Score
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ Database initialized successfully")
        
        # Create sample data if in debug mode
        if settings.debug:
            await create_sample_data()
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


async def close_db():
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("🔌 Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


async def create_sample_data():
    """Create sample data for development."""
    try:
        from models import Quiz, Question, Choice
        from utils import generate_unique_id
        
        async with AsyncSessionLocal() as db:
            # Check if sample data already exists
            from sqlalchemy import select
            result = await db.execute(select(Quiz).limit(1))
            if result.first():
                logger.info("Sample data already exists")
                return
            
            # Create sample quiz
            sample_quiz = Quiz(
                id=generate_unique_id(),
                title="Sample Geography Quiz",
                description="Test your knowledge of world geography!",
                created_by="system",
                is_active=True
            )
            
            db.add(sample_quiz)
            await db.flush()  # Get the quiz ID
            
            # Sample questions
            questions_data = [
                {
                    "question_text": "What is the capital of France?",
                    "choices": [
                        {"text": "London", "correct": False},
                        {"text": "Berlin", "correct": False},
                        {"text": "Paris", "correct": True},
                        {"text": "Madrid", "correct": False}
                    ]
                },
                {
                    "question_text": "Which continent is Brazil located in?",
                    "choices": [
                        {"text": "North America", "correct": False},
                        {"text": "South America", "correct": True},
                        {"text": "Europe", "correct": False},
                        {"text": "Asia", "correct": False}
                    ]
                },
                {
                    "question_text": "What is the largest ocean on Earth?",
                    "choices": [
                        {"text": "Atlantic Ocean", "correct": False},
                        {"text": "Indian Ocean", "correct": False},
                        {"text": "Arctic Ocean", "correct": False},
                        {"text": "Pacific Ocean", "correct": True}
                    ]
                }
            ]
            
            for i, q_data in enumerate(questions_data):
                question = Question(
                    id=generate_unique_id(),
                    quiz_id=sample_quiz.id,
                    question_text=q_data["question_text"],
                    question_type="multiple_choice",
                    time_limit=30,
                    points=100,
                    order_index=i
                )
                
                db.add(question)
                await db.flush()
                
                for j, c_data in enumerate(q_data["choices"]):
                    choice = Choice(
                        id=generate_unique_id(),
                        question_id=question.id,
                        choice_text=c_data["text"],
                        is_correct=c_data["correct"],
                        order_index=j
                    )
                    db.add(choice)
            
            await db.commit()
            logger.info("🎯 Sample quiz data created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")


# Health check function
async def check_db_health() -> bool:
    """Check if database is accessible."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(func.now())
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
