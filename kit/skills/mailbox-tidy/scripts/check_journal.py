"""메일함 정리 스킬의 기록이 메일마다 원래 자리를 적고, 보여 드린 안과 다른 미리 보기는 안 잡나를 문다.

    python -X utf8 -I check_journal.py [스크립트 폴더] [--teeth]

층 — 쓰는 사람의 계약. 곁의 `journal.py` 를 명령 그대로 부르고, 회사 메일 스킬은 부르지 않는다 — 그 손이 낸 글의 꼴을 표본으로 준다.
남기는 까닭 — 판정마다 check-design 1 절의 넷을 다 지난다(판정별 표 · 표본의 꼴은 `references/DESIGN.md` 「검사가 남는 까닭」).
언제 걷나 — 기록이 스킬에서 빠지거나, 회사 메일 스킬이 메일마다의 자리를 제 출력에 들어 기록이 걷힐 때.
여기서 못 재는 것 — 회사 메일 스킬의 꼴이 바뀌었나 · 대화의 모델이 미리 보기 · 실행을 기록에 흘려 보내나(같은 문서).

물림 — `--teeth` 는 계약 판정에 이어 판정마다 그 판정이 지키는 한 줄을 끈 사본에서 빨강을 본다. 계약 판정이 하나라도 빨가면 안 돌린다 —
늘 지는 판 앞에서는 모든 사본이 「잡혔다」로 센다. 사본을 못 심으면 그 물림이 빨갛다. 푸시 문은 인자 없이 불러 계약 판정만 돈다.

폴더를 안 주면 이 파일이 든 폴더만 읽는다 — 푸시 문(`skill-checks`)은 `.claude/skills` 만 임시 자리로 내보내 거기서 돌린다.
기대값은 표본을 지은 뜻과 「같다」의 계약에서 낸다 — 스크립트를 돌린 값에서 거꾸로 내지 않는다.
종료 값 — 끝 줄이 「통과 N/N」이면 0, 하나라도 어긋나면 1, 스크립트를 못 찾거나 못 돌렸으면 2.
"""

from __future__ import annotations

import ast
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import traceback

# ── 판정 손 — 씨앗 `_verdict.py` 의 일부를 줄여 둔 것(까닭은 `references/DESIGN.md`) ─────────────────────

# 한글 Windows 는 stdout 을 cp949 · strict 로 잡아, 판정 기호를 찍다 리디렉션 · 파이프에서만 죽는다 — `-X utf8` 없이 불려도 안 죽게 다시 잡는다
sys.stdout.reconfigure(encoding="utf-8")

EXIT_OK, EXIT_MISMATCH, EXIT_UNMEASURED = 0, 1, 2   # 쟀고 맞다 · 어긋났다 · 못 쟀다(초록이 아니다)
FAILS: list[str] = []
PASSES: list[str] = []


class Unmeasured(SystemExit):
    """「못 쟀다」로 그 자리에서 나간다 — 까닭을 stdout 에 찍고 2 로. `raise SystemExit("글자")` 는 1 로 나가 훅이 「어긋났다」로 읽는다."""

    def __init__(self, why):
        super().__init__(EXIT_UNMEASURED)
        self.why = str(why)
        print(self.why)

    def __str__(self):
        return self.why


def report(name, ok, detail=()):
    """계약 판정 한 줄 — 상세(줄들)는 실패에만 찍는다."""
    (PASSES if ok else FAILS).append(name)
    print(f"[{'OK ' if ok else 'NG '}] {name}")
    for row in detail if not ok else ():
        print(f"       {row}")


def edge(text):
    """통과할 때도 보여야 하는 경계 — 판정이 아니라 범위의 고지라 계수에 안 든다."""
    print(f"  ⚠ {text}")


HERE = pathlib.Path(__file__).resolve().parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
WITH_TEETH = "--teeth" in sys.argv[1:]          # 물림까지 — 정기 판의 몫(머리말 「물림」)
SCRIPTS = pathlib.Path(ARGS[0]).resolve() if ARGS else HERE
TIMEOUT_S = 30

# ── 표본 — 회사 메일 스킬이 찍는 꼴 그대로(가상의 회사 · 사람) ─────────────────────────────

