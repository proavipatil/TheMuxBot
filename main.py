"""Main bot application"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from pyrogram import Client
from pyrogram.errors import RPCError

# Load environment variables first
load_dotenv()

from config import Config, BOT_TOKEN, API_ID, API_HASH, WORKERS, AUTHORIZED_USERS, AUTHORIZED_GROUPS
from database import db
import handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TheBot(Client):
    """Main bot class"""
    
    def __init__(self):
        super().__init__(
            "thebot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=WORKERS,
            parse_mode="markdown"
        )
    
    async def start(self):
        """Start the bot"""
        try:
            await super().start()
            
            # Connect to database
            await db.connect()
            
            # Load authorized users and groups from database
            auth_users = await db.get_auth_users()
            auth_groups = await db.get_auth_groups()
            
            AUTHORIZED_USERS.extend(auth_users)
            AUTHORIZED_GROUPS.extend(auth_groups)
            
            bot_info = await self.get_me()
            logger.info(f"Bot started successfully: @{bot_info.username}")
            logger.info(f"Owner ID: {Config.OWNER_ID}")
            logger.info(f"Authorized users: {len(AUTHORIZED_USERS)}")
            logger.info(f"Authorized groups: {len(AUTHORIZED_GROUPS)}")
            
            # Test authorization for owner
            is_owner_auth = Config.is_authorized(Config.OWNER_ID)
            logger.info(f"Owner authorization test: {is_owner_auth}")
            
        except RPCError as e:
            if "API_ID" in str(e) or "API_HASH" in str(e):
                logger.error("Invalid API_ID or API_HASH")
            elif "BOT_TOKEN" in str(e) or "token" in str(e).lower():
                logger.error("Invalid BOT_TOKEN")
            else:
                logger.error(f"Pyrogram error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot"""
        await db.close()
        await super().stop()
        logger.info("Bot stopped")

async def main():
    """Main function"""
    print("Starting bot...")
    
    # Validate configuration
    if not Config.validate():
        logger.error("Invalid configuration. Please check your environment variables.")
        return
    
    print("Configuration validated successfully")
    
    # Create bot instance
    bot = TheBot()
    print("Bot instance created")
    
    try:
        print("Attempting to start bot...")
        # Start the bot
        await bot.start()
        print("Bot started successfully! Waiting for messages...")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Stop the bot
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())