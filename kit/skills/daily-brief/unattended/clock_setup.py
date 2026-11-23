"""시계 걸기 · 보고 시각표 · 보기 · 끄기 · 옮겨 받기 — `clock.py register · at · off · away · window-times · status · unregister · adopt` 의
손. 작업 스케줄러의 시계 작업 하나(`clock_task`)와 보고 시각표(`brief_schedule`)를 걸고 · 보이고 · 내린다. 시계 판의 코드는 안 부른다.

    cmd_register(args, home) · cmd_at(args, home) · cmd_off(args, home) · cmd_away(args, home) · cmd_window_times(args, home)
    cmd_status(args, home) · cmd_unregister(args, home) · cmd_adopt(args, home)     # 종료 값 — 0 됐다 · 1 멈췄다(끝 줄이 다음 걸음을 말한다)

`away … --chosen-at` · `window-times …` 의 끝 줄 하나와 종료 값은 창 곁의 손(`scripts/presses.py`)이 읽는다 — 꼴을 바꾸지 않는다. 명령마다
내는 글의 원본은 `references/DESIGN.md` 「사람 없는 실행의 문」 표다.
"""

from __future__ import annotations

import pathlib
from typing import Any

import away_mail as A
import brief_schedule as S
import brief_slots as BS
import brief_status as BST
import brief_window as BWN
import brief_words as BW
import claude_launch as L
import clock as tm
import clock_book as B
import clock_task as T
import task_base as TB
from task_base import shown
import launch_base as LB
import scan_door as D
import session_login as SL
import take_over as TO
import unattended_const as C
import unattended_store as st
import window_link as W

EXIT_OK, EXIT_STOPPED, EXIT_ARGS = 0, 1, 2
EVERY_FALLBACK_MIN = 15          # 스캔 작업의 주기를 못 읽었을 때 시계가 쓰는 주기 — 스캔의 기본 주기(그 스킬 `scan_const.EVERY_MIN`)
NO_CLAUDE = ("Claude Code 명령줄(claude)을 못 찾았다{where}. 정한 시각의 보고는 claude -p 로 띄운다 — VS Code 확장만 깐 PC 면 확장 폴더의 "
             "resources/native-binary/claude.exe 를 --claude 로 준다")
NO_SCAN_TASK = "메일함 스캔이 안 걸려 있다. 다음: scan.py register"
CLOCK_MISSING = "  ⚠ 시계가 안 걸려 있어 이 보고는 안 뜬다. 다음: clock.py register"
LEGACY_HINT = "[시계 — 걸려 있지 않다 · 옛 보고 시각표가 있다 — 다음: clock.py adopt]"
ADOPT_SKIPPED = {"unregistered": "[시계 — 걸 것이 없다: 메일함 스캔이 안 걸려 있다]",
                 "elsewhere": "[시계 — 건드리지 않았다: 이 홈의 스캔이 건 작업이 아니다]",
                 "present": "[시계 — 이미 걸려 있다]"}
ADOPTED, ADOPTED_FRESH = "[시계 — 걸었다 · 옛 보고 시각표를 옮겨 받았다]", "[시계 — 걸었다]"


# ── 보고 시각표 ──────────────────────────────────────────────────────────────────

def brief_wanted(args, home: pathlib.Path) -> tuple[list[str] | None, pathlib.Path | None, str]:
    """`--at` · `--claude` 를 재어 (보고 시각표, claude, 거절의 말). 보고를 안 청했으면 (None, None, ""). 시각을 안 주면 기본 시각 하나다."""
    if args.at is None:
        return None, None, ""
    times, bad = BS.times_given(args.at or [C.BRIEF_AT_DEFAULT])
    if bad:
        return None, None, f"{bad}. {BW.in_force(S.load(home)[0])}"
    held, refused = held_setting(home)
    if refused:
        return None, None, refused
    tight = BW.room_words(BS.first_tight(times, set(times) - set(held["times"] if held else [])))
    if tight:
        return None, None, f"{tight}. {BW.in_force(held)}"
    claude = LB.pick_claude(args.claude, held.get("claude") if held else None)
    if claude is None:
        return None, None, NO_CLAUDE.format(where=f"({args.claude})" if args.claude else "(PATH)")
    return times, claude, ""


