"""inbox.py 의 계약을 가짜 메일함으로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 메일함을 읽다가 **읽음 표시를 바꾸나**(사람이 새 메일을 못 알아본다 · 되돌릴 수 없다) · 읽기 길이
메일함을 바꾸는 주소를 서버에 보내나 · 끊긴 세션을 빈 받은편지함이나 「본문 없음」으로 읽나(새 메일이 안 온 것처럼 조용히
지나간다) · 하위 폴더 메일을 조용히 빠뜨리나 · 잰 꼴(보낸 사람 열 · 받는 꼴 · 받는 사람 목록 · 본문 · ECM 첨부 이름 · 주소록)을
잘못 풀어 사람 · 주소를 조용히 잃나 · 메일함을 바꾸는 손 둘이 그 메일 하나만 바꾸나.
남기는 까닭(check-design §1 넷) — 길이 분명하다(메일함 손을 고칠 때마다 · 이 파일을 그 자리에서 쓰는 앱이 있다) · 읽음이
바뀌거나 메일이 빠지면 조용하고 되돌릴 수 없다 · 쓰는 사람이 새 메일을 놓친다 · 다른 무엇도 안 잡는다(회사 메일함은 회사
PC 에서만 닿는다).

가짜 메일함은 사내 메일함에서 잰 주소 · 꼴을 흉내 낸다 — 꼴의 원본은 inbox.py 머리말 「사내 메일함에서 잰 것」이 가리키는
기록이다(이 파일은 inbox.py 의 값을 읽어 오지 않는다). 메일함 흉내가 지키는 것 — 여는 주소(``?OpenDocument`` ·
``?EditDocument``)를 부르면 그 메일이 읽음이 되고 ``ag_read_cancel`` 은 안 읽음(``z^ico-nomail``)으로 되돌린다. 쿠키가 없거나
세션이 끊긴 판이면 200 에 SSO 로 보내는 HTML 을 준다. 받은편지함 보기는 받은편지함 메일만 내고, 폴더 보기는 unid 로만 열리며
(제목으로 열면 0줄), 받는 사람 목록 · 모든편지함 보기는 기본 정렬이 날짜순이 아니다.

돌리는 법::

    python -X utf8 -I check_inbox.py [inbox.py 가 든 폴더]

폴더를 안 주면 이 파일의 폴더를 잰다. 일부러 틀린 사본을 다른 폴더에 두고 그 폴더를 주면 물림(검사가 정말 무나)을 잰다.

판정 — 끝 줄이 「통과 N/N」 이면 종료 코드 0, 하나라도 어긋나면 1, 가짜 메일함을 못 띄우는 등 재지 못했으면 2.

언제 걷나 — inbox.py 가 사라지거나, 같은 계약을 실물 메일함에서 재는 검사가 서서 이 검사가 더하는 믿음이 없어지면.

여기서 못 재는 것 — 사내 SSO 를 넘는 길(mail_login.js) · 회사에서 안 잰 꼴(끊긴 세션의 세션 확인 답 · 중요도 값의 뜻 ·
폴더에만 있는 메일에 읽음으로의 주소가 먹는지 — 여기서는 어느 메일이든 먹는다 · 모든편지함을 장으로 넘길 때의 차례 ·
평문 · HTML 둘을 든 메일 밖의 평문 조각).
"""

from __future__ import annotations

import contextlib
import hashlib
import http.server
import json
import logging
import pathlib
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

TREE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else __file__).resolve()
TREE = TREE if TREE.is_dir() else TREE.parent
sys.path.insert(0, str(TREE))
import inbox  # noqa: E402 — 잴 나무가 sys.path 에 먼저 서야 한다

# 「보기가 없다」 경고는 일부러 세운 판의 것이다 — 판정 줄 사이에 안 끼게 받아 버린다
logging.getLogger(inbox.__name__).addHandler(logging.NullHandler())

DB = "/02/mail2/000000.nsf"
COOKIE = ("DomAuthSessId", "good-session")
# 끊긴 세션에 사내 메일함이 내는 답의 첫머리(실측) — 200 · text/html
LOGIN_PAGE = ('<html><head><script>document.cookie = "EP_CERTIFY_CA=; path=/; domain=.posco.net;";'
              'window.location.href="http://swpsso.posco.net/idms/U61/jsp/login/login.jsp";'
              '</script></head><body></body></html>')
