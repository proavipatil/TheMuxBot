"""Utility functions for TheBot"""

import os
import asyncio
import subprocess
from typing import Tuple, Optional
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_readable_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 b"
    size_names = ["b", "kb", "mb", "gb", "tb"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def get_readable_time(seconds: int) -> str:
    """Convert seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

async def run_command(command: str, timeout: int = 300) -> Tuple[str, str, int]:
    """Execute shell command asynchronously"""
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=timeout
        )
        
        return (
            stdout.decode('utf-8', errors='ignore'),
            stderr.decode('utf-8', errors='ignore'),
            process.returncode
        )
    except asyncio.TimeoutError:
        return "", "command timed out", 1
    except Exception as e:
        return "", str(e), 1

def create_settings_keyboard() -> InlineKeyboardMarkup:
    """Create settings inline keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📁 paths", callback_data="settings_paths"),
            InlineKeyboardButton("👥 auth", callback_data="settings_auth")
        ],
        [
            InlineKeyboardButton("⚙️ config", callback_data="settings_config"),
            InlineKeyboardButton("📊 stats", callback_data="settings_stats")
        ],
        [InlineKeyboardButton("❌ close", callback_data="settings_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_auth_keyboard() -> InlineKeyboardMarkup:
    """Create auth management keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("👤 users", callback_data="auth_users"),
            InlineKeyboardButton("👥 groups", callback_data="auth_groups")
        ],
        [InlineKeyboardButton("🔙 back", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_code_block(text: str, language: str = "") -> str:
    """Format text as code block"""
    return f"```{language}\n{text}\n```"

def truncate_text(text: str, max_length: int = 4000) -> str:
    """Truncate text to fit telegram message limit"""
    if len(text) <= max_length:
        return text
    return text[:max_length-10] + "\n...truncated"