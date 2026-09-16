"""자식 프로세스의 말이 부모에게 성히 건너오나 — 해독 계약을 실물 자식으로 잰다.

좌표 — 이 절은 아뜰리에 #209 의 ⑤(기전)에서 왔다. 씨앗으로 뗀 자리와 사유는 결정 0040 ·
claude-config #25(2026-09-13 실측 — 어느 저장소에서나 도는 것 18장 중 하나가 이 절이었다)가 든다.

    python -X utf8 _check/child_decode_check.py                    # 기전만 (기본)
    python -X utf8 _check/child_decode_check.py <파일…>            # + 부모 쪽 소스 전수
    python -X utf8 _check/child_decode_check.py --child <파일…>    # + 자식 쪽 소스 전수

**왜 이 검사가 있나.** 어느 저장소에서나 `subprocess` 로 자식을 부르면 같은 병이 난다. 부모가
`encoding=` 만 주고 `errors=` 를 안 주면 해독이 **엄격**해지고, 자식의 통로가 utf-8 이 아닌 판으로
서면(`PYTHONUTF8` 없는 한글 Windows 가 그렇다) 그 자리에서 **자식이 남긴 실패 까닭이 통째로
사라진다** — 까닭이 필요한 바로 그 자리에서. 방아쇠는 자식의 말버릇이 아니라 **그 나무가 앉은
자리**라, 스크립트가 한글을 한 자도 안 써도 역추적이 제 경로를 찍기만 하면 걸린다.

재는 것 — 기전 하나가 늘 서고, 소스 축 셋은 인자가 세운다:

  **기전** — 자식을 진짜로 띄워 갈래 다섯(A∼E)과 성공 한 줄을 잰다. 자식 통로를
    `PYTHONIOENCODING` 으로 눕혀 「utf-8 로 못 읽는 바이트」를 실제로 내게 하므로, 그 판의
    콘솔이 없는 기계에서도 **같은 기전**이 선다.
  ㉠ **부모 쪽**(인자) — 준 파일의 글자로 받는 `subprocess` 호출이 `encoding=` 을 드나.
  ㉡ **부모 쪽**(인자) — 그 호출이 `errors=` 를 들어 **관대하게** 읽나.
  ㉢ **자식 쪽**(`--child`) — 준 파일이 제 stdout·stderr 를 utf-8 로 세우나.

⚠ **어느 파일이 부모이고 어느 파일이 자식인가는 이 검사가 안 가른다** — 의미 판단이라 인자로
  받는다. 원본의 ①∼④ 는 그 저장소의 서버 함수·콘솔층·수확기·굽는 자를 **이름으로** 잡는 절이라
  여기 안 산다. 그중 익명이 되는 축 셋만 위 꼴로 섰다.

⚠ **근거 대고 뺄 자리는 곁 선언 `child_decode.conf` 의 `[skip]` 이 든다** — 열쇠는
  `파일이름:라벨` 이고, 라벨은 그 자리를 **감싼 def·class 의 점 이름**이다(아무것도 안 감싼
  자리는 `<module>` · 자식 쪽 ㉢ 은 통로 이름 `stdout`·`stderr`). 판정 줄이 찍는 글자가 곧
  열쇠다. 줄 번호로 쥐던 옛 꼴(`server.py:51`)은 위에 한 줄만 나도 밀려 **뺀 자리가 조용히
  옮겨 갔다** — 그 꼴로 적힌 열쇠는 안 물고 경계에 이름을 대고 찍는다(claude-config #45 ⑤).

⚠ **양성 대조가 실물 판정보다 먼저 선다.** 인자를 주면 §1 이 일부러 어긋난 검체 넷과 제 꼴
  셋으로 탐지기가 무는지 보이고, 기전은 갈래 A(엄격 부모가 까닭을 잃는다)가 제 양성 대조다.
  자식 통로가 안 누우면 초록이 아니라 「못 쟀다」(2)로 나간다.

⚠ **부모 쪽 판정은 값을 안 문다** — `encoding`·`errors` 가 **있나**까지다. 어떤 판으로 읽어야
  하나는 그 저장소가 정한다. 자식 쪽은 값을 문다 — 부모가 utf-8 로 읽으려면 자식이 utf-8 로
  내야 하고, 그 짝은 기전의 갈래 C 가 잰다.

**안 재는 것** — 진짜 비-utf8 콘솔 창에서의 모양(재현한 것은 「자식 통로가 다른 판으로 선다」는
같은 기전이지 그 OS 자체가 아니다) · 바이트로 받는 호출(해독이 없어 잃을 말도 없다) ·
`from subprocess import run` 꼴(점 이름으로만 찾는다) · 그 호출이 **실제로** 무엇을 받나(소스
축은 원문의 꼴까지다 — 돌려 보지 않는다) · 그 저장소의 기록층·콘솔층이 판정 줄을 잃나(구조가
저장소마다 달라 이름으로 잡을 자리가 없다).

토큰도 망도 브라우저도 안 쓴다.
"""
import ast
import configparser
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report, show

