"""Claude 에게 일을 맡기고 답을 파일로 받는다 — 맡기는 쪽(Codex · agy)이 콘솔 있는 `python` 으로 부르고 끝날 때까지 기다린다.

    python claude_bg.py --prompt-file <파일> --out <답 파일> --cwd <작업 자리> [--write | --review [대상]]
                        [--resume <id>] [--model <이름>] [--timeout <초>] [--max-findings <n>]

내는 것 — 답과 맨 끝 줄 `[claude-bg] …` 을 `--out` 파일에 쓴다(인자가 틀렸어도 러너가 멈췄어도). 모드 셋 · 끝 줄의 칸 · 종료
코드 · 이어 묻기 · 규범이 어떻게 실리나는 `--help` 가 든다(표준 출력에 찍는 것은 그것뿐이다).
레인마다 무엇을 열고 닫나 · 사용자 설정을 어떻게 싣나 · 빌린 자리는 `references/DESIGN.md` 가 든다.
"""
import glob
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

EXIT = {'ok': 0, 'failed': 1, 'denied': 1, 'quota': 2, 'empty': 2, 'timeout': 3, 'usage': 4}
FOOTER = '[claude-bg]'
# 갈래 낱말의 뜻 — `--help` 의 종료 코드 표가 `EXIT` 의 이름마다 단다. 갈래 낱말은 끝 줄의 첫 낱말이기도 하다
STATUS_WORDS = {'ok': '답이 왔다', 'failed': '실패했다(러너가 멈춘 것 포함)',
                'denied': '거절된 도구 호출이 있다(리뷰 모드 밖) — 답이 그 도구 없이 지어졌다', 'quota': '한도 · 과부하',
                'empty': '빈 답', 'timeout': '시간 초과',
                'usage': '부르는 법이 틀렸다(인자 · 작업 자리 · 프롬프트 파일의 인코딩) 또는 Claude CLI 가 없다'}
# 끝 줄의 칸 — (이름, 뜻). 끝 줄을 짓는 `footer_line` 과 `--help` 가 같이 읽고, 차례가 끝 줄의 차례다
FOOTER_FIELDS = (
    ('rc', '받는 Claude 프로세스의 종료 코드'),
    ('elapsed', '걸린 시간 — `<N>s` 꼴(초)'),
    ('mode', '레인 — read(읽기만) · write(--write) · review(--review)'),
    ('norms', '시스템 프롬프트에 실은 홈 규범 — 홈 CLAUDE.md 와 거기서 `@경로` 로 푼 파일의 수. 홈 CLAUDE.md 가 없으면 `-`'),
    ('model', '받는 Claude 가 쓴 모델. 못 읽으면 `-`'),
    ('tools', '쓴 도구와 횟수 `<이름>:<수>`(쉼표로 여럿), 없으면 `-` — 읽기 · 검색이 없는 답은 기억으로 낸 것이다'),
    ('denied', '거절된 도구 호출 `<이름>:<수>` — 리뷰 모드에서 답이 온 때만(울타리가 한 일이라 실패로 안 친다)'),
    ('tokens', '`tokens in=<N> out=<N>` — 입력 · 출력 토큰'),
    ('resume', '이어 묻기 값 `<id>` — 대화 기록이 실제로 남았을 때만. 아니면 `-` 와 까닭'),
    ('raw', '날 출력(jsonl) 파일 경로 — 답이 안 온 갈래에서만'),
)

