"""보고 창의 맡길 일 — 창에서 누른 일들을 뒤의 실행(같은 스킬 `unattended/handed.py`)에 넘기고, 그 실행의 기록을 따라 일마다의 끝을
창에 돌려 적는다. 창 곁의 손(곁의 `presses.py` 의 `watch`)이 걸음마다 `step` 을 부른다. 이 파일은 다른 프로그램을 띄우지 않는다 — 실행의 명령은
부르는 쪽이 준 `scan` 하나로 부른다(`presses.run_unattended`).

손은 일의 글을 읽어 무엇을 가르지 않는다 — 누른 창의 보고 글에서 그 일을 찾아(`brief_tasks.tasks_of`) 사람이 카드에서 읽은 줄(`Task.line`)과 카드의
줄을 적힌 그대로 넘기고, 실행이 일마다 쓴 결과 글을 그대로 창에 적는다. 계약 — 창의 저장소 칸은 `references/DESIGN.md` 「맡길 일」의 표, 실행의
명령 · 입력 · 기록은 「사람 없는 실행의 문」의 표가 원본이다.

한 일은 한 번 — 사용자 폴더의 기록(`RUNS_FILE`)이 누름마다 넘긴 판과 일마다의 끝을 든다. 같은 보고의 같은 일이 도는 판에 들었거나 됨 · 여쭐 것 ·
확인 안 됨으로 맺었으면 다시 넘기지 않고 그 판을 따른다(창이 손과 연락이 끊긴 동안에도 실행은 따로 돈다 — 다시 넘기면 같은 방이 두 번
잡힌다). 다시 넘기는 것은 「못 함」(아무것도 안 바꿨다)으로 맺은 일뿐이다. 창에 적는 것은 기록에서 지은 그 창의 모습과 지금 저장소의 다른
칸뿐이다 — 손이 죽었다 다시 떠도, 창을 닫았다 열어도 같은 모습이 다시 선다.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
import brief_const as C  # noqa: E402
import edge as E  # noqa: E402
import clock as T  # noqa: E402
import unattended_link as L  # noqa: E402
import store as S  # noqa: E402
from brief_files import is_window  # noqa: E402
from brief_tasks import Task, tasks_of  # noqa: E402
from task_kinds import VIA_RUN, read_only  # noqa: E402
# RUNS_FILE 은 여기서 안 쓰지만 이 모듈의 이름으로도 선다 — 검사가 `runs.RUNS_FILE` 으로 기록 파일을 짚는다
from records import (ENDED, RUNNING, RUNS_FILE, RUNS_KEEP_DAYS, STARTING, Unreadable, live, read_runs, task_outcome,  # noqa: E402,F401
                     write_runs)

TASKS_NAME = ".daily-brief-handed-{ms}.json"   # 실행에 줄 맡긴 일 파일 — 사용자 폴더에 잠깐 두고 맡긴 뒤 지운다(실행이 제 자리에 베낀다)
FOLLOW_S = 2.0                                 # 도는 판의 기록을 다시 읽는 사이
MISSING_S = 300                                # 도는 판의 기록이 이만큼 내리 안 읽히면 맺는다 — 들었는지 모르니 확인 안 됨으로
RUN_KEYS = [C.RUN_PREFIX, C.TASK_PREFIX]          # 이 손이 창에서 읽는 칸 — 누름과 일마다의 결과
SESSION = re.compile(r"^[0-9a-fA-F-]{8,64}$")  # claude 의 세션 번호 꼴 — 창의 부탁이 들고 온 세션을 이 손이 넘긴 판의 것과 견주기 전에 본다

# 실행의 끝 → 창의 끝(계약 — 창이 읽는 `end`). 다 했다 · 로그인이 끊겼다 · 죽었다 · 천장에서 끊었다
ENDS = {"finished": "done", "login": "session", "died": "stopped", "cut": "stopped"}
# 실행의 일 상태 → 창의 일 상태. 기다림은 창이 스스로 끌어내 적지 않는다
STATES = {"doing": "doing", "done": "done", "asked": "asked", "failed": "failed", "unknown": "unsure"}
SETTLED = ("done", "asked", "unsure")          # 맺은 끝 가운데 다시 넘기지 않는 것 — 된 일 · 사람이 이어 답할 일 · 됐는지 모르는 일
SAID = {
    "gone": "누르신 일을 그 보고 글에서 찾지 못해 맡지 않았습니다 — 대화에서 말씀해 주세요",
    "bad": C.TASK_BAD,
    "unwritten": "맡긴 기록을 남기지 못해 맡지 않았습니다 — 아무것도 안 바뀌었습니다. 다시 맡겨 주세요",
    "unread": "맡긴 기록을 읽지 못해 맡지 않았습니다 — 아무것도 안 바뀌었습니다. 다시 맡겨 주시고, 그래도 안 되면 대화에서 말씀해 주세요",
    "nohand": "맡길 비서 프로그램이 곁에 없어 맡지 않았습니다 — 아무것도 안 바뀌었습니다",
    "lost": "맡기다 창 곁의 비서 프로그램이 멈춰 맡겨졌는지 확인하지 못했습니다 — 다시 맡기시기 전에 됐는지부터 확인해 주세요",
    "missing": "맡긴 일의 기록이 사라져 끝을 확인하지 못했습니다 — 됐는지부터 확인해 주세요",
    "readonly": "끝내지 못했습니다 — 메일을 읽기만 하는 일이라 바뀐 것은 없습니다. 다시 맡기셔도 됩니다",
}
# 뒤의 실행이 못 맡는다고 답한 까닭(계약의 `cannot`) → 사람에게 할 말. 실행의 `message` 는 프로그램의 말(폴더 경로 따위)이라 모르는 까닭일 때만 그대로 쓴다
CANNOT = {
    "nowork": "작업 폴더가 없어 맡지 않았습니다 — 아무것도 안 바뀌었습니다. 설치(PAI Setup)를 한 번 돌리시면 생깁니다",
    "noclaude": "이 PC 에서 Claude Code 를 찾지 못해 맡지 않았습니다 — 아무것도 안 바뀌었습니다. 대화에서 말씀해 주세요",
    "nohand": "회사 메일을 다루는 비서 프로그램이 없어 맡지 않았습니다 — 아무것도 안 바뀌었습니다. 설치(PAI Setup)를 한 번 돌리시면 생깁니다",
}
# 창 곁의 손의 기록(`presses.HAND_LOG`)에 남길 구절
LOG_UNREAD = "맡긴 일 — {key} 를 맡지 않았다(기록을 못 읽었다)"
LOG_UNWRITTEN = "맡긴 일 — {key} 를 맡지 않았다(기록을 못 썼다)"
LOG_TAKEN = "맡긴 일 — {key} 맡음 · 넘길 것 {go} · 따름 {held}"
LOG_LAUNCHED = "맡긴 일 — {key} 넘김 · {how}"
LOG_ORPHANS = "맡긴 일 — 맡았다고만 적고 기록에 없는 누름 {n}개를 못 맡김으로 맺었다"
REFUSED = C.RUN_REFUSED                        # 누름의 끝 — 아무것도 넘기지 못했다(까닭은 일마다)


# ── 창의 칸 ──────────────────────────────────────────────────────────────────

def press_page(key: str) -> str:
    """누름의 열쇠(`<창 이름>~<ms>`)에서 창 이름."""
    return key.rsplit("~", 1)[0]


def takeable(key: str, value: dict) -> bool:
    """맡을 누름인가 — 맡지도 맺지도 않았고, 누른 지 `brief_const.RUN_TAKE_S` 안이고, 누른 창이 그 열쇠의 창이고, 할 일이 있다. 늦은 누름은 창이
    「못 맡김」으로 맺는다 — 손이 뒤늦게 맡으면 그 뒤에 일이 된다."""
    if value.get("taken") or value.get("ended") or not isinstance(value.get("ids"), list) or not value["ids"]:
        return False
    at = E.pressed_at(value)
    page = press_page(key)
    return (at is not None and -C.RUN_TAKE_S < (T.local_now() - at).total_seconds() < C.RUN_TAKE_S and value.get("brief") == page
            and is_window(page) and all(isinstance(i, str) for i in value["ids"]))


# ── 넘기기 ───────────────────────────────────────────────────────────────────

def last_of(presses: dict, page: str, tid: str, but: str = "") -> tuple[str, dict] | None:
    """그 보고의 그 일을 든 가장 늦은 누름(`but` 은 빼고) — (열쇠, 누름)."""
    found = [(k, v) for k, v in presses.items() if k != but and v.get("page") == page and tid in (v.get("ids") or []) + list(v.get("held") or {})]
    return max(found, key=lambda kv: str(kv[1].get("at", ""))) if found else None


def live_or_settled(presses: dict, page: str, tid: str, but: str) -> str | None:
    """그 일이 이미 넘겨져 돌거나 다시 넘기면 안 될 끝으로 맺었으면 그 누름의 열쇠 — 다시 넘겨도 되면 None."""
    last = last_of(presses, page, tid, but)
    if last is None:
        return None
    key, v = last
    owner = (v.get("held") or {}).get(tid) or key   # 그 일을 실제로 넘긴 누름
    got = task_outcome(presses, key, tid) or {}
    if live(presses.get(owner) or {}):
        return owner if got.get("state") != "failed" else None   # 넘기는 중 · 도는 중 — 그 판의 끝을 따른다
    return owner if got.get("state") in SETTLED else None


def names_of(t: Task) -> str:
    """기록 · 다음 보고에 댈 그 일의 이름 — 「카드 n 「제목」 종류」."""
    return (f"카드 {t.num} " if t.num else "") + f"「{t.card}」 {t.kind}"


def hand_over(folder: pathlib.Path, key: str, value: dict, presses: dict) -> dict:
    """누름 하나를 가른다(창에 맡았다고 적은 뒤다) — {entry: 기록에 남길 누름, go: 실행에 넘길 일}. 이미 넘겨진 일은 그 판을 따르고(`held`), 못
    할 일은 그 까닭으로 맺는다. 누름의 `state` · `end` 는 이 누름이 넘긴 판의 몫이다 — 따르는 판까지 합친 끝은 `overall` 이 짓는다."""
    page = press_page(key)
    entry = {"page": page, "at": str(value.get("at")), "taken": T.stamp(T.local_now()), "ids": [], "held": {}, "tasks": {}, "names": {}, "kinds": {},
             "launch": None, "state": ENDED, "end": "done", "said": ""}
    got = S.page_brief(folder, page)               # 누른 창의 보고 글 — 못 읽으면 일마다 「찾지 못했다」로 맺는다
    tasks = tasks_of(got[1]) if got else None
    go: list[Task] = []
    for tid in dict.fromkeys(value["ids"]):
        t = (tasks or {}).get(tid)
        if t is None or t.row.via != VIA_RUN:
            entry["tasks"][tid] = {"state": "failed", "at": T.stamp(T.local_now()), "said": SAID["gone" if t is None else "bad"]}
            continue
        entry["names"][tid], entry["kinds"][tid] = names_of(t), t.kind
        follow = live_or_settled(presses, page, tid, key)
        if follow:
            entry["held"][tid] = follow
        else:
            go.append(t)
    if go:
        entry.update(ids=[t.id for t in go], state=STARTING, end=None)
    elif not entry["held"]:                        # 넘길 것도 따를 것도 없다 — 일마다 까닭이 섰다
        entry.update(end=REFUSED, ended=T.stamp(T.local_now()))
    return {"entry": entry, "go": go}


def launch(folder: pathlib.Path, key: str, entry: dict, go: list[Task], scan) -> None:
    """넘길 일을 실행에 넘긴다 — 기록에 「넘기는 중」을 남긴 뒤에 부른다(그 사이 손이 죽어도 다음 손이 그 누름을 다시 넘기지 않는다). 맡긴 일
    파일을 쓰고 → `handed start` 한 번 → 그 파일을 걷고 → 답을 가른다(`take_start`)."""
    path = folder / TASKS_NAME.format(ms=key.rsplit("~", 1)[-1])
    try:
        path.write_text(json.dumps(tasks_body(key, go), ensure_ascii=False), encoding="utf-8")
    except OSError:
        settle_all(entry, "failed", SAID["unwritten"], REFUSED)
        return
    try:
        end, rec = L.start(scan, path)
    finally:
        path.unlink(missing_ok=True)
    take_start(entry, key, end, rec, scan)


def tasks_body(key: str, go: list[Task]) -> dict:
    """실행에 줄 맡긴 일 파일의 몸 — `brief` 에 누름의 열쇠를 실어, 끝을 못 받은 판을 도는 판의 목록에서 찾는다. 일마다 사람이 카드에서 읽은
    줄 · 카드의 줄 그대로 · 결과 이름표."""
    return {"brief": key, "tasks": [{"id": t.id, "kind": t.kind, "line": t.line, "card": {"title": t.card, "lines": t.run_lines()},
                                     "labels": list(t.row.labels)} for t in go]}


def take_start(entry: dict, key: str, end: str, rec: dict, scan) -> None:
    """`handed start` 의 끝(`unattended_link.start`)을 누름에 얹는다 — 맡았다(그 판을 따른다) · 실행을 못 띄웠다 · 실행이 못 맡는다고 했다(기록을 안
    썼다) · 모른다(넘겨졌는지 도는 판의 목록에서 찾고, 없으면 확인 안 됨)."""
    if end == L.TOOK:
        entry.update(launch=rec["id"], state=RUNNING)
        absorb(entry, rec)
    elif end == L.NOT_LAUNCHED:
        settle_all(entry, "failed", SAID["nohand"], REFUSED)
    elif end == L.REFUSED:
        settle_all(entry, "failed", CANNOT.get(str(rec.get("cannot"))) or str(rec.get("message") or SAID["nohand"]), REFUSED)
    else:
        found_or_lost(entry, L.find_launch(key, scan))


def found_or_lost(entry: dict, found: dict | None) -> None:
    """도는 판의 목록에서 찾은 그 누름의 판을 따르게 하고, 못 찾았으면 확인 안 됨으로 맺는다 — 넘겨졌을 수 있다."""
    if found:
        entry.update(launch=found["id"], state=RUNNING)
        absorb(entry, found)
    else:
        settle_all(entry, "unsure", SAID["lost"], "stopped")


def settle_all(entry: dict, state: str, said: str, end: str) -> None:
    """넘기려던 일을 다 그 끝으로 맺는다 — 못 넘긴 판(`REFUSED`)이거나 넘겼는지 모르는 판."""
    for tid in entry["ids"]:
        entry["tasks"][tid] = unsure_row(entry, tid, said) if state == "unsure" else {"state": state, "at": T.stamp(T.local_now()), "said": said}
    entry.update(state=ENDED, end=end, ended=T.stamp(T.local_now()))


def unsure_row(entry: dict, tid: str, said: str) -> dict:
    """됐는지 모르는 일의 칸 — 종류는 누름이 넘길 때 적어 둔 것(`entry["kinds"]`)으로 읽고, 「못 함」으로 바꿀지는 `readonly_end` 가 가른다."""
    at = T.stamp(T.local_now())
    return readonly_end("unsure", (entry.get("kinds") or {}).get(tid), at) or {"state": "unsure", "at": at, "said": said}


def readonly_end(state: str, kind: object, at: str) -> dict | None:
    """아무것도 안 바꾸는 종류(`task_kinds.Kind.read_only`)가 「확인 안 됨」으로 끝났으면 그 일의 「못 함」 칸 — 모를 것이 없어 다시 맡겨도 된다.
    아니면 None. 넘기지 못한 판(`unsure_row`)과 실행의 기록(`absorb`)이 이 한 자로 가른다."""
    return {"state": "failed", "at": at, "said": SAID["readonly"]} if state == "unsure" and read_only(kind) else None


RESULT_FIELDS = (("said", str), ("facts", list), ("items", list), ("more", str))   # 실행의 기록 `tasks[].result` 의 칸 — 창의 `brief-task:` 칸과 같은 이름


def absorb(entry: dict, rec: dict) -> None:
    """실행의 기록 하나를 누름에 얹는다 — 일마다의 상태 · 때 · 결과(꼴대로 왔으면 그 칸들, 아니면 온 글 그대로) · 이어 갈 세션, 판이 끝났으면
    그 끝. 아무것도 안 바꾸는 종류가 「확인 안 됨」으로 맺었으면 「못 함」이다(`readonly_end` — 종류는 기록이 되돌려 준 이름으로 읽는다)."""
    session = rec.get("session") if isinstance(rec.get("session"), str) else None
    for t in rec.get("tasks") if isinstance(rec.get("tasks"), list) else []:
        if not isinstance(t, dict):
            continue
        state = STATES.get(str(t.get("state")))
        if t.get("id") not in entry["ids"] or state is None:
            continue
        failed = readonly_end(state, str(t.get("kind")), str(t.get("at") or T.stamp(T.local_now())))
        if failed:
            entry["tasks"][t["id"]] = failed
            continue
        got = t.get("result") if isinstance(t.get("result"), dict) else None
        row = {"state": state, "at": str(t.get("at") or T.stamp(T.local_now()))}
        if got:
            row.update({k: got[k] for k, kind in RESULT_FIELDS if isinstance(got.get(k), kind) and got[k]})
            row.setdefault("said", "")
        else:
            row["said"] = str(t.get("text") or "")
        if state in ("asked", "unsure") and session:
            row["session"] = session
        entry["tasks"][t["id"]] = row
    if session:
        entry["session"] = session
    if rec.get("alive") is False:
        entry.update(state=ENDED, end=ENDS.get(str(rec.get("end")), "stopped"), said=" ".join(str(rec.get("said") or "").split())[:C.SAID_MAX],
                     ended=str(rec.get("ended") or T.stamp(T.local_now())))


def follow(folder: pathlib.Path, presses: dict, scan, skip: set[str] = frozenset()) -> bool:
    """도는 판마다 실행의 기록을 다시 읽어 누름에 얹는다 — 바뀌었나. 넘기다 손이 죽은 누름(「넘기는 중」)은 도는 판의 목록에서 찾는다.
    이 손이 맡아 곧 넘길 누름(`skip`)은 넘기다 죽은 누름이 아니다."""
    changed = False
    for key, entry in presses.items():
        if key in skip:
            continue
        if entry.get("state") == STARTING:
            found_or_lost(entry, L.find_launch(key, scan))
            changed = True
        elif entry.get("state") == RUNNING and entry.get("launch"):
            changed |= follow_running(entry, scan)
    return changed


def follow_running(entry: dict, scan) -> bool:
    """도는 판 하나의 기록을 다시 읽어 얹는다 — 바뀌었나. 못 읽으면 그 때를 적고, `MISSING_S` 내리 못 읽으면 남은 일을 확인 안 됨으로 맺는다."""
    rec = L.show(scan, entry["launch"])
    if rec is not None:
        before = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        entry.pop("missing", None)
        absorb(entry, rec)
        return json.dumps(entry, sort_keys=True, ensure_ascii=False) != before
    if not entry.get("missing"):
        entry["missing"] = T.stamp(T.local_now())
        return True
    if (T.local_now() - dt.datetime.fromisoformat(entry["missing"])).total_seconds() >= MISSING_S:
        for tid in entry["ids"]:
            if (entry["tasks"].get(tid) or {}).get("state") in (None, "doing"):
                entry["tasks"][tid] = unsure_row(entry, tid, SAID["missing"])
        entry.update(state=ENDED, end="stopped", ended=T.stamp(T.local_now()))
        return True
    return False


# ── 창에 적기 — 기록에서 그 창의 모습을 짓고 다른 칸만 적는다 ─────────────────────────────

def latest(times: list[str]) -> str:
    """때들 가운데 가장 늦은 것 — 실행의 때(UTC)와 이 손의 때(서울)가 섞여 글자로는 못 견준다. 읽을 수 없는 때는 안 센다."""
    def at(x: str) -> dt.datetime | None:
        try:
            got = dt.datetime.fromisoformat(x.replace("Z", "+00:00"))
        except ValueError:
            return None
        return got if got.tzinfo else got.astimezone()
    known = [(at(x), x) for x in times if at(x) is not None]
    return max(known)[1] if known else ""


def overall(presses: dict, key: str, depth: int = 0) -> tuple[bool, str, str]:
    """누름 하나의 끝 — (맺었나, 끝, 맺은 때). 제가 넘긴 판과 따르는 판이 다 맺어야 맺는다. 끝은 더 나쁜 쪽(로그인 끊김 · 멈춤 · 못 맡김 ·
    다 함 차례)이다. 따르기만 한 누름의 때는 따르는 판들이 맺은 때다 — 그 누름을 맡은 때가 아니다. 따르는 누름이 기록에 없으면 멈춘 것으로 본다."""
    v = presses.get(key)
    if v is None or depth > len(presses):
        return True, "stopped", T.stamp(T.local_now())
    held = sorted(set((v.get("held") or {}).values()) - {key})
    parts = [] if held and not v.get("ids") else [(not live(v), str(v.get("end") or "done"), str(v.get("ended") or v.get("taken") or ""))]
    parts += [overall(presses, f, depth + 1) for f in held]
    if not all(p[0] for p in parts):
        return False, "", ""
    ends = [p[1] for p in parts]
    return True, next((e for e in ("session", "stopped", REFUSED) if e in ends), "done"), latest([p[2] for p in parts])


def want_rows(presses: dict, run_rows: dict, task_rows: dict) -> list[list[str]]:
    """창에 적을 칸 — 기록이 든 누름마다 그 누름의 칸(`press_cells`)과 일마다의 칸(`task_cells`). 저장소의 값과 같은 칸은 안 적는다."""
    return press_cells(presses, run_rows) + task_cells(presses, run_rows, task_rows)


def press_cells(presses: dict, run_rows: dict) -> list[list[str]]:
    """누름마다의 칸 — 맡은 때 · 맺었으면 그 끝(`overall`). 창의 저장소에 맺음이 적혀 있어도 판이 아직 돌면 그 맺음을 걷는다. 창의 저장소에
    없는 누름은 그 창이 지웠거나 다른 Edge 다 — 새로 세우지 않는다."""
    out = []
    for key, entry in presses.items():
        raw = run_rows.get(key)
        if raw is None:
            continue
        value = dict(raw[1])
        want = {**value, "taken": entry["taken"]}
        ended, end, ended_at = overall(presses, key)
        if ended:
            want.update(ended=ended_at or entry["taken"], end=end)
            if entry.get("said"):
                want["said"] = entry["said"]
        else:
            for k in ("ended", "end", "said"):
                want.pop(k, None)
        if want != value:
            out.append([C.RUN_PREFIX + key, json.dumps(want, ensure_ascii=False)])
    return out


def task_cells(presses: dict, run_rows: dict, task_rows: dict) -> list[list[str]]:
    """일마다의 칸 — 그 일을 든 가장 늦은 누름(창의 저장소에 있는 것)의 끝."""
    out = []
    seen: set[tuple[str, str]] = set()
    for key, entry in sorted(presses.items(), key=lambda kv: str(kv[1].get("at", "")), reverse=True):
        if key not in run_rows:
            continue
        for tid in list(entry.get("ids") or []) + list(entry.get("held") or {}) + list(entry.get("tasks") or {}):
            if (entry["page"], tid) in seen:
                continue
            seen.add((entry["page"], tid))
            got = task_outcome(presses, key, tid)
            if not got:
                continue
            row = {"run": key, **got}
            slot = f"{entry['page']}/{tid}"
            if task_rows.get(slot, (None, None))[1] != row:
                out.append([C.TASK_PREFIX + slot, json.dumps(row, ensure_ascii=False)])
    return out


# ── 한 걸음 ──────────────────────────────────────────────────────────────────

class Runs:
    """창 곁의 손이 든 맡긴 일 — 기록을 쥐고, 걸음마다 새 누름을 맡고 도는 판을 따르고 창에 적는다. `scan` 은 사람 없는 실행의 명령을 부르는 손(`presses.run_unattended`)."""

    def __init__(self, folder: pathlib.Path, scan):
        self.folder, self.scan, self.followed = folder, scan, 0.0
        self.presses: dict | None = None
        self.pending: dict[str, list] = {}          # 맡았고 아직 안 넘긴 누름 — {열쇠: 넘길 일}. 이 손이 사는 동안만(다시 뜬 손은 기록에서 찾는다)

    def load(self) -> dict | None:
        """기록 — 못 읽으면 None(그 위에 안 쓴다 · 새 누름을 안 넘긴다)."""
        if self.presses is None:
            try:
                self.presses = read_runs(self.folder)
            except Unreadable:
                return None
        return self.presses

    def save(self) -> bool:
        """맡긴 일의 기록을 파일에 쓴다 — 썼으면 True, 못 쓰면 False."""
        try:
            write_runs(self.folder, self.presses or {})
            return True
        except OSError:
            return False

    def busy(self) -> bool:
        """넘기는 중 · 도는 판이 있나 — 있으면 창 곁의 손이 열린 창이 없어도 남아 끝을 받는다."""
        presses = self.load() or {}
        return any(live(v) for v in presses.values())

    def sessions(self) -> set[str]:
        """이 손이 넘긴 판의 세션 — 창의 「대화로 이어 가기」가 들고 온 세션을 여기에 대 본다(창의 저장소는 file: 창끼리 하나라 믿지 않는다)."""
        return {str(v["session"]) for v in (self.load() or {}).values() if isinstance(v.get("session"), str) and SESSION.match(v["session"])}

    def adopt(self, run_rows: dict, presses: dict) -> bool:
        """손이 없을 때 창이 「못 맡김」으로 맺은 누름 가운데 그 일이 다 이 손이 넘긴 판에 들었거나 다시 넘기면 안 될 끝으로 맺은 것을 그 판을
        따르는 누름으로 받는다 — 창에서 그 일이 「못 맡김」으로 서 있는데 실제로는 돌거나 됐으면 사람이 또 맡긴다. 하나라도 이 손이 모르는 일이
        들었으면 받지 않는다 — 늦은 누름을 뒤늦게 넘기지 않는다. 받았나를 낸다."""
        took = False
        for key, (_, value) in run_rows.items():
            ids = value.get("ids")
            if key in presses or value.get("taken") or value.get("end") not in ("nohand", "noanswer") or not isinstance(ids, list) or not ids:
                continue
            page = press_page(key)
            holds = {tid: live_or_settled(presses, page, tid, key) for tid in ids if isinstance(tid, str)}
            if len(holds) != len(ids) or not all(holds.values()):
                continue
            names = {tid: ((presses.get(f) or {}).get("names") or {}).get(tid, "") for tid, f in holds.items()}
            presses[key] = {"page": page, "at": str(value.get("at")), "taken": T.stamp(T.local_now()), "ids": [], "held": holds, "tasks": {}, "names": names,
                            "launch": None, "state": ENDED, "end": "done", "said": ""}
            took = True
        return took

    def orphans(self, run_rows: dict, presses: dict) -> list[list[str]]:
        """창에 맡았다고 적혔는데 기록에 없는 누름의 칸 — 손이 「넘기는 중」을 남기기 전에 멈췄다(넘기기는 그 기록을 남긴 뒤에만 한다). 그래서
        넘긴 것이 없다 — 「못 맡김」과 그 까닭으로 맺는다. 아니면 창은 그 누름을 「하는 중」에 영영 묶는다. 기록이 걷었을 수 있는 오래된
        누름(`RUNS_KEEP_DAYS` 밖)은 건드리지 않는다 — 걷힌 판은 맡겨진 판이다."""
        cut = T.stamp(T.local_now() - dt.timedelta(days=RUNS_KEEP_DAYS))
        out = []
        for key, (_, value) in run_rows.items():
            if (value.get("taken") and not value.get("ended") and key not in presses and key not in self.pending
                    and str(value.get("taken")) >= cut):
                out += refuse_rows(key, value, SAID["unwritten"])
        return out

    def take(self, tab) -> list[str]:
        """새 누름을 맡기만 한다 — 맡을 누름마다 `take_one`. 다른 프로그램을 안 불러 곧 끝나므로, 넘기거나 따르느라 걸음이 길어진 동안에도
        기다리는 손이 불러 누름을 `brief_const.RUN_TAKE_S` 안에 맡는다(넘기기는 `step` 이). 기록에 남길 구절들을 낸다."""
        if tab is None:
            return []
        presses = self.load()
        said = [self.take_one(tab, key, raw, value, presses) for key, (raw, value) in E.cells(tab.read(RUN_KEYS), C.RUN_PREFIX).items()
                if takeable(key, value) and not (presses is not None and key in presses)]
        return [s for s in said if s]

    def take_one(self, tab, key: str, raw: str, value: dict, presses: dict | None) -> str:
        """누름 하나를 맡는다 — 창에 맡았다고 적고(그 사이 창이 맺었으면 안 맡는다) 기록에 「넘기는 중」을 남긴다. 기록을 못 읽었거나 못 썼으면
        그 위에 쓰지도 넘기지도 않고 일마다 까닭을 적어 맺는다. 기록에 남길 구절(안 맡았으면 "")."""
        taken = {**value, "taken": T.stamp(T.local_now())}
        if not tab.swap(C.RUN_PREFIX + key, raw, json.dumps(taken, ensure_ascii=False)):
            return ""
        if presses is None:
            tab.write(refuse_rows(key, taken, SAID["unread"]))
            return LOG_UNREAD.format(key=key)
        got = hand_over(self.folder, key, taken, presses)
        presses[key] = got["entry"]
        if not self.save():
            presses.pop(key)
            tab.write(refuse_rows(key, taken, SAID["unwritten"]))
            return LOG_UNWRITTEN.format(key=key)
        if got["go"]:
            self.pending[key] = got["go"]
        return LOG_TAKEN.format(key=key, go=len(got["go"]), held=len(got["entry"]["held"]))

    def step(self, tab) -> list[str]:
        """한 걸음 — 새 누름을 맡고, 맡은 누름을 넘기고, 창이 맺은 누름을 받고, 기록 없는 누름을 맺고, `FOLLOW_S` 마다 도는 판을 따르고, 창에
        적는다. 기록을 못 읽으면 맡기만 한다. 기록에 남길 구절들을 낸다."""
        said = self.take(tab)
        presses = self.load()
        if presses is None:
            return said
        said += self.launch_pending(presses)
        rows = tab.read(RUN_KEYS) if tab is not None else []
        run_rows, task_rows = E.cells(rows, C.RUN_PREFIX), E.cells(rows, C.TASK_PREFIX)
        if self.adopt(run_rows, presses):
            self.save()
        said += self.close_orphans(tab, run_rows, presses)
        self.follow_due(presses)
        if tab is not None:
            tab_write(tab, want_rows(presses, run_rows, task_rows))
        return said

    def launch_pending(self, presses: dict) -> list[str]:
        """이 손이 맡아 「넘기는 중」으로 둔 누름을 넘기고 기록을 쓴다 — 누름마다 기록에 남길 구절."""
        said = []
        for key in list(self.pending):
            go = self.pending.pop(key)
            if key in presses:
                launch(self.folder, key, presses[key], go, self.scan)
                self.save()
                said.append(LOG_LAUNCHED.format(key=key, how=presses[key].get("launch") or presses[key].get("end")))
        return said

    def close_orphans(self, tab, run_rows: dict, presses: dict) -> list[str]:
        """창에 맡았다고 적혔는데 기록에 없는 누름을 「못 맡김」으로 맺어 창에 적는다(`orphans`) — 맺었으면 기록에 남길 구절 하나."""
        if tab is None:
            return []
        orphans = self.orphans(run_rows, presses)
        if not orphans:
            return []
        tab.write(orphans)
        return [LOG_ORPHANS.format(n=sum(k.startswith(C.RUN_PREFIX) for k, _ in orphans))]

    def follow_due(self, presses: dict) -> None:
        """`FOLLOW_S` 가 지났으면 도는 판을 따르고(`follow` — 곧 넘길 누름은 빼고), 바뀌었으면 기록을 쓴다."""
        if time.monotonic() - self.followed < FOLLOW_S:
            return
        self.followed = time.monotonic()
        if follow(self.folder, presses, self.scan, skip=set(self.pending)):
            self.save()


def tab_write(tab, rows: list[list[str]]) -> None:
    """창에 칸들을 적는다 — 없으면 안 부른다."""
    if rows:
        tab.write(rows)


def refuse_rows(key: str, value: dict, said: str) -> list[list[str]]:
    """맡지 않은 누름의 칸 — 누름은 맺고 일마다 「못 함」과 그 까닭. 아무것도 안 넘겼다."""
    page, at = press_page(key), T.stamp(T.local_now())
    rows = [[C.RUN_PREFIX + key, json.dumps({**value, "ended": at, "end": REFUSED}, ensure_ascii=False)]]
    return rows + [[C.TASK_PREFIX + f"{page}/{tid}", json.dumps({"run": key, "state": "failed", "at": at, "said": said}, ensure_ascii=False)]
                   for tid in value.get("ids") or [] if isinstance(tid, str)]