HERE = Path(__file__).resolve().parent

# 자식 통로를 눕히는 판 — **utf-8 로 못 읽는 바이트를 내는 판이면 무엇이든 된다.** cp949 인
# 까닭은 이 병이 처음 난 자리가 한글 Windows 라서지, 그 판이어야 기전이 서는 것은 아니다.
CHILD_CODEC = "cp949"
TIMEOUT = 60
# 자식의 말을 **글자로** 받는 손들 — 점 이름으로만 찾는다.
DECODERS = ("subprocess.run", "subprocess.Popen", "subprocess.check_output")
# 이 낱말 중 하나라도 있으면 그 호출은 바이트가 아니라 글자를 받는다 — 곧 해독이 있다.
TEXT_KEYS = ("text", "universal_newlines", "encoding")
STREAMS = ("stdout", "stderr")
# 곁 선언의 **열쇠가 되는 라벨** — 감싼 def·class 의 점 이름이고, 아무것도 안 감싼 자리는 이것.
MODULE_LABEL = "<module>"
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

REASON = "자식이 남긴 실패 까닭 — 총량 34건 ≠ 실제 12건"   # 자식이 눕기 전에 남기는 말
DONE = "자식이 낸 성공 한 줄 — 12건 처리"                   # 자식이 성할 때 내는 말


# ── 소스를 읽는 자 ────────────────────────────────────────────────────────────

def _calls(node, dotted):
    """그 트리 아래의 `dotted` 호출 전부 — `subprocess.run` 처럼 점 이름으로 찾는다."""
    return [n for n in ast.walk(node)
            if isinstance(n, ast.Call) and ast.unparse(n.func) == dotted]


def _kw(call, name):
    """그 호출의 키워드 인자 값 — 없으면 None, 상수면 값 그대로."""
    for k in call.keywords:
        if k.arg == name:
            return k.value.value if isinstance(k.value, ast.Constant) else ast.unparse(k.value)
    return None


def _has(call, name):
    return any(k.arg == name for k in call.keywords)


def _labels(tree):
    """노드 → **그 자리를 감싼 def·class 의 점 이름.** 모듈 자리는 `MODULE_LABEL`.

    곁 선언이 근거 대고 뺄 자리를 가리키는 **열쇠**가 이 이름이다. 줄 번호는 위에 한 줄만
    나도 밀려, 뺀 자리가 조용히 다른 자리로 옮겨 가거나 아무 데도 안 가리키게 된다 —
    형제 `record_names_gen` 이 통로를 셀 때 줄이 아니라 라벨로 세는 까닭이 같다.
    """
    out = {id(tree): MODULE_LABEL}

    def walk(node, path):
        for child in ast.iter_child_nodes(node):
            here = path + [child.name] if isinstance(child, SCOPES) else path
            out[id(child)] = ".".join(here) or MODULE_LABEL
            walk(child, here)

    walk(tree, [])
    return out


def judge_parent(src, name):
    """부모 쪽 원문 한 장 — `(어긋남들, 잴 자리 수)`. 제 꼴이면 빈 목록."""
    tree = ast.parse(src)
    where = _labels(tree)
    out, sites = [], 0
    for dotted in DECODERS:
        for call in _calls(tree, dotted):
            if not any(_has(call, k) for k in TEXT_KEYS):
                continue          # 바이트로 받는다 — 해독이 없어 잃을 말도 없다
            sites += 1
            if not _has(call, "encoding"):
                out.append((name, where[id(call)], call.lineno, "㉠",
                            f"`{dotted}` 이 해독 판을 안 박았다 — 기계의 기본판을 따라가 "
                            "자리마다 다른 글자가 온다"))
            if not _has(call, "errors"):
                out.append((name, where[id(call)], call.lineno, "㉡",
                            f"`{dotted}` 이 엄격하게 읽는다 — 자식이 남긴 까닭이 "
                            "해독에서 걸려 통째로 사라진다"))
    return out, sites


