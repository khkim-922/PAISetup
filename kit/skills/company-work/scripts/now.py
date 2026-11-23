"""회사 일의 「지금」을 한 번에 낸다 — 바탕 스킬 company-work 의 손가락. 메일함 · 일정 · 비서의 파일은 안 바꾼다(세션이 낡았으면
회사 메일 손의 `session` 이 여느 부름처럼 세션 파일을 새로 받는다).

    python -X utf8 -I now.py

내는 것 — 표준 출력에 칸마다 한 덩이(칸 이름은 아래 상수):
    지금        이 PC 의 날 · 요일 · 시각
    사내 세션    서 있다 · 없다 · 확인 못 함 — 서 있으면 메일함 주소(형제 스킬 company-mail 의 `mail.py session --json` 의 `mailbox`)
    사용자 폴더  형제 스킬 mailbox-work 의 `work.py where --json` 의 `folder`
    오늘 보고    사용자 폴더의 가장 늦은 보고 글(형제 스킬 daily-brief 의 `window.py --latest` 가 대는 자리와 지은 때)이 오늘 것이면 지은
                때와 글 전부, 아니면 가장 늦은 것의 때와 자리
    업무 파일    자리(`work.py where --json` 의 `work_file`) · 마지막으로 쓴 때와 `READ_SECTIONS` 의 절 글 — 나머지 절은 이름만(파일의
                절 이름 · 차례는 mailbox-work 의 `lane.md`)

형제 스킬은 이 스킬 곁(같은 스킬 뿌리)에서 찾고 명령으로만 묻는다 — 코드를 싣지 않고, 사람에게 하는 말이 아니라 `--json` 이 내는 한
줄을 읽는다. 형제의 파일은 계약된 이름으로 읽기만 한다. 한 칸을 못 물으면 그 칸이 까닭을 말하고 나머지 칸은 그대로 낸다.

종료 값 — 0 냈다 · 2 인자가 틀렸다 · 3 사내 세션이 없다(나머지 칸은 그대로 낸다 — 다음 걸음은 스킬 ep-login).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys
from collections.abc import Sequence
from typing import Any, NamedTuple

HERE = pathlib.Path(__file__).resolve().parent
SKILLS = HERE.parents[1]                      # 스킬 뿌리 — 설치는 형제 스킬을 한 뿌리에 나란히 놓는다
MAIL_HAND = SKILLS / "company-mail" / "scripts" / "mail.py"
WORK_HAND = SKILLS / "mailbox-work" / "scripts" / "work.py"
BRIEF_HAND = SKILLS / "daily-brief" / "scripts" / "window.py"
HAND_CEILING_S = 200                          # 형제 명령 하나를 기다리는 천장 — ep-login 세션 손의 제 천장(`ep_session.TIMEOUT_SECONDS`)보다 길게
EXIT_OK, EXIT_ARGS, EXIT_SESSION = 0, 2, 3    # 3 은 사내 앱 손들과 같은 뜻이다(세션이 없다 → 스킬 ep-login) — 사본이다: 원본은 ep-login `ep_command.py` 의 EXIT_SESSION

# 형제가 코드에 내는 한 줄의 열쇠 — 없거나 비면 그 칸이 「못 읽었다」와 받은 답을 그대로 낸다(조용히 틀린 값을 안 낸다)
JSON_FLAG = "--json"
MAILBOX_KEY = "mailbox"                      # mail.py session --json
FOLDER_KEY, WORK_FILE_KEY = "folder", "work_file"   # work.py where --json
LATEST_FLAG = "--latest"
BRIEF_KEY, MADE_KEY = "brief", "made"         # window.py --latest — 없으면 빈 객체
HEAD = "## "
READ_SECTIONS = ("본 날 · 본 범위", "사용자", "일", "열린 것")         # 「무엇이 굴러가고 누구 차례인가」와 그것이 언제까지의 파악인가
WEEKDAYS = "월화수목금토일"                            # date.weekday() 의 0 ~ 6 — 사본이다: ep-login `ep_command.py` · daily-brief `brief_const.py` 가 같은 값을 든다(코드를 서로 안 싣는다)
NO_ANSWER = "(답이 비었다)"
STAMP = "{day}({weekday}) {time}"
DAY_FORM, TIME_FORM = "%Y-%m-%d", "%H:%M"
ABOUT = ("회사 일의 「지금」 — 사내 세션 · 메일함 주소 · 사용자 폴더 · 오늘 보고 · 업무 파일을 한 번에 낸다. "
         "메일함 · 일정 · 비서의 파일은 안 바꾼다.")          # 도움말의 첫 문단
# 형제 명령을 못 물은 까닭
NO_SIBLING = "{skill} 스킬이 이 스킬 곁에 없다({script})"
NO_REPLY = "{script} {argv} 이 {ceiling}초 안에 답하지 않았다"
NO_LAUNCH = "{script} 을 못 띄웠다({exc})"

# 칸마다 낼 줄 — 칸의 상태 하나에 틀 하나
TITLE = "# 지금 — {stamp}"
SESSION_UP = ("- 사내 세션: 서 있다", "- 메일함 주소: {url}")
SESSION_UP_NO_URL = "- 사내 세션: 서 있다 · 메일함 주소를 못 읽었다 — mail.py session {flag} 의 답: {said}"
SESSION_GONE = "- 사내 세션: 없다 — {said}"
SESSION_UNKNOWN = "- 사내 세션: 확인 못 함 — {said}"
FOLDER_LINE = "- 사용자 폴더: {folder}"
FOLDER_UNREAD = "- 사용자 폴더: 못 읽었다 — work.py where {flag} 의 답: {said}"
BRIEF_NO_FOLDER = "## 오늘 보고 — 사용자 폴더를 몰라 못 봤다"
BRIEF_NONE = "## 오늘 보고 — 없다(사용자 폴더에 보고 글이 하나도 없다)"
BRIEF_UNASKED = "## 오늘 보고 — 못 물었다: {said}"
BRIEF_UNREAD = "## 오늘 보고 — 못 읽었다(window.py {flag} 의 답: {said})"
BRIEF_PAST = "## 오늘 보고 — 없다 · 가장 늦은 보고는 {stamp} 에 지었다: {path}"
BRIEF_TODAY = "## 오늘 보고 — {stamp} 에 지었다: {path}"
BRIEF_TODAY_UNREAD = "## 오늘 보고 — {stamp} 에 지었다: {path} · 못 읽었다({exc})"
WORK_NO_FOLDER = "## 업무 파일 — 사용자 폴더를 몰라 못 봤다"
WORK_NONE = "## 업무 파일 — 아직 없다({path}) · 짓는 것은 스킬 mailbox-work 다"
WORK_UNREAD = "## 업무 파일 — {path} · 못 읽었다({exc})"
WORK_HEAD = "## 업무 파일 — {path} · 마지막으로 쓴 때 {stamp}"
WORK_REST = "(아래에 안 실은 절 — 그 파일에서 읽는다: {names})"
NAME_SEP = " · "

# 칸의 상태 — 셈이 내고 말이 받는다
SESSION_IS_UP, SESSION_IS_UP_NO_URL, SESSION_IS_GONE, SESSION_IS_UNKNOWN = "up", "up-no-url", "gone", "unknown"
FOLDER_IS_KNOWN, FOLDER_IS_UNREAD = "known", "unread"
BRIEF_IS_NO_FOLDER, BRIEF_IS_NONE, BRIEF_IS_UNASKED, BRIEF_IS_UNREAD, BRIEF_IS_PAST, BRIEF_IS_TODAY, BRIEF_IS_TODAY_UNREAD = (
    "no-folder", "none", "unasked", "unread", "past", "today", "today-unread")
WORK_IS_NO_FOLDER, WORK_IS_NONE, WORK_IS_UNREAD, WORK_IS_READ = "no-folder", "none", "unread", "read"


class Folder(NamedTuple):
    """사용자 폴더의 상태 — 상태의 이름 · 폴더 · 업무 파일의 자리 · 못 읽었으면 받은 답의 끝 줄."""
    state: str
    path: pathlib.Path | None = None
    work_file: pathlib.Path | None = None
    said: str = ""


class Brief(NamedTuple):
    """가장 늦은 보고의 상태 — 상태의 이름 · 지은 때 · 글의 자리 · 못 물었거나 못 읽었으면 받은 답의 끝 줄 · 오늘 것이면 읽은 글(못
    읽었으면 그 까닭)."""
    state: str
    at: dt.datetime | None = None
    path: pathlib.Path | None = None
    said: str = ""
    text: str = ""
    error: BaseException | None = None


class Work(NamedTuple):
    """업무 파일의 상태 — 상태의 이름 · 마지막으로 쓴 때 · 실을 절의 줄들 · 이름만 댈 절 · 못 읽은 까닭."""
    state: str
    written: dt.datetime | None = None
    shown: Sequence[list[str]] = ()
    rest: Sequence[str] = ()
    error: BaseException | None = None


# ── 바탕 — 형제 명령 · 끝 줄 · 파일 · 내는 줄 ─────────────────────────────────────

def ask(script: pathlib.Path, *argv: str) -> tuple[int | None, str, str]:
    """형제 명령 하나 — (종료 값, 표준 출력, 표준 출력과 오류를 이은 글). 없거나 · 못 띄웠거나 · 천장을 넘으면 종료 값이 None 이고
    셋째 글이 까닭이다."""
    if not script.is_file():
        return None, "", NO_SIBLING.format(skill=script.parents[1].name, script=script)
    try:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(script), *argv], capture_output=True, timeout=HAND_CEILING_S)
    except subprocess.TimeoutExpired:
        return None, "", NO_REPLY.format(script=script.name, argv=" ".join(argv), ceiling=HAND_CEILING_S)
    except OSError as exc:
        return None, "", NO_LAUNCH.format(script=script.name, exc=exc)
    out = done.stdout.decode("utf-8", "replace").strip()
    return done.returncode, out, (done.stdout + done.stderr).decode("utf-8", "replace").strip()


def last_json(out: str) -> Any:
    """`--json` 이 낸 표준 출력의 끝 줄을 JSON 으로 — 못 풀면 None."""
    try:
        return json.loads(last_line(out))
    except ValueError:
        return None


def pick(got: Any, *keys: str) -> list[str] | None:
    """JSON 객체에서 열쇠마다의 값 — 객체가 아니거나 열쇠 하나라도 비면 None."""
    if not isinstance(got, dict):
        return None
    picked = [got.get(k) for k in keys]
    return picked if all(isinstance(v, str) and v.strip() for v in picked) else None


def last_line(said: str) -> str:
    """받은 답의 끝 줄 — 비었으면 그렇다는 말."""
    return said.splitlines()[-1] if said else NO_ANSWER


def read_text(path: pathlib.Path) -> str:
    """글 파일 하나(UTF-8) — 못 읽으면 `OSError` · `UnicodeDecodeError`."""
    return path.read_text(encoding="utf-8")


def written_at(path: pathlib.Path) -> dt.datetime:
    """파일을 마지막으로 쓴 때 — 못 보면 `OSError`."""
    return dt.datetime.fromtimestamp(path.stat().st_mtime)


def clock() -> dt.datetime:
    """이 PC 의 지금 때."""
    return dt.datetime.now()


def say(lines: list[str]) -> None:
    """칸의 줄들을 이어 표준 출력에 낸다."""
    print("\n".join(lines))


# ── 셈 — 칸마다의 상태 ─────────────────────────────────────────────────────────

def session_state() -> tuple[str, str]:
    """사내 세션 — (상태, 메일함 주소 · 아니면 손이 남긴 끝 줄). 메일 손에 `session --json` 으로 묻는다."""
    code, out, said = ask(MAIL_HAND, "session", JSON_FLAG)
    if code == EXIT_OK:
        url = pick(last_json(out), MAILBOX_KEY)
        return (SESSION_IS_UP, url[0]) if url else (SESSION_IS_UP_NO_URL, last_line(said))
    if code == EXIT_SESSION:
        return SESSION_IS_GONE, last_line(said)
    return SESSION_IS_UNKNOWN, last_line(said)


def exit_for(session: str) -> int:
    """「지금」의 종료 값 — 세션이 없다고 손이 말했으면 3, 아니면 0."""
    return EXIT_SESSION if session == SESSION_IS_GONE else EXIT_OK


def folder_state() -> Folder:
    """사용자 폴더의 상태 — 읽었으면 폴더와 업무 파일의 자리, 못 읽었으면 받은 답의 끝 줄. 업무 파악 손에 `where --json` 으로 묻는다."""
    code, out, said = ask(WORK_HAND, "where", JSON_FLAG)
    found = pick(last_json(out), FOLDER_KEY, WORK_FILE_KEY) if code == EXIT_OK else None
    if not found:
        return Folder(FOLDER_IS_UNREAD, said=last_line(said))
    return Folder(FOLDER_IS_KNOWN, *(pathlib.Path(v) for v in found))


def latest_brief(folder: pathlib.Path | None, now: dt.datetime) -> Brief:
    """가장 늦은 보고의 상태 — 폴더를 모르거나 폴더가 없으면 그렇다고, 있으면 보고 글을 짓는 형제 스킬에 `--latest` 로 물어 그 답의 상태."""
    if folder is None:
        return Brief(BRIEF_IS_NO_FOLDER)
    if not folder.is_dir():
        return Brief(BRIEF_IS_NONE)
    return brief_from(*ask(BRIEF_HAND, "--dir", str(folder), LATEST_FLAG), now)


def brief_from(code: int | None, out: str, said: str, now: dt.datetime) -> Brief:
    """형제의 `--latest` 답 → 가장 늦은 보고의 상태 — 못 물음 · 없음 · 못 읽음 · 지난 것(때 · 자리) · 오늘 것(때 · 자리)."""
    if code != EXIT_OK:
        return Brief(BRIEF_IS_UNASKED, said=last_line(said))
    got = last_json(out)
    if got == {}:
        return Brief(BRIEF_IS_NONE)
    picked = pick(got, BRIEF_KEY, MADE_KEY)
    try:
        at = dt.datetime.fromisoformat(picked[1]) if picked else None
    except ValueError:
        at = None
    if picked is None or at is None:
        return Brief(BRIEF_IS_UNREAD, said=last_line(out))
    path = pathlib.Path(picked[0])
    return Brief(BRIEF_IS_PAST if at.date() != now.date() else BRIEF_IS_TODAY, at, path)


def with_text(brief: Brief) -> Brief:
    """오늘 것이면 그 보고 글(앞뒤 빈칸을 걷은 것)을 읽어 붙인 상태 — 못 읽으면 「오늘 것 · 못 읽음」과 그 까닭. 오늘 것이 아니면 받은 그대로."""
    if brief.state != BRIEF_IS_TODAY:
        return brief
    try:
        return brief._replace(text=read_text(brief.path).strip())
    except (OSError, UnicodeDecodeError) as exc:
        return brief._replace(state=BRIEF_IS_TODAY_UNREAD, error=exc)


def read_work(path: pathlib.Path | None) -> Work:
    """업무 파일의 상태 — 폴더 모름 · 없음 · 못 읽음(까닭) · 읽음(쓴 때 · 실을 절 · 이름만 댈 절)."""
    if path is None:
        return Work(WORK_IS_NO_FOLDER)
    if not path.is_file():
        return Work(WORK_IS_NONE)
    try:
        text = read_text(path)
        written = written_at(path)
    except (OSError, UnicodeDecodeError) as exc:
        return Work(WORK_IS_UNREAD, error=exc)
    return Work(WORK_IS_READ, written, *pick_sections(text))


def sections(text: str) -> list[tuple[str, list[str]]]:
    """「## 」 머리마다 (이름, 그 절의 줄들 — 머리 포함). 첫 머리 앞의 줄은 버린다."""
    out: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith(HEAD):
            out.append((line[len(HEAD):].strip(), [line]))
        elif out:
            out[-1][1].append(line)
    return out


