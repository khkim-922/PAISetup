"""메일함 스캔 — 회사 메일 손을 명령으로 불러 메일함의 지금을 사용자 폴더에 쌓고, 그 스캔을 작업 스케줄러에 걸고 · 보고 · 끈다.

    python -X utf8 -I scan.py run [--full | --new] [--now] [--hand <mail.py>] [--full-every 분]
    python -X utf8 -I scan.py register [--every 분] [--full-every 분] [--hand <mail.py>] [--brief-at [HH:MM …] | --brief-off]
                                       [--claude <claude>] [--brief-login | --brief-no-login] [--dry-run | --validate]
    python -X utf8 -I scan.py brief (--at [HH:MM …] | --off) [--login | --no-login] [--claude <claude>] [--dry-run]
    python -X utf8 -I scan.py status [--dry-run]
    python -X utf8 -I scan.py unregister [--dry-run]

run — 한 판. 지금 모습이 없거나 `--full-every` 분이 지났으면 메일함 전체(상자마다 메일 머리 · 폴더 목록 · 규칙)를 다시 보고 지난 모습과
    견준 바뀜을 적고, 그 사이에는 「이 시각 뒤」 새 메일만 더한다. 손의 읽는 명령만 부른다 — 메일함 · 본문 · 모델에 안 닿는다
register · status · unregister — 작업 스케줄러의 작업 하나(`scan_task.TASK_NAME`)를 걸고 · 보이고 · 지운다. `--dry-run` 은 보이기만,
    `--validate` 는 작업 스케줄러가 정의를 받나만 묻는다
brief — 정한 시각의 보고(보고 시각표 · 시각 하나 이상)와 띄울 claude 를 사용자 폴더에 남기거나(`--at`) 내린다(`--off`). 시각은 전부를
    준다 — 준 시각들이 시각표를 바꾼다. 띄우는 판정은 `scan_brief.py` 가 든다. `--claude` 를 안 주면 걸려 있던 claude 를 그대로 쓴다.
    스스로 로그인(`--login` · register 는 `--brief-login`)은 켠 PC 의 그날 첫 시각에서만 선다 — 안 주면 걸려 있던 값을 그대로 둔다

남기는 것 — 사용자 폴더 `mailbox-scan/` 의 `state.json`(지금 모습) · `events.jsonl`(새 메일과 바뀜) · `runs.jsonl`(판마다의 값) ·
`pending.json`(이어 볼 상자) · `brief*`(정한 시각의 보고). 왜 이 꼴인가는 `references/DESIGN.md` 가 든다.

종료 값 — 0 됐다(앞 판이 돌아 건너뛴 것도) · 1 멈췄다(세션 · 손 · 손의 글 꼴 · 다 못 봄 · 작업 스케줄러가 거절 — 다음 걸음을 끝 줄이
말한다) · 2 인자가 틀렸다.
"""

from __future__ import annotations

import argparse
import json
import locale
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 모듈 — `-I` 로 돌아도 싣는다
import scan_brief as B  # noqa: E402
import scan_const as C  # noqa: E402
import scan_diff as D  # noqa: E402
import scan_hand as H  # noqa: E402
import scan_store as st  # noqa: E402
import scan_task as T  # noqa: E402

EXIT_OK, EXIT_STOPPED = 0, 1
FULL, NEW = C.MODE_FULL, C.MODE_NEW
DONE, PARTIAL, SESSION, BUSY = C.RUN_DONE, C.RUN_PARTIAL, C.RUN_SESSION, C.RUN_BUSY
HAND_MISSING, HAND_OLD, HAND_ERROR, SHAPE, SWAP = C.RUN_HAND_MISSING, C.RUN_HAND_OLD, C.RUN_HAND_ERROR, C.RUN_SHAPE, C.RUN_SWAP
FIRST = C.RUN_FIRST      # 첫 판 — 바닥만 적었다


class SessionLost(Exception):
    """손이 종료 3 을 냈다 — 사내 세션이 없다 · 끊겼다."""


class HandFailed(Exception):
    """손이 0 · 3 밖의 종료 값을 냈다 — `said` 가 손의 말이다."""


class Run:
    """한 판의 셈 — 손 부르기 · 받은 줄 · 시간의 상한. 손이 `serve` 를 받으면 판 내내 손 하나에 잇달아 묻고(`H.Served`), 옛 판의 손이면
    명령마다 띄운다(`H.call`) — 어느 쪽이든 메일함에 가는 요청과 그 차례는 같다."""

    def __init__(self, hand: pathlib.Path, served: bool):
        self.hand_path = hand
        self.served = H.Served(hand) if served else None
        self.calls = 0
        self.lines = 0
        self.began = time.monotonic()

    def over_budget(self) -> bool:
        return time.monotonic() - self.began >= C.RUN_BUDGET_S

    def hand(self, args: list[str]) -> H.Called:
        self.calls += 1
        got = self.served.ask(args) if self.served else H.call(self.hand_path, args)
        self.lines += len(got.lines)
        if got.code == C.HAND_EXIT_SESSION:
            raise SessionLost(got.said)
        return got

    def close(self) -> None:
        if self.served:
            self.served.close()

    def seconds(self) -> float:
        return round(time.monotonic() - self.began, 1)


# ── 판 하나 ────────────────────────────────────────────────────────────────────

