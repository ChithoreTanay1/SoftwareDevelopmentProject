#!/usr/bin/env python3
"""
Robust PostgreSQL setup for Quiz Game
Ensures data integrity and proper relationships
"""

import asyncio
import logging
import asyncpg
from sqlalchemy import text
from sqlalchemy.orm import selectinload
from database import engine, Base
from models import Quiz, Question, Choice, Room, Player, Answer, Score
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_asyncpg_url(sqlalchemy_url: str) -> str:
    """Convert SQLAlchemy URL to asyncpg format"""
    return sqlalchemy_url.replace('postgresql+asyncpg://', 'postgresql://')

async def setup_database():
    """Setup complete database structure with proper constraints"""
    try:
        # Test connection first
        logger.info("🔌 Testing database connection...")
        asyncpg_url = get_asyncpg_url(settings.database_url)
        conn = await asyncpg.connect(asyncpg_url)
        await conn.close()
        logger.info("✅ Database connection successful!")

        # Create all tables
        logger.info("🗃️ Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # Clean start
            await conn.run_sync(Base.metadata.create_all)
        
        # Add custom constraints and indexes
        await add_custom_constraints()
        
        # Create sample data for testing
        await create_sample_data()
        
        logger.info("🎉 Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

async def add_custom_constraints():
    """Add additional constraints for data integrity"""
    async with engine.begin() as conn:
        # Add custom indexes for performance - ONE AT A TIME
        index_commands = [
            "CREATE INDEX IF NOT EXISTS idx_room_code ON rooms(room_code)",
            "CREATE INDEX IF NOT EXISTS idx_room_status ON rooms(status)",
            "CREATE INDEX IF NOT EXISTS idx_player_room ON players(room_id)",
            "CREATE INDEX IF NOT EXISTS idx_player_score ON players(total_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_answer_player_question ON answers(player_id, question_id)",
            "CREATE INDEX IF NOT EXISTS idx_question_quiz ON questions(quiz_id)",
            "CREATE INDEX IF NOT EXISTS idx_choice_question ON choices(question_id)"
        ]
        
        for command in index_commands:
            await conn.execute(text(command))
        
        logger.info("✅ Added custom constraints and indexes")
        
        # Add unique constraints (use DO block to handle existing constraints)
        await conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'unique_player_question'
                ) THEN
                    ALTER TABLE answers ADD CONSTRAINT unique_player_question 
                    UNIQUE (player_id, question_id);
                END IF;
            END $$;
        """))
        
        logger.info("✅ Added custom constraints and indexes")

async def create_sample_data():
    """Create robust sample data for testing"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from utils import generate_unique_id
    
    async with AsyncSession(engine) as session:
        # Check if sample data already exists
        result = await session.execute(select(Quiz).limit(1))
        if result.first():
            logger.info("📊 Sample data already exists")
            return
        
        logger.info("🎯 Creating sample quizzes...")
        
        # Sample Quiz 1: General Knowledge
        quiz1 = Quiz(
            id=generate_unique_id(),
            title="General Knowledge Challenge",
            description="Test your knowledge across various topics!",
            created_by="system_admin",
            is_active=True
        )
        session.add(quiz1)
        await session.flush()
        
        # Questions for Quiz 1
        questions_data = [
            {
                "text": "What is the capital of France?",
                "type": "multiple_choice",
                "time_limit": 30,
                "points": 100,
                "choices": [
                    {"text": "London", "correct": False},
                    {"text": "Berlin", "correct": False},
                    {"text": "Paris", "correct": True},
                    {"text": "Madrid", "correct": False}
                ]
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "type": "multiple_choice", 
                "time_limit": 25,
                "points": 100,
                "choices": [
                    {"text": "Venus", "correct": False},
                    {"text": "Mars", "correct": True},
                    {"text": "Jupiter", "correct": False},
                    {"text": "Saturn", "correct": False}
                ]
            },
            {
                "text": "What is 2 + 2?",
                "type": "multiple_choice",
                "time_limit": 15,
                "points": 50,
                "choices": [
                    {"text": "3", "correct": False},
                    {"text": "4", "correct": True},
                    {"text": "5", "correct": False}
                ]
            }
        ]
        
        for i, q_data in enumerate(questions_data):
            question = Question(
                id=generate_unique_id(),
                quiz_id=quiz1.id,
                question_text=q_data["text"],
                question_type=q_data["type"],
                time_limit=q_data["time_limit"],
                points=q_data["points"],
                order_index=i
            )
            session.add(question)
            await session.flush()
            
            for j, c_data in enumerate(q_data["choices"]):
                choice = Choice(
                    id=generate_unique_id(),
                    question_id=question.id,
                    choice_text=c_data["text"],
                    is_correct=c_data["correct"],
                    order_index=j
                )
                session.add(choice)
        
        # Sample Quiz 2: Science
        quiz2 = Quiz(
            id=generate_unique_id(),
            title="Science Fundamentals",
            description="Basic science knowledge test",
            created_by="science_teacher",
            is_active=True
        )
        session.add(quiz2)
        await session.flush()
        
        science_questions = [
            {
                "text": "Water is composed of which two elements?",
                "type": "multiple_choice",
                "time_limit": 30,
                "points": 100,
                "choices": [
                    {"text": "Hydrogen and Oxygen", "correct": True},
                    {"text": "Hydrogen and Carbon", "correct": False},
                    {"text": "Oxygen and Carbon", "correct": False},
                    {"text": "Nitrogen and Oxygen", "correct": False}
                ]
            }
        ]
        
        for i, q_data in enumerate(science_questions):
            question = Question(
                id=generate_unique_id(),
                quiz_id=quiz2.id,
                question_text=q_data["text"],
                question_type=q_data["type"],
                time_limit=q_data["time_limit"],
                points=q_data["points"],
                order_index=i
            )
            session.add(question)
            await session.flush()
            
            for j, c_data in enumerate(q_data["choices"]):
                choice = Choice(
                    id=generate_unique_id(),
                    question_id=question.id,
                    choice_text=c_data["text"],
                    is_correct=c_data["correct"],
                    order_index=j
                )
                session.add(choice)
        
        await session.commit()
        logger.info("✅ Sample data created successfully")

async def verify_database():
    """Verify database integrity and relationships"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, func
    
    async with AsyncSession(engine) as session:
        # Check table counts
        tables = [Quiz, Question, Choice, Room, Player, Answer, Score]
        for table in tables:
            result = await session.execute(select(func.count()).select_from(table))
            count = result.scalar()
            logger.info(f"📊 {table.__name__}: {count} records")
        
        # Verify quiz-question relationships
        result = await session.execute(
            select(Quiz).options(selectinload(Quiz.questions))
        )
        quizzes = result.scalars().all()
        
        for quiz in quizzes:
            logger.info(f"📝 Quiz '{quiz.title}' has {len(quiz.questions)} questions")
            for question in quiz.questions:
                logger.info(f"   - Question: {question.question_text} ({len(question.choices)} choices)")

if __name__ == "__main__":
    asyncio.run(setup_database())