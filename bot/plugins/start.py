"""
Start command plugin
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import Config

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    
    user = message.from_user
    
    start_text = f"""**mux bot v1.0**

professional telegram bot for video processing and media tools

**features:**
• terminal access with real-time output
• video muxing with mkvtoolnix and ffmpeg  
• download manager with aria2
• media information analysis
• file management and organization
• google drive integration

**owner:** `{Config.OWNER_ID}`
**user:** `{user.first_name}` (`{user.id}`)

use /help to see available commands"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("help", callback_data="help"),
            InlineKeyboardButton("about", callback_data="about")
        ],
        [
            InlineKeyboardButton("source", url="https://github.com/proavipatil/TheMuxBot")
        ]
    ])
    
    await message.reply_text(
        start_text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )