"""mailer.py 의 계약을 가짜 중계로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 메일이 정말 나가나 · 엉뚱한 사람에게 가나 · bcc 가 머리에
새나 · 받기를 거절당한 것을 성공으로 세나. 깨지면 작업 스케줄러 아래서 조용히
안 나간 날이 쌓이거나(되돌릴 수 없다), bcc 주소가 모두에게 보인다.

가짜 중계는 기본 중계에서 잰 꼴을 흉내 낸다 — STARTTLS 를 광고하고, 명령을
받으면 핸드셰이크 없이 연결을 끊는다(mailer.py 머리말의 실측).

돌리는 법::

    python -X utf8 -I check_mailer.py [mailer.py 가 든 폴더]

폴더를 안 주면 이 파일의 폴더를 잰다. 일부러 틀린 사본을 다른 폴더에 두고 그
폴더를 주면 물림(검사가 정말 무나)을 잰다.

판정 — 끝 줄이 「통과 N/N」 이면 종료 코드 0, 하나라도 어긋나면 1, 가짜 중계를
못 띄우는 등 재지 못했으면 2.

언제 걷나 — mailer.py 가 사라지거나, 같은 계약을 실물 중계에서 재는 검사가 서서
이 검사가 더하는 믿음이 없어지면.

여기서 못 재는 것 — STARTTLS 가 실제로 서는 길(가짜 중계에 인증서가 없다).
"""

from __future__ import annotations

import contextlib
import email
import email.policy
import json
import logging
import os
import pathlib
import socket
import sys
import tempfile
import threading
import traceback

# 이 검사는 이름 풀이도 하지 않는다 — smtplib 이 EHLO 이름으로 부르는 getfqdn 은
# DNS 를 묻는다. 127.0.0.1 밖으로 아무것도 안 나가게 막는다.
socket.getfqdn = lambda name="": "check.invalid"

TREE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else __file__).resolve()
TREE = TREE if TREE.is_dir() else TREE.parent
sys.path.insert(0, str(TREE))
import mailer  # noqa: E402 — 잴 나무가 sys.path 에 먼저 서야 한다

SENDER = "sender@example.test"


# ── 가짜 중계 ─────────────────────────────────────────────────────────────

class Unmeasured(Exception):
    """잴 판을 못 세웠다 — 어긋남이 아니라 「못 쟀다」다."""


class FakeRelay:
    """127.0.0.1 의 SMTP 흉내. `starttls` 는 "drop"(광고하고 끊는다) · "none"(광고 안 함)."""

    def __init__(self, starttls: str = "drop", refuse=()):
        self.starttls = starttls
        self.refuse = {a.lower() for a in refuse}
        self.connections = 0
        self.commands: list[str] = []
        self.mails: list[dict] = []
        try:
            self._sock = socket.socket()
            self._sock.bind(("127.0.0.1", 0))
            self._sock.listen()
        except OSError as exc:
            raise Unmeasured(f"가짜 중계를 못 띄웠다: {exc}") from exc
        self.port = self._sock.getsockname()[1]
        threading.Thread(target=self._serve, daemon=True).start()

    def close(self) -> None:
        self._sock.close()

    def _serve(self) -> None:
        while True:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                return
            threading.Thread(target=self._session, args=(conn,), daemon=True).start()

    def _session(self, conn: socket.socket) -> None:
        self.connections += 1
        reader = conn.makefile("rb")

        def say(*lines: str) -> None:
            conn.sendall("".join(f"{line}\r\n" for line in lines).encode())

        def address(line: str) -> str:
            return line.split(":", 1)[1].strip().split()[0].strip("<>")

        mail = None
        try:
            say("220 fake relay")
            while True:
                raw = reader.readline()
                if not raw:
                    return
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                verb = line.split(" ", 1)[0].upper()
                self.commands.append(verb)
                if verb == "EHLO":
                    extensions = ["250-fake", "250-8BITMIME"]
                    if self.starttls == "drop":
                        extensions.append("250-STARTTLS")
                    say(*extensions, "250 HELP")
                elif verb == "STARTTLS":
                    say("220 go ahead")
                    return              # 실측 꼴 — 핸드셰이크를 받지 않고 끊는다
                elif verb == "MAIL":
                    mail = {"from": address(line), "rcpts": [], "data": b""}
                    say("250 ok")
                elif verb == "RCPT":
                    rcpt = address(line)
                    if rcpt.lower() in self.refuse:
                        say("550 no such user")
                    else:
                        mail["rcpts"].append(rcpt)
                        say("250 ok")
                elif verb == "DATA":
                    say("354 go ahead")
                    chunks = []
                    while True:
                        row = reader.readline()
                        if not row or row == b".\r\n":
                            break
                        chunks.append(row[1:] if row.startswith(b"..") else row)
                    mail["data"] = b"".join(chunks)
                    self.mails.append(mail)
                    mail = None
                    say("250 queued")
                elif verb == "QUIT":
                    say("221 bye")
                    return
                else:                   # HELO · RSET · NOOP
                    mail = None if verb == "RSET" else mail
                    say("250 ok")
        except OSError:
            return
        finally:
            conn.close()


