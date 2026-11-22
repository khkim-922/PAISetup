"""빌려 온 사본이 진본과 같은가 — 머리말의 「빌려 온 자다 — 진본은 …」 곁말을 읽어 그 자리 · 그 판과 견준다.

층 — 만드는 사람의 흐름
걷는 조건 — 씨앗 사본에 곁말을 달아 손으로 받는 길이 사라지면(사본을 진본에서 만들어 내면) 걷는다

좌표 — 씨앗 규율은 곁 `README.md` 「이 폴더의 규율」 · 곁말의 꼴은 스킬 borrow-spec-as-pair
「빌린 뒤 좌표를 남긴다」 · 진본이 홈에 서는 자리는 `~/.claude/seeds/`.

    python -X utf8 _check/borrowed_check.py                       # 이 폴더 · 진본은 ~/.claude/seeds/
    python -X utf8 _check/borrowed_check.py <폴더>                # 잴 `_check/` 를 지정
    python -X utf8 _check/borrowed_check.py <폴더> --seeds <뿌리>  # 진본 뿌리를 지정 (씨앗 저장소 안에서는 `seeds`)
    python -X utf8 _check/borrowed_check.py --receive              # 갈린 사본을 진본으로 **받는다** — 곁말은 같은 자리에, 판은 올린다

내는 것 — 0 손댄 사본이 없다(진본이 앞서 가 받을 판이 있는 사본은 판정 곁에 이름으로 선다) · 1 손댄 사본이나
옛 도장, 또는 안 무는 양성 대조가 있다(`--receive` 를 주면 받은 뒤의 판정) · 2 못 쟀다(진본 뿌리가 없다 · 곁말
든 파일이 한 장도 없다 · 손댐을 가른 것이 0 이다).

받는 손(`--receive`) — 지금 진본과 갈린 사본(손댄 것 · 받을 판 · 못 가른 것)과 옛 도장의 사본마다 진본 글자를 놓고 곁말 블록을 받기 전 자리
(같은 문단 끝)에 되살리며 **판 번호를 진본 뿌리의 판으로 올린다**(아래 「어느 판의 진본과 견줬나」의
차례 그대로 · 판을 모르면 받은 날짜를 적는다 — 곁말의 그 자리는 사람이 읽는 영수증이고, 판정 줄은 그
날짜를 안 쓴다). 줄끝·BOM 은 받기 전 사본의 것을 지킨다.
`map_check --write` 와 같은 결의 쓰기 모드다 — 받은 뒤 같은 판에서 다시 재어 초록을 본다.
받는 것은 곁말 든 사본만이다 — 일부러 갈린 파일(곁말 없음)은 안 건드린다.

**왜 이 검사가 있나.** 씨앗에서 받아 간 파일은 사본이다 — `_verdict.py` · `exit_code_check.py` 가
그렇게 형제 저장소에 산다. 사본의 머리말은 「진본은 저기(커밋 판)」라고 적고 손으로 고치지 않는다고
약속하지만, 진본이 움직이면 사본은 조용히 낡고 사본을 손댄 사람은 진본이 있는 줄 모른다.
곁말은 파일을 열어야 보이고 폴더를 훑는 사람은 안 연다 — 그래서 곁말을 기계가
읽고, 그 약속을 이 검사가 문다.

재는 것 — 곁말이 든 파일마다 **곁말이 적은 판의 진본과 글자가 같은가**(손대지 않았나). 곁말 블록만 빼고 본다.
지금 진본과 같으면 거기서 끝이다. 갈렸으면 곁말의 판으로 가른다(`triage()`) — 그 판의 진본 그대로면 **받을 판이
있을 뿐**이라 빨강이 아니고(진본 저장소가 앞서 간 것은 받은 저장소의 결함이 아니다 — 빨강으로 세면 진본 저장소의
커밋마다 받은 저장소가 붉어진다), 그 판과도 다르면 손댄 것이라 빨강이다. 그 판을 꺼낼 수 있는 것은 진본 뿌리가
git 나무일 때다(진본 저장소의 `seeds` 를 `--seeds` 로 준 판). 홈 씨앗처럼 git 나무가 아니면 뿌리의 판(`.version`)이
곁말의 판과 같을 때만 손댐을 가르고, 다르면 「못 가른다」를 판정 곁에 찍는다 — 안 잰 자리다.

  곁말 블록 = 머리 `HEAD_LINES` 줄 안에서 굵은 꼴 「빌려 온 자다」가 든 줄 + 그 뒤 빈 줄 전까지의
  이어 줄들. 그래서 곁말은 **문단 끝에** 둔다 — 문단 머리에 두면 그 문단이 통째로 곁말로 읽혀
  어긋남으로 뜬다(그것이 곧 「자리가 틀렸다」는 빨강이다). 진본의 경로는 곁말 안의 백틱 `seeds/…` 에서
  읽는다. 줄끝(CRLF)과 BOM 은 안 본다 — 사본이 사는 저장소의 체크아웃이 그것을 바꾼다.

**어느 판의 진본과 견줬나를 판정 줄이 말한다.** 진본 뿌리의 판은 뿌리에 놓인 `.version` 한
줄(`<판> <ISO 날짜>` · 홈에 씨앗을 미는 자가 남긴다) → 뿌리가 git 나무면 HEAD → 둘 다 없으면
「판 모름」 차례로 읽는다. 모르는 판을 날짜로 메우지 않는 까닭은 `_stamp()` 머리말이 든다.

**잴 수 있나를 §1 양성 대조보다 먼저 묻는다.** 양성 대조의 판정들은 탐지기가 무나를 보이는 자검이지
이 나무를 잰 것이 아니다. 진본 뿌리가 없거나 곁말 든 파일이 한 장도 없는 판에서 자검 줄만 `[OK]` 로
찍히면 화면은 그만큼을 잰 것처럼 보인다 — 러너 홈에 `~/.claude/seeds` 가 없는 CI 가 그 판이다.
못 재는 판은 한 줄도 안 찍고 까닭을 대며 「못 쟀다」(2)로 나간다.

**양성 대조가 판정보다 먼저 선다.** 곁말을 못 읽으면 어긋남 0 이 나는데 그 0 은 초록이 아니다 —
§1 양성 대조가 임시 뿌리에 진본·사본 넷을 지어 같음·어긋남·CRLF·자리 틀림이 실제로 갈리는지
보이고, 받는 손 · 판을 읽는 차례 · 도장도 같은 절에서 문다.

**도장은 조건부로 잰다** — 곁말의 `(<판> 판)` 이 가리키는 판의 진본 본문을 꺼내 사본 본문과 견준다.
진본 뿌리가 git 나무일 때만이다(진본 저장소가 붙은 PC · CI 의 `--seeds`) — 몸통이 지금 판과 같아도
영수증이 옛 판이면 「영수증만 옛 판이다」 빨강이고 `--receive` 가 도장을 올린다(영수증은 진본이 앞서 갔을
때 손댐과 받을 판을 가르는 기준이라, 틀린 채 두면 다음에 진본이 움직일 때 손 안 댄 사본이 손댄 것으로 선다). 뿌리가 git 나무가
아니면(홈 씨앗 · 설치본) 그 항은 판정 없이 「도장은 못 쟀다」고 고지한다 — 초록으로 세지 않는다.
판을 해시로 안 적은 곁말(「같은 저장소 · 같은 판」 · 날짜)은 도장 항이 없고 몸통 견줌만 든다.

**안 재는 것** — git 나무가 아닌 진본 뿌리에서 곁말의 판과 뿌리의 판이 다른 사본의 손댐(위 「못 가른다」) ·
곁말 없이 베낀 사본(이름이 같아도 곁말이 없으면 이 자에게는 남이다 — 그것은 `drift_check` 류 재는 자의 몫) · 진본 뿌리가 그 나무의 최신 판인가(판을 찍기만 하고 묻지 않는다 — 찍힌 판이
그 물음의 재료다) · 곁말 밖에서 일부러 갈랐다고 선언한 파일(그 선언이 있으면 곁말도 없어야
한다 — 둘 다 있으면 어긋남으로 뜬다, 그것이 맞다) · 곁말을 못 다는 `.githooks/` 배포본(가리킬
`seeds/…` 자리가 없다 — 형제는 그 몸통만 들고 조각은 러너가 설정 저장소, 없으면 홈 씨앗에서 찾는다).

토큰도 망도 브라우저도 안 쓴다.
"""
import datetime
import difflib
import re
import shutil
import sys
import tempfile
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report

