"""보고 창에서 누르신 것을 누름 종류 표(`KINDS` — 열쇠 · 거둘 때인가 · 할 일 · 돌려 적을 칸)대로 거둬 그 할 일을 부르고 끝을 그 창에 돌려
적는다 — 일일 보고 스킬의 창 곁의 손. 「일정에 넣기」는 사람이 누른 카드의 값과 열쇠로만 일정 손(형제 스킬 company-calendar 의 `add`)을
부른다. 모델은 이 길에 없다.

    python -X utf8 -I ticks.py --dir <사용자 폴더> --watch                 창 곁에 남아 누름을 바로 거둔다(창을 여는 손이 띄운다)
    python -X utf8 -I ticks.py --dir <사용자 폴더> --presses [--within 초]  열린 보고 창의 누름을 한 번 거둔다(스캔 판의 뒷받침)

누름은 창(file://)의 localStorage `brief-cal:<열쇠>` 에 있다(`assets/report.js`) — 누른 때와 누른 창의 이름만 든다. 넣을 값은 그 창의 보고
글(같은 이름의 .md)에서 그 열쇠의 카드를 찾아 읽는다 — 창이 사람에게 보인 글과 같은 글이다. 일정 손은 미리 보기의 판을 다시 지어 열쇠가
다르면 안 넣는다(그 사이 일정이 바뀌었다).

한 누름은 한 번만 넣는다 — 넣기는 사용자 폴더의 기록(`LEDGER_FILE`)을 OS 잠금(`LEDGER_LOCK`) 아래에서 고친다: 일정 손을 부르기 전에 그
열쇠를 「넣는 중」으로 굳히고, 끝을 받은 뒤 그 끝으로 고친다. 잠금을 쥐고 「넣는 중」을 만나면 앞 손이 넣다 죽은 것이다 — 들었는지
모르니 다시 안 넣고 「확인 안 됨」으로 맺는다(두 벌이 들 수 있다). 창 곁의 손과 스캔 판이 같은 누름을 함께 봐도 기록이 한 번을 지킨다.

창 곁의 손은 「보고 맞추기」의 「자리 밖에서 보기」 켜고 끄기(`brief-away`)와 보고 시각 고름(`brief-times`)도 바로 거둔다 — 스캔 판이 부르는
것과 같은 자로 재는 스캔의 명령(형제 스킬 mailbox-scan 의 `scan.py brief --away … --chosen-at <누른 때>` · `scan.py brief --window-times …
--window-base … --chosen-at <누른 때>`)으로 걸고, 그 끝 줄을 그 창에 돌려 적는다. 못 부르면 남겨 두어 스캔 판이 받는다.
창 머리의 「비서에게 부탁하기」(`brief-ask`)도 이 손만 거둔다 — 곁의 `asks.py` 가 VS Code 의 작업 폴더 창에 대화를 연다. 스캔 판은 부탁을 안
거두고, 손은 누른 지 오래된 부탁을 안 연다 — 자리를 뜬 뒤에 VS Code 가 뜨면 놀란다. 맡길 일의 누름(`brief-run:`)도 이 손만 거둔다 — 곁의
`runs.py` 가 스캔의 `handed` 명령으로 뒤의 실행에 넘기고 그 기록을 따라 일마다의 끝을 창에 적는다. 맡긴 판이 도는 동안 손은 열린 창이 없어도
남고, 오래 걸리는 부름(일정 손 · 스캔의 명령 · VS Code 기다리기) 사이에도 숨 표를 적고 그 판을 돌본다(`Hand.tend`). 스캔 판의 뒷받침(곁의 `ticks.py`)도 표의 같은 줄로 재고 적는다.

내는 것 — `--presses` 는 끝 줄 하나(거둔 것이 없으면 「거둘 누름 없음」). `--watch` 는 아무것도 안 찍고 열린 보고 창이 없어지거나 로그인
Edge 에 못 닿으면 끝난다. 종료 값 — 0 거뒀다(거둘 것이 없었던 것도) · 3 로그인 Edge 에 못 닿았다. 무엇을 지키고 왜 그런가는
`references/DESIGN.md` 「일정에 넣기」가 든다.
"""

from __future__ import annotations