READ_TOOLS = 'Read,Glob,Grep,WebFetch,WebSearch'   # 읽기 · 찾기 · 웹 읽기 — 셸 · 쓰기는 모델이 아예 못 본다
WRITE_TOOLS = ('Edit', 'Write')                   # 고치기 레인에 더 보이는 것 — 셸은 끝내 안 연다
WRITE_SCOPE = './**'                              # 허락은 작업 자리 안만 — 띄우는 자리(`--cwd`) 기준이다
NO_HOOKS = {'disableAllHooks': True}
# 홈 규범 — 사용자 설정을 설정 원천으로 안 실으면 홈 CLAUDE.md 도 함께 꺼져, 래퍼가 그 글의 `@경로` 를 풀어 시스템 프롬프트에
# 덧붙인다(까닭은 references/DESIGN.md 「홈 규범」)
NORMS_FILE = 'CLAUDE.md'
IMPORT_DEPTH = 5                                               # `@경로` 를 따라 들어가는 깊이 — 하네스의 한도와 같다
IMPORT_TOKEN = re.compile(r'(?<![\w`])@(~?[^\s`()\[\]<>]+)')   # 줄 어디서든 `@경로` — 글자 · 백틱 바로 뒤의 @(메일 · 코드)는 아니다
CLAUDE_ARGS = ['-p', '--output-format', 'stream-json', '--verbose', '--strict-mcp-config', '--permission-mode', 'dontAsk']
NO_SKILLS = '--disable-slash-commands'   # 리뷰 모드 밖에서는 스킬을 끈다
# 리뷰 모드(`--review`) — 내장 리뷰 스킬과 그 등급. 등급은 후보마다 검증 에이전트를 띄우는 가장 낮은 것이다
REVIEW_COMMAND = '/code-review'
REVIEW_LEVEL = 'medium'
# 리뷰 모드에 더 보이는 것 — git 읽기용 셸 · 검증 에이전트. ⚠ 셸에 허락 규칙을 걸지 않는다 — `Bash(git diff:*)` 같은 접두
# 허락은 `git diff --output=<파일>` 같은 쓰기 꼴까지 연다(안 걸면 Claude Code 가 읽기로 가르는 명령만 선다)
REVIEW_TOOLS = ('Bash', 'Agent')
# 대상 칸 — 깃발 꼴(`--fix` · `--comment` …)과 등급 이름(`ultra` …)은 그 스킬이 대상이 아니라 다른 뜻으로 읽는다
REVIEW_TARGET_RE = re.compile(r'[^\s-]\S*')
REVIEW_LEVEL_NAMES = ('low', 'medium', 'high', 'xhigh', 'max', 'ultra')
MAX_FINDINGS_RE = re.compile(r'[1-9][0-9]*|all')
# 러너가 띄운 대화의 표 — 요청이 루프백 프록시를 지날 때만 받는 Claude 의 모든 요청(그 레인 것까지)에 머리 하나를 싣는다. 프록시는
# 그 대화를 레인처럼 도구 결과를 기다릴 때만 데운다 — 답하고 끝난 러너의 대화에 데우기를 안 버린다. 이름은 프록시의
# `RUNNER_HEADER` 와 같아야 한다. 하네스의 머리 칸(`Name: Value` 를 줄마다)에 이미 든 머리는 그대로 두고 덧붙인다
CUSTOM_HEADERS_ENV = 'ANTHROPIC_CUSTOM_HEADERS'
RUNNER_HEADER = 'x-agent-runner'
RUNNER_HEADER_VALUE = 'claude-background'
# 대화 기록의 자리 — 설정 폴더(`config_dir`)의 `projects/<작업 자리 이름>/<id>.jsonl`(Claude Code 2.1.296). 작업 자리 이름을
# 짓는 규칙은 빌리지 않는다 — `projects/*` 를 다 본다.
NO_RESUME = ('이어 묻기 못 함 — 대화 기록이 안 남았다({where} 에 이 대화가 없다). 받는 Claude 가 제 홈에 못 쓰는 자리'
             '(맡긴 쪽의 샌드박스)에서 돌았거나 대화가 서기 전에 멈췄다')


# 러너 넷이 함께 쓰는 손은 곁에 깔린 스킬 agent-envelope 의 `runner_common.py` 가 들고, 싣는 이름은 그 스킬의 `handout.py` 에
# 적힌 것뿐이다. 러너는 창 없이 돌아 말할 곳이 답 파일뿐이라, 그 부품을 못 실으면 여기서 답 파일에 끝 줄을 남기고 끝낸다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'agent-envelope' / 'scripts'))
try:
    import runner_common as common
    from runner_common import CLAUDE_DROP_ENV, CLAUDE_MODEL_RE, DEFAULT_TIMEOUT_SEC, PROMPT_ENCODINGS, write
