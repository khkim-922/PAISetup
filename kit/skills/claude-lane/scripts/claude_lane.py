"""셸과 제 격리 워크트리를 가진 헤드리스 Claude 레인(`claude -p`)을 띄우고, 끝나면 보고 · 비용 · 인증 · 거절 · 이어 묻기 값을 거둔다.

    python claude_lane.py --name <이름> --prompt-file <봉투> --out <보고 파일> --cwd <저장소>
                          [--base <가지>] [--billing subscription|api] [--key-env <환경변수 이름>] [--max-budget-usd <USD>]
                          [--model <이름>] [--effort <깊이>] [--timeout <초>]
    python claude_lane.py --resume <이름> --prompt-file <이어 줄 말> --out <보고 파일> --cwd <저장소> [...]

내는 것 — 띄우자마자 표준 출력에 시작 줄(트리 · 가지 · 피어 세션 이름) 하나, 끝나면 `--out` 에 보고(레인의 마지막 말)와 끝 줄
`[claude-lane] …`, 곁에 `<out>.result.json`(칸 전부) · `<out>.jsonl`(날 출력)을 쓰고 같은 끝 줄을 표준 출력에도 찍는다. 레인의 기록
(이어 묻기 값 · 결제 · 출발점)은 그 워크트리의 git 자리 `claude-lane/lane.json` 에 남아 트리를 걷으면 함께 걷힌다.
인자 · 끝 줄의 칸 · 종료 코드는 `--help` 가 든다. 왜 이렇게 띄우나와 잰 것은 `references/DESIGN.md` 가 든다.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

EXIT = {'ok': 0, 'failed': 1, 'billing': 1, 'budget': 2, 'quota': 2, 'empty': 2, 'timeout': 3, 'usage': 4}
FOOTER = '[claude-lane]'
# 갈래 낱말의 뜻 — `--help` 의 종료 코드 표가 `EXIT` 의 이름마다 단다. 갈래 낱말은 끝 줄의 첫 낱말이기도 하다
STATUS_WORDS = {'ok': '레인이 끝까지 돌고 보고를 냈다', 'failed': '실패했다(러너가 멈춘 것 포함)',
                'billing': '고른 결제와 다른 인증으로 돌았다(api 를 골랐는데 키가 안 셌다)',
                'budget': '지출 상한(--max-budget-usd)에 닿아 멈췄다 — 이어 묻기로 잇는다', 'quota': '한도 · 과부하',
                'empty': '빈 보고', 'timeout': '시간 초과 — 레인을 끊었다',
                'usage': '부르는 법이 틀렸다(인자 · 저장소 · 트리 · 키 환경변수 · 프롬프트 파일의 인코딩) 또는 Claude CLI 가 없다'}
# 끝 줄의 칸 — (이름, 뜻). 끝 줄을 짓는 `footer_line` 과 `--help` 가 같이 읽고, 차례가 끝 줄의 차례다
FOOTER_FIELDS = (
    ('rc', '레인 프로세스의 종료 코드'),
    ('elapsed', '걸린 시간 — `<N>s` 꼴(초)'),
    ('billing', '고른 결제 — subscription · api'),
    ('auth', '레인이 실제로 쓴 인증(날 출력 첫 줄의 apiKeySource) — api 면 ANTHROPIC_API_KEY 여야 한다. 못 읽으면 `-`'),
    ('cost', '`cost=$<USD>` — 레인이 센 비용(구독이면 한도로 치른 몫의 어림값)'),
    ('model', '레인이 쓴 모델'),
    ('turns', '레인의 턴 수'),
    ('denied', '거절된 도구 호출 `<이름>:<수>`(쉼표로 여럿), 없으면 `-` — 자동 모드 분류기와 push 막음이 한 일이다'),
    ('commits', '`commits=<N>` 출발점 뒤 레인 가지의 커밋 수 · `dirty=<N>` 커밋 안 한 경로 수'),
    ('resume', '`resume=<이름>` — 이어 묻기는 `--resume <이름>` 으로. 대화 id 가 안 남았으면 `-`'),
    ('tree', '레인의 워크트리 — 거두기는 agent-envelope 의 harvest_worktree.py 로'),
    ('result', '칸 전부를 든 `<out>.result.json` · 날 출력 `<out>.jsonl`'),
)

LANE_NAME_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,47}')   # 트리 폴더 · 가지 · 피어 세션 이름에 같이 들어 빈칸 · `/` 를 안 받는다
TREES_DIR = ('.claude', 'worktrees')   # 본 사본 안 트리 자리 — 하네스가 트리를 세우는 자리이고 저장소가 무시한다
TREE_PREFIX = 'lane-'                  # 트리 폴더 · 피어 세션 이름 머리
BRANCH_PREFIX = 'lane/'                # 레인 가지 머리
DEFAULT_BASE = 'main'                  # 트리가 뜨는 판 — 로컬 가지 이름(원격을 안 당긴다)
RECORD_DIR = 'claude-lane'             # 트리의 git 자리 안 기록 폴더 — 트리를 걷으면 git 이 함께 걷는다
RECORD_FILE = 'lane.json'
BILLINGS = ('subscription', 'api')
# 추론 깊이 — Claude CLI `--effort` 가 받는 낱말 그대로(`claude --help`). 안 주면 안 넘겨 CLI 가 사용자 설정을 따른다
EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')
KEY_VAR = 'ANTHROPIC_API_KEY'          # Claude CLI 가 API 키로 읽는 이름 — api 결제는 이 이름에만, 레인 프로세스에만 싣는다
KEY_ENV_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
# api 결제에서 레인 환경에서 걷는 것 — 다른 인증 값이 키를 앞지르거나, 게이트웨이 주소가 키를 그 게이트웨이로 보내지 않게
API_DROP_ENV = ('ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL')
BASE_URL_VAR = 'ANTHROPIC_BASE_URL'
# 요청이 Anthropic 으로 바로 가는 주소의 호스트 끝 — 이 길(또는 주소가 없을 때)에 선 `KEY_VAR` 는 Console 키다. 게이트웨이 자리의
#   `KEY_VAR` 는 그 게이트웨이의 키라 구독 결제에서도 둔다
DIRECT_HOST_SUFFIX = 'anthropic.com'
# 레인을 띄우는 깃발 — 자동 모드(분류기가 가른다 — `.claude/` 아래 편집도 선다), 묻는 창은 아무도 안 받아 묻는 대신 거절된다
CLAUDE_ARGS = ['-p', '--output-format', 'stream-json', '--verbose', '--permission-mode', 'auto', '--permission-prompts', 'none']
# push 막음 — 트리 밖으로 나가는 상태는 부모가 바꾼다. `git -C <자리> push` 꼴도 막는다. `git * push*` 처럼 넓히면 메시지에 push 가 든
#   커밋까지 막혀 쓰지 않는다. 가운데 `*` 뒤에는 `:*` 가 안 먹어(`git -C . push <원격>` 이 섰다) 빈칸 `*` 로 잇는다
PUSH_BAN = ['--disallowedTools', 'Bash(git push:*)', 'Bash(git push)', 'Bash(git -C * push *)', 'Bash(git -C * push)']
# 시간 한도 — Claude 부모의 배경 셸 한도(2 시간)보다 짧게 둬, 셸이 끊기 전에 러너가 레인을 끊고 끝 줄을 남긴다
LANE_TIMEOUT_SEC = 7000
BUDGET_RE = re.compile(r'[0-9]+(\.[0-9]+)?')
BUDGET_SUBTYPE = 'error_max_budget_usd'   # 상한에 닿은 결과의 subtype
GIT_TIMEOUT_SEC = 60
# 프로세스가 살았나 묻기 — 윈도는 열쇠만 받아 종료 값을 읽는다(신호를 안 보낸다 — 윈도의 `os.kill` 은 프로세스를 끝낸다)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259


# 러너 넷이 함께 쓰는 손은 곁에 깔린 스킬 agent-envelope 의 `runner_common.py` 가 들고, 싣는 이름은 그 스킬의 `handout.py` 에
# 적힌 것뿐이다. 그 부품을 못 실으면 여기서 말하고 끝낸다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'agent-envelope' / 'scripts'))
try:
    import runner_common as common
    from runner_common import CLAUDE_DROP_ENV, CLAUDE_MODEL_RE, PROMPT_ENCODINGS, write
except ImportError as missing:
    print(f'{FOOTER} failed · 공유 부품이 없다 — {missing}. 스킬 agent-envelope 이 이 스킬 곁에 깔려야 한다(설치를 다시 돌린다)')
    sys.exit(EXIT['failed'])


class Refused(Exception):
    """부르는 법이 틀렸다 — 끝 줄 `usage` 의 까닭."""


def git(args, cwd):
    """git 한 번 → (종료 코드, 표준 출력, 표준 오류). 못 띄우면 (None, '', 까닭)."""
    try:
        p = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=GIT_TIMEOUT_SEC, creationflags=common.CREATE_NO_WINDOW)
    except (OSError, subprocess.SubprocessError) as e:
        return None, '', str(e)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def main_checkout(cwd):
    """`cwd` 가 든 저장소의 본 사본 뿌리 — 트리 안에서 불러도 본 사본이다(공통 git 자리의 부모). 못 찾으면 Refused."""
    rc, out, err = git(['rev-parse', '--path-format=absolute', '--git-common-dir'], cwd)
    common_dir = Path(out) if rc == 0 and out else None
    if common_dir is None or common_dir.name != '.git':
        raise Refused(f'--cwd 가 본 사본이 있는 git 저장소가 아니다 — {cwd} {err}'.rstrip())
    return common_dir.parent


def tree_of(main, name):
    return main.joinpath(*TREES_DIR, TREE_PREFIX + name)


def make_tree(main, name, base):
    """본 사본의 `base` 에서 레인 트리와 가지를 세운다 → (트리, 출발 커밋). 트리 · 가지가 이미 있거나 git 이 지면 Refused."""
    tree = tree_of(main, name)
    if tree.exists():
        raise Refused(f'트리가 이미 있다 — {tree}. 끝난 레인을 이으면 --resume {name}, 새 레인이면 다른 --name')
    rc, sha, err = git(['rev-parse', '--verify', '--quiet', f'{base}^{{commit}}'], main)
    if rc != 0 or not sha:
        raise Refused(f'--base {base} 를 본 사본에서 못 찾는다 {err}'.rstrip())
    rc, _, err = git(['worktree', 'add', '-q', str(tree), '-b', BRANCH_PREFIX + name, sha], main)
    if rc != 0:
        raise Refused(f'트리를 못 세웠다 — {err}')
    return tree, sha


def record_path(tree):
    """레인 기록 파일 자리 — 트리의 git 자리 안. 트리가 git 트리가 아니면 Refused."""
    rc, out, err = git(['rev-parse', '--path-format=absolute', '--git-dir'], tree)
    if rc != 0 or not out:
        raise Refused(f'레인 트리를 git 이 못 읽는다 — {tree} {err}'.rstrip())
    return Path(out) / RECORD_DIR / RECORD_FILE


def read_record(tree):
    path = record_path(tree)
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise Refused(f'레인 기록을 못 읽는다 — {path} ({e}). 이 러너로 띄운 트리가 아니다') from e


def save_record(tree, record):
    path = record_path(tree)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding='utf-8')


def tree_state(tree, base_sha):
    """(출발점 뒤 커밋 수, 커밋 안 한 경로 수) — 못 세면 '-'."""
    rc, n, _ = git(['rev-list', '--count', f'{base_sha}..HEAD'], tree)
    commits = n if rc == 0 else '-'
    rc, out, _ = git(['status', '--porcelain'], tree)
    dirty = len(out.splitlines()) if rc == 0 else '-'
    return commits, dirty


def child_env(billing, key_env, env=None):
    """레인 프로세스에 줄 환경 — 부른 세션의 표지를 걷고, api 결제면 `key_env` 의 값을 `KEY_VAR` 로 싣고 다른 인증 값 · 게이트웨이
    주소를 걷는다. 구독은 Claude CLI 가 제 설정으로 붙는 길이라 게이트웨이 값(사내)은 두고, Anthropic 으로 바로 가는 자리에 선
    Console 키만 걷는다 — 키로 띄운 레인이 다시 띄우는 구독 레인이 그 키를 물려받아 크레딧을 쓰지 않게. 키 값이 비었으면 Refused —
    값은 어디에도 안 찍는다."""
    env = dict(os.environ if env is None else env)
    out = {k: v for k, v in env.items() if k not in CLAUDE_DROP_ENV}
    if billing != 'api':
        if direct_to_anthropic(env):
            out.pop(KEY_VAR, None)
        return out
    key = env.get(key_env or '') or ''
    if not key.strip():
        raise Refused(f'환경변수 {key_env} 에 키가 없다 — api 결제는 그 이름의 환경변수에 든 키를 레인에만 싣는다')
    for k in API_DROP_ENV:
        out.pop(k, None)
    out[KEY_VAR] = key.strip()
    return out


def direct_to_anthropic(env):
    """요청이 Anthropic 으로 바로 가나 — 주소가 없거나 그 호스트가 `DIRECT_HOST_SUFFIX` 로 끝나면 참."""
    url = (env.get(BASE_URL_VAR) or '').strip()
    if not url:
        return True
    try:
        host = urlsplit(url).hostname or ''
    except ValueError:
        return False
    return host == DIRECT_HOST_SUFFIX or host.endswith('.' + DIRECT_HOST_SUFFIX)


def lane_argv(name, model, effort, budget, session):
    """머리 뒤에 붙일 인자 — 프롬프트는 안 싣는다(표준 입력). 피어 세션 이름은 트리 폴더 이름과 같다. 빈 값은 그 깃발을 안 싣는다."""
    out = [*CLAUDE_ARGS, *PUSH_BAN, '--name', TREE_PREFIX + name]
    if model:
        out += ['--model', model]
    if effort:
        out += ['--effort', effort]
    if budget:
        out += ['--max-budget-usd', budget]
    if session:
        out += ['--resume', session]
    return out


def extract(events):
    """날 출력 이벤트 → 칸 사전. 첫 `system/init` 이 인증 · 모델 · 대화 id 를, 마지막 `result` 가 보고 · 비용 · 거절을 든다."""
    init, result = {}, {}
    for e in events:
        if e.get('type') == 'system' and e.get('subtype') == 'init' and not init:
            init = e
        elif e.get('type') == 'result':
            result = e
    denials = [d for d in result.get('permission_denials') or [] if d]
    names = [str(d.get('tool_name') or '?') if isinstance(d, dict) else str(d) for d in denials]
    return {'auth': init.get('apiKeySource') or '-', 'model': init.get('model') or '-',
            'session': result.get('session_id') or init.get('session_id') or '',
            'report': result.get('result') or '', 'cost': result.get('total_cost_usd'), 'turns': result.get('num_turns'),
            'subtype': result.get('subtype') or '', 'is_error': bool(result.get('is_error')), 'has_result': bool(result),
            'api_error_status': result.get('api_error_status'),
            'denied': {n: names.count(n) for n in sorted(set(names))}, 'denials': denials}


def judge(ex, rc, err_text, billing):
    """(갈래, 까닭). 결제 약속(api 면 키가 셌다)을 먼저 보고, 그다음 결과 이벤트로 가른다."""
    if billing == 'api' and ex['auth'] != '-' and ex['auth'] != KEY_VAR:
        return 'billing', f'api 결제를 골랐는데 레인이 {ex["auth"]} 로 붙었다 — 키가 안 셌다'
    if ex['subtype'] == BUDGET_SUBTYPE:
        return 'budget', '지출 상한에 닿았다'
    if rc != 0 or not ex['has_result'] or ex['is_error'] or ex['subtype'] != 'success':
        reason = ex['report'] or ex['subtype'] or '결과 이벤트가 없다'
        quota = common.claude_quota(ex['api_error_status'], f'{reason}\n{err_text}')
        return ('quota' if quota else 'failed'), reason
    if not ex['report'].strip():
        return 'empty', ''
    return 'ok', ''


def settle(a):
    """인자 · 기록에서 이 판의 값을 정한다 → (본 사본, 트리 또는 None, 기록). 새 레인은 아직 트리를 안 세운다 — 환경 · CLI 를 다 본
    뒤에 세워, 못 띄울 판에 빈 트리가 안 남는다. 틀리면 Refused."""
    if bool(a.name) == bool(a.resume):
        raise Refused('--name(새 레인)과 --resume(끝난 레인 잇기) 가운데 하나만 준다')
    name = a.name or a.resume
    if not LANE_NAME_RE.fullmatch(name):
        raise Refused(f'레인 이름 {name!r} — 영숫자로 열고 영숫자 · . · _ · - 만(48 자까지)')
    main = main_checkout(a.cwd)
    record, tree = {}, None
    if a.resume:
        tree = tree_of(main, name)
        if not tree.is_dir():
            raise Refused(f'트리가 없다 — {tree}. 이미 거뒀으면 새 레인으로 띄운다')
        record = read_record(tree)
        if alive(record.get('pid')):
            raise Refused(f'레인이 아직 돈다(러너 pid {record["pid"]}) — 도는 레인에는 피어 세션 {TREE_PREFIX}{name} 에 SendMessage 로 '
                          '보내고, 이어 묻기는 끝 줄이 난 뒤에 한다')
        if not record.get('session'):
            raise Refused('레인 기록에 대화 id 가 없다 — 앞 판이 대화를 세우기 전에 멈췄다. 새 레인으로 띄운다')
    billing = a.billing or record.get('billing') or BILLINGS[0]
    key_env = a.key_env or (record.get('key_env') if billing == 'api' else None)
    budget = a.max_budget_usd or record.get('budget')
    model = a.model or record.get('model')
    effort = a.effort or record.get('effort')
    if billing == 'api' and not (key_env and KEY_ENV_RE.fullmatch(key_env)):
        raise Refused('api 결제는 --key-env <키가 든 환경변수 이름> 을 준다(키 값이 아니라 이름)')
    if billing != 'api' and a.key_env:
        raise Refused('--key-env 는 --billing api 와 같이 준다')
    if billing == 'api' and not budget:
        raise Refused('api 결제는 --max-budget-usd <USD> 로 지출 상한을 준다 — 크레딧을 쓰는 판이라 상한은 부르는 쪽이 정한다')
    if budget and not BUDGET_RE.fullmatch(str(budget)):
        raise Refused(f'--max-budget-usd {budget!r} — 0 보다 큰 수')
    if model and not CLAUDE_MODEL_RE.fullmatch(model):
        raise Refused(f'--model 에 따옴표 · 공백이 든다 — {model!r}')
    if a.timeout <= 0:
        raise Refused('--timeout 은 1 이상의 초')
    record.update({'name': name, 'billing': billing, 'key_env': key_env, 'budget': budget and str(budget), 'model': model,
                   'effort': effort})
    return main, tree, record


def alive(pid):
    """러너 프로세스 `pid` 가 살았나 — 레인 프로세스는 러너와 함께 끝나 러너가 살았으면 레인이 돈다. 없거나 못 물으면 거짓."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name != 'nt':
        try:
            os.kill(pid, 0)
        except PermissionError:
            return True
        except OSError:
            return False
        return True
    import ctypes
    kernel = ctypes.windll.kernel32
    handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == STILL_ACTIVE
    finally:
        kernel.CloseHandle(handle)


