"""Claude 에게 일을 맡기고 답을 파일로 받는다 — Codex · agy 가 맡기는 쪽일 때의 러너(결정 0098 · 0100).

**받는 Claude 는 기본이 읽기만 한다.** 쓸 수 있는 도구를 읽기 · 찾기 · 웹 읽기(`READ_TOOLS`)로 좁혀 띄운다 — 셸 · 쓰기
도구는 모델에게 아예 안 보인다. 그래서 받는 쪽이 다른 에이전트를 다시 띄울 길(셸)도 없다. 묻지 않는 권한 방식(`dontAsk`)이라
목록 밖 호출은 묻는 대신 거절되고, 거절이 하나라도 있으면 실패로 친다 — 답이 그 도구 없이 지어졌다는 뜻이다(리뷰 모드는 아래).
**`--write` 를 주면 고치기 레인이다** — 편집 도구 둘(`WRITE_TOOLS`)을 더 보이되 허락은 작업 자리 안(`./**`)만 건다. 그
밖에 쓰려는 호출은 거절돼 실패로 남는다(실측 Claude Code 2.1.296 · 2026-10-10: 자리 안 `Edit` 은 섰고 자리 밖 `Write`
는 `permission_denials` 로 거절됐다 · 그 띄우기를 자동 모드 분류기가 안 막았다). 셸은 그래도 안 연다 — 윈도에는 Claude
샌드박스가 없어 셸이 자리를 못 지킨다. 검사 돌리기는 맡긴 쪽이 한다. 자리를 잘못 물려받지 않게 `--cwd` 를 받아야만 띈다.
**`--review [대상]` 을 주면 리뷰 모드다** — 내장 리뷰 스킬(`/code-review`)을 `REVIEW_LEVEL` 로 부르고, 여는 것은 그 스킬이
드는 만큼이다: 스킬을 켜고(`--disable-slash-commands` 를 뺀다), 셸과 검증 단계가 띄우는 `Agent` 를 보인다. 셸에는 허락 규칙을
안 건다 — Claude Code 가 읽기로 가르는 명령(`git diff` · `git log` · `cat` · `grep` 같은)만 서고, 코드 돌리기 · 파일로 내보내기
(`git diff --output=<파일>` 포함)는 거절된다(실측 2.1.300 · 2026-10-15). 사용자 설정의 허락 규칙도 안 선다 — 설정 원천을 안
싣고 그 파일에서 허락 규칙만 뺀 것을 넘긴다(`settings_args` · 세 레인이 다 그렇다). 그 거절은 울타리가 한 일이라 이 모드에서는 실패로 안
치고 끝 줄 `denied=` 로 남긴다(`judge`). 표준 입력이 그 슬래시 명령이 되고, 봉투(프롬프트
파일)는 시스템 프롬프트 덧붙이기(`--append-system-prompt-file`)로 간다 — 명령 뒤에 붙인 글은 리뷰 대상으로 읽힌다. 대상은
그 스킬의 낱말(`<pr#>` · `<가지>` · `<경로>`)이고 없으면 지금의 diff 다. 고치기 · 올리기 · 클라우드 리뷰 깃발(`--fix` ·
`--comment` · `ultra`)은 안 싣고, 대상 칸으로도 못 들어오게 깃발 꼴 · 등급 이름을 막는다. 고치기 레인 · 이어 묻기와는 같이
못 준다(4).
MCP 서버 · 슬래시 명령(스킬)은 끄고(리뷰 모드는 스킬을 켠다), 사용자 설정은 허락 규칙과 훅만 빼고 읽는다(`settings_args`) —
설정에는 자리 값(게이트웨이 주소 · 시간 한도 · 웹 가져오기 검증 건너뛰기)이 살고, 훅은 맡긴 일과 무관한 일(세션 시작 동기화
등)을 하며, 사람의 허락 규칙(이슈 닫기 · 다른 레인 띄우기 · 편집 자리)은 묻지 않는 권한 방식에서 그대로 서서 레인의 울타리를
넓힌다.
빌린 자리 — 상류 `pgpt-one-click-connect` 의 `app/optional-skills/pgpt-delegate/scripts/Invoke-PgptAgent.ps1` Claude
작업자 갈래(커밋 65e981a · 2026-10-09). 플래그 다섯(`--strict-mcp-config` · `--disable-slash-commands` · `--permission-mode
dontAsk` · `--tools` · `--allowedTools`)과 결과를 가르는 법(`subtype` · `is_error` · `permission_denials` · 빈 답)을
빌렸다. 일부러 가른 셋 — 설정은 안 끄고 훅만 끈다(상류는 게이트웨이를 제가 알아 값을 직접 넣지만 이 러너는 자리를
모른다) · 대화를 남긴다(이어 묻기 — agent-envelope 1 절) · 작업 규칙을 덧붙이지 않는다(봉투가 든다 — 결정 0095).
따라가는 법은 「일부러 갈랐다」 — 상류가 바뀌어도 이 러너는 따라가지 않는다.

**Codex 에서는 앞에서 기다린다** — 콘솔 있는 `python` 으로 부르면 끝날 때까지 돌아오지 않고, 끝나면 종료 코드로 갈래를
알린다. 답과 끝 줄은 `--out` 파일에 쓴다.

**프롬프트는 표준 입력으로 넘긴다** — 명령줄 길이 한도와 따옴표 해석을 안 탄다. 프롬프트 파일은 UTF-8 로 옮겨(`decode_prompt`)
넘긴다. npm 이 까는 실행 꼴(`.cmd` 셔틀)은 인자가 cmd.exe 를 거치므로, 셔틀이 부르는 것(꾸러미 `bin` 의 JS 나 실행 파일)을 바로
부른다.

맨 끝 줄 `[claude-bg] …` 의 칸과 종료 코드의 뜻은 `--help` 가 든다 — `FOOTER_FIELDS` · `EXIT` · `STATUS_WORDS` 에서 지어
찍으니 여기에 다시 적지 않는다(`--help` 만 표준 출력에 찍고, 나머지 말은 `--out` 파일로 간다).
**`--out` 을 받았으면 어느 갈래로 끝나든 답 파일과 끝 줄을 남긴다** — 인자가 틀렸어도, 러너가 멈췄어도 까닭을 적는다.
**이어 묻기 값은 대화 기록이 실제로 남았을 때만 싣는다** — 받는 Claude 가 제 홈에 못 쓰는 자리(맡긴 쪽의 샌드박스)에서
돌면 대화 id 는 나와도 기록이 없어 `--resume` 이 「No conversation found」로 진다(실측 2026-10-11 · Codex 샌드박스).
"""
import argparse
import codecs
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
DEFAULT_TIMEOUT_SEC = 1800      # 기본 한도 — 짧은 일도 그대로 둔다(끝나는 대로 돌아온다)
POLL_SEC = 2                    # 끝났나 보는 간격
STDERR_TAIL_CHARS = 2000        # 실패 때 답 파일에 옮기는 stderr 꼬리
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
# 프롬프트 파일이 받는 인코딩 — `decode_prompt` 가 받는 것과 같은 말이고 거절 사유 · `--help` 가 이 글을 읽는다
PROMPT_ENCODINGS = 'UTF-8(BOM 은 있어도 없어도) · UTF-16 LE/BE(BOM 이 있어야)'

