"""메일함 스캔의 이름 붙은 값 — 자리 · 파일 이름 · 상한 · 주기. 스캔 스크립트가 다 여기서 읽는다.

값마다 곁주석이 까닭을 든다. 한 판의 요청 수 · 걸린 시간에 기대는 값은 회사 판에서 다시 맞춘다.
"""

from __future__ import annotations

# ── 자리 — 사용자 폴더. 메일 비서 스킬(스캔 · 정리 · 업무 파악 · 일일 보고)이 함께 쓰는 자리이고 원본은 여기다 ──────────
# 바꾸면 사본 둘(mailbox-tidy `scripts/journal.py` · mailbox-work `scripts/work.py` 의 같은 이름)을 함께 바꾼다 — 서로의 코드를 안 싣는다
HOME_ENV = "MAIL_SECRETARY_HOME"         # 개발 · 검사가 사용자 폴더를 바꿀 때만 준다
HOME_NAME = "mail-secretary"             # %LOCALAPPDATA% 아래의 사용자 폴더 이름
SCAN_DIR = "mailbox-scan"                # 사용자 폴더 안의 스캔 자리 — 이 스킬의 파일은 다 여기 산다
STATE_FILE = "state.json"                # 메일함의 지금 모습 한 장 · 이음점 · 세션 상태 — 새 파일에 다 쓴 뒤 바꿔 끼운다
EVENTS_FILE = "events.jsonl"             # 새 메일 · 바뀜 — 덧붙이기만
RUNS_FILE = "runs.jsonl"                 # 판마다의 값(때 · 손 부르기 · 줄 · 초 · 끝 · 전체를 다 본 판의 받은편지함 셈) — 덧붙이기만
PENDING_FILE = "pending.json"            # 다 못 본 지금 모습 판의 다 본 상자들 — 다음 판이 잇는다
LOCK_FILE = "scan.lock"                  # 도는 판 하나 — 그 판의 열쇠와 시작 시각
TASK_XML_FILE = "mailbox-scan-task.xml"  # 작업 스케줄러에 건 정의의 사본 — 등록할 때 쓴다
FORMAT = 1                               # 스캔 파일의 꼴 번호 — 칸을 바꾸면 올린다(읽는 쪽이 모르는 판을 안 읽는다)

# 판의 갈래와 끝 — 판 기록(`runs.jsonl`)과 지금 모습의 `last_run` 에 적힌다. 쓰는 쪽(scan.py)과 읽는 쪽(reader.py)이 이 이름으로 가른다
MODE_FULL, MODE_NEW = "full", "new"
RUN_DONE, RUN_FIRST, RUN_PARTIAL, RUN_SESSION, RUN_BUSY = "done", "first", "partial", "session", "busy"
RUN_HAND_MISSING, RUN_HAND_OLD, RUN_HAND_ERROR, RUN_SHAPE, RUN_SWAP = "hand-missing", "hand-old", "hand-error", "shape", "swap-failed"

# 메일함 정리 스킬의 기록 — 비서가 바꾼 것을 「비서가 한 일」로 가르려고 읽기만 한다. 꼴의 원본은 스킬 `mailbox-tidy` 의 `scripts/journal.py`
TIDY_LOG_FILE = "mailbox-tidy-log.jsonl"
TIDY_HELD_FILE = "mailbox-tidy-held.json"

# ── 회사 메일 손 — 명령으로 부른다(손의 코드를 싣지 않는다 — 손이 바뀌어도 이 스킬이 안 깨지게) ──────────────────────────────────────────
# 스킬 뿌리를 찾는 차례 — 환경변수가 있으면 그 뿌리 하나, 없으면 설치가 스킬을 놓는 도구 홈을 차례로
SKILLS_ENV = "SECRETARY_SKILLS"
SKILL_HOMES = ((".claude", "skills"), (".agents", "skills"), (".gemini", "config", "skills"))
HAND_SKILL = "company-mail"
HAND_SCRIPT = ("scripts", "mail.py")
HAND_ENV = "MAILBOX_SCAN_HAND"           # 손의 자리를 굳히는 환경변수 — 예약 실행은 명령줄의 --hand 로 준다
# 세션 파일의 자리 — 받는 손과 같은 차례(`MAILBOX_COOKIES` → 형제 스킬 ep-login 의 받는 손 곁 `places.json` 의 기본 자리). 그 파일이
# 끊긴 뒤 새로 쓰였나로 「대화에서 EP 로그인을 했다」를 안다. 남의 코드를 안 싣고 그 데이터 파일만 읽는다
SESSION_FILE_ENV = "MAILBOX_COOKIES"
SESSION_HAND_ENV = "EP_SESSION_HAND"
SESSION_SKILL = "ep-login"
SESSION_HAND_SCRIPT = ("scripts", "edge_session.js")
SESSION_PLACES = "places.json"
SESSION_PLACES_KEY = "session_file"

