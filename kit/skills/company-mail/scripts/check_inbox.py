"""inbox.py 의 계약을 가짜 메일함으로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 메일함을 읽다가 **읽음 표시를 바꾸나**(사람이 새 메일을 못 알아본다 · 되돌릴 수 없다) · 읽기 길이
메일함을 바꾸는 주소를 서버에 보내나 · 끊긴 세션을 빈 받은편지함이나 「본문 없음」으로 읽나(새 메일이 안 온 것처럼 조용히
지나간다) · 하위 폴더 메일을 조용히 빠뜨리나 · 잰 꼴(보낸 사람 열 · 받는 꼴 · 받는 사람 목록 · 본문 · ECM 첨부 이름 · 주소록)을
잘못 풀어 사람 · 주소를 조용히 잃나 · 메일함을 바꾸는 손 둘이 그 메일 하나만 바꾸나 · 폴더 · 옮기기 · 규칙 손이 고른 것만 바꾸고
서버의 헛 「OK」를 옮겼다로 읽지 않나 · 메일이 든 폴더를 지워 메일을 휴지통에 보내나 · 규칙에 자동전달을 실어 남에게 메일이 나가게 하나.
남기는 까닭(check-design §1 넷) — 길이 분명하다(메일함 손을 고칠 때마다 · 이 파일을 그 자리에서 쓰는 앱이 있다) · 읽음이
바뀌거나 메일이 빠지면 조용하고 되돌릴 수 없다 · 쓰는 사람이 새 메일을 놓친다 · 다른 무엇도 안 잡는다(회사 메일함은 회사
PC 에서만 닿는다).

가짜 메일함은 사내 메일함에서 잰 주소 · 꼴을 흉내 낸다 — 꼴의 원본은 inbox.py 머리말 「사내 메일함에서 잰 것」이 가리키는
기록이다(이 파일은 inbox.py 의 값을 읽어 오지 않는다). 메일함 흉내가 지키는 것 — 여는 주소(``?OpenDocument`` ·
``?EditDocument``)를 부르면 그 메일이 읽음이 되고 ``ag_read_cancel`` 은 안 읽음(``z^ico-nomail``)으로 되돌린다. 쿠키가 없거나
세션이 끊긴 판이면 200 에 SSO 로 보내는 HTML 을 준다. 받은편지함 보기는 받은편지함 메일만 내고, 폴더 보기는 unid 로만 열리며
(제목으로 열면 0줄), 받는 사람 목록 보기는 기본 정렬이 날짜순이 아니다. 본문 주소에 501 을 내는 메일이 있다(``unserved``). 폴더 보기의 보낸 사람 열은 ``<이름>-ENG-<영문>``(주소
없음)이고 읽음 열은 HTML 조각(``class='mail_21'`` 안 읽음 · ``mail_22`` 읽음)이다. 모든편지함은 정렬 없이 날짜 내림차순이고
``ResortDescending=1`` 이면 내림차순 두 덩이다 — 실물에서 무엇이 가르는지 몰라 여기서는 날짜 차례의 짝수 자리(가장 새 메일부터)를
뒤 덩이로 낸다. 밖의 메일이 폴더 보기에서 서는 이름은 안 쟀다 — 여기서는 주소의 앞쪽만 낸다. 폴더 손 흉내는 실물처럼 늘 「OK」를 내고(모르는 열쇠면
아무것도 안 옮긴다), 메일이 든 폴더를 지우면 그 메일을 휴지통으로 보내며, 메일 쪽을 지워도 이전메일함 짝이 나무에 남는다.
규칙 흉내는 저장 폼을 그대로 들고 편집 화면(``new FormJS`` 머리 · 입력 칸)으로 돌려준다 — 서버가 규칙을 새 메일에 쓰는 일은 흉내 내지 않는다.

돌리는 법::

    python -X utf8 -I check_inbox.py [inbox.py 가 든 폴더]

폴더를 안 주면 이 파일의 폴더를 잰다. 일부러 틀린 사본을 다른 폴더에 두고 그 폴더를 주면 물림(검사가 정말 무나)을 잰다.

판정 — 끝 줄이 「통과 N/N」 이면 종료 코드 0, 하나라도 어긋나면 1, 가짜 메일함을 못 띄우는 등 재지 못했으면 2.

언제 걷나 — inbox.py 가 사라지거나, 같은 계약을 실물 메일함에서 재는 검사가 서서 이 검사가 더하는 믿음이 없어지면.

여기서 못 재는 것 — 사내 SSO 를 넘는 길(스킬 ep-login 의 받는 손) · 회사에서 안 잰 꼴(끊긴 세션의 세션 확인 답 · 중요도 값의 뜻 ·
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

DB = "/02/mail2/200001.nsf"   # 파일 번호 = 메일함 주인(OWNER)의 사번 — 회사의 꼴
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
DRAFT_VIEW, DRAFT_VIEW_UNID = "XML임시편지함", "9A8B7C6D5E4F30211203F4E5D6C7B8A9"
SEARCH_AGENT = "/ag_detail_search_mailbox?open"
SEARCH_SLOTS = {"ssbj": "subject", "sbdy": "html", "satt": "attachments"}   # 검색 손의 칸 → 흉내 메일의 칸
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


def folder_sender(sender: str) -> str:
    """폴더 보기의 보낸 사람 열 — 사내는 ``<이름>-ENG-<영문>``(주소 없음 · 실측), 밖의 주소만 온 메일은 주소의 앞쪽만(머리말)."""
    if "-=spl=-" in sender:
        ko, _, en = sender.partition("-ENG-")
        return f"{ko.partition('-=spl=-')[0]}-ENG-{en.partition('-=spl=-')[0]}"
    return sender.partition("@")[0]


def folder_read(unid: str, unread: bool, position: int) -> str:
    """폴더 보기의 읽음 열(XML 을 푼 뒤 · 실측) — ``div`` 와 ``id`` 사이 빈칸 둘 · 제 unid · 보기 안의 차례 번호."""
    return (f"<div  id='{unid}'><a href='#' class='{'mail_21' if unread else 'mail_22'}'></a>"
            f"<span id='xp_{position}' style='position:relative; top:-20px; left:25px; display:none;'></span></div>")


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
    mark: str = ""                  # 읽은 메일의 읽음 열 — 빈 글자면 ico-okmail · 회신함 ico-post · 전달함 ico-remail
    unserved: bool = False          # 본문 주소에 501 — 실물 메일함에 있는 꼴(폴더에 든 한 통 · inbox.py 머리말 N-가)
    draft: bool = False             # 임시보관함의 메일 — 받은편지함 · 폴더 · 모든편지함 보기에 안 서고 임시보관함 보기에만 선다

    def folder_label(self) -> str:
        """모든편지함의 폴더 열 — 받은편지함 ``[${INBOX}]`` · 하위 폴더는 끝 이름만(실측)."""
        if self.label is not None:
            return f"[{self.label}]"
        return f"[{self.folder.rsplit(chr(92), 1)[-1]}]" if self.folder else "[${INBOX}]"

    def cols(self, columns) -> dict:
        mark = ("z^ico-nomail" if self.cancelled else "ico-nomail") if self.unread else (self.mark or "ico-okmail")
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
    "f_top", "f_child", "f_comma", "f_ghost", "f_trash", "sent_1", "sent_2", "draft"), start=0xA1B2C3D4E5F60000)}
OWNER = {"email": "dh.park@nuri.example", "user_name": "박도현", "user_name_eng": "Dohyun Park", "user_id": "dhpark",
         "key": "CN=박도현/OU=DH/O=NURI", "empno": "200001", "company_name": "누리소재", "dept_name": "소재사업부",
         "dept_code": "n310_00", "grade": "부장", "grade_code": "P40", "job_title": "그룹장", "is_boss": "Y", "is_retire": "N"}
PEER = ("서하늘", "hn.seo@nuri.example", "Haneul Seo")
COLLEAGUE = {**OWNER, "email": PEER[1], "user_name": PEER[0], "user_name_eng": PEER[2], "user_id": "hnseo",
             "key": "CN=서하늘/OU=HN/O=NURI", "empno": "200002", "dept_code": "n310_10", "grade": "차장",
             "grade_code": "P30", "job_title": "일반", "job_title_code": "J10", "is_boss": "N"}
# 이름이 같은 다른 사람(다른 부서) · 같은 부서의 퇴직자 — 이름 찾기의 답에 섞여 오는 사람
HOMONYM = {**COLLEAGUE, "email": "hn.seo2@nuri.example", "user_id": "hnseo2", "key": "CN=서하늘/OU=HN2/O=NURI",
           "empno": "200003", "dept_name": "기술연구소", "dept_code": "n520_00"}
RETIRED = {**COLLEAGUE, "email": "old.kim@nuri.example", "user_name": "김지난", "user_id": "oldkim", "key": "CN=김지난/OU=OK/O=NURI",
           "empno": "199001", "is_retire": "Y"}
DIRECTORY = (OWNER, COLLEAGUE, HOMONYM, RETIRED)
# 조직도 — 회사 값 아래 맨 위 부서 둘, 소재사업부 아래 그룹 둘. 칸 이름은 실측 답의 꼴이다(inbox.py 머리말 조직도 줄)
ORG_DEPTS = (  # (코드, 이름, 깊이, 위 부서 코드 — 회사 값이면 맨 위)
    ("a100_00(07)", "임원", 1, COMPANY), ("n300_00(07)", "소재사업부", 1, COMPANY),
    ("n310_00(07)", "소재기획그룹", 2, "n300_00(07)"), ("n320_00(07)", "소재시험그룹", 2, "n300_00(07)"))
TRAINEE = {**COLLEAGUE, "email": "jw.lee@nuri.example", "user_name": "이지우", "user_id": "jwlee", "key": "CN=이지우/OU=JW/O=NURI",
           "empno": "200009", "grade": "사원", "job_title": "일반"}
ORG_MEMBERS = {"a100_00(07)": (OWNER,), "n300_00(07)": (OWNER,), "n310_00(07)": (COLLEAGUE, TRAINEE),
               "n320_00(07)": (HOMONYM,)}
GROUPS = {"[07:직책]리더(07)": "리더", "[07:직책]일반(07)": "일반"}
EXTERNAL = "alex.berg@far-cells.example"
FOLDER_TOP, FOLDER_CHILD, FOLDER_COMMA, FOLDER_EMPTY = "협력사", "프로젝트\\소재 시험", "소식\\공지, 안내", "회의.2026"
# SSO 주소를 적은 사내 안내 본문 — 끊긴 세션의 화면이 아니다
NOTICE = '<p>비밀번호 변경: <a href="http://swpsso.posco.net/idms/U61/jsp/pw.jsp">swpsso.posco.net</a></p>'
ECM_KEY = "1a2b3c4d5e6f7081"
# 본문 링크의 OBJECTID 는 머리의 열쇠와 다를 수 있다(잰 29 통 가운데 6) — 링크 쪽 값을 열쇠로 집으면 문다
ECM_LINK_OBJECT = "99aa88bb77cc66dd"


def ecm_note(key: str | None) -> bytes:
    """ECM 첨부 쪽지 — 잰 꼴(맨 앞 ``<!--@!ECM!@ … -->`` 머리 · 그 뒤 swp_interface.jsp 로 넘기는 본문). 열쇠가 None 이면
    머리 없는 쪽지다."""
    def hexed(s: str) -> str:
        return s.encode().hex()
    head = ("<!--@!ECM!@<empId>02|usr0123456789abcdef</empId><lineType>01</lineType>"
            f"<objectId>doc{key}</objectId><totalFileSize>382</totalFileSize><fileName>분기 실적.pptx</fileName>"
            "<fileSize>382</fileSize><fileType>pptx</fileType>"
            f"<servletUrl>http://swpecm.posco.net:7091/ECM/servlet/EcmSendFileServlet?DOCID=doc{key}</servletUrl>"
            "<secretLevelCode>2A</secretLevelCode><sendTime>20261103060000</sendTime>-->\n") if key else ""
    body = ("<html><body><script>location.href='http://swpecm.posco.net:7091/ECM/swp_interface.jsp?ACTID=viewlink"
            f"&OBJECTID={hexed(ECM_LINK_OBJECT)}&DOCID={hexed('doc' + (key or '0' * 16))}&SYSID={hexed('pcfma')}';"
            "</script></body></html>")
    return (head + body).encode()


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
                 files={"메모-표.csv": "이름,값\n가,1\n".encode() + bytes([0, 255, 13, 10]),
                        "분기 실적(pptx_2048KB).html": ecm_note(ECM_KEY)}),
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
        FakeMail(U["draft"], "[초안] 시험 일정 회신", "20261103100000", internal_sender(OWNER["user_name"], OWNER["email"],
                 OWNER["user_name_eng"]), "T", unread=False, folder="(Drafts)", draft=True, to_102=None,
                 html="<p>초안 본문 — 시험 일정</p>"),
    ]
    sent = [FakeSent(U["sent_1"], "회신: 주간 생산 보고", "20261103083000",
                     "CN=서하늘/OU=HN/O=NURI, 송재민 <jm.song@nuri.example>"),
            FakeSent(U["sent_2"], "견적 요청", "20261102150000", EXTERNAL, in_view=False)]
    return mails, sent


# ── 가짜 메일함 ───────────────────────────────────────────────────────────

class FakeDomino:
    """127.0.0.1 의 Domino 웹메일 흉내. ``paths`` 는 받은 요청, ``changes`` 는 메일함을 바꾼 요청."""

    def __init__(self, *, session: str = "ok", folders=(), all_view: bool = True, recipient_view: bool = True,
                 draft_view: bool = True):
        mails, sent = scenario()
        self.mails = {m.unid: m for m in mails}
        self.sent = sent
        self.session = session            # ok · login(200 HTML) · redirect(302 SSO)
        self.extra_folders = tuple(folders)   # 메일이 없어도 보기 목록에 서는 폴더
        self.all_view = all_view
        self.recipient_view = recipient_view
        self.draft_view = draft_view
        self.tree: dict[str, tuple[str, str]] = {}   # 폴더 열쇠 → (경로, 부모 열쇠) — 흉내 메일함이 지은 폴더
        self.archive_twins: set[str] = set()          # 메일 쪽은 지웠는데 이전메일함 짝이 남은 폴더 열쇠(실측)
        self.rules: dict[str, dict] = {}              # 규칙 unid → 저장 폼의 칸
        self.posts: list[tuple[str, dict]] = []
        self.twin: dict[str, tuple[str, str]] = {}
        self.stuck: set[str] = set()                 # 옮기기에 OK 를 내고 안 옮기는 메일
        for i, p in enumerate(sorted({*self.extra_folders, *(m.folder for m in self.mails.values() if m.folder)})):
            if not p.startswith("("):
                self.tree[f"newNode{1000 + i}"] = (p, "")
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

            def do_POST(self):
                size = int(self.headers.get("Content-Length") or 0)
                form = {k: v[0] for k, v in urllib.parse.parse_qs(self.rfile.read(size).decode(), keep_blank_values=True).items()}
                with box.lock:
                    box.paths.append(self.path)
                    box.posts.append((self.path, form))
                    box.answer_post(self, form)

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
        return sorted({*SYSTEM_FOLDERS, *(p for p, _ in self.tree.values()), *(m.folder for m in self.mails.values() if m.folder)})

    def node_of(self, path: str) -> str | None:
        return next((n for n, (p, _) in self.tree.items() if p == path), None)

    def answer(self, h) -> None:
        raw = urllib.parse.unquote(h.path)
        low = raw.lower()
        if self.session == "redirect":
            return self.send(h, 302, b"", "text/html", location="http://swpsso.example/login.jsp")
        if f"{COOKIE[0]}={COOKIE[1]}" not in (h.headers.get("Cookie") or "") or self.session == "login":
            return self.send(h, 200, LOGIN_PAGE.encode(), "text/html")
        if low == "/common/lib_f.nsf/checksessionstatus?openpage":
            return self.send(h, 200, b'{"status":"login"}', "text/html")
        if raw == "/":
            # 메일 서버 첫 화면 — 세션 주인의 메일 파일 경로를 들고 받은편지함으로 넘긴다(실측)
            page = (f'<html><body><script>var mailserver = "127.0.0.1"; var mailfile = "{DB.lstrip("/")}";'
                    'location.replace("http://" + mailserver + "/" + mailfile + "/FrameNew?openform");</script></body></html>')
            return self.send(h, 200, page.encode(), "text/html; charset=UTF-8")
        if low.startswith("/common/profile.nsf/ag_tree_dept_json?openagent"):
            query = urllib.parse.parse_qs(raw.split("&", 1)[1], keep_blank_values=True)
            under = query.get("dept", [""])[0]
            rows = [{"type": "dept", "key": c, "dept_name": n, "dept_name_eng": n, "dept_code": c, "depth": str(d),
                     "has_child": "Y" if any(p == c for *_, p in ORG_DEPTS) else "",
                     "email": f"dept_{c}@nuri.example"} for c, n, d, p in ORG_DEPTS if p == under]
            return self.send(h, 200, json.dumps({"result": rows}, ensure_ascii=False).encode(), "text/html")
        if low.startswith("/common/profile.nsf/ag_tree_user_json?openagent"):
            query = urllib.parse.parse_qs(raw.split("&", 1)[1], keep_blank_values=True)
            people = [{k: v for k, v in u.items() if k not in ("dept_code", "is_retire")} | {"type": "user"}
                      for u in ORG_MEMBERS.get(query.get("dept", [""])[0], ())]
            rows = people or [{"type": "nothing"}]
            return self.send(h, 200, json.dumps({"result": rows}, ensure_ascii=False).encode(), "text/html")
        if low.startswith("/common/lib_f.nsf/aggetdistribute?openagent"):
            name = urllib.parse.parse_qs(raw.split("&", 1)[1]).get("groupname", [""])[0]
            title = GROUPS.get(name)
            members = [{"type": "user", "fullname": u["key"], "name": u["user_name"], "grade": u["grade"],
                        "deptname": u["dept_name"], "email": u["email"]}
                       for u in DIRECTORY if title and u.get("job_title") == title]
            return self.send(h, 200, json.dumps({"result": "ok" if title else "fail", "memberlist": members},
                                                ensure_ascii=False).encode(), "application/json")
        if low.startswith("/common/profile.nsf/ag_org_search_json?openagent"):
            query = urllib.parse.parse_qs(raw.split("&", 1)[1] if "&" in raw else "", keep_blank_values=True)
            if query.get("type") == ["group"]:
                rows = [{"type": "group", "key": k, "group_name": n} for k, n in GROUPS.items()]
                return self.send(h, 200, json.dumps({"group": rows}, ensure_ascii=False).encode(), "text/html")
            key = query.get("search_key", [""])[0].casefold()
            # 이름 · 메일 · 사번으로 찾는다 — 부서 이름으로는 사람이 안 온다(실측)
            users = [p for p in DIRECTORY if key and key in (p["email"], p["user_name"], p["empno"])]
            return self.send(h, 200, json.dumps({"dept": [], "user": users, "total": len(users)},
                                                ensure_ascii=False).encode(), "text/html; charset=UTF-8")
        if not raw.startswith(DB):
            return self.send(h, 404, b"<html>not found</html>", "text/html")
        rest = raw[len(DB):]
        low = rest.lower()
        if low.startswith("/fdd_folder_fullpath?readviewentries"):
            return self.send(h, 200, self.tree_json(), "application/json; charset=UTF-8")
        if low.startswith("/agt_mail_folder_save?openagent"):
            return self.folder_save(h, urllib.parse.parse_qs(raw.split("?", 1)[1], keep_blank_values=True))
        if low.startswith("/trashdoc?openagent"):
            q = urllib.parse.parse_qs(raw.split("?", 1)[1], keep_blank_values=True)
            mail = self.mails.get(q.get("docid", [""])[0])
            if q.get("type") != ["recovery"] or mail is None or mail.folder != "($Trash)":
                return self.send(h, 200, b'{ "result":false }', "text/html")
            mail.folder = ""
            self.changes.append(("restore", mail.unid))
            return self.send(h, 200, b'{ "result":true } ', "text/html")
        parts = rest.split("/")
        if len(parts) == 3 and parts[1] == "0" and parts[2].split("?")[0].upper() in self.rules \
                and parts[2].lower().endswith("?editdocument"):
            return self.send(h, 200, self.rule_page(parts[2].split("?")[0].upper()).encode(), "text/html; charset=UTF-8")
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
            if self.draft_view:
                views.append({"@title": DRAFT_VIEW, "@unid": DRAFT_VIEW_UNID, "@folder": False})
            return self.send(h, 200, json.dumps(views, ensure_ascii=False).encode(), "application/json; charset=UTF-8")
        if "?readviewentries" in low:
            return self.send(h, 200, self.view(rest), "text/xml; charset=UTF-8")
        if low.startswith(SEARCH_AGENT):
            return self.search(h, rest)
        parts = rest.split("/")
        if len(parts) >= 4 and parts[1] == "0" and parts[2] in self.mails:
            mail, tail = self.mails[parts[2]], "/".join(parts[3:])
            if tail == "Body?OpenField":
                if mail.unserved:
                    return self.send(h, 501, b"<html>not implemented</html>", "text/html")
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

    def tree_json(self) -> bytes:
        """폴더 나무 보기(JSON · 실측 꼴) — 경로 · 열쇠 · 수 · 부모 · 이름. 맨 위 폴더의 부모는 ``nodeATag2`` 다."""
        rows = []
        # 짝 줄을 산 폴더보다 앞에 낸다 — 실물의 차례는 안 쟀고, 앞의 줄을 집는 손을 가려낸다
        for node, (path, parent) in [(n, self.twin[n]) for n in sorted(self.archive_twins)] + sorted(self.tree.items()):
            cell = lambda v: {"text": {"0": v}}
            rows.append({"@unid": hashlib.md5(node.encode()).hexdigest().upper(), "entrydata": [
                {"@columnnumber": "0", "@name": "$6", **cell(path)}, {"@columnnumber": "1", "@name": "NodeUnid", **cell(node)},
                {"@columnnumber": "2", "@name": "cnt", **cell(str(path.count(chr(92)) + 2))},
                {"@columnnumber": "3", "@name": "ParentID", **cell(parent or "nodeATag2")},
                {"@columnnumber": "4", "@name": "nodeText", **cell(path.rsplit(chr(92), 1)[-1])}]})
        return json.dumps({"@toplevelentries": str(len(rows)), "viewentry": rows}, ensure_ascii=False).encode()

    def folder_save(self, h, q: dict) -> None:
        """폴더 만들기 · 지우기의 흉내 — 실물처럼 늘 ``OK`` 를 낸다. 메일이 든 채 지우면 그 메일은 휴지통으로, 메일 쪽을 지워도
        이전메일함 짝이 남아 나무에 서다가 ``nodefrom=archive`` 로 한 번 더 지워야 사라진다(실측)."""
        one = lambda k: q.get(k, [""])[0]
        act, node = one("act"), one("nodeid")
        if act == "create" and node and node not in self.tree:
            parent = "" if one("pfcode") == "nofolder" else one("pfcode")
            up = self.tree.get(parent, ("", ""))[0] if parent else ""
            self.tree[node] = (f"{up}{chr(92)}{one('fname')}" if parent else one("fname"), parent)
            self.changes.append(("folder+", node))
        elif act == "delete_action" and one("nodefrom") == "mail" and node in self.tree:
            path = self.tree.pop(node)[0]
            self.twin[node] = (path, "")
            self.archive_twins.add(node)
            for m in self.mails.values():
                if m.folder == path:
                    m.folder = "($Trash)"
                    self.changes.append(("trash", m.unid))
            self.changes.append(("folder-", node))
        elif act == "delete_action" and one("nodefrom") == "archive":
            self.archive_twins.discard(node)
        return self.send(h, 200, b"OK\n", "text/html")

    def answer_post(self, h, form: dict) -> None:
        raw = urllib.parse.unquote(h.path)
        if f"{COOKIE[0]}={COOKIE[1]}" not in (h.headers.get("Cookie") or "") or self.session == "login":
            return self.send(h, 200, LOGIN_PAGE.encode(), "text/html")
        rest = raw[len(DB):] if raw.startswith(DB) else ""
        if rest == "/folder2?OpenForm" and form.get("Action") == "mailmove_action":
            # 실물처럼 못 옮겨도 OK 를 낸다 — 모르는 폴더 열쇠면 아무것도 안 옮긴다(실측). ``stuck`` 의 메일은 OK 를 내고 안 옮긴다
            target = form.get("nodeUNID", "")
            place = "" if target == "inbox" else self.tree.get(target, (None, ""))[0]
            for unid in filter(None, form.get("UNIDs", "").split(",")):
                if place is not None and unid in self.mails and unid not in self.stuck:
                    self.mails[unid].folder = place
                    self.changes.append(("move", unid))
            return self.send(h, 200, b"OK", "text/html")
        if rest.startswith("/Mailrule?OpenForm&Seq=1") or (rest.lower().endswith("?editdocument&seq=1")
                                                           and rest.split("/")[2].split("?")[0].upper() in self.rules):
            return self.rule_post(h, rest, form)
        return self.send(h, 404, b"<html>not found</html>", "text/html")

    def rule_post(self, h, rest: str, form: dict) -> None:
        if form.get("SubmitAction") == "delete":
            gone = self.rules.pop(form.get("ProcessUNID", "").upper(), None)
            self.changes.append(("rule-", form.get("ProcessUNID", "")))
            return self.send(h, 200, json.dumps({"result": gone is not None, "unid": "F" * 32}).encode(), "text/html")
        if form.get("SubmitAction") != "save":
            return self.send(h, 200, b'{"result":false}', "text/html")
        editing = rest.split("/")[2].split("?")[0].upper() if rest.startswith("/0/") else ""
        unid = editing or hashlib.md5(f"rule/{len(self.rules)}/{time.time_ns()}".encode()).hexdigest().upper()
        self.rules[unid] = dict(form)
        self.changes.append(("rule", unid))
        return self.send(h, 200, json.dumps({"result": True, "unid": unid, "saveoptions": "1"}).encode(), "text/html")

    def rule_page(self, unid: str) -> str:
        """규칙 편집 화면의 흉내 — 머리의 ``new FormJS({…})`` 와 입력 칸(실측 꼴 · 라디오는 checked 로 고른 것)."""
        f = self.rules[unid]
        folders = [f"{p}|{n}^" for n, (p, _) in sorted(self.tree.items())]
        info = {"dbPath": DB.lstrip("/"), "isEdit": True, "unid": unid, "folders": folders,
                "form": {"rules": f.get("rules", ""), "folder_id": f.get("folder_id", ""), "folder_name": f.get("folder_name", "")}}
        def radio(name, value):
            on = " checked" if f.get(name, "0") == value else ""
            return f'<input type="radio" name="{name}" value="{value}"{on}>'
        fields = "".join(f'<input name="{k}" value="{escape(f.get(k, ""), {chr(34): "&quot;"})}" Type="Text">'
                         for k in ("forward_list", "AllFwdOpt", "MydeptFwdOpt", "rule_from", "rule_to", "rule_cc",
                                   "rule_subject", "rule_attach"))
        radios = "".join(radio(n, v) for n, vs in (("expRule", ("inbox", "sent")), ("rule_fromType2", ("1", "0")),
                                                     ("rule_toType2", ("1", "0"))) for v in vs)
        return (f"<html><script>var _form = new FormJS({json.dumps(info, ensure_ascii=False)});</script>"
                f"<form>{fields}{radios}</form></html>")

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
        elif key == "xml_rule":
            rows = [(u, {"$92": "받은메일-ENG-inbox", "$88": f.get("rule_subject", ""), "$80": "", "xallfwdopt": "N"})
                    for u, f in sorted(self.rules.items())]
        elif self.draft_view and key == DRAFT_VIEW_UNID.lower():
            got = sorted((m for m in self.mails.values() if m.draft), key=lambda m: m.stamp, reverse=True)
            rows = [(m.unid, m.cols(INBOX_COLUMNS)) for m in got]
        elif self.all_view and key == ALL_VIEW_UNID.lower():
            got = [m for m in self.mails.values() if not m.draft and (m.folder is None or not m.folder.startswith("("))]
            # 정렬 없이는 날짜 내림차순 · ResortDescending=1 이면 내림차순 두 덩이(실측 — 가르는 규칙은 머리말)
            got.sort(key=lambda m: (m.stamp, m.unid), reverse=True)
            if descending:
                got = got[1::2] + got[0::2]
            rows = [(m.unid, m.cols(ALL_COLUMNS)) for m in got]
        else:
            # 폴더 보기는 unid 로만 열린다 — 제목으로 열면 0줄(실측). 모르는 보기도 빈 목록이다
            folder = next((p for p in self.folder_paths() if folder_unid(p).lower() == key), None)
            got = sorted((m for m in self.mails.values() if folder is not None and m.folder == folder),
                         key=lambda m: m.stamp, reverse=True)
            rows = [(m.unid, {**m.cols(FOLDER_COLUMNS), "xname": folder_sender(m.sender),
                              "read": folder_read(m.unid, m.unread, i + 1)}) for i, m in enumerate(got)]
            count = min(count, FOLDER_PAGE_MAX)
        page = rows[start - 1:start - 1 + count]
        body = "".join(
            f'<viewentry position="{start + i}" unid="{unid}" noteid="{start + i:x}" siblings="{len(rows)}">'
            + "".join(f'<entrydata columnnumber="{j}" name="{escape(k)}"><text>{escape(v)}</text></entrydata>'
                      for j, (k, v) in enumerate(cols.items()))
            + "</viewentry>" for i, (unid, cols) in enumerate(page))
        return (f'<?xml version="1.0" encoding="UTF-8"?><viewentries timestamp="20261103T000000,00Z" '
                f'toplevelentries="{len(rows)}">{body}</viewentries>').encode()

    def search(self, h, rest: str) -> None:
        """웹메일 검색 손의 흉내(실측 꼴) — ``stype=chatbot`` 에 칸이 하나라도 있어야 답하고(아니면 0 바이트), 칸을 여럿 주면 다
        든 메일만 낸다. 범위 ``all`` 은 임시보관함을 안 든다. JSON 은 실물처럼 줄마다 끊어 쓴다."""
        q = urllib.parse.parse_qs(rest.split("?", 1)[1], keep_blank_values=True)
        one = lambda k: q.get(k, [""])[0]
        wanted = {slot: one(slot) for slot in SEARCH_SLOTS if one(slot)}
        if one("stype") != "chatbot" or not wanted:
            return self.send(h, 200, b"", "text/html")
        scope = one("mbox")
        def held(m: FakeMail, slot: str, word: str) -> bool:
            value = getattr(m, SEARCH_SLOTS[slot])
            return word in ("{}".join(value) if isinstance(value, tuple) else (value or ""))
        def in_scope(m: FakeMail) -> bool:
            if scope == "draft":
                return m.draft
            if m.draft or (m.folder or "").startswith("($Trash"):
                return scope == "trash" and not m.draft
            if scope == "inbox":
                return m.folder == ""
            if scope == "sent":
                return False
            if scope == "unread":
                return m.unread
            return scope == "all"
        got = sorted((m for m in self.mails.values() if in_scope(m) and all(held(m, k, w) for k, w in wanted.items())),
                     key=lambda m: m.stamp, reverse=True)
        if scope in ("all", "sent"):    # 보낸 메일 — 실물의 category 는 시스템 표지 [${SENT}]
            got += [FakeMail(x.unid, x.subject, x.stamp, x.to, unread=False, folder="(Sent)") for x in self.sent
                    if x.in_view and all(w in x.subject for k, w in wanted.items() if k == "ssbj") and set(wanted) == {"ssbj"}]
            got.sort(key=lambda m: m.stamp, reverse=True)
        count, page = int(one("count") or 30), int(one("page") or 1)
        rows = got[(page - 1) * count:page * count]
        def row(m: FakeMail) -> str:
            # 실물 꼴 — 받은편지함 [${INBOX}] · 보낸편지함 [${SENT}] · 임시보관함 · 휴지통은 빈 칸 · 하위 폴더는 끝 이름만
            folder = ("" if m.draft or (m.folder or "").startswith("($Trash") else "[${SENT}]" if m.folder == "(Sent)"
                      else f"[{m.folder.rsplit(chr(92), 1)[-1]}]" if m.folder else "[${INBOX}]")
            who = m.sender.split("-=spl=-")[0] if "-=spl=-" in m.sender else m.sender
            return json.dumps({"unid": m.unid, "noteid": "1", "form": "Memo",
                               "icon": "ico-nomail" if m.unread else "ico-okmail", "category": folder,
                               "isdraft": "N", "attach": "T" if m.attachments else "N", "from": f"{who}-ENG-x",
                               "subject": m.subject, "date": m.stamp[:8] + "T" + m.stamp[8:] + ",00Z"},
                              ensure_ascii=False)
        body = f'{{"total":{len(got)}\n, "page":{page}\n, "data":[\n' + "\n,".join(row(m) for m in rows) + "\n]}"
        return self.send(h, 200, body.encode(), "text/json; charset=UTF-8")

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


def check_folder_hands_make_move_and_delete_only_what_was_asked():
    """폴더 만들기 · 옮기기 · 지우기 — 그 폴더 · 그 메일만 바뀌고 읽음은 그대로다. 서버의 ``OK`` 는 증거가 아니어서(실측 —
    못 옮겨도 OK) 손이 다시 봐야 하고, 메일이 든 채 지우면 메일이 휴지통으로 가므로(실측) 든 폴더 · 하위가 있는 폴더는 안 지운다.
    지우기는 이전메일함 짝까지 두 번이어야 나무에서도 사라진다(실측)."""
    unid = U["alone"]
    with stage() as (box, mailbox):
        before = box.unread()
        top = mailbox.create_folder("검토")
        sub = mailbox.create_folder("이번 주", parent="검토")
        assert (top.path, sub.path, sub.parent) == ("검토", "검토\\이번 주", top.node), (top, sub)
        assert "검토\\이번 주" in [f.path for f in mailbox.folders()]
        for bad in ("검토", "a_b", "Inbox", "($Trash)", ""):
            raises(inbox.MailboxConfigError, lambda b=bad: mailbox.create_folder(b))
        mailbox.move_mails([unid], "검토\\이번 주")
        assert box.mails[unid].folder == "검토\\이번 주" and box.unread() == before, "옮기기가 그 메일만 옮기지 않았거나 읽음을 바꿨다"
        raises(inbox.MailboxConfigError, lambda: mailbox.delete_folder("검토\\이번 주"))
        raises(inbox.MailboxConfigError, lambda: mailbox.delete_folder("검토"))
        assert not [c for c in box.changes if c[0] in ("trash", "folder-")], f"든 폴더를 지웠다: {box.changes}"
        mailbox.move_mails([unid], "")
        assert box.mails[unid].folder == "" and box.unread() == before
        mailbox.delete_folder("검토\\이번 주")
        mailbox.delete_folder("검토")
        assert not any(n.path.startswith("검토") for n in mailbox.folder_tree()), "이전메일함 짝이 나무에 남았다"
        raises(inbox.MailboxConfigError, lambda: mailbox.move_mails([unid], "없는 폴더"))
        assert not changing(box.paths), f"폴더 손이 여는 주소를 불렀다: {changing(box.paths)}"


def check_move_that_did_not_land_is_an_error_not_ok():
    """서버가 OK 를 내도 메일이 그 자리에 없으면 손이 말한다 — 안 그러면 사람은 옮겼다고 믿는다. 거꾸로, 새것 창 밖의 옛 메일을
    옮겼을 때 「없다」고 하면 안 된다 — 받은편지함이 1000 줄을 넘어도 끝까지 본다."""
    with stage(folders=(FOLDER_EMPTY,)) as (box, mailbox):
        box.stuck.add(U["alone"])
        raises(inbox.MailboxError, lambda: mailbox.move_mails([U["alone"]], FOLDER_EMPTY))
        assert box.mails[U["alone"]].folder == ""
    with stage() as (box, mailbox):
        old = box.mails[U["f_top"]]
        for i in range(1200):   # 옮길 옛 메일보다 새 메일 1200 통 — 새것 창 하나로는 안 보인다
            u = f"{0xB0000000 + i:032X}"
            box.mails[u] = FakeMail(u, f"새 메일 {i}", f"2026111{i % 10}0{i % 60:02d}000"[:14], PEER[1])
        mailbox.move_mails([old.unid], "")
        assert old.folder == "", "옛 메일을 받은편지함으로 못 옮겼다"


def check_folder_with_twin_row_or_rule_is_not_guessed():
    """나무에 같은 경로가 둘(지운 폴더의 짝)이면 고르지 않고, 규칙이 메일을 옮기는 폴더는 안 지운다 — 짝을 고르면 서버가 OK 를
    내고 아무것도 안 하고, 가리키던 폴더가 없어진 규칙이 새 메일을 어떻게 하나는 안 쟀다."""
    with stage(folders=(FOLDER_EMPTY,)) as (box, mailbox):
        box.twin["newNode1"] = (FOLDER_EMPTY, "")
        box.archive_twins.add("newNode1")   # 나무에서 산 폴더보다 먼저 선다
        raises(inbox.MailboxError, lambda: mailbox.move_mails([U["alone"]], FOLDER_EMPTY))
        assert box.mails[U["alone"]].folder == "" and not box.posts, "짝 줄을 골라 옮기기를 보냈다"
    with stage(folders=(FOLDER_EMPTY,)) as (box, mailbox):
        mailbox.save_rule(inbox.Rule(unid="", box="inbox", action="move_folder", folder=FOLDER_EMPTY,
                                     conditions={"subject": "[주간]"}))
        raises(inbox.MailboxConfigError, lambda: mailbox.delete_folder(FOLDER_EMPTY))
        assert FOLDER_EMPTY in [f.path for f in mailbox.folders()]


def check_trash_restore_brings_one_mail_back():
    with stage() as (box, mailbox):
        mailbox.restore_from_trash(U["f_trash"])
        assert box.mails[U["f_trash"]].folder == "" and box.changes == [("restore", U["f_trash"])], box.changes
        raises(inbox.MailboxError, lambda: mailbox.restore_from_trash(U["alone"]))   # 휴지통에 없는 메일 — 답이 거짓


def check_rule_hands_round_trip_and_never_forward():
    """규칙 넣기 · 읽기 · 고치기 · 지우기 — 자동전달 칸은 늘 비고 꺼져 나간다(남에게 메일이 나가는 길). 조건 없는 규칙(모든
    메일에 걸린다) · 없는 폴더 · 자동전달 규칙 고치기는 묻기 전에 막는다. 규칙 문서를 여는 주소는 메일 읽음을 안 바꾼다."""
    with stage(folders=(FOLDER_EMPTY,)) as (box, mailbox):
        before = box.unread()
        made = inbox.Rule(unid="", box="inbox", action="move_folder", folder=FOLDER_EMPTY,
                          conditions={"from": "hn.seo@nuri.example"}, exact_from=True)
        unid = mailbox.save_rule(made)
        got = mailbox.rule(unid)
        assert (got.box, got.action, got.folder, got.conditions, got.exact_from, got.forwards) == (
            "inbox", "move_folder", FOLDER_EMPTY, {"from": "hn.seo@nuri.example"}, True, False), got
        assert mailbox.rules() == [got]
        import dataclasses   # noqa: PLC0415
        assert mailbox.save_rule(dataclasses.replace(got, conditions={"subject": "[주간]"}, exact_from=False)) == unid
        assert mailbox.rule(unid).conditions == {"subject": "[주간]"} and len(box.rules) == 1
        for _, form in box.posts:
            if form.get("SubmitAction") == "save":
                assert (form["forward_list"], form["AllFwdOpt"], form["MydeptFwdOpt"]) == ("", "0", "0"), form
                assert not any(form[f"rule_{k}_1"] for k in inbox.RULE_FIELDS), "자동전달 탭의 조건 칸이 찼다"
        for bad in (dict(conditions={}), dict(conditions={"body": "x"}), dict(folder="없는 폴더"), dict(box="all")):
            raises(inbox.MailboxConfigError, lambda b=bad: mailbox.save_rule(dataclasses.replace(made, **b)))
        box.rules[unid]["forward_list"] = "ext@far-cells.example"
        raises(inbox.MailboxConfigError, lambda: mailbox.save_rule(dataclasses.replace(got, conditions={"subject": "x"})))
        mailbox.delete_rule(unid)
        assert not box.rules and box.unread() == before
        raises(inbox.MailboxConfigError, lambda: mailbox.rule(U["alone"]))   # 메일 문서를 규칙으로 안 연다
        assert not [c for c in box.changes if c[0] == "read"], f"규칙 손이 메일 읽음을 바꿨다: {box.changes}"


def check_rule_page_of_unknown_shape_is_an_error_not_an_empty_rule():
    """규칙 화면의 머리를 못 읽거나 갈래가 모르는 값이면 빈 규칙으로 읽지 않는다 — 빈 규칙은 자동전달 규칙을 조용히 숨긴다."""
    good = '<script>new FormJS({"form": {"rules": "forward", "folder_id": ""}, "folders": []});</script>'
    assert inbox.parse_rule_page("A" * 32, good).forwards, "자동전달 갈래를 자동전달로 안 읽었다"
    for page in ("<html></html>", good.replace('"forward"', '"copy_all"'), good.replace("});", "};")):
        raises(inbox.MailboxError, lambda p=page: inbox.parse_rule_page("A" * 32, p))


def check_reading_path_refuses_folder_and_rule_changers():
    """읽기 길(``_get``)은 폴더 · 휴지통 · 규칙을 바꾸는 주소를 서버에 닿기 전에 막는다 — 만들기 · 지우기 · 되살리기가 GET 이다(실측)."""
    with stage() as (box, mailbox):
        for path in ("/agt_mail_folder_save?OpenAgent&act=create&fname=x", "/folder2?OpenForm",
                     f"/TrashDoc?OpenAgent&docid={U['alone']}&type=recovery", "/Mailrule?OpenForm&Seq=1"):
            raises(inbox.ChangeRefused, lambda p=path: mailbox._get(p))
        raises(inbox.ChangeRefused, lambda: mailbox._send_folder(f"{DB}/0/{U['alone']}?OpenDocument", "x"))
        raises(inbox.ChangeRefused, lambda: mailbox._send_rule(f"{DB}/Mailrule?OpenForm&Seq=1", {"forward_list": "a@b"}, "x"))
        assert not box.paths, f"막아야 할 주소가 서버에 닿았다: {box.paths}"


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
    메일이 조용히 빠진다. 폴더 줄은 받는 꼴 · 중요도가 빈다(그 보기에 열이 없다). 안 읽음은 읽음 열 HTML 조각의 class 로 선다 —
    받은편지함의 낱말로 읽으면 폴더의 안 읽은 메일이 다 읽음이 된다."""
    with stage(folders=(FOLDER_EMPTY,)) as (box, mailbox):
        box.mails[U["f_child"]].unread = False
        folders = mailbox.folders()
        # 시스템 폴더((…))는 빠지고, 마디마다 가나다 차례
        assert [f.path for f in folders] == [FOLDER_COMMA, FOLDER_CHILD, FOLDER_TOP, FOLDER_EMPTY], [f.path for f in folders]
        for f in folders:
            got = mailbox.list_folder(f, count=50)
            mine = sorted((m for m in box.mails.values() if m.folder == f.path), key=lambda m: m.stamp, reverse=True)
            assert [e.unid for e in got] == [m.unid for m in mine], f"폴더 보기의 줄이 그 폴더의 메일이 아니다: {f.path}"
            assert all(e.folder == f.path and e.role == "" and e.importance == "" for e in got), got
            assert [e.unread for e in got] == [m.unread for m in mine], f"폴더 줄의 안 읽음이 메일함과 다르다: {f.path}"
        raises(inbox.MailboxConfigError, lambda: mailbox.list_folder(inbox.Folder(unid=FOLDER_CHILD, path=FOLDER_CHILD)))