READ_TOOLS = 'Read,Glob,Grep,WebFetch,WebSearch'   # 읽기 · 찾기 · 웹 읽기 — 셸 · 쓰기는 모델이 아예 못 본다
WRITE_TOOLS = ('Edit', 'Write')                   # 고치기 레인에 더 보이는 것 — 셸은 끝내 안 연다
WRITE_SCOPE = './**'                              # 허락은 작업 자리 안만 — 띄우는 자리(`--cwd`) 기준이다
NO_HOOKS = {'disableAllHooks': True}
# 홈 규범 — 받는 Claude 는 사용자 설정을 설정 원천으로 안 싣는데(`settings_args`), 그 플래그는 홈의 CLAUDE.md 도 같이 끈다(실측
#   2026-10-15 · Claude Code 2.1.300 · `--add-dir` 로도 안 실린다). 그래서 래퍼가 홈 CLAUDE.md 를 읽어 `@경로` 가져오기를 풀고 시스템
#   프롬프트에 덧붙인다 — 사람의 허락 규칙은 안 넘기면서 규범은 넘긴다. 경로에 걸리는 룰(`rules/`)은 안 온다 — 파일을 열 때
#   하네스가 싣는 것이라서다.
NORMS_FILE = 'CLAUDE.md'
IMPORT_DEPTH = 5                                               # `@경로` 를 따라 들어가는 깊이 — 하네스의 한도와 같다
IMPORT_TOKEN = re.compile(r'(?<![\w`])@(~?[^\s`()\[\]<>]+)')   # 줄 어디서든 `@경로` — 글자 · 백틱 바로 뒤의 @(메일 · 코드)는 아니다
CLAUDE_ARGS = ['-p', '--output-format', 'stream-json', '--verbose', '--strict-mcp-config', '--permission-mode', 'dontAsk']
NO_SKILLS = '--disable-slash-commands'   # 리뷰 모드 밖에서는 스킬을 끈다
# 리뷰 모드(`--review`) — 내장 리뷰 스킬과 그 등급. 등급은 후보마다 검증 에이전트를 띄우는 가장 낮은 것이다
REVIEW_COMMAND = '/code-review'
REVIEW_LEVEL = 'medium'
# 리뷰 모드에 더 보이는 것 — git 읽기용 셸 · 검증 에이전트. 셸에는 허락 규칙을 안 건다 — Claude Code 가 읽기로 가르는 명령
# (`git diff` · `git log` · `git show` · `git status`)만 서고, `git diff --output=<파일>` 같은 쓰기 꼴은 거절된다(실측 2.1.300 ·
# 2026-10-15). `Bash(git diff:*)` 같은 접두 허락은 그 쓰기 꼴까지 연다.
REVIEW_TOOLS = ('Bash', 'Agent')
# 대상 칸 — 깃발 꼴(`--fix` · `--comment` …)과 등급 이름(`ultra` …)은 그 스킬이 대상이 아니라 다른 뜻으로 읽는다
REVIEW_TARGET_RE = re.compile(r'[^\s-]\S*')
REVIEW_LEVEL_NAMES = ('low', 'medium', 'high', 'xhigh', 'max', 'ultra')
MAX_FINDINGS_RE = re.compile(r'[1-9][0-9]*|all')
# 셔틀(`.cmd`)이 부르는 꾸러미 — npm 전역 자리(셔틀 곁의 `node_modules`) 기준. 실제로 띄울 것은 꾸러미의
# `package.json` 의 `bin` 이 든다 — 판에 따라 JS(`cli.js`)이기도 하고 네이티브 실행 파일(`bin/claude.exe`)이기도 하다.
NPM_PACKAGE = ('@anthropic-ai', 'claude-code')
BIN_NAME = 'claude'
SHIM_EXT = ('.cmd', '.bat')
# Claude 세션 안에서 불려도 그 세션에 안 섞이게 — 부른 쪽 세션의 표지가 남으면 받는 쪽이 그 대화 id 를 이어 쓴다
# (실측 2026-10-09 · 리모트 세션: `CLAUDE_CODE_REMOTE_SESSION_ID` 를 걷어야 새 id 가 섰다)
DROP_ENV = ('CLAUDECODE', 'CLAUDE_CODE_SESSION_ID', 'CLAUDE_CODE_REMOTE_SESSION_ID')
# 한도 · 과부하의 꼴 — 결과의 `api_error_status`(429 · 529)나 문구. 다른 실패와 갈라야 「잠시 뒤 다시」와 「고칠 것」이 갈린다
QUOTA_STATUS = (429, 529)
QUOTA_RE = re.compile(r'usage limit|rate[_ ]limit|overloaded|\b429\b|\b529\b', re.I)
MODEL_NAME_RE = re.compile(r'[A-Za-z0-9._:/\[\]-]+')
# 답 파일의 인코딩. 윈도 PowerShell 5.1 의 `Get-Content` 는 BOM 없는 파일을 ANSI 코드 페이지(한국어 윈도는 949)로 읽어
# 한글과 끝 줄의 `·` 를 깨뜨린다(`·` → `쨌` — 실측 2026-10-11 · Codex 가 `Get-Content -Tail 1` 로 끝 줄을 읽었다). BOM 이 있으면
# UTF-8 로 읽는다. 다른 OS 는 BOM 없이 둔다 — 거기 셸은 UTF-8 로 읽고, BOM 은 첫 줄을 `^[claude-bg]` 로 찾는 손을 헛짚게 한다.
ANSWER_ENCODING = 'utf-8-sig' if os.name == 'nt' else 'utf-8'
# 대화 기록의 자리 — 설정 폴더(`CLAUDE_CONFIG_DIR`, 없으면 `~/.claude`)의 `projects/<작업 자리 이름>/<id>.jsonl`(실측
# Claude Code 2.1.296 · 윈도 · 2026-10-11). 작업 자리 이름을 짓는 규칙은 빌리지 않는다 — `projects/*` 를 다 본다.
CONFIG_DIR_ENV = 'CLAUDE_CONFIG_DIR'
NO_RESUME = ('이어 묻기 못 함 — 대화 기록이 안 남았다({where} 에 이 대화가 없다). 받는 Claude 가 제 홈에 못 쓰는 자리'
             '(맡긴 쪽의 샌드박스)에서 돌았거나 대화가 서기 전에 멈췄다')


