"""사내 세션 — 회사 메일 손의 `session` 한 번으로 사내 세션이 살았나를 보고, 보고 시각을 건 PC 에서는 그 시각에 형제 스킬 ep-login 의
입구를 사람 없는 꼴로 부른다. 살피기는 로그인 화면을 열지 않는다.

    got = look(hand)                    # LIVE · LOST · ERROR — 살았다 · 없다 · 손이 답을 못 냈다
    cmd = login_command(hand)           # 스스로 로그인이 부를 명령 — 입구나 node 가 없으면 None(거는 명령이 이것으로 거절한다)
    signed = sign_in(hand, at)          # 입구 한 번 — {at, ok: True} 나 {at, ok: False, said}

언제 로그인하고 언제 안 하나는 `references/DESIGN.md` 「정한 시각의 보고」가 든다.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
from datetime import datetime
from typing import Any

import clock as tm
import proc_base as P
import unattended_const as C


LIVE, LOST, ERROR = C.SESSION_LIVE, C.SESSION_LOST, C.SESSION_ERROR   # 살펴보기의 답(값의 자리는 unattended_const)


def look(hand: pathlib.Path | None) -> str:
    """사내 세션이 살았나 — 손의 `session` 한 번의 종료 값. 로그인 화면을 열지 않는다. 손이 없거나 · 시한을 넘기거나 · 못 띄웠거나 · 출력을
    UTF-8 로 못 풀면 ERROR(손이 답을 못 냈다)."""
    if hand is None:
        return ERROR
    try:
        done = P.run_python(hand, ["session"], C.HAND_TIMEOUT_S)
        done.stdout.decode("utf-8")
    except (subprocess.TimeoutExpired, OSError, UnicodeDecodeError):
        return ERROR
    return LIVE if done.returncode == C.HAND_EXIT_OK else LOST if done.returncode == C.HAND_EXIT_SESSION else ERROR


def entrance(hand: pathlib.Path | None) -> pathlib.Path | None:
    """형제 스킬 ep-login 의 입구 — `LOGIN_ENTRANCE_ENV`, 없으면 손과 같은 스킬 뿌리의 그 스킬. 없으면 None."""
    given = os.environ.get(C.LOGIN_ENTRANCE_ENV, "").strip()
    if given:
        path = pathlib.Path(given)
    elif hand is not None:
        path = hand.parents[2] / C.SESSION_SKILL / pathlib.Path(*C.LOGIN_ENTRANCE)
    else:
        return None
    return path if path.is_file() else None


def login_parts(hand: pathlib.Path | None) -> tuple[pathlib.Path | None, str | None]:
    """스스로 로그인이 부를 것 — (입구 · 없으면 None, node · 없으면 None)."""
    return entrance(hand), shutil.which(C.LOGIN_NODE)


def login_command(hand: pathlib.Path | None) -> list[str] | None:
    """스스로 로그인이 부를 명령 — 입구나 node 가 없으면 None(거는 줄 · `--dry-run` 이 그 PC 에서는 로그인이 안 선다고 말한다)."""
    return command_of(*login_parts(hand))


def command_of(script: pathlib.Path | None, node: str | None) -> list[str] | None:
    """입구 · node 로 스스로 로그인의 명령줄 — 하나라도 없으면 None."""
    return [node, str(script), *C.LOGIN_ARGS] if script is not None and node is not None else None


def sign_in(hand: pathlib.Path | None, at: datetime) -> dict[str, Any]:
    """스스로 로그인 한 번 — 입구를 사람 없는 꼴로 부른다(사람이 쳐야 하는 자리에서는 입구가 기다리지 않고 끝난다).
    내는 것 — {at, ok: True} 나 {at, ok: False, said}."""
    def failed(said: str) -> dict[str, Any]:
        """입구가 못 세운 끝 — 그 끝말을 줄여 싣는다."""
        return {"at": tm.utc_stamp(at), "ok": False, "said": said[:C.LOGIN_SAID_CHARS]}
    script, node = login_parts(hand)
    if script is None:
        return failed("로그인 입구(스킬 ep-login)를 못 찾았다")
    if node is None:
        return failed("node 를 못 찾았다")
    try:
        done = subprocess.run(command_of(script, node), capture_output=True, timeout=C.LOGIN_TIMEOUT_S,
                              stdin=subprocess.DEVNULL, **P.quiet())
    except subprocess.TimeoutExpired:
        return failed(f"로그인 입구가 {C.LOGIN_TIMEOUT_S}초 안에 안 끝났다")
    except OSError as exc:
        return failed(f"{type(exc).__name__}: {exc}")
    if done.returncode == 0:
        return {"at": tm.utc_stamp(at), "ok": True}
    lines = [x.strip() for x in done.stderr.decode("utf-8", "replace").splitlines() if x.strip()]
    return failed(lines[-1] if lines else f"로그인 입구가 종료 {done.returncode} 로 끝났다")
