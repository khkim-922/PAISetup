"""Codex 에게 일을 맡기고, Codex 가 한도면 자리 값이 허락할 때 Copilot 이 받는다 — 맡기는 쪽(Claude · agy)이 백그라운드
Bash 에서 `pythonw` 로 부른다.

    pythonw codex_copilot_bg.py --prompt-file <파일> --out <답 파일> --cwd <작업 자리> [--write | --review [대상]]
                                [--agent codex|copilot] [--resume <쪽>:<id>] [--model <이름>] [--timeout <초>]

내는 것 — 답과 맨 끝 줄 `[cc-bg] …` 을 `--out` 파일에 쓴다(어느 갈래로 끝나든). 모드 셋 · 차례 · 자리 값(`CC_BG_*`) · 끝 줄의
칸 · 종료 코드는 `--help` 가 든다(표준 출력에 찍는 것은 그것뿐이다).
레인마다 무엇으로 가두나 · 넘기는 까닭 · 자리 값이 오는 길은 `references/DESIGN.md` 가 든다.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AGENTS = ('codex', 'copilot')   # 차례 — 1번 · 2번
EXIT = {'ok': 0, 'failed': 1, 'quota': 2, 'empty': 2, 'timeout': 3, 'usage': 4}
FOOTER = '[cc-bg]'
# 갈래 낱말의 뜻 — `--help` 의 종료 코드 표가 `EXIT` 의 이름마다 단다. 갈래 낱말은 끝 줄의 첫 낱말이기도 하다
STATUS_WORDS = {'ok': '답이 왔다', 'failed': '실패했다(러너가 멈춘 것 포함)', 'quota': '한도(받을 쪽까지 다)', 'empty': '빈 답',
                'timeout': '시간 초과',
                'usage': '부르는 법이 틀렸다(인자 · 자리 값 · 프롬프트 파일의 인코딩) 또는 띄울 쪽이 없다(안 깔렸거나 이 자리에서 안 쓴다)'}
# 끝 줄의 칸 — (이름, 뜻). 끝 줄을 짓는 `footer_line` 과 `--help` 가 같이 읽고, 차례가 끝 줄의 차례다
FOOTER_FIELDS = (
    ('note', 'Copilot 이 쓰는 gh 로그인이 무효라 졌을 때만 — 그 말과 되살리는 명령(`gh auth login`)이 갈래 바로 뒤에 선다'),
    ('rc', '받은 쪽 CLI 의 종료 코드'),
    ('elapsed', '걸린 시간 — `<N>s` 꼴(초)'),
    ('mode', '레인 — read(읽기만) · write(--write) · review(--review)'),
    ('agent', '답한(마지막에 띄운) 쪽 — codex · copilot'),
    ('model', 'Codex 에 넘긴 모델 이름. 안 넘겼거나 Copilot 이면 `-`'),
    ('caller', '부른 쪽이 Copilot 이면 `copilot` — 그 쪽은 차례에서 빠져 있다(Copilot 이 부른 일을 Copilot 으로 되돌리지 않는다)'),
    ('failover', 'Codex 한도로 다음 쪽에 넘어온 자취 `<쪽>: <갈래>`(`;` 로 여럿) — 있을 때만'),
    ('tokens', '`tokens in=<N> out=<N>` — Copilot 은 `in=- out=-`'),
    ('web', 'Codex 가 실제로 마친 웹 검색 수 — 0 이면 기억으로 낸 답이다. Copilot 은 `-`'),
    ('resume', '이어 묻기 값 `<쪽>:<id>` — 그쪽 대화 기록이 실제로 남았을 때만. 아니면 `-` 와 까닭'),
    ('raw', '날 출력(jsonl) 파일 경로 — 답이 안 온 갈래에서만'),
)

# 셔틀(`.cmd`)이 부르는 JS — npm 전역 자리(셔틀 곁의 `node_modules`) 기준
NPM_ENTRY = {'codex': ('@openai', 'codex', 'bin', 'codex.js'),
             'copilot': ('@github', 'copilot', 'npm-loader.js')}

# Codex 의 한도 문구 — openai/codex `codex-rs/protocol/src/error.rs` 의 것이다. 「You’ve」의 아포스트로피가 판마다
# U+2019 · ASCII 로 갈려 그 뒤부터 문다. 마지막 둘은 API 키 방식 · 일반 429 를 재시도하다 다 쓴 꼴이다.
CODEX_QUOTA_RE = re.compile(r'hit your usage limit|Quota exceeded\. Check your plan|Selected model is at capacity|'
                            r'exceeded retry limit, last status: 429|rate limit exceeded')
# 앱 · 플러그인 · MCP 를 끄고 승인을 `never` 로 박는다 — 샌드박스가 두 레인의 유일한 울타리여야 한다(까닭은 references/DESIGN.md
# 「Codex 를 띄우는 고정 인자」)
CODEX_ARGS = ['-c', 'approval_policy="never"', '-c', 'features.apps=false', '-c', 'features.plugins=false',
              '-c', 'mcp_servers={}', '--skip-git-repo-check', '--json']
CODEX_SANDBOX = {False: 'read-only', True: 'workspace-write'}   # 읽기 레인 · 고치기 레인
# 고치기 레인의 쓰는 범위 — 작업 자리와 임시 폴더 변수 하나(러너가 세운 빈 폴더로 돌린다). 그 변수를 아예 닫으면 셸 도구의
# 검사 · 빌드가 진다
WRITE_SANDBOX = ['-c', 'sandbox_workspace_write.writable_roots=[]',
                 '-c', 'sandbox_workspace_write.exclude_tmpdir_env_var=false',
                 '-c', 'sandbox_workspace_write.exclude_slash_tmp=true']
# 임시 폴더 변수 — Codex 는 윈도에서 `TEMP` · `TMP`, 그 밖에서 `TMPDIR` 을 읽고 Copilot 의 「시스템 임시 폴더」도 이 변수를
# 따른다. 고치기 레인이면 셋 다 같은 새 폴더로 돌린다
TEMP_VARS = ('TEMP', 'TMP', 'TMPDIR')
WRITE_TMP_PREFIX = 'cc-bg-write-'
# 이어 묻기가 서는 대화 기록의 자리 — (홈 변수 · 그 변수가 없을 때의 홈 · 홈 아래 폴더 · 파일 이름 꼴). Codex 는
# `sessions/<년>/<월>/<일>/rollout-<시각>-<id>.jsonl`, Copilot 은 `session-state/<id>/`
STORE = {'codex': ('CODEX_HOME', '.codex', ('sessions', '*', '*', '*'), 'rollout-*-{id}.jsonl'),
         'copilot': ('COPILOT_HOME', '.copilot', ('session-state',), '{id}')}
NO_RESUME = ('이어 묻기 못 함 — 대화 기록이 안 남았다({where} 에 이 대화가 없다). 받는 쪽이 제 홈에 못 쓰는 자리'
             '(부른 쪽의 샌드박스)에서 돌았거나 대화가 서기 전에 멈췄다')

# 자리 값의 이름과 받는 값 — 받는 값은 Codex 설정의 낱말 그대로다(`web_search` · `windows.sandbox`).
KNOB_AGENTS = 'CC_BG_AGENTS'
KNOB_WEB_SEARCH = 'CC_BG_CODEX_WEB_SEARCH'
KNOB_WIN_SANDBOX = 'CC_BG_CODEX_WIN_SANDBOX'
KNOB_MODEL = 'CC_BG_CODEX_MODEL'
KNOB_MODEL_DELEGATE = 'CC_BG_CODEX_MODEL_DELEGATE'
WEB_SEARCH_MODES = ('disabled', 'cached', 'indexed', 'live')
WIN_SANDBOX_MODES = ('elevated', 'unelevated', 'mxc')
DEFAULT_WEB_SEARCH = 'live'                       # 값이 없으면 실시간 검색
MODEL_NAME_RE = re.compile(r'[A-Za-z0-9._:/-]+')  # TOML 따옴표 안에 그대로 들어간다 — 따옴표 · 공백을 막는다

# 이 러너를 Copilot 세션이 불렀다는 표 — Copilot 의 셸 도구가 세션 안에서 도는 명령에만 심는 환경변수다. 같은 때 심기는 CLI
# 설치 · 판 이름(`COPILOT_CLI*`)도 있으나 그것은 세션 없이 CLI 만 깔려도 서는 이름이라 「Copilot 이 부른 중」을 못 가른다.
# 러너가 시작할 때 제 환경에서만 읽는다 — 받는 쪽에 넘기는 환경(`run_once` 의 `env`)과 섞지 않는다
COPILOT_CALLER_ENV = 'COPILOT_AGENT_SESSION_ID'
CALLER_COPILOT_SAY = '부른 쪽이 Copilot 세션이다 — Copilot 이 부른 일은 Copilot 으로 되돌려 맡기지 않는다(차례는 codex 만)'

# Copilot 이 한도로 멈춘 꼴 — `session.error` 의 `errorType`(quota · 402 / rate_limit · 429). 종료 코드는 0 으로
# 끝난 기록도 있어 그것보다 이 이벤트를 먼저 본다.
COPILOT_QUOTA_TYPES = ('quota', 'rate_limit')
COPILOT_TOOLS = ('view', 'web_fetch', 'glob', 'rg')   # 읽기 · 웹 읽기만 — 셸 · 쓰기는 모델이 아예 못 본다
# 고치기 레인에 더 보이는 편집 도구 — Copilot 이 「edit」 갈래로 묶는 넷(모델 계열마다 받는 것이 다르다). 셸은 안 보인다 —
# OS 샌드박스 없이 사용자 권한으로 돌아 경로 검사를 울타리로 못 믿는다
COPILOT_EDIT_TOOLS = ('apply_patch', 'create', 'edit', 'str_replace_editor')
COPILOT_ARGS = ['--allow-tool=web_fetch', '--allow-all-urls', '--no-ask-user', '--output-format', 'json']
# 고치기 레인의 울타리 — 쓰기는 묻지 않고 허락하되 경로 검사의 허락 자리에서 시스템 임시 폴더를 뺀다. 경로 검사를 끄는 깃발
# (`--allow-all-paths` · `--allow-all` · `--yolo`)과 `--add-dir` 은 싣지 않는다
COPILOT_WRITE = ['--allow-tool=write', '--disallow-temp-dir']
# 리뷰 모드(`--review`)의 대상 — 값 꼴과 리뷰어에게 줄 한 줄. 문장은 `codex exec review` 의 세 대상과 같은 뜻이다.
REVIEW_TARGET_RE = re.compile(r'uncommitted|(base|commit):([A-Za-z0-9._/@^~-]+)')
REVIEW_TARGETS = {'uncommitted': 'Review the uncommitted changes: staged, unstaged and untracked.',
                  'base': 'Review the changes this branch would merge into `{ref}` (diff against `git merge-base HEAD {ref}`).',
                  'commit': 'Review the changes introduced by commit `{ref}`.'}
DEFAULT_REVIEW_TARGET = 'uncommitted'
REVIEW_SKILL = '$review-agent '   # Codex 의 리뷰 스킬을 이름으로 부르는 머리
REVIEW_AGENT = 'codex'            # 리뷰 모드를 받는 쪽 — Copilot 은 안 받는다(references/DESIGN.md)
# 저장된 로그인보다 앞서는 토큰 — Copilot 권한이 없는 토큰이면 인증부터 깨진다. `COPILOT_GITHUB_TOKEN` 은 Copilot 에
# 쓰라고 둔 것이라 남긴다.
COPILOT_DROP_ENV = ('GH_TOKEN', 'GITHUB_TOKEN')
# Copilot 이 gh 로그인의 토큰으로 인증하다 진 꼴(GitHub 의 401) — 보관본 references/copilot-gh-login-401.stderr.txt 그대로다.
# 뒤는 판마다 갈려 앞머리를 문다
COPILOT_GH_LOGIN_DEAD = 'Failed to fetch GitHub CLI user login (401)'
# gh 가 키링의 로그인보다 먼저 쓰는 환경변수 토큰 — 이것이 선 셸에서는 `gh auth login` 이 로그인을 안 받는다.
GH_ENV_TOKENS = ('GH_TOKEN', 'GITHUB_TOKEN')
GH_LOGIN_DEAD_SAY = ('Copilot 이 쓰는 gh 로그인이 무효가 됐다(대개 다른 기기에서 같은 범위로 gh 에 로그인한 탓이다) — '
                     '터미널에서 `gh auth login` 한 번이면 되살아난다')
GH_LOGIN_ENV_SAY = '(환경변수 토큰 {names} 이 선 셸에서는 gh 가 로그인을 안 받는다 — 그 변수를 비운 셸에서 친다)'


# 러너 셋이 함께 쓰는 손은 곁에 깔린 스킬 agent-envelope 의 `runner_common.py` 가 든다. 러너는 창 없이 돌아 말할 곳이 답 파일
# 뿐이라, 그 부품을 못 실으면 여기서 답 파일에 끝 줄을 남기고 끝낸다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'agent-envelope' / 'scripts'))
try:
    import runner_common as common
    from runner_common import (CREATE_NO_WINDOW, DEFAULT_TIMEOUT_SEC, POLL_SEC, PROMPT_ENCODINGS, SHIM_EXT, STDERR_TAIL_CHARS,
                               HelpFormat, Parser, decode_prompt, kill_tree, read_jsonl, write)
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

def prompt_problem(path):
    """프롬프트 파일을 못 넘기는 까닭 — 없으면 None. 받는 쪽은 표준 입력을 UTF-8 로 읽는다: PowerShell 5.1 의
    `Set-Content` 기본값(ANSI)으로 쓴 파일은 글자가 깨진 채 넘어가 답이 조용히 틀어진다. 그래서 `decode_prompt` 가 받는
    인코딩만 넘기고, 넘길 때(`stdin_for`)는 UTF-8 로 옮긴다."""
    try:
        with open(path, 'rb') as f:
            decode_prompt(f.read())
    except OSError as e:
        return f'프롬프트 파일을 못 읽었다 — {e}'
    except UnicodeDecodeError:
        return (f'프롬프트 파일이 받는 인코딩이 아니다 — {PROMPT_ENCODINGS} 만 받는다. '
                f'PowerShell 5.1 이면 `Set-Content -Encoding utf8` 로 쓴다: {path}')
    return None


def resume_field(agent, conv):
    """끝 줄의 이어 묻기 칸 — 그쪽 대화 기록이 있을 때만 `<쪽>:<id>` 를 싣는다. 없으면 `-` 와 까닭."""
    if not conv:
        return 'resume=-'
    var, default, sub, name = STORE[agent]
    home = os.environ.get(var) or os.path.join(os.path.expanduser('~'), default)
    if glob.glob(os.path.join(glob.escape(home), *sub, name.format(id=glob.escape(conv)))):
        return f'resume={agent}:{conv}'
    return 'resume=- · ' + NO_RESUME.format(where=os.path.join(home, sub[0]))


def gh_login_dead_say(agent, status, reason, env):
    """끝 줄에 실을 「gh 로그인이 무효다」 말 — 해당이 없으면 빈 글. Copilot 이 실패로 끝났고 그 까닭(오류 이벤트 · stderr)에
    `COPILOT_GH_LOGIN_DEAD` 가 들 때만이다 — 답 본문은 안 본다(그 문구를 인용한 답이 성공으로 올 수 있다). `env` 에
    `GH_ENV_TOKENS` 가 서 있으면 그 이름을 대고 그 셸에서는 로그인이 안 선다고 덧붙인다 — 값은 안 싣는다."""
    if agent != 'copilot' or status != 'failed' or COPILOT_GH_LOGIN_DEAD not in reason:
        return ''
    names = [k for k in GH_ENV_TOKENS if env.get(k)]
    return GH_LOGIN_DEAD_SAY + (GH_LOGIN_ENV_SAY.format(names='·'.join(names)) if names else '')


def head(agent):
    """띄울 머리 — 셔틀이면 그것이 부르는 JS 를 node 로. 못 찾으면 None."""
    found = shutil.which(agent)
    if not found:
        return None
    if not found.lower().endswith(SHIM_EXT):
        return [found]
    entry = os.path.join(os.path.dirname(found), 'node_modules', *NPM_ENTRY[agent])
    node = shutil.which('node')
    return [node, entry] if node and os.path.isfile(entry) else None


def read_knobs(env):
    """자리 값을 읽는다 — (값들, 틀린 까닭). 틀린 값이면 값들은 None 이다."""
    raw = env.get(KNOB_AGENTS, '').strip()
    agents = [x.strip() for x in raw.split(',')] if raw else list(AGENTS)
    if not all(agents) or any(x not in AGENTS for x in agents) or len(set(agents)) != len(agents):
        return None, f'{KNOB_AGENTS}={raw!r} — {" · ".join(AGENTS)} 가운데서 쉼표로 겹치지 않게'
    web = env.get(KNOB_WEB_SEARCH, '').strip() or DEFAULT_WEB_SEARCH
    if web not in WEB_SEARCH_MODES:
        return None, f'{KNOB_WEB_SEARCH}={web!r} — {" · ".join(WEB_SEARCH_MODES)} 가운데 하나'
    sandbox = env.get(KNOB_WIN_SANDBOX, '').strip()
    if sandbox and sandbox not in WIN_SANDBOX_MODES:
        return None, f'{KNOB_WIN_SANDBOX}={sandbox!r} — {" · ".join(WIN_SANDBOX_MODES)} 가운데 하나'
    models = {}
    for key, knob in (('model', KNOB_MODEL), ('model_delegate', KNOB_MODEL_DELEGATE)):
        name = env.get(knob, '').strip()
        if name and not MODEL_NAME_RE.fullmatch(name):
            return None, f'{knob}={name!r} — 모델 이름에 따옴표 · 공백이 든다'
        models[key] = name
    return {'agents': agents, 'web_search': web, 'win_sandbox': sandbox, **models}, None


def codex_model(knobs, given=''):
    """Codex 에 줄 모델 — 준 것(`--model`) · 맡기기 모델 · 기본 모델 가운데 처음 선 것. 다 없으면 빈 글(안 넘긴다)."""
    return given or knobs['model_delegate'] or knobs['model']


def codex_config(knobs, model=''):
    """자리 값을 Codex 설정 덮어쓰기(`-c`)로 — 이어 묻기에도 같이 건다. `model` 은 `--model` 로 받은 이름이다."""
    out = ['-c', f'web_search="{knobs["web_search"]}"']
    if knobs['win_sandbox']:
        out += ['-c', f'windows.sandbox="{knobs["win_sandbox"]}"']
    chosen = codex_model(knobs, model)
    if chosen:
        out += ['-c', f'model="{chosen}"']
    return out


def argv(agent, resume, knobs, write=False, model=''):
    """머리 뒤에 붙일 인자 — 프롬프트는 안 싣는다(표준 입력). 이어 물을 때도 고치기 레인이면 `--write` 를 다시 준다.
    `model` 은 `--model` 로 받은 이름이고 Codex 에만 간다. 리뷰 모드도 이 인자 그대로다 — 리뷰는 프롬프트 머리
    (`review_head`)가 부른다."""
    if agent == 'codex':
        tail = ['-c', f'sandbox_mode="{CODEX_SANDBOX[write]}"', *(WRITE_SANDBOX if write else []), *CODEX_ARGS,
                *codex_config(knobs, model)]
        if resume:
            return ['exec', 'resume', *tail, resume, '-']
        return ['exec', *tail, '-']
    tools = COPILOT_TOOLS + (COPILOT_EDIT_TOOLS if write else ())
    return (['--available-tools', *tools, *COPILOT_ARGS, *(COPILOT_WRITE if write else [])]
            + ([f'--resume={resume}'] if resume else []))


def review_head(target):
    """리뷰 모드에서 프롬프트 앞에 얹을 글 — 리뷰 스킬 부르기 + 대상 한 줄. `target` 은 `REVIEW_TARGET_RE` 를 통과한 값이다."""
    kind, _, ref = target.partition(':')
    return f'{REVIEW_SKILL}{REVIEW_TARGETS[kind].format(ref=ref)}\n\n'


def stdin_for(a):
    """표준 입력으로 넘길 파일 — 프롬프트를 UTF-8(BOM 없이)로 옮긴 임시 파일이고 닫으면 지워진다. 리뷰 모드면 앞에 머리를
    얹는다. BOM 은 걷는다(`decode_prompt`) — 머리 뒤에 남으면 본문 첫 글자가 된다."""
    with open(a.prompt_file, 'rb') as f:
        body = decode_prompt(f.read())
    tmp = tempfile.TemporaryFile()
    tmp.write(((review_head(a.review) if a.review else '') + body).encode('utf-8'))
    tmp.seek(0)
    return tmp


def judge_codex(events, rc, err_text):
    """(갈래, 답, 이어 묻기 id, 까닭, 토큰, 웹 검색 수). 답은 마지막 agent_message 다 — 앞의 것은 중간 말이다."""
    answer, conv, failed, last_error, usage, searches = '', None, None, '', {}, 0
    for e in events:
        t = e.get('type')
        item = e.get('item') or {}
        if t == 'thread.started':
            conv = e.get('thread_id')
        elif t == 'item.completed' and item.get('type') == 'agent_message':
            answer = item.get('text') or ''
        elif t == 'item.completed' and item.get('type') == 'web_search':
            searches += 1   # 마친 것만 센다 — 같은 검색이 item.started 로 한 번 더 온다
        elif t == 'turn.failed':
            failed = (e.get('error') or {}).get('message') or ''
        elif t == 'error':
            # 다시 시도하는 중에도 찍힌다 — 그래서 이것만으로 실패를 판정하지 않는다
            last_error = e.get('message') or ''
        elif t == 'turn.completed':
            usage = e.get('usage') or {}
    reason = failed if failed is not None else last_error
    tokens = f'in={usage.get("input_tokens", "-")} out={usage.get("output_tokens", "-")}'
    if failed is not None or rc != 0:
        status = 'quota' if CODEX_QUOTA_RE.search(f'{reason}\n{err_text}') else 'failed'
    elif not answer.strip():
        status = 'empty'
    else:
        status = 'ok'
    return status, answer, conv, reason, tokens, searches


def judge_copilot(events, rc, err_text):
    """(갈래, 답, 이어 묻기 id, 까닭, 토큰, 웹 검색 수 — 안 센다). 답은 내용이 든 마지막 assistant.message 다."""
    answer, conv, error = '', None, None
    for e in events:
        t = e.get('type')
        d = e.get('data') or {}
        if t == 'assistant.message' and d.get('content'):
            answer = d['content']
        elif t == 'session.error':
            error = d
        elif t == 'result':
            conv = e.get('sessionId')
    reason = (error or {}).get('message') or ''
    if error is not None and error.get('errorType') in COPILOT_QUOTA_TYPES:
        status = 'quota'
    elif error is not None or rc != 0:
        status = 'failed'
    elif not answer.strip():
        status = 'empty'
    else:
        status = 'ok'
    return status, answer, conv, reason, 'in=- out=-', None


JUDGE = {'codex': judge_codex, 'copilot': judge_copilot}


def run_once(agent, cmd_head, a, resume):
    """한 쪽을 한 번 띄워 끝까지 지켜본다. 돌려주는 것 — (갈래, 종료 코드, 답, id, 까닭, 토큰, 웹 검색 수, 날 출력 경로)."""
    # stderr 를 .md 로 둔다 — 회사 PC 의 Fasoo 가 .txt 를 감싸 러너가 제 꼬리를 못 읽는다(.md · .json 은 평문으로 남는다)
    raw_path, err_path = f'{a.out}.{agent}.jsonl', f'{a.out}.{agent}.stderr.md'
    env = dict(os.environ)
    if agent == 'copilot':
        for k in COPILOT_DROP_ENV:
            env.pop(k, None)
    # 고치기 레인은 임시 폴더를 이 실행만의 빈 폴더로 돌린다 — Codex 샌드박스가 여는 임시 폴더가 그것뿐이게
    # (`WRITE_SANDBOX`), Copilot 은 제 임시 파일이 거기 남아 함께 지워지게(그 모델은 거기도 못 쓴다 — `COPILOT_WRITE`)
    tmp = tempfile.mkdtemp(prefix=WRITE_TMP_PREFIX) if a.write else None
    if tmp:
        env.update({k: tmp for k in TEMP_VARS})
    started = time.monotonic()
    status = None
    try:
        # 답은 파이프가 아니라 파일로 받는다 — 파이프를 안 비운 채 기다리면 큰 답에서 멈춘다.
        with stdin_for(a) as stdin, open(raw_path, 'wb') as raw, open(err_path, 'wb') as err:
            try:
                proc = subprocess.Popen(cmd_head + argv(agent, resume, a.knobs, a.write, a.model), cwd=a.cwd, env=env,
                                        stdin=stdin, stdout=raw, stderr=err, creationflags=CREATE_NO_WINDOW)
            except OSError as e:
                return 'spawn', None, '', None, str(e), 'in=- out=-', None, raw_path
            while proc.poll() is None:
                if time.monotonic() > started + a.timeout:
                    kill_tree(proc)
                    status = 'timeout'
                    break
                time.sleep(POLL_SEC)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    with open(err_path, encoding='utf-8', errors='replace') as f:
        err_text = f.read()
    judged, answer, conv, reason, tokens, searches = JUDGE[agent](read_jsonl(raw_path), proc.returncode, err_text)
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
    return status, proc.returncode, answer, conv, reason, tokens, searches, raw_path


def build_parser():
    ap = Parser(add_help=False, formatter_class=HelpFormat,
                description='Codex 에게 일을 맡기고(한도가 차면 자리 값이 허락할 때 Copilot 이 받는다), 답과 끝 줄을 --out 파일로 받는다.')
    ap.add_argument('-h', '--help', action='store_true', help='이 도움말을 표준 출력에 찍고 끝낸다(파일은 안 쓴다)')
    ap.add_argument('--prompt-file', required=True, metavar='FILE', help='맡길 프롬프트 파일 — 받는 인코딩은 아래 「프롬프트 파일」')
    ap.add_argument('--out', required=True, metavar='FILE', help='답 파일 — 어느 갈래로 끝나든 답과 끝 줄을 여기 쓴다')
    ap.add_argument('--cwd', required=True, metavar='DIR', help='띄울 작업 자리 — 없는 폴더면 안 띄운다. --write 가 고치는 범위이기도 하다')
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SEC, metavar='SEC',
                    help=f'한 쪽을 한 번 띄우는 시간 한도(초). 기본 {DEFAULT_TIMEOUT_SEC}')
    ap.add_argument('--agent', choices=AGENTS, help='처음부터 이 쪽에 맡긴다(안 주면 차례대로). 차례에 없는 쪽은 안 띄운다')
    ap.add_argument('--resume', metavar='AGENT:ID', help='이어 묻기 — 끝 줄 resume= 의 값을 그대로(<쪽>:<id>)')
    ap.add_argument('--write', action='store_true', help='고치기 레인 — 작업 자리 안만 고친다(아래 「모드」)')
    ap.add_argument('--model', default='', metavar='NAME',
                    help='이 실행의 Codex 모델 — 빈 값은 안 준 것(자리 값이 고른다). Copilot 에는 안 간다')
    ap.add_argument('--review', nargs='?', const=DEFAULT_REVIEW_TARGET, metavar='TARGET',
                    help=f'리뷰 모드 — 대상은 {DEFAULT_REVIEW_TARGET}(기본) · base:<가지> · commit:<sha>')   # 대상은 `REVIEW_TARGET_RE`
    return ap


def help_epilog():
    """`--help` 의 아래쪽 — 모드 · 차례 · 자리 값 · 끝 줄 · 이어 묻기 · 프롬프트 파일 · 종료 코드. 끝 줄 칸은 `FOOTER_FIELDS` 에서,
    종료 코드는 `EXIT` 에서 짓는다."""
    return '\n'.join([
        '모드(끝 줄 mode= 에 적힌다):',
        '  read(기본)       읽기만 한다. Codex 는 읽기 전용 샌드박스에 앱 · 플러그인 · MCP 를 끄고 승인 never, Copilot 은 읽기 · 웹 읽기 도구만 보인다.',
        '  --write          고치기 레인 — 작업 자리(--cwd) 안만 고친다. Codex 는 쓰기 샌드박스에 임시 폴더를 이 실행만의 빈 폴더로 돌리고,',
        '                   Copilot 은 편집 도구 + 쓰기 허락(셸은 안 보인다). 이어 물을 때도 다시 준다(안 주면 읽기 레인으로 이어진다).',
        f'  --review [대상]  리뷰 — {REVIEW_AGENT} 만 받는다(한도여도 Copilot 으로 안 넘긴다). 읽기 레인 인자 그대로 리뷰 스킬을 프롬프트 머리로 부른다.',
        f'                   대상은 {DEFAULT_REVIEW_TARGET}(기본) · base:<가지> · commit:<sha>. --write · --resume · --agent copilot 과 같이 못 준다(`usage`).',
        '',
        f'차례: 자리 값 {KNOB_AGENTS} 가 정한다(없으면 {" → ".join(AGENTS)}). 차례에 없는 쪽은 --agent · --resume 으로도 안 띄운다(`usage`).',
        '  Codex 가 한도(사용 한도 · 할당량 · 용량 초과)면 다음 쪽이 받고, 그 밖의 실패 · 시간 초과는 그 자리에서 멈춘다.',
        f'  Copilot 세션이 부른 러너(환경변수 {COPILOT_CALLER_ENV} 가 선 셸)는 차례에서 copilot 이 빠진다 — Codex 한도는 Codex 의 실패로 끝나고,',
        '  --agent copilot · --resume copilot:<id> 는 띄우기 전에 `usage` 다. 끝 줄 caller=copilot 이 그 자국이다.',
        '',
        '자리 값(환경변수 — 설치기가 자리마다 심고, 없으면 기본):',
        f'  {KNOB_AGENTS:<27}차례이자 쓸 수 있는 쪽(쉼표)',
        f'  {KNOB_WEB_SEARCH:<27}Codex web_search — {" · ".join(WEB_SEARCH_MODES)}(기본 {DEFAULT_WEB_SEARCH})',
        f'  {KNOB_WIN_SANDBOX:<27}Codex windows.sandbox — {" · ".join(WIN_SANDBOX_MODES)}(없으면 Codex 설정을 따른다)',
        f'  {KNOB_MODEL_DELEGATE:<27}맡기기 모델(깊은 판단) — --model 이 없으면 이것을 먼저 쓴다',
        f'  {KNOB_MODEL:<27}기본 모델(심부름) — 맡기기 모델이 없을 때 쓴다. 값이 틀리면 그 이름을 대고 `usage` 로 멈춘다',
        '',
        f'끝 줄: 답 파일의 맨 끝 줄이다. `{FOOTER} <갈래>` 뒤에 아래 칸이 " · " 로 이어진다(없는 칸은 빠진다).',
        '  갈래는 아래 종료 코드 표의 이름이다. 인자가 틀렸거나 러너가 멈췄으면 칸 없이 `<갈래> · <까닭>` 만 든다.',
        *[f'  {name:<9}{meaning}' for name, meaning in FOOTER_FIELDS],
        '',
        '이어 묻기: 끝 줄 `resume=<쪽>:<id>` 의 값을 그대로 --resume 으로 준다 — 그 대화가 있는 쪽에서 잇는다. 끝 줄 model= 이 `-` 가 아니면',
        '  그 이름도 --model 로 준다(안 주면 맡기기 모델로 잇는다). 고치기 레인이면 --write 도 다시 준다.',
        '  `resume=-` 는 대화 기록이 안 남았다는 뜻이다 — 새로 맡긴다.',
        '',
        f'프롬프트 파일: {PROMPT_ENCODINGS} 만 받는다. 래퍼가 UTF-8 로 옮겨 표준 입력으로 넘긴다(길이 한도 없음).',
        '  그 밖(PowerShell 5.1 의 Set-Content 기본인 ANSI 따위)은 `usage` 로 끝나고 까닭이 --out 파일에 남는다.',
        '',
        '종료 코드(끝 줄의 갈래 이름과 같다):',
        *common.exit_table(EXIT, STATUS_WORDS),
    ]) + '\n'


def run(a):
    if not os.path.isfile(a.prompt_file):
        write(a.out, f'{FOOTER} usage · 프롬프트 파일이 없다 — {a.prompt_file}\n')
        return EXIT['usage']
    bad = prompt_problem(a.prompt_file)
    if bad:
        write(a.out, f'{FOOTER} usage · {bad}\n')
        return EXIT['usage']
    a.knobs, bad = read_knobs(os.environ)
    if bad:
        write(a.out, f'{FOOTER} usage · 자리 값이 틀렸다 — {bad}\n')
        return EXIT['usage']
    a.model = a.model.strip()
    if a.model and not MODEL_NAME_RE.fullmatch(a.model):
        write(a.out, f'{FOOTER} usage · --model {a.model!r} — 모델 이름에 따옴표 · 공백이 든다\n')
        return EXIT['usage']
    if a.review is not None:
        if not REVIEW_TARGET_RE.fullmatch(a.review):
            write(a.out, f'{FOOTER} usage · --review {a.review!r} — uncommitted · base:<가지> · commit:<sha> 가운데 하나\n')
            return EXIT['usage']
        if a.write or a.resume:
            write(a.out, f'{FOOTER} usage · --review 는 --write · --resume 과 같이 못 준다 — 리뷰는 읽기만 하는 새 대화다\n')
            return EXIT['usage']
        if a.agent not in (None, REVIEW_AGENT):
            write(a.out, f'{FOOTER} usage · --review 는 {REVIEW_AGENT} 만 받는다 — {a.agent} 셸은 읽기로 못 가둔다\n')
            return EXIT['usage']
    allowed = a.knobs['agents']
    caller_copilot = bool(os.environ.get(COPILOT_CALLER_ENV))
    if caller_copilot:
        allowed = [x for x in allowed if x != 'copilot']
    resume = None
    if a.resume:
        agent, _, resume = a.resume.partition(':')
        if agent not in AGENTS or not resume:
            write(a.out, f'{FOOTER} usage · --resume 은 `<쪽>:<id>` 꼴이다 — 쪽은 {" · ".join(AGENTS)}\n')
            return EXIT['usage']
        # 대화가 그쪽에 있다 — 다른 쪽으로 넘기면 앞 맥락이 없다
        order = [agent]
    elif a.review is not None:
        order = [REVIEW_AGENT]   # 한도여도 안 넘긴다 — 받는 쪽이 리뷰 모드를 안 받는다
    else:
        order = [a.agent] if a.agent else allowed
    # 부른 쪽이 Copilot 이면 Copilot 은 손으로 골라도 안 띄운다 — 까닭이 자리 값이 아니라 부른 쪽이라 따로 말한다
    if caller_copilot and ('copilot' in order or not order):
        write(a.out, f'{FOOTER} usage · {CALLER_COPILOT_SAY}\n')
        return EXIT['usage']
    # 자리가 안 쓰는 쪽은 손으로 골라도 안 띄운다 — 그쪽으로 보내지 않는 것이 그 자리의 선이다
    if any(x not in allowed for x in order):
        write(a.out, f'{FOOTER} usage · 이 자리에서 안 쓰는 쪽이다 — {KNOB_AGENTS}={",".join(allowed)}\n')
        return EXIT['usage']
    if not (a.cwd and os.path.isdir(a.cwd)):
        write(a.out, f'{FOOTER} usage · --cwd 가 폴더가 아니다 — {a.cwd}\n')
        return EXIT['usage']

    started = time.monotonic()
    tried = []
    ran = None
    for agent in order:
        cmd_head = head(agent)
        if cmd_head is None:
            tried.append(f'{agent}: 없음')
            continue
        ran = (agent,) + run_once(agent, cmd_head, a, resume)
        status = ran[1]
        if status == 'spawn':
            tried.append(f'{agent}: 못 띄움({ran[5]})')
            ran = None
            continue
        if status != 'quota' or agent == order[-1]:
            break
        tried.append(f'{agent}: {status}')
    elapsed = int(time.monotonic() - started)

    if ran is None:
        write(a.out, f'{FOOTER} usage · 띄울 쪽이 없다 — {"; ".join(tried) or "차례가 비었다"}\n')
        return EXIT['usage']
    agent, status, rc, answer, conv, reason, tokens, searches, raw_path = ran
    model = (codex_model(a.knobs, a.model) or '-') if agent == 'codex' else '-'
    said = gh_login_dead_say(agent, status, reason, os.environ)
    cells = {'rc': f'rc={rc}', 'elapsed': f'{elapsed}s', 'mode': f'mode={"write" if a.write else "review" if a.review else "read"}',
             'agent': f'agent={agent}', 'model': f'model={model}', 'tokens': f'tokens {tokens}',
             'web': f'web={"-" if searches is None else searches}', 'resume': resume_field(agent, conv)}
    if said:
        cells['note'] = said
    if caller_copilot:
        cells['caller'] = 'caller=copilot'
    if tried:
        cells['failover'] = f'failover={"; ".join(tried)}'
    if status != 'ok':
        cells['raw'] = f'raw={raw_path}'
    footer = common.footer_line(FOOTER, FOOTER_FIELDS, status, cells)
    if status == 'ok':
        write(a.out, f'{answer.rstrip()}\n\n{footer}\n')
    else:
        # 날 출력은 길어(이벤트 수백 줄) 옮기지 않는다 — 까닭과 그 자리만 적는다
        write(a.out, f'{answer.rstrip()}\n{reason}\n{footer}\n')
    return EXIT[status]


def main():
    return common.main(build_parser, help_epilog, run, FOOTER, EXIT)


if __name__ == '__main__':
    sys.exit(main())
