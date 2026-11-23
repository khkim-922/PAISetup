"""보고 맞춤의 대화 명령 — 사용자가 대화에서 「이런 건 안 올려도 됨」 · 「내일 다시」 하신 것을 보고 맞춤 파일에 보이고 더하고 걷고, 열린 보고
창에 바로 알린다. 일일 보고 스킬의 맞춤 손 — 파일의 꼴 · 읽기 · 쓰기는 곁의 `prefs_file.py` 가 든다.

    python -X utf8 -I prefs.py --dir <사용자 폴더> show                       맞춤 파일의 두 절을 번호와 함께 보인다
    python -X utf8 -I prefs.py --dir <사용자 폴더> quiet "<사용자의 말>"      「올리지 않을 것」에 그 말을 더한다
    python -X utf8 -I prefs.py --dir <사용자 폴더> later "<일 이름>" --mail <메일 번호>   「내일 다시 볼 것」에 더한다(돌아오는 날은 내일)
    python -X utf8 -I prefs.py --dir <사용자 폴더> forget <번호> [--later]    「올리지 않을 것」(--later 면 「내일 다시 볼 것」)의 그 번호 줄을
                                                                             걷는다(show 의 번호) — 미룬 일을 걷으면 다음 보고부터 다시 선다
    python -X utf8 -I prefs.py --dir <사용자 폴더> decline                    처음 보고 때 여쭌 메일함 스캔 · 아침 보고를 마다하신 것을 적는다 —
                                                                             show 가 「걸지 않기로 하신 것」으로 대면 다시 여쭙지 않는다

파일은 사용자 폴더의 `daily-brief-prefs.md` 하나다(업무 파일 곁 · 쓰는 손은 이것 · 보고 창 표시를 거두는 `ticks.py` · 옛 꼴을 옮기는 `finish.py`). 보고를 짓는 쪽은
`ticks.py` 의 끝 줄들로 받는다 — 무엇을 올리지 않고, 무엇이 오늘 돌아왔고, 무엇을 아직 미루나.

내는 것 — 표준 출력의 끝 줄이 한 일을 말한다. 종료 값 — 0 됐다 · 1 못 했다(번호가 없다 · 못 썼다) · 2 인자가 틀렸다.
무엇을 지키고 왜 그런가는 `references/DESIGN.md` 「보고 맞춤」이 든다.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 prefs_file.py · state.py(창에 알리기) — `-I` 로 돌아도 싣는다
import cli  # noqa: E402
import clock as T  # noqa: E402
import state as V  # noqa: E402
from brief_const import EXIT_FAIL, EXIT_OK  # noqa: E402
from brief_inline import UNID_HEX  # noqa: E402
from prefs_file import (BACK, BACK_AT, DECLINED, DECLINED_LINE, LATER, LATER_LINE, QUIET, QUIET_FROM_TALK, Prefs, Unreadable, clean,  # noqa: E402
                        path_of, put_later, put_quiet, read, write)

NO_FOLDER = "맞춤 파일을 못 다뤘다 — 폴더가 없다: {folder}. 다음: 업무 파일이 있는 사용자 폴더를 --dir 로 준다"
UNREAD = ("맞춤 파일을 못 읽어 아무것도 안 바꿨다({path}: {exc}) — 빈 것으로 읽고 쓰면 감추고 미룬 일이 사라진다. 다음: 그 파일을 "
          "확인하고 다시 부른다")
UNWRITTEN = "맞춤 파일을 못 썼다({path}: {exc}). 다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다"
EMPTY_WORDS = "더하지 않았다 — 말이 비었다. 다음: 올리지 않을 일을 사용자의 말로 준다"
BAD_MAIL = "더하지 않았다 — 메일 번호가 32자리가 아니다: {mail!r}"
NO_ROW = "걷지 않았다 — 「{name}」에 {number}번 줄이 없다({rows}줄). 다음: show 의 번호로 다시 부른다"
NO_TITLE = "이름 없는 일"
WHERE_TALK = "대화에서"
UNID32 = re.compile(UNID_HEX)


# ── 동사 — 동사마다 맞춤을 고치고 한 일의 말을 낸다(못 하면 `cli.Stop`) ─────────────────────

def show_lines(prefs: Prefs, path: pathlib.Path) -> list[str]:
    """`show` — 두 절을 번호와 함께, 다시 올린 것 · 걸지 않기로 하신 것은 있을 때만, 그리고 끝 줄. 그 절이 없는 옛 파일이면 걸지 않기로 하신
    것은 읽는 손이 지난 보고 글의 옛 꼴 한 줄에서 읽어 들인 것이다."""
    out = [f"## {QUIET}", "\n".join(f"{i}. {x[2:]}" for i, x in enumerate(prefs.quiet, 1)) or "없음",
           f"## {LATER}", "\n".join(f"{i}. {x[2:]}" for i, x in enumerate(prefs.later, 1)) or "없음"]
    if prefs.back:                         # 돌아와 보고에 댄 일 — 다음 보고가 지어지면 걷힌다(번호로 걷는 줄이 아니다)
        out += [f"## {BACK}", "\n".join(f"- {BACK_AT.sub('', x)[2:]}" for x in prefs.back)]
    declined = [x[2:] for x in prefs.declined]
    if declined:
        out += [f"## {DECLINED}", "\n".join(f"- {x}" for x in declined)]
    out.append(f"맞춤 파일: {path} — 올리지 않을 것 {len(prefs.quiet)}줄 · 내일 다시 볼 것 {len(prefs.later)}줄"
               + (f" · 다시 올린 것 {len(prefs.back)}줄" if prefs.back else "") + (" · 걸지 않기로 하신 것 있음" if declined else ""))
    return out


def add_quiet(prefs: Prefs, raw: str, now: dt.datetime) -> str:
    """`quiet` — 사용자의 말을 「올리지 않을 것」에 더한다. 말이 비면 `cli.Stop`."""
    words = clean(raw)
    if not words:
        raise cli.Stop(EMPTY_WORDS)
    put_quiet(prefs, QUIET_FROM_TALK.format(words=words, when=T.day_words(now)))
    return f"「{QUIET}」에 더했다: {words}"


def add_later(prefs: Prefs, title: str, mail: str, now: dt.datetime) -> str:
    """`later` — 그 일을 「내일 다시 볼 것」에 더한다(돌아오는 날은 내일). 메일 번호가 32자리가 아니면 `cli.Stop`."""
    if not UNID32.fullmatch(mail):
        raise cli.Stop(BAD_MAIL.format(mail=mail))
    due = (now.date() + dt.timedelta(days=1)).isoformat()
    put_later(prefs, LATER_LINE.format(title=clean(title) or NO_TITLE, due=due, when=T.day_words(now), where=WHERE_TALK, unid=mail.upper()))
    return f"「{LATER}」에 더했다 — {due} 첫 보고에 다시 올린다"


def note_declined(prefs: Prefs, now: dt.datetime) -> str:
    """`decline` — 처음 보고 때 여쭌 메일함 스캔 · 아침 보고를 마다하신 것을 적는다."""
    prefs.declined = [DECLINED_LINE.format(day=now.date().isoformat(), where=WHERE_TALK)]
    return f"「{DECLINED}」에 적었다 — 메일함 스캔 · 아침 보고를 다시 여쭙지 않는다(이 줄을 지우시면 다음 보고 때 다시 여쭙는다)"


def forget_row(prefs: Prefs, number: int, later: bool) -> str:
    """`forget` — 「올리지 않을 것」(`later` 면 「내일 다시 볼 것」)의 그 번호 줄을 걷는다. 그 번호가 없으면 `cli.Stop`."""
    rows, name = (prefs.later, LATER) if later else (prefs.quiet, QUIET)
    if not 1 <= number <= len(rows):
        raise cli.Stop(NO_ROW.format(name=name, number=number, rows=len(rows)))
    gone = rows.pop(number - 1)
    return f"「{name}」에서 걷었다: {gone[2:]} — " + ("다음 보고부터 그 일을 다시 올린다" if later else "다음 보고부터 그런 일도 다시 올린다")


def changed(args: argparse.Namespace, prefs: Prefs, now: dt.datetime) -> str:
    """바꾸는 동사 하나를 부른다 — 한 일의 말."""
    if args.verb == "quiet":
        return add_quiet(prefs, args.words, now)
    if args.verb == "later":
        return add_later(prefs, args.title, args.mail, now)
    if args.verb == "decline":
        return note_declined(prefs, now)
    return forget_row(prefs, args.number, args.later)


# ── 대화의 명령 ───────────────────────────────────────────────────────────────

def opened(folder: pathlib.Path) -> Prefs:
    """쓰기 전에 맞춤 파일을 읽는다 — 폴더가 없거나 못 읽으면 `cli.Stop`(빈 것으로 읽고 쓰면 감추고 미룬 일이 사라진다)."""
    if not folder.is_dir():
        raise cli.Stop(NO_FOLDER.format(folder=folder))
    try:
        return read(folder, strict=True)
    except Unreadable as exc:
        raise cli.Stop(UNREAD.format(path=path_of(folder), exc=exc)) from exc


def saved(folder: pathlib.Path, prefs: Prefs) -> None:
    """맞춤 파일을 쓴다 — 못 쓰면 `cli.Stop`."""
    try:
        write(folder, prefs)
    except OSError as exc:
        raise cli.Stop(UNWRITTEN.format(path=path_of(folder), exc=exc)) from exc


def parser() -> argparse.ArgumentParser:
    """인자 — 동사 다섯."""
    ap = argparse.ArgumentParser(description="보고 맞춤 파일 — 올리지 않을 것 · 내일 다시 볼 것을 보이고 더하고 걷는다.")
    ap.add_argument("--dir", required=True, help="업무 파일(work.md)과 보고 글이 사는 사용자 폴더")
    sub = ap.add_subparsers(dest="verb", required=True)
    sub.add_parser("show", help="두 절을 번호와 함께 보인다")
    q = sub.add_parser("quiet", help="「올리지 않을 것」에 사용자의 말을 더한다")
    q.add_argument("words")
    later = sub.add_parser("later", help="「내일 다시 볼 것」에 더한다(돌아오는 날은 내일)")
    later.add_argument("title")
    later.add_argument("--mail", required=True, help="그 일의 메일 번호(32자리) — 보고 줄의 「일:」 칸, 없으면 그 줄의 첫 메일 링크")
    f = sub.add_parser("forget", help="「올리지 않을 것」(--later 면 「내일 다시 볼 것」)의 그 번호 줄을 걷는다")
    f.add_argument("number", type=int)
    f.add_argument("--later", action="store_true", help="「내일 다시 볼 것」의 번호다 — 미룬 일을 걷어 다음 보고부터 다시 올린다")
    sub.add_parser("decline", help="처음 보고 때 여쭌 메일함 스캔 · 아침 보고를 마다하신 것을 적는다 — 다시 여쭙지 않는다")
    return ap


def main(argv: list[str] | None = None) -> int:
    """명령 입구 — 맞춤 파일을 열어 받은 하위 명령대로 보이거나 고쳐 쓰고, 열린 창에 알린 뒤 끝 줄을 낸다. 종료 값 — 0 · 1 못 읽었거나 못 썼다."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    folder = pathlib.Path(args.dir)
    try:
        prefs = opened(folder)
        if args.verb == "show":
            cli.say(show_lines(prefs, path_of(folder)))
            return EXIT_OK
        done = changed(args, prefs, T.wall_now())
        saved(folder, prefs)
    except cli.Stop as stop:
        cli.say([stop.line])
        return EXIT_FAIL
    told = V.sync(folder)
    cli.say([done_words(done, path_of(folder), told)])
    return EXIT_OK


def done_words(done: str, path: pathlib.Path, told: str) -> str:
    """끝 줄 — 한 일 · 맞춤 파일의 자리 · 열린 창에 알렸으면 그 말."""
    return f"{done} · 맞춤 파일 {path}" + (f" · {told}" if told else "")


if __name__ == "__main__":
    sys.exit(main())
