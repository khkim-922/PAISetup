"""맡길 일의 종류마다 한 줄 — 적는 칸 · 값의 차례 · 꼴 · 넘길 값 · 사람 칸 · 사람이 읽는 줄 · 무엇이 되나 · 시작 시각 · 창의 말 · 결과 이름표 ·
넘기는 길(`ROWS`). 맡길 일 읽기(`brief_tasks`)가 칸마다 그 줄을 골라 값을 한 번 이름 붙여 읽고(`Kind.read` → `Cells`) 셈해 두며, 창 그림 ·
메일 한 장 · 맡길 일 넘기기는 셈한 값만 읽는다 — 파이썬에서 종류로 갈래를 치는 자리는 이 표 밖에 없다. 밖에 남은 한 자리는 창의
스크립트(`assets/report.js`)다 — 끝난 Teams 회의 카드를 그 이름(`TEAMS.name`, 창을 지을 때 받는다)으로 모아 「보내셔야 잡힌다」를 덧붙인다.
그 밖의 새 종류는 이 표의 줄 하나다. 파일 · 망에 닿지 않는다. 종류의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」이다.
"""

from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 보고 글 읽기 — `-I` 로 돌아도 싣는다
from brief_inline import LABEL, UNID, plain  # noqa: E402
from brief_people import Person, people_in  # noqa: E402
from brief_put import PUT_STAMP, VIS_WORDS, Put, span_words  # noqa: E402

