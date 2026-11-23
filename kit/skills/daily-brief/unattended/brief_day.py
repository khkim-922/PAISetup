"""그날 칸 장부 — 지금 모습(`state["brief"]`) 안의 그날 칸을 열고 고른다. 서울 날짜가 바뀌면 새 장부를 열고 지난날 건너뛴 시각을 한 줄로
남긴다. 시각 하나를 쓰던 꼴의 장부는 첫 시각의 칸으로 옮겨 읽는다.

    day, old = roll_day(state, at, times)        # 그날 장부 — 날이 바뀌었으면 새 장부와 지난날 장부(keep 이면 지금 모습에 넣는다)
    slot = slot_of(day, t)                       # 그 시각의 칸 — 없으면 만든다
    t = next_slot(setting, state, folder, at)    # 다음 사람 없는 보고의 시각 — 오늘 남은 칸이 없으면 None
"""

from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Any

from brief_slots import seoul_date, windows
from brief_kinds import SETTLED
from brief_state import slot_state


def migrated(got: dict[str, Any], times: list[str]) -> dict[str, Any]:
    """시각 하나를 쓰던 꼴의 그날 장부 → 칸 꼴(첫 시각의 칸). 이미 칸 꼴이면 그대로."""
    if "slots" in got:
        return got
    old = {"tries": got.get("tries") or [], "launched": got.get("launched")}
    return {"date": got.get("date"), "slots": {times[0]: old} if times and (old["tries"] or old["launched"]) else {},
            "login": got.get("login")}


def roll_day(state: dict[str, Any], at: datetime, times: list[str], keep: bool = True) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """그날의 살펴보기 장부 — 서울 날짜가 바뀌었으면 새 장부를 연다. 시각 하나를 쓰던 꼴의 장부는 첫 시각의 칸으로 옮겨 읽는다. `keep` 이면
    지금 모습에 넣는다(판 안에서만 — status 는 안 바꾼다). 내는 것 — (그날 장부, 날을 넘긴 지난날 장부 · 안 넘겼거나 날이 없으면 None)."""
    got = state.get("brief")
    if isinstance(got, dict) and "slots" not in got:
        got = migrated(got, times)
        if keep:
            state["brief"] = got
    if not isinstance(got, dict) or got.get("date") != seoul_date(at):
        old = got if isinstance(got, dict) and got.get("date") else None
        got = {"date": seoul_date(at), "slots": {}, "login": None}
        if keep:
            state["brief"] = got
        return got, old
    return got, None


def today_of(state: dict[str, Any], at: datetime, times: list[str]) -> dict[str, Any]:
    """그날 장부의 칸만 읽는다 — 지금 모습을 안 바꾸고, 날이 바뀌었으면 빈 칸들(지난날 줄은 안 셈한다)."""
    got = state.get("brief")
    got = migrated(got, times) if isinstance(got, dict) else None
    return got if got and got.get("date") == seoul_date(at) else {"date": seoul_date(at), "slots": {}}


def slot_of(day: dict[str, Any], t: str) -> dict[str, Any]:
    """그날 장부의 그 시각 칸 — 없으면 빈 칸을 만들어 넣는다."""
    return day.setdefault("slots", {}).setdefault(t, {"tries": [], "launched": None})


def last_try(state: dict[str, Any]) -> str | None:
    """그날 가장 늦은 살펴보기의 답 — 판 기록에 싣는다. 없으면 None."""
    tries = [t for s in ((state.get("brief") or {}).get("slots") or {}).values() for t in s.get("tries") or []]
    return max(tries, key=lambda t: t.get("at") or "").get("session") if tries else None


def next_slot(setting: dict[str, Any], state: dict[str, Any] | None, folder: pathlib.Path, at: datetime) -> str | None:
    """다음 사람 없는 보고의 시각 — 지금 모습(`state` · 모르면 None — 오늘 남은 첫 칸을 댄다)의 그날 장부에서 오늘 아직 안 띄운 칸 가운데
    끝나지 않은 첫 것. 없으면 None. `folder` 는 앞 칸이 띄운 보고의 잠금을 볼 자리."""
    times = setting["times"]
    day = today_of(state or {}, at, times)
    for order, (t, _, _, end) in enumerate(windows(times, at)):
        if at < end and slot_state(day, times, order, at, at, setting, folder).state not in SETTLED:
            return t
    return None
