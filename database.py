"""Database module for TheBot"""

import asyncio
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config import DATABASE_URL

class Database:
    """Database handler"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to database"""
        if DATABASE_URL:
            self.client = AsyncIOMotorClient(DATABASE_URL)
            self.db = self.client.thebot
            
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            
    async def add_auth_user(self, user_id: int) -> bool:
        """Add authorized user"""
        if self.db is None:
            return False
        await self.db.auth_users.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id}},
            upsert=True
        )
        return True
        
    async def remove_auth_user(self, user_id: int) -> bool:
        """Remove authorized user"""
        if self.db is None:
            return False
        result = await self.db.auth_users.delete_one({"user_id": user_id})
        return result.deleted_count > 0
        
    async def get_auth_users(self) -> List[int]:
        """Get all authorized users"""
        if self.db is None:
            return []
        cursor = self.db.auth_users.find({})
        return [doc["user_id"] async for doc in cursor]
        
    async def add_auth_group(self, group_id: int) -> bool:
        """Add authorized group"""
        if self.db is None:
            return False
        await self.db.auth_groups.update_one(
            {"group_id": group_id},
            {"$set": {"group_id": group_id}},
            upsert=True
        )
        return True
        
    async def remove_auth_group(self, group_id: int) -> bool:
        """Remove authorized group"""
        if self.db is None:
            return False
        result = await self.db.auth_groups.delete_one({"group_id": group_id})
        return result.deleted_count > 0
        
    async def get_auth_groups(self) -> List[int]:
        """Get all authorized groups"""
        if self.db is None:
            return []
        cursor = self.db.auth_groups.find({})
        return [doc["group_id"] async for doc in cursor]

# Global database instance
db = Database()