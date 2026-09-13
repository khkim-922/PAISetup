"""가짜 `claude` 를 세우는 한 벌 — **심는 자**와 **담**.

이 파일은 혼자 안 돈다. 검사가 불러 쓰는 재료다(지금은 `cli_pipe_check.py` 하나).

⚠ **담이 이 파일이 선 까닭이다.** 가짜가 안 서면 `providers._cli_once` 는 오류를 내는
  대신 **이 PC 에 깔린 진짜 CLI** 를 부른다 — 검사가 빨간 것으로 끝나지 않고 그날의
  구독을 태우고, 판정이 그 PC 의 로그인 상태에 실린다(atelier #219 는 그렇게 실토큰을
  썼다). 그래서 부르기 **전에** 「지금 무엇이 불릴 것인가」를 `_cli_once` 와 **같은 자**로
  되읽고(`shutil.which(gateway.CLI_EXE)`), 우리가 심은 자리 밖이면 거기서 멈춘다.
  다른 자로 재면 검사만 초록이고 실제로는 진짜가 불린다.

⚠ **Windows 는 겉옷이 필요하다 — 그리고 그 겉옷 본문은 ASCII 라야 한다.**
  ① 확장자 없는 파일도 `.py` 도 `CreateProcess` 가 못 띄우고, `shutil.which` 는
     **PATHEXT 에 없는 확장자를 아예 안 본다.** 이름만 `claude` 인 파일을 PATH 에 세우면
     그래서 **안 잡히고 진짜가 잡힌다.**
  ② `.cmd` 겉옷을 씌우면 `CreateProcess` 가 `%ComSpec% /c` 로 감아 띄우는데, cmd.exe 는
     배치 파일 **본문을 콘솔 코드페이지**(한글 Windows 는 cp949)로 되읽는다. 본문을
     utf-8 로 적어 두면 경로에 한글이 한 자만 있어도 그 자리에서 깨져 「지정된 경로를
     찾을 수 없습니다」로 넘어진다 — **이 저장소 경로에 한글이 있다.** 그래서 본문에
     절대 경로를 안 적고, 파이썬은 환경변수로 · 몸통 경로는 cmd 가 스스로 아는 `%~dp0`
     로 받는다: 환경 블록과 배치 파일의 실제 경로는 유니코드로 건너가 코드페이지를
     안 탄다.
  ③ `-X utf8` 이 핵심이다: 겉옷 없이도 자식은 뜨지만, 한글 산출이 cp949 로 나가 utf-8 로
     읽는 부모 쪽에서 글자가 깨진다.
  POSIX 는 셔뱅이 들어 겉옷이 없다 — 같은 계약을 두 벌로 태우지 않는다.
"""
import os
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _plumb import Missing, gateway, get  # noqa: E402 — 배관은 선언이 고른다
from _verdict import EXIT_UNMEASURED, Unmeasured  # noqa: E402

# 겉옷이 부를 파이썬을 **환경변수로** 건넨다(위 ⚠②). 자식은 `_cli_once` 가 부모 환경을
# 그대로 물려 띄우므로 이 이름이 그대로 건너간다.
#
# ⚠ **접두어는 배관이 안 들 수도 있다** — 저장소마다 환경변수 접두어를 배관에 두지 않고
#   따로 선언하는 곳이 있다. 그 자리는 `gateway.conf` 의 `[values]` 가 값을 든다. 둘 다
#   없으면 **못 쟀다(2)** 다 — 이름을 지어내면 겉옷이 부를 파이썬이 자식에게 안 건너가고,
#   그 판은 「가짜가 안 섰다」가 아니라 조용히 진짜를 부르는 자리로 떨어진다.
try:
    FAKE_PY_ENV = f"{get('ENV_PREFIX')}_FAKE_PY"
except Missing as why:
    raise Unmeasured(f"⛔ 가짜 CLI 의 환경변수 이름을 못 지었다 — {why}") from why

# 「못 쟀다」로 나간다 — 어긋남(1)과 갈래가 다르다. 담에 걸린 판은 판정이 아니라
# **아예 안 잰 판**이다. 숫자의 진본은 종료코드 계약 하나다(`_verdict`).
REFUSED = EXIT_UNMEASURED


def plant(where, name, body):
    """가짜 자식 하나를 심고 **부를 이름**(경로)을 돌려준다.

    `body` 는 파이썬 원문이다 — 셔뱅은 이 함수가 얹는다.
    """
    where = Path(where)
    src = where / (f"{name}.py" if os.name == "nt" else name)
    src.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    src.chmod(src.stat().st_mode | stat.S_IEXEC | stat.S_IRWXU)
    if os.name != "nt":
        return str(src)
    os.environ[FAKE_PY_ENV] = sys.executable
    exe = where / f"{name}.cmd"
    # `encoding="ascii"` 가 위 ⚠② 를 **기계가 재게** 만든다 — 본문에 ASCII 밖 글자가
    # 섞이면 여기서 바로 죽고, cmd.exe 가 조용히 깨뜨리는 자리까지 안 간다.
    exe.write_text(f'@"%{FAKE_PY_ENV}%" -X utf8 "%~dp0{src.name}" %*\n',
                   encoding="ascii")
    return str(exe)


def guard(where):
    """부르기 **전에** 무엇이 불릴 것인가를 되읽는다 — 우리 자리 밖이면 멈춘다.

    `_cli_once` 가 자식을 찾는 그 줄(`shutil.which(gateway.CLI_EXE)`)을 그대로 쓴다.
    """
    seen = shutil.which(gateway.CLI_EXE)
    mine = Path(where).resolve()
    if not seen or not Path(seen).resolve().is_relative_to(mine):
        print("\n⛔ 가짜가 안 섰다 — **진짜 CLI 로 넘어가기 전에** 멈춘다.")
        print(f"   `{gateway.CLI_EXE}` 가 지금 가리키는 자리: {seen!r}")
        print(f"   가짜를 심은 자리: {str(mine)!r}")
        print("   이 검사는 실토큰을 쓰지 않는다 — 판정 없이 나간다.")
        sys.exit(REFUSED)
    return seen
