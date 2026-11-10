"""회의실 예약 스킬의 얇은 명령 — 곁의 손(``mrs.py``)으로 회의실 · 빈 곳 · 내 예약을 보고, 한 건을 넣고 · 고치고 · 취소한다.

부르는 꼴::

    python -X utf8 -I meeting_room.py rooms [말]                                  # 회의실 찾기 — 이름 · 지역 · 건물 · 층의 일부
    python -X utf8 -I meeting_room.py free  --start "YYYY-MM-DD HH:MM" --end "…" [--where 말] [--people N]   # 그 시각에 빈 회의실
    python -X utf8 -I meeting_room.py day   <회의실> [오늘|내일|YYYY-MM-DD]          # 그 회의실의 그날 예약
    python -X utf8 -I meeting_room.py mine  [오늘|YYYY-MM-DD] [끝 날]               # 내 예약(기본 오늘부터 14일)
    python -X utf8 -I meeting_room.py preview --room R --title T --start S --end E [--to 메일 …] [--note N] [--id 예약]   # 안 바꾼다
    python -X utf8 -I meeting_room.py book    …preview 와 같은 값… --seen <preview 의 seen>                              # ⚠ 넣는다
    python -X utf8 -I meeting_room.py change  --id 예약 …바꿀 값만… --seen <preview --id 의 seen>                        # ⚠ 고친다
    python -X utf8 -I meeting_room.py cancel  <예약 id>                                                                  # ⚠ 취소한다

    시각은 다 서울 벽시계다. ``--room`` 은 회의실 id 나 이름의 일부(한 곳만 걸려야 한다). ``--to`` 는 참석자 메일 주소 — 사람은
    스킬 company-mail 의 people · org 로 정하고 그 주소를 넘긴다. ``change`` 에 ``--to`` 를 주면 참석자 목록을 통째로 바꾼다.

하는 일 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 로 사내 세션을 쥐고(보기는 있는 파일부터, 바꾸기는 늘 받는 손부터
한 번만), 그 세션으로 회의실 예약 앱의 출입증을 받아 부른다. 판단(무엇을 넣을까 · 사람이 확인했나)은 여기 없다 — 바꾸는 명령은
사람이 그 한 건을 확인한 뒤에만 부른다(SKILL.md). 앱의 미리 검사는 정책만 보아, 겹침 · 지난 시각은 여기서 가린다.

내는 것 — 표준 출력에 JSON 하나. 종료 값: 0 됐다 · 1 도구 · 앱 고장(그대로 알린다) · 2 인자가 틀렸다(회의실이 여럿 걸림 등 —
``message`` 가 후보를 든다) · 3 사내 세션이 없다 · 끊겼다(스킬 ep-login). 0 이 아니면 ``message`` 가 까닭과 「다음: …」 을 든다.
``preview`` 는 ``ok``(넣을 수 있나) · ``blocks``(못 넣는 까닭) · ``notes``(넣을 수는 있으나 사람이 알아야 할 것) · ``seen`` 을 낸다.
바꾸는 명령의 끝은 ``state`` 와 사람에게 할 말 · 다음 걸음이 든 ``state_word`` 다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import date, datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
KST = timezone(timedelta(hours=9))
WEEKDAYS = "월화수목금토일"
DAY_WORDS = {"오늘": 0, "today": 0, "내일": 1, "tomorrow": 1, "모레": 2}
MINE_DAYS = 14                            # mine 의 기본 구간 — 오늘부터 두 주
MOST_ROOMS = 60                           # rooms 답에 싣는 회의실 수 — count 는 다 센 수다
MOST_FREE = 40                            # free 답에 싣는 빈 회의실 수
MOST_CANDIDATES = 15                      # 회의실이 여럿 걸릴 때 message 에 보이는 후보 수
LIVE = ("confirmed", "pending_approval")  # 회의실을 쥔 예약의 상태 — cancelled · rejected 는 비운 것이다
STATUS_WORDS = {"confirmed": "확정", "pending_approval": "승인 대기", "cancelled": "취소됨", "rejected": "거절됨"}
EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION = 0, 1, 2, 3
MUTATING = ("book", "change", "cancel")
NEXT_EP_LOGIN = "다음: 스킬 ep-login 으로 사내 세션을 세운 뒤 같은 명령을 다시 부른다"
STATE_WORDS = {
    "booked": "예약했습니다(내 예약에서 다시 읽어 확인했습니다). 참석자께는 회의 안내가 회사 메일로 갑니다 — 조금 걸릴 수 있습니다. "
              "다음: 이 줄의 id 를 들고 있다가 「방금 것 취소 · 시간 바꿔 줘」에 쓴다",
    "pending": "넣었지만 이 회의실은 승인이 필요해 「승인 대기」입니다 — 승인되면 확정됩니다",
    "changed": "고쳤습니다(다시 읽어 확인했습니다). 참석자께는 바뀐 안내가 갑니다",
    "cancelled": "취소했습니다(내 예약에서 사라진 것을 확인했습니다). 참석자께는 취소 안내가 갑니다",
    "gone": "내 예약에 그 예약이 없습니다 — 이미 취소됐거나 id 가 틀렸습니다. 다음: mine 으로 내 예약을 읽어 보인다",
    "not_mine": "내가 주관한 예약이 아니라 고치거나 취소하지 않습니다 — 주관하신 분께 부탁하거나 회의실 예약 화면에서 해 주세요",
    "series": "반복 예약입니다 — 여기서는 반복을 다루지 않습니다. 회의실 예약 화면에서 해 주세요",
    "moved": "보여 드린 뒤 그 사이에 바뀐 것이 있어 넣지 않았습니다. 다음: 답의 preview(지금 꼴)를 보이고 다시 묻는다",
    "blocked": "넣을 수 없습니다 — 답의 blocks 를 그대로 전한다",
    "unsure": "됐는지 확인하지 못했습니다. 다음: 다시 부르지 말고 mine 으로 읽어 보인다",
}


class Stop(Exception):
    def __init__(self, code: int, kind: str, message: str):
        super().__init__(message)
        self.code, self.kind = code, kind


def load(name: str, where: pathlib.Path):
    """곁의 모듈을 싣는다 — ``-I`` 로 돌면 그 폴더가 ``sys.path`` 에 없어 넣고 싣는다."""
    if str(where) not in sys.path:
        sys.path.insert(0, str(where))
    try:
        return __import__(name)
    except ImportError as exc:
        raise Stop(EXIT_TOOL, "tool", f"{name} 를 못 실었다({where}) — 설치를 다시 돌린다") from exc


# ── 시각 ────────────────────────────────────────────────────────────────
def kst(text: str) -> datetime:
    try:
        t = datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise Stop(EXIT_ARGS, "args", f"시각은 「YYYY-MM-DD HH:MM」(서울)으로 준다: {text!r}") from exc
    return t.replace(tzinfo=KST)


def iso(t: datetime) -> str:
    return t.astimezone(KST).isoformat(timespec="seconds")


def utc(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def parse_app(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(KST)


def day_of(text: str | None, today: date) -> date:
    word = (text or "오늘").strip().lower()
    if word in DAY_WORDS:
        return today + timedelta(days=DAY_WORDS[word])
    try:
        return date.fromisoformat(word)
    except ValueError as exc:
        raise Stop(EXIT_ARGS, "args", f"날은 오늘 · 내일 · 모레 · YYYY-MM-DD 가운데 하나로 준다: {text!r}") from exc


def day_span(first: date, last: date) -> tuple[str, str]:
    """서울 하루(들)의 처음과 끝을 앱이 받는 UTC 로 — 앱은 날짜만 주면 UTC 하루로 읽는다."""
    a = datetime.combine(first, datetime.min.time(), KST)
    b = datetime.combine(last + timedelta(days=1), datetime.min.time(), KST) - timedelta(milliseconds=1)
    return utc(a), b.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.999Z")


def when(start: datetime, end: datetime) -> str:
    s, e = start.astimezone(KST), end.astimezone(KST)
    head = f"{s:%m월 %d일}({WEEKDAYS[s.weekday()]}) {s:%H:%M}"
    return f"{head}–{e:%H:%M}" if s.date() == e.date() else f"{head} – {e:%m월 %d일}({WEEKDAYS[e.weekday()]}) {e:%H:%M}"


# ── 회의실 ──────────────────────────────────────────────────────────────
class Places:
    """층 id → 「지역 건물 층」 과 회사 id. ``rooms`` 의 회의실에는 층 · 건물의 이름이 없어 나무에서 받는다."""

    def __init__(self, hierarchy: list):
        self.where, self.company = {}, {}
        for co in hierarchy:
            for loc in co.get("locations", []):
                for b in loc.get("buildings", []):
                    for f in b.get("floors", []):
                        self.where[f["id"]] = f"{loc.get('name', '')} {b.get('name', '')} {f.get('name', '')}".strip()
                        self.company[f["id"]] = co.get("id", "")

    def of(self, room: dict) -> str:
        return self.where.get(room.get("floor_id"), "")


def room_row(room: dict, places: Places) -> dict:
    perm = (room.get("policy") or {}).get("reservation_permission") or {}
    teams = (room.get("policy") or {}).get("teams_integration") or {}
    return {"id": room["id"], "name": room["name"], "where": places.of(room), "capacity": room.get("capacity"),
            "type": room.get("room_type"), "approval": bool(perm.get("require_approval")),
            "bookable": bool(perm.get("user_can_reserve", True)) and bool(room.get("is_active", True)),
            "teams_link": bool(teams.get("meeting_link"))}


def find_rooms(rooms: list, places: Places, word) -> list:
    """이름 · 지역 · 건물 · 층에 낱말이 다 든 회의실 — 낱말은 문자열이나 그 목록이다."""
    keys = (" ".join(word) if isinstance(word, (list, tuple)) else (word or "")).lower().split()
    if not keys:
        return rooms
    return [r for r in rooms if all(k in f"{places.of(r)} {r['name']}".lower() for k in keys)]


def one_room(rooms: list, places: Places, word: str) -> dict:
    exact = [r for r in rooms if r["id"] == word]
    got = exact or find_rooms(rooms, places, word)
    if len(got) == 1:
        return got[0]
    if not got:
        raise Stop(EXIT_ARGS, "args", f"「{word}」에 걸리는 회의실이 없다. 다음: rooms 로 찾아 보인다")
    named = [r for r in got if r["name"] == word]
    if len(named) == 1:
        return named[0]
    listed = "; ".join(f"{places.of(r)} {r['name']} ({r['id']})" for r in got[:MOST_CANDIDATES])
    raise Stop(EXIT_ARGS, "args", f"「{word}」에 회의실이 {len(got)} 곳 걸린다 — {listed}. 다음: 사람에게 고르게 하고 그 id 로 다시 부른다")


# ── 예약 ────────────────────────────────────────────────────────────────
def live(r: dict) -> bool:
    return r.get("status") in LIVE


def overlaps(r: dict, start: datetime, end: datetime) -> bool:
    return parse_app(r["start_time"]) < end and start < parse_app(r["end_time"])


def person(p) -> str:
    if isinstance(p, dict):
        return p.get("display_name") or p.get("name") or p.get("email") or ""
    return str(p or "")


def booking_row(r: dict, me_id: str = "", names: dict | None = None) -> dict:
    org = r.get("organizer_id")
    out = {"id": r["id"], "title": r.get("title", ""), "when": when(parse_app(r["start_time"]), parse_app(r["end_time"])),
           "rooms": r.get("room_names") or [x.get("name") for x in r.get("rooms", [])] or [(names or {}).get(i, i) for i in r.get("room_ids", [])],
           "status": STATUS_WORDS.get(r.get("status"), r.get("status")), "organizer": person(org),
           "mine": mine_to_change(r, me_id)}
    att = r.get("attendees")
    if att:
        out["attendees"] = [person(a.get("employee_id")) or a.get("email") for a in att]
    if (r.get("teams_meeting") or {}).get("join_url"):
        out["teams"] = True
    return out


def fingerprint(*parts) -> str:
    """보여 준 판의 지문 — 사람이 본 것과 넣을 때의 판(겹침 · 고칠 예약의 꼴)이 같은지 가린다."""
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:16]


def attendees_of(app, emails: list[str]) -> tuple[list, list]:
    """참석자 메일 → 앱의 참석자 꼴과 못 찾은 주소. 앱 사람 목록에서 같은 주소(대소문자 무시)의 한 사람만 잇는다."""
    if not emails:
        return [], []
    by_mail = {}
    for u in app.directory():
        by_mail.setdefault(str(u.get("email", "")).lower(), u)
    got, missing = [], []
    for m in dict.fromkeys(e.strip() for e in emails if e.strip()):
        u = by_mail.get(m.lower())
        if u:
            got.append({"employee_id": u["id"], "email": u["email"], "name": person(u)})
        else:
            missing.append(m)
    return got, missing


def kept_attendees(r: dict) -> list:
    out = []
    for a in r.get("attendees") or []:
        emp = a.get("employee_id")
        row = {"email": a.get("email"), "name": person(emp) or a.get("email")}
        if isinstance(emp, dict) and emp.get("id"):
            row["employee_id"] = emp["id"]
        elif isinstance(emp, str) and emp:
            row["employee_id"] = emp
        out.append(row)
    return out


def body_of(me: dict, room_ids: list, title: str, note: str, start: datetime, end: datetime, attendees: list,
            base: dict | None = None) -> dict:
    """앱의 화면이 넣기 · 고치기에 보내는 꼴 그대로. 참석자는 ``employee_id`` · ``email`` 만 싣는다."""
    return {"company_id": (base or {}).get("company_id") or me["company_id"], "organizer_id": me["id"], "title": title,
            "user_description": note, "start_time": iso(start), "end_time": iso(end),
            "attendees": [{k: a[k] for k in ("employee_id", "email") if a.get(k)} for a in attendees],
            "room_ids": room_ids, "status": (base or {}).get("status") or "confirmed",
            "teams_link_visibility": (base or {}).get("teams_link_visibility") or "private"}


def cross_company(room: dict, places: Places, me: dict) -> bool:
    """남의 회사 회의실인데 그 회사가 타사 예약을 안 받는다 — 앱의 미리 검사도 같은 까닭으로 막는다."""
    owner = places.company.get(room.get("floor_id"))
    allow = ((room.get("policy") or {}).get("reservation_restrictions") or {}).get("allow_cross_tenant_reservation")
    return bool(owner) and owner != me.get("company_id") and not allow


def mine_to_change(r: dict, me_id: str) -> bool:
    """내가 주관한 예약인가 — 앱의 ``isOrganizer`` 가 있으면 그것, 없으면 주관자 id 를 견준다. 모르면 거짓이다."""
    if "isOrganizer" in r:
        return r["isOrganizer"] is True
    org = r.get("organizer_id")
    return bool(me_id) and (org.get("id") if isinstance(org, dict) else org) == me_id


def is_series(r: dict) -> bool:
    """반복 예약인가 — 앱의 화면이 반복을 싣는 두 칸(``is_recurring`` · ``recurring_end_date``)으로 가린다."""
    return bool(r.get("is_recurring")) or bool(r.get("recurring_end_date"))


# ── 미리 보기 — 넣기 · 고치기가 같은 판을 다시 짓는다 ─────────────────────
def plan(app, args, me: dict, now: datetime) -> dict:
    """넣을(고칠) 한 건의 꼴과 막는 까닭 · 알릴 것 · 지문. 바꾸지 않는다."""
    rooms, places = app.rooms(), Places(app.hierarchy())
    base = None
    if args.id:
        base = reread(app, args.id)
        if base is None:
            return {"state": "gone"}
        if not mine_to_change(base, me["id"]):
            return {"state": "not_mine"}
        if is_series(base):
            return {"state": "series"}
    room = one_room(rooms, places, args.room) if args.room else None
    room_ids = [room["id"]] if room else list(base.get("room_ids") or [])
    start = kst(args.start) if args.start else parse_app(base["start_time"])
    end = kst(args.end) if args.end else parse_app(base["end_time"])
    title = (args.title if args.title is not None else (base or {}).get("title", "")).strip()
    note = args.note if args.note is not None else (base or {}).get("user_description", "")
    if args.to is not None:
        attendees, missing = attendees_of(app, args.to)
    else:
        attendees, missing = (kept_attendees(base) if base else []), []
    blocks, notes = [], []
    if not title:
        blocks.append("제목이 비었다")
    if end <= start:
        blocks.append("끝이 시작보다 앞이다")
    if start < now:
        blocks.append("지난 시각이다 — 회의실 예약 앱은 지난 시각도 받지만 여기서는 넣지 않는다")
    by_id = {r["id"]: r for r in rooms}
    for rid in room_ids:
        r = by_id.get(rid)
        if r is None:
            blocks.append(f"회의실 {rid} 가 목록에 없다")
            continue
        row = room_row(r, places)
        if not row["bookable"]:
            blocks.append(f"{row['name']}: 일반 사용자가 예약할 수 없는 회의실이다")
        if cross_company(r, places, me):
            blocks.append(f"{row['name']}: 다른 회사 회의실이라 예약할 수 없다")
        if row["approval"]:
            notes.append(f"{row['name']}: 승인이 필요한 회의실 — 넣으면 「승인 대기」로 들어간다")
        if row["capacity"] and len(attendees) + 1 > row["capacity"]:
            notes.append(f"{row['name']}: 정원 {row['capacity']} 명인데 참석자가 주관자 포함 {len(attendees) + 1} 명이다")
        if row["teams_link"]:
            notes.append(f"{row['name']}: 이 회의실 정책으로 Teams 회의 링크가 저절로 붙는다")
    clash = []
    if end > start:
        a, b = utc(start), utc(end)
        clash = [x for x in app.between(a, b) if live(x) and x["id"] != args.id
                 and set(x.get("room_ids", [])) & set(room_ids) and overlaps(x, start, end)]
        for x in clash:
            blocks.append(f"그 시각에 이미 예약이 있다 — {when(parse_app(x['start_time']), parse_app(x['end_time']))} "
                          f"「{x.get('title', '')}」({person(x.get('organizer_id'))})")
        if not blocks:
            v = app.validate(room_ids, iso(start), iso(end), args.id)
            blocks += [e.get("message", str(e)) for e in v.get("errors", [])]
            if v.get("approvalRequiredRoomIds") and not any("승인" in n for n in notes):
                notes.append("승인이 필요한 회의실이 들었다 — 넣으면 「승인 대기」로 들어간다")
    if missing:
        blocks.append("회의실 예약 앱의 사람 목록에 없는 주소: " + ", ".join(missing))
    if not attendees:
        notes.append("참석자가 없다 — 회의실만 잡히고 누구에게도 안내가 안 간다")
    body = body_of(me, room_ids, title, note, start, end, attendees, base)
    names = [f"{places.of(by_id[r])} {by_id[r]['name']}".strip() for r in room_ids if r in by_id]
    seen = fingerprint(body, sorted(x["id"] + x.get("updated_at", "") for x in clash), (base or {}).get("updated_at"))
    return {"state": "ready" if not blocks else "blocked", "ok": not blocks, "title": title, "note": note,
            "when": when(start, end), "rooms": names, "attendees": [a["name"] for a in attendees],
            "blocks": blocks, "notes": notes, "seen": seen, "body": body,
            "was": booking_row(base, me["id"]) if base else None}


def shown(p: dict) -> dict:
    """사람에게 보일 판 — 앱에 보낼 몸통(``body``)은 뺀다."""
    return {k: v for k, v in p.items() if k != "body" and v not in (None, [], "")}


def reread(app, rid: str):
    """내 예약에서 그 id 의 살아 있는 예약 — 취소 · 거절된 줄은 없는 것으로 본다."""
    return next((r for r in app.mine() if r["id"] == rid and live(r)), None)


def run(args, session: pathlib.Path) -> dict:
    mrs = load("mrs", HERE)
    app = mrs.App(session)
    now = datetime.now(KST)
    today = now.date()
    me = app.me()
    if args.command == "rooms":
        places = Places(app.hierarchy())
        got = [room_row(r, places) for r in find_rooms(app.rooms(), places, args.word)]
        return {"count": len(got), "rooms": got[:MOST_ROOMS], "cut": len(got) > MOST_ROOMS}
    if args.command == "free":
        start, end = kst(args.start), kst(args.end)
        if end <= start:
            raise Stop(EXIT_ARGS, "args", "끝이 시작보다 앞이다")
        places = Places(app.hierarchy())
        cand = [r for r in find_rooms(app.rooms(), places, args.where)
                if room_row(r, places)["bookable"] and not cross_company(r, places, me)
                and (not args.people or (r.get("capacity") or 0) >= args.people)]
        busy = {rid for x in app.between(utc(start), utc(end)) if live(x) and overlaps(x, start, end) for rid in x.get("room_ids", [])}
        free = [room_row(r, places) for r in cand if r["id"] not in busy]
        return {"when": when(start, end), "count": len(free), "rooms": free[:MOST_FREE], "cut": len(free) > MOST_FREE}
    if args.command == "day":
        places = Places(app.hierarchy())
        room = one_room(app.rooms(), places, args.room)
        d = day_of(args.day, today)
        a, b = day_span(d, d)
        lo, hi = datetime.combine(d, datetime.min.time(), KST), datetime.combine(d + timedelta(days=1), datetime.min.time(), KST)
        rows = sorted((x for x in app.between(a, b) if live(x) and room["id"] in x.get("room_ids", []) and overlaps(x, lo, hi)),
                      key=lambda x: x["start_time"])
        return {"room": room_row(room, places), "day": d.isoformat(), "weekday": WEEKDAYS[d.weekday()],
                "bookings": [booking_row(x, me["id"], {room["id"]: room["name"]}) for x in rows]}
    if args.command == "mine":
        first = day_of(args.first, today)
        last = day_of(args.last, today) if args.last else first + timedelta(days=MINE_DAYS)
        lo = datetime.combine(first, datetime.min.time(), KST)
        hi = datetime.combine(last + timedelta(days=1), datetime.min.time(), KST)
        rows = sorted((x for x in app.mine() if overlaps(x, lo, hi)), key=lambda x: x["start_time"])
        return {"today": today.isoformat(), "today_weekday": WEEKDAYS[today.weekday()], "first": first.isoformat(),
                "last": last.isoformat(), "bookings": [booking_row(x, me["id"]) for x in rows]}
    if args.command == "cancel":
        base = reread(app, args.rid)
        if base is None:
            return {"state": "gone", "state_word": STATE_WORDS["gone"]}
        if not mine_to_change(base, me["id"]):
            return {"state": "not_mine", "state_word": STATE_WORDS["not_mine"]}
        if is_series(base):
            return {"state": "series", "state_word": STATE_WORDS["series"]}
        app.delete(args.rid)
        try:
            state = "cancelled" if reread(app, args.rid) is None else "unsure"
        except Exception:  # noqa: BLE001 — 지운 뒤라 어떤 실패도 다시 부를 까닭이 아니다
            state = "unsure"
        return {"state": state, "state_word": STATE_WORDS[state], "booking": booking_row(base, me["id"])}
    p = plan(app, args, me, now)
    if p["state"] in ("gone", "not_mine", "series"):
        return {"state": p["state"], "state_word": STATE_WORDS[p["state"]]}
    if args.command == "preview":
        return shown(p)
    if p["seen"] != args.seen:
        return {"state": "moved", "state_word": STATE_WORDS["moved"], "preview": shown(p)}
    if not p["ok"]:
        return {"state": "blocked", "state_word": STATE_WORDS["blocked"], "blocks": p["blocks"]}
    try:
        got = app.update(args.id, p["body"]) if args.id else app.create(p["body"])
    except mrs.AppError as exc:
        if exc.status is not None:   # 앱이 답으로 거절했다 — 안 바뀌었다
            raise
        return settle(app, args, me, args.id)   # 답 전에 끊겼다 — 들어갔을 수 있어 다시 부르지 않고 읽어 본다
    return settle(app, args, me, (got or {}).get("id") or args.id)


def settle(app, args, me: dict, rid: str | None) -> dict:
    """바꾼 뒤의 끝 — 앱이 받은 뒤라 다시 읽기가 무엇으로 지든 「모른다」다. 세션 · 도구 오류로 올리면 다시 부르라는 말이 되어 두 번 든다."""
    try:
        back = reread(app, rid) if rid else None
    except Exception:  # noqa: BLE001 — 바꾼 뒤라 어떤 실패도 다시 부를 까닭이 아니다
        back = None
    if back is None:
        return {"state": "unsure", "state_word": STATE_WORDS["unsure"]}
    state = "changed" if args.id else ("pending" if back.get("status") == "pending_approval" else "booked")
    return {"state": state, "state_word": STATE_WORDS[state], "booking": booking_row(back, me["id"])}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="회의실 예약 — 보기 · 넣기 · 고치기 · 취소")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("rooms", help="회의실 찾기(바꾸지 않는다)")
    r.add_argument("word", nargs="*", help="이름 · 지역 · 건물 · 층의 일부(빈칸으로 여럿)")
    f = sub.add_parser("free", help="그 시각에 빈 회의실(바꾸지 않는다)")
    f.add_argument("--start", required=True, help="YYYY-MM-DD HH:MM(서울)")
    f.add_argument("--end", required=True)
    f.add_argument("--where", nargs="*", help="지역 · 건물 · 층 · 이름의 일부")
    f.add_argument("--people", type=int, help="주관자 포함 인원 — 정원이 이보다 작은 곳은 뺀다")
    d = sub.add_parser("day", help="한 회의실의 그날 예약(바꾸지 않는다)")
    d.add_argument("room")
    d.add_argument("day", nargs="?")
    m = sub.add_parser("mine", help="내 예약(바꾸지 않는다)")
    m.add_argument("first", nargs="?")
    m.add_argument("last", nargs="?")
    for name, text in (("preview", "넣을 · 고칠 꼴 미리 보기(바꾸지 않는다)"), ("book", "⚠ 한 건 넣기"), ("change", "⚠ 한 건 고치기")):
        a = sub.add_parser(name, help=text)
        a.add_argument("--id", required=name == "change", help="고칠 예약 id(preview 에 주면 고치기 미리 보기)")
        a.add_argument("--room", required=name == "book", help="회의실 id 나 이름의 일부")
        a.add_argument("--title", required=name == "book")
        a.add_argument("--start", required=name == "book", help="YYYY-MM-DD HH:MM(서울)")
        a.add_argument("--end", required=name == "book")
        a.add_argument("--note", default=None, help="회의 설명")
        a.add_argument("--to", nargs="*", default=None, help="참석자 메일 주소(고치기에 주면 통째로 바꾼다)")
        if name != "preview":
            a.add_argument("--seen", required=True, help="preview 답의 seen — 사람이 본 판")
    c = sub.add_parser("cancel", help="⚠ 한 건 취소")
    c.add_argument("rid")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.command == "preview" and not args.id:
        missing = [k for k in ("room", "title", "start", "end") if getattr(args, k) is None]
        if missing:
            print(json.dumps({"error": "args", "message": "새 예약 미리 보기에는 --" + " · --".join(missing) + " 가 든다"}, ensure_ascii=False))
            return EXIT_ARGS
    try:
        mrs, ep = load("mrs", HERE), load("ep_session", EP_LOGIN_SCRIPTS)
        try:
            result = ep.session_first(lambda f: run(args, f), expired=(mrs.SessionExpired, mrs.SessionMissing),
                                      file_first=args.command not in MUTATING)
            code = EXIT_OK
        except ep.NoSession as exc:
            tail = (exc.got.said.splitlines() or [""])[-1]
            if exc.got.code in (ep.NO_EDGE, ep.NOT_LOGGED_IN):
                raise Stop(EXIT_SESSION, "session", f"사내 세션이 없다 — {tail}. {NEXT_EP_LOGIN}") from exc
            raise Stop(EXIT_TOOL, "tool", f"세션 손이 종료 {exc.got.code} 로 졌다 — {tail}") from exc
    except Stop as exc:
        result, code = {"error": exc.kind, "message": str(exc)}, exc.code
    except Exception as exc:  # noqa: BLE001 — 손의 예외를 종료 값으로 옮긴다
        mrs = sys.modules.get("mrs")
        if mrs and isinstance(exc, (mrs.SessionExpired, mrs.SessionMissing)):
            result, code = {"error": "session", "message": f"{exc}. {NEXT_EP_LOGIN}"}, EXIT_SESSION
        elif mrs and isinstance(exc, mrs.AppError):
            result, code = {"error": "tool", "message": str(exc)}, EXIT_TOOL
        else:
            result, code = {"error": "tool", "message": f"{type(exc).__name__}: {exc}"}, EXIT_TOOL
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return code


if __name__ == "__main__":
    sys.exit(main())
