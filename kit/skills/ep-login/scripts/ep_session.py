"""받는 손(``edge_session.js``)을 파이썬에서 부르고, 그 손이 남긴 세션 파일을 읽는 한 자리 — 사내 앱 스킬의 얇은 명령(company-mail ·
company-calendar · company-ecm · company-meeting-room)과 그 앱 손(``inbox.py`` · ``agenda.py`` · ``ecm.py`` · ``mrs.py``)이 이 폴더를
``sys.path`` 에 넣고 싣는다. 손을 돌리고 종료 값 · 끝 줄 경로 · 손의 말을 닫힌 꼴 하나로 낸다 — 어느 종료 값에 무엇을 할지는 부르는
쪽이 제 종료 값과 메시지의 「다음」 으로 옮긴다.

**세션 파일을 쿠키 통으로 읽는 것도 여기 하나다**(``load_jar``) — 파일의 꼴(Playwright 저장 상태 ``{"cookies": [...]}``)을 아는 자리가
손과 이 파일 둘뿐이게. 어느 호스트에 어느 쿠키가 실리나는 쿠키 통이 브라우저의 규칙(도메인 · 경로 · secure)대로 가린다 — 파일에 다른
사내 호스트의 쿠키가 함께 들어도 묻는 서버에는 그 서버의 쿠키만 간다. 만료 칸이 수가 아니거나 음수면 세션 쿠키(Playwright 는 ``-1``
로 적는다)로 싣고, 지난 시각이면 버리고, 이름 · 도메인이 없는 줄은 건너뛴다.

**그 쿠키를 싣고 사내 앱을 묻는 opener 도 여기서 받는다**(``opener``) — 리다이렉트를 따라가지 않고 ``Redirected``(넘기려던 주소를
든다)로 멈춘다. 끊긴 세션은 SSO 로 넘기는데, 따라가면 세션 쿠키가 SSO 에 실린다. 부르는 쪽은 ``Redirected`` 를 제 「세션이 끊겼다」로
옮긴다. 3xx 의 ``Location`` 을 성공 신호로 읽는 앱(회의실 예약의 출입증 받기)은 이 opener 를 안 쓰고 제 처리기를 둔다.

**흔한 길에서는 손을 안 띄운다**(``session_first``) — 회사 PC 는 프로세스 하나가 수백 ms 라, 세션 파일이 이미 있으면
그것으로 먼저 돌고 서버가 거절할 때(``expired``)만 손을 띄워 새 파일로 한 번 더 돈다. 파일의 자리는 손과 같은 차례로
안다(``known_file`` — ``MAILBOX_COOKIES``, 없으면 손의 글에 적힌 ``DEFAULT_FILE``). 읽는 일만 그렇게 두 번 돌고, 서버를
바꾸는 일은 ``file_first=False`` 로 늘 손부터 받아 한 번만 돈다 — 바꾼 뒤 끊긴 세션으로 둘째 판이 돌면 「이미 그렇다」는
틀린 말이 사람에게 간다. 첫 판의 표준 출력은 담아 두었다가 선 뒤에 내보내고, ``expired`` 가 아닌 예외로 멈추면 담은 것을
먼저 내보내고 올린다 — 되풀이해 찍히지도, 멈춘 자리까지의 글이 사라지지도 않게.

어떻게 부르나::

    import ep_session

    got = ep_session.attach()                       # domino — 메일 · 일정
    got = ep_session.attach(("ecm",))                # ECM 만 — Domino 는 안 가린다
    got = ep_session.attach(("domino", "ecm"))       # 둘 다 꼭 서야 할 때
    got = ep_session.attach(env={"MAILBOX_URL": url})   # 손에 더 줄 환경변수
    if got.usable:                                   # 0 · 또는 2 인데 남은 파일이 있다 — 그 파일로 서버에 물어 본다
        session = got.file

    result = ep_session.session_first(work, expired=(SessionExpired,))   # 파일부터 · 거절되면 손을 띄워 한 번 더
    result = ep_session.session_first(work, expired=(SessionExpired,), file_first=False)   # 바꾸는 일 — 늘 손부터 · 한 번
    # 손이 못 서면 NoSession(got) — got.code 를 제 종료 값으로 옮긴다. 둘째 판의 expired 는 그대로 올라온다

    jar = ep_session.load_jar(session, missing=SessionMissing)   # 세션 파일 → 쿠키 통 · 없거나 못 읽거나 비었으면 그 앱의 예외로
    try:
        ep_session.opener(jar).open(url)                          # 쿠키 통을 싣고 · 리다이렉트는 안 따라간다(jar 없이도 된다)
    except ep_session.Redirected as exc:                          # exc.location — 넘기려던 주소
        raise SessionExpired(...) from exc

무엇을 내나 — ``Attached(code, file, said)``. ``code`` 는 손의 종료 값(``OK`` 0 · ``TOOL`` 1 · ``NO_EDGE`` 2 · ``NOT_LOGGED_IN`` 3 ·
``ECM_HANDOFF`` 4 — 그 뜻은 ``edge_session.js`` 머리말. 4 는 ``ecm`` 을 준 부름에서만 나고, 로그인은 섰으니 사람에게 다시 로그인을
청하지 말고 스킬 ep-login 을 가리킨다 — 그 입구가 탭을 잠깐 여는 갈래(``--ecm-tab``)까지 돈다), ``file`` 은 표준 출력 끝 줄의 절대 경로가 있는 파일일 때만, ``said`` 는 손의 말(표준 오류 ·
없으면 표준 출력)이다. 손 · node 가 없거나 시한을 넘기면 돌리지 않고 ``TOOL`` 과 그 까닭을 낸다 — 예외는 안 낸다.
0 인데 끝 줄이 있는 파일의 절대 경로가 아니면 ``file`` 이 None 이다 — 부르는 쪽이 도구 고장으로 읽는다.

손의 자리 — 이 파일 곁의 ``edge_session.js``. 검사가 대역을 세울 때만 환경변수 ``EP_SESSION_HAND`` 가 그 자리를 바꾼다.
"""

