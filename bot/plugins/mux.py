"""
Video muxing plugin using mkvmerge
"""

import asyncio
import logging
import os
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import Config

logger = logging.getLogger(__name__)

def auth_required(func):
    """Decorator to check authorization"""
    async def wrapper(client: Client, message: Message):
        if not client.is_authorized(message.from_user.id, message.chat.id):
            await message.reply_text("unauthorized access")
            return
        return await func(client, message)
    return wrapper

@Client.on_message(filters.command("mux"))
@auth_required
async def mux_command(client: Client, message: Message):
    """Video muxing operations"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("merge videos", callback_data="mux_merge"),
            InlineKeyboardButton("add subtitles", callback_data="mux_subs")
        ],
        [
            InlineKeyboardButton("add audio", callback_data="mux_audio"),
            InlineKeyboardButton("extract streams", callback_data="mux_extract")
        ],
        [
            InlineKeyboardButton("help", callback_data="mux_help"),
            InlineKeyboardButton("close", callback_data="close")
        ]
    ])
    
    mux_text = """**video muxing operations**

select an operation to perform:

• **merge videos** - combine multiple video files
• **add subtitles** - add subtitle tracks to video
• **add audio** - add audio tracks to video  
• **extract streams** - extract video/audio/subtitle streams

**tools used:**
• mkvmerge (mkvtoolnix)
• ffmpeg
• mediainfo"""

    await message.reply_text(
        mux_text,
        reply_markup=keyboard
    )

@Client.on_message(filters.command("merge"))
@auth_required
async def merge_videos_command(client: Client, message: Message):
    """Merge multiple video files"""
    
    if len(message.command) < 3:
        await message.reply_text(
            "usage: `/merge <output_name> <file1> <file2> [file3...]`\n\n"
            "example: `/merge merged.mkv video1.mp4 video2.mp4`"
        )
        return
        
    args = message.text.split()[1:]
    output_name = args[0]
    input_files = args[1:]
    
    # Validate input files
    missing_files = []
    for file in input_files:
        if not os.path.exists(file):
            missing_files.append(file)
            
    if missing_files:
        await message.reply_text(f"files not found: `{', '.join(missing_files)}`")
        return
        
    status_msg = await message.reply_text(f"merging {len(input_files)} files...")
    
    try:
        # Build mkvmerge command
        output_path = os.path.join(Config.DOWNLOAD_PATH, output_name)
        
        cmd = ['mkvmerge', '-o', output_path]
        
        # Add input files
        for i, file in enumerate(input_files):
            if i == 0:
                cmd.append(file)
            else:
                cmd.extend(['+', file])
                
        # Execute merge
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            file_size = os.path.getsize(output_path)
            await status_msg.edit_text(
                f"**merge completed**\n\n"
                f"**output:** `{output_name}`\n"
                f"**size:** `{format_bytes(file_size)}`\n"
                f"**location:** `{Config.DOWNLOAD_PATH}`"
            )
        else:
            error_msg = stderr.decode('utf-8', errors='ignore')
            await status_msg.edit_text(f"merge failed\n`{error_msg[:500]}`")
            
    except Exception as e:
        await status_msg.edit_text(f"merge error: `{str(e)}`")

@Client.on_message(filters.command("addsubs"))
@auth_required
async def add_subtitles_command(client: Client, message: Message):
    """Add subtitles to video"""
    
    if len(message.command) < 4:
        await message.reply_text(
            "usage: `/addsubs <video_file> <subtitle_file> <output_name>`\n\n"
            "example: `/addsubs video.mp4 subs.srt output.mkv`"
        )
        return
        
    args = message.text.split()[1:]
    video_file = args[0]
    subtitle_file = args[1]
    output_name = args[2]
    
    # Validate files
    if not os.path.exists(video_file):
        await message.reply_text(f"video file not found: `{video_file}`")
        return
        
    if not os.path.exists(subtitle_file):
        await message.reply_text(f"subtitle file not found: `{subtitle_file}`")
        return
        
    status_msg = await message.reply_text("adding subtitles...")
    
    try:
        output_path = os.path.join(Config.DOWNLOAD_PATH, output_name)
        
        # Build mkvmerge command
        cmd = [
            'mkvmerge',
            '-o', output_path,
            video_file,
            subtitle_file
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            file_size = os.path.getsize(output_path)
            await status_msg.edit_text(
                f"**subtitles added**\n\n"
                f"**output:** `{output_name}`\n"
                f"**size:** `{format_bytes(file_size)}`\n"
                f"**location:** `{Config.DOWNLOAD_PATH}`"
            )
        else:
            error_msg = stderr.decode('utf-8', errors='ignore')
            await status_msg.edit_text(f"operation failed\n`{error_msg[:500]}`")
            
    except Exception as e:
        await status_msg.edit_text(f"error: `{str(e)}`")

def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"