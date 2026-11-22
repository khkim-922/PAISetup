"""일일 보고 손들이 사용자 폴더의 파일(기록 · 맞춤 파일 · 스캔의 설정 · 누른 창의 보고 글)을 읽고 바꿔 끼우는 한 자리 — 없음 · 읽음 ·
못 읽음을 가른다.

    data = read_bytes(path)        # 없으면 None · 못 읽으면 Unreadable
    data = read_json(path)         # 없으면 None · 못 읽거나 JSON 사전이 아니면 Unreadable
    got = page_brief(folder, page) # 누른 창의 보고 글 (그 .md 의 자리, 글) — 창 이름의 꼴이 아니거나 못 읽으면 None
    replace(path, data)            # 쓰는 손마다 제 임시 파일에 다 쓴 뒤 바꿔 끼운다 — 못 쓰면 OSError

윈도에서는 쓰는 쪽이 새 파일로 바꿔 끼우는 그 순간 읽기가 PermissionError 로 진다(없음으로는 안 진다) — 잠깐 기다려 다시 읽고, 그래도 지면 못
읽음이다. 못 읽은 파일을 빈 것으로 읽고 그 위에 쓰면 거기 든 것을 잃는다 — 쓰는 손은 못 읽음에서 멈추고, 보이는 손은 못 읽었다고 말한다.
임시 파일의 이름은 쓰는 손마다 다르다 — 두 손이 한 이름을 쓰면 서로의 임시 파일을 옮겨 한쪽이 넘어진다.
"""

from __future__ import annotations

import json
import os
import pathlib
import secrets
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_text.py — `-I` 로 돌아도 싣는다
from brief_text import made_of  # noqa: E402

REPLACE_TRIES = 5                  # 바꿔 끼우는 순간의 PermissionError 를 다시 해 보는 수
REPLACE_WAIT_S = 0.05              # 그 사이 — 바꿔 끼우기는 몇 밀리초라 넉넉하다


class Unreadable(Exception):
    """파일이 있는데 못 읽었다 — 다시 해 봐도 진 OSError · 글이 꼴이 아니다."""


def read_bytes(path: pathlib.Path) -> bytes | None:
    """파일의 바이트 — 없으면 None, 있는데 못 읽으면 `Unreadable`."""
    for attempt in range(REPLACE_TRIES):
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return None
        except PermissionError as exc:
            if attempt == REPLACE_TRIES - 1:
                raise Unreadable(f"{type(exc).__name__}: {exc}") from exc
            time.sleep(REPLACE_WAIT_S)
        except OSError as exc:
            raise Unreadable(f"{type(exc).__name__}: {exc}") from exc
    return None


def read_json(path: pathlib.Path) -> dict | None:
    """JSON 사전 하나 — 없으면 None, 못 읽거나 꼴이 아니면 `Unreadable`."""
    raw = read_bytes(path)
    if raw is None:
        return None
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise Unreadable(type(exc).__name__) from exc
    if not isinstance(data, dict):
        raise Unreadable("JSON 사전이 아니다")
    return data


def page_brief(folder: pathlib.Path, page: str) -> tuple[pathlib.Path, str] | None:
    """누른 창(`page` — 그 창의 파일 이름)의 보고 글 — (같은 이름의 .md 의 자리, 글). 창을 지은 글이다 — 카드 · 맡길 일은 창이 선 뒤 안
    바뀌고, 끝의 기록 절만 거두는 손(곁의 `ticks.py`)이 고친다. 이름이 보고 창의 꼴(`brief_text.made_of`)이 아니거나 글이 없거나 못 읽으면
    None. 거두는 손이 그 글을 바꿔 끼우는 순간에 읽어도 지지 않는다(`read_bytes` 가 다시 해 본다)."""
    if not page.endswith(".html") or made_of(page) is None:
        return None
    md = (folder / page).with_suffix(".md")
    try:
        raw = read_bytes(md)
        return (md, raw.decode("utf-8")) if raw is not None else None
    except (Unreadable, UnicodeDecodeError):
        return None


def replace(path: pathlib.Path, data: bytes) -> None:
    """곁의 제 임시 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 파일이 남지 않는다. 바꿔 끼우는 순간 남이 읽고 있으면(PermissionError) 잠깐 기다려
    다시 해 본다. 못 쓰면 임시 파일을 걷고 OSError 를 올린다."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}-{secrets.token_hex(3)}.tmp")
    try:
        tmp.write_bytes(data)
        for attempt in range(REPLACE_TRIES):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if attempt == REPLACE_TRIES - 1:
                    raise
                time.sleep(REPLACE_WAIT_S)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise
