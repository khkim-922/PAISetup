"""산출물 HTML 의 인라인 스크립트가 문법에 맞나 — 깨진 것을 잡고 못 재면 못 쟀다고 한다.

좌표 — 아뜰리에 #335 ㉯ 에서 받아 익명화했다. 씨앗 규율은 claude-config 결정 0040.

    python -X utf8 _check/script_syntax_check.py               # 자검만 — 검체는 이 파일이 든다
    python -X utf8 _check/script_syntax_check.py <판.html> …   # 그 산출물까지 잰다

**왜 이 검사가 있나.** 글자 유실을 세는 무결 대조는 `<script>` 가 깨져도 조용하다 — 난 자리의
실측(2026-09-05): 이어쓰기 이음매의 코드 펜스가 JS 템플릿 리터럴 안에 박혀 판이 통째로 죽었는데
저장에도 화면에도 아무것도 안 찍혔다(「유실 20」은 전부 이모지 치환이었다). **글자는 다 있는데
판이 안 도는** 자리라, 글자를 세는 눈으로는 영영 안 보인다. 막는 자가 아니라 말하는 자다.

**판정 함수를 제 안에 들었다 — 앱에서 인자로 안 받는다.** 난 자리는 앱의 함수를 불렀고 그
결합을 인자로 바꾸는 길도 있었다. 안 그런 까닭 셋 —

  · **자검이 선다.** 받는 꼴이면 아래 양성 대조가 *앱의* 함수를 재는데, 갓 복사한 저장소에는
    그 함수가 없어 이 자는 첫날부터 「못 쟀다」만 낸다. **양성 대조가 못 서는 씨앗은 씨앗이
    아니다** — 무는 이빨을 한 번도 안 보이고 초록만 내는 자가 된다
  · **결합이 한 줄이 아니었다.** 난 자리의 임포트 한 줄이 앱 꾸러미의 머리와 설정 모듈을 함께
    들여, 앱이 켜질 때 하는 일(TLS 주입)과 바깥 의존성 하나를 이 검사에 얹었다 — 실측: 그
    꾸러미가 안 깔린 파이썬에서는 검사가 아예 안 섰다. 「node 하나만 부른다」가 거기서 깨진다
  · **재는 것이 다르다.** 앱의 함수는 *저장할 때 값을 찍는* 자이고 이 자는 *나온 판을 무는*
    게이트다 — 부르는 자리도 계약도 달라, 같은 일을 둘이 드는 것이 손사본이 아니다

값은 치른다 — **앱이 제 판정 함수를 이미 들었으면 문법을 재는 손이 그 저장소에 둘이 된다.**
그 자리는 앱의 함수를 무는 검사를 저장소가 따로 세워 가른다. 그 검사는 앱의 계약이라 씨앗이
안 든다 — 여기는 *판이 성한가*만 묻고 *앱이 그것을 옳게 찍나*는 안 묻는다.

판정 — 일곱이 참이어야 한다:
  ① 성한 인라인 스크립트는 오류 0 · 잰 수 1
  ② 템플릿 리터럴 안에 펜스가 박힌 판은 오류 1 이고 사유가 node 의 말이다 (① 의 짝)
  ③ 자료 스크립트는 안 잰다 — 잰 수 0 · 건너뜀 1
  ④ `type="module"` 의 `import` 는 ESM 으로 잰다 — 오류 0 (`.js` 로 재면 늘 빨강이다)
  ⑤ `src` 가 달린 바깥 스크립트는 안 잰다 — 몸통이 이 저장소가 낸 것이 아니다
  ⑥ 스크립트가 없는 판은 node 를 **안 부른다** — 부르는 자리를 세어 그것까지 본다
  ⑦ node 를 못 찾으면 「못 쟀다」가 서고 오류 목록은 빈다 — 초록이 아니라 회색이다

⚠ **양성 대조가 실물보다 먼저 선다.** ② 가 실제로 빨개지는 것을 보인 다음에야 실물 판정이 뜻을
  갖는다 — ② 가 죽으면 실물이 몇 장이든 「오류 0」 초록이 난다.

⚠ **인자를 안 주면 실물은 안 잰 것이다.** 자검만 돌고 초록이 나는데, 그 초록은 *이 검사가 성하다*
  는 말이지 *이 저장소의 판이 성하다*는 말이 아니다. 그 갈림은 마지막 경계 줄이 든다.

**안 재는 것** — 스크립트가 *무슨 일을 하나*(문법만 본다) · 속성에 박힌 `on…` 처리기와 바깥
`.js` 파일(`<script>` 몸통만 뗀다) · 브라우저에서 실제로 도나(`node --check` 는 파싱까지다 —
없는 이름을 불러도 초록이다) · 판을 내는 자리가 이 값을 응답·장부에 싣나(그 저장소의 계약이라
여기가 아니다) · 화면이 이 값을 어떻게 말하나 · HTML 이 성한가(스크립트만 본다).

바깥으로 안 나간다 — node 하나만 부른다. 토큰도 망도 브라우저도 안 쓴다.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report

# 안 재는 종류 — JS 가 아니라 node 가 늘 빨강이다. 그 밖의 `type`(빈 것 · `text/javascript` ·
# `module` · 저장소가 제 손으로 지은 이름)은 **잰다.** 난 자리에서 실제로 깨진 스크립트가 바로
# 그 손수 지은 종류였다 — 「아는 종류만 잰다」로 뒤집으면 그 사고가 그대로 다시 빠져나간다.
SCRIPT_TYPES_NOT_JS = {
    "application/json", "application/ld+json", "importmap", "speculationrules",
    "text/html", "text/template", "text/x-template", "text/x-handlebars-template",
    "text/babel", "text/jsx", "text/typescript", "application/typescript",
}
NODE_CHECK_TIMEOUT_S = 20
# `shutil.which` 가 빈손일 때 마지막으로 두드리는 자리 — 윈도우 기본 설치 자리. 도구를 띄운
# 셸의 PATH 에 node 가 없는 PC 가 실재한다(난 자리의 커밋 훅이 거기서 넘어졌다).
NODE_FALLBACKS = (r"C:\Program Files\nodejs\node.exe",)
# node 의 말에서 싣는 글자 수 — 스택 전체가 실리면 판정 줄이 덮여 무엇이 깨졌는지가 안 보인다.
SAID_MAX = 200
_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
_ATTR_RE = re.compile(r"""([a-zA-Z-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?""")


def _script_attrs(head):
    """`<script …>` 머리의 속성 — 이름은 소문자, 값은 따옴표를 벗긴 글자."""
    out = {}
    for m in _ATTR_RE.finditer(head):
        out[m.group(1).lower()] = m.group(2) or m.group(3) or m.group(4) or ""
    return out


def node_exe():
    """문법을 재 줄 node — 없으면 None."""
    found = shutil.which("node")
    if found:
        return found
    for p in NODE_FALLBACKS:
        if os.path.isfile(p):
            return p
    return None


def script_syntax(html_text, find_node=node_exe):
    """인라인 `<script>` 의 문법 — `{"checked", "skipped", "errors", "unmeasured"}`.

    `errors` 한 줄은 `{"n": 몇 번째 스크립트인가, "type": 종류, "error": node 가 한 말}`.
    `unmeasured` 가 비지 않으면 그 판은 **안 잰 것**이다 — 오류 0 과 갈라 읽어야 한다.

    `find_node` 는 판정 ⑥·⑦ 이 무는 자리다 — node 를 **언제 찾나**가 곧 계약이라(스크립트가
    없으면 안 찾는다 · 못 찾으면 회색이다), 찾는 손을 밖에서 주면 그 둘을 재현으로 잰다.
    """
    checked, skipped, errors, todo = 0, 0, [], []
    for i, m in enumerate(_SCRIPT_RE.finditer(html_text or ""), start=1):
        attrs, body = _script_attrs(m.group(1)), m.group(2)
        kind = (attrs.get("type") or "").strip().lower()
        if "src" in attrs or kind in SCRIPT_TYPES_NOT_JS or not body.strip():
            skipped += 1
            continue
        todo.append((i, kind, body))
    if not todo:
        return {"checked": 0, "skipped": skipped, "errors": [], "unmeasured": ""}
    node = find_node()
    if not node:
        return {"checked": 0, "skipped": skipped, "errors": [],
                "unmeasured": f"node 를 못 찾아 스크립트 {len(todo)}개의 문법을 못 쟀다"}
    for i, kind, body in todo:
        # module 은 ESM 으로 — `.js` 로 재면 `import` 가 늘 빨강이다
        fd, path = tempfile.mkstemp(suffix=".mjs" if kind == "module" else ".js",
                                    prefix="script-syntax-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(body)
            try:
                r = subprocess.run([node, "--check", path], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace",
                                   timeout=NODE_CHECK_TIMEOUT_S)
            except (OSError, subprocess.TimeoutExpired) as exc:
                return {"checked": checked, "skipped": skipped, "errors": errors,
                        "unmeasured": f"node --check 가 안 돌았다 — {type(exc).__name__}"}
            checked += 1
            if r.returncode != 0:
                lines = [ln for ln in (r.stderr or "").splitlines() if ln.strip()]
                said = next((ln for ln in reversed(lines) if "Error" in ln),
                            lines[-1] if lines else "")
                errors.append({"n": i, "type": kind or "text/javascript",
                               "error": said.strip()[:SAID_MAX]})
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
    return {"checked": checked, "skipped": skipped, "errors": errors, "unmeasured": ""}


# ── 검체 — 이 파일이 든다. 저장소의 산출물이 없어도 자검이 선다 ────────────────────

NL = chr(10)
FENCE = "```"
OK_JS = "<html><body><script>const a = `x ${1 + 1}`; console.log(a);</script></body></html>"
# ② 의 검체 — 템플릿 리터럴 `${` 뒤에 펜스 한 줄이 끼었다. 난 자리의 실물 그대로의 꼴이고,
#   종류도 그때처럼 저장소가 제 손으로 지은 이름이다(그 종류를 안 재면 이 사고가 샌다).
BROKEN_JS = ("<html><body><script type=\"text/x-own\">const t = `물음: ${" + FENCE + NL
             + "picks[0].text}`;</script></body></html>")
DATA = "<html><body><script type=\"application/json\">{\"a\": [1, 2]}</script></body></html>"
MODULE = ("<html><body><script type=\"module\">import x from './x.js'; console.log(x);"
          "</script></body></html>")
EXTERNAL = "<html><head><script src=\"./support.js\"></script></head><body>x</body></html>"
NONE = "<html><body><p>글만 있는 판</p></body></html>"


class Spy:
    """node 를 찾는 손의 대역 — **몇 번 찾았나**를 세고, 빈손으로도 설 수 있다.

    ⑥ 이 「안 부른다」를 재려면 결과만 봐서는 모자란다. 스크립트가 없으면 잰 수는 어차피 0 이라,
    node 를 부르고 버려도 같은 값이 난다 — 부르는 자리를 세어야 「안 불렀다」가 판정이 된다.
    """

    def __init__(self, found):
        self.found, self.asked = found, 0

    def __call__(self):
        self.asked += 1
        return self.found


# ── §1 양성 대조 — 깨진 것을 정말 무나. 그 짝으로 성한 것은 안 무나 ────────────────

def positive_control():
    print("--- §1 양성 대조 — 일부러 깨뜨린 검체가 정말 빨개지나 (그 짝으로 성한 것은 조용한가)")
    r = script_syntax(BROKEN_JS)
    report("② 템플릿 리터럴 안의 펜스 — 오류 1 · 사유가 node 의 말이다",
           r["checked"] == 1 and len(r["errors"]) == 1
           and "SyntaxError" in r["errors"][0]["error"]
           and r["errors"][0]["type"] == "text/x-own", [repr(r)])
    r = script_syntax(OK_JS)
    report("① 성한 스크립트 — 오류 0 · 잰 수 1 (② 의 짝)",
           r["checked"] == 1 and not r["errors"] and not r["unmeasured"], [repr(r)])


# ── §2 갈래 — 무엇을 재고 무엇을 비켜 세우나 ──────────────────────────────────────

def kinds():
    print(NL + "--- §2 갈래 — 재는 종류와 비켜 세우는 종류가 갈리나")
    r = script_syntax(DATA)
    report("③ 자료 스크립트 — 안 잰다 (잰 수 0 · 건너뜀 1)",
           r["checked"] == 0 and r["skipped"] == 1 and not r["errors"], [repr(r)])
    r = script_syntax(MODULE)
    report("④ module 의 import — ESM 으로 재서 오류 0",
           r["checked"] == 1 and not r["errors"], [repr(r)])
    r = script_syntax(EXTERNAL)
    report("⑤ 바깥 스크립트(src) — 안 잰다 (잰 수 0 · 건너뜀 1)",
           r["checked"] == 0 and r["skipped"] == 1, [repr(r)])
    spy = Spy("(안 불려야 한다)")
    r = script_syntax(NONE, find_node=spy)
    report("⑥ 스크립트 없는 판 — node 를 안 부른다 (찾은 횟수 0 · 잰 수 0 · 못 잼 없음)",
           spy.asked == 0 and r["checked"] == 0 and not r["errors"] and not r["unmeasured"],
           [f"찾은 횟수 {spy.asked} · {r!r}"])


# ── §3 못 잼 갈래 — 없는 것을 초록으로 안 내나 ────────────────────────────────────

def grey():
    print(NL + "--- §3 못 잼 갈래 — node 가 없는 판을 초록으로 안 내나")
    spy = Spy(None)
    r = script_syntax(OK_JS, find_node=spy)
    report("⑦ node 없음 — 「못 쟀다」가 서고 오류 목록은 빈다 (초록이 아니라 회색이다)",
           spy.asked == 1 and bool(r["unmeasured"]) and not r["errors"] and r["checked"] == 0,
           [f"찾은 횟수 {spy.asked} · {r!r}"])


# ── §4 실물 — 인자로 받은 판. 안 주면 안 잰 것이다 ────────────────────────────────

def survey(paths):
    """실물 판정 — 읽은 장수와 못 읽은 자리를 함께 돌려준다."""
    seen, unreadable = 0, []
    for raw in paths:
        p = Path(raw)
        try:
            text = p.read_text(encoding="utf-8-sig")
        except OSError as exc:
            unreadable.append(f"{p} — {type(exc).__name__}: {exc}")
            continue
        seen += 1
        r = script_syntax(text)
        report(f"실물 {p.name} — 인라인 스크립트 문법 오류 0",
               not r["errors"] and not r["unmeasured"], [repr(r)])
        edge(f"실물 {p.name} — 잰 스크립트 {r['checked']}개 · 비켜 세운 것 {r['skipped']}개")
    return seen, unreadable


def main(argv):
    node = node_exe()
    print(f"--- node: {node or '(없음)'}")
    if not node:
        raise Unmeasured(
            "[안 잼] node 를 못 찾아 문법을 잴 자가 없다 — 이 판은 초록도 빨강도 아니다."
            f"{NL}어떻게 주나 — PATH 에 node 를 올리거나, 이 파일의 `NODE_FALLBACKS` 에"
            " 이 PC 의 설치 자리를 더한다.")

    positive_control()
    kinds()
    grey()

    print(NL + "--- §4 실물 — 인자로 받은 판")
    seen, unreadable = survey(argv[1:])
    if argv[1:] and not seen:
        raise Unmeasured(
            "[안 잼] 인자를 받았는데 한 장도 못 읽었다 — 실물 판정이 한 건도 안 섰다."
            f"{NL}어떻게 주나 — 읽을 수 있는 HTML 의 경로를 준다: "
            "`python -X utf8 _check/script_syntax_check.py <판.html> …`")
    for row in unreadable:
        edge(f"**못 읽은 판** — {row}")

    print(NL + "--- 안 잰 것")
    if not seen:
        edge("**실물을 한 장도 안 쟀다** — 인자를 안 줬다. 이 초록은 *이 검사가 성하다*는 말이지 "
             "*이 저장소의 판이 성하다*는 말이 아니다. 판을 내는 자리가 제 산출물을 인자로 준다")
    edge("스크립트가 **무슨 일을 하나** — 문법만 본다. 무엇을 하는 코드인가는 사람이 읽는다")
    edge("**브라우저에서 실제로 도나** — `node --check` 는 파싱까지다. 없는 이름을 불러도 초록이다")
    edge("속성에 박힌 `on…` 처리기와 바깥 `.js` 파일 — `<script>` 몸통만 뗀다")
    edge("판을 내는 자리가 이 값을 응답·장부에 싣나 — 그 저장소의 계약이라 여기가 아니다")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        return EXIT_MISMATCH
    print(f"전부 통과 (판정 {len(passes())}건 — 검체 일곱 · 실물 {seen}장)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
