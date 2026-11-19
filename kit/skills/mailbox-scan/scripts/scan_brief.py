"""정한 시각의 보고 — 스캔 판이 사용자가 정한 보고 시각표의 시각마다 일일 보고(스킬 daily-brief)를 사람 없이 한 번씩 띄운다. 설정 · 그날의
살펴보기 · 띄우기 · 권한 · 보고 창에서 고르신 시각.

    setting, problem = load(folder)              # brief.json — 안 걸었으면 (None, ""), 못 읽으면 (None, 까닭). 시각표는 setting["times"]
    save(folder, times=["07:30", "13:00"], claude=path, login=False) · clear(folder)
    times, bad = times_given(["07:30", "13:00"]) # 받은 시각들 → 정렬한 시각표 · 꼴이 아니면 까닭
    refused = no_room(times)                     # 기다릴 틈이 모자란 시각이 있으면 거절의 말 — 받으면 ""
    line = after_run(state, folder, evidence, hand, at)   # 판 끝 — 지금 칸의 시각이 사내 세션이 살아 있는 첫 판에 띄운다. 할 말이 없으면 ""
                                                          # 스스로 로그인을 켠 PC 는 그날 첫 시각의 띄우기 앞에 한 번 로그인 입구를 부른다
    lines = describe(state, folder, at)          # status 가 말할 줄 — 시각마다
    words = window_words(times)                  # 거는 말 · status 가 함께 쓰는 「언제 띄우나」 한 구절
    cmd, settings, prompt = plan(setting, hand, folder)   # 띄울 명령 · 권한 · 부탁 글(띄우기와 `--dry-run` 이 같은 것을 쓴다)

언제 띄우나 · 띄운 claude 에 무엇을 여나 · 로그인을 언제 하고 언제 안 하나 · 보고 창에서 고르신 시각을 어떻게 받나는
`references/DESIGN.md` 「정한 시각의 보고」가 든다.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any

import scan_const as C
import scan_hand as H
import scan_store as st

LIVE, LOST, ERROR = "live", "lost", "error"          # 살펴보기의 답 — 사내 세션이 살았다 · 없다 · 손이 답을 못 냈다
LOG_TAIL_CHARS = 200                                 # status 가 띄운 보고의 출력에서 옮겨 보이는 끝 줄의 글자 수
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_DIR.parents[1]                  # 이 스킬 · 일일 보고 스킬이 나란히 선 스킬 뿌리
# 보고 창 손(`ticks.py --times`)이 내는 고르신 시각의 줄 — 꼴의 원본은 그 손의 `TIMES_LINE`. 고른 때는 그 손에 그대로 돌려준다
CLOCKS = r"(?:\d{1,2}:\d{2})(?: \d{1,2}:\d{2})*"
WINDOW_TIMES = re.compile(rf"^고르신 보고 시각: ({CLOCKS}) · 보던 시각: ({CLOCKS}|-) · 고르신 때 (\S{{1,40}})$", re.M)
SAID_CHARS = 240                                     # 보고 창에 돌려 적는 말의 글자 수


# ── 설정 ─────────────────────────────────────────────────────────────────────

def clock(text: str) -> str | None:
    """「H:MM」 · 「HH:MM」 → 「HH:MM」. 꼴이 아니면 None."""
    try:
        return datetime.strptime(text.strip(), "%H:%M").strftime("%H:%M")
    except (ValueError, AttributeError):
        return None


def times_given(texts: list[str]) -> tuple[list[str], str]:
    """받은 시각들(빈칸 · 쉼표로 여럿도) → 정렬하고 겹친 것을 걷은 시각표. 꼴이 아닌 것이 있으면 ([], 까닭)."""
    got: set[str] = set()
    for part in " ".join(texts).replace(",", " ").split():
        one = clock(part)
        if one is None:
            return [], f"보고 시각 {part!r} 가 「HH:MM」 꼴이 아니다"
        got.add(one)
    if not got:
        return [], "보고 시각이 하나도 없다"
    return sorted(got), ""


def find_claude(explicit: str | None) -> pathlib.Path | None:
    """띄울 claude — `--claude` 가 가리키는 파일, 없으면 PATH 에서 `CLAUDE_NAMES` 차례. 못 찾으면 None."""
    if explicit:
        path = pathlib.Path(explicit).expanduser()
        return path.resolve() if path.is_file() else None
    for name in C.CLAUDE_NAMES:
        found = shutil.which(name)
        if found:
            return pathlib.Path(found)
    return None


def load(folder: pathlib.Path) -> tuple[dict[str, Any] | None, str]:
    """(설정, 못 읽은 까닭). 안 걸었으면 (None, ""). 시각 하나(꼴 1)로 걸어 둔 설정도 읽어 `times` 를 채운다."""
    try:
        data = json.loads((folder / C.BRIEF_FILE).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, ""
    except (OSError, ValueError) as exc:
        return None, f"{C.BRIEF_FILE} 를 못 읽었다({type(exc).__name__})"
    if not isinstance(data, dict) or data.get("format") not in C.BRIEF_FORMATS_READ or not data.get("claude"):
        return None, f"{C.BRIEF_FILE} 의 꼴이 이 스크립트와 다르다"
    raw = data.get("times") if data.get("format") != 1 else [data.get("at")]
    times, bad = times_given([str(x) for x in raw]) if isinstance(raw, list) and all(isinstance(x, str) for x in raw) else ([], "꼴")
    if bad:
        return None, f"{C.BRIEF_FILE} 의 보고 시각이 꼴이 아니다"
    data["times"] = times
    return data, ""


def save(folder: pathlib.Path, times: list[str], claude: pathlib.Path, login: bool = False) -> None:
    st.write_json(folder / C.BRIEF_FILE, {"format": C.BRIEF_FORMAT, "times": list(times), "claude": str(claude), "login": bool(login),
                                          "set": st.stamp(st.now()), "room_min": C.BRIEF_ROOM_MIN, "wait_min": C.BRIEF_WAIT_MIN})
    # ↑ 규칙의 수 둘은 보고 창이 더하실 시각을 바로 재는 데 쓴다(일일 보고의 window.state_of) — 원본은 scan_const 한 자리다


def login_words(login: bool) -> str:
    """로그인을 어떻게 하나의 한 구절 — 거는 말과 status 가 같은 말을 쓴다."""
    return ("그날 첫 시각의 보고 앞에 한 번 스스로 로그인한다(사내 세션이 살아 있어도 — 윈도 로그온마다 평소 Edge 에서 먼저) — 입력 없이 넘는 "
            "통합 인증으로만, 이어 ep-login 창을 띄워 둔다. 뒤 시각은 살아 있는 세션에서만 띄운다" if login
            else "로그인은 안 한다")


def clear(folder: pathlib.Path) -> bool:
    """보고를 내린다 — 걸려 있었으면 True."""
    try:
        (folder / C.BRIEF_FILE).unlink()
        return True
    except FileNotFoundError:
        return False


# ── 시각표의 칸 ──────────────────────────────────────────────────────────────

def seoul_date(at: datetime) -> str:
    return st.seoul(at, "%Y-%m-%d")


def on_day(text: str, at: datetime) -> datetime:
    """서울 날짜 `at` 의 그 시각(「HH:MM」)."""
    hour, minute = map(int, clock(text).split(":"))
    return at.astimezone(st.KST).replace(hour=hour, minute=minute, second=0, microsecond=0)


def until_given() -> str | None:
    """검사가 준 기다림의 끝 「HH:MM」(`BRIEF_UNTIL_ENV`) — 없으면 None(시각마다 `BRIEF_WAIT_MIN` 분까지)."""
    return clock(os.environ.get(C.BRIEF_UNTIL_ENV, ""))


def windows(times: list[str], at: datetime) -> list[tuple[str, datetime, datetime, datetime]]:
    """그날의 칸 — 시각마다 (시각, 덮는 첫때, 시작, 끝). 끝은 다음 시각 · 그 시각에서 `BRIEF_WAIT_MIN` 분 뒤 · 그날 자정 가운데 이른 것.
    덮는 첫때는 앞 칸의 끝(첫 칸은 그날 0시)이다 — 그 뒤 이 칸의 끝 전에 지은 보고 글(대화에서 지은 것도)이 이 칸의 보고다."""
    starts = [on_day(t, at) for t in times]
    midnight = on_day("00:00", at)
    given = until_given()
    out: list[tuple[str, datetime, datetime, datetime]] = []
    for i, (t, start) in enumerate(zip(times, starts)):
        cap = on_day(given, at) if given else start + timedelta(minutes=C.BRIEF_WAIT_MIN)
        end = min(cap, midnight + timedelta(days=1), *starts[i + 1:i + 2])
        out.append((t, out[-1][3] if out else midnight, start, end))
    return out


def squeezed(times: list[str]) -> list[tuple[str, str | None, int]]:
    """기다릴 틈이 `BRIEF_ROOM_MIN` 분보다 짧은 시각 — (시각, 붙은 다음 시각 · 그날 끝이면 None, 틈 분)."""
    out = []
    for i, (t, _, start, end) in enumerate(windows(times, st.now())):
        room = int((end - start).total_seconds() // 60)
        if room < C.BRIEF_ROOM_MIN:
            near = times[i + 1] if i + 1 < len(times) and on_day(times[i + 1], start) == end else None
            out.append((t, near, max(room, 0)))
    return out


def no_room(times: list[str], added: frozenset[str] | set[str] = frozenset()) -> str:
    """틈이 모자란 시각이 있으면 거절의 말(사람에게 하는 말) — 그 시각에는 스캔 판이 안 돌아 보고가 날마다 안 뜬다. 붙은 두 시각 가운데
    새로 더하신 쪽(`added`)을 짚는다. 받으면 ""."""
    for t, near, room in squeezed(times):
        if near:
            who, other = (near, t) if near in added and t not in added else (t, near)
            return (f"{who} 보고는 {other} 보고와 {room}분밖에 안 떨어져 있습니다 — 보고 시각끼리는 {C.BRIEF_ROOM_MIN}분 넘게 띄어 "
                    "주세요")
        latest = (datetime(2000, 1, 2) - timedelta(minutes=C.BRIEF_ROOM_MIN)).strftime("%H:%M")
        return f"{t} 보고는 그날이 끝나기까지 {room}분뿐입니다 — 보고 시각은 {latest} 전에 두어 주세요"
    return ""


def in_force(setting: dict[str, Any] | None) -> str:
    """지금 걸린 시각표의 한 구절 — 거절할 때마다 함께 댄다."""
    return f"지금 걸린 보고 시각은 {' · '.join(setting['times'])} 입니다" if setting else "지금 걸린 보고 예약은 없습니다"


def hhmm(t: datetime | str | None) -> str:
    """서울 「HH:MM」 — 저장된 글자도 받는다."""
    when = st.parse(t) if isinstance(t, str) or t is None else t
    return when.astimezone(st.KST).strftime("%H:%M") if when else ""


def end_words(end: datetime, start: datetime) -> str:
    """칸의 끝 「HH:MM」 — 그날 자정이면 「자정」."""
    return "자정" if end.astimezone(st.KST).date() != start.astimezone(st.KST).date() else hhmm(end)


def window_words(times: list[str]) -> str:
    """언제 띄우나의 한 구절 — 거는 말과 status 가 같은 말을 쓴다."""
    spans = " · ".join(f"{t}({end_words(end, start)} 까지)" for t, _, start, end in windows(times, st.now()))
    return f"날마다 서울 {spans} — 시각마다 그 틈에 사내 세션이 서는 첫 판에"


def current(times: list[str], at: datetime) -> tuple[int, str, datetime, datetime, datetime] | None:
    """지금 든 칸 — (차례, 시각, 덮는 첫때, 시작, 끝). 첫 시각 전 · 칸 사이 · 마지막 칸 뒤면 None."""
    for i, (t, cover, start, end) in enumerate(windows(times, at)):
        if start <= at < end:
            return i, t, cover, start, end
    return None


# ── 그날 ─────────────────────────────────────────────────────────────────────

def day_of(state: dict[str, Any], at: datetime, times: list[str], keep: bool = True, login: bool = False,
           setting: dict[str, Any] | None = None) -> dict[str, Any]:
    """그날의 살펴보기 — 서울 날짜가 바뀌었으면 새 판(지난날 건너뛴 시각을 `before` 에 한 줄로 남긴다). 시각 하나를 쓰던 꼴의 그날 칸은
    첫 시각의 칸으로 옮겨 읽는다. `keep` 이면 지금 모습에 넣는다(판 안에서만 — status 는 안 바꾼다)."""
    got = state.get("brief")
    if isinstance(got, dict) and "slots" not in got:
        old = {"tries": got.get("tries") or [], "launched": got.get("launched")}
        got = {"date": got.get("date"), "slots": {times[0]: old} if times and (old["tries"] or old["launched"]) else {},
               "login": got.get("login")}
        if keep:
            state["brief"] = got
    if not isinstance(got, dict) or got.get("date") != seoul_date(at):
        before = skipped_words(got, times, login, setting) if isinstance(got, dict) and got.get("date") else []
        got = {"date": seoul_date(at), "slots": {}, "login": None, **({"before": before} if before else {})}
        if keep:
            state["brief"] = got
    return got


def slot_of(day: dict[str, Any], t: str) -> dict[str, Any]:
    return day.setdefault("slots", {}).setdefault(t, {"tries": [], "launched": None})


def last_try(state: dict[str, Any]) -> str | None:
    """그날 가장 늦은 살펴보기의 답 — 판 기록에 싣는다. 없으면 None."""
    tries = [t for s in ((state.get("brief") or {}).get("slots") or {}).values() for t in s.get("tries") or []]
    return max(tries, key=lambda t: t.get("at") or "").get("session") if tries else None


def made_between(cover: datetime, end: datetime) -> list[pathlib.Path]:
    """그 칸의 날 보고 글 가운데 이름의 때(서울)가 `cover` 부터 `end` 전인 것 — 이름 차례."""
    out = []
    for f in sorted(st.home().glob(C.BRIEF_MADE.format(date=seoul_date(cover)))):
        try:
            made = datetime.strptime(f.stem[-4:], "%H%M").strftime("%H:%M")
        except ValueError:
            continue
        if cover <= on_day(made, cover) < end:
            out.append(f)
    return out


def reports(day: dict[str, Any], times: list[str], order: int, at: datetime) -> list[pathlib.Path]:
    """그 칸의 보고 글 — 덮는 첫때부터 끝 전에 이름의 때가 든 글에서 앞 칸이 띄운 보고가 남긴 글(그 띄운 때부터 `BRIEF_LOCK_STALE_S` 안)을
    빼고, 이 칸이 띄운 보고가 남긴 글을 더한다. 칸 끝 무렵 띄운 보고는 글을 칸이 끝난 뒤에 쓴다 — 그 글로 다음 칸이 안 띄우면 안 된다."""
    wins = windows(times, at)
    _, cover, _, end = wins[order]
    slots = day.get("slots") or {}

    def launched_span(t: str) -> tuple[datetime, datetime] | None:
        got = (slots.get(t) or {}).get("launched") or {}
        since = st.parse(got.get("at")) if not got.get("error") else None
        since = since.replace(second=0, microsecond=0) if since else None     # 글 이름의 때는 분까지다
        return (since, since + timedelta(seconds=C.BRIEF_LOCK_STALE_S)) if since else None

    prev = launched_span(wins[order - 1][0]) if order else None
    own = launched_span(wins[order][0])
    got = [f for f in made_between(cover, end) if not (prev and f in made_between(*prev))]
    got += [f for f in made_between(*own) if f not in got] if own else []
    return sorted(got, key=lambda f: f.name)


def lock_held(folder: pathlib.Path, at: datetime) -> dict[str, Any] | None:
    """스캔이 띄운 보고가 도는 중이면 그 잠금 — 띄운 때에서 `BRIEF_LOCK_STALE_S` 가 지났으면 끝났거나 멈춘 것이라 None."""
    try:
        held = json.loads((folder / C.BRIEF_LOCK_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    since = st.parse(held.get("started")) if isinstance(held, dict) else None
    if since is None or (at - since).total_seconds() >= C.BRIEF_LOCK_STALE_S:
        return None
    return held


def minute(t: datetime) -> int:
    return int(t.timestamp() // 60)


def waiting(day: dict[str, Any], times: list[str], order: int, slot: dict[str, Any], at: datetime, folder: pathlib.Path) -> str:
    """지금 칸에서 살펴보지 않는 까닭 — 살펴볼 때면 ""."""
    if reports(day, times, order, at):
        return "made"
    if slot.get("launched"):
        return "launched"
    if lock_held(folder, at):
        return "running"
    return ""


def spaced(slot: dict[str, Any], at: datetime) -> bool:
    """손에 다시 물어도 되나 — 그 칸의 마지막 살펴보기에서 `BRIEF_TRY_GAP_MIN` 분이 지났다(작업이 더 자주 깨워도 SSO 를 촘촘히 안 두드린다)."""
    tries = slot.get("tries") or []
    last = st.parse(tries[-1]["at"]) if tries else None
    return last is None or minute(at) - minute(last) >= C.BRIEF_TRY_GAP_MIN


def look(hand: pathlib.Path | None) -> str:
    """사내 세션이 살았나 — 손의 `session` 한 번. 로그인 화면을 열지 않는다."""
    if hand is None:
        return ERROR
    try:
        got = H.call(hand, ["session"])
    except H.ShapeError:
        return ERROR
    return LIVE if got.code == C.HAND_EXIT_OK else LOST if got.code == C.HAND_EXIT_SESSION else ERROR


def entrance(hand: pathlib.Path | None) -> pathlib.Path | None:
    """형제 스킬 ep-login 의 입구 — `LOGIN_ENTRANCE_ENV`, 없으면 손과 같은 스킬 뿌리의 그 스킬. 없으면 None."""
    given = os.environ.get(C.LOGIN_ENTRANCE_ENV, "").strip()
    if given:
        path = pathlib.Path(given)
    elif hand is not None:
        path = hand.parents[2] / C.SESSION_SKILL / pathlib.Path(*C.LOGIN_ENTRANCE)
    else:
        return None
    return path if path.is_file() else None


def login_command(hand: pathlib.Path | None) -> list[str] | None:
    """스스로 로그인이 부를 명령 — 입구나 node 가 없으면 None(거는 명령이 이것으로 거절하고 `--dry-run` 이 보인다)."""
    script, node = entrance(hand), shutil.which(C.LOGIN_NODE)
    return [node, str(script), *C.LOGIN_ARGS] if script is not None and node is not None else None


def sign_in(hand: pathlib.Path | None, at: datetime) -> dict[str, Any]:
    """스스로 로그인 한 번 — 입구를 사람 없는 꼴로 부른다(사람이 쳐야 하는 자리에서는 입구가 기다리지 않고 끝난다).
    내는 것 — {at, ok: True} 나 {at, ok: False, said}."""
    def failed(said: str) -> dict[str, Any]:
        return {"at": st.stamp(at), "ok": False, "said": said[:C.LOGIN_SAID_CHARS]}
    script, node = entrance(hand), shutil.which(C.LOGIN_NODE)
    if script is None:
        return failed("로그인 입구(스킬 ep-login)를 못 찾았다")
    if node is None:
        return failed("node 를 못 찾았다")
    try:
        done = subprocess.run([node, str(script), *C.LOGIN_ARGS], capture_output=True, timeout=C.LOGIN_TIMEOUT_S,
                              stdin=subprocess.DEVNULL, **H._quiet())
    except subprocess.TimeoutExpired:
        return failed(f"로그인 입구가 {C.LOGIN_TIMEOUT_S}초 안에 안 끝났다")
    except OSError as exc:
        return failed(f"{type(exc).__name__}: {exc}")
    if done.returncode == 0:
        return {"at": st.stamp(at), "ok": True}
    lines = [x.strip() for x in done.stderr.decode("utf-8", "replace").splitlines() if x.strip()]
    return failed(lines[-1] if lines else f"로그인 입구가 종료 {done.returncode} 로 끝났다")


def after_run(state: dict[str, Any], folder: pathlib.Path, evidence: str | None, hand: pathlib.Path | None, at: datetime) -> str:
    """판 끝 — 보고 창에서 고르신 시각을 먼저 받고, 지금 칸의 시각이 살펴볼 때면 사내 세션을 보고 살아 있으면 띄운다. `evidence` 는 그
    판이 손에서 받은 답이라 늘 쓰고(세션 파일이 새로 쓰여 판이 돌았으면 그 판에 바로 띄운다), 답이 없는 판(None)만 틈(`spaced`)을 지켜
    손에 묻는다. 세션이 없으면 로그인은 안 하고 기다린다 — 사용자가 스스로 로그인을 켠 PC 만 그날 첫 시각의 띄우기 앞에 한 번 입구를
    부르고(세션이 살았어도 — 평소 Edge 로그인은 입구가 로그온마다 한 번 든다), 서면 그 판에 띄운다(못 세운 날은 다시 안 부른다). 뒤
    시각은 스스로 로그인하지 않는다 — 살아 있는 세션에서만 띄운다.
    `state` 의 그날 칸을 고치고 파일 쓰기는 부르는 쪽 몫이다. 내는 것 — 판 끝에 찍을 줄(할 말이 없으면 "")."""
    said = window_times(folder)
    setting, _ = load(folder)
    if setting is None:
        return said
    times = setting["times"]
    day = day_of(state, at, times, login=bool(setting.get("login")), setting=setting)
    now = current(times, at)
    if now is None:
        return said
    order, t, _, _, end = now
    slot = slot_of(day, t)
    if waiting(day, times, order, slot, at, folder):
        return said
    lines = [said] if said else []
    if evidence is None:
        if not spaced(slot, at):
            return said
        evidence = look(hand)
        if evidence == LIVE:
            state.pop("session", None)       # 세션이 살아 있으니 끊겼다는 기다림을 걷는다 — 다음 주기에 스캔이 바로 돈다
    signed, was = None, evidence
    # 켠 PC 는 그날 첫 시각의 띄우기 앞에 입구를 한 번 부른다 — 세션이 살았어도: 입구가 이 윈도 로그온의 평소 Edge 로그인을 먼저 하고(포트
    # 창 세션은 새 로그온에도 살아 있을 수 있다), 이 로그온에 이미 했으면 받기만 하고 끝난다. 뒤 시각은 안 부른다 — 낮의 사람 없는 로그인은
    # 사람이 일하던 EP 세션을 끊을 수 있다
    if evidence in (LIVE, LOST) and order == 0 and setting.get("login") and not day.get("login"):
        signed = day["login"] = sign_in(hand, at)    # 하루 한 번 — 되풀이하면 다른 자리에서 연 사람의 메일을 판마다 끊는다
        if signed["ok"]:
            evidence = LIVE
            state.pop("session", None)
        elif was == LIVE:
            evidence = look(hand)                    # 평소 Edge 로그인이 포트 창의 메일을 끊고 입구가 다시 못 세웠을 수 있다
    slot["tries"].append({"at": st.stamp(at), "session": evidence})
    if evidence == LIVE:
        slot["launched"] = launch(setting, hand, folder, at, t, missed(day, times, at, bool(setting.get("login")), setting=setting))
        got = slot["launched"]
        if got.get("error"):
            return "\n".join([*lines, f"[보고 예약 — {t} 보고를 띄우지 못했다: {got['error']}]"])
        why = ("사내 세션이 없어 스스로 로그인했고" if was == LOST else "로그인 입구를 먼저 불렀고") if signed and signed["ok"] else "사내 세션이 있어"
        return "\n".join([*lines, f"[보고 예약 — {t} 보고: {why} 일일 보고를 띄웠다 · 출력 {got['log']}]"])
    tried = f" · 스스로 로그인이 안 섰다({signed['said']})" if signed else ""
    later = " · 뒤 시각은 스스로 로그인하지 않는다" if order and setting.get("login") else ""
    return "\n".join([*lines, f"[보고 예약 — {t} 보고: {MISS_WORDS[evidence]} 못 띄웠다{tried}{later} · {end_words(end, at)} 까지 사내 세션이 서는 "
                              "첫 판에 띄운다]"])


# ── 건너뛴 시각 ──────────────────────────────────────────────────────────────

def skip_why(slot: dict[str, Any], order: int, login: bool) -> str:
    """끝난 칸을 왜 건너뛰었나의 한 구절."""
    tries = slot.get("tries") or []
    if not tries:
        return "그 사이 스캔 판이 안 돌아(PC 꺼짐 · 로그온 전 · 작업이 꺼짐)"
    if all(x.get("session") == ERROR for x in tries):
        return "회사 메일 손이 사내 세션을 못 살펴봐"
    if order and login:
        return "사내 세션이 없어(뒤 시각은 스스로 로그인하지 않는다)"
    return "사내 세션이 없어"


def before_set(end: datetime, setting: dict[str, Any] | None) -> bool:
    """그 칸이 시각표를 걸기 전에 이미 끝났나 — 그런 칸은 건너뛴 보고가 아니다(그날은 안 뜨고 다음 날부터 뜬다)."""
    set_at = st.parse((setting or {}).get("set"))
    return set_at is not None and end <= set_at


def missed(day: dict[str, Any], times: list[str], at: datetime, login: bool = False, now: datetime | None = None,
           setting: dict[str, Any] | None = None) -> list[str]:
    """`at` 의 날 칸 가운데 지금(`now` · 없으면 `at`) 앞에 보고 없이 끝난 것 — 「HH:MM 보고는 … 건너뛰었다」 줄. 지난날 것(`before`)이 앞에 선다.
    시각표를 걸기 전에 이미 끝난 칸은 안 센다."""
    out, seen = [], False                   # 마지막 보고 뒤에 건너뛴 시각만 — 그 앞의 것은 그 보고가 이미 말했다
    for i, (t, _, _, end) in enumerate(windows(times, at)):
        if end > (now or at):
            break
        slot = (day.get("slots") or {}).get(t) or {}
        if not slot.get("tries") and before_set(end, setting):
            continue
        if slot.get("launched") or reports(day, times, i, at):
            out, seen = [], True
        else:
            out.append(f"{t} 보고는 {skip_why(slot, i, login)} 건너뛰었다")
    return out if seen else [*(day.get("before") or []), *out]


def skipped_words(day: dict[str, Any], times: list[str], login: bool = False, setting: dict[str, Any] | None = None) -> list[str]:
    """지난날의 그날 칸에서 보고 없이 끝난 시각 — 새 날의 첫 보고와 status 가 말한다. 그날 끝을 그날 23:59 로 잰다."""
    try:
        date = datetime.strptime(str(day.get("date")), "%Y-%m-%d")
    except ValueError:
        return []
    noon = on_day("12:00", date.replace(tzinfo=st.KST))
    then = on_day("00:00", noon) + timedelta(days=1)       # 그날이 다 끝난 때 — 자정까지 기다린 칸도 끝났다
    when = f"{date.month}/{date.day}"
    return [f"{when} {line}" for line in missed({**day, "before": []}, times, noon, login, then, setting)]


def edge_listening() -> bool:
    """이 PC 의 로그인 Edge 디버깅 포트가 받나 — 안 받으면 보고 창을 묻는 손을 안 띄운다(판마다 프로세스 하나를 아낀다)."""
    port = os.environ.get(C.EDGE_PORT_ENV, "").split(",")[0].strip()
    port = int(port) if port.isdigit() and 0 < int(port) < 65536 else C.EDGE_PORT_DEFAULT
    try:
        with socket.create_connection((C.EDGE_HOST, port), timeout=C.EDGE_PROBE_S):
            return True
    except OSError:
        return False


# ── 보고 창에서 고르신 시각 ─────────────────────────────────────────────────

def window_times(folder: pathlib.Path) -> str:
    """보고 창에서 고르신 보고 시각을 받아 건다 — 보고가 걸려 있을 때만, 거는 명령과 같은 자(`times_given` · `no_room`)로 재고, 받았나와
    까닭을 그 창에 돌려 적는다. 창은 보고 창 손이 이 PC 의 디버깅 포트로 읽는다 — 열린 보고 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다.
    창에서 받는 것은 시각뿐이다 — 스스로 로그인 · 띄울 claude 는 걸어 둔 그대로다. 내는 것 — 판 끝에 찍을 한 줄(할 말이 없으면 "")."""
    setting, _ = load(folder)
    ticks = SKILLS_ROOT / C.BRIEF_SKILL / pathlib.Path(*C.BRIEF_TICKS)
    if setting is None or not ticks.is_file() or not edge_listening():
        return ""
    old = setting["times"]
    picked = WINDOW_TIMES.search(ask_window(ticks, ["--times"]))
    if not picked:
        return ""
    chosen_at, set_at = st.parse(picked.group(3).replace("Z", "+00:00")), st.parse(setting.get("set"))
    times, bad = times_given(picked.group(1).split())
    base, _ = times_given(picked.group(2).split()) if picked.group(2) != "-" else (old, "")
    if chosen_at is None or (set_at is not None and chosen_at <= set_at):
        said = f"창에서 고르신 뒤에 대화에서 시각을 바꾸셔서 창에서 고르신 것은 걸지 않았습니다. {in_force(setting)}"   # 나중의 말씀이 이긴다
        refused = True
    elif bad:
        said, refused = f"{bad}. {in_force(setting)}", True
    else:
        said, refused = apply_window(folder, setting, sorted(set(times) - set(base)), sorted(set(base) - set(times)))
    ask_window(ticks, ["--times-done", picked.group(3), "--said", said[:SAID_CHARS], *(["--refused"] if refused else [])])
    return f"[보고 예약 — 보고 창에서 고르신 시각: {said}]"


def apply_window(folder: pathlib.Path, setting: dict[str, Any], added: list[str], removed: list[str]) -> tuple[str, bool]:
    """창에서 더하고 빼신 것을 지금 걸린 시각표 위에 건다 — 창이 보여 드리지 않은 시각은 안 뺀다. 틈을 모자라게 하는 더하신 시각은 하나씩
    빼 보고(붙은 둘이 다 새것이면 늦은 쪽), 남은 것을 건다. 내는 것 — (창에 적을 말, 걸지 않은 것이 있나). 말은 걸지 않은 시각을 다 까닭과
    함께, 건 것을 사실대로 댄다."""
    old = setting["times"]
    new = sorted((set(old) - set(removed)) | set(added))
    fresh, dropped = set(added) - set(old), []
    while True:
        tight = squeezed(new)
        if not tight:
            break
        t, near, room = tight[0]
        if near:
            cut = near if near in fresh else t if t in fresh else None
            why = f"{t if cut == near else near} 보고와 {room}분밖에 안 떨어져 있습니다"
        else:
            cut, why = (t if t in fresh else None), f"그날이 끝나기까지 {room}분뿐입니다"
        if cut is None:                      # 더하신 것 말고 다른 데가 틈이 모자라다 — 그대로 둔다
            new = old
            break
        dropped.append((cut, why))
        new = [x for x in new if x != cut]
        fresh.discard(cut)
    if new != old:
        save(folder, new, pathlib.Path(setting["claude"]), bool(setting.get("login")))
    now, _ = load(folder)
    taken = [t for t in added if t in (now or {}).get("times", [])]
    gone = [t for t in removed if t not in (now or {}).get("times", [])]
    parts = []
    if dropped:
        latest = (datetime(2000, 1, 2) - timedelta(minutes=C.BRIEF_ROOM_MIN)).strftime("%H:%M")
        parts.append("걸지 않은 시각: " + " · ".join(f"{t}({why})" for t, why in dropped)
                     + f" — 보고 시각끼리는 {C.BRIEF_ROOM_MIN}분 넘게 띄우고, 늦어도 {latest} 전에 두어 주세요")
    if taken or gone:
        parts.append(" · ".join([*(f"{t} 을 더했습니다" for t in taken), *(f"{t} 을 뺐습니다" for t in gone)]))
    if not dropped and new == old and (added or removed):
        parts.append("걸린 시각표를 바꾸지 못했습니다")
    parts.append(in_force(now))
    return ". ".join(parts), bool(dropped)


def tell_window(folder: pathlib.Path) -> str:
    """대화에서 시각표를 바꾼 뒤 열린 보고 창에 바로 알린다 — 일일 보고의 거두는 손(`ticks.py --sync`)으로 이 PC 의 디버깅 포트가 받을 때만.
    창이 없거나 못 닿으면 ""(창은 그 뒤 스캔 판이나 다음 거두기가 알린다)."""
    ticks = SKILLS_ROOT / C.BRIEF_SKILL / pathlib.Path(*C.BRIEF_TICKS)
    if not ticks.is_file() or not edge_listening():
        return ""
    said = ask_window(ticks, ["--sync"]).strip().splitlines()
    return said[-1] if said and said[-1].startswith("열린 보고 창에") else ""


def ask_window(ticks: pathlib.Path, args: list[str]) -> str:
    """보고 창 손 한 번 — 표준 출력. 못 돌았으면 빈 글."""
    try:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ticks), "--dir", str(st.home()), *args], capture_output=True,
                              timeout=C.BRIEF_TIMES_TIMEOUT_S, stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                              **H._quiet())
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return done.stdout.decode("utf-8", "replace").replace("\r\n", "\n")


# ── 띄우기 ───────────────────────────────────────────────────────────────────

def places(hand: pathlib.Path | None) -> dict[str, pathlib.Path]:
    """띄운 보고가 쓰는 자리 — 손 · 일정 손 · 스캔의 읽는 명령 · 보고 창 · 업무 파일의 쓰는 손 · 스킬 폴더 · 사용자 폴더. 없는 일정 손은 뺀다."""
    got = {"home": st.home(), "reader": SCRIPT_DIR / "reader.py", "scan_skill": SCRIPT_DIR.parent,
           "brief_skill": SKILLS_ROOT / C.BRIEF_SKILL, "work_skill": SKILLS_ROOT / C.WORK_SKILL,
           "window": SKILLS_ROOT / C.BRIEF_SKILL / pathlib.Path(*C.BRIEF_WINDOW),
           "ticks": SKILLS_ROOT / C.BRIEF_SKILL / pathlib.Path(*C.BRIEF_TICKS),
           "work_writer": SKILLS_ROOT / C.WORK_SKILL / pathlib.Path(*C.WORK_WRITER)}
    if hand is not None:
        got["mail"], got["mail_skill"] = hand, hand.parents[1]
        calendar = hand.parents[2] / C.CALENDAR_SKILL / pathlib.Path(*C.CALENDAR_SCRIPT)
        if calendar.is_file():
            got["calendar"], got["calendar_skill"] = calendar, calendar.parents[1]
    return got


def commands(p: dict[str, pathlib.Path]) -> list[str]:
    """열린 명령 — 권한 규칙의 꼴(끝의 「 *」는 뒤에 인자가 온다). 경로는 「C:/…」 꼴로 따옴표에 싼다 — Git Bash 와 파이썬이 함께 읽는다."""
    def run(script: pathlib.Path) -> str:
        return f'python -X utf8 -I "{script.as_posix()}"'
    got = [f"{run(p['mail'])} {r}" for r in C.MAIL_READS] if "mail" in p else []
    got += [f"{run(p['calendar'])} {r}" for r in C.CALENDAR_READS] if "calendar" in p else []
    got += [f"{run(p['reader'])} *", f'{run(p["window"])} --dir "{p["home"].as_posix()}" *', f"{run(p['work_writer'])} *",
            f'{run(p["ticks"])} --dir "{p["home"].as_posix()}"']
    return got


PROMPT = """사람 없는 예약 실행이다 — 메일함 스캔이 보고 시각 {at} 뒤 판에서 사내 세션이 살아 있는 것을 보고 띄웠다. 지금의 일일 보고를 지어 창으로 띄워 둔다 — 사용자가 오셔서 그 창을 본다.

