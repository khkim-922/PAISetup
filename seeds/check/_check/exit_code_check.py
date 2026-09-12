"""검사가 종료코드를 계약에서 받나 — 뭉개는 문자열 · 계약 밖 값 · 손글자 2 · main 의 return 을 문다.

좌표 — 계약의 뜻은 곁 `README.md` §종료코드 가 들고, 숫자와 「못 쟀다」 손은 `_verdict.py` 가 든다.
이 자가 난 자리는 AI-prompt-helper `_check/exit_code_check.py`(725d548)이고, 그 판으로 아뜰리에가
어긋남 32건을 쟀다(atelier #347). **세 벌로 갈리기 전에 여기로 올렸다** — `_verdict.py` 가 이미
간 길이다(claude-config #23). ④ 는 claude-config #25 의 실측에서 왔다 — 아뜰리에 19장·57자리가
`return 2` 로 나가는데 옛 판은 「어긋남 0」 초록을 냈다.

    python -X utf8 _check/exit_code_check.py            # 이 폴더
    python -X utf8 _check/exit_code_check.py <폴더>     # 잴 `_check/` 를 지정 (병렬 작업나무)

**왜 이 검사가 있나.** 종료코드(0 쟀고 맞다 · 1 어긋났다 · 2 못 쟀다)는 훅과 CI 가 읽는 **유일한
말**이다 — 화면 문구는 아무도 안 읽는다. 그래서 그 갈림이 곧 계약인데, 계약을 어겨도 **아무 데서도
안 터진다**: 화면은 그대로 맞는 말을 하고 코드만 조용히 틀리므로 사람이 보는 자리에서는 영영 안
걸린다. 계약은 곁 `README.md` §종료코드 가 세우고 숫자는 `_verdict` 가 쥐지만, **검사가 그 계약을
지키나**를 세는 자는 따로 있어야 한다. 여기가 그 자리다.

재는 것 셋 — 셋 다 다른 사고다:

  ① **문자열로 나가는 자리** — `raise SystemExit("글자")` · `sys.exit("글자")`. 파이썬은 그 글자를
     stderr 로 찍고 **무조건 1** 로 나간다. 화면은 「[안 잼]」이라고 맞는 말을 하는데 훅·CI 만
     조용히 「어긋났다」로 읽는다 — **못 쟀다가 판정으로 새는 자리다.**
  ② **계약 밖 값** — 0·1·2 아닌 정수로 나간다. 훅이 갈래를 못 가르고, 못 가른 것을 대개
     「0 이 아니니 어긋남」으로 뭉갠다 — ① 과 끝이 같다.
  ③ **손글자 2** — 「못 쟀다」를 정수 리터럴로 짓는다. **숫자의 진본은 계약 하나다**
     (`_verdict.EXIT_UNMEASURED` · `Unmeasured`). 리터럴로 적으면 그 뜻이 그 파일 안에서만 살고,
     계약이 움직여도 그 자리는 안 따라온다. 그리고 그 자리를 읽은 다음 사람이 ① 로 넘어가는
     길이 여기서 열린다 — 숫자를 손으로 적어도 되면 글자도 적어도 될 것처럼 보인다.
  ④ **나가는 함수의 `return`** — `sys.exit(main())` 꼴에서는 `main` 의 `return` 이 곧 종료코드다.
     옛 판은 `sys.exit` 의 인자가 호출식이라 「못 가름」으로 건너뛰었고, 그 함수 안의 `return 2` ·
     `return "글자"` 는 ①·③ 과 같은 사고인데 한 자리도 안 걸렸다. **`sys.exit(f(…))`·
     `raise SystemExit(f(…))` 가 부르는 함수의 `return` 을 나가는 자리로 센다** — 그 함수 안에
     둥지 튼 함수의 `return` 은 안 센다(그것은 나가는 값이 아니다).

⚠ **양성 대조가 판정보다 먼저 선다.** 어긋남 0 은 그 자체로 초록이 아니다 — 수집이 통째로 죽어도
  0 이 난다. §1 이 **일부러 어긋난 검체 일곱**으로 셋이 실제로 무는지 보이고, §2 가 제 꼴은 안
  무는지 보인다. 파일을 한 장도 못 읽으면 초록이 아니라 「못 쟀다」(2)로 나간다.

⚠ **무는 것은 「어떤 꼴로 적혔나」까지다.** 그 검사가 *실제로 그 코드로 나가나*는 못 잰다 — 돌려
  보지 않고 원문만 읽는다. 그래도 값이 있는 것은 계약을 어기는 **꼴** 셋이 다 원문에 보이기
  때문이다: 나가는 자리는 숨을 데가 없다.

**안 재는 것** — 리터럴 `0`·`1`(화면과 코드가 안 갈려 조용히 안 뭉개진다. ① 의 사고가 여기는
없다) · 인자 없는 `raise SystemExit`(값이 없어 갈래를 못 가른다) · **`.mjs`·`.sh`·`.ps1`**(파이썬
AST 만 읽는다 — 그 갈래의 `process.exit`·`exit` 는 무는 자가 없다) · `sys.exit` 에 안 물린
함수의 `return`(어느 함수가 나가는 함수인지는 `sys.exit(f())` 가 말한다) · `_check/` 밖의 검사
(검사와 생성기가 섞여 사는 폴더는 파일 목록으로 전수를 못 뜬다 — **어디인지는 저장소가 제
지도에 적는다**) · **문자열 안에 든 자식 코드**(`subprocess` 로 띄우는 조각은 AST 에 안
보인다) · 계약 상수를 물어 놓고 **엉뚱한 값에 이름만 맞춘 자리**(`EXIT_OK = 2` 같은 자리 —
이름을 믿는다).

토큰도 망도 브라우저도 안 쓴다.
"""
import ast
import sys
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report, show

