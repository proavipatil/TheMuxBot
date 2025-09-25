"""
Database operations for MuxBot
"""

import logging
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient

from .config import Config

logger = logging.getLogger(__name__)

class Database:
    """Database handler class"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(Config.MONGO_URI)
            self.db = self.client.muxbot
            await self.client.admin.command('ping')
            logger.info("connected to database")
        except Exception as e:
            logger.error(f"database connection failed: {e}")
            
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("database connection closed")
            
    async def get_auth_data(self) -> Dict[str, List[int]]:
        """Get authorized users and groups"""
        try:
            doc = await self.db.auth.find_one({"_id": "auth_data"})
            return doc or {"users": [], "groups": []}
        except Exception as e:
            logger.error(f"error getting auth data: {e}")
            return {"users": [], "groups": []}
            
    async def add_auth_user(self, user_id: int) -> bool:
        """Add authorized user"""
        try:
            await self.db.auth.update_one(
                {"_id": "auth_data"},
                {"$addToSet": {"users": user_id}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"error adding auth user: {e}")
            return False
            
    async def remove_auth_user(self, user_id: int) -> bool:
        """Remove authorized user"""
        try:
            await self.db.auth.update_one(
                {"_id": "auth_data"},
                {"$pull": {"users": user_id}}
            )
            return True
        except Exception as e:
            logger.error(f"error removing auth user: {e}")
            return False
            
    async def add_auth_group(self, group_id: int) -> bool:
        """Add authorized group"""
        try:
            await self.db.auth.update_one(
                {"_id": "auth_data"},
                {"$addToSet": {"groups": group_id}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"error adding auth group: {e}")
            return False
            
    async def remove_auth_group(self, group_id: int) -> bool:
        """Remove authorized group"""
        try:
            await self.db.auth.update_one(
                {"_id": "auth_data"},
                {"$pull": {"groups": group_id}}
            )
            return True
        except Exception as e:
            logger.error(f"error removing auth group: {e}")
            return False
            
    async def get_settings(self) -> Dict[str, Any]:
        """Get bot settings"""
        try:
            doc = await self.db.settings.find_one({"_id": "bot_settings"})
            return doc or {}
        except Exception as e:
            logger.error(f"error getting settings: {e}")
            return {}
            
    async def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update bot settings"""
        try:
            await self.db.settings.update_one(
                {"_id": "bot_settings"},
                {"$set": settings},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"error updating settings: {e}")
            return False