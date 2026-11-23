"""작업 스케줄러 바탕 — 비서의 작업 하나를 schtasks · PowerShell 로 걸고 · 묻고 · 지우고 · 정의를 받나 묻고, 그 답을 푼다. 바깥은 작업
스케줄러 하나다. 작업마다 다른 것(이름 · 정의의 틀 · 부르는 인자 · 시작 때)은 부르는 쪽의 작업 손이 든다.

이 파일의 원본은 스킬 mailbox-scan 의 `scripts/task_base.py` 다 — 같은 몸이 필요한 위 스킬은 이 파일을 바이트째 베껴 들고(스킬끼리 코드를
싣지 않는다), 원본 스킬은 누가 베끼는지 모른다. 원본만 고치고 베낀다.

    done = ask(register_command(task_name, xml_path))           # Answer(code, out, err) — 출력은 물을 때 푼다
    ask(query_command(task_name)) · ask(delete_command(task_name))
    ok = accepted(ask(validate_command(env), env=validate_env(env, xml_path)))   # 작업 스케줄러가 정의를 받나(등록 안 함)
    d = read_definition(done.out)                               # 걸린 정의의 간격 · 켜짐 · 한 번에 하나 · 부르는 것
    shown(register_command(task_name, xml_path))                # 사람에게 보일 명령줄
"""

from __future__ import annotations

import getpass
import locale
import os
import pathlib
import subprocess
import sys
from dataclasses import dataclass

SCHTASKS = "schtasks.exe"
# 메일함 스캔 작업이 로그온한 뒤 첫 판까지(분) — 로그온 직후 세션 손이 서기를 조금 기다린다. 일일 보고의 시계 작업은 이보다 늦게 깬다
# (둘이 같은 분에 깨면 시계가 청한 판이 앞 판을 기다리게 된다)
SCAN_LOGON_DELAY_MIN = 2
# 작업 스케줄러가 정의를 받나만 묻는 PowerShell — 정의 파일의 자리를 환경변수(`{env}`)로 받아 XML 을 넣어 볼 뿐 등록하지 않는다. 받으면 `VALIDATE_OK` 를 낸다
VALIDATE_OK = "ok"
VALIDATE_PS = ("$x = [IO.File]::ReadAllText($env:{env}); $s = New-Object -ComObject Schedule.Service; $s.Connect(); "
               "$d = $s.NewTask(0); $d.XmlText = $x; '" + VALIDATE_OK + "'")


def windowless_python() -> pathlib.Path:
    """창 없는 파이썬(pythonw.exe) — 지금 도는 파이썬 곁. 없으면 지금 파이썬(창이 뜬다 — 부르는 쪽이 알린다)."""
    here = pathlib.Path(sys.executable)
    w = here.with_name("pythonw.exe")
    return w if w.is_file() else here


def user_id() -> str:
    """작업을 돌릴 사용자 — 「도메인\\이름」(도메인이 없으면 이름)."""
    domain = os.environ.get("USERDOMAIN", "").strip()
    return f"{domain}\\{getpass.getuser()}" if domain else getpass.getuser()


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
