"""시계 한 판의 겉 — 작업 스케줄러가 주기마다 부르는 `clock.py tick` 의 손. OS 잠금을 쥐고, 옛 파일을 옮겨 받고, 그날 장부를 읽어 이 판의
때를 먼저 적은 뒤 판 한 번(`clock_round.round_lines`)을 하고 장부를 다시 쓴다.

    code = tick(home, hand)          # 종료 값 — 0 됐다(잠금을 못 쥐어 건너뛴 판도) · 1 손 · 스캔을 못 찾았다 · 그날 장부를 그 순간 못 읽었다

판 끝의 줄은 판이 낸 그대로 찍는다(할 말이 없으면 안 찍는다). 손 · 스캔이 없어도 판은 돈다 — 보고 창의 누름 거두기는 그 둘 없이도 선다.
"""

from __future__ import annotations

import pathlib

import clock as tm
import clock_book as B
import clock_round as R
import scan_door as D
import take_over as TO
import unattended_const as C
import unattended_store as st
from oslock import OsLock

EXIT_OK, EXIT_STOPPED = 0, 1
NO_HAND = "[시계 — {missing}]"
NO_SCAN = "[시계 — 메일함 스캔 스킬(mailbox-scan)을 못 찾았다: {path} — 보고 시각에 메일함을 못 읽는다]"
DAY_UNREAD = "[보고 예약 — 그날 장부를 그 순간 못 읽었다({why}) — 이 판은 쉬고 다음 확인에 다시 본다]"


def tick(home: pathlib.Path, hand: pathlib.Path) -> int:
    """시계 한 판 — 잠금을 못 쥐면 아무것도 안 내고 0. 쥐면 옛 파일을 옮겨 받고(`take_over`) 그날 장부를 읽어 이 판의 때를 먼저 적고(창의 `seen`),
    판을 한 뒤 장부를 다시 쓰고 판 끝의 줄을 찍는다. 앞 판의 때는 이 판의 때로 덮기 전에 읽어 판에 준다 — 앞 판 뒤에 선 스캔의 답만 새 답이다."""
    home.mkdir(parents=True, exist_ok=True)
    lock = OsLock(home / C.CLOCK_LOCK_FILE)
    if not lock.take():
        return EXIT_OK
    try:
        at = tm.utc_now()
        TO.take_over(home)
        try:
            book = B.load(home)
        except st.Unreadable as exc:
            print(DAY_UNREAD.format(why=exc))
            return EXIT_STOPPED
        since = tm.parse(B.clock_at(home))
        B.save(home, book, at)
        missing = parts_missing(hand)
        lines = R.round_lines(book, home, hand, at, since)
        B.save(home, book, at)
        for line in [*missing, *([lines] if lines else [])]:
            print(line)
        return EXIT_STOPPED if missing else EXIT_OK
    finally:
        lock.release()


def parts_missing(hand: pathlib.Path) -> list[str]:
    """판이 기대는 것 가운데 없는 것의 줄 — 회사 메일 손(`--hand`) · 곁의 메일함 스캔. 다 있으면 빈 것."""
    _, missing = D.mail_hand(str(hand))
    return ([NO_HAND.format(missing=missing)] if missing else []) + ([NO_SCAN.format(path=D.SCAN)] if not D.SCAN.is_file() else [])
