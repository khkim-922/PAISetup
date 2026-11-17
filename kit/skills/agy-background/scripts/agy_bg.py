"""agy 에게 일을 맡기고 답을 파일로 받는다 — 맡기는 쪽(Claude · Codex)이 백그라운드 Bash 에서 `pythonw` 로 부른다.

    pythonw agy_bg.py --prompt-file <파일> --out <답 파일> --cwd <작업 자리> [--model <이름>] [--timeout <초>]
                      [--conversation <id>]

내는 것 — 답과 맨 끝 줄 `[agy-bg] …` 을 `--out` 파일에 쓴다(어느 갈래로 끝나든). 끝 줄의 칸 · 종료 코드 · 인자의 뜻은 `--help`
가 든다(표준 출력에 찍는 것은 그것뿐이다). 한도나 과부하면 다음 후보 모델로 다시 띄운다(`candidates`).
왜 `pythonw` 인가 · 로그를 훑는 까닭 · `api:` 후보의 가짜 홈은 `references/DESIGN.md` 가 든다.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

AGY = 'agy'
# 한도 초과의 두 꼴 — 로그인 방식(로그) · API 키 방식(로그의 `Error 429` · stderr 의 `AGY_ERROR` JSON)
QUOTA_RE = re.compile(r'RESOURCE_EXHAUSTED \(code 429\)|"error_code":\s*429|Error 429\b')
# 과부하의 꼴 — API 키 방식 로그의 `Run: attempt N failed (Error 503, … Status: UNAVAILABLE …)`.
# ⚠ 로그인 방식의 503 꼴은 이 식이 모른다 — 그 꼴이 로그에 보이면 여기에 더한다(그 전에는 로그인 방식이 503 에서 안 넘어간다).
OVERLOAD_RE = re.compile(r'Error 503\b')
# 넘어가는 갈래 — 이 둘은 다음 후보로 다시 띄운다. 나머지(실패 · 빈 답 · 시간 초과)는 모델 탓이 아니라 멈춘다.
FAILOVER = ('quota', 'overload')
API_PREFIX = 'api:'                          # 이 머리를 단 후보는 API 키 방식으로 띄운다
API_SETTINGS = {'modelProvider': 'gemini'}   # agy 가 로그인 없이 API 키로 서는 설정 — agy 체인지로그
# agy 제 한도가 차면 종료 코드 0 · status SUCCESS · 빈 답으로 끝나고, 까닭은 stderr 한 줄에만 남는다.
PRINT_TIMEOUT_RE = re.compile(r'\[agy\] print timeout')
KILL_GRACE_SEC = 15         # agy 제 한도(--print-timeout) 뒤에 기다려 주는 여유
LOG_CARRY_CHARS = 200       # 읽기 경계에 걸친 패턴을 놓치지 않게 남기는 꼬리
MAX_PROMPT_CHARS = 30000    # 윈도 명령줄 한도(32,767자) 안에 인자 전체가 들게 남긴다
EXIT = {'ok': 0, 'failed': 1, 'quota': 2, 'overload': 2, 'empty': 2, 'timeout': 3, 'usage': 4}
# 갈래 낱말의 뜻 — `--help` 의 종료 코드 표가 `EXIT` 의 이름마다 단다. 갈래 낱말은 끝 줄의 첫 낱말이기도 하다
STATUS_WORDS = {'ok': '답이 왔다', 'failed': 'agy 가 실패했다(API 홈을 못 지은 것 · 러너가 멈춘 것 포함)', 'quota': '한도 초과',
                'overload': '과부하', 'empty': '빈 답', 'timeout': '시간 초과',
                'usage': '부르는 법이 틀렸다(인자 · 작업 자리 · 프롬프트 파일의 인코딩 · 길이)'}
FOOTER = '[agy-bg]'
# 끝 줄의 칸 — (이름, 뜻). 끝 줄을 짓는 `footer_line` 과 `--help` 가 같이 읽고, 차례가 끝 줄의 차례다
FOOTER_FIELDS = (
    ('rc', 'agy 의 종료 코드. `-` 는 agy 를 못 띄운 것(API 홈을 못 지었다)'),
    ('elapsed', '걸린 시간 — `<N>s` 꼴(초)'),
    ('model', '마지막에 띄운 모델. `api:` 로 시작하면 API 키 방식, `agy 기본` 은 모델을 안 골라 띄운 것'),
    ('failover', '한도나 과부하로 다음 모델로 넘어온 자취 `<모델>: <갈래>`(`;` 로 여럿) — 넘어왔을 때만'),
    ('tokens', '`tokens in=<N> out=<N>` — 입력 · 출력 토큰. `-` 는 못 받은 것'),
    ('conversation', '이어 묻기 id — 그 홈에 대화가 실제로 남았을 때만. 아니면 `-` 와 까닭'),
    ('log', 'agy 의 로그 파일 경로 — 답이 안 온 갈래에서만'),
)
# agy 훅 표 — 「이름 → 설정」이라 `entries` 가 없다. 명령에는 설치기가 훅 파일의 절대 경로를 박아(`agy-hooks.py`
# `command`) 홈을 가리키는 자리가 없어 그대로 옮긴다. 안 옮기면 API 키 방식 agy 는 DRM 길잡이 · BOM 훅 없이 돈다.
HOOKS_FILE = 'hooks.json'
# 우리 스킬이 사는 자리 — 진짜 홈의 agy 기본 전역 스킬 자리. API 홈의 스킬 목록에 절대 경로로 더한다(사본을 안 든다 —
# 까닭은 references/DESIGN.md 「API 홈의 스킬 자리」)
DEFAULT_SKILLS = ('.gemini', 'config', 'skills')
SKILLS_LIST = 'skills.json'
# 대화가 남는 자리 — `<홈>/.gemini/antigravity-cli/conversations/<id>.db`(agy 1.3.3 · 로그인 · API 홈 둘 다)
CONVERSATIONS = ('.gemini', 'antigravity-cli', 'conversations')
CONVERSATION_FILE = '{id}.db'
NO_RESUME = ('이어 묻기 못 함 — 대화가 안 남았다({where} 에 이 대화가 없다). agy 가 제 홈에 못 쓰는 자리(맡긴 쪽의 '
             '샌드박스)에서 돌았거나 대화가 서기 전에 멈췄다')


# 러너 셋이 함께 쓰는 손은 곁에 깔린 스킬 agent-envelope 의 `runner_common.py` 가 든다. 러너는 창 없이 돌아 말할 곳이 답 파일
# 뿐이라, 그 부품을 못 실으면 여기서 답 파일에 끝 줄을 남기고 끝낸다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'agent-envelope' / 'scripts'))
try:
    import runner_common as common
    from runner_common import (CREATE_NO_WINDOW, DEFAULT_TIMEOUT_SEC, POLL_SEC, PROMPT_ENCODINGS, HelpFormat, Parser,
                               decode_prompt, kill_tree, write)
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

def conversation_field(home, conv):
    """끝 줄의 이어 묻기 칸 — 띄운 홈에 대화가 남았을 때만 id 를 싣는다. 없으면 `-` 와 까닭."""
    if not conv:
        return 'conversation=-'
    where = os.path.join(home, *CONVERSATIONS)
    if os.path.isfile(os.path.join(where, CONVERSATION_FILE.format(id=conv))):
        return f'conversation={conv}'
    return 'conversation=- · ' + NO_RESUME.format(where=where)


class LogTail:
    """로그를 읽은 데까지 기억해 새로 붙은 것만 훑는다 — 긴 일의 로그는 수 MB 로 자란다."""

    def __init__(self, path):
        self.path, self.pos, self.carry = path, 0, ''

    def failover_hit(self):
        """새로 붙은 로그에 넘어갈 까닭이 보이면 그 갈래('quota' · 'overload'), 없으면 None."""
        try:
            with open(self.path, encoding='utf-8', errors='replace') as f:
                f.seek(self.pos)
                chunk = f.read()
                self.pos = f.tell()
        except OSError:
            return None
        text = self.carry + chunk
        self.carry = text[-LOG_CARRY_CHARS:]
        return failover_reason(text)


def failover_reason(text):
    """한도가 과부하보다 앞선다 — 둘 다 보이면 한도 쪽이 오래 간다."""
    if QUOTA_RE.search(text):
        return 'quota'
    if OVERLOAD_RE.search(text):
        return 'overload'
    return None


def put(path, text):
    """같으면 안 쓴다 — 띄울 때마다 짓는 파일이라 매번 쓰면 시각만 바뀌고, 쓸 수 없는 자리에서는 그 쓰기에서 진다.
    ⚠ BOM 없는 UTF-8 로 쓴다 — 답 파일(`write`)과 달리 agy 설정 파일이라 JSON 앞의 BOM 이 읽는 쪽을 깨뜨린다."""
    try:
        with open(path, encoding='utf-8') as f:
            if f.read() == text:
                return
    except (OSError, ValueError):
        pass
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def put_settings(path, wanted):
    """방식 설정을 심는다 — 그 값이 이미 서 있으면 안 쓴다. agy 는 이 파일을 제 꼴로 다시 써 두어(들여쓴
    `{"modelProvider": "gemini"}`) 글자로 견주면 띄울 때마다 다시 쓰게 되고, 쓸 수 없는 자리(맡긴 쪽의 샌드박스)에서는 그
    쓰기가 러너를 죽인다. 그래서 값으로 견준다. 우리 것 아닌 키는 둔다."""
    try:
        with open(path, encoding='utf-8') as f:
            current = json.load(f)
    except (OSError, ValueError):
        current = None
    if isinstance(current, dict) and all(current.get(k) == v for k, v in wanted.items()):
        return
    put(path, json.dumps(dict(current if isinstance(current, dict) else {}, **wanted), ensure_ascii=False, indent=2))


def api_key():
    """API 키 방식에 쓸 키 — agy 와 같은 차례다(둘 다 있으면 agy 가 `GOOGLE_API_KEY` 를 쓴다)."""
    return os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY') or ''


def derive_config(path, src_dir, real_home):
    """진짜 agy 설정 파일 하나를 가짜 홈에 쓸 꼴로 — 홈을 가리키는 자리만 진짜 홈의 절대 경로로 바꾼다.
    훅 표(`HOOKS_FILE`)는 그대로 옮긴다. 경로를 안 가리키는 파일(기계마다 갈리는 값)은 `None` — 옮기지 않는다."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except (OSError, ValueError):
        return None
    if os.path.basename(path) == HOOKS_FILE:
        return text
    fwd = real_home.replace('\\', '/')
    if path.endswith('.md'):
        return text.replace('](~/', f']({fwd}/')
    if not path.endswith('.json'):
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    entries = data.get('entries') if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return None
    for e in entries:
        p = e.get('path') if isinstance(e, dict) else None
        if isinstance(p, str) and not os.path.isabs(p):
            p = os.path.join(real_home, p[2:]) if p.startswith('~/') else os.path.join(src_dir, p)
            e['path'] = os.path.normpath(p).replace('\\', '/')
    return json.dumps(data, ensure_ascii=False, indent=2)


