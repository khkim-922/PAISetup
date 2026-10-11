"""Codex 에게 일을 맡기고, 한도가 차면 Copilot 에게 넘긴다 — 답은 파일로 받는다. 백그라운드 Bash 에서
`pythonw` 로 부른다. 왜 pythonw 인가(콘솔 없는 부모 밑에서 창이 뜨는 사정)는 agy 래퍼
`agy-background/scripts/agy_bg.py` 머리말이 든다 — 같은 윈도 사정이고, 여기도 같은 길(「창 없음」)로 띄운다.

**기본은 둘 다 읽기만 한다.** Codex 는 읽기 전용 샌드박스(`sandbox_mode`)에 앱 · 플러그인 · MCP 도구를 끄고, Copilot 은
읽기 · 웹 읽기 도구만 보이게(`--available-tools`) 띄운다. Copilot 은 거기에 더해 작업 자리와 임시 폴더 밖 파일을 못 연다.
**`--write` 를 주면 고치기 레인이다**(결정 0100) — Codex 를 작업 자리 쓰기 샌드박스(`workspace-write`)로 띄운다. 쓰는
자리는 작업 자리(`--cwd`)와 임시 폴더뿐이고 셸의 망은 닫힌 채다(Codex 기본값). 앱 · 플러그인 · MCP 는 그대로 끈다.
**고치기 레인은 Copilot 이 안 받는다** — Copilot 의 쓰는 범위를 가두는 법을 아직 안 쟀다. Codex 가 한도면 그대로
멈춘다(2). 자리를 잘못 물려받지 않게 `--cwd` 를 받아야만 띈다.

**프롬프트는 표준 입력으로 넘긴다** — 명령줄 길이 한도와 따옴표 해석을 안 탄다. 윈도에서 npm 이 까는
실행 꼴은 `.cmd` 셔틀이라 명령줄 인자가 cmd.exe 를 거친다(8191자 · `& | % ^` 해석). 그래서 셔틀이 부르는
JS 를 node 로 바로 부른다 — 인자는 고정 플래그뿐이다.

**넘기는 것은 Codex 의 한도뿐이다** — 사용 한도 · 할당량 · 용량 초과 · 429 재시도 소진. 그 밖의 실패와 시간
초과는 멈춘다: Copilot 으로 다시 띄우면 같은 일이 되풀이되거나 Codex 쪽 고장을 가린다. 깔리지 않은 쪽은
건너뛴다(끝 줄에 남는다).

**자리마다 다른 값은 환경변수로 받는다** — 배포본 설치기가 자리(사내 · 사외)마다 사용자 환경변수로 심고(그 값의
진본은 설치기의 `$CcBgVarsBySite`), 래퍼는 자리를 모른 채 그 값만 읽는다. 없으면 아래 기본값이다. 값이 틀리면
그 이름을 대고 멈춘다(4) — 조용히 기본값으로 물러나면 자리의 선(어느 쪽에 보내나)이 말없이 바뀐다.
  · `CC_BG_AGENTS` — 차례이자 쓸 수 있는 쪽(쉼표). 여기 없는 쪽은 `--agent` · `--resume` 으로도 못 부른다
  · `CC_BG_CODEX_WEB_SEARCH` — Codex 의 `web_search`. `disabled` 만이 검색 도구를 요청에서 뺀다(`cached` 도 싣는다)
  · `CC_BG_CODEX_WIN_SANDBOX` — Codex 의 `windows.sandbox`. 없으면 안 넘겨 Codex 설정을 따른다
  · `CC_BG_CODEX_MODEL` — Codex 의 `model`. 없으면 안 넘긴다

**말은 전부 `--out` 파일로 간다** — pythonw 에는 표준 출력이 없다. 맨 끝 줄 `[cc-bg] …` 이 갈래 · 걸린 시간 ·
맡은 쪽 · 넘어간 자취 · 토큰 · 웹 검색 수 · 이어 묻기 값을 든다:
  0 답이 왔다 · 1 실패했다 · 2 한도(받을 쪽까지 다) 또는 빈 답 · 3 시간 초과 · 4 부르는 법이 틀렸다 · 깔린 쪽이 없다

**웹 검색 수(`web=`)는 Codex 가 실제로 마친 검색이다** — 검색을 열어 두어도 검색 없이 기억으로 답할 수 있고,
모르는 도구를 오류 없이 삼키는 게이트웨이 뒤에서는 그것이 조용히 난다. 답만 보면 안 갈려 끝 줄이 센다.
Copilot 은 `-` 다 — 검색 도구가 없고, 주소를 연 횟수를 세는 이벤트 꼴은 아직 안 잡았다.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

AGENTS = ('codex', 'copilot')   # 차례 — 1번 · 2번
CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
DEFAULT_TIMEOUT_SEC = 1800      # 기본 한도 — 짧은 일도 그대로 둔다(끝나는 대로 돌아온다)
POLL_SEC = 2                    # 끝났나 보는 간격
STDERR_TAIL_CHARS = 2000        # 실패 때 답 파일에 옮기는 stderr 꼬리
EXIT = {'ok': 0, 'failed': 1, 'quota': 2, 'empty': 2, 'timeout': 3}
FOOTER = '[cc-bg]'

# 셔틀(`.cmd`)이 부르는 JS — npm 전역 자리(셔틀 곁의 `node_modules`) 기준
NPM_ENTRY = {'codex': ('@openai', 'codex', 'bin', 'codex.js'),
             'copilot': ('@github', 'copilot', 'npm-loader.js')}
SHIM_EXT = ('.cmd', '.bat')

# Codex 의 한도 문구 — openai/codex `codex-rs/protocol/src/error.rs` 의 것이다. 「You’ve」의 아포스트로피가 판마다
# U+2019 · ASCII 로 갈려 그 뒤부터 문다. 마지막 둘은 API 키 방식 · 일반 429 를 재시도하다 다 쓴 꼴이다.
CODEX_QUOTA_RE = re.compile(r'hit your usage limit|Quota exceeded\. Check your plan|Selected model is at capacity|'
                            r'exceeded retry limit, last status: 429|rate limit exceeded')
# 읽기 전용 샌드박스는 셸 명령에만 걸린다 — 앱 커넥터(`codex_apps`) · 플러그인 · MCP 서버의 도구는 샌드박스 밖에서
# 돌고(쓰기 · 보내기를 하는 도구도 있다) 웹 검색 값과 따로 웹을 연다. 그래서 셋을 다 끄고 띄운다 — 웹으로 가는 길이
# 검색 도구(`web_search`) 하나로 좁아져, 끝 줄의 `web=` 가 그 길을 다 센다.
CODEX_ARGS = ['-c', 'features.apps=false', '-c', 'features.plugins=false',
              '-c', 'mcp_servers={}', '--skip-git-repo-check', '--json']
CODEX_SANDBOX = {False: 'read-only', True: 'workspace-write'}   # 읽기 레인 · 고치기 레인
WRITE_AGENTS = ('codex',)   # 고치기 레인을 받는 쪽 — Copilot 은 쓰는 범위를 가두는 법을 안 쟀다

# 자리 값의 이름과 받는 값 — 받는 값은 Codex 설정의 낱말 그대로다(`web_search` · `windows.sandbox`).
KNOB_AGENTS = 'CC_BG_AGENTS'
KNOB_WEB_SEARCH = 'CC_BG_CODEX_WEB_SEARCH'
KNOB_WIN_SANDBOX = 'CC_BG_CODEX_WIN_SANDBOX'
KNOB_MODEL = 'CC_BG_CODEX_MODEL'
WEB_SEARCH_MODES = ('disabled', 'cached', 'indexed', 'live')
WIN_SANDBOX_MODES = ('elevated', 'unelevated', 'mxc')
DEFAULT_WEB_SEARCH = 'live'                       # 값이 없으면 실시간 검색
MODEL_NAME_RE = re.compile(r'[A-Za-z0-9._:/-]+')  # TOML 따옴표 안에 그대로 들어간다 — 따옴표 · 공백을 막는다

# Copilot 이 한도로 멈춘 꼴 — `session.error` 의 `errorType`(quota · 402 / rate_limit · 429). 종료 코드는 0 으로
# 끝난 기록도 있어 그것보다 이 이벤트를 먼저 본다.
COPILOT_QUOTA_TYPES = ('quota', 'rate_limit')
COPILOT_TOOLS = ('view', 'web_fetch', 'glob', 'rg')   # 읽기 · 웹 읽기만 — 셸 · 쓰기는 모델이 아예 못 본다
COPILOT_ARGS = ['--available-tools', *COPILOT_TOOLS, '--allow-tool=web_fetch', '--allow-all-urls',
                '--no-ask-user', '--output-format', 'json']
# 저장된 로그인보다 앞서는 토큰 — Copilot 권한이 없는 토큰이면 인증부터 깨진다. `COPILOT_GITHUB_TOKEN` 은 Copilot 에
# 쓰라고 둔 것이라 남긴다.
COPILOT_DROP_ENV = ('GH_TOKEN', 'GITHUB_TOKEN')


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
    model = env.get(KNOB_MODEL, '').strip()
    if model and not MODEL_NAME_RE.fullmatch(model):
        return None, f'{KNOB_MODEL}={model!r} — 모델 이름에 따옴표 · 공백이 든다'
    return {'agents': agents, 'web_search': web, 'win_sandbox': sandbox, 'model': model}, None


def codex_config(knobs):
    """자리 값을 Codex 설정 덮어쓰기(`-c`)로 — 이어 묻기에도 같이 건다."""
    out = ['-c', f'web_search="{knobs["web_search"]}"']
    if knobs['win_sandbox']:
        out += ['-c', f'windows.sandbox="{knobs["win_sandbox"]}"']
    if knobs['model']:
        out += ['-c', f'model="{knobs["model"]}"']
    return out


def argv(agent, resume, knobs, write=False):
    """머리 뒤에 붙일 인자 — 프롬프트는 안 싣는다(표준 입력). 이어 물을 때도 고치기 레인이면 `--write` 를 다시 준다."""
    if agent == 'codex':
        tail = ['-c', f'sandbox_mode="{CODEX_SANDBOX[write]}"', *CODEX_ARGS, *codex_config(knobs)]
        if resume:
            return ['exec', 'resume', *tail, resume, '-']
        return ['exec', *tail, '-']
    return COPILOT_ARGS + ([f'--resume={resume}'] if resume else [])


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
    raw_path, err_path = f'{a.out}.{agent}.jsonl', f'{a.out}.{agent}.stderr.txt'
    env = dict(os.environ)
    if agent == 'copilot':
        for k in COPILOT_DROP_ENV:
            env.pop(k, None)
    started = time.monotonic()
    status = None
    # 답은 파이프가 아니라 파일로 받는다 — 파이프를 안 비운 채 기다리면 큰 답에서 멈춘다.
    with open(a.prompt_file, 'rb') as stdin, open(raw_path, 'wb') as raw, open(err_path, 'wb') as err:
        try:
            proc = subprocess.Popen(cmd_head + argv(agent, resume, a.knobs, a.write), cwd=a.cwd, env=env, stdin=stdin,
                                    stdout=raw, stderr=err, creationflags=CREATE_NO_WINDOW)
        except OSError as e:
            return 'spawn', None, '', None, str(e), 'in=- out=-', None, raw_path
        while proc.poll() is None:
            if time.monotonic() > started + a.timeout:
                kill_tree(proc)
                status = 'timeout'
                break
            time.sleep(POLL_SEC)
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


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--prompt-file', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cwd')
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SEC)
    ap.add_argument('--agent', choices=AGENTS)
    ap.add_argument('--resume')   # 끝 줄의 `resume=` 값 그대로 — `<쪽>:<id>`
    ap.add_argument('--write', action='store_true')   # 고치기 레인 — 작업 자리 안만 고친다
    try:
        a = ap.parse_args()
    except SystemExit:
        return 4   # pythonw 라 argparse 의 말은 어디에도 안 닿는다 — 종료 코드만 남는다

    if not os.path.isfile(a.prompt_file):
        write(a.out, f'{FOOTER} usage · 프롬프트 파일이 없다 — {a.prompt_file}\n')
        return 4
    a.knobs, bad = read_knobs(os.environ)
    if bad:
        write(a.out, f'{FOOTER} usage · 자리 값이 틀렸다 — {bad}\n')
        return 4
    allowed = a.knobs['agents']
    resume = None
    if a.resume:
        agent, _, resume = a.resume.partition(':')
        if agent not in AGENTS or not resume:
            write(a.out, f'{FOOTER} usage · --resume 은 `<쪽>:<id>` 꼴이다 — 쪽은 {" · ".join(AGENTS)}\n')
            return 4
        # 대화가 그쪽에 있다 — 다른 쪽으로 넘기면 앞 맥락이 없다
        order = [agent]
    else:
        order = [a.agent] if a.agent else allowed
    # 자리가 안 쓰는 쪽은 손으로 골라도 안 띄운다 — 그쪽으로 보내지 않는 것이 그 자리의 선이다
    if any(x not in allowed for x in order):
        write(a.out, f'{FOOTER} usage · 이 자리에서 안 쓰는 쪽이다 — {KNOB_AGENTS}={",".join(allowed)}\n')
        return 4
    if a.write:
        if not (a.cwd and os.path.isdir(a.cwd)):
            write(a.out, f'{FOOTER} usage · --write 는 --cwd 로 작업 자리를 준다 — 쓰는 범위가 그 자리다\n')
            return 4
        if (a.agent or a.resume) and any(x not in WRITE_AGENTS for x in order):
            write(a.out, f'{FOOTER} usage · 고치기 레인은 {" · ".join(WRITE_AGENTS)} 만 받는다\n')
            return 4
        order = [x for x in order if x in WRITE_AGENTS]
        if not order:
            write(a.out, f'{FOOTER} usage · 고치기 레인을 받을 쪽이 이 자리에 없다 — {KNOB_AGENTS}={",".join(allowed)}\n')
            return 4

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
        return 4
    agent, status, rc, answer, conv, reason, tokens, searches, raw_path = ran
    footer = (f'{FOOTER} {status} · rc={rc} · {elapsed}s · mode={"write" if a.write else "read"} · agent={agent}'
              + (f' · failover={"; ".join(tried)}' if tried else '') +
              f' · tokens {tokens} · web={"-" if searches is None else searches}'
              f' · resume={f"{agent}:{conv}" if conv else "-"}')
    if status == 'ok':
        write(a.out, f'{answer.rstrip()}\n\n{footer}\n')
    else:
        # 날 출력은 길어(이벤트 수백 줄) 옮기지 않는다 — 까닭과 그 자리만 적는다
        write(a.out, f'{answer.rstrip()}\n{reason}\n{footer} · raw={raw_path}\n')
    return EXIT[status]


if __name__ == '__main__':
    sys.exit(main())
