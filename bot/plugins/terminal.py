"""
Terminal command plugin
"""

import asyncio
import logging
import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

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

@Client.on_message(filters.command("term"))
@auth_required
async def terminal_command(client: Client, message: Message):
    """Execute terminal command with real-time output"""
    
    if len(message.command) < 2:
        await message.reply_text("usage: `/term <command>`")
        return
        
    command = message.text.split(None, 1)[1]
    
    # Security check
    dangerous_commands = ['rm -rf', 'format', 'del /f', 'shutdown', 'reboot']
    if any(cmd in command.lower() for cmd in dangerous_commands):
        await message.reply_text("dangerous command blocked")
        return
    
    # Get current user and working directory
    current_user = os.environ.get('USER', 'user')
    current_dir = os.path.basename(os.getcwd())
    prompt = f"{current_user}:{current_dir}# "
    
    # Initial message with command prompt
    terminal_output = f"<code>{prompt}{command}</code>"
    status_msg = await message.reply_text(terminal_output, parse_mode=ParseMode.HTML)
    
    try:
        # Execute command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Combine stderr with stdout
            cwd=os.getcwd()
        )
        
        output_lines = []
        
        # Read output line by line for real-time updates
        while True:
            line = await process.stdout.readline()
            if not line:
                break
                
            line_text = line.decode('utf-8', errors='ignore').rstrip()
            if line_text:
                output_lines.append(line_text)
                
                # Update message with new output (limit to last 20 lines)
                display_lines = output_lines[-20:] if len(output_lines) > 20 else output_lines
                
                terminal_display = f"<code>{prompt}{command}\n"
                for output_line in display_lines:
                    terminal_display += f"{output_line}\n"
                terminal_display += f"{prompt}</code>"
                
                # Update message every few lines to avoid rate limits
                if len(output_lines) % 3 == 0 or len(terminal_display) > 3500:
                    try:
                        await status_msg.edit_text(terminal_display, parse_mode=ParseMode.HTML)
                        await asyncio.sleep(0.5)  # Small delay to avoid rate limits
                    except:
                        pass  # Ignore edit errors
        
        # Wait for process to complete
        await process.wait()
        
        # Final output
        if output_lines:
            # Show last 30 lines for final output
            display_lines = output_lines[-30:] if len(output_lines) > 30 else output_lines
            
            final_output = f"<code>{prompt}{command}\n"
            for line in display_lines:
                final_output += f"{line}\n"
            final_output += f"{prompt}</code>"
            
            # Send as file if too long
            if len(final_output) > Config.MAX_MESSAGE_LENGTH:
                with open("temp/terminal_output.txt", "w", encoding="utf-8") as f:
                    f.write(f"{prompt}{command}\n")
                    for line in output_lines:
                        f.write(f"{line}\n")
                    f.write(f"{prompt}")
                    
                await status_msg.delete()
                await message.reply_document(
                    "temp/terminal_output.txt",
                    caption=f"<code>{prompt}{command}</code>",
                    parse_mode=ParseMode.HTML
                )
                os.remove("temp/terminal_output.txt")
            else:
                await status_msg.edit_text(final_output, parse_mode=ParseMode.HTML)
        else:
            # No output
            final_output = f"<code>{prompt}{command}\n{prompt}</code>"
            await status_msg.edit_text(final_output, parse_mode=ParseMode.HTML)
            
    except asyncio.TimeoutError:
        timeout_output = f"<code>{prompt}{command}\n^C\n{prompt}</code>"
        await status_msg.edit_text(timeout_output, parse_mode=ParseMode.HTML)
    except Exception as e:
        error_output = f"<code>{prompt}{command}\nbash: {command}: {str(e)}\n{prompt}</code>"
        await status_msg.edit_text(error_output, parse_mode=ParseMode.HTML)

