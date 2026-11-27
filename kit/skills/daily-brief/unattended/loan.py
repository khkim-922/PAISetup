"""사람의 로그인을 돌려준다 — 이 PC 의 프로그램이 사람 없이 세운 사내 로그인(그 로그인이 사람의 평소 Edge 의 EP 포털을 죽였다)을 다 쓰면 형제 스킬
ep-login 입구의 돌려주는 문을 사람 없는 꼴로 한 번 부른다(`session_login.give_back` — 평소 Edge 에 로그인을 다시 열고 쓸모가 끝난 EP 탭을 닫는다).
빌린 로그인은 둘이다 — 시계가 보고 시각에 끊긴 세션 위에서 세운 것(그날 장부의 로그인 기록)과, 돌려준 날 보고 창의 단추(「일정에 넣기」 · 「결재 창
열기」 · 「맡기기」)가 세션을 쓰려다 끊겨 있어 잠깐 다시 세운 것(빌림 파일 `LOAN_FILE`). 둘 다 이 조각 하나가 OS 잠금(`LOAN_LOCK_FILE`) 아래에서
빌리고 돌려준다 — 시계 판 · 창 곁의 손 · 맡긴 일의 지킴이가 함께 불러도 한 번이다.

    line = give_back_step(state, folder, hand, at)       # 시계 판 끝 — 돌려줄 때면 돌려주고 판 끝의 줄(할 말이 없으면 ""). 그날 장부에 끝을 단다
    ok = lend(folder, hand, at, why, ceiling_s, lost)    # 단추의 일이 세션을 쓴다 — 끊겼으면 오늘 돌려준 뒤일 때만 다시 로그인한다. 산 세션에서 도나
    said = release(folder, hand, at, why, hold)          # 그 일이 세션을 놓는다 — 빌린 로그인을 쓰는 일이 더 없으면 곧 돌려준다
    rec = loan_of(folder, at)                            # 오늘의 빌림 파일 — status 가 말한다
    code = cmd_lend(args, home) · cmd_release(args, home)   # `clock.py lend · release` — 보고 창 곁의 손(`scripts/presses.py`)이 부른다

언제 돌려주고 언제 안 돌려주나는 `references/DESIGN.md` 「사람의 로그인을 돌려준다」가 든다.
"""

from __future__ import annotations

import os
import pathlib
import re
import time
from datetime import datetime, timedelta
from typing import Any

import clock as tm
import clock_task as CT
import task_base as TB
import unattended_const as C
import unattended_store as st
from brief_reports import launched_end, lock_held
from brief_schedule import load
from brief_slots import seoul_date, windows
from brief_state import slot_login
from oslock import OsLock
import scan_door as D
from session_login import LOST, give_back, look, sign_in

GIVEN = "given"            # 보고 앞 로그인 기록에 다는 돌려준 끝(빌림 파일의 `given` 한 줄) — 단 기록은 다시 안 돌려준다
PUT, APPR, RUN = "put", "appr", "run"
WHYS = (PUT, APPR, RUN)           # 세션을 쓰는 단추의 일 — 일정에 넣기 · 결재 창 열기 · 맡기기
GIVE_BACK_TRIES = 2                    # 돌려주는 문이 맺지 못하고 진 것을 그날 다시 해 보는 수의 끝 — 그 뒤로는 status 가 「EP 돌려줘」를 댄다
BUTTON = "button"                      # 돌려준 끝의 `of` — 보고 창의 단추가 빌린 로그인
LENT, NOT_LENT, RELEASED = "[보고 창 — 산 세션에서 한다]", "[보고 창 — 사내 세션이 없어 빌리지 않았다]", "[보고 창 — 놓았다]"
LOCK_STEP_S = 1.0                      # 잠금을 기다리는 사이
COUNTS = re.compile(r"port-closed=(\d+) .*ordinary-closed=(\d+)")   # 돌려주는 문의 끝 줄에서 닫은 탭의 수


# ── 빌림 파일 ────────────────────────────────────────────────────────────────────

