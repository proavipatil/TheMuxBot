"""
Main bot client implementation
"""

import logging
from pathlib import Path
from typing import Dict, Any

from pyrogram import Client, filters
from pyrogram.types import Message

from .config import Config
from .database import Database
# from .plugins import load_plugins

logger = logging.getLogger(__name__)

class MuxBot(Client):
    """Main bot client class"""
    
    def __init__(self):
        super().__init__(
            name="muxbot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.WORKERS,
            plugins={"root": "bot.plugins"}
        )
        
        self.config = Config
        self.db = Database() if Config.MONGO_URI else None
        self.owner_id = Config.OWNER_ID
        self.auth_users = set(Config.AUTH_USERS)
        self.auth_groups = set(Config.AUTH_GROUPS)
        
    async def start(self):
        """Start the bot"""
        if not Config.validate():
            logger.error("invalid configuration. check environment variables")
            logger.error(f"API_ID: {Config.API_ID}, API_HASH: {'set' if Config.API_HASH else 'not set'}, BOT_TOKEN: {'set' if Config.BOT_TOKEN else 'not set'}, OWNER_ID: {Config.OWNER_ID}")
            return
            
        await super().start()
        
        if self.db:
            await self.db.connect()
            
        # Load auth data from database
        if self.db:
            auth_data = await self.db.get_auth_data()
            self.auth_users.update(auth_data.get("users", []))
            self.auth_groups.update(auth_data.get("groups", []))
            
        me = await self.get_me()
        logger.info(f"bot started as @{me.username}")
        
    async def stop(self):
        """Stop the bot"""
        if self.db:
            await self.db.close()
        await super().stop()
        logger.info("bot stopped")
        
    def is_authorized(self, user_id: int, chat_id: int = None) -> bool:
        """Check if user is authorized"""
        if user_id == self.owner_id:
            return True
        if user_id in self.auth_users:
            return True
        if chat_id and chat_id in self.auth_groups:
            return True
        return False