def with_default_skills(text, real_home):
    """API 홈의 스킬 목록 글(`text` — 진짜 목록에서 지은 것 · 없으면 None)에 진짜 홈의 기본 스킬 자리를 더한다. 그 자리가
    없으면 목록을 그대로 두고, 이미 들었으면 또 넣지 않는다."""
    skills = os.path.join(real_home, *DEFAULT_SKILLS)
    if not os.path.isdir(skills):
        return text
    data = json.loads(text) if text else {'entries': []}
    want = os.path.normpath(skills).replace('\\', '/')
    paths = [e.get('path') for e in data['entries'] if isinstance(e, dict)]
    if not any(isinstance(p, str) and os.path.normcase(p) == os.path.normcase(want) for p in paths):
        data['entries'].append({'path': want})
    return json.dumps(data, ensure_ascii=False, indent=2)


def api_home_path(real_home):
    base = os.environ.get('LOCALAPPDATA') or os.path.join(real_home, '.cache')
    return os.path.join(base, 'agy-bg', 'api-home')


def api_home(real_home):
    """API 키 방식으로 띄울 홈을 짓는다 — 방식 한 줄과, 진짜 홈의 규범·스킬·룰·훅 설정에서 **매번 다시 지은**
    가리킴 파일들. 스킬 목록에는 진짜 홈의 기본 스킬 자리를 더한다(`with_default_skills` — 우리 스킬이 거기 산다).
    사본을 들고 있지 않으므로 진짜 설정을 고치면 다음 실행에 따라오고, **진짜 설정에서 빠진 파일은
    여기서도 걷는다** — 남기면 로그인 방식에는 없는 규범으로 돌고, 걷힌 훅 파일을 부르는 훅은 도구마다 오류를 낸다.
    걷는 것은 이 함수가 지을 꼴(`derive_config` 가 None 이 아닌 것)뿐이다 — agy 가 제 손으로 둔 파일은 둔다.
    ⚠ 링크(정션)를 안 쓴다 — 파이썬 3.12 전의 `shutil.rmtree` 는 정션을 따라 들어가 진짜 홈을 지운다."""
    home = api_home_path(real_home)
    cli = os.path.join(home, '.gemini', 'antigravity-cli')
    os.makedirs(cli, exist_ok=True)
    put_settings(os.path.join(cli, 'settings.json'), API_SETTINGS)
    src = os.path.join(real_home, '.gemini', 'config')
    dst = os.path.join(home, '.gemini', 'config')
    derived = {}
    if os.path.isdir(src):
        for name in os.listdir(src):
            text = derive_config(os.path.join(src, name), src, real_home)
            if text is not None:
                derived[name] = text
    listed = with_default_skills(derived.get(SKILLS_LIST), real_home)
    if listed is not None:
        derived[SKILLS_LIST] = listed
    if derived:
        os.makedirs(dst, exist_ok=True)
    for name, text in derived.items():
        put(os.path.join(dst, name), text)
    if os.path.isdir(dst):
        for name in os.listdir(dst):
            path = os.path.join(dst, name)
            if name not in derived and derive_config(path, dst, real_home) is not None:
                os.remove(path)
    return home