def pick_sections(text: str) -> tuple[list[list[str]], list[str]]:
    """업무 파일의 절 → (실을 절의 줄들 — `READ_SECTIONS` 의 것, 이름만 댈 나머지 절)."""
    parts = sections(text)
    return [lines for name, lines in parts if name in READ_SECTIONS], [name for name, _ in parts if name not in READ_SECTIONS]


# ── 말 — 상태를 칸의 줄로 ───────────────────────────────────────────────────────

def stamp(at: dt.datetime) -> str:
    """때를 사람 말로 — 날(요일) 시각."""
    return STAMP.format(day=f"{at:{DAY_FORM}}", weekday=WEEKDAYS[at.weekday()], time=f"{at:{TIME_FORM}}")


def nest(lines: list[str]) -> list[str]:
    """받은 글의 머리를 한 단 내린다 — 받은 글의 절(「## 」)이 이 출력의 칸 머리(「## 」) 아래에 서게(보고 글의 제목 한 줄은 칸 머리와 같은
    단에 선다). 끝의 빈 줄은 걷는다."""
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return ["#" + line if line.startswith("#") else line for line in lines]


def title_line(now: dt.datetime) -> str:
    """「지금」의 맨 위 줄 — 이 PC 의 날 · 요일 · 시각."""
    return TITLE.format(stamp=stamp(now))