# 보기 열(실측) — 받은편지함 · 보낸편지함. 폴더 보기는 받는 꼴 · 중요도 · 관련 문서가 빠지고 셋이 더해지고,
# 모든편지함은 관련 문서가 빠지고 폴더 열이 더해진다
INBOX_COLUMNS = ("xstar", "$81", "read", "xrtype", "xname", "xsubject", "xdate", "xsize", "$91", "attachment",
                 "xImportance", "xnh_read", "xrelatedid", "xforward_deny", "xremindopt", "xunopenedopt", "xbriefingopt")
FOLDER_COLUMNS = tuple(c for c in INBOX_COLUMNS if c not in ("xrtype", "xImportance", "xrelatedid")) + (
    "nh_read", "LOCALSAVE", "Security")
ALL_COLUMNS = tuple(c for c in INBOX_COLUMNS if c != "xrelatedid") + ("xfoldername",)
SENT_COLUMNS = ("xname", "xsubject", "xdate", "xstatus", "xoridocid", "xsendstatus")
RECIPIENT_VIEW, RECIPIENT_VIEW_UNID = "!전체목록추출용", "6E1B0F2A9C3D4E5F60718293A4B5C6D7"
ALL_VIEW, ALL_VIEW_UNID = "XML_모든편지함", "3C5D7E9F0A1B2C3D4E5F60718293A4B5"
SYSTEM_FOLDERS = ("($Inbox)", "($Trash)", "(Drafts)", "(Sent)", "($Alarms)")
FOLDER_PAGE_MAX = 1000          # 폴더 보기의 count 는 여기서 잘린다(실측)
COMPANY = "누리소재(07)"


class Unmeasured(Exception):
    """잴 판을 못 세웠다 — 어긋남이 아니라 「못 쟀다」다."""


def folder_unid(path: str) -> str:
    """폴더 경로 → 그 폴더 보기의 unid(32자리 16진). 가짜 메일함 안에서만 쓰는 값이다."""
    return hashlib.md5(f"fake-folder/{path}".encode()).hexdigest().upper()


def internal_sender(name: str, addr: str, name_eng: str) -> str:
    """사내 보낸 사람 열의 글자(XML 을 푼 뒤) — ``&lt;`` 는 XML 안에서 한 번 더 이스케이프된다(실측)."""
    return f"{name}-=spl=-{name} &lt;{addr}&gt;-ENG-{name_eng}-=spl=-{name_eng}&lt;{addr}&gt;"


def shown(stamp: str) -> tuple[str, str]:
    """YYYYMMDDHHMMSS → (xdate, $91) — 메일함이 주는 두 꼴(실측)."""
    s = stamp
    return f"{s[:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}:{s[12:]}", f"{s[:8]}T{s[8:]},00+09"


# ── 이야기 — 잰 꼴을 고루 담은 작은 메일함. 회사 · 사람은 다 지어낸 것이다 ─────────────────────

@dataclass
class FakeMail:
    """받은 메일 한 통. ``folder`` — 빈 글자는 받은편지함, 경로는 그 폴더, None 은 어느 폴더 보기에도 없는 메일.

    ``to_102`` 가 None 이면 받는 사람 목록 보기에 없다. ``label`` 을 주면 모든편지함의 폴더 열이 그 값을 든다 — 실물에서
    폴더 열이 폴더와 어긋나는 꼴이다.
    """
    unid: str
    subject: str
    stamp: str                      # YYYYMMDDHHMMSS (서울) — 차례의 원본
    sender: str
    role: str = "T"
    unread: bool = True
    cancelled: bool = False         # 되돌린 안 읽음 — 읽음 열이 z^ico-nomail
    attachments: tuple[str, ...] = ()
    files: dict[str, bytes] = field(default_factory=dict)
    html: str | None = "<p>본문</p>"
    text: str | None = None         # 평문 조각(M1.1) — 평문 · HTML 둘을 든 메일만
    to_102: str | None = ""
    folder: str | None = ""
    label: str | None = None
    importance: str = ""

    def folder_label(self) -> str:
        """모든편지함의 폴더 열 — 받은편지함 ``[${INBOX}]`` · 하위 폴더는 끝 이름만(실측)."""
        if self.label is not None:
            return f"[{self.label}]"
        return f"[{self.folder.rsplit(chr(92), 1)[-1]}]" if self.folder else "[${INBOX}]"

    def cols(self, columns) -> dict:
        mark = ("z^ico-nomail" if self.cancelled else "ico-nomail") if self.unread else "ico-okmail"
        xdate, sort = shown(self.stamp)
        values = {"read": mark, "xrtype": self.role, "xname": self.sender, "xsubject": self.subject, "xdate": xdate,
                  "xsize": " 5KB", "$91": sort, "attachment": "{}".join(self.attachments), "xrelatedid": self.unid,
                  "xImportance": self.importance, "xfoldername": self.folder_label()}
        return {c: values.get(c, "") for c in columns}


