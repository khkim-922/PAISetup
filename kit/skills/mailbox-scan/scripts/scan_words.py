"""스캔 한 판의 말 — 판 끝 한 줄 · 판의 갈래와 끝 낱말 · 세션을 기다리는 주기의 말. 바깥에 안 닿고 셈은 안 한다.

    print(summary(record))                       # 판 끝 한 줄 — 수와 때만
    OUTCOME_WORDS[outcome] · MODE_WORDS[mode]    # status 의 마지막 판 줄도 같은 말을 쓴다
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import scan_const as C
import scan_time as tm

OUTCOME_WORDS = {C.RUN_DONE: "됐다", C.RUN_FIRST: "첫 판 — 메일함의 바닥을 적었다(바뀜은 다음 판부터)",
                 C.RUN_PARTIAL: "다 못 봤다 — 다 본 상자까지 적고 다음 판이 잇는다",
                 C.RUN_SESSION: f"사내 세션이 없어 멈췄다 — 다음: {C.NEXT_LOGIN} 한다", C.RUN_BUSY: "앞 판이 돌아 건너뛰었다",
                 C.RUN_HAND_MISSING: f"회사 메일 손을 못 찾아 멈췄다 — 다음: {C.NEXT_HAND_MISSING}",
                 C.RUN_HAND_OLD: f"회사 메일 손이 옛 판이라 멈췄다 — 다음: {C.NEXT_HAND_OLD}",
                 C.RUN_HAND_ERROR: "회사 메일 손이 오류를 내 멈췄다 — 다음: reader.py status 가 손의 말을 보인다",
                 C.RUN_SHAPE: "회사 메일 손의 글 꼴이 이 스킬이 아는 꼴과 달라 멈췄다 — 다음: 손이 바뀐 것이다. 이 스킬의 hand_lines.py 를 손의 새 꼴에 맞춘다",
                 C.RUN_SWAP: "지금 모습을 바꿔 끼우지 못했다 — 옛 판이 그대로다. 다음 판이 다시 쓴다",
                 C.RUN_UNREAD: "판이 기대는 파일을 못 읽어 아무것도 안 쓰고 멈췄다 — 지금 모습 · 보고 시각표는 그대로다. 다음 판이 다시 읽는다"}
MODE_WORDS = {C.MODE_FULL: "메일함 전체", C.MODE_NEW: "새 메일만", "-": "—"}


def summary(record: dict[str, Any]) -> str:
    """판 끝의 한 줄 — 수와 때만(메일의 글은 안 싣는다)."""
    parts = [MODE_WORDS.get(record["mode"], record["mode"]), OUTCOME_WORDS.get(record["outcome"], record["outcome"]),
             f"새 메일 {record['new']}통 · 바뀜 {record['changes']}건", f"손 {record['calls']}번 · {record['seconds']}초"]
    if record.get("short"):
        parts.append(f"덜 본 자리 {len(record['short'])}곳")
    return "[스캔 — " + " · ".join(parts) + "]"


def busy_words(holder: datetime | None) -> str:
    """앞 판이 돌아 이번 주기를 건너뛴 한 줄 — 앞 판의 시작 때와 함께."""
    return f"[스캔 — 앞 판({tm.seoul(holder)} 시작)이 돌고 있어 이번 주기는 건너뛰었다]"


def gave_up_words(holder: datetime | None, waited_s: int) -> str:
    """앞 판을 준 시한만큼 기다렸는데 안 끝나 이번 판을 그만둔 한 줄(`run --wait`) — 앞 판의 시작 때 · 기다린 초와 함께."""
    return f"[스캔 — 앞 판({tm.seoul(holder)} 시작)이 {waited_s}초 기다려도 안 끝나 이번 판은 건너뛰었다]"


def waited_note(waited_s: int) -> str:
    """판 기록의 메모 — 앞 판의 잠금이 풀리기를 기다린 초(`run --wait`)."""
    return f"앞 판의 잠금을 {waited_s}초 기다렸다"


def waiting_words(lost_at: datetime | None, next_try: datetime | None) -> str:
    """세션이 끊겨 이번 판을 안 도는 까닭과 다음 걸음."""
    return (f"사내 세션이 끊겨 {tm.seoul(lost_at)}부터 멈춰 있다 — 다음 두드림은 {tm.seoul(next_try)}(다음: {C.NEXT_LOGIN} "
            "한 뒤 run --now 로 지금 돌린다)")
