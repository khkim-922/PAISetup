"""일일 보고 손들이 때를 짓는 한 자리 — 서울 벽시계 · 이 PC 의 시각 · 이 PC 의 벽시계 · 기록에 남기는 때의 꼴 · 사람이 읽는 때의 꼴.

카드 · 넣은 누름의 기록은 서울 벽시계(일정 손의 꼴 — `seoul_now`), 맡긴 일의 기록 · 창의 지금 모습은 시간대를 단 이 PC 의 시각(`local_now`),
보고 글 · 창 파일의 이름과 맞춤 파일의 날은 시간대 없는 이 PC 의 벽시계(`wall_now`)다 — 셋은 다른 사실이라 함수도 셋이다. 사람 없는 실행
(`unattended/`)의 장부 · 시각표는 UTC ISO 8601 로 남기고(`utc_now` · `utc_stamp` — 사전순이 시간순이다) 서울 글자로 보인다(`seoul`).
"""

from __future__ import annotations

import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_const.py — `-I` 로 돌아도 싣는다
from brief_const import SEOUL  # noqa: E402,F401 — 사람 없는 실행이 이 이름으로 싣는다


def seoul_now() -> dt.datetime:
    """지금 — 서울 벽시계."""
    return dt.datetime.now(SEOUL)


def local_now() -> dt.datetime:
    """지금 — 이 PC 의 시각(시간대를 단다)."""
    return dt.datetime.now().astimezone()


def wall_now() -> dt.datetime:
    """지금 — 이 PC 의 벽시계(시간대 없이). 보고 글 · 창 파일의 이름이 이 시각으로 선다."""
    return dt.datetime.now()


def stamp(at: dt.datetime) -> str:
    """기록에 남기는 때 — 초까지의 ISO 꼴."""
    return at.isoformat(timespec="seconds")


def day_words(at: dt.datetime) -> str:
    """사람이 읽는 날 — 「M/D」."""
    return f"{at.month}/{at.day}"


def moment_words(at: dt.datetime) -> str:
    """사람이 읽는 때 — 「M/D HH:MM」."""
    return f"{at.month}/{at.day} {at:%H:%M}"


def utc_now() -> dt.datetime:
    """지금 — UTC."""
    return dt.datetime.now(dt.timezone.utc)


def utc_stamp(at: dt.datetime) -> str:
    """사람 없는 실행이 남기는 때 — UTC ISO 8601(초까지). 시간대 없는 시각은 받지 않는다(`ValueError`)."""
    if at.tzinfo is None:
        raise ValueError("시간대 없는 시각은 받지 않는다")
    return at.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def parse(text: str | None) -> dt.datetime | None:
    """남긴 때(시간대가 붙은 ISO 글자)를 시각으로 — 못 읽거나 시간대가 없으면 None."""
    if not text:
        return None
    try:
        at = dt.datetime.fromisoformat(str(text))
    except ValueError:
        return None
    return at if at.tzinfo is not None else None


def parse_chosen(text: str) -> dt.datetime | None:
    """보고 창이 낸 고른 때(끝의 「Z」는 UTC)를 시각으로 — 못 읽으면 None."""
    return parse(text.replace("Z", "+00:00"))


def seoul(at: dt.datetime | None, form: str = "%Y-%m-%d %H:%M") -> str:
    """시각을 서울 글자로 — 없으면 빈 글."""
    return at.astimezone(SEOUL).strftime(form) if at else ""
