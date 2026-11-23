"""스캔 한 판 — 잠금 쥐기 → 판 준비 → (세션을 기다리는 주기면 판 맺기로) 판 하기 → 판 맺기.

    code = cmd_run(args)                           # `scan.py run` — 종료 값(0 됐다 · 1 멈췄다)

판 하나만 돈다 — 잠금을 못 쥐면 그 판은 건너뛴다. `--wait 초` 를 주면 앞 판의 잠금이 풀리기를 그 초 안에서 기다렸다 돌고, 시한이 지나면 건너뛴다.

판 하기는 지금 모습이 없거나 전체 주기(`--full-every` · 없으면 걸린 작업의 판이 준 것)가 지났으면 메일함 전체(상자마다 메일 머리 · 폴더 목록 · 규칙)를 다시 보고 지난 모습과 견주고,
그 사이에는 「이 시각 뒤」 새 메일만 더한다. 손의 읽는 명령만 부른다 — 메일함 · 본문 · 모델에 안 닿는다. 왜 이 꼴인가는
`references/DESIGN.md` 가 든다.
"""

from __future__ import annotations

import os
import pathlib
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import hand_lines as HL
import scan_const as C
import scan_diff as D
import scan_hand as H
import scan_store as st
import scan_time as tm
import scan_words as SW
import session_login as SL

EXIT_OK, EXIT_STOPPED = 0, 1
FULL, NEW = C.MODE_FULL, C.MODE_NEW
DONE, PARTIAL, SESSION, BUSY = C.RUN_DONE, C.RUN_PARTIAL, C.RUN_SESSION, C.RUN_BUSY
HAND_MISSING, HAND_OLD, HAND_ERROR, SHAPE, SWAP = C.RUN_HAND_MISSING, C.RUN_HAND_OLD, C.RUN_HAND_ERROR, C.RUN_SHAPE, C.RUN_SWAP
UNREAD = C.RUN_UNREAD
FIRST = C.RUN_FIRST      # 첫 판 — 바닥만 적었다
LOST_LOCK = "[스캔 — 이 판이 잠금을 잃었다(오래 멈춘 사이 다른 판이 돌았다). 아무것도 안 적었다]"


class SessionLost(Exception):
    """손이 종료 3 을 냈다 — 사내 세션이 없다 · 끊겼다."""


class HandFailed(Exception):
    """손이 0 · 3 밖의 종료 값을 냈다 — `said` 가 손의 말이다."""


class Run:
    """한 판의 셈 — 손 부르기 · 받은 줄 · 시간의 상한. 손이 `serve` 를 받으면 판 내내 손 하나에 잇달아 묻고(`H.Served`), 옛 판의 손이면
    명령마다 띄운다(`H.call`) — 어느 쪽이든 메일함에 가는 요청과 그 차례는 같다."""

    def __init__(self, hand: pathlib.Path, served: bool, since: datetime | None = None):
        """`since` — 시간의 상한을 잴 시작(판의 시작 때). 안 주면 지금이다 — 한 판 안의 두 번째 판 하기는 판의 시작에서 재야 판이 잠금 ·
        작업의 시한 안에 맺힌다."""
        self.hand_path = hand
        self.served = H.Served(hand) if served else None
        self.calls = 0
        self.lines = 0
        self.began = time.monotonic() - (max(0.0, (tm.now() - since).total_seconds()) if since else 0.0)

    def over_budget(self) -> bool:
        """한 판의 시간 상한(`RUN_BUDGET_S`)을 넘었나."""
        return time.monotonic() - self.began >= C.RUN_BUDGET_S

    def hand(self, args: list[str]) -> H.Called:
        """손에 명령 하나를 묻고 셈한다 — 세션 없음(종료 3)이면 `SessionLost`."""
        self.calls += 1
        got = self.served.ask(args) if self.served else H.call(self.hand_path, args)
        self.lines += len(got.lines)
        if got.code == C.HAND_EXIT_SESSION:
            raise SessionLost(got.said)
        return got

    def close(self) -> None:
        """띄워 둔 손을 거둔다."""
        if self.served:
            self.served.close()

    def seconds(self) -> float:
        """이 셈을 세운 뒤 지난 초 — 판 하기(손 부르기 · 풀기 · 견주기)가 다 든다."""
        return round(time.monotonic() - self.began, 1)


@dataclass
class Ended:
    """한 판의 끝 — 판의 갈래 · 끝 낱말 · 바뀜 · 판 값(판 기록에 싣는다)."""
    mode: str
    outcome: str
    events: list[dict[str, Any]] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)


# ── 판 하나 — 손 ─────────────────────────────────────────────────────────────────

