"""Codex 가 우리 훅을 실제로 믿나를 재고, 우리 훅에만 신뢰를 적는다 — Codex 제 설정 쓰기로. 폴더 신뢰(projects)도 같은 통로로 적는다.

    python -X utf8 codex-hook-trust.py status   --example codex-hooks.example.toml [--codex-home <홈>] [--codex <실행 파일>]
    python -X utf8 codex-hook-trust.py trust    --example codex-hooks.example.toml [--codex-home <홈>] [--codex <실행 파일>]
    python -X utf8 codex-hook-trust.py projects [--codex-home <홈>] [--codex <실행 파일>] <저장소 뿌리>...

홈은 `--codex-home` → 환경변수 `CODEX_HOME` → `~/.codex` 차례다(뒤의 둘은 Codex 가 제 홈을 고르는 차례와 같다).
Codex 는 PATH 의 `codex.cmd` · `codex` 에서 찾고, `--codex` 가 그 자리를 못박는다(검사 · 진단용).

**왜 있나.** 병합기(`codex-hook-install.py`)가 배선을 세워도 Codex 는 사람이 검토해 신뢰한 사용자 훅만 돌린다 —
대화형 시작에서는 신뢰를 묻지만 `codex exec` 는 신뢰 안 된 훅을 **말없이** 건너뛴다(codex-rs
`hooks/src/engine/discovery.rs` 의 「켜졌고 managed 이거나 trusted 일 때만 싣는다」). 그래서 설치기의 끝 검증은 설정의 글자가
아니라 Codex 가 읽은 신뢰 상태를 재야 하고, Codex 를 고른 설치는 그 신뢰까지 적어야 고른 기능이 선다(결정 0106).

**어디에 묻고 어디로 쓰나.** 신뢰를 적는 문서화된 CLI 는 없다. Codex 의 TUI 가 「Trust all」에서 보내는 것을 같은 통로로
보낸다(codex-rs `tui/src/hooks_rpc.rs` 의 `write_hook_trusts`) — stdio `codex app-server`(실험 단계 API):
  `config/read`(사용자 층의 판) → `hooks/list`(열쇠 · 현재 해시 · 신뢰 상태) →
  `config/batchWrite` {keyPath "hooks.state", value {<열쇠>: {trusted_hash: <현재 해시>}}, upsert, expectedVersion} →
  `hooks/list` 를 다시 불러 trusted 로 읽히나 확인한다.
해시는 우리가 셈하지 않는다 — Codex 가 낸 값을 그대로 되돌려 적을 뿐이다. 파일도 우리가 안 쓴다 — Codex 의 쓰는 자가 쓴다.
판을 먼저 읽고 목록을 뒤에 읽는다 — 그 사이나 쓰기 직전에 누가 설정을 고치면 쓰기가 판 어긋남으로 거절된다. 그때는
한 번 다시 읽고 다시 쓴다(codex-rs `app-server/src/request_processors/bedrock_auth.rs` 가 같은 자리에서 한 번 다시 한다).

**무엇이 우리 것인가.** 병합기의 판정(`ours_hook` — 명령이 씨앗 자리의 우리 몸통을 부르나)을 그대로 불러 쓴다.
Codex 가 내는 `command` 는 이 기계의 실효 명령(윈도면 `commandWindows`)이고, 우리 표지는 두 꼴에 다 든다.

**신뢰를 안 적는 것.**
  - 우리 것이 아닌 훅 — 사람의 훅은 사람이 Codex 에서 검토한다
  - 사람이 끈 우리 훅(`enabled = false`) — 끈 뜻을 신뢰로 덮지 않는다. `disabled` 로 알린다
  - 사용자 층 밖의 훅 · 관리 훅 — 신뢰를 적을 자리가 아니다(관리 훅은 신뢰 없이 돈다)

표준 출력 — 한 줄에 하나:
  EXPECTED=<n>                          예시에 든 우리 훅 수 — 설치기의 분모
  CODEX_HOME=<경로>                      Codex 가 스스로 밝힌 홈(initialize 응답) — 어느 설정을 쟀나
  TRUSTED_NOW=<이벤트>|<matcher>|<실효 명령>  (trust) 이번에 신뢰를 적고 Codex 가 trusted 로 다시 읽은 훅 — 기록에 그대로 찍는다
  HOOK=<이벤트>|<matcher>|<상태>          Codex 가 싣는 우리 훅마다, Codex 의 순서로. 상태 = trusted · untrusted · modified ·
                                        disabled(사람이 껐다) · managed. matcher 와 명령에는 `|` 가 든다 — 이벤트는 첫 `|` 앞,
                                        상태는 마지막 `|` 뒤에서 읽는다
  WIRED=<n>                             Codex 가 싣는 우리 훅 수
  TRUSTED=<n>                           그 가운데 Codex 가 돌리는 것(켜졌고 trusted · managed)
  NONE_LISTED=<까닭>                     우리 훅을 하나도 안 실을 때만 —
                                          no-config      `<홈>/config.toml` 이 없다
                                          not-in-config  설정에 우리 훅이 없다(배선이 빠졌다 — 병합기의 SKIP 을 본다)
                                          not-loaded     설정에는 있는데 Codex 가 안 싣는다(훅 기능이 꺼졌거나 관리 정책
                                                         `allow_managed_hooks_only` 가 사용자 훅을 막는다)
                                          unreadable     설정을 TOML 로 못 읽는다
  UNMEASURED=<종류>:<말>                 못 쟀다 — 종료 코드 3. 설치기는 「못 잼」으로 알리고 초록으로 세지 않는다.
                                        종류 = codex-absent · start-failed · exited · timeout · rpc-error · shape · list-error
  ERROR=<종류>:<말>                      예시를 못 읽었거나, 신뢰를 못 적었거나, 적은 뒤 확인이 안 됐다 — 종료 코드 1.
                                        종류 = example · merger · write · version-conflict · verify (그 밖은 예외 이름)

**폴더 신뢰(projects).** Codex 는 연 자리의 git 뿌리를 `[projects.'<자리>'] trust_level` 에서 찾아, 없으면 신뢰를 묻는다.
받은 저장소 뿌리마다 `trust_level = "trusted"` 를 적는다. 찾는 손이 둘이라 윈도에서는 열쇠도 두 벌이다(결정 0121):
  - 본체(CLI · VS Code 확장) — 소문자 · 역슬래시(Codex 가 프로젝트 층을 막을 때 「이 자리를 신뢰로 더하라」고 대는 꼴).
    본체는 역슬래시 열쇠를 대소문자 없이 맞추고 `/` 로 적힌 열쇠는 안 맞춘다 — 서 있나도 그 규칙으로 가린다.
  - 데스크탑 앱 — 폴더 선택기가 준 디스크 철자를 철자 그대로 찾는다(데스크탑 26.1007.2314.0 의 폴더 동의 `confirm` 이
    `config/read` 의 projects 를 JS 객체로 찾는다). 서 있나도 철자 그대로 가린다.
  윈도 밖에서는 두 열쇠가 같아 하나다. 사용자 설정 파일을 먼저 TOML 로 읽어 다 서 있으면 app-server 를 안 띄운다. 쓰기는 훅
  신뢰와 같은 통로다:
  `config/read`(사용자 층의 판 · projects) → `config/batchWrite` {keyPath "projects", value {<자리>: {trust_level: "trusted"}},
  upsert, expectedVersion} → `config/read` 를 다시 불러 사용자 층에서 trusted 로 읽히나 확인한다.
  사람이 `untrusted` 로 둔 자리는 안 덮는다 — 대소문자만 다른 열쇠 가운데 하나라도 `untrusted` 면 그 자리는 어느 철자로도 안
  적는다(Codex 도 그 자리는 안 묻는다).
  PROJECT=<열쇠>|<상태>                  받은 뿌리마다(같은 자리는 한 번) 열쇠마다 · 상태 = trusted(이미 섰다) · trusted-now(이번에
                                        적고 Codex 가 다시 읽었다) · untrusted(사람이 정했다 — 본체 열쇠 한 줄로 내고 안 덮었다)
  CODEX_HOME=<경로>                      app-server 를 띄운 판만 — Codex 가 스스로 밝힌 홈
  UNMEASURED · ERROR                    위와 같은 꼴 · ERROR 종류에 config(설정을 TOML 로 못 읽는다 — 안 쓴다)가 는다.
                                        부르는 자가 app-server 를 띄우지 말라 했는데(`plant_projects(start=False)`) 파일로
                                        못 가리면 UNMEASURED=tomllib 이다(파이썬 3.11 미만)

**데스크탑 프로젝트(local-projects).** 명령은 없다 — 세션 훅이 `plant_desktop_projects` 를 불러 저장소 뿌리를 Codex
데스크탑의 프로젝트 목록(제 상태 파일)에 더한다. app-server 를 안 거치고 파일을 쓴다(그 절 머리말 · 결정 0126).
**데스크탑 권한 모드(agent-mode).** 명령은 없다 — 세션 훅이 `plant_desktop_agent_mode` 를 불러 같은 상태 파일의 로컬 호스트 권한을
지금 값과 상관없이 「나 대신 승인」으로 쓴다(그 절 머리말 · 결정 0127).

종료 코드: 0 쟀다(trust 면 적을 것을 다 적고 다시 읽어 확인했다) · 1 ERROR · 2 인자가 틀렸다(argparse) · 3 UNMEASURED.
⚠ UNMEASURED 가 2 가 아닌 까닭 — argparse 가 인자 오류에 2 를 쓴다. 부르는 쪽의 실수와 Codex 를 못 잰 것이 한 값이면 안 갈린다.
⚠ trust 의 앞단(목록)에서 못 쟀으면 UNMEASURED 다 — 아무것도 안 썼다. 쓰기부터는 무엇이 막혀도 ERROR 다.
⚠ app-server 가 뜨면 Codex 는 홈에서 제 일(플러그인 동기화 — `<홈>/.tmp/` 등)을 한다. 사람이 Codex 를 켤 때와 같은 일이다.
"""

