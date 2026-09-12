"""빌려 온 사본이 진본과 같은가 — 머리말의 「빌려 온 자다 — 진본은 …」 곁말을 읽어 그 자리와 견준다.

좌표 — 씨앗 규율은 claude-config 결정 0040 · 곁말의 꼴은 스킬 borrow-spec-as-pair §4 · 진본이 홈에
서는 자리는 결정 0034(`~/.claude/seeds/`).

    python -X utf8 _check/borrowed_check.py                       # 이 폴더 · 진본은 ~/.claude/seeds/
    python -X utf8 _check/borrowed_check.py <폴더>                # 잴 `_check/` 를 지정
    python -X utf8 _check/borrowed_check.py <폴더> --seeds <뿌리>  # 진본 뿌리를 지정 (씨앗 저장소 안에서는 `seeds`)
    python -X utf8 _check/borrowed_check.py --receive              # 어긋난 사본을 진본으로 **받는다** — 곁말은 같은 자리에, 판은 올린다

**받는 손(`--receive`)** — 어긋난 사본마다 진본 글자를 놓고 곁말 블록을 옛 자리(같은 문단 끝)에
되살리며 판 번호를 진본 뿌리의 git 해시(없으면 날짜)로 올린다. 줄끝·BOM 은 옛 사본을 지킨다.
`map_check --write` 와 같은 결의 쓰기 모드다 — 받은 뒤 같은 판에서 다시 재어 초록을 본다.
받는 것은 **곁말 든 사본만**이다 — 일부러 갈린 파일(곁말 없음)은 안 건드린다.

**왜 이 검사가 있나.** 씨앗에서 받아 간 파일은 사본이다 — `_verdict.py` · `exit_code_check.py` 가
그렇게 형제 저장소에 산다. 사본의 머리말은 「진본은 저기(커밋 판)」라고 적고 **손으로 고치지
않는다**고 약속하는데, 그 약속을 무는 자가 없었다. 진본이 움직이면 사본은 조용히 낡고, 사본을
손댄 사람은 진본이 있는 줄 모른다 — 실측 2026-09-13: 형제 둘의 `_verdict.py` 는 같았는데
`log_race_check.py` 가 판정 손 셋을 **손으로 베껴** 들고 있어 진본의 표식 고침(`545f13a`)이
거기만 안 왔다. 곁말은 파일을 열어야 보이고 폴더를 훑는 사람은 안 연다. 그래서 곁말을 기계가
읽는다.

재는 것 — 곁말이 든 파일마다 **진본과 글자가 같은가.** 곁말 블록만 빼고 본다.

  곁말 블록 = 「빌려 온 자다」가 든 줄 + 그 뒤 **빈 줄 전까지의 이어 줄들.** 그래서 곁말은
  **문단 끝에** 둔다 — 문단 머리에 두면 그 문단이 통째로 곁말로 읽혀 어긋남으로 뜬다(그것이
  곧 「자리가 틀렸다」는 빨강이다). 진본의 경로는 곁말 안의 백틱 `seeds/…` 에서 읽는다.
  줄끝(CRLF)과 BOM 은 안 본다 — 사본이 사는 저장소의 체크아웃이 그것을 바꾼다.

⚠ **양성 대조가 판정보다 먼저 선다.** 곁말을 못 읽거나 진본 뿌리가 없으면 어긋남 0 이 나는데,
  그 0 은 초록이 아니다 — §1 이 임시 뿌리에 진본·사본 넷을 지어 같음·어긋남·CRLF·자리 틀림이
  실제로 갈리는지 보이고, 곁말 든 파일이 한 장도 없으면 「못 쟀다」(2)로 나간다.

**안 재는 것** — 곁말 없이 베낀 사본(이름이 같아도 곁말이 없으면 이 자에게는 남이다 — 그것은
`drift_check` 류 재는 자의 몫) · 곁말이 든 **판 번호**가 진본의 지금 판인가(글자가 같으면 판은
묻지 않는다) · 곁말 밖에서 **일부러 갈랐다**고 선언한 파일(그 선언이 있으면 곁말도 없어야
한다 — 둘 다 있으면 어긋남으로 뜬다, 그것이 맞다).

토큰도 망도 브라우저도 안 쓴다.
"""
import difflib
import re
import shutil
import sys
import tempfile
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report

HERE = Path(__file__).resolve().parent

