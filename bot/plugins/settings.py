"""
Settings management plugin
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import Config

def owner_only(func):
    """Decorator to check owner access"""
    async def wrapper(client: Client, message: Message):
        if message.from_user.id != Config.OWNER_ID:
            await message.reply_text("owner only command")
            return
        return await func(client, message)
    return wrapper

@Client.on_message(filters.command("settings"))
@owner_only
async def settings_command(client: Client, message: Message):
    """Handle bot settings"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("view config", callback_data="settings_view"),
            InlineKeyboardButton("system info", callback_data="settings_system")
        ],
        [
            InlineKeyboardButton("restart bot", callback_data="settings_restart"),
            InlineKeyboardButton("close", callback_data="close")
        ]
    ])
    
    settings_text = """**bot settings**

configure and manage bot settings

**current status:**
• **bot version:** `1.0.0`
• **authorized users:** `{}`
• **authorized groups:** `{}`
• **database:** `{}`

select an option below:""".format(
        len(client.auth_users),
        len(client.auth_groups),
        "connected" if client.db else "not configured"
    )
    
    await message.reply_text(
        settings_text,
        reply_markup=keyboard
    )

@Client.on_message(filters.command("config"))
@owner_only
async def config_command(client: Client, message: Message):
    """Show bot configuration"""
    
    config_text = f"""**bot configuration**

**telegram api:**
• **api id:** `{Config.API_ID}`
• **api hash:** `{'*' * 10}...`
• **bot token:** `{'*' * 10}...`

**authorization:**
• **owner id:** `{Config.OWNER_ID}`
• **auth users:** `{len(client.auth_users)}`
• **auth groups:** `{len(client.auth_groups)}`

**database:**
• **mongo uri:** `{'configured' if Config.MONGO_URI else 'not set'}`

**paths:**
• **download path:** `{Config.DOWNLOAD_PATH}`
• **temp path:** `{Config.TEMP_PATH}`

**bot settings:**
• **workers:** `{Config.WORKERS}`
• **max message length:** `{Config.MAX_MESSAGE_LENGTH}`
• **command prefix:** `{Config.CMD_PREFIX}`"""

    await message.reply_text(config_text)