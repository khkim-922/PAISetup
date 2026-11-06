"""agenda.py 의 계약을 가짜 일정 앱으로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 일정 앱은 GET 으로도 바뀐다 — 일정 줄이 내는 주소는 편집 화면이고 지우기도 GET 이다. 읽는 손이 그 주소를 한 번
지으면 일정이 조용히 지워지고, 넣기가 참석자 칸을 채우면 남에게 초대가 가고, 넣기 · 지우기가 답을 믿으면 「넣었습니다 · 지웠습니다」가
거짓이 된다. 공유받은 일정함을 읽는 손이 그 일정함 자리의 읽기 꼴 밖을 묻거나 사내 밖 서버에 쿠키를 싣는 것도, 같은 일정을 두 번 넣거나, 받은 초대 · 회의 · 반복 · 하루 종일 일정을 지우거나, 보인 뒤 바뀐 줄을 지우는 것도 여기서 문다.
남기는 까닭(check-design §1 넷) — 길이 분명하다(일정 줄마다 편집 주소가 실려 오고, 대화하는 모델이 이 손을 부른다 · 이 파일을 그 자리에서
쓰는 앱이 있다) · 깨지면 조용하고 되돌릴 수 없다(지워진 일정 · 몰래 든 일정 · 남에게 간 알림은 아무 표도 안 낸다) · 크게 다친다(남이
보는 공유 시스템이 바뀐다) · 다른 무엇도 안 잡는다(회사 일정 앱은 회사 PC 에서만 닿는다).

가짜 일정 앱은 사내 일정 앱에서 잰 주소 · 꼴을 흉내 낸다 — 꼴의 원본은 agenda.py 머리말 「사내 일정 앱에서 잰 것」이 가리키는 기록이고,
흉내는 그 앱 저장소(mail-secretary)의 ``_check/_fake_agenda.py``(68ad771)에서 옮겼다(이 파일은 agenda.py 의 값을 읽어 오지 않는다).
흉내가 지키는 것 — 쿠키가 없거나 세션이 끊긴 판이면 200 에 SSO 로 보내는 HTML. 일정은 두 배열(반복은 날짜마다 한 줄 · 단건)이고 제목은
HTML 엔티티로 낸다. 등록 화면의 폼은 잰 「값이 찬 칸」과 빈 칸을 숨은 칸으로 내고(고정 값 칸의 실물 값은 안 쟀다 — 지어낸 값이다), 저장은
폼이 낸 고정 값이 그대로 돌아와야 선다(답은 늘 창 닫기다). 참석자 칸이 찬 저장은 「남에게 알림이 갔다」로 남긴다. 편집 화면 · 지우기
주소를 부르면 바꾼 요청으로 남긴다. 받은 요청 · 쿠키 머리는 다 적어 「안 불렀다 · 안 실었다」를 그것으로 잰다 — 몸통이 스스로 말하는
기록이 아니다.

물림 — 막기를 푼 읽는 손 · 폼을 버리고 잰 칸만 싣는 넣기 · 지우지 않는 까닭을 안 보는 지우기에 같은 판정을 대어 빨강을 본다(매번 돈다).
일부러 틀린 사본을 다른 폴더에 두고 그 폴더를 주면 사본 전체의 물림을 잰다.

돌리는 법::

    python -X utf8 -I check_agenda.py [agenda.py 가 든 폴더]

폴더를 안 주면 이 파일의 폴더를 잰다.

판정 — 끝 줄이 「통과 N/N」이면 종료 코드 0, 하나라도 어긋나면 1, 가짜 일정 앱을 못 띄우는 등 재지 못했으면 2.

언제 걷나 — agenda.py 가 사라지거나, 같은 계약을 실물 일정 앱에서 재는 검사가 서서 이 검사가 더하는 믿음이 없어지면.

여기서 못 재는 것 — 사내 SSO 를 넘는 길 · 실물 등록 폼이 스크립트로 값을 채우는지 · 실물이 고정 값을 안 옮긴 저장에 무엇을 하는지(가짜는
「안 섰다」로 둔다) · 실물 지우기가 틀린 칸(남의 일정함 · 남의 이름)에 무엇을 하는지 · 실물 줄의 ``editable`` 값의 꼴 · 하루 종일 ·
여러 날 일정의 실물 꼴(가짜의 하루 종일 줄은 지어낸 꼴이다) · 일정 조회의 ``end`` 가 그날을 드는지(가짜는 든다).
"""

from __future__ import annotations

import contextlib
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
from datetime import date, datetime, timedelta, timezone

TREE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else __file__).resolve()
TREE = TREE if TREE.is_dir() else TREE.parent
sys.path.insert(0, str(TREE))
import agenda  # noqa: E402 — 잴 나무가 sys.path 에 먼저 서야 한다

logging.getLogger(agenda.__name__).addHandler(logging.NullHandler())

# ── 가짜 일정 앱의 꼴 — 사람 · 사번 · 고정 값은 지어낸 것이다 ─────────────────────────────────────────
DB = "/02/cal/calperson32.nsf"
EMPNO = "100001"
OWNER = f"CN=이도윤/OU={EMPNO}/OU=02/O=gaonnet"
CALENDAR_ID = f"{EMPNO}_Calendar"
SYS_ADMIN = "calAdmin=SYS/02/gaonnet"
EVENT_AREA = "업무"
COOKIE = ("DomAuthSessId", "good-session")
FOREIGN_COOKIE = ("JSESSIONID", "ecm-only")      # 다른 사내 호스트(ECM)의 쿠키 — 세션 파일에 함께 든다
KST = timezone(timedelta(hours=9))
# 끊긴 세션에 사내 앱이 내는 답의 첫머리(실측) — 200 · text/html
LOGIN_PAGE = ('<html><head><script>document.cookie = "EP_CERTIFY_CA=; path=/; domain=.posco.net;";'
              'window.location.href="http://swpsso.posco.net/idms/U61/jsp/login/login.jsp";'
              '</script></head><body></body></html>')
