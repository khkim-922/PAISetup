"""메일함 스캔 스킬이 새 메일 · 바뀜을 쌓고, 덜 본 판에 거짓을 안 적고, 아침 보고를 하루 한 번 띄우나를 문다.

    python -X utf8 -I check_scan.py [스크립트 폴더] [--teeth]

층 — 쓰는 사람의 계약. 스캔 스크립트를 명령 그대로 부르고, 곁의 회사 메일 손을 그 손 검사의 가짜 메일함에 대어 진짜로 부른다.
남기는 까닭 — 판정마다 check-design 1 절의 넷을 다 지난다(판정별 표 · 못 재는 것은 `references/DESIGN.md` 「검사가 남는 까닭」).
언제 걷나 — 스캔 스킬이 빠지거나, 손이 JSON 꼴을 내어 스캔이 그것을 읽게 되면 꼴 판정을 그 꼴의 판정으로 바꾼다.

폴더를 안 주면 이 파일의 폴더를 잰다. `--teeth` 는 판정마다 그 판정이 지키는 한 줄을 끈 사본으로 같은 판을 돌려 빨강을 본다.
기대값은 스킬 글 · 설계 문서의 문장과 판마다 심은 메일에서 낸다 — 스크립트를 돌린 값에서 거꾸로 내지 않는다.
종료 값 — 끝 줄이 「통과 N/N」이면 0, 어긋나면 1, 못 잰 판정이 있거나 형제 스킬 · node · 가짜 메일함이 없으면 2.
"""

from __future__ import annotations

import ast
import dataclasses
import fnmatch
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

# 판정 기호 · 한글을 찍다가 cp949 콘솔 · 파이프에서 죽지 않게 — 통과한 검사가 실패로 읽힌다
sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).resolve().parent
SKILLS = HERE.parents[1]                         # 이 스킬과 형제 스킬이 나란히 선 스킬 뿌리(저장소 · 설치 · 게이트의 내보낸 판이 다 같은 꼴)
HAND_DIR = SKILLS / "company-mail" / "scripts"
HAND = HAND_DIR / "mail.py"
FAKE_FILE = HAND_DIR / "check_inbox.py"
JOURNAL = SKILLS / "mailbox-tidy" / "scripts" / "journal.py"
WINDOW = SKILLS / "daily-brief" / "scripts" / "window.py"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
TEETH = "--teeth" in sys.argv[1:]
SCRIPTS = pathlib.Path(ARGS[0]).resolve() if ARGS else HERE
TIMEOUT_S = 180
WORKERS = 4
KST = timezone(timedelta(hours=9))

# ── 판정 한 벌 — 이름 → 맞다 · 어긋났다 · 못 쟀다. 종료 값은 0 맞다 · 1 어긋났다 · 2 못 쟀다 ─────────────────────
EXIT_OK, EXIT_MISMATCH, EXIT_UNMEASURED = 0, 1, 2
PASSES: list[str] = []
FAILS: list[str] = []
UNMEASURED: list[str] = []


class Unmeasured(SystemExit):
    """「못 쟀다」로 그 자리에서 나가는 손 — 까닭을 찍고 2 로 나간다. `SystemExit("글자")` 는 1 로 나가 「어긋났다」로 읽혀서 쓰지 않는다."""

    def __init__(self, why):
        super().__init__(EXIT_UNMEASURED)
        self.why = str(why)
        print(self.why)

    def __str__(self):
        return self.why


def report(name: str, ok: bool, detail=()) -> None:
    (PASSES if ok else FAILS).append(name)
    print(f"{'✓' if ok else '✗'} {name}")
    for row in detail if not ok else ():
        print(f"    {row}")


def edge(text: str) -> None:
    """판정이 아니라 통과에도 보여야 하는 말 — 셈에 안 든다."""
    print(f"  ⚠ {text}")


def unmeasured(name: str, why: str) -> None:
    UNMEASURED.append(name)
    print(f"? {name} — 못 쟀다: {why}")


# ── 가짜 메일함 — 곁의 손 검사를 그 자리에서 싣는다 ───────────────────────────────────────────

