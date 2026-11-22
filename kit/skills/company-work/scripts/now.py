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

HERE = pathlib.Path(__file__).resolve().parent
SKILLS = HERE.parents[1]                      # 스킬 뿌리 — 설치는 형제 스킬을 한 뿌리에 나란히 놓는다
MAIL_HAND = SKILLS / "company-mail" / "scripts" / "mail.py"
WORK_HAND = SKILLS / "mailbox-work" / "scripts" / "work.py"
BRIEF_HAND = SKILLS / "daily-brief" / "scripts" / "window.py"
HAND_CEILING_S = 200                          # 형제 명령 하나를 기다리는 천장 — ep-login 세션 손의 제 천장(`ep_session.TIMEOUT_SECONDS`)보다 길게
EXIT_OK, EXIT_ARGS, EXIT_SESSION = 0, 2, 3    # 3 은 사내 앱 손들과 같은 뜻이다(세션이 없다 → 스킬 ep-login)

# 형제가 코드에 내는 한 줄의 열쇠 — 없거나 비면 그 칸이 「못 읽었다」와 받은 답을 그대로 낸다(조용히 틀린 값을 안 낸다)
JSON_FLAG = "--json"
MAILBOX_KEY = "mailbox"                      # mail.py session --json
FOLDER_KEY, WORK_FILE_KEY = "folder", "work_file"   # work.py where --json
LATEST_FLAG = "--latest"
BRIEF_KEY, MADE_KEY = "brief", "made"         # window.py --latest — 없으면 빈 객체
HEAD = "## "
READ_SECTIONS = ("본 날 · 본 범위", "사용자", "일", "열린 것")         # 「무엇이 굴러가고 누구 차례인가」와 그것이 언제까지의 파악인가
WEEKDAYS = "월화수목금토일"


def ask(script: pathlib.Path, *argv: str) -> tuple[int | None, str, str]:
    """형제 명령 하나 — (종료 값, 표준 출력, 표준 출력과 오류를 이은 글). 없거나 · 못 띄웠거나 · 천장을 넘으면 종료 값이 None 이고
    셋째 글이 까닭이다."""
    if not script.is_file():
        return None, "", f"{script.parents[1].name} 스킬이 이 스킬 곁에 없다({script})"
    try:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(script), *argv], capture_output=True, timeout=HAND_CEILING_S)
    except subprocess.TimeoutExpired:
        return None, "", f"{script.name} {' '.join(argv)} 이 {HAND_CEILING_S}초 안에 답하지 않았다"
    except OSError as exc:
        return None, "", f"{script.name} 을 못 띄웠다({exc})"
    out = done.stdout.decode("utf-8", "replace").strip()
    return done.returncode, out, (done.stdout + done.stderr).decode("utf-8", "replace").strip()


def values(out: str, *keys: str) -> list[str] | None:
    """`--json` 이 낸 표준 출력의 끝 줄 → 열쇠마다의 값. 끝 줄이 JSON 객체가 아니거나 열쇠 하나라도 비면 None."""
    try:
        got = json.loads(last_line(out))
    except ValueError:
        return None
    if not isinstance(got, dict):
        return None
    picked = [got.get(k) for k in keys]
    return picked if all(isinstance(v, str) and v.strip() for v in picked) else None


def last_line(said: str) -> str:
    return said.splitlines()[-1] if said else "(답이 비었다)"


def session_part() -> tuple[list[str], bool]:
    """사내 세션 칸 — (줄들, 세션이 없다고 손이 말했나)."""
    code, out, said = ask(MAIL_HAND, "session", JSON_FLAG)
    if code == EXIT_OK:
        url = values(out, MAILBOX_KEY)
        if url:
            return ["- 사내 세션: 서 있다", f"- 메일함 주소: {url[0]}"], False
        return [f"- 사내 세션: 서 있다 · 메일함 주소를 못 읽었다 — mail.py session {JSON_FLAG} 의 답: {last_line(said)}"], False
    if code == EXIT_SESSION:
        return [f"- 사내 세션: 없다 — {last_line(said)}"], True
    return [f"- 사내 세션: 확인 못 함 — {last_line(said)}"], False


def folder_part() -> tuple[list[str], pathlib.Path | None, pathlib.Path | None]:
    """사용자 폴더 칸 — (줄들, 폴더, 업무 파일의 자리)."""
    code, out, said = ask(WORK_HAND, "where", JSON_FLAG)
    found = values(out, FOLDER_KEY, WORK_FILE_KEY) if code == EXIT_OK else None
    if not found:
        return [f"- 사용자 폴더: 못 읽었다 — work.py where {JSON_FLAG} 의 답: {last_line(said)}"], None, None
    folder, work = (pathlib.Path(v) for v in found)
    return [f"- 사용자 폴더: {folder}"], folder, work


