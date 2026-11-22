"""보고 글의 꼴을 읽고 고친다 — 글 → 제목 · 절 · 덩이(`parse`) · 맡길 일(`Task` · `tasks_of`) · 넣을 일정(`Put` · `cards_of`) · 사람
(`people_in`), 기록 절에 줄 더하기(`fold`), 보고 글 · 창 파일의 이름에서 지은 때(`made_of` · `kept_briefs`). 파일을 읽지 않고(이름만 본다)
망에 닿지 않는다. 꼴의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」이다.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import pathlib
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_const.py — `-I` 로 돌아도 싣는다
from brief_const import (FILE_NAME, KIND_CAL, KIND_FIND, KIND_MAIL, KIND_REPLY, KIND_ROOM, KIND_TEAMS,  # noqa: E402
                         WEEKDAYS)

# 끝의 두 절 — 다음 보고가 남은 글에서 어디부터 읽을지와 다시 올리지 않을 것을 찾는 자리(`lane.md` 「남긴다」). 머리가 이 말로 시작하면 그 절이다
END_SECTIONS = ("이 보고가 본 데", "끝났다고 하신 것")
DONE_SECTION = END_SECTIONS[1]
# 끝나지 않았다고 되돌리신 일 — 있을 때만 서는 끝의 절. 다음 업무 파악이 이 절로 「끝난 일」에서 그 일을 다시 연다
REOPEN_SECTION = "안 끝났다고 하신 것"
RECORD_SECTIONS = (*END_SECTIONS, REOPEN_SECTION)   # 다음 보고의 기록인 절 — 「끝났음」 상자는 「끝났다고 하신 것」에만 선다
NONE_LINE = re.compile(r"^(?:[-*+]\s*)?(?:없음|없습니다|없다)\s*\.?$")   # 줄 대신 쓴 「없음」 — 이 줄뿐인 「끝났다고 하신 것」은 창에 안 세운다
NONE_ROW = "- 없음"                                                  # 줄이 없는 절에 손이 세우는 한 줄(`NONE_LINE` 이 읽는다)

# 일정에 없는 약속 — 카드 끝의 칸(`lane.md` 「보고 글의 꼴」). 「일정 넣기」 · 옛 「넣을 일정」의 값은 일정 손 preview 답의 값을 손대지 않고
# 옮긴 것이고, 열쇠는 창을 지을 때 스크립트가 그 값의 미리 보기에서 받아 붙인다(`finish.py`):
#   <start> | <end> | <title> | 곳 <place> | <visibility> [| 열쇠 <key>]   (곳은 없으면 뺀다)
PUT_FIELD = "넣을 일정"
NO_TIME_FIELD, NO_TIME_VALUE = "시각", "메일에 없음"   # 날은 있고 시각이 없는 모임 — 단추 대신 대화로 가는 말을 단다
PUT_SPLIT, PLACE_MARK, KEY_MARK = " | ", "곳 ", "열쇠 "
VISIBILITY = {"public": False, "공개": False, "private": True, "비공개": True}   # preview 의 visibility(앞) · 사람 말(뒤) → 비공개인가
PUT_KEY = re.compile(r"^[0-9a-f]{8,64}$")      # 일정 손의 key(판의 해시 · 16진) — 길이는 그 손이 정한다
PUT_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2} (?:[01]\d|2[0-3]):[0-5]\d$")   # 일정 손의 시각 꼴(서울 벽시계)
VIS_WORDS = {False: "공개 — 다른 분이 제목을 볼 수 있습니다", True: "비공개 — 다른 분께는 바쁜 때로만 보입니다"}
# 맡길 일 — 카드의 낱낱 가운데 이 두 이름의 칸(`lane.md` 「보고 글의 꼴」). 무엇을 · 어느 갈래로 맡길지는 보고를 짓는 모델이 적고, 창은 적힌
# 것을 보이고 누름을 남길 뿐이다 — 종류를 짐작하거나 꼴이 틀린 줄을 고쳐 읽지 않는다. 옛 「넣을 일정」 칸은 「일정 넣기」 한 줄로 읽는다
DO_FIELD, TALK_FIELD = "바로 할 일", "대화로 할 일"
TASK_FIELDS = (DO_FIELD, TALK_FIELD, PUT_FIELD)
TOP_MARK = "추천"                               # 「대화로 할 일」 하나에 붙여 창 머리의 칸에 미리 세운다 — 보고 하나에 하나까지
TALK_KIND = "같이 의논"                         # 「대화로 할 일」 줄의 표지
ATTEND_MARK, NOTE_MARK, MAIL_MARK = "참석 ", "안내 ", "메일 "
# 맡긴 일의 값의 이름 — 뒤의 실행이 받는 카드 줄 끝에 「이름: 값」으로 선다(`Task.values`)
VALUE_WHEN, VALUE_ROOM, VALUE_TITLE, VALUE_ATTEND, VALUE_NOTE = "때", "방", "제목", "참석", "안내"
VALUE_TO, VALUE_MAIL, VALUE_SAY, VALUE_WHAT = "받는 분", "답할 메일", "할 말", "찾을 것"
# 종류마다 창이 드는 말 — (막대의 짧은 이름, 누르면 무엇이 되나, 끝났을 때 카드의 머리, 그 뒤의 덧말). 같은 종류는 어느 카드에서나 같은 말이다
KINDS = {
    KIND_FIND: ("찾아 정리", "메일을 읽기만 합니다", "찾아 정리했습니다", ""),
    KIND_REPLY: ("답장", "임시보관함에 두고 그 화면을 Edge 에 띄웁니다 — 보내기는 직접 누르십니다", "답장을 써 두었습니다", " — 아직 안 나갔습니다"),
    KIND_MAIL: ("새 메일", "임시보관함에 두고 그 화면을 Edge 에 띄웁니다 — 보내기는 직접 누르십니다", "새 메일을 써 두었습니다", " — 아직 안 나갔습니다"),
    KIND_ROOM: ("회의실", "{who}께 회의 안내 메일이 회사 메일로 가고, 내 일정에는 「[회의실 예약] {title}」{ro} 저절로 듭니다", "회의실을 잡았습니다", ""),
    KIND_TEAMS: ("Teams 회의", "제목 · 때 · 참석자를 채운 Teams 회의 예약 창을 띄웁니다 — [보내기]는 Teams 에서 직접 누르시고, 보내셔야 회의가 "
                               "잡혀 초대가 가고 내 일정에 보입니다", "Teams 회의 예약 창을 띄웠습니다", " — 보내셔야 잡힙니다"),
    KIND_CAL: ("일정", "내 일정함에만 넣습니다 — 아무에게도 알림이 안 갑니다", "내 일정함에 넣었습니다", ""),
}
COUNT_WORDS = ("", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열")   # 「두 분」 — 열을 넘으면 숫자로
TASK_ID_LEN = 12                               # 일의 번호 — 카드 머리 · 칸의 차례 · 칸의 글에서 낸 해시의 앞
# 절의 종류 — 머리가 링크 하나인 절: 「## [사람이 읽는 절 이름](section:<종류>)」. 이름은 모델이 그날 맞게 쓰고, 창은 종류만 읽는다
SECTION_HEAD = re.compile(r"^\[(?P<name>(?:[^\[\]\n]|\[[^\[\]\n]*\])+)\]\(section:(?P<kind>[a-z]+)\)$")
# 회의 한 장의 절 — 회의는 일이 아니라 이 절의 카드에는 누름 단추를 안 단다(그 안의 답 안 한 요청은 제 카드에서 누른다). 이름 글자로 읽는
# `MEETING_SECTION` 은 종류 표지 없이 쓴 글(표지 전의 보고 글)을 위한 것이다
MEETINGS = "meetings"
MEETING_SECTION = "오늘 · 내일 회의"
# 카드 · 줄이 어느 일인가 — 이 이름의 칸에 단 메일 링크가 누름 단추의 열쇠다(업무 파일이 그 일을 연 메일). 칸이 없으면 줄의 첫 메일 링크다
WORK_FIELD = "일"
# 사람 — 메일 링크처럼 링크 하나가 한 분이다: 「[이름 직함](person:<주소>)」(`lane.md` 「보고 글의 꼴」). 글은 사람이 읽는 이름, 주소는 회사
# 손이 낸 그분의 주소(메일 머리 · 주소록 그대로)라 사람을 가르는 열쇠다. 사람을 대는 칸은 이 링크들을 「 · 」로 잇고, 링크 바로 뒤 괄호가 그분의
# 덧말이다. 꼴이 아닌 칸은 쓴 글로만 서고 사람으로 안 센다 — 글을 갈라 사람을 짐작하지 않는다
PERSON_ENTRY = re.compile(r"\[(?P<name>(?:[^\[\]\n]|\[[^\[\]\n]*\])+)\]\(person:(?P<addr>[^()\n]*)\)(?:\s*\((?P<note>[^()\n]*)\))?")
PERSON_SEP = re.compile(r"\s*(?:·|,|、)\s*")
PERSON_ADDR = re.compile(r'^[^\s<>"`](?:[^<>"`\n]*[^\s<>"`])?$')   # 주소의 꼴 — 빈 글 · 앞뒤 빈칸 · 꺾쇠 · 따옴표가 없다(메일 주소 · Notes 이름)
PILLS = re.compile(r"\{!?[^{}\n]*\}")                              # 칸 끝에 붙는 표지 — 사람의 꼴을 잴 때 걷는다
# 회의실 — 사람처럼 링크 하나가 한 방이다: 「[방 이름(정원)](room:<회의실 손 free 의 id>)」. 글은 사람이 읽는 방, id 는 회의실 손이 잡을 때 받는 열쇠다
ROOM_CELL = re.compile(r"^\[(?P<name>(?:[^\[\]\n]|\[[^\[\]\n]*\])+)\]\(room:(?P<id>[A-Za-z0-9][A-Za-z0-9._:-]{0,99})\)$")
# 사람별 — 줄 끝의 칸 가운데 이 두 이름이 사람을 댄다. 사람별은 주소로 묶는다 — 같은 분이 다른 글(직함 · 덧말)로 적혀도 한 줄이다
WAIT_ME, WAIT_THEM = "기다리는 분", "답 주실 분"
OVER = re.compile(r"\{!([^{}\n]{1,40})\}")         # 붉은 표지(기한 지남) — 사람별의 그 일 곁에도 단다
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
    r"|\[(?P<plabel>(?:[^\[\]\n]|\[[^\[\]\n]*\])+)\]\(person:(?P<pref>[^()\n]*)\)"
    r"|\[(?P<rlabel>(?:[^\[\]\n]|\[[^\[\]\n]*\])+)\]\(room:(?P<rref>[^()\s]*)\)"
    r"|\[(?P<slabel>(?:[^\[\]\n]|\[[^\[\]\n]*\])+)\]\(section:(?P<sref>[a-z]+)\)"
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


# ── 일정에 없는 약속 — 카드의 「넣을 일정」 칸 ─────────────────────────────────

@dataclass(frozen=True)
class Put:
    """카드 하나가 넣을 일정 — 창이 사람에게 보이는 글과 거두는 손이 일정 손에 주는 값이 다 이것에서 나온다."""
    start: str
    end: str
    title: str
    place: str
    private: bool
    key: str

    def words(self) -> str:
        """사람이 읽는 「무엇을 넣나」 — 날 · 요일 · 시각 · 제목 · 곳. 공개 범위는 따로(`VIS_WORDS`)."""
        return " · ".join(filter(None, (span_words(self.start, self.end), self.title, self.place)))


def span_words(start: str, end: str) -> str:
    """「11월 26일(목) 14:00–16:00」 — 서울 벽시계 두 시각(`PUT_STAMP` 꼴)을 사람이 읽는 때로. 날을 넘기면 끝의 날도 댄다."""
    a, b = (dt.datetime.strptime(s, "%Y-%m-%d %H:%M") for s in (start, end))
    day = f"{a.month}월 {a.day}일({WEEKDAYS[a.weekday()]})"
    return (f"{day} {a:%H:%M}–{b:%H:%M}" if a.date() == b.date()
            else f"{day} {a:%H:%M} – {b.month}월 {b.day}일({WEEKDAYS[b.weekday()]}) {b:%H:%M}")


def put_of(value: str) -> Put | None:
    """「일정 넣기」 칸의 값 → Put. 꼴이 아니면 None — 시각 둘 · 제목 · (곳) · 공개 범위 · (열쇠). 제목에 「 | 」가 들어도 끝에서부터 읽는다.
    열쇠는 창을 지을 때 일정 손의 미리 보기에서 받아 붙인다(`finish.py`) — 모델이 쓴 글에는 없고, 붙이기 전이나 못 받았으면 빈 글이다."""
    parts = [p.strip() for p in value.strip().strip("`").split(PUT_SPLIT)]
    key = parts.pop()[len(KEY_MARK):].strip() if parts and parts[-1].startswith(KEY_MARK) else ""
    if len(parts) < 4 or parts[-1] not in VISIBILITY or (key and not PUT_KEY.match(key)):
        return None
    start, end, middle = parts[0], parts[1], parts[2:-1]
    place = middle.pop()[len(PLACE_MARK):].strip() if len(middle) > 1 and middle[-1].startswith(PLACE_MARK) else ""
    title = PUT_SPLIT.join(middle).strip()
    if not (PUT_STAMP.match(start) and PUT_STAMP.match(end) and start < end and title):
        return None
    return Put(start, end, title, place, VISIBILITY[parts[-1]], key)


def no_time_of(facts: list[tuple[str, str]]) -> tuple[bool, list[tuple[str, str]]]:
    """끝의 칸에서 「시각: 메일에 없음」을 떼어 낸다 — (시각 없는 모임인가, 남은 칸)."""
    hit = [f for f in facts if f[0] == NO_TIME_FIELD and plain(f[1]).strip().startswith(NO_TIME_VALUE)]
    return bool(hit), [f for f in facts if f not in hit]


# ── 맡길 일 — 카드의 「바로 할 일」 · 「대화로 할 일」 칸 ────────────────────────────

@dataclass(frozen=True)
class Task:
    """카드에 적힌 맡길 일 하나 — 창이 사람에게 보이는 줄과 창 곁의 손이 넘겨받는 일이 다 이것에서 나온다(`tasks_of`).
    `kind` 가 빈 글이면 꼴이 틀린 칸이다 — 그 줄은 적힌 글(`written`) 그대로 서고 맡길 수 없다."""
    id: str
    field: str                      # 칸 이름 — DO_FIELD · TALK_FIELD · PUT_FIELD(옛 꼴)
    kind: str                       # KINDS 의 하나 · TALK_KIND · ""(꼴이 틀렸다)
    parts: tuple[str, ...]          # 종류 뒤의 값 — 「 | 」로 가른 그대로
    written: str                    # 칸의 값 그대로
    card: str                       # 카드 제목(맨글자)
    num: str | None                 # 카드에 쓴 번호
    evidence: tuple[str, ...]       # 카드의 근거 — 머리 · 점 · 칸의 맨글자(메일 링크는 「글 (메일 번호 …)」 · 사람 링크는 「이름 <주소>」)
    put: Put | None = None          # 「일정 넣기」의 값 — 일정 손 미리 보기 답 그대로
    top: bool = False               # 「대화로 할 일」에 붙은 추천 표
    lines: tuple[str, ...] = ()     # 카드의 머리와 맡길 일 밖의 낱낱 — 보고 글에 적힌 그대로(메일 · 사람 링크가 든다)

    def people_cell(self) -> str:
        """사람을 대는 값 — 회의실 · Teams 회의는 「참석 」 칸의 값, 답장 · 새 메일은 받는 분. 없으면 빈 글. 적힌 그대로다(사람 링크가 든다)."""
        if self.kind in (KIND_ROOM, KIND_TEAMS):
            cell = next((p for p in self.parts if p.startswith(ATTEND_MARK)), "")
            return cell[len(ATTEND_MARK):].strip()
        return self.parts[0] if self.kind in (KIND_REPLY, KIND_MAIL) else ""

    def people(self) -> list[Person]:
        """그 일의 사람 — 참석자 · 받는 분. 꼴이 틀린 칸은 맡길 일이 아니라 빈 목록이다."""
        cell = self.people_cell()
        return (people_in(cell) or []) if cell else []

    def room(self) -> tuple[str, str] | None:
        """회의실 잡기의 방 — (사람이 읽는 방 이름, 회의실 손의 id). 꼴이 아니면 None."""
        m = ROOM_CELL.match(self.parts[2]) if self.kind == KIND_ROOM and len(self.parts) > 2 else None
        return (" ".join(plain(m.group("name")).split()), m.group("id")) if m else None

    def who(self) -> str:
        """사람이 읽는 사람들 — 「이름 직함(덧말) · …」."""
        return " · ".join(p.said() for p in self.people())

    def values(self) -> list[tuple[str, str]]:
        """그 일의 값 — 칸마다 (이름, 적힌 그대로의 값). 때는 해까지 든 서울 시각(사람이 읽는 줄은 「11월 19일(목)」로 해가 빠진다), 방 · 사람 ·
        답할 메일은 열쇠가 든 링크다. 종류의 칸이 다 든다 — 받는 쪽이 사람이 읽은 줄에서 값을 되살리거나 카드의 여러 메일 가운데 고르지 않게."""
        p, k = self.parts, self.kind
        if k == KIND_FIND:
            return [(VALUE_WHAT, p[0])]
        if k == KIND_REPLY:
            return [(VALUE_TO, p[0]), (VALUE_MAIL, f"[답할 메일](mail:{p[2][len(MAIL_MARK):].strip().upper()})"), (VALUE_SAY, p[1])]
        if k == KIND_MAIL:
            return [(VALUE_TO, p[0]), (VALUE_TITLE, p[1]), (VALUE_SAY, p[2])]
        when = (VALUE_WHEN, f"{p[0]} – {p[1]} (서울)") if k in (KIND_ROOM, KIND_TEAMS) else None
        if k == KIND_ROOM:
            return [when, (VALUE_ROOM, p[2]), (VALUE_TITLE, p[3]), (VALUE_ATTEND, p[4][len(ATTEND_MARK):].strip())]
        if k == KIND_TEAMS:
            return [when, (VALUE_TITLE, p[2]), (VALUE_ATTEND, p[3][len(ATTEND_MARK):].strip()),
                    *([(VALUE_NOTE, p[4][len(NOTE_MARK):].strip())] if len(p) > 4 else [])]
        return []                                  # 꼴이 틀린 칸 · 대화로 할 일 · 일정 넣기(넘기지 않는다)

    def run_lines(self) -> list[str]:
        """뒤에서 하는 실행에 줄 카드의 줄 — 보고 글에 적힌 그대로의 머리 · 낱낱 뒤에 그 일의 값(`values`)을 「이름: 값」 한 줄씩. 실행이 방과
        사람을 다시 찾지 않고, 답할 메일을 카드의 근거 메일 가운데서 짐작하지 않는다."""
        return [*self.lines, *(f"{name}: {value}" for name, value in self.values())]

    def start(self) -> str:
        """시작 시각(서울 벽시계) — 때가 없는 일이면 빈 글."""
        if self.put:
            return self.put.start
        return self.parts[0] if self.kind in (KIND_ROOM, KIND_TEAMS) else ""

    def line(self) -> str:
        """사람이 읽는 「무엇을 하나」 — 누르시면 이 줄의 값 그대로 끝까지 한다."""
        p = self.parts
        if self.kind == KIND_FIND:
            return p[0]
        if self.kind == KIND_REPLY:
            return f"{self.who()}께 — {p[1]}"
        if self.kind == KIND_MAIL:
            return f"{self.who()}께 「{p[1]}」 — {p[2]}"
        if self.kind == KIND_ROOM:
            return " · ".join((span_words(p[0], p[1]), (self.room() or (p[2], ""))[0], f"「{p[3]}」", ATTEND_MARK + self.who()))
        if self.kind == KIND_TEAMS:
            note = [f"안내 「{p[4][len(NOTE_MARK):].strip()}」"] if len(p) > 4 else []
            return " · ".join((span_words(p[0], p[1]), f"「{p[2]}」", ATTEND_MARK + self.who(), *note))
        if self.kind == KIND_CAL and self.put:
            return f"{self.put.words()} · {VIS_WORDS[self.put.private]}"
        return p[0] if self.kind == TALK_KIND else self.written

    def cons(self) -> str:
        """누르시면 무엇이 되나 — 종류가 정한다(회의실은 안내 메일이 갈 분의 수와 일정에 들 제목만 채운다)."""
        if self.kind not in KINDS:
            return ""
        text = KINDS[self.kind][1]
        if self.kind == KIND_ROOM:
            title = f"[회의실 예약] {self.parts[3]}"
            text = text.format(who=count_words(len(self.people())) + " 분", title=self.parts[3], ro=ro(title))
        return text

    def words(self) -> str:
        """「대화로 열기」가 VS Code 의 입력 칸에 채울 말 — 줄 · 빈 줄 · 카드의 근거. 창 곁의 손이 그 뒤에 보고 이름과 경로를 붙인다."""
        return "\n".join((self.line(), "", *self.evidence))


def count_words(n: int) -> str:
    return COUNT_WORDS[n] if 0 < n < len(COUNT_WORDS) else str(n)


def ro(word: str) -> str:
    """조사 「(으)로」 — 끝 글자에 받침이 있으면(ㄹ 받침은 빼고) 「으로」. 한글이 아니면 「(으)로」."""
    last = word.rstrip("」』)] ")[-1:] or "x"
    if not "가" <= last <= "힣":
        return "(으)로"
    jong = (ord(last) - ord("가")) % 28
    return "로" if jong in (0, 8) else "으로"


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


def check_parts(kind: str, p: list[str]) -> bool:
    """종류마다 값의 꼴 — 맞으면 참. 고쳐 읽지 않는다: 칸이 모자라거나 넘치거나 시각 · 메일 번호의 꼴이 틀리면 거짓이다."""
    def span(a: str, b: str) -> bool:
        return bool(PUT_STAMP.match(a) and PUT_STAMP.match(b) and a < b)

    def attend(cell: str) -> bool:
        return cell.startswith(ATTEND_MARK) and bool(people_in(cell[len(ATTEND_MARK):]))
    if not all(p):
        return False
    if kind == KIND_FIND:
        return len(p) == 1
    if kind == KIND_REPLY:
        return len(p) == 3 and bool(people_in(p[0])) and p[2].startswith(MAIL_MARK) and bool(UNID.match(p[2][len(MAIL_MARK):].strip()))
    if kind == KIND_MAIL:
        return len(p) == 3 and bool(people_in(p[0]))
    if kind == KIND_ROOM:
        return len(p) == 5 and span(p[0], p[1]) and bool(ROOM_CELL.match(p[2])) and attend(p[4])
    if kind == KIND_TEAMS:
        return len(p) in (4, 5) and span(p[0], p[1]) and attend(p[3]) and (len(p) == 4 or p[4].startswith(NOTE_MARK))
    return False


def task_of(field_name: str, value: str, tid: str, card: str, num: str | None, evidence: tuple[str, ...],
            lines: tuple[str, ...] = ()) -> Task:
    """칸 하나 → Task. 꼴이 틀리면 종류가 빈 Task 다."""
    written = value.strip().strip("`").strip()
    base = dict(id=tid, field=field_name, written=written, card=card, num=num, evidence=evidence, lines=lines)
    if field_name == PUT_FIELD:
        put = put_of(written)
        return Task(kind=KIND_CAL if put else "", parts=(written,), put=put, **base)
    parts = [x.strip() for x in written.split(PUT_SPLIT)]
    if field_name == TALK_FIELD:
        top = len(parts) > 1 and parts[-1] == TOP_MARK
        line = PUT_SPLIT.join(parts[:-1] if top else parts).strip()
        return Task(kind=TALK_KIND if line else "", parts=(line,), top=top, **base)
    kind, rest = parts[0], parts[1:]
    if kind == KIND_CAL:
        put = put_of(PUT_SPLIT.join(rest))
        return Task(kind=KIND_CAL if put else "", parts=tuple(rest), put=put, **base)
    return Task(kind=kind if kind in KINDS and check_parts(kind, rest) else "", parts=tuple(rest), **base)


def take_card(it: Item, seen: dict[str, int] | None = None) -> tuple[list[Task], list[str], list[tuple[str, str]], bool]:
    """줄의 낱낱을 가른다 — (맡길 일, 앞의 점, 끝의 칸, 시각 없는 모임인가). 맡길 일의 칸은 낱낱 어디에 있어도 떼어 낸다 — 점 사이에
    끼어도 글자로 남지 않게. 일의 번호는 카드 머리 · 칸의 차례 · 칸의 글에서 낸다 — 같은 보고 글이면 창과 창 곁의 손이 같은 번호를 낸다.
    `seen` 을 주면 한 보고 안에서 겹친 번호에 「-n」을 붙인다(같은 카드를 두 번 쓴 글)."""
    raw: list[tuple[str, str]] = []
    rest: list[str] = []
    for s in it.subs:
        m = FACT.match(s)
        if m and m.group("label").strip() in TASK_FIELDS:
            raw.append((m.group("label").strip(), m.group("value")))
        else:
            rest.append(s)
    points, facts = split_facts(rest)
    no_time, facts = no_time_of(facts)
    if not raw:
        return [], points, facts, no_time
    m = LEAD_BOLD.match(it.text)
    head, when = (m.group("head"), m.group("rest")) if m else (it.text, "")
    card = " ".join(plain(head).split())
    evidence = ((f"— 카드 「{card}」" + (f" — {with_numbers(when)}" if when.strip() else "")),
                *(f"· {with_numbers(x)}" for x in points), *(f"· {k}: {with_numbers(v)}" for k, v in facts))
    tasks = []
    for pos, (label, value) in enumerate(raw, 1):
        tid = hashlib.sha256(f"{plain(it.text)}\x1f{pos}\x1f{label}\x1f{value.strip()}".encode("utf-8")).hexdigest()[:TASK_ID_LEN]
        if seen is not None:
            seen[tid] = seen.get(tid, 0) + 1
            tid = tid if seen[tid] == 1 else f"{tid}-{seen[tid]}"
        tasks.append(task_of(label, value, tid, card, it.num, evidence, (it.text, *rest)))
    return tasks, points, facts, no_time


def report_items(rep: Report):
    """창에 서는 줄을 창이 세우는 차례로 — 빈 「끝났다고 하신 것」 절은 창처럼 건너뛴다."""
    for sec in rep.sections:
        if sec.title is not None and is_empty_done(sec):
            continue
        for b in sec.blocks:
            yield from (b.lines if b.kind == "list" else ())


def tasks_of(text: str) -> dict[str, Task]:
    """보고 글의 맡길 일 — {일의 번호: Task}. 창 곁의 손이 누름의 번호를 이 글의 카드에 대어 그 값과 근거로 한다 — 창이 사람에게 보인
    글과 같은 글이다. 꼴이 틀린 칸도 든다(종류가 빈 글 — 맡기지 않는다)."""
    seen: dict[str, int] = {}
    out: dict[str, Task] = {}
    for it in report_items(parse(text)):
        for t in take_card(it, seen)[0]:
            out[t.id] = t
    return out


def cards_of(text: str) -> dict[str, tuple[Put, str]]:
    """보고 글에서 「일정 넣기」를 든 카드 — {열쇠: (Put, 카드의 맨글자)}. 거두는 손이 누름을 이 글의 카드에 대어 그 값으로 넣는다 —
    창이 사람에게 보인 글과 같은 글이다. 옛 「넣을 일정」 칸도 같은 일로 읽는다."""
    out: dict[str, tuple[Put, str]] = {}
    for it in report_items(parse(text)):
        for t in take_card(it)[0]:
            if t.put and t.put.key and t.put.key not in out:
                out[t.put.key] = (t.put, plain(" ".join([it.text, *it.subs])))
    return out


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


def section_kind(title: str | None) -> str:
    """절 머리의 종류 — 머리 전체가 「[이름](section:<종류>)」 꼴이면 그 종류, 아니면 빈 글."""
    m = SECTION_HEAD.match((title or "").strip())
    return m.group("kind") if m else ""


def is_meetings(title: str | None) -> bool:
    """회의 한 장의 절인가 — 종류 표지(`MEETINGS`)가 든 머리, 표지 없이 쓴 글이면 이름이 `MEETING_SECTION` 으로 시작하는 머리."""
    return section_kind(title) == MEETINGS or plain(title or "").strip().startswith(MEETING_SECTION)


def item_key(it: Item) -> str | None:
    """줄 · 카드가 어느 일인가 — 누름 단추의 열쇠 메일 번호(대문자). 낱낱에 「일: <메일 링크>」 칸이 있으면 그 메일, 없으면 줄의 첫 메일
    링크(머리부터 낱낱 차례로). 메일 번호가 없으면 None."""
    for s in it.subs:
        m = FACT.match(s)
        if m and m.group("label").strip() == WORK_FIELD and first_unid(m.group("value")):
            return first_unid(m.group("value"))
    return next(filter(None, (first_unid(s) for s in [it.text, *it.subs])), None)


def item_title(it: Item) -> str:
    """줄의 일 이름 — 카드면 굵은 머리, 줄이면 맨글자의 줄표(「 — 」) 앞. 줄표 뒤는 형편 · 때 · 근거라 일 이름이 아니다."""
    m = LEAD_BOLD.match(it.text)
    title = " ".join(plain(m.group("head") if m else it.text).split())
    return title.split(" — ", 1)[0]


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


def missing_ends(rep: Report) -> list[str]:
    """글에 없는 끝의 절 — 절(##)이나 작은 절(###)의 머리가 그 이름으로 시작하면 있는 것으로 본다(「(2건)」 같은 덧말 · 굵게는 괜찮다)."""
    heads = [s.title for s in rep.sections[1:] if s.title]
    heads += [b.lines[0] for s in rep.sections for b in s.blocks if b.kind == "sub"]
    named = [plain(h).strip() for h in heads]
    return [end for end in END_SECTIONS if not any(h.startswith(end) for h in named)]


def made_of(name: str) -> dt.datetime | None:
    """보고 창(.html) · 보고 글(.md)의 이름에서 지은 때 — 이 PC 의 시각(`FILE_NAME` 이 그렇게 짓는다). 꼴이 아니면 None."""
    shape = FILE_NAME.replace("{:", "").replace("}", "").removesuffix(".html")
    for suffix in (".html", ".md"):
        try:
            return dt.datetime.strptime(name, shape + suffix)
        except ValueError:
            continue
    return None


def kept_briefs(folder: pathlib.Path) -> list[pathlib.Path]:
    """폴더에 남은 보고 글 — 이름이 `FILE_NAME` 꼴(.md)인 것만, 이름 차례(곧 지은 때의 차례)로."""
    return sorted((f for f in folder.glob("brief-*.md") if made_of(f.name)), key=lambda f: f.name)


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
        if start is None and len(head.group(1)) in (2, 3) and plain(head.group(2)).strip().startswith(name):
            start, level = i, len(head.group(1))
    return start, len(rows)


def section_rows(text: str, name: str) -> list[str]:
    """절 `name` 의 줄 — 빈 줄과 「없음」 줄을 뺀 그대로. 절이 없으면 빈 것."""
    rows = text.split("\n")
    start, end = section_span(rows, name)
    return [] if start is None else [r for r in rows[start + 1:end] if r.strip() and not NONE_LINE.match(r.strip())]


def fold(text: str, name: str, lines: list[str], drop: set[str] = frozenset()) -> tuple[str, set[str]]:
    """보고 글의 절 `name` 에서 첫 메일 번호가 `drop` 에 든 줄을 걷고 끝에 `lines` 를 더한 글과, 고치기 전 그 절 줄들의 첫 메일 번호.
    줄의 열쇠는 첫 메일 번호다(창의 상자와 같다) — 둘째부터의 번호는 근거일 뿐이라 그 번호의 표시가 이 줄을 건드리지 않는다.
    절이 없으면 더할 줄이 있을 때만 글 끝에 세운다. 줄을 더할 때 그 절의 「없음」 줄은 걷는다 — 남기면 「없음」과 일이 한 절에 함께 선다."""
    rows = text.split("\n")
    start, end = section_span(rows, name)
    if start is None:
        if not lines:
            return text, set()
        body = text.rstrip("\n")
        return f"{body}\n\n## {name}\n" + "\n".join(lines) + "\n", set()
    section = rows[start + 1:end]
    have = {k for k in map(first_unid, section) if k}
    if not lines and not (drop & have):
        return text, have
    kept = [r for r in section if not (lines and NONE_LINE.match(r.strip())) and first_unid(r) not in drop]
    while kept and not kept[-1].strip():
        kept.pop()
    tail = [""] if end < len(rows) else []
    new = rows[:start + 1] + kept + lines + tail + rows[end:]
    out = "\n".join(new)
    return (out if out.endswith("\n") else out + "\n"), have
