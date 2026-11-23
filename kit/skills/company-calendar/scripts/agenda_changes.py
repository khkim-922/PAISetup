"""일정을 바꾸는 이름 붙은 손 셋(``register`` · ``edit`` · ``delete``)과 그 손가락. 바깥: 일정 앱(망) — 읽는 손의 세션을 쓴다."""

from __future__ import annotations

import pathlib
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from datetime import date, datetime, timedelta

from agenda_shapes import (ADDED, ALL_DAY_RULE, ALREADY, AMP_TOKEN, Added, Book, CALLBACK, CALLBACK_NEW, CHANGED, CLASHED,
                           CalendarConfigError, CalendarError, Change, ChangeRefused, Detail, DELETED, DELETE_FIXED, DELETE_PATH, EDITED,
                           Edited, Event, FORM_NEEDS, FORM_PATH, FORM_VALUE, FormChanged, GONE, GUEST_FIELDS, KEEP_ALL_DAY,
                           KEEP_GUESTS, KEEP_NO_DOC, KEEP_SHARED, KST, LANG, MOVE_PATH, PRIVATE, Removed, SAVE_PATH, SAVE_PREV_PATH,
                           STAMP_FORM, Seen, SessionExpired, TIMEOUT_SECONDS, UNSURE, VISIBILITY, Want, clean_title, event_ident,
                           event_key, event_mark, event_ref, kst_day, same_event)
from agenda_shapes import _aware, log
from agenda_rows import _Form, _jsonp
from agenda_reader import Reader, read_each

# ── 바꾸는 손이 올리는 말 — 진단용이고 일정 제목 · 이름 · 사번은 안 든다 ────────────────────────────────────
WANT_BAD = "넣을 일정의 제목 · 시각이 비었거나 끝이 시작보다 앞이다"
FORM_LOST = "등록 화면 대신 폼 없는 답이 왔다 — 세션이 끊긴 것으로 읽는다 · 넣지 않았다"
FORM_LACKING = "등록 화면에 잰 칸이 없다({n}칸) — 넣지 않았다"
FORM_NO_RRULE = "등록 화면에 RRULE 칸이 없다 — 하루 종일로 넣지 않았다"
FORM_NO_IMPORTANCE = "등록 화면에 Importance 칸이 없다 — 중요로 넣지 않았다"
EDIT_SHARED = "공유받은 일정함의 줄이라 고치지 않는다"
EDIT_KEPT = "손수 든 단건이 아니라 고치지 않는다({why})"
EDIT_REFUSED = {KEEP_ALL_DAY: "하루 종일 일정의 시각은 옮기지 않는다", KEEP_GUESTS: "참석자 · 참조자가 든 일정이라 고치지 않는다"}
EDIT_NO_DOC = "일정 줄에 문서 열쇠가 없다 — 줄의 꼴이 잰 것과 다르다 · 고치지 않았다"
EDIT_BACKWARDS = "옮길 끝이 시작보다 앞이다"
EDIT_NO_TITLE = "제목을 비울 수는 없다"
DELETE_SHARED = "공유받은 일정함의 줄이라 지우지 않는다"
DELETE_KEPT = "손수 든 단건이 아니라 지우지 않는다({why})"
DELETE_GUESTS = "참석자 · 참조자가 든 일정이라 지우지 않는다"


# ── 넣기 — 일정을 바꾸는 손 하나 ────────────────────────────────────────────────────────────────────
def _span(day: date, end: datetime) -> tuple[date, date]:
    """그 일정을 다시 읽을 날 — 시작하는 날부터 끝나는 날 다음 날까지(앱의 ``end`` 가 그날을 드는지 안 쟀다)."""
    return day, kst_day(end) + timedelta(days=1)


def _side_events(r: Reader, first: date, last: date) -> list[Event]:
    """기본 밖 내 일정함(Teams 따위)의 ``first`` ~ ``last`` 일정 — 안 읽히는 일정함은 건너뛴다(끊긴 세션은 올린다)."""
    out, lost = read_each(r.side_books(), lambda b: r.events(first, last, b))
    for _book, exc in lost:
        log.info("일정 넣기 — 기본 밖 일정함 하나를 못 읽어 그 일정함 없이 겹침을 가린다(%s)", type(exc).__name__)
    return out


