"""사내 메일함(Lotus Notes · HCL Domino 웹메일)을 읽는 손과, 메일함을 바꾸는 이름 붙은 손 둘 — 표준 라이브러리만 쓰는 파일 하나.

무엇을 하나
    받은편지함 · 쓰는 사람이 지은 폴더 · 보낸편지함의 목록, 모든편지함의 받는 꼴 · 중요도, 받는 사람 목록 보기, 본문(HTML ·
    평문), 첨부, 사내 주소록 찾기, 세션 확인을 받는다. 이 길(읽기 길)은 **메일의 읽음 표시를 바꾸지 않는다** — 읽음을 안
    바꾸는 것으로 잰 주소 꼴만 묻고, 그 밖의 주소는 서버에 닿기 전에 ``ChangeRefused`` 로 막는다. 사람이 웹메일에서 열기
    전까지 그 메일은 「안 읽음」으로 남는다.

    메일함을 바꾸는 손은 읽음으로(``mark_read``) · 안 읽음으로(``mark_unread``) 둘뿐이고, 이름 붙은 함수 하나씩이다.
    읽기 길은 이 둘을 부르지 않는다.

어떻게 부르나
    로그인은 이 파일이 하지 않는다. 곁의 ``mail_login.js`` 가 브라우저로 사내 SSO 를 넘고 세션 쿠키를 파일로 남기면
    (Playwright 저장 상태 꼴 ``{"cookies": [...]}`` — 다른 손이 같은 꼴로 남겨도 된다), 이 파일은 그 쿠키로 메일 서버에
    묻는다::

        import inbox

        box = inbox.Mailbox.from_env()                  # 설정이 틀리면 여기서 MailboxConfigError
        for mail in box.list(count=20):                 # 받은편지함 — 새것부터
            if mail.unread:
                html = box.body(mail)                   # HTML 본문 — 꼴과 상관없이 한 길 · 없으면 None
                text = box.body(mail, "text")           # 평문 조각 — 없으면 None
                for a in mail.attachments:
                    if not a.ecm:                       # ECM 첨부는 이름 · 확장자 · 크기만 있다
                        data = box.attachment(mail, a)  # bytes

        for folder in box.folders():                    # 쓰는 사람이 지은 폴더 — 시스템 폴더는 안 낸다
            got = box.list_folder(folder, count=200)    # 그 폴더 — 새것부터 · 줄마다 folder 에 경로
        marks = box.list_all(count=200)                 # 모든편지함의 받는 꼴 · 중요도 — 보기가 없으면 None
        sent = box.list_sent(count=100)                 # 보낸편지함 — 받는 사람은 그 목록의 수신인 열
        lists = box.recipient_lists(count=600)          # unid → 받는 사람 목록 · 보기가 없으면 None
        people = box.find_people("me@company.com", "<회사>(<코드>)")   # 사내 주소록 — 밖의 주소는 빈 목록
        box.session_alive()                             # 메일을 안 건드리는 세션 확인

    주소 · 쿠키 파일을 환경변수 대신 바로 줄 때는 ``inbox.Mailbox(url, cookies_file)`` 다.

무엇을 내나
    목록은 ``Entry`` · ``SentEntry`` 를, 폴더는 ``Folder`` 를, 모든편지함은 ``Marks`` 를, 받는 사람 목록은 ``Recipient``
    묶음을, 주소록은 ``DirectoryPerson`` 을 낸다. 보낸 사람은 ``Sender``(이름 · 주소 · 영문 이름), 첨부 이름은
    ``AttachmentName`` 이다. 시각은 메일함이 준 글자 그대로 낸다 — 시각으로 푸는 일은 부르는 쪽이 한다. ``body`` 는 글자,
    ``attachment`` 는 bytes 를 낸다.

    세션이 끊겼으면 ``SessionExpired`` — 다시 로그인해 쿠키를 새로 남기라는 뜻이다. 읽기 길이 메일함을 바꿀 주소(또는
    읽기 전용으로 잰 꼴 밖의 주소)를 지으려 하면 ``ChangeRefused``. 설정 · 인자가 틀리면 ``MailboxConfigError``, 서버가
    답을 안 주면 ``MailboxError``(셋 다 이것의 갈래다). 무엇을 했는지는 ``logging`` 으로 남긴다(로거 이름은 이 모듈
    이름) — 셈과 방향만 싣고 본문 · 제목 · 이름 · 주소 · 첨부 이름은 안 싣는다.

메일함을 바꾸는 손 둘 — 언제 부르나는 부르는 쪽이 정한다
    ``mark_read`` · ``mark_unread`` 는 쓰는 사람의 메일함을 바꾼다. 사람이 그 메일 하나를 두고 「읽음으로 · 안 읽음으로」를
    분명히 고른 뒤에만 부른다 — 회차 · 예약 작업 · 모델의 판단이 스스로 부르면 사람이 새 메일을 못 알아본다. 이 파일은
    그 확인을 대신하지 않는다. 손 하나는 메일 하나만 바꾸고, 그 두 꼴 밖의 주소는 ``ChangeRefused`` 로 막는다.

환경변수(``from_env``)
    ``MAILBOX_URL``              메일함 주소 — 웹메일 주소창의 ``…/<번호>.nsf`` 까지(그 뒤는 버린다). 꼭 준다
    ``MAILBOX_COOKIES``          세션 쿠키 파일                 기본 ``~/.mailbox-session.json``
    ``MAILBOX_VIEW``             받은편지함 보기 이름           기본 ``XML_Inbox``
    ``MAILBOX_TIMEOUT_SECONDS``  응답 시한(초)                  기본 ``30``

사내 메일함에서 잰 것 — 어기면 조용히 망가진다. 바탕 사실의 원본은 사내 환경 기록(``~/.claude/posco/ENV-posco.md``
「네트워크 접근」)이고, 주소 · 꼴마다 잰 판(셈 · 못 잰 까닭)은 그 앱 저장소(mail-secretary)의 ``docs/company-facts.md`` 와
회사 확인 대장(그 저장소 이슈 #9)이 든다 — 줄 끝 괄호가 그 대장의 줄이다
    * IMAP · POP3 는 닫혀 있다. 열린 길은 웹(80 · 443)뿐이고, 앞에 사내 SSO 가 선다
    * ⚠ **문서를 여는 주소(``?OpenDocument`` · ``?EditDocument``)를 부르면 그 메일이 읽음으로 바뀌고, ``ag_read_cancel`` 은
      안 읽음으로 바꾼다.** 목록(``?ReadViewEntries``) · 본문(``/0/<unid>/Body?OpenField`` · 조각 ``/Body/M…?OpenElement``) ·
      첨부(``/$FILE/``) · 보기 목록 · 주소록 · 세션 확인은 안 바꾼다. 그래서 읽기 길은 그 꼴(``_read_only``)에 맞는 주소만
      묻는다 — 닫힌 목록이라, 새 꼴은 읽음을 안 바꾸는 것을 잰 뒤 여기에 더해야 묻는다 (A · A2)
    * 세션이 끊기면 서버가 오류 대신 **200 에 SSO 로 보내는 HTML** 을 준다 — 상태 코드로는 못 가린다. 답의 꼴(XML · JSON ·
      기대한 형식)과 SSO 로 보내는 스크립트로 가린다. 낱말 「swpsso」만으로는 안 가른다 — 본문에 SSO 주소를 적은 사내 안내를
      끊긴 세션으로 읽는다. 리다이렉트는 따라가지 않는다 — 따라가면 쿠키가 SSO 에 실린다
    * 받은편지함 목록의 ``read`` 열 — ``ico-nomail`` 이 안 읽음이다(되돌린 메일은 ``z^ico-nomail``). ``ico-okmail`` 읽음 ·
      ``ico-post`` 회신함 · ``ico-remail`` 전달함은 다 읽은 것이다 (A · D)
    * 보낸 사람 열 ``xname`` — 사내 메일은 ``<이름>-=spl=-<이름> &lt;<주소>&gt;-ENG-<영문>-=spl=-<영문>&lt;<주소>&gt;`` 이
      XML 안에서 한 번 더 이스케이프돼(``&amp;lt;``) 온다. 밖의 메일 · 시스템은 주소만 온다 (A)
    * 받는 꼴 열 ``xrtype`` — ``T`` 받는사람 · ``C`` 참조 · ``G`` 받는 사람 목록 밖의 그룹 · 배포 목록 (A)
    * 받은 메일의 받는 사람은 받은편지함 목록에 없고(``SendTo?OpenField`` 는 501) 보기 ``!전체목록추출용`` 의 ``$102``
      열이 든다 — 받는사람과 참조를 합친 한 글줄이고 사람마다 Notes 이름 · ``<이름> <주소>`` · ``<ID>(<약칭>)`` · 주소만
      꼴이 섞인다. 기본 정렬이 날짜순이 아니라 ``&ResortDescending=1`` 로 날짜 내림차순을 받는다. 보기의 unid 는
      ``/api/data/collections`` 에서 제목으로 찾는다 — 이 보기 이름은 한 메일함으로만 쟀다 (A)
    * 본문 ``/0/<unid>/Body?OpenField`` 는 조각 꼴(평문만 · 평문+HTML · ``multipart/related``)과 상관없이 HTML 본문을 한 번에
      준다. 조각 ``/Body/M1.1?OpenElement`` 는 평문 · HTML 둘을 든 메일의 평문이다. 다른 꼴(``multipart/related`` 는 본문이
      ``M1.1.1``)의 ``M1.1`` 은 안 쟀다 — 그 자리에 ``text/plain`` 이 아닌 것이 오면 평문 조각은 없는 것으로 낸다 (A)
    * 첨부 이름은 ``attachment`` 열에 ``{}`` 로 이어 온다. 큰 첨부는 ECM 을 가리키는 ``<원래 이름>(<확장자>_<크기>KB).html``
      이고, 그 파일은 받지 않는다(이름 · 확장자 · 크기만 쓴다 — 파일은 ECM 화면에서만 받아진다)
    * 받은편지함 보기(``XML_Inbox``)는 받은편지함만 든다 — 쓰는 사람의 규칙이 하위 폴더로 옮긴 메일은 그 폴더의 보기에만 있다 (A2)
    * 폴더 목록은 보기 목록(``/api/data/collections``)의 ``@folder: true`` 항목이다. 시스템 폴더(``($Inbox)`` · ``($Trash)`` ·
      ``(Drafts)`` · ``(Sent)`` · ``($Alarms)`` · ``(TrashBackup)`` · ``(규칙)`` · ``(폴더템플릿)``)는 제목이 ``(`` 로 시작한다.
      쓰는 사람이 지은 폴더의 제목(``@title``)은 ``부모\\자식`` 꼴로 경로를 다 든다 — 쉼표 · 점이 든 이름이 있다. 보기 목록에는
      제목이 겹치는 항목도 있어(폴더는 아니었다) 보기를 제목으로 찾을 때는 폴더를 뺀다 (A2)
    * 폴더마다의 보기는 **unid 로만 열린다**(``/<unid>?ReadViewEntries`` — 제목을 넣으면 0줄). 기본 정렬이 날짜 내림차순이고
      ``count`` 는 1000에서 잘린다. 열이 받은편지함과 달라 받는 꼴(``xrtype``) · 중요도(``xImportance``) · 관련 문서
      (``xrelatedid``)가 없고 ``nh_read`` · ``LOCALSAVE`` · ``Security`` 가 있다 — 받는 꼴 · 중요도는 모든편지함에서 unid 로 채운다 (A2)
    * 모든편지함(``XML_모든편지함`` — 이 보기 이름은 한 메일함으로만 쟀다)은 받은 것 · 보낸 것 · 폴더를 다 든다. 기본 정렬이
      섞여 있어 ``&ResortDescending=1`` 로 날짜 내림차순을 받는다 — 안 붙이면 창에서 끊지 못한다. 한 번에 받아서만 쟀다 —
      ``start`` 로 장을 넘길 때 차례가 이어지는지는 안 쟀다 (A2 · A4)
    * ⚠ **모든편지함의 폴더 열 ``xfoldername`` 은 폴더의 진본이 아니다** — 하위 폴더는 끝 이름만 오고, 어느 폴더 보기에도 없는
      메일이 폴더 이름을 들고 있고, 받은편지함 메일이 폴더 이름을 들기도 한다. 그래서 그 열은 안 읽는다 — 폴더는 폴더 보기가 든다 (A2)
    * 보낸편지함 보기 ``XML_Sent`` 는 받은편지함과 같은 ``?ReadViewEntries`` 이고, 그 보기의 ``xname`` 열이 수신인이다
    * 주소록 ``/common/profile.nsf/ag_org_search_json?OpenAgent`` 는 이름 · 메일 · 사번으로 찾고 밖의 주소는 0건이다.
      ``company`` 는 조직도 고름 상자의 값(``<회사>(<코드>)``)이고 메일함마다 다르다
    * 세션 확인 ``/common/lib_f.nsf/checksessionstatus?Openpage`` → ``{"status":"login"}`` — 웹메일이 수십 초마다 부르는
      주소이고 메일을 안 건드린다. 세션이 끊긴 때의 이 주소의 답은 안 쟀다 — 그 꼴이 아니면 다 「끊겼다」로 본다 (C)
    * 읽음으로는 ``/<db>/XML_Inbox/<unid>?OpenDocument``, 안 읽음으로는 ``/<db>/ag_read_cancel?OpenAgent&docid=<unid>&imapuser=0``
      (200 · 빈 HTML)이다. 받은편지함 메일로만 쟀다 — 폴더에만 있는 메일에 읽음으로의 주소가 먹는지는 안 쟀다 (D · A3)
"""

