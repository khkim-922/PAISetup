"""일정 손의 바탕 — 이름 붙은 값 · 예외 · 시각 · 꼴(일정함 · 일정 줄 · 넣을 것 · 손잡이 · 한 건 · 끝)과 시각 말. 바깥에 닿지 않는다.

형제 스킬 ep-login 의 자리를 ``sys.path`` 에 넣고 ``ep_command`` · ``ep_session`` 을 싣는 것도 여기다 — 일정 손의 모듈은 다 이 모듈부터 싣는다.
"""

from __future__ import annotations

import dataclasses
import hashlib
import logging
import pathlib
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent.parent / "ep-login" / "scripts"   # 형제 스킬 — 세션 파일을 읽는 자리
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_command  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다
import ep_session  # noqa: E402,F401 — 읽는 손이 바탕에서 받는다

LOGGER = "agenda"                   # 일정 손의 로거 이름 — 모듈이 여럿이어도 한 이름이다(부르는 쪽이 이 이름에 처리기를 단다)
log = logging.getLogger(LOGGER)

# ── 이름 붙은 값 ────────────────────────────────────────────────────────────────────────────────────
KST = ep_command.SEOUL                     # 서울 시간대 — 회의실 손과 주고받는 꼴이라 한 벌(ep_command)이다
TIMEOUT_SECONDS = 30.0
TITLE_MOST = 60                     # 회사 일정에 넣는 제목의 상한 — 넘치면 자른다
NOTE_MOST = 80                      # 설명 칸에 넣는 글의 상한
PLACE_MOST = 60                     # 장소 칸에 넣는 글의 상한(화면 칸은 200 자 — 대화가 넣는 장소는 짧다)
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
# 일정 한 건 미리 보기(장소 · 참석자 · 설명 · Teams 링크) — 문서 보기라 안 바꾼다(열기 전 뒤 `modified` 가 같다). 줄의 `url` 은 편집 화면이다
DETAIL_PATH = "/vweventprev/{unid}?opendocument"
UNID = re.compile(r"/vweventprev/([0-9A-Fa-f]{32})\?", re.IGNORECASE)
SEARCH_PATH = "/(agSearchCalendarEvent)?openagent"      # 상세검색 — 제목 · 장소 · 설명 · 참석자 · 기간
FT_SEARCH_PATH = "/(agFTSearchCalendarEvent)?openagent"  # 본문 전체 찾기
SEARCH_KEYS = ("callback", "username", "calendarId", "textColor", "colorId", "color", "eventTitle", "from", "to", "desc",
               "eventArea", "attend", "file")
FT_SEARCH_KEYS = ("callback", "calendarId", "username", "searchStr", "textColor", "colorId", "color")
# 공휴일 — 같은 서버의 공용 일정 DB(`/<회사 코드>/cal/calpublic.nsf`). 답은 HTML 안의 <RESULT>[…]</RESULT>
HOLIDAY_RESULT = re.compile(r"<RESULT>(.*?)</RESULT>", re.S | re.IGNORECASE)
# 일정 고치기 — 미리 보기의 [저장](제목 · 장소)과 끌어 옮기기(시각 — 끝만 바꾸는 크기 조절도 이 길로 보낸다 · SOURCES.md). 다 GET 이고 답은 JSONP 다
SAVE_PREV_PATH = "/(agSavePrevMe)?openagent"
MOVE_PATH = "/(agSetEventDate)?OpenAgent"
AMP_TOKEN = "1qazxsw21qazxsw2"      # 미리 보기 저장이 「&」 를 바꿔 싣는 글자 — 화면 그대로
LANG = "kor"
ALL_DAY_RULE = "ALLDAY"             # 빠른 등록의 RRULE — 하루 종일이면 이 값과 시각 없는 날짜를 싣는다
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
                              r"createdocument|deletedocument|saveoptions|agSavePrev|agSaveAttend|agSetEventDate|agNotice|"
                              r"agDelSelect|agDelBefor|\(wEvent|agUpdate", re.IGNORECASE)
# 등록 화면이 꼭 든 칸 — 잰 저장 몸통의 「값이 찬 칸」 가운데 우리가 덮는 것. 하나라도 없으면 화면의 꼴이 바뀐 것이다
FORM_NEEDS = ("Form", "Subject", "Description", "StartDate", "EndDate", "CalendarID", "EventArea", "visibility",
              "callback", "Editors")