HERE = Path(__file__).resolve().parent

# 굵은 꼴로만 문다 — 맨글자 「빌려 온 자다」는 이 검사의 제 머리말처럼 곁말을 *말하는* 자리에도
# 서므로, 그것까지 물면 받는 자가 제 자신을 사본으로 읽는다.
MARK = "**빌려 온 자다**"
# 곁말 안의 진본 경로 — 백틱으로 싸인 `seeds/…`. 저장소 이름은 앞에 맨글자로 오므로 안 읽는다.
SOURCE_RE = re.compile(r"`(seeds/[^`]+)`")
HEAD_LINES = 40             # 곁말은 머리말에 산다 — 이 아래는 본문이라 안 뒤진다
DEFAULT_SEEDS = Path.home() / ".claude" / "seeds"
# 진본 뿌리가 어느 판인가를 적어 둔 한 줄 — `<판> <ISO 날짜>`. 이 자는 첫 낱말을 판으로 읽는다.
# 홈 뿌리는 git 나무가 아니라 판을 물을 데가 없어 미는 자가 남긴다 — `deploy.ps1` 의 「씨앗의 판 줄」
# 칸과 세션 훅 `deploy_home_norms` 의 씨앗 칸은 claude-config 짧은 해시를, 설치기(`install.ps1`)는
# 릴리스 판 번호를 적는다. 이름이 한 낱말이라 선언 파일로 안 뽑는다 — 쓰는 자들과 이 자가 곁말로
# 서로를 가리킨다.
VERSION_FILE = ".version"

# 게이트 훅이 사는 폴더 이름 — 이 자는 안 잰다. 곁 `exit_code_check.py` 가 이 이름과 아래 `hooks_root()` 를
# 불러 가 제 `.githooks/` 팔의 뿌리를 찾는다 — 두 자리에 손으로 적지 않게 여기 둔다.
# ⚠ 두 이름을 바꾸면 그쪽 가져오기가 지고, 그 팔은 빨강 없이 「안 잰 자리」 고지로만 빈다.
HOOKS = ".githooks"


# ── 곁말을 읽는다 ──────────────────────────────────────────────────────────────

