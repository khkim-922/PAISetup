"""status 의 보고 예약 줄 — 걸었나 · 자리 밖에서 보기 · 경고 · 지난날 · 오늘 로그인 · 오늘 돌려준 로그인 · 시각마다 오늘 어떻게 됐나를 차례로 엮는다.

    lines = describe(state, folder, at, task)    # `task` — 시계 작업이 걸렸나(None 은 안 물었다)
"""

from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Any

import clock as tm
from brief_schedule import away_of, claude_present, load
from brief_slots import first_tight, windows
from brief_state import day_logins, skip_cause, slot_login, slot_mail, slot_state, status_state
from brief_told import today
from loan import status_lines as give_back_lines
from brief_words import day_lines, head_lines, room_words, slot_line, slot_status_line, unset_lines


def describe(state: dict[str, Any] | None, folder: pathlib.Path, at: datetime, task: bool | None = None) -> list[str]:
    """status 가 말할 줄을 엮는다 — 걸었나 · 머리 줄 · 그날 장부 줄 · 시각마다 오늘 어떻게 됐나. `task` 가 False 면 시계 작업이 안 걸렸다
    (None 은 안 물었다)."""
    setting, problem = load(folder)
    if setting is None:
        return unset_lines(problem)
    times = setting["times"]
    lines = head_lines(setting, away_of(setting), windows(times, tm.utc_now()), task, claude_present(setting), room_words(first_tight(times)))
    day = today(folder, state or {}, at, setting, keep=False)
    when = tm.seoul(at, "%m/%d")
    lines += day_lines(day.get("before") or [], day_logins(day), when)
    lines += give_back_lines(state, folder, at, times, when)
    for order, (t, _, _, end) in enumerate(windows(times, at)):
        v = slot_state(day, times, order, at, at, setting, folder)
        line = slot_line(v, status_state(v, task, at), skip_cause(v.slot), slot_login(day, v.slot, order))
        lines.append(slot_status_line(when, t, line, slot_mail(v, at), end, at))
    return lines
