"""메일함에서 바꾼 것을 적어 두고, 되돌릴 차례를 낸다 — 회사 메일 스킬의 미리 보기와 실행이 낸 글을 받는다. 메일함에는 닿지 않는다.

    <미리 보기> | python -X utf8 journal.py show <종류> --piece <n> [--to <폴더> | --inbox] [<메일 번호> …]   안의 조각 n 으로 적고 보인다
    <미리 보기> | python -X utf8 journal.py hold <종류> [--to <폴더> | --inbox] [--shown <n>] [--undoes <기록 번호>] [<메일 번호> …]
    <실행>      | python -X utf8 journal.py done
    python -X utf8 journal.py drop                      사람이 안 하기로 하신 미리 보기를 놓는다 — 실행하지 않았을 때만
    python -X utf8 journal.py log [--most N]            바꾼 것의 기록 — 새것부터
    python -X utf8 journal.py mails [<기록 번호> …]     바꾼 메일 — 기록마다 메일 번호 · 원래 자리 → 간 자리(읽기만 · 옛것부터)
    python -X utf8 journal.py undo <기록 번호>          그 바꿈을 되돌리는 차례와 메일 번호
    (`show` · `hold` · `done` 은 `--in <파일>` 로도 받는다)

종류 — move(메일 옮기기) · trash(휴지통으로) · restore(휴지통에서 되살리기) · folder-create · folder-delete · rule-add · rule-edit ·
rule-delete. `move` 는 회사 메일 스킬에 준 받을 자리를 같이 준다(`--to <폴더 경로>` 나 `--inbox`). 메일을 건드리는 셋은 회사 메일 스킬에
준 메일 번호를 **같은 차례로** 그대로 준다.

명령마다 무엇을 대나는 `references/DESIGN.md` 「명령마다 하는 일」이 든다.

남기는 것 — 사용자 폴더(`home()`)의 `LOG_FILE`(덧붙이기만) · 잡아 둔 바꿈 `HELD_FILE` · 보여 드린 안의 조각 `SHOWN_FILE`. 메일 번호 ·
자리 · 폴더 경로 · 규칙의 판만 적고 제목 · 보낸 분 · 본문은 안 적는다.

종료 값 — 0 됐다 · 1 못 했다(꼴이 다르다 · 보여 드린 조각과 다르다 · 실행의 글이 잡아 둔 바꿈과 다르다 · 잡아 둔 것이 없다 · 그런
기록이 없다 — 다음 걸음을 끝 줄이 말한다) · 2 인자가 틀렸다.

⚠ 메일마다의 자리는 미리 보기의 줄 차례로 메일 번호에 잇는다 — 회사 메일 스킬에 준 번호와 다른 차례로 주면 자리가 엇갈려 적힌다.
⚠ 실행의 「됐다」 줄에는 메일 번호가 없다 — 수 · 받을 자리 · 폴더가 같은 다른 바꿈의 실행은 가르지 못한다.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from collections.abc import Sequence
from datetime import datetime
from typing import Any

# 사용자 폴더 — 원본은 스킬 mailbox-scan 의 `scripts/scan_const.py` 「자리」다. 스킬은 서로의 코드를 싣지 않아 옮겨 든다 — 바꾸면 함께 바꾼다
HOME_ENV = "MAIL_SECRETARY_HOME"         # 개발 · 검사가 사용자 폴더를 바꿀 때만 준다
HOME_NAME = "mail-secretary"             # %LOCALAPPDATA% 아래의 사용자 폴더 이름
LOG_FILE = "mailbox-tidy-log.jsonl"
HELD_FILE = "mailbox-tidy-held.json"
SHOWN_FILE = "mailbox-tidy-shown.json"
FIRST_PIECE = 1                          # 이 번호의 조각을 적으면 새 안이다 — 앞서 적은 조각을 걷는다

EXIT_OK, EXIT_FAILED = 0, 1                 # 틀린 인자는 argparse 가 2 로 나간다

MOVE, TRASH, RESTORE = "move", "trash", "restore"
FOLDER_CREATE, FOLDER_DELETE = "folder-create", "folder-delete"
RULE_ADD, RULE_EDIT, RULE_DELETE = "rule-add", "rule-edit", "rule-delete"
KINDS = (MOVE, TRASH, RESTORE, FOLDER_CREATE, FOLDER_DELETE, RULE_ADD, RULE_EDIT, RULE_DELETE)
MAIL_KINDS = (MOVE, TRASH, RESTORE)
DONE, UNKNOWN = "done", "unknown"

# 자리 — 메일이 선 곳
INBOX, SENT, DRAFTS, FOLDER = "inbox", "sent", "drafts", "folder"
# 회사 메일 스킬의 미리 보기 · 실행이 내는 꼴(그 스킬 `scripts/mail.py` 의 `cmd_preview_*` · `cmd_apply_*` 가 찍는 줄)
PLACE_WORDS = {"받은편지함": INBOX, "보낸편지함": SENT, "임시보관함": DRAFTS}
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
ITEM = re.compile(r"^  (?:읽음|안읽음) · (.+)$")          # 메일 한 줄 — 읽음 · 제목 · 보낸 분 · 자리
KEY_LINE = re.compile(r"^확인 열쇠: [0-9a-f]+$")
RULE_NOW, RULE_THEN = "  지금 ", "  바꿀 "
UNID = re.compile(r"^[0-9A-F]{32}$")
TAIL_UNID = re.compile(r" · ([0-9A-F]{32})$")
SUCCESS = {MOVE: "옮겼다: ", TRASH: "휴지통으로 보냈다: ", RESTORE: "되살렸다: ", FOLDER_CREATE: "만들었다: ",
           FOLDER_DELETE: "지웠다: ", RULE_ADD: "규칙을 넣었다: ", RULE_EDIT: "규칙을 고쳤다: ", RULE_DELETE: "규칙을 지웠다"}
# 「됐다」 줄이 대는 것 — 메일 수와 받을 자리(`cmd_apply_move · trash · restore`) · 폴더 경로(`cmd_apply_folder`)
APPLIED = {MOVE: re.compile(r"^옮겼다: (\d+)통 → (.+?) \(다시 봐서"), TRASH: re.compile(r"^휴지통으로 보냈다: (\d+)통 \("),
           RESTORE: re.compile(r"^되살렸다: (\d+)통 \("), FOLDER_CREATE: re.compile(r"^만들었다: (.+?) \(다시 봐서"),
           FOLDER_DELETE: re.compile(r"^지웠다: (.+?) \(다시 봐서")}
STALE = ("확인 열쇠가", "않았다")                        # 열쇠가 안 맞아 아무것도 안 바꿨다는 실행 손의 줄 — 둘 다 든다
ELSEWHERE = re.compile(r"^! (\d+)통은 받은편지함에 없다")
HELD_KEY = "held"                                        # 기록 보기에 덧붙인 잡아 둔 바꿈의 표지 — 파일에는 안 적힌다

KIND_WORDS = {MOVE: "메일 옮기기", TRASH: "휴지통으로 보내기", RESTORE: "휴지통에서 되살리기", FOLDER_CREATE: "폴더 만들기",
              FOLDER_DELETE: "폴더 지우기", RULE_ADD: "규칙 넣기", RULE_EDIT: "규칙 고치기", RULE_DELETE: "규칙 지우기"}
OUTCOME_WORDS = {DONE: "됐다", UNKNOWN: "결과 모름"}

HELD = ("[기록 — 이 바꿈을 잡아 두었다({kind}{n}). 사람이 이대로 하자고 하시면 실행하고 그 글을 journal.py done 에 준다 — 안 하기로 "
        "하시면 실행하지 않고 journal.py drop 으로 놓는다]")
HELD_SUPERSEDED = ("[기록 — 앞서 잡아 둔 바꿈(실행했는지 모른다)을 기록 {id} 에 「결과 모름」으로 옮겼다. 사람이 안 하기로 하신 미리 보기는 "
                   "journal.py drop 으로 놓는다]")
DROPPED = "[기록 — 잡아 둔 바꿈을 기록 없이 놓았다({what})]"
NO_HELD_DROP = "[기록 — 잡아 둔 바꿈이 없어 놓을 것이 없다]"
MISMATCH = ("[기록 — 실행의 글이 잡아 둔 바꿈과 달라 적지 않았다({why}). 잡아 둔 바꿈은 그대로 둔다. 다음: 이 실행이 어느 미리 보기의 "
            "것인지 본다 — 잡아 둔 바꿈의 실행이면 그 실행의 글을 다시 주고, 아니면 사람에게 이 실행은 기록이 맞지 않는다고 말씀드린다]")
WHY_APPLIED_FORM = "실행의 「됐다」 줄을 이 파일이 아는 꼴로 못 읽었다"
WHY_APPLIED_COUNT = "실행은 {got}통 · 잡아 둔 것은 {want}통"
WHY_APPLIED_TARGET = "실행의 받을 자리 「{got}」 · 잡아 둔 것 「{want}」"
WHY_APPLIED_FOLDER = "실행의 폴더 「{got}」 · 잡아 둔 것 「{want}」"
NOT_HELD = ("[기록 — 이 바꿈을 잡지 않았다: {why}. 이대로 실행하면 비서가 되돌릴 기록이 안 남는다 — 사람에게 그렇게 말씀드리고, 하자고 "
            "하시면 그때만 실행한다. 다음: 회사 메일 스킬에 준 것과 같은 종류 · 받을 자리 · 메일 번호(같은 차례)로 미리 보기부터 다시 받는다]")
NO_HELD = "[기록 — 잡아 둔 바꿈이 없어 적지 않았다. 다음: 다음 바꿈은 미리 보기를 journal.py hold 로 받는다 — 이번 바꿈은 사람에게 기록이 안 남았다고 말씀드린다]"
STALE_DONE = "[기록 — 실행 손이 확인 열쇠가 안 맞아 바꾸지 않았다고 했다. 기록하지 않고 잡아 둔 것을 놓았다 — 다음: 미리 보기부터 다시]"
WROTE = "[기록 {id} 에 적었다 — {what} · {outcome}. 되돌리려면 journal.py undo {id}]"
WROTE_UNKNOWN_HINT = " — 실행 손의 「됐다」 줄이 없었다. 메일함에서 지금 자리를 본 뒤 사람에게 말씀드린다"

WHY_HEAD = "미리 보기에 「{kind}」의 머리 줄이 없다"
WHY_KEY = "미리 보기에 확인 열쇠 줄이 없다"
WHY_COUNT = "미리 보기의 메일 {lines}줄 · 머리의 {head}통 · 받은 메일 번호 {unids}개가 같지 않다"
WHY_PLACE = "{n}번째 메일 줄에서 자리(받은편지함 · 보낸편지함 · 임시보관함 · 폴더)를 못 읽었다"
WHY_ORDER = "{n}번째 메일 줄 끝의 메일 번호가 받은 {n}번째 번호와 다르다"
WHY_UNID = "메일 번호가 아니다(32자리): {bad}"
WHY_TARGET = "받을 자리가 미리 보기(「{head}」)와 받은 것(「{given}」)이 다르다"
WHY_TARGET_MISSING = "옮기기는 받을 자리를 준다(--to 폴더 경로 · --inbox)"
WHY_NO_UNIDS = "메일 번호를 받지 못했다"
WHY_RULE_LINES = "규칙의 지금 · 바꿀 두 줄을 못 읽었다"
WHY_FOR_MAILS = "메일 번호와 받을 자리는 메일을 건드리는 바꿈(move · trash · restore)에만 준다"

# 보여 드린 안 — 한 번 확인받는 안의 조각과, 실행 직전에 다시 받은 미리 보기를 그 조각에 대기
SHOWN_ROW = "[조각 {n}] {what}"
SHOWN = ("[기록 — 안의 {n}번 조각으로 적었다{reset}. 조각을 다 보인 뒤 안 전체를 한 번 여쭙는다 — 하자고 하시면 조각마다 새 미리 보기를 "
         "journal.py hold … --shown {n} 에 준다]")
SHOWN_RESET = " · 1번 조각이라 앞서 적어 둔 안(조각 {count}개)은 걷었다"
NOT_SHOWN = ("[기록 — 이 조각을 적지 않았다: {why}. 다음: 회사 메일 스킬에 준 것과 같은 종류 · 받을 자리 · 메일 번호(같은 차례)로 미리 "
             "보기부터 다시 받는다]")
HELD_SHOWN = ("[기록 — 보여 드린 {piece}번 조각과 같아 이 바꿈을 잡아 두었다({kind}{n}). 확인받은 안의 그 조각이니 실행하고 그 글을 "
              "journal.py done 에 준다]")
SHOWN_DIFF = "[기록 — 보여 드린 {n}번 조각과 다른 점:"
SHOWN_DIFF_TAIL = ("  그래서 잡지 않았다 — 실행하지 않는다. 다음: 사용자께 위 다른 점과 이 미리 보기를 보이고 여쭙는다. 이대로 하자고 하시면 "
                   "이 미리 보기를 --shown 없이 hold 로 잡는다]")
SHOWN_NONE = ("[기록 — {n}번 조각을 보인 기록이 없어 잡지 않았다. 다음: 이 미리 보기를 사용자께 보이고 확인받은 뒤 --shown 없이 hold 로 "
              "잡는다]")
DIFF_KIND = "  - 종류: 보인 것 {was} · 지금 {now}"
DIFF_TARGET = "  - 받을 자리: 보인 것 {was} · 지금 {now}"
DIFF_ADDED = "  - 보인 조각에 없던 메일 {count}통: {unids}"
DIFF_GONE = "  - 보인 조각에 있었는데 이 미리 보기에 없는 메일 {count}통: {unids}"
DIFF_PLACE = "  - 그 사이 자리가 바뀐 메일 {count}통: {moves}"
DIFF_PATH = "  - 폴더: 보인 것 「{was}」 · 지금 「{now}」"
DIFF_RULE = "  - 규칙: 보인 것 {was} · 지금 {now}"

LOG_EMPTY = "바꾼 것의 기록이 없다"
LOG_BAD = "[기록 — 기록 파일의 {n}번째 줄을 못 읽어 건너뛰었다]"
LOG_ROW = "[기록 {id}] {when} · {what} · {outcome}{chain}"
LOG_HELD = "결과 모름(잡아 둔 채 — 실행의 글이 안 왔다. 실행했는지는 미리 보기가 보인다)"
WHEN_UNKNOWN = "때 모름"                                  # 잡은 때를 적기 전의 잡아 둔 바꿈
# 되돌림의 사슬 — 처음 바꿈부터, 그것을 되돌린 기록 · 그 되돌림을 되돌린(다시 한) 기록 차례로. 같은 단의 여럿은 「·」로 잇는다
LOG_CHAIN = " · 되돌림 사슬 {chain}"
LINK_UNDO, LINK_REDO = "되돌림", "다시 함"
LINK_UNKNOWN, LINK_HELD = " · 결과 모름", " · 잡아 둔 채"
NO_ENTRY = "[기록 — 그런 기록 번호가 없다: {id}. 다음: journal.py log 로 번호를 본다]"
UNDONE_BY = ("이 기록을 되돌린 기록이 이미 있다({ids}) — 되돌림은 여러 바꿈일 수 있어 차례를 다 낸다. 남은 차례만 밟는다 — 미리 보기가 "
             "이미 제자리인 메일을 보인다")
UNDONE_MAYBE = "이 기록을 되돌리려다 결과를 모르는 기록이 있다({ids}) — 되돌렸는지 모른다. 미리 보기가 지금 자리를 보인다"
UNDONE_HELD = ("이 기록을 되돌리려고 잡아 둔 바꿈이 있다(기록 {ids} · 잡아 둔 채) — 실행했으면 그 실행의 글을 journal.py done 에 주고, "
               "안 하기로 하셨으면 journal.py drop 으로 놓는다")
UNDO_OF_HELD = ("이 바꿈은 잡아 둔 채다 — 실행했는지 모른다. 아래 차례의 미리 보기를 잡으면 이 바꿈이 기록 {id} 에 「결과 모름」으로 "
                "적힌다. 실행하지 않은 미리 보기였으면 되돌리지 말고 journal.py drop 으로 놓는다")

# 바꾼 메일 보기 — 기록마다 원래 자리 → 간 자리의 메일 번호 묶음과, 그 메일을 뒤에 다시 바꾼 기록
MAILS_HEAD = "[기록 파일 {path} — 바꾼 때의 자리를 적는다. 메일의 지금 자리는 메일함이 든다]"
MAILS_GROUP = "  {src} → {dst} {count}통: {unids}"
MAILS_LATER = "  그 뒤 다시 바뀐 메일 {count}통 — 기록 {id}({what} · {outcome}): {unids}"
MAILS_ELSEWHERE = "  그 가운데 {n}통은 받은편지함에 안 돌아왔다고 실행 손이 댔다 — 웹메일에서 자리를 본다"
TRASH_PLACE = "휴지통"
RESTORED_PLACE = "되살린 자리(받은 메일은 받은편지함)"   # 회사 메일 스킬의 되살리기가 돌려놓는 자리 — 폴더 · 보낸 메일은 그 손도 안 쟀다

UNDO_HEAD = ("되돌리는 차례 — 차례마다 회사 메일 스킬의 미리 보기를 사람에게 보이고 확인받은 뒤 실행한다. 미리 보기는 그 차례의 [ ] 안 "
             "명령으로 잡고, 메일 번호는 그 줄 끝의 것을 같은 차례로 준다:")
UNDO_FOOT = ("미리 보기가 메일의 지금 자리를 보인다 — 이미 제자리인 메일 · 그 사이 사람이 다른 데로 옮긴 메일은 그대로 말씀드리고 옮기지 "
             "않는다. 이 기록의 결과가 「결과 모름」이면 바뀌지 않은 몫이 있을 수 있다 — 미리 보기가 그것을 가린다")
HOLD_STEP = " [journal.py hold {kind}{target} --undoes {id}]"   # 그 차례의 미리 보기를 잡는 이 파일의 명령
STEP_MOVE_BACK = "{n}. {place}(으)로 옮길 메일 {count}통{hold}: {unids}"
STEP_NO_HAND = "{n}. {place}에 있던 메일 {count}통은 되돌리지 못한다 — 회사 메일 스킬에 그 자리로 옮기는 손이 없다(웹메일에서 사람이): {unids}"
STEP_RESTORE = "{n}. 휴지통에서 되살릴 메일 {count}통{hold}: {unids}"
STEP_AFTER_RESTORE = "{n}. 되살린 뒤 {place}(으)로 옮길 메일 {count}통{hold}: {unids}"
STEP_RESTORE_UNKNOWN = "    {place}에 있던 메일 {count}통은 되살아나는 자리를 안 쟀다 — 되살린 뒤 웹메일에서 자리를 본다"
STEP_RETRASH = "{n}. 다시 휴지통으로 보낼 메일 {count}통{hold}: {unids}"
STEP_FOLDER_DROP = "1. 폴더 「{path}」를 지운다{hold} — 비어 있을 때만 지워진다(그 사이 메일이 들었으면 사람에게 말씀드린다)"
STEP_FOLDER_MAKE = "1. 폴더 「{path}」를 다시 만든다{hold}"
STEP_RULE_DROP = "1. 넣은 규칙(열쇠 {unid})을 지운다{hold} — 넣은 규칙: {rule}"
STEP_RULE_DROP_NOKEY = "1. 넣은 규칙의 열쇠를 모른다 — 규칙 목록에서 이 꼴의 규칙을 찾아 지운다{hold}: {rule}"
STEP_RULE_BACK = "1. 규칙(열쇠 {unid})을 앞 판으로 고친다{hold} — 앞 판: {before} (지금 판으로 적힌 것: {after})"
STEP_RULE_BACK_NOKEY = "1. 고친 규칙의 열쇠를 모른다 — 규칙 목록에서 「{after}」 꼴의 규칙을 찾아 앞 판으로 고친다{hold}: {before}"
STEP_RULE_READD = "1. 지운 규칙을 다시 넣는다(새 열쇠가 선다){hold} — 지운 규칙: {before}"
PLACE_NAMES = {INBOX: "받은편지함", SENT: "보낸편지함", DRAFTS: "임시보관함"}


class Refused(Exception):
    """미리 보기의 꼴이 이 파일이 아는 꼴이 아니다 — 잡지 않는다."""


class Mismatch(Exception):
    """실행의 「됐다」 줄이 잡아 둔 바꿈과 다르다 — 적지 않고 잡아 둔 것을 그대로 둔다."""


# ── 자리 · 파일 ───────────────────────────────────────────────────────────────

def home() -> pathlib.Path:
    """사용자 폴더 — `MAIL_SECRETARY_HOME` 이 있으면 그 자리, 없으면 `%LOCALAPPDATA%\\mail-secretary`."""
    override = os.environ.get(HOME_ENV, "").strip()
    if override:
        return pathlib.Path(override)
    local = os.environ.get("LOCALAPPDATA", "").strip()
    return (pathlib.Path(local) if local else pathlib.Path.home() / "AppData" / "Local") / HOME_NAME


def decode(raw: bytes) -> str:
    """받은 바이트 → 글. BOM 이 있으면 그 꼴(UTF-8 · UTF-16 — Windows PowerShell 의 `>` 가 쓰는 꼴), 없으면 UTF-8, 안 되면 cp949.
    같은 몸이 스킬 mailbox-work 의 `work.py` · daily-brief 의 `window.py` 에 있다 — 고치면 셋을 함께 고친다(머리말의 받는 꼴이 같다)."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", errors="replace")


