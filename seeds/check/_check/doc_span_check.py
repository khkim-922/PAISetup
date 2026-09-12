r"""문서의 백틱 조각이 실물을 가리키나 — 경로는 나무에, 식별자는 코드에 있나.

좌표 — 이 자가 난 자리는 아뜰리에 #322 이고, 자기 이빨 규율은 아뜰리에 결정 0112 ·
씨앗 규율은 claude-config 결정 0040 이다.

    python -X utf8 _check/doc_span_check.py                  # 이 나무 · 선언은 곁 `doc_span.conf`
    python -X utf8 _check/doc_span_check.py <나무뿌리>        # 잴 나무를 지정 (병렬 작업나무)
    python -X utf8 _check/doc_span_check.py <나무뿌리> --conf <선언>

**왜 이 검사가 있나.** 문서가 `app/server.py` 나 `config.MODES` 를 백틱으로 가리킬 때, 그
좌표가 죽어도 **아무 데서도 안 터진다.** 마크다운 링크는 링크 검사가 물지만 백틱은 링크가
아니라 그 자가 안 본다. 그래서 옮기거나 이름을 바꾼 자리마다 문서만 조용히 낡고, 읽는
사람은 없는 것을 찾다 만다.

**그물이 좁으면 항진명제가 된다.** 확장자가 있는 경로만 보는 grep 은 `config.MODES` ·
`#planbox` · `paneGo` 를 한 건도 안 물고, `snake_case` 만 무는 그물은 화면 축(camelCase ·
DOM id)에서 0건으로 통과한다. **0 건이 초록으로 읽히는 그물은 안 재는 것과 같다.**

재는 것은 **꼴로 가른 뒤의 실재**다. 백틱 조각 하나하나에 꼴을 붙이고, 무는 꼴만 문다:
  · **경로** — `/` 가 들었거나 `/` 로 끝나거나 나무가 쓰는 확장자로 끝난다
    → 나무에 그 경로가 있어야 한다. 뿌리 기준 · 문서 자리 기준 · 꼬리 일치 · 이름만
      일치(홑이름으로 부르는 자리) 넷 중 하나로 푼다. `\` 는 `/` 로 눕혀 본다
  · **식별자** — `_` 가 들었거나 `a.b` 꼴이거나 `()` 로 끝나거나 `#id` · `.class` · camelCase
    → 선언한 코드 나무에 그 글자가 있어야 한다. `머리.꼬리` 는 머리가 우리 모듈이면
      **그 파일 안에서** 꼬리를 찾는다 — 문서는 `config.CSP_DOC` 로 부르지만 코드에는
      `CSP_DOC` 로 살지 통글자로 안 산다

## 그물은 한 벌이고 어휘가 저장소 것이다 — 이 씨앗의 가름

이 자를 씨앗으로 올리며 먼저 가른 것은 **그물 자체가 저장소마다 다시 서야 하는가**였다.
답은 **아니다** — 다만 **목록만 빼면 되는 것도 아니다.** 꼴 판정은 세 층으로 갈린다:

  ① **어느 저장소에서나 같은 꼴** — 빈칸이 들면 좌표 하나가 아니고, 따옴표가 들면
     리터럴이고, `=` 가 들면 값이 붙은 꼴이고, `/` 로 시작하면 이 나무의 상대 좌표가
     아니다. 이 층은 코드가 든다. 저장소가 손댈 자리가 없다
  ② **그 저장소의 나무가 정하는 것** — 무엇이 내 문서고 무엇이 내 코드인가 · 어떤 확장자를
     쓰나 · 깔아야 나는 폴더가 무엇인가. **목록이라 선언이 든다**
  ③ **그 저장소의 문서 어휘가 정하는 것** — 같은 꼴이 저장소마다 다른 것을 가리킨다.
     `#planbox` 는 화면을 든 저장소에서 DOM id 라 물어야 맞고, 이슈 번호를 `#5` 로 적는
     저장소에서는 물면 통째로 거짓 빨강이다. `$HOME/x` · `%USERPROFILE%\x` 도 경로 꼴인데
     좌표가 아니다. **이것이 「목록만 빼면 된다」가 안 되는 자리다** — 꼴 판정 안으로
     들어가는 선언이라 `[좌표가 아닌 머리]` 절이 따로 선다

그래서 **꼴을 새로 짓는 일은 받는 저장소에 없다.** 제 어휘를 머리글자로 적으면 그물이
그 자리에서 갈린다. ③ 을 ② 와 같은 「목록」으로 뭉뚱그리면, 받는 저장소는 거짓 빨강을
보고 **판정을 끄는 쪽**으로 간다 — 그 순간 이 검사는 다시 항진명제가 된다.

## 선언 — 받은 저장소가 무엇을 줘야 도나

**한 줄로 — 제 문서 나무와 코드 나무가 어디인가, 그리고 좌표가 아닌 머리글자와 근거 대고
뺀 이름이 무엇인가를 선언 한 장으로 준다.** 자리는 `<나무뿌리>/_check/doc_span.conf` 이고
`--conf` 로 다른 자리를 줄 수 있다. 없으면 초록이 아니라 「못 쟀다」(2)로 나간다.

    [문서]                 읽을 문서 — glob 과 홑파일. 비면 못 잰다
    [문서 · 안 본다]        이 접두어로 시작하는 문서는 안 읽는다 = 까닭
    [코드]                 식별자가 살 코드 나무 — glob. 비면 못 잰다
    [코드 · 확장자]         그중 이 확장자만 읽는다
    [모듈]                 `머리.꼬리` 의 머리로 풀 파일 — glob
    [나무에서 뺀다]         경로 쪽·코드 쪽 양쪽에서 뺄 폴더 이름 = 까닭
    [좌표가 아닌 머리]       이 글자로 시작하면 좌표가 아니다 = 까닭
    [나무 밖]              문서가 짚되 이 나무 밖에 사는 좌표 = 까닭
    [돌아야 나는 자리]       코드가 짓지만 그 일이 있어야 나는 자리 = 까닭

이름은 백틱으로 감쌀 수 있다 — `#` 로 시작하는 줄은 파서가 주석으로 읽으므로 **그 글자
자체를 이름으로 적을 때는 감싸야 한다**(`` `#` = 이슈 번호다 ``).

**목록에 이름을 적을 때는 까닭을 함께 둔다** — 까닭 없이 빼면 그냥 눈감은 것이고, 눈감은
자리는 다음 사람이 못 되짚는다. **빈 목록이 통과의 조건이 아니다.** 판정 곁에 이름과 까닭이
함께 찍히는 까닭이 그것이다 — 그 목록은 줄이려고 두는 것이지 채우려고 두는 것이 아니다.

⚠ **`[문서 · 안 본다]` 는 굳는 문서가 드는 자리다** — 결정 기록처럼 그때의 좌표가 사는 것이
  맞는 문서, 남의 글을 그대로 든 문서. 낡음이 아니라 사건이라 재면 거짓 빨강이 된다.

⚠ **`[돌아야 나는 자리]` 를 「코드가 그 이름을 쓰면 통과」라는 일반 규칙으로 바꾸지 않는다.**
  지운 파일의 이름은 다른 모듈의 주석·독스트링에 얼마든지 남아 있어, 그 규칙은 **파일이
  옮겨지고 지워지는 것**을 — 이 검사가 무는 첫째 낡음을 — 통째로 눈멀게 한다. 이름을 손으로
  적는 값이 여기 있다.

⚠ **코드 나무에 `.md` 를 들이지 않는다.** 들이면 문서가 제 조각을 제가 받아 주는 항진명제가
  선다(이 검사가 고치러 온 병 그대로). 돌아서 난 기록(`.log`)과 산출(`.json`)도 뺀다 —
  그것은 코드가 약속한 이름이 아니다.

⚠ **깔아야 나는 폴더를 나무로 세면 판정이 PC 마다 갈린다.** 깐 자리에서는 문서가 짚은
  라이브러리 파일이 「나무에 있다」로 풀려 초록이고, 갓 받은 자리(CI · 새 PC)에서는 같은
  문서가 빨갛다. 그런 이름은 `[나무에서 뺀다]` 와 `[나무 밖]` 이 까닭과 함께 든다.

## 무엇을 안 재나

⚠ **재는 것은 「그 글자가 있나」까지다.** 그 조각이 *맞는 것을 가리키나*는 못 잰다 —
  `config.MODES` 가 `config.py` 에 살아 있어도 문서가 그것을 **틀린 뜻으로** 적었으면 이
  검사는 초록이다. 뜻은 사람이 실물을 읽고 적은 판단이다.

⚠ **식별자는 통글자 검색이라 남의 자리에서도 걸린다** — 주석·문자열·다른 모듈의 같은
  이름이 다 통과시킨다. **「없다」는 확실하고 「있다」는 느슨한 자다.**

⚠ **어긋남 0 은 그 자체로 초록이 아니다.** 문서를 못 읽어도 0 이 나온다. 그래서 §1 이
  손댄 검체로 이 판정이 실제로 무는지를 **실물보다 먼저** 보이고, 선언이 없거나 문서·코드가
  빈손이면 초록이 아니라 「못 쟀다」(2)로 나간다.

토큰도 망도 브라우저도 안 쓴다.
"""
import configparser
import posixpath
import re
import shutil
import sys
import tempfile
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report

