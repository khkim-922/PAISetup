"""claude 띄우기 — 사람 없는 보고에 띄울 claude 의 명령 · 열린 명령(권한) · 부탁 글을 짓고, 환경을 손질해 떼어 띄운 뒤 기다리지
않는다. 맡긴 일의 손(`handed_run`)도 claude 찾기 · 환경 손질 · 떼어 띄우기를 여기서 쓴다.

    cmd, settings, prompt = plan(setting, hand, folder)      # 띄울 명령 · 권한 · 부탁 글(띄우기와 `--dry-run` 이 같은 것을 쓴다)
    launched = launch(setting, hand, folder, at, slot, skipped)   # {at, pid, log} 이나 {at, error}
    claude = find_claude(explicit)               # `--claude` 가 가리키는 파일, 없으면 PATH — 못 찾으면 None
    env = child_env(dict(os.environ))            # 겹친 세션의 표지를 걷고, 루프백 프록시를 지나면 보고의 표 머리를 싣는다
    subprocess.Popen(cmd, **detached())          # 떼어 띄우는 인자 — 부른 쪽이 끝나도 띄운 것이 산다

띄운 claude 에 무엇을 여나는 `references/DESIGN.md` 「정한 시각의 보고」가 든다.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

import scan_const as C
import scan_store as st
from window_link import BRIEF_DIR, TICKS, WINDOW


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


def places(hand: pathlib.Path | None) -> dict[str, pathlib.Path]:
    """띄운 보고가 쓰는 자리 — 손 · 일정 손 · 회의실 손 · 스캔의 읽는 명령 · 보고 창 · 업무 파일의 쓰는 손 · 스킬 폴더 · 사용자 폴더. 없는 일정 ·
    회의실 손은 뺀다."""
    got = {"home": st.home(), "reader": C.SCRIPT_DIR / "reader.py", "scan_skill": C.SCRIPT_DIR.parent,
           "brief_skill": BRIEF_DIR, "work_skill": C.SKILLS_ROOT / C.WORK_SKILL,
           "window": WINDOW, "ticks": TICKS,
           "work_writer": C.SKILLS_ROOT / C.WORK_SKILL / pathlib.Path(*C.WORK_WRITER)}
    if hand is not None:
        got["mail"], got["mail_skill"] = hand, hand.parents[1]
        calendar = hand.parents[2] / C.CALENDAR_SKILL / pathlib.Path(*C.CALENDAR_SCRIPT)
        if calendar.is_file():
            got["calendar"], got["calendar_skill"] = calendar, calendar.parents[1]
        meeting = hand.parents[2] / C.MEETING_SKILL / pathlib.Path(*C.MEETING_SCRIPT)
        if meeting.is_file():
            got["meeting"], got["meeting_skill"] = meeting, meeting.parents[1]
    return got


def commands(p: dict[str, pathlib.Path]) -> list[str]:
    """열린 명령 — 권한 규칙의 꼴(끝의 「 *」는 뒤에 인자가 온다). 경로는 「C:/…」 꼴로 따옴표에 싼다 — Git Bash 와 파이썬이 함께 읽는다."""
    def run(script: pathlib.Path) -> str:
        return f'python -X utf8 -I "{script.as_posix()}"'
    got = [f"{run(p['mail'])} {r}" for r in C.MAIL_READS] if "mail" in p else []
    got += [f"{run(p['calendar'])} {r}" for r in C.CALENDAR_READS] if "calendar" in p else []
    got += [f"{run(p['meeting'])} {r}" for r in C.MEETING_READS] if "meeting" in p else []
    got += [f"{run(p['reader'])} *", f'{run(p["window"])} --dir "{p["home"].as_posix()}" *', f"{run(p['work_writer'])} *",
            f'{run(p["ticks"])} --dir "{p["home"].as_posix()}"']
    return got


PROMPT = """사람 없는 예약 실행이다 — 메일함 스캔이 보고 시각 {at} 뒤 판에서 사내 세션이 살아 있는 것을 보고 띄웠다. 지금의 일일 보고를 지어 창으로 띄워 둔다 — 사용자가 오셔서 그 창을 본다.

