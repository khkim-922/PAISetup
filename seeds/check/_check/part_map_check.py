"""부품 지도 문서의 표가 부품 폴더 실물과 맞나 — 양쪽 차집합.

좌표 — 이 자가 난 자리는 아뜰리에 `_check/part_map_check.py`(아뜰리에 #322 「안 하기로 한 것」이
간선을 뺀 자리를 적어 둔다) · 자기 이빨 규율은 아뜰리에 결정 0112 · 씨앗 규율은 claude-config
결정 0040.

    python -X utf8 _check/part_map_check.py <지도 문서> <부품 폴더> <절 제목>
    python -X utf8 _check/part_map_check.py    # 곁 `part_map.conf` 의 [part_map] doc·app·section 을 적은 저장소

**왜 이 검사가 있나.** 부품 지도는 *어느 파일이 있고 그것이 무엇을 드나*를 든다. 그런데
부품 폴더에 파일이 나거나 사라져도 **아무 데서도 안 터진다** — 앱은 그대로 돌고 표만 조용히
낡는다. 비싼 쪽은 「없는 부품을 있다고 말하는」 줄이다: 그것을 읽은 사람은 **고칠 자리를
없는 파일에서 찾는다.** 반대쪽도 싸지 않다 — 새 파일에 줄이 없으면 그 파일은 *부품이
아닌 것*처럼 읽혀, 배관을 고칠 때 통째로 빠진다.

`map_check.py` 가 `_check/` 에 하는 일을 앱 폴더에 하는 것이고, 재는 것도 같은
**차집합 둘**이다:
  ① **표에 없는 부품** — 파일은 사는데 지도에 줄이 없다. 새로 짓고 안 적었거나
     이름을 바꾸고 한쪽만 고친 자리
  ② **실물 없는 줄** — 지도에 줄은 있는데 파일이 없다. 지우거나 옮긴 자리

**표를 절로 앵커한다** — 준 절 이름의 절 안에 사는 표 줄만 센다. 지도 문서에는 대개 표가
둘 이상이고 문서가 자라면 더 는다. 아무 표나 물면 남의 줄이 부품으로 서서 ②가 거짓 빨강이
된다. 절 제목이 바뀌면 표 줄이 0 이 되는데, 그때는 초록이 아니라 **「못 쟀다」(2)로** 나간다.

**일부러 안 재는 것** — 판정에 새겨 둔다:
  · **도해의 간선**(누가 누구를 부르나)은 안 문다. 집합이 아니라 배선 그래프라 파일
    목록에서 안 나온다 — 이 자가 난 저장소가 「안 하기로 한 것」에 이름으로 적어 둔 자리다
  · **줄이 *맞는 말을 하나*** 는 못 잰다. 「무엇을 든다」 따위 곁칸은 사람이 실물을 읽고
    적은 판단이라 기계가 대신 못 한다
  · **표 밖 산문**이 든 셈과 이름(문단이 「파일 몇 개」라 적은 수 따위)은 안 본다.
    표 줄이 아니라 문장이라 집합으로 안 뜬다
  · **파생물**(`__pycache__/`)과 점으로 시작하는 숨은 자리는 소스가 아니라 뺀다.
    뺀 것은 **이름과 까닭을 달아 판정 옆에 찍는다** — 그냥 눈감으면 다음 사람이 못 되짚는다

⚠ **그물이 접두사·확장자 목록이 아니다.** 부품 폴더 아래 사는 파일은 **전부** 제 줄이 있어야
  한다 — 확장자 흰 목록을 두면 새 꼴(`.mjs`·글꼴·그림)이 날 때 **아무 말 없이 대조 밖으로
  빠진다.** 부품이 아닌 것이 나면 아래 `SKIP` 에 까닭을 달아 빼고, 그 사실이 판정에 남는다.

⚠ **어긋남 0 은 그 자체로 초록이 아니다.** 표를 못 읽어도 0 이 나온다. 그래서 아래 §2 가
  **손댄 사본 여섯으로 이 판정이 실제로 무는지**를 같은 판에서 보이고, 한쪽이 빈손이면
  초록이 아니라 「못 쟀다」(2)로 나간다.

토큰도 네트워크도 브라우저도 안 쓴다.
"""
import configparser
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report  # noqa: E402

