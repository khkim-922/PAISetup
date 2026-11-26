"""보고 창에서 누르신 것을 누름 종류 표(`KINDS` — 열쇠 · 거둘 때인가 · 할 일 · 돌려 적을 칸)대로 거둬 그 할 일을 부르고 끝을 그 창에 돌려
적는다 — 일일 보고 스킬의 창 곁의 손. 「일정에 넣기」는 사람이 누른 카드의 값과 열쇠로만 일정 손(형제 스킬 company-calendar 의 `add`)을
부른다. 모델은 이 길에 없다.

    python -X utf8 -I ticks.py --dir <사용자 폴더> --watch                 창 곁에 남아 누름을 바로 거둔다(창을 여는 손이 띄운다)
    python -X utf8 -I ticks.py --dir <사용자 폴더> --presses [--within 초]  열린 보고 창의 누름을 한 번 거둔다(시계 판의 뒷받침)

누름은 창(file://)의 localStorage `brief-cal:<열쇠>` 에 있다(`assets/report.js`) — 누른 때와 누른 창의 이름만 든다. 넣을 값은 그 창의 보고
글(같은 이름의 .md)에서 그 열쇠의 카드를 찾아 읽는다 — 창이 사람에게 보인 글과 같은 글이다. 일정 손은 미리 보기의 판을 다시 지어 열쇠가
다르면 안 넣는다(그 사이 일정이 바뀌었다).

한 누름은 한 번만 넣는다 — 넣기는 사용자 폴더의 기록(`records.LEDGER_FILE`)을 OS 잠금(`records.LEDGER_LOCK`) 아래에서 고친다: 일정 손을 부르기 전에 그
열쇠를 「넣는 중」으로 굳히고, 끝을 받은 뒤 그 끝으로 고친다. 잠금을 쥐고 「넣는 중」을 만나면 앞 손이 넣다 죽은 것이다 — 들었는지
모르니 다시 안 넣고 「확인 안 됨」으로 맺는다(두 벌이 들 수 있다). 창 곁의 손과 시계 판이 같은 누름을 함께 봐도 기록이 한 번을 지킨다.

창 곁의 손은 「보고 맞추기」의 「자리 밖에서 보기」 켜고 끄기(`brief-away`)와 보고 시각 고름(`brief-times`)도 바로 거둔다 — 시계 판이 부르는
것과 같은 자로 재는 시계의 명령(같은 스킬 `unattended/clock.py away … --chosen-at <누른 때>` · `clock.py window-times …
--window-base … --chosen-at <누른 때>`)으로 걸고, 그 끝 줄을 그 창에 돌려 적는다. 못 부르면 남겨 두어 시계 판이 받는다.
창 머리의 「비서에게 부탁하기」(`brief-ask`)도 이 손만 거둔다 — 곁의 `asks.py` 가 VS Code 의 작업 폴더 창에 대화를 연다. 시계 판은 부탁을 안
거두고, 손은 누른 지 오래된 부탁을 안 연다 — 자리를 뜬 뒤에 VS Code 가 뜨면 놀란다. 맡길 일의 누름(`brief-run:`)도 이 손만 거둔다 — 곁의
`runs.py` 가 맡긴 일의 입구(`unattended/handed.py`)으로 뒤의 실행에 넘기고 그 기록을 따라 일마다의 끝을 창에 적는다. 맡긴 판이 도는 동안 손은 열린 창이 없어도
남고, 오래 걸리는 부름(일정 손 · 시계의 명령 · VS Code 기다리기) 사이에도 숨 표를 적고 그 판을 돌본다(`Hand.tend`). 시계 판의 뒷받침(곁의 `ticks.py`)도 표의 같은 줄로 재고 적는다.

내는 것 — `--presses` 는 끝 줄 하나(거둔 것이 없으면 「거둘 누름 없음」). `--watch` 는 아무것도 안 찍고 열린 보고 창이 없어지거나 로그인
Edge 에 못 닿으면 끝난다. 종료 값 — 0 거뒀다(거둘 것이 없었던 것도) · 3 로그인 Edge 에 못 닿았다. 무엇을 지키고 왜 그런가는
`references/DESIGN.md` 「일정에 넣기」가 든다.
"""

from __future__ import annotations

import functools
import json
import os
import pathlib
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손 · 손가락들 — `-I` 로 돌아도 싣는다
import asks as A  # noqa: E402
import brief_const as C  # noqa: E402
import cli  # noqa: E402
import edge as E  # noqa: E402
import press_kinds as M  # noqa: E402
import proc_base as P  # noqa: E402
import runs as R  # noqa: E402
import state as V  # noqa: E402
import clock as T  # noqa: E402
import unattended_link as L  # noqa: E402
import store as S  # noqa: E402
from oslock import OsLock  # noqa: E402
from detach import detached_tries  # noqa: E402
from records import (ADDED, ALREADY, ENTERING, FAILED, LEDGER_LOCK, MOVED, PAST, SESSION, UNSURE, read_ledger,  # noqa: E402
                     write_ledger)
from hand_wanted import hand_wanted  # noqa: E402
from brief_put import PUT_KEY, Put, put_moment  # noqa: E402
from brief_inline import APPROVAL as APPROVAL_ID, approvals_in  # noqa: E402
from brief_tasks import cards_of  # noqa: E402
from task_kinds import CAL, Cells  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TICKS = HERE / "ticks.py"
CALENDAR = HERE.parents[1] / "company-calendar" / "scripts" / "company_calendar.py"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
APPROVAL = HERE.parents[1] / "company-approval" / "scripts" / "approval.py"          # 형제 스킬 — 결재 문서의 창을 띄우는 손(open)
UNATTENDED = HERE.parent / C.UNATTENDED_DIR   # 같은 스킬의 사람 없는 실행 — 보고 시각 · 「자리 밖에서 보기」 · 맡긴 일의 명령(clock.py · handed.py)의 자리
WAIT_STEP_S = 0.5                              # 다른 프로그램의 끝을 기다리는 동안 숨 표 · 맡긴 일을 돌보는 사이
HAND_LOCK = "daily-brief-hand.lock"            # 창 곁의 손 하나 — 쥔 동안 산다. 둘째 손은 못 쥐고 바로 끝난다
HAND_LOG = "daily-brief-hand.log"              # 그 손이 언제 떴고 왜 끝났나 — 마지막 판만(뜰 때마다 새로 쓴다)
CALENDAR_TIMEOUT_S = 180                       # 일정 손 한 번의 시한 — 넣기는 세션 받기 · 등록 · 다시 읽기까지 한다. 넘기면 들었는지 모른다
PREVIEW_TIMEOUT_S = 90                         # 미리 보기 한 번의 시한 — 세션 받기 · 그날 일정 읽기. 넘기면 그 줄에 넣기 단추를 안 단다(보고는 선다)
STEP_S = 1.0                                   # 창 곁의 손이 누름을 보는 사이 — 이 PC 의 디버깅 포트만 부른다
ERRORS_MOST = 5                                # 창 곁의 손이 Edge 와 연달아 이만큼 못 주고받으면 끝난다(Edge 가 닫혔다)
NO_TAB_GRACE_S = 10                            # 열린 보고 창이 이만큼 내리 안 보여야 창 곁의 손이 끝난다 — 막 연 탭은 잠깐 file: 주소가 아니다

