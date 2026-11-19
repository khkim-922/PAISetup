"""맡기기 러너 셋(agy-background · codex-copilot-background · claude-background)이 함께 쓰는 손 — 인자 가르기(같이 받는 인자
넷) · 프롬프트 파일 읽기 · 띄울 머리 찾기(npm 셔틀) · 띄워 지켜보기 · 답 파일 쓰기 · 끝 줄 · 도움말 · 프로세스 끊기. 띄우는
명령 · 갈래 판정 · 끝 줄의 칸 · 종료 코드 표처럼 러너마다 갈리는 것은 러너가 든다.

부르는 꼴 — 러너는 스킬 홈에 이 스킬과 나란히 깔린다::

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'agent-envelope' / 'scripts'))
    import runner_common as common
    common.main(build_parser, help_epilog, run, FOOTER, EXIT)

러너는 창 없이 돌아 말할 곳이 답 파일(`--out`)뿐이다 — 이 파일을 못 실으면 러너가 제 손으로 그 파일에 끝 줄을 남긴다.

러너가 도는 동안 부른 Claude 대화가 식지 않게, 요청이 루프백 프록시를 지나는 자리에서는 그 프록시에 「이 세션(의 이 레인)이
나를 기다린다」를 알린다(`waiting_notice`). 프록시가 없거나 답이 없으면 아무 일도 없다.
"""
import argparse
import codecs
import glob
import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from urllib.parse import urlsplit

CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
DEFAULT_TIMEOUT_SEC = 1800      # 기본 한도 — 짧은 일도 그대로 둔다(끝나는 대로 돌아온다)
POLL_SEC = 2                    # 받는 쪽이 끝났나 보는 간격
STDERR_TAIL_CHARS = 2000        # 실패 때 답 파일에 옮기는 stderr 꼬리
SHIM_EXT = ('.cmd', '.bat')     # npm 이 윈도에 까는 실행 껍데기 — 그것이 부르는 것을 바로 띄운다(`npm_head`)
JS_EXT = ('.js', '.mjs', '.cjs')
# 프롬프트 파일이 받는 인코딩 — `decode_prompt` 가 받는 것과 같은 말이고 거절 사유 · `--help` 가 이 글을 읽는다
PROMPT_ENCODINGS = 'UTF-8(BOM 은 있어도 없어도) · UTF-16 LE/BE(BOM 이 있어야)'
# 답 파일의 인코딩 — 윈도는 BOM 을 단다(PowerShell 5.1 `Get-Content` 는 BOM 없는 파일을 ANSI 로 읽어 한글 · `·` 를 깨뜨린다).
# 다른 OS 는 BOM 없이 둔다 — 첫 줄을 끝 줄 머리(`^[…-bg]`)로 찾는 손을 BOM 이 헛짚게 한다
ANSWER_ENCODING = 'utf-8-sig' if os.name == 'nt' else 'utf-8'
# ── 기다리는 대화 알리기 ── 부른 Claude 의 Bash 가 자식에게 주는 환경에서 읽는다 — 세션 번호는 메인 · 레인이 같이 받고,
# 레인 번호는 어느 환경 값에도 없다. 요청이 지나는 길은 Claude Code 와 같은 `ANTHROPIC_BASE_URL`
SESSION_ENV = 'CLAUDE_CODE_SESSION_ID'
BASE_URL_ENV = 'ANTHROPIC_BASE_URL'
CONFIG_DIR_ENV = 'CLAUDE_CONFIG_DIR'
LOOPBACK_HOSTS = ('127.0.0.1', 'localhost', '::1')
WAIT_PATH = '/runner-wait'      # 프록시의 로컬 문 — 상류로 안 넘긴다. 옛 프록시는 403 으로 답해 아무 일도 없다
WAIT_EVERY_SEC = 60             # 알리는 간격 — 프록시의 데우기 간격(270초)보다 짧으면 러너가 도는 동안 횟수가 안 찬다
WAIT_TIMEOUT_SEC = 0.5          # 알림 한 번의 끝 — 곁 스레드에서만 기다려 러너를 안 늦춘다
# 부른 레인 찾기 — 그 세션의 레인 기록(`projects/*/<세션>/subagents/agent-<레인>.jsonl`, 이어 묻기 값 훅과 같은 자리)에서
# 끝 조각만 읽는다. 러너를 띄운 도구 호출은 기록의 끝에 있다
LANE_TAIL_BYTES = 262144
SESSION_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
LANE_FILE_RE = re.compile(r'agent-([A-Za-z0-9_-]{1,128})\.jsonl')
# 부른 레인을 찾는 판 수 — 러너를 띄운 호출은 러너가 뜰 때 이미 기록에 있다. 못 찾으면 그 뒤로는 메인만 알린다
LANE_SCANS = 2


