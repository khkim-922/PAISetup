"""환경변수 문서의 이름이 코드가 **읽는** 이름과 맞나 — 양쪽 차집합.

좌표 — 아뜰리에 #322(이 자가 난 자리 · 「그물이 좁으면 항진명제」는 그 ③) · 아뜰리에 결정 0112
(자기 이빨 규율) · 씨앗 규율은 claude-config 결정 0040.

    python -X utf8 _check/env_names_check.py --doc <문서> --ours <그물>
    python -X utf8 _check/env_names_check.py <나무뿌리> --doc <문서> --ours <그물>
    python -X utf8 _check/env_names_check.py <나무뿌리> --doc <문서> --ours '*' --skip 산출물,기록

**왜 이 검사가 있나.** 환경변수는 **들여도 지워도 아무 데서도 안 터진다.** 새 손잡이를 들이면
문서가 그것을 영영 안 들고, 읽는 줄을 지우면 문서만 없는 손잡이를 계속 약속한다. 비싼 쪽은
뒤엣것이다: 읽는 자리가 사라진 줄을 읽은 사람은 **안 걸리는 값을 세워 두고 걸린 줄 안다.**

재는 것은 **차집합 둘**이고, 둘은 서로 다른 사고다:
  ① **문서에 없는 이름** — 코드가 읽는데 표에 줄이 없다. 손잡이를 들이고 안 적은 자리
  ② **실물 없는 줄** — 표에 줄은 있는데 읽는 자리가 없다. 지우거나 이름을 바꾼 자리

**소유 그물(`--ours`)은 단순 인자가 아니다 — ①이 무는 범위가 곧 그 값이다.**
①은 「우리가 지은 이름만 우리가 전수를 진다」로 선다. `PATH`·`HOME` 처럼 바깥이 정의한
이름까지 물면 그 표가 남의 도구 설명서가 되고, 아무것도 안 물면 ①은 항진명제가 된다.
그래서 그물은 저장소가 **고르는** 것이지 이 파일이 정하는 것이 아니다:

  · **접두어 규율이 있는 저장소** — 그 접두어를 준다(쉼표로 여럿). 접두어 밖의 **새** 읽기는
    ①이 안 문다. **②는 그물을 안 본다** — 문서가 든 이름은 우리 것이든 아니든 읽는 자리가
    있어야 한다
  · **접두어 규율이 없는 저장소** — `*` 를 **명시로** 골라 「읽는 이름 전부가 우리 것」을
    선언하고, 바깥이 정의한 이름은 아래 `NOT_OURS` 에 **까닭을 달아** 뺀다. 그물이 넓어진
    만큼 뺀 자리를 사람이 지므로, 그 목록이 곧 그 저장소의 소유 선언이다
  · **안 주면 「못 쟀다」(2)다.** 어느 쪽도 기본값으로 깔지 않는다 — 좁게 깔면 ①이 조용히
    아무것도 안 물고, 넓게 깔면 남의 이름으로 빨강이 나서 사람이 검사를 끈다

**그물이 좁으면 이 검사는 항진명제다.** 그래서 읽기를 **AST 로** 가르고 리터럴만 세지 않는다:
  · `os.environ.get("X")` · `os.environ["X"]` · `.setdefault("X")` · `.pop("X")` · `os.getenv("X")`
  · **이름이 표에 담겨 도는 자리**도 푼다 — 이름표를 `for n in …` 으로 돌며 읽는 꼴이라,
    리터럴만 세면 키 묶음이 통째로 ①로 뜬다. 없는 어긋남이다
  · **못 푼 자리는 빨강이다.** 이름을 못 세면 그만큼 대조가 눈이 머는데, 그 눈먼 자리는
    ②를 조용히 통과시킨다 — 「못 쟀다」를 초록으로 세지 않는다
  · **그물 밖의 읽기 꼴**(`from os import environ` 류)도 빨강이다. 같은 까닭이다
  · **쓰기는 안 센다** — `os.environ[X] = v` 는 읽는 자리가 아니다
  · **`.mjs` 의 `process.env` 도 센다** — 안 세던 판에서는 화면 검사만 읽는 이름들이 그물의
    구멍에 살았다. 다만 **파이썬은 AST, `.mjs` 는 정규식이다** — 주석에 적힌 `process.env.X`
    도 읽기로 세어진다. 열쇠가 리터럴이 아닌 자리는 파이썬과 같이 **빨강**이다

**일부러 안 재는 것** — 판정 곁에 새겨 둔다:
  · 소유 그물 밖의 **새** 읽기(위 가름) · `NOT_OURS` 에 까닭을 달고 뺀 이름
  · 산출물·기록·옛 세대 폴더(`SKIP` 과 `--skip`)와 점으로 시작하는 폴더
  · **표 밖 산문이 든 이름** — 문서가 「변수가 아닌데 환경이 정하는 것」으로 따로 가른 자리다
  · **어느 나무가** 읽나 — 앱이 읽는 표와 검사만 읽는 표를 문서가 갈라도 한 자루로 센다

⚠ **이 자는 제 손잡이를 환경변수로도 받는다** — 그래서 이 파일이 재이는 나무 안에 살면
  그 이름들(`ENV_NAMES_DOC` 따위)이 **제 그물에 든다.** 접두어 그물에서는 밖이라 조용하고,
  `*` 를 고른 저장소에서는 문서에 줄을 두거나 `NOT_OURS` 에 까닭을 달아 뺀다. 판정 곁의
  고지가 그 자리를 말한다.

⚠ **재는 것은 「이름이 있나」까지다.** 그 줄이 *무엇을 정하나*를 맞게 말하는지는 못 잰다 —
  뜻은 사람이 실물을 읽고 적은 판단이라 기계가 대신 못 한다.

⚠ **어긋남 0 은 그 자체로 초록이 아니다.** 문서를 못 읽어도 0 이 나온다. 그래서 §1 이
  실물 판정보다 **먼저** 서서 손댄 사본 열하나로 이 판정이 정말 무는지 보이고, 한쪽이
  빈손이면 초록이 아니라 「못 쟀다」(2)로 나간다.

토큰도 망도 브라우저도 안 쓴다.
"""
import ast
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report  # noqa: E402

