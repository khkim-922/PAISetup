"""자리 밖에서 보기 — 켠 PC 에서 사람 없이 띄운 보고가 남긴 보고 글 한 장을 칸마다 한 통 본인 메일로 보내고, 켜고 끄기를 건다.

    said, refused = apply_away(folder, on, chosen, hand)  # 켜고 끈다 — 보고 창 · 대화가 함께 쓴다(켤 때 본인 주소를 주소록에서)
    line = mail_step(state, folder, hand, at)              # 판 끝의 맨 앞 — 앞 판이 남긴 「보내는 중」을 맺고, 끝난 보고마다 한 통
    if late(at): …                                         # 이 판이 메일 한 통 · 주소록 한 번을 새로 시작하기에 늦었나

언제 어떻게 한 통씩 보내나 · 두 통을 안 보내는 까닭은 `references/DESIGN.md` 「자리 밖에서 보기」가 든다.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

import clock_book as B
import proc_base as P
import unattended_const as C
import unattended_store as st
import clock as tm
from brief_day import next_slot
from brief_reports import launch_outcome, launches
from brief_schedule import away_of, load, put
from brief_slots import noon_of, seoul_date, windows
from brief_told import today
from brief_kinds import (AGAIN, AWAY_CLEAR, AWAY_LATE, AWAY_LEFT, AWAY_MARK_FAILED, AWAY_MARK_UNREAD, AWAY_TRIED, GONE, MAIL_NONE, MAIL_RETRYING,
                         NEW, NO_ADDRESS, STALE, UNREAD, UNSET)
from brief_state import mail_status
from brief_words import away_line
from window_link import sheet_of


def away_now(away: dict[str, Any]) -> str:
    """지금 켜져 있나의 한 구절 — 거절할 때마다 함께 댄다."""
    return "지금은 켜져 있어 사람 없이 지은 보고를 본인 메일로도 보냅니다" if away.get("on") else "지금은 꺼져 있어 메일로 보내지 않습니다"


def away_verdict(away: dict[str, Any], chosen: datetime) -> str:
    """자리 밖에서 보기의 고름을 따르나 — 나중의 말씀이 이긴다: 걸어 둔 고른 때보다 앞이면 STALE(그 사이 대화에서 바꾸셨다), 같으면 AGAIN(이미
    받은 그 누름), 아니면 NEW."""
    before = tm.parse(away.get("chosen"))
    if before is not None and chosen < before:
        return STALE
    if before is not None and chosen == before:
        return AGAIN
    return NEW


def away_refusal(why: str, on: bool, away: dict[str, Any], detail: str = "") -> str:
    """자리 밖에서 보기를 안 바꾼 말 — 걸린 보고가 없다(UNSET · 못 읽은 까닭 `detail`) · 뒤에 대화에서 바꾸셨다(STALE) · 본인 주소를 못 받았다
    (NO_ADDRESS) · 시각표를 못 읽었다(UNREAD) · 그 사이 보고가 내려졌다(GONE)."""
    if why == UNSET:
        if detail:
            return f"{'켜지' if on else '끄지'} 않았습니다 — {detail}"
        return ("켜지 않았습니다 — 사람 없는 보고가 걸려 있지 않습니다. 보고 시각을 먼저 거신 뒤 켜 주세요" if on
                else "메일로 보내지 않습니다 — 사람 없는 보고가 걸려 있지 않습니다")
    if why == STALE:
        return f"창에서 고르신 뒤에 대화에서 바꾸셔서 창에서 고르신 것은 따르지 않았습니다. {away_now(away)}"
    if why == NO_ADDRESS:
        return f"켜지 않았습니다 — 본인 메일 주소를 주소록에서 받지 못했습니다({detail}). {away_now(away)}"
    if why == UNREAD:
        return f"{'켜지' if on else '끄지'} 않았습니다 — 보고 시각표를 그 순간 못 읽었습니다({detail}). 다시 눌러 주세요. {away_now(away)}"
    return "바꾸지 않았습니다 — 그 사이 사람 없는 보고가 내려졌습니다"


def away_words(on: bool, next_t: str | None, first: str) -> str:
    """켜고 끈 뒤의 말 — 켰으면 어느 보고(`next_t` · 오늘 남은 칸이 없으면 내일 첫 시각 `first`)부터 보내나."""
    if on:
        return f"켰습니다 — 다음 사람 없는 보고({next_t or f'내일 {first}'})부터 메일로도 보냅니다"
    return "껐습니다 — 사람 없는 보고를 메일로 보내지 않습니다"


def apply_away(folder: pathlib.Path, on: bool, chosen: datetime, hand: pathlib.Path | None) -> tuple[str, bool]:
    """「자리 밖에서 보기」를 켜거나 끈다 — 보고 창의 누름(창 곁의 손 · 시계 판)과 대화(`clock.py away`)가 함께 쓰는 한 자리. 걸린
    보고를 읽고, 따르나를 가르고(`away_verdict`), 켤 때는 본인 주소를 주소록 손의 「나」에서 받아(못 받으면 안 켠다) 시각표 파일의 칸 하나로
    적는다. 내는 것 — (그 자리에 돌려 적을 말, 따르지 않았나)."""
    setting, problem = load(folder)
    if setting is None:
        return away_refusal(UNSET, on, {}, problem), bool(problem) or on
    away = away_of(setting)
    verdict = away_verdict(away, chosen)
    if verdict == STALE:
        return away_refusal(STALE, on, away), True
    if verdict == AGAIN:
        on_now = bool(away.get("on"))
        return away_words(on_now, next_slot(setting, B.load_or_none(folder), folder, tm.utc_now()) if on_now else None, setting["times"][0]), False
    if on:
        address, why = own_address(folder, hand)
        if not address:
            return away_refusal(NO_ADDRESS, on, away, why), True
        new = {"on": True, "address": address}
    else:
        new = {"on": False}
    new.update(chosen=chosen.astimezone(timezone.utc).isoformat(timespec="milliseconds"), set=tm.utc_stamp(tm.utc_now()))
    try:
        wrote = put(folder, "away", new)
    except st.Unreadable as exc:          # 빈 것 위에 쓰면 시각표가 사라진다
        return away_refusal(UNREAD, on, away, str(exc)), True
    if not wrote:
        return away_refusal(GONE, on, away), True
    return away_words(on, next_slot(setting, B.load_or_none(folder), folder, tm.utc_now()) if on else None, setting["times"][0]), False


def own_address(folder: pathlib.Path, hand: pathlib.Path | None) -> tuple[str, str]:
    """본인 주소 — 형제 스킬 company-directory 의 「나」(`DIRECTORY_ME`)가 사용자 폴더의 임시 폴더에 낸 사람 파일의 주소 하나. 내는 것 —
    (주소, "") 나 ("", 까닭)."""
    script = hand.parents[2] / C.DIRECTORY_SKILL / pathlib.Path(*C.DIRECTORY_SCRIPT) if hand is not None else None
    if script is None or not script.is_file():
        return "", "주소록 손(스킬 company-directory)을 못 찾았습니다"
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=C.AWAY_TEMP_PREFIX, dir=folder) as out:
        try:
            done = P.run_python(script, [*C.DIRECTORY_ME, "--out", out], C.DIRECTORY_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return "", f"주소록 손이 {C.DIRECTORY_TIMEOUT_S}초 안에 답하지 않았습니다"
        except OSError as exc:
            return "", f"주소록 손을 못 띄웠습니다({type(exc).__name__})"
        if done.returncode == C.HAND_EXIT_SESSION:
            return "", "사내 로그인이 끊겨 있습니다 — EP 로그인 뒤 다시 켜 주세요"
        if done.returncode != C.HAND_EXIT_OK:
            return "", f"주소록 손이 종료 {done.returncode} 로 끝났습니다"
        try:
            people = json.loads((pathlib.Path(out) / C.DIRECTORY_PEOPLE).read_text(encoding="utf-8")).get("people") or []
        except (OSError, ValueError, AttributeError):
            people = []
    found = {str(p["email"]).strip() for p in people if isinstance(p, dict) and isinstance(p.get("email"), str) and p["email"].count("@") == 1}
    if len(found) != 1:
        return "", "주소록이 「나」를 주소 하나로 내지 않았습니다"
    return found.pop(), ""


LEFT_SENDING = "보내던 판이 끝을 적기 전에 멈췄습니다"          # 앞 판이 남긴 「보내는 중」의 까닭


def send_sheet(folder: pathlib.Path, hand: pathlib.Path, sheet: bytes) -> tuple[str, str]:
    """보내는 손 한 번 — (끝, 까닭). 넘기기 전에 진 것만 `AWAY_RETRY` 이고, 시한을 넘겼거나 모르는 끝은 다 `AWAY_UNSURE` 다."""
    try:
        done = P.run_python(C.HERE / C.AWAY_SENDER, ["--dir", str(folder), "--hand", str(hand)], C.AWAY_SEND_TIMEOUT_S, sheet)
    except subprocess.TimeoutExpired:
        return C.AWAY_UNSURE, f"보내는 손이 {C.AWAY_SEND_TIMEOUT_S}초 안에 안 끝났습니다(중계가 받았는지 모른다)"
    except OSError as exc:
        return C.AWAY_RETRY, f"보내는 손을 못 띄웠습니다({type(exc).__name__})"
    lines = done.stdout.decode("utf-8", "replace").strip().splitlines()
    said = lines[-1].split(" — ", 1)[-1] if lines else f"보내는 손이 종료 {done.returncode} 로 끝났습니다"
    if done.returncode == C.SEND_EXIT_SENT:
        return C.AWAY_SENT, ""
    if done.returncode in (C.SEND_EXIT_BEFORE, 2):          # 2 — 인자가 틀려 아무것도 안 보냈다
        return C.AWAY_RETRY, said
    return C.AWAY_UNSURE, said


def left_sending(state: dict[str, Any], folder: pathlib.Path, at: datetime) -> tuple[str, Any]:
    """앞 판이 남긴 「보내는 중」 표지(`AWAY_SENDING_FILE`)를 맺는다 — 그 칸의 기록에 표지보다 늦은 끝이 있으면 그 판이 끝을 적은 것이라 표지만
    걷고, 없으면 그 판이 중계를 부른 뒤 끝을 적기 전에 죽은 것이라 「보냈는지 모른다」로 맺는다 — 다시 보내면 두 통일 수 있다. 표지를 지금
    모습과 따로 두는 까닭 — 판 도중에 지금 모습을 쓰면 그 판이 찾은 메일함의 바뀜이 바뀜 기록보다 앞서 굳어, 판이 죽으면 바뀜이 영영 안 적힌다.
    내는 것 — (AWAY_CLEAR, None) 이 판이 보내도 된다 · (AWAY_LEFT, 시각) 그 칸을 맺었고 보내도 된다 · (AWAY_MARK_UNREAD, 까닭) 표지가 있는데
    못 읽어 걷지 않았다(어느 칸의 표지인지 모른 채 걷으면 그 칸을 다시 보내 두 통이 된다) — 이 판은 안 보낸다."""
    path = folder / C.AWAY_SENDING_FILE
    try:
        mark = st.read_json(path)
    except st.Unreadable as exc:
        if not exc.broken:
            return AWAY_MARK_UNREAD, str(exc)
        mark = {}                                # 글이 깨진 표지 — 어느 칸인지 끝내 모른다. 걷는다
    if mark is None:
        return AWAY_CLEAR, None
    settled = None
    day = state.get("brief") if isinstance(state.get("brief"), dict) else {}
    slot = (day.get("slots") or {}).get(mark.get("slot")) if isinstance(mark, dict) and day.get("date") == mark.get("date") else None
    if isinstance(slot, dict):
        mail = slot.get("mail") or {}
        if str(mail.get("at") or "") < str(mark.get("at") or ""):
            slot["mail"] = {**mail, "state": C.AWAY_UNSURE, "why": LEFT_SENDING, "at": tm.utc_stamp(at), "tries": int(mail.get("tries") or 0) + 1}
            settled = mark.get("slot")
    path.unlink(missing_ok=True)
    return (AWAY_LEFT, settled) if settled is not None else (AWAY_CLEAR, None)


def late(at: datetime) -> bool:
    """이 판이 메일 한 통 · 주소록 한 번을 새로 시작하기에 늦었나 — 시작한 일이 시계 작업의 시한 안에 끝나야 한다(`AWAY_LATEST_S`)."""
    return (tm.utc_now() - at).total_seconds() > C.AWAY_LATEST_S


def mail_step(state: dict[str, Any], folder: pathlib.Path, hand: pathlib.Path | None, at: datetime) -> str:
    """자리 밖에서 보기 — 켠 PC 에서, 켠 뒤에 사람 없이 띄운 보고가 끝나 남긴 보고 글 한 장을 칸마다 한 통 본인 주소로 보낸다. 대화에서 지은
    보고는 띄운 칸이 없어 안 보낸다. 칸의 시각이 열쇠다 — 중계를 부르기 전에 「보내는 중」 표지(그날 · 칸의 시각)를 따로 굳히고, 끝을 받은 뒤
    칸의 기록(`slots.<시각>.mail`)에 그 끝을 적는다(그날 장부는 판 끝에 부르는 쪽이 쓴다 · 표지는 다음 판이 걷는다 — `left_sending`). 넘기기 전에 진 것은 그 칸이 끝날 때까지 판마다 다시 보내고(칸이 끝난 뒤 처음 보내 본 것은 한 번),
    넘기는 도중이나 뒤에 진 것과 앞 판이 남긴 「보내는 중」은 다시 안 보낸다 — 두 통을 보내기보다 못 보낸 채 알린다. 한 판에 한 통까지,
    판이 늦었으면(`late`) 안 보내고 다음 판에 둔다. 날이 바뀐 첫 판은 지난날의 칸부터 맺는다 — 그날 칸은 그 뒤 새 날에 걷힌다.
    내는 것 — 판 끝에 찍을 줄(바꾼 것이 없으면 "") · 칸의 기록을 고치면 늘 한 줄을 낸다."""
    setting, _ = load(folder)
    if setting is None:
        return ""
    times, done, tried = setting["times"], [], []
    left, detail = left_sending(state, folder, at)
    if left == AWAY_MARK_UNREAD:
        return away_line((AWAY_MARK_UNREAD, detail))
    if left == AWAY_LEFT:
        done.append((AWAY_LEFT, detail, LEFT_SENDING))
    old = state.get("brief")
    if isinstance(old, dict) and isinstance(old.get("slots"), dict) and old.get("date") and old.get("date") != seoul_date(at):
        noon = noon_of(old["date"])
        if noon is not None:
            send_day(old, times, noon, setting, folder, hand, at, done, tried)
    day = today(folder, state, at, setting)
    send_day(day, times, at, setting, folder, hand, at, done, tried)
    return "\n".join(away_line(item) for item in done)


def send_day(day: dict[str, Any], times: list[str], ref: datetime, setting: dict[str, Any], folder: pathlib.Path,
             hand: pathlib.Path | None, at: datetime, done: list[tuple[Any, ...]], tried: list[str]) -> None:
    """그날(`ref` 의 날) 칸들의 메일을 맺는다 — 보낼 칸마다(`due_mails`) 한 판에 한 통까지, 판이 늦었으면 다음 판에 두고, 보낼 수 있으면 한 통
    보낸다(`send_one`). 한 일을 `done` 에 더한다. `tried` 는 이 판에 보내 본 칸이다."""
    for t, slot, end, brief in due_mails(folder, day, times, ref, setting, at):
        if tried or late(at):
            done.append((AWAY_LATE, t))
            continue
        tried.append(t)
        done.append(send_one(day, t, slot, end, brief, folder, hand))


def due_mails(folder: pathlib.Path, day: dict[str, Any], times: list[str], ref: datetime, setting: dict[str, Any], at: datetime
              ) -> Iterator[tuple[str, dict[str, Any], datetime, pathlib.Path]]:
    """그날(`ref` 의 날) 칸 가운데 지금 보낼 것 — 켠 뒤에 띄웠고, 아직 맺지 않았고(다시 보낼 칸은 그 칸이 끝나기 전까지), 띄운 보고가 끝나
    글을 남긴 칸(보고 글은 사용자 폴더 `folder` 에 선다). 시각표에서 빠진 칸도 띄운 기록이 있으면 끝난 칸으로 본다. 내는 것 — 띄운 차례로 (시각, 칸, 칸의 끝, 보고 글)."""
    slots = day.get("slots") or {}
    away = away_of(setting)
    since = tm.parse(away.get("chosen"))
    if not away.get("on") or not away.get("address") or since is None:
        return
    ends = {t: end for t, _, _, end in windows(times, ref)}
    for launched_at, t in launches(day):
        slot, end = slots[t], ends.get(t, at)            # 시각표에서 빠진 칸은 끝난 칸이다 — 처음 보내 보는 것만 한다
        mail = slot.get("mail") or {}
        if launched_at < since:
            continue                                     # 켜기 전에 띄운 보고
        if mail_status(mail, end, at) not in (MAIL_NONE, MAIL_RETRYING):
            continue                                     # 맺었다 · 칸이 끝났다
        _, brief = launch_outcome(folder, day, t, at)
        if brief is not None:
            yield t, slot, end, brief


def send_one(day: dict[str, Any], t: str, slot: dict[str, Any], end: datetime, brief: pathlib.Path, folder: pathlib.Path,
             hand: pathlib.Path | None) -> tuple[Any, ...]:
    """칸 하나의 보고를 한 통 보낸다 — 메일 한 장(`sheet_of`) → 「보내는 중」 굳히기(`mark_sending`) → 보내는 손(`send_sheet`) → 칸의 기록에
    끝을 적는다. 표지를 못 굳혔으면 보내지 않고 칸도 안 고친다. 내는 것 — (AWAY_TRIED, 시각, 메일 상태, 메일 기록, 칸의 끝, 때) ·
    (AWAY_MARK_FAILED, 시각, 까닭)."""
    tries = int((slot.get("mail") or {}).get("tries") or 0) + 1
    if hand is None:
        got, why = C.AWAY_RETRY, "회사 메일 손을 못 찾았습니다"
    else:
        sheet, why = sheet_of(folder, brief, str(day.get("date") or ""), t)
        if not sheet:
            got = C.AWAY_RETRY
        else:
            failed = mark_sending(folder, day, t)
            if failed:
                return AWAY_MARK_FAILED, t, failed
            got, why = send_sheet(folder, hand, sheet)
    slot["mail"] = {"state": got, "at": tm.utc_stamp(tm.utc_now()), "brief": brief.name, "tries": tries, **({"why": why} if why else {})}
    now = tm.utc_now()
    return AWAY_TRIED, t, mail_status(slot["mail"], end, now), slot["mail"], end, now


def mark_sending(folder: pathlib.Path, day: dict[str, Any], t: str) -> str:
    """중계를 부르기 전에 「보내는 중」 표지(그날 · 칸의 시각 · 때)를 굳힌다 — 그 뒤 판이 끝을 적기 전에 죽으면 다음 판이 이 표지를 본다.
    내는 것 — 굳혔으면 "", 못 굳혔으면 그 까닭(오류의 이름)."""
    try:
        st.write_json(folder / C.AWAY_SENDING_FILE, {"date": day.get("date"), "slot": t, "at": tm.utc_stamp(tm.utc_now())})
    except OSError as exc:
        return type(exc).__name__
    return ""
