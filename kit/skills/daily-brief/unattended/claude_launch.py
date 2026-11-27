"""보고 띄우기 — 사람 없는 보고에 띄울 claude 의 명령 · 열린 명령(권한) · 부탁 글을 짓고, 환경을 손질해 떼어 띄운 뒤 기다리지 않는다.
claude 찾기 · 환경 손질 · 떼어 띄우는 인자는 claude 띄우기 바탕(`launch_base`)이 든다.

    cmd, settings, prompt = plan(setting, hand, folder)      # 띄울 명령 · 권한 · 부탁 글(띄우기와 `--dry-run` 이 같은 것을 쓴다)
    launched = launch(setting, hand, folder, at, slot, skipped)   # {at, pid, born, log} 이나 {at, error}

띄운 claude 에 무엇을 여나는 `references/DESIGN.md` 「정한 시각의 보고」가 든다.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
from datetime import datetime
from typing import Any

import unattended_const as C
import unattended_store as st
import clock as tm
from detach import detached
from launch_base import child_env, process_born


def places(hand: pathlib.Path | None, folder: pathlib.Path) -> dict[str, pathlib.Path]:
    """띄운 보고가 쓰는 자리 — 손 · 주소록 손(신원 손도) · 일정 손 · 회의실 손 · 결재 손 · 형제 스킬 mailbox-scan 의 읽는 명령 · 보고 창 · 업무 파일의 쓰는 손 ·
    스킬 폴더 · 사용자 폴더(`folder`). 없는 주소록 · 일정 · 회의실 · 결재 손은 뺀다."""
    scan_skill = C.SKILLS_ROOT / C.SCAN_SKILL
    got = {"home": folder, "reader": scan_skill / pathlib.Path(*C.SCAN_READER), "scan_skill": scan_skill,
           "brief_skill": C.SKILL_DIR, "work_skill": C.SKILLS_ROOT / C.WORK_SKILL,
           "window": C.WINDOW_SCRIPT, "ticks": C.TICKS_SCRIPT,
           "work_writer": C.SKILLS_ROOT / C.WORK_SKILL / pathlib.Path(*C.WORK_WRITER)}
    if hand is not None:
        got["mail"], got["mail_skill"] = hand, hand.parents[1]
        directory = hand.parents[2] / C.DIRECTORY_SKILL / pathlib.Path(*C.DIRECTORY_SCRIPT)
        if directory.is_file():
            got["directory"], got["directory_skill"] = directory, directory.parents[1]
        calendar = hand.parents[2] / C.CALENDAR_SKILL / pathlib.Path(*C.CALENDAR_SCRIPT)
        if calendar.is_file():
            got["calendar"], got["calendar_skill"] = calendar, calendar.parents[1]
        identity = hand.parents[2] / C.DIRECTORY_SKILL / pathlib.Path(*C.IDENTITY_SCRIPT)
        if identity.is_file():
            got["identity"] = identity
        approval = hand.parents[2] / C.APPROVAL_SKILL / pathlib.Path(*C.APPROVAL_SCRIPT)
        if approval.is_file():
            got["approval"], got["approval_skill"] = approval, approval.parents[1]
        meeting = hand.parents[2] / C.MEETING_SKILL / pathlib.Path(*C.MEETING_SCRIPT)
        if meeting.is_file():
            got["meeting"], got["meeting_skill"] = meeting, meeting.parents[1]
    return got


def commands(p: dict[str, pathlib.Path]) -> list[str]:
    """열린 명령 — 권한 규칙의 꼴(끝의 「 *」는 뒤에 인자가 온다). 경로는 「C:/…」 꼴로 따옴표에 싼다 — Git Bash 와 파이썬이 함께 읽는다."""
    def run(script: pathlib.Path) -> str:
        """그 스크립트를 부르는 열린 명령의 머리."""
        return f'python -X utf8 -I "{script.as_posix()}"'
    got = [f"{run(p['mail'])} {r}" for r in C.MAIL_READS] if "mail" in p else []
    got += [f"{run(p['directory'])} {r}" for r in C.DIRECTORY_READS] if "directory" in p else []
    got += [f"{run(p['calendar'])} {r}" for r in C.CALENDAR_READS] if "calendar" in p else []
    got += [f"{run(p['meeting'])} {r}" for r in C.MEETING_READS] if "meeting" in p else []
    got += [f"{run(p['identity'])} {r}" for r in C.IDENTITY_READS] if "identity" in p else []
    got += [f"{run(p['approval'])} {r}" for r in C.APPROVAL_READS] if "approval" in p else []
    got += [f"{run(p['reader'])} *", f'{run(p["window"])} --dir "{p["home"].as_posix()}" *', f"{run(p['work_writer'])} *",
            f'{run(p["ticks"])} --dir "{p["home"].as_posix()}"']
    return got


PROMPT = """사람 없는 예약 실행이다 — 일일 보고의 시계가 보고 시각 {at} 뒤 판에서 사내 세션이 살아 있는 것을 보고 띄웠다. 지금의 일일 보고를 지어 창으로 띄워 둔다 — 사용자가 오셔서 그 창을 본다.

