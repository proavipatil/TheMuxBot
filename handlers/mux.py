"""Video muxing handlers"""

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config, DOWNLOAD_PATH, TEMP_PATH
from utils import run_command, format_code_block, truncate_text, get_readable_file_size

@Client.on_message(filters.command("mux"))
async def mux_handler(client: Client, message: Message):
    """Handle /mux command for video muxing operations"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    mux_text = (
        "🎬 **video muxing tools**\n\n"
        "select muxing operation:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎥 merge video", callback_data="mux_merge"),
            InlineKeyboardButton("🎵 add audio", callback_data="mux_audio")
        ],
        [
            InlineKeyboardButton("📝 add subtitles", callback_data="mux_subs"),
            InlineKeyboardButton("📊 metadata", callback_data="mux_meta")
        ],
        [
            InlineKeyboardButton("🔧 custom mux", callback_data="mux_custom"),
            InlineKeyboardButton("❌ close", callback_data="mux_close")
        ]
    ])
    
    await message.reply_text(mux_text, reply_markup=keyboard, quote=True)

@Client.on_message(filters.command("extract"))
async def extract_handler(client: Client, message: Message):
    """Handle /extract command for extracting streams"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    if len(message.command) < 2:
        await message.reply_text(
            "**usage:** `/extract <file_path> [stream_type]`\n\n"
            "**stream types:**\n"
            "• `video` - extract video stream\n"
            "• `audio` - extract audio streams\n"
            "• `subs` - extract subtitle streams\n"
            "• `all` - extract all streams",
            quote=True
        )
        return
    
    args = message.text.split()[1:]
    file_path = args[0]
    stream_type = args[1] if len(args) > 1 else "all"
    
    if not os.path.exists(file_path):
        await message.reply_text(f"❌ **file not found:** `{file_path}`", quote=True)
        return
    
    status_msg = await message.reply_text("🔍 **extracting streams...**", quote=True)
    
    try:
        filename = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(TEMP_PATH, f"extracted_{filename}")
        os.makedirs(output_dir, exist_ok=True)
        
        if stream_type == "video":
            command = f'mkvextract tracks "{file_path}" 0:"{output_dir}/video.mkv"'
        elif stream_type == "audio":
            command = f'mkvextract tracks "{file_path}" 1:"{output_dir}/audio.mka"'
        elif stream_type == "subs":
            command = f'mkvextract tracks "{file_path}" 2:"{output_dir}/subtitles.srt"'
        else:  # all
            command = f'mkvextract tracks "{file_path}" 0:"{output_dir}/video.mkv" 1:"{output_dir}/audio.mka" 2:"{output_dir}/subtitles.srt"'
        
        stdout, stderr, returncode = await run_command(command)
        
        if returncode == 0:
            extracted_files = os.listdir(output_dir)
            files_info = []
            
            for file in extracted_files:
                file_path_full = os.path.join(output_dir, file)
                size = get_readable_file_size(os.path.getsize(file_path_full))
                files_info.append(f"• `{file}` ({size})")
            
            await status_msg.edit_text(
                f"✅ **extraction completed**\n\n"
                f"**output directory:** `{output_dir}`\n\n"
                f"**extracted files:**\n" + "\n".join(files_info)
            )
        else:
            await status_msg.edit_text(
                f"❌ **extraction failed**\n\n"
                f"**error:** `{stderr if stderr else 'unknown error'}`"
            )
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **error:** `{str(e)}`")

