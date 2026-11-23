"""사내 세션 파일의 자리 — 회사 메일 손이 쓰는 세션 파일이 어디 있나를 댄다. 판이 「끊긴 뒤 세션 파일이 새로 쓰였나」로 다시 두드릴 때를
가르는 데 쓴다. 남의 코드를 안 싣고 형제 스킬 ep-login 의 데이터 파일(`places.json`) 하나만 읽는다.

    path = session_file(hand)           # 손이 쓰는 세션 파일의 자리 — 모르면 None
"""

from __future__ import annotations

import json
import os
import pathlib

import scan_const as C


def session_file(hand: pathlib.Path) -> pathlib.Path | None:
    """손이 쓰는 세션 파일의 자리 — `MAILBOX_COOKIES`, 없으면 형제 스킬 ep-login 의 받는 손 곁 `places.json` 의 기본 자리. 모르면
    None."""
    raw = os.environ.get(C.SESSION_FILE_ENV, "").strip()
    if not raw:
        js = os.environ.get(C.SESSION_HAND_ENV, "").strip()
        script = pathlib.Path(js) if js else hand.parents[2] / C.SESSION_SKILL / pathlib.Path(*C.SESSION_HAND_SCRIPT)
        try:
            raw = json.loads(script.with_name(C.SESSION_PLACES).read_text(encoding="utf-8")).get(C.SESSION_PLACES_KEY) or ""
        except (OSError, ValueError, AttributeError):
            return None
        if not raw:
            return None
    return pathlib.Path(os.path.expanduser(raw))
