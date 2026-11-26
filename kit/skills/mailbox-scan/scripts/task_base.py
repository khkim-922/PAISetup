"""작업 스케줄러 바탕 — 비서의 작업 하나를 schtasks · PowerShell 로 걸고 · 묻고 · 지우고 · 정의를 받나 묻고, 그 답을 푼다. 바깥은 작업
스케줄러 하나다. 작업 정의의 틀(`DEFINITION` — 한 번에 하나 · 로그온한 사람의 세션 · 창 없는 파이썬)도 여기 하나다. 작업마다 다른 것(이름 ·
설명 · 부르는 인자 · 시작 때 · 시한)은 부르는 쪽의 작업 손이 든다.

이 파일의 원본은 스킬 mailbox-scan 의 `scripts/task_base.py` 다 — 같은 몸이 필요한 위 스킬은 이 파일을 바이트째 베껴 들고(스킬끼리 코드를
싣지 않는다), 원본 스킬은 누가 베끼는지 모른다. 원본만 고치고 베낀다.

    done = ask(register_command(task_name, xml_path))           # Answer(code, out, err) — 출력은 물을 때 푼다
    ask(query_command(task_name)) · ask(delete_command(task_name))
    ok = accepted(ask(validate_command(env), env=validate_env(env, xml_path)))   # 작업 스케줄러가 정의를 받나(등록 안 함)
    d = read_definition(done.out)                               # 걸린 정의의 간격 · 켜짐 · 한 번에 하나 · 부르는 것
    on = is_enabled(d)                                          # 걸린 작업이 켜져 있나 — 사람이 작업 스케줄러에서 끈 작업은 거짓
    every = interval_minutes(d["interval"])                     # 걸린 정의의 간격을 분으로 — 기간의 꼴이 아니거나 분으로 안 떨어지면 None
    parts = template_pattern(틀, 칸마다의_꼴).fullmatch(인자)   # 틀로 지은 인자를 칸으로 되읽는다
    same_path(a, b)                                             # 두 경로가 같은 자리인가(윈도의 대소문자 · 사이 글자)
    shown(register_command(task_name, xml_path))                # 사람에게 보일 명령줄
    xml = definition(description=설명, every=분, start=때, logon_delay=분, limit=분, arguments=인자, workdir=경로, enabled=참)   # 등록할 정의
"""

from __future__ import annotations

import getpass
import locale
import os
import pathlib
import re
import string
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from xml.sax.saxutils import escape

SCHTASKS = "schtasks.exe"
# 로그온한 뒤 첫 판까지(분)의 바탕 — 로그온 직후 세션 손이 서기를 조금 기다린다. 일일 보고의 시계 작업은 여기에 주기의 절반을 더해 깬다
SCAN_LOGON_DELAY_MIN = 2
# 작업 스케줄러가 정의를 받나만 묻는 PowerShell — 정의 파일의 자리를 환경변수(`{env}`)로 받아 XML 을 넣어 볼 뿐 등록하지 않는다. 받으면 `VALIDATE_OK` 를 낸다
VALIDATE_OK = "ok"
VALIDATE_PS = ("$x = [IO.File]::ReadAllText($env:{env}); $s = New-Object -ComObject Schedule.Service; $s.Connect(); "
               "$d = $s.NewTask(0); $d.XmlText = $x; '" + VALIDATE_OK + "'")


# 작업 정의의 틀 — 비서의 작업이 다 이 꼴로 선다. 각 칸이 왜 그 값인가는 스킬 mailbox-scan 의 `references/DESIGN.md` 「작업 스케줄러의 작업」이 든다
DEFINITION = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{description}</Description>
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
    <Enabled>{enabled}</Enabled>
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


def windowless_python() -> pathlib.Path:
    """창 없는 파이썬(pythonw.exe) — 지금 도는 파이썬 곁. 없으면 지금 파이썬(창이 뜬다 — 부르는 쪽이 알린다)."""
    here = pathlib.Path(sys.executable)
    w = here.with_name("pythonw.exe")
    return w if w.is_file() else here


def user_id() -> str:
    """작업을 돌릴 사용자 — 「도메인\\이름」(도메인이 없으면 이름)."""
    domain = os.environ.get("USERDOMAIN", "").strip()
    return f"{domain}\\{getpass.getuser()}" if domain else getpass.getuser()


def definition(*, description: str, every: int, start: datetime, logon_delay: int, limit: int, arguments: str, workdir: pathlib.Path,
               enabled: bool = True) -> str:
    """등록할 작업 정의(XML) — 틀(`DEFINITION`)에 설명 · 주기(분) · 첫 판의 때 · 로그온 뒤 첫 판(분) · 한 판의 시한(분) · 창 없는 파이썬이 받을
    인자 · 작업 폴더 · 켜짐을 채운다. 돌릴 사람과 파이썬은 이 PC 에서 읽는다(`user_id` · `windowless_python`)."""
    return DEFINITION.format(description=escape(description), every=every, start=start.strftime("%Y-%m-%dT%H:%M:%S"), user=escape(user_id()),
                             logon_delay=logon_delay, limit=limit, pythonw=escape(str(windowless_python())), arguments=escape(arguments),
                             workdir=escape(str(workdir)), enabled="true" if enabled else "false")


def template_pattern(template: str, forms: dict[str, str]) -> re.Pattern[str]:
    """`str.format` 틀을 그 틀로 지은 글을 되읽는 정규식으로 — 글자는 그대로, 칸마다 `forms` 의 꼴을 이름 붙은 묶음으로 잡는다."""
    parts = []
    for literal, name, _, _ in string.Formatter().parse(template):
        parts.append(re.escape(literal))
        if name:
            parts.append(f"(?P<{name}>{forms[name]})")
    return re.compile("".join(parts))