from __future__ import annotations

import html
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
DEFAULT_TIMEOUT = 30.0

# 보기 — 이름은 실측(받은편지함 · 보낸편지함 · 받는 사람 목록 · 모든편지함)
INBOX_VIEW = "XML_Inbox"
SENT_VIEW = "XML_Sent"
RECIPIENT_VIEW_TITLE = "!전체목록추출용"
ALL_VIEW_TITLE = "XML_모든편지함"
SYSTEM_FOLDER_MARK = "("          # 시스템 폴더의 제목은 이 글자로 시작한다
FOLDER_SEPARATOR = "\\"           # 폴더 제목의 부모 · 자식 가름

# 받은편지함 목록 열
COLUMN_SUBJECT, COLUMN_FROM, COLUMN_DATE, COLUMN_DATE_SORT = "xsubject", "xname", "xdate", "$91"
COLUMN_SIZE, COLUMN_IMPORTANCE, COLUMN_ROLE = "xsize", "xImportance", "xrtype"
COLUMN_ATTACHMENTS, COLUMN_READ, COLUMN_RELATED = "attachment", "read", "xrelatedid"
# 보낸편지함 목록 열 — 이 보기의 xname 은 수신인이다
SENT_COLUMN_TO = "xname"
# 받는 사람 목록 보기의 열 — 날짜 · 수/발신 · 수신인 · 발신인
VIEW_COLUMN_DATE, VIEW_COLUMN_DIRECTION, VIEW_COLUMN_TO, VIEW_COLUMN_FROM = "$101", "$91", "$102", "$103"