ALL = "*"                                # 소유 그물 = 읽는 이름 전부. 접두어 규율이 없는 저장소가 고른다
NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")  # 환경변수 이름꼴 — 표 칸과 이름표에 같은 자를 댄다
SPAN = re.compile(r"`([^`]+)`")          # 표 칸 안의 백틱 조각
KEYED = ("get", "setdefault", "pop")     # 이름 하나를 짚어 읽는 `os.environ` 의 손잡이들

# 어느 나무에서나 산출물인 자리. **씨앗은 이 셋만 든다** — 받은 저장소가 제 산출물·기록·옛
# 세대 폴더를 여기 적거나 `--skip` 으로 준다. 점으로 시작하는 폴더는 따로 뺀다.
SKIP = {"node_modules", "__pycache__", "venv"}

# **우리 소스의 소유 밖 이름** — 이름과 까닭을 함께 둔다. ①도 ②도 이 이름을 안 문다:
# 우리가 안 지었으므로 문서에 줄을 요구하지 않고, 문서가 들었어도 읽는 자리를 요구하지
# 않는다. 까닭이 없으면 그냥 눈감은 것이고, 눈감은 자리는 다음 사람이 못 되짚는다.
# **씨앗은 비어 있다** — 이 파일을 받은 저장소가 제 이름을 여기 적는다.
NOT_OURS = {}

# 이 자가 제 손잡이를 받는 환경변수 — argv 가 먼저고 이것이 그 다음이다. 훅·CI 가 한 번
# 세워 두면 부르는 자리마다 안 적는다. ⚠ 이 이름들이 제 그물에 드는 자리는 머리말이 든다.
ENV_DOC, ENV_OURS, ENV_SKIP = "ENV_NAMES_DOC", "ENV_NAMES_OURS", "ENV_NAMES_SKIP"
FLAGS = ("--doc", "--ours", "--skip")


class Code(NamedTuple):
    """이 나무의 코드가 무엇을 읽나 — 그리고 **무엇을 못 읽었나.**"""
    names: dict          # 이름 → 읽는 자리들
    indirect: list       # 이름표를 풀어 얻은 자리 (판정에 그대로 찍는다)
    unresolved: list     # 열쇠를 못 푼 읽기 자리 — 빨강
    outside: list        # 그물 밖의 읽기 꼴 — 빨강
    whole: list          # 이름 없이 통째로 넘기는 자리 (`{**os.environ}` 류)
    files: int
    js_files: int        # `.mjs` 장수 — 파이썬과 따로 센다(그물이 다르다)