def candidates(model, has_key):
    """띄울 모델을 차례대로 — 손으로 고른 것이 있으면 그것 하나, 없으면 맡기기 모델 · 기본 모델 뒤에
    넘길 모델들. 맡기기 모델(`AGY_MODEL_DELEGATE`)이 앞에 서는 까닭은 긴 일을 뒤에서 맡기는 것도
    맡기기라서다. 가벼운 일은 부르는 쪽이 `--model` 로 기본 모델을 준다(스킬이 든다).
    키가 없으면 `api:` 후보는 없는 것으로 친다. 아무것도 없으면 `[None]` — `--model` 없이 띄워
    agy 가 고르게 한다."""
    if model:
        return [model]
    out = []
    first = os.environ.get('AGY_MODEL_DELEGATE', '').split(';') + [os.environ.get('AGY_DEFAULT_MODEL', '')]
    for m in first + os.environ.get('AGY_FALLBACK_MODELS', '').split(';'):
        m = m.strip()
        if not m or m in out or (m.startswith(API_PREFIX) and not has_key):
            continue
        out.append(m)
    return out or [None]


def launch(model):
    """후보 하나를 띄울 꼴 — (agy 에 줄 모델 이름, 환경 · None 이면 물려받는다, agy 가 볼 홈). `api:` 후보는 API 홈을
    지어 그 홈을 보게 한다. 못 지으면 OSError 가 그대로 오른다 — 부른 쪽이 그 후보의 실패로 적는다."""
    real_home = os.path.expanduser('~')
    if model and model.startswith(API_PREFIX):
        home = api_home(real_home)
        env = dict(os.environ, USERPROFILE=home, HOME=real_home, GEMINI_API_KEY=api_key())
        return model[len(API_PREFIX):], env, home
    return model, None, real_home


