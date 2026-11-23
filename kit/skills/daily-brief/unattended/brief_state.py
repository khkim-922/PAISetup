"""칸의 상태 — 그날 칸 하나가 지금 어느 상태인가를 한 번 셈한다. 띄울 때인가(판 끝) · 건너뛴 칸(부탁 글 · 지난날) · status 의 한 시각이
다 이 셈 위에서 가른다. 사람 말은 짓지 않는다 — 상태의 이름과 그릇은 `brief_kinds` 가 든다.

    v = slot_state(day, times, order, ref, now, setting, folder)   # Slot — v.state 는 brief_kinds 의 열하나 가운데 하나
    told = untold(folder, day, times, at, now, setting)            # 마지막 보고 뒤 아직 말하지 않은 칸 · 못 간 메일
    spaced(slot, at)                                               # 손에 다시 물어도 되나(살펴보기 사이의 틈)
    after = looked_after(slot, start, since)                       # 그 칸의 세션 답이 새것이려면 그 뒤에 섰어야 하는 때
    due = login_due(day, slot, order, setting, evidence)           # 스스로 로그인의 입구를 부를 판인가 — LOGIN_DAILY · LOGIN_SLOT · ""
    logins = day_logins(day)                                       # 그날 입구를 부른 끝들 — (칸의 시각 · 그날의 한 번이면 "", 끝)
    login = slot_login(day, slot, order)                           # 그 칸의 띄우기 앞에 부른 입구의 끝 — 없으면 {}
"""

from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Any

import unattended_const as C
import clock as tm
from brief_kinds import (AHEAD, DUE, EMPTY, FAILED, HAND_ERROR, LEFT, LOGIN_DAILY, LOGIN_SLOT, LOGIN_UNSET, MADE, MAIL_FAILED, MAIL_NONE,
                         MAIL_RETRYING, MAIL_SENT, MAIL_UNSURE, MADE_EARLY, MADE_IN, MADE_SCAN, NO_RUN, NO_SESSION, PAST_SET, RUNNING, SETTLED,
                         SKIPPED, UNSCHEDULED, WAITING, WRITING, Slot, Told)
from brief_reports import last_line, launch_outcome, lock_held, reports
from brief_slots import minute, on_day, windows


def before_set(end: datetime, setting: dict[str, Any] | None) -> bool:
    """그 칸이 시각표를 걸기 전에 이미 끝났나 — 그런 칸은 건너뛴 보고가 아니다(그날은 안 뜨고 다음 날부터 뜬다)."""
    set_at = tm.parse((setting or {}).get("set"))
    return set_at is not None and end <= set_at


def slot_state(day: dict[str, Any], times: list[str], order: int, ref: datetime, now: datetime, setting: dict[str, Any] | None,
               folder: pathlib.Path, running: bool = True) -> Slot:
    """그날(`ref` 의 날) `order` 째 칸의 상태를 지금(`now`) 한 번 셈한다. 띄운 칸은 그 보고가 돌거나 끝났나를 `launch_outcome` 으로 가르고
    글 없이 끝났으면 출력의 끝 줄을 싣는다. `folder` 는 보고 글 · 띄운 기록이 선 사용자 폴더 — 끝난 칸만 보는 쪽은 `running` 을 거짓으로
    주어 앞 칸이 띄운 보고가 도나를 안 본다. 내는 것 — `Slot`."""
    t, _, start, end = windows(times, ref)[order]
    slot = (day.get("slots") or {}).get(t) or {}
    made = reports(folder, day, times, order, ref, now)
    launched = slot.get("launched")
    unset = not slot.get("tries") and before_set(end, setting)
    tail, how, early = "", "", ""
    if made:
        state = MADE
        how, early = made_how(made[-1], launched, start)
    elif launched and launched.get("error"):
        state = FAILED
    elif launched:
        state, _ = launch_outcome(folder, day, t, now)
        tail = last_line(pathlib.Path(launched.get("log") or "")) if state in (EMPTY, LEFT) else ""
    elif now < start:
        state = AHEAD
    elif now >= end:
        state = PAST_SET if unset else SKIPPED
    elif running and lock_held(folder, now):
        state = RUNNING
    elif slot.get("tries"):
        state = WAITING
    else:
        state = DUE
    return Slot(t, order, start, end, slot, made, state, unset, tail, how, early)