def write(path, text):
    """답 파일을 쓴다 — 인코딩은 `ANSWER_ENCODING`."""
    with open(path, 'w', encoding=ANSWER_ENCODING) as f:
        f.write(text)


class Usage(Exception):
    """인자를 못 갈랐다. argparse 는 그 말을 stderr 에 찍고 끝내지만 부른 쪽은 답 파일만 읽는다 — 답 파일에 옮긴다."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


class HelpFormat(argparse.RawDescriptionHelpFormatter):
    """`--help` 의 꼴 — 폭만 넓혀 플래그마다 한 줄에 둔다(아래쪽 절은 러너의 `help_epilog` 가 짠 그대로 간다)."""

    def __init__(self, prog):
        super().__init__(prog, max_help_position=26, width=140)


def out_arg(args):
    """인자를 못 갈랐을 때 답 파일 자리 — `--out <경로>` · `--out=<경로>` 만 찾는다. 없으면 None."""
    for i, x in enumerate(args):
        if x == '--out' and i + 1 < len(args):
            return args[i + 1]
        if x.startswith('--out='):
            return x[len('--out='):]
    return None


def decode_prompt(raw):
    """프롬프트 파일 바이트 → 글. 받는 인코딩은 `PROMPT_ENCODINGS` — 그 밖이면 UnicodeDecodeError. BOM 은 걷힌다.
    글에 NUL 이 있어도 거절한다: BOM 없는 UTF-16 · BOM 있는 UTF-32 는 UTF-8 로도 읽혀 NUL 이 낀 채 받는 쪽으로 간다."""
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        text = raw.decode('utf-16')
    else:
        text = raw.decode('utf-8-sig')
    if '\x00' in text:
        raise UnicodeDecodeError('utf-8', raw, 0, len(raw), 'NUL 문자가 든다')
    return text


def read_prompt(path):
    """프롬프트 파일 → (글, None), 못 넘기면 (None, 까닭). 받는 쪽은 프롬프트를 UTF-8 로 받는다 — PowerShell 5.1 의
    `Set-Content` 기본값(ANSI)으로 쓴 파일은 글자가 깨진 채 넘어가 답이 조용히 틀어진다. 그래서 `decode_prompt` 가 받는
    인코딩만 넘기고, 러너는 이 글을 UTF-8 로 옮겨 넘긴다(파일을 다시 안 읽는다)."""
    if not os.path.isfile(path):
        return None, f'프롬프트 파일이 없다 — {path}'
    try:
        with open(path, 'rb') as f:
            return decode_prompt(f.read()), None
    except OSError as e:
        return None, f'프롬프트 파일을 못 읽었다 — {e}'
    except UnicodeDecodeError:
        return None, (f'프롬프트 파일이 받는 인코딩이 아니다 — {PROMPT_ENCODINGS} 만 받는다. '
                      f'PowerShell 5.1 이면 `Set-Content -Encoding utf8` 로 쓴다: {path}')


def base_parser(description, cwd_help):
    """러너 셋이 같이 받는 인자 넷(`-h` · `--prompt-file` · `--out` · `--cwd`)을 단 인자 가르개 — 나머지 인자는 러너가 제
    차례로 잇는다(`--timeout` 도 러너마다 뜻 · 자리가 달라 러너가 단다)."""
    ap = Parser(add_help=False, formatter_class=HelpFormat, description=description)
    ap.add_argument('-h', '--help', action='store_true', help='이 도움말을 표준 출력에 찍고 끝낸다(파일은 안 쓴다)')
    ap.add_argument('--prompt-file', required=True, metavar='FILE', help='맡길 프롬프트 파일 — 받는 인코딩은 아래 「프롬프트 파일」')
    ap.add_argument('--out', required=True, metavar='FILE', help='답 파일 — 어느 갈래로 끝나든 답과 끝 줄을 여기 쓴다')
    ap.add_argument('--cwd', required=True, metavar='DIR', help=cwd_help)
    return ap


def npm_head(name, package):
    """띄울 머리 — PATH 의 `name` 이 npm 셔틀(`.cmd`)이면 곁의 꾸러미(`node_modules/<package>`)의 `package.json` `bin` 을
    따라간다: JS 면 node 로, 실행 파일이면 그대로. 셔틀은 인자를 cmd.exe 에 거쳐 넘겨(8191자 · `& | % ^` 해석) 건너뛴다.
    꾸러미가 판을 올리며 JS 에서 네이티브 실행 파일로 옮겨도(claude-code 가 옮겼다) 따라간다. 셔틀이 아니면 찾은 그것, 못
    찾거나 못 풀면 None."""
    found = shutil.which(name)
    if not found:
        return None
    if not found.lower().endswith(SHIM_EXT):
        return [found]
    pkg = os.path.join(os.path.dirname(found), 'node_modules', *package)
    try:
        with open(os.path.join(pkg, 'package.json'), encoding='utf-8') as f:
            bin_field = json.load(f).get('bin')
    except (OSError, ValueError):
        return None
    rel = bin_field.get(name) if isinstance(bin_field, dict) else bin_field
    target = os.path.join(pkg, rel) if isinstance(rel, str) else ''
    if not os.path.isfile(target):
        return None
    if not target.lower().endswith(JS_EXT):
        return [target]
    node = shutil.which('node')
    return [node, target] if node else None


def watch(cmd, cwd, env, stdin, raw_path, err_path, timeout):
    """받는 쪽을 한 번 띄워 끝날 때까지(넘으면 `timeout` 초에 끊는다) 지켜본다 — (갈래, 종료 코드, 날 출력 이벤트, stderr 글).
    갈래는 다 돌았으면 None(가르는 것은 러너의 판정이다), 끊었으면 'timeout', 못 띄웠으면 'spawn'(stderr 글 자리에 까닭).
    답은 파이프가 아니라 파일로 받는다 — 파이프를 안 비운 채 기다리면 큰 답에서 멈춘다."""
    started = time.monotonic()
    status = None
    with open(raw_path, 'wb') as raw, open(err_path, 'wb') as err:
        try:
            proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=stdin, stdout=raw, stderr=err, creationflags=CREATE_NO_WINDOW)
        except OSError as e:
            return 'spawn', None, [], str(e)
        while proc.poll() is None:
            if time.monotonic() > started + timeout:
                kill_tree(proc)
                status = 'timeout'
                break
            time.sleep(POLL_SEC)
    with open(err_path, encoding='utf-8', errors='replace') as f:
        err_text = f.read()
    return status, proc.returncode, read_jsonl(raw_path), err_text


def wrap_up(status, reason, err_text, raw_path, err_path):
    """한 판의 끝 손질 → 까닭. `ok` 면 날 출력 · stderr 파일을 지우고 까닭은 그대로, 아니면 파일은 남기고(끝 줄 `raw=` 가
    가리킨다) 까닭 뒤에 stderr 꼬리(`STDERR_TAIL_CHARS`)를 잇는다."""
    if status == 'ok':
        remove(raw_path, err_path)
        return reason
    return '\n'.join(s for s in (reason, err_text[-STDERR_TAIL_CHARS:].strip()) if s)


def remove(*paths):
    """파일을 지운다 — None 은 건너뛰고, 없거나 못 지우는 것은 그대로 둔다."""
    for path in paths:
        try:
            if path:
                os.remove(path)
        except OSError:
            pass


def write_answer(path, status, answer, footer, reason='', failure=None):
    """답 파일 — `ok` 면 답 · 빈 줄 · 끝 줄, 아니면 답 · 까닭 · 끝 줄. 날 출력은 길어 옮기지 않는다 — 그 자리는 끝 줄이 든다.
    실패 때의 글을 달리 짓는 러너는 `failure` 로 준다(그 글 · 끝 줄)."""
    if status == 'ok':
        write(path, f'{answer.rstrip()}\n\n{footer}\n')
    elif failure is None:
        write(path, f'{answer.rstrip()}\n{reason}\n{footer}\n')
    else:
        write(path, f'{failure}\n{footer}\n')


def kill_tree(proc):
    """띄운 프로세스와 그 밑 자식까지 같이 끊는다 — 머리만 끊으면 자식이 남는다."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)],
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
    else:
        proc.kill()
    proc.wait()


