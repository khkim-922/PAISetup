"""사람 없는 실행 이음 — 같은 스킬의 `unattended/` 입구 명령(`handed.py start · show · list` · `clock.py away · window-times … --chosen-at`)의
인자를 짓고 그 끝 줄 · JSON 을 읽는 창 곁의 유일한 자리. 프로그램은 띄우지 않는다 — 부르는 쪽이 준 `run`(`presses.run_unattended` —
`run(인자, 시한) -> (종료 값, 표준 출력)` · 인자의 첫 칸이 입구의 이름) 하나로 부른다. 명령 · 입력 · 답의 계약은 `references/DESIGN.md`
「사람 없는 실행의 문」 표가 원본이다.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_const.py — `-I` 로 돌아도 싣는다
from brief_const import CLOCK_ENTRY, HANDED_ENTRY  # noqa: E402

START_TIMEOUT_S = 60                           # `handed start` 한 번의 시한 — 기록을 쓰고 지킴이를 떼어 띄운 뒤 곧 돌아온다
SHOW_TIMEOUT_S = 30                            # `handed show` · `list` 한 번의 시한 — 읽기만 한다
AWAY_TIMEOUT_S = 300                           # `clock.py away · window-times … --chosen-at` 한 번의 시한 — 켤 때 주소록 손이 세션을 받아 본인 주소를 묻는다(그 스킬의 주소록 시한보다 길게)
NO_RUNNER = "사람 없는 실행(unattended)을 못 불렀다"
TIMEOUT_SAID = "시한"                          # 시한을 넘긴 시계 명령의 까닭 — 창에 그대로 선다
# 부른 손(`run`)이 시한을 넘긴 부름의 종료 값 자리에 내는 값 — 끝났는지 모른다(넘겨졌을 수 있다). 「못 띄웠다」(None)와 다른 답이다
TIMED_OUT = "timeout"
# `handed start` 한 번의 끝 — 맡았다 · 실행을 못 띄웠다(아무것도 안 넘겼다) · 실행이 못 맡는다고 했다(기록을 안 썼다) · 모른다(시한 · 꼴이 아닌 답)
TOOK, NOT_LAUNCHED, REFUSED, UNKNOWN = "took", "not-launched", "refused", "unknown"
NO_END = "끝 줄이 없거나 종료 {code} 다"


def last_json(out: str) -> dict:
    """표준 출력의 마지막 줄의 JSON 사전 — 없거나 꼴이 아니면 빈 것."""
    lines = [x for x in (out or "").strip().splitlines() if x.strip()]
    try:
        got = json.loads(lines[-1]) if lines else {}
    except ValueError:
        return {}
    return got if isinstance(got, dict) else {}


def start(scan, path: pathlib.Path) -> tuple[str, dict]:
    """`handed start --tasks <파일>` 한 번 — (끝 — TOOK · NOT_LAUNCHED · REFUSED · UNKNOWN, 끝 줄의 JSON). 시한을 넘긴 부름은 넘겨졌을 수 있어
    UNKNOWN 이다 — 「못 띄웠다」로 읽으면 사람이 같은 일을 또 맡긴다. 부른 손은 프로그램을 못 띄웠을 때만 종료 값 자리에 None 을 낸다
    (그때 출력은 비었다 — `presses.run_unattended`)."""
    code, out = scan([HANDED_ENTRY, "start", "--tasks", str(path)], START_TIMEOUT_S)
    rec = last_json(out)
    if code == 0 and rec.get("id"):
        return TOOK, rec
    if code is None:
        return NOT_LAUNCHED, rec
    if rec.get("cannot") or rec.get("error"):
        return REFUSED, rec
    return UNKNOWN, rec


def show(scan, launch: str) -> dict | None:
    """`handed show --id <판>` 한 번 — 그 판의 기록(답의 `id` 가 그 판일 때만), 아니면 None."""
    code, out = scan([HANDED_ENTRY, "show", "--id", launch], SHOW_TIMEOUT_S)
    rec = last_json(out)
    return rec if code == 0 and rec.get("id") == launch else None


def find_launch(key: str, scan) -> dict | None:
    """그 누름의 판 — 도는 판의 목록(`handed list`)에서 `brief` 가 그 누름의 열쇠인 것. 없으면 None."""
    code, out = scan([HANDED_ENTRY, "list"], SHOW_TIMEOUT_S)
    if code != 0:
        return None
    for line in (out or "").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict) and rec.get("brief") == key and rec.get("id"):
            return rec
    return None


def clock_said(scan, args: list[str]) -> tuple[bool | None, str]:
    """`--chosen-at` 을 준 시계의 명령 한 번 — (따르지 않았나, 그 창에 적을 말). 그 명령은 끝 줄에 그 말만 내고 종료 값으로 따랐나를
    댄다(0 따랐다 · 1 안 따랐다). 못 부르거나 끝 줄이 없거나 그 밖의 종료 값이면 (None, 까닭) — 남겨 두어 시계 판이 받는다."""
    code, out = scan([CLOCK_ENTRY, *args], AWAY_TIMEOUT_S)
    if code == TIMED_OUT:
        return None, TIMEOUT_SAID
    if code is None:
        return None, NO_RUNNER
    lines = out.strip().splitlines()
    if not lines or code not in (0, 1):
        return None, NO_END.format(code=code)
    return code != 0, lines[-1].strip()


def away_args(on: bool, at: str) -> list[str]:
    """「자리 밖에서 보기」를 켜고 끄는 시계 명령의 인자."""
    return ["away", "on" if on else "off", "--chosen-at", at]


def times_args(times: list[str], base: list[str], at: str) -> list[str]:
    """창에서 고르신 보고 시각을 거는 시계 명령의 인자 — 보던 시각(`base`)에서 더하고 빼신 것만 얹는다(시계 판이 같은 자로 잰다)."""
    return ["window-times", *times, "--window-base", *base, "--chosen-at", at]