def made_how(brief: pathlib.Path, launched: dict[str, Any] | None, start: datetime) -> tuple[str, str]:
    """그 칸의 보고 글이 어떻게 섰나 — (MADE_SCAN, "") 스캔이 띄웠다 · (MADE_EARLY, 「HH:MM」) 칸이 열리기 전에 지은 글이 대신한다 ·
    (MADE_IN, "") 칸 안에서 지었다. 글 이름의 끝 넉 자가 지은 때다."""
    if launched and not launched.get("error"):
        return MADE_SCAN, ""
    written = brief.stem[-4:-2] + ":" + brief.stem[-2:]
    return (MADE_EARLY, written) if on_day(written, start) < start else (MADE_IN, "")


def status_state(v: Slot, task: bool | None, at: datetime) -> str:
    """status 가 말할 칸의 상태 — 시계 작업이 안 걸렸고(`task` 가 False) 아직 일이 안 난 칸이 안 끝났으면 UNSCHEDULED, 아니면 칸의 상태."""
    return UNSCHEDULED if task is False and at < v.end and v.state not in SETTLED else v.state


def slot_mail(v: Slot, at: datetime) -> tuple[str, dict[str, Any]] | None:
    """칸의 메일 기록과 그 상태 — 기록이 없으면 None."""
    mail = v.slot.get("mail")
    return (mail_status(mail, v.end, at), mail) if isinstance(mail, dict) else None


def skip_cause(slot: dict[str, Any]) -> str:
    """끝난 칸을 왜 건너뛰었나 — 판이 안 돌았다 · 손이 세션을 못 살펴봤다 · 세션이 없고 그 칸의 스스로 로그인도 안 섰다 · 세션이 없었다."""
    tries = slot.get("tries") or []
    if not tries:
        return NO_RUN
    if all(x.get("session") == C.SESSION_ERROR for x in tries):
        return HAND_ERROR
    if (slot.get("login") or {}).get("ok") is False:
        return LOGIN_UNSET
    return NO_SESSION


def mail_status(mail: dict[str, Any], end: datetime, now: datetime) -> str:
    """칸의 메일 기록이 지금 어떤가 — 기록 없음 · 보냈다 · 칸이 끝나기 전에 넘기기 전에 진 것(판마다 다시 보낸다) · 칸이 끝나 못 보냈다 ·
    보냈는지 모른다(넘기는 도중 · 뒤에 졌다)."""
    state = mail.get("state")
    if not state:
        return MAIL_NONE
    if state == C.AWAY_SENT:
        return MAIL_SENT
    if state == C.AWAY_RETRY:
        return MAIL_RETRYING if now < end else MAIL_FAILED
    return MAIL_UNSURE


def untold(folder: pathlib.Path, day: dict[str, Any], times: list[str], at: datetime, now: datetime | None = None, setting: dict[str, Any] | None = None) -> Told:
    """`at` 의 날 칸 가운데 지금(`now` · 없으면 `at`) 앞에 끝났는데 보고가 아직 말하지 않은 것 — 마지막으로 보고가 선 칸 뒤의 건너뛴 칸 ·
    글 없이 끝난 칸 · 못 띄운 칸, 그리고 끝을 적은 뒤 띄운 보고가 아직 없는 못 간 메일. 시각표를 걸기 전에 끝난 안 살펴본 칸은 안 센다."""
    till = now or at
    items: list[tuple[Any, ...]] = []
    seen, mails, last = False, [], None      # 마지막 보고 뒤만 · 그 앞 칸들 가운데 가장 늦게 띄워 글 없이 끝나지 않은 때
    for i, (t, _, _, end) in enumerate(windows(times, at)):
        if end > till:
            break
        v = slot_state(day, times, i, at, till, setting, folder, running=False)
        got = v.slot.get("launched") or {}
        launched = tm.parse(got.get("at")) if not got.get("error") else None
        if launched and v.state != EMPTY and (last is None or launched > last):
            last = launched
        mail = v.slot.get("mail") or {}
        status = mail_status(mail, end, till)
        if status in (MAIL_FAILED, MAIL_UNSURE):
            mails.append((tm.parse(mail.get("at")), t, status, mail.get("why") or ""))
        if v.unset:
            continue
        if v.state == EMPTY:
            items.append((EMPTY, t, launched))
        elif v.state == FAILED:
            items.append((FAILED, t, got.get("at"), got["error"]))
        elif v.state in (MADE, WRITING, LEFT):
            items, seen = [], True
        else:
            items.append((SKIPPED, t, skip_cause(v.slot)))
    mails = [m for m in mails if last is None or m[0] is None or m[0] > last]
    return Told(items, not seen, mails)


