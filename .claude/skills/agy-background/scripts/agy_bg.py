"""agy 에게 긴 일을 맡기고 답을 파일로 받는다 — 백그라운드 Bash 에서 `pythonw` 로 부른다.

**왜 pythonw 인가.** 백그라운드 Bash 는 명령을 콘솔 없이 띄운다. 콘솔 없는 부모 밑에서 뜬 콘솔
프로그램은 새 콘솔을 받아 창이 뜨고, agy 가 명령을 돌릴 때마다 또 뜬다. `pythonw` 는 콘솔이 없는
GUI 프로그램이라 제 창이 없고, agy 를 「창 없음」(CREATE_NO_WINDOW)으로 띄워 **안 보이는 콘솔**을
붙인다 — agy 의 자식들은 그 콘솔을 물려받아 창을 안 낸다. `python`·`powershell`·`cmd`·`node` 로
감싸면 그것들이 콘솔 프로그램이라 제 창이 먼저 뜬다.

**왜 로그를 훑나.** agy 는 화면 없이 돌 때 한도 초과(429)를 밖으로 안 낸다 — 시간이 다 될
때까지 조용히 다시 시도하다가 빈 답으로 끝난다. 그래서 `--log-file` 을 받아 두고 훑다가 그 줄이
보이면 바로 끊는다. 패턴은 agy-bridge 의 `QUOTA_RE` 와 같다.

**말은 전부 `--out` 파일로 간다** — pythonw 에는 표준 출력이 없다. 부른 쪽은 종료 코드로 갈래를
알고 그 파일을 읽는다. 맨 끝 줄 `[agy-bg] …` 이 갈래 · 걸린 시간 · 토큰 · 이어 묻기 id 를 든다:
  0 답이 왔다 · 1 agy 가 실패했다 · 2 한도 초과 또는 빈 답 · 3 시간 초과 · 4 부르는 법이 틀렸다
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
QUOTA_RE = re.compile(r'RESOURCE_EXHAUSTED \(code 429\)')
# agy 제 한도가 차면 종료 코드 0 · status SUCCESS · 빈 답으로 끝나고, 까닭은 stderr 한 줄에만 남는다.
PRINT_TIMEOUT_RE = re.compile(r'\[agy\] print timeout')
DEFAULT_TIMEOUT_SEC = 1800  # 긴 일의 기본 한도 — 짧은 일은 이 래퍼가 아니라 MCP 로 간다
POLL_SEC = 2                # 로그를 훑고 agy 가 끝났나 보는 간격
KILL_GRACE_SEC = 15         # agy 제 한도(--print-timeout) 뒤에 기다려 주는 여유 — agy-bridge 와 같은 값
LOG_CARRY_CHARS = 200       # 읽기 경계에 걸친 패턴을 놓치지 않게 남기는 꼬리
MAX_PROMPT_CHARS = 30000    # 윈도 명령줄 한도(32,767자) 안에 인자 전체가 들게 남긴다
EXIT = {'ok': 0, 'failed': 1, 'quota': 2, 'empty': 2, 'timeout': 3}


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

    def quota_hit(self):
        try:
            with open(self.path, encoding='utf-8', errors='replace') as f:
                f.seek(self.pos)
                chunk = f.read()
                self.pos = f.tell()
        except OSError:
            return False
        text = self.carry + chunk
        self.carry = text[-LOG_CARRY_CHARS:]
        return bool(QUOTA_RE.search(text))


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--prompt-file', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cwd')
    ap.add_argument('--model', default=os.environ.get('AGY_DEFAULT_MODEL'))
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

    log, raw_path, err_path = a.out + '.agy.log', a.out + '.raw.json', a.out + '.stderr.txt'
    cmd = [AGY, '-p', prompt, '--output-format', 'json', '--dangerously-skip-permissions',
           '--print-timeout', f'{a.timeout}s', '--log-file', log]
    if a.model:
        cmd += ['--model', a.model]
    if a.conversation:
        cmd += ['--conversation', a.conversation]

    started = time.monotonic()
    status = None
    # 답은 파이프가 아니라 파일로 받는다 — 파이프를 안 비운 채 기다리면 큰 답에서 agy 가 멈춘다.
    # stderr 는 따로 받는다 — 같은 파일에 섞이면 그 한 줄이 JSON 을 깨뜨린다.
    with open(raw_path, 'wb') as raw, open(err_path, 'wb') as err:
        try:
            proc = subprocess.Popen(cmd, cwd=a.cwd, stdin=subprocess.DEVNULL, stdout=raw,
                                    stderr=err, creationflags=CREATE_NO_WINDOW)
        except OSError as e:
            write(a.out, f'[agy-bg] failed · agy 를 못 띄웠다 — {e}\n')
            return 1
        tail = LogTail(log)
        deadline = started + a.timeout + KILL_GRACE_SEC
        while proc.poll() is None:
            if tail.quota_hit():
                kill_tree(proc)
                status = 'quota'
            elif time.monotonic() > deadline:
                kill_tree(proc)
                status = 'timeout'
            else:
                time.sleep(POLL_SEC)
    elapsed = int(time.monotonic() - started)

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
        if tail.quota_hit():
            status = 'quota'
        elif PRINT_TIMEOUT_RE.search(err_text):
            status = 'timeout'
        elif proc.returncode != 0 or res.get('status') != 'SUCCESS':
            status = 'failed'
        elif not answer.strip():
            status = 'empty'
        else:
            status = 'ok'

    usage = res.get('usage') or {}
    footer = (f'[agy-bg] {status} · rc={proc.returncode} · {elapsed}s'
              f' · model={a.model or "agy 기본"}'
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