def fresh_state() -> dict[str, Any]:
    return {"format": C.FORMAT, "mails": {}, "gone": {}}


def cursor_date(state: dict[str, Any], at: datetime) -> str:
    """「이 시각 뒤」의 시각 — 이음점(가장 늦은 메일의 때)이고, 지금보다 뒤면 지금이다(앞날의 때를 단 메일 하나가 이음점을 앞질러 보내지 않게)."""
    now_text = st.seoul(at, C.MAIL_DATE)
    picked = (state.get("cursor") or {}).get("date") or st.seoul(st.parse(state["picture"]["started"]), C.MAIL_DATE)
    return min(picked, now_text)


def latest_cursor(mails: dict[str, dict[str, Any]], at: datetime) -> dict[str, str] | None:
    dated = [(m["date"], u) for u, m in mails.items() if m.get("date") and not m.get("missing_since")]
    if not dated:
        return None
    date, unid = max(dated)
    return {"date": min(date, st.seoul(at, C.MAIL_DATE)), "unid": unid}


def run_new(run: Run, state: dict[str, Any], at: datetime) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """새 메일만 — 「이 시각 뒤」 목록을 끝까지(--start 로 이어) 받아 처음 보는 메일을 더한다. 아는 메일은 안 건드린다(바뀜은 전체 판이 낸다)."""
    since = cursor_date(state, at)
    folders = state["picture"].get("folders") or []
    got_mails: dict[str, dict[str, Any]] = {}
    totals, reached, stuck, lonely, unfilled, latest = set(), True, [], 0, 0, None
    start = 1
    for _ in range(C.SINCE_PAGES_MOST):
        got = run.hand(["list", "--since", since, "--start", str(start)])
        if got.code != C.HAND_EXIT_OK:
            raise HandFailed(got.said)
        page = H.parse_since(got.lines, folders, start)
        totals.add(page.total)
        reached = reached and page.reached
        stuck += page.stuck
        lonely, unfilled = max(lonely, page.lonely), max(unfilled, page.unfilled)
        latest = latest or page.latest
        for m in page.mails:
            got_mails.setdefault(m["unid"], m)
        if page.next_start is None:
            break
        start = page.next_start
    else:
        reached = False
    reached = reached and not stuck and len(totals) <= 1
    stamp = st.stamp(at)
    last_look = st.parse(state.get("last_look"))
    events: list[dict[str, Any]] = []
    journal = D.Journal.load(st.home())
    for unid, mail in got_mails.items():
        if unid in state["mails"]:
            continue
        state["mails"][unid], made = D.new_mail(mail, stamp, last_look, state["gone"], journal)
        events += made
    if reached:
        if latest and st.mail_time(latest[0]):
            state["cursor"] = {"date": min(latest[0], st.seoul(at, C.MAIL_DATE)), "unid": latest[1]}
        state["last_new_done"] = stamp
    keys = {"받은편지함": D.INBOX, "보낸편지함": D.SENT}
    short = [{"box": keys.get(b) or D.box_key(D.FOLDER, b[len(H.FOLDER_WORD):]), "why": "cap"} for b in dict.fromkeys(stuck)]
    if not short and not reached:
        short = [{"box": D.INBOX, "why": "changed" if len(totals) > 1 else "guard"}]
    info = {"since": since, "listed": len(got_mails), "lonely": lonely, "unfilled": unfilled, "short": short}
    return (DONE if reached else PARTIAL), events, info


def sweep_box(run: Run, box: str, folder: str) -> dict[str, Any]:
    """상자 하나를 끝까지 읽는다 — 끝을 가르는 법은 `references/DESIGN.md` 「상자 하나를 끝까지」.
    내는 것 — {mails, complete, why, said, unfilled, read_at, paged — 한 번에 다 못 받은 상자인가(쪽이 찼거나 둘째 쪽에 줄이 왔다)}."""
    read_at = st.stamp(st.now())
    where = ["--folder", folder] if box == D.FOLDER else ["--sent"] if box == D.SENT else []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    start, unfilled, paged = 1, 0, False
    for _ in range(C.PAGES_MOST):
        got = run.hand(["list", *where, "--count", str(C.PAGE), "--start", str(start)])
        if got.code == C.HAND_EXIT_CONFIG and H.NO_FOLDER.match(got.said):
            return {"mails": rows, "complete": False, "why": "folder-gone", "said": got.said, "read_at": read_at}
        if got.code != C.HAND_EXIT_OK:
            return {"mails": rows, "complete": False, "why": f"hand-{got.code}", "said": got.said, "read_at": read_at}
        page = H.parse_list(got.lines, box, folder)
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


