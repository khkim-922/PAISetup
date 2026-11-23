"""스킬 company-ecm 의 얇은 명령 — 스킬 ep-login 의 붙는 손으로 사내 세션을 맞춘 뒤, 곁의 ECM 손(``ecm.py``)을 그대로 부른다.

부르는 꼴::

    python -X utf8 <이 스킬>/scripts/company_ecm.py <명령> [인자…]   # 명령 · 인자는 곁의 ecm.py 의 것 그대로(--help)

인자는 세션보다 먼저 ``ecm.py`` 의 명령줄과 값 가리기(``ecm.checked_args`` — 열쇠의 꼴 · 파일 · 짝처럼 서버 없이 가릴 수 있는
값)로 한 번만 가린다 — ``--help`` · 틀린 인자 · 틀린 값은 세션 없이 그 자리에서 끝난다(종료 값은 ``ecm.report``). 가린 인자는
``ecm.run`` 이 받는다.
세션이 드는 명령 가운데 읽는 것은 세션 파일이 이미 있으면 그것으로 먼저 돌고 ECM 이 끊겼다고 할 때만, 잠그거나 올리거나 권한을
바꾸는 것은 늘, 형제 스킬 ep-login 의 받는 손을 ``ecm`` 으로 말없이 돌린다(까닭과 바퀴는 그 폴더 ``ep_session.session_first`` 의
머리말). 어느 명령이 세션이 들고 바꾸는가는 ``ecm.py`` 의 손가락 표(``FINGERS`` 의 ``session`` · ``mutating``)가 든다. 쓰는 사람의
Edge 가 디버깅 포트로 떠 있고 로그인돼 있으면 그 손이 ECM 쿠키를 세션 파일에 맞추고(``ecm`` 만 재므로 메일 쪽 Domino 세션은 안
본다), 끝 줄에 그 파일의 절대 경로를 낸다 — 그 경로를 ``ecm.py`` 에 ``--session`` 으로 넘긴다. 세션 파일의 기본 자리는 받는 손만 든다.

내는 것: 종료 값은 ``ecm.py`` 의 것 그대로다(뜻은 그 머리말 「무엇을 내나」) — 붙는 손이 못 서면 그 표의 ``EXIT_SESSION`` ·
``EXIT_FAIL`` 로 옮긴다. 붙는 손의 종료 값은 이렇게 읽는다:

    0  붙었다 → 끝 줄의 경로로 ``ecm.py`` 를 부른다
    1  붙는 손이 고장 났다 → 그 손의 말 그대로 알리고 멈춘다(종료 1)
    2  Edge 에 못 붙었다 → 끝 줄에 남아 있는 세션 파일의 경로가 있으면 그것으로 ``ecm.py`` 를 불러 본다(ECM 세션이 아직 살았으면
       사람 손이 안 든다). 경로가 없으면 스킬 ep-login 을 가리킨다(종료 3)
    3  Edge 에서 EP 로그인이 안 됐거나 끊겼다 → 스킬 ep-login 을 가리킨다(종료 3) — 그 스킬이 로그인을 이끈다
    4  EP 로그인은 섰는데 받는 손이 ECM 의 SSO 넘김을 화면 없이 못 따라갔다 → 다시 로그인을 청하지 않고 스킬 ep-login 의
       입구를 가리킨다 — 그 입구가 탭을 잠깐 여는 갈래까지 돈다(종료 3)

``ecm.py`` 가 세션이 끊겼다고 하면(ECM 의 ``302 → /ECM/logout.jsp``) 스킬 ep-login 을 가리킨다.

환경변수 — ``ecm.py`` 가 읽는 것(``ECM_URL`` · ``ECM_AGENT_URL`` …)은 그 머리말이, 받는 손의 대역(``EP_SESSION_HAND``)은 ``ep_session.py`` 가 든다
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다


class SessionGone(Exception):
    """ecm.py 가 EXIT_SESSION 으로 끝났다 — session_first 의 expired 로 옮기는 신호. 메시지는 그 판의 ecm.py 가 표준 오류에 내려던 말이다."""


NO_EDGE_WORD = "쓰는 사람의 Edge 에 못 붙었다(디버깅 포트로 떠 있지 않다)"
NOT_LOGGED_IN_WORD = "Edge 는 떠 있는데 EP 로그인이 안 됐거나 끊겼다"
ECM_HANDOFF_WORD = "EP 로그인은 섰는데 받는 손이 ECM 넘김을 화면 없이 못 따라갔다 — 다시 로그인할 일은 아니다"
EP_LOGIN = "스킬 ep-login 으로 사내 세션을 받은 뒤 같은 명령을 다시 돌린다"
NO_EP_LOGIN_WORD = f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"
SESSION_REFUSED_WORD = f"ECM 이 세션을 안 받았다 — {EP_LOGIN}"
NO_ORDINARY_WORD = ("이 로그온에 평소 Edge 의 EP 로그인이 없다 — 이 PC 의 문서함 에이전트는 그 로그인이 있어야 문서를 연다. 다음: 스킬 ep-login 의 "
                    "입구를 ecm 으로 부른 뒤(login.sh ecm — 사용자의 평소 Edge 에서 EP 로그인이 선다) 같은 명령을 다시 돌린다")
ORDINARY_UNSURE_WORD = "이 로그온의 평소 EP 로그인이 섰는지는 모른다 — 문서가 안 열리면 사용자가 평소 Edge 에서 EP 에 로그인한 뒤 같은 명령을 다시 돌린다"
EP_LOGIN_ECM_ONLY = "다시 로그인할 일은 아니다 — 스킬 ep-login 으로 ECM 세션을 받은 뒤(탭 하나가 잠깐 열린다) 같은 명령을 다시 돌린다"


def load_ep_session():
    """형제 스킬 ep-login 의 ``ep_session`` 을 싣는다 — 받는 손을 돌리는 한 자리다. 없으면 None."""
    if str(EP_LOGIN_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(EP_LOGIN_SCRIPTS))
    try:
        return importlib.import_module("ep_session")
    except ImportError:
        return None


def main(argv: list[str]) -> int:
    """명령 한 판 — 인자를 한 번 가리고, 세션이 드는 줄이면 받는 손의 바퀴(``session_first``)로 세션을 맞춰 ``ecm.run`` 을 돈다."""
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))   # -I 로 돌면 이 폴더가 sys.path 에 없다
    ecm = importlib.import_module("ecm")
    try:
        args = ecm.checked_args(argv)      # --help · 틀린 인자 · 서버 없이 가릴 수 있는 틀린 값은 세션 없이 여기서 끝난다
    except ecm.REPORTED as exc:
        return ecm.report(exc)
    finger = ecm.FINGERS[args.command]
    if finger.session:
        ep = load_ep_session()
        if ep is None:
            print(NO_EP_LOGIN_WORD, file=sys.stderr)
            return ecm.EXIT_FAIL
        if ecm.uses_agent(finger, args) and not ordinary_ready(ep):
            print(NO_ORDINARY_WORD, file=sys.stderr)
            return ecm.EXIT_SESSION

        def use(file):
            # ecm.py 는 까닭을 표준 오류에 낸다 — session_first 는 표준 출력만 담으므로 여기서 담는다. 안 담으면 낡은 세션 파일로 돈 첫 판의
            # 「세션이 끊겼다 · ep-login」 말이 다시 받아 선 판의 답 곁에 남아, 선 명령을 끊긴 것으로 읽게 한다
            said = io.StringIO()
            try:
                with contextlib.redirect_stderr(said):
                    result = ecm.run(argparse.Namespace(**{**vars(args), "session": args.session or str(file)}))   # 준 --session 이 이긴다
            except BaseException:
                sys.stderr.write(said.getvalue())
                raise
            if result == ecm.EXIT_SESSION:
                raise SessionGone(said.getvalue().strip())
            sys.stderr.write(said.getvalue())
            return result

        try:
            return ep.session_first(use, ("ecm",), expired=(SessionGone,), file_first=not finger.mutating)
        except ep.NoSession as exc:
            return tell_no_session(ep, ecm, exc.got)
        except SessionGone as exc:
            if str(exc):
                print(exc, file=sys.stderr)
            print(SESSION_REFUSED_WORD, file=sys.stderr)
            return ecm.EXIT_SESSION
    return ecm.run(args)


def ordinary_ready(ep) -> bool:
    """이 로그온에 평소 EP 로그인이 있다고 볼 수 있나 — 형제 스킬 ep-login 의 읽기만 하는 답(``ep_session.ordinary_login``)을 받는다.
    섰다 → 참. 없다 → 거짓(문서함 에이전트를 부르기 전에 멈춘다). 해 봤다 · 가릴 수 없다(못 읽고 로그온 열쇠도 없다) · 못 가렸다 → 참이되 사람이 할 일을 한 줄 말한다 — 끝없이
    「입구부터」를 안 내게. 이 명령은 입구를 대신 부르지 않는다(하위 에이전트 안에서도 창을 안 띄운다)."""
    state = ep.ordinary_login()
    if state == ep.ORDINARY_MISSING:
        return False
    if state != ep.ORDINARY_STOOD:
        print(ORDINARY_UNSURE_WORD, file=sys.stderr)
    return True


def tell_no_session(ep, ecm, got) -> int:
    """받는 손이 세션을 못 세운 갈래(``got.code``)를 사람에게 할 말과 종료 값으로 옮긴다 — 로그인 끊김 · Edge 없음 · ECM 넘김은
    ``EXIT_SESSION``, 받는 손의 고장은 ``EXIT_FAIL``."""
    if got.code == ep.ECM_HANDOFF:
        print(f"{ECM_HANDOFF_WORD} — {EP_LOGIN_ECM_ONLY}", file=sys.stderr)
        return ecm.EXIT_SESSION
    if got.code in (ep.NOT_LOGGED_IN, ep.NO_EDGE):
        print(f"{NOT_LOGGED_IN_WORD if got.code == ep.NOT_LOGGED_IN else NO_EDGE_WORD} — {EP_LOGIN}", file=sys.stderr)
        return ecm.EXIT_SESSION
    why = f"받는 손이 실패했다(종료 {got.code})" if got.code != ep.OK else "받는 손이 세션 파일 경로를 끝 줄에 안 냈다"
    print(f"{why}: {got.said or '말 없음'}", file=sys.stderr)
    return ecm.EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
