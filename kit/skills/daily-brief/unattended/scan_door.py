"""스캔 이음 — 형제 스킬 mailbox-scan 의 두 문(`scan.py status --json` · `scan.py run --now --wait`)을 부르고 그 답을 읽는 이 폴더의
유일한 자리. 사용자 폴더와 회사 메일 손의 자리도 여기서 정한다 — 사용자 폴더는 스캔이 내준 답에서, 손은 형제 폴더에서. 스캔의 코드는 싣지
않는다(명령으로만 부른다). 문의 칸과 뜻은 그 스킬의 설계 「status --json · run --wait」이 든다.

    home = home_of(args.dir)                    # `--dir` 이 있으면 그것, 없으면 스캔의 `status --json --dry-run` 의 `home` — 못 정하면 None
    hand, missing = mail_hand(args.hand)        # `--hand` · 없으면 형제 스킬 company-mail 의 mail.py — 없으면 (None, 까닭)
    got = status(dry_run=True)                  # `status --json` 한 장 — 못 부르거나 꼴을 모르면 None
    seen = answer_since(after)                  # 그 뒤에 시작한 스캔 판의 세션 답 — 없으면 None
    answer, missed = ask_round(hand, since)     # 「지금 한 판」을 청해 그 판의 세션 답 — 안 돌았으면 (None, 까닭)
"""

from __future__ import annotations

import json
import pathlib
import subprocess
from datetime import datetime, timedelta
from typing import Any

import clock as tm
import proc_base as P
import unattended_const as C
from brief_kinds import SCAN_LATE, SCAN_STOPPED, SCAN_UNREACHED

SCAN = C.SKILLS_ROOT / C.SCAN_SKILL / pathlib.Path(*C.SCAN_SCRIPT)
HAND = C.SKILLS_ROOT / C.HAND_SKILL / pathlib.Path(*C.HAND_SCRIPT)
DIR_HELP = "사용자 폴더 — 없으면 곁의 메일함 스캔(scan.py status --json)이 대는 자리"
NO_HOME = "사용자 폴더를 못 정했다 — --dir 로 주거나 곁의 메일함 스캔 스킬(mailbox-scan)을 깐다"
HAND_GIVEN_MISSING = "--hand 가 가리키는 회사 메일 손이 없다: {path}"
HAND_SIBLING_MISSING = "회사 메일 손(company-mail 의 scripts/mail.py)을 못 찾았다 — 본 자리: {path}"


def status(dry_run: bool = True) -> dict[str, Any] | None:
    """스캔의 `status --json` 한 장 — 못 부르거나 · 끝 줄이 JSON 사전이 아니거나 · 꼴 번호를 모르면 None. `dry_run` 이면 작업 스케줄러에 안 묻는다."""
    if not SCAN.is_file():
        return None
    try:
        done = P.run_python(SCAN, ["status", "--json", *(["--dry-run"] if dry_run else [])], C.SCAN_STATUS_TIMEOUT_S)
    except (subprocess.TimeoutExpired, OSError):
        return None
    lines = done.stdout.decode("utf-8", "replace").strip().splitlines()
    try:
        got = json.loads(lines[-1]) if lines else None
    except ValueError:
        return None
    return got if isinstance(got, dict) and got.get("format") in C.SCAN_STATUS_FORMATS else None


def home_of(given: str | None) -> pathlib.Path | None:
    """사용자 폴더 — 준 것(`--dir`)이 있으면 그것, 없으면 스캔이 대는 자리(사본을 안 든다). 못 정하면 None."""
    if given:
        return pathlib.Path(given).expanduser()
    got = (status(dry_run=True) or {}).get("home")
    return pathlib.Path(got) if isinstance(got, str) and got else None


def mail_hand(given: str | None) -> tuple[pathlib.Path | None, str]:
    """회사 메일 손의 자리 — 준 것(`--hand`)이 있으면 그것, 없으면 형제 스킬 company-mail 의 mail.py. 없으면 (None, 까닭)."""
    path = pathlib.Path(given.strip()).expanduser() if given and given.strip() else HAND
    if not path.is_file():
        return None, (HAND_GIVEN_MISSING if given and given.strip() else HAND_SIBLING_MISSING).format(path=path)
    return path.resolve(), ""


def run_now(hand: pathlib.Path) -> int | None:
    """스캔에 「지금 한 판」을 청한다 — 세션을 기다리던 주기도 건너뛰고 · 앞 판이 돌면 `SCAN_WAIT_S` 안에서 기다렸다. 판의 갈래(전체 · 새
    메일)는 스캔이 제 때로 고른다 — 전체 판이 찰 때 청한 판이 그것을 안 하면 그 분의 보고가 낡은 「메일함 전체를 마지막으로 다 본 때」로
    읽는다. 낸 글은 안 읽는다(돈 판은 `status` 로 읽는다). 내는 것 — 종료 값, 못 띄웠거나 시한을 넘겼으면 None."""
    if not SCAN.is_file():
        return None
    try:
        done = P.run_python(SCAN, ["run", "--now", "--wait", str(C.SCAN_WAIT_S), "--hand", str(hand)], C.SCAN_CALL_TIMEOUT_S)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return done.returncode


def started_since(got: dict[str, Any] | None, since: datetime) -> dict[str, Any] | None:
    """`status --json` 의 마지막 판이 `since`(초까지 — 판의 때는 초까지 적힌다) 뒤에 시작했으면 그 판의 칸, 아니면 None."""
    last = (got or {}).get("last_run") or {}
    started = tm.parse(last.get("started"))
    return last if started is not None and started >= since.replace(microsecond=0) else None


def answer_since(after: datetime) -> str | None:
    """`after` 뒤(같은 초는 안 든다)에 시작한 스캔 판이 손에서 받은 사내 세션의 답 — 그런 판이 없거나 답이 없으면 None."""
    last = started_since(status(dry_run=True), after + timedelta(seconds=1))
    return last.get("session") if last else None


def ask_round(hand: pathlib.Path, since: datetime) -> tuple[str | None, str]:
    """스캔에 「지금 한 판」을 청하고(`run_now`) 그 판의 세션 답을 읽는다 — (세션 답 · 판이 돌았는데 답이 없으면 None, "") 이나 판이 안 돌았으면
    (None, 까닭 — SCAN_UNREACHED 못 불렀다 · SCAN_LATE 앞 판이 시한 안에 안 끝나 건너뛰었다 · SCAN_STOPPED 판을 못 하고 멈췄다)."""
    code = run_now(hand)
    got = status(dry_run=True) if code is not None else None
    if got is None:
        return None, SCAN_UNREACHED
    last = started_since(got, since)
    if last is None:
        return None, SCAN_LATE if code == 0 else SCAN_STOPPED
    return last.get("session"), ""
