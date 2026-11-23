"""작업 스케줄러 손 — 작업 하나(`TASK_NAME`)가 몇 분마다 `scan.py run` 을 창 없이(pythonw) 부르게 정의를 짓고, 걸린 정의의 인자 · 간격을
거는 꼴로 되읽는다. schtasks · PowerShell 을 띄우고 그 출력을 푸는 몸은 곁의 `task_base` 가 든다(일일 보고의 시계 작업과 같은 몸이다).

작업 정의의 각 칸이 왜 그 값인가는 `references/DESIGN.md` 「작업 스케줄러의 작업」이 든다.

    xml = task_xml(every=분, full_every=분, hand=경로, scan_py=경로)   # 등록할 정의(UTF-16 으로 쓴다 — schtasks /XML 이 그 꼴을 받는다)
    arguments_parts(d["arguments"]) · interval_minutes(d["interval"])   # 걸린 정의의 인자 · 간격을 거는 꼴로 되읽는다 — 그 꼴이 아니면 None
"""

from __future__ import annotations

import pathlib
import re
import string
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

from scan_const import TASK_TIME_LIMIT_MIN
from task_base import SCAN_LOGON_DELAY_MIN, user_id, windowless_python

TASK_NAME = r"\mail-secretary\mailbox-scan"     # 사용자 폴더와 같은 이름의 작업 폴더 — 그 폴더의 다른 작업(runner · watch)과 안 겹친다
FIRST_DELAY_MIN = 1                             # 등록한 뒤 첫 판까지

TEMPLATE = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>메일함 스캔 — {every}분마다 사내 메일함을 읽어 새 메일과 바뀜을 사용자 폴더에 적는다(메일함은 안 바꾼다)</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT{every}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>{start}</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{user}</UserId>
      <Delay>PT{logon_delay}M</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{user}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT{limit}M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{pythonw}</Command>
      <Arguments>{arguments}</Arguments>
      <WorkingDirectory>{workdir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""

VALIDATE_ENV = "MAILBOX_SCAN_TASK_XML"           # 정의를 받나 물을 때 정의 파일의 자리를 PowerShell 에 건네는 환경변수

# 작업이 부르는 명령의 인자 — 손의 자리를 명령줄에 굳힌다(작업은 대화의 환경변수를 안 물려받는다). 거는 쪽(`run_arguments`)과 되읽는 쪽
# (`arguments_parts`)이 이 틀 하나에서 나온다. 사용자 PC 의 작업 정의에 굳는 글이라 바꾸면 이미 건 PC 의 작업은 옛 꼴로 남는다
RUN_ARGUMENTS = '-X utf8 -I "{scan_py}" run --hand "{hand}" --full-every {full_every}'
RUN_ARGUMENT_FORMS = {"scan_py": r'[^"]*', "hand": r'[^"]*', "full_every": r"\d+"}   # 되읽을 때 칸마다 받는 글
INTERVAL_FORM = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?")   # 작업 정의의 간격(ISO 8601 기간 — 거는 꼴은 PT{분}M)


def template_pattern(template: str, forms: dict[str, str]) -> re.Pattern[str]:
    """`str.format` 틀을 그 틀로 지은 글을 되읽는 정규식으로 — 글자는 그대로, 칸마다 `forms` 의 꼴을 이름 붙은 묶음으로 잡는다."""
    parts = []
    for literal, name, _, _ in string.Formatter().parse(template):
        parts.append(re.escape(literal))
        if name:
            parts.append(f"(?P<{name}>{forms[name]})")
    return re.compile("".join(parts))


RUN_ARGUMENTS_READ = template_pattern(RUN_ARGUMENTS, RUN_ARGUMENT_FORMS)


def run_arguments(scan_py: pathlib.Path, hand: pathlib.Path, full_every: int) -> str:
    """작업이 부르는 명령의 인자 — 틀(`RUN_ARGUMENTS`)에 입구 · 손 · 전체 주기를 채운다."""
    return RUN_ARGUMENTS.format(scan_py=scan_py, hand=hand, full_every=full_every)


def arguments_parts(arguments: str) -> dict[str, str] | None:
    """걸린 작업의 인자를 틀의 칸(입구 `scan_py` · 손 `hand` · 전체 주기 `full_every`)으로 되읽는다 — 그 틀로 지은 글이 아니면 None."""
    got = RUN_ARGUMENTS_READ.fullmatch(arguments.strip())
    return got.groupdict() if got else None


def interval_minutes(interval: str) -> int | None:
    """작업 정의의 간격(ISO 8601 기간)을 분으로 — 기간의 꼴이 아니거나 분으로 안 떨어지면 None."""
    got = INTERVAL_FORM.fullmatch(interval.strip())
    if not got or not any(got.groups()):
        return None
    days, hours, minutes, seconds = (int(x or 0) for x in got.groups())
    total_s = ((days * 24 + hours) * 60 + minutes) * 60 + seconds
    return total_s // 60 if total_s % 60 == 0 else None


def task_xml(*, every: int, full_every: int, hand: pathlib.Path, scan_py: pathlib.Path, start: datetime | None = None) -> str:
    """등록할 작업 정의(XML) — 주기 · 손 · 입구를 채운다."""
    begin = (start or datetime.now() + timedelta(minutes=FIRST_DELAY_MIN)).strftime("%Y-%m-%dT%H:%M:%S")
    return TEMPLATE.format(every=every, start=begin, user=escape(user_id()), logon_delay=SCAN_LOGON_DELAY_MIN, limit=TASK_TIME_LIMIT_MIN,
                           pythonw=escape(str(windowless_python())), arguments=escape(run_arguments(scan_py, hand, full_every)),
                           workdir=escape(str(scan_py.parent)))