def cmd_run(args) -> int:
    """한 판(`scan.py run`) — 판 하나의 잠금을 쥐고(`--wait` 면 그 초 안에서 앞 판을 기다려) 판을 맡긴다(`play`). 못 쥐면 「건너뛰었다」를 판
    기록에 적고, 판이 기대는 파일을 못 읽으면 판 기록에만 적고 멈춘다(`unread`). 종료 값 — 0 됐다(앞 판이 돌아 건너뛴 것도) · 1 멈췄다."""
    folder = st.scan_dir(make=True)
    lock, held, at, waited = st.Lock.wait(folder, args.wait or 0)
    waited_s = round(waited)
    if lock is None:
        st.append(folder / C.RUNS_FILE, [busy_record(at, held, waited_s)])
        holder = tm.parse((held or {}).get("started"))
        print(SW.gave_up_words(holder, waited_s) if args.wait else SW.busy_words(holder))
        return EXIT_OK
    try:
        return play(args, folder, at, lock, held, waited_s)
    except st.Unreadable as exc:
        return unread(folder, at, exc)
    finally:
        lock.release()


def play(args, folder: pathlib.Path, at: datetime, lock: st.Lock, cleared: dict[str, Any] | None, waited_s: int) -> int:
    """판 하나를 엮는다 — 지금 모습 · 손 · 손의 능력을 갖추고, 세션을 기다리는 주기면 판 없이 맺고, 아니면 판을 하고 맺는다. 종료 값을 낸다."""
    state, notes = ready_state(folder, cleared, waited_s)
    note_full_every(state, args)
    try:
        hand = H.find_hand(args.hand)
    except H.HandMissing as exc:
        return finish(folder, lock, state, at, Ended("-", HAND_MISSING, info={"note": str(exc)}), None, notes)
    go, lost_at, next_try = session_back(state, hand, at, args.now)
    if not go:
        print(f"[스캔 — {SW.waiting_words(lost_at, next_try)}]")
        return EXIT_STOPPED
    ended, run = read(state, folder, at, args, hand)
    return finish(folder, lock, state, at, ended, run, notes)


def read(state: dict[str, Any], folder: pathlib.Path, at: datetime, args, hand: pathlib.Path, since: datetime | None = None) -> tuple[Ended, Run]:
    """판 하기 한 번 — 손의 능력을 보고, 「list --since」 없는 옛 손이면 판을 안 하고, 아니면 판을 한다(`sweep`). `since` 는 시간의 상한을 잴
    시작이다(`Run`). 내는 것 — (판의 끝, 그 셈)."""
    probe = hand_probe(state, hand)
    run = Run(hand, served=probe["serve"], since=since)
    if not probe["since"]:
        return Ended("-", HAND_OLD, info={"note": f"회사 메일 손이 「list --since」 없는 옛 판이다: {hand}"}), run
    return sweep(run, state, folder, at, args), run


def unread(folder: pathlib.Path, at: datetime, exc: st.Unreadable) -> int:
    """판이 기대는 파일을 못 읽어 멈춘다 — 지금 모습 · 바뀜 · 보고는 안 건드리고(빈 것으로 읽어 덮으면 그 기록이 사라진다) 판 기록에만 적는다.
    다음 판이 다시 읽는다."""
    record = unread_record(at, exc)
    st.append(folder / C.RUNS_FILE, [record])
    print(f"{SW.summary(record)} {exc}")
    return EXIT_STOPPED


def busy_record(at: datetime, held: dict[str, Any] | None, waited_s: int) -> dict[str, Any]:
    """앞 판이 돌아 건너뛴 주기의 기록 한 줄 — 앞 판의 시작 때를 함께 적고, 기다렸으면(`--wait`) 기다린 초를 메모로 단다."""
    record = {"started": tm.stamp(at), "mode": "-", "outcome": BUSY, "holder": (held or {}).get("started")}
    if waited_s:
        record["note"] = SW.waited_note(waited_s)
    return record


def unread_record(at: datetime, exc: st.Unreadable) -> dict[str, Any]:
    """못 읽어 멈춘 판의 기록 한 줄 — 손을 안 불렀고 아무것도 안 바꿨다."""
    return {"started": tm.stamp(at), "ended": tm.stamp(tm.now()), "mode": "-", "outcome": UNREAD, "calls": 0, "lines": 0, "seconds": 0,
            "new": 0, "changes": 0, "note": str(exc)}


# ── 판 준비 ─────────────────────────────────────────────────────────────────────

def fresh_state() -> dict[str, Any]:
    """지금 모습이 없을 때의 빈 판."""
    return {"format": C.FORMAT, "mails": {}, "gone": {}}