TAIL = "대화에서 「그 약속 넣어 줘」 하시면 지금 판으로 다시 보여 드립니다"
WORDS = {
    ADDED: "일정에 넣었습니다 · {when}. 빼시려면 대화에서 「그 일정 지워 줘」",
    ALREADY: "같은 일정이 이미 있어 넣지 않았습니다",
    UNSURE: "넣었는지 확인하지 못했습니다 — 일정 화면에서 보시고, 없으면 대화에서 「그 약속 넣어 줘」",
    PAST: CAL.late,                            # 창이 누르기 전부터 지난 줄에 다는 말과 같은 말이다 — 종류 표가 든다
    SESSION: "사내 로그인이 끊겨 아직 못 넣었습니다 — 로그인이 살아나면 그때 넣습니다(그 사이 일정이 바뀌면 안 넣습니다)",
    FAILED: "넣지 못했습니다 — {why}. 대화에서 「그 약속 넣어 줘」 하시면 넣습니다",
}
MOVED_MINE = "앞서 넣으신 「{title}」 일정이 그 시각에 들어 넣지 않았습니다. " + TAIL
MOVED_NEW = "보여 드린 뒤 그 시각에 「{title} {when}」 일정이 새로 들어 넣지 않았습니다. " + TAIL
MOVED_ELSE = "보여 드린 뒤 일정이 달라져 넣지 않았습니다. " + TAIL
# 일정 손의 종료 값 가운데 아무것도 안 바꾼 것이 확실한 셋(그 손 --help 의 범례 · 원본은 ep_command 의 EXIT_ARGS · EXIT_SESSION · EXIT_URL 의
# 손사본) — 인자가 틀렸다 · 사내 세션이 없다 · 일정 앱 주소가 틀렸다. 다 넣기 전에 멈춘다. 그 밖의 실패는 들었는지 모른다
EXIT_ARGS_CAL, EXIT_SESSION_CAL, EXIT_URL_CAL = 2, 3, 8


# ── 일정 손 ─────────────────────────────────────────────────────────────────

def run_calendar(put: Put, preview: bool = False) -> tuple[int | None, dict]:
    """일정 손 한 번 — 넣기(카드의 값과 열쇠 그대로), `preview` 면 같은 값의 미리 보기(일정을 안 바꾼다 — 그 판과 열쇠를 받는다. 넣기는 같은
    값으로 같은 판을 다시 지어 열쇠를 견준다). (종료 값 · 답) — 손을 못 띄웠으면 (None, {}), 시한을 넘겼으면 (-1, {})."""
    if not CALENDAR.is_file():
        return None, {"message": "일정 스킬이 곁에 없습니다"}
    cmd = P.python_argv(CALENDAR, "preview" if preview else "add", "--title", put.title, "--start", put.start, "--end", put.end)
    cmd += ["--place", put.place] if put.place else []
    cmd += ["--private"] if put.private else []
    cmd += [] if preview else ["--confirm", put.key]
    try:
        proc = subprocess.Popen(cmd, **piped())
    except OSError as exc:
        return None, {"message": f"일정 손을 못 띄웠습니다({type(exc).__name__})"}
    got = wait_out(proc, PREVIEW_TIMEOUT_S if preview else CALENDAR_TIMEOUT_S)
    if got is None:
        return -1, {}
    try:
        answer = json.loads(got.decode("utf-8", "replace"))
    except ValueError:
        answer = {}
    return proc.returncode, answer if isinstance(answer, dict) else {}


def moved_words(answer: dict, card_text: str, ledger: dict) -> str:
    """그 사이 바뀜의 말 — 지금 판의 겹침 가운데 카드에 안 보였던 일정을 짚는다. 이 창에서 앞서 넣은 카드면 그렇다고. 겹침 말고 다른 것이
    달랐으면 그저 달라졌다고."""
    clash = [c for c in ((answer.get("preview") or {}).get("clash") or []) if isinstance(c, dict) and c.get("title")]
    new = [c for c in clash if str(c["title"]) not in card_text]
    mine = [c for c in new if any(r.get("state") == ADDED and r.get("title") == c["title"] and r.get("start") == c.get("start")
                                  for r in ledger.values() if isinstance(r, dict))]
    if mine:
        return MOVED_MINE.format(title=mine[0]["title"])
    if new:
        return MOVED_NEW.format(title=new[0]["title"], when=new[0].get("when") or "")
    return MOVED_ELSE


def outcome(code: int | None, answer: dict, card_text: str, ledger: dict) -> tuple[str, str]:
    """일정 손의 끝 → (끝, 사람에게 할 말). 들었는지 모르는 끝(시한 · 손 오류 · 모르는 답)은 다 「확인 안 됨」이다 — 다시 넣으면 두 벌이 든다."""
    if code is None:
        return FAILED, WORDS[FAILED].format(why=answer.get("message") or "일정 손을 못 띄웠습니다")
    if code == EXIT_SESSION_CAL:
        return SESSION, WORDS[SESSION]
    if code == EXIT_ARGS_CAL:                      # 세션 전에 멈췄다 — 아무것도 안 바꿨다
        return FAILED, WORDS[FAILED].format(why="카드의 값을 일정 손이 받지 않았습니다")
    if code == EXIT_URL_CAL:                       # 일정 앱 주소를 못 읽어 넣기 전에 멈췄다
        return FAILED, WORDS[FAILED].format(why="일정 앱 주소를 찾지 못했습니다")
    state = answer.get("state") if code == 0 else None
    if state == MOVED and (answer.get("preview") or {}).get("already"):
        state = ALREADY                            # 판이 달라진 까닭이 그 일정이 이미 든 것이다 — 일정 손은 열쇠를 먼저 견줘 moved 로 낸다
    if state == ADDED:
        return ADDED, WORDS[ADDED].format(when=T.moment_words(T.seoul_now()))
    if state == ALREADY:
        return ALREADY, WORDS[ALREADY]
    if state == MOVED:
        return MOVED, moved_words(answer, card_text, ledger)
    return UNSURE, WORDS[UNSURE]


# ── 돌려준 로그인을 잠깐 빌린다 ───────────────────────────────────────────────────

