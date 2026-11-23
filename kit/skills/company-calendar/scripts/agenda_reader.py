"""일정함을 읽는 손 — 읽기 전용으로 잰 주소만 묻는다. 바깥: 일정 앱(망)."""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

from agenda_shapes import (APP_URL, Book, CALLBACK, CHANGES_CALENDAR, CalendarConfigError, CalendarError, ChangeRefused,
                           DETAIL_PATH, Detail, EVENTS_PATH, Event, FT_SEARCH_KEYS, FT_SEARCH_PATH, HOLIDAY_RESULT, KINDS_SHARED,
                           KIND_MINE, KST, LIST_PATH, SEARCH_KEYS, SEARCH_PATH, SHARED_DB, SHARED_EVENTS_PATH, SHARED_HOST,
                           SessionExpired, SessionMissing, TIMEOUT_SECONDS, TYPE_DEFAULT, event_key)
from agenda_shapes import ep_session, log
from agenda_rows import _jsonp, _person, parse_detail, parse_rows


def labelled(rows: list[Event], book: Book) -> list[Event]:
    """기본 밖 일정함 · 공유받은 일정함의 줄에 그 일정함 이름(``calendar``)을 단다 — 내 기본 일정함의 줄은 그대로."""
    if not (book.shared or book.name):
        return rows
    return [dataclasses.replace(e, calendar=book.name or _person(book.owner)) for e in rows]


def distinct_events(rows: list[Event]) -> list[Event]:
    """같은 줄(``event_key`` — 일정 열쇠 · 시작)은 처음 것 하나만 — 반복 · 단건 두 배열에 같은 줄이 올 수 있다."""
    out: dict[str, Event] = {}
    for e in rows:
        out.setdefault(event_key(e), e)
    return list(out.values())


def read_each(books: list[Book], read) -> tuple[list[Event], list[tuple[Book, CalendarError]]]:
    """곁 일정함마다 ``read(일정함)`` 의 줄을 일정함 차례로 잇는다 — 끊긴 세션은 올리고, 못 읽은 일정함은 (일정함, 예외)로 모은다.
    한 일정함이 안 읽혀도 나머지는 낸다 — 못 읽은 것을 이름으로 알리는 것은 부르는 쪽이다."""
    got: list[Event] = []
    lost: list[tuple[Book, CalendarError]] = []
    for b in books:
        try:
            got += read(b)
        except SessionExpired:
            raise
        except CalendarError as exc:
            lost.append((b, exc))
    return got, lost


DAY_SHAPE = r"\d{4}-\d{2}-\d{2}"       # 주소에 싣는 날의 꼴
# 공유받은 일정함의 일정 — 그 일정함의 DB 아래 이 꼴 하나만 묻는다(서버는 ``Reader._shared_server`` 가 가린다)
READ_SHARED = re.compile(rf"^/[\w./-]+\.nsf{re.escape(SHARED_EVENTS_PATH)}&callback={CALLBACK}"
                         rf"&calendarId=[\w%.-]+&username=[\w%.+-]+&start={DAY_SHAPE}&end={DAY_SHAPE}"
                         rf"&kind=(?:{'|'.join(KINDS_SHARED)})$")


def read_only_shapes(db_path: str) -> tuple:
    """읽는 손이 내 일정 DB(``db_path``)에 물을 수 있는 주소 꼴 — 닫힌 목록이라 새 꼴은 안 바꾸는 것을 잰 뒤 여기에 더해야 묻는다.
    일정함 목록 · 일정 목록과, 안 바꾸는 것을 회사에서 잰(SOURCES.md) 한 건 미리 보기 · 상세검색 · 본문 찾기."""
    db = re.escape(db_path)
    return (
        re.compile(rf"^{db}{re.escape(LIST_PATH)}$"),
        re.compile(rf"^{db}{re.escape(EVENTS_PATH)}&callback={CALLBACK}&calendarId=[\w%.-]+&username=[\w%.+-]+"
                   rf"&start={DAY_SHAPE}&end={DAY_SHAPE}&kind={KIND_MINE}$"),
        re.compile(rf"^{db}/vweventprev/[0-9A-F]{{32}}\?opendocument$"),
        re.compile(rf"^{db}{re.escape(SEARCH_PATH)}&" + "&".join(rf"{k}=[^&]*" for k in SEARCH_KEYS) + "$"),
        re.compile(rf"^{db}{re.escape(FT_SEARCH_PATH)}&" + "&".join(rf"{k}=[^&]*" for k in FT_SEARCH_KEYS) + "$"),
    )


