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

class Term:
    """Live update terminal class"""
    
    def __init__(self, process: asyncio.subprocess.Process) -> None:
        self._process = process
        self._line = b''
        self._output = b''
        self._init = asyncio.Event()
        self._is_init = False
        self._cancelled = False
        self._finished = False
        self._loop = asyncio.get_running_loop()
        self._listener = self._loop.create_future()
    
    @property
    def line(self) -> str:
        return self._by_to_str(self._line)
    
    @property
    def output(self) -> str:
        return self._by_to_str(self._output)
    
    @staticmethod
    def _by_to_str(data: bytes) -> str:
        return data.decode('utf-8', 'replace').strip()
    
    @property
    def cancelled(self) -> bool:
        return self._cancelled
    
    @property
    def finished(self) -> bool:
        return self._finished
    
    async def init(self) -> None:
        await self._init.wait()
    
    async def wait(self, timeout: int) -> None:
        self._check_listener()
        try:
            await asyncio.wait_for(self._listener, timeout)
        except asyncio.TimeoutError:
            pass
    
    def _check_listener(self) -> None:
        if self._listener.done():
            self._listener = self._loop.create_future()
    
    def cancel(self) -> None:
        if self._cancelled or self._finished:
            return
        try:
            self._process.terminate()
        except:
            pass
        self._cancelled = True
    
    @classmethod
    async def execute(cls, cmd: str) -> 'Term':
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        t_obj = cls(process)
        t_obj._start()
        return t_obj
    
    def _start(self) -> None:
        self._loop.create_task(self._worker())
    
    async def _worker(self) -> None:
        if self._cancelled or self._finished:
            return
        await asyncio.gather(
            self._read_stdout(),
            self._read_stderr()
        )
        await self._process.wait()
        self._finish()
    
    async def _read_stdout(self) -> None:
        await self._read(self._process.stdout)
    
    async def _read_stderr(self) -> None:
        await self._read(self._process.stderr)
    
    async def _read(self, reader: asyncio.StreamReader) -> None:
        while True:
            line = await reader.readline()
            if not line:
                break
            self._append(line)
    
    def _append(self, line: bytes) -> None:
        self._line = line
        self._output += line
        self._check_init()
        if not self._listener.done():
            self._listener.set_result(None)
    
    def _check_init(self) -> None:
        if self._is_init:
            return
        self._loop.call_later(0.1, self._init.set)
        self._is_init = True
    
    def _finish(self) -> None:
        if self._finished:
            return
        self._init.set()
        self._finished = True
        if not self._listener.done():
            self._listener.set_result(None)

@Client.on_message(filters.command("term"))
@auth_required
async def terminal_command(client: Client, message: Message):
    """Execute terminal command with live output"""
    
    if len(message.command) < 2:
        await message.reply_text("usage: `/term <command>`")
        return
        
    command = message.text.split(None, 1)[1]
    
    # Security check
    dangerous_commands = ['rm -rf', 'format', 'del /f', 'shutdown', 'reboot']
    if any(cmd in command.lower() for cmd in dangerous_commands):
        await message.reply_text("dangerous command blocked")
        return
    
    try:
        t_obj = await Term.execute(command)
    except Exception as e:
        await message.reply_text(f"error: {str(e)}")
        return
    
    current_user = os.environ.get('USER', 'root')
    current_dir = os.path.basename(os.getcwd()) or 'app'
    prefix = f"<b>{current_user}:{current_dir}#</b>" if current_user == 'root' else f"<b>{current_user}:{current_dir}$</b>"
    output = f"{prefix} <pre>{command}</pre>\n"
    
    status_msg = await message.reply_text(output, parse_mode=ParseMode.HTML)
    
    # Live update loop
    await t_obj.init()
    while not t_obj.finished:
        current_output = f"{output}<pre>{t_obj.line}</pre>"
        try:
            if current_output != status_msg.text:
                await status_msg.edit_text(current_output, parse_mode=ParseMode.HTML)
        except:
            pass
        await t_obj.wait(2)  # Update every 2 seconds
    
    if t_obj.cancelled:
        final_output = f"{output}<pre>^C</pre>\n{prefix}"
        await status_msg.edit_text(final_output, parse_mode=ParseMode.HTML)
        return
    
    # Final output
    final_output = f"{output}<pre>{t_obj.output}</pre>\n{prefix}"
    
    if len(final_output) > Config.MAX_MESSAGE_LENGTH:
        with open("temp/terminal_output.txt", "w", encoding="utf-8") as f:
            f.write(f"{current_user}:{current_dir}# {command}\n")
            f.write(t_obj.output)
            f.write(f"\n{current_user}:{current_dir}# ")
        
        await status_msg.delete()
        await message.reply_document(
            "temp/terminal_output.txt",
            caption=f"{prefix} <pre>{command}</pre>",
            parse_mode=ParseMode.HTML
        )
        os.remove("temp/terminal_output.txt")
    else:
        await status_msg.edit_text(final_output, parse_mode=ParseMode.HTML)

