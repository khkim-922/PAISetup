"""meeting_room.py · mrs.py 의 계약을 가짜 SSO · 가짜 회의실 앱으로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 넣기 · 고치기 · 취소는 참석자에게 회사 메일로 안내를 보내고 되돌릴 수 없다. 앱의 미리 검사는 겹침 · 지난 시각을
안 보아, 명령이 그것을 가리지 않으면 지난 시각 · 겹친 예약이 조용히 들어가 남에게 안내가 간다. 보여 준 판과 다른 판이 들어가거나, 남이
주관한 예약을 취소하거나, 다시 읽지 않고 「넣었습니다」라고 하는 것도 여기서 문다.
남기는 까닭(check-design §1 넷) — 길이 분명하다(대화하는 모델이 이 명령을 부른다) · 깨지면 조용하고 되돌릴 수 없다(간 안내는 못 거둔다)
· 크게 다친다(남이 보는 공유 시스템 · 남의 메일함) · 다른 무엇도 안 잡는다(실물 앱은 회사 PC 에서만 닿는다).

가짜가 지키는 꼴 — 회사 PC 에서 잰 것(``mrs.py`` 머리말 「들어가는 길」 · ``references/SOURCES.md``): SSO 넘김 화면은 세션 쿠키가 있을
때만 숨은 칸에 토큰을 내고, 출입증 자리는 폼 POST 에 302 로 ``accessToken`` 을 준다. 미리 검사는 늘 통과한다(실물도 겹침 · 지난 시각을
안 본다). 받은 요청은 다 적어 「안 넣었다 · 안 지웠다」를 그것으로 잰다.

물림 — 지난 시각 막기를 푼 사본 · 지문 견주기를 푼 사본에 같은 판정을 대어 빨강을 본다(매번 돈다).

돌리는 법::  python -X utf8 -I check_meeting_room.py

판정 — 끝 줄이 「통과 N/N」이면 종료 0, 어긋나면 1, 가짜를 못 띄우면 2.

언제 걷나 — meeting_room.py 가 사라지거나, 실물 앱에서 같은 계약을 재는 검사가 서면.

여기서 못 재는 것 — 실물 SSO · 실물 앱의 답 꼴 · 세션 받는 손(ep-login 의 검사가 잰다) · 승인 대기 · 반복 예약의 실물 꼴.
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import pathlib
import shutil
import sys
import tempfile
import threading
import urllib.parse
from datetime import datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
KST = timezone(timedelta(hours=9))
ME, OTHER, CO = "u-me", "u-other", "co-1"
ROOM = {"id": "r1", "location_id": "l1", "building_id": "b1", "floor_id": "f1", "name": "본관 201 소회의실", "capacity": 6,
        "room_type": "normal", "is_active": True,
        "policy": {"teams_integration": {"meeting_link": True}, "reservation_permission": {"user_can_reserve": True, "require_approval": False},
                   "reservation_restrictions": {"allow_cross_tenant_reservation": False}}}
TREE = [{"id": CO, "name": "회사", "locations": [{"name": "포항", "buildings": [{"name": "본사", "floors": [{"id": "f1", "name": "2F"}]}]}]}]
USERS = [{"id": "u-kang", "email": "kang@x.com", "name": "강", "display_name": "강(대리)"}]


def z(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class Fake:
    """가짜 SSO 와 가짜 앱의 상태 — 판마다 새로 세운다."""

    def __init__(self):
        self.calls, self.bookings, self.n = [], {}, 0

    def add(self, start: datetime, end: datetime, organizer=ME, title="있던 회의") -> str:
        self.n += 1
        rid = f"b{self.n}"
        self.bookings[rid] = {"id": rid, "company_id": CO, "organizer_id": {"id": organizer, "name": organizer}, "title": title,
                              "user_description": "", "start_time": z(start), "end_time": z(end), "attendees": [],
                              "status": "confirmed", "room_ids": ["r1"], "room_names": [ROOM["name"]],
                              "teams_link_visibility": "private", "updated_at": f"v{self.n}", "isOrganizer": organizer == ME}
        return rid


def handler(fake: Fake):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body=None, headers=None):
            raw = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
            self.send_response(code)
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            self._route("GET")

        def do_POST(self):
            self._route("POST")

        def do_PATCH(self):
            self._route("PATCH")

        def do_DELETE(self):
            self._route("DELETE")

        def _route(self, method):
            u = urllib.parse.urlsplit(self.path)
            n = int(self.headers.get("Content-Length") or 0)
            data = self.rfile.read(n) if n else b""
            fake.calls.append((method, u.path))
            if u.path == "/sso":
                ok = "SESS=1" in (self.headers.get("Cookie") or "")
                page = f'<form><input name="ssoToken" value="{"t" if ok else ""}"><input name="domainName" value="d"></form>'
                return self._send(200, page.encode())
            if u.path == "/api/auth/sso/posco":
                return self._send(302, None, {"Location": "/auth/sso-callback?accessToken=A&refreshToken=R"})
            if self.headers.get("Authorization") != "Bearer A":
                return self._send(401, {"message": "no"})
            return self._api(method, u, json.loads(data) if data else None)
    H._api = lambda self, m, u, b: api(fake, self, m, u, b)
    return H


def api(fake: Fake, h, method: str, u, body):
    p, q = u.path[len("/api/"):], urllib.parse.parse_qs(u.query)
    fixed = {"auth/me": {"user": {"id": ME, "company_id": CO}}, "rooms": [ROOM], "rooms/hierarchy": TREE,
             "users/directory": {"users": USERS}}
    if method == "GET" and p in fixed:
        return h._send(200, fixed[p])
    if method == "GET" and p == "reservations/my":
        return h._send(200, list(fake.bookings.values()))
    if method == "GET" and p == "reservations":
        a, b = q["startDate"][0], q["endDate"][0]
        return h._send(200, [x for x in fake.bookings.values() if x["start_time"] < b and a < x["end_time"]])
    if p == "reservations/validate":
        return h._send(200, {"valid": True, "errors": [], "approvalRequiredRoomIds": []})
    if method == "POST" and p == "reservations":
        rid = fake.add(datetime.fromisoformat(body["start_time"]), datetime.fromisoformat(body["end_time"]), title=body["title"])
        fake.bookings[rid]["attendees"] = body["attendees"]
        return h._send(201, fake.bookings[rid])
    rid = p.split("/")[-1]
    if method == "PATCH" and rid in fake.bookings:
        x = fake.bookings[rid]
        x.update(start_time=z(datetime.fromisoformat(body["start_time"])), end_time=z(datetime.fromisoformat(body["end_time"])),
                 title=body["title"], updated_at=x["updated_at"] + "'")
        return h._send(200, x)
    if method == "DELETE" and rid in fake.bookings:
        fake.bookings.pop(rid)
        return h._send(204)
    return h._send(404, {"message": p})


class Bench:
    """판 하나 — 가짜 서버 · 세션 파일 · 대역 받는 손(세션 파일 경로만 내는 node 글)을 세우고 명령을 돌린다."""

    def __init__(self, folder: pathlib.Path):
        self.folder, self.fake = folder, Fake()
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler(self.fake))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.session = self.tmp / "session.json"
        self.session.write_text(json.dumps({"cookies": [{"name": "SESS", "value": "1", "domain": "127.0.0.1", "path": "/"}]}), encoding="utf-8")
        hand = self.tmp / "hand.js"
        hand.write_text(f"console.log({json.dumps(str(self.session))});\n", encoding="utf-8")
        base = f"http://127.0.0.1:{self.srv.server_port}"
        self.env = {"MRS_BASE": base + "/api/", "MRS_SSO_PAGE": base + "/sso", "EP_SESSION_HAND": str(hand),
                    "MAILBOX_COOKIES": str(self.session)}

    def close(self):
        self.srv.shutdown()

    def run(self, *argv) -> tuple[int, dict]:
        import subprocess  # noqa: PLC0415
        env = {**os.environ, **self.env, "PYTHONUTF8": "1"}
        done = subprocess.run([sys.executable, "-X", "utf8", "-I", str(self.folder / "meeting_room.py"), *argv],
                              capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
        try:
            return done.returncode, json.loads(done.stdout)
        except ValueError:
            return done.returncode, {"raw": done.stdout + done.stderr}

    def mutated(self) -> list:
        return [c for c in self.fake.calls if c[0] in ("POST", "PATCH", "DELETE") and not c[1].endswith(("validate", "sso/posco"))]


def at(days: int, hour: int, minute: int = 0) -> datetime:
    d = datetime.now(KST).date() + timedelta(days=days)
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=KST)


def s(t: datetime) -> str:
    return t.strftime("%Y-%m-%d %H:%M")


def new(start: datetime, end: datetime, *more) -> list:
    return ["--room", "r1", "--title", "회의", "--start", s(start), "--end", s(end), *more]


def cases(b: Bench):
    """판정마다 (이름, 맞나, 어긋났을 때의 말). 판마다 새 Bench 로 돈다."""
    out = []
    # 지난 시각은 앱이 받아도 넣지 않는다
    code, p = b.run("preview", *new(at(-1, 15), at(-1, 16)))
    out.append(("지난 시각은 막는다", p.get("ok") is False and any("지난" in x for x in p.get("blocks", [])), p))
    # 겹치는 예약은 앱이 통과시켜도 막는다
    b.fake.add(at(1, 10), at(1, 11), organizer=OTHER)
    code, p = b.run("preview", *new(at(1, 10, 30), at(1, 11, 30)))
    out.append(("겹치는 예약은 막는다", p.get("ok") is False and any("이미 예약" in x for x in p.get("blocks", [])), p))
    # 막힌 판은 book 해도 안 넣는다
    code, r = b.run("book", *new(at(1, 10, 30), at(1, 11, 30)), "--seen", p.get("seen", ""))
    out.append(("막힌 판은 안 넣는다", r.get("state") == "blocked" and not b.mutated(), r))
    # 보여 준 판과 다른 seen 이면 안 넣는다
    code, r = b.run("book", *new(at(1, 14), at(1, 15)), "--seen", "다른판")
    out.append(("본 판이 아니면 안 넣는다", r.get("state") == "moved" and not b.mutated(), r))
    # 본 판 그대로면 넣고, 다시 읽어 확인하고, 참석자는 주소로 앱의 사람에 잇는다
    code, p = b.run("preview", *new(at(1, 14), at(1, 15), "--to", "KANG@x.com"))
    code, r = b.run("book", *new(at(1, 14), at(1, 15), "--to", "KANG@x.com"), "--seen", p.get("seen", ""))
    made = [x for x in b.fake.bookings.values() if x["title"] == "회의"]
    out.append(("본 판이면 넣는다", r.get("state") == "booked" and len(made) == 1, r))
    out.append(("참석자는 앱의 사람으로 잇는다", bool(made) and made[0]["attendees"] == [{"employee_id": "u-kang", "email": "kang@x.com"}],
                made[0]["attendees"] if made else None))
    # 앱이 모르는 주소는 막는다
    code, p = b.run("preview", *new(at(2, 9), at(2, 10), "--to", "nobody@x.com"))
    out.append(("모르는 주소는 막는다", p.get("ok") is False and any("nobody@x.com" in x for x in p.get("blocks", [])), p))
    # 남이 주관한 예약은 취소하지 않는다
    other = b.fake.add(at(3, 9), at(3, 10), organizer=OTHER)
    before = len(b.mutated())
    code, r = b.run("cancel", other)
    out.append(("남의 예약은 취소 안 한다", r.get("state") == "not_mine" and len(b.mutated()) == before, r))
    # 앱이 isOrganizer 를 안 실어도 남의 예약은 취소하지 않는다
    bare = b.fake.add(at(3, 11), at(3, 12), organizer=OTHER)
    b.fake.bookings[bare].pop("isOrganizer")
    code, r = b.run("cancel", bare)
    out.append(("주관자 표시가 없어도 남의 예약은 안 한다", r.get("state") == "not_mine" and len(b.mutated()) == before, r))
    # 내 예약은 취소하고 사라진 것을 확인한다
    if made:
        code, r = b.run("cancel", made[0]["id"])
        out.append(("내 예약은 취소한다", r.get("state") == "cancelled" and made[0]["id"] not in b.fake.bookings, r))
    return out


MUTANTS = {   # 물림 — 고친 사본에서 그 판정이 빨개져야 한다
    "지난 시각은 막는다": ("    if start < now:\n", "    if False:\n"),
    "본 판이 아니면 안 넣는다": ('    if p["seen"] != args.seen:\n', "    if False:\n"),
    "주관자 표시가 없어도 남의 예약은 안 한다": ('    return bool(me_id) and', '    return True or'),
}


def judge(folder: pathlib.Path) -> list:
    b = Bench(folder)
    try:
        return cases(b)
    finally:
        b.close()


def mutant(name: str, old: str, new_: str) -> tuple[str, bool, str]:
    """고친 사본을 스킬 홈 꼴(``<임시>/company-meeting-room/scripts`` 곁에 ``ep-login``)로 세워 같은 판정을 댄다."""
    home = pathlib.Path(tempfile.mkdtemp())
    tmp = home / "company-meeting-room" / "scripts"
    tmp.mkdir(parents=True)
    shutil.copytree(HERE.parents[1] / "ep-login", home / "ep-login")
    for f in ("mrs.py", "meeting_room.py"):
        shutil.copy2(HERE / f, tmp / f)
    src = (tmp / "meeting_room.py").read_text(encoding="utf-8")
    if old not in src:
        return f"물림 「{name}」", False, "돌연변이 자리가 코드에 없다 — 물림을 다시 지을 일"
    (tmp / "meeting_room.py").write_text(src.replace(old, new_, 1), encoding="utf-8")
    got = {n: ok for n, ok, _ in judge(tmp)}
    return f"물림 「{name}」", got.get(name) is False, "사본에서 빨개져야 한다"


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    try:
        rows = [(n, ok, why) for n, ok, why in judge(HERE)]
    except OSError as exc:
        print(f"못 쟀다 — 가짜를 못 띄웠다: {exc}")
        return 2
    rows += [mutant(n, *m) for n, m in MUTANTS.items()]
    bad = [r for r in rows if not r[1]]
    for n, ok, why in rows:
        print(("맞다  " if ok else "어긋남 ") + n + ("" if ok else f" — {json.dumps(why, ensure_ascii=False, default=str)[:400]}"))
    print(f"통과 {len(rows) - len(bad)}/{len(rows)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
