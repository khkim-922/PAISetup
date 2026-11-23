"""창이 보이는 지금 모습 — 사용자 폴더의 보고 시각표 · 그날 장부(사람 없는 실행 `unattended/` 의 파일)와 보고 맞춤 파일에서 짓고(`state_of`),
열린 보고 창에 적는다(`sync` — 저장 열쇠 `brief_const.STATE_KEY`). 사용자 폴더의 파일은 읽기만 한다. 창은 그 칸으로 「보고 맞추기」를 다시
그리고, 그보다 앞서 고른 것을 낡았다고 안다.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
import clock as T  # noqa: E402
import edge as E  # noqa: E402
import prefs_file as P  # noqa: E402
import store as S  # noqa: E402
from brief_const import CLOCK_AT, DAY_FILE, HHMM, SCHEDULE_FILE, STATE_KEY  # noqa: E402
from brief_inline import plain  # noqa: E402

UNREAD: dict[tuple[str, str], str] = {}          # 이 판에서 못 읽은 파일 — 보이는 쪽이 「없습니다」 대신 그렇다고 말한다(`state_of` 의 unread)


def read_json(folder: pathlib.Path | None, where: tuple[str, str]) -> dict:
    """사용자 폴더의 JSON 한 장 — 없으면 빈 것, 있는데 못 읽으면 빈 것에 더해 `UNREAD` 에 그 이름을 남긴다(보이기만 하는 자리 — 쓰지 않는다)."""
    if not folder:
        return {}
    try:
        return S.read_json(folder / pathlib.Path(*where)) or {}
    except S.Unreadable:
        UNREAD[where] = where[-1]
        return {}


def schedule_of(folder: pathlib.Path | None) -> tuple[list[str] | None, str]:
    """사용자 폴더의 보고 시각표에서 (걸린 보고 시각표, 건 때) — 안 걸렸거나 못 읽으면 (None, "")."""
    return schedule_from(read_json(folder, SCHEDULE))


def schedule_from(data: dict) -> tuple[list[str] | None, str]:
    """읽은 보고 시각표 → (걸린 보고 시각표, 건 때) — 시각이 없으면 (None, …). 시각 하나를 쓰던 꼴(`at`)도 읽는다. 옛 파일의 `login` 칸은
    안 읽는다 — 보고 시각이 걸린 것이 곧 그 시각의 스스로 로그인이다."""
    raw = (data.get("times") or [data.get("at")])
    times = sorted({t for t in raw if isinstance(t, str) and HHMM.fullmatch(t)})
    return (times or None), str(data.get("set") or "")


SYNCED = "열린 보고 창에 지금 모습을 알렸다"   # 대화의 시계 명령이 이 말을 줄 끝에 붙인다(사람 없는 실행 `window_link.py` 의 tell_window)
LINK = re.compile(r"\s*\[[^\]\n]*\]\(mail:[^)\s]*\)")
SCHEDULE, DAY = (SCHEDULE_FILE,), (DAY_FILE,)   # 사용자 폴더 안의 자리 — `read_json` 이 받는 꼴
UNREAD_WORDS = {SCHEDULE_FILE: "보고 시각표", DAY_FILE: "그날 장부", P.FILE_NAME: "보고 맞춤 파일"}


def state_of(folder: pathlib.Path | None) -> dict:
    """창이 보이는 지금 모습 — 사용자 폴더의 두 파일(보고 시각표 · 보고 맞춤 파일)에서 끌어낸다. 규칙의 수(`room` · `wait`)는 시각표를 건
    시계가 그 파일에 함께 적은 것이다(원본은 `unattended/unattended_const`) — 창은 그 수로 더하실 시각을 바로 재고, 수가 없으면 비서가
    받을 때 잰다. `signed` 는 시계가 세션 없이 스스로 로그인해 띄운 보고의 범위다 — 그 안에서 지은 창의 머리에 한 줄이
    선다(`render.signed_note`). 줄의 글은 링크를 걷은 맨글자이고 메일 번호는 따로 든다 — 창의 스크립트가 글자로만 세우고 링크는 번호에서만
    짓는다."""
    UNREAD.clear()
    data = read_json(folder, SCHEDULE)
    times, set_at = schedule_from(data)
    prefs = P.read(folder) if folder else P.Prefs()

    away = data.get("away") if isinstance(data.get("away"), dict) else {}
    return {"times": times or [], "set": set_at, "room": minutes(data, "room_min"), "wait": minutes(data, "wait_min"),
            "signed": signed_from(data),
            "away": {"on": away.get("on") is True, "address": str(away.get("address") or "") if away.get("on") is True else "",
                     "chosen": str(away.get("chosen") or "")},
            "seen": str(read_json(folder, DAY).get(CLOCK_AT) or ""),
            "quiet": [pref_row(x) for x in prefs.quiet], "later": [pref_row(x) for x in prefs.later],
            "unread": [UNREAD_WORDS.get(n, n) for n in sorted(set(UNREAD.values()))] + ([UNREAD_WORDS[P.FILE_NAME]] if prefs.unread else []),
            "at": T.stamp(T.local_now())}


def signed_from(data: dict) -> dict | None:
    """시각표 파일에 시계가 남긴 스스로 로그인한 보고의 범위 — {at 로그인한 때, until 그 보고가 글을 남길 수 있는 끝}(원본은 사람 없는 실행 `unattended/` 의
    `brief_schedule.note_signed`). 둘 다 시간대를 단 ISO 꼴일 때만 낸다 — 없거나 꼴이 아니면 None(그 한 줄이 안 설 뿐이다)."""
    got = data.get("signed")
    if not isinstance(got, dict):
        return None
    try:
        aware = all(dt.datetime.fromisoformat(got[k]).tzinfo is not None for k in ("at", "until"))
    except (KeyError, TypeError, ValueError):
        return None
    return {"at": got["at"], "until": got["until"]} if aware else None


def minutes(data: dict, name: str) -> int | None:
    """시각표에 적힌 규칙의 수(분) — 하루 안의 양의 정수가 아니면 None."""
    value = data.get(name)
    return value if isinstance(value, int) and 0 < value < 24 * 60 else None


def pref_row(line: str) -> dict:
    """맞춤 파일의 줄 하나 → 창이 세울 칸 — 열쇠 · 메일 번호 · 링크를 걷은 맨글자 · 돌아오는 날."""
    return {"key": P.key(line), "unid": P.unid_of(line) or "", "words": plain(LINK.sub("", line[2:])).strip(),
            "due": (P.due_of(line).isoformat() if P.due_of(line) else "")}


def row(folder: pathlib.Path) -> list[str]:
    """열린 창에 적을 지금 모습의 칸 하나 — (저장 열쇠, 지금 모습의 JSON)."""
    return [STATE_KEY, json.dumps(state_of(folder), ensure_ascii=False)]


def sync(folder: pathlib.Path) -> str:
    """열린 보고 창에 지금 모습을 적는다 — 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다(탭을 안 연다). 내는 것 — 한 줄(못 했으면 "")."""
    return SYNCED if E.tell_open(lambda: [row(folder)]) else ""