@Client.on_message(filters.command("ls"))
@auth_required  
async def list_directory(client: Client, message: Message):
    """List directory contents with terminal-like interface"""
    
    path = "."
    if len(message.command) > 1:
        path = message.text.split(None, 1)[1]
    
    # Get current user and directory info
    current_user = os.environ.get('USER', 'root')
    current_dir = os.path.basename(os.getcwd()) or 'app'
    prompt = f"{current_user}:{current_dir}# "
    
    ls_command = f"ls {path}" if path != "." else "ls"
    
    try:
        if not os.path.exists(path):
            error_output = f"<pre>{prompt}{ls_command}\nls: cannot access '{path}': No such file or directory\n{prompt}</pre>"
            await message.reply_text(error_output, parse_mode=ParseMode.HTML)
            return
            
        items = os.listdir(path)
        if not items:
            empty_output = f"<pre>{prompt}{ls_command}\n{prompt}</pre>"
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
        terminal_output = f"<pre>{prompt}{ls_command}\n"
        
        # Format items like real ls command
        for item in all_items[:30]:  # Limit to 30 items
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                terminal_output += f"{item}/\n"
            else:
                terminal_output += f"{item}\n"
        
        if len(all_items) > 30:
            terminal_output += "... (output truncated)\n"
        
        terminal_output += f"{prompt}</pre>"
        
        await message.reply_text(terminal_output, parse_mode=ParseMode.HTML)
        
    except PermissionError:
        error_output = f"<pre>{prompt}{ls_command}\nls: cannot open directory '{path}': Permission denied\n{prompt}</pre>"
        await message.reply_text(error_output, parse_mode=ParseMode.HTML)
    except Exception as e:
        error_output = f"<pre>{prompt}{ls_command}\nls: {str(e)}\n{prompt}</pre>"
        await message.reply_text(error_output, parse_mode=ParseMode.HTML)

@Client.on_message(filters.command("pwd"))
@auth_required
async def print_working_directory(client: Client, message: Message):
    """Print current working directory"""
    
    current_user = os.environ.get('USER', 'root')
    current_dir = os.path.basename(os.getcwd()) or 'app'
    prompt = f"{current_user}:{current_dir}# "
    
    pwd_output = f"<pre>{prompt}pwd\n{os.getcwd()}\n{prompt}</pre>"
    await message.reply_text(pwd_output, parse_mode=ParseMode.HTML)

@Client.on_message(filters.command("cd"))
@auth_required
async def change_directory(client: Client, message: Message):
    """Change current directory"""
    
    current_user = os.environ.get('USER', 'root')
    current_dir = os.path.basename(os.getcwd()) or 'app'
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
            error_output = f"<pre>{prompt}{cd_command}\nbash: cd: {target_dir}: No such file or directory\n{prompt}</pre>"
            await message.reply_text(error_output, parse_mode=ParseMode.HTML)
            return
            
        if not os.path.isdir(target_dir):
            error_output = f"<pre>{prompt}{cd_command}\nbash: cd: {target_dir}: Not a directory\n{prompt}</pre>"
            await message.reply_text(error_output, parse_mode=ParseMode.HTML)
            return
        
        os.chdir(target_dir)
        new_dir = os.path.basename(os.getcwd())
        new_prompt = f"{current_user}:{new_dir}# "
        
        success_output = f"<pre>{prompt}{cd_command}\n{new_prompt}</pre>"
        await message.reply_text(success_output, parse_mode=ParseMode.HTML)
        
    except PermissionError:
        error_output = f"<pre>{prompt}{cd_command}\nbash: cd: {target_dir}: Permission denied\n{prompt}</pre>"
        await message.reply_text(error_output, parse_mode=ParseMode.HTML)
    except Exception as e:
        error_output = f"<pre>{prompt}{cd_command}\nbash: cd: {str(e)}\n{prompt}</pre>"
        await message.reply_text(error_output, parse_mode=ParseMode.HTML)

def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"