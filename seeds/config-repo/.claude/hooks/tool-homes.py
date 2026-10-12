"""갈 곳 표를 읽어 규범 · 룰 · 에이전트 · 공용 메모리 목차 · 스킬을 도구 홈에 놓는 손 하나 (결정 0112 · 0113).

    python -X utf8 tool-homes.py sync  --layer standard|personal --from <뿌리> [--dry-run] [--home <홈>] [--box <값>]
    python -X utf8 tool-homes.py place [--dry-run] [--home <홈>] [--box <값>]
    python -X utf8 tool-homes.py check [--home <홈>] [--box <값>]

부르는 자는 셋이다 — 설치기는 짐으로 표준 층을(`sync --layer standard --from <짐>` · 끝 검증은 `check`), 배포와 세션 훅은
설정 저장소로 개인 층을(`sync --layer personal --from <저장소>`) 채운다. 배포는 `--dry-run` 의 줄을 계획 화면에 싣고 확인
뒤 같은 명령을 돌린다. `--home`(기본 사용자 홈) · `--box`(제작자 칸 값을 덮는다)는 가짜 홈 시험용이라 부르는 셋은 안 준다.

**무엇이 어느 홈에 어떤 꼴로 가나는 갈 곳 표(`<뿌리>/tool-homes.conf`)만 든다.** 항목 · 길 · 옛 자리와 꼴 · 조건의 뜻은 그
표의 머리가 든다 — 여기서는 놓는 법만 든다. 손은 표를 읽어 PC 의 중립 한 벌 `~/.paisetup` 의 두 층(standard · personal)을
채우고 홈에 놓는다. 어느 도구도 그 한 벌을 스스로 안 읽어서, 제작자 칸이 도구마다 뜻을 갖는다.

sync  — 한 층을 채운다. standard 는 짐에서 표의 층 안의 자리로, personal 은 설정 저장소에서 표의 저장소 자리로. 손과
        표도 제 몸을 층 뿌리에 싣는다. 층에는 표의 항목과 손 · 표만 든다 — 짐의 다른 것은 안 싣고, 층에 남은 다른 것은
        걷는다. 원본에 그 자리가 없으면 그 항목은 그 층에서 조용히 빠지고(층에 있었으면 걷는다) 다른 층이 이긴다 — 짐이
        안 싣는 항목(local)이 있고, 씨앗으로 만든 저장소는 제가 둔 원본만 든다. 저장소 자리가 여럿이면(폴더 항목) 그
        자리들의 내용을 한 폴더로 합치고, 같은 이름(항목 폴더 바로 밑)이 두 자리에 다 있으면 그 이름만 ERROR 를 내고 개인
        층에 안 싣는다(다른 층이 이긴다). each 항목의 뿌리에 바로 든 파일은 단위가 아니라 WARN 을 내고 안 싣는다. 원본은
        읽기만 하는 자리라 링크(심볼릭 링크 · 정션)를 따라간다 — 항목 자리 자체도, 폴더 항목 안의 폴더 · 파일도. 층에는
        링크 너머의 파일이 실린다. 폴더 항목 안에서 제 조상 폴더를 가리키는 링크(고리)는 안 따라가고, 끊긴 링크는 WARN 을
        내고 그 자리만 건너뛴다. 개인 층의 저장소 자리가 있는데 꼴이 표와 다르면(파일 · 폴더가 바뀜 · 끊긴 링크) WARN 을
        내고 그 자리를 그 층에서 뺀다. 항목마다 곁에 다 지은 뒤 바꿔 끼워 반쯤 채운 항목이 이기지 않게 하고, 바꿔 끼우기가
        막히면(윈도에서 누가 안의 파일을 열어 둠) 옛 항목을 그대로 둔다. 바뀐 것이 없으면 안 쓴다. 그 뒤 놓기를 맡을 층의
        손에게 place 를 넘기고, 그 줄을 이어 끝의 CHANGED 하나로 낸다. 개인 층을 채우러 온 뿌리에 표가 없으면 그 저장소는
        개인 층을 안 든다 — 아무것도 안 쓰고 넘기지도 않는다(`CHANGED=0` · 종료 0). 짐에 표가 없으면 짐이 깨진 것이라
        ERROR 다.
place — 길마다 조건이 서면 항목을 그 항목의 이긴 층에서 놓고, 안 서면 우리 것만 걷는다. 그 뒤 옛 기록(was)의 이름을 가르고,
        옛 자리를 백업으로 옮기고, 옛 기록 파일을 옮기고, 받는 쪽 홈의 러너를 알린다(아래 차례대로).
        import 는 한 자리에 길이 여럿일 수 있다 — 표지 사이에 조건이 서고 이긴 층이 있는 길마다 가져오기 한 줄을 표의
        차례로 두고, 줄이 하나도 없으면 블록을 걷는다. 폴더 항목의 길은 이긴 층의 항목 폴더 안 가져올 파일을 가리키고,
        그 파일이 없으면 그 줄을 빼고 WARN 을 낸다 — 없는 파일을 가리키는 가져오기는 Claude 가 말없이 건너뛴다.
check — place --dry-run 이 바꿀 것이 없으면 0, 있으면 그 줄과 함께 1, 층이나 표가 없으면(또는 못 재면) 2.

**이기는 단위는 항목이다** — 개인 층에 그 항목이 있으면 통째로 개인 층 것이다. 파일 단위로 섞으면 저장소에서 지운 룰이
  지난 릴리스의 표준 층에 남아 계속 깔린다. each 항목은 그 안의 폴더 하나(스킬 하나)가 단위다 — 이름마다 그 이름이 든 앞
  층(개인 → 표준)의 폴더가 통째로 간다. 저장소에서 지운 스킬이 새 짐을 깔 때까지 짐 판으로 놓이는 것은 받아들인 값이다.
**each 항목 놓기** — 놓을 이름은 길의 조건이 선 도구마다 두 층 이름의 합에서 그 도구의 not 과 keep 에 떨어지는 이름을 뺀
  것이다. 홈의 그 폴더가 없으면 쓰고, 링크면 백업으로 옮기고 쓰고, 기록에 그 폴더 아래 줄이 있으면 copy 그대로다. 기록에
  없으면(처음 만남) 파일 묶음과 바이트가 이긴 층과 같을 때(`__pycache__` 는 두 쪽 다 안 본다) 쓰지 않고 기록에만 올리고,
  다르면(파일이 더 있거나 모자라도) 폴더째 백업으로 옮기고 새로 쓴다 — 우리 것이 아닌 같은 이름 위에 파일 하나씩 덮으면
  사람의 파일이 우리 폴더에 섞여 남는다. 옮기기가 막히면(윈도에서 안의 파일이 열림) ERROR 를 내고 그 이름은 안 건드린다.
  처음 만남의 판정은 옛 기록과 무관하다 — 옛 기록은 걷기에만 쓰인다.
**걷기** — 기록에 있는데 이번에 안 놓는 파일(원본에서 빠졌다 · 칸을 껐다 · not 이 섰다)은 우리가 쓴 그대로면 지우고
  사람이 고쳤으면 백업으로 옮긴다. 걷은 뒤 비거나 `__pycache__` 만 남은 폴더는 copy 대상 폴더 아래에서 위로 걷는다 — 대상
  폴더 자체와 그 위는 그 도구 것이라 둔다.
**옛 기록(was)** — 손 전에 설치기 · 배포가 그 대상 폴더에 놓은 이름을 든 기록이다. place 첫머리에 한 번 읽는다. 이름만 있고
  해시가 없어 사람이 고쳤는지 못 가르므로, 옛 기록의 이름으로 걷는 것은 지우지 않고 늘 폴더째 백업으로 간다. 놓을 이름은
  처음 만남이 가르고, 아닌 이름은 —
    shared · 그 대상의 길 조건이 선다   — 폴더째 백업으로. 기록 파일을 옮긴다
    shared · 조건이 안 선다              — 기록 파일도 그 이름도 안 건드린다(설치기의 칸 없이 까는 걸음의 기록이다)
    shared 아님                          — 지금 어느 층의 그 항목에 있고 같은 대상의 shared 기록에 없으면 폴더째 백업으로.
                                           어느 층에도 없는 이름은 둔다(동료 저장소의 옛 배포가 민 그 사람 스킬일 수 있다) —
                                           그런 이름의 폴더가 홈에 남으면 기록 파일도 두어, 개인 층이 뒤에 서는 판에서 다음
                                           판이 마저 가른다
  기록에 그 폴더 아래 줄이 있는 이름은 손이 이미 맡아 걷기가 가르고, 링크인 대상 폴더 너머는 안 건드린다. 기록 파일은 옛
  자리까지 끝난 뒤 옮기고, 이름 하나라도 못 옮겼으면 둔다.
**옛 자리(old)** — 셋째 칸이 없으면 통째로 옮긴다. 옛 기록이면 그 기록들에 든 이름의 폴더만 옮기고(기록에 없는 것은 말없이
  둔다), 그렇게 옮겨 폴더가 비면 폴더도 옮긴다. was 에 안 든 그 기록 파일은 그 줄이 끝나면 옮긴다. list 면 목록 파일이
  우리가 써 온 꼴일 때만 옮긴다 — 맨 위 열쇠가 entries 하나 · 항목 하나 · 그 열쇠가 path 하나이고, 그 path 가 표의 다른
  old 폴더를 목록 파일 폴더 기준 상대 · `~/…` · 이 PC 홈의 절대 경로로 연다(`/` · `\\` · 끝 `/` · 대소문자 · BOM 을 안
  가린다). 그렇게 여는 항목이 다른 것과 섞였으면 WARN 을 내고 둔다 — 사람이 그 줄만 지운다.
**keep** — 다른 주인의 자리다. 그 아래를 쓰지도 · 걷지도 · 비키지도 · 기록하지도 않는다. 놓을 이름이 그 자리에 떨어지면
  WARN 을 내고 건너뛰고, keep 을 품은 copy 대상 폴더가 링크면 옮기지 않고 그 길을 ERROR 로 건너뛴다.
**받는 쪽 홈의 러너** — not 이름의 폴더가 그 도구의 홈(`*` 는 모든 홈)에 기록 밖으로 있으면 칸과 무관하게 WARN 한 줄을 내고
  둔다 — 우리 것이 아니다.
**놓기는 새 판의 손이 한다** — 손이 선 층 가운데 층 뿌리 표의 판 도장(`stamp` 줄 · 뽑는 자가 짐과 씨앗에 실리는 사본에
  찍는다)이 새 층의 손이 놓는다. 도장 없는 표(작업장 — 설정 저장소의 원본)와 못 읽는 표는 가장 새 판이고(못 읽으면 그
  층의 손이 받아 까닭을 낸다), 같으면 개인 층이다. 한 PC 에 지난 릴리스의 손(설치기)과 저장소의 손(배포)이 같이 있어,
  부른 쪽 손으로 놓으면 둘이 홈을 번갈아 고친다. 그래서 place · check 를 다른 손이 받으면 같은 인자로 그 손을 띄워 넘기고,
  그 줄을 이어 낸다. 넘겨받은 손은 다시 고르지 않고 제가 놓는다 — 고르는 법이 다른 두 판의 손이 서로 넘기며 맴돌지 않게.
  sync --dry-run 도 같이 넘긴다. 놓기를 맡을 손은 채워질 층을 셈에 넣은 뒤의 새 판(부른 손과 다른 층에 이미 선 손 가운데
  도장이 새것)이고, 넘겨받은 손이 채워질 층과 놓기를 다 셈한다 — 층에 실릴 손의 몸은 넘긴 손의 것으로 셈한다(실제 sync 는
  부른 손이 제 몸을 싣는다 · 넘김의 표지 값이 그 손의 자리다). 그 손을 못 띄우면(해석기가 진다 · 끝 줄이 없다) 부른 손이
  셈하되, 놓기를 맡을 층의 표를 못 읽으면 ERROR 가 아니라 WARN 한 줄과 채움 줄만 낸다.
**표 문법은 넓히기만 한다** — 새 판의 손은 옛 판의 표를 읽고, 있던 꼴의 뜻은 안 바뀐다. 옛 판의 손은 새 문법을 모를 수
  있어 놓기 미리보기도 새 판의 손이 한다.
**우리 것만 걷는다** — 표지 사이, 기록(`~/.paisetup/placed.tsv`)에 적은 해시 그대로인 파일, 우리가 써 온 옛 꼴(아래 OLD_*),
  옛 기록(was · old 의 기록 칸)이 말하는 이름의 폴더만 우리 것이다. 표지가 우리 것을 말하는 import · block 대상은 기록에 안 든다. 놓을 것이 없는 도구 폴더는 짓지 않는다.
  그 밖의 것을 덮거나 걷어야 하면 먼저 백업 자리(`~/.paisetup/backups/<시각>/<홈 기준 자리>` · 한 번 돌 때 한 자리 · 쓸 일이
  있을 때만)로 떠 두거나 옮긴다. 대상이 링크면 링크를 백업으로 옮기고 쓴다 — 링크 너머의 원본을 고치지 않는다.
  표지 짝이 안 맞으면 그 파일은 안 건드린다. 블록을 걷고 남은 글이 없으면 파일을 지운다.
**제작자 칸** — `--box` 가 없으면 사용자 값(윈도 레지스트리 `HKCU\\Environment`)을 먼저, 그다음 프로세스 값을 읽는다. 칸을
  바꾸기 전에 뜬 앱의 프로세스는 옛 값을 들고 있어 사용자 값이 진본이다. 쉼표 · 빈칸으로 가르고 대소문자를 안 가린다.
  빈 값(`--box ""` 도)은 claude 만, `none` 은 아무것도 아니다. 표에 없는 도구 이름은 WARN 을 내고 건너뛴다.
**한 번에 하나** — 잠금 파일 `~/.paisetup/.lock`. 잡혀 있으면 LOCK_WAIT 초까지 기다리고 못 잡으면 ERROR. 아무것도 안 쓰는
  판(--dry-run · check)은 잠금을 안 잡고 그 파일도 안 만든다.
**표가 틀리면 아무것도 안 한다** — 길 하나를 빼고 돌면 그 길이 놓은 파일이 「기록에 있는데 안 바라는 것」으로 걷힌다.

출력 계약 — 한 줄에 하나: `CHANGE=<동사> <자리> <까닭>`(세 칸은 탭으로 가른다) · `WARN=<까닭>` · `ERROR=<까닭>` · 끝에
  `CHANGED=0|1`. 동사는 fill(층을 원본으로 채운다) · drop(원본에 없는 층 항목을 걷는다) · write · remove · backup ·
  record(기록 `placed.tsv` 만 고친다)이고, 자리는 `~/` 로 연 홈 기준 자리다(폴더는 `/` 로 끝난다). --dry-run · check 는
  바꿀 줄을 같은 꼴로 낸다.
종료 — 0 됐다 · 1 ERROR 가 있었다(다른 대상은 계속 갔다). check 는 위의 0 · 1 · 2.
파이썬 3.8 이상 · 표준 라이브러리만 — 원격 컨테이너의 판을 우리가 못 정한다.
정한 자리 — 결정 0112 · 0113 · claude-config#133 「2 단계 첫 걸음 「규범 · 룰」」 코멘트와 그 뒤의 「계약 보탬」 코멘트들 ·
  「2 단계 둘째 걸음 「스킬」」 코멘트.
"""
import argparse
import collections
import datetime
import fnmatch
import hashlib
import json
import os
import pathlib
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

