"""보고 글(md)을 보고 창의 틀에 채워 그날의 HTML 로 남기고, 그 글을 곁에 남기고, 브라우저로 띄운다 — 일일 보고 스킬의 내는 손.

    python -X utf8 -I window.py --dir <사용자 폴더> --mailbox <메일함 주소> [--in <보고 글>] [--no-open]

    보고 글 — `--in` 의 파일, 없으면 표준 입력(UTF-8 · BOM 있는 UTF-16 · cp949). 꼴은 `lane.md` 「보고 글의 꼴」이 든다
    --dir     — 창과 보고 글을 남길 사용자 폴더. 한 번만 받는다(사람 없는 실행이 고정한 경계라서다) · 없는 폴더는 만들지 않는다
    --mailbox — 회사 메일 스킬의 `session` 이 낸 메일함 주소. 없거나 꼴이 아니면 메일 줄을 링크 없이 세운다
    --no-open — 짓기만 하고 띄우지 않는다. 띄울 때는 로그인 Edge 의 새 탭이 먼저고, 안 되면 기본 브라우저다

내는 것 — `<--dir>/brief-YYYY-MM-DD-HHMM.html`(이 PC 의 시각)과 같은 이름의 `.md`(받은 보고 글 · 다음 보고가 읽는 기록). 표준 출력의 끝
줄이 두 파일 · 절 · 줄 · 메일 링크의 수 · 띄웠나를 말하고, 경고 줄이 앞에, 「다음: …」이 뒤에 선다. 메일함 주소는 부르지 않는다.
창의 끝에는 「보고 맞추기」가 선다 — 같은 폴더의 보고 시각표(스킬 mailbox-scan 의 설정)와 보고 맞춤 파일(곁의 `prefs.py`)을 읽기만 해 보인다.
무엇을 지키고 왜 그런가는 `references/DESIGN.md` 가 든다.

종료 값 — 0 지었다 · 1 못 지었다(제목이 없다 · 글을 못 읽었다 · 폴더가 없다 · 못 썼다 — 끝 줄이 다음 걸음을 말한다) · 2 인자가 틀렸다.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import http.client
import os
import pathlib
import re
import string
import sys
import webbrowser
import json
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 prefs.py — `-I` 로 돌아도 싣는다
import prefs as P  # noqa: E402

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "assets" / "report.html"
SCRIPT = TEMPLATE.with_name("report.js")      # 창의 하나뿐인 스크립트 — 누르신 표시 · 고르신 시각. CSP 는 지을 때마다 이 글의 해시만 연다
FILE_NAME = "brief-{:%Y-%m-%d-%H%M}.html"
# 요일 이름 — ep-login 의 `ep_command.WEEKDAYS` 의 손사본이다(이 손은 홀로 서야 해서 못 싣는다). 하나를 고치면 다른 하나도 고친다
WEEKDAYS = "월화수목금토일"
DATELINE = "{:%Y-%m-%d}({}) {:%H:%M} 지음"

EDGE_HOST = "127.0.0.1"                        # 사용자의 로그인 Edge 는 이 PC 의 디버깅 포트에만 있다 — 다른 호스트는 부르지 않는다
EDGE_PORT_DEFAULT = "9222"                     # 스킬 ep-login 이 여는 포트(환경변수 EDGE_DEBUG_PORT 로 바뀐다 · 쉼표로 여럿이면 첫 것)
EDGE_TIMEOUT_S = 2

EXIT_OK, EXIT_FAIL = 0, 1                     # 틀린 인자는 argparse 가 2 로 나간다

# 끝의 두 절 — 다음 보고가 남은 글에서 어디부터 읽을지와 다시 올리지 않을 것을 찾는 자리(`lane.md` 「남긴다」). 머리가 이 말로 시작하면 그 절이다
END_SECTIONS = ("이 보고가 본 데", "끝났다고 하신 것")
DONE_SECTION = END_SECTIONS[1]
# 끝나지 않았다고 되돌리신 일 — 있을 때만 서는 끝의 절. 다음 업무 파악이 이 절로 「끝난 일」에서 그 일을 다시 연다
REOPEN_SECTION = "안 끝났다고 하신 것"
RECORD_SECTIONS = (*END_SECTIONS, REOPEN_SECTION)   # 다음 보고의 기록인 절 — 「끝났음」 상자는 「끝났다고 하신 것」에만 선다
NONE_LINE = re.compile(r"^(?:[-*+]\s*)?(?:없음|없습니다|없다)\s*\.?$")   # 줄 대신 쓴 「없음」 — 이 줄뿐인 「끝났다고 하신 것」은 창에 안 세운다

# 누르신 표시 — 창은 메일 번호마다 localStorage 의 이 열쇠에 남기고(값의 `mark` 가 무엇을 누르셨나다), 곁의 ticks.py 가 같은 이름으로 거둔다
DONE_PREFIX = "brief-done:"
TIMES_KEY = "brief-times"                      # 「보고 맞추기」에서 고르신 보고 시각 — 스캔 판이 ticks.py --times 로 받아 건다
STATE_KEY = "brief-state"                      # 창이 보이는 지금 모습(`state_of` — 시각표 · 규칙의 수 · 올리지 않을 것 · 내일 다시 볼 것) — 그것을 바꾸는
                                               # 명령(대화의 scan.py brief · prefs.py)과 스캔 판 · 거두는 손이 ticks.py 로 열린 창에 바로 적는다
UNQUIET_PREFIX = "brief-unquiet:"              # 「올리지 않기로 한 것」의 「다시 올리기」 — 맞춤 파일 줄의 열쇠(`prefs.key`)마다
TICK_NONE, TICK_TODO, TICK_DONE = "", "todo", "done"   # 줄의 단추 — 없음 · 할 일의 줄(셋 · 바탕은 안 눌림) · 「끝났다고 하신 것」의 줄(끝났음 하나 · 바탕은 눌림)
# 할 일의 줄에 서는 단추 — (표시의 값, 단추 글, 단추에 올리면 보이는 말). 「끝났다고 하신 것」의 줄에는 첫 것만 선다
MARKS = (("done", "끝났음", "끝난 일 — 다음 보고부터 올리지 않습니다"),
         ("later", "내일 다시", "오늘은 넘기고 내일 첫 보고에 다시 올립니다"),
         ("quiet", "안 올려도 됨", "이런 건 안 올려도 됨 — 이런 일은 보고에 올리지 않습니다(아래 「보고 맞추기」에서 되돌립니다)"))
VIA_EDGE = "via=edge"                          # 로그인 Edge 로 연 창의 주소 꼬리 — 표시가 거둬지는 창만 단추를 보인다
TICK_OFF = "이 창은 메일 비서의 Edge 밖에서 열려 누르신 것을 받지 않습니다 — 끝난 일 · 미룰 일은 대화에서 말씀해 주세요."
# 사람별 — 줄 끝의 칸 가운데 이 두 이름이 사람을 댄다(`lane.md` 「보고 글의 꼴」). 값은 「이름 직함(덧말)」을 「 · 」 · 「,」로 잇는다
WAIT_ME, WAIT_THEM = "기다리는 분", "답 주실 분"
PERSON_SPLIT = re.compile(r"\s*(?:·|,|、)\s*")
# 보고 시각표 — 사용자 폴더 아래 스킬 mailbox-scan 의 설정(원본 이름은 그 스킬 `scan_const.py` 의 SCAN_DIR · BRIEF_FILE). 읽기만 한다
SCAN_BRIEF = ("mailbox-scan", "brief.json")
SCAN_STATE = ("mailbox-scan", "state.json")   # 스캔의 지금 모습 — 마지막 판의 때(`last_run.started`)만 읽는다(스캔이 도나)
OVER = re.compile(r"\{!([^{}\n]{1,40})\}")         # 붉은 표지(기한 지남) — 사람별의 그 일 곁에도 단다

# 메일함 주소 — `http(s)://<호스트>[:<포트>]/…/<이름>.nsf`. 호스트 앞에 사용자 칸(@)이 서는 꼴 · 따옴표 · 빈칸 · 물음표는 받지 않는다
MAILBOX = re.compile(r"^https?://[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::\d{1,5})?(?:/[A-Za-z0-9._~%-]+)*/[A-Za-z0-9._~%-]+\.nsf$",
                     re.IGNORECASE)
MAIL_URL = "{mailbox}/XML_Inbox/{unid}?OpenDocument"   # 웹메일에서 그 메일을 여는 주소 — 폴더에만 든 메일에도 먹는다
UNID = re.compile(r"^[0-9A-Fa-f]{32}$")

# 줄의 꼴 — `lane.md` 「보고 글의 꼴」
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
NUMBERED = re.compile(r"^(\d{1,3})[.)]\s+(.*)$")
BULLET = re.compile(r"^[-*+]\s+(.*)$")
SUB = re.compile(r"^(?: {2,}|\t)\s*(?:[-*+]|\d{1,3}[.)])\s+(.*)$")
INDENTED = re.compile(r"^(?: {2,}|\t)\s*(\S.*)$")
QUOTE = re.compile(r"^>\s?(.*)$")
CLOCK = re.compile(r"^@\s+(.*)$")
THEMATIC = re.compile(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$")
FACT = re.compile(r"^(?P<label>[^:：`*{}\[\]]{1,10}?)\s*[:：]\s+(?P<value>\S.*)$")   # 낱낱 끝의 「이름: 값」
LEAD_BOLD = re.compile(r"^\*\*(?P<head>(?:(?!\*\*).)+)\*\*\s*(?:[—–-]+\s*)?(?P<rest>.*)$")
DASH = re.compile(r"\s+[—–-]\s+")             # 시간줄의 가름 — 빈칸을 끼운 줄표(「 — 」)

# 줄 안의 꼴 — 왼쪽부터 먼저 걸린 것. 고정 글자는 속을 안 읽고, 링크 글과 굵게는 속을 한 번 더 읽는다
INLINE = re.compile(
    r"`(?P<code>[^`\n]+)`"
    r"|\[(?P<label>(?:[^\[\]\n]|\[[^\[\]\n]*\])*)\]\(mail:(?P<ref>[^()\s]*)\)"
    r"|\{(?P<over>!?)(?P<pill>[^{}\n]{1,40})\}"
    r"|\*\*(?P<bold>(?:(?!\*\*).)+)\*\*"
)
URLISH = re.compile(r"(?i)\b(?:https?|ftp|file|javascript|data|vbscript|mailto):")


# ── 읽기 — 보고 글을 덩이로 ────────────────────────────────────────────────

@dataclass
class Item:
    num: str | None                 # 쓴 번호 — 「-」 줄이면 None
    text: str
    subs: list[str] = field(default_factory=list)


@dataclass
class Block:
    kind: str                       # para · list · quote · clock · sub
    lines: list = field(default_factory=list)       # para · quote · sub(제목 한 줄) — 글 줄 / list — Item / clock — 「@」 줄
    label: list[str] = field(default_factory=list)  # clock — 바로 위 줄(그 이름)
    after: list[str] = field(default_factory=list)  # clock — 바로 아래 줄(곁말)


@dataclass
class Section:
    title: str | None               # None 이면 첫 절 앞(제목 밑)
    blocks: list[Block] = field(default_factory=list)


@dataclass
class Report:
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


# ── 줄 안 — 이스케이프와 메일 링크 ──────────────────────────────────────────

@dataclass
class Ink:
    """줄 안을 짓는 손 — 메일함 주소를 들고, 지은 링크 · 링크로 못 지은 메일 번호 · 번호 꼴이 아닌 mail: 표시 · 누름 단추 무리를 세고,
    사람을 댄 줄(`WAIT_ME` · `WAIT_THEM`)을 모은다 — (칸 이름, 사람, 줄의 닻, 일 이름)."""
    mailbox: str | None
    links: int = 0
    unlinked: int = 0
    bad_refs: int = 0
    boxes: int = 0
    waits: list = field(default_factory=list)

    def mail(self, label_html: str, unid: str) -> str:
        unid = unid.upper()
        if self.mailbox is None:
            self.unlinked += 1
            return f'{label_html} <span class="unid">{unid}</span>'
        self.links += 1
        href = html.escape(MAIL_URL.format(mailbox=self.mailbox, unid=unid), quote=True)
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{label_html}</a>'

    def inline(self, text: str, links: bool = True) -> str:
        out, at = [], 0
        for m in INLINE.finditer(text):
            out.append(html.escape(text[at:m.start()], quote=True))
            at = m.end()
            if m.group("code") is not None:
                out.append(f"<code>{html.escape(m.group('code'), quote=True)}</code>")
            elif m.group("ref") is not None:
                ref, label = m.group("ref"), m.group("label")
                if not UNID.match(ref):
                    self.bad_refs += links           # 왼쪽 목록 · 창의 이름처럼 같은 글을 링크 없이 한 번 더 짓는 자리는 안 센다
                    out.append(html.escape(m.group(0), quote=True))
                    continue
                inner = self.inline(label, links=False) if label.strip() else html.escape(ref.upper(), quote=True)
                out.append(self.mail(inner, ref) if links else inner)
            elif m.group("pill") is not None:
                words = m.group("pill").strip()
                if not words:
                    out.append(html.escape(m.group(0), quote=True))
                    continue
                cls = "pill over" if m.group("over") else "pill"
                out.append(f'<span class="{cls}">{html.escape(words, quote=True)}</span>')
            else:
                out.append(f"<strong>{self.inline(m.group('bold'), links)}</strong>")
        out.append(html.escape(text[at:], quote=True))
        return "".join(out)


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
        for name in ("code", "label", "pill", "bold"):
            if m.group(name) is not None:
                return plain(m.group(name)) if name in ("label", "bold") else m.group(name)
        return m.group(0)
    return INLINE.sub(strip, text)


# ── 짓기 — 덩이를 틀의 자리로 ──────────────────────────────────────────────

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


def item_title(it: Item) -> str:
    """줄의 일 이름 — 카드면 굵은 머리, 줄이면 맨글자의 줄표(「 — 」) 앞. 줄표 뒤는 형편 · 때 · 근거라 일 이름이 아니다."""
    m = LEAD_BOLD.match(it.text)
    title = " ".join(plain(m.group("head") if m else it.text).split())
    return title.split(" — ", 1)[0]


def tick_box(it: Item, ink: Ink, tick: str) -> str:
    """누름 단추 무리 — 줄의 첫 메일 번호가 열쇠다(업무 파일은 일을 그 일을 연 메일로 잇는다). 메일 번호가 없으면 빈 글.
    할 일의 줄에는 「끝났음 · 내일 다시 · 안 올려도 됨」 셋이 서고, `tick` 이 `TICK_DONE` 이면 「끝났다고 하신 것」의 줄이라 「끝났음」 하나가
    눌린 채 선다(`data-done`) — 풀면 끝나지 않았다고 되돌리신 것이다. 처음엔 숨어 있다 — 창의 스크립트가 표시를 거둘 수 있는 창에서만 꺼낸다.
    스크립트가 막혀도 누를 수 없는 단추는 안 선다."""
    unid = next(filter(None, (first_unid(s) for s in [it.text, *it.subs])), None)
    if unid is None:
        return ""
    ink.boxes += 1
    title = item_title(it)
    base = ' data-done="1"' if tick == TICK_DONE else ""
    marks = MARKS[:1] if tick == TICK_DONE else MARKS
    buttons = "".join(f'<button type="button" class="mark" data-mark="{k}" aria-pressed="{"true" if base else "false"}" '
                      f'title="{html.escape(hint, quote=True)}">{word}</button>' for k, word, hint in marks)
    return (f'<div class="marks" role="group" aria-label="이 일을" hidden data-unid="{unid}"{base} data-title="{html.escape(title, quote=True)}">'
            f'{buttons}<span class="mark-note" aria-live="polite"></span></div>')


def people_of(value: str) -> list[str]:
    """칸 값에서 사람 — 「 · 」 · 「,」로 가르고, 괄호 덧말 앞까지를 이름으로 든다. 기한 표지 · 메일 링크 같은 꼴은 걷는다."""
    out = []
    for part in PERSON_SPLIT.split(plain(re.sub(r"\{!?[^{}]*\}", "", value))):
        name = " ".join(part.split("(", 1)[0].split()).strip(" -—")
        if name and name not in out:
            out.append(name)
    return out


def note_waits(it: Item, ink: Ink, facts: list[tuple[str, str]]) -> str:
    """사람을 댄 칸이 있으면 그 줄의 닻 이름을 주고 사람별 무리에 넣는다 — 없으면 빈 글."""
    found = [(label, who) for label, value in facts if label in (WAIT_ME, WAIT_THEM) for who in people_of(value)]
    if not found:
        return ""
    anchor = f"w{len({w[2] for w in ink.waits}) + 1}"
    over = next(iter(OVER.findall(" ".join([it.text, *it.subs]))), "").strip()
    ink.waits += [(label, who, anchor, item_title(it), over) for label, who in found]
    return anchor


def render_item(it: Item, ink: Ink, tick: str = TICK_NONE) -> tuple[str, str]:
    """줄 하나 — (무리, HTML). 무리는 card(점이 딸린 줄) · row. `tick` 이 있으면 메일 번호가 든 줄에 「끝났음」 상자를 단다."""
    points, facts = split_facts(it.subs)
    box = tick_box(it, ink, tick) if tick else ""
    anchor = note_waits(it, ink, facts) if tick == TICK_TODO else ""
    at = f' id="{anchor}"' if anchor else ""
    if points:
        m = LEAD_BOLD.match(it.text)
        head, rest = (m.group("head"), m.group("rest")) if m else (it.text, "")
        parts = [f'<div class="task-top"><h3>{ink.inline(head)}</h3>{box}</div>' if box else f"<h3>{ink.inline(head)}</h3>"]
        if rest:
            parts.append(f'<p class="when">{ink.inline(rest)}</p>')
        parts.append('<ul class="points">' + "".join(f"<li>{ink.inline(p)}</li>" for p in points) + "</ul>")
        if facts:
            parts.append('<dl class="facts">' + "".join(f"<dt>{ink.inline(k)}</dt><dd>{ink.inline(v)}</dd>" for k, v in facts)
                         + "</dl>")
        body = "".join(parts)
        if it.num is None:
            return "card", f'<li class="task plain"{at}><div>{body}</div></li>'
        return "card", f'<li class="task"{at}><span class="task-num">{html.escape(it.num)}</span><div>{body}</div></li>'
    tail = "".join(f' <span class="src-inline">({ink.inline(k)}: {ink.inline(v)})</span>' for k, v in facts)
    body = ink.inline(it.text) + tail
    if box:
        body = f'<div class="row-top"><div>{body}</div>{box}</div>'
    if it.num is None:
        return "row", f"<li{at}>{body}</li>"
    return "row", f'<li{at}><span class="num">{html.escape(it.num)}</span><div>{body}</div></li>'


def render_list(items: list[Item], ink: Ink, tick: str = TICK_NONE) -> str:
    """잇단 줄 — 같은 무리(카드 · 줄)와 같은 표(번호 · 「-」)끼리 한 목록으로 묶는다."""
    out: list[str] = []
    group: tuple[str, bool] | None = None
    for it in items:
        kind, piece = render_item(it, ink, tick)
        key = (kind, it.num is not None)
        if key != group:
            if group is not None:
                out.append("</ol>" if group[1] else "</ul>")
            tag = "ol" if key[1] else "ul"
            cls = "tasks" if kind == "card" else ("rows numbered" if key[1] else "rows")
            out.append(f'<{tag} class="{cls}">')
            group = key
        out.append(piece)
    if group is not None:
        out.append("</ol>" if group[1] else "</ul>")
    return "".join(out)


def render_quote(lines: list[str], ink: Ink) -> str:
    """주의 상자 — 「- 」 줄은 목록, 그 밖은 문단(빈 「>」 줄이 문단을 가른다)."""
    out: list[str] = []
    para: list[str] = []
    bullets: list[str] = []

    def flush() -> None:
        if para:
            out.append(f"<p>{ink.inline(' '.join(para))}</p>")
            para.clear()
        if bullets:
            out.append("<ul>" + "".join(f"<li>{ink.inline(b)}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for line in lines:
        bullet = BULLET.match(line.strip())
        if bullet:
            if para:
                flush()
            bullets.append(bullet.group(1).strip())
        elif not line.strip():
            flush()
        else:
            if bullets:
                flush()
            para.append(line.strip())
    flush()
    return '<div class="caution" role="note">' + "".join(out) + "</div>"


def render_clock(b: Block, ink: Ink) -> str:
    entries = []
    for line in b.lines:
        mark, desc, note = (DASH.split(line, maxsplit=2) + ["", ""])[:3]
        piece = f'<span class="t">{ink.inline(mark.strip())}</span>'
        if desc.strip():
            piece += f'<span class="d">{ink.inline(desc.strip())}</span>'
        if note.strip():
            piece += f'<span class="n">{ink.inline(note.strip())}</span>'
        entries.append(f"<li>{piece}</li>")
    parts = ['<div class="clock-wrap">']
    if b.label:
        parts.append(f'<p class="clock-label">{ink.inline(" ".join(b.label))}</p>')
    parts.append(f'<div class="clock-scroll"><ol class="clock" style="--n: {len(entries)}">' + "".join(entries) + "</ol></div>")
    parts += [f'<p class="clock-also">{ink.inline(a)}</p>' for a in b.after]
    parts.append("</div>")
    return "".join(parts)


def render_blocks(blocks: list[Block], ink: Ink, sid: str, toc: list[str], head: bool, tick: str = TICK_TODO) -> str:
    """덩이를 차례대로 — 제목 밑의 문단은 요약 상자로 묶고, 절 머리 바로 뒤 문단은 머리말로 세운다. `tick` 이 있으면 줄에 「끝났음」 상자를 단다."""
    out: list[str] = []
    summary: list[str] = []
    prev = "head"                                  # 바로 앞 덩이 — head(절 머리) · sub(작은 절 머리) · 그 밖
    subs = 0

    def close_summary() -> None:
        if summary:
            out.append('<div class="summary">' + "".join(summary) + "</div>")
            summary.clear()

    for b in blocks:
        if b.kind == "para":
            words = ink.inline(" ".join(b.lines))
            if head:
                summary.append(f"<p>{words}</p>")
            elif prev == "sub":                    # 작은 절의 머리말은 그 머리 안에 선다
                out[-1] = out[-1][:-len("</div>")] + f"<p>{words}</p></div>"
            elif prev == "head":
                out.append(f'<p class="intro">{words}</p>')
            else:
                out.append(f'<p class="para">{words}</p>')
            prev = "para"
            continue
        close_summary()
        prev = b.kind
        if b.kind == "sub":
            subs += 1
            anchor = f"{sid}-{subs}"
            toc.append(f'<li><a class="sub" href="#{anchor}">{ink.inline(b.lines[0], links=False)}</a></li>')
            out.append(f'<div class="sub-head" id="{anchor}"><h3>{ink.inline(b.lines[0])}</h3></div>')
        elif b.kind == "list":
            out.append(render_list(b.lines, ink, tick))
        elif b.kind == "quote":
            out.append(render_quote(b.lines, ink))
        elif b.kind == "clock":
            if head and b.label:
                toc.insert(0, f'<li><a href="#top">{ink.inline(" ".join(b.label), links=False)}</a></li>')
            out.append(render_clock(b, ink))
    close_summary()
    return "".join(out)


def section_tick(title: str | None) -> str:
    """절의 줄에 다는 상자 — 「끝났다고 하신 것」은 눌린 것이 바탕인 상자, 다른 기록의 절은 없음, 나머지는 할 일의 상자."""
    name = plain(title or "").strip()
    if name.startswith(DONE_SECTION):
        return TICK_DONE
    return TICK_NONE if any(name.startswith(end) for end in RECORD_SECTIONS) else TICK_TODO


def is_empty_done(sec: Section) -> bool:
    """줄이 없거나 「없음」 한 줄뿐인 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」 — 창에 안 세운다(보고 글에는 그대로 남아 다음 보고가 잇는다)."""
    if not (sec.title and plain(sec.title).strip().startswith((DONE_SECTION, REOPEN_SECTION))):
        return False
    words: list[str] = []
    for b in sec.blocks:
        if b.kind == "list":
            words += [w for i in b.lines for w in (i.text, *i.subs)]
        else:
            words += [*b.lines, *b.label, *b.after]
    return all(NONE_LINE.match(w.strip()) for w in words)


def page_script() -> tuple[str, str]:
    """창에 싣는 스크립트와 그것만 여는 CSP 칸(`'sha256-…'`). 해시는 실을 글 그대로에서 낸다 — 손으로 옮긴 해시는 없다."""
    code = string.Template(SCRIPT.read_text(encoding="utf-8")).substitute(done_prefix=DONE_PREFIX, via_edge=VIA_EDGE, times_key=TIMES_KEY,
                                                                          unquiet_prefix=UNQUIET_PREFIX, state_key=STATE_KEY)
    digest = base64.b64encode(hashlib.sha256(code.encode("utf-8")).digest()).decode("ascii")
    return code, f"'sha256-{digest}'"


def people_panel(ink: Ink) -> str:
    """사람별 — 같은 줄들을 사람으로 한 번 더 세운다: 나를 기다리는 분(`WAIT_ME`) · 내가 답을 기다리는 분(`WAIT_THEM`). 사람마다 그 일들로
    가는 닻 링크다. 사람을 댄 줄이 없으면 빈 글 — 새로 읽는 것도 더하는 글도 없다."""
    if not ink.waits:
        return ""
    cols = []
    for label, head, sub in ((WAIT_ME, "나를 기다리는 분", "그분께 내가 할 차례인 일"), (WAIT_THEM, "내가 기다리는 분", "그분의 답이 와야 나아가는 일")):
        people: dict[str, list[tuple[str, str, str]]] = {}
        for kind, who, anchor, title, over in ink.waits:
            if kind == label and (anchor, title, over) not in people.setdefault(who, []):
                people[who].append((anchor, title, over))
        rows = "".join(f'<li><span class="who">{html.escape(who)}</span><span class="cnt">{len(items)}</span><span class="what">'
                       + " · ".join(f'<span class="item" data-anchor="{a}"><a href="#{a}">{html.escape(t)}</a>'
                                    + (f' <span class="pill over">{html.escape(o)}</span>' if o else "") + "</span>" for a, t, o in items)
                       + "</span></li>" for who, items in people.items())
        cols.append(f'<div class="pcol"><h3>{head}</h3><p class="sub">{sub}</p>'
                    + (f"<ul>{rows}</ul>" if rows else '<p class="none">없습니다</p>') + "</div>")
    return '<div class="people" id="people" role="region" aria-label="사람별">' + "".join(cols) + "</div>"


def read_json(folder: pathlib.Path | None, where: tuple[str, str]) -> dict:
    try:
        data = json.loads((folder / pathlib.Path(*where)).read_text(encoding="utf-8")) if folder else None
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def schedule_of(folder: pathlib.Path | None) -> tuple[list[str] | None, bool, str]:
    """(걸린 보고 시각표, 스스로 로그인, 건 때) — 안 걸렸거나 못 읽으면 (None, False, ""). 시각 하나를 쓰던 꼴(`at`)도 읽는다."""
    data = read_json(folder, SCAN_BRIEF)
    raw = (data.get("times") or [data.get("at")])
    times = sorted({t for t in raw if isinstance(t, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", t)})
    return (times or None), bool(data.get("login")), str(data.get("set") or "")


LINK = re.compile(r"\s*\[[^\]\n]*\]\(mail:[^)\s]*\)")


def state_of(folder: pathlib.Path | None) -> dict:
    """창이 보이는 지금 모습 — 사용자 폴더의 두 파일(보고 시각표 · 보고 맞춤 파일)에서 끌어낸다. 규칙의 수(`room` · `wait`)는 시각표를 건
    스캔이 그 파일에 함께 적은 것이다(원본은 스킬 mailbox-scan 의 `scan_const`) — 창은 그 수로 더하실 시각을 바로 재고, 수가 없으면 비서가
    받을 때 잰다. 줄의 글은 링크를 걷은 맨글자이고 메일 번호는 따로 든다 — 창의 스크립트가 글자로만 세우고 링크는 번호에서만 짓는다."""
    times, login, set_at = schedule_of(folder)
    data = read_json(folder, SCAN_BRIEF)
    prefs = P.read(folder) if folder else P.Prefs()

    def number(name: str) -> int | None:
        value = data.get(name)
        return value if isinstance(value, int) and 0 < value < 24 * 60 else None

    def row(line: str) -> dict:
        return {"key": P.key(line), "unid": P.unid_of(line) or "", "words": plain(LINK.sub("", line[2:])).strip(),
                "due": (P.due_of(line).isoformat() if P.due_of(line) else "")}
    return {"times": times or [], "set": set_at, "login": login, "room": number("room_min"), "wait": number("wait_min"),
            "seen": str((read_json(folder, SCAN_STATE).get("last_run") or {}).get("started") or ""),
            "quiet": [row(x) for x in prefs.quiet], "later": [row(x) for x in prefs.later],
            "at": dt.datetime.now().astimezone().isoformat(timespec="seconds")}


def now_words(iso: str) -> str:
    """「M/D HH:MM」 — 창이 보이는 모습이 언제 것인가."""
    try:
        at = dt.datetime.fromisoformat(iso)
    except ValueError:
        return "이 보고를 지을 때"
    return f"{at.month}/{at.day} {at:%H:%M}"


def prefs_panel(folder: pathlib.Path | None, ink: Ink) -> str:
    """보고 맞추기 — 보고 시각(고르시면 스캔이 받아 건다) · 올리지 않기로 한 것(「다시 올리기」) · 내일 다시 볼 것. 고르는 칸은 처음엔 숨고
    창의 스크립트가 표시를 거둘 수 있는 창에서만 꺼낸다 — 아닌 창은 지금 값만 보인다."""
    state = state_of(folder)
    times, login = state["times"] or None, state["login"]
    prefs = P.read(folder) if folder else P.Prefs()
    if times is None:
        when = '<p class="pref-none" id="times-none">사람 없는 보고가 걸려 있지 않습니다 — 대화에서 「보고 시각 걸어 줘」 하시면 겁니다.</p>'
    else:
        chips = "".join(f'<span class="chip" data-time="{t}">{t}<button type="button" class="chip-x" data-drop="{t}" hidden '
                        f'aria-label="{t} 빼기">빼기</button></span>' for t in times)
        first = " 첫 시각의 보고만 스스로 로그인합니다." if login else ""
        when = (f'<div class="chips" id="times" data-times="{" ".join(times)}">{chips}'
                '<span class="add-time" hidden><input type="time" id="time-new" aria-label="더할 시각"><button type="button" class="btn ghost" '
                'id="time-add">더하기</button></span><button type="button" class="btn" id="times-save" hidden>이대로 바꾸기</button></div>'
                f'<p class="note">시각마다 다음 시각까지 사내 로그인을 기다려 한 번 띄웁니다.{first}</p>'
                '<p class="note times-said" id="times-said" aria-live="polite"></p>')
    quiet = "".join(f'<li data-key="{P.key(line)}"><span>{ink.inline(line[2:])}</span><button type="button" class="undo" '
                    f'data-key="{P.key(line)}" hidden>다시 올리기</button><span class="undo-note" aria-live="polite"></span></li>'
                    for line in prefs.quiet)
    later = "".join(f'<li data-key="{P.key(line)}"><span>{ink.inline(line[2:])}</span></li>' for line in prefs.later)
    href = html.escape(MAIL_URL.format(mailbox=ink.mailbox, unid="UNID"), quote=True) if ink.mailbox else ""
    asof = f"{now_words(state['at'])} 기준입니다 — 그 뒤 대화에서 바꾸신 것은 메일 비서의 Edge 로 연 창에 바로 보입니다"
    return (f'<aside class="prefs" id="prefs" aria-labelledby="h-prefs" data-state="{html.escape(json.dumps(state, ensure_ascii=False), quote=True)}" '
            f'data-mail-href="{href}"><h2 id="h-prefs">보고 맞추기</h2>'
            '<p class="hint" id="prefs-hint" hidden>여기서 고르신 것은 비서가 받아 다음 보고부터 따릅니다. 대화에서 말씀하셔도 같습니다.</p>'
            f'<p class="note" id="prefs-asof">{html.escape(asof)}</p>'
            f'<h3>보고 시각</h3>{when}'
            f'<h3>올리지 않기로 한 것</h3><ul class="pref-list" id="quiet-list">{quiet}</ul>'
            + f'<p class="pref-none" id="quiet-none"{" hidden" if quiet else ""}>없습니다</p>'
            + f'<h3 id="later-head"{"" if later else " hidden"}>내일 다시 볼 것</h3><ul class="pref-list" id="later-list">{later}</ul>'
            + '<p class="tick-off" id="prefs-off">이 창에서는 고르실 수 없습니다 — 대화에서 말씀해 주세요.</p></aside>')


def build(rep: Report, ink: Ink, now: dt.datetime, folder: pathlib.Path | None = None) -> tuple[str, int, int]:
    """틀에 채운 HTML · 절 수 · 줄 수."""
    template = string.Template(TEMPLATE.read_text(encoding="utf-8"))
    toc: list[str] = []
    title = rep.title or ""
    head_blocks = list(rep.sections[0].blocks)
    hero = [f"<h1>{ink.inline(title)}</h1>"]
    if head_blocks and head_blocks[0].kind == "para":
        hero.append(f'<p class="lede">{ink.inline(" ".join(head_blocks.pop(0).lines))}</p>')
    made = now.astimezone().isoformat(timespec="seconds")      # 창의 스크립트가 이보다 먼저 거둔 표시를 이 창에서 안 쓴다(report.js)
    hero.append(f'<p class="dateline" data-made="{made}">{DATELINE.format(now, WEEKDAYS[now.weekday()], now)}</p>')
    hero.append(render_blocks(head_blocks, ink, "s0", toc, head=True))
    sections, lines = [], sum(len(b.lines) for b in head_blocks if b.kind == "list")
    for n, sec in enumerate(rep.sections[1:], 1):
        if is_empty_done(sec):
            continue
        sid = f"s{n}"
        toc.append(f'<li><a href="#{sid}">{ink.inline(sec.title or "", links=False)}</a></li>')
        sub_toc: list[str] = []
        body = render_blocks(sec.blocks, ink, sid, sub_toc, head=False, tick=section_tick(sec.title))
        toc += sub_toc
        lines += sum(len(b.lines) for b in sec.blocks if b.kind == "list")
        sections.append(f'<section id="{sid}" aria-labelledby="h-{sid}"><h2 id="h-{sid}">{ink.inline(sec.title or "")}</h2>'
                        f"{body}</section>")
    if ink.boxes:
        hero.append(f'<p class="tick-off" id="tick-off" hidden>{html.escape(TICK_OFF)}</p>')
    people = people_panel(ink)
    if people:
        hero.append(people)
        toc.insert(1 if toc and toc[0].startswith('<li><a href="#top">') else 0, '<li><a href="#people">사람별</a></li>')
    sections.append(prefs_panel(folder, ink))
    toc.append('<li><a href="#prefs">보고 맞추기</a></li>')
    code, script_hash = page_script()
    page = template.substitute(
        page_title=html.escape(plain(title), quote=True),
        side_title=ink.inline(title, links=False),
        toc="\n".join(toc),
        hero="\n".join(hero),
        sections="\n".join(sections),
        script=code,
        script_hash=script_hash,
    )
    return page, len(sections) - 1, lines


# ── 들고 나기 ─────────────────────────────────────────────────────────────

def decode(raw: bytes) -> str:
    """받은 바이트 → 글. BOM 이 있으면 그 꼴(UTF-8 · UTF-16 — Windows PowerShell 의 `>` 가 쓰는 꼴), 없으면 UTF-8, 안 되면 cp949.
    같은 몸이 스킬 mailbox-work 의 `work.py` · mailbox-tidy 의 `journal.py` 에 있다 — 고치면 셋을 함께 고친다(머리말의 받는 꼴이 같다)."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", errors="replace")


