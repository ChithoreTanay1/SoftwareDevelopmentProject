#!/usr/bin/env python3
"""
Debug database connection issues
"""

import os
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_connection():
    logger.info("🔍 Debugging database connection...")
    logger.info(f"Current database_url: {settings.database_url}")
    logger.info(f"Environment DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
    
    # Parse the URL to see what's wrong
    if "postgresql" in settings.database_url:
        # Extract parts from URL
        url_parts = settings.database_url.replace("postgresql+asyncpg://", "").split("@")[0]
        if ":" in url_parts:
            user, password = url_parts.split(":")
            logger.info(f"Trying to connect as user: {user}")
            logger.info(f"With password: {'*' * len(password)}")
        else:
            logger.error("❌ Malformed database URL")

if __name__ == "__main__":
    debug_connection()