except ImportError as missing:
    _args = sys.argv[1:]
    _out = next((x[len('--out='):] for x in _args if x.startswith('--out=')), None)
    if _out is None and '--out' in _args[:-1]:
        _out = _args[_args.index('--out') + 1]
    if _out:
        try:
            with open(_out, 'w', encoding='utf-8-sig' if os.name == 'nt' else 'utf-8') as _f:
                _f.write(f'{FOOTER} failed · 공유 부품이 없다 — {missing}. 스킬 agent-envelope 이 이 스킬 곁에 깔려야 '
                         '한다(설치를 다시 돌린다)\n')
        except OSError:
            pass
    sys.exit(EXIT['failed'])


def transcripts_dir():
    return os.path.join(common.config_dir(), 'projects')


def resume_field(conv):
    """끝 줄의 이어 묻기 칸 — 대화 기록 파일이 있을 때만 id 를 싣는다. 없으면 `-` 와 까닭."""
    if not conv:
        return 'resume=-'
    where = transcripts_dir()
    if glob.glob(os.path.join(glob.escape(where), '*', glob.escape(conv) + '.jsonl')):
        return f'resume={conv}'
    return 'resume=- · ' + NO_RESUME.format(where=where)


def head():
    """띄울 머리. 못 찾으면 None. 검사가 가짜 CLI 로 바꿔 끼우는 자리다."""
    return common.claude_head()


def tool_args(write, review=False):
    """보일 도구와 미리 허락한 도구. 고치기 레인이면 편집 도구를 더하되 허락은 작업 자리 안으로 가둔다. 리뷰 모드면 셸 ·
    `Agent` 를 더하되 셸에는 허락 규칙을 안 건다(`REVIEW_TOOLS`)."""
    if review:
        return ['--tools', ','.join([READ_TOOLS, *REVIEW_TOOLS]), '--allowedTools', ','.join([READ_TOOLS, 'Agent'])]
    if not write:
        return ['--tools', READ_TOOLS, '--allowedTools', READ_TOOLS]
    shown = ','.join([READ_TOOLS, *WRITE_TOOLS])
    allowed = ','.join([READ_TOOLS, *(f'{t}({WRITE_SCOPE})' for t in WRITE_TOOLS)])
    return ['--tools', shown, '--allowedTools', allowed]


def settings_args(dest):
    """설정 인자 — 사용자 설정을 설정 원천으로 안 싣고(`--setting-sources ""`), 그 파일에서 허락 규칙(`permissions.allow`)만
    빼고 훅을 끈 것을 `dest` 파일에 써서 그 경로를 `--settings` 로 준다. 레인의 울타리는 래퍼가 건 허락이 다여야 한다 —
    사람의 허락 규칙이 서면 리뷰 모드의 셸(이슈 닫기 · 다른 레인 띄우기)과 고치기 레인의 편집(작업 자리 밖)이 묻지 않고
    선다. 자리 값(`env` · 모델)과 막는 규칙은 그대로 간다. 파일은 띄울 때마다 다시 읽는다 — 사본을 안 든다.
    ⚠ 설정을 명령줄에 JSON 으로 싣지 않는다 — `env` 에 키가 든 설정이면 그 키가 같은 사용자의 모든 프로세스 목록에 보이고,
    명령줄 한도(32767 자)도 넘을 수 있다. `dest` 는 부르는 쪽(`run_once`)이 끝나면 지운다."""
    path = os.path.join(common.config_dir(), 'settings.json')
    try:
        with open(path, encoding='utf-8-sig') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}
    permissions = dict(settings.get('permissions') or {})
    permissions.pop('allow', None)
    with open(dest, 'w', encoding='utf-8') as f:
        json.dump({**settings, 'permissions': permissions, **NO_HOOKS}, f)
    return ['--setting-sources', '', '--settings', dest]


def review_command(target, max_findings):
    """리뷰 모드의 표준 입력 — 내장 리뷰 스킬을 부르는 한 줄. 두 값은 `run` 이 꼴을 본 것이다."""
    return ' '.join([REVIEW_COMMAND, REVIEW_LEVEL, *(['--max-findings', max_findings] if max_findings else []),
                     *([target] if target else [])])