# ── 이름 붙인 값 — 한 벌 · 층 · 기록 · 표지 · 표의 낱말은 이 한 자리에 둔다 ─────────────────────────────────
HUB = '.paisetup'                      # 홈 아래 중립 한 벌
PERSONAL, STANDARD = 'personal', 'standard'
LAYERS = (PERSONAL, STANDARD)          # 이기는 차례 — 앞이 이긴다
TABLE = 'tool-homes.conf'              # 갈 곳 표 — 저장소 · 짐 · 층 뿌리가 다 같은 자리에 든다
HAND = 'tool-homes.py'                 # 층 뿌리에 실리는 손의 이름
LEDGER = 'placed.tsv'                  # 놓은 파일 기록 — `<홈 기준 자리>\t<sha256>` · 정렬 · BOM 없는 UTF-8
BACKUPS = 'backups'
BACKUP_STAMP = '%Y%m%d-%H%M%S'         # 같은 초에 두 번 돌면 `-2` · `-3` … 을 단다
LOCK = '.lock'
LOCK_WAIT = 15.0                       # 초 — 한 판은 1 초 안쪽이다. 느린 PC 에서도 남의 한 판을 넉넉히 기다리되 세션 시작을 오래 안 막는다
LOCK_POLL = 0.2
STAGE = '.tool-homes-'                 # 바꿔 끼우기 전에 곁에 짓는 자리의 이름 머리 — 남은 것은 다음 sync 가 걷는다
SKIP_DIRS = frozenset(['__pycache__'])
RELAYED = 'TOOL_HOMES_RELAYED'         # 넘김의 표지(환경 변수 · 값은 넘긴 손의 자리) — 있으면 다시 고르지 않고 제가 셈한다
RELAY_WARN = '놓기를 맡을 새 판의 표를 이 손이 못 읽는다 — 놓기 미리보기를 건너뛴다'
TILDE = '~/'
BOM = b'\xef\xbb\xbf'

BOX_VAR = 'PAISETUP_PERSONAL'
BOX_REG_KEY = 'Environment'            # HKCU 아래
BOX_NONE = 'none'
BOX_EMPTY = ('claude',)                # 칸 값이 비었을 때
BOX_SPLIT = re.compile(r'[,\s]+')

KIND_ITEM, KIND_ROUTE, KIND_OLD, KIND_STAMP = 'item', 'route', 'old', 'stamp'
KIND_NOT, KIND_KEEP, KIND_WAS = 'not', 'keep', 'was'
LOCAL = 'local'                        # item 줄의 표지 낱말 — 짐에 안 싣는 항목(뽑는 자가 읽는다)
EACH = 'each'                          # item 줄의 표지 낱말 — 항목 폴더 안의 폴더 하나하나가 이기는 단위이자 비키는 단위다
ITEM_FLAGS = (LOCAL, EACH)             # 다섯째 칸부터 · 차례가 없다
REPO_SPLIT = ','                       # item 줄 넷째 칸 — 저장소 자리 여럿(폴더 항목만)
ANY_TOOL = '*'                         # not 줄 넷째 칸 — 어느 홈에도
SHARED = 'shared'                      # was 줄 넷째 칸 — 설치기의 칸 없이 까는 걸음이 이 기록을 아직 쓴다
OLD_LISTED = 'list'                    # old 줄 셋째 칸 — 우리가 써 온 목록 꼴일 때만 옮긴다
LEDGER_SPLIT = ','                     # old 줄 셋째 칸 — 옛 기록 여럿
NAME_BARRED = ('/', '\\', ':')         # 옛 기록의 이름이 폴더 하나를 가리키지 않게 하는 글자 — 들면 그 줄을 안 센다
LIST_TOP, LIST_PATH = 'entries', 'path'   # agy 목록의 열쇠 — 우리는 이 둘만 썼다
LIST_OURS, LIST_MIXED = 'ours', 'mixed'
RUNNER_WARN = '받는 쪽 홈에 러너가 있다 · 우리 것이 아니라 안 걷는다'
ANY_WARN = '어느 홈에도 안 놓는 이름이 있다 · 우리 것이 아니라 안 걷는다'
STAMP = re.compile(r'\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z')   # UTC · 초까지 한 꼴이라야 글자 순이 곧 시간 순이다
IMPORT, BLOCK, LINES, INCLUDE, LIST, COPY = 'import', 'block', 'lines', 'include', 'list', 'copy'
COND_BOX = 'box'
FILE_FORMS = (IMPORT, BLOCK, LINES, INCLUDE, LIST)

ENTRY_BARRED = ('/', '..')             # 가져올 파일 칸을 열 수 없는 글자 — 항목 폴더 안의 상대 자리라야 한다

BEGIN = '<!-- paisetup:norms BEGIN -->'
END = '<!-- paisetup:norms END -->'
IMPORT_LINE = '@~/%s/%s/%s'            # HUB · 층 · 층 안의 자리(폴더 항목이면 뒤에 가져올 파일)

# Codex 블록의 글 — 홈에 이미 깔린 블록과 바이트 꼴이 같아야 다시 놓을 때 룰 줄의 자리(이긴 층)만 바뀐다
CODEX_HEAD = ('%s\n<!-- 설치 · 배포가 제작자 규범 원본에서 뽑아 쓴다. 여기서 고치면 다음 설치에 사라진다 — '
              '원본을 고친다. -->\n\n' % BEGIN)
CODEX_RULES_HEAD = ('\n## 영역 룰 — 파일을 만질 때만 걸리는 원칙\n\n'
                    '아래 파일을 만지기 전에 가리킨 룰을 읽고 따른다. 위 규범이 「룰이 든다」고 적은 자리가 이것들이다.\n\n')
CODEX_RULE_LINE = '- `%s` 를 만질 때는 `%s/%s` 를 먼저 읽는다'
CODEX_RULE_DESC = ' — '
RULE_GLOB = '*.md'
FRONT = re.compile(r'\A---\r?\n(.*?)\r?\n---\r?\n', re.S)

# agy — 앱은 목록의 `path` 로 드라이브 문자로 여는 절대 경로만 받고 CLI 는 `~/` 를 거절한다. 그래서 이 PC 홈의 절대 경로를
#   `/` 로 적고, BOM 없이 쓴다(BOM 이 붙으면 agy 가 목록을 JSON 으로 못 읽는다). 홈 경로에 `)` 가 들면 include 가 끊긴다.
INCLUDE_TEXT = '@[%s](%s)\n'
LIST_TEXT = '{\n  "entries": [\n    { "path": %s }\n  ]\n}\n'
# 우리 것으로 보는 옛 꼴 — 설치기 · 배포가 이 손을 부르기 전에 깐 글이 PC 에 남아 있다. `{home}` 은 이 PC 홈의 절대 경로(`/` 로)다
OLD_INCLUDE = ('@[norms](~/.claude/CLAUDE.md)', '@[norms](~/.paisetup/norms/norms.md)',
               '@[norms]({home}/.paisetup/norms/norms.md)')
OLD_LIST = ('../../.claude/rules', '../../.paisetup/norms/rules', '~/.paisetup/norms/rules',
            '{home}/.paisetup/norms/rules')