def check_all_mail_view_gives_marks_and_sender_newest_first():
    """모든편지함은 정렬 없이 받는다 — 그 꼴이 이미 날짜 내림차순이고, ``ResortDescending=1`` 은 내림차순 두 덩이를 내 창에서
    끊으면 뒤 덩이의 새 메일을 놓친다. 폴더 줄에 없는 받는 꼴 · 중요도와, 폴더 줄이 못 드는 보낸 분 주소 · 읽음 열(회신함 ·
    전달함)을 unid 로 준다."""
    with stage() as (box, mailbox):
        box.mails[U["f_child"]].unread, box.mails[U["f_child"]].mark = False, "ico-post"
        marks = mailbox.list_all(count=200)
        asked = box.paths[-1]
        assert "ReadViewEntries" in asked and "ResortDescending" not in asked, f"모든편지함을 정렬해 받았다: {asked}"
        by = {m.unid: m for m in marks}
        assert (by[U["f_top"]].role, by[U["f_top"]].importance) == ("T", "1"), by[U["f_top"]]
        assert (by[U["f_comma"]].role, by[U["f_child"]].role, by[U["f_child"]].importance) == ("G", "C", "2")
        assert by[U["f_top"]].sender.addr == "sm.ha@haneul-parts.example", by[U["f_top"]].sender
        assert by[U["f_child"]].sender == inbox.Sender(*PEER), by[U["f_child"]].sender
        assert (by[U["f_child"]].read_mark, by[U["f_top"]].read_mark) == ("ico-post", "ico-nomail"), \
            (by[U["f_child"]].read_mark, by[U["f_top"]].read_mark)
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
        box.mails[U["f_top"]].unserved = True
        assert mailbox.body(U["f_top"]) is None, "본문 주소가 501 인 메일에 None 이 아니다 — 메일함을 훑는 회차가 통째로 진다"
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
        raises(inbox.MailboxConfigError, lambda: mailbox.ecm_key(e, memo))
        assert len(box.paths) == asked, "ECM 첨부의 바이트를 내러 · ECM 아닌 첨부의 열쇠를 꺼내러 서버에 갔다"
        assert mailbox.ecm_key(e, ecm) == ECM_KEY, "ECM 첨부의 열쇠가 머리 objectId 가 아니다"
        assert mailbox.ecm_key(U["ecm"], ecm.listed) == ECM_KEY, "목록의 이름 그대로 꺼내는 길이 다르다"
        box.mails[U["ecm"]].files[ecm.listed] = ecm_note(None)
        missing = raises(inbox.MailboxError, lambda: mailbox.ecm_key(e, ecm))
        assert type(missing) is inbox.MailboxError, f"머리 없는 쪽지를 {type(missing).__name__} 로 읽었다"
    with stage(session="login") as (_, mailbox):
        raises(inbox.SessionExpired, lambda: mailbox.ecm_key(U["ecm"], "분기 실적(pptx_2048KB).html"))


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
        assert (me[0].empno, me[0].dept_code, me[0].grade_code, me[0].is_boss) == ("200001", "n310_00", "P40", True), me
        peer = mailbox.find_people(PEER[1], COMPANY)
        assert len(peer) == 1 and (peer[0].dept_code, peer[0].grade_code, peer[0].is_boss) == ("n310_10", "P30", False), \
            peer
        assert mailbox.find_people(EXTERNAL, COMPANY) == [], "밖의 주소가 주소록에 걸렸다"
        asked = [urllib.parse.unquote(p) for p in box.paths if "ag_org_search_json" in p]
        assert asked and all(f"company={COMPANY}" in p for p in asked), asked
        assert mailbox.session_alive() is True
    with stage(session="login") as (_, mailbox):
        assert mailbox.session_alive() is False, "끊긴 세션에 세션 확인이 참이다"
    # 새 칸 셋은 기본값이 있다 — 칸 셋 없이 한 사람을 짓던 쪽이 그대로 선다
    bare = inbox.DirectoryPerson(email="", name="", name_eng="", notes="", user_id="", empno="", dept="", grade="",
                                 job_title="", company="", retired=False)
    assert (bare.dept_code, bare.grade_code, bare.is_boss, bare.job_title_code) == ("", "", False, ""), bare


