"""사용자 폴더의 기록 파일 넷 — 바꾼 것의 기록 · 잡아 둔 바꿈 · 보여 드린 안 · 적어 둔 안들을 읽고 쓴다. 메일함에는 닿지 않는다.

기록 · 안들은 덧붙이기만 하고 있는 줄을 고치지 않는다. 잡아 둔 바꿈 · 보여 드린 안은 바꿔 끼운다. 줄의 뜻은 `journal.py` 머리말이 든다.
"""

from __future__ import annotations

import json
import os
import pathlib
from collections.abc import Sequence
from typing import Any

from journal_const import (ATOMIC_SUFFIX, HELD_FILE, HELD_KEY, HOME_ENV, HOME_NAME, LOG_FILE, PLANS_FILE, SHOWN_FILE,
                           UNKNOWN)


def home() -> pathlib.Path:
    """사용자 폴더 — `MAIL_SECRETARY_HOME` 이 있으면 그 자리, 없으면 `%LOCALAPPDATA%\\mail-secretary`."""
    override = os.environ.get(HOME_ENV, "").strip()
    if override:
        return pathlib.Path(override)
    local = os.environ.get("LOCALAPPDATA", "").strip()
    return (pathlib.Path(local) if local else pathlib.Path.home() / "AppData" / "Local") / HOME_NAME


def _write_atomic(path: pathlib.Path, text: str) -> None:
    """글을 임시 파일에 쓴 뒤 그 자리에 바꿔 끼운다 — 쓰다 끊겨도 앞 판이 남는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ATOMIC_SUFFIX)
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def _lines(path: pathlib.Path, key: str) -> tuple[list[dict[str, Any]], list[int]]:
    """덧붙이기만 하는 파일의 줄 전부(옛것부터)와 못 읽은 줄의 번호 — `key` 칸이 정수인 줄만 읽은 것으로 센다."""
    if not path.exists():
        return [], []
    rows, bad = [], []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):   # 끊긴 줄의 반쪽 글자도 그 줄만 못 읽는다
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get(key), int):
                raise ValueError
            rows.append(row)
        except ValueError:
            bad.append(n)
    return rows, bad


def _append_line(path: pathlib.Path, row: dict[str, Any]) -> None:
    """한 줄을 덧붙인다 — 있는 줄은 고치지 않는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def log_path(folder: pathlib.Path) -> pathlib.Path:
    """바꾼 것의 기록 파일의 자리."""
    return folder / LOG_FILE


def entries(folder: pathlib.Path) -> tuple[list[dict[str, Any]], list[int]]:
    """기록 전부(옛것부터)와 못 읽은 줄의 번호."""
    return _lines(log_path(folder), "id")


def undone_entry(folder: pathlib.Path, undoes: int | None) -> dict[str, Any]:
    """이 바꿈이 되돌리는 기록 — 되돌리는 번호를 안 줬으면 기록을 읽지 않고 빈 것, 그 번호의 기록이 없어도 빈 것."""
    if undoes is None:
        return {}
    return next((r for r in entries(folder)[0] if r["id"] == undoes), {})


def next_id(rows: Sequence[dict[str, Any]]) -> int:
    """다음 기록 번호 — `append` 가 주는 번호와 같다."""
    return max((r["id"] for r in rows), default=0) + 1


def append(folder: pathlib.Path, entry: dict[str, Any]) -> int:
    """기록 한 줄을 다음 번호로 덧붙이고 그 번호를 낸다 — 있는 줄은 고치지 않는다."""
    rows, _ = entries(folder)
    entry = {"id": next_id(rows), **entry}
    _append_line(log_path(folder), entry)
    return entry["id"]


def held(folder: pathlib.Path) -> dict[str, Any] | None:
    """잡아 둔 바꿈 — 없거나 못 읽으면 None."""
    path = folder / HELD_FILE
    if not path.exists():
        return None
    try:
        got = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return got if isinstance(got, dict) else None


def hold_change(folder: pathlib.Path, hold: dict[str, Any]) -> None:
    """바꿈 하나를 잡아 둔다 — 앞의 잡아 둔 바꿈 자리에 바꿔 끼운다."""
    _write_atomic(folder / HELD_FILE, json.dumps(hold, ensure_ascii=False))


def release_held(folder: pathlib.Path) -> None:
    """잡아 둔 바꿈을 놓는다 — 없으면 그대로."""
    (folder / HELD_FILE).unlink(missing_ok=True)


def close_held(folder: pathlib.Path, entry: dict[str, Any]) -> int:
    """잡아 둔 바꿈을 기록 한 줄로 맺은 뒤 놓고 그 기록 번호를 낸다 — 기록을 먼저 덧붙여, 놓다 끊겨도 바꿈이 기록 밖으로 새지 않는다."""
    entry_id = append(folder, entry)
    release_held(folder)
    return entry_id


def with_held(folder: pathlib.Path, rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """기록에 잡아 둔 바꿈을 다음 번호의 「결과 모름」으로 덧붙인 것 — 보이기만 한다(맺을 때도 그 번호로 적힌다)."""
    hold = held(folder)
    if hold is None:
        return list(rows)
    return [*rows, {**hold, "id": next_id(rows), "outcome": UNKNOWN, HELD_KEY: True}]


def shown_plan(folder: pathlib.Path) -> dict[str, Any]:
    """보여 드린 안 파일 — {"plan": 안 번호, "pieces": …}. 없거나 못 읽으면 빈 것."""
    try:
        got = json.loads((folder / SHOWN_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return got if isinstance(got, dict) else {}


def pieces_of(shown: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """보여 드린 안의 조각 — 조각 번호(글자) → 조각. 없거나 꼴이 다르면 빈 것."""
    pieces = shown.get("pieces")
    return pieces if isinstance(pieces, dict) else {}


def shown_pieces(folder: pathlib.Path) -> dict[str, dict[str, Any]]:
    """보여 드린 안의 조각 — 조각 번호(글자) → 조각. 없거나 못 읽으면 빈 것."""
    return pieces_of(shown_plan(folder))


def write_shown(folder: pathlib.Path, plan: int, pieces: dict[str, dict[str, Any]]) -> None:
    """보여 드린 안을 바꿔 끼운다."""
    _write_atomic(folder / SHOWN_FILE, json.dumps({"plan": plan, "pieces": pieces}, ensure_ascii=False))


def plan_rows(folder: pathlib.Path) -> list[dict[str, Any]]:
    """적어 둔 안들의 조각 줄 전부(옛것부터) — 못 읽은 줄은 건너뛴다."""
    return _lines(folder / PLANS_FILE, "plan")[0]


def append_plan_row(folder: pathlib.Path, row: dict[str, Any]) -> None:
    """적어 둔 안들에 조각 한 줄을 덧붙인다."""
    _append_line(folder / PLANS_FILE, row)