# 굵은 꼴로만 문다 — 맨글자 「빌려 온 자다」는 이 검사의 제 머리말처럼 곁말을 *말하는* 자리에도
# 서므로, 그것까지 물면 받는 자가 제 자신을 사본으로 읽는다(실측 2026-09-13 · 아뜰리에 A1).
MARK = "**빌려 온 자다**"
# 곁말 안의 진본 경로 — 백틱으로 싸인 `seeds/…`. 저장소 이름은 앞에 맨글자로 오므로 안 읽는다.
SOURCE_RE = re.compile(r"`(seeds/[^`]+)`")
HEAD_LINES = 40             # 곁말은 머리말에 산다 — 이 아래는 본문이라 안 뒤진다
DEFAULT_SEEDS = Path.home() / ".claude" / "seeds"


# ── 곁말을 읽는다 ──────────────────────────────────────────────────────────────

def _lines(text):
    return text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def marker(text):
    """(곁말 줄 번호, 진본 상대경로) — 곁말이 없으면 None. 진본 경로가 안 읽히면 경로가 None."""
    for i, line in enumerate(_lines(text)[:HEAD_LINES]):
        if MARK in line:
            m = SOURCE_RE.search(line)
            # 경로가 이어 줄에 있을 수 있다 — 블록 안을 마저 본다
            if not m:
                for cont in block(text, i)[1:]:
                    m = SOURCE_RE.search(cont)
                    if m:
                        break
            return i, (m.group(1) if m else None)
    return None


def block(text, start):
    """곁말 블록 — 시작 줄부터 빈 줄 전까지."""
    out = []
    for line in _lines(text)[start:]:
        if not line.strip():
            break
        out.append(line)
    return out


def body_without_marker(text, start):
    """사본의 글자에서 곁말 블록만 뺀 것 — 진본과 견줄 몸통."""
    ls = _lines(text)
    n = len(block(text, start))
    return "\n".join(ls[:start] + ls[start + n:])


def receive(copy_path, source_path, start, stamp):
    """진본을 사본 자리에 놓는다 — 곁말 블록은 **같은 문단 자리**에 되살리고 판 번호를 올린다.

    자리 규칙 — 옛 사본에서 곁말 앞에 빈 줄이 k 개였으면, 새 진본의 (k+1)번째 빈 줄 **앞**에 둔다
    (곁말은 문단 끝에 산다는 계약 그대로). 진본의 문단이 그보다 적으면 마지막 줄 뒤에 둔다.
    줄끝(CRLF)과 BOM 은 옛 사본의 것을 지킨다 — 받는 저장소의 체크아웃이 정한 것이다.
    """
    old_raw = copy_path.read_bytes()
    crlf = b"\r\n" in old_raw
    bom = old_raw.startswith(b"\xef\xbb\xbf")
    old = _lines(old_raw.decode("utf-8"))
    mark = block("\n".join(old), start)
    mark = [re.sub(r"\([^()]*판\)", f"({stamp} 판)", ln) for ln in mark]
    k = sum(1 for ln in old[:start] if not ln.strip())
    new = _lines(source_path.read_text(encoding="utf-8"))
    at = len(new)
    seen = 0
    for i, ln in enumerate(new):
        if not ln.strip():
            if seen == k:
                at = i
                break
            seen += 1
    out = "\n".join(new[:at] + mark + new[at:])
    if crlf:
        out = out.replace("\n", "\r\n")
    copy_path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8"))


