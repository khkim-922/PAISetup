"""보기 · 끄기 · 거두기 — `scan.py status · unregister · adopt` 의 손(`register` 는 거절만 한다). 메일함 스캔은 작업 스케줄러에 걸지 않는다 —
메일함은 일일 보고의 시계가 보고 시각에 청한 판과 대화의 판에서만 읽는다. 옛 판이 건 작업(`scan_task.TASK_NAME`)은 보이고 · 지우고 · 설치가
거둔다. 판의 코드는 안 부른다.

    cmd_register(args) · cmd_status(args) · cmd_unregister(args) · cmd_adopt(args)   # 종료 값 — 0 됐다 · 1 멈췄다(끝 줄이 다음 걸음을 말한다)

`status --json` 의 JSON 한 줄은 다른 프로그램이 읽는다 — 칸의 이름과 뜻은 `references/DESIGN.md` 「status --json · run --wait」 표가 든다.
`adopt` 의 끝 줄 하나와 종료 값은 설치가 읽는다 — 원본은 같은 문서 「옛 예약 거두기 — adopt」 표다.
"""

from __future__ import annotations

import json

import scan_const as C
import scan_store as st
import scan_time as tm
import scan_words as SW
import scan_task as T
import task_base as TB
from task_base import shown

EXIT_OK, EXIT_STOPPED = 0, 1
RETIRED = "메일함 스캔은 몇 분마다 걸지 않는다 — 메일함은 보고 시각과 대화에서 보고를 청하실 때 읽는다. 지금 한 판은 scan.py run --now"
ADOPT_NONE = "[예약 — 거둘 것이 없다: 메일함 스캔 예약이 안 걸려 있다]"
ADOPT_DONE = "[예약 — 메일함 스캔 예약을 거뒀다: 메일함은 보고 시각과 대화에서만 읽는다 · 쌓인 스캔 파일은 그대로다]"
ADOPT_FAILED = "[예약 — 메일함 스캔 예약을 못 거뒀다: {why}]"


def cmd_register(args) -> int:
    """거절한다 — 스캔은 작업 스케줄러에 걸지 않는다. 옛 안내 · 옛 손이 부르면 그 까닭과 지금 한 판의 길을 말한다."""
    print(f"[예약 — 걸지 않았다: {RETIRED}]")
    return EXIT_STOPPED


# ── 보기 · 끄기 ──────────────────────────────────────────────────────────────────

def cmd_status(args) -> int:
    """옛 판이 건 작업이 남았나 · 마지막 판을 보인다 — 작업 스케줄러에 묻고(`--dry-run` 이면 안 묻는다) 지금 모습을 읽은 뒤 그 줄들을 찍는다.
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
    record.update(every_min=TB.interval_minutes(d["interval"]), command=d["command"], arguments=d["arguments"])
    if parts is not None:
        record.update(hand=parts["hand"], calls_this_scan=TB.same_path(parts["scan_py"], C.SCAN_PY))
    return record


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
        return ["[예약 — 스캔 예약은 없다 · 메일함은 보고 시각과 대화에서 읽는다]"]
    return [f"[예약 — 옛 판이 건 스캔 예약이 남아 있다({T.TASK_NAME} · 간격 {d['interval']} · 켜짐 {d['enabled']}). 다음: scan.py adopt 로 거둔다]",
            f"  부르는 것: {d['command']} {d['arguments']}"]


def last_run_lines(state: dict[str, object] | None, unread_said: str) -> list[str]:
    """마지막 판의 줄 — 판의 때 · 갈래 · 끝, 판이 없으면 못 읽은 말이나 「스캔한 적이 없다」."""
    last = (state or {}).get("last_run")
    if last:
        return [f"  마지막 판: {tm.seoul(tm.parse(last.get('started')))} · {SW.MODE_WORDS.get(last.get('mode'), '')} · "
                f"{SW.OUTCOME_WORDS.get(last.get('outcome'), last.get('outcome'))}"]
    return [unread_said or "  스캔한 적이 없다 — 스캔 파일이 없다"]


def cmd_unregister(args) -> int:
    """옛 판이 건 작업을 지운다 — 쌓인 스캔 파일은 그대로다. 정한 시각의 보고는 일일 보고의 시계가 들어 여기서 안 내린다."""
    if args.dry_run:
        print(f"[예약 — 끄지 않고 보이기만 한다. 끄면: {shown(TB.delete_command(T.TASK_NAME))}]")
        return EXIT_OK
    done = TB.ask(TB.delete_command(T.TASK_NAME))
    if done.code != 0:
        print(f"[예약 — 못 껐다(걸린 작업이 없을 수 있다): {(done.out + done.err).strip()[-300:]}]")
        return EXIT_STOPPED
    print(f"[예약 — {T.TASK_NAME} 을 껐다. 쌓인 스캔 파일은 그대로다]")
    return EXIT_OK


# ── 옛 예약 거두기 ──────────────────────────────────────────────────────────────────

def cmd_adopt(args) -> int:
    """옛 판이 건 스캔 작업을 거둔다(`adopt` — 설치가 업데이트 때 부른다) — 걸려 있으면 어느 홈을 부르든 · 손으로 고쳤든 지우고, 그 작업의 정의
    사본(`TASK_XML_FILE`)도 걷는다. 쌓인 스캔 파일은 그대로다. 여러 번 불러도 같다. 끝 줄 하나. 종료 값 — 0 안 걸렸다 · 거뒀다 · 1 못 지웠다."""
    if TB.ask(TB.query_command(T.TASK_NAME)).code != 0:
        print(ADOPT_NONE)
        return EXIT_OK
    done = TB.ask(TB.delete_command(T.TASK_NAME))
    if done.code != 0:
        print(ADOPT_FAILED.format(why=(done.out + done.err).strip()[-300:]))
        return EXIT_STOPPED
    (st.scan_dir() / C.TASK_XML_FILE).unlink(missing_ok=True)
    print(ADOPT_DONE)
    return EXIT_OK
