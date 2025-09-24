"""File management handlers"""

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config, DOWNLOAD_PATH
from utils import run_command, format_code_block, truncate_text, get_readable_file_size
from utils.logger import log_to_channel
from utils.gdrive import gdrive
from html_telegraph_poster import TelegraphPoster

def post_to_telegraph(title: str, content: str) -> str:
    """Create a Telegraph post"""
    try:
        post_client = TelegraphPoster(use_api=True)
        post_client.create_api_token("TheBot")
        post_page = post_client.post(
            title=title,
            author="TheBot",
            author_url="",
            text=content,
        )
        return post_page["url"]
    except:
        return None

def safe_filename(path_):
    """Remove quotes from filename"""
    if path_ is None:
        return None
    safename = path_.replace("'", "").replace('"', "")
    if safename != path_:
        try:
            os.rename(path_, safename)
            return safename
        except:
            return path_
    return safename

@Client.on_message(filters.command("mi"))
async def mediainfo_handler(client: Client, message: Message):
    """Handle /mi command for media information"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    file_path = None
    is_url = False
    is_downloaded = False
    
    # Check if replying to media
    if message.reply_to_message:
        reply = message.reply_to_message
        available_media = (
            "audio", "document", "photo", "sticker", 
            "animation", "video", "voice", "video_note"
        )
        
        x_media = None
        for kind in available_media:
            x_media = getattr(reply, kind, None)
            if x_media is not None:
                break
        
        if x_media is None:
            await message.reply_text("❌ **reply to a valid media file**", quote=True)
            return
        
        status_msg = await message.reply_text("📥 **downloading file...**", quote=True)
        try:
            file_path = await reply.download(DOWNLOAD_PATH)
            file_path = safe_filename(file_path)
            is_downloaded = True
            await status_msg.edit_text("🔍 **analyzing media...**")
        except Exception as e:
            await status_msg.edit_text(f"❌ **download failed:** `{str(e)}`")
            return
    
    # Check if URL provided
    elif message.input_str:
        input_text = message.input_str.strip()
        
        if input_text.startswith("http"):
            is_url = True
            status_msg = await message.reply_text("🔍 **analyzing remote media...**", quote=True)
            
            # Try direct mediainfo on URL
            command = f'mediainfo "{input_text}"'
            stdout, stderr, returncode = await run_command(command)
            
            if returncode != 0 or not stdout.strip():
                # Try downloading first few MB for analysis
                ext = input_text.split('.')[-1] if '.' in input_text else 'tmp'
                temp_file = os.path.join(DOWNLOAD_PATH, f"temp_analysis.{ext}")
                
                curl_cmd = f'curl --silent "{input_text}" | head --bytes 10M > "{temp_file}" && mediainfo "{temp_file}"'
                stdout, stderr, returncode = await run_command(curl_cmd)
                
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        # Check if local file path
        elif os.path.exists(input_text):
            file_path = input_text
            status_msg = await message.reply_text("🔍 **analyzing media...**", quote=True)
            command = f'mediainfo "{file_path}"'
            stdout, stderr, returncode = await run_command(command)
        
        else:
            await message.reply_text(
                f"❌ **file not found:** `{input_text}`",
                quote=True
            )
            return
    
    else:
        await message.reply_text(
            "**usage:** `/mi <file_path/url>` or reply to a media file\n\n"
            "**examples:**\n"
            "• `/mi /path/to/video.mp4`\n"
            "• `/mi https://example.com/video.mp4`\n"
            "• Reply to any media file",
            quote=True
        )
        return
    
    try:
        # Get mediainfo output
        if not is_url and file_path:
            command = f'mediainfo "{file_path}"'
            stdout, stderr, returncode = await run_command(command)
        
        if returncode == 0 and stdout.strip():
            # Create telegraph post for detailed info
            body_text = f"""