from __future__ import annotations

import contextlib
import dataclasses
import http.cookiejar
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

HAND = pathlib.Path(__file__).resolve().with_name("edge_session.js")
HAND_ENV = "EP_SESSION_HAND"
DEFAULT_FILE_RE = re.compile(r"DEFAULT_FILE\s*=\s*'([^']+)'")   # 손의 글에 적힌 기본 자리 — 옮겨 적지 않고 거기서 읽는다
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


def known_file() -> pathlib.Path | None:
    """받는 손을 안 띄우고 세션 파일의 자리를 낸다 — 손과 같은 차례(``MAILBOX_COOKIES`` → 손의 ``DEFAULT_FILE``). 파일이 없으면 None."""
    raw = os.environ.get("MAILBOX_COOKIES", "").strip()
    if not raw:
        try:
            found = DEFAULT_FILE_RE.search(hand_path().read_text(encoding="utf-8", errors="replace"))
        except OSError:
            found = None
        if not found:
            return None
        raw = found.group(1)
    path = pathlib.Path(os.path.expanduser(raw))
    return path if path.is_file() else None


class SessionFileError(Exception):
    """세션 파일이 없거나 · 못 읽거나 · 쿠키가 없다 — ``load_jar`` 가 ``missing`` 을 안 받았을 때 낸다."""


def _lasting_until(raw) -> float | None:
    """만료 칸을 시각으로 — 수가 아니거나(``None`` · 글자 · 참거짓) 음수면 None(세션 쿠키), 그 밖은 그 시각."""
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or raw < 0:
        return None
    return float(raw)


