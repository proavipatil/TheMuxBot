"""Terminal command handlers"""

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config, COMMAND_TIMEOUT
from utils import run_command, format_code_block, truncate_text

@Client.on_message(filters.command("term"))
async def terminal_handler(client: Client, message: Message):
    """Handle /term command"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    if len(message.command) < 2:
        await message.reply_text(
            "**usage:** `/term <command>`\n\n"
            "**example:** `/term ls -la`",
            quote=True
        )
        return
    
    command = message.text.split(None, 1)[1]
    
    # Security check - block dangerous commands
    dangerous_commands = ['rm -rf', 'format', 'del /f', 'shutdown', 'reboot', 'halt']
    if any(dangerous in command.lower() for dangerous in dangerous_commands):
        await message.reply_text("⚠️ **dangerous command blocked**", quote=True)
        return
    
    status_msg = await message.reply_text(
        f"⚡ **executing command**\n\n`{command}`\n\nplease wait...",
        quote=True
    )
    
    try:
        stdout, stderr, returncode = await run_command(command, COMMAND_TIMEOUT)
        
        if returncode == 0:
            if stdout.strip():
                output = format_code_block(truncate_text(stdout))
                await status_msg.edit_text(
                    f"✅ **command executed successfully**\n\n"
                    f"**command:** `{command}`\n\n"
                    f"**output:**\n{output}"
                )
            else:
                await status_msg.edit_text(
                    f"✅ **command executed successfully**\n\n"
                    f"**command:** `{command}`\n\n"
                    f"**output:** no output"
                )
        else:
            error_output = stderr if stderr.strip() else "unknown error"
            await status_msg.edit_text(
                f"❌ **command failed**\n\n"
                f"**command:** `{command}`\n"
                f"**exit code:** `{returncode}`\n\n"
                f"**error:**\n{format_code_block(truncate_text(error_output))}"
            )
            
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **execution error**\n\n"
            f"**command:** `{command}`\n\n"
            f"**error:** `{str(e)}`"
        )

@Client.on_message(filters.command("ls"))
async def list_directory_handler(client: Client, message: Message):
    """Handle /ls command"""
    user_id = message.from_user.id
    
    if not Config.is_authorized(user_id, message.chat.id):
        await message.reply_text("⚠️ **unauthorized access**", quote=True)
        return
    
    path = "."
    if len(message.command) > 1:
        path = message.text.split(None, 1)[1]
    
    try:
        if not os.path.exists(path):
            await message.reply_text(f"❌ **path not found:** `{path}`", quote=True)
            return
        
        if os.path.isfile(path):
            file_size = os.path.getsize(path)
            from utils import get_readable_file_size
            await message.reply_text(
                f"📄 **file information**\n\n"
                f"**path:** `{path}`\n"
                f"**size:** `{get_readable_file_size(file_size)}`",
                quote=True
            )
            return
        
        items = os.listdir(path)
        if not items:
            await message.reply_text(f"📁 **empty directory:** `{path}`", quote=True)
            return
        
        directories = []
        files = []
        
        for item in sorted(items):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                directories.append(f"📁 {item}/")
            else:
                try:
                    size = os.path.getsize(item_path)
                    from utils import get_readable_file_size
                    files.append(f"📄 {item} ({get_readable_file_size(size)})")
                except:
                    files.append(f"📄 {item}")
        
        output_lines = []
        if directories:
            output_lines.extend(directories)
        if files:
            output_lines.extend(files)
        
        output = "\n".join(output_lines)
        
        await message.reply_text(
            f"📁 **directory listing**\n\n"
            f"**path:** `{os.path.abspath(path)}`\n"
            f"**items:** `{len(items)}`\n\n"
            f"{format_code_block(truncate_text(output))}",
            quote=True
        )
        
    except PermissionError:
        await message.reply_text(f"❌ **permission denied:** `{path}`", quote=True)
    except Exception as e:
        await message.reply_text(f"❌ **error:** `{str(e)}`", quote=True)