CLOSE_PAGE = "<html><head><script>try{opener.location.reload();}catch(e){};window.close();</script></head><body></body></html>"
# 등록 폼의 칸 — 잰 저장 몸통의 「값이 찬 칸」 · 「빈 채로 간 칸」 이름을 그대로(약 90칸 가운데 이름이 잰 것만)
FILLED = {"Form": "Event", "Subject": "", "Description": "", "StartDate": "", "EndDate": "", "TimeZoneID": "Asia/Seoul",
          "CalendarID": CALENDAR_ID, "EventArea": EVENT_AREA, "visibility": "public",
          "Editors": f"calEditors=이도윤/{EMPNO}/02/gaonnet", "Readers": "calReaders=*", "SysAdmin": SYS_ADMIN,
          "callback": "new", "sequence": "0", "__Click": "0", "Importance": "false", "locked": "False",
          "updatetype": "none", "cdate": "none", "CalDefaultPeriod": "0", "attAadditionalGuests": "0",
          "refAadditionalGuests": "0"}
EMPTY = ("EventId", "location", "attAttendees", "attRequired", "attOptional", "refReferences", "refNames", "RRULE",
         "FREQ", "BYDAY", "INTERVAL", "ExDate", "reminders", "remindersTime", "video_meet", "Owner", "calEditors")
FORM_FIELDS = 95                      # 잰 폼의 칸 수 — 이름을 안 잰 칸은 `extraNN` 으로 채운다
# 회사에서 잰 바꾸는 주소 — 읽는 손이 짓지 않아야 할 꼴
CHANGING = ("/vweventprev/00000000000000000000000000000001?editdocument",
            "/Eventquick?OpenForm",
            "/Eventquick?OpenForm&Seq=1",
            "/(wEventDelete)?openagent&calendarId=100001_Calendar&eventId=100001_20261020073001&ownerId=x&userName=x"
            "&alim=&msgtitle=&isediter=true&SAResponse=json&lang=kor&allimTarget=",
            "/quickRegistration?openform&startdate=2026-10-20%2009:00&enddate=2026-10-20%2010:00",
            "/(agCheckDoc)?openagent&unid=1&sourceowner=x&calid=x",
            "/confirmDelForNomalEvent?openform",
            "/MainFrame?openform")
CHANGE_MARKS = ("editdocument", "eventquick", "weventdelete", "quickregistration", "agcheckdoc", "confirmdel")
# 공유받은 일정함 둘 — 실물은 일정함마다 서버 · DB 가 다르다. 가짜는 한 서버에 DB 만 달리 세운다(호스트는 띄운 뒤 정해진다)
SHARED = {"200001_Calendar": ("GRW", "CN=한서진/OU=200001/OU=02/O=gaonnet", "한서진", "/02/cal/calperson07.nsf"),
          "200002_Calendar": ("GRR", "CN=윤재하/OU=200002/OU=02/O=gaonnet", "윤재하", "/02/cal/calperson11.nsf")}
OUTSIDE_HOST = "calendar.outside.example"      # 사내 도메인 밖 서버를 든 일정함 줄 — 읽는 손이 묻지 않아야 한다


class Unmeasured(Exception):
    """잴 판을 못 세웠다 — 어긋남이 아니라 「못 쟀다」다."""


@dataclass
class FakeEvent:
    """일정 하나 — 시각은 서울의 ``YYYY-MM-DD HH:MM``. ``repeat_days`` 가 1 보다 크면 그만큼의 날에 같은 열쇠로 풀린다."""
    start: str
    end: str
    title: str
    response: str = ""
    eventtype: str = ""
    repeat_days: int = 1
    all_day: bool = False
    editable: bool = True
    timezone: str = ""
    event_id: str = ""
    unid: str = field(default="")


