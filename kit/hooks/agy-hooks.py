"""agy(Antigravity CLI) 훅 어댑터 — DRM 길잡이 · PowerShell UTF-8 BOM 보정 · 컨텍스트 알림을 agy 의 꼴로 건넨다 (결정 0099 · #173).

    python -X utf8 agy-hooks.py drm-guide     < PreToolUse 입력     (matcher `view_file` · `run_command`)
    python -X utf8 agy-hooks.py utf8-bom      < PostToolUse 입력    (matcher 쓰기 도구 셋)
    python -X utf8 agy-hooks.py context-alert < PreInvocation 입력  (matcher 없음)
    python -X utf8 agy-hooks.py install --config ~/.gemini/config/hooks.json
    python -X utf8 agy-hooks.py remove  --config ~/.gemini/config/hooks.json

**왜 어댑터인가.** 몸통은 Claude 훅 꼴(`tool_name` · `tool_input`)을 받는다. agy 는 `toolCall.name` · `toolCall.args` 로 주고
경로 열쇠도 다르다(`AbsolutePath` · `TargetFile` · 셸은 `CommandLine` · `Cwd`). 판정은 몸통의 것을 불러 쓰고 여기서는 꼴만
바꾼다 — 같은 판정을 두 벌 두면 한쪽만 낡는다. 입력 꼴은 agy 문서 「Hooks」의 것이다(<https://antigravity.google/docs/hooks>).

**홈 훅 가운데 셋을 건다.** 그림 문 · Bash 겹역슬래시 보정 · 웹 다시 찾기는 Claude 쪽 사정(그림 크기 비용 · Git Bash 가
접는 역슬래시 · WebFetch 실패)에서 나온 훅이라 agy 에서는 막을 사고가 없다(결정 0083 실측 · 0099). 셸 실수 문은 몸통이
Claude 의 Bash · PowerShell 도구 입력(`tool_input.command`)만 읽어 agy 셸 꼴(`CommandLine`)로는 안 건다.

**모델에게 말이 닿는 자리는 하나다.** agy 의 PreToolUse 는 결정(`decision`)과 까닭(`reason`)만 받고, PostToolUse 도 모델에
말을 붙일 수 없다. 모델에 닿는 것은 PreInvocation 의 `injectSteps` 다 — 모델을 부를 때마다 돌고, 거기 낸 `ephemeralMessage`
를 모델이 읽는다(#173 실측). 사람의 글을 받는 훅은 없다.

**DRM 길잡이는 읽기 전에 막는다.** 감긴 파일을 읽으려는 그 도구 호출을 잡는 자리가 PreToolUse 다 — 막고 까닭에 스킬로 가는
길을 싣는다. 감긴 파일은 열어도 글자가 안 나오니 막아서 잃는 것이 없다. 읽는 길은 둘이다:
  · `view_file` — 경로 칸 하나
  · `run_command` — 명령 글. 그냥 「읽어 줘」라고 하면 모델은 셸로 먼저 간다(claude-config #137 실측). 명령의 뜻은 짐작하지
    않는다 — 글에서 경로 꼴의 낱말을 뽑아(몸통의 `candidates` 에 따옴표 안 · 맨 낱말을 더한다 — `shell_words`) 그 가운데
    **실제로 있는 감긴 파일**이 있으면 막는다. 명령이 그 파일로 무엇을 하든 같다. 명령어 이름 목록으로 가르지 않는다 — 목록은
    열려 있어 늘 빠진다. 상대 낱말은 그 호출의 일하는 자리(`Cwd`)에서 푼다.
  ⚠ **읽는 손은 지난다** — 그 명령도 감긴 파일의 경로를 적는다. 낱말 가운데 하나가 설치된 스킬 사본 어느 것의
    `read-drm.ps1` **과 같은 파일**이면 둔다(`calls_reader`). 이름이 아니라 파일로 가른다 — 같은 이름의 다른 파일은 못 지난다.
  ⚠ 글에 경로가 안 적힌 읽기는 못 본다 — 와일드카드(`*.docx`) · 변수로 이은 경로 · 먼저 써 둔 스크립트 속 경로 · 명령 안
    `cd` 뒤의 상대 낱말.
  ⚠ 러너가 주는 `--dangerously-skip-permissions` 아래에서도 막는다 — 그 플래그는 권한 묻기만 건너뛰고 PreToolUse 훅의
    deny 는 그대로 선다(#137 실측).
⚠ **둘 것에는 아무것도 안 낸다** — `"allow"` 는 agy 의 권한 묻기를 건너뛰게 한다. 우리 훅이 사람의 권한 설정을 넓히면 안
   된다. 빈 출력이면 agy 는 묻지도 막지도 않고 도구를 돌린다(claude-config #126 실측).
⚠ **재다 져도 막지 않는다** — 몸통과 같은 규율이다. 진 사실은 stderr 한 줄로 남긴다.

**컨텍스트 알림은 모델을 부르기 전에 붙인다.** 문턱 · 한 번씩 · 다시 무장 · 창이 작아 알리지 않는 판정은 몸통
(`context-alert.py` 의 `step`)이 들고, 여기서는 사용량과 창을 재서 알릴 한 줄을 `injectSteps` 에 싣는다.
  · 사용량 — 훅 입력의 `transcriptPath` 가 이름 대는 기록에서 `input_tokens` 가 선 마지막 `PLANNER_RESPONSE` 줄의
    `input_tokens` + `cache_read_tokens`. 1.3.3 CLI 는 `<대화 폴더>/.system_generated/logs/transcript_full.jsonl` 을 대고
    (문서는 곁의 `transcript.jsonl`), 두 기록의 응답 줄 토큰 수는 같다(#173 실측) — 그래서 이름을 고르지 않고 대는 파일을
    읽는다. 캐시가 붙은 응답은 `input_tokens` 가 캐시 몫만큼 줄고 둘의 합이 앞 응답의 합에서 이어 는다 — 캐시 읽은 몫은
    `input_tokens` 밖에 있다(#173 실측)
  · 창 — agy 는 창을 어디에도 안 적는다(기록 · 설정 · 훅 입력 · `agy models`). 그래서 자리 값(`PAISETUP_SITE` — 설치기가
    심는다)으로 가른다: 사외는 무료 판이라 200k, 사내는 회사 판이라 1M(사용자가 정한 값 · 모델별 표는 안 둔다). 자리를
    모르면 아무것도 안 붙인다. 값을 읽는 차례는 갈 곳 표의 손(`tool-homes.py` 의 `user_value`)을 불러 쓴다 — 사용자 값을
    먼저 읽어, 설치 전에 뜬 창에서 연 agy 도 자리를 안다
  · 한 번씩 — 모델을 부를 때마다 돌지만 몸통의 상태 파일이 대화(`conversationId`)마다 알린 문턱을 쥐어 같은 문턱에 두 번
    안 붙인다. 첫 부르기(`invocationNum` 0)도 잰다 — 그 번호는 사람의 글마다 0 부터 다시 세고(#173 실측), 도구 없이 한 번에
    답하는 턴은 0 하나뿐이다. 새 대화의 첫 부르기는 기록에 응답이 아직 없어 저절로 말이 없다
  ⚠ 재다 지면 아무 말 없이 빈 표(`{}`)를 낸다 — 모델을 부를 때마다 도는 훅이라 실패 줄은 매번 되풀이된다(몸통과 같은 규율).
  ⚠ 안티그래비티 앱의 기록(`~/.gemini/antigravity/brain/`)에는 응답 줄에 토큰 수가 없다 — 거기서 돌면 늘 말이 없다.

**배선도 이 파일이 든다** — `install` 이 agy 전역 훅 자리(`~/.gemini/config/hooks.json`)에 우리 이름(`paisetup-…`)의 항목만
얹는다. 그 파일은 「이름 → 설정」의 표라 남의 항목과 섞이지 않는다. 명령에는 이 파일의 절대 경로를 슬래시로 박고, 윈도에서는
따옴표를 안 친다(`script_word` — 까닭은 거기).
⚠ 사람이 우리 항목을 `"enabled": false` 로 꺼 두었으면 그 뜻을 잇는다.
`remove` 는 우리 이름의 항목만 걷는다(agy 를 고르지 않은 설치) — 사람이 꺼 둔 우리 항목도 우리 것이라 걷고, 파일이 없으면
짓지 않고, 다 걷혀 빈 표가 남아도 파일은 둔다.
⚠ 못 읽는 파일(JSON 이 아님 · 맨 위가 표가 아님)은 안 건드리고 까닭을 낸다. 고쳐 쓰기 전에 원본을 곁에 떠 둔다 — 떠 두는
   손은 Codex 병합기의 `backup_copy` 를 불러 쓴다(곁에 같이 실린다). 이름의 시각이 초 단위라 같은 초의 두 판이 한 이름을
   고르는데, 그 손은 있으면 다음 번호로 가 앞 판의 원본을 안 덮는다. 이름 머리(`BACKUP_SUFFIX`)만 우리 것이다.

출력 계약(`install` · `remove`) — 한 줄에 하나:
  CHANGED=0|1 · BACKUP=<경로>(고쳐 쓴 판에만) · ERROR=<까닭>(아무것도 안 썼다)
"""
import argparse
import importlib.util
import json
import os
import pathlib
import re
import shlex
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
VIEW_TOOLS = ('view_file',)
SHELL_TOOLS = ('run_command',)
GUIDE_TOOLS = VIEW_TOOLS + SHELL_TOOLS   # DRM 길잡이가 지키는 읽는 길 — matcher 가 이것이다
WRITE_TOOLS = ('write_to_file', 'replace_file_content', 'multi_replace_file_content')
VIEW_PATH_KEY = 'AbsolutePath'
SHELL_TEXT_KEY = 'CommandLine'     # run_command 의 명령 글 · 일하는 자리 — agy 1.3.3 실측(#137)
SHELL_CWD_KEY = 'Cwd'
WRITE_PATH_KEY = 'TargetFile'
HOOK_TIMEOUT = 10                  # 초 — agy 의 기본은 30. 둘 다 파일 머리만 읽는다
NAME_PREFIX = 'paisetup-'          # 우리 항목의 이름 머리 — 이 머리가 아닌 이름은 안 건드린다
BACKUP_SUFFIX = '.before-paisetup-'
MERGER_FILE = 'codex-hook-install.py'   # 원본을 떠 두는 손(`backup_copy`)의 진본 — 이 파일 곁에 같이 실린다
ENABLED_KEY = 'enabled'
CONTEXT_EVENT = 'PreInvocation'
CONTEXT_BODY = 'context-alert.py'   # 문턱 판정의 진본(`step`)
HOMES_HAND = 'tool-homes.py'        # 사용자 값을 읽는 차례의 진본(`user_value`) — 둘 다 이 파일 곁에 같이 실린다
SITE_VAR = 'PAISETUP_SITE'
# 자리 → agy 의 창(토큰) — 사용자가 정한 값이다(#173). 사외는 무료 판, 사내는 회사 판. 표에 없는 자리는 알리지 않는다
SITE_WINDOW = {'outside': 200000, 'inside': 1000000}
PLANNER = 'PLANNER_RESPONSE'
PLANNER_USED_KEYS = ('input_tokens', 'cache_read_tokens')   # 둘의 합이 모델이 본 입력이다(머리말 「컨텍스트 알림」)
# 명령 글의 낱말 — 따옴표 안은 통째로(빈칸 든 이름 · 겹따옴표 안의 홑따옴표도 따로), 그 밖은 셸이 가르는 글자 사이의 맨 낱말.
# 몸통의 `candidates` 는 절대 경로 꼴만 뽑아 셸의 상대 낱말(`Expand-Archive 보고서.docx`)을 못 본다
QUOTED_SPANS = (re.compile(r'"([^"\r\n]+)"'), re.compile(r"'([^'\r\n]+)'"))
BARE_WORD = re.compile(r'[^\s"\'`|&;<>(){}\[\],=]+')