HERE = Path(__file__).resolve().parent

CONTRACT = (0, 1, 2)        # 진본은 곁 `README.md` §종료코드
UNMEASURED_CODE = 2         # 이 값만 문다 — 0·1 은 위 「안 재는 것」이 든다
SUFFIX = ".py"

# 계약이 내놓은 **제 손**. 세기는 하고 **판정은 안 한다** — 이 손은 글자를 받는 것이 계약이고
# (까닭을 사람에게 들려 보낸다) 종료코드는 `_verdict` 가 숫자로 쥔다. 여기에 ① 을 대면
# 계약이 권하는 꼴이 곧 어긋남으로 뜬다.
SANCTIONED = ("raise Unmeasured",)


# ── 나가는 자리를 원문에서 찾는다 ──────────────────────────────────────────────

def _is_name(node, want):
    return isinstance(node, ast.Name) and node.id == want


def exit_sites(tree):
    """나가는 자리 전부 — `sys.exit(…)` · `exit(…)` · `raise SystemExit(…)` · `raise Unmeasured(…)`.

    `raise SystemExit(2)` 는 `Raise` 로만 센다 — 그 안의 `Call` 을 또 세면 한 자리가 두 번
    걸려 건수가 부풀고, 부푼 건수는 「몇 자리를 쟀나」를 도로 거짓말로 만든다.

    **계약의 제 손(`Unmeasured`)도 센다** — 안 세면 「나가는 자리 N곳」이 실제보다 적어져
    잰 범위가 부풀어 보인다. 판정은 `judge` 가 `SANCTIONED` 로 비켜 세운다.
    """
    for n in ast.walk(tree):
        if isinstance(n, ast.Raise) and n.exc is not None:
            exc = n.exc
            if isinstance(exc, ast.Call) and _is_name(exc.func, "SystemExit"):
                yield n.lineno, "raise SystemExit", (exc.args[0] if exc.args else None)
            elif _is_name(exc, "SystemExit"):
                yield n.lineno, "raise SystemExit", None
            elif isinstance(exc, ast.Call) and _is_name(exc.func, "Unmeasured"):
                yield n.lineno, "raise Unmeasured", (exc.args[0] if exc.args else None)
        elif isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Attribute) and f.attr == "exit"
                    and _is_name(f.value, "sys")):
                yield n.lineno, "sys.exit", (n.args[0] if n.args else None)
            elif _is_name(f, "exit"):
                yield n.lineno, "exit", (n.args[0] if n.args else None)
    # ④ 나가는 함수의 `return` — `sys.exit(f(…))`·`raise SystemExit(f(…))` 가 부르는 f 안에서
    for fn in exiting_functions(tree):
        for r in _own_returns(fn):
            yield r.lineno, f"return ({fn.name})", r.value


def exiting_functions(tree):
    """`sys.exit(f(…))` · `exit(f(…))` · `raise SystemExit(f(…))` 가 부르는 이름의 함수 정의들."""
    names = set()
    for n in ast.walk(tree):
        arg = None
        if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) and _is_name(n.exc.func, "SystemExit"):
            arg = n.exc.args[0] if n.exc.args else None
        elif isinstance(n, ast.Call):
            f = n.func
            if ((isinstance(f, ast.Attribute) and f.attr == "exit" and _is_name(f.value, "sys"))
                    or _is_name(f, "exit")):
                arg = n.args[0] if n.args else None
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
            names.add(arg.func.id)
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name in names]