UNREAD_MARK = "ico-nomail"
ATTACHMENT_SEPARATOR = "{}"
SPLIT_MARK, ENG_MARK = "-=spl=-", "-ENG-"
# ECM 을 가리키는 큰 첨부 — <원래 이름>(<확장자>_<크기>KB).html
ECM_ATTACHMENT = re.compile(r"^(?P<name>.+)\((?P<ext>[0-9A-Za-z]+)_(?P<kb>\d+)KB\)\.html$", re.IGNORECASE)

# 본문 — HTML 은 꼴과 상관없는 한 길, 평문은 조각 하나
BODY_KINDS = ("html", "text")
BODY_TEXT_PART = "M1.1"

# ⚠ 읽음 표시를 바꾸는 명령 — 읽기 길은 이 주소를 짓지 않고, 지으려 하면 서버에 닿기 전에 막는다
MARKS_AS_READ = re.compile(r"[?&](opendocument|editdocument)\b", re.IGNORECASE)
# 메일함을 바꾸는 주소 전부 — 읽음으로 · 안 읽음으로(되돌리기)
CHANGES_MAILBOX = re.compile(r"[?&](opendocument|editdocument)\b|/ag_read_cancel\b", re.IGNORECASE)
_UNID = re.compile(r"^[0-9A-Fa-f]{32}$")
_HEX32 = r"[0-9A-Fa-f]{32}"

log = logging.getLogger(__name__)


class MailboxError(Exception):
    """메일함을 못 읽었다. 메시지가 사유다."""


class MailboxConfigError(MailboxError):
    """설정이 틀렸다 — 주소 · 쿠키 파일 · 인자. 묻기 전에 잡힌다."""


