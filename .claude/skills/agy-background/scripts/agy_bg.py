"""agy 에게 일을 맡기고 답을 파일로 받는다 — 백그라운드 Bash 에서 `pythonw` 로 부른다.

**왜 pythonw 인가.** 백그라운드 Bash 는 명령을 콘솔 없이 띄운다. 콘솔 없는 부모 밑에서 뜬 콘솔
프로그램은 새 콘솔을 받아 창이 뜨고, agy 가 명령을 돌릴 때마다 또 뜬다. `pythonw` 는 콘솔이 없는
GUI 프로그램이라 제 창이 없고, agy 를 「창 없음」(CREATE_NO_WINDOW)으로 띄워 **안 보이는 콘솔**을
붙인다 — agy 의 자식들은 그 콘솔을 물려받아 창을 안 낸다. `python`·`powershell`·`cmd`·`node` 로
감싸면 그것들이 콘솔 프로그램이라 제 창이 먼저 뜬다.

**왜 로그를 훑나.** 로그인 방식 agy 는 화면 없이 돌 때 한도 초과(429)를 밖으로 안 낸다 — 시간이
다 될 때까지 조용히 다시 시도하다가 빈 답으로 끝난다. 그래서 `--log-file` 을 받아 두고 훑다가 그
줄(`RESOURCE_EXHAUSTED (code 429)` — agy-bridge 0.4.2 의 `QUOTA_RE` 에서 빌린 꼴)이 보이면 바로 끊는다.
API 키 방식은 꼴이 달라 로그에 `Error 429 …`, stderr 에 `"error_code":429` 를 남기고 바로 끝난다 —
둘 다 문다. 과부하(503 「수요가 몰렸다」)도 같이 문다 — agy 는 그 모델로 몇 분씩 다시 시도하다 시간을 다
쓴다(API 키 방식 실측 2026-10-08: 3.8 Flash 에서 5분 내내 503 · 다음 후보로 안 넘어갔다).

**한도나 과부하에 걸리면 다음 모델로 다시 띄운다.** 차례는 맡기기 모델(`AGY_MODEL_DELEGATE` — 있는
자리에서만) → 기본 모델(`AGY_DEFAULT_MODEL`) → 넘어갈 모델(`AGY_FALLBACK_MODELS`, `;` 로 여럿)이다. 값을
그렇게 짠 까닭(자리마다 서는 모델 · 한도가 차는 단위가 방식마다 다르다)은 그 값을 심는 설치기의 곁말이 든다.
`--model` 을 주면 그것 하나만 쓴다 — 손으로 고른 모델은 넘기지 않는다.

**`api:` 를 붙인 후보는 API 키 방식으로 띄운다.** agy 는 방식을 홈의 `settings.json` 한 파일로 정해,
같은 때 로그인 방식과 섞으려면 그 프로세스만 다른 홈을 봐야 한다 — 그래서 `USERPROFILE` 만 가짜 홈으로
준다(agy 는 `HOME` 을 안 보고 그것만 본다 — 실측). 키(`GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`)가 없으면
그 후보는 **조용히 건너뛴다** — 키 없는 PC 는 로그인 방식 후보만으로 그대로 돈다. 대가 둘:
agy 가 띄우는 명령 가운데 `USERPROFILE` 로 홈을 찾는 것(node · python)은 가짜 홈을 본다 — `HOME` 은
진짜 홈으로 두어 git 은 신원을 안 잃는다. 대화도 그 홈에 쌓여, 이어 물을 때는 `--model "api:…"` 로
같은 방식을 준다.

**말은 전부 `--out` 파일로 간다** — pythonw 에는 표준 출력이 없다. 부른 쪽은 종료 코드로 갈래를
알고 그 파일을 읽는다. 맨 끝 줄 `[agy-bg] …` 이 갈래 · 걸린 시간 · 모델 · 넘어간 자취 · 토큰 ·
이어 묻기 id 를 든다:
  0 답이 왔다 · 1 agy 가 실패했다 · 2 한도 초과 · 과부하(넘어갈 모델까지 다) 또는 빈 답 · 3 시간 초과 ·
  4 부르는 법이 틀렸다
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

AGY = 'agy'
CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
# 한도 초과의 두 꼴 — 로그인 방식(로그) · API 키 방식(로그의 `Error 429` · stderr 의 `AGY_ERROR` JSON)
QUOTA_RE = re.compile(r'RESOURCE_EXHAUSTED \(code 429\)|"error_code":\s*429|Error 429\b')
# 과부하의 꼴 — API 키 방식 로그의 `Run: attempt N failed (Error 503, … Status: UNAVAILABLE …)`(실측).
# ⚠ 로그인 방식의 503 꼴은 아직 못 봤다 — 보면 여기에 더한다.
OVERLOAD_RE = re.compile(r'Error 503\b')
# 넘어가는 갈래 — 이 둘은 다음 후보로 다시 띄운다. 나머지(실패 · 빈 답 · 시간 초과)는 모델 탓이 아니라 멈춘다.
FAILOVER = ('quota', 'overload')
API_PREFIX = 'api:'                          # 이 머리를 단 후보는 API 키 방식으로 띄운다
API_SETTINGS = {'modelProvider': 'gemini'}   # agy 가 로그인 없이 API 키로 서는 설정 — agy 체인지로그
# agy 제 한도가 차면 종료 코드 0 · status SUCCESS · 빈 답으로 끝나고, 까닭은 stderr 한 줄에만 남는다.
PRINT_TIMEOUT_RE = re.compile(r'\[agy\] print timeout')
DEFAULT_TIMEOUT_SEC = 1800  # 기본 한도 — 짧은 일도 그대로 둔다(끝나는 대로 돌아온다)
POLL_SEC = 2                # 로그를 훑고 agy 가 끝났나 보는 간격
KILL_GRACE_SEC = 15         # agy 제 한도(--print-timeout) 뒤에 기다려 주는 여유 — agy-bridge 0.4.2 에서 빌린 값
LOG_CARRY_CHARS = 200       # 읽기 경계에 걸친 패턴을 놓치지 않게 남기는 꼬리
MAX_PROMPT_CHARS = 30000    # 윈도 명령줄 한도(32,767자) 안에 인자 전체가 들게 남긴다
EXIT = {'ok': 0, 'failed': 1, 'quota': 2, 'overload': 2, 'empty': 2, 'timeout': 3}


def write(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def kill_tree(proc):
    """agy 가 띄운 셸까지 같이 끊는다 — agy 만 끊으면 자식이 남는다."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)],
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
    else:
        proc.kill()
    proc.wait()


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
    """같으면 안 쓴다 — 띄울 때마다 짓는 파일이라 매번 쓰면 시각만 바뀐다."""
    try:
        with open(path, encoding='utf-8') as f:
            if f.read() == text:
                return
    except OSError:
        pass
    write(path, text)


