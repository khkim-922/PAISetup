"""검사가 종료코드 계약과 초록 줄 건수를 지키나 — 파이썬은 AST 로, 노드·셸·파워셸은 글자 꼴로 문다.

층 — 만드는 사람의 흐름
걷는 조건 — 검사가 나가는 자리와 초록 줄을 공용 부품의 손으로만 내서 맨 나가는 자리와 손글자 건수가 남지 않으면 걷는다

좌표 — 계약의 뜻은 곁 `README.md` §종료코드 가, 숫자와 「못 쟀다」 손은 `_verdict.py` 가 든다 · 씨앗 규율은
claude-config 결정 0040 · 무엇을 남기고 걷나는 결정 0148(스킬 check-design) — 판정 셋을 이 한 벌로 합치고 손글자
2 판정을 걷은 자리는 claude-config #170 · atelier #445 다.

    python -X utf8 _check/exit_code_check.py            # 이 폴더 + 이 나무의 `.githooks/`
    python -X utf8 _check/exit_code_check.py <폴더>     # 잴 `_check/` 를 지정 (병렬 작업나무)

내는 것 — 0 계약을 지킨다 · 1 어긋난 자리가 있다(`파일:줄 — 갈래` 와 고칠 말) · 2 읽은 원문이 한 장도 없다.
곁 검사가 불러 쓰는 손이 하나 있다 — `blank(원문, 확장자)` 가 `.mjs`·`.sh`·`.ps1` 의 주석과 문자열을 자리째
걷어 `(걷어 낸 사본, 걷어 낸 문자열들)` 을 낸다(`from exit_code_check import blank`). 이름과 꼴을 지킨다.

**왜 이 검사가 있나.** 훅과 CI 가 읽는 말은 종료코드(0 쟀고 맞다 · 1 어긋났다 · 2 못 쟀다) 하나고, 그 계약은
언어를 안 가린다. 계약을 어겨도 화면은 맞는 말을 하고 코드만 조용히 틀려 사람이 보는 자리에서는 안 걸린다 —
「못 쟀다」가 「어긋났다」로 새면 빨강이 소음이 되고, 소음이 된 빨강은 아무도 안 읽는다. 초록 줄의 건수도
같다 — 손으로 적은 수는 판정 절이 통째로 사라져도 그대로라 판정이 준 것을 볼 자가 없다.

재는 것 다섯 — 원문 한 장을 한 번 읽어(파이썬은 AST 한 벌, 셋은 걷은 사본 한 벌) 다섯을 같이 본다:

  ① **문자열로 나간다** — `.py` 의 `sys.exit("글자")` · `raise SystemExit("글자")` · `.mjs` 의
     `process.exit("글자")`. 파이썬은 그 글자를 찍고 무조건 1 로 나가고, 노드는 그 값을 계약의 셋으로 못 읽는다.
  ② **계약 밖 값** — 네 갈래 다. 0·1·2 아닌 정수로 나가면 훅이 갈래를 못 가르고 대개 「어긋남」으로 뭉갠다.
  ③ **인자 없이 나간다** — `.mjs` 의 `process.exit()` 는 `process.exitCode`(안 세우면 0)로 나가 뜻 없이 초록이 난다.
  ④ **판정을 세우고 계수를 안 읽는다** — `.py` 가 `report(`·`show(` 를 부르면서 `passes` 를 한 번도 안 부른다.
     초록 줄이 건수를 파생할 재료가 그 파일에 없다.
  ⑤ **초록 줄 건수가 손글자다** — `.py` 는 「전부 통과」 뒤 같은 상수 조각의 숫자, `.mjs` 는 `console.log` 안
     「통과」 문구 속 「숫자+셈낱말」. 건수는 `len(passes())` · `${…length}` 가 센다.

**나가는 자리를 세는 법** — `.py` 는 `sys.exit(…)` · `exit(…)` · `raise SystemExit(…)` 에 더해 `sys.exit(f(…))` ·
`raise SystemExit(f(…))` 가 부르는 함수 **제 몸의** `return` 을 센다 — 그 값이 곧 종료코드다(둥지 튼 함수의
`return` 은 나가는 값이 아니다). 삼항이면 가지를 다 본다. 셋은 주석 · 문자열 · 정규식 · 헤어독 · 해어스트링을
자리째 공백으로 걷은 사본에서 꼴을 찾고 값은 원문에서 읽는다.

**경계가 이 폴더만이 아니다** — 0·1·2 를 실제로 내는 `.sh` 는 커밋 게이트 조각이고 그것은 나무의 `.githooks/` 에
산다. 그래서 제 자리에서 위로 올라가 `.githooks/` 아래 셸 원문을 같이 문다 — 확장자 없는 몸통은 첫 줄의 `#!` 로
갈래를 정하고, 셔뱅도 확장자도 없는 선언은 저절로 빠진다. 찾는 손은 곁 `borrowed_check.py` 가 든다 — 그 파일이
곁에 없는 폴더에서는 이 팔을 안 잰 자리로 찍는다.

⚠ **리터럴 `0`·`1`·`2` 는 안 문다** — 숫자는 계약(곁 `README.md` §종료코드)이 못박았고 리터럴은 그 수로 바르게
  나간다. 이름으로 쓰라고 무는 판정은 멀쩡한 코드를 고치게 할 뿐 결함을 못 잡는다(결정 0148 · 스킬 check-design 2 절).

⚠ **양성 대조가 판정보다 먼저 선다.** §1 이 갈래마다 일부러 어긋난 검체로 다섯이 정말 무는지, §2 가 네 갈래의
  제 꼴은 안 무는지 **센 자리 수까지**, §2' 가 심은 나무에서 원문을 정말 집는지 보인다. 원문을 한 장도 못 읽으면
  초록이 아니라 「못 쟀다」(2)로 나간다.

**안 재는 것** — 인자 없는 `raise SystemExit` · `sys.exit()`(값이 없어 갈래를 못 가른다) · `.sh`·`.ps1` 의 인자 없는
`exit`(`$?` 로 나가는데 그 값은 원문에 없다) · `sys.exit` 에 안 물린 함수의 `return` · `process.exitCode = N` 꼴 ·
`.mjs` 템플릿 `${…}` 속 코드 · 따옴표를 든 정규식을 문자열로 잘못 읽은 판(따옴표가 안 닫혀 「못 읽은 파일」로
빠진다) · `.sh`·`.ps1` 의 초록 줄 · 머리말(docstring)에 적힌 꼴 · 한국어 수사로 적은 건수(「계약 아홉」 — 글자가
곧 뜻이라 사람이 읽는다) · 「못 쟀다」의 갈래 선택(못 잰 것을 0 으로 내보내는 셸 자리는 세기만 한다) · 문자열 안에
든 자식 코드 · 계약 상수에 엉뚱한 값을 단 자리(`EXIT_OK = 2` — 이름을 믿는다) · `_check/` 의 하위 폴더와
`.githooks/` 밖 · **그 코드로 실제로 나가나**(돌려 보지 않고 원문만 읽는다).

토큰도 망도 브라우저도 안 쓴다.
"""
import ast
import re
import shutil
import sys
import tempfile
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report, show