def load_pending(folder: pathlib.Path, at: datetime) -> dict[str, Any] | None:
    """다 못 본 판의 다 본 상자들 — 없거나 못 읽으면 None. 기한(`PENDING_MAX_MIN`)을 넘은 상자 그림은 버린다."""
    try:
        data = json.loads((folder / C.PENDING_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("format") != C.FORMAT:
        return None
    oldest = at - timedelta(minutes=C.PENDING_MAX_MIN)
    boxes = {k: v for k, v in (data.get("boxes") or {}).items() if (st.parse(v.get("read_at")) or oldest) > oldest}
    return {**data, "boxes": boxes}


def run_full(run: Run, state: dict[str, Any], folder: pathlib.Path, at: datetime) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """메일함 전체를 보고 다 봤으면 지난 모습과 견준다 — 못 다 봤으면 다 본 상자를 `PENDING_FILE` 에 남긴다. 내는 것 — (결과, 바뀜, 판 값)."""
    got = run.hand(["folders"])
    if got.code != C.HAND_EXIT_OK:
        raise HandFailed(got.said)
    folders = H.parse_folders(got.lines)
    picture = state.get("picture")
    got = run.hand(["rules"])
    rules_read = got.code == C.HAND_EXIT_OK
    rules = H.parse_rules(got.lines) if rules_read else (picture or {}).get("rules") or []
    pending = load_pending(folder, at)
    note = []
    if pending and pending.get("folders") != folders:
        pending = None
        note.append("폴더 목록이 바뀌어 이어 보던 판을 버리고 처음부터 봤다")
    done: dict[str, Any] = dict((pending or {}).get("boxes") or {})
    boxes = [(D.INBOX, "")] + [(D.FOLDER, p) for p in folders] + [(D.SENT, "")]
    short: list[dict[str, str]] = []
    try:
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
    except SessionLost:
        state["last_full_try"] = st.stamp(at)
        st.write_json(folder / C.PENDING_FILE, {"format": C.FORMAT, "folders": folders, "boxes": done})   # 다 본 상자는 다음 판이 잇는다
        raise
    stamp = st.stamp(at)
    last_look = st.parse(state.get("last_look"))
    journal = D.Journal.load(st.home())
    events: list[dict[str, Any]] = []
    info: dict[str, Any] = {"boxes": len(boxes), "short": short, "note": " · ".join(note),
                            "unfilled": sum(v.get("unfilled", 0) for v in done.values())}
    state["last_full_try"] = stamp
    if short:
        st.write_json(folder / C.PENDING_FILE, {"format": C.FORMAT, "folders": folders, "boxes": done})
        if picture is not None:
            for key, got_box in done.items():
                for mail in got_box["mails"]:
                    if mail["unid"] not in state["mails"]:
                        state["mails"][mail["unid"]], made = D.new_mail(mail, stamp, last_look, state["gone"], journal)
                        events += made
        return PARTIAL, events, info
    read_at = {key: v["read_at"] for key, v in done.items() if key in {D.box_key(b, p) for b, p in boxes}}
    seen: dict[str, dict[str, Any]] = {}
    when: dict[str, str] = {}
    for key, got_box in done.items():
        if key not in read_at:
            continue
        for mail in got_box["mails"]:   # 두 상자에 서면 나중에 읽은 상자가 지금 자리다 — 읽는 사이 옮겨졌다
            if mail["unid"] not in seen or got_box["read_at"] > when[mail["unid"]]:
                seen[mail["unid"]], when[mail["unid"]] = mail, got_box["read_at"]
    if picture is None:
        state["mails"] = {u: {**m, "first_seen": None} for u, m in seen.items()}
        outcome = FIRST
    else:
        since = st.parse(picture["started"])
        events += D.compare_folders(picture.get("folders") or [], folders, stamp, journal, since)
        if rules_read and picture.get("rules_read", True):
            events += D.compare_rules(picture.get("rules") or [], rules, stamp, journal, since)
        paged = {key for key, v in done.items() if v.get("paged")}
        state["mails"], made = D.compare(state["mails"], picture["started"], seen, read_at, paged, stamp, last_look, state["gone"],
                                         journal)
        events += made
        outcome = DONE
    state["picture"] = {"started": min(read_at.values()), "ended": st.stamp(st.now()), "folders": folders, "rules": rules,
                        "rules_read": rules_read, "boxes": {k: {"read_at": done[k]["read_at"], "unfilled": done[k].get("unfilled", 0)}
                                                            for k in read_at}}
    state["cursor"] = latest_cursor(state["mails"], at) or state.get("cursor")
    state["last_full_done"] = stamp
    state["last_new_done"] = stamp
    (folder / C.PENDING_FILE).unlink(missing_ok=True)
    return outcome, events, info


def compact(folder: pathlib.Path, state: dict[str, Any], at: datetime) -> None:
    """오래된 새 메일 · 바뀜 · 판 기록을 접고 사라진 메일의 기억을 덜어 낸다 — 하루에 한 번. 지금 모습은 늘 한 장이다."""
    last = st.parse(state.get("compacted"))
    if last is not None and at - last < timedelta(hours=C.COMPACT_EVERY_H):
        return
    edge = st.stamp(at - timedelta(days=C.RETAIN_DAYS))
    for name, key in ((C.EVENTS_FILE, "at"), (C.RUNS_FILE, "started")):
        rows, bad = st.read_jsonl(folder / name)
        kept = [r for r in rows if str(r.get(key) or "") >= edge]
        if len(kept) != len(rows) or bad:
            st.rewrite_jsonl(folder / name, kept)
    gone_edge = st.stamp(at - timedelta(days=C.GONE_KEEP_DAYS))
    state["gone"] = {u: g for u, g in (state.get("gone") or {}).items() if str(g.get("at") or "") >= gone_edge}
    state["compacted"] = st.stamp(at)


def session_back(state: dict[str, Any], hand: pathlib.Path | None, at: datetime, now_flag: bool) -> tuple[bool, str]:
    """세션이 끊긴 뒤 이번 주기에 두드려도 되나 — (돈다, 안 돌면 그 말). 세션 파일이 끊긴 뒤 새로 쓰였거나 다음 두드림 때가 왔거나 `--now`."""
    lost = state.get("session")
    if not lost:
        return True, ""
    lost_at, next_try = st.parse(lost.get("lost_at")), st.parse(lost.get("next_try"))
    path = H.session_file(hand) if hand else None
    try:
        relogged = path is not None and lost_at is not None and path.stat().st_mtime > lost_at.timestamp()
    except OSError:
        relogged = False
    if now_flag or relogged or next_try is None or at >= next_try:
        return True, ""
    return False, (f"사내 세션이 끊겨 {st.seoul(lost_at)}부터 멈춰 있다 — 다음 두드림은 {st.seoul(next_try)}. 다음: 대화에서 스킬 ep-login 으로 "
                   "EP 로그인을 하면 다음 주기에 바로 다시 돈다(지금 돌리려면 run --now)")


def mark_session_lost(state: dict[str, Any], at: datetime, said: str) -> None:
    old = state.get("session") or {}
    step = int(old.get("step", 0)) + 1
    wait = min(C.BACKOFF_FIRST_MIN * 2 ** (step - 1), C.BACKOFF_MAX_MIN)
    state["session"] = {"lost_at": old.get("lost_at") or st.stamp(at), "next_try": st.stamp(at + timedelta(minutes=wait)), "step": step,
                        "said": said}


def cmd_run(args) -> int:
    folder = st.scan_dir(make=True)
    at = st.now()
    lock, held = st.Lock.take(folder, at)
    if lock is None:
        st.append(folder / C.RUNS_FILE, [{"started": st.stamp(at), "mode": "-", "outcome": BUSY,
                                          "holder": (held or {}).get("started")}])
        print(f"[스캔 — 앞 판({st.seoul(st.parse((held or {}).get('started')))} 시작)이 돌고 있어 이번 주기는 건너뛰었다]")
        return EXIT_OK
    try:
        return _run(args, folder, at, lock, held)
    finally:
        lock.release()


def _run(args, folder: pathlib.Path, at: datetime, lock: st.Lock, cleared: dict[str, Any] | None) -> int:
    state, broken = st.load_state(folder)
    notes: list[str] = []
    if cleared is not None:
        notes.append(f"남은 잠금({st.seoul(st.parse(cleared.get('started'))) or '때 모름'} 시작)을 풀고 돌았다")
    if broken:
        notes.append(f"{broken} — 메일함에서 다시 짓는다")
        try:
            os.replace(folder / C.STATE_FILE, folder / (C.STATE_FILE + ".broken"))
        except OSError:
            pass
    state = state or fresh_state()
    try:
        hand = H.find_hand(args.hand)
    except H.HandMissing as exc:
        return finish(folder, lock, state, at, "-", HAND_MISSING, [], {"note": str(exc)}, None, notes)
    go, why = session_back(state, hand, at, args.now)
    if not go:
        print(f"[스캔 — {why}]")
        # 잠금을 쥔 판만 살펴본다 — 잃은 판이 띄우면 그날 칸을 못 적어 다시 띄운다
        said = B.after_run(state, folder, None, hand, at) if lock.owns() else ""
        if said:
            try:
                st.write_json(folder / C.STATE_FILE, state)
            except st.SwapFailed as exc:
                said += f" — ⚠ 지금 모습에 못 적었다: {exc}"
            print(said)
        return EXIT_STOPPED
    probe_key = {"path": str(hand), "mtime": hand.stat().st_mtime, "size": hand.stat().st_size}
    probe = state.get("probe") or {}
    if {k: probe.get(k) for k in probe_key} != probe_key or "serve" not in probe:
        since = H.has_since(hand)
        probe = {**probe_key, "since": since, "serve": since and H.has_serve(hand)}   # list --since 없는 손은 판이 안 돈다
        state["probe"] = probe
    run = Run(hand, served=probe["serve"])
    if not probe["since"]:
        return finish(folder, lock, state, at, "-", HAND_OLD, [], {"note": f"회사 메일 손이 「list --since」 없는 옛 판이다: {hand}"},
                      run, notes)
    last_full_try = st.parse(state.get("last_full_try"))
    full = (args.full or state.get("picture") is None or last_full_try is None
            or (not args.new and at - last_full_try >= timedelta(minutes=args.full_every)))
    mode = FULL if full else NEW
    try:
        try:
            outcome, events, info = run_full(run, state, folder, at) if full else run_new(run, state, at)
        finally:
            run.close()                  # 판을 맺기(보고 띄우기 포함) 전에 손을 거둔다
    except SessionLost as exc:
        mark_session_lost(state, at, str(exc))
        return finish(folder, lock, state, at, mode, SESSION, [], {"said": str(exc)}, run, notes)
    except HandFailed as exc:
        return finish(folder, lock, state, at, mode, HAND_ERROR, [], {"said": str(exc)}, run, notes)
    except H.ShapeError as exc:
        return finish(folder, lock, state, at, mode, SHAPE, [], {"note": str(exc)}, run, notes)
    state.pop("session", None)
    if outcome in (DONE, FIRST):
        state["last_look"] = st.stamp(at)
    return finish(folder, lock, state, at, mode, outcome, events, info, run, notes)


def finish(folder: pathlib.Path, lock: st.Lock, state: dict[str, Any], at: datetime, mode: str, outcome: str,
           events: list[dict[str, Any]], info: dict[str, Any], run: Run | None, notes: list[str]) -> int:
    """판을 맺는다 — 바뀜을 덧붙이고, 지금 모습을 바꿔 끼우고, 판 기록을 덧붙인다. 잠금을 잃었으면(풀린 판이 깨어났다) 아무것도 안 쓴다."""
    record = {"started": st.stamp(at), "ended": st.stamp(st.now()), "mode": mode, "outcome": outcome,
              "calls": run.calls if run else 0, "lines": run.lines if run else 0, "seconds": run.seconds() if run else 0,
              "new": sum(e["kind"] == D.NEW for e in events), "changes": sum(e["kind"] != D.NEW for e in events),
              **{k: v for k, v in info.items() if v not in (None, "", [], 0)}}
    if notes:
        record["note"] = " · ".join([*notes, *([record["note"]] if record.get("note") else [])])
    if mode == FULL and outcome in (DONE, FIRST):
        record["inbox"] = inbox_count(state)
    if not lock.owns():
        print("[스캔 — 이 판이 잠금을 잃었다(오래 멈춘 사이 다른 판이 돌았다). 아무것도 안 적었다]")
        return EXIT_STOPPED
    evidence = B.LIVE if outcome in (DONE, FIRST, PARTIAL) else B.LOST if outcome == SESSION else None
    brief = B.after_run(state, folder, evidence, run.hand_path if run else None, at)
    if brief and B.last_try(state):
        record["brief"] = B.last_try(state)
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
    print(summary(record))
    if brief:
        print(brief)
    return EXIT_OK if record["outcome"] in (DONE, FIRST) else EXIT_STOPPED


def inbox_count(state: dict[str, Any]) -> list[int]:
    """받은편지함의 [통 수, 안 읽음] — 자리를 확인 중인 메일은 뺀다. 메일함 전체를 다 본 판만 싣는다(`reader.py signals` 가 읽는다)."""
    inbox = [m for m in (state.get("mails") or {}).values() if m.get("box") == D.INBOX and not m.get("missing_since")]
    return [len(inbox), sum(bool(m.get("unread")) for m in inbox)]


OUTCOME_WORDS = {DONE: "됐다", FIRST: "첫 판 — 메일함의 바닥을 적었다(바뀜은 다음 판부터)", PARTIAL: "다 못 봤다 — 다 본 상자까지 적고 다음 판이 잇는다",
                 SESSION: "사내 세션이 없어 멈췄다 — 다음: 대화에서 스킬 ep-login 으로 EP 로그인을 한다", BUSY: "앞 판이 돌아 건너뛰었다",
                 HAND_MISSING: "회사 메일 손을 못 찾아 멈췄다 — 다음: --hand 로 company-mail 의 scripts/mail.py 를 준다",
                 HAND_OLD: "회사 메일 손이 옛 판이라 멈췄다 — 다음: PAISetup 을 다시 깔아 손을 새 판(list --since 가 있는 판)으로 올린다",
                 HAND_ERROR: "회사 메일 손이 오류를 내 멈췄다 — 다음: reader.py status 가 손의 말을 보인다",
                 SHAPE: "회사 메일 손의 글 꼴이 이 스킬이 아는 꼴과 달라 멈췄다 — 다음: 손이 바뀐 것이다. 이 스킬의 scan_hand.py 를 손의 새 꼴에 맞춘다",
                 SWAP: "지금 모습을 바꿔 끼우지 못했다 — 옛 판이 그대로다. 다음 판이 다시 쓴다"}
MODE_WORDS = {FULL: "메일함 전체", NEW: "새 메일만", "-": "—"}


def summary(record: dict[str, Any]) -> str:
    """판 끝의 한 줄 — 수와 때만(메일의 글은 안 싣는다)."""
    parts = [MODE_WORDS.get(record["mode"], record["mode"]), OUTCOME_WORDS.get(record["outcome"], record["outcome"]),
             f"새 메일 {record['new']}통 · 바뀜 {record['changes']}건", f"손 {record['calls']}번 · {record['seconds']}초"]
    if record.get("short"):
        parts.append(f"덜 본 자리 {len(record['short'])}곳")
    return "[스캔 — " + " · ".join(parts) + "]"


# ── 작업 스케줄러 ───────────────────────────────────────────────────────────────

def _decode(raw: bytes) -> str:
    """작업 스케줄러 · PowerShell 의 출력 — UTF-16(BOM · 0 바이트)이나 UTF-8, 아니면 콘솔의 OEM 코드 페이지(한글 윈도는 949)다.
    `-X utf8` 로 돌면 로캘이 UTF-8 로 보여 그 코드 페이지를 따로 묻는다."""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in raw[:200]:
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    if sys.platform == "win32":
        import ctypes
        return raw.decode(f"cp{ctypes.windll.kernel32.GetOEMCP()}", errors="replace")
    return raw.decode(locale.getencoding(), errors="replace")


def _show(cmd: list[str]) -> str:
    return " ".join(f'"{c}"' if " " in c else c for c in cmd)


NO_CLAUDE = ("Claude Code 명령줄(claude)을 못 찾았다{where}. 정한 시각의 보고는 claude -p 로 띄운다 — VS Code 확장만 깐 PC 면 확장 폴더의 "
             "resources/native-binary/claude.exe 를 --claude 로 준다")


def brief_wanted(args, hand: pathlib.Path | None) -> tuple[list[str] | None, pathlib.Path | None, bool, str]:
    """`--brief-at` · `--claude` · 스스로 로그인 선택을 받아 (보고 시각표, claude, 스스로 로그인, 거절의 말). 보고를 안 청했으면
    (None, None, False, ""). 시각을 안 주면 기본 시각 하나다. claude 는 안 주면 걸려 있던 것(그 파일이 있으면), 없으면 PATH 에서 찾는다.
    스스로 로그인은 안 주면 걸려 있던 값이고, 새로 켜는데 입구나 node 가 없으면 거절한다."""
    if args.brief_at is None:
        if args.brief_login is not None:
            return None, None, False, "스스로 로그인은 보고 예약을 거는 선택이다 — 보고 시각과 함께 준다"
        return None, None, False, ""
    times, bad = B.times_given(args.brief_at or [C.BRIEF_AT_DEFAULT])
    if bad:
        return None, None, False, f"{bad}. {B.in_force(B.load(st.scan_dir())[0])}"
    held, _ = B.load(st.scan_dir())
    if B.no_room(times, set(times) - set(held["times"] if held else [])):
        return None, None, False, f"{B.no_room(times, set(times) - set(held['times'] if held else []))}. {B.in_force(held)}"
    kept = pathlib.Path(held["claude"]) if held and not args.claude and pathlib.Path(held["claude"]).is_file() else None
    claude = kept or B.find_claude(args.claude)
    if claude is None:
        return None, None, False, NO_CLAUDE.format(where=f"({args.claude})" if args.claude else "(PATH)")
    login = bool(held and held.get("login")) if args.brief_login is None else args.brief_login
    if args.brief_login and B.login_command(hand) is None:
        return None, None, False, "스스로 로그인을 켤 수 없다 — 로그인 입구(스킬 ep-login)나 node 를 못 찾았다. 다음: 그 선택 없이 건다"
    return times, claude, login, ""


def show_brief_plan(times: list[str], claude: pathlib.Path, hand: pathlib.Path | None, login: bool) -> None:
    """걸면 띄울 것 — 명령 · 스스로 로그인의 명령 · 열린 명령 · 막은 명령(`--dry-run`)."""
    cmd, settings, _ = B.plan({"times": times, "claude": str(claude)}, hand, st.scan_dir())
    print(f"[보고 예약 — {B.window_words(times)} 띄운다({B.login_words(login)}): {_show(cmd)} < {st.scan_dir() / C.BRIEF_PROMPT_FILE}]")
    if login:
        print("  스스로 로그인: " + (_show(B.login_command(hand)) if B.login_command(hand) else "⚠ 로그인 입구나 node 를 못 찾았다 — 이대로는 안 선다"))
    print("  열린 명령: " + " | ".join(settings["permissions"]["allow"]))
    print("  막은 명령: " + " | ".join(settings["permissions"]["deny"]))


def cmd_register(args) -> int:
    try:
        hand = H.find_hand(args.hand)
    except H.HandMissing as exc:
        print(f"[예약 — 걸지 않았다: {exc}. 다음: --hand 로 company-mail 의 scripts/mail.py 를 준다]")
        return EXIT_STOPPED
    if not H.has_since(hand):
        print(f"[예약 — 걸지 않았다: 회사 메일 손이 「list --since」 없는 옛 판이다({hand}). 다음: PAISetup 을 다시 깔아 손을 새 판으로 올린다]")
        return EXIT_STOPPED
    brief_at, claude, login, refused = brief_wanted(args, hand)
    if refused:
        print(f"[예약 — 걸지 않았다: {refused}]")
        return EXIT_STOPPED
    xml = T.task_xml(every=args.every, full_every=args.full_every, hand=hand, scan_py=pathlib.Path(__file__).resolve())
    path = st.scan_dir() / C.TASK_XML_FILE
    if T.windowless_python().name.lower() != "pythonw.exe":
        print("[예약 — ⚠ 창 없는 파이썬(pythonw.exe)을 못 찾아 판마다 창이 뜬다]")
    if args.dry_run:
        print(f"[예약 — 걸지 않고 보이기만 한다. 걸면 새 메일을 {args.every}분마다 · 메일함 전체를 {args.full_every}분마다 읽는다(앞 판이 돌면 "
              f"그 주기는 건너뛴다): {_show(T.register_command(path))}]")
        if brief_at:
            show_brief_plan(brief_at, claude, hand, login)
        elif args.brief_off:
            print("[보고 예약 — 걸면 보고 예약을 내린다]")
        print(xml)
        return EXIT_OK
    T.write_xml(path, xml)
    if args.validate:
        done = subprocess.run(T.validate_command(), capture_output=True, env={**os.environ, "MAILBOX_SCAN_TASK_XML": str(path)})
        out = _decode(done.stdout).strip()
        ok = done.returncode == 0 and out.endswith("ok")
        print(f"[예약 — 작업 스케줄러가 정의를 {'받는다' if ok else '거절했다'}(등록 안 함): {path}]")
        if not ok:
            print(_decode(done.stderr).strip()[-600:])
        return EXIT_OK if ok else EXIT_STOPPED
    done = subprocess.run(T.register_command(path), capture_output=True)
    if done.returncode != 0:
        print(f"[예약 — 작업 스케줄러가 거절했다: {(_decode(done.stdout) + _decode(done.stderr)).strip()[-400:]}]")
        return EXIT_STOPPED
    print(f"[예약 — {T.TASK_NAME} 을 걸었다: {args.every}분마다 · 메일함 전체는 {args.full_every}분마다 · 앞 판이 돌면 그 주기는 건너뛴다]")
    if brief_at:
        B.save(st.scan_dir(make=True), brief_at, claude, login)
        print(f"[보고 예약 — {B.window_words(brief_at)} 일일 보고를 띄운다 · {B.login_words(login)} · claude {claude}]{told()}")
    elif args.brief_off and B.clear(st.scan_dir()):
        print(f"[보고 예약 — 내렸다]{told()}")
    return EXIT_OK


def cmd_brief(args) -> int:
    """보고 예약만 걸고 · 바꾸고 · 내린다 — 작업 스케줄러는 안 건드린다(스캔 판이 이 설정을 읽는다)."""
    if args.off:
        if args.dry_run:
            print("[보고 예약 — 내리지 않고 보이기만 한다]")
            return EXIT_OK
        print(f"[보고 예약 — 내렸다]{told()}" if B.clear(st.scan_dir()) else "[보고 예약 — 걸려 있지 않았다]")
        return EXIT_OK
    try:
        hand = H.find_hand(None)
    except H.HandMissing:
        hand = None
    brief_at, claude, login, refused = brief_wanted(args, hand)
    if refused:
        print(f"[보고 예약 — 걸지 않았다: {refused}]")
        return EXIT_STOPPED
    if args.dry_run:
        show_brief_plan(brief_at, claude, hand, login)
        return EXIT_OK
    B.save(st.scan_dir(make=True), brief_at, claude, login)
    task = subprocess.run(T.query_command(), capture_output=True).returncode == 0
    print(f"[보고 예약 — {B.window_words(brief_at)} 일일 보고를 띄운다 · {B.login_words(login)} · claude {claude}]{told()}")
    if not task:
        print(f"  ⚠ 메일함 스캔이 작업 스케줄러에 안 걸려 있어 이 보고는 안 뜬다 — 스캔 판이 보고를 띄운다. 다음: register --brief-at "
              f"{' '.join(brief_at)} 로 스캔과 함께 건다")
    return EXIT_OK


def told() -> str:
    """대화에서 바꾼 것을 열린 보고 창에 알렸으면 그 한 구절."""
    said = B.tell_window(st.scan_dir())
    return f" · {said}" if said else ""


def cmd_status(args) -> int:
    task = None                     # 작업 스케줄러에 걸렸나 — 안 물었으면 None
    if args.dry_run:
        print(f"[예약 — 묻지 않고 보이기만 한다. 물으면: {_show(T.query_command())}]")
    else:
        done = subprocess.run(T.query_command(), capture_output=True)
        task = done.returncode == 0
        if done.returncode != 0:
            print(f"[예약 — 걸린 작업이 없다(또는 못 읽었다): {(_decode(done.stdout) + _decode(done.stderr)).strip()[-300:]}]")
        else:
            d = T.read_definition(_decode(done.stdout).strip())
            print(f"[예약 — {T.TASK_NAME} · 간격 {d['interval']} · 켜짐 {d['enabled']} · 한 번에 하나 {d['instances']}]")
            print(f"  부르는 것: {d['command']} {d['arguments']}")
    state, _ = st.load_state(st.scan_dir())
    last = (state or {}).get("last_run")
    if last:
        print(f"  마지막 판: {st.seoul(st.parse(last.get('started')))} · {MODE_WORDS.get(last.get('mode'), '')} · "
              f"{OUTCOME_WORDS.get(last.get('outcome'), last.get('outcome'))}")
    else:
        print("  스캔한 적이 없다 — 스캔 파일이 없다")
    for line in B.describe(state, st.scan_dir(), st.now(), task):
        print(line)
    return EXIT_OK


def cmd_unregister(args) -> int:
    if args.dry_run:
        print(f"[예약 — 끄지 않고 보이기만 한다. 끄면: {_show(T.delete_command())} · 보고 예약도 내린다]")
        return EXIT_OK
    brief = " · 보고 예약도 내렸다" if B.clear(st.scan_dir()) else ""     # 끄기를 청하셨으니 작업이 없어도 보고는 내린다
    done = subprocess.run(T.delete_command(), capture_output=True)
    if done.returncode != 0:
        print(f"[예약 — 못 껐다(걸린 작업이 없을 수 있다){brief}: {(_decode(done.stdout) + _decode(done.stderr)).strip()[-300:]}]")
        return EXIT_STOPPED
    print(f"[예약 — {T.TASK_NAME} 을 껐다{brief}. 쌓인 스캔 파일은 그대로다]")
    return EXIT_OK


BRIEF_AT_HELP = (f"보고 시각표 — 시각 하나 이상(서울 · 빈칸이나 쉼표로 · 안 주면 {C.BRIEF_AT_DEFAULT}). 시각마다 그 시각부터 다음 시각까지(길어야 "
                 f"{C.BRIEF_WAIT_MIN}분 · 그날 자정까지) 사내 세션이 서는 첫 판에 일일 보고를 한 번 띄운다. 시각마다 {C.BRIEF_ROOM_MIN}분 넘게 띄어야 걸린다")
FULL_EVERY_HELP = f"메일함 전체를 다시 보는 주기(분 · 기본 {C.FULL_EVERY_MIN} · 다 못 본 판을 잇는 기한 {C.PENDING_MAX_MIN}분보다 짧게)"


def login_flags(p: argparse.ArgumentParser, on: str, off: str) -> None:
    """스스로 로그인을 켜고 끄는 선택 한 쌍 — 둘 다 안 주면 걸려 있던 값을 그대로 둔다(`brief_login` 이 None)."""
    pair = p.add_mutually_exclusive_group()
    pair.add_argument(on, dest="brief_login", action="store_const", const=True, default=None,
                      help="그날 첫 보고 시각의 보고 앞에 한 번 스스로 로그인한다(사내 세션이 살아 있어도 · 뒤 시각은 안 한다) — 입력 없이 넘는 통합 인증으로만(VDI 는 안 선다). "
                           "평소 Edge 에 로그인 탭이 하나 열리고 ep-login 창이 떠 있게 되며, 평소 Edge · 다른 자리에서 열어 둔 메일과 EP "
                           "포털은 다시 로그인해야 할 수 있다")
    pair.add_argument(off, dest="brief_login", action="store_const", const=False, help="스스로 로그인을 끈다 — 사내 세션이 설 때까지 기다린다")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="메일함 스캔 — 회사 메일 손으로 메일함의 지금을 사용자 폴더에 쌓는다(메일함은 안 바꾼다)")
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="한 판 — 때가 됐으면 메일함 전체, 아니면 새 메일만")
    way = r.add_mutually_exclusive_group()
    way.add_argument("--full", action="store_true", help="메일함 전체를 다시 본다")
    way.add_argument("--new", action="store_true", help="새 메일만 본다(지금 모습이 없으면 전체)")
    r.add_argument("--now", action="store_true", help="세션이 끊긴 뒤의 기다림을 건너뛰고 지금 돈다 — 대화에서 EP 로그인을 한 뒤")
    r.add_argument("--hand", help="회사 메일 손 mail.py 의 자리 — 없으면 MAILBOX_SCAN_HAND · SECRETARY_SKILLS · 도구 홈")
    r.add_argument("--full-every", type=int, default=C.FULL_EVERY_MIN, help=FULL_EVERY_HELP)
    g = sub.add_parser("register", help="작업 스케줄러에 건다")
    g.add_argument("--every", type=int, default=C.EVERY_MIN, help=f"새 메일을 보는 주기(분 · 기본 {C.EVERY_MIN})")
    g.add_argument("--full-every", type=int, default=C.FULL_EVERY_MIN, help=FULL_EVERY_HELP)
    g.add_argument("--hand", help="회사 메일 손 mail.py 의 자리 — 작업의 명령줄에 굳힌다")
    how = g.add_mutually_exclusive_group()
    how.add_argument("--dry-run", action="store_true", help="걸지 않고 정의와 명령만 보인다")
    how.add_argument("--validate", action="store_true", help="작업 스케줄러가 정의를 받나만 묻는다(등록 안 함)")
    wake = g.add_mutually_exclusive_group()
    wake.add_argument("--brief-at", nargs="*", metavar="HH:MM", help=BRIEF_AT_HELP)
    wake.add_argument("--brief-off", action="store_true", help="보고 예약을 내린다")
    login_flags(g, "--brief-login", "--brief-no-login")
    g.add_argument("--claude", help="띄울 claude 의 자리 — 없으면 PATH 에서 찾는다")
    b = sub.add_parser("brief", help="보고 예약만 걸고 · 바꾸고 · 내린다(작업 스케줄러는 안 건드린다)")
    which = b.add_mutually_exclusive_group(required=True)
    which.add_argument("--at", dest="brief_at", nargs="*", metavar="HH:MM", help=BRIEF_AT_HELP)
    which.add_argument("--off", action="store_true", help="내린다")
    login_flags(b, "--login", "--no-login")
    b.add_argument("--claude", help="띄울 claude 의 자리 — 없으면 PATH 에서 찾는다")
    b.add_argument("--dry-run", action="store_true", help="걸지 않고 띄울 명령 · 열린 명령 · 막은 명령만 보인다")
    s = sub.add_parser("status", help="걸린 작업 · 마지막 판 · 보고 예약")
    s.add_argument("--dry-run", action="store_true", help="작업 스케줄러에 묻지 않는다(사용자 폴더의 것만 보인다)")
    u = sub.add_parser("unregister", help="작업을 지우고 보고 예약을 내린다(쌓인 스캔 파일은 그대로)")
    u.add_argument("--dry-run", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure") and sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    for name in ("every", "full_every"):
        if getattr(args, name, 1) is not None and getattr(args, name, 1) < 1:
            parser().error(f"--{name.replace('_', '-')} 는 1 분 이상이다")
    if getattr(args, "full_every", 0) >= C.PENDING_MAX_MIN:
        parser().error(f"--full-every 는 {C.PENDING_MAX_MIN}분보다 짧아야 한다 — 다 못 본 판을 잇는 기한이라, 같거나 길면 큰 메일함은 "
                       "덜 본 상자가 늘 버려져 끝내 다 못 본다")
    return {"run": cmd_run, "register": cmd_register, "brief": cmd_brief, "status": cmd_status,
            "unregister": cmd_unregister}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