@Client.on_message(filters.command("ls"))
@auth_required  
async def list_directory(client: Client, message: Message):
    """List directory contents with terminal-like interface"""
    
    path = "."
    if len(message.command) > 1:
        path = message.text.split(None, 1)[1]
    
    # Get current user and directory info
    current_user = os.environ.get('USER', 'user')
    current_dir = os.path.basename(os.getcwd())
    prompt = f"{current_user}:{current_dir}# "
    
    ls_command = f"ls {path}" if path != "." else "ls"
    
    try:
        if not os.path.exists(path):
            error_output = f"<code>{prompt}{ls_command}\nls: cannot access '{path}': No such file or directory\n{prompt}</code>"
            await message.reply_text(error_output, parse_mode=ParseMode.HTML)
            return
            
        items = os.listdir(path)
        if not items:
            empty_output = f"<code>{prompt}{ls_command}\n{prompt}</code>"
            await message.reply_text(empty_output, parse_mode=ParseMode.HTML)
            return
        
        # Format output like real ls command
        dirs = []
        files = []
        
        for item in sorted(items):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                dirs.append(item)
            else:
                files.append(item)
        
        # Combine directories and files
        all_items = dirs + files
        
        # Create terminal-like output
        terminal_output = f"<code>{prompt}{ls_command}\n"
        
        # Format items in columns (like real ls)
        items_per_line = 3
        for i in range(0, len(all_items), items_per_line):
            line_items = all_items[i:i+items_per_line]
            formatted_items = []
            
            for item in line_items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    formatted_items.append(f"{item}/")
                else:
                    formatted_items.append(item)
            
            # Pad items to align columns
            padded_line = ""
            for item in formatted_items:
                padded_line += f"{item:<25}"
            
            terminal_output += f"{padded_line.rstrip()}\n"
            
            # Limit output length
            if len(terminal_output) > 3000:
                terminal_output += "... (output truncated)\n"
                break
        
        terminal_output += f"{prompt}</code>"
        
        await message.reply_text(terminal_output, parse_mode=ParseMode.HTML)
        
    except PermissionError:
        error_output = f"<code>{prompt}{ls_command}\nls: cannot open directory '{path}': Permission denied\n{prompt}</code>"
        await message.reply_text(error_output, parse_mode=ParseMode.HTML)
    except Exception as e:
        error_output = f"<code>{prompt}{ls_command}\nls: {str(e)}\n{prompt}</code>"
        await message.reply_text(error_output, parse_mode=ParseMode.HTML)

@Client.on_message(filters.command("pwd"))
@auth_required
async def print_working_directory(client: Client, message: Message):
    """Print current working directory"""
    
    current_user = os.environ.get('USER', 'user')
    current_dir = os.path.basename(os.getcwd())
    prompt = f"{current_user}:{current_dir}# "
    
    pwd_output = f"<code>{prompt}pwd\n{os.getcwd()}\n{prompt}</code>"
    await message.reply_text(pwd_output, parse_mode=ParseMode.HTML)

@Client.on_message(filters.command("cd"))
@auth_required
async def change_directory(client: Client, message: Message):
    """Change current directory"""
    
    current_user = os.environ.get('USER', 'user')
    current_dir = os.path.basename(os.getcwd())
    prompt = f"{current_user}:{current_dir}# "
    
    if len(message.command) < 2:
        # Go to home directory
        target_dir = os.path.expanduser("~")
        cd_command = "cd"
    else:
        target_dir = message.text.split(None, 1)[1]
        cd_command = f"cd {target_dir}"
    
    try:
        if not os.path.exists(target_dir):
            error_output = f"<code>{prompt}{cd_command}\nbash: cd: {target_dir}: No such file or directory\n{prompt}</code>"
            await message.reply_text(error_output, parse_mode=ParseMode.HTML)
            return
            
        if not os.path.isdir(target_dir):
            error_output = f"<code>{prompt}{cd_command}\nbash: cd: {target_dir}: Not a directory\n{prompt}</code>"
            await message.reply_text(error_output, parse_mode=ParseMode.HTML)
            return
        
        os.chdir(target_dir)
        new_dir = os.path.basename(os.getcwd())
        new_prompt = f"{current_user}:{new_dir}# "
        
        success_output = f"<code>{prompt}{cd_command}\n{new_prompt}</code>"
        await message.reply_text(success_output, parse_mode=ParseMode.HTML)
        
    except PermissionError:
        error_output = f"<code>{prompt}{cd_command}\nbash: cd: {target_dir}: Permission denied\n{prompt}</code>"
        await message.reply_text(error_output, parse_mode=ParseMode.HTML)
    except Exception as e:
        error_output = f"<code>{prompt}{cd_command}\nbash: cd: {str(e)}\n{prompt}</code>"
        await message.reply_text(error_output, parse_mode=ParseMode.HTML)

def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"