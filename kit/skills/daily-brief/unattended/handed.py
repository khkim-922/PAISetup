"""맡긴 일 — 보고 창에서 사람이 골라 맡긴 일들을 작업 폴더에서 claude 한 번으로 차례로 하게 뒤에 띄우고, 도는 동안 일마다의 끝을
프로그램이 읽는 기록으로 낸다. 사람 없는 실행의 입구 하나다 — 어느 모듈도 이 파일을 싣지 않는다.

    python -X utf8 -I handed.py start --tasks <맡긴 일 JSON> [--work <작업 폴더>] [--claude <claude>] [--hand <mail.py>] [--dir <사용자 폴더>]
    python -X utf8 -I handed.py show --id <맡긴 판> [--dir <사용자 폴더>]
    python -X utf8 -I handed.py list [--dir <사용자 폴더>]
    python -X utf8 -I handed.py watch --id <맡긴 판> [--dir <사용자 폴더>]          지킴이 — start 가 떼어 띄운다

start — 맡긴 일을 받아 기록을 곧 쓰고 지킴이를 떼어 띄운 뒤 기다리지 않고 기록 하나(JSON)를 낸다. 지킴이가 사내 세션을 한 번 보고(없으면 — 오늘
    이 PC 가 로그인을 돌려준 뒤면 잠깐 다시 로그인하고(`loan.lend`), 아니면 claude 를 안 띄우고 로그인으로 맺는다), claude 를 작업 폴더에서 세션을 남긴 채 띄워 그 출력을 때와 함께 받아 적고, 끝나면 까닭을 적고 세션을 놓는다(`loan.release` —
    빌린 로그인은 쓰는 일이 더 없으면 곧 돌려준다).
    실행이 결과 글만 쓰고 맺어 손대지 않은 일이 남으면 같은 세션을 한 번 이어 남은 일을 하게 한다(`untouched` · `RESUME_MOST`).
show — 그 판의 지금 기록(JSON 하나). list — 아직 도는 판의 기록(줄마다 JSON 하나). 판의 폴더는 사용자 폴더의 `daily-brief-handed/` 에
    서고, 옛 자리 `mailbox-scan/handed/` 의 판도 읽는다. `--dir` 이 없으면 사용자 폴더를 곁의 스캔(`scan.py status --json`)에 묻는다.

이 손은 일의 글을 읽어 무엇을 가르지 않는다 — 받은 것을 그대로 넘기고, 돌아온 것을 그대로 적는다. 일마다의 끝은 claude 가 결과 글의 첫 줄에
다는 표지(`MARK`)에서 읽는다 — 흐름에는 일을 가르는 다른 표가 없다. 입력 · 기록의 칸과 상태 낱말은 `references/DESIGN.md` 「맡긴 일」 표가
든다.

종료 값 — 0 됐다 · 2 인자가 틀렸다(맡긴 일 파일의 꼴 · 그런 판이 없다) · 5 띄울 수 없다(작업 폴더 · claude · 메일 손이 없다 — 기록을 안 쓴다).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import secrets
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timedelta
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "scripts"), str(HERE)]   # 같은 스킬의 바탕(scripts/)을 먼저 · 곁의 모듈 — `-I` 로 돌아도 싣는다
import brief_schedule as S  # noqa: E402
import clock as tm  # noqa: E402
import launch_base as LB  # noqa: E402
import loan as LN  # noqa: E402
from detach import detached_tries  # noqa: E402
import proc_base as P  # noqa: E402
import scan_door as D  # noqa: E402
import session_login as SL  # noqa: E402
import unattended_const as C  # noqa: E402
import unattended_store as st  # noqa: E402

# ── 이름 붙은 값 ─────────────────────────────────────────────────────────────────
FORMAT = 1                                   # 기록의 꼴 번호 — 칸의 뜻을 바꾸면 올린다(읽는 창이 모르는 판을 안 그린다)
FILES_DIR = "handed"                         # 작업 폴더 안 — 판마다 그 실행이 쓰는 파일(메일 본문 따위)의 자리
RUN_FILE, TASKS_FILE, PROMPT_FILE, RESUME_FILE = "run.json", "tasks.json", "prompt.txt", "prompt-resume.txt"
RESUME_MOST = 1                              # 표지만 쓰고 차례를 마쳐 끝난 실행을 같은 세션으로 잇는 수 — 이어도 또 멈추면 남은 일은 못 함으로 맺는다
STREAM_FILE = "stream.jsonl"                 # claude 의 출력 한 줄마다 {t: 받은 때, line: 그 줄} — 지킴이가 받는 대로 덧붙인다
ERR_FILE, WATCH_LOG = "claude-stderr.log", "watch.log"
PROMPT_TEXT = HERE / "handed-run.md"         # 실행이 받는 글의 틀 — 사람이 읽고 고치는 자리
CEILING_S = 30 * 60                          # 한 판의 claude 가 이보다 오래 돌면 멈춘 것으로 보고 끊는다 — 일 하나가 몇십 초라 여러 건도 몇 분이고,
                                             # 그보다 열 배 길면 기다리는 것이 사람에게 더 나쁘다
STALE_S = CEILING_S + 3 * C.HAND_TIMEOUT_S + 120   # 끝이 안 적힌 판이 이보다 오래됐으면 지킴이 번호를 남이 받았어도 죽은 것으로 본다 —
                                                    # 지킴이의 가장 긴 판: 띄우기 전 · 잇기 전 · 맺기 전의 세션 보기 셋과 claude 의 천장, 출력 거두기
START_GRACE_S = 120                          # 지킴이가 제 번호를 적기 전의 틈 — 이 안에는 번호가 없어도 도는 판이다
KEEP_DAYS = 30                               # 끝난 판을 두는 날 — Claude Code 가 세션을 두는 기본(cleanupPeriodDays)과 같다. 넘으면 이어 갈 대화가 없다
TAIL_CHARS = 400                             # 죽은 판의 출력에서 옮겨 두는 끝 글자 수
WORK_ENV = "PAISETUP_WORK"                   # 작업 폴더 — 설치기가 사용자 환경값으로 심는다
USER_ENV_KEY = "Environment"                 # HKEY_CURRENT_USER 아래 사용자 환경값 — 보고 창 머리의 여는 손(일일 보고 `asks.py`)과 같은 차례로 읽는다
# 손을 띄운 쪽에서 물려받았을 수 있는 표지 — 띄울 claude 의 환경에서 걷는다. 앞의 여섯은 이 PC 에서 도는 Claude Code 세션의 것이고(그것을
# 든 claude 는 저를 남의 세션 아래로 읽는다), 뒤는 VS Code 확장 호스트가 제 아래 프로세스에 거는 것이다
CARRIED_MARKS = ("CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT", "TRACEPARENT", "TRACESTATE",
                 "ELECTRON_RUN_AS_NODE", "VSCODE_IPC_HOOK", "VSCODE_IPC_HOOK_CLI", "VSCODE_PID", "VSCODE_CWD", "VSCODE_NLS_CONFIG",
                 "VSCODE_HANDLES_UNCAUGHT_ERRORS", "VSCODE_ESM_ENTRYPOINT", "VSCODE_CODE_CACHE_PATH", "VSCODE_CRASH_REPORTER_PROCESS_TYPE")
# 띄울 claude 가 세션에 적는 띄운 쪽의 이름 — 그 세션은 사람이 VS Code 에서 이어 갈 대화다. 이 값을 안 주면 `claude -p` 는 세션을 프로그램의
# 것(`sdk-cli`)으로 적고, VS Code 확장은 그런 세션(`sdk-*`)을 창의 세션 목록에서 빼 `session=` 주소가 그 대화를 못 찾고 새 대화를 연다.
# `sdk-*` 가 아닌 값이면 목록에 든다 — 띄운 이를 그대로 댄다. 우회다: 이 환경값은 Claude Code 문서에 없고 CLI · 확장 2.1.330 에서 잰 꼴이다.
# 확장이 `-p` 세션을 목록에 넣거나 문서가 사람이 이을 세션을 적는 길을 내면 걷는다
ENTRYPOINT_ENV, ENTRYPOINT = "CLAUDE_CODE_ENTRYPOINT", "daily-brief-handed"
# 띄우는 꼴 — 권한 깃발 · 도구 · 모델을 안 준다: 사람의 설정이 그대로 실려 대화에서 시킨 것과 같은 판이 된다. 세션은 남긴다(이어 갈 대화)
CLAUDE_ARGS = ("-p", "--output-format", "stream-json", "--verbose")

# 일의 상태 — 기록의 `tasks[].state`
WAITING, DOING, DONE, ASKED, FAILED, UNKNOWN = "waiting", "doing", "done", "asked", "failed", "unknown"
# 판의 끝 — 기록의 `end`(도는 중이면 null)
FINISHED, LOGIN, DIED, CUT = "finished", "login", "died", "cut"
# 결과 글 첫 줄의 표지 — 「[일 2 · 됨]」. 낱말이 그 일의 상태다(실행이 받는 글 `handed-run.md` 가 같은 넷을 든다)
MARK_WORDS = {"됨": DONE, "여쭐 것": ASKED, "못 함": FAILED, "확인 안 됨": UNKNOWN}
CLOSE_WORD = "맺음"                          # 「[맺음]」 — 여러 일을 묶는 맺는 글의 머리. 그 뒤 글은 어느 카드에도 안 붙는다
NEXT_WORD = "넘어감"                         # 「[넘어감]」 — 다음 일로 넘어간다는 말의 머리. 맺는 글처럼 그 뒤 글은 어느 카드에도 안 붙는다
MARK = re.compile(r"^[ \t>*_#`]*\[\s*(?:일\s*(\d{1,3})\s*[·:|-]\s*(" + "|".join(MARK_WORDS) + r")|(" + CLOSE_WORD + "|" + NEXT_WORD
                  + r"))\s*\][ \t*_`]*(.*)$", re.M)
# 결과의 꼴 — 표지 아래 글이 JSON 객체 하나(코드 블록 하나로 감싸도 된다)이고 칸이 이 꼴일 때만 `result` 로 싣는다. 아니면 글 그대로다 —
# 고쳐 읽지 않는다(창은 그 글을 온 그대로 보인다). 칸의 뜻은 `references/DESIGN.md` 「맡긴 일」 기록 표
RESULT_FENCE = re.compile(r"^```(?:json)?[ \t]*\n(.*)\n```$", re.S)
RESULT_KEYS, ITEM_KEYS = {"said", "facts", "items", "more"}, {"label", "unid", "note"}
EXIT_OK, EXIT_ARGS, EXIT_CANNOT = 0, 2, 5
RUN_ID = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{6}$")   # 맡긴 때(서울) · 겹치지 않게 붙인 여섯 글자


class Refused(Exception):
    """맡길 수 없다 — `code` 는 종료 값, `body` 는 낼 JSON."""

    def __init__(self, code: int, body: dict[str, Any]):
        super().__init__(body.get("message", ""))
        self.code, self.body = code, body


# ── 작업 묶음 — 지킴이가 죽으면 claude 도 함께 끝난다 ─────────────────────────────────
JOB_EXTENDED_LIMIT = 9                       # JobObjectExtendedLimitInformation
JOB_KILL_ON_CLOSE = 0x2000                   # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE — 마지막 손잡이가 닫히면 묶음 안을 다 끝낸다


class Job:
    """윈도의 작업 묶음 하나 — 지킴이가 저를 넣고 claude 를 띄우면 claude 와 그 아래가 함께 든다. 손잡이는 지킴이만 쥐어, 지킴이가 어떻게든
    죽으면 OS 가 묶음 안을 끝낸다 — 기록이 「멈췄다」를 말하는데 claude 가 뒤에서 일을 이어 하는 판이 없다. 맺을 때는 `disarm` 으로 그 깃발을
    걷고 나간다 — 일이 띄운 창(처음 뜬 브라우저 따위)이 지킴이와 함께 닫히지 않게. 윈도가 아니거나 묶음을 못 지으면 `armed` 가 거짓이다."""

    def __init__(self) -> None:
        self.handle, self.armed = None, False
        if sys.platform != "win32":
            return
        import ctypes
        import ctypes.wintypes as wt
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreateJobObjectW.restype = wt.HANDLE
        k.GetCurrentProcess.restype = wt.HANDLE
        k.AssignProcessToJobObject.argtypes = (wt.HANDLE, wt.HANDLE)
        k.SetInformationJobObject.argtypes = (wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD)
        self._k, self._ct = k, ctypes
        handle = k.CreateJobObjectW(None, None)
        if handle and self._limit(handle, JOB_KILL_ON_CLOSE) and k.AssignProcessToJobObject(handle, k.GetCurrentProcess()):
            self.handle, self.armed = handle, True

    def _limit(self, handle: Any, flags: int) -> bool:
        """묶음의 한도 깃발을 `flags` 로 바꿔 건다 — 걸었으면 True."""
        ct = self._ct

        class Basic(ct.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ct.c_int64), ("PerJobUserTimeLimit", ct.c_int64), ("LimitFlags", ct.c_uint32),
                        ("MinimumWorkingSetSize", ct.c_size_t), ("MaximumWorkingSetSize", ct.c_size_t), ("ActiveProcessLimit", ct.c_uint32),
                        ("Affinity", ct.c_size_t), ("PriorityClass", ct.c_uint32), ("SchedulingClass", ct.c_uint32)]

        class Extended(ct.Structure):
            _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", ct.c_uint64 * 6), ("ProcessMemoryLimit", ct.c_size_t),
                        ("JobMemoryLimit", ct.c_size_t), ("PeakProcessMemoryUsed", ct.c_size_t), ("PeakJobMemoryUsed", ct.c_size_t)]
        info = Extended()
        info.BasicLimitInformation.LimitFlags = flags
        return bool(self._k.SetInformationJobObject(handle, JOB_EXTENDED_LIMIT, ct.byref(info), ct.sizeof(info)))

    def disarm(self) -> None:
        """「마지막 손잡이가 닫히면 묶음 안을 끝낸다」 깃발을 걷는다 — 걷었으면 `armed` 가 거짓이 된다."""
        if self.armed:
            self.armed = not self._limit(self.handle, 0)


# ── 맡긴 일 — 받는 꼴 ─────────────────────────────────────────────────────────────

def text_of(value: Any) -> str | None:
    """빈칸만이 아닌 글이면 그 글, 아니면 None."""
    return value if isinstance(value, str) and value.strip() else None


def read_tasks(path: pathlib.Path) -> dict[str, Any]:
    """맡긴 일 파일 → {brief, tasks: [{id, kind, line, card: {title, lines}}]}. 꼴이 아니면 `Refused(EXIT_ARGS)` — 무엇이 틀렸나를 댄다.
    값은 손대지 않는다 — 실행에 그대로 넘긴다."""
    def bad(why: str) -> Refused:
        return Refused(EXIT_ARGS, {"error": "args", "message": f"맡긴 일 파일의 꼴이 아니다 — {why}: {path}"})
    try:
        data = json.loads(path.read_bytes().decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise bad(f"못 읽었다({type(exc).__name__})") from None
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list) or not tasks:
        raise bad("tasks 가 빈 목록이거나 없다")
    out, seen = [], set()
    for n, t in enumerate(tasks, 1):
        card = t.get("card") if isinstance(t, dict) else None
        lines = card.get("lines") if isinstance(card, dict) else None
        if not (isinstance(t, dict) and text_of(t.get("id")) and text_of(t.get("kind")) and text_of(t.get("line"))):
            raise bad(f"{n}번째 일에 id · kind · line 가운데 빈 것이 있다")
        if not (isinstance(card, dict) and isinstance(card.get("title"), str) and isinstance(lines, list)
                and all(isinstance(x, str) for x in lines)):
            raise bad(f"{n}번째 일의 card 가 {{title: 글, lines: [글 …]}} 이 아니다")
        if t["id"] in seen:
            raise bad(f"id {t['id']!r} 가 겹친다")
        labels = t.get("labels", [])
        if not (isinstance(labels, list) and all(text_of(x) for x in labels)):
            raise bad(f"{n}번째 일의 labels 가 [글 …] 이 아니다")
        seen.add(t["id"])
        out.append({"id": t["id"], "kind": t["kind"], "line": t["line"], "card": {"title": card["title"], "lines": list(lines)}, "labels": list(labels)})
    brief = data.get("brief")
    return {"brief": brief if isinstance(brief, str) else "", "tasks": out}


def work_folder(given: str | None) -> pathlib.Path:
    """작업 폴더 — `--work`, 없으면 `PAISETUP_WORK`(사용자 환경값을 먼저 — 손을 띄운 쪽이 값을 심기 전에 떴으면 제 환경의 값이 낡았다 —
    그다음 이 프로세스의 환경). 없거나 폴더가 아니면 `Refused(EXIT_CANNOT)`."""
    raw = (given or user_env(WORK_ENV) or os.environ.get(WORK_ENV, "")).strip().strip('"')
    if not raw:
        raise Refused(EXIT_CANNOT, {"cannot": "nowork", "message": f"작업 폴더가 없습니다 — 사용자 환경값 {WORK_ENV} 가 비었습니다. 설치(PAI Setup)를 "
                                                                  "한 번 돌리시면 생깁니다"})
    place = pathlib.Path(os.path.expandvars(raw)).expanduser()
    if not place.is_dir():
        raise Refused(EXIT_CANNOT, {"cannot": "nowork", "message": f"작업 폴더 {place} 가 없습니다. 설치(PAI Setup)를 한 번 돌리시면 생깁니다"})
    return place.resolve()


def user_env(name: str) -> str:
    """사용자 환경값(HKCU\\Environment) 하나 — 윈도가 아니거나 없으면 ""."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, USER_ENV_KEY) as key:
            return str(winreg.QueryValueEx(key, name)[0]).strip()
    except (ImportError, OSError):
        return ""


