"""사내 게시판(Posco Family Groupware · XClick U14)의 손 — EP 세션으로 게시판에 들어가, 게시판 나무 · 글 목록 · 찾기 · 글 한 건 ·
첨부 목록 · 첨부 받기 · 임시보관함 목록을 읽는다. 게시판에 쓰지 않는다 — 글을 짓는 일은 곁의 ``draft_board.js`` 가 화면에서 한다.

부르는 꼴::

    import xclick
    app = xclick.App(<세션 파일>)                 # 스킬 ep-login 의 받는 손이 남긴 사내 세션(쿠키) 파일
    app.tree(write=False) · app.articles(bbs_id, …) · app.article(bbs_id, article_id) · app.files(article_id)
    app.download(file_id) · app.drafts()

내는 것 — 화면의 HTML 을 푼 dict · list. 예외 — ``SessionExpired``(사내 세션이 끊겼다 · 게시판이 안 들였다) · ``SessionMissing``
(세션 파일이 없다) · ``NotFound``(받은 id 로 글이 안 열렸다) · ``AppError``(게시판이 거절했다 · 답이 잰 꼴이 아니다).

들어가는 길(2026-11-16 회사 PC 에서 잰 것)::

    1. 사내 세션 쿠키(.posco.net)를 싣고 SSO 넘김 화면(SSO_PAGE)을 GET — 숨은 칸 폼(ssoToken · …)이 온다
    2. 그 칸을 dispatcherSubmitSSO.jsp 에 POST — 게시판이 제 세션(JSESSIONID)을 심고, 사용자 ID 를 든 스크립트(plainTxt = "id=…")를 낸다
    3. 그 글을 화면의 뒤섞기(``scramble`` — urlsecure.js 의 jQuery.encrypt)로 싸서 cefDispatcherSSO.jsp 에 _xcsparam 으로 POST — 섰다
    4. 그 뒤 XClickController 에 폼 꼴 POST 로 묻는다. 끊긴 세션은 「openMiniLoginPop」 한 줄을 낸다

조회수 — 글 읽기(viewArticle)는 ``transaction_yn=Y`` 로 부르면 조회수를 하나 올리고 ``N`` 이면 안 올린다(잰 것). 이 손은 늘 N 이다.
사내 밖으로는 안 나간다 — 부르는 주소는 이 파일의 상수뿐이고 프록시를 안 탄다. 리다이렉트를 따라가지 않는다.
"""

from __future__ import annotations

import base64
from datetime import date
import html
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent.parent / "ep-login" / "scripts"   # 형제 스킬
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_session  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다

ROOT = "http://swpappr.posco.net:7070/U14/U14010"
ENTRY = ROOT + "/dispatcherSubmitSSO.jsp?menu=BBS_ALL"
SSO_PAGE = "http://swpsso.posco.net/idms/U61/jsp/redirectSMSP.jsp?redir_url=" + urllib.parse.quote(ENTRY, safe="")
CONTROLLER = ROOT + "/XClickController"
BOARD_HOST = urllib.parse.urlsplit(ROOT).hostname   # 본문 그림을 묻는 호스트 — 이 밖은 안 묻는다
ROOT_ORIGIN = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(ROOT)).lower()   # 본문 그림을 묻는 자리 — 잰 스킴 · 호스트 · 포트
IMAGE_PATH = urllib.parse.urlsplit(ROOT).path + "/DownController.do"   # 본문 그림의 잰 꼴 — 이 길에 fileId 하나만(2026-11-16 · 게시판 15 곳 글 45 건)
TOP_BBS, TOP_TREE = "BBS85", "BBS_ALL_00001"   # 게시판 나무의 뿌리 — 이 뿌리로 찾으면 모든 게시판을 함께 찾는다(잰 것)
SCRAMBLE_KEY = "xclick6"           # 화면의 뒤섞기 열쇠(urlsecure.js 의 URL_SECURE_ENCKEY)
SCRAMBLE_DELTA, SCRAMBLE_ROUNDS = 123, 3   # 같은 파일의 delta · 돌림 수 — 화면이 고쳐 박은 값이다
TIMEOUT = 60
UA = "Mozilla/5.0"
LOGGED_OUT = "openMiniLoginPop"    # 끊긴 세션이 내는 한 줄의 낱말
CONDITION = "//condition-searchCondition-"   # 찾기 칸의 이름 머리 — 뒤에 title · contents · writer · filename
CONDITION_SEP = "\x0c"             # 여러 칸을 잇는 글자(화면의 "\14")
EARLIEST = "1990-01-01"            # 기간을 안 주면 이날부터 — 화면의 기본(6 개월)보다 넓게 찾는다