class SessionExpired(MailboxError):
    """세션이 끊겼다 — 다시 로그인해 쿠키 파일을 새로 남긴다(이 씨앗에서는 곁의 ``mail_login.js``)."""


class ChangeRefused(MailboxError):
    """읽기 길이 메일함을 바꿀 주소(또는 읽기 전용으로 잰 꼴 밖의 주소)를 지었다 — 서버에 닿기 전에 막았다."""


class _Missing(MailboxError):
    """그 주소에 아무것도 없다(HTTP 404) — 본문 · 조각이 없는 메일."""


@dataclass(frozen=True)
class Sender:
    """보낸 사람 열 하나를 푼 것. 밖의 메일은 주소만 차고 이름 · 영문 이름이 빈다."""
    name: str
    addr: str
    name_eng: str = ""


@dataclass(frozen=True)
class Recipient:
    """받는 사람 목록의 한 사람. 주소 없이 오는 사람은 ``notes`` 가 열쇠다 — Notes 이름(``CN=…/O=…``)이나 ``<ID>(<약칭>)``."""
    name: str
    addr: str
    notes: str = ""


@dataclass(frozen=True)
class AttachmentName:
    """목록의 첨부 이름 하나. ECM 첨부면 ``ecm`` 이 참이고 원래 이름 · 확장자 · 크기를 이름에서 뽑는다 — 파일은 받지 않는다.

    ``listed`` 는 목록이 준 글자 그대로다 — ``Mailbox.attachment`` 에는 이 값이나 이것 자체를 넘긴다.
    """
    listed: str
    name: str
    ext: str = ""
    size_kb: int | None = None
    ecm: bool = False


@dataclass(frozen=True)
class Entry:
    """받은편지함 · 폴더 목록의 한 줄. ``unid`` 가 그 메일의 열쇠다. 시각은 메일함이 준 글자 그대로다.

    ``folder`` 는 받은편지함이면 빈 글자, 폴더 보기에서 왔으면 그 폴더의 경로(``부모\\자식``)다. 폴더 줄은 받는 꼴 · 중요도 ·
    관련 문서가 빈다 — 그 보기에 열이 없다(``Mailbox.list_all`` 로 채운다).
    """
    unid: str
    subject: str
    sender: Sender
    date: str              # xdate — YYYY-MM-DD HH:MM:SS (서울)
    date_sort: str         # $91 — YYYYMMDDTHHMMSS,cc+09
    size: str
    importance: str
    role: str              # xrtype — T · C · G · 빈 글자
    attachments: tuple[AttachmentName, ...]
    unread: bool
    read_mark: str
    related: str = ""
    folder: str = ""


@dataclass(frozen=True)
class Folder:
    """쓰는 사람이 지은 폴더 하나. ``path`` 는 보기 목록의 제목 그대로(``부모\\자식``) — 보기는 ``unid`` 로만 열린다."""
    unid: str
    path: str


@dataclass(frozen=True)
class Marks:
    """모든편지함 한 줄에서 폴더 보기에 없는 열 — 받는 꼴(``xrtype``) · 중요도(``xImportance``). 시각은 창에서 끊는 데만 쓴다.

    폴더는 안 든다 — 이 보기의 폴더 열(``xfoldername``)은 경로가 아니다(머리말 「사내 메일함에서 잰 것」).
    """
    unid: str
    date: str
    date_sort: str
    role: str
    importance: str


@dataclass(frozen=True)
class SentEntry:
    """보낸편지함 목록의 한 줄. 받는 사람은 그 목록의 수신인 열을 푼 것이다."""
    unid: str
    subject: str
    recipients: tuple[Recipient, ...]
    date: str


@dataclass(frozen=True)
class DirectoryPerson:
    """사내 주소록의 한 사람. ``notes`` 는 Notes 이름(``key``) — 받는 사람 목록에서 그 사람을 알아보는 열쇠다."""
    email: str
    name: str
    name_eng: str
    notes: str
    user_id: str
    empno: str
    dept: str
    grade: str
    job_title: str
    company: str
    retired: bool


# ── 세션 ─────────────────────────────────────────────────────────────────