def check_exact_lookup_picks_only_that_person():
    """이름 찾기의 답에는 동명이인이 섞인다 — 주소 · Notes 이름 · ID 로는 그 한 사람만, 이름으로는 같은 이름 모두를 낸다."""
    with stage() as (box, mailbox):
        def emails(handle):
            return sorted(p.email for p in mailbox.find_exact(handle, COMPANY))
        assert emails(PEER[1].upper()) == [PEER[1]], emails(PEER[1].upper())
        assert emails(COLLEAGUE["key"]) == [PEER[1]], "Notes 이름으로 찾았는데 동명이인이 섞였다"
        assert emails("서하늘/hn/nuri") == [PEER[1]], "약식 Notes 이름이 정식과 같은 사람에 닿지 않는다"
        assert emails(f"{COLLEAGUE['user_id']}({PEER[0]})") == [PEER[1]], "ID 꼴로 찾았는데 그 사람만이 아니다"
        assert emails(PEER[0]) == sorted([PEER[1], HOMONYM["email"]]), "이름으로는 같은 이름이 다 나와야 가를 수 있다"
        assert emails(EXTERNAL) == [] and emails("  ") == [], "밖의 주소 · 빈 꼴에 사람이 나왔다"
        assert len(mailbox.find_people(PEER[0], COMPANY)) == 2, "대역이 동명이인을 안 섞어 이 검사가 안 문다"


