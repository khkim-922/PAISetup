"""초록 줄이 「몇 건을 쟀나」를 파생으로 찍나 — 판정을 세우고도 `passes()` 를 안 읽는 검사를 문다.

좌표 — 규율은 `_verdict.py` 머리말(「그 건수를 손으로 적지 않는다」)과 곁 `README.md` 폴더 규율 ⑥ ·
이 자가 선 까닭은 claude-config #25(실측 2026-09-13: 아뜰리에 검사 16장이 판정을 세우면서
`passes` 를 안 들였고, 그중 둘은 손글자 건수가 우연히 맞아 있었다).

    python -X utf8 _check/verdict_line_check.py            # 이 폴더
    python -X utf8 _check/verdict_line_check.py <폴더>     # 잴 `_check/` 를 지정

**왜 이 검사가 있나.** 「전부 통과」는 *여기까지* 통과다 — 무엇을 쟀나(건수)가 초록 줄에 안 서면
전부로 읽힌다. 그런데 그 건수를 손으로 적으면 절이 통째로 사라져도 글자는 그대로고 종료코드도
0 그대로라, **판정이 줄어든 것을 볼 자가 없다.** `_verdict.passes()` 가 이번 판에서 실제로 선
판정을 세는 까닭이 그것인데, 판정은 세우면서 그 계수를 안 읽는 파일이 생긴다 — 새 검사가 옛
검사를 베껴 나면 그 자리가 그대로 따라온다.

재는 것 둘 —

  ① **판정을 세우는데 계수를 안 읽는다** — `report(`·`show(` 를 부르면서 `passes` 를 한 번도
     안 부른다. 초록 줄이 건수를 찍을 재료가 그 파일에 없다.
  ② **초록 줄에 아라비아 숫자가 손글자로 앉았다** — 「전부 통과」 뒤 같은 상수 조각에 리터럴
     숫자. **괄호만 물지 않는다** — 옛 그물은 「전부 통과 바로 뒤 괄호 안」만 봐서 줄표·쉼표·
     콜론·맨공백 꼴(`전부 통과 — 판정 20건`)을 초록으로 보냈다(claude-config #45 ⑤ · 현행범은
     없었고 그물만 좁았다). `f"…{len(passes())}건…"` 은 상수 조각에 숫자가 없어 안 걸린다 —
     그것이 옳은 꼴이다.

⚠ **양성 대조가 판정보다 먼저 선다.** §1 이 일부러 어긋난 검체 둘과 제 꼴 하나로 둘이 실제로
  무는지 보이고, 파일을 한 장도 못 읽으면 「못 쟀다」(2)로 나간다.

**안 재는 것** — **머리말(docstring)에 적힌 꼴**(어긋난 꼴을 *말하는* 자리라 물면 받는 자가 제
머리말을 문다 — `_docstrings()` 가 그 자리를 뺀다) · 한국어 수사(「다섯 항」·「계약 아홉」)로 적은 범위(글자가 곧 뜻이라 기계가
못 가른다 — 그 자리는 사람이 읽는다) · `.mjs`·`.sh`(이 자는 파이썬 AST 만 읽는다 — `.mjs` 의
초록 줄은 곁 `shell_exit_check.py` ⑤ 가 물고 `.sh` 는 아직 무는 자가 없다) · 판정을 안 세우는
파일(재는 자 · 부품 — 계수를 읽을 까닭이 없다) · 초록 줄의 **범위**가 맞는 말인가(건수가
파생이어도 곁말은 손글자다).

토큰도 망도 브라우저도 안 쓴다.
"""
import ast
import re
import sys
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report

HERE = Path(__file__).resolve().parent
SUFFIX = ".py"
JUDGES = ("report", "show")          # 판정을 세우는 손 — `edge`·`unmeasured` 는 계수에 안 든다
COUNTER = "passes"
# 「전부 통과」 **뒤에 구분자 한 자 이상**(빈칸·괄호·줄표·쉼표·콜론)이 오고, 그 뒤 같은 줄에
# 리터럴 숫자가 앉은 자리. 구분자를 요구하는 까닭은 「전부 통과다」처럼 낱말이 이어지는 자리와
# 가르기 위해서고, 괄호에 안 가두는 까닭은 초록 줄이 괄호로만 범위를 다는 것이 아니어서다.
HAND_DIGIT = re.compile(r"전부 통과[\s\(（—–,，:：-]+[^\n\)）]*?\d")


def _called(tree, name):
    """그 이름을 부르는 자리가 있나 — 맨이름(`passes()`)과 속성(`_verdict.passes()`) 둘 다."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name) and f.id == name:
                return True
            if isinstance(f, ast.Attribute) and f.attr == name:
                return True
    return False


def _docstrings(tree):
    """머리말로 선 글자 조각들 — **무는 자리에서 뺀다.**

    머리말은 이 검사가 *무엇을 무나를 말하는* 자리다. 거기 적은 어긋난 꼴(「전부 통과 — 판정
    20건」)을 그대로 물면 **받는 자가 제 머리말을 문다** — 곁 `borrowed_check.py` 가 굵은 꼴
    곁말만 무는 것이 같은 자리다. 초록 줄은 찍히는 글자지 머리말이 아니다.
    """
    out = set()
    for n in ast.walk(tree):
        if not isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        first = n.body[0] if n.body else None
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                and isinstance(first.value.value, str):
            out.add(id(first.value))
    return out


def _hand_digits(tree):
    """「전부 통과 … 숫자」 꼴의 상수 조각 — (줄, 글자). 구분자는 괄호에 안 매인다."""
    said = _docstrings(tree)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                and id(n) not in said and HAND_DIGIT.search(n.value):
            out.append((n.lineno, n.value.strip()[:60]))
    return out


def judge(src, rel):
    """원문 한 장의 어긋남들 — `(파일, 줄, 갈래, 말)`. 제 꼴이면 빈 목록."""
    tree = ast.parse(src)
    out = []
    judges = any(_called(tree, j) for j in JUDGES)
    if judges and not _called(tree, COUNTER):
        out.append((rel, 0, "①", "판정을 세우는데 `passes()` 를 한 번도 안 읽는다 — 초록 줄이 건수를 파생할 재료가 없다"))
    for lineno, text in _hand_digits(tree):
        out.append((rel, lineno, "②", f"초록 줄에 숫자가 손글자로 앉았다 — {text!r}"))
    return out, judges


# ── §1 양성 대조 ───────────────────────────────────────────────────────────────

BAD = [
    ("①", "판정을 세우고 계수를 안 읽는다", """
