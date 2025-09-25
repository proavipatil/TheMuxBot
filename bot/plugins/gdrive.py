"""
Google Drive upload plugin using rclone
"""

import asyncio
import logging
import os
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message

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

@Client.on_message(filters.command("gup"))
@auth_required
async def gdrive_upload_command(client: Client, message: Message):
    """Upload files to Google Drive using rclone"""
    
    file_path = None
    
    # Check if replying to a media message
    if message.reply_to_message and message.reply_to_message.media:
        status_msg = await message.reply_text("downloading file...")
        
        try:
            file_path = await message.reply_to_message.download(
                file_name=f"{Config.TEMP_PATH}/"
            )
        except Exception as e:
            await status_msg.edit_text(f"download failed: `{str(e)}`")
            return
            
    # Check if file path provided
    elif len(message.command) > 1:
        input_path = message.text.split(None, 1)[1]
        file_path = input_path
        status_msg = await message.reply_text("preparing upload...")
    else:
        await message.reply_text("usage: `/gup <file_path>` or reply to media")
        return
        
    if not file_path or not os.path.exists(file_path):
        await status_msg.edit_text("file not found")
        return
        
    try:
        # Check if rclone is configured
        check_cmd = ['rclone', 'listremotes']
        check_process = await asyncio.create_subprocess_exec(
            *check_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await check_process.communicate()
        
        if check_process.returncode != 0:
            await status_msg.edit_text("rclone not configured. run `rclone config` first")
            return
            
        remotes = stdout.decode().strip().split('\n')
        if not remotes or not remotes[0]:
            await status_msg.edit_text("no rclone remotes found. configure google drive first")
            return
            
        # Use first remote (assuming it's Google Drive)
        remote = remotes[0].rstrip(':')
        
        await status_msg.edit_text(f"uploading to google drive...\n`{Path(file_path).name}`")
        
        # Upload using rclone
        upload_cmd = [
            'rclone',
            'copy',
            file_path,
            f'{remote}:MuxBot/',
            '--progress',
            '--stats', '1s'
        ]
        
        process = await asyncio.create_subprocess_exec(
            *upload_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Monitor upload progress
        while process.returncode is None:
            try:
                await asyncio.wait_for(process.wait(), timeout=10)
                break
            except asyncio.TimeoutError:
                await status_msg.edit_text(f"uploading to google drive...\n`{Path(file_path).name}`")
                
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            file_size = os.path.getsize(file_path)
            await status_msg.edit_text(
                f"**upload completed**\n\n"
                f"**file:** `{Path(file_path).name}`\n"
                f"**size:** `{format_bytes(file_size)}`\n"
                f"**location:** `{remote}:MuxBot/`"
            )
        else:
            error_msg = stderr.decode('utf-8', errors='ignore')
            await status_msg.edit_text(f"upload failed\n`{error_msg[:500]}`")
            
    except Exception as e:
        await status_msg.edit_text(f"upload error: `{str(e)}`")
    finally:
        # Clean up downloaded file if it was from Telegram
        if message.reply_to_message and message.reply_to_message.media:
            if os.path.exists(file_path):
                os.remove(file_path)

@Client.on_message(filters.command("glist"))
@auth_required
async def gdrive_list_command(client: Client, message: Message):
    """List files in Google Drive"""
    
    try:
        # Check rclone remotes
        check_cmd = ['rclone', 'listremotes']
        check_process = await asyncio.create_subprocess_exec(
            *check_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await check_process.communicate()
        
        if check_process.returncode != 0:
            await message.reply_text("rclone not configured")
            return
            
        remotes = stdout.decode().strip().split('\n')
        if not remotes or not remotes[0]:
            await message.reply_text("no rclone remotes found")
            return
            
        remote = remotes[0].rstrip(':')
        
        status_msg = await message.reply_text("listing google drive files...")
        
        # List files
        list_cmd = ['rclone', 'ls', f'{remote}:MuxBot/']
        
        process = await asyncio.create_subprocess_exec(
            *list_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            files_output = stdout.decode('utf-8', errors='ignore')
            
            if not files_output.strip():
                await status_msg.edit_text("no files found in MuxBot folder")
                return
                
            lines = files_output.strip().split('\n')
            result = f"**google drive files** (`{len(lines)}` files)\n\n"
            
            for line in lines[:20]:  # Limit to 20 files
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    size_str = format_bytes(int(parts[0]))
                    filename = parts[1]
                    result += f"📄 `{filename}` ({size_str})\n"
                    
            if len(lines) > 20:
                result += f"\n... and {len(lines) - 20} more files"
                
            await status_msg.edit_text(result)
        else:
            error_msg = stderr.decode('utf-8', errors='ignore')
            await status_msg.edit_text(f"list failed\n`{error_msg[:500]}`")
            
    except Exception as e:
        await message.reply_text(f"error listing files: `{str(e)}`")

def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"