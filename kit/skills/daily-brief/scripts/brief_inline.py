"""보고 글 한 줄 안의 꼴을 읽는다 — 고정 글자 · 메일 · 사람 · 방 · 절 링크 · 표지 · 굵게(`INLINE`). 맨글자(`plain`) · 첫 메일 번호(`first_unid`) ·
번호를 남긴 맨글자(`with_numbers`) · 글자로 쓴 주소의 수(`url_count`). 파일 · 망에 닿지 않는다. 꼴의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」이다.
"""

from __future__ import annotations

import re

UNID_HEX = r"[0-9A-Fa-f]{32}"                     # 메일 번호의 꼴 — 보고 글 · 맞춤 파일 · 대화의 명령 · 창의 스크립트가 다 이 글로 짓는다
UNID = re.compile(rf"^{UNID_HEX}$")               # 메일 번호 하나 — 링크가 되는 것은 이 꼴의 번호뿐이다
OVER = re.compile(r"\{!([^{}\n]{1,40})\}")         # 붉은 표지(기한 지남) — 사람별의 그 일 곁에도 단다

# 링크 글의 한 글자 — 대괄호 밖의 글자, 또는 속에 대괄호가 없는 대괄호 한 묶음. 메일 · 사람 · 방 · 절 링크가 다 이 꼴로 글을 읽는다
LABEL = r"(?:[^\[\]\n]|\[[^\[\]\n]*\])"
PERSON_REF = r"[^()\n]*"                          # 사람 링크의 주소 자리 — 줄 안의 링크와 사람 칸 읽기(`brief_people`)가 같은 꼴로 읽는다
SECTION_KIND = r"[a-z]+"                          # 절 링크의 종류 자리 — 줄 안의 링크와 절 머리 읽기(`brief_sections`)가 같은 꼴로 읽는다

# 줄 안의 꼴 — 왼쪽부터 먼저 걸린 것. 고정 글자는 속을 안 읽고, 링크 글과 굵게는 속을 한 번 더 읽는다
INLINE = re.compile(
    r"`(?P<code>[^`\n]+)`"
    rf"|\[(?P<label>{LABEL}*)\]\(mail:(?P<ref>[^()\s]*)\)"
    rf"|\[(?P<plabel>{LABEL}+)\]\(person:(?P<pref>{PERSON_REF})\)"
    rf"|\[(?P<rlabel>{LABEL}+)\]\(room:(?P<rref>[^()\s]*)\)"
    rf"|\[(?P<slabel>{LABEL}+)\]\(section:(?P<sref>{SECTION_KIND})\)"
    r"|\{(?P<over>!?)(?P<pill>[^{}\n]{1,40})\}"
    r"|\*\*(?P<bold>(?:(?!\*\*).)+)\*\*"
)
URLISH = re.compile(r"(?i)\b(?:https?|ftp|file|javascript|data|vbscript|mailto):")


def url_count(text: str) -> int:
    """글에 쓴 주소(링크로 짓지 않고 글자로 두는 것)의 수."""
    return len(URLISH.findall(text))


def first_unid(text: str) -> str | None:
    """글에서 처음 걸린 메일 번호(대문자) — 링크로 서는 `[글](mail:<번호>)` 만 센다(굵게 속도). 고정 글자 속 · 번호 꼴이 아닌 것은 안 센다."""
    for m in INLINE.finditer(text):
        if m.group("ref") is not None and UNID.match(m.group("ref")):
            return m.group("ref").upper()
        if m.group("bold") is not None:
            got = first_unid(m.group("bold"))
            if got:
                return got
    return None


def plain(text: str) -> str:
    """꼴 표시를 걷은 맨글자 — 창의 이름(<title>)에 쓴다. 이스케이프는 부르는 쪽이 한다."""
    def strip(m: re.Match) -> str:
        for name in ("code", "label", "plabel", "rlabel", "slabel", "pill", "bold"):
            if m.group(name) is not None:
                return plain(m.group(name)) if name in ("label", "plabel", "rlabel", "slabel", "bold") else m.group(name)
        return m.group(0)
    return INLINE.sub(strip, text)


def with_numbers(text: str) -> str:
    """맨글자 — 메일 링크는 「보일 글 (메일 번호 …)」로, 사람 링크는 「이름 <주소>」로 남긴다. 대화의 첫마디가 그 메일 · 그분을 다시 묻지 않고
    찾게."""
    def keep(m: re.Match) -> str:
        if m.group("ref") is not None and UNID.match(m.group("ref")):
            return f"{m.group('label')} (메일 번호 {m.group('ref').upper()})"
        if m.group("pref") is not None:
            return f"{plain(m.group('plabel'))} <{m.group('pref').strip()}>"
        if m.group("rref") is not None:
            return f"{plain(m.group('rlabel'))} (회의실 id {m.group('rref')})"
        return m.group(0)
    return " ".join(plain(INLINE.sub(keep, text)).split())
