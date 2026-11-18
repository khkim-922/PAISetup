"""아침 보고 — 스캔 판이 사용자가 정한 때 뒤에 일일 보고(스킬 daily-brief)를 사람 없이 한 번 띄운다. 설정 · 그날의 살펴보기 · 띄우기 · 권한.

    setting, problem = load(folder)              # brief.json — 안 걸었으면 (None, ""), 못 읽으면 (None, 까닭)
    save(folder, at="07:30", claude=path) · clear(folder)
    line = after_run(state, folder, evidence, hand, at)   # 판 끝 — 보고 시각부터 마감까지 사내 세션이 살아 있는 첫 판에 띄운다. 할 말이 없으면 ""
    lines = describe(state, folder, at)          # status 가 말할 줄
    words = window_words("07:30")                # 거는 말 · status 가 함께 쓰는 「언제 띄우나」 한 구절
    refused = too_late("13:00")                  # 마감에 닿는 보고 시각이면 거절의 말 — 받으면 ""
    cmd, settings, prompt = plan(setting, hand, folder)   # 띄울 명령 · 권한 · 부탁 글(띄우기와 `--dry-run` 이 같은 것을 쓴다)

언제 띄우나 · 띄운 claude 에 무엇을 여나 · 왜 로그인하지 않나는 `references/DESIGN.md` 「아침 보고」가 든다.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any

import scan_const as C
import scan_hand as H
import scan_store as st

LIVE, LOST, ERROR = "live", "lost", "error"          # 살펴보기의 답 — 사내 세션이 살았다 · 없다 · 손이 답을 못 냈다
LOG_TAIL_CHARS = 200                                 # status 가 띄운 보고의 출력에서 옮겨 보이는 끝 줄의 글자 수
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_DIR.parents[1]                  # 이 스킬 · 일일 보고 스킬이 나란히 선 스킬 뿌리


# ── 설정 ─────────────────────────────────────────────────────────────────────

def clock(text: str) -> str | None:
    """「H:MM」 · 「HH:MM」 → 「HH:MM」. 꼴이 아니면 None."""
    try:
        return datetime.strptime(text.strip(), "%H:%M").strftime("%H:%M")
    except (ValueError, AttributeError):
        return None


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
    """(설정, 못 읽은 까닭). 안 걸었으면 (None, "")."""
    try:
        data = json.loads((folder / C.BRIEF_FILE).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, ""
    except (OSError, ValueError) as exc:
        return None, f"{C.BRIEF_FILE} 를 못 읽었다({type(exc).__name__})"
    if (not isinstance(data, dict) or data.get("format") != C.BRIEF_FORMAT or not clock(str(data.get("at") or ""))
            or not data.get("claude")):
        return None, f"{C.BRIEF_FILE} 의 꼴이 이 스크립트와 다르다"
    return data, ""


def save(folder: pathlib.Path, at: str, claude: pathlib.Path) -> None:
    st.write_json(folder / C.BRIEF_FILE, {"format": C.BRIEF_FORMAT, "at": at, "claude": str(claude), "set": st.stamp(st.now())})


def clear(folder: pathlib.Path) -> bool:
    """보고를 내린다 — 걸려 있었으면 True."""
    try:
        (folder / C.BRIEF_FILE).unlink()
        return True
    except FileNotFoundError:
        return False


# ── 그날 ─────────────────────────────────────────────────────────────────────

def seoul_date(at: datetime) -> str:
    return st.seoul(at, "%Y-%m-%d")


def on_day(text: str, at: datetime) -> datetime:
    """서울 날짜 `at` 의 그 시각(「HH:MM」)."""
    hour, minute = map(int, clock(text).split(":"))
    return at.astimezone(st.KST).replace(hour=hour, minute=minute, second=0, microsecond=0)


def due_time(setting: dict[str, Any], at: datetime) -> datetime:
    return on_day(setting["at"], at)


def until_clock() -> str:
    """보고를 기다리는 마감 「HH:MM」 — `BRIEF_UNTIL`. 검사가 하루 어느 때에 돌아도 같은 판을 재게 `BRIEF_UNTIL_ENV` 가 바꾼다."""
    return clock(os.environ.get(C.BRIEF_UNTIL_ENV, "")) or C.BRIEF_UNTIL


def until_time(at: datetime) -> datetime:
    return on_day(until_clock(), at)


def too_late(at_text: str) -> str:
    """보고 시각이 마감에 닿으면 거절의 말 — 그 시각으로 걸면 기다릴 틈이 없어 보고가 날마다 안 뜬다. 받으면 ""."""
    if at_text < until_clock():
        return ""
    return f"보고 시각 {at_text} 이 마감 {until_clock()}(서울)에 닿는다 — 보고 시각부터 마감 사이에 띄우므로 마감보다 이른 시각을 준다"


def window_words(at_text: str) -> str:
    """언제 띄우나의 한 구절 — 거는 말과 status 가 같은 말을 쓴다."""
    return f"날마다 {at_text}부터 {until_clock()}(서울) 사이 사내 세션이 서는 첫 판에"


def day_of(state: dict[str, Any], at: datetime, keep: bool = True) -> dict[str, Any]:
    """그날의 살펴보기 — 서울 날짜가 바뀌었으면 새 판. `keep` 이면 지금 모습에 넣는다(판 안에서만 — status 는 안 바꾼다)."""
    got = state.get("brief")
    if not isinstance(got, dict) or got.get("date") != seoul_date(at):
        got = {"date": seoul_date(at), "tries": [], "launched": None}
        if keep:
            state["brief"] = got
    return got


def made_today(at: datetime) -> list[pathlib.Path]:
    """그날 보고 글 — 사용자 폴더의 `brief-<서울 날짜>-*.md`(이름 차례)."""
    return sorted(st.home().glob(C.BRIEF_MADE.format(date=seoul_date(at))))


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


def waiting(setting: dict[str, Any] | None, day: dict[str, Any], at: datetime, folder: pathlib.Path) -> str:
    """지금 살펴보지 않는 까닭 — 살펴볼 때면 ""."""
    if setting is None:
        return "off"
    if at < due_time(setting, at):
        return "early"
    if made_today(at):
        return "made"
    if day.get("launched"):
        return "launched"
    if lock_held(folder, at):
        return "running"
    if at >= until_time(at):
        return "closed"
    return ""


def spaced(day: dict[str, Any], at: datetime) -> bool:
    """손에 다시 물어도 되나 — 그날 마지막 살펴보기에서 `BRIEF_TRY_GAP_MIN` 분이 지났다(작업이 더 자주 깨워도 SSO 를 촘촘히 안 두드린다)."""
    tries = day.get("tries") or []
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


def after_run(state: dict[str, Any], folder: pathlib.Path, evidence: str | None, hand: pathlib.Path | None, at: datetime) -> str:
    """판 끝 — 살펴볼 때면 사내 세션을 보고 살아 있으면 띄운다. `evidence` 는 그 판이 손에서 받은 답이라 늘 쓰고(세션 파일이 새로
    쓰여 판이 돌았으면 그 판에 바로 띄운다), 답이 없는 판(None)만 틈(`spaced`)을 지켜 손에 묻는다. 로그인은 안 한다.
    `state` 의 그날 칸을 고치고 파일 쓰기는 부르는 쪽 몫이다. 내는 것 — 판 끝에 찍을 한 줄(할 말이 없으면 "")."""
    setting, _ = load(folder)
    day = day_of(state, at)
    if waiting(setting, day, at, folder):
        return ""
    if evidence is None:
        if not spaced(day, at):
            return ""
        evidence = look(hand)
        if evidence == LIVE:
            state.pop("session", None)       # 세션이 살아 있으니 끊겼다는 기다림을 걷는다 — 다음 주기에 스캔이 바로 돈다
    day["tries"].append({"at": st.stamp(at), "session": evidence})
    if evidence == LIVE:
        day["launched"] = launch(setting, hand, folder, at)
        got = day["launched"]
        if got.get("error"):
            return f"[아침 보고 — 띄우지 못했다: {got['error']}]"
        return f"[아침 보고 — 사내 세션이 있어 일일 보고를 띄웠다 · 출력 {got['log']}]"
    return f"[아침 보고 — {MISS_WORDS[evidence]} 못 띄웠다 · {until_clock()} 까지 사내 세션이 서는 첫 판에 띄운다]"


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
    got += [f"{run(p['reader'])} *", f'{run(p["window"])} --no-open --dir "{p["home"].as_posix()}" *', f"{run(p['work_writer'])} *",
            f'{run(p["ticks"])} --dir "{p["home"].as_posix()}"']
    return got


PROMPT = """사람 없는 예약 실행이다 — 메일함 스캔이 {at} 뒤 판에서 사내 세션이 살아 있는 것을 보고 띄웠다. 오늘의 일일 보고를 지어 남긴다.