# ── 기록 — 판마다 폴더 하나 ─────────────────────────────────────────────────────────

def run_roots(home: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """판 폴더가 서는 자리 둘 — (새 판이 서는 자리, 옛 자리). 도는 판의 폴더는 지킴이가 흐름 파일을 쥐어 못 옮겨, 옛 자리의 판도 읽는다."""
    return home / C.HANDED_DIR, home / pathlib.Path(*C.LEGACY_HANDED)


def run_dir(home: pathlib.Path, run_id: str) -> pathlib.Path:
    """그 판의 폴더 — 새 자리에 없고 옛 자리에 있으면 옛 자리, 아니면 새 자리."""
    new, old = run_roots(home)
    return old / run_id if not (new / run_id).is_dir() and (old / run_id).is_dir() else new / run_id


def read_run(home: pathlib.Path, run_id: str) -> dict[str, Any] | None:
    """그 판의 기록 — 없거나 글이 깨졌거나 꼴이 아니면 None(기다려도 안 바뀐다 — 걷기는 폴더의 때로 잰다), 있는데 못 읽으면 `st.Unreadable`."""
    if not RUN_ID.match(run_id or ""):
        return None
    try:
        data = st.read_json(run_dir(home, run_id) / RUN_FILE)
    except st.Unreadable as exc:
        if not exc.broken:
            raise
        return None
    return data if data and data.get("format") == FORMAT else None


def read_tasks_of(here: pathlib.Path) -> dict[str, Any]:
    """그 판의 맡긴 일(start 가 한 번 쓴다) — 없으면 빈 목록, 있는데 못 읽으면 `st.Unreadable`(빈 목록으로 읽으면 일 없는 실행을 띄우거나 다 했다로 맺는다)."""
    return st.read_json(here / TASKS_FILE) or {"tasks": []}


def update_run(home: pathlib.Path, run_id: str, change: dict[str, Any]) -> dict[str, Any]:
    """기록을 다시 읽고 `change` 를 얹어 새 파일로 바꿔 끼운다 — 쓰는 것은 start 와 그 판의 지킴이뿐이라(읽는 쪽은 안 쓴다) 잠금이 없다.
    기록이 없으면 OSError, 못 읽으면 `st.Unreadable` — 빈 것에 얹어 쓰면 칸이 다 빠진 기록이 서서 그 판이 「없는 판」이 된다."""
    data = read_run(home, run_id)
    if data is None:
        raise OSError(f"맡긴 판의 기록이 없다: {run_id}")
    data.update(change)
    st.write_json(run_dir(home, run_id) / RUN_FILE, data)
    return data


def new_id() -> str:
    """새 판의 번호 — 서울 시각(초까지)과 무작위 16 진 여섯 글자."""
    return f"{tm.seoul(tm.utc_now(), '%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"


def stamp() -> str:
    """기록의 때 — UTC ISO 8601 을 천분의 일 초까지. 한 판의 때는 다 이 꼴이라 글자끼리 견줘도 시간순이다(일의 끝과 다음 부름은 1 초 안에
    붙기도 한다)."""
    return tm.utc_now().isoformat(timespec="milliseconds")


def prune(home: pathlib.Path) -> None:
    """끝난 지 `KEEP_DAYS` 가 지난 판을 걷는다 — 기록 폴더와 그 판이 작업 폴더에 쓴 파일 자리. 도는 판은 안 건드린다."""
    edge = tm.utc_now() - timedelta(days=KEEP_DAYS)
    for d in (x for root in run_roots(home) if root.is_dir() for x in root.iterdir() if x.is_dir() and RUN_ID.match(x.name)):
        try:
            rec = record(home, d.name)
        except st.Unreadable:
            continue                                # 있는데 못 읽는 판 — 끝났는지 모르니 안 걷는다
        if rec is None:                             # 못 읽는 판 — 막 짓는 중일 수 있어 폴더의 때로만 잰다
            last = datetime.fromtimestamp(d.stat().st_mtime, tm.utc_now().tzinfo)
        else:
            last = tm.parse(str(rec.get("ended") or rec.get("started") or ""))
        if (rec is not None and rec["alive"]) or last is None or last > edge:
            continue
        files = pathlib.Path(str((rec or {}).get("files") or ""))
        if rec is not None and files.name == d.name and files.parent.name == FILES_DIR:
            shutil.rmtree(files, ignore_errors=True)
        shutil.rmtree(d, ignore_errors=True)


# ── start — 맡기고 곧 돌아온다 ───────────────────────────────────────────────────────

def start(home: pathlib.Path, tasks_path: str, work: str | None, claude: str | None, hand: str | None) -> dict[str, Any]:
    """맡긴 일 하나를 받는다 — 기록을 쓰고 지킴이를 떼어 띄운 뒤 지금 기록을 낸다. 못 맡기면 `Refused`(기록을 안 쓴다)."""
    handed = read_tasks(pathlib.Path(tasks_path))
    place = work_folder(work)
    saved = str((S.load(home)[0] or {}).get("claude") or "")
    program = LB.pick_claude(claude, saved)
    if program is None:
        raise Refused(EXIT_CANNOT, {"cannot": "noclaude", "message": "Claude Code 명령줄(claude)을 못 찾았습니다 — --claude 로 그 자리를 줍니다"})
    mail, missing = D.mail_hand(hand)
    if mail is None:
        raise Refused(EXIT_CANNOT, {"cannot": "nohand", "message": missing})
    prune(home)
    run_id = new_id()
    here = run_dir(home, run_id)
    here.mkdir(parents=True)
    st.write_json(here / TASKS_FILE, handed)
    st.write_json(here / RUN_FILE, {"format": FORMAT, "id": run_id, "brief": handed["brief"], "started": stamp(), "work": str(place),
                                    "files": str(place / FILES_DIR / run_id), "claude": str(program), "hand": str(mail), "pid": None,
                                    "claude_pid": None, "job": None, "end": None, "ended": None, "said": "", "exit": None})
    cmd = P.python_argv(HERE / C.HANDED_ENTRY, "watch", "--id", run_id, "--dir", str(home))
    failed: OSError | None = None
    for kw in detached_tries():
        try:
            with (here / WATCH_LOG).open("wb") as log:
                subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, close_fds=True, cwd=str(here), **kw)
            failed = None
            break
        except OSError as exc:
            failed = exc
    if failed is not None:
        update_run(home, run_id, {"end": DIED, "ended": stamp(), "said": f"지킴이를 못 띄웠다 — {type(failed).__name__}: {failed}"})
    return record(home, run_id) or {}


