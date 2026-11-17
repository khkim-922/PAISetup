"""사내 일정 앱(HCL Domino 웹 일정)의 내 일정함을 읽는 손과, 일정을 바꾸는 이름 붙은 손 둘(``register`` · ``delete``) — 표준
라이브러리와 형제 스킬 ep-login 의 ``ep_session``(세션 파일 → 쿠키 통, 스킬 홈에 나란히 깔린 ``../../ep-login/scripts/``)만 쓰는
파일 하나. 막는 까닭과 바꾸는 손의 경계는 ``references/DESIGN.md``, 일정 앱의 주소와 꼴은 ``references/SOURCES.md`` 가 든다.

⚠ ``register`` · ``delete`` 는 남이 보는 회사 일정을 바꾸고 지운 일정은 되돌릴 손이 없다 — 사람이 그 한 건을 분명히 고른 뒤에만
부른다. 읽는 손은 잰 JSON 주소 셋 밖을 서버에 닿기 전에 ``ChangeRefused`` 로 막는다(이 앱은 편집 화면 · 지우기도 GET 이다).

어떻게 부르나
    로그인은 이 파일이 하지 않는다. 사내 SSO 세션을 쿠키 파일(Playwright 저장 상태 꼴 ``{"cookies": [...]}``)로 남기는 손이
    따로 있고 — 메일 손과 같은 세션 한 벌이다 — 이 파일은 그 쿠키로 일정 서버에 묻는다::

        import agenda

        r = agenda.Reader(url, cookies_file)            # url — 일정 앱 주소창의 …/calperson<NN>.nsf 까지(그 뒤는 버린다)
        book = r.book()                                 # 내 기본 일정함(kind=PEO · 여럿이면 defaultCalendar)
        for e in r.between(first, last, book):          # 서울 날짜 first ~ last 에 걸친 일정 — 시작 차례
            e.when(), e.title, e.keep_reason, agenda.Seen.of(e).handle
        for b in r.shared_books():                      # 공유받은 일정함(GRW · GRR) — 읽기만 한다
            r.between(first, last, b)                   # 줄마다 e.calendar(그 일정함 이름) · e.private(일정함을 가진 사람이 비공개로 든 것)

        want = agenda.Want("시험 일정", agenda.kst("2026-11-07 14:00"), agenda.kst("2026-11-07 15:00"))
        got = agenda.register(url, cookies_file, want)  # ⚠ 일정을 바꾼다 — 그 한 건을 사람이 확인한 뒤에만
        got.state                                       # added · already · clashed · unsure
        gone = agenda.delete(url, cookies_file, agenda.Seen.parse(handle))   # ⚠ 일정을 바꾼다 — 확인한 뒤에만
        gone.state                                      # deleted · gone · changed · unsure

    ``Reader.from_env()`` 는 환경변수로 세운다 — ``CALENDAR_URL`` · ``MAILBOX_COOKIES`` 둘 다 꼭 준다. 쿠키 파일의 자리는 이 파일이
    정하지 않는다 — 세션을 남기는 손이 정하고, 부르는 쪽이 그 경로를 넘긴다.

무엇을 내나
    시각은 다 시간대가 붙은 UTC 이고, 보이기(``Event.when``)는 서울이다. ``Seen`` 은 사람에게 보인 일정 한 줄의 손잡이다 — 그 줄의
    열쇠 · 그 일정의 열쇠(둘 다 사번이 든 일정 열쇠의 해시) · 제목 · 시작 · 끝의 지문 · 서울 날짜를 한 글줄(``handle``)로 들어,
    대화를 건너 지우기에 넘긴다. ``register`` 는 ``Added``, ``delete`` 는 ``Removed`` 를 내고 끝은 다시 읽은 일정이 정한다(``state``).
    ⚠ 공유받은 일정함의 줄이라는 표지는 글줄에 안 실린다 — ``Seen.parse`` 로 되읽은 손잡이는 내 일정함의 줄로 읽혀, 지우기가 내
    일정함에서 그 열쇠를 찾고 없으면 ``gone`` 이다. 공유 줄의 글줄 손잡이를 지우기에 넘기지 않는다.

    예외 — 세션이 끊겼으면 ``SessionExpired``, 막은 주소 · 지우지 않는 줄은 ``ChangeRefused``(까닭은 ``reason``), 등록 화면의 꼴이
    잰 것과 다르면 ``FormChanged``, 쿠키 파일이 없거나 비었으면 ``SessionMissing``(``CalendarConfigError`` 의 갈래), 주소 · 인자가
    틀리면 ``CalendarConfigError``, 그 밖은 ``CalendarError``(다 이것의 갈래다). 무엇을 했는지는 ``logging`` 으로 남긴다(로거 이름은
    이 모듈 이름) — 셈과 방향만 싣고 일정 제목 · 이름 · 사번은 안 싣는다.
"""

from __future__ import annotations

import dataclasses
import hashlib
import html
import html.parser
import json
import logging
import os
import pathlib
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent.parent / "ep-login" / "scripts"   # 형제 스킬 — 세션 파일을 읽는 자리
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_session  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다

log = logging.getLogger(__name__)

# ── 이름 붙은 값 ────────────────────────────────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9), "KST")   # 서울은 일광 절약이 없어 +09:00 고정이다 — 윈도의 zoneinfo 는 tzdata 없이 서울을 모른다
TIMEOUT_SECONDS = 30.0
TITLE_MOST = 60                     # 회사 일정에 넣는 제목의 상한 — 넘치면 자른다
NOTE_MOST = 80                      # 설명 칸에 넣는 글의 상한
REF_LENGTH = 16                     # 손잡이 속 해시의 길이(16진 글자)