class Borrow:
    """단추의 일 하나가 돌려준 사내 로그인을 잠깐 빌리는 판 — 같은 스킬 시계의 명령(`clock.py lend · release` — `unattended/loan.py`)으로 묻는다.
    일을 하기 전에 그 세션을 쓴다고 적고(`hold_on` — 시계 판이
    도중에 돌려주지 않게), 세션이 없다는 끝(`SESSION`)을 처음 받으면 한 번만 빌리고(`take`), 그 걸음의 일을 다 하면 놓는다(`give`) — 한 걸음의 누름 여럿이 로그인
    하나를 함께 쓰고 그 걸음 끝에 한 번 돌려준다. 오늘 이 PC 가 로그인을 돌려준 적이 없으면 시계가 안 빌려 준다 — 전처럼 대화의 로그인을 청한다."""

    def __init__(self, folder: pathlib.Path, why: str, ceiling_s: int):
        self.folder, self.why, self.ceiling, self.tried, self.held, self.lent, self.futile = folder, why, ceiling_s, False, False, False, False

    def hold_on(self) -> None:
        """그 일이 산 세션을 쓰기 시작한다 — 시계에 쓰는 일로 적어(빌리지 않는다) 그 도중에 시계 판이 돌려주지 않게. 이 판에서 한 번만."""
        if self.held:
            return
        self.held = True
        code, _ = run_unattended(self.folder, [C.CLOCK_ENTRY, "lend", "--why", self.why, "--ceiling", str(self.ceiling)], C.LEND_CALL_S)
        self.lent = code == 0

    def take(self) -> bool:
        """세션이 없다는 끝을 받았다 — 이 판에서 처음이면 시계에 빌리기를 청한다. 내는 것 — 빌렸나(다시 해 볼까)."""
        if self.tried:
            return False
        self.tried = self.held = True
        code, _ = run_unattended(self.folder, [C.CLOCK_ENTRY, "lend", "--why", self.why, "--ceiling", str(self.ceiling), "--lost"],
                                 C.LEND_CALL_S)
        self.lent = code == 0
        return self.lent

    def give(self, hold: bool = False, futile: bool = False) -> None:
        """쓴다고 적었으면(`hold` 면 안 적었어도 — 결재 창은 사람이 그 세션의 창에서 누른다) 시계에 놓는다고 알린다 — 쓰는 일이 더 없으면 시계가 곧
        돌려준다. `futile` — 빌린 로그인 위에서도 세션 없음이었다(그 일에는 오늘 다시 안 빌린다). 못 알려도 빌림의 쓸 끝이 지나면 시계 판이 돌려준다."""
        if self.lent or hold:
            run_unattended(self.folder, [C.CLOCK_ENTRY, "release", "--why", self.why, *(["--hold"] if hold else []),
                                         *(["--futile"] if futile and self.lent else [])], C.LEND_CALL_S)
        self.lent = False


# ── 누름 하나 ───────────────────────────────────────────────────────────────

def card_for(folder: pathlib.Path, press: dict, key: str) -> tuple[Put, str] | None:
    """누름이 가리키는 카드 — 누른 창(`brief` — 그 창의 파일 이름)의 보고 글(`store.page_brief`)에서 그 열쇠의 카드. 글 · 카드가 없으면 None."""
    got = S.page_brief(folder, str(press.get("brief") or ""))
    if got is None:
        return None
    _, text = got
    return cards_of(text).get(key)


# 기록에서 본 누름 하나의 형편 — 넣다 죽은 기록 · 같은 누름의 맺은 끝 · 앞서 넣은 카드의 새 누름 · 새 누름
DEAD, REPLAY, ENTERED, NEW = "dead", "replay", "entered", "new"


def settle(folder: pathlib.Path, ledger: dict, key: str, press: dict, still=lambda: True) -> tuple[str, str] | None:
    """누름 하나를 맺는다 — (끝, 말) · 일정 손을 부르기 직전에 누름이 사라졌으면(사람이 다시 눌러 취소했다) None. 잠금을 쥔 채 부른다.
    차례가 곧 지킴이다 — 넣다 죽은 기록 맺기 → 같은 누름이면 그 끝 → 앞서 넣었나 → 카드 없음 · 지난 약속 → `still` → 넣기(`enter` — 「넣는 중」을
    먼저 적는다) → 끝 적기(`record_end` — 넣은 기록은 더 나쁜 끝으로 안 덮는다). `still` 은 그 누름이 창에 그대로 있나를 묻는다."""
    rec = ledger_rec(ledger, key)
    if standing(rec, press) == DEAD:
        rec = close_dead(folder, ledger, key, rec)
    stand = standing(rec, press)
    if stand == REPLAY:
        return replay_end(rec)
    entered = rec if stand == ENTERED else None
    found = card_for(folder, press, key)
    verdict = put_verdict(found)
    if verdict is None:
        if not still():
            return None
        verdict = enter(folder, ledger, key, press, found, entered)
    return record_end(folder, ledger, key, press, found, entered, verdict)


def ledger_rec(ledger: dict, key: str) -> dict | None:
    """그 열쇠의 기록 — 없거나 꼴이 아니면 None."""
    return ledger.get(key) if isinstance(ledger.get(key), dict) else None


def standing(rec: dict | None, press: dict) -> str:
    """기록에서 본 그 누름의 형편 하나 — DEAD(잠금을 쥐었는데 「넣는 중」 — 앞 손이 넣다 죽었다) · REPLAY(같은 누름 — 누른 때가 기록의 것과
    같거나 앞 — 의 맺은 끝: 창에 적은 끝이 사라져도 두 벌을 안 넣는다. 세션 없음은 맺은 것이 아니라 늘 다시 해 본다) · ENTERED(앞서 넣은 카드의
    새 누름 — 지운 일정을 다음 보고가 같은 판으로 다시 세운 카드 · 다른 창의 같은 카드: 일정 손이 판을 또 견주어, 이미 든 일정이면 열쇠가 달라
    안 넣는다) · NEW."""
    if rec and rec.get("state") == ENTERING:
        return DEAD
    if rec and rec.get("state") != SESSION and str(press.get("at") or "") <= str(rec.get("pressed") or ""):
        return REPLAY
    return ENTERED if rec and rec.get("state") == ADDED else NEW


def close_dead(folder: pathlib.Path, ledger: dict, key: str, rec: dict) -> dict:
    """넣다 죽은 기록을 맺어 기록에 적고 낸다 — 들었는지 모르니: 앞서 넣은 열쇠면 그 넣음으로, 아니면 「확인 안 됨」으로. 어느 쪽이든 죽은 그
    누름은 다시 안 부른다(넣고 죽었으면 두 벌). 못 쓰면 OSError."""
    was = rec.get("was")
    rec = {**was, "pressed": str(rec.get("pressed") or "")} if isinstance(was, dict) else \
        {**rec, "state": UNSURE, "said": WORDS[UNSURE], "at": T.stamp(T.seoul_now())}
    ledger[key] = rec
    write_ledger(folder, ledger)
    return rec


