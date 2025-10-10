#!/usr/bin/env python3
"""
PostgreSQL initialization script for Quiz Game
"""

import asyncio
import logging
from database import init_db, close_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_database():
    """Initialize the PostgreSQL database"""
    try:
        logger.info("🔄 Initializing PostgreSQL database...")
        await init_db()
        logger.info("✅ PostgreSQL database initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(initialize_database())