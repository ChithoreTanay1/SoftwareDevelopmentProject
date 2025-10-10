#!/usr/bin/env python3
"""
Database setup script for PostgreSQL.
Run this once to create the database and user.
"""

import asyncio
import asyncpg
import os
from config import settings

async def create_database():
    """Create database and user if they don't exist."""

    # Extract connection info from DATABASE_URL
    # Format: postgresql+asyncpg://user:password@host:port/database
    db_url = settings.database_url.replace("postgresql+asyncpg://", "")

    if "@" in db_url:
        user_pass, host_db = db_url.split("@", 1)
        user, password = user_pass.split(":", 1)
        host_port, database = host_db.split("/", 1)

        if ":" in host_port:
            host, port = host_port.split(":", 1)
        else:
            host = host_port
            port = "5432"
    else:
        # Default values
        user = "postgres"
        password = "password"
        host = "localhost"
        port = "5432"
        database = "quiz_game"

    # Connect to PostgreSQL (without specifying database)
    conn = await asyncpg.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database="postgres"  # Connect to default postgres database
    )

    try:
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", database
        )

        if not result:
            # Create database
            await conn.execute(f'CREATE DATABASE "{database}"')
            print(f" Database '{database}' created successfully")
        else:
            print(f" Database '{database}' already exists")

    except Exception as e:
        print(f" Error creating database: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_database())