HERE = Path(__file__).resolve().parent
SELF = Path(__file__).name
CONF = "doc_span.conf"

SPAN = re.compile(r"`([^`\n]+)`")
FENCE = re.compile(r"^```.*?^```", re.S | re.M)

# 선언의 절 이름 — 진본은 이 파일 머리말 「선언」이다.
S_DOC, S_DOC_SKIP = "문서", "문서 · 안 본다"
S_CODE, S_CODE_EXT, S_MODULE = "코드", "코드 · 확장자", "모듈"
S_TREE_SKIP, S_HEAD = "나무에서 뺀다", "좌표가 아닌 머리"
S_OUTSIDE, S_RUNTIME = "나무 밖", "돌아야 나는 자리"

# 판정 곁에 이름과 까닭이 함께 찍히는 목록 — `(절 이름, 판정 화면에 쓸 이름)`.
TABLES = ((S_OUTSIDE, "나무 밖"), (S_RUNTIME, "돌아야 나는 자리"))


# ── 선언 — 그 저장소가 제 나무와 제 어휘를 준다

class Spec:
    """한 나무의 선언 — 목록과 까닭. 기본값을 안 든다(빈손이면 「못 쟀다」가 난다)."""

    def __init__(self, docs=(), doc_skip=None, code=(), code_ext=(), modules=(),
                 tree_skip=None, heads=None, outside=None, runtime=None):
        self.docs = tuple(docs)
        self.doc_skip = dict(doc_skip or {})
        self.code = tuple(code)
        self.code_ext = {e.lower() for e in code_ext}
        self.modules = tuple(modules)
        self.tree_skip = dict(tree_skip or {})
        self.heads = dict(heads or {})
        self.outside = dict(outside or {})
        self.runtime = dict(runtime or {})

    def table(self, section):
        return self.outside if section == S_OUTSIDE else self.runtime


