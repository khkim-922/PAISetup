"""보고 창에서 누르신 것을 로그인 Edge 에서 거둔다 — 일일 보고 스킬의 거두는 손. 「끝났음」 · 푸신 「끝났음」은 가장 늦은 보고 글의
「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에, 「내일 다시」 · 「이런 건 빼기」 · 「다시 넣기」는 보고 맞춤 파일(곁의 `prefs.py`)에
옮기고, 끝에 이 보고가 보고에서 빼는 것 · 오늘 돌아온 것 · 아직 미룬 것을 댄다.

    python -X utf8 -I ticks.py --dir <사용자 폴더>
    python -X utf8 -I ticks.py --dir <사용자 폴더> --times-done <고르신 때> --said <말> [--refused]   시각을 받았나를 그 창에 돌려 적는다
    python -X utf8 -I ticks.py --dir <사용자 폴더> --away-done <고르신 때> --said <말> [--refused]    자리 밖에서 보기를 받았나를 돌려 적는다
    python -X utf8 -I ticks.py --dir <사용자 폴더> --presses [--within 초]                  「일정에 넣기」 누름을 거둬 넣는다(시계 판)
    python -X utf8 -I ticks.py --dir <사용자 폴더> --watch                                  창 곁에 남아 그 누름을 바로 거둔다(창을 여는 손이 띄운다)
    (셋 다 · 그리고 거둔 뒤에도 열린 창에 지금 모습(`state.state_of` — 시각표 · 규칙의 수 · 맞춤 파일의 두 절)을 적는다 — 창은 그보다 앞서
    고른 것을 낡았다고 알고, 대화에서 바꾸신 것을 다음 시계 판을 기다리지 않고 보인다. 대화의 명령은 같은 알림을 함수로 부른다 — `state.sync`)

    --dir — 보고 글(brief-….md)이 사는 사용자 폴더. 한 번만 받는다 · 그 안의 이름이 가장 늦은 보고 글 하나만 고친다
    --times-done · --away-done — 같은 스킬의 시계 판(`unattended/clock.py tick`)이 부른다. 열린 file: 탭이 없으면 아무것도 안
    연다(고르신 것을 읽는 쪽은 그 판이 `window_door.read_choices` 로 함수로 부른다)
    --presses · --watch — 곁의 `presses.py` 가 든다(그 머리말). 열린 보고 창이 없으면 아무것도 안 연다

표시는 창(file://)의 localStorage 에 있다(`assets/report.js`). 로그인 Edge(스킬 ep-login 이 연 디버깅 포트 — `EDGE_DEBUG_PORT`
기본 9222)의 file: 탭 하나에서 읽고, 열린 file: 탭이 없으면 가장 늦은 보고 창을 뒤 탭으로 잠깐 열어 읽고 닫는다. 옮긴 표시에는 남긴 때를
적어 두어 다시 옮기지 않고, 그 절에 이미 든 메일 번호도 더하지 않는다. 부르는 곳은 이 PC 의 디버깅 포트뿐이다 — 메일함에 닿지 않는다.

내는 것 — 표준 출력의 끝 줄이 더한 수 · 이미 든 수 · 고친 보고 글을 말하고, 거둘 수 없었으면 「다음: …」이 뒤에 선다. 그 앞 줄들이
맞춤 파일의 보고에서 빼는 것 · 돌아온 것 · 미룬 것과 지난 보고 뒤 창에서 누르신 「일정에 넣기」 · 맡기신 일의 끝이다(Edge 에 못 닿아도 댄다).
종료 값 — 0 거뒀다(거둘 표시가 없었던 것도) · 1 보고 글이나 맞춤 파일을 못 고쳤다 · 2 인자가 틀렸다 · 3 로그인 Edge 에 못 닿았다(표시는 그
Edge 에 남는다). 무엇을 지키고 왜 그런가는 `references/DESIGN.md` 「누르신 표시」 · 「보고 맞춤」이 든다.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
import brief_const as C  # noqa: E402
import cli  # noqa: E402
from brief_files import kept_briefs, made_of  # noqa: E402
from brief_inline import UNID  # noqa: E402
from brief_sections import DONE_SECTION, REOPEN_SECTION, fold, section_keys  # noqa: E402
import clock as T  # noqa: E402
import edge as E  # noqa: E402
import prefs_file as P  # noqa: E402
import press_kinds as M  # noqa: E402
import presses  # noqa: E402
import state as V  # noqa: E402
import store as S  # noqa: E402
import window_door as D  # noqa: E402
from brief_const import EXIT_FAIL, EXIT_NO_EDGE, EXIT_OK  # noqa: E402
from report_reads import report_lines  # noqa: E402

LINE = "- {title} — {when}보고 창에서 끝났다고 표시하셨습니다 [근거 메일](mail:{unid})"
REOPEN_LINE = "- {title} — {when}보고 창에서 끝나지 않았다고 표시하셨습니다 [근거 메일](mail:{unid})"
MARKS = ("done", "open", "later", "quiet", "clear")    # 표시의 값 — `assets/report.js` 가 적는 것. 옛 표시는 done(참 · 거짓)만 든다

NO_BRIEF = "거둘 자리가 없다 — {folder} 에 보고 글(brief-….md)이 없다. 창이 선 적이 없으니 표시도 없다"
NOTHING_NEW = "거둘 표시가 없다 — 창에서 새로 누르신 것이 없다(남긴 표시 {n}건) · 보고 글 {latest}"
BRIEF_UNREAD = "표시를 못 남겼다 — 보고 글을 못 읽었다({latest}: {exc}). 표시는 창에 그대로 있다. 다음: 그 파일을 확인하고 다시 부른다"
BRIEF_UNWRITTEN = "표시를 못 남겼다 — 보고 글을 못 썼다({latest}: {exc}). 표시는 창에 그대로 있다. 다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다"
PREFS_UNWRITTEN = ("표시를 못 남겼다 — 보고 맞춤 파일을 못 썼다({path}: {exc}). 표시는 창에 그대로 있다. 다음: 그 폴더에 "
                   "쓸 수 있는지 보고 다시 부른다")
UNSTAMPED = "경고: 보고 글 · 맞춤 파일에는 남겼지만 창에 「남겼다」를 못 적었다({exc}) — 다음 판이 보고 글에 든 번호를 보고 다시 더하지 않는다"
EDGE_LOST = ("표시를 못 거뒀다 — 로그인 Edge 와 주고받다 멈췄다({exc}). 누르신 표시는 그 Edge 에 남아 다음에 거둔다. "
             "다음: 대화에서 끝났다고 하신 일만 보고 글에 더하고 이어 간다")
PREFS_UNREAD = "표시를 못 거뒀다 — 보고 맞춤 파일을 못 읽었다({path}: {exc}). 표시는 창에 그대로 있다. 다음: 그 파일을 확인하고 다시 부른다"
BACK_UNWRITTEN = "경고: 돌아온 것을 보고 맞춤 파일에 못 적었다({exc}) — 다음 보고도 돌아온 것으로 다시 댄다"

# ── 표시 → 보고 글의 줄 ──────────────────────────────────────────────────────

def mark_of(value: dict) -> str:
    """표시가 무엇을 누르신 것인가 — `mark`, 옛 표시는 done 이 거짓이면 open · 그 밖은 done. 꼴이 아니면 ""."""
    mark = value.get("mark")
    if mark is None:
        return "open" if value.get("done") is False else "done"
    return mark if mark in MARKS else ""


def ticks_of(rows: list) -> list[tuple[str, dict]]:
    """창에서 읽은 (열쇠, 값) 가운데 꼴에 맞는 누름 표시만 — (메일 번호, 값). 열쇠의 메일 번호가 32자리가 아니거나 값이 꼴이 아니면 버린다."""
    return [(unid.upper(), v) for unid, v in E.stored(rows, C.DONE_PREFIX) if UNID.match(unid) and mark_of(v)]


def title_of(value: dict) -> str:
    """보고 글 한 줄에 설 일 이름 — 줄바꿈 · 꼴 표시를 걷고 길이를 줄인다. 창의 칸에서 온 글이라 절 머리 · 링크로 서지 못하게 한다."""
    return P.clean(str(value.get("title") or "")) or "이름 없는 일"


def when_of(value: dict) -> str:
    """누르신 때 — 이 PC 의 시각으로 「M/D HH:MM」. 꼴이 아니면 빈 글."""
    at = E.pressed_at(value)
    return T.moment_words(at) if at else ""


@dataclass
class Sorted:
    """표시를 나눈 끝 — 고친 보고 글 · 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에 더할 줄 · 그 절에 이미 들어 안 더한 수 · 끝났다 · 푼 ·
    맞춤 파일로 간 번호 · 맞춤 파일로 간 갈래마다의 수."""
    text: str = ""
    add: list[str] = field(default_factory=list)
    reopen: list[str] = field(default_factory=list)
    dup: int = 0
    done_ids: set[str] = field(default_factory=set)
    open_ids: set[str] = field(default_factory=set)
    aside: set[str] = field(default_factory=set)
    n: dict[str, int] = field(default_factory=lambda: {"later": 0, "quiet": 0, "clear": 0, "unquiet": 0})


def sort_marks(text: str, waiting: list[tuple[str, dict]], undo: list[tuple[str, dict]], prefs: P.Prefs) -> Sorted:
    """표시를 나눠 보고 글의 두 절을 고친 글과 맞춤의 바뀜을 짓는다(`prefs` 를 고친다) — 두 절에 이미 든 번호 읽기 → 표시마다 한 갈래
    (`take_mark`) → 「다시 넣기」 → 두 절 고치기(`folded`). 표시는 메일 번호마다 하나다(창의 저장소 열쇠)."""
    have, back = record_keys(text)
    done = Sorted()
    for unid, value in waiting:
        take_mark(done, prefs, unid, value, have, back)
    for k, _ in undo:
        done.n["unquiet"] += P.forget(prefs, k) is not None
    done.text = folded(text, done)
    return done


def record_keys(text: str) -> tuple[set[str], set[str]]:
    """보고 글의 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에 이미 든 줄의 첫 메일 번호."""
    return section_keys(text, DONE_SECTION), section_keys(text, REOPEN_SECTION)


def take_mark(done: Sorted, prefs: P.Prefs, unid: str, value: dict, have: set[str], back: set[str]) -> None:
    """표시 하나를 그 갈래로 얹는다(`done` · `prefs` 를 고친다) — 끝났다는 표시는 「끝났다고 하신 것」에(그 절에 이미 들었으면 세기만), 푸신
    표시는 「안 끝났다고 하신 것」에, 미루거나 올리지 말라신 일은 맞춤 파일로(「끝났다고 하신 것」에서 걷힌다 — 뒤에 누르신 것이 이긴다),
    되돌리신 표시는 맞춤 파일에서 걷는다."""
    mark = mark_of(value)
    when = when_of(value)
    words = dict(title=title_of(value), when=f"{when} " if when else "", unid=unid)
    at = E.pressed_at(value) or T.local_now()
    if mark == "open":
        done.open_ids.add(unid)
        if unid not in back:
            done.reopen.append(REOPEN_LINE.format(**words))
    elif mark == "done":
        done.done_ids.add(unid)
        P.drop_unid(prefs, unid)
        if unid in have:
            done.dup += 1
        else:
            done.add.append(LINE.format(**words))
    elif mark == "later":
        done.aside.add(unid)
        done.n["later"] += 1
        P.put_later(prefs, P.LATER_LINE.format(title=words["title"], due=(at.date() + dt.timedelta(days=1)).isoformat(),
                                               when=T.day_words(at), where="보고 창에서", unid=unid))
    elif mark == "quiet":
        done.aside.add(unid)
        done.n["quiet"] += 1
        P.put_quiet(prefs, P.QUIET_FROM_WINDOW.format(title=words["title"], when=T.day_words(at), unid=unid))
    else:
        done.n["clear"] += 1
        P.drop_unid(prefs, unid)


def folded(text: str, done: Sorted) -> str:
    """보고 글의 두 절을 고친 글 — 끝났다는 줄을 더하고 푼 · 맞춤 파일로 간 번호의 줄을 걷고, 푼 줄을 더하고 끝났다는 번호의 줄을 걷는다."""
    new = fold(text, DONE_SECTION, done.add, done.open_ids | done.aside)
    new = fold(new, REOPEN_SECTION, done.reopen, done.done_ids)
    return new


def collected_words(latest: pathlib.Path, done: Sorted, prefs_path: pathlib.Path) -> str:
    """거둔 끝 줄 — 더한 수 · 이미 든 수 · 옮긴 푼 표시 · 맞춤 파일로 옮긴 갈래마다의 수."""
    n, open_ids, add, dup = done.n, done.open_ids, done.add, done.dup
    moved = [f"「내일 다시」 {n['later']}건", f"「이런 건 빼기」 {n['quiet']}건", f"되돌리신 {n['clear']}건", f"「다시 넣기」 {n['unquiet']}건"]
    moved = [m for m, k in zip(moved, n) if n[k]]
    return ("거뒀다: " + (f"「끝났음」 표시 {len(add)}건을 {latest} 의 「{DONE_SECTION}」에 더했다" if add or dup or not (open_ids or sum(n.values()))
                        else f"보고 글 {latest}")
            + (f" · 그 절에 이미 든 {dup}건은 더하지 않았다" if dup else "")
            + (f" · 푸신 {len(open_ids)}건은 「{REOPEN_SECTION}」으로 옮겼다" if open_ids else "")
            + (f" · {' · '.join(moved)}은 보고 맞춤 파일 {prefs_path} 에 옮겼다" if moved else "")
            + " — 다음 업무 파악이 두 절로 그 일을 닫거나 다시 열고, 보고가 맞춤 파일을 따른다")


# ── 거두기의 걸음 ───────────────────────────────────────────────────────────

def latest_brief(folder: pathlib.Path) -> pathlib.Path:
    """가장 늦은 보고 글 — 없으면 `cli.Stop`(종료 0 — 창이 선 적이 없으니 표시도 없다)."""
    briefs = kept_briefs(folder) if folder.is_dir() else []
    if not briefs:
        raise cli.Stop(NO_BRIEF.format(folder=folder), EXIT_OK)
    return briefs[-1]


def no_edge(port: int, exc: Exception) -> tuple[int, str]:
    """로그인 Edge 에 못 닿은 끝 — 종료 3 과 그 말."""
    return EXIT_NO_EDGE, (f"표시를 못 거뒀다 — 로그인 Edge({C.EDGE_HOST}:{port})에 못 닿았다({exc}). 누르신 표시는 그 Edge 에 남아 다음에 "
                          "거둔다. 다음: 대화에서 끝났다고 하신 일만 보고 글에 더하고 이어 간다")


def window_of(latest: pathlib.Path) -> pathlib.Path:
    """표시를 읽을 창 — 보고 글 곁의 창 파일, 없으면 보고 글(열린 file: 탭이 없을 때 뒤 탭으로 열 자리)."""
    page_file = latest.with_suffix(".html")
    return page_file if page_file.is_file() else latest


def waiting_marks(rows: list) -> tuple[list, list, list]:
    """창의 칸 → (꼴에 맞는 표시, 아직 안 거둔 표시, 아직 안 거둔 「다시 넣기」)."""
    ticks = ticks_of(rows)
    waiting = [(u, v) for u, v in ticks if not v.get("folded")]
    undo = [(k, v) for k, v in E.stored(rows, C.UNQUIET_PREFIX) if not v.get("folded") and k]
    return ticks, waiting, undo


def brief_text(latest: pathlib.Path) -> str:
    """가장 늦은 보고 글의 글 — 못 읽으면 `cli.Stop`."""
    try:
        return latest.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise cli.Stop(BRIEF_UNREAD.format(latest=latest, exc=exc)) from exc


def write_brief(latest: pathlib.Path, text: str, new: str) -> None:
    """고친 보고 글을 바꿔 끼운다 — 안 바뀌었으면 안 쓴다. 못 쓰면 `cli.Stop`."""
    if new == text:
        return
    try:
        S.replace(latest, new.encode("utf-8"))
    except OSError as exc:
        raise cli.Stop(BRIEF_UNWRITTEN.format(latest=latest, exc=exc)) from exc


def write_prefs(folder: pathlib.Path, prefs: P.Prefs, before: tuple) -> None:
    """맞춤 파일을 쓴다 — 세 절이 그대로면 안 쓴다. 못 쓰면 `cli.Stop`."""
    if (prefs.quiet, prefs.later, prefs.back) == before:
        return
    try:
        P.write(folder, prefs)
    except OSError as exc:
        raise cli.Stop(PREFS_UNWRITTEN.format(path=P.path_of(folder), exc=exc)) from exc


def stamp_window(page: E.Tab, waiting: list, undo: list) -> list[str]:
    """거둔 표시에 남긴 때를 창에 적는다 — 다시 옮기지 않게. 못 적으면 경고 한 줄(보고 글에 든 번호는 다음 판이 다시 더하지 않는다)."""
    stamp = T.stamp(T.local_now())
    marks = [[C.DONE_PREFIX + unid, json.dumps({**value, "folded": stamp}, ensure_ascii=False)] for unid, value in waiting]
    marks += [[C.UNQUIET_PREFIX + k, json.dumps({**value, "folded": stamp}, ensure_ascii=False)] for k, value in undo]
    try:
        page.write(marks)
    except E.EdgeGone as exc:
        return [UNSTAMPED.format(exc=exc)]
    return []


def collect(folder: pathlib.Path, prefs: P.Prefs) -> tuple[int, str]:
    """창의 표시를 가장 늦은 보고 글과 맞춤 파일에 옮기고, 옮긴 표시에 남긴 때를 적는다 — (종료 값, 끝 줄). 보고 글과 맞춤 파일을 다 쓴
    뒤에만 창에 적는다 — 그 사이에 멈추면 다음 판이 다시 옮기고, 보고 글에 든 번호는 더하지 않는다."""
    try:
        latest = latest_brief(folder)
        with E.window(window_of(latest)) as page:
            ticks, waiting, undo = waiting_marks(page.read())
            if not waiting and not undo:
                return EXIT_OK, NOTHING_NEW.format(n=len(ticks), latest=latest)
            text = brief_text(latest)
            before = (list(prefs.quiet), list(prefs.later), list(prefs.back))
            done = sort_marks(text, waiting, undo, prefs)
            write_brief(latest, text, done.text)
            write_prefs(folder, prefs, before)
            cli.say(stamp_window(page, waiting, undo))
            return EXIT_OK, collected_words(latest, done, P.path_of(folder))
    except cli.Stop as stop:
        return stop.code, stop.line
    except E.NoEdge as exc:
        return no_edge(E.port(), exc)
    except E.EdgeGone as exc:
        return EXIT_NO_EDGE, EDGE_LOST.format(exc=exc)


def due_back(folder: pathlib.Path, prefs: P.Prefs) -> tuple[list[str], list[str], list[str]]:
    """「내일 다시」 줄 가운데 돌아올 날이 온 것을 「다시 올린 것」으로 옮기고 그 보고가 실었으면 걷는다(`prefs_file.take_due` — 보고 글
    이름의 때로 잰다) — (돌아온 것, 아직 미룬 것, 경고). 바뀌었으면 맞춤 파일에 적는다."""
    before = (list(prefs.later), list(prefs.back))
    briefs = kept_briefs(folder) if folder.is_dir() else []
    back, wait = P.take_due(prefs, T.wall_now(), [made_of(f.name) for f in briefs])
    if folder.is_dir() and (prefs.later, prefs.back) != before:
        try:
            P.write(folder, prefs)
        except OSError as exc:
            return back, wait, [BACK_UNWRITTEN.format(exc=exc)]
    return back, wait, []


def gather(folder: pathlib.Path) -> int:
    """거두기 — 맞춤 읽기 → 창의 표시 옮기기 → 돌아온 것 → 열린 창에 알리기 → 보고가 읽을 무리 → 끝 줄. 종료 값은 표시 옮기기의 것."""
    try:
        prefs = P.read(folder, strict=True)
    except P.Unreadable as exc:            # 빈 것으로 읽고 거두면 맞춤 파일을 덮는다 — 표시는 창에 그대로 두고 다음 판이 거둔다
        cli.say([PREFS_UNREAD.format(path=P.path_of(folder), exc=exc)])
        return EXIT_FAIL
    code, last = collect(folder, prefs)
    back, wait, warned = due_back(folder, prefs)
    cli.say(warned)
    V.sync(folder)                     # 열린 창이 거둔 뒤의 모습을 보이게 — 대화에서 걷은 것도 여기서 따라간다
    cli.say(report_lines(folder, prefs.quiet, back, wait) + [last])
    return code


def parser() -> argparse.ArgumentParser:
    """인자 — 모델의 길(거두기)과 프로그램이 부르는 문(시계 판의 셋 · 창 곁의 손)을 `--help` 의 다른 절에 둔다."""
    ap = argparse.ArgumentParser(description="보고 창에서 누르신 것을 로그인 Edge 에서 거둬 가장 늦은 보고 글과 보고 맞춤 파일에 옮긴다.")
    ap.add_argument("--dir", required=True, action=cli.Once, help="보고 글(brief-….md)이 사는 사용자 폴더(한 번만)")
    doors = ap.add_argument_group(cli.DOORS_TITLE, cli.DOORS_NOTE)
    way = doors.add_mutually_exclusive_group()
    way.add_argument("--times-done", metavar="고르신_때", help="고르신 시각을 받았나를 그 창에 돌려 적는다(시계 판이 부른다)")
    way.add_argument("--away-done", metavar="고르신_때", help="고르신 자리 밖에서 보기를 받았나를 그 창에 돌려 적는다(시계 판이 부른다)")
    doors.add_argument("--said", default="", help="--times-done · --away-done 과 함께 — 그 창에 보일 한 줄")
    doors.add_argument("--refused", action="store_true", help="--times-done · --away-done 과 함께 — 안 받았다")
    way.add_argument("--presses", action="store_true", help="열린 보고 창의 「일정에 넣기」 누름을 거둬 넣는다(시계 판이 부른다)")
    way.add_argument("--watch", action="store_true", help="보고 창 곁에 남아 누름을 바로 거둔다(창을 여는 손이 띄운다)")
    doors.add_argument("--within", type=int, default=0, metavar="초", help="--presses 와 함께 — 이 안에 끝낼 수 있는 넣기만 시작한다")
    return ap


def main(argv: list[str] | None = None) -> int:
    """명령 입구 — 받은 문(누름 넣기 · 창 곁 · 돌려 적기)을 그 손에 나누고, 문이 없으면 거둔다(`gather`)."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    folder = pathlib.Path(args.dir)
    if args.presses or args.watch:
        return presses.watch(folder) if args.watch else presses.round_once(folder, args.within)
    if args.times_done is not None:
        return D.door(folder, args.times_done, args.said, args.refused)
    if args.away_done is not None:
        return D.door(folder, args.away_done, args.said, args.refused, M.AWAY)
    return gather(folder)


if __name__ == "__main__":
    sys.exit(main())