def _load_cookies(path: pathlib.Path) -> http.cookiejar.CookieJar:
    """로그인 손이 남긴 Playwright 저장 상태(``{"cookies": [...]}``)를 쿠키 통으로 읽는다. 시한이 지난 쿠키는 버린다."""
    if not path.exists():
        raise MailboxConfigError(f"쿠키 파일이 없다: {path} — 로그인해 세션 쿠키를 먼저 남긴다")
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
    """메일함 하나. 읽기 길의 손은 다 읽기 전용이다 — 메일함을 바꾸는 손은 ``mark_read`` · ``mark_unread`` 둘뿐이다."""

    def __init__(self, url: str, cookies_file, *, view: str = INBOX_VIEW, timeout: float = DEFAULT_TIMEOUT):
        """``url`` 은 ``…/<이름>.nsf`` 까지 든 메일함 주소(그 뒤는 버린다), ``view`` 는 ``list`` 가 읽는 받은편지함 보기다.

        주소 · 쿠키 파일이 틀리면 묻기 전에 ``MailboxConfigError``.
        """
        match = re.match(r"^(https?://[^/]+)(/.+?\.nsf)", url.strip(), re.IGNORECASE)
        if not match:
            raise MailboxConfigError(f"메일함 주소(…/이름.nsf)가 아니다: {url!r}")
        self.server, self.db_path = match.group(1), match.group(2)
        self.base = self.server + self.db_path
        self.view = view
        self.timeout = timeout
        self._collections: list[dict] | None = None
        jar = _load_cookies(pathlib.Path(cookies_file).expanduser())
        # 리다이렉트를 따라가지 않는다 — 끊긴 세션은 SSO 로 보내는데, 따라가면 쿠키가 SSO 에 실린다
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar), _NoRedirect())
        db = re.escape(self.db_path)
        # 읽기 길이 물을 수 있는 주소 꼴 — 다 읽음을 안 바꾸는 것으로 잰 꼴이다. 닫힌 목록이라 새 꼴은 여기에 더해야 묻는다
        self._read_only = tuple(re.compile(p, re.IGNORECASE) for p in (
            rf"^{db}/[^/?]+\?ReadViewEntries(&[\w$%.=-]*)*$",
            rf"^{db}/api/data/collections$",
            rf"^{db}/0/{_HEX32}/Body\?OpenField$",
            rf"^{db}/0/{_HEX32}/Body/M\d+(\.\d+)*\?OpenElement$",
            rf"^{db}/0/{_HEX32}/\$FILE/[^?#]+$",
            r"^/common/lib_f\.nsf/checksessionstatus\?Openpage$",
            r"^/common/profile\.nsf/ag_org_search_json\?OpenAgent(&[\w$%.()+=-]*)*$",
        ))

    @classmethod
    def from_env(cls) -> Mailbox:
        """환경변수로 세운다(머리말 「환경변수」). 틀린 값이면 MailboxConfigError."""
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
                   view=os.environ.get("MAILBOX_VIEW", "").strip() or INBOX_VIEW, timeout=timeout)

    # ── 묻기 ────────────────────────────────────────────────────────────

    def _get(self, path: str) -> tuple[bytes, str]:
        """읽기 길의 GET — 메일함 안의 ``path``(``/`` 로 시작한다). 서버 뿌리 아래(주소록 · 세션 확인)는 ``_get_server``.

        내는 것 — (본문, content-type). 읽기 전용으로 잰 꼴이 아니면 묻지 않고 ``ChangeRefused``.
        """
        return self._fetch_read_only(self.db_path + path)

    def _get_server(self, path: str) -> tuple[bytes, str]:
        """읽기 길의 GET — 메일함 밖, 같은 서버의 ``path``(주소록 · 세션 확인)."""
        return self._fetch_read_only(path)

    def _fetch_read_only(self, path: str) -> tuple[bytes, str]:
        url = self.server + path
        if MARKS_AS_READ.search(path):
            raise ChangeRefused(f"읽음 표시를 바꾸는 주소라 묻지 않는다: {url}")
        if CHANGES_MAILBOX.search(path):
            raise ChangeRefused(f"메일함을 바꾸는 주소라 묻지 않는다: {url}")
        if not any(p.match(path) for p in self._read_only):
            raise ChangeRefused(f"읽기 전용으로 잰 주소 꼴이 아니라 묻지 않는다: {url}")
        return self._open(url)

    def _open(self, url: str) -> tuple[bytes, str]:
        try:
            with self._opener.open(url, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except _Redirected as exc:
            raise SessionExpired(f"세션이 끊겼다(→ {exc.location}) — 다시 로그인한다") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise SessionExpired(f"메일 서버가 거절했다(HTTP {exc.code}) — 다시 로그인한다") from exc
            if exc.code == 404:
                raise _Missing(url) from exc
            raise MailboxError(f"메일 서버가 HTTP {exc.code} 를 냈다: {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise MailboxError(f"메일 서버에 못 닿았다: {exc}") from exc

    def _view(self, name_or_unid: str, count: int, start: int, *, descending: bool = False) -> ET.Element:
        query = f"?ReadViewEntries&count={int(count)}&start={int(start)}" + ("&ResortDescending=1" if descending else "")
        body, kind = self._get(f"/{urllib.parse.quote(name_or_unid)}{query}")
        if "xml" not in kind.lower():
            raise SessionExpired(f"목록 대신 {kind or '알 수 없는 꼴'} 가 왔다 — 세션이 끊긴 것이다")
        try:
            return ET.fromstring(body)
        except ET.ParseError as exc:
            raise MailboxError(f"목록 XML 을 못 읽었다: {exc}") from exc

    def list(self, count: int = 30, start: int = 1) -> list[Entry]:
        """받은편지함을 새것부터 ``count`` 통. ``start`` 는 1 부터 센 자리. 하위 폴더로 옮긴 메일은 안 든다(``list_folder``)."""
        root = self._view(self.view, count, start)
        entries = [_entry(e) for e in root.iter("viewentry")]
        log.info("받은편지함 목록: %d통 · 안 읽음 %d", len(entries), sum(e.unread for e in entries))
        return entries

    def list_sent(self, count: int = 30, start: int = 1) -> list[SentEntry]:
        """보낸편지함을 ``count`` 통. 받는 사람은 그 목록의 수신인 열을 푼다."""
        root = self._view(SENT_VIEW, count, start)
        entries = [SentEntry(unid=e.get("unid", ""), subject=_column(e, COLUMN_SUBJECT),
                             recipients=parse_people(_column(e, SENT_COLUMN_TO)), date=_column(e, COLUMN_DATE))
                   for e in root.iter("viewentry")]
        log.info("보낸편지함 목록: %d통", len(entries))
        return entries

    def _view_list(self) -> list[dict]:
        """보기 목록(``/api/data/collections``) — 이 메일함 손이 사는 동안 한 번만 받는다."""
        if self._collections is None:
            body, kind = self._get("/api/data/collections")
            text = body.decode(_charset(kind), errors="replace")
            try:
                views = json.loads(text)
            except json.JSONDecodeError as exc:
                if _looks_like_login(text):
                    raise SessionExpired("보기 목록 대신 로그인 페이지가 왔다 — 다시 로그인한다") from exc
                raise MailboxError(f"보기 목록 JSON 을 못 읽었다: {exc}") from exc
            if not isinstance(views, list):
                raise MailboxError("보기 목록이 배열이 아니다")
            self._collections = [v for v in views if isinstance(v, dict)]
        return self._collections

    def view_unid(self, title: str) -> str | None:
        """보기 제목으로 그 보기의 unid 를 찾는다 — 메일함마다 다를 수 있어 보기 목록에서 받는다. 없으면 None.

        폴더는 뺀다 — 쓰는 사람이 보기와 같은 이름의 폴더를 지어도 그 폴더를 보기로 읽지 않게.
        """
        unid = next((str(v.get("@unid") or "") for v in self._view_list()
                     if v.get("@title", "") == title and not _is_folder(v)), "")
        return unid if _UNID.match(unid) else None

    def folders(self) -> list[Folder]:
        """쓰는 사람이 지은 폴더 — 보기 목록의 폴더 가운데 시스템 폴더(제목이 ``(`` 로 시작)를 뺀 것, 경로 차례로."""
        found: dict[str, Folder] = {}
        for v in self._view_list():
            title, unid = str(v.get("@title") or ""), str(v.get("@unid") or "")
            if _is_folder(v) and title.strip() and not title.startswith(SYSTEM_FOLDER_MARK) and _UNID.match(unid):
                found.setdefault(unid, Folder(unid=unid, path=title))
        folders = sorted(found.values(), key=lambda f: folder_order(f.path))
        log.info("폴더: %d개", len(folders))
        return folders

    def list_folder(self, folder: Folder, count: int = 30, start: int = 1) -> list[Entry]:
        """그 폴더를 새것부터 ``count`` 통 — 줄마다 ``folder`` 에 그 폴더의 경로를 싣는다. 받는 꼴 · 중요도는 빈다."""
        if not _UNID.match(folder.unid or ""):
            raise MailboxConfigError("폴더 보기는 unid 로만 연다 — 제목으로 열면 0줄이 온다")
        root = self._view(folder.unid, count, start)
        entries = [_entry(e, folder=folder.path) for e in root.iter("viewentry")]
        log.info("폴더 목록: %d통 · 안 읽음 %d", len(entries), sum(e.unread for e in entries))
        return entries

    def list_all(self, count: int = 30, start: int = 1) -> list[Marks] | None:
        """모든편지함을 날짜 내림차순으로 ``count`` 줄 — 받는 꼴 · 중요도만 낸다. 보기가 이 메일함에 없으면 None."""
        unid = self.view_unid(ALL_VIEW_TITLE)
        if unid is None:
            log.warning("모든편지함 보기가 이 메일함에 없다 — 폴더 메일의 받는 꼴 · 중요도 없이 돈다")
            return None
        root = self._view(unid, count, start, descending=True)
        marks = [Marks(unid=e.get("unid", ""), date=_column(e, COLUMN_DATE), date_sort=_column(e, COLUMN_DATE_SORT),
                       role=_column(e, COLUMN_ROLE).upper(), importance=_column(e, COLUMN_IMPORTANCE))
                 for e in root.iter("viewentry")]
        log.info("모든편지함: %d줄", len(marks))
        return marks

    def recipient_lists(self, count: int) -> dict[str, tuple[Recipient, ...]] | None:
        """받는 사람 목록 보기를 날짜 내림차순으로 한 장(``count`` 줄) 받아 unid → 받는 사람 목록을 낸다.

        보기가 이 메일함에 없으면 None — 부르는 쪽은 목록 없이 돈다. 받은 것 · 보낸 것이 섞여 오고 둘 다 낸다.
        """
        unid = self.view_unid(RECIPIENT_VIEW_TITLE)
        if unid is None:
            log.warning("받는 사람 목록 보기가 이 메일함에 없다 — 목록 없이 돈다")
            return None
        root = self._view(unid, count, 1, descending=True)
        lists = {e.get("unid", ""): parse_people(_column(e, VIEW_COLUMN_TO)) for e in root.iter("viewentry")}
        log.info("받는 사람 목록: %d줄", len(lists))
        return lists

    def body(self, mail: Entry | str, kind: str = "html") -> str | None:
        """본문 — ``kind`` 는 "html"(기본 · 조각 꼴과 상관없는 한 길) · "text"(평문 조각). 그 꼴의 본문이 없으면 None.

        끊긴 세션의 로그인 화면이 오면 어느 꼴이든 ``SessionExpired`` 다 — 「본문 없음」으로 낮추지 않는다.
        """
        if kind not in BODY_KINDS:
            raise MailboxConfigError(f"본문 꼴은 {' · '.join(BODY_KINDS)} 가운데 하나다: {kind!r}")
        unid = _unid(mail)
        path = f"/0/{unid}/Body?OpenField" if kind == "html" else f"/0/{unid}/Body/{BODY_TEXT_PART}?OpenElement"
        try:
            data, content_type = self._get(path)
        except _Missing:
            return None
        text = data.decode(_charset(content_type), errors="replace")
        if _looks_like_login(text):
            raise SessionExpired("본문 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        if kind == "text" and "text/plain" not in content_type.lower():
            return None   # 평문 조각 자리에 다른 꼴이 왔다 — multipart/related 처럼 평문 조각이 없는 메일
        return text

    def attachment(self, mail: Entry | str, name: AttachmentName | str) -> bytes:
        """메일에 바로 붙은 첨부 하나를 바이트 그대로 받는다. ``name`` 은 ``AttachmentName`` 이나 목록이 준 이름 그대로다.

        ECM 첨부(``AttachmentName.ecm``)는 받지 않는다 — ``MailboxConfigError``.
        """
        unid = _unid(mail)
        listed = name.listed if isinstance(name, AttachmentName) else name
        if ECM_ATTACHMENT.match(listed):
            raise MailboxConfigError("ECM 첨부는 받지 않는다 — 이름 · 확장자 · 크기만 쓴다")
        data, content_type = self._get(f"/0/{unid}/$FILE/{urllib.parse.quote(listed)}")
        if "text/html" in content_type.lower() and _looks_like_login(data.decode("utf-8", "replace")):
            raise SessionExpired("첨부 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        log.info("첨부: %d bytes", len(data))
        return data

    def session_alive(self) -> bool:
        """메일을 안 건드리고 세션이 살아 있나 묻는다 — 웹메일이 수십 초마다 부르는 주소다. 살아 있으면 참.

        서버에 못 닿으면 ``MailboxError`` — 「끊겼다」와 「못 물었다」를 가른다.
        """
        try:
            data, kind = self._get_server("/common/lib_f.nsf/checksessionstatus?Openpage")
        except (SessionExpired, _Missing):
            return False
        try:
            answer = json.loads(data.decode(_charset(kind), errors="replace"))
        except json.JSONDecodeError:
            return False
        return isinstance(answer, dict) and answer.get("status") == "login"

    def find_people(self, search_key: str, company: str) -> list[DirectoryPerson]:
        """사내 주소록에서 이름 · 메일 · 사번으로 찾는다. 밖의 주소는 빈 목록이다 — 「사내 사람인가」로도 쓴다.

        ``company`` 는 조직도 고름 상자의 값(``<회사>(<코드>)``)이고 메일함마다 다르다 — 부르는 쪽이 설정에서 넘긴다.
        """
        if not search_key.strip() or not company.strip():
            raise MailboxConfigError("주소록 찾기에는 찾을 말과 회사 값이 다 있어야 한다")
        query = urllib.parse.urlencode({
            "type": "org", "dbpath": self.db_path.lstrip("/"), "company": company, "category": "",
            "search_key": search_key, "date": str(int(time.time() * 1000))}, safe="()")
        data, kind = self._get_server(f"/common/profile.nsf/ag_org_search_json?OpenAgent&{query}")
        text = data.decode(_charset(kind), errors="replace")
        try:
            answer = json.loads(text)
        except json.JSONDecodeError as exc:
            if _looks_like_login(text):
                raise SessionExpired("주소록 대신 로그인 페이지가 왔다 — 다시 로그인한다") from exc
            raise MailboxError(f"주소록 JSON 을 못 읽었다: {exc}") from exc
        users = answer.get("user", []) if isinstance(answer, dict) else []
        return [DirectoryPerson(
            email=u.get("email") or "", name=u.get("user_name") or "", name_eng=u.get("user_name_eng") or "",
            notes=u.get("key") or "", user_id=u.get("user_id") or "", empno=u.get("empno") or "",
            dept=u.get("dept_name") or "", grade=u.get("grade") or "", job_title=u.get("job_title") or "",
            company=u.get("company_name") or "", retired=str(u.get("is_retire") or "").upper() in ("Y", "1", "TRUE"))
            for u in users if isinstance(u, dict)]

    # ── 메일함을 바꾸는 손 — 사람이 그 메일 하나를 분명히 고른 뒤에만 부른다(머리말) ──────────────

    def mark_read(self, mail: Entry | str) -> None:
        """⚠ 메일함을 바꾼다 — 그 메일 하나를 읽음으로. 읽기 길은 이 손을 부르지 않는다.

        받은편지함 메일로만 쟀다 — 폴더에만 있는 메일에 먹는지는 안 쟀다. 끊긴 세션이면 ``SessionExpired``(반영되지 않았다).
        """
        self._send_change(f"{self.db_path}/{INBOX_VIEW}/{_unid(mail)}?OpenDocument")

    def mark_unread(self, mail: Entry | str) -> None:
        """⚠ 메일함을 바꾼다 — 그 메일 하나를 안 읽음으로(읽음의 되돌리기). 부르는 자리는 ``mark_read`` 와 같다."""
        self._send_change(f"{self.db_path}/ag_read_cancel?OpenAgent&docid={_unid(mail)}&imapuser=0")

    def _send_change(self, path: str) -> None:
        """메일함을 바꾸는 주소를 부른다 — 위 두 손의 꼴만 받는다. 끊긴 세션의 로그인 페이지는 ``SessionExpired``."""
        db = re.escape(self.db_path)
        if not (re.fullmatch(rf"{db}/{INBOX_VIEW}/{_HEX32}\?OpenDocument", path)
                or re.fullmatch(rf"{db}/ag_read_cancel\?OpenAgent&docid={_HEX32}&imapuser=0", path)):
            raise ChangeRefused(f"메일함을 바꾸는 손 둘의 꼴이 아니다: {path}")
        data, kind = self._open(self.server + path)
        if _looks_like_login(data.decode(_charset(kind), errors="replace")):
            raise SessionExpired("메일함을 바꾸는 요청에 로그인 페이지가 왔다 — 반영되지 않았다")
        log.info("메일함을 바꿨다: %s", "읽음으로" if path.endswith("?OpenDocument") else "안 읽음으로")


# ── 풀기 ─────────────────────────────────────────────────────────────────

def _column(entry: ET.Element, name: str) -> str:
    for data in entry.iter("entrydata"):
        if data.get("name") == name:
            return " ".join(t.strip() for t in data.itertext() if t.strip())
    return ""


def _is_folder(view: dict) -> bool:
    return str(view.get("@folder")).casefold() == "true"


def folder_order(path: str) -> tuple:
    """폴더 경로의 차례 — 부모 · 자식 마디마다 견준다(「부모 2」가 「부모」와 「부모\\자식」 사이에 끼지 않게)."""
    return tuple(part.casefold() for part in path.split(FOLDER_SEPARATOR)), path


def _entry(entry: ET.Element, *, folder: str = "") -> Entry:
    mark = _column(entry, COLUMN_READ)
    return Entry(
        unid=entry.get("unid", ""),
        subject=_column(entry, COLUMN_SUBJECT),
        sender=parse_sender(_column(entry, COLUMN_FROM)),
        date=_column(entry, COLUMN_DATE),
        date_sort=_column(entry, COLUMN_DATE_SORT),
        size=_column(entry, COLUMN_SIZE),
        importance=_column(entry, COLUMN_IMPORTANCE),
        role=_column(entry, COLUMN_ROLE).upper(),
        attachments=tuple(parse_attachment(n) for n in _column(entry, COLUMN_ATTACHMENTS).split(ATTACHMENT_SEPARATOR)
                          if n.strip()),
        unread=UNREAD_MARK in mark,
        read_mark=mark,
        related=_column(entry, COLUMN_RELATED),
        folder=folder,
    )


_ANGLE = re.compile(r"<\s*([^<>\s]+@[^<>\s]+)\s*>")
_BARE = re.compile(r"^[^@\s<>,;\"]+@[^@\s<>,;\"]+$")


def parse_sender(raw: str) -> Sender:
    """보낸 사람 열을 푼다 — 사내 ``-=spl=-`` · ``-ENG-`` 꼴, 밖의 주소만, 그 밖의 ``이름 <주소>`` 꼴."""
    text = html.unescape(raw).strip()
    if SPLIT_MARK in text or ENG_MARK in text:
        ko, _, en = text.partition(ENG_MARK)
        name, addr = _spl_part(ko)
        name_eng, addr_eng = _spl_part(en)
        return Sender(name=name, addr=addr or addr_eng, name_eng=name_eng)
    person = parse_person(text)
    return Sender(name=person.name, addr=person.addr)


def _spl_part(part: str) -> tuple[str, str]:
    display, _, rest = part.partition(SPLIT_MARK)
    found = _ANGLE.search(rest or display)
    name = display.strip() if rest else (display[:found.start()] if found else display).strip()
    return name.strip('"').strip(), found.group(1) if found else ""


def parse_people(raw: str) -> tuple[Recipient, ...]:
    """받는 사람 글줄(쉼표로 이은 사람들)을 푼다. 따옴표 · 꺾쇠 안의 쉼표는 가름이 아니다."""
    text = html.unescape(raw or "")
    people, depth, quoted, token = [], 0, False, []
    for ch in text:
        if ch == '"':
            quoted = not quoted
        elif ch == "<" and not quoted:
            depth += 1
        elif ch == ">" and not quoted and depth:
            depth -= 1
        if ch == "," and not quoted and not depth:
            people.append("".join(token))
            token = []
        else:
            token.append(ch)
    people.append("".join(token))
    return tuple(p for p in (parse_person(t) for t in people) if p.name or p.addr or p.notes)


def parse_person(token: str) -> Recipient:
    """사람 하나 — ``이름 <주소>``(공백 · 탭 · 없음) · ``"이름" <주소>`` · 주소만 · Notes 이름 · ``<ID>(<약칭>)``.

    모르는 꼴은 버리지 않고 ``notes`` 에 그대로 둔다 — 버리면 함께 받은 사람 수가 조용히 준다.
    """
    t = token.strip().strip(";").strip()
    if not t:
        return Recipient("", "")
    found = _ANGLE.search(t)
    if found:
        return Recipient(name=t[:found.start()].strip().strip('"').strip(), addr=found.group(1))
    if _BARE.match(t):
        return Recipient(name="", addr=t)
    if t.upper().startswith("CN=") or ("/" in t and "@" not in t):
        first = t.split("/", 1)[0]
        return Recipient(name=first.split("=", 1)[1] if "=" in first else first, addr="", notes=t)
    # <ID>(<약칭>) 과 모르는 꼴 — 이름 · 주소 없이 글자 그대로가 열쇠다
    return Recipient(name="", addr="", notes=t)


def parse_attachment(listed: str) -> AttachmentName:
    """첨부 이름 하나 — ECM 꼴이면 원래 이름 · 확장자 · 크기를 뽑는다."""
    listed = listed.strip()
    found = ECM_ATTACHMENT.match(listed)
    if found:
        ext = found.group("ext").lower()
        return AttachmentName(listed=listed, name=f"{found.group('name').strip()}.{ext}", ext=ext,
                              size_kb=int(found.group("kb")), ecm=True)
    ext = listed.rsplit(".", 1)[1].lower() if "." in listed else ""
    return AttachmentName(listed=listed, name=listed, ext=ext)


def _unid(mail: Entry | str) -> str:
    unid = mail.unid if isinstance(mail, Entry) else mail
    if not _UNID.match(unid or ""):
        raise MailboxConfigError(f"메일 열쇠(unid)가 아니다: {unid!r}")
    return unid


def _charset(content_type: str) -> str:
    match = re.search(r"charset=([\w-]+)", content_type, re.IGNORECASE)
    return match.group(1) if match else "utf-8"


def _looks_like_login(text: str) -> bool:
    """끊긴 세션이 200 으로 준 SSO 화면인가 — 인증 쿠키를 지우거나 SSO 로그인으로 보내는 스크립트로 가른다. 낱말
    「swpsso」만으로는 안 가른다 — 본문에 SSO 주소를 적은 사내 안내를 끊긴 세션으로 읽는다."""
    return "EP_CERTIFY" in text or bool(_LOGIN_JUMP.search(text))


_LOGIN_JUMP = re.compile(r"location(?:\.href)?\s*=\s*[\"'][^\"']*swpsso[^\"']*login", re.IGNORECASE)


class _Redirected(Exception):
    def __init__(self, location: str):
        super().__init__(location)
        self.location = location


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise _Redirected(newurl)