# ── 실행이 받는 글 ──────────────────────────────────────────────────────────────────

TASK_BLOCK = """### 일 {n} — {kind}
- 누르신 줄: {line}
{labels}- 카드 「{title}」 — 보고 글에 적힌 그대로(`(mail:번호)` 가 그 메일의 번호입니다):
{lines}
"""
LABELS_LINE = "- 결과의 이름표: {labels}\n"


def prompt_of(handed: dict[str, Any], files: pathlib.Path) -> str:
    """실행이 받는 글 — 틀(`PROMPT_TEXT`)의 자리 넷을 채운다. 맡긴 일의 값은 손대지 않고 그대로 싣는다."""
    blocks = "\n".join(TASK_BLOCK.format(n=n, kind=t["kind"], line=t["line"], title=t["card"]["title"],
                                         labels=LABELS_LINE.format(labels=" · ".join(t["labels"])) if t.get("labels") else "",
                                         lines="\n".join(f"  > {x}" for x in t["card"]["lines"]) or "  > (없음)")
                       for n, t in enumerate(handed["tasks"], 1))
    text = PROMPT_TEXT.read_text(encoding="utf-8")
    for key, value in (("{count}", str(len(handed["tasks"]))), ("{files}", files.as_posix()),
                       ("{now}", tm.seoul(tm.utc_now(), "%Y-%m-%d %H:%M")), ("{tasks}", blocks)):
        text = text.replace(key, value)
    return text