def _span_of(want: Want) -> tuple[date, date]:
    """넣을 일정을 앞 · 뒤로 읽을 날 — 하루 종일이면 끝날까지."""
    return _span(want.day, datetime.combine(want.last_day, datetime.min.time(), KST) if want.all_day else want.end)


UNFIT_BACKWARDS, UNFIT_NO_TITLE = "backwards", "no_title"   # 값이 안 서는 까닭(``values_unfit``)


def values_unfit(title: str, start: datetime, end: datetime, *, span: bool) -> tuple[str, ...]:
    """넣거나 고칠 값이 안 서는 까닭들 — 끝이 시작 뒤가 아님(``span`` 일 때만 본다 — 고치기는 시각을 옮길 때만) · 빈 제목. 넣기 ·
    고치기와 명령의 그 판이 이것 하나로 본다. 다 서면 빈 차례."""
    unfit = []
    if span and _aware(end) <= _aware(start):
        unfit.append(UNFIT_BACKWARDS)
    if not title:
        unfit.append(UNFIT_NO_TITLE)
    return tuple(unfit)


def already_in(rows: list[Event], want: Want) -> Event | None:
    """읽은 줄 가운데 넣을 것과 같은 일정(``same_event``) — 없으면 None."""
    return next((e for e in rows if same_event(e, want)), None)


def fresh_clash(r: Reader, before: list[Event], want: Want, first: date, last: date, shown_clash: Iterable[str]) -> set[str]:
    """확인 뒤 그 시각에 새로 든 일정의 열쇠(``event_ref``) — 내 일정함 전부(기본 · 곁)에서 겹친 줄 가운데 확인에 안 보인 것."""
    around = before + _side_events(r, first, last)
    return {event_ref(e) for e in around if e.overlaps(want.start, want.end)} - set(shown_clash)


def open_form(r: Reader) -> dict[str, str]:
    """등록 화면의 첫 폼의 칸 — 폼이 없으면 ``SessionExpired``, 잰 칸이 없거나 고정 값이 다르면 ``FormChanged``(둘 다 안 넣는다)."""
    page, kind = r._open(r.url + FORM_PATH)
    form = _Form()
    form.feed(r._text(page, kind))
    if form.forms == 0:
        raise SessionExpired(FORM_LOST)
    lacking = [n for n in FORM_NEEDS if n not in form.fields]
    if lacking or form.fields.get("Form") != FORM_VALUE or not form.fields.get("Editors"):
        raise FormChanged(FORM_LACKING.format(n=len(lacking)))
    return form.fields


def form_fields(form: dict[str, str], want: Want, book: Book) -> dict[str, str]:
    """보낼 칸 — 폼의 칸을 다 기본값째 싣고 잰 칸만 바꾼다. 쓰는 사람 몫(``Editors`` · ``calEditors``)과 고정 값은 폼이 채운 그대로고,
    참석자 · 참조 칸은 비운다(남에게 알림이 안 가게). 하루 종일 · 중요에 드는 칸이 폼에 없으면 ``FormChanged``."""
    fields = {k: ("" if GUEST_FIELDS.match(k) else v) for k, v in form.items()}
    if want.all_day:     # 하루 종일 — 화면처럼 RRULE=ALLDAY 와 시각 없는 첫날 · 끝날(끝날도 든다)
        if "RRULE" not in form:
            raise FormChanged(FORM_NO_RRULE)
        start_text, end_text = want.day.isoformat(), want.last_day.isoformat()
        fields["RRULE"] = ALL_DAY_RULE
    else:
        start_text, end_text = (want.start.astimezone(KST).strftime(STAMP_FORM), want.end.astimezone(KST).strftime(STAMP_FORM))
    if want.important:
        if "Importance" not in form:
            raise FormChanged(FORM_NO_IMPORTANCE)
        fields["Importance"] = "true"
    fields.update(CalendarID=book.calendar_id, Subject=want.title, Description=want.note, StartDate=start_text, EndDate=end_text,
                  EventArea=want.place or form.get("EventArea", ""),
                  visibility=PRIVATE if want.private else (form.get("visibility") or VISIBILITY),
                  callback=CALLBACK_NEW)
    return fields