def expand_imports(text, base_dir, depth, seen):
    """`@경로` 를 그 파일의 글로 바꾼다 — 상대 경로는 가져오는 파일의 폴더 기준이고 `~` 는 홈이다. 없는 파일 · 되돌이 · 깊이를
    넘긴 것은 그대로 둔다. 돌려주는 것 — (바뀐 글, 푼 파일 수).
    하네스의 CLAUDE.md 가져오기를 작게 흉내 낸 것이다 — 걷는 조건: 하네스가 `--setting-sources` 와 CLAUDE.md 읽기를 따로
    가르게 되면 이 함수와 `norms_text` 를 걷고 `--setting-sources user` 로 돌아간다."""
    count = 0

    def sub(m):
        nonlocal count
        raw = m.group(1)
        stripped = raw.rstrip('.,;:')
        trail = raw[len(stripped):]
        path = os.path.normpath(os.path.join(base_dir, os.path.expanduser(stripped)))
        key = os.path.normcase(path)
        if depth <= 0 or key in seen or not os.path.isfile(path):
            return m.group(0)
        try:
            with open(path, encoding='utf-8-sig') as f:
                body = f.read()
        except (OSError, UnicodeDecodeError):
            return m.group(0)
        inner, n = expand_imports(body, os.path.dirname(path), depth - 1, seen | {key})
        count += 1 + n
        return inner.rstrip('\n') + trail
    return IMPORT_TOKEN.sub(sub, text), count


def norms_text(home):
    """홈 CLAUDE.md 를 가져오기까지 풀어 돌려준다 — (글, 푼 파일 수 — 홈 CLAUDE.md 포함). 홈 CLAUDE.md 가 없으면 (None, 0)."""
    path = os.path.join(home, NORMS_FILE)
    try:
        with open(path, encoding='utf-8-sig') as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return None, 0
    expanded, n = expand_imports(text, os.path.dirname(path), IMPORT_DEPTH, {os.path.normcase(path)})
    return expanded, n + 1


def argv(model, resume, write=False, review=False, system_file=None, settings_file=None):
    """머리 뒤에 붙일 인자 — 프롬프트는 안 싣는다(표준 입력). 이어 물을 때도 고치기 레인이면 `--write` 를 다시 준다.
    `review` 면 리뷰 모드로 띄운다. `system_file` 은 시스템 프롬프트에 덧붙일 파일(홈 규범 · 리뷰 모드의 봉투)이다. 넘길 설정은
    `settings_file` 에 쓴다."""
    out = list(CLAUDE_ARGS) + settings_args(settings_file) + ([] if review else [NO_SKILLS]) + tool_args(write, review)
    if system_file:
        out += ['--append-system-prompt-file', system_file]
    if model:
        out += ['--model', model]
    if resume:
        out += ['--resume', resume]
    return out


def judge(events, rc, err_text, review=False):
    """(갈래, 답, 이어 묻기 id, 까닭, 토큰, 모델, 쓴 도구 {이름: 수}). 판정은 마지막 `result` 이벤트가 든다.
    리뷰 모드(`review`)의 거절은 실패로 안 친다 — 셸을 git 읽기로만 연 울타리가 한 일이다(리뷰어가 코드를 돌려 보려는 호출이
    거절된다). 답은 그대로 받고, 거절된 도구는 까닭 칸에 `<이름>:<수>` 로 실어 끝 줄이 `denied=` 로 남긴다."""
    result, model, tools = None, '-', {}
    for e in events:
        t = e.get('type')
        if t == 'system' and e.get('subtype') == 'init':
            model = e.get('model') or model
        elif t == 'assistant':
            for b in (e.get('message') or {}).get('content') or []:
                if b.get('type') == 'tool_use':
                    tools[b.get('name') or '?'] = tools.get(b.get('name') or '?', 0) + 1
        elif t == 'result':
            result = e
    result = result or {}
    answer = result.get('result') or ''
    conv = result.get('session_id')
    usage = result.get('usage') or {}
    tokens = f'in={usage.get("input_tokens", "-")} out={usage.get("output_tokens", "-")}'
    denials = [d for d in result.get('permission_denials') or [] if d]
    reason = ''
    if rc != 0 or not result or result.get('is_error') or result.get('subtype') != 'success':
        reason = answer or result.get('subtype') or '결과 이벤트가 없다'
        quota = common.claude_quota(result.get('api_error_status'), f'{reason}\n{err_text}')
        status = 'quota' if quota else 'failed'
    elif denials and not review:
        status = 'denied'
        reason = '거절된 도구 호출 — 답이 그 도구 없이 지어졌다: ' + ', '.join(
            str(d.get('tool_name') or d) if isinstance(d, dict) else str(d) for d in denials)
    elif not answer.strip():
        status = 'empty'
    else:
        status = 'ok'
        if denials:
            names = [str(d.get('tool_name') or '?') if isinstance(d, dict) else str(d) for d in denials]
            reason = ','.join(f'{n}:{names.count(n)}' for n in sorted(set(names)))
    return status, answer, conv, reason, tokens, model, tools


