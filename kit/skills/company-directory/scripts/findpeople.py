"""그룹사 사람찾기 앱(findpeople)의 손 — 사내 세션으로 앱에 들어가 사람을 찾고 한 사람의 상세를 읽는다. 읽기만 한다.

부르는 꼴::

    import findpeople
    app = findpeople.App(<세션 파일>)     # 스킬 ep-login 의 받는 손이 남긴 사내 세션(쿠키) 파일
    app.own                              # 쓰는 사람의 회사 값(앱이 들일 때 준다 — poscochem 꼴)
    app.search(갈래, 말, 회사 값)          # → Found — 수 · 줄들 · 잘랐나
    app.detail(회사 값, 직번)             # → {칸 이름: 글자} — 칸은 회사마다 다르다

내는 것 — ``Found``(앱이 댄 수 · ``Row`` 들 · 답이 커서 잘랐나) · 상세의 칸 사전. 예외 — ``SessionExpired``(사내 세션이 끊겼다 · 앱이 안
들였다) · ``SessionMissing``(세션 파일이 없다 · 못 읽는다) · ``AppError``(앱이 거절했다 · 답이 꼴이 아니다 · 못 닿았다).

들어가는 길은 SSO 넘김 → ``s35050f001.do?event=auth`` POST → 스스로 내는 폼 ``searchFrm2`` → ``s35050f020.do`` 네 걸음이다 — 걸음마다의
꼴과 잰 값은 ``../references/SOURCES.md`` 「사람찾기」 가 든다. 앱의 세션 쿠키는 이 손의 쿠키 통에만 살고 세션 파일에 안 쓴다.

부르는 주소는 이 파일의 상수 다섯(들어가는 길 셋 · 찾기 ``SEARCH`` · 상세 ``DETAIL``)뿐이다 — 앱 화면의 문자 · 메일 · 모바일 보내기 ·
전화 걸기 · 실천다짐 등록 · 설정 화면은 부르지 않는다. 사진은 답의 몸에 인라인으로 오지만 글자로 풀 때 뗀다.
프록시를 안 타고 리다이렉트를 따라가지 않는다. 주소는 이 파일의 상수뿐이다.
"""

from __future__ import annotations

import dataclasses
import html
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "ep-login" / "scripts"   # 형제 스킬 — 세션 파일을 읽는 자리
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_session  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다

ROOT = "http://findpeople.posco.co.kr:7780"
APP = ROOT + "/S35/S35020/s35050f10/"
AUTH = APP + "s35050f001.do?event=auth"
SSO_PAGE = "http://swpsso.posco.net/idms/U61/jsp/redirectSMSP.jsp?redir_url=" + urllib.parse.quote(AUTH, safe="")
FIRST, SEARCH, DETAIL = APP + "s35050f020.do", APP + "s35050f030.do", APP + "s35050f050.do"
TIMEOUT = 60                  # 묻기 하나의 시한 — 수천 줄 답이 7.5 초 걸렸다(``SOURCES.md``)
MOST_BYTES = 1_500_000        # 찾기 답을 이만큼까지만 읽는다 — 쪽 나누기가 없어 흔한 말은 수천 줄(3.4 MB)이 한 몸으로 온다. 줄 하나가 1 KB 안팎
UA = "Mozilla/5.0"
GROUP = "A"                   # 회사 고름의 「국내그룹사」 묶음 — 내 회사와 홀딩스는 안 든다(``SOURCES.md``)
# 회사 값 → 화면의 탭 값 — 화면 JS 의 goOrgList 가 고르는 대로(홀딩스 H · 포스코 P · 나머지 그룹사 B)
TABS = {"poscoinc": "H", "posco": "P"}
TAB_OTHER = "B"
# 찾기 갈래 — 사람 말 → 화면의 searchTp. 원팀활동(oneTeam)은 안 잰 칸이라 안 든다
KINDS = {"전체": "searchAll", "이름": "empName", "직번": "empNo", "조직": "orgName", "담당업무": "jobName",
         "회사전화": "officePhone", "휴대전화": "handPhone", "메일": "email"}