def read_spec(path):
    """선언 한 장을 읽는다 — `키 = 까닭` 과 까닭 없는 홑줄을 함께 받는다.

    파서는 표준(`configparser`)이 든다. 손으로 쓰면 이어 줄·주석·절 가름을 다시 짓게 되고,
    그 셋이 다 이미 있는 자리다. 값 없는 키를 받으므로 glob 은 그냥 한 줄로 적는다.

    ⚠ **이름을 백틱으로 감쌀 수 있다.** 파서는 `#` 로 시작하는 줄을 주석으로 읽으므로,
      그 글자 자체를 이름으로 적으려면 감싸는 수밖에 없다 — 좌표를 백틱에 넣는 것은 이
      저장소들이 문서에서 이미 쓰는 꼴이라 새 문법이 아니다. 감싸지 않아도 받는다.
    """
    parser = configparser.ConfigParser(allow_no_value=True, interpolation=None,
                                       delimiters=("=",), comment_prefixes=("#",))
    parser.optionxform = str          # 키의 대소문자를 눕히지 않는다 — 이름이 곧 좌표다
    parser.read_string(path.read_text(encoding="utf-8-sig"))

    def name(key):
        k = key.strip()
        return k[1:-1] if len(k) > 2 and k[0] == k[-1] and k[0] in "`\"'" else k

    def keys(section):
        return tuple(name(k) for k in parser[section]) if parser.has_section(section) else ()

    def table(section):
        if not parser.has_section(section):
            return {}
        return {name(k): " ".join((v or "까닭이 안 적혔다").split())
                for k, v in parser[section].items()}

    return Spec(docs=keys(S_DOC), doc_skip=table(S_DOC_SKIP), code=keys(S_CODE),
                code_ext=keys(S_CODE_EXT), modules=keys(S_MODULE),
                tree_skip=table(S_TREE_SKIP), heads=table(S_HEAD),
                outside=table(S_OUTSIDE), runtime=table(S_RUNTIME))


# ── 꼴 가름 — 무는 것과 안 무는 것을 **한 자리에서** 이름으로 찍는다