def _own_returns(fn):
    """그 함수 **제 몸**의 `return` — 둥지 튼 함수·람다·클래스 안은 안 내려간다."""
    stack = list(fn.body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(n, ast.Return) and n.value is not None:
            yield n
        stack.extend(ast.iter_child_nodes(n))


def values(node):
    """나가는 값의 갈래 — **삼항이면 양쪽을 다 센다.**

    `sys.exit(EXIT_MISMATCH if bad else EXIT_OK)` 가 이 저장소의 흔한 꼴이라, 한쪽만 보면
    나머지 쪽에 숨은 손글자를 놓친다.
    """
    if node is None:
        yield "없음", None
    elif isinstance(node, ast.IfExp):
        yield from values(node.body)
        yield from values(node.orelse)
    elif isinstance(node, ast.JoinedStr):
        yield "문자열", "f-문자열"
    elif isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, str):
            yield "문자열", v
        elif isinstance(v, bool):          # 참거짓이 정수보다 먼저다 — `True` 도 int 다
            yield "참거짓", v
        elif isinstance(v, int):
            yield "정수", v
        elif v is None:
            yield "없음", None
        else:
            yield "그밖", v
    elif isinstance(node, (ast.Name, ast.Attribute)):
        yield "이름", ast.unparse(node)
    else:
        yield "못 가름", ast.unparse(node)


def judge(src, rel):
    """원문 한 장의 어긋남들 — `(파일, 줄, 갈래, 말)`. 제 꼴이면 빈 목록."""
    out = []
    for lineno, how, arg in exit_sites(ast.parse(src)):
        if how in SANCTIONED:
            continue
        for kind, val in values(arg):
            if kind == "문자열":
                out.append((rel, lineno, "①",
                            f"`{how}` 가 문자열로 나간다 — 파이썬이 그것을 stderr 로 찍고 "
                            "무조건 1 로 나간다. 「못 쟀다」가 판정으로 샌다"))
            elif kind == "정수" and val == UNMEASURED_CODE:
                out.append((rel, lineno, "③",
                            f"`{how}({val})` — 「못 쟀다」를 손글자로 짓는다. 숫자의 진본은 "
                            "계약 하나다(`EXIT_UNMEASURED` · `Unmeasured`)"))
            elif kind == "정수" and val not in CONTRACT:
                out.append((rel, lineno, "②",
                            f"`{how}({val})` — 계약 밖 값이다. 계약은 0·1·2 뿐이다"))
    return out


def count_sites(src):
    """그 원문에 나가는 자리가 몇이나 — 「무엇을 쟀나」의 건수다."""
    return sum(1 for _ in exit_sites(ast.parse(src)))


# ── §1 양성 대조 — 일부러 어긋난 검체로 셋이 무는지 먼저 보인다 ────────────────

BAD = [
    ("①", "문자열로 나간다", """
import sys
sys.exit("못 쟀다 — 검체가 없다")
"""),
    ("①", "`raise` 로 문자열이 나간다", """
raise SystemExit("못 쟀다 — 검체가 없다")
"""),
    ("①", "f-문자열로 나간다", """
import sys
why = "검체가 없다"
sys.exit(f"못 쟀다 — {why}")
"""),
    ("②", "계약 밖 값으로 나간다", """
import sys
sys.exit(3)
"""),
    ("③", "손글자 2 로 나간다", """
import sys
sys.exit(2)
"""),
    ("③", "`raise` 로 손글자 2 가 나간다", """
raise SystemExit(2)
"""),
    ("③", "삼항의 **한쪽**이 손글자 2 다", """
import sys
sys.exit(2 if left else 0)
"""),
    ("③", "나가는 함수(main)의 `return 2` 다", """
import sys
def main():
    if not_ready:
        return 2
    return EXIT_OK
sys.exit(main())
"""),
    ("①", "나가는 함수(main)가 문자열을 돌려준다", """
import sys
def main(argv):
    return "못 쟀다"
raise SystemExit(main(sys.argv))
"""),
]

GOOD = """
import sys
from _verdict import EXIT_MISMATCH, EXIT_OK, EXIT_UNMEASURED, Unmeasured

REFUSED = EXIT_UNMEASURED

def main():
    def inner():
        return 2          # 둥지 튼 함수 — 나가는 값이 아니다
    if bad:
        return 1 if bad else 0
    return EXIT_OK

def helper():
    return 2              # sys.exit 에 안 물린 함수 — 이 자는 안 문다

if not_ready:
    raise Unmeasured("[안 잼] 검체가 없다")
if fenced:
    sys.exit(REFUSED)
if left:
    sys.exit(EXIT_UNMEASURED)
sys.exit(EXIT_MISMATCH if bad else EXIT_OK)
sys.exit(main())
sys.exit(0)
sys.exit(1)
raise SystemExit
"""


