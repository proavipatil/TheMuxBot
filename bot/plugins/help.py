"""
Help command plugin
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handle /help command"""
    
    help_text = """**available commands:**

**terminal & system:**
• `/term <command>` - execute terminal command with real-time output
• `/ls [path]` - list directory contents
• `/pwd` - print current working directory
• `/cd [path]` - change directory

**media processing:**
• `/mi <file/url>` - get media information
• `/mux` - video muxing operations

**download & upload:**
• `/dl <url>` - download with aria2
• `/gup <file>` - upload to google drive

**authorization (owner only):**
• `/auth` - manage authorized users/groups
• `/settings` - bot configuration

**general:**
• `/start` - start the bot
• `/help` - show this help message

**note:** some commands require authorization"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("back", callback_data="start"),
            InlineKeyboardButton("close", callback_data="close")
        ]
    ])
    
    await message.reply_text(
        help_text,
        reply_markup=keyboard
    )