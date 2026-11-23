"""창 곁의 손이 사용자 폴더에 남기는 기록 둘 — 넣은 누름의 기록(열쇠마다 끝)과 맡긴 일의 기록(누름마다 넘긴 판 · 일마다의 끝)을 읽고 쓰는 한
자리, 그리고 맡긴 일의 기록에서 일 하나의 끝을 짚는 길. 없음과 못 읽음은 다른 답이다 — 못 읽은 기록 위에 쓰면 「넣는 중」 · 「넣음」 · 맡긴
판을 잃어 같은 일정을 또 넣고 같은 일을 다시 넘긴다.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 store.py · clock.py — `-I` 로 돌아도 싣는다
import clock as T  # noqa: E402
import store as S  # noqa: E402

LEDGER_FILE = "daily-brief-entries.json"       # 넣은 누름의 기록 — 열쇠마다 끝(넣는 중이면 그것도). 사용자 폴더에 산다
LEDGER_LOCK = "daily-brief-entries.lock"       # 그 기록을 고치는 손 하나 — OS 잠금이라 손이 죽으면 OS 가 푼다
LEDGER_KEEP_DAYS = 30                          # 기록을 두는 날 — 창이 날을 건너 열려 있어도 그 안의 누름은 한 번을 지킨다
# 넣은 누름의 끝 — 기록의 `state` 와 창에 돌려 적는 칸의 낱말
ADDED, ALREADY, MOVED, UNSURE, PAST, SESSION, FAILED, ENTERING = "added", "already", "moved", "unsure", "past", "session", "failed", "entering"
RUNS_FILE = "daily-brief-runs.json"           # 맡긴 누름의 기록 — 누름마다 넘긴 판 · 일마다의 끝. 사용자 폴더에 산다. 쓰는 것은 창 곁의 손 하나다(잠금)
# 맡긴 누름의 판 — 넘기는 중(기록에 남긴 뒤 넘기기 전) · 도는 중(실행이 맡았다) · 맺음. 앞의 둘이 「살아 있다」(`live`)
STARTING, RUNNING, ENDED = "starting", "running", "ended"
RUNS_KEEP_DAYS = 30                            # 맺은 누름의 기록을 두는 날 — 그 보고 창을 다시 열어 결과를 볼 만한 동안. 도는 누름은 날과 상관없이 둔다

Unreadable = S.Unreadable                      # 기록 파일이 있는데 못 읽었다


def read_ledger(folder: pathlib.Path) -> dict:
    """넣은 누름의 기록 — 없으면 빈 기록, 있는데 못 읽거나 꼴이 아니면 `Unreadable`. 빈 것으로 읽고 그 위에 쓰면 「넣는 중」 · 「넣음」을
    잃어 같은 일정을 또 넣는다."""
    return S.read_json(folder / LEDGER_FILE) or {}


def write_ledger(folder: pathlib.Path, ledger: dict) -> None:
    """새 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 기록이 남지 않는다. 오래된 줄은 걷는다. 못 쓰면 OSError 를 올린다."""
    cut = T.stamp(T.seoul_now() - dt.timedelta(days=LEDGER_KEEP_DAYS))
    keep = {k: v for k, v in ledger.items() if isinstance(v, dict) and str(v.get("at", "")) >= cut}
    S.replace(folder / LEDGER_FILE, json.dumps(keep, ensure_ascii=False, indent=1).encode("utf-8"))
    ledger.clear()
    ledger.update(keep)


def read_runs(folder: pathlib.Path) -> dict:
    """맡긴 일의 기록 — {누름의 열쇠: 누름}. 파일이 없으면 빈 기록, 있는데 못 읽거나 꼴이 아니면 `Unreadable`."""
    data = S.read_json(folder / RUNS_FILE)
    if data is None:
        return {}
    presses = data.get("presses")
    if not isinstance(presses, dict) or not all(isinstance(v, dict) and isinstance(v.get("page"), str) and isinstance(v.get("ids"), list)
                                                and isinstance(v.get("tasks"), dict) for v in presses.values()):
        raise Unreadable("꼴이 아니다")                # 칸이 빠진 누름 위에서 걸으면 손이 넘어진다 — 못 읽음으로 두고 그 위에 안 쓴다
    return presses


def write_runs(folder: pathlib.Path, presses: dict) -> None:
    """새 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 기록이 남지 않는다. 오래되고 맺은 누름은 걷는다. 못 쓰면 OSError."""
    cut = T.stamp(T.local_now() - dt.timedelta(days=RUNS_KEEP_DAYS))
    keep = {k: v for k, v in presses.items() if isinstance(v, dict) and (live(v) or str(v.get("taken", "")) >= cut)}
    for v in list(keep.values()):                  # 남는 누름이 따르는 누름도 남긴다 — 걷으면 따르는 쪽의 끝을 잃는다
        keep.update({f: presses[f] for f in (v.get("held") or {}).values() if f in presses})
    S.replace(folder / RUNS_FILE, json.dumps({"presses": keep}, ensure_ascii=False, indent=1).encode("utf-8"))


def live(entry: dict) -> bool:
    """맡긴 누름 하나가 아직 살아 있나 — 넘기는 중 · 도는 중. 판의 상태가 셋 밖인 누름(손으로 고친 기록)은 살아 있지 않다 — 따르는 길이
    없어 영영 안 맺히고, 살아 있다고 읽으면 창 곁의 손이 안 끝난다."""
    return entry.get("state") in (STARTING, RUNNING)


def task_outcome(presses: dict, key: str, tid: str) -> dict | None:
    """맡긴 일의 기록에서 그 누름의 그 일의 끝 — 따르는 누름이면 따르는 판의 것."""
    v = presses.get(key) or {}
    follow = (v.get("held") or {}).get(tid)
    if follow:
        return task_outcome(presses, follow, tid)
    return (v.get("tasks") or {}).get(tid)