# ── 판 ────────────────────────────────────────────────────────────────────

class Records(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines: list[tuple[str, str]] = []

    def emit(self, record):
        self.lines.append((record.levelname, record.getMessage()))


@contextlib.contextmanager
def stage(relay: FakeRelay | None = None, **env: str):
    """MAIL_* 를 이 판의 값으로만 세우고, mailer 의 로그를 모은다."""
    saved = {k: v for k, v in os.environ.items() if k.startswith("MAIL_")}
    for key in saved:
        del os.environ[key]
    if relay is not None:
        os.environ["MAIL_HOST"] = "127.0.0.1"
        os.environ["MAIL_PORT"] = str(relay.port)
    os.environ.setdefault("MAIL_TIMEOUT_SECONDS", "5")
    os.environ.update(env)
    records = Records()
    logger = logging.getLogger(mailer.__name__)
    logger.addHandler(records)
    logger.setLevel(logging.INFO)
    try:
        yield records
    finally:
        logger.removeHandler(records)
        for key in [k for k in os.environ if k.startswith("MAIL_")]:
            del os.environ[key]
        os.environ.update(saved)
        if relay is not None:
            relay.close()


def raises(kind, action) -> Exception:
    try:
        action()
    except kind as exc:
        return exc
    raise AssertionError(f"{kind.__name__} 를 기대했는데 아무 예외 없이 지나갔다")


def parsed(mail: dict) -> email.message.EmailMessage:
    return email.message_from_bytes(mail["data"], policy=email.policy.default)


# ── 계약 ──────────────────────────────────────────────────────────────────

def check_plain_fallback_delivers_and_warns():
    """기본 정책 · 중계가 STARTTLS 를 끊는다 → 새 연결로 평문 발송, 경고 한 줄."""
    relay = FakeRelay("drop")
    with stage(relay) as log:
        mailer.send("제목", to=["a@example.test"], sender=SENDER, html="<p>본문</p>")
    assert "STARTTLS" in relay.commands, "STARTTLS 를 시도하지 않았다"
    assert len(relay.mails) == 1, f"배달이 {len(relay.mails)}통이다"
    assert relay.connections == 2, f"끊긴 뒤 새로 이어야 한다 — 연결 {relay.connections}번"
    warned = [m for level, m in log.lines if level == "WARNING" and "평문" in m]
    assert warned, f"평문으로 물러난 경고가 없다: {log.lines}"


def check_required_tls_fails_instead_of_falling_back():
    """MAIL_USE_TLS=true · STARTTLS 가 끊긴다 → 실패하고 평문으로 보내지 않는다."""
    relay = FakeRelay("drop")
    with stage(relay, MAIL_USE_TLS="true"):
        raises(mailer.MailError,
               lambda: mailer.send("제목", to=["a@example.test"], sender=SENDER, text="본문"))
    assert not relay.mails, "TLS 를 요구했는데 평문으로 나갔다"
    assert relay.connections == 1, f"평문으로 다시 이었다 — 연결 {relay.connections}번"


def check_required_tls_fails_when_not_advertised():
    relay = FakeRelay("none")
    with stage(relay, MAIL_USE_TLS="1"):
        raises(mailer.MailError,
               lambda: mailer.send("제목", to=["a@example.test"], sender=SENDER, text="본문"))
    assert not relay.mails, "TLS 를 요구했는데 평문으로 나갔다"


def check_tls_off_does_not_try():
    relay = FakeRelay("drop")
    with stage(relay, MAIL_USE_TLS="false"):
        mailer.send("제목", to=["a@example.test"], sender=SENDER, text="본문")
    assert "STARTTLS" not in relay.commands, "끄라고 했는데 STARTTLS 를 시도했다"
    assert len(relay.mails) == 1 and relay.connections == 1


def check_not_advertised_sends_plain_with_warning():
    relay = FakeRelay("none")
    with stage(relay) as log:
        mailer.send("제목", to=["a@example.test"], sender=SENDER, text="본문")
    assert len(relay.mails) == 1 and relay.connections == 1
    assert any(level == "WARNING" for level, _ in log.lines), "평문 발송의 경고가 없다"


def check_bcc_in_envelope_not_in_headers():
    relay = FakeRelay("drop")
    with stage(relay):
        mailer.send("제목", to=["a@example.test", "b@example.test"], cc=["c@example.test"],
                    bcc=["hidden@example.test"], sender=SENDER, html="<p>본문</p>")
    mail = relay.mails[0]
    assert mail["from"] == SENDER
    assert sorted(mail["rcpts"]) == sorted(
        ["a@example.test", "b@example.test", "c@example.test", "hidden@example.test"]), \
        f"봉투 수신자가 다르다: {mail['rcpts']}"
    assert b"hidden@example.test" not in mail["data"], "bcc 주소가 메일 머리 · 본문에 보인다"
    message = parsed(mail)
    assert message["Bcc"] is None
    assert message["To"] == "a@example.test, b@example.test"
    assert message["Cc"] == "c@example.test"


def check_message_shape():
    """HTML 은 평문 짝과 함께 간다 · 제목 한글이 산다 · Message-ID 는 발신자 도메인."""
    relay = FakeRelay("drop")
    html = "<p>한글 본문</p>"
    with stage(relay):
        mailer.send("[주간] 한글 제목", to="a@example.test", sender=SENDER, html=html)
    message = parsed(relay.mails[0])
    assert message["Subject"] == "[주간] 한글 제목"
    assert message["From"] == SENDER
    assert message["Message-ID"].rstrip(">").endswith("@example.test"), message["Message-ID"]
    assert message["Date"], "Date 머리가 없다"
    assert message.get_content_type() == "multipart/alternative"
    assert message.get_body(("plain",)).get_content().strip() == mailer.HTML_ONLY_NOTE
    assert message.get_body(("html",)).get_content().strip() == html
    assert relay.mails[0]["rcpts"] == ["a@example.test"], "문자열 수신자가 주소 하나로 안 갔다"


def check_refused_recipient_raises():
    relay = FakeRelay("drop", refuse=["gone@example.test"])
    with stage(relay):
        exc = raises(mailer.MailRefused, lambda: mailer.send(
            "제목", to=["a@example.test", "gone@example.test"], sender=SENDER, text="본문"))
    assert "gone@example.test" in exc.refused, exc.refused


def check_all_refused_raises_same_kind():
    relay = FakeRelay("drop", refuse=["gone@example.test"])
    with stage(relay):
        raises(mailer.MailRefused, lambda: mailer.send(
            "제목", to=["gone@example.test"], sender=SENDER, text="본문"))
    assert not relay.mails


def check_load_recipients_rejects_before_work():
    with tempfile.TemporaryDirectory() as tmp, stage():
        path = pathlib.Path(tmp) / "recipients.json"

        def rejects(content, phrase: str):
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(content if isinstance(content, str) else json.dumps(content),
                                encoding="utf-8")
            exc = raises(mailer.MailConfigError, lambda: mailer.load_recipients(path))
            assert phrase in str(exc), f"{phrase!r} 를 기대했는데: {exc}"

        rejects(None, "없다")
        rejects("{ 깨진", "깨졌다")
        rejects([], "객체가 아니다")
        rejects({"to": ["a@example.test"]}, "from 이 없다")
        rejects({"from": SENDER, "to": []}, "to 가 비어 있다")
        rejects({"from": SENDER}, "to 가 비어 있다")
        rejects({"from": SENDER, "to": {"a": 1}}, "주소 목록")
        rejects({"from": SENDER, "to": ["a@example.test, b@example.test"]}, "주소가 아닌")
        rejects({"from": SENDER, "to": ["a@example.test"], "bcc": [42]}, "주소가 아닌")
        rejects({"from": SENDER, "to": ["a@example.test"], "error_notify": "nobody"},
                "주소가 아닌")

        path.write_text(json.dumps({"from": SENDER, "to": "a@example.test",
                                    "bcc": ["h@example.test"], "_comment": "x"}),
                        encoding="utf-8")
        got = mailer.load_recipients(path)
        assert got == {"sender": SENDER, "to": ["a@example.test"], "cc": [],
                       "bcc": ["h@example.test"]}, got


def check_default_sender_fills_missing_from():
    with tempfile.TemporaryDirectory() as tmp, stage(MAIL_DEFAULT_SENDER=SENDER):
        path = pathlib.Path(tmp) / "recipients.json"
        path.write_text(json.dumps({"to": ["a@example.test"]}), encoding="utf-8")
        assert mailer.load_recipients(path)["sender"] == SENDER


def check_bad_settings_rejected():
    for env, phrase in (({"MAIL_USE_TLS": "maybe"}, "MAIL_USE_TLS"),
                        ({"MAIL_PORT": "smtp"}, "MAIL_PORT"),
                        ({"MAIL_PORT": "0"}, "MAIL_PORT"),
                        ({"MAIL_TIMEOUT_SECONDS": "0"}, "MAIL_TIMEOUT_SECONDS"),
                        ({"MAIL_DEFAULT_SENDER": "nobody"}, "MAIL_DEFAULT_SENDER")):
        with stage(**env):
            exc = raises(mailer.MailConfigError, mailer.settings)
            assert phrase in str(exc), exc
    with stage():
        config = mailer.settings()
        assert (config.host, config.port, config.tls) == ("antispam.posco.net", 25, "try"), \
            "기본값이 실측한 중계와 다르다"


def check_notify_swallows_its_own_errors():
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "recipients.json"
        path.write_text(json.dumps({"from": SENDER, "to": ["a@example.test"],
                                    "error_notify": "ops@example.test"}), encoding="utf-8")

        closed = socket.socket()
        closed.bind(("127.0.0.1", 0))
        dead_port = closed.getsockname()[1]
        closed.close()
        with stage(MAIL_HOST="127.0.0.1", MAIL_PORT=str(dead_port), MAIL_TIMEOUT_SECONDS="3"):
            assert mailer.notify("알림", "본문", recipients_file=path) is False

        with stage(MAIL_PORT="not-a-port"):
            assert mailer.notify("알림", "본문", recipients_file=path) is False
        with stage():
            assert mailer.notify("알림", "본문",
                                 recipients_file=pathlib.Path(tmp) / "none.json") is False
        relay = FakeRelay("drop", refuse=["ops@example.test"])
        with stage(relay):
            assert mailer.notify("알림", "본문", recipients_file=path) is False

        relay = FakeRelay("drop")
        with stage(relay):
            assert mailer.notify("알림", "본문", recipients_file=path) is True
        assert relay.mails[0]["rcpts"] == ["ops@example.test"], "error_notify 가 안 받았다"

        # error_notify 가 없으면 to 의 첫 주소 — 수신자 설정이 틀려 멈춘 판에도 나간다
        path.write_text(json.dumps({"from": SENDER, "to": ["first@example.test", "x"]}),
                        encoding="utf-8")
        relay = FakeRelay("drop")
        with stage(relay):
            assert mailer.notify("알림", "본문", recipients_file=path) is True
        assert relay.mails[0]["rcpts"] == ["first@example.test"]


CHECKS = [value for name, value in sorted(globals().items()) if name.startswith("check_")]


def main() -> int:
    print(f"잰다: {TREE / 'mailer.py'}")
    passed = unmeasured = 0
    for check in CHECKS:
        try:
            check()
        except Unmeasured as exc:
            unmeasured += 1
            print(f"? {check.__name__}: 못 쟀다 — {exc}")
        except AssertionError as exc:
            print(f"✗ {check.__name__}: {exc}")
        except Exception:
            print(f"✗ {check.__name__}: 예상 못 한 예외\n{traceback.format_exc()}")
        else:
            passed += 1
            print(f"✓ {check.__name__}")
    print(f"통과 {passed}/{len(CHECKS)}" + (f" · 못 잼 {unmeasured}" if unmeasured else ""))
    if passed == len(CHECKS):
        return 0
    return 1 if passed + unmeasured < len(CHECKS) else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        print("못 쟀다")
        sys.exit(2)