def check_level_floor_stays_inside_its_track():
    """등급 거르기 — 같은 갈래 안에서만 위아래 · 두 자리 등급(P10)을 글자 차례로 안 읽는다 · 등급 없는 직급은 빠진다."""
    def at(code, floor, grade=""):
        p = inbox.DirectoryPerson(email="", name="", name_eng="", notes="", user_id="", empno="", dept="", grade=grade,
                                  job_title="", company="", retired=False, grade_code=code)
        return inbox.level_at_least(p.level, floor)
    assert at("26", "P5") and at("27", "p5") and at("31", "P5"), "리더 · 부장 · 사장이 P5 이상에 안 들었다"
    assert not at("21", "P5"), "P4(차장)가 P5 이상에 들었다"
    assert not at("32", "P5"), "E7 이 P 갈래 거르기에 들었다"
    assert not at("45", "P1") and not at("", "E1"), "등급 없는 직급이 걸렀는데 남았다"
    assert at("", "P8", "고문") and at("99", "P5", " 고문 "), "고문이 임원급으로 안 섰다 — 코드가 표에 없으면 직급 이름을 본다"
    assert not at("", "P9", "고문"), "고문이 다른 임원 위에 섰다 — 임원의 낮은 쪽이어야 한다"
    assert not at("44", "P1", "소장") and not at("10", "P1", "이사"), "소장 · 이사는 직급만으로 등급을 안 준다"
    assert at("21", "P4", "고문") and not at("21", "P5", "고문"), "직급 코드의 표가 직급 이름보다 먼저다"
    raises(inbox.MailboxConfigError, lambda: at("26", "리더"))