def judge_child(src, name):
    """자식 쪽 원문 한 장 — `(어긋남들, 잴 자리 수)`. 두 통로를 다 본다."""
    tree = ast.parse(src)
    out = []
    for stream in STREAMS:
        call = _calls(tree, f"sys.{stream}.reconfigure")
        got = _kw(call[0], "encoding") if call else None
        if len(call) != 1 or got != "utf-8":
            # ㉢ 의 라벨은 **통로 이름**이다 — 한 파일에 통로마다 판정이 하나씩이고, 아예 안
            # 세운 판에는 감쌀 자리조차 없다(줄 0). 감싼 이름을 쓰면 둘이 한 열쇠로 겹친다.
            out.append((name, stream, call[0].lineno if call else 0, "㉢",
                        f"{stream} 를 utf-8 로 안 세운다 — {len(call)}건 · encoding={got!r}"))
    return out, len(STREAMS)


# ── §1 양성·음성 대조 ─────────────────────────────────────────────────────────

BAD_PARENT = [
    ("㉠", "해독 판을 안 박았다", """
import subprocess
subprocess.run(["x"], capture_output=True, text=True, errors="replace")
"""),
    ("㉡", "엄격하게 읽는다 — 이 한 낱말이 까닭을 지운다", """
import subprocess
subprocess.run(["x"], capture_output=True, text=True, encoding="utf-8", timeout=60)
"""),
]

GOOD_PARENT = """
import subprocess
subprocess.run(["x"], capture_output=True, text=True, encoding="utf-8", errors="replace")
"""

BYTES_PARENT = """
import subprocess
subprocess.run(["x"], capture_output=True)
"""

BAD_CHILD = """
import sys
print(1)
"""

HALF_CHILD = """
import sys
sys.stdout.reconfigure(encoding="utf-8")
"""

GOOD_CHILD = """
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
"""

# 곁 선언이 쥘 **열쇠**가 줄이 아니라 이름인가 — 감싼 def 가 있는 검체.
LABELLED_PARENT = """
import subprocess
def _build_stamp():
    subprocess.run(["git", "rev-parse"], capture_output=True, text=True, encoding="utf-8")
"""
LABELLED_NAME = "_build_stamp"


def positive_control():
    print("--- §1 양성 대조 — 탐지기가 볼 줄 아나 (이게 빨가면 아래 초록은 다 무의미하다)")
    for want, said, src in BAD_PARENT:
        got, sites = judge_parent(src, "<검체>")
        report(f"부모 {want} {said}",
               len(got) == 1 and got[0][3] == want and sites == 1,
               [f"{len(got)}건 · 갈래 {[r[3] for r in got]} · 잴 자리 {sites}곳 "
                f"(기대 {want} 하나)"])
    got, _ = judge_child(BAD_CHILD, "<검체>")
    report("자식 ㉢ 두 통로를 다 안 세운 자를 짚는다", len(got) == len(STREAMS),
           [f"{len(got)}건 · 기대 {len(STREAMS)}"])
    got, _ = judge_child(HALF_CHILD, "<검체>")
    report("자식 ㉢ 한 통로만 세운 자를 짚는다 — 빠진 stderr 가 보인다", len(got) == 1,
           [f"{len(got)}건 · 갈래 {[r[3] for r in got]} (기대 하나)"])

    # ── 곁 선언의 열쇠 — **줄이 아니라 라벨이다.** 줄로 쥐면 편집마다 밀린다(#45 ⑤) ──
    got, _ = judge_parent(LABELLED_PARENT, "<검체>")
    report(f"부모 판정의 라벨은 감싼 def 이름이다 — `{LABELLED_NAME}`",
           [r[1] for r in got] == [LABELLED_NAME], [repr(got)])
    got, _ = judge_parent(BAD_PARENT[0][2], "<검체>")
    report(f"아무것도 안 감싼 자리의 라벨은 `{MODULE_LABEL}` 이다",
           [r[1] for r in got] == [MODULE_LABEL], [repr(got)])
    got, _ = judge_child(BAD_CHILD, "<검체>")
    report("자식 ㉢ 의 라벨은 통로 이름이다 — 둘이 한 열쇠로 안 겹친다",
           [r[1] for r in got] == list(STREAMS), [repr(got)])

    print("\n--- §2 음성 대조 — 제 꼴과 대상 아닌 자는 안 문다")
    got, sites = judge_parent(GOOD_PARENT, "<제 꼴>")
    report("부모가 판을 박고 관대하게 읽으면 어긋남 0 이다", not got and sites == 1,
           [f"{len(got)}건 · 잴 자리 {sites}곳"])
    got, sites = judge_parent(BYTES_PARENT, "<바이트로 받는 자>")
    report("바이트로 받는 호출은 대상이 아니다 — 해독이 없어 잃을 말도 없다",
           not got and not sites, [f"{len(got)}건 · 잴 자리 {sites}곳"])
    got, _ = judge_child(GOOD_CHILD, "<제 꼴>")
    report("자식이 두 통로를 utf-8 로 세우면 어긋남 0 이다", not got, [f"{len(got)}건"])