def load_jar(path, *, missing: type[Exception] = SessionFileError) -> http.cookiejar.CookieJar:
    """세션 파일(``{"cookies": [...]}``)을 쿠키 통으로 낸다 — 걸러 싣는 규칙은 머리말. 파일이 없거나 · JSON 으로 못 읽거나 · 실을
    쿠키가 하나도 없으면 ``missing``(부르는 앱 손의 「세션 없음」 예외)을 그 까닭과 함께 낸다. 파일을 바꾸지 않는다."""
    path = pathlib.Path(path).expanduser()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise missing(f"세션 파일이 없다: {path} — 스킬 ep-login 으로 사내 세션을 먼저 받는다") from exc
    except (OSError, ValueError) as exc:
        raise missing(f"세션 파일을 못 읽었다({type(exc).__name__}): {path} — 스킬 ep-login 으로 다시 받는다") from exc
    cookies = data.get("cookies") if isinstance(data, dict) else None
    if not isinstance(cookies, list) or not cookies:
        raise missing(f"세션 파일에 쿠키가 없다: {path} — 스킬 ep-login 으로 사내 세션을 먼저 받는다")
    jar, now = http.cookiejar.CookieJar(), time.time()
    for item in cookies:
        if not isinstance(item, dict) or not item.get("domain") or not item.get("name"):
            continue
        until = _lasting_until(item.get("expires"))
        if until is not None and until < now:
            continue
        domain = str(item["domain"])
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name=str(item["name"]), value=str(item.get("value", "")), port=None, port_specified=False,
            domain=domain, domain_specified=True, domain_initial_dot=domain.startswith("."),
            path=str(item.get("path") or "/"), path_specified=True, secure=bool(item.get("secure")),
            expires=None if until is None else int(until), discard=until is None,
            comment=None, comment_url=None, rest={}))
    return jar


class Redirected(Exception):
    """``opener`` 가 리다이렉트를 따라가지 않고 멈췄다 — ``location`` 은 넘기려던 주소."""

    def __init__(self, location: str):
        super().__init__(location)
        self.location = location


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """리다이렉트를 따라가지 않고 ``Redirected`` 를 낸다 — 까닭은 머리말."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Redirected(newurl)


def opener(jar: http.cookiejar.CookieJar | None = None) -> urllib.request.OpenerDirector:
    """``jar`` 를 싣고(주면) 리다이렉트는 안 따라가는 opener — 3xx 를 만나면 ``Redirected``."""
    handlers = [urllib.request.HTTPCookieProcessor(jar)] if jar is not None else []
    return urllib.request.build_opener(*handlers, NoRedirect())


class NoSession(Exception):
    """손을 띄웠는데 못 섰다 — ``got`` 이 손의 종료 값 · 말을 든다. 부르는 쪽이 제 종료 값으로 옮긴다."""

    def __init__(self, got: "Attached"):
        super().__init__(got.said)
        self.got = got


def _held(use, file, expired):
    """``use(file)`` 을 돌리되 표준 출력을 담는다 — 선 뒤에 내보내고, ``expired`` 면 버리고(둘째 판이 다시 찍는다), 그 밖의
    예외로 멈추면 멈춘 자리까지의 글을 먼저 내보내고 올린다."""
    held = io.StringIO()
    try:
        with contextlib.redirect_stdout(held):
            result = use(file)
    except expired:
        raise
    except BaseException:
        sys.stdout.write(held.getvalue())
        raise
    sys.stdout.write(held.getvalue())
    return result


def session_first(use, apps: tuple[str, ...] = (), *, expired=(), env: dict | None = None,
                  timeout: float = TIMEOUT_SECONDS, file_first: bool = True):
    """흔한 길에서 손을 안 띄운다 — 있는 세션 파일로 ``use(file)`` 을 먼저 돌리고, 그것이 ``expired`` 를 내거나 파일이 없을
    때만 손을 띄워 새 파일로 한 번 더 돈다(``file_first=False`` 면 늘 손부터 받아 한 번만). 손이 못 서면 ``NoSession``. 손이
    같은 낡은 파일만 가리키면(Edge 에 못 붙어 안 고쳤다) 둘째 판 없이 첫 판의 ``expired`` 를 올린다. 둘째 판의 ``expired`` 도
    그대로 올라간다. 표준 출력은 ``_held`` 가 든다."""
    file = known_file() if file_first else None
    stale = None
    if file is not None:
        try:
            return _held(use, file, expired)
        except expired as exc:
            stale = exc                              # 파일이 낡았다 — 손을 띄워 새로 받아 한 번 더
    got = attach(apps, env=env, timeout=timeout)
    if not got.usable:
        raise NoSession(got)
    if stale is not None and got.code == NO_EDGE and got.file == file:
        raise stale                                  # 손이 못 붙어 같은 파일만 가리킨다 — 또 거절될 판을 안 돈다
    return _held(use, got.file, expired)


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
