"""사내 메일 중계로 메일을 보낸다 — 표준 라이브러리만 쓰는 파일 하나.

무엇을 하나
    스크립트가 HTML · 평문 메일을 사내 중계(SMTP)로 보낸다. 기본 중계에서 잰
    동작을 기본값과 난간으로 박아 두었다 — 환경변수를 하나도 안 줘도 사내망
    안에서는 첫 판에 나간다.

어떻게 부르나
    이 파일을 스크립트 곁에 두고 부른다::

        import mailer

        mailer.send("제목", to=["a@company.com"], sender="me@company.com",
                    html="<p>본문</p>")

    수신자를 파일로 두는 스크립트는 **오래 걸리는 일을 시작하기 전에** 읽는다 —
    발송 직전에 설정이 틀린 것을 알면 그때까지 한 일을 버린다::

        recipients = mailer.load_recipients("recipients.json")  # 틀리면 여기서 MailConfigError
        ...오래 걸리는 일...
        mailer.send("제목", html=html, **recipients)

    수신자 파일의 꼴 — ``from`` 은 발신자, ``to`` · ``cc`` · ``bcc`` 는 주소 목록,
    ``error_notify`` 는 알림을 받을 주소 하나다(없으면 ``to`` 의 첫 주소가 받는다)::

        {"from": "me@company.com", "to": ["a@company.com"], "cc": [], "bcc": [],
         "error_notify": "me@company.com"}

    실패 알림처럼 「나가면 좋고, 못 나가도 본 흐름을 막으면 안 되는」 메일은
    ``notify`` 로 보낸다 — 제 오류를 삼킨다::

        mailer.notify("[작업 실패] 20261102", "사유 …", recipients_file="recipients.json")

무엇을 내나
    ``send`` 는 None 을 낸다. 못 보내면 예외다 — 설정이 틀리면 ``MailConfigError``,
    중계가 수신자를 하나라도 거절하면 ``MailRefused``, STARTTLS 를 요구했는데 안
    서면 ``MailError``. 연결 · 시한 오류는 ``smtplib`` · ``socket`` 의 예외가 그대로 온다.
    ``load_recipients`` 는 ``send`` 에 그대로 풀어 넣을 dict(``sender`` · ``to`` · ``cc`` ·
    ``bcc``)를 낸다. ``notify`` 는 보냈으면 True, 못 보냈으면 False 를 내고 예외를 안 낸다.
    무엇을 했는지는 ``logging`` 으로 남긴다(로거 이름은 이 모듈 이름).

환경변수 — 회사 SMTP 규약의 이름. 비워 둔 값은 안 준 것으로 본다
    ``MAIL_HOST``             중계 호스트                    기본 ``antispam.posco.net``
    ``MAIL_PORT``             포트                           기본 ``25``
    ``MAIL_DEFAULT_SENDER``   발신자를 따로 안 줬을 때의 발신자
    ``MAIL_USE_TLS``          비움 → STARTTLS 를 시도하고, 안 서면 경고를 남기고 평문으로 보낸다
                              참(1 · true · yes · on) → STARTTLS 가 안 서면 보내지 않고 실패한다
                              거짓(0 · false · no · off) → 시도하지 않고 평문으로 보낸다
    ``MAIL_TIMEOUT_SECONDS``  연결 · 응답 시한(초)            기본 ``60``

    ``MAIL_USERNAME`` · ``MAIL_PASSWORD`` · ``MAIL_USE_SSL`` 은 읽지 않는다 — 기본 중계는
    인증도 SSL 직접 연결(465)도 안 쓴다. 그것이 필요한 서버면 이 파일로는 안 나간다.

기본 중계에서 잰 것 — 어기면 조용히 망가진다. 원본은 사내 환경 기록
(``~/.claude/posco/ENV-posco.md`` 「네트워크 접근」)이다
    * 인증 없이 25 번으로 받는다. 사내망 밖에서는 닿지 않는다
    * STARTTLS 를 광고하지만 핸드셰이크에서 서버가 연결을 끊는다. 그래서 기본은
      「시도 → 끊기면 새 연결로 평문」이고 물러난 사실을 경고로 남긴다 — 본문이
      평문으로 사내망을 지난다는 뜻이다
    * 일부 수신자만 거절되면 ``smtplib`` 은 예외 없이 거절 목록만 돌려준다. 그것을
      성공으로 세면 누군가 조용히 못 받는다 — 그래서 하나라도 거절되면 ``MailRefused``
    * bcc 는 봉투(RCPT)에만 싣고 머리(헤더)에는 쓰지 않는다
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import re
import smtplib
import socket
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

DEFAULT_HOST = "antispam.posco.net"
DEFAULT_PORT = 25
DEFAULT_TIMEOUT = 60.0
# HTML 메일의 평문 짝 — HTML 을 못 그리는 클라이언트가 이 줄을 보여 준다
HTML_ONLY_NOTE = "본 메일은 HTML 형식입니다."

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}
# 봉투에 실을 수 있는 맨주소 — 쉼표 · 공백이 섞이면 주소 둘이 하나로 붙은 것이다
_BARE_ADDRESS = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+$")

log = logging.getLogger(__name__)


class MailError(Exception):
    """메일을 못 보냈다. 메시지가 사유다."""


class MailConfigError(MailError):
    """설정이 틀렸다 — 환경변수나 수신자 파일. 보내기 전에 잡힌다."""


class MailRefused(MailError):
    """중계가 수신자를 거절했다. `refused` 가 {주소: (코드, 응답)} 이다."""

    def __init__(self, message: str, refused: dict):
        super().__init__(message)
        self.refused = refused


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    tls: str            # "try" · "require" · "off"
    timeout: float
    default_sender: str | None


def settings() -> Settings:
    """환경변수를 읽어 발송 설정을 세운다. 틀린 값이면 MailConfigError.

    부를 때마다 다시 읽는다 — 스크립트가 도중에 환경변수를 바꿔도 따라간다.
    """
    env = {name: os.environ.get(name, "").strip() for name in (
        "MAIL_HOST", "MAIL_PORT", "MAIL_USE_TLS", "MAIL_TIMEOUT_SECONDS",
        "MAIL_DEFAULT_SENDER")}

    port_raw = env["MAIL_PORT"] or str(DEFAULT_PORT)
    if not port_raw.isdigit() or not 0 < int(port_raw) < 65536:
        raise MailConfigError(f"MAIL_PORT 가 포트 번호가 아니다: {port_raw!r}")

    tls_raw = env["MAIL_USE_TLS"].lower()
    if not tls_raw:
        tls = "try"
    elif tls_raw in _TRUE:
        tls = "require"
    elif tls_raw in _FALSE:
        tls = "off"
    else:
        raise MailConfigError(
            f"MAIL_USE_TLS 를 읽을 수 없다: {env['MAIL_USE_TLS']!r} — "
            "비우거나 true · false 중 하나로 둔다")

    timeout_raw = env["MAIL_TIMEOUT_SECONDS"] or str(DEFAULT_TIMEOUT)
    try:
        timeout = float(timeout_raw)
    except ValueError:
        timeout = 0.0
    if timeout <= 0:
        raise MailConfigError(f"MAIL_TIMEOUT_SECONDS 가 양수가 아니다: {timeout_raw!r}")

    sender = env["MAIL_DEFAULT_SENDER"] or None
    if sender:
        _check_address(sender, "MAIL_DEFAULT_SENDER")
    return Settings(env["MAIL_HOST"] or DEFAULT_HOST, int(port_raw), tls, timeout, sender)


# ── 주소 ──────────────────────────────────────────────────────────────────

def _check_address(value, where: str) -> str:
    """주소 하나인가. ``이름 <a@b>`` 꼴도 받는다.

    ⚠ 「@」 가 둘이면 주소 둘이 한 칸에 붙은 것이다 — 파이썬 판에 따라 ``parseaddr`` 가
    첫 주소만 꺼내 주므로, 그대로 두면 둘째 주소가 조용히 빠진다.
    """
    if (not isinstance(value, str) or value.count("@") != 1
            or not _BARE_ADDRESS.match(parseaddr(value)[1])):
        raise MailConfigError(f"{where} 에 주소가 아닌 값이 있다: {value!r}")
    return value


def _address_list(value, where: str) -> list[str]:
    """주소 목록으로 고른다. 문자열 하나는 주소 하나로 받는다.

    ⚠ 문자열을 목록인 줄 알고 돌면 글자 하나하나가 수신자가 된다 — 그래서 여기서 막는다.
    """
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        raise MailConfigError(f"{where} 는 주소 목록이어야 한다: {value!r}")
    return [_check_address(item, where) for item in value]


def _resolve_sender(sender: str | None, config: Settings, where: str) -> str:
    sender = sender or config.default_sender
    if not sender:
        raise MailConfigError(f"{where}에 from 이 없다")
    return _check_address(sender, where)


def load_recipients(path) -> dict:
    """수신자 파일을 읽고 다 쓸 만한지 본다 — **오래 걸리는 일을 시작하기 전에** 부른다.

    발송 설정(환경변수)도 함께 본다. 둘 중 하나라도 틀리면 MailConfigError.
    내는 것 — ``send`` 에 그대로 풀어 넣을 ``{"sender", "to", "cc", "bcc"}``.
    ``from`` 이 없으면 ``MAIL_DEFAULT_SENDER`` 로 채운다.
    """
    config = settings()
    path = pathlib.Path(path)
    if not path.exists():
        raise MailConfigError(f"수신자 설정이 없다: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MailConfigError(f"수신자 설정이 깨졌다: {exc}") from exc
    if not isinstance(data, dict):
        raise MailConfigError(f"수신자 설정이 객체가 아니다: {path}")

    sender = _resolve_sender(data.get("from"), config, "수신자 설정")
    to = _address_list(data.get("to"), "수신자 설정의 to")
    if not to:
        raise MailConfigError("수신자 설정에 to 가 비어 있다")
    if data.get("error_notify") is not None:
        _check_address(data["error_notify"], "수신자 설정의 error_notify")
    return {
        "sender": sender,
        "to": to,
        "cc": _address_list(data.get("cc"), "수신자 설정의 cc"),
        "bcc": _address_list(data.get("bcc"), "수신자 설정의 bcc"),
    }


# ── 발송 ──────────────────────────────────────────────────────────────────

def _connect(config: Settings) -> smtplib.SMTP:
    server = smtplib.SMTP(config.host, config.port, timeout=config.timeout,
                          local_hostname=socket.getfqdn())
    server.ehlo()
    return server


def _close(server: smtplib.SMTP) -> None:
    try:
        server.quit()
    except Exception:
        server.close()


def _secure(server: smtplib.SMTP, config: Settings) -> smtplib.SMTP:
    """정책대로 STARTTLS 를 세운다. 내는 것 — 이어서 쓸 연결(물러나면 새 평문 연결)."""
    if not server.has_extn("starttls"):
        if config.tls == "require":
            _close(server)
            raise MailError("중계가 STARTTLS 를 광고하지 않는다 — "
                            "MAIL_USE_TLS 가 켜져 있어 평문으로 보내지 않는다")
        log.warning("발송: 중계가 STARTTLS 를 광고하지 않는다 — 평문으로 보낸다")
        return server
    try:
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
    except Exception as exc:
        # 기본 중계가 여기로 온다 — 광고는 하지만 핸드셰이크에서 연결을 끊는다.
        # 끊긴 연결은 다시 못 쓰므로 새로 잇는다.
        _close(server)
        if config.tls == "require":
            raise MailError(f"STARTTLS 가 서지 않는다({type(exc).__name__}) — "
                            "MAIL_USE_TLS 가 켜져 있어 평문으로 물러나지 않는다") from exc
        log.warning("발송: STARTTLS 가 서지 않는다(%s) — 평문으로 보낸다",
                    type(exc).__name__)
        return _connect(config)
    log.info("발송: STARTTLS 로 보낸다")
    return server


def _deliver(message: EmailMessage, sender: str, envelope: list[str],
             config: Settings) -> None:
    server = _connect(config)
    try:
        if config.tls != "off":
            server = _secure(server, config)
        try:
            refused = server.sendmail(sender, envelope, message.as_bytes())
        except smtplib.SMTPRecipientsRefused as exc:
            refused = exc.recipients
        if refused:
            raise MailRefused(f"받기를 거절한 수신자가 있다: {refused}", refused)
    finally:
        _close(server)


def send(subject: str, *, to, cc=None, bcc=None, sender: str | None = None,
         html: str | None = None, text: str | None = None) -> None:
    """메일 한 통을 보낸다. 실패하면 예외다(모듈 머리말의 「무엇을 내나」).

    ``html`` 을 주면 HTML 메일이고 ``text`` 는 그 평문 짝이 된다(안 주면 안내 한 줄).
    ``html`` 없이 ``text`` 만 주면 평문 메일이다. ``to`` · ``cc`` · ``bcc`` 는 주소 목록,
    문자열 하나는 주소 하나로 받는다. ``bcc`` 는 머리에 안 쓴다.
    """
    config = settings()
    sender = _resolve_sender(sender, config, "발송 인자")
    to = _address_list(to, "to")
    cc = _address_list(cc, "cc")
    bcc = _address_list(bcc, "bcc")
    if not to:
        raise MailConfigError("to 가 비어 있다")
    if html is None and text is None:
        raise MailConfigError("본문이 없다 — html 이나 text 를 준다")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(to)
    if cc:
        message["Cc"] = ", ".join(cc)
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    # Message-ID 의 도메인은 발신자의 것 — 남의 도메인을 달면 스팸 판정이 의심한다
    message["Message-ID"] = make_msgid(domain=_domain(sender))
    if html is None:
        message.set_content(text)
    else:
        message.set_content(HTML_ONLY_NOTE if text is None else text)
        message.add_alternative(html, subtype="html")

    envelope = to + cc + bcc
    _deliver(message, sender, envelope, config)
    body = html if html is not None else text
    log.info("발송: 수신자 %d명 · %d bytes", len(envelope), len(body.encode("utf-8")))


def _domain(address: str) -> str | None:
    return parseaddr(address)[1].rpartition("@")[2] or None


def notify(subject: str, text: str, *, to: str | None = None,
           sender: str | None = None, recipients_file=None) -> bool:
    """평문 알림 한 통 — **제 오류를 삼킨다.** 보냈으면 True, 못 보냈으면 False.

    실패 알림이 실패해서 본 흐름의 종료 코드 · 마지막 로그가 바뀌면 안 되므로
    무엇이 틀려도 예외를 내지 않고 경고 한 줄만 남긴다.

    ``to`` 를 안 주면 ``recipients_file`` 의 ``error_notify``, 그것도 없으면 ``to`` 의 첫
    주소가 받는다. 이 파일은 ``load_recipients`` 보다 너그럽게 읽는다 — 수신자 설정이
    틀려서 멈춘 판에도 알림 받을 주소만 있으면 알림은 나가야 한다.
    """
    try:
        if recipients_file is not None and not (to and sender):
            data = json.loads(pathlib.Path(recipients_file).read_text(encoding="utf-8"))
            listed = data.get("to")
            first = listed if isinstance(listed, str) else (listed or [None])[0]
            to = to or data.get("error_notify") or first
            sender = sender or data.get("from")
        sender = sender or settings().default_sender
        if not (to and sender):
            log.warning("알림을 못 보냈다: 받을 주소나 발신자가 없다")
            return False
        send(subject, to=[to], sender=sender, text=text)
        log.info("알림을 보냈다: %s", to)
        return True
    except Exception as exc:
        log.warning("알림을 못 보냈다: %s", type(exc).__name__)
        return False
