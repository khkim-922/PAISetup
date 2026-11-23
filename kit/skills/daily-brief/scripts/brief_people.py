"""사람을 대는 칸의 값을 사람들로 읽는다(`people_in` → `Person`). 파일 · 망에 닿지 않는다. 꼴의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」이다.
"""

from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_inline.py — `-I` 로 돌아도 싣는다
from brief_inline import LABEL, PERSON_REF, plain  # noqa: E402

# 사람 — 메일 링크처럼 링크 하나가 한 분이다: 「[이름 직함](person:<주소>)」. 글은 사람이 읽는 이름, 주소는 회사 손이 낸 그분의 주소(메일
# 머리 · 주소록 그대로)라 사람을 가르는 열쇠다. 사람을 대는 칸은 이 링크들을 「 · 」로 잇고, 링크 바로 뒤 괄호가 그분의 덧말이다. 꼴이 아닌
# 칸은 쓴 글로만 서고 사람으로 안 센다 — 글을 갈라 사람을 짐작하지 않는다
PERSON_ENTRY = re.compile(rf"\[(?P<name>{LABEL}+)\]\(person:(?P<addr>{PERSON_REF})\)(?:\s*\((?P<note>[^()\n]*)\))?")
PERSON_SEP = re.compile(r"\s*(?:·|,|、)\s*")
PERSON_ADDR = re.compile(r'^[^\s<>"`](?:[^<>"`\n]*[^\s<>"`])?$')   # 주소의 꼴 — 빈 글 · 앞뒤 빈칸 · 꺾쇠 · 따옴표가 없다(메일 주소 · Notes 이름)
PILLS = re.compile(r"\{!?[^{}\n]*\}")                              # 칸 끝에 붙는 표지 — 사람의 꼴을 잴 때 걷는다


@dataclass(frozen=True)
class Person:
    """사람 링크 하나 — 사람이 읽는 이름(직함까지) · 그분을 가르는 주소 · 링크 뒤 괄호의 덧말."""
    name: str
    address: str
    note: str = ""

    def said(self) -> str:
        """사람이 읽는 꼴 — 「이름 직함(덧말)」."""
        return self.name + (f"({self.note})" if self.note else "")


def people_in(value: str) -> list[Person] | None:
    """사람을 대는 칸의 값 → 사람들. 꼴이 아니면 None — 값은 사람 링크(뒤에 괄호 덧말 하나까지)를 「 · 」로 이은 것이고 끝의 표지({…})는 걷고
    잰다. 링크 밖의 글이 하나라도 있으면 꼴이 아니다 — 글을 갈라 사람을 짐작하지 않는다."""
    text, out, at = PILLS.sub("", value).strip(), [], 0
    while True:
        m = PERSON_ENTRY.match(text, at)
        if not m or not PERSON_ADDR.match(m.group("addr")) or not plain(m.group("name")).strip():
            return None
        out.append(Person(" ".join(plain(m.group("name")).split()), m.group("addr"), " ".join((m.group("note") or "").split())))
        at = m.end()
        if at == len(text):
            return out
        sep = PERSON_SEP.match(text, at)
        if not sep or sep.end() == len(text):
            return None
        at = sep.end()
