"""보고 글을 제목 · 절 · 덩이로 가른다(`parse` → `Report` · `Section` · `Block` · `Item`) — 줄의 꼴(머리 · 번호 · 「-」 · 들여 쓴 낱낱 · 인용 ·
「@」 시간줄 · 가름줄)만 읽고, 줄 안의 꼴 · 카드 · 절의 뜻은 곁의 읽기(`brief_inline` · `brief_cards` · `brief_sections` · `brief_tasks`)가 든다.
파일 · 망에 닿지 않는다. 꼴의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」이다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# 줄의 꼴 — `lane.md` 「보고 글의 꼴」
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
NUMBERED = re.compile(r"^(\d{1,3})[.)]\s+(.*)$")
BULLET = re.compile(r"^[-*+]\s+(.*)$")
SUB = re.compile(r"^(?: {2,}|\t)\s*(?:[-*+]|\d{1,3}[.)])\s+(.*)$")
INDENTED = re.compile(r"^(?: {2,}|\t)\s*(\S.*)$")
QUOTE = re.compile(r"^>\s?(.*)$")
CLOCK = re.compile(r"^@\s+(.*)$")
THEMATIC = re.compile(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$")
DASH = re.compile(r"\s+[—–-]\s+")             # 시간줄의 가름 — 빈칸을 끼운 줄표(「 — 」)


@dataclass
class Item:
    """목록 덩이의 줄 하나 — 쓴 번호 · 글 · 그 아래 줄."""
    num: str | None                 # 쓴 번호 — 「-」 줄이면 None
    text: str
    subs: list[str] = field(default_factory=list)


@dataclass
class Block:
    """보고 글의 덩이 하나 — 꼴(문단 · 목록 · 인용 · 시간줄 · 작은 절)과 그 줄 · 시간줄의 둘레 줄."""
    kind: str                       # para · list · quote · clock · sub
    lines: list = field(default_factory=list)       # para · quote · sub(제목 한 줄) — 글 줄 / list — Item / clock — 「@」 줄
    label: list[str] = field(default_factory=list)  # clock — 바로 위 줄(그 이름)
    after: list[str] = field(default_factory=list)  # clock — 바로 아래 줄(곁말)


@dataclass
class Section:
    """보고 글의 절 하나 — 제목과 덩이들."""
    title: str | None               # None 이면 첫 절 앞(제목 밑)
    blocks: list[Block] = field(default_factory=list)


@dataclass
class Report:
    """보고 글 한 편 — 제목 · 절들 · 첫 제목 뒤에 더 나온 「# 」 제목의 수."""
    title: str | None = None
    sections: list[Section] = field(default_factory=lambda: [Section(None)])
    extra_titles: int = 0


def parse(text: str) -> Report:
    """보고 글을 제목 · 절 · 덩이로 가른다. 꼴을 모르는 줄은 문단의 글로 남긴다 — 버리는 줄은 빈 줄과 가름줄(---)뿐이다."""
    rep = Report()
    block: Block | None = None
    blank = False

    def sec() -> Section:
        return rep.sections[-1]

    def start(kind: str) -> Block:
        nonlocal block
        block = Block(kind)
        sec().blocks.append(block)
        return block

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            blank = True
            if block is not None and block.kind != "list":
                block = None
            continue
        if THEMATIC.match(line):
            block, blank = None, False
            continue
        head = HEADING.match(line)
        if head:
            level, words = len(head.group(1)), head.group(2)
            if level == 1 and rep.title is None:
                rep.title = words
            elif level <= 2:
                rep.extra_titles += level == 1
                rep.sections.append(Section(words))
            else:
                start("sub").lines.append(words)
            block, blank = None, False
            continue
        clock = CLOCK.match(line)
        if clock:
            if block is not None and block.kind == "clock" and not block.after and not blank:
                block.lines.append(clock.group(1))
            elif block is not None and block.kind == "para" and not blank:
                block.kind, block.label, block.lines = "clock", block.lines, [clock.group(1)]
            else:
                start("clock").lines.append(clock.group(1))
            blank = False
            continue
        if block is not None and block.kind == "clock" and not blank:
            block.after.append(line.strip())
            continue
        quote = QUOTE.match(line)
        if quote:
            if block is None or block.kind != "quote":
                start("quote")
            block.lines.append(quote.group(1))
            blank = False
            continue
        item = NUMBERED.match(line) or BULLET.match(line)
        if item:
            num, words = (item.group(1), item.group(2)) if item.re is NUMBERED else (None, item.group(1))
            if block is None or block.kind != "list":
                start("list")
            block.lines.append(Item(num, words.strip()))
            blank = False
            continue
        sub = SUB.match(line)
        if sub and block is not None and block.kind == "list":
            block.lines[-1].subs.append(sub.group(1).strip())
            blank = False
            continue
        if sub:                                    # 위에 줄이 없는 들여 쓴 낱낱 — 줄로 세운다
            start("list").lines.append(Item(None, sub.group(1).strip()))
            blank = False
            continue
        indented = INDENTED.match(line)
        if block is not None and block.kind == "list" and (indented or not blank):
            last = block.lines[-1]                 # 이어 쓴 줄 — 바로 위 낱낱이나 줄에 붙인다
            words = (indented.group(1) if indented else line).strip()
            if last.subs:
                last.subs[-1] += " " + words
            else:
                last.text += " " + words
            blank = False
            continue
        if block is not None and block.kind == "para" and not blank:
            block.lines.append(line.strip())
        else:
            start("para").lines.append(line.strip())
        blank = False
    return rep
