"""정한 시각의 시계 한 판 — 자리 밖에서 보기의 메일 → 보고 창에서 고르신 것 → 지금 칸의 띄우기 → 「일정에 넣기」 누름 거두기를 이 차례로
엮고 맨 끝에 사람의 로그인을 돌려준다. 셈 · 살피기 · 띄우기 · 보내기 · 창 부르기 · 스캔 부르기는 저마다의 조각이 든다 — 시각표 파일(`brief_schedule`) · 그날 장부
(`brief_day`) · 칸의 상태(`brief_state`) · 말(`brief_words`) · 사내 세션과 스스로 로그인(`session_login`) · 보고 띄우기(`claude_launch`) ·
자리 밖에서 보기(`away_mail`) · 보고 창 이음(`window_link`) · 보고 창에서 고르신 것(같은 스킬 `scripts/` 의
`window_door`) · 스캔 이음(`scan_door`) · 사람의 로그인 돌려주기(`loan`).

    line = round_lines(state, folder, hand, at, since)   # 판 끝의 줄 — 할 말이 없으면 "". `state` 는 판의 상태 `{"brief": 그날 장부}`
                                                          # (`clock_book`), `since` 는 시계의 앞 판 때(없으면 None)

지금 칸의 띄우기 — 그 칸에서 살펴볼 때면 사내 세션의 답을 잡고(스캔 판이 그 칸 안 · 마지막 살펴보기 뒤에 손에서 받은 답이 있으면 그것,
없으면 틈을 지켜 손에 한 번 묻는다), 부를 판이면 로그인 입구를 부르고(그날 첫 시각에 한 번 · 뒤 시각은 세션이 없을 때 그 칸에서 한 번),
세션이 살았거나 로그인이 섰으면 스캔에 「지금 한 판」을 청해 그 판의 세션 답이 「살았다」일 때만 띄운다 — 띄운 보고는 그 판이 산 세션에서
읽은 메일함 위에 선다. 언제 띄우나 · 띄운 claude 에 무엇을 여나 · 로그인을 언제 하고 언제 안 하나는 `references/DESIGN.md` 「정한 시각의
보고」가 든다.
"""

from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Any

import clock as tm
import scan_door as D
import unattended_const as C
from away_mail import apply_away, late, mail_step
from brief_day import slot_of
from brief_schedule import load, note_signed
from brief_slots import current
from brief_kinds import BUSY, LOGIN_DAILY
from brief_state import login_due, looked_after, slot_login, slot_state, spaced
from brief_window import take_window_times
from brief_told import today, told_lines
from brief_words import CHOSEN_UNREAD, SCAN_MISSED_WORDS, end_words
from claude_launch import launch
from loan import give_back_step
from session_login import ERROR, LIVE, look, LOST, sign_in
from window_door import Choices, read_choices
from window_link import ask_window, edge_listening, SAID_CHARS, window_presses

MISS_WORDS = {LOST: "사내 세션이 없어", ERROR: "손이 사내 세션을 못 살펴봐"}   # 판 끝 한 줄 — 손 오류를 「세션 없음」으로 말하지 않는다


def round_lines(state: dict[str, Any], folder: pathlib.Path, hand: pathlib.Path, at: datetime, since: datetime | None) -> str:
    """판 한 번 — 자리 밖에서 보기의 메일(`mail_step`)을 먼저 보내 그 끝이 이 판에 띄우는 보고의 부탁 글에 실리게 하고, 보고 창에서 고르신
    것(`window_choices`)을 받아 걸린 시각표에 얹은 뒤 띄우기(`brief_step`)를 하고, 보고 창의 「일정에 넣기」 누름을 그 뒤에 거둔다(보고를
    안 걸었어도). 누름을 거두는 데 몇 분이 들 수 있어 띄우기가 그것을 기다리지 않게 뒤에 둔다. 맨 끝이 사람의 로그인 돌려주기다
    (`loan.give_back_step`) — 남은 누름이 그 세션에서 먼저 들게. 내는 것 — 판 끝에 찍을 줄(할 말이 없으면 "")."""
    mailed = mail_step(state, folder, hand, at)
    chosen = window_choices(folder, hand, at)
    said = brief_step(state, folder, hand, at, since)
    pressed = window_presses(folder)
    given = give_back_step(state, folder, hand, at)
    return "\n".join(x for x in (mailed, chosen, said, pressed, given) if x)


