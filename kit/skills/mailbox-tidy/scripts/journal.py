"""메일함에서 바꾼 것을 적어 두고, 되돌릴 차례를 낸다 — 회사 메일 스킬의 미리 보기와 실행이 낸 글을 받는다. 메일함에는 닿지 않는다.

    <미리 보기> | python -X utf8 journal.py show <종류> --piece <n> [--why <무리 · 까닭>] [--to <폴더>]   안의 조각 n 으로 적고 보인다
    python -X utf8 journal.py shown                     적어 둔 안 — show 가 보인 줄을 조각마다 그대로(읽기만)
    python -X utf8 journal.py plans [--most N]          적어 둔 안들 — 아직 안 바꾼 조각의 받을 자리 · 메일 번호 · 까닭(읽기만 · 새것부터)
    <미리 보기> | python -X utf8 journal.py hold <종류> [--shown <n>] [--undoes <기록 번호>]   잡아 두고 실행 줄을 낸다
    <실행>      | python -X utf8 journal.py done
    python -X utf8 journal.py drop                      사람이 안 하기로 하신 미리 보기를 놓는다 — 실행하지 않았을 때만
    python -X utf8 journal.py log [--most N]            바꾼 것의 기록 — 새것부터
    python -X utf8 journal.py mails [<기록 번호> …]     바꾼 메일 — 기록마다 메일 번호 · 원래 자리 → 간 자리(읽기만 · 옛것부터)
    python -X utf8 journal.py undo <기록 번호>          그 바꿈을 되돌리는 차례 — 차례마다 칠 명령 줄
    (`show` · `hold` · `done` 은 `--in <파일>` 로도 받는다)

종류 — move(메일 옮기기) · trash(휴지통으로) · restore(휴지통에서 되살리기) · folder-create · folder-delete · rule-add · rule-edit ·
rule-delete. 메일 번호 · 받을 자리 · 확인 열쇠는 미리 보기에서 읽는다 — 메일 줄 끝의 번호 · 머리의 받을 자리 · 「확인 열쇠:」 줄. 따로
주지 않는다. `--to` 는 옮길 폴더를 같은 안의 앞 조각이 만들어 휴지통 미리 보기를 옮기기 조각으로 적을 때(`show move`)만 준다. 옛 꼴대로
메일 번호 · `--to` · `--inbox` 를 주면 미리 보기와 같은지만 대고, 다르면 잡지 않는다.

명령마다 무엇을 대나는 `references/DESIGN.md` 「명령마다 하는 일」이 든다.

남기는 것 — 사용자 폴더(`home()`)의 `LOG_FILE`(덧붙이기만) · 잡아 둔 바꿈 `HELD_FILE` · 보여 드린 안의 조각 `SHOWN_FILE` · 적어 둔
안들 `PLANS_FILE`(덧붙이기만). 기록 · 잡아 둔 바꿈 · 적어 둔 안들은 메일 번호 · 자리 · 폴더 경로 · 규칙의 판(안들은 조각의 까닭 한 줄도)만
적고 제목 · 보낸 분 · 본문은 안 적는다. 안의 조각은 손의 메일 줄(제목 · 보낸 분)도 든다 — 안을 지은 쪽과 사용자께 보이는 쪽이 달라도 같은
줄이 서게. 다음 안의 1번 조각이 덮는다 — 덮인 안의 메일 번호는 적어 둔 안들에 남는다.

종료 값 — 0 됐다 · 1 못 했다(꼴이 다르다 · 보여 드린 조각과 다르다 · 실행의 글이 잡아 둔 바꿈과 다르다 · 잡아 둔 것이 없다 · 그런
기록이 없다 — 다음 걸음을 끝 줄이 말한다) · 2 인자가 틀렸다.

⚠ 실행의 「됐다」 줄은 끝의 확인 열쇠로 잡아 둔 미리 보기에 잇는다. 열쇠는 미리 보기가 본 판의 지문이라, 같은 판에서 다시 한 같은
바꿈(지운 폴더를 다시 만들기 · 되돌린 메일을 다시 옮기기)의 실행 글은 앞의 것과 열쇠가 같아 가르지 못한다. 열쇠가 없는 「됐다」 줄
(갱신 전의 손)은 메일 수 · 받을 자리 · 폴더 경로로 대고, 규칙은 안 댄다.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shlex
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
PLANS_FILE = "mailbox-tidy-plans.jsonl"
FIRST_PIECE = 1                          # 이 번호의 조각을 적으면 새 안이다 — 앞서 적은 조각을 걷는다
PLANS_MOST = 5                           # plans 가 기본으로 보일 안의 수 — 안 바꾼 조각이 남은 안만 센다

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
ITEM = re.compile(r"^  (?:읽음|안읽음) · (.+)$")          # 메일 한 줄 — 읽음 · 제목 · 보낸 분 · 자리 · 메일 번호
KEY_LINE = re.compile(r"^확인 열쇠: ([0-9a-f]+)$")
APPLIED_KEY = re.compile(r" · 열쇠 ([0-9a-f]+)$")          # 「됐다」 줄 끝 — 실행이 맞춘 확인 열쇠(넣거나 고친 규칙은 규칙 열쇠 뒤에 선다)
FOLDER_SEP = "\\"                                        # 폴더 경로의 부모 · 자식 가름(그 스킬 `inbox.py` 의 FOLDER_SEPARATOR)
RULE_NOW, RULE_THEN = "  지금 ", "  바꿀 "
UNID = re.compile(r"^[0-9A-F]{32}$")
TAIL_UNID = re.compile(r" · ([0-9A-F]{32})$")
SUCCESS = {MOVE: "옮겼다: ", TRASH: "휴지통으로 보냈다: ", RESTORE: "되살렸다: ", FOLDER_CREATE: "만들었다: ",
           FOLDER_DELETE: "지웠다: ", RULE_ADD: "규칙을 넣었다: ", RULE_EDIT: "규칙을 고쳤다: ", RULE_DELETE: "규칙을 지웠다"}
# 열쇠가 없는 「됐다」 줄이 대는 것 — 메일 수와 받을 자리(`cmd_apply_move · trash · restore`) · 폴더 경로(`cmd_apply_folder`)
APPLIED = {MOVE: re.compile(r"^옮겼다: (\d+)통 → (.+?) \(다시 봐서"), TRASH: re.compile(r"^휴지통으로 보냈다: (\d+)통 \("),
           RESTORE: re.compile(r"^되살렸다: (\d+)통 \("), FOLDER_CREATE: re.compile(r"^만들었다: (.+?) \(다시 봐서"),
           FOLDER_DELETE: re.compile(r"^지웠다: (.+?) \(다시 봐서")}
STALE = ("확인 열쇠가", "않았다")                        # 열쇠가 안 맞아 아무것도 안 바꿨다는 실행 손의 줄 — 둘 다 든다
ELSEWHERE = re.compile(r"^! (\d+)통은 받은편지함에 없다")
HELD_KEY = "held"                                        # 기록 보기에 덧붙인 잡아 둔 바꿈의 표지 — 파일에는 안 적힌다

# 다음 걸음의 명령 줄 — 회사 메일 스킬의 손과 이 파일. 스킬은 한 부모 폴더에 나란히 깔린다(Git Bash 에서 그대로 칠 꼴).
# 곁에 손이 없으면 자리 대신 표지를 낸다 — 모델이 그 스킬의 자리로 채운다
SELF = pathlib.Path(__file__).resolve()
SIBLING_HAND = SELF.parents[2] / "company-mail" / "scripts" / "mail.py"
HAND = SIBLING_HAND if SIBLING_HAND.is_file() else pathlib.PurePosixPath("<회사 메일 스킬>/scripts/mail.py")
RUN = ("python", "-X", "utf8", "-I")
# 종류 → 손의 preview-<말> · apply-<말>. 명령 이름과 인자(--to · --inbox · --create · --parent · --delete · --confirm)의 원본은 그 스킬
# `mail.py` 의 `parser` 다 — 거기서 바뀌면 여기와 `hand_args` 를 함께 바꾼다
VERBS = {MOVE: "move", TRASH: "trash", RESTORE: "restore", FOLDER_CREATE: "folder", FOLDER_DELETE: "folder", RULE_ADD: "rule",
         RULE_EDIT: "rule", RULE_DELETE: "rule"}

KIND_WORDS = {MOVE: "메일 옮기기", TRASH: "휴지통으로 보내기", RESTORE: "휴지통에서 되살리기", FOLDER_CREATE: "폴더 만들기",
              FOLDER_DELETE: "폴더 지우기", RULE_ADD: "규칙 넣기", RULE_EDIT: "규칙 고치기", RULE_DELETE: "규칙 지우기"}
OUTCOME_WORDS = {DONE: "됐다", UNKNOWN: "결과 모름"}

HELD = ("[기록 — 이 바꿈을 잡아 두었다({kind}{n}). 사람이 이대로 하자고 하시면 {how} — 안 하기로 하시면 실행하지 않고 journal.py drop "
        "으로 놓는다]")
HOW_LINE = "아래 실행 줄을 그대로 친다(실행의 글이 journal.py done 으로 간다)"
HOW_SAME = "미리 보기와 같은 인자에 --confirm {key} 를 붙여 실행하고 그 글을 journal.py done 에 준다"
APPLY_ROW = "  {cmd}"
HELD_SUPERSEDED = ("[기록 — 앞서 잡아 둔 바꿈(실행했는지 모른다)을 기록 {id} 에 「결과 모름」으로 옮겼다. 사람이 안 하기로 하신 미리 보기는 "
                   "journal.py drop 으로 놓는다]")
HELD_SAME = "[기록 — 앞서 잡아 둔 같은 미리 보기(확인 열쇠가 같다 — 실행되지 않았다)를 기록 없이 이것으로 바꿨다]"
DROPPED = "[기록 — 잡아 둔 바꿈을 기록 없이 놓았다({what})]"
NO_HELD_DROP = "[기록 — 잡아 둔 바꿈이 없어 놓을 것이 없다]"
MISMATCH = ("[기록 — 실행의 글이 잡아 둔 바꿈과 달라 적지 않았다({why}). 잡아 둔 바꿈은 그대로 둔다. 다음: 이 실행이 어느 미리 보기의 "
            "것인지 본다 — 잡아 둔 바꿈의 실행이면 그 실행의 글을 다시 주고, 아니면 사람에게 이 실행은 기록이 맞지 않는다고 말씀드린다]")
WHY_APPLIED_FORM = "실행의 「됐다」 줄을 이 파일이 아는 꼴로 못 읽었다"
WHY_APPLIED_KEY = "실행이 맞춘 확인 열쇠 {got} · 잡아 둔 미리 보기의 열쇠 {want}"
WHY_APPLIED_COUNT = "실행은 {got}통 · 잡아 둔 것은 {want}통"
WHY_APPLIED_TARGET = "실행의 받을 자리 「{got}」 · 잡아 둔 것 「{want}」"
WHY_APPLIED_FOLDER = "실행의 폴더 「{got}」 · 잡아 둔 것 「{want}」"
NOT_HELD = ("[기록 — 이 바꿈을 잡지 않았다: {why}. 이대로 실행하면 비서가 되돌릴 기록이 안 남는다 — 사람에게 그렇게 말씀드리고, 하자고 "
            "하시면 그때만 실행한다. 다음: 회사 메일 스킬의 미리 보기를 다시 받아 같은 종류로 hold 에 흘린다]")
NO_HELD = "[기록 — 잡아 둔 바꿈이 없어 적지 않았다. 다음: 다음 바꿈은 미리 보기를 journal.py hold 로 받는다 — 이번 바꿈은 사람에게 기록이 안 남았다고 말씀드린다]"
STALE_DONE = "[기록 — 실행 손이 확인 열쇠가 안 맞아 바꾸지 않았다고 했다. 기록하지 않고 잡아 둔 것을 놓았다 — 다음: 미리 보기부터 다시]"
WROTE = "[기록 {id} 에 적었다 — {what} · {outcome}. 되돌리려면 journal.py undo {id}]"
WROTE_UNKNOWN_HINT = " — 실행 손의 「됐다」 줄이 없었다. 메일함에서 지금 자리를 본 뒤 사람에게 말씀드린다"

WHY_HEAD = "미리 보기에 「{kind}」의 머리 줄이 없다"
WHY_KEY = "미리 보기에 확인 열쇠 줄이 없다"
WHY_COUNT = "미리 보기의 메일 {lines}줄과 머리의 {head}통이 같지 않다"
WHY_GIVEN = "준 메일 번호 {unids}개와 미리 보기의 메일 {lines}줄이 같지 않다 — 번호는 미리 보기 줄 끝에서 읽으니 주지 않아도 된다"
WHY_PLACE = "{n}번째 메일 줄에서 자리(받은편지함 · 보낸편지함 · 임시보관함 · 폴더)를 못 읽었다"
WHY_TAIL = "{n}번째 메일 줄 끝에 메일 번호(32자리)가 없다 — 회사 메일 스킬이 이 파일보다 옛 판이면 그 스킬부터 맞춘다"
WHY_ORDER = "{n}번째 메일 줄 끝의 메일 번호가 준 {n}번째 번호와 다르다 — 번호는 미리 보기 줄 끝에서 읽으니 주지 않아도 된다"
WHY_UNID = "메일 번호가 아니다(32자리): {bad}"
WHY_TARGET = "받을 자리가 미리 보기(「{head}」)와 준 것(「{given}」)이 다르다"
WHY_TARGET_MISSING = "휴지통 미리 보기를 옮기기 조각으로 적을 때는 옮길 폴더를 --to 로 준다 — 그 미리 보기에는 받을 자리가 없다"
WHY_RULE_LINES = "규칙의 지금 · 바꿀 두 줄을 못 읽었다"
WHY_FOR_MAILS = "메일 번호와 받을 자리는 메일을 건드리는 바꿈(move · trash · restore)에만 준다"
WHY_PIECE_NEXT = ("조각은 안 안에서 차례대로 적는다 — 지금 안의 다음 조각은 {next}번이다. 새 안이면 --piece 1 부터 센다(plans 가 보인 "
                  "옛 조각 번호는 새 안에서 다시 센다). 이미 보인 조각을 빼거나 고칠 때도 --piece 1 부터 안을 다시 적는다 — 고친 조각을 "
                  "뒤 번호로 덧붙이면 옛 조각이 안에 남아 함께 잡힌다")

# 보여 드린 안 — 한 번 확인받는 안의 조각과, 실행 직전에 다시 받은 미리 보기를 그 조각에 대기
SHOWN_ROW = "[조각 {n}] {what}"
SHOWN = ("[기록 — 안 {plan} 의 {n}번 조각으로 적었다{reset}. 조각을 다 보인 뒤 안 전체를 한 번 여쭙는다 — 하자고 하시면 조각마다 새 "
         "미리 보기를 journal.py hold … --shown {n} 에 준다]")
SHOWN_RESET = (" · 1번 조각이라 앞서 적어 둔 안(조각 {count}개)은 걷었다 — 그 안의 안 바꾼 조각은 메일 번호째 journal.py plans 가 "
               "든다")
NOT_SHOWN = "[기록 — 이 조각을 적지 않았다: {why}. 다음: 회사 메일 스킬의 미리 보기를 다시 받아 같은 종류로 show 에 흘린다]"
HELD_SHOWN = "[기록 — 보여 드린 {piece}번 조각과 같아 이 바꿈을 잡아 두었다({kind}{n}). 확인받은 안의 그 조각이니 {how}]"
SHOWN_DIFF = "[기록 — 보여 드린 {n}번 조각과 다른 점:"
SHOWN_DIFF_TAIL = ("  그래서 잡지 않았다 — 실행하지 않는다. 다음: 사용자께 위 다른 점과 이 미리 보기를 보이고 여쭙는다. 이대로 하자고 하시면 "
                   "이 미리 보기를 --shown 없이 hold 로 잡는다]")
SHOWN_NONE = ("[기록 — {n}번 조각을 보인 기록이 없어 잡지 않았다. 다음: 이 미리 보기를 사용자께 보이고 확인받은 뒤 --shown 없이 hold 로 "
              "잡는다]")
SHOWN_EMPTY = "[기록 — 적어 둔 안이 없다. 다음: 조각마다 미리 보기를 journal.py show … --piece <n> 으로 흘려 안을 적는다]"
SHOWN_NO_BODY = "  (이 조각은 메일 줄 없이 적혔다 — 그 미리 보기를 다시 받아 show 로 적어야 줄이 선다)"
SHOWN_LIST = ("[기록 — 적어 둔 안: 조각 {count}개 · 처음 적은 때 {first} · 마지막 {last}. 이 줄들을 사용자께 그대로 보이고 안 전체를 한 번 "
              "여쭙는다 — 하자고 하시면 조각마다 새 미리 보기를 journal.py hold … --shown <n> 에 준다]")
DIFF_KIND = "  - 종류: 보인 것 {was} · 지금 {now}"
DIFF_TARGET = "  - 받을 자리: 보인 것 {was} · 지금 {now}"
DIFF_ADDED = "  - 보인 조각에 없던 메일 {count}통: {unids}"
DIFF_GONE = "  - 보인 조각에 있었는데 이 미리 보기에 없는 메일 {count}통: {unids}"
DIFF_PLACE = "  - 그 사이 자리가 바뀐 메일 {count}통: {moves}"
DIFF_PATH = "  - 폴더: 보인 것 「{was}」 · 지금 「{now}」"
DIFF_RULE = "  - 규칙: 보인 것 {was} · 지금 {now}"

# 적어 둔 안들 — show 가 적은 조각을 안마다 남기고, 그 뒤 「됐다」로 맺은 기록이 바꾼 것은 빼고 보인다
PLANS_HEAD = "[안 {plan}] 적은 때 {when} · 조각 {total}개 가운데 안 바꾼 것 {left}개"
PLANS_PIECE = "  [조각 {n}] {what}{why}{cmd}"
PLANS_WHY = " — {why}"
PLANS_HAND = " · 미리 보기: {cmd}"           # 손에 줄 받을 자리 · 메일 번호 · 폴더 경로가 든 명령 — 규칙 조각은 칸을 몰라 없다
PLANS_LATER = "    보인 뒤 기록 {ids} 이 바꾼 메일 {count}통은 뺐다"
PLANS_FOOT = ("[기록 — 안 바꾼 조각은 확인받은 안이 아니라 미리 보기의 입력이다. 다시 다루려면 조각마다 그 「미리 보기:」 명령(규칙 조각은 "
              "그 판의 칸)으로 손의 미리 보기를 다시 받아 journal.py show … --piece <n> 으로 새 안을 적고(위의 조각 번호가 아니라 "
              "새 안에서 1 부터 다시 센다), shown 의 줄을 사용자께 보이고 한 번 여쭙는다]")
PLANS_EMPTY = "[기록 — 안 바꾼 조각이 남은 안이 없다. 다음: 메일함에서 안을 새로 짓는다]"

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

UNDO_HEAD = ("되돌리는 차례 — 차례마다 그 줄 끝의 명령을 그대로 쳐서 회사 메일 스킬의 미리 보기를 기록에 잡는다. 그 미리 보기를 사람에게 "
             "보이고 확인받으면 기록이 내는 실행 줄을 친다. 명령이 없는 차례는 그 말대로 미리 보기를 지어 [ ] 안의 기록 명령에 흘린다:")
UNDO_FOOT = ("미리 보기가 메일의 지금 자리를 보인다 — 이미 제자리인 메일 · 그 사이 사람이 다른 데로 옮긴 메일은 그대로 말씀드리고 옮기지 "
             "않는다. 이 기록의 결과가 「결과 모름」이면 바뀌지 않은 몫이 있을 수 있다 — 미리 보기가 그것을 가린다")
HOLD_STEP = " [journal.py hold {kind} --undoes {id}]"   # 명령 줄을 못 짓는 차례 — 모델이 지은 미리 보기를 잡는 이 파일의 명령
STEP_MOVE_BACK = "{n}. {place}(으)로 옮길 메일 {count}통: {cmd}"
STEP_NO_HAND = "{n}. {place}에 있던 메일 {count}통은 되돌리지 못한다 — 회사 메일 스킬에 그 자리로 옮기는 손이 없다(웹메일에서 사람이): {unids}"
STEP_RESTORE = "{n}. 휴지통에서 되살릴 메일 {count}통: {cmd}"
STEP_AFTER_RESTORE = "{n}. 되살린 뒤 {place}(으)로 옮길 메일 {count}통: {cmd}"
STEP_RESTORE_UNKNOWN = "    {place}에 있던 메일 {count}통은 되살아나는 자리를 안 쟀다 — 되살린 뒤 웹메일에서 자리를 본다"
STEP_RETRASH = "{n}. 다시 휴지통으로 보낼 메일 {count}통: {cmd}"
STEP_FOLDER_DROP = "1. 폴더 「{path}」를 지운다 — 비어 있을 때만 지워진다(그 사이 메일이 들었으면 사람에게 말씀드린다): {cmd}"
STEP_FOLDER_MAKE = "1. 폴더 「{path}」를 다시 만든다: {cmd}"
STEP_RULE_DROP = "1. 넣은 규칙(열쇠 {unid})을 지운다 — 넣은 규칙 「{rule}」: {cmd}"
STEP_RULE_DROP_NOKEY = "1. 넣은 규칙의 열쇠를 모른다 — 규칙 목록에서 이 꼴의 규칙을 찾아 지운다{hold}: {rule}"
STEP_RULE_BACK = ("1. 규칙(열쇠 {unid})을 앞 판으로 고친다 — 회사 메일 스킬의 preview-rule --unid {unid} 에 앞 판의 칸을 준다{hold}: 앞 판 "
                  "{before} (지금 판으로 적힌 것: {after})")
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


def _lines(path: pathlib.Path, key: str) -> tuple[list[dict[str, Any]], list[int]]:
    """덧붙이기만 하는 파일의 줄 전부(옛것부터)와 못 읽은 줄의 번호 — `key` 칸이 정수인 줄만 읽은 것으로 센다."""
    if not path.exists():
        return [], []
    rows, bad = [], []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):   # 끊긴 줄의 반쪽 글자도 그 줄만 못 읽는다
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get(key), int):
                raise ValueError
            rows.append(row)
        except ValueError:
            bad.append(n)
    return rows, bad


def _append_line(path: pathlib.Path, row: dict[str, Any]) -> None:
    """한 줄을 덧붙인다 — 있는 줄은 고치지 않는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def entries(folder: pathlib.Path) -> tuple[list[dict[str, Any]], list[int]]:
    """기록 전부(옛것부터)와 못 읽은 줄의 번호."""
    return _lines(folder / LOG_FILE, "id")