<h2>MEDIA INFORMATION</h2>
<pre>{stdout}</pre>
"""
            
            telegraph_link = post_to_telegraph("MediaInfo", body_text)
            
            if telegraph_link:
                filename = os.path.basename(file_path) if file_path else "remote file"
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 detailed info", url=telegraph_link)]
                ])
                
                await status_msg.edit_text(
                    f"📊 **media information**\n\n"
                    f"**file:** `{filename}`\n\n"
                    f"**summary:** media analysis completed\n"
                    f"**details:** click button below for full report",
                    reply_markup=keyboard
                )
            else:
                # Fallback to text output
                await status_msg.edit_text(
                    f"📊 **media information**\n\n"
                    f"{format_code_block(truncate_text(stdout))}"
                )
        else:
            await status_msg.edit_text(
                f"❌ **mediainfo failed**\n\n"
                f"**error:** `{stderr if stderr else 'unsupported format'}`"
            )
        
        # Clean up downloaded file
        if is_downloaded and file_path:
            try:
                os.remove(file_path)
            except:
                pass
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **error:** `{str(e)}`")

@Client.on_message(filters.command("gup"))
async def google_upload_handler(client: Client, message: Message):
    """Handle /gup command for Google Drive upload"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    file_path = None
    
    # Check if replying to a document
    if message.reply_to_message and message.reply_to_message.document:
        status_msg = await message.reply_text("📥 **downloading file...**", quote=True)
        try:
            file_path = await message.reply_to_message.download(DOWNLOAD_PATH)
            await status_msg.edit_text("☁️ **uploading to google drive...**")
        except Exception as e:
            await status_msg.edit_text(f"❌ **download failed:** `{str(e)}`")
            return
    
    # Check if file path provided
    elif len(message.command) > 1:
        file_path = message.text.split(None, 1)[1]
        if not os.path.exists(file_path):
            await message.reply_text(f"❌ **file not found:** `{file_path}`", quote=True)
            return
        status_msg = await message.reply_text("☁️ **uploading to google drive...**", quote=True)
    
    else:
        await message.reply_text(
            "**usage:** `/gup <file_path>` or reply to a file",
            quote=True
        )
        return
    
    try:
        # Use rclone to upload to Google Drive
        filename = os.path.basename(file_path)
        command = f'rclone copy "{file_path}" gdrive: -P'
        
        stdout, stderr, returncode = await run_command(command, timeout=1800)  # 30 minutes timeout
        
        if returncode == 0:
            # Clean up downloaded file if it was downloaded
            if message.reply_to_message and message.reply_to_message.document:
                try:
                    os.remove(file_path)
                except:
                    pass
            
            file_size = get_readable_file_size(os.path.getsize(file_path)) if os.path.exists(file_path) else "unknown"
            
            await status_msg.edit_text(
                f"✅ **upload successful**\n\n"
                f"**file:** `{filename}`\n"
                f"**size:** `{file_size}`\n"
                f"**destination:** google drive"
            )
        else:
            await status_msg.edit_text(
                f"❌ **upload failed**\n\n"
                f"**file:** `{filename}`\n"
                f"**error:** `{stderr if stderr else 'unknown error'}`"
            )
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **error:** `{str(e)}`")

@Client.on_message(filters.command("wget"))
async def wget_handler(client: Client, message: Message):
    """Handle /wget command for simple downloads"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    if not message.input_str:
        await message.reply_text(
            "**usage:** `/wget <url>`\n\n"
            "**example:** `/wget https://example.com/file.mp4`\n\n"
            "**note:** for advanced downloads with progress, use `/dl`",
            quote=True
        )
        return
    
    url = message.input_str.strip()
    status_msg = await message.reply_text(f"📥 **downloading...**\n\n`{url}`", quote=True)
    
    try:
        filename = url.split('/')[-1] or 'downloaded_file'
        output_path = os.path.join(DOWNLOAD_PATH, filename)
        
        command = f'wget -O "{output_path}" "{url}"'
        stdout, stderr, returncode = await run_command(command, timeout=1800)
        
        if returncode == 0 and os.path.exists(output_path):
            file_size = get_readable_file_size(os.path.getsize(output_path))
            
            # Log to channel
            await log_to_channel(
                client,
                f"📥 **File Downloaded**\n\n**File:** `{filename}`\n**Size:** `{file_size}`",
                output_path if os.path.getsize(output_path) < 50*1024*1024 else None
            )
            
            # Upload to Google Drive if enabled
            gdrive_link = await gdrive.upload_file(output_path, filename)
            gdrive_text = f"\n**gdrive:** {gdrive_link}" if gdrive_link else ""
            
            await status_msg.edit_text(
                f"✅ **download completed**\n\n"
                f"**file:** `{filename}`\n"
                f"**size:** `{file_size}`\n"
                f"**path:** `{output_path}`{gdrive_text}"
            )
        else:
            await status_msg.edit_text(
                f"❌ **download failed**\n\n"
                f"**url:** `{url}`\n"
                f"**error:** `{stderr if stderr else 'unknown error'}`"
            )
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **error:** `{str(e)}`")