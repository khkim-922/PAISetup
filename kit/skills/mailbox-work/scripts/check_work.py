"""업무 파악 스킬의 쓰는 손(곁의 `work.py`)이 업무 파일을 받은 글 그대로 쓰고, 앞 판의 절을 빠뜨린 글 · 빈 글로는 덮어쓰지 않나를 문다.

    python -X utf8 -I check_work.py [스크립트 폴더] [--teeth]

층 — 쓰는 사람의 계약. 손을 명령 그대로 부르고, 사용자 폴더는 `MAIL_SECRETARY_HOME` 으로 임시 자리에 둔다.
남기는 까닭 — 판정마다 check-design 1 절의 넷을 다 지난다(판정별 표는 `references/DESIGN.md` 「검사가 남는 까닭」).
언제 걷나 — 업무 파일이 통째로 다시 쓰는 파일이 아니게 되거나(절마다 따로 쓰는 손), 업무 파악이 이 손 없이 파일을 쓰게 될 때.
여기서 못 재는 것 — 모델이 업무 파일을 스킬 글의 절대로 짓나 · 사람 없는 실행에서 이 손이 열린 명령에 들었나(메일함 스캔의 몫).

물림 — `--teeth` 는 계약 판정에 이어 그 판정이 지키는 한 줄을 끈 손의 사본에서 빨강을 본다. 계약 판정이 하나라도 빨가면 안 돌리고,
사본을 못 심으면 그 물림이 빨갛다. 푸시 문(`skill-checks`)은 인자 없이 불러 계약 판정만 돈다.

폴더를 안 주면 이 파일이 든 폴더만 읽는다. 기대값은 손의 「지키는 것」에서 낸다 — 쓴 파일은 받은 글과 한 자씩 같고(줄끝만 LF), 막은
쓰기 뒤의 파일은 앞 판과 한 자씩 같다.
종료 값 — 끝 줄이 「통과 N/N」이면 0, 하나라도 어긋나면 1, 손을 못 찾거나 못 돌렸으면 2.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import traceback

sys.stdout.reconfigure(encoding="utf-8")

EXIT_OK, EXIT_MISMATCH, EXIT_UNMEASURED = 0, 1, 2
FAILS: list[str] = []
PASSES: list[str] = []


class Unmeasured(SystemExit):
    """「못 쟀다」로 그 자리에서 나간다 — 까닭을 stdout 에 찍고 2 로."""

    def __init__(self, why):
        super().__init__(EXIT_UNMEASURED)
        self.why = str(why)
        print(self.why)

    def __str__(self):
        return self.why


def report(name, ok, detail=()):
    (PASSES if ok else FAILS).append(name)
    print(f"[{'OK ' if ok else 'NG '}] {name}")
    for row in detail if not ok else ():
        print(f"       {row}")


def edge(text):
    print(f"  ⚠ {text}")


HERE = pathlib.Path(__file__).resolve().parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
WITH_TEETH = "--teeth" in sys.argv[1:]
SCRIPTS = pathlib.Path(ARGS[0]).resolve() if ARGS else HERE
HAND = "work.py"
WORK = "work.md"
TIMEOUT_S = 30

# ── 표본 — 업무 파일 한 판(가상의 회사 · 사람). 절 이름은 스킬 글 「업무 파일」의 것 ─────────────────────────────

FIRST = """# 업무 파일

## 본 날 · 본 범위
2026-11-16 08:05 — 받은편지함 · 폴더 · 보낸편지함의 석 달치를 머리로 보고 41통을 열었다. 본 가장 늦은 메일 11/16 07:58 · 0000000000000000A1B2C3D4E5F60031

## 사용자
윤가람 · gr.yoon@gaon.example · 책임 · 소재개발그룹 · 부를 호칭 「책임님」 · 윗분 박서진 상무 — 11/16 대화에서 확인받았다

## 업무
양극재 시험 일정과 협력사 납기를 챙긴다.

## 일
- 0000000000000000A1B2C3D4E5F60007 협력사 납기 회신 — 하늘부품 → 사용자, 11/20 까지 · 사용자 차례