BAD_WORD = re.compile(r"[%_']|-{2,}|\s{2,}")   # 화면 JS 가 막는 말 — % _ ' · 잇단 「--」 · 잇단 빈칸(checkSpecial · chkHyphen · checkSpace)
LOGGED_OUT = ("사용자 정보가 없어", "redirectSMSP.jsp")   # 앱 세션이 없을 때의 답(257 바이트 스크립트)에 드는 글자


class AppError(Exception):
    """사람찾기 앱의 손이 낸 실패 — 앱이 거절했거나 답이 꼴이 아니거나 앱에 못 닿았다."""


class SessionMissing(AppError):
    """세션 파일이 없거나 못 읽는다 — 받는 손(스킬 ep-login)을 부를 자리다."""


class SessionExpired(AppError):
    """사내 세션이 끊겼거나 앱이 안 들였다 — 받는 손을 다시 부를 자리다."""


@dataclasses.dataclass(frozen=True)
class Row:
    """찾은 사람 한 줄 — 목록 · 명함 · 상세 어느 꼴에서 왔든 같은 칸이다. 칸 이름은 주소록의 사람과 같게 두어 같은 거르기가 걸린다
    (``level`` · ``is_boss`` · ``location`` 은 이 앱에 없어 빈 값이다)."""
    company: str            # 회사 값(poscoinc 꼴)
    empno: str
    name: str
    dept: str = ""
    job_title: str = ""     # 직책
    grade: str = ""         # 직급명칭
    office: str = ""        # 회사전화
    duty: str = ""          # 담당업무
    email: str = ""
    company_name: str = ""  # 회사 이름(포스코홀딩스 꼴) — 앱이 고름 상자에 댄 이름
    level: str = ""
    is_boss: bool = False
    location: str = ""


@dataclasses.dataclass(frozen=True)
class Found:
    """찾기 한 판의 답 — 앱이 머리에 댄 수(``total``) · 읽은 줄 · 답이 커서 ``MOST_BYTES`` 에서 잘랐나."""
    total: int
    rows: list
    cut: bool


# ── 답 읽기 — 화면 글자 → 값(바깥 없음) ────────────────────────────────────

TAG = re.compile(r"<[^>]+>")
INLINE = re.compile(r"</?(?:span|em|strong|b|font)\b[^>]*>", re.I)   # 글자 안의 꾸밈(맞은 말의 highlight) — 빈칸 없이 뗀다
DROP = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
COMMENT = re.compile(r"<!--.*?-->", re.S)  # 화면이 주석으로 남긴 칸(목록 줄 머리의 회사 칸) — 칸을 셀 때 밀리지 않게 뗀다
IMG = re.compile(r"<img\b[^>]*>", re.I)      # 사진은 인라인 base64 — 글자로 풀기 전에 통째로 뗀다
INPUT = re.compile(r"<input\b[^>]*>", re.I)
TOTAL = re.compile(r"검색 결과\s*<em>\s*<strong>(\d+)</strong>")
OPEN_DETAIL = re.compile(r"goDetail\('(\w*)','([^']*)','([^']*)'\)")
COMPANY_OPTION = re.compile(r'<option value="([a-z][\w-]*)"[^>]*>([^<]+)')
ROW_LABEL = re.compile(r'<th scope="row">(.*?)</th>((?:(?!<th).)*?)<td[^>]*>(.*?)</td>', re.S)


def text_of(chunk: str) -> str:
    """화면 조각 하나의 보이는 글자 — 스크립트 · 그림 · 태그를 떼고(맞은 말을 감싼 highlight 도) 빈칸을 하나로, 엔티티를 푼다."""
    return " ".join(html.unescape(TAG.sub(" ", INLINE.sub("", IMG.sub("", DROP.sub("", chunk))))).split())


