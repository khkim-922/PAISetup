"""`.mjs`·`.sh`·`.ps1` 검사가 종료코드 계약과 초록 줄을 지키나 — 글자 꼴로 문다.

좌표 — 계약의 뜻은 곁 `README.md` §종료코드 가 들고, 숫자와 「못 쟀다」 손은 `_verdict.py` 가 든다.
같은 축의 파이썬 판은 `exit_code_check.py`(나가는 자리)와 `verdict_line_check.py`(초록 줄) 둘인데,
**둘 다 파이썬 AST 만 읽는다** — 그래서 곁 `README.md` 「무엇을 안 재나」 첫 줄이 이 자리를 비워
두었다. 이 자가 그 줄을 닫는다. 실측 근거는 claude-config #25 의 가족 1·2·3 이다.

    python -X utf8 _check/shell_exit_check.py            # 이 폴더
    python -X utf8 _check/shell_exit_check.py <폴더>     # 잴 폴더를 지정 (병렬 작업나무)

**왜 이 검사가 있나.** 종료코드(0 쟀고 맞다 · 1 어긋났다 · 2 못 쟀다)는 훅과 CI 가 읽는 **유일한
말**이고, 그 계약은 언어를 안 가린다 — 훅은 `.py` 든 `.mjs` 든 `.sh` 든 같은 자리에서 코드만 본다.
그런데 무는 자가 파이썬에만 있으면 **계약이 언어 경계에서 조용히 끊긴다**: 같은 폴더 안에서 `.py`
는 물리고 그 곁의 `.mjs` 는 안 물린다. 안 물린 쪽이 안 지킨다는 말이 아니라, 지켰는지 아닌지를
**아무도 모른다**는 말이다. 여기가 그 자리다.

재는 것 다섯 — 언어마다 무는 자리가 다르다:

  ① `.mjs` **문자열로 나간다** — `process.exit("글자")`. 노드는 그 값을 정수로 못 읽고, 읽히는
     자리에서도 계약의 셋과 아무 관계가 없다. 화면은 까닭을 말하는데 코드만 조용히 틀린다.
  ② **계약 밖 값** — 세 갈래 다. 0·1·2 아닌 정수로 나간다. 훅이 갈래를 못 가르고, 못 가른 것을
     대개 「0 이 아니니 어긋남」으로 뭉갠다 — 「못 쟀다」가 판정으로 새는 자리다.
  ③ `.mjs` **손글자 2** — 「못 쟀다」를 정수 리터럴로 짓는다. `.mjs` 는 계약 상수를 제 파일에 둘
     수 있으므로(`const EXIT_UNMEASURED = 2`) **이름으로 나가는 것**이 계약이다. 리터럴로 적으면
     그 뜻이 그 자리에서만 살고, 계약이 움직여도 안 따라온다.
  ④ `.mjs` **인자 없음** — `process.exit()` 는 `process.exitCode`(안 세우면 0)로 나간다. 나가는
     자리에 뜻을 안 적었는데 **초록이 난다** — ①·② 보다 조용하다.
  ⑤ `.mjs` **초록 줄의 손글자 건수** — `console.log` 안의 「통과」 문구가 `${…length}` 같은 파생
     없이 「20건」 꼴로 수를 들었다. 손으로 적은 수는 절이 통째로 사라져도 그대로고 종료코드도 0
     그대로라, **판정이 줄어든 것을 볼 자가 없다**. 파이썬 판 `verdict_line_check` ② 와 같은 규율.
     **그물은 「숫자+셈낱말」이다** — 숫자만 물면 절 이름(「[3] 문 넷 … 통과시키나」)이 걸린다.

⚠ **`.sh`·`.ps1` 은 ③ 을 안 문다.** 그 두 언어에는 계약 상수를 둘 자리가 마땅찮아 `exit 2` 가 곧
  제 꼴이다. 같은 글자가 `.mjs` 에서는 어긋남이고 `.sh` 에서는 제 꼴인 것이 이 자의 갈림이다.

⚠ **「못 쟀다」 글자 뒤의 `exit 0` 은 안 물고 센다.** 못 잰 것을 0 으로 내보내는 자리는 #25 의
  가족 2 인데, 그것이 **꼴이 아니라 뜻**이다 — 그 갈래가 옳은지는 그 검사가 무엇을 재려 했나에
  달렸고 글자로는 안 갈린다. 그래서 판정을 안 내고 개수만 찍는다. **정하는 것은 사람이다.**

⚠ **양성 대조가 판정보다 먼저 선다.** 어긋남 0 은 그 자체로 초록이 아니다 — 걷어 내는 손이
  통째로 죽어도 0 이 난다. §1 이 **갈래마다 일부러 어긋난 검체**로 다섯이 실제로 무는지 보이고,
  §2 가 세 언어의 제 꼴은 안 무는지 **센 자리 수까지** 보인다. 파일을 한 장도 못 읽으면 초록이
  아니라 「못 쟀다」(2)로 나간다.

⚠ **AST 가 없다 — 글자 꼴로 문다.** 세 언어의 파서를 안 들이고, 대신 주석과 문자열을 **자리를
  남긴 채** 공백으로 갈아 낸 사본에서 꼴을 찾고 값은 원문에서 읽는다. 걷는 것은 `//`·`#` 줄
  주석 · `/* */`·`<# #>` 블록 · 따옴표 문자열 · 셸 헤어독(`<<TAG`) · PS 해어스트링(`@' '@`)이다.

**안 재는 것** — `.mjs` 템플릿 문자열 **안의 `${…}` 속 코드**(그 조각은 문자열로 읽고 지나간다 —
거기 든 `process.exit` 은 안 보인다) · **정규식 리터럴**(`/["']/` 처럼 따옴표를 든 정규식은 문자열
로 잘못 읽힌다. 그 판은 따옴표가 안 닫혀 **「못 읽은 파일」로 빠지지 초록에 안 든다**) ·
`process.exitCode = N` 꼴(나가는 자리가 아니라 값을 세워 두는 자리라 꼴이 다르다) · `.sh`·`.ps1`
의 **인자 없는 `exit`**(`$?` 로 나가는데 그 값은 원문에 없다) · `.sh`·`.ps1` 의 초록 줄(⑤ 는
`console.log` 를 그물로 쓴다 — 그 둘은 찍는 손이 갈래가 많아 그물이 안 선다) · **한국어 수사로
적은 건수**(「탭 경계 다섯」이 일곱이 돼도 여기는 초록이다 — 글자가 곧 뜻이라 사람이 읽는다) ·
**건수가 아예 없는 초록 줄**(⑤ 는 손글자 숫자를 무는 자지 없는 숫자를 무는 자가 아니다) ·
「못 쟀다」의 **갈래 선택**(위 ⚠ 가 든다 — 세기만 한다) · **그 코드로 실제로 나가나**(돌려 보지
않고 원문만 읽는다).

토큰도 망도 브라우저도 안 쓴다.
"""
import re
import sys
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report, show

