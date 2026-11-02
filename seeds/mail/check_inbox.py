"""inbox.py 의 계약을 가짜 메일함으로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 받은 메일을 읽다가 **읽음 표시를 바꾸나**(사람이 새 메일을 못
알아본다 · 되돌릴 수 없다) · 끊긴 세션을 빈 받은편지함으로 읽나(새 메일이 안 온 것처럼
조용히 지나간다) · 첨부가 바이트 그대로 오나.

가짜 메일함은 사내 메일함에서 잰 꼴을 흉내 낸다(inbox.py 머리말의 실측) — 목록은
XML, 본문은 MIME 조각, 첨부는 $FILE, ``?OpenDocument`` 를 부르면 그 메일이 읽음이
되고, 쿠키가 없으면 200 에 SSO 로 보내는 HTML 을 준다.

돌리는 법::

    python -X utf8 -I check_inbox.py [inbox.py 가 든 폴더]

폴더를 안 주면 이 파일의 폴더를 잰다. 일부러 틀린 사본을 다른 폴더에 두고 그
폴더를 주면 물림(검사가 정말 무나)을 잰다.

판정 — 끝 줄이 「통과 N/N」 이면 종료 코드 0, 하나라도 어긋나면 1, 가짜 메일함을
못 띄우는 등 재지 못했으면 2.

언제 걷나 — inbox.py 가 사라지거나, 같은 계약을 실물 메일함에서 재는 검사가 서서
이 검사가 더하는 믿음이 없어지면.

여기서 못 재는 것 — 사내 SSO 를 넘는 길(mail_login.js) · 실물 메일함의 다른 꼴의 메일.
"""

from __future__ import annotations

import contextlib
import http.server
import json
import pathlib
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse

TREE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else __file__).resolve()
TREE = TREE if TREE.is_dir() else TREE.parent
sys.path.insert(0, str(TREE))
import inbox  # noqa: E402 — 잴 나무가 sys.path 에 먼저 서야 한다

DB = "/02/mail2/000000.nsf"
COOKIE = ("DomAuthSessId", "good-session")
UNREAD_ID = "4AD9FBC3FAE3C2A449258EA30055EEE6"
READ_ID = "61303BF62C8FC9F049258EA300307B9E"
ATTACHMENT = "probe-표.csv"
ATTACHMENT_BYTES = "이름,값\n가,1\n".encode("utf-8") + bytes([0, 255, 13, 10])
# 끊긴 세션에 사내 메일함이 내는 답의 첫머리(실측) — 200 · text/html
LOGIN_PAGE = ('<html><head><script>document.cookie = "EP_CERTIFY_CA=; path=/; domain=.posco.net;";'
              'window.location.href="http://swpsso.posco.net/idms/U61/jsp/login/login.jsp";'
              '</script></head><body></body></html>')


class Unmeasured(Exception):
    """잴 판을 못 세웠다 — 어긋남이 아니라 「못 쟀다」다."""


# ── 가짜 메일함 ───────────────────────────────────────────────────────────

