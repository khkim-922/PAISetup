"""GitHub Copilot CLI 훅 어댑터 — 셸 실수 문 · 게이트 건너뛰기 물음 · DRM 길잡이 · PowerShell UTF-8 BOM 보정을 Copilot 의 꼴로 건넨다.

    <cmd.exe> /d /c if exist <이 파일> if exist <해석기> <해석기> -X utf8 <이 파일> <갈래> || exit 0     (Copilot 이 띄우는 꼴)
      갈래 pre-tool   < preToolUse 입력           (matcher 셸 · 읽기 도구)
      갈래 post-tool  < postToolUse 입력          (matcher 쓰기 도구)
      갈래 prompt     < userPromptSubmitted 입력
    python -X utf8 copilot-hooks.py install --config ~/.copilot/settings.json
    python -X utf8 copilot-hooks.py remove  --config ~/.copilot/settings.json

**왜 어댑터인가.** 몸통은 Claude 훅 꼴(`tool_name` · `tool_input`)을 받는다. Copilot 은 제 이벤트(`preToolUse` 따위)에
`toolName` · `toolArgs` 를 주고, 도구 이름 · 열쇠도 다르다 — 셸은 `powershell`(`command`), 읽기는 `view`(`path`), 고치기는
`apply_patch` 의 패치 글 하나(또는 `create` · `edit` · `str_replace_editor` 의 `path`). 판정은 몸통의 것을 불러 쓰고 여기서는
꼴만 바꾼다 — 같은 판정을 두 벌 두면 한쪽만 낡는다. 입력 · 출력 꼴은 Copilot 문서 「Hooks configuration」의 것이다
(<https://docs.github.com/en/copilot/reference/hooks-configuration>).

**싣는 것** — 셸 실수 문(`shell-slip.py` — Copilot 의 셸은 PowerShell 이라 그 문법으로 가른다) · 게이트 건너뛰기 물음(세션
저장소의 `.claude/hooks/gate-bypass-ask.sh` 를 그대로 부른다) · DRM 길잡이(`drm-guide.py` · 셸 낱말 읽기는 `agy-hooks.py`) ·
BOM 보정(`codex-safety-hooks.py` 의 패치 경로 읽기와 BOM 찍기). 겹역슬래시 훅은 안 싣는다 — Copilot 은 PowerShell 로 돌아
역슬래시를 안 접어, 두 배로 고치면 명령이 틀어진다. 그림 문 · 컨텍스트 알림 · 멈춤 메모 · 웹 다시 찾기 · Claude 전용 알림들은
Copilot 에 그 사고나 그 입력(`transcript_path`)이 없다.

**모델에게 닿는 자리.** preToolUse 는 막는 출력(`permissionDecision` · `permissionDecisionReason`)의 까닭만 모델에 닿고 결정 없는
덧말은 버려진다. postToolUse · userPromptSubmitted 는 맨 위 `additionalContext` 가 닿는다. 그래서 DRM 길잡이는 둘에 건다:
사람의 글에 감긴 파일의 경로가 있으면 그 턴의 덧말로, 모델이 감긴 파일을 `view` 나 셸로 열려 하면 막고 까닭으로 — agy
어댑터와 같은 판정이다(감긴 파일은 열어도 글자가 안 나와 막아서 잃는 것이 없다).

**`ask` 는 그대로 넘긴다.** 셸 실수 문과 게이트 물음은 사람에게 묻는 훅이라, 대화형 Copilot 에서는 사람에게 묻는다. Copilot 의
autopilot 모드(설치기가 심는다)와 `-p` 에서는 Copilot 이 `ask` 를 막기로 바꾸고 까닭은 그대로 모델에 닿는다. 묻기와 막기가
함께 서면 막기다(Copilot 도 하나라도 막으면 막는다) — 까닭은 다 잇는다.

**게이트 물음은 세션 저장소의 껍데기를 부른다.** 그 저장소의 등록은 Copilot 에서 아무것도 안 하게 서 있다(껍데기 머리말).
세션 자리(`cwd`)에서 저장소 뿌리(`.git` 이 선 자리)까지 거슬러 올라 그 껍데기를 찾고, Git 의 bash 로 Claude 꼴 입력을 먹인다.
⚠ **Copilot 이 신뢰한 폴더에서만 부른다** — 남이 만든 저장소의 껍데기를 우리 홈 훅이 돌리면 Copilot 의 폴더 신뢰를 건너뛴다.
  신뢰는 Copilot 홈 설정의 `trustedFolders`(그 자리이거나 그 위) · `COPILOT_ALLOW_ALL=true` 로 가른다.
⚠ 껍데기의 두 글롭이 다 `git` 을 요구해, 먹일 입력에 `git` 이 없으면 bash 를 안 띄운다 — 띄우는 값이 셸 호출마다 붙는다.

**재다 져도 막지 않는다** — Copilot 은 preToolUse 훅이 0 이 아닌 값으로 끝나거나 못 뜨면 그 도구 호출을 막는다. 깨진 훅
하나가 Copilot 의 모든 셸 · 읽기를 막는 것이 이 어댑터가 막아야 할 사고다. 그래서 세 겹이다:
  · 등록 — `cmd.exe` 가 이 파일과 해석기가 있을 때만 띄우고, 해석기가 0 이 아닌 값으로 끝나면 0 으로 바꾼다(`|| exit 0`).
    해석기를 지우거나 판을 옮기거나 이 파일이 문법 오류여도 막지 않고 지나간다. `cmd.exe` 는 윈도에 늘 있다
  · 갈래 — 모르는 갈래(등록과 이 파일의 판이 어긋난 자리)는 아무것도 안 내고 0 이다
  · 판정 — 몸통마다 따로 감싸 하나가 져도 나머지는 선다. 진 사실은 stderr 한 줄로 남긴다
⚠ **둘 것에는 아무것도 안 낸다** — `"allow"` 는 Copilot 의 권한 묻기를 건너뛰게 한다. 우리 훅이 사람의 권한 설정을 넓히면
   안 된다.

**배선도 이 파일이 든다** — `install` 이 Copilot 사용자 설정(`settings.json`)의 `hooks` 에 이벤트마다 우리 항목 하나를 얹는다.
우리 항목은 인자에 이 파일 이름(`copilot-hooks.py`)이 선 것이다 — 항목에 우리 표지 열쇠를 안 단다: 그 파일의 `hooks` 칸은 항목
하나라도 틀리면 칸째 버려져 사람의 훅까지 죽는다. 다시 깔면 그 자리에서 지금 꼴로 갈고, 남의 항목 · 다른 열쇠 · BOM · 줄끝 ·
들여쓰기는 둔다. `remove` 는 우리 항목만 걷고, 걷어서 빈 이벤트 · 빈 `hooks` 는 지운다 — 우리 항목이 없던 빈 칸은 둔다.
⚠ 명령 글자는 셸을 안 지나 `exec` · `args` 로 간다 — 인자에 빈칸 · `cmd.exe` 가 가르는 글자가 들면 Copilot 이 따옴표를 치는데
  `cmd.exe` 는 그 따옴표 꼴을 모른다. 그래서 그런 폴더는 8.3 짧은 이름으로 바꾸고, 그것도 안 되면 안 심고 까닭을 낸다.
⚠ 해석기는 `install` 을 돌린 해석기(`sys.executable`)다 — 설치기가 다시 돌 때마다 그 자리로 갈린다.
⚠ 못 읽는 파일(JSON 이 아님 · 맨 위가 표가 아님 · `hooks` 나 이벤트 칸의 꼴이 다름)은 안 건드리고 까닭을 낸다. 고쳐 쓰기 전에
   원본을 곁에 떠 둔다 — 떠 두고 옆 파일에 써서 바꿔 달고 옛 원본을 걷는 손은 Codex 병합기의 `replace_with_backup` 이다(곁에
   같이 실린다).

출력 계약(`install` · `remove`) — 한 줄에 하나:
  CHANGED=0|1 · BACKUP=<경로>(고쳐 쓴 판에만) · ERROR=<까닭>(아무것도 안 썼다 · 종료 1)
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT_NAME = 'copilot-hooks.py'   # 우리 항목을 알아보는 표지 — 등록 인자에 선 이 이름

# Copilot 의 도구 — 이름과 인자 열쇠
SHELL_TOOL = 'powershell'           # 윈도의 셸 — 인자 `command`
VIEW_TOOL = 'view'
EDITOR_TOOL = 'str_replace_editor'  # `command` 로 갈린다 — view · create · str_replace · insert
EDITOR_VIEW = 'view'
EDITOR_WRITES = ('create', 'str_replace', 'insert')
PATCH_TOOL = 'apply_patch'          # 인자가 패치 글 하나
PATH_WRITE_TOOLS = ('create', 'edit')
PATH_KEY = 'path'
COMMAND_KEY = 'command'
PRE_TOOLS = (SHELL_TOOL, VIEW_TOOL, EDITOR_TOOL)
POST_TOOLS = (PATCH_TOOL,) + PATH_WRITE_TOOLS + (EDITOR_TOOL,)

# 몸통 — 이 파일 곁에 같이 실린다
SHELL_SLIP_BODY = 'shell-slip.py'
DRM_BODY = 'drm-guide.py'
BOM_BODY = 'codex-safety-hooks.py'
AGY_ADAPTER = 'agy-hooks.py'         # 셸 낱말 읽기 · 읽는 손 가르기(`drm_guide`) · `short_path` 의 진본
MERGER_FILE = 'codex-hook-install.py'   # 원본을 떠 두고 고쳐 쓰는 손(`replace_with_backup` · `write_atomic`)의 진본
SHELL_DIALECT_TOOL = 'PowerShell'    # 셸 실수 문의 도구 이름 — 그 문법으로 가른다

GATE_SCRIPT = ('.claude', 'hooks', 'gate-bypass-ask.sh')
GATE_NEEDLE = 'git'                  # 껍데기의 두 글롭이 다 요구하는 글자(머리말 ⚠)
GATE_TIMEOUT = 5                     # 초 — 껍데기는 셸 내장만 쓴다
TRUST_KEY = 'trustedFolders'
TRUST_FILES = ('config.json', 'settings.json')
ALLOW_ALL_ENV = 'COPILOT_ALLOW_ALL'

DECISION_RANK = {'ask': 1, 'deny': 2}   # 함께 서면 큰 쪽 — 하나라도 막으면 막는다
HOOK_TIMEOUT = 10                    # 초 — Copilot 은 넘기면 지나간다
HOOKS_KEY = 'hooks'
EVENTS = {'preToolUse': ('pre-tool', PRE_TOOLS),
          'postToolUse': ('post-tool', POST_TOOLS),
          'userPromptSubmitted': ('prompt', None)}   # 이벤트 → (갈래, matcher 도구 — None 은 matcher 없음)
CMD_UNSAFE = set(' \t&|<>^%"()')     # 따옴표 없이 cmd.exe 를 건너는 낱말에 못 드는 글자
BACKUP_SUFFIX = '.before-paisetup-'
DEFAULT_INDENT = 2


# ── 꼴 바꾸기 ────────────────────────────────────────────────────────────────────
def load(name, filename):
    """곁의 몸통을 모듈로 부른다 — 이름에 `-` 가 들어 import 문으로는 못 부른다."""
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tool_call(data):
    """(도구 이름, 인자) — 인자는 표이거나(셸 · 읽기) 글이다(`apply_patch` 의 패치 글). Copilot 문서는 인자를 JSON 글로도
    적어, 표로 풀리는 글은 표로 받는다 — 패치 글은 JSON 이 아니라 글 그대로 남는다."""
    args = data.get('toolArgs')
    if isinstance(args, str):
        try:
            decoded = json.loads(args)
        except ValueError:
            decoded = None
        if isinstance(decoded, dict):
            args = decoded
    return str(data.get('toolName') or ''), args


def session_cwd(data):
    return str(data.get('cwd') or '') or os.getcwd()


def run_body(mod, payload):
    """몸통의 `main` 을 Claude 꼴 입력으로 돌려 그 표준 출력을 낸다 — 몸통의 실패 규율까지 그대로 쓴다."""
    out = io.StringIO()
    saved = sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
    try:
        with contextlib.redirect_stdout(out):
            mod.main()
    finally:
        sys.stdin = saved
    return out.getvalue()


def decision_of(text):
    """훅 출력 → (결정, 까닭). Claude 꼴(`hookSpecificOutput`)과 Copilot 꼴(맨 위)을 다 읽는다. 묻기 · 막기가 아니면 (None, '')."""
    try:
        o = json.loads(text) if text.strip() else {}
    except ValueError:
        return None, ''
    if not isinstance(o, dict):
        return None, ''
    inner = o.get('hookSpecificOutput') if isinstance(o.get('hookSpecificOutput'), dict) else o
    decision = inner.get('permissionDecision')
    if decision not in DECISION_RANK:
        return None, ''
    return decision, str(inner.get('permissionDecisionReason') or '')


def guarded(label, fn, *args):
    """판정 하나를 감싼다 — 지면 stderr 한 줄을 남기고 (None, '') 다(머리말 「재다 져도 막지 않는다」)."""
    try:
        return fn(*args)
    except BaseException as e:  # noqa: BLE001 — 몸통의 종료(`SystemExit`)까지 받는다
        sys.stderr.write('Copilot 훅 %s — 재다 졌다(%s)\n' % (label, type(e).__name__))
        return None, ''


# ── 판정 ─────────────────────────────────────────────────────────────────────────
def shell_slip(command):
    return load('shell_slip', SHELL_SLIP_BODY).judge(command, SHELL_DIALECT_TOOL)


def project_gate(cwd):
    """(저장소 뿌리, 껍데기) — 세션 자리에서 `.git` 이 선 자리까지 거슬러 올라 처음 만난 껍데기. 없으면 None.
    ⚠ 자리를 링크 끝으로 풀지 않는다 — 신뢰 목록은 사람이 쓴 꼴(매핑 드라이브 · subst)이라, 풀면 같은 폴더가 안 맞는다."""
    here = pathlib.Path(os.path.abspath(cwd))
    for d in (here,) + tuple(here.parents):
        script = d.joinpath(*GATE_SCRIPT)
        if script.is_file():
            return d, script
        if (d / '.git').exists():
            return None
    return None


def copilot_home():
    return pathlib.Path(os.environ.get('COPILOT_HOME') or pathlib.Path.home() / '.copilot')


def read_jsonc(path):
    """Copilot 홈의 설정 표 — 머리의 `//` 줄을 걷고 읽는다. 못 읽으면 빈 표."""
    try:
        text = path.read_text(encoding='utf-8-sig')
    except OSError:
        return {}
    try:
        o = json.loads('\n'.join(ln for ln in text.splitlines() if not ln.lstrip().startswith('//')))
    except ValueError:
        return {}
    return o if isinstance(o, dict) else {}


def trusted(root):
    """Copilot 이 이 저장소를 신뢰했나 — `COPILOT_ALLOW_ALL=true` 이거나 `trustedFolders` 가운데 그 자리 또는 그 위가 있다."""
    if os.environ.get(ALLOW_ALL_ENV) == 'true':
        return True
    target = os.path.normcase(os.path.abspath(str(root))).rstrip('\\/')
    for name in TRUST_FILES:
        folders = read_jsonc(copilot_home() / name).get(TRUST_KEY)
        for f in folders if isinstance(folders, list) else ():
            if not isinstance(f, str) or not f.strip():
                continue
            base = os.path.normcase(os.path.abspath(os.path.expanduser(f))).rstrip('\\/')
            if target == base or target.startswith(base + os.sep):
                return True
    return False


def git_bash():
    """껍데기를 돌릴 Git 의 bash — PATH 의 git 곁, 없으면 기본 설치 자리. 못 찾으면 None.
    PATH 의 맨 `bash` 는 쓰지 않는다 — PowerShell 에서 띄운 Copilot 의 PATH 에서는 WSL 런처가 잡힌다."""
    if os.name != 'nt':
        return shutil.which('sh')
    git = shutil.which('git')
    if git:
        for d in pathlib.Path(git).resolve().parents:
            bash = d / 'bin' / 'bash.exe'
            if bash.is_file():
                return str(bash)
    bash = pathlib.Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'Git' / 'bin' / 'bash.exe'
    return str(bash) if bash.is_file() else None


def gate_bypass(command, cwd):
    """세션 저장소의 게이트 물음 껍데기 — 그 답을 (결정, 까닭)으로. 껍데기 · 신뢰 · bash 가 없으면 (None, '')."""
    # 입력에 세션 자리를 안 싣는다 — 껍데기는 입력 글 전체에서 글자를 찾아, 자리 이름의 `git` 이 git 아닌 명령을 묻게 한다
    payload = json.dumps({'hook_event_name': 'PreToolUse', 'tool_name': SHELL_DIALECT_TOOL,
                          'tool_input': {'command': command}}, ensure_ascii=False)
    if GATE_NEEDLE not in payload:
        return None, ''
    found = project_gate(cwd)
    if not found or not trusted(found[0]):
        return None, ''
    bash = git_bash()
    if not bash:
        return None, ''
    root, script = found
    p = subprocess.run([bash, str(script)], input=payload, capture_output=True, text=True, encoding='utf-8',
                       cwd=str(root), env=dict(os.environ, CLAUDE_PROJECT_DIR=str(root)), timeout=GATE_TIMEOUT,
                       check=False)
    return decision_of(p.stdout)


def drm_read(name, args, cwd):
    """감긴 파일을 열려는 셸 · 읽기 — agy 어댑터의 판정(`drm_guide`)에 agy 꼴로 넘기고 그 막기를 받는다."""
    agy = load('agy_hooks', AGY_ADAPTER)
    if name == SHELL_TOOL:
        call = {'name': agy.SHELL_TOOLS[0], 'args': {agy.SHELL_TEXT_KEY: args.get(COMMAND_KEY), agy.SHELL_CWD_KEY: cwd}}
    else:
        call = {'name': agy.VIEW_TOOLS[0], 'args': {agy.VIEW_PATH_KEY: args.get(PATH_KEY)}}
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        agy.drm_guide({'toolCall': call, 'workspacePaths': [cwd]})
    o = json.loads(out.getvalue()) if out.getvalue().strip() else {}
    if not isinstance(o, dict) or o.get('decision') != 'deny':
        return None, ''
    return 'deny', str(o.get('reason') or '')


# ── 훅 셋 ────────────────────────────────────────────────────────────────────────
def pre_tool(data):
    """preToolUse — 셸은 셋(셸 실수 문 · 게이트 물음 · DRM 길잡이), 읽기는 DRM 길잡이. 묻기 · 막기가 있으면 한 덩이."""
    name, args = tool_call(data)
    if not isinstance(args, dict):
        return ''
    cwd = session_cwd(data)
    verdicts = []
    if name == SHELL_TOOL:
        command = args.get(COMMAND_KEY)
        if not isinstance(command, str) or not command:
            return ''
        verdicts.append(guarded('shell-slip', shell_slip, command))
        verdicts.append(guarded('gate-bypass-ask', gate_bypass, command, cwd))
        verdicts.append(guarded('drm-guide', drm_read, name, args, cwd))
    elif name == VIEW_TOOL or (name == EDITOR_TOOL and args.get(COMMAND_KEY) == EDITOR_VIEW):
        verdicts.append(guarded('drm-guide', drm_read, VIEW_TOOL, args, cwd))
    said = [(d, r) for d, r in verdicts if d in DECISION_RANK]
    if not said:
        return ''
    decision = max((d for d, _ in said), key=DECISION_RANK.get)
    reason = '\n\n'.join(r for _, r in said if r)
    return json.dumps({'permissionDecision': decision, 'permissionDecisionReason': reason}, ensure_ascii=False)


def post_tool(data):
    """postToolUse — 고친 PowerShell 파일에 BOM. 아무것도 안 낸다."""
    name, args = tool_call(data)
    cwd = session_cwd(data)
    bom = load('codex_safety_hooks', BOM_BODY)
    if name == PATCH_TOOL and isinstance(args, str):
        paths = list(bom.patch_paths(args))
    elif isinstance(args, dict) and (name in PATH_WRITE_TOOLS
                                     or (name == EDITOR_TOOL and args.get(COMMAND_KEY) in EDITOR_WRITES)):
        paths = [args.get(PATH_KEY)]
    else:
        paths = []
    for p in paths:
        if isinstance(p, str) and p:
            bom.add_bom(p, cwd)
    return ''


def prompt(data):
    """userPromptSubmitted — 사람의 글에 감긴 파일의 경로가 있으면 DRM 길잡이의 덧말을 그 턴에 붙인다."""
    payload = {'hook_event_name': 'UserPromptSubmit', 'prompt': str(data.get('prompt') or ''),
               'cwd': session_cwd(data), 'session_id': str(data.get('sessionId') or '')}
    try:
        o = json.loads(run_body(load('drm_guide', DRM_BODY), payload) or '{}')
    except ValueError:
        return ''
    inner = o.get('hookSpecificOutput') if isinstance(o, dict) else None
    context = inner.get('additionalContext') if isinstance(inner, dict) else None
    return json.dumps({'additionalContext': context}, ensure_ascii=False) if context else ''


HOOKS = {'pre-tool': pre_tool, 'post-tool': post_tool, 'prompt': prompt}   # 갈래 → 손


# ── 배선 ─────────────────────────────────────────────────────────────────────────
def cmd_word(path):
    """경로 → `cmd.exe` 가 따옴표 없이 한 낱말로 읽는 꼴 — 폴더만 8.3 짧은 이름으로 바꾸고 파일 이름은 둔다(우리 항목의
    표지가 파일 이름이다). 못 지으면 None."""
    p = pathlib.Path(path)

    def plain(w):
        return not any(c in CMD_UNSAFE for c in w)
    if plain(str(p)):
        return str(p)
    short = load('agy_hooks', AGY_ADAPTER).short_path(p.parent)
    word = str(pathlib.PureWindowsPath(short) / p.name) if short else ''
    return word if word and plain(word) else None


def launcher():
    """(`cmd.exe` 자리, 해석기 낱말, 이 파일 낱말) — 못 지으면 까닭 글."""
    if os.name != 'nt':
        return '윈도에서만 심는다 — 등록이 cmd.exe 로 실패를 0 으로 바꾸는 꼴이다'
    cmd = pathlib.Path(os.environ.get('SystemRoot') or r'C:\Windows') / 'System32' / 'cmd.exe'
    if not cmd.is_file():
        return '%s 가 없다' % cmd
    py, script = cmd_word(sys.executable), cmd_word(pathlib.Path(__file__).resolve())
    for word, src in ((py, sys.executable), (script, pathlib.Path(__file__).resolve())):
        if word is None:
            return '%s 에 cmd.exe 가 가르는 글자가 있고 짧은 이름도 없다 — 따옴표 없이 부를 꼴을 못 지어 안 심는다' % src
    return str(cmd), py, script


def wanted(cmd, py, script):
    """이벤트 → 우리 항목. 해석기 · 이 파일이 있을 때만 띄우고, 0 이 아닌 끝은 0 으로 바꾼다(머리말 「재다 져도 막지 않는다」)."""
    out = {}
    for event, (mode, tools) in EVENTS.items():
        entry = {'type': 'command', 'exec': cmd,
                 'args': ['/d', '/c', 'if', 'exist', script, 'if', 'exist', py, py, '-X', 'utf8', script, mode,
                          '||', 'exit', '0'],
                 'timeoutSec': HOOK_TIMEOUT}
        if tools:
            entry['matcher'] = '|'.join(tools)
        out[event] = entry
    return out


def is_ours(item):
    args = item.get('args') if isinstance(item, dict) else None
    return isinstance(args, list) and any(isinstance(a, str) and re.split(r'[\\/]', a)[-1].lower() == SCRIPT_NAME
                                          for a in args)


def strip_ours(hooks):
    """`hooks` 표에서 우리 항목을 걷는다 — 걷어서 빈 이벤트는 지우고, 원래 빈 것은 둔다."""
    out = {}
    for event, items in hooks.items():
        if isinstance(items, list):
            kept = [x for x in items if not is_ours(x)]
            if kept or len(kept) == len(items):
                out[event] = kept
        else:
            out[event] = items
    return out


def merge(table, entries):
    """(새 표, 바뀌었나). 우리 항목은 있던 자리에서 지금 꼴로, 없으면 이벤트 끝에. 남의 항목 · 열쇠는 그대로."""
    old = table.get(HOOKS_KEY) or {}
    others = strip_ours({e: v for e, v in old.items() if e not in entries})   # 지금 판이 안 드는 이벤트의 우리 항목
    hooks = {}
    for event, items in old.items():
        if event in entries:
            items = items or []
            at = next((i for i, x in enumerate(items) if is_ours(x)), len(items))
            kept = [x for x in items if not is_ours(x)]
            kept.insert(sum(1 for x in items[:at] if not is_ours(x)), entries[event])
            hooks[event] = kept
        elif event in others:
            hooks[event] = others[event]
    for event, entry in entries.items():
        hooks.setdefault(event, [entry])
    out = dict(table)
    out[HOOKS_KEY] = hooks
    return out, out != table


def without_ours(table):
    """(새 표, 바뀌었나) — 우리 항목만 걷는다. 걷어서 `hooks` 가 비면 그 열쇠도 지운다."""
    hooks = table.get(HOOKS_KEY)
    if not isinstance(hooks, dict):
        return table, False
    left = strip_ours(hooks)
    out = dict(table)
    if left or not hooks:
        out[HOOKS_KEY] = left
    else:
        del out[HOOKS_KEY]
    return out, out != table


def read_config(config):
    """(설정 표, 쓰는 꼴, 까닭) — 파일이 없으면 빈 표. 못 읽으면 표는 None 이고 까닭이 선다.
    쓰는 꼴 = (BOM, 줄끝, 들여쓰기, 끝 줄바꿈) — 고쳐 쓸 때 그대로 잇는다."""
    if not config.exists():
        return {}, (False, '\n', DEFAULT_INDENT, True), ''
    try:
        raw = config.read_bytes().decode('utf-8')
    except (OSError, UnicodeDecodeError) as e:
        return None, None, '%s 를 못 읽는다(%s) — 안 건드린다' % (config, type(e).__name__)
    bom = raw.startswith('\ufeff')
    body = raw[1:] if bom else raw
    try:
        current = json.loads(body)
    except ValueError as e:
        return None, None, '%s 를 JSON 으로 못 읽는다(%s) — 안 건드린다' % (config, type(e).__name__)
    if not isinstance(current, dict):
        return None, None, '%s 의 맨 위가 이름 → 값의 표가 아니다 — 안 건드린다' % config
    hooks = current.get(HOOKS_KEY)
    if hooks is not None and not isinstance(hooks, dict):
        return None, None, '%s 의 %s 가 이벤트 → 목록의 표가 아니다 — 안 건드린다' % (config, HOOKS_KEY)
    for event in EVENTS:
        if isinstance(hooks, dict) and hooks.get(event) is not None and not isinstance(hooks[event], list):
            return None, None, '%s 의 %s.%s 가 목록이 아니다 — 안 건드린다' % (config, HOOKS_KEY, event)
    m = re.search(r'\n([ \t]+)\S', body)
    fmt = (bom, '\r\n' if '\r\n' in body else '\n', m.group(1) if m else None, body.endswith('\n'))
    return current, fmt, ''


def dump(table, fmt):
    bom, newline, indent, trailing = fmt
    text = json.dumps(table, ensure_ascii=False, indent=indent) + ('\n' if trailing else '')
    return ('\ufeff' if bom else '') + text.replace('\n', newline)


def save(config, table, fmt, changed):
    """바뀌었으면 원본을 곁에 떠 두고 옆 파일에 써서 바꿔 단다 — 출력 계약의 CHANGED · BACKUP 줄을 낸다."""
    if not changed:
        print('CHANGED=0')
        return 0
    merger = load('codex_hook_install', MERGER_FILE)
    if config.exists():
        print('BACKUP=' + str(merger.replace_with_backup(config, dump(table, fmt), BACKUP_SUFFIX)))
    else:
        merger.write_atomic(config, dump(table, fmt))
    print('CHANGED=1')
    return 0


def install(config):
    made = launcher()
    if isinstance(made, str):
        print('ERROR=' + made)
        return 1
    config = pathlib.Path(config).expanduser()
    current, fmt, why = read_config(config)
    if current is None:
        print('ERROR=' + why)
        return 1
    merged, changed = merge(current, wanted(*made))
    return save(config, merged, fmt, changed)


def remove(config):
    """우리 항목만 걷는다 — 파일이 없거나 우리 항목이 없으면 안 쓴다. 출력 계약은 install 과 같다."""
    config = pathlib.Path(config).expanduser()
    current, fmt, why = read_config(config)
    if current is None:
        print('ERROR=' + why)
        return 1
    left, changed = without_ours(current)
    return save(config, left, fmt, changed)


def main():
    argv = sys.argv[1:]
    mode = argv[0] if argv else ''
    if mode in ('install', 'remove'):
        if len(argv) != 3 or argv[1] != '--config':
            print('ERROR=%s 에는 --config <설정 파일> 이 든다' % mode)
            return 1
        try:
            return (install if mode == 'install' else remove)(argv[2])
        except Exception as e:  # noqa: BLE001 — 설치기는 이 한 줄로 까닭을 받는다
            print('ERROR=%s: %s' % (type(e).__name__, e))
            return 1
    # 훅 갈래 — 무엇이 져도 0 이고, 표준 출력에는 한 덩이 JSON 이거나 아무것도 없다(머리말 「재다 져도 막지 않는다」)
    try:
        if mode not in HOOKS:
            sys.stderr.write('Copilot 훅 — 모르는 갈래(%s) · 아무것도 안 한다\n' % mode)
            return 0
        data = json.loads(sys.stdin.read() or '{}')
        out = HOOKS[mode](data) if isinstance(data, dict) else ''
    except BaseException as e:  # noqa: BLE001 — 몸통을 한 프로세스에 불러 그쪽의 종료까지 받는다
        sys.stderr.write('Copilot 훅 %s — 재다 졌다(%s)\n' % (mode, type(e).__name__))
        out = ''
    if out:
        sys.stdout.write(out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