# ── 일정 앱의 꼴(출처는 references/SOURCES.md) ────────────────────────────────────────────────────────
APP_URL = re.compile(r"^(https?://[^/]+)(/.+?\.nsf)", re.IGNORECASE)
# 잰 일정 앱 — 남긴 주소 · CALENDAR_URL 이 없을 때 쓰는 기본. 이 주소로 내 일정함이 안 읽히는 PC 는 그 사람의 일정 화면 주소를 받는다
DEFAULT_APP_URL = "http://pcfca03.posco.net/02/cal/calperson32.nsf"
LIST_PATH = "/agGetCalendar?OpenAgent&calltype=GNB"
EVENTS_PATH = "/getcalendareventMe?readform"
SHARED_EVENTS_PATH = "/getcalendarevent?readform"   # 공유받은 일정함의 일정 — 그 일정함의 서버 · DB 에서 묻는다
FORM_PATH = "/Eventquick?OpenForm"
SAVE_PATH = "/Eventquick?OpenForm&Seq=1"
DELETE_PATH = "/(wEventDelete)?openagent"
DELETE_FIXED = (("alim", ""), ("msgtitle", ""), ("isediter", "true"), ("SAResponse", "json"), ("lang", "kor"),
                ("allimTarget", ""))
KIND_MINE = "PEO"
TYPE_DEFAULT = "defaultCalendar"   # 내 일정함 줄 가운데 기본 일정함 — 일정함 목록의 `calendartype`(다른 값은 `TeamsCalendar`)
KINDS_SHARED = ("GRW", "GRR")       # 공유받은 일정함 — 일정함 목록이 그 서버(`calhost`) · DB(`caldbpath`)를 든다
SHARED_DB = re.compile(r"^/?([\w.-]+(?:/[\w.-]+)*\.nsf)$", re.IGNORECASE)
SHARED_HOST = re.compile(r"^[\w-]+(?:\.[\w-]+)*(?::\d+)?$")
CALLBACK = "seedAgenda"             # JSONP 의 함수 이름 — 아무 이름이나 받는다(잰 꼴은 이름 자리만)
# ⚠ 읽는 손이 짓지 않는 주소 — 편집 화면 · 등록 · 지우기와 그 앞 단계. 막기의 첫 문이고, 닫힌 목록(`Reader._read_only`)이 둘째 문이다
CHANGES_CALENDAR = re.compile(r"editdocument|eventquick|wEventDelete|agCheckDoc|confirmDel|quickRegistration|"
                              r"createdocument|deletedocument|saveoptions", re.IGNORECASE)
# 등록 화면이 꼭 든 칸 — 잰 저장 몸통의 「값이 찬 칸」 가운데 우리가 덮는 것. 하나라도 없으면 화면의 꼴이 바뀐 것이다
FORM_NEEDS = ("Form", "Subject", "Description", "StartDate", "EndDate", "CalendarID", "EventArea", "visibility",
              "callback", "Editors")
FORM_VALUE = "Event"
VISIBILITY = "public"               # 폼이 비워 둔 공개 범위 — 사람이 넣은 판의 값
CALLBACK_NEW = "new"
# 참석자 · 참조 칸 — 비워 보낸다(남에게 알림이 안 가게). 손님 수 칸(`…AadditionalGuests`)은 폼의 값 그대로다
GUEST_FIELDS = re.compile(r"^(att|ref)(?!AadditionalGuests$)", re.IGNORECASE)
STAMP_FORM = "%Y-%m-%d %H:%M"       # 등록의 StartDate · EndDate · `kst` 가 받는 꼴
STAMP_ROW = "%Y-%m-%d %H:%M:%S"     # 일정 줄의 start · end
RESPONSE_PENDING = "needsAction"    # 참석 답을 아직 안 한 초대(철자 그대로 — `attRsponseStatus`)
MEETING = "meeting"                 # 줄의 eventtype(소문자로 견준다)
TRUE_WORDS = ("true", "1", "y", "yes")

# 넣기의 끝 — 다시 읽어 그 일정이 섰나. clashed 는 확인 뒤 새 겹침이 생겨 안 넣은 것이다
ADDED, ALREADY, UNSURE, CLASHED = "added", "already", "unsure", "clashed"
# 지우기의 끝 — 다시 읽어 그 일정이 사라졌나. `UNSURE` 는 넣기와 같은 값이다
DELETED, GONE, CHANGED = "deleted", "gone", "changed"
# 지우지 않는 까닭(`Event.keep_reason`) — 쓰는 사람이 손수 든 단건만 지운다
KEEP_INVITE, KEEP_MEETING, KEEP_REPEAT, KEEP_ALL_DAY, KEEP_LOCKED = "invite", "meeting", "repeat", "all_day", "locked"
KEEP_SHARED = "shared"              # 공유받은 일정함의 줄 — 읽기만 한다


class CalendarError(Exception):
    """일정을 못 읽었거나 못 바꿨다. 메시지는 진단용이고 일정 제목 · 이름 · 사번은 안 든다."""


class CalendarConfigError(CalendarError):
    """주소 · 쿠키 파일 · 인자가 틀렸다 — 묻기 전에 잡힌다."""


class SessionMissing(CalendarConfigError):
    """쿠키 파일이 없거나 쿠키가 하나도 없다 — 사내 세션을 먼저 받아 남긴다."""


class SessionExpired(CalendarError):
    """세션이 끊겼다 — 답 대신 SSO 화면이 왔거나 SSO 로 보냈다. 세션을 다시 받아 쿠키 파일을 새로 남긴다."""


class ChangeRefused(CalendarError):
    """읽는 손이 일정을 바꿀 주소(또는 읽기 전용으로 잰 꼴 밖의 주소)를 지었거나, 지우는 손이 지우지 않는 줄을 받았다 — 서버에
    닿기 전에 막았다. 지우지 않는 줄이면 ``reason`` 이 ``Event.keep_reason`` 의 값이다."""

    def __init__(self, message: str, reason: str = ""):
        super().__init__(message)
        self.reason = reason


class FormChanged(CalendarError):
    """등록 화면의 꼴이 잰 것과 다르다 — 넣지 않았다."""


# ── 꼴 ─────────────────────────────────────────────────────────────────────────────────────────────


