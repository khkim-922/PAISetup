"""메일함 스캔의 이름 붙은 값 — 자리 · 파일 이름 · 상한 · 주기. 스캔 스크립트가 다 여기서 읽는다.

값마다 곁주석이 까닭을 든다. 한 판의 요청 수 · 걸린 시간에 기대는 값은 회사 판에서 다시 맞춘다.
"""

from __future__ import annotations

import pathlib

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent   # 이 스킬의 스크립트 자리
SCAN_ENTRY = "scan.py"                                  # 명령 입구 — 일일 보고의 시계 · 대화가 이 파일을 부른다
SCAN_PY = SCRIPT_DIR / SCAN_ENTRY                       # 이 스캔의 입구 — 옛 판이 건 작업이 이 스캔을 부르나를 대는 자리

# ── 자리 — 사용자 폴더. 메일 비서 스킬(스캔 · 정리 · 업무 파악 · 일일 보고)이 함께 쓰는 자리이고 원본은 여기다 ──────────
# 바꾸면 사본 둘(mailbox-tidy `scripts/journal_const.py` · mailbox-work `scripts/work.py` 의 같은 이름)을 함께 바꾼다 — 서로의 코드를 안 싣는다
HOME_ENV = "MAIL_SECRETARY_HOME"         # 개발 · 검사가 사용자 폴더를 바꿀 때만 준다
HOME_NAME = "mail-secretary"             # %LOCALAPPDATA% 아래의 사용자 폴더 이름
SCAN_DIR = "mailbox-scan"                # 사용자 폴더 안의 스캔 자리 — 이 스킬의 파일은 다 여기 산다
STATE_FILE = "state.json"                # 메일함의 지금 모습 한 장 · 이음점 · 세션 상태 — 새 파일에 다 쓴 뒤 바꿔 끼운다
EVENTS_FILE = "events.jsonl"             # 새 메일 · 바뀜 — 덧붙이기만
RUNS_FILE = "runs.jsonl"                 # 판마다의 값(때 · 손 부르기 · 줄 · 초 · 끝 · 전체를 다 본 판의 받은편지함 셈) — 덧붙이기만
PENDING_FILE = "pending.json"            # 다 못 본 지금 모습 판의 다 본 상자들 — 다음 판이 잇는다
LOCK_FILE = "scan.lock"                  # 도는 판 하나 — 그 판의 열쇠와 시작 시각
TASK_XML_FILE = "mailbox-scan-task.xml"  # 옛 판이 작업 스케줄러에 건 정의의 사본 — 거둘 때 함께 걷는다
FORMAT = 1                               # 스캔 파일의 꼴 번호 — 칸을 바꾸면 올린다(읽는 쪽이 모르는 판을 안 읽는다)
STATUS_FORMAT = 1                        # `status --json` 의 꼴 번호 — 칸의 이름이나 뜻을 바꾸면 올린다(읽는 프로그램이 모르는 꼴을 안 믿게)

# 판의 갈래와 끝 — 판 기록(`runs.jsonl`)과 지금 모습의 `last_run` 에 적힌다. 쓰는 쪽(scan.py)과 읽는 쪽(reader.py)이 이 이름으로 가른다
MODE_FULL, MODE_NEW = "full", "new"
RUN_DONE, RUN_FIRST, RUN_PARTIAL, RUN_SESSION, RUN_BUSY = "done", "first", "partial", "session", "busy"
RUN_HAND_MISSING, RUN_HAND_OLD, RUN_HAND_ERROR, RUN_SHAPE, RUN_SWAP = "hand-missing", "hand-old", "hand-error", "shape", "swap-failed"
# 멈춘 판의 다음 걸음 — 판 끝 한 줄(scan_words) · 읽는 명령의 상태 줄(reader) · 거는 명령(scan_setup)이 저마다의 말 틀에 끼운다
NEXT_HAND_MISSING = "--hand 로 company-mail 의 scripts/mail.py 를 준다"
NEXT_HAND_OLD = "PAISetup 을 다시 깔아 손을 새 판으로 올린다"
RUN_UNREAD = "unreadable"                # 판이 기대는 파일(지금 모습 · 정리 스킬의 잡아 둔 바꿈)이 있는데 못 읽어 아무것도 안 쓰고 멈췄다

# 메일함 정리 스킬의 기록 — 비서가 바꾼 것을 「비서가 한 일」로 가르려고 읽기만 한다. 꼴의 원본은 스킬 `mailbox-tidy` 의 `scripts/journal_const.py`(이름)와 `scripts/journal_store.py`(쓰는 손)
TIDY_LOG_FILE = "mailbox-tidy-log.jsonl"
TIDY_HELD_FILE = "mailbox-tidy-held.json"