def run_once(a, prompt, model, log, raw_path, err_path, env=None):
    """agy 를 한 번 띄워 끝까지 지켜본다(`model` 은 agy 에 줄 이름 · `env` 는 `launch` 의 것). 돌려주는 것 — (갈래,
    종료 코드, 답 JSON, 날 stdout, stderr). 띄우지도 못했으면 갈래가 'spawn' 이고 stderr 자리에 까닭이 든다."""
    cmd = [AGY, '-p', prompt, '--output-format', 'json', '--dangerously-skip-permissions',
           '--print-timeout', f'{a.timeout}s', '--log-file', log]
    if model:
        cmd += ['--model', model]
    if a.conversation:
        cmd += ['--conversation', a.conversation]
    # 앞 시도의 로그를 걷는다 — 남아 있으면 그 429 · 503 줄을 이번 시도의 것으로 읽는다.
    try:
        os.remove(log)
    except OSError:
        pass

    started = time.monotonic()
    status = None
    # 답은 파이프가 아니라 파일로 받는다 — 파이프를 안 비운 채 기다리면 큰 답에서 agy 가 멈춘다.
    # stderr 는 따로 받는다 — 같은 파일에 섞이면 그 한 줄이 JSON 을 깨뜨린다.
    with open(raw_path, 'wb') as raw, open(err_path, 'wb') as err:
        try:
            proc = subprocess.Popen(cmd, cwd=a.cwd, env=env, stdin=subprocess.DEVNULL, stdout=raw,
                                    stderr=err, creationflags=CREATE_NO_WINDOW)
        except OSError as e:
            return 'spawn', None, {}, '', str(e)
        tail = LogTail(log)
        deadline = started + a.timeout + KILL_GRACE_SEC
        while proc.poll() is None:
            hit = tail.failover_hit()
            if hit:
                kill_tree(proc)
                status = hit
            elif time.monotonic() > deadline:
                kill_tree(proc)
                status = 'timeout'
            else:
                time.sleep(POLL_SEC)

    with open(raw_path, encoding='utf-8', errors='replace') as f:
        raw_text = f.read()
    with open(err_path, encoding='utf-8', errors='replace') as f:
        err_text = f.read()
    try:
        res = json.loads(raw_text)
    except ValueError:
        res = {}
    answer = res.get('response') or ''
    if status is None:
        status = tail.failover_hit() or failover_reason(err_text)
    if status is None:
        if PRINT_TIMEOUT_RE.search(err_text):
            status = 'timeout'
        elif proc.returncode != 0 or res.get('status') != 'SUCCESS':
            status = 'failed'
        elif not answer.strip():
            status = 'empty'
        else:
            status = 'ok'
    return status, proc.returncode, res, raw_text, err_text