def mailbox_of(raw: str | None) -> str | None:
    """꼴에 맞는 메일함 주소(끝의 / 를 뗀 것) — 없거나 꼴이 아니면 None."""
    url = (raw or "").strip().rstrip("/")
    return url if MAILBOX.match(url) else None


def missing_ends(rep: Report) -> list[str]:
    """글에 없는 끝의 절 — 절(##)이나 작은 절(###)의 머리가 그 이름으로 시작하면 있는 것으로 본다(「(2건)」 같은 덧말 · 굵게는 괜찮다)."""
    heads = [s.title for s in rep.sections[1:] if s.title]
    heads += [b.lines[0] for s in rep.sections for b in s.blocks if b.kind == "sub"]
    named = [plain(h).strip() for h in heads]
    return [end for end in END_SECTIONS if not any(h.startswith(end) for h in named)]


def kept_briefs(folder: pathlib.Path) -> list[pathlib.Path]:
    """폴더에 남은 보고 글 — 이름이 `FILE_NAME` 꼴(.md)인 것만, 이름 차례(곧 지은 때의 차례)로."""
    shape = FILE_NAME.replace("{:", "").replace("}", "").removesuffix(".html") + ".md"
    out = []
    for f in folder.glob("brief-*.md"):
        try:
            dt.datetime.strptime(f.name, shape)
        except ValueError:
            continue
        out.append(f)
    return sorted(out, key=lambda f: f.name)


