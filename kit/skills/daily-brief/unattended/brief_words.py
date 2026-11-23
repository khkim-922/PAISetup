"""보고 시각표의 말 — 칸의 상태(`brief_state`)와 시각표를 사람에게 할 말로 옮긴다: 거는 말 · 거절의 말 · status 의 한 시각 · 건너뛴 칸의
줄(부탁 글 · 지난날) · 칸의 메일 기록 · 보고 창에 돌려 적는 말. 셈은 다른 조각이 하고 여기는 말만 짓는다.

    words = window_words(windows(times, now))    # 거는 말 · status 가 함께 쓰는 「언제 띄우나」 한 구절
    refused = room_words(first_tight(times, added))   # 기다릴 틈이 모자란 시각이 있으면 거절의 말 — 받으면 ""
    lines = told_words(untold(...), before)      # 보고가 아직 말하지 않은 칸 · 못 간 메일의 줄(셈은 brief_state.untold)
    line = slot_line(v, state, cause, login)     # status 의 한 시각(셈은 brief_state.slot_state · status_state · skip_cause · slot_login)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import unattended_const as C
import clock as tm
from brief_kinds import (AHEAD, AWAY_LATE, AWAY_LEFT, AWAY_MARK_FAILED, AWAY_MARK_UNREAD, EMPTY, FAILED, HAND_ERROR, LEFT, LOGIN_UNSET, MADE,
                         MADE_EARLY, MADE_SCAN, MAIL_FAILED, MAIL_RETRYING, MAIL_SENT, NO_RUN, UNSCHEDULED, NO_SESSION, PAST_SET, RUNNING, SKIPPED,
                         STALE, UNREAD, WAITING, WRITING, Slot, Told, SCAN_LATE, SCAN_STOPPED, SCAN_UNREACHED)
from brief_slots import latest_start

SCAN_MISSED_WORDS = {SCAN_LATE: "앞 판이 시한 안에 안 끝났다", SCAN_STOPPED: "스캔이 멈췄다", SCAN_UNREACHED: "스캔을 못 불렀다"}   # 청한 판이 안 돈 까닭
CHOSEN_UNREAD = "고르신 때를 못 읽어 따르지 않았습니다 — 대화에서 말씀해 주세요"   # 보고 창이 낸 고른 때를 못 읽었을 때 그 창에 돌려 적는 말
TRY_WORDS = {C.SESSION_LOST: "세션 없음", C.SESSION_ERROR: "손이 답을 못 냄"}
SKIP_WORDS = {NO_RUN: "그 사이 스캔 판이 안 돌아(PC 꺼짐 · 로그온 전 · 작업이 꺼짐)", HAND_ERROR: "회사 메일 손이 사내 세션을 못 살펴봐",
              LOGIN_UNSET: "사내 세션이 없고 스스로 로그인도 안 서", NO_SESSION: "사내 세션이 없어"}


LOGIN_WORDS = ("보고 시각마다 비서가 스스로 로그인할 수 있다 — 그날 첫 시각의 보고 앞에 한 번(사내 세션이 살아 있어도 · 윈도 로그온마다 평소 "
               "Edge 에서 먼저, 이어 ep-login 창을 띄워 둔다), 뒤 시각은 사내 세션이 끊겨 있을 때만 그 보고 앞에 한 번. 입력 없이 넘는 통합 "
               "인증으로만 선다. 로그인하면 평소 Edge 에 떠 있던 사내 메일 · 일정 창이 닫히고 그 EP 포털 탭에서는 앱을 새로 못 띄운다 — 평소 "
               "Edge 에서 로그아웃한 뒤 다시 로그인하면 된다. 보고 시각 사이에는 로그인하지 않는다")
# ↑ 거는 말과 status 가 같은 말을 쓴다 — 보고 시각을 거는 것이 곧 이 로그인이라 고를 거리로 말하지 않는다
LOGIN_MISSING = "⚠ 이 PC 에서 로그인 입구(스킬 ep-login)나 node 를 못 찾았다 — 세션이 끊긴 보고 시각에는 로그인이 안 서 그 보고가 기다린다"


def in_force(setting: dict[str, Any] | None) -> str:
    """지금 걸린 시각표의 한 구절 — 거절할 때마다 함께 댄다."""
    return f"지금 걸린 보고 시각은 {' · '.join(setting['times'])} 입니다" if setting else "지금 걸린 보고 예약은 없습니다"


def hhmm(t: datetime | str | None) -> str:
    """서울 「HH:MM」 — 저장된 글자도 받는다."""
    when = tm.parse(t) if isinstance(t, str) or t is None else t
    return when.astimezone(tm.SEOUL).strftime("%H:%M") if when else ""


def end_words(end: datetime, start: datetime) -> str:
    """칸의 끝 「HH:MM」 — 그날 자정이면 「자정」."""
    return "자정" if end.astimezone(tm.SEOUL).date() != start.astimezone(tm.SEOUL).date() else hhmm(end)


def window_words(wins: list[tuple[str, datetime, datetime, datetime]]) -> str:
    """언제 띄우나의 한 구절 — 그날의 칸(`brief_slots.windows`)을 받는다. 거는 말과 status 가 같은 말을 쓴다."""
    spans = " · ".join(f"{t}({end_words(end, start)} 까지)" for t, _, start, end in wins)
    return f"날마다 서울 {spans} — 시각마다 그 틈에 사내 세션이 서는 첫 판에"


def gap_words(other: str | None, room: int) -> str:
    """틈이 모자란 까닭의 구절 — 붙은 다른 시각이 있으면 그와 몇 분, 없으면 그날 끝까지 몇 분."""
    return f"{other} 보고와 {room}분밖에 안 떨어져 있습니다" if other else f"그날이 끝나기까지 {room}분뿐입니다"


def room_words(tight: tuple[str, str | None, int] | None) -> str:
    """틈이 모자란 시각(`brief_slots.first_tight`)의 거절의 말 — 그 시각에는 시계 판이 안 돌아 보고가 날마다 안 뜬다. 모자란 데가 없으면 ""."""
    if tight is None:
        return ""
    who, other, room = tight
    if other:
        return f"{who} 보고는 {gap_words(other, room)} — 보고 시각끼리는 {C.BRIEF_ROOM_MIN}분 넘게 띄어 주세요"
    return f"{who} 보고는 {gap_words(None, room)} — 보고 시각은 {latest_start()} 전에 두어 주세요"


def window_reply(taken: list[str], gone: list[str], dropped: list[tuple[str, str | None, int]], untouched: bool, now: dict[str, Any] | None) -> str:
    """보고 창에 돌려 적을 말 — 걸지 않은 시각을 다 까닭과 함께, 더하고 뺀 것을 사실대로 댄다. `untouched` 는 고르신 것이 있는데 시각표가 안
    바뀌었다, `now` 는 건 뒤 다시 읽은 시각표다."""
    parts = []
    if dropped:
        parts.append("걸지 않은 시각: " + " · ".join(f"{t}({gap_words(other, room)})" for t, other, room in dropped)
                     + f" — 보고 시각끼리는 {C.BRIEF_ROOM_MIN}분 넘게 띄우고, 늦어도 {latest_start()} 전에 두어 주세요")
    if taken or gone:
        parts.append(" · ".join([*(f"{t} 을 더했습니다" for t in taken), *(f"{t} 을 뺐습니다" for t in gone)]))
    if not dropped and untouched:
        parts.append("걸린 시각표를 바꾸지 못했습니다")
    parts.append(in_force(now))
    return ". ".join(parts)


def window_refusal(why: str, setting: dict[str, Any], detail: str = "") -> str:
    """보고 창의 고름을 안 건 말 — 그 뒤 대화에서 바꾸셨다(STALE) · 시각의 꼴(BAD · `detail`) · 시각표를 못 읽었다(UNREAD · `detail`)."""
    if why == STALE:
        return f"창에서 고르신 뒤에 대화에서 시각을 바꾸셔서 창에서 고르신 것은 걸지 않았습니다. {in_force(setting)}"
    if why == UNREAD:
        return f"걸지 않았습니다 — 보고 시각표를 그 순간 못 읽었습니다({detail}). 다시 골라 주세요. {in_force(setting)}"
    return f"{detail}. {in_force(setting)}"


def mail_words(status: str, mail: dict[str, Any], end: datetime, at: datetime) -> str:
    """칸의 메일 기록의 한 구절 — 상태(`brief_state.mail_status`)를 말로. 판 끝 · status 가 같은 말을 쓴다."""
    why = mail.get("why") or ""
    if status == MAIL_SENT:
        return f"본인 메일로 보냈다({hhmm(mail.get('at'))})"
    if status == MAIL_RETRYING:
        return f"메일을 아직 못 보냈다 — {why}. {end_words(end, at)} 까지 판마다 다시 보낸다"
    if status == MAIL_FAILED:
        return f"메일로 못 보냈다 — {why}({mail.get('tries') or 1}번 해 봤다)"
    return f"메일을 보냈는지 확인하지 못했다 — {why}. 다시 보내지 않는다 — 받은편지함에서 보시고, 없으면 PC 의 보고 창에서 보신다"


def mail_failure_words(t: str, status: str, why: str) -> str:
    """못 간 메일 한 칸의 줄 — 「HH:MM 보고는 메일로 못 보냈다 · 보냈는지 확인하지 못했다 — 까닭」."""
    if status == MAIL_FAILED:
        return f"{t} 보고는 메일로 못 보냈다 — {why}"
    return f"{t} 보고는 메일로 보냈는지 확인하지 못했다 — {why}"


def away_line(item: tuple[Any, ...]) -> str:
    """자리 밖에서 보기의 판 끝 한 줄 — 표지를 못 읽었다 · 앞 판의 표지로 칸을 맺었다 · 다음 판에 둔다 · 표지를 못 굳혔다 · 한 통 보내 봤다."""
    kind = item[0]
    if kind == AWAY_MARK_UNREAD:
        return f"[자리 밖에서 보기 — 「보내는 중」 표지를 못 읽어 이번 판에는 안 보냈다({item[1]}) — 다음 판이 다시 읽는다]"
    if kind == AWAY_LEFT:
        return f"[자리 밖에서 보기 — {item[1]} 보고: 메일을 보냈는지 확인하지 못했다 — {item[2]}. 다시 보내지 않는다]"
    if kind == AWAY_LATE:
        return f"[자리 밖에서 보기 — {item[1]} 보고: 이번 판에는 시간이 모자라 다음 판에 보낸다]"
    if kind == AWAY_MARK_FAILED:
        return f"[자리 밖에서 보기 — {item[1]} 보고: 「보내는 중」을 못 굳혀 이번 판에는 안 보냈다({item[2]})]"
    _, t, status, mail, end, at = item
    return f"[자리 밖에서 보기 — {t} 보고: {mail_words(status, mail, end, at)}]"


def told_words(told: Told, before: list[str]) -> list[str]:
    """보고가 아직 말하지 않은 칸(`brief_state.untold`)의 줄 — 건너뛴 칸 · 글 없이 끝난 칸 · 못 띄운 칸, 그 앞날의 줄(`before` — 말할
    차례일 때), 못 간 메일 차례로."""
    out = []
    for item in told.items:
        if item[0] == EMPTY:
            out.append(f"{item[1]} 보고는 {hhmm(item[2])}에 띄웠는데 보고 글이 안 섰다(띄운 판이 글을 못 남기고 끝났다)")
        elif item[0] == FAILED:
            out.append(f"{item[1]} 보고는 {hhmm(item[2])}에 띄우지 못했다 — {item[3]}")
        else:
            out.append(f"{item[1]} 보고는 {SKIP_WORDS[item[2]]} 건너뛰었다")
    return [*(before if told.with_before else []), *out] + [mail_failure_words(t, state, why) for _, t, state, why in told.mails]


def dated_lines(day_label: str, lines: list[str]) -> list[str]:
    """지난날의 줄 — 줄마다 그날(「M/D」)을 앞에 단다."""
    return [f"{day_label} {line}" for line in lines]


def looked(tries: list[dict[str, Any]]) -> str:
    """그 칸에서 살펴본 것의 한 구절 — 처음 · 마지막 때와 수, 답마다의 수(손 오류를 「세션 없음」에 섞지 않는다)."""
    counts = " · ".join(f"{word} {sum(t.get('session') == key for t in tries)}"
                        for key, word in TRY_WORDS.items() if any(t.get("session") == key for t in tries))
    return f"{hhmm(tries[0]['at'])}부터 {hhmm(tries[-1]['at'])}까지 {len(tries)}번 살펴봤다({counts})"


def slot_line(v: Slot, state: str, cause: str, login: dict[str, Any]) -> str:
    """status 의 한 시각 — 칸의 상태(`state` — `brief_state.status_state`) · 건너뛴 까닭(`cause`) · 그 칸의 띄우기 앞에 부른 입구의 끝(`login`
    — `brief_state.slot_login`)을 말로: 섰다 · 띄웠다 · 짓는 중 · 아직 · 기다린다 · 건너뛰었다와 다음 걸음. 셈은 안 한다."""
    tries, launched, made, t = v.slot.get("tries") or [], v.slot.get("launched"), v.made, v.t
    until = end_words(v.end, v.start)
    if state == MADE:
        if v.made_how == MADE_SCAN:
            return f"보고 글이 섰다 — {made[-1].name}(스캔이 {hhmm(launched['at'])}에 띄웠다)"
        if v.made_how == MADE_EARLY:
            return f"{v.early_at}에 지은 보고 글({made[-1].name})이 이 시각의 보고를 대신한다 — {t}에는 안 띄운다"
        return f"보고 글이 섰다 — {made[-1].name}"
    if state == FAILED:
        return f"{hhmm(launched['at'])}에 띄우지 못했다 — {launched['error']}. 다음: 대화에서 「보고해 줘」 하신다"
    if state == WRITING:
        return f"{hhmm(launched['at'])}에 띄웠다 — 보고를 짓는 중이다(출력 {launched.get('log')})"
    if state in (EMPTY, LEFT):
        return (f"{hhmm(launched['at'])}에 띄웠는데 보고 글이 안 섰다 — 출력 {launched.get('log')}" + (f" 의 끝 줄: {v.tail}" if v.tail else " 이 비었다")
                + ". 다음: 대화에서 「보고해 줘」 하신다")
    if state == UNSCHEDULED:
        return "일일 보고의 시계가 작업 스케줄러에 안 걸려 있어 이 시각의 보고는 안 뜬다(위 ⚠)"
    if state == AHEAD:
        return f"아직 안 됐다 — 그 뒤 {until} 까지 사내 세션이 서는 첫 판에 띄운다"
    if state == PAST_SET:
        return "오늘은 걸기 전에 이미 지난 시각이라 내일부터 뜬다"
    if state == SKIPPED:
        seen = f" — {looked(tries)}" if cause != NO_RUN else ""
        return (f"{until} 까지 {SKIP_WORDS[cause]} 보고를 건너뛰었다{seen}(이 시각은 오늘 다시 안 띄운다). 다음: {C.NEXT_LOGIN} 하신 뒤 "
                "「보고해 줘」 하신다")
    if state == RUNNING:
        return "스캔이 앞서 띄운 보고가 아직 도는 중이다 — 끝나면 이 시각을 살펴본다"
    if state == WAITING and login.get("ok") is True:
        return (f"사내 세션이 없어 {hhmm(login['at'])}에 스스로 로그인했지만 그 뒤 메일함 읽기가 세션 없이 졌다(그 사이 다른 자리에서 "
                f"로그인했을 수 있다) — 이 시각에는 다시 로그인하지 않고 {until} 까지 메일함을 산 세션에서 읽는 첫 판에 띄운다")
    if state == WAITING:
        return (f"사내 세션이 없어 아직 못 띄웠다 — {looked(tries)}. {until} 까지 사내 세션이 서는 첫 판에 띄운다 — {C.NEXT_LOGIN} "
                "하시거나 다른 사내 앱 스킬이 세션을 새로 받으면 그 뒤 첫 판이다")
    return f"{t} 이 지났다 — 다음 판에 사내 세션을 살펴보고 띄운다({until} 까지)"


def unset_lines(problem: str) -> list[str]:
    """보고 예약이 안 걸렸을 때 status 의 줄 — 시각표를 못 읽은 까닭(`problem`)이 있으면 그것과 다시 거는 길."""
    if problem:
        return [f"  보고 예약: ⚠ {problem} — 다음: clock.py at HH:MM 으로 다시 건다"]
    return [f"  보고 예약: 안 걸었다 — 걸려면 clock.py register --at HH:MM [HH:MM …](기본 {C.BRIEF_AT_DEFAULT})"]


def head_lines(setting: dict[str, Any], away: dict[str, Any], wins: list[tuple[str, datetime, datetime, datetime]], task: bool | None, claude_ok: bool,
               tight: str) -> list[str]:
    """status 의 보고 예약 머리 줄 — 언제 · 로그인 · claude, 자리 밖에서 보기, 그리고 작업이 안 걸렸다(`task` False) · claude 가 없다 ·
    틈이 모자라다(`tight` — 거절의 말)의 경고."""
    times = setting["times"]
    lines = [f"  보고 예약: {window_words(wins)} 일일 보고를 띄운다 · {LOGIN_WORDS} · claude {setting['claude']}"]
    lines.append(f"  자리 밖에서 보기: 켰다({tm.seoul(tm.parse(away.get('chosen')), '%m/%d %H:%M')}) — 사람 없이 띄운 보고를 칸마다 한 통 본인 주소"
                 f"({away.get('address')})로 보낸다" if away.get("on") else "  자리 밖에서 보기: 꺼져 있다 — 사람 없는 보고는 아무것도 안 보낸다")
    if task is False:
        lines.append("  ⚠ 일일 보고의 시계가 작업 스케줄러에 안 걸려 있어 정한 시각의 보고가 안 뜬다 — 시계 판이 보고를 띄운다. 다음: clock.py "
                     "register --at " + " ".join(times))
    if not claude_ok:
        lines.append("  ⚠ 그 claude 가 없다 — 다음: clock.py at HH:MM --claude <claude.exe 의 자리> 로 다시 준다")
    if tight:
        lines.append(f"  ⚠ {tight} — 이대로는 그 시각에 안 띄운다. 다음: clock.py at 으로 시각을 띄어 다시 건다")
    return lines


def day_lines(before: list[str], logins: list[tuple[str, dict[str, Any]]], when: str) -> list[str]:
    """status 의 그날 장부 줄 — 지난날 건너뛴 칸의 줄(`before`) · 오늘 스스로 로그인의 입구를 부른 끝마다 한 줄(`logins` —
    `brief_state.day_logins` · 뒤 시각의 칸에서 부른 것은 그 시각을 단다)."""
    lines = [f"  지난날: {line}" for line in before]
    for t, signed in logins:
        of = f"({t} 보고 앞)" if t else ""
        lines.append(f"  오늘({when}): {hhmm(signed['at'])}에 스스로 로그인했다{of}" if signed.get("ok") else
                     f"  오늘({when}): {hhmm(signed['at'])}에 스스로 로그인이 안 섰다{of} — {signed.get('said')}(이 보고 시각에는 다시 안 한다)")
    return lines


def slot_status_line(when: str, t: str, line: str, mail: tuple[str, dict[str, Any]] | None, end: datetime, at: datetime) -> str:
    """status 의 한 시각의 줄 — 칸의 말(`line`)에 메일 기록의 구절(`mail` — (상태, 기록))을 붙인다."""
    return f"  오늘({when}) {t}: {line}" + (f" · {mail_words(mail[0], mail[1], end, at)}" if mail else "")
