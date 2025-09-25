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

import aiofiles

try:
    from os import geteuid, setsid, getpgid, killpg
    from signal import SIGKILL
except ImportError:
    # pylint: disable=ungrouped-imports
    from os import kill as killpg
    # pylint: disable=ungrouped-imports
    from signal import CTRL_C_EVENT as SIGKILL

    def geteuid() -> int:
        return 1

    def getpgid(arg: Any) -> Any:
        return arg

    setsid = None

from pyrogram.types.messages_and_media.message import Str
from pyrogram import enums, filters, Client
from pyrogram.types import Message
from pyrogram.errors import MessageNotModified, MessageIdInvalid
from bot.config import Config


class MessageWrapper:
    """Wrapper to make Pyrogram Message behave like Userge Message"""
    def __init__(self, message: Message):
        self._message = message
        self.flags = {}
        self.input_str = ""
        self.filtered_input_str = ""
        self.reply_to_message = message.reply_to_message
        self.chat = message.chat
        self.text = message.text
        self._parse_input()
        self._parse_flags()

    def _parse_input(self):
        if self._message.text and len(self._message.text.split()) > 1:
            self.input_str = " ".join(self._message.text.split()[1:])
            self.filtered_input_str = self.input_str

    def _parse_flags(self):
        if self.input_str:
            parts = self.input_str.split()
            filtered_parts = []
            for part in parts:
                if part.startswith('-'):
                    flag = part[1:]
                    if flag.startswith('c') and len(flag) > 1 and flag[1:].isdigit():
                        self.flags['-c'] = flag[1:]
                    else:
                        self.flags[f'-{flag}'] = ''
                else:
                    filtered_parts.append(part)
            self.filtered_input_str = " ".join(filtered_parts)

    async def edit(self, text, parse_mode=None):
        try:
            return await self._message.edit_text(text, parse_mode=parse_mode)
        except (MessageNotModified, MessageIdInvalid):
            return await self._message.reply(text, parse_mode=parse_mode)

    async def err(self, text):
        return await self.edit(f"**ERROR**: `{text}`")

    async def edit_or_send_as_file(self, text, as_raw=False, parse_mode=None, filename="output.txt", caption=""):
        if len(text) > 4096 or as_raw:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            await self._message.reply_document(filename, caption=caption)
            os.remove(filename)
        else:
            await self.edit(text, parse_mode=parse_mode)

    async def canceled(self, reply=False):
        if reply:
            await self._message.reply("`Process Canceled!`")
        else:
            await self.edit("`Process Canceled!`")

    async def delete(self):
        return await self._message.delete()

    def cancel_callback(self, callback):
        class CancelContext:
            def __init__(self, cb):
                self.callback = cb
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return CancelContext(callback)


@Client.on_message(filters.command("exec") & filters.user(Config.OWNER_ID))
async def exec_command(client, message):
    if not message.text or len(message.text.split()) < 2:
        help_text = """**EXEC**:

**Header**: run commands in exec
**Flags**: 
  `-r`: raw text when send as file
**Usage**: `/exec [commands]`
**Examples**: `/exec echo "Userge"`"""
        await message.reply(help_text)
        return
    
    msg = MessageWrapper(message)
    await exec_(msg)


@Client.on_message(filters.command("eval") & filters.user(Config.OWNER_ID))
async def eval_command(client, message):
    if not message.text or len(message.text.split()) < 2:
        help_text = """**EVAL**:

**Header**: run python code line | lines
**Flags**:
  `-r`: raw text when send as file
  `-s`: silent mode (hide input code)
  `-p`: run in a private session
  `-n`: spawn new main session and run
  `-l`: list all running eval tasks
  `-c`: cancel specific running eval task
  `-ca`: cancel all running eval tasks
**Usage**: `/eval [flag] [code lines OR reply to .txt | .py file]`
**Examples**:
  `/eval print('Userge')`
  `/eval -s print('Userge')`
  `/eval 5 + 6`
  `/eval -s 5 + 6`
  `/eval -p x = 'private_value'`
  `/eval -n y = 'new_value'`
  `/eval -c2`
  `/eval -ca`
  `/eval -l`"""
        await message.reply(help_text)
        return
    
    msg = MessageWrapper(message)
    await eval_(msg)


