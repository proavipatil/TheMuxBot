"""
Callback query handlers
"""

import os
import platform
import psutil
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from bot.config import Config

@Client.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle callback queries"""
    
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Check authorization for sensitive callbacks
    if data.startswith(("settings_", "auth_")) and user_id != Config.OWNER_ID:
        await callback_query.answer("owner only", show_alert=True)
        return
        
    if data == "help":
        help_text = """**available commands:**

**terminal & system:**
• `/term <command>` - execute terminal command
• `/ls [path]` - list directory contents

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

        await callback_query.edit_message_text(help_text)
        
    elif data == "about":
        about_text = f"""**about mux bot**

**version:** `1.0.0`
**developer:** `MuxBot Team`
**language:** `Python 3.11.9`
**framework:** `Pyrogram`

**features:**
• professional video processing
• terminal access and file management
• media analysis and conversion
• download manager integration
• google drive support
• mongodb database
• authorization system

**owner:** `{Config.OWNER_ID}`
**source:** [github](https://github.com/proavipatil/TheMuxBot)"""

        await callback_query.edit_message_text(
            about_text,
            disable_web_page_preview=True
        )
        
    elif data == "start":
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
**user:** `{callback_query.from_user.first_name}` (`{user_id}`)

use /help to see available commands"""

        await callback_query.edit_message_text(start_text)
        
    elif data == "close":
        await callback_query.message.delete()
        
    elif data == "settings_view":
        config_text = f"""**bot configuration**

**telegram api:**
• **api id:** `{Config.API_ID}`
• **api hash:** `{'*' * 10}...`

**authorization:**
• **owner id:** `{Config.OWNER_ID}`
• **auth users:** `{len(client.auth_users)}`
• **auth groups:** `{len(client.auth_groups)}`

**database:**
• **mongo uri:** `{'configured' if Config.MONGO_URI else 'not set'}`

**paths:**
• **download:** `{Config.DOWNLOAD_PATH}`
• **temp:** `{Config.TEMP_PATH}`"""

        await callback_query.edit_message_text(config_text)
        
    elif data == "settings_system":
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_text = f"""**system information**

**platform:** `{platform.system()} {platform.release()}`
**python:** `{platform.python_version()}`
**cpu usage:** `{cpu_percent}%`
**memory:** `{memory.percent}%` (`{memory.used // 1024 // 1024} MB / {memory.total // 1024 // 1024} MB`)
**disk:** `{disk.percent}%` (`{disk.used // 1024 // 1024 // 1024} GB / {disk.total // 1024 // 1024 // 1024} GB`)

**bot stats:**
• **uptime:** `running`
• **workers:** `{Config.WORKERS}`
• **authorized users:** `{len(client.auth_users)}`
• **authorized groups:** `{len(client.auth_groups)}`"""

        await callback_query.edit_message_text(system_text)
        
    elif data == "settings_restart":
        await callback_query.answer("restart functionality not implemented", show_alert=True)
        
    else:
        await callback_query.answer("unknown callback", show_alert=True)
        
    await callback_query.answer()