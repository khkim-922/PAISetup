"""사내 회의실 예약 앱(MRS)의 손 — 출입증을 받고, 회의실 · 예약 · 사람 목록을 읽고, 예약 한 건을 넣고 · 고치고 · 지운다.

부르는 꼴::

    import mrs
    app = mrs.App(<세션 파일>)          # 스킬 ep-login 의 받는 손이 남긴 사내 세션(쿠키) 파일
    app.me() · app.rooms() · app.hierarchy() · app.between(first, last) · app.mine() · app.directory()
    app.validate(room_ids, start, end, reservation_id=None)
    app.create(body) · app.update(rid, body) · app.delete(rid)      # ⚠ 바꾼다 — 부르는 쪽이 사람의 확인을 받은 뒤에만

내는 것 — 앱의 JSON 그대로(dict · list). 시각은 앱이 UTC ISO(``…Z``)로 내고, 받을 때는 오프셋이 붙은 ISO 를 받는다.
예외 — ``SessionExpired``(사내 세션이 끊겼다 · 출입증을 못 받았다 — 받는 손을 다시 부를 자리) · ``SessionMissing``(세션 파일이
없다 · 못 읽는다) · ``AppError``(앱이 거절했다 · 답이 꼴이 아니다 — ``status`` 와 앱의 말을 든다).

들어가는 길은 SSO 넘김 → ``api/auth/sso/posco`` 에 폼 꼴 POST(302 의 Location 이 출입증을 든다) → Bearer 출입증으로 부르기 세
걸음이다 — 걸음마다의 꼴은 ``references/SOURCES.md`` 「들어가는 길」이 든다.

⚠ 앱의 ``reservations/validate`` 는 정책(타사 회의실 · 승인 · 시간 제한)만 보고 **겹치는 예약과 지난 시각은 안 본다** — 지난 시각
예약도 넣어지니, 겹침 · 지난 시각은 부르는 쪽이 가린다.

사내 밖으로는 안 나간다 — 부르는 주소는 이 파일의 두 상수(검사가 가짜를 세울 때만 환경변수 ``MRS_BASE`` · ``MRS_SSO_PAGE`` 가
바꾼다) 뿐이고, 프록시를 안 탄다(사내 호스트다). 리다이렉트를 따라가지 않는다 — 따라가면 쿠키가 엉뚱한 자리에 실린다.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent.parent / "ep-login" / "scripts"   # 형제 스킬 — 세션 파일을 읽는 자리
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_session  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다

BASE = os.environ.get("MRS_BASE", "https://mrs.posco.net/api/")
SSO_PAGE = os.environ.get("MRS_SSO_PAGE",
                          "http://swpsso.posco.net/idms/U61/jsp/redirect.jsp?redir_url=https://mrs.posco.net/api/auth/sso/posco")
SSO_FIELDS = ("ssoToken", "websealType", "domainName", "serverName", "LANG", "TIMEZONE")
TIMEOUT = 30
MOST_SAID = 600         # 앱의 거절 말에서 읽는 바이트 — 사람에게 전할 한두 줄이면 된다
LOGIN_TRIES = 2          # SSO_VALIDATION_FAILED 뒤 같은 세션으로 한 번 더 — 그래도 지면 받는 손을 다시 부를 자리다


class AppError(Exception):
    """회의실 예약 앱의 손이 낸 실패 — 사람에게 전할 말과, 앱이 답했으면 그 HTTP 상태."""
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class SessionMissing(AppError):
    """세션 파일이 없거나 비었다 — 받는 손(스킬 ep-login)을 부를 자리다."""
    pass


class SessionExpired(AppError):
    """사내 세션이 끊겼거나 앱이 출입증을 거절했다 — 받는 손을 다시 부를 자리다."""
    pass


class _Stay(urllib.request.HTTPRedirectHandler):
    """넘김(3xx)을 따라가지 않는 손잡이 — 넘김은 HTTPError 로 올라와 Location 을 읽는다."""
    def redirect_request(self, *a, **k):   # 따라가지 않는다 — 3xx 는 HTTPError 로 올라와 Location 을 읽는다
        """넘김을 따라가지 않는다 — None 이면 urllib 이 3xx 를 HTTPError 로 올린다."""
        return None


def _opener(jar=None):
    """프록시를 거치지 않고 넘김을 안 따라가는 여는 손 — 쿠키 통을 주면 그 쿠키를 싣는다."""
    parts = [urllib.request.ProxyHandler({}), _Stay()]
    if jar is not None:
        parts.append(urllib.request.HTTPCookieProcessor(jar))
    return urllib.request.build_opener(*parts)


class App:
    """회의실 예약 앱 한 판 — 사내 세션의 쿠키로 출입증을 받고, 앱의 JSON 자리를 부른다."""
    def __init__(self, session_file: pathlib.Path | str, *, timeout: float = TIMEOUT):
        self._jar = ep_session.load_jar(session_file, missing=SessionMissing)   # 어느 호스트에 실리나는 쿠키 통이 가린다
        self._timeout = timeout
        self._token = ""
        self._plain = _opener()

    # ── 출입증 ───────────────────────────────────────────────────────────
    def _login_once(self) -> str:
        """SSO 넘김 화면에서 토큰을 받아 앱에 넘기고, 앱이 넘김 주소에 실어 준 출입증(accessToken)을 낸다 — 못 받으면 SessionExpired."""
        try:
            r = _opener(self._jar).open(SSO_PAGE, timeout=self._timeout)
            page = r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as exc:
            raise SessionExpired(f"SSO 넘김 화면이 {exc.code} 로 답했다 — 사내 세션이 끊겼다") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"SSO 서버에 못 닿았다: {exc}") from exc
        form = ep_session.sso_form(page)
        if not form.get("ssoToken"):
            raise SessionExpired("SSO 넘김 화면에 토큰이 없다 — 사내 세션이 끊겼다")
        body = urllib.parse.urlencode({k: form.get(k, "") for k in SSO_FIELDS}).encode()
        loc = ""
        try:
            r = self._plain.open(urllib.request.Request(BASE + "auth/sso/posco", data=body), timeout=self._timeout)
            loc = r.headers.get("Location") or ""
        except urllib.error.HTTPError as exc:
            loc = exc.headers.get("Location") or ""
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"회의실 예약 앱에 못 닿았다: {exc}") from exc
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(loc).query)
        if q.get("accessToken", [""])[0]:
            return q["accessToken"][0]
        raise SessionExpired(f"회의실 예약 앱이 출입증을 안 줬다({(q.get('code') or ['답 없음'])[0]})")

    def login(self) -> None:
        """출입증을 받아 둔다 — 앱이 SSO 검증에 지면 같은 세션으로 ``LOGIN_TRIES`` 번까지."""
        last = None
        for i in range(LOGIN_TRIES):
            try:
                self._token = self._login_once()
                return
            except SessionExpired as exc:
                last = exc
                if i + 1 < LOGIN_TRIES:
                    time.sleep(1.0)
        raise last

    # ── 부르기 ───────────────────────────────────────────────────────────
    def call(self, method: str, path: str, data=None, query: dict | None = None):
        """앱의 자리 하나를 출입증으로 부르고 답 JSON 을 낸다 — 401 은 SessionExpired, 그 밖의 거절 · 닿지 못함은 AppError."""
        if not self._token:
            self.login()
        url = BASE + path + ("?" + urllib.parse.urlencode(query) if query else "")
        req = urllib.request.Request(url, method=method, data=None if data is None else json.dumps(data).encode(),
                                     headers={"Authorization": "Bearer " + self._token, "Content-Type": "application/json"})
        try:
            r = self._plain.open(req, timeout=self._timeout)
            raw = r.read()
        except urllib.error.HTTPError as exc:
            said = exc.read(MOST_SAID).decode("utf-8", "ignore")
            if exc.code == 401:
                raise SessionExpired("회의실 예약 앱이 출입증을 거절했다(401)", 401) from exc
            try:
                said = json.loads(said).get("message") or said
            except (ValueError, AttributeError):
                pass
            raise AppError(f"회의실 예약 앱이 {exc.code} 로 거절했다: {said}", exc.code) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise AppError(f"회의실 예약 앱에 못 닿았다: {exc}") from exc
        if not raw:
            return None
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise AppError("회의실 예약 앱의 답이 JSON 이 아니다") from exc

    # ── 읽기 ─────────────────────────────────────────────────────────────
    def me(self) -> dict:
        """나 — 앱이 아는 쓰는 사람(id · 이름 · 메일 · 회사)."""
        return self.call("GET", "auth/me")["user"]

    def rooms(self) -> list:
        """회의실 목록 — 정책(승인 · 예약 권한 · Teams)까지."""
        return self.call("GET", "rooms")

    def hierarchy(self) -> list:
        """회사 → 지역 → 건물 → 층의 나무."""
        return self.call("GET", "rooms/hierarchy")

    def between(self, first_utc: str, last_utc: str) -> list:
        """그 구간(UTC 글자)에 걸친 모든 예약."""
        return self.call("GET", "reservations", query={"startDate": first_utc, "endDate": last_utc})

    def mine(self) -> list:
        """내 예약 — 내가 주관한 것과 나를 부른 것."""
        return self.call("GET", "reservations/my")

    def directory(self) -> list:
        """앱의 전사 사람 목록 — 참석자 메일을 앱의 사람에 잇는 데 쓴다."""
        return self.call("GET", "users/directory")["users"]

    def validate(self, room_ids: list, start: str, end: str, reservation_id: str | None = None) -> dict:
        """넣거나 고칠 예약을 앱의 정책에 미리 대 본다 — 읽기다(앱의 화면도 입력마다 부른다)."""
        body = {"room_ids": room_ids, "start_time": start, "end_time": end}
        if reservation_id:
            body["reservation_id"] = reservation_id
        return self.call("POST", "reservations/validate", body)   # 읽기다 — 앱의 화면도 입력마다 부른다

    # ── 바꾸기 ⚠ ──────────────────────────────────────────────────────────
    def create(self, body: dict) -> dict:
        """⚠ 예약 하나를 넣는다 — 참석자에게 안내가 간다."""
        return self.call("POST", "reservations", body)

    def update(self, rid: str, body: dict) -> dict:
        """⚠ 예약 하나를 고친다 — 참석자에게 바뀐 안내가 간다."""
        return self.call("PATCH", f"reservations/{urllib.parse.quote(rid)}", body)

    def delete(self, rid: str) -> None:
        """⚠ 예약 하나를 지운다 — 참석자에게 취소 안내가 간다."""
        self.call("DELETE", f"reservations/{urllib.parse.quote(rid)}")

    def update_series(self, rid: str, body: dict) -> dict:
        """반복의 모든 회차를 고친다 — ``rid`` 는 그 반복의 회차 하나. 답은 ``{updatedCount, totalRequested, …}``."""
        return self.call("PATCH", f"reservations/{urllib.parse.quote(rid)}/series", body)

    def delete_series(self, rid: str) -> dict:
        """반복의 모든 회차를 지운다 — ``rid`` 는 그 반복의 회차 하나. 답은 ``{deletedCount, totalRequested, …}``."""
        return self.call("DELETE", f"reservations/{urllib.parse.quote(rid)}/series")

    # ── 내 설정 — 즐겨찾는 회의실 · 참석자 그룹. 바꾸는 손의 답은 다 바뀐 뒤의 설정 전체다 ─────────────────
    def prefs(self) -> dict:
        """내 설정 — 즐겨찾는 회의실과 참석자 그룹."""
        return self.call("GET", "me/preferences")

    def favorite(self, room_id: str, on: bool) -> dict:
        """회의실 하나를 즐겨찾기에 넣거나 뺀다."""
        return self.call("POST" if on else "DELETE", f"me/preferences/favorite-rooms/{urllib.parse.quote(room_id)}")

    def add_group(self, body: dict) -> dict:
        """참석자 그룹 하나를 만든다 — ``{name, members: [{employee_id, email}]}``."""
        return self.call("POST", "me/preferences/attendee-groups", body)

    def put_group(self, gid: str, body: dict) -> dict:
        """참석자 그룹 하나를 통째로 간다."""
        return self.call("PUT", f"me/preferences/attendee-groups/{urllib.parse.quote(gid)}", body)

    def drop_group(self, gid: str) -> dict:
        """참석자 그룹 하나를 지운다."""
        return self.call("DELETE", f"me/preferences/attendee-groups/{urllib.parse.quote(gid)}")