def write(path, text):
    """답 파일을 쓴다 — 인코딩은 `ANSWER_ENCODING`."""
    with open(path, 'w', encoding=ANSWER_ENCODING) as f:
        f.write(text)


class Usage(Exception):
    """인자를 못 갈랐다. argparse 는 그 말을 stderr 에 찍고 끝내지만 부른 쪽은 답 파일을 읽는다 — 답 파일에 옮긴다."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


def out_arg(args):
    """인자를 못 갈랐을 때 답 파일 자리 — `--out <경로>` · `--out=<경로>` 만 찾는다. 없으면 None."""
    for i, x in enumerate(args):
        if x == '--out' and i + 1 < len(args):
            return args[i + 1]
        if x.startswith('--out='):
            return x[len('--out='):]
    return None


def decode_prompt(raw):
    """프롬프트 파일 바이트 → 글. 받는 인코딩은 `PROMPT_ENCODINGS` — 그 밖이면 UnicodeDecodeError. BOM 은 걷힌다.
    글에 NUL 이 있어도 거절한다: BOM 없는 UTF-16 · BOM 있는 UTF-32 는 UTF-8 로도 읽혀 NUL 이 낀 채 표준 입력으로 간다."""
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        text = raw.decode('utf-16')
    else:
        text = raw.decode('utf-8-sig')
    if '\x00' in text:
        raise UnicodeDecodeError('utf-8', raw, 0, len(raw), 'NUL 문자가 든다')
    return text


def prompt_problem(path):
    """프롬프트 파일을 못 넘기는 까닭 — 없으면 None. 받는 Claude 는 표준 입력을 UTF-8 로 읽는다: PowerShell 5.1 의
    `Set-Content` 기본값(ANSI)으로 쓴 파일은 글자가 깨진 채 넘어가 답이 조용히 틀어진다. 그래서 `decode_prompt` 가 받는
    인코딩만 넘기고, 넘길 때(`run_once`)는 UTF-8 로 옮긴다."""
    try:
        with open(path, 'rb') as f:
            decode_prompt(f.read())
    except OSError as e:
        return f'프롬프트 파일을 못 읽었다 — {e}'
    except UnicodeDecodeError:
        return (f'프롬프트 파일이 받는 인코딩이 아니다 — {PROMPT_ENCODINGS} 만 받는다. '
                f'PowerShell 5.1 이면 `Set-Content -Encoding utf8` 로 쓴다: {path}')
    return None


def footer_line(status, cells):
    """끝 줄 — `FOOTER <갈래>` 뒤에 칸을 `FOOTER_FIELDS` 의 차례로 ` · ` 로 잇는다. `cells` 는 {칸 이름: 꼴을 갖춘 글}이고 있는
    칸만 든다. 이름이 `FOOTER_FIELDS` 에 없으면 KeyError — 칸을 더하면서 뜻을 안 다는 일을 막는다."""
    unknown = set(cells) - {name for name, _ in FOOTER_FIELDS}
    if unknown:
        raise KeyError(f'FOOTER_FIELDS 에 없는 끝 줄 칸: {sorted(unknown)}')
    return ' · '.join([f'{FOOTER} {status}'] + [cells[name] for name, _ in FOOTER_FIELDS if name in cells])


def transcripts_dir():
    return os.path.join(os.environ.get(CONFIG_DIR_ENV) or os.path.join(os.path.expanduser('~'), '.claude'), 'projects')


def resume_field(conv):
    """끝 줄의 이어 묻기 칸 — 대화 기록 파일이 있을 때만 id 를 싣는다. 없으면 `-` 와 까닭."""
    if not conv:
        return 'resume=-'
    where = transcripts_dir()
    if glob.glob(os.path.join(glob.escape(where), '*', glob.escape(conv) + '.jsonl')):
        return f'resume={conv}'
    return 'resume=- · ' + NO_RESUME.format(where=where)


def kill_tree(proc):
    """띄운 node 와 그 밑 CLI 까지 같이 끊는다 — 머리만 끊으면 자식이 남는다."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)],
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
    else:
        proc.kill()
    proc.wait()


