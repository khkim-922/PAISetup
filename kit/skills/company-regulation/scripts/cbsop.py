"""사내 사규관리 앱(cbsop)의 손 — EP 세션으로 앱에 들어가, 범주 · 전체 목록 · 검색 · 문서 한 건을 읽는다. 읽기만 한다.

부르는 꼴::

    import cbsop
    app = cbsop.App(<세션 파일>)          # 스킬 ep-login 의 받는 손이 남긴 사내 세션(쿠키) 파일
    app.menus() · app.all_in(menu_idx) · app.search(말, fields) · app.info(process_idx)

내는 것 — 앱의 JSON 그대로(dict · list). 예외 — ``SessionExpired``(사내 세션이 끊겼다 · 앱이 안 들였다 — 받는 손을 다시 부를
자리) · ``SessionMissing``(세션 파일이 없다 · 못 읽는다) · ``AppError``(앱이 거절했다 · 답이 꼴이 아니다).

들어가는 길(2026-11-12 회사 PC 에서 잰 것)::

    1. 사내 세션 쿠키(.posco.net)를 싣고 SSO 넘김 화면(SSO_PAGE)을 GET — 200 에 숨은 칸 폼(ssoToken · …)이 온다.
       세션이 끊겼으면 그 칸이 없다
    2. 그 칸을 앱 뿌리(APP_ROOT)에 POST — 앱이 ``var epId = encodeURIComponent('…')`` 로 열쇠를 든 화면을 낸다
    3. ``/test/test_login.do?aes=<열쇠>`` 를 GET — 302 → ``/main/main.do`` 면 선 것. 앱은 그때 제 세션(JSESSIONID)을 심는다
    4. 그 뒤 ``/main/ajax/…`` 를 폼 꼴 POST 로 부른다. 끊긴 앱 세션은 302 → ``/test/closePage.do`` 다

앱의 세션 쿠키는 이 손의 쿠키 통에만 살고 세션 파일에 안 쓴다 — 받는 손이 남기는 것은 회사 도메인(posco.net) 쿠키뿐이고, 들어가기는
한 번에 1 초 안쪽이라 부를 때마다 다시 들어간다.

⚠ 열람 기록 — 앱의 화면은 문서를 열 때 ``insertSopConnHis.do`` 를 따로 불러 열람 기록을 남긴다. 이 손은 그 주소를 부르지 않는다 —
읽기(``selectProcessInfo.do``) 쪽에서 서버가 따로 남기는지는 못 쟀다(``references/SOURCES.md``). 남은 기록을 지우는 손은 없다(만들지 않는다).

사내 밖으로는 안 나간다 — 부르는 주소는 이 파일의 상수(검사가 가짜를 세울 때만 환경변수 ``CBSOP_ROOT`` · ``CBSOP_SSO_PAGE`` 가
바꾼다)뿐이고, 프록시를 안 탄다(사내 호스트다). 리다이렉트를 따라가지 않는다 — 따라가면 쿠키가 엉뚱한 자리에 실린다.
"""

from __future__ import annotations

import html
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent.parent / "ep-login" / "scripts"   # 형제 스킬 — 세션 파일을 읽는 자리
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_session  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다

APP_ROOT = os.environ.get("CBSOP_ROOT", "https://cbsop.poscofuturem.com").rstrip("/")
SSO_PAGE = os.environ.get("CBSOP_SSO_PAGE",
                          "http://swpsso.posco.net/idms/U61/jsp/redirectSMSP.jsp?redir_url="
                          + urllib.parse.quote(APP_ROOT, safe=""))
LANDING = "/main/main.do"          # 들어가기가 선 302 의 자리
TIMEOUT = 60                       # 묻기 하나의 시한 — 큰 범주의 전체 목록이 35 초 남짓 걸린다
SEARCH_TIMEOUT = 180               # 본문 검색은 흔한 낱말에 20 초 가까이 걸렸다
EP_KEY = re.compile(r"encodeURIComponent\('([^']+)'\)")
URI_COMPONENT_SAFE = "!*'()"       # 화면의 encodeURIComponent 가 안 싸는 글자 — 그 밖(「/」 도)은 다 싼다
UA = "Mozilla/5.0"


class AppError(Exception):
    pass


class SessionMissing(AppError):
    pass


class SessionExpired(AppError):
    pass


def _sso_form(page: str) -> dict:
    out = {}
    for tag in re.findall(r"<input[^>]*>", page, flags=re.I):
        name = re.search(r'name\s*=\s*["\']([^"\']+)', tag, flags=re.I)
        value = re.search(r'value\s*=\s*["\']([^"\']*)', tag, flags=re.I)
        if name:
            out[name.group(1)] = html.unescape(value.group(1)) if value else ""
    return out


