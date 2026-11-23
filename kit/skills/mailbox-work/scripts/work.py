"""업무 파일(work.md)의 자리를 대고, 받은 글로 그 파일을 바꿔 쓴다 — 업무 파악 스킬의 쓰는 손. 메일함에는 닿지 않는다.

    python -X utf8 -I work.py where                 사용자 폴더 · 업무 파일의 자리 · 있나 · 마지막으로 쓴 때
    python -X utf8 -I work.py where --json          코드가 읽을 한 줄 — {"folder": 사용자 폴더, "work_file": 업무 파일의 자리}
    python -X utf8 -I work.py write [--in <파일>]   받은 글 전부로 업무 파일을 바꿔 쓴다(없으면 표준 입력)

받는 것 — `write` 의 글은 업무 파일 전부다(UTF-8 · BOM 있는 UTF-16 · cp949). 절(`## ` 머리)의 이름과 차례는 `lane.md` 「업무 파일」이 든다.
`write` 는 곁의 임시 파일에 다 쓴 뒤 바꿔 끼우고(줄끝 LF), 사용자 폴더가 없으면 만든다.

지키는 것 — 까닭은 `references/DESIGN.md`
    * 앞 판에 있던 절 머리가 받은 글에 없으면 쓰지 않는다 — 꼴이 바뀐 절(`RENAMED` · `MOVED_TO_TIDY`)만 예외다
    * 빈 글 · 절 머리가 하나도 없는 글은 쓰지 않는다
    * 업무 파일과 그 임시 파일만 쓴다 — 옮겨 간 절을 옮겨 적을 때만 같은 폴더의 정리 파일 끝에 덧붙인다

종료 값 — 0 됐다 · 1 안 썼다(빈 글 · 절이 빠졌다 · 못 썼다 — 끝 줄이 다음 걸음을 말한다) · 2 인자가 틀렸다.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections.abc import Sequence
from datetime import datetime

# 사용자 폴더 — 원본은 스킬 mailbox-scan 의 `scripts/scan_const.py` 「자리」다. 스킬은 서로의 코드를 싣지 않아 옮겨 든다 — 바꾸면 함께 바꾼다
HOME_ENV = "MAIL_SECRETARY_HOME"   # 개발 · 검사가 사용자 폴더를 바꿀 때만 준다
HOME_NAME = "mail-secretary"       # %LOCALAPPDATA% 아래의 사용자 폴더 이름
WORK_FILE = "work.md"
TEMP_SUFFIX = ".writing"           # 바꿔 끼우기 전의 임시 파일 — 업무 파일 곁
HEAD = "## "                       # 절 머리 — 앞 판과 견주는 단위
TIDY_FILE = "mailbox-tidy.md"      # 메일함 정리의 정리 파일 — 같은 사용자 폴더(주인은 스킬 mailbox-tidy)
# 업무 파일의 꼴이 바뀐 절 — ⚠ `lane.md` 「업무 파일」의 절 이름이 바뀌면 옛 이름을 더한다. 안 더하면 그 절을 든 앞 판 위로는 끝내 못 쓴다
RENAMED = {"업무 한 문단": "업무"}                       # 옛 이름 → 지금 이름
MOVED_TO_TIDY = ("정리한 뒤의 메일함", "정한 것")        # 정리 파일로 옮겨 간 절 — 앞 판의 것을 정리 파일에 옮겨 적고 빠뜨린다
EXIT_OK, EXIT_REFUSED, EXIT_ARGS = 0, 1, 2

WHERE_HAS = "[업무 파일 — {path} · 마지막으로 쓴 때 {at} · 사용자 폴더 {folder}. 다음: 그 파일의 「본 날 · 본 범위」에서 이어 파악한다]"
WHERE_NONE = "[업무 파일 — 아직 없다({path}) · 사용자 폴더 {folder}. 다음: 처음 파악으로 짓고 write 로 쓴다]"
WROTE = "[업무 파일 — 적었다: {path} · 절 {n}개{fresh}{moved}]"
MOVED_NOTE = " · 정리 파일로 옮겨 간 절을 {tidy} 에 옮겨 적었다: {names}"
EMPTY = "[업무 파일 — 쓰지 않았다: 받은 글이 비었거나 절 머리(「## 」)가 하나도 없다. 앞 판은 그대로다. 다음: 업무 파일 전부를 다시 준다]"
DROPPED = ("[업무 파일 — 쓰지 않았다: 앞 판의 절이 받은 글에 없다 — {names}. 앞 판은 그대로다. 다음: 그 절을 넣어 다시 준다 — 비울 절은 머리를 "
           "두고 「없음」으로 적는다]")
FAILED = "[업무 파일 — 못 썼다: {why}. 앞 판은 그대로다]"
NO_INPUT = "[업무 파일 — 쓰지 않았다: 글을 못 읽었다({why})]"
FRESH_NOTE = " · 처음 지었다"
NAME_MARK = "「{name}」"
NAME_SEP = " · "
ERROR_WORD = "{kind}: {exc}"
WRITTEN_AT = "%Y-%m-%d %H:%M"
RENAMED_KIND, MOVED_KIND = "renamed", "moved"       # 꼴이 바뀐 절의 갈래 — `kind` 가 내고 `compare` 가 가른다


# ── 바탕 — 자리 · 받는 글 · 내는 줄 ───────────────────────────────────────────────

def home() -> pathlib.Path:
    """사용자 폴더 — `MAIL_SECRETARY_HOME` 이 있으면 그 자리, 없으면 `%LOCALAPPDATA%\\mail-secretary`."""
    override = os.environ.get(HOME_ENV, "").strip()
    if override:
        return pathlib.Path(override)
    local = os.environ.get("LOCALAPPDATA", "").strip()
    return (pathlib.Path(local) if local else pathlib.Path.home() / "AppData" / "Local") / HOME_NAME


def decode(raw: bytes) -> str:
    """받은 바이트 → 글. BOM 이 있으면 그 꼴(UTF-8 · UTF-16 — Windows PowerShell 의 `>` 가 쓰는 꼴), 없으면 UTF-8, 안 되면 cp949.
    같은 몸이 스킬 mailbox-tidy 의 `journal_io.py` · daily-brief 의 `window.py` 에 있다 — 고치면 셋을 함께 고친다(머리말의 받는 꼴이 같다)."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", errors="replace")


