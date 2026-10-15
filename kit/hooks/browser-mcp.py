"""브라우저 MCP 어댑터 — 곁의 실행기(`browser-mcp.mjs`)를 고른 도구의 MCP 서버 `playwright` 로 등록 · 걷기 · 확인한다 (결정 0149).

    python -X utf8 browser-mcp.py install --host claude --host codex --host agy
    python -X utf8 browser-mcp.py remove  --host codex
    python -X utf8 browser-mcp.py check   --host claude --host agy [--gone codex]

**쓰는 손은 도구 제 CLI 다** — `claude mcp add -s user` · `codex mcp add` · `agy mcp add`(와 각자의 `remove`). 설정 파일을 우리가
고쳐 쓰지 않는다 — Claude 의 `~/.claude.json` 은 도는 세션이 같이 쓰는 파일이다. Codex 만 예외다: 그 CLI 는 도구 시간 한도를
못 적고, 다시 달면 표를 통째로 새로 써 사람이 둔 키를 잃는다. 그래서 Codex 는 처음 달 때만 CLI 를 쓰고, 시간 한도와 옛 꼴
고치기(명령 · 인자)는 곁의 Codex 틀 병합기(`codex-config-merge.py` 의 `merge`)가 그 자리만 맞춘다. 이 판의 첫 쓰기 전에 원본을
곁에 떠 둔다(`<config.toml>.before-browser-mcp-<시각>`).
**도구 CLI 는 껍데기를 건너 부른다** — 윈도의 npm 껍데기(`.cmd`)는 `cmd.exe` 가 인자를 다시 읽어 `%이름%` 을 펼치고 `" & | < > ^`
를 제 글자로 먹는다 — 사람의 값이 글자 그대로 안 닿는다. 껍데기가 가리키는 진짜 실행 파일(`…\\claude.exe` · `…\\codex.js` 면
`node …`)을 껍데기 글에서 읽어 직접 부른다. 못 읽으면 껍데기로 부르되, 넘길 값에 껍데기가 못 나르는 글자가 있으면 아무것도
고치기 전에 ERROR 로 멈춘다.
**도구 CLI 는 울타리 안에서 돈다** — 출력은 파이프가 아니라 파일로 받고(손자가 쥔 파이프를 안 기다린다), 넘기면 띄운 것과 그
아래만 끊는다 — 윈도는 띄울 때 묶은 작업 개체(job object · 그 안에서 태어난 프로세스만 든다), 그 밖은 프로세스 묶음.
출력 글자는 UTF-8 로 읽고, 안 읽히면 윈도의 ANSI 코드 페이지(`cmd.exe` 의 메시지)로 읽는다.
**읽는 손은 등록 파일이다** — 우리 것인가 · 꼴이 맞나는 파일을 되읽어 가른다(Claude `<설정 자리>/.claude.json` 의 `mcpServers` ·
Codex `<CODEX_HOME>/config.toml` 의 `mcp_servers` · agy `~/.gemini/config/mcp_config.json` 의 `mcpServers`).

**우리 것은 꼴로 가린다 — 이름이 아니다**(#132). 이름 `playwright` 는 사람이 손으로 붙이는 흔한 이름이라, 이름만 보고 덮으면 남의
서버를 지우고, 이름만 보고 건너뛰면 우리 옛 꼴이 안 옮겨 간다.
  · 우리 것 — 명령의 파일 이름이 `node` 이고 첫 인자의 파일 이름이 `browser-mcp.mjs` 다(어느 자리의 실행기든 — 옛 자리도 우리 것)
  · 맞는 꼴 — 첫 인자가 곁의 실행기다(Codex 는 위 시간 한도까지). 다르면 그 자리만 고친다 — Claude · agy 는 걷고 다시 달고,
    Codex 는 그 자리만 맞춘다
  · 남의 것 — 같은 이름인데 우리 것이 아니면 안 건드리고 WARN 을 낸다. 그 PC 에서는 우리 서버가 안 선다
  ⚠ **우리 항목에서 우리 몫은 실행기 자리(첫 인자)와 Codex 시간 한도뿐이다** — 명령(어느 `node` 인가) · 실행기 뒤의 인자(실행기가
    서버로 넘긴다) · 환경값 · 켜고 끈 값은 사람 것이라, 견줄 때 안 보고 고칠 때 그대로 잇는다. 서버의 손잡이
    (`PLAYWRIGHT_MCP_HEADLESS` · `--viewport-size` 같은)는 사람이 거기 둔다.
  ⚠ **고친 뒤 되읽어 사람 것이 그대로가 아니면 고치기 전 항목으로 되돌린다**(Claude · agy 는 옛 값으로 다시 달고 끈 값도 다시
    끄고, Codex 는 고치기 전 글로 되쓴다) — 그대로 두면 다음 판은 꼴이 맞아 말없이 지나간다. 되돌리기까지 지면 그 까닭을 함께 낸다.
    되돌리기까지 져 사람 것이 바뀐 채 남으면 지키려던 것과 그때의 항목 지문을 표지(`~/.paisetup/browser-mcp-pending.json`)에
    적는다 — 다음 `install` 은 항목이 그 지문 그대로일 때만 그것을 목표로 다시 맞추고(다르면 사람이 고친 것이라 버린다),
    `check` 는 그 도구를 어긋남으로 낸다. 맞추거나 그 도구를 걷으면 지운다.
  ⚠ 사람이 고른 `node` 경로가 없어졌으면(노드를 올리거나 옮겼다) 서버가 안 뜬다 — 맨 `node` 로 고치고 WARN 을 낸다.
    `check` 는 등록된 명령 · 뒤 인자 · 환경값 그대로 띄워 잰다(창 없이만 덮는다).

`install` 은 꾸러미와 브라우저가 서야 단다 — 실행기 `--resolve` 가 전역 playwright 와 띄울 실행 파일을 찾고 그 파일이 있어야
한다. 없으면 아무것도 안 하고 SKIP 을 낸다(이미 단 것도 둔다 — 다음 설치가 브라우저를 받으면 그대로 선다). SKIP 의 까닭은
실행기가 표준 오류에 낸 줄 가운데 뜻이 있는 것이다(실행기의 말 → 오류 머리 줄 → 노드 판 줄이 아닌 끝 줄).
`remove` 는 우리 것만 걷는다(고르지 않은 도구). `check` 는 등록 파일을 되읽어 꼴을 견주고, 실행기를 MCP 로 한 번 띄워
`initialize` · `tools/list` · `data:` 주소 이동 · 그림 한 장을 잰다(「우리 크로미움이 여기서 뜨나」의 답). 그 판은 창 없이
띄운다 — 설치 도중에 창이 뜨지 않게. 창 있게 뜨나는 이 판이 안 잰다.

출력 — 한 줄에 하나:
  install · remove   CHANGE=<도구> <add|readd|fix|remove|timeout> · BACKUP=codex <경로> · WARN=<도구> <까닭> · SKIP=<까닭> ·
                     ERROR=<도구> <까닭> · 끝에 CHANGED=0|1
  check              OK=<도구> · DIFF=<도구> <까닭> · LIVE=ok <도구 수> tools · LIVE=fail <까닭> · UNMEASURED=<무엇> <까닭>
종료 — install · remove: 0 됐다 · 1 ERROR 가 있었다. check: 0 다 맞다 · 1 어긋났다 · 2 못 쟀다(어긋남이 없을 때).
파이썬 3.8 이상 · 표준 라이브러리만(Codex 를 읽고 맞추는 데는 3.11 의 tomllib).
"""
import argparse
import importlib.util
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
LAUNCHER = HERE / 'browser-mcp.mjs'
LAUNCHER_NAME = LAUNCHER.name
SERVER = 'playwright'
NODE = 'node'
HOSTS = ('claude', 'codex', 'agy')
CODEX_MERGER = 'codex-config-merge.py'   # TOML 한 자리를 뜻으로 재고 맞추는 손의 진본 — 이 파일 곁에 같이 실린다
CODEX_HOOK_MERGER = 'codex-hook-install.py'   # 위 손이 부르는 원본 떠 두기 · 옆 파일 쓰기 · TOML 값 짓기의 진본
CODEX_BACKUP_SUFFIX = '.before-browser-mcp-'
# Codex 의 도구 시간 한도(초) — 기본 60 은 서버의 이동 한도(playwright `--timeout-navigation` 기본 60 000 ms)와 같아, 느린 페이지
# 하나가 서버의 답보다 Codex 의 끊기에 먼저 닿는다. 이동 한도의 두 배를 준다
CODEX_TOOL_TIMEOUT_SEC = 120
HOST_CLI_CAP = 60          # 도구 CLI 한 번의 울타리(초) — 멎은 CLI 하나가 설치를 영구히 세우지 않게
RESOLVE_CAP = 60           # 실행기 `--resolve` 의 울타리 — `npm root -g` 를 품는다
KILL_CAP = 15              # 끊거나 서버를 닫고 나서 기다리는 한도(초)
LIVE_CAP = 120             # 확인 판의 울타리 — 맨바닥 VDI 의 첫 브라우저 기동까지 든다
LIVE_URL = 'data:text/html,<title>browser-mcp</title><h1>browser-mcp</h1>'
LIVE_ENV = {'PLAYWRIGHT_MCP_HEADLESS': '1'}
MCP_PROTOCOL = '2025-06-18'
WIN = os.name == 'nt'
ERROR_LINE = re.compile(r'[A-Za-z]*Error\b')   # 노드가 던진 오류의 머리 줄(`TypeError: …`) — 곁에 찍히는 원문 줄과 가른다
LAUNCHER_SAYS = '[browser-mcp]'   # 실행기가 표준 오류에 내는 줄의 머리 — SKIP 까닭은 이 줄을 먼저 고른다
# 껍데기(`.cmd`)가 진짜 실행 파일을 가리키는 꼴 — 지금 npm 은 `"%dp0%\node_modules\…\claude.exe"`, 옛 npm · pnpm · yarn 은
# `"%~dp0\node_modules\…\cli.js"`. 껍데기 폴더 밖을 가리키는 것은 안 집는다(`..` 로 빠져나가는 꼴)
SHIM_TARGET = re.compile(r'"%(?:~dp0|dp0%)\\?([^"%]+)"')
SHIM_NODE_EXTS = ('.js', '.cjs', '.mjs')
# `cmd.exe` 가 다시 읽어 바꾸거나 먹는 글자 — 껍데기로만 부를 수 있을 때 이 글자가 든 값은 글자 그대로 못 넘긴다
SHIM_UNSAFE = set('%"^&|<>!\r\n')
PENDING_DIR = '.paisetup'                    # PC 의 우리 상태 자리 — 갈 곳 표의 손(`tool-homes.py`)의 기록과 같은 곳
PENDING_FILE = 'browser-mcp-pending.json'


