"""보고 글(md)을 보고 창의 틀에 채워 그날의 HTML 로 남기고, 그 글을 곁에 남기고, 브라우저로 띄운다 — 일일 보고 스킬의 내는 손.

    python -X utf8 -I window.py --dir <사용자 폴더> --mailbox <메일함 주소> [--in <보고 글>] [--no-open]
    python -X utf8 -I window.py --dir <사용자 폴더> --sheet <보고 글 이름> [--slot "YYYY-MM-DD HH:MM"]   메일 한 장(자리 밖에서 보기)
    python -X utf8 -I window.py --dir <사용자 폴더> --latest      가장 늦은 보고 글의 자리와 지은 때 — 코드가 읽는 JSON 한 줄

    보고 글 — `--in` 의 파일, 없으면 표준 입력(UTF-8 · BOM 있는 UTF-16 · cp949). 꼴은 `lane.md` 「보고 글의 꼴」이 든다
    --dir     — 창과 보고 글을 남길 사용자 폴더. 한 번만 받는다(사람 없는 실행이 고정한 경계라서다) · 없는 폴더는 만들지 않는다
    --mailbox — 회사 메일 스킬의 `session` 이 낸 메일함 주소. 없거나 꼴이 아니면 메일 줄을 링크 없이 세운다
    --no-open — 짓기만 하고 띄우지 않는다. 띄울 때는 로그인 Edge 의 새 탭이 먼저고, 안 되면 기본 브라우저다
    --latest  — 가장 늦은 보고 글(.md)의 자리와 지은 때(이 PC 의 시각)를 `{"brief": 자리, "made": "YYYY-MM-DDTHH:MM"}` 한 줄로 낸다 — 없으면
                `{}`. 보고 글의 이름 꼴을 아는 곳은 이 스킬 하나다 — 형제 스킬은 이 답을 읽는다. 폴더가 없으면 종료 1
    --sheet   — 창 대신 같은 보고 글에서 휴대폰 너비의 메일 한 장을 지어 표준 출력에 JSON({subject, html, text})으로 낸다. 아무것도 안 쓰고
                안 띄우고 안 보낸다 — 보내는 것은 사람 없는 실행의 시계 판이다(켠 PC 에서만)

내는 것 — `<--dir>/brief-YYYY-MM-DD-HHMM.html`(이 PC 의 시각)과 같은 이름의 `.md`(받은 보고 글을 마무리한 글 · 다음 보고가 읽는 기록). 짓기
전에 곁의 `finish.py` 가 받은 글을 마무리한다 — 지난 보고 글의 기록 절을 잇고, 「일정 넣기」 줄마다 곁의 일정 손 미리 보기(일정을 안 바꾼다)를
불러 열쇠를 단다. 표준 출력의 끝 줄이 두 파일 · 절 · 줄 · 메일 링크의 수 · 띄웠나를 말하고, 경고 줄이 앞에, 「다음: …」이 뒤에 선다. 메일함
주소는 부르지 않는다.
창의 끝에는 「보고 맞추기」가 선다 — 같은 폴더의 보고 시각표(사람 없는 실행 `unattended/` 의 설정)와 보고 맞춤 파일(곁의 `prefs.py`)을 읽기만 해 보인다.
카드의 「바로 할 일」 · 「대화로 할 일」 칸(맡길 일)은 표시 칸 · 단추로 서고 창 머리 아래에 「바로 맡길 일」 막대가 선다 — 창은 누름만 남기고,
하는 것은 창 곁의 손이다. 로그인 Edge 에 연 창이면 그 곁에 누름을 바로 거두는 손(곁의 `presses.py`)을 띄운다 — 맡길 일이 없어도 보고가 걸려
「자리 밖에서 보기」 단추가 서는 창이면 띄운다. 창 머리에는 「비서에게 부탁하기」 칸이 선다 — 이 PC 에 VS Code 의
Claude Code 확장이 있을 때만(곁의 `asks.py` 가 대화를 연다 · 그 칸이 서는 창도 손을 띄운다).
무엇을 지키고 왜 그런가는 `references/DESIGN.md` 가 든다.

종료 값 — 0 지었다 · 1 못 지었다(제목이 없다 · 글을 못 읽었다 · 폴더가 없다 · 못 썼다 — 끝 줄이 다음 걸음을 말한다) · 2 인자가 틀렸다.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import webbrowser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손 · 손가락들 — `-I` 로 돌아도 싣는다
import clock as T  # noqa: E402
import asks  # noqa: E402
import cli  # noqa: E402
import edge as E  # noqa: E402
import finish as F  # noqa: E402
import prefs_file as P  # noqa: E402
import presses  # noqa: E402
import store as S  # noqa: E402
import window_words as W  # noqa: E402
from hand_wanted import hand_wanted  # noqa: E402
from render import Ink, build  # noqa: E402
from render_mail import mail_sheet  # noqa: E402
from state import state_of  # noqa: E402
from brief_const import EXIT_FAIL, EXIT_OK, FILE_NAME, LATEST_BRIEF, LATEST_MADE  # noqa: E402
from brief_files import TEXT_SUFFIX, kept_briefs, made_of  # noqa: E402
from brief_inline import url_count  # noqa: E402
from brief_sections import missing_ends  # noqa: E402
from brief_text import parse  # noqa: E402

# 메일함 주소 — `http(s)://<호스트>[:<포트>]/…/<이름>.nsf`. 호스트 앞에 사용자 칸(@)이 서는 꼴 · 따옴표 · 빈칸 · 물음표는 받지 않는다
MAILBOX = re.compile(r"^https?://[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::\d{1,5})?(?:/[A-Za-z0-9._~%-]+)*/[A-Za-z0-9._~%-]+\.nsf$",
                     re.IGNORECASE)
SLOT = re.compile(r"^(\d{4}-\d{2}-\d{2}) ((?:[01]\d|2[0-3]):[0-5]\d)$")   # 칸 — 그 칸이 든 날과 그 시각(`--slot`)

# ── 들고 나기 ─────────────────────────────────────────────────────────────

def decode(raw: bytes) -> str:
    """받은 바이트 → 글. BOM 이 있으면 그 꼴(UTF-8 · UTF-16 — Windows PowerShell 의 `>` 가 쓰는 꼴), 없으면 UTF-8, 안 되면 cp949.
    같은 몸이 스킬 mailbox-work 의 `work.py` · mailbox-tidy 의 `journal_io.py` 에 있다 — 고치면 셋을 함께 고친다(머리말의 받는 꼴이 같다)."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", errors="replace")