def read_jsonl(path):
    """한 줄에 JSON 하나인 날 출력 → 객체 목록. `{` 로 안 여는 줄과 못 푸는 줄은 건너뛰고, 파일이 없으면 빈 목록이다."""
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


def footer_line(footer, fields, status, cells):
    """끝 줄 — `<footer> <갈래>` 뒤에 칸을 `fields`(이름, 뜻)의 차례로 ` · ` 로 잇는다. `cells` 는 {칸 이름: 꼴을 갖춘 글}이고 있는
    칸만 든다. 이름이 `fields` 에 없으면 KeyError — 칸을 더하면서 뜻을 안 다는 일을 막는다."""
    unknown = set(cells) - {name for name, _ in fields}
    if unknown:
        raise KeyError(f'끝 줄 칸의 표에 없는 칸: {sorted(unknown)}')
    return ' · '.join([f'{footer} {status}'] + [cells[name] for name, _ in fields if name in cells])


def exit_table(exit_codes, words):
    """종료 코드 표의 줄들 — `exit_codes` 에서 같은 코드를 쓰는 이름끼리 묶고 `words` 로 뜻을 단다. 이름은 끝 줄의 갈래다."""
    names = {}
    for name, code in exit_codes.items():
        names.setdefault(code, []).append(name)
    joined = {code: ' · '.join(ns) for code, ns in names.items()}
    width = max(len(j) for j in joined.values())
    return [f'  {code}  {joined[code]:<{width}}  ' + ' · '.join(words.get(n, n) for n in names[code])
            for code in sorted(names)]


