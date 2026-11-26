"""옛 스캔 작업의 이름과 인자 — 옛 판은 작업 하나(`TASK_NAME`)가 몇 분마다 `scan.py run` 을 창 없이 부르게 걸었다. 이 판은 그 작업을 걸지 않고,
남은 작업을 보이고(`status`) · 지우고(`unregister`) · 거둔다(`adopt`). 남은 작업의 인자를 그 판이 건 꼴로 되읽어 `status --json` 의 칸을 짓는다.

    arguments_parts(d["arguments"])   # 걸린 정의의 인자를 옛 판이 건 꼴의 칸(입구 · 손 · 전체 주기)으로 — 그 꼴이 아니면 None
"""

from __future__ import annotations

from task_base import template_pattern

TASK_NAME = r"\mail-secretary\mailbox-scan"     # 옛 판이 건 작업 — 사용자 폴더와 같은 이름의 작업 폴더에 일일 보고의 시계(daily-brief)와 나란히 섰다

# 옛 판의 작업이 부른 명령의 인자 — 사용자 PC 의 작업 정의에 굳은 글이다. 남은 작업을 이 틀로 되읽는다
RUN_ARGUMENTS = '-X utf8 -I "{scan_py}" run --hand "{hand}" --full-every {full_every}'
RUN_ARGUMENTS_READ = template_pattern(RUN_ARGUMENTS, {"scan_py": r'[^"]*', "hand": r'[^"]*', "full_every": r"\d+"})


def arguments_parts(arguments: str) -> dict[str, str] | None:
    """걸린 작업의 인자를 틀의 칸(입구 `scan_py` · 손 `hand` · 전체 주기 `full_every`)으로 되읽는다 — 그 틀로 지은 글이 아니면 None."""
    got = RUN_ARGUMENTS_READ.fullmatch(arguments.strip())
    return got.groupdict() if got else None