import datetime as dt
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
import brief_text as B  # noqa: E402
import edge as E  # noqa: E402
import runs as R  # noqa: E402
import state as V  # noqa: E402
import store as S  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TICKS = HERE / "ticks.py"
CALENDAR = HERE.parents[1] / "company-calendar" / "scripts" / "company_calendar.py"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
SCAN = HERE.parents[1] / "mailbox-scan" / "scripts" / "scan.py"   # 형제 스킬 — 보고 시각 · 「자리 밖에서 보기」 · 맡긴 일의 명령(brief · handed)의 주인
AWAY_TIMEOUT_S = 300                           # 그 명령 한 번의 시한 — 켤 때 주소록 손이 세션을 받아 본인 주소를 묻는다(그 스킬의 주소록 시한보다 길게)
WAIT_STEP_S = 0.5                              # 다른 프로그램의 끝을 기다리는 동안 숨 표 · 맡긴 일을 돌보는 사이
LEDGER_FILE = "daily-brief-entries.json"       # 넣은 누름의 기록 — 열쇠마다 끝(넣는 중이면 그것도). 사용자 폴더에 산다
LEDGER_LOCK = "daily-brief-entries.lock"       # 그 기록을 고치는 손 하나 — OS 잠금이라 손이 죽으면 OS 가 푼다
HAND_LOCK = "daily-brief-hand.lock"            # 창 곁의 손 하나 — 쥔 동안 산다. 둘째 손은 못 쥐고 바로 끝난다
HAND_LOG = "daily-brief-hand.log"              # 그 손이 언제 떴고 왜 끝났나 — 마지막 판만(뜰 때마다 새로 쓴다)
LEDGER_KEEP_DAYS = 30                          # 기록을 두는 날 — 창이 날을 건너 열려 있어도 그 안의 누름은 한 번을 지킨다
CALENDAR_TIMEOUT_S = 180                       # 일정 손 한 번의 시한 — 넣기는 세션 받기 · 등록 · 다시 읽기까지 한다. 넘기면 들었는지 모른다
PREVIEW_TIMEOUT_S = 90                         # 미리 보기 한 번의 시한 — 세션 받기 · 그날 일정 읽기. 넘기면 그 줄에 넣기 단추를 안 단다(보고는 선다)
SESSION_RETRY_S = 300                          # 사내 로그인이 끊겨 못 넣은 누름을 창 곁의 손이 다시 해 보는 사이 — 매 걸음 세션 손을 두드리지 않게.
                                               # 스캔 판은 이 사이를 안 기다린다 — 판이 드물어(기본 15분) 살아난 세션을 곧 받는다
STEP_S = 1.0                                   # 창 곁의 손이 누름을 보는 사이 — 이 PC 의 디버깅 포트만 부른다
ERRORS_MOST = 5                                # 창 곁의 손이 Edge 와 연달아 이만큼 못 주고받으면 끝난다(Edge 가 닫혔다)
# 카드의 시각은 서울 벽시계다 — 일정 손의 꼴(형제 스킬 ep-login `ep_command.SEOUL` 의 손사본 · 이 손은 홀로 서야 해서 못 싣는다). 일광 절약이 없다
SEOUL = dt.timezone(dt.timedelta(hours=9))
NO_TAB_GRACE_S = 10                            # 열린 보고 창이 이만큼 내리 안 보여야 창 곁의 손이 끝난다 — 막 연 탭은 잠깐 file: 주소가 아니다

ADDED, ALREADY, MOVED, UNSURE, PAST, SESSION, FAILED, ENTERING = "added", "already", "moved", "unsure", "past", "session", "failed", "entering"
TAIL = "대화에서 「그 약속 넣어 줘」 하시면 지금 판으로 다시 보여 드립니다"
WORDS = {
    ADDED: "일정에 넣었습니다 · {when}. 빼시려면 대화에서 「그 일정 지워 줘」",
    ALREADY: "같은 일정이 이미 있어 넣지 않았습니다",
    UNSURE: "넣었는지 확인하지 못했습니다 — 일정 화면에서 보시고, 없으면 대화에서 「그 약속 넣어 줘」",
    PAST: "지난 약속이라 넣지 않았습니다",
    SESSION: "사내 로그인이 끊겨 아직 못 넣었습니다 — 로그인이 살아나면 그때 넣습니다(그 사이 일정이 바뀌면 안 넣습니다)",
    FAILED: "넣지 못했습니다 — {why}. 대화에서 「그 약속 넣어 줘」 하시면 넣습니다",
}
MOVED_MINE = "앞서 넣으신 「{title}」 일정이 그 시각에 들어 넣지 않았습니다. " + TAIL
MOVED_NEW = "보여 드린 뒤 그 시각에 「{title} {when}」 일정이 새로 들어 넣지 않았습니다. " + TAIL
MOVED_ELSE = "보여 드린 뒤 일정이 달라져 넣지 않았습니다. " + TAIL
# 일정 손의 종료 값 가운데 아무것도 안 바꾼 것이 확실한 셋(그 손 --help 의 범례 · 원본은 ep_command 의 EXIT_ARGS · EXIT_SESSION · EXIT_URL 의
# 손사본) — 인자가 틀렸다 · 사내 세션이 없다 · 일정 앱 주소가 틀렸다. 다 넣기 전에 멈춘다. 그 밖의 실패는 들었는지 모른다
EXIT_ARGS_CAL, EXIT_SESSION_CAL, EXIT_URL_CAL = 2, 3, 8


def now() -> dt.datetime:
    return dt.datetime.now(SEOUL)