def launch(cmd, tree, env, prompt, out, timeout):
    """레인을 한 번 띄워 끝까지 지켜본다 → (갈래 또는 None, 종료 코드, 이벤트, stderr 글). 날 출력은 `<out>.jsonl` 에 남긴다."""
    raw_path, err_path = f'{out}.jsonl', f'{out}.stderr.md'
    with tempfile.TemporaryFile() as stdin:
        stdin.write(prompt.encode('utf-8'))
        stdin.seek(0)
        waited, rc, events, err_text = common.watch(cmd, str(tree), env, stdin, raw_path, err_path, timeout)
    if not err_text.strip():
        common.remove(err_path)
    return waited, rc, events, err_text


def footer_cells(rc, elapsed, record, ex, commits, dirty, tree, out):
    denied = ','.join(f'{k}:{v}' for k, v in ex['denied'].items()) or '-'
    cost = ex['cost']
    return {'rc': f'rc={rc}', 'elapsed': f'{elapsed}s', 'billing': f'billing={record["billing"]}', 'auth': f'auth={ex["auth"]}',
            'cost': f'cost=${cost:.4f}' if isinstance(cost, (int, float)) else 'cost=-', 'model': f'model={ex["model"]}',
            'turns': f'turns={ex["turns"] if ex["turns"] is not None else "-"}', 'denied': f'denied={denied}',
            'commits': f'commits={commits} dirty={dirty}', 'resume': f'resume={record["name"] if ex["session"] else "-"}',
            'tree': f'tree={tree}', 'result': f'result={out}.result.json · {out}.jsonl'}