## 열린 것
없음
"""
# 한글 Windows 콘솔(cp949)로 올 수 있는 글 — cp949 에 없는 글자(긴 줄표)를 뺀 같은 판
CP949_FIRST = FIRST.replace("—", "-")
# 다음 날 이어 파악 — 일이 하나 늘고 열린 것이 찬다. 절은 그대로(차례는 바뀌어도 된다)
NEXT = FIRST.replace("## 열린 것\n없음\n", "## 열린 것\n- 새 직함으로 보이는 서명 — 확인 전\n") \
    .replace("· 사용자 차례\n", "· 사용자 차례\n- 0000000000000000A1B2C3D4E5F60040 시험 성적서 검토 — 품질팀 → 사용자\n")
# 「사용자」 절을 빠뜨린 다시 쓰기
DROPS_USER = NEXT.split("## 사용자\n")[0] + "## 업무\n" + NEXT.split("## 업무\n")[1]


def run(folder: pathlib.Path, scripts: pathlib.Path, *args: str, stdin: bytes = b"") -> tuple[int, str]:
    env = {**os.environ, "MAIL_SECRETARY_HOME": str(folder), "PYTHONIOENCODING": "utf-8"}
    try:
        got = subprocess.run([sys.executable, "-X", "utf8", "-I", str(scripts / HAND), *args], input=stdin, capture_output=True,
                             env=env, timeout=TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unmeasured(f"[안 잼] 손을 못 돌렸다: {type(exc).__name__}: {exc}") from exc
    return got.returncode, (got.stdout + got.stderr).decode("utf-8", errors="replace")


def fresh_home() -> pathlib.Path:
    """빈 임시 자리 — 그 안의 아직 없는 사용자 폴더를 낸다(손이 폴더를 만드나도 함께 본다)."""
    return pathlib.Path(tempfile.mkdtemp()) / "mail-secretary"


def read(folder: pathlib.Path) -> str | None:
    path = folder / WORK
    return path.read_bytes().decode("utf-8") if path.is_file() else None


# ── 판정 — 스크립트 폴더를 받아 (맞나, 상세) 를 낸다(물림이 사본에 같은 판정을 댄다) ─────────────────────────────

def writes_as_given(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """없는 폴더에 처음 쓰면 폴더를 만들고 받은 글 그대로 남긴다 — cp949 · CRLF 로 와도 UTF-8 · LF 로. 끝 줄이 자리를 댄다."""
    folder = fresh_home()
    try:
        why: list[str] = []
        code, out = run(folder, scripts, "write", stdin=CP949_FIRST.replace("\n", "\r\n").encode("cp949"))
        if code != 0 or read(folder) != CP949_FIRST or str(folder / WORK) not in out:
            why.append(f"처음 쓰기(cp949 · CRLF): 종료 {code} · 같은가 {read(folder) == CP949_FIRST} · 끝 줄 {out.strip()[-200:]}")
        code, out = run(folder, scripts, "write", stdin=NEXT.encode("utf-8"))
        if code != 0 or read(folder) != NEXT:
            why.append(f"절을 다 든 다시 쓰기: 종료 {code} · 같은가 {read(folder) == NEXT} · {out.strip()[-200:]}")
        return not why, why
    finally:
        shutil.rmtree(folder.parent, ignore_errors=True)


def keeps_sections(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """앞 판에 있던 절이 빠진 글(빈 글 포함)은 안 쓴다 — 1 로 끝나고 파일은 앞 판 그대로, 끝 줄이 빠진 절의 이름을 댄다."""
    folder = fresh_home()
    try:
        folder.mkdir(parents=True)
        (folder / WORK).write_bytes(FIRST.encode("utf-8"))
        why: list[str] = []
        code, out = run(folder, scripts, "write", stdin=DROPS_USER.encode("utf-8"))
        if code != 1 or read(folder) != FIRST or "사용자" not in out:
            why.append(f"「사용자」를 뺀 글: 종료 {code} · 앞 판 그대로 {read(folder) == FIRST} · 끝 줄 {out.strip()[-200:]}")
        for name, given in (("빈 글", b""), ("절 없는 글", "업무 파일을 다시 지었다\n".encode("utf-8"))):
            code, out = run(folder, scripts, "write", stdin=given)
            if code != 1 or read(folder) != FIRST:
                why.append(f"{name}: 종료 {code} · 앞 판 그대로 {read(folder) == FIRST} · {out.strip()[-160:]}")
        return not why, why
    finally:
        shutil.rmtree(folder.parent, ignore_errors=True)


# 정리 스킬이 쓰던 꼴의 업무 파일 — 옛 이름의 「업무 한 문단」과, 지금은 정리 파일이 드는 두 절을 든다
OLD_TIDY = FIRST.replace("## 업무\n", "## 업무 한 문단\n") + """
## 정리한 뒤의 메일함
11/15 정리 뒤 받은편지함 120통(안 읽음 8) · 기록 번호 3