@dataclass
class FakeSent:
    """보낸편지함의 메일 한 통 — 목록의 xname 이 수신인이다."""
    unid: str
    subject: str
    stamp: str
    to: str
    in_view: bool = True


U = {name: f"{i:032X}" for i, name in enumerate((
    "alone", "cc", "group", "ecm", "cancelled", "unmatched", "read_one",
    "f_top", "f_child", "f_comma", "f_ghost", "f_trash", "sent_1", "sent_2"), start=0xA1B2C3D4E5F60000)}
OWNER = {"email": "dh.park@nuri.example", "user_name": "박도현", "user_name_eng": "Dohyun Park", "user_id": "dhpark",
         "key": "CN=박도현/OU=DH/O=NURI", "empno": "200001", "company_name": "누리소재", "dept_name": "소재사업부",
         "grade": "부장", "job_title": "그룹장", "is_retire": "N"}
PEER = ("서하늘", "hn.seo@nuri.example", "Haneul Seo")
EXTERNAL = "alex.berg@far-cells.example"
FOLDER_TOP, FOLDER_CHILD, FOLDER_COMMA, FOLDER_EMPTY = "협력사", "프로젝트\\소재 시험", "소식\\공지, 안내", "회의.2026"
# SSO 주소를 적은 사내 안내 본문 — 끊긴 세션의 화면이 아니다
NOTICE = '<p>비밀번호 변경: <a href="http://swpsso.posco.net/idms/U61/jsp/pw.jsp">swpsso.posco.net</a></p>'


def scenario():
    """잰 꼴마다 한 통 — (받은 메일, 보낸 메일). 날짜 차례와 unid 차례가 어긋나게 둔다 — 정렬을 안 붙인 보기를 가려낸다."""
    peer = internal_sender(*PEER)
    mails = [
        FakeMail(U["alone"], "시험 일정 검토 요청", "20261103090000", peer, "T",
                 text="본문 첫 줄\n둘째 줄", to_102=OWNER["key"]),
        FakeMail(U["cc"], "주간 생산 보고", "20261103093000", peer, "C", unread=False, label=FOLDER_TOP,
                 to_102=f"CN=강태오/OU=TO/O=NURI, 박도현 <{OWNER['email']}>, 송재민\t<jm.song@nuri.example>"),
        FakeMail(U["group"], "[전사] 보안 교육 안내", "20261103070000", "notice@nuri.example", "G", html=NOTICE,
                 to_102=f'taeo(강태오), "Berg, Alex"<{EXTERNAL}>, ops@nuri.example'),
        FakeMail(U["ecm"], "분기 실적 자료", "20261103060000", EXTERNAL, "T", html=None, to_102=OWNER["key"],
                 attachments=("분기 실적(pptx_2048KB).html", "메모-표.csv"),
                 files={"메모-표.csv": "이름,값\n가,1\n".encode() + bytes([0, 255, 13, 10])}),
        FakeMail(U["cancelled"], "되돌린 메일", "20261103050000", peer, "T", cancelled=True, to_102=OWNER["key"]),
        FakeMail(U["unmatched"], "옮긴 메일", "20261103040000", peer, "T", to_102=None),
        FakeMail(U["read_one"], "이미 읽은 메일", "20261103030000", peer, "T", unread=False, to_102=OWNER["key"]),
        FakeMail(U["f_top"], "협력사 납기 확인", "20261103083000", "sm.ha@haneul-parts.example", "T",
                 folder=FOLDER_TOP, importance="1", to_102=OWNER["key"]),
        FakeMail(U["f_child"], "소재 시험 결과", "20261103063000", peer, "C", folder=FOLDER_CHILD, importance="2",
                 to_102=f"CN=서하늘/OU=HN/O=NURI, {OWNER['key']}"),
        FakeMail(U["f_comma"], "[안내] 사내 행사", "20261103053000", "notice@nuri.example", "G", folder=FOLDER_COMMA,
                 to_102="ops@nuri.example"),
        FakeMail(U["f_ghost"], "[안내] 어느 폴더에도 없는 메일", "20261103043000", "notice@nuri.example", "G",
                 folder=None, label="공지, 안내", to_102="ops@nuri.example"),
        FakeMail(U["f_trash"], "지운 메일", "20261103033000", peer, "T", folder="($Trash)", to_102=OWNER["key"]),
    ]
    sent = [FakeSent(U["sent_1"], "회신: 주간 생산 보고", "20261103083000",
                     "CN=서하늘/OU=HN/O=NURI, 송재민 <jm.song@nuri.example>"),
            FakeSent(U["sent_2"], "견적 요청", "20261102150000", EXTERNAL, in_view=False)]
    return mails, sent


