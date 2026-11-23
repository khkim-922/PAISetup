"""보고 시각표 파일 — 사용자 폴더의 `daily-brief-schedule.json` 을 읽고, 시각표를 걸고 내리고, 칸 하나(`away` · `picked`)를 바꿔 쓰는 유일한 자리.

    setting, problem = load(folder)              # 안 걸었으면 (None, ""), 못 읽으면 (None, 까닭). 시각표는 setting["times"]
    save(folder, times=["07:30", "13:00"], claude=path) · clear(folder)
    put(folder, "away", {...})                   # 칸 하나만 바꿔 쓴다 — 못 읽으면 `st.Unreadable` · 안 걸려 있으면 False
    away = away_of(setting)                      # 걸어 둔 자리 밖에서 보기 — 안 켰으면 빈 것
    note_signed(folder, at)                      # 세션이 없다가 스스로 로그인한 때와 그 보고의 끝 — 일일 보고의 창이 읽는 `signed` 칸

칸의 뜻은 `references/DESIGN.md` 「정한 시각의 보고」가 든다.
"""

from __future__ import annotations

import pathlib
from datetime import datetime, timedelta
from typing import Any

import unattended_const as C
import unattended_store as st
import clock as tm
from brief_slots import times_given


def read_brief(folder: pathlib.Path) -> dict[str, Any] | None:
    """보고 시각표 파일 그대로 — 없으면 None, 있는데 못 읽으면 `st.Unreadable`. 한 칸만 바꿔 쓰는 쪽은 이것으로 읽어 다른 칸을 옮겨 적는다."""
    return st.read_json(folder / C.SCHEDULE_FILE)


def load(folder: pathlib.Path) -> tuple[dict[str, Any] | None, str]:
    """(설정, 못 읽은 까닭). 안 걸었으면 (None, ""). 시각 하나(꼴 1)로 걸어 둔 설정도 읽어 `times` 를 채운다. 읽기만 하는 쪽의 답이다 — 쓰는
    쪽은 `read_brief` 의 `st.Unreadable` 로 「못 읽었다」를 가른다."""
    try:
        data = read_brief(folder)
    except st.Unreadable as exc:
        return None, str(exc)
    return setting_of(data)


def setting_of(data: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str]:
    """시각표 파일 그대로(`read_brief`) → (설정, 꼴이 아닌 까닭). 없으면 (None, "")."""
    if data is None:
        return None, ""
    if data.get("format") not in C.BRIEF_FORMATS_READ or not data.get("claude"):
        return None, f"{C.SCHEDULE_FILE} 의 꼴이 이 스크립트와 다르다"
    raw = data.get("times") if data.get("format") != 1 else [data.get("at")]
    times, bad = times_given([str(x) for x in raw]) if isinstance(raw, list) and all(isinstance(x, str) for x in raw) else ([], "꼴")
    if bad:
        return None, f"{C.SCHEDULE_FILE} 의 보고 시각이 꼴이 아니다"
    data["times"] = times
    return data, ""


KEPT = ("away", "signed")                        # 시각표를 다시 걸어도 그대로 실어 두는 칸 — 자리 밖에서 보기 · 스스로 로그인한 보고의 범위


def save(folder: pathlib.Path, times: list[str], claude: pathlib.Path) -> None:
    """시각표를 건다 — 걸려 있던 자리 밖에서 보기(`away`)와 스스로 로그인한 보고의 범위(`signed`)는 그대로 실어 둔다(시각을 바꿔도 켜고
    끄기 · 지금 짓는 보고의 한 줄은 안 바뀐다). 스스로 로그인을 켜는 칸은 없다 — 시각이 걸린 것이 곧 그 시각의 로그인이라, 옛 파일의
    `login` 칸은 옮기지 않아 다시 걸면 걷힌다. 걸려 있던 파일을 못 읽으면 `st.Unreadable` 이고 안 쓴다 — 빈 것으로 읽어 쓰면 켜 둔 자리
    밖에서 보기가 꺼진다. 글이 깨진 파일은 새 시각표로 고친다(옮길 칸이 없다)."""
    try:
        held = read_brief(folder) or {}
    except st.Unreadable as exc:
        if not exc.broken:
            raise
        held = {}
    st.write_json(folder / C.SCHEDULE_FILE, {"format": C.BRIEF_FORMAT, "times": list(times), "claude": str(claude),
                                          "set": tm.utc_stamp(tm.utc_now()), "room_min": C.BRIEF_ROOM_MIN, "wait_min": C.BRIEF_WAIT_MIN,
                                          **{k: held[k] for k in KEPT if isinstance(held.get(k), dict)}})
    # ↑ 규칙의 수 둘은 보고 창이 더하실 시각을 바로 재는 데 쓴다(일일 보고의 state.py `state_of`) — 원본은 unattended_const 한 자리다


def put(folder: pathlib.Path, key: str, value: Any) -> bool:
    """걸린 시각표 파일의 칸 하나만 바꿔 쓴다 — 다른 칸은 그대로 옮겨 적는다. 그 사이 보고가 내려졌으면 안 쓰고 False(칸만 든 파일을
    세우지 않는다). 걸린 파일을 못 읽으면 `st.Unreadable` 이고 안 쓴다 — 빈 것 위에 쓰면 시각표가 사라진다."""
    current = read_brief(folder)
    if current is None:
        return False
    st.write_json(folder / C.SCHEDULE_FILE, {**current, key: value})
    return True


def note_signed(folder: pathlib.Path, at: datetime, launched: datetime | None = None) -> bool:
    """세션이 없다가 스스로 로그인한 때를 시각표 파일의 `signed` 칸에 남긴다 — {at 로그인한 때, until 그 로그인으로 띄운 보고가 글을 남길 수
    있는 끝(띄운 때 `launched` · 안 주면 로그인한 때에서 `BRIEF_LOCK_STALE_S` — 띄운 보고가 그 뒤로는 끝난 것이다)}. 일일 보고의 창이 그 사이에 지은 보고에 한 줄을 세운다. 파일을
    못 읽거나 못 쓰거나 그 사이 보고가 내려졌으면 False — 그 줄만 안 서고 띄우기는 그대로 간다."""
    try:
        return put(folder, "signed", {"at": tm.utc_stamp(at), "until": tm.utc_stamp((launched or at) + timedelta(seconds=C.BRIEF_LOCK_STALE_S))})
    except OSError:                      # 못 읽음(`st.Unreadable`) · 못 바꿔 끼움
        return False


def clear(folder: pathlib.Path) -> bool:
    """보고를 내린다 — 걸려 있었으면 True."""
    try:
        (folder / C.SCHEDULE_FILE).unlink()
        return True
    except FileNotFoundError:
        return False


def claude_present(setting: dict[str, Any]) -> bool:
    """걸어 둔 claude 가 그 자리에 있나."""
    return pathlib.Path(setting["claude"]).is_file()


def away_of(setting: dict[str, Any] | None) -> dict[str, Any]:
    """걸어 둔 자리 밖에서 보기 — {on, address, chosen, set}. 안 켰으면 빈 것."""
    away = (setting or {}).get("away")
    return away if isinstance(away, dict) else {}