def run(a):
    a.prompt, bad = common.read_prompt(a.prompt_file)
    out = os.path.abspath(a.out)
    try:
        if bad:
            raise Refused(bad)
        main, tree, record = settle(a)
        env = child_env(record['billing'], record['key_env'])
        head = common.claude_head()
        if head is None:
            raise Refused('Claude Code CLI(`claude`)를 못 찾는다')
        if tree is None:
            tree, base_sha = make_tree(main, record['name'], a.base)
            record.update({'tree': str(tree), 'branch': BRANCH_PREFIX + record['name'], 'base': a.base, 'base_sha': base_sha})
        record['pid'] = os.getpid()   # 도는 동안의 표 — 끝나면 걷는다. 러너가 끊겨 남아도 그 pid 가 죽어 있어 이어 묻기를 안 막는다
        save_record(tree, record)
    except Refused as e:
        line = f'{FOOTER} usage · {e}'
        write(out, line + '\n')
        print(line, flush=True)
        return EXIT['usage']

    print(f'{FOOTER} 떴다 · 트리 {tree} · 가지 {record["branch"]} · 출발 {record["base_sha"][:8]} · 결제 {record["billing"]} · '
          f'피어 세션 {TREE_PREFIX}{record["name"]} — 도는 동안 부모 Claude 세션은 ListAgents 에서 이 이름을 찾아 SendMessage 로 '
          f'고침을 보낼 수 있다 · 끝 줄은 {out}', flush=True)
    started = time.monotonic()
    cmd = head + lane_argv(record['name'], record['model'], record.get('effort'), record['budget'],
                           record.get('session') if a.resume else None)
    waited, rc, events, err_text = launch(cmd, tree, env, a.prompt, out, a.timeout)
    elapsed = int(time.monotonic() - started)
    if waited == 'spawn':
        line = f'{FOOTER} usage · 못 띄웠다 — {err_text}'
        write(out, line + '\n')
        print(line, flush=True)
        return EXIT['usage']
    ex = extract(events)
    status, reason = judge(ex, rc, err_text, record['billing'])
    status = waited or status
    record.pop('pid', None)
    if ex['session']:
        record['session'] = ex['session']
    record.setdefault('runs', []).append(out)
    save_record(tree, record)
    commits, dirty = tree_state(tree, record['base_sha'])
    cells = footer_cells(rc, elapsed, record, ex, commits, dirty, tree, out)
    footer = common.footer_line(FOOTER, FOOTER_FIELDS, status, cells)
    with open(f'{out}.result.json', 'w', encoding='utf-8') as f:
        json.dump({'status': status, 'reason': reason, 'rc': rc, 'elapsed_sec': elapsed, 'billing': record['billing'],
                   'auth': ex['auth'], 'cost_usd': ex['cost'], 'model': ex['model'], 'turns': ex['turns'],
                   'session': ex['session'], 'denials': ex['denials'], 'commits': commits, 'dirty': dirty,
                   'tree': str(tree), 'branch': record['branch'], 'base_sha': record['base_sha']}, f, ensure_ascii=False, indent=1)
    if status != 'ok':
        reason = '\n'.join(s for s in (reason, err_text[-common.STDERR_TAIL_CHARS:].strip()) if s)
    common.write_answer(out, status, ex['report'], footer, reason)
    print(footer, flush=True)
    return EXIT[status]


