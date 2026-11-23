"""명령을 멈추는 꼴 — 종료 값과 사람에게 낼 말이고, 0 이 아닌 끝은 늘 다음 걸음을 든다.

부르는 꼴::

    from mail_stop import Stop
    raise Stop(EXIT_ARGS, "그런 폴더가 없다: …")      # 부르는 명령의 입구가 받아 stop.said() 를 내고 stop.code 로 끝난다

이 스킬의 명령(``mail.py``)과 형제 스킬 company-directory 의 명령이 한 꼴을 쓴다 — 메일 손이 내준 조각(``mail_open`` · ``mail_kept``)이
멈추면 어느 명령의 입구든 같은 꼴로 받는다. 종료 값은 사내 앱 명령의 한 표(형제 스킬 ep-login 의 ``ep_command``)가 든다.
"""

from __future__ import annotations

import pathlib
import sys

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
import ep_command  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다

SESSION_CUT_FACT = "메일함 세션이 끊겼다"                  # 메일함이 세션을 거절한 판의 사실 — 걸음(ep-login)은 종료 값 3 의 걸음이 붙인다
SESSION_CUT = SESSION_CUT_FACT + "."
SESSION_CUT_WHY = SESSION_CUT_FACT + "({why})."            # 같은 사실에 메일함 손이 댄 까닭을 붙인 꼴
# 제 걸음을 안 댄 멈춤에 붙는 걸음 — 종료 값마다 하나. 멈추는 자리가 제 걸음을 대면(``stepped``) 그 말이 앞선다(``Stop.said``)
NEXT_WORDS = {
    ep_command.EXIT_TOOL: "다음: 이 말을 그대로 사람에게 알린다 — 같은 명령을 되풀이하지 않는다. 웹메일 화면에서 할 일이면 사람이 웹메일에서 한다",
    ep_command.EXIT_ARGS: "다음: 위 말이 짚은 값을 고쳐 다시 부른다 — 같은 인자로 되풀이하지 않는다(인자의 꼴은 <명령> --help)",
    ep_command.EXIT_SESSION: ep_command.NEXT_EP_LOGIN,
    ep_command.EXIT_STALE: "다음: 미리 보기(preview-…)를 다시 불러 지금 판을 사람에게 보이고 확인받는다",
}


class Stop(Exception):
    """명령을 멈춘다 — ``code`` 가 종료 값, 메시지가 사람에게 낼 글이다. ``stepped`` 는 그 글이 제 다음 걸음을 드나다 — 글을 지은 자리가
    안다. 참이면 글 그대로, 거짓이면 종료 값의 걸음(``NEXT_WORDS``)을 붙인다. 남의 멈춤(형제 스킬 ep-login 의 ``ep_command.Stop``)을
    다시 싣는 자리는 그 멈춤의 ``stepped`` 를 그대로 옮긴다 — 글을 뒤져 걸음을 가리지 않는다."""

    def __init__(self, code: int, message: str, *, stepped: bool = False):
        super().__init__(message)
        self.code = code
        self.stepped = stepped

    def said(self) -> str:
        """사람에게 낼 글 — 제 걸음을 안 들었으면 종료 값의 걸음을 붙인다. 0 이 아닌 끝은 늘 다음 걸음을 한 번 든다."""
        text = str(self)
        step = NEXT_WORDS.get(self.code)
        return text if self.stepped or not step else f"{text}\n{step}"


def from_ep(exc) -> Stop:
    """형제 스킬 ep-login 의 멈춤(``ep_command.Stop``)을 이 명령의 멈춤으로 — 종료 값 · 글 · 제 걸음을 들었나(``stepped``) 그대로다."""
    return Stop(exc.code, str(exc), stepped=exc.stepped)
