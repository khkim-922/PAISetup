"""회사 메일 손 이음 — 손(스킬 company-mail 의 `scripts/mail.py`)을 찾고 명령으로 부른다. 손의 코드는 싣지 않고 프로세스로 부른다.

출력은 UTF-8 로만 풀고 못 풀면 `ShapeError` 로 멈춘다. 받은 줄을 메일 머리로 푸는 것은 `hand_lines` 가 든다.

    hand = find_hand(explicit)               # --hand · MAILBOX_SCAN_HAND · SECRETARY_SKILLS · 도구 홈 차례 — 없으면 HandMissing
    has_since(hand) · has_serve(hand)        # 「list --since」 · 「serve」가 있는 판인가(`--help` 로 묻는다)
    got = call(hand, ["folders"])            # Called(code, lines, said) — 손의 종료 값 그대로. 한 번 띄워 한 번 묻는다
    served = Served(hand); served.ask(["folders"]) … served.close()   # 같은 Called — 손 하나를 띄워 두고 잇달아 묻는다(`serve`)

꼴의 원본 — 손 `mail.py` 의 `serve` 답 꼴(`SERVE_HELP`).
"""

from __future__ import annotations

import json
import os
import pathlib
import queue
import re
import subprocess
import threading
from dataclasses import dataclass

import proc_base as P
from hand_lines import ShapeError
from scan_const import HAND_ENV, HAND_SCRIPT, HAND_SKILL, HAND_TIMEOUT_S, SKILL_HOMES, SKILLS_ENV


class HandMissing(Exception):
    """회사 메일 손을 못 찾았다 — 글자가 어디를 봤는지 말한다."""


@dataclass
class Called:
    """손 한 번의 답 — 종료 값 · 표준 출력의 줄 · 0 이 아닐 때의 까닭 · 물은 명령."""
    code: int
    lines: list[str]
    said: str              # 0 이 아닐 때 손이 댄 까닭(끝 줄) — 메일함의 글(폴더 이름)이 들 수 있다
    command: str = ""


# ── 손 찾기 · 부르기 ────────────────────────────────────────────────────────────

def skill_roots() -> list[pathlib.Path]:
    """볼 스킬 뿌리 — `SECRETARY_SKILLS` 가 있으면 그것 하나, 없으면 도구 홈 셋."""
    given = os.environ.get(SKILLS_ENV, "").strip()
    if given:
        return [pathlib.Path(given).expanduser()]
    return [pathlib.Path.home().joinpath(*parts) for parts in SKILL_HOMES]


def find_hand(explicit: str | None = None) -> pathlib.Path:
    """손 `mail.py` 의 자리 — `--hand` → `MAILBOX_SCAN_HAND` → 스킬 뿌리들 차례. 어디에도 없으면 `HandMissing`."""
    for given, word in ((explicit, "--hand"), (os.environ.get(HAND_ENV, ""), HAND_ENV)):
        if given and given.strip():
            path = pathlib.Path(given.strip()).expanduser()
            if not path.is_file():
                raise HandMissing(f"{word} 가 가리키는 회사 메일 손이 없다: {path}")
            return path.resolve()
    tried = []
    for root in skill_roots():
        path = root / HAND_SKILL / pathlib.Path(*HAND_SCRIPT)
        tried.append(str(path))
        if path.is_file():
            return path.resolve()
    raise HandMissing("회사 메일 손(company-mail 의 scripts/mail.py)을 못 찾았다 — 본 자리: " + " · ".join(tried))


def _called(code: int, out: bytes, command: str) -> Called:
    """손의 종료 값 · 표준 출력 → `Called`. 출력을 UTF-8 로 못 풀면 `ShapeError`."""
    try:
        text = out.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ShapeError(f"{command} — 손의 출력을 UTF-8 로 못 풀었다({exc.start}째 바이트)") from exc
    lines = [x.rstrip("\r") for x in text.splitlines() if x.strip()]
    return Called(code, lines, lines[-1] if lines and code != 0 else "", command)


def _timed_out(timeout: float, command: str) -> Called:
    """시한을 넘긴 손의 답 — 손의 종료 1 과 같게, 까닭은 시한이다."""
    return Called(1, [], f"회사 메일 손이 {timeout:.0f}초 안에 안 끝났다", command)


def call(hand: pathlib.Path, args: list[str], timeout: float = HAND_TIMEOUT_S) -> Called:
    """손 한 번 — 종료 값 · 표준 출력의 줄 · 0 이 아닐 때의 까닭. 표준 오류(손의 경고)는 안 읽는다. 출력을 UTF-8 로 못 풀면 `ShapeError`.
    시한을 넘기면 손의 종료 1 과 같게 낸다(`said` 가 시한을 말한다)."""
    command = " ".join(a for a in args[:1])
    try:
        done = P.run_python(hand, args, timeout)
    except subprocess.TimeoutExpired:
        return _timed_out(timeout, command)
    return _called(done.returncode, done.stdout, command)


