"""사내 메일함(Lotus Notes · HCL Domino 웹메일)에서 받은 메일을 읽는다 — 표준 라이브러리만 쓰는 파일 하나.

무엇을 하나
    받은편지함의 목록 · 본문(평문 · HTML) · 첨부를 받는다. **메일의 읽음 표시를 바꾸지 않는다** —
    사람이 웹메일에서 열기 전까지 그 메일은 「안 읽음」으로 남는다.

어떻게 부르나
    로그인은 이 파일이 하지 않는다. 곁의 ``mail_login.js`` 가 브라우저로 사내 SSO 를 넘고
    세션 쿠키를 파일로 남기면, 이 파일은 그 쿠키로 메일 서버에 묻는다::

        import inbox

        box = inbox.Mailbox.from_env()                 # 설정이 틀리면 여기서 MailboxConfigError
        for mail in box.list(count=20):                # 새것부터
            if mail.unread:
                text = box.body(mail, "text")          # 평문 — 없으면 None
                for name in mail.attachments:
                    data = box.attachment(mail, name)  # bytes

무엇을 내나
    ``list`` 는 ``Mail`` 목록을 낸다(제목 · 보낸 사람 · 날짜 · 크기 · 중요도 · 첨부 이름 · 읽음).
    ``body`` 는 글자, ``attachment`` 는 bytes 를 낸다. 세션이 끊겼으면 ``SessionExpired`` —
    ``mail_login.js`` 를 다시 돌리라는 뜻이다. 서버가 답을 안 주면 ``MailboxError``.
    무엇을 했는지는 ``logging`` 으로 남긴다(로거 이름은 이 모듈 이름).

환경변수
    ``MAILBOX_URL``      메일함 주소 — 웹메일 주소창의 ``…/221682.nsf`` 까지(그 뒤는 버린다). 꼭 준다
    ``MAILBOX_COOKIES``  ``mail_login.js`` 가 남긴 쿠키 파일    기본 ``~/.mailbox-session.json``
    ``MAILBOX_VIEW``     받은편지함 보기 이름                  기본 ``XML_Inbox``
    ``MAILBOX_TIMEOUT_SECONDS``  응답 시한(초)                 기본 ``30``

사내 메일함에서 잰 것 — 어기면 조용히 망가진다. 원본은 사내 환경 기록
(``~/.claude/posco/ENV-posco.md`` 「네트워크 접근」)이다
    * IMAP · POP3 는 닫혀 있다. 열린 길은 웹(80 · 443)뿐이고, 앞에 사내 SSO 가 선다
    * ⚠ **문서를 여는 주소(``?OpenDocument``)를 부르면 그 메일이 읽음으로 바뀐다.** 목록
      (``?ReadViewEntries``) · 본문 조각(``/Body/M…?OpenElement``) · 첨부(``/$FILE/``)는 안 바꾼다.
      그래서 이 파일은 ``?OpenDocument`` · ``?EditDocument`` 를 짓지 않고, 지으려 하면 막는다
    * 세션이 끊기면 서버가 오류 대신 **200 에 SSO 로 보내는 HTML** 을 준다 — 상태 코드로는
      못 가린다. 답의 꼴(XML · 기대한 형식)로 가린다
    * 본문은 MIME 조각이다 — 평문 ``M1.1`` · HTML ``M1.2`` 가 흔한 꼴이다. 다른 꼴의 메일
      (평문만 · 서식 있는 Notes 문서)은 안 쟀다
    * 목록의 ``read`` 열이 읽음을 든다 — ``ico-nomail`` 이 안 읽음이다. 첨부 이름은
      ``attachment`` 열에 ``{}`` 로 이어 온다
"""

from __future__ import annotations

import http.cookiejar
import json
import logging
import os
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

DEFAULT_COOKIES = "~/.mailbox-session.json"
DEFAULT_VIEW = "XML_Inbox"
DEFAULT_TIMEOUT = 30.0

# 목록 열 이름 — 사내 웹메일 보기 XML_Inbox 의 열(실측)
COLUMN_SUBJECT, COLUMN_FROM, COLUMN_DATE = "xsubject", "xname", "xdate"
COLUMN_SIZE, COLUMN_IMPORTANCE = "xsize", "xImportance"
COLUMN_ATTACHMENTS, COLUMN_READ = "attachment", "read"
UNREAD_MARK = "ico-nomail"
ATTACHMENT_SEPARATOR = "{}"
# 본문 조각 — 평문 · HTML
BODY_PARTS = {"text": "M1.1", "html": "M1.2"}
# ⚠ 읽음 표시를 바꾸는 명령 — 이 파일은 이 주소를 짓지 않는다
MARKS_AS_READ = re.compile(r"[?&](opendocument|editdocument)\b", re.IGNORECASE)
_UNID = re.compile(r"^[0-9A-Fa-f]{32}$")