def _stamp(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d %H:%M")


class FakeCalendar:
    """127.0.0.1 의 사내 일정 앱 흉내. ``paths`` 는 받은 GET, ``posts`` 는 받은 POST, ``changes`` 는 일정을 바꾼 요청,
    ``cookies`` 는 요청마다 실려 온 쿠키 머리."""

    def __init__(self, events=(), *, session: str = "ok", calendars: str = "normal", form: str = "normal",
                 saves: str = "normal", deletes: str = "normal"):
        self.events: list[FakeEvent] = []
        self._made = 0
        for e in events:
            self.add(e)
        self.session = session          # ok · login(200 SSO HTML) · redirect(302 SSO) · denied(401)
        self.calendars = calendars      # normal · none(내 일정함 없음) · two(내 일정함이 둘) · outside(사내 밖 서버의 공유 일정함)
        self.form = form                # normal · changed(잰 칸이 없는 화면) · prefilled(참석자 칸이 찬 폼)
        self.saves = saves              # normal · cut(저장하고 답 없이 끊는다)
        self.deletes = deletes          # normal · ignore(답은 하는데 안 지운다) · cut(지우고 답 없이 끊는다)
        self.paths: list[str] = []
        self.posts: list[tuple[str, dict]] = []
        self.changes: list[tuple[str, str]] = []
        self.cookies: list[str] = []
        self.lock = threading.Lock()
        app = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                with app.lock:
                    app.paths.append(self.path)
                    app.cookies.append(self.headers.get("Cookie") or "")
                    app.answer(self)

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                body = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8"), keep_blank_values=True) if n else {}
                with app.lock:
                    app.posts.append((self.path, {k: v[0] for k, v in body.items()}))
                    app.cookies.append(self.headers.get("Cookie") or "")
                    app.save(self, {k: v[0] for k, v in body.items()})

        try:
            self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        except OSError as exc:
            raise Unmeasured(f"가짜 일정 앱을 못 띄웠다: {exc}") from exc
        self.url = f"http://127.0.0.1:{self.server.server_port}{DB}"
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def add(self, e: FakeEvent) -> FakeEvent:
        # 실물 열쇠는 `<사번>_<만든 시각>` 이라 지운 일정의 열쇠를 새 일정이 다시 받지 않는다 — 만든 차례로 짓는다
        self._made = n = self._made + 1
        e.event_id = e.event_id or f"{EMPNO}_{datetime(2026, 1, 1) + timedelta(seconds=n):%Y%m%d%H%M%S}"
        e.unid = e.unid or f"{n:032X}"
        self.events.append(e)
        return e

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def changed(self, kind: str) -> list[str]:
        return [eid for k, eid in self.changes if k == kind]

    # ── 답 ──
    def send(self, h, status: int, body: str, kind: str = "text/html; charset=UTF-8") -> None:
        raw = body.encode("utf-8")
        h.send_response(status)
        h.send_header("Content-Type", kind)
        h.send_header("Content-Length", str(len(raw)))
        h.end_headers()
        h.wfile.write(raw)

    def cut(self, h) -> None:
        """답 없이 끊는다 — 요청이 도중에 진 판."""
        h.close_connection = True
        with contextlib.suppress(OSError):
            h.connection.shutdown(2)

    def _session_ok(self, h) -> bool:
        return self.session == "ok" and f"{COOKIE[0]}={COOKIE[1]}" in (h.headers.get("Cookie") or "")

    def _lost(self, h) -> None:
        if self.session == "denied":
            return self.send(h, 401, "<html>unauthorized</html>")
        if self.session == "redirect":
            h.send_response(302)
            h.send_header("Location", "http://swpsso.posco.net/idms/U61/jsp/login/login.jsp")
            h.send_header("Content-Length", "0")
            h.end_headers()
            return
        self.send(h, 200, LOGIN_PAGE)

    def answer(self, h) -> None:
        if not self._session_ok(h):
            return self._lost(h)
        raw = urllib.parse.unquote(h.path)
        shared = next((cid for cid, v in SHARED.items() if raw.startswith(v[3] + "/")), None)
        if shared:
            rest, _, query = raw[len(SHARED[shared][3]):].partition("?")
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(h.path).query, keep_blank_values=True)
            if "editdocument" in f"{rest}?{query}".lower() or "weventdelete" in rest.lower():
                self.changes.append(("shared_changed", rest))
                return self.send(h, 200, "<html>changed</html>")
            if rest.lower() == "/getcalendarevent" and query.lower().startswith("readform"):
                return self.send(h, 200, self.shared_jsonp((q.get("callback") or [""])[0], (q.get("calendarId") or [""])[0],
                                                           (q.get("username") or [""])[0]))
            return self.send(h, 404, "<html>not found</html>")
        if not raw.startswith(DB):
            return self.send(h, 404, "<html>not found</html>")
        rest, _, query = raw[len(DB):].partition("?")
        low = f"{rest}?{query}".lower()
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(h.path).query, keep_blank_values=True)
        one = lambda k: (q.get(k) or [""])[0]   # noqa: E731
        if "?editdocument" in low:
            unid = rest.rsplit("/", 1)[-1]
            hit = next((e for e in self.events if e.unid == unid), None)
            self.changes.append(("edit_opened", hit.event_id if hit else unid))
            return self.send(h, 200, "<html>event edit form</html>")
        if rest.lower() == "/(weventdelete)":
            self.changes.append(("delete_called", one("eventId")))
            hit = next((e for e in self.events if e.event_id == one("eventId")), None)
            # 내 일정함 · 쓰는 사람의 Notes 이름이 맞을 때만 지운다(잰 꼴의 칸). 실물이 틀린 칸에 무엇을 하는지는 안 쟀다
            mine = one("calendarId") == CALENDAR_ID and one("ownerId") == OWNER and one("userName") == OWNER
            if hit is not None and mine and self.deletes != "ignore":
                self.events.remove(hit)
                self.changes.append(("deleted", hit.event_id))
            if self.deletes == "cut":
                return self.cut(h)
            return self.send(h, 200, '{"RETURN" : "" }')
        if low == "/aggetcalendar?openagent&calltype=gnb":
            return self.send(h, 200, json.dumps(self.calendar_rows(), ensure_ascii=False))
        if low.startswith("/getcalendareventme?readform"):
            return self.send(h, 200, self.events_jsonp(one("callback"), one("calendarId"), one("start"), one("end")))
        if low == "/eventquick?openform":
            return self.send(h, 200, self.form_page())
        return self.send(h, 404, "<html>not found</html>")

    def calendar_rows(self) -> list[dict]:
        def row(kind: str, cid: str, owner: str, host: str, path: str) -> dict:
            return {"kind": kind, "docid": cid.replace("_", "")[:32].ljust(32, "0"), "calendartype": "defaultCalendar",
                    "calendarid": cid, "subject": "일정", "owner": owner, "sourceowner": owner,
                    "calvisibility": "public", "selected": "true", "isCalDav": "true", "calhost": host,
                    "caldbserver": host, "caldbpath": path, "email": "", "ownerdeptname": "", "sourceownerusecalendar": "Y",
                    "addcode": "02"}
        mine = row("PEO", CALENDAR_ID, OWNER, "pcfca03", DB.lstrip("/"))
        here = urllib.parse.urlsplit(self.url).netloc
        groups = []
        for cid, (kind, owner, name, path) in SHARED.items():
            # 실물 꼴 — `owner` 는 보는 사람(나), 일정함 주인은 `sourceowner`, 목록 이름은 `subject`
            groups.append(dict(row(kind, cid, OWNER, here, path.lstrip("/")), sourceowner=owner, subject=name))
        if self.calendars == "outside":
            groups.append(dict(row("GRR", "200003_Calendar", OWNER, OUTSIDE_HOST, "02/cal/calperson99.nsf"),
                               sourceowner="CN=밖사람/OU=200003/OU=02/O=gaonnet", subject="밖사람"))
        if self.calendars == "none":
            return groups
        if self.calendars == "two":
            return [mine, dict(mine, calendarid="100009_Calendar"), *groups]
        return [mine, *groups]

    def _row(self, e: FakeEvent, start: datetime, end: datetime) -> dict:
        return {"eventId": e.event_id, "eventtype": e.eventtype, "CalendarServer": "pcfca03", "CalendarDB": DB.lstrip("/"),
                "CalendarID": CALENDAR_ID, "repeat": "true" if e.repeat_days > 1 else "false",
                "allDay": "true" if e.all_day else "false", "originalallDay": "true" if e.all_day else "false",
                "title": e.title.replace("[", "&#91;").replace("]", "&#93;"), "start": f"{start:%Y-%m-%d %H:%M:%S}",
                "end": f"{end:%Y-%m-%d %H:%M:%S}", "timeZone": e.timezone, "colorId": "1",
                "attRsponseStatus": e.response, "owner": OWNER, "Importance": "false", "visibility": "public",
                "editable": "true" if e.editable else "false", "editors": "", "attOwner": OWNER, "Owner": OWNER,
                "url": f"{DB}/vweventprev/{e.unid}?editdocument"}

    def shared_jsonp(self, callback: str, cid: str, username: str) -> str:
        """공유 일정함의 일정 — 그 일정함 주인의 이름으로 물었을 때만 줄을 낸다. 한 줄은 주인이 비공개로 든 것이다."""
        data2 = []
        if cid in SHARED and username == SHARED[cid][1]:
            for i, (title, vis) in enumerate((("본부 주간회의", "public"), ("병원 진료", "private"))):
                e = FakeEvent(f"2026-11-10 {9 + i * 4:02d}:00", f"2026-11-10 {10 + i * 4:02d}:00", f"{SHARED[cid][2]} {title}",
                              event_id=f"{cid[:6]}_2026010100000{i}", unid=f"{cid[:6]}{i:026X}")
                r = self._row(e, _stamp(e.start), _stamp(e.end))
                r.update(CalendarID=cid, visibility=vis, editable="", owner=SHARED[cid][1], Owner=SHARED[cid][1],
                         url=f"{SHARED[cid][3]}/vweventprev/{e.unid}?editdocument")
                data2.append(r)
        body = {"color": "", "textColor": "", "colorId": "", "cuser": OWNER, "data": [], "data2": data2}
        return f"{callback}({json.dumps(body, ensure_ascii=False)})"

    def events_jsonp(self, callback: str, cid: str, start: str, end: str) -> str:
        lo, hi = datetime.strptime(start, "%Y-%m-%d"), datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        data, data2 = [], []
        if cid == CALENDAR_ID:
            for e in self.events:
                s, t = _stamp(e.start), _stamp(e.end)
                for i in range(e.repeat_days):
                    a, b = s + timedelta(days=i), t + timedelta(days=i)
                    if lo <= a < hi:
                        (data if e.repeat_days > 1 else data2).append(self._row(e, a, b))
        body = {"color": "#3a87ad", "textColor": "#ffffff", "colorId": "1", "start": start, "end": end, "cuser": OWNER,
                "data": data, "data2": data2}
        return f"{callback}({json.dumps(body, ensure_ascii=False)})"

    def form_page(self) -> str:
        if self.form == "changed":
            return "<html><body><form method='post' action='Eventquick?OpenForm&Seq=1'><input name='Title'></form></body></html>"
        inputs = "".join(f'<input type="hidden" name="{k}" value="{v}">' for k, v in FILLED.items() if k != "Description")
        # prefilled — 참석자 · 참조 칸에 값이 든 폼. 실물이 이 칸을 채워 오는지는 안 쟀다(잰 저장은 빈 채로 갔다) — 비우는 손의 물림용 꼴이다
        guest = f"이도윤/{EMPNO}/02/gaonnet" if self.form == "prefilled" else ""
        inputs += "".join(f'<input type="hidden" name="{k}" value="{guest if k.startswith(("att", "ref")) else ""}">'
                          for k in EMPTY)
        rest = FORM_FIELDS - len(FILLED) - len(EMPTY)
        inputs += "".join(f'<input type="hidden" name="extra{i:02d}" value="">' for i in range(rest))
        return (f'<html><body><form method="post" name="_Event" action="{DB}/Eventquick?OpenForm&amp;Seq=1">{inputs}'
                '<textarea name="Description"></textarea><input type="button" value="저장"></form></body></html>')

    def save(self, h, body: dict) -> None:
        if not self._session_ok(h):
            return self._lost(h)
        if urllib.parse.unquote(h.path).lower() != f"{DB}/eventquick?openform&seq=1".lower():
            return self.send(h, 404, "<html>not found</html>")
        try:
            start, end = _stamp(body.get("StartDate", "")), _stamp(body.get("EndDate", ""))
        except ValueError:
            return self.send(h, 200, CLOSE_PAGE)
        # 폼의 고정 값이 그대로 돌아와야 선다 — 안 옮긴 저장은 「안 섰다」(답은 늘 창 닫기다)
        if any(body.get(k) != FILLED[k] for k in ("Form", "SysAdmin", "CalendarID", "Editors", "Readers")) \
                or len(body) < FORM_FIELDS:
            return self.send(h, 200, CLOSE_PAGE)
        if any(body.get(k) for k in EMPTY if k.startswith(("att", "ref"))):
            self.changes.append(("guests_notified", ""))   # 참석자 칸이 찬 저장 — 실물은 남에게 알림을 보낸다
        e = self.add(FakeEvent(f"{start:%Y-%m-%d %H:%M}", f"{end:%Y-%m-%d %H:%M}", body.get("Subject", "")))
        self.changes.append(("saved", e.event_id))
        if self.saves == "cut":
            return self.cut(h)
        return self.send(h, 200, CLOSE_PAGE)


