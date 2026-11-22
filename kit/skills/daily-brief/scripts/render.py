"""보고 글을 그린다 — 읽은 보고 글(`brief_text.Report`)과 창이 보이는 지금 모습을 보고 창의 HTML(`build` · 틀 `assets/report.html` · 스크립트
`assets/report.js`)로, 같은 글을 휴대폰 너비의 메일 한 장(`mail_sheet`)으로. 줄 안의 꼴은 한 걸음(`inline_walk`)이 읽고 겉(창 · 메일)만 둘이다.
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
import prefs_file as P  # noqa: E402
from brief_const import (ASK_KEY, ASK_NO_VSCODE, ASK_OPEN_CEILING_S, ASK_TAKE_S, AWAY_KEY, CAL_PREFIX, DONE_PREFIX, HAND_BEAT_S,  # noqa: E402
                         HAND_KEY, KIND_CAL, KIND_ROOM, KIND_TEAMS, RUN_PREFIX, RUN_REFUSED, RUN_TAKE_S, STATE_KEY, TASK_BAD,
                         TASK_PREFIX, TIMES_KEY, UNQUIET_PREFIX, VIA_EDGE, WEEKDAYS)
from brief_text import (BULLET, DASH, DONE_SECTION, INLINE, KINDS, LEAD_BOLD, OVER, PUT_FIELD, RECORD_SECTIONS,  # noqa: E402
                        TALK_KIND, TOP_MARK, UNID, WAIT_ME, WAIT_THEM, Block, Item, Report, Task, is_empty_done, is_meetings, item_key,
                        item_title, parse, people_in, plain, report_items, take_card)

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "assets" / "report.html"
SCRIPT = TEMPLATE.with_name("report.js")      # 창의 하나뿐인 스크립트 — 누르신 표시 · 고르신 시각. CSP 는 지을 때마다 이 글의 해시만 연다
DATELINE = "{:%Y-%m-%d}({}) {:%H:%M} 지음"

ASK_MAX = 1000                                 # 칸이 받는 글자 수 — 두 번 인코딩한 주소가 Windows 명령 줄 한도의 절반 남짓에 든다
ASK_OFF = "이 창은 메일 비서의 Edge 밖에서 열려 여기서는 부탁하실 수 없습니다 — 대화에서 말씀해 주세요."
ASK_HINT = "누르시면 VS Code 의 작업 폴더 창에 새 대화가 열리고 이 말이 입력 칸에 채워집니다 — 엔터를 누르셔야 시작합니다."
PUT_BAD = "넣을 값의 꼴이 틀려 이 창에서는 넣을 수 없습니다 — 대화에서 「그 약속 넣어 줘」 하시면 넣습니다"
PUT_NOKEY = "이 창에서는 넣지 않습니다 — 까닭은 위 카드에 적었습니다"
NO_TIME_SAID = "메일에 시각이 없어 넣지 못합니다 — 시각을 정해 대화에서 「그 약속 ○시로 넣어 줘」 하시면 넣습니다."
TALK_CONS = "누르시면 이 카드의 근거와 함께 VS Code 에 대화를 엽니다 — 엔터를 누르셔야 시작합니다"
TOP_TAG = "· 창 맨 위에 추천으로 올린 일"
TASK_GO, TALK_GO = "이것만 맡기기", "대화로 열기"
TICK_LABEL = "바로 맡길 일에 넣기"
LATE_WORDS = {KIND_ROOM: "지난 회의라 잡지 않습니다", KIND_TEAMS: "지난 회의라 띄우지 않습니다"}
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


def inline_walk(text: str, skin) -> str:
    """줄 안의 꼴을 왼쪽부터 읽어 겉(`skin` — 창 · 메일)으로 짓는다: 고정 글자 · 메일 링크 · 사람 · 회의실 · 표지 · 굵게. 꼴 밖의 글과 꼴이
    아닌 표시(번호가 아닌 mail: · 빈 표지)는 이스케이프해 쓴 그대로 둔다. 링크 글 속은 겉의 `inside()` 로 한 번 더 읽는다."""
    out, at = [], 0
    for m in INLINE.finditer(text):
        out.append(html.escape(text[at:m.start()], quote=True))
        at = m.end()
        if m.group("code") is not None:
            out.append(skin.code(m.group("code")))
        elif m.group("ref") is not None:
            ref, label = m.group("ref"), m.group("label")
            if not UNID.match(ref):
                skin.bad_ref()
                out.append(html.escape(m.group(0), quote=True))
                continue
            inner = inline_walk(label, skin.inside()) if label.strip() else html.escape(ref.upper(), quote=True)
            out.append(skin.mail(inner, ref))
        elif m.group("pref") is not None:
            out.append(skin.person(inline_walk(m.group("plabel"), skin.inside()), m.group("pref").strip()))
        elif m.group("rref") is not None:
            out.append(skin.room(inline_walk(m.group("rlabel"), skin.inside()), m.group("rref")))
        elif m.group("sref") is not None:              # 절의 종류 표지 — 사람에게는 이름만 선다
            out.append(inline_walk(m.group("slabel"), skin))
        elif m.group("pill") is not None:
            words = m.group("pill").strip()
            out.append(skin.pill(words, bool(m.group("over"))) if words else html.escape(m.group(0), quote=True))
        else:
            out.append(skin.bold(inline_walk(m.group("bold"), skin)))
    out.append(html.escape(text[at:], quote=True))
    return "".join(out)


class WindowSkin:
    """창의 겉 — 메일 링크는 웹메일에서 그 메일을 여는 링크(`Ink.mail` 이 센다), 사람 · 회의실은 이름이 서고 주소 · id 는 올리면 보이는 표,
    표지는 둥근 표, 굵게는 <strong>. `links` 가 거짓이면 링크 · 사람 · 회의실의 겉 없이 글만 — 같은 글을 링크 없이 한 번 더 짓는 자리라
    번호가 아닌 mail: 표시도 안 센다."""

    def __init__(self, ink: Ink, links: bool = True):
        self.ink, self.links = ink, links

    def inside(self) -> WindowSkin:
        return WindowSkin(self.ink, False)

    def code(self, words: str) -> str:
        return f"<code>{html.escape(words, quote=True)}</code>"

    def bad_ref(self) -> None:
        self.ink.bad_refs += self.links

    def mail(self, inner: str, unid: str) -> str:
        return self.ink.mail(inner, unid) if self.links else inner

    def person(self, inner: str, addr: str) -> str:
        return f'<span class="person" title="{html.escape(addr, quote=True)}">{inner}</span>' if self.links else inner

    def room(self, inner: str, rid: str) -> str:
        return f'<span class="room" title="{html.escape(rid, quote=True)}">{inner}</span>' if self.links else inner

    def pill(self, words: str, over: bool) -> str:
        return f'<span class="{"pill over" if over else "pill"}">{html.escape(words, quote=True)}</span>'

    def bold(self, inner: str) -> str:
        return f"<strong>{inner}</strong>"


def attr(**kv: str | None) -> str:
    """`data-…` 속성 — 값이 None 이면 뺀다. 이름의 「_」는 「-」로."""
    return "".join(f' data-{k.replace("_", "-")}="{html.escape(v, quote=True)}"' for k, v in kv.items() if v is not None)


def todo_block(tasks: list[Task], ink: Ink, anchor: str, top_id: str | None, ready: bool) -> str:
    """카드 끝의 할 일 칸 — 「바로 할 일」마다 표시 칸 · 줄 · 무엇이 되나 · 「이것만 맡기기」, 「대화로 할 일」마다 「대화로 열기」.
    표시 칸 · 단추는 처음엔 숨는다 — 창의 스크립트가 누름을 남길 수 있는 창에서만 꺼낸다(스크립트가 막혀도 누를 수 없는 단추는 안 선다).
    `ready` 가 거짓(이 PC 에 VS Code 의 Claude Code 가 없다)이면 「대화로 열기」를 안 세운다. 꼴이 틀린 칸은 적힌 글 그대로와 그렇다는 말."""
    out = []
    for t in tasks:
        if not t.kind:
            if t.field == PUT_FIELD:
                ink.bad_puts += 1
            else:
                ink.bad_tasks.append(f"{t.field}: {t.written}")
            out.append(f'<div class="todo-row bad"><span class="todo-what"><span class="kind">{html.escape(t.field)}</span>'
                       f'{html.escape(t.written)}<span class="todo-cons no">{html.escape(TASK_BAD if t.field != PUT_FIELD else PUT_BAD)}'
                       '</span></span></div>')
            continue
        if t.kind == TALK_KIND:
            is_top = ready and t.id == top_id
            tag = f'<span class="top-tag">{html.escape(TOP_TAG)}</span>' if is_top else ""
            cons = f'<span class="todo-cons">{html.escape(TALK_CONS)}</span>' if ready else ""
            go = f'<button type="button" class="put ghost talk-go" hidden>{TALK_GO}</button>' if ready else ""
            out.append(f'<div class="todo-row"{attr(talk=t.id, words=t.words(), line=t.line(), top="1" if is_top else None)}>'
                       f'<span class="todo-what"><span class="kind talk">{TALK_KIND}</span>「{html.escape(t.line())}」{tag}{cons}</span>{go}</div>'
                       '<p class="put-note" aria-live="polite"></p>')
            continue
        if t.put is not None and not t.put.key:   # 열쇠를 못 받은 일정 넣기 — 까닭은 마무리(`finish.py`)가 카드의 점으로 넣었다
            out.append(f'<div class="todo-row bad"><span class="todo-what"><span class="kind">{html.escape(t.kind)}</span>{html.escape(t.line())}'
                       f'<span class="todo-cons no">{html.escape(PUT_NOKEY)}</span></span></div>')
            continue
        short, _, head, tail = KINDS[t.kind]
        ink.tasks.append((t, anchor))
        label = f"{TICK_LABEL} — " + (f"카드 {t.num} " if t.num else f"「{t.card}」 ") + t.kind
        data = attr(t=t.id, kind=t.kind, k=short, c=t.num or "", title=t.card, anchor=anchor, line=t.line(), head=head, tail=tail or None,
                    start=t.start() or None, late=LATE_WORDS.get(t.kind), ev="\n".join(t.evidence))
        key = attr(key=t.put.key, start=t.put.start) if t.put else ""
        out.append(f'<div class="todo-row"{data}><span class="todo-tick" hidden><input type="checkbox" checked{attr(t=t.id)} '
                   f'aria-label="{html.escape(label, quote=True)}"></span><span class="todo-what"><span class="kind">{t.kind}</span>'
                   f'{html.escape(t.line())}<span class="todo-cons">{html.escape(t.cons())}</span></span>'
                   f'<button type="button" class="put task-go"{key} aria-pressed="false" hidden>{TASK_GO}</button><span class="st" hidden></span></div>'
                   '<p class="put-note" aria-live="polite"></p><div class="run" hidden></div>')
    return f'<div class="todo">{"".join(out)}</div>' if out else ""


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
    if points or tasks or no_time:
        m = LEAD_BOLD.match(it.text)
        head, rest = (m.group("head"), m.group("rest")) if m else (it.text, "")
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
        elif no_time:
            parts.append(f'<p class="no-time">{html.escape(NO_TIME_SAID)}</p>')
        body = "".join(parts)
        dated = any(t.kind in (KIND_CAL, KIND_ROOM, KIND_TEAMS) or (t.field == PUT_FIELD) for t in tasks)
        appt = " appt" if tick == TICK_TODO and (dated or no_time) else ""
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
    return TICK_NONE if name.startswith(RECORD_SECTIONS) or is_meetings(title) else TICK_TODO


def page_script() -> tuple[str, str]:
    """창에 싣는 스크립트와 그것만 여는 CSP 칸(`'sha256-…'`). 해시는 실을 글 그대로에서 낸다 — 손으로 옮긴 해시는 없다."""
    code = string.Template(SCRIPT.read_text(encoding="utf-8")).substitute(done_prefix=DONE_PREFIX, via_edge=VIA_EDGE, times_key=TIMES_KEY,
                                                                          unquiet_prefix=UNQUIET_PREFIX, state_key=STATE_KEY,
                                                                          cal_prefix=CAL_PREFIX, hand_key=HAND_KEY, away_key=AWAY_KEY,
                                                                          hand_stale_ms=str(3 * HAND_BEAT_S * 1000), ask_key=ASK_KEY,
                                                                          ask_take_ms=str(ASK_TAKE_S * 1000), run_prefix=RUN_PREFIX,
                                                                          task_prefix=TASK_PREFIX, run_take_ms=str(RUN_TAKE_S * 1000), run_refused=RUN_REFUSED, kind_teams=KIND_TEAMS, unread_tail=UNREAD_TAIL,
                                                                          ask_open_ms=str((ASK_OPEN_CEILING_S + ASK_TAKE_S) * 1000))
    digest = base64.b64encode(hashlib.sha256(code.encode("utf-8")).digest()).decode("ascii")
    return code, f"'sha256-{digest}'"


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
    return f"{at.month}/{at.day} {at:%H:%M}"


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
        ph, cls, hint = top.line(), ' class="suggest"', ASK_SUGGEST_HINT.format(title=top.card)
        tag = f'<span class="ask-tag" id="ask-tag">{TOP_MARK}</span>'
        data = attr(top=top.id, top_words=top.words(), top_line=top.line(), plain=plain_ph, top_hint=hint, hint=ASK_HINT)
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
    times, login = state["times"] or None, state["login"]
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
    """틀에 채운 HTML · 절 수 · 줄 수. `state` 는 창이 보이는 지금 모습(`state.state_of`), `prefs` 는 보고 맞춤, `ready` 는 이 PC 에 VS Code 의
    Claude Code 가 있나(`asks.ready`) — 그리기는 사용자 폴더 · 이 PC 를 읽지 않는다."""
    template = string.Template(TEMPLATE.read_text(encoding="utf-8"))
    toc: list[str] = []
    ink.ready = ready
    seen: dict[str, int] = {}
    for it in report_items(rep):                   # 맡길 일을 미리 가른다 — 창 곁의 손이 같은 글에서 내는 번호와 같게(`tasks_of`)
        got = take_card(it, seen)[0]
        if got:
            ink.item_tasks[id(it)] = got
    tops = [t for ts in ink.item_tasks.values() for t in ts if t.kind == TALK_KIND and t.top]
    top = tops[0] if len(tops) == 1 else None      # 추천은 보고 하나에 하나 — 둘 넘게 적혔으면 아무것도 안 올리고 경고한다
    ink.top_id, ink.tops = (top.id if top else None), len(tops)
    title = rep.title or ""
    head_blocks = list(rep.sections[0].blocks)
    hero = [f"<h1>{ink.inline(title)}</h1>"]
    if head_blocks and head_blocks[0].kind == "para":
        hero.append(f'<p class="lede">{ink.inline(" ".join(head_blocks.pop(0).lines))}</p>')
    made = now.astimezone().isoformat(timespec="seconds")      # 창의 스크립트가 이보다 먼저 거둔 표시를 이 창에서 안 쓴다(report.js)
    hero.append(f'<p class="dateline" data-made="{made}">{DATELINE.format(now, WEEKDAYS[now.weekday()], now)}</p>')
    hero.append(render_blocks(head_blocks, ink, "s0", toc, head=True))
    sections, lines = [], sum(len(b.lines) for b in head_blocks if b.kind == "list")
    records_at = None                              # 끝의 기록 절이 시작하는 자리 — 맨 아래의 누름은 마지막 카드 뒤, 그 앞에 선다
    for n, sec in enumerate(rep.sections[1:], 1):
        if is_empty_done(sec):
            continue
        if records_at is None and plain(sec.title or "").strip().startswith(RECORD_SECTIONS):
            records_at = len(sections)
        sid = f"s{n}"
        toc.append(f'<li><a href="#{sid}">{ink.inline(sec.title or "", links=False)}</a></li>')
        sub_toc: list[str] = []
        body = render_blocks(sec.blocks, ink, sid, sub_toc, head=False, tick=section_tick(sec.title))
        toc += sub_toc
        lines += sum(len(b.lines) for b in sec.blocks if b.kind == "list")
        sections.append(f'<section id="{sid}" aria-labelledby="h-{sid}"><h2 id="h-{sid}">{ink.inline(sec.title or "")}</h2>'
                        f"{body}</section>")
    if ink.boxes or ink.tasks:
        hero.append(f'<p class="tick-off" id="tick-off" hidden>{html.escape(TICK_ASK_OFF if ink.ready else TICK_OFF)}</p>')
    hero.append(ask_panel(ink.ready, top))
    hero.append(board_panel(ink))
    people = people_panel(ink)
    if people:
        hero.append(people)
        toc.insert(1 if toc and toc[0].startswith('<li><a href="#top">') else 0, '<li><a href="#people">사람별</a></li>')
    if ink.tasks:                                  # 왼쪽 목록도 창의 차례대로 — 머리 칸 아래의 막대가 사람별보다 위다
        toc.insert(1 if toc and toc[0].startswith('<li><a href="#top">') else 0,
                   f'<li><a href="#board">{BOARD_TITLE} {len(ink.tasks)}</a></li>')
    sections.insert(len(sections) if records_at is None else records_at, board_end(ink))
    sections.append(prefs_panel(state, prefs, ink))
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
    return page, len(sections) - 2, lines


# ── 메일 한 장 — 자리 밖에서 보기 ─────────────────────────────────────────────
# 같은 보고 글에서 휴대폰 너비의 메일 한 장을 짓는다. 메일 프로그램은 <style> · 스크립트 · 바깥 글꼴을 거르므로 꾸밈은 다 줄마다의 style
# 속성에 든다. 누름 단추가 없고, 링크도 없다 — 근거 메일은 보고 글이 쓴 그 글(보낸 분 · 날짜 · 제목)로 선다(사내 웹메일 링크가 휴대폰 메일
# 앱에서 열리는지 안 쟀다). 글은 다 이스케이프한다 — 창과 같다.
MAIL_TAG = "[메일 비서]"
SUBJECT_MAX = 140                              # 제목의 글자 수 — 메일 목록에서 잘리는 만큼보다 넉넉히, 한 줄을 넘는 머리말은 자른다
# 맡길 일이 든 절의 머리에 서는 한 줄 — 메일에서는 누를 수 없어 어디서 맡기나를 댄다. 카드의 할 일은 줄의 글로만 선다
MAIL_TASK_INTRO = "맡기시려면 PC 의 보고 창에서 누르세요 — 메일에서는 맡기실 수 없습니다."
MAIL_TASK_BAD = "적힌 꼴이 틀려 창에서도 맡기실 수 없습니다 — 대화에서 말씀해 주세요"
MAIL_META = "{slot} 사람 없이 지은 보고 · PC 의 보고 창에 같은 보고가 떠 있습니다"
MAIL_FOOT = ("「자리 밖에서 보기」를 켜 두셔서 보내 드렸습니다 — 이 메일은 본인에게만 갑니다. 그만 받으시려면 PC 의 보고 창 끝 「보고 맞추기」에서 "
             "끄시거나, 대화에서 「보고 메일 그만 보내」 하세요.")
MS_SERIF = "font-family:'Noto Serif KR','Nanum Myeongjo',Batang,serif;"
MS = {
    "body": "margin:0;padding:0;background:#FAFAF9;",
    "sheet": ("max-width:600px;margin:0 auto;padding:16px;font-family:'Malgun Gothic','맑은 고딕','Noto Sans KR',sans-serif;font-size:15px;"
              "line-height:1.65;color:#1C1917;word-break:keep-all;overflow-wrap:anywhere;"),
    "eyebrow": "margin:0;font-size:11px;letter-spacing:0.08em;color:#78716C;font-weight:600;",
    "h1": f"margin:4px 0 6px;{MS_SERIF}font-size:26px;line-height:1.25;font-weight:600;",
    "lede": "margin:0;font-size:16px;color:#57534E;",
    "meta": "margin:8px 0 0;font-size:13px;color:#78716C;",
    "clock": "margin:20px 0 0;padding:14px 16px;background:#F5F5F4;border:1px solid #D6D3D1;border-radius:12px;",
    "clock_label": "margin:0 0 8px;font-size:13px;font-weight:600;color:#57534E;",
    "clock_row": "margin:4px 0 0;",
    "clock_t": "font-size:18px;",
    "aside": "color:#57534E;font-size:13px;",
    "h2": f"margin:28px 0 10px;padding-bottom:8px;border-bottom:1px solid #D6D3D1;{MS_SERIF}font-size:20px;font-weight:600;",
    "h3": "margin:18px 0 8px;font-size:16px;font-weight:600;",
    "intro": "margin:0 0 10px;font-size:14px;color:#57534E;",
    "card": "margin:0 0 10px;padding:14px 16px;background:#F5F5F4;border:1px solid #D6D3D1;border-radius:12px;",
    "card_appt": "margin:0 0 10px;padding:14px 16px;background:#F5F5F4;border:1px solid #D6D3D1;border-left:4px solid #C2410C;border-radius:12px;",
    "card_title": "margin:0;font-weight:600;font-size:16px;",
    "card_when": "margin:2px 0 0;font-size:14px;color:#57534E;",
    "point": "margin:6px 0 0;font-size:14px;",
    "facts": "margin:8px 0 0;font-size:13px;color:#57534E;",
    "put": "margin:8px 0 0;font-size:13px;color:#57534E;",
    "put_said": "margin:4px 0 0;font-size:13px;color:#78716C;",
    "row": "margin:0 0 6px;font-size:14px;",
    "para": "margin:0 0 10px;font-size:14px;",
    "caution": "margin:0 0 10px;padding:12px 14px;border:1px solid #F59E0B;border-radius:12px;background:#FFFBEB;font-size:14px;",
    "pill": "display:inline-block;padding:0 8px;border-radius:9999px;background:#E7E5E4;color:#57534E;font-size:12px;line-height:1.8;",
    "pill_over": "display:inline-block;padding:0 8px;border-radius:9999px;background:#DC2626;color:#FAFAF9;font-size:12px;line-height:1.8;",
    "foot": "margin:28px 0 0;padding-top:12px;border-top:1px solid #D6D3D1;font-size:12px;color:#78716C;line-height:1.7;",
}


class MailSkin:
    """메일의 겉 — 메일 프로그램은 <style> 을 거르므로 꾸밈은 줄마다의 style 속성에 든다. 고정 글자는 글만, 메일 링크는 그 글만(링크 없이 —
    글 없는 링크는 창처럼 메일 번호로 선다), 사람은 이름만(주소는 메일 한 장에 안 싣는다), 회의실도 방 이름만, 굵게는 <b>."""

    def inside(self) -> MailSkin:
        return self

    def code(self, words: str) -> str:
        return html.escape(words, quote=True)

    def bad_ref(self) -> None:
        pass

    def mail(self, inner: str, unid: str) -> str:
        return inner

    def person(self, inner: str, addr: str) -> str:
        return inner

    def room(self, inner: str, rid: str) -> str:
        return inner

    def pill(self, words: str, over: bool) -> str:
        return f'<span style="{MS["pill_over" if over else "pill"]}">{html.escape(words, quote=True)}</span>'

    def bold(self, inner: str) -> str:
        return f"<b>{inner}</b>"


def mail_inline(text: str) -> str:
    """줄 안 — 메일의 겉(`MailSkin`)으로. 창과 같은 걸음(`inline_walk`)이 같은 꼴을 읽는다."""
    return inline_walk(text, MailSkin())


def mail_plain(text: str) -> str:
    """평문 짝의 한 줄 — 꼴 표시를 걷은 맨글자(메일 링크는 그 글만)."""
    return " ".join(plain(text).split())


def mail_item(it: Item, html_out: list[str], text_out: list[str]) -> None:
    """줄 하나 — 점 · 칸 · 맡길 일이 딸리면 카드, 아니면 한 줄. 맡길 일은 종류와 사람이 읽는 줄(창의 줄과 같은 글)로 선다 — 어디서 누르나는 그
    절의 머리에 선 한 줄이 댄다(`MAIL_TASK_INTRO`)."""
    tasks, points, facts, no_time = take_card(it)
    if not (points or tasks or no_time):
        tail = "".join(f" ({mail_inline(k)}: {mail_inline(v)})" for k, v in facts)
        html_out.append(f'<p style="{MS["row"]}">{mail_inline(it.text)}{tail}</p>')
        text_out.append("- " + mail_plain(it.text) + "".join(f" ({mail_plain(k)}: {mail_plain(v)})" for k, v in facts))
        return
    m = LEAD_BOLD.match(it.text)
    head, rest = (m.group("head"), m.group("rest")) if m else (it.text, "")
    parts = [f'<p style="{MS["card_title"]}">{mail_inline(head)}</p>']
    text_out.append("- " + mail_plain(head) + (f" — {mail_plain(rest)}" if rest else ""))
    if rest:
        parts.append(f'<p style="{MS["card_when"]}">{mail_inline(rest)}</p>')
    parts += [f'<p style="{MS["point"]}">{mail_inline(p)}</p>' for p in points]
    text_out += [f"  · {mail_plain(p)}" for p in points]
    if facts:
        parts.append(f'<p style="{MS["facts"]}">' + "<br>".join(f"<b>{mail_inline(k)}</b> {mail_inline(v)}" for k, v in facts) + "</p>")
        text_out += [f"  {mail_plain(k)}: {mail_plain(v)}" for k, v in facts]
    for t in tasks:
        what = (f"{t.kind} — {t.line()}" if t.kind and t.kind != TALK_KIND else f"{TALK_KIND} — 「{t.line()}」" if t.kind
                else f"{t.field}: {t.written} — {MAIL_TASK_BAD}")
        parts.append(f'<p style="{MS["put" if t.kind else "put_said"]}">{html.escape(what)}</p>')
        text_out.append(f"  {what}")
    if no_time and not tasks:
        parts.append(f'<p style="{MS["put_said"]}">{html.escape(NO_TIME_SAID)}</p>')
        text_out.append(f"  {NO_TIME_SAID}")
    dated = any(t.kind in (KIND_CAL, KIND_ROOM, KIND_TEAMS) or t.field == PUT_FIELD for t in tasks)
    html_out.append(f'<div style="{MS["card_appt" if dated or no_time else "card"]}">' + "".join(parts) + "</div>")


def mail_blocks(blocks: list[Block], html_out: list[str], text_out: list[str]) -> None:
    """덩이를 차례대로 — 문단 · 줄 · 작은 절 · 주의 상자 · 시간줄."""
    for b in blocks:
        if b.kind == "para":
            words = " ".join(b.lines)
            html_out.append(f'<p style="{MS["intro"]}">{mail_inline(words)}</p>')
            text_out.append(mail_plain(words))
        elif b.kind == "sub":
            html_out.append(f'<p style="{MS["h3"]}">{mail_inline(b.lines[0])}</p>')
            text_out.append(f"[{mail_plain(b.lines[0])}]")
        elif b.kind == "list":
            for it in b.lines:
                mail_item(it, html_out, text_out)
        elif b.kind == "quote":
            words = [x for x in b.lines if x.strip()]
            html_out.append(f'<div style="{MS["caution"]}">' + "<br>".join(mail_inline(x) for x in words) + "</div>")
            text_out += [f"> {mail_plain(x)}" for x in words]
        elif b.kind == "clock":
            rows = []
            for line in b.lines:
                mark, desc, note = (DASH.split(line, maxsplit=2) + ["", ""])[:3]
                rows.append(f'<p style="{MS["clock_row"]}"><b style="{MS["clock_t"]}">{mail_inline(mark.strip())}</b> {mail_inline(desc.strip())}'
                            + (f' <span style="{MS["aside"]}">— {mail_inline(note.strip())}</span>' if note.strip() else "") + "</p>")
                text_out.append(" — ".join(mail_plain(x) for x in (mark, desc, note) if x.strip()))
            label = f'<p style="{MS["clock_label"]}">{mail_inline(" ".join(b.label))}</p>' if b.label else ""
            html_out.append(f'<div style="{MS["clock"]}">{label}' + "".join(rows)
                            + "".join(f'<p style="{MS["meta"]}">{mail_inline(a)}</p>' for a in b.after) + "</div>")


def task_section(blocks: list[Block]) -> bool:
    """맡길 일이 든 절인가 — 그 절의 머리에 어디서 맡기나를 한 줄 세운다."""
    return any(take_card(it)[0] for b in blocks for it in (b.lines if b.kind == "list" else ()))


def mail_sheet(text: str, made: dt.datetime, slot: str, slot_day: dt.date | None = None) -> dict:
    """보고 글 한 장 → 메일 한 장 {subject, html, text}. 창과 같은 글을 같은 꼴 읽기(`parse`)로 읽어 같은 사실을 다 싣고, 빈 「끝났다고 하신 것」은
    창처럼 뺀다. 제목은 「[메일 비서] 칸의 날 M/D(요일) 칸의 시각 보고 — 머리말」 — 머리말이 없으면 제목 줄이다. 칸의 날(`slot_day`)이 없으면
    지은 날이다. 끝의 「… 지음」은 늘 지은 때(`made`)다 — 저녁 칸의 보고가 자정 뒤에 지어지면 제목은 그 칸의 날, 지음은 다음 날이다."""
    rep = parse(text)
    head = list(rep.sections[0].blocks)
    lede = " ".join(head.pop(0).lines) if head and head[0].kind == "para" else ""
    on = slot_day or made.date()
    day = f"{on.month}/{on.day}({WEEKDAYS[on.weekday()]})"
    subject = " ".join(f"{MAIL_TAG} {day} {slot} 보고 — {mail_plain(lede or rep.title or '')}".split())
    subject = subject if len(subject) <= SUBJECT_MAX else subject[:SUBJECT_MAX - 1] + "…"
    h = [f'<p style="{MS["eyebrow"]}">메일 비서</p>', f'<h1 style="{MS["h1"]}">{mail_inline(rep.title or "")}</h1>']
    t = [mail_plain(rep.title or "")]
    if lede:
        h.append(f'<p style="{MS["lede"]}">{mail_inline(lede)}</p>')
        t.append(mail_plain(lede))
    meta = MAIL_META.format(slot=slot)
    h.append(f'<p style="{MS["meta"]}">{html.escape(meta)}</p>')
    t.append(meta)
    mail_blocks(head, h, t)
    for sec in rep.sections[1:]:
        if is_empty_done(sec):
            continue
        h.append(f'<h2 style="{MS["h2"]}">{mail_inline(sec.title or "")}</h2>')
        t += ["", f"■ {mail_plain(sec.title or '')}"]
        blocks = sec.blocks
        if task_section(blocks):                     # 머리말(첫 줄 앞의 문단) 뒤에 — 모델이 쓴 머리말은 그대로 두고 어디서 맡기나를 댄다
            lead = next((i for i, b in enumerate(blocks) if b.kind != "para"), len(blocks))
            mail_blocks(blocks[:lead], h, t)
            h.append(f'<p style="{MS["intro"]}">{html.escape(MAIL_TASK_INTRO)}</p>')
            t.append(MAIL_TASK_INTRO)
            blocks = blocks[lead:]
        mail_blocks(blocks, h, t)
    dateline = DATELINE.format(made, WEEKDAYS[made.weekday()], made)
    h.append(f'<p style="{MS["foot"]}">{html.escape(MAIL_FOOT)}<br>{html.escape(dateline)}</p>')
    t += ["", MAIL_FOOT, dateline]
    page = ('<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(subject)}</title></head><body style="{MS["body"]}"><div style="{MS["sheet"]}">' + "".join(h) + "</div></body></html>")
    return {"subject": subject, "html": page, "text": "\n".join(t) + "\n"}