import argparse
import collections
import contextlib
import importlib.util
import json
import math
import os
import pathlib
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid

try:
    import tomllib
except ImportError:   # 3.10 이하 — 예시를 못 읽으므로 분모가 안 선다
    tomllib = None

MERGER_FILE = 'codex-hook-install.py'   # 우리 훅 판정의 진본 — 이 파일 곁에 같이 실린다
# 첫 기동은 느린 VDI 에서 node · 백신 검사가 겹친다(이 PC 0.162.1 실측: 기동 0.2 초 · 호출 0.1 초 미만)
INIT_TIMEOUT_SEC = 120
CALL_TIMEOUT_SEC = 60
EXIT_GRACE_SEC = 10   # 표준입력을 닫은 뒤 스스로 끝나기를 기다리는 시간 — 넘으면 자식까지 끊는다
POLL_SEC = 0.5
STDERR_TAIL_LINES = 5
DETAIL_MAX = 300   # 한 줄 계약 — 남의 긴 오류문이 줄을 덮지 않게

EXIT_ERROR = 1
EXIT_UNMEASURED = 3

CODEX_NAMES = ('codex.cmd', 'codex')   # 윈도 npm 껍데기가 먼저 — 그 곁의 codex.js 를 node 로 바로 부른다
NPM_ENTRY = ('node_modules', '@openai', 'codex', 'bin', 'codex.js')
NODE = 'node'
APP_SERVER = 'app-server'
CLIENT_INFO = {'name': 'codex-hook-trust', 'version': '1'}
CWD_PREFIX = 'codex-hook-trust-'   # hooks/list 를 묻는 빈 자리 — 프로젝트 층(.codex)이 끼지 않는다
CONFIG_FILE = 'config.toml'
DEFAULT_HOME = '~/.codex'

STATE_KEY_PATH = 'hooks.state'
TRUSTED_HASH = 'trusted_hash'
UPSERT = 'upsert'
USER = 'user'   # 사용자 층 — hooks/list 의 source 와 config/read 층 이름의 type 이 같은 낱말을 쓴다
VERSION_CONFLICT = 'configVersionConflict'
WRITE_ERROR_CODE = 'config_write_error_code'
WRITE_OK = ('ok', 'okOverridden')
WRITE_ATTEMPTS = 2   # 판이 어긋나면 한 번 다시 읽고 다시 쓴다

PROJECTS_KEY_PATH = 'projects'
TRUST_LEVEL = 'trust_level'
LEVEL_TRUSTED, LEVEL_UNTRUSTED = 'trusted', 'untrusted'   # codex-rs `TrustLevel`
P_HAVE, P_NOW, P_KEPT = 'trusted', 'trusted-now', 'untrusted'   # PROJECT= 의 상태