def stamp(at: dt.datetime) -> str:
    return at.isoformat(timespec="seconds")


def when_words(at: dt.datetime) -> str:
    return f"{at.month}/{at.day} {at:%H:%M}"


# ── OS 잠금 — 손이 죽으면 OS 가 푼다 ────────────────────────────────────────────

class OsLock:
    """파일 하나의 첫 바이트를 잠근다 — 못 쥐면 `take` 가 False. 시각으로 푸는 잠금과 달리 죽은 손을 「도는 중」으로 잘못 읽지 않는다."""

    def __init__(self, path: pathlib.Path):
        self.path, self.file = path, None

    def take(self) -> bool:
        try:
            f = open(self.path, "a+b")
        except OSError:
            return False
        try:
            f.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            f.close()
            return False
        self.file = f
        return True

    def release(self) -> None:
        if self.file is None:
            return
        try:
            self.file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        self.file.close()
        self.file = None


# ── 기록 — 열쇠마다 끝 ────────────────────────────────────────────────────────

def read_ledger(folder: pathlib.Path) -> dict:
    """넣은 누름의 기록 — 없으면 빈 기록, 있는데 못 읽거나 꼴이 아니면 `R.Unreadable`. 빈 것으로 읽고 그 위에 쓰면 「넣는 중」 · 「넣음」을
    잃어 같은 일정을 또 넣는다."""
    return S.read_json(folder / LEDGER_FILE) or {}


def write_ledger(folder: pathlib.Path, ledger: dict) -> None:
    """새 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 기록이 남지 않는다. 오래된 줄은 걷는다. 못 쓰면 OSError 를 올린다."""
    cut = stamp(now() - dt.timedelta(days=LEDGER_KEEP_DAYS))
    keep = {k: v for k, v in ledger.items() if isinstance(v, dict) and str(v.get("at", "")) >= cut}
    S.replace(folder / LEDGER_FILE, json.dumps(keep, ensure_ascii=False, indent=1).encode("utf-8"))
    ledger.clear()
    ledger.update(keep)


# ── 일정 손 ─────────────────────────────────────────────────────────────────

def run_calendar(put: B.Put, preview: bool = False) -> tuple[int | None, dict]:
    """일정 손 한 번 — 넣기(카드의 값과 열쇠 그대로), `preview` 면 같은 값의 미리 보기(일정을 안 바꾼다 — 그 판과 열쇠를 받는다. 넣기는 같은
    값으로 같은 판을 다시 지어 열쇠를 견준다). (종료 값 · 답) — 손을 못 띄웠으면 (None, {}), 시한을 넘겼으면 (-1, {})."""
    if not CALENDAR.is_file():
        return None, {"message": "일정 스킬이 곁에 없습니다"}
    cmd = [sys.executable, "-X", "utf8", "-I", str(CALENDAR), "preview" if preview else "add", "--title", put.title, "--start", put.start,
           "--end", put.end]
    cmd += ["--place", put.place] if put.place else []
    cmd += ["--private"] if put.private else []
    cmd += [] if preview else ["--confirm", put.key]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **quiet())
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
        return ADDED, WORDS[ADDED].format(when=when_words(now()))
    if state == ALREADY:
        return ALREADY, WORDS[ALREADY]
    if state == MOVED:
        return MOVED, moved_words(answer, card_text, ledger)
    return UNSURE, WORDS[UNSURE]


# ── 누름 하나 ───────────────────────────────────────────────────────────────

def card_for(folder: pathlib.Path, press: dict, key: str) -> tuple[B.Put, str] | None:
    """누름이 가리키는 카드 — 누른 창(`brief` — 그 창의 파일 이름)의 보고 글(`store.page_brief`)에서 그 열쇠의 카드. 글 · 카드가 없으면 None."""
    got = S.page_brief(folder, str(press.get("brief") or ""))
    if got is None:
        return None
    _, text = got
    return B.cards_of(text).get(key)


