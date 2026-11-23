"""메일함 스캔 — 회사 메일 손을 명령으로 불러 메일함의 지금을 사용자 폴더에 쌓고, 그 스캔을 작업 스케줄러에 걸고 · 보고 · 끈다.

    python -X utf8 -I scan.py run [--full | --new] [--now] [--hand <mail.py>] [--full-every 분] [--wait 초]
    python -X utf8 -I scan.py register [--every 분] [--full-every 분] [--hand <mail.py>] [--dry-run | --validate]
    python -X utf8 -I scan.py status [--dry-run] [--json]
    python -X utf8 -I scan.py unregister [--dry-run]

run — 한 판. 지금 모습이 없거나 `--full-every` 분이 지났으면 메일함 전체(상자마다 메일 머리 · 폴더 목록 · 규칙)를 다시 보고 지난 모습과
    견준 바뀜을 적고, 그 사이에는 「이 시각 뒤」 새 메일만 더한다. 손의 읽는 명령만 부른다 — 메일함 · 본문 · 모델에 안 닿는다.
    앞 판이 돌면 그 판은 건너뛴다 — `--wait` 를 주면 앞 판의 잠금이 풀리기를 그 초 안에서 기다렸다 돌고, 시한이 지나면 건너뛴다
register · status · unregister — 작업 스케줄러의 작업 하나(`scan_task.TASK_NAME`)를 걸고 · 보이고 · 지운다. `--dry-run` 은 보이기만,
    `--validate` 는 작업 스케줄러가 정의를 받나만 묻는다. `status --json` 은 사람의 줄 대신 프로그램이 읽는 JSON 한 줄(스캔 자리 · 걸린
    작업 · 마지막 판)이다 — 칸은 `references/DESIGN.md` 「status --json · run --wait」

남기는 것 — 사용자 폴더 `mailbox-scan/` 의 `state.json`(지금 모습) · `events.jsonl`(새 메일과 바뀜) · `runs.jsonl`(판마다의 값) ·
`pending.json`(이어 볼 상자). 왜 이 꼴인가는 `references/DESIGN.md` 가 든다.

종료 값 — 0 됐다(앞 판이 돌아 건너뛴 것도) · 1 멈췄다(세션 · 손 · 손의 글 꼴 · 다 못 봄 · 작업 스케줄러가 거절 — 다음 걸음을 끝 줄이
말한다) · 2 인자가 틀렸다.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 모듈 — `-I` 로 돌아도 싣는다
import scan_const as C  # noqa: E402
import scan_round as R  # noqa: E402
import scan_setup as U  # noqa: E402


FULL_EVERY_HELP = f"메일함 전체를 다시 보는 주기(분 · 기본 {C.FULL_EVERY_MIN} · 다 못 본 판을 잇는 기한 {C.PENDING_MAX_MIN}분보다 짧게)"
RUN_FULL_EVERY_HELP = (f"메일함 전체를 다시 보는 주기(분 · 없으면 걸린 작업의 판이 준 주기, 그것도 없으면 {C.FULL_EVERY_MIN} · 다 못 본 판을 잇는 "
                       f"기한 {C.PENDING_MAX_MIN}분보다 짧게)")
PROGRAM_DOORS = "프로그램이 부르는 문"   # 사람 · 모델이 아니라 다른 프로그램(정한 시각에 보고를 띄우는 시계)이 부르는 인자의 절
CLOCK_DOOR = "정한 시각에 보고를 띄우는 프로그램이 스캔에 한 판을 청하고 그 판을 읽을 때 쓴다 — 칸과 뜻은 references/DESIGN.md"


def parser() -> argparse.ArgumentParser:
    """명령줄의 꼴 — 하위 명령 · 인자 · 도움말."""
    ap = argparse.ArgumentParser(description="메일함 스캔 — 회사 메일 손으로 메일함의 지금을 사용자 폴더에 쌓는다(메일함은 안 바꾼다)")
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="한 판 — 때가 됐으면 메일함 전체, 아니면 새 메일만")
    way = r.add_mutually_exclusive_group()
    way.add_argument("--full", action="store_true", help="메일함 전체를 다시 본다")
    way.add_argument("--new", action="store_true", help="새 메일만 본다(지금 모습이 없으면 전체)")
    r.add_argument("--now", action="store_true", help="세션이 끊긴 뒤의 기다림을 건너뛰고 지금 돈다 — 대화에서 EP 로그인을 한 뒤")
    r.add_argument("--hand", help="회사 메일 손 mail.py 의 자리 — 없으면 MAILBOX_SCAN_HAND · SECRETARY_SKILLS · 도구 홈")
    r.add_argument("--full-every", type=int, help=RUN_FULL_EVERY_HELP)
    r.add_argument_group(PROGRAM_DOORS, CLOCK_DOOR).add_argument(
        "--wait", type=int, metavar="초", help="앞 판이 돌면 그 잠금이 풀리기를 이 초 안에서 기다렸다 돈다(시한이 지나면 건너뛴다 · 1 이상) — 일일 보고의 시계가 부른다")
    g = sub.add_parser("register", help="작업 스케줄러에 건다")
    g.add_argument("--every", type=int, default=C.EVERY_MIN, help=f"새 메일을 보는 주기(분 · 기본 {C.EVERY_MIN})")
    g.add_argument("--full-every", type=int, default=C.FULL_EVERY_MIN, help=FULL_EVERY_HELP)
    g.add_argument("--hand", help="회사 메일 손 mail.py 의 자리 — 작업의 명령줄에 굳힌다")
    how = g.add_mutually_exclusive_group()
    how.add_argument("--dry-run", action="store_true", help="걸지 않고 정의와 명령만 보인다")
    how.add_argument("--validate", action="store_true", help="작업 스케줄러가 정의를 받나만 묻는다(등록 안 함)")
    s = sub.add_parser("status", help="걸린 작업 · 마지막 판")
    s.add_argument("--dry-run", action="store_true", help="작업 스케줄러에 묻지 않는다(사용자 폴더의 것만 보인다)")
    s.add_argument_group(PROGRAM_DOORS, CLOCK_DOOR).add_argument(
        "--json", action="store_true", help="사람의 줄 대신 JSON 한 줄 — 스캔 자리 · 걸린 작업 · 마지막 판 — 일일 보고의 시계가 부른다")
    u = sub.add_parser("unregister", help="작업을 지운다(쌓인 스캔 파일은 그대로)")
    u.add_argument("--dry-run", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    """명령 입구 — 받은 하위 명령을 그 손에 나눈다. 주기 인자의 범위를 잰다 — 틀리면 종료 2."""
    if hasattr(sys.stdout, "reconfigure") and sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    for name in ("every", "full_every"):
        if getattr(args, name, 1) is not None and getattr(args, name, 1) < 1:
            parser().error(f"--{name.replace('_', '-')} 는 1 분 이상이다")
    if getattr(args, "wait", None) is not None and args.wait < 1:
        parser().error("--wait 는 1 초 이상이다")
    if (getattr(args, "full_every", None) or 0) >= C.PENDING_MAX_MIN:
        parser().error(f"--full-every 는 {C.PENDING_MAX_MIN}분보다 짧아야 한다 — 다 못 본 판을 잇는 기한이라, 같거나 길면 큰 메일함은 "
                       "덜 본 상자가 늘 버려져 끝내 다 못 본다")
    return {"run": R.cmd_run, "register": U.cmd_register, "status": U.cmd_status, "unregister": U.cmd_unregister}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