class AppError(Exception):
    pass


class Refused(AppError):
    """묻지 않은 주소 — 게시판 밖의 그림."""


class NotFound(AppError):
    """받은 id 로 글이 안 열렸다 — 게시판 id 와 글 id 가 안 맞는다. 부르는 쪽은 인자가 틀린 것으로 옮긴다."""


class SessionMissing(AppError):
    pass


class SessionExpired(AppError):
    pass


def scramble(plain: str, key: str = SCRAMBLE_KEY) -> str:
    """화면의 jQuery.encrypt 와 같은 글자 — UTF-8 바이트를 4 바이트 작은끝 수로 묶어 XXTEA 꼴로 세 번 섞고 base64 의 「=」 을 「!」 로."""
    if not plain:
        return ""
    raw = plain.encode("utf-8")
    v = [int.from_bytes(raw[i:i + 4].ljust(4, b"\0"), "little") for i in range(0, len(raw), 4)]
    if len(v) <= 1:
        v.append(0)
    kb = key.encode("utf-8")[:16]
    k = [int.from_bytes(kb[i:i + 4].ljust(4, b"\0"), "little") for i in range(0, len(kb), 4)]
    n, z, total = len(v), v[-1], 0
    i32 = lambda x: ((int(x) & 0xFFFFFFFF) ^ 0x80000000) - 0x80000000   # noqa: E731 — JS 의 비트 연산은 32 비트 부호 수로 본다
    for _ in range(SCRAMBLE_ROUNDS):
        total += SCRAMBLE_DELTA
        e = (total & 0xFFFFFFFF) >> 2 & 3
        for p in range(n):
            y = v[(p + 1) % n]
            idx = (p & 3) ^ e
            kv = k[idx] if idx < len(k) else 0    # JS 는 없는 칸을 undefined → 0 으로 본다
            mx = i32(i32(i32(z) ^ i32(y)) + i32(i32(y) ^ i32(z)) ^ i32(i32(i32(total) ^ i32(y)) + i32(kv ^ i32(z))))
            v[p] += mx                            # JS 의 v[p] += mx 는 32 비트로 안 자른다 — 바이트로 낼 때 자른다
            z = v[p]
    out = b"".join((int(x) & 0xFFFFFFFF).to_bytes(4, "little") for x in v)
    return base64.b64encode(out).decode().replace("=", "!")


def text_of(fragment: str) -> str:
    """HTML 조각 → 한 줄 글자(태그 · 주석을 걷고 겹친 빈칸을 하나로)."""
    s = re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>", " ", fragment, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


