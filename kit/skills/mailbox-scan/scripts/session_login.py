"""사내 세션 살피기와 스스로 로그인 — 회사 메일 손의 `session` 한 번으로 사내 세션이 살았나를 보고, 스스로 로그인을 켠 PC 에서는 형제 스킬
ep-login 의 입구를 사람 없는 꼴로 부른다. 살피기는 로그인 화면을 열지 않는다.

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

import scan_const as C
import scan_hand as H
import scan_store as st


LIVE, LOST, ERROR = "live", "lost", "error"          # 살펴보기의 답 — 사내 세션이 살았다 · 없다 · 손이 답을 못 냈다


def look(hand: pathlib.Path | None) -> str:
    """사내 세션이 살았나 — 손의 `session` 한 번. 로그인 화면을 열지 않는다."""
    if hand is None:
        return ERROR
    try:
        got = H.call(hand, ["session"])
    except H.ShapeError:
        return ERROR
    return LIVE if got.code == C.HAND_EXIT_OK else LOST if got.code == C.HAND_EXIT_SESSION else ERROR


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


def login_command(hand: pathlib.Path | None) -> list[str] | None:
    """스스로 로그인이 부를 명령 — 입구나 node 가 없으면 None(거는 명령이 이것으로 거절하고 `--dry-run` 이 보인다)."""
    script, node = entrance(hand), shutil.which(C.LOGIN_NODE)
    return [node, str(script), *C.LOGIN_ARGS] if script is not None and node is not None else None


def sign_in(hand: pathlib.Path | None, at: datetime) -> dict[str, Any]:
    """스스로 로그인 한 번 — 입구를 사람 없는 꼴로 부른다(사람이 쳐야 하는 자리에서는 입구가 기다리지 않고 끝난다).
    내는 것 — {at, ok: True} 나 {at, ok: False, said}."""
    def failed(said: str) -> dict[str, Any]:
        return {"at": st.stamp(at), "ok": False, "said": said[:C.LOGIN_SAID_CHARS]}
    script, node = entrance(hand), shutil.which(C.LOGIN_NODE)
    if script is None:
        return failed("로그인 입구(스킬 ep-login)를 못 찾았다")
    if node is None:
        return failed("node 를 못 찾았다")
    try:
        done = subprocess.run([node, str(script), *C.LOGIN_ARGS], capture_output=True, timeout=C.LOGIN_TIMEOUT_S,
                              stdin=subprocess.DEVNULL, **H.quiet())
    except subprocess.TimeoutExpired:
        return failed(f"로그인 입구가 {C.LOGIN_TIMEOUT_S}초 안에 안 끝났다")
    except OSError as exc:
        return failed(f"{type(exc).__name__}: {exc}")
    if done.returncode == 0:
        return {"at": st.stamp(at), "ok": True}
    lines = [x.strip() for x in done.stderr.decode("utf-8", "replace").splitlines() if x.strip()]
    return failed(lines[-1] if lines else f"로그인 입구가 종료 {done.returncode} 로 끝났다")
