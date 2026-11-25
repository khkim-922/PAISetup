"""사내 전자결재 앱(IAMS)의 손 — 손 셋(읽기 · 쓰기 · 창)의 바탕. EP 세션으로 결재 앱의 거래를 부르고, 화면을 받고, 임시저장 짐을 보낸다.
상신 · 승인 · 반려는 부르지 않는다. 손 셋이 함께 쓰는 자리도 여기 하나다 — 앱 안의 주소 · 문서 열쇠의 꼴(``key_of`` · ``doc_of``) · 결재함의
기간과 조회 칸 · 사람의 Edge 에 창을 띄우는 길(``browser`` · ``launch``).

부르는 꼴::

    import iams
    app = iams.App(<세션 파일>)                       # 스킬 ep-login 의 받는 손이 남긴 사내 세션(쿠키) 파일
    rows = app.tx(path, {"paramMap": {...}})          # 거래 하나 — 답 JSON(dict)
    page = app.page(path)                             # 화면 하나 — 글자(utf-8 · 안 되면 cp949)
    page = app.save({"apprDocVO": doc, "apprLineVO": lines})   # 임시저장 — 답 화면의 글자
    iams.dataset(page, "apprDocDS")                   # 화면에 박힌 데이터셋 줄들
    key = iams.doc_of("<id>.1.1.1"); iams.at(iams.VIEW, key)   # 문서 열쇠 → 칸 넷 → 그 문서의 주소

내는 것 — 앱의 JSON · 화면 글자 그대로. 예외 — ``SessionExpired``(사내 세션이 끊겼다 · 앱이 안 들였다 — 받는 손을 다시 부를 자리) ·
``SessionMissing``(세션 파일이 없다 · 못 읽는다) · ``Rejected``(앱이 임시저장 짐을 안 받았다고 말했다 — 아무것도 안 섰다) ·
``AppError``(그 밖 — 답이 꼴이 아니다 · 못 닿았다. 보낸 짐이 섰는지는 모른다) · ``Refused``(이 손이 안 부르는 주소다).

이 앱은 제 세션 쿠키를 안 심는다 — 부를 때마다 SSO 넘김 화면에서 토큰을 새로 받아 함께 보낸다(``_token``). 넘김 화면이 토큰을 냈다고
세션이 산 것은 아니다 — 섰는지는 앱의 답으로 가른다: JSON · 화면이 오면 섰고, ``error.do`` 로 넘기면 끊겼다(``_answer``).

사내 밖으로는 안 나간다 — 부르는 주소는 이 파일의 상수(검사가 가짜를 세울 때만 환경변수 ``IAMS_ROOT`` · ``IAMS_SSO_PAGE`` 가
바꾼다)뿐이고, 프록시를 안 탄다. 리다이렉트를 따라가지 않는다.
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
import uuid
from datetime import date, datetime, timedelta

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent.parent / "ep-login" / "scripts"   # 형제 스킬 — 세션 파일을 읽는 자리
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_command  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다
import ep_session  # noqa: E402
from ep_command import EXIT_ARGS, EXIT_TOOL, Stop  # noqa: E402

APP_ROOT = os.environ.get("IAMS_ROOT", "http://appv.poscofuturem.com:8083").rstrip("/")
SSO_PAGE = os.environ.get("IAMS_SSO_PAGE", "http://swpsso.posco.net/idms/U61/jsp/redirectSMSP.jsp")   # ``?redir_url=<부를 주소>`` 를 붙여 연다
SSO_FIELDS = ("ssoToken", "websealType", "domainName", "serverName", "LANG", "TIMEZONE")   # 넘김 화면이 내는 칸 — 앱의 SSO 필터가 읽는다
SAVE_PATH = "/iams/save.ex"        # [임시저장] 의 자리 — 상신(``submit.ex``)과 다른 주소다
TIMEOUT = 120                      # 묻기 하나의 시한 — 큰 함의 목록이 수십 초 걸린다
UA = "Mozilla/5.0"
AJAX_HEADERS = {"ex-http-ajax": "true", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}   # 거래를 화면 대신 JSON 으로 받는 머리
URI_COMPONENT_SAFE = "!*'()"       # 화면의 encodeURIComponent 가 안 싸는 글자(quote 가 늘 두는 「-_.~」 밖)
ENDED = ("errors.filter.fail", "errors.invalid.session")   # 앱이 끊긴 세션을 넘기는 오류 화면의 말 — 토큰이 없거나 낡았다
# 이 손이 부르지 않는 자리 — 사람이 누르는 결재 단추 · 앱 설정 · 받는 사람에게 가는 메일. 이름 일부가 걸리면 묻지 않는다
FORBIDDEN = ("submit", "approve", "reject", "recall", "resend", "receipt", "/disuse.ex", "updateRefrnComment",
             "saveMyApprovalLine", "saveAbsence", "sendApprovalMail")
DATASET = re.compile(r'<span ex-ds="([^"]+)">\s*<span ex-ds-data>\s*(\[.*?\])\s*</span>', re.S)   # 화면에 박힌 데이터셋
SAVED_FLAG = re.compile(r'id="_FLAG_"\s+value="([^"]*)"')      # 답 화면의 저장 표시 — 「S」 면 섰다
SAVE_ERROR = re.compile(r"_ERROR_MESSAGE_START_(.*?)_ERROR_MESSAGE_END_|id=\"_E_MSG_\"[^>]*>([^<]+)<", re.S)   # 답 화면이 든 앱의 거절 말
SAVED = "S"

# ── 앱 안의 자리 — 손 셋(읽기 · 쓰기 · 창)이 함께 읽는 한 자리. 문서를 받는 주소는 열쇠 칸 넷({APPR_DOC_ID} · {OVN} · {AVN} · {APVN})을 받는다 ──
DETAILS = "/iams/comx/documentService/selectApprDetails.ex"            # 문서 한 건의 결재선 · 의견 · 참조 · 배포 · 첨부 · 관련 문서 · 본문
DRAFTS = "/iams/commonSearch/documentsDAO/selectApprovalProgress.ex"   # 임시저장 목록(PROG_KIND NEW · LEGACY_ID IAMS)
DRAFTS_QUERY = {"paramMap": {"LEGACY_ID": "IAMS", "PROG_KIND": "NEW"}}
DEPT_TREE = "/iams/commonSearch/userDAO/selectDepartmentTree.ex"   # 결재 앱이 지금 쓰는 부서 나무(배포처 지정 창의 거래 · 읽기만)
NEW_DOC = "/iams/request.ex?formId={form}&_MENU_ACTION_=NEW"             # 새 문서 창 — 열어도 서버에 아무것도 안 남는다(WRITE-MAP 2 절, 잰 것)
_DOC_QUERY = "apprDocId={APPR_DOC_ID}&avn={AVN}&ovn={OVN}&apvn={APVN}"
DRAFT_DOC = "/iams/request.ex?" + _DOC_QUERY + "&_MENU_ACTION_=SAVE"     # 임시저장 다시 열기 · 고치는 창(WRITE-MAP 9 절, 잰 것)
VIEW = "/iams/document.ex?" + _DOC_QUERY + "&_MENU_ID_=_APPROVAL_&_MENU_ACTION_=NONE"   # 보기만 하는 문서 창 — 단추를 안 세운다
REUSE_DOC = "/iams/cpltReuse.ex?" + _DOC_QUERY                           # 완료 · 반려 문서의 [재사용] — ⚠ 여는 순간 임시저장이 선다
CANCELLED_REUSE_DOC = "/iams/reuse.ex?" + _DOC_QUERY                     # 취소된 문서의 [재사용] — 같다
KEY_FIELDS = ("APPR_DOC_ID", "OVN", "AVN", "APVN")
KEY_SEP = "."
KEY = re.compile(r"([0-9A-Za-z]+)\.(\d+)\.(\d+)\.(\d+)")                  # 문서 열쇠 — APPR_DOC_ID.OVN.AVN.APVN
CASCADE = re.compile(r"\"cascadeAt\"\s*:\s*'([YN]?)'")                    # 문서 창(request.ex)이 결재선 지정 창에 넘기는 다단결재 여부


def cascade_of(page: str | None) -> bool | None:
    """그 업무가 결재자 여럿(다단)을 받나 — 문서 창(request.ex)이 결재선 지정 창에 넘기는 값. 화면에 그 값이 없으면 None.
    보기 창(document.ex)은 이 값을 안 든다고 읽는다 — 다단을 가를 때는 같은 양식의 새 문서 창(``NEW_DOC`` — 서버에 안 남는다)을 연다."""
    m = CASCADE.search(page or "")
    return None if not m or not m.group(1) else m.group(1) == "Y"


# ── 문서 열쇠 — box · read · related · preview · save · open · discard 가 내고 받는 꼴 하나 ──────────────────────
def key_of(row: dict) -> str | None:
    """앱의 줄(목록 · 문서 화면 · 저장 답) → 문서 열쇠 ``APPR_DOC_ID.OVN.AVN.APVN``. 칸 하나라도 비면 None — 못 여는 열쇠를 안 낸다.
    관련 문서 줄의 REF_ 칸은 ``ref_key_of`` 가 읽는다."""
    parts = [row.get(k) for k in KEY_FIELDS]
    return None if any(v in (None, "") for v in parts) else KEY_SEP.join(map(str, parts))


def ref_key_of(row: dict) -> str | None:
    """관련 문서 줄(REF_APPR_DOC_ID · REF_OVN · REF_AVN · REF_APVN) → 그 문서의 열쇠. 칸이 비면 None."""
    return key_of({k: row.get(f"REF_{k}") for k in KEY_FIELDS})


def doc_of(text: str, flag: str = "문서") -> dict:
    """문서 열쇠 → 앱이 문서를 받는 칸 넷. 꼴이 아니면 Stop(인자) — ``flag`` 는 그 값을 받은 인자의 이름."""
    got = KEY.fullmatch((text or "").strip())
    if not got:
        raise Stop(EXIT_ARGS, "args", f"{flag} 의 문서 열쇠가 꼴이 아니다: {text!r}. 다음: box 답의 줄의 id(「문서id.1.1.1」 꼴)를 그대로 준다",
                   stepped=True)
    doc_id, ovn, avn, apvn = got.groups()
    return {"APPR_DOC_ID": doc_id, "OVN": int(ovn), "AVN": int(avn), "APVN": int(apvn)}


def details(app, seed: dict) -> dict:
    """문서 한 건의 결재선 · 의견 · 참조 · 배포 · 첨부 · 관련 문서 · 본문 — 문서 화면이 뜨며 보내는 거래 그대로(그 화면의 문서 줄을 싣는다)."""
    return app.tx(DETAILS, {"apprDocVO": seed})


def live_depts(app) -> set:
    """결재 앱이 지금 쓰는 부서 코드들 — 배포처 지정 창이 그리는 부서 나무 그대로."""
    got = app.tx(DEPT_TREE, {"paramMap": {}})
    return {str(r.get("DEPT_CODE")) for r in next((v for v in got.values() if isinstance(v, list)), []) if r.get("DEPT_CODE")}


def at(template: str, key: dict) -> str:
    """문서를 받는 주소 하나 — 열쇠 칸 넷을 주소에 싸서 넣는다."""
    return template.format(**{k: urllib.parse.quote(str(key[k]), safe="") for k in KEY_FIELDS})


def browser(path: str) -> str:
    """앱 안 경로 → 사람의 브라우저가 여는 주소 — SSO 넘김 화면의 ``redir_url`` 로 싼 앱의 온 주소(이 손이 토큰을 받는 길과 같다)."""
    return f"{SSO_PAGE}?redir_url={urllib.parse.quote(APP_ROOT + path, safe='')}"


# ── 결재함의 기간 — 목록 손과 창 손이 함께 쓴다 ────────────────────────────────────────────────────
BOX_MONTHS = 6                     # 기간을 꼭 받는 함의 화면이 묻는 가장 긴 기간(「6개월 이상 조회할 수 없습니다」)
BOX_DAYS = 30                      # 기간을 꼭 받는 함에 기간을 안 주면 오늘에서 이만큼 앞부터 — 화면의 addMonth(-1)


def months_after(day: date, months: int) -> date:
    """``day`` 에서 ``months`` 달 뒤의 같은 날 — 그 달에 없는 날이면 그 달 끝날."""
    y, m = divmod(day.month - 1 + months, 12)
    y, m = day.year + y, m + 1
    nxt = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    return date(y, m, min(day.day, (nxt - timedelta(days=1)).day))


def period(box: dict, since: str | None, until: str | None, today: date) -> tuple[date | None, date | None] | None:
    """함이 받는 기간 (앞 · 뒤 — 안 준 쪽은 None). 기간이 없는 함에 주면 Stop(인자). 꼭 받는 함은 안 준 쪽을 채운다(앞은 뒤에서
    한 달 전 · 뒤는 오늘)고 6 달을 넘으면 Stop(인자). 꼭 받지 않는 함은 준 쪽만 — 안 준 쪽을 지어내지 않는다."""
    if box.get("dates") is None:
        if since or until:
            raise Stop(EXIT_ARGS, "args", f"「{box['word']}」은 기간으로 안 거른다. 다음: --since · --until 을 빼고 다시 부른다", stepped=True)
        return None
    if not (since or until or box.get("need")):
        return None
    lo = ep_command.date_of(since, "--since 는") if since else None
    hi = ep_command.date_of(until, "--until 은") if until else None
    if box.get("need"):
        hi = hi or today
        lo = lo or hi - timedelta(days=BOX_DAYS)
    if lo and hi and lo > hi:
        raise Stop(EXIT_ARGS, "args", f"--since({lo})가 --until({hi})보다 뒤다. 다음: 앞뒤를 바꿔 다시 부른다", stepped=True)
    if box.get("need") and hi > months_after(lo, BOX_MONTHS):
        raise Stop(EXIT_ARGS, "args", f"앱이 이 함을 {BOX_MONTHS} 달까지만 묻는다({lo} ~ {hi}). 다음: 기간을 {BOX_MONTHS} 달 안으로 나눠 "
                                      "차례로 부른다", stepped=True)
    return lo, hi


def box_query(box: dict, span, words: str | None) -> dict:
    """함 하나의 조회 칸(``paramMap``) — 화면의 ``onSearch`` 가 싣는 꼴 그대로(PROG_KIND · NO_WAIT · LEGACY_ID · 준 기간 · 제목)."""
    query = {field: box[key] for field, key in (("PROG_KIND", "kind"), ("NO_WAIT", "no_wait"), ("LEGACY_ID", "legacy")) if box.get(key)}
    lo, hi = span or (None, None)
    if lo:
        query[f"{box['dates']}_DT_FR"] = lo.isoformat()
    if hi:
        query[f"{box['dates']}_DT_TO"] = hi.isoformat()
    if words:
        query["SUBJECT"] = words
    return query


# ── 사람의 Edge 에 창 띄우기 — 창 손이 열고, 쓰기 손이 저장한 뒤 연다. 여는 손은 ep-login 의 것(``ep_session.open_ordinary``)이다 ──────────
OPEN_SINK_ENV = "APPROVAL_OPEN_SINK"     # 시험장이 채운다 — 차면 창을 안 열고 그 파일에 연 주소를 한 줄 적는다


def sunk(url: str, sink: str) -> str:
    """시험장의 대역 — 띄우지 않고 ``sink`` 파일에 연 주소를 한 줄 적는다."""
    path = pathlib.Path(sink)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": datetime.now(ep_command.SEOUL).isoformat(timespec="seconds"), "url": url}, ensure_ascii=False) + "\n")
    return "사람의 평소 Edge 에 새 탭으로 열었다(가짜 회사 — 창 없음)"


def launch(url: str) -> str:
    """주소를 사람의 평소 Edge 에 새 탭으로 연다 — ep-login 이 EP 포털을 여는 그 손(``ep_session.open_ordinary``)으로. 어디에 열었나의 말을
    낸다. 못 열면 Stop(도구) — 주소를 말에 싣는다."""
    sink = os.environ.get(OPEN_SINK_ENV, "").strip()
    if sink:
        return sunk(url, sink)
    try:
        ep_session.open_ordinary(url)
    except ep_session.NotOpened as exc:
        raise Stop(EXIT_TOOL, "tool", f"{exc}. 다음: 사람에게 이 주소를 Edge 주소창에 붙여 여시라고 전한다 — {url}", stepped=True) from exc
    return "사람의 평소 Edge 에 새 탭으로 열었다"


class AppError(Exception):
    """결재 앱의 손이 낸 실패 — 앱이 거절했거나 답이 꼴이 아니거나 앱에 못 닿았다. ``save`` 에서는 보낸 짐이 섰는지 모른다 — ``Rejected`` 와
    ``sent`` 가 거짓인 것(짐을 보내기 전에 졌다)만 안 섰다."""

    sent = True


class Rejected(AppError):
    """앱이 답 화면에서 그 짐을 안 받았다고 말했다(``_FLAG_`` 가 「S」 가 아니다) — 서버에 아무것도 안 섰다."""


class SessionMissing(AppError):
    """세션 파일이 없거나 못 읽는다 — 받는 손(스킬 ep-login)을 부를 자리다."""


class SessionExpired(AppError):
    """사내 세션이 끊겼거나 앱이 안 들였다 — 받는 손을 다시 부를 자리다."""


class Refused(AppError):
    """이 손이 안 부르는 자리라 묻지 않았다(``FORBIDDEN``)."""


def uri_component(value) -> str:
    """화면의 ``encodeURIComponent`` 와 같은 글자 — dict · list 는 JSON 으로 옮긴 뒤 싼다."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return urllib.parse.quote(text, safe=URI_COMPONENT_SAFE)