HERE = Path(__file__).resolve().parent

CONTRACT = (0, 1, 2)        # 진본은 곁 `README.md` §종료코드
UNMEASURED_CODE = 2         # 셈에만 쓴다 — 「못 쟀다」 갈래가 있는 셸 원문을 센다(판정이 아니다)
PY = ".py"
SHELLS = (".mjs", ".sh", ".ps1")

# 계약이 내놓은 **제 손**. 세기는 하고 판정은 안 한다 — 이 손은 글자를 받는 것이 계약이고(까닭을 사람에게
# 들려 보낸다) 종료코드는 `_verdict` 가 숫자로 쥔다. ① 을 대면 계약이 권하는 꼴이 곧 어긋남으로 뜬다.
SANCTIONED = ("raise Unmeasured",)

# ── 초록 줄 · 파이썬 ──────────────────────────────────────────────────────────
JUDGES = ("report", "show")          # 판정을 세우는 손 — `edge`·`unmeasured` 는 계수에 안 든다
COUNTER = "passes"
# 「전부 통과」 뒤에 구분자 한 자 이상(빈칸·괄호·줄표·쉼표·콜론)이 오고 그 뒤 같은 줄에 리터럴 숫자가 앉은 자리.
# 구분자를 요구해야 「전부 통과다」처럼 낱말이 이어지는 자리와 갈리고, 괄호에 안 가둬야 줄표·콜론 꼴도 문다.
HAND_DIGIT = re.compile(r"전부 통과[\s\(（—–,，:：-]+[^\n\)）]*?\d")

# ── 셋 · 글자 꼴 ──────────────────────────────────────────────────────────────
# 확장자가 없는 훅 몸통(`pre-commit`·`commit-msg`)의 갈래는 첫 줄이 말한다 — 확장자로만 걷으면 그 둘이 빠진다.
SHEBANG = re.compile(r"^#!.*\b\w*sh\b")
LINE_COMMENT = {".mjs": "//", ".sh": "#", ".ps1": "#"}
BLOCK_COMMENT = {".mjs": ("/*", "*/"), ".ps1": ("<#", "#>")}
QUOTES = {".mjs": "'\"`", ".sh": "'\"", ".ps1": "'\""}

MJS_EXIT = re.compile(r"process\s*\.\s*exit\s*\(")
MJS_LOG = re.compile(r"console\s*\.\s*log\s*\(")
SH_EXIT = re.compile(r"(?<![\w.$-])exit(?![\w-])")
PS_EXIT = re.compile(r"(?<![\w.$-])exit(?![\w-])", re.IGNORECASE)
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
# 정규식과 나눗셈을 가르는 어림 — 앞의 뜻 있는 글자가 자리를 여는 쪽이면 정규식이다. 따옴표를 든 정규식
# (`/HOME_SCREEN = "([^"]+)"/`)을 글자로 안 걷으면 거기서 문자열이 열려 그 뒤가 통째로 글자가 된다.
REGEX_OPENS = set("(,=:[!&|?{};+-*%~^<>")
REGEX_WORD = re.compile(r"(?:^|[^\w$])(return|typeof|instanceof|case|do|else|void|yield|await)$")

GREEN_WORD = "통과"
ESCAPES = re.compile(r"\\u\{[^}]*\}|\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}|\\.")
# 손글자 건수는 셈낱말이 바로 뒤에 붙은 숫자만이다 — 그냥 숫자를 다 물면 절 이름(「[3] 문 넷 — … 통과시키나」)이 걸린다.
HAND_COUNT = re.compile(r"\d+\s*[건장곳개항줄]")
INT_ONLY = re.compile(r"[+-]?\d+")
NAME_ONLY = re.compile(r"[\w.$\[\]{}:@-]+")

# 「못 쟀다」를 말하는 글자 그물 — **판정이 아니라 셈에만 쓴다**. 넓히면 셈이 부풀고 좁히면 새는데 어느 쪽도
# 판정이 아니라 괜찮다. 세는 까닭은 그 자리가 있다는 것을 사람 눈앞에 두기 위해서다.
UNMEASURED_WORDS = ("못 쟀다", "못 잰", "잴 것이 없다", "안 쟀다", "못 쟤")
UNMEASURED_NAME = re.compile(r"UNMEASURED", re.IGNORECASE)