def read_given(infile: str | None) -> str:
    """받은 글 — `--in` 의 파일이나 표준 입력을 풀어 줄끝을 LF 로. 못 읽으면 `OSError`."""
    raw = pathlib.Path(infile).read_bytes() if infile else sys.stdin.buffer.read()
    return decode(raw).replace("\r\n", "\n").replace("\r", "\n")


def utf8_out() -> None:
    """표준 출력을 UTF-8 로 다시 잡는다 — 한글 Windows 의 cp949 콘솔이 리디렉션 · 파이프에서 한글을 깨지 않게."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def say(line: str) -> None:
    """사람(또는 부른 코드)에게 할 한 줄을 표준 출력에 낸다."""
    print(line)


# ── 절 ───────────────────────────────────────────────────────────────────────

def heads(text: str) -> list[str]:
    """절 머리 — 「## 」로 시작하는 줄의 이름(앞뒤 빈칸을 걷는다)."""
    return [line[len(HEAD):].strip() for line in text.splitlines() if line.startswith(HEAD)]


def sections(text: str) -> dict[str, str]:
    """절 머리 → 그 절의 글(머리 줄부터 다음 머리 앞까지)."""
    got: dict[str, list[str]] = {}
    name = None
    for line in text.splitlines():
        if line.startswith(HEAD):
            name = line[len(HEAD):].strip()
            got[name] = [line]
        elif name is not None:
            got[name].append(line)
    return {k: "\n".join(v).rstrip() for k, v in got.items()}


def renamed_to(head: str) -> list[str]:
    """앞 판의 절 머리가 이름이 바뀐 절이면 그 지금 이름들 — 옛 이름으로 시작하는 머리를 같은 절로 본다. 아니면 빈 목록."""
    return [now for old, now in RENAMED.items() if head.startswith(old)]


def kind(head: str) -> str | None:
    """앞 판의 절 머리가 꼴이 바뀐 절이면 그 갈래 — 「renamed」 · 「moved」 · 아니면 None(그 낱말로 시작하는 머리를 같은 절로 본다)."""
    if renamed_to(head):
        return RENAMED_KIND
    if any(head.startswith(m) for m in MOVED_TO_TIDY):
        return MOVED_KIND
    return None