def replay_end(rec: dict) -> tuple[str, str]:
    """맺은 기록의 끝 — (끝, 말)."""
    return str(rec.get("state")), str(rec.get("said") or "")


def put_verdict(found: tuple[Put, str] | None) -> tuple[str, str] | None:
    """넣기 전에 맺을 끝 — 카드를 못 찾았으면 못 넣음, 지난 약속이면 지난 약속, 넣을 것이면 None. 시작은 일정 넣기 종류의 시작(`CAL.start`)이다 —
    창의 늦음 잠금이 읽는 줄의 시작(`brief_tasks.Task.start`)과 같은 자."""
    put = found[0] if found else None
    if found is None:
        return FAILED, WORDS[FAILED].format(why="누르신 카드를 그 보고 글에서 찾지 못했습니다")
    elif put_moment(CAL.start(Cells(), put)) <= T.seoul_now():
        return PAST, WORDS[PAST]
    return None


def enter(folder: pathlib.Path, ledger: dict, key: str, press: dict, found: tuple[Put, str], entered: dict | None) -> tuple[str, str]:
    """「넣는 중」을 기록에 굳힌 뒤 일정 손을 한 번 부른다 — (끝, 말). 기록을 못 쓰면 OSError — 부르는 쪽이 일정 손을 안 부르고 멈춘다."""
    put = found[0]
    ledger[key] = {"state": ENTERING, "at": T.stamp(T.seoul_now()), "pressed": str(press.get("at") or ""), "title": put.title, "start": put.start,
                   **({"was": entered} if entered else {})}
    write_ledger(folder, ledger)
    code, answer = run_calendar(put)
    return outcome(code, answer, found[1], ledger)


def record_end(folder: pathlib.Path, ledger: dict, key: str, press: dict, found: tuple[Put, str] | None, entered: dict | None,
               verdict: tuple[str, str]) -> tuple[str, str]:
    """끝을 기록에 적고 창에 돌려 적을 끝을 낸다. 넣은 열쇠의 기록은 더 나쁜 끝으로 안 덮는다 — 다른 창에서 같은 카드를 또 눌러도 그 일정은
    들어 있다. 일정 손이 그 일정이 없는 판을 보였을 때(moved · 지운 뒤 그 시각에 다른 일정)와 다시 넣었을 때만 새 끝이다. 세션 없음은 누름을
    남겨 다시 해 보게 그 끝을 창에 적고, 나머지는 그 넣음을 그대로 창에 돌려 적는다. 카드를 못 찾은 누름은 기록에 안 남긴다."""
    state, said = verdict
    if entered and state not in (ADDED, MOVED):
        ledger[key] = entered if state == SESSION else \
            {**entered, "pressed": max(str(press.get("at") or ""), str(entered.get("pressed") or ""))}
        write_ledger(folder, ledger)
        if state == SESSION:
            return state, said
        return ADDED, str(entered.get("said") or "")
    if found is None:
        return state, said
    put = found[0]
    ledger[key] = {"state": state, "said": said, "at": T.stamp(T.seoul_now()), "pressed": str(press.get("at") or ""), "title": put.title,
                   "start": put.start, "end": put.end}
    write_ledger(folder, ledger)
    return state, said


def press_row(tab: E.Tab, prefix: str, key: str) -> dict | None:
    """창의 저장소에서 지금 그 누름(머리 `prefix` 의 열쇠 `key`) — 없으면 None."""
    return dict(E.stored(tab.read(), prefix)).get(key)


def put_presses(kind: "Kind", tab: E.Tab, folder: pathlib.Path, until: float | None = None, eager: bool = False) -> dict[str, int]:
    """창의 「일정에 넣기」 누름을 거둬 맺고 끝을 그 창에 돌려 적는다 — 끝마다의 수. 기록의 잠금을 못 쥐면(다른 손이 넣는 중) 아무것도 안
    한다 — {"busy": 1}. `until`(monotonic)을 주면 그 안에 일정 손의 시한이 다 들어가는 누름만 시작한다. `eager` 는 `due` 의 것."""
    pending = [(k, v) for k, v in E.stored(tab.read(), kind.key) if PUT_KEY.match(k) and kind.due(v, eager) is not None]
    if not pending:
        return {}
    lock = OsLock(folder / LEDGER_LOCK)
    if not lock.take():
        return {"busy": 1}
    counts: dict[str, int] = {}
    borrow = Borrow(folder, "put", CALENDAR_TIMEOUT_S * len(pending) + C.LEND_CALL_S)
    try:
        try:
            ledger = read_ledger(folder)
        except S.Unreadable:                      # 그 위에 쓰지 않는다 — 누름은 그대로 두고 다음에
            return {"unread": len(pending)}
        for key, press in pending:
            if until is not None and time.monotonic() + CALENDAR_TIMEOUT_S > until:
                counts["later"] = counts.get("later", 0) + 1
                continue
            try:
                still = lambda k=key, v=press: press_row(tab, kind.key, k) == v   # noqa: E731
                borrow.hold_on()
                got = kind.job(folder, ledger, key, press, still)
                if got is not None and got[0] == SESSION and (until is None or time.monotonic() + C.LEND_CALL_S + CALENDAR_TIMEOUT_S <= until) \
                        and borrow.take():                # 돌려준 로그인을 잠깐 빌려 그 누름을 다시 넣는다 — 세션 없음은 아무것도 안 바꿨다
                    got = kind.job(folder, ledger, key, press, still)
                    borrow.futile = borrow.futile or (got is not None and got[0] == SESSION)
            except OSError:                       # 기록을 못 썼다 — 일정 손을 안 불렀거나 끝을 못 남겼다. 누름은 그대로 두고 다음에
                counts["unwritten"] = counts.get("unwritten", 0) + 1
                continue
            if got is None:                       # 부르기 직전에 사람이 취소했다 — 아무것도 안 하고 창에도 안 적는다
                counts["cancelled"] = counts.get("cancelled", 0) + 1
                continue
            state, said = got
            counts[state] = counts.get(state, 0) + 1
            tab.write([[kind.key + key, json.dumps(kind.back(press, state, said), ensure_ascii=False)]])
    finally:
        lock.release()
        borrow.give(futile=borrow.futile)         # 이 걸음의 누름을 다 넣었다 — 빌렸으면 곧 돌려준다
    return counts


def collect_puts(kind: "Kind", tab: E.Tab, folder: pathlib.Path, hand: "Hand") -> str:
    """창 곁의 손이 「일정에 넣기」 누름을 거두는 걸음 — 기록에 남길 한 구절(거둔 것이 없으면 "")."""
    counts = put_presses(kind, tab, folder)
    return "거뒀다 — " + count_said(counts) if counts else ""


