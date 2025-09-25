"""
Configuration module for MuxBot
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Bot configuration class"""
    
    # Telegram API credentials
    API_ID: int = int(os.environ.get("API_ID", "0"))
    API_HASH: str = os.environ.get("API_HASH", "")
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
    
    # Bot owner and authorization
    OWNER_ID: int = int(os.environ.get("OWNER_ID", "0"))
    AUTH_USERS: List[int] = []
    AUTH_GROUPS: List[int] = []
    
    # Database
    MONGO_URI: str = os.environ.get("MONGO_URI", "")
    
    # Telegraph
    TELEGRAPH_TOKEN: str = os.environ.get("TELEGRAPH_TOKEN", "")
    
    # Paths
    DOWNLOAD_PATH: str = os.environ.get("DOWNLOAD_PATH", "downloads")
    TEMP_PATH: str = os.environ.get("TEMP_PATH", "temp")
    
    # Bot settings
    CMD_PREFIX: str = "/"
    MAX_MESSAGE_LENGTH: int = 4096
    WORKERS: int = int(os.environ.get("WORKERS", "4"))
    
    # Progress indicators
    FINISHED_PROGRESS: str = "█"
    UNFINISHED_PROGRESS: str = "░"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        return all([
            cls.API_ID and cls.API_ID != 0,
            cls.API_HASH and cls.API_HASH != "",
            cls.BOT_TOKEN and cls.BOT_TOKEN != "",
            cls.OWNER_ID and cls.OWNER_ID != 0
        ])