def build_parser():
    ap = Parser(add_help=False, formatter_class=HelpFormat,
                description='agy(Antigravity CLI · 제미나이)에게 일을 맡기고, 답과 끝 줄을 --out 파일로 받는다.')
    ap.add_argument('-h', '--help', action='store_true', help='이 도움말을 표준 출력에 찍고 끝낸다(파일은 안 쓴다)')
    ap.add_argument('--prompt-file', required=True, metavar='FILE', help='맡길 프롬프트 파일 — 받는 인코딩은 아래 「프롬프트 파일」')
    ap.add_argument('--out', required=True, metavar='FILE', help='답 파일 — 어느 갈래로 끝나든 답과 끝 줄을 여기 쓴다')
    ap.add_argument('--cwd', required=True, metavar='DIR', help='agy 를 띄울 작업 자리 — 없는 폴더면 안 띄운다')
    ap.add_argument('--model', metavar='NAME', help='이 모델 하나만 쓴다(안 넘어간다). 안 주면 자리 값(AGY_*)의 차례')
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SEC, metavar='SEC',
                    help=f'agy 한 번의 시간 한도(초). 기본 {DEFAULT_TIMEOUT_SEC}')
    ap.add_argument('--conversation', metavar='ID', help='이어 묻기 — 끝 줄 conversation= 의 값을 그대로')
    return ap