# ── §3 기전 — 실물 자식으로 잰다 ──────────────────────────────────────────────

# ⚠ **실물이 내는 꼴만 낸다.** 자식은 실패하면 눕고(`sys.exit`) 성공 한 줄은 그 뒤에 찍는다 —
#   그래서 실패 판에서는 stdout 이 비어 부모의 `stdout or stderr` 가 stderr 를 집는다. 검체가
#   둘을 같이 내면 실물이 절대 안 만드는 꼴이 되고, 그 위의 판정은 멀쩡한 코드를 빨갛게 만든다.
KID_SRC = '''\
import sys, pathlib
pathlib.Path(sys.argv[2]).write_text(
    f"{{sys.stdout.encoding}} {{sys.stdout.errors}}", encoding="utf-8")
if sys.argv[1] == "fixed":                     # 고친 자식과 같은 손질
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
if sys.argv[3] == "fail":
    sys.exit({reason!r})                       # 실물과 같은 차례 — 찍기 전에 눕는다
print({done!r})
'''.format(reason=REASON, done=DONE)

# 자식이 **뜨기도 전에** 죽는 갈래 — 자식 손질로는 원리적으로 못 덮는다(손질하는 줄에 닿기
# 전에 죽는다). 역추적이 제 파일 경로를 찍으므로, 한글 폴더에 앉은 나무는 스크립트가 한글을
# 한 자도 안 써도 걸린다 — 「앉은 자리가 방아쇠」라는 말이 이 모양이다.
EARLY_SRC = 'raise RuntimeError("자식이 못 선다")\n'