FORM_VALUE = "Event"
VISIBILITY = "public"               # 폼이 비워 둔 공개 범위 — 사람이 넣은 판의 값
PRIVATE = "private"                 # 등록 화면의 「비공개」 단추 값
CALLBACK_NEW = "new"
# 참석자 · 참조 칸 — 비워 보낸다(남에게 알림이 안 가게). 손님 수 칸(`…AadditionalGuests`)은 폼의 값 그대로다
GUEST_FIELDS = re.compile(r"^(att|ref)(?!AadditionalGuests$)", re.IGNORECASE)
STAMP_FORM = ep_command.STAMP_FORM  # 등록의 StartDate · EndDate · `kst` 가 받는 꼴(서울 벽시계 — 회의실 손과 한 벌)
STAMP_ROW = "%Y-%m-%d %H:%M:%S"     # 일정 줄의 start · end
RESPONSE_PENDING = "needsAction"    # 참석 답을 아직 안 한 초대(철자 그대로 — `attRsponseStatus`)
MEETING = "meeting"                 # 줄의 eventtype(소문자로 견준다)
TRUE_WORDS = ("true", "1", "y", "yes")

# 넣기의 끝 — 다시 읽어 그 일정이 섰나. clashed 는 확인 뒤 새 겹침이 생겨 안 넣은 것이다
ADDED, ALREADY, UNSURE, CLASHED = "added", "already", "unsure", "clashed"
# 지우기의 끝 — 다시 읽어 그 일정이 사라졌나. `UNSURE` 는 넣기와 같은 값이다
DELETED, GONE, CHANGED = "deleted", "gone", "changed"
EDITED = "edited"                   # 고치기의 끝 — 다시 읽어 바꾼 값이 섰다(gone · changed · unsure 는 지우기와 같은 뜻)
# 지우지 않는 까닭(`Event.keep_reason`) — 쓰는 사람이 손수 든 단건만 지운다
KEEP_INVITE, KEEP_MEETING, KEEP_REPEAT, KEEP_LOCKED = "invite", "meeting", "repeat", "locked"
KEEP_ALL_DAY = "all_day"            # 하루 종일 줄의 시각 옮기기 — 지우기 · 제목 · 장소 고치기는 받는다(2026-11-19 회사에서 잼)
KEEP_GUESTS = "guests"              # 한 건 읽기에 참석자 · 참조자가 든 줄 — 고치면 그분들께 알림이 갈 수 있다(고치기만 본다)
KEEP_SHARED = "shared"              # 공유받은 일정함의 줄 — 읽기만 한다
KEEP_NO_DOC = "no_doc"              # 일정 줄에 문서 열쇠가 없어 한 건을 못 읽었다 — 참석자를 몰라 고치지 않는다(고칠 판만 본다)


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


def clock_span(a: datetime, b: datetime) -> str:
    """두 시각의 서울 벽시계 「HH:MM–HH:MM」."""
    return f"{a.astimezone(KST):%H:%M}–{b.astimezone(KST):%H:%M}"


def kst(text: str) -> datetime:
    """서울 벽시계 ``YYYY-MM-DD HH:MM`` → 시간대가 붙은 UTC. 꼴이 아니면 ``CalendarConfigError`` — 말은 ``ep_command.stamp_of`` 의 것이다."""
    try:
        return ep_command.stamp_of(text).astimezone(timezone.utc)
    except ep_command.Stop as exc:
        raise CalendarConfigError(str(exc)) from exc


def kst_day(t: datetime) -> date:
    """시각의 서울 날짜."""
    return _aware(t).astimezone(KST).date()