def help_epilog():
    """`--help` 의 아래쪽 — 모드 · 끝 줄 · 이어 묻기 · 프롬프트 파일 · 종료 코드. 끝 줄 칸은 `FOOTER_FIELDS` 에서, 종료 코드는
    `EXIT` 에서 짓는다."""
    return '\n'.join([
        '모드: 없다 — agy 는 권한을 묻지 않고 돈다. 쓰기를 프롬프트로는 못 막으니 작업 자리(--cwd)로 막는다.',
        '  조사만 시키면 --cwd 는 스크래치패드로 주고, 저장소를 줬으면 끝난 뒤 `git status --porcelain` 으로 남긴 것을 본다.',
        '',
        f'끝 줄: 답 파일의 맨 끝 줄이다. `{FOOTER} <갈래>` 뒤에 아래 칸이 " · " 로 이어진다(없는 칸은 빠진다).',
        '  갈래는 아래 종료 코드 표의 이름이다. 인자가 틀렸거나 러너가 멈췄으면 칸 없이 `<갈래> · <까닭>` 만 든다.',
        *[f'  {name:<13}{meaning}' for name, meaning in FOOTER_FIELDS],
        '',
        '이어 묻기: 끝 줄 `conversation=<id>` 의 값을 그대로 --conversation 으로 준다. 끝 줄 model= 이 `api:` 로 시작하면',
        '  그 이름도 --model 로 준다(같은 방식으로 잇는다). `conversation=-` 는 대화가 안 남았다는 뜻이다 — 새로 맡긴다.',
        '',
        f'프롬프트 파일: {PROMPT_ENCODINGS} 만 받는다. 래퍼가 UTF-8 로 옮겨 agy 의 명령줄에 싣는다.',
        '  그 밖(PowerShell 5.1 의 Set-Content 기본인 ANSI 따위)은 `usage` 로 끝나고 까닭이 --out 파일에 남는다.',
        f'  프롬프트는 명령줄로 가므로 {MAX_PROMPT_CHARS}자를 넘으면 `usage` 다 — 큰 자료는 경로를 주고 agy 가 읽게 한다.',
        '',
        '종료 코드(끝 줄의 갈래 이름과 같다):',
        *common.exit_table(EXIT, STATUS_WORDS),
        '  한도 초과 · 과부하는 넘어갈 모델까지 다 막혔을 때다.',
    ]) + '\n'


