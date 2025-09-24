"""Configuration module for TheBot"""

import os
from typing import List, Optional

# Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Authorization
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
AUTHORIZED_USERS: List[int] = []
AUTHORIZED_GROUPS: List[int] = []

# Google Drive Configuration
G_DRIVE_CLIENT_ID = os.environ.get("G_DRIVE_CLIENT_ID", "")
G_DRIVE_CLIENT_SECRET = os.environ.get("G_DRIVE_CLIENT_SECRET", "")
G_DRIVE_AUTH_TOKEN_DATA = os.environ.get("G_DRIVE_AUTH_TOKEN_DATA", "")
G_DRIVE_PARENT_ID = os.environ.get("G_DRIVE_PARENT_ID", "")
G_DRIVE_INDEX_LINK = os.environ.get("G_DRIVE_INDEX_LINK", "")

# Logging Configuration
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "0")) if os.environ.get("LOG_CHANNEL_ID") else None
TELEGRAPH_TOKEN = os.environ.get("TELEGRAPH_TOKEN", "")

# Paths
DOWNLOAD_PATH = os.environ.get("DOWNLOAD_PATH", "./downloads/")
TEMP_PATH = os.environ.get("TEMP_PATH", "./temp/")
LOG_PATH = os.environ.get("LOG_PATH", "./logs/")

# Bot Settings
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "2147483648"))  # 2GB
WORKERS = int(os.environ.get("WORKERS", "4"))
COMMAND_TIMEOUT = int(os.environ.get("COMMAND_TIMEOUT", "300"))  # 5 minutes

# Create directories
for path in [DOWNLOAD_PATH, TEMP_PATH, LOG_PATH]:
    os.makedirs(path, exist_ok=True)

class Config:
    """Configuration class"""
    
    @staticmethod
    def validate() -> bool:
        """Validate required configuration"""
        required = [BOT_TOKEN, API_ID, API_HASH, OWNER_ID]
        return all(required)
    
    @staticmethod
    def is_authorized(user_id: int, chat_id: Optional[int] = None) -> bool:
        """Check if user/chat is authorized"""
        if user_id == OWNER_ID:
            return True
        if user_id in AUTHORIZED_USERS:
            return True
        if chat_id and chat_id in AUTHORIZED_GROUPS:
            return True
        return False