# **이 셋이 이 검사가 저장소에 매이는 전부다** — 지도 문서 · 부품 폴더 · 표가 사는 절 제목.
# **씨앗은 비워서 낸다** — 이 파일을 받은 저장소가 제 자리를 여기 적거나 부를 때 인자로
# 준다(여기 적은 줄이 곧 이 파일이 씨앗과 갈리는 사유다). 셋 중 하나라도 비면 차집합이
# 설 재료가 없으므로 판정이 아니라 **「못 쟀다」(2)로** 나간다.
DOC = ""            # 부품 지도 문서의 자리 — 부를 때 첫 인자가 덮는다
APP = ""            # 부품이 사는 폴더 — 그 아래 **전부**가 제 줄을 지녀야 한다
SECTION = ""        # 표가 사는 절의 제목 — 제목이 곧 앵커다

# 이름꼴 — 표 칸과 파일 목록에 **같은 자**를 댄다. 산문 칸(빈칸·괄호·한글)은 여기서 걸린다.
PATHNAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]+$")

# 실물이되 **부품이 아닌** 자리 — 이름과 까닭을 함께 둔다. 까닭이 없으면 그냥 눈감은
# 것이고, 눈감은 자리는 다음 사람이 못 되짚는다.
SKIP = {
    "__pycache__": "파이썬이 구운 파생물 — 소스가 아니고 `.gitignore` 도 뺀다",
}
DOTTED = "점으로 시작하는 숨은 자리 — 부품이 아니다"


# ── 실물 쪽 — 부품 폴더 아래를 통째로 훑는다

def _skip_why(rel):
    """이 파일을 부품 목록에서 뺄 까닭 — 없으면 None(=센다)."""
    for part in rel.split("/"):
        if part in SKIP:
            return SKIP[part]
        if part.startswith("."):
            return DOTTED
    return None