# ── 자리 ─────────────────────────────────────────────────────────────────────────
def registry_path(host):
    if host == 'claude':
        base = os.environ.get('CLAUDE_CONFIG_DIR')
        return pathlib.Path(base) / '.claude.json' if base else pathlib.Path.home() / '.claude.json'
    if host == 'codex':
        base = os.environ.get('CODEX_HOME')
        return (pathlib.Path(base) if base else pathlib.Path.home() / '.codex') / 'config.toml'
    return pathlib.Path.home() / '.gemini' / 'config' / 'mcp_config.json'


def norm_path(p):
    s = str(p).replace('\\', '/')
    return s.casefold() if WIN else s


def person_args(entry):
    """실행기 뒤의 인자 — 사람 것이다(실행기가 서버로 넘긴다)."""
    return [str(a) for a in ((entry or {}).get('args') or [])[1:]]


def wanted_args(entry=None):
    return [LAUNCHER.as_posix()] + person_args(entry)


# ── 등록 읽기 — `(항목 표 | None)` · 못 읽으면 예외 ───────────────────────────────────
def read_entry(host):
    path = registry_path(host)
    if not path.exists():
        return None
    if host == 'codex':
        import tomllib   # 3.11 이상 — 없으면 못 읽는 것이다(예외가 부르는 쪽에서 못 쟀다로 선다)
        with open(path, 'rb') as f:
            data = tomllib.load(f)
        table = data.get('mcp_servers')
    else:
        with open(path, encoding='utf-8-sig') as f:
            data = json.load(f)
        table = data.get('mcpServers') if isinstance(data, dict) else None
    entry = table.get(SERVER) if isinstance(table, dict) else None
    return entry if isinstance(entry, dict) else None