def settle(folder: pathlib.Path, ledger: dict, key: str, press: dict, still=lambda: True) -> tuple[str, str] | None:
    """누름 하나를 맺는다 — (끝, 말) · 일정 손을 부르기 직전에 누름이 사라졌으면(사람이 다시 눌러 취소했다) None. 잠금을 쥔 채 부른다.
    기록이 이미 맺은 누름은 그 끝을 다시 낸다 — 일정 손을 또 부르지 않는다. `still` 은 그 누름이 창에 그대로 있나를 묻는다."""
    rec = ledger.get(key) if isinstance(ledger.get(key), dict) else None
    if rec and rec.get("state") == ENTERING:      # 잠금을 쥐었는데 넣는 중 — 앞 손이 넣다 죽었다. 들었는지 모른다
        was = rec.get("was")                      # 앞서 넣은 열쇠면 그 넣음으로 맺는다 — 어느 쪽이든 죽은 그 누름은 다시 안 부른다(넣고 죽었으면 두 벌)
        rec = {**was, "pressed": str(rec.get("pressed") or "")} if isinstance(was, dict) else \
            {**rec, "state": UNSURE, "said": WORDS[UNSURE], "at": stamp(now())}
        ledger[key] = rec
        write_ledger(folder, ledger)
    # 같은 누름(누른 때가 기록의 것과 같거나 앞)의 맺은 끝은 다시 낸다 — 창에 적은 끝이 사라져도 두 벌을 안 넣는다. 그 뒤의 새 누름(지운
    # 일정을 다음 보고가 같은 판으로 다시 세운 카드 · 다른 창의 같은 카드 · 못 넣음 뒤 다시 누름)은 다시 해 본다 — 일정 손이 판을 또 견주어,
    # 이미 든 일정이면 열쇠가 달라 안 넣는다. 세션 없음은 맺은 것이 아니라 늘 다시 해 본다
    if rec and rec.get("state") != SESSION and str(press.get("at") or "") <= str(rec.get("pressed") or ""):
        return str(rec.get("state")), str(rec.get("said") or "")
    entered = rec if rec and rec.get("state") == ADDED else None
    found = card_for(folder, press, key)
    put = found[0] if found else None
    if found is None:
        state, said = FAILED, WORDS[FAILED].format(why="누르신 카드를 그 보고 글에서 찾지 못했습니다")
    elif dt.datetime.strptime(put.start, "%Y-%m-%d %H:%M").replace(tzinfo=SEOUL) <= now():
        state, said = PAST, WORDS[PAST]
    elif not still():
        return None
    else:
        ledger[key] = {"state": ENTERING, "at": stamp(now()), "pressed": str(press.get("at") or ""), "title": put.title, "start": put.start,
                       **({"was": entered} if entered else {})}
        write_ledger(folder, ledger)              # 못 쓰면 OSError — 부르는 쪽이 일정 손을 안 부르고 멈춘다
        code, answer = run_calendar(put)
        state, said = outcome(code, answer, found[1], ledger)
    # 넣은 열쇠의 기록은 더 나쁜 끝으로 안 덮는다 — 다른 창에서 같은 카드를 또 눌러도 그 일정은 들어 있다. 일정 손이 그 일정이 없는 판을
    # 보였을 때(moved · 지운 뒤 그 시각에 다른 일정)와 다시 넣었을 때만 새 끝이다. 세션 없음은 누름을 남겨 다시 해 보게 그 끝을 창에 적고,
    # 나머지는 그 넣음을 그대로 창에 돌려 적는다
    if entered and state not in (ADDED, MOVED):
        ledger[key] = entered if state == SESSION else \
            {**entered, "pressed": max(str(press.get("at") or ""), str(entered.get("pressed") or ""))}
        write_ledger(folder, ledger)
        if state == SESSION:
            return state, said
        return ADDED, str(entered.get("said") or "")
    if put is None:
        return state, said
    ledger[key] = {"state": state, "said": said, "at": stamp(now()), "pressed": str(press.get("at") or ""), "title": put.title,
                   "start": put.start, "end": put.end}
    write_ledger(folder, ledger)
    return state, said


def due(press: dict, eager: bool = False) -> bool:
    """거둘 누름인가 — 아직 안 맺었고, 사내 로그인이 끊겨 못 넣은 것은 `SESSION_RETRY_S` 가 지난 것만(`eager` — 스캔 판 — 면 늘)."""
    if press.get("done"):
        return False
    if eager:
        return True
    tried = E.pressed_at({"at": press.get("tried")}) if press.get("tried") else None
    return tried is None or (now() - tried).total_seconds() >= SESSION_RETRY_S


def press_row(tab: E.Tab, prefix: str, key: str) -> dict | None:
    """창의 저장소에서 지금 그 누름(머리 `prefix` 의 열쇠 `key`) — 없으면 None."""
    return dict(E.stored(tab.read(), prefix)).get(key)


def put_due(press: dict, eager: bool = False) -> dict | None:
    """「일정에 넣기」 누름 하나가 거둘 때인가 — 그 누름(할 일 `settle` 이 받는다) · 아니면 None(`due`)."""
    return press if due(press, eager) else None


def put_back(press: dict, state: str, said: str) -> dict:
    """그 창에 돌려 적을 「일정에 넣기」 칸 — 끝과 말, 맺었으면 맺은 때 · 사내 로그인이 끊겨 못 넣었으면 해 본 때(그 누름은 남아 다시 해 본다)."""
    row = {**press, "state": state, "said": said}
    if state == SESSION:
        row["tried"] = stamp(now())
    else:
        row["done"] = stamp(now())
    return row