0. 맨 먼저 열린 명령의 ticks.py 로 보고 창에서 누르신 것을 거둔다 — 업무 파악이 그 절을 읽고, 끝 줄들이 보고에서 빼는 것과 미룬 것을 댄다. 로그인 Edge 에 못 닿아 Exit code 3 으로 끝나도 그대로 넘어간다.
1. 그 뒤 스킬 mailbox-work 의 글 {work_lane} 를 읽고 「두 길」대로 업무 파악을 한다 — {writer} where 가 업무 파일이 있다고 하면 「이어 파악」, 없으면 처음 파악(그 스킬 폴더의 first-understanding.md)이고, 「사람이 없을 때」 절이 이 실행의 경계다. 업무 파일은 {writer} write 로만 쓴다 — 이 실행에는 파일을 쓰는 도구가 없다.
2. 그 뒤 스킬 daily-brief 의 글 {brief_lane} 를 읽고 그 글대로 짓는다 — 「사람 없는 예약 실행」 절이 이 실행의 경계다.
3. 회사 메일 · 주소록 · 일정 · 회의실 · 결재 손을 부르는 꼴은 그 스킬의 글({skills})이, 메일함 스캔이 쌓은 것을 읽는 꼴은 {scan_skill}/SKILL.md 가 든다.
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
    p = places(hand, folder)
    opened = commands(p)
    settings = {"permissions": {"allow": [f"Bash({c})" for c in opened], "deny": list(C.BRIEF_DENY)}}
    dirs = [p[k] for k in ("brief_skill", "work_skill", "scan_skill", "mail_skill", "directory_skill", "calendar_skill", "meeting_skill",
                                  "approval_skill") if k in p and p[k].is_dir()]
    cmd = [str(setting["claude"]), "-p", "--settings", str(folder / C.LAUNCH_SETTINGS_FILE), "--permission-mode", "dontAsk",
           "--tools", C.CLAUDE_TOOLS, "--strict-mcp-config", "--no-session-persistence",
           *[a for d in dirs for a in ("--add-dir", str(d))]]
    skills = " · ".join(f"{p[k].as_posix()}/SKILL.md" for k in ("mail_skill", "directory_skill", "calendar_skill", "meeting_skill", "approval_skill")
                        if k in p)
    prompt = PROMPT.format(at=at or setting["times"][0], brief_lane=(p["brief_skill"] / C.LANE_FILE).as_posix(),
                           skills=skills or "회사 메일 스킬 company-mail", work_lane=(p["work_skill"] / C.LANE_FILE).as_posix(),
                           writer=pathlib.Path(*C.WORK_WRITER).name, work_name=C.WORK_FILE,
                           scan_skill=p["scan_skill"].as_posix(), home=p["home"].as_posix(),
                           commands="\n".join(f"   {c.replace(' *', ' …')}" for c in opened),
                           missed=MISSED.format(lines="\n".join(f"   {x}" for x in skipped)) if skipped else "")
    return cmd, settings, prompt


def launch(setting: dict[str, Any], hand: pathlib.Path | None, folder: pathlib.Path, at: datetime, slot: str | None = None,
           skipped: list[str] | None = None) -> dict[str, Any]:
    """권한 · 부탁 글을 사용자 폴더에 지어 claude 를 띄우고 기다리지 않는다(출력은 `LAUNCH_LOG_FILE`). 내는 것 — {at, pid, born(뜬 때 · 못 물었으면 None), log} 이나 {at, error}."""
    cmd, settings, prompt = plan(setting, hand, folder, slot, skipped)
    st.write_json(folder / C.LAUNCH_SETTINGS_FILE, settings)
    (folder / C.LAUNCH_PROMPT_FILE).write_text(prompt, encoding="utf-8")
    log = folder / C.LAUNCH_LOG_FILE
    env = child_env(dict(os.environ))
    try:
        with (folder / C.LAUNCH_PROMPT_FILE).open("rb") as given, log.open("wb") as out:
            proc = subprocess.Popen(cmd, cwd=str(folder), stdin=given, stdout=out, stderr=subprocess.STDOUT, env=env, close_fds=True,
                                    **detached())
    except OSError as exc:
        return {"at": tm.utc_stamp(at), "error": f"{type(exc).__name__}: {exc}"}
    born = process_born(proc.pid)
    st.write_json(folder / C.LAUNCH_FILE, {"started": tm.utc_stamp(at), "pid": proc.pid, "born": born})
    return {"at": tm.utc_stamp(at), "pid": proc.pid, "born": born, "log": str(log)}
