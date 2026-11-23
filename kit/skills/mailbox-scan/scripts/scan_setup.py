"""걸기 · 보기 · 끄기 — `scan.py register · status · unregister` 의 손. 작업 스케줄러의 작업 하나(`scan_task`)를 걸고 · 보이고 · 지운다.
판의 코드는 안 부른다.

    cmd_register(args) · cmd_status(args) · cmd_unregister(args)   # 종료 값 — 0 됐다 · 1 멈췄다(끝 줄이 다음 걸음을 말한다)

`status --json` 의 JSON 한 줄은 다른 프로그램이 읽는다 — 칸의 이름과 뜻은 `references/DESIGN.md` 「status --json · run --wait」 표가 든다.
"""

from __future__ import annotations

import json
import os
import pathlib

import scan_const as C
import scan_hand as H
import scan_store as st
import scan_time as tm
import scan_words as SW
import scan_task as T
import task_base as TB
from task_base import shown

EXIT_OK, EXIT_STOPPED = 0, 1


# ── 걸기 ────────────────────────────────────────────────────────────────────────

def cmd_register(args) -> int:
    """스캔을 작업 스케줄러에 건다 — 손을 확인하고, 작업 정의를 지어(보이기만 · 받나만 묻기도) 건다."""
    hand, refused = usable_hand(args.hand)
    if refused:
        print(f"[예약 — 걸지 않았다: {refused}]")
        return EXIT_STOPPED
    xml = T.task_xml(every=args.every, full_every=args.full_every, hand=hand, scan_py=C.SCAN_PY)
    path = st.scan_dir() / C.TASK_XML_FILE
    if TB.windowless_python().name.lower() != "pythonw.exe":
        print("[예약 — ⚠ 창 없는 파이썬(pythonw.exe)을 못 찾아 판마다 창이 뜬다]")
    if args.dry_run:
        show_register_plan(args, path, xml)
        return EXIT_OK
    TB.write_xml(path, xml)
    if args.validate:
        return validate_task(path)
    done = TB.ask(TB.register_command(T.TASK_NAME, path))
    if done.code != 0:
        print(f"[예약 — 작업 스케줄러가 거절했다: {(done.out + done.err).strip()[-400:]}]")
        return EXIT_STOPPED
    print(f"[예약 — {T.TASK_NAME} 을 걸었다: {args.every}분마다 · 메일함 전체는 {args.full_every}분마다 · 앞 판이 돌면 그 주기는 건너뛴다]")
    return EXIT_OK


def usable_hand(given: str | None) -> tuple[pathlib.Path | None, str]:
    """작업에 굳힐 회사 메일 손 — 찾고, 「list --since」 가 있는 판인가를 묻는다. 내는 것 — (손, "") 이나 (None, 거절의 말)."""
    try:
        hand = H.find_hand(given)
    except H.HandMissing as exc:
        return None, f"{exc}. 다음: {C.NEXT_HAND_MISSING}"
    if not H.has_since(hand):
        return None, f"회사 메일 손이 「list --since」 없는 옛 판이다({hand}). 다음: {C.NEXT_HAND_OLD}"
    return hand, ""


def validate_task(path: pathlib.Path) -> int:
    """작업 스케줄러가 지은 정의를 받나만 묻는다(등록 안 함) — 받으면 0, 거절하면 그 말과 1."""
    done = TB.ask(TB.validate_command(T.VALIDATE_ENV), env=TB.validate_env(T.VALIDATE_ENV, path))
    ok = TB.accepted(done)
    print(f"[예약 — 작업 스케줄러가 정의를 {'받는다' if ok else '거절했다'}(등록 안 함): {path}]")
    if not ok:
        print(done.err.strip()[-600:])
    return EXIT_OK if ok else EXIT_STOPPED


def show_register_plan(args, path: pathlib.Path, xml: str) -> None:
    """걸지 않고 보이기(`--dry-run`) — 걸면 무엇을 얼마마다 읽나 · 작업 스케줄러에 거는 명령 · 작업 정의."""
    print(f"[예약 — 걸지 않고 보이기만 한다. 걸면 새 메일을 {args.every}분마다 · 메일함 전체를 {args.full_every}분마다 읽는다(앞 판이 돌면 "
          f"그 주기는 건너뛴다): {shown(TB.register_command(T.TASK_NAME, path))}]")
    print(xml)


# ── 보기 · 끄기 ──────────────────────────────────────────────────────────────────

def cmd_status(args) -> int:
    """걸린 작업 · 마지막 판을 보인다 — 작업 스케줄러에 묻고(`--dry-run` 이면 안 묻는다) 지금 모습을 읽은 뒤 그 줄들을 찍는다.
    `--json` 이면 사람의 줄 대신 프로그램이 읽는 한 줄을 낸다(`status_json`)."""
    if args.json:
        return status_json(args)
    done, _, d = asked_task(args.dry_run)
    for line in task_lines(done, d):
        print(line)
    state, unread_said = read_state()
    for line in last_run_lines(state, unread_said):
        print(line)
    return EXIT_OK


def status_json(args) -> int:
    """걸린 작업 · 마지막 판을 프로그램이 읽는 JSON 한 줄로 낸다(`status --json`) — 작업 스케줄러에 묻고(`--dry-run` 이면 안 묻는다) 지금
    모습을 읽어 칸을 짓는다. 종료 값은 늘 0 — 모르는 칸은 null 이다."""
    done, task, d = asked_task(args.dry_run)
    state, _ = read_state()
    print(json.dumps(status_record(task, d, state), ensure_ascii=False))
    return EXIT_OK