class App:
    def __init__(self, session_file: pathlib.Path | str, *, timeout: float = TIMEOUT):
        self._jar = ep_session.load_jar(session_file, missing=SessionMissing)   # 앱 쿠키도 이 통에 받아 이 판 동안만 산다
        self._open = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                                 urllib.request.HTTPCookieProcessor(self._jar), ep_session.NoRedirect()).open
        self._timeout = timeout
        self._in = False

    def _get(self, url: str, data: dict | None = None, timeout: float | None = None) -> str:
        body = None if data is None else urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body, headers={"User-Agent": UA})
        with self._open(req, timeout=timeout or self._timeout) as r:
            return r.read().decode("utf-8", "replace")

    # ── 들어가기 ─────────────────────────────────────────────────────────
    def login(self) -> None:
        try:
            page = self._get(SSO_PAGE)
        except ep_session.Redirected as exc:
            raise SessionExpired(f"SSO 넘김 화면이 다른 곳으로 보냈다({exc.location}) — 사내 세션이 끊겼다") from exc
        except urllib.error.HTTPError as exc:
            raise SessionExpired(f"SSO 넘김 화면이 {exc.code} 로 답했다 — 사내 세션이 끊겼다") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"SSO 서버에 못 닿았다: {exc}") from exc
        form = _sso_form(page)
        if not form.get("ssoToken"):
            raise SessionExpired("SSO 넘김 화면에 토큰이 없다 — 사내 세션이 끊겼다")
        try:
            hand = self._get(APP_ROOT + "/", form)
        except ep_session.Redirected as exc:
            raise SessionExpired(f"사규 앱이 들이지 않았다({exc.location})") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"사규 앱에 못 닿았다: {exc}") from exc
        key = EP_KEY.search(hand)
        if not key:
            raise SessionExpired("사규 앱이 EP 열쇠를 안 냈다 — 사내 세션이 끊겼다")
        try:
            self._get(f"{APP_ROOT}/test/test_login.do?aes={urllib.parse.quote(key.group(1), safe='')}")
        except ep_session.Redirected as exc:
            if urllib.parse.urlsplit(exc.location).path == LANDING:
                self._in = True
                return
            raise SessionExpired(f"사규 앱이 들이지 않았다({exc.location})") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"사규 앱에 못 닿았다: {exc}") from exc
        raise SessionExpired("사규 앱이 들어가기에 답만 하고 넘기지 않았다")

    # ── 부르기 ───────────────────────────────────────────────────────────
    def call(self, path: str, data: dict | None = None, timeout: float | None = None):
        if not self._in:
            self.login()
        try:
            raw = self._get(APP_ROOT + path, data or {}, timeout)
        except ep_session.Redirected as exc:
            raise SessionExpired(f"사규 앱 세션이 끊겼다({exc.location})") from exc
        except urllib.error.HTTPError as exc:
            raise AppError(f"사규 앱이 {exc.code} 로 거절했다: {path}") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"사규 앱에 못 닿았다: {exc}") from exc
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise AppError(f"사규 앱의 답이 JSON 이 아니다: {path}") from exc

    # ── 읽기 ─────────────────────────────────────────────────────────────
    def menus(self) -> list:
        """맨 위 범주 — [{menuIdx, menuName, openYn, …}]."""
        return self.call("/main/ajax/getMainMenuList.do")["mainmenuList"]

    def all_in(self, menu_idx: int) -> list:
        """한 범주 아래 문서 전부(화면의 「EXCEL」 이 받는 목록) — [{processIdx, processName, categoriName0..3, …}]."""
        return self.call("/main/ajax/getProcessListAll.do", {"preIdx": menu_idx})["processList"]

    def search(self, text: str, fields: str = "subject") -> dict:
        """앱의 통합 검색 — fields 는 subject · content · file_name · user_name · team_name 을 쉼표로. 화면처럼 검색어를 한 번
        싸서 searchText · searchText2 둘에 다 준다 — searchText2 가 비면 본문 검색이 늘 0 건이다(잰 것)."""
        word = urllib.parse.quote(text, safe=URI_COMPONENT_SAFE)
        return self.call("/main/ajax/searchListCnt.do",
                         {"searchText": word, "searchText2": word, "menuId": "", "searchConditionPram": fields},
                         timeout=SEARCH_TIMEOUT)

    def info(self, process_idx: int) -> dict:
        """문서 한 건 — ProcessInfo[0](메타 · 본문 HTML) · searchTobe(최근 개정의 바뀐 자리) · 관련 표준 · 첨부."""
        return self.call("/main/ajax/selectProcessInfo.do", {"processIdx": process_idx})