def child_env(env):
    """받는 Claude 에 줄 환경 — 부른 쪽 세션의 표지를 걷고, 요청이 루프백 프록시를 지나면 러너의 표 머리를 싣는다(`RUNNER_HEADER`).
    프록시가 없는 자리(사외 · 게이트웨이 직결)는 머리를 안 싣는다 — 그 자리의 요청은 지금과 같다."""
    out = {k: v for k, v in env.items() if k not in CLAUDE_DROP_ENV}
    if common.loopback_proxy(out):
        lines = [line for line in (out.get(CUSTOM_HEADERS_ENV) or '').splitlines()
                 if line.strip() and line.split(':', 1)[0].strip().lower() != RUNNER_HEADER]
        out[CUSTOM_HEADERS_ENV] = '\n'.join(lines + [f'{RUNNER_HEADER}: {RUNNER_HEADER_VALUE}'])
    return out


def run_once(cmd_head, a):
    """한 번 띄워 끝까지 지켜본다. 돌려주는 것 — (갈래, 종료 코드, 답, id, 까닭, 토큰, 모델, 도구, 날 출력 경로)."""
    # stderr 를 .md 로 둔다 — 회사 PC 의 Fasoo 가 .txt 를 감싸 러너가 제 꼬리를 못 읽는다(.md · .json 은 평문으로 남는다)
    raw_path, err_path = f'{a.out}.claude.jsonl', f'{a.out}.claude.stderr.md'
    settings_path = f'{a.out}.claude.settings.json'   # 넘길 설정 — 끝나면 지운다(`settings_args`)
    env = child_env(os.environ)
    # 시스템 프롬프트 파일(끝나면 지운다)에 홈 규범을 싣고, 리뷰 모드면 봉투를 그 뒤에 잇는다 — 그 모드의 표준 입력은 슬래시
    # 명령이라 봉투가 거기 못 간다. 받는 쪽은 `--cwd` 에서 돌아 절대 경로로 준다. 봉투 글은 `run` 이 읽어 둔 것이다
    body = a.prompt
    review = a.review is not None
    norms, norms_n = norms_text(common.config_dir())
    parts = ([norms] if norms else []) + ([body] if review else [])
    system_path = None
    if parts:
        system_path = os.path.abspath(f'{a.out}.claude.system.md')
        with open(system_path, 'wb') as f:   # 바이트로 — 글 모드는 윈도에서 줄끝을 CRLF 로 바꿔 쓴다
            f.write(('\n\n'.join(p.rstrip('\n') for p in parts) + '\n').encode('utf-8'))
    stdin_file = tempfile.TemporaryFile()
    stdin_file.write((review_command(a.review, a.max_findings) if review else body).encode('utf-8'))
    stdin_file.seek(0)
    try:
        with stdin_file as stdin:
            waited, rc, events, err_text = common.watch(
                cmd_head + argv(a.model, a.resume, a.write, review, system_path, settings_path),
                a.cwd, env, stdin, raw_path, err_path, a.timeout)
    finally:
        common.remove(settings_path, system_path)
    if waited == 'spawn':
        return 'spawn', None, '', None, err_text, 'in=- out=-', '-', {}, raw_path, norms_n
    judged, answer, conv, reason, tokens, model, tools = judge(events, rc, err_text, review)
    status = waited or judged
    reason = common.wrap_up(status, reason, err_text, raw_path, err_path)
    return status, rc, answer, conv, reason, tokens, model, tools, raw_path, norms_n


