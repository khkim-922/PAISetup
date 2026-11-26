"""일일 보고의 사람 없는 실행(정한 시각의 시계 · 맡긴 일)이 쓰는 이름 붙은 값 — 사용자 폴더의 파일 이름 · 시한 · 형제 스킬의 자리 · 띄운
claude 의 울타리. `unattended/` 의 손이 다 여기서 읽는다.

값마다 곁주석이 까닭을 든다. 스캔과 같은 사실을 드는 값(회사 메일 손의 자리 · 종료 값 · 시한 · 세션 답 낱말 · 「다음:」 말)은 스캔의 원본을
바이트째 베낀 곁의 `hand_facts` 에서 다시 내보낸다 — 손으로 맞추지 않는다.
"""

from __future__ import annotations

import pathlib

HERE = pathlib.Path(__file__).resolve().parent          # 이 폴더 — 사람 없는 실행의 입구 둘(clock.py · handed.py)이 선다
SKILL_DIR = HERE.parent                                  # 일일 보고 스킬
SKILLS_ROOT = SKILL_DIR.parent                           # 이 스킬과 형제 스킬(메일함 스캔 · 업무 파악 · 회사 메일)이 나란히 선 스킬 뿌리
from brief_const import CLOCK_AT, CLOCK_ENTRY, DAY_FILE, HANDED_ENTRY, SCHEDULE_FILE  # noqa: E402,F401 — 입구 · 창이 읽는 파일의 이름(원본은 바탕)

# ── 사용자 폴더 — 이 스킬의 파일은 사용자 폴더 바로 밑에 `daily-brief-` 머리로 선다(꼴의 원본은 references/DESIGN.md 「새 파일 이름」) ──
# SCHEDULE_FILE — 보고 시각표 · 띄울 claude · 자리 밖에서 보기 · 고른 것 · 스스로 로그인한 범위 / DAY_FILE — 그날 장부 + 시계의 마지막 판 때
# (`CLOCK_AT` — 시계가 판마다 잠금을 쥔 뒤 적고 창의 `seen` 이 읽는다). 시계가 OS 잠금 아래 혼자 쓴다
LAUNCH_FILE = "daily-brief-launch.json"       # 띄운 보고 하나 — 띄운 때 · 프로세스 번호 · 그 프로세스가 뜬 때(끝났나는 `brief_reports.run_end` 가 가른다)
LAUNCH_SETTINGS_FILE = "daily-brief-launch-settings.json"   # 띄울 때마다 짓는 claude 의 권한(열린 · 막은 명령) — `claude --settings` 로 준다
LAUNCH_PROMPT_FILE = "daily-brief-launch-prompt.txt"        # 띄울 때마다 짓는 부탁 글 — 표준 입력으로 준다(명령줄에 한글 · 따옴표를 안 싣는다)
LAUNCH_LOG_FILE = "daily-brief-launch.log"                  # 마지막으로 띄운 보고의 출력 — 띄울 때마다 새로 쓴다
AWAY_SENDING_FILE = "daily-brief-away-sending.json"         # 중계를 부르기 전에 굳히는 「보내는 중」 표지(그날 · 칸의 시각 · 때) — 다음 판이 칸의 기록과 견줘 걷는다
AWAY_TEMP_PREFIX = "daily-brief-away-me-"                   # 주소록 손이 「나」를 쓰는 임시 폴더의 머리 — 쓰고 곧 지운다
HANDED_DIR = "daily-brief-handed"             # 맡긴 판의 폴더 — 판마다 하나(기록 · 맡긴 일 · 부탁 글 · 흐름)
CLOCK_LOCK_FILE = "daily-brief-clock.lock"    # 시계 판 하나 — OS 잠금(`oslock.py`) · 손이 죽으면 OS 가 푼다
CLOCK_XML_FILE = "daily-brief-clock.xml"      # 작업 스케줄러에 건 시계 정의의 사본 — 등록할 때 쓴다
# 옛 자리 — 메일함 스캔이 보고를 들던 판의 파일. 새 파일이 없을 때만 읽어 옮겨 받는다(`adopt` · 시계의 첫 판). 옛 것은 안 지운다
LEGACY_DIR = "mailbox-scan"
LEGACY_SCHEDULE = (LEGACY_DIR, "brief.json")
LEGACY_STATE = (LEGACY_DIR, "state.json")    # 그 안의 `brief` 칸이 옛 그날 장부다 — 스캔은 그 칸을 다시 안 쓰고 안 지운다
LEGACY_LAUNCH = (LEGACY_DIR, "brief.lock")
LEGACY_LAUNCH_LOG = (LEGACY_DIR, "brief-run.log")
LEGACY_AWAY_SENDING = (LEGACY_DIR, "away-sending.json")
LEGACY_HANDED = (LEGACY_DIR, "handed")
LEGACY_DAY_KEY = "brief"
LEGACY_FILES = ((LEGACY_SCHEDULE, SCHEDULE_FILE), (LEGACY_LAUNCH, LAUNCH_FILE), (LEGACY_LAUNCH_LOG, LAUNCH_LOG_FILE),
                       (LEGACY_AWAY_SENDING, AWAY_SENDING_FILE))   # 옮겨 받는 파일 짝 — (옛 자리, 새 이름). 그날 장부는 옛 지금 모습의 칸이라 따로 옮긴다

