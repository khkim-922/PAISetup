"""기록 손의 콘솔과 시계 — 받는 글(`--in` 의 파일이나 표준 입력)을 글로 풀고, 사람에게 할 줄을 표준 출력에 내고, 지금 때를 댄다."""

from __future__ import annotations

import pathlib
import sys
from collections.abc import Iterable
from datetime import datetime


def decode(raw: bytes) -> str:
    """받은 바이트 → 글. BOM 이 있으면 그 꼴(UTF-8 · UTF-16 — Windows PowerShell 의 `>` 가 쓰는 꼴), 없으면 UTF-8, 안 되면 cp949.
    같은 몸이 스킬 mailbox-work 의 `work.py` · daily-brief 의 `window.py` 에 있다 — 고치면 셋을 함께 고친다(머리말의 받는 꼴이 같다)."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", errors="replace")


def read_input(path: str | None) -> str:
    """`--in` 의 파일이나 표준 입력 — 바이트로 받아 `decode` 한다."""
    raw = pathlib.Path(path).read_bytes() if path else sys.stdin.buffer.read()
    return decode(raw)


def say(lines: Iterable[str]) -> None:
    """사람에게 할 줄들을 차례로 표준 출력에 낸다."""
    for line in lines:
        print(line)


def echo_input(text: str) -> None:
    """받은 손의 글을 줄마다 그대로 다시 낸다 — 파이프가 받아 가 사람에게 보일 글이 이것뿐이다."""
    say(text.splitlines())


def now() -> str:
    """지금 때 — 기록 · 안에 적는 꼴(초까지 · 시간대를 붙인 ISO)."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def utf8_out() -> None:
    """표준 출력을 UTF-8 로 다시 잡는다 — 한글 Windows 의 cp949 콘솔이 리디렉션 · 파이프에서 한글을 깨지 않게."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
