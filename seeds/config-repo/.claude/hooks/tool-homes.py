"""갈 곳 표를 읽어 규범 · 룰 · 에이전트를 도구 홈에 놓는 손 하나 (결정 0112).

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
        안 싣는 항목(local)이 있고, 씨앗으로 만든 저장소는 제가 둔 원본만 든다. 개인 층의 저장소 자리가 있는데 꼴이 표와
        다르면(파일 · 폴더가 바뀜 · 링크) WARN 을 내고 그 층에서 뺀다. 항목마다 곁에 다 지은 뒤 바꿔 끼워 반쯤 채운 항목이
        이기지 않게 하고, 바꿔 끼우기가 막히면(윈도에서 누가 안의 파일을 열어 둠) 옛 항목을 그대로 둔다. 바뀐 것이 없으면
        안 쓴다. 그 뒤 놓기를 맡을 층의 손에게 place 를 넘기고, 그 줄을 이어 끝의 CHANGED 하나로 낸다. 개인 층을 채우러
        온 뿌리에 표가 없으면 그 저장소는 개인 층을 안 든다 — 아무것도 안 쓰고 넘기지도 않는다(`CHANGED=0` · 종료 0).
        짐에 표가 없으면 짐이 깨진 것이라 ERROR 다.
place — 길마다 조건이 서면 항목을 그 항목의 이긴 층에서 놓고, 안 서면 우리 것만 걷는다. 그 뒤 옛 자리를 백업으로 옮긴다.
check — place --dry-run 이 바꿀 것이 없으면 0, 있으면 그 줄과 함께 1, 층이나 표가 없으면(또는 못 재면) 2.

**이기는 단위는 항목이다** — 개인 층에 그 항목이 있으면 통째로 개인 층 것이다. 파일 단위로 섞으면 저장소에서 지운 룰이
  지난 릴리스의 표준 층에 남아 계속 깔린다.
**놓기는 새 판의 손이 한다** — 손이 선 층 가운데 층 뿌리 표의 판 도장(`stamp` 줄 · 뽑는 자가 짐과 씨앗에 실리는 사본에
  찍는다)이 새 층의 손이 놓는다. 도장 없는 표(작업장 — 설정 저장소의 원본)와 못 읽는 표는 가장 새 판이고(못 읽으면 그
  층의 손이 받아 까닭을 낸다), 같으면 개인 층이다. 한 PC 에 지난 릴리스의 손(설치기)과 저장소의 손(배포)이 같이 있어,
  부른 쪽 손으로 놓으면 둘이 홈을 번갈아 고친다. 그래서 place · check 를 다른 손이 받으면 같은 인자로 그 손을 띄워 넘기고,
  그 줄을 이어 낸다. 넘겨받은 손은 다시 고르지 않고 제가 놓는다 — 고르는 법이 다른 두 판의 손이 서로 넘기며 맴돌지 않게.
  sync --dry-run 만은 부른 쪽 손이 채워질 층을 셈한다 — 채워질 손이 아직 층에 없다.
**우리 것만 걷는다** — 표지 사이, 기록(`~/.paisetup/placed.tsv`)에 적은 해시 그대로인 파일, 우리가 써 온 옛 꼴(아래 OLD_*)만
  우리 것이다. 표지가 우리 것을 말하는 import · block 대상은 기록에 안 든다. 놓을 것이 없는 도구 폴더는 짓지 않는다.
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
정한 자리 — 결정 0112 · claude-config#133 「2 단계 첫 걸음 「규범 · 룰」」 코멘트와 그 「계약 보탬」 둘.
"""
import argparse
import collections
import datetime
import fnmatch
import hashlib
import json
import os
import pathlib
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
RELAYED = 'TOOL_HOMES_RELAYED'         # 넘겨받은 손의 표지(환경 변수) — 있으면 다시 고르지 않고 제가 놓는다
TILDE = '~/'
BOM = b'\xef\xbb\xbf'

BOX_VAR = 'PAISETUP_PERSONAL'
BOX_REG_KEY = 'Environment'            # HKCU 아래
BOX_NONE = 'none'
BOX_EMPTY = ('claude',)                # 칸 값이 비었을 때
BOX_SPLIT = re.compile(r'[,\s]+')

KIND_ITEM, KIND_ROUTE, KIND_OLD, KIND_STAMP = 'item', 'route', 'old', 'stamp'
LOCAL = 'local'                        # item 줄의 다섯째 칸 — 짐에 안 싣는 항목(뽑는 자가 읽는다)
STAMP = re.compile(r'\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z')   # UTC · 초까지 한 꼴이라야 글자 순이 곧 시간 순이다
IMPORT, BLOCK, LINES, INCLUDE, LIST, COPY = 'import', 'block', 'lines', 'include', 'list', 'copy'
COND_BOX = 'box'
FILE_FORMS = (IMPORT, BLOCK, LINES, INCLUDE, LIST)