def form_of(page: str, name: str) -> dict:
    """그 이름의 폼의 숨은 칸 → {name: value} — 폼이 없으면 빈 사전. 단추 · 고름 칸은 뺀다(화면이 내지 않는 값)."""
    m = re.search(r'<form[^>]*name="%s".*?</form>' % re.escape(name), page, re.S | re.I)
    out = {}
    for tag in INPUT.findall(m.group(0) if m else ""):
        n, kind = re.search(r'name="([^"]*)"', tag), re.search(r'type="([^"]*)"', tag)
        if not n or (kind and kind.group(1).lower() in ("button", "radio", "checkbox")):
            continue
        v = re.search(r'value\s*=\s*"([^"]*)"', tag)
        out.setdefault(n.group(1), html.unescape(v.group(1)) if v else "")
    return out


def companies_of(page: str) -> dict:
    """첫 화면의 회사 고름 상자 → {회사 값: 회사 이름} — 앱이 쓰는 사람에게 보이는 회사들이다(찾기 갈래의 고름 값은 안 든다)."""
    return {v: text_of(n) for v, n in COMPANY_OPTION.findall(page) if v not in KINDS.values()}


def own_of(page: str) -> str:
    """첫 화면에서 쓰는 사람의 회사 값 — 회사 고름 상자에 미리 골라 둔 값(찾기 갈래의 고름 값은 안 본다). 없으면 빈 글자."""
    return next((v for v in re.findall(r'<option value="([a-z][\w-]*)"[^>]*\bselected', page) if v not in KINDS.values()), "")


def labelled(chunk: str) -> dict:
    """``<th scope="row">칸</th>`` 바로 뒤 ``<td>`` 의 글자 → {칸: 글자} — 상세 · 명함은 칸 차림이 회사마다 달라 자리 아닌 이름으로 읽는다."""
    out = {}
    for label, _, value in ROW_LABEL.findall(chunk):
        out.setdefault(text_of(label), text_of(value))
    return out


def shape_of(page: str) -> str:
    """찾기 답의 꼴 — ``one``(1 건 · 상세로 가는 폼) · ``cards``(2–19 건 명함) · ``list``(20 건 넘는 목록) · ``none``(0 건). 앱 세션이 없다는
    답이면 ``out``, 그 밖은 ``odd``. 0 바이트는 ``odd`` 다 — 칸이 빠진 요청에도 그렇게 와 끊긴 세션으로 읽지 않는다."""
    if any(w in page for w in LOGGED_OUT) and len(page) < 2000:
        return "out"
    if 'name="detailFrm"' in page and "s35050f050.do" in page and not TOTAL.search(page):
        return "one"
    if 'class="bbsListA"' in page:
        return "list"
    if 'class="personInfo2"' in page:
        return "cards"
    if TOTAL.search(page) and int(TOTAL.search(page).group(1)) == 0:
        return "none"
    return "odd"