def scan_files(app_dir):
    """부품 폴더에 실제로 사는 부품 — (센 것, 까닭 대고 뺀 것).

    이름은 표와 **같은 꼴**(`static/app.css`)로 낸다 — 폴더를 벗기면 `app.css` 와
    `static/app.css` 가 남남이 되어 하위 폴더의 줄이 통째로 어긋남으로 뜬다.
    """
    kept, skipped = set(), []
    for path in sorted(Path(app_dir).rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(app_dir).as_posix()
        why = _skip_why(rel)
        if why:
            skipped.append(f"{rel} — {why}")
        else:
            kept.add(rel)
    return kept, skipped


# ── 문서 쪽 — 그 절의 표 첫 칸만 본다

def _bounds(lines, section):
    """표가 사는 절의 줄 범위 [시작, 끝) — 제목을 못 찾으면 빈 범위."""
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and section in line:
            start = i + 1
            break
    if start is None:
        return 0, 0
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            return start, i
    return start, len(lines)


def _row_head(line):
    """표 한 줄의 첫 칸이 부품 이름이면 그 이름, 아니면 None."""
    s = line.strip()
    if not s.startswith("|"):
        return None
    cells = s.split("|")
    if len(cells) < 2:
        return None
    name = cells[1].strip().strip("`").strip()
    return name if PATHNAME.match(name) else None


def scan_doc(text, section):
    """지도의 표 줄이 든 부품 이름 — **그 절 안에서 · 첫 칸만.**

    본문이 곁말로 다른 파일을 가리키는 자리가 많아, 「어디든 이름이 있나」로 재면
    ①(표에 없는 부품)이 통째로 눈이 먼다. 제 줄에 앉은 것만 센다.
    """
    lines = text.splitlines()
    lo, hi = _bounds(lines, section)
    return {n for n in (_row_head(line) for line in lines[lo:hi]) if n}


def compare(files, rows):
    """(표에 없는 부품, 실물 없는 줄)."""
    return sorted(files - rows), sorted(rows - files)


# ── 자기 이빨 — 손댄 사본으로 이 판정이 정말 무는지 본다

# 임시 나무 안의 자리 — 실물 자리와 **일부러 다른 이름**이다. 받은 저장소의 `DOC`·`APP` 이
# 무엇이든 사본은 같은 모양으로 서야, 읽개(절 앵커 · 표 읽기 · 하위 폴더 훑기)가 자리
# 이름과 무관하게 물리는지를 잰다.
TMP_DOC = "map.md"
TMP_APP = "parts"


def _plant(names, doc_text):
    """부품 이름만 빈 파일로 세운 임시 나무 — 문서는 준 글자 그대로."""
    root = Path(tempfile.mkdtemp(prefix="part-map-"))
    (root / TMP_DOC).write_text(doc_text, encoding="utf-8")
    (root / TMP_APP).mkdir()
    for name in names:
        path = root / TMP_APP / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    return root


def _drop_row(text, section):
    """절 안의 첫 부품 줄 하나를 지운 문서 — (지운 문서, 지운 이름)."""
    lines = text.splitlines(keepends=True)
    lo, hi = _bounds(lines, section)
    for i in range(lo, hi):
        name = _row_head(lines[i])
        if name:
            return "".join(lines[:i] + lines[i + 1:]), name
    return text, None


def _survey(root, section):
    files, _ = scan_files(root / TMP_APP)
    return compare(files, scan_doc((root / TMP_DOC).read_text(encoding="utf-8"), section))


def _settings(argv):
    """(지도 문서, 부품 폴더, 절 제목) — 인자가 덮고, 없으면 상수가 든다.

    셋은 **한 벌**이라 일부만 받지 않는다. 하나만 받으면 나머지가 상수에서 오는데,
    상수가 빈 씨앗에서는 「절반만 준 자리」가 「아무것도 안 준 자리」와 같은 말을 해
    무엇이 빠졌는지 사람이 못 되짚는다.
    """
    args = argv[1:]
    if args and len(args) != 3:
        raise Unmeasured(
            f"[안 잼] 인자를 {len(args)}개 줬다 — 지도 문서 · 부품 폴더 · 절 제목 셋이 한 벌이다. "
            "어떻게 주나: `python -X utf8 _check/part_map_check.py <지도 문서> <부품 폴더> <절 제목>`")
    doc, app, section = args if args else _conf()
    if not (doc and app and section):
        missing = " · ".join(n for n, v in
                             (("지도 문서", doc), ("부품 폴더", app), ("절 제목", section)) if not v)
        raise Unmeasured(
            f"[안 잼] 잴 자리를 안 줬다 — 빈 것: {missing}. 씨앗은 이 셋을 비워서 낸다. "
            "어떻게 주나: `python -X utf8 _check/part_map_check.py <지도 문서> <부품 폴더> <절 제목>` "
            f"으로 주거나, 곁 `{CONF}` 의 `[part_map]` 절에 doc · app · section 을 적는다"
            "(나무뿌리 기준 경로 · 이 파일은 안 고친다 — 사본은 진본과 글자가 같아야 한다)")
    return Path(doc).resolve(), Path(app).resolve(), section


CONF = "part_map.conf"


def _conf():
    """곁 선언 `[part_map]` 의 doc · app · section — 없으면 상수 셋(씨앗은 빈 값). 경로는 나무뿌리 기준."""
    conf = HERE / CONF
    if not conf.is_file():
        return DOC, APP, SECTION
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(conf, encoding="utf-8")
    sec = cp["part_map"] if cp.has_section("part_map") else {}
    root = HERE.parent
    doc, app = sec.get("doc", DOC), sec.get("app", APP)
    return (str(root / doc) if doc else DOC), (str(root / app) if app else APP), sec.get("section", SECTION)


def main(argv):
    doc_path, app_dir, section = _settings(argv)

    if not doc_path.is_file():
        raise Unmeasured(f"[안 잼] 지도 문서가 없다 — {doc_path}. 어떻게 주나: 첫 인자가 그 자리다")
    if not app_dir.is_dir():
        raise Unmeasured(f"[안 잼] 부품 폴더가 없다 — {app_dir}. 어떻게 주나: 둘째 인자가 그 자리다")

    doc_said = doc_path.name
    doc_text = doc_path.read_text(encoding="utf-8")
    files, skipped = scan_files(app_dir)
    rows = scan_doc(doc_text, section)

    # 한쪽이 빈손이면 차집합도 비어 **아무것도 안 재고 초록이 난다.** 그 자리를 먼저 막는다.
    if not files or not rows:
        raise Unmeasured(
            f"[안 잼] 실물 {len(files)}개 · 표 줄 {len(rows)}개. 둘 중 하나가 비면 차집합은 "
            f"늘 0 이라 판정이 안 선다 (표 줄이 0 이면 「{section}」 절 제목이 바뀐 자리부터 본다)")

    print("--- ① 실물 대조")
    unlisted, ghost = compare(files, rows)
    report("표에 없는 부품이 없다 — 파일마다 제 줄이 있다", not unlisted,
           [f"{n} — 파일은 사는데 {doc_said} 에 줄이 없다" for n in unlisted])
    report("실물 없는 줄이 없다 — 줄마다 그 파일이 산다", not ghost,
           [f"{n} — {doc_said} 에 줄은 있는데 파일이 없다" for n in ghost])

    edge(f"쟀다: 실물 {len(files)}개 ↔ 표 줄 {len(rows)}개 "
         f"({app_dir.name}/ 아래 전부 ↔ 「{section}」 절의 표 첫 칸 · 지도는 {doc_said})")
    edge("근거 대고 뺐다 — " + (" · ".join(skipped) if skipped else "이 나무에는 없다"))
    edge("안 쟀다 — 도해의 간선(누가 누구를 부르나). 집합이 아니라 배선 그래프라 파일 "
         "목록에서 안 나온다")
    edge("안 쟀다 — 표 밖 산문이 든 셈·이름(문단이 「파일 몇 개」라 적은 수 따위). "
         "표 줄이 아니라 문장이라 집합으로 안 뜬다")
    edge("안 쟀다 — 그 줄이 **무엇을 드나**. 이름 곁의 칸은 사람이 실물을 읽고 적은 판단이다")

    print("\n--- ② 자기 이빨 — 손댄 사본이 정말 빨강을 내나")
    # ⚠ **사본의 파일 목록은 `rows` 로 세운다 — `files` 가 아니다.** 실물에서 뜨면 ①이
    #   빨간 날 사본도 같이 빨개져, 「손댄 탓」과 「원래 어긋나 있던 탓」이 안 갈린다.
    #   지도 글자는 실물 그대로 쓴다 — 절 앵커와 표 읽개가 진짜 문서 모양에 물리는지도
    #   같이 재려는 것이다.
    tmps = []
    try:
        # ㉮ 양성 대조 — 안 건드린 사본은 초록이라야 한다. 이게 없으면 아래 빨강이
        #    「손댄 탓」인지 「사본이 애초에 깨진 탓」인지 안 갈린다.
        #    하위 폴더(`static/`)까지 훑는지도 여기서 함께 선다 — 안 내려가면 그 줄들이
        #    통째로 「실물 없는 줄」로 떠 이 판정이 빨개진다.
        base = _plant(rows, doc_text); tmps.append(base)
        got = _survey(base, section)
        report("㉮ 안 건드린 사본은 초록이다 (양성 대조)", got == ([], []),
               [f"실측 {got} — 기대 ([], [])"])

        # ㉯ 표 줄 하나를 지운다 → 그 부품이 「표에 없는 부품」으로 서야 한다
        dropped_text, dropped = _drop_row(doc_text, section)
        cut = _plant(rows, dropped_text); tmps.append(cut)
        got = _survey(cut, section)
        report(f"㉯ 표 줄을 하나 지우면 빨강이다 ({dropped})",
               got == ([dropped], []) if dropped else False,
               [f"실측 {got} — 기대 ([{dropped!r}], [])"])

        # ㉰ 가짜 부품 파일을 심는다 → 같은 갈래로 서야 한다
        fake = "zzz_planted_part.py"
        planted = _plant(rows | {fake}, doc_text); tmps.append(planted)
        got = _survey(planted, section)
        report(f"㉰ 가짜 부품을 심으면 빨강이다 ({fake})", got == ([fake], []),
               [f"실측 {got} — 기대 ([{fake!r}], [])"])

        # ㉱ 파일 하나를 지운다 → **다른 갈래**(실물 없는 줄)가 서야 한다.
        #    ㉯㉰ 는 둘 다 같은 갈래를 무므로, 이것이 없으면 둘째 갈래는 이빨이 없다.
        gone = sorted(rows)[0]
        holed = _plant(rows - {gone}, doc_text); tmps.append(holed)
        got = _survey(holed, section)
        report(f"㉱ 파일을 하나 지우면 다른 갈래로 빨강이다 ({gone})", got == ([], [gone]),
               [f"실측 {got} — 기대 ([], [{gone!r}])"])

        # ㉲ **절 앵커가 정말 무나** — 다른 절의 표에 앉은 이름은 부품으로 안 선다.
        #    안 물면 남의 표 줄이 부품 집합에 섞여 ②가 조용히 거짓 초록이 된다.
        away = "zzz_outside_section.py"
        loose = _plant(rows | {away},
                       doc_text + f"\n## 다른 절\n\n| `{away}` | 남의 표에 앉은 이름 |\n")
        tmps.append(loose)
        got = _survey(loose, section)
        report(f"㉲ 다른 절의 표 줄은 안 센다 ({away})", got == ([away], []),
               [f"실측 {got} — 기대 ([{away!r}], []). 절 밖 줄을 세면 ([], []) 로 뭉갠다"])

        # ㉳ **까닭 대고 뺀 꼴이 정말 그 자리로 세어지나.** 위 「근거 대고 뺐다」 줄이
        #    이걸로 서는데, 삼켜지면 그 줄이 「없다」고 **거짓말을 한다** — 판정은 초록인 채로.
        buried = _plant(rows, doc_text); tmps.append(buried)
        (buried / TMP_APP / "__pycache__").mkdir()
        (buried / TMP_APP / "__pycache__" / "server.cpython-313.pyc").write_bytes(b"")
        kept, cut_off = scan_files(buried / TMP_APP)
        got = compare(kept, scan_doc(doc_text, section))
        report("㉳ 파생물은 초록이되 뺀 자리로 센다 (`__pycache__/`)",
               got == ([], []) and bool(cut_off),
               [f"실측 판정 {got} · 뺀 자리 {cut_off} — "
                f"기대 ([], []) 와 한 자리 이상 (실물 {len(kept)}개)"])
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    bad = fails()
    if bad:
        print(f"\n❌ {len(bad)}건 실패 — {' · '.join(bad)}", file=sys.stderr)
        return EXIT_MISMATCH
    print(f"\n✅ 부품 지도와 실물이 맞는다 — 판정 {len(passes())}건 "
          f"(실물 {len(files)} ↔ 표 줄 {len(rows)} · 자기 이빨 여섯 포함)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