def mailbox_of(raw: str | None) -> str | None:
    """꼴에 맞는 메일함 주소(끝의 / 를 뗀 것) — 없거나 꼴이 아니면 None."""
    url = (raw or "").strip().rstrip("/")
    return url if MAILBOX.match(url) else None


def slot_of(raw: str) -> tuple[str, dt.date | None]:
    """`--slot` 의 값 → (그 시각 HH:MM, 그 날) — 꼴이 아니면 ("", None)."""
    slot = SLOT.match(raw)
    return (slot.group(2), dt.date.fromisoformat(slot.group(1))) if slot else ("", None)


def received(src: str) -> str:
    """받은 보고 글 — `--in` 의 파일, 없으면 표준 입력을 글로 풀고 줄끝을 「\\n」으로 맞춘다. 못 읽으면 `cli.Stop`."""
    try:
        data = pathlib.Path(src).read_bytes() if src else sys.stdin.buffer.read()
    except OSError as exc:
        raise cli.Stop(W.READ_FAIL.format(src=src, exc=exc)) from exc
    text = decode(data).replace("\r\n", "\n").replace("\r", "\n")
    return text


def titled(text: str, why: str) -> None:
    """글에 제목(맨 위 「# …」)이 있나 — 없으면 그 까닭(`why`)으로 `cli.Stop`."""
    if not parse(text).title:
        raise cli.Stop(why)


def folder_of(raw: str) -> pathlib.Path:
    """창과 보고 글을 남길 사용자 폴더 — 없으면 `cli.Stop`(없는 폴더는 만들지 않는다)."""
    folder = pathlib.Path(raw)
    if not folder.is_dir():
        raise cli.Stop(W.NO_FOLDER.format(folder=folder))
    return folder


def finished(text: str, folder: pathlib.Path) -> tuple[str, list[str]]:
    """받은 글을 마무리한다(`finish.finish` — 지난 보고의 기록 절 · 「일정 넣기」의 열쇠) — (마무리한 글, 경고). 지난 보고 글을 못 읽으면
    `cli.Stop` — 그 글의 기록 절을 잇지 못한 새 글이 그 자리를 덮으면 사용자가 정하신 것이 사라진다."""
    try:
        return F.finish(text, folder)
    except F.Unread as exc:
        raise cli.Stop(W.PREV_UNREAD.format(exc=exc)) from exc