0. 맨 먼저 열린 명령의 ticks.py 로 보고 창에서 누르신 것을 거둔다 — 업무 파악이 그 절을 읽고, 끝 줄들이 올리지 않을 것과 미룬 것을 댄다. 로그인 Edge 에 못 닿아 Exit code 3 으로 끝나도 그대로 넘어간다.
1. 그 뒤 스킬 mailbox-work 의 글 {work_lane} 를 읽고 「두 길」대로 업무 파악을 한다 — {writer} where 가 업무 파일이 있다고 하면 「이어 파악」, 없으면 처음 파악(그 스킬 폴더의 first-understanding.md)이고, 「사람이 없을 때」 절이 이 실행의 경계다. 업무 파일은 {writer} write 로만 쓴다 — 이 실행에는 파일을 쓰는 도구가 없다.
2. 그 뒤 스킬 daily-brief 의 글 {brief_lane} 를 읽고 그 글대로 짓는다 — 「사람 없는 예약 실행」 절이 이 실행의 경계다.
3. 회사 메일 · 일정 · 회의실 손을 부르는 꼴은 그 스킬의 글({skills})이, 메일함 스캔이 쌓은 것을 읽는 꼴은 {scan_skill}/SKILL.md 가 든다.
4. 이 실행에서 열린 명령은 아래 꼴뿐이다 — 경로와 따옴표까지 그대로 쓰고, 「…」 자리에 인자를 둔다. 「…」 앞은 한 글자도 바꾸지 않는다 — 보고 창의 --mailbox 같은 인자와 heredoc 은 「…」 자리, 곧 그 뒤에 둔다. 그 밖의 명령은 막혀 있다.
{commands}
   종료 값은 Bash 의 결과가 댄다(0 이 아니면 결과 머리에 「Exit code N」) — 명령 뒤에 `; echo $?` 같은 것을 덧붙이지 않는다. 한 부름에 이은 명령 가운데 하나라도 위 꼴이 아니면 그 부름 전체가 막힌다.
   「Permission to use Bash has been denied」는 그 부름의 명령 글이 위 꼴과 달랐다는 뜻이지 Bash 가 꺼진 것이 아니다 — 덧붙인 것을 걷고 위 꼴 그대로 다시 부른다.