# ── 형제 스킬 — 명령으로만 부른다(코드를 싣지 않는다 — 그 스킬이 바뀌어도 이 손이 안 깨지게) ──────────────────────────────────
SCAN_SKILL = "mailbox-scan"
SCAN_SCRIPT = ("scripts", "scan.py")          # 스캔의 입구 — `run --now --wait` · `status --json` 두 문만 부른다
SCAN_READER = ("scripts", "reader.py")        # 쌓인 것을 읽는 명령 — 띄운 claude 에 연다
SCAN_STATUS_FORMATS = (1,)                    # 읽을 줄 아는 `status --json` 의 꼴 번호(원본은 그 스킬 `scan_const.STATUS_FORMAT`)
SCAN_WAIT_S = 900                             # 청한 판이 앞 판의 잠금을 기다리는 시한 — 스캔의 한 판이 손을 부르는 시간의 한계(그 스킬의 RUN_BUDGET_S) 안
SCAN_CALL_TIMEOUT_S = 2400                    # 청한 부름의 시한 — 기다림 + 가장 긴 한 판(그 스킬의 잠금이 낡는 때 `LOCK_STALE_S` — 판의 상한 · 손 · 신원 명령의 시한을 든다)보다 길게
SCAN_STATUS_TIMEOUT_S = 60                    # `status --json` 한 번의 시한 — 파일 하나를 읽는다(`--dry-run` 이면 작업 스케줄러에 안 묻는다)
# 회사 메일 손의 자리 · 종료 값 · 시한 · 로그인이 사는 스킬 · 세션 답 낱말 · 다음 걸음 — 스캔과 같은 사실이라 곁의 `hand_facts` 사본이 든다.
# 걸 때 `--hand` 를 안 주면 형제 폴더의 회사 메일 손을 쓴다
from hand_facts import (HAND_EXIT_OK, HAND_EXIT_SESSION, HAND_SCRIPT, HAND_SKILL, HAND_TIMEOUT_S, NEXT_LOGIN, SESSION_LIVE,  # noqa: E402,F401
                        SESSION_LOST, SESSION_SKILL)
SESSION_ERROR = "error"                       # 사내 세션을 살펴본 손이 답을 못 냈다 — 이 스킬의 살펴보기만 내는 답
# ── 정한 시각의 보고 — 시계 판이 보고 시각표의 시각마다 일일 보고를 사람 없이 한 번씩 띄운다 ──────────────
BRIEF_FORMAT = 2                         # 시각표 파일의 꼴 번호 — 2 는 시각표(`times`). 1(시각 하나 `at`)도 읽는다 — 그 꼴로 걸어 둔 PC 가 다시 안 걸어도 돈다
BRIEF_FORMATS_READ = (1, 2)
BRIEF_AT_DEFAULT = "07:30"               # 보고 시각표의 기본(서울) — 시각 하나. 사용자가 `clock.py at` 으로 바꾸고 더한다
BRIEF_WAIT_MIN = 270                     # 시각 하나가 사내 세션을 기다리는 가장 긴 틈(분) — 그 시각부터 다음 시각까지, 다음 시각이 더 멀면 이만큼까지
                                         # 띄우고 그 뒤 그 시각은 건너뛴다. 기본 07:30 이 12:00 까지 기다리던 것과 같은 값이다 — 아침 보고가 오후에
                                         # 서지 않고, 사내 인증을 하루 내내 두드리지 않는다. 어느 시각도 그날(서울 자정)을 넘겨 기다리지 않는다