def dataset(page: str, name: str) -> list:
    """화면에 박힌 데이터셋 ``name`` 의 줄들 — 없으면 빈 목록."""
    for found, rows in DATASET.findall(page):
        if found == name:
            return json.loads(rows)
    return []


def doc_row(page: str | None) -> dict | None:
    """문서 화면(보기 · 새 문서 · 임시저장 · 재사용 · 저장 답)이 심은 문서 한 줄(``apprDocDS``) — 없으면 None."""
    rows = dataset(page or "", "apprDocDS")
    return rows[0] if rows and isinstance(rows[0], dict) else None


def decoded(raw: bytes) -> str:
    """앱의 답 바이트 → 글자 — 거래 · 화면은 utf-8 이고, 옛 화면 몇은 cp949 다."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", "replace")


class App:
    """결재 앱 한 판 — 부를 때마다 SSO 토큰을 새로 받아 거래 · 화면 · 임시저장을 묻는다."""

    def __init__(self, session_file: pathlib.Path | str, *, timeout: float = TIMEOUT):
        jar = ep_session.load_jar(session_file, missing=SessionMissing)
        self._open = ep_session.opener(jar).open      # 프록시 없이 · 리다이렉트는 안 따라간다
        self._timeout = timeout

    # ── 넘김 토큰 ────────────────────────────────────────────────────────
    def _token(self, path: str) -> dict:
        """``path`` 로 넘기는 SSO 토큰 칸(``SSO_FIELDS``) — 토큰이 없으면 SessionExpired. 있다고 세션이 산 것은 아니다(``_answer`` 가 가린다)."""
        url = browser(path)
        try:
            with self._open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=self._timeout) as r:
                form = ep_session.sso_form(decoded(r.read()))
        except ep_session.Redirected as exc:
            raise SessionExpired(f"SSO 넘김 화면이 다른 곳으로 보냈다({exc.location}) — 사내 세션이 끊겼다") from exc
        except urllib.error.HTTPError as exc:
            raise SessionExpired(f"SSO 넘김 화면이 {exc.code} 로 답했다 — 사내 세션이 끊겼다") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"SSO 서버에 못 닿았다: {exc}") from exc
        if not form.get("ssoToken"):
            raise SessionExpired("SSO 넘김 화면에 토큰이 없다 — 사내 세션이 끊겼다")
        return {k: form[k] for k in SSO_FIELDS if k in form}

    # ── 묻기 ─────────────────────────────────────────────────────────────
    def _answer(self, path: str, req: urllib.request.Request) -> bytes:
        """요청 하나를 보내 답 바이트 — 앱이 오류 화면으로 넘기면 그 말로 SessionExpired(끊긴 세션) · AppError(그 밖), 거절 · 못 닿음은 AppError."""
        try:
            with self._open(req, timeout=self._timeout) as r:
                return r.read()
        except ep_session.Redirected as exc:
            if any(word in exc.location for word in ENDED):
                raise SessionExpired(f"결재 앱이 세션을 안 받았다({exc.location}) — 사내 세션이 끊겼다") from exc
            raise AppError(f"결재 앱이 {path} 를 다른 곳으로 넘겼다({exc.location})") from exc
        except urllib.error.HTTPError as exc:
            raise AppError(f"결재 앱이 {exc.code} 로 거절했다: {path}") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"결재 앱에 못 닿았다: {exc}") from exc

    def _post(self, path: str, fields: dict, headers: dict) -> bytes:
        """토큰 칸과 ``fields``(값은 ``uri_component`` 로 싼다)를 폼 POST 로 — 안 부르는 자리면 묻기 전에 Refused."""
        if any(word.lower() in path.lower() for word in FORBIDDEN):
            raise Refused(f"결재 앱의 {path} 는 이 손이 부르지 않는다 — 사람이 문서 창에서 누른다")
        body = urllib.parse.urlencode(self._token(path))
        body += "".join(f"&{k}={uri_component(v)}" for k, v in fields.items())
        req = urllib.request.Request(APP_ROOT + path, data=body.encode(), headers={"User-Agent": UA, **headers})
        return self._answer(path, req)

    def tx(self, path: str, fields: dict | None = None) -> dict:
        """거래 하나 — ``fields`` 는 칸 이름 → 값(조회 조건 ``paramMap`` · 데이터셋 ``…VO``). 답 JSON. JSON 이 아니면 AppError."""
        raw = self._post(path, fields or {}, AJAX_HEADERS)
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise AppError(f"결재 앱의 답이 JSON 이 아니다: {path} — {decoded(raw)[:120]!r}") from exc

    def page(self, path: str, fields: dict | None = None) -> str:
        """화면 하나 — 사람의 브라우저가 여는 꼴(폼 POST)로 받은 글자."""
        return decoded(self._post(path, fields or {}, {}))

    def save(self, datasets: dict) -> str:
        """[임시저장] 한 판 — ``datasets``(``apprDocVO`` · ``apprLineVO`` · …, 한 줄이면 dict · 여럿이면 list, 빈 것은 안 준다)를 화면처럼
        multipart 로 ``SAVE_PATH`` 에 보낸다. 앱의 SSO 필터는 multipart 몸통을 못 읽어 토큰 칸은 주소 뒤 쿼리에 싣는다. 답 화면의 ``_FLAG_`` 가
        ``SAVED`` 가 아니면 앱의 말로 AppError. 답 화면의 글자를 낸다 — 새 문서 열쇠는 그 화면의 ``apprDocDS`` 가 든다."""
        bound = "----iams" + uuid.uuid4().hex
        fields = {"_SAVE_KIND_": "", **{k: uri_component(v) for k, v in datasets.items()}}
        parts = [f'--{bound}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()]
        parts.append(f'--{bound}\r\nContent-Disposition: form-data; name="ATTACH_FILE"; filename=""\r\n'
                     "Content-Type: application/octet-stream\r\n\r\n\r\n".encode())
        parts.append(f"--{bound}--\r\n".encode())
        try:
            token = self._token(SAVE_PATH)
        except AppError as exc:
            exc.sent = False               # 짐을 보내기 전에 졌다 — 서버에 아무것도 안 섰다(쓰기 손이 이것으로 「모른다」와 가른다)
            raise
        url = f"{APP_ROOT}{SAVE_PATH}?{urllib.parse.urlencode(token)}"
        req = urllib.request.Request(url, data=b"".join(parts),
                                     headers={"User-Agent": UA, "Content-Type": f"multipart/form-data; boundary={bound}"})
        page = decoded(self._answer(SAVE_PATH, req))
        flag = SAVED_FLAG.search(page)
        if not flag:
            raise AppError(f"결재 앱의 임시저장 답 화면에 저장 표시(_FLAG_)가 없다 — 섰는지 모른다: {page[:120]!r}")
        if flag.group(1) != SAVED:
            said = next((" ".join(g.split()) for m in SAVE_ERROR.findall(page) for g in m if g.strip()), "까닭을 안 냈다")
            raise Rejected(f"결재 앱이 임시저장을 안 받았다 — {said[:200]}")
        return page
