"""보고 시각표와 그날의 칸 — 시각표 파일(`brief.json`)을 읽고 걸고, 시각마다의 칸 · 그날 띄운 것 · 건너뛴 것을 셈하고, status 가
말할 줄을 짓는다. 띄운 보고가 끝났나와 남긴 글을 가른다. 프로세스를 띄우지 않는다.

    setting, problem = load(folder)              # 안 걸었으면 (None, ""), 못 읽으면 (None, 까닭). 시각표는 setting["times"]
    save(folder, times=["07:30", "13:00"], claude=path, login=False) · clear(folder)
    times, bad = times_given(["07:30", "13:00"]) # 받은 시각들 → 정렬한 시각표 · 꼴이 아니면 까닭
    refused = no_room(times)                     # 기다릴 틈이 모자란 시각이 있으면 거절의 말 — 받으면 ""
    said, refused = take_window_times(folder, setting, picked, seen, at_text)   # 보고 창에서 고르신 시각을 건다(판 · 창 곁의 손이 함께)
    day = day_of(state, at, times)               # 그날의 칸 장부(`state["brief"]`) — current · waiting · spaced · missed 가 그 위에서 셈한다
    ended = run_over(launched, at, later)        # 그 칸이 띄운 보고가 끝났나(도는 중이면 None) — 건너뛴 보고 줄 · 자리 밖에서 보기가 함께 쓴다
    brief = unattended_brief(launched, ended)    # 그 보고가 남긴 글 — 없으면 None
    lines = describe(state, folder, at)          # status 가 말할 줄 — 시각마다
    words = window_words(times)                  # 거는 말 · status 가 함께 쓰는 「언제 띄우나」 한 구절

칸과 그날의 뜻 · 까닭은 `references/DESIGN.md` 「정한 시각의 보고」가 든다.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import scan_const as C
import scan_store as st
from session_login import ERROR, LOST


LOG_TAIL_CHARS = 200                                 # status 가 띄운 보고의 출력에서 옮겨 보이는 끝 줄의 글자 수


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


def read_brief(folder: pathlib.Path) -> dict[str, Any] | None:
    """보고 시각표 파일 그대로 — 없으면 None, 있는데 못 읽으면 `st.Unreadable`. 한 칸만 바꿔 쓰는 쪽은 이것으로 읽어 다른 칸을 옮겨 적는다."""
    return st.read_json(folder / C.BRIEF_FILE)


def load(folder: pathlib.Path) -> tuple[dict[str, Any] | None, str]:
    """(설정, 못 읽은 까닭). 안 걸었으면 (None, ""). 시각 하나(꼴 1)로 걸어 둔 설정도 읽어 `times` 를 채운다. 읽기만 하는 쪽의 답이다 — 쓰는
    쪽은 `read_brief` 의 `st.Unreadable` 로 「못 읽었다」를 가른다."""
    try:
        data = read_brief(folder)
    except st.Unreadable as exc:
        return None, str(exc)
    return setting_of(data)


def setting_of(data: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str]:
    """시각표 파일 그대로(`read_brief`) → (설정, 꼴이 아닌 까닭). 없으면 (None, "")."""
    if data is None:
        return None, ""
    if data.get("format") not in C.BRIEF_FORMATS_READ or not data.get("claude"):
        return None, f"{C.BRIEF_FILE} 의 꼴이 이 스크립트와 다르다"
    raw = data.get("times") if data.get("format") != 1 else [data.get("at")]
    times, bad = times_given([str(x) for x in raw]) if isinstance(raw, list) and all(isinstance(x, str) for x in raw) else ([], "꼴")
    if bad:
        return None, f"{C.BRIEF_FILE} 의 보고 시각이 꼴이 아니다"
    data["times"] = times
    return data, ""


def save(folder: pathlib.Path, times: list[str], claude: pathlib.Path, login: bool = False) -> None:
    """시각표를 건다 — 걸려 있던 자리 밖에서 보기(`away`)는 그대로 실어 둔다(시각을 바꿔도 켜고 끄기는 안 바뀐다). 걸려 있던 파일을 못 읽으면
    `st.Unreadable` 이고 안 쓴다 — 빈 것으로 읽어 쓰면 켜 둔 자리 밖에서 보기가 꺼진다. 글이 깨진 파일은 새 시각표로 고친다(옮길 칸이 없다)."""
    try:
        kept = (read_brief(folder) or {}).get("away")
    except st.Unreadable as exc:
        if not exc.broken:
            raise
        kept = None
    st.write_json(folder / C.BRIEF_FILE, {"format": C.BRIEF_FORMAT, "times": list(times), "claude": str(claude), "login": bool(login),
                                          "set": st.stamp(st.now()), "room_min": C.BRIEF_ROOM_MIN, "wait_min": C.BRIEF_WAIT_MIN,
                                          **({"away": kept} if isinstance(kept, dict) else {})})
    # ↑ 규칙의 수 둘은 보고 창이 더하실 시각을 바로 재는 데 쓴다(일일 보고의 state.py `state_of`) — 원본은 scan_const 한 자리다


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
    """스캔이 띄운 보고가 도는 중이면 그 잠금 — 띄운 때에서 `BRIEF_LOCK_STALE_S` 가 지났으면 끝났거나 멈춘 것이라 None. 못 읽은 잠금은 그
    파일의 고친 때로 잰다(`st.held_since`) — 못 읽었다고 안 도는 것으로 읽으면 보고를 하나 더 띄운다."""
    held = st.held_since(folder / C.BRIEF_LOCK_FILE)
    since = st.parse(held.get("started")) if held else None
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


STILL_ACTIVE = 259                                               # 윈도 GetExitCodeProcess 가 도는 프로세스에 내는 값
QUERY_LIMITED = 0x1000                                           # PROCESS_QUERY_LIMITED_INFORMATION — 같은 사용자의 프로세스를 묻는 권한


def process_alive(pid: Any) -> bool | None:
    """그 프로세스가 아직 도나 — 모르면(번호가 없다) None. 끝난 프로세스의 번호를 다른 프로세스가 받았으면 「돈다」로 읽는다 — 그때는 칸의
    시한(`BRIEF_LOCK_STALE_S`)이 끝을 정한다."""
    if not isinstance(pid, int) or pid <= 0:
        return None
    if sys.platform == "win32":
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(QUERY_LIMITED, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)                                          # POSIX 의 0 은 묻기만 한다
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def run_over(launched: dict[str, Any], at: datetime, later: datetime | None) -> datetime | None:
    """그 칸이 띄운 보고가 끝났나 — 끝났으면 그 보고가 글을 남길 수 있던 마지막 때, 도는 중이면 None. 뒤 칸이 다시 띄웠으면(`later`) 이 보고는
    그 앞에 끝났다(출력 파일은 이제 뒤 보고의 것이다). 아니면 띄운 프로세스가 끝났나로 가르고, 끝났으면 출력 파일을 마지막으로 쓴 때가 끝이다
    (`claude -p` 는 다 끝난 뒤에 답을 낸다) — 출력 없이 죽은 보고는 띄운 때가 끝이라 그 뒤 대화에서 지은 글을 안 잡는다. 프로세스 번호가 없는
    옛 기록은 출력 파일에 글이 섰나로 가른다. 어느 쪽이든 띄운 때에서 `BRIEF_LOCK_STALE_S` 를 넘지 않는다."""
    since = st.parse(launched.get("at"))
    cap = since + timedelta(seconds=C.BRIEF_LOCK_STALE_S)
    if later is not None:
        return min(cap, later)
    log = pathlib.Path(launched.get("log") or "")
    alive = process_alive(launched.get("pid"))
    if at < cap and (alive or (alive is None and not last_line(log))):
        return None
    try:
        written = datetime.fromtimestamp(log.stat().st_mtime, timezone.utc) + timedelta(minutes=1)   # 글 이름의 때는 분까지다
    except OSError:
        written = since
    return min(cap, max(since, written))


def unattended_brief(launched: dict[str, Any], ended: datetime) -> pathlib.Path | None:
    """그 칸이 띄운 보고가 남긴 보고 글 — 띄운 때부터 그 보고가 끝난 때까지 이름의 때가 든 글 가운데 마지막(끝의 절을 더해 다시 지은 글이
    뒤에 선다). 대화에서 그 뒤에 지은 글은 안 든다. 자정 무렵 띄운 보고는 다음 날의 이름으로 글을 남긴다 — 그날 것도 본다. 없으면 None."""
    since = st.parse(launched.get("at")).replace(second=0, microsecond=0)
    got = made_between(since, ended)
    next_day = on_day("00:00", since) + timedelta(days=1)
    got += made_between(next_day, ended) if ended > next_day else []
    return got[-1] if got else None


def came_out_empty(launched: dict[str, Any], made: list[pathlib.Path], now: datetime, later: datetime | None) -> bool:
    """그 칸이 띄운 보고가 글 없이 끝났나 — 그 칸의 보고 글(`made` · 대화에서 지은 것도)이 없고, 띄운 판이 끝났는데(`run_over` · 뒤 칸이 다시
    띄운 때 `later`) 그 판이 남긴 글(`unattended_brief` — 자정 넘어 남긴 글도)이 없다. 도는 중이면 거짓이다 — 아직 짓는 보고를 못
    지었다고 말하지 않는다. 자리 밖에서 보기가 보낼 글을 고르는 것과 같은 셈이다."""
    if made:
        return False
    ended = run_over(launched, now, later)
    return ended is not None and unattended_brief(launched, ended) is None


def missed(day: dict[str, Any], times: list[str], at: datetime, login: bool = False, now: datetime | None = None,
           setting: dict[str, Any] | None = None) -> list[str]:
    """`at` 의 날 칸 가운데 지금(`now` · 없으면 `at`) 앞에 보고 없이 끝난 것 — 「HH:MM 보고는 … 건너뛰었다」 줄, 띄웠는데 글 없이 끝났거나 못
    띄운 칸은 그렇다는 줄(그 칸의 보고는 아무것도 말하지 않았으니 앞 줄들도 걷지 않는다). 지난날 것(`before`)이 앞에 선다.
    시각표를 걸기 전에 이미 끝난 칸은 안 센다. 끝난 칸의 메일(자리 밖에서 보기)이 못 갔으면 그 줄이 뒤에 선다 — 그 끝을 적은 뒤 띄운
    보고가 아직 없는 것만(그 뒤 띄운 보고는 이미 말했다)."""
    out, seen = [], False                   # 마지막 보고 뒤에 건너뛴 시각만 — 그 앞의 것은 그 보고가 이미 말했다
    mails, last = [], None                  # 못 간 메일의 (끝을 적은 때, 줄) · 그 앞 칸들 가운데 가장 늦게 띄워 글이 선 때
    slots = day.get("slots") or {}
    started = sorted(st.parse(s["launched"]["at"]) for s in slots.values()
                     if isinstance(s, dict) and isinstance(s.get("launched"), dict) and s["launched"].get("at") and not s["launched"].get("error"))
    for i, (t, _, _, end) in enumerate(windows(times, at)):
        if end > (now or at):
            break
        slot = slots.get(t) or {}
        got = slot.get("launched") or {}
        launched = st.parse(got.get("at")) if not got.get("error") else None
        made = reports(day, times, i, at)
        later = next((s for s in started if launched and s > launched), None)
        empty = launched is not None and came_out_empty(got, made, now or at, later)
        if launched and not empty and (last is None or launched > last):
            last = launched
        when, word = mail_missed(slot, t, end, now or at)
        if word:
            mails.append((when, word))
        if not slot.get("tries") and before_set(end, setting):
            continue
        if empty:
            out.append(f"{t} 보고는 {hhmm(launched)}에 띄웠는데 보고 글이 안 섰다(띄운 판이 글을 못 남기고 끝났다)")
        elif got.get("error") and not made:
            out.append(f"{t} 보고는 {hhmm(got.get('at'))}에 띄우지 못했다 — {got['error']}")
        elif got or made:
            out, seen = [], True
        else:
            out.append(f"{t} 보고는 {skip_why(slot, i, login)} 건너뛰었다")
    told = [word for when, word in mails if last is None or when is None or when > last]
    return (out if seen else [*(day.get("before") or []), *out]) + told


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


def take_window_times(folder: pathlib.Path, setting: dict[str, Any], picked: list[str], seen: list[str], at_text: str) -> tuple[str, bool]:
    """보고 창에서 고르신 보고 시각을 거는 명령과 같은 자(`times_given` · `no_room`)로 재고 건다 — 스캔 판과 창 곁의 손이 함께 쓰는 한 자리.
    `seen` 은 그때 창이 보이던 시각(비면 지금 걸린 것)이고, 거기서 더하고 빼신 것만 지금 걸린 시각표 위에 얹는다. 나중의 말씀이 이긴다 —
    고른 때(`at_text`)가 걸어 둔 때보다 앞이면 안 건다. 두 길이 같은 고름을 함께 받으면 둘째는 첫 끝을 다시 낸다(건 뒤라 「앞서 고른 것」으로
    잘못 읽지 않게). 내는 것 — (그 창에 적을 말, 걸지 않은 것이 있나)."""
    old = setting["times"]
    before = setting.get("picked")
    if isinstance(before, dict) and before.get("at") == at_text:
        return str(before.get("said") or in_force(setting)), bool(before.get("refused"))
    chosen_at, set_at = st.parse(at_text.replace("Z", "+00:00")), st.parse(setting.get("set"))
    times, bad = times_given(picked)
    base, _ = times_given(seen) if seen else (old, "")
    if chosen_at is None or (set_at is not None and chosen_at <= set_at):
        said = f"창에서 고르신 뒤에 대화에서 시각을 바꾸셔서 창에서 고르신 것은 걸지 않았습니다. {in_force(setting)}"   # 나중의 말씀이 이긴다
        refused = True
    elif bad:
        said, refused = f"{bad}. {in_force(setting)}", True
    else:
        try:
            said, refused = apply_window(folder, setting, sorted(set(times) - set(base)), sorted(set(base) - set(times)))
        except st.Unreadable as exc:
            return f"걸지 않았습니다 — 보고 시각표를 그 순간 못 읽었습니다({exc}). 다시 골라 주세요. {in_force(setting)}", True
        try:          # 받은 고름의 표지 — 못 읽은 파일 위에는 안 쓴다. 시각표는 위에서 이미 걸렸다 — 표지가 빠지면 같은 고름을 함께 받은
                      # 다른 길이 「대화에서 바꾸셨다」로 거절할 수 있지만, 빈 것 위에 표지를 써 시각표를 지우는 것보다 낫다
            current = read_brief(folder)
            if current is not None:       # 그 사이 보고가 내려졌으면 표지만 든 파일을 세우지 않는다
                st.write_json(folder / C.BRIEF_FILE, {**current, "picked": {"at": at_text, "said": said, "refused": refused}})
        except st.Unreadable:
            pass
    return said, refused


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


def away_of(setting: dict[str, Any] | None) -> dict[str, Any]:
    """걸어 둔 자리 밖에서 보기 — {on, address, chosen, set}. 안 켰으면 빈 것."""
    away = (setting or {}).get("away")
    return away if isinstance(away, dict) else {}


def next_slot(setting: dict[str, Any], folder: pathlib.Path, at: datetime) -> str:
    """다음 사람 없는 보고의 시각 — 오늘 아직 안 띄운 칸 가운데 끝나지 않은 첫 것, 없으면 「내일 HH:MM」."""
    try:
        state, _ = st.load_state(folder)
    except st.Unreadable:
        state = None                     # 말 한 구절에만 쓴다 — 그날 칸을 모르면 오늘 남은 첫 칸을 댄다
    times = setting["times"]
    day = day_of(json.loads(json.dumps(state or {})), at, times, keep=False, login=bool(setting.get("login")), setting=setting)
    for order, (t, _, _, end) in enumerate(windows(times, at)):
        if at < end and not ((day.get("slots") or {}).get(t) or {}).get("launched") and not reports(day, times, order, at):
            return t
    return f"내일 {times[0]}"


def mail_words(mail: dict[str, Any], end: datetime, at: datetime) -> str:
    """칸의 메일 기록의 한 구절 — 판 끝 · status 가 같은 말을 쓴다."""
    state, why = mail.get("state"), mail.get("why") or ""
    if state == C.AWAY_SENT:
        return f"본인 메일로 보냈다({hhmm(mail.get('at'))})"
    if state == C.AWAY_RETRY and at < end:
        return f"메일을 아직 못 보냈다 — {why}. {end_words(end, at)} 까지 판마다 다시 보낸다"
    if state == C.AWAY_RETRY:
        return f"메일로 못 보냈다 — {why}({mail.get('tries') or 1}번 해 봤다)"
    return f"메일을 보냈는지 확인하지 못했다 — {why}. 다시 보내지 않는다 — 받은편지함에서 보시고, 없으면 PC 의 보고 창에서 보신다"


def mail_missed(slot: dict[str, Any], t: str, end: datetime, now: datetime) -> tuple[datetime | None, str]:
    """끝난 칸의 메일이 못 갔으면 (그 끝을 적은 때, 「HH:MM 보고는 메일로 …」 줄) — 갔거나 기록이 없으면 (None, "")."""
    mail = slot.get("mail") or {}
    state, why = mail.get("state"), mail.get("why") or ""
    if state == C.AWAY_RETRY and now >= end:
        return st.parse(mail.get("at")), f"{t} 보고는 메일로 못 보냈다 — {why}"
    if state == C.AWAY_UNSURE:
        return st.parse(mail.get("at")), f"{t} 보고는 메일로 보냈는지 확인하지 못했다 — {why}"
    return None, ""


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
    away = away_of(setting)
    lines.append(f"  자리 밖에서 보기: 켰다({st.seoul(st.parse(away.get('chosen')), '%m/%d %H:%M')}) — 사람 없이 띄운 보고를 칸마다 한 통 본인 주소"
                 f"({away.get('address')})로 보낸다" if away.get("on") else "  자리 밖에서 보기: 꺼져 있다 — 사람 없는 보고는 아무것도 안 보낸다")
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
        mail = f" · {mail_words(slot['mail'], end, at)}" if isinstance(slot.get("mail"), dict) else ""
        lines.append(f"  오늘({when}) {t}: {slot_line(day, slot, order, t, start, end, setting, folder, at, task)}{mail}")
    return lines