def ready_state(folder: pathlib.Path, cleared: dict[str, Any] | None, waited_s: int) -> tuple[dict[str, Any], list[str]]:
    """판이 고칠 지금 모습 — 글이 깨진 판은 `.broken` 으로 옮겨 두고 새로 시작한다. 내는 것 — (지금 모습, 판 기록에 남길 메모 — 앞 판을
    기다렸으면 그 초도)."""
    state, broken = st.load_state(folder)
    notes: list[str] = [SW.waited_note(waited_s)] if waited_s else []
    if cleared is not None:
        notes.append(f"남은 잠금({tm.seoul(tm.parse(cleared.get('started'))) or '때 모름'} 시작)을 풀고 돌았다")
    if broken:
        notes.append(f"{broken} — 메일함에서 다시 짓는다")
        try:
            os.replace(folder / C.STATE_FILE, folder / (C.STATE_FILE + ".broken"))
        except OSError:
            pass
    return state or fresh_state(), notes


def session_back(state: dict[str, Any], hand: pathlib.Path | None, at: datetime, now_flag: bool) -> tuple[bool, datetime | None, datetime | None]:
    """세션이 끊긴 뒤 이번 주기에 두드려도 되나 — (돈다, 끊긴 때, 다음 두드림). 세션 파일이 끊긴 뒤 새로 쓰였거나 다음 두드림 때가 왔거나
    `--now` 면 돈다."""
    lost = state.get("session")
    if not lost:
        return True, None, None
    lost_at, next_try = tm.parse(lost.get("lost_at")), tm.parse(lost.get("next_try"))
    path = SL.session_file(hand) if hand else None
    try:
        relogged = path is not None and lost_at is not None and path.stat().st_mtime > lost_at.timestamp()
    except OSError:
        relogged = False
    if now_flag or relogged or next_try is None or at >= next_try:
        return True, lost_at, next_try
    return False, lost_at, next_try


def hand_probe(state: dict[str, Any], hand: pathlib.Path) -> dict[str, Any]:
    """손이 받는 명령(`list --since` · `serve`) — 손 파일이 바뀌었을 때만 손에 묻고 지금 모습에 적는다. 내는 것 — 적어 둔 답."""
    probe_key = {"path": str(hand), "mtime": hand.stat().st_mtime, "size": hand.stat().st_size}
    probe = state.get("probe") or {}
    if {k: probe.get(k) for k in probe_key} != probe_key or "serve" not in probe:
        since = H.has_since(hand)
        probe = {**probe_key, "since": since, "serve": since and H.has_serve(hand)}   # list --since 없는 손은 판이 안 돈다
        state["probe"] = probe
    return probe


# ── 판 하기 ─────────────────────────────────────────────────────────────────────

def note_full_every(state: dict[str, Any], args) -> None:
    """준 전체 주기(`--full-every`)를 지금 모습에 적는다 — 걸린 작업의 판은 늘 그 값을 주므로, 주기를 안 준 판(정한 시각의 시계가 청한 판 ·
    대화의 판)이 그 PC 가 건 주기를 읽는다(`full_every_of`). 안 줬으면 아무것도 안 한다."""
    if args.full_every is not None:
        state["full_every"] = args.full_every


def full_every_of(state: dict[str, Any], args) -> int:
    """이 판의 전체 주기(분) — 준 것(`--full-every`), 없으면 걸린 작업의 판이 마지막으로 준 것(`note_full_every`), 그것도 없으면 기본."""
    noted = state.get("full_every")
    return args.full_every or (noted if isinstance(noted, int) and 0 < noted < C.PENDING_MAX_MIN else C.FULL_EVERY_MIN)


def wants_full(state: dict[str, Any], at: datetime, args) -> bool:
    """이 판이 메일함 전체를 봐야 하나 — `--full` · 지금 모습이 없다 · 전체 판을 해 본 적이 없다 · 전체 주기(`full_every_of`)가 지났다(`--new` 가
    아니면)."""
    last_full_try = tm.parse(state.get("last_full_try"))
    return (args.full or state.get("picture") is None or last_full_try is None
            or (not args.new and at - last_full_try >= timedelta(minutes=full_every_of(state, args))))


