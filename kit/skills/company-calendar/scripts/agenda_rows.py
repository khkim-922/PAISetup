"""일정 앱의 글 꼴을 일정 손의 꼴로 푼다 — JSONP 몸통 · 일정 줄 · 한 건 문서 · 등록 화면의 폼. 바깥에 닿지 않는다."""

from __future__ import annotations

import html
import html.parser
import json
import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from agenda_shapes import (CALLBACK, CalendarError, Detail, Event, KST, MEETING, PRIVATE, Person, STAMP_ROW, SessionExpired,
                           TRUE_WORDS, UNID)


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
    """앱의 참 · 거짓 칸을 읽는다 — ``TRUE_WORDS`` 의 낱말이면 참."""
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


def parse_rows(rows, me: str = "") -> tuple[list[Event], int]:
    """일정 줄들 — (읽은 줄, 시각을 못 읽거나 꼴이 아니어서 버린 줄 수). 차례는 받은 그대로다."""
    out, skipped = [], 0
    for row in rows:
        e = parse_row(row, me) if isinstance(row, dict) else None
        if e is None:
            skipped += 1
            continue
        out.append(e)
    return out, skipped


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
        """첫 폼 안의 칸 하나를 적는다 — 보내지 않는 칸(안 고른 체크 · 단추 · 파일)은 빼고, 고르기는 고른 값이나 첫 값을 기다린다."""
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
        """폼 · 글 칸 · 고르기가 닫힌다 — 고른 것이 없던 고르기는 첫 값을 갖는다."""
        if tag == "form":
            self._in_form = False
        elif tag == "textarea":
            self._textarea = None
        elif tag == "select" and self._select:
            self.fields.setdefault(self._select, self._first_option or "")
            self._select = None

    def handle_data(self, data):
        """열린 글 칸(textarea)의 글을 그 칸에 잇는다."""
        if self._textarea:
            self.fields[self._textarea] += data
