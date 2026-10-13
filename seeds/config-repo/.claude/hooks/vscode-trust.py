"""VS Code 의 작업 영역 신뢰 목록에 작업 루트 저장소를 더한다 — 세션 훅이 `plant_trusted_folders` 를 부르고, 설치기는 심은 기록의 수를 묻는다.

    python -X utf8 vscode-trust.py status

**왜 있나.** VS Code 는 폴더를 처음 열 때 제 작업 영역 신뢰를 묻고, 답하기 전에는 제한 모드라 신뢰를 밝히지 않은 확장(Claude · Codex ·
agy)이 다 꺼진다. 설정으로 신뢰를 주는 길은 검사를 통째로 끄는 것(`security.workspace.trust.enabled`)뿐이라 안 쓴다 — 모든 폴더를
믿게 된다. 그래서 사람이 「Trust」를 누를 때 VS Code 가 적는 자리에 같은 꼴로 적는다(결정 0130).

**어디에 적나**(VS Code 1.141 `2a59476c` — `workspaceTrust.ts` · `storageMainService.ts` · `storageMain.ts` · `storage.ts` · `uri.ts`).
  열쇠 `content.trust.model.key` · 값은 JSON 글 `{"uriTrustInfo": [{"uri": <URI>, "trusted": true}, ...]}` · SQLite 표 `ItemTable`.
  그 열쇠는 「앱 공유」 층이라 공유 DB(`~/.vscode-shared/sharedStorage/state.vscdb`)에 산다 — `--user-data-dir` 이 달라도 같은 DB 다.
  공유 DB 에 없으면 VS Code 는 앱 DB(`%APPDATA%\\Code\\User\\globalStorage\\state.vscdb`)에서 찾아 공유 DB 로 옮기고 거기서는 지운다.
  우리는 공유 DB 에만 쓴다. 없으면 VS Code 가 짓는 문장 그대로 짓는다.
  URI 는 `URI.file(<디스크 철자>)` 를 VS Code 가 JSON 으로 내는 꼴에서 캐시 칸(`fsPath` · `external`)을 뺀 것이다 —
  `{"$mid": 1, "path": "/C:/…", "scheme": "file"}`. 캐시 칸은 VS Code 가 읽은 뒤 스스로 셈한다(`URI.revive`).

**무엇을 적나.** 받은 저장소 뿌리마다 한 줄이다 — 작업 루트 한 줄로 적지 않는다. VS Code 는 위 폴더의 신뢰로 그 아래를 다 믿어, 루트
한 줄이면 거기 새로 받는 남의 저장소까지 믿고 위 폴더로 믿은 저장소는 그 창에서 신뢰를 못 뺀다(`canSetWorkspaceTrust`).
  이미 섰나는 VS Code 의 규칙대로 가린다 — 신뢰한 어느 줄의 경로가 그 뿌리와 같거나 그 위 폴더면 섰다(`isEqualOrParent` · 윈도는
  ASCII 대소문자를 안 가린다).

**안 적는 것.**
  - VS Code 가 떠 있을 때 — 떠 있는 VS Code 는 DB 를 다시 안 읽고, 그 사이 신뢰를 고치면 제 기억으로 덮는다. 어느 창이든 공유 DB 를
    같이 쓰므로 실행 파일 이름(`Code.exe`)으로 가린다
  - 앱 DB 에 VS Code 가 아직 안 옮긴 신뢰 목록이 있을 때 — 공유 DB 에 먼저 적으면 VS Code 가 그 목록을 안 옮겨 사람이 믿던 폴더가
    사라진다. VS Code 가 한 번 뜨면 옮긴다
  - 사람이 뺀 저장소 — VS Code 는 신뢰를 빼면 그 줄을 지울 뿐이다. 그래서 선 적이 있는 뿌리를 우리 기록(공유 DB 곁의
    `.paisetup-trusted-folders.json`)에 남기고, 거기 있는데 지금 안 섰으면 다시 안 넣는다. 기록이 없을 때만 「본 적 없음」이고,
    있는데 못 읽으면(잠김 · 깨짐) 아무것도 안 쓰고 미룬다. 기록은 쓴 뒤에도 VS Code 가 안 떠 있다고 가렸을 때만 남긴다 — 그 사이
    떴으면 적은 것이 덮였을 수 있다
  - VS Code 가 떠 있나를 못 가렸을 때 — 떠 있는 것으로 보고 미룬다
  - VS Code 가 없는 PC — `code` 가 PATH 에 없고 공유 DB 도 없으면 아무것도 안 짓는다
  - 윈도 밖 — 떠 있나를 못 가린다

표준 출력(status) — 한 줄:
  SEEN=<n>    우리 기록에 든 뿌리 수 — 0 이면 아직 한 자리도 신뢰가 선 것을 못 봤다(못 심었다 · 미뤘다) · `?` 면 기록을 못 읽었다.
              종료 코드 0
"""