# ── 가짜 메일함 ───────────────────────────────────────────────────────────

class FakeDomino:
    """127.0.0.1 의 Domino 웹메일 흉내. ``paths`` 는 받은 요청, ``changes`` 는 메일함을 바꾼 요청."""

    def __init__(self, *, session: str = "ok", folders=(), all_view: bool = True, recipient_view: bool = True):
        mails, sent = scenario()
        self.mails = {m.unid: m for m in mails}
        self.sent = sent
        self.session = session            # ok · login(200 HTML) · redirect(302 SSO)
        self.extra_folders = tuple(folders)   # 메일이 없어도 보기 목록에 서는 폴더
        self.all_view = all_view
        self.recipient_view = recipient_view
        self.paths: list[str] = []
        self.changes: list[tuple[str, str]] = []
        self.lock = threading.Lock()
        box = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                with box.lock:
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

    def unread(self) -> set[str]:
        return {u for u, m in self.mails.items() if m.unread}

    def in_inbox(self) -> list[FakeMail]:
        """받은편지함 보기가 내는 메일 — 받은편지함의 것만, 새것부터."""
        return sorted((m for m in self.mails.values() if m.folder == ""), key=lambda m: m.stamp, reverse=True)

    def folder_paths(self) -> list[str]:
        return sorted({*SYSTEM_FOLDERS, *self.extra_folders, *(m.folder for m in self.mails.values() if m.folder)})

    def answer(self, h) -> None:
        raw = urllib.parse.unquote(h.path)
        low = raw.lower()
        if self.session == "redirect":
            return self.send(h, 302, b"", "text/html", location="http://swpsso.example/login.jsp")
        if f"{COOKIE[0]}={COOKIE[1]}" not in (h.headers.get("Cookie") or "") or self.session == "login":
            return self.send(h, 200, LOGIN_PAGE.encode(), "text/html")
        if low == "/common/lib_f.nsf/checksessionstatus?openpage":
            return self.send(h, 200, b'{"status":"login"}', "text/html")
        if low.startswith("/common/profile.nsf/ag_org_search_json?openagent"):
            query = urllib.parse.parse_qs(raw.split("&", 1)[1] if "&" in raw else "", keep_blank_values=True)
            key = query.get("search_key", [""])[0].casefold()
            users = [OWNER] if key and key in (OWNER["email"], OWNER["user_name"], OWNER["empno"]) else []
            return self.send(h, 200, json.dumps({"dept": [], "user": users, "total": len(users)},
                                                ensure_ascii=False).encode(), "text/html; charset=UTF-8")
        if not raw.startswith(DB):
            return self.send(h, 404, b"<html>not found</html>", "text/html")
        rest = raw[len(DB):]
        low = rest.lower()
        if "?opendocument" in low or "?editdocument" in low:
            for unid, mail in self.mails.items():
                if unid.lower() in low:
                    mail.unread, mail.cancelled = False, False
                    self.changes.append(("read", unid))
            return self.send(h, 200, b"<html>mail page</html>", "text/html; charset=UTF-8")
        if low.startswith("/ag_read_cancel?openagent"):
            docid = urllib.parse.parse_qs(rest.split("?", 1)[1]).get("docid", [""])[0]
            if docid in self.mails:
                self.mails[docid].unread, self.mails[docid].cancelled = True, True
                self.changes.append(("unread", docid))
            return self.send(h, 200, b"<html><head></head><body></body></html>", "text/html")
        if rest == "/api/data/collections":
            views = [{"@title": "XML_Inbox", "@unid": "2" * 32, "@folder": False},
                     {"@title": "XML_Sent", "@unid": "3" * 32, "@folder": False}]
            views += [{"@title": p, "@unid": folder_unid(p), "@folder": True} for p in self.folder_paths()]
            if self.recipient_view:
                views.append({"@title": RECIPIENT_VIEW, "@unid": RECIPIENT_VIEW_UNID, "@folder": False})
            if self.all_view:
                views.append({"@title": ALL_VIEW, "@unid": ALL_VIEW_UNID, "@folder": False})
            return self.send(h, 200, json.dumps(views, ensure_ascii=False).encode(), "application/json; charset=UTF-8")
        if "?readviewentries" in low:
            return self.send(h, 200, self.view(rest), "text/xml; charset=UTF-8")
        parts = rest.split("/")
        if len(parts) >= 4 and parts[1] == "0" and parts[2] in self.mails:
            mail, tail = self.mails[parts[2]], "/".join(parts[3:])
            if tail == "Body?OpenField":
                if mail.html is None:
                    return self.send(h, 404, b"<html>not found</html>", "text/html")
                return self.send(h, 200, mail.html.encode(), "text/html; charset=UTF-8")
            if tail.endswith("?OpenField"):
                return self.send(h, 501, b"<html>not implemented</html>", "text/html")
            if tail == "Body/M1.1?OpenElement" and mail.text is not None:
                return self.send(h, 200, mail.text.encode(), "text/plain; charset=utf-8")
            if tail == "Body/M1.2?OpenElement" and mail.text is not None and mail.html is not None:
                return self.send(h, 200, mail.html.encode(), "text/html; charset=UTF-8")
            if parts[3] == "$FILE" and "/".join(parts[4:]) in mail.files:
                return self.send(h, 200, mail.files["/".join(parts[4:])], "application/octet-stream")
        return self.send(h, 404, b"<html>not found</html>", "text/html")

    def view(self, rest: str) -> bytes:
        name, query = rest[1:].split("?", 1)
        q = urllib.parse.parse_qs(query.replace("ReadViewEntries", "", 1), keep_blank_values=True)
        count, start = int(q.get("count", ["30"])[0]), int(q.get("start", ["1"])[0])
        descending = q.get("ResortDescending", [""])[0] == "1"
        key = name.lower()
        if key == "xml_inbox":
            rows = [(m.unid, m.cols(INBOX_COLUMNS)) for m in self.in_inbox()]
        elif key == "xml_sent":
            rows = [(s.unid, dict(zip(SENT_COLUMNS, (s.to, s.subject, shown(s.stamp)[0], "", "", ""))))
                    for s in sorted(self.sent, key=lambda s: s.stamp, reverse=True)]
        elif self.recipient_view and key == RECIPIENT_VIEW_UNID.lower():
            got = [(m.unid, m.stamp, "수신", m.to_102) for m in self.mails.values() if m.to_102 is not None]
            got += [(s.unid, s.stamp, "발신", s.to) for s in self.sent if s.in_view]
            # 기본 정렬은 날짜순이 아니다(실측) — unid 차례로 낸다. ResortDescending=1 이면 날짜 내림차순
            got.sort(key=(lambda r: r[1]) if descending else (lambda r: r[0]), reverse=descending)
            rows = [(u, {"xsubject": "", "$101": shown(st)[1], "$91": d, "$102": to, "$103": "", "xname": ""})
                    for u, st, d, to in got]
        elif self.all_view and key == ALL_VIEW_UNID.lower():
            got = [m for m in self.mails.values() if m.folder is None or not m.folder.startswith("(")]
            got.sort(key=(lambda m: m.stamp) if descending else (lambda m: m.unid), reverse=descending)
            rows = [(m.unid, m.cols(ALL_COLUMNS)) for m in got]
        else:
            # 폴더 보기는 unid 로만 열린다 — 제목으로 열면 0줄(실측). 모르는 보기도 빈 목록이다
            folder = next((p for p in self.folder_paths() if folder_unid(p).lower() == key), None)
            got = sorted((m for m in self.mails.values() if folder is not None and m.folder == folder),
                         key=lambda m: m.stamp, reverse=True)
            rows = [(m.unid, m.cols(FOLDER_COLUMNS)) for m in got]
            count = min(count, FOLDER_PAGE_MAX)
        page = rows[start - 1:start - 1 + count]
        body = "".join(
            f'<viewentry position="{start + i}" unid="{unid}" noteid="{start + i:x}" siblings="{len(rows)}">'
            + "".join(f'<entrydata columnnumber="{j}" name="{escape(k)}"><text>{escape(v)}</text></entrydata>'
                      for j, (k, v) in enumerate(cols.items()))
            + "</viewentry>" for i, (unid, cols) in enumerate(page))
        return (f'<?xml version="1.0" encoding="UTF-8"?><viewentries timestamp="20261103T000000,00Z" '
                f'toplevelentries="{len(rows)}">{body}</viewentries>').encode()

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
def stage(*, cookie=COOKIE, expires=-1, **fake):
    """가짜 메일함과 그 메일함을 가리키는 쿠키 파일을 세운다. 내는 것 — (메일함 흉내, Mailbox)."""
    box = FakeDomino(**fake)
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