def stamp(at: dt.datetime) -> str:
    return f"{at:%Y-%m-%d}({WEEKDAYS[at.weekday()]}) {at:%H:%M}"


def brief_part(folder: pathlib.Path | None, now: dt.datetime) -> list[str]:
    """오늘 보고 칸 — 가장 늦은 보고 글이 오늘 것이면 그 글 전부. 어느 글이 가장 늦고 언제 지었나는 보고 글을 짓는 형제 스킬이 답한다."""
    if folder is None:
        return ["## 오늘 보고 — 사용자 폴더를 몰라 못 봤다"]
    if not folder.is_dir():
        return ["## 오늘 보고 — 없다(사용자 폴더에 보고 글이 하나도 없다)"]
    code, out, said = ask(BRIEF_HAND, "--dir", str(folder), LATEST_FLAG)
    if code != 0:
        return [f"## 오늘 보고 — 못 물었다: {last_line(said)}"]
    try:
        got = json.loads(last_line(out))
    except ValueError:
        got = None
    if got == {}:
        return ["## 오늘 보고 — 없다(사용자 폴더에 보고 글이 하나도 없다)"]
    picked = values(out, BRIEF_KEY, MADE_KEY) if isinstance(got, dict) else None
    try:
        at = dt.datetime.fromisoformat(picked[1]) if picked else None
    except ValueError:
        at = None
    if picked is None or at is None:
        return [f"## 오늘 보고 — 못 읽었다(window.py {LATEST_FLAG} 의 답: {last_line(out)})"]
    path = pathlib.Path(picked[0])
    if at.date() != now.date():
        return [f"## 오늘 보고 — 없다 · 가장 늦은 보고는 {stamp(at)} 에 지었다: {path}"]
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"## 오늘 보고 — {stamp(at)} 에 지었다: {path} · 못 읽었다({exc})"]
    return [f"## 오늘 보고 — {stamp(at)} 에 지었다: {path}", "", *nest(text.splitlines())]


def nest(lines: list[str]) -> list[str]:
    """받은 글의 머리를 한 단 내린다 — 받은 글의 절(「## 」)이 이 출력의 칸 머리(「## 」) 아래에 서게(보고 글의 제목 한 줄은 칸 머리와 같은
    단에 선다). 끝의 빈 줄은 걷는다."""
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return ["#" + line if line.startswith("#") else line for line in lines]


def sections(text: str) -> list[tuple[str, list[str]]]:
    """「## 」 머리마다 (이름, 그 절의 줄들 — 머리 포함). 첫 머리 앞의 줄은 버린다."""
    out: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith(HEAD):
            out.append((line[len(HEAD):].strip(), [line]))
        elif out:
            out[-1][1].append(line)
    return out


def work_part(path: pathlib.Path | None) -> list[str]:
    """업무 파일 칸 — 자리 · 마지막으로 쓴 때 · `READ_SECTIONS` 의 절 글 · 나머지 절의 이름."""
    if path is None:
        return ["## 업무 파일 — 사용자 폴더를 몰라 못 봤다"]
    if not path.is_file():
        return [f"## 업무 파일 — 아직 없다({path}) · 짓는 것은 스킬 mailbox-work 다"]
    try:
        text = path.read_text(encoding="utf-8")
        written = dt.datetime.fromtimestamp(path.stat().st_mtime)
    except (OSError, UnicodeDecodeError) as exc:
        return [f"## 업무 파일 — {path} · 못 읽었다({exc})"]
    parts = sections(text)
    shown = [lines for name, lines in parts if name in READ_SECTIONS]
    rest = [name for name, _ in parts if name not in READ_SECTIONS]
    out = [f"## 업무 파일 — {path} · 마지막으로 쓴 때 {stamp(written)}"]
    if rest:
        out.append(f"(아래에 안 실은 절 — 그 파일에서 읽는다: {' · '.join(rest)})")
    for lines in shown:
        out += ["", *nest(lines)]
    return out


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="회사 일의 「지금」 — 사내 세션 · 메일함 주소 · 사용자 폴더 · 오늘 보고 · 업무 파일을 한 번에 낸다. "
                                        "메일함 · 일정 · 비서의 파일은 안 바꾼다.").parse_args(argv)
    now = dt.datetime.now()
    session, gone = session_part()
    folder_lines, folder, work = folder_part()
    out = [f"# 지금 — {stamp(now)}", *session, *folder_lines, "", *brief_part(folder, now), "", *work_part(work)]
    print("\n".join(out))
    return EXIT_SESSION if gone else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
