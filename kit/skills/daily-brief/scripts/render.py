"""보고 창을 그린다 — 읽은 보고 글(`brief_text.Report`)과 창이 보이는 지금 모습을 보고 창의 HTML(`build` · 틀 `assets/report.html` · 스크립트
`assets/report.js`)로. 같은 글의 메일 한 장은 곁의 `render_mail.py` 가, 둘이 함께 쓰는 줄 안의 한 걸음(`inline_walk`)은 `render_base.py` 가 든다
— 이 파일은 창의 겉(`WindowSkin`)만 끼운다.
파일을 쓰거나 사용자 폴더를 읽지 않고 망에 닿지 않는다 — 짓는 글만 낸다. 무엇을 지키고 왜 그런가는 `references/DESIGN.md` 가 든다.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import html
import json
import pathlib
import string
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
import clock as T  # noqa: E402
import prefs_file as P  # noqa: E402
from render_base import DATELINE, NO_TIME_SAID, inline_walk  # noqa: E402
from brief_const import (ASK_KEY, ASK_NO_VSCODE, ASK_OPEN_CEILING_S, ASK_TAKE_S, AWAY_KEY, CAL_PREFIX, DONE_PREFIX, HAND_BEAT_S,  # noqa: E402
                         HAND_KEY, RUN_PREFIX, RUN_REFUSED, RUN_TAKE_S, SEOUL_OFFSET, STATE_KEY, TASK_BAD,
                         TASK_PREFIX, TIMES_KEY, UNQUIET_PREFIX, VIA_EDGE, WEEKDAYS)
from brief_cards import WAIT_ME, WAIT_THEM, card_head, item_key, item_title  # noqa: E402
from brief_inline import OVER, UNID_HEX, plain  # noqa: E402
from brief_people import people_in  # noqa: E402
from brief_sections import DONE_SECTION, RECORD_SECTIONS, is_empty_done, is_meetings, names_section, report_items  # noqa: E402
from brief_tasks import (ROW_BAD, ROW_BAD_PUT, ROW_PUT, ROW_RUN, ROW_TALK, ROW_TALK_TOP, ROW_UNKEYED, TOP_MARK, Task,  # noqa: E402
                         asks_time, card_shaped, dated_card, row_shape, take_card)
from brief_text import BULLET, DASH, Block, Item, Report  # noqa: E402
from task_kinds import TEAMS, VIA_TALK  # noqa: E402

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "assets" / "report.html"
SCRIPT = TEMPLATE.with_name("report.js")      # 창의 하나뿐인 스크립트 — 누르신 표시 · 고르신 시각. CSP 는 지을 때마다 이 글의 해시만 연다


ASK_MAX = 1000                                 # 칸이 받는 글자 수 — 두 번 인코딩한 주소가 Windows 명령 줄 한도의 절반 남짓에 든다
ASK_OFF = "이 창은 메일 비서의 Edge 밖에서 열려 여기서는 부탁하실 수 없습니다 — 대화에서 말씀해 주세요."
ASK_HINT = "누르시면 VS Code 의 작업 폴더 창에 새 대화가 열리고 이 말이 입력 칸에 채워집니다 — 엔터를 누르셔야 시작합니다."
PUT_BAD = "넣을 값의 꼴이 틀려 이 창에서는 넣을 수 없습니다 — 대화에서 「그 약속 넣어 줘」 하시면 넣습니다"
PUT_NOKEY = "이 창에서는 넣지 않습니다 — 까닭은 위 카드에 적었습니다"

TOP_TAG = "· 창 맨 위에 추천으로 올린 일"
TASK_GO, TALK_GO = "이것만 맡기기", "대화로 열기"
TICK_LABEL = "바로 맡길 일에 넣기"
BOARD_TITLE = "바로 맡길 일"
BAR_HINT = "무엇을 하는지는 아래 카드마다 적혀 있습니다 — 읽어 보시고 뺄 것은 카드에서 표시를 푸세요. 맨 아래에서도 맡기실 수 있습니다."
END_HINT = "위 카드에서 표시한 일입니다. 누르시면 카드에 적힌 그대로 위에서부터 차례로 하고, 하나 끝날 때마다 그 카드에 결과가 섭니다."
LIST_OPEN, LIST_CLOSE = "목록 펴기", "목록 접기"
ASK_SUGGEST_HINT = ("「{title}」 카드의 일입니다. 그대로 누르시면 이 말로, 치시면 치신 말로 VS Code 에 대화를 엽니다 — 엔터를 누르셔야 "
                    "시작합니다.")
TICK_NONE, TICK_TODO, TICK_DONE = "", "todo", "done"   # 줄의 단추 — 없음 · 할 일의 줄(셋 · 바탕은 안 눌림) · 「끝났다고 하신 것」의 줄(끝났음 하나 · 바탕은 눌림)
# 할 일의 줄에 서는 단추 — (표시의 값, 단추 글, 단추에 올리면 보이는 말). 「끝났다고 하신 것」의 줄에는 첫 것만 선다
MARKS = (("done", "끝났음", "끝난 일 — 다음 보고부터 올리지 않습니다"),
         ("later", "내일 다시", "오늘은 넘기고 내일 첫 보고에 다시 올립니다"),
         ("quiet", "안 올려도 됨", "이런 건 안 올려도 됨 — 이런 일은 보고에 올리지 않습니다(아래 「보고 맞추기」에서 되돌립니다)"))
TICK_OFF = "이 창은 메일 비서의 Edge 밖에서 열려 누르신 것을 받지 않습니다 — 끝난 일 · 미룰 일은 대화에서 말씀해 주세요."
# 부탁 칸도 서는 창의 같은 줄 — 부탁 칸의 줄(ASK_OFF)과 거의 같은 말이라 창의 스크립트가 이 한 줄만 세운다
TICK_ASK_OFF = "이 창은 메일 비서의 Edge 밖에서 열려 누르신 것을 받지 않고, 여기서 부탁하실 수도 없습니다 — 끝난 일 · 미룰 일 · 부탁은 대화에서 말씀해 주세요."
PEOPLE_BAD = "적힌 꼴이 틀려 사람별에 세우지 않았습니다"
# 보고 맞추기의 시각 곁 한 줄 — 보고 시각을 건 것이 곧 그 시각의 스스로 로그인이라 고를 거리가 아니라 사실과 그 값으로 말한다
TIMES_LOGIN = (" 첫 시각은 그 보고 앞에 한 번, 뒤 시각은 사내 로그인이 끊겨 있을 때만 비서가 스스로 로그인합니다 — 그러면 평소 쓰시는 Edge 의 "
               "사내 메일 · 일정 창이 닫히고 그 EP 포털 탭에서는 앱을 새로 못 띄웁니다(로그아웃하고 로그인하시면 됩니다).")
# 비서가 사람 없이 로그인해 지은 보고의 머리에 서는 한 줄 — 그 로그인이 사람 쪽에서 무엇을 닫았고 무엇을 다시 해야 하나
SIGNED_NOTE = ("{at}에 비서가 사내 로그인을 새로 했습니다 — 평소 쓰시는 Edge 에 떠 있던 사내 메일 · 일정 창은 닫혔고, 거기 EP 포털에서는 앱(ERP · MES "
               "따위)이 새로 안 뜹니다(이미 띄워 두신 앱 창은 그대로 됩니다). 앱을 새로 띄우시려면 평소 Edge 에서 EP 를 로그아웃한 뒤 다시 로그인해 "
               "주세요(대화에서 「EP 돌려줘」 하시면 평소 Edge 에 로그인을 열어 드립니다).")

MAIL_URL = "{mailbox}/XML_Inbox/{unid}?OpenDocument"   # 웹메일에서 그 메일을 여는 주소 — 폴더에만 든 메일에도 먹는다


# ── 줄 안 — 이스케이프와 메일 링크 ──────────────────────────────────────────

@dataclass
class Ink:
    """줄 안을 짓는 손 — 메일함 주소를 들고, 지은 링크 · 링크로 못 지은 메일 번호 · 번호 꼴이 아닌 mail: 표시 · 누름 단추 무리를 세고,
    사람을 댄 줄(`WAIT_ME` · `WAIT_THEM`)을 모은다 — (칸 이름, 주소, 이름, 줄의 닻, 일 이름, 기한 지남 표지)."""
    mailbox: str | None
    links: int = 0
    unlinked: int = 0
    bad_refs: int = 0
    boxes: int = 0
    bad_puts: int = 0               # 「넣을 일정」 칸의 꼴이 틀려 단추를 못 단 카드
    bad_tasks: list = field(default_factory=list)   # 꼴이 틀린 맡길 일의 칸 — 그 글 그대로(끝 줄 앞에서 경고한다)
    tasks: list = field(default_factory=list)       # 선 「바로 할 일」 — (Task, 카드의 닻)
    item_tasks: dict = field(default_factory=dict)  # 줄마다 미리 가른 맡길 일 — {id(줄): [Task]}(`take_card`)
    top_id: str | None = None                       # 창 머리의 칸에 미리 세울 「대화로 할 일」의 번호
    ready: bool = False                             # 이 PC 에 VS Code 의 Claude Code 가 있나 — 없으면 「대화로 열기」를 안 세운다
    tops: int = 0                                   # 추천 표가 붙은 「대화로 할 일」의 수 — 둘 넘으면 아무것도 안 올리고 경고한다
    waits: list = field(default_factory=list)
    bad_people: list = field(default_factory=list)  # 꼴이 틀린 사람 칸 — 「이름: 값」 그대로(끝 줄 앞에서 경고한다)

    def mail(self, label_html: str, unid: str) -> str:
        """메일 링크 하나 — 메일함 주소가 있으면 웹메일에서 그 메일을 여는 링크(링크 수를 센다), 없으면 글 곁에 메일 번호(못 이은 수를 센다)."""
        unid = unid.upper()
        if self.mailbox is None:
            self.unlinked += 1
            return f'{label_html} <span class="unid">{unid}</span>'
        self.links += 1
        href = html.escape(MAIL_URL.format(mailbox=self.mailbox, unid=unid), quote=True)
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{label_html}</a>'

    def inline(self, text: str, links: bool = True) -> str:
        """줄 안 — 창의 겉(`WindowSkin`)으로. `links` 가 거짓이면 링크 · 표 없이 글만 짓는다(링크 글 속 · 왼쪽 목록 · 창의 이름)."""
        return inline_walk(text, WindowSkin(self, links))


class WindowSkin:
    """창의 겉 — 메일 링크는 웹메일에서 그 메일을 여는 링크(`Ink.mail` 이 센다), 사람 · 회의실은 이름이 서고 주소 · id 는 올리면 보이는 표,
    표지는 둥근 표, 굵게는 <strong>. `links` 가 거짓이면 링크 · 사람 · 회의실의 겉 없이 글만 — 같은 글을 링크 없이 한 번 더 짓는 자리라
    번호가 아닌 mail: 표시도 안 센다."""

    def __init__(self, ink: Ink, links: bool = True):
        self.ink, self.links = ink, links

    def inside(self) -> WindowSkin:
        """링크 글 속에 쓸 겉 — 같은 창의 겉에서 링크 · 사람 · 회의실의 겉을 뺀 것."""
        return WindowSkin(self.ink, False)

    def code(self, words: str) -> str:
        """고정 글자 — <code> 로."""
        return f"<code>{html.escape(words, quote=True)}</code>"

    def bad_ref(self) -> None:
        """꼴이 틀린 메일 표시 하나를 센다 — 링크를 짓는 판에서만."""
        self.ink.bad_refs += self.links

    def mail(self, inner: str, unid: str) -> str:
        """메일 표시 — 링크를 짓는 판이면 웹메일 링크(`Ink.mail`), 아니면 글만."""
        return self.ink.mail(inner, unid) if self.links else inner

    def person(self, inner: str, addr: str) -> str:
        """사람 — 이름에 주소를 올리면 보이는 표로, 링크 없는 판이면 이름만."""
        return f'<span class="person" title="{html.escape(addr, quote=True)}">{inner}</span>' if self.links else inner

    def room(self, inner: str, rid: str) -> str:
        """회의실 — 이름에 id 를 올리면 보이는 표로, 링크 없는 판이면 이름만."""
        return f'<span class="room" title="{html.escape(rid, quote=True)}">{inner}</span>' if self.links else inner

    def pill(self, words: str, over: bool) -> str:
        """표지 — 둥근 표로(`over` 면 넘친 표)."""
        return f'<span class="{"pill over" if over else "pill"}">{html.escape(words, quote=True)}</span>'

    def bold(self, inner: str) -> str:
        """굵게 — <strong> 으로."""
        return f"<strong>{inner}</strong>"


def attr(**kv: str | None) -> str:
    """`data-…` 속성 — 값이 None 이면 뺀다. 이름의 「_」는 「-」로."""
    return "".join(f' data-{k.replace("_", "-")}="{html.escape(v, quote=True)}"' for k, v in kv.items() if v is not None)


def todo_block(tasks: list[Task], ink: Ink, anchor: str, top_id: str | None, ready: bool) -> str:
    """카드 끝의 할 일 칸 — 줄마다 꼴을 가르고(`brief_tasks.row_shape`) → 끝 줄 앞의 경고와 창 곁의 손이 받을 일에 세고(`note_row`) → 그 꼴의
    줄을 짓는다(`ROW_WORDS`). 칸이 없으면 빈 글."""
    out = []
    for t in tasks:
        shape = row_shape(t, top_id)
        note_row(ink, t, shape, anchor)
        out.append(ROW_WORDS[shape](t, shape, anchor, ready))
    return f'<div class="todo">{"".join(out)}</div>' if out else ""


def note_row(ink: Ink, t: Task, shape: str, anchor: str) -> None:
    """할 일 줄 하나를 그 꼴대로 센다 — 꼴이 틀린 「넣을 일정」은 수로, 꼴이 틀린 다른 칸은 그 글 그대로(끝 줄 앞에서 경고한다), 누를 수 있는 일은
    창 곁의 손이 받을 일로(그 줄의 닻과 함께)."""
    if shape == ROW_BAD_PUT:
        ink.bad_puts += 1
    elif shape == ROW_BAD:
        ink.bad_tasks.append(f"{t.field}: {t.written}")
    elif shape in (ROW_PUT, ROW_RUN):
        ink.tasks.append((t, anchor))


def bad_row(t: Task, shape: str, anchor: str, ready: bool) -> str:
    """꼴이 틀린 칸의 줄 — 칸 이름 · 적힌 글 그대로 · 맡길 수 없다는 말(옛 「넣을 일정」 칸이면 그 칸의 말)."""
    return (f'<div class="todo-row bad"><span class="todo-what"><span class="kind">{html.escape(t.field)}</span>'
            f'{html.escape(t.written)}<span class="todo-cons no">{html.escape(PUT_BAD if shape == ROW_BAD_PUT else TASK_BAD)}'
            '</span></span></div>')


def talk_row(t: Task, shape: str, anchor: str, ready: bool) -> str:
    """「대화로 할 일」의 줄 — 줄 · 추천이면 그 표 · `ready`(이 PC 에 VS Code 의 Claude Code 가 있다)이면 무엇이 되나와 숨은 「대화로 열기」.
    `ready` 가 거짓이면 추천 표도 안 단다."""
    is_top = ready and shape == ROW_TALK_TOP
    tag = f'<span class="top-tag">{html.escape(TOP_TAG)}</span>' if is_top else ""
    cons = f'<span class="todo-cons">{html.escape(t.cons)}</span>' if ready else ""
    go = f'<button type="button" class="put ghost talk-go" hidden>{TALK_GO}</button>' if ready else ""
    return (f'<div class="todo-row"{attr(talk=t.id, words=t.words(), line=t.line, top="1" if is_top else None)}>'
            f'<span class="todo-what"><span class="kind talk">{t.kind}</span>「{html.escape(t.line)}」{tag}{cons}</span>{go}</div>'
            '<p class="put-note" aria-live="polite"></p>')


def unkeyed_row(t: Task, shape: str, anchor: str, ready: bool) -> str:
    """열쇠를 못 받은 일정 넣기의 줄 — 줄과 이 창에서는 안 넣는다는 말. 까닭은 마무리(`finish.py`)가 카드의 점으로 넣었다."""
    return (f'<div class="todo-row bad"><span class="todo-what"><span class="kind">{html.escape(t.kind)}</span>{html.escape(t.line)}'
            f'<span class="todo-cons no">{html.escape(PUT_NOKEY)}</span></span></div>')


def task_row(t: Task, shape: str, anchor: str, ready: bool) -> str:
    """누를 수 있는 일의 줄 — 숨은 표시 칸 · 줄 · 무엇이 되나 · 숨은 「이것만 맡기기」(일정 넣기면 그 열쇠와 시작을 단다) · 결과 자리. 표시 칸과
    단추는 창의 스크립트가 누름을 남길 수 있는 창에서만 꺼낸다(스크립트가 막혀도 누를 수 없는 단추는 안 선다)."""
    label = f"{TICK_LABEL} — " + (f"카드 {t.num} " if t.num else f"「{t.card}」 ") + t.kind
    data = attr(t=t.id, kind=t.kind, k=t.row.short, c=t.num or "", title=t.card, anchor=anchor, line=t.line, head=t.row.head,
                tail=t.row.tail or None, start=t.start or None, late=t.row.late or None, ev="\n".join(t.evidence))
    key = attr(key=t.put.key, start=t.start) if shape == ROW_PUT else ""   # 시작은 줄과 같은 한 값(`Task.start`) — 창의 늦음 잠금이 둘을 읽는다
    return (f'<div class="todo-row"{data}><span class="todo-tick" hidden><input type="checkbox" checked{attr(t=t.id)} '
            f'aria-label="{html.escape(label, quote=True)}"></span><span class="todo-what"><span class="kind">{t.kind}</span>'
            f'{html.escape(t.line)}<span class="todo-cons">{html.escape(t.cons)}</span></span>'
            f'<button type="button" class="put task-go"{key} aria-pressed="false" hidden>{TASK_GO}</button><span class="st" hidden></span></div>'
            '<p class="put-note" aria-live="polite"></p><div class="run" hidden></div>')


# 할 일 줄의 꼴마다 그 줄을 짓는 조각 — 꼴은 `brief_tasks.row_shape` 가 가른다
ROW_WORDS = {ROW_BAD_PUT: bad_row, ROW_BAD: bad_row, ROW_TALK: talk_row, ROW_TALK_TOP: talk_row, ROW_UNKEYED: unkeyed_row,
             ROW_PUT: task_row, ROW_RUN: task_row}


# ── 짓기 — 덩이를 틀의 자리로 ──────────────────────────────────────────────


def tick_box(it: Item, ink: Ink, tick: str) -> str:
    """누름 단추 무리 — 줄의 일 열쇠(`item_key` — 「일:」 칸의 메일, 없으면 첫 메일 번호)가 열쇠다(업무 파일은 일을 그 일을 연 메일로 잇는다).
    메일 번호가 없으면 빈 글.
    할 일의 줄에는 「끝났음 · 내일 다시 · 안 올려도 됨」 셋이 서고, `tick` 이 `TICK_DONE` 이면 「끝났다고 하신 것」의 줄이라 「끝났음」 하나가
    눌린 채 선다(`data-done`) — 풀면 끝나지 않았다고 되돌리신 것이다. 처음엔 숨어 있다 — 창의 스크립트가 표시를 거둘 수 있는 창에서만 꺼낸다.
    스크립트가 막혀도 누를 수 없는 단추는 안 선다."""
    unid = item_key(it)
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


def note_waits(it: Item, ink: Ink, facts: list[tuple[str, str]]) -> tuple[str, set[int]]:
    """사람을 댄 칸이 있으면 그 줄의 닻 이름을 주고 사람별 무리에 넣는다 — (닻 · 없으면 빈 글, 꼴이 틀린 칸의 자리). 꼴이 틀린 칸은 사람별에
    안 들고 끝 줄 앞에서 경고한다(`Ink.bad_people`)."""
    found, bad = [], set()
    for n, (label, value) in enumerate(facts):
        if label not in (WAIT_ME, WAIT_THEM):
            continue
        people = people_in(value)
        if people is None:
            bad.add(n)
            ink.bad_people.append(f"{label}: {value}")
            continue
        found += [(label, p) for p in people]
    if not found:
        return "", bad
    anchor = f"w{len({w[3] for w in ink.waits}) + 1}"
    over = next(iter(OVER.findall(" ".join([it.text, *it.subs]))), "").strip()
    ink.waits += [(label, p.address, p.name, anchor, item_title(it), over) for label, p in found]
    return anchor, bad


def fact_value(ink: Ink, value: str, bad: bool) -> str:
    """칸의 값 — 사람을 대는 칸의 꼴이 틀렸으면 쓴 글 그대로 뒤에 그렇다는 말을 단다(맡길 일의 틀린 줄과 같은 꼴)."""
    return ink.inline(value) + (f'<span class="todo-cons no">{html.escape(PEOPLE_BAD)}</span>' if bad else "")


def render_item(it: Item, ink: Ink, tick: str = TICK_NONE) -> tuple[str, str]:
    """줄 하나 — (무리, HTML). 무리는 card(점이 딸린 줄 · 맡길 일이 든 줄) · row. `tick` 이 있으면 메일 번호가 든 줄에 「끝났음」 상자를 단다.
    맡길 일은 미리 가른 것(`Ink.item_tasks`)을 쓴다 — 창 곁의 손이 같은 글에서 내는 번호와 같다."""
    _, points, facts, no_time = take_card(it)
    tasks = ink.item_tasks.get(id(it), [])
    box = tick_box(it, ink, tick) if tick else ""
    anchor, bad = note_waits(it, ink, facts) if tick == TICK_TODO else ("", set())
    if tasks and not anchor:
        anchor = f"c-{tasks[0].id}"
    at = f' id="{anchor}"' if anchor else ""
    if card_shaped(points, tasks, no_time):
        head, rest = card_head(it.text)
        parts = [f'<div class="task-top"><h3>{ink.inline(head)}</h3>{box}</div>' if box else f"<h3>{ink.inline(head)}</h3>"]
        if rest:
            parts.append(f'<p class="when">{ink.inline(rest)}</p>')
        if points:
            parts.append('<ul class="points">' + "".join(f"<li>{ink.inline(p)}</li>" for p in points) + "</ul>")
        if facts:
            parts.append('<dl class="facts">' + "".join(f"<dt>{ink.inline(k)}</dt><dd>{fact_value(ink, v, n in bad)}</dd>"
                                                        for n, (k, v) in enumerate(facts)) + "</dl>")
        if tasks:
            parts.append(todo_block(tasks, ink, anchor, ink.top_id, ink.ready))
        if asks_time(tasks, no_time):
            parts.append(f'<p class="no-time">{html.escape(NO_TIME_SAID)}</p>')
        body = "".join(parts)
        appt = " appt" if tick == TICK_TODO and dated_card(tasks, no_time) else ""
        if it.num is None:
            return "card", f'<li class="task plain{appt}"{at}><div>{body}</div></li>'
        return "card", f'<li class="task{appt}"{at}><span class="task-num">{html.escape(it.num)}</span><div>{body}</div></li>'
    tail = "".join(f' <span class="src-inline">({ink.inline(k)}: {fact_value(ink, v, n in bad)})</span>' for n, (k, v) in enumerate(facts))
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
    """시간줄 덩이 하나를 HTML 로 — 줄마다 때 · 할 일 · 곁말을 세우고, 위 줄의 이름과 아래 곁말을 둘레에 단다."""
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
    if names_section(title, DONE_SECTION):
        return TICK_DONE
    return TICK_NONE if names_section(title, RECORD_SECTIONS) or is_meetings(title) else TICK_TODO


def page_script() -> tuple[str, str]:
    """창에 싣는 스크립트와 그것만 여는 CSP 칸(`'sha256-…'`). 해시는 실을 글 그대로에서 낸다 — 손으로 옮긴 해시는 없다."""
    code = string.Template(SCRIPT.read_text(encoding="utf-8")).substitute(done_prefix=DONE_PREFIX, unid_hex=UNID_HEX, seoul_offset=SEOUL_OFFSET, via_edge=VIA_EDGE, times_key=TIMES_KEY,
                                                                          unquiet_prefix=UNQUIET_PREFIX, state_key=STATE_KEY,
                                                                          cal_prefix=CAL_PREFIX, hand_key=HAND_KEY, away_key=AWAY_KEY,
                                                                          hand_stale_ms=str(3 * HAND_BEAT_S * 1000), ask_key=ASK_KEY,
                                                                          ask_take_ms=str(ASK_TAKE_S * 1000), run_prefix=RUN_PREFIX,
                                                                          task_prefix=TASK_PREFIX, run_take_ms=str(RUN_TAKE_S * 1000), run_refused=RUN_REFUSED, kind_teams=TEAMS.name, unread_tail=UNREAD_TAIL,
                                                                          ask_open_ms=str((ASK_OPEN_CEILING_S + ASK_TAKE_S) * 1000))
    digest = base64.b64encode(hashlib.sha256(code.encode("utf-8")).digest()).decode("ascii")
    return code, f"'sha256-{digest}'"


def signed_note(signed: dict | None, now: dt.datetime) -> str:
    """스캔이 세션 없이 스스로 로그인해 띄운 보고의 범위(`state["signed"]` — 로그인한 때 `at` 부터 그 보고가 글을 남길 수 있는 끝 `until` 까지)
    안에서 짓는 창의 머리에 서는 한 줄. 범위 밖에 지은 창 · 적힌 범위가 없는 창에는 빈 글 — 로그인 없이 지은 보고는 그 줄을 안 든다."""
    if not signed:
        return ""
    at, until = dt.datetime.fromisoformat(signed["at"]), dt.datetime.fromisoformat(signed["until"])
    if not at <= now.astimezone() < until:
        return ""
    return f'<p class="signed-note" id="signed-note">{html.escape(SIGNED_NOTE.format(at=f"{at.astimezone():%H:%M}"))}</p>'


def people_panel(ink: Ink) -> str:
    """사람별 — 같은 줄들을 사람으로 한 번 더 세운다: 나를 기다리는 분(`WAIT_ME`) · 내가 답을 기다리는 분(`WAIT_THEM`). 사람마다 그 일들로
    가는 닻 링크다. 사람을 댄 줄이 없으면 빈 글 — 새로 읽는 것도 더하는 글도 없다."""
    if not ink.waits:
        return ""
    cols = []
    for label, head, sub in ((WAIT_ME, "나를 기다리는 분", "그분께 내가 할 차례인 일"), (WAIT_THEM, "내가 기다리는 분", "그분의 답이 와야 나아가는 일")):
        people: dict[str, list[tuple[str, str, str]]] = {}     # 주소 → 그분의 일들 — 한 분은 한 줄이다
        names: dict[str, str] = {}                            # 주소 → 처음 적힌 이름
        for kind, address, name, anchor, title, over in ink.waits:
            if kind == label and (anchor, title, over) not in people.setdefault(address, []):
                names.setdefault(address, name)
                people[address].append((anchor, title, over))
        rows = "".join(f'<li><span class="who" title="{html.escape(address, quote=True)}">{html.escape(names[address])}</span>'
                       f'<span class="cnt">{len(items)}</span><span class="what">'
                       + " · ".join(f'<span class="item" data-anchor="{a}"><a href="#{a}">{html.escape(t)}</a>'
                                    + (f' <span class="pill over">{html.escape(o)}</span>' if o else "") + "</span>" for a, t, o in items)
                       + "</span></li>" for address, items in people.items())
        cols.append(f'<div class="pcol"><h3>{head}</h3><p class="sub">{sub}</p>'
                    + (f"<ul>{rows}</ul>" if rows else '<p class="none">없습니다</p>') + "</div>")
    return '<div class="people" id="people" role="region" aria-label="사람별">' + "".join(cols) + "</div>"


UNREAD_TAIL = "을(를) 지금 읽지 못했습니다 — 아래가 비어 보여도 비어 있는 것이 아닙니다. 잠시 뒤 창을 다시 여시면 보입니다."   # 창의 스크립트도 이 글을 받는다


def unread_note(names: list[str]) -> str:
    """못 읽은 파일이 있을 때 「보고 맞추기」 머리에 서는 한 줄 — 비어 보이는 칸이 비어 있는 것이 아니라고 말한다. 없으면 빈 글."""
    return " · ".join(names) + UNREAD_TAIL if names else ""


def now_words(iso: str) -> str:
    """「M/D HH:MM」 — 창이 보이는 모습이 언제 것인가."""
    try:
        at = dt.datetime.fromisoformat(iso)
    except ValueError:
        return "이 보고를 지을 때"
    return T.moment_words(at)


AWAY_NOTE = ("켜 두시면 사람 없이 지은 보고를 본인 메일로도 한 통씩 보내 드립니다 — 휴대폰 메일로 보실 수 있습니다. 대화에서 청하신 보고는 안 "
             "보냅니다. 메일에서는 누를 수 없어, 맡길 일 · 끝났음은 이 창에서 하십니다.")


def away_to(away: dict) -> str:
    """받는 분의 한 줄 — 켰으면 켤 때 주소록에서 받은 본인 주소. 창에는 고칠 칸이 없다."""
    if away.get("on") and away.get("address"):
        return f"받는 분 — 본인({away['address']}) · 바꿀 수 없습니다"
    return "지금 꺼져 있습니다 — 받는 분은 본인뿐입니다(켜시면 주소록에서 본인 주소를 받습니다)"


def away_part(away: dict) -> str:
    """「자리 밖에서 보기」 칸 — 켜고 끄는 단추 하나와 받는 분 · 한 줄 설명. 단추는 처음엔 숨고 창의 스크립트가 거둘 수 있는 창에서만 꺼낸다 —
    아닌 창은 지금 켜졌나만 보인다."""
    on = "true" if away.get("on") else "false"
    return ('<h3>자리 밖에서 보기</h3><div class="away">'
            f'<button type="button" class="switch" id="away-switch" role="switch" aria-checked="{on}" hidden><span class="knob"></span>메일로도 받기</button>'
            f'<span class="away-to" id="away-to">{html.escape(away_to(away))}</span></div>'
            f'<p class="note">{html.escape(AWAY_NOTE)}</p><p class="note away-said" id="away-said" aria-live="polite"></p>')


def ask_panel(ready: bool, top: Task | None = None) -> str:
    """창 머리의 「비서에게 부탁하기」 — 칸 · 단추 · 한 줄 설명. 칸은 처음엔 숨고 그렇다는 한 줄이 선다 — 창의 스크립트가 거둘 수 있는
    창에서만 칸을 꺼내고 그 줄을 숨긴다. 이 PC 에 VS Code 의 Claude Code 가 없으면(`ready` 가 거짓) 칸 대신 그렇다는 한 줄만 선다.
    `top`(추천이 붙은 「대화로 할 일」)이 있으면 그 줄이 칸에 흐린 글로 서고 「추천」 표가 붙는다 — 치시면 사라지고, 그대로 누르시면 그 일의
    말(카드의 근거까지)로 연다. 치신 말은 지금처럼 그 말 그대로 연다."""
    if not ready:
        return f'<p class="ask-off">{html.escape(ASK_NO_VSCODE)}</p>'
    plain_ph = "예) 이번 주 일정 정리해 줘"
    if top is None:
        ph, cls, tag, hint, data = plain_ph, "", "", ASK_HINT, ""
    else:
        ph, cls, hint = top.line, ' class="suggest"', ASK_SUGGEST_HINT.format(title=top.card)
        tag = f'<span class="ask-tag" id="ask-tag">{TOP_MARK}</span>'
        data = attr(top=top.id, top_words=top.words(), top_line=top.line, plain=plain_ph, top_hint=hint, hint=ASK_HINT)
    return ('<div class="ask" id="ask" role="region" aria-labelledby="ask-label" hidden>'
            f'<label class="ask-label" id="ask-label" for="ask-in">비서에게 부탁하기{tag}</label>'
            f'<div class="ask-row"><textarea id="ask-in" rows="1" maxlength="{ASK_MAX}"{cls} placeholder="{html.escape(ph, quote=True)}"{data}></textarea>'
            '<button type="button" class="btn" id="ask-go">대화로 열기</button></div>'
            f'<p class="ask-hint" id="ask-hint">{html.escape(hint)}</p>'
            '<p class="ask-said" id="ask-said" aria-live="polite"></p></div>'
            f'<p class="tick-off" id="ask-off">{html.escape(ASK_OFF)}</p>')


def board_rows(ink: Ink) -> str:
    """편 목록의 줄 — 한 일에 한 줄(표시 칸 · 종류 · 카드 제목 · 표지 · 카드로 가는 닻). 무엇이 되나는 카드의 줄에만 선다."""
    rows = []
    for t, anchor in ink.tasks:
        where = f"카드 {t.num}" if t.num else "카드로"
        rows.append(f'<li class="brow"{attr(t=t.id)}><span class="b-tick"></span><span class="bline"><span class="kind">{t.kind}</span>'
                    f'<span class="btitle">{html.escape(t.card)}</span></span><span class="b-st"></span>'
                    f'<a class="bcard" href="#{anchor}">{html.escape(where)}</a></li>')
    return "".join(rows)


def board_bar(end: bool) -> str:
    """막대의 첫 줄 — 제목 · 셈(창의 스크립트가 채운다) · 맡긴 뒤의 표지 · (위에만) 목록 펴기 · 누름."""
    toggle = "" if end else (f'<button type="button" class="bar-toggle" aria-expanded="false" aria-controls="brows" data-open="{LIST_OPEN}" '
                             f'data-close="{LIST_CLOSE}">{LIST_OPEN}</button>')
    return (f'<div class="bar"><p class="bar-what"><span class="board-title">{BOARD_TITLE}</span><span class="bar-n"></span>'
            '<span class="bar-kinds" hidden></span><span class="st bar-st" hidden></span></p>'
            f'{toggle}<button type="button" class="btn board-go"></button></div>')


def board_panel(ink: Ink) -> str:
    """머리 칸 아래의 「바로 맡길 일」 — 처음엔 접힌 막대 하나. 맡길 일이 없는 보고에는 안 선다. 막대는 처음엔 숨는다 — 창의 스크립트가 누름을
    남길 수 있는 창에서만 꺼낸다."""
    if not ink.tasks:
        return ""
    return (f'<div class="board top" id="board" role="region" aria-label="{BOARD_TITLE}" hidden>{board_bar(False)}'
            f'<p class="bar-hint">{html.escape(BAR_HINT)}</p><p class="board-said" aria-live="polite" hidden></p>'
            f'<ul class="brows" id="brows">{board_rows(ink)}</ul></div>')


def board_end(ink: Ink) -> str:
    """마지막 카드 뒤의 같은 누름 — 카드를 다 읽은 자리에서 맡긴다. 셈 · 단추 · 상태는 머리 칸 아래 막대와 한 몸이고, 뺀 것을 이름으로 댄다."""
    if not ink.tasks:
        return ""
    return (f'<div class="board end" role="region" aria-label="{BOARD_TITLE} — 맨 아래" hidden>{board_bar(True)}'
            f'<p class="bar-hint">{html.escape(END_HINT)}</p><p class="board-said" aria-live="polite" hidden></p>'
            '<p class="end-left" hidden></p></div>')


def prefs_panel(state: dict, prefs: P.Prefs, ink: Ink) -> str:
    """보고 맞추기 — 보고 시각(고르시면 스캔이 받아 건다) · 올리지 않기로 한 것(「다시 올리기」) · 내일 다시 볼 것. 고르는 칸은 처음엔 숨고
    창의 스크립트가 표시를 거둘 수 있는 창에서만 꺼낸다 — 아닌 창은 지금 값만 보인다."""
    times = state["times"] or None
    if times is None:
        when = '<p class="pref-none" id="times-none">사람 없는 보고가 걸려 있지 않습니다 — 대화에서 「보고 시각 걸어 줘」 하시면 겁니다.</p>'
    else:
        chips = "".join(f'<span class="chip" data-time="{t}">{t}<button type="button" class="chip-x" data-drop="{t}" hidden '
                        f'aria-label="{t} 빼기">빼기</button></span>' for t in times)
        when = (f'<div class="chips" id="times" data-times="{" ".join(times)}">{chips}'
                '<span class="add-time" hidden><input type="time" id="time-new" aria-label="더할 시각"><button type="button" class="btn ghost" '
                'id="time-add">더하기</button></span><button type="button" class="btn" id="times-save" hidden>이대로 바꾸기</button></div>'
                f'<p class="note">시각마다 다음 시각까지 사내 로그인을 기다려 한 번 띄웁니다.{TIMES_LOGIN}</p>'
                '<p class="note times-said" id="times-said" aria-live="polite"></p>' + away_part(state["away"]))
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
            + f'<p class="note no" id="prefs-unread"{"" if state["unread"] else " hidden"}>{html.escape(unread_note(state["unread"]))}</p>'
            + f'<h3>보고 시각</h3>{when}'
            f'<h3>올리지 않기로 한 것</h3><ul class="pref-list" id="quiet-list">{quiet}</ul>'
            + f'<p class="pref-none" id="quiet-none"{" hidden" if quiet else ""}>없습니다</p>'
            + f'<h3 id="later-head"{"" if later else " hidden"}>내일 다시 볼 것</h3><ul class="pref-list" id="later-list">{later}</ul>'
            + '<p class="tick-off" id="prefs-off">이 창에서는 고르실 수 없습니다 — 대화에서 말씀해 주세요.</p></aside>')


def build(rep: Report, ink: Ink, now: dt.datetime, state: dict, prefs: P.Prefs, ready: bool) -> tuple[str, int, int]:
    """틀에 채운 HTML · 절 수 · 줄 수 — 맡길 일 미리 가르기 → 머리 → 절 → 머리 아래 패널 → 왼쪽 목록 → 끝의 막대 · 보고 맞추기 → 틀 채우기.
    `state` 는 창이 보이는 지금 모습(`state.state_of` — 그 `signed` 가 머리의 한 줄을 정한다), `prefs` 는 보고 맞춤, `ready` 는 이 PC 에 VS Code 의 Claude Code 가 있나(`asks.ready`)
    — 그리기는 사용자 폴더 · 이 PC 를 읽지 않는다."""
    ink.ready = ready
    top = sort_tasks(rep, ink)
    toc: list[str] = []
    hero, head_lines = head_part(rep, ink, now, toc, state["signed"])
    sections, records_at, body_lines = section_parts(rep, ink, toc)
    people = people_panel(ink)
    hero += head_panels(ink, top, people)
    side_list(toc, ink, people)
    tail_parts(sections, records_at, ink, state, prefs, toc)
    return filled(rep.title or "", ink, toc, hero, sections), len(sections) - 2, head_lines + body_lines


def sort_tasks(rep: Report, ink: Ink) -> Task | None:
    """맡길 일을 줄마다 미리 가르고(창 곁의 손이 같은 글에서 내는 번호와 같게 — `tasks_of`) 창 머리에 올릴 추천을 고른다 — `ink` 에 적고 그
    추천을 낸다. 추천은 보고 하나에 하나 — 둘 넘게 적혔으면 아무것도 안 올리고(끝 줄 앞에서 경고한다) None."""
    seen: dict[str, int] = {}
    for it in report_items(rep):
        got = take_card(it, seen)[0]
        if got:
            ink.item_tasks[id(it)] = got
    tops = [t for ts in ink.item_tasks.values() for t in ts if t.row.via == VIA_TALK and t.top]
    top = tops[0] if len(tops) == 1 else None
    ink.top_id, ink.tops = (top.id if top else None), len(tops)
    return top


def head_part(rep: Report, ink: Ink, now: dt.datetime, toc: list[str], signed: dict | None) -> tuple[list[str], int]:
    """창 머리 — 제목 · 머리글(첫 문단) · 지은 때 · 스스로 로그인해 지은 보고의 한 줄(`signed` 의 범위 안일 때만) · 제목 밑 덩이 — 와 그 덩이의
    줄 수. 지은 때는 창의 스크립트가 이보다 먼저 거둔 표시를 이 창에서 안 쓰는 기준이다(report.js)."""
    head_blocks = list(rep.sections[0].blocks)
    hero = [f"<h1>{ink.inline(rep.title or '')}</h1>"]
    if head_blocks and head_blocks[0].kind == "para":
        hero.append(f'<p class="lede">{ink.inline(" ".join(head_blocks.pop(0).lines))}</p>')
    made = T.stamp(now.astimezone())
    hero.append(f'<p class="dateline" data-made="{made}">{DATELINE.format(now, WEEKDAYS[now.weekday()], now)}</p>')
    hero += [note for note in [signed_note(signed, now)] if note]
    hero.append(render_blocks(head_blocks, ink, "s0", toc, head=True))
    return hero, sum(len(b.lines) for b in head_blocks if b.kind == "list")


def section_parts(rep: Report, ink: Ink, toc: list[str]) -> tuple[list[str], int | None, int]:
    """절마다의 HTML(빈 「끝났다고 하신 것」은 안 세운다) · 끝의 기록 절이 시작하는 자리(맨 아래의 누름은 마지막 카드 뒤, 그 앞에 선다) · 줄 수.
    왼쪽 목록에 절과 그 작은 절을 더한다."""
    sections, lines, records_at = [], 0, None
    for n, sec in enumerate(rep.sections[1:], 1):
        if is_empty_done(sec):
            continue
        if records_at is None and names_section(sec.title, RECORD_SECTIONS):
            records_at = len(sections)
        sid = f"s{n}"
        toc.append(f'<li><a href="#{sid}">{ink.inline(sec.title or "", links=False)}</a></li>')
        sub_toc: list[str] = []
        body = render_blocks(sec.blocks, ink, sid, sub_toc, head=False, tick=section_tick(sec.title))
        toc += sub_toc
        lines += sum(len(b.lines) for b in sec.blocks if b.kind == "list")
        sections.append(f'<section id="{sid}" aria-labelledby="h-{sid}"><h2 id="h-{sid}">{ink.inline(sec.title or "")}</h2>'
                        f"{body}</section>")
    return sections, records_at, lines


def head_panels(ink: Ink, top: Task | None, people: str) -> list[str]:
    """머리 아래의 패널 — 거둘 수 없는 창의 한 줄(단추 · 맡길 일이 서는 창만) · 부탁 칸 · 「바로 맡길 일」 막대 · 사람별(있을 때만)."""
    out = [f'<p class="tick-off" id="tick-off" hidden>{html.escape(TICK_ASK_OFF if ink.ready else TICK_OFF)}</p>'] if ink.boxes or ink.tasks else []
    return out + [ask_panel(ink.ready, top), board_panel(ink)] + ([people] if people else [])


def side_list(toc: list[str], ink: Ink, people: str) -> None:
    """왼쪽 목록의 머리 칸을 창의 차례대로 끼운다 — 머리 칸 아래의 막대가 사람별보다 위다(`toc` 를 고친다)."""
    if people:
        toc.insert(1 if toc and toc[0].startswith('<li><a href="#top">') else 0, '<li><a href="#people">사람별</a></li>')
    if ink.tasks:
        toc.insert(1 if toc and toc[0].startswith('<li><a href="#top">') else 0,
                   f'<li><a href="#board">{BOARD_TITLE} {len(ink.tasks)}</a></li>')


def tail_parts(sections: list[str], records_at: int | None, ink: Ink, state: dict, prefs: P.Prefs, toc: list[str]) -> None:
    """끝의 덩이 — 맨 아래의 「바로 맡길 일」은 기록 절 앞(없으면 끝), 「보고 맞추기」는 맨 끝에 — 와 그 목록 줄(`sections` · `toc` 를 고친다)."""
    sections.insert(len(sections) if records_at is None else records_at, board_end(ink))
    sections.append(prefs_panel(state, prefs, ink))
    toc.append('<li><a href="#prefs">보고 맞추기</a></li>')


def filled(title: str, ink: Ink, toc: list[str], hero: list[str], sections: list[str]) -> str:
    """틀(`assets/report.html`)에 창의 이름 · 왼쪽 목록 · 머리 · 절 · 스크립트와 그 CSP 해시를 채운 HTML."""
    template = string.Template(TEMPLATE.read_text(encoding="utf-8"))
    code, script_hash = page_script()
    return template.substitute(
        page_title=html.escape(plain(title), quote=True),
        side_title=ink.inline(title, links=False),
        toc="\n".join(toc),
        hero="\n".join(hero),
        sections="\n".join(sections),
        script=code,
        script_hash=script_hash,
    )
