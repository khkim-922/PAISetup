"""보고 창 이음 — 같은 스킬의 보고 창 손(`window.py --sheet` · `ticks.py --times-done` · `--away-done` · `--presses`)을 사람 없는 실행에서
프로세스로 부르고, 대화에서 시각표를 바꾼 뒤 열린 창에 알리는(`state.sync`) 유일한 자리. 고르신 것을 읽는 쪽은 창의 문이 함수로 낸다
(`window_door.read_choices`).

    if edge_listening(): ask_window(folder, ticks, ["--times-done", at, "--said", said])   # 로그인 Edge 의 디버깅 포트가 받을 때만 — 못 돌았으면 빈 글
    sheet, why = sheet_of(folder, brief, date, slot)     # 보고 글 한 장 → 메일 한 장(JSON 바이트)
    line = window_presses(folder)                        # 「일정에 넣기」 누름을 거둔다 — 창 곁의 손이 없을 때의 뒷받침
    said = tell_window(folder)                           # 대화에서 시각표를 바꾼 뒤 열린 창에 알린다 — 대화 줄 끝에 붙일 「 · …」 구절

창에서 고르신 것을 어떻게 받나는 `references/DESIGN.md` 「보고 창 이음」이 든다.
"""

from __future__ import annotations

import pathlib
import socket
import subprocess

import edge as E
import proc_base as P
import state as V
import unattended_const as C
from brief_const import EDGE_HOST, ROUND_HEAD


SAID_CHARS = 240                                     # 보고 창에 돌려 적는 말의 글자 수


def edge_listening() -> bool:
    """이 PC 의 로그인 Edge 디버깅 포트(`edge.port`)가 받나 — 안 받으면 보고 창을 묻는 손을 안 띄운다(판마다 프로세스 하나를 아낀다)."""
    try:
        with socket.create_connection((EDGE_HOST, E.port()), timeout=C.EDGE_PROBE_S):
            return True
    except OSError:
        return False


def sheet_of(folder: pathlib.Path, brief: pathlib.Path, date: str, slot: str) -> tuple[bytes, str]:
    """사용자 폴더의 보고 글 한 장 → 메일 한 장(보고 창 손 `window.py --sheet` 가 창과 같은 글에서 짓는다). `date` 는 그 칸이 든 날(그날 칸의
    기록의 날 — 제목이 그 칸의 날을 댄다). 내는 것 — (JSON 바이트, "") 나 (b"", 까닭)."""
    try:
        done = P.run_python(C.WINDOW_SCRIPT, ["--dir", str(folder), "--sheet", brief.name, "--slot", f"{date} {slot}"], C.AWAY_SHEET_TIMEOUT_S)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return b"", f"보고 창 손이 메일 한 장을 못 지었습니다({type(exc).__name__})"
    if done.returncode != 0:
        lines = done.stdout.decode("utf-8", "replace").strip().splitlines()
        return b"", f"보고 창 손이 메일 한 장을 못 지었습니다({lines[-1][:120] if lines else f'종료 {done.returncode}'})"
    return done.stdout, ""


def window_presses(folder: pathlib.Path) -> str:
    """보고 창에서 누르신 「일정에 넣기」를 거둔다 — 창 곁의 손이 없을 때의 뒷받침이다. 판단 없이 일일 보고의 넣는 손(`ticks.py --presses`)이
    누른 카드의 열쇠로 일정 손을 부르고 끝을 그 창에 돌려 적는다(창 곁의 손이 먼저 넣은 누름은 그 손의 기록으로 지나간다). 보고를 걸었든
    안 걸었든 시계 판마다 한다 — 대화에서 청한 보고의 창도 누름을 받는다. 열린 보고 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다.
    내는 것 — 판 끝에 찍을 한 줄(할 말이 없으면 "")."""
    if not C.TICKS_SCRIPT.is_file() or not edge_listening():
        return ""
    # 넣는 손은 끝 안에서 빌려 다시 넣기까지만 시작한다 — 끝을 넘을 수 있는 것은 쓴다고 적기가 잠금을 기다림(돌려주는 문 한 번)과 끝 뒤의 놓기 한 번이다
    lines = ask_window(folder, C.TICKS_SCRIPT, ["--presses", "--within", str(C.BRIEF_PRESSES_WITHIN_S)],
                       C.BRIEF_PRESSES_TIMEOUT_S + C.LEND_TIMEOUT_S + C.GIVE_BACK_TIMEOUT_S).strip().splitlines()
    said = lines[-1].strip() if lines else ""
    return f"[보고 창 — {said}]" if said.startswith(ROUND_HEAD) else ""       # 거둔 수가 있는 끝 줄만


def tell_window(folder: pathlib.Path) -> str:
    """대화에서 시각표를 바꾼 뒤 열린 보고 창에 바로 알린다 — 이 PC 의 디버깅 포트가 받을 때만 창의 지금 모습을 적는다(`state.sync`). 내는 것 —
    알렸으면 대화 줄 끝에 붙일 구절(「 · 열린 보고 창에 …」), 창이 없거나 못 닿으면 ""(창은 그 뒤 시계 판이나 다음 거두기가 알린다)."""
    if not edge_listening():
        return ""
    said = V.sync(folder)
    return f" · {said}" if said else ""


def ask_window(folder: pathlib.Path, ticks: pathlib.Path, args: list[str], timeout: int = C.BRIEF_TIMES_TIMEOUT_S) -> str:
    """보고 창 손 한 번(사용자 폴더 `folder`) — 표준 출력. 못 돌았으면 빈 글."""
    try:
        done = P.run_python(ticks, ["--dir", str(folder), *args], timeout)
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return done.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
