"""
Media info plugin
"""

import asyncio
import json
import logging
import os
import subprocess
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

@Client.on_message(filters.command("mi"))
@auth_required
async def media_info_command(client: Client, message: Message):
    """Get media information"""
    
    file_path = None
    
    # Check if replying to a media message
    if message.reply_to_message and message.reply_to_message.media:
        status_msg = await message.reply_text("downloading media...")
        
        try:
            file_path = await message.reply_to_message.download(
                file_name=f"{Config.TEMP_PATH}/"
            )
        except Exception as e:
            await status_msg.edit_text(f"download failed: `{str(e)}`")
            return
            
    # Check if file path or URL provided
    elif len(message.command) > 1:
        input_path = message.text.split(None, 1)[1]
        
        if input_path.startswith(('http://', 'https://')):
            status_msg = await message.reply_text("downloading from url...")
            # For URLs, we'd need to implement download logic
            await status_msg.edit_text("url download not implemented yet")
            return
        else:
            file_path = input_path
            status_msg = await message.reply_text("analyzing media...")
    else:
        await message.reply_text("usage: `/mi <file_path>` or reply to media")
        return
        
    if not file_path or not os.path.exists(file_path):
        await status_msg.edit_text("file not found")
        return
        
    try:
        # Use ffprobe to get media info
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            await status_msg.edit_text(f"ffprobe error: `{stderr.decode()}`")
            return
            
        media_info = json.loads(stdout.decode())
        
        # Format the output
        result = format_media_info(media_info, file_path)
        
        # Send as file if too long
        if len(result) > Config.MAX_MESSAGE_LENGTH:
            output_file = f"{Config.TEMP_PATH}/mediainfo.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
                
            await status_msg.delete()
            await message.reply_document(
                output_file,
                caption=f"media info for: `{Path(file_path).name}`"
            )
            os.remove(output_file)
        else:
            await status_msg.edit_text(result)
            
    except Exception as e:
        await status_msg.edit_text(f"error analyzing media: `{str(e)}`")
    finally:
        # Clean up downloaded file
        if message.reply_to_message and message.reply_to_message.media:
            if os.path.exists(file_path):
                os.remove(file_path)

def format_media_info(info, file_path):
    """Format media info for display"""
    
    result = f"**media information**\n\n"
    result += f"**file:** `{Path(file_path).name}`\n"
    
    # Format info
    format_info = info.get('format', {})
    if format_info:
        result += f"**format:** `{format_info.get('format_name', 'unknown')}`\n"
        
        duration = format_info.get('duration')
        if duration:
            result += f"**duration:** `{format_duration(float(duration))}`\n"
            
        size = format_info.get('size')
        if size:
            result += f"**size:** `{format_bytes(int(size))}`\n"
            
        bitrate = format_info.get('bit_rate')
        if bitrate:
            result += f"**bitrate:** `{int(bitrate)//1000} kbps`\n"
    
    result += "\n**streams:**\n"
    
    # Stream info
    streams = info.get('streams', [])
    for i, stream in enumerate(streams):
        codec_type = stream.get('codec_type', 'unknown')
        codec_name = stream.get('codec_name', 'unknown')
        
        result += f"\n**stream {i}:** `{codec_type}`\n"
        result += f"**codec:** `{codec_name}`\n"
        
        if codec_type == 'video':
            width = stream.get('width')
            height = stream.get('height')
            if width and height:
                result += f"**resolution:** `{width}x{height}`\n"
                
            fps = stream.get('r_frame_rate', '0/0')
            if fps and '/' in fps:
                try:
                    num, den = map(int, fps.split('/'))
                    if den != 0:
                        result += f"**fps:** `{num/den:.2f}`\n"
                except:
                    pass
                    
        elif codec_type == 'audio':
            sample_rate = stream.get('sample_rate')
            if sample_rate:
                result += f"**sample rate:** `{sample_rate} hz`\n"
                
            channels = stream.get('channels')
            if channels:
                result += f"**channels:** `{channels}`\n"
    
    return result

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"