RESUME_TEXT = ("아직 결과 글이 없는 일({left})을 이어서 합니다 — 처음 받은 글의 약속 그대로입니다. 한 일을 마치면 결과 글을 그 표지로 열고, 글만 쓰고 "
               "멈추지 말고 곧바로 다음 일의 부름을 잇습니다. 이 실행이 끝나면 남은 일은 하지 못합니다.\n")


def untouched(tasks: list[dict[str, Any]], seen: dict[str, Any]) -> list[int]:
    """끝난 실행에서 아직 손대지 않은 일의 번호 — 표지가 없고, 마지막 표지 뒤로 부름이 하나도 없을 때만(하다 만 일이 있으면 빈 목록 —
    이으면 두 번 들 수 있다). 표지를 하나도 안 단 판도 무엇이라도 불렀으면 빈 목록이다."""
    if seen["called_since_mark"]:
        return []
    return [n for n in range(1, len(tasks) + 1) if n not in seen["marks"]]


def child_env(env: dict[str, str]) -> dict[str, str]:
    """띄울 claude 의 환경 — 보고의 실행과 같은 손질(`launch_base.child_env`)에 물려받았을 표지(`CARRIED_MARKS`)를 더 걷고, 띄운 쪽의
    이름(`ENTRYPOINT`)을 준다 — 그래야 「대화로 이어 가기」 가 그 세션을 연다."""
    return {**{k: v for k, v in LB.child_env(env).items() if k.upper() not in CARRIED_MARKS}, ENTRYPOINT_ENV: ENTRYPOINT}