@Client.on_message(filters.command("decrypt"))
async def decrypt_handler(client: Client, message: Message):
    """Handle /decrypt command for mp4decrypt"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    if len(message.command) < 3:
        await message.reply_text(
            "**usage:** `/decrypt <input_file> <key> [output_file]`\n\n"
            "**example:** `/decrypt encrypted.mp4 1234567890abcdef decrypted.mp4`",
            quote=True
        )
        return
    
    args = message.text.split()[1:]
    input_file = args[0]
    key = args[1]
    output_file = args[2] if len(args) > 2 else f"decrypted_{os.path.basename(input_file)}"
    
    if not os.path.exists(input_file):
        await message.reply_text(f"❌ **file not found:** `{input_file}`", quote=True)
        return
    
    status_msg = await message.reply_text("🔓 **decrypting file...**", quote=True)
    
    try:
        output_path = os.path.join(TEMP_PATH, output_file)
        command = f'mp4decrypt --key {key} "{input_file}" "{output_path}"'
        
        stdout, stderr, returncode = await run_command(command)
        
        if returncode == 0 and os.path.exists(output_path):
            file_size = get_readable_file_size(os.path.getsize(output_path))
            await status_msg.edit_text(
                f"✅ **decryption completed**\n\n"
                f"**input:** `{os.path.basename(input_file)}`\n"
                f"**output:** `{output_file}`\n"
                f"**size:** `{file_size}`\n"
                f"**path:** `{output_path}`"
            )
        else:
            await status_msg.edit_text(
                f"❌ **decryption failed**\n\n"
                f"**error:** `{stderr if stderr else 'unknown error'}`"
            )
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **error:** `{str(e)}`")

@Client.on_callback_query(filters.regex("^mux_"))
async def mux_callback_handler(client: Client, callback_query):
    """Handle mux callback queries"""
    user_id = callback_query.from_user.id
    
    if not Config.is_authorized(user_id):
        await callback_query.answer("⚠️ unauthorized access", show_alert=True)
        return
    
    data = callback_query.data.split("_", 1)[1]
    
    if data == "merge":
        text = (
            "🎥 **merge video files**\n\n"
            "use: `/term mkvmerge -o output.mkv input1.mkv + input2.mkv`\n\n"
            "this will merge multiple video files into one"
        )
    elif data == "audio":
        text = (
            "🎵 **add audio track**\n\n"
            "use: `/term mkvmerge -o output.mkv video.mkv audio.mka`\n\n"
            "this will add audio track to video file"
        )
    elif data == "subs":
        text = (
            "📝 **add subtitles**\n\n"
            "use: `/term mkvmerge -o output.mkv video.mkv subtitles.srt`\n\n"
            "this will add subtitle track to video file"
        )
    elif data == "meta":
        text = (
            "📊 **add metadata**\n\n"
            "use: `/term mkvmerge -o output.mkv --title \"Movie Title\" video.mkv`\n\n"
            "this will add metadata to video file"
        )
    elif data == "custom":
        text = (
            "🔧 **custom muxing**\n\n"
            "**common mkvmerge commands:**\n"
            "• merge: `mkvmerge -o out.mkv in1.mkv + in2.mkv`\n"
            "• add audio: `mkvmerge -o out.mkv video.mkv audio.mka`\n"
            "• add subs: `mkvmerge -o out.mkv video.mkv subs.srt`\n"
            "• set title: `mkvmerge -o out.mkv --title \"Title\" in.mkv`\n"
            "• extract: `mkvextract tracks in.mkv 0:video.mkv`\n\n"
            "use `/term` command to execute custom mkvmerge operations"
        )
    elif data == "close":
        await callback_query.message.delete()
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 back", callback_data="mux_back")]
    ])
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^mux_back$"))
async def mux_back_handler(client: Client, callback_query):
    """Handle mux back callback"""
    mux_text = (
        "🎬 **video muxing tools**\n\n"
        "select muxing operation:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎥 merge video", callback_data="mux_merge"),
            InlineKeyboardButton("🎵 add audio", callback_data="mux_audio")
        ],
        [
            InlineKeyboardButton("📝 add subtitles", callback_data="mux_subs"),
            InlineKeyboardButton("📊 metadata", callback_data="mux_meta")
        ],
        [
            InlineKeyboardButton("🔧 custom mux", callback_data="mux_custom"),
            InlineKeyboardButton("❌ close", callback_data="mux_close")
        ]
    ])
    
    await callback_query.edit_message_text(mux_text, reply_markup=keyboard)