# ── 회사 메일 손 — 명령으로 부른다(손의 코드를 싣지 않는다 — 손이 바뀌어도 이 스킬이 안 깨지게) ──────────────────────────────────────────
# 스킬 뿌리를 찾는 차례 — 환경변수가 있으면 그 뿌리 하나, 없으면 설치가 스킬을 놓는 도구 홈을 차례로
SKILLS_ENV = "SECRETARY_SKILLS"
SKILL_HOMES = ((".claude", "skills"), (".agents", "skills"), (".gemini", "config", "skills"))
# 회사 메일 손의 자리 · 종료 값 · 시한 · 로그인이 사는 스킬 · 세션 답 낱말 · 다음 걸음 — 일일 보고의 시계와 같은 사실이라 곁의 `hand_facts`
# (원본)가 든다
from hand_facts import (HAND_EXIT_CONFIG, HAND_EXIT_FAIL, HAND_EXIT_OK, HAND_EXIT_SESSION, HAND_SCRIPT, HAND_SKILL,  # noqa: E402,F401
                        HAND_TIMEOUT_S, NEXT_LOGIN, SESSION_LIVE, SESSION_LOST, SESSION_SKILL)
HAND_ENV = "MAILBOX_SCAN_HAND"           # 손의 자리를 굳히는 환경변수 — 예약 실행은 명령줄의 --hand 로 준다
# 보낸 분의 신원 — 주소록 스킬(company-directory)의 신원 명령을 명령으로 부른다(그 코드를 싣지 않는다). 찾는 차례는 `IDENTITY_ENV` → 회사 메일
# 손과 같은 스킬 뿌리. 다시 묻는 날 · 한 부름이 서버에 묻는 주소의 위는 그 명령이 든다 — 스캔은 판마다 주소를 다 주고 그 답을 받아 적는다
IDENTITY_SKILL = "company-directory"
IDENTITY_SCRIPT = ("scripts", "identity.py")
IDENTITY_ENV = "MAILBOX_SCAN_IDENTITY"
IDENTITY_FORMAT = 1      # 신원 명령 답의 꼴 번호 — 그 명령의 `IDENTITY_FORMAT` 과 같아야 읽는다(다르면 신원을 안 붙이고 판 기록에 적는다). 답의
                         # 상태 낱말(섰다 · 여럿 · 없음 · 모름)은 그 꼴의 일부다 — 원본은 그 스킬 references/DESIGN.md 「신원 한 줄의 꼴」
IDENTITY_TIMEOUT_S = 120 # 신원 명령 한 번의 시한 — 넘으면 이번 판은 신원을 안 고치고 판은 그대로 맺는다
IDENTITY_PULL_TIMEOUT_S = 150   # 미리 받기(`pull --unattended` — 한 번에 한 회사, 가장 큰 회사가 1 분 안쪽)의 시한 — 메일함 전체 판에서만 부른다
UNKNOWN_IDENTITY = "모름"   # 신원 명령이 아직 못 지은 신원의 상태 — 다음 판이 다시 묻는다

# 세션 파일의 자리 — 받는 손과 같은 차례(`MAILBOX_COOKIES` → 형제 스킬 ep-login 의 받는 손 곁 `places.json` 의 기본 자리). 그 파일이
# 끊긴 뒤 새로 쓰였나로 「대화에서 EP 로그인을 했다」를 안다. 남의 코드를 안 싣고 그 데이터 파일만 읽는다
SESSION_FILE_ENV = "MAILBOX_COOKIES"
SESSION_HAND_ENV = "EP_SESSION_HAND"
SESSION_HAND_SCRIPT = ("scripts", "edge_session.js")
SESSION_PLACES = "places.json"
SESSION_PLACES_KEY = "session_file"