def check_category_is_passed_through():
    with stage() as (box, mailbox):
        mailbox.find_people(PEER[1], COMPANY)
        mailbox.directory_answer(PEER[1], COMPANY, category="dept")
        asked = [urllib.parse.parse_qs(p.split("&", 1)[1], keep_blank_values=True)
                 for p in box.paths if "ag_org_search_json" in p]
        assert asked[-1].get("category") == ["dept"], "category 칸이 주소록에 안 실렸다"
        assert all(q.get("category") == [""] for q in asked[:-1]), "category 를 안 줬는데 빈 값이 아니다"


def check_org_chart_walks_the_tree_and_keeps_subtree_people():
    """조직도 — 나무를 끝까지 펼치고, 부서의 사람은 하위 조직까지 · 두 부서에 든 사람은 한 번 · 바로 든 사람만도 낸다."""
    with stage() as (box, mailbox):
        chart = mailbox.org_snapshot(COMPANY)
        assert sorted(chart.depts) == sorted(c for c, *_ in ORG_DEPTS), chart.depts
        top = chart.find_depts("소재 사업부")
        assert [d.code for d in top] == ["n300_00(07)"], "띄어쓰기를 가려 부서를 못 찾았다"
        assert len(chart.find_depts("소재")) == 3, "이름 일부로 찾은 부서가 다르다"
        assert [d.name for d in chart.path("n310_00(07)")] == ["소재사업부", "소재기획그룹"]
        deep = sorted(p.email for p in chart.people("n300_00(07)"))
        assert deep == sorted([OWNER["email"], PEER[1], TRAINEE["email"], HOMONYM["email"]]), deep
        assert [p.email for p in chart.people("n300_00(07)", deep=False)] == [OWNER["email"]]
        assert len(chart.people()) == 4, "임원 · 본부 두 곳에 든 사람이 둘로 셌다"
        assert chart.people("n310_00(07)")[0].dept_code == "n310_00(07)", "구성원의 부서 코드가 그 부서가 아니다"
        assert chart.members["n320_00(07)"] and not chart.members.get("없음"), chart.members
        groups = mailbox.org_groups(COMPANY, "jobtitle")
        assert [n for _, n in groups] == list(GROUPS.values()), groups
        members = mailbox.group_members("[07:직책]리더(07)")
        assert members == [] , members
        assert [m[3] for m in mailbox.group_members("[07:직책]일반(07)")] == \
            [p["email"] for p in DIRECTORY if p.get("job_title") == "일반"]
        raises(inbox.MailboxError, lambda: mailbox.group_members("없는 그룹"))
        raises(inbox.MailboxConfigError, lambda: mailbox.org_groups(COMPANY, "team"))
        raises(inbox.DirectoryGap, lambda: mailbox.org_snapshot("없는회사(99)"))
    with stage(session="login") as (_, mailbox):
        raises(inbox.SessionExpired, lambda: mailbox.org_snapshot(COMPANY))


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


