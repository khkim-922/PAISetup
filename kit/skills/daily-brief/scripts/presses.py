"""보고 창의 「일정에 넣기」 누름을 거둬 그 한 건을 일정에 넣는다 — 일일 보고 스킬의 넣는 손. 사람이 누른 카드의 값과 열쇠로만 일정 손
(형제 스킬 company-calendar 의 `add`)을 부르고, 끝을 그 창에 돌려 적는다. 모델은 이 길에 없다.

    python -X utf8 -I ticks.py --dir <사용자 폴더> --watch                 창 곁에 남아 누름을 바로 거둔다(창을 여는 손이 띄운다)
    python -X utf8 -I ticks.py --dir <사용자 폴더> --presses [--within 초]  열린 보고 창의 누름을 한 번 거둔다(스캔 판의 뒷받침)

누름은 창(file://)의 localStorage `brief-cal:<열쇠>` 에 있다(`assets/report.js`) — 누른 때와 누른 창의 이름만 든다. 넣을 값은 그 창의 보고
글(같은 이름의 .md)에서 그 열쇠의 카드를 찾아 읽는다 — 창이 사람에게 보인 글과 같은 글이다. 일정 손은 미리 보기의 판을 다시 지어 열쇠가
다르면 안 넣는다(그 사이 일정이 바뀌었다).

한 누름은 한 번만 넣는다 — 넣기는 사용자 폴더의 기록(`LEDGER_FILE`)을 OS 잠금(`LEDGER_LOCK`) 아래에서 고친다: 일정 손을 부르기 전에 그
열쇠를 「넣는 중」으로 굳히고, 끝을 받은 뒤 그 끝으로 고친다. 잠금을 쥐고 「넣는 중」을 만나면 앞 손이 넣다 죽은 것이다 — 들었는지
모르니 다시 안 넣고 「확인 안 됨」으로 맺는다(두 벌이 들 수 있다). 창 곁의 손과 스캔 판이 같은 누름을 함께 봐도 기록이 한 번을 지킨다.

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
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 ticks.py · window.py — `-I` 로 돌아도 싣는다
import ticks as T  # noqa: E402
import window as W  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TICKS = HERE / "ticks.py"
CALENDAR = HERE.parents[1] / "company-calendar" / "scripts" / "company_calendar.py"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
LEDGER_FILE = "daily-brief-entries.json"       # 넣은 누름의 기록 — 열쇠마다 끝(넣는 중이면 그것도). 사용자 폴더에 산다
LEDGER_LOCK = "daily-brief-entries.lock"       # 그 기록을 고치는 손 하나 — OS 잠금이라 손이 죽으면 OS 가 푼다
HAND_LOCK = "daily-brief-hand.lock"            # 창 곁의 손 하나 — 쥔 동안 산다. 둘째 손은 못 쥐고 바로 끝난다
HAND_LOG = "daily-brief-hand.log"              # 그 손이 언제 떴고 왜 끝났나 — 마지막 판만(뜰 때마다 새로 쓴다)
LEDGER_KEEP_DAYS = 30                          # 기록을 두는 날 — 창이 날을 건너 열려 있어도 그 안의 누름은 한 번을 지킨다
CALENDAR_TIMEOUT_S = 180                       # 일정 손 한 번의 시한 — 넣기는 세션 받기 · 등록 · 다시 읽기까지 한다. 넘기면 들었는지 모른다
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
QUIET_WRITE = "(function (rows) { rows.forEach(function (r) { localStorage.setItem(r[0], r[1]); }); return rows.length; })(%s)"
# ↑ 숨 표처럼 창이 다시 그릴 까닭이 없는 쓰기 — 저장소 사건을 안 일으킨다(그 창은 2초마다 스스로 숨 표를 읽는다)


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
    try:
        data = json.loads((folder / LEDGER_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_ledger(folder: pathlib.Path, ledger: dict) -> None:
    """새 파일에 다 쓴 뒤 바꿔 끼운다 — 반쯤 쓴 기록이 남지 않는다. 오래된 줄은 걷는다. 못 쓰면 OSError 를 올린다."""
    cut = stamp(now() - dt.timedelta(days=LEDGER_KEEP_DAYS))
    keep = {k: v for k, v in ledger.items() if isinstance(v, dict) and str(v.get("at", "")) >= cut}
    tmp = folder / f".{LEDGER_FILE}.tmp"
    tmp.write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, folder / LEDGER_FILE)
    ledger.clear()
    ledger.update(keep)


# ── 일정 손 ─────────────────────────────────────────────────────────────────

def run_calendar(put: W.Put) -> tuple[int | None, dict]:
    """일정 손의 넣기 한 번 — 카드의 값과 열쇠 그대로. (종료 값 · 답) — 손을 못 띄웠으면 (None, {}), 시한을 넘겼으면 (-1, {})."""
    if not CALENDAR.is_file():
        return None, {"message": "일정 스킬이 곁에 없습니다"}
    cmd = [sys.executable, "-X", "utf8", "-I", str(CALENDAR), "add", "--title", put.title, "--start", put.start, "--end", put.end]
    cmd += ["--place", put.place] if put.place else []
    cmd += ["--private"] if put.private else []
    cmd += ["--confirm", put.key]
    try:
        done = subprocess.run(cmd, capture_output=True, timeout=CALENDAR_TIMEOUT_S, stdin=subprocess.DEVNULL,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **quiet())
    except subprocess.TimeoutExpired:
        return -1, {}
    except OSError as exc:
        return None, {"message": f"일정 손을 못 띄웠습니다({type(exc).__name__})"}
    try:
        answer = json.loads(done.stdout.decode("utf-8", "replace"))
    except ValueError:
        answer = {}
    return done.returncode, answer if isinstance(answer, dict) else {}


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

def card_for(folder: pathlib.Path, press: dict, key: str) -> tuple[W.Put, str] | None:
    """누름이 가리키는 카드 — 누른 창(`brief` — 그 창의 파일 이름)의 보고 글에서 그 열쇠의 카드. 이름이 보고 창의 꼴이 아니거나 글 ·
    카드가 없으면 None."""
    name = str(press.get("brief") or "")
    if not name.endswith(".html") or W.made_of(name) is None:
        return None
    try:
        text = (folder / name).with_suffix(".md").read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return W.cards_of(text).get(key)


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
    tried = T.pressed_at({"at": press.get("tried")}) if press.get("tried") else None
    return tried is None or (now() - tried).total_seconds() >= SESSION_RETRY_S


# ── 창 ──────────────────────────────────────────────────────────────────────

class Tab:
    """열린 보고 창 하나 — 붙어 읽고 쓴다. 새로 열지 않는다(사람의 Edge 에 탭이 뜨면 안 된다)."""

    def __init__(self, cdp: T.Cdp, target: str):
        self.cdp, self.target = cdp, target
        self.session = cdp.call("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]

    def filed(self) -> bool:
        """file: 문서가 섰나 — 막 연 탭은 about:blank 의 저장소를 본다."""
        try:
            return self.cdp.evaluate(self.session, T.WHERE_EXPR) == "file:"
        except T.EdgeGone:
            return False

    def read(self) -> list:
        return json.loads(self.cdp.evaluate(self.session, T.READ_EXPR) or "[]")

    def write(self, rows: list[list[str]], quiet: bool = False) -> None:
        self.cdp.evaluate(self.session, (QUIET_WRITE if quiet else T.WRITE_EXPR) % json.dumps(rows, ensure_ascii=False))

    def row(self, key: str) -> dict | None:
        """창의 저장소에서 지금 그 누름 — 없으면 None."""
        return dict(T.stored(self.read(), W.CAL_PREFIX)).get(key)


def brief_tabs(cdp: T.Cdp) -> list[tuple[str, str]]:
    """열린 보고 창 — (탭, 파일 이름). file: 탭 가운데 이름이 보고 창의 꼴인 것만."""
    out = []
    for t in cdp.call("Target.getTargets").get("targetInfos", []):
        url = str(t.get("url", ""))
        if t.get("type") != "page" or not url.startswith("file:"):
            continue
        name = urllib.parse.unquote(urllib.parse.urlsplit(url).path).rsplit("/", 1)[-1]
        if name.endswith(".html") and W.made_of(name):
            out.append((t["targetId"], name))
    return out


def collect(tab: Tab, folder: pathlib.Path, until: float | None = None, eager: bool = False) -> dict[str, int]:
    """창의 누름을 거둬 맺고 끝을 그 창에 돌려 적는다 — 끝마다의 수. 기록의 잠금을 못 쥐면(다른 손이 넣는 중) 아무것도 안 한다 — {"busy": 1}.
    `until`(monotonic)을 주면 그 안에 일정 손의 시한이 다 들어가는 누름만 시작한다. `eager` 는 `due` 의 것."""
    pending = [(k, v) for k, v in T.stored(tab.read(), W.CAL_PREFIX) if W.PUT_KEY.match(k) and due(v, eager)]
    if not pending:
        return {}
    lock = OsLock(folder / LEDGER_LOCK)
    if not lock.take():
        return {"busy": 1}
    counts: dict[str, int] = {}
    try:
        ledger = read_ledger(folder)
        for key, press in pending:
            if until is not None and time.monotonic() + CALENDAR_TIMEOUT_S > until:
                counts["later"] = counts.get("later", 0) + 1
                continue
            try:
                got = settle(folder, ledger, key, press, lambda k=key, v=press: tab.row(k) == v)
            except OSError:                       # 기록을 못 썼다 — 일정 손을 안 불렀거나 끝을 못 남겼다. 누름은 그대로 두고 다음에
                counts["unwritten"] = counts.get("unwritten", 0) + 1
                continue
            if got is None:                       # 부르기 직전에 사람이 취소했다 — 아무것도 안 하고 창에도 안 적는다
                counts["cancelled"] = counts.get("cancelled", 0) + 1
                continue
            state, said = got
            counts[state] = counts.get(state, 0) + 1
            row = {**press, "state": state, "said": said}
            if state == SESSION:
                row["tried"] = stamp(now())
            else:
                row["done"] = stamp(now())
            tab.write([[W.CAL_PREFIX + key, json.dumps(row, ensure_ascii=False)]])
    finally:
        lock.release()
    return counts


# ── 스캔 판의 뒷받침 ────────────────────────────────────────────────────────

COUNT_WORDS = {ADDED: "넣음", ALREADY: "이미 있음", MOVED: "그 사이 바뀜", UNSURE: "확인 안 됨", PAST: "지난 약속", SESSION: "세션 없음",
               FAILED: "못 넣음", "later": "다음 판으로", "unwritten": "기록을 못 씀", "busy": "창 곁의 손이 넣는 중",
               "cancelled": "부르기 전에 취소됨"}


def round_once(folder: pathlib.Path, within: int = 0) -> int:
    """스캔 판 한 번 — 열린 보고 창의 누름을 거둬 맺고, 지금 모습을 그 창에 적고, 창 곁의 손이 없으면 띄운다(창에 「일정에 넣기」 카드가
    있을 때만). 열린 보고 창이 없으면 아무것도 안 연다."""
    try:
        cdp = T.Cdp(T.edge_port())
    except T.EdgeGone:
        print("거둘 누름을 못 봤다 — 로그인 Edge 에 못 닿았다")
        return T.EXIT_NO_EDGE
    try:
        tabs = brief_tabs(cdp)
        if not tabs:
            print("거둘 누름 없음 — 열린 보고 창이 없다")
            return T.EXIT_OK
        tab = Tab(cdp, tabs[0][0])
        if not tab.filed():
            print("거둘 누름 없음 — 보고 창이 아직 다 안 섰다")
            return T.EXIT_OK
        counts = collect(tab, folder, time.monotonic() + within if within > 0 else None, eager=True)
        tab.write([T.state_row(folder)])          # 창이 스캔이 돈다는 것을 안다 — 누름 직후의 말이 그것으로 갈린다
        started = None
        if any(W.cards_of(read_brief(folder, name)) for _, name in tabs):
            started = start_hand(folder)
        said = " · ".join(f"{COUNT_WORDS.get(k, k)} {n}" for k, n in counts.items())
        print(("보고 창의 「일정에 넣기」 — " + said if said else "거둘 누름 없음")
              + (" · 창 곁의 손을 다시 띄웠다" if started else ""))
        return T.EXIT_OK
    except T.EdgeGone as exc:
        print(f"거둘 누름을 다 못 봤다 — 로그인 Edge 와 주고받다 멈췄다({exc})")
        return T.EXIT_NO_EDGE
    finally:
        cdp.close()


RECENT_WORDS = {ADDED: "넣음", ALREADY: "같은 일정이 이미 있어 안 넣음", MOVED: "그 사이 일정이 바뀌어 안 넣음", UNSURE: "넣었는지 확인 못 함",
                PAST: "지난 약속이라 안 넣음", SESSION: "사내 로그인이 끊겨 아직 못 넣음", FAILED: "못 넣음", ENTERING: "넣는 중"}


def recent_lines(folder: pathlib.Path) -> list[str]:
    """보고를 짓는 쪽이 읽을 것 — 가장 늦은 보고 글 뒤에 창에서 누르신 「일정에 넣기」의 끝(없으면 빈 목록). 그 글의 이름이 지은 때다."""
    briefs = W.kept_briefs(folder) if folder.is_dir() else []
    if not briefs:
        return []
    since = stamp(W.made_of(briefs[-1].name).astimezone().astimezone(SEOUL))   # 이름은 이 PC 의 시각 — 기록과 같은 서울 꼴로 견준다
    rows = sorted((v for v in read_ledger(folder).values() if isinstance(v, dict) and str(v.get("at", "")) >= since),
                  key=lambda v: str(v.get("at", "")))
    if not rows:
        return []
    return (["일정에 넣기 — 지난 보고 뒤 창에서 누르신 카드의 끝이다. 다시 세울지는 lane.md 「무엇이 내 약속인가」의 「지난번 누르신 카드」:"]
            + [f"- 「{v.get('title', '')}」 {v.get('start', '')} — {RECENT_WORDS.get(str(v.get('state')), str(v.get('state')))}" for v in rows])


def read_brief(folder: pathlib.Path, page_name: str) -> str:
    try:
        return (folder / page_name).with_suffix(".md").read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


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


def log(folder: pathlib.Path, line: str, fresh: bool = False) -> None:
    try:
        with (folder / HAND_LOG).open("w" if fresh else "a", encoding="utf-8") as f:
            f.write(f"{stamp(now())} {line}\n")
    except OSError:
        pass


def watch(folder: pathlib.Path) -> int:
    """창 곁의 손 — 열린 보고 창이 있는 동안 `STEP_S` 마다 누름을 거두고 `W.HAND_BEAT_S` 마다 숨 표를 적는다. 열린 보고 창이 없어지면 끝나고,
    Edge 와 연달아 `ERRORS_MOST` 번 못 주고받으면 끝난다. 둘째 손은 잠금을 못 쥐고 바로 끝난다."""
    hand = OsLock(folder / HAND_LOCK)
    if not hand.take():
        return T.EXIT_OK
    log(folder, f"떴다 — pid {os.getpid()}", fresh=True)
    errors, cdp, tab, beat, seen = 0, None, None, 0.0, time.monotonic()
    try:
        while True:
            try:
                if cdp is None:
                    cdp, tab = T.Cdp(T.edge_port()), None
                tabs = brief_tabs(cdp)
                if not tabs:
                    if time.monotonic() - seen >= NO_TAB_GRACE_S:
                        log(folder, "끝났다 — 열린 보고 창이 없다")
                        return T.EXIT_OK
                    time.sleep(STEP_S)
                    continue
                seen = time.monotonic()
                if tab is None or tab.target not in {t for t, _ in tabs}:
                    tab = Tab(cdp, tabs[0][0])
                if tab.filed():
                    if time.monotonic() - beat >= W.HAND_BEAT_S:
                        tab.write([[W.HAND_KEY, json.dumps({"beat": stamp(now()), "pid": os.getpid()})]], quiet=True)
                        beat = time.monotonic()
                    counts = collect(tab, folder)
                    if counts:
                        log(folder, "거뒀다 — " + " · ".join(f"{COUNT_WORDS.get(k, k)} {n}" for k, n in counts.items()))
                errors = 0
            except T.EdgeGone as exc:
                errors += 1
                if cdp is not None:
                    cdp.close()
                cdp, tab = None, None
                if errors >= ERRORS_MOST:
                    log(folder, f"끝났다 — 로그인 Edge 와 {errors}번 못 주고받았다({exc})")
                    return T.EXIT_NO_EDGE
            time.sleep(STEP_S)
    finally:
        if cdp is not None:
            cdp.close()
        hand.release()
