"""기록 손의 이름 붙은 값 — 사용자 폴더 · 기록 파일 이름 · 종류 · 자리 · 결과 · 종료 값 · 셈과 말이 주고받는 상태의 이름 · 멈춘 까닭의 이름과 그것을 드는 예외 둘. 아무것도 안 싣는다."""

from __future__ import annotations

# 사용자 폴더 — 원본은 스킬 mailbox-scan 의 `scripts/scan_const.py` 「자리」다. 스킬은 서로의 코드를 싣지 않아 옮겨 든다 — 바꾸면 함께 바꾼다
HOME_ENV = "MAIL_SECRETARY_HOME"         # 개발 · 검사가 사용자 폴더를 바꿀 때만 준다
HOME_NAME = "mail-secretary"             # %LOCALAPPDATA% 아래의 사용자 폴더 이름
# 기록 파일 넷 — 이름과 칸은 메일함 스캔이 「비서가 한 일」을 가르려고 읽는다(그 스킬 `scan_const.py` 의 TIDY_*)
LOG_FILE = "mailbox-tidy-log.jsonl"
HELD_FILE = "mailbox-tidy-held.json"
SHOWN_FILE = "mailbox-tidy-shown.json"
PLANS_FILE = "mailbox-tidy-plans.jsonl"
ATOMIC_SUFFIX = ".tmp"                   # 바꿔 끼우는 쓰기의 임시 파일 — 같은 자리에 이 꼬리를 붙인다
STAMP_MINUTE = 16                        # 적은 때(초까지의 ISO)의 앞 열여섯 자 — 사람에게 분까지 보인다
STAMP_T, STAMP_SPACE = "T", " "          # ISO 의 날 · 시각 가름 — 보일 때는 빈칸으로
FIRST_PIECE = 1                          # 이 번호의 조각을 적으면 새 안이다 — 앞서 적은 조각을 걷는다
PLANS_MOST = 5                           # plans 가 기본으로 보일 안의 수 — 안 바꾼 조각이 남은 안만 센다
LOG_MOST = 20                            # log 가 기본으로 보일 기록의 수

EXIT_OK, EXIT_FAILED = 0, 1                 # 틀린 인자는 argparse 가 2 로 나간다

# 이 스킬의 명령 — 스크립트 이름 · 하위 명령 아홉 · 되돌리는 기록 번호의 인자. 입구(`journal.py` 의 `parser` · `main`)와 다음 걸음의
# 명령 줄(`hand_line.py`)이 이 이름을 함께 쓴다
JOURNAL_SCRIPT = "journal.py"
CMD_SHOW, CMD_SHOWN, CMD_PLANS, CMD_HOLD, CMD_DONE = "show", "shown", "plans", "hold", "done"
CMD_DROP, CMD_LOG, CMD_MAILS, CMD_UNDO = "drop", "log", "mails", "undo"
UNDOES_FLAG = "--undoes"

# 종류 · 결과 — 사본이 메일함 스캔 `scan_diff.py` 에 있다
MOVE, TRASH, RESTORE = "move", "trash", "restore"
FOLDER_CREATE, FOLDER_DELETE = "folder-create", "folder-delete"
RULE_ADD, RULE_EDIT, RULE_DELETE = "rule-add", "rule-edit", "rule-delete"
KINDS = (MOVE, TRASH, RESTORE, FOLDER_CREATE, FOLDER_DELETE, RULE_ADD, RULE_EDIT, RULE_DELETE)
MAIL_KINDS = (MOVE, TRASH, RESTORE)
FOLDER_KINDS = (FOLDER_CREATE, FOLDER_DELETE)
DONE, UNKNOWN = "done", "unknown"
HELD_KEY = "held"                        # 기록 보기에 덧붙인 잡아 둔 바꿈의 표지 — 파일에는 안 적힌다

# 자리 — 메일이 선 곳
INBOX, SENT, DRAFTS, FOLDER = "inbox", "sent", "drafts", "folder"
# 회사 메일 스킬이 자리를 적는 낱말(그 스킬 `scripts/mail.py` 의 미리 보기 · 실행이 찍는 꼴) — 사람에게 자리를 말할 때도 이 낱말이다
PLACE_WORDS = {"받은편지함": INBOX, "보낸편지함": SENT, "임시보관함": DRAFTS}
PLACE_NAMES = {place: word for word, place in PLACE_WORDS.items()}
FOLDER_SEP = "\\"                        # 폴더 경로의 부모 · 자식 가름(그 스킬 `inbox.py` 의 FOLDER_SEPARATOR)