def positive_control():
    """검체가 실제로 그 꼴인지부터 묻는다 — 이 절이 빨강이면 아래 §3 의 0 은 뜻이 없다."""
    print(f"--- §1 양성 대조 — 일부러 어긋난 검체 {len(BAD)}이 정말 빨개지나")
    for want, said, src in BAD:
        got = judge(src, "<검체>")
        report(f"{want} {said}",
               len(got) == 1 and got[0][2] == want,
               [f"{len(got)}건 · 갈래 {[r[2] for r in got]} (기대 {want} 하나)"])

    print("\n--- §2 음성 대조 — 제 꼴은 한 자리도 안 문다")
    clean = judge(GOOD, "<제 꼴>")
    report("계약을 지킨 원문은 어긋남 0 이다", not clean,
           [f"{r[0]}:{r[1]} {r[2]} {r[3]}" for r in clean])
    # 열인 까닭 — `sys.exit` 여섯(`REFUSED` · `EXIT_UNMEASURED` · 삼항 · `main()` · 0 · 1) +
    # 인자 없는 `raise SystemExit` 하나 + 계약의 제 손 `raise Unmeasured` 하나 + 나가는 함수
    # `main` 제 몸의 `return` 둘(둥지 튼 `inner` 와 안 물린 `helper` 는 안 센다). **제 손까지
    # 세는 것이 요점이다** — 안 세고 비켜 세우면 「안 문다」와 「못 본다」가 한 칸에 뭉개진다.
    show("  그 원문에서 센 「나가는 자리」", count_sites(GOOD), 10)
    edge("**음성 대조가 이 판의 값을 절반 든다** — 양성만 보이면 「전부 빨강」인 자도 "
         "만점을 받는다. 위 건수가 0 으로 떨어지면 잴 것이 없어진 것이므로 함께 문다.")


# ── §3 실물 전수 ───────────────────────────────────────────────────────────────

def sources(check_dir):
    """이 폴더의 파이썬 원문 — 하위 폴더는 안 본다(검체·기록이다).

    **밑줄로 시작하는 부품도 든다.** `_fake_cli.py` 는 담에 걸린 판을 「못 쟀다」로 내보내고
    `_verdict.py` 는 계약 자신을 들므로, 둘이야말로 이 계약을 먼저 지켜야 하는 자리다.
    """
    return sorted(p for p in Path(check_dir).iterdir()
                  if p.is_file() and p.suffix == SUFFIX)


def survey(check_dir):
    """(어긋남들, 읽은 파일 수, 나가는 자리 수, 못 읽은 파일들)."""
    bad, seen, sites, unreadable = [], 0, 0, []
    for p in sources(check_dir):
        try:
            src = p.read_text(encoding="utf-8-sig")
            bad += judge(src, p.name)
            sites += count_sites(src)
        except (OSError, SyntaxError) as exc:
            unreadable.append(f"{p.name} — {type(exc).__name__}: {exc}")
            continue
        seen += 1
    return bad, seen, sites, unreadable


def main(argv):
    check_dir = Path(argv[1]).resolve() if len(argv) > 1 else HERE
    print(f"잴 폴더 — {check_dir}\n")

    positive_control()

    print("\n--- §3 실물 전수 — 이 폴더의 검사·부품이 계약을 지키나")
    bad, seen, sites, unreadable = survey(check_dir)

    # 센티널이 먼저다 — 한 장도 못 읽은 판은 어긋남 0 이 나도 초록이 아니다.
    if not seen:
        raise Unmeasured(f"[안 잼] 읽은 파일이 0 이다 — {check_dir} 에 파이썬 원문이 없다. "
                         "어긋남 0 은 이 판에서 아무 뜻도 없다")

    for rel, lineno, kind, said in bad:
        report(f"{rel}:{lineno} — {kind}", False, [said])
    report(f"계약을 어기는 자리가 없다 (파일 {seen}장 · 나가는 자리 {sites}곳)", not bad)

    if unreadable:
        for row in unreadable:
            edge(f"**못 읽은 파일** — {row}")
        edge("못 읽은 파일은 판정이 아니라 **안 잰 자리**다 — 위 건수에서 빠져 있다.")

    edge(f"잰 범위 — `{check_dir.name}/*.py` {seen}장의 **나가는 자리 {sites}곳**. "
         "하위 폴더와 `_check/` 밖의 검사는 안 든다 — 그 경계는 저장소의 지도가 든다.")
    edge("**리터럴 `0`·`1` 은 안 문다** — 화면과 코드가 안 갈려 조용히 뭉개지는 사고가 "
         "거기는 없다. 그래서 `sys.exit(1)` 을 손글자로 적은 자리는 이 초록에 안 든다.")
    edge("**`.mjs`·`.sh`·`.ps1` 은 안 든다** — 파이썬 AST 만 읽는다. 그 갈래의 나가는 자리는 무는 자가 없다.")
    edge("**「그 코드로 실제로 나가나」는 안 잰다** — 원문의 꼴까지다. 돌려 보지 않는다.")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        return EXIT_MISMATCH
    print(f"전부 통과 (판정 {len(passes())}건 — 양성 {len(BAD)} · 음성 2 · 실물 전수 1)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