def _stamp(seeds_root):
    """곁말에 적을 판 — 진본 뿌리가 git 나무면 짧은 해시, 아니면 오늘 날짜."""
    try:
        import subprocess
        out = subprocess.run(["git", "-C", str(seeds_root), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    import datetime
    return datetime.date.today().isoformat()


def compare(copy_text, source_text, start):
    """(같은가, 갈린 줄 수)."""
    mine = body_without_marker(copy_text, start)
    theirs = "\n".join(_lines(source_text))
    if mine == theirs:
        return True, 0
    diff = [d for d in difflib.unified_diff(theirs.split("\n"), mine.split("\n"), lineterm="", n=0)
            if d[:1] in "+-" and d[:3] not in ("+++", "---")]
    return False, len(diff)


# ── §1 양성 대조 — 임시 뿌리에 넷을 지어 판정이 실제로 가르는지 먼저 보인다 ────

# 실물 꼴 그대로 — 첫 줄 · 빈 줄 · 좌표 문단 · 빈 줄 · 본문. 좌표 문단 뒤에 빈 줄이 있어야
# 「문단 끝」 자리가 선다(옛 검체는 그 빈 줄이 없어 곁말이 파일 끝에 앉았다 — 실측).
SOURCE = "\"\"\"부품 하나.\n\n좌표 — 어디.\n\n몸통 설명.\n\"\"\"\nX = 1\n"


def _copy(text_source, mark_lines, mutate=None, crlf=False):
    ls = text_source.split("\n")
    # 곁말을 「좌표 — 어디.」 문단 끝(그 줄 바로 뒤 · 빈 줄 앞)에 끼운다
    at = ls.index("좌표 — 어디.") + 1
    ls[at:at] = mark_lines
    text = "\n".join(ls)
    if mutate:
        text = text.replace("X = 1", mutate)
    if crlf:
        text = text.replace("\n", "\r\n")
    return text


def positive_control():
    print("--- §1 양성 대조 — 임시 뿌리의 진본·사본 넷이 정말 갈리나")
    tmp = Path(tempfile.mkdtemp(prefix="borrowed-"))
    try:
        src_dir = tmp / "seeds" / "check" / "_check"
        src_dir.mkdir(parents=True)
        (src_dir / "_part.py").write_text(SOURCE, encoding="utf-8")
        one = ["⚠ **빌려 온 자다** — 진본은 claude-config `seeds/check/_check/_part.py`(abc1234 판)이고,",
               "  고침은 **진본에서 받는다** — 이 사본을 손으로 고치지 않는다."]
        cases = [
            ("같은 사본은 같음이다",                    _copy(SOURCE, one), True),
            ("몸통이 갈린 사본은 어긋남이다",           _copy(SOURCE, one, mutate="X = 2"), False),
            ("CRLF 로 체크아웃된 사본은 같음이다",      _copy(SOURCE, one, crlf=True), True),
            ("곁말을 문단 머리에 둔 사본은 어긋남이다",
             "\"\"\"부품 하나.\n\n" + one[0] + "\n" + one[1] + "\n좌표 — 어디.\n\n몸통 설명.\n\"\"\"\nX = 1\n", False),
        ]
        for said, copy_text, want_same in cases:
            found = marker(copy_text)
            if found is None or found[1] is None:
                report(said, False, ["곁말을 못 읽었다"])
                continue
            same, _n = compare(copy_text, SOURCE, found[0])
            report(said, same == want_same, [f"같음={same} (기대 {want_same})"])
        report("곁말 없는 파일은 남이다 — 곁말이 None 이다", marker(SOURCE) is None)
        # 받는 손 — 갈린 사본(CRLF)을 받으면 같음이 되고, 곁말은 같은 문단 끝에 서며, 판이 오른다
        copy_path = tmp / "_part.py"
        copy_path.write_bytes(_copy(SOURCE, one, mutate="X = 2", crlf=True).encode("utf-8"))
        receive(copy_path, src_dir / "_part.py", marker(copy_path.read_text(encoding="utf-8"))[0], "new1234")
        got = copy_path.read_bytes().decode("utf-8")
        found = marker(got)
        report("받은 사본은 같음이고 곁말이 같은 자리에 서며 판이 올랐다",
               found is not None and compare(got, SOURCE, found[0])[0]
               and "(new1234 판)" in got and "\r\n" in got
               and _lines(got)[found[0] - 1] == "좌표 — 어디.",
               [got[:200]])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── §2 실물 전수 ───────────────────────────────────────────────────────────────

def survey(check_dir, seeds_root):
    """(어긋남들, 같음 수, 진본 없음들, 경로 못 읽음들)."""
    bad, same, missing, unreadable = [], 0, [], []
    for p in sorted(Path(check_dir).iterdir()):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found = marker(text)
        if found is None:
            continue
        start, rel = found
        if rel is None:
            unreadable.append(p.name)
            continue
        source = Path(seeds_root) / Path(rel).relative_to("seeds")
        if not source.is_file():
            missing.append(f"{p.name} → {source}")
            continue
        ok, n = compare(text, source.read_text(encoding="utf-8"), start)
        if ok:
            same += 1
            print(f"  = 같음   {p.name}  ← {rel}")
        else:
            bad.append((p.name, rel, n))
    return bad, same, missing, unreadable


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    seeds_root = DEFAULT_SEEDS
    if "--seeds" in argv:
        seeds_root = Path(argv[argv.index("--seeds") + 1]).resolve()
        args = [a for a in args if a != str(seeds_root) and Path(a).resolve() != seeds_root]
    check_dir = Path(args[0]).resolve() if args else HERE
    print(f"잴 폴더 — {check_dir}\n진본 뿌리 — {seeds_root}\n")

    positive_control()

    print("\n--- §2 실물 전수 — 곁말 든 사본이 진본과 같은가")
    if not seeds_root.is_dir():
        raise Unmeasured(f"[안 잼] 진본 뿌리가 없다 — {seeds_root}. 홈에 씨앗이 안 깔렸으면 "
                         "deploy.ps1 이 안 돈 것이고, 씨앗 저장소 안이면 `--seeds seeds` 를 준다")
    bad, same, missing, unreadable = survey(check_dir, seeds_root)
    if bad and "--receive" in argv:
        stamp = _stamp(seeds_root)
        for name, rel, _n in bad:
            copy_path = check_dir / name
            found = marker(copy_path.read_text(encoding="utf-8"))
            receive(copy_path, Path(seeds_root) / Path(rel).relative_to("seeds"), found[0], stamp)
            print(f"  ← 받았다 {name}  ← {rel} ({stamp} 판)")
        edge(f"**받았다** — 어긋난 사본 {len(bad)}장을 진본으로 놓고 곁말 판을 {stamp} 로 올렸다. 아래는 받은 뒤의 판정이다")
        bad, same, missing, unreadable = survey(check_dir, seeds_root)
    if not (bad or same or missing or unreadable):
        raise Unmeasured(f"[안 잼] 곁말 든 파일이 한 장도 없다 — {check_dir}. "
                         "빌려 온 것이 없으면 잴 것이 없고, 있는데 곁말이 없으면 이 자에게는 남이다")

    # 센티널 — 곁말은 있는데 견준 것이 0 이면 어긋남도 0 이라 **아무것도 안 잰 초록**이 난다.
    # 진본을 한 장도 못 찾은 판(홈에 씨앗이 안 깔린 PC · 뿌리를 잘못 준 판)이 그렇다 — 실측
    # 2026-09-13 헬퍼 B1. 그 판은 초록이 아니라 「못 쟀다」다.
    if not (same or bad):
        raise Unmeasured(f"[안 잼] 곁말 든 파일 {len(missing) + len(unreadable)}장 중 진본과 견준 것이 "
                         f"0 이다 — 진본 없음 {len(missing)} · 경로 못 읽음 {len(unreadable)}. "
                         f"진본 뿌리 {seeds_root} 가 맞는가")
    for name, rel, n in bad:
        report(f"{name} — 진본 {rel} 과 어긋남", False, [f"갈린 줄 {n}"])
    report(f"곁말 든 사본이 진본과 같다 (같음 {same} · 어긋남 {len(bad)})", not bad)

    for row in missing:
        edge(f"**진본이 없다** — {row}. 곁말이 가리키는 자리에 파일이 없다 — 옮겨졌거나 곁말이 낡았다")
    for row in unreadable:
        edge(f"**곁말은 있는데 `seeds/…` 경로가 없다** — {row}. 진본을 씨앗 밖(형제 앱)에 두는 파일이면 "
             "그것이 맞고 이 자는 남이다 — 씨앗에서 받은 것이면 곁말이 낡았다")
    if missing or unreadable:
        edge("진본이 없거나 경로를 못 읽은 파일은 판정이 아니라 **안 잰 자리**다 — 위 건수에서 빠져 있다")

    edge(f"잰 범위 — `{check_dir.name}/` 의 곁말 든 파일 {same + len(bad)}장. "
         "곁말 없이 베낀 사본은 안 든다 — 그것은 갈림을 세우는 자(`drift_check` 류)의 몫이다")
    edge("**판 번호는 안 문다** — 글자가 같으면 곁말의 커밋이 옛것이어도 초록이다")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        print("고치는 법: 진본에서 다시 받는다. 사본을 고쳐야 했다면 그 고침은 진본으로 올린다")
        return EXIT_MISMATCH
    print(f"전부 통과 (판정 {len(passes())}건 — 양성 대조 {len(passes()) - 1} · 실물 전수 1)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