# ── watch — 지킴이 ─────────────────────────────────────────────────────────────────

def kill_tree(pid: int) -> None:
    """그 claude 와 그것이 띄운 셸 · 손을 함께 끝낸다 — 쥔 프로세스의 번호로만."""
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, **P.quiet())
    else:
        try:
            os.kill(pid, 9)
        except OSError:
            pass


def watch(home: pathlib.Path, run_id: str) -> int:
    """지킴이 한 판 — 작업 묶음에 저를 넣고, 사내 세션을 보고, claude 를 띄워 출력을 받아 적고, 끝의 까닭을 적는다. 어디서 지든 끝을 적고
    claude 를 거둔다."""
    rec = read_run(home, run_id)
    if rec is None or rec.get("end"):
        return EXIT_ARGS
    job = Job()
    rec = update_run(home, run_id, {"pid": os.getpid(), "job": job.armed})
    proc: subprocess.Popen | None = None
    borrowed = False
    try:
        hand = pathlib.Path(rec["hand"])
        lost = SL.look(hand) == SL.LOST
        if not LN.lend(home, hand, tm.utc_now(), LN.RUN, CEILING_S + C.LEND_TIMEOUT_S, lost) and lost:   # 오늘 돌려준 로그인이면 잠깐 빌린다
            update_run(home, run_id, {"end": LOGIN, "ended": stamp(), "said": "띄우기 전에 보니 사내 세션이 없어 claude 를 띄우지 않았다"})
            return EXIT_OK
        borrowed = True
        here = run_dir(home, run_id)
        files = pathlib.Path(rec["files"])
        files.mkdir(parents=True, exist_ok=True)
        handed = read_tasks_of(here)
        (here / PROMPT_FILE).write_text(prompt_of(handed, files), encoding="utf-8")
        args, began, resumed, given_path = list(CLAUDE_ARGS), datetime.now(), 0, here / PROMPT_FILE
        while True:
            with given_path.open("rb") as given, (here / ERR_FILE).open("ab") as err:
                proc = subprocess.Popen([rec["claude"], *args], cwd=rec["work"], stdin=given, stdout=subprocess.PIPE, stderr=err,
                                        env=child_env(dict(os.environ)), close_fds=True, **P.quiet())
            update_run(home, run_id, {"claude_pid": proc.pid, "resumed": resumed})
            reader = threading.Thread(target=pump, args=(proc, here / STREAM_FILE), daemon=True)
            reader.start()
            try:
                code, end = proc.wait(timeout=max(1.0, CEILING_S - (datetime.now() - began).total_seconds())), None
            except subprocess.TimeoutExpired:
                kill_tree(proc.pid)
                code, end = proc.wait(), CUT
            reader.join(timeout=30)
            seen = parse_stream(here / STREAM_FILE, len(handed["tasks"]))
            left, session = untouched(handed["tasks"], seen), seen["session"]
            if end or code != 0 or not left or not session or resumed >= RESUME_MOST or SL.look(hand) == SL.LOST:
                break
            # 표지만 쓰고 차례를 마쳐 실행이 끝났다 — 하다 만 일이 없을 때만 같은 세션을 이어 남은 일을 하게 한다(두 번 들지 않게)
            resumed += 1
            args, given_path = [*CLAUDE_ARGS, "--resume", session], here / RESUME_FILE
            given_path.write_text(RESUME_TEXT.format(left=" · ".join(f"일 {n}" for n in left)), encoding="utf-8")
        update_run(home, run_id, settle(home, run_id, hand, code, end))
        return EXIT_OK
    except BaseException as exc:   # noqa: BLE001 — 어디서 지든 claude 를 거두고 끝을 적는다
        if proc is not None and proc.poll() is None:
            kill_tree(proc.pid)
        update_run(home, run_id, {"end": DIED, "ended": stamp(), "said": f"지킴이가 멈췄다 — {type(exc).__name__}: {exc}"[:TAIL_CHARS]})
        return EXIT_OK
    finally:
        if borrowed:
            LN.release(home, pathlib.Path(rec["hand"]), tm.utc_now(), LN.RUN)   # 세션을 놓는다 — 빌린 로그인을 쓰는 일이 더 없으면 곧 돌려준다
        job.disarm()