def ours(entry):
    cmd = pathlib.PurePath(str(entry.get('command') or '').replace('\\', '/')).name.casefold()
    args = entry.get('args') or []
    first = pathlib.PurePath(str(args[0]).replace('\\', '/')).name if args else ''
    return cmd in (NODE, NODE + '.exe') and first == LAUNCHER_NAME


def command_alive(command):
    """등록된 명령이 띄울 수 있는 것인가 — 맨 이름(`node`)은 PATH 가, 경로는 그 파일이 답한다."""
    command = str(command or '')
    if not command:
        return False
    if '/' not in command and '\\' not in command:
        return bool(shutil.which(command))
    return pathlib.Path(command).is_file()


def command_diff(entry):
    """우리 몫(실행기 자리)과 띄울 수 있는 명령인가 — 같으면 빈 글. 명령의 고름 · 뒤 인자 · 환경값은 사람 것이라 안 본다.
    ⚠ 사람이 고른 `node` 경로라도 그 파일이 없으면(노드를 올리거나 옮겼다) 서버가 안 뜬다 — 그때는 맨 `node` 로 고친다."""
    args = entry.get('args') or []
    if not args or norm_path(args[0]) != norm_path(LAUNCHER.as_posix()):
        return f'실행기 자리가 {args[0] if args else None!r} 다'
    if not command_alive(entry.get('command')):
        return f'명령 {entry.get("command")!r} 이 없다'
    return ''


def shape_diff(host, entry):
    """맞는 꼴과 다른 곳 — 같으면 빈 글."""
    why = command_diff(entry)
    if not why and host == 'codex' and entry.get('tool_timeout_sec') != CODEX_TOOL_TIMEOUT_SEC:
        why = f'tool_timeout_sec 가 {entry.get("tool_timeout_sec")!r} 다'
    return why


def disabled(host, entry):
    if host == 'codex':
        return entry.get('enabled') is False
    if host == 'agy':
        return entry.get('disabled') is True
    return False


def person_part(host, entry):
    """사람 것(명령 · 뒤 인자 · 환경값 · 끈 값) — 고친 뒤 되읽어 그대로인지 견주고, 못 지키면 표지에 적는다."""
    entry = entry or {}
    return {'command': str(entry.get('command') or ''), 'args': person_args(entry),
            'env': {str(k): str(v) for k, v in (entry.get('env') or {}).items()}, 'disabled': disabled(host, entry)}


