"""보낸 분에 신원 붙이기 — 스캔이 쌓은 받은 메일의 보낸 분 주소마다 주소록 스킬의 신원 명령이 지은 신원을 지금 모습에 적는다.

    got = attach(state, hand, at, full)      # 판 값(판 기록에 싣는다) — 묻지 못했으면 그 까닭. 판을 멈추지 않는다

신원은 주소마다 한 줄로 지금 모습의 `senders`(주소 소문자 → 신원)에 산다 — 메일마다 베껴 두지 않는다(같은 사람의 메일 수백 통이 한 줄을
가리킨다). 읽는 명령이 메일을 보일 때 그 주소의 신원을 붙인다. 신원의 칸과 뜻은 그 명령(스킬 company-directory 의 `scripts/identity.py`)
머리말이 든다 — 이 조각은 상태 · 지은 때만 보고 칸을 안 푼다.

신원 명령은 프로세스로 부른다(코드를 싣지 않는다). 그 명령이 없거나 · 시한을 넘기거나 · 꼴이 다르면 이번 판은 신원을 안 고치고 그 까닭을 판
값에 적는다 — 판은 그대로 맺는다. 못 지은 주소(「모름」)는 적지 않아 다음 판이 다시 묻는다.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
from datetime import datetime
from typing import Any

import proc_base as P
import scan_const as C
import scan_diff as D
import scan_time as tm


def find_identity(hand: pathlib.Path) -> pathlib.Path | None:
    """신원 명령의 자리 — `MAILBOX_SCAN_IDENTITY` → 회사 메일 손과 같은 스킬 뿌리. 없으면 None."""
    given = os.environ.get(C.IDENTITY_ENV, "").strip()
    path = pathlib.Path(given).expanduser() if given else hand.resolve().parents[2] / C.IDENTITY_SKILL / pathlib.Path(*C.IDENTITY_SCRIPT)
    return path if path.is_file() else None


def wanted(state: dict[str, Any]) -> list[str]:
    """신원을 물을 주소 — 받은 메일(보낸편지함 밖)의 보낸 분 모두, 새 메일의 보낸 분이 먼저다. 다시 짓는 날 · 서버에 묻는 몫은 신원 명령이 제 표로
    가른다 — 표로 선 주소는 서버에 안 닿는다(주소 수백에 0.3 초). 몫이 다 차면 옛 메일의 보낸 분이 다음 판으로 밀린다."""
    mails = sorted((m for m in (state.get("mails") or {}).values() if m.get("box") != D.SENT and m.get("addr")),
                   key=lambda m: m.get("date") or "", reverse=True)
    out = []
    for m in mails:
        addr = m["addr"].strip().casefold()
        if addr not in out:
            out.append(addr)
    return out


def call(script: pathlib.Path, args: list[str], addrs: list[str], timeout: float) -> tuple[dict | None, str]:
    """신원 명령 한 번 — (답, 못 받은 까닭). 답이 꼴이 아니면 (None, 까닭)."""
    try:
        done = P.run_python(script, args, timeout, "\n".join(addrs).encode("utf-8"))
    except subprocess.TimeoutExpired:
        return None, f"신원 명령이 {timeout:.0f}초 안에 안 끝났다"
    except OSError as exc:
        return None, f"신원 명령을 못 띄웠다({exc})"
    if args[0] != "lookup":
        return {"code": done.returncode}, ""
    try:
        got = json.loads(done.stdout.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None, f"신원 명령의 답이 JSON 이 아니다(종료 값 {done.returncode})"
    if not isinstance(got, dict) or got.get("format") != C.IDENTITY_FORMAT or not isinstance(got.get("people"), dict):
        return None, f"신원 명령의 답이 아는 꼴(꼴 번호 {C.IDENTITY_FORMAT})이 아니다"
    return got, ""


def attach(state: dict[str, Any], hand: pathlib.Path, at: datetime, full: bool) -> dict[str, Any]:
    """물을 주소(`wanted`)의 신원을 신원 명령으로 받아 지금 모습의 `senders` 에 적는다 — 「모름」 은 안 적는다. 메일함 전체 판이면 미리 받는
    조직도 가운데 낡은 것 하나를 받게 한다(`pull --unattended`). 내는 것 — 판 값 {asked · filled · note}."""
    addrs = wanted(state)
    script = find_identity(hand) if addrs or full else None
    if script is None:
        return {"note": "신원 명령(company-directory 의 scripts/identity.py)을 못 찾아 보낸 분 신원을 안 붙였다"} if addrs else {}
    info: dict[str, Any] = {}
    if addrs:
        got, why = call(script, ["lookup"], addrs, C.IDENTITY_TIMEOUT_S)
        if got is None:
            return {"note": why}
        senders = state.setdefault("senders", {})
        stamp = tm.stamp(at)
        filled = 0
        for addr, who in got["people"].items():
            if isinstance(who, dict) and who.get("state") not in (None, C.UNKNOWN_IDENTITY):
                fresh = {k: v for k, v in who.items() if k not in ("at", "addr")}
                if {k: v for k, v in (senders.get(addr) or {}).items() if k != "at"} != fresh:
                    senders[addr] = fresh | {"at": stamp}
                    filled += 1
        info = {"asked": len(addrs), "filled": filled, **({"note": "사내 세션이 없어 신원을 다 못 물었다"} if not got.get("session") else {})}
    if full:
        done, why = call(script, ["pull", "--unattended"], [], C.IDENTITY_PULL_TIMEOUT_S)
        why = why or (f"조직도 미리 받기가 종료 값 {done['code']} 로 끝났다" if done and done.get("code") else "")
        if why:
            info["note"] = " · ".join(x for x in (info.get("note"), why) if x)
    return info
