"""기록 손이 사람에게 하는 말 — 셈이 낸 상태 · 기록 한 줄을 받아 글로만 옮긴다. 파일 · 프로세스 · 표준 입출력에는 닿지 않는다.

말 틀은 다 여기 이름으로 산다 — 멈춘 까닭의 문장도 까닭의 이름으로 여기서 고른다(`WHY_FORMS`). 이 모듈은 이름 붙은 값(`journal_const.py`)만 싣는다.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from journal_const import (DONE, FOLDER, FOLDER_CREATE, FOLDER_DELETE, FOLDER_KINDS, INBOX, MAIL_KINDS, MOVE, PLACE_NAMES, RESTORE,
                           RULE_ADD, RULE_DELETE, RULE_EDIT, TRASH, UNKNOWN)
import journal_const as c

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
HOLD_STEP = " [journal.py hold {kind} --undoes {id}]"   # 명령 줄을 못 짓는 차례 — 모델이 지은 미리 보기를 잡는 기록 손의 명령
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

# 말 조각 — 기록 한 줄 · 자리 · 다른 점을 짓는 틀
HELD_COUNT = " · 메일 {count}통"
PIECE_FROM = "조각 번호는 {first} 부터다: {text}"
FOLDER_PLACE = "폴더 「{folder}」"
DESCRIBE_MAILS = "{word} {count}통({origin}){target}"
DESCRIBE_TARGET = " → {target}"
DESCRIBE_ORIGIN = "{place} {count}"
DESCRIBE_FOLDER = "{word} 「{path}」"
DESCRIBE_RULE = "{word} — {rule}"
DIFF_MOVE = "{unid}({was} → {now})"
RULE_ARROW = " → "
CHAIN_ARROW = " → "
CHAIN_LINK = "{id}({word})"
LIST_SEP = " · "
UNID_SEP = " "
BAD_SEP, BAD_MOST = ", ", 3                # 메일 번호가 아닌 것을 댈 때 — 앞의 몇 개만 쉼표로 잇는다

DIFF_FORMS = {c.DIFF_IS_KIND: DIFF_KIND, c.DIFF_IS_TARGET: DIFF_TARGET, c.DIFF_IS_ADDED: DIFF_ADDED, c.DIFF_IS_GONE: DIFF_GONE,
              c.DIFF_IS_MOVED: DIFF_PLACE, c.DIFF_IS_PATH: DIFF_PATH, c.DIFF_IS_RULE: DIFF_RULE}
STEP_FORMS = {c.STEP_IS_MOVE_BACK: STEP_MOVE_BACK, c.STEP_IS_NO_HAND: STEP_NO_HAND, c.STEP_IS_RESTORE: STEP_RESTORE,
              c.STEP_IS_AFTER_RESTORE: STEP_AFTER_RESTORE, c.STEP_IS_RESTORE_UNKNOWN: STEP_RESTORE_UNKNOWN, c.STEP_IS_RETRASH: STEP_RETRASH,
              c.STEP_IS_FOLDER_DROP: STEP_FOLDER_DROP, c.STEP_IS_FOLDER_MAKE: STEP_FOLDER_MAKE, c.STEP_IS_RULE_DROP: STEP_RULE_DROP,
              c.STEP_IS_RULE_DROP_NOKEY: STEP_RULE_DROP_NOKEY, c.STEP_IS_RULE_BACK: STEP_RULE_BACK,
              c.STEP_IS_RULE_BACK_NOKEY: STEP_RULE_BACK_NOKEY, c.STEP_IS_RULE_READD: STEP_RULE_READD}
LINK_WORDS = {c.LINK_IS_UNDO: LINK_UNDO, c.LINK_IS_REDO: LINK_REDO}
LINK_TAILS = {c.ENDED_DONE: "", c.ENDED_HELD: LINK_HELD, c.ENDED_UNKNOWN: LINK_UNKNOWN}
WHY_FORMS = {c.WHY_IS_HEAD: WHY_HEAD, c.WHY_IS_KEY: WHY_KEY, c.WHY_IS_COUNT: WHY_COUNT, c.WHY_IS_GIVEN: WHY_GIVEN, c.WHY_IS_PLACE: WHY_PLACE,
             c.WHY_IS_TAIL: WHY_TAIL, c.WHY_IS_ORDER: WHY_ORDER, c.WHY_IS_UNID: WHY_UNID, c.WHY_IS_TARGET: WHY_TARGET,
             c.WHY_IS_TARGET_MISSING: WHY_TARGET_MISSING, c.WHY_IS_RULE_LINES: WHY_RULE_LINES, c.WHY_IS_FOR_MAILS: WHY_FOR_MAILS,
             c.WHY_IS_PIECE_NEXT: WHY_PIECE_NEXT, c.WHY_IS_APPLIED_FORM: WHY_APPLIED_FORM, c.WHY_IS_APPLIED_KEY: WHY_APPLIED_KEY,
             c.WHY_IS_APPLIED_COUNT: WHY_APPLIED_COUNT, c.WHY_IS_APPLIED_TARGET: WHY_APPLIED_TARGET,
             c.WHY_IS_APPLIED_FOLDER: WHY_APPLIED_FOLDER}


# ── 자리 · 때 · 기록 한 줄 ─────────────────────────────────────────────────────────

def _place_word(place: str, folder: str) -> str:
    """자리를 사람 말로."""
    if place != FOLDER:
        return PLACE_NAMES.get(place, place)
    return FOLDER_PLACE.format(folder=folder)


def target_word(to: str | None) -> str:
    """옮기기의 받을 자리를 사람 말로 — 빈 것은 받은편지함."""
    return _place_word(FOLDER if to else INBOX, to or "")


def _rule_word(rule: dict[str, Any] | None) -> str:
    """규칙의 판을 사람 말로 — 앞 판 → 바꿀 판(있는 것만)."""
    rule = rule or {}
    return RULE_ARROW.join(x for x in (rule.get("before"), rule.get("after")) if x)


def when_word(at: Any) -> str:
    """적은 때를 사람 말로 — 분까지 · 없으면 「때 모름」."""
    return str(at or "")[:c.STAMP_MINUTE].replace(c.STAMP_T, c.STAMP_SPACE) or WHEN_UNKNOWN


def outcome_word(state: str, outcome: Any) -> str:
    """기록 한 줄의 결과를 사람 말로 — 잡아 둔 채면 그렇게, 모르는 결과 낱말은 적힌 그대로."""
    return LOG_HELD if state == c.ENDED_HELD else OUTCOME_WORDS.get(outcome, outcome)


def origin_word(key: tuple[str, str] | None) -> str:
    """원래 자리 열쇠를 사람 말로 — None 은 휴지통."""
    return TRASH_PLACE if key is None else _place_word(*key)


def describe(e: dict[str, Any], counts: Sequence[tuple[tuple[str, str] | None, int]]) -> str:
    """기록 한 줄이 한 일 — 메일 번호 없이. 메일 바꿈은 원래 자리마다의 수(`counts` — 셈이 낸다)를 옮긴다."""
    kind = e.get("kind", "")
    word = KIND_WORDS.get(kind, kind)
    if kind in MAIL_KINDS:
        origin = LIST_SEP.join(DESCRIBE_ORIGIN.format(place=origin_word(k), count=v) for k, v in counts)
        target = DESCRIBE_TARGET.format(target=target_word(e.get("to"))) if kind == MOVE else ""
        return DESCRIBE_MAILS.format(word=word, count=sum(v for _, v in counts), origin=origin, target=target)
    if kind in FOLDER_KINDS:
        return DESCRIBE_FOLDER.format(word=word, path=e.get('path', ''))
    rule = e.get("rule") or {}
    return DESCRIBE_RULE.format(word=word, rule=rule.get('after') or rule.get('before') or '')


def chain_word(root: int, tiers: Sequence[Sequence[tuple[int, str, str]]]) -> str:
    """되돌림의 사슬 — 「5 → 8(되돌림) → 9(다시 함)」. 단마다 (기록 번호, 고리, 맺은 꼴). 사슬이 없으면 빈 글."""
    if not tiers:
        return ""
    parts = [str(root)] + [LIST_SEP.join(CHAIN_LINK.format(id=i, word=LINK_WORDS[link] + LINK_TAILS[state]) for i, link, state in ids)
                           for ids in tiers]
    return LOG_CHAIN.format(chain=CHAIN_ARROW.join(parts))


def row_line(e: dict[str, Any], state: str, counts: Sequence[tuple[tuple[str, str] | None, int]], chain: str = "") -> str:
    """기록 한 줄 — 번호 · 때 · 한 일 · 결과(맺은 꼴 `state` 가 잡아 둔 채면 그렇게) · 되돌림의 사슬."""
    return LOG_ROW.format(id=e["id"], when=when_word(e.get("at")), what=describe(e, counts), outcome=outcome_word(state, e.get("outcome")),
                          chain=chain)


# ── 명령마다의 줄 ─────────────────────────────────────────────────────────────

def shown_lines(n: int, piece: dict[str, Any], counts: Sequence[tuple[tuple[str, str] | None, int]], body: Sequence[str], plan: int,
                dropped: int) -> list[str]:
    """`show` 가 조각을 적은 뒤 보일 줄 — 조각의 머리 · 메일 줄 · 다음 걸음(앞 안을 걷었으면 그 수도)."""
    reset = SHOWN_RESET.format(count=dropped) if dropped else ""
    return [SHOWN_ROW.format(n=n, what=describe(piece, counts)), *body, SHOWN.format(plan=plan, n=n, reset=reset)]


def shown_list_lines(rows: Sequence[tuple[str, dict[str, Any], Sequence[tuple[tuple[str, str] | None, int]], Sequence[str], bool]],
                     first: Any, last: Any) -> list[str]:
    """`shown` 이 낼 줄 — 조각마다 머리와 보인 메일 줄(줄이 빠진 메일 조각은 그 말), 끝에 조각 수와 처음 · 마지막 적은 때(셈이 고른 것)."""
    out: list[str] = []
    for n, piece, counts, body, no_body in rows:
        out.append(SHOWN_ROW.format(n=n, what=describe(piece, counts)))
        out += list(body) if body else [SHOWN_NO_BODY] if no_body else []
    out.append(SHOWN_LIST.format(count=len(rows), first=when_word(first), last=when_word(last)))
    return out


def difference_lines(n: int, facts: Sequence[tuple[str, Any, Any]]) -> list[str]:
    """보인 조각과 다른 점의 줄 — (다른 점, 보인 것, 지금)마다 한 줄, 앞뒤로 멈춘 까닭과 다음 걸음."""
    out = [SHOWN_DIFF.format(n=n)]
    for what, was, now in facts:
        if what == c.DIFF_IS_KIND:
            out.append(DIFF_FORMS[what].format(was=KIND_WORDS.get(was, was), now=KIND_WORDS[now]))
        elif what == c.DIFF_IS_TARGET:
            out.append(DIFF_FORMS[what].format(was=target_word(was), now=target_word(now)))
        elif what in (c.DIFF_IS_ADDED, c.DIFF_IS_GONE):
            out.append(DIFF_FORMS[what].format(count=len(now), unids=UNID_SEP.join(now)))
        elif what == c.DIFF_IS_MOVED:
            out.append(DIFF_FORMS[what].format(count=len(now), moves=LIST_SEP.join(
                DIFF_MOVE.format(unid=u, was=_place_word(*a), now=_place_word(*b)) for u, a, b in now)))
        elif what == c.DIFF_IS_PATH:
            out.append(DIFF_FORMS[what].format(was=was, now=now))
        else:
            out.append(DIFF_FORMS[what].format(was=_rule_word(was), now=_rule_word(now)))
    return [*out, SHOWN_DIFF_TAIL]


def held_lines(kind: str, mail_count: int | None, shown: int | None, apply_cmd: str | None, key: str) -> list[str]:
    """`hold` 가 잡은 뒤 보일 줄 — 잡았다는 말과 다음 걸음, 실행 줄을 지었으면 그 줄."""
    n = HELD_COUNT.format(count=mail_count) if mail_count is not None else ""
    said = HELD if shown is None else HELD_SHOWN
    how = HOW_LINE if apply_cmd is not None else HOW_SAME.format(key=key)
    lines = [said.format(kind=KIND_WORDS[kind], n=n, piece=shown, how=how)]
    if apply_cmd is not None:
        lines.append(APPLY_ROW.format(cmd=apply_cmd))
    return lines


def wrote_line(entry_id: int, entry: dict[str, Any], counts: Sequence[tuple[tuple[str, str] | None, int]], outcome: str) -> str:
    """`done` 이 기록으로 맺은 뒤의 말 — 결과를 모르면 메일함에서 볼 걸음을 붙인다."""
    said = WROTE.format(id=entry_id, what=describe(entry, counts), outcome=OUTCOME_WORDS[outcome])
    return said + (WROTE_UNKNOWN_HINT if outcome == UNKNOWN else "")


def plans_lines(blocks: Sequence[dict[str, Any]]) -> list[str]:
    """`plans` 가 낼 줄 — 안마다 머리와 남은 조각(까닭 · 미리 보기 명령 · 그 뒤 뺀 메일), 끝에 다음 걸음. 남은 안이 없으면 그 말."""
    out: list[str] = []
    for block in blocks:
        out.append(PLANS_HEAD.format(plan=block["plan"], when=when_word(block["first"]), total=block["total"],
                                     left=len(block["pieces"])))
        for n, rest, counts, cut, cmd in block["pieces"]:
            why = PLANS_WHY.format(why=rest["why"]) if rest.get("why") else ""
            hand = PLANS_HAND.format(cmd=cmd) if cmd is not None else ""
            out.append(PLANS_PIECE.format(n=n, what=describe(rest, counts), why=why, cmd=hand))
            cut_ids, cut_count = cut
            if cut_ids:
                out.append(PLANS_LATER.format(ids=LIST_SEP.join(map(str, cut_ids)), count=cut_count))
    return [*out, PLANS_FOOT] if out else [PLANS_EMPTY]


def none_logged(rows: Sequence[Any]) -> list[str]:
    """기록이 하나도 없다는 말 한 줄 — 기록이 있으면 빈 목록."""
    return [] if rows else [LOG_EMPTY]


def bad_lines(bad: Sequence[int]) -> list[str]:
    """기록 파일에서 못 읽어 건너뛴 줄마다 한 줄."""
    return [LOG_BAD.format(n=n) for n in bad]


def mail_lines(e: dict[str, Any], groups: Sequence[tuple[tuple[str, str] | None, Sequence[str]]],
               later: Sequence[tuple[dict[str, Any], Sequence[str], str]]) -> list[str]:
    """기록 하나가 바꾼 메일 줄 — 원래 자리 → 간 자리마다(자리 None 은 휴지통) · 실행 손이 안 돌아왔다고 댄 수 · 뒤의 기록이 다시 바꾼 메일.
    바꾼 메일이 없으면(폴더 · 규칙) 빈 목록."""
    if not groups:
        return []
    kind = e.get("kind")
    dst = {MOVE: target_word(e.get("to")), TRASH: TRASH_PLACE, RESTORE: RESTORED_PLACE}[kind]
    out = [MAILS_GROUP.format(src=TRASH_PLACE if src is None else _place_word(*src), dst=dst, count=len(unids), unids=UNID_SEP.join(unids))
           for src, unids in groups]
    if e.get("elsewhere"):
        out.append(MAILS_ELSEWHERE.format(n=e["elsewhere"]))
    for r, touched, state in later:
        out.append(MAILS_LATER.format(id=r["id"], what=KIND_WORDS.get(r.get("kind", ""), ""), outcome=outcome_word(state, r.get("outcome")),
                                      count=len(touched),
                                      unids=UNID_SEP.join(touched)))
    return out


def undo_notes(e: dict[str, Any], state: str, done: Sequence[int], maybe: Sequence[int], pending: Sequence[int]) -> list[str]:
    """되돌리기 전에 알릴 형편 — 이 바꿈이 잡아 둔 채인가(맺은 꼴 `state`) · 되돌린 · 결과를 모르는 · 잡아 둔 되돌림 기록."""
    return ([UNDO_OF_HELD.format(id=e["id"])] if state == c.ENDED_HELD else []) \
        + ([UNDONE_BY.format(ids=LIST_SEP.join(map(str, done)))] if done else []) \
        + ([UNDONE_MAYBE.format(ids=LIST_SEP.join(map(str, maybe)))] if maybe else []) \
        + ([UNDONE_HELD.format(ids=LIST_SEP.join(map(str, pending)))] if pending else [])


def undo_step_line(step: str, values: dict[str, Any]) -> str:
    """되돌리는 차례의 한 걸음을 사람 말로 — 걸음의 이름으로 틀을 고르고 값(자리는 사람 말로 · 잡을 명령은 그 표지로)을 채운다."""
    place = values.get("place")
    words = {**values, "place": _place_word(place, values.get("folder", "")) if place is not None else "",
             "unids": UNID_SEP.join(values.get("unids", ())), "count": len(values.get("unids", ())),
             "hold": HOLD_STEP.format(kind=values.get("hold_kind", ""), id=values.get("entry_id", ""))}
    return STEP_FORMS[step].format(**words)


def why_word(stop: c.Why) -> str:
    """멈춘 까닭을 사람 말로 — 까닭의 이름으로 틀을 고르고 그 값(메일 번호가 아닌 것은 앞의 몇 개만 이어서)을 채운다."""
    words = {**stop.values, "bad": BAD_SEP.join(stop.values.get("bad", ())[:BAD_MOST])}
    return WHY_FORMS[stop.reason].format(**words)


def not_shown(stop: c.Refused) -> list[str]:
    """조각을 안 적은 까닭과 다음 걸음."""
    return [NOT_SHOWN.format(why=why_word(stop))]


def not_held(stop: c.Refused) -> list[str]:
    """바꿈을 안 잡은 까닭과 다음 걸음."""
    return [NOT_HELD.format(why=why_word(stop))]


def shown_none(n: int) -> list[str]:
    """그 번호의 조각을 보인 기록이 없어 안 잡았다는 말."""
    return [SHOWN_NONE.format(n=n)]


def superseded(entry_id: int) -> list[str]:
    """앞의 잡아 둔 바꿈을 「결과 모름」 기록으로 옮겼다는 말."""
    return [HELD_SUPERSEDED.format(id=entry_id)]


def mismatch(stop: c.Mismatch) -> list[str]:
    """실행의 글이 잡아 둔 바꿈과 달라 안 적었다는 말과 다음 걸음."""
    return [MISMATCH.format(why=why_word(stop))]


def dropped(hold: dict[str, Any], counts: Sequence[tuple[tuple[str, str] | None, int]]) -> list[str]:
    """잡아 둔 바꿈을 기록 없이 놓았다는 말."""
    return [DROPPED.format(what=describe(hold, counts))]


def piece_from(text: str) -> str:
    """조각 번호가 첫 번호보다 작아 못 받는다는 말."""
    return PIECE_FROM.format(first=c.FIRST_PIECE, text=text)


def no_entry(entry_id: int) -> str:
    """그런 기록 번호가 없다는 말."""
    return NO_ENTRY.format(id=entry_id)


def mails_head(path: Any) -> str:
    """바꾼 메일 보기의 머리 — 기록 파일의 자리."""
    return MAILS_HEAD.format(path=path)