U_INBOX, U_TOP, U_CHILD = "0000000000000000A1B2C3D4E5F60007", "0000000000000000A1B2C3D4E5F60012", "0000000000000000A1B2C3D4E5F60013"
TOP, CHILD, TARGET = "협력사", "프로젝트\\배터리 소재", "회의.2026"
MOVE_SUBJECTS = ("지난달 메일", "협력사 납기 확인 요청", "소재 시험 결과 공유")
MOVE_SENDER_ADDR = "sm.ha@haneul-parts.example"
PREVIEW_MOVE = f"""옮길 메일 3통 → {TARGET} — 아직 안 옮겼다(읽음 표시는 그대로 남는다)
  안읽음 · {MOVE_SUBJECTS[0]} · 윤가람 <gr.yoon@gaon.example> · 받은편지함 · {U_INBOX}
  안읽음 · {MOVE_SUBJECTS[1]} · {MOVE_SENDER_ADDR} · 폴더 {TOP} · {U_TOP}
  안읽음 · {MOVE_SUBJECTS[2]} · 윤가람 <gr.yoon@gaon.example> · 폴더 {CHILD} · {U_CHILD}
확인 열쇠: b05553a7bf04
사람이 이 목록 그대로 옮기자고 하면 같은 인자에 apply-move · --confirm <열쇠> 로 옮긴다.
"""
APPLY_MOVE = f"옮겼다: 3통 → {TARGET} (다시 봐서 다 들었다) · 열쇠 b05553a7bf04\n"
APPLY_STALE = "확인 열쇠가 지금 메일 자리와 다르다 — 옮기지 않았다. preview-move 로 다시 보이고 확인받는다\n"
U_READ, U_COMMA, COMMA = "0000000000000000A1B2C3D4E5F60008", "0000000000000000A1B2C3D4E5F60014", "소식\\공지, 안내"
PREVIEW_TRASH = f"""휴지통으로 보낼 메일 2통 — 아직 안 보냈다(읽음 표시는 그대로 남고, preview-restore 로 되살릴 수 있다)
  읽음 · 이미 읽은 메일 · 윤가람 <gr.yoon@gaon.example> · 받은편지함 · {U_READ}
  안읽음 · [안내] 사내 행사 일정 · notice@gaon.example · 폴더 {COMMA} · {U_COMMA}
확인 열쇠: 66b5ebacb4c1
사람이 이 목록 그대로 지우자고 하면 같은 인자에 apply-trash · --confirm <열쇠> 로 휴지통에 보낸다.
"""
APPLY_TRASH = "휴지통으로 보냈다: 2통 (다시 봐서 다 들었다) — 되살리려면 preview-restore · 열쇠 66b5ebacb4c1\n"
RULE_UNID = "5AAD4C9DABA1EF0CBC08A923CC4B0601"
PREVIEW_RULE = """규칙 넣기: 받은 메일 · 보낸 사람∋sm.ha@haneul-parts.example · 폴더로 옮김 → 협력사
— 아직 안 바꿨다. 규칙은 서버가 곧바로 새 메일에 쓴다 · 이미 받은 메일은 안 옮긴다 · 자동전달 칸은 늘 빈다
확인 열쇠: 457c823eac76
사람이 이대로 하자고 하면 같은 인자에 apply-rule · --confirm <열쇠> 로 바꾼다.
"""
APPLY_RULE = f"규칙을 넣었다: 받은 메일 · 보낸 사람∋sm.ha@haneul-parts.example · 폴더로 옮김 → 협력사 · {RULE_UNID}\n"
# 되돌리는 미리 보기 — 기록 1 의 받은편지함 메일을 받은편지함으로(사용자가 안 하기로 하신 판)
PREVIEW_BACK = f"""옮길 메일 1통 → 받은편지함 — 아직 안 옮겼다(읽음 표시는 그대로 남는다)
  안읽음 · {MOVE_SUBJECTS[0]} · 윤가람 <gr.yoon@gaon.example> · 폴더 {TARGET} · {U_INBOX}
확인 열쇠: 0123456789ab
사람이 이 목록 그대로 옮기자고 하면 같은 인자에 apply-move · --confirm <열쇠> 로 옮긴다.
"""
# 다른 바꿈 — 한 통을 「보관」으로. 그 실행이 아닌 실행(위 APPLY_MOVE · 3통 → 회의.2026)을 이 바꿈에 주는 판
PREVIEW_ONE = f"""옮길 메일 1통 → 보관 — 아직 안 옮겼다(읽음 표시는 그대로 남는다)
  읽음 · 이미 읽은 메일 · 윤가람 <gr.yoon@gaon.example> · 폴더 {COMMA} · {U_COMMA}
확인 열쇠: 0123456789ab
사람이 이 목록 그대로 옮기자고 하면 같은 인자에 apply-move · --confirm <열쇠> 로 옮긴다.
"""
PREVIEW_FOLDER = f"폴더 만들기: {TARGET} — 아직 안 바꿨다\n확인 열쇠: 0123456789ab\n사람이 이대로 하자고 하면 같은 인자에 apply-folder · --confirm <열쇠> 로 바꾼다.\n"
APPLY_OTHER_FOLDER = "만들었다: 보관 (다시 봐서 섰다)\n"

LOG_FILE, HELD_FILE = "mailbox-tidy-log.jsonl", "mailbox-tidy-held.json"


# ── 부르는 손 ─────────────────────────────────────────────────────────────────