0. 맨 먼저 열린 명령의 ticks.py 로 보고 창에서 누르신 것을 거둔다 — 업무 파악이 그 절을 읽고, 끝 줄들이 올리지 않을 것과 미룬 것을 댄다. Edge 에 못 닿으면(종료 3) 그대로 넘어간다.
1. 그 뒤 스킬 mailbox-work 의 글 {work_lane} 를 읽고 「두 길」대로 업무 파악을 한다 — {writer} where 가 업무 파일이 있다고 하면 「이어 파악」, 없으면 처음 파악(그 스킬 폴더의 first-understanding.md)이고, 「사람이 없을 때」 절이 이 실행의 경계다. 업무 파일은 {writer} write 로만 쓴다 — 이 실행에는 파일을 쓰는 도구가 없다.
2. 그 뒤 스킬 daily-brief 의 글 {brief_lane} 를 읽고 그 글대로 짓는다 — 「사람 없는 예약 실행」 절이 이 실행의 경계다.
3. 회사 메일 · 일정 손을 부르는 꼴은 그 스킬의 글({skills})이, 메일함 스캔이 쌓은 것을 읽는 꼴은 {scan_skill}/SKILL.md 가 든다.
4. 이 실행에서 열린 명령은 아래 꼴뿐이다 — 경로와 따옴표까지 그대로 쓰고, 「…」 자리에 인자를 둔다. 그 밖의 명령은 막혀 있다.
{commands}
5. 사용자 폴더는 {home} 이다(지금 자리) — 업무 파일 {work_name} 와 지난 보고 글 brief-….md 가 여기 있다.
{missed}"""
MISSED = "6. 건너뛴 보고 — 아래는 보고 없이 지나간 시각이다. 「이 보고가 본 데」에 그대로 적는다(어느 시각을 왜 건너뛰었나):\n{lines}\n"


def plan(setting: dict[str, Any], hand: pathlib.Path | None, folder: pathlib.Path, at: str | None = None,
         skipped: list[str] | None = None) -> tuple[list[str], dict[str, Any], str]:
    """(띄울 명령, `--settings` 로 줄 권한, 표준 입력으로 줄 부탁 글). `at` 은 띄우는 칸의 시각(없으면 첫 시각), `skipped` 는 그 앞에 건너뛴 시각."""
    p = places(hand)
    opened = commands(p)
    settings = {"permissions": {"allow": [f"Bash({c})" for c in opened], "deny": list(C.BRIEF_DENY)}}
    dirs = [p[k] for k in ("brief_skill", "work_skill", "scan_skill", "mail_skill", "calendar_skill") if k in p and p[k].is_dir()]
    cmd = [str(setting["claude"]), "-p", "--settings", str(folder / C.BRIEF_SETTINGS_FILE), "--permission-mode", "dontAsk",
           "--tools", C.CLAUDE_TOOLS, "--strict-mcp-config", "--no-session-persistence",
           *[a for d in dirs for a in ("--add-dir", str(d))]]
    skills = " · ".join(f"{p[k].as_posix()}/SKILL.md" for k in ("mail_skill", "calendar_skill") if k in p)
    prompt = PROMPT.format(at=at or setting["times"][0], brief_lane=(p["brief_skill"] / C.LANE_FILE).as_posix(),
                           skills=skills or "회사 메일 스킬 company-mail", work_lane=(p["work_skill"] / C.LANE_FILE).as_posix(),
                           writer=pathlib.Path(*C.WORK_WRITER).name, work_name=C.WORK_FILE,
                           scan_skill=p["scan_skill"].as_posix(), home=p["home"].as_posix(),
                           commands="\n".join(f"   {c.replace(' *', ' …')}" for c in opened),
                           missed=MISSED.format(lines="\n".join(f"   {x}" for x in skipped)) if skipped else "")
    return cmd, settings, prompt


def _detached() -> dict[str, Any]:
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def launch(setting: dict[str, Any], hand: pathlib.Path | None, folder: pathlib.Path, at: datetime, slot: str | None = None,
           skipped: list[str] | None = None) -> dict[str, Any]:
    """권한 · 부탁 글을 사용자 폴더에 지어 claude 를 띄우고 기다리지 않는다(출력은 `BRIEF_LOG_FILE`). 내는 것 — {at, pid, log} 이나 {at, error}."""
    cmd, settings, prompt = plan(setting, hand, folder, slot, skipped)
    st.write_json(folder / C.BRIEF_SETTINGS_FILE, settings)
    (folder / C.BRIEF_PROMPT_FILE).write_text(prompt, encoding="utf-8")
    log = folder / C.BRIEF_LOG_FILE
    env = {k: v for k, v in os.environ.items() if k not in C.NESTED_ENV}
    try:
        with (folder / C.BRIEF_PROMPT_FILE).open("rb") as given, log.open("wb") as out:
            proc = subprocess.Popen(cmd, cwd=str(st.home()), stdin=given, stdout=out, stderr=subprocess.STDOUT, env=env, close_fds=True,
                                    **_detached())
    except OSError as exc:
        return {"at": st.stamp(at), "error": f"{type(exc).__name__}: {exc}"}
    st.write_json(folder / C.BRIEF_LOCK_FILE, {"started": st.stamp(at), "pid": proc.pid})
    return {"at": st.stamp(at), "pid": proc.pid, "log": str(log)}


# ── 보이기 ───────────────────────────────────────────────────────────────────

def last_line(log: pathlib.Path) -> str:
    """띄운 보고의 출력에서 끝 줄 — 비었으면 "". `claude -p` 는 다 끝난 뒤에 답을 내므로, 출력이 섰으면 그 실행은 끝났다."""
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return lines[-1][:LOG_TAIL_CHARS] if lines else ""


TRY_WORDS = {LOST: "세션 없음", ERROR: "손이 답을 못 냄"}


def looked(tries: list[dict[str, Any]]) -> str:
    """그 칸에서 살펴본 것의 한 구절 — 처음 · 마지막 때와 수, 답마다의 수(손 오류를 「세션 없음」에 섞지 않는다)."""
    counts = " · ".join(f"{word} {sum(t.get('session') == key for t in tries)}"
                        for key, word in TRY_WORDS.items() if any(t.get("session") == key for t in tries))
    return f"{hhmm(tries[0]['at'])}부터 {hhmm(tries[-1]['at'])}까지 {len(tries)}번 살펴봤다({counts})"
MISS_WORDS = {LOST: "사내 세션이 없어", ERROR: "손이 사내 세션을 못 살펴봐"}   # 판 끝 한 줄 — 손 오류를 「세션 없음」으로 말하지 않는다


def slot_line(day: dict[str, Any], slot: dict[str, Any], order: int, t: str, start: datetime, end: datetime, setting: dict[str, Any],
              folder: pathlib.Path, at: datetime, task: bool | None = None) -> str:
    """status 의 한 시각 — 섰다 · 띄웠다 · 도는 중 · 아직 · 기다린다 · 건너뛰었다와 다음 걸음."""
    tries, launched, made = slot.get("tries") or [], slot.get("launched"), reports(day, setting["times"], order, at)
    until = end_words(end, start)
    if made:
        if launched and not launched.get("error"):
            return f"보고 글이 섰다 — {made[-1].name}(스캔이 {hhmm(launched['at'])}에 띄웠다)"
        written = made[-1].stem[-4:-2] + ":" + made[-1].stem[-2:]
        if on_day(written, start) < start:
            return f"{written}에 지은 보고 글({made[-1].name})이 이 시각의 보고를 대신한다 — {t}에는 안 띄운다"
        return f"보고 글이 섰다 — {made[-1].name}"
    if launched and launched.get("error"):
        return f"{hhmm(launched['at'])}에 띄우지 못했다 — {launched['error']}. 다음: 대화에서 「보고해 줘」 하신다"
    if launched:
        tail = last_line(pathlib.Path(launched.get("log") or ""))
        if lock_held(folder, at) and not tail:
            return f"{hhmm(launched['at'])}에 띄웠다 — 보고를 짓는 중이다(출력 {launched.get('log')})"
        return (f"{hhmm(launched['at'])}에 띄웠는데 보고 글이 안 섰다 — 출력 {launched.get('log')}" + (f" 의 끝 줄: {tail}" if tail else " 이 비었다")
                + ". 다음: 대화에서 「보고해 줘」 하신다")
    if task is False and at < end:
        return "메일함 스캔이 작업 스케줄러에 안 걸려 있어 이 시각의 보고는 안 뜬다(위 ⚠)"
    if at < start:
        return f"아직 안 됐다 — 그 뒤 {until} 까지 사내 세션이 서는 첫 판에 띄운다"
    if at >= end and not tries and before_set(end, setting):
        return "오늘은 걸기 전에 이미 지난 시각이라 내일부터 뜬다"
    if at >= end:
        why = skip_why(slot, order, bool(setting.get("login")))
        seen = f" — {looked(tries)}" if tries else ""
        return (f"{until} 까지 {why} 보고를 건너뛰었다{seen}(이 시각은 오늘 다시 안 띄운다). 다음: 대화에서 스킬 ep-login 으로 EP 로그인을 하신 뒤 "
                "「보고해 줘」 하신다")
    if lock_held(folder, at):
        return "스캔이 앞서 띄운 보고가 아직 도는 중이다 — 끝나면 이 시각을 살펴본다"
    if tries:
        later = " 뒤 시각이라 스스로 로그인은 안 한다 —" if order and setting.get("login") else ""
        return (f"사내 세션이 없어 아직 못 띄웠다 — {looked(tries)}. {until} 까지 사내 세션이 서는 첫 판에 띄운다 —{later} 대화에서 스킬 ep-login "
                "으로 EP 로그인을 하시거나 다른 사내 앱 스킬이 세션을 새로 받으면 그 뒤 첫 판이다")
    return f"{t} 이 지났다 — 다음 판에 사내 세션을 살펴보고 띄운다({until} 까지)"


def describe(state: dict[str, Any] | None, folder: pathlib.Path, at: datetime, task: bool | None = None) -> list[str]:
    """status 가 말할 줄 — 걸었나 · 시각마다 오늘 띄웠나 · 안 띄웠으면 왜와 다음 걸음. `task` 가 False 면 스캔 작업이 안 걸렸다(None 은 안 물었다)."""
    setting, problem = load(folder)
    if setting is None:
        if problem:
            return [f"  보고 예약: ⚠ {problem} — 다음: brief --at HH:MM 으로 다시 건다"]
        return [f"  보고 예약: 안 걸었다 — 걸려면 register --brief-at HH:MM [HH:MM …](기본 {C.BRIEF_AT_DEFAULT})"]
    times = setting["times"]
    lines = [f"  보고 예약: {window_words(times)} 일일 보고를 띄운다 · {login_words(bool(setting.get('login')))} · claude {setting['claude']}"]
    if task is False:
        lines.append("  ⚠ 메일함 스캔이 작업 스케줄러에 안 걸려 있어 정한 시각의 보고가 안 뜬다 — 스캔 판이 보고를 띄운다. 다음: register --brief-at "
                     + " ".join(times))
    if not pathlib.Path(setting["claude"]).is_file():
        lines.append("  ⚠ 그 claude 가 없다 — 다음: brief --at HH:MM --claude <claude.exe 의 자리> 로 다시 준다")
    if no_room(times):
        lines.append(f"  ⚠ {no_room(times)} — 이대로는 그 시각에 안 띄운다. 다음: brief --at 으로 시각을 띄어 다시 건다")
    day = day_of(json.loads(json.dumps(state or {})), at, times, keep=False, login=bool(setting.get("login")), setting=setting)
    when = st.seoul(at, "%m/%d")
    for line in day.get("before") or []:
        lines.append(f"  지난날: {line}")
    signed = day.get("login")
    if signed:
        lines.append(f"  오늘({when}): {hhmm(signed['at'])}에 스스로 로그인했다" if signed.get("ok") else
                     f"  오늘({when}): {hhmm(signed['at'])}에 스스로 로그인이 안 섰다 — {signed.get('said')}(오늘은 다시 안 한다)")
    for order, (t, _, start, end) in enumerate(windows(times, at)):
        slot = (day.get("slots") or {}).get(t) or {}
        lines.append(f"  오늘({when}) {t}: {slot_line(day, slot, order, t, start, end, setting, folder, at, task)}")
    return lines