def public_view(db_path: str) -> str:
    """공용 일정 DB 의 공휴일 보기 자리 — 내 일정 DB 와 같은 회사 코드(경로의 첫 마디) 아래다. 코드가 낱말 꼴이 아니면 빈 글자(묻지
    않는다)."""
    code = db_path.strip("/").split("/", 1)[0]
    return f"/{code}/cal/calpublic.nsf/vwHolidays" if re.fullmatch(r"\w+", code) else ""


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
        self._read_only = read_only_shapes(self.db_path)
        self._public = public_view(self.db_path)

    @classmethod
    def from_env(cls) -> Reader:
        """환경변수로 세운다 — ``CALENDAR_URL`` · ``MAILBOX_COOKIES``(둘 다 꼭 준다 · 없으면 ``CalendarConfigError`` · ``SessionMissing``)."""
        url = os.environ.get("CALENDAR_URL", "").strip()
        if not url:
            raise CalendarConfigError("CALENDAR_URL 이 비어 있다 — 일정 앱 주소의 …/이름.nsf 까지 준다")
        return cls(url, os.environ.get("MAILBOX_COOKIES", "").strip())

    @property
    def url(self) -> str:
        """일정 앱 주소 — 서버와 DB 자리를 잇는다."""
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
        if not self._public or not re.fullmatch(rf"\[startDate\]>={DAY_SHAPE} AND \[startDate\]<={DAY_SHAPE}", query):
            raise ChangeRefused("공휴일 보기로 잰 주소 꼴이 아니라 묻지 않는다")
        return self._open(self.server + full)

    def _get_shared(self, server: str, path: str) -> tuple[bytes, str]:
        """공유받은 일정함의 읽기 GET — 그 일정함의 서버 · DB 아래 잰 꼴 하나만. 꼴 밖이면 묻지 않고 ``ChangeRefused``."""
        if CHANGES_CALENDAR.search(path) or not READ_SHARED.match(path):
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
        """답의 바이트를 글로 — 답이 댄 문자셋으로, 모르는 문자셋이면 UTF-8."""
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
        side, lost = read_each(self.side_books(), lambda b: self.between(first, last, b))
        got += side
        got.sort(key=lambda e: (e.start, e.end, e.title))
        return got, [(b.name, str(exc)) for b, exc in lost]

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
        body = _jsonp(self._text(*self._events_page(book, start, end)))
        rows, skipped = parse_rows([*(body.get("data") or ()), *(body.get("data2") or ())], book.owner)
        events = sorted(distinct_events(labelled(rows, book)), key=lambda e: (e.start, e.end, e.title))
        self._note_unread(book.name or (_person(book.owner) if book.shared else ""), skipped)
        log.info("일정: %d줄(반복 %d · 단건 %d) · 못 읽은 줄 %d", len(events), len(body.get("data") or ()),
                 len(body.get("data2") or ()), skipped)
        return events

    def _events_page(self, book: Book, start: date, end: date) -> tuple[bytes, str]:
        """일정 목록 한 쪽 — 내 일정함은 읽는 손의 자리, 공유받은 일정함은 그 일정함의 서버 · DB 에서 잰 꼴 하나로 묻는다."""
        q = urllib.parse.urlencode({"callback": CALLBACK, "calendarId": book.calendar_id, "username": book.owner,
                                    "start": start.isoformat(), "end": end.isoformat(), "kind": book.kind})
        if book.shared:
            return self._get_shared(self._shared_server(book.server), f"{book.db_path}{SHARED_EVENTS_PATH}&{q}")
        return self._get(f"{EVENTS_PATH}&{q}")

    def _note_unread(self, name: str, skipped: int) -> None:
        """시각을 못 읽어 버린 줄이 있으면 ``unread`` 에 (일정함 이름, 줄 수)를 쌓는다 — 부르는 쪽이 「안 보인 일정이 있다」를 알릴 길이다."""
        if skipped:
            self.unread.append((name, skipped))

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
        """찾기의 답을 일정 줄로 푼다 — 못 읽은 줄 수를 적고 시작 차례로 세운다."""
        body = _jsonp(self._text(*got))
        out, skipped = parse_rows(body.get("data") or (), book.owner)
        self._note_unread("", skipped)
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