import contextlib
import json
import ntpath
import os
import shutil
import sqlite3
import sys
import tempfile
import urllib.request

PRODUCT_NAME = 'Code'                       # product.json `nameShort` — 앱 DB 의 사용자 데이터 폴더 이름
SHARED_DATA_FOLDER = '.vscode-shared'       # product.json `sharedDataFolderName` — 홈 아래 공유 자리
SHARED_STORAGE = 'sharedStorage'            # storageMainService.ts — 공유 자리 아래 DB 폴더
DB_NAME = 'state.vscdb'
APP_DB_REL = ('User', 'globalStorage')      # 사용자 데이터 자리 아래 앱 DB 폴더
TRUST_KEY = 'content.trust.model.key'       # workspaceTrust.ts `WORKSPACE_TRUST_STORAGE_KEY`
MIGRATED_KEY = '__$__migratedStorageMarker'  # storage.ts `MIGRATED_KEY` — 공유 DB 가 앱 DB 에서 옮긴 열쇠 목록
TRUST_LIST, URI_FIELD, TRUSTED_FIELD = 'uriTrustInfo', 'uri', 'trusted'
URI_MARSHALLED_ID = 1                       # `MarshalledId.Uri` — URI 가 JSON 으로 나갈 때 붙는 표지
FILE_SCHEME = 'file'
# storage.ts `SQLiteStorageDatabase.doConnect` 가 DB 를 열 때마다 내는 두 문장 — 없는 DB 를 이 꼴로 짓는다
CREATE_SQL = ('PRAGMA user_version = 1;'
              'CREATE TABLE IF NOT EXISTS ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB);')
UPSERT_SQL = ('INSERT INTO ItemTable VALUES (?,?) '
              'ON CONFLICT (key) DO UPDATE SET value = excluded.value WHERE value != excluded.value')
BUSY_SEC = 5
SEEN_FILE = '.paisetup-trusted-folders.json'
EXE_NAME = 'code.exe'                       # 떠 있나 — 실행 파일 이름을 소문자로 견준다
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PID_SLOTS, IMAGE_CHARS = 8192, 32768
VT_HAVE, VT_NOW, VT_GONE = 'trusted', 'trusted-now', 'removed-by-user'
VT_OFF, VT_ABSENT, VT_RUNNING, VT_UNMOVED = 'not-windows', 'vscode-absent', 'vscode-running', 'app-db-unmoved'
VT_UNKNOWN, VT_RECORD = 'running-unknown', 'record-unreadable'
SEEN_UNREADABLE = '?'   # status — 기록을 못 읽었다(설치기는 안내 줄을 낸다)


class Stop(Exception):
    """한 줄 계약으로 멈춘다 — `line` 이 표준 출력에 그대로 갈 줄이다."""
    def __init__(self, line):
        super().__init__(line)
        self.line = line


def error(kind, detail):
    return Stop(f'ERROR={kind}:{detail}')


def shared_dir():
    """공유 자리 — VS Code 의 `appSharedDataHome`(홈 아래 `sharedDataFolderName`). `--shared-data-dir` · 포터블은 안 덮는다."""
    return os.path.join(os.path.expanduser('~'), SHARED_DATA_FOLDER)