def sweep(run: Run, state: dict[str, Any], folder: pathlib.Path, at: datetime, args) -> Ended:
    """판을 골라(전체 · 새 메일) 돌리고 손을 거둔 뒤, 손이 멈춘 까닭을 끝 낱말로 바꾼다. 다 봤으면 세션 기다림을 걷고 본 때를 적는다."""
    mode = FULL if wants_full(state, at, args) else NEW
    try:
        try:
            outcome, events, info = run_full(run, state, folder, at) if mode == FULL else run_new(run, state, at)
        finally:
            run.close()                  # 판을 맺기(보고 띄우기 포함) 전에 손을 거둔다
    except SessionLost as exc:
        mark_session_lost(state, at, str(exc))
        return Ended(mode, SESSION, info={"said": str(exc)})
    except HandFailed as exc:
        return Ended(mode, HAND_ERROR, info={"said": str(exc)})
    except HL.ShapeError as exc:
        return Ended(mode, SHAPE, info={"note": str(exc)})
    settle(state, outcome, at)
    return Ended(mode, outcome, events, info)


def settle(state: dict[str, Any], outcome: str, at: datetime) -> None:
    """손이 답한 판의 지금 모습 — 세션 기다림을 걷고, 다 본 판이면 본 때를 적는다."""
    state.pop("session", None)
    if outcome in (DONE, FIRST):
        state["last_look"] = tm.stamp(at)


def mark_session_lost(state: dict[str, Any], at: datetime, said: str) -> None:
    """끊긴 세션을 적는다 — 다음 두드림 때를 두 배씩(상한까지) 늘린다."""
    old = state.get("session") or {}
    step = int(old.get("step", 0)) + 1
    wait = min(C.BACKOFF_FIRST_MIN * 2 ** (step - 1), C.BACKOFF_MAX_MIN)
    state["session"] = {"lost_at": old.get("lost_at") or tm.stamp(at), "next_try": tm.stamp(at + timedelta(minutes=wait)), "step": step,
                        "said": said}


def add_new(state: dict[str, Any], mails: Iterable[dict[str, Any]], at: datetime, journal: D.Journal) -> list[dict[str, Any]]:
    """처음 보는 메일을 지금 모습에 더하고 그 바뀜을 낸다 — 아는 메일은 안 건드린다(바뀜은 전체 판의 견주기가 낸다)."""
    stamp, last_look = tm.stamp(at), tm.parse(state.get("last_look"))
    events: list[dict[str, Any]] = []
    for mail in mails:
        if mail["unid"] not in state["mails"]:
            state["mails"][mail["unid"]], made = D.new_mail(mail, stamp, last_look, state["gone"], journal)
            events += made
    return events


# ── 새 메일 판 ───────────────────────────────────────────────────────────────────

@dataclass
class SincePages:
    """「이 시각 뒤」 목록을 끝까지 이어 받은 것 — 메일(번호마다 처음 것) · 쪽마다 댄 총수 · 다 봤나 · 못 내려간 자리 · 가장 늦은 메일."""
    mails: dict[str, dict[str, Any]] = field(default_factory=dict)
    totals: set[int] = field(default_factory=set)
    reached: bool = True
    stuck: list[str] = field(default_factory=list)
    lonely: int = 0
    unfilled: int = 0
    latest: tuple[str, str] | None = None


def not_ahead(date: str, at: datetime) -> str:
    """메일의 때 글자를 지금보다 뒤가 아니게 — 앞날의 때를 단 메일 하나가 이음점을 앞질러 보내 그 사이 메일을 놓치지 않게."""
    return min(date, tm.seoul(at, C.MAIL_DATE))


def cursor_date(state: dict[str, Any], at: datetime) -> str:
    """「이 시각 뒤」의 시각 — 이음점(가장 늦은 메일의 때)이고, 지금보다 뒤면 지금이다(앞날의 때를 단 메일 하나가 이음점을 앞질러 보내지 않게)."""
    picked = (state.get("cursor") or {}).get("date") or tm.seoul(tm.parse(state["picture"]["started"]), C.MAIL_DATE)
    return not_ahead(picked, at)


def since_pages(run: Run, since: str, folders: list[str]) -> SincePages:
    """「이 시각 뒤」 목록을 끝까지(--start 로 이어) 받는다 — 쪽 수의 안전 상한에 닿으면 다 못 본 것이다."""
    pages = SincePages()
    start = 1
    for _ in range(C.SINCE_PAGES_MOST):
        got = run.hand(["list", "--since", since, "--start", str(start)])
        if got.code != C.HAND_EXIT_OK:
            raise HandFailed(got.said)
        page = HL.parse_since(got.lines, folders, start)
        pages.totals.add(page.total)
        pages.reached = pages.reached and page.reached
        pages.stuck += page.stuck
        pages.lonely, pages.unfilled = max(pages.lonely, page.lonely), max(pages.unfilled, page.unfilled)
        pages.latest = pages.latest or page.latest
        for m in page.mails:
            pages.mails.setdefault(m["unid"], m)
        if page.next_start is None:
            break
        start = page.next_start
    else:
        pages.reached = False
    return pages


