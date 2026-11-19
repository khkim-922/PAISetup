"""보고 맞춤 파일 — 사용자가 보고 창이나 대화에서 「이런 건 안 올려도 됨」 · 「내일 다시」 하신 것을 사람이 읽는 글로 든다. 일일 보고 스킬의
맞춤 손: 그 파일의 꼴 · 읽기 · 쓰기 · 대화에서 보이고 더하고 걷는 명령.

    python -X utf8 -I prefs.py --dir <사용자 폴더> show                       맞춤 파일의 두 절을 번호와 함께 보인다
    python -X utf8 -I prefs.py --dir <사용자 폴더> quiet "<사용자의 말>"      「올리지 않을 것」에 그 말을 더한다
    python -X utf8 -I prefs.py --dir <사용자 폴더> later "<일 이름>" --mail <메일 번호>   「내일 다시 볼 것」에 더한다(돌아오는 날은 내일)
    python -X utf8 -I prefs.py --dir <사용자 폴더> forget <번호> [--later]    「올리지 않을 것」(--later 면 「내일 다시 볼 것」)의 그 번호 줄을
                                                                             걷는다(show 의 번호) — 미룬 일을 걷으면 다음 보고부터 다시 선다

파일은 사용자 폴더의 `daily-brief-prefs.md` 하나다(업무 파일 곁 · 쓰는 손은 이것과 보고 창 표시를 거두는 `ticks.py` 뿐). 보고를 짓는 쪽은
`ticks.py` 의 끝 줄들로 받는다 — 무엇을 올리지 않고, 무엇이 오늘 돌아왔고, 무엇을 아직 미루나.

내는 것 — 표준 출력의 끝 줄이 한 일을 말한다. 종료 값 — 0 됐다 · 1 못 했다(번호가 없다 · 못 썼다) · 2 인자가 틀렸다.
무엇을 지키고 왜 그런가는 `references/DESIGN.md` 「보고 맞춤」이 든다.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import pathlib
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 ticks.py(창에 알리기) — `-I` 로 돌아도 싣는다

FILE_NAME = "daily-brief-prefs.md"
TITLE = "# 일일 보고 — 사용자께 맞춘 것"
INTRO = "보고 창에서 누르시거나 대화에서 말씀하신 것을 보고가 날마다 읽습니다. 줄을 지우시면 그대로 따릅니다."
QUIET = "올리지 않을 것"           # 사용자가 올리지 말라고 하신 일의 보기 — 보고는 같은 갈래의 일을 올리지 않는다
LATER = "내일 다시 볼 것"          # 「내일 다시」 하신 일 — 돌아오는 날의 첫 보고에 다시 선다
EMPTY = "- 없음"
UNID = re.compile(r"\(mail:([0-9A-Fa-f]{32})\)")
DUE = re.compile(r"`(\d{4}-\d{2}-\d{2})`")
TITLE_MAX = 80
NUMBERISH = re.compile(r"\(?mail:[^\s)]*\)?|\b[0-9A-Fa-f]{32}\b")   # 이름 속 메일 번호 꼴 — 다음 보고가 그 번호를 이 일의 메일로 읽는다
EXIT_OK, EXIT_FAIL = 0, 1

QUIET_FROM_WINDOW = "- 「{title}」 같은 일 — {when} 보고 창에서 「이런 건 안 올려도 됨」 하셨습니다 [보기 메일](mail:{unid})"
QUIET_FROM_TALK = "- {words} — {when} 대화에서 말씀하셨습니다"
LATER_LINE = "- {title} — `{due}` 첫 보고에 다시 올립니다 · {when} {where} 「내일 다시」 하셨습니다 [근거 메일](mail:{unid})"


@dataclass
class Prefs:
    quiet: list[str] = field(default_factory=list)
    later: list[str] = field(default_factory=list)


def path_of(folder: pathlib.Path) -> pathlib.Path:
    return folder / FILE_NAME


def lines_of(text: str, name: str) -> list[str]:
    """절 `name`(「## 」 머리) 아래 「- 」 줄 — 「없음」은 뺀다."""
    out, inside = [], False
    for row in text.splitlines():
        if row.startswith("## "):
            inside = row[3:].strip().startswith(name)
            continue
        if inside and row.startswith("- ") and row.strip() != EMPTY:
            out.append(row.rstrip())
    return out


def read(folder: pathlib.Path) -> Prefs:
    """맞춤 파일 — 없거나 못 읽으면 빈 것. 사람이 손으로 고친 파일도 「- 」 줄만 읽는다."""
    try:
        text = path_of(folder).read_bytes().decode("utf-8-sig", errors="replace")
    except OSError:
        return Prefs()
    return Prefs(lines_of(text, QUIET), lines_of(text, LATER))


def write(folder: pathlib.Path, prefs: Prefs) -> None:
    """맞춤 파일을 곁의 임시 파일에 다 쓴 뒤 바꿔 끼운다. 쓰지 못하면 OSError."""
    body = [TITLE, "", INTRO, "", f"## {QUIET}", *(prefs.quiet or [EMPTY]), "", f"## {LATER}", *(prefs.later or [EMPTY]), ""]
    tmp = folder / f".{FILE_NAME}.tmp"
    try:
        tmp.write_bytes("\n".join(body).encode("utf-8"))
        os.replace(tmp, path_of(folder))
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


def key(line: str) -> str:
    """줄의 열쇠 — 메일 번호가 있으면 그 번호(대문자), 없으면 글에서 낸 짧은 지문(「w」 + 10자리). 보고 창의 「다시 올리기」가 이 열쇠로 그 줄을 짚는다."""
    m = UNID.search(line)
    return m.group(1).upper() if m else "w" + hashlib.sha1(line.encode("utf-8")).hexdigest()[:10]


def unid_of(line: str) -> str | None:
    m = UNID.search(line)
    return m.group(1).upper() if m else None


def due_of(line: str) -> dt.date | None:
    """「내일 다시」 줄이 돌아오는 날 — 꼴이 아니면 None(그런 줄은 바로 돌아온 것으로 본다)."""
    m = DUE.search(line)
    try:
        return dt.date.fromisoformat(m.group(1)) if m else None
    except ValueError:
        return None


def clean(words: str) -> str:
    """줄에 들일 글 — 줄바꿈 · 꼴 표시 · 메일 번호 꼴을 걷고 줄인다. 창의 칸이나 대화에서 온 글이라 절 머리 · 링크로 서지 못하게 한다."""
    words = " ".join(str(words or "").split())
    words = re.sub(r"[\[\]{}`*#<>]", "", NUMBERISH.sub("", words)).strip(" -—")
    return (words[:TITLE_MAX - 1].rstrip() + "…") if len(words) > TITLE_MAX else words


def when_words(at: dt.datetime) -> str:
    return f"{at.month}/{at.day}"


def put_quiet(prefs: Prefs, line: str) -> None:
    """「올리지 않을 것」에 한 줄 — 같은 열쇠의 줄은 바꾼다. 그 메일이 「내일 다시」에 있으면 걷는다(뒤에 누르신 것이 이긴다)."""
    k = key(line)
    prefs.quiet = [x for x in prefs.quiet if key(x) != k] + [line]
    prefs.later = [x for x in prefs.later if unid_of(x) != unid_of(line) or unid_of(line) is None]


def put_later(prefs: Prefs, line: str) -> None:
    """「내일 다시 볼 것」에 한 줄 — 같은 메일의 줄은 바꾸고, 그 메일의 「올리지 않을 것」 줄은 걷는다."""
    u = unid_of(line)
    prefs.later = [x for x in prefs.later if unid_of(x) != u] + [line]
    prefs.quiet = [x for x in prefs.quiet if unid_of(x) != u]


def drop_unid(prefs: Prefs, unid: str) -> bool:
    """그 메일의 줄을 두 절에서 다 걷는다 — 걷은 것이 있으면 True."""
    before = len(prefs.quiet) + len(prefs.later)
    prefs.quiet = [x for x in prefs.quiet if unid_of(x) != unid]
    prefs.later = [x for x in prefs.later if unid_of(x) != unid]
    return len(prefs.quiet) + len(prefs.later) != before


def forget(prefs: Prefs, k: str) -> str | None:
    """「올리지 않을 것」에서 열쇠 `k` 의 줄을 걷는다 — 걷은 줄이나 None."""
    for line in prefs.quiet:
        if key(line) == k:
            prefs.quiet.remove(line)
            return line
    return None


def take_due(prefs: Prefs, today: dt.date, first: bool) -> tuple[list[str], list[str]]:
    """(돌아온 줄, 아직 미룬 줄) — 돌아온 줄은 맞춤 파일에서 걷는다. 돌아오는 날이 지났거나, 오늘이 그날이고 이 보고가 오늘의 첫 보고면
    돌아온다. 날이 꼴이 아닌 줄도 돌아온다 — 미룬 채 잊히지 않게."""
    back, wait = [], []
    for line in prefs.later:
        due = due_of(line)
        (back if due is None or due < today or (due == today and first) else wait).append(line)
    prefs.later = wait
    return back, wait


def tell(folder: pathlib.Path) -> str:
    """열린 보고 창에 바뀐 맞춤을 바로 알린다 — 곁의 거두는 손(`ticks.sync`)으로 이 PC 의 디버깅 포트에만. 못 하면 ""(다음에 거둘 때 따라간다)."""
    import ticks  # noqa: PLC0415 — ticks 가 이 모듈을 싣는다. 대화의 명령에서만 싣는다
    return ticks.sync(folder)


# ── 대화의 명령 ───────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="보고 맞춤 파일 — 올리지 않을 것 · 내일 다시 볼 것을 보이고 더하고 걷는다.")
    ap.add_argument("--dir", required=True, help="업무 파일(work.md)과 보고 글이 사는 사용자 폴더")
    sub = ap.add_subparsers(dest="verb", required=True)
    sub.add_parser("show", help="두 절을 번호와 함께 보인다")
    q = sub.add_parser("quiet", help="「올리지 않을 것」에 사용자의 말을 더한다")
    q.add_argument("words")
    later = sub.add_parser("later", help="「내일 다시 볼 것」에 더한다(돌아오는 날은 내일)")
    later.add_argument("title")
    later.add_argument("--mail", required=True, help="그 일의 메일 번호(32자리) — 보고 줄의 첫 메일 링크")
    f = sub.add_parser("forget", help="「올리지 않을 것」(--later 면 「내일 다시 볼 것」)의 그 번호 줄을 걷는다")
    f.add_argument("number", type=int)
    f.add_argument("--later", action="store_true", help="「내일 다시 볼 것」의 번호다 — 미룬 일을 걷어 다음 보고부터 다시 올린다")
    args = ap.parse_args(argv)

    folder = pathlib.Path(args.dir)
    if not folder.is_dir():
        print(f"맞춤 파일을 못 다뤘다 — 폴더가 없다: {folder}. 다음: 업무 파일이 있는 사용자 폴더를 --dir 로 준다")
        return EXIT_FAIL
    prefs = read(folder)
    now = dt.datetime.now()
    if args.verb == "show":
        print(f"## {QUIET}")
        print("\n".join(f"{i}. {x[2:]}" for i, x in enumerate(prefs.quiet, 1)) or "없음")
        print(f"## {LATER}")
        print("\n".join(f"{i}. {x[2:]}" for i, x in enumerate(prefs.later, 1)) or "없음")
        print(f"맞춤 파일: {path_of(folder)} — 올리지 않을 것 {len(prefs.quiet)}줄 · 내일 다시 볼 것 {len(prefs.later)}줄")
        return EXIT_OK
    if args.verb == "quiet":
        words = clean(args.words)
        if not words:
            print("더하지 않았다 — 말이 비었다. 다음: 올리지 않을 일을 사용자의 말로 준다")
            return EXIT_FAIL
        put_quiet(prefs, QUIET_FROM_TALK.format(words=words, when=when_words(now)))
        done = f"「{QUIET}」에 더했다: {words}"
    elif args.verb == "later":
        if not re.fullmatch(r"[0-9A-Fa-f]{32}", args.mail):
            print(f"더하지 않았다 — 메일 번호가 32자리가 아니다: {args.mail!r}")
            return EXIT_FAIL
        due = (now.date() + dt.timedelta(days=1)).isoformat()
        put_later(prefs, LATER_LINE.format(title=clean(args.title) or "이름 없는 일", due=due, when=when_words(now), where="대화에서",
                                           unid=args.mail.upper()))
        done = f"「{LATER}」에 더했다 — {due} 첫 보고에 다시 올린다"
    else:
        rows, name = (prefs.later, LATER) if args.later else (prefs.quiet, QUIET)
        if not 1 <= args.number <= len(rows):
            print(f"걷지 않았다 — 「{name}」에 {args.number}번 줄이 없다({len(rows)}줄). 다음: show 의 번호로 다시 부른다")
            return EXIT_FAIL
        gone = rows.pop(args.number - 1)
        done = f"「{name}」에서 걷었다: {gone[2:]} — " + ("다음 보고부터 그 일을 다시 올린다" if args.later else "다음 보고부터 그런 일도 다시 올린다")
    try:
        write(folder, prefs)
    except OSError as exc:
        print(f"맞춤 파일을 못 썼다({path_of(folder)}: {exc}). 다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다")
        return EXIT_FAIL
    told = tell(folder)
    print(f"{done} · 맞춤 파일 {path_of(folder)}" + (f" · {told}" if told else ""))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
