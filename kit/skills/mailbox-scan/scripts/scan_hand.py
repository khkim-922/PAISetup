"""회사 메일 손(스킬 company-mail 의 `scripts/mail.py`)을 명령으로 부르고, 그 손이 찍은 사람용 글을 메일 머리로 푼다.

손의 코드는 싣지 않고 프로세스로 부른다. 손의 글은 모든 줄을 아는 꼴에 대고 끝 줄이 댄 수와 견줘, 어긋나면 `ShapeError` 로 멈춘다.
출력은 UTF-8 로만 풀고 못 풀면 멈춘다 — 잘못 풀면 폴더 경로가 앞 판과 어긋나 거짓 옮김이 사람이 한 일로 선다.

    hand = find_hand(explicit)               # --hand · MAILBOX_SCAN_HAND · SECRETARY_SKILLS · 도구 홈 차례 — 없으면 HandMissing
    has_since(hand)                          # 「list --since」가 있는 판인가(`list --help` 로 묻는다)
    got = call(hand, ["folders"])            # Called(code, lines, said) — 손의 종료 값 그대로
    parse_folders(got.lines) · parse_rules · parse_list(got.lines, box, folder) · parse_since(got.lines, folders)
    rule_folder(rule["text"])                # 그 규칙이 메일을 옮기는 폴더 — 폴더로 옮기지 않는 규칙이면 None

꼴의 원본 — 손 `mail.py` 의 `cmd_folders` · `cmd_rules` · `rule_line` · `cmd_list` · `entry_line` · `who_sent` · `since_line` ·
`list_since` 가 찍는 줄(6d3d1add 판). 손이 기계가 읽는 꼴(JSON)을 내면 이 파일이 걷힌다.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

from scan_const import (HAND_ENV, HAND_SCRIPT, HAND_SKILL, HAND_TIMEOUT_S, MAIL_DATE, MAIL_DATE_MINUTE, SESSION_FILE_ENV, SESSION_HAND_ENV,
                        SESSION_HAND_SCRIPT, SESSION_PLACES, SESSION_PLACES_KEY, SESSION_SKILL, SKILL_HOMES, SKILLS_ENV)

SEP = " · "
UNID_TAIL = re.compile(r" · ([0-9A-Fa-f]{32})$")
MARKED = re.compile(r"^\[(읽음|안읽음)\] ")
SENT_MARK = "[보냄] "
SENT_WORD = "받는 분 "
INBOX_WORD, SENT_BOX_WORD, FOLDER_WORD = "받은편지함", "보낸편지함", "폴더 "
FILES_TAIL = re.compile(r" · 첨부 (\d+)$")
WHO_BOTH = re.compile(r"^(.*) <([^<>]*)>$")
ADDRESS = re.compile(r"^[\w.+-]+@[\w-]+(?:\.[\w-]+)+$")
NO_SENDER, UNFILLED_SENDER = "(보낸 분 없음)", "(보낸 분 못 채움)"   # 손 mail.py 의 `who` · `UNFILLED_SENDER`

# 끝 줄 — 손이 명령마다 찍는 꼴. 이 밖의 줄은 메일 줄이 아니면 꼴이 바뀐 것이다
FOLDERS_END = re.compile(r"^— 폴더 (\d+)개$")
RULES_END = re.compile(r"^— 규칙 (\d+)개 \(=: 일치 · ∋: 포함\)$")
RULE_LINE = re.compile(r"^((?:받은|보낸) 메일 · .*) · ([0-9A-Fa-f]{32})$")
# 규칙 글의 동작 칸 — 폴더로 옮기는 규칙만 「 · 폴더로 옮김 → <경로>」를 달고, 자동전달이 걸렸으면 그 뒤에 표지가 붙는다(손의 `rule_line`)
RULE_MOVE = " · 폴더로 옮김 → "
RULE_FORWARD_TAIL = " · ⚠ 자동전달 — 이 손은 안 고친다"
LIST_END = re.compile(r"^— (받은편지함|폴더 .+?) (\d+)통을 보였다 · 그 가운데 안 읽음 (\d+)(?: — 그 뒤의 안 읽음까지 보려면 --unread)?"
                      r"(?: \(이 폴더의 메일은 read <unid> --folder \".*\" 가 빠르다\))?(?: · (.*))?$")
SENT_END = re.compile(r"^— 보낸편지함 (\d+)통 · 받는 분 칸은 첫 사람만이다 — .*$")
FILL_NOTE = re.compile(r"^(?:보낸 분 주소를 못 채운 폴더 메일 (\d+)통\(모든편지함 새것 \d+줄에 없다\)|"
                       r"이 메일함에 모든편지함 보기가 없어 폴더 메일 (\d+)통의 보낸 분 주소를 못 채웠다)$")
SINCE_HEAD = re.compile(r"^— (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) 부터의 메일 (\d+)통(?:\(([^()]*)\))?"
                        r"(?: · 가장 늦은 메일 (\S* \S*) · ([0-9A-Fa-f]{32}))?( · 그 시각부터 메일이 없다)?$")
SINCE_STUCK = re.compile(r"^— ⚠ 그 시각까지 못 내려간 자리가 있다 — (.*) · 그 앞은 안 봤다\(그 사이 메일이 없다는 뜻이 아니다\)$")
STUCK_BOX = re.compile(r"(받은편지함|보낸편지함|폴더 .+?) 새것 \d+통까지만 봤다\(")
SINCE_REACHED = re.compile(r"^— 받은편지함 · 폴더 (\d+)개 · 보낸편지함 — 그 시각까지 다 봤다"
                           r"(?: · 모든편지함에만 있는 (\d+)통은 안 냈다\(.*\))?$")
SINCE_SENT_NOTE = re.compile(r"^— 보낸 메일의 받는 분은 첫 사람만이다 — .*$")
SINCE_MORE = re.compile(r"^— (\d+)–(\d+)번째를 보였다 · 더 옛 메일 (\d+)통이 남았다 — 다음: 같은 명령에 --start (\d+)$")
SINCE_FILL = re.compile(r"^— (" + FILL_NOTE.pattern[1:-1] + r")$")
NO_FOLDER = re.compile(r"^그런 폴더가 없다: ")   # 손의 종료 2 가운데 「그 폴더가 지금 없다」 — 이름이 바뀌었거나 지워졌다


class HandMissing(Exception):
    """회사 메일 손을 못 찾았다 — 글자가 어디를 봤는지 말한다."""


class ShapeError(Exception):
    """손의 글이 이 파일이 아는 꼴이 아니다 — 메일의 글은 싣지 않고 어느 명령의 몇째 줄인지만 댄다."""


@dataclass
class Called:
    code: int
    lines: list[str]
    said: str              # 0 이 아닐 때 손이 댄 까닭(끝 줄) — 메일함의 글(폴더 이름)이 들 수 있다
    command: str = ""


@dataclass
class Listed:
    """한 상자의 한 쪽 — 메일 머리 · 끝 줄이 댄 수 · 보낸 분을 못 채운 폴더 메일 수."""
    mails: list[dict[str, Any]] = field(default_factory=list)
    unfilled: int = 0


@dataclass
class Since:
    """「이 시각 뒤」 목록 한 쪽."""
    mails: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0
    latest: tuple[str, str] | None = None        # (때, 번호)
    reached: bool = False
    stuck: list[str] = field(default_factory=list)
    lonely: int = 0
    unfilled: int = 0
    next_start: int | None = None


# ── 손 찾기 · 부르기 ────────────────────────────────────────────────────────────

def skill_roots() -> list[pathlib.Path]:
    """볼 스킬 뿌리 — `SECRETARY_SKILLS` 가 있으면 그것 하나, 없으면 도구 홈 셋."""
    given = os.environ.get(SKILLS_ENV, "").strip()
    if given:
        return [pathlib.Path(given).expanduser()]
    return [pathlib.Path.home().joinpath(*parts) for parts in SKILL_HOMES]


def find_hand(explicit: str | None = None) -> pathlib.Path:
    """손 `mail.py` 의 자리 — `--hand` → `MAILBOX_SCAN_HAND` → 스킬 뿌리들 차례. 어디에도 없으면 `HandMissing`."""
    for given, word in ((explicit, "--hand"), (os.environ.get(HAND_ENV, ""), HAND_ENV)):
        if given and given.strip():
            path = pathlib.Path(given.strip()).expanduser()
            if not path.is_file():
                raise HandMissing(f"{word} 가 가리키는 회사 메일 손이 없다: {path}")
            return path.resolve()
    tried = []
    for root in skill_roots():
        path = root / HAND_SKILL / pathlib.Path(*HAND_SCRIPT)
        tried.append(str(path))
        if path.is_file():
            return path.resolve()
    raise HandMissing("회사 메일 손(company-mail 의 scripts/mail.py)을 못 찾았다 — 본 자리: " + " · ".join(tried))


def _quiet() -> dict[str, Any]:
    """창 없는 실행(작업 스케줄러의 pythonw)에서 손 · 손이 띄우는 node 가 콘솔 창을 안 띄우게 — 손에 창 없는 콘솔을 준다."""
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}


def call(hand: pathlib.Path, args: list[str], timeout: float = HAND_TIMEOUT_S) -> Called:
    """손 한 번 — 종료 값 · 표준 출력의 줄 · 0 이 아닐 때의 까닭. 표준 오류(손의 경고)는 안 읽는다. 출력을 UTF-8 로 못 풀면 `ShapeError`.
    시한을 넘기면 손의 종료 1 과 같게 낸다(`said` 가 시한을 말한다)."""
    command = " ".join(a for a in args[:1])
    try:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(hand), *args], capture_output=True, timeout=timeout,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"}, stdin=subprocess.DEVNULL, **_quiet())
    except subprocess.TimeoutExpired:
        return Called(1, [], f"회사 메일 손이 {timeout:.0f}초 안에 안 끝났다", command)
    try:
        text = done.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ShapeError(f"{command} — 손의 출력을 UTF-8 로 못 풀었다({exc.start}째 바이트)") from exc
    lines = [x.rstrip("\r") for x in text.splitlines() if x.strip()]
    said = lines[-1] if lines and done.returncode != 0 else ""
    return Called(done.returncode, lines, said, command)


def has_since(hand: pathlib.Path) -> bool:
    """「list --since」를 받는 판인가 — 손의 `list --help` 에 그 깃발이 서나로 묻는다(그 깃발이 없는 옛 판의 손이 깔린 PC 도 있다)."""
    got = call(hand, ["list", "--help"], timeout=60)
    return got.code == 0 and any(re.search(r"(?<![\w-])--since\b", x) for x in got.lines)


def session_file(hand: pathlib.Path) -> pathlib.Path | None:
    """손이 쓰는 세션 파일의 자리 — `MAILBOX_COOKIES`, 없으면 형제 스킬 ep-login 의 받는 손 곁 `places.json` 의 기본 자리. 모르면
    None."""
    raw = os.environ.get(SESSION_FILE_ENV, "").strip()
    if not raw:
        js = os.environ.get(SESSION_HAND_ENV, "").strip()
        script = pathlib.Path(js) if js else hand.parents[2] / SESSION_SKILL / pathlib.Path(*SESSION_HAND_SCRIPT)
        try:
            raw = json.loads(script.with_name(SESSION_PLACES).read_text(encoding="utf-8")).get(SESSION_PLACES_KEY) or ""
        except (OSError, ValueError, AttributeError):
            return None
        if not raw:
            return None
    return pathlib.Path(os.path.expanduser(raw))


# ── 줄 풀기 ─────────────────────────────────────────────────────────────────────

def _date(text: str) -> str | None:
    """손이 찍은 때 → 쌓는 꼴(초까지). 분까지인 꼴(폴더 줄)은 「:00」 을 붙여 맞춘다. 두 꼴 밖이면 None."""
    from datetime import datetime
    for form, tail in ((MAIL_DATE, ""), (MAIL_DATE_MINUTE, ":00")):
        try:
            datetime.strptime(text, form)
        except ValueError:
            continue
        return text + tail
    return None


def _sender(text: str) -> dict[str, Any]:
    """손의 보낸 분 칸(`who_sent`) → 이름 · 주소 · 못 채움."""
    if text == NO_SENDER:
        return {"name": "", "addr": ""}
    if text == UNFILLED_SENDER:
        return {"name": "", "addr": "", "unfilled": True}
    both = WHO_BOTH.match(text)
    if both:
        return {"name": both.group(1), "addr": both.group(2)}
    return {"name": "", "addr": text} if ADDRESS.match(text) else {"name": text, "addr": ""}


def _split_place(rest: str, folders: list[str]) -> tuple[str, str, str] | None:
    """「자리 · 나머지」 → (상자, 폴더 경로, 나머지). 폴더 경로는 아는 폴더 가운데 가장 긴 것부터 맞추고, 없으면 첫 가름에서 끊는다."""
    if rest.startswith(INBOX_WORD + SEP):
        return "inbox", "", rest[len(INBOX_WORD + SEP):]
    if not rest.startswith(FOLDER_WORD):
        return None
    body = rest[len(FOLDER_WORD):]
    for path in sorted(folders, key=len, reverse=True):
        if body.startswith(path + SEP):
            return "folder", path, body[len(path + SEP):]
    path, sep, tail = body.partition(SEP)
    return ("folder", path, tail) if sep and path else None


def _received(line: str, box: str, folder: str, with_place: bool, folders: list[str]) -> dict[str, Any] | None:
    """받은편지함 · 폴더 줄(`entry_line`) → 메일 머리. 꼴이 아니면 None."""
    mark = MARKED.match(line)
    tail = UNID_TAIL.search(line)
    if not mark or not tail:
        return None
    middle = line[mark.end():tail.start()]
    date_text, sep, rest = middle.partition(SEP)
    if not sep:
        return None
    if with_place:
        split = _split_place(rest, folders)
        if split is None:
            return None
        box, folder, rest = split
    who, sep, subject = rest.partition(SEP)
    if not sep:
        return None
    files = FILES_TAIL.search(subject)
    date = _date(date_text)
    if date is None and date_text:
        return None
    mail = {"unid": tail.group(1).upper(), "box": box, "folder": folder, "date": date, "subject": subject,
            "unread": mark.group(1) == "안읽음", "files": 0, **_sender(who)}
    if files:
        mail["subject"], mail["files"] = subject[:files.start()], int(files.group(1))
    return mail


def _sent(line: str, with_place: bool) -> dict[str, Any] | None:
    """보낸편지함 줄 → 메일 머리. 받는 분은 손의 목록이 준 첫 사람(들)이다."""
    tail = UNID_TAIL.search(line)
    if not tail:
        return None
    middle = line[:tail.start()]
    if with_place:
        if not middle.startswith(SENT_MARK):
            return None
        middle = middle[len(SENT_MARK):]
    date_text, sep, rest = middle.partition(SEP)
    if not sep:
        return None
    if with_place:
        if not rest.startswith(SENT_BOX_WORD + SEP):
            return None
        rest = rest[len(SENT_BOX_WORD + SEP):]
    if not rest.startswith(SENT_WORD):
        return None
    to, sep, subject = rest[len(SENT_WORD):].partition(SEP)
    if not sep:
        return None
    date = _date(date_text)
    if date is None and date_text:
        return None
    return {"unid": tail.group(1).upper(), "box": "sent", "folder": "", "date": date, "subject": subject,
            "unread": None, "files": 0, "name": "", "addr": "", "to": to}


def _bad(command: str, n: int, why: str) -> ShapeError:
    return ShapeError(f"{command} 의 {n}째 줄 — {why}")


def parse_folders(lines: list[str]) -> list[str]:
    if not lines or not FOLDERS_END.match(lines[-1]):
        raise _bad("folders", len(lines), "끝 줄(「— 폴더 N개」)이 없다")
    paths = lines[:-1]
    if int(FOLDERS_END.match(lines[-1]).group(1)) != len(paths):
        raise _bad("folders", len(lines), f"끝 줄의 수와 폴더 줄 {len(paths)}개가 다르다")
    return paths


def parse_rules(lines: list[str]) -> list[dict[str, str]]:
    if not lines or not RULES_END.match(lines[-1]):
        raise _bad("rules", len(lines), "끝 줄(「— 규칙 N개 …」)이 없다")
    rules = []
    for n, line in enumerate(lines[:-1], 1):
        got = RULE_LINE.match(line)
        if not got:
            raise _bad("rules", n, "규칙 줄의 꼴이 아니다")
        rules.append({"unid": got.group(2).upper(), "text": got.group(1)})
    if int(RULES_END.match(lines[-1]).group(1)) != len(rules):
        raise _bad("rules", len(lines), f"끝 줄의 수와 규칙 줄 {len(rules)}개가 다르다")
    return rules


def rule_folder(text: str) -> str | None:
    """규칙 글(`parse_rules` 의 text) → 그 규칙이 메일을 옮기는 폴더의 경로. 폴더로 옮기지 않는 규칙이면 None. 동작 칸은 조건 뒤에
    서므로 마지막 표지에서 자른다 — 조건 값에 그 낱말이 들어도 안 헷갈린다."""
    _, mark, tail = text.rpartition(RULE_MOVE)
    if not mark:
        return None
    return tail[:-len(RULE_FORWARD_TAIL)] if tail.endswith(RULE_FORWARD_TAIL) else tail


def parse_list(lines: list[str], box: str, folder: str = "") -> Listed:
    """상자 하나의 한 쪽(`list` · `list --folder` · `list --sent` 에 --count · --start) → 메일 머리와 수."""
    command = {"inbox": "list", "sent": "list --sent"}.get(box, "list --folder")
    if not lines:
        raise _bad(command, 0, "끝 줄이 없다")
    end, body = lines[-1], lines[:-1]
    out = Listed()
    if box == "sent":
        head = SENT_END.match(end)
        if not head:
            raise _bad(command, len(lines), "끝 줄(「— 보낸편지함 N통 …」)이 아니다")
        for n, line in enumerate(body, 1):
            mail = _sent(line, with_place=False)
            if mail is None:
                raise _bad(command, n, "보낸편지함 줄의 꼴이 아니다")
            out.mails.append(mail)
        if int(head.group(1)) != len(out.mails):
            raise _bad(command, len(lines), f"끝 줄의 수와 메일 줄 {len(out.mails)}통이 다르다")
        return out
    head = LIST_END.match(end)
    want_place = INBOX_WORD if box == "inbox" else f"{FOLDER_WORD}{folder}"
    if not head or head.group(1) != want_place:
        raise _bad(command, len(lines), "끝 줄(「— <자리> N통을 보였다 …」)이 아니다")
    for n, line in enumerate(body, 1):
        mail = _received(line, box, folder, with_place=False, folders=[])
        if mail is None:
            raise _bad(command, n, "메일 줄의 꼴이 아니다")
        out.mails.append(mail)
    if int(head.group(2)) != len(out.mails) or int(head.group(3)) != sum(m["unread"] for m in out.mails):
        raise _bad(command, len(lines), f"끝 줄의 수 · 안 읽음과 메일 줄 {len(out.mails)}통이 다르다")
    if head.group(4):
        note = FILL_NOTE.match(head.group(4))
        if not note:
            raise _bad(command, len(lines), "끝 줄의 곁말이 아는 꼴이 아니다")
        out.unfilled = int(note.group(1) or note.group(2))
    return out


def parse_since(lines: list[str], folders: list[str], start: int) -> Since:
    """「이 시각 뒤」 목록(`list --since … --start N`) 한 쪽 → 메일 머리 · 끝 줄들이 댄 것. 메일 줄 수를 끝 줄의 차례와 견준다."""
    command = "list --since"
    out = Since()
    ends = 0
    head_seen = False
    for n, line in enumerate(lines, 1):
        if line.startswith("— "):
            ends += 1
            head = SINCE_HEAD.match(line)
            if head and not head_seen:
                head_seen = True
                out.total = int(head.group(2))
                if head.group(4):
                    out.latest = (head.group(4), head.group(5).upper())
                continue
            stuck = SINCE_STUCK.match(line)
            if stuck:
                out.stuck = STUCK_BOX.findall(stuck.group(1)) or [stuck.group(1)]
                continue
            reached = SINCE_REACHED.match(line)
            if reached:
                out.reached = True
                out.lonely = int(reached.group(2) or 0)
                continue
            fill = SINCE_FILL.match(line)
            if fill:
                note = FILL_NOTE.match(fill.group(1))
                out.unfilled = int(note.group(1) or note.group(2))
                continue
            more = SINCE_MORE.match(line)
            if more:
                lo, hi, out.next_start = int(more.group(1)), int(more.group(2)), int(more.group(4))
                if hi - lo + 1 != len(out.mails) or lo != start:
                    raise _bad(command, n, f"끝 줄이 댄 차례({lo}–{hi})와 메일 줄 {len(out.mails)}통이 다르다")
                continue
            if SINCE_SENT_NOTE.match(line):
                continue
            raise _bad(command, n, "끝 줄의 꼴이 아니다")
        if ends:
            raise _bad(command, n, "끝 줄 뒤에 메일 줄이 섰다")
        mail = _sent(line, with_place=True) if line.startswith(SENT_MARK) else _received(line, "inbox", "", True, folders)
        if mail is None:
            raise _bad(command, n, "메일 줄의 꼴이 아니다")
        out.mails.append(mail)
    if not head_seen:
        raise _bad(command, len(lines), "머리 끝 줄(「— <시각> 부터의 메일 N통 …」)이 없다")
    if not (out.reached or out.stuck):
        raise _bad(command, len(lines), "그 시각까지 다 봤나를 대는 끝 줄이 없다")
    if out.next_start is None and out.total - (start - 1) != len(out.mails):
        raise _bad(command, len(lines), f"끝 줄의 수({out.total}통 가운데 {start}째부터)와 메일 줄 {len(out.mails)}통이 다르다")
    return out