# ── 보고 창의 고름 ────────────────────────────────────────────────────────────────

def window_choices(folder: pathlib.Path, hand: pathlib.Path | None, at: datetime) -> str:
    """보고 창에서 고르신 보고 시각과 「자리 밖에서 보기」를 받아 건다 — 보고가 걸려 있을 때만, 보고 창의 문 한 번(`window_door.read_choices`)으로
    둘을 읽는다. 창은 그 문이 이 PC 의 디버깅 포트로 읽는다 — 열린 보고 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다. 창에서 받는 것은
    이 둘뿐이다 — 스스로 로그인 · 띄울 claude 는 걸어 둔 그대로다. 내는 것 — 판 끝에 찍을 줄(할 말이 없으면 "")."""
    setting, _ = load(folder)
    ticks = C.TICKS_SCRIPT
    if setting is None or not ticks.is_file() or not edge_listening():
        return ""
    got = read_choices(folder) or Choices(None, None)
    times = window_times(folder, setting, ticks, got.times)
    away = window_away(folder, ticks, got.away, hand, at)
    return "\n".join(x for x in (times, away) if x)


def window_times(folder: pathlib.Path, setting: dict[str, Any], ticks: pathlib.Path, picked: tuple[list[str], list[str], str] | None) -> str:
    """보고 창에서 고르신 보고 시각(`picked` — 고르신 시각들 · 보던 시각들 · 고른 때)을 걸고(`take_window_times`), 받았나와 까닭을 그 창에 돌려 적는다 — 창 곁의 손이
    없을 때의 뒷받침이다(그 손은 같은 일을 `clock.py window-times` 로 바로 한다). 내는 것 — 판 끝에 찍을 한 줄(고르신 시각이 없으면 "")."""
    if picked is None:
        return ""
    said, refused = take_window_times(folder, setting, *picked)
    ask_window(folder, ticks, ["--times-done", picked[2], "--said", said[:SAID_CHARS], *(["--refused"] if refused else [])])
    return f"[보고 예약 — 보고 창에서 고르신 시각: {said}]"


def window_away(folder: pathlib.Path, ticks: pathlib.Path, picked: tuple[bool, str] | None, hand: pathlib.Path | None, at: datetime) -> str:
    """보고 창에서 고르신 「자리 밖에서 보기」(`picked` — 켬인가 · 고른 때)를 건다(`apply_away`) — 창 곁의 손이 없을 때의 뒷받침이다(그 손은
    같은 일을 `clock.py away` 로 바로 한다). 받았나와 까닭을 그 창에 돌려 적는다. 내는 것 — 판 끝에 찍을 한 줄(고르신 것이 없으면 "")."""
    if picked is None:
        return ""
    if late(at):
        return "[자리 밖에서 보기 — 보고 창에서 고르신 것은 이번 판에 시간이 모자라 다음 판에 받는다]"
    on, at_text = picked
    chosen = tm.parse_chosen(at_text)
    if chosen is None:
        said, refused = CHOSEN_UNREAD, True
    else:
        said, refused = apply_away(folder, on, chosen, hand)
    ask_window(folder, ticks, ["--away-done", at_text, "--said", said[:SAID_CHARS], *(["--refused"] if refused else [])])
    return f"[자리 밖에서 보기 — 보고 창에서 고르신 것: {said}]"


# ── 띄우기 ──────────────────────────────────────────────────────────────────────

