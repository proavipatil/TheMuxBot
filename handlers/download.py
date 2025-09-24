"""Download handlers with aria2"""

import os
import asyncio
import math
from pathlib import Path
from subprocess import PIPE, Popen
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config, DOWNLOAD_PATH, COMMAND_TIMEOUT
from utils import run_command, get_readable_file_size
from utils.logger import log_to_channel
from utils.gdrive import gdrive
import aria2p
import requests

def subprocess_run(cmd):
    """Run subprocess command"""
    subproc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True)
    talk = subproc.communicate()
    exitCode = subproc.returncode
    if exitCode != 0:
        return None
    return talk

def aria_start():
    """Start aria2 daemon"""
    trackers_list = requests.get(
        "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
    ).text.replace("\n\n", ",")
    trackers = f"[{trackers_list}]"
    
    cmd = f"""aria2c \
          --enable-rpc \
          --rpc-listen-all=false \
          --rpc-listen-port=6800 \
          --max-connection-per-server=10 \
          --rpc-max-request-size=1024M \
          --check-certificate=false \
          --follow-torrent=mem \
          --seed-time=0 \
          --max-upload-limit=1K \
          --max-concurrent-downloads=5 \
          --min-split-size=10M \
          --split=10 \
          --bt-tracker={trackers} \
          --daemon=true \
          --allow-overwrite=true"""
    
    subprocess_run(cmd)
    aria2 = aria2p.API(
        aria2p.Client(host="http://localhost", port=6800, secret="")
    )
    return aria2

# Initialize aria2 client
try:
    aria2p_client = aria_start()
except:
    aria2p_client = None