def open_report(uri: str) -> str:
    """보고 창을 로그인 Edge 의 새 탭에, 안 되면 기본 브라우저로 띄우고 어디에 띄웠나를 한 줄로 낸다.
    로그인 Edge 가 먼저다 — 메일 링크가 같은 세션에서 열려야 로그인 창이 안 뜬다. 그 Edge 로 연 창만 주소 꼬리(`VIA_EDGE`)를 달아,
    누르신 표시가 거둬지는 창에서만 단추가 선다."""
    port = (os.environ.get("EDGE_DEBUG_PORT", "").split(",")[0]).strip()
    port = port if port.isdigit() and 0 < int(port) < 65536 else EDGE_PORT_DEFAULT
    try:
        conn = http.client.HTTPConnection(EDGE_HOST, int(port), timeout=EDGE_TIMEOUT_S)
        try:
            conn.request("PUT", "/json/new?" + uri + "?" + VIA_EDGE)   # 새 Chromium 은 PUT 만 받는다
            ok = conn.getresponse().status == 200
        finally:
            conn.close()
        if ok:
            return "띄웠다(로그인된 Edge 의 새 탭)"
    except (OSError, http.client.HTTPException, ValueError):
        pass
    if webbrowser.open(uri):
        return "띄웠다(기본 브라우저 — 메일 링크가 로그인을 물을 수 있다)"
    return "못 띄웠다 — 이 파일을 사용자께 알려 드린다"