def held_setting(home: pathlib.Path) -> tuple[dict[str, Any] | None, str]:
    """지금 걸린 보고 시각표 — 글이 깨진 파일은 없는 것으로 본다(새로 걸면 고쳐진다). 그 순간 못 읽었으면 거절의 말을 낸다 — 빈 것으로 읽으면
    claude · 자리 밖에서 보기를 기본값으로 덮어 쓴다. 내는 것 — (설정, 거절의 말)."""
    try:
        raw = S.read_brief(home)
    except st.Unreadable as exc:
        if not exc.broken:
            return None, f"걸려 있던 보고 시각표를 그 순간 못 읽었다({exc}). 다음: 같은 명령을 다시 준다"
        raw = None
    held, _ = S.setting_of(raw)
    return held, ""


def save_and_tell(home: pathlib.Path, times: list[str], claude: pathlib.Path, hand: pathlib.Path | None, retry: str) -> bool:
    """보고 시각표를 걸고 그 한 줄을 낸다 — 보고 시각의 로그인과 그 값을 늘 말하고, 이 PC 에서 로그인 입구를 못 찾으면 그것도 말한다. 열린
    보고 창에 알렸으면 그 구절을 붙인다. 걸려 있던 파일을 그 순간 못 읽으면 안 걸고 그렇다고 말한다(`retry` 가 다음 걸음). 걸었으면 True."""
    try:
        S.save(home, times, claude)
    except st.Unreadable as exc:
        print(f"[보고 예약 — 걸지 않았다: 걸려 있던 보고 시각표를 그 순간 못 읽었다({exc}). 다음: {retry}]")
        return False
    print(f"{set_line(times, claude)}{W.tell_window(home)}")
    if SL.login_command(hand) is None:
        print(f"  {BW.LOGIN_MISSING}")
    return True


def set_line(times: list[str], claude: pathlib.Path) -> str:
    """보고 시각표를 건 뒤의 한 줄 — 언제 띄우나 · 보고 시각의 로그인과 그 값 · 띄울 claude."""
    return f"[보고 예약 — {BW.window_words(BS.windows(times, tm.utc_now()))} 일일 보고를 띄운다 · {BW.LOGIN_WORDS} · claude {claude}]"


def show_brief_plan(home: pathlib.Path, times: list[str], claude: pathlib.Path, hand: pathlib.Path | None) -> None:
    """걸면 띄울 것 — 명령 · 보고 시각의 로그인 명령 · 열린 명령 · 막은 명령(`--dry-run`)."""
    cmd, settings, _ = L.plan({"times": times, "claude": str(claude)}, hand, home)
    print(f"[보고 예약 — {BW.window_words(BS.windows(times, tm.utc_now()))} 띄운다({BW.LOGIN_WORDS}): {shown(cmd)} < {home / C.LAUNCH_PROMPT_FILE}]")
    print("  보고 시각의 로그인: " + (shown(SL.login_command(hand)) if SL.login_command(hand) else BW.LOGIN_MISSING))
    print("  열린 명령: " + " | ".join(settings["permissions"]["allow"]))
    print("  막은 명령: " + " | ".join(settings["permissions"]["deny"]))


def put_times(args, home: pathlib.Path, hand: pathlib.Path | None, retry: str) -> int:
    """보고 시각표를 걸고 바꾼다 — 재고(`brief_wanted`), 보이기만 하거나 건다. 종료 값 — 0 됐다 · 1 안 걸었다."""
    times, claude, refused = brief_wanted(args, home)
    if refused:
        print(f"[보고 예약 — 걸지 않았다: {refused}]")
        return EXIT_STOPPED
    if args.dry_run:
        show_brief_plan(home, times, claude, hand)
        return EXIT_OK
    return EXIT_OK if save_and_tell(home, times, claude, hand, retry) else EXIT_STOPPED