HAND_EXIT_OK, HAND_EXIT_FAIL, HAND_EXIT_CONFIG, HAND_EXIT_SESSION = 0, 1, 2, 3   # 손의 종료 값(그 손 mail.py 머리말 「무엇을 내나」)
HAND_TIMEOUT_S = 240     # 손 한 번의 시한 — 손 안의 세션 받기 시한(스킬 ep-login 의 `ep_session.py` `TIMEOUT_SECONDS`)보다 길어야 손이 제 판을 끝낸다
PAGE = 1000              # 목록 한 번에 청하는 줄 — 서버가 보기의 count 를 이 수에서 자른다(손 mail.py 의 `DEEP_PAGE` 와 같은 값)
PAGES_MOST = 200         # 상자 하나에서 청하는 쪽의 안전 상한 — 서버가 끝없이 새 줄을 주는 고장에서 멈춘다
SINCE_PAGES_MOST = 60    # 「이 시각 뒤」 목록을 --start 로 잇는 쪽의 안전 상한 — 같은 고장에서 멈춘다(한 쪽이 답의 크기만큼 담아 쪽 수가 적다)

# ── 주기 · 상한 — 회사에서 한 판의 값을 재면 고친다 ───────────────────────────────────────────
EVERY_MIN = 15           # 예약의 기본 주기(분) — 사용자가 바꾼다. 새 메일만 보는 판은 손 부르기 한두 번이다. 하루 보고와 대화가 스캔 뒤 틈을
                         # 손으로 한 번 더 읽으니 촘촘함이 보고를 낫게 하지 않는다(회사에서 한 판의 값을 재기 전의 기본값)
FULL_EVERY_MIN = 120     # 메일함 전체를 다시 보는 주기(분) — 상자마다 손을 두 번 넘게 불러 무겁다. 아래 PENDING_MAX_MIN 보다 짧아야 다 못 본 판을
                         # 다음 전체 판이 잇는다(회사에서 한 판의 값을 재기 전의 기본값)
RUN_BUDGET_S = 15 * 60   # 한 판이 손을 부르는 시간의 상한 — 넘으면 다 본 상자까지 적고 다음 판이 잇는다
LOCK_STALE_S = RUN_BUDGET_S + HAND_TIMEOUT_S + 60   # 이보다 오래된 잠금은 잠 · 꺼짐 · 멈춘 판이 남긴 것이다 — 풀고 돈다
TASK_TIME_LIMIT_MIN = 25 # 작업 스케줄러가 한 판을 끊는 시한 — 위 셋보다 길어야 스캔이 제 상한으로 먼저 멈춘다
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

# ── 정한 시각의 보고 — 스캔 판이 보고 시각표의 시각마다 일일 보고를 사람 없이 한 번씩 띄운다 ──────────────
BRIEF_FILE = "brief.json"                # 보고를 걸었나 · 보고 시각표 · 띄울 claude — `register --brief-at` · `brief --at` 이 쓰고 판이 읽는다
BRIEF_LOCK_FILE = "brief.lock"           # 스캔이 띄운 보고 하나 — 띄운 때를 적고, 그 때로 푼다(`BRIEF_LOCK_STALE_S`)
BRIEF_SETTINGS_FILE = "brief-settings.json"   # 띄울 때마다 짓는 claude 의 권한(열린 명령 · 막은 명령) — `claude --settings` 로 준다
BRIEF_PROMPT_FILE = "brief-prompt.txt"   # 띄울 때마다 짓는 부탁 글 — claude 의 표준 입력으로 준다(명령줄에 한글 · 따옴표를 안 싣는다)
BRIEF_LOG_FILE = "brief-run.log"         # 마지막으로 띄운 보고의 출력 — 띄울 때마다 새로 쓴다
BRIEF_FORMAT = 2                         # brief.json 의 꼴 번호 — 2 는 시각표(`times`). 1(시각 하나 `at`)도 읽는다 — 그 꼴로 걸어 둔 PC 가 다시 안 걸어도 돈다
BRIEF_FORMATS_READ = (1, 2)
BRIEF_AT_DEFAULT = "07:30"               # 보고 시각표의 기본(서울) — 시각 하나. 사용자가 `--brief-at` 으로 바꾸고 더한다
BRIEF_WAIT_MIN = 270                     # 시각 하나가 사내 세션을 기다리는 가장 긴 틈(분) — 그 시각부터 다음 시각까지, 다음 시각이 더 멀면 이만큼까지
                                         # 띄우고 그 뒤 그 시각은 건너뛴다. 기본 07:30 이 12:00 까지 기다리던 것과 같은 값이다 — 아침 보고가 오후에
                                         # 서지 않고, 사내 인증을 하루 내내 두드리지 않는다. 어느 시각도 그날(서울 자정)을 넘겨 기다리지 않는다