def build_parser():
    ap = common.base_parser('Claude 에게 일을 맡기고, 답과 끝 줄을 --out 파일로 받는다. 기본은 읽기만 한다.',
                            '받는 Claude 를 띄울 작업 자리 — 없는 폴더면 안 띄운다. --write 가 고치는 범위이기도 하다')
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SEC, metavar='SEC', help=f'시간 한도(초). 기본 {DEFAULT_TIMEOUT_SEC}')
    ap.add_argument('--model', metavar='NAME', help='받는 Claude 의 모델. 안 주면 사용자 설정의 모델로 뜬다')
    ap.add_argument('--resume', metavar='ID', help='이어 묻기 — 끝 줄 resume= 의 값을 그대로')
    ap.add_argument('--write', action='store_true', help='고치기 레인 — 작업 자리 안만 고친다(아래 「모드」)')
    ap.add_argument('--review', nargs='?', const='', metavar='TARGET',
                    help='리뷰 모드 — 값은 리뷰 대상(<pr#> · <가지> · <경로> 하나), 없으면 지금의 diff')
    ap.add_argument('--max-findings', metavar='N|all', help='리뷰 모드에서 그 스킬에 넘기는 한도 — 수나 all')
    return ap


def help_epilog():
    """`--help` 의 아래쪽 — 모드 · 끝 줄 · 이어 묻기 · 프롬프트 파일 · 종료 코드. 끝 줄 칸은 `FOOTER_FIELDS` 에서, 종료 코드는
    `EXIT` 에서 짓는다."""
    return '\n'.join([
        '모드(끝 줄 mode= 에 적힌다):',
        f'  read(기본)       읽기만 한다 — 보이는 도구가 {READ_TOOLS.replace(",", " · ")} 뿐이고 셸 · 쓰기 도구는 모델이 아예 못 본다.',
        '                   MCP 서버 · 스킬 · 훅은 끄고, 사용자 설정의 허락 규칙은 안 넘긴다. 목록 밖 호출은 묻지 않고 거절되며, 거절이 있으면 실패다.',
        '                   홈 규범(CLAUDE.md 와 `@경로` 가져오기)은 래퍼가 풀어 시스템 프롬프트로 싣는다(끝 줄 norms=) — 세 레인이 다 그렇다.',
        f'  --write          고치기 레인 — 편집 도구({" · ".join(WRITE_TOOLS)})를 더 보이되 허락은 작업 자리 안({WRITE_SCOPE})만이다. 셸은 끝내 안 연다.',
        '                   이어 물을 때도 다시 준다(안 주면 읽기 레인으로 이어진다).',
        f'  --review [대상]  리뷰 — 내장 리뷰 스킬({REVIEW_COMMAND} {REVIEW_LEVEL})을 켜고 셸 · 검증 에이전트({" · ".join(REVIEW_TOOLS)})를 더 보인다.',
        '                   셸은 Claude Code 가 읽기로 가르는 명령(git diff · git log · cat · grep 같은)만 서고 코드 돌리기 · 파일로 내보내기는 거절된다.',
        '                   그 거절은 울타리가 한 일이라 실패로 안 치고 끝 줄 denied= 로 남는다. 프롬프트 파일은 봉투로 홈 규범 뒤에 이어 시스템 프롬프트에 덧붙는다.',
        f'                   대상은 <pr#> · <가지> · <경로> 하나(깃발 꼴 · 등급 이름 {" · ".join(REVIEW_LEVEL_NAMES)} 는 안 받는다).',
        '                   --max-findings <수|all> 은 이 모드에서만 받는다. --write · --resume 과 같이 못 준다(`usage`).',
        '',
        f'끝 줄: 답 파일의 맨 끝 줄이다. `{FOOTER} <갈래>` 뒤에 아래 칸이 " · " 로 이어진다(없는 칸은 빠진다).',
        '  갈래는 아래 종료 코드 표의 이름이다. 인자가 틀렸거나 러너가 멈췄으면 칸 없이 `<갈래> · <까닭>` 만 든다.',
        *[f'  {name:<9}{meaning}' for name, meaning in FOOTER_FIELDS],
        '',
        '이어 묻기: 끝 줄 `resume=<id>` 의 값을 그대로 --resume 으로 준다. 고치기 레인이면 --write 도 다시 준다.',
        '  `resume=-` 는 대화 기록이 안 남았다는 뜻이다 — 새로 맡긴다.',
        '',
        f'프롬프트 파일: {PROMPT_ENCODINGS} 만 받는다. 래퍼가 UTF-8 로 옮겨 표준 입력으로 넘긴다(길이 한도 없음).',
        '  홈 규범(CLAUDE.md 와 거기서 `@경로` 로 가져온 파일)은 래퍼가 풀어 시스템 프롬프트 파일로 덧붙인다 — 사용자 설정을 안 싣는',
        '  띄우기에서는 하네스가 CLAUDE.md 를 안 읽어서다. 리뷰 모드의 봉투는 그 파일에 규범 뒤로 이어 간다(파일은 끝나면 지운다).',
        '  그 밖(PowerShell 5.1 의 Set-Content 기본인 ANSI 따위)은 `usage` 로 끝나고 까닭이 --out 파일에 남는다.',
        '',
        '종료 코드(끝 줄의 갈래 이름과 같다):',
        *common.exit_table(EXIT, STATUS_WORDS),
    ]) + '\n'


