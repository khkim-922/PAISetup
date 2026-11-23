"""카드에 적힌 맡길 일을 읽는다 — 칸 하나 → `Task`(`task_of` — 종류마다의 셈은 `task_kinds` 의 줄이 든다) · 칸이 든 넣을 일정(`put_in`) ·
카드 하나 → 맡길 일과 남은 몫(`take_card`) · 카드로 서나 · 약속의 카드인가 · 시각을 여쭙나(`card_shaped` · `dated_card` · `asks_time`) ·
보고 글 → 맡길 일(`tasks_of`) · 일정 넣기를 든 카드(`cards_of`), 맡길 일 하나 → 누를 수 있는 넣을 일정(`pressable_put`) · 창의 할 일 줄의
꼴(`row_shape`). 파일 · 망에 닿지 않는다.
꼴의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」 · 「맡길 일」이다.
"""

from __future__ import annotations

import hashlib
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 보고 글 읽기 — `-I` 로 돌아도 싣는다
from brief_cards import FACT, card_head, card_name, split_facts  # noqa: E402
from brief_inline import plain, with_numbers  # noqa: E402
from brief_put import PUT_SPLIT, Put, no_time_of, put_of  # noqa: E402
from brief_sections import report_items  # noqa: E402
from brief_text import Item, parse  # noqa: E402
from task_kinds import BAD, DO_FIELD, FIELD_KINDS, NAMED, PUT_FIELD, VIA_NONE, VIA_PUT, VIA_TALK, Cells, Kind, shown_of  # noqa: E402

# 맡길 일 — 카드의 낱낱 가운데 종류 표가 대는 칸(`task_kinds.DO_FIELD` · `FIELD_KINDS`). 무엇을 · 어느 갈래로 맡길지는 보고를 짓는 모델이
# 적고, 창은 적힌 것을 보이고 누름을 남길 뿐이다 — 종류를 짐작하거나 꼴이 틀린 줄을 고쳐 읽지 않는다
TASK_FIELDS = (DO_FIELD, *FIELD_KINDS)
TOP_MARK = "추천"                               # 받는 종류(`Kind.topped`)의 칸 끝에 붙여 창 머리의 칸에 미리 세운다 — 보고 하나에 하나까지
TASK_ID_LEN = 12                               # 일의 번호 — 카드 머리 · 칸의 차례 · 칸의 글에서 낸 해시의 앞
# 창의 할 일 줄 하나의 꼴(`row_shape`) — 꼴이 틀린 옛 「넣을 일정」 칸 · 꼴이 틀린 다른 칸 · 「대화로 할 일」 · 그 가운데 창 머리의 추천 · 열쇠를
# 못 받은 일정 넣기 · 누를 수 있는 일정 넣기 · 누를 수 있는 다른 일. 줄을 짓는 쪽과 세는 쪽은 이 이름으로만 가른다
ROW_BAD_PUT, ROW_BAD, ROW_TALK, ROW_TALK_TOP, ROW_UNKEYED, ROW_PUT, ROW_RUN = ("bad-put", "bad", "talk", "talk-top", "unkeyed", "put", "run")