def brief_step(state: dict[str, Any], folder: pathlib.Path, hand: pathlib.Path, at: datetime, since: datetime | None) -> str:
    """판의 띄우기 — 지금 칸을 고르고, 그 칸에서 살펴볼 때면 사내 세션의 답을 잡고(`session_now`), 부를 판이면 입구를 한 번 부르고
    (`self_login`), 세션이 살았으면 스캔에 한 판을 청해(`scan_door.ask_round`) 그 판의 세션 답으로 띄우거나 기다린다. 청한 판이 안 돌았으면
    살펴보기를 안 적고 다음 판이 다시 청한다(로그인은 그 칸에서 다시 안 한다). `state` 의 그날 칸을 고치고 그 파일 쓰기는 부르는 쪽 몫이다
    (시각표 파일의 `signed` 칸만 여기서 바로 쓴다 — 띄운 보고가 창을 짓기 전에 서야 한다). 내는 것 — 판 끝에 찍을 줄(할 말이 없으면 "")."""
    setting, _ = load(folder)
    if setting is None:
        return ""
    picked = slot_now(folder, state, setting, at)
    if picked is None:
        return ""
    day, order, t, start, end, slot = picked
    if slot_state(day, setting["times"], order, at, at, setting, folder).state in BUSY:
        return ""
    evidence = session_now(slot, start, since, hand, at)
    if evidence is None:
        return ""
    evidence, was, signed = self_login(day, slot, order, setting, evidence, hand, folder, at)
    if evidence == LIVE:
        answer, missed = D.ask_round(hand, tm.utc_now())
        if missed:
            return missed_line(t, end, at, missed)
        evidence = answer if answer in (LIVE, LOST) else ERROR
    slot["tries"].append({"at": tm.utc_stamp(tm.utc_now()), "session": evidence})
    if evidence != LIVE:
        return waiting_line(t, end, at, evidence, signed)
    note_launch(folder, day, slot, order, at)
    slot["launched"] = launch(setting, hand, folder, at, t, told_lines(folder, day, setting["times"], at, setting))
    return launched_line(t, slot["launched"], was, signed)


def slot_now(folder: pathlib.Path, state: dict[str, Any], setting: dict[str, Any],
             at: datetime) -> tuple[dict[str, Any], int, str, datetime, datetime, dict[str, Any]] | None:
    """지금 칸 — 그날 장부를 열고(날이 바뀌었으면 새 장부) 지금 든 칸을 고른다. 내는 것 — (그날 장부, 차례, 시각, 시작, 끝, 칸). 칸 밖이면 None."""
    times = setting["times"]
    day = today(folder, state, at, setting)
    now = current(times, at)
    if now is None:
        return None
    order, t, _, start, end = now
    return day, order, t, start, end, slot_of(day, t)


def session_now(slot: dict[str, Any], start: datetime, since: datetime | None, hand: pathlib.Path, at: datetime) -> str | None:
    """이 칸에서 쓸 사내 세션의 답 — 스캔 판이 그 칸 안 · 마지막 살펴보기와 시계의 앞 판(`since`) 뒤에 손에서 받은 답이 있으면 그것(세션 파일이
    새로 쓰여 스캔이 돌았으면 그 판으로 바로 띄운다), 없으면 틈(`spaced`)을 지켜 손에 한 번 묻는다. 틈이 안 지났으면 None — 이 판은 안 살펴본다."""
    seen = D.answer_since(looked_after(slot, start, since))
    if seen in (LIVE, LOST):
        return seen
    return look(hand) if spaced(slot, at) else None


def self_login(day: dict[str, Any], slot: dict[str, Any], order: int, setting: dict[str, Any], evidence: str,
               hand: pathlib.Path | None, folder: pathlib.Path, at: datetime) -> tuple[str, str, dict[str, Any] | None]:
    """보고 시각을 건 PC 의 띄우기 앞 — 부를 판이면(`login_due` — 그날 첫 시각의 한 번 · 뒤 시각의 칸에서 세션이 없을 때 한 번) 입구를
    사람 없는 꼴로 한 번 부르고 그 끝을 적는다(끊긴 세션 앞의 부름이면 `lost` — 그 로그인으로 띄운 보고의 창이 그것을 말한다). 내는 것 —
    (그 뒤의 세션 답, 부르기 전의 답, 입구의 끝 — 안 불렀으면 None)."""
    due = login_due(day, slot, order, setting, evidence)
    if not due:
        return evidence, evidence, None
    signed = sign_in(hand, at)
    if evidence == LOST:
        signed["lost"] = True
    (day if due == LOGIN_DAILY else slot)["login"] = signed   # 적힌 자리는 다시 안 부른다 — 그날 장부나 그 칸
    return session_after(signed, evidence, hand), evidence, signed


