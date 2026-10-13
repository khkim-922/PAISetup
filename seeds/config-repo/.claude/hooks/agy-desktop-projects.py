"""agy 데스크탑(Antigravity)의 프로젝트 목록에 작업 루트 저장소를 더한다 — 세션 훅이 `plant_agy_projects` 를 부른다.

**왜 있나.** 맨바닥 설치 뒤 Antigravity 를 열면 프로젝트 목록이 비어 사람이 저장소마다 더한다. Codex 데스크탑(0126)과 같은 손을
덜어 준다(결정 0132).

**어디에 쓰나**(Antigravity 2.22.0 · #162 조사). 프로젝트 하나에 파일 하나 — `~/.gemini/config/projects/<uuid>.json`(protobuf
`exa.project_pb.Project` 를 JSON 으로). 언어 서버가 그 폴더를 지켜 목록을 화면에 민다. 사람이 프로젝트를 지우면 파일이 사라질 뿐
묘비가 없다.
  새 파일 — `{"id": <uuid4>, "name": <폴더 이름>, "projectResources": {"resources": [{"gitFolder": {"folderUri": <U>}}]},
  "isWorkspaceOnly": false}`. `settings` 칸은 안 넣는다 — 프로젝트 설정이 전역 Turbo(0127)를 가린다.
  `U` 는 앱이 짓는 꼴(VS Code 의 `URI.file(…).toString()`) — `file:///` + 드라이브 소문자 + `%3A` + 슬래시 경로, 나머지 글자는 퍼센트
  인코딩하고 `/` 는 둔다.
  임시 파일은 `~/.gemini/config/` 에 쓰고 이름 바꾸기로 `projects/` 에 넣는다 — 지켜보는 언어 서버가 반쯤 쓴 파일을 안 읽게.

**안 쓰는 것.**
  - 이미 선 저장소 — 그 폴더의 읽히는 `*.json` 가운데 그 뿌리를 `folderUri` 로 든 것이 있으면(디코딩한 경로를 대소문자 없이)
  - 사람이 뺀 저장소 — 목록에 한 번 선 뿌리를 우리 기록(`~/.gemini/config/.paisetup-agy-projects.json`)에 남기고, 거기 있는데 지금
    없으면 다시 안 넣는다. 기록이 `projects/` 밖인 까닭 — 그 안의 못 읽는 파일은 앱이 기본값으로 덮는다. 기록이 없을 때만 「본 적
    없음」이고, 있는데 못 읽으면 아무것도 안 쓰고 미룬다. 기록은 쓴 뒤에도 앱이 안 떠 있다고 가렸을 때만 남긴다 — 그 사이 떴으면 앱이
    새 파일을 못 봤을 수 있다
  - 앱이 떠 있을 때(실행 파일 `Antigravity.exe`) · 떠 있나를 못 가렸을 때 · agy 가 서지 않은 PC(`~/.gemini/config/` 가 없다) · 윈도 밖
"""

import contextlib
import json
import ntpath
import os
import tempfile
import urllib.parse
import uuid

CONFIG_REL = ('.gemini', 'config')
PROJECTS_DIR = 'projects'
PROJECT_EXT = '.json'
SEEN_FILE = '.paisetup-agy-projects.json'
EXE_NAME = 'antigravity.exe'                # 떠 있나 — 실행 파일 이름을 소문자로 견준다(제거 프로그램은 이름이 다르다)
RESOURCES, PROJECT_RESOURCES, GIT_FOLDER, FOLDER_URI = 'resources', 'projectResources', 'gitFolder', 'folderUri'
FILE_SCHEME = 'file://'
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PID_SLOTS, IMAGE_CHARS = 8192, 32768
AP_HAVE, AP_NOW, AP_GONE = 'listed', 'listed-now', 'removed-by-user'
AP_OFF, AP_ABSENT, AP_RUNNING = 'not-windows', 'agy-absent', 'app-running'
AP_UNKNOWN, AP_RECORD = 'running-unknown', 'record-unreadable'


class Stop(Exception):
    """한 줄 계약으로 멈춘다 — `line` 이 표준 출력에 그대로 갈 줄이다."""
    def __init__(self, line):
        super().__init__(line)
        self.line = line


def error(kind, detail):
    return Stop(f'ERROR={kind}:{detail}')


def config_dir():
    return os.path.join(os.path.expanduser('~'), *CONFIG_REL)


def agy_running():
    """Antigravity 가 떠 있나 — 윈도 밖은 None. 프로세스마다 실행 파일 경로를 묻는다(같은 사용자의 것만 열린다)."""
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


def folder_uri(root):
    """앱이 짓는 `folderUri` — VS Code 의 `URI.file(root).toString()`: 드라이브 글자 소문자 · `:` 는 `%3A` · `/` 는 두고 나머지는
    퍼센트 인코딩. UNC 는 권한(소문자)을 `file://` 뒤에 둔다."""
    p = root.replace('\\', '/')
    if p.startswith('//'):
        authority, _, rest = p[2:].partition('/')
        return FILE_SCHEME + urllib.parse.quote(authority.lower(), safe='') + urllib.parse.quote('/' + rest, safe='/')
    if len(p) >= 2 and p[1] == ':':
        return FILE_SCHEME + '/' + p[0].lower() + '%3A' + urllib.parse.quote(p[2:], safe='/')
    return FILE_SCHEME + urllib.parse.quote(p if p.startswith('/') else '/' + p, safe='/')


