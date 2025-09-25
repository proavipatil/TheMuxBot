"""
Download manager plugin using aria2
"""

import asyncio
import json
import logging
import os
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

@Client.on_message(filters.command("dl"))
@auth_required
async def download_command(client: Client, message: Message):
    """Download files using aria2"""
    
    if len(message.command) < 2:
        await message.reply_text("usage: `/dl <url>`")
        return
        
    url = message.text.split(None, 1)[1]
    
    # Validate URL
    if not url.startswith(('http://', 'https://', 'ftp://', 'magnet:')):
        await message.reply_text("invalid url format")
        return
        
    status_msg = await message.reply_text(f"starting download...\n`{url}`")
    
    try:
        # Create aria2 command
        cmd = [
            'aria2c',
            '--dir', Config.DOWNLOAD_PATH,
            '--max-connection-per-server=16',
            '--max-concurrent-downloads=1',
            '--split=16',
            '--min-split-size=1M',
            '--continue=true',
            '--summary-interval=1',
            '--progress-summary-interval=1',
            url
        ]
        
        # Start aria2 process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Monitor download progress
        while process.returncode is None:
            try:
                # Check if process is still running
                await asyncio.wait_for(process.wait(), timeout=5)
                break
            except asyncio.TimeoutError:
                # Update status message
                await status_msg.edit_text(f"downloading...\n`{url}`")
                
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            await status_msg.edit_text(f"download completed\n`{url}`")
        else:
            error_msg = stderr.decode('utf-8', errors='ignore')
            await status_msg.edit_text(f"download failed\n`{error_msg[:500]}`")
            
    except Exception as e:
        await status_msg.edit_text(f"download error: `{str(e)}`")

@Client.on_message(filters.command("downloads"))
@auth_required
async def downloads_command(client: Client, message: Message):
    """List downloaded files"""
    
    try:
        download_path = Config.DOWNLOAD_PATH
        if not os.path.exists(download_path):
            await message.reply_text("download directory not found")
            return
            
        files = os.listdir(download_path)
        if not files:
            await message.reply_text("no downloads found")
            return
            
        result = f"**downloads** (`{len(files)}` files)\n\n"
        
        for file in sorted(files)[:20]:  # Limit to 20 files
            file_path = os.path.join(download_path, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                size_str = format_bytes(size)
                result += f"📄 `{file}` ({size_str})\n"
            elif os.path.isdir(file_path):
                result += f"📁 `{file}/`\n"
                
        if len(files) > 20:
            result += f"\n... and {len(files) - 20} more files"
            
        await message.reply_text(result)
        
    except Exception as e:
        await message.reply_text(f"error listing downloads: `{str(e)}`")

def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"