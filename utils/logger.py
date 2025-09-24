from pyrogram import Client
from config import LOG_CHANNEL_ID

async def log_to_channel(client: Client, message: str, file_path: str = None):
    if not LOG_CHANNEL_ID:
        return
    
    try:
        if file_path:
            await client.send_document(LOG_CHANNEL_ID, file_path, caption=message)
        else:
            await client.send_message(LOG_CHANNEL_ID, message)
    except Exception:
        pass