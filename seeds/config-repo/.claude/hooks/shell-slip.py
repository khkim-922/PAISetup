"""셸 실수 문의 몸통 — Bash · PowerShell 도구의 명령에서 비싼 실수 둘을 그 순간에 골라 묻거나 막는다.

부르는 꼴: 껍데기(`shell-slip.sh`)가 PreToolUse 입력 JSON 을 표준입력으로 넘긴다(낌새가 있을 때만).
내는 것: 걸리면 `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":…,"permissionDecisionReason":…}}`
  한 덩이 — 막을 것이 하나라도 들면 `deny`, 아니면 `ask`. 안 걸리면 아무것도 안 낸다.
종료 값: 0 — 냈거나 낼 것이 없다. 입력을 못 읽거나 가르다 지면 예외로 끝나고, 껍데기가 낌새를 대며 묻는 답으로 갈음한다.

거는 둘 — 무엇에 걸고 무엇을 두나. 커밋의 출력을 파이프로 넘기는 실수는 안 건다 — 두 달에 369 번 걸릴 물음은 소음이다(결정 0162).
  이름 · 창 제목으로 끄기(묻는다) — 같은 이름 · 제목을 가진 남의 프로그램까지 함께 닫힌다.
    건다: pkill · killall · taskkill /IM · taskkill /FI 의 PID 아닌 거르개 · Stop-Process(spps · PowerShell 의 kill)가 -Name 이거나
    -Id 없이 Get-Process 가 고른 것을 받을 때 · 창 제목(MainWindowTitle)으로 고른 것을 끄기 · 이름으로 고른 것의 .Kill() ·
    pgrep 이 고른 것을 kill.
    둔다: Stop-Process -Id · taskkill /PID · kill <PID> · 그 낱말을 찾거나 찍는 명령(grep · echo 의 인자 · 따옴표 안의 글).
  상태를 바꾸는 스크립트를 앞만 읽고 끊는 자에(막는다) — STATE_SCRIPTS 가운데 하나를 실행한 출력이 같은 파이프에서 head ·
    Select-Object -First 로 간다. 그 줄 수가 차면 스크립트가 그 자리에서 멈춰, 쓰기 전에 끊기면 성공처럼 보이고 아무것도 안
    바뀐다.
    둔다: 스크립트 글을 읽는 명령(Get-Content · cat · grep · git diff) · -Last · tail · 파일로 받은 뒤 거르기 · 읽기만 하는 판
    (설치기 -Describe · 뽑기 --check · --touches · --gate-only · 손 check · --dry-run · 배포의 -Yes 없는 계획 판) — 끊겨도 잃는 것이 없다.

어떻게 읽나 — 따옴표 · heredoc · here-string · 묶음(`( )` · `{ }` · `$( )` · 백틱)을 아는 작은 가르개로 명령 글을 파이프 ·
단 · 낱말로 가르고, 단마다 실제로 도는 명령을 앞붙이(sudo · env · xargs · & · .)를 걷고 고른다. 셸을 띄우는 명령
(powershell -Command · -File · -EncodedCommand · bash -c · cmd /c)과 묶음의 안은 그 문법으로 다시 갈라 같은 판정에 넣는다.
⚠ 셸 문법을 다 따르지는 않는다 — 모르는 꼴은 낱말로 읽혀 안 걸리는 쪽으로 진다. 묻기가 잦으면 아무도 안 읽는다.
"""
import base64
import json
import re
import sys

SH, PS, CMD = 'sh', 'ps', 'cmd'                 # 명령 글의 문법 — 도구가 첫 문법을, 셸을 띄우는 명령이 안쪽 문법을 정한다
TOOL_DIALECT = {'PowerShell': PS}               # 그 밖의 도구(Bash)는 SH
ESCAPE = {SH: '\\', PS: '`', CMD: '^'}          # 따옴표 밖에서 다음 글자를 그대로 두는 글자
GROUP = '\x00'                                  # 낱말 안의 묶음 자리 — 낱말 글에서 묶음을 알아보는 표지
MAX_DEPTH = 4                                   # 안쪽 명령을 다시 가르는 깊이 한도

