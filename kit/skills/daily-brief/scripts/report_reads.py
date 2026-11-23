"""보고를 짓는 쪽이 거두는 손(`ticks.py`)의 끝 줄 앞에서 읽을 무리 — 맞춤(올리지 않을 것 · 돌아온 것 · 미룬 것), 그리고 가장 늦은 보고 글 뒤에
창에서 누르신 「일정에 넣기」의 끝과 맡기신 일의 끝. 「지난 보고 뒤」는 가장 늦은 보고 글의 이름에서 한 번 읽고, 두 기록은 저마다 제 시계의
꼴로 견준다. 사용자 폴더의 기록 둘을 읽기만 한다.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
import clock as T  # noqa: E402
import records as R  # noqa: E402
from brief_const import SEOUL  # noqa: E402
from brief_files import kept_briefs, made_of  # noqa: E402

PUT_WORDS = {R.ADDED: "넣음", R.ALREADY: "같은 일정이 이미 있어 안 넣음", R.MOVED: "그 사이 일정이 바뀌어 안 넣음", R.UNSURE: "넣었는지 확인 못 함",
             R.PAST: "지난 약속이라 안 넣음", R.SESSION: "사내 로그인이 끊겨 아직 못 넣음", R.FAILED: "못 넣음", R.ENTERING: "넣는 중"}
PUT_HEAD = "일정에 넣기 — 지난 보고 뒤 창에서 누르신 카드의 끝이다. 다시 세울지는 lane.md 「무엇이 내 약속인가」의 「지난번 누르신 카드」:"
PUT_UNREAD = "일정에 넣기 — 기록({path})을 못 읽었다({exc}). 지난 보고 뒤 창에서 누르신 카드의 끝을 모른다"
RUN_WORDS = {"done": "됨", "asked": "여쭐 것이 있어 멈춤", "failed": "못 함", "unsure": "됐는지 확인 못 함", "doing": "하는 중"}
RUN_HEAD = "맡긴 일 — 지난 보고 뒤 창에서 맡기신 일의 끝이다. 다시 올릴지는 lane.md 「맡길 일」의 「지난번 맡기신 일」:"
RUN_UNREAD = "맡긴 일 — 기록({path})을 못 읽었다({exc}). 지난 보고 뒤 창에서 맡기신 일의 끝을 모른다"
RUN_DOING, RUN_WAITING = "하는 중", "기다림"     # 일의 끝이 아직 없을 때 — 판이 돈다 · 판이 맺었는데 그 일의 칸이 없다
FIRST_MAX = 80                                 # 일마다 댈 결과 첫 줄의 길이


def report_lines(folder: pathlib.Path, quiet: list[str], back: list[str], wait: list[str]) -> list[str]:
    """보고가 읽을 무리 셋 — 맞춤, 지난 보고 뒤의 「일정에 넣기」, 지난 보고 뒤의 맡긴 일. 없는 무리는 안 선다."""
    made = latest_made(folder)
    return summary(quiet, back, wait) + put_lines(folder, made) + run_lines(folder, made)


def latest_made(folder: pathlib.Path) -> dt.datetime | None:
    """가장 늦은 보고 글을 지은 때(이 PC 의 시각 — 그 이름이 든다) — 보고 글이 없으면 None."""
    briefs = kept_briefs(folder) if folder.is_dir() else []
    return made_of(briefs[-1].name) if briefs else None


def summary(quiet: list[str], back: list[str], wait: list[str]) -> list[str]:
    """보고를 짓는 쪽이 읽을 맞춤 — 올리지 않을 것 · 돌아온 것 · 미룬 것(없는 무리는 안 선다)."""
    out: list[str] = []
    if quiet:
        out += ["올리지 않을 것 — 사용자가 정하셨다. 같은 갈래의 일은 이 보고에 올리지 않고 「이 보고가 본 데」에 그 수만 적는다:", *quiet]
    if back:
        out += ["돌아온 것 — 「내일 다시」 하신 일이 돌아오는 날이 와 돌아왔다. 아직 열려 있으면 이 보고에 다시 올린다:", *back]
    if wait:
        out += ["미룬 것 — 「내일 다시」 하신 일이다. 돌아오는 날 전에는 이 보고에 올리지 않는다:", *wait]
    return out


# ── 「일정에 넣기」 ─────────────────────────────────────────────────────────

def put_lines(folder: pathlib.Path, made: dt.datetime | None) -> list[str]:
    """지난 보고 뒤 창에서 누르신 「일정에 넣기」의 끝 — 보고 글이 없으면 빈 목록, 기록을 못 읽으면 그렇다는 한 줄."""
    if made is None:
        return []
    try:
        rows = puts_since(folder, made)
    except R.Unreadable as exc:
        return [PUT_UNREAD.format(path=folder / R.LEDGER_FILE, exc=exc)]
    return put_words(rows)


def puts_since(folder: pathlib.Path, made: dt.datetime) -> list[dict]:
    """넣은 누름의 기록 가운데 `made` 뒤의 것 — 맺은 때 차례. 이름의 때는 이 PC 의 시각이라 기록과 같은 서울 꼴로 바꿔 견준다."""
    since = T.stamp(made.astimezone().astimezone(SEOUL))
    ledger = R.read_ledger(folder)
    return sorted((v for v in ledger.values() if isinstance(v, dict) and str(v.get("at", "")) >= since), key=lambda v: str(v.get("at", "")))


def put_words(rows: list[dict]) -> list[str]:
    """누름마다 「제목」 시각 — 끝의 말. 없으면 빈 목록."""
    if not rows:
        return []
    return [PUT_HEAD] + [f"- 「{v.get('title', '')}」 {v.get('start', '')} — {PUT_WORDS.get(str(v.get('state')), str(v.get('state')))}" for v in rows]


# ── 맡긴 일 ────────────────────────────────────────────────────────────────

def run_lines(folder: pathlib.Path, made: dt.datetime | None) -> list[str]:
    """지난 보고 뒤 창에서 맡기신 일마다 그 끝 — 보고 글이 없으면 빈 목록, 기록을 못 읽으면 그렇다는 한 줄."""
    if made is None:
        return []
    try:
        rows = runs_since(folder, made)
    except R.Unreadable as exc:
        return [RUN_UNREAD.format(path=folder / R.RUNS_FILE, exc=exc)]
    return run_words(rows)


def runs_since(folder: pathlib.Path, made: dt.datetime) -> list[tuple[str, str, str]]:
    """맡긴 일의 기록 가운데 `made` 뒤에 맡은 누름의 일마다 (이름, 끝의 상태, 결과 첫 줄) — 같은 일은 가장 늦은 누름의 끝 하나. 끝이 아직
    없으면 판이 도는 동안은 「하는 중」. 결과가 값뿐이면(회의실 따위) 그 값이 무엇을 했나를 첫 줄로 댄다."""
    since = T.stamp(made.astimezone())
    presses = R.read_runs(folder)
    rows, seen = [], set()
    for key, v in sorted(presses.items(), key=lambda kv: str(kv[1].get("taken", "")), reverse=True):
        if str(v.get("taken", "")) < since:
            continue
        for tid, name in (v.get("names") or {}).items():
            if (v.get("page"), tid) in seen:
                continue
            seen.add((v.get("page"), tid))
            got = R.task_outcome(presses, key, tid) or {}
            state = got.get("state") or (RUN_DOING if R.live(v) else "")
            facts = " · ".join(f"{f[0]} {f[1]}" for f in got.get("facts") or [] if isinstance(f, list) and len(f) == 2)
            rows.append((name, state, " ".join(str(got.get("said") or facts).split())[:FIRST_MAX]))
    return rows


def run_words(rows: list[tuple[str, str, str]]) -> list[str]:
    """일마다 「이름 — 끝 · 결과 첫 줄」. 없으면 빈 목록."""
    if not rows:
        return []
    return [RUN_HEAD] + [f"- {name} — {RUN_WORDS.get(state, state or RUN_WAITING)}" + (f" · {first}" if first else "") for name, state, first in rows]