# ── 이야기 — 2026-11-09(월) 주의 일정. 회의 · 사람은 다 지어낸 것이다 ─────────────────────────────────

DAY = date(2026, 11, 10)


def world() -> list[FakeEvent]:
    """잰 꼴을 고루 담은 한 주 — 손수 든 단건 · 받은 초대 · 쓰는 사람이 연 회의 · 반복 · 하루 종일 · 고칠 수 없는 줄 · 엔티티 제목 ·
    +09:00 시간대 칸."""
    return [FakeEvent("2026-11-10 09:00", "2026-11-10 09:30", "[팀] 실적 정리"),                       # 손수 든 단건
            FakeEvent("2026-11-10 10:00", "2026-11-10 11:00", "4분기 경영회의", response="needsAction",
                      eventtype="Meeting"),                                                           # 받은 초대
            FakeEvent("2026-11-10 13:00", "2026-11-10 14:00", "협력사 면담", eventtype="Meeting"),      # 쓰는 사람이 연 회의
            FakeEvent("2026-11-09 08:30", "2026-11-09 09:00", "주간 점검", repeat_days=5),              # 반복 — 다섯 날
            FakeEvent("2026-11-10 00:00", "2026-11-11 00:00", "창립 기념일", all_day=True),             # 하루 종일
            FakeEvent("2026-11-10 16:00", "2026-11-10 16:30", "보안 교육", editable=False),             # 고칠 수 없는 줄
            FakeEvent("2026-11-11 15:00", "2026-11-11 16:00", "자료 검토", timezone="+09:00")]           # 시간대 칸이 찬 줄