# 상태를 바꾸는 스크립트 — 설치기(install) · 배포(deploy) · 원격 설치(setup-remote) · 배포본 뽑기(build-dist) · 홈에 놓는 손
#   (tool-homes). 이름으로만 알아본다 — 다른 저장소의 같은 이름(deploy.ps1 · install.ps1)도 상태를 바꾸는 꼴이라 같이 막는다.
STATE_SCRIPTS = ('deploy.ps1', 'install.ps1', 'install.cmd', 'setup-remote.sh', 'build-dist.sh', 'tool-homes.py')
STATE_NAME = re.compile(r'(?:^|[\\/.:])(%s)$' % '|'.join(re.escape(s) for s in STATE_SCRIPTS))
# 읽기만 하는 판 — 그 스크립트가 아무것도 안 쓰는 깃발 · 부명령. 끊겨도 잃는 것이 없어 안 막는다(소문자로 견주고 PowerShell 의
#   `-깃발:값` 은 `:` 앞까지). deploy.ps1 은 승인 스위치 없이는 계획만 찍고 묻는다 — `-Yes` 가 없는 판이 읽기다.
READ_ONLY_ARGS = {'install.ps1': ('-describe',), 'build-dist.sh': ('--check', '--touches', '--gate-only'),
                  'tool-homes.py': ('check', '--dry-run')}
PLAN_UNLESS = {'deploy.ps1': '-yes'}

# 앞붙이 — 뒤의 명령을 돌리는 말. 그 선택 가운데 값을 하나 받는 것 · 이름=값 꼴 · timeout 의 시간도 같이 걷는다
PREFIX_CMDS = ('sudo', 'exec', 'nohup', 'time', 'command', 'builtin', 'nice', 'stdbuf', 'env', 'timeout', 'xargs', '&', '.', 'call')
PREFIX_VALUE_OPTS = {'xargs': ('-n', '-P', '-I', '-L', '-s', '-d', '-E', '-a'), 'sudo': ('-u', '-g'), 'env': ('-u', '-C', '-S'),
                     'nice': ('-n',), 'timeout': ('-s', '-k')}
ASSIGN = re.compile(r'[A-Za-z_][A-Za-z0-9_]*=')

PS_HOSTS = ('powershell', 'pwsh')
SH_HOSTS = ('bash', 'sh', 'zsh', 'dash')
CMD_HOSTS = ('cmd',)
RUNNERS = ('python', 'python3', 'pythonw', 'py', 'node', 'uv', 'uvx')   # 스크립트 파일을 인자로 받아 돌리는 것
PS_HOST_VALUE = ('windowstyle', 'inputformat', 'outputformat', 'version', 'configurationname', 'psconsolefile',
                 'settingsfile', 'workingdirectory')                   # 값을 하나 받는 powershell 매개변수(앞 두 글자 이상)
PS_HOST_VALUE_SHORT = ('w', 'v', 'wd', 'if', 'of', 'ep')
SH_HOST_VALUE = ('-o', '+o', '-O', '+O')

STOP_VERBS = ('stop-process', 'spps')           # PowerShell 의 kill 별칭은 문법이 PS 일 때만 이 무리다
LISTERS = ('get-process', 'gps')                # 프로세스를 이름 · 속성으로 고르는 자 — PowerShell 의 ps 별칭도
PID_LOOKUPS = ('pgrep', 'pidof')

WHY_KILL = ('이름 · 창 제목으로 프로세스를 끈다(%s). 같은 이름 · 제목을 가진 다른 프로그램(브라우저 · 편집기)까지 함께 닫힌다. '
            '직접 띄운 프로세스라면 띄울 때 PID 를 받아(Start-Process -PassThru 의 .Id · $!) 그 PID 로만 끈다 — '
            'Stop-Process -Id · taskkill /PID. PID 를 못 받았으면 띄우기 전에 뜬 목록과의 차집합만 끈다. '
            '이름으로 꺼야 하는 까닭이 분명할 때만 승인한다.')
