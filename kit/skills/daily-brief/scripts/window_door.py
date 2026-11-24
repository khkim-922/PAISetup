"""시계 판이 쓰는 창의 문 — 열린 보고 창에서 고르신 보고 시각 · 「자리 밖에서 보기」를 읽어 시계 판에 값으로 내고(`read_choices` — 같은 스킬의
`unattended/` 가 함수로 부른다), 시계가 받았나를 그 창의 그 칸에 돌려 적는다(거두는 손 `ticks.py` 의 `--times-done` · `--away-done`). 창 곁의 손과 같은 누름 종류 표의 줄(`press_kinds.TIMES` · `press_kinds.AWAY`)로 재고 적는다. 어느 길이든 그 창에 지금 모습을
함께 적는다. 열린 보고 창이 없으면 아무것도 안 연다.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import NamedTuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
import brief_const as C  # noqa: E402
import cli  # noqa: E402
import edge as E  # noqa: E402
import press_kinds as M  # noqa: E402
import state as V  # noqa: E402
from brief_const import EXIT_NO_EDGE, EXIT_OK  # noqa: E402

NO_EDGE = "보고 창의 시각을 못 읽었다 — 로그인 Edge({host}:{port})에 못 닿았다({exc})"
EDGE_LOST = "보고 창의 시각을 못 읽었다 — 로그인 Edge 와 주고받다 멈췄다({exc})"
NO_WINDOW = "고르신 보고 시각 없음 — 열린 보고 창이 없다"
NOT_WRITTEN = "안 적었다 — 그 뒤에 새로 고르셨거나 고르신 것이 없다"
WRITTEN = "적었다 — 보고 창에 받았나를 돌려 적었다"


class Choices(NamedTuple):
    """보고 창에서 고르신 것 가운데 시계가 받을 것 — `times` (고르신 시각들, 그때 보던 시각들, 고른 때) · `away` (켬인가, 고른 때). 거둘 고름이
    없는 쪽은 None."""
    times: tuple[list[str], list[str], str] | None
    away: tuple[bool, str] | None


def door(folder: pathlib.Path, done_at: str, said: str, refused: bool, kind: M.Measure = M.TIMES) -> int:
    """`--times-done` · `--away-done` — 열린 보고 창에 붙어 그 칸을 읽고 지금 모습을 적은 뒤, 시계가 받았나를 `kind` 의 칸에 돌려 적고 한 일의
    줄을 낸다. 종료 값 — 0 · 3 로그인 Edge 에 못 닿았다."""
    try:
        with E.window(None) as page:
            got = dict(E.stored(page.read(), kind.key)).get("")
            page.write([V.row(folder)])
            cli.say(write_back(page, got, done_at, said, refused, kind))
            return EXIT_OK
    except E.NoEdge as exc:
        cli.say([NO_EDGE.format(host=C.EDGE_HOST, port=E.port(), exc=exc)])
        return EXIT_NO_EDGE
    except E.NoWindow:
        cli.say([NO_WINDOW])
        return EXIT_OK
    except E.EdgeGone as exc:
        cli.say([EDGE_LOST.format(exc=exc)])
        return EXIT_NO_EDGE


def write_back(page: E.Tab, got: dict | None, done_at: str, said: str, refused: bool, kind: M.Measure) -> list[str]:
    """시계가 받았나를 그 창의 그 칸에 돌려 적는다(`kind.back`) — 그 칸이 시계가 받은 고름(같은 고른 때)일 때만. 낸 것은 한 일의 한 줄."""
    if not got or got.get("at") != done_at:
        return [NOT_WRITTEN]
    page.write([[kind.key, json.dumps(kind.back(got, said, refused), ensure_ascii=False)]])
    return [WRITTEN]


def read_choices(folder: pathlib.Path) -> Choices | None:
    """열린 보고 창에 붙어 고르신 것을 읽고(`choices_of`) 그 창에 지금 모습을 적는다 — 시계 판이 함수로 부른다. 열린 보고 창이 없거나 로그인
    Edge 에 못 닿았거나 주고받다 멈췄으면 None(아무것도 안 연다)."""
    try:
        with E.window(None) as page:
            rows = page.read()
            page.write([V.row(folder)])
            return choices_of(rows)
    except (E.EdgeGone, E.NoWindow):
        return None


def choices_of(rows: list) -> Choices:
    """창에서 읽은 칸에서 시계가 받을 고름 — 보고 시각 고름(`press_kinds.TIMES`)과 「자리 밖에서 보기」 고름(`press_kinds.AWAY`)을 창 곁의 손과
    같은 자로, 시계 판의 때(늘 거둔다)로 잰다. 거둘 고름이 없는 쪽은 None."""
    return Choices(M.TIMES.due(dict(E.stored(rows, M.TIMES.key)).get(""), True), M.AWAY.due(dict(E.stored(rows, M.AWAY.key)).get(""), True))