def kst(text: str) -> datetime:
    """서울 벽시계 ``YYYY-MM-DD HH:MM`` → 시간대가 붙은 UTC. 꼴이 아니면 ``CalendarConfigError``."""
    try:
        return datetime.strptime(text.strip(), STAMP_FORM).replace(tzinfo=KST).astimezone(timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise CalendarConfigError(f"시각은 YYYY-MM-DD HH:MM(서울) 꼴로 준다: {text!r}") from exc


def kst_day(t: datetime) -> date:
    """시각의 서울 날짜."""
    return _aware(t).astimezone(KST).date()


def _aware(t: datetime) -> datetime:
    if t.tzinfo is None:
        raise CalendarConfigError("시간대 없는 시각은 받지 않는다 — 어느 시계의 것인지 모르면 9시간이 조용히 틀린다")
    return t


def _stamp(t: datetime) -> str:
    """열쇠 · 지문에 싣는 시각 글자 — UTC ISO 8601(초까지). 같은 일정이면 늘 같은 글자다."""
    return _aware(t).astimezone(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Book:
    """일정함 하나 — 일정함 목록의 한 줄. 내 일정함(``kind=PEO``)은 ``owner`` 가 쓰는 사람의 Notes 이름(``CN=…/OU=…/OU=…/O=…``)이고
    ``server`` · ``db_path`` 가 비었다(읽는 손의 주소를 쓴다). 공유받은 일정함(``GRW`` · ``GRR``)은 ``owner`` 가 그 일정함을 가진 사람의
    Notes 이름 · ``name`` 이 목록에 뜨는 이름 · ``server`` · ``db_path`` 가 그 일정함이 든 자리(목록의 ``calhost`` · ``caldbpath``)다."""
    calendar_id: str
    owner: str
    kind: str = KIND_MINE
    name: str = ""
    server: str = ""
    db_path: str = ""

    @property
    def shared(self) -> bool:
        return self.kind != KIND_MINE


@dataclass(frozen=True)
class Event:
    """일정 한 줄. 반복 일정은 날짜마다 한 줄로 풀려 온다 — 같은 ``event_id`` 가 여러 날에 선다. 시각은 UTC."""
    event_id: str
    title: str
    start: datetime
    end: datetime
    all_day: bool = False
    repeat: bool = False
    response: str = ""                 # attRsponseStatus — needsAction · accepted · 빈 글자
    meeting: bool = False              # eventtype 이 Meeting
    editable: bool = False             # 쓰는 사람이 이 줄을 고칠 수 있다 — 줄의 `editors` 에 그 사람이 든다(`_edits`)
    calendar: str = ""                 # 공유받은 일정함의 이름(``Book.name``) — 내 일정함의 줄이면 빈 글자
    private: bool = False              # 줄의 visibility 가 private — 일정함을 가진 사람이 비공개로 든 일정

    @property
    def day(self) -> date:
        return kst_day(self.start)

    @property
    def keep_reason(self) -> str:
        """지우지 않는 까닭 — 빈 글자면 지워도 된다(쓰는 사람이 손수 든 단건). 갈래마다의 까닭은 ``references/DESIGN.md``
        「지우지 않는 줄」이 든다."""
        if self.calendar:
            return KEEP_SHARED
        if self.response:
            return KEEP_INVITE
        if self.meeting:
            return KEEP_MEETING
        if self.repeat:
            return KEEP_REPEAT
        if self.all_day:
            return KEEP_ALL_DAY
        if not self.editable:
            return KEEP_LOCKED
        return ""

    def overlaps(self, start: datetime, end: datetime) -> bool:
        return self.start < end and start < self.end

    def when(self) -> str:
        """「10:00–11:00」 · 「하루 종일」 — 서울 시각."""
        if self.all_day:
            return "하루 종일"
        return f"{self.start.astimezone(KST):%H:%M}–{self.end.astimezone(KST):%H:%M}"


@dataclass(frozen=True)
class Want:
    """회사 일정에 넣을 한 건 — 시각은 시간대가 붙은 것만(``kst`` 로 짓는다). ``note`` 는 설명 칸이다."""
    title: str
    start: datetime
    end: datetime
    note: str = ""

    @property
    def day(self) -> date:
        return kst_day(self.start)

    def cleaned(self) -> Want:
        """회사 일정에 실제로 남는 꼴 — 보이지 않는 글자 · 줄바꿈을 걷고 상한에서 자른 제목 · 설명. 확인에 이 꼴을 보인다."""
        return dataclasses.replace(self, title=clean_title(self.title), note=clean_note(self.note))


@dataclass(frozen=True)
class Seen:
    """사람에게 보인 일정 한 줄의 손잡이 — 그 줄의 열쇠(``ref`` — 일정 열쇠 · 시작의 해시) · 그 일정의 열쇠(``ident`` — 일정
    열쇠만의 해시 · 시각을 옮겨도 같다) · 제목 · 시작 · 끝의 지문(``mark``) · 서울 날짜(``day``). 일정 열쇠(사번이 든다)를 그대로
    싣지 않는다. ``handle`` 이 한 글줄 꼴이고 ``parse`` 가 되읽는다 — 글줄에는 ``shared`` 가 안 실려, 되읽은 손잡이는 늘 거짓이다."""
    ref: str
    ident: str
    mark: str
    day: date
    shared: bool = False               # 공유받은 일정함의 줄 — 지우기가 묻지 않고 거절한다(``of`` 로 지은 것만 · ``parse`` 는 거짓)

    _HANDLE = re.compile(rf"^([0-9a-f]{{{REF_LENGTH}}})\.([0-9a-f]{{{REF_LENGTH}}})\.([0-9a-f]{{{REF_LENGTH}}})"
                         rf"\.(\d{{4}}-\d{{2}}-\d{{2}})$")

    @classmethod
    def of(cls, e: Event) -> Seen:
        return cls(ref=event_ref(e), ident=event_ident(e), mark=event_mark(e), day=e.day, shared=bool(e.calendar))

    @property
    def handle(self) -> str:
        return f"{self.ref}.{self.ident}.{self.mark}.{self.day.isoformat()}"

    @classmethod
    def parse(cls, text: str) -> Seen:
        m = cls._HANDLE.match((text or "").strip())
        if not m:
            raise CalendarConfigError("일정 손잡이의 꼴이 아니다 — 일정을 읽은 답의 handle 을 그대로 준다")
        try:
            day = date.fromisoformat(m.group(4))
        except ValueError as exc:
            raise CalendarConfigError("일정 손잡이의 날짜가 날짜가 아니다") from exc
        return cls(ref=m.group(1), ident=m.group(2), mark=m.group(3), day=day)


@dataclass(frozen=True)
class Added:
    """넣기의 끝 — ``state`` 는 added(다시 읽어 섰다) · already(같은 일정이 이미 있다 · 안 넣었다) · clashed(확인 뒤 그 시각에 새
    일정이 들었다 · 안 넣었다) · unsure(넣었는지 모른다)."""
    state: str
    event: Event | None = None
    detail: str = ""


@dataclass(frozen=True)
class Removed:
    """지우기의 끝 — ``state`` 는 deleted(다시 읽어 사라졌다) · gone(그날에 없다 · 안 불렀다) · changed(보인 뒤 바뀌었다 · 안
    지웠다 — ``event`` 가 지금의 그 줄이다) · unsure(불렀는데 다시 읽어도 남아 있다 · 지웠는지 모른다)."""
    state: str
    event: Event | None = None
    detail: str = ""


def event_key(e: Event) -> str:
    return f"{e.event_id}@{_stamp(e.start)}"


def event_ref(e: Event) -> str:
    """일정 한 줄을 가리키는 열쇠 — 일정 열쇠(사번이 든다)의 해시."""
    return hashlib.sha256(event_key(e).encode()).hexdigest()[:REF_LENGTH]


def event_ident(e: Event) -> str:
    """그 일정의 열쇠 — 일정 열쇠만의 해시. 같은 날 시각을 옮긴 줄을 「바뀜」으로 알아본다(반복의 날마다 같은 값이다)."""
    return hashlib.sha256(e.event_id.encode()).hexdigest()[:REF_LENGTH]


def event_mark(e: Event) -> str:
    """보인 일정의 지문 — 제목 · 시작 · 끝. 지우기가 지금의 그 줄과 견준다(그사이 바뀌었으면 안 지운다)."""
    return hashlib.sha256(f"{clean_title(e.title)}|{_stamp(e.start)}|{_stamp(e.end)}".encode()).hexdigest()[:REF_LENGTH]


def _clean(text: str, most: int) -> str:
    text = "".join(ch for ch in unicodedata.normalize("NFC", text or "") if unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()[:most]


def clean_title(text: str) -> str:
    """제목 — 보이지 않는 글자 · 줄바꿈을 걷고 ``TITLE_MOST`` 에서 자른다. 회사 일정에 남는 글이다."""
    return _clean(text, TITLE_MOST)


def clean_note(text: str) -> str:
    """설명 칸 — 제목과 같은 거름에 ``NOTE_MOST`` 상한."""
    return _clean(text, NOTE_MOST)


def same_event(e: Event, w: Want) -> bool:
    """같은 일정인가 — 제목 · 시작 · 끝이 같다. 넣기 앞에 이미 있나 · 넣기 뒤에 섰나를 이것 하나로 본다."""
    return clean_title(e.title) == clean_title(w.title) and e.start == w.start and e.end == w.end


# ── 읽는 손 ─────────────────────────────────────────────────────────────────────────────────────────


class Reader:
    """일정함을 읽는 손 — 읽기 전용으로 잰 주소 셋만 묻는다. 바꾸는 손 둘(``register`` · ``delete``)도 이 손의 세션을 쓴다."""

    def __init__(self, url: str, cookies_file: pathlib.Path | str, *, timeout: float = TIMEOUT_SECONDS):
        """``url`` 은 ``…/<이름>.nsf`` 까지 든 일정 앱 주소(그 뒤는 버린다). 주소 · 쿠키 파일이 틀리면 묻기 전에
        ``CalendarConfigError``."""
        found = APP_URL.match((url or "").strip())
        if not found:
            raise CalendarConfigError("일정 앱 주소(…/이름.nsf)가 아니다")
        self.server, self.db_path = found.group(1), found.group(2)
        self.timeout = timeout
        if not str(cookies_file or "").strip():
            raise SessionMissing("쿠키 파일을 안 줬다 — 세션을 남긴 손이 낸 경로를 넘긴다")
        jar = ep_session.load_jar(cookies_file, missing=SessionMissing)   # 다른 사내 호스트의 쿠키는 쿠키 통이 일정 서버에 안 싣는다
        self._opener = ep_session.opener(jar)   # 리다이렉트는 안 따라간다 — 따라가면 쿠키가 SSO 에 실린다
        self._calendars: list[dict] | None = None   # 받은 일정함 목록 — 이 손이 사는 동안 한 번만 묻는다(``calendars``)
        db = re.escape(self.db_path)
        day = r"\d{4}-\d{2}-\d{2}"
        # 읽는 손이 물을 수 있는 주소 꼴 — 닫힌 목록이라 새 꼴은 안 바꾸는 것을 잰 뒤 여기에 더해야 묻는다
        self._read_only = (
            re.compile(rf"^{db}{re.escape(LIST_PATH)}$"),
            re.compile(rf"^{db}{re.escape(EVENTS_PATH)}&callback={CALLBACK}&calendarId=[\w%.-]+&username=[\w%.+-]+"
                       rf"&start={day}&end={day}&kind={KIND_MINE}$"),
        )
        # 공유받은 일정함의 일정 — 그 일정함의 DB 아래 이 꼴 하나만 묻는다(서버는 `_shared_server` 가 가린다)
        self._read_shared = re.compile(rf"^/[\w./-]+\.nsf{re.escape(SHARED_EVENTS_PATH)}&callback={CALLBACK}"
                                       rf"&calendarId=[\w%.-]+&username=[\w%.+-]+&start={day}&end={day}"
                                       rf"&kind=(?:{'|'.join(KINDS_SHARED)})$")

    @classmethod
    def from_env(cls) -> Reader:
        """환경변수로 세운다 — ``CALENDAR_URL`` · ``MAILBOX_COOKIES``(둘 다 꼭 준다 · 없으면 ``CalendarConfigError`` · ``SessionMissing``)."""
        url = os.environ.get("CALENDAR_URL", "").strip()
        if not url:
            raise CalendarConfigError("CALENDAR_URL 이 비어 있다 — 일정 앱 주소의 …/이름.nsf 까지 준다")
        return cls(url, os.environ.get("MAILBOX_COOKIES", "").strip())

    @property
    def url(self) -> str:
        return self.server + self.db_path

    # ── 묻기 ──
    def _get(self, path: str) -> tuple[bytes, str]:
        """읽기 GET — 앱 안의 ``path``. 일정을 바꾸는 주소 · 잰 꼴 밖의 주소는 묻지 않고 ``ChangeRefused``."""
        if CHANGES_CALENDAR.search(path):
            raise ChangeRefused("일정을 바꾸는 주소라 묻지 않는다")
        full = self.db_path + path
        if not any(p.match(full) for p in self._read_only):
            raise ChangeRefused("읽기 전용으로 잰 주소 꼴이 아니라 묻지 않는다")
        return self._open(self.server + full)

    def _get_shared(self, server: str, path: str) -> tuple[bytes, str]:
        """공유받은 일정함의 읽기 GET — 그 일정함의 서버 · DB 아래 잰 꼴 하나만. 꼴 밖이면 묻지 않고 ``ChangeRefused``."""
        if CHANGES_CALENDAR.search(path) or not self._read_shared.match(path):
            raise ChangeRefused("공유 일정함의 읽기 전용으로 잰 주소 꼴이 아니라 묻지 않는다")
        return self._open(server + path)

    def _shared_server(self, host: str) -> str:
        """공유 일정함 서버의 주소 — 읽는 손과 같은 호스트거나 같은 사내 도메인(첫 이름표를 뗀 나머지)의 호스트만. 세션 쿠키를
        사내 밖으로 싣지 않으려는 문이다. 아니면 ``CalendarError``."""
        host = (host or "").strip().lower()
        own = urllib.parse.urlsplit(self.server)
        parts = (own.hostname or "").split(".")
        domain = ".".join(parts[1:]) if len(parts) >= 3 and not parts[-1].isdigit() else ""
        bare = host.split(":", 1)[0]
        if not SHARED_HOST.match(host) or not (host == own.netloc.lower() or (domain and bare.endswith("." + domain))):
            raise CalendarError("공유 일정함의 서버가 사내 도메인 밖이라 묻지 않는다")
        return f"{own.scheme}://{host}"

    def _open(self, url: str, data: bytes | None = None) -> tuple[bytes, str]:
        """막기 없는 요청 — 읽기는 ``_get`` · ``_get_shared`` 를 거쳐서만, 바꾸기는 ``register`` · ``delete`` 만 이것을 바로 부른다."""
        req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
        if data is not None:
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except ep_session.Redirected as exc:
            raise SessionExpired("세션이 끊겼다 — 일정 서버가 다른 곳으로 보냈다") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise SessionExpired(f"일정 서버가 거절했다(HTTP {exc.code})") from exc
            raise CalendarError(f"일정 서버가 HTTP {exc.code} 를 냈다") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise CalendarError(f"일정 서버에 못 닿았다: {type(exc).__name__}") from exc

    @staticmethod
    def _text(data: bytes, kind: str) -> str:
        m = re.search(r"charset=([\w-]+)", kind or "", re.IGNORECASE)
        try:
            return data.decode(m.group(1) if m else "utf-8", errors="replace")
        except LookupError:
            return data.decode("utf-8", errors="replace")

    def calendars(self) -> list[dict]:
        """일정함 목록 — JSON 배열(``text/html`` 로 온다). 내 것 · 공유받은 것이 다 든다. JSON 이 아니면 끊긴 세션이다.
        한 손은 목록을 한 번만 받는다 — 오래 쥐고 여러 판을 묻는 앱은 판마다 손을 새로 세워야 새 공유 일정함이 보인다."""
        if self._calendars is not None:
            return list(self._calendars)
        data, kind = self._get(LIST_PATH)
        try:
            rows = json.loads(self._text(data, kind))
        except ValueError:
            raise SessionExpired("일정함 목록 대신 JSON 이 아닌 답이 왔다 — 세션이 끊긴 것으로 읽는다") from None
        if not isinstance(rows, list):
            raise CalendarError("일정함 목록이 배열이 아니다")
        self._calendars = [r for r in rows if isinstance(r, dict)]
        return list(self._calendars)

    def _mine(self) -> list[dict]:
        """내 일정함 줄(``kind=PEO``) — 둘 이상이면 ``owner`` 가 다 같을 때만 선다(내 일정함이 기본 · Teams 둘인 사람). ``owner`` 가
        다른 줄이 섞이면 ``CalendarError``(남의 일정함을 내 것으로 읽지 않게)."""
        mine = [r for r in self.calendars() if str(r.get("kind", "")).upper() == KIND_MINE]
        if not mine:
            raise CalendarError(f"내 일정함(kind={KIND_MINE})이 0개다")
        owners = {str(r.get("owner") or "").strip() for r in mine}
        if len(mine) > 1 and len(owners) != 1:
            raise CalendarError(f"내 일정함(kind={KIND_MINE})이 {len(mine)}개고 owner 가 서로 다르다")
        return mine

    def book(self) -> Book:
        """내 기본 일정함 — 넣기 · 지우기가 가는 곳. ``kind=PEO`` 한 줄이면 그 줄이고, 여럿(같은 ``owner``)이면 ``calendartype=defaultCalendar``
        한 줄이다. 없거나 그 줄이 하나가 아니면 ``CalendarError``."""
        mine = self._mine()
        if len(mine) > 1:
            mine = [r for r in mine if str(r.get("calendartype") or "") == TYPE_DEFAULT]
            if len(mine) != 1:
                raise CalendarError(f"내 일정함이 여럿인데 기본 일정함(calendartype={TYPE_DEFAULT})이 {len(mine)}개다")
        cid, owner = str(mine[0].get("calendarid") or "").strip(), str(mine[0].get("owner") or "").strip()
        if not cid or not owner:
            raise CalendarError("내 일정함 줄에 calendarid · owner 가 없다")
        return Book(calendar_id=cid, owner=owner)

    def side_books(self) -> list[Book]:
        """기본 일정함 밖의 내 일정함(Teams 따위 · 같은 ``owner``) — 읽기만 한다. ``name`` 이 줄의 ``subject``(없으면 ``calendartype``)다."""
        main = self.book()
        out = []
        for r in self._mine():
            cid = str(r.get("calendarid") or "").strip()
            if cid and cid != main.calendar_id:
                out.append(Book(calendar_id=cid, owner=main.owner, name=str(r.get("subject") or r.get("calendartype") or "").strip() or cid))
        return out

    def mine_between(self, first: date, last: date) -> tuple[list[Event], list[tuple[str, str]]]:
        """내 일정함 전부의 서울 날짜 ``first`` ~ ``last`` 일정 — 기본 일정함의 줄과, 기본 밖 일정함의 줄(``calendar`` 에 그 이름 ·
        지우는 손잡이는 없다)을 시작 차례로 한 목록에 낸다. 기본 밖 일정함이 안 읽히면(세션 끊김이 아닌 한) 나머지는 낸다 —
        두 번째에 (이름, 까닭)을 단다."""
        got = self.between(first, last)
        failed = []
        for b in self.side_books():
            try:
                got += self.between(first, last, b)
            except SessionExpired:
                raise
            except CalendarError as exc:
                failed.append((b.name, str(exc)))
        got.sort(key=lambda e: (e.start, e.end, e.title))
        return got, failed

    def shared_books(self) -> list[Book]:
        """공유받은 일정함 — 일정함 목록의 ``GRW`` · ``GRR`` 줄(목록 차례). 서버 · DB · 열쇠 · 일정함을 가진 사람이 빈 줄은 버린다. 사람마다 다른
        값(누구의 일정함이 · 어느 서버 · DB 에 있나)은 다 이 목록이 든다."""
        out = []
        for r in self.calendars():
            kind = str(r.get("kind", "")).upper()
            if kind not in KINDS_SHARED:
                continue
            cid = str(r.get("calendarid") or "").strip()
            owner = str(r.get("sourceowner") or r.get("owner") or "").strip()
            host = str(r.get("calhost") or "").strip()
            found = SHARED_DB.match(str(r.get("caldbpath") or "").strip())
            if not (cid and owner and host and found):
                log.info("공유 일정함 한 줄을 버렸다 — 서버 · DB · 열쇠 · 일정함을 가진 사람 가운데 빈 칸이 있다")
                continue
            name = str(r.get("subject") or "").strip() or _person(owner)
            out.append(Book(calendar_id=cid, owner=owner, kind=kind, name=name, server=host, db_path="/" + found.group(1)))
        return out

    def events(self, start: date, end: date, book: Book | None = None) -> list[Event]:
        """``start`` 부터 ``end`` 까지(앱이 받는 그대로)의 일정 — 반복(``data``) · 단건(``data2``) 두 배열을 다 받는다. 시작 차례.
        ``book`` 이 없으면 내 일정함이다. 공유받은 일정함이면 그 일정함의 자리에서 묻고 줄마다 ``calendar`` 에 그 이름을 단다."""
        book = book or self.book()
        q = urllib.parse.urlencode({"callback": CALLBACK, "calendarId": book.calendar_id, "username": book.owner,
                                    "start": start.isoformat(), "end": end.isoformat(), "kind": book.kind})
        if book.shared:
            data, kind = self._get_shared(self._shared_server(book.server), f"{book.db_path}{SHARED_EVENTS_PATH}&{q}")
        else:
            data, kind = self._get(f"{EVENTS_PATH}&{q}")
        text = self._text(data, kind).strip()
        m = re.fullmatch(rf"{CALLBACK}\((.*)\)\s*;?", text, re.S)
        if not m:
            raise SessionExpired("일정 대신 JSONP 가 아닌 답이 왔다 — 세션이 끊긴 것으로 읽는다")
        try:
            body = json.loads(m.group(1))
        except ValueError:
            raise CalendarError("일정 JSONP 의 몸통을 못 읽었다") from None
        if not isinstance(body, dict):
            raise CalendarError("일정 JSONP 의 몸통이 객체가 아니다")
        out: dict[str, Event] = {}
        skipped = 0
        for name in ("data", "data2"):
            for row in body.get(name) or ():
                e = parse_row(row, book.owner) if isinstance(row, dict) else None
                if e is None:
                    skipped += 1
                    continue
                if book.shared or book.name:
                    e = dataclasses.replace(e, calendar=book.name or _person(book.owner))
                out.setdefault(event_key(e), e)
        events = sorted(out.values(), key=lambda e: (e.start, e.end, e.title))
        log.info("일정: %d줄(반복 %d · 단건 %d) · 못 읽은 줄 %d", len(events), len(body.get("data") or ()),
                 len(body.get("data2") or ()), skipped)
        return events

    def between(self, first: date, last: date, book: Book | None = None) -> list[Event]:
        """서울 날짜 ``first`` ~ ``last``(둘 다 든다)에 걸친 일정 — ``book`` 이 없으면 내 일정함이다. 앱의 ``end`` 가 그날을 드는지 안 쟀으므로 하루 더 묻고 서울
        날짜로 거른다 — 어느 쪽이든 그날의 일정이 빠지지 않는다."""
        if last < first:
            raise CalendarConfigError("끝 날짜가 시작 날짜보다 앞이다")
        lo = datetime(first.year, first.month, first.day, tzinfo=KST)
        hi = datetime(last.year, last.month, last.day, tzinfo=KST) + timedelta(days=1)
        return [e for e in self.events(first, last + timedelta(days=1), book)
                if e.overlaps(lo, hi) or (e.start == e.end and lo <= e.start < hi)]


def _person(notes_name: str) -> str:
    """Notes 이름(``CN=이름/OU=…``)의 이름 — 꼴이 아니면 그대로."""
    m = re.match(r"^CN=([^/]+)", notes_name or "")
    return m.group(1).strip() if m else (notes_name or "").strip()


def _truthy(v: Any) -> bool:
    return str(v).strip().lower() in TRUE_WORDS


def _at(text: str, zone: str) -> datetime:
    """일정 줄의 시각 — ``YYYY-MM-DD HH:MM:SS``. 시간대 칸이 비면 서울, ``+HH:MM`` 이면 그 시간대."""
    naive = datetime.strptime(text.strip(), STAMP_ROW)
    tz = KST
    m = re.fullmatch(r"([+-])(\d{2}):(\d{2})", (zone or "").strip())
    if m:
        sign = 1 if m.group(1) == "+" else -1
        tz = timezone(sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3))))
    return naive.replace(tzinfo=tz).astimezone(timezone.utc)


