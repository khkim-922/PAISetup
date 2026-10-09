"""Claude 에게 읽기만 하는 일을 맡기고 답을 파일로 받는다 — Codex 가 맡기는 쪽일 때의 러너(결정 0098).

**받는 Claude 는 읽기만 한다.** 쓸 수 있는 도구를 읽기 · 찾기 · 웹 읽기(`READ_TOOLS`)로 좁혀 띄운다 — 셸 · 쓰기 도구는
모델에게 아예 안 보인다. 그래서 받는 쪽이 다른 에이전트를 다시 띄울 길(셸)도 없다. 묻지 않는 권한 방식(`dontAsk`)이라
목록 밖 호출은 묻는 대신 거절되고, 거절이 하나라도 있으면 실패로 친다 — 답이 그 도구 없이 지어졌다는 뜻이다.
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
  0 답이 왔다 · 1 실패했다(거절된 도구 호출 포함) · 2 한도 · 과부하 또는 빈 답 · 3 시간 초과 · 4 부르는 법이 틀렸다 · Claude 가 없다
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
DEFAULT_TIMEOUT_SEC = 1800      # 기본 한도 — 짧은 일도 그대로 둔다(끝나는 대로 돌아온다)
POLL_SEC = 2                    # 끝났나 보는 간격
STDERR_TAIL_CHARS = 2000        # 실패 때 답 파일에 옮기는 stderr 꼬리
EXIT = {'ok': 0, 'failed': 1, 'denied': 1, 'quota': 2, 'empty': 2, 'timeout': 3}
FOOTER = '[claude-bg]'

READ_TOOLS = 'Read,Glob,Grep,WebFetch,WebSearch'   # 읽기 · 찾기 · 웹 읽기 — 셸 · 쓰기는 모델이 아예 못 본다
CLAUDE_ARGS = ['-p', '--output-format', 'stream-json', '--verbose',
               '--setting-sources', 'user', '--settings', json.dumps({'disableAllHooks': True}),
               '--strict-mcp-config', '--disable-slash-commands', '--permission-mode', 'dontAsk',
               '--tools', READ_TOOLS, '--allowedTools', READ_TOOLS]
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


def write(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


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


def argv(model, resume):
    """머리 뒤에 붙일 인자 — 프롬프트는 안 싣는다(표준 입력)."""
    out = list(CLAUDE_ARGS)
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
            proc = subprocess.Popen(cmd_head + argv(a.model, a.resume), cwd=a.cwd, env=env, stdin=stdin,
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
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--prompt-file', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cwd')
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SEC)
    ap.add_argument('--model')
    ap.add_argument('--resume')   # 끝 줄의 `resume=` 값 그대로
    try:
        a = ap.parse_args()
    except SystemExit:
        return 4

    if not os.path.isfile(a.prompt_file):
        write(a.out, f'{FOOTER} usage · 프롬프트 파일이 없다 — {a.prompt_file}\n')
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
    footer = (f'{FOOTER} {status} · rc={rc} · {elapsed}s · model={model} · tools={used}'
              f' · tokens {tokens} · resume={conv or "-"}')
    if status == 'ok':
        write(a.out, f'{answer.rstrip()}\n\n{footer}\n')
    else:
        # 날 출력은 길어(이벤트 수십 줄) 옮기지 않는다 — 까닭과 그 자리만 적는다
        write(a.out, f'{answer.rstrip()}\n{reason}\n{footer} · raw={raw_path}\n')
    return EXIT[status]


if __name__ == '__main__':
    sys.exit(main())