def write_pair(folder: pathlib.Path, now: dt.datetime, page: str, text: str) -> tuple[pathlib.Path, pathlib.Path]:
    """창 HTML 을 쓰고, 선 뒤에만 같은 이름의 보고 글을 남긴다 — (창, 보고 글). 남은 글은 다음 보고가 사용자께 낸 보고로 읽는다. 못 쓰면 `cli.Stop`."""
    out = folder / FILE_NAME.format(now)
    kept = out.with_suffix(TEXT_SUFFIX)
    try:
        out.write_text(page, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise cli.Stop(W.PAGE_FAIL.format(out=out, exc=exc)) from exc
    try:
        kept.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise cli.Stop(W.KEPT_FAIL.format(kept=kept, exc=exc)) from exc
    return out, kept


def open_report(uri: str, hand_for: pathlib.Path | None = None) -> str:
    """보고 창을 로그인 Edge 의 새 탭에, 안 되면 기본 브라우저로 띄우고 어디에 띄웠나를 한 줄로 낸다.
    로그인 Edge 가 먼저다 — 메일 링크가 같은 세션에서 열려야 로그인 창이 안 뜬다. 그 Edge 로 연 창만 주소 꼬리(`VIA_EDGE`)를 달아,
    누르신 표시가 거둬지는 창에서만 단추가 선다. `hand_for`(사용자 폴더)를 주면 그 Edge 에 연 때만 창 곁에 누름을 바로 거두는 손을
    띄운다(곁의 `presses.start_hand`) — 기본 브라우저로 연 창은 거둘 수 없는 창이라 안 띄운다."""
    if E.open_tab(uri):
        return W.edge_words(None if hand_for is None else presses.start_hand(hand_for), hand_for is not None)
    if webbrowser.open(uri):
        return W.IN_BROWSER
    return W.NOWHERE


def shown_where(no_open: bool, out: pathlib.Path, folder: pathlib.Path, wanted: bool) -> str:
    """띄운 곳의 말 — `--no-open` 이면 안 띄우고, 아니면 띄운다(창 곁의 손은 그 손을 띄울 창일 때만 — `wanted`)."""
    if no_open:
        return W.NOT_OPENED
    return open_report(out.resolve().as_uri(), folder if wanted else None)


# ── 세 길 ─────────────────────────────────────────────────────────────────

def sheet_main(folder: pathlib.Path, name: str, slot: str, slot_day: dt.date | None) -> int:
    """`--sheet` — 사용자 폴더의 보고 글 한 장(이름 하나 · 보고 글의 꼴)에서 메일 한 장을 지어 표준 출력에 JSON 으로 낸다. 아무것도 안 쓰고 안
    띄운다(보내는 것은 사람 없는 실행의 시계 판이다)."""
    try:
        made = sheet_made(name)
        text = sheet_text(folder, name)
        titled(text, W.SHEET_NO_TITLE)
    except cli.Stop as stop:
        cli.say([stop.line])
        return EXIT_FAIL
    sys.stdout.buffer.write(json.dumps(mail_sheet(text, made, slot or f"{made:%H:%M}", slot_day), ensure_ascii=False).encode("utf-8"))
    return EXIT_OK


def sheet_made(name: str) -> dt.datetime:
    """`--sheet` 가 받은 이름이 보고 글(이름 하나 · .md · 보고 글 이름의 꼴)이면 그 지은 때 — 아니면 `cli.Stop`."""
    made = made_of(name)
    if made is None or not name.endswith(TEXT_SUFFIX) or pathlib.Path(name).name != name:
        raise cli.Stop(W.SHEET_NOT_BRIEF.format(name=name))
    return made


def sheet_text(folder: pathlib.Path, name: str) -> str:
    """사용자 폴더의 그 보고 글 — 없거나 못 읽으면 `cli.Stop`. 거두는 손이 그 글을 바꿔 끼우는 순간이면 `read_bytes` 가 다시 해 본다."""
    try:
        raw, why = S.read_bytes(folder / name), "FileNotFoundError"
    except S.Unreadable as exc:
        raw, why = None, str(exc).split(":", 1)[0]
    if raw is None:
        raise cli.Stop(W.SHEET_UNREAD.format(name=name, why=why))
    return decode(raw)


def latest_main(folder: pathlib.Path) -> int:
    """`--latest` — 가장 늦은 보고 글의 자리와 지은 때를 JSON 한 줄로 낸다(없으면 `{}`). 아무것도 안 쓴다. 폴더가 없으면 종료 1."""
    if not folder.is_dir():
        cli.say([W.LATEST_NO_FOLDER.format(folder=folder)])
        return EXIT_FAIL
    briefs = kept_briefs(folder)
    got = {LATEST_BRIEF: str(briefs[-1].resolve()), LATEST_MADE: f"{made_of(briefs[-1].name):%Y-%m-%dT%H:%M}"} if briefs else {}
    cli.say([json.dumps(got, ensure_ascii=False)])
    return EXIT_OK


def build_main(args: argparse.Namespace) -> int:
    """창 짓기 — 받은 글 → 제목 · 폴더 → 마무리 → 그리기 → 두 파일 → 경고 → 띄우기 → 끝 줄. 멈추면 그 까닭 한 줄과 종료 1."""
    try:
        text = received(args.src)
        titled(text, W.NO_TITLE)
        folder = folder_of(args.dir)
        text, warned = finished(text, folder)
        rep, ink, now = parse(text), Ink(mailbox_of(args.mailbox)), T.wall_now()
        state, prefs, ready = state_of(folder), P.read(folder), asks.ready()
        page, sections, lines = build(rep, ink, now, state, prefs, ready)
        out, kept = write_pair(folder, now, page, text)
    except cli.Stop as stop:
        cli.say([stop.line])
        return EXIT_FAIL
    ends = missing_ends(rep)
    cli.say(W.warn_lines(warned, rep.extra_titles, sections, ink.bad_refs, url_count(text), ends, ink.bad_puts, ink.bad_tasks, ink.tops,
                         ink.bad_people))
    shown = shown_where(args.no_open, out, folder, hand_wanted(text, bool(state["times"]), ready))
    cli.say(W.end_lines(out, kept, sections, lines, ink.links, len(ink.tasks), shown, ends, ink.unlinked, bool(args.mailbox.strip())))
    return EXIT_OK


def parser() -> argparse.ArgumentParser:
    """인자 — 모델의 길(짓기)과 프로그램이 부르는 문(`--sheet` · `--slot` · `--latest`)을 `--help` 의 다른 절에 둔다."""
    ap = argparse.ArgumentParser(description="보고 글(md)을 보고 창의 틀에 채워 그날의 HTML 로 남기고, 그 글을 곁에 같은 이름의 .md 로 남기고, "
                                             "띄운다. 글의 꼴은 스킬 폴더의 lane.md 「보고 글의 꼴」 · 「남긴다」가 든다.")
    ap.add_argument("--dir", required=True, action=cli.Once, help="그날의 HTML 과 보고 글을 남길 폴더 — 업무 파일(work.md)이 있는 사용자 폴더(한 번만)")
    ap.add_argument("--mailbox", default="", help="회사 메일 스킬 session 이 낸 메일함 주소 http(s)://<호스트>/…/<이름>.nsf")
    ap.add_argument("--in", dest="src", default="", help="보고 글 파일 — 없으면 표준 입력")
    ap.add_argument("--no-open", action="store_true", help="짓기만 하고 브라우저로 띄우지 않는다")
    doors = ap.add_argument_group(cli.DOORS_TITLE, cli.DOORS_NOTE)
    doors.add_argument("--sheet", metavar="보고 글", help="창 대신 그 보고 글(--dir 안의 이름)에서 메일 한 장을 지어 JSON 으로 낸다 — 자리 밖에서 보기(시계 판이 부른다)")
    doors.add_argument("--latest", action="store_true", help="가장 늦은 보고 글의 자리와 지은 때를 JSON 한 줄로 낸다(없으면 {}) — 형제 스킬이 읽는다")
    doors.add_argument("--slot", default="", metavar="YYYY-MM-DD HH:MM",
                       help="--sheet 와 함께 — 그 보고를 띄운 칸의 날과 시각(제목 · 머리에 선다 · 없으면 지은 날 · 때)")
    return ap


def main(argv: list[str] | None = None) -> int:
    """명령 입구 — 받은 길(가장 늦은 보고 · 메일 한 장 · 창 짓기)을 그 손에 나눈다."""
    args = parser().parse_args(argv)
    if args.latest:
        return latest_main(pathlib.Path(args.dir))
    if args.sheet:
        return sheet_main(pathlib.Path(args.dir), args.sheet, *slot_of(args.slot))
    return build_main(args)


if __name__ == "__main__":
    sys.exit(main())
