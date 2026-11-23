"""회사 메일 손의 글 꼴 — 그 손의 미리 보기와 실행이 찍는 줄을 잡아 둘 바꿈 · 맺을 결과로 읽는다. 꼴이 다르면 `Refused` · `Mismatch` 를
까닭의 이름과 값으로 올린다(문장은 `journal_words.py` 가 고른다).

꼴의 원본은 회사 메일 스킬 `scripts/mail.py` 의 `cmd_preview_*` · `cmd_apply_*` 가 찍는 줄이다 — 거기서 바뀌면 여기를 함께 바꾼다.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

import journal_const as c
from journal_const import (DONE, FOLDER, FOLDER_CREATE, FOLDER_DELETE, FOLDER_KINDS, INBOX, MAIL_KINDS, MOVE, PLACE_NAMES, PLACE_WORDS,
                           Mismatch, Refused, RESTORE, RULE_ADD, RULE_DELETE, RULE_EDIT, TRASH, UNKNOWN)

FOLDER_WORD = "폴더 "
SEP = " · "
HEADS = {
    MOVE: re.compile(r"^옮길 메일 (\d+)통 → (.+?) — 아직 안 옮겼다"),
    TRASH: re.compile(r"^휴지통으로 보낼 메일 (\d+)통 — 아직 안 보냈다"),
    RESTORE: re.compile(r"^휴지통에서 되살릴 메일 (\d+)통 — 아직 안 되살렸다"),
    FOLDER_CREATE: re.compile(r"^폴더 만들기: (.+) — 아직 안 바꿨다$"),
    FOLDER_DELETE: re.compile(r"^폴더 지우기: (.+) \(비어 있고 하위 폴더가 없어야 지운다\) — 아직 안 바꿨다$"),
    RULE_ADD: re.compile(r"^규칙 넣기: (.+)$"),
    RULE_EDIT: re.compile(r"^규칙 고치기:$"),
    RULE_DELETE: re.compile(r"^규칙 지우기: (.+)$"),
}
ITEM = re.compile(r"^  (?:읽음|안읽음) · (.+)$")          # 메일 한 줄 — 읽음 · 제목 · 보낸 분 · 자리 · 메일 번호
KEY_LINE = re.compile(r"^확인 열쇠: ([0-9a-f]+)$")
APPLIED_KEY = re.compile(r" · 열쇠 ([0-9a-f]+)$")          # 「됐다」 줄 끝 — 실행이 맞춘 확인 열쇠(넣거나 고친 규칙은 규칙 열쇠 뒤에 선다)
RULE_NOW, RULE_THEN = "  지금 ", "  바꿀 "
UNID_FORM = "[0-9A-F]{32}"                                # 메일 번호의 꼴 — 줄 끝에 서는 것과 인자로 받는 것이 같다
UNID = re.compile(f"^{UNID_FORM}$")
TAIL_UNID = re.compile(f" · ({UNID_FORM})$")
SUCCESS = {MOVE: "옮겼다: ", TRASH: "휴지통으로 보냈다: ", RESTORE: "되살렸다: ", FOLDER_CREATE: "만들었다: ",
           FOLDER_DELETE: "지웠다: ", RULE_ADD: "규칙을 넣었다: ", RULE_EDIT: "규칙을 고쳤다: ", RULE_DELETE: "규칙을 지웠다"}
# 열쇠가 없는 「됐다」 줄이 대는 것 — 메일 수와 받을 자리(`cmd_apply_move · trash · restore`) · 폴더 경로(`cmd_apply_folder`)
APPLIED = {MOVE: re.compile(r"^옮겼다: (\d+)통 → (.+?) \(다시 봐서"), TRASH: re.compile(r"^휴지통으로 보냈다: (\d+)통 \("),
           RESTORE: re.compile(r"^되살렸다: (\d+)통 \("), FOLDER_CREATE: re.compile(r"^만들었다: (.+?) \(다시 봐서"),
           FOLDER_DELETE: re.compile(r"^지웠다: (.+?) \(다시 봐서")}
STALE = ("확인 열쇠가", "않았다")                        # 열쇠가 안 맞아 아무것도 안 바꿨다는 실행 손의 줄 — 둘 다 든다
ELSEWHERE = re.compile(r"^! (\d+)통은 받은편지함에 없다")


def place_of(rest: str) -> tuple[str, str] | None:
    """메일 한 줄의 「읽음 · 」 뒤 → (자리, 폴더 경로). 끝의 메일 번호는 떼고 본다. 못 읽으면 None."""
    for word, place in PLACE_WORDS.items():
        if rest.endswith(SEP + word):
            return place, ""
    i = rest.rfind(SEP + FOLDER_WORD)
    if i < 0:
        return None
    path = rest[i + len(SEP + FOLDER_WORD):]
    return (FOLDER, path) if path else None


def _items(lines: Sequence[str]) -> list[str]:
    """머리 다음의 들여 쓴 줄들 — 메일 한 통에 한 줄."""
    out = []
    for line in lines[1:]:
        if not line.startswith("  "):
            break
        out.append(line)
    return out


def from_head(kind: str, text: str) -> list[str]:
    """미리 보기의 빈 줄 아닌 줄들을 그 종류의 머리 줄부터 — 머리 앞의 줄(표준 오류를 함께 흘린 경고)은 건너뛴다. 머리가 없으면 `Refused`."""
    lines = [x for x in text.splitlines() if x.strip()]
    at = next((i for i, x in enumerate(lines) if HEADS[kind].match(x)), None)
    if at is None:
        raise Refused(c.WHY_IS_HEAD, kind=kind)
    return lines[at:]


def key_of(lines: Sequence[str]) -> str:
    """미리 보기의 확인 열쇠 — 그 줄이 없으면 `Refused`."""
    key = next((m.group(1) for x in lines if (m := KEY_LINE.match(x))), None)
    if key is None:
        raise Refused(c.WHY_IS_KEY)
    return key


# 옛 꼴의 부름 — 준 메일 번호 · 받을 자리가 미리 보기와 같은지만 댄다(안 줬으면 지나간다)

def check_given_count(unids: Sequence[str], items: Sequence[str]) -> None:
    """준 메일 번호의 수가 미리 보기의 메일 줄 수와 같은가 — 다르면 `Refused`."""
    if unids and len(unids) != len(items):
        raise Refused(c.WHY_IS_GIVEN, unids=len(unids), lines=len(items))


def check_given_target(shown: str, to: str | None) -> None:
    """준 받을 자리가 미리 보기 머리의 받을 자리와 같은가 — 다르면 `Refused`."""
    if to is not None and shown != (to or PLACE_NAMES[INBOX]):
        raise Refused(c.WHY_IS_TARGET, head=shown, given=to or PLACE_NAMES[INBOX])


def check_given_unid(unids: Sequence[str], n: int, unid: str) -> None:
    """준 n 번째 메일 번호가 n 번째 메일 줄 끝의 번호와 같은가 — 다르면 `Refused`."""
    if unids and unids[n - 1] != unid:
        raise Refused(c.WHY_IS_ORDER, n=n)


def target_of(shown: str, to: str | None) -> str:
    """옮기기 머리의 받을 자리 → 적을 꼴(받은편지함은 빈 것). 옛 꼴로 준 받을 자리와 다르면 `Refused`."""
    check_given_target(shown, to)
    return "" if shown == PLACE_NAMES[INBOX] else shown


def tail_of(n: int, line: str) -> tuple[str, str]:
    """n 번째 메일 줄 → (줄 끝의 메일 번호, 들여쓰기와 그 번호를 뗀 앞의 글). 끝에 번호가 없으면 `Refused`."""
    rest = line[2:]
    tail = TAIL_UNID.search(rest)
    if tail is None:
        raise Refused(c.WHY_IS_TAIL, n=n)
    return tail.group(1), rest[:tail.start()]


def origin_of(kind: str, n: int, line: str, rest: str) -> dict[str, str]:
    """n 번째 메일 줄이 말한 원래 자리 — {"place", "folder"}. 되살리기는 자리를 안 적어 빈 것. 줄의 꼴이 다르거나 자리를 못 읽으면 `Refused`."""
    if not ITEM.match(line):
        raise Refused(c.WHY_IS_PLACE, n=n)
    if kind == RESTORE:
        return {}
    where = place_of(rest)
    if where is None:
        raise Refused(c.WHY_IS_PLACE, n=n)
    return {"place": where[0], "folder": where[1]}


def read_mails(kind: str, items: Sequence[str], unids: Sequence[str]) -> list[dict[str, str]]:
    """미리 보기의 메일 줄들 → 잡아 둘 메일들. 줄마다 번호 읽기 → 옛 꼴로 준 번호에 대기 → 자리 읽기의 차례로 멈춘다 — 번호와 자리는 한
    줄에서 읽는다."""
    mails = []
    for n, line in enumerate(items, 1):
        unid, rest = tail_of(n, line)
        check_given_unid(unids, n, unid)
        mails.append({"unid": unid, **origin_of(kind, n, line, rest)})
    return mails


def mail_fields(kind: str, head: re.Match[str], items: Sequence[str], unids: Sequence[str], to: str | None) -> dict[str, Any]:
    """메일을 건드리는 미리 보기의 칸 — 옮기기면 받을 자리(`to`), 그리고 메일마다의 번호 · 자리(`mails`). 줄 수가 머리의 수와 다르면
    `Refused`, 그 뒤 옛 꼴로 준 번호의 수 → 받을 자리 → 줄마다의 차례로 댄다."""
    if len(items) != int(head.group(1)):
        raise Refused(c.WHY_IS_COUNT, lines=len(items), head=head.group(1))
    check_given_count(unids, items)
    target = {"to": target_of(head.group(2), to)} if kind == MOVE else {}
    return {**target, "mails": read_mails(kind, items, unids)}


def rule_of(kind: str, head: re.Match[str], lines: Sequence[str]) -> dict[str, str]:
    """규칙 미리 보기의 판 — 고치기는 「지금」 · 「바꿀」 두 줄(못 읽으면 `Refused`), 넣기는 머리의 바뀔 판, 지우기는 머리의 지금 판."""
    if kind == RULE_EDIT:
        now = next((x[len(RULE_NOW):] for x in lines if x.startswith(RULE_NOW)), None)
        then = next((x[len(RULE_THEN):] for x in lines if x.startswith(RULE_THEN)), None)
        if not now or not then:
            raise Refused(c.WHY_IS_RULE_LINES)
        return {"before": now, "after": then}
    return {"after": head.group(1)} if kind == RULE_ADD else {"before": head.group(1)}


def read_preview(kind: str, text: str, unids: Sequence[str], to: str | None) -> dict[str, Any]:
    """미리 보기 → 잡아 둘 바꿈 — 머리부터의 줄 · 확인 열쇠 · 종류마다의 칸(메일 · 폴더 경로 · 규칙의 판)을 그 손가락으로 읽어 엮는다. 준
    `unids` · `to` 는 옛 꼴의 부름이라 미리 보기와 같은지만 댄다(안 줬으면 빈 것 · None). 꼴이 다르면 `Refused`."""
    lines = from_head(kind, text)
    head = HEADS[kind].match(lines[0])
    hold: dict[str, Any] = {"kind": kind, "key": key_of(lines)}
    if kind in MAIL_KINDS:
        hold.update(mail_fields(kind, head, _items(lines), unids, to))
    elif kind in FOLDER_KINDS:
        hold["path"] = head.group(1)
    else:
        hold["rule"] = rule_of(kind, head, lines)
    return hold


def preview_body(kind: str, text: str) -> list[str]:
    """미리 보기에서 사람에게 보일 몸 — 머리 줄 다음부터 확인 열쇠 줄 앞까지. 꼴은 `read_preview` 가 먼저 댔다고 본다."""
    lines = from_head(kind, text)
    key = next(i for i, x in enumerate(lines) if KEY_LINE.match(x))
    return lines[1:key]


def read_shown(kind: str, text: str, unids: Sequence[str], to: str | None) -> tuple[dict[str, Any], list[str]]:
    """`show` 가 받는 미리 보기 → (적을 조각, 보일 몸). 꼴이 다르면 `Refused`. 옮기기 조각은 휴지통 미리 보기도 받는다(받을 자리는 `to`)."""
    lines = text.splitlines()
    if kind == MOVE and not any(HEADS[MOVE].match(x) for x in lines) and any(HEADS[TRASH].match(x) for x in lines):
        if to is None:
            raise Refused(c.WHY_IS_TARGET_MISSING)
        return {**read_preview(TRASH, text, unids, None), "kind": MOVE, "to": to}, preview_body(TRASH, text)
    return read_preview(kind, text, unids, to), preview_body(kind, text)


def check_applied(hold: dict[str, Any], ok: str) -> None:
    """「됐다」 줄이 잡아 둔 바꿈의 실행인가 — 다르거나 못 읽으면 `Mismatch`. 줄 끝의 확인 열쇠가 있고 잡아 둔 미리 보기의 열쇠를 알면
    그 둘로 댄다(열쇠는 미리 보기가 본 판 — 받을 자리와 메일마다의 번호 · 자리 · 폴더 경로 · 규칙의 판 — 의 지문이다). 열쇠가 없는 줄
    (갱신 전의 손)이나 열쇠를 적기 전에 잡아 둔 바꿈은 메일 수 · 받을 자리 · 폴더 경로로 대고, 규칙은 대지 않는다."""
    got_key, want_key = APPLIED_KEY.search(ok), hold.get("key")
    if got_key and want_key:
        if got_key.group(1) != want_key:
            raise Mismatch(c.WHY_IS_APPLIED_KEY, got=got_key.group(1), want=want_key)
        return
    kind = hold["kind"]
    form = APPLIED.get(kind)
    if form is None:
        return
    got = form.match(ok)
    if got is None:
        raise Mismatch(c.WHY_IS_APPLIED_FORM)
    if kind in MAIL_KINDS:
        count, want = int(got.group(1)), len(hold.get("mails") or [])
        if count != want:
            raise Mismatch(c.WHY_IS_APPLIED_COUNT, got=count, want=want)
        if kind == MOVE and got.group(2) != (hold.get("to") or PLACE_NAMES[INBOX]):
            raise Mismatch(c.WHY_IS_APPLIED_TARGET, got=got.group(2), want=hold.get("to") or PLACE_NAMES[INBOX])
    elif got.group(1) != hold.get("path"):
        raise Mismatch(c.WHY_IS_APPLIED_FOLDER, got=got.group(1), want=hold.get("path"))


def read_applied(hold: dict[str, Any], text: str) -> tuple[str | None, dict[str, Any]]:
    """실행의 글 → (결과 · 안 바뀌었으면 None, 더 적을 것). 「됐다」 줄이 잡아 둔 바꿈과 다르면 `Mismatch`."""
    lines = [x for x in text.splitlines() if x.strip()]
    kind = hold["kind"]
    ok = next((x for x in lines if x.startswith(SUCCESS[kind])), None)
    if ok is None:
        stale = any(all(w in x for w in STALE) for x in lines)
        return (None, {}) if stale else (UNKNOWN, {})
    check_applied(hold, ok)
    more: dict[str, Any] = {}
    if kind in (RULE_ADD, RULE_EDIT):
        tail = TAIL_UNID.search(APPLIED_KEY.sub("", ok))
        if tail:
            more["rule_unid"] = tail.group(1)
    if kind == RESTORE:
        away = next((ELSEWHERE.match(x) for x in lines if ELSEWHERE.match(x)), None)
        if away:
            more["elsewhere"] = int(away.group(1))
    return DONE, more