class Once(argparse.Action):
    """두 번째로 오면 인자 오류(종료 2)로 멈춘다 — 줄인 이름(`--di`)이나 `--dir=…` 꼴로 와도 같은 칸이라 함께 걸린다."""

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            parser.error(f"{option_string} 는 한 번만 준다")
        setattr(namespace, self.dest, values)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="보고 글(md)을 보고 창의 틀에 채워 그날의 HTML 로 남기고, 그 글을 곁에 같은 이름의 .md 로 남기고, "
                                             "띄운다. 글의 꼴은 스킬 폴더의 lane.md 「보고 글의 꼴」 · 「남긴다」가 든다.")
    ap.add_argument("--dir", required=True, action=Once, help="그날의 HTML 과 보고 글을 남길 폴더 — 업무 파일(work.md)이 있는 사용자 폴더(한 번만)")
    ap.add_argument("--mailbox", default="", help="회사 메일 스킬 session 이 낸 메일함 주소 http(s)://<호스트>/…/<이름>.nsf")
    ap.add_argument("--in", dest="src", default="", help="보고 글 파일 — 없으면 표준 입력")
    ap.add_argument("--no-open", action="store_true", help="짓기만 하고 브라우저로 띄우지 않는다")
    args = ap.parse_args(argv)

    try:
        data = pathlib.Path(args.src).read_bytes() if args.src else sys.stdin.buffer.read()
    except OSError as exc:
        print(f"보고 글을 못 읽었다({args.src}: {exc}). 다음: 보고 글 파일의 자리를 확인하고 다시 부른다")
        return EXIT_FAIL
    text = decode(data)
    rep = parse(text)
    if not rep.title:
        print("보고 창을 짓지 않았다 — 보고 글에 제목(맨 위 「# …」 한 줄)이 없다. 다음: 제목 줄을 더해 다시 부른다")
        return EXIT_FAIL
    folder = pathlib.Path(args.dir)
    if not folder.is_dir():
        print(f"보고 창을 짓지 않았다 — 폴더가 없다: {folder}. 다음: 업무 파일(work.md)이 있는 사용자 폴더를 --dir 로 준다")
        return EXIT_FAIL

    mailbox = mailbox_of(args.mailbox)
    ink = Ink(mailbox)
    now = dt.datetime.now()
    page, sections, lines = build(rep, ink, now, folder)
    out = folder / FILE_NAME.format(now)
    kept = out.with_suffix(".md")
    try:
        out.write_text(page, encoding="utf-8", newline="\n")
    except OSError as exc:
        print(f"보고 창을 못 썼다({out}: {exc}). 다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다")
        return EXIT_FAIL
    try:                                           # 창이 선 뒤에만 — 남은 글은 다음 보고가 사용자께 낸 보고로 읽는다
        kept.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\n")
    except OSError as exc:
        print(f"보고 창은 지었지만 보고 글을 못 남겼다({kept}: {exc}) — 다음 보고는 이 보고를 모른 채 그 앞 보고에서 잇는다. "
              "다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다")
        return EXIT_FAIL

    ends = missing_ends(rep)
    if rep.extra_titles:
        print(f"경고: 제목(# …)이 {rep.extra_titles + 1}개라 둘째부터는 절로 세웠다")
    if sections == 0:
        print("경고: 절(## …)이 하나도 없다 — 왼쪽 절 목록이 빈다")
    if ink.bad_refs:
        print(f"경고: 메일 번호(32자리)가 아닌 mail: 링크 {ink.bad_refs}개는 쓴 그대로 글자로 두었다")
    urls = len(URLISH.findall(text))
    if urls:
        print(f"알림: 글에 쓴 주소 {urls}개는 링크로 짓지 않고 글자로 두었다 — 링크는 메일 번호에서만 선다")
    for end in ends:
        print(f"경고: 끝에 「{end}」 절이 없다 — 다음 보고는 남은 이 글만 읽고 잇는다")
    shown = "띄우지 않았다(--no-open)" if args.no_open else open_report(out.resolve().as_uri())
    print(f"보고 창을 지었다: {out} · 남긴 보고 글: {kept} — 절 {sections} · 줄 {lines} · 메일 링크 {ink.links} · {shown}")
    if ends:
        print(f"다음: 남긴 보고 글 끝에 {' · '.join(f'「## {e}」' for e in ends)} 절을 더한다(파일을 쓸 도구가 없는 실행이면 그 절을 넣은 글로 다시 부른다) — 다음 보고가 그 글에서 어디부터 읽을지와 "
              "다시 올리지 않을 것을 찾는다")
    if ink.unlinked:
        why = "메일함 주소가 없어" if not args.mailbox.strip() else "메일함 주소가 꼴(http(s)://<호스트>/…/<이름>.nsf)에 안 맞아"
        print(f"다음: {why} 메일 {ink.unlinked}곳을 링크 없이 번호로 세웠다 — 회사 메일 스킬의 session 이 낸 메일함 주소를 --mailbox 로 주고 "
              "다시 부른다")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