def put_presses(kind: "Kind", tab: E.Tab, folder: pathlib.Path, until: float | None = None, eager: bool = False) -> dict[str, int]:
    """창의 「일정에 넣기」 누름을 거둬 맺고 끝을 그 창에 돌려 적는다 — 끝마다의 수. 기록의 잠금을 못 쥐면(다른 손이 넣는 중) 아무것도 안
    한다 — {"busy": 1}. `until`(monotonic)을 주면 그 안에 일정 손의 시한이 다 들어가는 누름만 시작한다. `eager` 는 `due` 의 것."""
    pending = [(k, v) for k, v in E.stored(tab.read(), kind.key) if B.PUT_KEY.match(k) and kind.due(v, eager) is not None]
    if not pending:
        return {}
    lock = OsLock(folder / LEDGER_LOCK)
    if not lock.take():
        return {"busy": 1}
    counts: dict[str, int] = {}
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
                got = kind.job(folder, ledger, key, press, lambda k=key, v=press: press_row(tab, kind.key, k) == v)
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
    return counts


def collect_puts(kind: "Kind", tab: E.Tab, folder: pathlib.Path, hand: "Hand") -> str:
    """창 곁의 손이 「일정에 넣기」 누름을 거두는 걸음 — 기록에 남길 한 구절(거둔 것이 없으면 "")."""
    counts = put_presses(kind, tab, folder)
    return "거뒀다 — " + " · ".join(f"{COUNT_WORDS.get(k, k)} {n}" for k, n in counts.items()) if counts else ""


# ── 자리 밖에서 보기 ────────────────────────────────────────────────────────

def run_scan(args: list[str], timeout: float) -> tuple[int | None, str]:
    """스캔의 명령 한 번(형제 스킬 mailbox-scan 의 `scan.py <args>`) — (종료 값, 표준 출력). 못 띄웠거나 스킬이 곁에 없으면 (None, ""), 시한을
    넘겼으면 (None, "시한") — 그 프로세스는 끊는다. 기다리는 동안 숨 표 · 맡긴 일을 돌본다(`wait_out`)."""
    if not SCAN.is_file():
        return None, ""
    cmd = [sys.executable, "-X", "utf8", "-I", str(SCAN), *args]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **quiet())
    except OSError:
        return None, ""
    got = wait_out(proc, timeout)
    return (None, "시한") if got is None else (proc.returncode, got.decode("utf-8", "replace"))


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


def brief_said(args: list[str]) -> tuple[bool | None, str]:
    """`--chosen-at` 을 준 스캔의 brief 명령 한 번 — (따르지 않았나, 그 창에 적을 말). 그 명령은 끝 줄에 그 말만 내고 종료 값으로 따랐나를
    댄다(0 따랐다 · 1 안 따랐다). 못 부르거나 끝 줄이 없거나 그 밖의 종료 값이면 (None, 까닭) — 남겨 두어 스캔 판이 받는다."""
    code, out = run_scan(["brief", *args], AWAY_TIMEOUT_S)
    if code is None:
        return None, out or "메일함 스캔 스킬을 못 불렀다"
    lines = out.strip().splitlines()
    if not lines or code not in (0, 1):
        return None, f"끝 줄이 없거나 종료 {code} 다"
    return code != 0, lines[-1].strip()


def run_away(on: bool, at: str) -> tuple[bool | None, str]:
    """스캔의 켜고 끄는 명령 한 번 — `brief_said` 의 답."""
    return brief_said(["--away", "on" if on else "off", "--chosen-at", at])


def away_due(row: dict | None, eager: bool = False) -> tuple[bool, str] | None:
    """「자리 밖에서 보기」 고름이 거둘 때인가 — (켬인가, 고른 때) · 아니면 None. 안 받은 고름만 — 못 부른 고름은 `SESSION_RETRY_S` 뒤에
    다시 해 본다(`eager` — 스캔 판 — 면 늘)."""
    if not row or row.get("done") or not isinstance(row.get("on"), bool) or not C.AT.match(str(row.get("at") or "")) or not due(row, eager):
        return None
    return row["on"], str(row["at"])


# ── 보고 시각 ───────────────────────────────────────────────────────────────

def run_times(times: list[str], base: list[str], at: str) -> tuple[bool | None, str]:
    """스캔의 창 시각을 거는 명령 한 번 — `brief_said` 의 답. 스캔 판이 창의 시각을 받을 때와 같은 자로 재고 건다 — 보던 시각(`base`)에서
    더하고 빼신 것만 지금 걸린 시각표 위에 얹고, 그 뒤 대화에서 바꾸셨으면 안 건다."""
    return brief_said(["--window-times", *times, "--window-base", *base, "--chosen-at", at])