def api_key():
    """API 키 방식에 쓸 키 — agy 와 같은 차례다(둘 다 있으면 agy 가 `GOOGLE_API_KEY` 를 쓴다)."""
    return os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY') or ''


def derive_config(path, src_dir, real_home):
    """진짜 agy 설정 파일 하나를 가짜 홈에 쓸 꼴로 — 홈을 가리키는 자리만 진짜 홈의 절대 경로로 바꾼다.
    경로를 안 가리키는 파일(기계마다 갈리는 값)은 `None` — 옮기지 않는다."""
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8') as f:
        text = f.read()
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


def api_home(real_home):
    """API 키 방식으로 띄울 홈을 짓는다 — 방식 한 줄과, 진짜 홈의 규범·스킬·룰 설정에서 **매번 다시 지은**
    가리킴 파일들. 사본을 들고 있지 않으므로 진짜 설정을 고치면 다음 실행에 따라온다.
    ⚠ 링크(정션)를 안 쓴다 — 파이썬 3.12 전의 `shutil.rmtree` 는 정션을 따라 들어가 진짜 홈을 지운다."""
    base = os.environ.get('LOCALAPPDATA') or os.path.join(real_home, '.cache')
    home = os.path.join(base, 'agy-bg', 'api-home')
    cli = os.path.join(home, '.gemini', 'antigravity-cli')
    os.makedirs(cli, exist_ok=True)
    put(os.path.join(cli, 'settings.json'), json.dumps(API_SETTINGS))
    src = os.path.join(real_home, '.gemini', 'config')
    if os.path.isdir(src):
        dst = os.path.join(home, '.gemini', 'config')
        os.makedirs(dst, exist_ok=True)
        for name in os.listdir(src):
            text = derive_config(os.path.join(src, name), src, real_home)
            if text is not None:
                put(os.path.join(dst, name), text)
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


