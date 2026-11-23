"""스캔 파일의 자리와 쓰는 법 — 사용자 폴더 · 시각 · 한 번에 바꾸는 쓰기 · 덧붙이는 기록 · 한 판만 도는 잠금.

부르는 꼴::

    import scan_store as st
    folder = st.scan_dir()                    # 사용자 폴더의 mailbox-scan — 없으면 만든다(쓰는 쪽만)
    st.write_json(folder / "state.json", d)   # 새 파일에 다 쓴 뒤 바꿔 끼운다 — 읽는 쪽은 반쯤 써진 판을 못 본다
    d = st.read_json(path)                    # 없으면 None · 읽었으면 dict · 있는데 못 읽었으면 `Unreadable` — 셋은 다른 답이다
    st.append(folder / "events.jsonl", rows)  # 덧붙이기만 — 끝 줄이 반쯤 써졌어도 읽는 쪽(read_jsonl)이 견딘다
    rows, bad = st.read_jsonl(path)           # 못 읽은 줄은 건너뛰고 그 수를 낸다
    lock = st.Lock.take(folder, now)          # 도는 판이 있으면 None — 오래된 잠금은 풀고 쥔다
    lock, held, at, waited = st.Lock.wait(folder, seconds)   # 도는 판이 있으면 그 잠금이 풀리기를 seconds 초 안에서 기다렸다 쥔다

시각은 `scan_time` 이 든다.
"""

from __future__ import annotations

import json
import os
import pathlib
import secrets
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from scan_const import (FORMAT, HOME_ENV, HOME_NAME, LOCK_FILE, LOCK_STALE_S, LOCK_WAIT_POLL_S, REPLACE_TRIES, REPLACE_WAIT_S, SCAN_DIR,
                        STATE_FILE)
from scan_time import now, parse, stamp

# ── 자리 ─────────────────────────────────────────────────────────────────────

def home() -> pathlib.Path:
    """사용자 폴더 — `MAIL_SECRETARY_HOME` 이 있으면 그 자리, 없으면 `%LOCALAPPDATA%\\mail-secretary`(이름의 원본과 사본은 scan_const 「자리」)."""
    override = os.environ.get(HOME_ENV, "").strip()
    if override:
        return pathlib.Path(override)
    local = os.environ.get("LOCALAPPDATA", "").strip()
    return (pathlib.Path(local) if local else pathlib.Path.home() / "AppData" / "Local") / HOME_NAME


def scan_dir(make: bool = False) -> pathlib.Path:
    """사용자 폴더 안의 스캔 자리 — `make` 면 없을 때 만든다."""
    folder = home() / SCAN_DIR
    if make:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


# ── 쓰기 ─────────────────────────────────────────────────────────────────────

class SwapFailed(OSError):
    """새 판을 다 썼는데 바꿔 끼우지 못했다 — 읽는 쪽이 오래 쥐고 있다. 옛 판은 그대로다."""


class Unreadable(OSError):
    """파일은 있는데 못 읽었다 — 「없다」가 아니다. 이것을 빈 것으로 읽어 그 위에 쓰면 그 파일의 다른 칸이 사라진다.
    `broken` 이 참이면 글이 JSON 한 장(객체)이 아니다(기다려도 안 바뀐다), 거짓이면 다른 손이 쥐었거나 막혀 기다려 다시 읽어도 안 됐다."""

    def __init__(self, path: pathlib.Path, why: str, broken: bool):
        super().__init__(f"{path.name} 를 못 읽었다({why})")
        self.path, self.broken = path, broken


def _swap(temp: pathlib.Path, path: pathlib.Path) -> None:
    """다 쓴 새 파일을 제자리에 바꿔 끼운다. 윈도에서 읽는 쪽이 그 파일을 쥐고 있으면 잠깐 기다려 다시 한다 — 끝내 못 하면 새 파일을 걷고
    `SwapFailed`(옛 판이 그대로다)."""
    for attempt in range(REPLACE_TRIES):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt == REPLACE_TRIES - 1:
                temp.unlink(missing_ok=True)
                raise SwapFailed(f"{path.name} 를 바꿔 끼우지 못했다 — 다른 손이 쥐고 있다") from None
            time.sleep(REPLACE_WAIT_S)