def changing(paths) -> list[str]:
    return [p for p in paths if any(m in p.lower() for m in ("opendocument", "editdocument", "ag_read_cancel"))]


# ── 메일함 불변 ───────────────────────────────────────────────────────────

def check_reading_everything_keeps_unread():
    with stage() as (box, mailbox):
        before = box.unread()
        entries = mailbox.list(count=50)
        for folder in mailbox.folders():
            entries += mailbox.list_folder(folder, count=50)
        mailbox.list_all(count=200)
        mailbox.list_sent(count=50)
        mailbox.recipient_lists(count=200)
        for e in entries:
            mailbox.body(e)
            mailbox.body(e, "text")
            for a in e.attachments:
                if not a.ecm:
                    mailbox.attachment(e, a)
        mailbox.session_alive()
        mailbox.find_people(OWNER["email"], COMPANY)
        assert box.unread() == before, f"읽기만 했는데 안 읽음이 바뀌었다: {sorted(before ^ box.unread())}"
        assert not box.changes and not changing(box.paths), f"메일함을 바꾸는 주소를 불렀다: {changing(box.paths)}"
        again = mailbox.list(count=50)
        assert sum(e.unread for e in again) == len(before & {m.unid for m in box.in_inbox()}), \
            "다시 읽은 목록의 안 읽음 수가 다르다"


