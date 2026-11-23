"""보고 창 머리의 「비서에게 부탁하기」 — 친 말을 채운 Claude Code 대화를 VS Code 의 작업 폴더 창에 연다. 일일 보고 스킬의 여는 손.

창 곁의 손(곁의 `presses.py`)이 창의 부탁(localStorage `brief_const.ASK_KEY`)을 거둬 `take` 를 부르고, 끝을 그 창에 돌려 적는다. 창을 지을 때
`ready` 가 칸을 세울지 정한다. 모델은 이 길에 없다 — 친 말을 읽어 무엇을 가르지 않고, 정해 둔 주소 하나(`LINK_HEAD`)만 연다. 말은 입력
칸에 채워질 뿐 보내지지 않는다 — 엔터는 사람이 친다.

차례 — VS Code 를 등록된 `vscode:` 처리기에서 찾는다 · 확장과 작업 폴더가 있나 본다 · 첫마디를 짓는다 · 두 번 인코딩해 길이를 본다 ·
`Code.exe <작업 폴더>` · VS Code 창들 가운데 z 차례 맨 위 창의 제목이 작업 폴더를 대기를 기다린다(천장만 둔다) · 주소를 연다 · 그 창을 앞에
세워 본다(Windows 가 안 들어주면 작업 표시줄 단추를 깜빡인다 — 흉내 낸 입력은 안 쓴다).
주소만 열면 VS Code 는 마지막으로 올라온 창(다른 폴더 · 되살린 지난 창)에 연다 — 그래서 폴더 창을 먼저 올린다. 확장은 VS Code 가 한 번 푼
query 를 다시 풀어, 한 번만 인코딩하면 `&` 에서 잘리고 `+` 는 빈칸이 되고 `%` 가 끼면 한글까지 깨진다 — 그래서 두 번 인코딩한다.
무엇을 지키고 왜 그런가는 `references/DESIGN.md` 「비서에게 부탁하기」가 든다.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_const.py · 보고 글 읽기 · store.py — `-I` 로 돌아도 싣는다
import brief_const as C  # noqa: E402
from brief_inline import plain  # noqa: E402
from brief_text import parse  # noqa: E402
import store as S  # noqa: E402

LINK_HEAD = "vscode://anthropic.claude-code/open?"   # 여는 주소는 이 처리기 하나다 — Claude Code 확장의 주소 처리기(채우기만 하고 안 보낸다)
EXTENSION_ID = "anthropic.claude-code"
HANDLER_KEY = r"vscode\shell\open\command"     # HKEY_CLASSES_ROOT 아래 — 사용자 설치(HKCU)와 모든 사용자 설치(HKLM)를 합쳐 보인다
WORK_ENV = "PAISETUP_WORK"                     # 작업 폴더 — 설치기가 사용자 환경값으로 심는다
USER_ENV_KEY = "Environment"                   # HKEY_CURRENT_USER 아래 — 사용자 환경값
EXT_ENV = "VSCODE_EXTENSIONS"                  # VS Code 가 확장 자리로 먼저 읽는 값
URL_MOST = 32_000                              # 여는 주소의 끝 — Windows 명령 줄 한도(32,767)가 자다. 넘기면 주소가 끝까지 안 간다
STEP_S = 0.05                                  # 작업 폴더 창이 맨 위에 섰나를 다시 보는 사이
# 손이 띄운 쪽에서 물려받았을 수 있는 표지 — VS Code 를 띄우고 주소를 열기 전에 손의 환경에서 걷는다. 앞의 여섯은 이 PC 에서 도는 Claude Code
# 세션의 것이다(창 곁의 손을 대화가 띄웠으면 손이 든다) — 꺼져 있던 VS Code 가 물려받으면 그 터미널에서 띄운 claude 가 「세션 안의 세션」으로
# 읽는다(확장이 제 손을 띄울 때 걷는 이름과 같다). 뒤는 VS Code 확장 호스트가 제 아래 프로세스에 거는 것이다(대화가 VS Code 의 Claude Code
# 였으면 손까지 내려온다) — ELECTRON_RUN_AS_NODE 를 든 Code.exe 는 창을 안 띄우고 Node 로 돈다
CARRIED_MARKS = ("CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT", "TRACEPARENT", "TRACESTATE",
                 "ELECTRON_RUN_AS_NODE", "VSCODE_IPC_HOOK", "VSCODE_IPC_HOOK_CLI", "VSCODE_PID", "VSCODE_CWD", "VSCODE_NLS_CONFIG",
                 "VSCODE_HANDLES_UNCAUGHT_ERRORS", "VSCODE_ESM_ENTRYPOINT", "VSCODE_CODE_CACHE_PATH", "VSCODE_CRASH_REPORTER_PROCESS_TYPE")

OPENED, NO_VSCODE, NO_WORK, TOO_LONG, NOT_READY, FAILED = "opened", "novscode", "nowork", "toolong", "notready", "failed"
FAIL_HEAD = "대화를 열지 못했습니다 — "
WORDS = {
    "front": "VS Code 의 작업 폴더 창에 열었습니다 · {when} — 채워 둔 말이 입력 칸에 있습니다. 엔터를 누르셔야 시작합니다.",
    "behind": ("VS Code 의 작업 폴더 창에 열었습니다 · {when} — 그 창은 이 창 뒤에 떠 있습니다. 작업 표시줄에서 깜빡이는 VS Code 를 누르시면 "
               "채워 둔 말이 보이고, 엔터를 누르셔야 시작합니다."),
    NO_VSCODE: FAIL_HEAD + C.ASK_NO_VSCODE,
    NO_WORK: FAIL_HEAD + "작업 폴더{where}가 없습니다. 설치 프로그램(PAI Setup)을 다시 돌리시면 생깁니다.",
    TOO_LONG: FAIL_HEAD + "말이 너무 길어 VS Code 에 넘길 수 없습니다. 줄여서 다시 눌러 주세요.",
    NOT_READY: FAIL_HEAD + "VS Code 의 작업 폴더 창이 서지 않았습니다. VS Code 에서 작업 폴더({path})를 열어 보시고 다시 눌러 주세요.",
    FAILED: FAIL_HEAD + "VS Code 를 여는 데서 멈췄습니다({why}). 다시 눌러 주세요.",
}


# ── 찾기 — VS Code · 확장 · 작업 폴더 ─────────────────────────────────────────

def vscode_exe() -> pathlib.Path | None:
    """등록된 `vscode:` 처리기의 실행 파일(`"…\\Code.exe" --open-url -- "%1"` 의 첫 칸) — 없거나 그 파일이 없으면 None."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, HANDLER_KEY) as k:
            command = str(winreg.QueryValueEx(k, "")[0])
    except (ImportError, OSError):
        return None
    m = re.match(r'\s*(?:"([^"]+)"|(\S+))', command)
    exe = pathlib.Path(m.group(1) or m.group(2)) if m else None
    return exe if exe and exe.is_file() else None


