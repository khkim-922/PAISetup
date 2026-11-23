"""메일 한 통의 받는 사람 명단 — 받은 메일의 「함께 받은 사람」을 받는 사람 목록 보기에서 꺼내고, 명단 줄의 칸과 한 줄의 말을 정한다.

부르는 꼴::

    import mail_recipients as R
    rows = box.sent_people(unid)                         # 보낸 메일 — 받는 사람 · 참조 · 숨은참조 칸 그대로(inbox.Recipient 여럿)
    got = R.received_together(box, unid)                 # 받은 메일 — (명단, 못 읽은 꼴, 훑은 줄 수)
    if got.state:
        why = R.together_why(got)                        # 못 읽은 까닭의 말 — 부르는 쪽이 「말하고 잇기」 · 「멈추기」를 고른다
    R.field_of(r) · R.person_word(r)                     # 줄의 칸 · 한 줄의 말

보낸 메일은 웹메일이 숨은참조를 안 남기기도 해 숨은참조 칸이 비면 있었는지 모른다(``BCC_UNKNOWN``). 받은 메일의 받는 사람 목록 보기는
받는 사람과 참조를 한 글줄로 합쳐 두 칸을 못 가르고, 숨은참조는 받은 쪽에 안 남는다. 이 스킬의 ``read`` 와 형제 스킬
company-directory 의 「지난 메일」 출처가 같은 명단을 읽는다.
"""

from __future__ import annotations

import pathlib
import sys
from typing import NamedTuple

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))                   # ``-I`` 로 돌면 이 폴더도 ``sys.path`` 에 없다
import inbox  # noqa: E402 — 자리를 넣은 뒤에 싣는다
from mail_people import DEPT_WORD, FIELD_WORDS  # noqa: E402

RECIPIENT_SCAN = inbox.VIEW_PAGE_MOST   # 받은 메일의 함께 받은 사람을 찾는 받는 사람 목록 보기의 새것 줄 수 — 그 보기는 한 장만 받는다
BCC_UNKNOWN = "숨은참조 — 보낸 메일에는 웹메일이 숨은참조를 안 남겨 있었는지 모른다. 있었으면 사람이 다시 넣는다"
NO_VIEW, NOT_IN_VIEW, EMPTY = "no_view", "not_in_view", "empty"   # 함께 받은 사람을 못 읽은 꼴 — 빈 글자는 읽었다
TOGETHER_WHY = {NO_VIEW: "이 메일함에 받는 사람 목록 보기가 없다", NOT_IN_VIEW: "받는 사람 목록 보기의 새것 {seen}줄에 그 메일이 없다",
                EMPTY: "받는 사람 목록 보기의 그 메일 줄이 비었다"}


class Together(NamedTuple):
    """받은 메일 한 통의 함께 받은 사람 — 명단 · 못 읽은 꼴(``NO_VIEW`` · ``NOT_IN_VIEW`` · ``EMPTY`` · 읽었으면 빈 글자) · 훑은 줄 수."""
    rows: tuple
    state: str
    seen: int


def received_together(box, unid: str) -> Together:
    """받은 메일 한 통의 함께 받은 사람을 받는 사람 목록 보기의 새것 ``RECIPIENT_SCAN`` 줄에서 꺼낸다. 메일함 오류
    (``inbox.MailboxError`` · 끊긴 세션)는 부르는 쪽으로 그대로 간다."""
    lists = box.recipient_lists(RECIPIENT_SCAN)
    if lists is None:
        return Together((), NO_VIEW, 0)
    rows = {u.upper(): r for u, r in lists.items()}.get(unid.upper())
    if rows is None:
        return Together((), NOT_IN_VIEW, len(lists))
    return Together(rows, "" if rows else EMPTY, len(lists))


def together_why(got: Together) -> str:
    """함께 받은 사람을 못 읽은 까닭을 사람 말로."""
    return TOGETHER_WHY[got.state].format(seen=got.seen)


def field_of(r) -> str:
    """명단 줄 하나가 든 칸 — 칸을 모르는 줄은 받는 사람 칸이다."""
    return r.field if r.field in FIELD_WORDS else "to"


def person_word(r) -> str:
    """받는 사람 줄 하나를 한 줄로 — 조직은 이름 뒤에 표지를, 주소가 없으면 열쇠 그대로."""
    name = f"{r.name}{DEPT_WORD}" if r.kind == inbox.DEPT_TYPE else r.name
    return " · ".join(x for x in (name, r.addr) if x) or r.notes