def session_lines(state: str, value: str) -> list[str]:
    """사내 세션 칸의 줄 — 서 있으면 메일함 주소까지."""
    if state == SESSION_IS_UP:
        return [SESSION_UP[0], SESSION_UP[1].format(url=value)]
    if state == SESSION_IS_UP_NO_URL:
        return [SESSION_UP_NO_URL.format(flag=JSON_FLAG, said=value)]
    return [(SESSION_GONE if state == SESSION_IS_GONE else SESSION_UNKNOWN).format(said=value)]


def folder_lines(home: Folder) -> list[str]:
    """사용자 폴더 칸의 줄 — 못 읽었으면 받은 답의 끝 줄."""
    if home.state == FOLDER_IS_UNREAD:
        return [FOLDER_UNREAD.format(flag=JSON_FLAG, said=home.said)]
    return [FOLDER_LINE.format(folder=home.path)]


def brief_lines(brief: Brief) -> list[str]:
    """오늘 보고 칸의 줄 — 상태마다 한 줄, 오늘 것이면 머리를 내린 글 전부(못 읽었으면 그 까닭)."""
    if brief.state == BRIEF_IS_NO_FOLDER:
        return [BRIEF_NO_FOLDER]
    if brief.state == BRIEF_IS_NONE:
        return [BRIEF_NONE]
    if brief.state == BRIEF_IS_UNASKED:
        return [BRIEF_UNASKED.format(said=brief.said)]
    if brief.state == BRIEF_IS_UNREAD:
        return [BRIEF_UNREAD.format(flag=LATEST_FLAG, said=brief.said)]
    if brief.state == BRIEF_IS_PAST:
        return [BRIEF_PAST.format(stamp=stamp(brief.at), path=brief.path)]
    if brief.state == BRIEF_IS_TODAY_UNREAD:
        return [BRIEF_TODAY_UNREAD.format(stamp=stamp(brief.at), path=brief.path, exc=brief.error)]
    return [BRIEF_TODAY.format(stamp=stamp(brief.at), path=brief.path), "", *nest(brief.text.splitlines())]


