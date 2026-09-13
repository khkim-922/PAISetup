"""무는 자 — 검사 파일이 배관 모듈의 어느 속성을 코드로 무는지 AST 로 센다.

정규식이 아니라 AST 라서 주석·독스트링·산문은 안 걸린다.
문자열 안에 든 하위 프로그램(subprocess -c 로 넘기는 판)도 다시 파싱해 따라 들어간다.

  python _plumb_names.py <트리> <검사파일...>       # 검사파일 경로는 트리 기준 상대

⚠ **`app` 을 직접 무는 자리만 센다.** 선언으로 바꾼 트리의 검사는 `_plumb` 를 물으므로
여기서 0 이 나오는 것이 정상이다 — 이 자를 가리킬 자리는 **아직 안 바꾼 형제**다(그 저장소가
제 `gateway.conf` 에 무엇을 적어야 하나를 이 수가 답한다). 0 이 두 뜻을 지므로 밑에서 갈라 적는다.
"""
import ast
import sys
from pathlib import Path


def harvest(src, path, out, depth=0):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "app":
            for a in node.names:
                aliases[a.asname or a.name] = f"{node.module}.{a.name}"
    def note(alias, attr, node, how=""):
        out.setdefault(aliases[alias], {}).setdefault(attr, []).append(
            path + ":" + str(node.lineno) + how + ("  (안긴 판)" if depth else ""))

    for node in ast.walk(tree):
        # 점으로 무는 자 — gateway.CLI_EXE
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
           and node.value.id in aliases:
            note(node.value.id, node.attr, node)
        # 이름을 문자열로 무는 자 — getattr(gateway, "_ssl_why", None)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("getattr", "hasattr", "setattr", "delattr") \
                and len(node.args) >= 2 and isinstance(node.args[0], ast.Name) \
                and node.args[0].id in aliases \
                and isinstance(node.args[1], ast.Constant) \
                and isinstance(node.args[1].value, str):
            note(node.args[0].id, node.args[1].value, node, "  (" + node.func.id + ")")
    if depth == 0:
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
               and "from app import" in node.value:
                harvest(node.value, path + ":" + str(node.lineno) + "<문자열>", out, depth + 1)


def main():
    root = Path(sys.argv[1]).resolve()
    out = {}
    for rel in sys.argv[2:]:
        p = root / rel
        if not p.exists():
            print("  ! 없다: " + rel)
            continue
        harvest(p.read_text(encoding="utf-8"), rel, out)
    total = 0
    for mod in sorted(out):
        print("\n[" + mod + "]  속성 " + str(len(out[mod])))
        total += len(out[mod])
        for attr in sorted(out[mod]):
            sites = out[mod][attr]
            print("  %-22s %2d회  %s" % (attr, len(sites), " · ".join(sites)))
    print("\n== 모듈 " + str(len(out)) + " · 속성 이름 합 " + str(total))
    if not total:
        print("   ⚠ 직접 무는 자리 0 — 두 뜻이다. 선언(`_plumb`)으로 바꾼 트리면 **정상**이고,")
        print("     아직 `from app import …` 로 무는 형제를 가리켰는데 0 이면 **못 잰 것**이다.")
        print("     가린 자리부터 보라: 건넨 경로가 트리 기준 상대인가 · 그 파일이 정말 그 트리에 있나")


main()
