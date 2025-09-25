#!/usr/bin/env python3
"""
Professional Telegram Mux Bot
Main entry point for the bot
"""

import asyncio
import logging
import sys
from pathlib import Path

from bot import MuxBot
from bot.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    try:
        # Create necessary directories
        Path("downloads").mkdir(exist_ok=True)
        Path("temp").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Initialize and start bot
        bot = MuxBot()
        logger.info("starting mux bot...")
        await bot.start()
        logger.info("bot started successfully")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("bot stopped by user")
    except Exception as e:
        logger.error(f"error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())