def pump(proc: subprocess.Popen, path: pathlib.Path) -> None:
    """claude 의 출력을 줄마다 받은 때와 함께 덧붙인다 — 한 줄씩 디스크로 내려, 읽는 쪽이 도는 동안 그 줄까지 본다."""
    with path.open("a", encoding="utf-8") as out:
        for raw in proc.stdout:
            out.write(json.dumps({"t": stamp(), "line": raw.decode("utf-8", "replace").rstrip("\r\n")}, ensure_ascii=False) + "\n")
            out.flush()


def settle(home: pathlib.Path, run_id: str, hand: pathlib.Path, code: int, end: str | None) -> dict[str, Any]:
    """끝난 claude → 기록에 얹을 끝. 맺음 사건이 성공이고 종료 0 이면 다 했다, 아니면 죽었다(끊었으면 끊겼다). 못 끝낸 일이 있으면 사내 세션을
    한 번 보고, 없으면 로그인이 끊긴 끝이다 — 손이 종료 3 을 낸 뒤의 일들은 그래서 못 했다."""
    here = run_dir(home, run_id)
    handed = read_tasks_of(here)
    seen = parse_stream(here / STREAM_FILE, len(handed["tasks"]))
    result = seen["result"] or {}
    if end is None:
        end = FINISHED if code == 0 and result.get("subtype") == "success" and not result.get("is_error") else DIED
    open_left = len(seen["marks"]) < len(handed["tasks"])   # 표지 없이 남은 일 — 실행이 제 까닭으로 「못 함」을 단 일은 안 센다
    if end != CUT and open_left and SL.look(hand) == SL.LOST:
        end = LOGIN
    said = "" if end == FINISHED else tail(here)
    return {"end": end, "ended": stamp(), "said": said, "exit": code}


def tail(here: pathlib.Path) -> str:
    """죽은 판이 남긴 말 — claude 의 오류 출력, 없으면 맺음 글의 끝."""
    try:
        err = (here / ERR_FILE).read_bytes().decode("utf-8", "replace").strip()
    except OSError:
        err = ""
    return (err or str((parse_stream(here / STREAM_FILE, 0)["result"] or {}).get("result") or "").strip())[-TAIL_CHARS:]


# ── 읽기 — 흐름에서 일마다의 끝 ──────────────────────────────────────────────────────