def check_mailbox_is_found_from_the_server_root():
    with stage() as (box, mailbox):
        server = box.url[:-len(DB)]
        jar = pathlib.Path(tempfile.mkdtemp()) / "s.json"
        jar.write_text(json.dumps({"cookies": [{"name": COOKIE[0], "value": COOKIE[1], "domain": "127.0.0.1", "path": "/"}]}),
                       encoding="utf-8")
        assert inbox.discover_mailbox(server, jar, timeout=5) == box.url, "첫 화면에서 메일함 주소를 못 받았다"
        box.session = "login"
        raises(inbox.SessionExpired, lambda: inbox.discover_mailbox(server, jar, timeout=5))
        raises(inbox.MailboxConfigError, lambda: inbox.discover_mailbox(box.url, jar, timeout=5))
        assert not changing(box.paths), changing(box.paths)


def check_drafts_view_lists_only_drafts():
    with stage() as (box, mailbox):
        drafts = mailbox.list_drafts(count=10)
        assert [d.unid for d in drafts] == [U["draft"]] and drafts[0].folder == "(Drafts)", drafts
        assert U["draft"] not in {e.unid for e in mailbox.list(count=50)}, "받은편지함에 임시보관함 메일이 섰다"
        assert mailbox.body(drafts[0]) == "<p>초안 본문 — 시험 일정</p>"
    with stage(draft_view=False) as (box, mailbox):
        assert mailbox.list_drafts() is None