# ── 표지 — 사람 것을 못 지켰고 되돌리기도 진 도구 ────────────────────────────────────────
# 되돌리기까지 지면 등록은 사람 것이 바뀐 채 남고, 그 사람 것은 어디에도 안 남는다 — 표지 없이 「맞을 때까지 판마다 ERROR」로는
# 못 간다: 다음 판은 무엇이 맞는 값인지 모른 채 지금 값을 사람 것으로 읽어 말없이 지나간다. 그래서 그때 지키려던 사람 것
# (`target`)과, 표지를 적을 때의 항목 지문(`seen`)을 함께 적는다. 다음 `install` 은 항목이 그 지문 그대로일 때만 표지를 목표로
# 다시 맞추고, 지문이 다르면 그 사이 사람이 고친 것이라 표지를 버린다. `check` 도 지문이 그대로일 때만 어긋남으로 낸다. 맞추거나
# 그 도구를 걷으면(`remove`) 지운다.
def pending_path():
    return pathlib.Path.home() / PENDING_DIR / PENDING_FILE


def fingerprint(entry):
    return None if entry is None else json.dumps(entry, sort_keys=True, ensure_ascii=False, default=str)


def pending_target(pending, host, entry):
    """표지가 아직 서는가 — 항목이 표지를 적을 때 그대로면 지킬 사람 것, 아니면 None."""
    rec = pending.get(host)
    if isinstance(rec, dict) and isinstance(rec.get('target'), dict) and rec.get('seen') == fingerprint(entry):
        return rec['target']
    return None


def load_pending():
    try:
        with open(pending_path(), encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_pending(pending):
    path = pending_path()
    if not pending:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)


# ── 울타리 안에서 띄우기 ─────────────────────────────────────────────────────────────
class Capped(Exception):
    """울타리를 넘겨 띄운 것을 다 끊었다."""


if WIN:
    import ctypes
    from ctypes import wintypes

    _K32 = ctypes.WinDLL('kernel32', use_last_error=True)
    _NTDLL = ctypes.WinDLL('ntdll')
    _K32.CreateJobObjectW.restype = wintypes.HANDLE
    _K32.CreateJobObjectW.argtypes = (wintypes.LPVOID, wintypes.LPCWSTR)
    _K32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _K32.AssignProcessToJobObject.restype = wintypes.BOOL
    _K32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _K32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _NTDLL.NtResumeProcess.argtypes = (wintypes.HANDLE,)
    CREATE_SUSPENDED = 0x00000004


class Tree:
    """띄운 프로세스 하나와 그 아래 — 끊을 때 그 묶음만 끊는다.

    윈도는 멈춘 채 띄워 작업 개체에 넣고 나서 풀어 준다 — 그래야 첫 손자까지 그 안에서 태어난다. 부모 번호(PPID)를 따라가는
    `taskkill /T` 는 같은 번호를 앞서 쓴 프로세스의 고아까지 끊을 수 있다. 작업 개체에 못 넣으면(바깥 작업이 막는다) 띄운 것
    하나만 끊는다."""

    def __init__(self, argv, **kw):
        self.job = None
        if WIN:
            kw['creationflags'] = kw.get('creationflags', 0) | CREATE_SUSPENDED
        else:
            kw['start_new_session'] = True
        self.p = subprocess.Popen(argv, **kw)
        if WIN:
            job = _K32.CreateJobObjectW(None, None)
            handle = int(self.p._handle)
            if job and _K32.AssignProcessToJobObject(job, handle):
                self.job = job
            elif job:
                _K32.CloseHandle(job)
            _NTDLL.NtResumeProcess(handle)

    def kill(self):
        try:
            if self.job:
                _K32.TerminateJobObject(self.job, 1)
            elif not WIN:
                os.killpg(self.p.pid, signal.SIGKILL)
            else:
                self.p.kill()
        except OSError:
            self.p.kill()
        try:
            self.p.wait(KILL_CAP)
        except subprocess.TimeoutExpired:
            pass
        self.close()

    def close(self):
        """작업 개체 손잡이만 놓는다 — 그 안에 남은 것은 안 끊는다(CLI 가 띄운 상주 프로세스가 있을 수 있다)."""
        if self.job:
            _K32.CloseHandle(self.job)
            self.job = None


def decode(raw):
    """UTF-8 로 읽고, 안 읽히면 윈도의 ANSI 코드 페이지(`cmd.exe` 의 메시지)로 읽는다."""
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('mbcs' if WIN else 'utf-8', 'replace')


def run_capped(argv, cap, merge_err=False):
    """`(종료 값, 표준 출력, 표준 오류)` — 출력은 파일로 받아 손자가 쥔 파이프를 안 기다린다. 넘기면 다 끊고 Capped."""
    with tempfile.TemporaryFile() as fo, tempfile.TemporaryFile() as fe:
        t = Tree(argv, stdin=subprocess.DEVNULL, stdout=fo, stderr=fo if merge_err else fe)
        try:
            rc = t.p.wait(cap)
        except subprocess.TimeoutExpired:
            t.kill()
            raise Capped(f'{pathlib.Path(argv[0]).name} {" ".join(argv[1:3])} 가 {cap}초 안에 안 끝나 끊었다') from None
        t.close()
        fo.seek(0)
        fe.seek(0)
        return rc, decode(fo.read()), decode(fe.read())