BEGIN = '<!-- paisetup:norms BEGIN -->'
END = '<!-- paisetup:norms END -->'
IMPORT_LINE = '@~/%s/%s/%s'            # HUB · 층 · 층 안의 자리

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

Item = collections.namedtuple('Item', 'name path repo')            # path — 층 안의 자리 · repo — 설정 저장소 안의 자리
Route = collections.namedtuple('Route', 'item tool form target cond')


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
    """`root` 아래 항목의 파일 — {상대 자리: 파일}(파일 항목은 열쇠가 빈 글 하나). 없거나 꼴이 다르면 None."""
    p = root / item_path.rstrip('/')
    if item_path.endswith('/'):
        return walk_files(p) if p.is_dir() and not is_link(p) else None
    return {'': p} if p.is_file() else None


def same_files(a, b):
    if set(a) != set(b):
        return False
    return all(a[k].read_bytes() == b[k].read_bytes() for k in a)


# ── 갈 곳 표 ─────────────────────────────────────────────────────────────────────────────────────────────
class Table:
    def __init__(self, items, routes, olds, stamp):
        self.items, self.routes, self.olds = items, routes, olds
        self.stamp = stamp                                 # 판 도장 — 없으면 None(작업장 · 가장 새 판)
        self.groups = collections.OrderedDict()            # 대상 → 길들(표의 차례)
        for r in routes:
            self.groups.setdefault(r.target, []).append(r)
        self.tools = sorted(set(r.tool for r in routes))


def read_table(path):
    """(표, 틀린 까닭들). 표 파일이 없으면 (None, [])."""
    if not path.is_file():
        return None, []
    items, routes, olds, stamps, bad = collections.OrderedDict(), [], [], [], []
    for n, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        f = raw.split()
        if not f or f[0].startswith('#'):
            continue
        where = '%s:%d' % (path.name, n)
        if f[0] == KIND_ITEM and (len(f) == 4 or (len(f) == 5 and f[4] == LOCAL)):
            if f[1] in items:
                bad.append('%s — 항목 이름이 겹친다(%s)' % (where, f[1]))
            elif f[2].endswith('/') != f[3].endswith('/'):
                bad.append('%s — 층 안의 자리와 저장소 자리의 꼴(파일 · 폴더)이 다르다' % where)
            items[f[1]] = Item(f[1], f[2], f[3])
        elif f[0] == KIND_ROUTE and len(f) == 6:
            routes.append(Route(*f[1:]))
        elif f[0] == KIND_OLD and len(f) == 2 and f[1].startswith(TILDE):
            olds.append(f[1])
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
        elif r.form == COPY and not (r.target.endswith('/') and folder_item):
            bad.append('길 %s → %s — copy 는 폴더 항목을 폴더에 놓는다' % (r.item, r.target))
        elif r.form in FILE_FORMS and r.target.endswith('/'):
            bad.append('길 %s → %s — %s 의 자리는 파일이다' % (r.item, r.target, r.form))
        elif r.form in (IMPORT, BLOCK) and folder_item:
            bad.append('길 %s → %s — %s 는 파일 항목을 쓴다' % (r.item, r.target, r.form))
        elif r.form == LINES and not folder_item:
            bad.append('길 %s → %s — lines 는 폴더 항목을 쓴다' % (r.item, r.target))
        elif r.form not in FILE_FORMS + (COPY,):
            bad.append('길 %s → %s — 모르는 꼴이다(%s)' % (r.item, r.target, r.form))
    table = Table(items, routes, olds, stamps[0] if len(stamps) == 1 else None)
    for target, rs in table.groups.items():
        forms = [r.form for r in rs]
        if forms.count(BLOCK) == 1 and forms[0] == BLOCK and all(x == LINES for x in forms[1:]):
            continue
        if len(forms) == 1 and forms[0] in (IMPORT, INCLUDE, LIST, COPY):
            continue
        bad.append('자리 %s — 한 자리에 맞지 않는 꼴들이다(%s)' % (target, ' · '.join(forms)))
    return table, bad


def source_files(item, layer, root, out):
    """채울 파일 — {층 안 상대 자리: 원본 파일}. 그 층에 이 항목이 안 서면 None.

    표준 층은 짐의 층 안의 자리, 개인 층은 표의 저장소 자리에서 읽는다. 그 자리가 없으면 조용히 안 선다. 개인 층의 저장소
    자리가 있는데 꼴이 표와 다르면 WARN 을 내고 이 층에서 뺀다 — 원본을 두었는데 안 깔리는 까닭이 보이게.
    """
    rel = item.path if layer == STANDARD else item.repo
    got = item_files(root, rel)
    if got is None and layer == PERSONAL and os.path.lexists(str(root / rel.rstrip('/'))):
        out.warn('%s — 저장소 자리 %s 의 꼴이 표와 다르다 · 개인 층에서 이 항목을 뺀다' % (item.name, rel))
    return got


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
        if not self.dry:
            dest = self.backup_root() / self.rel(p)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if move or is_link(p):
                os.rename(str(p), str(dest))
            else:
                shutil.copy2(str(p), str(dest))
        self.out.change('backup', shown, why)

    def write(self, p, data, why):
        if not self.dry:
            write_atomic(p, data)
        self.out.change('write', TILDE + self.rel(p), why)

    def remove(self, p, why):
        if not self.dry:
            p.unlink()
        self.out.change('remove', TILDE + self.rel(p), why)

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