def list_rows(page: str, names: dict) -> list:
    """목록 꼴의 줄 — 표 ``bbsListA`` 의 ``<tr>`` 마다 칸 일곱(이름 · 현소속 · 직책 · 직급명칭 · 회사전화 · 담당업무 · 메일). 잘린 몸의 마지막 줄은
    닫는 태그가 없어 안 든다."""
    body = COMMENT.sub("", page[page.find('class="bbsListA"'):])
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        hit = OPEN_DETAIL.search(tr)
        cells = [text_of(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if not hit or len(cells) < 7:
            continue
        _, empno, company = hit.groups()
        rows.append(Row(company, empno, cells[0], cells[1], cells[2], cells[3], cells[4], cells[5], cells[6],
                        names.get(company, company)))
    return rows


def card_rows(page: str, names: dict) -> list:
    """명함 꼴의 줄 — 카드(``dl.personInfo2``)마다 이름과 칸 이름으로 읽은 칸. 휴대전화 · 사진은 안 읽는다."""
    rows = []
    for card in re.split(r'<dl class="personInfo2">', COMMENT.sub("", page))[1:]:
        hit = OPEN_DETAIL.search(card)
        if not hit:
            continue
        _, empno, company = hit.groups()
        name = text_of(re.search(r'<dt class="name">(.*?)</dt>', card, re.S).group(1)) if '<dt class="name">' in card else ""
        f = labelled(card)
        rows.append(Row(company, empno, name, f.get("현소속", ""), f.get("직책", ""), f.get("직급명칭", ""), f.get("회사전화", ""),
                        f.get("담당업무", ""), f.get("메일주소", ""), names.get(company, f.get("회사", company))))
    return rows


def detail_row(company: str, empno: str, fields: dict, names: dict) -> Row:
    """상세의 칸 → 한 줄 — 「이름」 은 「한글 / 영문」 의 앞, 「직책/직무」 는 앞이 직책이다."""
    title = fields.get("직책/직무", fields.get("직책", "")).split("/", 1)[0].strip()
    return Row(company, fields.get("직번", empno), fields.get("이름", "").split("/", 1)[0].strip(), fields.get("현소속", ""), title,
               fields.get("직급명칭", ""), fields.get("회사전화", ""), fields.get("담당업무", ""), fields.get("E-mail", ""),
               names.get(company, company))


def tab_of(company: str) -> str:
    """회사 값 → 화면의 탭 값(``companyTp``) — 홀딩스 H · 포스코 P · 그 밖의 그룹사와 국내그룹사 묶음 B."""
    return TABS.get(company, TAB_OTHER)


def word_problem(word: str) -> str:
    """화면이 안 받는 찾을 말이면 그 까닭, 받으면 빈 글자 — 공백을 뺀 두 글자 이상 · ``%`` ``_`` ``'`` · 잇단 「--」 · 잇단 빈칸은 안 된다."""
    if len(word.replace(" ", "")) < 2:
        return "찾을 말은 빈칸을 빼고 두 글자 이상이다"
    if BAD_WORD.search(word):
        return "찾을 말에 % _ ' · 잇단 「--」 · 잇단 빈칸은 못 쓴다(사람찾기 화면이 막는다)"
    return ""


# ── 앱 한 판 — 망에 닿는 자리 ──────────────────────────────────────────────

class App:
    """사람찾기 앱 한 판 — 사내 세션의 쿠키로 들어가 찾기 · 상세를 읽는다. 들어가기는 처음 부를 때 한 번이다."""

    def __init__(self, session_file, *, timeout: float = TIMEOUT):
        self._jar = ep_session.load_jar(session_file, missing=SessionMissing)   # 앱 쿠키도 이 통에 받아 이 판 동안만 산다
        self._open = ep_session.opener(self._jar).open
        self._timeout = timeout
        self._base: dict | None = None      # 첫 화면의 frm 숨은 칸 — 찾기 · 상세가 그 위에 고친다
        self.names: dict = {}               # 회사 값 → 이름(첫 화면의 고름 상자)
        self.own = ""                       # 쓰는 사람의 회사 값

    def _post(self, url: str, data: dict | None, most: int | None = None) -> tuple[str, bool]:
        """주소 하나를 (``data`` 를 주면 폼 POST 로) 열어 받은 글자와 ``most`` 에서 잘랐나 — 넘김 · 거절 · 못 닿음을 손의 예외로."""
        body = None if data is None else urllib.parse.urlencode(data).encode()
        try:
            with self._open(urllib.request.Request(url, data=body, headers={"User-Agent": UA}), timeout=self._timeout) as r:
                raw = r.read(most + 1) if most else r.read()
        except ep_session.Redirected as exc:
            raise SessionExpired(f"사람찾기 앱이 다른 곳으로 보냈다({exc.location}) — 사내 세션이 끊겼다") from exc
        except urllib.error.HTTPError as exc:
            raise AppError(f"사람찾기 앱이 {exc.code} 로 거절했다") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"사람찾기 앱에 못 닿았다: {exc}") from exc
        cut = bool(most) and len(raw) > most
        return (raw[:most] if cut else raw).decode("utf-8", "replace"), cut

    def login(self) -> None:
        """앱에 들어간다 — SSO 넘김 화면의 칸을 앱의 auth 에 넘겨 스스로 내는 폼(``searchFrm2``)을 받고, 그것을 내 첫 화면이 서면 들어간
        것이다. 토큰 칸이 와도 세션이 산 것은 아니라(``ep_session.sso_form``) 앱이 그 폼을 내나로 가린다."""
        page, _ = self._post(SSO_PAGE, None)
        form = ep_session.sso_form(page)
        if not form.get("ssoToken"):
            raise SessionExpired("SSO 넘김 화면에 토큰이 없다 — 사내 세션이 끊겼다")
        page, _ = self._post(AUTH, form)
        hand = form_of(page, "searchFrm2")
        if not hand:
            raise SessionExpired("사람찾기 앱이 들이지 않았다(들어가는 폼이 안 왔다) — 사내 세션이 끊겼다")
        page, _ = self._post(FIRST, hand)
        base = form_of(page, "frm")
        if not base:
            raise AppError("사람찾기 첫 화면의 꼴이 아니다(frm 이 없다)")
        own = own_of(page) or hand.get("company", "")
        if not own:
            raise AppError("사람찾기 첫 화면에서 쓰는 사람의 회사를 못 읽었다(잰 꼴이 아니다)")
        self._base, self.names, self.own = base, companies_of(page), own

    def _form(self, **fields) -> dict:
        """첫 화면의 frm 위에 그 판의 칸을 고친 폼 — 처음이면 들어간다."""
        if self._base is None:
            self.login()
        return {**self._base, "categoryCode": "000", "categoryName": "전체", **fields}

    def search(self, kind: str, word: str, company: str) -> Found:
        """찾기 한 판 — 화면의 갈래(``KINDS`` 값) · 말 · 회사 값. 1 건 답은 상세를 한 번 따라가 한 줄로, 명함 · 목록은 줄로 읽는다. 답이
        ``MOST_BYTES`` 를 넘으면 거기서 끊고 읽은 줄만 낸다(``cut``) — 수는 앱이 머리에 댄 값이다."""
        page, cut = self._post(SEARCH, self._form(event="find_e", actionCode="102", searchTp=kind, searchWord=word.strip(),
                                                    companyLov=company, company=company, companyTp=tab_of(company)), MOST_BYTES)
        shape = shape_of(page)
        if shape == "out":
            raise SessionExpired("사람찾기 앱이 사용자 정보가 없다고 했다 — 사내 세션이 끊겼다")
        if shape == "none":
            return Found(0, [], False)
        if shape == "one":
            hand = form_of(page, "detailFrm")
            return Found(1, [self._detail_row(hand.get("company", company), hand.get("empNo", ""), hand)], False)
        if shape == "odd":
            raise AppError(f"사람찾기 찾기의 답이 잰 꼴이 아니다({len(page)} 바이트)")
        rows = list_rows(page, self.names) if shape == "list" else card_rows(page, self.names)
        total = TOTAL.search(page)
        return Found(int(total.group(1)) if total else len(rows), rows, cut)

    def detail(self, company: str, empno: str) -> dict:
        """한 사람의 상세 — {칸 이름: 글자}. 칸 차림은 회사마다 다르다(근무형태 · 근무현황 · 팩스 · 실천다짐 …). 휴대전화는 든 그대로다."""
        page, _ = self._post(DETAIL, self._form(event="find", actionCode="203", company=company, companyTp=tab_of(company),
                                                empNo=empno), None)
        if shape_of(page) == "out":
            raise SessionExpired("사람찾기 앱이 사용자 정보가 없다고 했다 — 사내 세션이 끊겼다")
        fields = labelled(COMMENT.sub("", page))
        if "이름" not in fields:
            raise AppError(f"사람찾기 상세의 꼴이 아니다({company} {empno})")
        return fields

    def _detail_row(self, company: str, empno: str, hand: dict) -> Row:
        """1 건 답이 가리킨 사람의 한 줄 — 그 상세를 읽어 줄로 옮긴다."""
        return detail_row(company, empno, self.detail(company, hand.get("empNo", empno)), self.names)