def times_due(row: dict | None, eager: bool = False) -> tuple[list[str], list[str], str] | None:
    """「보고 시각」 고름(「이대로 바꾸기」)이 거둘 때인가 — (고르신 시각, 그때 보던 시각, 고른 때) · 아니면 None. 시각은 「HH:MM」 꼴만 ·
    겹침 없이 차례로. 안 받은 고름만(`away_due` 와 같은 다시 해 보기)."""
    picked = row.get("times") if row else None
    if not row or row.get("done") or not (isinstance(picked, list) and picked and all(isinstance(t, str) and C.HHMM.match(t) for t in picked)) \
            or not C.AT.match(str(row.get("at") or "")) or not due(row, eager):
        return None
    base = [t for t in row.get("base") or [] if isinstance(t, str) and C.HHMM.match(t)] if isinstance(row.get("base"), list) else []
    return sorted(set(picked)), sorted(set(base)), str(row["at"])


def said_back(row: dict, said: str, refused: bool) -> dict:
    """스캔의 명령이 고름을 받았나를 그 창에 돌려 적을 칸 — 받은 때 · 그 끝 줄(한 줄로 · `brief_const.SAID_MAX` 에서 자른다) · 안 따랐나."""
    return {**row, "done": stamp(now()), "said": " ".join(said.split())[:C.SAID_MAX], "refused": refused}


def eul(word: str) -> str:
    """조사 「을/를」 — 끝 글자에 받침이 있으면 「을」."""
    last = word[-1:]
    return "을" if "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 else "를"


def collect_said(kind: "Kind", tab: E.Tab, folder: pathlib.Path, hand: "Hand") -> str:
    """창의 고름 하나(자리 밖에서 보기 · 보고 시각)를 거둔다 — 거둘 때면 스캔의 명령으로 걸고 받았나 · 까닭을 그 창에 적는다. 못 부른 고름은
    「해 본 때」를 적어 `SESSION_RETRY_S` 뒤에 다시 해 보고, 그 사이 스캔 판이 받는다(나중의 말씀이 이긴다 — 두 길이 같은 자로 잰다).
    내는 것 — 기록에 남길 한 구절(거둔 것이 없으면 "")."""
    row = dict(E.stored(tab.read(), kind.key)).get("")
    got = kind.due(row)
    if got is None:
        return ""
    refused, said = kind.job(*got)
    if refused is None:
        tab.write([[kind.key, json.dumps({**row, "tried": stamp(now())}, ensure_ascii=False)]], quiet=True)
        return f"{kind.name}{eul(kind.name)} 못 걸었다({said}) — 스캔 판이 받는다"
    tab.write([[kind.key, json.dumps(kind.back(row, said, refused), ensure_ascii=False)], V.row(folder)])
    return f"{kind.name} — {said}"


# ── 비서에게 부탁하기 ────────────────────────────────────────────────────────

def ask_due(row: dict | None, eager: bool = False) -> tuple[str, str, str] | None:
    """창 머리의 부탁이 거둘 때인가 — (친 말, 누른 창의 이름, 들고 온 세션) · 아니면 None. 안 맡은 부탁이 누른 지 `brief_const.ASK_TAKE_S`
    안일 때만 — 그보다 늦은 부탁은 안 연다: 창이 이미 「못 열었다」로 맺었거나 맺는다. 친 말은 읽어 가르지 않는다. 스캔 판은 부탁을 안
    거둔다 — `eager` 를 안 본다."""
    if not row or row.get("done") or row.get("taken") or not C.AT.match(str(row.get("at") or "")):
        return None
    words, at = row.get("words"), E.pressed_at(row)
    if not (isinstance(words, str) and words.strip()) or at is None or (now() - at).total_seconds() >= C.ASK_TAKE_S:
        return None
    return words.strip(), str(row.get("brief") or ""), str(row.get("session") or "")


def open_ask(folder: pathlib.Path, words: str, page: str, session: str, tick) -> tuple[str, str]:
    """부탁 하나를 VS Code 에 연다(곁의 `asks.take`) — (끝, 그 창에 적을 말). `tick` 은 기다리는 동안 거듭 부를 것."""
    try:
        return A.take(folder, words, page, f"{now():%H:%M}", tick, session)
    except Exception as exc:  # noqa: BLE001 — 맡은 부탁은 끝을 꼭 적는다: 손이 넘어지면 창이 「여는 중」에 묶이고 다른 누름도 멈춘다
        return A.FAILED, A.WORDS[A.FAILED].format(why=type(exc).__name__)


def ask_back(taken: dict, state: str, said: str) -> dict:
    """그 창에 돌려 적을 부탁의 칸 — 맡은 칸에 맺은 때 · 끝 · 말."""
    return {**taken, "done": stamp(now()), "state": state, "said": said}


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
    taken = {**row, "taken": stamp(now())}
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


