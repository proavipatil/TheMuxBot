""" run shell or python command(s) """

import asyncio
import io
import keyword
import os
import re
import shlex
import sys
import threading
import traceback
from contextlib import contextmanager
from enum import Enum
from getpass import getuser
from shutil import which
from typing import Awaitable, Any, Callable, Dict, Optional, Tuple, Iterable

try:
    from os import geteuid, setsid, getpgid, killpg
    from signal import SIGKILL
except ImportError:
    from os import kill as killpg
    from signal import CTRL_C_EVENT as SIGKILL

    def geteuid() -> int:
        return 1

    def getpgid(arg: Any) -> Any:
        return arg

    setsid = None

from pyrogram import enums, filters
from bot.client import bot
from bot.config import Config

def input_checker(func: Callable[[Any], Awaitable[Any]]):
    async def wrapper(client, message) -> None:
        if not message.text or len(message.text.split()) < 2:
            await message.reply_text("No Command Found!")
            return

        cmd = " ".join(message.text.split()[1:])

        if "config.env" in cmd:
            await message.reply_text("`That's a dangerous operation! Not Permitted!`")
            return
        await func(client, message, cmd)
    return wrapper

@bot.on_message(filters.command("exec") & filters.user(Config.OWNER_ID))
@input_checker
async def exec_command(client, message, cmd):
    """ run commands in exec """
    msg = await message.reply_text("`Executing exec ...`")
    
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        out = stdout.decode('utf-8', 'replace').strip()
        err = stderr.decode('utf-8', 'replace').strip()
        ret = process.returncode
        pid = process.pid
        
    except Exception as t_e:
        await msg.edit_text(f"Error: {str(t_e)}")
        return

    output = f"**EXEC**:\n\n__Command:__\n`{cmd}`\n__PID:__\n`{pid}`\n__RETURN:__\n`{ret}`\n\n**stderr:**\n`{err or 'no error'}`\n\n**stdout:**\n`{out or 'no output'}`"
    
    if len(output) > 4096:
        with open("exec.txt", "w") as f:
            f.write(output)
        await message.reply_document("exec.txt", caption=cmd)
        os.remove("exec.txt")
        await msg.delete()
    else:
        await msg.edit_text(output, parse_mode=enums.ParseMode.MARKDOWN)

_KEY = '_OLD'
_EVAL_TASKS: Dict[asyncio.Future, str] = {}

@bot.on_message(filters.command("eval") & filters.user(Config.OWNER_ID))
async def eval_command(client, message):
    """ run python code """
    for t in tuple(_EVAL_TASKS):
        if t.done():
            del _EVAL_TASKS[t]

    if not message.text or len(message.text.split()) < 2:
        await message.reply_text("Unable to Parse Input!")
        return

    cmd = " ".join(message.text.split()[1:])
    msg = await message.reply_text("`Executing eval ...`")

    async def _callback(output: Optional[str], errored: bool):
        final = f"**>** ```python\n{cmd}```\n\n"
        if isinstance(output, str):
            output = output.strip()
            if output == '':
                output = None
        if output is not None:
            final += f"**>>** ```python\n{output}```"
        
        if len(final) > 4096:
            with open("eval.txt", "w") as f:
                f.write(final)
            await message.reply_document("eval.txt", caption=cmd)
            await msg.delete()
        elif final:
            await msg.edit_text(final, parse_mode=enums.ParseMode.MARKDOWN, disable_web_page_preview=True)
        else:
            await msg.delete()

    _g, _l = _context(_ContextType.GLOBAL, message=message)
    l_d = {}
    try:
        exec(_wrap_code(cmd, _l.keys()), _g, l_d)
    except Exception:
        _g[_KEY] = _l
        await _callback(traceback.format_exc(), True)
        return

    future = asyncio.get_running_loop().create_future()
    asyncio.create_task(_run_coro_task(future, l_d['__aexec'](*_l.values()), _callback))
    hint = cmd.split('\n')[0]
    _EVAL_TASKS[future] = hint[:25] + "..." if len(hint) > 25 else hint

    try:
        await future
    except asyncio.CancelledError:
        await msg.edit_text("**EVAL Process Canceled!**")
    finally:
        _EVAL_TASKS.pop(future, None)