def asked_task(dry_run: bool) -> tuple[TB.Answer | None, bool | None, dict[str, str] | None]:
    """작업 스케줄러에 걸린 작업을 묻는다 — (답 · 안 물었으면 None, 걸렸나 · 안 물었으면 None, 걸렸으면 그 정의). 사람의 줄과 JSON 이 이 한
    자리로 가른다."""
    done = None if dry_run else TB.ask(TB.query_command(T.TASK_NAME))
    task = None if done is None else done.code == 0
    return done, task, TB.read_definition(done.out.strip()) if task else None


def status_record(task: bool | None, d: dict[str, str] | None, state: dict[str, object] | None) -> dict[str, object]:
    """`status --json` 의 한 장 — 꼴 번호 · 사용자 폴더 · 스캔 자리 · 걸린 작업 · 마지막 판."""
    return {"format": C.STATUS_FORMAT, "home": str(st.home()), "folder": str(st.scan_dir()), "task": task_record(task, d),
            "last_run": last_run_record(state)}


def task_record(task: bool | None, d: dict[str, str] | None) -> dict[str, object]:
    """걸린 작업의 칸 — 걸렸나(안 물었으면 null) · 걸렸으면 주기(분) · 손 · 부르는 프로그램과 인자 그대로 · 이 스캔의 입구를 부르나. 인자가
    거는 꼴이 아니면(손으로 고쳤다) 거기서 읽는 칸은 null 이다."""
    record: dict[str, object] = {"registered": task, "every_min": None, "hand": None, "command": None, "arguments": None,
                                 "calls_this_scan": None}
    if d is None:
        return record
    parts = T.arguments_parts(d["arguments"])
    record.update(every_min=T.interval_minutes(d["interval"]), command=d["command"], arguments=d["arguments"])
    if parts is not None:
        record.update(hand=parts["hand"], calls_this_scan=same_path(parts["scan_py"], C.SCAN_PY))
    return record


def same_path(a: str | pathlib.Path, b: str | pathlib.Path) -> bool:
    """두 경로가 같은 자리인가 — 윈도의 대소문자 · 사이 글자(`/` · `\\`) · `..` 를 고른 뒤 견준다."""
    return os.path.normcase(os.path.normpath(str(a))) == os.path.normcase(os.path.normpath(str(b)))


def last_run_record(state: dict[str, object] | None) -> dict[str, object] | None:
    """마지막 판의 칸 — 시작 · 끝(UTC ISO 8601) · 끝 낱말 · 그 판의 사내 세션 답(`RUN_SESSION_ANSWER` — 판 맺기와 같은 표). 판이 없거나 지금
    모습을 못 읽었으면 None."""
    last = (state or {}).get("last_run")
    if not last:
        return None
    return {"started": last.get("started"), "ended": last.get("ended"), "outcome": last.get("outcome"),
            "session": C.RUN_SESSION_ANSWER.get(last.get("outcome"))}


def read_state() -> tuple[dict[str, object] | None, str]:
    """지금 모습 — (읽은 것 · 없으면 None, 못 읽었으면 그 말)."""
    try:
        state, _ = st.load_state(st.scan_dir())
        return state, ""
    except st.Unreadable as exc:
        return None, f"  ⚠ {exc} — 지금 모습을 못 보였다. 다시 물으면 읽는다"


def task_lines(done: TB.Answer | None, d: dict[str, str] | None) -> list[str]:
    """걸린 작업의 줄 — 안 물었으면(`done` 이 None) 물을 명령, 없거나 못 읽었으면 그 답, 걸렸으면 정의(`d`)의 간격 · 켜짐 · 부르는 것."""
    if done is None:
        return [f"[예약 — 묻지 않고 보이기만 한다. 물으면: {shown(TB.query_command(T.TASK_NAME))}]"]
    if d is None:
        return [f"[예약 — 걸린 작업이 없다(또는 못 읽었다): {(done.out + done.err).strip()[-300:]}]"]
    return [f"[예약 — {T.TASK_NAME} · 간격 {d['interval']} · 켜짐 {d['enabled']} · 한 번에 하나 {d['instances']}]",
            f"  부르는 것: {d['command']} {d['arguments']}"]


def last_run_lines(state: dict[str, object] | None, unread_said: str) -> list[str]:
    """마지막 판의 줄 — 판의 때 · 갈래 · 끝, 판이 없으면 못 읽은 말이나 「스캔한 적이 없다」."""
    last = (state or {}).get("last_run")
    if last:
        return [f"  마지막 판: {tm.seoul(tm.parse(last.get('started')))} · {SW.MODE_WORDS.get(last.get('mode'), '')} · "
                f"{SW.OUTCOME_WORDS.get(last.get('outcome'), last.get('outcome'))}"]
    return [unread_said or "  스캔한 적이 없다 — 스캔 파일이 없다"]


def cmd_unregister(args) -> int:
    """작업을 지운다 — 쌓인 스캔 파일은 그대로다. 정한 시각의 보고는 일일 보고의 시계가 들어 여기서 안 내린다."""
    if args.dry_run:
        print(f"[예약 — 끄지 않고 보이기만 한다. 끄면: {shown(TB.delete_command(T.TASK_NAME))}]")
        return EXIT_OK
    done = TB.ask(TB.delete_command(T.TASK_NAME))
    if done.code != 0:
        print(f"[예약 — 못 껐다(걸린 작업이 없을 수 있다): {(done.out + done.err).strip()[-300:]}]")
        return EXIT_STOPPED
    print(f"[예약 — {T.TASK_NAME} 을 껐다. 쌓인 스캔 파일은 그대로다]")
    return EXIT_OK