def append(folder: pathlib.Path, entry: dict[str, Any]) -> int:
    """기록 한 줄을 덧붙이고 그 번호를 낸다 — 있는 줄은 고치지 않는다."""
    rows, _ = entries(folder)
    entry = {"id": next_id(rows), **entry}
    _append_line(folder / LOG_FILE, entry)
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
    """미리 보기 → 잡아 둘 바꿈. 메일 번호는 메일 줄 끝 · 받을 자리는 머리 · 확인 열쇠는 그 줄에서 읽는다. 준 `unids` · `to` 는 옛 꼴의
    부름이라 미리 보기와 같은지만 댄다(안 줬으면 빈 것 · None). 꼴이 다르면 `Refused`. 머리 앞의 줄(표준 오류를 함께 흘린 경고)은 건너뛴다."""
    lines = [x for x in text.splitlines() if x.strip()]
    at = next((i for i, x in enumerate(lines) if HEADS[kind].match(x)), None)
    if at is None:
        raise Refused(WHY_HEAD.format(kind=kind))
    lines = lines[at:]
    head = HEADS[kind].match(lines[0])
    key = next((m.group(1) for x in lines if (m := KEY_LINE.match(x))), None)
    if key is None:
        raise Refused(WHY_KEY)
    hold: dict[str, Any] = {"kind": kind, "key": key}
    if kind in MAIL_KINDS:
        items = _items(lines)
        if len(items) != int(head.group(1)):
            raise Refused(WHY_COUNT.format(lines=len(items), head=head.group(1)))
        if unids and len(unids) != len(items):
            raise Refused(WHY_GIVEN.format(unids=len(unids), lines=len(items)))
        if kind == MOVE:
            shown = head.group(2)
            if to is not None and shown != (to or PLACE_NAMES[INBOX]):
                raise Refused(WHY_TARGET.format(head=shown, given=to or PLACE_NAMES[INBOX]))
            hold["to"] = "" if shown == PLACE_NAMES[INBOX] else shown
        mails = []
        for n, line in enumerate(items, 1):
            rest = line[2:]
            tail = TAIL_UNID.search(rest)
            if tail is None:
                raise Refused(WHY_TAIL.format(n=n))
            unid = tail.group(1)
            if unids and unids[n - 1] != unid:
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
    """「됐다」 줄이 잡아 둔 바꿈의 실행인가 — 다르거나 못 읽으면 `Mismatch`. 줄 끝의 확인 열쇠가 있고 잡아 둔 미리 보기의 열쇠를 알면
    그 둘로 댄다(열쇠는 미리 보기가 본 판 — 받을 자리와 메일마다의 번호 · 자리 · 폴더 경로 · 규칙의 판 — 의 지문이다). 열쇠가 없는 줄
    (갱신 전의 손)이나 열쇠를 적기 전에 잡아 둔 바꿈은 메일 수 · 받을 자리 · 폴더 경로로 대고, 규칙은 대지 않는다."""
    got_key, want_key = APPLIED_KEY.search(ok), hold.get("key")
    if got_key and want_key:
        if got_key.group(1) != want_key:
            raise Mismatch(WHY_APPLIED_KEY.format(got=got_key.group(1), want=want_key))
        return
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
        tail = TAIL_UNID.search(APPLIED_KEY.sub("", ok))
        if tail:
            more["rule_unid"] = tail.group(1)
    if kind == RESTORE:
        away = next((ELSEWHERE.match(x) for x in lines if ELSEWHERE.match(x)), None)
        if away:
            more["elsewhere"] = int(away.group(1))
    return DONE, more