def loan_of(folder: pathlib.Path, at: datetime) -> dict[str, Any]:
    """오늘(서울)의 빌림 파일 {date, given: [돌려준 끝 {at, ok, of, line | said, typed?}], lent: 빌린 로그인 {at, ok, said?} | None,
    users: [그 세션을 쓰는 일 {why, until}]} — 없거나 날이 지났거나 글이 깨졌으면 빈 오늘의 것. 그 순간 못 읽으면 `st.Unreadable`(빈 것으로
    읽어 쓰면 오늘 돌려준 것을 잊고 또 돌려준다)."""
    try:
        got = st.read_json(folder / C.LOAN_FILE)
    except st.Unreadable as exc:
        if not exc.broken:
            raise
        got = None
    if not isinstance(got, dict) or got.get("date") != seoul_date(at):
        got = {}
    def rows(key: str) -> list[dict[str, Any]]:
        """그 칸의 줄들 — 꼴이 아닌 줄은 뺀다."""
        return [g for g in got.get(key) or [] if isinstance(g, dict)]
    return {"date": seoul_date(at), "given": rows("given"), "users": rows("users"),
            "lent": got.get("lent") if isinstance(got.get("lent"), dict) else None,
            "futile": [w for w in got.get("futile") or [] if isinstance(w, str)]}


def save(folder: pathlib.Path, rec: dict[str, Any]) -> None:
    """빌림 파일을 바꿔 끼워 쓴다 — 못 쓰면 OSError."""
    st.write_json(folder / C.LOAN_FILE, rec)


def given_ok(rec: dict[str, Any]) -> bool:
    """오늘 돌려주는 문이 한 번이라도 섰나 — 그 뒤에 끊긴 세션은 우리가 돌려줘서 끊긴 것이다."""
    return any(g.get("ok") for g in rec["given"])


def typed_today(rec: dict[str, Any]) -> bool:
    """오늘 돌려주는 문이 SSO 가 안 서는 로그온이라고 했나 — 그러면 그날은 다시 안 부른다(칠 사람이 없고, 아무것도 안 열었다)."""
    return any(g.get("typed") for g in rec["given"])


def users_of(rec: dict[str, Any], at: datetime) -> list[dict[str, Any]]:
    """그 세션을 지금 쓰는 일들 {why, until} — 쓸 끝(`until`)이 안 지난 것만. 끝은 쓰겠다고 할 때 그 일의 천장 뒤로 두고(놓는다고 하기 전에
    죽은 손이 영영 붙들지 않게), 결재 창처럼 사람이 그 세션에서 누를 일은 놓을 때 `GIVE_BACK_AFTER_MIN` 분 뒤로 고친다."""
    return [u for u in rec["users"] if (tm.parse(u.get("until")) or at) > at]


def in_use(folder: pathlib.Path, rec: dict[str, Any], at: datetime) -> bool:
    """그 세션을 지금 쓰는 프로그램이 있나 — 시계가 띄운 보고가 돈다 · 보고 창의 단추가 맡긴 일이 그 세션을 쓴다(`users_of`)."""
    return bool(lock_held(folder, at) or users_of(rec, at))


def locked(folder: pathlib.Path, wait_s: float) -> OsLock | None:
    """빌리고 돌려주는 잠금 — `wait_s` 안에 쥐면 그 잠금, 못 쥐면 None(다른 손이 입구를 부르는 중이다)."""
    lock = OsLock(folder / C.LOAN_LOCK_FILE)
    end = time.monotonic() + wait_s
    while not lock.take():
        if time.monotonic() >= end:
            return None
        time.sleep(LOCK_STEP_S)
    return lock


def hand_back(folder: pathlib.Path, rec: dict[str, Any], hand: pathlib.Path | None, at: datetime, of: str) -> dict[str, Any]:
    """돌려주는 문을 한 번 부르고 그 끝을 빌림 파일에 적는다. 맺은 끝이면(`settled`) 빌린 로그인을 걷는다 — 그 문이 포트 창의 세션을 끊었다.
    내는 것 — 그 끝."""
    got = {**give_back(hand, at), "of": of}
    rec["given"].append(got)
    if settled(got, rec):
        rec["lent"] = None
    save(folder, rec)
    return got


def failures(rec: dict[str, Any]) -> list[dict[str, Any]]:
    """오늘 돌려주는 문이 맺지 못하고 진 끝들 — 섰다 · SSO 가 안 선다가 아닌 것(시한 · Edge 를 못 찾음 따위)."""
    return [g for g in rec["given"] if not g.get("ok") and not g.get("typed")]