ROW = re.compile(r'<tr class="table_m\d"[^>]*>(.*?)(?=<tr class="table_m\d"|$)', re.S)
CELL = re.compile(r'<td[^>]*briefYn="\w"[^>]*>(.*?)</td>', re.S)
CHK = re.compile(r"name=\"chkid\" value='(\{[^']+\})'")
WRITER_TAG = re.compile(r"<a id='user[^']*'[^>]*>(.*?)</a>", re.S)
DATE_CELL = re.compile(r'briefYn="\w"[^>]*>\s*((?:\d{4}-)?\d\d-\d\d(?: \d\d:\d\d)?)\s*</td>')
VIEWS_LINK = re.compile(r'readUserListPop\([^)]*\);return false;">\s*(\d+)\s*</a>')
DRAFT_STATE = re.compile(r"임시저장|예약저장|예약")
TOTAL = re.compile(r"총\s*([\d,]+)\s*건")
TREE_ITEM = re.compile(r"new TreeData\('([^']+)','([^']+)','[^']+', decodeURL\('([^']*)'\),\d+,'\w',(\{[^}]*\})")
FILE_ITEM = re.compile(r'_fileArr\.push\(\[url\+"\?fileId=([^"]+)","((?:[^"\\]|\\.)*)",(\d+)\]')
WRITER = re.compile(r'vsub_title"[^>]*>\s*게시자\s*</td>\s*<td class="vsub_value">(.*?)</td>', re.S)
PERIOD = re.compile(r'vsub_title"[^>]*>\s*게시기한\s*</td>\s*<td class="vsub_value"\s*>(.*?)</td>', re.S)
STAMP = re.compile(r"(\d{4}-\d\d-\d\d \d\d:\d\d)&nbsp;\s*\|\s*조회수")
SUBJECT = re.compile(r'<div class="top_subject"[^>]*>(.*?)</div>', re.S)
CONTENT = re.compile(r'<div id="contentArea_[^"]+"[^>]*>(.*?)</div>\s*</td>\s*</tr>\s*</table>', re.S)
# 본문 칸 안의 감싸개 — 글 화면이 본문을 한 행 한 칸의 표(`table-layout:auto` · 칸 `min-height:100px`)에 담아 낸다(2026-11-16 · 회사 PC).
# 글이 아니라 화면의 틀이라 벗긴다 — 두면 본문을 푸는 손이 글의 표를 「칸 안에 든 표」로 읽어 표 전체를 한 줄로 잇는다
WRAPPER = re.compile(r"\s*<table[^>]*table-layout:\s*auto[^>]*>\s*<tr[^>]*>\s*(?:<!--.*?-->\s*)*<td[^>]*min-height:\s*100px[^>]*>(.*)"
                     r"</td>\s*</tr>\s*</table>\s*", re.S | re.I)


def parse_rows(page: str) -> dict:
    """글 목록 화면 → {total, rows}. 줄마다 board(게시판 id) · id · title · board_name · writer · date · views · notice · files.

    칸은 자리가 아니라 꼴로 집는다 — 목록 꼴(게시판 · 찾기 · 모든 게시판)마다 칸의 차례가 다르고 칸 안에 표가 든다(잰 것).
    제목 · 게시판 id 는 고름 칸의 JSON, 작성자는 사람 꼬리표, 게시일은 날짜 꼴, 조회는 조회자 목록 링크, 게시판 이름은
    나무에서 그 id 로 대는 쪽(``names``)이 든다 — 화면의 게시판 이름 칸은 꼴마다 있다 없다 한다."""
    rows = []
    for m in ROW.finditer(page):
        block = m.group(1)
        chk = CHK.search(block)
        if not chk:
            continue
        key = json.loads(html.unescape(chk.group(1)))
        writer = WRITER_TAG.search(block)
        posted = DATE_CELL.search(block)
        views = VIEWS_LINK.search(block)
        rows.append({
            "board": key.get("bbsId", ""), "id": key.get("articleId", ""),
            "title": html.unescape(key.get("title", "")),
            "writer": text_of(writer.group(1)) if writer else "",
            "date": posted.group(1) if posted else "", "views": int(views.group(1)) if views else None,
            "notice": "icon_notice" in block, "files": "viewArticleAttachFile" in block,
        })
    total = TOTAL.search(text_of(page))
    return {"total": int(total.group(1).replace(",", "")) if total else len(rows), "rows": rows}


def parse_tree(page: str) -> list:
    """게시판 나무 한 층 → [(bbs_id, tree_id, 이름, 묶음인가)]."""
    out = []
    for bbs, tree_id, name, data in TREE_ITEM.findall(page):
        folder = re.search(r'folderYn"\s*:\s*"(\w)', data)
        out.append((bbs, tree_id, html.unescape(urllib.parse.unquote(name)), bool(folder and folder.group(1) == "Y")))
    return out


def parse_files(page: str) -> list:
    """첨부 목록 화면 → [{id, name, size}]."""
    return [{"id": fid, "name": json.loads(f'"{name}"'), "size": int(size)} for fid, name, size in FILE_ITEM.findall(page)]