BRIEF_ROOM_MIN = 30                      # 시각마다 있어야 할 가장 짧은 틈(분) — 이보다 짧으면 거는 명령이 거절한다. 스캔은 기본 15분마다 깨어, 틈이
                                         # 이보다 짧으면 그 시각에 판이 하나도 안 돌아 날마다 조용히 안 뜬다
BRIEF_UNTIL_ENV = "MAILBOX_SCAN_BRIEF_UNTIL"   # 검사가 기다림의 끝을 서울 시각 하나로 바꿀 때만 준다(`BRIEF_WAIT_MIN` 대신) — 하루 어느 때에 돌아도
                                               # 같은 판을 재게
BRIEF_TRY_GAP_MIN = 5                    # 판이 답을 안 준 주기에 손의 session 으로 살펴보는 사이의 가장 짧은 틈(분) — 작업이 더 자주 깨워도 이보다
                                         # 촘촘히 안 묻는다. 분 단위로 잰다: 작업은 정각 분에 깨우고 프로세스가 뜨는 데 몇십 초가 들어, 초까지 재면
                                         # 5분마다의 판이 한 판씩 건너뛴다
# 스스로 로그인 — 사용자가 켠 PC 에서만, 그날 첫 시각의 보고 앞에 형제 스킬 ep-login 의 입구를 사람 없는 꼴로 하루 한 번 부른다. 뒤 시각은
# 살아 있는 세션에서만 띄운다 — 낮의 사람 없는 로그인은 사람이 일하던 EP 세션을 끊을 수 있다
LOGIN_ENTRANCE = ("scripts", "ep_login.js")   # 그 스킬의 입구 — 받아 보고, 안 서면 평소 Edge 에서 먼저 · 이어 제 창을 띄워 통합 인증으로
                                              # 세운다(명령으로만 부른다)
LOGIN_ENTRANCE_ENV = "EP_LOGIN_ENTRANCE"  # 검사가 입구를 대역으로 바꿀 때만 준다
LOGIN_ARGS = ("domino", "--unattended")   # 메일 · 일정의 세션만 · 사람이 쳐야 하는 자리(VDI · 통합 인증이 안 선 화면)에서는 입구가 기다리지 않고 4 다
LOGIN_NODE = "node"                       # 입구를 돌릴 node — PATH 에서 찾는다(회사 메일 손이 세션 손을 돌리는 것과 같은 node)
LOGIN_TIMEOUT_S = 240                     # 입구 한 번의 시한 — 입구가 사람 없는 부름의 두 걸음(평소 Edge · ep-login 창)에 저마다 쓰는 시한(1분씩)과
                                          # 창 · 포트가 서는 틈보다 넉넉히. 넘기면 입구가 끝말 없이 끊겨 status 가 까닭을 못 댄다
LOGIN_SAID_CHARS = 200                    # status 가 옮겨 보이는 입구의 끝말 글자 수
BRIEF_LOCK_STALE_S = 60 * 60             # 띄운 보고가 이보다 오래 안 끝났으면 멈춘 것으로 본다(회사에서 한 판의 값을 재기 전의 기본값)
BRIEF_MADE = "brief-{date}-*.md"         # 그날 보고 글 — 사용자 폴더에 일일 보고의 손이 남긴다(원본은 스킬 daily-brief 의 scripts/window.py
                                         # `FILE_NAME` — 이름은 지은 때의 PC 시계다. 회사 PC 는 서울 시계라 서울 날짜로 찾는다)