def _temp_of(path: pathlib.Path) -> pathlib.Path:
    """쓰는 쪽마다 따로인 새 파일 — 두 프로세스가 같은 파일을 함께 쓰면(스캔 판과 창 곁의 손) 한 이름의 새 파일을 서로 비우고 옮겨, 반쯤 써진
    판이 제자리에 서거나 한쪽이 FileNotFoundError 로 진다."""
    return path.with_name(f"{path.name}.{os.getpid()}-{secrets.token_hex(4)}.new")


def write_json(path: pathlib.Path, data: Any) -> None:
    """새 파일에 다 쓰고 디스크에 내린 뒤 한 번에 바꿔 끼운다(`_swap`) — 반쯤 써진 판은 어디에도 안 선다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = _temp_of(path)
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    _swap(temp, path)


def _read_bytes(path: pathlib.Path) -> bytes:
    """파일 그대로 — 없으면 FileNotFoundError, 있는데 못 읽으면 `Unreadable`. ⚠ 윈도에서는 다른 프로세스가 그 파일을 새 판으로 바꿔 끼우는
    그 순간 읽기가 PermissionError 로 진다 — 쓰는 쪽(`_swap`)이 기다리는 것과 같은 수만큼 기다려 다시 읽는다."""
    for attempt in range(REPLACE_TRIES):
        try:
            return path.read_bytes()
        except FileNotFoundError:
            raise
        except PermissionError as exc:
            if attempt == REPLACE_TRIES - 1:
                raise Unreadable(path, type(exc).__name__, broken=False) from None
            time.sleep(REPLACE_WAIT_S)
        except OSError as exc:
            raise Unreadable(path, type(exc).__name__, broken=False) from None
    raise AssertionError("닿지 않는다")


def read_json(path: pathlib.Path) -> dict[str, Any] | None:
    """스캔 자리의 JSON 파일 한 장 — 답은 셋이다: 없으면 None · 읽었으면 그 dict · 있는데 못 읽었으면 `Unreadable`. 꼴 번호는 부르는 쪽이
    본다. 한 칸만 바꿔 쓰는 쪽은 이것으로 읽고, `Unreadable` 이면 쓰지 않는다."""
    try:
        raw = _read_bytes(path)
    except FileNotFoundError:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except ValueError as exc:                 # UnicodeDecodeError 도 ValueError 다
        raise Unreadable(path, type(exc).__name__, broken=True) from None
    if not isinstance(data, dict):
        raise Unreadable(path, "JSON 객체가 아니다", broken=True)
    return data


def append(path: pathlib.Path, rows: Iterable[dict[str, Any]]) -> int:
    """줄을 덧붙인다 — 있는 줄은 안 고친다. 한 번에 써 내리고 디스크에 내린다. 덧붙인 수를 낸다."""
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    if not text:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    return text.count("\n")


def read_jsonl(path: pathlib.Path) -> tuple[list[dict[str, Any]], int]:
    """덧붙인 기록 전부(옛것부터)와 못 읽은 줄의 수 — 반쯤 써진 끝 줄 · 깨진 줄은 건너뛴다. 파일이 없으면 빈 것, 있는데 못 읽으면 `Unreadable`."""
    try:
        raw = _read_bytes(path).decode("utf-8", errors="replace")
    except FileNotFoundError:
        return [], 0
    rows, bad = [], 0
    for line in raw.splitlines():
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


def rewrite_jsonl(path: pathlib.Path, rows: Iterable[dict[str, Any]]) -> None:
    """기록을 새로 쓴다(오래된 줄을 접을 때) — 새 파일에 다 쓴 뒤 바꿔 끼운다."""
    temp = _temp_of(path)
    with temp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    _swap(temp, path)


def load_state(folder: pathlib.Path) -> tuple[dict[str, Any] | None, str]:
    """지금 모습 한 장 — (판, 깨진 까닭). 파일이 없으면 (None, ""), 글이 깨졌거나 꼴 번호가 다르면 (None, 까닭) — 메일함에서 다시 지어도 되는 판.
    있는데 못 읽었으면(다른 손이 쥐었다) `Unreadable` 이 그대로 나간다 — 그 판을 깨진 것으로 읽어 다시 지으면 그날 띄운 보고 · 보낸 메일의 기록이
    사라져 두 번 띄우고 두 번 보낸다."""
    path = folder / STATE_FILE
    try:
        data = read_json(path)
    except Unreadable as exc:
        if not exc.broken:
            raise
        return None, str(exc)
    if data is None:
        return None, ""
    if data.get("format") != FORMAT:
        return None, f"{STATE_FILE} 의 꼴 번호가 이 스크립트({FORMAT})와 다르다"
    return data, ""


# ── 한 판만 돈다 ────────────────────────────────────────────────────────────────

def held_since(path: pathlib.Path) -> dict[str, Any] | None:
    """잠금 파일 하나(`{started, …}`) — 없으면 None. 있는데 못 읽으면 `{"started": 그 파일의 고친 때}` 로 낸다(그 때로 낡음을 잰다). 고친 때도
    못 보면 지금으로 낸다 — 그 잠금을 도는 판의 것으로 둔다."""
    try:
        return read_json(path)
    except Unreadable:
        try:
            at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        except FileNotFoundError:
            return None
        except OSError:
            at = now()
        return {"started": stamp(at), "unread": True}


class Lock:
    """도는 판 하나의 잠금(O_EXCL) — `LOCK_STALE_S` 보다 오래된 잠금은 푼다. 풀린 판은 쓰기 전에 `owns` 로 제 열쇠를 다시 보고 물러난다.
    그 시한이 왜 맞나는 `references/DESIGN.md` 「잠금」."""

    def __init__(self, path: pathlib.Path, token: str, started: datetime):
        self.path, self.token, self.started = path, token, started

    @classmethod
    def take(cls, folder: pathlib.Path, at: datetime) -> tuple[Lock | None, dict[str, Any] | None]:
        """쥔다 — (잠금, 풀어 준 옛 잠금). 도는 판이 있으면 (None, 그 판의 잠금)."""
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / LOCK_FILE
        token = secrets.token_hex(8)
        cleared = None
        for _ in range(2):
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                held = held_since(folder / LOCK_FILE)
                since = parse((held or {}).get("started"))
                if since is not None and (at - since).total_seconds() < LOCK_STALE_S:
                    return None, held
                cleared = held or {}
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                except PermissionError:
                    return None, held
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"token": token, "started": stamp(at), "pid": os.getpid()}, f)
            return cls(path, token, at), cleared
        return None, held_since(folder / LOCK_FILE)

    @classmethod
    def wait(cls, folder: pathlib.Path, seconds: float) -> tuple[Lock | None, dict[str, Any] | None, datetime, float]:
        """도는 판이 있으면 `seconds` 초 안에서 그 잠금이 풀리기를 기다렸다 쥔다 — 사이(`LOCK_WAIT_POLL_S`)마다 잠들었다 `take` 로 다시 쥐어
        본다. 쥐어 볼 때마다 그 때로 쥐어(잠금의 시작 때가 기다린 뒤의 때다) 낡음의 규칙이 `take` 그대로다. 0 초면 한 번만 쥐어 본다.
        내는 것 — (잠금 · 못 쥐었으면 None, `take` 의 둘째 값, 마지막으로 쥐어 본 때, 기다린 초)."""
        began = time.monotonic()
        while True:
            at = now()
            lock, held = cls.take(folder, at)
            left = seconds - (time.monotonic() - began)
            if lock is not None or left <= 0:
                return lock, held, at, time.monotonic() - began
            time.sleep(min(LOCK_WAIT_POLL_S, left))

    def owns(self) -> bool:
        """이 판이 아직 잠금을 쥐었나 — 잠금 파일의 열쇠가 제 열쇠인가."""
        held = held_since(self.path)
        return bool(held) and held.get("token") == self.token

    def release(self) -> None:
        """제 잠금이면 푼다."""
        if self.owns():
            try:
                self.path.unlink()
            except OSError:
                pass
