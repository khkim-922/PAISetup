"""시계의 작업 스케줄러 손 — 작업 하나(`TASK_NAME`)가 몇 분마다 `clock.py tick` 을 창 없이(pythonw) 부르게 정의를 짓는다. 정의의 틀과
schtasks · PowerShell 을 띄우고 그 출력을 푸는 몸은 곁의 `task_base` 가 든다(스킬 mailbox-scan 의 원본을 베낀 몸이다).
시작 때는 주기의 절반 뒤 · 로그온 뒤 첫 판은 바탕(`SCAN_LOGON_DELAY_MIN`)에 주기의 절반을 더해 건다 — 옛 판이 건 스캔 작업이 아직 남은 PC 에서도
둘이 같은 분에 깨지 않는다(같은 분에 깨면 시계가 청한 판이 앞 판을 기다리게 된다).

    xml = task_xml(every=분, home=경로, hand=경로, enabled=참)   # 등록할 정의(UTF-16 으로 쓴다 — schtasks /XML 이 그 꼴을 받는다)
    arguments_parts(d["arguments"])                     # 걸린 정의의 인자를 거는 꼴의 칸(입구 · 사용자 폴더 · 손)으로 — 그 꼴이 아니면 None
"""

from __future__ import annotations

import pathlib
from datetime import datetime, timedelta

from task_base import SCAN_LOGON_DELAY_MIN, definition, template_pattern
from unattended_const import CLOCK_ENTRY, CLOCK_TIME_LIMIT_MIN, HERE

TASK_LEAF = "daily-brief"                       # 작업의 이름 — 사람이 읽는 줄이 이 이름으로 댄다
TASK_NAME = r"\mail-secretary" + "\\" + TASK_LEAF   # 사용자 폴더와 같은 이름의 작업 폴더 — 옛 판의 스캔 작업(mailbox-scan)이 섰던 자리다
FIRST_DELAY_MIN = 1                             # 등록한 뒤 첫 판까지(여기에 주기의 절반을 더한다)
DESCRIPTION = ("일일 보고의 시계 — {every}분마다 정한 시각의 보고와 보고 창의 누름을 살핀다(보고 시각에 메일함 스캔에 한 판을 청해 "
               "보고를 띄운다)")   # 작업 스케줄러 화면에 보이는 설명

VALIDATE_ENV = "DAILY_BRIEF_TASK_XML"           # 정의를 받나 물을 때 정의 파일의 자리를 PowerShell 에 건네는 환경변수

# 작업이 부르는 명령의 인자 — 사용자 폴더 · 손의 자리를 명령줄에 굳힌다(작업은 대화의 환경변수를 안 물려받는다). 거는 쪽(`tick_arguments`)과
# 되읽는 쪽(`arguments_parts`)이 이 틀 하나에서 나온다. 사용자 PC 의 작업 정의에 굳는 글이라 바꾸면 이미 건 PC 의 작업은 옛 꼴로 남는다
TICK_ARGUMENTS = '-X utf8 -I "{clock_py}" tick --dir "{home}" --hand "{hand}"'
TICK_ARGUMENTS_READ = template_pattern(TICK_ARGUMENTS, {"clock_py": r'[^"]*', "home": r'[^"]*', "hand": r'[^"]*'})


def tick_arguments(home: pathlib.Path, hand: pathlib.Path) -> str:
    """작업이 부르는 명령의 인자 — 틀(`TICK_ARGUMENTS`)에 입구 · 사용자 폴더 · 손을 채운다."""
    return TICK_ARGUMENTS.format(clock_py=HERE / CLOCK_ENTRY, home=home, hand=hand)


def arguments_parts(arguments: str) -> dict[str, str] | None:
    """걸린 시계의 인자를 틀의 칸(입구 `clock_py` · 사용자 폴더 `home` · 손 `hand`)으로 되읽는다 — 그 틀로 지은 글이 아니면 None."""
    got = TICK_ARGUMENTS_READ.fullmatch(arguments.strip())
    return got.groupdict() if got else None


def task_xml(*, every: int, home: pathlib.Path, hand: pathlib.Path, start: datetime | None = None, enabled: bool = True) -> str:
    """등록할 작업 정의(XML) — 바탕의 틀(`task_base.definition`)에 주기 · 사용자 폴더 · 손 · 켜짐을 채운다. 시작 때 · 로그온 뒤 첫 판은 주기의
    절반 늦게 둔다."""
    half = every // 2
    return definition(description=DESCRIPTION.format(every=every), every=every,
                      start=start or datetime.now() + timedelta(minutes=FIRST_DELAY_MIN + half), logon_delay=SCAN_LOGON_DELAY_MIN + half,
                      limit=CLOCK_TIME_LIMIT_MIN, arguments=tick_arguments(home, hand), workdir=HERE, enabled=enabled)