CLOCK_EVERY_MIN = 15                     # 시계 작업이 깨는 주기(분) — 거는 명령과 옮겨 받기가 늘 이 값으로 건다(옛 스캔의 주기를 베낀 시계도 이 값으로 다시 선다). 판은 보고 시각의 칸
                                         # 안에서만 메일함을 읽어(스캔에 한 판을 청한다) 주기는 메일 서버의 부담이 아니라 보고가 얼마나 늦게 서나 ·
                                         # 보고 창의 누름을 얼마나 늦게 거두나다
BRIEF_ROOM_MIN = 30                      # 시각마다 있어야 할 가장 짧은 틈(분) — 이보다 짧으면 거는 명령이 거절한다. 시계는 `CLOCK_EVERY_MIN` 분마다 깨어,
                                         # 틈이 이보다 짧으면 그 시각에 판이 하나도 안 돌아 날마다 조용히 안 뜬다
BRIEF_UNTIL_ENV = "MAILBOX_SCAN_BRIEF_UNTIL"   # 검사가 기다림의 끝을 서울 시각 하나로 바꿀 때만 준다(`BRIEF_WAIT_MIN` 대신) — 하루 어느 때에 돌아도
                                               # 같은 판을 재게
BRIEF_TRY_GAP_MIN = 5                    # 판이 답을 안 준 주기에 손의 session 으로 살펴보는 사이의 가장 짧은 틈(분) — 작업이 더 자주 깨워도 이보다
                                         # 촘촘히 안 묻는다. 분 단위로 잰다: 작업은 정각 분에 깨우고 프로세스가 뜨는 데 몇십 초가 들어, 초까지 재면
                                         # 5분마다의 판이 한 판씩 건너뛴다
# 스스로 로그인 — 보고 시각을 건 PC 에서(시각을 건 것이 곧 이 로그인이다 · 따로 켜는 값은 없다), 보고 시각의 띄우기 앞에 형제 스킬 ep-login 의 입구를 사람 없는 꼴로 부른다: 그날 첫 시각에 한 번
# (세션이 살았어도), 뒤 시각은 세션이 끊겨 있을 때 그 칸에서 한 번. 보고 시각 사이의 판은 안 부른다 — 로그인하는 순간 사람의 평소 Edge 에서
# 메일 · 일정 창이 닫히고 EP 포털이 죽어, 그 값을 보고 시각에만 치른다
LOGIN_ENTRANCE = ("scripts", "ep_login.js")   # 그 스킬의 입구 — 받아 보고, 안 서면 평소 Edge 에서 먼저 · 이어 제 창을 띄워 통합 인증으로
                                              # 세운다(명령으로만 부른다)
LOGIN_ENTRANCE_ENV = "EP_LOGIN_ENTRANCE"  # 검사가 입구를 대역으로 바꿀 때만 준다
LOGIN_ARGS = ("domino", "--unattended")   # 메일 · 일정의 세션만 · 사람이 쳐야 하는 자리(SSO 가 안 서는 로그온 · 통합 인증이 안 선 화면)에서는 입구가 기다리지 않고 4 다
LOGIN_NODE = "node"                       # 입구를 돌릴 node — PATH 에서 찾는다(회사 메일 손이 세션 손을 돌리는 것과 같은 node)
from brief_const import LOGIN_TIMEOUT_S  # noqa: E402,F401 — 입구 한 번의 시한(값의 자리는 바탕 — 빌리기의 시한이 그 위에서 셈한다)
LOGIN_SAID_CHARS = 200                    # status 가 옮겨 보이는 입구의 끝말 글자 수
# 돌려주기 — 시계가 끊긴 세션 위에서 스스로 로그인한 판(그 로그인이 사람의 평소 Edge 의 EP 포털을 죽였다)은 그 보고가 끝나고 그 뒤 이만큼 지나
# 처음 도는 판에 같은 입구의 돌려주는 문을 사람 없는 꼴로 한 번 부른다 — 평소 Edge 에 로그인을 다시 열고 쓸모가 끝난 EP 탭을 닫는다. 보고 창의
# 「일정에 넣기」가 그 사이 그 세션에서 넣을 틈이다. 언제 부르고 언제 안 부르나는 `references/DESIGN.md` 「사람의 로그인을 돌려준다」가 든다
from brief_const import GIVE_BACK_AFTER_MIN  # noqa: E402,F401 — 값의 자리는 바탕(보고 창의 말도 같은 값을 읽는다)
GIVE_BACK_ARGS = ("--give-back", "--unattended")   # 그 문의 끝 줄(종료 0) — `given-back port-closed=N port-left=N ordinary-closed=N ordinary-kept=N`
GIVE_BACK_TYPED = 4                       # 그 문의 4 — SSO 가 안 서는 로그온이라 아무것도 안 열고 안 닫았다(칠 사람이 없다) · 그날은 다시 안 부른다
from brief_const import GIVE_BACK_TIMEOUT_S  # noqa: E402,F401 — 돌려주는 문 한 번의 시한(값의 자리는 바탕)
LOAN_FILE = "daily-brief-loan.json"       # 보고 창의 단추가 돌려준 뒤 잠깐 다시 세운 로그인 한 장(그날 · 빌린 때 · 쓰는 일들 · 돌려준 끝) — 쓰는 것은 `loan.py` 하나다
LOAN_LOCK_FILE = "daily-brief-loan.lock"  # 빌리고 돌려주는 손 하나 — 시계 판 · 창 곁의 손 · 맡긴 일의 지킴이가 함께 불러도 입구를 한 번 부른다
from brief_const import LEND_CALL_S as LEND_TIMEOUT_S  # noqa: E402 — 빌리기 · 놓기 한 번의 시한(원본은 바탕 — 창 곁의 손도 같은 값으로 부른다)
BRIEF_LOCK_STALE_S = 60 * 60             # 띄운 보고가 이보다 오래 안 끝났으면 멈춘 것으로 본다(회사에서 한 판의 값을 재기 전의 기본값). 스스로 로그인한
                                         # 때부터 이만큼이 그 보고가 창을 지을 수 있는 범위다(시각표 파일의 `signed` — `brief_schedule.note_signed`)