def mechanism():
    """자식을 진짜로 띄워 잰다 — 통로를 못 눕히면 그 까닭을 돌려준다(아니면 None)."""
    tmp = Path(tempfile.mkdtemp(prefix="child-decode-"))
    # 엄격 부모의 해독은 **읽개 스레드 안에서** 터지는 판이 있다. 그 판의 파이썬은 역추적을
    # stderr 로 쏟고 `run()` 은 조용히 돌아오는데, 그 역추적이 곧 이 검사가 세우려는 **증거**다.
    # 쏟게 두면 초록 판에 남의 빨강처럼 보이는 글이 얹히므로, 받아서 A 의 경계로 돌린다.
    thread_errs = []
    prev_hook = threading.excepthook
    threading.excepthook = lambda args: thread_errs.append(args.exc_type.__name__)
    try:
        kid = tmp / "자식.py"              # 경로에 한글 — 역추적이 이 이름을 찍는다
        kid.write_text(KID_SRC, encoding="utf-8")
        early = tmp / "일찍죽는자식.py"
        early.write_text(EARLY_SRC, encoding="utf-8")
        probe = tmp / "probe.txt"

        def call(script, mode="fixed", outcome="fail", **kw):
            """부모가 자식을 읽는 그 계약 — 잴 인자만 세운다.

            ⚠ `errors=` 를 여기서 안 박는 것이 **일부러다** — 엄격 부모가 이 검사의 검체이고,
              관대한 판은 부르는 자리가 `errors="replace"` 로 준다.
            """
            env = dict(os.environ, PYTHONIOENCODING=CHILD_CODEC)
            # utf-8 모드가 켜져 있으면 통로가 안 눕는다 — 켜진 기계에서 조용히 안 재이는 자리.
            env.pop("PYTHONUTF8", None)
            thread_errs.clear()
            try:
                p = subprocess.run([sys.executable, str(script), mode, str(probe), outcome],
                                   env=env, capture_output=True, text=True,
                                   encoding="utf-8", timeout=TIMEOUT, **kw)
                said = p.stdout or p.stderr or ""       # 부모가 까닭을 집는 그 식
                return said, (" · ".join(thread_errs) or None)
            except Exception as exc:                    # noqa: BLE001
                return "", type(exc).__name__

        # 검체가 정말 누웠나 — 아니면 아래 판정은 아무것도 안 잰 초록이 된다.
        call(kid, "bare", errors="replace")
        stood = probe.read_text(encoding="utf-8") if probe.is_file() else "(안 남음)"
        if not stood.startswith(CHILD_CODEC):
            edge(f"자식이 {stood!r} 로 섰다 — 이 판에서는 「utf-8 로 못 읽는 바이트」가 "
                 "안 나와 아래 기전 판정이 성립하지 않는다.")
            return f"자식 통로를 {CHILD_CODEC} 로 못 세웠다 — 자식이 {stood!r} 로 섰다"
        show("검체가 선 통로 — 「utf-8 이 아닌 판」이 재현됐다", stood, f"{CHILD_CODEC} strict")

        said_a, raised_a = call(kid, "bare")                    # A 옛 자식 · 엄격 부모
        said_b, _ = call(kid, "bare", errors="replace")         # B 옛 자식 · 관대 부모
        said_c, _ = call(kid, "fixed", errors="replace")        # C 고친 자식 · 관대 부모
        said_ok, _ = call(kid, "fixed", "ok", errors="replace")  # C' 성공 한 줄도 성한가
        said_d, _ = call(early, "bare")                         # D 일찍 죽음 · 엄격 부모
        said_e, _ = call(early, "bare", errors="replace")       # E 일찍 죽음 · 관대 부모

        print("  A 옛 자식 · 엄격 부모 — **오늘의 병** (이 절의 양성 대조)")
        report("A: 부모가 해독에서 걸려 까닭이 통째로 사라진다", REASON not in said_a,
               [f"까닭이 살아 있다 — 이 검사가 재려던 병이 이 판에 없다: {said_a!r}"])
        edge(f"A 가 잃는 모양은 판마다 다르다 — 이 자리에서는 {raised_a or '조용한 빈손'}. "
             "읽개가 딴 스레드인 판에서는 `run()` 이 **안 울고** `stdout` 이 None 으로 오고, "
             "부르는 자리에서 터지는 판에서는 예외가 올라온다. **둘 다 까닭이 사라진다** — "
             "이 검사가 드는 것은 그 하나다.")

        print("  B 옛 자식 · 관대 부모 — 부모 혼자로는 반쪽")
        report("B: 부모가 안 죽고 무언가는 건너온다 — 기능은 산다", bool(said_b),
               [f"빈손이다: {said_b!r}"])
        report("B: 그래도 까닭은 **성히 못 온다** — 자식이 다른 판으로 냈으니 글자가 뭉개진다",
               REASON not in said_b, [f"성히 왔다: {said_b!r}"])
        edge(f"B 가 건네는 것: {said_b.strip()[:34]!r}… — 「기능은 산다, 잃는 것은 말이다」가 "
             "이 줄이고, **자식 손질이 왜 따로 필요한가**도 이 줄이다.")

        print("  C 고친 자식 · 관대 부모 — 둘을 합쳐야 낫는다")
        report("C: 자식이 남긴 실패 까닭이 **글자 그대로** 건너온다", REASON in said_c,
               [f"실제 {said_c!r}", f"기대에 든 말 {REASON!r}"])
        report("C': 성공 한 줄도 성히 온다 — 사람이 읽는 그 글이다", DONE in said_ok,
               [f"실제 {said_ok!r}"])

        print("  D·E 자식이 뜨기도 전에 죽는 갈래 — 자식 손질로 **원리적으로** 못 덮는다")
        report("D: 엄격 부모면 역추적의 한글 경로에서 걸려 **아무것도 안 남는다**",
               said_d == "", [f"무언가 남았다: {said_d!r}"])
        report("E: 관대 부모면 역추적의 뼈대(예외 이름·줄)가 남아 **진단이 된다** — "
               "부모의 `errors=` 는 자식 손질의 중복이 아니다",
               "RuntimeError" in said_e and "Traceback" in said_e, [f"실제 {said_e!r}"])
        edge("E 에서 한글 부분은 뭉개진 채 온다 — 자식이 손질에 닿기 전에 죽어서다. 여기서 "
             "부모가 지키는 것은 **까닭의 글자가 아니라 까닭의 존재**다: D 의 빈손(아무 단서 "
             "없음)과 E 의 역추적(어디서 무엇이 터졌나) 사이의 차이.")
        return None
    finally:
        threading.excepthook = prev_hook
        shutil.rmtree(tmp, ignore_errors=True)   # 뒷정리가 판정을 죽이지 않게


