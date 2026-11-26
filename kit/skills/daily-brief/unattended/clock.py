"""정한 시각의 시계 — 일일 보고를 정한 시각마다 사람 없이 띄우고, 보고 창에서 고르신 것 · 누르신 「일정에 넣기」를 받는 작업과 그 시각표를
걸고 · 보이고 · 내린다. 사람 없는 실행의 입구 하나다 — 어느 모듈도 이 파일을 싣지 않는다.

    python -X utf8 -I clock.py tick --dir <사용자 폴더> --hand <mail.py>
    python -X utf8 -I clock.py register [--at [HH:MM …]] [--hand <mail.py>] [--claude <claude>] [--dry-run | --validate] [--dir …]
    python -X utf8 -I clock.py at [HH:MM …] [--claude <claude>] [--dry-run] [--dir …]
    python -X utf8 -I clock.py off [--dry-run] [--dir …]
    python -X utf8 -I clock.py away on|off [--chosen-at <고른 때>] [--dry-run] [--dir …]
    python -X utf8 -I clock.py window-times HH:MM [HH:MM …] [--window-base [HH:MM …]] --chosen-at <고른 때> [--dir …]
    python -X utf8 -I clock.py status [--dry-run] [--dir …]
    python -X utf8 -I clock.py unregister [--dry-run] [--dir …]
    python -X utf8 -I clock.py adopt [--dir …]
    python -X utf8 -I clock.py lend --why put|appr|run --ceiling <초> [--lost] [--dir …]
    python -X utf8 -I clock.py release --why put|appr|run [--hold] [--futile] [--dir …]

tick — 작업 스케줄러가 주기마다 부르는 한 판. 보고 시각의 칸이면 사내 세션을 보고 · 부를 판이면 스스로 로그인하고 · 메일함 스캔에 「지금 한
    판」을 청한 뒤 그 판이 산 세션에서 읽었으면 일일 보고를 띄운다. 보고 창의 고름 · 누름은 판마다 받는다.
register · status · unregister — 작업 스케줄러의 시계 작업 하나(`clock_task.TASK_NAME`)를 걸고 · 보이고 · 지운다. 주기는 시계의 것
    (`unattended_const.CLOCK_EVERY_MIN`)이다. 쌓인 파일은 안 건드린다.
at · off — 보고 시각표(시각 하나 이상 · 서울)와 띄울 claude 를 걸고 · 내린다. 시각은 전부를 준다. 보고 시각을 거는 것이 곧 그 시각의 스스로
    로그인이다(그날 첫 시각에 한 번 · 뒤 시각은 세션이 끊겨 있을 때 · 시각 사이에는 안 한다).
away — 자리 밖에서 보기 — 켠 PC 에서만 시계 판의 코드가 사람 없이 띄운 보고를 칸마다 한 통 본인 주소로 보낸다.
window-times — 보고 창에서 고르신 시각(창 곁의 손이 준다) — 시계 판이 창에서 받을 때와 같은 자로 재고 건다.
adopt — 시계를 이 홈으로 옮겨 받는다 — 옛 파일을 새 이름으로 옮기고, 걸린 시계가 다른 홈의 입구 · 손을 부르면 이 홈의 것으로 다시 걸며, 시계가
    없으면 보고 시각표가 있는 PC 에만 건다. 메일함 스캔의 작업에는 기대지 않는다(설치는 업데이트 때 한 홈에서 부른다). 여러 번 불러도 같다.

lend · release — 보고 창의 단추(「일정에 넣기」 · 「결재 창 열기」)가 사내 세션을 쓰기 앞뒤에 창 곁의 손이 부른다 — 오늘 돌려준 로그인을 잠깐
    다시 빌리고, 다 쓰면 곧 돌려준다(`loan.py`).
`--dir` 이 없으면 사용자 폴더를 곁의 스캔(`scan.py status --json`)에 묻는다(`tick` 은 늘 받는다). 명령마다 내는 글 · 종료 값의 원본은
`references/DESIGN.md` 「사람 없는 실행의 문」 표다. 종료 값 — 0 됐다 · 1 멈췄다(끝 줄이 다음 걸음을 말한다) · 2 인자가 틀렸다.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "scripts"), str(HERE)]   # 같은 스킬의 바탕(scripts/)을 먼저 · 곁의 모듈 — 안의 `clock` 은 바탕의 것이다
import cli  # noqa: E402
import clock_setup as U  # noqa: E402
import clock_tick as K  # noqa: E402
import loan as LN  # noqa: E402
import scan_door as D  # noqa: E402
import unattended_const as C  # noqa: E402

AT_HELP = (f"보고 시각표 — 시각 하나 이상(서울 · 빈칸이나 쉼표로 · 안 주면 {C.BRIEF_AT_DEFAULT}). 시각마다 그 시각부터 다음 시각까지(길어야 "
           f"{C.BRIEF_WAIT_MIN}분 · 그날 자정까지) 사내 세션이 서는 첫 판에 일일 보고를 한 번 띄운다. 시각마다 {C.BRIEF_ROOM_MIN}분 넘게 띄어야 걸린다. "
           "보고 시각에 사내 세션이 끊겨 있으면 그 판이 스스로 로그인해 메일함을 읽고 띄운다 — 그러면 평소 Edge 의 사내 메일 · 일정 창이 닫히고 "
           f"그 EP 포털에서 앱을 새로 못 띄우다가, 그 보고가 끝나고 {C.GIVE_BACK_AFTER_MIN}분 뒤 로그인을 평소 Edge 로 돌려준다(거는 줄이 말한다)")
CLAUDE_HELP = "띄울 claude 의 자리 — 없으면 걸어 둔 것, 그것도 없으면 PATH 에서 찾는다"
CHOSEN_HELP = "보고 창에서 고르신 때(창 곁의 손이 준다 · 나중의 말씀이 이긴다)"


def parser() -> argparse.ArgumentParser:
    """명령줄의 꼴 — 하위 명령 · 인자 · 도움말."""
    ap = argparse.ArgumentParser(prog=C.CLOCK_ENTRY, description="정한 시각의 시계 — 일일 보고를 정한 시각마다 사람 없이 띄운다")
    sub = ap.add_subparsers(dest="command", required=True)
    t = sub.add_parser("tick", help="한 판 — 작업 스케줄러가 부른다")
    t.add_argument("--dir", required=True, help="사용자 폴더")
    t.add_argument("--hand", required=True, help="회사 메일 손 mail.py 의 자리")
    g = sub.add_parser("register", help="시계를 작업 스케줄러에 건다")
    g.add_argument("--at", nargs="*", metavar="HH:MM", help=AT_HELP)
    g.add_argument("--hand", help="회사 메일 손 mail.py 의 자리 — 없으면 형제 스킬 company-mail 의 것")
    g.add_argument("--claude", help=CLAUDE_HELP)
    how = g.add_mutually_exclusive_group()
    how.add_argument("--dry-run", action="store_true", help="걸지 않고 정의와 명령만 보인다")
    how.add_argument("--validate", action="store_true", help="작업 스케줄러가 정의를 받나만 묻는다(등록 안 함)")
    a = sub.add_parser("at", help="보고 시각표를 걸고 바꾼다(작업 스케줄러는 안 건드린다)")
    a.add_argument("at", nargs="*", metavar="HH:MM", help=AT_HELP)
    a.add_argument("--claude", help=CLAUDE_HELP)
    a.add_argument("--dry-run", action="store_true", help="걸지 않고 띄울 명령 · 열린 명령 · 막은 명령만 보인다")
    o = sub.add_parser("off", help="보고 예약을 내린다")
    o.add_argument("--dry-run", action="store_true")
    w = sub.add_parser("away", help="자리 밖에서 보기를 켜고 끈다 — 켜면 사람 없이 띄운 보고를 칸마다 한 통 본인 주소(켤 때 주소록의 「나」)로 보낸다")
    w.add_argument("switch", choices=("on", "off"))
    w.add_argument_group(cli.DOORS_TITLE, "창 곁의 손(presses.py)이 보고 창의 누름을 넘길 때 쓴다 — 끝 줄 하나(그 창에 적을 말)와 종료 값으로 답한다"
                         ).add_argument("--chosen-at", metavar="때", help=CHOSEN_HELP)
    w.add_argument("--dry-run", action="store_true")
    x = sub.add_parser("window-times", help="보고 창에서 고르신 보고 시각을 건다 — 창 곁의 손이 부른다")
    x.add_argument("times", nargs="+", metavar="HH:MM", help="고르신 보고 시각 전부")
    x.add_argument("--window-base", nargs="*", metavar="HH:MM", help="고르실 때 창이 보이던 시각(없으면 지금 걸린 것)")
    x.add_argument("--chosen-at", metavar="때", help=CHOSEN_HELP)
    s = sub.add_parser("status", help="시계 작업 · 보고 예약 — 시각마다 오늘 어떻게 됐나")
    s.add_argument("--dry-run", action="store_true", help="작업 스케줄러에 묻지 않는다(사용자 폴더의 것만 보인다)")
    u = sub.add_parser("unregister", help="시계 작업을 지우고 보고 예약을 내린다(쌓인 파일은 그대로)")
    u.add_argument("--dry-run", action="store_true")
    n = sub.add_parser("lend", help="보고 창의 단추가 사내 세션을 쓴다고 적는다 — 끊겼으면 오늘 돌려준 뒤일 때만 다시 로그인한다(창 곁의 손이 부른다)")
    n.add_argument("--why", required=True, choices=LN.WHYS, help="세션을 쓰는 단추의 일")
    n.add_argument("--ceiling", type=int, required=True, help="그 일이 세션을 쓰는 가장 긴 초 — 놓는다고 안 해도 그 뒤로는 안 쓴다")
    n.add_argument("--lost", action="store_true", help="그 일이 방금 세션 없음을 냈다(손에 다시 안 묻는다)")
    r = sub.add_parser("release", help="보고 창의 단추의 일이 사내 세션을 놓는다 — 빌린 로그인을 쓰는 일이 더 없으면 곧 돌려준다")
    r.add_argument("--why", required=True, choices=LN.WHYS)
    r.add_argument("--hold", action="store_true", help="사람이 그 세션의 창에서 누른다(결재 창) — 돌려주기를 그만큼 미룬다")
    r.add_argument("--futile", action="store_true", help="빌린 로그인 위에서도 세션 없음이었다 — 그 일에는 오늘 다시 안 빌려 준다")
    sub.add_parser("adopt", help="옛 파일을 옮겨 받고 시계를 이 홈으로 건다(다른 홈을 부르면 · 없는데 보고 시각표가 있으면) — 설치 · 대화가 부른다")
    for one in (g, a, o, w, x, s, u, n, r, sub.choices["adopt"]):
        one.add_argument("--dir", help=D.DIR_HELP)
    return ap


def main(argv: list[str] | None = None) -> int:
    """명령 입구 — 사용자 폴더를 정하고(`--dir` · 없으면 스캔에 묻는다) 받은 하위 명령을 그 손에 나눈다. 못 정하면 그 말과 1."""
    if hasattr(sys.stdout, "reconfigure") and sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    if args.command == "tick":
        return K.tick(pathlib.Path(args.dir), pathlib.Path(args.hand))
    home = D.home_of(args.dir)
    if home is None:
        print(f"[시계 — {D.NO_HOME}]")
        return U.EXIT_STOPPED
    return {"register": U.cmd_register, "at": U.cmd_at, "off": U.cmd_off, "away": U.cmd_away, "window-times": U.cmd_window_times,
            "status": U.cmd_status, "unregister": U.cmd_unregister, "adopt": U.cmd_adopt,
            "lend": LN.cmd_lend, "release": LN.cmd_release}[args.command](args, home)


if __name__ == "__main__":
    sys.exit(main())
