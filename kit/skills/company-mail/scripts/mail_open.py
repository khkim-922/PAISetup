"""세션으로 메일함을 연다 — 메일함 주소를 고르고(준 주소 · 같은 로그인에 받아 둔 주소 · 메일 서버 첫 화면) 메일함 손을 세운다.

부르는 꼴::

    import mail_open
    opened = mail_open.open_mailbox(url, session_file, inbox)   # 준 주소(빈 글자면 고른다) · 세션 파일 → Opened(고른 주소, 메일함 손)
    url = mail_open.given_url(url)                              # 사람 · 설정이 준 주소(--url 값 · MAILBOX_URL 순) — 없으면 빈 글자
    with mail_open.stops_from_mail(inbox):                      # 그 안의 세션 손 · 메일함 손의 예외 → Stop(종료 값 · 말 · 걸음)
        ...

``inbox`` 는 곁의 메일함 손 모듈이다. 못 열면 ``mail_stop.Stop`` — 세션이 없거나 끊겼으면 3, 주소를 못 받았으면 2. 메일 서버 첫 화면이
댄 주소는 그 세션 쿠키의 지문(``session_mark``)과 함께 받아 둔다(``mailbox.json`` — 받아 둔 조직도와 같은 자리 ``mail_kept.cache_dir``)
— 같은 로그인 동안 서버에 다시 묻지 않고, 다른 로그인의 지문에는 안 낸다. 쿠키 값은 안 적는다. 이 스킬의 명령과 형제 스킬
company-directory 의 찾기가 같은 자리로 열고, 세션 손 · 메일함 손의 예외도 같은 자리(``stops_from_mail``)에서 같은 말의 멈춤으로 옮긴다.
"""

from __future__ import annotations

import contextlib
import json
import os
import pathlib
import re
import sys
from typing import NamedTuple

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
for _where in (HERE, EP_LOGIN_SCRIPTS):
    if str(_where) not in sys.path:
        sys.path.insert(0, str(_where))             # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
import ep_command  # noqa: E402 — 자리를 넣은 뒤에 싣는다
import ep_session  # noqa: E402
import mail_kept  # noqa: E402
from mail_stop import SESSION_CUT_WHY, Stop, from_ep  # noqa: E402
from mail_token import token  # noqa: E402

SESSION_UNREAD = "세션 파일을 못 읽었다({session}: {why})."   # 세션 파일이 없거나 꼴이 틀린 판의 사실 — 걸음(ep-login)은 종료 값 3 의 걸음이 붙인다
URL_UNKNOWN = "메일함 주소를 세션으로 못 받았다({why}) — --url 이나 MAILBOX_URL 로 준다"   # 서버 첫 화면이 메일함을 안 댄 판의 말
CHANGE_REFUSED = "메일함을 바꿀 주소라 묻지 않았다(inbox.py 의 막기): {why}"   # 메일함 손이 바꾸는 주소를 막은 판
MAILBOX_FAILED = "메일함에서 못 받았다: {why}"   # 메일함 손이 답을 못 받은 판 — 부르는 명령은 못 받은 것을 제 말로 댄다(stops_from_mail 의 failed)
MAILBOX_CACHE_FILE = "mailbox.json"   # 받아 둔 메일함 주소 — 받아 둔 조직도와 같은 자리(``mail_kept.cache_dir``) · 세션 쿠키의 지문에 묶인다(``session_mark``)
MAILFILE_NUMBER = re.compile(r"/(\d+)\.nsf$", re.IGNORECASE)   # 메일함 파일 번호 = 그 메일함을 쓰는 사람의 사번(<사번>.nsf)


class Opened(NamedTuple):
    """세션으로 연 메일함 — 고른 주소(``url`` — 세션 줄 · 화면 손 · 첨부 자리 · 사번이 읽는다)와 그 메일함 손(``box`` — ``inbox.Mailbox``)."""
    url: str
    box: object


def open_mailbox(url: str, session_file, inbox) -> Opened:
    """세션으로 메일함을 연다 — 주소를 골라(``mailbox_url``) 메일함 손을 세운다(``mailbox_hand``). ``url`` 은 사람이 준 주소(``--url``
    값 · 없으면 빈 글자)다."""
    chosen = mailbox_url(url, session_file, inbox)
    return Opened(chosen, mailbox_hand(chosen, session_file, inbox))


def mailbox_url(url: str, session_file, inbox) -> str:
    """메일함 주소 — 준 주소 · ``MAILBOX_URL`` 순(``given_url``), 둘 다 없으면 그 세션의 주소(``session_url``)."""
    return given_url(url) or session_url(mail_server(), session_file, inbox)


def given_url(url: str) -> str:
    """사람 · 설정이 준 메일함 주소 — 준 값(``--url``) · ``MAILBOX_URL`` 순. 없으면 빈 글자."""
    return (url or os.environ.get("MAILBOX_URL", "")).strip()


def mail_server() -> str:
    """메일 서버 — ``MAIL_SERVER``, 없으면 형제 스킬 ep-login 의 기본 서버(``ep_session.DOMINO_SERVER``)."""
    return os.environ.get("MAIL_SERVER", "").strip() or ep_session.DOMINO_SERVER