# ── §4 소스 전수 ──────────────────────────────────────────────────────────────

def survey(paths, judge):
    bad, seen, sites, unreadable = [], 0, 0, []
    for raw in paths:
        p = Path(raw)
        try:
            got, n = judge(p.read_text(encoding="utf-8-sig"), p.name)
        except (OSError, SyntaxError) as exc:
            unreadable.append(f"{p.name} — {type(exc).__name__}: {exc}")
            continue
        seen += 1
        sites += n
        bad += got
    return bad, seen, sites, unreadable


def parse(args):
    """인자를 두 봉투로 — 맨 파일은 부모 쪽, `--child` 뒤는 자식 쪽."""
    parent, child = [], []
    bucket = parent
    for a in args:
        if a == "--child":
            bucket = child
        elif a == "--parent":
            bucket = parent
        elif a.startswith("-"):
            raise Unmeasured(f"[안 잼] 모르는 인자 {a!r} — 어떻게 주나: 부모 쪽 파이썬 원문은 "
                             "그냥 늘어놓고 자식 쪽은 `--child` 뒤에 둔다")
        else:
            bucket.append(a)
    return parent, child


CONF = "child_decode.conf"
# 옛 꼴 열쇠 — 라벨 자리에 줄 번호가 앉은 것. 안 물고 **이름을 대고** 경계로 찍는다.
OLD_KEY = re.compile(r":\d+$")


def _skips():
    """곁 선언 `[skip]` — `파일이름:라벨 = 까닭`. 근거 대고 빼는 자리다 — 씨앗은 선언을 안 싣는다.

    **라벨은 그 자리를 감싼 def·class 의 점 이름**이다(`server.py:_build_stamp`). 아무것도 안
    감싼 자리는 `<module>` 이고, 자식 쪽 ㉢ 은 통로 이름(`stdout`·`stderr`)이 라벨이다 — 열쇠는
    이 검사가 판정 줄에 찍는 글자 그대로다.

    ⚠ **옛 열쇠는 줄 번호였다**(`server.py:51`). 위에 한 줄만 나도 밀려, 뺀 자리가 조용히 다른
      자리로 옮겨 가거나 아무 데도 안 가리키게 된다 — 근거 대고 뺀 것이 눈감은 것이 되는
      자리다(claude-config #45 ⑤). 옛 꼴로 적힌 열쇠는 안 물고 **경계에 이름을 대고 찍는다.**

    옛 판(아뜰리에)은 「답이 ASCII 라」 `git rev-parse` 한 자리를 산문으로 뺐고, 씨앗의 넓은 그물은
    그 자리를 문다. 빼는 것은 되, **까닭이 판정 옆에 찍혀야** 한다 — 눈감은 자리와 갈리게.
    """
    conf = HERE / CONF
    if not conf.is_file():
        return {}
    # ⚠ 구분자를 `=` 하나로 — 기본값은 `:` 도 구분자라 `파일:줄` 열쇠가 `파일` 에서 잘린다(실측).
    cp = configparser.ConfigParser(interpolation=None, delimiters=("=",))
    cp.optionxform = str
    cp.read(conf, encoding="utf-8")
    return dict(cp["skip"]) if cp.has_section("skip") else {}