WHY_STATE = ('상태를 바꾸는 스크립트(%s)의 출력을 앞만 읽고 끊는 자(head · Select-Object -First)에 물렸다 — 그 줄 수가 차면 '
             '스크립트가 그 자리에서 멈춘다. 쓰기 전에 끊기면 성공처럼 보이고 아무것도 안 바뀐다. 출력을 파일로 받고(> out.txt '
             '2>&1) 그 파일을 거른다 — head -n N out.txt · Get-Content out.txt -TotalCount N.')


# ── 가르개 ───────────────────────────────────────────────────────────────────────────────────────────────
def close_of(src, i, opener, closer, dialect):
    """src[i] 의 여는 글자에 짝인 닫는 글자의 자리 — 따옴표 안은 안 센다. 짝이 없으면 -1."""
    depth, j, n, esc = 0, i, len(src), ESCAPE[dialect]
    while j < n:
        c = src[j]
        if c == esc and dialect != CMD:
            j += 2
            continue
        if c == "'" and dialect != CMD:
            k = src.find("'", j + 1)
            if k < 0:
                return -1
            j = k + 1
            continue
        if c == '"':
            k = j + 1
            while k < n and src[k] != '"':
                k += 2 if src[k] == esc and dialect != CMD else 1
            if k >= n:
                return -1
            j = k + 1
            continue
        if c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


def skip_heredocs(src, i, docs):
    """줄 머리 i 부터 heredoc 본문을 건너뛴 자리 — docs 는 (끝말, 탭 걷기)를 나온 차례대로."""
    n = len(src)
    for delim, strip in docs:
        while i < n:
            j = src.find('\n', i)
            line = src[i:j if j >= 0 else n].rstrip('\r')
            i = j + 1 if j >= 0 else n
            if (line.lstrip('\t') if strip else line) == delim:
                break
    return i


HEREDOC_DELIM = re.compile(r"""'([^']*)'|"([^"]*)"|\\?([^\s;&|<>()'"]+)""")


