"""그날 장부와 아직 말하지 않은 칸 — 그날 장부를 열 때 지난날 건너뛴 칸의 줄을 남기고, 띄우는 보고의 부탁 글에 실을 줄을 엮는 손.

    day = today(folder, state, at, setting)              # 그날 장부 — 날이 바뀌었으면 새 장부에 지난날 줄(`before`)을 남긴다
    lines = told_lines(folder, day, times, at, setting)  # 이 판에 띄우는 보고가 말할 건너뛴 칸 · 못 간 메일의 줄
"""

from __future__ import annotations

import pathlib
from datetime import datetime, timedelta
from typing import Any

from brief_day import roll_day
from brief_slots import noon_of, on_day
from brief_state import untold
from brief_words import dated_lines, told_words


def today(folder: pathlib.Path, state: dict[str, Any], at: datetime, setting: dict[str, Any], keep: bool = True) -> dict[str, Any]:
    """그날 장부를 연다 — 날이 바뀌었으면 새 장부에 지난날 건너뛴 칸의 줄(`before`)을 남긴다. `keep` 이면 판의 상태에 넣는다(판 안에서만). `folder` 는 보고 글이 선 사용자 폴더."""
    times = setting["times"]
    day, old = roll_day(state, at, times, keep)
    if old is not None:
        before = yesterday_lines(folder, old, times, setting)
        if before:
            day["before"] = before
    return day


def yesterday_lines(folder: pathlib.Path, old: dict[str, Any], times: list[str], setting: dict[str, Any] | None) -> list[str]:
    """지난날 장부에서 보고 없이 끝난 칸의 줄 — 그날이 다 끝난 때(자정)로 재고 줄마다 그날을 단다. 날을 못 읽으면 빈 것."""
    noon = noon_of(old.get("date"))
    if noon is None:
        return []
    then = on_day("00:00", noon) + timedelta(days=1)       # 그날이 다 끝난 때 — 자정까지 기다린 칸도 끝났다
    return dated_lines(f"{noon.month}/{noon.day}", told_words(untold(folder, {**old, "before": []}, times, noon, then, setting), []))


def told_lines(folder: pathlib.Path, day: dict[str, Any], times: list[str], at: datetime, setting: dict[str, Any]) -> list[str]:
    """이 판에 띄우는 보고가 말할 줄 — 마지막 보고 뒤 건너뛴 칸 · 글 없이 끝난 칸 · 못 띄운 칸 · 지난날 줄 · 못 간 메일."""
    return told_words(untold(folder, day, times, at, setting=setting), day.get("before") or [])