def send_form(r: Reader, fields: dict[str, str]) -> str:
    """저장 요청 하나 — 도중에 지면 그 예외 이름을 낸다(서버가 받았는지 모른다 · 끝은 다시 읽어 정한다). 다 갔으면 빈 글자."""
    try:
        r._open(r.url + SAVE_PATH, data=urllib.parse.urlencode(fields).encode("utf-8"))
    except CalendarError as exc:
        return type(exc).__name__
    return ""


def added_after(r: Reader, want: Want, book: Book, first: date, last: date, before: list[Event], detail: str) -> Added:
    """넣은 뒤 다시 읽어 끝을 정한다 — 넣기 앞에 없던 같은 일정이 섰으면 added, 안 섰거나 다시 읽기가 지면 unsure."""
    try:
        after = r.events(first, last, book)
    except CalendarError as exc:
        log.warning("일정 넣기 — 다시 읽기가 졌다(%s) · 넣었는지 모른다", type(exc).__name__)
        return Added(UNSURE, None, type(exc).__name__)
    known = {event_key(e) for e in before}
    made = already_in([e for e in after if event_key(e) not in known], want)
    log.info("일정 넣기 — %s", "다시 읽어 섰다" if made else "다시 읽어도 안 보인다")
    return Added(ADDED, made) if made else Added(UNSURE, None, detail)


def register(url: str, cookies_file: pathlib.Path | str, want: Want, *, timeout: float = TIMEOUT_SECONDS,
             reader: Reader | None = None, shown_clash: Iterable[str] | None = None) -> Added:
    """⚠ 회사 일정을 바꾼다 — 내 기본 일정함에 한 건을 넣고 ``Added`` 를 낸다. 사람이 그 한 건을 확인한 뒤에만 부른다.

    ``shown_clash`` 는 확인에 보인 겹침의 ``event_ref`` 들이다 — 확인은 내 일정함 전부(기본 · Teams)의 겹침을 보이므로, 그 밖의
    일정이 그 시각에 어느 내 일정함에든 생겼으면 ``clashed`` 로 안 넣는다. 기본 밖 일정함이 안 읽히면(세션 끊김이 아닌 한) 그
    일정함 없이 가린다 — 확인도 그 일정함을 못 읽었다고 알렸다. 등록 화면에 잰 칸이 없으면 ``FormChanged``(안 넣음). 등록 화면을
    열기 전에 진 것(세션 · 서버)은 아무것도 안 바꾼 채 올린다.
    """
    want = want.cleaned()
    if values_unfit(want.title, want.start, want.end, span=True):
        raise CalendarConfigError(WANT_BAD)
    r = reader or Reader(url, cookies_file, timeout=timeout)
    book = r.book()
    first, last = _span_of(want)
    before = r.events(first, last, book)
    hit = already_in(before, want)
    if hit is not None:
        log.info("일정 넣기 — 같은 일정이 이미 있어 넣지 않았다")
        return Added(ALREADY, hit)
    if shown_clash is not None:
        fresh = fresh_clash(r, before, want, first, last, shown_clash)
        if fresh:
            log.info("일정 넣기 — 확인 뒤 그 시각에 새 일정 %d건이 들어 넣지 않았다", len(fresh))
            return Added(CLASHED)
    fields = form_fields(open_form(r), want, book)
    return added_after(r, want, book, first, last, before, send_form(r, fields))


# ── 고치기 — 일정을 바꾸는 손 하나 ──────────────────────────────────────────────────────────────────
def locate(r: Reader, book: Book, seen: Seen) -> tuple[str, Event | None]:
    """보인 줄을 지금 읽어 — (끝 낱말, 지금 그 줄). 끝 낱말은 ""(그대로) · ``CHANGED``(옮겨졌거나 제목 · 시작 · 끝이 다르다) ·
    ``GONE``(그날에 없다). 고치기 · 지우기와 그 미리 보기가 이것 하나로 본다."""
    now = r.events(seen.day, seen.day + timedelta(days=1), book)
    hit = next((e for e in now if event_ref(e) == seen.ref), None)
    if hit is None:
        moved = next((e for e in now if event_ident(e) == seen.ident and e.day == seen.day), None)
        return (CHANGED, moved) if moved is not None else (GONE, None)
    return ("", hit) if event_mark(hit) == seen.mark else (CHANGED, hit)