@Client.on_message(filters.command("term") & filters.user(Config.OWNER_ID))
async def term_command(client, message):
    if not message.text or len(message.text.split()) < 2:
        help_text = """**TERM**:

**Header**: run commands in shell (terminal)
**Flags**:
  `-r`: raw text when send as file
**Usage**: `/term [commands]`
**Examples**: `/term echo "Userge"`"""
        await message.reply(help_text)
        return
    
    msg = MessageWrapper(message)
    await term_(msg)


def input_checker(func: Callable[[Any], Awaitable[Any]]):
    async def wrapper(message) -> None:
        replied = message.reply_to_message

        if not message.input_str:
            if (func.__name__ == "eval_"
                    and replied and replied.document
                    and replied.document.file_name.endswith(('.txt', '.py'))
                    and replied.document.file_size <= 2097152):

                dl_loc = await replied.download()
                async with aiofiles.open(dl_loc) as jv:
                    message.text += " " + await jv.read()
                os.remove(dl_loc)
                message.flags.update({'file': True})
            else:
                await message.err("No Command Found!")
                return

        cmd = message.input_str

        if "config.env" in cmd:
            await message.edit("`That's a dangerous operation! Not Permitted!`")
            return
        await func(message)
    return wrapper


@input_checker
async def exec_(message):
    """ run commands in exec """
    await message.edit("`Executing exec ...`")
    cmd = message.filtered_input_str
    as_raw = '-r' in message.flags

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
        await message.err(str(t_e))
        return

    output = f"**EXEC**:\n\n__Command:__\n`{cmd}`\n__PID:__\n`{pid}`\n__RETURN:__\n`{ret}`\n\n**stderr:**\n`{err or 'no error'}`\n\n**stdout:**\n``{out or 'no output'}`` "
    await message.edit_or_send_as_file(text=output,
                                       as_raw=as_raw,
                                       parse_mode=enums.ParseMode.MARKDOWN,
                                       filename="exec.txt",
                                       caption=cmd)


_KEY = '_OLD'
_EVAL_TASKS: Dict[asyncio.Future, str] = {}


@input_checker
async def eval_(message):
    """ run python code """
    for t in tuple(_EVAL_TASKS):
        if t.done():
            del _EVAL_TASKS[t]

    flags = message.flags

    if flags:
        if '-l' in flags:
            if _EVAL_TASKS:
                out = "**Eval Tasks**\n\n"
                i = 0
                for c in _EVAL_TASKS.values():
                    out += f"**{i}** - `{c}`\n"
                    i += 1
                out += f"\nuse `/eval -c[id]` to Cancel"
                await message.edit(out)
            else:
                await message.edit("No running eval tasks !")
                await asyncio.sleep(5)
                await message.delete()
            return

        size = len(_EVAL_TASKS)

        if ('-c' in flags or '-ca' in flags) and size == 0:
            await message.edit("No running eval tasks !")
            await asyncio.sleep(5)
            await message.delete()
            return

        if '-ca' in flags:
            for t in _EVAL_TASKS:
                t.cancel()
            await message.edit(f"Canceled all running eval tasks [{size}] !")
            await asyncio.sleep(5)
            await message.delete()
            return

        if '-c' in flags:
            t_id = int(flags.get('-c', -1))
            if t_id < 0 or t_id >= size:
                await message.edit(f"Invalid eval task id [{t_id}] !")
                await asyncio.sleep(5)
                await message.delete()
                return
            tuple(_EVAL_TASKS)[t_id].cancel()
            await message.edit(f"Canceled eval task [{t_id}] !")
            await asyncio.sleep(5)
            await message.delete()
            return

    cmd = message.filtered_input_str
    if not cmd:
        await message.err("Unable to Parse Input!")
        return

    msg = message
    replied = message.reply_to_message
    if (replied and replied.from_user
            and replied.from_user.is_self and isinstance(replied.text, Str)
            and str(replied.text.html).startswith("<b>></b> <pre>")):
        msg = replied

    await msg.edit("`Executing eval ...`", parse_mode=enums.ParseMode.MARKDOWN)

    is_file = replied and replied.document and flags.get("file")
    as_raw = '-r' in flags
    silent_mode = '-s' in flags
    if '-n' in flags:
        context_type = _ContextType.NEW
    elif '-p' in flags:
        context_type = _ContextType.PRIVATE
    else:
        context_type = _ContextType.GLOBAL

    async def _callback(output: Optional[str], errored: bool):
        final = ""
        if not silent_mode:
            final += "**>**" + (replied.link if is_file else f"```python\n{cmd}```") + "\n\n"
        if isinstance(output, str):
            output = output.strip()
            if output == '':
                output = None
        if output is not None:
            final += f"**>>** ```python\n{output}```"
        if errored and message.chat.type in (
                enums.ChatType.GROUP,
                enums.ChatType.SUPERGROUP,
                enums.ChatType.CHANNEL):
            await msg.edit(f"**Error occurred, check logs**")
        elif final:
            await msg.edit_or_send_as_file(text=final,
                                           as_raw=as_raw,
                                           parse_mode=enums.ParseMode.MARKDOWN,
                                           filename="eval.txt",
                                           caption=cmd)
        else:
            await msg.delete()

    _g, _l = _context(context_type, message=message, replied=message.reply_to_message)
    l_d = {}
    try:
        # nosec pylint: disable=W0122
        exec(_wrap_code(cmd, _l.keys()), _g, l_d)
    except Exception:  # pylint: disable=broad-except
        _g[_KEY] = _l
        await _callback(traceback.format_exc(), True)
        return

    future = asyncio.get_running_loop().create_future()
    asyncio.create_task(
        _run_coro(
            future,
            l_d['__aexec'](
                *_l.values()),
            _callback))
    hint = cmd.split('\n')[0]
    _EVAL_TASKS[future] = hint[:25] + "..." if len(hint) > 25 else hint

    with msg.cancel_callback(future.cancel):
        try:
            await future
        except asyncio.CancelledError:
            await asyncio.gather(msg.canceled())
        finally:
            _EVAL_TASKS.pop(future, None)