def same_path(a: str | pathlib.Path, b: str | pathlib.Path) -> bool:
    """두 경로가 같은 자리인가 — 윈도의 대소문자 · 사이 글자(`/` · `\\`) · `..` 를 고른 뒤 견준다."""
    return os.path.normcase(os.path.normpath(str(a))) == os.path.normcase(os.path.normpath(str(b)))


def write_xml(path: pathlib.Path, xml: str) -> None:
    """schtasks /XML 이 받는 꼴로 쓴다 — UTF-16(BOM)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(xml, encoding="utf-16")


def register_command(task_name: str, xml_path: pathlib.Path) -> list[str]:
    """정의 파일로 작업을 거는 schtasks 명령줄."""
    return [SCHTASKS, "/Create", "/TN", task_name, "/XML", str(xml_path), "/F"]


def query_command(task_name: str) -> list[str]:
    """걸린 작업의 정의를 묻는 schtasks 명령줄."""
    return [SCHTASKS, "/Query", "/TN", task_name, "/XML"]


def delete_command(task_name: str) -> list[str]:
    """작업을 지우는 schtasks 명령줄."""
    return [SCHTASKS, "/Delete", "/TN", task_name, "/F"]


def validate_command(env: str) -> list[str]:
    """작업 스케줄러가 정의를 받나만 묻는 PowerShell 명령줄(등록 안 함) — 정의 파일의 자리는 환경변수 `env` 로 받는다."""
    return ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", VALIDATE_PS.replace("{env}", env)]


def validate_env(env: str, xml_path: pathlib.Path) -> dict[str, str]:
    """정의를 받나 묻는 PowerShell 의 환경 — 지금 환경에 정의 파일의 자리를 `env` 라는 이름으로 얹는다."""
    return {**os.environ, env: str(xml_path)}


def shown(cmd: list[str]) -> str:
    """사람에게 보일 명령줄 — 빈칸이 든 인자는 따옴표에 싼다."""
    return " ".join(f'"{c}"' if " " in c else c for c in cmd)


@dataclass
class Answer:
    """작업 스케줄러 · PowerShell 한 번의 답 — 종료 값과 받은 그대로의 표준 출력 · 표준 오류. 글자(`out` · `err`)는 읽는 쪽이 물을 때만
    푼다 — 종료 값만 보는 쪽이 못 푸는 출력에 넘어지지 않게."""
    code: int
    raw_out: bytes
    raw_err: bytes

    @property
    def out(self) -> str:
        """표준 출력을 푼 글자."""
        return decode(self.raw_out)

    @property
    def err(self) -> str:
        """표준 오류를 푼 글자."""
        return decode(self.raw_err)


def ask(command: list[str], env: dict[str, str] | None = None) -> Answer:
    """작업 스케줄러(schtasks) · PowerShell 을 한 번 띄워 답을 받는다 — 출력은 물을 때 `decode` 로 푼다."""
    done = subprocess.run(command, capture_output=True, env=env)
    return Answer(done.returncode, done.stdout, done.stderr)


def accepted(done: Answer) -> bool:
    """정의를 받나 물은 답(`validate_command`)이 「받는다」인가 — 종료 0 이고 끝 글이 `VALIDATE_OK` 다."""
    return done.code == 0 and done.out.strip().endswith(VALIDATE_OK)


def decode(raw: bytes) -> str:
    """작업 스케줄러 · PowerShell 의 출력 — UTF-16(BOM · 0 바이트)이나 UTF-8, 아니면 콘솔의 OEM 코드 페이지(한글 윈도는 949)다.
    `-X utf8` 로 돌면 로캘이 UTF-8 로 보여 그 코드 페이지를 따로 묻는다."""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in raw[:200]:
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    if sys.platform == "win32":
        import ctypes
        return raw.decode(f"cp{ctypes.windll.kernel32.GetOEMCP()}", errors="replace")
    return raw.decode(locale.getencoding(), errors="replace")


def read_definition(xml: str) -> dict[str, str]:
    """작업 스케줄러가 돌려준 정의(XML)에서 사람에게 말할 것 — 간격 · 켜짐 · 한 번에 하나 · 부르는 인자."""
    import xml.etree.ElementTree as ET
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    root = ET.fromstring(xml)

    def text(path: str) -> str:
        """정의에서 그 자리의 글 — 없으면 빈 글."""
        node = root.find(path, ns)
        return (node.text or "").strip() if node is not None else ""
    return {"interval": text(".//t:TimeTrigger/t:Repetition/t:Interval"), "enabled": text("./t:Settings/t:Enabled"),
            "instances": text("./t:Settings/t:MultipleInstancesPolicy"), "command": text(".//t:Exec/t:Command"),
            "arguments": text(".//t:Exec/t:Arguments")}


INTERVAL_FORM = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?")   # 작업 정의의 간격(ISO 8601 기간 — 거는 꼴은 PT{분}M)


def interval_minutes(interval: str) -> int | None:
    """작업 정의의 간격(ISO 8601 기간)을 분으로 — 기간의 꼴이 아니거나 분으로 안 떨어지면 None."""
    got = INTERVAL_FORM.fullmatch(interval.strip())
    if not got or not any(got.groups()):
        return None
    days, hours, minutes, seconds = (int(x or 0) for x in got.groups())
    total_s = ((days * 24 + hours) * 60 + minutes) * 60 + seconds
    return total_s // 60 if total_s % 60 == 0 else None


def is_enabled(d: dict[str, str]) -> bool:
    """걸린 정의(`read_definition`)가 켜진 작업인가 — 작업 스케줄러가 「꺼짐」으로 적은 것만 거짓(칸이 없으면 켜짐이 기본이다)."""
    return d.get("enabled", "").strip().lower() != "false"
