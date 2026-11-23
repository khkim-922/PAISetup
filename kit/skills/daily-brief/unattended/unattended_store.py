"""사람 없는 실행의 JSON 파일 한 장 — 일일 보고 바탕(`store`)의 읽기 · 바꿔 끼우기 위에 이 폴더가 기대는 꼴(못 읽은 말 · 글이 깨졌나)을 얹는
한 자리. 바꿔 끼우는 몸은 바탕에 하나다 — 여기는 그 몸을 다시 짓지 않는다.

    data = read_json(path)          # 없으면 None · 있는데 못 읽으면 `Unreadable`(`broken` — 글이 꼴이 아니다)
    write_json(path, data)          # 다 쓴 뒤 바꿔 끼운다 — 못 쓰면 OSError
    held = held_since(path)         # 띄운 기록 한 장 — 못 읽으면 그 파일의 고친 때를 띄운 때로
    rows, bad = read_jsonl(path)    # 덧붙인 줄들 — 반쯤 써진 끝 줄 · 깨진 줄은 건너뛴다
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any

import clock as tm
import store as S


class Unreadable(OSError):
    """파일은 있는데 못 읽었다 — 「없다」가 아니다. 이것을 빈 것으로 읽어 그 위에 쓰면 그 파일의 다른 칸이 사라진다.
    `broken` 이 참이면 글이 JSON 한 장(객체)이 아니다(기다려도 안 바뀐다), 거짓이면 다른 손이 쥐었거나 막혀 다시 읽어도 안 됐다."""

    def __init__(self, path: pathlib.Path, why: str, broken: bool):
        super().__init__(f"{path.name} 를 못 읽었다({why})")
        self.path, self.broken = path, broken


def read_json(path: pathlib.Path) -> dict[str, Any] | None:
    """JSON 한 장 — 없으면 None · 읽었으면 그 dict · 있는데 못 읽었으면 `Unreadable`(바탕이 가른 까닭과 깨짐을 옮겨 싣는다)."""
    try:
        return S.read_json(path)
    except S.Unreadable as exc:
        raise Unreadable(path, exc.why, exc.broken) from None


def write_json(path: pathlib.Path, data: Any) -> None:
    """JSON 한 장을 바탕의 바꿔 끼우기(`store.replace`)로 쓴다 — 자리가 없으면 만든다. 못 쓰면 OSError."""
    path.parent.mkdir(parents=True, exist_ok=True)
    S.replace(path, json.dumps(data, ensure_ascii=False).encode("utf-8"))


def held_since(path: pathlib.Path) -> dict[str, Any] | None:
    """띄운 기록 한 장(`{started, …}`) — 없으면 None. 있는데 못 읽으면 `{"started": 그 파일의 고친 때}` 로 낸다(그 때로 낡음을 잰다). 고친 때도
    못 보면 지금으로 낸다 — 그 기록을 도는 것으로 둔다."""
    try:
        return read_json(path)
    except Unreadable:
        try:
            at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        except FileNotFoundError:
            return None
        except OSError:
            at = tm.utc_now()
        return {"started": tm.utc_stamp(at), "unread": True}


def read_jsonl(path: pathlib.Path) -> tuple[list[dict[str, Any]], int]:
    """덧붙인 줄 전부(옛것부터)와 못 읽은 줄의 수 — 반쯤 써진 끝 줄 · 깨진 줄은 건너뛴다. 파일이 없으면 빈 것, 있는데 못 읽으면 `Unreadable`."""
    try:
        raw = S.read_bytes(path)
    except S.Unreadable as exc:
        raise Unreadable(path, exc.why, exc.broken) from None
    if raw is None:
        return [], 0
    rows, bad = [], 0
    for line in raw.decode("utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            bad += 1
    return rows, bad