# ── 파이썬 — 나가는 자리를 AST 에서 찾는다 ─────────────────────────────────────

def _is_name(node, want):
    return isinstance(node, ast.Name) and node.id == want


def exit_sites(tree):
    """나가는 자리 전부 — `(줄, 부르는 꼴, 인자 노드)`.

    `sys.exit(…)` · `exit(…)` · `raise SystemExit(…)` · `raise Unmeasured(…)` 와 나가는 함수 제 몸의 `return`.
    `raise SystemExit(2)` 는 `Raise` 로만 센다 — 그 안의 `Call` 을 또 세면 한 자리가 두 번 걸려 「몇 자리를
    쟀나」가 부푼다. 계약의 제 손(`Unmeasured`)도 센다 — 안 세면 잰 범위가 실제보다 넓어 보인다.
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
    """나가는 값의 갈래 — `(갈래, 값)` 들. 삼항이면 양쪽을 다 낸다 — 한쪽만 보면 다른 쪽에 숨은 값을 놓친다."""
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


# ── 파이썬 — 초록 줄 ──────────────────────────────────────────────────────────

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
    """머리말로 선 글자 조각들 — **무는 자리에서 뺀다.** 머리말은 어긋난 꼴을 *말하는* 자리라 물면 제 머리말을 문다."""
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
    """「전부 통과 … 숫자」 꼴의 상수 조각 — `(줄, 글자)`."""
    said = _docstrings(tree)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                and id(n) not in said and HAND_DIGIT.search(n.value):
            out.append((n.lineno, n.value.strip()[:60]))
    return out


def _judge_py(src, rel):
    tree = ast.parse(src)
    bad, found = [], []
    for lineno, how, arg in exit_sites(tree):
        kinds = list(values(arg))
        found.append((lineno, how, kinds))
        if how in SANCTIONED:
            continue
        for kind, val in kinds:
            if kind == "문자열":
                bad.append((rel, lineno, "①",
                            f"`{how}` 가 문자열로 나간다 — 파이썬이 그것을 stderr 로 찍고 무조건 1 로 "
                            "나간다. 「못 쟀다」가 판정으로 샌다"))
            elif kind == "정수" and val not in CONTRACT:
                bad.append((rel, lineno, "②", f"`{how}({val})` — 계약 밖 값이다. 계약은 0·1·2 뿐이다"))
    judges = any(_called(tree, j) for j in JUDGES)
    if judges and not _called(tree, COUNTER):
        bad.append((rel, 0, "④", "판정을 세우는데 `passes()` 를 한 번도 안 읽는다 — 초록 줄이 건수를 파생할 "
                                 "재료가 없다"))
    for lineno, text in _hand_digits(tree):
        bad.append((rel, lineno, "⑤", f"초록 줄에 숫자가 손글자로 앉았다 — {text!r}. 건수는 `len(passes())` 가 센다"))
    return bad, found, judges


# ── 셋 — 주석과 문자열을 걷는다 · 자리는 남긴다 ────────────────────────────────

def _wipe(out, a, b):
    """[a, b) 를 공백으로 간다 — **줄바꿈은 남긴다.** 자리와 줄 수가 원문과 맞아야 한다."""
    for k in range(a, min(b, len(out))):
        if out[k] != "\n":
            out[k] = " "


def _close_quote(src, i, q, suffix):
    """따옴표 안쪽 끝 — 닫는 따옴표 **다음** 자리. 못 닫으면 None.

    셸의 홑따옴표는 안에 달아나기가 없다 — 거기서 `\\'` 를 이어 읽으면 그 뒤가 통째로 문자열이 된다.
    """
    escapes = not (suffix == ".sh" and q == "'")
    j = i + 1
    while j < len(src):
        if escapes and src[j] == "\\":
            j += 2
            continue
        if src[j] == q:
            return j + 1
        j += 1
    return None


def _is_regex_start(out, i):
    """그 `/` 가 정규식의 시작인가 — 앞의 뜻 있는 글자가 값이면 나눗셈, 자리를 여는 글자나 낱말이면 정규식."""
    k = i - 1
    while k >= 0 and out[k] in " \t\r\n":
        k -= 1
    if k < 0 or out[k] in REGEX_OPENS:
        return True
    return bool(REGEX_WORD.search("".join(out[max(0, k - 12):k + 1])))


def _regex_end(src, i):
    """정규식 리터럴의 끝 — 닫는 `/` 다음의 깃발까지. 나눗셈이었으면 None. `[…]` 안의 `/` 는 글자다."""
    j, klass = i + 1, False
    while j < len(src):
        c = src[j]
        if c == "\\":
            j += 2
            continue
        if c == "\n":
            return None
        if klass:
            klass = c != "]"
        elif c == "[":
            klass = True
        elif c == "/":
            j += 1
            while j < len(src) and src[j].isalpha():
                j += 1
            return j
        j += 1
    return None


def _close_template(src, i):
    """`` ` `` 자리에서 템플릿의 끝 — 닫는 백틱 **다음** 자리. 못 닫으면 None.

    `${…}` 안은 글자가 아니라 코드다 — 따라 들어가지 않으면 중첩 템플릿의 백틱을 닫는 백틱으로 읽어 그 뒤가 한
    자리씩 밀리고, 밀린 쪽의 나가는 자리가 통째로 글자가 된다.
    """
    j = i + 1
    while j < len(src):
        if src[j] == "\\":
            j += 2
            continue
        if src[j] == "`":
            return j + 1
        if src.startswith("${", j):
            j = _close_interp(src, j + 2)
            if j is None:
                return None
            continue
        j += 1
    return None