def settled(got: dict[str, Any], rec: dict[str, Any]) -> bool:
    """그 끝으로 그 로그인을 맺나 — 섰다 · SSO 가 안 선다(그날 다시 안 부른다) · 진 것이 오늘 `GIVE_BACK_TRIES` 번에 닿았다(판마다 평소 Edge 에
    로그인을 거듭 열지 않는다). 그 밖에 진 것은 맺지 않고 `BRIEF_TRY_GAP_MIN` 분 뒤 판에 다시 부른다."""
    return bool(got.get("ok") or got.get("typed")) or len(failures(rec)) >= GIVE_BACK_TRIES


def retry_wait(rec: dict[str, Any], at: datetime) -> bool:
    """앞 판에 진 돌려주기 뒤 `BRIEF_TRY_GAP_MIN` 분이 안 지났나."""
    last = max((tm.parse(g.get("at")) for g in failures(rec)), default=None, key=lambda x: x or at)
    return bool(last and at - last < timedelta(minutes=C.BRIEF_TRY_GAP_MIN))


def given_words(got: dict[str, Any]) -> str:
    """돌려준 끝 한 구절 — 판 끝의 줄과 status 가 쓴다."""
    when = tm.seoul(tm.parse(got.get("at")), "%H:%M")
    if got.get("ok"):
        m = COUNTS.search(str(got.get("line") or ""))
        shut = f" · EP 탭 {int(m.group(1)) + int(m.group(2))}개를 닫았다" if m else ""
        return f"{when}에 사내 로그인을 평소 Edge 로 돌려줬다{shut}"
    if got.get("typed"):
        return f"{when}에 사내 로그인을 못 돌려줬다 — 이 PC 는 SSO 가 안 서 사람이 아이디를 쳐야 한다(오늘은 다시 안 한다). 다음: 대화에서 「EP 돌려줘」"
    return f"{when}에 사내 로그인을 못 돌려줬다 — {got.get('said')}. 다음: 대화에서 「EP 돌려줘」"


# ── 보고 앞 로그인 ────────────────────────────────────────────────────────────────


def loans_of(day: dict[str, Any], times: list[str], at: datetime) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """그날 돌려줄 로그인 — 시계가 끊긴 세션 위에서 세운 보고 앞 로그인(첫 시각은 `lost` 인 그날의 한 번 · 뒤 시각은 칸의 한 번 — 뒤 시각은
    끊긴 세션에서만 부른다) 가운데 섰고 아직 돌려준 끝이 없는 것. 그 칸이 띄웠든 못 띄웠든 든다 — 로그인은 이미 평소 Edge 의 포털을 죽였다.
    살아 있던 세션 앞의 부름은 시계가 로그인을 새로 했는지 몰라 안 든다 — 그 세션은 사람이 대화에서 세운 것일 수 있다. 내는 것 — (칸의 시각,
    로그인 기록, 칸의 끝 — 시각표에서 빠진 칸이면 None)."""
    ends = {t: end for t, _, _, end in windows(times, at)}
    got = []
    for order, (t, _, _, _) in enumerate(windows(times, at)):
        login = slot_login(day, (day.get("slots") or {}).get(t) or {}, order)
        if login.get("ok") is True and (order or login.get("lost")) and GIVEN not in login:
            got.append((t, login, ends.get(t)))
    return got


def due_at(day: dict[str, Any], t: str, login: dict[str, Any], end: datetime | None, at: datetime) -> datetime | None:
    """그 로그인을 돌려줄 때 — 그 로그인 뒤에 띄운 보고가 다 끝난 때(`launched_end` — 도는 동안은 기다리고, 띄운 때에서 `BRIEF_LOCK_STALE_S` 를 넘지
    않는다 · 못 띄운 것은 띄우려던 때)와 로그인한 때 가운데 늦은 것에서 `GIVE_BACK_AFTER_MIN` 분 뒤. 그 칸이 아직 안 띄웠고 칸이 안 끝났으면 None
    (그 칸이 곧 그 세션으로 띄운다) · 보고가 아직 돌면 None. 뒤 칸이 같은 세션으로 띄운 보고도 그 로그인의 것으로 센다."""
    since = tm.parse(login.get("at")) or at
    slot = (day.get("slots") or {}).get(t) or {}
    if not slot.get("launched") and end is not None and at < end:
        return None
    ref = since
    for s_t, s in (day.get("slots") or {}).items():
        launched = s.get("launched") if isinstance(s, dict) else None
        began = tm.parse((launched or {}).get("at"))
        if began is None or began < since:
            continue                               # 그 로그인 앞에 띄웠거나 띄운 때를 못 읽은 기록 — 그 로그인의 보고가 아니다
        ended = began if launched.get("error") else launched_end(day, s_t, at)
        if ended is None:
            return None
        ref = max(ref, ended)
    return ref + timedelta(minutes=C.GIVE_BACK_AFTER_MIN)