def _has(s, chars):
    return any(c in s for c in chars)


def classify(span, exts, heads=()):
    """백틱 조각 하나의 꼴. `(이름, 무나)` 로 돌려준다 — 첫 맞는 데서 멈춘다.

    `heads` 는 그 저장소가 **좌표가 아니라고 선언한 머리글자**다. 꼴 판정 안으로 들어가는
    유일한 선언이고, 까닭은 이 파일 머리말 「이 씨앗의 가름」 ③ 이 든다.
    """
    s = span.strip()
    if _has(s, " \t"):
        return "명령줄·산문", False          # 빈칸이 들면 좌표 하나가 아니다
    if len(s) < 2 or not re.search(r"[A-Za-z0-9]", s):
        return "기호", False
    if _has(s, "<>*") or "…" in s:
        return "자리표시", False
    if _has(s, "[]{}"):
        return "묶음표", False               # 로그 태그 · 꾸러미 부품 이름 · 조각 문법
    if _has(s, "\"'"):
        return "리터럴", False
    if s.startswith("/"):
        return "절대 길", False              # 이 나무의 상대 좌표가 아니다 — 문·바깥 경로
    for head in heads:
        if s.startswith(head):
            return f"좌표가 아닌 머리({head})", False
    if "=" in s:
        return "값 붙은 꼴", False
    if ":" in s:
        return "선언·스킴", False            # `min-height:0` · `data:` · `file://`
    if s.startswith("-"):
        return "이름 조각·깃발", False       # `--dry` · `-web-ko.md`
    if re.fullmatch(r"[0-9][0-9./~,]*[A-Za-z]?", s):
        # 가름표가 들어도 온통 숫자면 걸음 표시(`6/7`)지 경로가 아니다 — 경로 판정보다
        # 먼저 선다. 숫자만으로 된 경로는 없으므로 이 자리에서 잃는 좌표가 없다.
        return "숫자", False
    if re.fullmatch(r"\.[A-Za-z0-9]+", s) and s.lower() in exts:
        return "확장자 이름", False          # 나무가 실제로 쓰는 확장자다
    if _has(s, "/\\") or s.endswith("/") or any(s.lower().endswith(e) for e in exts):
        return "경로", True
    if ("_" in s or s.endswith(")") or s.startswith("#") or s.startswith(".")
            or re.search(r"\.[A-Za-z_]", s) or re.search(r"[a-z][A-Z]", s)):
        return "식별자", True
    return "낱말", False


# ── 나무 쪽 — 경로가 실재하나

class Tree:
    """이 나무의 경로 한 벌 — 실재를 네 갈래로 푼다."""

    def __init__(self, root, spec):
        self.root = Path(root)
        self.paths = set()
        self.names = set()
        for p in self.root.rglob("*"):
            rel = p.relative_to(self.root)
            if any(part in spec.tree_skip for part in rel.parts):
                continue
            self.paths.add(rel.as_posix())
            self.names.add(p.name)
        self.exts = {("." + n.rsplit(".", 1)[1]).lower()
                     for n in self.names if "." in n[1:]}
        # 확장자를 뗀 이름 — 「안 문 낱말」 중 실은 좌표인 것을 세는 데 쓴다
        self.stems = {n.rsplit(".", 1)[0] if "." in n[1:] else n
                      for n in self.names}

    def holds(self, span, doc_rel):
        """이 경로 조각이 나무에 있나 — 뿌리·문서자리·꼬리·홑이름 넷 중 하나.

        **문서 자리 기준**을 함께 보는 까닭 — 참고 문서들은 서로를 `reference/env.md` ·
        `../_check/README.md` 처럼 제 자리에서 부른다. 뿌리 기준만 대면 그 꼴이 통째로
        거짓 빨강이 된다.

        ⚠ **`\\` 는 `/` 로 눕혀 본다** — 윈도우가 사는 저장소는 같은 자리를 `.\\deploy.ps1`
          로 적는다. 눕히기는 푸는 길을 더할 뿐이라 이미 풀리던 것을 빨갛게 못 만든다.
        """
        p = span.replace("\\", "/").rstrip("/")
        if p.startswith("./"):
            p = p[2:]
        if not p:
            return True                                  # `/` 하나는 길이지 경로가 아니다
        if p in self.paths:
            return True
        near = posixpath.normpath(posixpath.join(posixpath.dirname(doc_rel), p))
        if near in self.paths:
            return True
        if any(rp.endswith("/" + p) for rp in self.paths):
            return True
        return "/" not in p and p in self.names