log = logging.getLogger(__name__)


class MailboxError(Exception):
    """메일함을 못 읽었다. 메시지가 사유다."""


class MailboxConfigError(MailboxError):
    """설정이 틀렸다 — 환경변수나 쿠키 파일. 묻기 전에 잡힌다."""


class SessionExpired(MailboxError):
    """세션이 끊겼다 — ``mail_login.js`` 로 다시 로그인한다."""


class _Missing(MailboxError):
    """그 주소에 아무것도 없다(HTTP 404) — 본문 조각이 없는 메일."""


@dataclass(frozen=True)
class Mail:
    """목록의 한 줄. ``unid`` 가 그 메일의 열쇠다."""
    unid: str
    subject: str
    sender: str
    date: str
    size: str
    importance: str
    attachments: tuple[str, ...]
    unread: bool


# ── 세션 ─────────────────────────────────────────────────────────────────

def _load_cookies(path: pathlib.Path) -> http.cookiejar.CookieJar:
    """``mail_login.js`` 가 남긴 Playwright 저장 상태(``{"cookies": [...]}``)를 쿠키 통으로 읽는다."""
    if not path.exists():
        raise MailboxConfigError(f"쿠키 파일이 없다: {path} — mail_login.js 를 먼저 돌린다")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MailboxConfigError(f"쿠키 파일이 깨졌다: {exc}") from exc
    cookies = data.get("cookies") if isinstance(data, dict) else None
    if not isinstance(cookies, list) or not cookies:
        raise MailboxConfigError(f"쿠키 파일에 쿠키가 없다: {path}")

    jar = http.cookiejar.CookieJar()
    now = time.time()
    for item in cookies:
        expires = item.get("expires", -1)
        if expires not in (-1, None) and expires < now:
            continue
        domain = item["domain"]
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name=item["name"], value=item["value"], port=None, port_specified=False,
            domain=domain, domain_specified=True, domain_initial_dot=domain.startswith("."),
            path=item.get("path", "/"), path_specified=True, secure=bool(item.get("secure")),
            expires=None if expires in (-1, None) else int(expires), discard=expires in (-1, None),
            comment=None, comment_url=None, rest={}))
    return jar


