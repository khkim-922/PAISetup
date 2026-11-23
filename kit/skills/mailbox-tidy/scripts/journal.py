"""메일함에서 바꾼 것을 적어 두고, 되돌릴 차례를 낸다 — 회사 메일 스킬의 미리 보기와 실행이 낸 글을 받는다. 메일함에는 닿지 않는다.

    <미리 보기> | python -X utf8 journal.py show <종류> --piece <n> [--why <무리 · 까닭>] [--to <폴더>]   안의 조각 n 으로 적고 보인다
    python -X utf8 journal.py shown                     적어 둔 안 — show 가 보인 줄을 조각마다 그대로(읽기만)
    python -X utf8 journal.py plans [--most N]          적어 둔 안들 — 아직 안 바꾼 조각의 받을 자리 · 메일 번호 · 까닭(읽기만 · 새것부터)
    <미리 보기> | python -X utf8 journal.py hold <종류> [--shown <n>] [--undoes <기록 번호>]   잡아 두고 실행 줄을 낸다
    <실행>      | python -X utf8 journal.py done
    python -X utf8 journal.py drop                      사람이 안 하기로 하신 미리 보기를 놓는다 — 실행하지 않았을 때만
    python -X utf8 journal.py log [--most N]            바꾼 것의 기록 — 새것부터
    python -X utf8 journal.py mails [<기록 번호> …]     바꾼 메일 — 기록마다 메일 번호 · 원래 자리 → 간 자리(읽기만 · 옛것부터)
    python -X utf8 journal.py undo <기록 번호>          그 바꿈을 되돌리는 차례 — 차례마다 칠 명령 줄
    (`show` · `hold` · `done` 은 `--in <파일>` 로도 받는다)

종류 — move(메일 옮기기) · trash(휴지통으로) · restore(휴지통에서 되살리기) · folder-create · folder-delete · rule-add · rule-edit ·
rule-delete. 메일 번호 · 받을 자리 · 확인 열쇠는 미리 보기에서 읽는다 — 메일 줄 끝의 번호 · 머리의 받을 자리 · 「확인 열쇠:」 줄. 따로
주지 않는다. `--to` 는 옮길 폴더를 같은 안의 앞 조각이 만들어 휴지통 미리 보기를 옮기기 조각으로 적을 때(`show move`)만 준다. 옛 꼴대로
메일 번호 · `--to` · `--inbox` 를 주면 미리 보기와 같은지만 대고, 다르면 잡지 않는다.

명령마다 무엇을 대나는 `references/DESIGN.md` 「명령마다 하는 일」이 든다.

남기는 것 — 사용자 폴더(`journal_store.home`)의 기록(덧붙이기만) · 잡아 둔 바꿈 · 보여 드린 안의 조각 · 적어 둔 안들(덧붙이기만) — 파일
이름은 `journal_const.py` 의 `LOG_FILE` · `HELD_FILE` · `SHOWN_FILE` · `PLANS_FILE`. 기록 · 잡아 둔 바꿈 · 적어 둔 안들은 메일 번호 · 자리 · 폴더 경로 · 규칙의 판(안들은 조각의 까닭 한 줄도)만
적고 제목 · 보낸 분 · 본문은 안 적는다. 안의 조각은 손의 메일 줄(제목 · 보낸 분)도 든다 — 안을 지은 쪽과 사용자께 보이는 쪽이 달라도 같은
줄이 서게. 다음 안의 1번 조각이 덮는다 — 덮인 안의 메일 번호는 적어 둔 안들에 남는다.

종료 값 — 0 됐다 · 1 못 했다(꼴이 다르다 · 보여 드린 조각과 다르다 · 실행의 글이 잡아 둔 바꿈과 다르다 · 잡아 둔 것이 없다 · 그런
기록이 없다 — 다음 걸음을 끝 줄이 말한다) · 2 인자가 틀렸다.

⚠ 실행의 「됐다」 줄은 끝의 확인 열쇠로 잡아 둔 미리 보기에 잇는다. 열쇠는 미리 보기가 본 판의 지문이라, 같은 판에서 다시 한 같은
바꿈(지운 폴더를 다시 만들기 · 되돌린 메일을 다시 옮기기)의 실행 글은 앞의 것과 열쇠가 같아 가르지 못한다. 열쇠가 없는 「됐다」 줄
(갱신 전의 손)은 메일 수 · 받을 자리 · 폴더 경로로 대고, 규칙은 안 댄다.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections.abc import Sequence
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 모듈 — `-I` 로 돌아도 싣는다

from hand_line import held_apply_line  # noqa: E402
from hand_text import UNID, read_applied, read_preview, read_shown  # noqa: E402
from journal_const import (CMD_DONE, CMD_DROP, CMD_HOLD, CMD_LOG, CMD_MAILS, CMD_PLANS, CMD_SHOW, CMD_SHOWN, CMD_UNDO, EXIT_FAILED, EXIT_OK,  # noqa: E402
                           FIRST_PIECE, KINDS, LOG_MOST, MAIL_KINDS, PLANS_MOST, PRIOR_TWIN, PRIOR_UNKNOWN, UNDOES_FLAG, UNKNOWN,
                           WHY_IS_FOR_MAILS, WHY_IS_UNID, Mismatch, Refused)
from journal_io import echo_input, now, read_input, say, utf8_out  # noqa: E402
from journal_store import (append_plan_row, close_held, entries, held, hold_change, home, log_path, next_id, pieces_of, plan_rows,  # noqa: E402
                           release_held, shown_pieces, shown_plan, undone_entry, with_held, write_shown)
from journal_view import (check_piece_order, is_first_piece, shown_piece, chain_of, closed_entry, counted, differences, ending, find_entry, kept_pieces, log_slice, mail_count,  # noqa: E402
                          mail_view, new_plan_number, opens_plan, pick_entries, plan_row, plans_left, prior_hold, shown_rows, shown_span, stamped,
                          undo_plan, undo_tries, undone_rule_unid, with_piece)
from journal_words import (HELD_SAME, NO_HELD, NO_HELD_DROP, SHOWN_EMPTY, STALE_DONE, UNDO_FOOT,  # noqa: E402
                           UNDO_HEAD, bad_lines, chain_word, difference_lines, dropped, held_lines, mail_lines, mails_head, mismatch,
                           no_entry, none_logged, not_held, not_shown, piece_from, plans_lines, row_line, shown_lines, shown_list_lines, shown_none,
                           superseded, undo_notes, undo_step_line, wrote_line)


# ── 명령 손 — 손가락을 차례로 엮기만 한다 ─────────────────────────────────────────

def cmd_show(args: Any, folder: pathlib.Path) -> int:
    """안 적기 — 미리 보기를 지금 안의 조각 n 으로 안들 · 보인 안에 적고 보일 줄을 낸다. 꼴이 다르면 받은 글을 그대로 다시 내고 1."""
    text = read_input(args.infile)
    shown = shown_plan(folder)
    pieces, plan = pieces_of(shown), shown.get("plan")
    first = is_first_piece(args.piece)
    try:
        unids, to = given(args)
        piece, body = read_shown(args.kind, text, unids, to)
        check_piece_order(args.piece, first, pieces, plan)
    except Refused as exc:
        # 적지 못한 조각은 손의 글을 그대로 보인다 — 파이프가 받아 갔다
        echo_input(text)
        say(not_shown(exc))
        return EXIT_FAILED
    if opens_plan(first, plan):
        plan = new_plan_number(plan_rows(folder))
    pieces, dropped_count = kept_pieces(first, pieces)
    at = now()
    append_plan_row(folder, plan_row(plan, args.piece, piece, at, next_id(entries(folder)[0]), args.why))
    write_shown(folder, plan, with_piece(pieces, args.piece, piece, body, at))
    say(shown_lines(args.piece, piece, counted(piece), body, plan, dropped_count))
    return EXIT_OK


def cmd_shown(args: Any, folder: pathlib.Path) -> int:
    """보인 안 — 적어 둔 안을 조각마다 그대로 다시 낸다. 안이 없으면 1."""
    pieces = shown_pieces(folder)
    if not pieces:
        say([SHOWN_EMPTY])
        return EXIT_FAILED
    say(shown_list_lines(shown_rows(pieces), *shown_span(pieces)))
    return EXIT_OK


def cmd_plans(args: Any, folder: pathlib.Path) -> int:
    """남은 안 — 안마다 아직 안 바꾼 조각과 그 미리 보기 명령을 낸다."""
    rows, _ = entries(folder)
    say(plans_lines(plans_left(plan_rows(folder), rows, args.most)))
    return EXIT_OK


def cmd_hold(args: Any, folder: pathlib.Path) -> int:
    """잡기 — 실행 직전 미리 보기를 (보인 조각에 대어) 잡아 두고 실행 줄을 낸다. 앞의 잡아 둔 바꿈은 같은 것이면 바꾸고 아니면 「결과 모름」으로
    옮긴다. 꼴이 다르거나 보인 조각과 다르면 1."""
    text = read_input(args.infile)
    # 미리 보기는 파이프가 받아 갔다 — 사람에게 보일 글을 여기서 다시 낸다
    echo_input(text)
    try:
        unids, to = given(args)
        hold = read_preview(args.kind, text, unids, to)
    except Refused as exc:
        say(not_held(exc))
        return EXIT_FAILED
    if args.shown is not None:
        shown = shown_piece(shown_pieces(folder), args.shown)
        if shown is None:
            say(shown_none(args.shown))
            return EXIT_FAILED
        diff = differences(shown, hold)
        if diff:
            say(difference_lines(args.shown, diff))
            return EXIT_FAILED
    old = held(folder)
    prior = prior_hold(old, hold)
    if prior == PRIOR_TWIN:
        release_held(folder)
        say([HELD_SAME])
    elif prior == PRIOR_UNKNOWN:
        say(superseded(close_held(folder, closed_entry(old, UNKNOWN, {}, now()))))
    hold = stamped(hold, args.undoes, now())
    hold_change(folder, hold)
    apply_cmd = held_apply_line(hold, undone_rule_unid(undone_entry(folder, args.undoes)))
    say(held_lines(args.kind, mail_count(hold), args.shown, apply_cmd, hold["key"]))
    return EXIT_OK


def cmd_done(args: Any, folder: pathlib.Path) -> int:
    """맺기 — 실행의 글을 잡아 둔 바꿈에 대어 맞으면 기록 한 줄로 맺고 놓는다. 잡은 것이 없거나 · 다르거나 · 안 바뀌었으면 1."""
    hold = held(folder)
    text = read_input(args.infile)
    # 실행의 글도 파이프가 받아 갔다 — 사람에게 알릴 결과를 여기서 다시 낸다
    echo_input(text)
    if hold is None:
        say([NO_HELD])
        return EXIT_FAILED
    try:
        outcome, more = read_applied(hold, text)
    except Mismatch as exc:
        say(mismatch(exc))
        return EXIT_FAILED
    if outcome is None:
        release_held(folder)
        say([STALE_DONE])
        return EXIT_FAILED
    entry = closed_entry(hold, outcome, more, now())
    entry_id = close_held(folder, entry)
    say([wrote_line(entry_id, entry, counted(entry), outcome)])
    return EXIT_OK


def cmd_drop(args: Any, folder: pathlib.Path) -> int:
    """놓기 — 잡아 둔 바꿈을 기록 없이 놓는다. 잡은 것이 없으면 1."""
    hold = held(folder)
    if hold is None:
        say([NO_HELD_DROP])
        return EXIT_FAILED
    release_held(folder)
    say(dropped(hold, counted(hold)))
    return EXIT_OK


def cmd_log(args: Any, folder: pathlib.Path) -> int:
    """기록 — 바꾼 것의 기록을 새것부터(잡아 둔 채인 바꿈과 되돌림의 사슬도) 낸다."""
    rows, bad = entries(folder)
    rows = with_held(folder, rows)
    say(bad_lines(bad))
    say(none_logged(rows))
    say(row_line(e, ending(e), counted(e), chain_word(*chain_of(rows, e["id"]))) for e in log_slice(rows, args.most))
    return EXIT_OK


def cmd_mails(args: Any, folder: pathlib.Path) -> int:
    """바꾼 메일 — 기록마다 메일 번호 · 원래 자리 → 간 자리를 낸다. 없는 기록 번호가 있으면 1."""
    rows, bad = entries(folder)
    rows = with_held(folder, rows)
    picked, missing = pick_entries(rows, args.ids)
    lines = [mails_head(log_path(folder)), *bad_lines(bad), *none_logged(rows)]
    for e in picked:
        lines += [row_line(e, ending(e), counted(e), chain_word(*chain_of(rows, e["id"]))), *mail_lines(e, *mail_view(rows, e))]
    say([*lines, *(no_entry(i) for i in missing)])
    return EXIT_FAILED if missing else EXIT_OK


def cmd_undo(args: Any, folder: pathlib.Path) -> int:
    """되돌리는 차례 — 기록 하나의 되돌림 형편과 차례마다 칠 명령 줄을 낸다. 그런 기록이 없으면 1."""
    rows, _ = entries(folder)
    rows = with_held(folder, rows)
    e = find_entry(rows, args.id)
    if e is None:
        say([no_entry(args.id)])
        return EXIT_FAILED
    say([row_line(e, ending(e), counted(e)), *undo_notes(e, ending(e), *undo_tries(rows, e)), UNDO_HEAD, *(undo_step_line(s, v) for s, v in undo_plan(e)), UNDO_FOOT])
    return EXIT_OK


# ── 인자 꼴 · 입구 ────────────────────────────────────────────────────────────

def piece_number(text: str) -> int:
    """`--piece` · `--shown` 의 값 — 1 부터의 정수가 아니면 argparse 가 2 로 나간다."""
    n = int(text)
    if n < FIRST_PIECE:
        raise argparse.ArgumentTypeError(piece_from(text))
    return n


def given(args: Any) -> tuple[list[str], str | None]:
    """`show` · `hold` 가 옛 꼴로 받은 인자 — (메일 번호, 받을 자리 — 받은편지함이면 "" · 안 줬으면 None). 번호의 꼴이 아니거나 메일을 안
    건드리는 종류에 줬으면 `Refused`."""
    unids = [u.strip().upper() for u in args.unids]
    bad = [u for u in unids if not UNID.match(u)]
    if bad:
        raise Refused(WHY_IS_UNID, bad=bad)
    if args.kind not in MAIL_KINDS and (unids or args.to is not None or args.inbox):
        raise Refused(WHY_IS_FOR_MAILS)
    return unids, "" if args.inbox else args.to


def parser() -> argparse.ArgumentParser:
    """명령의 인자 꼴 — 하위 아홉과 그 인자."""
    ap = argparse.ArgumentParser(description="메일함에서 바꾼 것을 적어 두고 되돌릴 차례를 낸다 — 회사 메일 스킬의 글을 받는다")
    sub = ap.add_subparsers(dest="command", required=True)
    s = sub.add_parser(CMD_SHOW, help="안 전체를 확인받기 전에 조각 하나의 미리 보기를 조각 n 으로 적고 보일 꼴로 낸다")
    h = sub.add_parser(CMD_HOLD, help="미리 보기를 읽어 바꿈 하나를 잡아 둔다")
    for q in (s, h):
        q.add_argument("kind", choices=KINDS)
        target = q.add_mutually_exclusive_group()
        target.add_argument("--to", help="show move 가 휴지통 미리 보기를 받을 때만 — 옮길 폴더 경로. 옮기기 미리 보기는 머리의 받을 자리를 읽는다")
        # 옛 꼴의 부름(메일 번호 · --inbox)은 받되 도움말에 안 보인다 — 미리 보기에서 읽는 값을 다시 치라는 말로 읽히지 않게
        target.add_argument("--inbox", action="store_true", help=argparse.SUPPRESS)
        q.add_argument("--in", dest="infile", help="표준 입력 대신 읽을 파일")
        q.add_argument("unids", nargs="*", help=argparse.SUPPRESS)
    s.add_argument("--piece", type=piece_number, required=True, help=f"안에서 이 조각의 번호 — {FIRST_PIECE} 이면 새 안을 연다")
    s.add_argument("--why", help="이 조각의 무리 이름과 까닭 한 줄 — plans 가 다음 판에 같이 낸다. 메일 제목 · 보낸 분은 안 적는다")
    h.add_argument("--shown", type=piece_number, help="확인받은 안의 이 조각과 같을 때만 잡는다")
    h.add_argument(UNDOES_FLAG, type=int, help="이 바꿈이 되돌리는 기록 번호")
    d = sub.add_parser(CMD_DONE, help="실행의 글을 읽어 잡아 둔 바꿈을 기록으로 맺는다")
    d.add_argument("--in", dest="infile", help="표준 입력 대신 읽을 파일")
    sub.add_parser(CMD_DROP, help="사람이 안 하기로 하신 미리 보기를 기록 없이 놓는다 — 실행하지 않았을 때만(실행했으면 done)")
    sub.add_parser(CMD_SHOWN, help="적어 둔 안 — show 가 조각마다 보인 줄을 그대로 다시 낸다(읽기만)")
    pl = sub.add_parser(CMD_PLANS, help="적어 둔 안들 — 아직 안 바꾼 조각의 받을 자리 · 메일 번호 · 까닭(읽기만 · 새것부터). 미리 보기의 입력일 뿐이다")
    pl.add_argument("--most", type=int, default=PLANS_MOST, help="보일 안의 수 — 안 바꾼 조각이 남은 안만 센다(0 이면 다)")
    lg = sub.add_parser(CMD_LOG, help="바꾼 것의 기록 — 새것부터 · 잡아 둔 채인 바꿈과 되돌림의 사슬도")
    lg.add_argument("--most", type=int, default=LOG_MOST, help="보일 기록의 수(0 이면 다)")
    ml = sub.add_parser(CMD_MAILS, help="바꾼 메일 — 기록마다 메일 번호 · 원래 자리 → 간 자리 · 뒤에 다시 바꾼 기록(읽기만 · 옛것부터)")
    ml.add_argument("ids", nargs="*", type=int, help="볼 기록 번호 — 없으면 다")
    u = sub.add_parser(CMD_UNDO, help="기록 하나를 되돌리는 차례")
    u.add_argument("id", type=int)
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    """명령 입구 — 사용자 폴더를 대고 하위 명령을 그 손에 넘긴다."""
    utf8_out()
    args = parser().parse_args(argv)
    folder = home()
    return {CMD_SHOW: cmd_show, CMD_SHOWN: cmd_shown, CMD_PLANS: cmd_plans, CMD_HOLD: cmd_hold, CMD_DONE: cmd_done, CMD_DROP: cmd_drop,
            CMD_LOG: cmd_log, CMD_MAILS: cmd_mails, CMD_UNDO: cmd_undo}[args.command](args, folder)


if __name__ == "__main__":
    sys.exit(main())