# ── 코드 쪽 — 식별자가 실재하나

def code_corpus(root, spec):
    """코드 나무의 글자 한 자루와, 우리 모듈 이름 → 그 파일 글자."""
    root = Path(root)
    blob, files = [], []
    for g in spec.code:
        for p in sorted(root.glob(g)):
            rel = p.relative_to(root)
            # **이 파일은 제 증인이 못 된다** — 아래 자기 이빨의 씨 글자가 자루에 들면 심은
            # 가짜가 제 손으로 통과한다. 실제로 그렇게 통과했고, 양성 대조가 그 자리를 잡았다.
            if (not p.is_file() or p.suffix.lower() not in spec.code_ext
                    or p.name == SELF or any(x in spec.tree_skip for x in rel.parts)):
                continue
            try:
                blob.append(p.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, OSError):
                continue
            files.append(rel.as_posix())
    mods = {}
    for g in spec.modules:
        for p in sorted(root.glob(g)):
            try:
                mods.setdefault(p.stem, "")
                mods[p.stem] += p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
    return "\n".join(blob), mods, files


def code_holds(span, blob, mods):
    """이 식별자가 코드에 있나.

    `머리.꼬리` 는 머리가 우리 모듈이면 **그 파일 안에서** 꼬리를 찾는다 — 문서는
    `config.CSP_DOC` 로 부르지만 코드에는 `CSP_DOC` 로 산다. 통글자로 재면 우리가 쓰는
    가리킴 꼴 전부가 거짓 빨강이 된다.
    """
    s = span
    if s.endswith(")"):
        s = s.split("(", 1)[0]
    if s in blob:
        return True
    if "." in s[1:]:
        head, _, tail = s.partition(".")
        if head in mods and tail:
            return all(part in mods[head] for part in tail.split("."))
    return False


# ── 문서 쪽

def docs_of(root, spec):
    """읽을 문서 — glob 과 홑파일을 함께 받고, 안 보기로 한 접두어는 뺀다."""
    root = Path(root)
    out = []
    for g in spec.docs:
        hit = sorted(root.glob(g))
        out += hit if hit else ([root / g] if (root / g).is_file() else [])
    seen, kept = set(), []
    for p in out:
        rel = p.relative_to(root).as_posix()
        if not p.is_file() or rel in seen:
            continue
        if any(rel.startswith(s) for s in spec.doc_skip):
            continue
        seen.add(rel)
        kept.append(p)
    return kept


def allowed(span, spec):
    """허용 목록에 걸리면 `(목록 이름, 까닭)`. `/` 로 끝나는 줄은 그 아래 전부를 든다."""
    for section, label in TABLES:
        table = spec.table(section)
        if span in table:
            return label, table[span]
        for name, why in table.items():
            if name.endswith("/") and span.startswith(name):
                return label, why
    return None


def survey(root, spec):
    """(어긋남, 꼴별 건수, 안 문 견본, 조각 총수, 코드 장수, 못 문 좌표)."""
    root = Path(root)
    tree = Tree(root, spec)
    blob, mods, code_files = code_corpus(root, spec)
    bad, counts, samples, total = [], {}, {}, 0

    for doc in docs_of(root, spec):
        rel = doc.relative_to(root).as_posix()
        # 울타리 블록은 **빈 줄로 갈아** 지운다 — 통째로 지우면 뒤 줄 번호가 밀려
        # 좌표가 거짓말을 한다
        text = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"),
                         doc.read_text(encoding="utf-8"))
        for n, line in enumerate(text.splitlines(), 1):
            for raw in SPAN.findall(line):
                span = raw.strip()
                total += 1
                kind, bite = classify(span, tree.exts, spec.heads)
                counts[kind] = counts.get(kind, 0) + 1
                if not bite:
                    samples.setdefault(kind, set()).add(span)
                    continue
                hit = allowed(span, spec)
                if hit:
                    key = f"{hit[0]}(근거 대고 뺌)"
                    counts[key] = counts.get(key, 0) + 1
                    continue
                ok = (tree.holds(span, rel) if kind == "경로"
                      else code_holds(span, blob, mods))
                if not ok:
                    bad.append((rel, n, kind, span))
    # 「낱말」이라 안 문 것 중 실은 파일 이름인 것 — 그물의 구멍을 검사가 스스로 센다.
    # **붙임표가 든 것만 센다** — 홑낱말은 모듈 이름이면서 산문의 낱말이기도 해 꼴로 못
    # 가른다(그래서 안 무는 것이 규칙이다). 붙임표가 들면 산문의 낱말일 수 없어, 거기부터가
    # 줄일 수 있는 자리다.
    stemmed = sorted(w for w in samples.get("낱말", ())
                     if "-" in w and w in tree.stems)
    return bad, counts, samples, total, len(code_files), stemmed


