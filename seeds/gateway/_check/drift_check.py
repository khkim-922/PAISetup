"""씨앗과 앱이 얼마나 갈렸나 — 같은 이름의 함수·상수를 곁말 걷고 견준다. 게이트가 아니라 재는 자다.

    python -X utf8 _check/drift_check.py <앱 나무>            # 그 앱의 app/ 과 이 씨앗을 견준다

내는 것 — 이름마다 한 줄(같음 · 갈림(닮은 정도) · 없음(앱))과 합계. 종료 0 견줬다(판정은 안 낸다) ·
2 못 쟀다(인자가 하나가 아니다 — 이 도움말을 찍는다 · 앱 나무에 app/ 이 없다).
견주는 짝은 씨앗 `app/gateway.py` ↔ 앱 `app/gateway.py`+`app/config.py`, 씨앗 `app/providers.py` ↔ 앱
`app/providers.py` 다. 맨 윗자리의 함수와 대문자 상수만 세고, 함수는 머리 독스트링을 걷고 견준다.

왜 있나 — 씨앗은 복사해 출발하는 밑판이라 앱은 갈려도 된다. 다만 **왜 갈렸나를 모른 채**
갈리는 것이 문제다. 이 자는 갈린 자리를 이름으로 세워 사람이 판정할 목록을 준다:
같음(코드가 같다) · 갈림(코드가 다르다 — 왜인지 그 자리의 곁말이 들어야 한다) · 없음(씨앗에만
있다 · 앱에만 있는 이름은 수만 센다). 판정은 안 낸다 — 갈림이 곧 결함이 아니고, 같음이 곧 맞음도 아니다.

이름으로 세우므로 한쪽에만 이름이 있는 값과 손글자는 안 잡힌다 — 그 자리는 절을 통째로
읽는 수밖에 없다(claude-config 스킬 `borrow-spec-as-pair` 「낱말이 아니라 자리로 읽는다」).
"""
import ast
import difflib
import io
import sys
from pathlib import Path

from _verdict import EXIT_UNMEASURED

SEED = Path(__file__).resolve().parent.parent / "app"
# 앱 쪽 짝 — 갈래 표·자격은 `gateway.py` 나 `config.py` 에 산다(앱마다 이름이 갈린다)
PAIRS = [("gateway.py", ("gateway.py", "config.py")), ("providers.py", ("providers.py",))]


def defs(path):
    """원문 한 장의 맨 윗자리 이름들 — ({함수: (줄, 원문)}, {대문자 상수: (줄, 값 원문)}).

    함수는 머리 독스트링을 걷고 `ast.unparse` 로 다시 쓴 원문이라 주석 · 띄어쓰기는 견주기에 안 든다.
    클래스 · async 함수 · 주석 단 대입(`X: int = …`)은 안 센다.
    """
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    fns, consts = {}, {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            body = list(node.body)
            if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body = body[1:] or [ast.Pass()]
            node.body = body
            fns[node.name] = (node.lineno, ast.unparse(node))
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id.isupper():
            consts[node.targets[0].id] = (node.lineno, ast.unparse(node.value))
    return fns, consts


def compare(kind, ours, theirs, seed_file, app_file):
    """두 이름표를 맞대 (이름, 갈래, 씨앗 자리, 앱 자리) 줄들을 이름 차례로 낸다 — 갈림은 줄 단위 닮은 정도를 단다."""
    rows = []
    for name in sorted(set(ours) | set(theirs)):
        if name not in theirs:
            rows.append((name, "없음(앱)", f"{seed_file}:{ours[name][0]}", "-"))
        elif name not in ours:
            rows.append((name, "없음(씨앗)", "-", f"{app_file}:{theirs[name][0]}"))
        elif ours[name][1] == theirs[name][1]:
            rows.append((name, "같음", f"{seed_file}:{ours[name][0]}", f"{app_file}:{theirs[name][0]}"))
        else:
            r = difflib.SequenceMatcher(None, ours[name][1].splitlines(),
                                        theirs[name][1].splitlines()).ratio()
            rows.append((name, f"갈림({r:.2f})", f"{seed_file}:{ours[name][0]}",
                         f"{app_file}:{theirs[name][0]}"))
    return rows


def main(app_root):
    """짝마다 견준 줄과 합계를 찍고 종료 값을 낸다 — 0, 또는 `app/` 이 없으면 2."""
    app = Path(app_root).resolve() / "app"
    if not app.is_dir():
        print(f"앱 나무에 app/ 이 없다: {app}", file=sys.stderr)
        return EXIT_UNMEASURED
    total = {"같음": 0, "갈림": 0, "없음": 0}
    for seed_name, candidates in PAIRS:
        seed_fns, seed_consts = defs(SEED / seed_name)
        app_fns, app_consts = {}, {}
        used = []
        for cand in candidates:
            if (app / cand).exists():
                f, c = defs(app / cand)
                app_fns.update(f)
                app_consts.update(c)
                used.append(cand)
        label = "+".join(used) or "(없음)"
        print(f"\n== 씨앗 app/{seed_name} ↔ 앱 app/{label}")
        for kind, ours, theirs in (("함수", seed_fns, app_fns), ("상수", seed_consts, app_consts)):
            rows = compare(kind, ours, theirs, f"app/{seed_name}", f"app/{label}")
            # 씨앗에 없는 것은 앱 고유라 목록만 세고 줄은 안 찍는다 — 앱이 크면 소음이다
            own = [r for r in rows if r[1] == "없음(씨앗)"]
            for name, verdict, at_seed, at_app in rows:
                if verdict == "없음(씨앗)":
                    continue
                key = verdict.split("(")[0]
                total[key] += 1
                print(f"  {verdict:10s} {kind} {name:26s} {at_seed:22s} {at_app}")
            print(f"  (앱에만 있는 {kind} {len(own)}개는 세지 않았다 — 앱 고유다)")
    print(f"\n같음 {total['같음']} · 갈림 {total['갈림']} · 씨앗에만 있음 {total['없음']}")
    print("판정은 여기서 안 낸다 — 갈림마다 그 자리 곁말이 「왜」를 들어야 한다.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(EXIT_UNMEASURED)
    sys.exit(main(sys.argv[1]))