def show_help(ap, epilog, ok):
    """`--help` — 도움말을 표준 출력에 찍고 `ok`(종료 코드)를 낸다. 인자 검사보다 앞서고 파일은 안 쓴다."""
    ap.epilog = epilog
    out = sys.stdout
    if out is None:   # pythonw 에는 표준 출력이 없다 — 찍을 곳이 없다
        return ok
    if hasattr(out, 'reconfigure'):   # 윈도 파이프의 기본 인코딩(cp949)은 `—` 를 못 적어 죽는다 — 에이전트 셸은 UTF-8 로 읽는다
        out.reconfigure(encoding='utf-8')
    out.write(ap.format_help())
    return ok


def config_dir(env=None):
    """부른 쪽 Claude 의 설정 폴더 — `CLAUDE_CONFIG_DIR` 가 서 있으면 그것, 아니면 홈의 `.claude`."""
    return (os.environ if env is None else env).get(CONFIG_DIR_ENV) or os.path.join(os.path.expanduser('~'), '.claude')


def loopback_proxy(env=None):
    """요청이 루프백 프록시를 지나면 (호스트, 포트) — `ANTHROPIC_BASE_URL` 이 `http://127.0.0.1:<포트>/…` · `localhost` ·
    `[::1]` 일 때만이다. 아니면(사외 · 게이트웨이 직결 · 값이 없다) None."""
    url = (os.environ if env is None else env).get(BASE_URL_ENV) or ''
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return None
    if parts.scheme != 'http' or parts.hostname not in LOOPBACK_HOSTS or not port:
        return None
    return parts.hostname, port


def caller_lane(session, marker, config_dir):
    """이 러너를 부른 레인의 번호 — 그 세션의 레인 기록 가운데 끝 조각의 도구 호출(`command` 칸)에 `marker`(이 러너의 답 파일
    이름)가 든 기록이 꼭 하나면 그 번호, 없거나 둘 이상이면 빈 글(메인이 불렀거나 못 가른다 — 레인은 어림하지 않는다)."""
    if not (marker and SESSION_RE.fullmatch(session or '')):
        return ''
    pattern = os.path.join(glob.escape(long_path(config_dir)), 'projects', '*', session, 'subagents', 'agent-*.jsonl')
    found = set()
    for path in glob.glob(pattern):
        name = LANE_FILE_RE.fullmatch(os.path.basename(path))
        if name and _calls_with(path, marker):
            found.add(name.group(1))
    return found.pop() if len(found) == 1 else ''


def long_path(path):
    """윈도에서는 긴 경로 머리(`\\\\?\\`)를 단 절대 경로 — 작업 자리 이름을 접은 기록 폴더 이름이 길어 레인 기록의 경로가 260 자를
    넘으면 머리 없이는 `glob` 이 조용히 빈손으로 온다. 다른 OS 는 그대로."""
    if os.name != 'nt':
        return path
    full = os.path.abspath(path)
    if full.startswith('\\\\?\\'):
        return full
    return '\\\\?\\UNC\\' + full[2:] if full.startswith('\\\\') else '\\\\?\\' + full