def run(scripts: pathlib.Path, script: str, args: list[str], home: pathlib.Path, stdin: str | bytes = "") -> tuple[int, str]:
    """스크립트 하나를 명령 그대로 부른다 — (종료 값, 표준 출력과 오류)."""
    data = stdin.encode("utf-8") if isinstance(stdin, str) else stdin
    env = {**os.environ, "MAIL_SECRETARY_HOME": str(home), "PYTHONIOENCODING": "utf-8"}
    try:
        got = subprocess.run([sys.executable, "-X", "utf8", "-I", "-B", str(scripts / script), *args], input=data, capture_output=True,
                             env=env, timeout=TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unmeasured(f"[안 잼] {script} 를 못 돌렸다 — {type(exc).__name__}") from exc
    return got.returncode, got.stdout.decode("utf-8", "replace") + got.stderr.decode("utf-8", "replace")


def log_rows(home: pathlib.Path) -> list[dict]:
    path = home / LOG_FILE
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.exists() else []


class Home:
    """판마다 새 사용자 폴더 — 앞 판이 세운 기록을 물려받지 않는다."""

    def __enter__(self) -> pathlib.Path:
        self._tmp = tempfile.TemporaryDirectory()
        return pathlib.Path(self._tmp.name) / "home"

    def __exit__(self, *exc) -> None:
        self._tmp.cleanup()


# ── 기록 — 원래 자리 ───────────────────────────────────────────────────────────

MOVE_ARGS = ["hold", "move", "--to", TARGET, U_INBOX, U_TOP, U_CHILD]
MOVE_WANT = [{"unid": U_INBOX, "place": "inbox", "folder": ""}, {"unid": U_TOP, "place": "folder", "folder": TOP},
             {"unid": U_CHILD, "place": "folder", "folder": CHILD}]


def records_each_origin(scripts: pathlib.Path) -> tuple[bool, list[dict]]:
    """옮기기를 잡고 맺으면 메일마다 제 줄이 말한 자리가 그 번호에 적힌다 — 물림이 이 판정을 다시 부른다."""
    with Home() as home:
        held, _ = run(scripts, "journal.py", MOVE_ARGS, home, PREVIEW_MOVE)
        done, _ = run(scripts, "journal.py", ["done"], home, APPLY_MOVE)
        rows = log_rows(home)
    ok = held == 0 and done == 0 and len(rows) == 1 and rows[0].get("mails") == MOVE_WANT and rows[0].get("to") == TARGET \
        and rows[0].get("outcome") == "done"
    return ok, rows


def shows_unsettled(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """맺지 못한 바꿈이 log · undo 에 다음 번호의 「결과 모름」으로 서고, 다음 바꿈을 잡으면 그 번호로 적힌다."""
    with Home() as home:
        run(scripts, "journal.py", MOVE_ARGS, home, PREVIEW_MOVE)
        code, log = run(scripts, "journal.py", ["log"], home)
        code2, undo = run(scripts, "journal.py", ["undo", "1"], home)
        run(scripts, "journal.py", ["hold", "rule-add"], home, PREVIEW_RULE)
        rows = log_rows(home)
    ok = (code == 0 and "[기록 1]" in log and "결과 모름" in log and code2 == 0 and all(u in undo for u in (U_INBOX, U_TOP, U_CHILD))
          and len(rows) == 1 and rows[0].get("id") == 1 and rows[0].get("outcome") == "unknown" and rows[0].get("mails") == MOVE_WANT)
    return ok, [log[-300:], undo[-300:], json.dumps(rows, ensure_ascii=False)[:300]]


def releases_declined(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """안 하기로 한 미리 보기는 drop 으로 기록 없이 놓이고, 놓지 않은 채 다음 바꿈에 밀려 「결과 모름」이 된 되돌림은 「되돌렸다」로 세지 않는다."""
    with Home() as home:
        run(scripts, "journal.py", MOVE_ARGS, home, PREVIEW_MOVE)
        code, dropped = run(scripts, "journal.py", ["drop"], home)
        released = code == 0 and not (home / HELD_FILE).exists() and not log_rows(home)
        run(scripts, "journal.py", MOVE_ARGS, home, PREVIEW_MOVE)
        run(scripts, "journal.py", ["done"], home, APPLY_MOVE)                                         # 기록 1
        run(scripts, "journal.py", ["hold", "move", "--inbox", "--undoes", "1", U_INBOX], home, PREVIEW_BACK)
        run(scripts, "journal.py", ["hold", "rule-add"], home, PREVIEW_RULE)                           # 앞의 되돌림이 기록 2(결과 모름)로
        _, undo = run(scripts, "journal.py", ["undo", "1"], home)
        _, log = run(scripts, "journal.py", ["log"], home)
    ok = released and "되돌린 기록이 이미 있다" not in undo and "(2)" in undo and "2(되돌림)" not in log
    return ok, [dropped[-200:], undo[-400:], log[-400:]]


def refuses_other_apply(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """실행의 「됐다」 줄이 잡아 둔 바꿈과 수 · 받을 자리 · 폴더가 다르면 적지 않고 1 로 멈추며, 잡아 둔 것은 그대로 남는다."""
    with Home() as home:
        run(scripts, "journal.py", ["hold", "move", "--to", "보관", U_COMMA], home, PREVIEW_ONE)
        code, out = run(scripts, "journal.py", ["done"], home, APPLY_MOVE)
        moved = code == 1 and not log_rows(home) and (home / HELD_FILE).exists()
    with Home() as home:
        run(scripts, "journal.py", ["hold", "folder-create"], home, PREVIEW_FOLDER)
        code2, out2 = run(scripts, "journal.py", ["done"], home, APPLY_OTHER_FOLDER)
        made = code2 == 1 and not log_rows(home) and (home / HELD_FILE).exists()
    return moved and made, [out[-300:], out2[-300:]]


APPLY_BACK = "옮겼다: 1통 → 받은편지함 (다시 봐서 다 들었다) · 열쇠 0123456789ab\n"


def shows_changed_mails(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """바꾼 메일 보기 — 기록마다 원래 자리 → 간 자리가 그 자리의 메일 번호만 묶어 서고, 뒤의 기록이 다시 바꾼 메일은 그 기록을 댄다."""
    with Home() as home:
        run(scripts, "journal.py", MOVE_ARGS, home, PREVIEW_MOVE)
        run(scripts, "journal.py", ["done"], home, APPLY_MOVE)                                         # 기록 1 — 세 자리에서 회의.2026 으로
        run(scripts, "journal.py", ["hold", "move", "--inbox", "--undoes", "1", U_INBOX], home, PREVIEW_BACK)
        run(scripts, "journal.py", ["done"], home, APPLY_BACK)                                         # 기록 2 — 기록 1 의 한 통을 되돌림
        run(scripts, "journal.py", ["hold", "rule-add"], home, PREVIEW_RULE)
        run(scripts, "journal.py", ["done"], home, APPLY_RULE)                                         # 기록 3 — 메일을 안 건드린 바꿈
        code, out = run(scripts, "journal.py", ["mails"], home)
    first, block = False, []
    for line in out.splitlines():
        if line.startswith("[기록 "):
            first = line.startswith("[기록 1]")
        if first:
            block.append(line)

    def only(line: str, unid: str) -> bool:
        return unid in line and sum(u in line for u in (U_INBOX, U_TOP, U_CHILD)) == 1

    groups = (any(only(x, U_INBOX) and "받은편지함" in x and TARGET in x for x in block)
              and any(only(x, U_CHILD) and f"「{CHILD}」" in x and TARGET in x for x in block)
              and any(only(x, U_TOP) and f"「{TOP}」" in x and TARGET in x for x in block))
    later = any(only(x, U_INBOX) and "기록 2" in x for x in block)
    return code == 0 and groups and later, [out[-700:]]


# 보여 드린 안 — 안의 조각 둘(위 옮기기 · 아직 없는 폴더 「보관」으로 옮길 두 통)과 실행 직전에 다시 받은 미리 보기
KEEP = "보관"
PREVIEW_TO_KEEP = f"""옮길 메일 2통 → {KEEP} — 아직 안 옮겼다(읽음 표시는 그대로 남는다)
  읽음 · 이미 읽은 메일 · 윤가람 <gr.yoon@gaon.example> · 받은편지함 · {U_READ}
  안읽음 · [안내] 사내 행사 일정 · notice@gaon.example · 폴더 {COMMA} · {U_COMMA}
확인 열쇠: 0123456789ab
사람이 이 목록 그대로 옮기자고 하면 같은 인자에 apply-move · --confirm <열쇠> 로 옮긴다.
"""
# 보인 뒤 한 자리씩 달라진 미리 보기 — (이름, 받을 자리, 메일 번호, 미리 보기, 다른 점에 서야 할 말)
SHOWN_DRIFTS = [
    ("그 사이 사용자가 한 통을 다른 폴더로 옮겼다", TARGET, [U_INBOX, U_TOP, U_CHILD],
     PREVIEW_MOVE.replace(f" · 폴더 {TOP} · {U_TOP}", f" · 폴더 {KEEP} · {U_TOP}"), U_TOP),
    ("받을 자리가 보인 것과 다르다", KEEP, [U_INBOX, U_TOP, U_CHILD], PREVIEW_MOVE.replace(f"→ {TARGET} —", f"→ {KEEP} —"), KEEP),
    ("보인 메일 한 통이 빠졌다", TARGET, [U_INBOX, U_TOP],
     PREVIEW_MOVE.replace("옮길 메일 3통", "옮길 메일 2통").replace(PREVIEW_MOVE.splitlines()[3] + "\n", ""), U_CHILD),
]


def holds_only_as_shown(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """보여 드린 안 — show 가 조각을 적고, 실행 직전 미리 보기가 그 조각과 같을 때만(읽음은 안 본다) hold --shown 이 잡으며 다르면 1 로 멈춘다."""
    why: list[str] = []
    with Home() as home:
        code, out = run(scripts, "journal.py", ["show", "move", "--piece", "1", "--to", TARGET, U_INBOX, U_TOP, U_CHILD], home, PREVIEW_MOVE)
        items = [x for x in PREVIEW_MOVE.splitlines() if x.startswith("  ")]
        if code != 0 or not all(x in out.splitlines() for x in items) or (home / HELD_FILE).exists():
            why.append(f"show(조각 1): 종료 값 {code} · 메일 줄을 다 안 보였거나 바꿈을 잡았다 — {out[-300:]}")
        code, out = run(scripts, "journal.py", ["show", "move", "--piece", "2", "--to", KEEP, U_READ, U_COMMA], home, PREVIEW_TRASH)
        items = [x for x in PREVIEW_TRASH.splitlines() if x.startswith("  ")]
        if code != 0 or not all(x in out.splitlines() for x in items) or "휴지통으로 보낼" in out:
            why.append(f"show(조각 2 · 아직 없는 폴더): 휴지통 미리 보기의 메일 줄을 옮기기 조각으로 적고 보이지 않았다 — {out[-300:]}")
        for name, to, unids, text, word in SHOWN_DRIFTS:
            code, out = run(scripts, "journal.py", ["hold", "move", "--to", to, "--shown", "1", *unids], home, text)
            said = out.split("다른 점:", 1)[-1] if "다른 점:" in out else ""
            if code != 1 or (home / HELD_FILE).exists() or word not in said:
                why.append(f"{name}: 종료 값 {code} · 잡았나 {(home / HELD_FILE).exists()} — 다른 점에 「{word}」가 서야 한다: {out[-300:]}")
            (home / HELD_FILE).unlink(missing_ok=True)      # 틀리게 잡았어도 다음 경우는 빈 자리에서 잰다
        opened = PREVIEW_MOVE.replace(f"  안읽음 · {MOVE_SUBJECTS[0]}", f"  읽음 · {MOVE_SUBJECTS[0]}")
        code, out = run(scripts, "journal.py", ["hold", "move", "--to", TARGET, "--shown", "1", U_INBOX, U_TOP, U_CHILD], home, opened)
        if code != 0 or not (home / HELD_FILE).exists():
            why.append(f"읽음만 달라진 미리 보기를 보인 조각과 같게 잡지 않았다: 종료 값 {code} — {out[-300:]}")
        run(scripts, "journal.py", ["drop"], home)
        code, out = run(scripts, "journal.py", ["hold", "move", "--to", KEEP, "--shown", "2", U_READ, U_COMMA], home, PREVIEW_TO_KEEP)
        if code != 0 or not (home / HELD_FILE).exists():
            why.append(f"휴지통 미리 보기로 보인 조각을 그 폴더로 옮기는 같은 미리 보기에서 잡지 않았다: 종료 값 {code} — {out[-300:]}")
    return not why, why


def lists_shown(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """적어 둔 안 — shown 이 show 가 조각마다 보인 메일 줄을 조각 차례로 그대로 다시 내고, 안이 없으면 1 로 멈춘다."""
    why: list[str] = []
    with Home() as home:
        code, out = run(scripts, "journal.py", ["shown"], home)
        if code != 1:
            why.append(f"안이 없는데 종료 값 {code} — {out[-200:]}")
        run(scripts, "journal.py", ["show", "move", "--piece", "1", "--to", TARGET, U_INBOX, U_TOP, U_CHILD], home, PREVIEW_MOVE)
        run(scripts, "journal.py", ["show", "move", "--piece", "2", "--to", KEEP, U_READ, U_COMMA], home, PREVIEW_TRASH)
        code, out = run(scripts, "journal.py", ["shown"], home)
        lines = out.splitlines()
        one = [x for x in PREVIEW_MOVE.splitlines() if x.startswith("  ")]
        two = [x for x in PREVIEW_TRASH.splitlines() if x.startswith("  ")]
        heads = [i for i, x in enumerate(lines) if x.startswith("[조각 ")]
        at = {x: i for i, x in enumerate(lines)}
        in_order = (len(heads) == 2 and all(x in at for x in one + two)
                    and all(heads[0] < at[x] < heads[1] for x in one) and all(at[x] > heads[1] for x in two))
        if code != 0 or not in_order or (home / HELD_FILE).exists():
            why.append(f"두 조각의 메일 줄을 조각 차례로 다 안 냈거나 바꿈을 잡았다: 종료 값 {code} — {out[-400:]}")
        # 다음 차례(3)가 아닌 번호 — 다른 안의 옛 조각 번호를 그대로 준 꼴. 지금 안에 섞이지 않고 1 로 멈춘다
        code, out = run(scripts, "journal.py", ["show", "trash", "--piece", "2", U_READ, U_COMMA], home, PREVIEW_TRASH)
        _, after = run(scripts, "journal.py", ["shown"], home)
        if code != 1 or after.splitlines() != lines:
            why.append(f"지금 안의 다음 차례가 아닌 조각 번호를 받아 안을 바꿨다: 종료 값 {code} — {out[-300:]}")
    with Home() as home:
        code, out = run(scripts, "journal.py", ["show", "trash", "--piece", "2", U_READ, U_COMMA], home, PREVIEW_TRASH)
        _, after = run(scripts, "journal.py", ["shown"], home)
        if code != 1 or "[조각 " in after:
            why.append(f"안이 없는데 1 이 아닌 조각 번호로 안을 열었다: 종료 값 {code} — {out[-300:]}")
    return not why, why


# 안 바꾼 조각 — 무리 이름 · 까닭 한 줄(show --why)과 조각 밖에서 한 통만 「보관」으로 옮긴 실행
WHY = "행사 안내 · 지난 것"
APPLY_ONE = f"옮겼다: 1통 → {KEEP} (다시 봐서 다 들었다) · 열쇠 0123456789ab\n"
PLANS_FILE = "mailbox-tidy-plans.jsonl"


def keeps_unexecuted(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """안 바꾼 조각 — 다음 안의 1번 조각이 덮어도 plans 가 그 조각의 메일 번호를 보인 차례로 낸다. 보인 뒤 「됐다」로 맺은 기록이 바꾼 조각 ·
    메일은 빼고(조각 밖에서 따로 잡은 바꿈도), 보이기 전의 기록은 안 센다. 안들의 파일에는 메일의 제목 · 보낸 분이 없다."""
    why: list[str] = []
    with Home() as home:
        run(scripts, "journal.py", ["hold", "trash", U_READ, U_COMMA], home, PREVIEW_TRASH)
        run(scripts, "journal.py", ["done"], home, APPLY_TRASH)                # 기록 1 — 안을 보이기 전(그 뒤 웹메일에서 되살렸다)
        run(scripts, "journal.py", ["show", "move", "--piece", "1", "--to", TARGET, U_INBOX, U_TOP, U_CHILD], home, PREVIEW_MOVE)
        run(scripts, "journal.py", ["show", "move", "--piece", "2", "--why", WHY, "--to", KEEP, U_READ, U_COMMA], home, PREVIEW_TRASH)
        run(scripts, "journal.py", ["hold", "move", "--to", TARGET, "--shown", "1", U_INBOX, U_TOP, U_CHILD], home, PREVIEW_MOVE)
        run(scripts, "journal.py", ["done"], home, APPLY_MOVE)                 # 기록 2 — 조각 1 을 바꿨다
        run(scripts, "journal.py", ["hold", "move", "--to", KEEP, U_COMMA], home, PREVIEW_ONE)
        run(scripts, "journal.py", ["done"], home, APPLY_ONE)                  # 기록 3 — 조각 2 의 한 통을 조각 밖에서 바꿨다
        run(scripts, "journal.py", ["show", "folder-create", "--piece", "1"], home, PREVIEW_FOLDER)   # 새 안이 앞 안을 덮는다
        code, out = run(scripts, "journal.py", ["plans"], home)
        kept = (home / PLANS_FILE).read_text(encoding="utf-8") if (home / PLANS_FILE).exists() else ""
        held = (home / HELD_FILE).exists()
    blocks: dict[str, list[str]] = {}
    head = ""
    for line in out.splitlines():
        if line.startswith("[안 "):
            head = line.split("]", 1)[0] + "]"
        if head:
            blocks.setdefault(head, []).append(line)
    one, two = blocks.get("[안 1]", []), blocks.get("[안 2]", [])
    piece = [x for x in one if U_READ in x]
    if code != 0 or held:
        why.append(f"종료 값 {code} · 바꿈을 잡았나 {held} — {out[-300:]}")
    if len(piece) != 1 or WHY not in piece[0] or U_COMMA in piece[0]:
        why.append(f"덮인 안의 안 바꾼 조각이 남은 메일 번호(보이기 전 기록은 안 센다) · 까닭으로 서지 않았다 — {out[-500:]}")
    if not any("기록 3" in x and "1통" in x for x in one):
        why.append(f"조각 밖에서 바꾼 한 통을 뺀 기록을 대지 않았다 — {out[-500:]}")
    if any(u in out for u in (U_INBOX, U_TOP, U_CHILD)):
        why.append(f"바꾼 조각 1 의 메일 번호가 아직 서 있다 — {out[-500:]}")
    if not any("폴더 만들기" in x and TARGET in x for x in two):
        why.append(f"지금 안(안 2)의 조각이 안 섰다 — {out[-500:]}")
    leaked = [s for s in (*MOVE_SUBJECTS, MOVE_SENDER_ADDR, "gr.yoon@gaon.example", "이미 읽은 메일", "사내 행사 일정") if s in kept]
    if not kept or leaked:
        why.append(f"안들의 파일이 없거나 메일 글이 들었다: {leaked} — {kept[:300]}")
    return not why, why


def echoes_preview(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """hold 는 받은 미리 보기를 그대로 다시 낸다 — 미리 보기는 파이프로 기록에 흘러가 사람에게 보일 글이 이것뿐이다."""
    with Home() as home:
        code, out = run(scripts, "journal.py", MOVE_ARGS, home, PREVIEW_MOVE)
    shown = [x for x in PREVIEW_MOVE.splitlines() if x.startswith("  ")]
    return code == 0 and all(x in out.splitlines() for x in shown), [out[-400:]]


def check_journal() -> None:
    ok, rows = records_each_origin(SCRIPTS)
    report("기록 — 옮기기는 메일마다 미리 보기의 그 줄이 말한 원래 자리를 그 번호에 적는다", ok, [json.dumps(rows, ensure_ascii=False)[:400]])

    with Home() as home:
        run(SCRIPTS, "journal.py", MOVE_ARGS, home, PREVIEW_MOVE)
        run(SCRIPTS, "journal.py", ["done"], home, APPLY_MOVE)
        text = (home / LOG_FILE).read_text(encoding="utf-8")
        code, undo = run(SCRIPTS, "journal.py", ["undo", "1"], home)
    lines = undo.splitlines()
    wants = [("받은편지함", U_INBOX), (f"「{TOP}」", U_TOP), (f"「{CHILD}」", U_CHILD)]
    grouped = all(any(place in x and unid in x and sum(u in x for u in (U_INBOX, U_TOP, U_CHILD)) == 1 for x in lines) for place, unid in wants)
    report("기록 — 되돌리는 차례는 원래 자리마다 그 자리의 메일 번호만 묶어 낸다", code == 0 and grouped, [undo[-500:]])
    report("기록 — 기록 파일에는 메일의 제목 · 보낸 분이 없다",
           not any(s in text for s in (*MOVE_SUBJECTS, MOVE_SENDER_ADDR, "gr.yoon@gaon.example")), [text[:300]])

    with Home() as home:
        code, out = run(SCRIPTS, "journal.py", ["hold", "move", "--to", TARGET, U_INBOX, U_TOP], home, PREVIEW_MOVE)
        drift = PREVIEW_MOVE.replace(f" · 받은편지함 · {U_INBOX}\n", f" · {U_INBOX}\n")
        code2, out2 = run(SCRIPTS, "journal.py", MOVE_ARGS, home, drift)
        code3, out3 = run(SCRIPTS, "journal.py", ["hold", "move", "--inbox", U_INBOX, U_TOP, U_CHILD], home, PREVIEW_MOVE)
        nothing = not (home / HELD_FILE).exists() and not log_rows(home)
    report("기록 — 메일 번호 수가 줄 수와 다르거나 · 자리를 못 읽거나 · 받을 자리가 다르면 잡지 않고 1 로 멈춘다",
           (code, code2, code3) == (1, 1, 1) and nothing, [out[-200:], out2[-200:], out3[-200:]])

    with Home() as home:
        run(SCRIPTS, "journal.py", MOVE_ARGS, home, PREVIEW_MOVE)
        code, out = run(SCRIPTS, "journal.py", ["done"], home, APPLY_STALE)
        stale_ok = code == 1 and not log_rows(home) and not (home / HELD_FILE).exists()
    report("기록 — 열쇠가 안 맞아 안 바뀐 실행은 적지 않고 잡아 둔 것을 놓는다", stale_ok, [out[-200:]])

    with Home() as home:
        run(SCRIPTS, "journal.py", ["hold", "trash", U_READ, U_COMMA], home, PREVIEW_TRASH)
        run(SCRIPTS, "journal.py", ["done"], home, APPLY_TRASH)
        code, undo = run(SCRIPTS, "journal.py", ["undo", "1"], home)
    restore = next((x for x in undo.splitlines() if "되살릴" in x), "")
    after = [x for x in undo.splitlines() if "되살린 뒤" in x]
    report("기록 — 휴지통에 보낸 것은 다 되살리고, 폴더에 있던 메일만 그 폴더로 옮기는 차례를 낸다",
           code == 0 and U_READ in restore and U_COMMA in restore and len(after) == 1 and COMMA in after[0] and U_COMMA in after[0]
           and U_READ not in after[0], [undo[-400:]])

    with Home() as home:
        run(SCRIPTS, "journal.py", ["hold", "rule-add"], home, PREVIEW_RULE)
        run(SCRIPTS, "journal.py", ["done"], home, APPLY_RULE)
        code, undo = run(SCRIPTS, "journal.py", ["undo", "1"], home)
        run(SCRIPTS, "journal.py", ["hold", "rule-delete", "--undoes", "1"], home,
            PREVIEW_RULE.replace("규칙 넣기:", "규칙 지우기:"))
        run(SCRIPTS, "journal.py", ["done"], home, "규칙을 지웠다 (목록에서 다시 봐서 없다)\n")
        code2, again = run(SCRIPTS, "journal.py", ["undo", "1"], home)
    report("기록 — 넣은 규칙의 열쇠를 실행의 줄에서 받아 되돌릴 때 그 열쇠를 댄다", code == 0 and RULE_UNID in undo, [undo[-300:]])
    report("기록 — 되돌린 기록이 있으면 그 번호를 대며 차례를 낸다(되돌림은 여러 바꿈일 수 있다)",
           code2 == 0 and "되돌린 기록이 이미 있다(2)" in again, [again[-300:]])

    with Home() as home:
        code, out = run(SCRIPTS, "journal.py", MOVE_ARGS, home, "경고: 임시보관함 보기가 이 메일함에 없다\n" + PREVIEW_MOVE)
        rows_ok = code == 0 and (home / HELD_FILE).exists()
    report("기록 — 표준 오류를 함께 흘려 머리 앞에 경고 줄이 서도 미리 보기를 잡는다", rows_ok, [out[-200:]])

    report("기록 — 잡으며 받은 미리 보기의 메일 줄을 그대로 다시 낸다(사람에게 보일 글)", *echoes_preview(SCRIPTS))
    report("기록 — 잡아 둔 채 맺지 못한 바꿈도 log 에 「결과 모름」으로 서고 undo 가 차례를 내며, 다음 바꿈을 잡으면 버리지 않고 그 번호의 "
           "「결과 모름」으로 기록된다", *shows_unsettled(SCRIPTS))
    report("기록 — 안 하기로 한 미리 보기는 drop 으로 놓이고, 결과를 모르는 되돌림은 「되돌렸다」로 세지 않는다", *releases_declined(SCRIPTS))
    report("기록 — 실행의 「됐다」 줄이 잡아 둔 바꿈과 수 · 받을 자리 · 폴더가 다르면 적지 않고 잡아 둔 것을 남긴다", *refuses_other_apply(SCRIPTS))
    report("기록 — 바꾼 메일 보기는 원래 자리 → 간 자리마다 메일 번호를 묶고 뒤에 다시 바꾼 기록을 댄다", *shows_changed_mails(SCRIPTS))
    report("기록 — 보여 드린 안은 조각의 메일 줄을 다 보이고, 실행 직전 미리 보기가 그 조각과 같을 때만 잡고 다르면 다른 점을 대며 멈춘다",
           *holds_only_as_shown(SCRIPTS))
    report("기록 — 적어 둔 안은 show 가 조각마다 보인 메일 줄을 조각 차례로 그대로 다시 내고(안을 지은 쪽과 보이는 쪽이 달라도 같은 줄), "
           "다음 차례가 아닌 조각 번호는 안에 안 섞는다",
           *lists_shown(SCRIPTS))
    report("기록 — 안 바꾼 조각은 다음 안에 덮여도 plans 가 메일 번호째 내고, 보인 뒤 바꾼 조각 · 메일은 빼며, 안들의 파일에 메일 글이 없다",
           *keeps_unexecuted(SCRIPTS))


# ── 홀로 선다 — 스킬의 스크립트는 표준 라이브러리와 제 폴더의 것만 싣는다 ─────────────────────

# import 말고 코드를 싣는 길 — 경로로 모듈 싣기 · 남의 스크립트 돌리기 · 이름으로 싣기. 찾는 자리를 넓히는 줄은 제 폴더를 넣을 때만 된다
LOADERS = ("spec_from_file_location", "SourceFileLoader", "runpy", "import_module", "__import__(")
OWN_DIR = "Path(__file__).resolve().parent)"


def hands(scripts: pathlib.Path) -> list[pathlib.Path]:
    """스킬의 손 — 폴더의 .py 가운데 검사(`check_*.py`)가 아닌 것. 검사는 금줄 낱말을 제 표로 들어 훑으면 늘 걸린다."""
    return sorted(f for f in scripts.glob("*.py") if not f.name.startswith("check_"))


def strangers(scripts: pathlib.Path) -> list[str]:
    """스크립트가 표준 라이브러리 · 같은 폴더 밖에서 싣는 것 — 앱 몸통 · 다른 스킬의 손의 스크립트 · 경로로 싣는 길."""
    own = {f.stem for f in hands(scripts)}
    out: list[str] = []
    for f in hands(scripts):
        text = f.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            out += [f"{f.name}:{node.lineno} import {n}" for n in names if n not in sys.stdlib_module_names and n not in own]
        out += [f"{f.name}: {w}" for w in LOADERS if w in text]
        out += [f"{f.name}:{i} {line.strip()}" for i, line in enumerate(text.splitlines(), 1)
                if ("sys.path.insert" in line or "sys.path.append" in line) and OWN_DIR not in line]
    return out


def check_alone() -> None:
    got = strangers(SCRIPTS)
    report("홀로 선다 — 스크립트는 표준 라이브러리와 제 폴더의 것만 싣는다(몸통 · 손의 코드 · 경로로 싣는 길이 없다)", not got, got)


# ── 물림 — 일부러 틀린 사본에서 빨강이 나나 ─────────────────────────────────────────

def mutant(patch_file: str, old: str, new: str) -> pathlib.Path | None:
    """스크립트 폴더를 임시 자리에 베끼고 한 파일의 한 줄을 바꾼다 — 바꿀 줄이 없으면 None(물림을 다시 지을 일)."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    for f in hands(SCRIPTS):
        shutil.copy2(f, tmp / f.name)
    target = tmp / patch_file
    text = target.read_text(encoding="utf-8")
    if old not in text:
        shutil.rmtree(tmp, ignore_errors=True)
        return None
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return tmp


def check_teeth() -> None:
    flip = mutant("journal.py", "zip(items, unids)", "zip(items, list(reversed(unids)))")
    report("물림 — 번호를 거꾸로 잇는 기록에서는 「메일마다의 자리」 판정이 빨갛다(표본을 심었다)",
           flip is not None and not records_each_origin(flip)[0], ["물림 표본을 못 심었다 — journal.py 의 번호 잇기가 바뀌었으면 이 물림을 다시 짓는다"])
    body = mutant("journal.py", "import sys\n", "import sys\nfrom secretary import judge\n")
    hand = mutant("journal.py", "from typing import Any\n",
                  "from typing import Any\nsys.path.append(str(pathlib.Path.home() / '.claude/skills/company-mail/scripts'))\n")
    report("물림 — 몸통을 싣거나 손의 폴더를 찾는 자리에 더한 사본에서는 「홀로 선다」 판정이 빨갛다",
           body is not None and hand is not None and bool(strangers(body)) and bool(strangers(hand)),
           ["물림 표본을 못 심었다 — journal.py 의 import 줄이 바뀌었으면 이 물림을 다시 짓는다"])
    for tmp in (flip, body, hand):
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
    for name, file, old, new, judge in TEETH:
        tmp = mutant(file, old, new)
        report(f"물림 — {name}", tmp is not None and not judge(tmp)[0],
               [f"물림 표본을 못 심었다 — {file} 의 「{old.strip()[:50]}」 줄이 바뀌었으면 이 물림을 다시 짓는다"])
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)


# 판정 하나에 사본 하나 — (이름, 파일, 바꿀 줄, 바꾼 줄, 빨개져야 할 판정). 바꾼 줄은 그 판정이 지키는 자리를 끄거나 옛 꼴로 되돌린다.
# 바꿀 줄은 코드로만 고른다 — 주석이 든 줄을 고르면 주석만 고쳐도 물림을 못 심어 빨개진다
TEETH = [
    ("미리 보기를 다시 안 내는 기록에서는 「받은 미리 보기를 다시 낸다」 판정이 빨갛다", "journal.py",
     "        print(line)\n    try:\n        unids, to = given(args)\n",
     "        pass\n    try:\n        unids, to = given(args)\n", echoes_preview),
    ("잡아 둔 바꿈을 안 보이는 기록에서는 「맺지 못한 바꿈」 판정이 빨갛다", "journal.py",
     '    return [*rows, {**hold, "id": next_id(rows), "outcome": UNKNOWN, HELD_KEY: True}]\n', "    return list(rows)\n", shows_unsettled),
    ("새 바꿈을 잡을 때 앞의 잡아 둔 바꿈을 버리는 기록에서는 「맺지 못한 바꿈」 판정이 빨갛다", "journal.py",
     '    entry_id = append(folder, {**old, "outcome": UNKNOWN, "at": _now()})\n', "    entry_id = None\n", shows_unsettled),
    ("결과를 모르는 되돌림도 세는 기록에서는 「안 하기로 한 미리 보기」 판정이 빨갛다", "journal.py",
     'if r.get("outcome") == DONE and not r.get(HELD_KEY)]', "if not r.get(HELD_KEY)]", releases_declined),
    ("실행을 대어 보지 않는 기록에서는 「다른 실행」 판정이 빨갛다", "journal.py",
     "    check_applied(hold, ok)\n", "    pass\n", refuses_other_apply),
    ("뒤에 다시 바꾼 기록을 안 대는 보기에서는 「바꾼 메일 보기」 판정이 빨갛다", "journal.py",
     "        if touched:\n", "        if False:\n", shows_changed_mails),
    ("보인 조각에 대지 않는 기록에서는 「보여 드린 안」 판정이 빨갛다", "journal.py",
     "        diff = differences(shown, hold)\n", "        diff = []\n", holds_only_as_shown),
    ("메일의 자리를 안 대는 견주기에서는 「보여 드린 안」 판정이 빨갛다(번호 묶음만 같으면 잡는다)", "journal.py",
     "        moved = [u for u in now if u in was and now[u] != was[u]]\n", "        moved = []\n", holds_only_as_shown),
    ("조각의 메일 줄을 안 보이는 show 에서는 「보여 드린 안」 판정이 빨갛다", "journal.py",
     "*body, SHOWN.format(", "SHOWN.format(", holds_only_as_shown),
    ("조각의 메일 줄을 안 다시 내는 shown 에서는 「적어 둔 안」 판정이 빨갛다", "journal.py",
     "        for line in body if isinstance(body, list) and body else [SHOWN_NO_BODY]:\n",
     "        for line in [SHOWN_NO_BODY]:\n", lists_shown),
    ("조각 번호의 차례를 안 보는 show 에서는 「적어 둔 안」 판정이 빨갛다", "journal.py",
     "        if args.piece != FIRST_PIECE and args.piece != nxt:\n", "        if False:\n", lists_shown),
    ("조각을 안들에 안 남기는 show 에서는 「안 바꾼 조각」 판정이 빨갛다", "journal.py",
     "    _append_line(folder / PLANS_FILE, row)\n", "    pass\n", keeps_unexecuted),
    ("그 뒤 바꾼 기록을 안 빼는 plans 에서는 「안 바꾼 조각」 판정이 빨갛다", "journal.py",
     '    later = [r for r in rows if r["id"] >= int(row.get("log_from") or 0) and r.get("outcome") == DONE]\n',
     "    later = []\n", keeps_unexecuted),
    ("보이기 전의 기록도 세는 plans 에서는 「안 바꾼 조각」 판정이 빨갛다", "journal.py",
     'r["id"] >= int(row.get("log_from") or 0) and ', "", keeps_unexecuted),
]


def main() -> int:
    if not (SCRIPTS / "journal.py").is_file():
        raise Unmeasured(f"[안 잼] 스크립트를 못 찾았다: {SCRIPTS}")
    print(f"잰다: {SCRIPTS}")
    for check in (check_alone, check_journal, check_teeth):
        if check is check_teeth and not WITH_TEETH:
            continue
        if check is check_teeth and FAILS:
            edge("계약 판정이 빨개 물림을 안 돌렸다 — 늘 지는 판 앞의 물림은 뜻이 없다(머리말 「물림」)")
            continue
        try:
            check()
        except Unmeasured:
            raise
        except Exception:   # noqa: BLE001 — 판정 하나가 넘어져도 나머지를 잰다
            report(f"판정이 넘어지지 않고 끝난다 ({check.__name__})", False, traceback.format_exc().splitlines()[-8:])
    edge("회사 메일 스킬의 꼴이 바뀌었나 · 대화가 미리 보기 · 실행을 기록에 흘려 보내나는 여기서 못 잰다(머리말)")
    print("\n잰 것 — 홀로 선다 · 기록의 자리 · 되돌리는 차례 · 기록에 메일 글 없음 · 꼴이 다르면 멈춤 · 안 바뀐 실행 · "
          "휴지통 되돌리기 · 규칙 열쇠 · 되돌린 기록 · 경고 줄 · 미리 보기를 다시 냄 · 잡아 둔 채 · 놓기 · 다른 실행 · 바꾼 메일 보기 · "
          "보여 드린 안 · 적어 둔 안 · 안 바꾼 조각" +(f" · 물림 {2 + len(TEETH)}" if WITH_TEETH else " (물림은 --teeth)") + (f" — 어긋남 {len(FAILS)}건" if FAILS else ""))
    # 건수는 손으로 적지 않는다 — 이번 판에서 실제로 선 판정을 센다
    print(f"통과 {len(PASSES)}/{len(PASSES) + len(FAILS)}")
    return EXIT_MISMATCH if FAILS else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