def cmd_at(args, home: pathlib.Path) -> int:
    """보고 시각표를 걸고 바꾼다(`at`) — 걸었는데 시계가 작업 스케줄러에 안 걸려 있으면 그렇다고 알린다."""
    done = put_times(args, home, D.mail_hand(None)[0], "같은 명령을 다시 준다")
    if done == EXIT_OK and not args.dry_run and TB.ask(TB.query_command(T.TASK_NAME)).code != 0:
        print(CLOCK_MISSING)
    return done


def cmd_off(args, home: pathlib.Path) -> int:
    """보고 예약을 내린다(`off`) — 내렸으면 열린 보고 창에 알린다."""
    if args.dry_run:
        print("[보고 예약 — 내리지 않고 보이기만 한다]")
        return EXIT_OK
    print(f"[보고 예약 — 내렸다]{W.tell_window(home)}" if S.clear(home) else "[보고 예약 — 걸려 있지 않았다]")
    return EXIT_OK


def cmd_away(args, home: pathlib.Path) -> int:
    """자리 밖에서 보기를 켜고 끈다 — 대화의 말(고른 때는 지금)과 창 곁의 손이 준 보고 창의 누름(`--chosen-at`)이 같은 길로 간다. 켤 때 본인
    주소를 주소록 손의 「나」에서 받는다. 나중의 말씀이 이긴다. 끝 줄 — 대화면 「[자리 밖에서 보기 — 말]」, `--chosen-at` 이면 그 창에 적을 말
    한 줄만(창 곁의 손이 그대로 옮긴다). 종료 값 0 따랐다 · 1 안 따랐다."""
    on = args.switch == "on"
    if args.dry_run:
        print("[자리 밖에서 보기 — 바꾸지 않고 보이기만 한다. " + ("켜면 주소록의 「나」에서 본인 주소를 받아, 켠 뒤 사람 없이 띄운 보고를 칸마다 한 통 "
              "그 주소로만 보낸다(받는 분 · 보내는 분이 다 본인)]" if on else "끄면 사람 없는 보고를 메일로 안 보낸다]"))
        return EXIT_OK
    chosen = tm.parse_chosen(args.chosen_at) if args.chosen_at else tm.utc_now()
    if chosen is None:
        print(BW.CHOSEN_UNREAD)
        return EXIT_STOPPED
    home.mkdir(parents=True, exist_ok=True)
    said, refused = A.apply_away(home, on, chosen, D.mail_hand(None)[0])
    if args.chosen_at:                  # 창 곁의 손이 부른 것 — 그 손이 이 말을 그 창에 적고 지금 모습도 알린다
        print(said)
        return EXIT_STOPPED if refused else EXIT_OK
    address = (S.away_of(S.load(home)[0]).get("address") or "") if on and not refused else ""
    print(f"[자리 밖에서 보기 — {said}]" + (f" · 받는 분 · 보내는 분 본인({address})" if address else "") + W.tell_window(home))
    return EXIT_STOPPED if refused else EXIT_OK


def cmd_window_times(args, home: pathlib.Path) -> int:
    """보고 창에서 고르신 보고 시각을 건다 — 창 곁의 손이 준 고름(시각들 · `--window-base` · `--chosen-at`)을 시계 판이 창에서 받을 때와 같은
    자(`brief_window.take_window_times`)로 잰다. 끝 줄 — 그 창에 적을 말 한 줄(창 곁의 손이 그대로 옮긴다). 종료 값 0 따랐다 · 1 안 따랐다."""
    if not args.chosen_at:
        print("고르신 때가 없어 걸지 않았습니다 — 대화에서 말씀해 주세요")
        return EXIT_STOPPED
    setting, bad = S.load(home)
    if setting is None:
        print(f"걸지 않았습니다 — {bad or '사람 없는 보고가 걸려 있지 않습니다'}. {BW.in_force(None)}")
        return EXIT_STOPPED
    said, refused = BWN.take_window_times(home, setting, args.times, args.window_base or [], args.chosen_at)
    print(said)
    return EXIT_STOPPED if refused else EXIT_OK


# ── 시계 작업 ────────────────────────────────────────────────────────────────────

def scan_task() -> dict[str, Any]:
    """곁의 스캔이 건 작업의 칸(`status --json` 의 `task`) — 못 물었으면 빈 것."""
    return (D.status(dry_run=False) or {}).get("task") or {}


