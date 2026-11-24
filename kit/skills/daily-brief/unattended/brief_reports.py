"""보고가 섰나 · 끝났나 — 칸의 보고 글을 찾고, 그 칸이 띄운 보고가 끝났나와 남긴 글을 가른다. 바깥은 사용자 폴더의 보고 글 · 띄운 보고의
기록(`daily-brief-launch.json`) · 출력(`daily-brief-launch.log`)이다.

    made = reports(folder, day, times, order, at, now)   # 그 칸의 보고 글(대화에서 지은 것도)
    kind, brief = launch_outcome(folder, day, t, now)    # 그 칸이 띄운 보고 — WRITING · EMPTY · LEFT(남긴 글)
"""

from __future__ import annotations

import pathlib
from datetime import datetime, timedelta, timezone
from typing import Any

import unattended_const as C
import unattended_store as st
import clock as tm
from brief_files import BRIEF_PREFIX, TEXT_SUFFIX, made_of
from brief_kinds import EMPTY, LEFT, WRITING
from brief_slots import on_day, seoul_date, windows
from launch_base import process_alive

LOG_TAIL_CHARS = 200                                 # status 가 띄운 보고의 출력에서 옮겨 보이는 끝 줄의 글자 수


def made_between(folder: pathlib.Path, cover: datetime, end: datetime) -> list[pathlib.Path]:
    """사용자 폴더의 그 칸의 날 보고 글 가운데 이름의 때(서울)가 `cover` 부터 `end` 전인 것 — 이름 차례. 이름의 꼴은 이 스킬의 원본
    (`brief_files.made_of` — 지은 때의 PC 시계다. 회사 PC 는 서울 시계라 서울 날짜로 찾는다)이 읽는다."""
    out = []
    for f in sorted(folder.glob(f"{BRIEF_PREFIX}{seoul_date(cover)}-*{TEXT_SUFFIX}")):
        when = made_of(f.name)
        if when is None:
            continue
        made = when.strftime("%H:%M")
        if cover <= on_day(made, cover) < end:
            out.append(f)
    return out


def reports(folder: pathlib.Path, day: dict[str, Any], times: list[str], order: int, at: datetime, now: datetime) -> list[pathlib.Path]:
    """그 칸의 보고 글 — 덮는 첫때부터 끝 전에 이름의 때가 든 글에서 앞 칸이 띄운 보고가 남긴 글(그 띄운 때부터 그 보고가 끝난 때까지)을
    빼고, 이 칸이 띄운 보고가 남긴 글을 더한다. 칸 끝 무렵 띄운 보고는 글을 칸이 끝난 뒤에 쓴다 — 그 글로 다음 칸이 안 띄우면 안 된다.
    끝은 `launched_end` 가 가른다(지금 `now` 까지 돌면 지금까지)."""
    wins = windows(times, at)
    _, cover, _, end = wins[order]
    prev = launched_span(day, wins[order - 1][0], now) if order else None
    own = launched_span(day, wins[order][0], now)
    got = [f for f in made_between(folder, cover, end) if not (prev and f in made_between(folder, *prev))]
    got += [f for f in made_between(folder, *own) if f not in got] if own else []
    return sorted(got, key=lambda f: f.name)


def launched_span(day: dict[str, Any], t: str, now: datetime) -> tuple[datetime, datetime] | None:
    """그 시각 칸이 띄운 보고가 글을 남길 수 있던 때의 범위 — 띄운 때(분까지 — 글 이름의 때는 분까지다)부터 그 보고가 끝난 때(돌면 지금)까지.
    못 띄웠거나 안 띄웠거나 띄운 때를 못 읽으면 None."""
    got = ((day.get("slots") or {}).get(t) or {}).get("launched") or {}
    since = tm.parse(got.get("at")) if not got.get("error") else None
    if since is None:
        return None
    return since.replace(second=0, microsecond=0), launched_end(day, t, now) or now


def lock_held(folder: pathlib.Path, at: datetime) -> dict[str, Any] | None:
    """시계가 띄운 보고가 도는 중이면 그 기록 — 기록에 적은 띄운 때 · 프로세스 번호와 출력(`LAUNCH_LOG_FILE`)으로 `run_end` 가 「안 끝났다」를
    내면. 못 읽은 잠금은 그 파일의 고친 때를 띄운 때로 잰다(`st.held_since`) — 프로세스를 모르니 출력이 빈 동안은 돈다고 본다(못 읽었다고
    안 도는 것으로 읽으면 보고를 하나 더 띄운다). 어느 쪽이든 띄운 때에서 `BRIEF_LOCK_STALE_S` 를 넘지 않는다."""
    held = st.held_since(folder / C.LAUNCH_FILE)
    since = tm.parse(held.get("started")) if held else None
    if since is None:
        return None
    return held if run_end(since, held.get("pid"), held.get("born"), folder / C.LAUNCH_LOG_FILE, at, None) is None else None