LINK_TAGS = (getattr(stat, 'IO_REPARSE_TAG_SYMLINK', 0xA000000C), getattr(stat, 'IO_REPARSE_TAG_MOUNT_POINT', 0xA0000003))

# path — 층 안의 자리 · repos — 설정 저장소 안의 자리들 · local · each — 표지 낱말
Item = collections.namedtuple('Item', 'name path repos local each')
# entry — 폴더 항목의 import 가 가리킬 항목 폴더 안의 파일(길 줄의 끝 칸). 다른 길에는 없다(None)
Route = collections.namedtuple('Route', 'item tool form target cond entry', defaults=(None,))
Not = collections.namedtuple('Not', 'item name tool')
Was = collections.namedtuple('Was', 'target ledger shared')
# ledgers — 옛 기록들(없으면 빈 묶음 — 통째로 옮긴다) · listed — 우리가 써 온 목록 꼴일 때만 옮긴다
Old = collections.namedtuple('Old', 'place ledgers listed')


class Busy(Exception):
    pass


# ── 출력 ─────────────────────────────────────────────────────────────────────────────────────────────────
class Out:
    def __init__(self):
        self.changed = False
        self.failed = False

    @staticmethod
    def _one(text):
        return re.sub(r'[\t\r\n]+', ' ', str(text))

    def line(self, text):
        print(text, flush=True)

    def change(self, verb, where, why):
        self.changed = True
        self.line('CHANGE=%s\t%s\t%s' % (verb, where, self._one(why)))

    def warn(self, why):
        self.line('WARN=' + self._one(why))

    def error(self, why):
        self.failed = True
        self.line('ERROR=' + self._one(why))

    def relay(self, text):
        """넘겨받은 손의 줄을 잇는다 — CHANGED 는 여기서 합쳐 끝에 한 번 낸다."""
        if text.startswith('CHANGED='):
            self.changed = self.changed or text.strip() == 'CHANGED=1'
            return
        if text.startswith('CHANGE='):
            self.changed = True
        elif text.startswith('ERROR='):
            self.failed = True
        self.line(text)

    def end(self):
        self.line('CHANGED=%d' % int(self.changed))


# ── 파일 손 ──────────────────────────────────────────────────────────────────────────────────────────────
def sha(data):
    return hashlib.sha256(data).hexdigest()


def is_link(p):
    """심볼릭 링크 · 정션 — 3.12 아래의 `islink` 는 윈도 정션을 못 본다."""
    try:
        st = os.lstat(str(p))
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    return getattr(st, 'st_reparse_tag', 0) in LINK_TAGS


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, part = tempfile.mkstemp(prefix=STAGE + path.name + '.', suffix='.part', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        if path.is_file() and not is_link(path):
            shutil.copymode(str(path), part)
        os.replace(part, str(path))
    except BaseException:
        if os.path.exists(part):
            os.remove(part)
        raise


def walk_files(top):
    """{폴더 안 상대 자리(/ 로): 파일} — 파이썬 캐시는 원본에 없는 것이 당연해 뺀다."""
    found = {}
    for d, dirs, files in os.walk(str(top)):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            p = pathlib.Path(d) / f
            found[pathlib.PurePath(os.path.relpath(str(p), str(top))).as_posix()] = p
    return found


def item_files(root, item_path):
    """층 `root` 아래 항목의 파일 — {상대 자리: 파일}(파일 항목은 열쇠가 빈 글 하나). 없거나 꼴이 다르면 None.
    층의 링크는 손이 지은 것이 아니라 항목으로 안 본다 — 원본 읽기는 `source_tree` 다."""
    p = root / item_path.rstrip('/')
    if item_path.endswith('/'):
        return walk_files(p) if p.is_dir() and not is_link(p) else None
    return {'': p} if p.is_file() else None


def real(p):
    """링크를 다 푼 자리 — 견주기용(윈도는 대소문자를 안 가린다)."""
    return os.path.normcase(os.path.realpath(str(p)))


def fold(rel):
    """홈 기준 자리(/ 로)를 견주기용으로 — 윈도는 대소문자를 안 가린다. normcase 와 달리 / 를 그대로 둔다."""
    return rel.lower() if os.name == 'nt' else rel


def at_or_under(child, parent):
    return child == parent or child.startswith(parent.rstrip(os.sep) + os.sep)


def source_tree(top, shown, out):
    """원본 폴더 항목의 파일 — {상대 자리(/ 로): 파일}. 링크를 따라간다(안의 폴더 · 파일도).

    제 조상 폴더(이 폴더에 이르는 길의 어느 폴더 · 그 위)를 가리키는 링크는 고리라 안 따라간다 — 같은 곳을 가리키는 두
    링크는 고리가 아니라 두 이름으로 다 선다. 끊긴 링크는 WARN 을 내고 그 자리만 건너뛴다. 파이썬 캐시는 원본에 없는 것이
    당연해 뺀다. `shown` 은 까닭 줄에 대는 항목 자리다.
    """
    found = {}
    top = pathlib.Path(os.path.abspath(str(top)))

    def visit(d, prefix, chain):
        try:
            entries = sorted(os.scandir(str(d)), key=lambda e: e.name)
        except OSError:
            return          # os.walk 와 같이 못 여는 폴더는 건너뛴다
        for e in entries:
            p, rel = pathlib.Path(e.path), prefix + e.name
            link = is_link(p)
            if link and not os.path.exists(e.path):
                out.warn('%s%s — 끊긴 링크다(가리키는 곳이 없다) · 그 자리만 건너뛴다' % (shown, rel))
            elif p.is_dir():
                where = real(p)
                if e.name in SKIP_DIRS or (link and any(at_or_under(c, where) for c in chain)):
                    continue
                visit(p, rel + '/', chain + [where])
            elif p.is_file():
                found[rel] = p
    visit(top, '', [real(top)] + [real(x) for x in top.parents])
    return found


def same_files(a, b):
    if set(a) != set(b):
        return False
    return all(a[k].read_bytes() == b[k].read_bytes() for k in a)


# ── 갈 곳 표 ─────────────────────────────────────────────────────────────────────────────────────────────
class Table:
    def __init__(self, items, routes, olds, stamp, nots=(), keeps=(), wases=()):
        self.items, self.routes, self.olds = items, routes, olds
        self.nots, self.keeps, self.wases = list(nots), list(keeps), list(wases)
        self.stamp = stamp                                 # 판 도장 — 없으면 None(작업장 · 가장 새 판)
        self.groups = collections.OrderedDict()            # 대상 → 길들(표의 차례)
        for r in routes:
            self.groups.setdefault(r.target, []).append(r)
        self.tools = sorted(set(r.tool for r in routes))

    def barred(self, item, name, tool):
        """not 줄이 그 이름을 그 도구의 홈에 안 놓게 하나."""
        return any(x.item == item and x.name == name and x.tool in (tool, ANY_TOOL) for x in self.nots)

    def route_of(self, target):
        """each 항목의 copy 길 — 그 대상 폴더로 가는 길 하나. 없으면 None."""
        for r in self.routes:
            if r.target == target and r.form == COPY and r.item in self.items and self.items[r.item].each:
                return r
        return None


def read_old(f, where, bad):
    """old 줄 — Old 하나. 꼴이 틀리면 까닭을 bad 에 더하고 None."""
    if len(f) == 2:
        return Old(f[1], (), False)
    if f[2] == OLD_LISTED:
        if f[1].endswith('/'):
            bad.append('%s — 목록 꼴(%s)을 둔 old 의 자리는 파일이다' % (where, OLD_LISTED))
            return None
        return Old(f[1], (), True)
    ledgers = tuple(f[2].split(LEDGER_SPLIT))
    if not f[1].endswith('/'):
        bad.append('%s — 옛 기록 칸을 둔 old 의 자리는 폴더다' % where)
    elif not all(x.startswith(TILDE) and not x.endswith('/') for x in ledgers):
        bad.append('%s — 옛 기록은 `~/` 로 연 파일이다' % where)
    else:
        return Old(f[1], ledgers, False)
    return None


def read_table(path):
    """(표, 틀린 까닭들). 표 파일이 없으면 (None, [])."""
    if not path.is_file():
        return None, []
    items, routes, olds, stamps, bad = collections.OrderedDict(), [], [], [], []
    nots, keeps, wases = [], [], []
    for n, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        f = raw.split()
        if not f or f[0].startswith('#'):
            continue
        where = '%s:%d' % (path.name, n)
        flags = f[4:]
        if f[0] == KIND_ITEM and 4 <= len(f) <= 6 and set(flags) <= set(ITEM_FLAGS) and len(set(flags)) == len(flags):
            repos = tuple(f[3].split(REPO_SPLIT))
            folder = f[2].endswith('/')
            if f[1] in items:
                bad.append('%s — 항목 이름이 겹친다(%s)' % (where, f[1]))
            elif not all(repos) or len(set(repos)) != len(repos):
                bad.append('%s — 저장소 자리가 비었거나 겹친다' % where)
            elif len(repos) > 1 and not folder:
                bad.append('%s — 저장소 자리 여럿은 폴더 항목만 든다' % where)
            elif any(r.endswith('/') != folder for r in repos):
                bad.append('%s — 층 안의 자리와 저장소 자리의 꼴(파일 · 폴더)이 다르다' % where)
            elif EACH in flags and not folder:
                bad.append('%s — %s 는 폴더 항목만 든다' % (where, EACH))
            items[f[1]] = Item(f[1], f[2], repos, LOCAL in flags, EACH in flags)
        elif f[0] == KIND_ROUTE and len(f) in (6, 7):
            routes.append(Route(*f[1:]))
        elif f[0] == KIND_NOT and len(f) == 4:
            nots.append(Not(*f[1:]))
        elif f[0] == KIND_KEEP and len(f) == 2 and f[1].startswith(TILDE):
            keeps.append(f[1])
        elif f[0] == KIND_WAS and (len(f) == 3 or (len(f) == 4 and f[3] == SHARED)):
            if not (f[1].startswith(TILDE) and f[1].endswith('/')):
                bad.append('%s — was 의 대상은 `~/` 로 연 폴더다' % where)
            elif not f[2].startswith(TILDE) or f[2].endswith('/'):
                bad.append('%s — was 의 옛 기록은 `~/` 로 연 파일이다' % where)
            else:
                wases.append(Was(f[1], f[2], len(f) == 4))
        elif f[0] == KIND_OLD and len(f) in (2, 3) and f[1].startswith(TILDE):
            old = read_old(f, where, bad)
            if old is not None:
                olds.append(old)
        elif f[0] == KIND_STAMP and len(f) == 2 and STAMP.match(f[1]):
            stamps.append(f[1])
        elif f[0] == KIND_STAMP:
            bad.append('%s — 판 도장은 `stamp <YYYY-MM-DDTHH:MM:SSZ>` 꼴이다' % where)
        else:
            bad.append('%s — 모르는 줄이다' % where)
    if len(stamps) > 1:
        bad.append('%s — 판 도장이 %d 줄이다' % (path.name, len(stamps)))
    for r in routes:
        item = items.get(r.item)
        folder_item = item is not None and item.path.endswith('/')
        if item is None:
            bad.append('길 %s → %s — 표에 없는 항목이다' % (r.item, r.target))
        elif r.cond != COND_BOX:
            bad.append('길 %s → %s — 모르는 조건이다(%s)' % (r.item, r.target, r.cond))
        elif not r.target.startswith(TILDE):
            bad.append('길 %s → %s — 자리는 `~/` 로 연다' % (r.item, r.target))
        elif r.form not in FILE_FORMS + (COPY,):
            bad.append('길 %s → %s — 모르는 꼴이다(%s)' % (r.item, r.target, r.form))
        elif item.each and r.form != COPY:
            bad.append('길 %s → %s — %s 항목의 길은 copy 만 선다' % (r.item, r.target, EACH))
        elif r.form == COPY and not (r.target.endswith('/') and folder_item):
            bad.append('길 %s → %s — copy 는 폴더 항목을 폴더에 놓는다' % (r.item, r.target))
        elif r.form in FILE_FORMS and r.target.endswith('/'):
            bad.append('길 %s → %s — %s 의 자리는 파일이다' % (r.item, r.target, r.form))
        elif r.form == BLOCK and folder_item:
            bad.append('길 %s → %s — block 은 파일 항목을 쓴다' % (r.item, r.target))
        elif r.form == LINES and not folder_item:
            bad.append('길 %s → %s — lines 는 폴더 항목을 쓴다' % (r.item, r.target))
        elif r.form == IMPORT and folder_item and r.entry is None:
            bad.append('길 %s → %s — 폴더 항목의 import 는 가져올 파일 칸이 선다' % (r.item, r.target))
        elif r.form == IMPORT and folder_item and r.entry.startswith(ENTRY_BARRED):
            bad.append('길 %s → %s — 가져올 파일은 항목 폴더 안의 상대 자리다(%s 로 열 수 없다)'
                       % (r.item, r.target, ' · '.join(ENTRY_BARRED)))
        elif r.entry is not None and not (r.form == IMPORT and folder_item):
            bad.append('길 %s → %s — 가져올 파일 칸은 폴더 항목의 import 만 쓴다' % (r.item, r.target))
    tools = set(r.tool for r in routes)
    for x in nots:
        item = items.get(x.item)
        if item is None or not item.each:
            bad.append('not %s %s — %s 항목이 아니다' % (x.item, x.name, EACH))
        elif x.tool != ANY_TOOL and x.tool not in tools:
            bad.append('not %s %s — 표에 없는 도구다(%s)' % (x.item, x.name, x.tool))
    table = Table(items, routes, olds, stamps[0] if len(stamps) == 1 else None, nots, keeps, wases)
    for w in wases:
        if table.route_of(w.target) is None:
            bad.append('was %s — %s 항목의 copy 길 대상이 아니다' % (w.target, EACH))
    for target, rs in table.groups.items():
        forms = [r.form for r in rs]
        if forms.count(BLOCK) == 1 and forms[0] == BLOCK and all(x == LINES for x in forms[1:]):
            continue
        if all(x == IMPORT for x in forms):
            continue        # 한 자리에 import 길이 여럿 설 수 있다 — 길마다 한 줄
        if len(forms) == 1 and forms[0] in (INCLUDE, LIST, COPY):
            continue
        bad.append('자리 %s — 한 자리에 맞지 않는 꼴들이다(%s)' % (target, ' · '.join(forms)))
    return table, bad


def source_files(item, layer, root, out):
    """채울 파일 — {층 안 상대 자리: 원본 파일}. 그 층에 이 항목이 안 서면 None.

    표준 층은 짐의 층 안의 자리, 개인 층은 표의 저장소 자리에서 읽는다 — 저장소 자리가 여럿이면 한 폴더로 합치고, 같은
    이름(항목 폴더 바로 밑)이 두 자리에 다 있으면 그 이름만 ERROR 를 내고 안 싣는다(다른 층이 이긴다). 링크는 따라간다
    (항목 자리 자체도). 그 자리가 없으면 조용히 안 선다. 개인 층의 저장소 자리가 있는데 꼴이 표와 다르면(끊긴 링크도)
    WARN 을 내고 그 자리를 이 층에서 뺀다 — 원본을 두었는데 안 깔리는 까닭이 보이게. each 항목의 뿌리에 바로 든 파일은
    단위가 아니라 WARN 을 내고 안 싣는다.
    """
    rels = (item.path,) if layer == STANDARD else item.repos
    if not item.path.endswith('/'):
        p = root / rels[0]
        got = {'': p} if p.is_file() else None
        if got is None and layer == PERSONAL and os.path.lexists(str(p)):
            out.warn('%s — 저장소 자리 %s 의 꼴이 표와 다르다 · 개인 층에서 이 항목을 뺀다' % (item.name, rels[0]))
        return got
    parts = []
    for rel in rels:
        p = root / rel.rstrip('/')
        got = source_tree(p, rel, out) if p.is_dir() else None
        if got is None:
            if layer == PERSONAL and os.path.lexists(str(p)):
                out.warn('%s — 저장소 자리 %s 의 꼴이 표와 다르다 · 개인 층에서 %s' % (
                    item.name, rel, '이 항목을 뺀다' if len(rels) == 1 else '그 자리를 뺀다'))
            continue
        if item.each:
            for k in sorted(k for k in got if '/' not in k):
                out.warn('%s%s — %s 항목의 뿌리에 바로 든 파일은 단위가 아니다 · 층에 안 싣는다' % (rel, k, item.name))
                del got[k]
        parts.append((rel, got))
    if len(parts) < 2:
        return parts[0][1] if parts else None
    owners = collections.OrderedDict()
    for rel, got in parts:
        for name in sorted(set(k.split('/', 1)[0] for k in got)):
            owners.setdefault(name, []).append(rel)
    clash = set()
    for name, where in owners.items():
        if len(where) > 1:
            clash.add(name)
            out.error('%s — 같은 이름 %s 가 저장소 자리 %s 에 다 있다 · 개인 층에 안 싣는다(다른 층이 이긴다)'
                      % (item.name, name, ' · '.join(where)))
    return dict((k, p) for rel, got in parts for k, p in got.items() if k.split('/', 1)[0] not in clash)


# ── 제작자 칸 ────────────────────────────────────────────────────────────────────────────────────────────
def box_raw():
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, BOX_REG_KEY) as k:
                value = winreg.QueryValueEx(k, BOX_VAR)[0]
            if isinstance(value, str) and value.strip():
                return value
        except OSError:
            pass
    return os.environ.get(BOX_VAR, '')