TRUST_STATES = ('managed', 'untrusted', 'trusted', 'modified')   # codex-rs app-server-protocol `HookTrustStatus`
NEEDS_REVIEW = ('untrusted', 'modified')   # TUI 의 `hook_needs_review` 와 같은 둘
RUNS = ('trusted', 'managed')
DISABLED = 'disabled'
HOOK_KEYS = ('key', 'eventName', 'enabled', 'trustStatus', 'currentHash', 'source', 'isManaged')


class Stop(Exception):
    """한 줄 계약으로 끝낸다 — `line` 을 찍고 `code` 로 나간다."""

    def __init__(self, line, code):
        super().__init__(line)
        self.line, self.code = line, code


class Transport(Exception):
    """app-server 와 말이 안 통했다 — 부른 자리가 UNMEASURED 인지 ERROR 인지 정한다."""

    def __init__(self, kind, detail):
        super().__init__(f'{kind}:{detail}')
        self.kind, self.detail = kind, detail


def clip(text):
    return ' '.join(str(text).split())[:DETAIL_MAX]


def unmeasured(kind, detail):
    return Stop(f'UNMEASURED={kind}:{clip(detail)}', EXIT_UNMEASURED)


def error(kind, detail):
    return Stop(f'ERROR={kind}:{clip(detail)}', EXIT_ERROR)


def load_merger():
    path = pathlib.Path(__file__).resolve().with_name(MERGER_FILE)
    sys.dont_write_bytecode = True   # 씨앗 자리는 거울로 깔린다 — 캐시를 흘리지 않는다
    try:
        spec = importlib.util.spec_from_file_location('codex_hook_install', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (OSError, SyntaxError, ImportError) as exc:
        raise error('merger', f'{path}: {exc}') from exc
    return mod


def count_ours(merger, data):
    """TOML 로 읽은 설정(또는 예시)의 `[hooks]` 에서 우리 훅 수 — 병합기가 다루는 이벤트만 센다."""
    hooks = data.get(merger.HOOKS_TABLE) if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return 0
    n = 0
    for ev in merger.EVENTS:
        entries = hooks.get(ev)
        for entry in entries if isinstance(entries, list) else []:
            inner = entry.get(merger.NESTED_HOOKS_KEY) if isinstance(entry, dict) else None
            n += sum(1 for h in inner if merger.ours_hook(h)) if isinstance(inner, list) else 0
    return n


def read_toml(merger, path):
    with open(path, encoding='utf-8') as f:
        return tomllib.loads(f.read().lstrip(merger.BOM))


def expected_count(merger, example):
    if tomllib is None:
        raise error('example', 'tomllib 이 없다 — 파이썬 3.11 이상이 든다')
    try:
        return count_ours(merger, read_toml(merger, example))
    except (OSError, ValueError) as exc:   # TOMLDecodeError 는 ValueError 다
        raise error('example', f'{example}: {exc}') from exc


def codex_command(override):
    """app-server 를 띄울 명령. npm 껍데기면 그 곁의 codex.js 를 node 로 부른다 — 윈도의 .cmd 를 거치지 않는다."""
    if override:
        if not os.path.isfile(override):
            raise unmeasured('codex-absent', override)
        exe = override
    else:
        exe = next(filter(None, map(shutil.which, CODEX_NAMES)), None)
        if exe is None:
            raise unmeasured('codex-absent', 'PATH 에 codex 가 없다')
    entry = os.path.join(os.path.dirname(exe), *NPM_ENTRY)
    node = shutil.which(NODE)
    if node and os.path.isfile(entry):
        return [node, entry, APP_SERVER]
    return [exe, APP_SERVER]


class AppServer:
    """stdio JSON-RPC 로 `codex app-server` 하나와 말한다. 알림과 서버가 먼저 거는 요청은 흘려보낸다."""

    def __init__(self, cmd, home, cwd):
        env = dict(os.environ)
        env['CODEX_HOME'] = home   # 자식에게만 — 이 프로세스의 환경은 그대로다
        extra = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
        try:
            self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      cwd=cwd, env=env, **extra)
        except OSError as exc:
            raise Transport('start-failed', f'{cmd[0]}: {exc}') from exc
        self.lines = queue.Queue()
        self.err = collections.deque(maxlen=STDERR_TAIL_LINES)
        self.next_id = 0
        threading.Thread(target=self._pump, daemon=True).start()
        threading.Thread(target=self._drain, daemon=True).start()

    def _pump(self):
        for line in self.p.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _drain(self):   # 표준 오류를 비워 두지 않으면 관이 차서 서버가 선다
        for line in self.p.stderr:
            self.err.append(line.decode('utf-8', 'replace').strip())

    def _send(self, message):
        try:
            self.p.stdin.write((json.dumps(message) + '\n').encode('utf-8'))
            self.p.stdin.flush()
        except OSError as exc:
            raise Transport('exited', f'보내는 관이 닫혔다({exc}) {self.tail()}') from exc

    def tail(self):
        return ' / '.join(self.err)

    def notify(self, method):
        self._send({'method': method})

    def call(self, method, params, timeout):
        """응답 하나(`result` 나 `error` 가 든 dict)를 돌려준다."""
        i = self.next_id
        self.next_id += 1
        self._send({'id': i, 'method': method, 'params': params})
        deadline = time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise Transport('timeout', f'{method}:{timeout}s')
            try:
                line = self.lines.get(timeout=min(left, POLL_SEC))
            except queue.Empty:
                continue
            if line is None:
                try:
                    rc = self.p.wait(timeout=EXIT_GRACE_SEC)
                except subprocess.TimeoutExpired:
                    rc = '?'
                raise Transport('exited', f'{method}:rc={rc} {self.tail()}')
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if isinstance(msg, dict) and msg.get('id') == i and 'method' not in msg:
                return msg

    def close(self):
        try:
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(timeout=EXIT_GRACE_SEC)
            return
        except subprocess.TimeoutExpired:
            pass
        # npm 껍데기(node)를 거치면 진짜 서버는 그 자식이다 — 껍데기만 끊으면 서버가 남는다
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(self.p.pid), '/T', '/F'], capture_output=True)
        else:   # 새 세션으로 띄웠다 — 그 무리를 통째로 끊는다
            try:
                os.killpg(os.getpgid(self.p.pid), signal.SIGKILL)
            except OSError:
                pass
        try:
            self.p.wait(timeout=EXIT_GRACE_SEC)
        except subprocess.TimeoutExpired:
            self.p.kill()