from _verdict import fails, report
report("하나", True)
print("전부 통과" if not fails() else "어긋남")
"""),
    # ⚠ 검체의 손글자를 **이 파일에서는 이어 붙여** 둔다 — 한 상수로 두면 이 검사가 제 검체를 문다.
    #   검체 원문은 이어 붙인 결과라 그대로 한 상수이고, 그래서 판정 ② 가 문다.
    ("②", "초록 줄 숫자가 손글자다 — 괄호 꼴", """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과 (판정 """ + """20건 — 넷·셋)" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    # ⚠ 아래 셋이 **이 판에서 넓힌 자리**다 — 옛 그물은 괄호만 물어 이 꼴들을 초록으로
    #   보냈다(#45 ⑤). 검체를 안 세우면 넓힌 그물이 도로 좁아져도 볼 자가 없다.
    ("②", "초록 줄 숫자가 손글자다 — 줄표 꼴", """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과 — 판정 """ + """20건" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    ("②", "초록 줄 숫자가 손글자다 — 콜론 꼴", """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과: 판정 """ + """20건" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    ("②", "초록 줄 숫자가 손글자다 — 쉼표 꼴", """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과, 판정 """ + """20건" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    ("②", "초록 줄 숫자가 손글자다 — 구분자 없이 빈칸 하나", """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과 """ + """20건" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
]

GOOD = """
from _verdict import fails, passes, report, show
report("하나", True)
show("둘", 1, 1)
print(f"✅ 전부 통과 (판정 {len(passes())}건 — 계약 아홉)" if not fails() else f"{len(fails())}건")
"""

PART = """
FAILS = []
def helper(x):
    return x
"""


def positive_control():
    print(f"--- §1 양성 대조 — 일부러 어긋난 검체 {len(BAD)}이 정말 빨개지나")
    for want, said, src in BAD:
        got, _ = judge(src, "<검체>")
        report(f"{want} {said}", len(got) == 1 and got[0][2] == want,
               [f"{len(got)}건 · 갈래 {[r[2] for r in got]} (기대 {want} 하나)"])
    print("\n--- §2 음성 대조 — 제 꼴과 부품은 안 문다")
    clean, judges = judge(GOOD, "<제 꼴>")
    report("파생 건수와 한국어 범위는 어긋남 0 이다", not clean and judges,
           [f"{r[0]}:{r[1]} {r[2]} {r[3]}" for r in clean])
    clean, judges = judge(PART, "<부품>")
    report("판정을 안 세우는 부품은 대상이 아니다", not clean and not judges)


# ── §3 실물 전수 ───────────────────────────────────────────────────────────────

def survey(check_dir):
    bad, seen, judged, unreadable = [], 0, 0, []
    for p in sorted(Path(check_dir).iterdir()):
        if not (p.is_file() and p.suffix == SUFFIX):
            continue
        try:
            got, judges = judge(p.read_text(encoding="utf-8-sig"), p.name)
        except (OSError, SyntaxError) as exc:
            unreadable.append(f"{p.name} — {type(exc).__name__}: {exc}")
            continue
        seen += 1
        judged += 1 if judges else 0
        bad += got
    return bad, seen, judged, unreadable


def main(argv):
    check_dir = Path(argv[1]).resolve() if len(argv) > 1 else HERE
    print(f"잴 폴더 — {check_dir}\n")
    positive_control()

    print("\n--- §3 실물 전수 — 이 폴더의 검사가 건수를 파생하나")
    bad, seen, judged, unreadable = survey(check_dir)
    if not seen:
        raise Unmeasured(f"[안 잼] 읽은 파일이 0 이다 — {check_dir} 에 파이썬 원문이 없다")

    for rel, lineno, kind, said in bad:
        report(f"{rel}:{lineno} — {kind}", False, [said])
    report(f"건수를 파생 못 하는 검사가 없다 (파일 {seen}장 · 판정을 세우는 파일 {judged}장)", not bad)

    for row in unreadable:
        edge(f"**못 읽은 파일** — {row}")
    edge(f"잰 범위 — `{check_dir.name}/*.py` {seen}장. `.mjs`·`.sh` 는 안 든다 — 파이썬 AST 만 "
         "읽는다. `.mjs` 의 초록 줄은 곁 `shell_exit_check.py` ⑤ 가 든다")
    edge("**한국어 수사로 적은 범위는 안 문다** — 「계약 아홉」이 열이 돼도 여기는 초록이다. 그 자리는 사람이 읽는다")
    edge("**범위가 맞는 말인가는 안 잰다** — 건수가 파생이어도 곁말은 손글자다")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        return EXIT_MISMATCH
    print(f"전부 통과 (판정 {len(passes())}건 — 양성 {len(BAD)} · 음성 2 · 실물 전수 1)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