def user_data_dir():
    """사용자 데이터 자리 — VS Code 가 고르는 차례(`userDataPath.ts`)에서 포터블 · `--user-data-dir` 을 뺀 것."""
    base = (os.environ.get('VSCODE_APPDATA') or os.environ.get('APPDATA')
            or os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming'))
    return os.path.join(base, PRODUCT_NAME)


def vscode_on_path():
    return shutil.which('code') is not None


def vscode_running():
    """VS Code 가 떠 있나 — 윈도 밖은 None. 프로세스마다 실행 파일 경로를 묻는다(같은 사용자의 것만 열린다)."""
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
            if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)) and ntpath.basename(buf.value).lower() == EXE_NAME:
                return True
        finally:
            k32.CloseHandle(h)
    return False


# ── VS Code 의 URI · 신뢰 규칙(윈도) ───────────────────────────────────────────────────────────────────────
def uri_of(root):
    """`URI.file(root)` 의 (권한, 경로) — 역슬래시를 슬래시로 바꾸고, UNC 는 권한을 가르고, 경로 앞에 `/` 를 세운다."""
    p, authority = root.replace('\\', '/'), ''
    if p.startswith('//'):
        i = p.find('/', 2)
        authority, p = (p[2:], '/') if i == -1 else (p[2:i], p[i:] or '/')
    return authority, p if p.startswith('/') else '/' + p


def fs_path(authority, path):
    """`originalFSPath` — 드라이브 글자의 대소문자를 둔 윈도 철자."""
    if authority and len(path) > 1:
        v = '//' + authority + path
    elif len(path) >= 3 and path[0] == '/' and path[1].isascii() and path[1].isalpha() and path[2] == ':':
        v = path[1:]
    else:
        v = path
    return v.replace('/', '\\')


def ascii_lower(s):
    return ''.join(c.lower() if 'A' <= c <= 'Z' else c for c in s)


def covers(parent, base):
    """`extpath.isEqualOrParent(base, parent, ignoreCase)` — 신뢰 줄의 철자(parent)가 폴더 철자(base)와 같거나 그 위 폴더인가."""
    if base == parent:
        return True
    if not base or not parent:
        return False
    if '..' in base or '..' in parent:
        base, parent = ntpath.normpath(base), ntpath.normpath(parent)
    if len(parent) > len(base) or ascii_lower(base[:len(parent)]) != ascii_lower(parent):
        return False
    if len(parent) == len(base):
        return True
    return base[len(parent) - 1 if parent.endswith('\\') else len(parent)] == '\\'


def trusted_paths(raw):
    """저장된 값 → (값 객체, 신뢰한 file 줄의 철자 목록). 값이 없으면 빈 객체. 꼴이 다르면 ValueError — VS Code 가 다시 쓸 때
    빈 목록으로 덮을 값이라 우리는 손대지 않는다."""
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    obj = {} if raw is None else json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError('신뢰 값이 객체가 아니다')
    entries = obj.get(TRUST_LIST)
    if entries in (None, False, 0, ''):   # VS Code 의 `!result.uriTrustInfo` — 없는 것으로 보고 빈 목록에서 시작한다
        entries = obj[TRUST_LIST] = []
    if not isinstance(entries, list):
        raise ValueError(f'{TRUST_LIST} 가 목록이 아니다')
    paths = []
    for e in entries:
        u = e.get(URI_FIELD) if isinstance(e, dict) and e.get(TRUSTED_FIELD) else None
        if (isinstance(u, dict) and u.get('scheme') == FILE_SCHEME and isinstance(u.get('path'), str)
                and not u.get('query') and not u.get('fragment')):
            paths.append(fs_path(u.get('authority') or '', u['path']))
    return obj, paths


def entry_of(root):
    authority, path = uri_of(root)
    uri = {'$mid': URI_MARSHALLED_ID, 'path': path, 'scheme': FILE_SCHEME}
    if authority:
        uri['authority'] = authority
    return {URI_FIELD: uri, TRUSTED_FIELD: True}