def review_problem(a):
    """리뷰 모드 인자가 틀린 까닭 — 없으면 None."""
    if a.review is None:
        return '--max-findings 는 --review 와 같이 준다' if a.max_findings else None
    if a.write or a.resume:
        return '--review 는 --write · --resume 과 같이 못 준다 — 리뷰는 읽기만 하는 새 대화다'
    if a.review and (not REVIEW_TARGET_RE.fullmatch(a.review) or a.review.lower() in REVIEW_LEVEL_NAMES):
        return f'--review 대상 {a.review!r} — 빈칸 없는 <pr#> · <가지> · <경로> 하나(깃발 꼴 · 등급 이름은 안 받는다)'
    if a.max_findings and not MAX_FINDINGS_RE.fullmatch(a.max_findings):
        return f'--max-findings {a.max_findings!r} — 1 이상의 수나 all'
    return None


def run(a):
    a.prompt, bad = common.read_prompt(a.prompt_file)
    if bad:
        write(a.out, f'{FOOTER} usage · {bad}\n')
        return EXIT['usage']
    if not os.path.isdir(a.cwd):
        write(a.out, f'{FOOTER} usage · --cwd 가 폴더가 아니다 — {a.cwd}\n')
        return EXIT['usage']
    if a.model and not CLAUDE_MODEL_RE.fullmatch(a.model):
        write(a.out, f'{FOOTER} usage · --model 에 따옴표 · 공백이 든다 — {a.model!r}\n')
        return EXIT['usage']
    bad = review_problem(a)
    if bad:
        write(a.out, f'{FOOTER} usage · {bad}\n')
        return EXIT['usage']
    cmd_head = head()
    if cmd_head is None:
        write(a.out, f'{FOOTER} usage · Claude Code CLI(`claude`)를 못 찾는다\n')
        return EXIT['usage']

    started = time.monotonic()
    status, rc, answer, conv, reason, tokens, model, tools, raw_path, norms_n = run_once(cmd_head, a)
    elapsed = int(time.monotonic() - started)
    if status == 'spawn':
        write(a.out, f'{FOOTER} usage · 못 띄웠다 — {reason}\n')
        return EXIT['usage']
    used = ','.join(f'{k}:{v}' for k, v in sorted(tools.items())) or '-'
    lane = 'write' if a.write else 'review' if a.review is not None else 'read'
    cells = {'rc': f'rc={rc}', 'elapsed': f'{elapsed}s', 'mode': f'mode={lane}', 'norms': f'norms={norms_n or "-"}',
             'model': f'model={model}', 'tools': f'tools={used}', 'tokens': f'tokens {tokens}', 'resume': resume_field(conv)}
    if status == 'ok' and reason:
        cells['denied'] = f'denied={reason}'   # 리뷰 모드의 거절 — `judge`
    if status != 'ok':
        cells['raw'] = f'raw={raw_path}'
    footer = common.footer_line(FOOTER, FOOTER_FIELDS, status, cells)
    common.write_answer(a.out, status, answer, footer, reason)
    return EXIT[status]


def main():
    return common.main(build_parser, help_epilog, run, FOOTER, EXIT)


if __name__ == '__main__':
    sys.exit(main())