def _calls_with(path, marker):
    """기록 끝 조각의 assistant 줄에 `marker` 를 `command` 에 든 도구 호출이 있나. 못 읽는 줄 · 잘린 첫 줄은 건너뛴다."""
    try:
        with open(path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - LANE_TAIL_BYTES))
            tail = f.read().decode('utf-8', errors='replace')
    except OSError:
        return False
    for line in tail.splitlines():
        if marker not in line or '"tool_use"' not in line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get('message') if isinstance(entry, dict) and entry.get('type') == 'assistant' else None
        content = message.get('content') if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            command = (block.get('input') or {}).get('command') if isinstance(block, dict) and block.get('type') == 'tool_use' else None
            # 이름 앞뒤가 이름 글자가 아니어야 한다 — `final_answer.md` 가 `answer.md` 로 걸리지 않게
            if isinstance(command, str) and re.search(rf'(?<![\w.-]){re.escape(marker)}(?![\w.-])', command):
                return True
    return False


def notify_waiting(target, session, lane):
    """루프백 프록시에 한 번 알린다 — 답의 상태 코드, 못 닿았으면 None. `http.client` 는 시스템 프록시 설정을 안 탄다(루프백을
    시스템 프록시로 돌리면 제 길을 끊는다)."""
    host, port = target
    conn = http.client.HTTPConnection(host, port, timeout=WAIT_TIMEOUT_SEC)
    try:
        body = json.dumps({'session': session, 'lane': lane}).encode('utf-8')
        conn.request('POST', WAIT_PATH, body=body, headers={'Content-Type': 'application/json'})
        response = conn.getresponse()
        response.read()
        return response.status
    except (OSError, http.client.HTTPException, ValueError):
        return None
    finally:
        conn.close()


class waiting_notice:
    """러너가 도는 동안 곁 스레드가 `WAIT_EVERY_SEC` 마다 부른 대화를 프록시에 알린다 — 부른 쪽이 Claude 이고(세션 번호가 환경에
    선다) 요청이 루프백 프록시를 지날 때만. 레인 번호는 그 레인의 기록에서 찾고, 못 찾으면 세션만 알린다(프록시는 그 세션의
    메인을 잇는다). 러너가 끝나거나 죽으면 알림이 멎고, 프록시는 그 뒤 데우기 세 번에서 옛 규칙대로 멈춘다 — 끝을 따로 안
    알린다. 스레드는 데몬이라 러너의 끝을 붙잡지 않고, 어떤 실패도 러너 쪽으로 새지 않는다(답 파일에 아무것도 안 쓴다)."""

    def __init__(self, out, env=None, every=WAIT_EVERY_SEC):
        env = os.environ if env is None else env
        self.target = loopback_proxy(env)
        self.session = env.get(SESSION_ENV) or ''
        self.marker = os.path.basename(out or '')
        self.config_dir = config_dir(env)
        self.every = every
        self.stop = threading.Event()
        self.thread = None

    def __enter__(self):
        if self.target and SESSION_RE.fullmatch(self.session):
            self.thread = threading.Thread(target=self._loop, daemon=True, name='runner-wait')
            self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        return False

    def _loop(self):
        lane, scans = '', 0
        try:
            while True:
                if not lane and scans < LANE_SCANS:
                    lane, scans = caller_lane(self.session, self.marker, self.config_dir), scans + 1
                notify_waiting(self.target, self.session, lane)
                if self.stop.wait(self.every):
                    return
        except Exception:   # 알림은 덤이다 — 무엇이 지든 러너는 그대로 돈다
            return


def main(build_parser, help_epilog, run, footer, exit_codes):
    """러너 한 판 — 인자를 가르고 `run(a)` 의 종료 코드를 낸다. `--help` 는 인자 검사보다 앞선다. 인자가 틀렸거나 `run` 이
    멈추면 그 까닭을 `--out` 파일의 끝 줄(`<footer> usage · …` · `<footer> failed · …`)로 남긴다 — 부른 쪽은 그것만 본다."""
    ap = build_parser()
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        return show_help(ap, help_epilog(), exit_codes['ok'])
    try:
        a = ap.parse_args(args)
    except Usage as e:
        out = out_arg(args)
        if out:
            try:
                write(out, f'{footer} usage · 인자가 틀렸다 — {e}\n')
            except OSError:
                pass
        return exit_codes['usage']
    try:
        with waiting_notice(getattr(a, 'out', None)):
            return run(a)
    except Exception as e:   # 어디서 멈췄든 답 파일과 끝 줄을 남긴다
        write(a.out, f'{traceback.format_exc()}\n{footer} failed · 러너가 멈췄다 — {type(e).__name__}: {e}\n')
        return exit_codes['failed']