# ── 누름 종류 표 ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Kind:
    """누름 종류 한 줄 — 새 누름은 이 표의 줄 하나와 할 일 함수 하나다. `key` 창의 저장소 열쇠(끝이 「:」 면 머리 — 누름마다 그 뒤가 열쇠) ·
    `due(누름, 스캔 판인가)` 거둘 때면 할 일이 받을 값, 아니면 None · `job` 할 일 · `back(누름, 끝…)` 그 창에 돌려 적을 칸 · `collect(줄, 창,
    폴더, 손)` 창 곁의 손이 이 종류를 거두는 걸음(기록에 남길 한 구절). 스캔 판의 뒷받침(곁의 `ticks.py` 의 `--presses` · `--times` ·
    `--times-done` · `--away-done`)도 같은 줄의 `due` · `job` · `back` 을 부른다 — 두 길이 같은 자로 재고 같은 칸을 적는다."""
    name: str
    key: str
    due: Callable[..., Any]
    job: Callable[..., Any]
    back: Callable[..., dict]
    collect: Callable[..., str]


ASK = Kind("부탁", C.ASK_KEY, ask_due, open_ask, ask_back, collect_ask)
PUT = Kind("일정에 넣기", C.CAL_PREFIX, put_due, settle, put_back, collect_puts)
AWAY = Kind("자리 밖에서 보기", C.AWAY_KEY, away_due, run_away, said_back, collect_said)
TIMES = Kind("보고 시각", C.TIMES_KEY, times_due, run_times, said_back, collect_said)
# 창 곁의 손이 걸음마다 거두는 차례 — 부탁이 맨 앞이다(사람이 VS Code 를 기다리고 있다). 맡길 일의 누름(`brief_const.RUN_PREFIX`)은 이 표에
# 없다 — 누른 지 `brief_const.RUN_TAKE_S` 안에 맡아야 해서, 표의 줄이 오래 걸리는 동안(일정 손 · 스캔의 명령 · VS Code 기다리기)에도
# `Hand.tend` 가 맡는다(곁의 `runs.py`). 표의 줄은 한 걸음에 한 번 돈다
KINDS = (ASK, PUT, AWAY, TIMES)


# ── 스캔 판의 뒷받침 ────────────────────────────────────────────────────────

COUNT_WORDS = {ADDED: "넣음", ALREADY: "이미 있음", MOVED: "그 사이 바뀜", UNSURE: "확인 안 됨", PAST: "지난 약속", SESSION: "세션 없음",
               FAILED: "못 넣음", "later": "다음 판으로", "unwritten": "기록을 못 씀", "busy": "창 곁의 손이 넣는 중",
               "cancelled": "부르기 전에 취소됨", "unread": "기록을 못 읽음"}


def round_once(folder: pathlib.Path, within: int = 0) -> int:
    """스캔 판 한 번 — 열린 보고 창의 누름을 거둬 맺고, 지금 모습을 그 창에 적고, 창 곁의 손이 없으면 띄운다(창에 「일정에 넣기」 카드가
    있거나 「자리 밖에서 보기」 단추가 설 때만 — `hand_wanted`). 열린 보고 창이 없으면 아무것도 안 연다."""
    try:
        cdp = E.Cdp(E.port())
    except E.EdgeGone:
        print("거둘 누름을 못 봤다 — 로그인 Edge 에 못 닿았다")
        return C.EXIT_NO_EDGE
    try:
        tabs = E.brief_tabs(cdp)
        if not tabs:
            print("거둘 누름 없음 — 열린 보고 창이 없다")
            return C.EXIT_OK
        tab = E.Tab(cdp, tabs[0][0])
        if not tab.filed():
            print("거둘 누름 없음 — 보고 창이 아직 다 안 섰다")
            return C.EXIT_OK
        counts = put_presses(PUT, tab, folder, time.monotonic() + within if within > 0 else None, eager=True)
        tab.write([V.row(folder)])          # 창이 스캔이 돈다는 것을 안다 — 누름 직후의 말이 그것으로 갈린다
        started = None
        if any(hand_wanted(folder, (S.page_brief(folder, name) or (None, ""))[1]) for _, name in tabs):
            started = start_hand(folder)
        said = " · ".join(f"{COUNT_WORDS.get(k, k)} {n}" for k, n in counts.items())
        print(("보고 창의 「일정에 넣기」 — " + said if said else "거둘 누름 없음")
              + (" · 창 곁의 손을 다시 띄웠다" if started else ""))
        return C.EXIT_OK
    except E.EdgeGone as exc:
        print(f"거둘 누름을 다 못 봤다 — 로그인 Edge 와 주고받다 멈췄다({exc})")
        return C.EXIT_NO_EDGE
    finally:
        cdp.close()


RECENT_WORDS = {ADDED: "넣음", ALREADY: "같은 일정이 이미 있어 안 넣음", MOVED: "그 사이 일정이 바뀌어 안 넣음", UNSURE: "넣었는지 확인 못 함",
                PAST: "지난 약속이라 안 넣음", SESSION: "사내 로그인이 끊겨 아직 못 넣음", FAILED: "못 넣음", ENTERING: "넣는 중"}


