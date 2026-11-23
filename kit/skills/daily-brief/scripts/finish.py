"""보고 글을 남기기 전에 코드가 든 값으로 마무리한다 — 창을 여는 손(`window.py`)이 모델이 쓴 글을 받아 창을 짓기 전에 부른다. 창과 남는 보고
글이 마무리한 이 글 하나에서 선다.

- **기록 절을 잇는다** — 지난 보고 글의 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」을 새 글에 잇는다. 사용자가 정하신 것은 날마다 모델이
  옮겨 적지 않는다. 지난 글을 못 읽으면 창을 짓지 않는다(`Unread`)
- **「일정 넣기」 줄에 열쇠를 단다** — 열쇠 없는 줄마다 일정 손의 미리 보기를 같은 값으로 불러, 받은 열쇠를 그 줄 끝에 달고 그 시각의 지금
  (비었다 · 겹치는 일정)을 카드의 점으로 넣는다. 사람이 보는 판과 누른 뒤 넣는 손이 견주는 판이 한 미리 보기에서 나온다 — 모델은 열쇠를
  옮겨 적지 않는다. 이미 든 일정 · 미리 보기를 못 받은 줄은 열쇠 없이 그렇다는 점을 단다(창은 넣기 단추 대신 그 말을 단다)
- **옛 꼴의 「걸지 않기로 하셨다」를 맞춤 파일로** — 지난 보고 글만 그 말씀을 들었으면 맞춤 파일 「걸지 않기로 하신 것」에 한 번 옮긴다

사용자 폴더에서 읽는 것은 지난 보고 글 · 맞춤 파일이고, 쓰는 것은 옛 꼴을 옮길 때의 맞춤 파일뿐이다. 무엇을 지키고 왜
그런가는 `references/DESIGN.md` 「보고 글을 마무리한다」가 든다.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
from brief_cards import FACT  # noqa: E402
from brief_files import kept_briefs  # noqa: E402
from brief_inline import first_unid, plain  # noqa: E402
from brief_put import KEY_MARK, PUT_KEY, PUT_SPLIT, Put  # noqa: E402
from brief_sections import DONE_SECTION, NONE_ROW, REOPEN_SECTION, fold, section_rows, section_span  # noqa: E402
from brief_tasks import put_in  # noqa: E402
from brief_text import SUB  # noqa: E402
import prefs_file as P  # noqa: E402
import presses  # noqa: E402
import store as S  # noqa: E402

NOW_FREE = "그 시각은 비어 있습니다"
NOW_CLASH = "그 시각에 겹치는 일정 — {clash}"
NOW_ALREADY = "같은 일정이 이미 있어 넣지 않습니다"
NOW_UNSEEN = "일정을 확인하지 못해 이 창에서는 넣지 않습니다 — 대화에서 「그 약속 넣어 줘」 하시면 넣습니다"


def finish(text: str, folder: pathlib.Path, preview=presses.run_calendar) -> tuple[str, list[str]]:
    """모델이 쓴 보고 글 → (마무리한 글, 끝 줄 앞에 낼 경고). `preview` 는 일정 손을 부르는 손(시험이 갈아 끼운다)."""
    warns = keep_declined(folder)
    text, more = carry(text, folder)
    text, last = stamp_puts(text, preview)
    return text, warns + more + last


def keep_declined(folder: pathlib.Path) -> list[str]:
    """지난 보고 글만 「걸지 않기로 하셨다」는 말씀을 든 옛 꼴이면 맞춤 파일에 옮긴다 — 새 보고 글이 가장 늦은 글이 되는 이 순간이 지나면 그
    말씀이 어디에도 안 남는다. 맞춤 파일을 못 읽으면 쓰지 않고 경고한다(빈 것 위에 쓰면 감추고 미룬 일이 사라진다)."""
    try:
        prefs = P.read(folder, strict=True)        # 그 절이 없는 파일이면 읽는 손이 지난 보고 글의 옛 꼴을 읽어 들인다(`legacy`)
    except P.Unreadable as exc:
        return [f"경고: 보고 맞춤 파일을 못 읽어 「{P.DECLINED}」을 옮기지 못했다({exc}) — 다음 보고 때 스캔 · 아침 보고를 다시 여쭐 수 있다"]
    if not prefs.legacy:
        return []
    try:
        P.write(folder, prefs)
    except OSError as exc:
        return [f"경고: 「{P.DECLINED}」을 보고 맞춤 파일에 못 적었다({exc}) — 다음 보고 때 스캔 · 아침 보고를 다시 여쭐 수 있다"]
    return []


# ── 기록 절 ───────────────────────────────────────────────────────────────

class Unread(Exception):
    """지난 보고 글이 있는데 못 읽었다 — 기록 절을 잇지 못한 새 글이 가장 늦은 글이 되면 사용자의 말씀이 사라진다. 창을 짓지 않는다."""


def carry(text: str, folder: pathlib.Path) -> tuple[str, list[str]]:
    """지난 보고 글의 기록 절 둘을 새 글에 잇는다 — 새 글에 이미 든 줄(같은 첫 메일 번호 · 번호가 없으면 같은 글)은 다시 안 넣는다. 두 절은 일마다
    사용자의 마지막 말씀이라(같은 메일 번호는 한쪽에만 선다 — 거두는 손 · 대화가 맞은편 줄을 걷는다) 날마다 그대로 잇는다. 「끝났다고 하신 것」은
    줄이 없어도 「없음」으로 세운다 — 다음 보고 · 업무 파악 · 거두는 손이 그 절을 찾는다. 지난 글을 못 읽으면 `Unread`."""
    briefs = kept_briefs(folder) if folder.is_dir() else []
    prev = ""
    if briefs:
        try:
            prev = (S.read_bytes(briefs[-1]) or b"").decode("utf-8", errors="replace")
        except S.Unreadable as exc:
            raise Unread(f"{briefs[-1].name}: {exc}") from exc
    for name in (DONE_SECTION, REOPEN_SECTION):
        keys = {first_unid(r) or r.strip() for r in section_rows(text, name)}
        text = fold(text, name, [r for r in section_rows(prev, name) if (first_unid(r) or r.strip()) not in keys])
    if section_span(text.split("\n"), DONE_SECTION)[0] is None:
        text = fold(text, DONE_SECTION, [NONE_ROW])   # 절이 없으면 끝에 세우는 꼴은 `fold` 한 자리가 든다
    return text, []


# ── 「일정 넣기」의 열쇠 ─────────────────────────────────────────────────────

UNSEEN_WARN = ("경고: 「{field}」 「{title}」의 일정을 미리 보지 못해 넣기 단추를 안 달았다(일정 손 종료 {code}) — 대화에서 넣을 수 있다고 "
               "카드에 적었다")
READY, ALREADY, UNSEEN = "ready", "already", "unseen"   # 미리 보기 한 번의 끝 — 열쇠를 받았다 · 같은 일정이 이미 있다 · 못 받았다


def stamp_puts(text: str, preview) -> tuple[str, list[str]]:
    """열쇠 없는 「일정 넣기」 줄마다 미리 보기를 한 번 불러 열쇠를 달고 그 시각의 지금을 카드의 점으로 넣는다. 열쇠가 이미 있는 줄(모델이 옮긴
    옛 꼴)은 그대로 둔다. 줄마다 미리 보기 → 그 줄 고치기 → 앞 판의 점 걷기 → 새 점 넣기의 차례다."""
    rows, warns = text.split("\n"), []
    i = 0
    while i < len(rows):
        put, field = put_row(rows[i])
        if put is None or put.key:
            i += 1
            continue
        code, answer = preview(put, True)
        state, key = preview_end(code, answer)
        rows[i] = keyed_row(rows[i], key) if state == READY else rows[i]
        warns += [UNSEEN_WARN.format(field=field, title=put.title, code=code)] if state == UNSEEN else []
        i -= drop_points(rows, i)                  # 앞서 마무리한 글을 다시 받았으면 그때 넣은 점을 걷는다 — 지금 판의 점 하나만 선다
        rows.insert(point_at(rows, i), sub_row(rows[i], point_words(state, answer)))
        i += 2
    return "\n".join(rows), warns


def preview_end(code: int | None, answer: dict) -> tuple[str, str]:
    """미리 보기 한 번의 끝 — (READY · ALREADY · UNSEEN, 받은 열쇠). 꼴에 맞는 열쇠를 「ready」로 받은 것만 READY 다."""
    key = str(answer.get("key") or "") if code == 0 else ""
    if key and answer.get("state") == "ready" and PUT_KEY.match(key):
        return READY, key
    if code == 0 and answer.get("state") == "already":
        return ALREADY, ""
    return UNSEEN, ""


def keyed_row(row: str, key: str) -> str:
    """「일정 넣기」 줄 끝에 열쇠를 단다 — 값을 「`…`」로 싸 쓴 줄은 열쇠도 그 안에."""
    row = row.rstrip()
    tick = "`" if row.endswith("`") and row.count("`") >= 2 else ""
    return row[:len(row) - len(tick)] + f"{PUT_SPLIT}{KEY_MARK}{key}" + tick


def point_words(state: str, answer: dict) -> str:
    """카드에 넣을 그 시각의 점 — 받은 판의 지금 · 이미 있음 · 못 봄."""
    return now_words(answer) if state == READY else NOW_ALREADY if state == ALREADY else NOW_UNSEEN


def sub_row(row: str, words: str) -> str:
    """그 줄과 같은 들여쓰기의 낱낱 한 줄."""
    return row[:len(row) - len(row.lstrip())] + "- " + words


NOW_HEADS = (NOW_FREE, NOW_CLASH.split("{", 1)[0], NOW_ALREADY, NOW_UNSEEN)


def drop_points(rows: list[str], i: int) -> int:
    """「일정 넣기」 줄 `i` 의 카드에서 마무리가 넣은 그 시각의 점을 걷는다 — 걷은 줄 수(그 줄 앞에 있던 것)."""
    start = i
    while start > 0 and SUB.match(rows[start - 1]):
        start -= 1
    gone = [j for j in range(start, i) if (m := SUB.match(rows[j])) and m.group(1).strip().startswith(NOW_HEADS)]
    for j in reversed(gone):
        del rows[j]
    return len(gone)


def put_row(row: str) -> tuple[Put | None, str]:
    """카드의 낱낱 한 줄이 「일정 넣기」 칸이면 (그 값, 칸 이름) — 아니면 (None, "")."""
    sub = SUB.match(row)
    m = FACT.match(sub.group(1).strip()) if sub else None
    if not m:
        return None, ""
    label = m.group("label").strip()
    put = put_in(label, m.group("value"))
    return (put, label) if put else (None, "")


def point_at(rows: list[str], i: int) -> int:
    """「일정 넣기」 줄 `i` 의 카드에서 점을 넣을 자리 — 그 카드의 낱낱 가운데 처음 선 칸(「이름: 값」) 앞. 카드의 점이 칸보다 앞에 서야 창이
    끝의 칸을 칸으로 읽는다."""
    start = i
    while start > 0 and SUB.match(rows[start - 1]):
        start -= 1
    for j in range(start, i + 1):
        sub = SUB.match(rows[j])
        if sub and FACT.match(sub.group(1).strip()):
            return j
    return i


def now_words(answer: dict) -> str:
    """미리 보기 판의 그 시각 — 겹치는 일정이 없으면 「비어 있습니다」, 있으면 「HH:MM–HH:MM 제목」을 잇는다."""
    clash = [c for c in answer.get("clash") or [] if isinstance(c, dict) and c.get("title")]
    if not clash:
        return NOW_FREE
    return NOW_CLASH.format(clash=" · ".join(f"{c.get('when') or ''} {plain(str(c['title']))}".strip() for c in clash))
