"""창이 보이는 지금 모습 — 사용자 폴더의 보고 시각표 · 스캔의 지금 모습(형제 스킬 mailbox-scan 의 파일)과 보고 맞춤 파일에서 짓고(`state_of`),
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
import edge as E  # noqa: E402
import prefs_file as P  # noqa: E402
import store as S  # noqa: E402
from brief_const import HHMM, SCAN_BRIEF, SCAN_STATE, STATE_KEY  # noqa: E402
from brief_text import plain  # noqa: E402

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


def schedule_of(folder: pathlib.Path | None) -> tuple[list[str] | None, bool, str]:
    """(걸린 보고 시각표, 스스로 로그인, 건 때) — 안 걸렸거나 못 읽으면 (None, False, ""). 시각 하나를 쓰던 꼴(`at`)도 읽는다."""
    data = read_json(folder, SCAN_BRIEF)
    raw = (data.get("times") or [data.get("at")])
    times = sorted({t for t in raw if isinstance(t, str) and HHMM.fullmatch(t)})
    return (times or None), bool(data.get("login")), str(data.get("set") or "")


LINK = re.compile(r"\s*\[[^\]\n]*\]\(mail:[^)\s]*\)")
UNREAD_WORDS = {SCAN_BRIEF[-1]: "보고 시각표", SCAN_STATE[-1]: "스캔의 지금 모습", P.FILE_NAME: "보고 맞춤 파일"}


def state_of(folder: pathlib.Path | None) -> dict:
    """창이 보이는 지금 모습 — 사용자 폴더의 두 파일(보고 시각표 · 보고 맞춤 파일)에서 끌어낸다. 규칙의 수(`room` · `wait`)는 시각표를 건
    스캔이 그 파일에 함께 적은 것이다(원본은 스킬 mailbox-scan 의 `scan_const`) — 창은 그 수로 더하실 시각을 바로 재고, 수가 없으면 비서가
    받을 때 잰다. 줄의 글은 링크를 걷은 맨글자이고 메일 번호는 따로 든다 — 창의 스크립트가 글자로만 세우고 링크는 번호에서만 짓는다."""
    UNREAD.clear()
    times, login, set_at = schedule_of(folder)
    data = read_json(folder, SCAN_BRIEF)
    prefs = P.read(folder) if folder else P.Prefs()

    def number(name: str) -> int | None:
        value = data.get(name)
        return value if isinstance(value, int) and 0 < value < 24 * 60 else None

    def row(line: str) -> dict:
        return {"key": P.key(line), "unid": P.unid_of(line) or "", "words": plain(LINK.sub("", line[2:])).strip(),
                "due": (P.due_of(line).isoformat() if P.due_of(line) else "")}
    away = data.get("away") if isinstance(data.get("away"), dict) else {}
    return {"times": times or [], "set": set_at, "login": login, "room": number("room_min"), "wait": number("wait_min"),
            "away": {"on": away.get("on") is True, "address": str(away.get("address") or "") if away.get("on") is True else "",
                     "chosen": str(away.get("chosen") or "")},
            "seen": str((read_json(folder, SCAN_STATE).get("last_run") or {}).get("started") or ""),
            "quiet": [row(x) for x in prefs.quiet], "later": [row(x) for x in prefs.later],
            "unread": [UNREAD_WORDS.get(n, n) for n in sorted(set(UNREAD.values()))] + ([UNREAD_WORDS[P.FILE_NAME]] if prefs.unread else []),
            "at": dt.datetime.now().astimezone().isoformat(timespec="seconds")}


def row(folder: pathlib.Path) -> list[str]:
    return [STATE_KEY, json.dumps(state_of(folder), ensure_ascii=False)]


def sync(folder: pathlib.Path) -> str:
    """열린 보고 창에 지금 모습을 적는다 — 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다(탭을 안 연다). 내는 것 — 한 줄(못 했으면 "")."""
    return "열린 보고 창에 지금 모습을 알렸다" if E.tell_open(lambda: [row(folder)]) else ""