def parse(src, dialect):
    """명령 글 → 파이프 목록. 파이프 = 단 목록, 단 = 낱말 목록, 낱말 = (글, [안쪽 명령 글]).

    && · || · ; · 줄 · (sh 의) 홑 & 는 파이프를 끊고, | · |& 는 단을 끊는다. 넘김(2>&1 · &>)은 낱말이다.
    묶음은 낱말 안에 GROUP 표지로 남고 그 안의 글이 안쪽 명령 글로 붙는다. heredoc · here-string 본문은 글이지 명령이 아니다."""
    pipes, segs, words = [], [], []
    cur, docs = None, []
    esc, i, n = ESCAPE[dialect], 0, len(src)

    def word():
        nonlocal cur
        if cur is None:
            cur = [[], []]
        return cur

    def end_word():
        nonlocal cur
        if cur is not None:
            words.append((''.join(cur[0]), cur[1]))
            cur = None

    def end_seg():
        nonlocal words
        end_word()
        segs.append(words)
        words = []

    def end_pipe():
        nonlocal segs
        end_seg()
        if any(segs):
            pipes.append(segs)
        segs = []

    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ''
        if c == '\n':
            end_pipe()
            i = skip_heredocs(src, i + 1, docs) if docs else i + 1
            docs = []
            continue
        if c in ' \t\r':
            end_word()
            i += 1
            continue
        if c == '#' and cur is None and dialect != CMD:
            j = src.find('\n', i)
            i = n if j < 0 else j
            continue
        if c == esc:
            if nxt == '\n' or (nxt == '\r' and src[i + 2:i + 3] == '\n'):
                i += 2 if nxt == '\n' else 3        # 줄 이음
                continue
            word()[0].append(nxt)
            i += 2
            continue
        if dialect == PS and c == '@' and cur is None and nxt in ('"', "'") and src[i + 2:i + 3] in ('\n', '\r'):
            end = src.find('\n' + nxt + '@', i + 2)      # here-string — 본문은 글이다
            end = n if end < 0 else end
            word()[0].append(src[i + 2:end])
            i = end + 3
            continue
        if dialect == SH and c == '$' and nxt == "'":
            j, buf = i + 2, []
            while j < n and src[j] != "'":
                if src[j] == '\\' and j + 1 < n:
                    buf.append(src[j + 1])
                    j += 2
                    continue
                buf.append(src[j])
                j += 1
            word()[0].extend(buf)
            i = j + 1
            continue
        if c == "'" and dialect != CMD:
            j, buf = i + 1, []
            while j < n:
                if src[j] == "'":
                    if dialect == PS and src[j + 1:j + 2] == "'":
                        buf.append("'")
                        j += 2
                        continue
                    break
                buf.append(src[j])
                j += 1
            word()[0].extend(buf)
            i = j + 1
            continue
        if c == '"':
            j, buf = i + 1, []
            while j < n:
                d = src[j]
                if d == '"':
                    if dialect == PS and src[j + 1:j + 2] == '"':
                        buf.append('"')
                        j += 2
                        continue
                    break
                if dialect == SH and d == '\\' and src[j + 1:j + 2] in ('"', '\\', '$', '`', '\n'):
                    buf.append(src[j + 1])
                    j += 2
                    continue
                if dialect == PS and d == '`' and j + 1 < n:
                    buf.append(src[j + 1])
                    j += 2
                    continue
                buf.append(d)
                j += 1
            word()[0].extend(buf)
            i = j + 1
            continue
        if dialect == SH and c == '`':
            j = i + 1
            while j < n and src[j] != '`':
                j += 2 if src[j] == '\\' else 1
            w = word()
            w[0].append(GROUP)
            w[1].append(src[i + 1:j])
            i = j + 1
            continue
        if c == '$' and nxt == '{':
            j = src.find('}', i)                     # ${변수} — 글이다
            j = n - 1 if j < 0 else j
            word()[0].append(src[i:j + 1])
            i = j + 1
            continue
        if c in '({' or (c == '$' and nxt == '('):
            at = i + 1 if c == '$' else i
            opener = src[at]
            closer = ')' if opener == '(' else '}'
            j = close_of(src, at, opener, closer, dialect)
            if j > 0:
                w = word()
                w[0].append(GROUP)
                w[1].append(src[at + 1:j])
                i = j + 1
                continue
        if c == ';':
            end_pipe()
            i += 1
            continue
        if c == '|':
            if nxt == '|':
                end_pipe()
                i += 2
                continue
            end_seg()
            i += 2 if nxt == '&' else 1
            continue
        if c == '&':
            prev = ''.join(cur[0])[-1:] if cur is not None else ''
            if prev in ('>', '<') or nxt == '>':     # 2>&1 · >&2 · &> — 넘김이다
                word()[0].append('&')
                i += 1
                continue
            if nxt == '&':
                end_pipe()
                i += 2
                continue
            if dialect == PS:                        # 부름 연산자 — 뒤가 돌 명령이다
                end_word()
                words.append(('&', []))
                i += 1
                continue
            end_pipe()
            i += 1
            continue
        if dialect == SH and c == '<' and nxt == '<' and src[i + 2:i + 3] != '<':
            j, strip = i + 2, src[i + 2:i + 3] == '-'
            j += 1 if strip else 0
            while j < n and src[j] in ' \t':
                j += 1
            m = HEREDOC_DELIM.match(src, j)
            if m:
                end_word()
                delim = next(g for g in m.groups() if g is not None)
                docs.append((delim, strip))
                words.append(('<<' + delim, []))
                i = m.end()
                continue
        word()[0].append(c)
        i += 1
    end_pipe()
    return pipes


