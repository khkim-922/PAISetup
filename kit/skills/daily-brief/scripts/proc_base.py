"""프로세스 바탕 — 곁의 파이썬 손(회사 메일 손 · 형제 스킬의 입구)을 창 없이 · UTF-8 로 띄우는 한 자리.

이 파일의 원본은 스킬 mailbox-scan 의 `scripts/proc_base.py` 다 — 같은 몸이 필요한 위 스킬은 이 파일을 바이트째 베껴 들고(스킬끼리 코드를
싣지 않는다), 원본 스킬은 누가 베끼는지 모른다. 원본만 고치고 베낀다.

    subprocess.run(cmd, **quiet())               # 창 없는 실행에서 띄운 것이 콘솔 창을 안 띄우게
    done = run_python(script, args, timeout)     # 곁의 파이썬 스크립트 한 번 — 출력을 받는다
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
from typing import Any


def quiet() -> dict[str, Any]:
    """창 없는 실행(작업 스케줄러의 pythonw)에서 띄운 손 · 손이 띄우는 node 가 콘솔 창을 안 띄우게 하는 `subprocess` 인자 — 창 없는 콘솔을 준다."""
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}


def python_argv(script: pathlib.Path, *args: str) -> list[str]:
    """곁의 파이썬 스크립트를 지금 파이썬으로 부르는 명령줄 — `-X utf8 -I`(UTF-8 · 사용자 자리의 모듈을 안 싣는다)."""
    return [sys.executable, "-X", "utf8", "-I", str(script), *args]


def utf8_env() -> dict[str, str]:
    """띄운 파이썬이 출력을 UTF-8 로 내게 하는 환경 — 지금 환경에 `PYTHONIOENCODING` 만 얹는다."""
    return {**os.environ, "PYTHONIOENCODING": "utf-8"}


def run_python(script: pathlib.Path, args: list[str], timeout: float, given: bytes | None = None) -> subprocess.CompletedProcess:
    """곁의 파이썬 스크립트 한 번 — 창 없이 · UTF-8 로 띄워 출력을 받는다. `given` 이 있으면 표준 입력으로 주고, 없으면 표준 입력을 닫는다.
    시한을 넘기면 `subprocess.TimeoutExpired`, 못 띄우면 `OSError` 를 그대로 낸다."""
    stdin = {"input": given} if given is not None else {"stdin": subprocess.DEVNULL}
    return subprocess.run(python_argv(script, *args), capture_output=True, timeout=timeout, env=utf8_env(), **stdin, **quiet())