WINDOW_SCRIPT = SKILL_DIR / "scripts" / "window.py"   # 보고 창 손 — 메일 한 장(--sheet) · 띄운 보고가 창을 띄운다
TICKS_SCRIPT = SKILL_DIR / "scripts" / "ticks.py"     # 거두는 손 — 띄운 보고가 업무 파악보다 먼저 부르고, 시계 판은 그 창에서 고르신 것 · 누름만
                                                      # 묻는다(열린 창이 없으면 아무것도 안 연다)
BRIEF_TIMES_TIMEOUT_S = 20               # 판이 보고 창의 시각을 묻는 손 한 번의 시한 — 그 손은 이 PC 의 디버깅 포트만 짧게 부른다
BRIEF_PRESSES_WITHIN_S = 360             # 판이 보고 창의 「일정에 넣기」 누름을 거두는 데 쓰는 시간 — 그 손은 이 안에 일정 손의 시한이 다 드는 넣기만
                                         # 시작하고 남은 누름은 다음 판에 둔다. 판 전체의 시한(`CLOCK_TIME_LIMIT_MIN`)을 넘기지 않게 짧게 둔다
BRIEF_PRESSES_TIMEOUT_S = BRIEF_PRESSES_WITHIN_S + 60   # 그 손 한 번의 시한 — 넣기 도중에 끊으면 들었는지 모르는 끝이 남아 넉넉히 둔다
# 그 손을 띄우기 전에 로그인 Edge 의 디버깅 포트가 받나만 본다 — 자리 · 포트는 이 스킬 바탕(`brief_const.EDGE_HOST` · `edge.port`)이 든다
EDGE_PROBE_S = 0.5
# 자리 밖에서 보기 — 사용자가 켠 PC 에서만, 사람 없이 띄운 보고가 남긴 보고 글 한 장을 칸마다 한 통 본인 주소로 보낸다. 보내는 것은 판의
# 코드다 — 띄운 claude 에는 보내는 명령이 없다(BRIEF_DENY 그대로)
DIRECTORY_SKILL = "company-directory"    # 본인 주소를 받는 주소록 손 — 회사 메일 손과 같은 스킬 뿌리에 나란히 선다
DIRECTORY_SCRIPT = ("scripts", "directory.py")
DIRECTORY_ME = ("find", "--me")          # 그 손의 「나」 — 이 세션의 메일함을 쓰는 사람(그 손 find --help)
DIRECTORY_PEOPLE = "people.json"         # 그 손이 --out 폴더에 쓰는 사람 파일(원본 이름은 그 손의 PEOPLE_JSON)
DIRECTORY_TIMEOUT_S = HAND_TIMEOUT_S     # 주소록 손 한 번의 시한 — 그 손도 세션을 받아 메일 서버에 묻는다
AWAY_SENDER = "away_sender.py"           # 보내는 손 — 이 폴더에 산다(머리말)
AWAY_SHEET_TIMEOUT_S = 60                # 보고 창 손이 보고 글 한 장을 메일 한 장으로 짓는 시한 — 파일 하나를 읽어 바꾸기만 한다
AWAY_SEND_TIMEOUT_S = 300                # 보내는 손 한 번의 시한 — 중계는 걸음(연결 · 인사 · STARTTLS 뒤 다시 연결 · 넘기기)마다 메일 손의 응답
                                         # 시한(mailer.py 기본 60초)을 쓴다. 넘겨 끊으면 중계가 받았는지 모르는 끝으로 적고 다시 안 보낸다