def build_parser():
    ap = common.base_parser('셸과 제 격리 워크트리를 가진 헤드리스 Claude 레인(claude -p)을 띄우고, 보고와 끝 줄을 --out 파일로 받는다.',
                            '레인 트리를 세울 저장소 — 그 안 어디든(트리 안이어도) 본 사본의 .claude/worktrees/ 에 선다')
    ap.add_argument('--name', metavar='NAME', help='새 레인 이름 — 트리 lane-<NAME> · 가지 lane/<NAME> · 피어 세션 lane-<NAME>')
    ap.add_argument('--resume', metavar='NAME', help='끝난 레인을 제 트리에서 대화째 잇는다 — 프롬프트 파일이 이어 줄 말이다')
    ap.add_argument('--base', default=DEFAULT_BASE, metavar='REF', help=f'트리가 뜨는 본 사본의 판. 기본 {DEFAULT_BASE}(로컬)')
    ap.add_argument('--billing', choices=BILLINGS, help='결제 — subscription(기본 · claude 가 제 설정으로 붙는다) · api(--key-env 의 키)')
    ap.add_argument('--key-env', metavar='VAR', help='api 결제의 키가 든 환경변수 이름 — 값은 레인 프로세스에만 실린다')
    ap.add_argument('--max-budget-usd', metavar='USD', help='이 판의 지출 상한 — api 결제면 꼭 준다. 이어 묻기는 앞 판 값을 물려받는다')
    ap.add_argument('--model', metavar='NAME', help='레인의 모델 — 무게마다의 이름은 agent-envelope 의 models.conf')
    ap.add_argument('--effort', choices=EFFORTS, metavar='LEVEL',
                    help=f'레인의 추론 깊이 — {" · ".join(EFFORTS)}. 안 주면 안 넘겨 Claude CLI 가 사용자 설정을 따른다')
    ap.add_argument('--timeout', type=int, default=LANE_TIMEOUT_SEC, metavar='SEC', help=f'시간 한도(초). 기본 {LANE_TIMEOUT_SEC}')
    return ap


