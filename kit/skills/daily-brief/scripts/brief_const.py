"""일일 보고의 창 · 창 곁의 손 · 형제 스킬과의 이음이 함께 쓰는 이름 붙은 값 — 저장 열쇠 · 시한 · 파일 이름 꼴 · Edge 이름.

값만 든다 — 셈 · 읽기는 그 값을 쓰는 조각이 든다. 한 조각만 쓰는 값은 그 조각 곁에 둔다.
"""

import datetime as dt
import re

FILE_NAME = "brief-{:%Y-%m-%d-%H%M}.html"
LATEST_BRIEF, LATEST_MADE = "brief", "made"     # `window.py --latest` 가 내는 JSON 의 열쇠 — 형제 스킬(company-work 의 now.py)이 읽는 계약
# 요일 이름 — ep-login 의 `ep_command.WEEKDAYS` 의 손사본이다(이 손은 홀로 서야 해서 못 싣는다). 하나를 고치면 다른 하나도 고친다
WEEKDAYS = "월화수목금토일"
# 카드의 시각은 서울 벽시계다 — 일정 손의 꼴(형제 스킬 ep-login `ep_command.SEOUL` 의 손사본 · 같은 까닭으로 못 싣는다). 일광 절약이 없다
SEOUL = dt.timezone(dt.timedelta(hours=9))
SEOUL_OFFSET = dt.datetime(2000, 1, 1, tzinfo=SEOUL).isoformat()[-6:]   # 「+09:00」 — 창의 스크립트가 카드의 시각에 붙여 읽는다(지을 때 넣는다)
EDGE_HOST = "127.0.0.1"                        # 사용자의 로그인 Edge 는 이 PC 의 디버깅 포트에만 있다 — 다른 호스트는 부르지 않는다
EDGE_PORT_DEFAULT = "9222"                     # 스킬 ep-login 이 여는 포트(환경변수 EDGE_DEBUG_PORT 로 바뀐다 · 쉼표로 여럿이면 첫 것)
# 누르신 표시 — 창은 메일 번호마다 localStorage 의 이 열쇠에 남기고(값의 `mark` 가 무엇을 누르셨나다), 곁의 ticks.py 가 같은 이름으로 거둔다
DONE_PREFIX = "brief-done:"
TIMES_KEY = "brief-times"                      # 「보고 맞추기」에서 고르신 보고 시각 — 창 곁의 손이(없으면 시계 판이 창의 문 window_door 로) 받아 건다
STATE_KEY = "brief-state"                      # 창이 보이는 지금 모습(`state_of` — 시각표 · 규칙의 수 · 올리지 않을 것 · 내일 다시 볼 것) — 그것을 바꾸는
                                               # 명령(대화의 clock.py · prefs.py)과 시계 판 · 거두는 손이 열린 창에 바로 적는다
