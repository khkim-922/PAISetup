"""agy(Antigravity CLI) 훅 어댑터 — DRM 길잡이와 PowerShell UTF-8 BOM 보정을 agy 의 꼴로 건넨다 (결정 0099).

    python -X utf8 agy-hooks.py drm-guide    < PreToolUse 입력   (matcher `view_file`)
    python -X utf8 agy-hooks.py utf8-bom     < PostToolUse 입력  (matcher 쓰기 도구 셋)
    python -X utf8 agy-hooks.py install --config ~/.gemini/config/hooks.json

**왜 어댑터인가.** 몸통은 Claude 훅 꼴(`tool_name` · `tool_input`)을 받는다. agy 는 `toolCall.name` · `toolCall.args` 로 주고
경로 열쇠도 다르다(`AbsolutePath` · `TargetFile`). 판정은 몸통의 것을 불러 쓰고 여기서는 꼴만 바꾼다 — 같은 판정을 두 벌
두면 한쪽만 낡는다. 입력 꼴은 agy 문서 「Hooks」의 것이다(<https://antigravity.google/docs/hooks>).

**홈 훅 다섯 가운데 둘만 건다.** 그림 문 · Bash 겹역슬래시 차단 · 웹 다시 찾기는 Claude 쪽 사정(그림 크기 비용 · Git Bash 가
접는 역슬래시 · WebFetch 실패)에서 나온 훅이라 agy 에서는 막을 사고가 없다(결정 0083 실측 · 0099).

**DRM 길잡이는 열기 전에 막는다.** agy 의 PreToolUse 는 결정(`decision`)과 까닭(`reason`)만 받는다 — 도구 뒤 훅은 모델에
말을 붙일 수 없고, 사람의 글을 받는 훅도 없다. 그래서 감긴 파일을 `view_file` 로 열려는 순간 막고 까닭에 스킬로 가는 길을
싣는다. 감긴 파일은 열어도 글자가 안 나오니 막아서 잃는 것이 없다.
⚠ **둘 것에는 아무것도 안 낸다** — `"allow"` 는 agy 의 권한 묻기를 건너뛰게 한다. 우리 훅이 사람의 권한 설정을 넓히면 안
   된다. 빈 출력을 agy 가 어떻게 받는지는 회사 PC 확인 목록이 잰다.
⚠ **재다 져도 막지 않는다** — 몸통과 같은 규율이다. 진 사실은 stderr 한 줄로 남긴다.

**배선도 이 파일이 든다** — `install` 이 agy 전역 훅 자리(`~/.gemini/config/hooks.json`)에 우리 이름(`paisetup-…`)의 항목만
얹는다. 그 파일은 「이름 → 설정」의 표라 남의 항목과 섞이지 않는다. 명령에는 이 파일의 절대 경로를 슬래시로 박는다 — agy 가
윈도에서 어느 셸로 훅을 돌리는지 문서에 없어, 어느 셸에서나 같은 뜻인 꼴을 쓴다.
⚠ 사람이 우리 항목을 `"enabled": false` 로 꺼 두었으면 그 뜻을 잇는다.
⚠ 못 읽는 파일(JSON 이 아님 · 맨 위가 표가 아님)은 안 건드리고 까닭을 낸다. 고쳐 쓰기 전에 원본을 곁에 떠 둔다.

출력 계약(`install`) — 한 줄에 하나:
  CHANGED=0|1 · BACKUP=<경로>(고쳐 쓴 판에만) · ERROR=<까닭>(아무것도 안 썼다)
"""
import argparse
import datetime
import importlib.util
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
VIEW_TOOLS = ('view_file',)
WRITE_TOOLS = ('write_to_file', 'replace_file_content', 'multi_replace_file_content')
VIEW_PATH_KEY = 'AbsolutePath'
WRITE_PATH_KEY = 'TargetFile'
HOOK_TIMEOUT = 10                  # 초 — agy 의 기본은 30. 둘 다 파일 머리만 읽는다
NAME_PREFIX = 'paisetup-'          # 우리 항목의 이름 머리 — 이 머리가 아닌 이름은 안 건드린다
BACKUP_SUFFIX = '.before-paisetup-'
ENABLED_KEY = 'enabled'


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


# ── 훅 둘 ────────────────────────────────────────────────────────────────────────
def drm_guide(data):
    name, args = tool_call(data)
    raw = str(args.get(VIEW_PATH_KEY) or '')
    if name not in VIEW_TOOLS or not raw:
        return
    drm = load('drm_guide', 'drm-guide.py')
    sdir = drm.skill_dir()
    _, ext_re = drm.ext_pattern(drm.handled_exts(sdir) if sdir else set())
    hits = drm.wrapped_paths([raw], ext_re, base_dir(data))
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


# ── 배선 ─────────────────────────────────────────────────────────────────────────
def command(mode):
    return 'python -X utf8 "%s" %s' % (pathlib.Path(__file__).resolve().as_posix(), mode)


def wanted():
    """우리 항목 — 이름 → agy 훅 설정. matcher 는 정규식이라 `^…$` 로 묶어 이름이 닮은 도구에 안 걸리게 한다."""
    def entry(event, tools, mode):
        return {event: [{'matcher': '^(%s)$' % '|'.join(tools),
                         'hooks': [{'type': 'command', 'command': command(mode), 'timeout': HOOK_TIMEOUT}]}]}
    return {NAME_PREFIX + 'drm-guide': entry('PreToolUse', VIEW_TOOLS, 'drm-guide'),
            NAME_PREFIX + 'utf8-bom': entry('PostToolUse', WRITE_TOOLS, 'utf8-bom')}


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


def install(config):
    config = pathlib.Path(config).expanduser()
    current = {}
    if config.exists():
        try:
            current = json.loads(config.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError) as e:
            print('ERROR=%s 를 JSON 으로 못 읽는다(%s) — 안 건드린다' % (config, type(e).__name__))
            return 1
        if not isinstance(current, dict):
            print('ERROR=%s 의 맨 위가 이름 → 설정의 표가 아니다 — 안 건드린다' % config)
            return 1
    merged, changed = merge(current)
    if not changed:
        print('CHANGED=0')
        return 0
    if config.exists():
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        backup = config.resolve().with_name(config.name + BACKUP_SUFFIX + stamp)
        shutil.copy2(config.resolve(), backup)
        print('BACKUP=' + str(backup))
    write_atomic(config, json.dumps(merged, ensure_ascii=False, indent=2) + '\n')
    print('CHANGED=1')
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=('drm-guide', 'utf8-bom', 'install'))
    ap.add_argument('--config')
    args = ap.parse_args()
    if args.mode == 'install':
        if not args.config:
            ap.error('install 에는 --config 가 든다')
        try:
            return install(args.config)
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
        (drm_guide if args.mode == 'drm-guide' else utf8_bom)(data)
    except BaseException as e:  # noqa: BLE001 — 재다 져도 막지 않는다. 몸통을 한 프로세스에 불러 그쪽의 종료까지 받는다
        sys.stderr.write('agy 훅 %s — 재다 졌다(%s)\n' % (args.mode, type(e).__name__))
    return 0


if __name__ == '__main__':
    sys.exit(main())