def read_input(path: str | None) -> str:
    """`--in` 의 파일이나 표준 입력 — 바이트로 받아 `decode` 한다."""
    raw = pathlib.Path(path).read_bytes() if path else sys.stdin.buffer.read()
    return decode(raw)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_atomic(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def entries(folder: pathlib.Path) -> tuple[list[dict[str, Any]], list[int]]:
    """기록 전부(옛것부터)와 못 읽은 줄의 번호."""
    path = folder / LOG_FILE
    if not path.exists():
        return [], []
    rows, bad = [], []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):   # 끊긴 줄의 반쪽 글자도 그 줄만 못 읽는다
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get("id"), int):
                raise ValueError
            rows.append(row)
        except ValueError:
            bad.append(n)
    return rows, bad


def append(folder: pathlib.Path, entry: dict[str, Any]) -> int:
    """기록 한 줄을 덧붙이고 그 번호를 낸다 — 있는 줄은 고치지 않는다."""
    rows, _ = entries(folder)
    entry = {"id": max((r["id"] for r in rows), default=0) + 1, **entry}
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / LOG_FILE).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return entry["id"]


def held(folder: pathlib.Path) -> dict[str, Any] | None:
    path = folder / HELD_FILE
    if not path.exists():
        return None
    try:
        got = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return got if isinstance(got, dict) else None


