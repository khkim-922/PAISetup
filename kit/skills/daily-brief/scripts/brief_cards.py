"""줄 · 카드 하나의 생김을 읽는다 — 머리와 때(`card_head`) · 이름(`card_name` · `item_title`) · 앞의 점과 끝의 칸(`split_facts`) · 어느 일인가
(`item_key`). 파일 · 망에 닿지 않는다. 꼴의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」이다.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_text.py · brief_inline.py — `-I` 로 돌아도 싣는다
from brief_inline import first_unid, plain  # noqa: E402
from brief_text import Item  # noqa: E402

FACT = re.compile(r"^(?P<label>[^:：`*{}\[\]]{1,10}?)\s*[:：]\s+(?P<value>\S.*)$")   # 낱낱 끝의 「이름: 값」
LEAD_BOLD = re.compile(r"^\*\*(?P<head>(?:(?!\*\*).)+)\*\*\s*(?:[—–-]+\s*)?(?P<rest>.*)$")
# 카드 · 줄이 어느 일인가 — 이 이름의 칸에 단 메일 링크가 누름 단추의 열쇠다(업무 파일이 그 일을 연 메일). 칸이 없으면 줄의 첫 메일 링크다
WORK_FIELD = "일"
# 사람별 — 줄 끝의 칸 가운데 이 두 이름이 사람을 댄다. 사람별은 주소로 묶는다 — 같은 분이 다른 글(직함 · 덧말)로 적혀도 한 줄이다
WAIT_ME, WAIT_THEM = "기다리는 분", "답 주실 분"


def card_head(text: str) -> tuple[str, str]:
    """줄 머리 → (카드 제목, 그 뒤의 때와 곳). 맨 앞 `**…**` 가 없으면 줄 전체가 제목이고 뒤는 빈 글이다."""
    m = LEAD_BOLD.match(text)
    return (m.group("head"), m.group("rest")) if m else (text, "")


def card_name(it: Item) -> str:
    """카드의 이름 — 제목의 맨글자를 빈칸 하나로 이은 것."""
    return " ".join(plain(card_head(it.text)[0]).split())


def item_title(it: Item) -> str:
    """줄의 일 이름 — 카드면 굵은 머리, 줄이면 맨글자의 줄표(「 — 」) 앞. 줄표 뒤는 형편 · 때 · 근거라 일 이름이 아니다."""
    return card_name(it).split(" — ", 1)[0]


def split_facts(subs: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    """낱낱을 앞의 점과 끝의 칸으로 가른다 — 끝에서부터 「이름: 값」 꼴이 이어지는 데까지가 칸이다."""
    facts: list[tuple[str, str]] = []
    cut = len(subs)
    while cut > 0:
        m = FACT.match(subs[cut - 1])
        if not m:
            break
        facts.insert(0, (m.group("label").strip(), m.group("value")))
        cut -= 1
    return subs[:cut], facts


def item_key(it: Item) -> str | None:
    """줄 · 카드가 어느 일인가 — 누름 단추의 열쇠 메일 번호(대문자). 낱낱에 「일: <메일 링크>」 칸이 있으면 그 메일, 없으면 줄의 첫 메일
    링크(머리부터 낱낱 차례로). 메일 번호가 없으면 None."""
    for s in it.subs:
        m = FACT.match(s)
        if m and m.group("label").strip() == WORK_FIELD and first_unid(m.group("value")):
            return first_unid(m.group("value"))
    return next(filter(None, (first_unid(s) for s in [it.text, *it.subs])), None)