# ── 자리 밖에서 보기 ────────────────────────────────────────────────────────

def run_unattended(folder: pathlib.Path, args: list[str], timeout: float) -> tuple[int | str | None, str]:
    """사람 없는 실행의 명령 한 번(`unattended/<args[0]> <args[1:]> --dir <사용자 폴더>`) — (종료 값, 표준 출력). 못 띄웠거나 입구가 없으면
    (None, ""), 시한을 넘겼으면 (`unattended_link.TIMED_OUT`, "") — 그 프로세스는 끊는다. 기다리는 동안 숨 표 · 맡긴 일을 돌본다(`wait_out`)."""
    entry = UNATTENDED / args[0]
    if not entry.is_file():
        return None, ""
    cmd = P.python_argv(entry, *args[1:], "--dir", str(folder))
    try:
        proc = subprocess.Popen(cmd, **piped())
    except OSError:
        return None, ""
    got = wait_out(proc, timeout)
    return (L.TIMED_OUT, "") if got is None else (proc.returncode, got.decode("utf-8", "replace"))


def piped() -> dict[str, Any]:
    """곁의 파이썬 손 한 번을 기다려 출력을 받는 `Popen` 인자 — 창 없이 · UTF-8 로(`proc_base`), 표준 입력은 닫고 출력 · 오류는 받는다."""
    return {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "stdin": subprocess.DEVNULL, "env": P.utf8_env(), **P.quiet()}


def wait_out(proc, timeout: float) -> bytes | None:
    """그 프로세스가 끝나기를 기다려 표준 출력을 낸다 — 시한을 넘기면 끊고 None. 기다리는 동안 `WAIT_STEP_S` 마다 `ticker` 를 부른다 — 창 곁의
    손이 오래 걸리는 부름 사이에도 숨 표를 적고 맡긴 일의 끝을 받는다(안 적으면 창이 손을 없다고 읽어 도는 일을 「못 끝냄」으로 맺는다)."""
    end = time.monotonic() + timeout
    while True:
        try:
            return proc.communicate(timeout=WAIT_STEP_S)[0]
        except subprocess.TimeoutExpired:
            if time.monotonic() >= end:
                proc.kill()
                proc.communicate()
                return None
            ticker[0]()


ticker = [lambda: None]                            # 창 곁의 손이 걸어 두는 돌봄 — 그 밖에서 부르면 아무것도 안 한다


def run_away(folder: pathlib.Path, on: bool, at: str) -> tuple[bool | None, str]:
    """시계의 켜고 끄는 명령 한 번 — `clock_said` 의 답."""
    return L.clock_said(functools.partial(run_unattended, folder), L.away_args(on, at))


# ── 보고 시각 ───────────────────────────────────────────────────────────────

def run_times(folder: pathlib.Path, times: list[str], base: list[str], at: str) -> tuple[bool | None, str]:
    """시계의 창 시각을 거는 명령 한 번 — `clock_said` 의 답. 시계 판이 창의 시각을 받을 때와 같은 자로 재고 건다 — 보던 시각(`base`)에서
    더하고 빼신 것만 지금 걸린 시각표 위에 얹고, 그 뒤 대화에서 바꾸셨으면 안 건다."""
    return L.clock_said(functools.partial(run_unattended, folder), L.times_args(times, base, at))


def eul(word: str) -> str:
    """조사 「을/를」 — 끝 글자에 받침이 있으면 「을」."""
    last = word[-1:]
    return "을" if "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 else "를"


def collect_said(kind: "Kind", tab: E.Tab, folder: pathlib.Path, hand: "Hand") -> str:
    """창의 고름 하나(자리 밖에서 보기 · 보고 시각)를 거둔다 — 거둘 때면 시계의 명령으로 걸고 받았나 · 까닭을 그 창에 적는다. 못 부른 고름은
    「해 본 때」를 적어 `press_kinds.SESSION_RETRY_S` 뒤에 다시 해 보고, 그 사이 시계 판이 받는다(나중의 말씀이 이긴다 — 두 길이 같은 자로 잰다).
    내는 것 — 기록에 남길 한 구절(거둔 것이 없으면 "")."""
    row = dict(E.stored(tab.read(), kind.key)).get("")
    got = kind.due(row)
    if got is None:
        return ""
    refused, said = kind.job(folder, *got)
    if refused is None:
        tab.write([[kind.key, json.dumps({**row, "tried": T.stamp(T.seoul_now())}, ensure_ascii=False)]], quiet=True)
        return f"{kind.name}{eul(kind.name)} 못 걸었다({said}) — 시계 판이 받는다"
    tab.write([[kind.key, json.dumps(kind.back(row, said, refused), ensure_ascii=False)], V.row(folder)])
    return f"{kind.name} — {said}"


# ── 비서에게 부탁하기 ────────────────────────────────────────────────────────

def open_ask(folder: pathlib.Path, words: str, page: str, session: str, tick) -> tuple[str, str]:
    """부탁 하나를 VS Code 에 연다(곁의 `asks.take`) — (끝, 그 창에 적을 말). `tick` 은 기다리는 동안 거듭 부를 것."""
    try:
        return A.take(folder, words, page, f"{T.seoul_now():%H:%M}", tick, session)
    except Exception as exc:  # noqa: BLE001 — 맡은 부탁은 끝을 꼭 적는다: 손이 넘어지면 창이 「여는 중」에 묶이고 다른 누름도 멈춘다
        return A.FAILED, A.WORDS[A.FAILED].format(why=type(exc).__name__)


def collect_ask(kind: "Kind", tab: E.Tab, folder: pathlib.Path, hand: "Hand") -> str:
    """창 머리의 부탁을 거둔다 — 거둘 때면 맡고(창의 값이 그대로일 때만) VS Code 에 연 뒤 끝을 그 창에 적는다. 부탁이 세션을 들었으면(「대화로
    이어 가기」) 그 세션이 이 손이 넘긴 판의 것(`Runs.sessions`)일 때만 잇는다 — 아니면 말만 채워 연다.
    내는 것 — 기록에 남길 한 구절(거둔 것이 없으면 "")."""
    raw = next((v for k, v in tab.read() if k == kind.key), None)
    row = dict(E.stored([[kind.key, raw]], kind.key)).get("") if isinstance(raw, str) else None
    got = kind.due(row)
    if got is None:
        return ""
    words, page, session = got
    taken = {**row, "taken": T.stamp(T.seoul_now())}
    if not tab.swap(kind.key, raw, json.dumps(taken, ensure_ascii=False)):
        return ""
    beaten = [time.monotonic()]

    def tick() -> None:                            # VS Code 가 뜨기를 기다리는 동안에도 숨 표를 적고 맡긴 일을 돌본다 — 창이 손을 없다고 읽지 않게
        ticker[0]()
        if time.monotonic() - beaten[0] >= C.HAND_BEAT_S:
            try:
                tab.write([beat_row()], quiet=True)
            except E.EdgeGone:
                pass
            beaten[0] = time.monotonic()
    state, said = kind.job(folder, words, page, session if session in hand.runs.sessions() else "", tick)
    tab.write([[kind.key, json.dumps(kind.back(taken, state, said), ensure_ascii=False)]])
    return f"{kind.name} — {state}"