def uri_key(uri):
    """`folderUri` → 대소문자 없이 견줄 윈도 경로 — `file://` 이 아니면 None."""
    if not isinstance(uri, str) or not uri.lower().startswith(FILE_SCHEME):
        return None
    authority, _, path = uri[len(FILE_SCHEME):].partition('/')
    path = urllib.parse.unquote('/' + path)
    if authority:
        v = '//' + urllib.parse.unquote(authority) + path
    elif len(path) >= 3 and path[0] == '/' and path[2] == ':':
        v = path[1:]
    else:
        v = path
    return os.path.normcase(v.replace('/', '\\'))


def listed_keys(pdir):
    """`projects/` 의 읽히는 파일이 든 저장소 뿌리(견줄 꼴) — 못 읽는 파일은 앱이 덮을 것이라 「없다」로 본다."""
    keys = set()
    for name in (os.listdir(pdir) if os.path.isdir(pdir) else ()):
        if not name.lower().endswith(PROJECT_EXT):
            continue
        try:
            with open(os.path.join(pdir, name), encoding='utf-8-sig') as f:
                obj = json.load(f)
        except (OSError, ValueError):
            continue
        res = obj.get(PROJECT_RESOURCES) if isinstance(obj, dict) else None
        for r in (res.get(RESOURCES) or []) if isinstance(res, dict) else ():
            folder = r.get(GIT_FOLDER) if isinstance(r, dict) else None
            key = uri_key(folder.get(FOLDER_URI)) if isinstance(folder, dict) else None
            if key:
                keys.add(key)
    return keys


def replace_into(cfg, dest, text):
    """곁(`cfg`)에 쓰고 이름 바꾸기로 `dest` 에 넣는다 — 못 쓰면 임시 파일을 안 남기고 OSError 를 올린다."""
    fd, tmp = tempfile.mkstemp(dir=cfg, prefix='.paisetup-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        os.replace(tmp, dest)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def write_project(cfg, pdir, root):
    """새 프로젝트 파일 하나 — 앱의 꼴(두 칸 들여쓰기 · 끝 줄바꿈 없음 · 한글 그대로)이다."""
    new_id = str(uuid.uuid4())
    obj = {'id': new_id, 'name': os.path.basename(root),
           PROJECT_RESOURCES: {RESOURCES: [{GIT_FOLDER: {FOLDER_URI: folder_uri(root)}}]}, 'isWorkspaceOnly': False}
    os.makedirs(pdir, exist_ok=True)
    replace_into(cfg, os.path.join(pdir, new_id + PROJECT_EXT), json.dumps(obj, ensure_ascii=False, indent=2))


def plant_agy_projects(paths, cfg=None, running=agy_running):
    """받은 저장소 뿌리를 agy 데스크탑 프로젝트로 하나씩 더한다 — `((이름, 상태) 목록, 미룬 까닭 또는 None)`.
    상태 = AP_HAVE(이미 어느 프로젝트의 폴더다) · AP_NOW(이번에 더했다) · AP_GONE(목록에 섰다가 사람이 뺐다 — 안 넣었다).
    미룬 까닭 = AP_OFF(윈도 밖) · AP_ABSENT(agy 가 서지 않았다) · AP_RUNNING(앱이 떠 있다) · AP_UNKNOWN(떠 있나를 못 가렸다) ·
    AP_RECORD(우리 기록을 못 읽었다) — 미룬 판은 아무것도 안 쓴다.
    `cfg` 는 `~/.gemini/config` 자리를 못박는다(검사용). 폴더를 못 읽으면 ERROR=agy-projects · 못 쓰면 ERROR=agy-write 의 `Stop`."""
    if os.name != 'nt':
        return [], AP_OFF
    cfg = cfg or config_dir()
    if not os.path.isdir(cfg):
        return [], AP_ABSENT
    up = running()
    if up is None:
        return [], AP_UNKNOWN
    if up:
        return [], AP_RUNNING
    seen_path = os.path.join(cfg, SEEN_FILE)
    try:
        with open(seen_path, encoding='utf-8') as f:
            got = json.load(f)
    except FileNotFoundError:
        got = []
    except (OSError, ValueError):   # 잠겼다 · 폴더다 · 깨졌다 — 「본 적 없음」으로 읽으면 사람이 뺀 저장소를 다시 넣는다
        return [], AP_RECORD
    if not (isinstance(got, list) and all(isinstance(s, str) for s in got)):
        return [], AP_RECORD
    seen = set(got)
    pdir = os.path.join(cfg, PROJECTS_DIR)
    try:
        listed = listed_keys(pdir)
    except OSError as exc:
        raise error('agy-projects', f'{pdir}: {exc}') from exc
    roots = {}
    for p in paths:
        d = os.path.realpath(p)
        roots.setdefault(os.path.normcase(d), d)
    states, added = [], []
    for key, root in roots.items():
        if key in listed:
            states.append((os.path.basename(root), AP_HAVE))
        elif key in seen:
            states.append((os.path.basename(root), AP_GONE))
        else:
            try:
                write_project(cfg, pdir, root)
            except OSError as exc:
                raise error('agy-write', f'{pdir}: {exc}') from exc
            added.append(key)
            states.append((os.path.basename(root), AP_NOW))
    new_seen = seen | {k for k in roots if k in listed} | set(added)
    if new_seen != seen and running() is False:   # 떴거나 못 가렸으면 안 남긴다 — 다음 판이 다시 본다
        with contextlib.suppress(OSError):   # 못 적으면 다음 판이 목록에 선 것을 보고 다시 적는다
            replace_into(cfg, seen_path, json.dumps(sorted(new_seen), ensure_ascii=False, separators=(',', ':')))
    return states, None