5. 사용자 폴더는 {home} 이다(지금 자리) — 업무 파일 {work_name} 와 지난 보고 글 brief-….md 가 여기 있다.
{missed}"""
MISSED = ("6. 건너뛴 보고 · 못 간 메일 — 아래는 보고 없이 지나간 시각과 본인 메일로 못 간 보고다. 「이 보고가 본 데」에 그대로 적는다(어느 "
          "시각을 왜 건너뛰었나 · 어느 보고가 왜 메일로 안 갔나):\n{lines}\n")


def plan(setting: dict[str, Any], hand: pathlib.Path | None, folder: pathlib.Path, at: str | None = None,
         skipped: list[str] | None = None) -> tuple[list[str], dict[str, Any], str]:
    """(띄울 명령, `--settings` 로 줄 권한, 표준 입력으로 줄 부탁 글). `at` 은 띄우는 칸의 시각(없으면 첫 시각), `skipped` 는 그 앞에 건너뛴 시각."""
    p = places(hand)
    opened = commands(p)
    settings = {"permissions": {"allow": [f"Bash({c})" for c in opened], "deny": list(C.BRIEF_DENY)}}
    dirs = [p[k] for k in ("brief_skill", "work_skill", "scan_skill", "mail_skill", "calendar_skill", "meeting_skill") if k in p and p[k].is_dir()]
    cmd = [str(setting["claude"]), "-p", "--settings", str(folder / C.BRIEF_SETTINGS_FILE), "--permission-mode", "dontAsk",
           "--tools", C.CLAUDE_TOOLS, "--strict-mcp-config", "--no-session-persistence",
           *[a for d in dirs for a in ("--add-dir", str(d))]]
    skills = " · ".join(f"{p[k].as_posix()}/SKILL.md" for k in ("mail_skill", "calendar_skill", "meeting_skill") if k in p)
    prompt = PROMPT.format(at=at or setting["times"][0], brief_lane=(p["brief_skill"] / C.LANE_FILE).as_posix(),
                           skills=skills or "회사 메일 스킬 company-mail", work_lane=(p["work_skill"] / C.LANE_FILE).as_posix(),
                           writer=pathlib.Path(*C.WORK_WRITER).name, work_name=C.WORK_FILE,
                           scan_skill=p["scan_skill"].as_posix(), home=p["home"].as_posix(),
                           commands="\n".join(f"   {c.replace(' *', ' …')}" for c in opened),
                           missed=MISSED.format(lines="\n".join(f"   {x}" for x in skipped)) if skipped else "")
    return cmd, settings, prompt


def detached() -> dict[str, Any]:
    """떼어 띄우는 `Popen` 인자 — 창 없이, 부른 프로세스와 다른 묶음으로 띄워 부른 쪽이 끝나도 띄운 것이 산다."""
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _loopback_proxy(env: dict[str, str]) -> bool:
    """claude 의 요청이 루프백 프록시를 지나나 — `ANTHROPIC_BASE_URL` 이 `http://<루프백>:<포트>/…` 일 때만."""
    try:
        parts = urlsplit(env.get(C.BASE_URL_ENV) or "")
        port = parts.port
    except ValueError:
        return False
    return parts.scheme == "http" and parts.hostname in C.LOOPBACK_HOSTS and bool(port)


def child_env(env: dict[str, str]) -> dict[str, str]:
    """띄울 claude 의 환경 — 겹친 세션의 표지를 걷고, 루프백 프록시를 지나면 보고의 표 머리를 싣는다(`C.RUNNER_HEADER`).
    이미 든 다른 머리 줄은 그대로 둔다. 프록시가 없는 자리(사외 · 게이트웨이 직결)는 머리를 안 싣는다."""
    out = {k: v for k, v in env.items() if k not in C.NESTED_ENV}
    if _loopback_proxy(out):
        lines = [line for line in (out.get(C.CUSTOM_HEADERS_ENV) or "").splitlines()
                 if line.strip() and line.split(":", 1)[0].strip().lower() != C.RUNNER_HEADER]
        out[C.CUSTOM_HEADERS_ENV] = "\n".join(lines + [f"{C.RUNNER_HEADER}: {C.RUNNER_HEADER_VALUE}"])
    return out


def launch(setting: dict[str, Any], hand: pathlib.Path | None, folder: pathlib.Path, at: datetime, slot: str | None = None,
           skipped: list[str] | None = None) -> dict[str, Any]:
    """권한 · 부탁 글을 사용자 폴더에 지어 claude 를 띄우고 기다리지 않는다(출력은 `BRIEF_LOG_FILE`). 내는 것 — {at, pid, log} 이나 {at, error}."""
    cmd, settings, prompt = plan(setting, hand, folder, slot, skipped)
    st.write_json(folder / C.BRIEF_SETTINGS_FILE, settings)
    (folder / C.BRIEF_PROMPT_FILE).write_text(prompt, encoding="utf-8")
    log = folder / C.BRIEF_LOG_FILE
    env = child_env(dict(os.environ))
    try:
        with (folder / C.BRIEF_PROMPT_FILE).open("rb") as given, log.open("wb") as out:
            proc = subprocess.Popen(cmd, cwd=str(st.home()), stdin=given, stdout=out, stderr=subprocess.STDOUT, env=env, close_fds=True,
                                    **detached())
    except OSError as exc:
        return {"at": st.stamp(at), "error": f"{type(exc).__name__}: {exc}"}
    st.write_json(folder / C.BRIEF_LOCK_FILE, {"started": st.stamp(at), "pid": proc.pid})
    return {"at": st.stamp(at), "pid": proc.pid, "log": str(log)}