def cmd_register(args, home: pathlib.Path) -> int:
    """시계를 작업 스케줄러에 건다 — 스캔이 걸렸나 보고, 손을 정하고, 보고 시각표 요청을 재고, 정의를 지어(보이기만 · 받나만 묻기도) 건 뒤
    `--at` 이 있으면 시각표를 건다. 주기는 스캔의 걸린 주기를 따른다 — 보고 시각의 틈 규칙이 그 주기에 기댄다."""
    task = scan_task()
    if task.get("registered") is not True:
        print(f"[예약 — 걸지 않았다: {NO_SCAN_TASK}]")
        return EXIT_STOPPED
    hand, missing = D.mail_hand(args.hand or task.get("hand"))
    if hand is None:
        print(f"[예약 — 걸지 않았다: {missing}]")
        return EXIT_STOPPED
    times, claude, refused = brief_wanted(args, home)
    if refused:
        print(f"[예약 — 걸지 않았다: {refused}]")
        return EXIT_STOPPED
    every = task.get("every_min") or EVERY_FALLBACK_MIN
    xml = T.task_xml(every=every, home=home, hand=hand)
    path = home / C.CLOCK_XML_FILE
    if TB.windowless_python().name.lower() != "pythonw.exe":
        print("[예약 — ⚠ 창 없는 파이썬(pythonw.exe)을 못 찾아 판마다 창이 뜬다]")
    if args.dry_run:
        print(f"[예약 — 걸지 않고 보이기만 한다. 걸면 시계 판이 {every}분마다 돈다(앞 판이 돌면 그 주기는 건너뛴다): {shown(TB.register_command(T.TASK_NAME, path))}]")
        if times:
            show_brief_plan(home, times, claude, hand)
        print(xml)
        return EXIT_OK
    TB.write_xml(path, xml)
    if args.validate:
        return validate_task(path)
    if not put_task(path):
        return EXIT_STOPPED
    print(f"[예약 — {T.TASK_LEAF} 시계를 걸었다: {every}분마다 · 앞 판이 돌면 그 주기는 건너뛴다]")
    if times:
        return EXIT_OK if save_and_tell(home, times, claude, hand, "clock.py at 으로 다시 건다") else EXIT_STOPPED
    return EXIT_OK


def put_task(path: pathlib.Path) -> bool:
    """정의 파일로 작업을 건다 — 작업 스케줄러가 거절하면 그 말을 내고 False."""
    done = TB.ask(TB.register_command(T.TASK_NAME, path))
    if done.code != 0:
        print(f"[예약 — 작업 스케줄러가 거절했다: {(done.out + done.err).strip()[-400:]}]")
        return False
    return True


def validate_task(path: pathlib.Path) -> int:
    """작업 스케줄러가 지은 정의를 받나만 묻는다(등록 안 함) — 받으면 0, 거절하면 그 말과 1."""
    done = TB.ask(TB.validate_command(T.VALIDATE_ENV), env=TB.validate_env(T.VALIDATE_ENV, path))
    ok = TB.accepted(done)
    print(f"[예약 — 작업 스케줄러가 정의를 {'받는다' if ok else '거절했다'}(등록 안 함): {path}]")
    if not ok:
        print(done.err.strip()[-600:])
    return EXIT_OK if ok else EXIT_STOPPED


def cmd_status(args, home: pathlib.Path) -> int:
    """시계 작업 · 보고 예약을 보인다 — 작업 스케줄러에 묻고(`--dry-run` 이면 안 묻는다) 시계 작업 줄, 시계가 없고 옛 시각표만 있으면 옮겨 받으라는
    줄, 그 뒤 보고 예약 줄(`brief_status.describe`)을 찍는다."""
    done = None if args.dry_run else TB.ask(TB.query_command(T.TASK_NAME))
    task = None if done is None else done.code == 0
    for line in task_lines(done, TB.read_definition(done.out.strip()) if task else None):
        print(line)
    if task is False and legacy_only(home):
        print(LEGACY_HINT)
    for line in BST.describe(B.load_or_none(home), home, tm.utc_now(), task):
        print(line)
    return EXIT_OK


