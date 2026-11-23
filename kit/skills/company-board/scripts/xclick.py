"""사내 게시판(Posco Family Groupware · XClick U14)의 손 — EP 세션으로 게시판에 들어가, 게시판 나무 · 글 목록 · 찾기 · 글 한 건 ·
첨부 목록 · 첨부 받기 · 임시보관함 목록 · 글의 의견 · 열람내역 · 게시판 옵션 · 쓰기 창의 폼(임시글 · 재활용)을 읽는다. 게시판에 쓰지 않는다 — 글을 짓는 일은 곁의 ``draft_board.js`` 가 화면에서 한다.

부르는 꼴::

    import xclick
    app = xclick.App(<세션 파일>)                 # 스킬 ep-login 의 받는 손이 남긴 사내 세션(쿠키) 파일
    app.tree(write=False) · app.articles(bbs_id, …) · app.article(bbs_id, article_id) · app.files(article_id)
    app.download(file_id) · app.drafts() · app.readers(bbs_id, article_id) · app.options(bbs_id)
    app.draft_form(bbs_id, draft_id) · app.copy_form(bbs_id, article_id) · article_link(bbs_id, article_id)

내는 것 — 화면의 HTML 을 푼 dict · list. 예외 — ``SessionExpired``(사내 세션이 끊겼다 · 게시판이 안 들였다) · ``SessionMissing``
(세션 파일이 없다) · ``NotFound``(받은 id 로 글이 안 열렸다) · ``AppError``(게시판이 거절했다 · 답이 잰 꼴이 아니다).

들어가는 길은 SSO 넘김 → 게시판 세션 → 뒤섞은(``scramble``) 사용자 ID POST 세 걸음이다 — 걸음마다의 꼴은 ``references/SOURCES.md``
「들어가기」가 든다. ⚠ 글 읽기(viewArticle)는 늘 ``transaction_yn=N`` 으로 부른다 — ``Y`` 면 조회수가 오른다. 사내 밖으로는 안
나간다 — 부르는 주소는 이 파일의 상수뿐이고 프록시를 안 타며 리다이렉트를 따라가지 않는다.
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
IMAGE_PATH = urllib.parse.urlsplit(ROOT).path + "/DownController.do"   # 본문 그림의 잰 꼴 — 이 길에 fileId 하나만(``references/SOURCES.md``)
TOP_BBS, TOP_TREE = "BBS85", "BBS_ALL_00001"   # 게시판 나무의 뿌리 — 이 뿌리로 찾으면 모든 게시판을 함께 찾는다
SCRAMBLE_KEY = "xclick6"           # 화면의 뒤섞기 열쇠(urlsecure.js 의 URL_SECURE_ENCKEY)
SCRAMBLE_DELTA, SCRAMBLE_ROUNDS = 123, 3   # 같은 파일의 delta · 돌림 수 — 화면이 고쳐 박은 값이다
TIMEOUT = 60
UA = "Mozilla/5.0"
LOGGED_OUT = "openMiniLoginPop"    # 끊긴 세션이 내는 한 줄의 낱말
CONDITION = "//condition-searchCondition-"   # 찾기 칸의 이름 머리 — 뒤에 title · contents · writer · filename
CONDITION_SEP = "\x0c"             # 여러 칸을 잇는 글자(화면의 "\14")
WRITE_PARAMS = json.loads((pathlib.Path(__file__).resolve().parent / "write_params.json").read_text(encoding="utf-8"))   # 짓는 손과 한 벌


def write_params(kind: str, board: str, article_id: str = "") -> dict:
    """writeArticle 의 칸(곁의 write_params.json — 짓는 손이 창을 열 때와 같은 한 벌)."""
    return {k: str(v).replace("{board}", board).replace("{id}", article_id) for k, v in WRITE_PARAMS[kind].items() if k != "_"}


EARLIEST = "1990-01-01"            # 기간을 안 주면 이날부터 — 화면의 기본(6 개월)보다 넓게 찾는다


class AppError(Exception):
    """게시판 손이 낸 실패 — 게시판이 거절했거나 답이 잰 꼴이 아니거나 게시판에 못 닿았다."""
    pass


class Refused(AppError):
    """묻지 않은 주소 — 게시판 밖의 그림."""


class NotFound(AppError):
    """받은 id 로 글이 안 열렸다 — 게시판 id 와 글 id 가 안 맞는다. 부르는 쪽은 인자가 틀린 것으로 옮긴다."""


class SessionMissing(AppError):
    """세션 파일이 없거나 비었다 — 받는 손(스킬 ep-login)을 부를 자리다."""
    pass


class SessionExpired(AppError):
    """사내 세션이 끊겼거나 게시판이 안 들였다 — 받는 손을 다시 부를 자리다."""
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
# 본문 칸 안의 감싸개 — 글 화면이 본문을 담는 한 행 한 칸의 표다. 화면의 틀이라 벗긴다 — 두면 본문을 푸는 손이 글의 표를
# 「칸 안에 든 표」로 읽어 표 전체를 한 줄로 잇는다
WRAPPER = re.compile(r"\s*<table[^>]*table-layout:\s*auto[^>]*>\s*<tr[^>]*>\s*(?:<!--.*?-->\s*)*<td[^>]*min-height:\s*100px[^>]*>(.*)"
                     r"</td>\s*</tr>\s*</table>\s*", re.S | re.I)


COMMENT_COUNT = re.compile(r"<font style='color:#f26522'>\[(\d+)\]</font>")   # 목록 줄 제목 끝의 의견 수
ROW_KEY = re.compile(r'"(articleId|bbsId)":"([^"]*)"')
ROW_TITLE = re.compile(r"<a id='list[^']*'[^>]*>\s*<font[^>]*>(.*?)</font>\s*</a>", re.S)
COMMENT_LINE = re.compile(r'<table[^>]*class="c_line"[^>]*>(.*?)</table>\s*<div style="display:none;" id="_refCommentDiv', re.S)
COMMENT_WHO = re.compile(r'<span class="c_name">(.*?)</span>', re.S)
COMMENT_AT = re.compile(r'<span[^>]*class="c_date">\s*([\d-]+ [\d:]+)\s*</span>')
COMMENT_TEXT = re.compile(r'<td class="c_text"[^>]*>(.*?)</td>', re.S)
COMMENT_TAG = re.compile(r'img/tag_\w+\.png" title="([^"]*)"')
COMMENT_TOTAL = re.compile(r"의견\((\d+)\s*건\)")
READER_ROW = re.compile(r'<tr class="table_m\d">\s*(.*?)</tr>', re.S)
TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
LINK_SSO = "http://swpsso.posco.net/idms/U61/jsp/redirectSMSP.jsp?redir_url="   # 화면 「URL복사」 의 시스템 값 ssoURL(xclick-cef //articleURL)
LINK_ARTICLE = ROOT + "/dispatcherSubmitSSO.jsp?"                               # 같은 자리의 articleURL


def row_key(raw: str) -> dict:
    """목록 줄 고름 칸의 JSON — 상세검색 꼴은 제목의 큰따옴표를 안 감싸 JSON 이 깨진다. 그때는 id 둘만 꼴로 집는다(제목은 링크 글자에서)."""
    text = html.unescape(raw)
    try:
        return json.loads(text)
    except ValueError:
        return dict(ROW_KEY.findall(text))


def row_title(key: dict, block: str) -> str:
    """목록 줄의 제목 — 고름 칸의 JSON 에 있으면 그것, 깨진 꼴(``row_key`` 가 id 만 집은 것)이면 줄의 링크 글자(의견 수는 걷는다)."""
    if "title" in key:
        return html.unescape(key["title"])
    shown = ROW_TITLE.search(block)
    return text_of(COMMENT_COUNT.sub("", shown.group(1))) if shown else ""


def article_link(bbs_id: str, article_id: str) -> str:
    """글 화면 「URL복사」 와 같은 바로가기 — ssoURL + encodeURIComponent(articleURL + menu · bbsid · articleid)."""
    target = f"{LINK_ARTICLE}menu=BBS_ALL&bbsid={bbs_id}&articleid={article_id}"
    return LINK_SSO + urllib.parse.quote(target, safe="-_.!~*'()")


def parse_comments(page: str) -> dict:
    """글 화면의 의견 칸 → {total, rows}. 줄마다 who(이름과 직함 · 부서 — 화면 글자 그대로) · at · text · kind(기타 · 질문 …) ·
    reply(남의 의견에 단 답글). 화면이 한 번에 다 싣는다 — 쪽이 없다."""
    total = COMMENT_TOTAL.search(page)
    rows = []
    for block in COMMENT_LINE.findall(page):
        who, at, body = COMMENT_WHO.search(block), COMMENT_AT.search(block), COMMENT_TEXT.search(block)
        kind = COMMENT_TAG.search(block)
        text = body.group(1).replace("<br>", "\n") if body else ""
        rows.append({"who": text_of(who.group(1)) if who else "", "at": at.group(1) if at else "",
                     "text": "\n".join(text_of(x) for x in text.split("\n")).strip(),
                     **({"kind": kind.group(1)} if kind else {}), **({"reply": True} if "icon_reply" in block else {})})
    return {"total": int(total.group(1)) if total else len(rows), "rows": rows}


def parse_readers(page: str) -> dict:
    """열람내역 창 → {total, rows}. 줄마다 at · name · dept · title(직함). 사번 칸은 싣지 않는다."""
    rows = []
    for block in READER_ROW.findall(page):
        cells = [text_of(c) for c in TD.findall(block)]
        if len(cells) >= 5 and cells[0].isdigit():
            rows.append({"at": cells[1], "name": cells[2], "dept": cells[3], "title": cells[4]})
    total = TOTAL.search(text_of(page))
    return {"total": int(total.group(1).replace(",", "")) if total else len(rows), "rows": rows}


def parse_rows(page: str) -> dict:
    """글 목록 화면 → {total, rows}. 줄마다 board(게시판 id) · id · title · board_name · writer · date · views · notice · files.

    칸은 자리가 아니라 꼴로 집는다 — 목록 꼴(게시판 · 찾기 · 모든 게시판)마다 칸의 차례가 다르고 칸 안에 표가 든다.
    게시판 이름은 나무에서 그 id 로 대는 쪽(``names``)이 든다 — 화면의 게시판 이름 칸은 꼴마다 있다 없다 한다."""
    rows = []
    for m in ROW.finditer(page):
        block = m.group(1)
        chk = CHK.search(block)
        if not chk:
            continue
        key = row_key(chk.group(1))
        writer = WRITER_TAG.search(block)
        posted = DATE_CELL.search(block)
        views = VIEWS_LINK.search(block)
        said = COMMENT_COUNT.search(block)
        rows.append({
            "board": key.get("bbsId", ""), "id": key.get("articleId", ""),
            "title": row_title(key, block), "comments": int(said.group(1)) if said else 0,
            "writer": text_of(writer.group(1)) if writer else "",
            "date": posted.group(1) if posted else "", "views": int(views.group(1)) if views else None,
            "notice": "icon_notice" in block, "files": "viewArticleAttachFile" in block,
        })
    total = TOTAL.search(text_of(page))
    # 「총 N 건」 은 찾은 줄이 하나도 없으면 화면에 안 선다 — 그때 남는 줄은 낱말과 상관없이 오는 고정 공지뿐이라 센 수는 0 이다
    return {"total": int(total.group(1).replace(",", "")) if total else sum(not r["notice"] for r in rows), "rows": rows}


def parse_drafts(page: str) -> dict:
    """임시 · 예약보관함 화면 → {rows}. 줄마다 board · id · title · date · state(임시저장 · 예약저장 · 예약)."""
    rows = []
    for m in ROW.finditer(page):
        chk = CHK.search(m.group(1))
        if chk:
            key = row_key(chk.group(1))
            posted = DATE_CELL.search(m.group(1))
            state = DRAFT_STATE.search(text_of(m.group(1)))
            rows.append({"board": key.get("bbsId", ""), "id": key.get("articleId", ""), "title": row_title(key, m.group(1)),
                         "date": posted.group(1) if posted else "", "state": state.group(0) if state else ""})
    return {"rows": rows}


def form_value(page: str, name: str) -> str:
    """쓰기 창 폼의 ``<input id=name …>`` 값 — 칸의 속성 차례는 칸마다 다르다(제목 칸은 value 앞에 objtitle 이 선다)."""
    tag = re.search(rf'<input\b[^>]*\bid="{name}"[^>]*>', page)
    got = re.search(r'\bvalue="([^"]*)"', tag.group(0)) if tag else None
    return html.unescape(got.group(1)) if got else ""


def parse_write_form(page: str) -> dict:
    """쓰기 · 편집 창 폼 → {article_id, org_id, copy, title, html(숨은 content 칸의 저장된 본문 전문), end_date, notify_date, status, board}."""
    body = re.search(r'<textarea id="content" name="content"[^>]*>(.*?)</textarea>', page, re.S)
    return {"article_id": form_value(page, "articleId"), "org_id": form_value(page, "orgArticleId"), "copy": form_value(page, "articleCopyYn"),
            "title": form_value(page, "title"), "html": html.unescape(body.group(1)) if body else "",
            "end_date": form_value(page, "endDate"), "notify_date": form_value(page, "notifyDate"), "status": form_value(page, "status"),
            "board": form_value(page, "bbsId")}


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
            "period": pick(PERIOD), "html": unwrap(body.group(1)), "comments": parse_comments(page)}


def unwrap(content: str) -> str:
    """본문 칸 → 글의 HTML. 칸 전체가 한 행 한 칸의 감싸개 표면 그 칸 안만 낸다(``WRAPPER``) — 한 겹만 벗긴다."""
    wrapped = WRAPPER.fullmatch(content)
    return wrapped.group(1) if wrapped else content


class App:
    """게시판 한 판 — 사내 세션의 쿠키로 들어가 게시판 화면을 읽고 푼다."""
    def __init__(self, session_file: pathlib.Path | str, *, timeout: float = TIMEOUT):
        self._jar = ep_session.load_jar(session_file, missing=SessionMissing)
        self._open = ep_session.opener(self._jar).open   # 프록시 없이 · 리다이렉트는 안 따라간다
        self._timeout = timeout
        self._in = False

    def _raw(self, url: str, data: dict | list | None = None) -> bytes:
        """주소 하나를 (``data`` 를 주면 폼 POST 로) 열어 받은 바이트 — 넘김은 SessionExpired, 그 밖의 거절 · 닿지 못함은 AppError."""
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

    def _ask(self, url: str, data: dict | list | None = None) -> bytes:
        """게시판에 묻는 바이트 — 아직 안 들어갔으면 먼저 들어간다(``login``). 들어가기 밖의 모든 물음이 이 한 자리를 지난다."""
        if not self._in:
            self.login()
        return self._raw(url, data)

    def _get(self, url: str, data: dict | list | None = None) -> str:
        """게시판 화면 한 장의 글 — 로그인 창이 왔으면 ``SessionExpired``."""
        page = self._ask(url, data).decode("utf-8", "replace")
        if LOGGED_OUT in page[:300]:
            raise SessionExpired("게시판이 로그인 창을 냈다 — 사내 세션이 끊겼다")
        return page

    def login(self) -> None:
        """게시판에 들어간다 — SSO 넘김 화면의 토큰을 게시판에 넘기고, 받은 사용자 ID 를 뒤섞어(``scramble``) 내어 게시판 세션을 연다. 못 들어가면 SessionExpired."""
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
        """게시판 컨트롤러(``CONTROLLER``)에 폼 하나를 내고 받은 화면의 글."""
        return self._get(CONTROLLER, data)

    # ── 읽기 ────────────────────────────────────────────────────────────
    def tree(self, *, write: bool = False) -> list:
        """게시판 나무 전체 — [{id, name, path, folder}]. ``write`` 면 쓸 수 있는 게시판만(화면의 글쓰기 고름 상자와 같다)."""
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
                 until: str = "", page: int = 1, count: int = 20, filters: dict | None = None, without: str = "") -> dict:
        """게시판 하나(묶음이면 그 아래 다)의 글 — 낱말을 주면 ``fields`` 칸에서 찾는다. 뿌리면 모든 게시판.

        ``filters`` 는 화면 [추가기능 > 필터링] 의 칸(``notifyYn`` 공지감추기 · ``unreadArticleYn`` 안읽은게시물만 · ``myArticleYn`` 내게시물만)에
        "true" 를 준다. ``without`` 을 주면 화면의 상세검색(listSearchArticle)으로 묻는다 — 제외할 단어는 그 명령에서만 걸린다"""
        if without:
            return self.detail_search(bbs_id, words=words, fields=fields, since=since, until=until, page=page, count=count, without=without)
        data = {"facade": "BBSArticleFacade", "command": "listArticle", "nextpage": "/bbs/articleGenList.jsp",
                "categoryId": "BBS_ALL", "bbsId": bbs_id, "paging_listcnt": str(count), "currpage_no": str(page),
                "srchStartDate": since, "srchEndDate": until or date.today().isoformat()}   # 끝 날을 비우면 게시판이 화면의 기본 기간만 본다
        if words:
            data.update(srchKeyword=words, srchChkConditionList=CONDITION_SEP.join(CONDITION + f for f in fields), searchMode="Y")
        data.update({k: "true" for k in filters or {}})
        return parse_rows(self.call(data))

    def detail_search(self, bbs_id: str, *, words: str, fields: tuple, since: str, until: str, page: int, count: int, without: str) -> dict:
        """화면 상세검색(listSearchArticle) — ``srchTargetCurMap=N`` 이 「하위포함」이다(화면이 뜻을 거꾸로 쓴다). 고정 공지를 따로 안 세우고
        낱말이 든 고정 공지도 찾은 줄로 낸다. 줄 꼴은 목록과 같고 날짜에 해가 없다(``MM-DD HH:MM``)."""
        data = {"facade": "BBSArticleFacade", "command": "listSearchArticle", "nextpage": "/bbs/articleSrchList.jsp", "categoryId": "BBS_ALL",
                "srchDetailSearchYn": "Y", "srchBBSId": bbs_id, "bbsId": bbs_id, "srchTargetCurMap": "N",
                "paging_listcnt": str(count), "currpage_no": str(page), "srchStartDate": since, "srchEndDate": until or date.today().isoformat(),
                "srchKeyword": words, "srchChkConditionList": CONDITION_SEP.join(CONDITION + f for f in fields), "srchExceptWord": without}
        return parse_rows(self.call(data))

    def readers(self, bbs_id: str, article_id: str, *, page: int = 1, count: int = 100) -> dict:
        """글 하나의 열람내역(화면의 조회수 링크) — 읽기만 한다. 연 사람의 읽음 · 조회수는 안 바뀌었다(``references/SOURCES.md``)."""
        return parse_readers(self.call({"facade": "BBSArticleFacade", "command": "listArticleReadUser", "nextpage": "/bbs/pop/bbsReadUserListPop.jsp",
                                        "articleId": article_id, "bbsId": bbs_id, "paging_listcnt": str(count), "currpage_no": str(page)}))

    def options(self, bbs_id: str) -> dict:
        """게시판 하나의 옵션(쓰기 창이 칸을 켜고 끄는 값 — ``termModifyYn`` 게시기한을 바꾸게 하나 · ``dispPeriod`` 기본 게시 기간 …)."""
        raw = self._get(f"{ROOT}/AjaxController?facade=BBSFacade&command=getBBSOptionAjax&categoryId=BBS_ALL&bbsId={urllib.parse.quote(bbs_id)}")
        try:
            return json.loads(raw)["bbsOptVO"]
        except (ValueError, KeyError, TypeError) as exc:
            raise AppError(f"게시판 옵션 답이 잰 꼴이 아니다: {bbs_id}") from exc

    def article(self, bbs_id: str, article_id: str) -> dict:
        """글 한 건 — 조회수를 안 올리고(``transaction_yn=N``) 글 화면을 풀어 바로가기(link)를 붙인다. 글이 안 열리면 NotFound."""
        page = self.call({"facade": "BBSArticleFacade", "command": "viewArticle", "nextpage": "/bbs/articleView.jsp",
                          "transaction_yn": "N", "articleId": article_id, "articleBbsId": bbs_id, "categoryId": "BBS_ALL", "popYn": "Y"})
        return dict(parse_article(page), link=article_link(bbs_id, article_id))

    def files(self, article_id: str) -> list:
        """글 하나의 첨부 목록 — [{id, name, size}]."""
        return parse_files(self._get(f"{ROOT}/common/fileattach/download.jsp?refId={urllib.parse.quote(article_id)}"
                                     "&downYn=Y&innoFDId=innoFDId&fileTitle="))

    def image(self, src: str) -> bytes:
        """본문 ``<img src>`` 하나의 바이트 — 상대 주소는 글 화면(CONTROLLER)에 대어 풀고, 게시판 호스트 · 포트의 잰 꼴(IMAGE_PATH 에
        fileId 하나)만 묻는다 — 그 밖이면 ``Refused``(게시판 호스트의 다른 길은 사내 세션을 싣고 무엇을 할지 모른다). 게시판이 대는
        Content-Type 은 그림 꼴을 안 말해, 꼴은 부르는 쪽이 바이트 머리로 가린다."""
        url = urllib.parse.urljoin(CONTROLLER, src.strip())
        parts = urllib.parse.urlsplit(url)
        host = (parts.hostname or "").lower()
        if host != BOARD_HOST:
            raise Refused(f"게시판 밖의 그림이라 묻지 않는다({host or '주소 없음'}) — 화면에서 본다")
        keys = [k for k, _ in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)]
        if f"{parts.scheme}://{parts.netloc}".lower() != ROOT_ORIGIN or parts.path != IMAGE_PATH or keys != ["fileId"]:
            raise Refused(f"게시판 본문 그림의 잰 꼴(DownController.do?fileId=)이 아니라 묻지 않는다({parts.path[:60]}) — 화면에서 본다")
        data = self._ask(url)
        if LOGGED_OUT.encode() in data[:300]:
            raise SessionExpired("그림 대신 로그인 창이 왔다 — 사내 세션이 끊겼다")
        return data

    def download(self, file_id: str) -> bytes:
        """첨부 하나의 바이트."""
        return self._ask(f"{ROOT}/DownController?fileId={urllib.parse.quote(file_id)}&down_filename=f")

    def draft_form(self, bbs_id: str, article_id: str) -> dict:
        """임시글 편집 창의 폼(writeArticle EDIT · TEMP)을 GET 으로 — 창을 안 띄운다. 숨은 content 칸이 저장된 본문 전문을 든다."""
        page = self.call(write_params("draft", bbs_id, article_id))
        got = parse_write_form(page)
        if got["article_id"] != article_id:
            raise NotFound(f"임시글 {article_id} 의 편집 폼이 안 열렸다 — drafts 로 id 와 게시판을 본다")
        return got

    def copy_form(self, bbs_id: str, article_id: str) -> dict:
        """화면 리본 「재활용」 이 여는 창(writeArticle EDIT · articleCopyYn=Y)의 폼을 GET 으로 — 원글은 안 건드리고 아무것도 안 생긴다.
        {title, html, end_date, …, article_id(빈 값이어야 새 글이다) · copy(Y)}. 그 글이 아니면 NotFound."""
        page = self.call(write_params("copy", bbs_id, article_id))
        got = parse_write_form(page)
        if got["org_id"] != article_id or got["copy"] != "Y" or got["article_id"]:
            raise NotFound(f"글 {article_id} 의 재활용 폼이 안 열렸다 — 게시판 id 와 글 id 가 맞는지 본다")
        return got

    def drafts(self) -> dict:
        """임시 · 예약보관함 — 줄마다 board · id · title · date · state."""
        return parse_drafts(self.call({"facade": "BBSArticleFacade", "command": "listTempArticle", "nextpage": "/bbs/articleTempList.jsp",
                                       "categoryId": "BBS_ALL", "menuGbn": "TEMP", "paging_listcnt": "50", "currpage_no": "1"}))