# ── 꼴 바꾸기 ────────────────────────────────────────────────────────────────────
def load(name, filename):
    """곁의 몸통을 모듈로 부른다 — 이름에 `-` 가 들어 import 문으로는 못 부른다."""
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tool_call(data):
    """(짧은 도구 이름, 인자 표). 이름에 묶음 머리(`default_api:` · `functions.`)가 붙어도 끝 이름으로 본다."""
    call = data.get('toolCall') if isinstance(data.get('toolCall'), dict) else {}
    args = call.get('args')
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = {}
    name = str(call.get('name') or '').split(':')[-1].split('.')[-1]
    return name, (args if isinstance(args, dict) else {})


def base_dir(data):
    """상대 경로를 풀 자리 — 첫 작업 폴더. 없으면 지금 자리."""
    ws = data.get('workspacePaths')
    if isinstance(ws, list) and ws and isinstance(ws[0], str) and ws[0]:
        return ws[0]
    return os.getcwd()


def shell_words(text):
    """명령 글 → 경로 후보 낱말. 따옴표 안은 통째로, 그 밖은 맨 낱말로 — 뜻은 안 가린다(가르는 것은 파일의 상태다)."""
    return [w for rx in QUOTED_SPANS for w in rx.findall(text)] + BARE_WORD.findall(text)


