"""보고 창의 맡길 일 — 창에서 누른 일들을 뒤의 실행(형제 스킬 mailbox-scan 의 `scan.py handed`)에 넘기고, 그 실행의 기록을 따라 일마다의 끝을
창에 돌려 적는다. 창 곁의 손(곁의 `presses.py` 의 `watch`)이 걸음마다 `step` 을 부른다. 이 파일은 다른 프로그램을 띄우지 않는다 — 스캔의 명령은
부르는 쪽이 준 `scan` 하나로 부른다(`presses.run_scan`).

손은 일의 글을 읽어 무엇을 가르지 않는다 — 누른 창의 보고 글에서 그 일을 찾아(`brief_text.tasks_of`) 사람이 카드에서 읽은 줄(`Task.line`)과 카드의
줄을 적힌 그대로 넘기고, 실행이 일마다 쓴 결과 글을 그대로 창에 적는다. 계약 — 창의 저장소 칸은 `references/DESIGN.md` 「맡길 일」의 표, 실행의
명령 · 입력 · 기록은 형제 스킬 mailbox-scan 의 설계 「맡긴 일」의 표가 원본이다.

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
import brief_text as B  # noqa: E402
import edge as E  # noqa: E402
import store as S  # noqa: E402

RUNS_FILE = "daily-brief-runs.json"            # 맡긴 누름의 기록 — 누름마다 넘긴 판 · 일마다의 끝. 사용자 폴더에 산다. 쓰는 것은 창 곁의 손 하나다(잠금)
RUNS_KEEP_DAYS = 30                            # 맺은 누름의 기록을 두는 날 — 그 보고 창을 다시 열어 결과를 볼 만한 동안. 도는 누름은 날과 상관없이 둔다
TASKS_NAME = ".daily-brief-handed-{ms}.json"   # 실행에 줄 맡긴 일 파일 — 사용자 폴더에 잠깐 두고 맡긴 뒤 지운다(실행이 제 자리에 베낀다)
START_TIMEOUT_S = 60                           # `handed start` 한 번의 시한 — 기록을 쓰고 지킴이를 떼어 띄운 뒤 곧 돌아온다
SHOW_TIMEOUT_S = 30                            # `handed show` · `list` 한 번의 시한 — 읽기만 한다
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
    "nohand": "맡길 비서 프로그램(메일함 스캔)이 곁에 없어 맡지 않았습니다 — 아무것도 안 바뀌었습니다",
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
REFUSED = C.RUN_REFUSED                        # 누름의 끝 — 아무것도 넘기지 못했다(까닭은 일마다)


def now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def stamp(at: dt.datetime | None = None) -> str:
    return (at or now()).isoformat(timespec="seconds")


# ── 기록 — 없음과 못 읽음은 다른 답이다 ───────────────────────────────────────────

Unreadable = S.Unreadable                      # 기록 파일이 있는데 못 읽었다 — 그 위에 쓰면 맡긴 판을 잃어 같은 일을 다시 넘긴다


def read_runs(folder: pathlib.Path) -> dict:
    """기록 — {누름의 열쇠: 누름}. 파일이 없으면 빈 기록, 있는데 못 읽거나 꼴이 아니면 `Unreadable`."""
    data = S.read_json(folder / RUNS_FILE)
    if data is None:
        return {}
    presses = data.get("presses")
    if not isinstance(presses, dict) or not all(isinstance(v, dict) and isinstance(v.get("page"), str) and isinstance(v.get("ids"), list)
                                                and isinstance(v.get("tasks"), dict) for v in presses.values()):
        raise Unreadable("꼴이 아니다")                # 칸이 빠진 누름 위에서 걸으면 손이 넘어진다 — 못 읽음으로 두고 그 위에 안 쓴다
    return presses


def write_runs(folder: pathlib.Path, presses: dict) -> None:
    """새 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 기록이 남지 않는다. 오래되고 맺은 누름은 걷는다. 못 쓰면 OSError."""
    cut = stamp(now() - dt.timedelta(days=RUNS_KEEP_DAYS))
    keep = {k: v for k, v in presses.items() if isinstance(v, dict) and (v.get("state") != "ended" or str(v.get("taken", "")) >= cut)}
    for v in list(keep.values()):                  # 남는 누름이 따르는 누름도 남긴다 — 걷으면 따르는 쪽의 끝을 잃는다
        keep.update({f: presses[f] for f in (v.get("held") or {}).values() if f in presses})
    S.replace(folder / RUNS_FILE, json.dumps({"presses": keep}, ensure_ascii=False, indent=1).encode("utf-8"))


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
    return (at is not None and -C.RUN_TAKE_S < (now() - at).total_seconds() < C.RUN_TAKE_S and value.get("brief") == page
            and page.endswith(".html") and B.made_of(page) is not None and all(isinstance(i, str) for i in value["ids"]))


# ── 넘기기 ───────────────────────────────────────────────────────────────────

def last_of(presses: dict, page: str, tid: str, but: str = "") -> tuple[str, dict] | None:
    """그 보고의 그 일을 든 가장 늦은 누름(`but` 은 빼고) — (열쇠, 누름)."""
    found = [(k, v) for k, v in presses.items() if k != but and v.get("page") == page and tid in (v.get("ids") or []) + list(v.get("held") or {})]
    return max(found, key=lambda kv: str(kv[1].get("at", ""))) if found else None


def outcome(presses: dict, key: str, tid: str) -> dict | None:
    """그 누름에서 그 일의 끝 — 따르는 누름이면 따르는 판의 것."""
    v = presses.get(key) or {}
    follow = (v.get("held") or {}).get(tid)
    if follow:
        return outcome(presses, follow, tid)
    return (v.get("tasks") or {}).get(tid)


def live_or_settled(presses: dict, page: str, tid: str, but: str) -> str | None:
    """그 일이 이미 넘겨져 돌거나 다시 넘기면 안 될 끝으로 맺었으면 그 누름의 열쇠 — 다시 넘겨도 되면 None."""
    last = last_of(presses, page, tid, but)
    if last is None:
        return None
    key, v = last
    owner = (v.get("held") or {}).get(tid) or key   # 그 일을 실제로 넘긴 누름
    got = outcome(presses, key, tid) or {}
    if (presses.get(owner) or {}).get("state") != "ended":
        return owner if got.get("state") != "failed" else None   # 넘기는 중 · 도는 중 — 그 판의 끝을 따른다
    return owner if got.get("state") in SETTLED else None


def names_of(t: B.Task) -> str:
    """기록 · 다음 보고에 댈 그 일의 이름 — 「카드 n 「제목」 종류」."""
    return (f"카드 {t.num} " if t.num else "") + f"「{t.card}」 {t.kind}"


def hand_over(folder: pathlib.Path, key: str, value: dict, presses: dict) -> dict:
    """누름 하나를 가른다(창에 맡았다고 적은 뒤다) — {entry: 기록에 남길 누름, go: 실행에 넘길 일}. 이미 넘겨진 일은 그 판을 따르고(`held`), 못
    할 일은 그 까닭으로 맺는다. 누름의 `state` · `end` 는 이 누름이 넘긴 판의 몫이다 — 따르는 판까지 합친 끝은 `overall` 이 짓는다."""
    page = press_page(key)
    entry = {"page": page, "at": str(value.get("at")), "taken": stamp(), "ids": [], "held": {}, "tasks": {}, "names": {}, "kinds": {},
             "launch": None, "state": "ended", "end": "done", "said": ""}
    got = S.page_brief(folder, page)               # 누른 창의 보고 글 — 못 읽으면 일마다 「찾지 못했다」로 맺는다
    tasks = B.tasks_of(got[1]) if got else None
    go: list[B.Task] = []
    for tid in dict.fromkeys(value["ids"]):
        t = (tasks or {}).get(tid)
        if t is None or t.kind not in B.KINDS or t.kind == C.KIND_CAL:
            entry["tasks"][tid] = {"state": "failed", "at": stamp(), "said": SAID["gone" if t is None else "bad"]}
            continue
        entry["names"][tid], entry["kinds"][tid] = names_of(t), t.kind
        follow = live_or_settled(presses, page, tid, key)
        if follow:
            entry["held"][tid] = follow
        else:
            go.append(t)
    if go:
        entry.update(ids=[t.id for t in go], state="starting", end=None)
    elif not entry["held"]:                        # 넘길 것도 따를 것도 없다 — 일마다 까닭이 섰다
        entry.update(end=REFUSED, ended=stamp())
    return {"entry": entry, "go": go}


def launch(folder: pathlib.Path, key: str, entry: dict, go: list[B.Task], scan) -> None:
    """넘길 일을 실행에 넘긴다 — 기록에 「넘기는 중」을 남긴 뒤에 부른다(그 사이 손이 죽어도 다음 손이 그 누름을 다시 넘기지 않는다). 맡긴 일
    파일의 `brief` 에 누름의 열쇠를 실어, 끝을 못 받은 판을 도는 판의 목록에서 찾는다."""
    path = folder / TASKS_NAME.format(ms=key.rsplit("~", 1)[-1])
    body = {"brief": key, "tasks": [{"id": t.id, "kind": t.kind, "line": t.line(), "card": {"title": t.card, "lines": t.run_lines()},
                                     "labels": list(C.RESULT_LABELS.get(t.kind, ()))} for t in go]}
    try:
        path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    except OSError:
        settle_all(entry, "failed", SAID["unwritten"], REFUSED)
        return
    try:
        code, out = scan(["handed", "start", "--tasks", str(path)], START_TIMEOUT_S)
    finally:
        path.unlink(missing_ok=True)
    rec = last_json(out)
    if code == 0 and rec.get("id"):
        entry.update(launch=rec["id"], state="running")
        absorb(entry, rec)
    elif code is None and not out:                # 실행을 못 띄웠다 — 아무것도 안 넘겼다
        settle_all(entry, "failed", SAID["nohand"], REFUSED)
    elif rec.get("cannot") or rec.get("error"):   # 실행이 못 맡는다고 답했다(작업 폴더 · claude · 메일 손이 없다 · 꼴) — 기록을 안 썼다
        settle_all(entry, "failed", CANNOT.get(str(rec.get("cannot"))) or str(rec.get("message") or SAID["nohand"]), REFUSED)
    else:                                         # 시한을 넘겼거나 답이 꼴이 아니다 — 넘겨졌는지 도는 판에서 찾는다
        found = find_launch(key, scan)
        if found:
            entry.update(launch=found["id"], state="running")
            absorb(entry, found)
        else:
            settle_all(entry, "unsure", SAID["lost"], "stopped")


def last_json(out: str) -> dict:
    lines = [x for x in (out or "").strip().splitlines() if x.strip()]
    try:
        got = json.loads(lines[-1]) if lines else {}
    except ValueError:
        return {}
    return got if isinstance(got, dict) else {}


def find_launch(key: str, scan) -> dict | None:
    """그 누름의 판 — 도는 판의 목록(`handed list`)에서 `brief` 가 그 누름의 열쇠인 것. 없으면 None."""
    code, out = scan(["handed", "list"], SHOW_TIMEOUT_S)
    if code != 0:
        return None
    for line in (out or "").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict) and rec.get("brief") == key and rec.get("id"):
            return rec
    return None


def settle_all(entry: dict, state: str, said: str, end: str) -> None:
    """넘기려던 일을 다 그 끝으로 맺는다 — 못 넘긴 판(`REFUSED`)이거나 넘겼는지 모르는 판."""
    for tid in entry["ids"]:
        entry["tasks"][tid] = unsure_row(entry, tid, said) if state == "unsure" else {"state": state, "at": stamp(), "said": said}
    entry.update(state="ended", end=end, ended=stamp())


def unsure_row(entry: dict, tid: str, said: str) -> dict:
    """됐는지 모르는 일의 칸 — 아무것도 안 바꾸는 종류(`brief_const.READ_ONLY_KINDS`)는 모를 것이 없어 「못 함」이다(다시 맡겨도 된다)."""
    if (entry.get("kinds") or {}).get(tid) in C.READ_ONLY_KINDS:
        return {"state": "failed", "at": stamp(), "said": SAID["readonly"]}
    return {"state": "unsure", "at": stamp(), "said": said}


RESULT_FIELDS = (("said", str), ("facts", list), ("items", list), ("more", str))   # 실행의 기록 `tasks[].result` 의 칸 — 창의 `brief-task:` 칸과 같은 이름


def absorb(entry: dict, rec: dict) -> None:
    """실행의 기록 하나를 누름에 얹는다 — 일마다의 상태 · 때 · 결과(꼴대로 왔으면 그 칸들, 아니면 온 글 그대로) · 이어 갈 세션, 판이 끝났으면
    그 끝. 아무것도 안 바꾸는 종류가 「확인 안 됨」으로 맺었으면 「못 함」이다(`unsure_row`)."""
    session = rec.get("session") if isinstance(rec.get("session"), str) else None
    for t in rec.get("tasks") if isinstance(rec.get("tasks"), list) else []:
        if not isinstance(t, dict):
            continue
        state = STATES.get(str(t.get("state")))
        if t.get("id") not in entry["ids"] or state is None:
            continue
        if state == "unsure" and str(t.get("kind")) in C.READ_ONLY_KINDS:
            entry["tasks"][t["id"]] = {"state": "failed", "at": str(t.get("at") or stamp()), "said": SAID["readonly"]}
            continue
        got = t.get("result") if isinstance(t.get("result"), dict) else None
        row = {"state": state, "at": str(t.get("at") or stamp())}
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
        entry.update(state="ended", end=ENDS.get(str(rec.get("end")), "stopped"), said=" ".join(str(rec.get("said") or "").split())[:C.SAID_MAX],
                     ended=str(rec.get("ended") or stamp()))


def follow(folder: pathlib.Path, presses: dict, scan, skip: set[str] = frozenset()) -> bool:
    """도는 판마다 실행의 기록을 다시 읽어 누름에 얹는다 — 바뀌었나. 넘기다 손이 죽은 누름(「넘기는 중」)은 도는 판의 목록에서 찾고, 없으면
    확인 안 됨으로 맺는다 — 넘겨졌을 수 있다."""
    changed = False
    for key, entry in presses.items():
        if key in skip:                            # 이 손이 맡아 곧 넘길 누름 — 넘기다 죽은 누름이 아니다
            continue
        if entry.get("state") == "starting":
            found = find_launch(key, scan)
            if found:
                entry.update(launch=found["id"], state="running")
                absorb(entry, found)
            else:
                settle_all(entry, "unsure", SAID["lost"], "stopped")
            changed = True
        elif entry.get("state") == "running" and entry.get("launch"):
            code, out = scan(["handed", "show", "--id", entry["launch"]], SHOW_TIMEOUT_S)
            rec = last_json(out)
            if code == 0 and rec.get("id") == entry["launch"]:
                before = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                entry.pop("missing", None)
                absorb(entry, rec)
                changed |= json.dumps(entry, sort_keys=True, ensure_ascii=False) != before
            elif not entry.get("missing"):
                entry["missing"] = stamp()
                changed = True
            elif (now() - dt.datetime.fromisoformat(entry["missing"])).total_seconds() >= MISSING_S:
                for tid in entry["ids"]:
                    if (entry["tasks"].get(tid) or {}).get("state") in (None, "doing"):
                        entry["tasks"][tid] = unsure_row(entry, tid, SAID["missing"])
                entry.update(state="ended", end="stopped", ended=stamp())
                changed = True
    return changed


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
        return True, "stopped", stamp()
    held = sorted(set((v.get("held") or {}).values()) - {key})
    parts = [] if held and not v.get("ids") else [(v.get("state") == "ended", str(v.get("end") or "done"), str(v.get("ended") or v.get("taken") or ""))]
    parts += [overall(presses, f, depth + 1) for f in held]
    if not all(p[0] for p in parts):
        return False, "", ""
    ends = [p[1] for p in parts]
    return True, next((e for e in ("session", "stopped", REFUSED) if e in ends), "done"), latest([p[2] for p in parts])


def want_rows(presses: dict, run_rows: dict, task_rows: dict) -> list[list[str]]:
    """창에 적을 칸 — 기록이 든 누름마다 그 누름의 칸(맡은 때 · 맺었으면 그 끝 — 창의 저장소에 맺음이 적혀 있어도 판이 아직 돌면 그 맺음을 걷는다)과
    일마다의 칸(그 일을 든 가장 늦은 누름의 끝). 저장소의 값과 같은 칸은 안 적는다."""
    out = []
    for key, entry in presses.items():
        raw = run_rows.get(key)
        if raw is None:
            continue                               # 창의 저장소에 없는 누름 — 그 창이 지웠거나 다른 Edge 다. 새로 세우지 않는다
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
    seen: set[tuple[str, str]] = set()
    for key, entry in sorted(presses.items(), key=lambda kv: str(kv[1].get("at", "")), reverse=True):
        if key not in run_rows:
            continue
        for tid in list(entry.get("ids") or []) + list(entry.get("held") or {}) + list(entry.get("tasks") or {}):
            if (entry["page"], tid) in seen:
                continue
            seen.add((entry["page"], tid))
            got = outcome(presses, key, tid)
            if not got:
                continue
            row = {"run": key, **got}
            slot = f"{entry['page']}/{tid}"
            if task_rows.get(slot, (None, None))[1] != row:
                out.append([C.TASK_PREFIX + slot, json.dumps(row, ensure_ascii=False)])
    return out


# ── 한 걸음 ──────────────────────────────────────────────────────────────────

class Runs:
    """창 곁의 손이 든 맡긴 일 — 기록을 쥐고, 걸음마다 새 누름을 맡고 도는 판을 따르고 창에 적는다. `scan` 은 스캔의 명령을 부르는 손."""

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
        try:
            write_runs(self.folder, self.presses or {})
            return True
        except OSError:
            return False

    def busy(self) -> bool:
        """넘기는 중 · 도는 판이 있나 — 있으면 창 곁의 손이 열린 창이 없어도 남아 끝을 받는다."""
        presses = self.load() or {}
        return any(v.get("state") in ("starting", "running") for v in presses.values())

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
            presses[key] = {"page": page, "at": str(value.get("at")), "taken": stamp(), "ids": [], "held": holds, "tasks": {}, "names": names,
                            "launch": None, "state": "ended", "end": "done", "said": ""}
            took = True
        return took

    def orphans(self, run_rows: dict, presses: dict) -> list[list[str]]:
        """창에 맡았다고 적혔는데 기록에 없는 누름의 칸 — 손이 「넘기는 중」을 남기기 전에 멈췄다(넘기기는 그 기록을 남긴 뒤에만 한다). 그래서
        넘긴 것이 없다 — 「못 맡김」과 그 까닭으로 맺는다. 아니면 창은 그 누름을 「하는 중」에 영영 묶는다. 기록이 걷었을 수 있는 오래된
        누름(`RUNS_KEEP_DAYS` 밖)은 건드리지 않는다 — 걷힌 판은 맡겨진 판이다."""
        cut = stamp(now() - dt.timedelta(days=RUNS_KEEP_DAYS))
        out = []
        for key, (_, value) in run_rows.items():
            if (value.get("taken") and not value.get("ended") and key not in presses and key not in self.pending
                    and str(value.get("taken")) >= cut):
                out += refuse_rows(key, value, SAID["unwritten"])
        return out

    def take(self, tab) -> list[str]:
        """새 누름을 맡기만 한다 — 창에 맡았다고 적고 기록에 「넘기는 중」을 남긴다(넘기기는 `step` 이). 다른 프로그램을 안 불러 곧 끝나므로, 넘기거나
        따르느라 걸음이 길어진 동안에도 기다리는 손이 불러 누름을 `brief_const.RUN_TAKE_S` 안에 맡는다. 기록에 남길 구절들을 낸다."""
        said: list[str] = []
        if tab is None:
            return said
        presses = self.load()
        rows = tab.read(RUN_KEYS)
        for key, (raw, value) in E.cells(rows, C.RUN_PREFIX).items():
            if not takeable(key, value) or (presses is not None and key in presses):
                continue
            taken = {**value, "taken": stamp()}
            if not tab.swap(C.RUN_PREFIX + key, raw, json.dumps(taken, ensure_ascii=False)):
                continue                           # 그 사이 창이 맺었다 — 맡지 않는다
            if presses is None:                    # 기록을 못 읽었다 — 그 위에 쓰지도 넘기지도 않는다. 일마다 까닭을 적고 맺는다
                tab.write(refuse_rows(key, taken, SAID["unread"]))
                said.append(f"맡긴 일 — {key} 를 맡지 않았다(기록을 못 읽었다)")
                continue
            got = hand_over(self.folder, key, taken, presses)
            presses[key] = got["entry"]
            if not self.save():                    # 「넘기는 중」을 못 남겼다 — 넘기지 않는다
                presses.pop(key)
                tab.write(refuse_rows(key, taken, SAID["unwritten"]))
                said.append(f"맡긴 일 — {key} 를 맡지 않았다(기록을 못 썼다)")
                continue
            if got["go"]:
                self.pending[key] = got["go"]
            said.append(f"맡긴 일 — {key} 맡음 · 넘길 것 {len(got['go'])} · 따름 {len(got['entry']['held'])}")
        return said

    def step(self, tab) -> list[str]:
        """한 걸음 — 새 누름을 맡고(`take`), 맡은 누름을 넘기고, `FOLLOW_S` 마다 도는 판을 따르고, 창에 적는다. 기록에 남길 구절들을 낸다."""
        said = self.take(tab)
        presses = self.load()
        if presses is None:
            return said
        for key in list(self.pending):             # 이 손이 맡아 「넘기는 중」으로 둔 누름 — 넘긴다
            go = self.pending.pop(key)
            if key in presses:
                launch(self.folder, key, presses[key], go, self.scan)
                self.save()
                said.append(f"맡긴 일 — {key} 넘김 · {presses[key].get('launch') or presses[key].get('end')}")
        rows = tab.read(RUN_KEYS) if tab is not None else []
        run_rows, task_rows = E.cells(rows, C.RUN_PREFIX), E.cells(rows, C.TASK_PREFIX)
        if self.adopt(run_rows, presses):
            self.save()
        if tab is not None:
            orphans = self.orphans(run_rows, presses)
            if orphans:
                tab.write(orphans)
                said.append(f"맡긴 일 — 맡았다고만 적고 기록에 없는 누름 {sum(k.startswith(C.RUN_PREFIX) for k, _ in orphans)}개를 못 맡김으로 맺었다")
        if time.monotonic() - self.followed >= FOLLOW_S:
            self.followed = time.monotonic()
            if follow(self.folder, presses, self.scan, skip=set(self.pending)):
                self.save()
        if tab is not None:
            changed = want_rows(presses, run_rows, task_rows)
            if changed:
                tab.write(changed)
        return said


def refuse_rows(key: str, value: dict, said: str) -> list[list[str]]:
    """맡지 않은 누름의 칸 — 누름은 맺고 일마다 「못 함」과 그 까닭. 아무것도 안 넘겼다."""
    page, at = press_page(key), stamp()
    rows = [[C.RUN_PREFIX + key, json.dumps({**value, "ended": at, "end": REFUSED}, ensure_ascii=False)]]
    return rows + [[C.TASK_PREFIX + f"{page}/{tid}", json.dumps({"run": key, "state": "failed", "at": at, "said": said}, ensure_ascii=False)]
                   for tid in value.get("ids") or [] if isinstance(tid, str)]


RECENT_WORDS = {"done": "됨", "asked": "여쭐 것이 있어 멈춤", "failed": "못 함", "unsure": "됐는지 확인 못 함", "doing": "하는 중"}


def recent_lines(folder: pathlib.Path) -> list[str]:
    """보고를 짓는 쪽이 읽을 것 — 가장 늦은 보고 글 뒤에 창에서 맡기신 일마다 그 끝(없으면 빈 목록 · 기록을 못 읽으면 그렇다는 한 줄)."""
    briefs = B.kept_briefs(folder) if folder.is_dir() else []
    if not briefs:
        return []
    since = stamp(B.made_of(briefs[-1].name).astimezone())
    try:
        presses = read_runs(folder)
    except Unreadable as exc:
        return [f"맡긴 일 — 기록({folder / RUNS_FILE})을 못 읽었다({exc}). 지난 보고 뒤 창에서 맡기신 일의 끝을 모른다"]
    rows, seen = [], set()
    for key, v in sorted(presses.items(), key=lambda kv: str(kv[1].get("taken", "")), reverse=True):   # 같은 일은 가장 늦은 누름의 끝 하나
        if str(v.get("taken", "")) < since:
            continue
        for tid, name in (v.get("names") or {}).items():
            if (v.get("page"), tid) in seen:
                continue
            seen.add((v.get("page"), tid))
            got = outcome(presses, key, tid) or {}
            state = got.get("state") or ("하는 중" if v.get("state") != "ended" else "")
            facts = " · ".join(f"{f[0]} {f[1]}" for f in got.get("facts") or [] if isinstance(f, list) and len(f) == 2)
            first = " ".join(str(got.get("said") or facts).split())[:80]   # 결과가 값뿐이면(회의실 따위) 그 값이 무엇을 했나를 댄다
            rows.append(f"- {name} — {RECENT_WORDS.get(state, state or '기다림')}" + (f" · {first}" if first else ""))
    if not rows:
        return []
    return (["맡긴 일 — 지난 보고 뒤 창에서 맡기신 일의 끝이다. 다시 올릴지는 lane.md 「맡길 일」의 「지난번 맡기신 일」:"] + rows)