def work_lines(path: pathlib.Path | None, work: Work) -> list[str]:
    """업무 파일 칸의 줄 — 상태마다 한 줄, 읽었으면 자리 · 마지막으로 쓴 때 · 이름만 댄 절 · 실은 절마다 머리를 내린 글."""
    if work.state == WORK_IS_NO_FOLDER:
        return [WORK_NO_FOLDER]
    if work.state == WORK_IS_NONE:
        return [WORK_NONE.format(path=path)]
    if work.state == WORK_IS_UNREAD:
        return [WORK_UNREAD.format(path=path, exc=work.error)]
    out = [WORK_HEAD.format(path=path, stamp=stamp(work.written))]
    if work.rest:
        out.append(WORK_REST.format(names=NAME_SEP.join(work.rest)))
    for lines in work.shown:
        out += ["", *nest(lines)]
    return out


# ── 손 ───────────────────────────────────────────────────────────────────────

def parser() -> argparse.ArgumentParser:
    """명령의 인자 꼴 — 받는 인자가 없다(도움말과, 틀린 인자의 종료 2 만 선다)."""
    return argparse.ArgumentParser(description=ABOUT)


def main(argv: list[str] | None = None) -> int:
    """「지금」을 한 번에 — 지금 → 세션 칸 → 폴더 칸 → 보고 칸 → 업무 칸을 이 차례로 엮어 내고, 세션이 없으면 3 으로 끝낸다."""
    parser().parse_args(argv)
    now = clock()
    session, value = session_state()
    home = folder_state()
    brief = with_text(latest_brief(home.path, now))
    say([title_line(now), *session_lines(session, value), *folder_lines(home), "", *brief_lines(brief),
         "", *work_lines(home.work_file, read_work(home.work_file))])
    return exit_for(session)


if __name__ == "__main__":
    sys.exit(main())