## 정한 것
- 협력사 공지 폴더는 안 만든다(11/15 마다하심)
"""


def migrates_old_tidy(scripts: pathlib.Path) -> tuple[bool, list[str]]:
    """정리 스킬이 쓰던 업무 파일 위에 지금 꼴로 쓰면 쓴다 — 옮겨 간 두 절은 정리 파일 끝에 옮겨 적히되, 이미 있는 절은 다시 안 덧붙인다."""
    folder = fresh_home()
    try:
        folder.mkdir(parents=True)
        why: list[str] = []
        (folder / WORK).write_bytes(OLD_TIDY.encode("utf-8"))
        code, out = run(folder, scripts, "write", stdin=NEXT.encode("utf-8"))
        tidy = folder / "mailbox-tidy.md"
        got = tidy.read_text(encoding="utf-8") if tidy.is_file() else ""
        if code != 0 or read(folder) != NEXT or "120통(안 읽음 8)" not in got or "11/15 마다하심" not in got:
            why.append(f"옛 꼴 위 쓰기: 종료 {code} · 업무 파일이 받은 글 {read(folder) == NEXT} · 정리 파일 {got[:120]!r} · {out.strip()[-160:]}")
        (folder / WORK).write_bytes(OLD_TIDY.encode("utf-8"))
        tidy.write_text("## 정한 것\n- 지금 판 — 정리 스킬이 고친 것\n", encoding="utf-8")
        code, out = run(folder, scripts, "write", stdin=NEXT.encode("utf-8"))
        got = tidy.read_text(encoding="utf-8")
        if code != 0 or got.count("## 정한 것") != 1 or "11/15 마다하심" in got or "120통(안 읽음 8)" not in got:
            why.append(f"정리 파일에 이미 있는 절: 종료 {code} · 정리 파일 {got[:200]!r}")
        return not why, why
    finally:
        shutil.rmtree(folder.parent, ignore_errors=True)


CONTRACT = [
    ("받은 글 그대로 쓴다 — 없는 사용자 폴더를 만들고, cp949 · CRLF 로 와도 UTF-8 · LF 로 남고, 끝 줄이 자리를 댄다", writes_as_given),
    ("앞 판의 절을 빠뜨린 글 · 빈 글로는 안 덮는다 — 1 로 끝나고 파일은 앞 판 그대로, 끝 줄이 빠진 절을 댄다", keeps_sections),
    ("정리 스킬이 쓰던 업무 파일 위에도 쓴다 — 이름이 바뀐 절은 새 이름으로 서고, 정리 파일로 옮겨 간 절은 정리 파일에 한 번 옮겨 적힌다",
     migrates_old_tidy),
]

# 판정 하나에 사본 하나 — (이름, 바꿀 줄, 바꾼 줄, 빨개져야 할 판정)
TEETH = [
    ("앞 판의 절을 안 견주는 손에서는 「앞 판의 절」 판정이 빨갛다",
     "        missing = [h for h in heads(old_text) if h not in new]\n", "        missing = []\n", keeps_sections),
    ("옮겨 간 절을 정리 파일에 안 옮기는 손에서는 「옛 꼴」 판정이 빨갛다",
     "            moved = move_to_tidy(folder, old_text, moving)\n", "            moved = []\n", migrates_old_tidy),
    ("cp949 를 UTF-8 로 읽는 손에서는 「받은 글 그대로」 판정이 빨갛다",
     '        return raw.decode("cp949", errors="replace")\n', '        return raw.decode("utf-8", errors="replace")\n', writes_as_given),
]


def mutant(old: str, new: str) -> pathlib.Path | None:
    """손을 임시 자리에 베끼고 한 줄을 바꾼다 — 바꿀 줄이 없으면 None(물림을 다시 지을 일)."""
    text = (SCRIPTS / HAND).read_text(encoding="utf-8")
    if old not in text:
        return None
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / HAND).write_text(text.replace(old, new, 1), encoding="utf-8")
    return tmp


def main() -> int:
    if not (SCRIPTS / HAND).is_file():
        raise Unmeasured(f"[안 잼] 손을 못 찾았다: {SCRIPTS / HAND}")
    print(f"잰다: {SCRIPTS}")
    for name, judge in CONTRACT:
        try:
            ok, why = judge(SCRIPTS)
        except Unmeasured:
            raise
        except Exception:   # noqa: BLE001 — 판정 하나가 넘어져도 나머지를 잰다
            ok, why = False, traceback.format_exc().splitlines()[-6:]
        report(name, ok, why)
    if WITH_TEETH and FAILS:
        edge("계약 판정이 빨개 물림을 안 돌렸다 — 늘 지는 판 앞의 물림은 뜻이 없다")
    elif WITH_TEETH:
        for name, old, new, judge in TEETH:
            tmp = mutant(old, new)
            try:
                report(f"물림 — {name}", tmp is not None and not judge(tmp)[0],
                       [f"물림 표본을 못 심었다 — {HAND} 의 「{old.strip()[:50]}」 줄이 바뀌었으면 이 물림을 다시 짓는다"])
            finally:
                if tmp is not None:
                    shutil.rmtree(tmp, ignore_errors=True)
    edge("모델이 업무 파일을 스킬 글의 절대로 짓나 · 사람 없는 실행에 이 손이 열렸나는 여기서 못 잰다(머리말)")
    print("\n잰 것 — 받은 글 그대로 · 앞 판의 절(빈 글 포함)" + (f" · 물림 {len(TEETH)}" if WITH_TEETH else " (물림은 --teeth)")
          + (f" — 어긋남 {len(FAILS)}건" if FAILS else ""))
    print(f"통과 {len(PASSES)}/{len(PASSES) + len(FAILS)}")
    return EXIT_MISMATCH if FAILS else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