def last_line(log: pathlib.Path) -> str:
    """띄운 보고의 출력에서 끝 줄 — 비었으면 "". `claude -p` 는 다 끝난 뒤에 답을 내므로, 출력이 섰으면 그 실행은 끝났다."""
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return lines[-1][:LOG_TAIL_CHARS] if lines else ""


def run_end(started: datetime, pid: Any, born: Any, log: pathlib.Path, now: datetime, later: datetime | None) -> datetime | None:
    """스캔이 띄운 보고 한 판이 끝난 때 — 도는 중이면 None. 뒤 칸이 다시 띄웠으면(`later`) 이 보고는 그 앞에 끝났다(출력 파일은 이제 뒤 보고의
    것이다). 아니면 띄운 프로세스(`pid` · 뜬 때 `born` — 번호를 남이 받았으면 끝났다)가 끝났나로 가르고, 끝났으면 출력 파일을 마지막으로 쓴 때가 끝이다(`claude -p` 는 다 끝난 뒤에 답을
    낸다) — 출력 없이 죽은 보고는 띄운 때가 끝이다. 프로세스 번호가 없으면(옛 기록 · 못 읽은 잠금) 출력 파일에 글이 섰나로 가른다. 어느 쪽이든
    띄운 때에서 `BRIEF_LOCK_STALE_S` 를 넘지 않는다 — 그 뒤로는 끝난 것이다."""
    cap = started + timedelta(seconds=C.BRIEF_LOCK_STALE_S)
    if later is not None:
        return min(cap, later)
    alive = process_alive(pid, born)
    if now < cap and (alive or (alive is None and not last_line(log))):
        return None
    try:
        if not log.name:                     # 출력 자리가 없는 기록 — 빈 경로는 지금 자리(.)를 가리켜 엉뚱한 때를 읽는다
            raise FileNotFoundError(log)
        written = datetime.fromtimestamp(log.stat().st_mtime, timezone.utc) + timedelta(minutes=1)   # 글 이름의 때는 분까지다
    except OSError:
        written = started
    return min(cap, max(started, written))


def launched_end(day: dict[str, Any], t: str, now: datetime) -> datetime | None:
    """그날 `t` 칸이 띄운 보고가 끝난 때(`run_end`) — 뒤 칸이 다시 띄운 때를 함께 댄다. 도는 중이면 None. 그 칸이 띄운 때를 읽을 수 있어야 한다."""
    launched = day["slots"][t]["launched"]
    since = tm.parse(launched.get("at"))
    later = next((at for at, _ in launches(day) if at > since), None)
    return run_end(since, launched.get("pid"), launched.get("born"), pathlib.Path(launched.get("log") or ""), now, later)


def unattended_brief(folder: pathlib.Path, launched: dict[str, Any], ended: datetime) -> pathlib.Path | None:
    """그 칸이 띄운 보고가 남긴 보고 글 — 띄운 때부터 그 보고가 끝난 때까지 이름의 때가 든 글 가운데 마지막(끝의 절을 더해 다시 지은 글이
    뒤에 선다). 대화에서 그 뒤에 지은 글은 안 든다. 자정 무렵 띄운 보고는 다음 날의 이름으로 글을 남긴다 — 그날 것도 본다. 없으면 None."""
    since = tm.parse(launched.get("at")).replace(second=0, microsecond=0)
    got = made_between(folder, since, ended)
    next_day = on_day("00:00", since) + timedelta(days=1)
    got += made_between(folder, next_day, ended) if ended > next_day else []
    return got[-1] if got else None


def launches(day: dict[str, Any]) -> list[tuple[datetime, str]]:
    """그날 장부에서 띄운 칸들 — (띄운 때, 시각)을 띄운 차례로. 못 띄운 칸은 뺀다."""
    slots = day.get("slots") or {}
    got = [(tm.parse((s.get("launched") or {}).get("at")), t) for t, s in slots.items()
           if isinstance(s, dict) and (s.get("launched") or {}).get("at") and not (s.get("launched") or {}).get("error")]
    return sorted((at, t) for at, t in got if at is not None)


def launch_outcome(folder: pathlib.Path, day: dict[str, Any], t: str, now: datetime) -> tuple[str, pathlib.Path | None]:
    """그날 `t` 칸이 띄운 보고가 지금 어떤가 — (WRITING, None) 아직 돈다 · (EMPTY, None) 글 없이 끝났다 · (LEFT, 글) 끝나 글을 남겼다. 끝은
    `launched_end` 가 띄운 프로세스와 출력으로 가르고, 뒤 칸이 다시 띄웠으면 이 보고는 그 앞에 끝났다. 그 칸이 띄운 기록이 있어야 한다 — 띄운 때를 못 읽으면 WRITING."""
    launched = day["slots"][t]["launched"]
    if tm.parse(launched.get("at")) is None:
        return WRITING, None                 # 띄운 때를 못 읽은 기록 — 끝을 모르니 도는 것으로 둔다(새로 안 띄우고 건너뛴 칸으로 안 센다)
    ended = launched_end(day, t, now)
    if ended is None:
        return WRITING, None
    brief = unattended_brief(folder, launched, ended)
    return (LEFT, brief) if brief is not None else (EMPTY, None)