@bot.on_message(filters.command("term") & filters.user(Config.OWNER_ID))
@input_checker
async def term_command(client, message, cmd):
    """ run commands in shell (terminal with live update) """
    msg = await message.reply_text("`Executing terminal ...`")
    
    try:
        parsed_cmd = parse_py_template(cmd, message)
    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")
        return
    
    try:
        t_obj = await Term.execute(parsed_cmd)
    except Exception as t_e:
        await msg.edit_text(f"Error: {str(t_e)}")
        return

    cur_user = getuser()
    uid = geteuid()

    prefix = f"<b>{cur_user}:~#</b>" if uid == 0 else f"<b>{cur_user}:~$</b>"
    output = f"{prefix} <pre>{cmd}</pre>\n"

    await t_obj.init()
    while not t_obj.finished:
        try:
            await msg.edit_text(f"{output}<pre>{t_obj.line}</pre>", parse_mode=enums.ParseMode.HTML)
        except:
            pass
        await t_obj.wait(2)
    
    if t_obj.cancelled:
        await msg.edit_text("Process Canceled!")
        return

    out_data = f"{output}<pre>{t_obj.output}</pre>\n{prefix}"
    
    if len(out_data) > 4096:
        with open("term.txt", "w") as f:
            f.write(out_data)
        await message.reply_document("term.txt", caption=cmd)
        await msg.delete()
    else:
        await msg.edit_text(out_data, parse_mode=enums.ParseMode.HTML)

def parse_py_template(cmd: str, msg):
    glo, loc = _context(_ContextType.PRIVATE, message=msg)

    def replacer(mobj):
        return shlex.quote(str(eval(mobj.expand(r"\1"), glo, loc)))
    return re.sub(r"{{(.+?)}}", replacer, cmd)

class _ContextType(Enum):
    GLOBAL = 0
    PRIVATE = 1
    NEW = 2

def _context(context_type: _ContextType, **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if context_type == _ContextType.NEW:
        try:
            del globals()[_KEY]
        except KeyError:
            pass
    if _KEY not in globals():
        globals()[_KEY] = globals().copy()
    _g = globals()[_KEY]
    if context_type == _ContextType.PRIVATE:
        _g = _g.copy()
    _l = _g.pop(_KEY, {})
    _l.update(kwargs)
    return _g, _l

def _wrap_code(code: str, args: Iterable[str]) -> str:
    head = "async def __aexec(" + ', '.join(args) + "):\n try:\n  "
    tail = "\n finally: globals()['" + _KEY + "'] = locals()"
    if '\n' in code:
        code = code.replace('\n', '\n  ')
    elif (any(True for k_ in keyword.kwlist if k_ not in (
            'True', 'False', 'None', 'lambda', 'await') and code.startswith(f"{k_} "))
          or ('=' in code and '==' not in code)):
        code = f"\n  {code}"
    else:
        code = f"\n  return {code}"
    return head + code + tail

async def _run_coro_task(future: asyncio.Future, coro: Awaitable[Any],
                        callback: Callable[[str, bool], Awaitable[Any]]) -> None:
    try:
        ret, exc = None, None
        with redirect() as out:
            try:
                ret = await coro
            except asyncio.CancelledError:
                return
            except Exception:
                exc = traceback.format_exc().strip()
            output = exc or out.getvalue()
            if ret is not None:
                output += str(ret)
        await callback(output, exc is not None)
    finally:
        if not future.done():
            future.set_result(None)

_PROXIES = {}

class _Wrapper:
    def __init__(self, original):
        self._original = original

    def __getattr__(self, name: str):
        return getattr(
            _PROXIES.get(
                threading.current_thread().ident,
                self._original),
            name)

sys.stdout = _Wrapper(sys.stdout)
sys.__stdout__ = _Wrapper(sys.__stdout__)
sys.stderr = _Wrapper(sys.stderr)
sys.__stderr__ = _Wrapper(sys.__stderr__)

@contextmanager
def redirect() -> io.StringIO:
    ident = threading.current_thread().ident
    source = io.StringIO()
    _PROXIES[ident] = source
    try:
        yield source
    finally:
        del _PROXIES[ident]
        source.close()

class Term:
    """ live update term class """

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
        killpg(getpgid(self._process.pid), SIGKILL)
        self._cancelled = True

    @classmethod
    async def execute(cls, cmd: str) -> 'Term':
        kwargs = dict(
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        if setsid:
            kwargs['preexec_fn'] = setsid
        if sh := which(os.environ.get("USERGE_SHELL", "bash")):
            kwargs['executable'] = sh
        process = await asyncio.create_subprocess_shell(cmd, **kwargs)
        t_obj = cls(process)
        t_obj._start()
        return t_obj

    def _start(self) -> None:
        self._loop.create_task(self._worker())

    async def _worker(self) -> None:
        if self._cancelled or self._finished:
            return
        await asyncio.wait([asyncio.create_task(self._read_stdout()), asyncio.create_task(self._read_stderr())])
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

    def _check_init(self) -> None:
        if self._is_init:
            return
        self._loop.call_later(1, self._init.set)
        self._is_init = True

    def _finish(self) -> None:
        if self._finished:
            return
        self._init.set()
        self._finished = True
        if not self._listener.done():
            self._listener.set_result(None)