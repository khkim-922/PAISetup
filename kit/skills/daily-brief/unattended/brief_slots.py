"""보고 시각표의 칸 셈 — 시각표에서 그날의 칸(시각마다 덮는 첫때 · 시작 · 끝)과 틈을 셈한다. 바깥에 안 닿고 사람 말을 짓지 않는다.

    times, bad = times_given(["07:30", "13:00"]) # 받은 시각들 → 정렬한 시각표 · 꼴이 아니면 까닭
    wins = windows(times, at)                    # 그날의 칸 — (시각, 덮는 첫때, 시작, 끝)
    now = current(times, at)                     # 지금 든 칸 — 칸 밖이면 None
    tight = first_tight(times, added)            # 기다릴 틈이 모자란 첫 시각 — 없으면 None

칸과 그날의 뜻은 `references/DESIGN.md` 「정한 시각의 보고」가 든다.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import unattended_const as C
import clock as tm


def clock(text: str) -> str | None:
    """「H:MM」 · 「HH:MM」 → 「HH:MM」. 꼴이 아니면 None."""
    try:
        return datetime.strptime(text.strip(), "%H:%M").strftime("%H:%M")
    except (ValueError, AttributeError):
        return None


def times_given(texts: list[str]) -> tuple[list[str], str]:
    """받은 시각들(빈칸 · 쉼표로 여럿도) → 정렬하고 겹친 것을 걷은 시각표. 꼴이 아닌 것이 있으면 ([], 까닭)."""
    got: set[str] = set()
    for part in " ".join(texts).replace(",", " ").split():
        one = clock(part)
        if one is None:
            return [], f"보고 시각 {part!r} 가 「HH:MM」 꼴이 아니다"
        got.add(one)
    if not got:
        return [], "보고 시각이 하나도 없다"
    return sorted(got), ""


def seoul_date(at: datetime) -> str:
    """서울 날짜 「YYYY-MM-DD」 — 그날 칸 장부와 보고 글 이름의 날."""
    return tm.seoul(at, "%Y-%m-%d")


def on_day(text: str, at: datetime) -> datetime:
    """서울 날짜 `at` 의 그 시각(「HH:MM」)."""
    hour, minute = map(int, clock(text).split(":"))
    return at.astimezone(tm.SEOUL).replace(hour=hour, minute=minute, second=0, microsecond=0)


def noon_of(date_text: Any) -> datetime | None:
    """저장된 날짜(「YYYY-MM-DD」)의 서울 정오 — 그날의 칸을 셈할 바탕. 꼴이 아니면 None."""
    try:
        date = datetime.strptime(str(date_text), "%Y-%m-%d")
    except ValueError:
        return None
    return on_day("12:00", date.replace(tzinfo=tm.SEOUL))


def minute(t: datetime) -> int:
    """분 단위의 때 — 틈을 분으로 잰다."""
    return int(t.timestamp() // 60)


def until_given() -> str | None:
    """검사가 준 기다림의 끝 「HH:MM」(`BRIEF_UNTIL_ENV`) — 없으면 None(시각마다 `BRIEF_WAIT_MIN` 분까지)."""
    return clock(os.environ.get(C.BRIEF_UNTIL_ENV, ""))


def windows(times: list[str], at: datetime) -> list[tuple[str, datetime, datetime, datetime]]:
    """그날의 칸 — 시각마다 (시각, 덮는 첫때, 시작, 끝). 끝은 다음 시각 · 그 시각에서 `BRIEF_WAIT_MIN` 분 뒤 · 그날 자정 가운데 이른 것.
    덮는 첫때는 앞 칸의 끝(첫 칸은 그날 0시)이다 — 그 뒤 이 칸의 끝 전에 지은 보고 글(대화에서 지은 것도)이 이 칸의 보고다."""
    starts = [on_day(t, at) for t in times]
    midnight = on_day("00:00", at)
    given = until_given()
    out: list[tuple[str, datetime, datetime, datetime]] = []
    for i, (t, start) in enumerate(zip(times, starts)):
        cap = on_day(given, at) if given else start + timedelta(minutes=C.BRIEF_WAIT_MIN)
        end = min(cap, midnight + timedelta(days=1), *starts[i + 1:i + 2])
        out.append((t, out[-1][3] if out else midnight, start, end))
    return out


def current(times: list[str], at: datetime) -> tuple[int, str, datetime, datetime, datetime] | None:
    """지금 든 칸 — (차례, 시각, 덮는 첫때, 시작, 끝). 첫 시각 전 · 칸 사이 · 마지막 칸 뒤면 None."""
    for i, (t, cover, start, end) in enumerate(windows(times, at)):
        if start <= at < end:
            return i, t, cover, start, end
    return None


def squeezed(times: list[str]) -> list[tuple[str, str | None, int]]:
    """기다릴 틈이 `BRIEF_ROOM_MIN` 분보다 짧은 시각 — (시각, 붙은 다음 시각 · 그날 끝이면 None, 틈 분)."""
    out = []
    for i, (t, _, start, end) in enumerate(windows(times, tm.utc_now())):
        room = int((end - start).total_seconds() // 60)
        if room < C.BRIEF_ROOM_MIN:
            near = times[i + 1] if i + 1 < len(times) and on_day(times[i + 1], start) == end else None
            out.append((t, near, max(room, 0)))
    return out


def first_tight(times: list[str], added: frozenset[str] | set[str] = frozenset()) -> tuple[str, str | None, int] | None:
    """기다릴 틈이 모자란 첫 시각 — (짚을 시각, 붙은 다른 시각 · 그날 끝이면 None, 틈 분). 붙은 두 시각 가운데 새로 더하신 쪽(`added`)을
    짚는다. 틈이 다 넉넉하면 None."""
    for t, near, room in squeezed(times):
        if near:
            who, other = (near, t) if near in added and t not in added else (t, near)
            return who, other, room
        return t, None, room
    return None


def latest_start() -> str:
    """보고 시각을 둘 수 있는 가장 늦은 「HH:MM」 — 그날이 끝나기 전에 `BRIEF_ROOM_MIN` 분이 남는 때."""
    return (datetime(2000, 1, 2) - timedelta(minutes=C.BRIEF_ROOM_MIN)).strftime("%H:%M")