def row_refusal(hit: Event, change: Change) -> str:
    """줄만 보고 가르는 고치지 않는 까닭 — 손수 든 단건이 아니면 그 까닭(``keep_reason``), 하루 종일 줄의 시각을 옮기면
    ``KEEP_ALL_DAY``, 아니면 빈 글자. 고칠 판과 고치는 손이 이것 하나로 본다."""
    if hit.keep_reason:
        return hit.keep_reason
    if hit.all_day and change.moves:
        return KEEP_ALL_DAY
    return ""


def doc_refusal(doc: Detail | None) -> str:
    """한 건을 보고 가르는 고치지 않는 까닭 — 한 건을 못 읽었으면 ``KEEP_NO_DOC``, 참석자 · 참조자가 들면(모르면 든 것으로)
    ``KEEP_GUESTS``, 아니면 빈 글자. 고칠 판과 고치는 손이 이것 하나로 본다."""
    if doc is None:
        return KEEP_NO_DOC
    return KEEP_GUESTS if doc.guests else ""


def new_times(hit: Event, change: Change) -> tuple[datetime, datetime]:
    """고친 뒤의 (시작, 끝) — 시작만 주면 길이를 지켜 옮기고(화면의 끌어 옮기기와 같다) 끝만 주면 끝만 바꾼다. 안 옮기면 그대로.
    고칠 판과 고치는 손이 이것 하나로 셈한다."""
    if not change.moves:
        return hit.start, hit.end
    start = change.start or hit.start
    return start, change.end or (start + (hit.end - hit.start))


def new_title(hit: Event, change: Change) -> str:
    """고친 뒤의 제목 — 안 바꾸면 지금 제목(회사 일정에 남는 꼴)."""
    return clean_title(hit.title) if change.title is None else change.title


def edit_values(hit: Event, doc: Detail, change: Change) -> tuple[str, str]:
    """고친 뒤의 (제목, 장소) — 안 바꾸는 칸은 지금 값."""
    return new_title(hit, change), doc.place if change.place is None else change.place


def _agent(r: Reader, path: str, params: list[tuple[str, str]]) -> dict:
    """바꾸는 에이전트 한 번 — GET 에 JSONP 로 답한다. 답을 못 읽으면 빈 dict(끝은 다시 읽어 정한다)."""
    data, kind = r._open(f"{r.url}{path}&{urllib.parse.urlencode([('callback', CALLBACK), *params])}")
    try:
        return _jsonp(r._text(data, kind))
    except CalendarError:
        return {}


def send_edit(r: Reader, book: Book, hit: Event, doc: Detail, change: Change, title: str, place: str, start: datetime,
              end: datetime) -> tuple[bool, str]:
    """고칠 요청 — 제목 · 장소가 바뀌면 미리 보기 [저장], 시각이 바뀌면 끌어 옮기기. (일정 앱이 「참석자께 알릴까」를 물었나,
    도중에 진 예외 이름 — 서버가 받았는지 모른다 · 끝은 다시 읽어 정한다)."""
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
    return notice, detail


def edited_after(r: Reader, book: Book, seen: Seen, hit: Event, title: str, place: str, start: datetime, end: datetime,
                 detail: str, notice: bool) -> Edited:
    """고친 뒤 다시 읽어 끝을 정한다 — 그 일정의 줄과 한 건이 바란 제목 · 장소 · 시각이면 edited, 다르거나 다시 읽기가 지면 unsure."""
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
        raise ChangeRefused(EDIT_SHARED, KEEP_SHARED)
    r = reader or Reader(url, cookies_file, timeout=timeout)
    book = r.book()
    state, hit = locate(r, book, seen)
    if state:
        return Edited(state, hit)
    why = row_refusal(hit, change)
    if why:
        raise ChangeRefused(EDIT_REFUSED.get(why) or EDIT_KEPT.format(why=why), why)
    if not hit.unid:
        raise CalendarError(EDIT_NO_DOC)
    doc = r.detail(hit.unid)
    why = doc_refusal(doc)
    if why:
        raise ChangeRefused(EDIT_REFUSED[why], why)
    start, end = new_times(hit, change)
    title, place = edit_values(hit, doc, change)
    unfit = values_unfit(title, start, end, span=change.moves)
    if UNFIT_BACKWARDS in unfit:
        raise CalendarConfigError(EDIT_BACKWARDS)
    if unfit:
        raise CalendarConfigError(EDIT_NO_TITLE)
    notice, detail = send_edit(r, book, hit, doc, change, title, place, start, end)
    return edited_after(r, book, seen, hit, title, place, start, end, detail, notice)