def legacy_only(home: pathlib.Path) -> bool:
    """옛 보고 시각표는 있는데 새 시각표가 없나 — 옮겨 받기를 아직 안 한 PC."""
    return (home / pathlib.Path(*C.LEGACY_SCHEDULE)).is_file() and not (home / C.SCHEDULE_FILE).exists()


def task_lines(done: TB.Answer | None, d: dict[str, str] | None) -> list[str]:
    """시계 작업의 줄 — 안 물었으면(`done` 이 None) 물을 명령, 없거나 못 읽었으면 그 답, 걸렸으면 정의(`d`)의 간격 · 켜짐 · 부르는 것."""
    if done is None:
        return [f"[예약 — 묻지 않고 보이기만 한다. 물으면: {shown(TB.query_command(T.TASK_NAME))}]"]
    if d is None:
        return [f"[예약 — 걸린 작업이 없다(또는 못 읽었다): {(done.out + done.err).strip()[-300:]}]"]
    return [f"[예약 — {T.TASK_LEAF} · 간격 {d['interval']} · 켜짐 {d['enabled']} · 한 번에 하나 {d['instances']}]",
            f"  부르는 것: {d['command']} {d['arguments']}"]


def cmd_unregister(args, home: pathlib.Path) -> int:
    """시계 작업을 지우고 보고 예약을 내린다 — 스캔 작업 · 쌓인 파일은 안 건드린다. 끄기를 청하셨으니 작업이 없어도 보고는 내린다."""
    if args.dry_run:
        print(f"[예약 — 끄지 않고 보이기만 한다. 끄면: {shown(TB.delete_command(T.TASK_NAME))} · 보고 예약도 내린다]")
        return EXIT_OK
    brief = " · 보고 예약도 내렸다" if S.clear(home) else ""
    done = TB.ask(TB.delete_command(T.TASK_NAME))
    if done.code != 0:
        print(f"[예약 — 못 껐다(걸린 작업이 없을 수 있다){brief}: {(done.out + done.err).strip()[-300:]}]")
        return EXIT_STOPPED
    print(f"[예약 — {T.TASK_LEAF} 시계를 껐다{brief}. 스캔 작업은 그대로다]")
    return EXIT_OK


def cmd_adopt(args, home: pathlib.Path) -> int:
    """이미 스캔을 건 PC 를 옮겨 받는다 — 곁의 스캔이 건 작업이 이 홈의 스캔을 부를 때만, 옛 파일을 옮겨 받고(`take_over`) 시계가 없을 때만
    건다(손 · 주기는 스캔의 답에서, 시각 · claude 는 옮겨 받은 시각표에서). 여러 번 불러도 같다. 끝 줄 하나. 종료 값 — 0(건너뛴 갈래 전부) ·
    1 작업 스케줄러가 거절했다."""
    task = scan_task()
    skipped = adopt_skip(task)
    if skipped:
        print(ADOPT_SKIPPED[skipped])
        return EXIT_OK
    moved = TO.take_over(home)
    if TB.ask(TB.query_command(T.TASK_NAME)).code == 0:
        print(ADOPT_SKIPPED["present"])
        return EXIT_OK
    hand, missing = D.mail_hand(task.get("hand"))
    if hand is None:
        print(f"[시계 — 못 걸었다: {missing}]")
        return EXIT_STOPPED
    path = home / C.CLOCK_XML_FILE
    TB.write_xml(path, T.task_xml(every=task.get("every_min") or EVERY_FALLBACK_MIN, home=home, hand=hand))
    if not put_task(path):
        return EXIT_STOPPED
    print(ADOPTED if C.SCHEDULE_FILE in moved or (home / C.SCHEDULE_FILE).exists() else ADOPTED_FRESH)
    return EXIT_OK


def adopt_skip(task: dict[str, Any]) -> str:
    """옮겨 받기를 건너뛸 까닭 — "unregistered" 스캔이 안 걸렸다 · "elsewhere" 걸린 작업이 이 홈의 스캔을 안 부른다 · "" 옮겨 받는다."""
    if task.get("registered") is not True:
        return "unregistered"
    return "" if task.get("calls_this_scan") is True else "elsewhere"