def check_search_is_one_field_scoped_and_keeps_unread():
    with stage() as (box, mailbox):
        before = box.unread()
        total, rows = mailbox.search("시험", scope="all", field="subject")
        assert total == 2 and [r.unid for r in rows] == [U["alone"], U["f_child"]], (total, rows)
        assert rows[1].folder == "소재 시험" and rows[0].folder == "", f"시스템 표지 [${{INBOX}}] 를 안 풀었다: {rows}"
        sent = mailbox.search("주간", scope="sent", field="subject")[1]
        assert [(r.unid, r.folder) for r in sent] == [(U["sent_1"], inbox.SENT_FOLDER)], sent
        assert [e.unid for e in mailbox.list_sent_mail(count=50)] == [U["sent_1"], U["sent_2"]]
        assert mailbox.search("시험", scope="draft", field="subject")[1][0].unid == U["draft"]
        assert U["draft"] not in {r.unid for r in mailbox.search("초안", scope="all", field="body")[1]}, "전체가 임시보관함을 들었다"
        assert mailbox.search("메모-표", scope="all", field="attachment")[0] == 1
        assert mailbox.search("없는 낱말", scope="all", field="subject") == (0, [])
        total, rows = mailbox.search("시험", scope="all", field="subject", count=1, page=2)
        assert total == 2 and [r.unid for r in rows] == [U["f_child"]], rows
        for bad in (dict(scope="everything"), dict(field="sender")):
            raises(inbox.MailboxConfigError, lambda b=bad: mailbox.search("시험", **b))
        raises(inbox.MailboxConfigError, lambda: mailbox.search("  "))
        asked = [p for p in box.paths if "ag_detail_search_mailbox" in p]
        assert asked and all(p.count("ssbj=") + p.count("sbdy=") + p.count("satt=") == 1 for p in asked), \
            f"한 번에 한 칸이 아니다: {asked}"
        assert box.unread() == before and not changing(box.paths), changing(box.paths)
    with stage(session="login") as (box, mailbox):
        raises(inbox.SessionExpired, lambda: mailbox.search("시험"))


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
