"""받는 손(``edge_session.js``)을 파이썬에서 부르는 한 자리 — 사내 앱 스킬의 얇은 명령(company-mail · company-calendar ·
company-ecm)이 이 폴더를 ``sys.path`` 에 넣고 싣는다. 손을 돌리고 종료 값 · 끝 줄 경로 · 손의 말을 닫힌 꼴 하나로 낸다 —
어느 종료 값에 무엇을 할지는 부르는 쪽이 제 종료 값으로 옮긴다(그 스킬의 SKILL.md).

어떻게 부르나::

    import ep_session

    got = ep_session.attach()                       # domino — 메일 · 일정
    got = ep_session.attach(("ecm",))                # ECM 만 — Domino 는 안 가린다
    got = ep_session.attach(("domino", "ecm"))       # 둘 다 꼭 서야 할 때
    got = ep_session.attach(env={"MAILBOX_URL": url})   # 손에 더 줄 환경변수
    if got.usable:                                   # 0 · 또는 2 인데 남은 파일이 있다 — 그 파일로 서버에 물어 본다
        session = got.file

무엇을 내나 — ``Attached(code, file, said)``. ``code`` 는 손의 종료 값(``OK`` 0 · ``TOOL`` 1 · ``NO_EDGE`` 2 · ``NOT_LOGGED_IN`` 3 ·
``ECM_HANDOFF`` 4 — 그 뜻은 ``edge_session.js`` 머리말. 4 는 ``ecm`` 을 준 부름에서만 나고, 로그인은 섰으니 사람에게 다시 로그인을
청하지 말고 스킬 ep-login 의 「ECM 만 못 받았다」를 가리킨다), ``file`` 은 표준 출력 끝 줄의 절대 경로가 있는 파일일 때만, ``said`` 는 손의 말(표준 오류 ·
없으면 표준 출력)이다. 손 · node 가 없거나 시한을 넘기면 돌리지 않고 ``TOOL`` 과 그 까닭을 낸다 — 예외는 안 낸다.
0 인데 끝 줄이 있는 파일의 절대 경로가 아니면 ``file`` 이 None 이다 — 부르는 쪽이 도구 고장으로 읽는다.

손의 자리 — 이 파일 곁의 ``edge_session.js``. 검사가 대역을 세울 때만 환경변수 ``EP_SESSION_HAND`` 가 그 자리를 바꾼다.
"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import shutil
import subprocess

HAND = pathlib.Path(__file__).resolve().with_name("edge_session.js")
HAND_ENV = "EP_SESSION_HAND"
OK, TOOL, NO_EDGE, NOT_LOGGED_IN, ECM_HANDOFF = 0, 1, 2, 3, 4   # edge_session.js 의 종료 값 — 닫힌 다섯
TIMEOUT_SECONDS = 180                              # ECM 넘김(열두 걸음 · 걸음마다 5 초)까지 든다


@dataclasses.dataclass(frozen=True)
class Attached:
    code: int
    file: pathlib.Path | None
    said: str

    @property
    def usable(self) -> bool:
        """손이 쓴 파일(0)이거나, Edge 에 못 붙었지만 남은 파일이 있다(2) — 서버가 받나는 부르는 쪽이 그 파일로 가린다."""
        return self.file is not None and self.code in (OK, NO_EDGE)


def hand_path() -> pathlib.Path:
    return pathlib.Path(os.environ.get(HAND_ENV, "").strip() or HAND)


def attach(apps: tuple[str, ...] = (), *, env: dict | None = None, timeout: float = TIMEOUT_SECONDS) -> Attached:
    """받는 손을 말없이 돌린다 — ``apps`` 는 꼭 서야 하는 앱(``"ecm"``), 안 주면 손의 기본(domino)이다."""
    hand = hand_path()
    if not hand.is_file():
        return Attached(TOOL, None, f"받는 손이 없다: {hand} — 스킬 ep-login 이 이 스킬 곁에 깔려야 한다(설치를 다시 돌린다)")
    node = shutil.which("node")
    if not node:
        return Attached(TOOL, None, "node 가 없다 — 설치를 다시 돌린다")
    run_env = {**os.environ, **(env or {})}
    try:
        done = subprocess.run([node, str(hand), *apps], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=run_env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return Attached(TOOL, None, f"받는 손이 {timeout:.0f} 초 안에 안 끝났다")
    except OSError as exc:
        return Attached(TOOL, None, f"받는 손을 못 띄웠다: {exc}")
    lines = [line.strip() for line in (done.stdout or "").splitlines() if line.strip()]
    last = pathlib.Path(lines[-1]) if lines else None
    file = last if last is not None and last.is_absolute() and last.is_file() else None
    said = (done.stderr or "").strip() or "\n".join(lines)
    return Attached(done.returncode, file, said)
