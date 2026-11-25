"""창 곁의 거두는 손을 띄울 창인가를 가르는 한 자리 — 창을 여는 손(`window.py`)과 시계 판의 뒷받침(`presses.round_once`)이 같은 자로 잰다.
보고 글과 부르는 쪽이 이미 든 두 값(보고가 걸렸나 · 부탁 칸이 서나)만 본다 — 파일 · 이 PC 를 읽지 않는다.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_tasks.py — `-I` 로 돌아도 싣는다
from brief_inline import approvals_in  # noqa: E402
from brief_tasks import cards_of, tasks_of  # noqa: E402
from task_kinds import VIA_NONE  # noqa: E402


def hand_wanted(text: str, scheduled: bool, ask_ready: bool) -> bool:
    """창 곁의 거두는 손을 띄울 창인가 — 「일정 넣기」 카드가 있거나, 맡길 일이 있거나, 보고가 걸려(`scheduled`) 「보고 맞추기」에 「자리 밖에서
    보기」 단추가 서거나, 창 머리에 「비서에게 부탁하기」 칸이 서거나(`ask_ready`), 「결재 창 열기」 단추가 서는(결재 문서 링크) 창."""
    return bool(cards_of(text)) or bool(approvals_in(text)) or any(t.row.via != VIA_NONE for t in tasks_of(text).values()) or scheduled or ask_ready
