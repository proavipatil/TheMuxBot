"""Settings and callback handlers"""

import os
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from config import Config, DOWNLOAD_PATH, TEMP_PATH, LOG_PATH
from utils import create_settings_keyboard, create_auth_keyboard, get_readable_file_size
from database import db

@Client.on_message(filters.command("settings"))
async def settings_handler(client: Client, message: Message):
    """Handle /settings command"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    settings_text = (
        "⚙️ **bot settings**\n\n"
        "configure bot parameters and view system information"
    )
    
    await message.reply_text(
        settings_text,
        reply_markup=create_settings_keyboard(),
        quote=True
    )

@Client.on_callback_query(filters.regex("^settings_"))
async def settings_callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle settings callback queries"""
    user_id = callback_query.from_user.id
    
    if not Config.is_authorized(user_id):
        await callback_query.answer("⚠️ unauthorized access", show_alert=True)
        return
    
    data = callback_query.data.split("_", 1)[1]
    
    if data == "main":
        settings_text = (
            "⚙️ **bot settings**\n\n"
            "configure bot parameters and view system information"
        )
        await callback_query.edit_message_text(
            settings_text,
            reply_markup=create_settings_keyboard()
        )
    
    elif data == "paths":
        paths_text = (
            "📁 **path configuration**\n\n"
            f"**download path:** `{DOWNLOAD_PATH}`\n"
            f"**temp path:** `{TEMP_PATH}`\n"
            f"**log path:** `{LOG_PATH}`\n\n"
            "**disk usage:**\n"
        )
        
        try:
            # Get disk usage for each path
            for path_name, path in [("download", DOWNLOAD_PATH), ("temp", TEMP_PATH), ("logs", LOG_PATH)]:
                if os.path.exists(path):
                    total_size = 0
                    file_count = 0
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            try:
                                total_size += os.path.getsize(os.path.join(root, file))
                                file_count += 1
                            except:
                                pass
                    paths_text += f"• {path_name}: `{get_readable_file_size(total_size)}` ({file_count} files)\n"
        except Exception as e:
            paths_text += f"error calculating disk usage: `{str(e)}`"
        
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 back", callback_data="settings_main")]
        ])
        
        await callback_query.edit_message_text(paths_text, reply_markup=keyboard)
    
    elif data == "auth":
        await callback_query.edit_message_text(
            "👥 **authorization management**\n\n"
            "manage authorized users and groups",
            reply_markup=create_auth_keyboard()
        )
    
    elif data == "config":
        config_text = (
            "⚙️ **configuration**\n\n"
            f"**bot version:** `1.0.0`\n"
            f"**python version:** `3.11.9`\n"
            f"**command timeout:** `{Config.COMMAND_TIMEOUT}s`\n"
            f"**max file size:** `{get_readable_file_size(Config.MAX_FILE_SIZE)}`\n"
            f"**workers:** `{Config.WORKERS}`\n\n"
            "**installed tools:**\n"
            "• mkvmerge (mkvtoolnix)\n"
            "• ffmpeg\n"
            "• mediainfo\n"
            "• mp4decrypt\n"
            "• rclone\n"
            "• wget/curl"
        )
        
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 back", callback_data="settings_main")]
        ])
        
        await callback_query.edit_message_text(config_text, reply_markup=keyboard)
    
    elif data == "stats":
        try:
            # Get system stats
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            stats_text = (
                "📊 **system statistics**\n\n"
                f"**cpu usage:** `{cpu_percent}%`\n"
                f"**memory usage:** `{memory.percent}%`\n"
                f"**memory used:** `{get_readable_file_size(memory.used)}`\n"
                f"**memory total:** `{get_readable_file_size(memory.total)}`\n\n"
                f"**disk usage:** `{disk.percent}%`\n"
                f"**disk used:** `{get_readable_file_size(disk.used)}`\n"
                f"**disk total:** `{get_readable_file_size(disk.total)}`"
            )
        except ImportError:
            stats_text = (
                "📊 **system statistics**\n\n"
                "install `psutil` package to view system stats"
            )
        except Exception as e:
            stats_text = f"📊 **system statistics**\n\nerror: `{str(e)}`"
        
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 back", callback_data="settings_main")]
        ])
        
        await callback_query.edit_message_text(stats_text, reply_markup=keyboard)
    
    elif data == "close":
        await callback_query.message.delete()

@Client.on_callback_query(filters.regex("^auth_"))
async def auth_callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle auth callback queries"""
    user_id = callback_query.from_user.id
    
    if user_id != Config.OWNER_ID:
        await callback_query.answer("⚠️ owner access required", show_alert=True)
        return
    
    data = callback_query.data.split("_", 1)[1]
    
    if data == "users":
        try:
            auth_users = await db.get_auth_users()
            
            text = "👤 **authorized users**\n\n"
            if auth_users:
                for user in auth_users:
                    text += f"• `{user}`\n"
            else:
                text += "no authorized users"
            
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 back", callback_data="settings_auth")]
            ])
            
            await callback_query.edit_message_text(text, reply_markup=keyboard)
        except Exception as e:
            await callback_query.answer(f"error: {str(e)}", show_alert=True)
    
    elif data == "groups":
        try:
            auth_groups = await db.get_auth_groups()
            
            text = "👥 **authorized groups**\n\n"
            if auth_groups:
                for group in auth_groups:
                    text += f"• `{group}`\n"
            else:
                text += "no authorized groups"
            
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 back", callback_data="settings_auth")]
            ])
            
            await callback_query.edit_message_text(text, reply_markup=keyboard)
        except Exception as e:
            await callback_query.answer(f"error: {str(e)}", show_alert=True)

@Client.on_callback_query(filters.regex("^(help|status)$"))
async def general_callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle general callback queries"""
    user_id = callback_query.from_user.id
    
    if not Config.is_authorized(user_id):
        await callback_query.answer("⚠️ unauthorized access", show_alert=True)
        return
    
    if callback_query.data == "help":
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
            "• `/settings` - bot configuration"
        )
        
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 back", callback_data="back_to_start")]
        ])
        
        await callback_query.edit_message_text(help_text, reply_markup=keyboard)
    
    elif callback_query.data == "status":
        status_text = (
            "📊 **bot status**\n\n"
            "✅ **online and operational**\n\n"
            "**features available:**\n"
            "• terminal access\n"
            "• media processing\n"
            "• file management\n"
            "• cloud integration\n"
            "• authorization system"
        )
        
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 back", callback_data="back_to_start")]
        ])
        
        await callback_query.edit_message_text(status_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start_handler(client: Client, callback_query: CallbackQuery):
    """Handle back to start callback"""
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
    
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 help", callback_data="help"),
            InlineKeyboardButton("⚙️ settings", callback_data="settings_main")
        ],
        [InlineKeyboardButton("📊 status", callback_data="status")]
    ])
    
    await callback_query.edit_message_text(start_text, reply_markup=keyboard)