# ── 도구 CLI ─────────────────────────────────────────────────────────────────────
def shim_target(cmd_path):
    """npm 껍데기가 가리키는 진짜 실행 줄 — `[exe]` 나 `[node, js]` · 못 읽으면 None."""
    try:
        text = decode(pathlib.Path(cmd_path).read_bytes())
    except OSError:
        return None
    home = pathlib.Path(cmd_path).resolve().parent
    for rel in reversed(SHIM_TARGET.findall(text)):
        target = (home / rel).resolve()
        if home not in target.parents or not target.is_file():
            continue
        if target.suffix.lower() == '.exe':
            return [str(target)]
        node = shutil.which(NODE)
        if target.suffix.lower() in SHIM_NODE_EXTS and node:
            return [node, str(target)]
    return None


def host_argv(host):
    """`(부를 줄, 값이 글자 그대로 닿나)` — 도구가 PATH 에 없으면 RuntimeError."""
    exe = shutil.which(host)
    if not exe:
        raise RuntimeError(f'{host} 명령이 PATH 에 없다')
    if WIN and pathlib.Path(exe).suffix.lower() in ('.cmd', '.bat'):
        real = shim_target(exe)
        return (real, True) if real else ([exe], False)
    return [exe], True


def run_cli(host, args):
    """`(종료 값, 끝 줄)` — 울타리를 넘으면 Capped."""
    argv, _ = host_argv(host)
    rc, text, _ = run_capped(argv + args, HOST_CLI_CAP, merge_err=True)
    tail = [ln for ln in text.splitlines() if ln.strip() and 'PATH aliases' not in ln]
    return rc, (tail[-1] if tail else '')


def env_pairs(env):
    return [f'{k}={v}' for k, v in (env or {}).items()]


def refuse_unsafe(host, command, args, env):
    """껍데기로만 부를 수 있는데 값에 그것이 못 나르는 글자가 있으면 — 아무것도 고치기 전에 — 멈춘다."""
    _, verbatim = host_argv(host)
    if verbatim:
        return
    bad = sorted({v for v in [command] + list(args) + env_pairs(env) if SHIM_UNSAFE & set(v)})
    if bad:
        raise RuntimeError(f'{host} 를 cmd 껍데기로만 부를 수 있는데 {bad} 에 껍데기가 못 나르는 글자'
                           f'({"".join(sorted(SHIM_UNSAFE - {chr(13), chr(10)}))})가 있어 안 건드렸다')


def cli_add(host, command, args, env):
    """그 꼴로 단다 — 깃발 자리는 도구마다 다르다(Claude 는 이름 뒤 · agy · Codex 는 이름 앞)."""
    cmd = ['--', command] + list(args)
    pairs = env_pairs(env)
    if host == 'claude':   # `-e` 는 여러 값을 먹어 이름 앞에 두면 이름을 삼킨다 · 기본 범위는 그 폴더 하나(local)다
        return run_cli(host, ['mcp', 'add', '-s', 'user', SERVER] + [x for kv in pairs for x in ('-e', kv)] + cmd)
    return run_cli(host, ['mcp', 'add'] + [x for kv in pairs for x in ('--env', kv)] + [SERVER] + cmd)