def since_short(pages: SincePages, reached: bool) -> list[dict[str, str]]:
    """새 메일 판이 덜 본 자리 — 손이 훑는 상한에 닿은 상자마다, 그런 상자 없이 덜 봤으면 받은편지함 하나(목록이 바뀌었나 · 안전 상한)."""
    keys = {"받은편지함": D.INBOX, "보낸편지함": D.SENT}
    short = [{"box": keys.get(b) or D.box_key(D.FOLDER, b[len(HL.FOLDER_WORD):]), "why": "cap"} for b in dict.fromkeys(pages.stuck)]
    if not short and not reached:
        short = [{"box": D.INBOX, "why": "changed" if len(pages.totals) > 1 else "guard"}]
    return short


def saw_all(pages: SincePages) -> bool:
    """「이 시각 뒤」 목록을 다 봤나 — 손이 다 봤다고 했고, 못 내려간 자리가 없고, 쪽마다 댄 총수가 하나다(받는 사이 목록이 안 바뀌었다)."""
    return pages.reached and not pages.stuck and len(pages.totals) <= 1


def run_new(run: Run, state: dict[str, Any], at: datetime) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """새 메일 판 — 「이 시각 뒤」 쪽을 다 받고, 다 봤나를 가르고, 처음 보는 메일을 더하고, 다 봤으면 이음점을 옮긴다. 내는 것 — (결과, 바뀜,
    판 값)."""
    since = cursor_date(state, at)
    pages = since_pages(run, since, state["picture"].get("folders") or [])
    reached = saw_all(pages)
    events = add_new(state, pages.mails.values(), at, D.Journal.load(st.home()))
    if reached:
        if pages.latest and tm.mail_time(pages.latest[0]):
            state["cursor"] = {"date": not_ahead(pages.latest[0], at), "unid": pages.latest[1]}
        state["last_new_done"] = tm.stamp(at)
    info = {"since": since, "listed": len(pages.mails), "lonely": pages.lonely, "unfilled": pages.unfilled, "short": since_short(pages, reached)}
    return (DONE if reached else PARTIAL), events, info


# ── 메일함 전체 판 ────────────────────────────────────────────────────────────────

@dataclass
class Frame:
    """전체 판의 틀 — 폴더 목록 · 규칙 · 규칙을 이번에 읽었나 · 볼 상자들."""
    folders: list[str]
    rules: list[dict[str, str]]
    rules_read: bool
    boxes: list[tuple[str, str]]


def sweep_box(run: Run, box: str, folder: str) -> dict[str, Any]:
    """상자 하나를 끝까지 읽는다 — 끝을 가르는 법은 `references/DESIGN.md` 「상자 하나를 끝까지」.
    내는 것 — {mails, complete, why, said, unfilled, read_at, paged — 한 번에 다 못 받은 상자인가(쪽이 찼거나 둘째 쪽에 줄이 왔다)}."""
    read_at = tm.stamp(tm.now())
    where = ["--folder", folder] if box == D.FOLDER else ["--sent"] if box == D.SENT else []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    start, unfilled, paged = 1, 0, False
    for _ in range(C.PAGES_MOST):
        got = run.hand(["list", *where, "--count", str(C.PAGE), "--start", str(start)])
        if got.code == C.HAND_EXIT_CONFIG and HL.NO_FOLDER.match(got.said):
            return {"mails": rows, "complete": False, "why": "folder-gone", "said": got.said, "read_at": read_at}
        if got.code != C.HAND_EXIT_OK:
            return {"mails": rows, "complete": False, "why": f"hand-{got.code}", "said": got.said, "read_at": read_at}
        page = HL.parse_list(got.lines, box, folder)
        unfilled += page.unfilled
        fresh = [m for m in page.mails if m["unid"] not in seen]
        if not fresh:
            done = not page.mails or (bool(rows) and all(m["unid"] == rows[-1]["unid"] for m in page.mails))
            return {"mails": rows, "complete": done, "why": "" if done else "repeated", "unfilled": unfilled, "read_at": read_at,
                    "paged": paged}
        seen.update(m["unid"] for m in fresh)
        paged = paged or bool(rows) or len(page.mails) >= C.PAGE
        rows += fresh
        start += len(page.mails)
        if run.over_budget():
            return {"mails": rows, "complete": False, "why": "budget", "read_at": read_at}
    return {"mails": rows, "complete": False, "why": "guard", "read_at": read_at}