def calls_reader(drm, words, cwd):
    """명령이 읽는 손을 부르나 — 낱말 가운데 설치된 스킬 사본 어느 것의 `read-drm.ps1` 과 **같은 파일**이 있나. 길잡이는
    첫째 사본의 손을 내주지만, 모델은 제 홈의 스킬 본문을 읽고 그 사본의 손을 부른다(agy 홈 `~/.gemini/config/skills`)."""
    readers = [os.path.join(d, drm.READER) for d in drm.skill_dirs()]
    for w in words:
        p = drm.resolve(w, cwd)
        for reader in readers:
            try:
                if os.path.isfile(p) and os.path.samefile(p, reader):
                    return True
            except OSError:
                continue
    return False


# ── 훅 셋 ────────────────────────────────────────────────────────────────────────
def drm_guide(data):
    name, args = tool_call(data)
    if name in VIEW_TOOLS:
        text, cwd = str(args.get(VIEW_PATH_KEY) or ''), base_dir(data)
    elif name in SHELL_TOOLS:
        text, cwd = str(args.get(SHELL_TEXT_KEY) or ''), str(args.get(SHELL_CWD_KEY) or '') or base_dir(data)
    else:
        return
    if not text:
        return
    drm = load('drm_guide', 'drm-guide.py')
    sdir = drm.skill_dir()
    alt, ext_re = drm.ext_pattern(drm.handled_exts(sdir) if sdir else set())
    if name in VIEW_TOOLS:
        toks = [text]
    else:
        words = shell_words(text)
        if calls_reader(drm, words, cwd):
            return
        toks = drm.candidates(text, alt) + words
    hits = drm.wrapped_paths(toks, ext_re, cwd)
    if not hits:
        return
    scratch = os.path.expanduser(str(data.get('artifactDirectoryPath') or '')) or tempfile.gettempdir()
    reason = drm.message('PreToolUse', hits, [], sdir, os.path.join(scratch, drm.OUT_SUBDIR))
    sys.stdout.write(json.dumps({'decision': 'deny', 'reason': reason}, ensure_ascii=False))