@dataclass(frozen=True)
class Task:
    """카드에 적힌 맡길 일 하나 — 칸의 값과 그 종류의 줄(`row` — `task_kinds` 의 한 줄), 그 줄이 셈한 사람이 읽는 줄 · 무엇이 되나 · 시작 ·
    넘길 값(`task_of` 가 한 번 셈한다). 창이 사람에게 보이는 줄과 창 곁의 손이 넘겨받는 일이 다 이것에서 나온다(`tasks_of`).
    꼴이 틀린 칸은 종류가 `task_kinds.BAD` 다 — 그 줄은 적힌 글(`written`) 그대로 서고 맡길 수 없다."""
    id: str
    field: str                      # 칸 이름 — `task_kinds` 의 DO_FIELD · TALK_FIELD · PUT_FIELD(옛 꼴)
    row: Kind                       # 종류의 줄 — 넘기는 길 · 창의 말 · 결과 이름표는 여기서 읽는다
    written: str                    # 칸의 값 그대로
    card: str                       # 카드 제목(맨글자)
    num: str | None                 # 카드에 쓴 번호
    evidence: tuple[str, ...]       # 카드의 근거 — 머리 · 점 · 칸의 맨글자(메일 링크는 「글 (메일 번호 …)」 · 사람 링크는 「이름 <주소>」)
    line: str                       # 사람이 읽는 「무엇을 하나」 — 누르시면 이 줄의 값 그대로 끝까지 한다(`Kind.line`)
    cons: str                       # 누르시면 무엇이 되나(`Kind.said`)
    start: str                      # 시작 시각(서울 벽시계) — 때가 없는 일이면 빈 글(`Kind.start`)
    values: tuple[tuple[str, str], ...]   # 뒤의 실행에 넘길 값 — 칸마다 (이름, 적힌 그대로의 값)(`Kind.values`)
    put: Put | None = None          # 「일정 넣기」의 값 — 일정 손 미리 보기 답 그대로
    top: bool = False               # 「대화로 할 일」에 붙은 추천 표
    lines: tuple[str, ...] = ()     # 카드의 머리와 맡길 일 밖의 낱낱 — 보고 글에 적힌 그대로(메일 · 사람 링크가 든다)

    @property
    def kind(self) -> str:
        """종류 이름 — 카드에 적힌 그대로, 꼴이 틀린 칸이면 빈 글. 기록 · 뒤의 실행 · 창이 이 이름으로 그 일의 종류를 적는다."""
        return self.row.name

    def run_lines(self) -> list[str]:
        """뒤에서 하는 실행에 줄 카드의 줄 — 보고 글에 적힌 그대로의 머리 · 낱낱 뒤에 그 일의 값(`values`)을 「이름: 값」 한 줄씩. 실행이 방과
        사람을 다시 찾지 않고, 답할 메일을 카드의 근거 메일 가운데서 짐작하지 않는다."""
        return [*self.lines, *(f"{name}: {value}" for name, value in self.values)]

    def words(self) -> str:
        """「대화로 열기」가 VS Code 의 입력 칸에 채울 말 — 줄 · 빈 줄 · 카드의 근거. 창 곁의 손이 그 뒤에 보고 이름과 경로를 붙인다."""
        return "\n".join((self.line, "", *self.evidence))


def cell_text(value: str) -> str:
    """맡길 일 칸의 값에서 읽을 글 — 앞뒤 빈칸과 값을 감싼 「`」를 걷은 그대로."""
    return value.strip().strip("`").strip()


def named_kind(written: str) -> tuple[Kind | None, str | None]:
    """「바로 할 일」 칸의 글(`cell_text`) → (첫 값이 이름인 종류(`task_kinds.NAMED`) · 모르는 이름이면 None, 이름 뒤의 글 · 「 | 」가 없으면 None).
    넣을 일정 가리기(`put_in`)와 종류의 줄 고르기(`cell_row`)가 이 한 자리로 이름을 뗀다."""
    name, sep, rest = written.partition(PUT_SPLIT)
    return NAMED.get(name.strip()), (rest if sep else None)


def put_in(field_name: str, value: str) -> Put | None:
    """칸 하나가 든 넣을 일정 — 넘기는 길이 일정 넣기(`VIA_PUT`)인 종류의 값: 칸 이름이 그 종류를 정하면(옛 「넣을 일정」) 칸 전체,
    「바로 할 일」이면 이름 뒤의 값. 그런 칸이 아니거나 꼴이 틀렸으면 None. 창을 짓기 전의 마무리(`finish.put_row`)와 맡길 일 읽기(`task_of`)가
    이 한 자리로 가른다."""
    fixed = FIELD_KINDS.get(field_name)
    if fixed is not None:
        return put_of(value) if fixed.via == VIA_PUT else None
    if field_name != DO_FIELD:
        return None
    row, rest = named_kind(cell_text(value))
    return put_of(rest) if row is not None and row.via == VIA_PUT and rest is not None else None