def resolve(found):
    """찾은 실행 꼴 → 띄울 머리. 셔틀이면 꾸러미의 `bin` 을 따라간다 — JS 면 node 로, 실행 파일이면 그대로. 못 풀면 None."""
    if not found.lower().endswith(SHIM_EXT):
        return [found]
    pkg = os.path.join(os.path.dirname(found), 'node_modules', *NPM_PACKAGE)
    try:
        with open(os.path.join(pkg, 'package.json'), encoding='utf-8') as f:
            bin_field = json.load(f).get('bin')
    except (OSError, ValueError):
        return None
    rel = bin_field.get(BIN_NAME) if isinstance(bin_field, dict) else bin_field
    target = os.path.join(pkg, rel) if isinstance(rel, str) else ''
    if not os.path.isfile(target):
        return None
    if not target.lower().endswith(('.js', '.mjs', '.cjs')):
        return [target]
    node = shutil.which('node')
    return [node, target] if node else None


def head():
    """띄울 머리. 못 찾으면 None."""
    found = shutil.which(BIN_NAME)
    return resolve(found) if found else None


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
    path = os.path.join(config_dir(), 'settings.json')
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


def config_dir():
    """받는 Claude 의 설정 폴더 — `CLAUDE_CONFIG_DIR` 가 서 있으면 그것, 아니면 홈의 `.claude`."""
    return os.environ.get(CONFIG_DIR_ENV) or os.path.join(os.path.expanduser('~'), '.claude')