def cookie_file(folder: pathlib.Path, *, expires: float = -1, foreign: bool = True) -> pathlib.Path:
    """세션 손이 남기는 꼴의 쿠키 파일 — 일정 서버(127.0.0.1)의 쿠키와, 다른 사내 호스트의 쿠키가 함께 든다."""
    cookies = [{"name": COOKIE[0], "value": COOKIE[1], "domain": "127.0.0.1", "path": "/", "expires": expires,
                "httpOnly": True, "secure": False, "sameSite": "Lax"}]
    if foreign:
        cookies.append({"name": FOREIGN_COOKIE[0], "value": FOREIGN_COOKIE[1], "domain": "swpecm.posco.net",
                        "path": "/ECM", "expires": -1, "httpOnly": True, "secure": False, "sameSite": "Lax"})
    path = folder / "session.json"
    path.write_text(json.dumps({"cookies": cookies, "origins": []}), encoding="utf-8")
    return path


@contextlib.contextmanager
def stage(events=None, *, expires: float = -1, **fake):
    """가짜 일정 앱 하나와 그 앱에 붙은 읽는 손 — (앱, 손, 쿠키 파일)."""
    cal = FakeCalendar(world() if events is None else events, **fake)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            ck = cookie_file(pathlib.Path(tmp), expires=expires)
            yield cal, agenda.Reader(cal.url, ck, timeout=5), ck
    finally:
        cal.close()


def raises(kind, action) -> Exception:
    try:
        action()
    except kind as exc:
        return exc
    except Exception as exc:  # noqa: BLE001 — 다른 예외는 어긋남이다
        raise AssertionError(f"{kind.__name__} 대신 {type(exc).__name__}: {exc}") from exc
    raise AssertionError(f"{kind.__name__} 가 안 났다")


def changing(paths) -> list[str]:
    return [p for p in paths if any(m in urllib.parse.unquote(p).lower() for m in CHANGE_MARKS)]


def by_title(reader, title: str, first: date = DAY, last: date = DAY):
    hit = [e for e in reader.between(first, last) if e.title == title]
    assert len(hit) == 1, f"「{title}」 이 {len(hit)}줄이다"
    return hit[0]


def want(title="시험 일정", start="2026-11-10 14:30", end="2026-11-10 15:00", note=""):
    return agenda.Want(title, agenda.kst(start), agenda.kst(end), note)


# ── 읽기 ──────────────────────────────────────────────────────────────

def refused_paths(reader, cal) -> list[str]:
    """바꾸는 주소마다 서버에 닿기 전에 ``ChangeRefused`` 인가 — 어긋난 줄."""
    bad, before = [], len(cal.paths)
    for path in CHANGING:
        try:
            reader._get(path)
            bad.append(f"막지 않았다: {path[:40]}")
        except agenda.ChangeRefused:
            pass
        except agenda.CalendarError as exc:
            bad.append(f"막지 않고 서버에 물었다: {path[:40]} ({type(exc).__name__})")
    if changing(cal.paths[before:]):
        bad.append(f"바꾸는 주소가 일정 앱에 닿았다 {len(changing(cal.paths[before:]))}번")
    return bad


def check_changing_urls_are_refused_before_asking():
    with stage() as (cal, reader, ck):
        bad = refused_paths(reader, cal)
        assert not bad, bad
        assert not cal.paths and not cal.changes, cal.paths

        class OpenReader(agenda.Reader):        # 물림 — 막기를 푼 읽는 손
            def _get(self, path):
                return self._open(self.server + self.db_path + path)
        mutant = refused_paths(OpenReader(cal.url, ck, timeout=5), cal)
        assert mutant and cal.changes, "물림이 안 물었다 — 막기를 푼 손에도 판정이 초록이다"


def check_reading_everything_asks_only_the_two_read_addresses():
    with stage() as (cal, reader, _):
        week = reader.between(date(2026, 11, 9), date(2026, 11, 13))
        assert not changing(cal.paths) and not cal.changes, cal.paths
        reached = sorted({p.split("?")[0].rsplit("/", 1)[-1] for p in cal.paths})
        assert reached == ["agGetCalendar", "getcalendareventMe"], reached   # 양성 대조 — 읽기 둘이 닿았다
        repeats = [e for e in week if e.repeat]
        assert len(repeats) == 5 and len({e.event_id for e in repeats}) == 1, repeats   # 반복은 날짜마다 한 줄
        assert len(week) == 11, [e.title for e in week]                      # 단건 여섯 + 반복 다섯
        titles = {e.title for e in week}
        assert "[팀] 실적 정리" in titles, titles                            # 엔티티를 푼다
        invite = next(e for e in week if e.title == "4분기 경영회의")
        assert invite.response == "needsAction" and invite.meeting, invite
        own = next(e for e in week if e.title == "[팀] 실적 정리")
        assert (own.when(), own.day) == ("09:00–09:30", DAY), (own.when(), own.day)
        zoned = next(e for e in week if e.title == "자료 검토")
        assert zoned.when() == "15:00–16:00", zoned.when()                   # +09:00 칸도 서울 시각 그대로
        assert next(e for e in week if e.title == "창립 기념일").when() == "하루 종일"


def check_between_keeps_only_the_asked_days():
    with stage() as (_, reader, _ck):
        day = reader.between(DAY, DAY)
        assert {e.day for e in day} == {DAY}, sorted({e.day for e in day})
        assert {e.title for e in day} >= {"[팀] 실적 정리", "4분기 경영회의", "주간 점검", "창립 기념일"}, day
        assert "자료 검토" not in {e.title for e in day}, "다음 날 일정이 그날에 섰다"
        raises(agenda.CalendarConfigError, lambda: reader.between(DAY, DAY - timedelta(days=1)))