HERE = Path(__file__).resolve().parent

CONTRACT = (0, 1, 2)        # 진본은 곁 `README.md` §종료코드
UNMEASURED_CODE = 2         # `.mjs` 에서만 문다 — 아래 LITERAL_TWO 가 그 갈림을 든다
SUFFIXES = (".mjs", ".sh", ".ps1")
LITERAL_TWO = (".mjs",)     # 손글자 2 를 어긋남으로 보는 갈래 — 계약 상수를 둘 자리가 있는 쪽

# 걷는 손 — 언어마다 주석과 문자열의 꼴이 다르다.
LINE_COMMENT = {".mjs": "//", ".sh": "#", ".ps1": "#"}
BLOCK_COMMENT = {".mjs": ("/*", "*/"), ".ps1": ("<#", "#>")}
QUOTES = {".mjs": "'\"`", ".sh": "'\"", ".ps1": "'\""}

MJS_EXIT = re.compile(r"process\s*\.\s*exit\s*\(")
MJS_LOG = re.compile(r"console\s*\.\s*log\s*\(")
SH_EXIT = re.compile(r"(?<![\w.$-])exit(?![\w-])")
PS_EXIT = re.compile(r"(?<![\w.$-])exit(?![\w-])", re.IGNORECASE)
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
# 정규식과 나눗셈을 가르는 어림 — 앞의 뜻 있는 글자가 자리를 여는 쪽이면 정규식이다.
# **걷어야 하는 까닭** — 따옴표를 든 정규식(`/HOME_SCREEN = "([^"]+)"/`)을 글자로 안 읽으면
# 거기서 문자열이 열려 그 뒤가 통째로 글자가 된다. 실측: AI-prompt-helper `screen_check.mjs:54`
# 가 그 꼴이고, 옛 판은 그 파일의 나가는 자리 셋을 **하나도 못 보고 초록**을 냈다.
REGEX_OPENS = set("(,=:[!&|?{};+-*%~^<>")
REGEX_WORD = re.compile(r"(?:^|[^\w$])(return|typeof|instanceof|case|do|else|void|yield|await)$")