# ── 시계 판의 돌려주기 ─────────────────────────────────────────────────────────────

def give_back_step(state: dict[str, Any], folder: pathlib.Path, hand: pathlib.Path | None, at: datetime) -> str:
    """시계 판 끝의 돌려주기 — 돌려줄 로그인(그날 장부의 보고 앞 로그인 가운데 그 보고가 끝나고 `GIVE_BACK_AFTER_MIN` 분이 지난 것 · 단추가 빌렸는데
    쓰는 일이 더 없는 것)이 있고, 그 세션을 지금 쓰는 일이 없으면(`in_use`) 돌려주는 문을 한 번 부르고 그 끝을 빌림 파일과 그날 장부의 그 로그인
    기록(`GIVEN`)에 적는다 — 적힌 로그인은 다시 안 돌려준다(SSO 가 안 서는 로그온의 4 도 그 끝으로 적혀 그날 다시 안 부른다). 잠금을 다른 손이 쥐었거나 빌림
    파일을 그 순간 못 읽으면 다음 판에 다시 본다. 내는 것 — 판 끝의 줄(할 말이 없으면 "")."""
    day = state.get("brief") if isinstance(state.get("brief"), dict) else {}
    setting, _ = load(folder)
    lock = locked(folder, 0)
    if lock is None:
        return ""
    try:
        try:
            rec = loan_of(folder, at)
        except st.Unreadable:
            return ""
        loans = loans_of(day, setting["times"], at) if setting is not None and day.get("date") == seoul_date(at) else []
        whens = [due_at(day, t, login, end, at) for t, login, end in loans]
        if any(w is None or w > at for w in whens) or in_use(folder, rec, at):
            later = [w for w in whens if w is not None and w > at] + [tm.parse(u.get("until")) for u in users_of(rec, at)]
            if loans and all(w is not None for w in whens) and later and not lock_held(folder, at):
                wake(folder, hand, max(later))     # 다 언제 돌려줄지 섰다(틈 · 쓰는 일의 끝) — 그 때에 판 한 번을 걸어 시계의 주기를 안 기다린다
            return ""                              # 한 로그인이라도 아직 그 틈 안이면 기다린다 — 한 번 돌려주면 그 세션을 다 끊는다
        due = [(t, login) for t, login, _ in loans]
        if not (due or (rec["lent"] or {}).get("ok")) or retry_wait(rec, at):
            return ""
        got = hand_back(folder, rec, hand, at, " · ".join(t for t, _ in due) or BUTTON)
        if settled(got, rec):
            for _, login in due:
                login[GIVEN] = got
        return f"[보고 예약 — {given_words(got)}]"
    except OSError:
        return "[보고 예약 — 사내 로그인을 돌려준 끝을 못 적었다 — 다음 판에 다시 본다]"
    finally:
        lock.release()



def wake(folder: pathlib.Path, hand: pathlib.Path | None, due: datetime) -> None:
    """돌려줄 때(`due`)에 시계 판 한 번을 부르는 한 번만의 작업을 걸거나 그 때로 고친다(`clock_task.GIVE_BACK_TASK_NAME` — 돌고 나면 작업 스케줄러가
    지운다). 그 판이 돌려주기를 한다 — 놓쳐도 시계의 다음 판이 한다. 손이 없거나 · 작업 스케줄러가 거절하면 아무 말 없이 넘긴다(다음 판이 다시 건다)."""
    if hand is None:
        return
    path = folder / C.GIVE_BACK_TASK_XML
    try:
        TB.write_xml(path, CT.give_back_xml(at=due.astimezone().replace(tzinfo=None) + timedelta(seconds=C.WAKE_SLACK_S), home=folder, hand=hand))
    except OSError:
        return
    if C.WAKE_OFF_ENV not in os.environ:
        TB.ask(TB.register_command(CT.GIVE_BACK_TASK_NAME, path))


# ── 보고 창의 단추가 빌린다 ────────────────────────────────────────────────────────