def result_of(srv, method, params, timeout=CALL_TIMEOUT_SEC):
    """재는 자리의 호출 — 말이 안 통하거나 오류가 오면 UNMEASURED 다."""
    try:
        msg = srv.call(method, params, timeout)
    except Transport as t:
        raise unmeasured(t.kind, t.detail) from t
    if 'error' in msg:
        err = msg['error'] if isinstance(msg['error'], dict) else {}
        raise unmeasured('rpc-error', f'{method}:{err.get("code")}:{err.get("message", msg["error"])}')
    res = msg.get('result')
    if not isinstance(res, dict):
        raise unmeasured('shape', f'{method} 의 result 가 객체가 아니다')
    return res


def list_ours(merger, srv, cwd):
    """`hooks/list` 에서 우리 훅만 Codex 의 순서로. 꼴이 어긋나면 UNMEASURED — 모르는 꼴을 아는 꼴로 읽지 않는다."""
    res = result_of(srv, 'hooks/list', {'cwds': [cwd]})
    data = res.get('data')
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise unmeasured('shape', 'hooks/list 의 data 가 물은 자리 하나짜리 목록이 아니다')
    entry = data[0]
    errors = entry.get('errors')
    if errors:   # 설정을 못 읽었다 — Codex 가 이 자리의 훅을 하나도 못 셌다
        first = errors[0] if isinstance(errors, list) else errors
        raise unmeasured('list-error', first.get('message', first) if isinstance(first, dict) else first)
    hooks = entry.get('hooks')
    if not isinstance(hooks, list):
        raise unmeasured('shape', 'hooks/list 의 hooks 가 목록이 아니다')
    ours = []
    for h in hooks:
        if not isinstance(h, dict) or any(k not in h for k in HOOK_KEYS):
            raise unmeasured('shape', 'hooks/list 의 훅에 아는 칸이 다 없다: ' + json.dumps(h, ensure_ascii=False)[:120])
        if h['trustStatus'] not in TRUST_STATES:
            raise unmeasured('shape', f'모르는 신뢰 상태 {h["trustStatus"]!r}')
        if merger.ours_hook({'command': h.get('command')}):
            ours.append(h)
    return ours


def user_layer(srv):
    """`config/read` 의 사용자 층(프로필 아님) — 판(`version`)과 Codex 가 읽은 설정(`config`)이 든다. 없으면 None(설정 파일이 아직 없다)."""
    res = result_of(srv, 'config/read', {'includeLayers': True})
    layers = res.get('layers')
    if not isinstance(layers, list):
        raise unmeasured('shape', 'config/read 의 layers 가 목록이 아니다')
    users = [layer for layer in layers if isinstance(layer, dict) and isinstance(layer.get('name'), dict)
             and layer['name'].get('type') == USER and layer['name'].get('profile') is None]
    if len(users) > 1 or (users and not isinstance(users[0].get('version'), str)):
        raise unmeasured('shape', 'config/read 의 사용자 층이 하나가 아니거나 판이 없다')
    return users[0] if users else None


def user_version(srv):
    """사용자 층의 판 — 쓰기의 expectedVersion. 사용자 층이 없으면 None."""
    layer = user_layer(srv)
    return layer['version'] if layer else None


def event_label(h):
    """`preToolUse` → `PreToolUse` — 예시와 병합기가 쓰는 이름."""
    name = str(h['eventName'])
    return name[:1].upper() + name[1:]


def state_of(h):
    return DISABLED if not h['enabled'] else h['trustStatus']


def writable(h):
    return h['enabled'] and h['source'] == USER and not h['isManaged'] and h['trustStatus'] in NEEDS_REVIEW


def none_listed_cause(merger, home):
    cfg = os.path.join(home, CONFIG_FILE)
    if not os.path.isfile(cfg):
        return 'no-config'
    try:
        data = read_toml(merger, cfg)
    except (OSError, ValueError):
        return 'unreadable'
    return 'not-loaded' if count_ours(merger, data) else 'not-in-config'


def report(merger, ours, expected, home):
    for h in ours:
        print(f'HOOK={event_label(h)}|{h.get("matcher") or ""}|{state_of(h)}')
    print(f'WIRED={len(ours)}')
    print(f'TRUSTED={sum(1 for h in ours if h["enabled"] and h["trustStatus"] in RUNS)}')
    if not ours and expected:
        print('NONE_LISTED=' + none_listed_cause(merger, home))


def write_edits(srv, edits, version):
    """Codex 의 쓰는 자로 적는다 — 판이 어긋나면 False, 그 밖의 거절은 ERROR."""
    params = {'edits': edits, 'filePath': None, 'expectedVersion': version, 'reloadUserConfig': True}
    try:
        msg = srv.call('config/batchWrite', params, CALL_TIMEOUT_SEC)
    except Transport as t:
        raise error('write', f'{t.kind}:{t.detail}') from t
    if 'error' in msg:
        err = msg['error'] if isinstance(msg['error'], dict) else {}
        data = err.get('data') if isinstance(err.get('data'), dict) else {}
        if data.get(WRITE_ERROR_CODE) == VERSION_CONFLICT:
            return False
        raise error('write', f'{data.get(WRITE_ERROR_CODE) or err.get("code")}:{err.get("message", msg["error"])}')
    res = msg.get('result')
    status = res.get('status') if isinstance(res, dict) else None
    if status not in WRITE_OK:
        raise error('write', f'알 수 없는 쓰기 결과 {status!r}')
    return True


def write_trust(srv, todo, version):
    """우리 훅의 신뢰를 적는다 — Codex 가 낸 현재 해시를 그대로 되돌려 적는다."""
    return write_edits(srv, [{'keyPath': STATE_KEY_PATH, 'mergeStrategy': UPSERT,
                              'value': {h['key']: {TRUSTED_HASH: h['currentHash']} for h in todo}}], version)


def trust(merger, srv, cwd):
    """신뢰를 적고 다시 읽는다 — `(적은 훅, 다시 읽은 우리 훅)`. 적을 것이 없으면 적은 훅은 빈 목록이다."""
    for _ in range(WRITE_ATTEMPTS):
        version = user_version(srv)   # 판이 먼저 — 목록 뒤에 설정이 바뀌면 쓰기가 거절된다
        ours = list_ours(merger, srv, cwd)
        todo = [h for h in ours if writable(h)]
        if not todo:
            return [], ours
        if version is None:
            raise unmeasured('shape', '쓸 훅이 있는데 config/read 에 사용자 층이 없다')
        if write_trust(srv, todo, version):
            break
    else:
        raise error('version-conflict', f'설정이 {WRITE_ATTEMPTS} 번 다 읽은 뒤에 바뀌었다 — 다른 Codex 가 쓰는 중인가 본다')
    try:
        return todo, list_ours(merger, srv, cwd)
    except Stop as s:   # 썼는데 다시 못 읽었다 — 적은 것이 섰는지 모른다
        raise error('verify', s.line.split('=', 1)[1]) from s