def utf8_bom(data):
    name, args = tool_call(data)
    raw = str(args.get(WRITE_PATH_KEY) or '')
    if name in WRITE_TOOLS and raw:
        load('codex_safety_hooks', 'codex-safety-hooks.py').add_bom(raw, base_dir(data))
    sys.stdout.write('{}')   # agy 문서의 PostToolUse 출력 — 빈 표


def planner_used(ca, path):
    """agy 기록 → 마지막 응답이 본 입력 토큰 수 · 못 찾으면 None. 꼬리를 거꾸로 읽는 손은 몸통의 것이다."""
    for raw in ca.tail_lines(path):
        if PLANNER.encode() not in raw:
            continue
        try:
            o = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(o, dict) or o.get('type') != PLANNER or not isinstance(o.get('input_tokens'), int):
            continue
        return sum(int(o.get(k) or 0) for k in PLANNER_USED_KEYS)
    return None


def context_line(data):
    """PreInvocation 입력 → 알릴 한 줄 · 없으면 None(머리말 「컨텍스트 알림」)."""
    tp = os.path.expanduser(str(data.get('transcriptPath') or ''))
    if not tp or not os.path.isfile(tp):
        return None
    ca = load('context_alert', CONTEXT_BODY)
    used = planner_used(ca, tp)
    if used is None:
        return None
    window = SITE_WINDOW.get(load('tool_homes', HOMES_HAND).user_value(SITE_VAR).strip().lower())
    if window is None:
        return None
    return ca.step(data.get('conversationId'), used, window)