# ── 결재 창 열기 ────────────────────────────────────────────────────────────
APPR_OPENED, APPR_FAILED, APPR_SESSION = "opened", "failed", "session"
APPR_WORDS = {
    APPR_OPENED: "평소 Edge 에 결재 창을 띄웠습니다 — 결재 · 반려는 그 창에서 누르시면 됩니다",
    APPR_SESSION: "사내 로그인이 끊겨 결재 창을 못 띄웠습니다 — 대화에서 「EP 로그인 해 줘」 하신 뒤 다시 누르시면 됩니다",
    APPR_FAILED: "결재 창을 못 띄웠습니다 — {why}. 대화에서 「그 결재 창 띄워 줘」 하시면 띄웁니다",
}


def start_approval(doc: str):
    """결재 손 open 한 번을 띄우고 기다리지 않는다 — 그 프로세스 · 못 띄웠으면 (None, 까닭). 창 곁의 손은 걸음마다 끝났나만 본다
    (`approval_done`) — 열기를 기다리는 동안에도 다른 누름(부탁 · 다른 결재)을 제때 맡는다."""
    if not APPROVAL.is_file():
        return None, "결재 스킬이 곁에 없습니다"
    try:
        return subprocess.Popen(P.python_argv(APPROVAL, "open", doc), **piped()), ""
    except OSError as exc:
        return None, f"결재 손을 못 띄웠습니다({type(exc).__name__})"


def approval_done(proc, started: float) -> tuple[str, str] | None:
    """띄운 open 이 끝났으면 (끝, 말), 아직이면 None. `C.APPR_OPEN_S` 를 넘기면 끊고 못 띄움으로 맺는다."""
    if proc.poll() is None:
        if time.monotonic() - started < C.APPR_OPEN_S:
            return None
        proc.kill()
        proc.communicate()
        return APPR_FAILED, APPR_WORDS[APPR_FAILED].format(why="시한 안에 끝나지 않았습니다")
    try:
        answer = json.loads(proc.communicate()[0].decode("utf-8", "replace"))
    except ValueError:
        answer = {}
    answer = answer if isinstance(answer, dict) else {}
    if proc.returncode == 0 and answer.get("state") == "opened":
        return APPR_OPENED, APPR_WORDS[APPR_OPENED]
    if answer.get("error") == "session":           # 결재 손의 답이 대는 갈래(ep_command 의 멈춤 답) — 종료 값을 옮겨 적지 않는다
        return APPR_SESSION, APPR_WORDS[APPR_SESSION]
    why = str(answer.get("message") or "결재 손이 답하지 않았습니다").split(". 다음:")[0]
    return APPR_FAILED, APPR_WORDS[APPR_FAILED].format(why=why)


def open_approval(folder: pathlib.Path, doc: str, press: dict):
    """누른 결재 문서 하나의 창을 띄우기 시작한다 — 그 프로세스, 또는 바로 맺을 (끝, 말). 누른 창의 보고 글에 링크로 선 문서만 연다 —
    창의 저장소는 file: 창끼리 하나라 거기 적힌 id 를 믿지 않는다."""
    got = S.page_brief(folder, str(press.get("brief") or ""))
    if not APPROVAL_ID.match(doc) or got is None or doc not in approvals_in(got[1]):
        return APPR_FAILED, APPR_WORDS[APPR_FAILED].format(why="누르신 결재를 그 보고 글에서 찾지 못했습니다")
    proc, why = start_approval(doc)
    return (APPR_FAILED, APPR_WORDS[APPR_FAILED].format(why=why)) if proc is None else proc


def collect_approvals(kind: "Kind", tab: E.Tab, folder: pathlib.Path, hand: "Hand") -> str:
    """「결재 창 열기」 누름을 거둔다 — 거둘 때인 누름마다 맡고(창의 값이 그대로일 때만 — 한 누름은 한 번 띄운다) 결재 손을 띄워 두고,
    띄워 둔 것 가운데 끝난 것의 끝을 그 창에 적는다. 끝은 그 칸이 아직 맡은 값 그대로일 때만 적는다 — 그 사이 다시 누르신 새 누름을 덮지
    않는다. 못 적으면 띄워 둔 기록을 남겨 다음 걸음에 다시 적는다. 내는 것 — 기록에 남길 한 구절(거둔 것이 없으면 "")."""
    said = []
    for doc, (raw, press) in E.cells(tab.read(), kind.key).items():
        if kind.due(press) is None or press.get("taken") or doc in hand.opening:
            continue
        taken = json.dumps({**press, "taken": T.stamp(T.seoul_now())}, ensure_ascii=False)
        if not tab.swap(kind.key + doc, raw, taken):
            continue
        got = kind.job(folder, doc, press)
        borrow = Borrow(folder, "appr", C.APPR_OPEN_S + C.LEND_CALL_S)
        if not isinstance(got, tuple):
            borrow.hold_on()                       # 띄우는 동안 시계 판이 그 세션을 돌려주지 않게
        hand.opening[doc] = (taken, got if isinstance(got, tuple) else None, got if not isinstance(got, tuple) else None, time.monotonic(), borrow)
    for doc, (taken, end, proc, started, borrow) in list(hand.opening.items()):
        end = end or approval_done(proc, started)
        if end is None:
            continue
        if end[0] == APPR_SESSION and borrow.lent:
            borrow.futile = True
        if end[0] == APPR_SESSION and borrow.take():   # 돌려준 로그인을 잠깐 빌려 다시 띄운다 — 세션 없음은 창을 안 띄웠다
            again, why = start_approval(doc)
            hand.opening[doc] = (taken, None if again else (APPR_FAILED, APPR_WORDS[APPR_FAILED].format(why=why)), again, time.monotonic(), borrow)
            continue
        borrow.give(hold=end[0] == APPR_OPENED, futile=borrow.futile)         # 띄운 결재 창은 사람이 그 세션에서 누른다 — 돌려주기를 그만큼 미룬다
        tab.swap(kind.key + doc, taken, json.dumps(kind.back(json.loads(taken), *end), ensure_ascii=False))
        del hand.opening[doc]
        said.append(end[0])
    return f"{kind.name} — {' · '.join(said)}" if said else ""