class FakeMailbox:
    """127.0.0.1 의 Domino 웹메일 흉내. `paths` 는 받은 요청 주소, `read` 는 읽음이 된 메일."""

    def __init__(self, session: str = "ok"):
        self.session = session        # "ok" · "login"(200 HTML) · "redirect"(302 SSO)
        self.paths: list[str] = []
        self.read = {READ_ID}
        box = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                box.paths.append(self.path)
                box.answer(self)

        try:
            self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        except OSError as exc:
            raise Unmeasured(f"가짜 메일함을 못 띄웠다: {exc}") from exc
        self.url = f"http://127.0.0.1:{self.server.server_port}{DB}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def answer(self, handler) -> None:
        raw = urllib.parse.unquote(handler.path)
        if self.session == "redirect":
            return self.send(handler, 302, b"", "text/html", location="http://swpsso.example/login.jsp")
        if f"{COOKIE[0]}={COOKIE[1]}" not in (handler.headers.get("Cookie") or "") or self.session == "login":
            return self.send(handler, 200, LOGIN_PAGE.encode(), "text/html")
        if not raw.startswith(DB):
            return self.send(handler, 404, b"", "text/html")
        rest = raw[len(DB):]
        lowered = rest.lower()
        if "?opendocument" in lowered or "?editdocument" in lowered:
            for unid in (UNREAD_ID, READ_ID):
                if unid.lower() in lowered:
                    self.read.add(unid)
            return self.send(handler, 200, b"<html>mail page</html>", "text/html; charset=UTF-8")
        if "?readviewentries" in lowered:
            return self.send(handler, 200, self.view_xml(), "text/xml; charset=UTF-8")
        if rest == f"/0/{UNREAD_ID}/Body/M1.1?OpenElement":
            return self.send(handler, 200, "본문 첫 줄\n둘째 줄".encode(), "text/plain; charset=utf-8")
        if rest == f"/0/{UNREAD_ID}/Body/M1.2?OpenElement":
            return self.send(handler, 200, "<p>본문 첫 줄</p>".encode(), "text/html; charset=UTF-8")
        if rest == f"/0/{UNREAD_ID}/$FILE/{ATTACHMENT}":
            return self.send(handler, 200, ATTACHMENT_BYTES, "application/octet-stream")
        return self.send(handler, 404, b"<html>not found</html>", "text/html")

    def view_xml(self) -> bytes:
        def entry(position, unid, subject, attachments):
            mark = "ico-okmail" if unid in self.read else "z^ico-nomail"
            cols = {"xsubject": subject, "xname": "보낸이 &lt;a@example.test&gt;",
                    "xdate": "2026-11-03 09:00:00", "xsize": "5KB", "xImportance": "2",
                    "attachment": attachments, "read": mark}
            data = "".join(f'<entrydata columnnumber="{i}" name="{k}"><text>{v}</text></entrydata>'
                           for i, (k, v) in enumerate(cols.items()))
            return f'<viewentry position="{position}" unid="{unid}" noteid="1" siblings="2">{data}</viewentry>'
        body = (entry(1, UNREAD_ID, "새 메일", f"probe-note.txt{{}}{ATTACHMENT}")
                + entry(2, READ_ID, "읽은 메일", ""))
        return (f'<?xml version="1.0" encoding="UTF-8"?><viewentries timestamp="20261103T000000,00Z" '
                f'toplevelentries="2">{body}</viewentries>').encode()

    @staticmethod
    def send(handler, code, body, kind, location=None):
        handler.send_response(code)
        handler.send_header("Content-Type", kind)
        handler.send_header("Content-Length", str(len(body)))
        if location:
            handler.send_header("Location", location)
        handler.end_headers()
        handler.wfile.write(body)


@contextlib.contextmanager
def stage(session: str = "ok", cookie=COOKIE, expires=-1):
    """가짜 메일함과 그 메일함을 가리키는 쿠키 파일을 세운다. 내는 것 — (메일함, Mailbox)."""
    box = FakeMailbox(session)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cookies = pathlib.Path(tmp) / "session.json"
            cookies.write_text(json.dumps({"cookies": [
                {"name": cookie[0], "value": cookie[1], "domain": "127.0.0.1", "path": "/",
                 "expires": expires, "httpOnly": True, "secure": False}]}), encoding="utf-8")
            yield box, inbox.Mailbox(box.url + "/FrameNew?openform", cookies, timeout=5)
    finally:
        box.close()


def raises(kind, action) -> Exception:
    try:
        action()
    except kind as exc:
        return exc
    raise AssertionError(f"{kind.__name__} 가 안 났다")


# ── 검사 ─────────────────────────────────────────────────────────────────