def codex_home(given):
    """Codex 의 홈 — 준 자리 → 환경변수 `CODEX_HOME` → `~/.codex` 차례(Codex 가 제 홈을 고르는 차례와 같다)."""
    return os.path.abspath(os.path.expanduser(given or os.environ.get('CODEX_HOME') or DEFAULT_HOME))


@contextlib.contextmanager
def app_server(cmd, home):
    """app-server 하나를 띄워 initialize 까지 마치고 `(서버, initialize 결과, 묻는 빈 자리)` 를 내준다. 띄우기 · 첫 말이 막히면
    UNMEASURED. 나올 때 서버를 끊고 빈 자리를 걷는다."""
    cwd = tempfile.mkdtemp(prefix=CWD_PREFIX)
    try:
        try:
            srv = AppServer(cmd, home, cwd)
        except Transport as t:
            raise unmeasured(t.kind, t.detail) from t
        try:
            init = result_of(srv, 'initialize', {'clientInfo': CLIENT_INFO}, INIT_TIMEOUT_SEC)
            try:
                srv.notify('initialized')
            except Transport as t:
                raise unmeasured(t.kind, t.detail) from t
            yield srv, init, cwd
        finally:
            srv.close()
    finally:
        shutil.rmtree(cwd, ignore_errors=True)


# ── 폴더 신뢰(projects) ──────────────────────────────────────────────────────────────────────────────────
def project_key(path):
    """Codex 본체가 그 자리의 신뢰를 찾는 열쇠 — 윈도면 소문자 · 역슬래시, 그 밖은 경로 그대로."""
    return os.path.normcase(os.path.abspath(path))


def desktop_key(path):
    """Codex 데스크탑이 찾는 열쇠 — 윈도면 디스크에 선 철자(역슬래시), 그 밖은 본체 열쇠와 같다.
    받은 철자가 아니라 디스크의 철자다 — 사람이 친 대소문자로 온 경로도 폴더 선택기가 주는 꼴로 바꾼다."""
    return os.path.realpath(path) if os.name == 'nt' else project_key(path)


def project_levels(projects):
    """{열쇠: trust_level} — 윈도에서는 Codex 본체처럼 열쇠의 대소문자를 안 가린다. `/` 는 그대로 둔다(본체가 그 꼴을 안 맞춘다).
    대소문자만 다른 열쇠가 여럿이면 `untrusted` 가 이긴다 — 사람이 막은 뜻을 다른 철자의 신뢰로 덮지 않는다."""
    levels = {}
    for k, v in (projects.items() if isinstance(projects, dict) else ()):
        if isinstance(v, dict):
            key = k.lower() if os.name == 'nt' else k
            if levels.get(key) != LEVEL_UNTRUSTED:
                levels[key] = v.get(TRUST_LEVEL)
    return levels


def project_states(paths, projects):
    """받은 뿌리마다(같은 자리는 한 번) 열쇠마다 `(열쇠, 상태)` — 상태는 P_HAVE · P_KEPT · None(적을 자리).
    본체 열쇠는 대소문자 없이, 데스크탑 열쇠는 철자 그대로 가린다. 사람이 막은 자리는 본체 열쇠 한 줄(P_KEPT)만 낸다."""
    levels = project_levels(projects)
    exact = projects if isinstance(projects, dict) else {}
    roots = {}
    for p in paths:
        roots.setdefault(project_key(p), p)
    states = []
    for key, path in roots.items():
        level = levels.get(key)
        if level == LEVEL_UNTRUSTED:
            states.append((key, P_KEPT))
            continue
        states.append((key, P_HAVE if level == LEVEL_TRUSTED else None))
        dkey = desktop_key(path)
        if dkey != key:
            entry = exact.get(dkey)
            states.append((dkey, P_HAVE if isinstance(entry, dict) and entry.get(TRUST_LEVEL) == LEVEL_TRUSTED else None))
    return states


def file_projects(home):
    """사용자 설정 파일의 `projects` — 파일이 없으면 빈 표. tomllib 이 없으면 None(파일로는 못 가린다). 못 읽으면 ERROR=config."""
    if tomllib is None:
        return None
    path = os.path.join(home, CONFIG_FILE)
    try:
        with open(path, encoding='utf-8-sig') as f:
            return tomllib.loads(f.read()).get(PROJECTS_KEY_PATH, {})
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:   # TOMLDecodeError 는 ValueError 다
        raise error('config', f'{path}: {exc}') from exc


def layer_projects(layer):
    """사용자 층에서 Codex 가 읽은 `projects` — 층이 없으면 빈 표."""
    config = layer.get('config') if layer else None
    return config.get(PROJECTS_KEY_PATH, {}) if isinstance(config, dict) else {}


def plant_projects(paths, home, codex=None, start=True):
    """받은 저장소 뿌리마다 폴더 신뢰를 본체 · 데스크탑 철자로 적는다 — `((열쇠, 상태) 목록, Codex 가 밝힌 홈 또는 None)`.
    설정 파일로 다 서 있으면 app-server 를 안 띄운다. `start` 가 거짓이면 아예 안 띄우고 파일로 가린 상태를 낸다(None 이 빈 자리).
    못 쟀으면 UNMEASURED · 못 적었으면 ERROR 의 `Stop` 을 올린다 — 쓰기 앞에서 멈춘 판은 아무것도 안 썼다."""
    projects = file_projects(home)
    if projects is not None:
        states = project_states(paths, projects)
        if not start or all(s for _, s in states):
            return states, None
    elif not start:
        raise unmeasured('tomllib', '파이썬 3.11 미만이라 설정 파일로 못 가린다')
    cmd = codex_command(codex)
    # Codex 는 `CODEX_HOME` 이 가리키는 폴더가 없으면 안 뜬다(0.162.1 실측) — 처음 켤 때 제가 짓는 `~/.codex` 를 먼저 짓는다
    try:
        os.makedirs(home, exist_ok=True)
    except OSError as exc:
        raise unmeasured('start-failed', f'{home}: {exc}') from exc
    with app_server(cmd, home) as (srv, init, _):
        shown = str(init['codexHome']) if init.get('codexHome') else None
        for _ in range(WRITE_ATTEMPTS):
            layer = user_layer(srv)   # 판과 projects 를 한 번에 읽는다 — 그 뒤에 설정이 바뀌면 쓰기가 거절된다
            todo = [k for k, s in project_states(paths, layer_projects(layer)) if s is None]
            if not todo:
                return project_states(paths, layer_projects(layer)), shown
            if write_edits(srv, [{'keyPath': PROJECTS_KEY_PATH, 'mergeStrategy': UPSERT,
                                  'value': {k: {TRUST_LEVEL: LEVEL_TRUSTED} for k in todo}}],
                           layer['version'] if layer else None):
                break
        else:
            raise error('version-conflict', f'설정이 {WRITE_ATTEMPTS} 번 다 읽은 뒤에 바뀌었다 — 다른 Codex 가 쓰는 중인가 본다')
        try:
            after = project_states(paths, layer_projects(user_layer(srv)))
        except Stop as s:   # 썼는데 다시 못 읽었다 — 적은 것이 섰는지 모른다
            raise error('verify', s.line.split('=', 1)[1]) from s
    missing = [k for k, s in after if k in todo and s != P_HAVE]
    if missing:
        raise error('verify', f'{len(missing)} 자리가 적은 뒤에도 trusted 로 안 읽힌다: {missing[0]}')
    return [(k, P_NOW if k in todo else s) for k, s in after], shown


