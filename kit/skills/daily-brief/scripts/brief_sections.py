"""보고 글의 절을 가리고 고친다 — 머리가 그 절을 이르나(`names_section` · `starts_named`) · 절 머리의 종류(`section_kind` · `is_meetings`) · 창에 안
세울 기록 절(`is_empty_done`) · 창에 서는 줄의 차례(`report_items`) · 빠진 끝의 절(`missing_ends`), 글 줄에서 절의 자리(`section_span`) ·
줄(`section_rows`) · 기록 절 고치기(`fold`). 파일 · 망에 닿지 않는다. 꼴의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」 · 「남긴다」다.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_text.py · brief_inline.py — `-I` 로 돌아도 싣는다
from brief_inline import LABEL, SECTION_KIND, first_unid, plain  # noqa: E402
from brief_text import HEADING, Report, Section  # noqa: E402

# 끝의 두 절 — 다음 보고가 남은 글에서 어디부터 읽을지와 다시 올리지 않을 것을 찾는 자리(`lane.md` 「남긴다」). 머리가 이 말로 시작하면 그 절이다
END_SECTIONS = ("이 보고가 본 데", "끝났다고 하신 것")
DONE_SECTION = END_SECTIONS[1]
# 끝나지 않았다고 되돌리신 일 — 있을 때만 서는 끝의 절. 다음 업무 파악이 이 절로 「끝난 일」에서 그 일을 다시 연다
REOPEN_SECTION = "안 끝났다고 하신 것"
RECORD_SECTIONS = (*END_SECTIONS, REOPEN_SECTION)   # 다음 보고의 기록인 절 — 「끝났음」 상자는 「끝났다고 하신 것」에만 선다
NONE_LINE = re.compile(r"^(?:[-*+]\s*)?(?:없음|없습니다|없다)\s*\.?$")   # 줄 대신 쓴 「없음」 — 이 줄뿐인 「끝났다고 하신 것」은 창에 안 세운다
NONE_ROW = "- 없음"                                                  # 줄이 없는 절에 손이 세우는 한 줄(`NONE_LINE` 이 읽는다)
# 절의 종류 — 머리가 링크 하나인 절: 「## [사람이 읽는 절 이름](section:<종류>)」. 이름은 모델이 그날 맞게 쓰고, 창은 종류만 읽는다
SECTION_HEAD = re.compile(rf"^\[(?P<name>{LABEL}+)\]\(section:(?P<kind>{SECTION_KIND})\)$")
# 회의 한 장의 절 — 회의는 일이 아니라 이 절의 카드에는 누름 단추를 안 단다(그 안의 답 안 한 요청은 제 카드에서 누른다). 이름 글자로 읽는
# `MEETING_SECTION` 은 종류 표지 없이 쓴 글(표지 전의 보고 글)을 위한 것이다
MEETINGS = "meetings"
MEETING_SECTION = "오늘 · 내일 회의"


def starts_named(words: str, names: str | tuple[str, ...]) -> bool:
    """머리의 글(꼴 표시를 걷었든 안 걷었든 받은 그대로)이 절 이름 `names` 가운데 하나로 시작하나 — 앞뒤 빈칸은 안 본다. 「(2건)」 같은 덧말은
    괜찮다. 절을 이름으로 가리는 자리가 다 이 한 자로 잰다 — 꼴 표시를 걷는 읽기는 `names_section`, 옛 보고 글을 적힌 그대로 읽는 `old_forms` 는 이것."""
    return words.strip().startswith(names)


def names_section(title: str | None, names: str | tuple[str, ...]) -> bool:
    """절 머리 `title` 이 절 `names` 가운데 하나를 이르나 — 굵게 · 링크 같은 꼴 표시를 걷은 맨글자(`plain`)로 `starts_named`. 머리가 없으면 거짓."""
    return starts_named(plain(title or ""), names)


def section_kind(title: str | None) -> str:
    """절 머리의 종류 — 머리 전체가 「[이름](section:<종류>)」 꼴이면 그 종류, 아니면 빈 글."""
    m = SECTION_HEAD.match((title or "").strip())
    return m.group("kind") if m else ""


def is_meetings(title: str | None) -> bool:
    """회의 한 장의 절인가 — 종류 표지(`MEETINGS`)가 든 머리, 표지 없이 쓴 글이면 이름이 `MEETING_SECTION` 으로 시작하는 머리."""
    return section_kind(title) == MEETINGS or names_section(title, MEETING_SECTION)


def is_empty_done(sec: Section) -> bool:
    """줄이 없거나 「없음」 한 줄뿐인 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」 — 창에 안 세운다(보고 글에는 그대로 남아 다음 보고가 잇는다)."""
    if not names_section(sec.title, (DONE_SECTION, REOPEN_SECTION)):
        return False
    words: list[str] = []
    for b in sec.blocks:
        if b.kind == "list":
            words += [w for i in b.lines for w in (i.text, *i.subs)]
        else:
            words += [*b.lines, *b.label, *b.after]
    return all(NONE_LINE.match(w.strip()) for w in words)


def report_items(rep: Report):
    """창에 서는 줄을 창이 세우는 차례로 — 빈 「끝났다고 하신 것」 절은 창처럼 건너뛴다."""
    for sec in rep.sections:
        if sec.title is not None and is_empty_done(sec):
            continue
        for b in sec.blocks:
            yield from (b.lines if b.kind == "list" else ())


def missing_ends(rep: Report) -> list[str]:
    """글에 없는 끝의 절 — 절(##)이나 작은 절(###)의 머리가 그 이름으로 시작하면 있는 것으로 본다(「(2건)」 같은 덧말 · 굵게는 괜찮다)."""
    heads = [s.title for s in rep.sections[1:] if s.title]
    heads += [b.lines[0] for s in rep.sections for b in s.blocks if b.kind == "sub"]
    return [end for end in END_SECTIONS if not any(names_section(h, end) for h in heads)]


def section_span(rows: list[str], name: str) -> tuple[int | None, int]:
    """글 줄들에서 절 `name` 의 자리 — (머리 줄, 그 절이 끝나는 줄(다음 같은 층 이상의 머리 · 없으면 끝)). 머리(## · ###)가 그 이름으로 시작하는
    첫 절이다. 없으면 (None, 줄 수)."""
    start, level = None, 0
    for i, row in enumerate(rows):
        head = HEADING.match(row)
        if not head:
            continue
        if start is not None and len(head.group(1)) <= level:
            return start, i
        if start is None and len(head.group(1)) in (2, 3) and names_section(head.group(2), name):
            start, level = i, len(head.group(1))
    return start, len(rows)


def section_rows(text: str, name: str) -> list[str]:
    """절 `name` 의 줄 — 빈 줄과 「없음」 줄을 뺀 그대로. 절이 없으면 빈 것."""
    rows = text.split("\n")
    start, end = section_span(rows, name)
    return [] if start is None else [r for r in rows[start + 1:end] if r.strip() and not NONE_LINE.match(r.strip())]


def row_keys(rows: list[str]) -> set[str]:
    """줄들의 열쇠 — 줄마다 첫 메일 번호(창의 상자와 같다). 둘째부터의 번호는 근거일 뿐이라 열쇠가 아니다 — 그 번호의 표시가 남의 줄을 건드리지 않는다."""
    return {k for k in map(first_unid, rows) if k}


def section_keys(text: str, name: str) -> set[str]:
    """보고 글의 절 `name` 에 든 줄들의 열쇠(`row_keys`). 절이 없으면 빈 것."""
    rows = text.split("\n")
    start, end = section_span(rows, name)
    return set() if start is None else row_keys(rows[start + 1:end])


def fold(text: str, name: str, lines: list[str], drop: set[str] = frozenset()) -> str:
    """보고 글의 절 `name` 에서 열쇠(`row_keys`)가 `drop` 에 든 줄을 걷고 끝에 `lines` 를 더한 글. 걷을 것도 더할 것도 없으면 글 그대로다.
    절이 없으면 더할 줄이 있을 때만 글 끝에 세운다. 줄을 더할 때 그 절의 「없음」 줄은 걷는다 — 남기면 「없음」과 일이 한 절에 함께 선다."""
    rows = text.split("\n")
    start, end = section_span(rows, name)
    if start is None:
        if not lines:
            return text
        body = text.rstrip("\n")
        return f"{body}\n\n## {name}\n" + "\n".join(lines) + "\n"
    section = rows[start + 1:end]
    if not lines and not (drop & row_keys(section)):
        return text
    kept = [r for r in section if not (lines and NONE_LINE.match(r.strip())) and first_unid(r) not in drop]
    while kept and not kept[-1].strip():
        kept.pop()
    tail = [""] if end < len(rows) else []
    new = rows[:start + 1] + kept + lines + tail + rows[end:]
    out = "\n".join(new)
    return out if out.endswith("\n") else out + "\n"
