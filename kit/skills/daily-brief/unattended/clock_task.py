"""시계의 작업 스케줄러 손 — 작업 하나(`TASK_NAME`)가 몇 분마다 `clock.py tick` 을 창 없이(pythonw) 부르게 정의를 짓는다. schtasks ·
PowerShell 을 띄우고 그 출력을 푸는 몸은 곁의 `task_base` 가 든다(메일함 스캔의 작업 손과 같은 몸이다 — 작업의 이름 · 설명 · 인자 · 시작
때만 다르다).
시작 때는 스캔 작업과 어긋나게 건다 — 주기의 절반 뒤 · 로그온은 스캔보다 늦게. 둘이 같은 분에 깨면 시계가 청한 판이 앞 판을 기다리게 된다.

    xml = task_xml(every=분, home=경로, hand=경로)       # 등록할 정의(UTF-16 으로 쓴다 — schtasks /XML 이 그 꼴을 받는다)
"""

from __future__ import annotations

import pathlib
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

from task_base import SCAN_LOGON_DELAY_MIN, user_id, windowless_python
from unattended_const import CLOCK_ENTRY, CLOCK_TIME_LIMIT_MIN, HERE

TASK_LEAF = "daily-brief"                       # 작업의 이름 — 사람이 읽는 줄이 이 이름으로 댄다
TASK_NAME = r"\mail-secretary" + "\\" + TASK_LEAF   # 메일함 스캔과 같은 작업 폴더 — 그 폴더의 스캔 작업(mailbox-scan)과 나란히 선다
FIRST_DELAY_MIN = 1                             # 등록한 뒤 첫 판까지(여기에 주기의 절반을 더한다)

TEMPLATE = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>일일 보고의 시계 — {every}분마다 정한 시각의 보고와 보고 창의 누름을 살핀다(보고 시각에 메일함 스캔에 한 판을 청해 보고를 띄운다)</Description>
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

VALIDATE_ENV = "DAILY_BRIEF_TASK_XML"           # 정의를 받나 물을 때 정의 파일의 자리를 PowerShell 에 건네는 환경변수

# 작업이 부르는 명령의 인자 — 사용자 폴더 · 손의 자리를 명령줄에 굳힌다(작업은 대화의 환경변수를 안 물려받는다). 사용자 PC 의 작업 정의에
# 굳는 글이라 바꾸면 이미 건 PC 의 작업은 옛 꼴로 남는다
TICK_ARGUMENTS = '-X utf8 -I "{clock_py}" tick --dir "{home}" --hand "{hand}"'


def tick_arguments(home: pathlib.Path, hand: pathlib.Path) -> str:
    """작업이 부르는 명령의 인자 — 틀(`TICK_ARGUMENTS`)에 입구 · 사용자 폴더 · 손을 채운다."""
    return TICK_ARGUMENTS.format(clock_py=HERE / CLOCK_ENTRY, home=home, hand=hand)


def task_xml(*, every: int, home: pathlib.Path, hand: pathlib.Path, start: datetime | None = None) -> str:
    """등록할 작업 정의(XML) — 주기 · 사용자 폴더 · 손을 채운다. 시작 때 · 로그온 뒤 첫 판은 스캔 작업보다 주기의 절반 늦게 둔다."""
    half = every // 2
    begin = (start or datetime.now() + timedelta(minutes=FIRST_DELAY_MIN + half)).strftime("%Y-%m-%dT%H:%M:%S")
    return TEMPLATE.format(every=every, start=begin, user=escape(user_id()), logon_delay=SCAN_LOGON_DELAY_MIN + half, limit=CLOCK_TIME_LIMIT_MIN,
                           pythonw=escape(str(windowless_python())), arguments=escape(tick_arguments(home, hand)), workdir=escape(str(HERE)))