UNQUIET_PREFIX = "brief-unquiet:"              # 「올리지 않기로 한 것」의 「다시 올리기」 — 맞춤 파일 줄의 열쇠(`prefs_file.key`)마다
CAL_PREFIX = "brief-cal:"                      # 「일정에 넣기」의 누름 — 카드의 열쇠(일정 손 preview 의 key)마다. 곁의 presses.py 가 거둬 넣고 끝을 돌려 적는다
HAND_KEY = "brief-hand"                        # 창 곁의 거두는 손이 살아 있다는 숨 표 — 창이 누름 직후의 말을 고르는 데 쓴다
AWAY_KEY = "brief-away"                        # 「보고 맞추기」의 「자리 밖에서 보기」 켜고 끄기 — 창 곁의 손이(없으면 시계 판이) 받아 건다
HAND_BEAT_S = 5                                # 그 손이 숨 표를 적는 사이(초). 창은 이 세 배 넘게 숨 표가 없으면 손이 없다고 본다
# 창 머리의 「비서에게 부탁하기」 — 친 말을 채운 Claude Code 대화를 VS Code 의 작업 폴더 창에 연다(곁의 asks.py). 부탁은 한 번에 하나다 —
# 여는 동안 단추가 잠긴다. 거두는 것은 창 곁의 손뿐이고 스캔 판은 안 거둔다 — 자리를 뜬 뒤에 VS Code 가 뜨면 놀란다
ASK_KEY = "brief-ask"
ASK_TAKE_S = 3 * HAND_BEAT_S                   # 누른 뒤 이 안에 손이 안 거두면 창이 「못 열었다」로 맺고, 손도 그보다 늦은 부탁은 안 연다
RUN_TAKE_S = ASK_TAKE_S                        # 맡길 일의 누름도 같다 — 이 안에 손이 안 맡으면 창이 「못 맡김」으로 맺고, 손도 그보다 늦은 누름은 안 맡는다
ASK_OPEN_CEILING_S = 30                        # 손이 작업 폴더 창이 서기를 기다리는 천장 — 정한 시간으로 기다리지 않고 그 상태를 본다
ASK_NO_VSCODE = "이 PC 에는 VS Code 의 Claude Code 가 없어 여기서는 부탁하실 수 없습니다 — 쓰시는 대화 창에서 말씀해 주세요."
TASK_BAD = "적힌 꼴이 틀려 이 창에서는 맡기실 수 없습니다 — 대화에서 말씀해 주세요"
# 창이 남기는 누름 · 창 곁의 손이 적는 결과 — 열쇠의 꼴과 칸은 `references/DESIGN.md` 「맡길 일」의 표가 원본이다
RUN_PREFIX = "brief-run:"                      # 누름 하나 — <창 이름>~<누른 때(ms)>
RUN_REFUSED = "refused"                        # 누름의 끝 — 창 곁의 손이 아무것도 넘기지 못했다(까닭은 일마다). 창은 「못 맡김」으로 세운다
TASK_PREFIX = "brief-task:"                    # 일 하나의 결과 — <창 이름>/<일의 번호>
VIA_EDGE = "via=edge"                          # 로그인 Edge 로 연 창의 주소 꼬리 — 표시가 거둬지는 창만 단추를 보인다
# 사람 없는 실행 — 같은 스킬의 `unattended/` 폴더와 그 입구 둘(시계 · 맡긴 일). 창 곁의 손은 이 이름으로 부르고(`unattended_link`), 그 폴더는 이
# 이름을 여기서 싣는다(`unattended_const`) — 입구의 이름은 작업 스케줄러의 작업 · 설치가 기대는 약속이다
UNATTENDED_DIR, CLOCK_ENTRY, HANDED_ENTRY = "unattended", "clock.py", "handed.py"
# 사용자 폴더에서 창이 읽기만 하는 사람 없는 실행의 파일 — 보고 시각표와 그날 장부(그 안의 `clock_at` 이 시계의 마지막 판 때). 원본 이름은
# `unattended_const` 의 SCHEDULE_FILE · DAY_FILE · CLOCK_AT 이고 그쪽이 이 값을 싣는다
SCHEDULE_FILE, DAY_FILE, CLOCK_AT = "daily-brief-schedule.json", "daily-brief-day.json", "clock_at"
# 손 명령(window.py · ticks.py · prefs.py)의 종료 값 — 틀린 인자는 argparse 가 2 로 나간다. 3 은 사람 없는 실행과 lane.md 가 「Edge 에 못 닿았다」로 읽는다
EXIT_OK, EXIT_FAIL, EXIT_NO_EDGE = 0, 1, 3
# 창이 남긴 칸의 꼴 — 누른 때(`at`)와 고르신 보고 시각(HH:MM). 창에 돌려 적는 말은 이 길이에서 자른다
AT = re.compile(r"^\S{1,40}$")
HHMM = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
SAID_MAX = 240
# 넣는 손(`ticks.py --presses`)이 거둔 수를 댄 끝 줄의 머리 — 시계 판(`unattended/window_link.py`)이 이 머리로 그 줄을 골라 판 끝에 싣는다
ROUND_HEAD = "보고 창의 「일정에 넣기」 — "