GREEN_WORD = "통과"
ESCAPES = re.compile(r"\\u\{[^}]*\}|\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}|\\.")
# 손글자 건수 — **숫자만으로는 안 문다.** 셈낱말이 바로 뒤에 붙은 숫자만 건수로 읽는다.
# 그냥 숫자를 다 물면 절 이름(「[3] 문 넷 — … 통과시키나」)까지 걸린다 — 아뜰리에
# `text_gate.mjs:169` 가 그 꼴로 이 그물의 첫 판에 잘못 걸렸다.
HAND_COUNT = re.compile(r"\d+\s*[건장곳개항줄]")
INT_ONLY = re.compile(r"[+-]?\d+")
NAME_ONLY = re.compile(r"[\w.$\[\]{}:@-]+")

# 「못 쟀다」를 말하는 글자 그물 — **판정이 아니라 셈에만 쓴다**. 같은 뜻을 다른 말로 적은
# 자리는 이 그물에 안 걸린다. 넓히면 셈이 부풀고 좁히면 샌다 — 어느 쪽도 판정이 아니라
# 괜찮다. 세는 까닭은 그 자리가 **있다는 것**을 사람 눈앞에 두기 위해서다.
UNMEASURED_WORDS = ("못 쟀다", "못 잰", "잴 것이 없다", "안 쟀다", "못 쟤")
UNMEASURED_NAME = re.compile(r"UNMEASURED", re.IGNORECASE)


# ── 주석과 문자열을 걷는다 — 자리는 남긴다 ────────────────────────────────────

def _wipe(out, a, b):
    """[a, b) 를 공백으로 간다 — **줄바꿈은 남긴다.** 자리와 줄 수가 원문과 맞아야 한다."""
    for k in range(a, min(b, len(out))):
        if out[k] != "\n":
            out[k] = " "


def _close_quote(src, i, q, suffix):
    """따옴표 안쪽 끝 — 닫는 따옴표 **다음** 자리. 못 닫으면 None.

    셸의 홑따옴표는 안에 달아나기가 없다 — 거기서 `\\'` 를 이어 읽으면 그 뒤가 통째로
    문자열이 되어 나가는 자리가 사라진다.
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
    """그 `/` 가 정규식의 시작인가 — 나눗셈과 가르는 어림.

    앞의 뜻 있는 글자가 값이면 나눗셈이고, 자리를 여는 글자(`(`·`=`·`,` …)나 낱말이면
    정규식이다. 이미 걷은 사본을 뒤로 읽으므로 주석은 공백이 되어 저절로 건너뛴다.
    """
    k = i - 1
    while k >= 0 and out[k] in " \t\r\n":
        k -= 1
    if k < 0 or out[k] in REGEX_OPENS:
        return True
    return bool(REGEX_WORD.search("".join(out[max(0, k - 12):k + 1])))


def _regex_end(src, i):
    """정규식 리터럴의 끝 — 닫는 `/` 다음의 깃발까지. 나눗셈이었으면 None.

    `[…]` 안의 `/` 는 달아나기 없이 글자다. 줄을 넘으면 정규식이 아니다.
    """
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

    `${…}` 안은 글자가 아니라 **코드**다. 안 따라 들어가면 거기 든 중첩 템플릿의 백틱을
    닫는 백틱으로 읽어 **그 뒤가 한 자리씩 밀린다** — 밀린 쪽에서는 나가는 자리가 통째로
    글자가 되어 「어긋남 0」 초록이 난다. 실측으로 걸린 자리는 아뜰리에
    `pick_and_clear.mjs:65` 와 AI-prompt-helper `screen_check.mjs:918` 이다.
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
    """(걷어 낸 사본, 걷어 낸 문자열들) — 사본은 원문과 **길이도 줄도 같다**.

    꼴은 사본에서 찾고 값은 원문의 같은 자리에서 읽는다. 이 짝이 이 자의 밑판이다 —
    주석에 적힌 `process.exit` 이나 글자로 찍는 `exit 1` 을 나가는 자리로 세면 실물
    전수가 통째로 거짓이 된다(실측: `check-rails.mjs:48` · `check-deploy-probes.sh:65`).
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