def extension_dir() -> pathlib.Path:
    """VS Code 가 확장을 찾는 자리 — VS Code 가 고르는 차례 그대로: `VSCODE_EXTENSIONS` · 홈의 `.vscode/extensions`. 설치판(사용자 · 모든
    사용자 설치 — 등록된 `vscode:` 처리기가 서는 판)은 휴대 판의 값(VSCODE_PORTABLE)을 안 읽는다."""
    given = os.environ.get(EXT_ENV, "").strip()
    return pathlib.Path(given) if given else pathlib.Path.home() / ".vscode" / "extensions"


def has_extension() -> bool:
    """VS Code 확장 폴더에 Claude Code 확장(`EXTENSION_ID`)이 깔렸나."""
    return any((p / "package.json").is_file() for p in extension_dir().glob(EXTENSION_ID + "-*"))


def ready() -> bool:
    """부탁을 열 수 있는 PC 인가 — 등록된 VS Code 와 그 Claude Code 확장이 있다. 작업 폴더는 누를 때 본다(없으면 그 까닭을 창에 적는다)."""
    return vscode_exe() is not None and has_extension()


def work_value() -> str:
    """작업 폴더 값 — 사용자 환경값(윈도 레지스트리 `HKCU\\Environment`)을 먼저, 그다음 이 프로세스의 값. 설치기가 값을 심기 전에 뜬
    프로세스(창 곁의 손 · 그 손을 띄운 대화)는 옛 환경을 들고 있어 사용자 환경값이 진본이다. `%…%` 가 든 값(REG_EXPAND_SZ)은 푼다."""
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, USER_ENV_KEY) as k:
                value, kind = winreg.QueryValueEx(k, WORK_ENV)
            if isinstance(value, str) and value.strip():
                return winreg.ExpandEnvironmentStrings(value) if kind == winreg.REG_EXPAND_SZ else value
        except OSError:
            pass
    return os.environ.get(WORK_ENV, "")


def work_folder() -> tuple[pathlib.Path | None, str]:
    """(작업 폴더, 받은 값) — 값이 없거나 그 폴더가 없으면 폴더 자리가 None."""
    raw = work_value().strip().strip('"')
    if not raw:
        return None, ""
    path = pathlib.Path(raw)
    return (path if path.is_dir() else None), raw


# ── 첫마디 · 주소 ────────────────────────────────────────────────────────────