# ── 문서 쪽 — 표 칸만 본다

def scan_doc(text):
    """환경변수 문서의 표가 든 이름.

    **표 칸 안의 백틱 조각만** 센다. 본문 산문에도 대문자 이름이 앉는데(파이썬 상수,
    「변수가 아닌데 환경이 정하는 것」의 `PATH`) 그것까지 물면 **변수가 아닌 것을 변수로
    세워** ②가 통째로 거짓 빨강이 된다. 표에 앉았나가 곧 문서가 「이것은 변수다」라고
    선언한 자리다.

    **첫 칸만 보지 않는다** — 키 묶음 표는 첫 칸이 묶음 이름이고 변수는 둘째 칸에 산다.
    """
    out = set()
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        for cell in s.split("|")[1:-1]:
            out |= {t for t in SPAN.findall(cell) if NAME.match(t)}
    return out


# ── 코드 쪽 — AST 로 읽기만 가른다

def _is_environ(node):
    """`os.environ` 그 자체인가."""
    return (isinstance(node, ast.Attribute) and node.attr == "environ"
            and isinstance(node.value, ast.Name) and node.value.id == "os")


def _module_consts(tree):
    """모듈 자리(들여쓰기 밖)의 이름 → 묶인 식.

    **함수 안 지역 이름은 안 든다.** 같은 글자를 쓰는 지역 변수까지 풀면 남의 자리 글자가
    딸려 들어와 대조가 조용히 부푼다 — 부푼 쪽은 ②를 통과시킨다.
    """
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = node.value
    return out


def _binds(target, ident):
    return any(isinstance(n, ast.Name) and n.id == ident for n in ast.walk(target))


def _looped(node, ident):
    """이 자리를 **감싼** 반복이 `ident` 를 묶고 있으면 그 도는 식.

    감싼 것만 본다 — 파일 어딘가의 같은 이름을 집으면 그것이 곧 부푸는 자리다.
    """
    cur = getattr(node, "_up", None)
    while cur is not None:
        if isinstance(cur, (ast.For, ast.AsyncFor)) and _binds(cur.target, ident):
            return cur.iter
        for gen in getattr(cur, "generators", ()):
            if _binds(gen.target, ident):
                return gen.iter
        cur = getattr(cur, "_up", None)
    return None


def _strings(node, consts, seen=None):
    """식 하나가 담은 이름꼴 글자 — `Name` 은 모듈 상수로 한 번 더 따라간다."""
    seen = set() if seen is None else seen
    out = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            if NAME.match(sub.value):
                out.add(sub.value)
        elif isinstance(sub, ast.Name) and sub.id not in seen:
            seen.add(sub.id)
            src = consts.get(sub.id)
            if src is not None:
                out |= _strings(src, consts, seen)
    return out