# ── 나가는 자리를 걷어 낸 사본에서 찾는다 ─────────────────────────────────────

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
    """삼항이면 가지를 다 돌려준다 — 자리가 맞는 사본에서 가르고 원문에서 썬다.

    조건 쪽까지 함께 돌아오지만 이름·못 가름으로 떨어져 판정에 안 든다. **가지를 하나만
    보면 나머지 쪽에 숨은 손글자를 놓친다** — `exit(bad ? 1 : 2)` 가 그 꼴이다.
    """
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
    """나가는 자리 전부 — `(줄, 부르는 꼴, 원문 인자, [(갈래, 값)])`."""
    out = []
    if suffix == ".mjs":
        for m in MJS_EXIT.finditer(masked):
            close = _close_paren(masked, m.end() - 1)
            if close is None:
                continue
            raw, msk = src[m.end():close], masked[m.end():close]
            out.append((src.count("\n", 0, m.start()) + 1, "process.exit", raw.strip(),
                        [_one(p) for p in _branches(raw, msk)]))
        return out

    pattern = PS_EXIT if suffix == ".ps1" else SH_EXIT
    for m in pattern.finditer(masked):
        j = m.end()
        while j < len(masked) and masked[j] not in "\n;)}&|#":
            j += 1
        raw, msk = src[m.end():j], masked[m.end():j]
        out.append((src.count("\n", 0, m.start()) + 1, "exit", raw.strip(),
                    [_one(p) for p in _branches(raw, msk)]))
    return out


# ── 초록 줄 — `console.log` 안의 「통과」 문구가 건수를 파생하나 ────────────────

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
    """초록 줄의 손글자 숫자들 — `(파일, 줄, 갈래, 말)`."""
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


# ── 판정 ──────────────────────────────────────────────────────────────────────

def judge(src, rel, suffix):
    """원문 한 장의 어긋남들 — `(파일, 줄, 갈래, 말)`. 제 꼴이면 빈 목록."""
    masked, strings = blank(src, suffix)
    out = []
    for lineno, how, _raw, kinds in sites(src, masked, suffix):
        for kind, val in kinds:
            if kind == "문자열" and suffix == ".mjs":
                out.append((rel, lineno, "①",
                            f"`{how}({val!r})` 가 문자열로 나간다 — 계약의 셋과 아무 "
                            "관계가 없는 값이다. 「못 쟀다」가 판정으로 샌다"))
            elif kind == "없음" and suffix == ".mjs":
                out.append((rel, lineno, "④",
                            f"`{how}()` — 인자가 없다. `process.exitCode`(안 세우면 0)로 "
                            "나가 **뜻을 안 적고 초록이 난다**"))
            elif kind == "정수" and val == UNMEASURED_CODE and suffix in LITERAL_TWO:
                out.append((rel, lineno, "③",
                            f"`{how}({val})` — 「못 쟀다」를 손글자로 짓는다. 이 갈래는 "
                            "계약 상수를 제 파일에 둘 수 있다(`const EXIT_UNMEASURED = 2`)"))
            elif kind == "정수" and val not in CONTRACT:
                out.append((rel, lineno, "②",
                            f"`{how}({val})` — 계약 밖 값이다. 계약은 0·1·2 뿐이다"))
    if suffix == ".mjs":
        out += green_flaws(src, masked, strings, rel)
    return out


def boundaries(src, kinds_by_site):
    """「못 쟀다」를 찍고 `exit 0` 으로 나가는 자리 수 — **판정이 아니라 셈이다**(가족 2).

    같은 줄과 바로 앞 줄(빈 줄은 건너뛴다)을 본다 — 셸은 `{ echo …; exit 0; }` 로 한 줄에
    붙는 꼴이 흔하고, 따로 적는 꼴도 있다.
    """
    lines, n = src.splitlines(), 0
    for lineno, _how, _raw, kinds in kinds_by_site:
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


def has_unmeasured_branch(kinds_by_site):
    """그 원문에 「못 쟀다」(2)로 나가는 갈래가 있나 — 손글자 2 이거나 그 뜻의 이름이다."""
    for _lineno, _how, _raw, kinds in kinds_by_site:
        for kind, val in kinds:
            if kind == "정수" and val == UNMEASURED_CODE:
                return True
            if kind == "이름" and UNMEASURED_NAME.search(str(val)):
                return True
    return False


# ── §1 양성 대조 — 갈래마다 일부러 어긋난 검체로 다섯이 무는지 먼저 보인다 ─────