def recent_lines(folder: pathlib.Path) -> list[str]:
    """보고를 짓는 쪽이 읽을 것 — 가장 늦은 보고 글 뒤에 창에서 누르신 「일정에 넣기」의 끝(없으면 빈 목록). 그 글의 이름이 지은 때다."""
    briefs = B.kept_briefs(folder) if folder.is_dir() else []
    if not briefs:
        return []
    since = stamp(B.made_of(briefs[-1].name).astimezone().astimezone(SEOUL))   # 이름은 이 PC 의 시각 — 기록과 같은 서울 꼴로 견준다
    try:
        ledger = read_ledger(folder)
    except S.Unreadable as exc:
        return [f"일정에 넣기 — 기록({folder / LEDGER_FILE})을 못 읽었다({exc}). 지난 보고 뒤 창에서 누르신 카드의 끝을 모른다"]
    rows = sorted((v for v in ledger.values() if isinstance(v, dict) and str(v.get("at", "")) >= since), key=lambda v: str(v.get("at", "")))
    if not rows:
        return []
    return (["일정에 넣기 — 지난 보고 뒤 창에서 누르신 카드의 끝이다. 다시 세울지는 lane.md 「무엇이 내 약속인가」의 「지난번 누르신 카드」:"]
            + [f"- 「{v.get('title', '')}」 {v.get('start', '')} — {RECENT_WORDS.get(str(v.get('state')), str(v.get('state')))}" for v in rows])


def hand_wanted(folder: pathlib.Path | None, text: str) -> bool:
    """창 곁의 거두는 손을 띄울 창인가 — 「일정 넣기」 카드가 있거나, 보고가 걸려 「보고 맞추기」에 「자리 밖에서 보기」 단추가 서거나,
    맡길 일이 있거나, 창 머리에 「비서에게 부탁하기」 칸이 서는 창."""
    return (bool(B.cards_of(text)) or any(t.kind for t in B.tasks_of(text).values()) or V.schedule_of(folder)[0] is not None
            or A.ready())


# ── 창 곁의 손 ──────────────────────────────────────────────────────────────

def quiet() -> dict:
    """창 없이 띄운다 — 윈도에서 콘솔 창이 안 뜨게."""
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}


def start_hand(folder: pathlib.Path) -> bool | None:
    """창 곁의 손을 띄운다 — True 띄웠다 · False 이미 돈다(그 손이 잠금을 쥐고 있다) · None 못 띄웠다. 기다리지 않는다."""
    probe = OsLock(folder / HAND_LOCK)
    if not probe.take():
        return False
    probe.release()
    cmd = [sys.executable, "-X", "utf8", "-I", str(TICKS), "--dir", str(folder), "--watch"]
    flags = (subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if sys.platform == "win32" else 0
    for extra in ((subprocess.CREATE_BREAKAWAY_FROM_JOB if sys.platform == "win32" else 0), 0):
        try:                                       # 띄운 쪽이 작업 묶음(job) 안이면 그 묶음이 끝날 때 함께 끊기지 않게 — 묶음이 안 놓아 주면 그대로
            kw = {"creationflags": flags | extra} if sys.platform == "win32" else {"start_new_session": True}
            subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                             cwd=str(folder), **kw)
            return True
        except OSError:
            continue
    return None


def beat_row() -> list[str]:
    """창 곁의 손이 살아 있다는 숨 표 한 줄 — 창은 `brief_const.HAND_BEAT_S` 의 세 배 넘게 이것이 없으면 손이 없다고 본다."""
    return [C.HAND_KEY, json.dumps({"beat": stamp(now()), "pid": os.getpid()})]


def log(folder: pathlib.Path, line: str, fresh: bool = False) -> None:
    try:
        with (folder / HAND_LOG).open("w" if fresh else "a", encoding="utf-8") as f:
            f.write(f"{stamp(now())} {line}\n")
    except OSError:
        pass


class Hand:
    """창 곁의 손의 한 판 — 붙은 창 · 숨 표를 적은 때 · 맡긴 일(`runs.Runs`)을 든다. `tend` 는 걸음마다, 그리고 오래 걸리는 부름(일정 손 · 스캔의
    명령 · VS Code 를 기다리기)의 사이에도 불린다 — 숨 표를 적고, 새로 맡긴 누름을 맡고, 도는 판의 끝을 창에 적는다. 그 안에서 다시 불리면
    숨 표만 적는다(맡기는 부름이 기다리는 동안 또 맡지 않게)."""

    def __init__(self, folder: pathlib.Path):
        self.folder, self.tab, self.beat, self.inside, self.stepped = folder, None, 0.0, False, 0.0
        self.runs = R.Runs(folder, run_scan)

    def tend(self) -> None:
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
        except Exception as exc:  # noqa: BLE001 — 돌보다 넘어져도 손은 산다: 기다리던 부름(일정 손 · 스캔의 명령)을 버려 두지 않고 다음 걸음이 기록을 다시 읽는다
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