# ── 데스크탑 프로젝트(local-projects) ───────────────────────────────────────────────────────────────────
# Codex 데스크탑의 프로젝트 목록 원본은 제 상태 파일의 `local-projects` 다 — 데스크탑은 뜰 때마다 그 목록을 돌며 app-server
#   짝이 없는 것을 `project/import` 로 맺는다(데스크탑 26.1007 · 결정 0126). app-server 에만 만든 프로젝트는 목록에 안 선다.
# ⚠ **데스크탑이 떠 있으면 안 쓴다** — 앱이 그 파일을 제 기억으로 다시 써, 그 사이 적은 것이 사라진다.
# ⚠ **목록에 한 번 섰던 자리는 사람이 빼면 다시 안 넣는다** — 선 적이 있는 뿌리를 우리 기록(`.paisetup-desktop-projects.json`)에
#   남긴다. 그 기록은 쓴 뒤에도 데스크탑이 안 떠 있다고 가렸을 때만 적는다 — 그 사이 떴으면 적은 것이 사라졌을 수 있어 다음 판이
#   다시 본다. 기록이 없을 때만 「본 적 없음」이다 — 있는데 못 읽으면(잠김 · 깨짐) 아무것도 안 쓰고 미룬다.
# ⚠ **떠 있나를 못 가리면 떠 있는 것으로 본다** — 미루는 쪽이 잃는 것이 없다.
DESKTOP_STATE = '.codex-global-state.json'
DESKTOP_SEEN = '.paisetup-desktop-projects.json'
LOCAL_PROJECTS, PROJECT_ORDER, ROOT_PATHS = 'local-projects', 'project-order', 'rootPaths'
DESKTOP_PACKAGE_DIR, DESKTOP_EXE = '\\openai.codex_', '\\app\\chatgpt.exe'   # 데스크탑 실행 파일 자리 — 소문자로 견준다.
#   ChatGPT 데스크탑과 실행 파일 이름이 같아 꾸러미 폴더로 가른다. 같은 꾸러미의 샌드박스 서비스는 늘 돌아 데스크탑이 아니다
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PID_SLOTS, IMAGE_CHARS = 8192, 32768
DP_HAVE, DP_NOW, DP_GONE = 'listed', 'listed-now', 'removed-by-user'
DP_OFF, DP_NEVER, DP_RUNNING = 'not-windows', 'desktop-never-ran', 'desktop-running'
DP_UNKNOWN, DP_RECORD = 'running-unknown', 'record-unreadable'


def read_seen_list(path):
    """우리 기록(글 목록) — 없으면 빈 것. 못 읽거나 글 목록이 아니면 None 이다(부르는 쪽이 미룬다)."""
    try:
        with open(path, encoding='utf-8') as f:
            got = json.load(f)
    except FileNotFoundError:
        return set()
    except (OSError, ValueError):   # 잠겼다 · 폴더다 · 깨졌다
        return None
    return set(got) if isinstance(got, list) and all(isinstance(s, str) for s in got) else None


def desktop_running():
    """Codex 데스크탑이 떠 있나 — 윈도 밖은 None. 프로세스마다 실행 파일 경로를 묻는다(같은 사용자의 것만 열린다)."""
    if os.name != 'nt':
        return None
    import ctypes
    from ctypes import wintypes
    psapi, k32 = ctypes.WinDLL('psapi'), ctypes.WinDLL('kernel32')
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k32.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                               ctypes.POINTER(wintypes.DWORD))
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    pids, got = (wintypes.DWORD * PID_SLOTS)(), wintypes.DWORD()
    if not psapi.EnumProcesses(pids, ctypes.sizeof(pids), ctypes.byref(got)):
        return None
    buf = ctypes.create_unicode_buffer(IMAGE_CHARS)
    for pid in pids[:got.value // ctypes.sizeof(wintypes.DWORD)]:
        h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            continue
        try:
            n = wintypes.DWORD(IMAGE_CHARS)
            if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                image = buf.value.lower()
                if DESKTOP_PACKAGE_DIR in image and image.endswith(DESKTOP_EXE):
                    return True
        finally:
            k32.CloseHandle(h)
    return False


def compact_json(obj):
    """데스크탑이 제 상태 파일을 쓰는 꼴의 글 — 공백 없는 한 줄 · 끝 줄바꿈 없음 · 한글 그대로."""
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def refuse_non_json(token):
    raise ValueError(f'JSON 이 아닌 값 {token} 이 들었다 — 앱은 이 글을 못 읽는다')


def finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f'수 {text} 가 넘친다 — 우리가 되쓰면 앱이 못 읽는 Infinity 가 된다')
    return value


def read_desktop_state(text):
    """데스크탑 상태 파일의 글을 읽는다. 앱의 `JSON.parse` 가 못 읽는 상수(`NaN` · `Infinity` · `-Infinity`)나 우리가 되쓰면 그
    상수가 되는 수(넘치는 수 — `1e400`)가 들었거나, 우리 꼴(`compact_json`)로 UTF-8 에 못 담는 글자(짝 없는 서로게이트 — 앱은
    `\\ud800` 꼴로 적는다)가 들었으면 ValueError 다.
    ⚠ 파이썬 `json` 은 그 상수를 읽고 그대로 되쓴다 — 앱은 본 파일을 못 읽으면 `.bak` 을 읽고, 둘 다 못 읽으면 빈 상태로 뜬다
    (프로젝트 · 설정이 다 사라진다). 그래서 읽는 자리에서 막는다 — 두 심기가 이 하나로 읽는다."""
    state = json.loads(text, parse_constant=refuse_non_json, parse_float=finite_float)
    try:
        compact_json(state).encode('utf-8')
    except UnicodeEncodeError as exc:
        raise ValueError(f'짝 없는 서로게이트 \\u{ord(exc.object[exc.start]):04x} 가 든 글이라 우리가 되쓸 수 없어 손대지 '
                         '않았다') from None
    return state


