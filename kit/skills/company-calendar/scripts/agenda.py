"""사내 일정 앱(HCL Domino 웹 일정)의 내 일정함을 읽는 손과, 일정을 바꾸는 이름 붙은 손 셋(``register`` · ``edit`` · ``delete``) — 표준
라이브러리와 형제 스킬 ep-login 의 ``ep_session``(세션 파일 → 쿠키 통, 스킬 홈에 나란히 깔린 ``../../ep-login/scripts/``)만 쓰는
파일 하나. 막는 까닭과 바꾸는 손의 경계는 ``references/DESIGN.md``, 일정 앱의 주소와 꼴은 ``references/SOURCES.md`` 가 든다.

⚠ ``register`` · ``edit`` · ``delete`` 는 남이 보는 회사 일정을 바꾸고 지운 일정은 되돌릴 손이 없다 — 사람이 그 한 건을 분명히 고른
뒤에만 부른다. 읽는 손은 안 바꾸는 것을 잰 주소 밖을 서버에 닿기 전에 ``ChangeRefused`` 로 막는다(이 앱은 편집 화면 · 고치기 · 지우기도
GET 이다).

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
        done = agenda.edit(url, cookies_file, agenda.Seen.parse(handle), agenda.Change(title="새 제목", place="본관 201"))   # ⚠
        done.state                                      # edited · gone · changed · unsure
        r.detail(e.unid)                                # 한 건 — 장소 · 설명 · 참석자와 응답 · Teams 링크(안 바꾼다)
        r.search(place="지하강당", first=…, last=…) · r.search_text("교육") · r.holidays(first, last)

    ``Reader.from_env()`` 는 환경변수로 세운다 — ``CALENDAR_URL`` · ``MAILBOX_COOKIES`` 둘 다 꼭 준다. 쿠키 파일의 자리는 이 파일이
    정하지 않는다 — 세션을 남기는 손이 정하고, 부르는 쪽이 그 경로를 넘긴다.

무엇을 내나
    시각은 다 시간대가 붙은 UTC 이고, 보이기(``Event.when``)는 서울이다. 시각을 못 읽은 줄은 버리고 ``Reader.unread`` 에 일정함마다
    그 수를 쌓는다. ``Seen`` 은 사람에게 보인 일정 한 줄의 손잡이다 — 그 줄의
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
import ep_command  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다
import ep_session  # noqa: E402

log = logging.getLogger(__name__)

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
    """서울 벽시계 ``YYYY-MM-DD HH:MM`` → 시간대가 붙은 UTC. 꼴이 아니면 ``CalendarConfigError`` — 말은 ``ep_command.stamp_of`` 의 것이다."""
    try:
        return ep_command.stamp_of(text).astimezone(timezone.utc)
    except ep_command.Stop as exc:
        raise CalendarConfigError(str(exc)) from exc


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
    unid: str = ""                     # 그 일정 문서의 열쇠(32 자리 16진) — 줄의 `url` 에서 뽑는다. 한 건 읽기 · 고치기가 쓴다
    important: bool = False            # 줄의 Importance — 「중요」 표시
    # 초대한 사람(줄의 attOwner)이 쓰는 사람이 아니다 — 받은 초대. 내가 든 일정은 빈 글자로 온다. 칸이 없는 줄(공유 · 찾기)은 None(모른다)
    invited: bool | None = None

    @property
    def day(self) -> date:
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
    place: str = ""                    # 장소 칸(``EventArea``)
    private: bool = False              # 비공개로 넣는다(``visibility=private``) — 다른 분께 제목이 안 보인다
    all_day: bool = False              # 하루 종일 — ``start`` 는 첫날 0 시, ``end`` 는 끝날 다음 날 0 시(서울)다(``whole_days`` 로 짓는다)
    important: bool = False            # 「중요」 표시(``Importance``)

    @property
    def day(self) -> date:
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
        return cls(ref=event_ref(e), ident=event_ident(e), mark=event_mark(e), day=e.day, shared=bool(e.calendar))

    @property
    def handle(self) -> str:
        return f"{self.ref}.{self.ident}.{self.mark}.{self.day.isoformat()}"

    @classmethod
    def parse(cls, text: str) -> Seen:
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
    """같은 일정인가 — 제목 · 시작 · 끝이 같다. 하루 종일이면 제목 · 하루 종일 · 서울의 첫날이 같다(하루 종일 줄의 시각 꼴은
    날짜만 믿는다). 넣기 앞에 이미 있나 · 넣기 뒤에 섰나를 이것 하나로 본다."""
    if clean_title(e.title) != clean_title(w.title):
        return False
    if w.all_day or e.all_day:
        return e.all_day == w.all_day and e.day == w.day and kst_day(e.end - timedelta(seconds=1)) == w.last_day
    return e.start == w.start and e.end == w.end


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
        # 시각을 못 읽어 버린 줄 — (일정함 이름 · 내 기본 일정함은 빈 글자, 줄 수)를 묻는 차례로 쌓는다. 버린 줄은 목록에 안 서니,
        # 부르는 쪽이 「그 일정함에 안 보인 일정이 있다」를 알릴 길은 이것뿐이다
        self.unread: list[tuple[str, int]] = []
        db = re.escape(self.db_path)
        day = r"\d{4}-\d{2}-\d{2}"
        # 읽는 손이 물을 수 있는 주소 꼴 — 닫힌 목록이라 새 꼴은 안 바꾸는 것을 잰 뒤 여기에 더해야 묻는다
        self._read_only = (
            re.compile(rf"^{db}{re.escape(LIST_PATH)}$"),
            re.compile(rf"^{db}{re.escape(EVENTS_PATH)}&callback={CALLBACK}&calendarId=[\w%.-]+&username=[\w%.+-]+"
                       rf"&start={day}&end={day}&kind={KIND_MINE}$"),
        )
        # 한 건 미리 보기 · 상세검색 · 본문 찾기 — 안 바꾸는 것을 회사에서 쟀다(SOURCES.md)
        self._read_only += (
            re.compile(rf"^{db}/vweventprev/[0-9A-F]{{32}}\?opendocument$"),
            re.compile(rf"^{db}{re.escape(SEARCH_PATH)}&" + "&".join(rf"{k}=[^&]*" for k in SEARCH_KEYS) + "$"),
            re.compile(rf"^{db}{re.escape(FT_SEARCH_PATH)}&" + "&".join(rf"{k}=[^&]*" for k in FT_SEARCH_KEYS) + "$"),
        )
        code = self.db_path.strip("/").split("/", 1)[0]
        self._public = (f"/{code}/cal/calpublic.nsf/vwHolidays" if re.fullmatch(r"\w+", code) else "")
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

    def _get_public(self, query: str) -> tuple[bytes, str]:
        """공용 일정 DB(같은 서버 · 같은 회사 코드)의 공휴일 보기 한 꼴만 — 꼴 밖이면 묻지 않고 ``ChangeRefused``."""
        full = f"{self._public}?searchView&query={urllib.parse.quote(query, safe='')}"
        if not self._public or not re.fullmatch(r"\[startDate\]>=\d{4}-\d{2}-\d{2} AND \[startDate\]<=\d{4}-\d{2}-\d{2}", query):
            raise ChangeRefused("공휴일 보기로 잰 주소 꼴이 아니라 묻지 않는다")
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
        body = _jsonp(self._text(data, kind))
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
        if skipped:
            self.unread.append((book.name or (_person(book.owner) if book.shared else ""), skipped))
        log.info("일정: %d줄(반복 %d · 단건 %d) · 못 읽은 줄 %d", len(events), len(body.get("data") or ()),
                 len(body.get("data2") or ()), skipped)
        return events

    # ── 한 건 · 찾기 · 공휴일 ──
    def detail(self, unid: str) -> Detail:
        """내 일정함의 일정 한 건 — 미리 보기 문서(``vweventprev/<unid>?opendocument``)의 장소 · 설명 · 참석자와 응답 · 참조자 · Teams
        링크 · 고친 시각. 문서 보기라 안 바꾼다(편집 화면 ``?editdocument`` 은 짓지 않는다)."""
        unid = (unid or "").strip().upper()
        if not re.fullmatch(r"[0-9A-F]{32}", unid):
            raise CalendarConfigError("일정 문서 열쇠의 꼴이 아니다 — show 가 낸 줄의 handle 을 그대로 준다")
        data, kind = self._get(DETAIL_PATH.format(unid=unid))
        return parse_detail(self._text(data, kind), unid)

    def search(self, *, title: str = "", place: str = "", note: str = "", attendee: str = "", first: date, last: date,
               book: Book | None = None) -> list[Event]:
        """상세검색 — 기간(서울 날짜 · 둘 다 든다) 안에서 제목 · 장소 · 설명 · 참석자 이름에 그 글자가 든 일정(조건은 다 함께 걸린다).
        ⚠ 답의 줄은 끝이 시작과 같게 온다 — 끝 시각은 안 믿는다(부르는 쪽이 한 건 읽기 · show 로 본다)."""
        book = book or self.book()
        q = urllib.parse.urlencode({"callback": CALLBACK, "username": book.owner, "calendarId": book.calendar_id, "textColor": "",
                                    "colorId": "", "color": "", "eventTitle": title, "from": f"{first:%Y.%m.%d}",
                                    "to": f"{last:%Y.%m.%d}", "desc": note, "eventArea": place, "attend": attendee, "file": "false"})
        return self._found(self._get(f"{SEARCH_PATH}&{q}"), book)

    def search_text(self, text: str, book: Book | None = None) -> list[Event]:
        """본문 전체 찾기 — 제목 · 설명 · 장소 어디든 그 낱말이 든 일정(기간 없이 지난 해까지). 줄의 끝 시각이 온다."""
        book = book or self.book()
        q = urllib.parse.urlencode({"callback": CALLBACK, "calendarId": book.calendar_id, "username": book.owner, "searchStr": text,
                                    "textColor": "", "colorId": "", "color": ""})
        return self._found(self._get(f"{FT_SEARCH_PATH}&{q}"), book)

    def _found(self, got: tuple[bytes, str], book: Book) -> list[Event]:
        body = _jsonp(self._text(*got))
        out, skipped = [], 0
        for row in body.get("data") or ():
            e = parse_row(row, book.owner) if isinstance(row, dict) else None
            if e is None:
                skipped += 1
                continue
            out.append(e)
        if skipped:
            self.unread.append(("", skipped))
        out.sort(key=lambda e: (e.start, e.title))
        log.info("일정 찾기: %d줄 · 못 읽은 줄 %d", len(out), skipped)
        return out

    def holidays(self, first: date, last: date) -> dict[date, str]:
        """공휴일 — 서울 날짜 ``first`` ~ ``last``(둘 다 든다)의 {날: 이름}. 일정 앱의 공용 일정 DB(``vwHolidays``)가 든다."""
        data, kind = self._get_public(f"[startDate]>={first.isoformat()} AND [startDate]<={last.isoformat()}")
        m = HOLIDAY_RESULT.search(self._text(data, kind))
        if not m:
            raise CalendarError("공휴일 대신 <RESULT> 가 없는 답이 왔다")
        try:
            rows = json.loads(m.group(1).replace("\n", " "))
        except ValueError:
            raise CalendarError("공휴일 목록을 못 읽었다") from None
        out: dict[date, str] = {}
        for r in rows if isinstance(rows, list) else ():
            try:
                d = date.fromisoformat(str(r.get("start") or "")) if isinstance(r, dict) else None
            except ValueError:
                d = None
            if d is None or not first <= d <= last:
                continue
            name = str(r.get("title") or "").strip() or "공휴일"
            out[d] = name if d not in out or name in out[d] else f"{out[d]} · {name}"
        return out

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


def _jsonp(text: str) -> dict:
    """``<CALLBACK>( … )`` 의 몸통 — 꼴이 아니면 끊긴 세션(SSO HTML 이 온다)."""
    m = re.fullmatch(rf"\s*{CALLBACK}\((.*)\)\s*;?\s*", text, re.S)
    if not m:
        raise SessionExpired("JSONP 가 아닌 답이 왔다 — 세션이 끊긴 것으로 읽는다")
    try:
        body = json.loads(m.group(1))
    except ValueError:
        raise CalendarError("JSONP 의 몸통을 못 읽었다") from None
    if not isinstance(body, dict):
        raise CalendarError("JSONP 의 몸통이 객체가 아니다")
    return body


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


_DOC_FIELD = re.compile(r'^\s*,?\s*"(\w+)"\s*:\s*"((?:[^"\\]|\\.)*)"', re.M)
# 문서 칸 목록 표 — 첫 칸이 값, 셋째 칸이 칸 이름(``<tt>Subject</tt>`` 꼴도)
_DUMP_ROW = re.compile(r"<tr[^>]*>\s*<td[^>]*>((?:(?!</td>|<tr).)*)</td>\s*<td[^>]*>(?:(?!</td>|<tr).)*</td>\s*<td[^>]*>\s*(?:<tt>)?"
                       r"\s*(\w+)\s*(?:</tt>)?\s*</td>\s*</tr>", re.S | re.IGNORECASE)


def _plain(fragment: str) -> str:
    """문서 칸의 HTML 조각 → 글 — 줄바꿈 표시는 줄바꿈으로, 태그는 걷고 엔티티를 푼다."""
    text = re.sub(r"(?i)<br\s*/?>|&lt;br&gt;", "\n", fragment or "")
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _people(doc: Mapping[str, str], kind: str) -> tuple:
    """``EventDoc`` 의 쉼표로 이은 칸들에서 사람들 — 이름 칸에 든 사람마다 한 줄. 칸 수가 이름 수와 다르면 그 칸은 비운다."""
    names = [n.strip() for n in doc.get(f"{kind}DisplayName", "").split(",")]
    if not any(names):
        return ()
    emails = [n.strip() for n in doc.get(f"{kind}Email", "").split(",")]
    said = [n.strip() for n in doc.get(f"{kind}RsponseStatus", "").split(",")]
    notes = [n.strip() for n in doc.get(f"{kind}Comment", "").split(",")]

    def at(xs, i):
        return xs[i] if len(xs) == len(names) else ""
    return tuple(Person(n, at(emails, i), at(said, i), _plain(at(notes, i))) for i, n in enumerate(names) if n)


def parse_detail(page: str, unid: str = "") -> Detail:
    """미리 보기 문서의 칸 — 스크립트 ``EventDoc`` 의 칸과 칸 목록 표의 ``Subject`` · ``EventArea`` · ``Description``. ``EventDoc``
    가 없으면 끊긴 세션이다(SSO HTML 이 온다)."""
    m = re.search(r"var\s+EventDoc\s*=\s*\{(.*?)\n\s*\}\s*;", page, re.S)
    if not m:
        raise SessionExpired("일정 한 건 대신 EventDoc 이 없는 답이 왔다 — 세션이 끊긴 것으로 읽는다")
    doc: dict[str, str] = {}
    for k, v in _DOC_FIELD.findall(m.group(1)):
        doc.setdefault(k, v.replace('\\"', '"'))
    dump: dict[str, str] = {}
    for value, name in _DUMP_ROW.findall(page):
        dump.setdefault(name, value)
    return Detail(unid=unid, title=_plain(dump.get("Subject", "")), place=_plain(dump.get("EventArea", "")),
                  note=_plain(dump.get("Description", "")), attendees=_people(doc, "att"), references=_people(doc, "ref"),
                  meeting_url=doc.get("PcMeetingUrl", "").strip(), organizer=_person(doc.get("attowner", "")),
                  modified=doc.get("modified", "").strip(), visibility=doc.get("visibility", "").strip(),
                  counted=all(doc.get(f"{k}AadditionalGuests", "").strip() == "0" for k in ("att", "ref")))


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


def _invited(row: Mapping[str, Any], me: str) -> bool | None:
    """받은 초대인가 — 줄의 ``attOwner``(초대한 사람의 Notes 이름)가 차 있고 쓰는 사람이 아니면 참, 비었으면 거짓, 칸이 없거나 쓰는
    사람을 모르면 None."""
    if "attOwner" not in row or not me:
        return None
    who = str(row.get("attOwner") or "").strip()
    return bool(who) and who.casefold() != me.strip().casefold()


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
                 private=str(row.get("visibility") or "").strip().lower() == PRIVATE,
                 unid=(UNID.search(str(row.get("url") or "")) or [None, ""])[1].upper(), important=_truthy(row.get("Importance")),
                 invited=_invited(row, me))


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


def _side_events(r: Reader, first: date, last: date) -> list[Event]:
    """기본 밖 내 일정함(Teams 따위)의 ``first`` ~ ``last`` 일정 — 안 읽히는 일정함은 건너뛴다(끊긴 세션은 올린다)."""
    out: list[Event] = []
    for b in r.side_books():
        try:
            out += r.events(first, last, b)
        except SessionExpired:
            raise
        except CalendarError as exc:
            log.info("일정 넣기 — 기본 밖 일정함 하나를 못 읽어 그 일정함 없이 겹침을 가린다(%s)", type(exc).__name__)
    return out


def _span_of(want: Want) -> tuple[date, date]:
    return _span(want.day, datetime.combine(want.last_day, datetime.min.time(), KST) if want.all_day else want.end)


def register(url: str, cookies_file: pathlib.Path | str, want: Want, *, timeout: float = TIMEOUT_SECONDS,
             reader: Reader | None = None, shown_clash: Iterable[str] | None = None) -> Added:
    """⚠ 회사 일정을 바꾼다 — 내 기본 일정함에 한 건을 넣고 ``Added`` 를 낸다. 사람이 그 한 건을 확인한 뒤에만 부른다.

    ``shown_clash`` 는 확인에 보인 겹침의 ``event_ref`` 들이다 — 확인은 내 일정함 전부(기본 · Teams)의 겹침을 보이므로, 그 밖의
    일정이 그 시각에 어느 내 일정함에든 생겼으면 ``clashed`` 로 안 넣는다. 기본 밖 일정함이 안 읽히면(세션 끊김이 아닌 한) 그
    일정함 없이 가린다 — 확인도 그 일정함을 못 읽었다고 알렸다. 등록 화면에 잰 칸이 없으면 ``FormChanged``(안 넣음). 등록 화면을
    열기 전에 진 것(세션 · 서버)은 아무것도 안 바꾼 채 올린다.
    """
    want = want.cleaned()
    if not want.title or _aware(want.end) <= _aware(want.start):
        raise CalendarConfigError("넣을 일정의 제목 · 시각이 비었거나 끝이 시작보다 앞이다")
    r = reader or Reader(url, cookies_file, timeout=timeout)
    book = r.book()
    first, last = _span_of(want)
    before = r.events(first, last, book)
    hit = next((e for e in before if same_event(e, want)), None)
    if hit is not None:
        log.info("일정 넣기 — 같은 일정이 이미 있어 넣지 않았다")
        return Added(ALREADY, hit)
    if shown_clash is not None:
        around = before + _side_events(r, first, last)
        fresh = {event_ref(e) for e in around if e.overlaps(want.start, want.end)} - set(shown_clash)
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
    if want.all_day:     # 하루 종일 — 화면처럼 RRULE=ALLDAY 와 시각 없는 첫날 · 끝날(끝날도 든다)
        if "RRULE" not in form.fields:
            raise FormChanged("등록 화면에 RRULE 칸이 없다 — 하루 종일로 넣지 않았다")
        start_text, end_text = want.day.isoformat(), want.last_day.isoformat()
        fields["RRULE"] = ALL_DAY_RULE
    else:
        start_text, end_text = (want.start.astimezone(KST).strftime(STAMP_FORM), want.end.astimezone(KST).strftime(STAMP_FORM))
    if want.important:
        if "Importance" not in form.fields:
            raise FormChanged("등록 화면에 Importance 칸이 없다 — 중요로 넣지 않았다")
        fields["Importance"] = "true"
    fields.update(CalendarID=book.calendar_id, Subject=want.title, Description=want.note, StartDate=start_text, EndDate=end_text,
                  EventArea=want.place or form.fields.get("EventArea", ""),
                  visibility=PRIVATE if want.private else (form.fields.get("visibility") or VISIBILITY),
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


# ── 고치기 — 일정을 바꾸는 손 하나 ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Change:
    """한 건 고치기에서 바꿀 것 — 안 바꾸는 칸은 None. 시각은 시간대가 붙은 것만."""
    title: str | None = None
    place: str | None = None
    start: datetime | None = None
    end: datetime | None = None

    def cleaned(self) -> Change:
        return dataclasses.replace(self, title=None if self.title is None else clean_title(self.title),
                                   place=None if self.place is None else _clean(self.place, PLACE_MOST))

    @property
    def moves(self) -> bool:
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


def locate(r: Reader, book: Book, seen: Seen) -> tuple[str, Event | None]:
    """보인 줄을 지금 읽어 — (끝 낱말, 지금 그 줄). 끝 낱말은 ""(그대로) · ``CHANGED``(옮겨졌거나 제목 · 시작 · 끝이 다르다) ·
    ``GONE``(그날에 없다). 고치기 · 지우기와 그 미리 보기가 이것 하나로 본다."""
    now = r.events(seen.day, seen.day + timedelta(days=1), book)
    hit = next((e for e in now if event_ref(e) == seen.ref), None)
    if hit is None:
        moved = next((e for e in now if event_ident(e) == seen.ident and e.day == seen.day), None)
        return (CHANGED, moved) if moved is not None else (GONE, None)
    return ("", hit) if event_mark(hit) == seen.mark else (CHANGED, hit)


def _agent(r: Reader, path: str, params: list[tuple[str, str]]) -> dict:
    """바꾸는 에이전트 한 번 — GET 에 JSONP 로 답한다. 답을 못 읽으면 빈 dict(끝은 다시 읽어 정한다)."""
    data, kind = r._open(f"{r.url}{path}&{urllib.parse.urlencode([('callback', CALLBACK), *params])}")
    try:
        return _jsonp(r._text(data, kind))
    except CalendarError:
        return {}


def edit(url: str, cookies_file: pathlib.Path | str, target: Event | Seen, change: Change, *, timeout: float = TIMEOUT_SECONDS,
         reader: Reader | None = None) -> Edited:
    """⚠ 회사 일정을 바꾼다 — 내 일정함의 한 줄의 제목 · 장소 · 시각을 고친다. 사람이 그 한 건과 바뀔 값을 확인한 뒤에만 부른다.

    지우기와 같은 경계 — 보인 줄이 옮겨졌거나 제목 · 시작 · 끝이 다르면 ``changed``, 그날에 없으면 ``gone``(둘 다 안 부른다), 쓰는
    사람이 손수 든 단건이 아니면 ``ChangeRefused``. 더해 한 건 읽기에 참석자 · 참조자가 들면(고치면 알림이 갈 수 있다) ``ChangeRefused``
    (``guests``), 하루 종일 일정의 시각은 안 옮긴다(``all_day``). 제목 · 장소는 미리 보기의 [저장](``agSavePrevMe``), 시각은 끌어
    옮기기(``agSetEventDate``)와 같은 요청이다. 답은 성공을 못 가려 다시 읽은 줄 · 한 건이 끝을 정한다."""
    change = change.cleaned()
    seen = target if isinstance(target, Seen) else Seen.of(target)
    if seen.shared:
        raise ChangeRefused("공유받은 일정함의 줄이라 고치지 않는다", KEEP_SHARED)
    r = reader or Reader(url, cookies_file, timeout=timeout)
    book = r.book()
    state, hit = locate(r, book, seen)
    if state:
        return Edited(state, hit)
    if hit.keep_reason:
        raise ChangeRefused(f"손수 든 단건이 아니라 고치지 않는다({hit.keep_reason})", hit.keep_reason)
    if hit.all_day and change.moves:
        raise ChangeRefused("하루 종일 일정의 시각은 옮기지 않는다", KEEP_ALL_DAY)
    if not hit.unid:
        raise CalendarError("일정 줄에 문서 열쇠가 없다 — 줄의 꼴이 잰 것과 다르다 · 고치지 않았다")
    doc = r.detail(hit.unid)
    if doc.guests:
        raise ChangeRefused("참석자 · 참조자가 든 일정이라 고치지 않는다", KEEP_GUESTS)
    start, end = hit.start, hit.end
    if change.moves:     # 시작만 주면 길이를 지켜 옮긴다(화면의 끌어 옮기기와 같다) · 끝만 주면 끝만 바꾼다
        start = change.start or hit.start
        end = change.end or (start + (hit.end - hit.start))
        if _aware(end) <= _aware(start):
            raise CalendarConfigError("옮길 끝이 시작보다 앞이다")
    title = clean_title(hit.title) if change.title is None else change.title
    place = doc.place if change.place is None else change.place
    if not title:
        raise CalendarConfigError("제목을 비울 수는 없다")
    notice, detail = False, ""
    try:
        if title != clean_title(hit.title) or place != doc.place:
            got = _agent(r, SAVE_PREV_PATH, [
                ("calendarId", book.calendar_id), ("eventId", hit.event_id), ("subject", title.replace("&", AMP_TOKEN)),
                ("eventarea", place.replace("&", AMP_TOKEN)), ("updatetype", "current"), ("cdate", ""),
                ("attOwner", book.owner), ("owner", book.owner), ("username", book.owner), ("MailTitle", ""),
                ("attRsponseMe", ""), ("attComment", ""), ("attAadditionalGuests", "0")])
            notice = notice or str(got.get("notice", "")).lower() == "true"
        if change.moves and (start != hit.start or end != hit.end):
            got = _agent(r, MOVE_PATH, [
                ("lang", LANG), ("eventid", hit.event_id),
                ("drag_start", hit.start.astimezone(KST).strftime(STAMP_FORM)), ("drag_end", hit.end.astimezone(KST).strftime(STAMP_FORM)),
                ("event_start", start.astimezone(KST).strftime(STAMP_FORM)), ("event_end", end.astimezone(KST).strftime(STAMP_FORM)),
                ("eventowner", book.owner), ("username", book.owner)])
            notice = notice or str(got.get("notice", "")).lower() == "true"
    except CalendarError as exc:   # 요청이 도중에 졌다 — 서버가 받았는지 모른다. 다시 읽어 가린다
        detail = type(exc).__name__
    lo, hi = min(seen.day, kst_day(start)), max(seen.day, kst_day(end)) + timedelta(days=1)
    try:
        after = next((e for e in r.events(lo, hi, book) if e.event_id == hit.event_id), None)
        place_now = r.detail(after.unid).place if after is not None and after.unid else None
    except CalendarError as exc:
        log.warning("일정 고치기 — 다시 읽기가 졌다(%s) · 고쳤는지 모른다", type(exc).__name__)
        return Edited(UNSURE, None, None, type(exc).__name__, notice)
    ok = (after is not None and clean_title(after.title) == title and place_now == place
          and after.start == start and after.end == end)
    log.info("일정 고치기 — %s", "다시 읽어 섰다" if ok else "다시 읽은 값이 바라던 것과 다르다")
    return Edited(EDITED if ok else UNSURE, after, place_now, detail, notice)


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
    state, hit = locate(r, book, seen)
    if state:
        log.info("일정 지우기 — 보인 뒤 그 줄이 %s 지우지 않았다", "바뀌어" if state == CHANGED else "그날에 없어")
        return Removed(state, hit)
    if hit.keep_reason:
        raise ChangeRefused(f"손수 든 단건이 아니라 지우지 않는다({hit.keep_reason})", hit.keep_reason)
    if hit.response:     # 응답 칸이 찬 내 일정 — 참석자가 들었으면 지우기가 그분들께 알림이 될 수 있다. 한 건 읽기로 본다
        if not hit.unid or r.detail(hit.unid).guests:
            raise ChangeRefused("참석자 · 참조자가 든 일정이라 지우지 않는다", KEEP_GUESTS)
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