async def check_progress_for_dl(gid, message: Message, previous):
    """Check download progress"""
    complete = False
    while not complete:
        try:
            t_file = aria2p_client.get_download(gid)
        except:
            return await message.edit("download cancelled by user")
        
        complete = t_file.is_complete
        
        try:
            if t_file.error_message:
                await message.edit(f"❌ **download failed**\n\n`{t_file.error_message}`")
                return
            
            if not complete and not t_file.error_message:
                percentage = int(t_file.progress)
                downloaded = percentage * int(t_file.total_length) / 100
                
                progress_bar = "█" * (percentage // 10) + "░" * (10 - percentage // 10)
                
                msg = (
                    f"📥 **downloading**\n\n"
                    f"**name:** `{t_file.name}`\n"
                    f"**progress:** `[{progress_bar}] {percentage}%`\n"
                    f"**completed:** `{get_readable_file_size(int(downloaded))}`\n"
                    f"**total:** `{t_file.total_length_string()}`\n"
                    f"**speed:** `{t_file.download_speed_string()}`\n"
                    f"**connections:** `{t_file.connections}`\n"
                    f"**eta:** `{t_file.eta_string()}`\n"
                    f"**gid:** `{gid}`"
                )
                
                if msg != previous:
                    await message.edit(msg)
                    previous = msg
            else:
                if complete and not t_file.name.lower().startswith("[metadata]"):
                    file_path = os.path.join(t_file.dir, t_file.name)
                    
                    # Log to channel
                    await log_to_channel(
                        message._client,
                        f"📥 **Download Completed**\n\n**File:** `{t_file.name}`\n**Size:** `{t_file.total_length_string()}`",
                        file_path if os.path.getsize(file_path) < 50*1024*1024 else None
                    )
                    
                    # Upload to Google Drive if enabled
                    gdrive_link = await gdrive.upload_file(file_path, t_file.name)
                    gdrive_text = f"\n**gdrive:** {gdrive_link}" if gdrive_link else ""
                    
                    return await message.edit(
                        f"✅ **download completed**\n\n"
                        f"**name:** `{t_file.name}`\n"
                        f"**size:** `{t_file.total_length_string()}`\n"
                        f"**path:** `{file_path}`{gdrive_text}"
                    )
            
            await asyncio.sleep(2)
            await check_progress_for_dl(gid, message, previous)
            
        except Exception as e:
            if "not found" in str(e):
                await message.edit(f"❌ **download cancelled**\n\n`{t_file.name}`")
            elif "depth exceeded" in str(e):
                t_file.remove(force=True)
                await message.edit(f"❌ **download failed**\n\n`{t_file.name}`\ntorrent/link is dead")

@Client.on_message(filters.command("dl"))
async def aria_download(client: Client, message: Message):
    """Handle /dl command for aria2 downloads"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    if not aria2p_client:
        await message.reply_text("❌ **aria2 not available**", quote=True)
        return
    
    myoptions = {
        "dir": DOWNLOAD_PATH
    }
    
    # Check if replying to torrent file
    if (message.reply_to_message and 
        message.reply_to_message.document and 
        message.reply_to_message.document.file_name.lower().endswith('.torrent')):
        
        status_msg = await message.reply_text("📥 **downloading torrent file...**", quote=True)
        
        try:
            resource = await message.reply_to_message.download(DOWNLOAD_PATH)
            download = aria2p_client.add_torrent(resource, options=myoptions)
        except Exception as e:
            await status_msg.edit(f"❌ **error:** `{str(e)}`")
            return
    
    # Check if URL/magnet provided
    elif message.input_str:
        resource = message.input_str.strip()
        status_msg = await message.reply_text("📥 **adding to download queue...**", quote=True)
        
        try:
            if resource.lower().startswith("http"):
                download = aria2p_client.add_uris([resource], options=myoptions)
            elif resource.lower().startswith("magnet:"):
                download = aria2p_client.add_magnet(resource, options=myoptions)
            else:
                await status_msg.edit("❌ **invalid url or magnet link**")
                return
        except Exception as e:
            await status_msg.edit(f"❌ **error:** `{str(e)}`")
            return
    else:
        await message.reply_text(
            "**usage:** `/dl <url/magnet>` or reply to torrent file\n\n"
            "**examples:**\n"
            "• `/dl https://example.com/file.zip`\n"
            "• `/dl magnet:?xt=urn:btih:...`",
            quote=True
        )
        return
    
    gid = download.gid
    await status_msg.edit("⚡ **starting download...**")
    await check_progress_for_dl(gid=gid, message=status_msg, previous="")

@Client.on_message(filters.command("aclear"))
async def aria_clear(client: Client, message: Message):
    """Handle /aclear command"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    if not aria2p_client:
        await message.reply_text("❌ **aria2 not available**", quote=True)
        return
    
    try:
        aria2p_client.remove_all(force=True)
        aria2p_client.purge()
        await message.reply_text("✅ **cleared all downloads**", quote=True)
    except Exception as e:
        await message.reply_text(f"❌ **error:** `{str(e)}`", quote=True)

@Client.on_message(filters.command("acancel"))
async def aria_cancel(client: Client, message: Message):
    """Handle /acancel command"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    if not aria2p_client:
        await message.reply_text("❌ **aria2 not available**", quote=True)
        return
    
    if not message.input_str:
        await message.reply_text(
            "**usage:** `/acancel <gid>`\n\n"
            "**example:** `/acancel nf5bgi7g`",
            quote=True
        )
        return
    
    gid = message.input_str.strip()
    
    try:
        download = aria2p_client.get_download(gid)
        file_name = download.name
        aria2p_client.remove(downloads=[download], force=True, files=True, clean=True)
        await message.reply_text(
            f"✅ **download cancelled**\n\n`{file_name}`",
            quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ **gid not found:** `{gid}`", quote=True)

@Client.on_message(filters.command("ashow"))
async def aria_show(client: Client, message: Message):
    """Handle /ashow command"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    if not aria2p_client:
        await message.reply_text("❌ **aria2 not available**", quote=True)
        return
    
    try:
        downloads = aria2p_client.get_downloads()
        
        if not downloads:
            await message.reply_text("📭 **no active downloads**", quote=True)
            return
        
        msg = "📥 **active downloads**\n\n"
        
        for download in downloads:
            if str(download.status) != "complete":
                msg += (
                    f"**file:** `{download.name}`\n"
                    f"**speed:** `{download.download_speed_string()}`\n"
                    f"**progress:** `{download.progress_string()}`\n"
                    f"**size:** `{download.total_length_string()}`\n"
                    f"**status:** `{download.status}`\n"
                    f"**eta:** `{download.eta_string()}`\n"
                    f"**gid:** `{download.gid}`\n\n"
                )
        
        await message.reply_text(msg, quote=True)
        
    except Exception as e:
        await message.reply_text(f"❌ **error:** `{str(e)}`", quote=True)