def run(a):
    # 자리는 `--cwd` 가 필수라 늘 오지만, 그 선언이 퇴행하면 `None` 이 여기로 와 멈춘다 — 멈춤은 갈래 1 이고
    # 부르는 쪽은 까닭을 못 읽는다. 관문이 제 갈래(4)로 내게 `None` 도 같이 문다
    if not (a.cwd and os.path.isdir(a.cwd)):
        write(a.out, f'{FOOTER} usage · --cwd 가 폴더가 아니다 — {a.cwd}\n')
        return EXIT['usage']
    try:
        # 글로 읽는다 — 프롬프트는 명령줄로 가니 UTF-8 로 옮기는 일은 파이썬이 한다. BOM 은 걷힌다(`decode_prompt`)
        with open(a.prompt_file, 'rb') as f:
            prompt = decode_prompt(f.read())
    except OSError as e:
        write(a.out, f'{FOOTER} usage · 프롬프트 파일을 못 읽었다 — {e}\n')
        return EXIT['usage']
    except UnicodeDecodeError:
        write(a.out, f'{FOOTER} usage · 프롬프트 파일이 받는 인코딩이 아니다 — {PROMPT_ENCODINGS} 만 받는다. '
                     f'PowerShell 5.1 이면 `Set-Content -Encoding utf8` 로 쓴다: {a.prompt_file}\n')
        return EXIT['usage']
    if len(prompt) > MAX_PROMPT_CHARS:
        write(a.out, f'{FOOTER} usage · 프롬프트가 {len(prompt)}자다 — {MAX_PROMPT_CHARS}자를 넘으면 '
                     '명령줄에 안 든다. 큰 자료는 파일 경로를 주고 agy 가 읽게 한다\n')
        return EXIT['usage']

    if a.model and a.model.startswith(API_PREFIX) and not api_key():
        write(a.out, f'{FOOTER} usage · api: 후보는 키가 있어야 띄운다 — GOOGLE_API_KEY 나 GEMINI_API_KEY 가 없다\n')
        return EXIT['usage']

    # stderr 를 .md 로 둔다 — 회사 PC 의 Fasoo 가 .txt 를 감싸 러너가 제 꼬리를 못 읽는다(.md · .json 은 평문으로 남는다)
    log, raw_path, err_path = a.out + '.agy.log', a.out + '.raw.json', a.out + '.stderr.md'
    started = time.monotonic()
    tried = []
    models = candidates(a.model, bool(api_key()))
    for i, model in enumerate(models):
        try:
            agy_model, env, home = launch(model)
        except OSError as e:
            # 모델 탓이 아니다 — 다음 후보로 안 넘기고 까닭을 단 실패로 멈춘다(실패는 멈춘다는 차례 규칙 그대로)
            status, rc, res, raw_text, home = 'failed', None, {}, '', None
            where = api_home_path(os.path.expanduser('~'))
            err_text = (f'API 홈을 못 지었다 — {type(e).__name__}: {e}\n그 자리({where})에 못 쓰는 자리에서 돌았다. '
                        '맡긴 쪽의 샌드박스 안이면 샌드박스 밖에서 다시 부른다(스킬 본문)')
            break
        status, rc, res, raw_text, err_text = run_once(a, prompt, agy_model, log, raw_path, err_path, env)
        if status == 'spawn':
            write(a.out, f'{FOOTER} failed · agy 를 못 띄웠다 — {err_text}\n')
            return EXIT['failed']
        if status not in FAILOVER or i == len(models) - 1:
            break
        tried.append(f'{model}: {status}')
    elapsed = int(time.monotonic() - started)

    answer = res.get('response') or ''
    usage = res.get('usage') or {}
    conv = res.get('conversation_id')
    cells = {'rc': f'rc={"-" if rc is None else rc}', 'elapsed': f'{elapsed}s', 'model': f'model={model or "agy 기본"}',
             'tokens': f'tokens in={usage.get("input_tokens", "-")} out={usage.get("output_tokens", "-")}',
             'conversation': conversation_field(home, conv)}
    if tried:
        cells['failover'] = f'failover={"; ".join(tried)}'
    if status != 'ok':
        cells['log'] = f'log={log}'
    footer = common.footer_line(FOOTER, FOOTER_FIELDS, status, cells)
    if status == 'ok':
        for p in (raw_path, err_path, log):
            try:
                os.remove(p)
            except OSError:
                pass
        write(a.out, f'{answer.rstrip()}\n\n{footer}\n')
    else:
        # 답이 없으면 agy 가 낸 것을 그대로 둔다 — 까닭이 거기 있다. 로그도 남긴다.
        write(a.out, f'{answer or raw_text}\n{err_text}\n{footer}\n')
    return EXIT[status]


def main():
    return common.main(build_parser, help_epilog, run, FOOTER, EXIT)


if __name__ == '__main__':
    sys.exit(main())