# ── 다음 걸음의 명령 줄 — 미리 보기 · 기록이 이미 든 값으로 짓는다 ─────────────────────────────

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


def preview_line(kind: str, args: Sequence[str], *then: str) -> str:
    """손의 미리 보기를 이 파일의 명령(`then`)에 흘리는 줄."""
    return f"{command(HAND, f'preview-{VERBS[kind]}', *args)} | {command(SELF, *then)}"


def apply_line(kind: str, args: Sequence[str], key: str) -> str:
    """잡아 둔 미리 보기의 실행을 `done` 에 흘리는 줄 — 미리 보기와 같은 인자에 그 열쇠."""
    return f"{command(HAND, f'apply-{VERBS[kind]}', *args, '--confirm', key)} | {command(SELF, 'done')}"


def held_args(hold: dict[str, Any], rule_unid: str = "") -> list[str] | None:
    """잡아 둔 바꿈을 손에 줄 인자 — 미리 보기에서 읽은 받을 자리 · 메일 번호 · 폴더 경로. 규칙 지우기는 미리 보기에 열쇠가 없어
    부르는 쪽이 기록에서 준다(`rule_unid`)."""
    return hand_args(hold["kind"], to=hold.get("to") or "", unids=[m["unid"] for m in hold.get("mails") or []], path=hold.get("path") or "",
                     rule_unid=rule_unid)


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
    """기록 하나를 되돌리는 차례 — 차례마다 칠 명령 줄(손의 미리 보기 → 이 파일의 `hold … --undoes`)을 댄다. 값을 다 모르는 차례(규칙의
    칸)는 할 일을 말하고 잡을 이 파일의 명령만 댄다."""
    kind = e.get("kind")
    mails = e.get("mails") or []
    entry_id = str(e.get("id"))

    def hold(step_kind: str) -> str:
        return HOLD_STEP.format(kind=step_kind, id=entry_id)

    def line(step_kind: str, **values: Any) -> str:
        return preview_line(step_kind, hand_args(step_kind, **values) or [], "hold", step_kind, "--undoes", entry_id)

    def groups(pick) -> list[tuple[str, str, list[str]]]:
        out: dict[tuple[str, str], list[str]] = {}
        for m in mails:
            if pick(m):
                out.setdefault((m.get("place", ""), m.get("folder", "")), []).append(m["unid"])
        return [(p, f, u) for (p, f), u in out.items()]

    def back(n: int, form: str, place: str, folder: str, unids: list[str]) -> str:
        return form.format(n=n, place=_place_word(place, folder), count=len(unids), unids=" ".join(unids),
                           cmd=line(MOVE, to=folder if place == FOLDER else "", unids=unids))

    every = [m["unid"] for m in mails]
    steps: list[str] = []
    if kind == MOVE:
        n = 0
        for place, folder, unids in groups(lambda m: True):
            n += 1
            steps.append(back(n, STEP_NO_HAND if place in (SENT, DRAFTS) else STEP_MOVE_BACK, place, folder, unids))
    elif kind == TRASH:
        steps.append(STEP_RESTORE.format(n=1, count=len(mails), cmd=line(RESTORE, unids=every)))
        n = 1
        for place, folder, unids in groups(lambda m: m.get("place") == FOLDER):
            n += 1
            steps.append(back(n, STEP_AFTER_RESTORE, place, folder, unids))
        for place, folder, unids in groups(lambda m: m.get("place") == SENT):
            steps.append(STEP_RESTORE_UNKNOWN.format(place=_place_word(place, folder), count=len(unids)))
    elif kind == RESTORE:
        steps.append(STEP_RETRASH.format(n=1, count=len(mails), cmd=line(TRASH, unids=every)))
    elif kind in (FOLDER_CREATE, FOLDER_DELETE):
        path = e.get("path", "")
        if kind == FOLDER_CREATE:
            steps.append(STEP_FOLDER_DROP.format(path=path, cmd=line(FOLDER_DELETE, path=path)))
        else:
            steps.append(STEP_FOLDER_MAKE.format(path=path, cmd=line(FOLDER_CREATE, path=path)))
    else:
        rule = e.get("rule") or {}
        key = rule.get("unid") or ""
        if kind == RULE_ADD:
            steps.append(STEP_RULE_DROP.format(unid=key, rule=rule.get("after", ""), cmd=line(RULE_DELETE, rule_unid=key)) if key
                         else STEP_RULE_DROP_NOKEY.format(rule=rule.get("after", ""), hold=hold(RULE_DELETE)))
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