def mailbox_frame(run: Run, state: dict[str, Any]) -> Frame:
    """폴더 목록과 규칙을 손에서 받는다 — 규칙을 못 받으면 지난 모습의 규칙을 그대로 쓴다. 볼 상자는 받은편지함 · 폴더마다 · 보낸편지함."""
    got = run.hand(["folders"])
    if got.code != C.HAND_EXIT_OK:
        raise HandFailed(got.said)
    folders = HL.parse_folders(got.lines)
    got = run.hand(["rules"])
    rules_read = got.code == C.HAND_EXIT_OK
    rules = HL.parse_rules(got.lines) if rules_read else (state.get("picture") or {}).get("rules") or []
    return Frame(folders, rules, rules_read, [(D.INBOX, "")] + [(D.FOLDER, p) for p in folders] + [(D.SENT, "")])


def load_pending(folder: pathlib.Path, at: datetime) -> dict[str, Any] | None:
    """다 못 본 판의 다 본 상자들 — 없거나 못 읽으면 None(메일함에서 다시 읽으면 되는 이음 자료라 처음부터 본다). 기한(`PENDING_MAX_MIN`)을
    넘은 상자 그림은 버린다."""
    try:
        data = st.read_json(folder / C.PENDING_FILE)
    except st.Unreadable:
        return None
    if data is None or data.get("format") != C.FORMAT:
        return None
    oldest = at - timedelta(minutes=C.PENDING_MAX_MIN)
    boxes = {k: v for k, v in (data.get("boxes") or {}).items() if (tm.parse(v.get("read_at")) or oldest) > oldest}
    return {**data, "boxes": boxes}


def save_pending(folder: pathlib.Path, folders: list[str], done: dict[str, Any]) -> None:
    """다 본 상자들을 이어 볼 파일에 남긴다 — 다음 판이 잇는다."""
    st.write_json(folder / C.PENDING_FILE, {"format": C.FORMAT, "folders": folders, "boxes": done})


def drop_pending(folder: pathlib.Path) -> None:
    """다 본 판이 이어 볼 파일을 걷는다."""
    (folder / C.PENDING_FILE).unlink(missing_ok=True)


def walk_boxes(run: Run, boxes: list[tuple[str, str]], done: dict[str, Any]) -> list[dict[str, str]]:
    """다 본 상자(`done`)를 건너 상자마다 끝까지 읽어 `done` 에 더한다 — 판의 시간 상한을 넘으면 남은 상자는 덜 본 자리다. 내는 것 — 덜 본 자리."""
    short: list[dict[str, str]] = []
    for box, path in boxes:
        key = D.box_key(box, path)
        if key in done:
            continue
        if run.over_budget():
            short.append({"box": key, "why": "budget"})
            continue
        swept = sweep_box(run, box, path)
        if swept["complete"]:
            done[key] = {"read_at": swept["read_at"], "unfilled": swept.get("unfilled", 0), "mails": swept["mails"],
                         "paged": bool(swept.get("paged"))}
        else:
            short.append({"box": key, "why": swept["why"], **({"said": swept["said"]} if swept.get("said") else {})})
    return short


def one_picture(done: dict[str, Any], boxes: list[tuple[str, str]]) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    """다 본 상자들을 메일함 한 모습으로 합친다 — 두 상자에 선 메일은 나중에 읽은 상자가 지금 자리다(읽는 사이 옮겨졌다). 내는 것 — (상자마다
    읽은 때, 메일 번호마다 메일)."""
    read_at = {key: v["read_at"] for key, v in done.items() if key in {D.box_key(b, p) for b, p in boxes}}
    seen: dict[str, dict[str, Any]] = {}
    when: dict[str, str] = {}
    for key, got_box in done.items():
        if key not in read_at:
            continue
        for mail in got_box["mails"]:   # 두 상자에 서면 나중에 읽은 상자가 지금 자리다 — 읽는 사이 옮겨졌다
            if mail["unid"] not in seen or got_box["read_at"] > when[mail["unid"]]:
                seen[mail["unid"]], when[mail["unid"]] = mail, got_box["read_at"]
    return read_at, seen


def resume(folder: pathlib.Path, at: datetime, folders: list[str]) -> tuple[dict[str, Any], str]:
    """이어 볼 상자들 — 다 못 본 판이 남긴 다 본 상자. 폴더 목록이 그 사이 바뀌었으면 버리고 처음부터 본다. 내는 것 — (다 본 상자, 판 메모)."""
    pending = load_pending(folder, at)
    note = []
    if pending and pending.get("folders") != folders:
        pending = None
        note.append("폴더 목록이 바뀌어 이어 보던 판을 버리고 처음부터 봤다")
    return dict((pending or {}).get("boxes") or {}), " · ".join(note)


