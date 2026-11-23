"""그날 장부 파일 — 사용자 폴더의 `daily-brief-day.json` 을 읽고 쓰는 유일한 자리. 그 파일은 그날 장부(날 · 칸들 · 그날의 스스로 로그인)에
시계의 마지막 판 때(`clock_at`)를 얹은 한 장이다. 옮겨 온 셈(`brief_day` · `brief_told` · `brief_status` · `away_mail`)은 장부를 판의
상태 `{"brief": 그날 장부}` 로 받아 읽고 고친다 — 그 꼴을 여기서 지어 주고 거둔다.

    book = load(folder)              # 판의 상태 — 없으면 빈 장부 · 글이 깨졌으면 빈 장부 · 그 순간 못 읽으면 `st.Unreadable`
    book = load_or_none(folder)      # 보이기만 하는 쪽 — 못 읽으면 None
    save(folder, book, at)           # 장부와 이 판의 때를 바꿔 끼워 쓴다 — 못 쓰면 OSError
    at = clock_at(folder)            # 시계의 마지막 판 때(글자) — 없거나 못 읽으면 ""
"""

from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Any

import clock as tm
import unattended_const as C
import unattended_store as st

DAY = C.LEGACY_DAY_KEY                        # 판의 상태 안의 그날 장부 칸 — 옮겨 온 셈이 이 이름으로 읽는다


def path_of(folder: pathlib.Path) -> pathlib.Path:
    """그날 장부 파일의 자리."""
    return folder / C.DAY_FILE


def load(folder: pathlib.Path) -> dict[str, Any]:
    """판의 상태 `{"brief": 그날 장부}` — 파일이 없거나 글이 깨졌으면 빈 상태(그날 장부는 다음 판이 새로 연다). 그 순간 못 읽었으면
    `st.Unreadable` — 빈 것으로 읽어 쓰면 그날 띄운 칸을 잃어 같은 시각을 다시 띄운다."""
    try:
        data = st.read_json(path_of(folder))
    except st.Unreadable as exc:
        if not exc.broken:
            raise
        data = None
    if not data:
        return {}
    day = {k: v for k, v in data.items() if k != C.CLOCK_AT}
    return {DAY: day} if day else {}


def load_or_none(folder: pathlib.Path) -> dict[str, Any] | None:
    """보이기만 하는 쪽의 판의 상태 — 그 순간 못 읽었으면 None(그날 장부 없이 서는 말이 쓴다)."""
    try:
        return load(folder)
    except st.Unreadable:
        return None


def save(folder: pathlib.Path, book: dict[str, Any], at: datetime) -> None:
    """판의 상태의 그날 장부와 이 판의 때를 한 장으로 바꿔 끼워 쓴다. 못 쓰면 OSError."""
    st.write_json(path_of(folder), {**(book.get(DAY) or {}), C.CLOCK_AT: tm.utc_stamp(at)})


def clock_at(folder: pathlib.Path) -> str:
    """시계의 마지막 판 때 — 없거나 못 읽으면 ""."""
    try:
        return str((st.read_json(path_of(folder)) or {}).get(C.CLOCK_AT) or "")
    except st.Unreadable:
        return ""