def next_id(rows: Sequence[dict[str, Any]]) -> int:
    """다음 기록 번호 — `append` 가 주는 번호와 같다."""
    return max((r["id"] for r in rows), default=0) + 1


def with_held(folder: pathlib.Path, rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """기록에 잡아 둔 바꿈을 다음 번호의 「결과 모름」으로 덧붙인 것 — 보이기만 한다(맺을 때도 그 번호로 적힌다)."""
    hold = held(folder)
    if hold is None:
        return list(rows)
    return [*rows, {**hold, "id": next_id(rows), "outcome": UNKNOWN, HELD_KEY: True}]


# ── 미리 보기 읽기 ────────────────────────────────────────────────────────────

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


def read_preview(kind: str, text: str, unids: Sequence[str], to: str | None) -> dict[str, Any]:
    """미리 보기 → 잡아 둘 바꿈. 꼴이 다르면 `Refused`. 머리 앞의 줄(표준 오류를 함께 흘린 경고)은 건너뛴다."""
    lines = [x for x in text.splitlines() if x.strip()]
    at = next((i for i, x in enumerate(lines) if HEADS[kind].match(x)), None)
    if at is None:
        raise Refused(WHY_HEAD.format(kind=kind))
    lines = lines[at:]
    head = HEADS[kind].match(lines[0])
    if not any(KEY_LINE.match(x) for x in lines):
        raise Refused(WHY_KEY)
    hold: dict[str, Any] = {"kind": kind}
    if kind in MAIL_KINDS:
        items = _items(lines)
        if not unids:
            raise Refused(WHY_NO_UNIDS)
        if not (len(items) == int(head.group(1)) == len(unids)):
            raise Refused(WHY_COUNT.format(lines=len(items), head=head.group(1), unids=len(unids)))
        if kind == MOVE:
            shown = head.group(2)
            if to is None:
                raise Refused(WHY_TARGET_MISSING)
            if shown != (to or PLACE_NAMES[INBOX]):
                raise Refused(WHY_TARGET.format(head=shown, given=to or PLACE_NAMES[INBOX]))
            hold["to"] = to
        mails = []
        for n, (line, unid) in enumerate(zip(items, unids), 1):
            rest = line[2:]
            tail = TAIL_UNID.search(rest)
            if tail:
                if tail.group(1) != unid:
                    raise Refused(WHY_ORDER.format(n=n))
                rest = rest[:tail.start()]
            if not ITEM.match(line):
                raise Refused(WHY_PLACE.format(n=n))
            if kind == RESTORE:
                mails.append({"unid": unid})
                continue
            where = place_of(rest)
            if where is None:
                raise Refused(WHY_PLACE.format(n=n))
            mails.append({"unid": unid, "place": where[0], "folder": where[1]})
        hold["mails"] = mails
    elif kind in (FOLDER_CREATE, FOLDER_DELETE):
        hold["path"] = head.group(1)
    elif kind == RULE_EDIT:
        now = next((x[len(RULE_NOW):] for x in lines if x.startswith(RULE_NOW)), None)
        then = next((x[len(RULE_THEN):] for x in lines if x.startswith(RULE_THEN)), None)
        if not now or not then:
            raise Refused(WHY_RULE_LINES)
        hold["rule"] = {"before": now, "after": then}
    elif kind == RULE_ADD:
        hold["rule"] = {"after": head.group(1)}
    else:
        hold["rule"] = {"before": head.group(1)}
    return hold


def preview_body(kind: str, text: str) -> list[str]:
    """미리 보기에서 사람에게 보일 몸 — 머리 줄 다음부터 확인 열쇠 줄 앞까지. 꼴은 `read_preview` 가 먼저 댔다고 본다."""
    lines = [x for x in text.splitlines() if x.strip()]
    at = next(i for i, x in enumerate(lines) if HEADS[kind].match(x))
    key = next(i for i in range(at, len(lines)) if KEY_LINE.match(lines[i]))
    return lines[at + 1:key]


def read_shown(kind: str, text: str, unids: Sequence[str], to: str | None) -> tuple[dict[str, Any], list[str]]:
    """`show` 가 받는 미리 보기 → (적을 조각, 보일 몸). 꼴이 다르면 `Refused`. 옮기기 조각은 휴지통 미리 보기도 받는다(받을 자리는 `to`)."""
    lines = text.splitlines()
    if kind == MOVE and not any(HEADS[MOVE].match(x) for x in lines) and any(HEADS[TRASH].match(x) for x in lines):
        if to is None:
            raise Refused(WHY_TARGET_MISSING)
        return {**read_preview(TRASH, text, unids, None), "kind": MOVE, "to": to}, preview_body(TRASH, text)
    return read_preview(kind, text, unids, to), preview_body(kind, text)


def _target_word(e: dict[str, Any]) -> str:
    """옮기기의 받을 자리를 사람 말로 — 빈 것은 받은편지함."""
    return _place_word(FOLDER if e.get("to") else INBOX, e.get("to") or "")


def _rule_word(e: dict[str, Any]) -> str:
    rule = e.get("rule") or {}
    return " → ".join(x for x in (rule.get("before"), rule.get("after")) if x)


def differences(shown: dict[str, Any], fresh: dict[str, Any]) -> list[str]:
    """보여 드린 조각과 다시 받은 미리 보기가 다른 점 — 손의 확인 열쇠가 대는 것만 견주고 읽음은 안 댄다. 같으면 빈 목록."""
    kind = fresh["kind"]
    if shown.get("kind") != kind:
        return [DIFF_KIND.format(was=KIND_WORDS.get(shown.get("kind", ""), shown.get("kind")), now=KIND_WORDS[kind])]
    out: list[str] = []
    if kind == MOVE and (shown.get("to") or "") != (fresh.get("to") or ""):
        out.append(DIFF_TARGET.format(was=_target_word(shown), now=_target_word(fresh)))
    if kind in MAIL_KINDS:
        def places(e: dict[str, Any]) -> dict[str, tuple[str, str]]:
            return {m["unid"]: (m.get("place", ""), m.get("folder", "")) for m in e.get("mails") or []}
        was, now = places(shown), places(fresh)
        added = [u for u in now if u not in was]
        gone = [u for u in was if u not in now]
        moved = [u for u in now if u in was and now[u] != was[u]]
        if added:
            out.append(DIFF_ADDED.format(count=len(added), unids=" ".join(added)))
        if gone:
            out.append(DIFF_GONE.format(count=len(gone), unids=" ".join(gone)))
        if moved:
            out.append(DIFF_PLACE.format(count=len(moved), moves=" · ".join(
                f"{u}({_place_word(*was[u])} → {_place_word(*now[u])})" for u in moved)))
    elif kind in (FOLDER_CREATE, FOLDER_DELETE):
        if shown.get("path") != fresh.get("path"):
            out.append(DIFF_PATH.format(was=shown.get("path"), now=fresh.get("path")))
    elif (shown.get("rule") or {}) != (fresh.get("rule") or {}):
        out.append(DIFF_RULE.format(was=_rule_word(shown), now=_rule_word(fresh)))
    return out


def check_applied(hold: dict[str, Any], ok: str) -> None:
    """「됐다」 줄이 대는 메일 수 · 받을 자리 · 폴더 경로가 잡아 둔 바꿈과 같은가 — 다르거나 못 읽으면 `Mismatch`."""
    kind = hold["kind"]
    form = APPLIED.get(kind)
    if form is None:
        return
    got = form.match(ok)
    if got is None:
        raise Mismatch(WHY_APPLIED_FORM)
    if kind in MAIL_KINDS:
        count, want = int(got.group(1)), len(hold.get("mails") or [])
        if count != want:
            raise Mismatch(WHY_APPLIED_COUNT.format(got=count, want=want))
        if kind == MOVE and got.group(2) != (hold.get("to") or PLACE_NAMES[INBOX]):
            raise Mismatch(WHY_APPLIED_TARGET.format(got=got.group(2), want=hold.get("to") or PLACE_NAMES[INBOX]))
    elif got.group(1) != hold.get("path"):
        raise Mismatch(WHY_APPLIED_FOLDER.format(got=got.group(1), want=hold.get("path")))


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
        tail = TAIL_UNID.search(ok)
        if tail:
            more["rule_unid"] = tail.group(1)
    if kind == RESTORE:
        away = next((ELSEWHERE.match(x) for x in lines if ELSEWHERE.match(x)), None)
        if away:
            more["elsewhere"] = int(away.group(1))
    return DONE, more


# ── 말 ───────────────────────────────────────────────────────────────────────

def _place_word(place: str, folder: str) -> str:
    """자리를 사람 말로."""
    if place != FOLDER:
        return PLACE_NAMES.get(place, place)
    return f"폴더 「{folder}」"


def describe(e: dict[str, Any]) -> str:
    """기록 한 줄이 한 일 — 메일 번호 없이."""
    kind = e.get("kind", "")
    word = KIND_WORDS.get(kind, kind)
    if kind in MAIL_KINDS:
        mails = e.get("mails") or []
        counts: dict[str, int] = {}
        for m in mails:
            key = _place_word(m.get("place", ""), m.get("folder", "")) if kind != RESTORE else "휴지통"
            counts[key] = counts.get(key, 0) + 1
        origin = " · ".join(f"{k} {v}" for k, v in counts.items())
        target = f" → {_target_word(e)}" if kind == MOVE else ""
        return f"{word} {len(mails)}통({origin}){target}"
    if kind in (FOLDER_CREATE, FOLDER_DELETE):
        return f"{word} 「{e.get('path', '')}」"
    rule = e.get("rule") or {}
    return f"{word} — {rule.get('after') or rule.get('before') or ''}"


def links(rows: Sequence[dict[str, Any]], entry_id: int) -> list[dict[str, Any]]:
    """그 기록을 되돌리려 한 기록들 — 되돌림 하나가 바꿈 여럿일 수 있다. 됐다고 맺은 것만 「되돌렸다」로 센다(부르는 쪽이 결과로 가른다)."""
    return [r for r in rows if r.get("undoes") == entry_id]


def _link_word(depth: int, r: dict[str, Any]) -> str:
    word = LINK_UNDO if depth % 2 else LINK_REDO
    if r.get(HELD_KEY):
        return word + LINK_HELD
    return word if r.get("outcome") == DONE else word + LINK_UNKNOWN


def chain(rows: Sequence[dict[str, Any]], entry_id: int) -> str:
    """그 기록이 든 되돌림의 사슬 — 「5 → 8(되돌림) → 9(다시 함)」. 사슬이 없으면 빈 글."""
    by_id = {r["id"]: r for r in rows}
    root, seen = entry_id, {entry_id}
    while (up := by_id.get(root, {}).get("undoes")) in by_id and up not in seen:
        root = up
        seen.add(up)
    tiers, frontier, seen = [], [root], {root}
    while nxt := [r["id"] for r in rows if r.get("undoes") in frontier and r["id"] not in seen]:
        seen.update(nxt)
        tiers.append(nxt)
        frontier = nxt
    if not tiers:
        return ""
    parts = [str(root)] + [" · ".join(f"{i}({_link_word(depth, by_id[i])})" for i in ids) for depth, ids in enumerate(tiers, 1)]
    return LOG_CHAIN.format(chain=" → ".join(parts))


def undo_steps(e: dict[str, Any]) -> list[str]:
    """기록 하나를 되돌리는 차례 — 차례마다 그 미리 보기를 잡을 이 파일의 명령을 댄다."""
    kind = e.get("kind")
    mails = e.get("mails") or []
    entry_id = e.get("id")

    def hold(step_kind: str, place: str = "", folder: str = "") -> str:
        target = "" if step_kind != MOVE else (f' --to "{folder}"' if place == FOLDER else " --inbox")
        return HOLD_STEP.format(kind=step_kind, target=target, id=entry_id)

    def groups(pick) -> list[tuple[str, str, list[str]]]:
        out: dict[tuple[str, str], list[str]] = {}
        for m in mails:
            if pick(m):
                out.setdefault((m.get("place", ""), m.get("folder", "")), []).append(m["unid"])
        return [(p, f, u) for (p, f), u in out.items()]

    def back(n: int, form: str, place: str, folder: str, unids: list[str]) -> str:
        return form.format(n=n, place=_place_word(place, folder), count=len(unids), unids=" ".join(unids),
                           hold=hold(MOVE, place, folder))

    every = " ".join(m["unid"] for m in mails)
    steps: list[str] = []
    if kind == MOVE:
        n = 0
        for place, folder, unids in groups(lambda m: True):
            n += 1
            steps.append(back(n, STEP_NO_HAND if place in (SENT, DRAFTS) else STEP_MOVE_BACK, place, folder, unids))
    elif kind == TRASH:
        steps.append(STEP_RESTORE.format(n=1, count=len(mails), unids=every, hold=hold(RESTORE)))
        n = 1
        for place, folder, unids in groups(lambda m: m.get("place") == FOLDER):
            n += 1
            steps.append(back(n, STEP_AFTER_RESTORE, place, folder, unids))
        for place, folder, unids in groups(lambda m: m.get("place") == SENT):
            steps.append(STEP_RESTORE_UNKNOWN.format(place=_place_word(place, folder), count=len(unids)))
    elif kind == RESTORE:
        steps.append(STEP_RETRASH.format(n=1, count=len(mails), unids=every, hold=hold(TRASH)))
    elif kind in (FOLDER_CREATE, FOLDER_DELETE):
        path = e.get("path", "")
        if kind == FOLDER_CREATE:
            steps.append(STEP_FOLDER_DROP.format(path=path, hold=hold(FOLDER_DELETE)))
        else:
            steps.append(STEP_FOLDER_MAKE.format(path=path, hold=hold(FOLDER_CREATE)))
    else:
        rule = e.get("rule") or {}
        key = rule.get("unid") or ""
        if kind == RULE_ADD:
            steps.append((STEP_RULE_DROP if key else STEP_RULE_DROP_NOKEY).format(unid=key, rule=rule.get("after", ""),
                                                                                  hold=hold(RULE_DELETE)))
        elif kind == RULE_EDIT:
            steps.append((STEP_RULE_BACK if key else STEP_RULE_BACK_NOKEY).format(
                unid=key, before=rule.get("before", ""), after=rule.get("after", ""), hold=hold(RULE_EDIT)))
        else:
            steps.append(STEP_RULE_READD.format(before=rule.get("before", ""), hold=hold(RULE_ADD)))
    return steps


# ── 명령 ─────────────────────────────────────────────────────────────────────

def _settle_old(folder: pathlib.Path) -> int | None:
    """잡아 둔 바꿈이 남았으면 「결과 모름」 기록으로 옮기고 그 번호를 낸다."""
    old = held(folder)
    if old is None:
        return None
    entry_id = append(folder, {**old, "outcome": UNKNOWN, "at": _now()})
    (folder / HELD_FILE).unlink(missing_ok=True)
    return entry_id


def given(args) -> tuple[list[str], str | None]:
    """`show` · `hold` 가 받은 (메일 번호, 받을 자리 — 받은편지함이면 "" · 안 줬으면 None). 틀리면 `Refused`."""
    unids = [u.strip().upper() for u in args.unids]
    bad = [u for u in unids if not UNID.match(u)]
    if bad:
        raise Refused(WHY_UNID.format(bad=", ".join(bad[:3])))
    if args.kind not in MAIL_KINDS and (unids or args.to is not None or args.inbox):
        raise Refused(WHY_FOR_MAILS)
    return unids, "" if args.inbox else args.to


def shown_pieces(folder: pathlib.Path) -> dict[str, dict[str, Any]]:
    """보여 드린 안의 조각 — 조각 번호(글자) → 조각. 없거나 못 읽으면 빈 것."""
    try:
        got = json.loads((folder / SHOWN_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    pieces = got.get("pieces") if isinstance(got, dict) else None
    return pieces if isinstance(pieces, dict) else {}


def cmd_show(args, folder: pathlib.Path) -> int:
    text = read_input(args.infile)
    try:
        unids, to = given(args)
        piece, body = read_shown(args.kind, text, unids, to)
    except Refused as exc:
        for line in text.splitlines():       # 적지 못한 조각은 손의 글을 그대로 보인다 — 파이프가 받아 갔다
            print(line)
        print(NOT_SHOWN.format(why=exc))
        return EXIT_FAILED
    pieces = shown_pieces(folder)
    reset = ""
    if args.piece == FIRST_PIECE:
        reset = SHOWN_RESET.format(count=len(pieces)) if pieces else ""
        pieces = {}
    pieces[str(args.piece)] = {**piece, "at": _now()}
    _write_atomic(folder / SHOWN_FILE, json.dumps({"pieces": pieces}, ensure_ascii=False))
    for line in [SHOWN_ROW.format(n=args.piece, what=describe(piece)), *body, SHOWN.format(n=args.piece, reset=reset)]:
        print(line)
    return EXIT_OK


def cmd_hold(args, folder: pathlib.Path) -> int:
    text = read_input(args.infile)
    for line in text.splitlines():           # 미리 보기는 파이프가 받아 갔다 — 사람에게 보일 글을 여기서 다시 낸다
        print(line)
    try:
        unids, to = given(args)
        hold = read_preview(args.kind, text, unids, to)
    except Refused as exc:
        print(NOT_HELD.format(why=exc))
        return EXIT_FAILED
    if args.shown is not None:
        shown = shown_pieces(folder).get(str(args.shown))
        if shown is None:
            print(SHOWN_NONE.format(n=args.shown))
            return EXIT_FAILED
        diff = differences(shown, hold)
        if diff:
            for line in [SHOWN_DIFF.format(n=args.shown), *diff, SHOWN_DIFF_TAIL]:
                print(line)
            return EXIT_FAILED
    superseded = _settle_old(folder)
    if superseded is not None:
        print(HELD_SUPERSEDED.format(id=superseded))
    hold["undoes"] = args.undoes
    hold["at"] = _now()
    _write_atomic(folder / HELD_FILE, json.dumps(hold, ensure_ascii=False))
    n = f" · 메일 {len(hold['mails'])}통" if "mails" in hold else ""
    said = HELD if args.shown is None else HELD_SHOWN
    print(said.format(kind=KIND_WORDS[args.kind], n=n, piece=args.shown))
    return EXIT_OK


def cmd_done(args, folder: pathlib.Path) -> int:
    hold = held(folder)
    text = read_input(args.infile)
    for line in text.splitlines():           # 실행의 글도 파이프가 받아 갔다 — 사람에게 알릴 결과를 여기서 다시 낸다
        print(line)
    if hold is None:
        print(NO_HELD)
        return EXIT_FAILED
    try:
        outcome, more = read_applied(hold, text)
    except Mismatch as exc:
        print(MISMATCH.format(why=exc))
        return EXIT_FAILED
    if outcome is None:
        (folder / HELD_FILE).unlink(missing_ok=True)
        print(STALE_DONE)
        return EXIT_FAILED
    entry = {**hold, "outcome": outcome, "at": _now()}
    if more.get("rule_unid"):
        entry["rule"] = {**(entry.get("rule") or {}), "unid": more["rule_unid"]}
    if "elsewhere" in more:
        entry["elsewhere"] = more["elsewhere"]
    entry_id = append(folder, entry)
    (folder / HELD_FILE).unlink(missing_ok=True)
    said = WROTE.format(id=entry_id, what=describe(entry), outcome=OUTCOME_WORDS[outcome])
    print(said + (WROTE_UNKNOWN_HINT if outcome == UNKNOWN else ""))
    return EXIT_OK


def cmd_drop(args, folder: pathlib.Path) -> int:
    hold = held(folder)
    if hold is None:
        print(NO_HELD_DROP)
        return EXIT_FAILED
    (folder / HELD_FILE).unlink(missing_ok=True)
    print(DROPPED.format(what=describe(hold)))
    return EXIT_OK


def row_line(rows: Sequence[dict[str, Any]], e: dict[str, Any], *, with_chain: bool = True) -> str:
    """기록 한 줄 — 번호 · 때 · 한 일 · 결과(잡아 둔 채면 그렇게) · 되돌림의 사슬."""
    outcome = LOG_HELD if e.get(HELD_KEY) else OUTCOME_WORDS.get(e.get("outcome"), e.get("outcome"))
    when = str(e.get("at") or "")[:16].replace("T", " ") or WHEN_UNKNOWN
    return LOG_ROW.format(id=e["id"], when=when, what=describe(e), outcome=outcome, chain=chain(rows, e["id"]) if with_chain else "")


def cmd_log(args, folder: pathlib.Path) -> int:
    rows, bad = entries(folder)
    rows = with_held(folder, rows)
    for n in bad:
        print(LOG_BAD.format(n=n))
    if not rows:
        print(LOG_EMPTY)
        return EXIT_OK
    for e in reversed(rows[-args.most:] if args.most else rows):
        print(row_line(rows, e))
    return EXIT_OK


def mail_lines(rows: Sequence[dict[str, Any]], e: dict[str, Any]) -> list[str]:
    """기록 하나가 바꾼 메일 줄 — 원래 자리 → 간 자리마다 · 뒤의 기록이 다시 바꾼 메일은 그 기록마다 묶는다. 폴더 · 규칙 바꿈은 빈 목록."""
    kind = e.get("kind")
    mails = e.get("mails") or []
    if kind not in MAIL_KINDS or not mails:
        return []
    dst = {MOVE: _target_word(e), TRASH: TRASH_PLACE, RESTORE: RESTORED_PLACE}[kind]
    groups: dict[str, list[str]] = {}
    for m in mails:
        src = TRASH_PLACE if kind == RESTORE else _place_word(m.get("place", ""), m.get("folder", ""))
        groups.setdefault(src, []).append(m["unid"])
    out = [MAILS_GROUP.format(src=src, dst=dst, count=len(unids), unids=" ".join(unids)) for src, unids in groups.items()]
    if e.get("elsewhere"):
        out.append(MAILS_ELSEWHERE.format(n=e["elsewhere"]))
    mine = {m["unid"] for m in mails}
    for later in rows:
        if later["id"] <= e["id"]:
            continue
        touched = [m["unid"] for m in later.get("mails") or [] if m.get("unid") in mine]
        if touched:
            outcome = LOG_HELD if later.get(HELD_KEY) else OUTCOME_WORDS.get(later.get("outcome"), later.get("outcome"))
            out.append(MAILS_LATER.format(id=later["id"], what=KIND_WORDS.get(later.get("kind", ""), ""), outcome=outcome,
                                          count=len(touched), unids=" ".join(touched)))
    return out


def cmd_mails(args, folder: pathlib.Path) -> int:
    rows, bad = entries(folder)
    rows = with_held(folder, rows)
    out = [MAILS_HEAD.format(path=folder / LOG_FILE), *(LOG_BAD.format(n=n) for n in bad)]
    if not rows:
        out.append(LOG_EMPTY)
    by_id = {r["id"]: r for r in rows}
    missing = [i for i in args.ids if i not in by_id]
    for e in [by_id[i] for i in sorted(set(args.ids)) if i in by_id] if args.ids else rows:
        out += [row_line(rows, e), *mail_lines(rows, e)]
    out += [NO_ENTRY.format(id=i) for i in missing]
    for line in out:
        print(line)
    return EXIT_FAILED if missing else EXIT_OK


def cmd_undo(args, folder: pathlib.Path) -> int:
    rows, _ = entries(folder)
    rows = with_held(folder, rows)
    e = next((r for r in rows if r["id"] == args.id), None)
    if e is None:
        print(NO_ENTRY.format(id=args.id))
        return EXIT_FAILED
    tried = links(rows, e["id"])
    done = [r["id"] for r in tried if r.get("outcome") == DONE and not r.get(HELD_KEY)]
    maybe = [r["id"] for r in tried if r.get("outcome") != DONE and not r.get(HELD_KEY)]
    pending = [r["id"] for r in tried if r.get(HELD_KEY)]
    note = ([UNDO_OF_HELD.format(id=e["id"])] if e.get(HELD_KEY) else []) \
        + ([UNDONE_BY.format(ids=" · ".join(map(str, done)))] if done else []) \
        + ([UNDONE_MAYBE.format(ids=" · ".join(map(str, maybe)))] if maybe else []) \
        + ([UNDONE_HELD.format(ids=" · ".join(map(str, pending)))] if pending else [])
    for line in [row_line(rows, e, with_chain=False), *note, UNDO_HEAD, *undo_steps(e), UNDO_FOOT]:
        print(line)
    return EXIT_OK


def piece_number(text: str) -> int:
    n = int(text)
    if n < FIRST_PIECE:
        raise argparse.ArgumentTypeError(f"조각 번호는 {FIRST_PIECE} 부터다: {text}")
    return n


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="메일함에서 바꾼 것을 적어 두고 되돌릴 차례를 낸다 — 회사 메일 스킬의 글을 받는다")
    sub = ap.add_subparsers(dest="command", required=True)
    s = sub.add_parser("show", help="안 전체를 확인받기 전에 조각 하나의 미리 보기를 조각 n 으로 적고 보일 꼴로 낸다")
    h = sub.add_parser("hold", help="미리 보기를 읽어 바꿈 하나를 잡아 둔다")
    for q in (s, h):
        q.add_argument("kind", choices=KINDS)
        target = q.add_mutually_exclusive_group()
        target.add_argument("--to", help="move 의 받을 폴더 경로 — 회사 메일 스킬에 준 그대로")
        target.add_argument("--inbox", action="store_true", help="move 의 받을 자리가 받은편지함")
        q.add_argument("--in", dest="infile", help="표준 입력 대신 읽을 파일")
        q.add_argument("unids", nargs="*", help="회사 메일 스킬에 준 메일 번호 — 같은 차례로")
    s.add_argument("--piece", type=piece_number, required=True, help=f"안에서 이 조각의 번호 — {FIRST_PIECE} 이면 새 안을 연다")
    h.add_argument("--shown", type=piece_number, help="확인받은 안의 이 조각과 같을 때만 잡는다")
    h.add_argument("--undoes", type=int, help="이 바꿈이 되돌리는 기록 번호")
    d = sub.add_parser("done", help="실행의 글을 읽어 잡아 둔 바꿈을 기록으로 맺는다")
    d.add_argument("--in", dest="infile", help="표준 입력 대신 읽을 파일")
    sub.add_parser("drop", help="사람이 안 하기로 하신 미리 보기를 기록 없이 놓는다 — 실행하지 않았을 때만(실행했으면 done)")
    lg = sub.add_parser("log", help="바꾼 것의 기록 — 새것부터 · 잡아 둔 채인 바꿈과 되돌림의 사슬도")
    lg.add_argument("--most", type=int, default=20, help="보일 기록의 수(0 이면 다)")
    ml = sub.add_parser("mails", help="바꾼 메일 — 기록마다 메일 번호 · 원래 자리 → 간 자리 · 뒤에 다시 바꾼 기록(읽기만 · 옛것부터)")
    ml.add_argument("ids", nargs="*", type=int, help="볼 기록 번호 — 없으면 다")
    u = sub.add_parser("undo", help="기록 하나를 되돌리는 차례")
    u.add_argument("id", type=int)
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    folder = home()
    return {"show": cmd_show, "hold": cmd_hold, "done": cmd_done, "drop": cmd_drop, "log": cmd_log, "mails": cmd_mails,
            "undo": cmd_undo}[args.command](args, folder)


if __name__ == "__main__":
    sys.exit(main())