class Served:
    """손 하나(`mail.py serve`)를 판 내내 띄워 두고 명령을 하나씩 묻는다 — 명령마다 파이썬을 새로 안 띄운다. 한 번 묻기(`ask`)의 꼴과
    뜻은 `call` 과 같다(종료 값 · 줄 · 까닭 · 시한). 손이 답 없이 지거나 시한을 넘기면 그 손을 거두고 그 물음은 그 손의 종료 값으로
    지며, 다음 물음은 새 손이 받는다 — 한 상자의 고장이 뒤 상자를 못 읽게 하지 않는다. 답의 꼴은 손 `mail.py` 의 `SERVE_HELP` 다."""

    def __init__(self, hand: pathlib.Path):
        self.hand = hand
        self.proc: subprocess.Popen | None = None
        self.answers: queue.Queue = queue.Queue()
        self.asked = 0

    def _start(self) -> None:
        """손 하나를 `serve` 로 띄우고 그 답을 큐로 받는 일꾼을 세운다."""
        self.proc = subprocess.Popen(P.python_argv(self.hand, "serve"), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     env=P.utf8_env(), **P.quiet())
        self.answers = queue.Queue()
        threading.Thread(target=_read_answers, args=(self.proc.stdout, self.answers), daemon=True).start()

    def _drop(self) -> int:
        """손을 거둔다 — 그 손의 종료 값(거둬서 끝났으면 그 값)."""
        proc, self.proc = self.proc, None
        if proc is None:
            return 1
        if proc.poll() is None:
            proc.kill()
        try:
            return proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            return 1

    def ask(self, args: list[str], timeout: float = HAND_TIMEOUT_S) -> Called:
        """띄워 둔 손에 명령 하나를 묻는다 — 답의 꼴과 뜻은 `call` 과 같다."""
        command = " ".join(a for a in args[:1])
        self.asked += 1
        request = json.dumps({"id": self.asked, "argv": args}).encode("ascii") + b"\n"
        for last in (False, True):
            if self.proc is None or self.proc.poll() is not None:
                self._drop()
                self._start()
            try:
                self.proc.stdin.write(request)
                self.proc.stdin.flush()
                break
            except OSError:               # 손이 앞 답 뒤에 졌다 — 이 물음은 아직 안 받았으니 새 손에 한 번 더
                self._drop()
                if last:
                    return Called(1, [], "회사 메일 손을 띄웠는데 물음을 못 받았다", command)
        try:
            got = self.answers.get(timeout=timeout)
        except queue.Empty:
            self._drop()
            return _timed_out(timeout, command)
        if got is None:
            code = self._drop()
            return Called(code or 1, [], f"회사 메일 손이 답 없이 끝났다(종료 값 {code})", command)
        if isinstance(got, bytes):        # 손이 답의 꼴 밖에서 말하고 끝났다(싣다가 졌다) — 따로 부른 손의 실패처럼 그 글과 종료 값으로
            return _called(self._drop() or 1, got, command)
        head, body = got
        if head.get("id") != self.asked:
            self._drop()
            raise ShapeError(f"{command} — 손의 답이 물은 차례({self.asked})의 것이 아니다({head.get('id')!r})")
        return _called(head["code"], body, command)

    def close(self) -> None:
        """표준 입력을 닫아 손이 스스로 끝나게 한다 — 안 끝나면 거둔다."""
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            proc.stdin.close()
            proc.wait(timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait(timeout=30)


def _read_answers(out, answers: queue.Queue) -> None:
    """손의 답을 하나씩 큐에 넣는다 — (머리, 몸) · 답 머리가 아닌 줄이 오면 그 줄부터 끝까지의 바이트 · 끝(답이 다 오기 전의 끝 포함)이면
    None."""
    try:
        while True:
            line = out.readline()
            if not line:
                break
            try:
                head = json.loads(line)
                size = head["bytes"]
                if not isinstance(head.get("code"), int) or not isinstance(size, int) or size < 0:
                    raise ValueError
            except (ValueError, KeyError, TypeError):
                answers.put(line + out.read())
                return
            body = out.read(size)
            if len(body) != size:
                break
            answers.put((head, body))
    except (OSError, ValueError):
        pass
    answers.put(None)


def has_since(hand: pathlib.Path) -> bool:
    """「list --since」를 받는 판인가 — 손의 `list --help` 에 그 깃발이 서나로 묻는다(그 깃발이 없는 옛 판의 손이 깔린 PC 도 있다)."""
    got = call(hand, ["list", "--help"], timeout=60)
    return got.code == 0 and any(re.search(r"(?<![\w-])--since\b", x) for x in got.lines)


def has_serve(hand: pathlib.Path) -> bool:
    """명령 여럿을 한 프로세스로 받는 판인가(`serve`) — 없는 옛 판의 손이면 명령마다 `call` 로 부른다."""
    return call(hand, ["serve", "--help"], timeout=60).code == 0