# ── 지우기 — 일정을 바꾸는 손 하나 ──────────────────────────────────────────────────────────────────
def has_guests(r: Reader, hit: Event) -> bool:
    """응답 칸이 찬 내 일정에 참석자 · 참조자가 드나 — 한 건을 읽어 본다. 문서 열쇠가 없어 못 읽으면 든 것으로 둔다."""
    return not hit.unid or r.detail(hit.unid).guests


def send_delete(r: Reader, book: Book, hit: Event) -> str:
    """지우기 요청 하나 — 도중에 지면 그 예외 이름을 낸다(서버가 받았는지 모른다 · 끝은 다시 읽어 정한다). 다 갔으면 빈 글자."""
    q = urllib.parse.urlencode([("calendarId", book.calendar_id), ("eventId", hit.event_id), ("ownerId", book.owner),
                                ("userName", book.owner), *DELETE_FIXED])
    try:
        r._open(f"{r.url}{DELETE_PATH}&{q}")
    except CalendarError as exc:
        return type(exc).__name__
    return ""


def removed_after(r: Reader, book: Book, seen: Seen, hit: Event, first: date, last: date, detail: str) -> Removed:
    """지운 뒤 다시 읽어 끝을 정한다 — 그 줄이 사라졌으면 deleted, 남았거나 다시 읽기가 지면 unsure."""
    try:
        after = r.events(first, last, book)
    except CalendarError as exc:
        log.warning("일정 지우기 — 다시 읽기가 졌다(%s) · 지웠는지 모른다", type(exc).__name__)
        return Removed(UNSURE, hit, type(exc).__name__)
    left = any(event_ref(e) == seen.ref for e in after)
    log.info("일정 지우기 — %s", "다시 읽어도 남아 있다" if left else "다시 읽어 사라졌다")
    return Removed(UNSURE, hit, detail) if left else Removed(DELETED, hit)


def delete(url: str, cookies_file: pathlib.Path | str, target: Event | Seen, *, timeout: float = TIMEOUT_SECONDS,
           reader: Reader | None = None) -> Removed:
    """⚠ 회사 일정을 바꾼다 — 내 일정함의 한 줄을 지운다. 사람이 그 한 건을 확인한 뒤에만 부른다.

    ``target`` 은 사람에게 보인 그 줄(``Event``)이나 그 손잡이(``Seen``)다. ``Removed`` 를 낸다 — 그 줄이 옮겨졌거나 제목 · 시작 ·
    끝이 보인 것(``mark``)과 다르면 ``changed``, 그날에 없으면 ``gone``(둘 다 지우기를 안 부른다). 쓰는 사람이 손수 든 단건이
    아니면 묻기 전에 ``ChangeRefused``(``reason`` 에 까닭)."""
    seen = target if isinstance(target, Seen) else Seen.of(target)
    if seen.shared:   # 공유받은 일정함의 줄 — 내 일정함에 같은 열쇠의 줄이 있어도 그것을 지우지 않게 묻기 전에 거절한다
        raise ChangeRefused(DELETE_SHARED, KEEP_SHARED)
    r = reader or Reader(url, cookies_file, timeout=timeout)
    book = r.book()
    first, last = seen.day, seen.day + timedelta(days=1)
    state, hit = locate(r, book, seen)
    if state:
        log.info("일정 지우기 — 보인 뒤 그 줄이 %s 지우지 않았다", "바뀌어" if state == CHANGED else "그날에 없어")
        return Removed(state, hit)
    if hit.keep_reason:
        raise ChangeRefused(DELETE_KEPT.format(why=hit.keep_reason), hit.keep_reason)
    if hit.response and has_guests(r, hit):   # 응답 칸이 찬 내 일정 — 참석자가 들었으면 지우기가 그분들께 알림이 될 수 있다
        raise ChangeRefused(DELETE_GUESTS, KEEP_GUESTS)
    return removed_after(r, book, seen, hit, first, last, send_delete(r, book, hit))