def lend(folder: pathlib.Path, hand: pathlib.Path | None, at: datetime, why: str, ceiling_s: int, lost: bool | None = None,
         owner: int | None = None) -> bool:
    """보고 창의 단추가 맡긴 일(`why` — put · appr · run)이 사내 세션을 쓴다고 적는다 — 쓰는 동안 시계 판이 돌려주지 않게(쓸 끝은 `ceiling_s` 뒤 —
    놓는다고 하기 전에 죽은 손이 영영 붙들지 않게 · `owner` 는 놓을 때 제 것을 찾는 프로세스 번호 — 없으면 이 프로세스). 세션이 끊겨 있으면(`lost` — 모르면 손에 한 번 묻는다) 오늘 이 PC 가 로그인을 돌려준 뒤일 때만
    잠깐 다시 로그인한다(빌린 로그인 `lent`). 안 빌리는 때 — 오늘 돌려준 적이 없다(사람이 다른 자리에서 로그인해 끊겼다 · 대화가 세운 세션이
    끊겼다 — 전처럼 대화의 EP 로그인을 청한다) · SSO 가 안 서는 로그온 · 그 일이 오늘 빌린 로그인 위에서도 세션 없음을 냈다(`futile` — 판마다 로그인하고
    돌려주기를 되풀이하지 않는다) · 빌린 로그인이 섰는데 또 끊겼다(사람이 다른 자리에서 로그인했다 — 판마다 그 창을
    다시 닫지 않는다) · 앞 빌림의 로그인이 `BRIEF_TRY_GAP_MIN` 분 안에 못 섰다. 내는 것 — 그 일이
    산 세션에서 돌 수 있나."""
    lock = locked(folder, C.GIVE_BACK_TIMEOUT_S)
    if lock is None:
        return False
    try:
        rec = loan_of(folder, at)
        if lost is None:
            lost = look(hand) == LOST
        lent = rec["lent"] or {}
        if lost and lent.get("ok"):
            lost = look(hand) == LOST              # 함께 세션 없음을 받은 다른 일이 방금 빌렸을 수 있다 — 지금 살았으면 함께 쓴다
        if lost:
            tried = tm.parse(lent.get("at"))
            if not given_ok(rec) or typed_today(rec) or why in rec["futile"] or lent.get("ok") or (lent and tried and at - tried < timedelta(minutes=C.BRIEF_TRY_GAP_MIN)):
                return False                       # 빌린 로그인이 섰는데 지금도 끊겼다 — 사람이 다른 자리에서 로그인했다: 다시 끊지 않는다
            rec["lent"] = sign_in(hand, at)
            if not rec["lent"].get("ok"):
                save(folder, rec)
                return False
        rec["users"] = [*users_of(rec, at), {"why": why, "until": tm.utc_stamp(at + timedelta(seconds=ceiling_s)), "pid": owner or os.getpid()}]
        save(folder, rec)
        return True
    except OSError:                                # 못 읽음(`st.Unreadable`) · 못 씀 — 빌리지 않고 전처럼 세션 없음으로 맺는다
        return False
    finally:
        lock.release()


def release(folder: pathlib.Path, hand: pathlib.Path | None, at: datetime, why: str, hold: bool = False, futile: bool = False,
            owner: int | None = None) -> str:
    """그 세션을 쓴 일 하나(`why` 의 첫 것)가 세션을 놓는다 — 걷고, `hold` 면(결재 창 — 사람이 그 세션이 사는 창에서 누른다) 그 뒤
    `GIVE_BACK_AFTER_MIN` 분 더 쓰는 것으로 적는다(빌리지 않은 일도). `futile` 이면(빌린 로그인 위에서도 세션 없음이었다) 그 일에는
    오늘 다시 안 빌려 준다. 그 뒤 빌린 로그인을 쓰는 일이 더 없고 시계가 띄운 보고도 안 돌면 곧 돌려준다. 내는 것 — 돌려준 끝의 한 구절(안
    돌려줬으면 "")."""
    lock = locked(folder, C.GIVE_BACK_TIMEOUT_S)
    if lock is None:
        return ""                                  # 다른 손이 빌리거나 돌려주는 중 — 그 손이나 다음 시계 판이 돌려준다
    try:
        rec = loan_of(folder, at)
        users = users_of(rec, at)
        mine = next((u for u in users if u.get("why") == why and u.get("pid") == (owner or os.getpid())), None) or \
            next((u for u in users if u.get("why") == why and "hold" not in u), None)   # 그 손이 적은 것 — 없으면 같은 일의 붙들지 않은 것
        if mine is not None:
            users.remove(mine)
        if hold:                                   # 빌리지 않고 산 세션에서 띄운 결재 창도 — 시계 판이 그 세션을 그 틈 안에 돌려주지 않게
            users.append({"why": why, "until": tm.utc_stamp(at + timedelta(minutes=C.GIVE_BACK_AFTER_MIN)), "hold": True})
        rec["users"] = users
        if futile and why not in rec["futile"]:
            rec["futile"].append(why)
        save(folder, rec)
        if not (rec["lent"] or {}).get("ok") or in_use(folder, rec, at):
            return ""
        return given_words(hand_back(folder, rec, hand, at, BUTTON))
    except OSError:
        return ""                                  # 못 읽음 · 못 씀 — 빌린 로그인은 다음 시계 판이 돌려준다
    finally:
        lock.release()


