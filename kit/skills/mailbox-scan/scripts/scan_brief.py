"""정한 시각의 보고 — 스캔 판 끝의 손. 자리 밖에서 보기의 메일 · 보고 창에서 고르신 것 · 시각마다의 띄우기 · 「일정에 넣기」 누름
거두기를 이 차례로 엮는다. 셈 · 살피기 · 띄우기 · 보내기 · 창 부르기는 저마다의 조각이 든다 — 시각표와 그날의 칸(`brief_schedule`) ·
사내 세션과 스스로 로그인(`session_login`) · claude 띄우기(`claude_launch`) · 자리 밖에서 보기(`away_mail`) · 보고 창 이음(`window_link`).

    line = after_run(state, folder, evidence, hand, at)   # 판 끝 — 자리 밖에서 보기를 켰으면 띄운 보고가 남긴 글을 칸마다 한 통 본인 메일로
                                                          # 보내고, 지금 칸의 시각이 사내 세션이 살아 있는 첫 판에 띄운다. 할 말이 없으면 ""
                                                          # 그 뒤에 보고 창의 「일정에 넣기」 누름을 거둔다(보고를 안 걸었어도)
                                                          # 스스로 로그인을 켠 PC 는 그날 첫 시각의 띄우기 앞에 한 번 로그인 입구를 부른다

언제 띄우나 · 띄운 claude 에 무엇을 여나 · 로그인을 언제 하고 언제 안 하나는 `references/DESIGN.md` 「정한 시각의 보고」가, 보고 창에서
고르신 시각 · 「자리 밖에서 보기」와 누르신 「일정에 넣기」를 어떻게 받나는 「보고 창 이음」이, 켠 PC 의 보고를 언제 어떻게 한 통씩 보내나는
「자리 밖에서 보기」가 든다.
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime
from typing import Any

import scan_store as st
from away_mail import apply_away, late, mail_step
from brief_schedule import current, day_of, end_words, load, missed, slot_of, spaced, take_window_times, waiting
from claude_launch import launch
from session_login import ERROR, LIVE, look, LOST, sign_in
from window_link import ask_window, edge_listening, SAID_CHARS, TICKS, WINDOW_AWAY, window_presses, WINDOW_TIMES


def after_run(state: dict[str, Any], folder: pathlib.Path, evidence: str | None, hand: pathlib.Path | None, at: datetime) -> str:
    """판 끝 — 자리 밖에서 보기의 메일(`mail_step`)을 먼저 보내 그 끝이 이 판에 띄우는 보고의 부탁 글에 실리게 하고, 고르신 것과 띄우기
    (`brief_step`)를 하고, 보고 창의 「일정에 넣기」 누름을 그 뒤에 거둔다(보고를 안 걸었어도). 누름을 거두는 데 몇 분이 들 수 있어 띄우기가
    그것을 기다리지 않게 뒤에 둔다. 내는 것 — 판 끝에 찍을 줄(할 말이 없으면 "")."""
    mailed = mail_step(state, folder, hand, at)
    said = brief_step(state, folder, evidence, hand, at)
    pressed = window_presses()
    return "\n".join(x for x in (mailed, said, pressed) if x)


def brief_step(state: dict[str, Any], folder: pathlib.Path, evidence: str | None, hand: pathlib.Path | None, at: datetime) -> str:
    """판 끝 — 보고 창에서 고르신 시각을 먼저 받고, 지금 칸의 시각이 살펴볼 때면 사내 세션을 보고 살아 있으면 띄운다. `evidence` 는 그
    판이 손에서 받은 답이라 늘 쓰고(세션 파일이 새로 쓰여 판이 돌았으면 그 판에 바로 띄운다), 답이 없는 판(None)만 틈(`spaced`)을 지켜
    손에 묻는다. 세션이 없으면 로그인은 안 하고 기다린다 — 사용자가 스스로 로그인을 켠 PC 만 그날 첫 시각의 띄우기 앞에 한 번 입구를
    부르고(세션이 살았어도 — 평소 Edge 로그인은 입구가 로그온마다 한 번 든다), 서면 그 판에 띄운다(못 세운 날은 다시 안 부른다). 뒤
    시각은 스스로 로그인하지 않는다 — 살아 있는 세션에서만 띄운다.
    `state` 의 그날 칸을 고치고 파일 쓰기는 부르는 쪽 몫이다. 내는 것 — 판 끝에 찍을 줄(할 말이 없으면 "")."""
    said = window_choices(folder, hand, at)
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


def window_choices(folder: pathlib.Path, hand: pathlib.Path | None, at: datetime) -> str:
    """보고 창에서 고르신 보고 시각과 「자리 밖에서 보기」를 받아 건다 — 보고가 걸려 있을 때만, 보고 창 손 한 번(`ticks.py --times`)의 답에서
    둘을 읽는다. 창은 그 손이 이 PC 의 디버깅 포트로 읽는다 — 열린 보고 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다. 창에서 받는 것은
    이 둘뿐이다 — 스스로 로그인 · 띄울 claude 는 걸어 둔 그대로다. 내는 것 — 판 끝에 찍을 줄(할 말이 없으면 "")."""
    setting, _ = load(folder)
    ticks = TICKS
    if setting is None or not ticks.is_file() or not edge_listening():
        return ""
    got = ask_window(ticks, ["--times"])
    times = window_times(folder, setting, ticks, got)
    away = window_away(folder, ticks, got, hand, at)
    return "\n".join(x for x in (times, away) if x)


def window_times(folder: pathlib.Path, setting: dict[str, Any], ticks: pathlib.Path, got: str) -> str:
    """보고 창에서 고르신 보고 시각(`got` — 보고 창 손의 답)을 걸고(`take_window_times`), 받았나와 까닭을 그 창에 돌려 적는다 — 창 곁의 손이
    없을 때의 뒷받침이다(그 손은 같은 일을 `scan.py brief --window-times` 로 바로 한다). 내는 것 — 판 끝에 찍을 한 줄(고르신 시각이 없으면 "")."""
    picked = WINDOW_TIMES.search(got)
    if not picked:
        return ""
    said, refused = take_window_times(folder, setting, picked.group(1).split(), picked.group(2).split() if picked.group(2) != "-" else [],
                                      picked.group(3))
    ask_window(ticks, ["--times-done", picked.group(3), "--said", said[:SAID_CHARS], *(["--refused"] if refused else [])])
    return f"[보고 예약 — 보고 창에서 고르신 시각: {said}]"


def window_away(folder: pathlib.Path, ticks: pathlib.Path, got: str, hand: pathlib.Path | None, at: datetime) -> str:
    """보고 창에서 고르신 「자리 밖에서 보기」(`got` — 보고 창 손의 답)를 건다(`apply_away`) — 창 곁의 손이 없을 때의 뒷받침이다(그 손은
    같은 일을 `scan.py brief --away` 로 바로 한다). 받았나와 까닭을 그 창에 돌려 적는다. 내는 것 — 판 끝에 찍을 한 줄(고르신 것이 없으면 "")."""
    picked = WINDOW_AWAY.search(got)
    if not picked:
        return ""
    if late(at):
        return "[자리 밖에서 보기 — 보고 창에서 고르신 것은 이번 판에 시간이 모자라 다음 판에 받는다]"
    chosen = st.parse(picked.group(2).replace("Z", "+00:00"))
    if chosen is None:
        said, refused = "고르신 때를 못 읽어 따르지 않았습니다 — 대화에서 말씀해 주세요", True
    else:
        said, refused = apply_away(folder, json.loads(picked.group(1)), chosen, hand)
    ask_window(ticks, ["--away-done", picked.group(2), "--said", said[:SAID_CHARS], *(["--refused"] if refused else [])])
    return f"[자리 밖에서 보기 — 보고 창에서 고르신 것: {said}]"


MISS_WORDS = {LOST: "사내 세션이 없어", ERROR: "손이 사내 세션을 못 살펴봐"}   # 판 끝 한 줄 — 손 오류를 「세션 없음」으로 말하지 않는다