BAD = [
    ("①", ".mjs — 문자열로 나간다", ".mjs", """
process.exit("못 쟀다 — 검체가 없다");
"""),
    ("②", ".mjs — 계약 밖 값으로 나간다", ".mjs", """
process.exit(3);
"""),
    ("③", ".mjs — 삼항의 **한쪽**이 손글자 2 다", ".mjs", """
process.exit(bad ? 1 : 2);
"""),
    ("④", ".mjs — 인자 없이 나간다", ".mjs", """
process.exit();
"""),
    # ⚠ 검체의 손글자를 **이 파일에서는 이어 붙여** 둔다 — 한 상수로 두면 곁의
    #   `verdict_line_check.py` ② 가 제 검체를 문다. 검체 원문은 이어 붙인 결과라 그대로
    #   한 글자고, 그래서 ⑤ 가 문다.
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

# 제 꼴 — 세 언어가 저마다 계약을 지킨 원문이다. 걷는 손이 죽으면 여기 심어 둔 주석·문자열·
# 헤어독 속 가짜 나가는 자리가 살아나 **빨강이 난다** — 그것이 이 절의 이빨이다.
GOOD = {
    ".mjs": """
const EXIT_OK = 0, EXIT_MISMATCH = 1, EXIT_UNMEASURED = 2;
// 옛 판은 process.exit(3) 으로 나갔다 — 주석은 걷는다
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
console.log(fails ? `❌ ${fails}건 어긋남` : `✅ 전부 통과 (판정 ${results.length}건 — 위 경계 안에서)`);
process.exit(0);
process.exit(1);
process.exit(fails ? EXIT_MISMATCH : EXIT_OK);
""",
    ".sh": """
# 옛 판은 exit 3 으로 나갔다 — 주석은 걷는다
echo 'exit 9 는 글자다' > "$tmp/bare.sh"
cat <<'MSG'
여기 적힌 exit 8 도 글자다
MSG
[ -d "$DIR" ] || { echo "담긴 것이 없다 — 잴 것이 없다: $DIR"; exit 0; }
[ -n "$PY" ] || { echo "? 못 쟀다 — 파이썬을 못 부른다"; exit 2; }
exit "$rc"
""",
    ".ps1": """
# 옛 판은 exit 3 으로 나갔다 — 주석은 걷는다
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

# 제 꼴에서 세야 하는 「나가는 자리」 — **걷는 손의 센티널이다.** 이 수가 부풀면 주석·문자열을
# 못 걷은 것이고, 줄면 나가는 자리를 못 찾은 것이다. 둘 다 실물 전수의 0 을 거짓으로 만든다.
GOOD_SITES = {".mjs": 5, ".sh": 3, ".ps1": 3}


def positive_control():
    """검체가 실제로 그 꼴인지부터 묻는다 — 이 절이 빨강이면 아래 §3 의 0 은 뜻이 없다."""
    print(f"--- §1 양성 대조 — 일부러 어긋난 검체 {len(BAD)}이 정말 빨개지나")
    for want, said, suffix, src in BAD:
        got = judge(src, "<검체>", suffix)
        report(f"{want} {said}",
               len(got) == 1 and got[0][2] == want,
               [f"{len(got)}건 · 갈래 {[r[2] for r in got]} (기대 {want} 하나)"])

    print("\n--- §2 음성 대조 — 세 언어의 제 꼴은 한 자리도 안 문다")
    for suffix, src in GOOD.items():
        clean = judge(src, "<제 꼴>", suffix)
        report(f"{suffix} — 계약을 지킨 원문은 어긋남 0 이다", not clean,
               [f"{r[0]}:{r[1]} {r[2]} {r[3]}" for r in clean])
        masked, _ = blank(src, suffix)
        show(f"  {suffix} 에서 센 「나가는 자리」", len(sites(src, masked, suffix)), GOOD_SITES[suffix])

    sh = GOOD[".sh"]
    masked, _ = blank(sh, ".sh")
    show("  .sh 에서 센 「못 쟀다 뒤의 `exit 0`」", boundaries(sh, sites(sh, masked, ".sh")), 1)
    edge("**음성 대조가 이 판의 값을 절반 든다** — 양성만 보이면 「전부 빨강」인 자도 만점을 "
         "받는다. 위 자리 수가 어긋나면 걷는 손이 무너진 것이므로 함께 문다.")
    edge("**경계 셈은 판정이 아니라 이빨이다** — 위 한 자리는 「잴 것이 없다 … `exit 0`」 이라 "
         "빨강이 아니라 셈으로 나가야 맞다. 이 수가 0 이 되면 세는 손이 죽은 것이다.")


# ── §3 실물 전수 ───────────────────────────────────────────────────────────────

def sources(check_dir):
    """이 폴더의 `.mjs`·`.sh`·`.ps1` — 하위 폴더는 안 본다(검체·기록이다)."""
    return sorted(p for p in Path(check_dir).iterdir()
                  if p.is_file() and p.suffix in SUFFIXES)


def survey(check_dir):
    """(어긋남들, 갈래별 파일 수, 나가는 자리 수, 경계 셈, 2 갈래 없는 파일 수, 못 읽은 파일들)."""
    bad, seen, site_n, bound, no2, unreadable = [], {s: 0 for s in SUFFIXES}, 0, 0, 0, []
    for p in sources(check_dir):
        try:
            src = p.read_text(encoding="utf-8-sig")
            masked, _ = blank(src, p.suffix)
            found = sites(src, masked, p.suffix)
            bad += judge(src, p.name, p.suffix)
        except (OSError, ValueError) as exc:
            unreadable.append(f"{p.name} — {type(exc).__name__}: {exc}")
            continue
        seen[p.suffix] += 1
        site_n += len(found)
        bound += boundaries(src, found)
        no2 += 1 if found and not has_unmeasured_branch(found) else 0
    return bad, seen, site_n, bound, no2, unreadable


def main(argv):
    check_dir = Path(argv[1]).resolve() if len(argv) > 1 else HERE
    print(f"잴 폴더 — {check_dir}\n")

    positive_control()

    print("\n--- §3 실물 전수 — 이 폴더의 `.mjs`·`.sh`·`.ps1` 이 계약을 지키나")
    bad, seen, site_n, bound, no2, unreadable = survey(check_dir)

    # 센티널이 먼저다 — 한 장도 못 읽은 판은 어긋남 0 이 나도 초록이 아니다.
    total = sum(seen.values())
    if not total:
        raise Unmeasured(f"[안 잼] 읽은 파일이 0 이다 — {check_dir} 에 "
                         f"{' · '.join(SUFFIXES)} 원문이 없다. 어긋남 0 은 아무 뜻도 없다")

    for rel, lineno, kind, said in bad:
        report(f"{rel}:{lineno} — {kind}", False, [said])
    tally = " · ".join(f"`{s}` {seen[s]}장" for s in SUFFIXES)
    report(f"계약을 어기는 자리가 없다 ({tally} · 나가는 자리 {site_n}곳)", not bad)

    if unreadable:
        for row in unreadable:
            edge(f"**못 읽은 파일** — {row}")
        edge("못 읽은 파일은 판정이 아니라 **안 잰 자리**다 — 위 건수에서 빠져 있다.")

    edge(f"잰 범위 — `{check_dir.name}/` 의 {tally} 의 **나가는 자리 {site_n}곳**. "
         "하위 폴더와 이 폴더 밖은 안 든다 — 그 경계는 저장소의 지도가 든다.")
    edge(f"**「못 쟀다」를 찍고 `exit 0` 으로 나가는 자리 {bound}곳** — 판정을 안 냈다. "
         "그 갈래가 옳은지는 꼴이 아니라 뜻이라 **사람이 읽는다**(#25 가족 2).")
    edge(f"**2 로 나가는 갈래가 한 자리도 없는 파일 {no2}장** — 역시 판정이 아니다. "
         "잴 것이 늘 있는 게이트는 그 갈래가 없는 것이 맞고, 있어야 하는데 없는 자리와 "
         "글자로는 안 갈린다.")
    edge("**`.sh`·`.ps1` 의 손글자 2 는 안 문다** — 계약 상수를 둘 자리가 마땅찮아 "
         "`exit 2` 가 곧 제 꼴이다. 그 갈림은 `.mjs` 에만 선다.")
    edge("**한국어 수사로 적은 건수는 안 문다** — 「탭 경계 다섯」이 일곱이 돼도 여기는 "
         "초록이다. 그 자리는 사람이 읽는다.")
    edge("**「그 코드로 실제로 나가나」는 안 잰다** — 원문의 꼴까지다. 돌려 보지 않는다.")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        return EXIT_MISMATCH
    print(f"전부 통과 (판정 {len(passes())}건 — 양성 {len(BAD)} · 음성 {len(GOOD)}갈래 · 실물 전수 1)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