def _edits(row: Mapping[str, Any], me: str) -> bool:
    """쓰는 사람이 이 줄을 고칠 수 있나 — 앱의 ``editable`` 이 참이거나, 줄의 ``editors``(쉼표로 이은 Notes 이름)에 ``me`` 가 든다.
    앱의 ``editable`` 은 내 일정 · 공유 일정 모두 빈 글자로 오고, 고칠 수 있는 사람은 ``editors`` 가 든다."""
    if _truthy(row.get("editable")):
        return True
    names = {n.strip().casefold() for n in str(row.get("editors") or "").split(",") if n.strip()}
    return bool(me) and me.strip().casefold() in names


def parse_row(row: Mapping[str, Any], me: str = "") -> Event | None:
    """일정 줄 하나 — 시각을 못 읽으면 None(그 줄만 버린다). ``me`` 는 쓰는 사람의 Notes 이름(내 일정함의 ``owner``)이다."""
    zone = str(row.get("timeZone") or "")
    try:
        start, end = _at(str(row.get("start") or ""), zone), _at(str(row.get("end") or ""), zone)
    except ValueError:
        return None
    return Event(event_id=str(row.get("eventId") or ""), title=html.unescape(str(row.get("title") or "")).strip(),
                 start=start, end=max(start, end), all_day=_truthy(row.get("allDay")), repeat=_truthy(row.get("repeat")),
                 response=str(row.get("attRsponseStatus") or ""),
                 meeting=str(row.get("eventtype") or "").strip().lower() == MEETING, editable=_edits(row, me),
                 private=str(row.get("visibility") or "").strip().lower() == "private")