def sweep(what, paths, judge):
    """한 축의 전수 — 판정 하나와 경계를 찍는다. 곁 선언이 뺀 자리는 까닭과 함께 경계로."""
    bad, seen, sites, unreadable = survey(paths, judge)
    skips = _skips()
    kept, skipped = [], []
    for row in bad:
        key = f"{row[0]}:{row[1]}"
        (skipped if key in skips else kept).append(row)
    bad = kept
    for rel, label, lineno, _kind, _said in skipped:
        edge(f"**근거 대고 뺐다** — {rel}:{label} (줄 {lineno}) · {skips[f'{rel}:{label}']}")
    for key in sorted(k for k in skips if OLD_KEY.search(k)):
        edge(f"**옛 꼴 열쇠라 안 물었다** — `[skip]` 의 `{key}` 는 줄 번호로 적혀 있다. "
             f"라벨(`파일:감싼 이름`)로 고친다 — 판정 줄이 찍는 글자 그대로다")
    if not seen:
        raise Unmeasured(f"[안 잼] {what} 파일을 한 장도 못 읽었다 — 어떻게 주나: "
                         "파이썬 원문의 경로를 준다")
    # 센티널 — 잴 자리가 0 이면 어긋남도 0 이라 **아무것도 안 잰 초록**이 난다. 준 목록이
    # 틀렸거나 그 파일들이 애초에 자식을 안 부르는 것이고, 둘 다 초록으로 낼 말이 아니다.
    if not sites:
        raise Unmeasured(f"[안 잼] {what} 잴 자리가 0 곳이다 (파일 {seen}장) — 어떻게 주나: "
                         "자식을 부르는(또는 자식으로 불리는) 원문을 준다")
    for rel, label, lineno, kind, said in bad:
        report(f"{rel}:{label} (줄 {lineno}) — {kind}", False, [said])
    report(f"{what} 계약을 어기는 자리가 없다 (파일 {seen}장 · 잴 자리 {sites}곳)", not bad)
    for row in unreadable:
        edge(f"**못 읽은 파일** — {row} · 판정이 아니라 **안 잰 자리**다")


def main(argv):
    parent_files, child_files = parse(argv[1:])
    for raw in parent_files + child_files:
        if not Path(raw).is_file():
            raise Unmeasured(f"[안 잼] 준 자리가 파일이 아니다 — {raw!r}. 어떻게 주나: "
                             "부모 쪽은 그냥 늘어놓고 자식 쪽은 `--child` 뒤에 둔다")
    scan = bool(parent_files or child_files)
    print(f"소스 축 — 부모 쪽 {len(parent_files)}장 · 자식 쪽 {len(child_files)}장 "
          "(인자가 세운다)\n")

    if scan:
        positive_control()
        print()

    print("--- §3 기전 — 자식을 진짜로 띄워 잰다 (그 판의 콘솔 없이도 같은 병이 선다)")
    why = mechanism()

    if scan:
        print("\n--- §4 소스 전수 — 준 파일이 계약을 지키나")
        if parent_files:
            sweep("부모 쪽", parent_files, judge_parent)
        if child_files:
            sweep("자식 쪽", child_files, judge_child)
            edge("**자식 쪽이 stderr 까지 드는 까닭** — 자식의 실패 까닭은 눕는 손과 역추적, "
                 "곧 stderr 로만 나간다. stdout 만 세우면 성공 한 줄은 성히 오고 **까닭만** "
                 "뭉개져, 잘 돌 때는 아무 표시도 안 난다.")
    else:
        edge("**소스 축 셋은 안 들었다** — 부모 쪽·자식 쪽 파일을 한 장도 안 줬다. 어느 파일이 "
             "그 자리인가는 의미 판단이라 이 검사가 안 고른다.")

    edge("**원본의 ①∼④ 는 안 들었다** — 그 저장소의 서버 함수·콘솔층·수확기·굽는 자를 "
         "**이름으로** 잡는 절이라 여기 안 산다. 익명이 되는 축 셋만 인자 받는 꼴로 섰다.")
    edge("**부모 쪽은 값을 안 문다** — `encoding`·`errors` 가 있나까지다. 어떤 판으로 읽어야 "
         "하나는 그 저장소가 정한다.")
    edge("**`from subprocess import run` 꼴은 안 문다** — 점 이름으로만 찾는다.")
    edge(f"**진짜 비-utf8 콘솔 창에서의 모양은 안 잰다** — 재현한 것은 「자식 통로가 "
         f"{CHILD_CODEC} 로 선다」는 같은 기전이지 그 OS 자체가 아니다.")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        return EXIT_MISMATCH
    if why:
        raise Unmeasured(f"[안 잼] {why} — 어떻게 주나: `PYTHONUTF8`·`PYTHONIOENCODING` 이 "
                         "바깥에서 박혀 있지 않은 자리에서 돌린다\n"
                         "   양성 대조와 소스 축은 통과했다. 기전만 안 잰 것이다.")
    print(f"전부 통과 (판정 {len(passes())}건 — 기전 갈래 A∼E 와 성공 한 줄 · "
          f"소스 전수 부모 {len(parent_files)}장 · 자식 {len(child_files)}장)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