# 맡길 일의 칸 — 카드의 낱낱 가운데 이 이름의 칸(`lane.md` 「보고 글의 꼴」). 「바로 할 일」은 첫 값이 종류의 이름이고, 다른 칸은 칸 이름이
# 종류를 정해 칸 전체가 그 종류의 값이다(`FIELD_KINDS`). 옛 「넣을 일정」 칸은 「일정 넣기」 한 줄로 읽는다
DO_FIELD, TALK_FIELD = "바로 할 일", "대화로 할 일"
PUT_FIELD = "넣을 일정"
# 넘기는 길 — 뒤의 실행(같은 스킬 `unattended/handed.py`) · 제 누름(창 곁의 손이 일정 손으로) · VS Code 대화 · 맡길 수 없다(꼴이 틀린 칸)
VIA_RUN, VIA_PUT, VIA_TALK, VIA_NONE = "run", "put", "talk", ""
ATTEND_MARK, NOTE_MARK, MAIL_MARK = "참석 ", "안내 ", "메일 "
# 맡긴 일의 값의 이름 — 뒤의 실행이 받는 카드 줄 끝에 「이름: 값」으로 선다(`brief_tasks.Task.run_lines`)
VALUE_WHEN, VALUE_ROOM, VALUE_TITLE, VALUE_ATTEND, VALUE_NOTE = "때", "방", "제목", "참석", "안내"
VALUE_TO, VALUE_MAIL, VALUE_SAY, VALUE_WHAT = "받는 분", "답할 메일", "할 말", "찾을 것"
COUNT_WORDS = ("", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열")   # 「두 분」 — 열을 넘으면 숫자로
ROOM_TITLE = "[회의실 예약] {title}"            # 회의실을 잡으면 내 일정에 저절로 드는 제목(회의실 손이 짓는다)
# 회의실 — 사람처럼 링크 하나가 한 방이다: 「[방 이름(정원)](room:<회의실 손 free 의 id>)」. 글은 사람이 읽는 방, id 는 회의실 손이 잡을 때 받는 열쇠다
ROOM_CELL = re.compile(rf"^\[(?P<name>{LABEL}+)\]\(room:(?P<id>[A-Za-z0-9][A-Za-z0-9._:-]{{0,99}})\)$")


# ── 칸의 값을 이름으로 — 종류마다의 차례대로 한 번 읽는다 ─────────────────────

@dataclass(frozen=True)
class Cells:
    """맡길 일 한 칸의 값을 이름으로 — 그 종류의 차례(`Kind.cells`)대로 읽은 것(`read_cells`). 머리말(「참석 」 · 「안내 」 · 「메일 」)은
    뗐고, 그 종류에 없는 칸은 빈 글이다. 셈(꼴 · 넘길 값 · 사람 · 줄 · 무엇이 되나 · 시작)은 다 이 이름으로 읽는다."""
    what: str = ""                  # 찾을 것(찾아 정리)
    to: str = ""                    # 받는 분 — 사람 링크(답장 · 새 메일)
    title: str = ""                 # 제목(새 메일 · 회의실 · Teams)
    say: str = ""                   # 할 말(답장 · 새 메일 · 대화)
    mail: str = ""                  # 답할 메일의 번호(답장)
    start: str = ""                 # 시작 — 서울 벽시계(회의실 · Teams)
    end: str = ""                   # 끝
    room: str = ""                  # 방 — 회의실 링크
    attend: str = ""                # 참석 — 사람 링크
    note: str = ""                  # 안내(Teams — 적었을 때만)


def after(cell: str, mark: str) -> str:
    """칸의 머리말(「참석 」 · 「안내 」 · 「메일 」, 없으면 빈 글)을 뗀 값."""
    return cell[len(mark):].strip()


def read_cells(order: tuple[tuple[str, str], ...], extra: tuple[tuple[str, str], ...], p: tuple[str, ...]) -> Cells | None:
    """칸의 값(「 | 」로 가른 그대로) → 이름 붙은 값. `order` 의 칸이 그 차례로 다 있고 `extra` 의 칸은 있으면 그 뒤에 선다 — 칸마다
    (이름, 머리말). 칸 수가 모자라거나 넘치거나 · 빈 값이 있거나 · 머리말이 빠졌으면 None(고쳐 읽지 않는다)."""
    if not len(order) <= len(p) <= len(order) + len(extra):
        return None
    named = {}
    for (name, mark), value in zip((*order, *extra), p):
        if not value or not value.startswith(mark):
            return None
        named[name] = after(value, mark)
    return Cells(**named)


# ── 칸 하나의 셈 — 표의 줄들이 함께 쓴다 ──────────────────────────────────────

def count_words(n: int) -> str:
    """사람 수의 말 — 「한」 · 「두」 … 「열」, 열을 넘으면 숫자."""
    return COUNT_WORDS[n] if 0 < n < len(COUNT_WORDS) else str(n)


def ro(word: str) -> str:
    """조사 「(으)로」 — 끝 글자에 받침이 있으면(ㄹ 받침은 빼고) 「으로」. 한글이 아니면 「(으)로」."""
    last = word.rstrip("」』)] ")[-1:] or "x"
    if not "가" <= last <= "힣":
        return "(으)로"
    jong = (ord(last) - ord("가")) % 28
    return "로" if jong in (0, 8) else "으로"


def span_fits(a: str, b: str) -> bool:
    """두 시각이 일정 손의 꼴(`PUT_STAMP`)이고 시작이 끝보다 앞인가."""
    return bool(PUT_STAMP.match(a) and PUT_STAMP.match(b) and a < b)


def people_fit(cell: str) -> bool:
    """사람을 대는 칸(받는 분 · 참석)이 사람 링크로 선 사람들인가."""
    return bool(people_in(cell))


def said_all(people: tuple[Person, ...]) -> str:
    """사람들 → 사람이 읽는 「이름 직함(덧말) · …」."""
    return " · ".join(x.said() for x in people)


def room_name(cell: str) -> str:
    """방 칸 → 사람이 읽는 방 이름. 회의실 링크 꼴이 아니면 칸 그대로."""
    m = ROOM_CELL.match(cell)
    return " ".join(plain(m.group("name")).split()) if m else cell


@dataclass(frozen=True)
class Shown:
    """사람이 읽는 칸의 말 — 꼴이 맞은 값(`Cells`)과 사람 칸의 사람들에서 한 번 짓는다(`shown_of`). 줄을 짓는 셈(`Kind.line`)은 이것을 옮기기만 한다."""
    when: str = ""                  # 시작 · 끝 → 「11월 26일(목) 14:00–16:00」
    room: str = ""                  # 방 링크 → 사람이 읽는 방 이름
    people: str = ""                # 사람 칸의 사람들 → 「이름 직함(덧말) · …」


def shown_of(c: Cells, people: tuple[Person, ...]) -> Shown:
    """이름 붙은 값 → 사람이 읽는 칸의 말. 시작이 없는 종류(꼴이 틀린 칸도)는 때가 빈 글이다 — 시작이 있으면 꼴(`span_fits`)이 이미 맞았다."""
    return Shown(when=span_words(c.start, c.end) if c.start else "", room=room_name(c.room) if c.room else "", people=said_all(people))


def span_value(c: Cells) -> tuple[str, str]:
    """넘길 때 — 해까지 든 서울 시각 둘(사람이 읽는 줄은 「11월 19일(목)」로 해가 빠진다)."""
    return VALUE_WHEN, f"{c.start} – {c.end} (서울)"


# ── 종류마다의 꼴 · 값 · 줄 ─────────────────────────────────────────────────

def read_fits(c, put) -> bool:
    """꼴이 차례로 다 읽힌 것으로 선다(찾아 정리 · 대화) — 값 하나가 비지 않았다."""
    return True


def reply_fits(c, put) -> bool:
    """답장의 꼴 — 받는 분이 사람 링크이고 답할 메일이 32자리 메일 번호."""
    return people_fit(c.to) and bool(UNID.match(c.mail))


def mail_fits(c, put) -> bool:
    """새 메일의 꼴 — 받는 분이 사람 링크."""
    return people_fit(c.to)


def room_fits(c, put) -> bool:
    """회의실 잡기의 꼴 — 두 시각 · 방이 회의실 링크 · 참석이 사람 링크."""
    return span_fits(c.start, c.end) and bool(ROOM_CELL.match(c.room)) and people_fit(c.attend)


def teams_fits(c, put) -> bool:
    """Teams 회의의 꼴 — 두 시각 · 참석이 사람 링크."""
    return span_fits(c.start, c.end) and people_fit(c.attend)


def put_fits(c, put) -> bool:
    """일정 넣기의 꼴 — 칸의 값이 넣을 일정으로 읽혔다(`brief_put.put_of`)."""
    return put is not None


def never_fits(c, put) -> bool:
    """꼴이 틀린 칸 — 어떤 값도 맞지 않는다."""
    return False


def find_values(c):
    """찾아 정리가 넘길 값 — 찾을 것."""
    return [(VALUE_WHAT, c.what)]


def reply_values(c):
    """답장이 넘길 값 — 받는 분 · 답할 메일(메일 링크) · 할 말."""
    return [(VALUE_TO, c.to), (VALUE_MAIL, f"[답할 메일](mail:{c.mail.upper()})"), (VALUE_SAY, c.say)]


def mail_values(c):
    """새 메일이 넘길 값 — 받는 분 · 제목 · 할 말."""
    return [(VALUE_TO, c.to), (VALUE_TITLE, c.title), (VALUE_SAY, c.say)]


def room_values(c):
    """회의실 잡기가 넘길 값 — 때 · 방(회의실 링크) · 제목 · 참석."""
    return [span_value(c), (VALUE_ROOM, c.room), (VALUE_TITLE, c.title), (VALUE_ATTEND, c.attend)]


def teams_values(c):
    """Teams 회의가 넘길 값 — 때 · 제목 · 참석 · (적었으면 안내)."""
    return [span_value(c), (VALUE_TITLE, c.title), (VALUE_ATTEND, c.attend), *([(VALUE_NOTE, c.note)] if c.note else [])]


def no_values(c):
    """넘길 값이 없다 — 뒤의 실행에 넘기지 않는 종류다."""
    return []


def what_line(c, s, put, written) -> str:
    """찾아 정리의 줄 — 찾을 것 그대로."""
    return c.what


def say_line(c, s, put, written) -> str:
    """대화의 줄 — 할 말 그대로."""
    return c.say


def reply_line(c, s, put, written) -> str:
    """답장의 줄 — 「받는 분께 — 무슨 답」."""
    return f"{s.people}께 — {c.say}"


def mail_line(c, s, put, written) -> str:
    """새 메일의 줄 — 「받는 분께 「제목」 — 할 말」."""
    return f"{s.people}께 「{c.title}」 — {c.say}"


def room_line(c, s, put, written) -> str:
    """회의실 잡기의 줄 — 때 · 방 이름 · 「제목」 · 참석."""
    return " · ".join((s.when, s.room, f"「{c.title}」", ATTEND_MARK + s.people))


def teams_line(c, s, put, written) -> str:
    """Teams 회의의 줄 — 때 · 「제목」 · 참석 · (적었으면 안내)."""
    note = [f"{NOTE_MARK}「{c.note}」"] if c.note else []
    return " · ".join((s.when, f"「{c.title}」", ATTEND_MARK + s.people, *note))


def put_line(c, s, put, written) -> str:
    """일정 넣기의 줄 — 무엇을 넣나 · 공개 범위."""
    return f"{put.words()} · {VIS_WORDS[put.private]}"


def written_line(c, s, put, written) -> str:
    """꼴이 틀린 칸의 줄 — 적힌 글 그대로."""
    return written


def room_fill(c, people) -> dict:
    """회의실 잡기의 무엇이 되나에 채울 칸 — 안내 메일이 갈 분의 수 · 일정에 들 제목과 그 조사."""
    return {"who": count_words(len(people)) + " 분", "title": c.title, "ro": ro(ROOM_TITLE.format(title=c.title))}


def no_fill(c, people) -> dict:
    """무엇이 되나에 채울 칸이 없다."""
    return {}


def span_start(c, put) -> str:
    """때가 든 일의 시작."""
    return c.start


def put_start(c, put) -> str:
    """일정 넣기의 시작 — 넣을 일정의 시작."""
    return put.start


def no_start(c, put) -> str:
    """때가 없는 일 — 빈 글."""
    return ""


# ── 표 ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Kind:
    """맡길 일 종류 하나 — 카드에 적는 이름 · 넘기는 길 · 적는 칸 · 값의 차례 · 셈(꼴 · 넘길 값 · 줄 · 무엇이 되나의 칸 · 시작) · 사람 칸 ·
    창의 말 · 결과 이름표. 셈은 이름 붙은 값(`Cells`)과 넣을 일정 · 사람이 읽는 칸의 말(`Shown`) · 사람 칸의 사람들을 받는다 — 맡길 일
    읽기(`brief_tasks.task_of`)가 칸마다 한 번 부르고, 부르는 쪽은 셈한 값만 읽는다."""
    name: str                                   # 카드에 적는 종류 이름 — 모델이 쓰고 뒤의 실행이 `kind` 로 받는다(계약)
    via: str                                    # 넘기는 길 — VIA_RUN · VIA_PUT · VIA_TALK · VIA_NONE
    fits: Callable[[Cells, Put | None], bool]   # 값의 꼴 — 고쳐 읽지 않는다: 시각 · 번호 · 링크의 꼴이 틀리면 거짓
    values: Callable[[Cells], list]             # 넘길 값 — 칸마다 (이름, 적힌 그대로의 값). 방 · 사람 · 답할 메일은 열쇠가 든 링크다
    line: Callable[[Cells, Shown, Put | None, str], str]   # 사람이 읽는 「무엇을 하나」 — 누르시면 이 줄의 값 그대로 끝까지 한다
    start: Callable[[Cells, Put | None], str]   # 시작 시각(서울 벽시계) — 때가 없는 일이면 빈 글
    cells: tuple[tuple[str, str], ...] | None = ()   # 값의 차례 — 칸마다 (`Cells` 의 이름, 머리말). None 이면 값은 넣을 일정이 든다(`brief_put`)
    extra: tuple[tuple[str, str], ...] = ()     # 적었으면 차례 뒤에 서는 칸
    field: str = DO_FIELD                       # 적는 칸 — 「바로 할 일」이면 첫 값이 이 이름, 다른 칸이면 칸 전체가 이 종류의 값이다
    topped: bool = False                        # 칸 끝의 「| 추천」을 떼어 창 머리에 미리 세울 표로 받나
    people: str = ""                            # 사람 칸 — 사람을 대는 값(참석자 · 받는 분)이 선 `Cells` 의 이름. 없으면 빈 글
    fill: Callable[[Cells, tuple], dict] = no_fill   # `cons` 의 칸(회의실은 안내 메일이 갈 분의 수와 일정에 들 제목)
    cons: str = ""                              # 누르시면 무엇이 되나 — 같은 종류는 어느 카드에서나 같은 말이다
    short: str = ""                             # 막대의 짧은 이름
    head: str = ""                              # 끝났을 때 카드의 머리
    tail: str = ""                              # 그 뒤의 덧말
    late: str = ""                              # 시작이 지난 줄에 창이 다는 말(빈 글이면 안 단다)
    labels: tuple[str, ...] = ()                # 끝난 일의 카드에 머리 아래 설 값의 이름표 — 뒤의 실행이 이 차례로 값을 적고 창은 받은 그대로 세운다
    read_only: bool = False                     # 아무것도 안 바꾸나 — 도중에 멈췄어도 됐는지 모를 것이 없어 「못 함」이고 다시 맡겨도 된다
    dated: bool = False                         # 때가 든 일인가 — 카드를 약속의 꼴로 세운다

    def read(self, p: tuple[str, ...]) -> Cells | None:
        """칸의 값 → 이 종류의 차례로 이름 붙인 값(`read_cells`). 값을 넣을 일정이 드는 종류는 빈 `Cells`."""
        return Cells() if self.cells is None else read_cells(self.cells, self.extra, p)

    def persons(self, c: Cells) -> tuple[Person, ...]:
        """사람 칸(`people`)의 사람들 — 칸이 없거나 사람 링크의 꼴이 아니면 빈 것."""
        cell = getattr(c, self.people) if self.people else ""
        return tuple(people_in(cell) or ()) if cell else ()

    def said(self, c: Cells, people: tuple[Person, ...]) -> str:
        """누르시면 무엇이 되나 — `cons` 에 그 값과 사람들로 채운 칸을 넣은 말."""
        return self.cons.format(**self.fill(c, people))


DRAFTED = "임시보관함에 두고 그 화면을 Edge 에 띄웁니다 — 보내기는 직접 누르십니다"
NOT_SENT = " — 아직 안 나갔습니다"
MAIL_LABELS = ("받는 분", "제목", "글")
SPAN = (("start", ""), ("end", ""))             # 때가 든 일의 앞 두 칸 — 시작 · 끝

FIND = Kind("찾아 정리", VIA_RUN, read_fits, find_values, what_line, no_start, cells=(("what", ""),), cons="메일을 읽기만 합니다",
            short="찾아 정리", head="찾아 정리했습니다", read_only=True)   # 결과 이름표가 없다 — 메일 한 통에 한 줄이다
REPLY = Kind("답장 써 두기", VIA_RUN, reply_fits, reply_values, reply_line, no_start, cells=(("to", ""), ("say", ""), ("mail", MAIL_MARK)),
             people="to", cons=DRAFTED, short="답장", head="답장을 써 두었습니다", tail=NOT_SENT, labels=MAIL_LABELS)
MAIL = Kind("새 메일 써 두기", VIA_RUN, mail_fits, mail_values, mail_line, no_start, cells=(("to", ""), ("title", ""), ("say", "")),
            people="to", cons=DRAFTED, short="새 메일", head="새 메일을 써 두었습니다", tail=NOT_SENT, labels=MAIL_LABELS)
ROOM = Kind("회의실 잡기", VIA_RUN, room_fits, room_values, room_line, span_start,
            cells=(*SPAN, ("room", ""), ("title", ""), ("attend", ATTEND_MARK)), people="attend", fill=room_fill,
            cons="{who}께 회의 안내 메일이 회사 메일로 가고, 내 일정에는 「" + ROOM_TITLE + "」{ro} 저절로 듭니다", short="회의실",
            head="회의실을 잡았습니다", late="지난 회의라 잡지 않습니다", labels=("회의실", "때", "참석", "Teams", "내 일정"), dated=True)
TEAMS = Kind("Teams 회의 띄우기", VIA_RUN, teams_fits, teams_values, teams_line, span_start,
             cells=(*SPAN, ("title", ""), ("attend", ATTEND_MARK)), extra=(("note", NOTE_MARK),), people="attend",
             cons="제목 · 때 · 참석자를 채운 Teams 회의 예약 창을 띄웁니다 — [보내기]는 Teams 에서 직접 누르시고, 보내셔야 회의가 잡혀 초대가 가고 "
                  "내 일정에 보입니다", short="Teams 회의", head="Teams 회의 예약 창을 띄웠습니다", tail=" — 보내셔야 잡힙니다",
             late="지난 회의라 띄우지 않습니다", labels=("제목", "때", "참석", "안내 글"), dated=True)
CAL = Kind("일정 넣기", VIA_PUT, put_fits, no_values, put_line, put_start, cells=None, cons="내 일정함에만 넣습니다 — 아무에게도 알림이 안 갑니다",
           short="일정", late="지난 약속이라 넣지 않았습니다", dated=True)   # 끝의 말은 넣은 손이 끝마다 짓는다(`presses.WORDS`) — 머리가 없다
TALK = Kind("같이 의논", VIA_TALK, read_fits, no_values, say_line, no_start, cells=(("say", ""),), field=TALK_FIELD, topped=True,
            cons="누르시면 이 카드의 근거와 함께 VS Code 에 대화를 엽니다 — 엔터를 누르셔야 시작합니다")   # 칸 이름이 곧 이 종류다
BAD = Kind("", VIA_NONE, never_fits, no_values, written_line, no_start)   # 꼴이 틀린 칸 — 적힌 글 그대로 서고 맡길 수 없다

KINDS = (FIND, REPLY, MAIL, ROOM, TEAMS, CAL, TALK)
ROWS = {k.name: k for k in KINDS}
NAMED = {k.name: k for k in KINDS if k.field == DO_FIELD}   # 「바로 할 일」의 첫 값으로 적는 종류
OLD_PUT = CAL                                   # 옛 「넣을 일정」 칸은 이 종류 한 줄로 읽는다
FIELD_KINDS = {**{k.field: k for k in KINDS if k.field != DO_FIELD}, PUT_FIELD: OLD_PUT}   # 칸 이름이 정한 종류 — 칸 전체가 그 종류의 값


def read_only(name: object) -> bool:
    """기록에 남은 종류 이름이 아무것도 안 바꾸는 종류인가 — 모르는 이름 · 글이 아닌 값(손으로 고친 기록)이면 거짓(됐는지 모를 수 있다)."""
    return isinstance(name, str) and ROWS.get(name, BAD).read_only