AWAY_LATEST_S = 7 * 60
# ↑ 시계 판이 시작한 뒤 메일 한 통 · 주소록 한 번을 새로 시작해도 되는 끝(초). 넘긴 판은 안 보내고 다음 판(`CLOCK_EVERY_MIN` 분 뒤)에 둔다. 그 뒤의
#   일(창의 고름 · 로그인 · 청한 스캔 · 누름 거두기)까지 다 든 판의 끝이 시계 작업의 시한(`CLOCK_TIME_LIMIT_MIN`)이다

AWAY_SENT, AWAY_RETRY, AWAY_UNSURE = "sent", "retry", "unsure"   # 칸의 메일 기록(`slots.<시각>.mail.state`)
SEND_EXIT_SENT, SEND_EXIT_BEFORE, SEND_EXIT_UNSURE = 0, 4, 5   # 보내는 손의 종료 값 — 보냈다 · 넘기기 전에 졌다 · 넘기는 도중이나 뒤에 졌다
CALENDAR_SKILL = "company-calendar"      # 회사 메일 손과 같은 스킬 뿌리에 나란히 선다
CALENDAR_SCRIPT = ("scripts", "company_calendar.py")
IDENTITY_SCRIPT = ("scripts", "identity.py")   # 주소록 손의 보낸 분 신원 — 스캔이 못 본 메일의 보낸 분만 묻는다(lookup 은 로그인 손을 안 띄운다)
APPROVAL_SKILL = "company-approval"      # 전자결재 손 — 같은 스킬 뿌리에 선다. 보고가 결재하실 것 · 올리신 결재를 읽는다
APPROVAL_SCRIPT = ("scripts", "approval.py")
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
RUNNER_HEADER_VALUE = "daily-brief"
BASE_URL_ENV = "ANTHROPIC_BASE_URL"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
# 손의 읽는 명령 — 사람 없는 보고에 여는 것(손 mail.py 머리말 「어떻게 부르나」 · company_calendar.py 머리말). 권한 규칙의 꼴 그대로다 —
# 끝의 「 *」는 그 뒤에 무엇이 와도(인자 · `2>&1`) 되고 명령만 써도 된다. 「;」 · 「&&」 · 「|」로 이은 다른 명령은 따로 대어 막힌다
MAIL_READS = ("session *", "folders *", "rules *", "list *", "read *", "read-many *", "summary *", "search *")
# session 은 보고 창의 메일함 주소를, folders · rules 는 업무 파악이 폴더 · 규칙을(스캔이 낡았을 때) 받는다
DIRECTORY_READS = ("find *",)
# 주소록 손(DIRECTORY_SKILL)의 찾기 — 업무 파악이 사용자 · 윗분을 짐작하는 주소록 · 조직도를 받는다(업무 파악 스킬의 「읽는 법」 ·
# first-understanding.md). `--out` 은 아래에서 막는다 — 준 자리에 아무 파일이나 쓴다
IDENTITY_READS = ("lookup *",)
# 보낸 분 신원(주소록 손 identity.py)의 lookup — 표준 입력의 주소(heredoc)마다 신원 JSON 을 낸다. 세션 파일을 있는 그대로만 써 로그인 손을 안
# 띄우고 아무것도 안 바꾼다(그 손 머리말). show · pull 은 대화의 문이라 안 연다
APPROVAL_READS = ("box *", "read *")
# 전자결재 손의 읽기 — 결재하실 것(box todo) · 올리신 결재(box sent · sent-stopped)와 결재선(read). 결재 앱에 아무것도 안 남긴다(그 손 SKILL.md
# 「읽는다」). 창을 띄우는 open 과 쓰기는 아래에서 막는다
CALENDAR_READS = ("show *", "calendars *", "event *", "preview *")
# event 는 회의 한 장의 참석자 · 곳 · Teams 를, preview 는 「일정에 없는 약속」 카드의 값과 열쇠를 받는다(일정을 안 바꾼다 — 넣기는 사람이 카드를
# 누른 뒤 일일 보고의 넣는 손이 그 열쇠로 한다)
MEETING_READS = ("mine *", "free *", "rooms *")
# mine 은 회의 한 장이 그 시각에 내 회의실 예약이 있나를, 그리고 지난 날을 주면 늘 잡던 건물 · 층을 본다. free(그 시각에 빈 회의실) · rooms(회의실
# 찾기)는 카드의 「회의실 잡기」 줄에 그 시각에 정말 비는 방 하나를 적으려 읽는다(일일 보고 lane.md 「맡길 일」). 셋 다 예약 · 설정을 안 바꾸고
# 파일을 안 쓰고 창을 안 띄운다(손 meeting_room.py 머리말 · 그 READS 표). 사람의 근무지는 열린 주소록 find 가 낸다
# 막는 명령 — 사용자 설정의 allow 가 함께 실려도 막을 자리다(deny 가 어느 allow 보다 앞선다): 손의 바꾸는 · 내보내는 · 파일을 쓰는 ·
# 사람의 화면에 창을 띄우는(일정 손의 teams-meeting) 명령, EP 로그인 · 문서함 스킬, 밖으로 나가거나 무엇이든 돌리는 프로그램, MCP.
# ⚠ 열린 명령의 깃발이 파일을 쓰면(`read --images` · 주소록 `find --out`) 열린 꼴에 맞으므로 여기서 따로 막는다
# ⚠ 일정 손의 바꾸는 명령은 스크립트 이름 바로 뒤의 자리로만 막는다 — 열린 `preview` 는 메일에서 온 제목 · 곳을 인자로 받아, 글자만 보면
#   「credit · address」 가 든 미리 보기가 막혀 그 약속의 카드가 말없이 안 선다
BRIEF_DENY = ("Bash(*mail.py* draft *)", "Bash(*mail.py*send-draft*)", "Bash(*mail.py*apply-*)",
              "Bash(*mail.py*preview-*)", "Bash(*mail.py*attachment*)", "Bash(*mail.py*--images*)",
              "Bash(*directory.py*--out*)",
              *(f"Bash(*company_calendar.py{q} {c}*)" for c in ("add", "delete", "edit", "remember", "teams-meeting") for q in ('"', "")),
              "Bash(*meeting_room.py*book*)", "Bash(*meeting_room.py*change*)", "Bash(*meeting_room.py*cancel*)",
              "Bash(*meeting_room.py*preview*)", "Bash(*meeting_room.py*pref*)",
              *(f"Bash(*approval.py{q} {c}*)" for c in ("open", "save", "discard", "preview", "form", "forms") for q in ('"', "")),
              *(f"Bash(*identity.py{q} {c}*)" for c in ("show", "pull") for q in ('"', "")),
              "Bash(*ep-login/scripts*)", "Bash(*edge_session.js*)", "Bash(*ep_login.js*)", "Bash(*company-ecm/scripts*)",
              "Bash(gh *)", "Bash(git *)", "Bash(curl *)", "Bash(wget *)", "Bash(node *)", "Bash(npx *)", "Bash(powershell*)",
              "Bash(pwsh*)", "Bash(cmd*)", "Bash(claude*)", "Bash(schtasks*)", "mcp__*")

# 작업 스케줄러가 시계 판 하나를 끊는 시한(분) — 판이 그 안에서 제 일을 다 맺게 판의 가장 긴 길(자리 밖 메일을 시작해도 되는 끝 · 메일 한 장 ·
# 보내기 · 로그인 · 창의 고름 · 청한 스캔 · 누름 거두기와 그 안의 쓴다고 적기 · 끝 뒤의 놓기 · 판 끝의 돌려주기)에 5분을 더한다
CLOCK_TIME_LIMIT_MIN = -(-(AWAY_LATEST_S + AWAY_SHEET_TIMEOUT_S + AWAY_SEND_TIMEOUT_S + LOGIN_TIMEOUT_S + BRIEF_TIMES_TIMEOUT_S
                           + SCAN_STATUS_TIMEOUT_S * 2 + SCAN_CALL_TIMEOUT_S + BRIEF_PRESSES_TIMEOUT_S
                           + LEND_TIMEOUT_S + GIVE_BACK_TIMEOUT_S * 2) // 60) + 5