def _close_interp(src, j):
    """`${` 다음 자리에서 짝이 되는 `}` **다음** 자리 — 안의 글자와 중첩 템플릿을 따라간다."""
    depth = 1
    while j < len(src):
        ch = src[j]
        if ch == "`":
            j = _close_template(src, j)
            if j is None:
                return None
            continue
        if ch in "'\"":
            j = _close_quote(src, j, ch, ".mjs")
            if j is None:
                return None
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if not depth:
                return j + 1
        j += 1
    return None


def _close_heredoc(src, i, m):
    """셸 헤어독의 끝 — 닫는 표 줄 **다음** 자리. 못 닫으면 글 끝."""
    tag = m.group(2)
    j = src.find("\n", m.end())
    if j < 0:
        return len(src)
    for line in re.finditer(r"^[ \t]*" + re.escape(tag) + r"[ \t]*$", src[j:], re.MULTILINE):
        return j + line.end()
    return len(src)


def blank(src, suffix):
    """`.mjs`·`.sh`·`.ps1` 원문의 주석과 문자열을 걷는다 — `(걷어 낸 사본, [(자리, 문자열)])`.

    받는 것 — 원문 글자와 그 확장자(`SHELLS` 중 하나). 사본은 원문과 **길이도 줄도 같아** 꼴은 사본에서 찾고 값은
    원문의 같은 자리에서 읽는다. 따옴표가 안 닫히면 `ValueError` 다(정규식을 문자열로 읽었을 수 있다).
    곁 검사가 불러 쓰는 손이다 — 이름과 꼴을 바꾸면 그쪽이 죽는다.
    """
    out, strings = list(src), []
    lc, bc, quotes = LINE_COMMENT[suffix], BLOCK_COMMENT.get(suffix), QUOTES[suffix]
    i, n = 0, len(src)
    while i < n:
        if src.startswith(lc, i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            _wipe(out, i, j)
            i = j
            continue
        if bc and src.startswith(bc[0], i):
            j = src.find(bc[1], i + len(bc[0]))
            j = n if j < 0 else j + len(bc[1])
            _wipe(out, i, j)
            i = j
            continue
        if suffix == ".ps1" and src[i] == "@" and src[i + 1:i + 2] in ("'", '"'):
            q = src[i + 1]
            end = src.find("\n" + q + "@", i)
            j = n if end < 0 else end + 3
            _wipe(out, i, j)
            i = j
            continue
        if suffix == ".sh" and src.startswith("<<", i) and not src.startswith("<<<", i):
            m = HEREDOC.match(src, i)
            if m:
                j = _close_heredoc(src, i, m)
                _wipe(out, i, j)
                i = j
                continue
        if suffix == ".mjs" and src[i] == "/" and _is_regex_start(out, i):
            j = _regex_end(src, i)
            if j is not None:                 # 못 닫으면 나눗셈이었다 — 그냥 지나간다
                _wipe(out, i, j)
                i = j
                continue
        if src[i] in quotes:
            j = (_close_template(src, i) if src[i] == "`"
                 else _close_quote(src, i, src[i], suffix))
            if j is None:
                raise ValueError(f"{i} 자리의 따옴표 {src[i]!r} 가 안 닫혔다 — "
                                 "정규식 리터럴을 문자열로 읽었을 수 있다")
            strings.append((i, src[i:j]))
            _wipe(out, i, j)
            i = j
            continue
        i += 1
    return "".join(out), strings


# ── 셋 — 나가는 자리와 초록 줄 ────────────────────────────────────────────────

def _close_paren(masked, i):
    """`(` 자리에서 짝이 되는 `)` — 못 닫으면 None. 문자열은 이미 지워져 있다."""
    depth = 0
    while i < len(masked):
        if masked[i] == "(":
            depth += 1
        elif masked[i] == ")":
            depth -= 1
            if not depth:
                return i
        i += 1
    return None


def _branches(raw, msk):
    """삼항이면 가지를 다 돌려준다 — 자리가 맞는 사본에서 가르고 원문에서 썬다(조건 쪽은 이름·못 가름으로 떨어진다)."""
    cuts, depth = [], 0
    for k, ch in enumerate(msk):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch in "?:" and not depth:
            cuts.append(k)
    at = 0
    for k in cuts:
        yield raw[at:k]
        at = k + 1
    yield raw[at:]


def _one(text):
    """값 한 조각의 갈래 — `(갈래, 값)`."""
    t = text.strip()
    if not t:
        return "없음", None
    if t[0] in "'\"`" and len(t) > 1 and t[-1] == t[0]:
        inner = t[1:-1]
        # 셸·PS 의 `"$rc"` 와 `.mjs` 의 `` `${code}` `` 는 글자가 아니라 펼침이다
        return ("이름" if "$" in inner else "문자열"), inner
    if INT_ONLY.fullmatch(t):
        return "정수", int(t)
    if NAME_ONLY.fullmatch(t):
        return "이름", t
    return "못 가름", t


def sites(src, masked, suffix):
    """셋의 나가는 자리 전부 — `(줄, 부르는 꼴, [(갈래, 값)])`."""
    out = []
    if suffix == ".mjs":
        for m in MJS_EXIT.finditer(masked):
            close = _close_paren(masked, m.end() - 1)
            if close is None:
                continue
            raw, msk = src[m.end():close], masked[m.end():close]
            out.append((src.count("\n", 0, m.start()) + 1, "process.exit",
                        [_one(p) for p in _branches(raw, msk)]))
        return out

    pattern = PS_EXIT if suffix == ".ps1" else SH_EXIT
    for m in pattern.finditer(masked):
        j = m.end()
        while j < len(masked) and masked[j] not in "\n;)}&|#":
            j += 1
        raw, msk = src[m.end():j], masked[m.end():j]
        out.append((src.count("\n", 0, m.start()) + 1, "exit", [_one(p) for p in _branches(raw, msk)]))
    return out


def _log_spans(masked):
    """`console.log( … )` 의 자리들 — 문자열이 그 안에 드는지 자리로 가른다."""
    out = []
    for m in MJS_LOG.finditer(masked):
        close = _close_paren(masked, m.end() - 1)
        if close is not None:
            out.append((m.start(), close))
    return out


def _strip_interp(text):
    """템플릿의 `${…}` 를 걷는다 — 중첩 중괄호까지 센다. 파생 건수는 여기서 사라진다."""
    out, i = [], 0
    while i < len(text):
        if text.startswith("${", i):
            depth, j = 1, i + 2
            while j < len(text) and depth:
                depth += {"{": 1, "}": -1}.get(text[j], 0)
                j += 1
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def green_flaws(src, masked, strings, rel):
    """`.mjs` 초록 줄의 손글자 숫자들 — `(파일, 줄, 갈래, 말)`."""
    spans, out = _log_spans(masked), []
    for off, text in strings:
        if GREEN_WORD not in text or not any(a <= off < b for a, b in spans):
            continue
        bare = ESCAPES.sub("", _strip_interp(text))
        hit = HAND_COUNT.search(bare)
        if hit:
            out.append((rel, src.count("\n", 0, off) + 1, "⑤",
                        f"초록 줄의 건수가 손글자다 — {hit.group()!r} in {bare.strip()[:60]!r}. "
                        "건수는 `${…length}` 가 센다"))
    return out


def _judge_shell(src, rel, suffix):
    masked, strings = blank(src, suffix)
    bad, found = [], sites(src, masked, suffix)
    for lineno, how, kinds in found:
        for kind, val in kinds:
            if kind == "문자열" and suffix == ".mjs":
                bad.append((rel, lineno, "①",
                            f"`{how}({val!r})` 가 문자열로 나간다 — 계약의 셋과 아무 관계가 없는 값이다. "
                            "「못 쟀다」가 판정으로 샌다"))
            elif kind == "없음" and suffix == ".mjs":
                bad.append((rel, lineno, "③",
                            f"`{how}()` — 인자가 없다. `process.exitCode`(안 세우면 0)로 나가 "
                            "**뜻을 안 적고 초록이 난다**"))
            elif kind == "정수" and val not in CONTRACT:
                bad.append((rel, lineno, "②", f"`{how}({val})` — 계약 밖 값이다. 계약은 0·1·2 뿐이다"))
    if suffix == ".mjs":
        bad += green_flaws(src, masked, strings, rel)
    return bad, found, False


def judge(src, rel, suffix):
    """원문 한 장을 한 번 읽는다 — `(어긋남들, 나가는 자리들, 판정을 세우나)`.

    어긋남은 `(파일, 줄, 갈래, 말)` 이고 제 꼴이면 빈 목록이다. 나가는 자리는 `(줄, 부르는 꼴, [(갈래, 값)])`.
    「판정을 세우나」는 `.py` 만 잰다. `.py` 문법 오류는 `SyntaxError`, 셋의 안 닫힌 따옴표는 `ValueError` 로 올라간다.
    """
    return _judge_py(src, rel) if suffix == PY else _judge_shell(src, rel, suffix)


def boundaries(src, found):
    """「못 쟀다」를 찍고 `exit 0` 으로 나가는 셸 자리 수 — **판정이 아니라 셈이다**.

    같은 줄과 바로 앞 줄(빈 줄은 건너뛴다)을 본다 — 셸은 `{ echo …; exit 0; }` 로 한 줄에 붙는 꼴이 흔하다.
    """
    lines, n = src.splitlines(), 0
    for lineno, _how, kinds in found:
        if not any(k == "정수" and v == 0 for k, v in kinds):
            continue
        window = [lines[lineno - 1]] if lineno - 1 < len(lines) else []
        i = lineno - 2
        while i >= 0 and not lines[i].strip():
            i -= 1
        if i >= 0:
            window.append(lines[i])
        if any(w in "\n".join(window) for w in UNMEASURED_WORDS):
            n += 1
    return n


def has_unmeasured_branch(found):
    """그 원문에 「못 쟀다」(2)로 나가는 갈래가 있나 — 리터럴 2 이거나 그 뜻의 이름이다."""
    for _lineno, _how, kinds in found:
        for kind, val in kinds:
            if kind == "정수" and val == UNMEASURED_CODE:
                return True
            if kind == "이름" and UNMEASURED_NAME.search(str(val)):
                return True
    return False


# ── 원문 집기 — 이 폴더와 나무의 `.githooks/` ───────────────────────────────────

def hooks_finder():
    """곁 `borrowed_check.py` 의 `.githooks/` 찾개 — `(폴더 이름, 뿌리 찾개)`. 그 파일이 곁에 없으면 `(None, None)`.

    같은 walk-up 을 두 자리에 손으로 적지 않으려고 그쪽 것을 부른다. 곁에 없는 폴더(그 파일을 안 받은 씨앗 갈래)
    에서는 `.githooks/` 팔이 안 잰 자리가 된다 — 부르는 쪽이 그렇다고 찍는다.
    """
    try:
        from borrowed_check import HOOKS, hooks_root
    except ImportError:
        return None, None
    return HOOKS, hooks_root


def hook_sources(check_dir):
    """`.githooks/` 아래의 셸 원문 — `[(파일, 갈래, 이름)]`. 뿌리를 못 찾거나 찾개가 없으면 빈 목록.

    이름은 뿌리에서의 상대 자리다 — `encoding.sh` 하나로는 어느 `encoding.sh` 인지 안 갈린다.
    """
    hooks, find_root = hooks_finder()
    root = find_root(check_dir) if find_root else None
    if root is None:
        return []
    out = []
    for p in sorted((root / hooks).rglob("*")):
        if not p.is_file():
            continue
        name = p.relative_to(root).as_posix()
        if p.suffix in SHELLS:
            out.append((p, p.suffix, name))
            continue
        if p.suffix:
            continue
        try:
            head = p.read_text(encoding="utf-8-sig").splitlines()[:1]
        except (OSError, UnicodeDecodeError):
            continue
        if head and SHEBANG.search(head[0]):
            out.append((p, ".sh", name))
    return out


def sources(check_dir):
    """잴 원문들 — `[(파일, 갈래, 이름)]`. 이 폴더의 네 갈래(하위 폴더는 검체·기록이라 안 본다) + `.githooks/` 셸 조각."""
    here = [(p, p.suffix, p.name) for p in sorted(Path(check_dir).iterdir())
            if p.is_file() and p.suffix in (PY, *SHELLS)]
    return here + hook_sources(check_dir)


def survey(check_dir):
    """실물 전수 — 사전 하나: 어긋남 · 갈래별 파일 수 · 나가는 자리 수 · 판정을 세우는 `.py` 수 · 셈 둘 · 못 읽은 파일."""
    got = {"bad": [], "seen": {s: 0 for s in (PY, *SHELLS)}, "sites": 0, "judging": 0,
           "bound": 0, "no2": 0, "unreadable": []}
    for p, suffix, name in sources(check_dir):
        try:
            src = p.read_text(encoding="utf-8-sig")
            bad, found, judges = judge(src, name, suffix)
        except (OSError, SyntaxError, ValueError) as exc:
            got["unreadable"].append(f"{name} — {type(exc).__name__}: {exc}")
            continue
        got["bad"] += bad
        got["seen"][suffix] += 1
        got["sites"] += len(found)
        got["judging"] += 1 if judges else 0
        if suffix != PY:
            got["bound"] += boundaries(src, found)
            got["no2"] += 1 if found and not has_unmeasured_branch(found) else 0
    return got


# ── §1 양성 대조 — 갈래마다 일부러 어긋난 검체로 다섯이 정말 무는지 먼저 보인다 ─────

# ⚠ 초록 줄 손글자 검체(⑤)는 **이 파일에서는 이어 붙여** 둔다 — 한 상수로 두면 이 검사가 제 검체를 ⑤ 로 문다.
#   검체 원문은 이어 붙인 결과라 그대로 한 글자고, 그래서 판정이 문다.
BAD = [
    ("①", ".py — 문자열로 나간다", PY, """
import sys
sys.exit("못 쟀다 — 검체가 없다")
"""),
    ("①", ".py — `raise` 로 문자열이 나간다", PY, """
raise SystemExit("못 쟀다 — 검체가 없다")
"""),
    ("①", ".py — f-문자열로 나간다", PY, """
import sys
why = "검체가 없다"
sys.exit(f"못 쟀다 — {why}")
"""),
    ("①", ".py — 나가는 함수(main)가 문자열을 돌려준다", PY, """
import sys
def main(argv):
    return "못 쟀다"
raise SystemExit(main(sys.argv))
"""),
    ("②", ".py — 계약 밖 값으로 나간다", PY, """
import sys
sys.exit(3)
"""),
    ("②", ".py — 삼항의 **한쪽**이 계약 밖 값이다", PY, """
import sys
sys.exit(3 if left else 0)
"""),
    ("②", ".py — 나가는 함수(main)의 `return 3` 이다", PY, """
import sys
def main():
    if not_ready:
        return 3
    return EXIT_OK
sys.exit(main())
"""),
    ("④", ".py — 판정을 세우고 계수를 안 읽는다", PY, """
from _verdict import fails, report
report("하나", True)
print("전부 통과" if not fails() else "어긋남")
"""),
    ("⑤", ".py — 초록 줄 숫자가 손글자다 · 괄호 꼴", PY, """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과 (판정 """ + """20건 — 넷·셋)" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    ("⑤", ".py — 초록 줄 숫자가 손글자다 · 줄표 꼴", PY, """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과 — 판정 """ + """20건" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    ("⑤", ".py — 초록 줄 숫자가 손글자다 · 콜론 꼴", PY, """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과: 판정 """ + """20건" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    ("⑤", ".py — 초록 줄 숫자가 손글자다 · 쉼표 꼴", PY, """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과, 판정 """ + """20건" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    ("⑤", ".py — 초록 줄 숫자가 손글자다 · 빈칸 하나", PY, """
from _verdict import fails, passes, report
report("하나", True)
print("✅ 전부 통과 """ + """20건" if not fails() else f"{len(fails())}건 · {len(passes())}")
"""),
    ("①", ".mjs — 문자열로 나간다", ".mjs", """
process.exit("못 쟀다 — 검체가 없다");
"""),
    ("②", ".mjs — 계약 밖 값으로 나간다", ".mjs", """
process.exit(3);
"""),
    ("②", ".mjs — 삼항의 **한쪽**이 계약 밖 값이다", ".mjs", """
process.exit(bad ? 1 : 3);
"""),
    ("③", ".mjs — 인자 없이 나간다", ".mjs", """
process.exit();
"""),
    ("⑤", ".mjs — 초록 줄 숫자가 손글자다", ".mjs", """
console.log(`✅ 전부 통과 (판정 """ + """20건 — 넷·셋)`);
"""),
    ("②", ".sh — 계약 밖 값으로 나간다", ".sh", """
exit 7
"""),
    ("②", ".ps1 — 계약 밖 값으로 나간다", ".ps1", """
exit 7
"""),
]

# 제 꼴 — 네 갈래가 저마다 계약을 지킨 원문이다. 리터럴 2 를 일부러 넣는다 — 그것을 물면 걷은 판정이 살아난 것이다.
# 걷는 손이 죽으면 셋에 심어 둔 주석·문자열·헤어독 속 가짜 나가는 자리가 살아나 빨강이 난다.
GOOD = {
    PY: """
import sys
from _verdict import EXIT_MISMATCH, EXIT_OK, EXIT_UNMEASURED, Unmeasured, fails, passes, report, show

REFUSED = EXIT_UNMEASURED

def main():
    def inner():
        return 3          # 둥지 튼 함수 — 나가는 값이 아니다
    if bad:
        return 1 if bad else 0
    if not_ready:
        return 2          # 리터럴 2 — 계약의 수라 안 문다
    return EXIT_OK

def helper():
    return 3              # sys.exit 에 안 물린 함수 — 나가는 값이 아니다

report("하나", True)
show("둘", 1, 1)
if not_ready:
    raise Unmeasured("[안 잼] 검체가 없다")
if fenced:
    sys.exit(REFUSED)
if left:
    sys.exit(2)
print(f"✅ 전부 통과 (판정 {len(passes())}건 — 계약 아홉)" if not fails() else f"{len(fails())}건")
sys.exit(EXIT_MISMATCH if bad else EXIT_OK)
sys.exit(main())
sys.exit(0)
sys.exit(1)
raise SystemExit
""",
    ".mjs": """
const EXIT_OK = 0, EXIT_MISMATCH = 1, EXIT_UNMEASURED = 2;
// 주석의 process.exit(3) 은 걷는다
const said = "process.exit(9) 라고 적힌 글자";
const note = "통과 3건 — console.log 밖이라 ⑤ 가 안 본다";
// 따옴표를 든 정규식 — 글자로 안 걷으면 여기서 문자열이 열려 **아래가 다 글자가 된다**
const HOME = (readFileSync(f, "utf8").match(/HOME_SCREEN = "([^"]+)"/) || [])[1];
if (!HOME) { console.log("못 쟀다 — 진본에 그 이름이 없다"); process.exit(EXIT_UNMEASURED); }
const half = total / 2;   // 나눗셈 — 정규식으로 읽으면 여기서 또 밀린다
// 중첩 템플릿 — `${…}` 안의 글자까지 안 따라가면 저 백틱을 닫는 백틱으로 읽는다
console.log(`고른 것 ${list.map((s) => s.replace("`", "'")).join(" ")} 끝`);
console.log("[3] 문 넷 — 서버가 바이트를 통과시키나");
if (left) process.exit(code);
if (blind) process.exit(2);
console.log(fails ? `❌ ${fails}건 어긋남` : `✅ 전부 통과 (판정 ${results.length}건 — 위 경계 안에서)`);
process.exit(0);
process.exit(1);
process.exit(fails ? EXIT_MISMATCH : EXIT_OK);
""",
    ".sh": """
# 주석의 exit 3 은 걷는다
echo 'exit 9 는 글자다' > "$tmp/bare.sh"
cat <<'MSG'
여기 적힌 exit 8 도 글자다
MSG
[ -d "$DIR" ] || { echo "담긴 것이 없다 — 잴 것이 없다: $DIR"; exit 0; }
[ -n "$PY" ] || { echo "? 못 쟀다 — 파이썬을 못 부른다"; exit 2; }
exit "$rc"
""",
    ".ps1": """
# 주석의 exit 3 은 걷는다
<# 여러 줄 주석 안의 exit 4 도 걷는다 #>
$said = "exit 5 라고 적힌 글자"
$block = @'
여기 적힌 exit 6 도 글자다
'@
if (-not (Test-Path $norm)) { "잴 것이 없다"; exit 2 }
if ($bad) { exit 1 }
exit 0
""",
}

# 제 꼴에서 세야 하는 「나가는 자리」 — 걷는 손과 찾는 손의 센티널이다. 부풀면 주석·문자열을 못 걷은 것이고,
# 줄면 나가는 자리를 못 찾은 것이다. 수는 위 원문을 손으로 센 값이다:
#   .py  — `sys.exit` 여섯 · 인자 없는 `raise SystemExit` 하나 · 계약의 제 손 `raise Unmeasured` 하나 · 나가는
#          함수 `main` 제 몸의 `return` 셋(둥지 튼 `inner` 와 안 물린 `helper` 는 안 센다)
#   .mjs — `process.exit` 여섯(주석·문자열 속 둘은 안 센다) · .sh — `exit` 셋 · .ps1 — `exit` 셋
GOOD_SITES = {PY: 11, ".mjs": 6, ".sh": 3, ".ps1": 3}


def positive_control():
    """검체가 실제로 그 꼴인지부터 묻는다 — 이 절이 빨강이면 아래 §3 의 0 은 뜻이 없다."""
    print(f"--- §1 양성 대조 — 일부러 어긋난 검체 {len(BAD)}이 정말 빨개지나")
    for want, said, suffix, src in BAD:
        got, _, _ = judge(src, "<검체>", suffix)
        report(f"{want} {said}",
               len(got) == 1 and got[0][2] == want,
               [f"{len(got)}건 · 갈래 {[r[2] for r in got]} (기대 {want} 하나)"])

    print("\n--- §2 음성 대조 — 네 갈래의 제 꼴은 한 자리도 안 문다")
    for suffix, src in GOOD.items():
        clean, found, _ = judge(src, "<제 꼴>", suffix)
        report(f"{suffix} — 계약을 지킨 원문은 어긋남 0 이다 (리터럴 2 도 제 꼴이다)", not clean,
               [f"{r[0]}:{r[1]} {r[2]} {r[3]}" for r in clean])
        show(f"  {suffix} 에서 센 「나가는 자리」", len(found), GOOD_SITES[suffix])
    sh = GOOD[".sh"]
    show("  .sh 에서 센 「못 쟀다 뒤의 `exit 0`」", boundaries(sh, judge(sh, "<제 꼴>", ".sh")[1]), 1)
    edge("**음성 대조가 이 판의 값을 절반 든다** — 양성만 보이면 「전부 빨강」인 자도 만점을 받는다. "
         "위 자리 수가 어긋나면 걷는 손이나 찾는 손이 무너진 것이므로 함께 문다.")

    hooks, _ = hooks_finder()
    print("\n--- §2' 원문 집기 — 심은 나무에서 네 갈래와 훅 조각을 정말 집나")
    tmp = Path(tempfile.mkdtemp(prefix="exit-code-"))
    try:
        deep = tmp / "_check"
        (deep / "fixtures").mkdir(parents=True)
        (deep / "a_check.py").write_text('"""제 꼴."""\nimport sys\nsys.exit(0)\n', encoding="utf-8")
        (deep / "b_check.mjs").write_text("process.exit(0);\n", encoding="utf-8")
        (deep / "c_check.sh").write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
        (deep / "d_check.ps1").write_text("exit 0\n", encoding="utf-8")
        (deep / "notes.txt").write_text("exit 9\n", encoding="utf-8")                  # 네 갈래 밖
        (deep / "fixtures" / "e_check.py").write_text("import sys\nsys.exit(9)\n", encoding="utf-8")  # 하위 폴더
        want = ["a_check.py", "b_check.mjs", "c_check.sh", "d_check.ps1"]
        if hooks:
            (tmp / hooks / "gates.d").mkdir(parents=True)
            (tmp / hooks / "gates.d" / "encoding.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (tmp / hooks / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")   # 확장자가 없다
            (tmp / hooks / "gates.conf").write_text("[pre-commit]\nencoding\n", encoding="utf-8")
            want += [f"{hooks}/gates.d/encoding.sh", f"{hooks}/pre-commit"]
        show("  집은 원문", [name for _p, _s, name in sources(deep)], want)
        show("  집은 원문의 어긋남", [(r[0], r[2]) for r in survey(deep)["bad"]], [("c_check.sh", "②")])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if not hooks:
        edge("**`.githooks/` 집기는 안 쟀다** — 곁 `borrowed_check.py` 가 이 폴더에 없어 뿌리를 찾는 손이 없다.")


# ── §3 실물 전수 ───────────────────────────────────────────────────────────────

def main(argv):
    check_dir = Path(argv[1]).resolve() if len(argv) > 1 else HERE
    hooks, find_root = hooks_finder()
    root = find_root(check_dir) if find_root else None
    print(f"잴 폴더 — {check_dir}")
    print(f"게이트 조각 — {root / hooks if root else '못 찾았다'}\n")

    positive_control()

    print("\n--- §3 실물 전수 — 이 폴더와 게이트 조각이 종료코드 계약과 초록 줄을 지키나")
    got = survey(check_dir)
    seen = got["seen"]

    # 센티널이 먼저다 — 한 장도 못 읽은 판은 어긋남 0 이 나도 초록이 아니다.
    if not sum(seen.values()):
        raise Unmeasured(f"[안 잼] 읽은 파일이 0 이다 — {check_dir} 에 "
                         f"{' · '.join((PY, *SHELLS))} 원문이 없다. 어긋남 0 은 아무 뜻도 없다")

    for rel, lineno, kind, said in got["bad"]:
        report(f"{rel}:{lineno} — {kind}", False, [said])
    tally = " · ".join(f"`{s}` {seen[s]}장" for s in (PY, *SHELLS))
    report(f"계약을 어기는 자리가 없다 ({tally} · 나가는 자리 {got['sites']}곳 · "
           f"판정을 세우는 `.py` {got['judging']}장)", not got["bad"])

    for row in got["unreadable"]:
        edge(f"**못 읽은 파일** — {row}")
    if got["unreadable"]:
        edge("못 읽은 파일은 판정이 아니라 **안 잰 자리**다 — 위 건수에서 빠져 있다.")

    if not hooks:
        edge("**`.githooks/` 는 안 잰 자리다** — 곁 `borrowed_check.py` 가 없어 뿌리를 찾는 손이 없다.")
    elif root is None:
        edge(f"**`{hooks}/` 를 못 찾았다 — 게이트 조각은 안 잰 자리다.** 0·1·2 를 실제로 내는 `.sh` 가 거기 사는데 "
             "그 팔이 이 판에서는 비었다.")
    else:
        edge(f"잰 범위 — `{check_dir.name}/` 의 네 갈래와 **`{hooks}/` 의 셸 조각 "
             f"{len(hook_sources(check_dir))}장**({root / hooks}). 하위 폴더와 그 밖은 안 든다.")
    if not sum(seen[s] for s in SHELLS):
        edge("**`.mjs`·`.sh`·`.ps1` 원문이 0장이다** — 그 팔은 이 판에서 비었다(셋 갈래 판정은 안 섰다).")
    edge(f"**「못 쟀다」를 찍고 `exit 0` 으로 나가는 셸 자리 {got['bound']}곳 · 2 로 나가는 갈래가 한 자리도 없는 "
         f"셸 원문 {got['no2']}장** — 판정이 아니다. 그 갈래가 옳은지는 꼴이 아니라 뜻이라 **사람이 읽는다**.")
    edge("**리터럴 `0`·`1`·`2` 는 안 문다** — 숫자는 계약이 못박았다. 한국어 수사로 적은 건수도 안 문다.")
    edge("**「그 코드로 실제로 나가나」는 안 잰다** — 원문의 꼴까지다. 돌려 보지 않는다.")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        return EXIT_MISMATCH
    print(f"전부 통과 (판정 {len(passes())}건 — 양성 {len(BAD)} · 음성 {len(GOOD)}갈래 · 원문 집기 · 실물 전수)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