def run_once(a, prompt, model, log, raw_path, err_path):
    """agy 를 한 번 띄워 끝까지 지켜본다. 돌려주는 것 — (갈래, 종료 코드, 답 JSON, 날 stdout, stderr).
    띄우지도 못했으면 갈래가 'spawn' 이고 stderr 자리에 까닭이 든다."""
    env = None
    if model and model.startswith(API_PREFIX):
        real_home = os.path.expanduser('~')
        env = dict(os.environ, USERPROFILE=api_home(real_home), HOME=real_home, GEMINI_API_KEY=api_key())
        model = model[len(API_PREFIX):]
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


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--prompt-file', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cwd')
    ap.add_argument('--model')
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SEC)
    ap.add_argument('--conversation')
    try:
        a = ap.parse_args()
    except SystemExit:
        return 4   # pythonw 라 argparse 의 말은 어디에도 안 닿는다 — 종료 코드만 남는다

    try:
        with open(a.prompt_file, encoding='utf-8') as f:
            prompt = f.read()
    except OSError as e:
        write(a.out, f'[agy-bg] usage · 프롬프트 파일을 못 읽었다 — {e}\n')
        return 4
    if len(prompt) > MAX_PROMPT_CHARS:
        write(a.out, f'[agy-bg] usage · 프롬프트가 {len(prompt)}자다 — {MAX_PROMPT_CHARS}자를 넘으면 '
                     '명령줄에 안 든다. 큰 자료는 파일 경로를 주고 agy 가 읽게 한다\n')
        return 4

    if a.model and a.model.startswith(API_PREFIX) and not api_key():
        write(a.out, '[agy-bg] usage · api: 후보는 키가 있어야 띄운다 — GOOGLE_API_KEY 나 GEMINI_API_KEY 가 없다\n')
        return 4

    log, raw_path, err_path = a.out + '.agy.log', a.out + '.raw.json', a.out + '.stderr.txt'
    started = time.monotonic()
    tried = []
    models = candidates(a.model, bool(api_key()))
    for i, model in enumerate(models):
        status, rc, res, raw_text, err_text = run_once(a, prompt, model, log, raw_path, err_path)
        if status == 'spawn':
            write(a.out, f'[agy-bg] failed · agy 를 못 띄웠다 — {err_text}\n')
            return 1
        if status not in FAILOVER or i == len(models) - 1:
            break
        tried.append(f'{model}: {status}')
    elapsed = int(time.monotonic() - started)

    answer = res.get('response') or ''
    usage = res.get('usage') or {}
    footer = (f'[agy-bg] {status} · rc={rc} · {elapsed}s'
              f' · model={model or "agy 기본"}'
              + (f' · failover={"; ".join(tried)}' if tried else '') +
              f' · tokens in={usage.get("input_tokens", "-")} out={usage.get("output_tokens", "-")}'
              f' · conversation={res.get("conversation_id") or "-"}')
    if status == 'ok':
        for p in (raw_path, err_path, log):
            try:
                os.remove(p)
            except OSError:
                pass
        write(a.out, f'{answer.rstrip()}\n\n{footer}\n')
    else:
        # 답이 없으면 agy 가 낸 것을 그대로 둔다 — 까닭이 거기 있다. 로그도 남긴다.
        write(a.out, f'{answer or raw_text}\n{err_text}\n{footer} · log={log}\n')
    return EXIT[status]


if __name__ == '__main__':
    sys.exit(main())