# ── 넣기 — 일정을 바꾸는 손 하나 ────────────────────────────────────────────────────────────────────


class _Form(html.parser.HTMLParser):
    """등록 화면의 첫 폼에서 이름 붙은 칸의 값 — 숨은 칸 · 글 칸 · 고른 상자 · 체크된 칸 · 글 상자."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.fields: dict[str, str] = {}
        self.forms = 0
        self._in_form = False
        self._textarea: str | None = None
        self._select: str | None = None
        self._first_option: str | None = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "form":
            self.forms += 1
            self._in_form = self.forms == 1
            return
        if not self._in_form:
            return
        name = a.get("name", "")
        if tag == "input" and name:
            kind = a.get("type", "text").lower()
            if kind in ("checkbox", "radio") and "checked" not in a:
                return
            if kind in ("submit", "button", "image", "reset", "file"):
                return
            self.fields.setdefault(name, a.get("value", ""))
        elif tag == "textarea" and name:
            self._textarea = name
            self.fields.setdefault(name, "")
        elif tag == "select" and name:
            self._select, self._first_option = name, None
        elif tag == "option" and self._select:
            value = a.get("value", "")
            if self._first_option is None:
                self._first_option = value
            if "selected" in a:
                self.fields[self._select] = value

    def handle_endtag(self, tag):
        if tag == "form":
            self._in_form = False
        elif tag == "textarea":
            self._textarea = None
        elif tag == "select" and self._select:
            self.fields.setdefault(self._select, self._first_option or "")
            self._select = None

    def handle_data(self, data):
        if self._textarea:
            self.fields[self._textarea] += data


def _span(day: date, end: datetime) -> tuple[date, date]:
    """그 일정을 다시 읽을 날 — 시작하는 날부터 끝나는 날 다음 날까지(앱의 ``end`` 가 그날을 드는지 안 쟀다)."""
    return day, kst_day(end) + timedelta(days=1)


def register(url: str, cookies_file: pathlib.Path | str, want: Want, *, timeout: float = TIMEOUT_SECONDS,
             reader: Reader | None = None, shown_clash: Iterable[str] | None = None) -> Added:
    """⚠ 회사 일정을 바꾼다 — 내 일정함에 한 건을 넣고 ``Added`` 를 낸다. 사람이 그 한 건을 확인한 뒤에만 부른다.

    ``shown_clash`` 는 확인에 보인 겹침의 ``event_ref`` 들이다 — 그 밖의 일정이 그 시각에 생겼으면 ``clashed`` 로 안 넣는다.
    등록 화면에 잰 칸이 없으면 ``FormChanged``(안 넣음). 등록 화면을 열기 전에 진 것(세션 · 서버)은 아무것도 안 바꾼 채 올린다.
    """
    want = want.cleaned()
    if not want.title or _aware(want.end) <= _aware(want.start):
        raise CalendarConfigError("넣을 일정의 제목 · 시각이 비었거나 끝이 시작보다 앞이다")
    r = reader or Reader(url, cookies_file, timeout=timeout)
    book = r.book()
    first, last = _span(want.day, want.end)
    before = r.events(first, last, book)
    hit = next((e for e in before if same_event(e, want)), None)
    if hit is not None:
        log.info("일정 넣기 — 같은 일정이 이미 있어 넣지 않았다")
        return Added(ALREADY, hit)
    if shown_clash is not None:
        fresh = {event_ref(e) for e in before if e.overlaps(want.start, want.end)} - set(shown_clash)
        if fresh:
            log.info("일정 넣기 — 확인 뒤 그 시각에 새 일정 %d건이 들어 넣지 않았다", len(fresh))
            return Added(CLASHED)
    page, kind = r._open(r.url + FORM_PATH)
    form = _Form()
    form.feed(r._text(page, kind))
    if form.forms == 0:
        raise SessionExpired("등록 화면 대신 폼 없는 답이 왔다 — 세션이 끊긴 것으로 읽는다 · 넣지 않았다")
    lacking = [n for n in FORM_NEEDS if n not in form.fields]
    if lacking or form.fields.get("Form") != FORM_VALUE or not form.fields.get("Editors"):
        raise FormChanged(f"등록 화면에 잰 칸이 없다({len(lacking)}칸) — 넣지 않았다")
    # 폼의 칸을 다 기본값째 싣고 잰 칸만 바꾼다 — 쓰는 사람 몫(`Editors` · `calEditors`)과 고정 값은 폼이 채운 그대로다
    fields = {k: ("" if GUEST_FIELDS.match(k) else v) for k, v in form.fields.items()}
    fields.update(CalendarID=book.calendar_id, Subject=want.title, Description=want.note,
                  StartDate=want.start.astimezone(KST).strftime(STAMP_FORM),
                  EndDate=want.end.astimezone(KST).strftime(STAMP_FORM),
                  EventArea=form.fields.get("EventArea", ""), visibility=form.fields.get("visibility") or VISIBILITY,
                  callback=CALLBACK_NEW)
    detail = ""
    try:
        r._open(r.url + SAVE_PATH, data=urllib.parse.urlencode(fields).encode("utf-8"))
    except CalendarError as exc:   # 저장 요청이 도중에 졌다 — 서버가 받았는지 모른다. 다시 읽어 가린다
        detail = type(exc).__name__
    try:
        after = r.events(first, last, book)
    except CalendarError as exc:
        log.warning("일정 넣기 — 다시 읽기가 졌다(%s) · 넣었는지 모른다", type(exc).__name__)
        return Added(UNSURE, None, type(exc).__name__)
    known = {event_key(e) for e in before}
    made = next((e for e in after if same_event(e, want) and event_key(e) not in known), None)
    log.info("일정 넣기 — %s", "다시 읽어 섰다" if made else "다시 읽어도 안 보인다")
    return Added(ADDED, made) if made else Added(UNSURE, None, detail)


# ── 지우기 — 일정을 바꾸는 손 하나 ──────────────────────────────────────────────────────────────────


def delete(url: str, cookies_file: pathlib.Path | str, target: Event | Seen, *, timeout: float = TIMEOUT_SECONDS,
           reader: Reader | None = None) -> Removed:
    """⚠ 회사 일정을 바꾼다 — 내 일정함의 한 줄을 지운다. 사람이 그 한 건을 확인한 뒤에만 부른다.

    ``target`` 은 사람에게 보인 그 줄(``Event``)이나 그 손잡이(``Seen``)다. ``Removed`` 를 낸다 — 그 줄이 옮겨졌거나 제목 · 시작 ·
    끝이 보인 것(``mark``)과 다르면 ``changed``, 그날에 없으면 ``gone``(둘 다 지우기를 안 부른다). 쓰는 사람이 손수 든 단건이
    아니면 묻기 전에 ``ChangeRefused``(``reason`` 에 까닭)."""
    seen = target if isinstance(target, Seen) else Seen.of(target)
    if seen.shared:   # 공유받은 일정함의 줄 — 내 일정함에 같은 열쇠의 줄이 있어도 그것을 지우지 않게 묻기 전에 거절한다
        raise ChangeRefused("공유받은 일정함의 줄이라 지우지 않는다", KEEP_SHARED)
    r = reader or Reader(url, cookies_file, timeout=timeout)
    book = r.book()
    first, last = seen.day, seen.day + timedelta(days=1)
    now = r.events(first, last, book)
    hit = next((e for e in now if event_ref(e) == seen.ref), None)
    if hit is None:
        moved = next((e for e in now if event_ident(e) == seen.ident and e.day == seen.day), None)
        if moved is not None:
            log.info("일정 지우기 — 보인 뒤 그 일정의 시각이 옮겨져 지우지 않았다")
            return Removed(CHANGED, moved)
        log.info("일정 지우기 — 그날에 그 줄이 없어 부르지 않았다")
        return Removed(GONE)
    if event_mark(hit) != seen.mark:
        log.info("일정 지우기 — 보인 뒤 그 줄이 바뀌어 지우지 않았다")
        return Removed(CHANGED, hit)
    if hit.keep_reason:
        raise ChangeRefused(f"손수 든 단건이 아니라 지우지 않는다({hit.keep_reason})", hit.keep_reason)
    q = urllib.parse.urlencode([("calendarId", book.calendar_id), ("eventId", hit.event_id), ("ownerId", book.owner),
                                ("userName", book.owner), *DELETE_FIXED])
    detail = ""
    try:
        r._open(f"{r.url}{DELETE_PATH}&{q}")
    except CalendarError as exc:   # 지우기 요청이 도중에 졌다 — 서버가 받았는지 모른다. 다시 읽어 가린다
        detail = type(exc).__name__
    try:
        after = r.events(first, last, book)
    except CalendarError as exc:
        log.warning("일정 지우기 — 다시 읽기가 졌다(%s) · 지웠는지 모른다", type(exc).__name__)
        return Removed(UNSURE, hit, type(exc).__name__)
    left = any(event_ref(e) == seen.ref for e in after)
    log.info("일정 지우기 — %s", "다시 읽어도 남아 있다" if left else "다시 읽어 사라졌다")
    return Removed(UNSURE, hit, detail) if left else Removed(DELETED, hit)