BRIEF_SKILL = "daily-brief"              # 이 스킬과 같은 스킬 뿌리에 나란히 선다
BRIEF_WINDOW = ("scripts", "window.py")  # 보고 창을 짓고 띄우는 손 — 사람 없는 실행도 창을 띄워 둔다
BRIEF_TICKS = ("scripts", "ticks.py")    # 보고 창에서 누르신 것을 거두는 손 — 띄운 보고가 업무 파악보다 먼저 부르고, 판은 그 창에서 고르신
                                         # 보고 시각만 묻는다(`--times` · 열린 창이 없으면 아무것도 안 연다)
BRIEF_TIMES_TIMEOUT_S = 20               # 판이 보고 창의 시각을 묻는 손 한 번의 시한 — 그 손은 이 PC 의 디버깅 포트만 짧게 부른다
BRIEF_PRESSES_WITHIN_S = 360             # 판이 보고 창의 「일정에 넣기」 누름을 거두는 데 쓰는 시간 — 그 손은 이 안에 일정 손의 시한이 다 드는 넣기만
                                         # 시작하고 남은 누름은 다음 판에 둔다. 판 전체의 시한(TASK_TIME_LIMIT_MIN)을 넘기지 않게 짧게 둔다
BRIEF_PRESSES_TIMEOUT_S = BRIEF_PRESSES_WITHIN_S + 60   # 그 손 한 번의 시한 — 넣기 도중에 끊으면 들었는지 모르는 끝이 남아 넉넉히 둔다
# 그 손을 띄우기 전에 로그인 Edge 의 디버깅 포트가 받나만 본다 — 이름과 기본값의 원본은 스킬 daily-brief 의 `window.py`(EDGE_HOST ·
# EDGE_PORT_DEFAULT · 환경변수 EDGE_DEBUG_PORT · 쉼표로 여럿이면 첫 것). 서로의 코드를 안 실어 옮겨 든다 — 바꾸면 함께 바꾼다
EDGE_HOST = "127.0.0.1"
EDGE_PORT_ENV = "EDGE_DEBUG_PORT"
EDGE_PORT_DEFAULT = 9222
EDGE_PROBE_S = 0.5
CALENDAR_SKILL = "company-calendar"      # 회사 메일 손과 같은 스킬 뿌리에 나란히 선다
CALENDAR_SCRIPT = ("scripts", "company_calendar.py")
MEETING_SKILL = "company-meeting-room"   # 회의실 예약 손 — 같은 스킬 뿌리에 선다. 보고의 회의 한 장이 내 예약을 읽는다
MEETING_SCRIPT = ("scripts", "meeting_room.py")
CLAUDE_NAMES = ("claude.exe", "claude")  # PATH 에서 찾는 차례 — 네이티브 판이 먼저, 없으면 npm 판의 claude.cmd(PATHEXT 가 붙인다)
CLAUDE_TOOLS = "Bash,Read,Glob,Grep"     # 사람 없는 실행에 남기는 기본 도구 — 쓰기 · 고치기 · 웹 · 스킬 · 하위 에이전트 · PowerShell 은 아예 없다.
                                         # 업무 파일은 아래 쓰는 손(열린 명령)으로만 쓴다 — 파일 도구를 주면 그 손의 절 지킴을 건너뛴다
WORK_SKILL = "mailbox-work"              # 업무 파악 스킬 — 이 스킬과 같은 스킬 뿌리에 나란히 선다. 사람 없는 보고가 짓기 전에 그 업무 파악을 한다
WORK_WRITER = ("scripts", "work.py")     # 그 스킬의 쓰는 손 — 업무 파일 하나만 바꿔 쓰고 앞 판의 절이 빠진 글 · 빈 글은 안 쓴다(사람 없는 실행에 연다)
WORK_FILE = "work.md"                    # 업무 파일 — 사용자 폴더에 산다(주인은 스킬 mailbox-work · 원본 이름은 그 쓰는 손의 WORK_FILE)
LANE_FILE = "lane.md"                    # 업무 파악 · 일일 보고 스킬의 걸음을 든 글 — 사람 없는 보고는 맡길 곳이 없어 그 글대로 한다(SKILL.md 는
                                         # 맡기는 쪽의 글이다)