# ── 단 읽기 ───────────────────────────────────────────────────────────────────────────────────────────────
def cmd_name(text):
    """낱말의 명령 이름 — 마지막 경로 조각 · 소문자 · `.exe` 뺌."""
    base = re.split(r'[\\/]', text)[-1].lower()
    return base[:-4] if base.endswith('.exe') else base


def effective(seg, dialect):
    """단에서 실제로 도는 명령 낱말의 자리 — 앞붙이 · 이름=값 · PowerShell 의 `$x =` 를 걷는다. 없으면 None."""
    k = 0
    while k < len(seg):
        text = seg[k][0]
        name = cmd_name(text)
        if dialect == SH and ASSIGN.match(text):
            k += 1
            continue
        if dialect == PS and text.startswith('$') and k + 1 < len(seg) and seg[k + 1][0] == '=':
            k += 2
            continue
        if name in PREFIX_CMDS:
            k += 1
            while k < len(seg):
                opt = seg[k][0]
                if opt.startswith('-') and len(opt) > 1:
                    k += 2 if opt in PREFIX_VALUE_OPTS.get(name, ()) else 1
                    continue
                if name == 'env' and ASSIGN.match(opt):
                    k += 1
                    continue
                break
            if name == 'timeout' and k < len(seg):
                k += 1
            continue
        return k
    return None


def head_of(seg, dialect):
    """(명령 이름, 인자 글 목록) — 도는 명령이 없으면 (None, [])."""
    k = effective(seg, dialect)
    if k is None:
        return None, []
    return cmd_name(seg[k][0]), [t for t, _ in seg[k + 1:]]


def params(args):
    """PowerShell 꼴 매개변수 이름들 — `-` 를 떼고 소문자 · `:값` 뺌."""
    return [a[1:].lower().split(':')[0] for a in args if a.startswith('-') and len(a) > 1]


def ps_host_kind(p):
    """powershell 매개변수 → command · file · encoded · value · flag."""
    if p == 'c' or (len(p) >= 2 and 'command'.startswith(p)):
        return 'command'
    if p == 'f' or (len(p) >= 2 and 'file'.startswith(p)):
        return 'file'
    if p in ('e', 'ec') or (len(p) >= 2 and 'encodedcommand'.startswith(p)):
        return 'encoded'
    if p in PS_HOST_VALUE_SHORT or (len(p) >= 2 and 'executionpolicy'.startswith(p)) or \
            (len(p) >= 2 and any(v.startswith(p) for v in PS_HOST_VALUE)):
        return 'value'
    return 'flag'


def host_inner(seg, dialect):
    """셸을 띄우는 단이 돌리는 안쪽 명령 글 — [(글, 문법)]."""
    name, args = head_of(seg, dialect)
    if name in PS_HOSTS:
        j = 0
        while j < len(args):
            a = args[j]
            if a.startswith('-') and len(a) > 1:
                kind = ps_host_kind(a[1:].lower().split(':')[0])
                if kind == 'command':
                    rest = args[j + 1:]
                    return [] if not rest or rest == ['-'] else [(' '.join(rest), PS)]
                if kind == 'file':
                    return [(' '.join(args[j + 1:]), PS)]
                if kind == 'encoded':
                    try:
                        return [(base64.b64decode(args[j + 1]).decode('utf-16-le'), PS)]
                    except (IndexError, ValueError):
                        return []
                j += 2 if kind == 'value' else 1
                continue
            return [(' '.join(args[j:]), PS)]
        return []
    if name in SH_HOSTS:
        j = 0
        while j < len(args):
            a = args[j]
            if a in SH_HOST_VALUE:
                j += 2
                continue
            if a.startswith('-') and not a.startswith('--') and 'c' in a[1:]:
                return [(args[j + 1], SH)] if j + 1 < len(args) else []
            if a[:1] in ('-', '+'):
                j += 1
                continue
            return []
        return []
    if name in CMD_HOSTS:
        for j, a in enumerate(args):
            if a.lower() in ('/c', '/k', '//c', '//k'):
                return [(' '.join(args[j + 1:]), CMD)]
        return []
    return []