def check_reading_everything_keeps_unread():
    with stage() as (box, mailbox):
        mails = mailbox.list()
        new = next(m for m in mails if m.unid == UNREAD_ID)
        mailbox.body(new, "text")
        mailbox.body(new, "html")
        for name in new.attachments:
            with contextlib.suppress(inbox.MailboxError):
                mailbox.attachment(new, name)
        assert UNREAD_ID not in box.read, "목록 · 본문 · 첨부를 받다가 메일이 읽음이 됐다"
        opened = [p for p in box.paths if "opendocument" in p.lower() or "editdocument" in p.lower()]
        assert not opened, f"읽음 표시를 바꾸는 주소를 불렀다: {opened}"
        assert mailbox.list()[0].unread, "다시 읽은 목록에서 새 메일이 읽음으로 보인다"


def check_marking_url_is_refused_before_asking():
    with stage() as (box, mailbox):
        raises(inbox.MailboxError, lambda: mailbox._get(f"/0/{UNREAD_ID}?OpenDocument"))
        assert not box.paths, f"막아야 할 주소가 서버에 닿았다: {box.paths}"


def check_list_shape():
    with stage() as (_, mailbox):
        mails = mailbox.list()
        assert [m.unid for m in mails] == [UNREAD_ID, READ_ID], mails
        new, old = mails
        assert new.unread and not old.unread, (new.unread, old.unread)
        assert new.subject == "새 메일", new.subject
        assert new.sender == "보낸이 <a@example.test>", new.sender
        assert new.attachments == ("probe-note.txt", ATTACHMENT), new.attachments
        assert old.attachments == (), old.attachments


def check_body_text_and_html():
    with stage() as (_, mailbox):
        assert mailbox.body(UNREAD_ID, "text") == "본문 첫 줄\n둘째 줄"
        assert mailbox.body(UNREAD_ID, "html") == "<p>본문 첫 줄</p>"
        assert mailbox.body(READ_ID, "text") is None, "본문 조각이 없는 메일에 None 이 아니다"


def check_attachment_bytes_exact():
    with stage() as (_, mailbox):
        assert mailbox.attachment(UNREAD_ID, ATTACHMENT) == ATTACHMENT_BYTES, "첨부 바이트가 바뀌었다"


def check_login_page_is_session_expired_not_empty_inbox():
    with stage(session="login") as (_, mailbox):
        raises(inbox.SessionExpired, mailbox.list)
        raises(inbox.SessionExpired, lambda: mailbox.body(UNREAD_ID, "html"))


def check_redirect_is_session_expired_and_not_followed():
    with stage(session="redirect") as (box, mailbox):
        raises(inbox.SessionExpired, mailbox.list)
        assert len(box.paths) == 1, f"리다이렉트를 따라갔다: {box.paths}"


def check_expired_cookie_is_dropped():
    with stage(expires=time.time() - 60) as (_, mailbox):
        raises(inbox.SessionExpired, mailbox.list)


def check_bad_config_rejected_before_asking():
    with tempfile.TemporaryDirectory() as tmp:
        missing = pathlib.Path(tmp) / "none.json"
        raises(inbox.MailboxConfigError, lambda: inbox.Mailbox("http://127.0.0.1/x.nsf", missing))
        empty = pathlib.Path(tmp) / "empty.json"
        empty.write_text(json.dumps({"cookies": []}), encoding="utf-8")
        raises(inbox.MailboxConfigError, lambda: inbox.Mailbox("http://127.0.0.1/x.nsf", empty))
        raises(inbox.MailboxConfigError, lambda: inbox.Mailbox("http://127.0.0.1/inbox", empty))
    with stage() as (_, mailbox):
        raises(inbox.MailboxConfigError, lambda: mailbox.body("../../names.nsf", "text"))
        raises(inbox.MailboxConfigError, lambda: mailbox.body(UNREAD_ID, "pdf"))


CHECKS = [value for name, value in sorted(globals().items()) if name.startswith("check_")]


def main() -> int:
    print(f"잰다: {TREE / 'inbox.py'}")
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