def dump(obj):
    """VS Code 가 `JSON.stringify` 로 쓰는 꼴 — 공백 없이 · 한글 그대로."""
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


# ── DB ─────────────────────────────────────────────────────────────────────────────────────────────────────
def read_items(db, keys):
    """읽기 전용으로 연 DB 에서 열쇠마다 값 — 없는 열쇠는 None."""
    con = sqlite3.connect('file:' + urllib.request.pathname2url(db) + '?mode=ro', uri=True, timeout=BUSY_SEC)
    try:
        return {k: (row[0] if row else None)
                for k in keys for row in [con.execute('SELECT value FROM ItemTable WHERE key = ?', (k,)).fetchone()]}
    finally:
        con.close()


def migrated(raw):
    """공유 DB 가 옮긴 열쇠 — 못 읽는 글은 VS Code 처럼 빈 것으로 본다."""
    try:
        got = json.loads(raw) if raw else []
    except ValueError:
        return set()
    return set(got) if isinstance(got, list) else set()


def write_trust(db, add):
    """공유 DB 의 신뢰 값을 한 거래 안에서 읽고 `add(그 값) → 새 값 글 또는 None` 으로 고친다 — 없는 DB 는 VS Code 의 꼴로 짓는다."""
    os.makedirs(os.path.dirname(db), exist_ok=True)
    new = not os.path.isfile(db)
    con = sqlite3.connect(db, timeout=BUSY_SEC, isolation_level=None)
    try:
        if new:
            con.executescript(CREATE_SQL)
        con.execute('BEGIN IMMEDIATE')   # 두 세션이 함께 돌아도 한쪽의 더함이 다른 쪽의 쓰기에 안 덮인다
        try:
            row = con.execute('SELECT value FROM ItemTable WHERE key = ?', (TRUST_KEY,)).fetchone()
            value = add(row[0] if row else None)
            if value is not None:
                con.execute(UPSERT_SQL, (TRUST_KEY, value))
            con.execute('COMMIT')
        except BaseException:
            con.execute('ROLLBACK')
            raise
    finally:
        con.close()


def seen_path(shared):
    return os.path.join(shared, SHARED_STORAGE, SEEN_FILE)


def read_seen(shared):
    """우리 기록 — 없으면 빈 것. 못 읽거나 글 목록이 아니면 None 이다 — 「본 적 없음」으로 읽으면 사람이 뺀 저장소를 다시 넣는다."""
    try:
        with open(seen_path(shared), encoding='utf-8') as f:
            got = json.load(f)
    except FileNotFoundError:
        return set()
    except (OSError, ValueError):   # 잠겼다 · 폴더다 · 깨졌다
        return None
    return set(got) if isinstance(got, list) and all(isinstance(s, str) for s in got) else None