def cell_row(field_name: str, written: str, put: Put | None) -> tuple[Kind, Cells, bool]:
    """칸 하나 → (종류의 줄, 이름 붙은 값, 추천 표). 칸 이름이 종류를 정하면(`FIELD_KINDS` — 「대화로 할 일」 · 옛 「넣을 일정」) 칸 전체가 그
    종류의 값 하나이고 끝의 「| 추천」은 그 종류가 받으면(`Kind.topped`) 떼어 표로, 「바로 할 일」이면 첫 값이 이름인 종류(`named_kind`)의 값들이다.
    값을 한 번 이름 붙여 읽는다(`Kind.read`). 모르는 이름이거나 · 그 종류의 차례로 못 읽거나 · 꼴(`Kind.fits`)이 안 맞으면 `BAD`(값은 빈 것)."""
    row, top = FIELD_KINDS.get(field_name), False
    if row is not None:
        values = [x.strip() for x in written.split(PUT_SPLIT)]
        top = row.topped and len(values) > 1 and values[-1] == TOP_MARK
        parts = (PUT_SPLIT.join(values[:-1] if top else values).strip(),)
    else:
        row, rest = named_kind(written)
        parts = () if rest is None else tuple(x.strip() for x in rest.split(PUT_SPLIT))
    cells = row.read(parts) if row is not None else None
    row = row if row is not None and cells is not None and row.fits(cells, put) else BAD
    return row, (Cells() if row is BAD else cells), top


def task_of(field_name: str, value: str, tid: str, card: str, num: str | None, evidence: tuple[str, ...],
            lines: tuple[str, ...] = ()) -> Task:
    """칸 하나 → Task — 넣을 일정(`put_in`)과 종류의 줄 · 이름 붙은 값(`cell_row`)을 고르고, 사람 칸의 사람들(`Kind.persons`)과 사람이 읽는 칸의
    말(`shown_of`)을 한 번 지어 그 줄의 셈(줄 · 무엇이 되나 · 시작 · 넘길 값)을 한 번씩 부른다."""
    written = cell_text(value)
    put = put_in(field_name, value)
    row, cells, top = cell_row(field_name, written, put)
    people = row.persons(cells)
    shown = shown_of(cells, people)
    return Task(id=tid, field=field_name, row=row, written=written, card=card, num=num, evidence=evidence,
                line=row.line(cells, shown, put, written), cons=row.said(cells, people), start=row.start(cells, put),
                values=tuple(row.values(cells)), put=put, top=top, lines=lines)


# ── 카드 하나 → 맡길 일 ───────────────────────────────────────────────────

def task_cells(subs: list[str]) -> tuple[list[tuple[str, str]], list[str]]:
    """낱낱 → (맡길 일의 칸 (이름, 값) · 나머지 낱낱). 맡길 일의 칸은 낱낱 어디에 있어도 떼어 낸다 — 점 사이에 끼어도 글자로 남지 않게."""
    cells: list[tuple[str, str]] = []
    rest: list[str] = []
    for s in subs:
        m = FACT.match(s)
        if m and m.group("label").strip() in TASK_FIELDS:
            cells.append((m.group("label").strip(), m.group("value")))
        else:
            rest.append(s)
    return cells, rest


def evidence_of(it: Item, card: str, points: list[str], facts: list[tuple[str, str]]) -> tuple[str, ...]:
    """카드의 근거 — 카드 이름(`card`)과 때 · 점 · 칸의 맨글자(메일 · 사람 · 방 링크는 번호 · 주소 · id 를 남긴다 — `with_numbers`)."""
    when = card_head(it.text)[1]
    return ((f"— 카드 「{card}」" + (f" — {with_numbers(when)}" if when.strip() else "")),
            *(f"· {with_numbers(x)}" for x in points), *(f"· {k}: {with_numbers(v)}" for k, v in facts))


def task_id(it: Item, pos: int, label: str, value: str, seen: dict[str, int] | None) -> str:
    """일의 번호 — 카드 머리 · 칸의 차례 · 칸의 글에서 낸 해시의 앞(`TASK_ID_LEN`). 같은 보고 글이면 창과 창 곁의 손이 같은 번호를 낸다.
    `seen` 을 주면 한 보고 안에서 겹친 번호에 「-n」을 붙이고 센 수를 거기 적는다(같은 카드를 두 번 쓴 글)."""
    tid = hashlib.sha256(f"{plain(it.text)}\x1f{pos}\x1f{label}\x1f{value.strip()}".encode("utf-8")).hexdigest()[:TASK_ID_LEN]
    if seen is None:
        return tid
    seen[tid] = seen.get(tid, 0) + 1
    return tid if seen[tid] == 1 else f"{tid}-{seen[tid]}"