def read_box(given, tools, out):
    raw = box_raw() if given is None else given
    names = [n for n in BOX_SPLIT.split(raw.strip().lower()) if n]
    if not names:
        return set(BOX_EMPTY)
    box = set()
    for n in names:
        if n == BOX_NONE:
            continue
        if n in tools:
            box.add(n)
        else:
            out.warn('제작자 칸에 모르는 이름이 있다 — %s (건너뛴다 · 표의 도구: %s)' % (n, ' · '.join(tools)))
    return box


# ── 잠금 ─────────────────────────────────────────────────────────────────────────────────────────────────
class Lock:
    def __init__(self, hub):
        self.path = hub / LOCK
        self.fd = None

    def _try(self):
        os.lseek(self.fd, 0, os.SEEK_SET)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(str(self.path), os.O_RDWR | os.O_CREAT, 0o644)
        deadline = time.monotonic() + LOCK_WAIT
        while True:
            try:
                self._try()
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    os.close(self.fd)
                    raise Busy('잠금을 못 잡았다 — 다른 손이 %g 초 넘게 돌고 있다(%s)' % (LOCK_WAIT, self.path)) from None
                time.sleep(LOCK_POLL)

    def __exit__(self, *exc):
        try:
            os.lseek(self.fd, 0, os.SEEK_SET)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)


# ── 층 채우기 ────────────────────────────────────────────────────────────────────────────────────────────
def sweep_stage(root, table):
    """앞 판이 죽으며 남긴 짓는 자리를 걷는다 — 잠금 안에서만 부른다. 못 걷은 것은 다음 판이 다시 걷는다."""
    parents = set([root]) | set((root / i.path.rstrip('/')).parent for i in table.items.values())
    for d in parents:
        if not d.is_dir():
            continue
        for e in d.iterdir():
            if not e.name.startswith(STAGE):
                continue
            if e.is_dir() and not is_link(e):
                shutil.rmtree(str(e), ignore_errors=True)
            else:
                try:
                    e.unlink()
                except OSError:
                    pass


