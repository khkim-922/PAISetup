"""다음 걸음의 명령 줄 — 회사 메일 손의 미리 보기 · 실행을 이 스킬의 `journal.py` 에 흘리는 줄을 미리 보기 · 기록이 이미 든 값으로 짓는다.

스킬은 한 부모 폴더에 나란히 깔린다(Git Bash 에서 그대로 칠 꼴). 곁에 손이 없으면 자리 대신 표지를 낸다 — 모델이 그 스킬의 자리로 채운다.
명령 이름과 인자(--to · --inbox · --create · --parent · --delete · --confirm)의 원본은 그 스킬 `mail.py` 의 `parser` 다 — 거기서 바뀌면
여기의 `VERBS` 와 `hand_args` 를 함께 바꾼다.
"""

from __future__ import annotations

import pathlib
import shlex
from collections.abc import Sequence
from typing import Any

from journal_const import (CMD_DONE, CMD_HOLD, FOLDER_CREATE, FOLDER_DELETE, FOLDER_SEP, JOURNAL_SCRIPT, MOVE, RESTORE, RULE_ADD, RULE_DELETE,
                           RULE_EDIT, TRASH, UNDOES_FLAG)

SELF = pathlib.Path(__file__).resolve().with_name(JOURNAL_SCRIPT)   # 줄 끝에서 미리 보기 · 실행의 글을 받는 이 스킬의 명령
SIBLING_HAND = SELF.parents[2] / "company-mail" / "scripts" / "mail.py"
HAND = SIBLING_HAND if SIBLING_HAND.is_file() else pathlib.PurePosixPath("<회사 메일 스킬>/scripts/mail.py")
RUN = ("python", "-X", "utf8", "-I")
# 종류 → 손의 preview-<말> · apply-<말>
VERBS = {MOVE: "move", TRASH: "trash", RESTORE: "restore", FOLDER_CREATE: "folder", FOLDER_DELETE: "folder", RULE_ADD: "rule",
         RULE_EDIT: "rule", RULE_DELETE: "rule"}
PREVIEW_VERB, APPLY_VERB, CONFIRM = "preview-{verb}", "apply-{verb}", "--confirm"
PIPE = " | "


def command(script: pathlib.PurePath, *words: str) -> str:
    """Git Bash 에서 그대로 칠 명령 하나 — 낱말마다 셸 따옴표를 씌운다(폴더 경로의 빈칸 · 쉼표 · 역슬래시가 그대로 간다)."""
    return " ".join([*RUN, *(shlex.quote(w) for w in (script.as_posix(), *words))])


def hand_args(kind: str, *, to: str = "", unids: Sequence[str] = (), path: str = "", rule_unid: str = "") -> list[str] | None:
    """그 바꿈을 회사 메일 스킬에 줄 인자 — 미리 보기와 실행이 같다(실행은 `--confirm` 을 더한다). 값을 다 모르면 None — 규칙 넣기 ·
    고치기의 칸은 기록에 사람 말(규칙 한 줄)로만 있다."""
    if kind == MOVE:
        return [*(["--to", to] if to else ["--inbox"]), *unids]
    if kind in (TRASH, RESTORE):
        return list(unids)
    if kind == FOLDER_CREATE:
        parent, _, name = path.rpartition(FOLDER_SEP)
        return ["--create", name, *(["--parent", parent] if parent else [])]
    if kind == FOLDER_DELETE:
        return ["--delete", path]
    if kind == RULE_DELETE and rule_unid:
        return ["--delete", rule_unid]
    return None


def preview_command(kind: str, args: Sequence[str]) -> str:
    """손의 미리 보기 명령 하나."""
    return command(HAND, PREVIEW_VERB.format(verb=VERBS[kind]), *args)


def preview_line(kind: str, args: Sequence[str], *then: str) -> str:
    """손의 미리 보기를 `journal.py` 의 하위 명령(`then`)에 흘리는 줄."""
    return preview_command(kind, args) + PIPE + command(SELF, *then)


def undo_line(kind: str, args: Sequence[str], entry_id: str) -> str:
    """기록 하나를 되돌리는 미리 보기를 `journal.py hold <종류> --undoes <기록 번호>` 에 흘리는 줄."""
    return preview_line(kind, args, CMD_HOLD, kind, UNDOES_FLAG, entry_id)


def apply_line(kind: str, args: Sequence[str], key: str) -> str:
    """잡아 둔 미리 보기의 실행을 `done` 에 흘리는 줄 — 미리 보기와 같은 인자에 그 열쇠."""
    return command(HAND, APPLY_VERB.format(verb=VERBS[kind]), *args, CONFIRM, key) + PIPE + command(SELF, CMD_DONE)


def held_apply_line(hold: dict[str, Any], rule_unid: str = "") -> str | None:
    """잡아 둔 바꿈의 실행 줄 — 손에 줄 인자를 다 모르면(규칙의 칸) None."""
    args = held_args(hold, rule_unid)
    return apply_line(hold["kind"], args, hold["key"]) if args is not None else None


def held_args(hold: dict[str, Any], rule_unid: str = "") -> list[str] | None:
    """잡아 둔 바꿈을 손에 줄 인자 — 미리 보기에서 읽은 받을 자리 · 메일 번호 · 폴더 경로. 규칙 지우기는 미리 보기에 열쇠가 없어
    부르는 쪽이 기록에서 준다(`rule_unid`)."""
    return hand_args(hold["kind"], to=hold.get("to") or "", unids=[m["unid"] for m in hold.get("mails") or []], path=hold.get("path") or "",
                     rule_unid=rule_unid)
