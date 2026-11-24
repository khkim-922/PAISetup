"""뒤에 사는 claude 를 띄우는 바탕 — 띄울 claude 를 찾고 · 그 환경을 손질하고 · 그 프로세스가 아직 도나 본다.
어느 손의 밑에도 안 두고 여기 한 자리에 둔다(보고 띄우기 · 맡긴 일 · 시계 걸기 · 보고가 끝났나 보기가 다 빌려 쓴다). 곁의 파이썬 손을 띄우는
몸은 `proc_base` 가, 떼어 띄우는 인자는 `detach` 가 든다(둘 다 같은 스킬 `scripts/`).

    born = process_born(pid)                     # 그 프로세스가 뜬 때 — 번호와 함께 적어 번호를 남이 받은 것을 가린다
    alive = process_alive(pid, born)             # 그 프로세스가 아직 도나 — 모르면 None
    claude = pick_claude(given, saved)           # `--claude` · 걸어 둔 것 · PATH 차례 — 못 찾으면 None
    env = child_env(dict(os.environ))            # 겹친 세션의 표지를 걷고, 루프백 프록시를 지나면 보고의 표 머리를 싣는다
"""

from __future__ import annotations

import os
import pathlib
import shutil
import sys
from typing import Any
from urllib.parse import urlsplit

import unattended_const as C

STILL_ACTIVE = 259                                               # 윈도 GetExitCodeProcess 가 도는 프로세스에 내는 값
NO_SUCH_PROCESS = 87                                             # ERROR_INVALID_PARAMETER — OpenProcess 가 그런 번호의 프로세스가 없을 때 내는 값
QUERY_LIMITED = 0x1000                                           # PROCESS_QUERY_LIMITED_INFORMATION — 같은 사용자의 프로세스를 묻는 권한


def process_born(pid: Any) -> int | None:
    """그 번호의 프로세스가 뜬 때(윈도 FILETIME 의 정수) — 번호와 함께 적어 두면 끝난 프로세스의 번호를 남이 받은 것을 가린다. 윈도 밖이거나
    못 물었으면 None."""
    if sys.platform != "win32" or not isinstance(pid, int) or pid <= 0:
        return None
    import ctypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel.OpenProcess(QUERY_LIMITED, False, pid)
    if not handle:
        return None
    try:
        return _born(kernel, handle)
    finally:
        kernel.CloseHandle(handle)


def _born(kernel: Any, handle: Any) -> int | None:
    """열린 프로세스가 뜬 때 — GetProcessTimes 의 첫 값. 못 물었으면 None."""
    import ctypes
    times = [ctypes.c_ulonglong() for _ in range(4)]
    return times[0].value if kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)) else None


def process_alive(pid: Any, born: Any = None) -> bool | None:
    """그 프로세스가 아직 도나 — 모르면 None(번호가 없다 · 그런 프로세스가 없다는 답이 아닌 까닭으로 못 물었다 — 끝났다고 읽으면 도는
    보고 곁에 하나를 더 띄운다). 뜬 때(`born` — `process_born` 이 낸 값)를 주면 그 번호의 지금 프로세스가 다른 때에 떴을 때 끝났다고 읽는다 —
    바쁜 PC 는 끝난 프로세스의 번호를 몇 초 안에 남에게 준다. 뜬 때를 안 주면 번호를 받은 남도 「돈다」로 읽고 부르는 쪽의 시한이 끝을 정한다."""
    if not isinstance(pid, int) or pid <= 0:
        return None
    if sys.platform == "win32":
        import ctypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel.OpenProcess(QUERY_LIMITED, False, pid)
        if not handle:
            return False if ctypes.get_last_error() == NO_SUCH_PROCESS else None
        try:
            if isinstance(born, int) and _born(kernel, handle) not in (None, born):
                return False
            code = ctypes.c_ulong()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)                                          # POSIX 의 0 은 묻기만 한다
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def find_claude(explicit: str | None) -> pathlib.Path | None:
    """띄울 claude 의 자리 — `--claude` 가 가리키는 파일, 없으면 PATH 에서 `CLAUDE_NAMES` 차례. 못 찾으면 None."""
    if explicit:
        path = pathlib.Path(explicit).expanduser()
        return path.resolve() if path.is_file() else None
    for name in C.CLAUDE_NAMES:
        found = shutil.which(name)
        if found:
            return pathlib.Path(found)
    return None


def pick_claude(given: str | None, saved: str | None) -> pathlib.Path | None:
    """띄울 claude 를 고른다 — 준 것(`--claude`)이 있으면 그것, 없으면 걸어 둔 것(그 파일이 있으면 적힌 그대로 — 바로 가기를 풀어 판의 자리를
    굳히지 않는다), 그것도 없으면 PATH. 못 찾으면 None."""
    if given:
        return find_claude(given)
    return (pathlib.Path(saved) if saved and pathlib.Path(saved).is_file() else None) or find_claude(None)


def _loopback_proxy(env: dict[str, str]) -> bool:
    """claude 의 요청이 루프백 프록시를 지나나 — `ANTHROPIC_BASE_URL` 이 `http://<루프백>:<포트>/…` 일 때만."""
    try:
        parts = urlsplit(env.get(C.BASE_URL_ENV) or "")
        port = parts.port
    except ValueError:
        return False
    return parts.scheme == "http" and parts.hostname in C.LOOPBACK_HOSTS and bool(port)


def child_env(env: dict[str, str]) -> dict[str, str]:
    """띄울 claude 의 환경 — 겹친 세션의 표지를 걷고, 루프백 프록시를 지나면 보고의 표 머리를 싣는다(`C.RUNNER_HEADER`).
    이미 든 다른 머리 줄은 그대로 둔다. 프록시가 없는 자리(사외 · 게이트웨이 직결)는 머리를 안 싣는다."""
    out = {k: v for k, v in env.items() if k not in C.NESTED_ENV}
    if _loopback_proxy(out):
        lines = [line for line in (out.get(C.CUSTOM_HEADERS_ENV) or "").splitlines()
                 if line.strip() and line.split(":", 1)[0].strip().lower() != C.RUNNER_HEADER]
        out[C.CUSTOM_HEADERS_ENV] = "\n".join(lines + [f"{C.RUNNER_HEADER}: {C.RUNNER_HEADER_VALUE}"])
    return out
