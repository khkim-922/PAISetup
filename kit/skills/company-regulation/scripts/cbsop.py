"""사내 사규관리 앱(cbsop)의 손 — EP 세션으로 앱에 들어가, 범주 · 전체 목록 · 검색 · 문서 한 건을 읽는다. 읽기만 한다.

부르는 꼴::

    import cbsop
    app = cbsop.App(<세션 파일>)          # 스킬 ep-login 의 받는 손이 남긴 사내 세션(쿠키) 파일
    app.menus() · app.all_in(menu_idx) · app.changed(부터, 까지, 상태) · app.search(말, fields) · app.info(process_idx) · app.related(process_idx)
    app.screen_allows(process_idx) · app.history · past · tobe · trail(개정이력과 그 판) · app.person(사번) · app.used · access(내 목록)
    app.image(본문 그림 주소)

내는 것 — 앱의 JSON 그대로(dict · list). 예외 — ``SessionExpired``(사내 세션이 끊겼다 · 앱이 안 들였다 — 받는 손을 다시 부를
자리) · ``SessionMissing``(세션 파일이 없다 · 못 읽는다) · ``AppError``(앱이 거절했다 · 답이 꼴이 아니다).

들어가는 길은 SSO 넘김 → 앱 뿌리 POST → ``test_login.do?aes=`` → ``main.do`` 네 걸음이다 — 걸음마다의 꼴은 ``references/SOURCES.md``
「들어가는 길」이 든다. 앱의 세션 쿠키는 이 손의 쿠키 통에만 살고 세션 파일에 안 쓴다 — 들어가기가 짧아 부를 때마다 다시 들어간다.

⚠ 앱의 화면은 문서를 열 때 ``insertSopConnHis.do`` 로 열람 기록을 따로 남긴다 — 이 손은 그 주소를 부르지 않는다. 읽기 쪽에서 서버가
따로 남기는지는 못 쟀다(``references/SOURCES.md``).

사내 밖으로는 안 나간다 — 부르는 주소는 이 파일의 상수(검사가 가짜를 세울 때만 환경변수 ``CBSOP_ROOT`` · ``CBSOP_SSO_PAGE`` 가
바꾼다)뿐이고, 프록시를 안 탄다. 리다이렉트를 따라가지 않는다 — 따라가면 쿠키가 엉뚱한 자리에 실린다.
"""

from __future__ import annotations

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
TIMEOUT = 60                       # 묻기 하나의 시한 — 큰 범주의 전체 목록이 수십 초 걸린다(잰 값은 ``references/SOURCES.md``)
SEARCH_TIMEOUT = 180               # 본문 검색의 시한 — 흔한 낱말이면 수십 초 걸려 목록보다 넉넉히 둔다
EP_KEY = re.compile(r"encodeURIComponent\('([^']+)'\)")
URI_COMPONENT_SAFE = "!*'()"       # 화면의 encodeURIComponent 가 안 싸는 글자 — 그 밖(「/」 도)은 다 싼다
UA = "Mozilla/5.0"
SCREEN_DOC = "/main/goProcessInfoPop.do"   # 사람이 문서를 여는 화면 창 — 등급 문서를 읽기 전에 그 창이 여나를 본다(``screen_allows``)
SCREEN_DENIED = "권한이 없습니다"            # 그 창이 막을 때 내는 스크립트의 말
MY_SCREEN = "/myProcessList/oftenUseProcess.do"   # 내 목록 화면 — 앱이 쓰는 사람의 사번을 박아 둔다
MY_EMPCD = re.compile(r'empcd\s*:\s*"(\d+)"')
OPEN_GRADE = "일반"             # 화면에 묻지 않고 여는 보안등급 — 그 밖은 화면의 문서 창이 여나를 먼저 본다(``screen_allows``)
GRADES = {"기밀": "SEC", "사외비A/비공개": "APR", "사외비A": "ADE", "사외비B/비공개": "BPR", "사외비B": "BPB", OPEN_GRADE: "NPB"}   # 화면 「접근 가능한 표준」 의 등급 칸
IMAGE_PATH = re.compile(r"/uploads/output/[^/?#]+/[^/?#]+/media/[^/?#]+")   # 본문 그림의 잰 꼴 — 앱 호스트의 그림 주소는 이 꼴 하나다(``references/SOURCES.md``)


class AppError(Exception):
    pass


class SessionMissing(AppError):
    pass


class SessionExpired(AppError):
    pass


class Refused(AppError):
    """잰 꼴 밖의 주소라 묻지 않았다."""


