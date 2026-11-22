"""자리 밖에서 보기 — 켠 PC 에서 사람 없이 띄운 보고가 남긴 보고 글 한 장을 칸마다 한 통 본인 메일로 보내고, 켜고 끄기를 건다.

    said, refused = apply_away(folder, on, chosen, hand)  # 켜고 끈다 — 보고 창 · 대화가 함께 쓴다(켤 때 본인 주소를 주소록에서)
    line = mail_step(state, folder, hand, at)              # 판 끝의 맨 앞 — 앞 판이 남긴 「보내는 중」을 맺고, 끝난 보고마다 한 통
    if late(at): …                                         # 이 판이 메일 한 통 · 주소록 한 번을 새로 시작하기에 늦었나

언제 어떻게 한 통씩 보내나 · 두 통을 안 보내는 까닭은 `references/DESIGN.md` 「자리 밖에서 보기」가 든다.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any

import scan_const as C
import scan_hand as H
import scan_store as st
from brief_schedule import away_of, day_of, load, mail_words, next_slot, on_day, read_brief, run_over, seoul_date, unattended_brief, windows
from window_link import sheet_of


def away_now(away: dict[str, Any]) -> str:
    """지금 켜져 있나의 한 구절 — 거절할 때마다 함께 댄다."""
    return "지금은 켜져 있어 사람 없이 지은 보고를 본인 메일로도 보냅니다" if away.get("on") else "지금은 꺼져 있어 메일로 보내지 않습니다"


def apply_away(folder: pathlib.Path, on: bool, chosen: datetime, hand: pathlib.Path | None) -> tuple[str, bool]:
    """「자리 밖에서 보기」를 켜거나 끈다 — 보고 창의 누름(창 곁의 손 · 스캔 판)과 대화(`scan.py brief --away`)가 함께 쓰는 한 자리.
    켤 때 본인 주소를 주소록 손의 「나」에서 받아 시각표 파일에 적는다 — 받는 사람을 다른 데서 받는 칸이 없다. 주소를 못 받으면 켜지 않는다.
    나중의 말씀이 이긴다 — `chosen`(고른 때)이 걸어 둔 고른 때보다 앞이면(그 사이 대화에서 바꾸셨다) 안 바꾸고, 같으면 이미 받은 그 누름이다.
    내는 것 — (그 자리에 돌려 적을 말, 따르지 않았나)."""
    setting, problem = load(folder)
    if setting is None and problem:
        return f"{'켜지' if on else '끄지'} 않았습니다 — {problem}", True
    if setting is None:
        return (("켜지 않았습니다 — 사람 없는 보고가 걸려 있지 않습니다. 보고 시각을 먼저 거신 뒤 켜 주세요", True) if on
                else ("메일로 보내지 않습니다 — 사람 없는 보고가 걸려 있지 않습니다", False))
    away = away_of(setting)
    before = st.parse(away.get("chosen"))
    if before is not None and chosen < before:
        return f"창에서 고르신 뒤에 대화에서 바꾸셔서 창에서 고르신 것은 따르지 않았습니다. {away_now(away)}", True
    if before is not None and chosen == before:
        return away_words(away, setting, folder), False
    if on:
        address, why = own_address(hand)
        if not address:
            return f"켜지 않았습니다 — 본인 메일 주소를 주소록에서 받지 못했습니다({why}). {away_now(away)}", True
        new = {"on": True, "address": address}
    else:
        new = {"on": False}
    new.update(chosen=chosen.astimezone(timezone.utc).isoformat(timespec="milliseconds"), set=st.stamp(st.now()))
    try:
        current = read_brief(folder)
    except st.Unreadable as exc:          # 빈 것 위에 쓰면 시각표가 사라진다
        return f"{'켜지' if on else '끄지'} 않았습니다 — 보고 시각표를 그 순간 못 읽었습니다({exc}). 다시 눌러 주세요. {away_now(away)}", True
    if current is None:
        return "바꾸지 않았습니다 — 그 사이 사람 없는 보고가 내려졌습니다", True
    st.write_json(folder / C.BRIEF_FILE, {**current, "away": new})
    return away_words(new, setting, folder), False


def away_words(away: dict[str, Any], setting: dict[str, Any], folder: pathlib.Path) -> str:
    """켜고 끈 뒤의 말 — 켰으면 어느 보고부터 보내나."""
    if away.get("on"):
        return f"켰습니다 — 다음 사람 없는 보고({next_slot(setting, folder, st.now())})부터 메일로도 보냅니다"
    return "껐습니다 — 사람 없는 보고를 메일로 보내지 않습니다"


def own_address(hand: pathlib.Path | None) -> tuple[str, str]:
    """본인 주소 — 형제 스킬 company-directory 의 「나」(`DIRECTORY_ME`)가 낸 사람 파일의 주소 하나. 내는 것 — (주소, "") 나 ("", 까닭)."""
    script = hand.parents[2] / C.DIRECTORY_SKILL / pathlib.Path(*C.DIRECTORY_SCRIPT) if hand is not None else None
    if script is None or not script.is_file():
        return "", "주소록 손(스킬 company-directory)을 못 찾았습니다"
    with tempfile.TemporaryDirectory(prefix="away-me-", dir=st.scan_dir(make=True)) as out:
        try:
            done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(script), *C.DIRECTORY_ME, "--out", out], capture_output=True,
                                  timeout=C.DIRECTORY_TIMEOUT_S, stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                                  **H.quiet())
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
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(C.SCRIPT_DIR / C.AWAY_SENDER), "--dir", str(folder), "--hand", str(hand)],
                              input=sheet, capture_output=True, timeout=C.AWAY_SEND_TIMEOUT_S, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                              **H.quiet())
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


def left_sending(state: dict[str, Any], folder: pathlib.Path, at: datetime, lines: list[str]) -> bool:
    """앞 판이 남긴 「보내는 중」 표지(`AWAY_SENDING_FILE`)를 맺는다 — 그 칸의 기록에 표지보다 늦은 끝이 있으면 그 판이 끝을 적은 것이라 표지만
    걷고, 없으면 그 판이 중계를 부른 뒤 끝을 적기 전에 죽은 것이라 「보냈는지 모른다」로 맺는다 — 다시 보내면 두 통일 수 있다. 표지를 지금
    모습과 따로 두는 까닭 — 판 도중에 지금 모습을 쓰면 그 판이 찾은 메일함의 바뀜이 바뀜 기록보다 앞서 굳어, 판이 죽으면 바뀜이 영영 안 적힌다.
    내는 것 — 이 판이 보내도 되나. 표지가 있는데 못 읽으면 걷지 않고 거짓을 낸다 — 어느 칸의 표지인지 모른 채 걷으면 그 칸을 다시 보내 두 통이 된다."""
    path = folder / C.AWAY_SENDING_FILE
    try:
        mark = st.read_json(path)
    except st.Unreadable as exc:
        if not exc.broken:
            lines.append(f"[자리 밖에서 보기 — 「보내는 중」 표지를 못 읽어 이번 판에는 안 보냈다({exc}) — 다음 판이 다시 읽는다]")
            return False
        mark = {}                                # 글이 깨진 표지 — 어느 칸인지 끝내 모른다. 걷는다
    if mark is None:
        return True
    day = state.get("brief") if isinstance(state.get("brief"), dict) else {}
    slot = (day.get("slots") or {}).get(mark.get("slot")) if isinstance(mark, dict) and day.get("date") == mark.get("date") else None
    if isinstance(slot, dict):
        mail = slot.get("mail") or {}
        if str(mail.get("at") or "") < str(mark.get("at") or ""):
            slot["mail"] = {**mail, "state": C.AWAY_UNSURE, "why": LEFT_SENDING, "at": st.stamp(at), "tries": int(mail.get("tries") or 0) + 1}
            lines.append(f"[자리 밖에서 보기 — {mark.get('slot')} 보고: 메일을 보냈는지 확인하지 못했다 — {LEFT_SENDING}. 다시 보내지 않는다]")
    path.unlink(missing_ok=True)
    return True


def late(at: datetime) -> bool:
    """이 판이 메일 한 통 · 주소록 한 번을 새로 시작하기에 늦었나 — 시작한 일이 판의 잠금 · 작업의 시한 안에 끝나야 한다(`AWAY_LATEST_S`)."""
    return (st.now() - at).total_seconds() > C.AWAY_LATEST_S


def mail_step(state: dict[str, Any], folder: pathlib.Path, hand: pathlib.Path | None, at: datetime) -> str:
    """자리 밖에서 보기 — 켠 PC 에서, 켠 뒤에 사람 없이 띄운 보고가 끝나 남긴 보고 글 한 장을 칸마다 한 통 본인 주소로 보낸다. 대화에서 지은
    보고는 띄운 칸이 없어 안 보낸다. 칸의 시각이 열쇠다 — 중계를 부르기 전에 「보내는 중」 표지(그날 · 칸의 시각)를 따로 굳히고, 끝을 받은 뒤
    칸의 기록(`slots.<시각>.mail`)에 그 끝을 적는다(지금 모습은 판 끝에 부르는 쪽이 쓴다 · 표지는 다음 판이 걷는다 — `left_sending`). 넘기기 전에 진 것은 그 칸이 끝날 때까지 판마다 다시 보내고(칸이 끝난 뒤 처음 보내 본 것은 한 번),
    넘기는 도중이나 뒤에 진 것과 앞 판이 남긴 「보내는 중」은 다시 안 보낸다 — 두 통을 보내기보다 못 보낸 채 알린다. 한 판에 한 통까지,
    판이 늦었으면(`late`) 안 보내고 다음 판에 둔다. 날이 바뀐 첫 판은 지난날의 칸부터 맺는다 — 그날 칸은 그 뒤 새 날에 걷힌다.
    내는 것 — 판 끝에 찍을 줄(바꾼 것이 없으면 "") · 칸의 기록을 고치면 늘 한 줄을 내어 부르는 쪽이 지금 모습을 쓰게 한다."""
    setting, _ = load(folder)
    if setting is None:
        return ""
    times, lines, tried = setting["times"], [], []
    if not left_sending(state, folder, at, lines):
        return "\n".join(lines)
    old = state.get("brief")
    if isinstance(old, dict) and isinstance(old.get("slots"), dict) and old.get("date") and old.get("date") != seoul_date(at):
        try:
            noon = on_day("12:00", datetime.strptime(str(old["date"]), "%Y-%m-%d").replace(tzinfo=st.KST))
        except ValueError:
            noon = None
        if noon is not None:
            send_day(old, times, noon, setting, folder, hand, at, lines, tried)
    day = day_of(state, at, times, login=bool(setting.get("login")), setting=setting)
    send_day(day, times, at, setting, folder, hand, at, lines, tried)
    return "\n".join(lines)


def send_day(day: dict[str, Any], times: list[str], ref: datetime, setting: dict[str, Any], folder: pathlib.Path,
             hand: pathlib.Path | None, at: datetime, lines: list[str], tried: list[str]) -> None:
    """그날(`ref` 의 날) 칸들의 메일을 맺는다 — `mail_step` 의 몸. 시각표에서 빠진 칸도 띄운 기록이 있으면 맺는다(그 칸은 끝난 칸으로 본다).
    `tried` 는 이 판에 보내 본 칸 — 한 판에 하나까지다."""
    slots = day.get("slots") or {}
    away = away_of(setting)
    since = st.parse(away.get("chosen"))
    if not away.get("on") or not away.get("address") or since is None:
        return
    ends = {t: end for t, _, _, end in windows(times, ref)}
    started = sorted((st.parse((s.get("launched") or {}).get("at")), t) for t, s in slots.items()
                     if isinstance(s, dict) and (s.get("launched") or {}).get("at") and not (s.get("launched") or {}).get("error"))
    for i, (launched_at, t) in enumerate(started):
        slot, end = slots[t], ends.get(t, at)            # 시각표에서 빠진 칸은 끝난 칸이다 — 처음 보내 보는 것만 한다
        launched, mail = slot["launched"], slot.get("mail") or {}
        if launched_at < since:
            continue                                     # 켜기 전에 띄운 보고
        if mail.get("state") and not (mail.get("state") == C.AWAY_RETRY and at < end):
            continue                                     # 맺었다 · 칸이 끝났다
        ended = run_over(launched, at, started[i + 1][0] if i + 1 < len(started) else None)
        brief = unattended_brief(launched, ended) if ended else None
        if brief is None:
            continue
        if tried or late(at):
            lines.append(f"[자리 밖에서 보기 — {t} 보고: 이번 판에는 시간이 모자라 다음 판에 보낸다]")
            continue
        tries = int(mail.get("tries") or 0) + 1
        tried.append(t)
        if hand is None:
            got, why = C.AWAY_RETRY, "회사 메일 손을 못 찾았습니다"
        else:
            sheet, why = sheet_of(brief, str(day.get("date") or ""), t)
            if not sheet:
                got = C.AWAY_RETRY
            else:
                try:                                     # 중계를 부르기 전에 굳힌다 — 그 뒤 판이 끝을 적기 전에 죽으면 다음 판이 이 표지를 본다
                    st.write_json(folder / C.AWAY_SENDING_FILE, {"date": day.get("date"), "slot": t, "at": st.stamp(st.now())})
                except OSError as exc:
                    lines.append(f"[자리 밖에서 보기 — {t} 보고: 「보내는 중」을 못 굳혀 이번 판에는 안 보냈다({type(exc).__name__})]")
                    continue
                got, why = send_sheet(folder, hand, sheet)
        slot["mail"] = {"state": got, "at": st.stamp(st.now()), "brief": brief.name, "tries": tries, **({"why": why} if why else {})}
        lines.append(f"[자리 밖에서 보기 — {t} 보고: {mail_words(slot['mail'], end, st.now())}]")