def write_seen(shared, seen):
    path = seen_path(shared)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix='.paisetup-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(dump(sorted(seen)))
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def plant_trusted_folders(paths, shared=None, app_db=None, running=vscode_running, installed=vscode_on_path):
    """받은 저장소 뿌리를 VS Code 신뢰 목록에 하나씩 더한다 — `((이름, 상태) 목록, 미룬 까닭 또는 None)`.
    상태 = VT_HAVE(이미 신뢰한 줄이 덮는다) · VT_NOW(이번에 더했다) · VT_GONE(신뢰가 선 적이 있는데 지금 없다 — 사람이 뺐다 · 안 넣었다).
    미룬 까닭 = VT_OFF(윈도 밖) · VT_ABSENT(VS Code 가 없다) · VT_RUNNING(떠 있다) · VT_UNKNOWN(떠 있나를 못 가렸다) ·
    VT_RECORD(우리 기록을 못 읽었다) · VT_UNMOVED(앱 DB 의 목록을 VS Code 가 아직 안 옮겼다) — 미룬 판은 아무것도 안 쓴다.
    `shared` · `app_db` 는 공유 자리 · 앱 DB 를 못박는다(검사용) — 안 주면 이 PC 의 VS Code 자리다.
    DB 를 못 읽거나 꼴이 다르면 ERROR=vscode-state · 못 쓰면 ERROR=vscode-write · 쓴 뒤 다시 안 읽히면 ERROR=verify 의 `Stop`."""
    if os.name != 'nt':
        return [], VT_OFF
    shared = shared or shared_dir()
    db = os.path.join(shared, SHARED_STORAGE, DB_NAME)
    app_db = app_db or os.path.join(user_data_dir(), *APP_DB_REL, DB_NAME)
    if not (os.path.isfile(db) or installed()):
        return [], VT_ABSENT
    up = running()
    if up is None:
        return [], VT_UNKNOWN
    if up:
        return [], VT_RUNNING
    seen = read_seen(shared)
    if seen is None:
        return [], VT_RECORD
    roots = {}
    for p in paths:
        d = os.path.realpath(p)
        roots.setdefault(os.path.normcase(d), d)
    judged = {}

    def add(raw):
        """신뢰 값 글 → 받은 뿌리마다 상태를 `judged` 에 두고, 더할 줄이 있으면 새 값 글 · 없으면 None."""
        obj, have = trusted_paths(raw)
        todo = []
        for key, root in roots.items():
            if any(covers(t, root) for t in have):
                judged[key] = VT_HAVE
            elif key in seen:
                judged[key] = VT_GONE
            else:
                judged[key] = VT_NOW
                todo.append(entry_of(root))
        if not todo:
            return None
        obj[TRUST_LIST] += todo
        return dump(obj)

    try:
        items = read_items(db, (TRUST_KEY, MIGRATED_KEY)) if os.path.isfile(db) else {}
        if (items.get(TRUST_KEY) is None and TRUST_KEY not in migrated(items.get(MIGRATED_KEY))
                and os.path.isfile(app_db) and read_items(app_db, (TRUST_KEY,))[TRUST_KEY] is not None):
            return [], VT_UNMOVED
        pending = add(items.get(TRUST_KEY))
    except (sqlite3.Error, OSError, ValueError) as exc:   # UnicodeDecodeError · JSONDecodeError 는 ValueError 다
        raise error('vscode-state', f'{db}: {exc}') from exc
    if pending is not None:   # 거래 안에서 다시 읽고 다시 가린다 — 그 사이 다른 세션이 더했을 수 있다
        try:
            write_trust(db, add)
        except (sqlite3.Error, OSError) as exc:
            raise error('vscode-write', f'{db}: {exc}') from exc
        except ValueError as exc:   # 거래 안에서 읽은 값의 꼴이 달랐다 — 아무것도 안 썼다
            raise error('vscode-state', f'{db}: {exc}') from exc
        try:
            _, after = trusted_paths(read_items(db, (TRUST_KEY,))[TRUST_KEY])
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise error('verify', f'{db}: {exc}') from exc
        missing = [roots[k] for k, s in judged.items() if s == VT_NOW and not any(covers(t, roots[k]) for t in after)]
        if missing:
            raise error('verify', f'{len(missing)} 자리가 쓴 뒤에도 신뢰로 안 읽힌다: {missing[0]}')
    new_seen = seen | {k for k, s in judged.items() if s in (VT_HAVE, VT_NOW)}
    if new_seen != seen and running() is False:   # 떴거나 못 가렸으면 안 남긴다 — 다음 판이 다시 본다
        with contextlib.suppress(OSError):   # 못 적으면(공유 자리가 아직 없다 · 쓰기 막힘) 다음 판이 선 것을 보고 다시 적는다
            write_seen(shared, new_seen)
    return [(os.path.basename(roots[k]), judged[k]) for k in roots], None


def main():
    if sys.argv[1:] != ['status']:
        print('쓰기: python -X utf8 vscode-trust.py status', file=sys.stderr)
        return 2
    seen = read_seen(shared_dir())
    print(f'SEEN={SEEN_UNREADABLE if seen is None else len(seen)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