def split_marks(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    """글 한 덩이 → (첫 표지 앞의 글, [(일 번호, 상태, 표지 뒤의 글) …]). 맺는 글의 머리는 번호 0 · 상태 빈 글이다."""
    found = list(MARK.finditer(text))
    if not found:
        return text, []
    out = []
    for i, m in enumerate(found):
        rest = text[m.end():found[i + 1].start() if i + 1 < len(found) else len(text)]
        head = (0, "") if m.group(3) else (int(m.group(1)), MARK_WORDS[m.group(2)])
        out.append((*head, (m.group(4) + rest).strip()))
    return text[:found[0].start()], out


def parse_stream(path: pathlib.Path, tasks: int) -> dict[str, Any]:
    """흐름 파일 → {session, model, result(마지막 맺음 사건), cost · turns(맺음마다 더한 것), marks: {번호: {state, t, text}}, tools: [부른 때 …],
    called_since_mark: 마지막 표지 뒤에 부름이 있었나(흐름의 차례로 — 때는 같은 천분의 일 초에 겹칠 수 있다), loose: 마지막 부름 뒤 표지에 안
    딸린 글, first · last: 첫 줄 · 끝 줄의 때}. `tasks` 는 맡긴 일의 수 — 그 밖의 번호를 단 표지는 안 센다. 표지를 단 글 뒤로 다음 부름 전까지
    온 글은 그 일의 결과 글에 붙는다. 같은 번호의 표지가 다시 서면 나중 것이다."""
    seen: dict[str, Any] = {"session": None, "model": None, "result": None, "marks": {}, "tools": [], "loose": [], "first": None,
                            "last": None, "cost": None, "turns": None, "called_since_mark": False}
    current = None
    rows, _ = st.read_jsonl(path) if path.is_file() else ([], 0)
    for row in rows:
        t = str(row.get("t") or "")
        seen["last"] = t or seen["last"]
        try:
            e = json.loads(str(row.get("line") or ""))
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        seen["first"] = seen["first"] or t
        kind = e.get("type")
        if kind == "system" and e.get("subtype") == "init":
            seen["session"], seen["model"] = e.get("session_id") or seen["session"], e.get("model") or seen["model"]
            current, seen["loose"] = None, []      # 이은 실행의 첫 글이 앞 실행의 마지막 카드에 붙지 않게
        elif kind == "result":                     # 이은 실행마다 하나 — 끝은 마지막 것, 값 · 턴은 더한다
            current, seen["result"] = None, e
            seen["session"] = e.get("session_id") or seen["session"]
            for key, field in (("cost", "total_cost_usd"), ("turns", "num_turns")):
                if isinstance(e.get(field), (int, float)):
                    seen[key] = (seen[key] or 0) + e[field]
        elif kind == "assistant":
            for c in (e.get("message") or {}).get("content") or []:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    seen["tools"].append(t)
                    current, seen["loose"], seen["called_since_mark"] = None, [], True
                elif c.get("type") == "text" and str(c.get("text") or "").strip():
                    before, marks = split_marks(str(c["text"]))
                    if before.strip():
                        if current is not None:
                            seen["marks"][current]["text"] = (seen["marks"][current]["text"] + "\n\n" + before.strip()).strip()
                        else:
                            seen["loose"].append(before.strip())
                    for n, state, body in marks:
                        if 1 <= n <= tasks:
                            seen["marks"][n] = {"state": state, "t": t, "text": body}
                            seen["called_since_mark"] = False
                        current = n if 1 <= n <= tasks else None
    return seen


def result_of(text: str) -> dict[str, Any] | None:
    """결과 글 → 꼴대로 쓴 결과({said, facts, items, more} — 빈 칸은 뺀다), 꼴이 아니면 None. 꼴 — JSON 객체 하나(코드 블록 하나로 감싸도
    된다) · 칸은 `RESULT_KEYS` 안 · said · more 는 글, facts 는 [이름표, 값] 글 짝의 목록, items 는 {label(빈 글 아님), unid, note} 의 목록 ·
    said · facts · items 가운데 하나는 비지 않는다. 글을 고쳐 꼴을 맞추지 않는다."""
    body = text.strip()
    fenced = RESULT_FENCE.match(body)
    try:
        data = json.loads(fenced.group(1) if fenced else body)
    except ValueError:
        return None
    if not isinstance(data, dict) or not data or not set(data) <= RESULT_KEYS:
        return None
    said, more, facts, items = data.get("said", ""), data.get("more", ""), data.get("facts", []), data.get("items", [])
    if not (isinstance(said, str) and isinstance(more, str) and isinstance(facts, list) and isinstance(items, list)):
        return None
    if not all(isinstance(f, list) and len(f) == 2 and all(isinstance(x, str) and x.strip() for x in f) for f in facts):
        return None
    if not all(isinstance(i, dict) and set(i) <= ITEM_KEYS and text_of(i.get("label")) and all(isinstance(v, str) for v in i.values())
               for i in items):
        return None
    if not (said.strip() or facts or items):
        return None
    out = {"said": said.strip(), "facts": facts, "items": items, "more": more.strip()}
    return {k: v for k, v in out.items() if v}


def task_states(tasks: list[dict[str, Any]], seen: dict[str, Any], ended: bool, ended_at: str | None) -> list[dict[str, Any]]:
    """일마다 {id, kind, state, at, text, result}. `result` 는 결과 글이 꼴대로면 그 칸들(`result_of`), 아니면 None. 표지가 선 일은 그 낱말 ·
    그 때 · 그 글이다. 표지가 없는 일은 —
    도는 중이면 첫째가 하는 중(앞 일의 표지 뒤부터) · 나머지는 기다림.
    끝났으면, 표지를 하나도 안 단 판이 무엇이라도 불렀으면 다 확인 안 됨이다(무엇을 했는지 가를 수 없다). 그 밖에는 첫째가 마지막 표지 뒤에 부름이
    있었으면 확인 안 됨(하다 멈췄다 — 바꾸는 부름이었는지 모른다), 없었으면 못 함이고, 나머지는 못 함(차례대로 하므로 시작하지 않았다)이다."""
    marks = seen["marks"]
    first_open = next((n for n in range(1, len(tasks) + 1) if n not in marks), None)
    called_after = seen["called_since_mark"]
    out = []
    for n, task in enumerate(tasks, 1):
        row = {"id": task["id"], "kind": task["kind"], "state": WAITING, "at": None, "text": ""}
        if n in marks:
            row.update(state=marks[n]["state"], at=marks[n]["t"], text=marks[n]["text"])
        elif not ended:
            if n == first_open:
                row.update(state=DOING, at=max((m["t"] for k, m in marks.items() if k < n), default=seen["first"]))
        elif not marks and seen["tools"]:
            row.update(state=UNKNOWN, at=ended_at, text="\n\n".join(seen["loose"]) if n == 1 else "")
        else:
            row.update(state=UNKNOWN if n == first_open and called_after else FAILED, at=ended_at,
                       text="\n\n".join(seen["loose"]) if n == first_open else "")
        row["result"] = result_of(row["text"]) if n in marks else None   # 표지 없이 맺은 일의 글은 실행이 그 일의 결과로 쓴 글이 아니다
        out.append(row)
    return out


def watcher_alive(rec: dict[str, Any]) -> bool:
    """지킴이가 아직 도나 — 번호를 적기 전이면 맡긴 지 `START_GRACE_S` 안일 때만, 적었으면 그 프로세스가 살았나로. 맡긴 지 `STALE_S` 가
    지났으면 번호를 남이 받았어도 죽은 것이다."""
    started = tm.parse(str(rec.get("started") or ""))
    age = (tm.utc_now() - started).total_seconds() if started else STALE_S
    if age >= STALE_S:
        return False
    if not isinstance(rec.get("pid"), int):
        return age < START_GRACE_S
    return LB.process_alive(rec["pid"]) is not False


def record(home: pathlib.Path, run_id: str) -> dict[str, Any] | None:
    """그 판의 지금 기록 — 아무것도 안 쓴다. 끝이 안 적혔는데 지킴이가 없으면 죽은 판으로 낸다(작업 묶음이 claude 도 함께 끝냈다)."""
    rec = read_run(home, run_id)
    if rec is None:
        return None
    here = run_dir(home, run_id)
    try:
        handed = read_tasks_of(here)
    except st.Unreadable as exc:
        if not exc.broken:
            raise
        handed = {"tasks": []}                     # 글이 깨진 맡긴 일 — 보이기만 하는 자리라 일 없이 낸다(판을 걷는 잣대는 기록이다)
    seen = parse_stream(here / STREAM_FILE, len(handed["tasks"]))
    if rec.get("end") is None and not watcher_alive(rec):
        rec = read_run(home, run_id) or rec              # 지킴이가 끝을 적고 막 나갔을 수 있다 — 다시 읽는다
        if rec.get("end") is None:
            left = tail(here)
            rec = {**rec, "end": DIED, "ended": seen["last"] or rec.get("started"),
                   "said": "지킴이가 끝을 적지 못하고 멈췄다" + (f" — {left}" if left else "")}
        seen = parse_stream(here / STREAM_FILE, len(handed["tasks"]))
    ended = rec.get("end") is not None
    result = seen["result"] or {}
    return {"format": FORMAT, "id": rec["id"], "brief": rec.get("brief") or "", "started": rec.get("started"), "ended": rec.get("ended"),
            "alive": not ended, "end": rec.get("end"), "said": rec.get("said") or "", "session": seen["session"], "work": rec.get("work"),
            "files": rec.get("files"), "model": seen["model"], "cost": seen["cost"], "turns": seen["turns"], "resumed": rec.get("resumed") or 0,
            "end_text": result.get("result") if isinstance(result.get("result"), str) else "",
            "tasks": task_states(handed["tasks"], seen, ended, rec.get("ended"))}


def alive_runs(home: pathlib.Path) -> list[dict[str, Any]]:
    """사용자 폴더의 판 가운데 아직 도는 것의 기록 — 새 판부터, 그 순간 못 읽은 판은 뺀다."""
    names = sorted({d.name for root in run_roots(home) if root.is_dir() for d in root.iterdir() if d.is_dir() and RUN_ID.match(d.name)},
                   reverse=True)
    out = []
    for n in names:
        try:
            r = record(home, n)
        except st.Unreadable:
            continue                                # 그 순간 못 읽은 판은 이번 목록에서만 빠진다 — 다음에 물으면 읽는다
        if r and r["alive"]:
            out.append(r)
    return out


# ── 명령줄 ──────────────────────────────────────────────────────────────────────

def parser() -> argparse.ArgumentParser:
    """명령줄의 꼴 — 하위 명령(start · show · watch · list) · 인자 · 도움말."""
    ap = argparse.ArgumentParser(prog=C.HANDED_ENTRY, description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="action", required=True)
    s = sub.add_parser("start", help="맡긴 일을 받아 뒤에서 띄우고 곧 돌아온다")
    s.add_argument("--tasks", required=True, help="맡긴 일 JSON 파일(꼴은 references/DESIGN.md 「맡긴 일」)")
    s.add_argument("--work", help=f"작업 폴더 — 없으면 {WORK_ENV}")
    s.add_argument("--claude", help="띄울 claude — 없으면 보고가 건 것, 그것도 없으면 PATH")
    s.add_argument("--hand", help="회사 메일 손 mail.py — 없으면 형제 스킬 company-mail 의 것")
    s.add_argument("--dir", help=D.DIR_HELP)
    for name, words in (("show", "그 판의 지금 기록"), ("watch", "지킴이 — start 가 띄운다")):
        one = sub.add_parser(name, help=words)
        one.add_argument("--id", required=True)
        one.add_argument("--dir", help=D.DIR_HELP)
    sub.add_parser("list", help="아직 도는 판의 기록 — 줄마다 하나").add_argument("--dir", help=D.DIR_HELP)
    return ap


def emit(obj: Any) -> None:
    """JSON 한 줄을 표준 출력에 낸다."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    """명령 입구 — 사용자 폴더를 정하고(`--dir` · 없으면 스캔에 묻는다) 받은 명령을 그 손에 나눈다."""
    if hasattr(sys.stdout, "reconfigure") and sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    a = parser().parse_args(argv)
    home = D.home_of(a.dir)
    if home is None:
        emit({"cannot": "nohome", "message": D.NO_HOME})
        return EXIT_CANNOT
    if a.action == "watch":
        return watch(home, a.id)
    if a.action == "list":
        for r in alive_runs(home):
            emit(r)
        return EXIT_OK
    if a.action == "show":
        try:
            got, why = record(home, a.id), f"그런 판이 없다: {a.id}"
        except st.Unreadable as exc:
            got, why = None, f"그 판의 기록을 그 순간 못 읽었다({exc}) — 다시 물으면 읽는다: {a.id}"
        emit(got if got else {"error": "args", "message": why})
        return EXIT_OK if got else EXIT_ARGS
    try:
        emit(start(home, a.tasks, a.work, a.claude, a.hand))
        return EXIT_OK
    except Refused as exc:
        emit(exc.body)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