def load_fake():
    """`company-mail/scripts/check_inbox.py` 를 모듈로 싣는다 — 그 파일은 `sys.argv[1]` 의 나무(곁의 inbox.py)를 실어 잰다."""
    if not FAKE_FILE.is_file() or not HAND.is_file():
        raise Unmeasured(f"[못 잼] 곁의 회사 메일 스킬이 없다: {HAND_DIR} — 손(mail.py)과 가짜 메일함(check_inbox.py)이 거기 있어야 한다")
    saved = sys.argv
    sys.argv = [str(FAKE_FILE), str(HAND_DIR)]
    try:
        spec = importlib.util.spec_from_file_location("mailbox_scan_fake_inbox", FAKE_FILE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as exc:  # noqa: BLE001 — 무엇으로 지든 가짜를 못 세운 것이다
        raise Unmeasured(f"[못 잼] 가짜 메일함을 못 실었다: {exc!r}") from exc
    finally:
        sys.argv = saved


fake = load_fake()
FakeMail, FakeSent, folder_unid, internal_sender = fake.FakeMail, fake.FakeSent, fake.folder_unid, fake.internal_sender


# ── 심는 메일 — 지어낸 회사 · 사람(실제 회사 · 사람을 싣지 않는다) ─────────────────────────────────
PEER = internal_sender("윤가람", "gr.yoon@gaon.example", "Garam Yoon")
EXT = "j.weber@altamira-cells.example"
NOTICE = "notice@gaon.example"
LATER = "q.ross@meridian-tech.example"          # 첫 판 뒤에 처음 메일을 보내는 분
BASE = datetime(2026, 10, 1, 9, 0, tzinfo=KST)
AFTER_BASE = "2026-10-10"                       # 심은 바닥 메일(10월 1 ~ 4일) 뒤 · 새로 오는 메일(지금) 앞의 날
F1, F2 = "가 협력사", "나 프로젝트"             # 손의 폴더 목록은 경로 차례다 — F1 을 F2 보다 먼저 읽는다
RENAMED = "가 협력사 2026"                         # 사람이 웹메일에서 F1 의 이름을 바꾼 뒤의 이름


def unid(n: int) -> str:
    return f"{0x5CA0000000000000 + n:032X}"


def stamp(when: datetime) -> str:
    """가짜 메일함의 때 꼴 — 서울 YYYYMMDDHHMMSS."""
    return when.astimezone(KST).strftime("%Y%m%d%H%M%S")


def mail(n: int, subject: str, day: int, sender: str = PEER, *, unread: bool = True, folder: str = "", when: datetime | None = None,
         kind=None, **extra) -> FakeMail:
    return (kind or FakeMail)(unid(n), subject, stamp(when or BASE + timedelta(days=day, minutes=n)), sender, "T", unread=unread,
                              to_102=None, folder=folder, **extra)


def sent(n: int, subject: str, day: int, to: str) -> FakeSent:
    return FakeSent(unid(n), subject, stamp(BASE + timedelta(days=day, minutes=n)), to)


# ── 세계 ─────────────────────────────────────────────────────────────────

def sibling_hand() -> pathlib.Path:
    """곁의 회사 메일 손 — 이 저장소 · 설치에서 맞는 판은 늘 이 스킬과 나란히 선 그 폴더의 것이다."""
    if not HAND.is_file():
        raise Unmeasured(f"[못 잼] 곁의 회사 메일 손이 없다: {HAND}")
    return HAND


LOGGED_HAND = '''import json, runpy, sys
with open({log!r}, "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:], ensure_ascii=False) + "\\n")
sys.argv = [{hand!r}, *sys.argv[1:]]
runpy.run_path({hand!r}, run_name="__main__")
'''
# claude 대역이 적는 것 — 진짜 claude 를 안 띄우고, 스캔이 무엇을 어디서 어떻게 띄웠나만 남긴다
STUB_RECORD = '''import json, os, sys
with open({log!r}, "a", encoding="utf-8") as f:
    f.write(json.dumps({{"argv": sys.argv[1:], "cwd": os.getcwd(), "stdin": sys.stdin.read(),
                        "nested": [k for k in ("CLAUDECODE",) if k in os.environ]}}, ensure_ascii=False) + "\\n")
'''
# 손의 끝 줄 꼴이 바뀐 판 — 목록의 끝 줄 「N통을 보였다」를 「N통을 냈다」로(손의 줄 끝 꼴이 바뀌는 갈래)
DRIFTED_HAND = '''import subprocess, sys
done = subprocess.run([sys.executable, "-X", "utf8", "-I", {hand!r}, *sys.argv[1:]], capture_output=True)
out = done.stdout.decode("utf-8").replace("통을 보였다", "통을 냈다")
sys.stdout.buffer.write(out.encode("utf-8"))
sys.exit(done.returncode)
'''


class World:
    """가짜 메일함 하나 · 사용자 폴더 하나 · 스캔 스크립트 폴더 하나 — 판정 하나가 처음부터 끝까지 쓴다(앞 판정의 상태를 안 물려받는다)."""

    def __init__(self, scripts: pathlib.Path, hand: pathlib.Path, mails, sent_mails=(), folders=(), box_cls=fake.FakeDomino, wrap: str = ""):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="scan-check-"))
        self.scripts, self.real_hand = scripts, hand
        self.box = box_cls(mails=mails, sent=sent_mails, folders=folders)   # 심는 메일 · 지는 보기(broken)는 곁의 가짜가 인자로 받는다
        self.cookies = self.tmp / "mailbox-session.json"   # 이 메일함을 가리키는 쿠키 파일(Playwright 저장 상태 꼴)
        self.cookies.write_text(json.dumps({"cookies": [
            {"name": fake.COOKIE[0], "value": fake.COOKIE[1], "domain": "127.0.0.1", "path": "/", "expires": -1,
             "httpOnly": True, "secure": False}], "origins": []}), encoding="utf-8")
        stub = self.tmp / "session_hand_standin.js"   # 세션 손 대역 — 진짜 Edge 를 안 띄우고 가짜 메일함의 쿠키 파일 자리를 끝 줄로 낸다
        stub.write_text(f"console.log({json.dumps(str(self.cookies))});\n", encoding="utf-8")
        self.log = self.tmp / "hand-calls.jsonl"
        self.hand = hand
        if wrap:
            self.hand = self.tmp / "hand_wrapper.py"
            self.hand.write_text((LOGGED_HAND if wrap == "log" else DRIFTED_HAND).format(log=str(self.log), hand=str(hand)), encoding="utf-8")
        self.home = self.tmp / "home"
        self.env = {**os.environ, "MAIL_SECRETARY_HOME": str(self.home), "MAILBOX_URL": self.box.url, "MAILBOX_COOKIES": str(self.cookies),
                    "EP_SESSION_HAND": str(stub), "MAIL_ORG_CACHE_DIR": str(self.tmp / "org"), "MAILBOX_SCAN_HAND": str(self.hand)}
        self.env.pop("SECRETARY_SKILLS", None)

    def _run(self, script: pathlib.Path, args, inp: str | None = None) -> tuple[int, str]:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(script), *args], env=self.env, capture_output=True,
                              input=inp.encode("utf-8") if inp is not None else None, timeout=TIMEOUT_S)
        return done.returncode, done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")

    def scan(self, *args) -> tuple[int, str]:
        return self._run(self.scripts / "scan.py", args)

    def read(self, *args) -> tuple[int, str]:
        return self._run(self.scripts / "reader.py", args)

    def real(self, *args) -> str:
        return self._run(self.real_hand, args)[1]

    def journal(self, *args, inp: str = "") -> str:
        return self._run(JOURNAL, args, inp)[1]

    def folder(self) -> pathlib.Path:
        return self.home / "mailbox-scan"

    def state(self) -> dict:
        try:
            return json.loads((self.folder() / "state.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def jsonl(self, name: str) -> list[dict]:
        path = self.folder() / name if name != "calls" else self.log
        try:
            return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        except OSError:
            return []

    def events(self) -> list[dict]:
        return self.jsonl("events.jsonl")

    def runs(self) -> list[dict]:
        return self.jsonl("runs.jsonl")

    def last(self) -> dict:
        """마지막 판 기록 — 없으면 빈 것(판이 하나도 안 적혔다)."""
        return (self.runs() or [{}])[-1]

    # ── 아침 보고 — 진짜 claude 대신 받은 것을 적고 끝나는 대역 ─────────────────────────────
    def stub_claude(self) -> pathlib.Path:
        """claude 대역 — 명령줄 · 자리 · 표준 입력 · 겹친 세션 변수를 한 줄씩 적고 끝난다. npm 판처럼 .cmd 로 선다(윈도)."""
        record = self.tmp / "claude_record.py"
        record.write_text(STUB_RECORD.format(log=str(self.claude_log)), encoding="utf-8")
        if sys.platform == "win32":
            stub = self.tmp / "claude.cmd"
            stub.write_text(f'@"{sys.executable}" "{record}" %*\r\n', encoding="utf-8")
        else:
            stub = self.tmp / "claude"
            stub.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{record}" "$@"\n', encoding="utf-8")
            stub.chmod(0o755)
        return stub

    @property
    def claude_log(self) -> pathlib.Path:
        return self.tmp / "claude-launches.jsonl"

    def set_brief(self, at: str) -> tuple[int, str]:
        return self.scan("brief", "--at", at, "--claude", str(self.stub_claude()))

    def launches(self, expect: int = 0, wait_s: float = 60) -> list[dict]:
        """대역이 적은 띄움 — `expect` 개가 설 때까지(띄움은 기다리지 않고 떠나 늦게 선다) 기다린다. 0 이면 잠깐만 본다."""
        end = time.monotonic() + (wait_s if expect else 3)
        while True:
            try:
                got = [json.loads(x) for x in self.claude_log.read_text(encoding="utf-8").splitlines() if x.strip()]
            except OSError:
                got = []
            if (expect and len(got) >= expect) or time.monotonic() >= end:
                return got
            time.sleep(0.3)

    def day(self) -> dict:
        return self.state().get("brief") or {}

    def edit_state(self, change) -> None:
        """지금 모습을 고쳐 둔다 — 판 사이(도는 판이 없을 때)에만. 때가 흐른 것 · 날이 바뀐 것 · 지금 모습을 잃은 것을 흉내 낸다."""
        state = self.state()
        change(state)
        (self.folder() / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def rewind(self, minutes: float) -> None:
        """그날 살펴본 때를 `minutes` 분 앞으로 민다 — 그만큼 때가 흐른 판이다."""
        def back(state):
            for t in (state.get("brief") or {}).get("tries") or []:
                t["at"] = (datetime.fromisoformat(t["at"]) - timedelta(minutes=minutes)).isoformat(timespec="seconds")
        self.edit_state(back)

    def hand_calls(self, name: str) -> int:
        return sum(1 for c in self.jsonl("calls") if c and c[0] == name)

    def close(self) -> None:
        self.box.close()
        shutil.rmtree(self.tmp, ignore_errors=True)


def kinds(events, kind: str) -> dict[str, dict]:
    return {e.get("unid"): e for e in events if e.get("kind") == kind}


class Verdicts:
    """한 판의 판정들 — 이름 → (맞다, 어긋난 자리). `need` 가 하나라도 어긋나면 그 판정은 빨강이다."""

    def __init__(self):
        self.got: dict[str, tuple[bool, list[str]]] = {}

    def need(self, name: str, ok: bool, why: str) -> None:
        okay, details = self.got.get(name, (True, []))
        self.got[name] = (okay and bool(ok), details + ([] if ok else [why]))


# ── 판 — 한 판이 판정 몇을 낸다 ──────────────────────────────────────────────────

J_FIRST, J_NEW, J_READS, J_SLICE = "첫 판은 바닥만 적는다", "새 메일이 쌓인다", "메일함을 안 바꾼다(손의 목록 명령만)", "읽는 명령이 잘라 낸다"
J_USER, J_SECRETARY = "사람이 연 · 옮긴 · 지운 메일이 바뀜으로 선다", "비서가 한 일은 비서 · 도중은 모름"
J_PARTIAL, J_INRUN = "덜 본 판은 견주지 않고 다음 판이 잇는다", "한 판 안에서 옮겨진 메일에 거짓 사라짐이 없다"
J_SESSION, J_BUSY, J_STALE, J_SHAPE = "세션이 끊기면 멈추고 적고 안 두드린다", "겹쳐 안 돈다", "남은 잠금이 풀린다", "손의 글 꼴이 바뀌면 멈춘다"
J_MINUTE, J_THIRD = "폴더 메일의 때가 분까지여도 풀려 새 메일에 선다", "때의 꼴이 둘 밖이면 멈춘다"
J_TASK, J_ALONE = "예약 — 한 번에 하나 · 주기 · 손을 명령줄에", "홀로 선다 — 싣는 것"
J_DEFAULTS = "예약 — 기본 주기는 새 메일 15분 · 전체 120분이고 전체 주기는 잇는 기한보다 짧아야 걸린다"
J_SIGNALS = "정리 신호의 재료 — 받은편지함의 지금과 흐름 · 규칙이 채우는 폴더 · 폴더마다 가장 새 메일의 때를 센다"
# 사용자가 정한 기본 주기 — 회사 PC 에서 한 판을 잰 뒤 바뀌면 여기와 함께 바꾼다
DEFAULT_EVERY, DEFAULT_FULL_EVERY, PENDING_LIMIT = 15, 120, 180


def story_new(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """첫 판 → 새 메일 판 → 읽는 명령. 받은편지함 셋 · 보낸편지함 하나."""
    v = Verdicts()
    base = [mail(1, "증설 시나리오 검토 요청", 0), mail(2, "Q1 volume forecast", 1, EXT, unread=False),
            mail(3, "[공지] 분기 마감 일정", 2, NOTICE)]
    w = World(scripts, hand, base, [sent(4, "회신: 증설 시나리오", 3, "윤가람")], wrap="log")
    try:
        code, out = w.scan("run")
        v.need(J_FIRST, code == 0 and w.last().get("outcome") == "first", f"첫 판의 끝이 first 가 아니다: {out[-300:]}")
        v.need(J_FIRST, w.events() == [], f"첫 판이 바뀜 · 새 메일을 냈다: {[e.get('kind') for e in w.events()]}")
        v.need(J_FIRST, len(w.state().get("mails") or {}) == 4, f"첫 판의 바닥이 메일 넷이 아니다: {len(w.state().get('mails') or {})}")
        now = datetime.now(KST)
        w.box.mails[unid(5)] = mail(5, "견적서 송부", 0, LATER, when=now - timedelta(seconds=30))
        w.box.mails[unid(6)] = mail(6, "회의록 공유", 0, PEER, unread=False, when=now)        # 스캔보다 먼저 사람이 열었다
        before_calls = len(w.jsonl("calls"))
        code, out = w.scan("run")
        new = kinds(w.events(), "new")
        v.need(J_NEW, code == 0 and set(new) == {unid(5), unid(6)}, f"새 메일 판이 새 메일 둘을 안 적었다: {sorted(new)} · {out[-200:]}")
        v.need(J_NEW, set(kinds(w.events(), "opened")) == {unid(6)}, "스캔보다 먼저 연 메일 하나만 「처음 볼 때 이미 읽음」이어야 한다")
        v.need(J_NEW, w.last().get("mode") == "new", "그 판이 새 메일만 보는 판이 아니다")
        calls = w.jsonl("calls")[before_calls:]
        v.need(J_NEW, [c[:2] for c in calls] == [["list", "--since"]], f"새 메일 판의 손 부르기가 「이 시각 뒤」 목록 한 번이 아니다: {calls}")
        _, shown = w.read("new", "--since", AFTER_BASE)
        v.need(J_NEW, unid(5) in shown and unid(6) in shown and "처음 볼 때 이미 읽음" in shown, "읽는 명령이 새 메일을 안 냈다")
        # 메일함을 안 바꾼다 — 스캔이 부른 손의 명령이 다 목록 명령이고, 메일함에 바꾸는 요청이 안 갔다
        allowed = {"folders", "rules", "list"}
        odd = [c for c in w.jsonl("calls") if c[0] not in allowed]
        v.need(J_READS, not odd, f"스캔이 목록 밖의 손 명령을 불렀다: {odd}")
        v.need(J_READS, w.box.changes == [] and w.box.unread() == {unid(1), unid(3), unid(5)}, f"메일함이 바뀌었다: {w.box.changes}")
        # 읽는 명령이 잘라 낸다 · 마지막으로 다 본 때를 함께 낸다
        later = (datetime.now(KST) + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M")
        _, none_after = w.read("new", "--since", later)
        v.need(J_SLICE, unid(5) not in none_after and unid(6) not in none_after and unid(1) not in none_after,
               "그 시각 뒤에 온 것도 처음 본 것도 아닌 메일이 「새 메일」에 섰다")
        v.need(J_SLICE, unid(1) not in shown, "첫 판의 바닥이 「새 메일」에 섰다")
        _, unread_only = w.read("mails", "--unread")
        v.need(J_SLICE, unid(5) in unread_only and unid(6) not in unread_only and unid(2) not in unread_only, "안 읽음 거르기가 틀렸다")
        _, from_peer = w.read("mails", "--from", "gr.yoon")
        v.need(J_SLICE, unid(1) in from_peer and unid(6) in from_peer and unid(5) not in from_peer, "보낸 분 거르기가 틀렸다")
        _, no_changes = w.read("changes", "--since", later)
        v.need(J_SLICE, "뒤 바뀜 0건" in no_changes, "그 시각 뒤 바뀜이 없는데 섰다")
        for out_ in (shown, none_after, unread_only, no_changes):
            v.need(J_SLICE, "마지막으로 다 본 때" in out_, "읽는 명령이 마지막으로 다 본 때를 안 냈다")
    finally:
        w.close()
    return v


def story_user(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """사람이 웹메일에서 한 일 — 읽기 · 옮기기 · 받은편지함과 폴더의 지우기 · 폴더 이름 바꾸기."""
    v = Verdicts()
    base = [mail(1, "읽을 메일", 0), mail(2, "옮길 메일", 1), mail(3, "지울 메일", 2), mail(4, "그대로", 3),
            mail(5, "폴더 메일", 0, EXT, folder=F1), mail(6, "폴더에서 지울 메일", 1, EXT, folder=F1)]
    w = World(scripts, hand, base, [sent(7, "보낸 메일", 2, "gr.yoon@gaon.example")])
    try:
        w.scan("run")
        b = w.box
        b.mails[unid(1)].unread = False
        b.mails[unid(2)].folder = F1
        b.mails[unid(3)].folder = "($Trash)"
        b.mails[unid(6)].folder = "($Trash)"
        node = b.node_of(F1)
        b.tree[node] = (RENAMED, b.tree[node][1])
        for m in b.mails.values():
            if m.folder == F1:
                m.folder = RENAMED
        w.scan("run", "--full")
        ev = w.events()
        read, moved, gone = kinds(ev, "read"), kinds(ev, "moved"), kinds(ev, "gone")
        v.need(J_USER, read.get(unid(1), {}).get("by") == "user", "사람이 연 메일이 「읽음이 됨 · 사람」으로 안 섰다")
        v.need(J_USER, moved.get(unid(2), {}).get("to") == ["folder", RENAMED] and moved[unid(2)].get("from") == ["inbox", ""]
               and moved[unid(2)].get("by") == "user", f"옮긴 메일이 어디서 어디로 · 사람으로 안 섰다: {moved.get(unid(2))}")
        v.need(J_USER, moved.get(unid(5), {}).get("from") == ["folder", F1] and moved[unid(5)].get("to") == ["folder", RENAMED],
               "이름이 바뀐 폴더의 메일이 옛 이름 → 새 이름으로 안 섰다")
        v.need(J_USER, {(e["kind"], e.get("path")) for e in ev if e["kind"].startswith("folder")} ==
               {("folder-removed", F1), ("folder-added", RENAMED)}, "폴더 이름 바꿈이 지우기 · 만들기로 안 섰다")
        v.need(J_USER, gone.get(unid(3), {}).get("from") == ["inbox", ""] and gone[unid(3)].get("by") == "user", "지운 받은편지함 메일이 「사라짐」으로 안 섰다")
        v.need(J_USER, unid(6) not in gone and (w.state().get("mails") or {}).get(unid(6), {}).get("missing_since"),
               "폴더에서 지운 메일은 한 판 미뤄 가려야 한다(그 상자가 가장 먼저 읽은 상자가 아니다)")
        v.need(J_USER, unid(4) not in moved and unid(4) not in read and unid(4) not in gone, "그대로 둔 메일에 바뀜이 섰다")
        w.scan("run", "--full")
        gone = kinds(w.events(), "gone")
        v.need(J_USER, gone.get(unid(6), {}).get("from") == ["folder", F1], "폴더에서 지운 메일이 다음 판에도 「사라짐」으로 안 섰다")
        _, out = w.read("changes", "--since", "2026-10-01")
        v.need(J_USER, "읽음이 됨 · 사람" in out and f"옮겨짐 받은편지함 → 폴더 {RENAMED} · 사람" in out and "사라짐(받은편지함에서) · 사람" in out,
               "읽는 명령이 바뀜을 사람 말로 안 냈다")
    finally:
        w.close()
    return v


def story_secretary(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """비서(정리 스킬)가 손의 미리 보기 → 기록 잡기 → 실행 → 기록 맺기로 옮기고 지운 메일 · 잡아 둔 채 도중인 바꿈 · 사람이 옮긴 메일."""
    v = Verdicts()
    base = [mail(1, "비서가 옮길 메일", 0), mail(2, "도중인 바꿈", 1), mail(3, "사람이 옮길 메일", 2), mail(4, "비서가 지울 메일", 3),
            mail(5, "폴더 메일", 0, EXT, folder=F1)]
    w = World(scripts, hand, base)
    try:
        w.scan("run")

        def secretary(kind: str, target: list[str], *unids: str, finish: bool = True) -> None:
            verb = {"move": "move", "trash": "trash"}[kind]
            preview = w.real(f"preview-{verb}", *unids, *target)
            w.journal("hold", kind, *target, *unids, inp=preview)
            key = re.search(r"확인 열쇠: ([0-9a-f]+)", preview).group(1)
            applied = w.real(f"apply-{verb}", *unids, *target, "--confirm", key)
            if finish:
                w.journal("done", inp=applied)
        secretary("move", ["--to", F1], unid(1))
        secretary("trash", [], unid(4))
        w.box.mails[unid(3)].folder = F1
        secretary("move", ["--to", F1], unid(2), finish=False)
        w.scan("run", "--full")
        moved, gone = kinds(w.events(), "moved"), kinds(w.events(), "gone")
        v.need(J_SECRETARY, moved.get(unid(1), {}).get("by") == "secretary", f"비서가 옮긴 메일이 비서로 안 섰다: {moved.get(unid(1))}")
        v.need(J_SECRETARY, gone.get(unid(4), {}).get("by") == "secretary", f"비서가 지운 메일이 비서로 안 섰다: {gone.get(unid(4))}")
        v.need(J_SECRETARY, moved.get(unid(2), {}).get("by") == "unknown", f"잡아 둔 채 도중인 바꿈이 모름으로 안 섰다: {moved.get(unid(2))}")
        v.need(J_SECRETARY, moved.get(unid(3), {}).get("by") == "user", "사람이 옮긴 메일이 사람으로 안 섰다(양성 대조)")
        _, out = w.read("changes", "--since", "2026-10-01")
        v.need(J_SECRETARY, "비서 2" in out and "· 비서 ·" in out and "모름(정리의 바꿈이 도중이다)" in out, "읽는 명령이 바꾼 이를 안 냈다")
    finally:
        w.close()
    return v


def story_partial(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """폴더 보기 하나가 지는 판 — 견주지 않고 다 본 상자를 남기고, 고친 뒤 다음 판이 남은 상자만 읽어 맺는다."""
    v = Verdicts()
    base = [mail(1, "그대로", 0), mail(2, "진짜로 지울 메일", 1), mail(3, "가 폴더 메일", 0, EXT, folder=F1),
            mail(4, "나 폴더 메일 하나", 0, EXT, folder=F2), mail(5, "나 폴더 메일 둘", 1, EXT, folder=F2)]
    w = World(scripts, hand, base, [sent(6, "보낸 메일", 2, "gr.yoon@gaon.example")], wrap="log")
    try:
        w.scan("run")
        cursor = w.state().get("cursor")
        w.box.broken[folder_unid(F2).lower()] = 1
        w.box.mails[unid(2)].folder = "($Trash)"
        code, out = w.scan("run", "--full")
        v.need(J_PARTIAL, code == 1 and w.last().get("outcome") == "partial", f"보기 하나가 진 판이 「다 못 봤다」로 안 섰다: {out[-200:]}")
        v.need(J_PARTIAL, w.events() == [], f"덜 본 판이 바뀜을 냈다: {[(e['kind'], e.get('unid')) for e in w.events()]}")
        v.need(J_PARTIAL, w.state().get("cursor") == cursor, "덜 본 판이 이음점을 옮겼다")
        _, now = w.read("now")
        v.need(J_PARTIAL, f"폴더 {F2} · 2통" in now and "확인 중" not in now, "덜 본 판이 지금 모습의 그 상자를 비웠다")
        _, status = w.read("status")
        v.need(J_PARTIAL, "다 못 봤다" in status and f"폴더 {F2}" in status, "읽는 명령이 덜 본 판과 그 자리를 안 냈다")
        del w.box.broken[folder_unid(F2).lower()]
        mark = len(w.jsonl("calls"))
        code, out = w.scan("run", "--full")
        listed = [c for c in w.jsonl("calls")[mark:] if c[0] == "list"]
        v.need(J_PARTIAL, listed and all("--folder" in c and c[c.index("--folder") + 1] == F2 for c in listed),
               f"다음 판이 다 본 상자를 다시 읽었다(이어 보지 않았다): {listed}")
        gone = kinds(w.events(), "gone")
        v.need(J_PARTIAL, set(gone) == {unid(2)}, f"맺은 판의 「사라짐」이 진짜로 지운 메일 하나가 아니다: {sorted(gone)}")
    finally:
        w.close()
    return v


class MovingBox(fake.FakeDomino):
    """한 판 안에서 옮겨지는 메일 — 폴더 F1 의 보기를 처음 물을 때, F2(나중에 읽는 상자)의 메일 하나를 받은편지함(이미 읽은 상자)으로 옮긴다."""
    arm: str = ""

    def answer(self, h):
        if self.arm and folder_unid(F1).lower() in h.path.lower() and "readviewentries" in h.path.lower():
            self.mails[self.arm].folder, self.arm = "", ""
        return super().answer(h)


def story_inrun(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    v = Verdicts()
    base = [mail(1, "그대로", 0), mail(2, "가 폴더 메일", 0, EXT, folder=F1), mail(3, "옮겨질 메일", 0, EXT, folder=F2),
            mail(4, "진짜로 지울 메일", 1)]
    w = World(scripts, hand, base, box_cls=MovingBox)
    try:
        w.scan("run")
        w.box.mails[unid(4)].folder = "($Trash)"
        w.box.arm = unid(3)
        w.scan("run", "--full")
        ev = w.events()
        v.need(J_INRUN, w.box.mails[unid(3)].folder == "", "대역이 그 판 안에서 메일을 안 옮겼다(판이 시험을 못 탔다)")
        v.need(J_INRUN, unid(4) in kinds(ev, "gone"), "양성 대조 — 진짜로 지운 받은편지함 메일이 「사라짐」으로 안 섰다")
        v.need(J_INRUN, unid(3) not in kinds(ev, "gone"), "한 판 안에서 옮겨진 메일이 「사라짐」으로 섰다")
        w.scan("run", "--full")
        ev = w.events()
        moved = kinds(ev, "moved")
        v.need(J_INRUN, moved.get(unid(3), {}).get("to") == ["inbox", ""] and moved[unid(3)].get("from") == ["folder", F2],
               f"다음 판이 그 메일을 옮겨짐(어디서 어디로)으로 안 갈랐다: {moved.get(unid(3))}")
        v.need(J_INRUN, unid(3) not in kinds(ev, "gone") and unid(3) not in kinds(ev, "back"), "거짓 「사라짐 → 다시 나타남」이 섰다")
    finally:
        w.close()
    return v


def story_session(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    v = Verdicts()
    w = World(scripts, hand, [mail(1, "그대로", 0)])
    try:
        w.scan("run")
        w.box.session = "login"
        asked = len(w.box.paths)
        code, out = w.scan("run")
        v.need(J_SESSION, code == 1 and w.last().get("outcome") == "session", f"세션이 끊긴 판이 멈춤으로 안 섰다: {out[-200:]}")
        v.need(J_SESSION, len(w.box.paths) > asked, "양성 대조 — 그 판이 메일함을 한 번도 안 물었다")
        _, status = w.read("status")
        v.need(J_SESSION, "사내 세션이 끊겼다" in status and "EP 로그인" in status, "읽는 명령이 세션이 끊긴 때와 다음 걸음을 안 냈다")
        asked, runs = len(w.box.paths), len(w.runs())
        code, out = w.scan("run")
        v.need(J_SESSION, code == 1 and len(w.box.paths) == asked, "세션이 끊긴 뒤 다음 주기가 메일함(SSO)을 또 두드렸다")
        v.need(J_SESSION, len(w.runs()) == runs, "기다리는 주기마다 판 기록을 쌓았다")
        w.box.session = "ok"
        later = time.time() + 5
        os.utime(w.cookies, (later, later))                     # 대화에서 EP 로그인을 해 세션 파일이 새로 쓰였다
        code, out = w.scan("run")
        v.need(J_SESSION, code == 0 and "session" not in w.state(), f"세션 파일이 새로 쓰인 뒤 다음 주기에 안 돌았다: {out[-200:]}")
    finally:
        w.close()
    return v


def story_lock(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    v = Verdicts()
    for name, age in ((J_BUSY, timedelta(seconds=30)), (J_STALE, timedelta(hours=2))):
        w = World(scripts, hand, [mail(1, "그대로", 0)])
        try:
            w.folder().mkdir(parents=True, exist_ok=True)
            started = (datetime.now(timezone.utc) - age).isoformat(timespec="seconds")
            (w.folder() / "scan.lock").write_text(json.dumps({"token": "elsewhere", "started": started}), encoding="utf-8")
            code, out = w.scan("run")
            if name == J_BUSY:
                v.need(J_BUSY, code == 0 and "건너뛰었다" in out and w.box.paths == [], f"도는 판이 있는데 또 돌았다: {out[-200:]}")
                v.need(J_BUSY, [r.get("outcome") for r in w.runs()] == ["busy"] and not (w.folder() / "state.json").exists(),
                       "건너뛴 주기가 판 기록에 「건너뜀」으로 안 섰다")
            else:
                v.need(J_STALE, code == 0 and w.last().get("outcome") == "first" and "남은 잠금" in w.last().get("note", ""),
                       f"잠 · 꺼짐이 남긴 잠금이 다음 판을 막았다: {out[-200:]}")
                v.need(J_STALE, not (w.folder() / "scan.lock").exists(), "판이 끝난 뒤 잠금이 남았다")
        finally:
            w.close()
    return v


def story_shape(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    v = Verdicts()
    w = World(scripts, hand, [mail(1, "그대로", 0), mail(2, "둘째", 1)], wrap="drift")
    try:
        code, out = w.scan("run")
        v.need(J_SHAPE, code == 1 and w.last().get("outcome") == "shape", f"손의 끝 줄 꼴이 바뀌었는데 멈추지 않았다: {out[-200:]}")
        v.need(J_SHAPE, not w.state().get("mails") and not w.state().get("picture") and w.events() == [], "꼴을 모르는 글로 지금 모습을 적었다")
        v.need(J_SHAPE, "그대로" not in json.dumps(w.runs(), ensure_ascii=False), "멈춘 까닭에 메일의 글이 실렸다")
    finally:
        w.close()
    return v


@dataclasses.dataclass
class MinuteMail(FakeMail):
    """실물 손이 폴더 줄에 찍는 때의 꼴(분까지)을 내는 메일 — 곁의 가짜는 모든 상자에 초까지 찍어 폴더만의 꼴을 못 만든다.
    ``shape`` 가 ``other`` 면 둘 밖의 꼴(일/월/해)이다. 받은편지함 메일은 초까지 그대로다."""
    shape: str = "minute"

    def cols(self, columns) -> dict:
        cols = super().cols(columns)
        if self.folder and cols.get("xdate"):
            cols["xdate"] = (cols["xdate"][:16] if self.shape == "minute"
                             else datetime.strptime(self.stamp, "%Y%m%d%H%M%S").strftime("%d/%m/%Y %H:%M"))
        return cols


def story_dates(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """폴더 줄의 때가 분까지인 꼴(실물에서 잰 꼴) — 풀려 쌓이고 「이 시각 뒤」 새 메일에 서며, 둘 밖의 꼴은 멈춘다."""
    v = Verdicts()
    base = [mail(1, "그대로", 0, kind=MinuteMail), mail(3, "가 폴더 바닥", 0, EXT, folder=F1, kind=MinuteMail)]
    w = World(scripts, hand, base, [], folders=(F1,))
    try:
        w.scan("run")
        now = datetime.now(KST)
        w.box.mails[unid(5)] = mail(5, "폴더로 간 새 메일", 0, EXT, folder=F1, when=now - timedelta(minutes=3), kind=MinuteMail)
        w.box.mails[unid(6)] = mail(6, "받은편지함 새 메일", 0, PEER, when=now - timedelta(seconds=20), kind=MinuteMail)
        code, out = w.scan("run")
        got = (w.state().get("mails") or {}).get(unid(5)) or {}
        v.need(J_MINUTE, code == 0 and re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", got.get("date") or "") is not None,
               f"분까지인 폴더 메일의 때가 안 풀려 date 가 비었다: {got.get('date')!r} · {out[-200:]}")
        v.need(J_MINUTE, not [u for u, m in (w.state().get("mails") or {}).items() if m["box"] == "folder" and not m["date"]],
               "때를 찍은 폴더 메일에 date 가 빈 것이 있다")
        _, shown = w.read("new", "--since", (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M"))
        v.need(J_MINUTE, unid(5) in shown and unid(6) in shown, f"「이 시각 뒤 새 메일」에 폴더 메일이 안 섰다: {shown[-300:]}")
        cursor = (w.state().get("cursor") or {}).get("date") or ""
        v.need(J_MINUTE, cursor == ((w.state().get("mails") or {}).get(unid(6)) or {}).get("date"),
               f"이음점이 가장 늦은 메일(받은편지함 초까지 · 폴더 분까지가 섞인 가운데)의 때가 아니다: {cursor!r}")
    finally:
        w.close()
    w = World(scripts, hand, [mail(1, "그대로", 0, kind=MinuteMail, shape="other"),
                              mail(3, "폴더 메일", 0, EXT, folder=F1, kind=MinuteMail, shape="other")], [], folders=(F1,))
    try:
        code, out = w.scan("run")
        v.need(J_THIRD, code == 1 and w.last().get("outcome") == "shape", f"둘 밖의 때 꼴인데 멈추지 않았다: {out[-200:]}")
        v.need(J_THIRD, not w.state().get("mails"), "둘 밖의 때 꼴을 안 채로 메일을 쌓았다")
    finally:
        w.close()
    return v


F3 = "다 빈 폴더"


def story_signals(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """메일함 전체를 본 판 셋에 받은편지함이 자라고 규칙이 F1 을 채운다 — 하루쯤 전 · 이레쯤 전은 그때나 그 앞의 가장 늦은 판이다.
    판 기록의 때만 뒤로 민다 — 셈은 스캔이 그 판에 실은 그대로다."""
    v = Verdicts()
    base = [mail(1, "읽을 메일", 0), mail(2, "읽은 메일", 1, unread=False), mail(3, "안 읽은 메일", 2),
            mail(4, "규칙 폴더 안 읽음", 0, EXT, folder=F1), mail(5, "규칙 폴더 읽음", 1, EXT, folder=F1, unread=False),
            mail(6, "10월 폴더 메일", 0, EXT, folder=F2, unread=False)]
    w = World(scripts, hand, base, [], folders=(F3,))
    try:
        code, out = w.read("signals")
        v.need(J_SIGNALS, code == 3 and "스캔 파일이 없다" in out, f"스캔 파일이 없는데 종료 3 이 아니다: {code} · {out[-200:]}")
        preview = w.real("preview-rule", "--folder", F1, "--subject", "[주간]")
        found = re.search(r"확인 열쇠: ([0-9a-f]+)", preview)
        w.real("apply-rule", "--folder", F1, "--subject", "[주간]", "--confirm", found.group(1) if found else "-")
        v.need(J_SIGNALS, f"폴더로 옮김 → {F1}" in w.real("rules"), "양성 대조 — 가짜 메일함에 F1 로 옮기는 규칙이 안 섰다(판이 시험을 못 탔다)")
        w.scan("run")
        _, early = w.read("signals")
        v.need(J_SIGNALS, early.count("판 기록이 거기까지 안 닿는다") == 2, f"첫 판뿐인데 흐름이 하루 · 이레 전까지 닿는다고 했다: {early[-600:]}")

        def push_back(hours: float) -> None:
            path = w.folder() / "runs.jsonl"
            rows = w.runs()
            for r in rows:
                if r.get("pushed") is None:
                    r["started"] = (datetime.fromisoformat(r["started"]) - timedelta(hours=hours)).isoformat(timespec="seconds")
                    r["pushed"] = hours
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        push_back(8 * 24)
        now = datetime.now(KST)
        w.box.mails[unid(1)].unread = False
        w.box.mails[unid(7)] = mail(7, "새 메일 하나", 0, LATER, when=now - timedelta(minutes=9))
        w.box.mails[unid(8)] = mail(8, "새 메일 둘", 0, LATER, when=now - timedelta(minutes=8))
        w.box.mails[unid(9)] = mail(9, "[주간] 규칙 폴더 새 메일", 0, EXT, folder=F1, when=now - timedelta(minutes=7))
        w.scan("run", "--full")
        push_back(25)
        w.box.mails[unid(10)] = mail(10, "새 메일 셋", 0, LATER, when=now - timedelta(minutes=6))
        code, out = w.scan("run", "--full")
        v.need(J_SIGNALS, code == 0 and [r.get("mode") for r in w.runs()] == ["full"] * 3, f"전체를 본 판이 셋이 아니다: {w.runs()} · {out[-200:]}")
        code, got = w.read("signals")
        lines = got.splitlines()

        def line(word: str) -> str:
            return next((x for x in lines if word in x), "")
        v.need(J_SIGNALS, code == 0 and "받은편지함 지금 — 6통(안 읽음 4)" in got, f"받은편지함의 지금이 6통(안 읽음 4)이 아니다: {line('받은편지함 지금')}")
        v.need(J_SIGNALS, "6통(안 읽음 4)" in line("가장 늦은 판"), f"가장 늦은 판의 셈이 틀렸다: {line('가장 늦은 판')}")
        v.need(J_SIGNALS, "5통(안 읽음 3)" in line("1일쯤 전"), f"하루쯤 전이 25시간 전 판(5통 · 안 읽음 3)이 아니다: {line('1일쯤 전')}")
        v.need(J_SIGNALS, "3통(안 읽음 2)" in line("7일쯤 전"), f"이레쯤 전이 8일 전 판(3통 · 안 읽음 2)이 아니다: {line('7일쯤 전')}")
        v.need(J_SIGNALS, "판 3번" in line("기록이 닿는 데") and "8일" in line("기록이 닿는 데"), f"기록이 닿는 데가 8일 · 판 셋이 아니다: {line('기록이 닿는 데')}")
        v.need(J_SIGNALS, "폴더로 옮기는 규칙 1개" in got and f"폴더 {F1} · 3통(안 읽음 2)" in got and "규칙 1개" in line(f"폴더 {F1} · 3통"),
               f"규칙이 채우는 폴더 F1 이 3통(안 읽음 2) · 규칙 1개로 안 섰다: {line('규칙이 채우는')} · {line(f'폴더 {F1} ·')}")
        v.need(J_SIGNALS, not any(f"폴더 {F2}" in x and "규칙" in x for x in lines), "규칙이 안 채우는 F2 가 규칙 폴더로 섰다")
        order = [next((i for i, x in enumerate(lines) if f"폴더 {f} · " in x and ("가장 새 메일" in x or "메일 없음" in x)), -1) for f in (F3, F2, F1)]
        v.need(J_SIGNALS, -1 not in order and order == sorted(order), f"폴더마다 가장 새 메일이 빈 폴더 · 옛것부터가 아니다: {order}")
        v.need(J_SIGNALS, "메일 없음" in lines[order[0]] and "가장 새 메일 2026-10-01" in lines[order[1]]
               and f"가장 새 메일 {(now - timedelta(minutes=7)).strftime('%Y-%m-%d')}" in lines[order[2]],
               f"폴더마다 가장 새 메일의 때가 틀렸다: {[lines[i] for i in order if i >= 0]}")
        inside = got[got.find("<<<메일함 글 시작>>>"):got.find("<<<메일함 글 끝>>>")]
        v.need(J_SIGNALS, "마지막으로 다 본 때" in got and F1 in inside and F1 not in got.replace(inside, ""),
               "신호가 다 본 때를 안 내거나 폴더 · 규칙의 글을 자료 구역 밖에 냈다")
    finally:
        w.close()
    return v


def check_task(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """예약 — 걸지 않고(`--dry-run`) 작업의 정의를 받아 한 번에 하나 · 준 주기 · 손을 굳힌 명령줄인지 본다. 끄기 · 보기도 묻기만 한다."""
    v = Verdicts()
    env = {**os.environ, "MAIL_SECRETARY_HOME": tempfile.mkdtemp(prefix="scan-task-")}
    try:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(scripts / "scan.py"), "register", "--every", "7", "--full-every", "45",
                               "--hand", str(hand), "--dry-run"], env=env, capture_output=True, timeout=TIMEOUT_S)
        out = done.stdout.decode("utf-8", "replace")
        xml = out[out.find("<?xml"):]
        v.need(J_TASK, done.returncode == 0 and "<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>" in xml,
               "작업이 앞 판이 도는 동안 새 판을 안 띄우는 정의(IgnoreNew)가 아니다")
        v.need(J_TASK, "<Interval>PT7M</Interval>" in xml, "작업의 주기가 준 7분이 아니다")
        v.need(J_TASK, f'run --hand &quot;{hand}&quot; --full-every 45' in xml or f'run --hand "{hand}" --full-every 45' in xml,
               "작업의 명령줄에 손의 자리 · 전체 주기가 굳지 않았다")
        v.need(J_TASK, "<LogonType>InteractiveToken</LogonType>" in xml, "작업이 로그온한 사람의 세션에서만 도는 정의가 아니다")
        for verb, word in (("status", "/Query"), ("unregister", "/Delete")):
            got = subprocess.run([sys.executable, "-X", "utf8", "-I", str(scripts / "scan.py"), verb, "--dry-run"], env=env, capture_output=True,
                                 timeout=60)
            text = got.stdout.decode("utf-8", "replace")
            v.need(J_TASK, got.returncode == 0 and word in text and "mailbox-scan" in text, f"{verb} --dry-run 이 할 일을 안 보였다")
    finally:
        shutil.rmtree(env["MAIL_SECRETARY_HOME"], ignore_errors=True)
    return v


def check_defaults(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """기본 주기 — 주기를 안 준 정의가 사용자가 정한 값을 들고, 전체 주기가 잇는 기한에 닿으면 인자 오류(종료 2) · 그 바로 아래는 받는다."""
    v = Verdicts()
    env = {**os.environ, "MAIL_SECRETARY_HOME": tempfile.mkdtemp(prefix="scan-defaults-")}

    def scan(*args) -> tuple[int, str]:
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(scripts / "scan.py"), *args], env=env, capture_output=True,
                              timeout=TIMEOUT_S)
        return done.returncode, done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")
    try:
        code, out = scan("register", "--hand", str(hand), "--dry-run")
        xml = out[out.find("<?xml"):]
        v.need(J_DEFAULTS, code == 0 and f"<Interval>PT{DEFAULT_EVERY}M</Interval>" in xml,
               f"주기를 안 준 정의의 주기가 {DEFAULT_EVERY}분이 아니다: {re.findall(r'<Interval>[^<]*</Interval>', xml)}")
        v.need(J_DEFAULTS, f"--full-every {DEFAULT_FULL_EVERY}" in xml,
               f"주기를 안 준 정의의 전체 주기가 {DEFAULT_FULL_EVERY}분이 아니다: {re.findall(r'--full-every \d+', xml)}")
        # 일일 보고의 첫 확인(daily-brief 의 first-setup.md)이 이 줄의 수로 두 주기를 말씀드린다 — XML 을 안 읽어도 서야 한다
        v.need(J_DEFAULTS, f"새 메일을 {DEFAULT_EVERY}분마다 · 메일함 전체를 {DEFAULT_FULL_EVERY}분마다" in out[:out.find("<?xml")],
               f"걸기 전 보이기가 두 주기를 사람 말로 안 댄다: {out[:300]}")
        for args in (("register", "--hand", str(hand), "--full-every", str(PENDING_LIMIT), "--dry-run"),
                     ("run", "--full-every", str(PENDING_LIMIT))):
            code, out = scan(*args)
            v.need(J_DEFAULTS, code == 2 and "--full-every" in out, f"{args[0]} 가 잇는 기한에 닿는 전체 주기를 안 막았다: {code} · {out[-200:]}")
        code, out = scan("register", "--hand", str(hand), "--full-every", str(PENDING_LIMIT - 1), "--dry-run")
        v.need(J_DEFAULTS, code == 0 and f"--full-every {PENDING_LIMIT - 1}" in out, f"잇는 기한 바로 아래 전체 주기를 막았다: {out[-200:]}")
    finally:
        shutil.rmtree(env["MAIL_SECRETARY_HOME"], ignore_errors=True)
    return v


# import 말고 코드를 싣는 길 — 경로로 모듈 싣기 · 남의 스크립트 돌리기 · 이름으로 싣기. 찾는 자리를 넓히는 줄은 제 폴더를 넣을 때만 된다
LOADERS = ("spec_from_file_location", "SourceFileLoader", "runpy", "import_module", "__import__(")
OWN_DIR = "Path(__file__).resolve().parent)"


def check_alone(scripts: pathlib.Path) -> Verdicts:
    """홀로 선다 — 스크립트가 표준 라이브러리와 제 폴더의 모듈만 싣는다. 검사(`check_*.py`)는 훑지 않는다 — 가짜를 경로로 싣고 금줄 낱말을 든다."""
    v = Verdicts()
    files = sorted(f for f in scripts.glob("*.py") if not f.name.startswith("check_"))
    own = {p.stem for p in files}
    v.need(J_ALONE, bool(files), f"스크립트가 없다: {scripts}")
    for f in files:
        text = f.read_text(encoding="utf-8")
        for word in LOADERS:
            v.need(J_ALONE, word not in text, f"{f.name} 이 {word} 로 코드를 싣는다")
        for i, line in enumerate(text.splitlines(), 1):
            v.need(J_ALONE, not (("sys.path.insert" in line or "sys.path.append" in line) and OWN_DIR not in line),
                   f"{f.name}:{i} 이 제 폴더 밖을 찾는 자리에 넣는다: {line.strip()}")
        for node in ast.walk(ast.parse(text)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]] if node.level == 0 else ["(상대)"]
            for n in names:
                v.need(J_ALONE, n in sys.stdlib_module_names or n in own, f"{f.name}:{node.lineno} 이 {n} 을 싣는다")
    return v


# ── 아침 보고 — 스캔 판이 정한 때 뒤에 일일 보고를 사람 없이 한 번 띄운다 ─────────────────────────

J_BRIEF_A, J_BRIEF_B = "아침 보고 — 세션이 없으면 세 번 살펴보고 그날은 그만둔다", "아침 보고 — 세션을 찾은 살펴보기는 한 번 띄우고 그친다"
J_BRIEF_C, J_BRIEF_D = "아침 보고 — 살펴보기는 5분 넘게 띄운다(작업이 더 자주 깨워도)", "아침 보고 — 날이 바뀌면 다시 센다"
J_BRIEF_WHEN = "아침 보고 — 때 전 · 그날 보고 글이 선 뒤 · 띄운 보고가 도는 동안은 안 띄운다"
J_BRIEF_OPEN = "아침 보고 — 띄운 claude 는 읽는 명령만 연다(로그인 · 문서함 · 바꾸기 · 내보내기 없음)"
J_BRIEF_SET = "아침 보고 — claude 가 없으면 안 걸고 그렇다고 말한다"
J_BRIEF_WORK = "아침 보고 — 업무 파일은 업무 파악의 쓰는 손으로만 쓰고(파일 도구 없음), 업무 파악부터 한다"
GAP_MIN, TRIES_MOST = 5, 3                      # 사용자가 정한 수 — 하루 세 번 · 5분 넘게 띄어
# 사람 없는 보고에 여는 명령의 표(계약) — 원본은 손 mail.py 머리말 「어떻게 부르나」의 읽기와 업무 파악이 읽는 보기(폴더 · 규칙 · 세는
# 보기 · 주소록)다
OPEN_MAIL = ("session *", "folders *", "rules *", "list *", "read *", "read-many *", "summary *", "search *", "people *")
OPEN_CALENDAR = ("show *", "calendars *")
BRIEF_TOOLS = {"Bash", "Read", "Glob", "Grep"}  # 쓰기 · 고치기 · 웹 · 스킬 · 하위 에이전트 · PowerShell 이 없는 도구 묶음 — 업무 파일은 쓰는 손으로만
# 업무 파악 스킬 · 그 쓰는 손(work.md 의 주인은 그 스킬 하나 · 그 손이 앞 판의 절이 빠진 글을 안 쓴다)
WORK_SKILL, WORK_WRITER = "mailbox-work", ("scripts", "work.py")


def hand_mutating(script: pathlib.Path) -> tuple[str, ...]:
    """손이 「메일함 · 일정을 바꾸거나 밖으로 내보낸다」고 든 명령 — 그 손의 `MUTATING` 을 소스에서 읽는다(원본은 손이다)."""
    for node in ast.walk(ast.parse(script.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "MUTATING" for t in node.targets):
            return tuple(ast.literal_eval(node.value))
    raise Unmeasured(f"[못 잼] {script} 에 MUTATING 이 없다")


def made_brief(w: World) -> None:
    """그날 보고 글을 진짜 보고 창 손으로 남긴다 — 사용자 폴더에 대화가 지은 보고가 이미 선 판."""
    if not WINDOW.is_file():
        raise Unmeasured(f"[못 잼] 곁의 일일 보고 스킬의 보고 창 손이 없다: {WINDOW}")
    w.home.mkdir(parents=True, exist_ok=True)
    done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(WINDOW), "--dir", str(w.home), "--no-open"], env=w.env,
                          input="# 시험 보고\n\n## 이 보고가 본 데\n시험\n".encode("utf-8"), capture_output=True, timeout=TIMEOUT_S)
    if done.returncode != 0:
        raise Unmeasured(f"[못 잼] 보고 창 손이 보고 글을 못 남겼다: {done.stdout.decode('utf-8', 'replace')[-200:]}")


def seoul_clock() -> bool:
    """이 PC 시계가 서울인가 — 보고 창 손은 PC 시계로 보고 글의 이름을 짓고, 스캔은 서울 날짜로 그날 글을 찾는다(회사 PC 는 서울이다)."""
    return datetime.now().astimezone().utcoffset() == timedelta(hours=9)


def at_minute_start() -> None:
    """분이 바뀌기 직전이면 다음 분까지 기다린다 — 분으로 재는 틈의 판정이 판 사이에 분을 넘어 갈리지 않게."""
    second = datetime.now().second
    if second > 45:
        time.sleep(61 - second)


def st_hhmm(when: str) -> str:
    return datetime.fromisoformat(when).astimezone(KST).strftime("%H:%M")


def story_brief_tries(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """세션이 없는 아침 — 첫 살펴보기는 그 판의 답(세션 없음)을 쓰고, 기다리는 주기에는 손의 session 을 한 번씩, 세 번째 뒤로는 안 본다."""
    v = Verdicts()
    w = World(scripts, hand, [mail(1, "그대로", 0)], wrap="log")
    try:
        w.scan("run")
        w.set_brief("00:00")
        w.box.session = "login"
        w.scan("run")
        day = w.day()
        v.need(J_BRIEF_A, [t.get("session") for t in day.get("tries") or []] == ["lost"] and not day.get("launched"),
               f"세션이 끊긴 판이 첫 살펴보기(세션 없음)로 안 적혔다: {day}")
        v.need(J_BRIEF_A, w.hand_calls("session") == 0, "그 판이 이미 세션 없음을 받았는데 손의 session 을 또 불렀다")
        for n in (2, 3):
            w.rewind(GAP_MIN + 1)
            _, out = w.scan("run")
            v.need(J_BRIEF_A, len(w.day().get("tries") or []) == n and w.hand_calls("session") == n - 1,
                   f"기다리는 주기의 {n}번째 살펴보기가 손의 session 한 번으로 안 섰다: {w.day()} · {out[-200:]}")
        w.rewind(GAP_MIN + 1)
        before = w.hand_calls("session")
        w.scan("run")
        v.need(J_BRIEF_A, len(w.day().get("tries") or []) == TRIES_MOST and w.hand_calls("session") == before,
               f"세 번 다 세션이 없었는데 네 번째로 살펴봤다: {w.day()}")
        v.need(J_BRIEF_A, w.launches() == [], "세션이 없는데 보고를 띄웠다")
        _, status = w.scan("status", "--dry-run")
        times = [st_hhmm(t["at"]) for t in w.day().get("tries") or []]
        v.need(J_BRIEF_A, "건너뛰었다" in status and all(t in status for t in times) and "EP 로그인" in status,
               f"status 가 오늘 보고를 세 번 살펴본 때와 함께 건너뛰었다고 · 다음 걸음을 안 말한다: {status[-400:]}")
    finally:
        w.close()
    return v


def story_brief_launch(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """세션이 있는 아침 — 첫 판이 띄우고, 띄운 보고가 글을 못 남겨도 그날은 다시 안 띄운다. status 가 띄웠다 · 글이 안 섰다 · 섰다를 말한다."""
    v = Verdicts()
    w = World(scripts, hand, [mail(1, "그대로", 0)], wrap="log")
    try:
        w.set_brief("00:00")
        code, out = w.scan("run")
        got = w.launches(1)
        day = w.day()
        v.need(J_BRIEF_B, len(got) == 1 and (day.get("launched") or {}).get("pid") and
               [t.get("session") for t in day.get("tries") or []] == ["live"], f"세션이 있는 판이 보고를 한 번 띄우지 않았다: {day} · {out[-300:]}")
        v.need(J_BRIEF_B, w.hand_calls("session") == 0, "그 판이 메일함까지 닿았는데 손의 session 을 또 불렀다")
        _, status = w.scan("status", "--dry-run")
        v.need(J_BRIEF_B, "띄웠다" in status, f"status 가 오늘 띄운 것을 안 말한다: {status[-300:]}")
        (w.folder() / "brief.lock").unlink(missing_ok=True)     # 띄운 보고가 글을 못 남기고 끝났다(잠금이 풀린 뒤)
        w.rewind(GAP_MIN + 1)
        w.scan("run")
        v.need(J_BRIEF_B, len(w.launches()) == 1 and len(w.day().get("tries") or []) == 1,
               f"그날 한 번 띄운 뒤 또 살펴보거나 띄웠다: {w.day()} · 띄움 {len(w.launches())}")
        _, status = w.scan("status", "--dry-run")
        v.need(J_BRIEF_B, "안 섰다" in status, f"status 가 띄웠는데 보고 글이 안 선 것을 안 말한다: {status[-300:]}")
        if seoul_clock():
            made_brief(w)
            _, status = w.scan("status", "--dry-run")
            v.need(J_BRIEF_B, "보고 글이 섰다" in status, f"status 가 오늘 보고 글이 선 것을 안 말한다: {status[-300:]}")
    finally:
        w.close()
    return v


def story_brief_open(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """띄운 것 — 진짜 손 곁에서 띄워 대역이 받은 명령줄 · 자리 · 부탁 글 · 권한을 읽는 명령의 표와 손이 든 바꾸는 명령에 댄다."""
    v = Verdicts()
    w = World(scripts, hand, [mail(1, "그대로", 0)])
    w.env["CLAUDECODE"] = "1"                   # 대화 안에서 부른 판(run --now)과 같은 자리 — 띄운 claude 에는 안 가야 한다
    try:
        w.set_brief("00:00")
        w.scan("run")
        got = w.launches(1)
        one = got[0] if got else {"argv": [], "cwd": "", "stdin": "", "nested": ["(못 띄움)"]}
        argv = one["argv"]

        def flag(name: str) -> str:
            return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else ""
        v.need(J_BRIEF_OPEN, "-p" in argv and flag("--permission-mode") == "dontAsk", f"사람 없는 실행이 dontAsk 권한 방식이 아니다: {argv}")
        v.need(J_BRIEF_OPEN, set(flag("--tools").split(",")) == BRIEF_TOOLS, f"기본 도구가 읽기 · Bash 넷이 아니다: {flag('--tools')!r}")
        v.need(J_BRIEF_OPEN, "--strict-mcp-config" in argv and not any("dangerously" in a or "bypassPermissions" in a for a in argv),
               f"MCP 를 걷지 않았거나 권한을 건너뛰는 인자가 있다: {argv}")
        v.need(J_BRIEF_OPEN, pathlib.Path(one["cwd"]).resolve() == w.home.resolve() and one["nested"] == [],
               f"사용자 폴더에서 안 떴거나 겹친 세션 변수가 따라갔다: {one['cwd']} · {one['nested']}")
        brief_skill = scripts.parents[1] / "daily-brief"        # 스캔 스킬 곁의 일일 보고 스킬
        v.need(J_BRIEF_OPEN, (brief_skill / "SKILL.md").as_posix() in one["stdin"] and "사람 없는 예약 실행" in one["stdin"],
               "부탁 글이 일일 보고 스킬의 글과 그 사람 없는 실행 절을 가리키지 않는다")
        try:
            perms = json.loads(pathlib.Path(flag("--settings")).read_text(encoding="utf-8"))["permissions"]
        except (OSError, ValueError, KeyError):
            perms = {"allow": ["(못 읽음)"], "deny": []}
        home = w.home.as_posix()
        calendar = hand.parents[2] / "company-calendar" / "scripts" / "company_calendar.py"

        def runs(script: pathlib.Path) -> str:
            return f'python -X utf8 -I "{script.as_posix()}"'
        expect = [f"Bash({runs(hand)} {r})" for r in OPEN_MAIL]
        expect += [f"Bash({runs(calendar)} {r})" for r in OPEN_CALENDAR] if calendar.is_file() else []
        work_skill = scripts.parents[1] / WORK_SKILL                # 스캔 스킬 곁의 업무 파악 스킬
        writer = f"Bash({runs(work_skill / pathlib.Path(*WORK_WRITER))} *)"
        expect += [f"Bash({runs(scripts / 'reader.py')} *)", f'Bash({runs(brief_skill / "scripts" / "window.py")} --no-open --dir "{home}" *)',
                   writer]
        allow = perms.get("allow") or []
        bash_allow = [a for a in allow if a.startswith("Bash(")]
        v.need(J_BRIEF_OPEN, sorted(bash_allow) == sorted(expect),
               f"열린 명령이 읽는 명령의 표와 다르다: 더 연 것 {sorted(set(bash_allow) - set(expect))} · 빠진 것 {sorted(set(expect) - set(bash_allow))}")
        names = [r.split(" ")[0] for r in OPEN_MAIL]
        v.need(J_BRIEF_OPEN, not set(names) & set(hand_mutating(hand)), "열린 메일 명령 가운데 손이 「메일함을 바꾼다」고 든 명령이 있다")
        unknown = [n for n in names if subprocess.run([sys.executable, "-X", "utf8", "-I", str(hand), n, "--help"], capture_output=True,
                                                     env=w.env, timeout=60).returncode != 0]
        v.need(J_BRIEF_OPEN, not unknown, f"열린 메일 명령 가운데 손에 없는 명령이 있다(손이 --help 를 거절했다): {unknown}")
        deny_all = perms.get("deny") or []
        deny = [d[5:-1] for d in deny_all if d.startswith("Bash(") and d.endswith(")")]
        blocked = [f'{runs(hand)} {m} 0123' for m in hand_mutating(hand)]
        blocked += [f'{runs(calendar)} {m} 1' for m in hand_mutating(calendar)] if calendar.is_file() else []
        root = hand.parents[2]
        # 막은 목록의 갈래마다 표본 하나 — 하나라도 안 걸리면 막은 목록이 줄었다. `read --images` 는 열린 `read` 의 꼴에 맞고도 막혀야 한다
        blocked += [f"{runs(hand)} preview-move 0123 --to x", f"{runs(hand)} attachment 0123 --save all",
                    f"{runs(hand)} read 0123 --images",
                    f"{runs(hand)} recipients 0123 --to-file x", f"{runs(hand)} org 품질팀 --emails-file x",
                    f"{runs(calendar)} preview-add 1", f"{runs(calendar)} remember",
                    f'node "{(root / "ep-login" / "scripts" / "edge_session.js").as_posix()}"',
                    f'node "{(root / "ep-login" / "scripts" / "ep_login.js").as_posix()}"',
                    f'python -X utf8 -I "{(root / "ep-login" / "scripts" / "ep_session.py").as_posix()}"',
                    f'python -X utf8 -I "{(root / "company-ecm" / "scripts" / "ecm.py").as_posix()}" get 0123',
                    "gh issue create --title x", "git push", "curl http://example.com", "wget http://example.com", "node -e 1",
                    "npx x", "powershell -c 1", "pwsh -c 1", "cmd /c 1", "claude -p x", "schtasks /Delete /TN x"]
        loose = [c for c in blocked if not any(fnmatch.fnmatchcase(c, d) for d in deny)]
        v.need(J_BRIEF_OPEN, not loose, f"사용자 설정이 열어도 막혀야 할 명령이 막은 목록에 안 걸린다: {loose}")
        v.need(J_BRIEF_OPEN, any(fnmatch.fnmatchcase("mcp__github__issue_write", d) for d in deny_all if not d.startswith("Bash(")),
               "사용자 설정이 연 MCP 도구가 막은 목록에 안 걸린다")
        # 업무 파일을 쓰는 길은 업무 파악의 쓰는 손 하나다 — 파일 도구를 주면 모델이 그 손의 절 지킴을 건너뛴다
        tools = set(flag("--tools").split(","))
        v.need(J_BRIEF_WORK, not tools & {"Edit", "Write", "NotebookEdit"}, f"사람 없는 실행에 파일을 쓰는 도구가 있다: {flag('--tools')!r}")
        v.need(J_BRIEF_WORK, not [a for a in allow if not a.startswith("Bash(")], f"Bash 밖의 열린 권한이 있다: {allow}")
        v.need(J_BRIEF_WORK, writer in bash_allow, f"업무 파악의 쓰는 손이 열린 명령에 그 꼴로 없다: {writer}")
        stdin = one["stdin"]
        name = pathlib.Path(*WORK_WRITER).name
        at_work, at_brief = stdin.find(f"{work_skill.as_posix()}/SKILL.md"), stdin.find(f"{brief_skill.as_posix()}/SKILL.md")
        step = stdin[at_work:at_brief] if 0 <= at_work < at_brief else ""
        v.need(J_BRIEF_WORK, all(word in step for word in ("두 길", f"{name} where", "이어 파악", f"{name} write")),
               f"부탁 글이 업무 파악(두 길 · {name} where · 이어 파악 · {name} write)을 보고 짓기보다 먼저 시키지 않는다")
        dirs = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a == "--add-dir"]
        if work_skill.is_dir():
            v.need(J_BRIEF_WORK, str(work_skill) in dirs, f"업무 파악 스킬 폴더를 읽게 열지 않았다(--add-dir): {dirs}")
        elif scripts.resolve() == HERE:
            v.need(J_BRIEF_WORK, False, f"업무 파악 스킬이 스캔 스킬 곁에 없다 — 저장소 · 설치에서는 늘 곁에 선다: {work_skill}")
    finally:
        w.close()
    return v


def story_brief_gap(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """작업이 5분보다 자주 깨워도 — 잇단 판 · 4분 뒤 판은 안 살펴보고, 5분 뒤 판은 살펴본다."""
    v = Verdicts()
    w = World(scripts, hand, [mail(1, "그대로", 0)], wrap="log")
    try:
        w.scan("run")
        w.set_brief("00:00")
        w.box.session = "login"
        w.scan("run")
        w.scan("run")
        v.need(J_BRIEF_C, len(w.day().get("tries") or []) == 1 and w.hand_calls("session") == 0,
               f"잇단 판이 5분 안에 또 살펴봤다: {w.day()}")
        at_minute_start()

        def last_at(minutes_ago: int):
            def put(state):
                floor = datetime.now(timezone.utc).replace(second=0, microsecond=0)
                state["brief"]["tries"][-1]["at"] = (floor - timedelta(minutes=minutes_ago)).isoformat(timespec="seconds")
            return put
        w.edit_state(last_at(GAP_MIN - 1))
        w.scan("run")
        v.need(J_BRIEF_C, len(w.day().get("tries") or []) == 1, f"{GAP_MIN - 1}분 뒤 판이 살펴봤다: {w.day()}")
        w.edit_state(last_at(GAP_MIN))
        w.scan("run")
        v.need(J_BRIEF_C, len(w.day().get("tries") or []) == 2 and w.hand_calls("session") == 1,
               f"{GAP_MIN}분 뒤 판이 안 살펴봤다(양성 대조): {w.day()}")
    finally:
        w.close()
    return v


def story_brief_day(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """어제 세 번 다 세션이 없었던 날 뒤 — 오늘은 새로 세어 세션이 있으면 띄운다."""
    v = Verdicts()
    w = World(scripts, hand, [mail(1, "그대로", 0)], wrap="log")
    try:
        w.scan("run")
        w.set_brief("00:00")
        yesterday = datetime.now(KST) - timedelta(days=1)

        def put(state):
            state["brief"] = {"date": yesterday.strftime("%Y-%m-%d"), "launched": None,
                              "tries": [{"at": (yesterday - timedelta(minutes=10 * i)).isoformat(timespec="seconds"), "session": "lost"}
                                        for i in range(TRIES_MOST)]}
        w.edit_state(put)
        w.scan("run")
        day = w.day()
        v.need(J_BRIEF_D, day.get("date") == datetime.now(KST).strftime("%Y-%m-%d") and len(day.get("tries") or []) == 1
               and (day.get("launched") or {}).get("pid") and len(w.launches(1)) == 1, f"날이 바뀌었는데 새로 세어 띄우지 않았다: {day}")
    finally:
        w.close()
    return v


def story_brief_when(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """띄우지 않을 때 — 그날 보고 글이 이미 섰다 · 보고 시각 전 · 스캔이 띄운 보고가 도는데 지금 모습을 잃었다."""
    v = Verdicts()
    if not seoul_clock():
        unmeasured(J_BRIEF_WHEN, "이 PC 시계가 서울이 아니다 — 보고 창 손은 PC 시계로 이름을 짓고 스캔은 서울 날짜로 찾는다")
        return v
    w = World(scripts, hand, [mail(1, "그대로", 0)], wrap="log")
    try:
        made_brief(w)
        w.set_brief("00:00")
        w.scan("run")
        v.need(J_BRIEF_WHEN, not w.day().get("tries") and w.launches() == [], f"그날 보고 글이 섰는데 살펴보거나 띄웠다: {w.day()}")
    finally:
        w.close()
    w = World(scripts, hand, [mail(1, "그대로", 0)], wrap="log")
    try:
        if datetime.now(KST).strftime("%H:%M") < "23:58":
            w.set_brief("23:59")
            w.scan("run")
            v.need(J_BRIEF_WHEN, not w.day().get("tries") and w.launches() == [], f"보고 시각 전에 살펴봤다: {w.day()}")
        w.set_brief("00:00")
        w.scan("run")
        v.need(J_BRIEF_WHEN, len(w.launches(1)) == 1, "양성 대조 — 보고 시각 뒤 세션이 있는 판이 안 띄웠다")
        w.edit_state(lambda state: state.pop("brief", None))      # 지금 모습을 잃었다(깨져 다시 지었다)
        w.scan("run")
        v.need(J_BRIEF_WHEN, len(w.launches()) == 1, "스캔이 띄운 보고가 도는 중인데 지금 모습을 잃은 판이 또 띄웠다")
    finally:
        w.close()
    return v


def story_brief_set(scripts: pathlib.Path, hand: pathlib.Path) -> Verdicts:
    """claude 가 없는 PC — 걸기를 거절하고 아무것도 안 남긴다 · 걸어 둔 claude 가 사라지면 status 가 말한다."""
    v = Verdicts()
    w = World(scripts, hand, [mail(1, "그대로", 0)])
    try:
        missing = str(w.tmp / "no-such" / "claude.exe")
        for args in (("brief", "--at", "07:30", "--claude", missing),
                     ("register", "--brief-at", "07:30", "--claude", missing, "--hand", str(hand), "--dry-run")):
            code, out = w.scan(*args)
            v.need(J_BRIEF_SET, code == 1 and "못 찾았다" in out and not (w.folder() / "brief.json").exists(),
                   f"{args[0]} 가 claude 없이 보고를 걸었다: {code} · {out[-200:]}")
        w.set_brief("07:30")
        (w.tmp / ("claude.cmd" if sys.platform == "win32" else "claude")).unlink()
        _, status = w.scan("status", "--dry-run")
        v.need(J_BRIEF_SET, "07:30" in status and "claude 가 없다" in status, f"status 가 걸어 둔 claude 가 없다고 안 말한다: {status[-300:]}")
    finally:
        w.close()
    return v


# 판 — 혼자 잰 시간이 긴 판부터 선다. 일꾼 넷이 앞에서부터 집어 가, 긴 판이 끝에 서면 혼자 돌며 판 전체를 늘인다. 차례는 판정과 무관하다
STORIES = [story_brief_when, story_brief_launch, story_secretary, story_signals, story_inrun, story_partial, story_user, story_dates,
           story_brief_tries, story_brief_gap, story_new, story_brief_day, story_session, story_lock, story_brief_open, story_shape,
           story_brief_set]
NEEDS_NODE = {story_secretary: J_SECRETARY, story_session: J_SESSION, story_brief_tries: J_BRIEF_A, story_brief_gap: J_BRIEF_C,
              story_signals: J_SIGNALS}
ORDER = [J_FIRST, J_NEW, J_READS, J_SLICE, J_USER, J_SECRETARY, J_PARTIAL, J_INRUN, J_SESSION, J_BUSY, J_STALE, J_SHAPE, J_MINUTE, J_THIRD,
         J_TASK, J_DEFAULTS, J_ALONE, J_SIGNALS, J_BRIEF_A, J_BRIEF_B, J_BRIEF_C, J_BRIEF_D, J_BRIEF_WHEN, J_BRIEF_OPEN, J_BRIEF_WORK,
         J_BRIEF_SET]

# 물림 — (판정, 파일, 끌 줄, 바꿀 줄). 끄는 것은 그 판정이 지키는 한 줄이다
MUTATIONS = [
    (J_FIRST, "scan.py", 'state["mails"] = {u: {**m, "first_seen": None} for u, m in seen.items()}',
     'state["mails"], _made = D.compare({}, stamp, seen, read_at, stamp, last_look, state["gone"], journal)\n        events += _made'),
    (J_NEW, "scan.py", "    for unid, mail in got_mails.items():", "    for unid, mail in []:"),
    (J_READS, "scan.py", '        got = run.hand(["list", "--since", since, "--start", str(start)])',
     '        got = run.hand(["list", "--since", since, "--start", str(start)])\n        run.hand(["read", "0" * 32])'),
    (J_SLICE, "reader.py", "    picked = newest_first([m for m in s.mails.values() if fresh(m)])", "    picked = newest_first(list(s.mails.values()))"),
    (J_USER, "scan_diff.py", "        if place(old) != place(mail):", "        if False:"),
    (J_SECRETARY, "scan_diff.py", "        return cls(rows, held if isinstance(held, dict) else None)", "        return cls([], None)"),
    (J_PARTIAL, "scan.py", "    if short:\n        st.write_json", "    if False:\n        st.write_json"),
    (J_INRUN, "scan_diff.py", '        settled = old.get("missing_since") or box_key(*place(old)) == first_box', "        settled = True"),
    (J_SESSION, "scan.py", '    lost = state.get("session")\n    if not lost:', '    lost = state.get("session")\n    if True:'),
    (J_BUSY, "scan_store.py", "                if since is not None and (at - since).total_seconds() < LOCK_STALE_S:", "                if False:"),
    (J_STALE, "scan_store.py", "                if since is not None and (at - since).total_seconds() < LOCK_STALE_S:", "                if True:"),
    (J_SHAPE, "scan_hand.py", "    head = LIST_END.match(end)\n",
     "    head = LIST_END.match(end.replace('통을 냈다', '통을 보였다'))\n"),
    (J_MINUTE, "scan_hand.py", '(MAIL_DATE_MINUTE, ":00")', '(MAIL_DATE_MINUTE, "")'),
    (J_THIRD, "scan_hand.py", "    if date is None and date_text:\n        return None\n    mail =", "    mail ="),
    (J_TASK, "scan_task.py", "<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>",
     "<MultipleInstancesPolicy>Parallel</MultipleInstancesPolicy>"),
    (J_ALONE, "scan.py", "import scan_const as C  # noqa: E402", "import scan_const as C  # noqa: E402\nimport secretary  # noqa: E402,F401"),
    (J_BRIEF_A, "scan_brief.py", "    if len(tries) >= C.BRIEF_TRIES_MOST:\n        return \"gave-up\"", "    if False:\n        return \"gave-up\""),
    (J_BRIEF_B, "scan_brief.py", '    if day.get("launched"):\n        return "launched"', '    if False:\n        return "launched"'),
    (J_BRIEF_C, "scan_brief.py", "    if last is not None and minute(at) - minute(last) < C.BRIEF_TRY_GAP_MIN:",
     "    if last is not None and minute(at) - minute(last) < 0:"),
    (J_BRIEF_D, "scan_brief.py", '    if not isinstance(got, dict) or got.get("date") != seoul_date(at):', "    if not isinstance(got, dict):"),
    (J_BRIEF_WHEN, "scan_brief.py", '    if made_today(at):\n        return "made"', '    if False:\n        return "made"'),
    (J_BRIEF_OPEN, "scan_brief.py", '"--permission-mode", "dontAsk"', '"--permission-mode", "acceptEdits"'),
    (J_BRIEF_OPEN, "scan_const.py", '"Bash(schtasks*)", ', ""),
    (J_BRIEF_WORK, "scan_const.py", 'CLAUDE_TOOLS = "Bash,Read,Glob,Grep"', 'CLAUDE_TOOLS = "Bash,Read,Glob,Grep,Write"'),
    (J_BRIEF_WORK, "scan_brief.py", """, f"{run(p['work_writer'])} *"]""", "]"),
    (J_DEFAULTS, "scan_const.py", "\nEVERY_MIN = 15 ", "\nEVERY_MIN = 5 "),
    (J_SIGNALS, "reader.py", "before = [wc for wc in counts if wc[0] <= edge]", "before = counts"),
    (J_BRIEF_SET, "scan.py", "    if claude is None:\n        return None, None, NO_CLAUDE", "    if False:\n        return None, None, NO_CLAUDE"),
]
WHO = {J_FIRST: story_new, J_NEW: story_new, J_READS: story_new, J_SLICE: story_new, J_USER: story_user,
       J_SECRETARY: story_secretary, J_PARTIAL: story_partial, J_INRUN: story_inrun, J_SESSION: story_session, J_BUSY: story_lock,
       J_STALE: story_lock, J_SHAPE: story_shape, J_MINUTE: story_dates, J_THIRD: story_dates, J_BRIEF_A: story_brief_tries,
       J_BRIEF_B: story_brief_launch, J_BRIEF_C: story_brief_gap, J_BRIEF_D: story_brief_day, J_BRIEF_WHEN: story_brief_when,
       J_BRIEF_OPEN: story_brief_open, J_BRIEF_SET: story_brief_set, J_TASK: check_task, J_ALONE: check_alone,
       J_BRIEF_WORK: story_brief_open, J_DEFAULTS: check_defaults, J_SIGNALS: story_signals}


def judge_all(scripts: pathlib.Path, hand: pathlib.Path, only: set | None = None) -> dict[str, tuple[bool, list[str]]]:
    """판들을 넷씩 함께 돌려 판정을 모은다 — 판마다 제 가짜 메일함 · 제 사용자 폴더라 서로 안 닿는다."""
    node = shutil.which("node") is not None
    results: dict[str, tuple[bool, list[str]]] = {}
    lock = threading.Lock()

    def one(fn):
        try:
            got = fn(scripts) if fn is check_alone else fn(scripts, hand)
        except Exception:
            got = Verdicts()
            got.need(f"({fn.__name__})", False, traceback.format_exc(limit=3))
        with lock:
            results.update(got.got)
    jobs = [fn for fn in [*STORIES, check_task, check_defaults, check_alone] if (only is None or fn in only) and (node or fn not in NEEDS_NODE)]
    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(one, jobs))
    return results


def teeth(hand: pathlib.Path, skip: set = frozenset()) -> None:
    """물림 — 판정마다 그 줄을 끈 사본으로 그 판을 돌려 그 판정이 빨개지는지 본다. 사본은 스킬 뿌리와 같은 꼴(`<뿌리>/mailbox-scan/scripts`)로 선다."""
    def one(mutation):
        name, file, old, new = mutation
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="scan-teeth-"))
        try:
            copy = tmp / "mailbox-scan" / "scripts"
            shutil.copytree(SCRIPTS, copy, ignore=shutil.ignore_patterns("__pycache__"))
            text = (copy / file).read_text(encoding="utf-8")
            if text.count(old) != 1:
                return name, False, f"사본을 못 심었다 — {file} 에 끌 줄이 {text.count(old)}번 있다(물림을 다시 지을 일)", []
            (copy / file).write_text(text.replace(old, new), encoding="utf-8")
            got = judge_all(copy, hand, only={WHO[name]}).get(name)
            if got is None:
                return name, False, "그 판정이 안 섰다", []
            return name, not got[0], "" if not got[0] else "끈 사본에서도 초록이다", got[1][:2]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    with ThreadPoolExecutor(2) as pool:
        for name, bit, why, reasons in pool.map(one, [m for m in MUTATIONS if m[0] not in skip]):
            report(f"물림 — {name}", bit, [why] if why else [])
            for reason in reasons if bit else ():
                edge(f"끈 사본의 빨강: {reason.splitlines()[0][:160]}")     # 그 판정이 제 까닭으로 빨개졌나 — 사람이 읽는다


def main() -> int:
    if not (SCRIPTS / "scan.py").is_file() or not (SCRIPTS / "reader.py").is_file():
        raise Unmeasured(f"[못 잼] 스캔 스크립트가 없다: {SCRIPTS}")
    if not JOURNAL.is_file():
        raise Unmeasured(f"[못 잼] 곁의 메일함 정리 스킬의 기록(journal.py)이 없다: {JOURNAL}")
    hand = sibling_hand()
    print(f"잰다: {SCRIPTS} · 손 {hand}")
    began = time.monotonic()
    if TEETH:
        # 물림은 바탕이 초록인 판정에만 뜻이 있다 — 늘 지는 판정 앞에서는 끈 사본도 「잡혔다」로 센다
        base = judge_all(SCRIPTS, hand)
        red = {name for name, (ok, _) in base.items() if not ok} | {n for n in ORDER if n not in base}
        for name in sorted(red):
            unmeasured(f"물림 — {name}", "바탕(끄지 않은 스크립트)에서 그 판정이 초록이 아니다 — 계약 판정부터 고친다")
        teeth(hand, skip=red)
        total = len(MUTATIONS)
    else:
        results = judge_all(SCRIPTS, hand)
        if shutil.which("node") is None:
            for name in NEEDS_NODE.values():
                unmeasured(name, "node 가 없어 손이 세션 손 대역을 못 띄운다")
        for name in [*ORDER, *sorted(k for k in results if k not in ORDER)]:
            if name in results:
                ok, why = results[name]
                report(name, ok, why)
            elif name not in UNMEASURED:
                report(name, False, ["그 판정이 안 섰다 — 그 판이 도중에 죽었다(위의 「(판 이름)」 줄)"])
        total = len(set(ORDER) | set(results))
    took = round(time.monotonic() - began, 1)
    print(f"{'물림 ' if TEETH else ''}통과 {len(PASSES)}/{total}" + (f" · 못 잼 {len(UNMEASURED)}" if UNMEASURED else "") + f" · {took}초")
    if FAILS:
        return EXIT_MISMATCH
    if UNMEASURED or len(PASSES) < total:
        return EXIT_UNMEASURED
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("못 쟀다")
        sys.exit(EXIT_UNMEASURED)