def is_empty(text: str, new: list[str]) -> bool:
    """쓰지 않을 빈 글인가 — 글이 비었거나 절 머리가 하나도 없다."""
    return not text.strip() or not new


def compare(old_text: str, new: list[str]) -> tuple[list[str], list[str]]:
    """앞 판의 절 가운데 받은 글에 없는 것 → (잃은 절, 정리 파일로 옮겨 갈 절). 이름이 바뀐 절은 새 이름이 받은 글에 있으면 잃은 것이 아니다."""
    missing = [h for h in heads(old_text) if h not in new]
    renamed_ok = [h for h in missing if kind(h) == RENAMED_KIND and any(now in new for now in renamed_to(h))]
    moving = [h for h in missing if kind(h) == MOVED_KIND]
    lost = [h for h in missing if h not in renamed_ok and h not in moving]
    return lost, moving


# ── 파일 ─────────────────────────────────────────────────────────────────────

def old_version(path: pathlib.Path) -> str | None:
    """업무 파일의 앞 판 — 없으면 None."""
    return decode(path.read_bytes()) if path.is_file() else None


def written_at(path: pathlib.Path) -> datetime | None:
    """업무 파일을 마지막으로 쓴 때 — 없으면 None."""
    return datetime.fromtimestamp(path.stat().st_mtime) if path.is_file() else None


def temp_of(path: pathlib.Path) -> pathlib.Path:
    """바꿔 끼우기 전의 임시 파일 — 업무 파일 곁."""
    return path.with_name(path.name + TEMP_SUFFIX)


def tidy_path(folder: pathlib.Path) -> pathlib.Path:
    """메일함 정리의 정리 파일 자리 — 같은 사용자 폴더."""
    return folder / TIDY_FILE


def make_folder(folder: pathlib.Path) -> None:
    """사용자 폴더를 만든다 — 있으면 그대로. 못 만들면 `OSError`."""
    folder.mkdir(parents=True, exist_ok=True)


def move_to_tidy(folder: pathlib.Path, old_text: str, names: list[str]) -> list[str]:
    """앞 판의 그 절들을 정리 파일 끝에 덧붙인다 — 정리 파일에 같은 낱말로 시작하는 절이 이미 있으면 그 절은 건너뛴다. 옮겨 적은 이름을 낸다."""
    tidy = tidy_path(folder)
    have = heads(decode(tidy.read_bytes())) if tidy.is_file() else []
    body = sections(old_text)
    add = [n for n in names if not any(h.startswith(n) or n.startswith(h) for h in have)]
    if add:
        prev = decode(tidy.read_bytes()).rstrip() if tidy.is_file() else ""
        text = "\n\n".join([p for p in (prev, *(body[n] for n in add)) if p]) + "\n"
        tidy.write_text(text, encoding="utf-8", newline="\n")
    return add


def replace_with(path: pathlib.Path, text: str) -> None:
    """업무 파일을 받은 글로 바꿔 끼운다 — 곁의 임시 파일에 다 쓴 뒤(끝 줄바꿈을 채워 LF 로) 그 자리에 옮긴다."""
    temp = temp_of(path)
    temp.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")
    os.replace(temp, path)


def drop_temp(path: pathlib.Path) -> None:
    """못 쓴 판의 임시 파일을 걷는다 — 없으면 그대로."""
    temp_of(path).unlink(missing_ok=True)


# ── 말 ───────────────────────────────────────────────────────────────────────

def names_word(names: list[str]) -> str:
    """절 이름들을 사람 말로 — 「이름」 · 「이름」."""
    return NAME_SEP.join(NAME_MARK.format(name=h) for h in names)


def error_word(exc: BaseException) -> str:
    """못 읽은 · 못 쓴 까닭을 사람 말로 — 오류의 종류와 그 글."""
    return ERROR_WORD.format(kind=type(exc).__name__, exc=exc)


def no_input_line(exc: BaseException) -> str:
    """받은 글을 못 읽어 안 썼다는 끝 줄."""
    return NO_INPUT.format(why=error_word(exc))


def dropped_line(lost: list[str]) -> str:
    """앞 판의 절이 빠져 안 썼다는 끝 줄 — 빠진 절의 이름과 다음 걸음."""
    return DROPPED.format(names=names_word(lost))