def write_compact_json(path, obj):
    """데스크탑이 제 상태 파일을 쓰는 꼴(`compact_json`)로 옆에 쓰고 옮긴다."""
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.paisetup-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(compact_json(obj))
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def plant_desktop_projects(paths, home, running=desktop_running):
    """받은 저장소 뿌리를 Codex 데스크탑 프로젝트로 하나씩 더한다 — `((이름, 상태) 목록, 미룬 까닭 또는 None)`.
    상태 = DP_HAVE(이미 어느 프로젝트의 폴더다) · DP_NOW(이번에 더했다) · DP_GONE(목록에 섰다가 사람이 뺐다 — 안 넣었다).
    미룬 까닭 = DP_OFF(윈도 밖) · DP_NEVER(데스크탑이 아직 상태 파일을 안 지었다) · DP_RUNNING(데스크탑이 떠 있다) ·
    DP_UNKNOWN(떠 있나를 못 가렸다) · DP_RECORD(우리 기록을 못 읽었다) — 미룬 판은 아무것도 안 쓴다.
    상태 파일을 못 읽거나 꼴이 다르거나 JSON 이 아닌 상수 · 못 되쓸 글자가 들었으면(`read_desktop_state`) ERROR=desktop-state 의
    `Stop` — 아무것도 안 썼다. 못 쓰면 ERROR=desktop-write 의 `Stop`."""
    if os.name != 'nt':
        return [], DP_OFF
    path = os.path.join(home, DESKTOP_STATE)
    if not os.path.isfile(path):
        return [], DP_NEVER
    up = running()
    if up is None:
        return [], DP_UNKNOWN
    if up:
        return [], DP_RUNNING
    seen_path = os.path.join(home, DESKTOP_SEEN)
    seen = read_seen_list(seen_path)
    if seen is None:
        return [], DP_RECORD
    try:
        with open(path, encoding='utf-8') as f:
            state = read_desktop_state(f.read())
        projects = state.get(LOCAL_PROJECTS, {}) if isinstance(state, dict) else None
        order = state.get(PROJECT_ORDER, []) if isinstance(state, dict) else None
        if not isinstance(projects, dict) or not isinstance(order, list):
            raise ValueError(f'{LOCAL_PROJECTS} · {PROJECT_ORDER} 꼴이 다르다')
    except (OSError, ValueError) as exc:
        raise error('desktop-state', f'{path}: {exc}') from exc
    listed = {os.path.normcase(r) for p in projects.values() if isinstance(p, dict)
              for r in (p.get(ROOT_PATHS) or []) if isinstance(r, str)}
    roots = {}
    for p in paths:
        d = os.path.realpath(p)
        roots.setdefault(os.path.normcase(d), d)
    now_ms = int(time.time() * 1000)
    states, added = [], []
    for key, root in roots.items():
        name = os.path.basename(root)
        if key in listed:
            states.append((name, DP_HAVE))
        elif key in seen:
            states.append((name, DP_GONE))
        else:
            new_id = str(uuid.uuid4())
            projects[new_id] = {'id': new_id, 'name': name, ROOT_PATHS: [root], 'createdAt': now_ms, 'updatedAt': now_ms}
            order.append(new_id)
            added.append(key)
            states.append((name, DP_NOW))
    if added:
        state[LOCAL_PROJECTS], state[PROJECT_ORDER] = projects, order
        try:
            write_compact_json(path, state)
        except OSError as exc:
            raise error('desktop-write', f'{path}: {exc}') from exc
    new_seen = seen | {k for k in roots if k in listed} | set(added)
    if new_seen != seen and running() is False:   # 떴거나 못 가렸으면 안 남긴다 — 다음 판이 다시 본다
        with contextlib.suppress(OSError):   # 못 적으면 다음 판이 목록에 선 것을 보고 다시 적는다
            write_compact_json(seen_path, sorted(new_seen))
    return states, None


# ── 데스크탑 권한 모드(agent-mode) ─────────────────────────────────────────────────────────────────────────────
# 데스크탑의 권한 고르기 값은 제 상태 파일의 `electron-persisted-atom-state` → `agent-mode-by-host-id`(호스트마다)에 선다. 그 호스트의
#   값이 없으면 새 대화는 `config.toml` 에서 고른 기본을 쓰고(`approvals_reviewer` 가 검토자를 대면 「나 대신 승인」), 윈도 샌드박스 설정을
#   마치기 전에는 `read-only` 다. 앱이 그 칸에 쓰는 때는 사람이 고를 때와, 로그인 뒤 샌드박스 설정을 마칠 때(`auto` — 「승인 요청」 ·
#   지금 값과 상관없이 덮는다) 둘이다(데스크탑 26.1007 번들 · 결정 0127 「Codex 데스크탑의 기본 권한」).
# ⚠ **로컬 호스트의 그 한 칸만 「나 대신 승인」으로 쓴다 — 지금 값이 무엇이든**(없음 · `auto` · 그 밖). 앱이 적은 값과 사람이 고른 값이
#   글자로 안 갈리고, 이 칸은 이 기능 하나만 든다(사용자 결정 2026-10-14). 기록은 안 남긴다 — 설치마다 다시 쓴다.
# ⚠ **상태 파일이 없으면 안 짓는다** — 지으면 앱이 첫 실행 준비를 건너뛰고, 심은 값도 로그인 뒤 샌드박스 설정이 덮는다.
# ⚠ **떠 있으면 안 쓴다** — 앱은 그 파일을 다시 안 읽고 저장 때마다 제 기억을 통째로 써, 그 사이 적은 것이 사라진다.
# ⚠ **그 칸 밖의 바이트는 그대로다** — 앱이 쓰는 꼴(`JSON.stringify` — 공백 없는 한 줄)로 되짜 원래 글과 같을 때만 쓴다. 다르면 안 쓰고
#   진다 — 앱이 쓴 글에도 파이썬 `json` 이 달리 적는 꼴(짝 없는 서로게이트의 `\u` 꼴 · `0.00001` 같은 작은 수)이 들고, 손으로 고친
#   글도 다르다. 앱이 저장마다 같은 글을 곁의 `.bak` 에도 쓰므로 우리도 같은 글을 거기 쓴다
#   (앱은 본 파일을 못 읽을 때만 `.bak` 을 읽는다 — 본 파일이 깨졌을 때 옛 값으로 돌아가지 않게 한다).
DESKTOP_ATOMS, AGENT_MODES, LOCAL_HOST = 'electron-persisted-atom-state', 'agent-mode-by-host-id', 'local'
MODE_APPROVE_FOR_ME = 'guardian-approvals'
DESKTOP_BACKUP_SUFFIX = '.bak'
DM_NOW, DM_HAVE = 'planted-now', 'approve-for-me'