@input_checker
async def term_(message):
    """ run commands in shell (terminal with live update) """
    cmd = message.filtered_input_str
    as_raw = '-r' in message.flags

    try:
        parsed_cmd = parse_py_template(cmd, message)
    except Exception as e:  # pylint: disable=broad-except
        await message.err(str(e))
        return
    try:
        t_obj = await Term.execute(parsed_cmd)  # type: Term
    except Exception as t_e:  # pylint: disable=broad-except
        await message.err(str(t_e))
        return

    cur_user = getuser()
    uid = geteuid()

    prefix = f"<b>{cur_user}:~#</b>" if uid == 0 else f"<b>{cur_user}:~$</b>"
    output = f"{prefix} <pre>{cmd}</pre>\n"
    
    # Track if we've made the first edit to avoid duplicate messages
    first_edit = True

    with message.cancel_callback(t_obj.cancel):
        await t_obj.init()
        while not t_obj.finished:
            try:
                current_output = f"{output}<pre>{t_obj.line}</pre>"
                if first_edit:
                    await message.edit(current_output, parse_mode=enums.ParseMode.HTML)
                    first_edit = False
                else:
                    await message.edit(current_output, parse_mode=enums.ParseMode.HTML)
            except (MessageNotModified, MessageIdInvalid):
                pass
            await t_obj.wait(10)  # Increased timeout to avoid flood limits
        if t_obj.cancelled:
            await message.canceled(reply=True)
            return

    out_data = f"{output}<pre>{t_obj.output}</pre>\n{prefix}"
    await message.edit_or_send_as_file(
        out_data, as_raw=as_raw, parse_mode=enums.ParseMode.HTML, filename="term.txt", caption=cmd)


def parse_py_template(cmd: str, msg):
    glo, loc = _context(_ContextType.PRIVATE, message=msg,
                        replied=msg.reply_to_message)

    def replacer(mobj):
        # nosec pylint: disable=W0123
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


async def _run_coro(future: asyncio.Future, coro: Awaitable[Any],
              callback: Callable[[str, bool], Awaitable[Any]]) -> None:
    try:
        ret, exc = None, None
        with redirect() as out:
            try:
                ret = await coro
            except asyncio.CancelledError:
                return
            except Exception:  # pylint: disable=broad-except
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