# 판의 끝이 대는 사내 세션의 답 — 손이 답한 판은 살았다, 세션 없음으로 멈춘 판은 없다. 표에 없는 끝(판이 없었다 · 손이 못 답했다)은 답이 없다.
# `status --json` 의 마지막 판의 세션 답(정한 시각의 보고를 띄우는 프로그램이 읽는다)이 이 표로 가른다
RUN_SESSION_ANSWER = {RUN_DONE: SESSION_LIVE, RUN_FIRST: SESSION_LIVE, RUN_PARTIAL: SESSION_LIVE, RUN_SESSION: SESSION_LOST}
PAGE = 1000              # 목록 한 번에 청하는 줄 — 서버가 보기의 count 를 이 수에서 자른다(손 mail.py 의 `DEEP_PAGE` 와 같은 값)
PAGES_MOST = 200         # 상자 하나에서 청하는 쪽의 안전 상한 — 서버가 끝없이 새 줄을 주는 고장에서 멈춘다
SINCE_PAGES_MOST = 60    # 「이 시각 뒤」 목록을 --start 로 잇는 쪽의 안전 상한 — 같은 고장에서 멈춘다(한 쪽이 답의 크기만큼 담아 쪽 수가 적다)

# ── 주기 · 상한 — 회사에서 한 판의 값을 재면 고친다 ───────────────────────────────────────────
FULL_EVERY_MIN = 120     # 메일함 전체를 다시 보는 주기(분) — 상자마다 손을 두 번 넘게 불러 무겁다. 아래 PENDING_MAX_MIN 보다 짧아야 다 못 본 판을
                         # 다음 전체 판이 잇는다(회사에서 한 판의 값을 재기 전의 기본값)
RUN_BUDGET_S = 15 * 60   # 한 판이 손을 부르는 시간의 상한 — 넘으면 다 본 상자까지 적고 다음 판이 잇는다
LOCK_STALE_S = RUN_BUDGET_S + HAND_TIMEOUT_S + IDENTITY_TIMEOUT_S + IDENTITY_PULL_TIMEOUT_S + 60   # 이보다 오래된 잠금은 잠 · 꺼짐 · 멈춘 판이
                         # 남긴 것이다 — 풀고 돈다. 판은 손의 상한 뒤에 신원 명령 둘을 잠금을 쥔 채 부른다
LOCK_WAIT_POLL_S = 2     # `run --wait` 가 도는 판의 잠금을 다시 쥐어 보는 사이(초) — 판은 몇 분이 들어 이 사이는 조금 늦음으로만 보인다. 사이마다
                         # 잠들어 기다려 CPU 를 안 쓴다
PENDING_MAX_MIN = 180    # 다 못 본 지금 모습 판을 잇는 기한 — 넘은 상자 그림은 너무 낡아 버리고 처음부터 본다. 전체 주기(`--full-every`)는
                         # 이보다 짧아야 한다 — 같거나 길면 덜 본 판의 상자가 늘 버려져 큰 메일함은 끝내 다 못 본다(scan.py 가 거절한다)
BACKOFF_FIRST_MIN = 15   # 세션이 끊긴 뒤 첫 다시 두드림까지 — 그 뒤로 두 배씩
BACKOFF_MAX_MIN = 240    # 다시 두드리는 간격의 상한 — 밤새 SSO 를 몇 분마다 두드리지 않게
RETAIN_DAYS = 14         # 새 메일 · 바뀜 · 판의 기록을 두는 날 — 일일 보고(하루 · 주말)와 업무 파악 갱신(한 주)이 읽는 폭보다 넉넉히

# ── 정리 신호의 재료 — `reader.py signals` 가 판 기록에서 받은편지함의 흐름을 짚는 때(시간 전). 셈만 내고 가르지 않는다 ───────────
SIGNAL_SPANS_H = (24, 7 * 24)   # 하루쯤 전 · 이레쯤 전 — 판 기록(RETAIN_DAYS)이 가장 긴 것보다 넉넉해야 닿는다
GONE_KEEP_DAYS = 30      # 사라진 메일을 기억하는 날 — 그 안에 다시 나타나면 「새 메일」이 아니라 「다시 나타남」이다
COMPACT_EVERY_H = 24     # 오래된 기록을 접는 주기
REPLACE_TRIES = 25       # 지금 모습을 바꿔 끼울 때 읽는 쪽이 파일을 쥐고 있으면(윈도) 다시 해 보는 수
REPLACE_WAIT_S = 0.2

SEOUL_OFFSET_H = 9       # 메일함의 시각(`xdate`)은 서울 시각이다(손 mail.py 도 그렇게 읽는다) — 서울은 일광 절약이 없다
MAIL_DATE = "%Y-%m-%d %H:%M:%S"   # 손이 받은편지함 · 보낸편지함 줄에 찍는 메일의 때 꼴(초까지) — 쌓을 때의 꼴도 이것이다
MAIL_DATE_MINUTE = "%Y-%m-%d %H:%M"   # 손이 폴더 줄에 찍는 꼴(분까지) — 쌓을 때 「:00」 을 붙여 위 꼴로 맞춘다