def session_url(server: str, session, inbox) -> str:
    """그 세션의 메일함 주소 — 같은 로그인에 받아 둔 것(``kept_mailbox``)이 있으면 그것, 없으면 메일 서버 첫 화면에 묻는다
    (``inbox.discover_mailbox``). 받은 주소는 받아 둔다. 세션이 끊겼거나 세션 파일을 못 읽으면 Stop(3), 주소를 못 받으면 Stop(2)."""
    mark = session_mark(server, session)
    try:
        url = kept_mailbox(mark) or inbox.discover_mailbox(server, session)
        keep_mailbox(mark, url)
    except (inbox.SessionExpired, inbox.SessionMissing) as exc:
        raise mailbox_stop(exc, inbox, session) from exc
    except inbox.MailboxConfigError as exc:
        raise Stop(ep_command.EXIT_ARGS, URL_UNKNOWN.format(why=exc), stepped=False) from exc
    return url


def mailbox_hand(url: str, session, inbox):
    """그 주소 · 세션 파일의 메일함 손(``inbox.Mailbox``) — 세션 파일을 못 읽으면 Stop(3), 주소 꼴이 틀리면 Stop(2)."""
    try:
        return inbox.Mailbox(url, session)
    except inbox.MailboxConfigError as exc:
        raise mailbox_stop(exc, inbox, session) from exc


@contextlib.contextmanager
def stops_from_mail(inbox, *, failed: str = MAILBOX_FAILED):
    """그 안에서 난 세션 손 · 메일함 손의 예외를 멈춤으로 옮긴다 — 세션 손이 못 섰으면(``ep_session.NoSession``) ``no_session``, 메일함
    손의 오류면 ``mailbox_stop``. ``failed`` 는 메일함이 답을 안 준 판의 말 꼴(``{why}`` 자리)이다. 이 스킬의 명령 한 판과 형제 스킬
    company-directory 의 찾기 한 판이 이 한 자리로 옮긴다 — 같은 사실은 두 스킬에서 같은 말이다."""
    try:
        yield
    except ep_session.NoSession as exc:
        raise no_session(exc.got) from exc
    except inbox.MailboxError as exc:
        raise mailbox_stop(exc, inbox, failed=failed) from exc


def no_session(got) -> Stop:
    """세션 손이 못 선 까닭(``ep_session.NoSession`` 의 ``got``)을 이 명령의 멈춤으로 — 종료 값과 말은 사내 앱 명령의 한 자리(형제 스킬
    ep-login 의 ``ep_command.no_session``)가 든다."""
    return from_ep(ep_command.no_session(got))


def mailbox_stop(exc, inbox, session="", *, failed: str = MAILBOX_FAILED) -> Stop:
    """메일함 손의 오류 하나(``inbox.MailboxError`` 의 갈래) → 멈춤 — 세션이 끊겼거나 세션 파일(``session``)을 못 읽었으면 3, 읽기 길이
    막은 주소는 1, 설정 · 인자가 틀렸으면 2, 메일함이 답을 안 주면 1(말 꼴은 ``failed``). 글은 사실과 메일함 손이 댄 까닭이고 걸음은
    종료 값이 붙인다. 메일함을 여는 자리와 명령 한 판(``stops_from_mail``)이 같은 표로 옮긴다."""
    if isinstance(exc, inbox.SessionExpired):
        return Stop(ep_command.EXIT_SESSION, SESSION_CUT_WHY.format(why=exc))
    if isinstance(exc, inbox.SessionMissing):
        return Stop(ep_command.EXIT_SESSION, SESSION_UNREAD.format(session=session, why=exc))
    if isinstance(exc, inbox.ChangeRefused):
        return Stop(ep_command.EXIT_TOOL, CHANGE_REFUSED.format(why=exc))
    if isinstance(exc, inbox.MailboxConfigError):
        return Stop(ep_command.EXIT_ARGS, str(exc))
    return Stop(ep_command.EXIT_TOOL, failed.format(why=exc))


def session_mark(server: str, session) -> str:
    """그 세션이 그 메일 서버에 싣는 쿠키의 지문 — 받아 둔 메일함 주소를 로그인 한 판에 묶는다. 다른 사람이 로그인하거나 다시
    로그인하면 쿠키가 달라져 지문도 달라진다. 세션 파일을 못 읽으면 빈 글자다(받아 둔 것을 안 쓴다 — 묻는 손이 그 까닭을 낸다)."""
    host = server.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0].lower()
    try:
        jar = ep_session.load_jar(session)
    except ep_session.SessionFileError:
        return ""
    mine = sorted((c.name, c.value) for c in jar
                  if host == c.domain.lstrip(".").lower() or host.endswith("." + c.domain.lstrip(".").lower()))
    return token("mailbox", server, mine) if mine else ""


def kept_mailbox(mark: str) -> str:
    """그 지문으로 받아 둔 메일함 주소 — 없거나 지문이 다르거나 파일이 깨졌으면 빈 글자다."""
    try:
        raw = json.loads((mail_kept.cache_dir() / MAILBOX_CACHE_FILE).read_text(encoding="utf-8"))
        return str(raw["url"]) if mark and raw.get("mark") == mark else ""
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return ""


def keep_mailbox(mark: str, url: str) -> None:
    """메일함 주소를 그 지문과 함께 받아 둔다 — 쿠키 값은 안 적는다. 못 써도 명령은 선다."""
    if not mark or kept_mailbox(mark) == url:
        return
    try:
        mail_kept.cache_dir().mkdir(parents=True, exist_ok=True)
        (mail_kept.cache_dir() / MAILBOX_CACHE_FILE).write_text(json.dumps({"mark": mark, "url": url}), encoding="utf-8")
    except OSError:
        pass
