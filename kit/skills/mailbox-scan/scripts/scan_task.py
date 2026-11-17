"""스캔을 윈도 작업 스케줄러에 걸고 · 보고 · 끄는 손 — 작업 하나(`TASK_NAME`)가 몇 분마다 `scan.py run` 을 창 없이(pythonw) 부른다.

작업 정의의 각 칸이 왜 그 값인가는 `references/DESIGN.md` 「작업 스케줄러의 작업」이 든다.

    xml = task_xml(every=분, full_every=분, hand=경로)   # 등록할 정의(UTF-16 으로 쓴다 — schtasks /XML 이 그 꼴을 받는다)
    register_command(xml_path) · query_command() · delete_command()   # schtasks 의 명령줄 — 도는 쪽은 scan.py 가 든다
"""

from __future__ import annotations

import getpass
import os
import pathlib
import sys
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

from scan_const import TASK_TIME_LIMIT_MIN

TASK_NAME = r"\mail-secretary\mailbox-scan"     # 사용자 폴더와 같은 이름의 작업 폴더 — 그 폴더의 다른 작업(runner · watch)과 안 겹친다
SCHTASKS = "schtasks.exe"
FIRST_DELAY_MIN = 1                             # 등록한 뒤 첫 판까지
LOGON_DELAY_MIN = 2                             # 로그온한 뒤 첫 판까지 — 로그온 직후 세션 손이 서기를 조금 기다린다

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

# 작업 스케줄러가 정의를 받나만 묻는다 — 정의를 지어 XML 을 넣어 볼 뿐 등록하지 않는다
VALIDATE_PS = ("$x = [IO.File]::ReadAllText($env:MAILBOX_SCAN_TASK_XML); $s = New-Object -ComObject Schedule.Service; $s.Connect(); "
               "$d = $s.NewTask(0); $d.XmlText = $x; 'ok'")


def windowless_python() -> pathlib.Path:
    """창 없는 파이썬(pythonw.exe) — 지금 도는 파이썬 곁. 없으면 지금 파이썬(창이 뜬다 — 부르는 쪽이 알린다)."""
    here = pathlib.Path(sys.executable)
    w = here.with_name("pythonw.exe")
    return w if w.is_file() else here


def user_id() -> str:
    domain = os.environ.get("USERDOMAIN", "").strip()
    return f"{domain}\\{getpass.getuser()}" if domain else getpass.getuser()


def run_arguments(scan_py: pathlib.Path, hand: pathlib.Path, full_every: int) -> str:
    """작업이 부르는 명령의 인자 — 손의 자리를 명령줄에 굳힌다(작업은 대화의 환경변수를 안 물려받는다)."""
    return f'-X utf8 -I "{scan_py}" run --hand "{hand}" --full-every {full_every}'


def task_xml(*, every: int, full_every: int, hand: pathlib.Path, scan_py: pathlib.Path, start: datetime | None = None) -> str:
    begin = (start or datetime.now() + timedelta(minutes=FIRST_DELAY_MIN)).strftime("%Y-%m-%dT%H:%M:%S")
    return TEMPLATE.format(every=every, start=begin, user=escape(user_id()), logon_delay=LOGON_DELAY_MIN, limit=TASK_TIME_LIMIT_MIN,
                           pythonw=escape(str(windowless_python())), arguments=escape(run_arguments(scan_py, hand, full_every)),
                           workdir=escape(str(scan_py.parent)))


def write_xml(path: pathlib.Path, xml: str) -> None:
    """schtasks /XML 이 받는 꼴로 쓴다 — UTF-16(BOM)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(xml, encoding="utf-16")


def register_command(xml_path: pathlib.Path) -> list[str]:
    return [SCHTASKS, "/Create", "/TN", TASK_NAME, "/XML", str(xml_path), "/F"]


def query_command() -> list[str]:
    return [SCHTASKS, "/Query", "/TN", TASK_NAME, "/XML"]


def delete_command() -> list[str]:
    return [SCHTASKS, "/Delete", "/TN", TASK_NAME, "/F"]


def validate_command() -> list[str]:
    return ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", VALIDATE_PS]


def read_definition(xml: str) -> dict[str, str]:
    """작업 스케줄러가 돌려준 정의(XML)에서 사람에게 말할 것 — 간격 · 켜짐 · 한 번에 하나 · 부르는 인자."""
    import xml.etree.ElementTree as ET
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    root = ET.fromstring(xml)

    def text(path: str) -> str:
        node = root.find(path, ns)
        return (node.text or "").strip() if node is not None else ""
    return {"interval": text(".//t:TimeTrigger/t:Repetition/t:Interval"), "enabled": text("./t:Settings/t:Enabled"),
            "instances": text("./t:Settings/t:MultipleInstancesPolicy"), "command": text(".//t:Exec/t:Command"),
            "arguments": text(".//t:Exec/t:Arguments")}