# ── §1 자기 이빨 — 손댄 검체로 이 판정이 정말 무는지 **실물보다 먼저** 본다

SEED_DOC = ("# 씨\n\n"
            "경로 하나 `app/server.py` · 식별자 하나 `_seed_mark` 를 든다.\n")
SEED_CODE = 'SEED = 1\n\n\ndef _seed_mark():\n    return SEED\n'


def seed_spec(**over):
    """검체 나무의 선언 — **실물 선언을 안 읽는다.**

    읽으면 받은 저장소마다 이빨의 답이 갈려, 「이 판정이 무나」와 「이 저장소가 성한가」가
    한 판정에 섞인다. 이빨은 어느 저장소에서 돌리든 같은 답이어야 한다.
    """
    base = dict(docs=("docs/**/*.md",), code=("app/**/*",), code_ext=(".py",),
                modules=("app/*.py",), tree_skip={".git": "판이 든다"})
    base.update(over)
    return Spec(**base)


def _plant(doc_extra=""):
    """문서 한 장과 코드 한 장만 세운 임시 나무."""
    root = Path(tempfile.mkdtemp(prefix="doc-span-"))
    (root / "docs").mkdir()
    (root / "docs" / "x.md").write_text(SEED_DOC + doc_extra, encoding="utf-8")
    (root / "app").mkdir()
    (root / "app" / "server.py").write_text(SEED_CODE, encoding="utf-8")
    return root


