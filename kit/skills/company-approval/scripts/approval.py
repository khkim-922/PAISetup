"""전자결재 스킬의 얇은 명령 — 곁의 손으로 결재함을 읽고, 결재 문서를 임시저장까지 짓고, 그 문서 창을 사람의 Edge 에 띄운다.
상신 · 승인 · 반려 · 회수는 하지 않는다 — 사람이 띄운 창에서 누른다.

부르는 꼴 · 명령마다의 인자 · 종료 값은 ``--help`` 가 낸다 — 그 글은 표(``approval_table`` 의 ``STARTS`` · ``CHANGES`` · ``ENDS`` · ``READS`` ·
``NOT_YET`` · ``BOXES``)와 이 파일의 ``EXITS`` · argparse 에서 선다. 이 머리말은 고치는 사람이 읽는 계약만 든다.

- 짜임 — 이 파일은 입구다: 인자 → 표에 대 본 거름(세션 전) → 세션 쥐기(``ep_session.session_first``) → 명령의 손. 읽기 명령은
  ``approval_read`` 가, 쓰기 명령(preview · save · discard)은 ``approval_write`` 가, 창 띄우기(open)는 ``approval_open`` 이 든다.
  결재 앱에 묻는 한 자리는 바탕 ``iams`` 다 — 손 셋이 함께 쓰는 것(앱 안의 주소 · 문서 열쇠의 꼴 · 결재함의 기간 · Edge 에 창 띄우기)도 거기 하나다.
  표는 ``approval_table`` 하나다(입구 밑 · 손 밑). 손 셋은 서로 · 입구를 안 부르고 ``iams`` 와 그 표만 읽는다
- 문서 열쇠 — 명령이 내고 받는 문서는 다 box 줄의 id 꼴(``APPR_DOC_ID.OVN.AVN.APVN``) 하나다. 한 명령이 낸 id 를 다음 명령이 그대로 받는다
- 쓰기의 차례 — preview 와 save 는 같은 판(``approval_write.plan``)을 짓고 그 해시가 key 다. 보인 뒤 무엇이든 달라졌으면 저장하지
  않는다(종료 4). 저장한 뒤에는 임시저장 목록에서 그 문서를 다시 읽어 끝을 정하고, 섰으면 그 문서의 고치는 창을 사람의 Edge 에 띄운다
- 사람 — 결재선 · 참조 · 배포의 사람은 주소록(스킬 company-directory)이 쓴 사람 파일(people.json)로 받는다. 이름을 사람으로 가르는 일은
  주소록 몫이다
- 내는 것 — 표준 출력에 JSON 하나(``ep_command.finish``)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
try:
    import ep_command
    import ep_session
    from ep_command import EXIT_ARGS, EXIT_OK, EXIT_SESSION, EXIT_STALE, EXIT_TOOL, Stop
    import iams                                 # 바탕 — 문서 열쇠의 꼴(세션 앞 거름이 쓴다)
    from approval_table import BOXES, CHANGES, ENDS, NOT_YET, READS, STARTS
except ImportError:                             # 형제 스킬 ep-login 이 곁에 없다 — 답의 꼴(JSON 하나 · 종료 1)은 지킨다
    print(json.dumps({"error": "tool", "message": f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"},
                     ensure_ascii=False))
    sys.exit(1)

HAND = "iams"                               # 결재 앱 손의 모듈 이름 — 이 파일 곁
# 명령 → 그 일을 하는 손의 모듈. 손 셋은 서로 · 입구를 안 부르고 바탕 iams 와 표 approval_table 만 읽는다
HANDS = {"forms": "approval_read", "form": "approval_read", "box": "approval_read", "read": "approval_read",
         "open": "approval_open", "preview": "approval_write", "save": "approval_write", "discard": "approval_write"}
MUTATING = ("save", "discard")
EXITS = ep_command.exit_legend((EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION, EXIT_STALE),
                               {EXIT_ARGS: "없는 손가락 · 그 출발이 안 받는 손가락 · 빠진 값이면 어디서 하나나 받는 꼴을 댄다",
                                EXIT_STALE: "보인 판과 지금 판이 달라 저장 · 지우기를 안 했다 — 답의 preview 를 다시 보인다"})


# ── 표에서 짓는 것 — 지도 · 인자 거르기 ────────────────────────────────────────────────────────────
def finger_map() -> str:
    """--help 의 지도 — 표 다섯에서 짓는다."""
    names = list(STARTS)
    lines = ["지도 — 출발 하나 × 바꿀 것 아무 조합 × 끝 하나. 한 번 부름이 문서 한 건을 한 번 다룬다", "", "출발"]
    lines += [f"  {k:<6} {s.takes + ' <문서>' if s.takes else '(인자 없음)':<14} {s.word} — {s.screen}" for k, s in STARTS.items()]
    lines += ["", "바꿀 것 (● 꼭 든다 · ○ 받는다 · △ 받되 회사에서 안 쟀다 · — 없다)"]
    lines += ep_command.change_lines(CHANGES, names, 16, "회사에서 안 쟀다 — 저장한 뒤 read 로 그대로 섰는지 본다")
    lines += ["", "끝 (상신 · 승인 · 반려는 없다 — 사람이 그 문서 창에서 누른다)"]
    lines += [f"  {k:<8} 출발 {' · '.join(starts):<18} {word}" for k, (starts, word, _) in ENDS.items()]
    lines += ["", "읽기"] + [f"  {k:<6} {w}" for k, w in READS.items()]
    lines += ["", "아직 없는 손가락 (인자를 주면 세션 전에 사람이 어디서 하나를 대며 종료 2 로 멈춘다)"]
    lines += ep_command.not_yet_lines(NOT_YET, CHANGES, 14)
    return "\n".join(lines)


def end_of(args) -> str:
    """부른 명령이 맺는 끝 — preview 는 그 출발의 끝 가운데 바꿀 것을 받는 것(save)이다."""
    return "save" if args.command == "preview" else args.command


def fingers(args) -> str:
    """부른 명령의 출발을 고르고 표에 대 본다 — 아직 없는 손가락 · 출발에 없는 끝 · 출발에 없는 손가락 · 바꿀 것을 안 받는 끝 · 빠진 값을
    차례로 거른다(저마다 그 일을 어디서 하는지 대며 Stop(인자)). 출발을 낸다."""
    ep_command.refuse_not_yet(args, NOT_YET, CHANGES)
    start = ep_command.pick_start(args, STARTS)
    end = end_of(args)
    starts, word, takes_changes = ENDS[end]
    if start not in starts:
        raise Stop(EXIT_ARGS, "args", f"「{STARTS[start].word}」에서는 {end}({word.split(' — ')[0]})를 못 한다. 다음: "
                                      f"{' · '.join(STARTS[s].takes or s for s in starts)} 로 다시 부른다", stepped=True)
    if not takes_changes and any(ep_command.given(args, c) for c in CHANGES.values()):
        raise Stop(EXIT_ARGS, "args", f"{end} 는 바꿀 것을 안 받는다. 다음: 고치려면 save --draft 로 부른다", stepped=True)
    ep_command.refuse_foreign(args, CHANGES, start, STARTS[start].word)
    if end != "discard":
        ep_command.refuse_missing(args, CHANGES, start, STARTS[start].word)
    for c in ("approvers", "agree", "refs"):
        ep_command.people_of(getattr(args, c, None))    # 사람 파일의 꼴 — 틀렸으면 세션 전에 Stop(인자)
    for flag, values in (("--from", [getattr(args, "from", None)]), ("--draft", [getattr(args, "draft", None)]),
                         ("--link", getattr(args, "link", None) or [])):
        for value in values:
            if value is not None:
                iams.doc_of(value, flag)                # 문서 열쇠의 꼴 — 틀렸으면 세션 전에 Stop(인자)(다시 쓰기 창을 열기 전에)
    if getattr(args, "body_file", None):
        ep_command.text_file(args.body_file, "--body-file 의 파일")
    return start


# ── 인자 · 입구 ───────────────────────────────────────────────────────────
def parser() -> argparse.ArgumentParser:
    """명령의 인자 표 — 하위 명령과 인자를 표(``STARTS`` · ``CHANGES`` · ``ENDS`` · ``READS`` · ``NOT_YET``)에서 세우고 지도 · 종료 값 범례를 --help 에 단다."""
    raw = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(prog="approval.py", description="사내 전자결재 — 결재함 읽기 · 문서 읽기 · 임시저장까지 짓기 · 문서 창 띄우기(상신 · 결재는 사람이)",
                                epilog=f"{finger_map()}\n\n{EXITS}", formatter_class=raw)
    sub = p.add_subparsers(dest="command", required=True, metavar="<명령>")
    sub.add_parser("forms", help=READS["forms"])
    f = sub.add_parser("form", help=READS["form"])
    f.add_argument("form_id", metavar="FORM_ID", help="forms 의 FORM_ID")
    b = sub.add_parser("box", help=READS["box"], formatter_class=raw,
                       epilog="결재함\n" + "\n".join(f"  {k:<13} {v['word']}" for k, v in BOXES.items()))
    b.add_argument("box", choices=list(BOXES), metavar="함", help=" · ".join(BOXES))
    b.add_argument("--since", metavar="YYYY-MM-DD", help="이날부터 — 기간을 꼭 받는 함은 안 주면 한 달 전(앱이 6 달까지만 묻는다)")
    b.add_argument("--until", metavar="YYYY-MM-DD", help="이날까지 — 기간을 꼭 받는 함은 안 주면 오늘")
    b.add_argument("--subject", dest="words", metavar="말", help="제목에 든 말(앱이 거른다)")
    b.add_argument("--from", dest="start", type=int, default=0, metavar="N", help="N 째 줄부터(답의 more 가 댄다)")
    r = sub.add_parser("read", help=READS["read"])
    r.add_argument("doc", metavar="문서", help="box 줄의 id")
    r.add_argument("--from", dest="start", type=int, default=0, metavar="N", help="본문을 N 째 글자부터(답의 more 가 댄다)")
    o = sub.add_parser("open", help=READS["open"])
    o.add_argument("doc", metavar="문서", help="box 줄의 id")
    o.add_argument("--box", choices=list(BOXES), metavar="함",
                   help="그 줄이 온 함 — 창의 단추(결재 · 참조 의견 · 배포 · 임시저장 고치기)가 함에서 갈린다. 안 주면 결재하기 함에 있으면 결재 창 · 임시저장이면 고치는 창 · 그 밖은 보기 창")
    for name in ("preview", *ENDS):
        a = sub.add_parser(name, help="지을 꼴 미리 보기 · key(저장하지 않는다)" if name == "preview" else f"⚠ {ENDS[name][1]}",
                           epilog=finger_map(), formatter_class=raw)
        for s in STARTS.values():
            if s.takes:
                a.add_argument(s.takes, default=None, metavar="문서", help=f"출발 — {s.word}")
        if name == "preview" or ENDS[name][2]:
            for c in CHANGES.values():
                for flag, extra in c.flags:
                    a.add_argument(flag, default=None, **{"help": c.word, **extra})
            for n in NOT_YET.values():
                for flag, extra in n.flags:
                    a.add_argument(flag, **{"default": None, "help": f"아직 없다 — {n.word}", **extra})
        if name != "preview":
            a.add_argument("--confirm", required=True, metavar="key", help=ENDS[name][1].split("열쇠: ")[-1])
    return p


def work(args, app) -> dict:
    """명령 하나 — 세션 앞 거름(쓰기 명령은 ``fingers``)을 지난 뒤 세션을 쥐고 그 명령의 손을 돈다. 바꾸는 명령은 늘 받는 손부터 한 번."""
    start = fingers(args) if args.command in ("preview", *ENDS) else None
    hand = ep_command.load(HANDS[args.command], HERE)
    return ep_session.session_first(lambda f: hand.run(app.App(f), args, start), expired=(app.SessionExpired, app.SessionMissing),
                                    file_first=args.command not in MUTATING)


def main() -> int:
    """명령 입구 — 인자를 읽고 앱 손을 실어 ``work`` 의 답을 JSON 하나로 찍는다(종료 값은 ``ep_command.finish``)."""
    args = parser().parse_args()
    return ep_command.finish(lambda app: work(args, app), HAND, HERE, indent=1, args_errors=("Refused",))


if __name__ == "__main__":
    sys.exit(main())