def check_changing_urls_are_refused_before_asking():
    unid = U["alone"]
    with stage() as (box, mailbox):
        for path in (f"/0/{unid}?OpenDocument", f"/XML_Inbox/{unid}?OpenDocument", f"/0/{unid}?EditDocument&type=Reply",
                     f"/ag_read_cancel?OpenAgent&docid={unid}&imapuser=0", f"/XML_Inbox/{unid}?opendocument&x=1"):
            raises(inbox.ChangeRefused, lambda p=path: mailbox._get(p))
        # 읽기 전용으로 잰 꼴 밖은 다 막는다 — 메일함을 바꾸는 주소를 다 알지 못해도 새는 길이 없게
        for path in (f"/0/{unid}/SendTo?OpenField", f"/{unid}", "/names.nsf?OpenDatabase"):
            raises(inbox.ChangeRefused, lambda p=path: mailbox._get(p))
        raises(inbox.ChangeRefused, lambda: mailbox._get_server("/common/profile.nsf/ag_read_cancel?OpenAgent"))
        assert not box.paths, f"막아야 할 주소가 서버에 닿았다: {box.paths}"


def check_marking_hands_change_only_that_mail():
    unid = U["alone"]
    with stage() as (box, mailbox):
        before = box.unread()
        mailbox.mark_read(unid)
        assert box.changes == [("read", unid)], box.changes
        assert box.unread() == before - {unid}, "읽음으로가 그 메일 하나만 바꾸지 않았다"
        assert any(p.endswith(f"/XML_Inbox/{unid}?OpenDocument") for p in box.paths), box.paths
        mailbox.mark_unread(unid)
        assert box.unread() == before, "안 읽음으로가 앞 상태로 안 돌렸다"
        mark = next(e for e in mailbox.list(count=50) if e.unid == unid).read_mark
        assert mark == "z^ico-nomail", f"되돌린 메일의 읽음 열: {mark!r}"
        raises(inbox.MailboxConfigError, lambda: mailbox.mark_read("../../names.nsf"))
        raises(inbox.ChangeRefused, lambda: mailbox._send_change(f"{DB}/0/{unid}?OpenDocument"))
    with stage(session="login") as (_, mailbox):
        raises(inbox.SessionExpired, lambda: mailbox.mark_read(unid))


# ── 잰 꼴 풀기 ────────────────────────────────────────────────────────────