def help_epilog():
    """`--help` 의 아래쪽 — 레인 · 결제 · 끝 줄 · 이어 묻기 · 프롬프트 파일 · 종료 코드. 끝 줄 칸은 `FOOTER_FIELDS` 에서, 종료 코드는
    `EXIT` 에서 짓는다."""
    return '\n'.join([
        '레인:',
        f'  본 사본의 --base 에서 트리 {"/".join(TREES_DIR)}/{TREE_PREFIX}<이름> 과 가지 {BRANCH_PREFIX}<이름> 을 세우고 그 트리에서 claude -p 를 띄운다.',
        '  권한은 자동 모드(분류기가 가르고 .claude/ 아래 편집도 선다) · 묻는 창은 아무도 안 받아 묻는 대신 거절된다(끝 줄 denied=).',
        f'  셸 · 편집 · 스킬 · 홈 규범 · 사용자 설정 · 훅은 대화형 세션과 같이 실린다. {" ".join(PUSH_BAN[1:])} 는 막는다 — 트리 밖으로 나가는 상태는 부모 몫이다.',
        '  표준 출력: 띄우자마자 시작 줄(트리 · 가지 · 피어 세션 이름), 끝나면 끝 줄. 도는 동안 같은 PC 의 Claude 세션에는 피어 세션',
        f'  {TREE_PREFIX}<이름> 으로 보여 SendMessage 로 고침을 보낼 수 있다.',
        '',
        '결제:',
        '  subscription(기본)  Claude CLI 가 제 설정으로 붙는다 — 사외는 claude 로그인(구독 한도), 사내는 그 자리의 게이트웨이 값.',
        f'                      Anthropic 으로 바로 가는 자리에 선 {KEY_VAR}(키로 띄운 레인이 물려받은 Console 키)만 걷는다 — 게이트웨이 키는 둔다.',
        f'  api                 --key-env 이름의 환경변수 값을 레인 프로세스에만 {KEY_VAR} 로 싣고 {" · ".join(API_DROP_ENV)} 를 걷는다.',
        '                      --max-budget-usd 가 꼭 선다. 끝 줄 auth= 가 ANTHROPIC_API_KEY 가 아니면 billing 으로 끝난다. 키 값은 어디에도 안 찍는다.',
        '',
        f'끝 줄: --out 파일의 맨 끝 줄이자 표준 출력의 끝 줄이다. `{FOOTER} <갈래>` 뒤에 아래 칸이 " · " 로 이어진다.',
        '  인자가 틀렸거나 러너가 멈췄으면 칸 없이 `<갈래> · <까닭>` 만 든다. --out 의 끝 줄 앞은 레인의 마지막 말(보고)이다.',
        *[f'  {name:<9}{meaning}' for name, meaning in FOOTER_FIELDS],
        '',
        '이어 묻기: --resume <이름> --prompt-file <이어 줄 말> --out <새 보고 파일> --cwd <저장소>. 같은 트리에서 대화 id 로 잇고,',
        '  결제 · 키 환경변수 이름 · 상한 · 모델 · 추론 깊이는 앞 판 기록을 물려받는다(주면 이긴다). 트리를 거두면 기록도 함께 걷혀 못 잇는다.',
        '',
        f'프롬프트 파일: {PROMPT_ENCODINGS} 만 받는다. 래퍼가 UTF-8 로 옮겨 표준 입력으로 넘긴다(길이 한도 없음).',
        '',
        '종료 코드(끝 줄의 갈래 이름과 같다):',
        *common.exit_table(EXIT, STATUS_WORDS),
    ]) + '\n'


def main():
    if hasattr(sys.stdout, 'reconfigure'):   # 윈도 파이프의 기본 인코딩(cp949)은 `—` 를 못 적어 죽는다 — 에이전트 셸은 UTF-8 로 읽는다
        sys.stdout.reconfigure(encoding='utf-8')
    return common.main(build_parser, help_epilog, run, FOOTER, EXIT)


if __name__ == '__main__':
    sys.exit(main())
