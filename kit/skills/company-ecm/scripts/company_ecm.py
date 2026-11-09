"""스킬 company-ecm 의 얇은 명령 — 스킬 ep-login 의 붙는 손으로 사내 세션을 맞춘 뒤, 곁의 ECM 손(``ecm.py``)을 그대로 부른다.

부르는 꼴::

    python -X utf8 <이 스킬>/scripts/company_ecm.py <명령> [인자…]   # 명령 · 인자는 곁의 ecm.py 의 것 그대로(--help)

세션이 드는 명령(``NEEDS_SESSION``) 가운데 읽는 것은
세션 파일이 이미 있으면 그것으로 먼저 돌고 ECM 이 끊겼다고 할 때만, 잠그거나 올리거나 권한을 바꾸는 것(``MUTATING``)은 늘, 형제 스킬
ep-login 의 받는 손을 ``ecm`` 으로 말없이 돌린다(까닭과 바퀴는 그 폴더 ``ep_session.session_first`` 의 머리말). 쓰는 사람의 Edge 가 디버깅 포트로 떠 있고 로그인돼 있으면 그 손이 ECM 쿠키를
세션 파일에 맞추고(``ecm`` 만 재므로 메일 쪽 Domino 세션은 안 본다), 끝 줄에 그 파일의 절대 경로를 낸다 — 그 경로를 ``ecm.py`` 에 ``--session`` 으로 넘긴다. 세션 파일의 기본 자리는 받는 손만 든다.

내는 것: 종료 값은 ``ecm.py`` 의 것과 같다 — 0 됨 · 1 실패 · 2 인자가 틀렸다 · 3 사내 세션을 다시 받아야 한다(스킬 ep-login) · 4 기본
앱을 사람이 한 번 골라야 한다. 붙는 손의 종료 값은 이렇게 읽는다:

    0  붙었다 → 끝 줄의 경로로 ``ecm.py`` 를 부른다
    1  붙는 손이 고장 났다 → 그 손의 말 그대로 알리고 멈춘다(종료 1)
    2  Edge 에 못 붙었다 → 끝 줄에 남아 있는 세션 파일의 경로가 있으면 그것으로 ``ecm.py`` 를 불러 본다(ECM 세션이 아직 살았으면
       사람 손이 안 든다). 경로가 없으면 스킬 ep-login 을 가리킨다(종료 3)
    3  Edge 에서 EP 로그인이 안 됐거나 끊겼다 → 스킬 ep-login 을 가리킨다(종료 3) — 그 스킬이 로그인을 이끈다
    4  EP 로그인은 섰는데 받는 손이 ECM 의 SSO 넘김을 화면 없이 못 따라갔다 → 다시 로그인을 청하지 않고 스킬 ep-login 의
       탭을 잠깐 여는 갈래(``--ecm-tab``)를 가리킨다(종료 3)

``ecm.py`` 가 세션이 끊겼다고 하면(ECM 의 ``302 → /ECM/logout.jsp``) 스킬 ep-login 을 가리킨다.

환경변수 — ``ecm.py`` 가 읽는 것(``ECM_URL`` · ``ECM_AGENT_URL`` …)은 그 머리말이, 받는 손의 대역(``EP_SESSION_HAND``)은 ``ep_session.py`` 가 든다
"""

from __future__ import annotations

import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
NEEDS_SESSION = ("session", "cabinets", "folders", "list", "count", "version", "open", "read", "edit", "checkin", "register",
                 "access", "who", "preview-access", "apply-access")
MUTATING = ("edit", "checkin", "register", "apply-access")   # 서버를 잠그거나 판 · 권한을 바꾼다 — 세션 손부터 받아 한 번만 돈다


class SessionGone(Exception):
    """ecm.py 가 EXIT_SESSION 으로 끝났다 — session_first 의 expired 로 옮기는 신호."""
NO_EDGE_WORD = "쓰는 사람의 Edge 에 못 붙었다(디버깅 포트로 떠 있지 않다)"
NOT_LOGGED_IN_WORD = "Edge 는 떠 있는데 EP 로그인이 안 됐거나 끊겼다"
ECM_HANDOFF_WORD = "EP 로그인은 섰는데 받는 손이 ECM 넘김을 화면 없이 못 따라갔다 — 다시 로그인할 일은 아니다"
EP_LOGIN = "스킬 ep-login 으로 사내 세션을 받은 뒤 같은 명령을 다시 돌린다"
EP_LOGIN_ECM_ONLY = "스킬 ep-login 의 탭을 잠깐 여는 갈래(--ecm-tab)로 ECM 세션을 받은 뒤 같은 명령을 다시 돌린다"


def load_ep_session():
    """형제 스킬 ep-login 의 ``ep_session`` 을 싣는다 — 받는 손을 돌리는 한 자리다. 없으면 None."""
    if str(EP_LOGIN_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(EP_LOGIN_SCRIPTS))
    try:
        return importlib.import_module("ep_session")
    except ImportError:
        return None


def main(argv: list[str]) -> int:
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))   # -I 로 돌면 이 폴더가 sys.path 에 없다
    ecm = importlib.import_module("ecm")
    if argv and argv[0] in NEEDS_SESSION:
        ep = load_ep_session()
        if ep is None:
            print(f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다", file=sys.stderr)
            return ecm.EXIT_FAIL

        def use(file):
            result = ecm.main(["--session", str(file), *argv])
            if result == ecm.EXIT_SESSION:
                raise SessionGone()
            return result

        # 읽는 명령은 세션 파일부터 · ECM 이 끊겼다고 하면 손을 띄워 한 번 더. 잠그거나 올리는 명령(MUTATING)은 늘 손부터 · 한 번
        try:
            return ep.session_first(use, ("ecm",), expired=(SessionGone,), file_first=argv[0] not in MUTATING)
        except ep.NoSession as exc:
            got = exc.got
            if got.code == ep.ECM_HANDOFF:
                print(f"{ECM_HANDOFF_WORD} — {EP_LOGIN_ECM_ONLY}", file=sys.stderr)
                return ecm.EXIT_SESSION
            if got.code in (ep.NOT_LOGGED_IN, ep.NO_EDGE):
                print(f"{NOT_LOGGED_IN_WORD if got.code == ep.NOT_LOGGED_IN else NO_EDGE_WORD} — {EP_LOGIN}", file=sys.stderr)
                return ecm.EXIT_SESSION
            why = f"받는 손이 실패했다(종료 {got.code})" if got.code != ep.OK else "받는 손이 세션 파일 경로를 끝 줄에 안 냈다"
            print(f"{why}: {got.said or '말 없음'}", file=sys.stderr)
            return ecm.EXIT_FAIL
        except SessionGone:
            print(f"ECM 이 세션을 안 받았다 — {EP_LOGIN}", file=sys.stderr)
            return ecm.EXIT_SESSION
    return ecm.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
