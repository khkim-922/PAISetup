"""보고 창에서 누르신 것을 로그인 Edge 에서 거둔다 — 일일 보고 스킬의 거두는 손. 「끝났음」 · 푸신 「끝났음」은 가장 늦은 보고 글의
「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에, 「내일 다시」 · 「안 올려도 됨」 · 「다시 올리기」는 보고 맞춤 파일(곁의 `prefs.py`)에
옮기고, 끝에 이 보고가 올리지 않을 것 · 오늘 돌아온 것 · 아직 미룬 것을 댄다.

    python -X utf8 -I ticks.py --dir <사용자 폴더>
    python -X utf8 -I ticks.py --dir <사용자 폴더> --times                                  보고 창에서 고르신 보고 시각 · 자리 밖에서 보기만 읽는다
    python -X utf8 -I ticks.py --dir <사용자 폴더> --times-done <고르신 때> --said <말> [--refused]   시각을 받았나를 그 창에 돌려 적는다
    python -X utf8 -I ticks.py --dir <사용자 폴더> --away-done <고르신 때> --said <말> [--refused]    자리 밖에서 보기를 받았나를 돌려 적는다
    python -X utf8 -I ticks.py --dir <사용자 폴더> --sync                                   열린 보고 창에 지금 모습만 알린다
    python -X utf8 -I ticks.py --dir <사용자 폴더> --presses [--within 초]                  「일정에 넣기」 누름을 거둬 넣는다(스캔 판)
    python -X utf8 -I ticks.py --dir <사용자 폴더> --watch                                  창 곁에 남아 그 누름을 바로 거둔다(창을 여는 손이 띄운다)
    (셋 다 · 그리고 거둔 뒤에도 열린 창에 지금 모습(`state.state_of` — 시각표 · 규칙의 수 · 맞춤 파일의 두 절)을 적는다 — 창은 그보다 앞서
    고른 것을 낡았다고 알고, 대화에서 바꾸신 것을 다음 스캔을 기다리지 않고 보인다. `--sync` 는 그것을 바꾸는 대화의 명령이 부른다)

    --dir — 보고 글(brief-….md)이 사는 사용자 폴더. 한 번만 받는다 · 그 안의 이름이 가장 늦은 보고 글 하나만 고친다
    --times · --times-done · --away-done — 스킬 mailbox-scan 의 스캔 판이 부른다(보고 시각표와 자리 밖에서 보기의 주인은 그 스킬이다). 열린
    file: 탭이 없으면 아무것도 안 연다
    --presses · --watch — 곁의 `presses.py` 가 든다(그 머리말). 열린 보고 창이 없으면 아무것도 안 연다

표시는 창(file://)의 localStorage 에 있다(`assets/report.js`). 로그인 Edge(스킬 ep-login 이 연 디버깅 포트 — `EDGE_DEBUG_PORT`
기본 9222)의 file: 탭 하나에서 읽고, 열린 file: 탭이 없으면 가장 늦은 보고 창을 뒤 탭으로 잠깐 열어 읽고 닫는다. 옮긴 표시에는 남긴 때를
적어 두어 다시 옮기지 않고, 그 절에 이미 든 메일 번호도 더하지 않는다. 부르는 곳은 이 PC 의 디버깅 포트뿐이다 — 메일함에 닿지 않는다.

내는 것 — 표준 출력의 끝 줄이 더한 수 · 이미 든 수 · 고친 보고 글을 말하고, 거둘 수 없었으면 「다음: …」이 뒤에 선다. 그 앞 줄들이
맞춤 파일의 올리지 않을 것 · 돌아온 것 · 미룬 것과 지난 보고 뒤 창에서 누르신 「일정에 넣기」 · 맡기신 일의 끝이다(Edge 에 못 닿아도 댄다).
`--times` 의 끝 줄 — 고르신 것이 있으면 「고르신 보고 시각: HH:MM … · 보던 시각: HH:MM …(없으면 -) · 고르신 때 <때>」(`TIMES_LINE` · 스캔이
이 꼴로 읽는다 — 보던 시각에서 무엇을 더하고 빼셨나로 걸린 시각표를 고친다). 「자리 밖에서 보기」를 고르셨으면 그 앞에 「고르신 자리 밖에서
보기: true|false · 고르신 때 <때>」(`AWAY_LINE` — 켬 · 끔은 JSON 의 참 · 거짓 글자)가 선다.
종료 값 — 0 거뒀다(거둘 표시가 없었던 것도) · 1 보고 글이나 맞춤 파일을 못 고쳤다 · 2 인자가 틀렸다 · 3 로그인 Edge 에 못 닿았다(표시는 그
Edge 에 남는다). 무엇을 지키고 왜 그런가는 `references/DESIGN.md` 「누르신 표시」 · 「보고 맞춤」이 든다.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
import brief_const as C  # noqa: E402
import brief_text as B  # noqa: E402
import cli  # noqa: E402
import edge as E  # noqa: E402
import prefs_file as P  # noqa: E402
import presses  # noqa: E402
import runs as R  # noqa: E402
import state as V  # noqa: E402
import store as S  # noqa: E402
from brief_const import EXIT_FAIL, EXIT_NO_EDGE, EXIT_OK  # noqa: E402

LINE = "- {title} — {when}보고 창에서 끝났다고 표시하셨습니다 [근거 메일](mail:{unid})"
REOPEN_LINE = "- {title} — {when}보고 창에서 끝나지 않았다고 표시하셨습니다 [근거 메일](mail:{unid})"

TIMES_LINE = "고르신 보고 시각: {times} · 보던 시각: {base} · 고르신 때 {at}"   # 스캔 판이 이 꼴로 읽는다(그 스킬 `window_link.py` 의 WINDOW_TIMES)
AWAY_LINE = "고르신 자리 밖에서 보기: {on} · 고르신 때 {at}"                    # 같은 판이 이 꼴로 읽는다(그 스킬 `window_link.py` 의 WINDOW_AWAY)
MARKS = ("done", "open", "later", "quiet", "clear")    # 표시의 값 — `assets/report.js` 가 적는 것. 옛 표시는 done(참 · 거짓)만 든다

# ── 표시 → 보고 글의 줄 ──────────────────────────────────────────────────────

def mark_of(value: dict) -> str:
    """표시가 무엇을 누르신 것인가 — `mark`, 옛 표시는 done 이 거짓이면 open · 그 밖은 done. 꼴이 아니면 ""."""
    mark = value.get("mark")
    if mark is None:
        return "open" if value.get("done") is False else "done"
    return mark if mark in MARKS else ""


def ticks_of(rows: list) -> list[tuple[str, dict]]:
    """창에서 읽은 (열쇠, 값) 가운데 꼴에 맞는 누름 표시만 — (메일 번호, 값). 열쇠의 메일 번호가 32자리가 아니거나 값이 꼴이 아니면 버린다."""
    return [(unid.upper(), v) for unid, v in E.stored(rows, C.DONE_PREFIX) if B.UNID.match(unid) and mark_of(v)]


def title_of(value: dict) -> str:
    """보고 글 한 줄에 설 일 이름 — 줄바꿈 · 꼴 표시를 걷고 길이를 줄인다. 창의 칸에서 온 글이라 절 머리 · 링크로 서지 못하게 한다."""
    return P.clean(str(value.get("title") or "")) or "이름 없는 일"


def when_of(value: dict) -> str:
    """누르신 때 — 이 PC 의 시각으로 「M/D HH:MM」. 꼴이 아니면 빈 글."""
    at = E.pressed_at(value)
    return f"{at.month}/{at.day} {at:%H:%M}" if at else ""


# ── 들고 나기 ─────────────────────────────────────────────────────────────

def n_moved(n: dict) -> int:
    return sum(n.values())


def summary(quiet: list[str], back: list[str], wait: list[str]) -> list[str]:
    """보고를 짓는 쪽이 읽을 맞춤 — 올리지 않을 것 · 돌아온 것 · 미룬 것(없는 무리는 안 선다)."""
    out: list[str] = []
    if quiet:
        out += ["올리지 않을 것 — 사용자가 정하셨다. 같은 갈래의 일은 이 보고에 올리지 않고 「이 보고가 본 데」에 그 수만 적는다:", *quiet]
    if back:
        out += ["돌아온 것 — 「내일 다시」 하신 일이 돌아오는 날이 와 돌아왔다. 아직 열려 있으면 이 보고에 다시 올린다:", *back]
    if wait:
        out += ["미룬 것 — 「내일 다시」 하신 일이다. 돌아오는 날 전에는 이 보고에 올리지 않는다:", *wait]
    return out


def collect(folder: pathlib.Path, prefs: P.Prefs) -> tuple[int, str]:
    """창의 표시를 가장 늦은 보고 글과 맞춤 파일에 옮기고, 옮긴 표시에 남긴 때를 적는다 — (종료 값, 끝 줄). 보고 글과 맞춤 파일을 다 쓴
    뒤에만 창에 적는다 — 그 사이에 멈추면 다음 판이 다시 옮기고, 보고 글에 든 번호는 더하지 않는다."""
    briefs = B.kept_briefs(folder) if folder.is_dir() else []
    if not briefs:
        return EXIT_OK, f"거둘 자리가 없다 — {folder} 에 보고 글(brief-….md)이 없다. 창이 선 적이 없으니 표시도 없다"
    latest = briefs[-1]
    page_file = latest.with_suffix(".html")
    port = E.port()
    try:
        cdp = E.Cdp(port)
    except E.EdgeGone as exc:
        return EXIT_NO_EDGE, (f"표시를 못 거뒀다 — 로그인 Edge({C.EDGE_HOST}:{port})에 못 닿았다({exc}). 누르신 표시는 그 Edge 에 남아 다음에 "
                              "거둔다. 다음: 대화에서 끝났다고 하신 일만 보고 글에 더하고 이어 간다")
    page = None
    try:
        page = E.page(cdp, page_file if page_file.is_file() else latest)
        rows = page.read()
        ticks = ticks_of(rows)
        waiting = [(u, v) for u, v in ticks if not v.get("folded")]
        undo = [(k, v) for k, v in E.stored(rows, C.UNQUIET_PREFIX) if not v.get("folded") and k]
        if not waiting and not undo:
            return EXIT_OK, f"거둘 표시가 없다 — 창에서 새로 누르신 것이 없다(남긴 표시 {len(ticks)}건) · 보고 글 {latest}"
        try:
            text = latest.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return EXIT_FAIL, f"표시를 못 남겼다 — 보고 글을 못 읽었다({latest}: {exc}). 표시는 창에 그대로 있다. 다음: 그 파일을 확인하고 다시 부른다"
        # 끝났다는 표시는 「끝났다고 하신 것」에, 푸신 표시는 「안 끝났다고 하신 것」에 — 맞은편 절의 같은 번호 줄은 걷는다. 미루거나 올리지
        # 말라신 일은 맞춤 파일로 가고 「끝났다고 하신 것」에서 걷힌다(뒤에 누르신 것이 이긴다)
        _, have = B.fold(text, B.DONE_SECTION, [])
        _, back = B.fold(text, B.REOPEN_SECTION, [])
        add, reopen, dup = [], [], 0               # 표시는 메일 번호마다 하나다(창의 저장소 열쇠)
        done_ids, open_ids, aside = set(), set(), set()
        n = {"later": 0, "quiet": 0, "clear": 0, "unquiet": 0}
        before = (list(prefs.quiet), list(prefs.later), list(prefs.back))
        for unid, value in waiting:
            mark = mark_of(value)
            when = when_of(value)
            words = dict(title=title_of(value), when=f"{when} " if when else "", unid=unid)
            at = E.pressed_at(value) or dt.datetime.now().astimezone()
            if mark == "open":
                open_ids.add(unid)
                if unid not in back:
                    reopen.append(REOPEN_LINE.format(**words))
            elif mark == "done":
                done_ids.add(unid)
                P.drop_unid(prefs, unid)
                if unid in have:
                    dup += 1
                else:
                    add.append(LINE.format(**words))
            elif mark == "later":
                aside.add(unid)
                n["later"] += 1
                P.put_later(prefs, P.LATER_LINE.format(title=words["title"], due=(at.date() + dt.timedelta(days=1)).isoformat(),
                                                       when=P.when_words(at), where="보고 창에서", unid=unid))
            elif mark == "quiet":
                aside.add(unid)
                n["quiet"] += 1
                P.put_quiet(prefs, P.QUIET_FROM_WINDOW.format(title=words["title"], when=P.when_words(at), unid=unid))
            else:
                n["clear"] += 1
                P.drop_unid(prefs, unid)
        for k, _ in undo:
            n["unquiet"] += P.forget(prefs, k) is not None
        new, _ = B.fold(text, B.DONE_SECTION, add, open_ids | aside)
        new, _ = B.fold(new, B.REOPEN_SECTION, reopen, done_ids)
        if new != text:
            try:
                S.replace(latest, new.encode("utf-8"))
            except OSError as exc:
                return EXIT_FAIL, f"표시를 못 남겼다 — 보고 글을 못 썼다({latest}: {exc}). 표시는 창에 그대로 있다. 다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다"
        if (prefs.quiet, prefs.later, prefs.back) != before:
            try:
                P.write(folder, prefs)
            except OSError as exc:
                return EXIT_FAIL, (f"표시를 못 남겼다 — 보고 맞춤 파일을 못 썼다({P.path_of(folder)}: {exc}). 표시는 창에 그대로 있다. 다음: 그 폴더에 "
                                   "쓸 수 있는지 보고 다시 부른다")
        stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        marks = [[C.DONE_PREFIX + unid, json.dumps({**value, "folded": stamp}, ensure_ascii=False)] for unid, value in waiting]
        marks += [[C.UNQUIET_PREFIX + k, json.dumps({**value, "folded": stamp}, ensure_ascii=False)] for k, value in undo]
        try:
            page.write(marks)
        except E.EdgeGone as exc:
            print(f"경고: 보고 글 · 맞춤 파일에는 남겼지만 창에 「남겼다」를 못 적었다({exc}) — 다음 판이 보고 글에 든 번호를 보고 다시 더하지 않는다")
        moved = [f"「내일 다시」 {n['later']}건", f"「안 올려도 됨」 {n['quiet']}건", f"되돌리신 {n['clear']}건", f"「다시 올리기」 {n['unquiet']}건"]
        moved = [m for m, k in zip(moved, n) if n[k]]
        return EXIT_OK, ("거뒀다: " + (f"「끝났음」 표시 {len(add)}건을 {latest} 의 「{B.DONE_SECTION}」에 더했다" if add or dup or not (open_ids or n_moved(n))
                                       else f"보고 글 {latest}")
                         + (f" · 그 절에 이미 든 {dup}건은 더하지 않았다" if dup else "")
                         + (f" · 푸신 {len(open_ids)}건은 「{B.REOPEN_SECTION}」으로 옮겼다" if open_ids else "")
                         + (f" · {' · '.join(moved)}은 보고 맞춤 파일 {P.path_of(folder)} 에 옮겼다" if moved else "")
                         + " — 다음 업무 파악이 두 절로 그 일을 닫거나 다시 열고, 보고가 맞춤 파일을 따른다")
    except E.EdgeGone as exc:
        return EXIT_NO_EDGE, (f"표시를 못 거뒀다 — 로그인 Edge 와 주고받다 멈췄다({exc}). 누르신 표시는 그 Edge 에 남아 다음에 거둔다. "
                              "다음: 대화에서 끝났다고 하신 일만 보고 글에 더하고 이어 간다")
    finally:
        if page is not None:
            page.close()
        cdp.close()


def away_pick(row: dict | None) -> str:
    """창이 남긴 「자리 밖에서 보기」 고름 — 거둘 때면(창 곁의 손과 같은 자 `presses.AWAY`) 스캔이 읽을 줄(`AWAY_LINE`), 아니면 ""."""
    got = presses.AWAY.due(row, True)
    return AWAY_LINE.format(on=json.dumps(got[0]), at=got[1]) if got else ""


def times(folder: pathlib.Path, done_at: str | None, said: str, refused: bool, kind: presses.Kind = presses.TIMES) -> int:
    """보고 창에서 고르신 보고 시각과 「자리 밖에서 보기」를 읽거나(`done_at` 이 None), 받았나를 그 창의 그 누름 종류(`kind` — 시각 · 자리 밖에서
    보기)의 칸에 돌려 적는다 — 창 곁의 손과 같은 자(`kind.due`)로 재고 같은 칸(`kind.back`)을 적는다. 두 길 다 그 창에 지금 모습을 함께
    적는다. 열린 보고 창이 없으면 아무것도 안 연다."""
    port = E.port()
    try:
        cdp = E.Cdp(port)
    except E.EdgeGone as exc:
        print(f"보고 창의 시각을 못 읽었다 — 로그인 Edge({C.EDGE_HOST}:{port})에 못 닿았다({exc})")
        return EXIT_NO_EDGE
    page = None
    try:
        try:
            page = E.page(cdp, None)
        except E.NoWindow:
            print("고르신 보고 시각 없음 — 열린 보고 창이 없다")
            return EXIT_OK
        rows = page.read()
        got = dict(E.stored(rows, kind.key)).get("")
        page.write([V.row(folder)])
        if done_at is not None:
            if not got or got.get("at") != done_at:
                print("안 적었다 — 그 뒤에 새로 고르셨거나 고르신 것이 없다")
                return EXIT_OK
            page.write([[kind.key, json.dumps(kind.back(got, said, refused), ensure_ascii=False)]])
            print("적었다 — 보고 창에 받았나를 돌려 적었다")
            return EXIT_OK
        away = away_pick(dict(E.stored(rows, C.AWAY_KEY)).get(""))
        if away:
            print(away)
        picked = kind.due(got, True)
        if picked is None:
            print("고르신 보고 시각 없음")
            return EXIT_OK
        chosen, base, at = picked
        print(TIMES_LINE.format(times=" ".join(chosen), base=" ".join(base) or "-", at=at))
        return EXIT_OK
    except E.EdgeGone as exc:
        print(f"보고 창의 시각을 못 읽었다 — 로그인 Edge 와 주고받다 멈췄다({exc})")
        return EXIT_NO_EDGE
    finally:
        if page is not None:
            page.close()
        cdp.close()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="보고 창에서 누르신 것을 로그인 Edge 에서 거둬 가장 늦은 보고 글과 보고 맞춤 파일에 옮긴다.")
    ap.add_argument("--dir", required=True, action=cli.Once, help="보고 글(brief-….md)이 사는 사용자 폴더(한 번만)")
    way = ap.add_mutually_exclusive_group()
    way.add_argument("--times", action="store_true", help="보고 창에서 고르신 보고 시각만 읽는다(스캔 판이 부른다)")
    way.add_argument("--times-done", metavar="고르신_때", help="고르신 시각을 받았나를 그 창에 돌려 적는다(스캔 판이 부른다)")
    way.add_argument("--away-done", metavar="고르신_때", help="고르신 자리 밖에서 보기를 받았나를 그 창에 돌려 적는다(스캔 판이 부른다)")
    ap.add_argument("--said", default="", help="--times-done · --away-done 과 함께 — 그 창에 보일 한 줄")
    ap.add_argument("--refused", action="store_true", help="--times-done · --away-done 과 함께 — 안 받았다")
    way.add_argument("--sync", action="store_true", help="열린 보고 창에 지금 모습만 알린다(그것을 바꾸는 대화의 명령이 부른다)")
    way.add_argument("--presses", action="store_true", help="열린 보고 창의 「일정에 넣기」 누름을 거둬 넣는다(스캔 판이 부른다)")
    way.add_argument("--watch", action="store_true", help="보고 창 곁에 남아 누름을 바로 거둔다(창을 여는 손이 띄운다)")
    ap.add_argument("--within", type=int, default=0, metavar="초", help="--presses 와 함께 — 이 안에 끝낼 수 있는 넣기만 시작한다")
    args = ap.parse_args(argv)

    folder = pathlib.Path(args.dir)
    if args.presses or args.watch:
        return presses.watch(folder) if args.watch else presses.round_once(folder, args.within)
    if args.times or args.times_done is not None:
        return times(folder, args.times_done, args.said, args.refused)
    if args.away_done is not None:
        return times(folder, args.away_done, args.said, args.refused, presses.AWAY)
    if args.sync:
        print(V.sync(folder) or "알리지 않았다 — 열린 보고 창이 없거나 로그인 Edge 에 못 닿았다")
        return EXIT_OK
    try:
        prefs = P.read(folder, strict=True)
    except P.Unreadable as exc:            # 빈 것으로 읽고 거두면 맞춤 파일을 덮는다 — 표시는 창에 그대로 두고 다음 판이 거둔다
        print(f"표시를 못 거뒀다 — 보고 맞춤 파일을 못 읽었다({P.path_of(folder)}: {exc}). 표시는 창에 그대로 있다. 다음: 그 파일을 확인하고 다시 부른다")
        return EXIT_FAIL
    code, last = collect(folder, prefs)
    before = (list(prefs.later), list(prefs.back))
    briefs = B.kept_briefs(folder) if folder.is_dir() else []
    back, wait = P.take_due(prefs, dt.datetime.now(), [B.made_of(f.name) for f in briefs])
    if folder.is_dir() and (prefs.later, prefs.back) != before:
        try:
            P.write(folder, prefs)
        except OSError as exc:
            print(f"경고: 돌아온 것을 보고 맞춤 파일에 못 적었다({exc}) — 다음 보고도 돌아온 것으로 다시 댄다")
    V.sync(folder)                     # 열린 창이 거둔 뒤의 모습을 보이게 — 대화에서 걷은 것도 여기서 따라간다
    for line in summary(prefs.quiet, back, wait):
        print(line)
    for line in presses.recent_lines(folder) + R.recent_lines(folder):
        print(line)
    print(last)
    return code


if __name__ == "__main__":
    sys.exit(main())