def parse_article(page: str) -> dict:
    """글 화면 → {title, writer, posted, period, html}. 본문이 없으면(게시판 id 가 틀렸다 · 글이 없다) AppError."""
    body = CONTENT.search(page)
    if not body:
        raise NotFound("글 화면에 본문 칸이 없다 — 게시판 id 와 글 id 가 맞는지 본다(목록 줄의 id 를 그대로 쓴다)")
    pick = lambda rx: text_of(rx.search(page).group(1)).lstrip(": ").strip() if rx.search(page) else ""   # noqa: E731
    return {"title": pick(SUBJECT), "writer": pick(WRITER), "posted": STAMP.search(page).group(1) if STAMP.search(page) else "",
            "period": pick(PERIOD), "html": unwrap(body.group(1))}


def unwrap(content: str) -> str:
    """본문 칸 → 글의 HTML. 칸 전체가 한 행 한 칸의 감싸개 표면 그 칸 안만 낸다(``WRAPPER``) — 한 겹만 벗긴다."""
    wrapped = WRAPPER.fullmatch(content)
    return wrapped.group(1) if wrapped else content


class App:
    def __init__(self, session_file: pathlib.Path | str, *, timeout: float = TIMEOUT):
        self._jar = ep_session.load_jar(session_file, missing=SessionMissing)
        self._open = ep_session.opener(self._jar).open   # 프록시 없이 · 리다이렉트는 안 따라간다
        self._timeout = timeout
        self._in = False

    def _raw(self, url: str, data: dict | list | None = None) -> bytes:
        body = None if data is None else urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body, headers={"User-Agent": UA})
        try:
            with self._open(req, timeout=self._timeout) as r:
                return r.read()
        except ep_session.Redirected as exc:
            raise SessionExpired(f"게시판이 다른 곳으로 넘겼다({exc.location}) — 사내 세션이 끊겼다") from exc
        except urllib.error.HTTPError as exc:
            raise AppError(f"게시판이 {exc.code} 로 답했다: {url.split('?')[0]}") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"게시판에 못 닿았다: {exc}") from exc

    def _get(self, url: str, data: dict | list | None = None) -> str:
        page = self._raw(url, data).decode("utf-8", "replace")
        if LOGGED_OUT in page[:300]:
            raise SessionExpired("게시판이 로그인 창을 냈다 — 사내 세션이 끊겼다")
        return page

    def login(self) -> None:
        page = self._raw(SSO_PAGE).decode("utf-8", "replace")
        form = ep_session.sso_form(page)
        if not form.get("ssoToken"):
            raise SessionExpired("SSO 넘김 화면에 토큰이 없다 — 사내 세션이 끊겼다")
        hand = self._raw(ENTRY, form).decode("utf-8", "replace")
        uid = re.search(r'plainTxt\s*=\s*"([^"]+)"', hand)
        if not uid:
            raise SessionExpired("게시판이 사용자 ID 를 안 냈다 — 사내 세션이 끊겼다")
        self._raw(ROOT + "/cefDispatcherSSO.jsp", {"_xcsparam": scramble(uid.group(1)), "menu": "BBS_ALL",
                                                    "login_locale": "ko", "login_timezone": "%2B540"})
        self._in = True

    def call(self, data: dict | list) -> str:
        if not self._in:
            self.login()
        return self._get(CONTROLLER, data)

    # ── 읽기 ────────────────────────────────────────────────────────────
    def tree(self, *, write: bool = False) -> list:
        """게시판 나무 전체 — [{id, name, path, folder}]. ``write`` 면 쓸 수 있는 게시판만(화면의 글쓰기 고름 상자와 같다)."""
        if not self._in:
            self.login()
        out = []

        def walk(bbs, tree_id, path):
            url = (f"{CONTROLLER}?facade=BBSFacade&command=treeBBSSub&nextpage=/common/dynamicTree.jsp&bbsId={bbs}"
                   f"&upTreeId={tree_id}&userMode=USER&thememode=USER&authMode={'WRITE' if write else 'READ'}&srchUseYn=Y&dynamicTree=true")
            for child, child_tree, name, folder in parse_tree(self._get(url, {})):
                out.append({"id": child, "name": name, "path": path + [name], "folder": folder})
                if folder:
                    walk(child, child_tree, path + [name])

        walk(TOP_BBS, TOP_TREE, [])
        return out

    def articles(self, bbs_id: str = TOP_BBS, *, words: str = "", fields: tuple = (), since: str = EARLIEST,
                 until: str = "", page: int = 1, count: int = 20) -> dict:
        """게시판 하나(묶음이면 그 아래 다)의 글 — 낱말을 주면 ``fields`` 칸에서 찾는다. 뿌리면 모든 게시판."""
        data = {"facade": "BBSArticleFacade", "command": "listArticle", "nextpage": "/bbs/articleGenList.jsp",
                "categoryId": "BBS_ALL", "bbsId": bbs_id, "paging_listcnt": str(count), "currpage_no": str(page),
                "srchStartDate": since, "srchEndDate": until or date.today().isoformat()}   # 끝 날을 비우면 화면의 기본 기간(1 년)으로 준다(잰 것)
        if words:
            data.update(srchKeyword=words, srchChkConditionList=CONDITION_SEP.join(CONDITION + f for f in fields), searchMode="Y")
        return parse_rows(self.call(data))

    def article(self, bbs_id: str, article_id: str) -> dict:
        page = self.call({"facade": "BBSArticleFacade", "command": "viewArticle", "nextpage": "/bbs/articleView.jsp",
                          "transaction_yn": "N", "articleId": article_id, "articleBbsId": bbs_id, "categoryId": "BBS_ALL", "popYn": "Y"})
        return parse_article(page)

    def files(self, article_id: str) -> list:
        if not self._in:
            self.login()
        return parse_files(self._get(f"{ROOT}/common/fileattach/download.jsp?refId={urllib.parse.quote(article_id)}"
                                     "&downYn=Y&innoFDId=innoFDId&fileTitle="))

    def image(self, src: str) -> bytes:
        """본문 ``<img src>`` 하나 — 상대 주소는 글 화면(CONTROLLER)에 대어 풀고, 게시판 호스트 · 포트의 잰 꼴(IMAGE_PATH 에 fileId
        하나)만 묻는다 — 게시판 호스트의 다른 길은 사내 세션을 싣고 무엇을 할지 모른다. 그 밖이면 묻지 않고
        ``Refused``. 게시판은 그림에 Content-Type ``application/smnet`` 을 댄다(잼) — 꼴은 부르는 쪽이 바이트 머리로 가린다."""
        url = urllib.parse.urljoin(CONTROLLER, src.strip())
        parts = urllib.parse.urlsplit(url)
        host = (parts.hostname or "").lower()
        if host != BOARD_HOST:
            raise Refused(f"게시판 밖의 그림이라 묻지 않는다({host or '주소 없음'}) — 화면에서 본다")
        keys = [k for k, _ in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)]
        if f"{parts.scheme}://{parts.netloc}".lower() != ROOT_ORIGIN or parts.path != IMAGE_PATH or keys != ["fileId"]:
            raise Refused(f"게시판 본문 그림의 잰 꼴(DownController.do?fileId=)이 아니라 묻지 않는다({parts.path[:60]}) — 화면에서 본다")
        if not self._in:
            self.login()
        data = self._raw(url)
        if LOGGED_OUT.encode() in data[:300]:
            raise SessionExpired("그림 대신 로그인 창이 왔다 — 사내 세션이 끊겼다")
        return data

    def download(self, file_id: str) -> bytes:
        if not self._in:
            self.login()
        return self._raw(f"{ROOT}/DownController?fileId={urllib.parse.quote(file_id)}&down_filename=f")

    def drafts(self) -> dict:
        """임시 · 예약보관함 — 줄마다 board · id · title · date · state."""
        page = self.call({"facade": "BBSArticleFacade", "command": "listTempArticle", "nextpage": "/bbs/articleTempList.jsp",
                          "categoryId": "BBS_ALL", "menuGbn": "TEMP", "paging_listcnt": "50", "currpage_no": "1"})
        rows = []
        for m in ROW.finditer(page):
            chk = CHK.search(m.group(1))
            if chk:
                key = json.loads(html.unescape(chk.group(1)))
                posted = DATE_CELL.search(m.group(1))
                state = DRAFT_STATE.search(text_of(m.group(1)))
                rows.append({"board": key.get("bbsId", ""), "id": key.get("articleId", ""), "title": html.unescape(key.get("title", "")),
                             "date": posted.group(1) if posted else "", "state": state.group(0) if state else ""})
        return {"rows": rows}