def context_alert(data):
    try:
        line = context_line(data)
    except Exception:  # noqa: BLE001 — 재다 지면 조용히 빈 표를 낸다(머리말 「컨텍스트 알림」 ⚠)
        line = None
    sys.stdout.write(json.dumps({'injectSteps': [{'ephemeralMessage': line}]}, ensure_ascii=False) if line else '{}')


HOOKS = {'drm-guide': drm_guide, 'utf8-bom': utf8_bom, 'context-alert': context_alert}   # 훅 갈래 → 손


# ── 배선 ─────────────────────────────────────────────────────────────────────────
def short_path(path):
    """윈도의 8.3 짧은 이름 — 못 얻으면 None. 짧은 이름이 꺼진 볼륨에서는 긴 이름이 그대로 돌아온다."""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(32768)
        n = ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, len(buf))
    except (AttributeError, OSError):
        return None
    return buf.value if 0 < n < len(buf) else None


def script_word():
    """명령에 박을 이 파일의 자리 — 셸이 한 낱말로 읽는 꼴. 못 지으면 None.

    ⚠ **윈도에서는 따옴표를 안 친다.** agy 는 윈도에서 훅 명령을 cmd.exe 로 돌리면서 명령 속 큰따옴표를 `\\"` 로 감싸
      넘긴다(Go 의 인자 이스케이프 · claude-config #126 실측). cmd 는 그 역슬래시를 모르고 python 은 따옴표를 글자로 받아,
      따옴표까지 붙은 경로를 못 찾고 2 로 진다 — agy 는 0 이 아닌 훅을 도구 오류로 바꿔 `view_file` 이 다 막히고 쓰기는
      「실패」로 보고된다. 그래서 cmd 가 가르는 글자(빈칸 · `&|<>^%"`)가 든 경로는 8.3 짧은 이름으로 그 글자를 없애고,
      그것도 안 되면 None 이다 — 깨진 훅을 심느니 안 심고 까닭을 낸다.
    """
    path = pathlib.Path(__file__).resolve()
    word = path.as_posix()
    if os.name != 'nt':
        return shlex.quote(word)

    def plain(w):
        return not any(c.isspace() or c in '&|<>^%"' for c in w)
    if plain(word):
        return word
    short = short_path(path)
    if short and plain(short):
        return pathlib.PureWindowsPath(short).as_posix()
    return None


def command(mode):
    return 'python -X utf8 %s %s' % (script_word(), mode)


def wanted():
    """우리 항목 — 이름 → agy 훅 설정. matcher 는 정규식이라 `^…$` 로 묶어 이름이 닮은 도구에 안 걸리게 한다.
    PreInvocation 은 matcher 를 안 받아 처리기를 이벤트 밑에 바로 둔다(agy 문서 「Hooks」의 꼴)."""
    def handler(mode):
        return {'type': 'command', 'command': command(mode), 'timeout': HOOK_TIMEOUT}

    def entry(event, tools, mode):
        return {event: [{'matcher': '^(%s)$' % '|'.join(tools), 'hooks': [handler(mode)]}]}
    return {NAME_PREFIX + 'drm-guide': entry('PreToolUse', GUIDE_TOOLS, 'drm-guide'),
            NAME_PREFIX + 'utf8-bom': entry('PostToolUse', WRITE_TOOLS, 'utf8-bom'),
            NAME_PREFIX + 'context-alert': {CONTEXT_EVENT: [handler('context-alert')]}}


