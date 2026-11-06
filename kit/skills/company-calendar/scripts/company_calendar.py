"""회사 일정 스킬의 얇은 명령 — 곁의 일정 손(``agenda.py``)을 불러 보기 · 넣기 · 지우기를 한다.

부르는 꼴::

    python -X utf8 -I company_calendar.py remember "<일정 화면 주소창의 주소>"   # 주소를 재 보고 남긴다
    python -X utf8 -I company_calendar.py show [오늘|내일|YYYY-MM-DD] [끝 날]       # 기본 오늘 · 내일 · 내 일정함만
    python -X utf8 -I company_calendar.py show … --shared [--who 이름]              # 공유받은 일정함도 · 그 사람 것만
    python -X utf8 -I company_calendar.py calendars                                 # 공유받은 일정함 목록
    python -X utf8 -I company_calendar.py preview --title T --start "YYYY-MM-DD HH:MM" --end "…" [--note N]   # 안 바꾼다
    python -X utf8 -I company_calendar.py add     --title T --start "…" --end "…" [--note N] --seen <preview 의 seen>   # ⚠ 바꾼다
    python -X utf8 -I company_calendar.py delete <handle>                                                    # ⚠ 바꾼다

    공통 — ``--url``(없으면 ``CALENDAR_URL`` → 남긴 주소). 시각은 다 서울 벽시계다.

하는 일 — 명령마다 먼저 형제 스킬 ep-login 의 받는 손을 인자 없이 말없이 돌려(그 폴더의 ``ep_session.py`` 가 돌린다) 쓰는 사람의
Edge 에서 그때의 세션을 받는다. 세션 파일의 자리는 그 손이 정하고, 끝 줄에 낸 절대 경로를 이 명령이 읽는다 — 그 자리를 여기 다시
적지 않는다. 그 쿠키로 곁의 일정 손을 부른다.
판단(무엇을 넣을까 · 지워도 되나 묻기)은 여기 없다 — 바꾸는 명령은 사람이 그 한 건을 확인한 뒤에만 부른다(SKILL.md).

내는 것 — 표준 출력에 JSON 하나. 종료 값: 0 됐다 · 1 도구 고장(그대로 알린다) · 2 인자가 틀렸다 · 3 세션이 없다 · 끊겼다(스킬
ep-login) · 4 일정 앱 주소가 없다 · 틀렸다. 넣기 · 지우기의 끝은 0 과 함께 ``state`` 가 든다.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import date, datetime, timedelta

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
SAVED_URL = "~/.company-calendar.json"   # 남긴 일정 앱 주소 — 저장소 밖 · 비밀이 없다(사번 · 쿠키가 안 든다)
DAY_WORDS = {"오늘": 0, "today": 0, "내일": 1, "tomorrow": 1, "모레": 2}
NO_CLASH = "none"                        # 확인에 보인 겹침이 없다는 seen 값
EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION, EXIT_URL = 0, 1, 2, 3, 4


class Stop(Exception):
    """명령을 멈춘다 — ``code`` 가 종료 값, ``kind`` 가 JSON 의 error 값이다."""

    def __init__(self, code: int, kind: str, message: str):
        super().__init__(message)
        self.code, self.kind = code, kind


def load_agenda():
    """곁의 ``agenda`` 를 싣는다 — ``-I`` 로 돌면 이 폴더가 ``sys.path`` 에 없어 넣고 싣는다."""
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import agenda  # noqa: PLC0415 — 자리를 넣은 뒤에 싣는다
    return agenda


def load_ep_session():
    """형제 스킬 ep-login 의 ``ep_session`` 을 싣는다 — 받는 손을 돌리는 한 자리다."""
    if str(EP_LOGIN_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(EP_LOGIN_SCRIPTS))
    try:
        import ep_session   # noqa: PLC0415 — 자리를 넣은 뒤에 싣는다
    except ImportError as exc:
        raise Stop(EXIT_TOOL, "tool", f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다") from exc
    return ep_session


def attach() -> pathlib.Path:
    """쓰는 사람의 Edge 에서 그때의 세션을 받는다 — 받는 손이 쓴 파일(0)이나, Edge 에 못 붙었을 때 남은 파일(2)을 낸다. 그 세션이
    아직 살았는지는 일정 서버가 가린다(끊겼으면 ``SessionExpired`` → ep-login). 남은 파일이 없거나 로그인이 안 됐으면(3) ep-login 으로 멈춘다."""
    ep = load_ep_session()
    got = ep.attach()
    if got.usable:
        return got.file
    tail = (got.said.splitlines() or [""])[-1]
    if got.code in (ep.NO_EDGE, ep.NOT_LOGGED_IN):
        raise Stop(EXIT_SESSION, "session", f"사내 세션이 없다(세션 손 종료 {got.code} — {tail})")
    if got.code == ep.OK:
        raise Stop(EXIT_TOOL, "tool", "세션 손이 0 으로 끝났는데 끝 줄에 세션 파일의 절대 경로가 없다")
    raise Stop(EXIT_TOOL, "tool", f"세션 손이 종료 {got.code} 로 졌다 — {tail}")


def saved_url() -> str:
    try:
        data = json.loads(pathlib.Path(SAVED_URL).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(data.get("calendar_url") or "") if isinstance(data, dict) else ""


def resolve(args) -> str:
    url = (args.url or os.environ.get("CALENDAR_URL", "") or saved_url()).strip()
    if args.command != "remember" and not url:
        raise Stop(EXIT_URL, "url", "일정 앱 주소가 없다 — Edge 에서 메일 → 일정을 열어 주소창의 주소를 받는다")
    return url


def day_of(text: str, today: date) -> date:
    if text.strip().lower() in DAY_WORDS:
        return today + timedelta(days=DAY_WORDS[text.strip().lower()])
    try:
        return date.fromisoformat(text.strip())
    except ValueError as exc:
        raise Stop(EXIT_ARGS, "args", f"날은 오늘 · 내일 · 모레 · YYYY-MM-DD 가운데 하나로 준다: {text!r}") from exc


def row(agenda, e) -> dict:
    out = {"day": e.day.isoformat(), "when": e.when(), "title": e.title, "handle": agenda.Seen.of(e).handle,
           "keep": e.keep_reason, "pending": e.response == agenda.RESPONSE_PENDING, "meeting": e.meeting,
           "repeat": e.repeat, "all_day": e.all_day}
    if e.calendar:                       # 공유받은 일정함의 줄 — 누구 일정함인가 · 주인이 비공개로 든 것인가. 지우는 손잡이는 없다
        out.update(calendar=e.calendar, private=e.private)
        del out["handle"], out["pending"]  # 참석 답은 그 일정함 주인의 것이라 내 초대로 읽히지 않게 뺀다
    return out


def shared_books(reader, who: str | None) -> list:
    """공유받은 일정함 — ``who`` 를 주면 이름에 그 글자가 든 것만. 하나도 안 걸리면 인자가 틀린 것이다(목록을 보인다)."""
    books = reader.shared_books()
    if who:
        picked = [b for b in books if who.strip() in b.name]
        if not picked:
            names = ", ".join(b.name for b in books) or "없음"
            raise Stop(EXIT_ARGS, "args", f"공유받은 일정함에 「{who}」가 없다 — 있는 것: {names}")
        return picked
    return books


def want_of(args, agenda):
    w = agenda.Want(args.title, agenda.kst(args.start), agenda.kst(args.end), args.note or "").cleaned()
    if not w.title or w.end <= w.start:
        raise Stop(EXIT_ARGS, "args", "제목이 비었거나 끝이 시작보다 앞이다")
    return w


def run(args) -> dict:
    agenda = load_agenda()
    url = resolve(args)
    today = datetime.now(agenda.KST).date()
    if args.command == "remember":
        url = (args.address or "").strip()
    found = agenda.APP_URL.match(url)
    if not found:
        raise Stop(EXIT_URL, "url", "일정 앱 주소(…/calperson<NN>.nsf)가 든 주소가 아니다")
    url = found.group(1) + found.group(2)
    session = attach()
    reader = agenda.Reader(url, session)
    if args.command == "remember":
        try:
            reader.book()                # 이 주소로 내 일정함이 읽히나 — 읽혀야 남긴다
        except agenda.SessionExpired:
            raise
        except agenda.CalendarError as exc:
            raise Stop(EXIT_URL, "url", f"이 주소로 내 일정함을 못 읽었다({exc}) — 일정 화면의 주소인지 본다") from exc
        place = pathlib.Path(SAVED_URL).expanduser()
        place.write_text(json.dumps({"calendar_url": url}, ensure_ascii=False), encoding="utf-8")
        return {"saved": str(place), "url": url}
    if args.command == "calendars":
        return {"shared": [{"name": b.name, "kind": b.kind} for b in reader.shared_books()]}
    if args.command == "show":
        first = day_of(args.first or "오늘", today)
        last = day_of(args.last, today) if args.last else (first + timedelta(days=1) if not args.first else first)
        out = {"today": today.isoformat(), "first": first.isoformat(), "last": last.isoformat()}
        if not args.who:
            out["events"] = [row(agenda, e) for e in reader.between(first, last)]
        if args.shared or args.who:
            shared, failed = [], []
            for b in shared_books(reader, args.who):
                try:
                    shared += reader.between(first, last, b)
                except agenda.CalendarError as exc:   # 한 일정함이 안 읽혀도 나머지는 보인다 — 못 읽은 것은 이름으로 알린다
                    # 그 서버의 「끊긴 세션」 꼴(403 · SSO 화면)도 여기 든다 — 같은 세션으로 방금 일정함 목록을 읽었으니 내 세션은
                    # 살았고, 공유가 풀렸거나 그 서버가 안 받는 것이다. ep-login 으로 보내면 같은 끝을 되풀이한다
                    failed.append({"calendar": b.name, "message": str(exc)})
            shared.sort(key=lambda e: (e.start, e.end, e.calendar))
            out["shared"] = [row(agenda, e) for e in shared]
            if failed:
                out["shared_failed"] = failed
        return out
    if args.command in ("preview", "add"):
        w = want_of(args, agenda)
        if args.command == "add":
            shown = set() if args.seen == NO_CLASH else set(args.seen.split(","))
            got = agenda.register(url, session, w, reader=reader, shown_clash=shown)
            return {"state": got.state, "event": row(agenda, got.event) if got.event else None}
        day = reader.between(w.day, agenda.kst_day(w.end))
        same = next((e for e in day if agenda.same_event(e, w)), None)
        clash = [e for e in day if e.overlaps(w.start, w.end) and e is not same]
        return {"title": w.title, "note": w.note, "day": w.day.isoformat(),
                "when": f"{w.start.astimezone(agenda.KST):%H:%M}–{w.end.astimezone(agenda.KST):%H:%M}",
                "already": row(agenda, same) if same else None, "clash": [row(agenda, e) for e in clash],
                "seen": ",".join(sorted(agenda.event_ref(e) for e in clash)) or NO_CLASH,
                "visibility": agenda.VISIBILITY}
    seen = agenda.Seen.parse(args.handle)
    try:
        got = agenda.delete(url, session, seen, reader=reader)
    except agenda.ChangeRefused as exc:
        return {"state": "refused", "keep": exc.reason}
    return {"state": got.state, "event": row(agenda, got.event) if got.event else None}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="회사 일정 — 보기 · 넣기 · 지우기")
    p.add_argument("--url", help="일정 앱 주소(…/calperson<NN>.nsf) — 없으면 CALENDAR_URL · 남긴 주소")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("remember", help="일정 앱 주소를 재 보고 남긴다")
    r.add_argument("address")
    s = sub.add_parser("show", help="일정 보기(바꾸지 않는다)")
    s.add_argument("first", nargs="?")
    s.add_argument("last", nargs="?")
    s.add_argument("--shared", action="store_true", help="공유받은 일정함의 일정도 함께")
    s.add_argument("--who", help="공유받은 일정함 가운데 이름에 이 글자가 든 것만(내 일정은 빼고)")
    sub.add_parser("calendars", help="공유받은 일정함 목록(바꾸지 않는다)")
    for name in ("preview", "add"):
        a = sub.add_parser(name, help="넣을 꼴 미리 보기(바꾸지 않는다)" if name == "preview" else "⚠ 한 건 넣기")
        a.add_argument("--title", required=True)
        a.add_argument("--start", required=True, help="YYYY-MM-DD HH:MM(서울)")
        a.add_argument("--end", required=True, help="YYYY-MM-DD HH:MM(서울)")
        a.add_argument("--note", default="")
        if name == "add":
            a.add_argument("--seen", required=True, help="preview 답의 seen — 확인에 보인 겹침")
    d = sub.add_parser("delete", help="⚠ 한 건 지우기")
    d.add_argument("handle")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        result, code = run(args), EXIT_OK
    except Stop as exc:
        result, code = {"error": exc.kind, "message": str(exc)}, exc.code
    except Exception as exc:  # noqa: BLE001 — 일정 손의 예외를 종료 값으로 옮긴다
        agenda = sys.modules.get("agenda")
        if agenda and isinstance(exc, agenda.SessionExpired):
            result, code = {"error": "session", "message": str(exc)}, EXIT_SESSION
        elif agenda and isinstance(exc, agenda.SessionMissing):
            result, code = {"error": "session", "message": str(exc)}, EXIT_SESSION
        elif agenda and isinstance(exc, agenda.CalendarConfigError):
            result, code = {"error": "args", "message": str(exc)}, EXIT_ARGS
        elif agenda and isinstance(exc, agenda.CalendarError):
            result, code = {"error": "tool", "message": str(exc)}, EXIT_TOOL
        else:
            result, code = {"error": "tool", "message": f"{type(exc).__name__}: {exc}"}, EXIT_TOOL
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return code


if __name__ == "__main__":
    sys.exit(main())