def session_after(signed: dict[str, Any], was: str, hand: pathlib.Path | None) -> str:
    """입구를 부른 뒤의 세션 답 — 섰으면 살았다. 못 세웠는데 부르기 전에 살아 있었으면 손에 다시 묻는다 — 평소 Edge 로그인이 포트 창의 메일을
    끊고 입구가 다시 못 세웠을 수 있다."""
    if signed["ok"]:
        return LIVE
    return look(hand) if was == LIVE else was


def missed_line(t: str, end: datetime, at: datetime, missed: str) -> str:
    """청한 스캔 판이 안 돈 판 끝의 한 줄 — 왜(`SCAN_MISSED_WORDS`) · 언제까지 다음 판에 다시 청하나."""
    return (f"[보고 예약 — {t} 보고: 메일함 스캔 한 판을 못 받아 못 띄웠다({SCAN_MISSED_WORDS[missed]}) · {end_words(end, at)} 까지 다음 확인에 "
            "다시 청한다]")


def launched_line(t: str, got: dict[str, Any], was: str, signed: dict[str, Any] | None) -> str:
    """띄운 판 끝의 한 줄 — 띄웠나와 왜 그 판이었나(세션이 있었다 · 스스로 로그인했다 · 입구를 먼저 불렀다) · 출력 자리."""
    if got.get("error"):
        return f"[보고 예약 — {t} 보고를 띄우지 못했다: {got['error']}]"
    why = ("사내 세션이 없어 스스로 로그인한 뒤 메일함을 다시 읽고" if was == LOST else "로그인 입구를 먼저 불렀고") if signed and signed["ok"] else "사내 세션이 있어"
    return f"[보고 예약 — {t} 보고: {why} 일일 보고를 띄웠다 · 출력 {got['log']}]"


def waiting_line(t: str, end: datetime, at: datetime, evidence: str, signed: dict[str, Any] | None) -> str:
    """못 띄운 판 끝의 한 줄 — 왜(세션 없음 · 손 오류 · 이 판의 스스로 로그인이 안 섰다 · 섰는데 그 뒤 메일함 읽기가 졌다) · 언제까지 기다리나."""
    tried = ("" if signed is None else f" · 스스로 로그인이 안 섰다({signed['said']})" if not signed["ok"] else
             " · 스스로 로그인은 섰는데 그 뒤 메일함 읽기가 졌다 — 이 시각에는 다시 로그인하지 않는다")
    return (f"[보고 예약 — {t} 보고: {MISS_WORDS[evidence]} 못 띄웠다{tried} · {end_words(end, at)} 까지 사내 세션이 서는 "
            "첫 판에 띄운다]")


def note_launch(folder: pathlib.Path, day: dict[str, Any], slot: dict[str, Any], order: int, at: datetime) -> None:
    """띄우는 판 — 이 보고가 세션 없이 선 스스로 로그인 위에서 뜨면 그 로그인한 때와 이 보고의 끝을 보고 창이 읽는 자리에 남긴다
    (`note_signed` — 그 로그인이 사람의 평소 Edge 에서 메일 · 일정 창을 닫고 EP 포털을 죽였다는 것을 그 보고의 창이 말한다): 그 칸의 로그인이
    섰다(뒤 시각 — 칸의 로그인은 끊긴 세션에서만 부른다) · 그날의 한 번이 끊긴 세션에서 섰다(그날 첫 시각의 칸만). 살아 있던 세션 앞의
    부름은 로그인을 새로 했는지 몰라 안 남긴다."""
    login = slot_login(day, slot, order)
    if login.get("ok") is True and (order or login.get("lost")):
        note_signed(folder, tm.parse(login["at"]), at)
