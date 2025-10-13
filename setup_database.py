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
    
    print(f"Attempting to connect with:")
    print(f"User: {user}")
    print(f"Host: {host}:{port}")
    print(f"Database: {database}")
    
    try:
        # First try with password
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres"
        )
        print(" Connected with password authentication")
        
    except asyncpg.InvalidPasswordError:
        print(" Password authentication failed. Trying without password...")
        try:
            # Try without password (common in local development)
            conn = await asyncpg.connect(
                user=user,
                host=host,
                port=port,
                database="postgres"
            )
            print(" Connected without password")
        except Exception as e:
            print(f" Connection failed: {e}")
            print("\nPlease check your PostgreSQL configuration:")
            print("1. Make sure PostgreSQL is running")
            print("2. Check your username and password")
            print("3. Try these common passwords: '', 'postgres', 'password'")
            return
    
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
        print(" Database setup completed")

if __name__ == "__main__":
    asyncio.run(create_database())