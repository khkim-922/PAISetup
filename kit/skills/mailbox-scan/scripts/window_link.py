"""보고 창 이음 — 형제 스킬 daily-brief 의 보고 창 손(`window.py --sheet` · `ticks.py --times` · `--times-done` · `--away-done` ·
`--presses` · `--sync`)을 이 스킬에서 부르는 유일한 자리. 그 손이 내는 줄의 꼴(고르신 시각 · 자리 밖에서 보기)도 여기서 읽는다.

    if edge_listening(): got = ask_window(ticks, ["--times"])   # 로그인 Edge 의 디버깅 포트가 받을 때만 묻는다 — 못 돌았으면 빈 글
    sheet, why = sheet_of(brief, date, slot)     # 보고 글 한 장 → 메일 한 장(JSON 바이트)
    line = window_presses()                      # 「일정에 넣기」 누름을 거둔다 — 창 곁의 손이 없을 때의 뒷받침
    said = tell_window()                         # 대화에서 시각표를 바꾼 뒤 열린 창에 알린다

창에서 고르신 것을 어떻게 받나는 `references/DESIGN.md` 「보고 창 이음」이 든다.
"""

from __future__ import annotations

import os
import pathlib
import re
import socket
import subprocess
import sys

import scan_const as C
import scan_hand as H
import scan_store as st


BRIEF_DIR = C.SKILLS_ROOT / C.BRIEF_SKILL                 # 일일 보고 스킬 — 이 스킬과 같은 스킬 뿌리에 나란히 선다
WINDOW = BRIEF_DIR / pathlib.Path(*C.BRIEF_WINDOW)         # 보고 창 손 — 메일 한 장(--sheet)
TICKS = BRIEF_DIR / pathlib.Path(*C.BRIEF_TICKS)           # 거두는 손 — 고르신 것 · 돌려 적기 · 누름 · 알리기
# 보고 창 손(`ticks.py --times`)이 내는 고르신 시각의 줄 — 꼴의 원본은 그 손의 `TIMES_LINE`. 고른 때는 그 손에 그대로 돌려준다
CLOCKS = r"(?:\d{1,2}:\d{2})(?: \d{1,2}:\d{2})*"
WINDOW_TIMES = re.compile(rf"^고르신 보고 시각: ({CLOCKS}) · 보던 시각: ({CLOCKS}|-) · 고르신 때 (\S{{1,40}})$", re.M)
# 같은 손이 내는 고르신 「자리 밖에서 보기」의 줄 — 꼴의 원본은 그 손의 `AWAY_LINE`. 켬 · 끔은 JSON 의 참 · 거짓 글자다
WINDOW_AWAY = re.compile(r"^고르신 자리 밖에서 보기: (true|false) · 고르신 때 (\S{1,40})$", re.M)
SAID_CHARS = 240                                     # 보고 창에 돌려 적는 말의 글자 수


def edge_listening() -> bool:
    """이 PC 의 로그인 Edge 디버깅 포트가 받나 — 안 받으면 보고 창을 묻는 손을 안 띄운다(판마다 프로세스 하나를 아낀다)."""
    port = os.environ.get(C.EDGE_PORT_ENV, "").split(",")[0].strip()
    port = int(port) if port.isdigit() and 0 < int(port) < 65536 else C.EDGE_PORT_DEFAULT
    try:
        with socket.create_connection((C.EDGE_HOST, port), timeout=C.EDGE_PROBE_S):
            return True
    except OSError:
        return False


def sheet_of(brief: pathlib.Path, date: str, slot: str) -> tuple[bytes, str]:
    """보고 글 한 장 → 메일 한 장(일일 보고의 보고 창 손 `window.py --sheet` 가 창과 같은 글에서 짓는다). `date` 는 그 칸이 든 날(그날 칸의
    기록의 날 — 제목이 그 칸의 날을 댄다). 내는 것 — (JSON 바이트, "") 나 (b"", 까닭)."""
    try:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(WINDOW), "--dir", str(st.home()), "--sheet", brief.name, "--slot", f"{date} {slot}"],
                              capture_output=True, timeout=C.AWAY_SHEET_TIMEOUT_S, stdin=subprocess.DEVNULL,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **H.quiet())
    except (subprocess.TimeoutExpired, OSError) as exc:
        return b"", f"보고 창 손이 메일 한 장을 못 지었습니다({type(exc).__name__})"
    if done.returncode != 0:
        lines = done.stdout.decode("utf-8", "replace").strip().splitlines()
        return b"", f"보고 창 손이 메일 한 장을 못 지었습니다({lines[-1][:120] if lines else f'종료 {done.returncode}'})"
    return done.stdout, ""


def window_presses() -> str:
    """보고 창에서 누르신 「일정에 넣기」를 거둔다 — 창 곁의 손이 없을 때의 뒷받침이다. 판단 없이 일일 보고의 넣는 손(`ticks.py --presses`)이
    누른 카드의 열쇠로 일정 손을 부르고 끝을 그 창에 돌려 적는다(창 곁의 손이 먼저 넣은 누름은 그 손의 기록으로 지나간다). 보고를 걸었든
    안 걸었든 판마다 한다 — 대화에서 청한 보고의 창도 누름을 받는다. 열린 보고 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다.
    내는 것 — 판 끝에 찍을 한 줄(할 말이 없으면 "")."""
    if not TICKS.is_file() or not edge_listening():
        return ""
    lines = ask_window(TICKS, ["--presses", "--within", str(C.BRIEF_PRESSES_WITHIN_S)], C.BRIEF_PRESSES_TIMEOUT_S).strip().splitlines()
    said = lines[-1].strip() if lines else ""
    return f"[보고 창 — {said}]" if said.startswith("보고 창의") else ""


def tell_window() -> str:
    """대화에서 시각표를 바꾼 뒤 열린 보고 창에 바로 알린다 — 일일 보고의 거두는 손(`ticks.py --sync`)으로 이 PC 의 디버깅 포트가 받을 때만.
    창이 없거나 못 닿으면 ""(창은 그 뒤 스캔 판이나 다음 거두기가 알린다)."""
    if not TICKS.is_file() or not edge_listening():
        return ""
    said = ask_window(TICKS, ["--sync"]).strip().splitlines()
    return said[-1] if said and said[-1].startswith("열린 보고 창에") else ""


def ask_window(ticks: pathlib.Path, args: list[str], timeout: int = C.BRIEF_TIMES_TIMEOUT_S) -> str:
    """보고 창 손 한 번 — 표준 출력. 못 돌았으면 빈 글."""
    try:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ticks), "--dir", str(st.home()), *args], capture_output=True,
                              timeout=timeout, stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                              **H.quiet())
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return done.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