def _lines(text):
    return text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def marker(text):
    """(곁말 줄 번호, 진본 상대경로) — 곁말이 없으면 None. 진본 경로가 안 읽히면 경로가 None.

    머리 `HEAD_LINES` 줄 안에서 `MARK` 가 든 첫 줄만 본다.
    """
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

    받는 것 — 사본 경로 · 진본 경로 · 사본의 곁말 줄 번호 · 올릴 판. 곁말 블록 안의 `(… 판)` 을
    `(<판> 판)` 으로 갈고 사본 파일을 덮어쓴다. 돌려주는 것은 없다.

    자리 규칙 — 받기 전 사본에서 곁말 앞에 빈 줄이 k 개였으면, 새 진본의 (k+1)번째 빈 줄 **앞**에 둔다
    (곁말은 문단 끝에 산다는 계약 그대로). 진본의 문단이 그보다 적으면 마지막 줄 뒤에 둔다.
    줄끝(CRLF)과 BOM 은 받기 전 사본의 것을 지킨다 — 받는 저장소의 체크아웃이 정한 것이다.
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
    """진본 뿌리가 어느 판인가 — `(판, 어디서 읽었나)`. 모르면 `(None, 까닭)`.

    차례 셋 — ① 뿌리의 `.version` 첫 줄의 첫 낱말(홈에 씨앗을 미는 자가 남긴다) ② 뿌리가 git
    나무면 `HEAD` 짧은 해시 ③ 둘 다 없으면 모른다.

    ⚠ **③ 을 오늘 날짜로 메우지 않는다.** 돌린 날은 진본의 판이 아니다 — 그 날짜를 달면 홈이 아무리
      낡아도 판정 줄이 최신과 견준 것처럼 읽힌다(claude-config `10de3ef`). 모르는 것은 모른다고 적고,
      받은 날짜는 `--receive` 의 영수증 자리에만 쓴다.
    """
    rows = []
    try:
        rows = (Path(seeds_root) / VERSION_FILE).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        pass
    field = (rows[0] if rows else "").split()
    if field:
        return field[0], f"{VERSION_FILE} · {' '.join(field[1:]) or '날짜 없음'}에 깔렸다"
    try:
        import subprocess
        out = subprocess.run(["git", "-C", str(seeds_root), "rev-parse", "--short", "HEAD"], env=_git_env(),
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip(), "뿌리가 git 나무다 — HEAD"
    except (OSError, subprocess.SubprocessError):
        pass
    return None, f"뿌리에 `{VERSION_FILE}` 도 없고 git 나무도 아니다"


def _git_env():
    """다른 나무를 부르는 git 의 환경 — `os.environ` 사본에서 훅이 내보낸 이 저장소 변수를 뺀 사전.

    ⚠ **다른 나무를 부르는 git 은 다 이 환경을 물린다.** 커밋 훅 안에서 돌면 git 이 `GIT_DIR` ·
      `GIT_INDEX_FILE` 따위를 내보내고, 이 검사가 부르는 `git -C <임시 폴더> init/commit` 이 그것을
      물려받는다. 본 트리에서는 그 값이 상대(`.git`)라 임시 폴더 안에서 풀려 무해하지만, 연결된 작업
      트리(`git worktree add`)에서는 절대 경로라 `init` 이 진짜 저장소를 다시 초기화한다(`core.bare=true`
      가 서고 시험 커밋이 그 가지에 얹힌다 · claude-config `7c38ef0`). 진본 뿌리를 묻는 `rev-parse` ·
      `cat-file` 도 같은 까닭으로 엉뚱한 저장소를 읽는다.

    걷을 이름은 git 이 댄다(`git rev-parse --local-env-vars`) — 손으로 적은 목록은 git 판이 오르면 낡는다.
    그 물음이 지면(git 이 없다) 걷지 않은 사본을 돌려준다 — 그때는 뒤따르는 git 호출도 어차피 진다.
    """
    import os
    import subprocess
    env = dict(os.environ)
    try:
        out = subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.SubprocessError):
        return env
    for name in out.stdout.split():
        env.pop(name, None)
    return env


def _git_tree(root):
    """검체용 git 나무 하나 — `root` 에 init 하고 빈 커밋을 하나 세워 짧은 HEAD 를 돌려준다. 못 세우면
    None(git 이 없는 기계).

    빈 커밋은 `HEAD` 를 세우려고 둔다 — 빈 나무에서 `rev-parse` 는 진다.
    ⚠ 이름·서명은 이 자리에서 박는다 — 돌리는 사람의 설정에 끌려가면 그 기계에서만 검체가 안 서고,
      그 자리는 조용히 「못 쟀다」가 된다.
    """
    import subprocess
    steps = [["init", "-q"],
             ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
              "commit", "-q", "--allow-empty", "-m", "t"]]
    try:
        for step in steps:
            if subprocess.run(["git", "-C", str(root)] + step, env=_git_env(),
                              capture_output=True, timeout=30).returncode:
                return None
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], env=_git_env(),
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _git_commit(root, msg):
    """검체 나무에 지금 글자를 한 판 더 — 짧은 해시. 못 세우면 None. 이름·서명은 `_git_tree()` 와 같은 까닭으로 박는다."""
    import subprocess
    try:
        if subprocess.run(["git", "-C", str(root), "add", "-A"], env=_git_env(), capture_output=True, timeout=30).returncode:
            return None
        if subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg], env=_git_env(),
                          capture_output=True, timeout=30).returncode:
            return None
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], env=_git_env(),
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def compare(copy_text, source_text, start):
    """사본에서 곁말 블록을 뺀 몸통과 진본을 줄끝·BOM 을 눕혀 견준다 — (같은가, 갈린 줄 수)."""
    mine = body_without_marker(copy_text, start)
    theirs = "\n".join(_lines(source_text))
    if mine == theirs:
        return True, 0
    diff = [d for d in difflib.unified_diff(theirs.split("\n"), mine.split("\n"), lineterm="", n=0)
            if d[:1] in "+-" and d[:3] not in ("+++", "---")]
    return False, len(diff)