def check_my_calendar_only_when_exactly_one():
    for kind in ("none", "two"):
        with stage(calendars=kind) as (_, reader, _ck):
            raises(agenda.CalendarError, reader.book)


def check_login_page_and_redirect_are_session_expired():
    with stage(session="login") as (_, reader, _ck):
        raises(agenda.SessionExpired, reader.book)
    with stage(session="redirect") as (cal, reader, _ck):
        raises(agenda.SessionExpired, reader.book)
        assert len(cal.paths) == 1, f"리다이렉트를 따라갔다: {cal.paths}"
    with stage(session="denied") as (_, reader, _ck):
        raises(agenda.SessionExpired, reader.book)
    with stage(expires=time.time() - 60) as (_, reader, _ck):
        raises(agenda.SessionExpired, reader.book)                            # 시한이 지난 쿠키는 버린다


def check_only_this_hosts_cookies_are_sent():
    with stage() as (cal, reader, _):
        reader.book()
        assert cal.cookies and all(f"{COOKIE[0]}={COOKIE[1]}" in c for c in cal.cookies), cal.cookies   # 양성 대조
        assert not any(FOREIGN_COOKIE[0] in c for c in cal.cookies), "다른 호스트의 쿠키가 일정 서버에 실렸다"


def check_bad_config_rejected_before_asking():
    with tempfile.TemporaryDirectory() as tmp:
        folder = pathlib.Path(tmp)
        # 세션이 없는 판은 따로 선다 — 부르는 쪽이 「세션을 받으세요」로 이끈다(주소 · 인자 틀림과 다르다)
        raises(agenda.SessionMissing, lambda: agenda.Reader("http://127.0.0.1/x.nsf", folder / "none.json"))
        raises(agenda.SessionMissing, lambda: agenda.Reader("http://127.0.0.1/x.nsf", ""))     # 기본 자리가 없다 — 늘 넘긴다
        empty = folder / "empty.json"
        empty.write_text(json.dumps({"cookies": []}), encoding="utf-8")
        raises(agenda.SessionMissing, lambda: agenda.Reader("http://127.0.0.1/x.nsf", empty))
        ck = cookie_file(folder)
        raises(agenda.CalendarConfigError, lambda: agenda.Reader("http://127.0.0.1/calendar", ck))
        raises(agenda.CalendarConfigError, lambda: agenda.kst("2026-11-10"))
        raises(agenda.CalendarConfigError, lambda: agenda.Seen.parse("100001_20260101000001@x"))
        naive = agenda.Want("x", datetime(2026, 11, 10, 9), datetime(2026, 11, 10, 10))
        with stage() as (cal, reader, ck2):
            raises(agenda.CalendarConfigError, lambda: agenda.register(cal.url, ck2, naive, reader=reader))
            raises(agenda.CalendarConfigError, lambda: agenda.register(cal.url, ck2, want(end="2026-11-10 14:30"),
                                                                       reader=reader))
            assert not cal.paths and not cal.posts, cal.paths


# ── 넣기 ──────────────────────────────────────────────────────────────

def check_register_carries_the_form_and_reads_back():
    with stage() as (cal, reader, ck):
        got = agenda.register(cal.url, ck, want(note="3층 회의실"), reader=reader)
        assert got.state == agenda.ADDED and got.event is not None, got
        saves = [b for p, b in cal.posts if "eventquick" in p.lower()]
        assert len(saves) == 1, f"넣기 POST {len(saves)}번"
        b = saves[0]
        assert len(b) >= FORM_FIELDS, f"칸 {len(b)} < 폼 {FORM_FIELDS}"
        assert all(b.get(k) == FILLED[k] for k in ("SysAdmin", "Editors", "Readers", "Form", "TimeZoneID")), b
        assert (b["StartDate"], b["EndDate"], b["Subject"], b["Description"]) == \
            ("2026-11-10 14:30", "2026-11-10 15:00", "시험 일정", "3층 회의실"), b           # 서울 벽시계 그대로
        assert (b["CalendarID"], b["callback"], b["visibility"], b["EventArea"]) == (CALENDAR_ID, "new", "public", EVENT_AREA)
        assert not cal.changed("guests_notified"), "참석자 · 참조 칸이 찬 채 저장했다 — 남에게 알림이 간다"
        assert cal.changed("saved") == [got.event.event_id], (cal.changes, got)               # 그 일정을 다시 읽어 받았다
        assert not cal.changed("edit_opened") and not cal.changed("delete_called"), cal.changes
    with stage(form="prefilled") as (cal, reader, ck):
        got = agenda.register(cal.url, ck, want(), reader=reader)
        assert got.state == agenda.ADDED and not cal.changed("guests_notified"), \
            "폼이 채워 온 참석자 · 참조 칸을 그대로 보냈다 — 남에게 알림이 간다"
        b = [b for p, b in cal.posts if "eventquick" in p.lower()][0]
        assert (b["attAadditionalGuests"], b["refAadditionalGuests"]) == ("0", "0"), b   # 손님 수 칸은 폼 그대로


def check_register_never_adds_the_same_event_twice():
    with stage() as (cal, reader, ck):
        first = agenda.register(cal.url, ck, want(), reader=reader)
        posts = len(cal.posts)
        again = agenda.register(cal.url, ck, want(), reader=reader)
        assert (first.state, again.state) == (agenda.ADDED, agenda.ALREADY), (first, again)
        assert len(cal.posts) == posts and len(cal.changed("saved")) == 1, cal.changes
        # 같은 제목이어도 시각이 다르면 다른 일정이다 — 양성 대조
        other = agenda.register(cal.url, ck, want(start="2026-11-10 17:00", end="2026-11-10 17:30"), reader=reader)
        assert other.state == agenda.ADDED and len(cal.changed("saved")) == 2, other


