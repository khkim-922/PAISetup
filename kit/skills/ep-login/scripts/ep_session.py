"""받는 손(``edge_session.js``)을 파이썬에서 부르고 그 손이 남긴 세션 파일을 읽는 한 자리 — 사내 앱 스킬의 얇은 명령과 앱
손이 이 폴더를 ``sys.path`` 에 넣고 싣는다. 손 돌리기(``attach`` · ``session_first``) · 세션 파일 → 쿠키 통(``load_jar``) · 프록시
없이 리다이렉트를 안 따르는 ``opener`` · SSO 넘김 화면의 숨은 칸(``sso_form``) · 이름 견주기 꼴(``squash``) · node 손 돌리기
(``run_hand``) · 이 로그온에 평소 EP 로그인이 섰나(``ordinary_login`` — 아무것도 안 연다) · 회사 자리 값(``places.json`` → ``DEFAULT_FILE`` · ``DOMINO_SERVER`` · ``ECM_URL`` · ``ECM_MAIN_PAGE``) · 대화에 내는
답 하나의 크기(``OUT_BYTES``)를 든다. 얇은 명령의 뼈대는 곁의 ``ep_command.py`` 가 든다. 파일부터 도는 바퀴 · 리다이렉트를 안
따르는 까닭 · 쿠키 통이 무엇을 싣나는 ``references/DESIGN.md`` 가 든다.

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
        ep_session.opener(jar).open(url)                          # 쿠키 통을 싣고 · 프록시 없이 · 리다이렉트는 안 따라간다(jar 없이도 된다)
    except ep_session.Redirected as exc:                          # exc.location — 넘기려던 주소
        raise SessionExpired(...) from exc
    form = ep_session.sso_form(page)                              # SSO 넘김 화면의 숨은 칸 → {name: value}

    ep_session.squash("안전 · 환경(포항)")                         # → "안전환경포항" — 이름 · 낱말을 견줄 때 양쪽에 댄다
    try:
        ran = ep_session.run_hand(script, ["save", ...], env={...}, timeout=초)   # node 손 한 판 — ran.code · ran.answer · ran.said
    except ep_session.NoNode: ...                                 # node 가 없다
    except ep_session.TimedOut: ...                               # 시한을 넘겼다 — 어느 종료 값 · 말로 옮길지는 부르는 쪽이 든다

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
import html
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
# 회사 자리 값 — 받는 손(edge_session.js)과 같은 파일을 읽는다. 형제 스킬의 파이썬 손은 아래 이름으로 받는다
PLACES_FILE = "places.json"
PLACES = json.loads(pathlib.Path(__file__).resolve().with_name(PLACES_FILE).read_text(encoding="utf-8"))
DEFAULT_FILE = PLACES["session_file"]              # 세션 파일의 기본 자리(``~`` 로 연다)
DOMINO_SERVER = PLACES["domino_server"]            # 메일(Domino) 서버
ECM_URL = PLACES["ecm"]                            # ECM 주소 — 맥락(``…/ECM``)까지
ECM_MAIN_PAGE = PLACES["ecm_main_page"]            # ECM 메인 화면 — ``ECM_URL`` 뒤에 붙는 자리
OK, TOOL, NO_EDGE, NOT_LOGGED_IN, ECM_HANDOFF = 0, 1, 2, 3, 4   # edge_session.js 의 종료 값 — 닫힌 다섯
TIMEOUT_SECONDS = 180                              # ECM 넘김(열두 걸음 · 걸음마다 5 초)까지 든다
# 사내 앱 스킬의 얇은 명령이 대화에 내는 답 하나의 크기(바이트) — 대화 도구가 긴 출력을 잘라 싣는 한도 아래에 둔다. 넘친 답은
# 종료 0 이라 아무도 모른다(한도와 까닭은 references/DESIGN.md 「답 하나의 크기」)
OUT_BYTES = 24000
SQUASHED = re.compile(r"[\s·ㆍ()\[\]]+")            # 이름을 견줄 때 안 보는 글자 — 빈칸 · 가운뎃점(두 꼴) · 둥근 괄호 · 대괄호
INPUT_TAG = re.compile(r"<input[^>]*>", re.IGNORECASE)
INPUT_NAME = re.compile(r'name\s*=\s*["\']([^"\']+)', re.IGNORECASE)
INPUT_VALUE = re.compile(r'value\s*=\s*["\']([^"\']*)', re.IGNORECASE)
SAID_TAIL = 300                                    # 손이 답 없이 졌을 때 표준 오류에서 읽는 끝 글자 수 — 사람에게 전할 한두 줄


@dataclasses.dataclass(frozen=True)
class Attached:
    """받는 손을 한 번 돌린 결과 — 손의 종료 값(code) · 손이 쓴 세션 파일(file · 없으면 None) · 손의 말(said)."""
    code: int
    file: pathlib.Path | None
    said: str

    @property
    def usable(self) -> bool:
        """손이 쓴 파일(0)이거나, Edge 에 못 붙었지만 남은 파일이 있다(2) — 서버가 받나는 부르는 쪽이 그 파일로 가린다."""
        return self.file is not None and self.code in (OK, NO_EDGE)


def hand_path() -> pathlib.Path:
    """받는 손(``edge_session.js``)의 자리 — ``EP_SESSION_HAND`` 이 있으면 그 값, 없으면 이 파일 곁."""
    return pathlib.Path(os.environ.get(HAND_ENV, "").strip() or HAND)


def session_path() -> pathlib.Path | None:
    """받는 손이 쓰는 세션 파일의 자리 — 손과 같은 차례(``MAILBOX_COOKIES`` → 손 곁 ``places.json`` 의 기본 자리). 파일이 있는지는
    안 본다. 손 곁에 그 값이 없으면(검사의 대역 손) None."""
    raw = os.environ.get("MAILBOX_COOKIES", "").strip()
    if not raw:
        try:
            raw = json.loads(hand_path().with_name(PLACES_FILE).read_text(encoding="utf-8")).get("session_file") or ""
        except (OSError, ValueError, AttributeError):
            raw = ""
        if not raw:
            return None
    return pathlib.Path(os.path.expanduser(raw))


def known_file() -> pathlib.Path | None:
    """받는 손을 안 띄우고 세션 파일을 낸다 — ``session_path`` 의 자리에 파일이 있을 때만, 없으면 None."""
    path = session_path()
    return path if path is not None and path.is_file() else None


class SessionFileError(Exception):
    """세션 파일이 없거나 · 못 읽거나 · 쿠키가 없다 — ``load_jar`` 가 ``missing`` 을 안 받았을 때 낸다."""


def _lasting_until(raw) -> float | None:
    """만료 칸을 시각으로 — 수가 아니거나(``None`` · 글자 · 참거짓) 음수면 None(세션 쿠키), 그 밖은 그 시각."""
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or raw < 0:
        return None
    return float(raw)


def load_jar(path, *, missing: type[Exception] = SessionFileError) -> http.cookiejar.CookieJar:
    """세션 파일(``{"cookies": [...]}``)을 쿠키 통으로 낸다. 파일이 없거나 · JSON 으로 못 읽거나 · 실을
    쿠키가 하나도 없으면 ``missing``(부르는 앱 손의 「세션 없음」 예외)을 그 까닭과 함께 낸다. 파일을 바꾸지 않는다. 만료 칸이 수가
    아니거나 음수면 세션 쿠키로 싣고, 지난 시각이면 버리고, 이름 · 도메인이 없는 줄은 건너뛴다."""
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
    """리다이렉트를 따라가지 않고 ``Redirected`` 를 낸다 — 따라가면 세션 쿠키가 SSO 에 실린다."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """넘김을 따라가지 않는다 — 넘기려던 주소를 들고 ``Redirected`` 를 낸다."""
        raise Redirected(newurl)


def opener(jar: http.cookiejar.CookieJar | None = None) -> urllib.request.OpenerDirector:
    """``jar`` 를 싣고(주면) 프록시 없이 묻고 리다이렉트는 안 따라가는 opener — 3xx 를 만나면 ``Redirected``. 3xx 의 ``Location``
    을 성공 신호로 읽는 앱은 이 opener 대신 제 처리기를 둔다."""
    handlers = [urllib.request.HTTPCookieProcessor(jar)] if jar is not None else []
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), *handlers, NoRedirect())


def sso_form(page: str) -> dict:
    """SSO 넘김 화면의 ``<input>`` 칸 → ``{name: value}`` — name · value 의 차례와 따옴표 꼴(겹 · 홑)을 안 가리고, 값의 HTML
    엔티티는 푼다(브라우저가 폼을 낼 때와 같은 글자). value 없는 칸은 빈 글자, name 없는 칸은 버린다. 세션이 끊긴 화면은 토큰
    칸(``ssoToken``)이 없거나 비었다 — 그 판정은 부르는 앱 손이 한다."""
    out = {}
    for tag in INPUT_TAG.findall(page):
        name, value = INPUT_NAME.search(tag), INPUT_VALUE.search(tag)
        if name:
            out[name.group(1)] = html.unescape(value.group(1)) if value else ""
    return out


def squash(text: str | None) -> str:
    """견주기 꼴 — 빈칸 · 가운뎃점 · 괄호를 빼고 대소문자를 접는다(「안전 · 환경」 = 「안전환경」 · 「(포항)화성」 = 「포항화성」 ·
    「[공지] 식단」 = 「공지식단」). None 은 빈 글자다. 견주는 양쪽에 같이 댄다."""
    return SQUASHED.sub("", text or "").casefold()


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


class NoNode(Exception):
    """node 가 PATH 에 없어 손을 못 돌렸다."""


class TimedOut(Exception):
    """손이 시한 안에 안 끝났다 — 손은 거뒀다. 그 사이 손이 한 일이 섰는지는 모른다."""


@dataclasses.dataclass(frozen=True)
class Ran:
    """node 손 한 판의 끝 — ``code`` 손의 종료 값 · ``answer`` 끝 줄의 답 · ``said`` 손이 댄 까닭(없으면 빈 글자)."""
    code: int
    answer: dict
    said: str


def _node(script, args, env: dict | None, timeout: float) -> subprocess.CompletedProcess:
    """node 로 ``script`` 를 돌려 끝난 판을 낸다 — 출력은 UTF-8 로 읽고 못 읽는 바이트는 바꿔 읽는다(손의 글 한 조각 때문에 판
    전체를 잃지 않게). ``env`` 는 이 프로세스의 환경에 더할 변수다. node 가 없으면 ``NoNode``, 시한을 넘기면 ``TimedOut``, 그 밖에
    못 띄운 까닭은 ``OSError`` 그대로 올린다."""
    node = shutil.which("node")
    if not node:
        raise NoNode()
    try:
        return subprocess.run([node, str(script), *args], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env={**os.environ, **(env or {})}, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise TimedOut(f"{timeout:.0f} 초") from exc


def run_hand(script, args=(), *, env: dict | None = None, timeout: float) -> Ran:
    """화면을 다루는 node 손(임시저장 · 보내기 · 창 띄우기) 한 판 — 손은 표준 출력의 끝 줄(빈 줄 아닌)에 답을 JSON 객체 하나로
    낸다. ``answer`` 는 그 답이다 — 줄이 없으면 ``{}``, 끝 줄이 JSON 객체가 아니면 ``{"error": 그 줄}``. ``said`` 는 손이 댄 까닭 —
    답의 ``error``, 없으면 표준 오류의 끝 SAID_TAIL 자다. 손의 자리 · 시한 · 종료 값을 무엇으로 옮기나 · 까닭 없이 진 판에 할 말은
    부르는 쪽이 든다(손마다 다르다). ``NoNode`` · ``TimedOut`` 은 ``_node`` 그대로 올라간다."""
    done = _node(script, args, env, timeout)
    lines = [line for line in (done.stdout or "").splitlines() if line.strip()]
    try:
        answer = json.loads(lines[-1]) if lines else {}
    except ValueError:
        answer = None
    if not isinstance(answer, dict):
        answer = {"error": lines[-1]}
    return Ran(done.returncode, answer, str(answer.get("error") or (done.stderr or "").strip()[-SAID_TAIL:]))


def attach(apps: tuple[str, ...] = (), *, env: dict | None = None, timeout: float = TIMEOUT_SECONDS) -> Attached:
    """받는 손을 말없이 돌린다 — ``apps`` 는 꼭 서야 하는 앱(``"ecm"``), 안 주면 손의 기본(domino)이다."""
    hand = hand_path()
    if not hand.is_file():
        return Attached(TOOL, None, f"받는 손이 없다: {hand} — 스킬 ep-login 이 이 스킬 곁에 깔려야 한다(설치를 다시 돌린다)")
    try:
        done = _node(hand, apps, env, timeout)
    except NoNode:
        return Attached(TOOL, None, "node 가 없다 — 설치를 다시 돌린다")
    except TimedOut:
        return Attached(TOOL, None, f"받는 손이 {timeout:.0f} 초 안에 안 끝났다")
    except OSError as exc:
        return Attached(TOOL, None, f"받는 손을 못 띄웠다: {exc}")
    lines = [line.strip() for line in (done.stdout or "").splitlines() if line.strip()]
    last = pathlib.Path(lines[-1]) if lines else None
    file = last if last is not None and last.is_absolute() and last.is_file() else None
    said = (done.stderr or "").strip() or "\n".join(lines)
    return Attached(done.returncode, file, said)


# ── 평소 EP 로그인 — 빌려 주는 답 ────────────────────────────────────────────
STATUS = pathlib.Path(__file__).resolve().with_name("ordinary_status.js")
STATUS_ENV = "EP_ORDINARY_STATUS"                  # 그 답의 문을 바꾼다 — 검사가 대역을 둔다
ORDINARY_STOOD, ORDINARY_TRIED, ORDINARY_MISSING = "stood", "tried", "missing"   # ordinary_status.js 가 내는 낱말 — 닫힌 셋
ORDINARY_UNSURE = "unsure"                         # 평소 Edge 를 못 읽고 로그온 열쇠도 없다 — 가릴 수 없다. 부르는 쪽은 「해 봤다」처럼 잇는다
ORDINARY_UNKNOWN = "unknown"                       # 그 문이 답을 못 냈다(node 없음 · 시한 · 낯선 낱말) — 부르는 쪽은 「해 봤다」처럼 잇는다
EYE_START_S, EYE_LOOK_S = PLACES["eye_start_s"], PLACES["eye_look_s"]   # 평소 Edge 를 보는 눈의 두 시한(ordinary_logon.js 가 같은 값을 쓴다) — 뜨기 · 보기 하나
# 그 문의 시한 — 뜨기 셋(node · 로그온 열쇠를 묻는 PowerShell · 눈)을 다 덮어 느리게 뜬 멀쩡한 눈을 먼저 끊지 않고, 뜬 뒤의 물음들(열쇠의
# 물음 하나 · 한 번 읽기의 보기 몇 번)에는 보기 시한 다섯 몫을 준다. 뜬 뒤가 그보다 길면 눈이 보다 멈춘 것이라 「못 가렸다」가 맞다
STATUS_TIMEOUT_SECONDS = 3 * EYE_START_S + 5 * EYE_LOOK_S


def ordinary_login(*, env: dict | None = None, timeout: float = STATUS_TIMEOUT_SECONDS) -> str:
    """이 윈도 로그온에 평소 EP 로그인이 한 번 섰나 — 아무것도 안 열고 안 쓴다(입구의 「섰다」 기록을 먼저 읽고, 기록이 없을 때만 눈으로
    평소 Edge 를 본다). 내는 것: ``ORDINARY_STOOD`` · ``ORDINARY_TRIED``(해 봤는데 섰는지 모른다) · ``ORDINARY_MISSING``(없다 — 입구를 ecm
    으로 부른다) · ``ORDINARY_UNSURE``(못 읽고 로그온 열쇠도 없다) · ``ORDINARY_UNKNOWN``(못 가렸다). 문서함 손이 PC 의 문서함 에이전트를 부르기 전에 묻는다 — 입구를 대신 부르지 않는다."""
    script = pathlib.Path(os.environ.get(STATUS_ENV, "").strip() or STATUS)
    try:
        done = _node(script, (), env, timeout)
    except (NoNode, TimedOut, OSError):
        return ORDINARY_UNKNOWN
    word = (done.stdout or "").strip().splitlines()[-1:] or [""]
    return word[0] if done.returncode == 0 and word[0] in (ORDINARY_STOOD, ORDINARY_TRIED, ORDINARY_MISSING, ORDINARY_UNSURE) else ORDINARY_UNKNOWN