def cli_remove(host):
    if host == 'claude':
        return run_cli(host, ['mcp', 'remove', SERVER, '-s', 'user'])
    return run_cli(host, ['mcp', 'remove', SERVER])


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CodexFile:
    """Codex `config.toml` 을 고치는 손 — 이 판의 첫 쓰기(CLI 든 병합기든) 전에 원본을 떠 두고 글로도 쥔다(되돌리기)."""

    def __init__(self):
        self.path = registry_path('codex')
        self.merger = load_module('codex_config_merge', CODEX_MERGER)
        self.merger.M = load_module('codex_hook_install', CODEX_HOOK_MERGER)
        self.backup = None
        self.original = None       # 첫 쓰기 전의 글 — 없던 파일이면 None
        self.first = True

    def before_write(self):
        """첫 쓰기 앞에서만 뜬다 — 없던 파일은 뜰 원본이 없고, 둘째 쓰기 앞의 파일은 이미 우리가 고친 것이다."""
        if self.first and self.path.exists():
            with open(self.path, encoding='utf-8', newline='') as f:
                self.original = f.read()
            self.backup = self.merger.M.backup_copy(self.path, CODEX_BACKUP_SUFFIX)
        self.first = False

    def settle(self, entry):
        """시간 한도(와 실행기 자리가 다르면 인자 — 뒤 인자는 사람 것 그대로)를 그 자리만 맞춘다 — 바꿨으면 True."""
        template = f'[mcp_servers.{SERVER}]\n'
        if entry is not None and not command_alive(entry.get('command')):
            template += f'command = {self.merger.M.render_value(NODE)}\n'
        if entry is not None and command_diff(entry):
            template += f'args = {self.merger.M.render_value(wanted_args(entry))}\n'
        template += f'tool_timeout_sec = {CODEX_TOOL_TIMEOUT_SEC}\n'
        with open(self.path, encoding='utf-8', newline='') as f:
            current = f.read()
        new, changed, _ = self.merger.merge(current, template)
        if changed:
            self.before_write()
            self.merger.M.write_atomic(self.path, new)
        return changed

    def restore(self, entry):
        """우리 표만 고치기 전 값으로 되돌린다 — 앞으로 갈 때처럼 병합기로 그 자리만. 파일 통째로 되쓰면 그 사이 Codex 앱이나
        사람이 다른 자리에 적은 것을 잃는다. 없던 항목이면 CLI 로 걷는다. 병합기는 키를 지우지 못해 우리가 더한
        `tool_timeout_sec` 는 남는다 — 우리 몫이라 사람 것은 그대로다."""
        if self.first:
            return
        if entry is None:
            cli_remove('codex')
            return
        template = f'[mcp_servers.{SERVER}]\n'
        template += f'command = {self.merger.M.render_value(str(entry.get("command")))}\n'
        template += f'args = {self.merger.M.render_value([str(a) for a in entry.get("args") or []])}\n'
        if 'tool_timeout_sec' in entry:
            template += f'tool_timeout_sec = {self.merger.M.render_value(entry["tool_timeout_sec"])}\n'
        with open(self.path, encoding='utf-8', newline='') as f:
            current = f.read()
        new, changed, _ = self.merger.merge(current, template)
        if changed:
            self.merger.M.write_atomic(self.path, new)


# ── 실행기에게 묻기 ───────────────────────────────────────────────────────────────
def meaningful(stderr_text):
    """실행기의 표준 오류에서 까닭 한 줄 — 실행기의 말(끝 것) → 오류 머리 줄(첫 것) → 노드 판 줄이 아닌 끝 줄."""
    lines = [ln.strip() for ln in stderr_text.splitlines() if ln.strip()]
    said = [ln for ln in lines if ln.startswith(LAUNCHER_SAYS)]
    if said:
        return said[-1]
    errs = [ln for ln in lines if ERROR_LINE.match(ln)]
    if errs:
        return errs[0]
    rest = [ln for ln in lines if not ln.startswith('Node.js v')]
    return rest[-1] if rest else ''


def resolve():
    """`(계획 표 | None, 까닭)` — 실행기가 전역 playwright 와 띄울 실행 파일을 찾았나."""
    node = shutil.which(NODE)
    if not node:
        return None, 'node 가 PATH 에 없다'
    try:
        rc, out, err = run_capped([node, str(LAUNCHER), '--resolve'], RESOLVE_CAP)
    except Capped:
        return None, f'실행기가 {RESOLVE_CAP}초 안에 답을 안 냈다'
    if rc != 0:
        return None, meaningful(err) or f'실행기가 {rc} 로 끝났다'
    plan = json.loads(out.strip().splitlines()[-1])
    if not plan.get('exists'):
        return None, f'브라우저 실행 파일이 없다({plan.get("exe")})'
    return plan, ''


# ── 걸음 ─────────────────────────────────────────────────────────────────────────
def readd(host, entry, target):
    """Claude · agy — 사람 것(`target`)을 이어 우리 꼴로 다시 단다. 이미 걷었는데 진 것은 예외로 낸다."""
    if entry is not None:
        rc, tail = cli_remove(host)
        if rc != 0:
            raise RuntimeError(f'옛 꼴을 못 걷었다({rc}: {tail})')
    command = target['command'] if target else NODE
    rc, tail = cli_add(host, command, wanted_args() + (target['args'] if target else []), target['env'] if target else {})
    if rc != 0:
        raise RuntimeError(f'못 달았다({rc}: {tail})')
    if target and target['disabled'] and host == 'agy':   # agy 의 `mcp add` 는 꺼 둔 값도 켠다
        rc, tail = run_cli(host, ['mcp', 'disable', SERVER])
        if rc != 0:
            raise RuntimeError(f'사람이 끈 항목을 다시 못 껐다({rc}: {tail})')


def restore(host, entry):
    """고치기 전 항목으로 되돌린다 — 되돌렸으면 빈 글, 못 했으면 까닭."""
    try:
        now = read_entry(host)
        if now is not None:
            cli_remove(host)
        if entry is not None:
            rc, tail = cli_add(host, str(entry.get('command')), [str(a) for a in entry.get('args') or []],
                               entry.get('env') or {})
            if rc != 0:
                return f'옛 항목을 못 달았다({rc}: {tail})'
            if disabled(host, entry):
                run_cli(host, ['mcp', 'disable', SERVER])
        back = read_entry(host)
        if (back is None) != (entry is None) or (entry is not None and (
                person_part(host, back) != person_part(host, entry) or back.get('args') != entry.get('args'))):
            return '되읽은 항목이 옛 항목과 다르다'
        return ''
    except Exception as exc:
        return str(exc)