# ── 거절 · 어긋남의 까닭 — 읽는 쪽(`hand_text.py` · `journal_view.py` · `journal.py`)이 이름과 값으로 올리고 말(`journal_words.py`)이 그 이름의 문장을 고른다 ──
# 미리 보기 · 받은 인자를 못 받는 까닭(`Refused`)
WHY_IS_HEAD, WHY_IS_KEY, WHY_IS_COUNT, WHY_IS_GIVEN = "head", "key", "count", "given"
WHY_IS_PLACE, WHY_IS_TAIL, WHY_IS_ORDER, WHY_IS_UNID = "place", "tail", "order", "unid"
WHY_IS_TARGET, WHY_IS_TARGET_MISSING, WHY_IS_RULE_LINES, WHY_IS_FOR_MAILS = "target", "target-missing", "rule-lines", "for-mails"
WHY_IS_PIECE_NEXT = "piece-next"
# 실행의 「됐다」 줄이 잡아 둔 바꿈과 다른 까닭(`Mismatch`)
WHY_IS_APPLIED_FORM, WHY_IS_APPLIED_KEY, WHY_IS_APPLIED_COUNT = "applied-form", "applied-key", "applied-count"
WHY_IS_APPLIED_TARGET, WHY_IS_APPLIED_FOLDER = "applied-target", "applied-folder"


class Why(Exception):
    """까닭의 이름(`reason` — 위 WHY_IS_*)과 그 값(`values`)을 드는 멈춤 — 문장은 들지 않는다."""

    def __init__(self, reason: str, **values: object) -> None:
        super().__init__(reason)
        self.reason = reason
        self.values = values


class Refused(Why):
    """미리 보기의 꼴이나 받은 인자가 이 손이 아는 꼴이 아니다 — 잡지도 적지도 않는다."""


class Mismatch(Why):
    """실행의 「됐다」 줄이 잡아 둔 바꿈과 다르다 — 적지 않고 잡아 둔 것을 그대로 둔다."""


# ── 셈(`journal_view.py`)이 내고 말(`journal_words.py`)이 받는 상태의 이름 ──
# 잡아 둔 바꿈이 새 미리 보기 앞에 선 꼴 — 없다 · 실행 안 된 같은 미리 보기 · 실행했는지 모른다
PRIOR_NONE, PRIOR_TWIN, PRIOR_UNKNOWN = "none", "twin", "unknown"
# 보인 조각과 다시 받은 미리 보기가 다른 점
DIFF_IS_KIND, DIFF_IS_TARGET, DIFF_IS_ADDED, DIFF_IS_GONE = "kind", "target", "added", "gone"
DIFF_IS_MOVED, DIFF_IS_PATH, DIFF_IS_RULE = "moved", "path", "rule"
# 되돌리는 차례의 걸음
STEP_IS_MOVE_BACK, STEP_IS_NO_HAND, STEP_IS_RESTORE, STEP_IS_AFTER_RESTORE = "move-back", "no-hand", "restore", "after-restore"
STEP_IS_RESTORE_UNKNOWN, STEP_IS_RETRASH = "restore-unknown", "retrash"
STEP_IS_FOLDER_DROP, STEP_IS_FOLDER_MAKE = "folder-drop", "folder-make"
STEP_IS_RULE_DROP, STEP_IS_RULE_DROP_NOKEY, STEP_IS_RULE_BACK, STEP_IS_RULE_BACK_NOKEY = "rule-drop", "rule-drop-nokey", "rule-back", "rule-back-nokey"
STEP_IS_RULE_READD = "rule-readd"
# 되돌림 사슬의 고리 — 되돌림 · 다시 함
LINK_IS_UNDO, LINK_IS_REDO = "undo", "redo"
# 기록 한 줄이 맺은 꼴 — 됐다 · 결과 모름 · 잡아 둔 채(기록 보기에 덧붙인 잡아 둔 바꿈). `journal_view.ending` 하나가 가른다
ENDED_DONE, ENDED_UNKNOWN, ENDED_HELD = "done", "unknown", "held"
