"""스캔 파일의 자리와 쓰는 법 — 사용자 폴더 · 시각 · 한 번에 바꾸는 쓰기 · 덧붙이는 기록 · 한 판만 도는 잠금.

부르는 꼴::

    import scan_store as st
    folder = st.scan_dir()                    # 사용자 폴더의 mailbox-scan — 없으면 만든다(쓰는 쪽만)
    st.write_json(folder / "state.json", d)   # 새 파일에 다 쓴 뒤 바꿔 끼운다 — 읽는 쪽은 반쯤 써진 판을 못 본다
    st.append(folder / "events.jsonl", rows)  # 덧붙이기만 — 끝 줄이 반쯤 써졌어도 읽는 쪽(read_jsonl)이 견딘다
    rows, bad = st.read_jsonl(path)           # 못 읽은 줄은 건너뛰고 그 수를 낸다
    lock = st.Lock.take(folder, now)          # 도는 판이 있으면 None — 오래된 잠금은 풀고 쥔다

시각 — 저장은 UTC ISO 8601, 보이기는 서울(+09:00 고정 — `zoneinfo` 는 윈도에서 `tzdata` 가 따로 들어 안 쓴다).
"""

from __future__ import annotations

import json
import os
import pathlib
import secrets
import time
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from typing import Any

from scan_const import (FORMAT, HOME_ENV, HOME_NAME, LOCK_FILE, LOCK_STALE_S, MAIL_DATE, MAIL_DATE_MINUTE, REPLACE_TRIES, REPLACE_WAIT_S, SCAN_DIR,
                        SEOUL_OFFSET_H, STATE_FILE)

KST = timezone(timedelta(hours=SEOUL_OFFSET_H), "KST")


# ── 시각 ─────────────────────────────────────────────────────────────────────

def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(t: datetime) -> str:
    """저장할 글자 — UTC ISO 8601. 사전순이 시간순이다."""
    if t.tzinfo is None:
        raise ValueError("시간대 없는 시각은 받지 않는다")
    return t.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse(text: str | None) -> datetime | None:
    """저장된 글자 · 시간대가 붙은 ISO 글자(정리 스킬의 기록)를 시각으로. 못 읽거나 시간대가 없으면 None."""
    if not text:
        return None
    try:
        t = datetime.fromisoformat(str(text))
    except ValueError:
        return None
    return t if t.tzinfo is not None else None


def mail_time(date: str | None) -> datetime | None:
    """메일의 때(서울 글자) → 시각. 그 꼴이 아니면 None — 때를 모르는 메일이다."""
    if not date:
        return None
    for form in (MAIL_DATE, MAIL_DATE_MINUTE):   # 옛 state.json 에 든 분까지인 글자도 푼다
        try:
            return datetime.strptime(date, form).replace(tzinfo=KST)
        except ValueError:
            continue
    return None


def seoul(t: datetime | None, form: str = "%Y-%m-%d %H:%M") -> str:
    return t.astimezone(KST).strftime(form) if t else ""


# ── 자리 ─────────────────────────────────────────────────────────────────────

def home() -> pathlib.Path:
    """사용자 폴더 — `MAIL_SECRETARY_HOME` 이 있으면 그 자리, 없으면 `%LOCALAPPDATA%\\mail-secretary`(이름의 원본과 사본은 scan_const 「자리」)."""
    override = os.environ.get(HOME_ENV, "").strip()
    if override:
        return pathlib.Path(override)
    local = os.environ.get("LOCALAPPDATA", "").strip()
    return (pathlib.Path(local) if local else pathlib.Path.home() / "AppData" / "Local") / HOME_NAME


def scan_dir(make: bool = False) -> pathlib.Path:
    folder = home() / SCAN_DIR
    if make:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


# ── 쓰기 ─────────────────────────────────────────────────────────────────────

class SwapFailed(OSError):
    """새 판을 다 썼는데 바꿔 끼우지 못했다 — 읽는 쪽이 오래 쥐고 있다. 옛 판은 그대로다."""


def write_json(path: pathlib.Path, data: Any) -> None:
    """새 파일에 다 쓰고 디스크에 내린 뒤 한 번에 바꿔 끼운다. 윈도에서 읽는 쪽이 그 파일을 쥐고 있으면 잠깐 기다려 다시 한다 —
    끝내 못 하면 `SwapFailed` 이고 옛 판이 그대로 남는다(반쯤 써진 판은 어디에도 안 선다)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".new")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    for attempt in range(REPLACE_TRIES):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt == REPLACE_TRIES - 1:
                raise SwapFailed(f"{path.name} 를 바꿔 끼우지 못했다 — 다른 손이 쥐고 있다") from None
            time.sleep(REPLACE_WAIT_S)


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
    """덧붙인 기록 전부(옛것부터)와 못 읽은 줄의 수 — 반쯤 써진 끝 줄 · 깨진 줄은 건너뛴다. 파일이 없으면 빈 것."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
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
    temp = path.with_name(path.name + ".new")
    with temp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    for attempt in range(REPLACE_TRIES):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt == REPLACE_TRIES - 1:
                raise SwapFailed(f"{path.name} 를 바꿔 끼우지 못했다") from None
            time.sleep(REPLACE_WAIT_S)


def load_state(folder: pathlib.Path) -> tuple[dict[str, Any] | None, str]:
    """지금 모습 한 장 — (판, 못 읽은 까닭). 파일이 없으면 (None, ""), 못 읽거나 꼴 번호가 다르면 (None, 까닭)."""
    path = folder / STATE_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, ""
    except (OSError, ValueError) as exc:
        return None, f"{STATE_FILE} 를 못 읽었다({type(exc).__name__})"
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        return None, f"{STATE_FILE} 의 꼴 번호가 이 스크립트({FORMAT})와 다르다"
    return data, ""


# ── 한 판만 돈다 ────────────────────────────────────────────────────────────────

class Lock:
    """도는 판 하나의 잠금(O_EXCL) — `LOCK_STALE_S` 보다 오래된 잠금은 푼다. 풀린 판은 쓰기 전에 `owns` 로 제 열쇠를 다시 보고 물러난다.
    그 시한이 왜 맞나는 `references/DESIGN.md` 「잠금」."""

    def __init__(self, path: pathlib.Path, token: str, started: datetime):
        self.path, self.token, self.started = path, token, started

    @classmethod
    def holder(cls, folder: pathlib.Path) -> dict[str, Any] | None:
        try:
            got = json.loads((folder / LOCK_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return got if isinstance(got, dict) else None

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
                held = cls.holder(folder)
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
        return None, cls.holder(folder)

    def owns(self) -> bool:
        held = self.holder(self.path.parent)
        return bool(held) and held.get("token") == self.token

    def release(self) -> None:
        if self.owns():
            try:
                self.path.unlink()
            except OSError:
                pass