def install(hosts, out):
    plan, why = resolve()
    if plan is None:
        out('SKIP=' + why)
        return False, False
    pending = load_pending()
    changed = failed = False
    for host in hosts:
        entry = cf = target = None
        wrote = False
        try:
            entry = read_entry(host)
            if entry is not None and not ours(entry):
                out(f'WARN={host} 같은 이름({SERVER})의 남의 서버가 있어 안 단다 — {entry.get("command")} {entry.get("args")}')
                continue
            # 지킬 사람 것 — 앞 판이 못 지켜 표지에 적은 것이 아직 서면 그것, 아니면 지금 항목의 것(Codex 는 늘 지금 것)
            target = pending_target(pending, host, entry) if host != 'codex' else None
            if host in pending and target is None:
                pending.pop(host)
                out(f'WARN={host} 표지를 버렸다 — 표지를 적은 뒤 그 항목이 바뀌었다(사람이 고친 것으로 본다)')
            target = target or (person_part(host, entry) if entry is not None else None)
            if target is not None and not command_alive(target['command']):
                out(f'WARN={host} 등록된 명령 {target["command"]!r} 이 없어 PATH 의 {NODE} 로 바꾼다')
                target = dict(target, command=NODE)
            if entry is not None and not shape_diff(host, entry) and person_part(host, entry) == target:
                pending.pop(host, None)
                continue
            if host == 'codex':
                cf = CodexFile()
                if entry is None:
                    refuse_unsafe(host, NODE, wanted_args(), {})
                    cf.before_write()
                    wrote = True
                    rc, tail = cli_add(host, NODE, wanted_args(), {})
                    if rc != 0:
                        raise RuntimeError(f'못 달았다({rc}: {tail})')
                    out(f'CHANGE={host} add')
                fixed = entry is not None and bool(command_diff(entry))
                if cf.settle(entry):
                    wrote = True
                    out(f'CHANGE={host} ' + ('fix' if fixed else 'timeout'))
                if cf.backup:
                    out(f'BACKUP={host} {cf.backup}')
            else:
                refuse_unsafe(host, target['command'] if target else NODE, wanted_args() + (target['args'] if target else []),
                              target['env'] if target else {})
                wrote = True
                readd(host, entry, target)
                out(f'CHANGE={host} ' + ('readd' if entry is not None else 'add'))
            changed = changed or wrote
            now = read_entry(host) or {'command': None}
            left = shape_diff(host, now)
            if not left and target is not None and person_part(host, now) != target:
                left = f'사람 것을 못 이었다({target} → {person_part(host, now)})'
            if left:
                raise RuntimeError(f'달고 되읽은 꼴이 다르다 — {left}')
            pending.pop(host, None)
        except Exception as exc:   # 도구 하나가 져도 나머지는 간다 — 까닭은 한 줄로
            tail = ''
            if wrote:
                undo = ''
                if cf is not None:
                    try:
                        cf.restore(entry)
                    except Exception as rexc:
                        undo = str(rexc)
                else:
                    undo = restore(host, entry)
                tail = f' — 되돌리기도 못 했다: {undo}' if undo else ' — 고치기 전 항목으로 되돌렸다'
            try:
                final = read_entry(host)
            except Exception:
                final = None
            if target is not None and host != 'codex' and (final is None or person_part(host, final) != target):
                pending[host] = {'target': target, 'seen': fingerprint(final)}
                tail += f' · 지킬 사람 것을 {pending_path()} 에 적었다 — 다음 판이 다시 맞춘다'
            out(f'ERROR={host} {exc}{tail}')
            failed = True
    save_pending(pending)
    return changed, failed


def remove(hosts, out):
    pending = load_pending()
    changed = failed = False
    for host in hosts:
        pending.pop(host, None)        # 안 고른 도구의 표지는 버린다 — 다시 고를 때 옛 목표를 덮어쓰면 안 된다
        try:
            entry = read_entry(host)
            if entry is None:
                continue
            if not ours(entry):
                out(f'WARN={host} 같은 이름({SERVER})의 남의 서버라 안 걷는다')
                continue
            rc, tail = cli_remove(host)
            if rc != 0 or read_entry(host) is not None:
                raise RuntimeError(f'못 걷었다({rc}: {tail})')
            out(f'CHANGE={host} remove')
            changed = True
        except Exception as exc:
            out(f'ERROR={host} {exc}')
            failed = True
    save_pending(pending)
    return changed, failed