def positive_control():
    """일부러 어긋난 검체가 정말 빨개지나 — 실물을 대기 전에 선다."""
    print("--- §1 자기 이빨 — 손댄 검체가 정말 빨강을 내나 (양성 대조가 먼저다)")
    tmps = []
    try:
        base = _plant(); tmps.append(base)
        got = survey(base, seed_spec())[0]
        report("㉮ 안 건드린 검체는 초록이다 (양성 대조)", not got,
               [f"실측 {got} — 기대 없음"])

        pbad = _plant("가짜 경로 `app/nowhere.py` 를 든다.\n"); tmps.append(pbad)
        got = [b for b in survey(pbad, seed_spec())[0] if b[2] == "경로"]
        report("㉯ 문서에 가짜 경로를 심으면 빨강이다", bool(got),
               [f"실측 {got} — 기대 경로 어긋남 한 건 이상"])

        ibad = _plant("가짜 식별자 `_seed_ghost` 를 든다.\n"); tmps.append(ibad)
        got = [b for b in survey(ibad, seed_spec())[0] if b[2] == "식별자"]
        report("㉰ 문서에 가짜 식별자를 심으면 빨강이다", bool(got),
               [f"실측 {got} — 기대 식별자 어긋남 한 건 이상"])

        # ㉱ **화면 축이 정말 물리나** — 이 검사가 있는 까닭 자체다. camelCase·DOM id 를
        #    안 물면 좁은 그물로 돌아가도 ㉮㉯㉰ 가 다 초록이라 항진명제가 되살아난다.
        wide = _plant("`paneGo` 와 `#ghostbox` 를 든다.\n"); tmps.append(wide)
        got = {s for _, _, k, s in survey(wide, seed_spec())[0] if k == "식별자"}
        report("㉱ camelCase 와 `#id` 도 그물에 든다 (좁은 그물이면 0건으로 통과한다)",
               got == {"paneGo", "#ghostbox"},
               [f"실측 {sorted(got)} — 기대 ['#ghostbox', 'paneGo']"])

        # ㉲ **가리킴 꼴이 안 풀리면 거짓 빨강이 쏟아진다** — `모듈.이름` 은 코드에 통글자로
        #    안 산다. 못 풀면 우리 문서의 그 꼴 수십 개가 통째로 빨강이 된다.
        dotted = _plant("`server._seed_mark` 를 든다.\n"); tmps.append(dotted)
        got = [b for b in survey(dotted, seed_spec())[0] if b[2] == "식별자"]
        report("㉲ `모듈.이름` 은 그 파일 안에서 풀린다 (통글자로는 코드에 없다)",
               not got, [f"실측 {got} — 기대 없음"])

        # ㉳ **안 무는 꼴이 정말 안 물리나** — 낱말까지 물면 산문이 통째로 빨강이 된다.
        words = _plant("`default` 와 `/api/ghost` 와 `6/7` 을 든다.\n"); tmps.append(words)
        got = survey(words, seed_spec())[0]
        report("㉳ 낱말·절대 길·걸음 표시는 안 문다 (다른 검사가 드는 자리다)", not got,
               [f"실측 {got} — 기대 없음"])

        # ㉴ **선언한 머리가 정말 그물을 가르나** — 이 씨앗이 더한 축이다. 안 물리면 받는
        #    저장소가 제 어휘(`#5` 같은 이슈 번호)에서 거짓 빨강을 보고 판정을 끈다.
        vocab = _plant("`#5` 와 `#ghostbox` 를 든다.\n"); tmps.append(vocab)
        spoken = seed_spec(heads={"#": "이슈 번호다 — 좌표가 아니다"})
        silent = {s for _, _, k, s in survey(vocab, spoken)[0] if k == "식별자"}
        loud = {s for _, _, k, s in survey(vocab, seed_spec())[0] if k == "식별자"}
        report("㉴ 좌표가 아니라고 선언한 머리는 안 문다 (선언 없으면 문다)",
               not silent and loud == {"#5", "#ghostbox"},
               [f"실측 선언 있음 {sorted(silent)} · 선언 없음 {sorted(loud)} — "
                f"기대 [] · ['#5', '#ghostbox']"])

        # ㉵ **윈도우가 사는 저장소는 같은 자리를 눕혀 적는다** — 안 눕히면 그 저장소의
        #    경로 조각이 통째로 거짓 빨강이라, 받자마자 판정을 끄게 된다.
        back = _plant("`app\\server.py` 를 든다.\n"); tmps.append(back)
        got = [b for b in survey(back, seed_spec())[0] if b[2] == "경로"]
        report("㉵ `\\` 로 적은 경로도 나무에서 풀린다", not got,
               [f"실측 {got} — 기대 없음"])

        # ㉶ **선언을 읽는 자도 재이는 것이다** — 읽개가 조용히 빈손을 내면 목록이 통째로
        #    비고, 빈 목록은 「근거 대고 뺀 것이 없다」로 보여 초록으로 읽힌다.
        conf = _plant(); tmps.append(conf)
        (conf / CONF).write_text(
            f"# 주석이다\n[{S_DOC}]\ndocs/**/*.md\n\n[{S_HEAD}]\n"
            f"`#` = 감싼 이름이 선다\n\n[{S_OUTSIDE}]\n밖.md = 까닭이 이어\n  줄로 온다\n",
            encoding="utf-8")
        spec = read_spec(conf / CONF)
        report("㉶ 선언이 그대로 선다 — 감싼 이름 · 이어 줄 까닭 · 주석 건너뜀",
               spec.docs == ("docs/**/*.md",) and set(spec.heads) == {"#"}
               and spec.outside.get("밖.md") == "까닭이 이어 줄로 온다",
               [f"실측 문서 {spec.docs} · 머리 {spec.heads} · 나무 밖 {spec.outside}"])
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)


# ── §2 실물 전수