def merge(current):
    """(새 표, 바뀌었나). 남의 이름은 그대로 · 우리 이름은 지금 꼴로 · 사람이 끈 우리 항목은 꺼진 채로."""
    out = dict(current)
    for name, spec in wanted().items():
        old = current.get(name)
        new = dict(spec)
        if isinstance(old, dict) and old.get(ENABLED_KEY) is False:
            new = {ENABLED_KEY: False, **new}
        out[name] = new
    return out, out != current


def write_atomic(path, text):
    """옆 파일에 쓰고 옮긴다. 심볼릭 링크면 가리키는 파일을 간다."""
    path = path.resolve() if path.is_symlink() else path
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, part = tempfile.mkstemp(prefix=path.name + '.', suffix='.part', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        if path.exists():
            shutil.copymode(path, part)
        os.replace(part, path)
    except BaseException:
        if os.path.exists(part):
            os.remove(part)
        raise


def without_ours(current):
    """(새 표, 바뀌었나) — 우리 이름(`paisetup-…`)의 항목만 걷는다. 사람이 꺼 둔 우리 항목도 우리 것이라 걷는다."""
    out = dict((k, v) for k, v in current.items() if not k.startswith(NAME_PREFIX))
    return out, out != current


def read_config(config):
    """(설정 표, 까닭) — 파일이 없으면 빈 표. 못 읽으면 표는 None 이고 까닭이 선다."""
    if not config.exists():
        return {}, ''
    try:
        current = json.loads(config.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as e:
        return None, '%s 를 JSON 으로 못 읽는다(%s) — 안 건드린다' % (config, type(e).__name__)
    if not isinstance(current, dict):
        return None, '%s 의 맨 위가 이름 → 설정의 표가 아니다 — 안 건드린다' % config
    return current, ''


def remove(config):
    """우리 항목만 걷는다 — 파일이 없거나 우리 항목이 없으면 안 쓴다. 출력 계약은 install 과 같다."""
    config = pathlib.Path(config).expanduser()
    current, why = read_config(config)
    if current is None:
        print('ERROR=' + why)
        return 1
    left, changed = without_ours(current)
    return save(config, left, changed)


def install(config):
    if script_word() is None:
        print('ERROR=이 파일의 자리(%s)에 셸이 가르는 글자가 있고 짧은 이름도 없다 — 따옴표 없이 부를 꼴을 못 지어 안 심는다'
              % pathlib.Path(__file__).resolve())
        return 1
    config = pathlib.Path(config).expanduser()
    current, why = read_config(config)
    if current is None:
        print('ERROR=' + why)
        return 1
    merged, changed = merge(current)
    return save(config, merged, changed)


def save(config, table, changed):
    """바뀌었으면 원본을 곁에 떠 두고 쓴다 — 출력 계약의 CHANGED · BACKUP 줄을 낸다."""
    if not changed:
        print('CHANGED=0')
        return 0
    if config.exists():
        merger = load('codex_hook_install', MERGER_FILE)
        print('BACKUP=' + str(merger.backup_copy(config, BACKUP_SUFFIX)))
    write_atomic(config, json.dumps(table, ensure_ascii=False, indent=2) + '\n')
    print('CHANGED=1')
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=tuple(HOOKS) + ('install', 'remove'))
    ap.add_argument('--config')
    args = ap.parse_args()
    if args.mode in ('install', 'remove'):
        if not args.config:
            ap.error('%s 에는 --config 가 든다' % args.mode)
        try:
            return (install if args.mode == 'install' else remove)(args.config)
        except Exception as e:  # noqa: BLE001 — 설치기는 이 한 줄로 까닭을 받는다
            print('ERROR=%s: %s' % (type(e).__name__, e))
            return 1
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    try:
        HOOKS[args.mode](data)
    except BaseException as e:  # noqa: BLE001 — 재다 져도 막지 않는다. 몸통을 한 프로세스에 불러 그쪽의 종료까지 받는다
        sys.stderr.write('agy 훅 %s — 재다 졌다(%s)\n' % (args.mode, type(e).__name__))
    return 0


if __name__ == '__main__':
    sys.exit(main())
