"""Claude 에게 일을 맡기고 답을 파일로 받는다 — Codex · agy 가 맡기는 쪽일 때의 러너(결정 0098 · 0100).

**받는 Claude 는 기본이 읽기만 한다.** 쓸 수 있는 도구를 읽기 · 찾기 · 웹 읽기(`READ_TOOLS`)로 좁혀 띄운다 — 셸 · 쓰기
도구는 모델에게 아예 안 보인다. 그래서 받는 쪽이 다른 에이전트를 다시 띄울 길(셸)도 없다. 묻지 않는 권한 방식(`dontAsk`)이라
목록 밖 호출은 묻는 대신 거절되고, 거절이 하나라도 있으면 실패로 친다 — 답이 그 도구 없이 지어졌다는 뜻이다.
**`--write` 를 주면 고치기 레인이다** — 편집 도구 둘(`WRITE_TOOLS`)을 더 보이되 허락은 작업 자리 안(`./**`)만 건다. 그
밖에 쓰려는 호출은 거절돼 실패로 남는다(실측 Claude Code 2.1.296 · 2026-10-10: 자리 안 `Edit` 은 섰고 자리 밖 `Write`
는 `permission_denials` 로 거절됐다 · 그 띄우기를 자동 모드 분류기가 안 막았다). 셸은 그래도 안 연다 — 윈도에는 Claude
샌드박스가 없어 셸이 자리를 못 지킨다. 검사 돌리기는 맡긴 쪽이 한다. 자리를 잘못 물려받지 않게 `--cwd` 를 받아야만 띈다.
MCP 서버 · 슬래시 명령(스킬)은 끄고, 사용자 설정은 읽되 훅은 끈다 — 설정에는 자리 값(게이트웨이 주소 · 시간 한도 ·
웹 가져오기 검증 건너뛰기)이 살고, 훅은 맡긴 일과 무관한 일(세션 시작 동기화 등)을 한다.
빌린 자리 — 상류 `pgpt-one-click-connect` 의 `app/optional-skills/pgpt-delegate/scripts/Invoke-PgptAgent.ps1` Claude
작업자 갈래(커밋 65e981a · 2026-10-09). 플래그 다섯(`--strict-mcp-config` · `--disable-slash-commands` · `--permission-mode
dontAsk` · `--tools` · `--allowedTools`)과 결과를 가르는 법(`subtype` · `is_error` · `permission_denials` · 빈 답)을
빌렸다. 일부러 가른 셋 — 설정은 안 끄고 훅만 끈다(상류는 게이트웨이를 제가 알아 값을 직접 넣지만 이 러너는 자리를
모른다) · 대화를 남긴다(이어 묻기 — agent-envelope 1절 표) · 작업 규칙을 덧붙이지 않는다(봉투가 든다 — 결정 0095).
따라가는 법은 「일부러 갈랐다」 — 상류가 바뀌어도 이 러너는 따라가지 않는다.

**Codex 에서는 앞에서 기다린다** — 콘솔 있는 `python` 으로 부르면 끝날 때까지 돌아오지 않고, 끝나면 종료 코드로 갈래를
알린다. 답과 끝 줄은 `--out` 파일에 쓴다.

**프롬프트는 표준 입력으로 넘긴다** — 명령줄 길이 한도와 따옴표 해석을 안 탄다. npm 이 까는 실행 꼴(`.cmd` 셔틀)은
인자가 cmd.exe 를 거치므로, 셔틀이 부르는 것(꾸러미 `bin` 의 JS 나 실행 파일)을 바로 부른다.

맨 끝 줄 `[claude-bg] …` 이 갈래 · 걸린 시간 · 모델 · 쓴 도구 수 · 토큰 · 이어 묻기 값을 든다:
  0 답이 왔다 · 1 실패했다(거절된 도구 호출 · 러너가 멈춘 것 포함) · 2 한도 · 과부하 또는 빈 답 · 3 시간 초과 ·
  4 부르는 법이 틀렸다 · Claude 가 없다
**`--out` 을 받았으면 어느 갈래로 끝나든 답 파일과 끝 줄을 남긴다** — 인자가 틀렸어도, 러너가 멈췄어도 까닭을 적는다.
**이어 묻기 값은 대화 기록이 실제로 남았을 때만 싣는다** — 받는 Claude 가 제 홈에 못 쓰는 자리(맡긴 쪽의 샌드박스)에서
돌면 대화 id 는 나와도 기록이 없어 `--resume` 이 「No conversation found」로 진다(실측 2026-10-11 · Codex 샌드박스).
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback

CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
DEFAULT_TIMEOUT_SEC = 1800      # 기본 한도 — 짧은 일도 그대로 둔다(끝나는 대로 돌아온다)
POLL_SEC = 2                    # 끝났나 보는 간격
STDERR_TAIL_CHARS = 2000        # 실패 때 답 파일에 옮기는 stderr 꼬리
EXIT = {'ok': 0, 'failed': 1, 'denied': 1, 'quota': 2, 'empty': 2, 'timeout': 3}
FOOTER = '[claude-bg]'

READ_TOOLS = 'Read,Glob,Grep,WebFetch,WebSearch'   # 읽기 · 찾기 · 웹 읽기 — 셸 · 쓰기는 모델이 아예 못 본다
WRITE_TOOLS = ('Edit', 'Write')                   # 고치기 레인에 더 보이는 것 — 셸은 끝내 안 연다
WRITE_SCOPE = './**'                              # 허락은 작업 자리 안만 — 띄우는 자리(`--cwd`) 기준이다
CLAUDE_ARGS = ['-p', '--output-format', 'stream-json', '--verbose',
               '--setting-sources', 'user', '--settings', json.dumps({'disableAllHooks': True}),
               '--strict-mcp-config', '--disable-slash-commands', '--permission-mode', 'dontAsk']
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


def prompt_problem(path):
    """프롬프트 파일을 못 넘기는 까닭 — 없으면 None. 받는 Claude 는 표준 입력을 UTF-8 로 읽는다: PowerShell 5.1 의
    `Set-Content`(ANSI) · `Out-File`(UTF-16) 기본값으로 쓴 파일은 글자가 깨진 채 넘어가 답이 조용히 틀어진다."""
    try:
        with open(path, 'rb') as f:
            f.read().decode('utf-8')
    except OSError as e:
        return f'프롬프트 파일을 못 읽었다 — {e}'
    except UnicodeDecodeError:
        return f'프롬프트 파일이 UTF-8 이 아니다 — PowerShell 5.1 이면 `Set-Content -Encoding utf8` 로 쓴다: {path}'
    return None


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


def tool_args(write):
    """보일 도구와 미리 허락한 도구. 고치기 레인이면 편집 도구를 더하되 허락은 작업 자리 안으로 가둔다."""
    if not write:
        return ['--tools', READ_TOOLS, '--allowedTools', READ_TOOLS]
    shown = ','.join([READ_TOOLS, *WRITE_TOOLS])
    allowed = ','.join([READ_TOOLS, *(f'{t}({WRITE_SCOPE})' for t in WRITE_TOOLS)])
    return ['--tools', shown, '--allowedTools', allowed]


def argv(model, resume, write=False):
    """머리 뒤에 붙일 인자 — 프롬프트는 안 싣는다(표준 입력). 이어 물을 때도 고치기 레인이면 `--write` 를 다시 준다."""
    out = list(CLAUDE_ARGS) + tool_args(write)
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


def judge(events, rc, err_text):
    """(갈래, 답, 이어 묻기 id, 까닭, 토큰, 모델, 쓴 도구 {이름: 수}). 판정은 마지막 `result` 이벤트가 든다."""
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
    elif denials:
        status = 'denied'
        reason = '거절된 도구 호출 — 답이 그 도구 없이 지어졌다: ' + ', '.join(
            str(d.get('tool_name') or d) if isinstance(d, dict) else str(d) for d in denials)
    elif not answer.strip():
        status = 'empty'
    else:
        status = 'ok'
    return status, answer, conv, reason, tokens, model, tools


def run_once(cmd_head, a):
    """한 번 띄워 끝까지 지켜본다. 돌려주는 것 — (갈래, 종료 코드, 답, id, 까닭, 토큰, 모델, 도구, 날 출력 경로)."""
    raw_path, err_path = f'{a.out}.claude.jsonl', f'{a.out}.claude.stderr.txt'
    env = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    started = time.monotonic()
    status = None
    # 답은 파이프가 아니라 파일로 받는다 — 파이프를 안 비운 채 기다리면 큰 답에서 멈춘다.
    with open(a.prompt_file, 'rb') as stdin, open(raw_path, 'wb') as raw, open(err_path, 'wb') as err:
        try:
            proc = subprocess.Popen(cmd_head + argv(a.model, a.resume, a.write), cwd=a.cwd, env=env, stdin=stdin,
                                    stdout=raw, stderr=err, creationflags=CREATE_NO_WINDOW)
        except OSError as e:
            return 'spawn', None, '', None, str(e), 'in=- out=-', '-', {}, raw_path
        while proc.poll() is None:
            if time.monotonic() > started + a.timeout:
                kill_tree(proc)
                status = 'timeout'
                break
            time.sleep(POLL_SEC)
    with open(err_path, encoding='utf-8', errors='replace') as f:
        err_text = f.read()
    judged, answer, conv, reason, tokens, model, tools = judge(read_jsonl(raw_path), proc.returncode, err_text)
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
    return status, proc.returncode, answer, conv, reason, tokens, model, tools, raw_path


def main():
    ap = Parser(add_help=False)
    ap.add_argument('--prompt-file', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cwd', required=True)
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SEC)
    ap.add_argument('--model')
    ap.add_argument('--resume')   # 끝 줄의 `resume=` 값 그대로
    ap.add_argument('--write', action='store_true')   # 고치기 레인 — 작업 자리 안만 고친다
    args = sys.argv[1:]
    try:
        a = ap.parse_args(args)
    except Usage as e:
        out = out_arg(args)
        if out:
            try:
                write(out, f'{FOOTER} usage · 인자가 틀렸다 — {e}\n')
            except OSError:
                pass
        return 4
    try:
        return run(a)
    except Exception as e:   # 어디서 멈췄든 답 파일과 끝 줄을 남긴다 — 부른 쪽은 그것만 본다
        write(a.out, f'{traceback.format_exc()}\n{FOOTER} failed · 러너가 멈췄다 — {type(e).__name__}: {e}\n')
        return EXIT['failed']


def run(a):
    if not os.path.isfile(a.prompt_file):
        write(a.out, f'{FOOTER} usage · 프롬프트 파일이 없다 — {a.prompt_file}\n')
        return 4
    bad = prompt_problem(a.prompt_file)
    if bad:
        write(a.out, f'{FOOTER} usage · {bad}\n')
        return 4
    if not (a.cwd and os.path.isdir(a.cwd)):
        write(a.out, f'{FOOTER} usage · --cwd 가 폴더가 아니다 — {a.cwd}\n')
        return 4
    if a.model and not MODEL_NAME_RE.fullmatch(a.model):
        write(a.out, f'{FOOTER} usage · --model 에 따옴표 · 공백이 든다 — {a.model!r}\n')
        return 4
    cmd_head = head()
    if cmd_head is None:
        write(a.out, f'{FOOTER} usage · Claude Code CLI(`claude`)를 못 찾는다\n')
        return 4

    started = time.monotonic()
    status, rc, answer, conv, reason, tokens, model, tools, raw_path = run_once(cmd_head, a)
    elapsed = int(time.monotonic() - started)
    if status == 'spawn':
        write(a.out, f'{FOOTER} usage · 못 띄웠다 — {reason}\n')
        return 4
    used = ','.join(f'{k}:{v}' for k, v in sorted(tools.items())) or '-'
    footer = (f'{FOOTER} {status} · rc={rc} · {elapsed}s · mode={"write" if a.write else "read"} · model={model} · tools={used}'
              f' · tokens {tokens} · {resume_field(conv)}')
    if status == 'ok':
        write(a.out, f'{answer.rstrip()}\n\n{footer}\n')
    else:
        # 날 출력은 길어(이벤트 수십 줄) 옮기지 않는다 — 까닭과 그 자리만 적는다
        write(a.out, f'{answer.rstrip()}\n{reason}\n{footer} · raw={raw_path}\n')
    return EXIT[status]


if __name__ == '__main__':
    sys.exit(main())