class App:
    GRADES = GRADES                    # 부르는 쪽이 등급 이름을 코드로 바꿀 때 — 화면의 표 그대로

    def __init__(self, session_file: pathlib.Path | str, *, timeout: float = TIMEOUT):
        self._jar = ep_session.load_jar(session_file, missing=SessionMissing)   # 앱 쿠키도 이 통에 받아 이 판 동안만 산다
        self._open = ep_session.opener(self._jar).open   # 프록시 없이 · 리다이렉트는 안 따라간다
        self._timeout = timeout
        self._in = False
        self._me: str | None = None        # 쓰는 사람의 사번 — ``me`` 가 한 번 받는다

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
        form = ep_session.sso_form(page)
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
    def screen(self, path: str, data: dict | None = None, timeout: float | None = None) -> str:
        """앱의 한 자리를 들어간 세션으로 받아 글자 그대로 — data 가 있으면 폼 POST, 없으면 GET. 끊긴 세션 · 거절 · 못 닿음을 손의 예외로."""
        if not self._in:
            self.login()
        try:
            return self._get(APP_ROOT + path, data, timeout)
        except ep_session.Redirected as exc:
            raise SessionExpired(f"사규 앱 세션이 끊겼다({exc.location})") from exc
        except urllib.error.HTTPError as exc:
            raise AppError(f"사규 앱이 {exc.code} 로 거절했다: {path}") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"사규 앱에 못 닿았다: {exc}") from exc

    def call(self, path: str, data: dict | None = None, timeout: float | None = None):
        raw = self.screen(path, data or {}, timeout)
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

    def search(self, text: str, fields: str = "subject", menu_id: int | str = "") -> dict:
        """앱의 통합 검색 — fields 는 subject · content · file_name · user_name · team_name 을 쉼표로. 화면처럼 검색어를 한 번
        싸서 searchText · searchText2 둘에 다 준다 — searchText2 가 비면 본문 검색이 늘 0 건이다. menu_id 는 맨 위 범주의 menuIdx(빈 글자면
        모든 범주)."""
        word = urllib.parse.quote(text, safe=URI_COMPONENT_SAFE)
        return self.call("/main/ajax/searchListCnt.do",
                         {"searchText": word, "searchText2": word, "menuId": menu_id, "searchConditionPram": fields},
                         timeout=SEARCH_TIMEOUT)

    def image(self, src: str) -> bytes:
        """본문 ``<img src>`` 하나 — 앱 호스트의 잰 꼴(IMAGE_PATH · 물음표 없이)만 묻고, 그 밖이면 묻지 않고 ``Refused``. 그림은 앱
        세션 없이도 받아진다 — 그래서 들어가기를 안 거친다. 앱은 그림에 Content-Type ``application/octet-stream`` 을 댄다 — 꼴은
        부르는 쪽이 바이트 머리로 가린다."""
        url = urllib.parse.urljoin(APP_ROOT + "/", src.strip())
        parts = urllib.parse.urlsplit(url)
        if any(seg in (".", "..") for seg in urllib.parse.unquote(parts.path).split("/")):
            # 잰 꼴의 칸 수만 맞추고 「..」 로 그 밖으로 올라가는 주소 — 서버가 풀면 울타리 밖을 묻게 된다
            raise Refused(f"경로에 「..」 이 든 그림 주소라 묻지 않는다({parts.path[:40]}) — 화면에서 본다")
        if f"{parts.scheme}://{parts.netloc}".lower() != APP_ROOT.lower() or parts.query or not IMAGE_PATH.fullmatch(parts.path):
            raise Refused(f"사규 앱의 본문 그림 꼴이 아니라 묻지 않는다({parts.hostname or '주소 없음'}{parts.path[:40]}) — 화면에서 본다")
        try:
            with self._open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=self._timeout) as r:
                return r.read()
        except ep_session.Redirected as exc:
            raise AppError(f"그림 주소가 다른 곳으로 보냈다({exc.location})") from exc
        except urllib.error.HTTPError as exc:
            raise AppError(f"사규 앱이 그림을 {exc.code} 로 거절했다") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"사규 앱에 못 닿았다: {exc}") from exc

    def info(self, process_idx: int) -> dict:
        """문서 한 건 — ProcessInfo[0](메타 · 본문 HTML) · searchTobe(최근 개정의 바뀐 자리) · searchProcessFileList(첨부) ·
        reviewerList · searchRelationSite. 관련 표준은 여기 없다 — ``related``."""
        return self.call("/main/ajax/selectProcessInfo.do", {"processIdx": process_idx})

    def related(self, process_idx: int) -> list:
        """화면 「관련표준」 표 — [{processIdx, processName, menuName, reDeptnm, hname, regDate, stateNm, …}]."""
        return self.call("/main/ajax/selectRelationProcessList.do", {"processIdx": process_idx}).get("relationProcessList") or []

    def screen_allows(self, process_idx: int) -> bool:
        """사람의 화면이 이 문서를 여나 — 화면의 문서 창(``goProcessInfoPop.do``)을 GET 해 가린다. 막으면 「권한이 없습니다」 스크립트
        하나가 오고, 열면 그 문서 번호를 든 화면이 온다. 둘 다 아니면 가리지 못한 것이라 ``AppError``(여는 쪽으로 넘기지 않는다).
        창의 스크립트는 안 돌린다 — 화면이 여는 순간 부르는 열람 기록(``insertSopConnHis.do``)은 그 스크립트가 따로 부른다."""
        page = self.screen(f"{SCREEN_DOC}?processIdx={int(process_idx)}")
        if SCREEN_DENIED in page:
            return False
        if f'var processIdx = "{int(process_idx)}"' in page:
            return True
        raise AppError(f"문서 {process_idx} 의 화면이 여는지 막는지 가리지 못했다(잰 꼴이 아니다) — 사규 화면에서 연다")

    def changed(self, since: str, until: str, state: str) -> list:
        """화면 「최근 변경된 표준」 — 날은 앱 꼴(YYYY.MM.DD), state 는 공개 · 삭제 · 빈 글자(전체)."""
        return self.call("/myProcessList/getChangedProcessList.do",
                         {"fromDate": since, "toDate": until, "state": state, "searchText": ""}).get("changedProcessList") or []

    def history(self, process_idx: int) -> list:
        """화면 「개정이력」 — 판마다 [{version, enforcementDate, mainContent | revisedContent, hname, reHname, workIdx, processHisIdx, …}].
        새 판부터."""
        return self.call("/main/ajax/selectRevisionHistoryInfo.do", {"processIdx": process_idx}).get("revisionHistoryInfo") or []

    def past(self, process_his_idx: int) -> dict:
        """지난 판 한 건 — ProcessHisInfo[0](메타 · 본문 HTML) · 첨부 · 관련사이트."""
        return self.call("/main/ajax/selectProcessHisInfo.do", {"processHisIdx": process_his_idx})

    def tobe(self, work_idx: int) -> list:
        """한 개정의 전후대비표 — [{tobeGubunNm, oldContent, toContent, note}]."""
        return self.call("/myProcessList/searchTobeList.do", {"workIdx": work_idx}).get("searchTobeList") or []

    def trail(self, work_idx: int) -> list:
        """한 개정의 결재 경과 — [{apRegDate, codeName, reHname, apHname, opinion}]."""
        return self.call("/main/ajax/selectRevisionHistoryDetailInfo.do", {"workIdx": work_idx}).get("revisionHistoryDetailInfo") or []

    def person(self, empcd: str) -> dict | None:
        """화면에서 이름을 누르면 뜨는 사람 창 — {hname, deptcdDisp, jikwicdDisp, jikckcdDisp, responsibility, officePhone, handpon, email}.
        퇴사자면 None."""
        return self.call("/cmmn/ajax/getEmpInfo.do", {"empcd": empcd}).get("empInfo")

    def me(self) -> str:
        """쓰는 사람의 사번 — 앱은 내 목록 화면에 그 값을 박아 둔다(``empcd : "…"``). 이 판 동안 한 번만 받는다."""
        if self._me is None:
            found = set(MY_EMPCD.findall(self.screen(MY_SCREEN)))
            if len(found) != 1:
                raise AppError(f"내 목록 화면에서 내 사번을 하나로 못 읽었다({len(found)} 개) — 사규 화면에서 본다")
            self._me = found.pop()
        return self._me

    def used(self, since: str, until: str) -> list:
        """화면 「최근 사용 표준」(내가 화면에서 연 문서) — [{processIdx, processName, menuName1..3, reDeptnm, hname, reRegDate, txtIdx}]."""
        return self.call("/myProcessList/searchOftenUseProcessList.do",
                         {"fromDate": since, "toDate": until, "empcd": self.me()}).get("OftenUseProcessList") or []

    def access(self, grade: str) -> list:
        """화면 「접근 가능한 표준」 의 한 등급(읽기 범위) — 등급 코드는 ``GRADES``. 빈 등급(전체)은 1 분 가까이 걸려 안 받는다."""
        if grade not in GRADES.values():
            raise Refused(f"등급 코드가 아니다: {grade}")
        return self.call("/myProcessList/getMyAuthProcessList.do",
                         {"empcd": self.me(), "securityGrade": grade, "authRange": "r"}).get("myProcessList") or []