0. 맨 먼저 열린 명령의 ticks.py 로 보고 창의 「끝났음」 표시를 지난 보고 글에 거둔다 — 업무 파악이 그 절을 읽는다. Edge 에 못 닿으면(종료 3) 그대로 넘어간다.
1. 그 뒤 스킬 mailbox-work 의 글 {work_lane} 를 읽고 「두 길」대로 업무 파악을 한다 — {writer} where 가 업무 파일이 있다고 하면 「이어 파악」, 없으면 처음 파악(그 스킬 폴더의 first-understanding.md)이고, 「사람이 없을 때」 절이 이 실행의 경계다. 업무 파일은 {writer} write 로만 쓴다 — 이 실행에는 파일을 쓰는 도구가 없다.
2. 그 뒤 스킬 daily-brief 의 글 {brief_lane} 를 읽고 그 글대로 짓는다 — 「사람 없는 예약 실행」 절이 이 실행의 경계다.
3. 회사 메일 · 일정 손을 부르는 꼴은 그 스킬의 글({skills})이, 메일함 스캔이 쌓은 것을 읽는 꼴은 {scan_skill}/SKILL.md 가 든다.
4. 이 실행에서 열린 명령은 아래 꼴뿐이다 — 경로와 따옴표까지 그대로 쓰고, 「…」 자리에 인자를 둔다. 그 밖의 명령은 막혀 있다.
{commands}
5. 사용자 폴더는 {home} 이다(지금 자리) — 업무 파일 {work_name} 와 지난 보고 글 brief-….md 가 여기 있다.
"""


def plan(setting: dict[str, Any], hand: pathlib.Path | None, folder: pathlib.Path) -> tuple[list[str], dict[str, Any], str]:
    """(띄울 명령, `--settings` 로 줄 권한, 표준 입력으로 줄 부탁 글)."""
    p = places(hand)
    opened = commands(p)
    settings = {"permissions": {"allow": [f"Bash({c})" for c in opened], "deny": list(C.BRIEF_DENY)}}
    dirs = [p[k] for k in ("brief_skill", "work_skill", "scan_skill", "mail_skill", "calendar_skill") if k in p and p[k].is_dir()]
    cmd = [str(setting["claude"]), "-p", "--settings", str(folder / C.BRIEF_SETTINGS_FILE), "--permission-mode", "dontAsk",
           "--tools", C.CLAUDE_TOOLS, "--strict-mcp-config", "--no-session-persistence",
           *[a for d in dirs for a in ("--add-dir", str(d))]]
    skills = " · ".join(f"{p[k].as_posix()}/SKILL.md" for k in ("mail_skill", "calendar_skill") if k in p)
    prompt = PROMPT.format(at=setting["at"], brief_lane=(p["brief_skill"] / C.LANE_FILE).as_posix(),
                           skills=skills or "회사 메일 스킬 company-mail", work_lane=(p["work_skill"] / C.LANE_FILE).as_posix(),
                           writer=pathlib.Path(*C.WORK_WRITER).name, work_name=C.WORK_FILE,
                           scan_skill=p["scan_skill"].as_posix(), home=p["home"].as_posix(),
                           commands="\n".join(f"   {c.replace(' *', ' …')}" for c in opened))
    return cmd, settings, prompt


def _detached() -> dict[str, Any]:
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def launch(setting: dict[str, Any], hand: pathlib.Path | None, folder: pathlib.Path, at: datetime) -> dict[str, Any]:
    """권한 · 부탁 글을 사용자 폴더에 지어 claude 를 띄우고 기다리지 않는다(출력은 `BRIEF_LOG_FILE`). 내는 것 — {at, pid, log} 이나 {at, error}."""
    cmd, settings, prompt = plan(setting, hand, folder)
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

def hhmm(stamp: str | None) -> str:
    return st.seoul(st.parse(stamp), "%H:%M")


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
    """그날 살펴본 것의 한 구절 — 처음 · 마지막 때와 수, 답마다의 수(손 오류를 「세션 없음」에 섞지 않는다)."""
    counts = " · ".join(f"{word} {sum(t.get('session') == key for t in tries)}"
                        for key, word in TRY_WORDS.items() if any(t.get("session") == key for t in tries))
    return f"{hhmm(tries[0]['at'])}부터 {hhmm(tries[-1]['at'])}까지 {len(tries)}번 살펴봤다({counts})"
MISS_WORDS = {LOST: "사내 세션이 없어", ERROR: "손이 사내 세션을 못 살펴봐"}   # 판 끝 한 줄 — 손 오류를 「세션 없음」으로 말하지 않는다


def describe(state: dict[str, Any] | None, folder: pathlib.Path, at: datetime) -> list[str]:
    """status 가 말할 줄 — 걸었나 · 오늘 띄웠나 · 안 띄웠으면 왜와 다음 걸음."""
    setting, problem = load(folder)
    if setting is None:
        if problem:
            return [f"  아침 보고: ⚠ {problem} — 다음: brief --at HH:MM 으로 다시 건다"]
        return [f"  아침 보고: 안 걸었다 — 걸려면 register --brief-at HH:MM(기본 {C.BRIEF_AT_DEFAULT})"]
    lines = [f"  아침 보고: {window_words(setting['at'])} 일일 보고를 띄운다 · claude {setting['claude']}"]
    if not pathlib.Path(setting["claude"]).is_file():
        lines.append("  ⚠ 그 claude 가 없다 — 다음: brief --at HH:MM --claude <claude.exe 의 자리> 로 다시 준다")
    day = day_of(state or {}, at, keep=False)
    tries, launched, made = day.get("tries") or [], day.get("launched"), made_today(at)
    when = st.seoul(at, "%m/%d")
    if made:
        by = f"(스캔이 {hhmm(launched['at'])}에 띄웠다)" if launched and not launched.get("error") else ""
        lines.append(f"  오늘({when}): 보고 글이 섰다 — {made[-1].name}{by}")
    elif launched and launched.get("error"):
        lines.append(f"  오늘({when}): {hhmm(launched['at'])}에 띄우지 못했다 — {launched['error']}. 다음: 대화에서 「아침 보고 해 줘」 하신다")
    elif launched:
        tail = last_line(pathlib.Path(launched.get("log") or ""))
        if lock_held(folder, at) and not tail:
            lines.append(f"  오늘({when}): {hhmm(launched['at'])}에 띄웠다 — 보고를 짓는 중이다(출력 {launched.get('log')})")
        else:
            lines.append(f"  오늘({when}): {hhmm(launched['at'])}에 띄웠는데 보고 글이 안 섰다 — 출력 {launched.get('log')}"
                         + (f" 의 끝 줄: {tail}" if tail else " 이 비었다") + ". 다음: 대화에서 「아침 보고 해 줘」 하신다")
    elif too_late(setting["at"]):
        lines.append(f"  ⚠ {too_late(setting['at'])} — 이대로는 날마다 안 띄운다. 다음: brief --at HH:MM 으로 앞당긴다")
    elif at < due_time(setting, at):
        lines.append(f"  오늘({when}): {setting['at']} 이 아직 안 됐다 — 그 뒤 {until_clock()} 까지 사내 세션이 서는 첫 판에 띄운다")
    elif lock_held(folder, at):
        lines.append(f"  오늘({when}): 스캔이 앞서 띄운 보고가 아직 도는 중이다")
    elif at >= until_time(at):
        if tries:
            lines.append(f"  오늘({when}): {until_clock()} 까지 사내 세션이 안 서 보고를 건너뛰었다 — {looked(tries)}(오늘은 다시 안 띄운다). "
                         "다음: 대화에서 스킬 ep-login 으로 EP 로그인을 하신 뒤 「아침 보고 해 줘」 하신다")
        else:
            lines.append(f"  오늘({when}): {setting['at']} 부터 {until_clock()} 사이에 스캔 판이 안 돌아 보고를 못 띄웠다(PC 꺼짐 · 로그온 전 · "
                         "작업이 꺼짐). 다음: 대화에서 「아침 보고 해 줘」 하신다")
    elif tries:
        lines.append(f"  오늘({when}): 사내 세션이 없어 아직 못 띄웠다 — {looked(tries)}. {until_clock()} 까지 사내 세션이 서는 첫 판에 띄운다 — "
                     "대화에서 스킬 ep-login 으로 EP 로그인을 하시거나 다른 사내 앱 스킬이 세션을 새로 받으면 그 뒤 첫 판이다")
    else:
        lines.append(f"  오늘({when}): {setting['at']} 이 지났다 — 다음 판에 사내 세션을 살펴보고 띄운다({until_clock()} 까지)")
    return lines