def check_list_shape_sender_role_and_paging():
    with stage() as (box, mailbox):
        everything = mailbox.list(count=3, start=1) + mailbox.list(count=50, start=4)
        assert [e.unid for e in everything] == [m.unid for m in box.in_inbox()], \
            "받은편지함을 새것부터 장을 넘기며 잃거나 겹쳤다(폴더 메일은 안 든다)"
        by = {e.unid: e for e in everything}
        assert by[U["alone"]].sender == inbox.Sender(*PEER), by[U["alone"]].sender
        assert by[U["ecm"]].sender == inbox.Sender("", EXTERNAL, ""), by[U["ecm"]].sender
        assert (by[U["alone"]].role, by[U["cc"]].role, by[U["group"]].role) == ("T", "C", "G")
        assert by[U["alone"]].unread and not by[U["read_one"]].unread
        assert by[U["cancelled"]].unread, "되돌린 안 읽음(z^ico-nomail)을 읽음으로 읽었다"
        assert by[U["alone"]].subject == "시험 일정 검토 요청" and by[U["alone"]].folder == ""
        assert (by[U["alone"]].date, by[U["alone"]].date_sort) == shown("20261103090000"), by[U["alone"]]


def check_folders_are_users_own_opened_by_unid():
    """폴더는 쓰는 사람이 지은 것만 · 경로는 보기 목록의 제목 그대로 · 보기는 unid 로 연다 — 제목으로 열면 0줄이 와서 그 폴더의
    메일이 조용히 빠진다. 폴더 줄은 받는 꼴 · 중요도가 빈다(그 보기에 열이 없다)."""
    with stage(folders=(FOLDER_EMPTY,)) as (box, mailbox):
        folders = mailbox.folders()
        # 시스템 폴더((…))는 빠지고, 마디마다 가나다 차례
        assert [f.path for f in folders] == [FOLDER_COMMA, FOLDER_CHILD, FOLDER_TOP, FOLDER_EMPTY], [f.path for f in folders]
        for f in folders:
            got = mailbox.list_folder(f, count=50)
            mine = sorted((m for m in box.mails.values() if m.folder == f.path), key=lambda m: m.stamp, reverse=True)
            assert [e.unid for e in got] == [m.unid for m in mine], f"폴더 보기의 줄이 그 폴더의 메일이 아니다: {f.path}"
            assert all(e.folder == f.path and e.role == "" and e.importance == "" for e in got), got
        raises(inbox.MailboxConfigError, lambda: mailbox.list_folder(inbox.Folder(unid=FOLDER_CHILD, path=FOLDER_CHILD)))


def check_all_mail_view_gives_role_and_importance_newest_first():
    """모든편지함은 날짜 내림차순(Resort)으로 받아야 창에서 끊을 수 있고, 폴더 줄에 없는 받는 꼴 · 중요도를 unid 로 준다."""
    with stage() as (_, mailbox):
        marks = mailbox.list_all(count=200)
        by = {m.unid: m for m in marks}
        assert (by[U["f_top"]].role, by[U["f_top"]].importance) == ("T", "1"), by[U["f_top"]]
        assert (by[U["f_comma"]].role, by[U["f_child"]].role, by[U["f_child"]].importance) == ("G", "C", "2")
        stamps = [m.date_sort for m in marks]
        assert stamps == sorted(stamps, reverse=True), "모든편지함이 날짜 내림차순이 아니다"
    with stage(all_view=False) as (_, mailbox):
        assert mailbox.list_all(count=200) is None, "모든편지함 보기가 없는 메일함에서 None 이 아니다"


def check_recipient_list_view_shapes():
    R = inbox.Recipient
    with stage() as (_, mailbox):
        lists = mailbox.recipient_lists(count=200)
        assert lists[U["cc"]] == (R("강태오", "", "CN=강태오/OU=TO/O=NURI"), R("박도현", OWNER["email"]),
                                  R("송재민", "jm.song@nuri.example")), lists[U["cc"]]
        assert lists[U["group"]] == (R("", "", "taeo(강태오)"), R("Berg, Alex", EXTERNAL), R("", "ops@nuri.example")), \
            lists[U["group"]]
        assert U["unmatched"] not in lists, "보기에 없는 메일이 목록을 받았다"
        assert lists[U["sent_1"]][1] == R("송재민", "jm.song@nuri.example"), "보낸 것의 받는 사람이 안 풀렸다"
    # 한 장으로 받을 때 날짜 내림차순이어야 새 메일이 장 안에 든다 — 기본 정렬(unid 차례)이면 새 메일이 장 밖으로 밀린다
    with stage() as (box, mailbox):
        newest = max((m for m in box.mails.values() if m.to_102 is not None), key=lambda m: m.stamp)
        assert newest.unid in mailbox.recipient_lists(count=1), "받는 사람 목록 한 장이 새것부터가 아니다"
    with stage(recipient_view=False) as (_, mailbox):
        assert mailbox.recipient_lists(count=200) is None, "보기가 없는 메일함에서 None 이 아니다"