def failed_line(exc: BaseException) -> str:
    """쓰다 못 썼다는 끝 줄 — 앞 판은 그대로다."""
    return FAILED.format(why=error_word(exc))


def where_json(folder: pathlib.Path, path: pathlib.Path) -> str:
    """코드가 읽을 자리 한 줄 — {"folder": 사용자 폴더, "work_file": 업무 파일의 자리}."""
    return json.dumps({"folder": str(folder), "work_file": str(path)}, ensure_ascii=False)


def where_line(folder: pathlib.Path, path: pathlib.Path, at: datetime | None) -> str:
    """업무 파일의 자리 한 줄 — 있으면 쓴 때와 이어 파악, 없으면 처음 파악."""
    if at is None:
        return WHERE_NONE.format(path=path, folder=folder)
    return WHERE_HAS.format(path=path, at=at.strftime(WRITTEN_AT), folder=folder)


def wrote_line(path: pathlib.Path, n: int, fresh: bool, tidy: pathlib.Path, moved: list[str]) -> str:
    """쓴 뒤의 끝 줄 — 자리 · 절 수 · 처음 지었나 · 정리 파일(`tidy`)로 옮겨 적은 절."""
    note = MOVED_NOTE.format(tidy=tidy, names=names_word(moved)) if moved else ""
    return WROTE.format(path=path, n=n, fresh=FRESH_NOTE if fresh else "", moved=note)


# ── 명령 손 ──────────────────────────────────────────────────────────────────

def cmd_where(args, folder: pathlib.Path) -> int:
    """자리 대기 — 업무 파일의 자리를 한 줄(또는 코드가 읽을 JSON)로 낸다."""
    path = folder / WORK_FILE
    say(where_json(folder, path) if args.json else where_line(folder, path, written_at(path)))
    return EXIT_OK


def cmd_write(args, folder: pathlib.Path) -> int:
    """바꿔 쓰기 — 받은 글을 앞 판과 견주어, 절이 빠지지 않았으면 옮겨 간 절을 정리 파일에 옮긴 뒤 업무 파일을 바꿔 끼운다. 안 쓰면 1."""
    try:
        text = read_given(args.infile)
    except OSError as exc:
        say(no_input_line(exc))
        return EXIT_REFUSED
    new = heads(text)
    if is_empty(text, new):
        say(EMPTY)
        return EXIT_REFUSED
    path = folder / WORK_FILE
    old_text = old_version(path)
    moving: list[str] = []
    if old_text is not None:
        lost, moving = compare(old_text, new)
        if lost:
            say(dropped_line(lost))
            return EXIT_REFUSED
    moved: list[str] = []
    try:
        make_folder(folder)
        if moving:
            moved = move_to_tidy(folder, old_text, moving)
        replace_with(path, text)
    except OSError as exc:
        drop_temp(path)
        say(failed_line(exc))
        return EXIT_REFUSED
    say(wrote_line(path, len(new), old_text is None, tidy_path(folder), moved))
    return EXIT_OK


def parser() -> argparse.ArgumentParser:
    """명령의 인자 꼴 — 하위 둘(where · write)과 그 인자."""
    ap = argparse.ArgumentParser(description="업무 파일(work.md)의 자리를 대고 받은 글로 바꿔 쓴다 — 메일함에는 닿지 않는다")
    sub = ap.add_subparsers(dest="command", required=True)
    where = sub.add_parser("where", help="사용자 폴더 · 업무 파일의 자리 · 있나 · 마지막으로 쓴 때")
    where.add_argument("--json", action="store_true",
                       help='코드가 읽을 꼴 — {"folder": <사용자 폴더>, "work_file": <업무 파일의 자리>} 한 줄만 낸다(있나 · 쓴 때는 그 파일에서 본다)')
    w = sub.add_parser("write", help="받은 글 전부로 업무 파일을 바꿔 쓴다 — 앞 판의 절이 빠졌거나 빈 글이면 안 쓴다")
    w.add_argument("--in", dest="infile", help="표준 입력 대신 읽을 파일")
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    """명령 입구 — 표준 출력을 UTF-8 로 잡고 하위 명령을 사용자 폴더와 함께 그 손에 넘긴다."""
    utf8_out()
    args = parser().parse_args(argv)
    return {"where": cmd_where, "write": cmd_write}[args.command](args, home())


if __name__ == "__main__":
    sys.exit(main())
