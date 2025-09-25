"""Start command handler"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    """Handle /start command"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id):
        await message.reply_text(
            "⚠️ **access denied**\n\n"
            "you are not authorized to use this bot.\n"
            "contact the administrator for access.",
            quote=True
        )
        return
    
    start_text = (
        "🤖 **thebot - professional mux bot**\n\n"
        "**available commands:**\n"
        "• `/term` - execute terminal commands\n"
        "• `/ls` - list directory contents\n"
        "• `/mi` - get media information\n"
        "• `/gup` - upload files to google drive\n"
        "• `/settings` - bot configuration\n"
        "• `/auth` - manage authorization\n\n"
        "**features:**\n"
        "• video muxing and processing\n"
        "• audio/subtitle integration\n"
        "• metadata management\n"
        "• cloud storage integration\n"
        "• professional terminal interface"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 help", callback_data="help"),
            InlineKeyboardButton("⚙️ settings", callback_data="settings_main")
        ],
        [InlineKeyboardButton("📊 status", callback_data="status")]
    ])
    
    await message.reply_text(start_text, reply_markup=keyboard, quote=True)

@Client.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    """Handle /help command"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        return
    
    help_text = (
        "📖 **command reference**\n\n"
        "**terminal commands:**\n"
        "• `/term <command>` - execute shell command\n"
        "• `/ls [path]` - list directory contents\n\n"
        "**media tools:**\n"
        "• `/mi <file>` - show media information\n"
        "• `/mux` - video muxing operations menu\n"
        "• `/extract <file> [type]` - extract streams\n"
        "• `/decrypt <file> <key>` - decrypt content\n\n"
        "**file management:**\n"
        "• `/gup <file>` - upload to google drive\n"
        "• `/dl <url/magnet>` - download with aria2\n"
        "• `/wget <url>` - simple download\n"
        "• `/aclear` - clear downloads\n"
        "• `/ashow` - show active downloads\n\n"
        "**administration:**\n"
        "• `/auth <user_id>` - authorize user\n"
        "• `/unauth <user_id>` - remove authorization\n"
        "• `/settings` - bot configuration\n\n"
        "**note:** all commands require proper authorization"
    )
    
    await message.reply_text(help_text, quote=True)

@Client.on_message(filters.command("test") & filters.private)
async def test_handler(client: Client, message: Message):
    """Test handler without authorization"""
    user_id = message.from_user.id
    await message.reply_text(
        f"🧪 **Test Response**\n\n"
        f"Your ID: `{user_id}`\n"
        f"Owner ID: `{Config.OWNER_ID}`\n"
        f"Is Owner: `{user_id == Config.OWNER_ID}`\n"
        f"Is Authorized: `{Config.is_authorized(user_id)}`",
        quote=True
    )