def compare_picture(state: dict[str, Any], picture: dict[str, Any] | None, frame: Frame, seen: dict[str, dict[str, Any]],
                    read_at: dict[str, str], done: dict[str, Any], at: datetime, journal: D.Journal) -> tuple[str, list[dict[str, Any]]]:
    """다 본 메일함을 지난 모습과 견줘 메일 · 폴더 · 규칙의 바뀜을 내고 지금 모습의 메일을 고친다 — 지난 모습이 없으면 바닥만 적는다(첫 판).
    내는 것 — (끝 낱말, 바뀜)."""
    if picture is None:
        state["mails"] = {u: {**m, "first_seen": None} for u, m in seen.items()}
        return FIRST, []
    stamp, last_look = tm.stamp(at), tm.parse(state.get("last_look"))
    since = tm.parse(picture["started"])
    events = D.compare_folders(picture.get("folders") or [], frame.folders, stamp, journal, since)
    if frame.rules_read and picture.get("rules_read", True):
        events += D.compare_rules(picture.get("rules") or [], frame.rules, stamp, journal, since)
    paged = {key for key, v in done.items() if v.get("paged")}
    state["mails"], made = D.compare(state["mails"], picture["started"], seen, read_at, paged, stamp, last_look, state["gone"], journal)
    return DONE, events + made


def latest_cursor(mails: dict[str, dict[str, Any]], at: datetime) -> dict[str, str] | None:
    """다 본 메일함에서 다시 잡은 이음점 — 자리를 확인 중이 아닌 메일 가운데 가장 늦은 때(지금보다 뒤면 지금). 때 있는 메일이 없으면 None."""
    dated = [(m["date"], u) for u, m in mails.items() if m.get("date") and not m.get("missing_since")]
    if not dated:
        return None
    date, unid = max(dated)
    return {"date": not_ahead(date, at), "unid": unid}


def new_picture(state: dict[str, Any], frame: Frame, read_at: dict[str, str], done: dict[str, Any], at: datetime) -> None:
    """다 본 판의 새 지금 모습 — 메일함의 그림(때 · 폴더 · 규칙 · 상자마다 읽은 때) · 이음점 · 다 본 때를 적는다."""
    state["picture"] = {"started": min(read_at.values()), "ended": tm.stamp(tm.now()), "folders": frame.folders, "rules": frame.rules,
                        "rules_read": frame.rules_read, "boxes": {k: {"read_at": done[k]["read_at"], "unfilled": done[k].get("unfilled", 0)}
                                                                  for k in read_at}}
    state["cursor"] = latest_cursor(state["mails"], at) or state.get("cursor")
    state["last_full_done"] = tm.stamp(at)
    state["last_new_done"] = tm.stamp(at)


def run_full(run: Run, state: dict[str, Any], folder: pathlib.Path, at: datetime) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """메일함 전체 판 — 폴더 · 규칙을 받고, 이어 볼 상자를 잇고, 상자를 돌고, 덜 봤으면 다 본 상자를 남기고(그 새 메일은 적는다), 다 봤으면 한
    모습으로 합쳐 지난 모습과 견주고 새 지금 모습을 짓는다. 내는 것 — (결과, 바뀜, 판 값)."""
    frame = mailbox_frame(run, state)
    picture = state.get("picture")
    done, note = resume(folder, at, frame.folders)
    try:
        short = walk_boxes(run, frame.boxes, done)
    except SessionLost:
        state["last_full_try"] = tm.stamp(at)
        save_pending(folder, frame.folders, done)   # 다 본 상자는 다음 판이 잇는다
        raise
    journal = D.Journal.load(st.home())
    info: dict[str, Any] = {"boxes": len(frame.boxes), "short": short, "note": note, "unfilled": sum(v.get("unfilled", 0) for v in done.values())}
    state["last_full_try"] = tm.stamp(at)
    if short:
        save_pending(folder, frame.folders, done)
        events = add_new(state, (m for got_box in done.values() for m in got_box["mails"]), at, journal) if picture is not None else []
        return PARTIAL, events, info
    read_at, seen = one_picture(done, frame.boxes)
    outcome, events = compare_picture(state, picture, frame, seen, read_at, done, at, journal)
    new_picture(state, frame, read_at, done, at)
    drop_pending(folder)
    return outcome, events, info


# ── 판 맺기 ─────────────────────────────────────────────────────────────────────