def _key_of(node):
    """이 자리가 환경변수를 **읽는** 자리면 그 열쇠 식, 아니면 None.

    쓰기(`os.environ[X] = v`)는 안 든다 — 읽는 이름이 아니다.
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        fn = node.func
        if _is_environ(fn.value) and fn.attr in KEYED and node.args:
            return node.args[0]
        if (isinstance(fn.value, ast.Name) and fn.value.id == "os"
                and fn.attr == "getenv" and node.args):
            return node.args[0]
    elif isinstance(node, ast.Subscript) and _is_environ(node.value):
        if isinstance(node.ctx, ast.Load):
            return node.slice
    return None


def scan_module(rel, text):
    """한 파일이 읽는 이름과, 못 읽은 자리들."""
    tree = ast.parse(text, filename=str(rel))
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child._up = parent
    consts = _module_consts(tree)

    names, indirect, unresolved, outside, whole = {}, [], [], [], []
    taken = set()      # 이름을 세고 쓴 `os.environ` 자리

    for node in ast.walk(tree):
        # 그물 밖 — 이 꼴이 들어오면 `os.environ` 만 보는 자가 눈이 먼다
        if isinstance(node, ast.ImportFrom) and node.module == "os":
            for a in node.names:
                if a.name in ("environ", "getenv", "environb"):
                    outside.append(f"{rel}:{node.lineno} — `from os import {a.name}`")
            continue

        # 이름을 **세고** 쓴 자리만 표시한다. 아무 `.value` 나 표시하면 `env=os.environ`
        # 같은 통째 전달이 조용히 삼켜져, 아래 「이름 없이 넘기는 자리」가 눈이 먼다.
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and _is_environ(node.func.value) and node.func.attr in KEYED):
            taken.add(id(node.func.value))
        elif isinstance(node, ast.Subscript) and _is_environ(node.value):
            taken.add(id(node.value))          # 읽기든 쓰기든 이름 하나를 짚은 자리다
        key = _key_of(node)
        if key is None:
            continue

        where = f"{rel}:{node.lineno}"
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            names.setdefault(key.value, []).append(where)
            continue

        got = set()
        if isinstance(key, ast.Name):
            src = _looped(node, key.id)        # 감싼 반복이 먼저다
            if src is None:
                src = consts.get(key.id)
            if src is not None:
                got = _strings(src, consts)
        if got:
            for n in got:
                names.setdefault(n, []).append(where)
            indirect.append(f"{where} — {' · '.join(sorted(got))}")
        else:
            unresolved.append(where)

    for node in ast.walk(tree):
        if _is_environ(node) and id(node) not in taken:
            whole.append(f"{rel}:{node.lineno}")

    return names, indirect, unresolved, outside, whole


def _walk(root, suffix, skip):
    """이 나무의 원문 — 산출물·기록·옛 세대와 점 폴더는 뺀다."""
    root = Path(root)
    for p in sorted(root.rglob(f"*{suffix}")):
        rel = p.relative_to(root)
        if any(part in skip or part.startswith(".") for part in rel.parts[:-1]):
            continue
        yield p, rel


# ── `.mjs` 쪽 — AST 가 아니라 정규식이다. 경계는 머리말이 든다.
#    `process.env` 를 먼저 찾고 **바로 뒤가 무엇인지**로 갈래를 가른다: 점 이름 · 리터럴
#    열쇠 · 리터럴 아닌 열쇠(빨강) · 아무것도 아님(통째로 넘기는 꼴). 파이썬 쪽 갈래와
#    같은 자를 대야 두 그물이 같은 것을 세고 같은 것을 못 세었다고 말한다.
JS_ENV = re.compile(r"process\s*\.\s*env\b")
JS_DOT = re.compile(r"\s*\.\s*([A-Za-z_$][\w$]*)")
JS_LIT = re.compile(r"""\s*\[\s*(["'])([^"']*)\1\s*\]""")
JS_IDX = re.compile(r"\s*\[")


def scan_js(rel, text):
    """한 `.mjs` 가 읽는 이름과, 못 읽은 자리들."""
    names, unresolved, whole = {}, [], []
    for m in JS_ENV.finditer(text):
        rest = text[m.end():]
        where = f"{rel}:{text.count(chr(10), 0, m.start()) + 1}"
        dot = JS_DOT.match(rest)
        lit = None if dot else JS_LIT.match(rest)
        if dot or lit:
            names.setdefault(dot.group(1) if dot else lit.group(2), []).append(where)
        elif JS_IDX.match(rest):
            unresolved.append(f"{where} — 열쇠가 리터럴이 아니다")
        else:
            whole.append(where)
    return names, unresolved, whole


def scan_code(root, skip=SKIP):
    names, indirect, unresolved, outside, whole, files = {}, [], [], [], [], 0
    for path, rel in _walk(root, ".py", skip):
        got, ind, unr, out, wh = scan_module(rel.as_posix(),
                                             path.read_text(encoding="utf-8"))
        for n, where in got.items():
            names.setdefault(n, []).extend(where)
        indirect += ind
        unresolved += unr
        outside += out
        whole += wh
        files += 1
    js_files = 0
    for path, rel in _walk(root, ".mjs", skip):
        got, unr, wh = scan_js(rel.as_posix(), path.read_text(encoding="utf-8"))
        for n, where in got.items():
            names.setdefault(n, []).extend(where)
        unresolved += unr
        whole += wh
        js_files += 1
    return Code(names, indirect, unresolved, outside, whole, files, js_files)


def is_ours(name, ours):
    """이 이름이 **우리가 지은 것**인가 — ①이 무는 범위가 이 한 줄이다."""
    if name in NOT_OURS:
        return False
    return True if ours == ALL else name.startswith(tuple(ours))


def compare(doc, code, ours):
    """(문서에 없는 이름, 실물 없는 줄).

    ①만 그물을 본다. **②는 접두사를 안 본다** — 문서가 든 이름은 우리 것이든 아니든 읽는
    자리가 있어야 한다. 소유 밖으로 뺀 이름만 양쪽에서 함께 빠진다.
    """
    missing = sorted(n for n in code if is_ours(n, ours) and n not in doc)
    ghost = sorted(n for n in doc if n not in code and n not in NOT_OURS)
    return missing, ghost


# ── §1 자기 이빨 — 손댄 사본으로 이 판정이 정말 무는지 본다. **실물 판정보다 먼저 선다.**

FIX_DOC = Path("docs") / "env.md"
FIX_OURS = ("SEEDNET_",)
SEED_DOC = ("| 변수 | 무엇을 정하나 |\n|---|---|\n"
            "| `SEEDNET_ONE` | 첫째 |\n"
            "| `SEEDNET_TWO` | 둘째 |\n")
SEED_CODE = ('import os\n'
             'A = os.environ.get("SEEDNET_ONE")\n'
             'B = os.environ["SEEDNET_TWO"]\n')
# 이름이 **표에 담겨** 도는 꼴 — 키 묶음이 이 모양이다
SEED_TABLE = ('import os\n'
              'BUNDLE = {"g": ("SEEDNET_ONE", "SEEDNET_TWO")}\n'
              'def pick(g):\n'
              '    for n in BUNDLE.get(g, ()):\n'
              '        if os.environ.get(n):\n'
              '            return os.environ[n]\n'
              '    return ""\n')


def _plant(doc_text, code_text, js_text=None):
    """문서 한 장과 파이썬 한 장(그리고 시키면 `.mjs` 한 장)만 세운 임시 나무."""
    root = Path(tempfile.mkdtemp(prefix="env-names-"))
    (root / FIX_DOC).parent.mkdir(parents=True)
    (root / FIX_DOC).write_text(doc_text, encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "x.py").write_text(code_text, encoding="utf-8")
    if js_text is not None:
        (root / "eye").mkdir()
        (root / "eye" / "x.mjs").write_text(js_text, encoding="utf-8")
    return root


def _survey(root, ours=FIX_OURS):
    doc = scan_doc((root / FIX_DOC).read_text(encoding="utf-8"))
    return compare(doc, scan_code(root).names, ours)


def teeth():
    """손댄 사본이 정말 빨강을 내나 — 양성 대조가 맨 앞에 선다."""
    tmps = []
    try:
        # ㉮ 양성 대조 — 안 건드린 사본은 초록이라야 한다. 이게 없으면 아래 빨강이
        #    「손댄 탓」인지 「사본이 애초에 깨진 탓」인지 안 갈린다.
        base = _plant(SEED_DOC, SEED_CODE); tmps.append(base)
        got = _survey(base)
        report("㉮ 안 건드린 사본은 초록이다 (양성 대조)", got == ([], []),
               [f"실측 {got} — 기대 ([], [])"])

        # ㉯ 문서에 가짜 줄 → ② 갈래(실물 없는 줄)
        ghost_name = "SEEDNET_GHOST"
        doc_bad = _plant(SEED_DOC + f"| `{ghost_name}` | 아무도 안 읽는다 |\n",
                         SEED_CODE); tmps.append(doc_bad)
        got = _survey(doc_bad)
        report(f"㉯ 문서에 가짜 이름을 심으면 빨강이다 ({ghost_name})",
               got == ([], [ghost_name]),
               [f"실측 {got} — 기대 ([], [{ghost_name!r}])"])

        # ㉰ 코드에 가짜 읽기 → ① 갈래(문서에 없는 이름)
        new_name = "SEEDNET_PLANTED"
        code_bad = _plant(SEED_DOC,
                          SEED_CODE + f'C = os.environ.get("{new_name}")\n')
        tmps.append(code_bad)
        got = _survey(code_bad)
        report(f"㉰ 코드에 가짜 읽기를 심으면 빨강이다 ({new_name})",
               got == ([new_name], []),
               [f"실측 {got} — 기대 ([{new_name!r}], [])"])

        # ㉱ **이름표를 도는 꼴이 정말 풀리나.** 이게 없으면 리터럴만 세는 좁은 그물로
        #    돌아가도 ㉮㉯㉰ 가 다 초록이라, 없는 어긋남 둘이 조용히 선다.
        table = _plant(SEED_DOC, SEED_TABLE); tmps.append(table)
        got = _survey(table)
        report("㉱ 이름표를 도는 읽기도 풀린다 (리터럴이 한 자도 없는 사본)",
               got == ([], []),
               [f"실측 {got} — 기대 ([], []). 못 풀면 표 줄 둘이 「실물 없는 줄」로 뜬다"])

        # ㉲ 못 푼 자리가 정말 **빨강으로** 서나 — 「못 쟀다」가 초록에 묻히면 ②가 눈이 먼다
        blind = _plant(SEED_DOC, SEED_CODE + 'D = os.environ.get(globals()["z"])\n')
        tmps.append(blind)
        stuck = scan_code(blind).unresolved
        report("㉲ 열쇠를 못 푸는 읽기는 못 푼 자리로 선다", bool(stuck),
               [f"실측 {stuck} — 기대 한 자리 이상"])

        # ㉳ **이름 없이 통째로 넘기는 자리가 정말 세어지나.** 판정 곁의 「안 쟀다」 줄이
        #    이걸로 서는데, 삼켜지면 그 줄이 「없다」고 **거짓말을 한다** — 판정은 초록인 채로.
        pipe = _plant(SEED_DOC, SEED_CODE + 'import subprocess\n'
                                            'subprocess.run(["x"], env=os.environ)\n')
        tmps.append(pipe)
        passed = scan_code(pipe).whole
        report("㉳ 이름 없이 통째로 넘기는 자리는 그 자리로 센다 (`env=os.environ`)",
               bool(passed), [f"실측 {passed} — 기대 한 자리 이상"])

        # ㉴ **`.mjs` 의 읽기가 정말 세어지나.** 이게 없으면 그물이 파이썬으로 좁아져도
        #    위 이빨이 다 초록이라, 화면 검사만 읽는 이름이 조용히 「실물 없는 줄」이 된다.
        js_name = "SEEDNET_JS_ONLY"
        js = _plant(SEED_DOC + f"| `{js_name}` | `.mjs` 만 읽는다 |\n", SEED_CODE,
                    f"const a = process.env.{js_name};\n")
        tmps.append(js)
        got = _survey(js)
        report(f"㉴ `.mjs` 의 읽기도 세어진다 ({js_name})", got == ([], []),
               [f"실측 {got} — 기대 ([], []). 못 세면 표 줄이 「실물 없는 줄」로 뜬다"])

        # ㉵ `.mjs` 에서도 **못 푼 열쇠는 빨강이다** — 파이썬 쪽 ㉲ 와 같은 자를 댄다.
        js_blind = _plant(SEED_DOC, SEED_CODE, "const b = process.env[pick()];\n")
        tmps.append(js_blind)
        stuck = scan_code(js_blind).unresolved
        report("㉵ `.mjs` 의 리터럴 아닌 열쇠도 못 푼 자리로 선다", bool(stuck),
               [f"실측 {stuck} — 기대 한 자리 이상"])

        # ㉶㉷ **소유 그물이 ①의 범위를 정한다** — 한 나무를 두 그물로 재어 그 가름을 보인다.
        #     이 둘이 없으면 그물이 어느 쪽으로 굳어도 위 이빨이 다 초록이라, ①이 통째로
        #     항진명제가 되거나(좁게) 남의 이름으로 빨강을 내도(넓게) 아무 데서도 안 보인다.
        naked = "NAKED_OUTSIDER"
        wide = _plant(SEED_DOC, SEED_CODE + f'E = os.environ.get("{naked}")\n')
        tmps.append(wide)
        got = _survey(wide, FIX_OURS)
        report(f"㉶ 접두어 그물 밖의 새 읽기는 ①이 안 문다 ({naked})", got == ([], []),
               [f"실측 {got} — 기대 ([], []). 물면 이 표가 남의 도구 설명서가 된다"])
        got = _survey(wide, ALL)
        report(f"㉷ 그물을 전부로 고르면 접두어 없는 이름도 ①이 문다 ({naked})",
               got == ([naked], []),
               [f"실측 {got} — 기대 ([{naked!r}], []). 안 물면 그 저장소의 ①은 항진명제다"])

        # ㉸ **소유 밖 목록이 ①과 ② 양쪽에서 함께 빠지나.** 그물을 전부로 고른 저장소는
        #    바깥 이름을 뺄 자리가 이 목록 하나뿐이라, 한쪽만 빠지면 그 저장소가 ①을 끈다.
        lent, ghosted = "LENT_BY_OUTSIDE", "GHOSTED_BY_OUTSIDE"
        pair = _plant(SEED_DOC + f"| `{ghosted}` | 바깥이 정한 이름 |\n",
                      SEED_CODE + f'F = os.environ.get("{lent}")\n')
        tmps.append(pair)
        NOT_OURS[lent] = "이빨이 세운 검체 — 코드가 읽되 우리가 안 지은 이름"
        NOT_OURS[ghosted] = "이빨이 세운 검체 — 문서가 들되 우리 소스가 안 읽는 이름"
        try:
            got = _survey(pair, ALL)
        finally:
            del NOT_OURS[lent], NOT_OURS[ghosted]
        report("㉸ 소유 밖으로 뺀 이름은 ①도 ②도 안 문다", got == ([], []),
               [f"실측 {got} — 기대 ([], []). 한쪽만 빠지면 넓은 그물을 든 저장소가 ①을 끈다"])
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)


# ── 손잡이를 읽는다 — argv 가 먼저, 환경변수가 그 다음

def _opt(argv, flag, env_name):
    if flag in argv:
        i = argv.index(flag)
        return argv[i + 1] if i + 1 < len(argv) else None
    return os.environ.get(env_name)


def _positional(argv):
    out, eat = [], False
    for a in argv[1:]:
        if eat:
            eat = False
            continue
        if a in FLAGS:
            eat = True
            continue
        if a.startswith("--"):
            continue
        out.append(a)
    return out


HOWTO = ("어떻게 주나 — `--doc <나무뿌리 기준 문서 경로>` 와 `--ours <접두어[,접두어…]>` 또는 "
         f"`--ours '{ALL}'`(읽는 이름 전부가 우리 것). 환경변수 {ENV_DOC}·{ENV_OURS} 로도 받는다. "
         "나무뿌리는 첫 자리 인자이고 안 주면 이 폴더의 윗자리다. 그물을 기본값으로 안 까는 "
         "까닭은 이 파일 머리말이 든다")


def main(argv):
    args = _positional(argv)
    root = Path(args[0]).resolve() if args else HERE.parent
    doc_arg = _opt(argv, "--doc", ENV_DOC)
    ours_arg = _opt(argv, "--ours", ENV_OURS)
    skip_arg = _opt(argv, "--skip", ENV_SKIP)

    lack = [n for n, v in (("--doc", doc_arg), ("--ours", ours_arg)) if not v]
    if lack:
        raise Unmeasured(f"[안 잼] 손잡이가 없다 — {' · '.join(lack)}. {HOWTO}")

    ours = ALL if ours_arg.strip() == ALL else tuple(
        p.strip() for p in ours_arg.split(",") if p.strip())
    if not ours:
        raise Unmeasured(f"[안 잼] 소유 그물이 빈 글자다 — ①이 아무것도 안 물어 항진명제가 "
                         f"된다. {HOWTO}")
    skip = SKIP | {d.strip() for d in (skip_arg or "").split(",") if d.strip()}
    doc_path = Path(doc_arg) if Path(doc_arg).is_absolute() else root / doc_arg

    print("--- §1 자기 이빨 — 손댄 사본이 정말 빨강을 내나 (양성 대조가 먼저 선다)")
    teeth()
    bitten = len(passes()) + len(fails())

    print(f"\n--- §2 실물 대조 — {root}")
    if not doc_path.is_file():
        raise Unmeasured(f"[안 잼] 문서가 없다 — {doc_path}. {HOWTO}")

    doc = scan_doc(doc_path.read_text(encoding="utf-8"))
    code = scan_code(root, skip)

    # 한쪽이 빈손이면 차집합이 늘 0 이라 **아무것도 안 재고 초록이 난다.**
    if not doc or not code.names:
        raise Unmeasured(f"[안 잼] 한쪽이 빈손이다 — 문서 이름 {len(doc)}개 · 코드가 읽는 "
                         f"이름 {len(code.names)}개. 둘 중 하나가 비면 차집합이 늘 0 이라 "
                         f"판정이 안 선다. {HOWTO}")

    rel_doc = doc_arg if not Path(doc_arg).is_absolute() else doc_path.name
    net = "읽는 이름 전부" if ours == ALL else " · ".join(f"`{p}…`" for p in ours)
    missing, ghost = compare(doc, code.names, ours)
    report(f"문서에 없는 이름이 없다 — 코드가 읽는 소유 그물({net}) 마다 제 줄이 있다",
           not missing,
           [f"{n} — 읽는데 {rel_doc} 에 줄이 없다 ({' · '.join(code.names[n])})"
            for n in missing])
    report("실물 없는 줄이 없다 — 문서의 이름마다 읽는 자리가 있다", not ghost,
           [f"{n} — {rel_doc} 에 줄은 있는데 읽는 자리가 없다" for n in ghost])
    report("열쇠를 못 푼 읽기 자리가 없다", not code.unresolved,
           [f"{w} — 이름을 못 세 이 자리는 대조 밖이다" for w in code.unresolved])
    report("그물 밖의 읽기 꼴이 없다", not code.outside, list(code.outside))

    edge(f"쟀다: 문서 이름 {len(doc)}개 ↔ 코드가 읽는 이름 {len(code.names)}개 "
         f"(파이썬 {code.files}장 — 표 칸 대 AST · `.mjs` {code.js_files}장 — 정규식)")
    for line in code.indirect:
        edge(f"이름표를 풀어 셌다 — {line}")
    for name, why in sorted(NOT_OURS.items()):
        edge(f"근거 대고 뺐다 — {name}: {why}")
    if not NOT_OURS:
        edge("소유 밖으로 뺀 이름 — 이 나무에는 없다(`NOT_OURS` 가 비었다). 바깥이 정한 "
             "이름을 뺄 자리가 거기다 — 까닭 없이 빼면 눈감은 것이다")
    outsiders = sorted(n for n in code.names if not is_ours(n, ours))
    edge(f"안 쟀다 — 소유 그물({net}) 밖의 **새** 읽기는 ①이 안 문다. 이번 판에서 그런 "
         f"이름: " + (" · ".join(outsiders) or "없다"))
    edge("안 쟀다 — " + " · ".join(f"`{d}/`" for d in sorted(skip))
         + " · 점으로 시작하는 폴더")
    edge("느슨하게 쟀다 — `.mjs` 는 AST 가 아니라 정규식이다(주석에 적힌 "
         "`process.env.X` 도 읽기로 세어져, 없는 읽는 자리를 하나 세울 수 있다)")
    edge("안 쟀다 — 이름 없이 통째로 넘기는 자리 "
         + (" · ".join(code.whole) if code.whole else "없다")
         + " (자식에게 환경을 물려주는 꼴이라 셀 이름이 없다)")
    edge("안 쟀다 — 표 밖 산문이 든 이름. 문서가 「변수가 아닌데 환경이 정하는 것」으로 "
         "따로 가른 자리(`PATH` 따위)라, 물면 변수 아닌 것을 변수로 세운다")
    edge("안 쟀다 — **어느 나무가** 읽나. 문서가 앱이 읽는 표와 검사만 읽는 표를 갈라 "
         "적어도 이 검사는 둘을 한 자루로 센다 — 이름이 앱에서 검사로 옮겨 앉아도 조용하다")
    edge(f"안 쟀다 — 이 파일이 제 손잡이를 받는 환경변수({ENV_DOC} · {ENV_OURS} · "
         f"{ENV_SKIP})가 **제 그물에 드는가**. 이 파일이 재이는 나무 안에 살면 든다 — "
         "접두어 그물에서는 밖이라 조용하고, 전부를 고른 저장소는 문서에 줄을 두거나 "
         "소유 밖으로 뺀다")
    edge("안 쟀다 — 그 줄이 **무엇을 정하나**. 뜻은 사람이 실물을 읽고 적은 판단이다")

    bad = fails()
    if bad:
        print(f"\n❌ {len(bad)}건 실패 — {' · '.join(bad)}", file=sys.stderr)
        return EXIT_MISMATCH
    print(f"\n✅ 문서와 실물의 이름이 맞는다 — 판정 {len(passes())}건 "
          f"(자기 이빨 {bitten}건 · 실물 대조 {len(passes()) - bitten}건 · "
          f"문서 {len(doc)} ↔ 코드 {len(code.names)})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