def take_card(it: Item, seen: dict[str, int] | None = None) -> tuple[list[Task], list[str], list[tuple[str, str]], bool]:
    """줄 하나 → (맡길 일, 앞의 점, 끝의 칸, 시각 없는 모임인가). 맡길 일의 칸을 떼고(`task_cells`) → 남은 낱낱을 점과 칸으로 가르고 → 시각
    없는 모임의 칸을 떼고 → 칸마다 번호(`task_id`)와 카드의 근거(`evidence_of`)를 단 Task 를 짓는다. `seen` 은 `task_id` 로 간다."""
    cells, rest = task_cells(it.subs)
    points, facts = split_facts(rest)
    no_time, facts = no_time_of(facts)
    if not cells:
        return [], points, facts, no_time
    card = card_name(it)
    evidence = evidence_of(it, card, points, facts)
    tasks = [task_of(label, value, task_id(it, pos, label, value, seen), card, it.num, evidence, (it.text, *rest))
             for pos, (label, value) in enumerate(cells, 1)]
    return tasks, points, facts, no_time


def card_shaped(points: list[str], tasks: list[Task], no_time: bool) -> bool:
    """줄이 카드로 서나 — 앞의 점 · 맡길 일 · 시각 없는 모임 가운데 하나라도 든다(아니면 한 줄). 창과 메일 한 장이 이 한 자로 가른다."""
    return bool(points or tasks or no_time)


def dated_card(tasks: list[Task], no_time: bool) -> bool:
    """카드가 약속의 카드인가 — 맡길 일 가운데 때가 든 종류(`Kind.dated`)로 읽혔거나 칸 이름이 때가 든 종류를 정한 칸(옛 「넣을 일정」 —
    꼴이 틀렸어도)이 있거나, 시각 없는 모임이다. 창과 메일 한 장이 이 한 자로 그린다."""
    return no_time or any(t.row.dated or FIELD_KINDS.get(t.field, BAD).dated for t in tasks)


def asks_time(tasks: list[Task], no_time: bool) -> bool:
    """카드에 시각을 여쭙는 말(`render_base.NO_TIME_SAID`)이 서나 — 시각 없는 모임이고 맡길 일이 없다(있으면 그 일의 줄이 선다)."""
    return no_time and not tasks


# ── 보고 글 → 맡길 일 ─────────────────────────────────────────────────────

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
    """보고 글에서 누를 수 있는 「일정 넣기」(`pressable_put`)를 든 카드 — {열쇠: (Put, 카드의 맨글자)}. 거두는 손이 누름을 이 글의 카드에 대어
    그 값으로 넣는다 — 창이 사람에게 보인 글과 같은 글이다. 옛 「넣을 일정」 칸도 같은 일로 읽는다."""
    out: dict[str, tuple[Put, str]] = {}
    for it in report_items(parse(text)):
        for t in take_card(it)[0]:
            put = pressable_put(t)
            if put is not None and put.key not in out:
                out[put.key] = (put, plain(" ".join([it.text, *it.subs])))
    return out


# ── 맡길 일 하나 → 누를 수 있나 · 창의 줄 꼴 ─────────────────────────────────────

def pressable_put(t: Task) -> Put | None:
    """맡길 일이 든 넣을 일정 가운데 누를 수 있는 것 — 창을 짓기 전에 미리 보기의 열쇠를 받은 것(`Put.key`). 넣을 일정이 없거나 열쇠가 없으면
    None. 창의 넣기 단추(`row_shape`)와 거두는 손의 카드 찾기(`cards_of`)가 이 한 자로 가른다."""
    return t.put if t.put is not None and t.put.key else None


def row_shape(t: Task, top_id: str | None) -> str:
    """창의 할 일 줄 하나의 꼴(`ROW_…`) — 꼴이 틀린 칸은 옛 「넣을 일정」 칸인가로, 대화로 할 일은 창 머리의 추천(`top_id`)인가로, 넣을 일정이
    든 일은 누를 수 있나(`pressable_put`)로 가른다."""
    if t.row.via == VIA_NONE:
        return ROW_BAD_PUT if t.field == PUT_FIELD else ROW_BAD
    if t.row.via == VIA_TALK:
        return ROW_TALK_TOP if t.id == top_id else ROW_TALK
    if t.put is not None:
        return ROW_PUT if pressable_put(t) is not None else ROW_UNKEYED
    return ROW_RUN
