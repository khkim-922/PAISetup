"""칸의 상태의 꼴 — 그날 칸 하나의 상태 이름과 그 셈을 담는 그릇. 셈하는 조각(`brief_state`)이 채우고 말을 짓는 조각(`brief_words`)이
읽는다. 바깥에 안 닿는다.

상태 — 앞의 것이 이긴다:
    MADE      그 칸의 보고 글이 섰다(대화에서 지은 것도)
    FAILED    띄우려다 못 띄웠다
    WRITING   띄운 보고가 아직 돈다(띄운 프로세스 · 출력으로 가른다)
    EMPTY     띄운 보고가 글 없이 끝났다
    LEFT      띄운 보고가 끝나 글을 남겼는데 그 칸의 보고 글로는 안 잡혔다(자정을 넘겨 남긴 글 따위)
    AHEAD     칸이 아직 안 열렸다
    PAST_SET  시각표를 걸기 전에 이미 끝났고 한 번도 안 살펴봤다(건너뛴 것이 아니다)
    SKIPPED   보고 없이 칸이 끝났다
    RUNNING   앞 칸이 띄운 보고의 잠금이 아직 새것이다
    WAITING   살펴봤는데 사내 세션이 없어 기다린다
    DUE       칸이 열렸고 아직 안 살펴봤다
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

MADE, FAILED, WRITING, EMPTY, LEFT, AHEAD, PAST_SET, SKIPPED, RUNNING, WAITING, DUE = (
    "made", "failed", "writing", "empty", "left", "ahead", "past-set", "skipped", "running", "waiting", "due")
SETTLED = (MADE, FAILED, WRITING, EMPTY, LEFT)        # 그 칸의 일이 이미 났다 — 글이 섰거나 띄웠다(띄우다 못 띄운 것도)
BUSY = SETTLED + (RUNNING,)                          # 이 상태의 칸에서는 살펴보지도 띄우지도 않는다 — 난 칸 · 앞 보고가 도는 칸
UNSCHEDULED = "unscheduled"                          # status 만의 상태 — 시계 작업이 안 걸려 이 칸은 안 뜬다(아직 일이 안 난 칸)
# 그 칸의 보고 글이 어떻게 섰나(MADE 만) — 스캔이 띄워서 · 칸이 열리기 전에 지은 글이 대신 · 칸 안에서 지어서
MADE_SCAN, MADE_EARLY, MADE_IN = "scan", "early", "in"

# 고름을 받는 가름 — 이미 받았다 · 얹는다 · 새 고름 · 나중의 말씀에 졌다 · 꼴이 아니다 · 못 읽었다 · 걸린 보고가 없다 · 주소를 못 받았다 ·
# 그 사이 보고가 내려졌다(보고 창의 시각 · 자리 밖에서 보기)
AGAIN, APPLY, NEW, STALE, BAD, UNREAD, UNSET, NO_ADDRESS, GONE = (
    "again", "apply", "new", "stale", "bad", "unread", "unset", "no-address", "gone")

# 청한 스캔 판이 안 돈 까닭 — 앞 판이 기다림의 시한 안에 안 끝났다 · 스캔이 판을 못 하고 멈췄다 · 스캔을 못 불렀다(없다 · 시한 · 답의 꼴)
SCAN_LATE, SCAN_STOPPED, SCAN_UNREACHED = "scan-late", "scan-stopped", "scan-unreached"

# 칸의 메일 기록이 지금 어떤가 — 기록 없음 · 보냈다 · 칸이 끝나기 전이라 판마다 다시 보낸다 · 칸이 끝나 못 보냈다 · 보냈는지 모른다
MAIL_NONE, MAIL_SENT, MAIL_RETRYING, MAIL_FAILED, MAIL_UNSURE = "none", "sent", "retrying", "failed", "unsure"
# 자리 밖에서 보기 판 끝의 일 — 「보내는 중」 표지를 못 읽었다 · 표지가 없거나 걷었다 · 앞 판의 표지로 칸을 「모른다」로 맺었다 ·
# 시간이 모자라 다음 판에 둔다 · 표지를 못 굳혔다 · 한 통 보내 봤다
AWAY_MARK_UNREAD, AWAY_CLEAR, AWAY_LEFT, AWAY_LATE, AWAY_MARK_FAILED, AWAY_TRIED = (
    "mark-unread", "clear", "left", "late", "mark-failed", "tried")

# 건너뛴 까닭 — 스캔 판이 안 돌았다 · 손이 세션을 못 살펴봤다 · 사내 세션이 없고 그 칸의 스스로 로그인도 안 섰다 · 사내 세션이 없었다
NO_RUN, HAND_ERROR, LOGIN_UNSET, NO_SESSION = "no-run", "hand-error", "login-unset", "no-session"
# 스스로 로그인의 입구를 부를 판 — 그날 첫 시각의 한 번(세션이 살았어도 · 끝은 그날 장부의 `login`) · 뒤 시각의 칸에서 세션이 없을 때 한 번(끝은 그 칸의 `login`)
LOGIN_DAILY, LOGIN_SLOT = "daily", "slot"


@dataclass
class Slot:
    """칸 하나의 셈 — 시각 · 차례 · 시작 · 끝 · 그날 장부의 칸 · 그 칸의 보고 글 · 상태 · 걸기 전에 끝난 안 살펴본 칸인가 · 띄운 보고의
    출력 끝 줄(글 없이 끝난 칸만) · 보고 글이 어떻게 섰나와 칸이 열리기 전에 지은 글의 때(MADE 만)."""
    t: str
    order: int
    start: datetime
    end: datetime
    slot: dict[str, Any]
    made: list[pathlib.Path] = field(default_factory=list)
    state: str = DUE
    unset: bool = False
    tail: str = ""
    made_how: str = ""
    early_at: str = ""


@dataclass
class Told:
    """보고가 아직 말하지 않은 칸 — 마지막 보고 뒤의 칸마다 (상태, 시각, 값) · 그 앞날의 줄(`before`)도 말할 차례인가 · 못 간 메일마다
    (끝을 적은 때, 시각, 메일 끝, 까닭)."""
    items: list[tuple[Any, ...]]
    with_before: bool
    mails: list[tuple[Any, ...]]
