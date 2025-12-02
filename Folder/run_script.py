#!/usr/bin/env python3


import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from config import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("quiz_game.log") if not settings.debug else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


class QuizGameServer:
    """Quiz game server with proper lifecycle management."""
    
    def __init__(self):
        self.server = None
        self.shutdown_event = asyncio.Event()
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Graceful shutdown process."""
        logger.info("Shutting down Quiz Game server...")
        self.shutdown_event.set()
        
        if self.server:
            self.server.should_exit = True
    
    async def start(self):
        """Start the server."""
        try:
            logger.info("Starting Kahoot-style Quiz Game API server...")
            logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
            logger.info(f"Server will run on {settings.host}:{settings.port}")
            
            # Configure uvicorn
            config = uvicorn.Config(
                "app:app",
                host=settings.host,
                port=settings.port,
                reload=settings.debug,
                log_level="info" if not settings.debug else "debug",
                access_log=True,
                loop="asyncio",
                # WebSocket settings
                ws_ping_interval=20,
                ws_ping_timeout=10,
                ws_max_size=16777216,  # 16MB
            )
            
            self.server = uvicorn.Server(config)
            
            # Start server
            await self.server.serve()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    async def run(self):
        """Main run method."""
        try:
            # Start the server
            await self.start()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            logger.info("Server stopped")


async def main():
    """Main entry point."""
    server = QuizGameServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)