NESTED_ENV = ("CLAUDECODE",)             # 대화 안에서 부른 판(run --now)이 띄울 때 걷는 변수 — 있으면 claude 가 겹친 세션이라며 안 뜬다
# 띄운 보고의 표 — 요청이 루프백 프록시를 지날 때만 그 claude 의 모든 요청에 머리 하나를 싣는다. 프록시는 그 대화를 도구 결과를
# 기다릴 때만 데우고, 답하고 끝난 보고에는 데우기를 안 버린다 — 머리가 없으면 사람의 메인 대화로 보여 끝난 뒤에도 데워진다.
# 빌린 곳 — 이 저장소 스킬 claude-background 의 claude_bg.py `child_env` · `RUNNER_HEADER`(31aa5f11 판)와 agent-envelope 의
# runner_common.py `loopback_proxy`. 손으로 따라간다 — 머리 이름은 프록시(posco/pgpt-proxy/opus5_proxy.py)의 `RUNNER_HEADER` 와 같아야 한다.
# 값만 다르다(그쪽은 claude-background) — 프록시는 값을 안 가린다
CUSTOM_HEADERS_ENV = "ANTHROPIC_CUSTOM_HEADERS"
RUNNER_HEADER = "x-agent-runner"
RUNNER_HEADER_VALUE = "mailbox-scan"
BASE_URL_ENV = "ANTHROPIC_BASE_URL"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
# 손의 읽는 명령 — 사람 없는 보고에 여는 것(손 mail.py 머리말 「어떻게 부르나」 · company_calendar.py 머리말). 권한 규칙의 꼴 그대로다 —
# 끝의 「 *」는 그 뒤에 무엇이 와도(인자 · `2>&1`) 되고 명령만 써도 된다. 「;」 · 「&&」 · 「|」로 이은 다른 명령은 따로 대어 막힌다
MAIL_READS = ("session *", "folders *", "rules *", "list *", "read *", "read-many *", "summary *", "search *", "who *")
# session 은 보고 창의 메일함 주소를, folders · rules 는 업무 파악이 폴더 · 규칙을(스캔이 낡았을 때), who 는 사용자 · 윗분을 짐작하는 주소록 ·
# 조직도를 받는다(업무 파악 스킬의 「읽는 법」 · first-understanding.md). who 의 `--out` 은 아래에서 막는다 — 준 자리에 아무 파일이나 쓴다
CALENDAR_READS = ("show *", "calendars *", "event *", "preview *")
# event 는 회의 한 장의 참석자 · 곳 · Teams 를, preview 는 「일정에 없는 약속」 카드의 값과 열쇠를 받는다(일정을 안 바꾼다 — 넣기는 사람이 카드를
# 누른 뒤 일일 보고의 넣는 손이 그 열쇠로 한다)
MEETING_READS = ("mine *",)              # 회의 한 장이 그 시각에 내 회의실 예약이 있나를 본다(손 meeting_room.py 머리말)
# 막는 명령 — 사용자 설정의 allow 가 함께 실려도 막을 자리다(deny 가 어느 allow 보다 앞선다): 손의 바꾸는 · 내보내는 · 파일을 쓰는
# 명령, EP 로그인 · 문서함 스킬, 밖으로 나가거나 무엇이든 돌리는 프로그램, MCP.
# ⚠ 열린 명령의 깃발이 파일을 쓰면(`read --images` · `who --out`) 열린 꼴에 맞으므로 여기서 따로 막는다
# ⚠ 일정 손의 바꾸는 명령은 스크립트 이름 바로 뒤의 자리로만 막는다 — 열린 `preview` 는 메일에서 온 제목 · 곳을 인자로 받아, 글자만 보면
#   「credit · address」 가 든 미리 보기가 막혀 그 약속의 카드가 말없이 안 선다
BRIEF_DENY = ("Bash(*mail.py* draft *)", "Bash(*mail.py*send-draft*)", "Bash(*mail.py*apply-*)",
              "Bash(*mail.py*preview-*)", "Bash(*mail.py*attachment*)", "Bash(*mail.py*--out*)",
              "Bash(*mail.py*--images*)",
              *(f"Bash(*company_calendar.py{q} {c}*)" for c in ("add", "delete", "edit", "remember") for q in ('"', "")),
              "Bash(*meeting_room.py*book*)", "Bash(*meeting_room.py*change*)", "Bash(*meeting_room.py*cancel*)",
              "Bash(*meeting_room.py*preview*)", "Bash(*meeting_room.py*pref*)",
              "Bash(*ep-login/scripts*)", "Bash(*edge_session.js*)", "Bash(*ep_login.js*)", "Bash(*company-ecm/scripts*)",
              "Bash(gh *)", "Bash(git *)", "Bash(curl *)", "Bash(wget *)", "Bash(node *)", "Bash(npx *)", "Bash(powershell*)",
              "Bash(pwsh*)", "Bash(cmd*)", "Bash(claude*)", "Bash(schtasks*)", "mcp__*")