def expand_imports(text, base_dir, depth, seen):
    """`@경로` 를 그 파일의 글로 바꾼다 — 상대 경로는 가져오는 파일의 폴더 기준이고 `~` 는 홈이다. 없는 파일 · 되돌이 · 깊이를
    넘긴 것은 그대로 둔다. 돌려주는 것 — (바뀐 글, 푼 파일 수).
    하네스의 CLAUDE.md 가져오기를 작게 흉내 낸 것이다(결정 0154) — 걷는 조건: 하네스가 `--setting-sources` 와 CLAUDE.md 읽기를 따로
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


def read_jsonl(path):
    out = []
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if line.startswith('{'):
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    except OSError:
        pass
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
        quota = result.get('api_error_status') in QUOTA_STATUS or QUOTA_RE.search(f'{reason}\n{err_text}')
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


def run_once(cmd_head, a):
    """한 번 띄워 끝까지 지켜본다. 돌려주는 것 — (갈래, 종료 코드, 답, id, 까닭, 토큰, 모델, 도구, 날 출력 경로)."""
    raw_path, err_path = f'{a.out}.claude.jsonl', f'{a.out}.claude.stderr.txt'
    settings_path = f'{a.out}.claude.settings.json'   # 넘길 설정 — 끝나면 지운다(`settings_args`)
    env = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    started = time.monotonic()
    status = None
    # 프롬프트는 UTF-8 로 옮겨 넘긴다(`decode_prompt`). 시스템 프롬프트 파일(`system_path` — 끝나면 지운다)에는 홈 규범
    # (`norms_text`)을 싣고, 리뷰 모드면 그 뒤에 봉투를 잇는다 — 리뷰 모드의 표준 입력은 슬래시 명령이라 봉투가 거기 못 간다.
    # 받는 쪽은 `--cwd` 에서 돌아 절대 경로로 준다
    with open(a.prompt_file, 'rb') as f:
        prompt_raw = f.read()
    body = decode_prompt(prompt_raw)
    review = a.review is not None
    norms, norms_n = norms_text(config_dir())
    parts = ([norms] if norms else []) + ([body] if review else [])
    system_path = None
    if parts:
        system_path = os.path.abspath(f'{a.out}.claude.system.txt')
        with open(system_path, 'wb') as f:   # 바이트로 — 글 모드는 윈도에서 줄끝을 CRLF 로 바꿔 쓴다
            f.write(('\n\n'.join(p.rstrip('\n') for p in parts) + '\n').encode('utf-8'))
    stdin_file = tempfile.TemporaryFile()
    stdin_file.write((review_command(a.review, a.max_findings) if review else body).encode('utf-8'))
    stdin_file.seek(0)
    # 답은 파이프가 아니라 파일로 받는다 — 파이프를 안 비운 채 기다리면 큰 답에서 멈춘다.
    try:
        with stdin_file as stdin, open(raw_path, 'wb') as raw, open(err_path, 'wb') as err:
            try:
                proc = subprocess.Popen(cmd_head + argv(a.model, a.resume, a.write, review, system_path, settings_path),
                                        cwd=a.cwd, env=env, stdin=stdin, stdout=raw, stderr=err, creationflags=CREATE_NO_WINDOW)
            except OSError as e:
                return 'spawn', None, '', None, str(e), 'in=- out=-', '-', {}, raw_path, norms_n
            while proc.poll() is None:
                if time.monotonic() > started + a.timeout:
                    kill_tree(proc)
                    status = 'timeout'
                    break
                time.sleep(POLL_SEC)
    finally:
        for path in (settings_path, system_path):
            try:
                if path:
                    os.remove(path)
            except OSError:
                pass
    with open(err_path, encoding='utf-8', errors='replace') as f:
        err_text = f.read()
    judged, answer, conv, reason, tokens, model, tools = judge(read_jsonl(raw_path), proc.returncode, err_text, review)
    if status is None:
        status = judged
    if status == 'ok':
        for p in (raw_path, err_path):
            try:
                os.remove(p)
            except OSError:
                pass
    else:
        reason = '\n'.join(s for s in (reason, err_text[-STDERR_TAIL_CHARS:].strip()) if s)
    return status, proc.returncode, answer, conv, reason, tokens, model, tools, raw_path, norms_n


class HelpFormat(argparse.RawDescriptionHelpFormatter):
    """`--help` 의 꼴 — 폭만 넓혀 플래그마다 한 줄에 둔다(아래쪽 절은 `help_epilog` 가 짠 그대로 간다)."""

    def __init__(self, prog):
        super().__init__(prog, max_help_position=26, width=140)


def build_parser():
    ap = Parser(add_help=False, formatter_class=HelpFormat,
                description='Claude 에게 일을 맡기고, 답과 끝 줄을 --out 파일로 받는다. 기본은 읽기만 한다.')
    ap.add_argument('-h', '--help', action='store_true', help='이 도움말을 표준 출력에 찍고 끝낸다(파일은 안 쓴다)')
    ap.add_argument('--prompt-file', required=True, metavar='FILE', help='맡길 프롬프트 파일 — 받는 인코딩은 아래 「프롬프트 파일」')
    ap.add_argument('--out', required=True, metavar='FILE', help='답 파일 — 어느 갈래로 끝나든 답과 끝 줄을 여기 쓴다')
    ap.add_argument('--cwd', required=True, metavar='DIR', help='받는 Claude 를 띄울 작업 자리 — 없는 폴더면 안 띄운다. --write 가 고치는 범위이기도 하다')
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SEC, metavar='SEC', help=f'시간 한도(초). 기본 {DEFAULT_TIMEOUT_SEC}')
    ap.add_argument('--model', metavar='NAME', help='받는 Claude 의 모델. 안 주면 사용자 설정의 모델로 뜬다')
    ap.add_argument('--resume', metavar='ID', help='이어 묻기 — 끝 줄 resume= 의 값을 그대로')
    ap.add_argument('--write', action='store_true', help='고치기 레인 — 작업 자리 안만 고친다(아래 「모드」)')
    ap.add_argument('--review', nargs='?', const='', metavar='TARGET',
                    help='리뷰 모드 — 값은 리뷰 대상(<pr#> · <가지> · <경로> 하나), 없으면 지금의 diff')
    ap.add_argument('--max-findings', metavar='N|all', help='리뷰 모드에서 그 스킬에 넘기는 한도 — 수나 all')
    return ap


def exit_table():
    """종료 코드 표의 줄들 — `EXIT` 에서 같은 코드를 쓰는 이름끼리 묶고 `STATUS_WORDS` 로 뜻을 단다. 이름은 끝 줄의 갈래다."""
    names = {}
    for name, code in EXIT.items():
        names.setdefault(code, []).append(name)
    joined = {code: ' · '.join(ns) for code, ns in names.items()}
    width = max(len(j) for j in joined.values())
    return [f'  {code}  {joined[code]:<{width}}  ' + ' · '.join(STATUS_WORDS.get(n, n) for n in names[code])
            for code in sorted(names)]


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
        *exit_table(),
    ]) + '\n'


def show_help(ap):
    """`--help` — 도움말을 표준 출력에 찍고 0. 인자 검사보다 앞서고 파일은 안 쓴다."""
    ap.epilog = help_epilog()
    out = sys.stdout
    if out is None:   # pythonw 에는 표준 출력이 없다 — 찍을 곳이 없다
        return EXIT['ok']
    if hasattr(out, 'reconfigure'):   # 윈도 파이프의 기본 인코딩(cp949)은 `—` 를 못 적어 죽는다 — 에이전트 셸은 UTF-8 로 읽는다
        out.reconfigure(encoding='utf-8')
    out.write(ap.format_help())
    return EXIT['ok']


def main():
    ap = build_parser()
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        return show_help(ap)
    try:
        a = ap.parse_args(args)
    except Usage as e:
        out = out_arg(args)
        if out:
            try:
                write(out, f'{FOOTER} usage · 인자가 틀렸다 — {e}\n')
            except OSError:
                pass
        return EXIT['usage']
    try:
        return run(a)
    except Exception as e:   # 어디서 멈췄든 답 파일과 끝 줄을 남긴다 — 부른 쪽은 그것만 본다
        write(a.out, f'{traceback.format_exc()}\n{FOOTER} failed · 러너가 멈췄다 — {type(e).__name__}: {e}\n')
        return EXIT['failed']


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
    if not os.path.isfile(a.prompt_file):
        write(a.out, f'{FOOTER} usage · 프롬프트 파일이 없다 — {a.prompt_file}\n')
        return EXIT['usage']
    bad = prompt_problem(a.prompt_file)
    if bad:
        write(a.out, f'{FOOTER} usage · {bad}\n')
        return EXIT['usage']
    if not (a.cwd and os.path.isdir(a.cwd)):
        write(a.out, f'{FOOTER} usage · --cwd 가 폴더가 아니다 — {a.cwd}\n')
        return EXIT['usage']
    if a.model and not MODEL_NAME_RE.fullmatch(a.model):
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
    footer = footer_line(status, cells)
    if status == 'ok':
        write(a.out, f'{answer.rstrip()}\n\n{footer}\n')
    else:
        # 날 출력은 길어(이벤트 수십 줄) 옮기지 않는다 — 까닭과 그 자리만 적는다
        write(a.out, f'{answer.rstrip()}\n{reason}\n{footer}\n')
    return EXIT[status]


if __name__ == '__main__':
    sys.exit(main())