def check_body_html_one_path_and_text_part():
    with stage() as (box, mailbox):
        assert mailbox.body(U["alone"]) == "<p>본문</p>", "기본 꼴이 HTML 본문이 아니다"
        assert mailbox.body(U["alone"], "html") == "<p>본문</p>"
        assert mailbox.body(U["alone"], "text") == "본문 첫 줄\n둘째 줄", "평문 조각이 아니다"
        assert mailbox.body(U["read_one"]) == "<p>본문</p>", "평문 조각이 없는 메일의 HTML 본문을 못 받았다"
        assert mailbox.body(U["read_one"], "text") is None, "평문 조각이 없는 메일에 None 이 아니다"
        assert mailbox.body(U["ecm"]) is None, "본문이 없는 메일에 None 이 아니다"
        assert mailbox.body(U["group"]) == NOTICE, "SSO 주소를 적은 본문을 끊긴 세션으로 읽었다"
        html_paths = [p for p in box.paths if "/Body" in p and "OpenElement" not in p]
        assert html_paths and all(p.endswith("/Body?OpenField") for p in html_paths), html_paths


def check_attachments_direct_bytes_and_ecm_names():
    with stage() as (box, mailbox):
        e = next(x for x in mailbox.list(count=50) if x.unid == U["ecm"])
        ecm, memo = e.attachments
        assert (ecm.ecm, ecm.name, ecm.ext, ecm.size_kb) == (True, "분기 실적.pptx", "pptx", 2048), ecm
        assert (memo.ecm, memo.name, memo.ext) == (False, "메모-표.csv", "csv"), memo
        want = box.mails[U["ecm"]].files["메모-표.csv"]
        assert mailbox.attachment(e, memo) == want, "첨부 바이트가 바뀌었다"
        assert mailbox.attachment(U["ecm"], memo.listed) == want, "목록의 이름 그대로 받는 길이 다르다"
        asked = len(box.paths)
        raises(inbox.MailboxConfigError, lambda: mailbox.attachment(e, ecm))
        assert len(box.paths) == asked, "ECM 첨부를 받으러 갔다"


def check_sent_list_recipients():
    with stage() as (_, mailbox):
        sent = {s.unid: s for s in mailbox.list_sent(count=50)}
        assert set(sent) == {U["sent_1"], U["sent_2"]}, sent
        assert sent[U["sent_2"]].recipients == (inbox.Recipient("", EXTERNAL),), sent[U["sent_2"]]


def check_directory_and_session_probe():
    with stage() as (box, mailbox):
        me = mailbox.find_people(OWNER["email"], COMPANY)
        assert len(me) == 1 and (me[0].notes, me[0].grade, me[0].user_id, me[0].retired) == \
            (OWNER["key"], "부장", "dhpark", False), me
        assert mailbox.find_people(EXTERNAL, COMPANY) == [], "밖의 주소가 주소록에 걸렸다"
        asked = [urllib.parse.unquote(p) for p in box.paths if "ag_org_search_json" in p]
        assert asked and all(f"company={COMPANY}" in p for p in asked), asked
        assert mailbox.session_alive() is True
    with stage(session="login") as (_, mailbox):
        assert mailbox.session_alive() is False, "끊긴 세션에 세션 확인이 참이다"


# ── 끊긴 세션 · 설정 ──────────────────────────────────────────────────────

def check_login_page_is_session_expired_not_empty_inbox():
    with stage(session="login") as (_, mailbox):
        raises(inbox.SessionExpired, mailbox.list)
        raises(inbox.SessionExpired, mailbox.list_sent)
        raises(inbox.SessionExpired, mailbox.folders)
        raises(inbox.SessionExpired, lambda: mailbox.recipient_lists(count=10))
        raises(inbox.SessionExpired, lambda: mailbox.body(U["alone"]))
        raises(inbox.SessionExpired, lambda: mailbox.body(U["alone"], "text"))
        raises(inbox.SessionExpired, lambda: mailbox.attachment(U["ecm"], "메모-표.csv"))
        raises(inbox.SessionExpired, lambda: mailbox.find_people(OWNER["email"], COMPANY))


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
    with stage() as (box, mailbox):
        raises(inbox.MailboxConfigError, lambda: mailbox.body("../../names.nsf"))
        raises(inbox.MailboxConfigError, lambda: mailbox.body(U["alone"], "pdf"))
        raises(inbox.MailboxConfigError, lambda: mailbox.find_people("", COMPANY))
        assert not box.paths, box.paths


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