def swap_in(dest, folder, files):
    """항목을 곁에 다 지은 뒤 바꿔 끼운다. 옛 것을 비키지 못하면 OSError — 옛 항목은 그대로다."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not folder:
        if dest.is_dir() and not is_link(dest):
            take_out(dest)
        write_atomic(dest, files[''].read_bytes())
        return
    tag = '%s%s.%d' % (STAGE, dest.name, os.getpid())
    new, old = dest.parent / (tag + '.new'), dest.parent / (tag + '.old')
    new.mkdir()
    try:
        for rel, src in files.items():
            t = new / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(src), str(t))
        moved = False
        if os.path.lexists(str(dest)):
            os.rename(str(dest), str(old))   # 윈도에서 안의 파일을 누가 열어 두었으면 여기서 막힌다
            moved = True
        try:
            os.rename(str(new), str(dest))
        except OSError:
            if moved:
                os.rename(str(old), str(dest))
            raise
    except BaseException:
        if new.exists():
            shutil.rmtree(str(new))
        raise
    if moved:
        shutil.rmtree(str(old), ignore_errors=True)   # 못 걷은 것은 다음 sync 의 sweep_stage 가 걷는다


def take_out(dest):
    """층의 항목을 걷는다 — 폴더는 먼저 이름을 비켜, 막히면 하나도 안 지운 채 OSError 를 낸다."""
    if dest.is_dir() and not is_link(dest):
        old = dest.parent / ('%s%s.%d.old' % (STAGE, dest.name, os.getpid()))
        os.rename(str(dest), str(old))
        shutil.rmtree(str(old), ignore_errors=True)
    else:
        dest.unlink()


def strays(root, table):
    """층 안에서 표의 항목 · 손 · 표가 아닌 자리 — 층에는 그것들만 든다. 짓는 자리는 sweep_stage 몫이라 뺀다."""
    items = set(i.path.rstrip('/') for i in table.items.values())
    above = set()
    for p in items:
        parts = p.split('/')
        above |= set('/'.join(parts[:n]) for n in range(1, len(parts)))
    found = []

    def visit(d, prefix):
        for e in sorted(d.iterdir(), key=lambda x: x.name):
            rel = prefix + e.name
            if e.name.startswith(STAGE) or rel in items or (not prefix and e.name in (TABLE, HAND)):
                continue
            if rel in above and e.is_dir() and not is_link(e):
                visit(e, rel + '/')
            else:
                found.append(e)
    if root.is_dir() and not is_link(root):
        visit(root, '')
    return found


def fill_layer(home, layer, table, fills, selves, out, dry):
    root = home / HUB / layer
    if not dry:
        sweep_stage(root, table)
    for e in strays(root, table):
        shown = '%s%s/%s/%s%s' % (TILDE, HUB, layer, pathlib.PurePath(os.path.relpath(str(e), str(root))).as_posix(),
                                  '/' if e.is_dir() and not is_link(e) else '')
        try:
            if not dry:
                take_out(e)
            out.change('drop', shown, '표에 없는 자리다')
        except Exception as x:  # noqa: BLE001
            out.error('%s — 못 걷었다 (%s: %s)' % (shown, type(x).__name__, x))
    for item in table.items.values():
        new = fills[item.name]
        dest = root / item.path.rstrip('/')
        shown = '%s%s/%s/%s' % (TILDE, HUB, layer, item.path)
        cur = item_files(root, item.path)
        try:
            if new is None:
                if cur is None and not os.path.lexists(str(dest)):
                    continue
                if not dry:
                    take_out(dest)
                out.change('drop', shown, '원본에 이 항목이 없다')
            elif cur is None or not same_files(cur, new):
                if not dry:
                    swap_in(dest, item.path.endswith('/'), new)
                out.change('fill', shown, '층에 없다' if cur is None else '원본과 다르다')
        except Exception as e:  # noqa: BLE001 — 한 항목이 막혀도 나머지는 간다
            out.error('%s — 바꿔 끼우지 못했다 · 옛 항목을 그대로 둔다 (%s: %s)' % (shown, type(e).__name__, e))
    for name, src in selves:   # 손을 마지막에 — 손이 서야 이 층이 놓기를 맡는다
        dest = root / name
        data = src.read_bytes()
        if dest.is_file() and dest.read_bytes() == data:
            continue
        try:
            if not dry:
                write_atomic(dest, data)
            out.change('fill', '%s%s/%s/%s' % (TILDE, HUB, layer, name), '제 몸을 층 뿌리에 싣는다')
        except Exception as e:  # noqa: BLE001
            out.error('%s%s/%s/%s — 못 실었다 (%s: %s)' % (TILDE, HUB, layer, name, type(e).__name__, e))


# ── 놓기 ─────────────────────────────────────────────────────────────────────────────────────────────────
class Run:
    """한 번의 놓기 — 홈 · 기록 · 이번 판의 백업 자리. dry 면 아무것도 안 쓰고 줄만 낸다."""

    def __init__(self, home, dry, out):
        self.home, self.dry, self.out = home, dry, out
        self.hub = home / HUB
        self.home_abs = str(home).replace('\\', '/').rstrip('/')
        self.ledger = read_ledger(self.hub / LEDGER)
        self.ledger_was = dict(self.ledger)
        self._backup_root = None
        self.gone = set()       # 이번 판에 지웠거나 옮긴 자리(홈 기준) — --dry-run 도 세어, 뒤 판정이 바뀐 뒤의 홈을 본다
        self.keeps = []         # keep 자리(홈 기준 · 끝 / 없이 · fold 로)

    def gone_at(self, rel):
        parts = rel.rstrip('/').split('/')
        return any('/'.join(parts[:n]) in self.gone for n in range(1, len(parts) + 1))

    def present(self, p):
        """홈에 있고 이번 판에 지우거나 옮기지 않았다."""
        return os.path.lexists(str(p)) and not self.gone_at(self.rel(p))

    def kept(self, rel):
        """그 자리가 keep 자리이거나 그 아래다 — 다른 주인의 자리라 쓰지도 · 걷지도 · 비키지도 · 기록하지도 않는다."""
        r = fold(rel.rstrip('/'))
        return any(r == k or r.startswith(k + '/') for k in self.keeps)

    def holds_keep(self, rel):
        """그 자리 아래(그 자리 자체도)에 keep 자리가 있다."""
        r = fold(rel.rstrip('/'))
        return any(k == r or k.startswith(r + '/') for k in self.keeps)

    def left_in(self, p, cache_too=False):
        """폴더에 이번 판 뒤에도 남는 것이 있나 — 지웠거나 옮긴 것은 안 센다. cache_too 가 아니면 __pycache__ 도 안 센다."""
        with os.scandir(str(p)) as it:
            entries = list(it)
        for e in entries:
            q = pathlib.Path(e.path)
            if self.gone_at(self.rel(q)):
                continue
            if not cache_too and e.name in SKIP_DIRS and e.is_dir(follow_symlinks=False) and not is_link(q):
                continue
            return True
        return False

    def at(self, target):
        return self.home / target[len(TILDE):].rstrip('/')

    def rel(self, p):
        return pathlib.PurePath(os.path.relpath(str(p), str(self.home))).as_posix()

    def show(self, p):
        return TILDE + self.rel(p) + ('/' if p.is_dir() and not is_link(p) else '')

    def backup_root(self):
        if self._backup_root is None:
            base = self.hub / BACKUPS / datetime.datetime.now().strftime(BACKUP_STAMP)
            n = 1
            while True:
                cand = base if n == 1 else base.with_name('%s-%d' % (base.name, n))
                try:
                    cand.mkdir(parents=True)
                except FileExistsError:
                    n += 1
                    continue
                self._backup_root = cand
                break
        return self._backup_root

    def backup(self, p, move, why):
        shown = self.show(p)
        moved = move or is_link(p)
        if not self.dry:
            dest = self.backup_root() / self.rel(p)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if moved and dest.is_dir() and p.is_dir() and not is_link(p) and not os.listdir(str(p)):
                os.rmdir(str(p))    # 안의 것을 이번 판에 먼저 옮겨 백업 자리에 그 폴더가 이미 섰다 — 빈 폴더만 걷으면 옮긴 것이다
            elif moved:
                os.rename(str(p), str(dest))
            else:
                shutil.copy2(str(p), str(dest))
        if moved:
            self.gone.add(self.rel(p))
        self.out.change('backup', shown, why)

    def write(self, p, data, why):
        if not self.dry:
            write_atomic(p, data)
        self.out.change('write', TILDE + self.rel(p), why)

    def remove(self, p, why):
        if not self.dry:
            p.unlink()
        self.gone.add(self.rel(p))
        self.out.change('remove', TILDE + self.rel(p), why)

    def remove_dir(self, p, why):
        """빈 폴더(__pycache__ 만 남은 것도)를 걷는다 — 다른 것이 남았으면 os.rmdir 이 막는다."""
        if not self.dry:
            with os.scandir(str(p)) as it:
                caches = [pathlib.Path(e.path) for e in it if e.name in SKIP_DIRS and e.is_dir(follow_symlinks=False)]
            for q in caches:
                if not is_link(q):
                    shutil.rmtree(str(q))
            os.rmdir(str(p))
        self.gone.add(self.rel(p))
        self.out.change('remove', TILDE + self.rel(p) + '/', why)

    def record(self, key, digest, why):
        if digest is None:
            self.ledger.pop(key, None)
        else:
            self.ledger[key] = digest
        if why:
            self.out.change('record', TILDE + key, why)

    def save(self):
        if self.dry or self.ledger == self.ledger_was:
            return
        text = ''.join('%s\t%s\n' % (k, self.ledger[k]) for k in sorted(self.ledger))
        write_atomic(self.hub / LEDGER, text.encode('utf-8'))


def read_ledger(path):
    found = {}
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            parts = line.split('\t')
            if len(parts) == 2 and parts[0] and parts[1]:
                found[parts[0]] = parts[1]
    return found


def field(front, key):
    """머리말의 한 줄 값 — 감싼 따옴표를 걷는다. 없으면 빈 글."""
    m = re.search(r'^%s:\s*(.+?)\s*$' % re.escape(key), front, re.M)
    return m.group(1).strip('"\'') if m else ''


def rule_lines(files, rules_home):
    """폴더 항목 바로 밑의 `*.md` 마다 한 줄 — 차례는 이 플랫폼의 경로 차례(윈도는 대소문자를 안 가린다)다."""
    out = []
    names = [k for k in files if '/' not in k and fnmatch.fnmatch(k, RULE_GLOB)]
    for name in sorted(names, key=pathlib.PurePath):
        m = FRONT.match(files[name].read_text(encoding='utf-8-sig'))
        front = m.group(1) if m else ''
        globs, desc = field(front, 'globs'), field(front, 'description')
        if not globs:
            continue
        line = CODEX_RULE_LINE % (globs, rules_home, name)
        out.append(line + (CODEX_RULE_DESC + desc if desc else ''))
    return out


def codex_block(norms_file, rule_sets):
    """규범 본문 + 룰마다 「이 파일들을 만질 때 이 룰을 먼저 읽는다」 한 줄. rule_sets — [(가리킬 자리, 파일들)]."""
    norms = norms_file.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
    body = norms.rstrip() + '\n'
    lines = []
    for rules_home, files in rule_sets:
        lines += rule_lines(files, rules_home)
    if lines:
        body += CODEX_RULES_HEAD + '\n'.join(lines) + '\n'
    return CODEX_HEAD + body + END + '\n'


def merge(current, new_block):
    """(결과, 까닭). 까닭이 있으면 못 고친다. `new_block` 이 빈 글이면 블록을 걷는다."""
    nb, ne = current.count(BEGIN), current.count(END)
    if nb == 0 and ne == 0:
        if not new_block:
            return current, ''
        if not current.strip():
            return new_block, ''
        return current.rstrip('\r\n') + '\n\n' + new_block, ''
    if nb != 1 or ne != 1 or current.index(BEGIN) > current.index(END):
        return None, '표지 짝이 안 맞는다(BEGIN %d · END %d) — 안 건드린다' % (nb, ne)
    i, j = current.index(BEGIN), current.index(END) + len(END)
    rest = current[j:]
    rest = rest[1:] if rest.startswith('\n') else rest[2:] if rest.startswith('\r\n') else rest
    head = current[:i]
    if not new_block:   # 걷기 — 붙일 때 앞에 둔 빈 줄 하나도 같이 걷는다
        head = head[:-1] if head.endswith('\n\n') else head
        return (head + rest) if (head + rest).strip() else '', ''
    return head + new_block + rest, ''


def place_marked(run, path, text, whole_is_old):
    """표지 사이를 text 로 — 빈 글이면 블록을 걷는다. whole_is_old 면 표지 없는 파일을 옛 통째 사본으로 본다."""
    link = is_link(path)
    if path.is_dir() and not link:
        raise ValueError('파일 자리에 폴더가 있다')
    raw = path.read_bytes() if path.is_file() else b''
    current = raw.decode('utf-8-sig')
    crlf = '\r\n' in current
    lf = current.replace('\r\n', '\n')
    old_copy = whole_is_old and BEGIN not in lf and END not in lf and lf.strip() != ''
    if old_copy:
        if not text:
            return          # 끈 칸 — 표지 없는 파일은 우리 것이라 할 수 없다
        merged = text
    else:
        merged, why = merge(lf, text)
        if why:
            run.out.error('%s — %s' % (TILDE + run.rel(path), why))
            return
    if crlf:
        merged = merged.replace('\n', '\r\n')
    data = merged.encode('utf-8')
    if raw.startswith(BOM) and merged:
        data = BOM + data
    if data == raw and not (link and text):
        return
    there = os.path.lexists(str(path))
    if link:
        run.backup(path, True, '링크다 — 걷고 파일로 쓴다')
        there = False
    elif old_copy:
        run.backup(path, False, '표지가 없다 — 옛 통째 사본으로 보고 블록만 쓴다')
    if merged.strip():
        run.write(path, data, '표지 사이를 원본으로' if text else '블록을 걷는다 · 표지 밖 글은 둔다')
    elif there:
        run.remove(path, '블록을 걷고 남은 글이 없다')


def import_line(run, route, item, got):
    """import 길 하나의 가져오기 줄 — 조건이 안 서거나 이긴 층이 없으면(got 이 None) None. 폴더 항목은 이긴 층의 항목
    폴더 안 가져올 파일을 가리키고, 그 파일이 없으면 None 과 WARN 이다."""
    if not got:
        return None
    layer, files = got
    if route.entry is None:
        return IMPORT_LINE % (HUB, layer, item.path)
    if route.entry not in files:
        run.out.warn('%s — 이긴 층(%s)의 %s 에 가져올 파일 %s 가 없다 · 그 가져오기 줄을 뺀다'
                     % (route.target, layer, item.path, route.entry))
        return None
    return IMPORT_LINE % (HUB, layer, item.path + route.entry)


def agy_target(run, layer, item):
    return '%s/%s/%s/%s' % (run.home_abs, HUB, layer, item.path.rstrip('/'))


def agy_text(run, form, layer, item):
    target = agy_target(run, layer, item)
    if form == INCLUDE:
        return INCLUDE_TEXT % (item.name, target)
    return LIST_TEXT % json.dumps(target, ensure_ascii=False)


def is_ours(run, form, path, raw, item):
    """include · list 파일이 우리 것인가 — 기록의 해시 그대로이거나 우리가 쓴 꼴 그대로(덧붙은 열쇠가 없다)."""
    if run.ledger.get(run.rel(path)) == sha(raw):
        return True
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return False
    if form == INCLUDE:
        shapes = set(s.format(home=run.home_abs) for s in OLD_INCLUDE)
        shapes |= set(agy_text(run, INCLUDE, layer, item).strip() for layer in LAYERS)
        return text.strip() in shapes
    paths = set(s.format(home=run.home_abs) for s in OLD_LIST) | set(agy_target(run, layer, item) for layer in LAYERS)
    try:
        doc = json.loads(text)
    except ValueError:
        return False
    if not (isinstance(doc, dict) and list(doc) == ['entries'] and isinstance(doc['entries'], list)
            and len(doc['entries']) == 1):
        return False
    entry = doc['entries'][0]
    return isinstance(entry, dict) and list(entry) == ['path'] and entry['path'] in paths


def place_whole(run, path, text, form, item):
    """파일 통째로 우리 것인 꼴(include · list). text 가 None 이면 우리 것만 걷는다."""
    key = run.rel(path)
    link = is_link(path)
    if path.is_dir() and not link:
        raise ValueError('파일 자리에 폴더가 있다')
    raw = path.read_bytes() if path.is_file() else None
    if text is not None:
        data = text.encode('utf-8')
        if raw == data and not link:
            if run.ledger.get(key) != sha(data):
                run.record(key, sha(data), '같은 바이트가 이미 있다 — 기록에 올린다')
            return
        if link:
            run.backup(path, True, '링크다 — 걷고 파일로 쓴다')
        elif raw is not None and not is_ours(run, form, path, raw, item):
            run.backup(path, False, '우리가 쓴 꼴이 아니다')
        run.write(path, data, '이 PC 홈의 절대 경로로 이긴 층을 가리킨다')
        run.record(key, sha(data), None)
        return
    if raw is not None and not link and is_ours(run, form, path, raw, item):
        run.remove(path, '칸을 껐거나 항목이 없다 · 우리 것이다')
        run.record(key, None, None)
    elif key in run.ledger:
        run.record(key, None, '놓은 파일이 없다' if raw is None else '우리 것이 아니게 됐다 — 둔다')


def open_folder(run, folder, prefix, link_dirs, fresh_dirs):
    """copy 길의 대상 폴더가 링크면 백업으로 옮기고 폴더로 쓴다 — 그랬으면 True. keep 을 품은 링크는 안 옮기고 ERROR 와
    None 이다(그 길을 건너뛴다)."""
    if not link_dirs[prefix]:
        return False
    if run.holds_keep(prefix):
        run.out.error('%s — 링크인데 다른 주인의 자리(keep)를 품었다 · 안 옮기고 이 길을 건너뛴다' % (TILDE + prefix))
        return None
    run.backup(folder, True, '링크다 — 걷고 폴더로 쓴다')
    link_dirs[prefix] = False
    fresh_dirs.add(prefix)
    return True


def copy_files(run, folder, prefix, files, fresh, desired):
    """파일마다 — 없으면 쓰고, 같으면 두고(기록에 없으면 올리고), 기록 해시 그대로면 덮고, 사람이 고쳤으면 떠 두고 덮는다."""
    for rel in sorted(files):
        dest = folder / rel
        key = prefix + rel
        if run.kept(key):
            run.out.warn('%s — 다른 주인의 자리(keep)다 · 안 놓는다' % (TILDE + key))
            continue
        desired.add(key)
        try:
            data = files[rel].read_bytes()
            want = sha(data)
            if fresh or not os.path.lexists(str(dest)):
                run.write(dest, data, '새로 놓는다')
            elif is_link(dest):
                run.backup(dest, True, '링크다 — 걷고 파일로 쓴다')
                run.write(dest, data, '이긴 층에서 놓는다')
            elif dest.is_dir():
                run.out.error('%s — 파일 자리에 폴더가 있다 · 안 건드린다' % (TILDE + key))
                continue
            else:
                cur = sha(dest.read_bytes())
                if cur == want:
                    if run.ledger.get(key) != want:
                        run.record(key, want, '같은 바이트가 이미 있다 — 기록에 올린다')
                    continue
                if run.ledger.get(key) != cur:
                    run.backup(dest, False, '기록에 없거나 사람이 고쳤다')
                run.write(dest, data, '원본과 다르다')
            run.record(key, want, None)
        except Exception as e:  # noqa: BLE001 — 파일 하나가 막혀도 나머지는 간다
            run.out.error('%s — %s: %s' % (TILDE + key, type(e).__name__, e))


def place_copy(run, route, got, link_dirs, fresh_dirs, desired):
    folder = run.at(route.target)
    prefix = run.rel(folder) + '/'
    link_dirs[prefix] = is_link(folder)
    if got is None:
        return              # 걷기는 기록 훑기(sweep_ledger)가 한다
    fresh = open_folder(run, folder, prefix, link_dirs, fresh_dirs)
    if fresh is not None:
        copy_files(run, folder, prefix, got[1], fresh, desired)


def owned(ledger, top):
    """기록에 그 폴더(top — 끝이 /) 아래 줄이 있다."""
    return any(k.startswith(top) for k in ledger)


def units(files):
    """each 항목의 파일을 이름마다 — {이름: {그 폴더 안 상대 자리: 파일}}. 항목 뿌리에 바로 든 파일은 단위가 아니라 뺀다."""
    found = {}
    for rel, p in files.items():
        if '/' in rel:
            name, rest = rel.split('/', 1)
            found.setdefault(name, {})[rest] = p
    return found


def place_each(run, table, route, got, link_dirs, fresh_dirs, desired):
    """each 항목의 copy 길 — 이름마다 이긴 층의 폴더를 통째로 놓는다. got — {이름: (층, 파일들)} · 조건이 안 서면 None.
    돌려주는 것은 놓을 이름들이다(not 과 keep 에 떨어지는 이름을 뺀다)."""
    folder = run.at(route.target)
    prefix = run.rel(folder) + '/'
    link_dirs[prefix] = is_link(folder)
    if got is None:
        return set()
    names = []
    for name in sorted(got):
        if table.barred(route.item, name, route.tool):
            continue
        if run.kept(prefix + name) or run.holds_keep(prefix + name):
            run.out.warn('%s%s%s/ — 다른 주인의 자리(keep)에 떨어진다 · 안 놓는다' % (TILDE, prefix, name))
            continue
        names.append(name)
    if not names:
        return set()
    fresh = open_folder(run, folder, prefix, link_dirs, fresh_dirs)
    if fresh is None:
        return set()
    for name in names:
        place_unit(run, folder, prefix, name, got[name][1], fresh, desired)
    return set(names)


def place_unit(run, folder, prefix, name, files, fresh, desired):
    """이름 하나 — 홈의 그 폴더가 없으면 쓰고, 링크면 백업으로 옮기고 쓰고, 기록에 그 폴더 아래 줄이 있으면 copy 그대로다.
    기록에 없으면(처음 만남) 파일 묶음과 바이트가 이긴 층과 같으면(__pycache__ 는 두 쪽 다 안 본다) 쓰지 않고 기록에만
    올리고, 다르면 폴더째 백업으로 옮기고 새로 쓴다 — 옮기기가 막히면 ERROR 를 내고 그 이름은 안 건드린다(섞어 쓰지 않는다)."""
    unit = folder / name
    top = prefix + name + '/'
    try:
        if not fresh and os.path.lexists(str(unit)):
            if is_link(unit):
                run.backup(unit, True, '링크다 — 걷고 폴더로 쓴다')
                fresh = True
            elif not owned(run.ledger, top):
                there = walk_files(unit) if unit.is_dir() else None
                if there is not None and same_files(there, files):
                    for rel in sorted(files):
                        desired.add(top + rel)
                        run.record(top + rel, sha(files[rel].read_bytes()), '같은 바이트가 이미 있다 — 기록에 올린다')
                    return
                try:
                    run.backup(unit, True, '기록에 없는 같은 이름이 원본과 다르다 — 폴더째 비킨다')
                except OSError as e:
                    run.out.error('%s — 폴더째 못 옮겼다 · 이 이름은 안 건드린다 (%s: %s)' % (TILDE + top, type(e).__name__, e))
                    return
                fresh = True
    except Exception as e:  # noqa: BLE001 — 이름 하나가 막혀도 나머지는 간다
        run.out.error('%s — %s: %s' % (TILDE + top, type(e).__name__, e))
        return
    copy_files(run, unit, top, files, fresh, desired)


def sweep_ledger(run, desired, whole, link_dirs, fresh_dirs, tops):
    """기록에 있는데 이번에 바라지 않는 파일 — 우리가 쓴 그대로면 지우고, 사람이 고쳤으면 백업으로 옮긴다. 그 뒤 빈 폴더를
    걷는다(clear_empty)."""
    swept = []
    for key in sorted(run.ledger):
        if key in desired or key in whole or run.kept(key):
            continue
        under = [d for d in link_dirs if key.startswith(d)]
        if any(link_dirs[d] for d in under):
            continue        # 링크 폴더 너머는 안 건드린다
        p = run.home / key
        swept.append(key)
        try:
            if any(key.startswith(d) for d in fresh_dirs) or not os.path.lexists(str(p)):
                run.record(key, None, '놓은 파일이 없다')
            elif is_link(p) or p.is_dir():
                run.record(key, None, '그 자리가 우리가 놓은 파일이 아니다 — 둔다')
            else:
                if sha(p.read_bytes()) == run.ledger[key]:
                    run.remove(p, '원본에서 빠졌거나 칸을 껐다 · 우리가 쓴 그대로다')
                else:
                    run.backup(p, True, '원본에서 빠졌거나 칸을 껐다 · 사람이 고쳤다')
                run.record(key, None, None)
        except Exception as e:  # noqa: BLE001
            run.out.error('%s — %s: %s' % (TILDE + key, type(e).__name__, e))
    clear_empty(run, swept, tops)


def clear_empty(run, keys, tops):
    """걷은 자리의 폴더가 비었으면(__pycache__ 만 남아도) copy 대상 폴더 아래에서 위로 걷는다 — 대상 폴더 자체와 그 위는
    둔다(도구의 홈 폴더는 그 도구 것이다)."""
    folders = set()
    for key in keys:
        top = max((t for t in tops if key.startswith(t)), key=len, default=None)
        if top is None:
            continue
        parts = key[len(top):].split('/')[:-1]
        folders.update(top + '/'.join(parts[:n]) for n in range(1, len(parts) + 1))
    for rel in sorted(folders, key=lambda r: (-r.count('/'), r)):
        p = run.home / rel
        try:
            if run.kept(rel) or run.gone_at(rel) or is_link(p) or not p.is_dir() or run.left_in(p):
                continue
            run.remove_dir(p, '걷은 뒤 비었다')
        except Exception as e:  # noqa: BLE001
            run.out.error('%s%s/ — 빈 폴더를 못 걷었다 (%s: %s)' % (TILDE, rel, type(e).__name__, e))


def read_names(path):
    """옛 기록의 이름들 — 한 줄에 하나 · 빈 줄은 건너뛴다. 파일이 없으면 None. 폴더 하나를 가리키지 않는 줄은 안 센다."""
    if not path.is_file():
        return None
    names = []
    for line in path.read_text(encoding='utf-8-sig', errors='replace').splitlines():
        n = line.strip()
        if n and n not in ('.', '..') and not any(c in n for c in NAME_BARRED):
            names.append(n)
    return names


def settle_was(run, table, ledgers, placing, on, link_dirs, known):
    """옛 기록(was)의 이름을 가른다 — 놓을 이름은 처음 만남 판정(place_unit)에 맡기고, 아닌 이름을 폴더째 백업으로 옮긴다.
    돌려주는 것은 기록 파일마다 옮겨도 되나다(옛 자리까지 끝난 뒤 옮긴다).

    shared  · 조건이 선다     — 아닌 이름은 폴더째 백업 · 기록 파일을 옮긴다
    shared  · 조건이 안 선다  — 기록 파일도 그 이름도 안 건드린다(설치기의 칸 없이 까는 걸음의 기록이다)
    그 밖                     — 아닌 이름이 어느 층의 그 항목에 있고 같은 대상의 shared 기록에 없으면 폴더째 백업. 어느 층에도
                                없는 이름은 둔다 — 그런 이름의 폴더가 홈에 남으면 기록 파일도 둔다(다음 판이 마저 가른다)
    기록에 그 폴더 아래 줄이 있는 이름(손이 이미 맡았다) · keep 에 떨어지는 이름 · 링크인 대상 폴더는 안 건드린다. 옮기기가
    막히면 ERROR 이고 기록 파일을 둔다.
    """
    shared = {}
    for w in table.wases:
        if w.shared:
            shared.setdefault(w.target, set()).update(ledgers.get(w.ledger) or ())
    verdict = collections.OrderedDict()
    for w in table.wases:
        names = ledgers.get(w.ledger)
        if names is None:
            continue
        folder = run.at(w.target)
        prefix = run.rel(folder) + '/'
        if (w.shared and w.target not in on) or link_dirs.get(prefix, is_link(folder)):
            verdict[w.ledger] = False
            continue
        item = table.route_of(w.target).item
        settled = True
        for name in sorted(set(names)):
            unit = folder / name
            if (name in placing.get(w.target, ()) or run.kept(prefix + name) or run.holds_keep(prefix + name)
                    or owned(run.ledger_was, prefix + name + '/') or not run.present(unit)):
                continue
            if not w.shared:
                if name not in known.get(item, ()):
                    settled = False     # 동료 저장소의 옛 배포가 민 그 사람 스킬일 수 있다
                    continue
                if name in shared.get(w.target, ()):
                    continue
            try:
                run.backup(unit, True, '옛 기록에 든 이름인데 이번에 안 놓는다 — 폴더째 옮긴다')
            except Exception as e:  # noqa: BLE001
                settled = False
                run.out.error('%s — 폴더째 못 옮겼다 · 옛 기록을 둔다 (%s: %s)' % (TILDE + prefix + name + '/', type(e).__name__, e))
        verdict[w.ledger] = verdict.get(w.ledger, True) and settled
    return verdict


def settle_old_names(run, old, p, ledgers):
    """옛 기록 칸을 둔 옛 자리 — 그 기록들에 든 이름의 폴더만 옮기고, 다 옮긴 뒤 비면 폴더도 옮긴다. 기록에 없는 것은
    말없이 둔다. 다 갈랐으면 True."""
    names = set()
    for x in old.ledgers:
        names.update(ledgers.get(x) or ())
    if not run.present(p):
        return True
    if is_link(p) or not p.is_dir():
        return False
    rel = run.rel(p)
    settled = True
    for name in sorted(names):
        unit = p / name
        if not run.present(unit) or run.kept(rel + '/' + name) or run.holds_keep(rel + '/' + name):
            continue
        try:
            run.backup(unit, True, '옛 자리 — 옛 기록에 든 이름이다')
        except Exception as e:  # noqa: BLE001
            settled = False
            run.out.error('%s — 옛 자리를 못 옮겼다 (%s: %s)' % (TILDE + rel + '/' + name + '/', type(e).__name__, e))
    if settled and names and not run.left_in(p, cache_too=True):
        run.backup(p, True, '옛 자리 — 옛 기록의 이름을 다 옮겨 비었다')
    return settled


def list_state(run, table, old, raw):
    """옛 목록의 꼴 — LIST_OURS(맨 위 열쇠가 entries 하나 · 항목 하나 · 그 열쇠가 path 하나이고 그 path 가 표의 다른 old
    폴더를 우리가 써 온 꼴로 연다) · LIST_MIXED(그렇게 여는 항목이 있는데 무엇이 더 붙었다) · None(못 읽는다 · 안 연다).
    우리가 써 온 꼴은 목록 파일 폴더 기준 상대 · `~/…` · 이 PC 홈의 절대 경로다 — `/` 든 `\\` 든 · 끝 / 와 대소문자를 안
    가린다. BOM 은 읽을 때 걷는다."""
    try:
        doc = json.loads(raw.decode('utf-8-sig'))
    except ValueError:      # UnicodeDecodeError 도 ValueError 다
        return None
    if not isinstance(doc, dict):
        return None
    base = '/' + posixpath.dirname(old.place[len(TILDE):])
    shapes = set()
    for o in table.olds:
        if o is old or not o.place.endswith('/'):
            continue
        rel = o.place[len(TILDE):].rstrip('/')
        shapes |= set([posixpath.relpath('/' + rel, base), TILDE + rel, run.home_abs + '/' + rel])
    shapes = set(s.casefold() for s in shapes)
    entries = doc.get(LIST_TOP)

    def opens(e):
        return (isinstance(e, dict) and isinstance(e.get(LIST_PATH), str)
                and e[LIST_PATH].replace('\\', '/').rstrip('/').casefold() in shapes)
    if not any(opens(e) for e in (entries if isinstance(entries, list) else [entries])):
        return None
    if (list(doc) == [LIST_TOP] and isinstance(entries, list) and len(entries) == 1 and isinstance(entries[0], dict)
            and list(entries[0]) == [LIST_PATH]):
        return LIST_OURS
    return LIST_MIXED


def settle_list(run, table, old, p):
    if not run.present(p) or not p.is_file():
        return
    state = list_state(run, table, old, p.read_bytes())
    if state == LIST_OURS:
        run.backup(p, True, '옛 목록 — 옛 자리를 여는 우리가 쓴 꼴 그대로다')
    elif state == LIST_MIXED:
        run.out.warn('%s — 옛 자리를 여는 우리 항목이 다른 것과 섞였다 · 그 줄만 지운다 — 손은 둔다' % old.place)


def settle_olds(run, table, ledgers):
    """옛 자리 — 셋째 칸이 없으면 통째로, 옛 기록이면 그 이름만, list 면 우리가 쓴 꼴일 때만 옮긴다. was 에 안 든 옛 기록
    파일은 그 줄이 끝나면 옮긴다."""
    was_ledgers = set(w.ledger for w in table.wases)
    for old in table.olds:
        p = run.at(old.place)
        rel = run.rel(p)
        try:
            if run.kept(rel) or run.holds_keep(rel):
                if run.present(p):
                    run.out.warn('%s — 다른 주인의 자리(keep)다 · 옛 자리로 안 옮긴다' % old.place)
            elif old.listed:
                settle_list(run, table, old, p)
            elif old.ledgers:
                if settle_old_names(run, old, p, ledgers):
                    for x in old.ledgers:
                        q = run.at(x)
                        if x not in was_ledgers and run.present(q) and q.is_file():
                            run.backup(q, True, '옛 기록 — 그 옛 자리를 다 갈랐다')
            elif run.present(p):
                run.backup(p, True, '옛 자리 — 층이 섰다')
        except Exception as e:  # noqa: BLE001
            run.out.error('%s — 옛 자리를 못 옮겼다 (%s: %s)' % (old.place, type(e).__name__, e))


def warn_runners(run, table):
    """not 이름의 폴더가 그 도구의 홈에 기록 밖으로 있으면 WARN 한 줄 — 우리 것이 아니라 안 걷는다. 칸과 무관하게 잰다."""
    for x in table.nots:
        for r in table.routes:
            if r.item != x.item or r.form != COPY or x.tool not in (r.tool, ANY_TOOL):
                continue
            folder = run.at(r.target)
            top = run.rel(folder) + '/' + x.name
            if run.present(folder / x.name) and not owned(run.ledger, top + '/') and not run.kept(top):
                run.out.warn('%s%s/ — %s' % (TILDE, top, ANY_WARN if x.tool == ANY_TOOL else RUNNER_WARN))


def place(run, table, views, box):
    """표대로 놓는다. views — 층 → (항목 → 파일들 또는 None).

    차례 — 길마다 놓기 · 기록 훑기(걷기 · 빈 폴더) · 옛 기록(was)의 이름 · 옛 자리(old) · 옛 기록 파일 · 받는 쪽 홈의 러너.
    옛 기록은 첫머리에 한 번 읽는다 — old 줄도 같은 기록을 읽고, 기록 파일은 옛 자리까지 끝난 뒤 옮긴다."""
    run.keeps = [fold(k[len(TILDE):].rstrip('/')) for k in table.keeps]
    won, each_won = {}, {}
    for item in table.items.values():
        if item.each:
            got = {}
            for layer in LAYERS:
                files = views[layer](item)
                for name, unit in sorted(units(files or {}).items()):
                    got.setdefault(name, (layer, unit))
            each_won[item.name] = got
            continue
        for layer in LAYERS:
            files = views[layer](item)
            if files is not None:
                won[item.name] = (layer, files)
                break

    def pick(route):
        return won.get(route.item) if route.tool in box else None

    ledgers = collections.OrderedDict()
    for x in [w.ledger for w in table.wases] + [y for o in table.olds for y in o.ledgers]:
        if x not in ledgers:
            ledgers[x] = read_names(run.at(x))
    desired, whole, link_dirs, fresh_dirs, placing = set(), set(), {}, set(), {}
    for target, routes in table.groups.items():
        first = routes[0]
        item = table.items[first.item]
        path = run.at(target)
        try:
            if run.kept(run.rel(path)):
                run.out.warn('%s — 다른 주인의 자리(keep)다 · 이 길을 건너뛴다' % target)
            elif first.form == COPY and item.each:
                placing[target] = place_each(run, table, first, each_won[item.name] if first.tool in box else None,
                                             link_dirs, fresh_dirs, desired)
            elif first.form == COPY:
                place_copy(run, first, pick(first), link_dirs, fresh_dirs, desired)
            elif first.form == IMPORT:
                lines = [import_line(run, r, table.items[r.item], pick(r)) for r in routes]
                lines = [x for x in lines if x]
                text = ('%s\n%s\n%s\n' % (BEGIN, '\n'.join(lines), END)) if lines else ''
                place_marked(run, path, text, True)
            elif first.form == BLOCK:
                got = pick(first)
                text = ''
                if got:
                    rule_sets = []
                    for r in routes[1:]:
                        g = pick(r)
                        if g:
                            home_of_rules = '%s%s/%s/%s' % (TILDE, HUB, g[0], table.items[r.item].path.rstrip('/'))
                            rule_sets.append((home_of_rules, g[1]))
                    text = codex_block(got[1][''], rule_sets)
                place_marked(run, path, text, False)
            else:
                whole.add(run.rel(path))
                got = pick(first)
                place_whole(run, path, agy_text(run, first.form, got[0], item) if got else None, first.form, item)
        except Exception as e:  # noqa: BLE001 — 한 자리가 막혀도 나머지는 간다
            run.out.error('%s — %s: %s' % (target, type(e).__name__, e))
    tops = sorted(set(run.rel(run.at(r.target)) + '/' for r in table.routes if r.form == COPY))
    sweep_ledger(run, desired, whole, link_dirs, fresh_dirs, tops)
    on = set(r.target for r in table.routes if r.tool in box)
    known = dict((name, set(got)) for name, got in each_won.items())
    verdict = settle_was(run, table, ledgers, placing, on, link_dirs, known)
    settle_olds(run, table, ledgers)
    for x, settled in verdict.items():
        q = run.at(x)
        if settled and run.present(q) and q.is_file():
            try:
                run.backup(q, True, '옛 기록 — 그 이름을 다 갈랐다')
            except Exception as e:  # noqa: BLE001
                run.out.error('%s — 옛 기록을 못 옮겼다 (%s: %s)' % (x, type(e).__name__, e))
    warn_runners(run, table)
    run.save()


def layer_views(home):
    return dict((layer, (lambda item, root=home / HUB / layer: item_files(root, item.path))) for layer in LAYERS)


# ── 명령 ─────────────────────────────────────────────────────────────────────────────────────────────────
def stamp_key(table_path):
    """판 도장을 견줄 열쇠 — 큰 쪽이 새 판이다. 도장 없는 표와 못 읽는 표는 가장 새 판이다."""
    try:
        table, _ = read_table(table_path)
    except (OSError, ValueError):
        table = None
    stamp = table.stamp if table is not None else None
    return (1, '') if stamp is None else (0, stamp)


def placing_layer(home, own=None):
    """놓기를 맡을 층 — 손이 선 층 가운데 표의 도장이 새 층 · 같으면 앞 층(개인). 없으면 None.

    own=(층, 표 자리) — sync --dry-run 이 채워질 층을 셈할 때 그 층을 채울 원본 표로 본다.
    """
    best, best_key = None, None
    for layer in LAYERS:
        if own is not None and layer == own[0]:
            table_path = own[1]
        elif (home / HUB / layer / HAND).is_file():
            table_path = home / HUB / layer / TABLE
        else:
            continue
        key = stamp_key(table_path)
        if best is None or key > best_key:
            best, best_key = layer, key
    return best


def winning_hand(home):
    layer = placing_layer(home)
    return None if layer is None else home / HUB / layer / HAND


def same_file(a, b):
    try:
        return os.path.samefile(str(a), str(b))
    except OSError:
        return False


def passthrough(a):
    args = []
    if a.home:
        args += ['--home', os.path.abspath(a.home)]
    if a.box is not None:
        args += ['--box', a.box]
    return args


def launch(hand, args):
    """놓기를 맡을 층의 손을 띄운다 — (종료 값, 그 손의 줄들). 넘김의 표지 값은 이 손의 자리다."""
    sys.stdout.flush()
    env = dict(os.environ)
    env[RELAYED] = str(pathlib.Path(__file__).resolve())
    p = subprocess.run([sys.executable or 'python', '-X', 'utf8', str(hand)] + args, stdout=subprocess.PIPE, env=env)
    return p.returncode, p.stdout.decode('utf-8', 'replace').splitlines()


def hand_over(hand, args, out):
    """놓기를 맡을 층의 손을 띄워 넘긴다 — 그 줄을 잇고 그 종료 값을 돌려준다."""
    rc, lines = launch(hand, args)
    for line in lines:
        out.relay(line)
    return rc


def relay_dry(hand, a, root, out):
    """sync --dry-run 을 놓기를 맡을 손에게 같은 인자로 넘긴다 — 그 손이 끝 줄(CHANGED=)까지 냈으면 그 줄을 잇고 종료 값을
    돌려준다. 못 띄웠으면(해석기가 진다 · 끝 줄이 없다) 아무것도 안 잇고 None — 이 손이 셈한다."""
    try:
        rc, lines = launch(hand, ['sync', '--layer', a.layer, '--from', str(root), '--dry-run'] + passthrough(a))
    except OSError:
        return None
    if not lines or not lines[-1].startswith('CHANGED='):
        return None
    for line in lines:
        out.relay(line)
    return 1 if (rc or out.failed) else 0


def own_body(dry):
    """층 뿌리에 실을 손의 몸 — 넘겨받은 sync --dry-run 이면 넘긴 손(실제 sync 에서 제 몸을 싣는 손)이다."""
    given = os.environ.get(RELAYED, '') if dry else ''
    if os.path.isabs(given) and os.path.isfile(given):
        return pathlib.Path(given)
    return pathlib.Path(__file__).resolve()


def cmd_place(a, home, out, dry, check):
    """place · check — 놓기를 맡을 층의 손이 아니면 넘긴다. 넘겨받은 손은 다시 고르지 않는다. 돌려주는 값은 종료 값이다."""
    absent = 2 if check else 1
    if os.environ.get(RELAYED):
        hand = pathlib.Path(__file__).resolve()
    else:
        hand = winning_hand(home)
        if hand is None:
            out.error('층에 손이 없다 — sync 가 먼저 돈다(%s)' % (home / HUB))
            return absent
        if not same_file(hand, __file__):
            args = ['check'] if check else ['place'] + (['--dry-run'] if dry else [])
            rc = hand_over(hand, args + passthrough(a), out)
            return rc if rc in (0, 1, absent) else absent
    table, bad = read_table(hand.parent / TABLE)
    if table is None:
        out.error('표가 없다 — %s' % (hand.parent / TABLE))
        return absent
    for why in bad:
        out.error(why)
    if bad:
        return absent
    box = read_box(a.box, table.tools, out)
    if dry:
        place(Run(home, True, out), table, layer_views(home), box)
    else:
        try:
            with Lock(home / HUB):
                place(Run(home, False, out), table, layer_views(home), box)
        except Busy as e:
            out.error(e)
    if check:
        return 1 if (out.changed or out.failed) else 0
    return 1 if out.failed else 0


def cmd_sync(a, home, out):
    root = pathlib.Path(os.path.abspath(a.src))
    table, bad = read_table(root / TABLE)
    if table is None:
        if a.layer == PERSONAL:
            return 0    # 그 저장소는 개인 층을 안 든다 — 아무것도 안 쓰고 놓기도 안 넘긴다(씨앗 설정 저장소가 이 꼴이다)
        out.error('표가 없다 — %s' % (root / TABLE))
        return 1
    for why in bad:
        out.error(why)
    if bad:
        return 1
    winner = None           # 넘겨받은 손이면 None 그대로 — 다시 고르지 않는다
    if a.dry_run and not os.environ.get(RELAYED):
        winner = placing_layer(home, (a.layer, root / TABLE))
        hand = home / HUB / winner / HAND
        if winner != a.layer and not same_file(hand, __file__):
            rc = relay_dry(hand, a, root, out)
            if rc is not None:
                return rc
    fills = dict((item.name, source_files(item, a.layer, root, out)) for item in table.items.values())
    selves = ((TABLE, root / TABLE), (HAND, own_body(a.dry_run)))
    if a.dry_run:
        fill_layer(home, a.layer, table, fills, selves, out, True)
        return dry_place(a, home, table, fills, winner, out)
    try:
        with Lock(home / HUB):
            fill_layer(home, a.layer, table, fills, selves, out, False)
    except Busy as e:
        out.error(e)
        return 1
    failed = out.failed
    rc = cmd_place(a, home, out, False, False)
    return 1 if (failed or rc) else 0


def dry_place(a, home, table, fills, winner, out):
    """채워질 층을 셈해 놓을 줄을 낸다 — 그 층은 원본으로 읽고, 표는 채운 뒤 놓기를 맡을 층의 것을 쓴다: winner 가 채워질
    층이면 원본 표, 다른 층이면 그 층의 표, None(넘겨받은 손)이면 이 손이 선 층의 표."""
    if winner != a.layer:
        path = pathlib.Path(__file__).resolve().parent / TABLE if winner is None else home / HUB / winner / TABLE
        table, bad = read_table(path)
        if table is None or bad:
            if winner is not None and not same_file(home / HUB / winner / HAND, __file__):
                out.warn(RELAY_WARN)   # 그 층의 손을 못 띄웠다(relay_dry) — 옛 판의 손이 새 문법을 모르는 자리다
                return 1 if out.failed else 0
            out.error('놓기를 맡을 층의 표가 없거나 틀렸다 — %s' % path)
            return 1
    views = layer_views(home)
    views[a.layer] = lambda item: fills[item.name]
    place(Run(home, True, out), table, views, read_box(a.box, table.tools, out))
    return 1 if out.failed else 0


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='backslashreplace')
    ap = argparse.ArgumentParser(description='갈 곳 표를 읽어 도구 홈에 놓는 손')
    sub = ap.add_subparsers(dest='cmd')
    sub.required = True
    s = sub.add_parser('sync')
    s.add_argument('--layer', choices=(STANDARD, PERSONAL), required=True)
    s.add_argument('--from', dest='src', required=True)
    s.add_argument('--dry-run', action='store_true')
    p = sub.add_parser('place')
    p.add_argument('--dry-run', action='store_true')
    c = sub.add_parser('check')
    for x in (s, p, c):
        x.add_argument('--home')
        x.add_argument('--box')
    a = ap.parse_args(argv)
    home = pathlib.Path(os.path.abspath(a.home)) if a.home else pathlib.Path.home()
    out = Out()
    try:
        if a.cmd == 'sync':
            rc = cmd_sync(a, home, out)
        else:
            rc = cmd_place(a, home, out, a.cmd == 'check' or a.dry_run, a.cmd == 'check')
    except Exception as e:  # noqa: BLE001 — 부르는 자는 이 한 줄로 까닭을 받는다
        out.error('%s: %s' % (type(e).__name__, e))
        rc = 2 if a.cmd == 'check' else 1
    out.end()
    return rc


if __name__ == '__main__':
    sys.exit(main())