# ── 누름 종류 표 ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Kind:
    """누름 종류 한 줄 — 새 누름은 이 표의 줄 하나와 할 일 함수 하나다. `key` 창의 저장소 열쇠(끝이 「:」 면 머리 — 누름마다 그 뒤가 열쇠) ·
    `due` · `back` 은 재는 반(`press_kinds` 의 같은 줄) · `job` 할 일 · `collect(줄, 창,
    폴더, 손)` 창 곁의 손이 이 종류를 거두는 걸음(기록에 남길 한 구절). 시계 판의 뒷받침(곁의 `ticks.py` 의 `--presses` · `--times-done` ·
    `--away-done` · 창의 문 `window_door.read_choices`)도 같은 줄의 `due` · `job` · `back` 을 부른다 — 두 길이 같은 자로 재고 같은 칸을 적는다."""
    name: str
    key: str
    due: Callable[..., Any]
    job: Callable[..., Any]
    back: Callable[..., dict]
    collect: Callable[..., str]


ASK = Kind(M.ASK.name, M.ASK.key, M.ASK.due, open_ask, M.ASK.back, collect_ask)
PUT = Kind(M.PUT.name, M.PUT.key, M.PUT.due, settle, M.PUT.back, collect_puts)
AWAY = Kind(M.AWAY.name, M.AWAY.key, M.AWAY.due, run_away, M.AWAY.back, collect_said)
TIMES = Kind(M.TIMES.name, M.TIMES.key, M.TIMES.due, run_times, M.TIMES.back, collect_said)
APPR = Kind(M.APPR.name, M.APPR.key, M.APPR.due, open_approval, M.APPR.back, collect_approvals)
# 창 곁의 손이 걸음마다 거두는 차례 — 부탁이 맨 앞이다(사람이 VS Code 를 기다리고 있다). 결재 창 열기가 그다음이다(사람이 창을 기다린다). 맡길 일의 누름(`brief_const.RUN_PREFIX`)은 이 표에
# 없다 — 누른 지 `brief_const.RUN_TAKE_S` 안에 맡아야 해서, 표의 줄이 오래 걸리는 동안(일정 손 · 시계의 명령 · VS Code 기다리기)에도
# `Hand.tend` 가 맡는다(곁의 `runs.py`). 표의 줄은 한 걸음에 한 번 돈다
KINDS = (ASK, APPR, PUT, AWAY, TIMES)


# ── 시계 판의 뒷받침 ────────────────────────────────────────────────────────

COUNT_WORDS = {ADDED: "넣음", ALREADY: "이미 있음", MOVED: "그 사이 바뀜", UNSURE: "확인 안 됨", PAST: "지난 약속", SESSION: "세션 없음",
               FAILED: "못 넣음", "later": "다음 판으로", "unwritten": "기록을 못 씀", "busy": "창 곁의 손이 넣는 중",
               "cancelled": "부르기 전에 취소됨", "unread": "기록을 못 읽음"}


ROUND_NO_EDGE = "거둘 누름을 못 봤다 — 로그인 Edge 에 못 닿았다"
ROUND_EDGE_LOST = "거둘 누름을 다 못 봤다 — 로그인 Edge 와 주고받다 멈췄다({exc})"
ROUND_NO_WINDOW = "거둘 누름 없음 — 열린 보고 창이 없다"
ROUND_NOT_FILED = "거둘 누름 없음 — 보고 창이 아직 다 안 섰다"
ROUND_NONE = "거둘 누름 없음"
ROUND_REHANDED = " · 창 곁의 손을 다시 띄웠다"


def round_once(folder: pathlib.Path, within: int = 0) -> int:
    """시계 판 한 번 — 열린 보고 창에 붙어 「일정에 넣기」 누름을 거둬 맺고, 지금 모습을 그 창에 적고, 창 곁의 손이 없으면 띄운 뒤 끝 줄을
    낸다(손은 그 손을 띄울 창일 때만 — `hand_wanted`). 열린 보고 창이 없으면 아무것도 안 연다. 종료 값 — 0 · 3 로그인 Edge 에 못 닿았다."""
    try:
        with E.connected() as cdp:
            tabs = E.brief_tabs(cdp)
            tab = filed_tab(cdp, tabs)
            counts = put_presses(PUT, tab, folder, time.monotonic() + within if within > 0 else None, eager=True)
            tab.write([V.row(folder)])          # 창이 시계가 돈다는 것을 안다 — 누름 직후의 말이 그것으로 갈린다
            cli.say([round_words(counts, rehand(folder, tabs))])
            return C.EXIT_OK
    except E.NoEdge:
        cli.say([ROUND_NO_EDGE])
        return C.EXIT_NO_EDGE
    except cli.Stop as stop:
        cli.say([stop.line])
        return stop.code
    except E.EdgeGone as exc:
        cli.say([ROUND_EDGE_LOST.format(exc=exc)])
        return C.EXIT_NO_EDGE


def filed_tab(cdp: E.Cdp, tabs: list[tuple[str, str]]) -> E.Tab:
    """열린 보고 창 가운데 첫 것에 붙는다 — 창이 없거나 아직 다 안 섰으면 `cli.Stop`(종료 0 — 거둘 누름 없음)."""
    if not tabs:
        raise cli.Stop(ROUND_NO_WINDOW, C.EXIT_OK)
    tab = E.Tab(cdp, tabs[0][0])
    if not tab.filed():
        raise cli.Stop(ROUND_NOT_FILED, C.EXIT_OK)
    return tab


def rehand(folder: pathlib.Path, tabs: list[tuple[str, str]]) -> bool | None:
    """열린 보고 창 가운데 하나라도 창 곁의 손을 띄울 창이면 손을 띄운다(이미 돌면 안 띄운다 — `start_hand`) — 그 답, 안 띄울 창뿐이면 None."""
    if not tabs:
        return None
    scheduled, ready = V.schedule_of(folder)[0] is not None, A.ready()
    if any(hand_wanted((S.page_brief(folder, name) or (None, ""))[1], scheduled, ready) for _, name in tabs):
        return start_hand(folder)
    return None


def round_words(counts: dict[str, int], started: bool | None) -> str:
    """시계 판의 끝 줄 — 「일정에 넣기」의 끝마다의 수(없으면 「거둘 누름 없음」), 창 곁의 손을 다시 띄웠으면 그 말."""
    said = count_said(counts)
    return (C.ROUND_HEAD + said if said else ROUND_NONE) + (ROUND_REHANDED if started else "")


def count_said(counts: dict[str, int]) -> str:
    """「일정에 넣기」 끝마다의 수 — 「넣음 2 · 세션 없음 1」."""
    return " · ".join(f"{COUNT_WORDS.get(k, k)} {n}" for k, n in counts.items())


# ── 창 곁의 손 ──────────────────────────────────────────────────────────────