# ── 명령 — 보고 창 곁의 손이 부른다 ────────────────────────────────────────────────

def cmd_lend(args, home: pathlib.Path) -> int:
    """`clock.py lend --why W --ceiling S [--lost]` — 보고 창 곁의 손이 단추의 일을 하기 전(산 세션으로 보고 — 손에 안 묻는다)과 그 일이 세션
    없음을 낸 뒤(`--lost`) 부른다. 끝 줄 하나. 종료 값 — 0 산 세션에서 하면 된다
    (빌렸거나 살아 있다) · 1 빌리지 않았다(전처럼 세션 없음으로 맺는다)."""
    hand, _ = D.mail_hand(None)
    ok = lend(home, hand, tm.utc_now(), args.why, args.ceiling, bool(args.lost), os.getppid())   # 부른 창 곁의 손이 주인이다
    print(LENT if ok else NOT_LENT)
    return 0 if ok else 1


def cmd_release(args, home: pathlib.Path) -> int:
    """`clock.py release --why W [--hold] [--futile]` — 단추의 일이 끝난 뒤 부른다. 끝 줄 하나(돌려줬으면 그 구절). 종료 값 0."""
    hand, _ = D.mail_hand(None)
    said = release(home, hand, tm.utc_now(), args.why, args.hold, args.futile, os.getppid())
    print(f"[보고 창 — {said}]" if said else RELEASED)
    return 0


# ── status 의 줄 ───────────────────────────────────────────────────────────────

def status_lines(state: dict[str, Any] | None, folder: pathlib.Path, at: datetime, times: list[str], when: str) -> list[str]:
    """status 가 말할 오늘의 돌려주기 — 돌려준 끝마다 한 줄 · 아직 안 돌려준 보고 앞 로그인(언제 돌려주나) · 보고 창의 단추가 빌려 쓰는 중인
    로그인. 보이기만 한다 — 그날 장부 · 빌림 파일을 안 고친다. 빌림 파일을 그 순간 못 읽으면 그렇다고 한 줄."""
    try:
        rec = loan_of(folder, at)
    except st.Unreadable as exc:
        return [f"  오늘({when}): 사내 로그인을 돌려준 기록을 그 순간 못 읽었다({exc})"]
    lines = [f"  오늘({when}): {given_words(g)}" + (f"({g['of']} 보고 앞 로그인)" if g.get("of") not in (None, BUTTON) else
                                                    "(보고 창의 단추가 잠깐 다시 한 로그인)" if g.get("of") == BUTTON else "")
             for g in rec["given"]]
    day = (state or {}).get("brief") if isinstance((state or {}).get("brief"), dict) else {}
    if day.get("date") == seoul_date(at):
        for t, login, end in loans_of(day, times, at):
            due = due_at(day, t, login, end, at)
            lines.append(f"  오늘({when}): {t} 보고 앞에 스스로 한 로그인은 " +
                         ("그 보고가 끝난 뒤 " if due is None else f"{tm.seoul(due, '%H:%M')} 뒤 첫 확인에 ") +
                         f"평소 Edge 로 돌려준다(보고가 끝나고 {C.GIVE_BACK_AFTER_MIN}분 — 그 사이 보고 창의 단추가 그 로그인을 쓴다)")
    if (rec["lent"] or {}).get("ok"):
        lines.append(f"  오늘({when}): {tm.seoul(tm.parse(rec['lent'].get('at')), '%H:%M')}에 보고 창의 단추가 사내 로그인을 잠깐 다시 했다 — "
                     "그 일이 끝나면 평소 Edge 로 돌려준다")
    return lines