def prefill(words: str, title: str, brief: pathlib.Path | None) -> str:
    """입력 칸에 채울 글 — 친 말, 빈 줄, 어느 보고 창에서 보낸 부탁인가, 그 보고 글의 자리. 친 말은 고치지 않는다."""
    lines = [words, "", f"— {title} 창에서 보낸 부탁입니다" if title else "— 보고 창에서 보낸 부탁입니다"]
    return "\n".join(lines + ([f"· 보고 글: {brief}"] if brief else []))


def link(text: str, session: str = "") -> str:
    """여는 주소 — 글을 두 번 퍼센트 인코딩한다(VS Code 가 한 번 · 확장이 한 번 푼다). `session` 을 주면 그 대화를 이어 연다(뒤에서 돈 실행의
    세션 — 확장의 세션 목록에 드는 것만 이어진다: 작업 폴더에서 돌았고, 띄운 쪽 이름이 프로그램의 것(`sdk-*`)이 아니다. 목록에 없으면 확장은
    새 대화를 연다)."""
    head = LINK_HEAD + (f"session={urllib.parse.quote(session, safe='')}&" if session else "")
    return head + "prompt=" + urllib.parse.quote(urllib.parse.quote(text, safe=""), safe="")


# ── VS Code 창 — 표준 라이브러리(ctypes)의 Win32 만. 프로세스 목록 · 명령 줄은 안 읽는다 ─────────────

def _user32():
    """창을 묻고 앞으로 올리는 user32 의 Win32 함수를 인자 · 반환 꼴을 매겨 싣는다."""
    import ctypes
    import ctypes.wintypes as wt
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.GetForegroundWindow.restype = wt.HWND
    u.GetWindowTextLengthW.argtypes = [wt.HWND]
    u.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
    u.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
    u.IsWindowVisible.argtypes = [wt.HWND]
    u.GetWindow.argtypes = [wt.HWND, ctypes.c_uint]
    u.GetWindow.restype = wt.HWND
    u.SetForegroundWindow.argtypes = [wt.HWND]
    return u


def _image(pid: int) -> str:
    """프로세스 번호 `pid` 의 실행 파일 경로 — 못 물으면 빈 글."""
    import ctypes
    import ctypes.wintypes as wt
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.restype = wt.HANDLE
    k.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    h = k.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION — 실행 파일의 이름만 묻는다
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wt.DWORD(len(buf))
        return buf.value if k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)) else ""
    finally:
        k.CloseHandle(h)


def top_window(exe: pathlib.Path) -> tuple[int, str] | None:
    """VS Code 창들 가운데 z 차례 맨 위 — (핸들, 제목). 그 실행 파일이 띄운, 보이고 제목이 있는 맨 위 창(주인 없는 창)만 센다. 없으면 None."""
    import ctypes
    import ctypes.wintypes as wt
    u = _user32()
    want = os.path.normcase(str(exe))
    found: list[tuple[int, str]] = []

    def each(hwnd, _):
        if not u.IsWindowVisible(hwnd) or u.GetWindow(hwnd, 4):     # GW_OWNER — 대화 상자 따위는 안 센다
            return True
        n = u.GetWindowTextLengthW(hwnd)
        if not n:
            return True
        pid = wt.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if os.path.normcase(_image(pid.value)) != want:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, buf, n + 1)
        found.append((int(hwnd), buf.value))
        return False                               # EnumWindows 는 z 차례 위에서부터 낸다 — 첫 것이 맨 위다
    u.EnumWindows(ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)(each), 0)
    return found[0] if found else None


def names_folder(title: str, name: str) -> bool:
    """제목이 그 폴더를 대나 — VS Code 설정 `window.title` 의 기본 꼴(「편집기 - 폴더 - Visual Studio Code」 · 「폴더 - Visual Studio Code」)."""
    return f" - {name} - " in title or title.startswith(f"{name} - ")


def shed_marks() -> None:
    """손의 환경에서 물려받은 표지(`CARRIED_MARKS`)를 걷는다 — 손이 띄우는 VS Code 와 손이 여는 주소(ShellExecute 가 손의 환경을 넘긴다)가
    다 이 환경을 받는다. 사람이 둔 VS Code 의 값(VSCODE_APPDATA · VSCODE_EXTENSIONS)은 그대로 둔다."""
    for name in [k for k in os.environ if k.upper() in CARRIED_MARKS]:
        os.environ.pop(name, None)