def check_register_stops_on_a_clash_that_came_after_the_confirmation():
    with stage() as (cal, reader, ck):
        shown = {agenda.event_ref(e) for e in reader.between(DAY, DAY) if e.overlaps(want().start, want().end)}
        assert len(shown) == 1, shown                                             # 확인 때 보인 겹침 — 하루 종일 일정 하나
        cal.add(FakeEvent("2026-11-10 14:00", "2026-11-10 15:00", "급히 잡힌 보고", response="needsAction",
                          eventtype="Meeting"))                                   # 확인 뒤 초대가 들었다
        got = agenda.register(cal.url, ck, want(), reader=reader, shown_clash=shown)
        assert got.state == agenda.CLASHED and not cal.posts, (got, cal.posts)
        seen_now = {agenda.event_ref(e) for e in reader.between(DAY, DAY) if e.overlaps(want().start, want().end)}
        got = agenda.register(cal.url, ck, want(), reader=reader, shown_clash=seen_now)   # 그 겹침을 보이고 다시 확인받았다
        assert got.state == agenda.ADDED, got


def check_register_refuses_a_changed_form_and_cleans_the_title():
    with stage(form="changed") as (cal, reader, ck):
        raises(agenda.FormChanged, lambda: agenda.register(cal.url, ck, want(), reader=reader))
        assert not cal.posts, "잰 칸이 없는 등록 화면에 저장했다"
    with stage() as (cal, reader, ck):
        long = "가" * 70 + "\n둘째 줄​"
        got = agenda.register(cal.url, ck, want(title=long), reader=reader)
        sent = [b for _, b in cal.posts][0]["Subject"]
        assert len(sent) == 60 and "\n" not in sent and "​" not in sent, repr(sent)
        assert got.state == agenda.ADDED and got.event.title == sent, got
        assert want(title=long).cleaned().title == sent       # 확인에 보이는 꼴이 남는 꼴이다


def check_register_decides_by_reading_back_not_by_the_answer():
    # 저장하고 답 없이 끊겨도 다시 읽어 섰으면 「넣음」이다
    with stage(saves="cut") as (cal, reader, ck):
        got = agenda.register(cal.url, ck, want(), reader=reader)
        assert got.state == agenda.ADDED and got.event is not None, got
    # 폼을 버리고 잰 칸만 지어 싣는 넣기(물림) — 앱이 안 세우고 「확인 안 됨」이어야 한다(「넣음」이면 답을 믿은 것이다)

    class _Bare(agenda._Form):
        def feed(self, data):
            super().feed(data)
            self.fields = {k: self.fields[k] for k in agenda.FORM_NEEDS if k in self.fields}
    with stage() as (cal, reader, ck):
        real = agenda._Form
        agenda._Form = _Bare
        try:
            got = agenda.register(cal.url, ck, want(), reader=reader)
        finally:
            agenda._Form = real
        assert got.state == agenda.UNSURE and not cal.changed("saved"), got


# ── 지우기 ────────────────────────────────────────────────────────────

def check_delete_own_single_entry_and_read_back():
    with stage() as (cal, reader, ck):
        own = by_title(reader, "[팀] 실적 정리")
        assert own.keep_reason == "", own.keep_reason
        handle = agenda.Seen.of(own).handle
        assert "100001" not in handle, "손잡이에 사번이 든다"
        got = agenda.delete(cal.url, ck, agenda.Seen.parse(handle), reader=reader)
        assert got.state == agenda.DELETED, got
        assert cal.changed("deleted") == [own.event_id] and len(cal.changed("delete_called")) == 1, cal.changes
        assert "[팀] 실적 정리" not in {e.title for e in reader.between(DAY, DAY)}
        again = agenda.delete(cal.url, ck, own, reader=reader)
        assert again.state == agenda.GONE and len(cal.changed("delete_called")) == 1, (again, cal.changes)
        assert not cal.changed("edit_opened"), "편집 화면을 열었다"


def check_delete_only_what_was_shown():
    with stage() as (cal, reader, ck):
        own = by_title(reader, "[팀] 실적 정리")
        seen = agenda.Seen.of(own)
        fake = next(e for e in cal.events if e.event_id == own.event_id)
        fake.title = "[팀] 실적 정리 — 고침"                                         # 보인 뒤 제목이 바뀌었다
        got = agenda.delete(cal.url, ck, seen, reader=reader)
        assert got.state == agenda.CHANGED and got.event.title == fake.title, got
        fake.title, fake.start = own.title, "2026-11-10 09:10"                        # 보인 뒤 같은 날 시각이 옮겨졌다
        got = agenda.delete(cal.url, ck, seen, reader=reader)
        assert got.state == agenda.CHANGED and got.event.when() == "09:10–09:30", got
        fake.start, fake.end = "2026-11-12 09:00", "2026-11-12 09:30"                 # 다른 날로 옮겨졌다 — 그날에 없다
        got = agenda.delete(cal.url, ck, seen, reader=reader)
        assert got.state == agenda.GONE, got
        assert not cal.changed("delete_called"), f"보인 것과 다른 줄에 지우기를 불렀다: {cal.changes}"


def check_delete_refuses_what_is_not_a_hand_made_single():
    cases = {"4분기 경영회의": agenda.KEEP_INVITE, "협력사 면담": agenda.KEEP_MEETING, "주간 점검": agenda.KEEP_REPEAT,
             "창립 기념일": agenda.KEEP_ALL_DAY, "보안 교육": agenda.KEEP_LOCKED}
    with stage() as (cal, reader, ck):
        for title, reason in cases.items():
            e = by_title(reader, title)
            exc = raises(agenda.ChangeRefused, lambda e=e: agenda.delete(cal.url, ck, agenda.Seen.of(e), reader=reader))
            assert exc.reason == reason, (title, exc.reason)
        assert not cal.changed("delete_called"), f"지우지 않는 줄에 지우기를 불렀다: {cal.changes}"
        # 물림 — 까닭을 안 보는 지우기면 받은 초대가 지워진다(판정이 빨개져야 한다)
        real = agenda.Event.keep_reason
        agenda.Event.keep_reason = property(lambda self: "")
        try:
            invite = by_title(reader, "4분기 경영회의")
            agenda.delete(cal.url, ck, invite, reader=reader)
        finally:
            agenda.Event.keep_reason = real
        assert cal.changed("deleted"), "물림이 안 물었다 — 까닭을 푼 지우기에도 초대가 남았다"