def inner_texts(seg, dialect):
    """이 단이 **돌리는** 안쪽 명령 글 — 도는 낱말이 묶음이면 그 안 · 셸을 띄우는 명령이면 그 안. [(글, 문법)]."""
    k = effective(seg, dialect)
    out = []
    if k is not None and seg[k][0].startswith(GROUP):
        out += [(t, dialect) for t in seg[k][1]]
    return out + host_inner(seg, dialect)


def find(seg, dialect, fn, depth=0):
    """fn(단, 문법)이 참인 첫 값 — 이 단과, 이 단이 돌리는 안쪽 명령의 모든 단에서 찾는다. 없으면 None."""
    got = fn(seg, dialect)
    if got or depth >= MAX_DEPTH:
        return got
    for text, d in inner_texts(seg, dialect):
        for pipe in parse(text, d):
            for s in pipe:
                got = find(s, d, fn, depth + 1)
                if got:
                    return got
    return None


def walk(src, dialect, depth=0):
    """명령 글과 그 안쪽(묶음 · 셸을 띄우는 명령 · 인자 안의 묶음)의 파이프를 다 낸다 — (파이프, 문법)."""
    if depth > MAX_DEPTH:
        return
    for pipe in parse(src, dialect):
        yield pipe, dialect
        for seg in pipe:
            for _, nested in seg:
                for text in nested:
                    yield from walk(text, dialect, depth + 1)
            for text, d in host_inner(seg, dialect):
                yield from walk(text, d, depth + 1)


# ── 판정 ─────────────────────────────────────────────────────────────────────────────────────────────────
def is_kill_verb(seg, dialect):
    name, _ = head_of(seg, dialect)
    return name in STOP_VERBS or name == 'taskkill' or (name == 'kill' and dialect == PS)


def is_lister(seg, dialect):
    """Get-Process 가 -Id 없이 고른다 — 이름 · 속성으로 고른 것이다."""
    name, args = head_of(seg, dialect)
    return (name in LISTERS or (name == 'ps' and dialect == PS)) and 'id' not in params(args)


def is_pid_lookup(seg, dialect):
    return head_of(seg, dialect)[0] in PID_LOOKUPS


def arg_runs(seg, dialect, fn):
    """인자 안의 묶음(`$(pgrep x)` · `(Get-Process x)`)이 fn 에 걸리나."""
    for _, nested in seg[1:]:
        for text in nested:
            for pipe in parse(text, dialect):
                if any(find(s, dialect, fn) for s in pipe):
                    return True
    return False


def kill_by_name(pipe, i, dialect):
    """파이프의 i 째 단이 이름 · 창 제목으로 끄면 그 꼴 이름 — 아니면 None."""
    seg = pipe[i]
    name, args = head_of(seg, dialect)
    upstream = pipe[:i]
    if name in ('pkill', 'killall'):
        return name
    if name == 'taskkill':
        low = [a.lower() for a in args]
        for j, a in enumerate(low):
            flag = a.lstrip('/-')
            if a[:1] in ('/', '-') and flag == 'im':
                return 'taskkill /IM'
            if a[:1] in ('/', '-') and flag == 'fi' and j + 1 < len(low) and not low[j + 1].lstrip().startswith('pid'):
                return 'taskkill /FI'
        return None
    if name in STOP_VERBS or (name == 'kill' and dialect == PS):
        ps_ = params(args)
        least = 2 if name == 'kill' else 1
        if any((len(p) >= least and 'name'.startswith(p)) or (len(p) >= 3 and 'processname'.startswith(p)) for p in ps_):
            return 'Stop-Process -Name'
        if arg_runs(seg, dialect, is_lister):       # -Id (Get-Process x).Id · -InputObject (Get-Process x)
            return 'Get-Process 가 고른 것을 Stop-Process'
        if 'id' in ps_:
            return None
        if any(find(s, dialect, is_lister) for s in upstream):
            return 'Get-Process 가 고른 것을 Stop-Process'
        return None
    if name in ('foreach-object', '%', 'foreach') and any(a.lower() == 'kill' for a in args):
        if any(find(s, dialect, is_lister) for s in upstream):
            return 'Get-Process 가 고른 것을 ForEach-Object Kill'
        return None
    if name == 'kill':
        if any(find(s, dialect, is_pid_lookup) for s in upstream) or arg_runs(seg, dialect, is_pid_lookup):
            return 'pgrep 이 고른 것을 kill'
    return None