def live_probe(command=NODE, extra_args=(), extra_env=None):
    """`(판정, 글)` — 판정은 ok · fail · unmeasured. 등록된 명령 · 뒤 인자 · 환경값으로 실행기를 MCP 로 띄워 네 걸음을 잰다
    (창 없이 — `LIVE_ENV` 가 이긴다)."""
    node = shutil.which(command) if '/' not in command and '\\' not in command else command
    if not node or not command_alive(command):
        return 'fail', f'명령 {command!r} 이 없다'
    work = tempfile.mkdtemp(prefix='browser-mcp-check-')
    env = dict(os.environ, **{str(k): str(v) for k, v in (extra_env or {}).items()}, **LIVE_ENV)
    t = Tree([node, str(LAUNCHER)] + list(extra_args), cwd=work, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
             stderr=subprocess.PIPE)
    p = t.p
    err = []
    threading.Thread(target=lambda: err.extend(p.stderr), daemon=True).start()
    deadline = time.monotonic() + LIVE_CAP
    replies = {}

    def reader():
        for raw in p.stdout:
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if 'id' in msg:
                replies[msg['id']] = msg
    threading.Thread(target=reader, daemon=True).start()

    def call(n, method, params):
        p.stdin.write((json.dumps({'jsonrpc': '2.0', 'id': n, 'method': method, 'params': params}) + '\n').encode())
        p.stdin.flush()
        while n not in replies:
            if time.monotonic() > deadline:
                raise TimeoutError(method)
            if p.poll() is not None and n not in replies:
                raise RuntimeError(f'서버가 {p.returncode} 로 끝났다')
            time.sleep(0.05)
        r = replies[n]
        if 'error' in r or (r.get('result') or {}).get('isError'):
            text = json.dumps(r.get('error') or r['result'].get('content'), ensure_ascii=False)
            raise RuntimeError(f'{method} 가 졌다 — {text[:300]}')
        return r['result']

    try:
        call(1, 'initialize', {'protocolVersion': MCP_PROTOCOL, 'capabilities': {},
                               'clientInfo': {'name': 'browser-mcp-check', 'version': '0'}})
        p.stdin.write((json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n').encode())
        p.stdin.flush()
        tools = [x['name'] for x in call(2, 'tools/list', {}).get('tools', [])]
        call(3, 'tools/call', {'name': 'browser_navigate', 'arguments': {'url': LIVE_URL}})
        shot = call(4, 'tools/call', {'name': 'browser_take_screenshot', 'arguments': {}})
        if not any(c.get('type') == 'image' for c in shot.get('content', [])):
            return 'fail', '그림이 안 왔다'
        call(5, 'tools/call', {'name': 'browser_close', 'arguments': {}})
        return 'ok', f'{len(tools)} tools'
    except TimeoutError as exc:
        return 'unmeasured', f'{exc} 가 {LIVE_CAP}초 안에 안 끝났다'
    except Exception as exc:
        tail = decode(b''.join(err[-3:])).strip().replace('\n', ' | ')
        return 'fail', f'{exc}' + (f' — {tail[:300]}' if tail else '')
    finally:
        try:
            p.stdin.close()
            p.wait(KILL_CAP)
            t.close()
        except Exception:
            t.kill()          # 브라우저까지 — 서버 하나만 끊으면 크로미움이 남는다
        shutil.rmtree(work, ignore_errors=True)


def check(hosts, gone, out):
    diff = unmeasured = False
    pending = load_pending()
    launches = {}          # 등록된 띄우는 꼴(명령 · 뒤 인자 · 환경값)마다 그것을 든 도구 — 꼴마다 한 번씩 띄워 잰다
    for host, want in [(h, True) for h in hosts] + [(h, False) for h in gone]:
        try:
            entry = read_entry(host)
        except Exception as exc:
            out(f'UNMEASURED={host} {registry_path(host)} 를 못 읽었다 — {exc}')
            unmeasured = True
            continue
        mine = entry is not None and ours(entry)
        if want:
            why = '등록이 없다' if entry is None else (shape_diff(host, entry) if mine else '같은 이름의 남의 서버다')
            if not why and pending_target(pending, host, entry) is not None:
                why = f'앞 판이 사람 것을 못 지켰다 — {pending_path()}'
        else:
            why = '안 고른 도구에 우리 등록이 남았다' if mine else ''
        if why:
            out(f'DIFF={host} {why}')
            diff = True
        else:
            out(f'OK={host}' + ('' if want else ' gone'))
        if want and mine:
            part = person_part(host, entry)
            key = json.dumps([part['command'], part['args'], part['env']], ensure_ascii=False, sort_keys=True)
            launches.setdefault(key, []).append(host)
    for key, who in launches.items():
        command, extra, env = json.loads(key)
        verdict, text = live_probe(command, extra, env)
        where = f' ({" · ".join(who)})' if len(launches) > 1 else ''
        if verdict == 'ok':
            out('LIVE=ok ' + text + where)
        elif verdict == 'fail':
            out('LIVE=fail ' + text + where)
            diff = True
        else:
            out('UNMEASURED=live ' + text + where)
            unmeasured = True
    return 1 if diff else (2 if unmeasured else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('install', 'remove', 'check'))
    ap.add_argument('--host', action='append', default=[], choices=HOSTS)
    ap.add_argument('--gone', action='append', default=[], choices=HOSTS)
    args = ap.parse_args()

    def out(line):
        print(line, flush=True)

    if args.action == 'check':
        return check(args.host, args.gone, out)
    changed, failed = (install if args.action == 'install' else remove)(args.host, out)
    out('CHANGED=' + ('1' if changed else '0'))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