def check_delete_decides_by_reading_back_not_by_the_answer():
    with stage(deletes="ignore") as (cal, reader, ck):
        got = agenda.delete(cal.url, ck, by_title(reader, "[팀] 실적 정리"), reader=reader)
        assert got.state == agenda.UNSURE, got                                   # 답은 같은데 남았다
    with stage(deletes="cut") as (cal, reader, ck):
        got = agenda.delete(cal.url, ck, by_title(reader, "[팀] 실적 정리"), reader=reader)
        assert got.state == agenda.DELETED, got                                  # 답 없이 끊겨도 사라졌으면 지움


def check_shared_calendars_ask_only_their_event_address():
    with stage() as (cal, reader, _):
        books = reader.shared_books()
        assert [(b.kind, b.name, b.db_path) for b in books] == [(v[0], v[2], v[3]) for v in SHARED.values()], books
        got = [e for b in books for e in reader.between(DAY, DAY, b)]
        assert not changing(cal.paths) and not cal.changes, (cal.paths, cal.changes)
        asked = sorted({urllib.parse.unquote(p).split("?")[0] for p in cal.paths if "getcalendarevent" in p})
        assert asked == sorted(v[3] + "/getcalendarevent" for v in SHARED.values()), asked   # 양성 대조 — 그 일정함 자리에 물었다
        assert len(got) == 4 and {e.calendar for e in got} == {v[2] for v in SHARED.values()}, got   # 주인 이름으로 물어 줄이 왔다
        assert all(e.keep_reason == agenda.KEEP_SHARED for e in got), [e.keep_reason for e in got]
        assert [e.private for e in got if e.title.endswith("병원 진료")] == [True, True], got
        assert all(not e.calendar for e in reader.between(DAY, DAY)), "내 일정함의 줄에 공유 일정함 이름이 붙었다"
        server = reader._shared_server(books[0].server)
        for path in (f"{books[0].db_path}/vweventprev/00000000000000000000000000000001?editdocument",
                     f"{books[0].db_path}/(wEventDelete)?openagent&calendarId=200001_Calendar&eventId=x"):
            raises(agenda.ChangeRefused, lambda p=path: reader._get_shared(server, p))
        assert not cal.changes, cal.changes


def check_shared_calendar_outside_the_company_domain_is_not_asked():
    with stage(calendars="outside") as (cal, reader, _):
        outside = next(b for b in reader.shared_books() if b.server == OUTSIDE_HOST)
        opened: list[str] = []
        real = reader._open
        reader._open = lambda url, data=None: (opened.append(url), real(url, data))[1]
        raises(agenda.CalendarError, lambda: reader.between(DAY, DAY, outside))
        assert not opened, f"사내 밖 서버에 물었다: {opened}"

        class OpenGate(agenda.Reader):          # 물림 — 도메인 문을 푼 손은 밖 서버에 묻는다
            def _shared_server(self, host):
                return "http://" + host
        loose = OpenGate(cal.url, _, timeout=1)
        tried: list[str] = []
        loose._open = lambda url, data=None: tried.append(url) or (b"", "")
        with contextlib.suppress(agenda.CalendarError):
            loose.between(DAY, DAY, outside)
        assert tried and OUTSIDE_HOST in tried[0], "물림이 안 물었다 — 문을 푼 손도 밖 서버에 안 물었다"


def check_shared_row_is_never_deleted():
    # 공유 줄과 같은 열쇠 · 시각 · 제목의 손수 든 단건이 내 일정함에도 있다 — 공유 줄의 손잡이로 그 줄을 지우지 않는다
    with stage() as (cal, reader, ck):
        row = reader.between(DAY, DAY, reader.shared_books()[0])[0]
        twin = cal.add(FakeEvent(f"{row.start.astimezone(KST):%Y-%m-%d %H:%M}", f"{row.end.astimezone(KST):%Y-%m-%d %H:%M}",
                                 row.title, event_id=row.event_id))
        assert any(agenda.event_ref(e) == agenda.event_ref(row) and not e.keep_reason for e in reader.between(DAY, DAY)), \
            "판이 안 섰다 — 내 일정함에 같은 열쇠의 지울 수 있는 줄이 없다"
        for target in (row, agenda.Seen.of(row)):
            exc = raises(agenda.ChangeRefused, lambda t=target: agenda.delete(cal.url, ck, t, reader=reader))
            assert exc.reason == agenda.KEEP_SHARED, exc.reason
        assert not cal.changed("delete_called") and twin in cal.events, cal.changes


def check_shared_server_stays_in_the_company_domain():
    with stage() as (_, reader, ck):
        company = agenda.Reader("http://pcfca03.posco.net/02/cal/calperson32.nsf", ck)
        assert company._shared_server("pcfca01.posco.net") == "http://pcfca01.posco.net"     # 다른 사내 서버
        assert company._shared_server("PCFCA03.posco.net:8080") == "http://pcfca03.posco.net:8080"
        for host in ("evilposco.net", "posco.net.evil.example", "u@pcfca01.posco.net", "pcfca01.posco.net.",
                     "10.0.0.1", "", "pcfca01..posco.net"):
            raises(agenda.CalendarError, lambda h=host: company._shared_server(h))
        local = reader._shared_server(urllib.parse.urlsplit(reader.url).netloc)              # 이름표 없는 호스트는 제 자리만
        assert local == reader.server, local
        raises(agenda.CalendarError, lambda: reader._shared_server("pcfca01.posco.net"))


def check_added_event_can_be_deleted_by_its_handle():
    with stage() as (cal, reader, ck):
        got = agenda.register(cal.url, ck, want(), reader=reader)
        assert got.event is not None and got.event.keep_reason == "", got        # 넣은 줄은 손수 든 단건이다
        gone = agenda.delete(cal.url, ck, agenda.Seen.parse(agenda.Seen.of(got.event).handle), reader=reader)
        assert gone.state == agenda.DELETED and cal.changed("deleted") == cal.changed("saved"), (gone, cal.changes)


CHECKS = [value for name, value in sorted(globals().items()) if name.startswith("check_")]


def main() -> int:
    print(f"잰다: {TREE / 'agenda.py'}")
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