def _aware(t: datetime) -> datetime:
    """시간대가 붙은 시각만 받는다 — 없으면 CalendarConfigError."""
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
        """공유받은 일정함인가 — 내 일정함의 갈래가 아니다."""
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
    unid: str = ""                     # 그 일정 문서의 열쇠(32 자리 16진) — 줄의 `url` 에서 뽑는다. 한 건 읽기 · 고치기가 쓴다
    important: bool = False            # 줄의 Importance — 「중요」 표시
    # 초대한 사람(줄의 attOwner)이 쓰는 사람이 아니다 — 받은 초대. 내가 든 일정은 빈 글자로 온다. 칸이 없는 줄(공유 · 찾기)은 None(모른다)
    invited: bool | None = None

    @property
    def day(self) -> date:
        """일정이 시작하는 서울 날짜."""
        return kst_day(self.start)

    @property
    def keep_reason(self) -> str:
        """지우지 않는 까닭 — 빈 글자면 지워도 된다(쓰는 사람이 손수 든 단건). 갈래마다의 까닭은 ``references/DESIGN.md``
        「지우지 않는 줄」이 든다."""
        if self.calendar:
            return KEEP_SHARED
        # 응답 칸은 받은 초대에만 서지 않는다 — 내가 든 일정도 미리 보기 [저장] 뒤 accepted 로 선다(2026-11-19 잼). 초대한 사람을 알면 그것으로
        # 가르고, 모르면(칸이 없는 줄) 응답이 찬 줄을 초대로 둔다
        if self.invited or (self.invited is None and self.response):
            return KEEP_INVITE
        if self.meeting:
            return KEEP_MEETING
        if self.repeat:
            return KEEP_REPEAT
        if not self.editable:
            return KEEP_LOCKED
        return ""

    def overlaps(self, start: datetime, end: datetime) -> bool:
        """일정이 ``start`` ~ ``end`` 에 겹치나."""
        return self.start < end and start < self.end

    def when(self) -> str:
        """「10:00–11:00」 · 「하루 종일」 — 서울 시각."""
        if self.all_day:
            return "하루 종일"
        return clock_span(self.start, self.end)


@dataclass(frozen=True)
class Want:
    """회사 일정에 넣을 한 건 — 시각은 시간대가 붙은 것만(``kst`` 로 짓는다). ``note`` 는 설명 칸이다."""
    title: str
    start: datetime
    end: datetime
    note: str = ""
    place: str = ""                    # 장소 칸(``EventArea``)
    private: bool = False              # 비공개로 넣는다(``visibility=private``) — 다른 분께 제목이 안 보인다
    all_day: bool = False              # 하루 종일 — ``start`` 는 첫날 0 시, ``end`` 는 끝날 다음 날 0 시(서울)다(``whole_days`` 로 짓는다)
    important: bool = False            # 「중요」 표시(``Importance``)

    @property
    def day(self) -> date:
        """넣을 일정이 시작하는 서울 날짜."""
        return kst_day(self.start)

    @property
    def last_day(self) -> date:
        """그 일정이 드는 마지막 서울 날짜 — 하루 종일이면 끝(다음 날 0 시)의 앞날이다."""
        return kst_day(self.end - timedelta(microseconds=1)) if self.all_day else kst_day(self.end)

    def cleaned(self) -> Want:
        """회사 일정에 실제로 남는 꼴 — 보이지 않는 글자 · 줄바꿈을 걷고 상한에서 자른 제목 · 설명 · 장소. 확인에 이 꼴을 보인다."""
        return dataclasses.replace(self, title=clean_title(self.title), note=clean_note(self.note),
                                   place=_clean(self.place, PLACE_MOST))