def spaced(slot: dict[str, Any], at: datetime) -> bool:
    """손에 다시 물어도 되나 — 그 칸의 마지막 살펴보기에서 `BRIEF_TRY_GAP_MIN` 분이 지났다(작업이 더 자주 깨워도 SSO 를 촘촘히 안 두드린다)."""
    tries = slot.get("tries") or []
    last = tm.parse(tries[-1]["at"]) if tries else None
    return last is None or minute(at) - minute(last) >= C.BRIEF_TRY_GAP_MIN


def looked_after(slot: dict[str, Any], start: datetime, since: datetime | None) -> datetime:
    """그 칸의 사내 세션 답이 새것이려면 그 뒤에 섰어야 하는 때 — 칸의 시작 · 그 칸의 마지막 살펴보기 · 시계의 앞 판(`since` · 없으면 안 센다)
    가운데 가장 늦은 것. 앞 판 뒤에 선 답만 이 판이 처음 보는 답이다 — 앞 판이 이미 쓴 답을 다시 쓰면 그 사이 살아난 세션을 놓친다."""
    tries = slot.get("tries") or []
    return max(t for t in (start, tm.parse(tries[-1]["at"]) if tries else None, since) if t is not None)


def login_due(day: dict[str, Any], slot: dict[str, Any], order: int, setting: dict[str, Any], evidence: str) -> str:
    """이 판이 스스로 로그인의 입구를 부를 판인가 — LOGIN_DAILY 그날 첫 시각의 한 번(세션이 살았어도 — 입구가 그 윈도 로그온의 평소 Edge
    로그인을 먼저 한다) · LOGIN_SLOT 뒤 시각의 칸에서 세션이 없을 때 한 번 · "" 안 부른다. 따로 켠 값은 없다 — 보고 시각이 걸린 것이 곧
    그 시각의 로그인이고, 이 셈은 시각표가 걸린 판에서만 불린다(`setting`). 손이 세션을 못 살펴본 판 · 이 칸에서 이미 부른 판은 안 부른다 —
    한 칸에서 되풀이하면 사람이 다른 자리에서 연 메일을 판마다 끊는다."""
    if evidence not in (C.SESSION_LIVE, C.SESSION_LOST) or slot.get("login"):
        return ""
    if order == 0:
        return "" if day.get("login") else LOGIN_DAILY
    return LOGIN_SLOT if evidence == C.SESSION_LOST else ""


def slot_login(day: dict[str, Any], slot: dict[str, Any], order: int) -> dict[str, Any]:
    """그 칸의 띄우기 앞에 부른 입구의 끝 {at, ok, said, lost} — 첫 시각의 칸은 그날의 한 번(그날 장부의 `login`), 뒤 시각은 그 칸의 `login`.
    안 불렀으면 {}."""
    return (slot.get("login") if order else day.get("login")) or {}


def day_logins(day: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """그날 스스로 로그인의 입구를 부른 끝들 — (칸의 시각 · 그날 첫 시각의 한 번이면 "", 끝 {at, ok, said})을 부른 차례로."""
    got = [("", day["login"])] if day.get("login") else []
    got += [(t, s["login"]) for t, s in (day.get("slots") or {}).items() if isinstance(s, dict) and s.get("login")]
    return sorted(got, key=lambda one: one[1].get("at") or "")