def raise_folder(exe: pathlib.Path, work: pathlib.Path) -> None:
    """`Code.exe <작업 폴더>` — 그 폴더 창이 있으면 VS Code 창들 맨 위로 올리고, 없으면 새 창으로 연다. 기다리지 않는다. 꺼져 있던 VS Code 를
    이 부름이 띄우면 그 VS Code 가 손보다 오래 산다 — 손이 든 작업 묶음(job)에서 떼어 띄운다."""
    cmd = [str(exe), str(work)]
    flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB, subprocess.CREATE_NEW_PROCESS_GROUP) \
        if sys.platform == "win32" else (0,)
    for i, flag in enumerate(flags):
        try:
            subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                             cwd=str(work), **({"creationflags": flag} if sys.platform == "win32" else {}))
            return
        except OSError:
            if i == len(flags) - 1:
                raise


def wait_top(exe: pathlib.Path, name: str, ceiling: float, tick=lambda: None) -> int | None:
    """맨 위 VS Code 창이 그 폴더를 댈 때까지 — 그 창의 핸들. 천장까지 안 서면 None. 기다리는 동안 `tick` 을 거듭 부른다(손이 살아 있다는
    숨 표 — 꺼져 있던 VS Code 가 뜨는 동안 창이 손을 없다고 읽지 않게)."""
    end = time.monotonic() + ceiling
    while True:
        top = top_window(exe)
        if top and names_folder(top[1], name):
            return top[0]
        if time.monotonic() >= end:
            return None
        tick()
        time.sleep(STEP_S)


def bring_forward(hwnd: int) -> bool:
    """그 창을 앞에 세워 본다 — 섰으면 True. Windows 는 사람이 다른 창을 쓰는 동안 뒤의 프로세스가 앞 창을 바꾸는 것을 막는다. 그때는 그 창의
    작업 표시줄 단추를 그 창이 앞에 설 때까지 깜빡인다(FlashWindowEx). 흉내 낸 입력은 쓰지 않는다."""
    import ctypes
    import ctypes.wintypes as wt
    u = _user32()
    if u.SetForegroundWindow(hwnd) and int(u.GetForegroundWindow() or 0) == hwnd:
        return True

    class FLASHWINFO(ctypes.Structure):
        _fields_ = [("cbSize", wt.UINT), ("hwnd", wt.HWND), ("dwFlags", wt.DWORD), ("uCount", wt.UINT), ("dwTimeout", wt.DWORD)]
    flash_all_until_front = 0x3 | 0xC              # FLASHW_ALL · FLASHW_TIMERNOFG
    u.FlashWindowEx(ctypes.byref(FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, flash_all_until_front, 0, 0)))
    return False


# ── 부탁 하나 ───────────────────────────────────────────────────────────────

def brief_of(folder: pathlib.Path, page: str) -> tuple[str, pathlib.Path | None]:
    """누른 창(`page` — 그 창의 파일 이름)의 보고 이름과 보고 글의 자리 — 그 글이 없으면(`store.page_brief`) ("", None)."""
    got = S.page_brief(folder, page)
    if got is None:
        return "", None
    md, text = got
    return plain(parse(text).title or "").strip(), md.resolve()


def take(folder: pathlib.Path, words: str, page: str, when: str, tick=lambda: None, session: str = "") -> tuple[str, str]:
    """부탁 하나를 연다 — (끝, 그 창에 적을 말). `words` 는 친 말 그대로, `page` 는 누른 창의 파일 이름, `when` 은 말에 넣을 연 때, `tick` 은
    작업 폴더 창을 기다리는 동안 거듭 부를 것, `session` 은 이어 갈 대화(없으면 새 대화). VS Code 와 확장 · 작업 폴더 · 주소의 길이를 먼저
    보고, 하나라도 아니면 아무것도 안 띄운다. 부작용 — 이 프로세스의 환경에서 물려받은 표지를 걷는다(`shed_marks`)."""
    exe = vscode_exe()
    if exe is None or not has_extension():
        return NO_VSCODE, WORDS[NO_VSCODE]
    work, raw = work_folder()
    if work is None:
        return NO_WORK, WORDS[NO_WORK].format(where=f"({raw})" if raw else "")
    title, md = brief_of(folder, page)
    url = link(prefill(words, title, md), session)
    if len(url) > URL_MOST:
        return TOO_LONG, WORDS[TOO_LONG]
    shed_marks()
    try:
        raise_folder(exe, work)
    except OSError as exc:
        return FAILED, WORDS[FAILED].format(why=type(exc).__name__)
    hwnd = wait_top(exe, work.name, C.ASK_OPEN_CEILING_S, tick)
    if hwnd is None:
        return NOT_READY, WORDS[NOT_READY].format(path=work)
    try:
        os.startfile(url)                          # ShellExecute — 등록된 처리기(Code.exe --open-url)가 받는다
    except (OSError, ValueError) as exc:
        return FAILED, WORDS[FAILED].format(why=type(exc).__name__)
    return OPENED, WORDS["front" if bring_forward(hwnd) else "behind"].format(when=when)