def start_hand(folder: pathlib.Path) -> bool | None:
    """창 곁의 손을 띄운다 — True 띄웠다 · False 이미 돈다(그 손이 잠금을 쥐고 있다) · None 못 띄웠다. 기다리지 않는다."""
    probe = OsLock(folder / HAND_LOCK)
    if not probe.take():
        return False
    probe.release()
    cmd = P.python_argv(TICKS, "--dir", str(folder), "--watch")
    for kw in detached_tries():                    # 띄운 쪽이 작업 묶음(job) 안이면 그 묶음이 끝날 때 함께 끊기지 않게 — 묶음이 안 놓아 주면 그대로
        try:
            subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                             cwd=str(folder), **kw)
            return True
        except OSError:
            continue
    return None


def beat_row() -> list[str]:
    """창 곁의 손이 살아 있다는 숨 표 한 줄 — 창은 `brief_const.HAND_BEAT_S` 의 세 배 넘게 이것이 없으면 손이 없다고 본다."""
    return [C.HAND_KEY, json.dumps({"beat": T.stamp(T.seoul_now()), "pid": os.getpid()})]


def log(folder: pathlib.Path, line: str, fresh: bool = False) -> None:
    """창 곁의 손의 기록 파일에 때와 한 줄을 남긴다(`fresh` 면 새로 쓴다) — 못 쓰면 그냥 지나간다."""
    try:
        with (folder / HAND_LOG).open("w" if fresh else "a", encoding="utf-8") as f:
            f.write(f"{T.stamp(T.seoul_now())} {line}\n")
    except OSError:
        pass


class Hand:
    """창 곁의 손의 한 판 — 붙은 창 · 숨 표를 적은 때 · 맡긴 일(`runs.Runs`)을 든다. `tend` 는 걸음마다, 그리고 오래 걸리는 부름(일정 손 · 사람 없는
    실행의 명령 · VS Code 를 기다리기)의 사이에도 불린다 — 숨 표를 적고, 새로 맡긴 누름을 맡고, 도는 판의 끝을 창에 적는다. 그 안에서 다시 불리면
    숨 표를 적고 새 누름만 맡는다 — 다른 프로그램을 안 불러, 넘기는 부름이 기다리는 동안 또 넘기지 않는다."""

    def __init__(self, folder: pathlib.Path):
        self.folder, self.tab, self.beat, self.inside, self.stepped = folder, None, 0.0, False, 0.0
        self.opening: dict = {}                     # 띄워 둔 결재 창 열기 — 문서 id → (맡은 값, 끝 · 없으면 None, 프로세스, 띄운 때, 빌림)
        self.runs = R.Runs(folder, functools.partial(run_unattended, folder))

    def tend(self) -> None:
        """걸음 하나 — 숨 표를 적을 때면 적고, 새로 맡긴 누름을 맡고, 도는 판의 끝을 창에 적는다(맡는 걸음 안에서 다시 불리면 새 누름만 맡는다)."""
        try:
            if self.tab is not None and time.monotonic() - self.beat >= C.HAND_BEAT_S:
                self.tab.write([beat_row()], quiet=True)
                self.beat = time.monotonic()
            if time.monotonic() - self.stepped < WAIT_STEP_S:
                return                              # 기다리는 손이 잦게 불러도 저장소는 이 사이보다 잦게 안 읽는다
            self.stepped = time.monotonic()
            if self.inside:                         # 넘기거나 따르는 걸음 안 — 새 누름만 맡는다(다른 프로그램을 안 부른다)
                for said in self.runs.take(self.tab):
                    log(self.folder, said)
                return
            self.inside = True
            try:
                for said in self.runs.step(self.tab):
                    log(self.folder, said)
            finally:
                self.inside = False
        except E.EdgeGone:
            self.tab = None                         # 창이 닫혔거나 Edge 가 멈췄다 — 다음 걸음이 다시 붙는다. 도는 판은 기록에서 계속 따른다
        except Exception as exc:  # noqa: BLE001 — 돌보다 넘어져도 손은 산다: 기다리던 부름(일정 손 · 시계의 명령)을 버려 두지 않고 다음 걸음이 기록을 다시 읽는다
            log(self.folder, f"맡긴 일을 돌보다 넘어졌다 — {type(exc).__name__}: {exc}")
            self.runs.presses, self.runs.pending = None, {}


def watch(folder: pathlib.Path) -> int:
    """창 곁의 손 — 열린 보고 창이 있는 동안 `STEP_S` 마다 누름을 거두고 `C.HAND_BEAT_S` 마다 숨 표를 적는다. 열린 보고 창이 없어지면 끝나고,
    Edge 와 연달아 `ERRORS_MOST` 번 못 주고받으면 끝난다 — 맡긴 판이 도는 동안은 둘 다 기다린다(그 판의 끝을 기록에 받아 두고, 창이 다시
    열리면 바로 적는다). 둘째 손은 잠금을 못 쥐고 바로 끝난다."""
    hand = OsLock(folder / HAND_LOCK)
    if not hand.take():
        return C.EXIT_OK
    log(folder, f"떴다 — pid {os.getpid()}", fresh=True)
    me = Hand(folder)
    ticker[0] = me.tend
    errors, cdp, seen = 0, None, time.monotonic()
    try:
        while True:
            try:
                if cdp is None:
                    cdp, me.tab = E.Cdp(E.port()), None
                tabs = E.brief_tabs(cdp)
                if not tabs:
                    me.tab = None
                    me.tend()                       # 창이 없어도 도는 판은 따른다
                    if time.monotonic() - seen >= NO_TAB_GRACE_S and not me.runs.busy():
                        log(folder, "끝났다 — 열린 보고 창이 없다")
                        return C.EXIT_OK
                    time.sleep(STEP_S)
                    continue
                seen = time.monotonic()
                if me.tab is None or me.tab.target not in {t for t, _ in tabs}:
                    me.tab = E.Tab(cdp, tabs[0][0])
                if me.tab.filed():
                    me.tend()                       # 맨 앞 — 숨 표 · 맡긴 일(누른 지 몇 초 안에 맡아야 한다)
                    for kind in KINDS:              # 그다음 — 누름 종류 표의 차례대로
                        said = kind.collect(kind, me.tab, folder, me)
                        if said:
                            log(folder, said)
                errors = 0
            except E.EdgeGone as exc:
                errors += 1
                if cdp is not None:
                    cdp.close()
                cdp, me.tab = None, None
                me.tend()
                if errors >= ERRORS_MOST and not me.runs.busy():
                    log(folder, f"끝났다 — 로그인 Edge 와 {errors}번 못 주고받았다({exc})")
                    return C.EXIT_NO_EDGE
            time.sleep(STEP_S)
    finally:
        ticker[0] = lambda: None
        if cdp is not None:
            cdp.close()
        hand.release()