def whole_days(first: date, last: date) -> tuple[datetime, datetime]:
    """하루 종일 일정의 (시작, 끝) — 첫날 서울 0 시부터 끝날 다음 날 0 시까지(UTC)."""
    if last < first:
        raise CalendarConfigError(f"하루 종일 일정의 끝날({last})이 첫날({first})보다 앞이다. 다음: --start <첫날> --end <끝날> 차례로 준다 — "
                                  "하루면 둘을 같게")
    lo = datetime(first.year, first.month, first.day, tzinfo=KST)
    hi = datetime(last.year, last.month, last.day, tzinfo=KST) + timedelta(days=1)
    return lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)


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
        """보인 일정 한 줄의 손잡이를 짓는다 — 그 줄의 열쇠 · 일정의 열쇠 · 지문 · 날."""
        return cls(ref=event_ref(e), ident=event_ident(e), mark=event_mark(e), day=e.day, shared=bool(e.calendar))

    @property
    def handle(self) -> str:
        """손잡이를 대화를 건널 글 한 줄로 쓴다."""
        return f"{self.ref}.{self.ident}.{self.mark}.{self.day.isoformat()}"

    @classmethod
    def parse(cls, text: str) -> Seen:
        """글 한 줄을 손잡이로 되읽는다 — 꼴이 아니면 CalendarConfigError."""
        m = cls._HANDLE.match((text or "").strip())
        if not m:
            raise CalendarConfigError("일정 손잡이의 꼴이 아니다. 다음: show 로 그날을 읽어 그 줄의 handle 을 손대지 않고 준다")
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
    """일정 한 줄의 날것 열쇠 — 일정 열쇠와 시작 시각(반복의 날마다 갈린다)."""
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
    """글을 회사 일정에 남는 꼴로 — 보이지 않는 글자를 걷고 빈칸을 하나로, ``most`` 에서 자른다."""
    text = "".join(ch for ch in unicodedata.normalize("NFC", text or "") if unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()[:most]


def clean_title(text: str) -> str:
    """제목 — 보이지 않는 글자 · 줄바꿈을 걷고 ``TITLE_MOST`` 에서 자른다. 회사 일정에 남는 글이다."""
    return _clean(text, TITLE_MOST)


def clean_note(text: str) -> str:
    """설명 칸 — 제목과 같은 거름에 ``NOTE_MOST`` 상한."""
    return _clean(text, NOTE_MOST)


def same_event(e: Event, w: Want) -> bool:
    """같은 일정인가 — 제목 · 시작 · 끝이 같다. 하루 종일이면 제목 · 하루 종일 · 서울의 첫날이 같다(하루 종일 줄의 시각 꼴은
    날짜만 믿는다). 넣기 앞에 이미 있나 · 넣기 뒤에 섰나를 이것 하나로 본다."""
    if clean_title(e.title) != clean_title(w.title):
        return False
    if w.all_day or e.all_day:
        return e.all_day == w.all_day and e.day == w.day and kst_day(e.end - timedelta(seconds=1)) == w.last_day
    return e.start == w.start and e.end == w.end


@dataclass(frozen=True)
class Person:
    """한 건 읽기의 참석자 · 참조자 한 사람 — 이름 · 메일 · 응답(``accepted`` · ``declined`` · ``tentative`` · ``needsAction``) · 한마디."""
    name: str
    email: str = ""
    response: str = ""
    comment: str = ""


@dataclass(frozen=True)
class Detail:
    """일정 한 건의 미리 보기 — 줄에 안 오는 칸. ``organizer`` 는 받은 초대면 연 사람(내가 든 일정이면 빈 글자)."""
    unid: str
    title: str
    place: str
    note: str
    attendees: tuple
    references: tuple
    meeting_url: str
    organizer: str
    modified: str
    visibility: str

    counted: bool = True               # 참석자 · 참조자 수 칸이 둘 다 「0」 으로 읽혔다 — 아니면 사람이 없다고 믿지 않는다

    @property
    def guests(self) -> bool:
        """참석자 · 참조자가 든다(또는 수 칸을 못 읽어 모른다) — 고치면 그분들께 알림이 갈 수 있다. 모르면 든 것으로 둔다."""
        return bool(self.attendees or self.references) or not self.counted


@dataclass(frozen=True)
class Change:
    """한 건 고치기에서 바꿀 것 — 안 바꾸는 칸은 None. 시각은 시간대가 붙은 것만."""
    title: str | None = None
    place: str | None = None
    start: datetime | None = None
    end: datetime | None = None

    def cleaned(self) -> Change:
        """고칠 칸을 회사 일정에 남는 꼴로 — 준 칸만 다듬는다."""
        return dataclasses.replace(self, title=None if self.title is None else clean_title(self.title),
                                   place=None if self.place is None else _clean(self.place, PLACE_MOST))

    @property
    def moves(self) -> bool:
        """시각을 옮기는 고침인가 — 시작이나 끝을 준다."""
        return self.start is not None or self.end is not None


@dataclass(frozen=True)
class Edited:
    """고치기의 끝 — ``state`` 는 edited(다시 읽어 바꾼 값이 섰다) · gone · changed(보인 뒤 바뀌었다 · 안 고쳤다) · unsure(불렀는데
    다시 읽은 값이 바라던 것과 다르다 — ``event`` 가 지금의 그 줄이다)."""
    state: str
    event: Event | None = None
    place: str | None = None
    detail: str = ""
    notice: bool = False               # 일정 앱이 「참석자께 알릴까」를 물었다(알림은 안 보냈다)