def finish(folder: pathlib.Path, lock: st.Lock, state: dict[str, Any], at: datetime, ended: Ended, run: Run | None, notes: list[str]) -> int:
    """판을 맺는다 — 판 기록을 짓고, 잠금을 잃었으면(풀린 판이 깨어났다) 아무것도 안 쓰고, 아니면 바뀜 · 지금 모습 · 판 기록을 쓰고 판 끝
    한 줄을 낸다. 종료 값 — 0 됐다 · 1 멈췄다."""
    record = round_record(at, ended, run, notes, state)
    if not lock.owns():
        print(LOST_LOCK)
        return EXIT_STOPPED
    save_round(folder, state, record, ended.events, at)
    print(SW.summary(record))
    return EXIT_OK if record["outcome"] in (DONE, FIRST) else EXIT_STOPPED


def round_record(at: datetime, ended: Ended, run: Run | None, notes: list[str], state: dict[str, Any]) -> dict[str, Any]:
    """판 기록 한 줄 — 때 · 갈래 · 끝 · 손 부르기 · 줄 · 초 · 새 메일과 바뀜의 수 · 판 값 · 메모, 메일함 전체를 다 본 판은 받은편지함 셈."""
    record = {"started": tm.stamp(at), "ended": tm.stamp(tm.now()), "mode": ended.mode, "outcome": ended.outcome,
              "calls": run.calls if run else 0, "lines": run.lines if run else 0, "seconds": run.seconds() if run else 0,
              "new": sum(e["kind"] == D.NEW for e in ended.events), "changes": sum(e["kind"] != D.NEW for e in ended.events),
              **{k: v for k, v in ended.info.items() if v not in (None, "", [], 0)}}
    if notes:
        record["note"] = " · ".join([*notes, *([record["note"]] if record.get("note") else [])])
    if ended.mode == FULL and ended.outcome in (DONE, FIRST):
        record["inbox"] = inbox_count(state)
    return record


def save_round(folder: pathlib.Path, state: dict[str, Any], record: dict[str, Any], events: list[dict[str, Any]], at: datetime) -> None:
    """판을 쓴다 — 바뀜마다 판의 때를 달고, 지금 모습에 마지막 판을 적고, 바뀜 → 접기 → 지금 모습 → 판 기록 차례로 쓴다. 지금 모습을 못
    바꿔 끼우면 판 기록의 끝을 그것으로 바꾼다."""
    for e in events:
        e["run"] = record["started"]
    state["last_run"] = {k: record[k] for k in ("started", "ended", "mode", "outcome") if k in record}
    for k in ("note", "said", "short"):
        if k in record:
            state["last_run"][k] = record[k]
    try:
        st.append(folder / C.EVENTS_FILE, events)
        compact(folder, state, at)
        st.write_json(folder / C.STATE_FILE, state)
    except st.SwapFailed as exc:
        record["outcome"], record["note"] = SWAP, str(exc)
    st.append(folder / C.RUNS_FILE, [record])


def compact(folder: pathlib.Path, state: dict[str, Any], at: datetime) -> None:
    """오래된 새 메일 · 바뀜 · 판 기록을 접고 사라진 메일의 기억을 덜어 낸다 — 하루에 한 번. 지금 모습은 늘 한 장이다."""
    last = tm.parse(state.get("compacted"))
    if last is not None and at - last < timedelta(hours=C.COMPACT_EVERY_H):
        return
    edge = tm.stamp(at - timedelta(days=C.RETAIN_DAYS))
    for name, key in ((C.EVENTS_FILE, "at"), (C.RUNS_FILE, "started")):
        try:
            rows, bad = st.read_jsonl(folder / name)
        except st.Unreadable:
            continue                     # 못 읽은 기록은 접지 않는다 — 빈 것으로 읽어 새로 쓰면 기록이 다 사라진다
        kept = [r for r in rows if str(r.get(key) or "") >= edge]
        if len(kept) != len(rows) or bad:
            st.rewrite_jsonl(folder / name, kept)
    gone_edge = tm.stamp(at - timedelta(days=C.GONE_KEEP_DAYS))
    state["gone"] = {u: g for u, g in (state.get("gone") or {}).items() if str(g.get("at") or "") >= gone_edge}
    state["compacted"] = tm.stamp(at)


def inbox_count(state: dict[str, Any]) -> list[int]:
    """받은편지함의 [통 수, 안 읽음] — 자리를 확인 중인 메일은 뺀다. 메일함 전체를 다 본 판만 싣는다(`reader.py signals` 가 읽는다)."""
    inbox = [m for m in (state.get("mails") or {}).values() if m.get("box") == D.INBOX and not m.get("missing_since")]
    return [len(inbox), sum(bool(m.get("unread")) for m in inbox)]