def place_copy(run, route, got, link_dirs, fresh_dirs, desired):
    folder = run.at(route.target)
    prefix = run.rel(folder) + '/'
    link_dirs[prefix] = is_link(folder)
    if got is None:
        return              # 걷기는 기록 훑기(sweep_ledger)가 한다
    fresh = False
    if link_dirs[prefix]:
        run.backup(folder, True, '링크다 — 걷고 폴더로 쓴다')
        link_dirs[prefix], fresh = False, True
        fresh_dirs.add(prefix)
    for rel in sorted(got[1]):
        dest = folder / rel
        key = prefix + rel
        desired.add(key)
        try:
            data = got[1][rel].read_bytes()
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


def sweep_ledger(run, desired, whole, link_dirs, fresh_dirs):
    """기록에 있는데 이번에 바라지 않는 파일 — 우리가 쓴 그대로면 지우고, 사람이 고쳤으면 백업으로 옮긴다."""
    for key in sorted(run.ledger):
        if key in desired or key in whole:
            continue
        under = [d for d in link_dirs if key.startswith(d)]
        if any(link_dirs[d] for d in under):
            continue        # 링크 폴더 너머는 안 건드린다
        p = run.home / key
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


def place(run, table, views, box):
    """표대로 놓는다. views — 층 → (항목 → 파일들 또는 None)."""
    won = {}
    for item in table.items.values():
        for layer in LAYERS:
            files = views[layer](item)
            if files is not None:
                won[item.name] = (layer, files)
                break

    def pick(route):
        return won.get(route.item) if route.tool in box else None

    desired, whole, link_dirs, fresh_dirs = set(), set(), {}, set()
    for target, routes in table.groups.items():
        first = routes[0]
        item = table.items[first.item]
        path = run.at(target)
        try:
            if first.form == COPY:
                place_copy(run, first, pick(first), link_dirs, fresh_dirs, desired)
            elif first.form == IMPORT:
                got = pick(first)
                text = ('%s\n%s\n%s\n' % (BEGIN, IMPORT_LINE % (HUB, got[0], item.path), END)) if got else ''
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
    sweep_ledger(run, desired, whole, link_dirs, fresh_dirs)
    for old in table.olds:
        p = run.at(old)
        if os.path.lexists(str(p)):
            try:
                run.backup(p, True, '옛 자리 — 층이 섰다')
            except Exception as e:  # noqa: BLE001
                run.out.error('%s — 옛 자리를 못 옮겼다 (%s: %s)' % (old, type(e).__name__, e))
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


def hand_over(hand, args, out):
    """놓기를 맡을 층의 손을 띄워 넘긴다 — 그 줄을 잇고 그 종료 값을 돌려준다."""
    sys.stdout.flush()
    env = dict(os.environ)
    env[RELAYED] = '1'
    p = subprocess.run([sys.executable or 'python', '-X', 'utf8', str(hand)] + args, stdout=subprocess.PIPE, env=env)
    for line in p.stdout.decode('utf-8', 'replace').splitlines():
        out.relay(line)
    return p.returncode


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
    fills = dict((item.name, source_files(item, a.layer, root, out)) for item in table.items.values())
    selves = ((TABLE, root / TABLE), (HAND, pathlib.Path(__file__).resolve()))
    if a.dry_run:
        fill_layer(home, a.layer, table, fills, selves, out, True)
        return dry_place(a, home, root, table, fills, out)
    try:
        with Lock(home / HUB):
            fill_layer(home, a.layer, table, fills, selves, out, False)
    except Busy as e:
        out.error(e)
        return 1
    failed = out.failed
    rc = cmd_place(a, home, out, False, False)
    return 1 if (failed or rc) else 0


def dry_place(a, home, root, table, fills, out):
    """채워질 층을 셈해 놓을 줄을 낸다 — 그 층은 원본으로 읽고, 표는 채운 뒤 놓기를 맡을 층의 것을 쓴다."""
    winner = placing_layer(home, (a.layer, root / TABLE))
    if winner != a.layer:
        table, bad = read_table(home / HUB / winner / TABLE)
        if table is None or bad:
            out.error('놓기를 맡을 층의 표가 없거나 틀렸다 — %s' % (home / HUB / winner / TABLE))
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
