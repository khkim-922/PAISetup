"""누름 종류마다 재는 반 — 창의 저장소 열쇠 · 거둘 때인가(`due`) · 그 창에 돌려 적을 칸(`back`). 창 곁의 손(`presses.KINDS` — 할 일 · 거두는
걸음을 더한다)과 시계 판이 부르는 창의 문(`window_door`)이 이 한 표로 재고 같은 칸을 적는다. 할 일을 부르지 않고 창 · 파일에 닿지 않는다.
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
import brief_const as C  # noqa: E402
import clock as T  # noqa: E402
import edge as E  # noqa: E402
from records import SESSION  # noqa: E402

SESSION_RETRY_S = 300                          # 사내 로그인이 끊겨 못 넣은 누름을 창 곁의 손이 다시 해 보는 사이 — 매 걸음 세션 손을 두드리지 않게.
                                               # 시계 판은 이 사이를 안 기다린다 — 판이 드물어(기본 15분) 살아난 세션을 곧 받는다


def due(press: dict, eager: bool = False) -> bool:
    """거둘 누름인가 — 아직 안 맺었고, 사내 로그인이 끊겨 못 넣은 것은 `SESSION_RETRY_S` 가 지난 것만(`eager` — 시계 판 — 면 늘)."""
    if press.get("done"):
        return False
    if eager:
        return True
    tried = E.pressed_at({"at": press.get("tried")}) if press.get("tried") else None
    return tried is None or (T.seoul_now() - tried).total_seconds() >= SESSION_RETRY_S


def put_due(press: dict, eager: bool = False) -> dict | None:
    """「일정에 넣기」 누름 하나가 거둘 때인가 — 그 누름(할 일 `settle` 이 받는다) · 아니면 None(`due`)."""
    return press if due(press, eager) else None


def put_back(press: dict, state: str, said: str) -> dict:
    """그 창에 돌려 적을 「일정에 넣기」 칸 — 끝과 말, 맺었으면 맺은 때 · 사내 로그인이 끊겨 못 넣었으면 해 본 때(그 누름은 남아 다시 해 본다)."""
    row = {**press, "state": state, "said": said}
    if state == SESSION:
        row["tried"] = T.stamp(T.seoul_now())
    else:
        row["done"] = T.stamp(T.seoul_now())
    return row


def away_due(row: dict | None, eager: bool = False) -> tuple[bool, str] | None:
    """「자리 밖에서 보기」 고름이 거둘 때인가 — (켬인가, 고른 때) · 아니면 None. 안 받은 고름만 — 못 부른 고름은 `SESSION_RETRY_S` 뒤에
    다시 해 본다(`eager` — 시계 판 — 면 늘)."""
    if not row or row.get("done") or not isinstance(row.get("on"), bool) or not C.AT.match(str(row.get("at") or "")) or not due(row, eager):
        return None
    return row["on"], str(row["at"])


def times_due(row: dict | None, eager: bool = False) -> tuple[list[str], list[str], str] | None:
    """「보고 시각」 고름(「이대로 바꾸기」)이 거둘 때인가 — (고르신 시각, 그때 보던 시각, 고른 때) · 아니면 None. 시각은 「HH:MM」 꼴만 ·
    겹침 없이 차례로. 안 받은 고름만(`away_due` 와 같은 다시 해 보기)."""
    picked = row.get("times") if row else None
    if not row or row.get("done") or not (isinstance(picked, list) and picked and all(isinstance(t, str) and C.HHMM.match(t) for t in picked)) \
            or not C.AT.match(str(row.get("at") or "")) or not due(row, eager):
        return None
    base = [t for t in row.get("base") or [] if isinstance(t, str) and C.HHMM.match(t)] if isinstance(row.get("base"), list) else []
    return sorted(set(picked)), sorted(set(base)), str(row["at"])


def said_back(row: dict, said: str, refused: bool) -> dict:
    """스캔의 명령이 고름을 받았나를 그 창에 돌려 적을 칸 — 받은 때 · 그 끝 줄(한 줄로 · `brief_const.SAID_MAX` 에서 자른다) · 안 따랐나."""
    return {**row, "done": T.stamp(T.seoul_now()), "said": " ".join(said.split())[:C.SAID_MAX], "refused": refused}


def ask_due(row: dict | None, eager: bool = False) -> tuple[str, str, str] | None:
    """창 머리의 부탁이 거둘 때인가 — (친 말, 누른 창의 이름, 들고 온 세션) · 아니면 None. 안 맡은 부탁이 누른 지 `brief_const.ASK_TAKE_S`
    안일 때만 — 그보다 늦은 부탁은 안 연다: 창이 이미 「못 열었다」로 맺었거나 맺는다. 친 말은 읽어 가르지 않는다. 시계 판은 부탁을 안
    거둔다 — `eager` 를 안 본다."""
    if not row or row.get("done") or row.get("taken") or not C.AT.match(str(row.get("at") or "")):
        return None
    words, at = row.get("words"), E.pressed_at(row)
    if not (isinstance(words, str) and words.strip()) or at is None or (T.seoul_now() - at).total_seconds() >= C.ASK_TAKE_S:
        return None
    return words.strip(), str(row.get("brief") or ""), str(row.get("session") or "")


def ask_back(taken: dict, state: str, said: str) -> dict:
    """그 창에 돌려 적을 부탁의 칸 — 맡은 칸에 맺은 때 · 끝 · 말."""
    return {**taken, "done": T.stamp(T.seoul_now()), "state": state, "said": said}


@dataclass(frozen=True)
class Measure:
    """누름 종류 하나의 재는 반 — `key` 창의 저장소 열쇠(끝이 「:」 면 머리 — 누름마다 그 뒤가 열쇠) · `due(누름, 시계 판인가)` 거둘 때면 할 일이
    받을 값, 아니면 None · `back(누름, 끝…)` 그 창에 돌려 적을 칸."""
    name: str
    key: str
    due: Callable[..., Any]
    back: Callable[..., dict]


ASK = Measure("부탁", C.ASK_KEY, ask_due, ask_back)
PUT = Measure("일정에 넣기", C.CAL_PREFIX, put_due, put_back)
AWAY = Measure("자리 밖에서 보기", C.AWAY_KEY, away_due, said_back)
TIMES = Measure("보고 시각", C.TIMES_KEY, times_due, said_back)