def plant_desktop_agent_mode(home, running=desktop_running):
    """데스크탑 로컬 호스트의 권한 모드를 「나 대신 승인」으로 쓴다 — `(상태 또는 None, 미룬 까닭 또는 None)`.
    상태 = DM_NOW(다른 값이었거나 없어 썼다) · DM_HAVE(이미 그 값이다 — 안 썼다). 미룬 까닭 = `plant_desktop_projects` 의 OFF ·
    NEVER(상태 파일이 없다 — 안 짓는다) · RUNNING · UNKNOWN — 미룬 판은 아무것도 안 쓴다.
    못 읽거나 꼴이 다르거나 JSON 이 아닌 상수 · 못 되쓸 글자가 들었거나(`read_desktop_state`) 앱의 꼴로 되짜지 않으면
    ERROR=desktop-state · 못 쓰면 ERROR=desktop-write 의 `Stop` — 본 파일도 `.bak` 도 안 바뀌었다."""
    if os.name != 'nt':
        return None, DP_OFF
    path = os.path.join(home, DESKTOP_STATE)
    if not os.path.isfile(path):
        return None, DP_NEVER
    up = running()
    if up is None:
        return None, DP_UNKNOWN
    if up:
        return None, DP_RUNNING
    try:
        with open(path, encoding='utf-8', newline='') as f:
            raw = f.read()
        state = read_desktop_state(raw)
        if not isinstance(state, dict):
            raise ValueError('글 전체가 객체가 아니다')
        atoms = state.get(DESKTOP_ATOMS, {})
        modes = atoms.get(AGENT_MODES, {}) if isinstance(atoms, dict) else None
        if not isinstance(modes, dict):
            raise ValueError(f'{DESKTOP_ATOMS} · {AGENT_MODES} 꼴이 다르다')
        if compact_json(state) != raw:
            raise ValueError('이 상태 파일을 바이트 그대로 되쓸 수 없어 손대지 않았다(앱이 쓴 글에도 우리가 달리 적는 글자 · 숫자 꼴이 '
                             '들 수 있다) — 권한은 앱에서 고르면 된다')
    except (OSError, ValueError) as exc:   # UnicodeDecodeError · JSONDecodeError 는 ValueError 다
        raise error('desktop-state', f'{path}: {exc}') from exc
    if modes.get(LOCAL_HOST) == MODE_APPROVE_FOR_ME:
        return DM_HAVE, None
    modes[LOCAL_HOST] = MODE_APPROVE_FOR_ME
    atoms[AGENT_MODES], state[DESKTOP_ATOMS] = modes, atoms
    try:
        write_compact_json(path, state)
    except (OSError, ValueError) as exc:   # 못 담는 글자(짝 없는 서로게이트)는 ValueError 다 — 옆에 쓰고 옮겨 본 파일은 그대로다
        raise error('desktop-write', f'{path}: {exc}') from exc
    with contextlib.suppress(OSError):   # 앱도 `.bak` 쓰기가 지면 알리고 간다 — 본 파일이 섰으니 앱은 그것을 읽는다
        write_compact_json(path + DESKTOP_BACKUP_SUFFIX, state)
    return DM_NOW, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=('status', 'trust', 'projects'))
    ap.add_argument('paths', nargs='*', help='projects — 폴더 신뢰를 적을 저장소 뿌리')
    ap.add_argument('--example', help='status · trust — 우리 훅의 분모를 세는 예시')
    ap.add_argument('--codex-home')
    ap.add_argument('--codex', help='codex 실행 파일을 못박는다(검사 · 진단용). 없으면 PATH 에서 찾는다')
    args = ap.parse_args()
    if args.mode == 'projects' and not args.paths:
        ap.error('projects 는 저장소 뿌리를 하나 이상 받는다')
    if args.mode != 'projects' and (not args.example or args.paths):
        ap.error(f'{args.mode} 는 --example 을 받고 저장소 뿌리는 안 받는다')
    try:
        if args.mode == 'projects':
            states, shown = plant_projects(args.paths, codex_home(args.codex_home), args.codex)
            if shown:
                print(f'CODEX_HOME={shown}')
            for key, state in states:
                print(f'PROJECT={key}|{state}')
            return 0
        merger = load_merger()
        expected = expected_count(merger, args.example)
        print(f'EXPECTED={expected}')
        home = codex_home(args.codex_home)
        with app_server(codex_command(args.codex), home) as (srv, init, cwd):
            if init.get('codexHome'):   # 「안 실림」의 까닭은 Codex 가 실제로 읽은 홈에서 가린다
                home = str(init['codexHome'])
                print(f'CODEX_HOME={home}')
            if args.mode == 'status':
                report(merger, list_ours(merger, srv, cwd), expected, home)
                return 0
            written, after = trust(merger, srv, cwd)
            now = {h['key']: h for h in after}
            confirmed = [now[h['key']] for h in written if now.get(h['key'], {}).get('trustStatus') == 'trusted']
            for h in confirmed:
                print(f'TRUSTED_NOW={event_label(h)}|{h.get("matcher") or ""}|{h.get("command", "")}')
            report(merger, after, expected, home)
            if len(confirmed) != len(written):
                raise error('verify', f'{len(written) - len(confirmed)} 개가 적은 뒤에도 trusted 로 안 읽힌다')
            return 0
    except Stop as s:
        print(s.line)
        return s.code
    except Exception as exc:   # 설치기와의 약속은 한 줄이다 — 트레이스백으로 죽으면 까닭이 안 읽힌다
        print('ERROR=' + type(exc).__name__ + ':' + clip(exc))
        return EXIT_ERROR


if __name__ == '__main__':
    sys.exit(main())
