"""회사 일정 스킬의 얇은 명령 — 곁의 일정 손(``agenda.py``)을 불러 보기 · 넣기 · 지우기를 한다.

부르는 꼴::

    python -X utf8 -I company_calendar.py remember "<일정 화면 주소창의 주소>"   # 주소를 재 보고 남긴다
    python -X utf8 -I company_calendar.py show [오늘|내일|모레|YYYY-MM-DD] [끝 날]  # 기본 오늘 · 내일 · 내 일정함(기본 · Teams)만
    python -X utf8 -I company_calendar.py show … --shared [--who 이름]              # 공유받은 일정함도 · 그 사람 것만
    python -X utf8 -I company_calendar.py calendars                                 # 공유받은 일정함 목록
        show 의 답이 OUT_BYTES 를 넘으면 뒤 날짜의 줄부터 덜어 내고(하루를 가운데서 안 끊는다) ``more`` 가 이어 볼 구간을 든다
    python -X utf8 -I company_calendar.py preview --title T --start "YYYY-MM-DD HH:MM" --end "…" [--note N]   # 안 바꾼다
    python -X utf8 -I company_calendar.py add     --title T --start "…" --end "…" [--note N] --seen <preview 의 seen>   # ⚠ 바꾼다
    python -X utf8 -I company_calendar.py delete <handle>                                                    # ⚠ 바꾼다

    공통 — ``--url``(없으면 ``CALENDAR_URL`` → 남긴 주소 → 잰 기본 ``agenda.DEFAULT_APP_URL``). 시각은 다 서울 벽시계다.

세션 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 가 쥔다: 보기는 있는 세션 파일로 먼저 돌고, 넣기 · 지우기(``MUTATING``)는
늘 쓰는 사람의 Edge 에서 받는다(까닭은 그 함수의 머리말). ⚠ 판단(무엇을 넣을까 · 지워도 되나)은 여기 없다 — 바꾸는 명령은 사람이
그 한 건을 확인한 뒤에만 부른다(SKILL.md).

내는 것 — 표준 출력에 JSON 하나. 종료 값: 0 됐다 · 1 도구 고장(그대로 알린다) · 2 인자가 틀렸다 · 3 세션이 없다 · 끊겼다(스킬
ep-login) · 4 일정 앱 주소가 틀렸거나 잰 기본 주소로 내 일정함이 안 읽힌다. 0 이 아니면 ``message`` 가 까닭과 「다음: …」 을 든다.
일정 줄 — ``handle``(지우기에 넘기는 손잡이 · 사람에게 안 보인다) · ``weekday`` · ``pending``(참석 답을 안 한 받은 초대) · ``keep`` 이
차면 지우지 않는 줄이고 ``keep_word`` 가 사람에게 할 말이다 · 공유 줄은 ``calendar``(누구 일정함) · ``private``(일정함을 가진 사람이 비공개로 든 것).
넣기 · 지우기의 끝은 0 과 함께 ``state`` 와 사람에게 할 말 · 다음 걸음이 든 ``state_word`` 가 든다.
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
NO_CLASH = "none"                        # 확인에 보인 겹침이 없다는 seen 값
EXIT_URL = 4                             # 일정 앱 주소가 틀렸거나 잰 기본 주소로 내 일정함이 안 읽힌다 — 나머지 종료 값은 ep_command
INDENT = 1                               # 답(JSON)을 찍는 들여쓰기 — 답의 크기도 이 꼴로 센다
MUTATING = ("add", "delete")             # 회사 일정을 바꾼다 — 세션 손부터 받아 한 번만 돈다
NEXT_URL = "다음: 사람에게 「Edge 에서 메일을 열고 위의 일정 메뉴를 눌러, 열린 일정 화면의 주소창 주소를 그대로 붙여 주세요」 하고, 받은 주소로 remember 를 부른다"
# 지우지 않는 줄 — 사람에게 할 말. 까닭은 agenda.Event.keep_reason 이 가른다
KEEP_WORDS = {
    "invite": "받은 회의 초대입니다 — 지우면 곧 참석 답이 됩니다. 참석 답은 초대 메일이나 회사 일정 화면에서 해 주세요",
    "meeting": "회의로 든 일정입니다 — 지우면 참석하실 분께 알림이 갈 수 있어 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "repeat": "반복 일정입니다 — 지우기가 그날 하나만 걷는지 아직 확인하지 않아 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "all_day": "하루 종일 일정입니다 — 지우기를 아직 확인하지 않아 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "locked": "고칠 수 있는 일정으로 읽히지 않았습니다 — 일정 앱이 막은 것인지 그 표시를 못 알아본 것인지 가리지 못해 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "shared": "공유받은 일정함의 일정입니다 — 여기서는 읽기만 합니다",
}
# 넣기 · 지우기의 끝 — 사람에게 할 말과 다음 걸음
STATE_WORDS = {
    "added": "넣었습니다(다시 읽어 확인했습니다). 다음: 이 줄의 handle 을 들고 있다가 「방금 것 지워 줘」 에 쓴다",
    "already": "같은 일정이 이미 있어 넣지 않았습니다",
    "clashed": "확인하신 뒤 그 시각에 다른 일정이 들어와 넣지 않았습니다. 다음: preview 를 다시 불러 새 겹침을 보이고 다시 묻는다",
    "deleted": "지웠습니다(다시 읽어 사라진 것을 확인했습니다)",
    "gone": "그날 일정에 없습니다 — 이미 지워졌거나 다른 날로 옮겨졌습니다",
    "changed": "보여 드린 뒤 그 일정이 바뀌었습니다. 다음: 답의 event(지금의 꼴)를 보이고 다시 묻는다",
    "unsure": "됐는지 확인하지 못했습니다. 다음: 다시 부르지 말고 show 로 그날을 읽어 보인다",
}


if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    from ep_command import EXIT_ARGS, OUT_BYTES, WEEKDAYS, Stop, day_of, load, size
except ImportError:                             # 형제 스킬 ep-login 이 곁에 없다 — 답의 꼴(JSON 하나 · 종료 1)은 지킨다
    print(json.dumps({"error": "tool", "message": f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"}, ensure_ascii=False))
    sys.exit(1)


def saved_url() -> str:
    try:
        data = json.loads(pathlib.Path(SAVED_URL).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(data.get("calendar_url") or "") if isinstance(data, dict) else ""


def resolve(args, default: str) -> tuple[str, bool]:
    """일정 앱 주소와 그것이 기본값인가 — ``--url`` → ``CALENDAR_URL`` → 남긴 주소 → 잰 기본(``agenda.DEFAULT_APP_URL``)."""
    given = (args.url or os.environ.get("CALENDAR_URL", "") or saved_url()).strip()
    return (given, False) if given else (default, True)


def weekday_of(day: date) -> str:
    return WEEKDAYS[day.weekday()]


def row(agenda, e) -> dict:
    out = {"day": e.day.isoformat(), "weekday": weekday_of(e.day), "when": e.when(), "title": e.title, "handle": agenda.Seen.of(e).handle,
           "keep": e.keep_reason, "pending": e.response == agenda.RESPONSE_PENDING, "meeting": e.meeting,
           "repeat": e.repeat, "all_day": e.all_day}
    if e.keep_reason:
        out["keep_word"] = KEEP_WORDS.get(e.keep_reason, e.keep_reason)
    if e.calendar:                       # 공유받은 일정함의 줄 — 누구 일정함인가 · 일정함을 가진 사람이 비공개로 든 것인가. 지우는 손잡이는 없다
        out.update(calendar=e.calendar, private=e.private)
        del out["handle"], out["pending"]  # 참석 답은 그 일정함을 가진 사람의 것이라 내 초대로 읽히지 않게 뺀다
    return out


def fit_days(out: dict, last: date, again: str) -> None:
    """보기의 답이 OUT_BYTES 를 넘으면 뒤 날짜의 줄부터 덜어 낸다 — 하루를 가운데서 끊지 않는다(그날이 비어 보이면 그날에 일정을
    겹쳐 잡는다). 덜었으면 ``more`` 가 이어 볼 구간을 든다. 하루치만으로 넘치면 그 하루는 그대로 낸다."""
    lists = [k for k in ("events", "shared") if k in out]
    days = sorted({r["day"] for k in lists for r in out[k]})
    while len(days) > 1 and size(out, INDENT) > OUT_BYTES:
        cut = days.pop()
        for k in lists:
            out[k] = [r for r in out[k] if r["day"] < cut]
        out["more"] = f"다음: {cut} 부터는 안 실었다 — show {cut} {last.isoformat()}{again} 로 이어 본다"


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


def run(args, session: pathlib.Path) -> dict:
    agenda = load("agenda", HERE)
    url, by_default = resolve(args, agenda.DEFAULT_APP_URL)
    today = datetime.now(agenda.KST).date()
    if args.command == "remember":
        url = (args.address or "").strip()
    found = agenda.APP_URL.match(url)
    if not found:
        raise Stop(EXIT_URL, "url", "일정 앱 주소(…/calperson<NN>.nsf)가 든 주소가 아니다")
    url = found.group(1) + found.group(2)
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
    if by_default:
        try:
            reader.book()                # 잰 기본 주소가 이 사람의 일정함을 드나 — 다른 서버에 일정이 있는 사람은 주소를 받는다
        except agenda.SessionExpired:
            raise
        except agenda.CalendarError as exc:
            raise Stop(EXIT_URL, "url", f"기본 일정 앱 주소({url})로 내 일정함이 안 읽힌다({exc}) — 일정 DB 가 다른 서버에 있는 사람이다. {NEXT_URL}") from exc
    if args.command == "calendars":
        return {"shared": [{"name": b.name, "kind": b.kind} for b in reader.shared_books()]}
    if args.command == "show":
        first = day_of(args.first or "오늘", today)
        last = day_of(args.last, today) if args.last else (first + timedelta(days=1) if not args.first else first)
        out = {"today": today.isoformat(), "today_weekday": weekday_of(today),
               "first": first.isoformat(), "last": last.isoformat()}
        if not args.who:
            mine, side_failed = reader.mine_between(first, last)
            out["events"] = [row(agenda, e) for e in mine]
            failed = [{"calendar": n, "message": m} for n, m in side_failed]
        else:
            failed = []
        if args.shared or args.who:
            shared = []
            for b in shared_books(reader, args.who):
                try:
                    shared += reader.between(first, last, b)
                except agenda.CalendarError as exc:   # 한 일정함이 안 읽혀도 나머지는 보인다 — 못 읽은 것은 이름으로 알린다
                    # 그 서버의 「끊긴 세션」 꼴도 여기 든다 — 방금 같은 세션으로 목록을 읽었으니 공유가 풀렸거나 그 서버가 안 받는
                    # 것이다. ep-login 으로 보내면 같은 끝을 되풀이한다
                    failed.append({"calendar": b.name, "message": str(exc)})
            shared.sort(key=lambda e: (e.start, e.end, e.calendar))
            out["shared"] = [row(agenda, e) for e in shared]
        if failed:
            out["shared_failed"] = failed
        fit_days(out, last, (" --shared" if args.shared else "") + (f" --who {args.who}" if args.who else ""))
        return out
    if args.command in ("preview", "add"):
        w = want_of(args, agenda)
        if args.command == "add":
            shown = set() if args.seen == NO_CLASH else set(args.seen.split(","))
            got = agenda.register(url, session, w, reader=reader, shown_clash=shown)
            return {"state": got.state, "state_word": STATE_WORDS[got.state], "event": row(agenda, got.event) if got.event else None}
        day, side_failed = reader.mine_between(w.day, agenda.kst_day(w.end))   # 겹침은 기본 일정함과 다른 내 일정함(Teams) 둘 다에서 본다
        same = next((e for e in day if not e.calendar and agenda.same_event(e, w)), None)   # 이미 있나는 넣을 자리(기본 일정함)에서만
        clash = [e for e in day if e.overlaps(w.start, w.end) and e is not same]
        return {"title": w.title, "note": w.note, "day": w.day.isoformat(), "weekday": weekday_of(w.day),
                "when": f"{w.start.astimezone(agenda.KST):%H:%M}–{w.end.astimezone(agenda.KST):%H:%M}",
                "already": row(agenda, same) if same else None, "clash": [row(agenda, e) for e in clash],
                "seen": ",".join(sorted(agenda.event_ref(e) for e in clash)) or NO_CLASH,
                "visibility": agenda.VISIBILITY,
                **({"shared_failed": [{"calendar": n, "message": m} for n, m in side_failed]} if side_failed else {})}
    seen = agenda.Seen.parse(args.handle)
    try:
        got = agenda.delete(url, session, seen, reader=reader)
    except agenda.ChangeRefused as exc:
        return {"state": "refused", "keep": exc.reason, "state_word": KEEP_WORDS.get(exc.reason) or str(exc)}
    return {"state": got.state, "state_word": STATE_WORDS[got.state], "event": row(agenda, got.event) if got.event else None}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="회사 일정 — 보기 · 넣기 · 지우기")
    p.add_argument("--url", help="일정 앱 주소(…/calperson<NN>.nsf) — 없으면 CALENDAR_URL · 남긴 주소 · 잰 기본")
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
    return ep_command.finish(
        lambda agenda: ep_session.session_first(lambda f: run(args, f), expired=(agenda.SessionExpired, agenda.SessionMissing),
                                                file_first=args.command not in MUTATING),
        "agenda", HERE, indent=INDENT, app_error="CalendarError", args_errors=("CalendarConfigError",))   # 설정 · 인자가 틀린 것은 2


if __name__ == "__main__":
    sys.exit(main())