def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = [a for a in argv[1:] if a.startswith("--")]
    root = Path(args[0]).resolve() if args else HERE.parent
    conf = Path(args[1]).resolve() if "--conf" in flags and len(args) > 1 else root / HERE.name / CONF

    positive_control()
    teeth = len(passes())

    print(f"\n--- §2 실물 전수 — {root}")
    if not conf.is_file():
        raise Unmeasured(
            f"[안 잼] 선언이 없다 — {conf}. 이 검사는 「무엇이 내 문서고 무엇이 내 "
            f"코드인가」를 저장소에서 받는다. **어떻게 주나** — 그 자리에 선언 한 장을 "
            f"세우고 적어도 `[{S_DOC}]` 와 `[{S_CODE}]` 절에 glob 을 적는다(절 이름과 "
            f"꼴은 이 파일 머리말 「선언」이 든다). 다른 자리면 "
            f"`<나무뿌리> --conf <선언>` 로 준다.")

    spec = read_spec(conf)
    docs = docs_of(root, spec)
    if not docs or not spec.code:
        raise Unmeasured(
            f"[안 잼] 재료가 없다 — 문서 {len(docs)}장 · 코드 glob {len(spec.code)}개 "
            f"({conf}). **어떻게 주나** — `[{S_DOC}]` 와 `[{S_CODE}]` 절의 glob 이 이 "
            f"나무({root})에서 실제로 파일에 닿는지 본다. 한쪽이 비면 판정이 안 선다.")

    bad, counts, samples, total, code_files, stemmed = survey(root, spec)
    if not total or not code_files:
        raise Unmeasured(
            f"[안 잼] 조각 {total}개 · 코드 {code_files}장 — 한쪽이 비면 어긋남은 늘 0 이라 "
            f"판정이 안 선다. **어떻게 주나** — 문서에 백틱 조각이 있는지, `[{S_CODE}]` 와 "
            f"`[{S_CODE_EXT}]` 가 서로 맞는 파일을 가리키는지 본다 ({conf}).")

    paths = counts.get("경로", 0)
    idents = counts.get("식별자", 0)
    report(f"경로 조각이 다 실재한다 — 나무에 그 자리가 있다 ({paths}건)",
           not [b for b in bad if b[2] == "경로"],
           [f"{d}:{n} — `{s}`" for d, n, k, s in bad if k == "경로"])
    report(f"식별자 조각이 다 실재한다 — 코드에 그 글자가 있다 ({idents}건)",
           not [b for b in bad if b[2] == "식별자"],
           [f"{d}:{n} — `{s}`" for d, n, k, s in bad if k == "식별자"])

    edge(f"쟀다: 문서 {len(docs)}장의 백틱 조각 {total}개 — 그중 경로 {paths} · "
         f"식별자 {idents}개를 물었다 (코드 나무 {code_files}장)")
    print("  ⚠ 안 문 것 — 꼴별 건수와 견본:")
    for kind in sorted(samples, key=lambda k: -counts[k]):
        seen = sorted(samples[kind])
        show_ = " · ".join(f"`{v}`" for v in seen[:4])
        print(f"       {kind} {counts[kind]}건 ({len(seen)}종) — {show_}"
              + (" …" if len(seen) > 4 else ""))

    # **그 목록에서 가장 먼저 줄일 자리를 검사가 스스로 짚는다** — 「낱말」이라 안 문 것
    # 중에 확장자 뗀 파일 이름과 맞는 것들. 좌표인데 꼴이 낱말과 안 갈려 지금은 못 문다.
    # 세어 두면 다음 사람이 「이만큼이 남았다」를 눈으로 본다.
    edge(f"못 문 좌표 {len(stemmed)}종 — 「낱말」이라 안 물었는데 실은 **확장자를 떼고 "
         f"부르는 파일 이름**이다. 이 목록이 다음에 줄일 자리다: "
         + (" · ".join(f"`{w}`" for w in stemmed[:8]) or "없다")
         + (f" … 외 {len(stemmed) - 8}종" if len(stemmed) > 8 else ""))
    for section, label in TABLES:
        for name, why in sorted(spec.table(section).items()):
            edge(f"근거 대고 뺐다 · {label} — `{name}`: {why}")
    for head, why in sorted(spec.heads.items()):
        edge(f"좌표가 아니라고 선언한 머리 — `{head}`: {why}")
    for name, why in sorted(spec.doc_skip.items()):
        edge(f"안 봤다 · 문서 — `{name}`: {why}")
    for name, why in sorted(spec.tree_skip.items()):
        edge(f"나무에서 뺐다 — `{name}`: {why}")
    edge("안 쟀다 — 그 조각이 **맞는 것을 가리키나**. 글자가 살아 있어도 문서가 틀린 뜻으로 "
         "적었으면 이 검사는 초록이다")
    edge("안 쟀다 — 식별자는 통글자 검색이라 주석·문자열·남의 모듈에서도 걸린다. "
         "「없다」는 확실하고 「있다」는 느슨하다")
    edge("안 쟀다 — 선언의 목록이 **맞는 말인가**. 까닭은 사람이 적은 판단이라 기계가 "
         "읽기만 하고 재지는 않는다")

    print()
    if fails():
        print(f"❌ {len(fails())}건 어긋남 — {' · '.join(fails())}", file=sys.stderr)
        return EXIT_MISMATCH
    print(f"✅ 문서의 백틱 좌표가 실물을 가리킨다 — 판정 {len(passes())}건 "
          f"(자기 이빨 {teeth}건 · 문서 {len(docs)}장의 조각 {total}개 중 "
          f"{paths + idents}개를 물었다)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