class Mailbox:
    """메일함 하나. 받는 것은 다 읽기 전용이다 — 읽음 표시를 바꾸는 주소는 짓지 않는다."""

    def __init__(self, url: str, cookies_file, *, view: str = DEFAULT_VIEW,
                 timeout: float = DEFAULT_TIMEOUT):
        match = re.match(r"^(https?://[^/]+/.+?\.nsf)", url.strip(), re.IGNORECASE)
        if not match:
            raise MailboxConfigError(f"MAILBOX_URL 이 메일함 주소(…/이름.nsf)가 아니다: {url!r}")
        self.base = match.group(1)
        self.view = view
        self.timeout = timeout
        jar = _load_cookies(pathlib.Path(cookies_file).expanduser())
        # 리다이렉트를 따라가지 않는다 — 끊긴 세션은 SSO 로 보내는데, 따라가면 쿠키가 SSO 에 실린다
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar), _NoRedirect())

    @classmethod
    def from_env(cls) -> Mailbox:
        """환경변수로 세운다. 틀린 값이면 MailboxConfigError."""
        url = os.environ.get("MAILBOX_URL", "").strip()
        if not url:
            raise MailboxConfigError("MAILBOX_URL 이 비어 있다 — 웹메일 주소의 …/이름.nsf 까지 준다")
        timeout_raw = os.environ.get("MAILBOX_TIMEOUT_SECONDS", "").strip() or str(DEFAULT_TIMEOUT)
        try:
            timeout = float(timeout_raw)
        except ValueError:
            timeout = 0.0
        if timeout <= 0:
            raise MailboxConfigError(f"MAILBOX_TIMEOUT_SECONDS 가 양수가 아니다: {timeout_raw!r}")
        return cls(url, os.environ.get("MAILBOX_COOKIES", "").strip() or DEFAULT_COOKIES,
                   view=os.environ.get("MAILBOX_VIEW", "").strip() or DEFAULT_VIEW, timeout=timeout)

    # ── 묻기 ────────────────────────────────────────────────────────────

    def _get(self, path: str) -> tuple[bytes, str]:
        """메일함 아래 ``path`` 를 GET 한다. 내는 것 — (본문, content-type)."""
        url = self.base + path
        if MARKS_AS_READ.search(url):
            raise MailboxError(f"읽음 표시를 바꾸는 주소라 묻지 않는다: {url}")
        try:
            with self._opener.open(url, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except _Redirected as exc:
            raise SessionExpired(f"세션이 끊겼다(→ {exc.location}) — mail_login.js 로 다시 로그인한다") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise SessionExpired(f"메일 서버가 거절했다(HTTP {exc.code}) — 다시 로그인한다") from exc
            if exc.code == 404:
                raise _Missing(url) from exc
            raise MailboxError(f"메일 서버가 HTTP {exc.code} 를 냈다: {url}") from exc

    def list(self, count: int = 30, start: int = 1) -> list[Mail]:
        """받은편지함을 새것부터 ``count`` 통. ``start`` 는 1 부터 센 자리."""
        body, kind = self._get(f"/{urllib.parse.quote(self.view)}?ReadViewEntries"
                               f"&count={int(count)}&start={int(start)}")
        if "xml" not in kind.lower():
            raise SessionExpired(f"목록 대신 {kind or '알 수 없는 꼴'} 가 왔다 — 세션이 끊긴 것이다")
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise MailboxError(f"목록 XML 을 못 읽었다: {exc}") from exc
        mails = [_mail(entry) for entry in root.iter("viewentry")]
        log.info("목록: %d통 · 안 읽음 %d", len(mails), sum(m.unread for m in mails))
        return mails

    def body(self, mail: Mail | str, kind: str = "text") -> str | None:
        """본문 — ``kind`` 는 "text"(평문) · "html". 그 꼴의 조각이 없으면 None."""
        if kind not in BODY_PARTS:
            raise MailboxConfigError(f"본문 꼴은 text · html 가운데 하나다: {kind!r}")
        unid = _unid(mail)
        try:
            data, content_type = self._get(f"/0/{unid}/Body/{BODY_PARTS[kind]}?OpenElement")
        except _Missing:
            return None
        expected = "text/plain" if kind == "text" else "text/html"
        if expected not in content_type.lower():
            # 끊긴 세션의 SSO 페이지도 text/html 로 온다 — html 꼴에서는 아래 표지로 가린다
            return None
        text = data.decode(_charset(content_type), errors="replace")
        if kind == "html" and _looks_like_login(text):
            raise SessionExpired("본문 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        return text

    def attachment(self, mail: Mail | str, name: str) -> bytes:
        """첨부 하나를 바이트 그대로 받는다."""
        unid = _unid(mail)
        data, content_type = self._get(f"/0/{unid}/$FILE/{urllib.parse.quote(name)}")
        if "text/html" in content_type.lower() and _looks_like_login(data.decode("utf-8", "replace")):
            raise SessionExpired("첨부 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        log.info("첨부: %s · %d bytes", name, len(data))
        return data


# ── 풀기 ─────────────────────────────────────────────────────────────────

def _column(entry: ET.Element, name: str) -> str:
    for data in entry.iter("entrydata"):
        if data.get("name") == name:
            return " ".join(t.strip() for t in data.itertext() if t.strip())
    return ""


def _mail(entry: ET.Element) -> Mail:
    attachments = _column(entry, COLUMN_ATTACHMENTS)
    return Mail(
        unid=entry.get("unid", ""),
        subject=_column(entry, COLUMN_SUBJECT),
        sender=_column(entry, COLUMN_FROM),
        date=_column(entry, COLUMN_DATE),
        size=_column(entry, COLUMN_SIZE),
        importance=_column(entry, COLUMN_IMPORTANCE),
        attachments=tuple(n for n in attachments.split(ATTACHMENT_SEPARATOR) if n),
        unread=UNREAD_MARK in _column(entry, COLUMN_READ),
    )


def _unid(mail: Mail | str) -> str:
    unid = mail.unid if isinstance(mail, Mail) else mail
    if not _UNID.match(unid or ""):
        raise MailboxConfigError(f"메일 열쇠(unid)가 아니다: {unid!r}")
    return unid


def _charset(content_type: str) -> str:
    match = re.search(r"charset=([\w-]+)", content_type, re.IGNORECASE)
    return match.group(1) if match else "utf-8"


def _looks_like_login(text: str) -> bool:
    return "swpsso" in text or "EP_CERTIFY" in text


class _Redirected(Exception):
    def __init__(self, location: str):
        super().__init__(location)
        self.location = location


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise _Redirected(newurl)