# ── 도장 — 곁말의 판이 가리키는 진본과 사본이 맞나 ────────────────────────────
STAMP_RE = re.compile(r"\(([0-9a-f]{7,40}) 판\)")
# 진본과 같은 저장소에 사는 사본의 곁말(씨앗끼리 · 게이트웨이 씨앗의 두 사본) — 판을 따로 안 적고 지금 진본과 같다고 약속한다.
SAME_TREE = "같은 저장소"


def stamp_of(text, start):
    """곁말 블록의 도장 — `(<짧은 해시> 판)`. 없거나 해시 꼴이 아니면(「같은 저장소 · 같은 판」 · 날짜 ·
    릴리스 판 번호) None."""
    m = STAMP_RE.search("\n".join(block(text, start)))
    return m.group(1) if m else None


def _git_toplevel(seeds_root):
    """진본 뿌리를 든 git 나무의 꼭대기 — 없으면 None(홈 씨앗 · 설치본 · git 없는 기계)."""
    import subprocess
    try:
        out = subprocess.run(["git", "-C", str(seeds_root), "rev-parse", "--show-toplevel"], env=_git_env(),
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    top = out.stdout.strip()
    return Path(top).resolve() if out.returncode == 0 and top else None


def _git_blobs(toplevel, keys):
    """`<판>:<경로>` 마다 그 판의 본문 — 프로세스 하나(`cat-file --batch`)로 다 꺼낸다. 없는 것은 None.

    판마다 `git show` 를 띄우지 않는다 — 사본 수만큼 프로세스가 서고, 윈도우에서 그 값이 견줌보다 크다.
    """
    import subprocess
    out = {}
    if not keys:
        return out
    try:
        p = subprocess.run(["git", "-C", str(toplevel), "cat-file", "--batch"], env=_git_env(),
                           input=("\n".join(keys) + "\n").encode("utf-8"), capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return {k: None for k in keys}
    data, i = p.stdout, 0
    for k in keys:
        nl = data.find(b"\n", i)
        if nl < 0:
            out[k] = None
            continue
        head = data[i:nl].decode("utf-8", "replace").split()
        i = nl + 1
        if len(head) == 3 and head[2].isdigit():          # <sha> <type> <size>
            size = int(head[2])
            out[k] = data[i:i + size].decode("utf-8", "replace")
            i += size + 1
        else:                                             # <object> missing · ambiguous
            out[k] = None
    return out


def stamp_pass(good, seeds_root):
    """몸통이 맞은 사본마다 — 곁말의 판에서 꺼낸 진본과도 같은가.

    받는 것 — `survey()` 가 낸 맞은 것들 `[(파일, 곁말 줄, rel, 진본 경로)]` 과 진본 뿌리.
    돌려주는 것 — `measured`(뿌리가 git 나무였나) · `stale` [(이름, rel, 도장, 갈린 줄)] · `ok`(맞음 수) ·
    `unknown`(판이나 그 판의 파일을 나무에서 못 찾았거나 진본이 나무 밖인 줄들) · `nostamp`(판을 해시로
    안 적은 사본 이름들) · `why`(못 잰 까닭).
    **찍지 않는다** — 받는 손이 이 결과로 도장을 올린 뒤 다시 재므로, 찍는 자는 `stamp_report()` 다.
    """
    top = _git_toplevel(seeds_root)
    res = {"measured": top is not None, "stale": [], "ok": 0, "unknown": [], "nostamp": [],
           "why": "진본 뿌리가 git 나무가 아니다(홈 씨앗 · 설치본)"}
    if top is None:
        return res
    rows = []
    for p, start, rel, source in good:
        text = p.read_text(encoding="utf-8")
        st = stamp_of(text, start)
        if st is None:
            res["nostamp"].append(p.name)
            continue
        try:
            inside = source.resolve().relative_to(top).as_posix()
        except ValueError:
            res["unknown"].append(f"{p.name} (진본 {source} 이 나무 {top} 밖이다)")
            continue
        rows.append((p, start, rel, st, f"{st}:{inside}", text))
    blobs = _git_blobs(top, sorted({r[4] for r in rows}))
    for p, start, rel, st, key, text in rows:
        body = blobs.get(key)
        if body is None:
            res["unknown"].append(f"{p.name} ({st} 판 — 이 나무에 그 판이나 그 판의 파일이 없다)")
            continue
        same, n = compare(text, body, start)
        if same:
            res["ok"] += 1
        else:
            res["stale"].append((p.name, rel, st, n))
    return res


def stamp_report(st):
    if not st["measured"]:
        edge(f"**도장은 못 쟀다** — {st['why']}. 곁말의 판이 그 판의 진본과 맞나는 진본 저장소가 붙은 PC 나 "
             "CI 에서 `--seeds <진본 저장소>/seeds` 로 돌릴 때 잰다")
        return
    for name, _rel, old, n in st["stale"]:
        report(f"{name} — 도장 {old} 판의 진본과 다르다(갈린 줄 {n}) — 몸통은 지금 판을 따라왔는데 영수증만 옛 판이다",
               False, ["고치는 법: `--receive` 로 도장을 올린다"])
    if st["ok"] or st["stale"]:
        report(f"도장이 제 판의 진본과 맞는다 (맞음 {st['ok']} · 옛 도장 {len(st['stale'])})", not st["stale"])
    for row in st["unknown"]:
        edge(f"**도장의 판을 이 나무에서 못 찾았다** — {row}. 얕은 클론이거나 판이 잘못 적혔다 — 판정이 아니라 "
             "**안 잰 자리**다")
    if st["nostamp"]:
        edge(f"**판 없는 곁말** — {' · '.join(st['nostamp'])}. 「같은 저장소 · 같은 판」처럼 판을 안 적은 사본은 "
             "도장 항이 없다 — 몸통 견줌만 든다")


# ── 갈린 사본 가르기 — 손댄 것인가, 받을 판이 있는 것인가 ────────────────────────

def _same_version(a, b):
    """짧은 해시 둘이 같은 판인가 — 길이가 다를 수 있어 앞머리로 본다."""
    return bool(a and b) and (a.startswith(b) or b.startswith(a))


def triage(rows, seeds_root, ver):
    """지금 진본과 갈린 사본들을 셋으로 가른다 — 견주는 자는 지금 진본이 아니라 **곁말이 적은 판**이다.

    받는 것 — `survey()` 가 낸 갈린 것들 `[(파일, 곁말 줄, rel, 진본 경로, 갈린 줄)]` · 진본 뿌리 · 그 뿌리의 판(`_stamp`).
    돌려주는 것 — `behind` [(이름, rel, 도장, 갈린 줄)] 곁말의 판 그대로라 받을 판이 있을 뿐인 사본 · `bad`
    [(이름, rel, 갈린 줄, 까닭)] 곁말의 판과도 다른 사본 · `undecided` [(이름, rel, 까닭)] 어느 쪽인지 못 가른 사본.

    갈래 —
      · 곁말이 「같은 저장소 · 같은 판」이다 → `bad`. 지금 진본과 같다고 약속한 사본이다
      · 곁말의 판이 해시가 아니다(판을 모르는 뿌리에서 `--receive` 가 적은 받은 날짜 · 릴리스 판 번호) → `undecided`.
        그 판을 꺼낼 데가 없다
      · 뿌리가 git 나무다 → 그 판의 진본을 꺼내 견준다. 같으면 `behind`, 다르면 `bad`, 그 판을 못 찾으면 `undecided`
      · 뿌리가 git 나무가 아니다(홈 씨앗 · 설치본) → 뿌리의 판이 곁말의 판이면 지금 진본이 곧 그 판이라 `bad`,
        아니면(또는 판 모름) 옛 판을 꺼낼 데가 없어 `undecided`
    ⚠ 받을 판이 있다는 것은 받은 저장소의 결함이 아니다 — 진본이 앞서 간 것이라 빨강으로 세면 진본 저장소의 커밋마다
      받은 저장소가 붉어진다. 손댄 사본만 빨강이다.
    """
    out = {"behind": [], "bad": [], "undecided": []}
    top = _git_toplevel(seeds_root)
    keyed = []
    for p, start, rel, source, n in rows:
        st = stamp_of(p.read_text(encoding="utf-8"), start)
        if st is None and SAME_TREE in "\n".join(block(p.read_text(encoding="utf-8"), start)):
            out["bad"].append((p.name, rel, n, f"곁말이 「{SAME_TREE}」이다 — 지금 진본과 같다고 약속한 사본이다"))
        elif st is None:
            out["undecided"].append((p.name, rel, "곁말의 판이 해시가 아니라(받은 날짜 · 릴리스 판) 그 판을 꺼낼 데가 없다"))
        elif top is None:
            if _same_version(st, ver):
                out["bad"].append((p.name, rel, n, f"진본 뿌리가 곁말의 {st} 판인데 다르다"))
            else:
                out["undecided"].append((p.name, rel, f"진본 뿌리는 {ver or '판 모름'}, 곁말은 {st} 판이고 뿌리가 "
                                                     "git 나무가 아니라 그 판을 꺼낼 데가 없다"))
        else:
            try:
                inside = source.resolve().relative_to(top).as_posix()
            except ValueError:
                out["undecided"].append((p.name, rel, f"진본 {source} 이 나무 {top} 밖이다"))
                continue
            keyed.append((p, start, rel, n, st, f"{st}:{inside}"))
    blobs = _git_blobs(top, sorted({k[5] for k in keyed})) if keyed else {}
    for p, start, rel, n, st, key in keyed:
        body = blobs.get(key)
        if body is None:
            out["undecided"].append((p.name, rel, f"{st} 판 — 이 나무에 그 판이나 그 판의 파일이 없다(얕은 클론이거나 "
                                                 "판이 잘못 적혔다)"))
        elif compare(p.read_text(encoding="utf-8"), body, start)[0]:
            out["behind"].append((p.name, rel, st, n))
        else:
            out["bad"].append((p.name, rel, n, f"곁말의 {st} 판과도 다르다 — 손으로 고쳤거나 판이 틀렸다"))
    return out


# ── `.githooks/` 뿌리 찾기 — 곁 `exit_code_check.py` 가 불러 간다 ──────────────────

def hooks_root(start):
    """`.githooks/` 를 든 나무 뿌리 — 제 자리부터 위로 훑는다. 없으면 None.

    `_check/` 는 저장소마다 다른 깊이에 산다(형제는 뿌리 바로 아래 · 씨앗 저장소는
    `seeds/check/` 아래). 깊이를 박지 않고 **폴더가 나올 때까지** 올라가는 까닭이 그것이다.
    """
    start = Path(start).resolve()
    for d in [start, *start.parents]:
        if (d / HOOKS).is_dir():
            return d
    return None


# ── §1 양성 대조 — 임시 뿌리에 넷을 지어 판정이 실제로 가르는지 먼저 보인다 ────

# 실물 꼴 그대로 — 첫 줄 · 빈 줄 · 좌표 문단 · 빈 줄 · 본문. 좌표 문단 뒤에 빈 줄이 있어야
# 「문단 끝」 자리가 선다 — 없으면 받는 손이 곁말을 파일 끝에 앉혀, 받는 손 판정이 실물에 없는 꼴을 잰다.
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
        # ── 판을 읽는 차례 — 판 파일 → git 나무 → 모름. 셋이 실제로 갈리나 ──
        # 「판 모름」을 먼저 문다 — 셋째 자리가 날짜로 메워지면 판을 모르는 판정이 최신과 견준 것처럼
        # 읽힌다(`_stamp()` 머리말).
        bare = tmp / "bare-root"
        bare.mkdir()
        got = _stamp(bare)
        report("판 파일도 git 나무도 없으면 판 모름이다", got[0] is None, [repr(got)])
        (bare / VERSION_FILE).write_text("abc1234 2026-09-13\n", encoding="utf-8")
        got = _stamp(bare)
        report("판 파일이 있으면 그 첫 낱말이 판이고 날짜가 곁말로 선다",
               got[0] == "abc1234" and "2026-09-13" in got[1], [repr(got)])
        # ── 갈린 사본 가르기 · git 나무가 아닌 뿌리 — 뿌리의 판이 곁말의 판이면 손댐이고, 아니면 못 가른다 ──
        #    기대는 뜻에서 온다: 지금 진본이 곧 곁말의 판인데 다르면 그 차이는 사본에서 났다 · 판이 다르면 옛 판을
        #    꺼낼 데가 없다. 이 둘이 없으면 홈 씨앗으로 도는 커밋 훅이 진본이 앞서 갈 때마다 붉어지거나(옛 판),
        #    판이 같은 손댐까지 놓친다.
        bsrc = bare / "check" / "_check"
        bsrc.mkdir(parents=True)
        (bsrc / "_part.py").write_text(SOURCE, encoding="utf-8")
        rows = []
        for st in ("abc1234", "def5678", "2026-09-13"):
            c = tmp / f"bare_{st}.py"
            c.write_text(_copy(SOURCE, [one[0].replace("abc1234", st), one[1]], mutate="X = 3"), encoding="utf-8")
            rows.append((c, marker(c.read_text(encoding="utf-8"))[0], "seeds/check/_check/_part.py",
                         bsrc / "_part.py", 1))
        got = triage(rows, bare, "abc1234")
        report("git 나무가 아닌 뿌리 — 뿌리의 판과 같은 판의 갈린 사본은 손댐 · 다른 판과 받은 날짜는 못 가른다",
               [r[0] for r in got["bad"]] == ["bare_abc1234.py"]
               and sorted(r[0] for r in got["undecided"]) == ["bare_2026-09-13.py", "bare_def5678.py"]
               and not got["behind"], [repr(got)])
        tree = tmp / "git-root"
        tree.mkdir()
        head = _git_tree(tree)
        if head:
            got = _stamp(tree)
            report("판 파일이 없고 git 나무면 HEAD 가 판이다", got[0] == head, [repr(got), head])
            (tree / VERSION_FILE).write_text("abc1234 2026-09-13\n", encoding="utf-8")
            got = _stamp(tree)
            report("판 파일이 git 나무보다 앞선다 — 홈 사본은 제 나무의 HEAD 가 아니다",
                   got[0] == "abc1234", [repr(got), head])
            # ── 도장 — 몸통이 지금 판과 같아도 영수증이 옛 판이면 빨강인가 ──
            gsrc = tree / "seeds" / "check" / "_check"
            gsrc.mkdir(parents=True)
            (gsrc / "_part.py").write_text(SOURCE, encoding="utf-8")
            v1 = _git_commit(tree, "첫 판")
            new_source = SOURCE.replace("X = 1", "X = 1  # 둘째 판")
            (gsrc / "_part.py").write_text(new_source, encoding="utf-8")
            v2 = _git_commit(tree, "둘째 판")
            if v1 and v2:
                good = []
                for st in (v1, v2, "0000000"):
                    c = tree / f"copy_{st}.py"
                    c.write_text(_copy(new_source, [one[0].replace("abc1234", st), one[1]]), encoding="utf-8")
                    good.append((c, marker(c.read_text(encoding="utf-8"))[0],
                                 "seeds/check/_check/_part.py", gsrc / "_part.py"))
                got = stamp_pass(good, tree / "seeds")
                report("옛 판 도장은 빨강 · 지금 판 도장은 맞음 · 없는 판은 안 잰 자리다",
                       got["measured"] and [r[0] for r in got["stale"]] == [f"copy_{v1}.py"]
                       and got["ok"] == 1 and len(got["unknown"]) == 1, [repr(got)])
                got = stamp_pass(good, bare)
                report("git 나무가 아닌 뿌리에서는 도장을 못 쟀다고 말한다", not got["measured"], [repr(got)])
                # ── 갈린 사본 가르기 · git 나무 — 견주는 자는 곁말의 판이다 ──
                #    셋: 첫 판 그대로인 사본(진본만 앞서 갔다 → 받을 판) · 첫 판에서 손댄 사본(→ 어긋남) · 판 해시 없이
                #    「같은 저장소 · 같은 판」인 사본(→ 지금 진본과 같아야 하니 어긋남). 받을 판을 빨강으로 세면 진본
                #    저장소의 커밋마다 받은 저장소가 붉어지고, 손댐을 받을 판으로 세면 손으로 고친 사본이 조용히 산다.
                rows = []
                for tag, text in (
                        ("behind", _copy(SOURCE, [one[0].replace("abc1234", v1), one[1]])),
                        ("edited", _copy(SOURCE, [one[0].replace("abc1234", v1), one[1]], mutate="X = 3")),
                        ("nohash", _copy(SOURCE, [one[0].replace("abc1234", "같은 저장소 · 같은"), one[1]]))):
                    c = tree / f"drift_{tag}.py"
                    c.write_text(text, encoding="utf-8")
                    rows.append((c, marker(text)[0], "seeds/check/_check/_part.py", gsrc / "_part.py", 1))
                got = triage(rows, tree / "seeds", v2)
                report("git 나무 — 곁말의 판 그대로면 받을 판 · 그 판에서 손댔거나 판 해시가 없으면 어긋남",
                       [r[0] for r in got["behind"]] == ["drift_behind.py"]
                       and sorted(r[0] for r in got["bad"]) == ["drift_edited.py", "drift_nohash.py"]
                       and not got["undecided"], [repr(got)])
            else:
                edge("**도장 갈래는 못 쟀다** — 임시 나무에 커밋을 못 세웠다")
        else:
            edge("**git 나무 갈래는 못 쟀다** — 이 기계에 git 이 없거나 임시 나무를 못 세웠다. "
                 "그 갈래는 이 저장소 안에서 `--seeds seeds` 로 돌릴 때 실물로 밟힌다")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── §2 실물 전수 ───────────────────────────────────────────────────────────────

def collect(check_dir):
    """곁말 든 파일들 — `[(파일, 곁말 줄, 진본 상대경로|None)]`.

    하위 폴더와 UTF-8 로 안 읽히는 파일은 건너뛴다. 견주기 전에 「잴 것이 있나」를 이 자가 답한다 — 그 물음이 §1 양성 대조보다 앞에 서야 해서 읽는
    자리와 견주는 자리가 갈려 있다(머리말 「잴 수 있나를 §1 양성 대조보다 먼저 묻는다」).
    """
    out = []
    for p in sorted(Path(check_dir).iterdir()):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found = marker(text)
        if found is not None:
            out.append((p, found[0], found[1]))
    return out


def survey(found, seeds_root):
    """(지금 진본과 갈린 것들 [(파일, 곁말 줄, rel, 진본 경로, 갈린 줄)], 같음 수, 진본 없음들, 경로 못 읽음들,
    맞은 것들 [(파일, 곁말 줄, rel, 진본 경로)]). 갈린 것을 손댐 · 받을 판으로 가르는 자는 `triage()` 다.

    같은 사본마다 `= 같음` 한 줄을 찍는다 — 판정은 부르는 쪽이 세운다.
    """
    bad, same, missing, unreadable, good = [], 0, [], [], []
    for p, start, rel in found:
        if rel is None:
            unreadable.append(p.name)
            continue
        source = Path(seeds_root) / Path(rel).relative_to("seeds")
        if not source.is_file():
            missing.append(f"{p.name} → {source}")
            continue
        ok, n = compare(p.read_text(encoding="utf-8"),
                        source.read_text(encoding="utf-8"), start)
        if ok:
            same += 1
            good.append((p, start, rel, source))
            print(f"  = 같음   {p.name}  ← {rel}")
        else:
            bad.append((p, start, rel, source, n))
    return bad, same, missing, unreadable, good


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    seeds_root = DEFAULT_SEEDS
    if "--seeds" in argv:
        seeds_root = Path(argv[argv.index("--seeds") + 1]).resolve()
        args = [a for a in args if a != str(seeds_root) and Path(a).resolve() != seeds_root]
    check_dir = Path(args[0]).resolve() if args else HERE
    print(f"잴 폴더 — {check_dir}\n진본 뿌리 — {seeds_root}\n")

    # ── 전제 — 잴 수 있나를 §1 양성 대조보다 먼저 묻는다 ──
    # ⚠ 이 걸음을 `positive_control()` 뒤로 옮기지 않는다 — 못 재는 판에서도 자검 줄이 `[OK]` 로 먼저
    #   찍혀 화면이 그만큼을 잰 것처럼 보인다. 러너 홈에 씨앗이 없는 CI 가 그 판이다.
    if not seeds_root.is_dir():
        raise Unmeasured(f"[안 잼] 진본 뿌리가 없다 — {seeds_root}. 아무것도 안 쟀다(양성 대조도 "
                         "안 돌렸다 — 그 줄들은 이 나무를 잰 것이 아니라 탐지기 자검이다). 홈에 "
                         "씨앗이 안 깔렸으면 deploy.ps1 이 안 돈 것이고, 씨앗 저장소 안이면 "
                         "`--seeds seeds` 를 준다. CI 러너처럼 홈에 씨앗이 없는 자리면 이 검사는 "
                         "그 판에서 재는 자가 아니다")
    found = collect(check_dir)
    if not found:
        raise Unmeasured(f"[안 잼] 곁말 든 파일이 한 장도 없다 — {check_dir}. 아무것도 안 쟀다. "
                         "빌려 온 것이 없으면 잴 것이 없고, 있는데 곁말이 없으면 이 자에게는 "
                         "남이다(씨앗 저장소 제 나무가 그 자리다 — 거기는 진본이지 사본이 아니다)")

    positive_control()
    # 자검이 몇 건이었나 — **손으로 안 적는다.** 아래 초록 줄이 자검과 실물을 갈라 찍는다.
    self_test = len(passes()) + len(fails())

    print("\n--- §2 실물 전수 — 곁말 든 사본이 진본과 같은가")
    ver, where = _stamp(seeds_root)
    print(f"진본 판 — {ver or '모름'} ({where})")
    drift, same, missing, unreadable, good = survey(found, seeds_root)
    stamps = stamp_pass(good, seeds_root)
    if (drift or stamps["stale"]) and "--receive" in argv:
        # 곁말의 판 자리는 사람이 읽는 영수증이라 판을 모르면 받은 날짜를 적는다 — 판정 줄은 그 날짜를
        # 안 쓴다(돌린 날은 진본의 판이 아니다 · `_stamp()` 머리말).
        stamp = ver or datetime.date.today().isoformat()
        # 손댄 사본 · 받을 판 · 못 가른 것을 가리지 않고 받는다 — 받는 손의 뜻은 「이 뿌리의 지금 판으로 맞춘다」다
        for copy_path, at, rel, source, _n in drift:
            receive(copy_path, source, at, stamp)
            print(f"  ← 받았다 {copy_path.name}  ← {rel} ({stamp} 판)")
        for name, rel, old, _n in stamps["stale"]:
            copy_path = check_dir / name
            at = marker(copy_path.read_text(encoding="utf-8"))
            receive(copy_path, Path(seeds_root) / Path(rel).relative_to("seeds"), at[0], stamp)
            print(f"  ← 도장 올림 {name}  ({old} → {stamp} 판)")
        n_stale = len(stamps["stale"])
        edge(f"**받았다** — 갈린 사본 {len(drift)}장을 진본으로 놓고 옛 도장 {n_stale}장을 {stamp} 판으로 올렸다. 아래는 받은 뒤의 판정이다")
        # 받으면 곁말 줄이 밀린다 — 다시 걷어야 그 뒤의 견줌이 제 자리를 본다
        drift, same, missing, unreadable, good = survey(collect(check_dir), seeds_root)
        stamps = stamp_pass(good, seeds_root)
    split = triage(drift, seeds_root, ver)
    bad, behind, undecided = split["bad"], split["behind"], split["undecided"]

    # 센티널 — 곁말은 있는데 견준 것이 0 이면 어긋남도 0 이라 아무것도 안 잰 초록이 난다. 진본을 한 장도
    # 못 찾은 판(홈에 씨앗이 안 깔린 PC · 뿌리를 잘못 준 판)이 그렇다 — 그 판은 「못 쟀다」다.
    if not (same or bad or behind):
        raise Unmeasured(f"[안 잼] 곁말 든 파일 {len(found)}장 중 손댐을 가른 것이 0 이다 — 진본 없음 {len(missing)} · "
                         f"경로 못 읽음 {len(unreadable)} · 판이 달라 못 가름 {len(undecided)}. "
                         f"진본 뿌리 {seeds_root} 가 맞는가 — 진본 저장소의 `seeds` 를 `--seeds` 로 주면 가른다")
    for name, rel, n, why in bad:
        report(f"{name} — 진본 {rel} 과 어긋남", False, [f"갈린 줄 {n} · {why}"])
    report(f"곁말 든 사본이 곁말의 판과 같다 — 손댄 사본이 없다 (지금 판과 같음 {same} · 받을 판이 있음 "
           f"{len(behind)} · 어긋남 {len(bad)} · 못 가름 {len(undecided)} · 진본 판 {ver or '모름'})", not bad)
    stamp_report(stamps)
    for name, _rel, st, n in behind:
        edge(f"**받을 판이 있다** — {name}: 곁말의 {st} 판 그대로이고 지금 진본({ver or '판 모름'})과 갈린 줄 {n}. "
             "이 저장소의 결함이 아니다 — 받는 손은 `--receive`")
    for name, _rel, why in undecided:
        edge(f"**손댄 것인지 받을 판인지 못 가른다** — {name}: {why}. 판정이 아니라 **안 잰 자리**다 — 진본 저장소의 "
             "`seeds` 를 `--seeds` 로 주면 가른다")

    for row in missing:
        edge(f"**진본이 없다** — {row}. 곁말이 가리키는 자리에 파일이 없다 — 옮겨졌거나 곁말이 낡았다")
    for row in unreadable:
        edge(f"**곁말은 있는데 `seeds/…` 경로가 없다** — {row}. 진본을 씨앗 밖(형제 앱)에 두는 파일이면 "
             "그것이 맞고 이 자는 남이다 — 씨앗에서 받은 것이면 곁말이 낡았다")
    if missing or unreadable:
        edge("진본이 없거나 경로를 못 읽은 파일은 판정이 아니라 **안 잰 자리**다 — 위 건수에서 빠져 있다")

    edge(f"잰 범위 — `{check_dir.name}/` 의 곁말 든 파일 {same + len(bad) + len(behind)}장. "
         "곁말 없이 베낀 사본은 안 든다 — 그것은 갈림을 세우는 자(`drift_check` 류)의 몫이다")
    if ver is None:
        edge(f"**진본의 판을 모른다** — {where}. 이 판정은 「지금 이 뿌리와 같다」까지고 "
             f"**그 뿌리가 낡았나는 안 잰 자리다** — 홈에 씨앗을 미는 자가 그 자리에 "
             f"`{VERSION_FILE}` 을 남긴다(`deploy.ps1` 의 「씨앗의 판 줄」 칸 · 세션 훅 "
             "`deploy_home_norms` 의 씨앗 칸 · 설치기 `install.ps1`). 셋 가운데 하나를 한 번 돌린다")
    else:
        edge(f"**견준 진본은 {ver} 판이다** ({where}) — 그 판이 진본 나무의 최신인가는 "
             "이 자가 안 문다. 판을 찍는 것이 그 물음의 재료다")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 (진본 판 {ver or '모름'}) — {' · '.join(fails())}")
        print("고치는 법: 진본에서 다시 받는다(`--receive`). 사본을 고쳐야 했다면 그 고침은 진본으로 올린다")
        return EXIT_MISMATCH
    print(f"전부 통과 (판정 {len(passes())}건 — 양성 대조 {self_test} · 실물 전수 "
          f"{len(passes()) - self_test}) — 견준 진본 판 {ver or '모름'}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