def state_script(seg, dialect):
    """이 단이 실행하는 STATE_SCRIPTS 의 이름 — 도는 낱말이거나, 스크립트를 받아 돌리는 명령의 인자다. 읽기만 하는 판
    (READ_ONLY_ARGS · PLAN_UNLESS)이거나 아니면 None."""
    k = effective(seg, dialect)
    if k is None:
        return None
    j = k
    m = STATE_NAME.search(seg[k][0].lower())
    if not m and cmd_name(seg[k][0]) in PS_HOSTS + SH_HOSTS + RUNNERS:
        for j in range(k + 1, len(seg)):
            m = STATE_NAME.search(seg[j][0].lower())
            if m:
                break
    if not m:
        return None
    name = m.group(1)
    args = [t.lower().split(':')[0] if t.startswith('-') else t.lower() for t, _ in seg[j + 1:]]
    if any(a in READ_ONLY_ARGS.get(name, ()) for a in args):
        return None
    if name in PLAN_UNLESS and PLAN_UNLESS[name] not in args:
        return None
    return name


def truncates(seg, dialect):
    """앞만 읽고 끊는 자 — head · Select-Object -First."""
    name, args = head_of(seg, dialect)
    if name == 'head':
        return True
    return name in ('select-object', 'select') and any(p and 'first'.startswith(p) for p in params(args))


def state_truncated(pipe, dialect):
    for i, seg in enumerate(pipe):
        script = find(seg, dialect, state_script)
        if script and any(truncates(s, dialect) for s in pipe[i + 1:]):
            return script
    return None


def judge(command, tool_name):
    """(판단, 까닭) — 판단은 'deny' · 'ask' · None."""
    dialect = TOOL_DIALECT.get(tool_name, SH)
    raw = command.lower()
    kills, scripts = [], []
    segs = []
    for pipe, d in walk(command, dialect):
        for i in range(len(pipe)):
            why = kill_by_name(pipe, i, d)
            if why and why not in kills:
                kills.append(why)
        script = state_truncated(pipe, d)
        if script and script not in scripts:
            scripts.append(script)
        segs += [(s, d) for s in pipe]
    if 'mainwindowtitle' in raw and (any(is_kill_verb(s, d) for s, d in segs) or '.kill(' in raw or '.closemainwindow(' in raw):
        kills.append('창 제목(MainWindowTitle)으로 고른 것을 끈다')
    if '.kill(' in raw and (any(is_lister(s, d) for s, d in segs) or 'getprocessesbyname' in raw):
        kills.append('이름으로 고른 프로세스의 .Kill()')
    why = []
    if scripts:
        why.append(WHY_STATE % ' · '.join(scripts))
    if kills:
        why.append(WHY_KILL % ' · '.join(kills))
    if not why:
        return None, ''
    return ('deny' if scripts else 'ask'), ' '.join(why)


def main():
    hook_input = json.load(sys.stdin)
    command = (hook_input.get('tool_input') or {}).get('command')
    if not isinstance(command, str):
        return 0
    decision, why = judge(command, hook_input.get('tool_name') or '')
    if decision:
        sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': decision,
                                                            'permissionDecisionReason': why}}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