def unexecuted_twin(old: dict[str, Any] | None, new: dict[str, Any]) -> bool:
    """잡아 둔 바꿈이 새 미리 보기와 같은 종류 · 같은 확인 열쇠라 실행되지 않은 것인가. 열쇠는 그 미리 보기가 본 자리의 지문이라, 실행됐으면
    자리가 바뀌어 열쇠가 달라지거나(옮기기 · 폴더 만들기 · 규칙 고치기) 미리 보기가 안 선다(휴지통 · 되살리기 · 폴더 · 규칙 지우기).
    규칙 넣기만 실행 뒤에도 같은 열쇠가 나와 뺀다 — 그것은 「결과 모름」으로 옮긴다."""
    return bool(old and old.get("key") and old.get("key") == new.get("key") and old.get("kind") == new["kind"] != RULE_ADD)


def given(args) -> tuple[list[str], str | None]:
    """`show` · `hold` 가 받은 (메일 번호, 받을 자리 — 받은편지함이면 "" · 안 줬으면 None). 틀리면 `Refused`."""
    unids = [u.strip().upper() for u in args.unids]
    bad = [u for u in unids if not UNID.match(u)]
    if bad:
        raise Refused(WHY_UNID.format(bad=", ".join(bad[:3])))
    if args.kind not in MAIL_KINDS and (unids or args.to is not None or args.inbox):
        raise Refused(WHY_FOR_MAILS)
    return unids, "" if args.inbox else args.to


def _shown(folder: pathlib.Path) -> dict[str, Any]:
    """보여 드린 안 파일 — {"plan": 안 번호, "pieces": …}. 없거나 못 읽으면 빈 것."""
    try:
        got = json.loads((folder / SHOWN_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return got if isinstance(got, dict) else {}


def shown_pieces(folder: pathlib.Path) -> dict[str, dict[str, Any]]:
    """보여 드린 안의 조각 — 조각 번호(글자) → 조각. 없거나 못 읽으면 빈 것."""
    pieces = _shown(folder).get("pieces")
    return pieces if isinstance(pieces, dict) else {}


def plan_rows(folder: pathlib.Path) -> list[dict[str, Any]]:
    """적어 둔 안들의 조각 줄 전부(옛것부터) — 못 읽은 줄은 건너뛴다."""
    return _lines(folder / PLANS_FILE, "plan")[0]


def cmd_show(args, folder: pathlib.Path) -> int:
    text = read_input(args.infile)
    pieces, plan = shown_pieces(folder), _shown(folder).get("plan")
    try:
        unids, to = given(args)
        piece, body = read_shown(args.kind, text, unids, to)
        # 1 이 아닌 번호는 지금 안의 다음 차례만 받는다 — 다른 안의 옛 번호를 그대로 주면 지금 안에 섞이고 그 자리의 조각이 plans 에서 덮인다
        nxt = max((int(k) for k in pieces if k.isdigit()), default=0) + 1 if isinstance(plan, int) else FIRST_PIECE
        if args.piece != FIRST_PIECE and args.piece != nxt:
            raise Refused(WHY_PIECE_NEXT.format(next=nxt))
    except Refused as exc:
        for line in text.splitlines():       # 적지 못한 조각은 손의 글을 그대로 보인다 — 파이프가 받아 갔다
            print(line)
        print(NOT_SHOWN.format(why=exc))
        return EXIT_FAILED
    reset = ""
    if args.piece == FIRST_PIECE or not isinstance(plan, int):
        plan = max((r["plan"] for r in plan_rows(folder)), default=0) + 1
    if args.piece == FIRST_PIECE:
        reset = SHOWN_RESET.format(count=len(pieces)) if pieces else ""
        pieces = {}
    at = _now()
    # 안들에는 메일 줄(제목 · 보낸 분)을 안 싣는다. log_from — 이 조각을 보인 뒤에 붙는 첫 기록 번호(그 뒤 바꾼 것을 가르는 금)
    row = {"plan": plan, "piece": args.piece, **piece, "at": at, "log_from": next_id(entries(folder)[0])}
    if args.why:
        row["why"] = args.why.strip()
    _append_line(folder / PLANS_FILE, row)
    pieces[str(args.piece)] = {**piece, "body": body, "at": at}
    _write_atomic(folder / SHOWN_FILE, json.dumps({"plan": plan, "pieces": pieces}, ensure_ascii=False))
    for line in [SHOWN_ROW.format(n=args.piece, what=describe(piece)), *body, SHOWN.format(plan=plan, n=args.piece, reset=reset)]:
        print(line)
    return EXIT_OK


def left_of(row: dict[str, Any], rows: Sequence[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[int, int]]:
    """적어 둔 조각에서 아직 안 바꾼 몫 → (남은 조각 · 다 바꿨으면 None, 그 뒤 메일을 바꾼 기록 번호 → 뺀 통 수).
    조각을 보인 뒤(`log_from` 부터) 「됐다」로 맺은 기록만 바꾼 것으로 센다 — 결과 모름은 남긴다(다시 받는 미리 보기가 지금 자리를 보인다).
    메일 바꿈은 어느 안 · 어느 조각에서 왔든 그 메일 번호를 바꾼 기록이면 뺀다 — 조각 밖에서 따로 잡은 바꿈도 메일함을 바꿨다."""
    later = [r for r in rows if r["id"] >= int(row.get("log_from") or 0) and r.get("outcome") == DONE]
    kind = row.get("kind")
    if kind in MAIL_KINDS:
        by: dict[str, int] = {}
        for r in later:
            for m in r.get("mails") or []:
                by.setdefault(m.get("unid", ""), r["id"])
        keep = [m for m in row.get("mails") or [] if m.get("unid") not in by]
        cut: dict[int, int] = {}
        for m in row.get("mails") or []:
            if m.get("unid") in by:
                cut[by[m["unid"]]] = cut.get(by[m["unid"]], 0) + 1
        return ({**row, "mails": keep} if keep else None), cut
    if kind in (FOLDER_CREATE, FOLDER_DELETE):
        same = any(r.get("kind") == kind and r.get("path") == row.get("path") for r in later)
    else:
        def plain(rule: Any) -> dict[str, Any]:
            return {k: v for k, v in (rule or {}).items() if k != "unid"}   # 넣은 규칙의 열쇠는 맺을 때 붙는다
        same = any(r.get("kind") == kind and plain(r.get("rule")) == plain(row.get("rule")) for r in later)
    return (None if same else row), {}


def cmd_plans(args, folder: pathlib.Path) -> int:
    rows, _ = entries(folder)
    last: dict[int, dict[int, dict[str, Any]]] = {}
    for r in plan_rows(folder):                  # 같은 안의 같은 조각을 다시 적었으면 나중 줄이 선다
        last.setdefault(r["plan"], {})[int(r.get("piece") or FIRST_PIECE)] = r
    out: list[str] = []
    shown = 0
    for plan in sorted(last, reverse=True):
        if args.most and shown >= args.most:
            break
        pieces = last[plan]
        lines: list[str] = []
        left = 0
        for n in sorted(pieces):
            rest, cut = left_of(pieces[n], rows)
            if rest is None:
                continue
            left += 1
            why = PLANS_WHY.format(why=rest["why"]) if rest.get("why") else ""
            hand = held_args(rest)
            cmd = PLANS_HAND.format(cmd=command(HAND, f"preview-{VERBS[rest['kind']]}", *hand)) if hand is not None else ""
            lines.append(PLANS_PIECE.format(n=n, what=describe(rest), why=why, cmd=cmd))
            if cut:
                lines.append(PLANS_LATER.format(ids=" · ".join(map(str, sorted(cut))), count=sum(cut.values())))
        if not left:
            continue
        shown += 1
        when = min(str(p.get("at") or "")[:16].replace("T", " ") or WHEN_UNKNOWN for p in pieces.values())
        out += [PLANS_HEAD.format(plan=plan, when=when, total=len(pieces), left=left), *lines]
    for line in [*out, PLANS_FOOT] if out else [PLANS_EMPTY]:
        print(line)
    return EXIT_OK


def cmd_shown(args, folder: pathlib.Path) -> int:
    pieces = shown_pieces(folder)
    if not pieces:
        print(SHOWN_EMPTY)
        return EXIT_FAILED
    order = sorted(pieces, key=lambda k: int(k) if k.isdigit() else 0)
    for n in order:
        p = pieces[n]
        body = p.get("body")
        print(SHOWN_ROW.format(n=n, what=describe(p)))
        # 메일 줄이 원래 없는 조각(폴더 · 규칙)은 머리 줄이 전부다 — 줄이 빠졌다는 말은 메일을 건드리는 조각에만 한다
        for line in body if isinstance(body, list) and body else [SHOWN_NO_BODY] if p.get("kind") in MAIL_KINDS else []:
            print(line)
    ats = sorted(str(pieces[n].get("at") or "")[:16].replace("T", " ") or WHEN_UNKNOWN for n in order)
    print(SHOWN_LIST.format(count=len(order), first=ats[0], last=ats[-1]))
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
    if unexecuted_twin(held(folder), hold):
        (folder / HELD_FILE).unlink(missing_ok=True)
        print(HELD_SAME)
    elif (superseded := _settle_old(folder)) is not None:
        print(HELD_SUPERSEDED.format(id=superseded))
    hold["undoes"] = args.undoes
    hold["at"] = _now()
    _write_atomic(folder / HELD_FILE, json.dumps(hold, ensure_ascii=False))
    n = f" · 메일 {len(hold['mails'])}통" if "mails" in hold else ""
    said = HELD if args.shown is None else HELD_SHOWN
    undone = next((r for r in entries(folder)[0] if r["id"] == args.undoes), {}) if args.undoes is not None else {}
    hand = held_args(hold, rule_unid=(undone.get("rule") or {}).get("unid") or "" if undone.get("kind") == RULE_ADD else "")
    how = HOW_LINE if hand is not None else HOW_SAME.format(key=hold["key"])
    print(said.format(kind=KIND_WORDS[args.kind], n=n, piece=args.shown, how=how))
    if hand is not None:
        print(APPLY_ROW.format(cmd=apply_line(args.kind, hand, hold["key"])))
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
        target.add_argument("--to", help="show move 가 휴지통 미리 보기를 받을 때만 — 옮길 폴더 경로. 옮기기 미리 보기는 머리의 받을 자리를 읽는다")
        # 옛 꼴의 부름(메일 번호 · --inbox)은 받되 도움말에 안 보인다 — 미리 보기에서 읽는 값을 다시 치라는 말로 읽히지 않게
        target.add_argument("--inbox", action="store_true", help=argparse.SUPPRESS)
        q.add_argument("--in", dest="infile", help="표준 입력 대신 읽을 파일")
        q.add_argument("unids", nargs="*", help=argparse.SUPPRESS)
    s.add_argument("--piece", type=piece_number, required=True, help=f"안에서 이 조각의 번호 — {FIRST_PIECE} 이면 새 안을 연다")
    s.add_argument("--why", help="이 조각의 무리 이름과 까닭 한 줄 — plans 가 다음 판에 같이 낸다. 메일 제목 · 보낸 분은 안 적는다")
    h.add_argument("--shown", type=piece_number, help="확인받은 안의 이 조각과 같을 때만 잡는다")
    h.add_argument("--undoes", type=int, help="이 바꿈이 되돌리는 기록 번호")
    d = sub.add_parser("done", help="실행의 글을 읽어 잡아 둔 바꿈을 기록으로 맺는다")
    d.add_argument("--in", dest="infile", help="표준 입력 대신 읽을 파일")
    sub.add_parser("drop", help="사람이 안 하기로 하신 미리 보기를 기록 없이 놓는다 — 실행하지 않았을 때만(실행했으면 done)")
    sub.add_parser("shown", help="적어 둔 안 — show 가 조각마다 보인 줄을 그대로 다시 낸다(읽기만)")
    pl = sub.add_parser("plans", help="적어 둔 안들 — 아직 안 바꾼 조각의 받을 자리 · 메일 번호 · 까닭(읽기만 · 새것부터). 미리 보기의 입력일 뿐이다")
    pl.add_argument("--most", type=int, default=PLANS_MOST, help="보일 안의 수 — 안 바꾼 조각이 남은 안만 센다(0 이면 다)")
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
    return {"show": cmd_show, "shown": cmd_shown, "plans": cmd_plans, "hold": cmd_hold, "done": cmd_done, "drop": cmd_drop, "log": cmd_log,
            "mails": cmd_mails, "undo": cmd_undo}[args.command](args, folder)


if __name__ == "__main__":
    sys.exit(main())
