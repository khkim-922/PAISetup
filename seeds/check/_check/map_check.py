"""검사 지도가 실물과 맞나 — 줄 ↔ 파일의 차집합 · 「무엇을 재나」 칸은 머리 첫 줄에서 낸다.

좌표 — 아뜰리에 #307 ⑥ · #322 ⑧ (이 자가 난 저장소) · 씨앗 규율은 claude-config 결정 0040.

    python _check/map_check.py            # 이 폴더
    python _check/map_check.py <폴더>     # 잴 `_check/` 를 지정 (병렬 작업나무)

**왜 이 검사가 있나.** 이 폴더의 지도는 *어느 검사가 있고 무엇을 재나*를 든다. 그런데
검사를 새로 짓거나 지우거나 이름을 바꿔도 **아무 데서도 안 터진다** — 검사는 그대로 돌고
지도만 조용히 낡는다. 그리고 낡은 자리가 하필 「없는 검사를 있다고 말하는」 쪽이면, 그
줄을 읽은 사람은 **재지도 않은 자리를 봤다고 여긴다.** 문서 낡음 중에 가장 비싼 꼴이다.

재는 것은 **차집합 둘**이고, 둘은 서로 다른 사고다:
  ① **표에 없는 검사** — 파일은 사는데 지도에 줄이 없다. 새로 지어 놓고 안 적었거나
     이름을 바꾸고 한쪽만 고친 자리. 그 검사는 아무도 안 돌린다
  ② **실물 없는 줄** — 지도에 줄은 있는데 파일이 없다. 지우거나 옮긴 자리. 읽는 사람이
     없는 검사를 믿는다

그 위에 ③ **「무엇을 재나」 칸**이 앉는다 — 줄이 있나가 아니라 **그 줄의 첫 곁칸이 실물과
같나**다. 종전에는 사람이 파일을 읽고 표에 옮겨 적었고, 그 순간부터 손사본이라 검사를
고쳐도 표가 안 따라왔다. 지금은 **각 검사 파일의 머리 첫 줄이 진본**이고 칸은 거기서 낸다:

    python _check/map_check.py --write    # 표식이 이끄는 표의 둘째 칸을 다시 쓴다

**머리 첫 줄의 계약 둘** — 이 자가 문다:
  · **표 한 칸에 드는 길이 안**(아래 `LIMIT`) — 넘치면 표가 문단이 되고, 문단이 되면
    사람이 다시 손으로 줄여 앉혀 손사본이 돌아온다
  · **마침표로 닫힌다** — 「한 문장인가」를 기계가 가르는 유일한 눈금이다. 안 닫히면
    다음 줄로 이어지는 문장이라 칸에 앉는 순간 **반 토막이 참말처럼 선다**

⚠ **이슈·ADR 좌표는 첫 줄에 안 둔다** — 표 한 칸에 좌표가 89번 되풀이되면 칸이 안 읽힌다.
  둘째 줄 이하(`좌표 — …`)로 내리되 **지우지는 않는다.**

⚠ **첫 줄은 지도(`.md`)에 앉으므로 문서 검사의 그물에도 든다** — 백틱 조각은
  `doc_span_check.py` 가 경로·식별자로 읽어 실물을 찾는다. 좌표만 백틱으로 감싸고
  낱말(`image/webp` 같은 형식 이름)은 맨글자로 둔다 — 안 그러면 그 검사가 빨강을 낸다.

**칸 단위 파생이라 구간 표식이 아니다.** 다른 생성물은 `<!-- generated: … -->` 와
`<!-- /generated -->` 로 구간을 울타리 치는데, 이 표는 한 줄 안에서 **둘째 칸만** 기계 것이고
「언제 돌리나」·「무엇이 있어야 도나」는 사람 것이다. 구간을 치면 손대지 말라는 말이 사람 칸까지
덮는다. 그래서 표식은 **표 머리 곁 한 줄**로 서고 닫는 짝이 없다 — 표의 끝은 표가 스스로 말하고,
어느 칸인지는 그 표의 머리줄이 말한다.

**일부러 안 재는 것 셋** — 판정에 새겨 둔다:
  · **밑줄로 시작하는 공용 부품**(`_verdict.py`·`_serve.py` 따위)은 검사가 아니라 부품이라
    표의 대상이 아니다. **양쪽에서 함께 뺀다** — 한쪽만 빼면 그것이 곧 어긋남으로 뜬다
  · **`fixtures/`·`log/` 안**은 안 본다. 검체와 기록이지 검사가 아니다
  · **`_check/` 밖의 검사**(`kb/`·`prompts/`·`.githooks/`)는 안 문다. 그 폴더들은 검사와
    생성기가 섞여 있어 **파일 목록으로 전수를 못 뜬다** — 지도의 그 표는 손으로 유지되고,
    그 사실이 지도의 「무엇을 안 재나」에 적혀 있다

⚠ **③ 이 무는 것은 「같은 글자인가」까지다.** 그 문장이 *맞는 말을 하나*는 못 잰다 —
  진본을 그대로 옮겼는지만 보므로, 머리 첫 줄이 틀리면 표도 나란히 틀린다. 그래도 값이
  있는 것은 **틀릴 자리가 둘에서 하나로 준다**는 데 있다. 「언제 돌리나」·「무엇이 있어야
  도나」 칸과 어느 갈래 절에 앉나는 여전히 사람이 실물을 읽고 적은 판단이다.

⚠ **어긋남 0 은 그 자체로 초록이 아니다.** 표를 못 읽어도 0 이 나온다. 그래서 아래 §2 가
  **손댄 사본 일곱으로 이 판정이 실제로 무는지**를 같은 판에서 보이고(아뜰리에 결정 0112 의 자기 이빨
  규율), 양쪽이 빈손이거나 표식이 한 자리도 없으면 초록이 아니라 「못 쟀다」(2)로 나간다.

토큰도 네트워크도 브라우저도 안 쓴다.
"""
import ast
import configparser
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from _verdict import EXIT_MISMATCH, EXIT_OK, EXIT_UNMEASURED, edge, fails, passes, report  # noqa: E402

MAP = "README.md"
SUFFIXES = (".py", ".mjs", ".ps1")
PART = "_"          # 밑줄로 시작하면 공용 부품 — 검사가 아니다
LIMIT = 80          # 머리 첫 줄이 넘으면 안 되는 글자 수 — 표 한 칸에 드는 길이
CELL = 2            # 표 줄에서 파생되는 칸의 자리 — 첫 칸이 이름, 그 다음이 「무엇을 재나」

# 표 머리 곁에 서는 칸 단위 생성 표식. **닫는 짝이 없다** — 까닭은 이 파일 머리말.
MARK = ("<!-- generated(둘째 칸): python _check/map_check.py --write · 손으로 고치지 않는다 · "
        "어긋남은 같은 스크립트가 기본으로 문다 · 진본은 그 검사 파일의 머리 첫 줄 · "
        "나머지 칸은 사람 것이라 닫는 표식이 없다 -->")


def _is_check(name):
    """검사 파일의 이름꼴인가 — 표 줄과 파일 목록이 **같은 자**로 걸러진다."""
    return (name.endswith(SUFFIXES)
            and not name.startswith(PART)
            and "/" not in name and "\\" not in name)


def scan_files(check_dir):
    """이 폴더에 실제로 사는 검사 파일 — 하위 폴더는 안 본다(검체·기록이다)."""
    return {p.name for p in Path(check_dir).iterdir()
            if p.is_file() and _is_check(p.name)}


def scan_map(text):
    """지도의 표 줄이 든 검사 파일 — **첫 칸만** 본다.

    본문이 곁말로 다른 검사를 가리키는 자리가 많아, 「어디든 이름이 있나」로 재면
    ①(표에 없는 검사)이 통째로 눈이 먼다. 제 줄에 앉은 것만 센다.
    """
    out = set()
    for line in text.splitlines():
        name = _row_head(line)
        if name:
            out.add(name)
    return out


# 갈래표의 **게이트 절** 이름 — 기계가 「무엇을 태우나」를 여기서 판다 (아뜰리에 결정 0260).
# ⚠ 목록을 CI 에 손으로 적지 않는다. 적으면 새 검사가 조용히 빠지고, 빠진 자리는
#   아무 데서도 안 보인다 — 아뜰리에의 한 검사가 그 꼴로 이틀을 빨갛게 살았다(atelier #342).
GATE_SECTION = "게이트"

# **인자를 받아야 도는 검사** — 기계가 그냥 부르면 「못 쟀다」(2)를 낸다. 빼되 이름과
# 까닭을 함께 둔다 — 까닭 없이 빼면 눈감은 것이다. **씨앗은 비어 있고 이 파일에는 적지 않는다** —
# 받은 저장소는 곁 `map_check.conf` 의 `[needs_arg]` 절에 `이름 = 까닭` 으로 적는다(이 사본은
# 진본과 글자가 같아야 `borrowed_check` 가 초록이다 — 저장소 값은 선언 파일이 든다).
NEEDS_ARG = {}
CONF = "map_check.conf"


def _needs_arg(check_dir):
    """곁 선언의 `[needs_arg]` — 없으면 빈 사전. 선언은 씨앗이 안 싣는다."""
    conf = Path(check_dir) / CONF
    if not conf.is_file():
        return {}
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str            # 파일 이름은 대소문자가 뜻이다
    cp.read(conf, encoding="utf-8")
    return dict(cp["needs_arg"]) if cp.has_section("needs_arg") else {}


def gate_rows(text):
    """지도의 **게이트 절**에 앉은 검사 이름 — 절을 따라가며 첫 칸만 줍는다.

    ⚠ **어느 절에 앉나는 이 검사가 안 무는 자리다**(사람이 적는다 — 판정 곁의 「안 잰
      것」이 그렇게 말한다). 그래서 여기서 읽는 것은 사람이 적어 둔 갈래이고, 빈손이면
      판정이 아니라 **「못 쟀다」로 나간다**: 절 이름이 갈리면 목록이 조용히 0 이 되는데
      **빈 목록은 CI 에서 초록으로 읽힌다.**
    """
    out, here = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            here = line[3:].split("—")[0].strip()
        name = _row_head(line)
        if name and here == GATE_SECTION:
            out.append(name)
    return out


def print_gates(map_text, needs):
    """태울 목록을 낸다 — 이름은 stdout, **뺀 것과 까닭은 stderr.** `needs` 는 뺄 것(이름 → 까닭)."""
    rows = gate_rows(map_text)
    if not rows:
        print(f"⚠ 못 쟀다 — 지도에 「{GATE_SECTION}」 절의 표 줄이 하나도 없다. "
              "절 이름이 갈렸으면 목록이 조용히 비고, 빈 목록은 초록으로 읽힌다.",
              file=sys.stderr)
        return EXIT_UNMEASURED
    for name in rows:
        if name in needs:
            print(f"— 뺐다: {name} · {needs[name]}", file=sys.stderr)
            continue
        print(name)
    return EXIT_OK


def _row_head(line):
    """표 한 줄의 첫 칸이 검사 이름이면 그 이름, 아니면 None."""
    s = line.strip()
    if not s.startswith("|"):
        return None
    cells = s.split("|")
    if len(cells) < 2:
        return None
    name = cells[1].strip().strip("`").strip()
    return name if _is_check(name) else None


def compare(files, rows):
    """(표에 없는 검사, 실물 없는 줄)."""
    return sorted(files - rows), sorted(rows - files)


# ── ③ 「무엇을 재나」 칸 — 진본은 그 검사 파일의 머리 첫 줄이다

def head_line(path):
    """검사 파일의 머리 첫 줄 — 못 읽으면 None.

    갈래마다 머리가 다른 자리에 산다. **꼴이 아니라 그 언어의 관례**로 가른다:
    파이썬은 모듈 독스트링, `.mjs` 는 파일 머리 첫 주석 줄, `.ps1` 은 머리 첫 주석
    줄이되 `.SYNOPSIS` 가 있으면 그것(파워셸이 `Get-Help` 로 내는 자리라 진본이다).
    """
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".py":
        try:
            doc = ast.get_docstring(ast.parse(text), clean=False)
        except SyntaxError:
            return None
        head = (doc or "").splitlines()
    else:
        head = _comment_head(text, path.suffix)
    return head[0].strip() if head and head[0].strip() else None


def _comment_head(text, suffix):
    """머리 주석 덩이를 줄 목록으로 — 주석 표시는 걷고 글자만 남긴다."""
    lines = text.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return []
    first = lines[i].strip()
    if suffix == ".ps1":
        for k, line in enumerate(lines):
            if line.strip().lower().startswith(".synopsis"):
                rest = [x.strip() for x in lines[k + 1:] if x.strip()]
                return rest[:1]
        if first.startswith("<#"):
            return _until(lines, i, "#>", "<#")
        return _run(lines, i, "#")
    if first.startswith("/*"):
        return _until(lines, i, "*/", "/*")
    return _run(lines, i, "//")


def _run(lines, i, mark):
    """한 줄 주석이 잇달아 선 덩이."""
    out = []
    while i < len(lines) and lines[i].strip().startswith(mark):
        out.append(lines[i].strip()[len(mark):].strip())
        i += 1
    return out


def _bare(line):
    """줄머리의 주석 별표만 걷는다.

    ⚠ **굵은 글씨(`**`)는 글자라 안 걷는다.** 뭉뚱그려 `lstrip("*")` 로 걷으면
    `**워드 COM …**` 이 `워드 COM …**` 이 되어 **칸이 조용히 반쪽 문법**으로 앉는다.
    주석 별표는 뒤에 빈칸이 오거나 그 줄이 별표 하나로 끝나는 자리뿐이다.
    """
    s = line.strip()
    return s[1:].strip() if s.startswith("*") and not s.startswith("**") else s


def _until(lines, i, close, open_mark):
    """여닫는 주석 덩이 — 여는 표시와 줄머리 별표를 걷는다."""
    out = [_bare(lines[i].strip()[len(open_mark):])]
    i += 1
    while i < len(lines) and not lines[i].strip().startswith(close):
        out.append(_bare(lines[i]))
        i += 1
    return [x for n, x in enumerate(out) if n or x]     # 여는 줄이 비면 다음 줄이 머리다


def cell_of(first):
    """칸에 앉는 글자 — 첫 줄에서 **맺음 마침표 하나만** 뗀다.

    독스트링 첫 줄은 문장이라 마침표로 닫히는데(PEP 257 · 이 파일의 계약도 같다),
    표 한 칸은 문장이 아니라 조각이라 이 문서의 나머지 칸과 맺음이 갈린다.
    떼는 것이 하나뿐이라 되돌릴 수 있다 — 뜻을 만드는 손질은 여기 없다.
    """
    return first[:-1] if first.endswith(".") else first


def _flaws(first):
    """머리 첫 줄이 계약을 어긴 자리 — 성하면 빈 목록."""
    bad = []
    if len(first) > LIMIT:
        bad.append(f"{len(first)}자 — {LIMIT}자를 넘어 표 한 칸에 안 든다")
    if not first.endswith("."):
        bad.append("마침표로 안 닫힌다 — 다음 줄로 이어지는 문장인지 기계가 못 가른다")
    return bad


def row_lines(lines):
    """표식이 이끄는 표의 자료 줄 번호 — 표식이 없으면 빈 목록.

    표식 다음이 머리줄·구분줄이고 그 뒤가 자료다. 구분줄이 없으면 표가 아니므로
    **그 표식은 세지 않는다** — 문서를 고치다 표식만 남은 자리를 조용히 안 넘긴다.
    """
    out, i, n = [], 0, len(lines)
    while i < n:
        if lines[i].strip() != MARK:
            i += 1
            continue
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        if j + 1 >= n or "---" not in lines[j + 1] or not lines[j + 1].lstrip().startswith("|"):
            i += 1
            continue
        j += 2
        while j < n and lines[j].lstrip().startswith("|"):
            out.append(j)
            j += 1
        i = j
    return out


def set_cell(line, cell):
    """표 한 줄의 파생 칸만 갈아 앉힌다 — 나머지 칸은 글자 그대로 둔다."""
    cells = line.split("|")
    cells[CELL] = f" {cell} "
    return "|".join(cells)


def cell_gap(check_dir):
    """(표에 앉은 검사, 어긋난 칸, 머리 첫 줄의 흠) — 판정을 안 찍고 재기만 한다.

    본판과 §2 의 사본이 **같은 자**로 재게 하려고 재기와 판정을 갈랐다.
    """
    lines = (check_dir / MAP).read_text(encoding="utf-8").split("\n")
    seated, gaps, flaw = [], [], []
    for i in row_lines(lines):
        name = _row_head(lines[i])
        if not name:
            continue
        seated.append(name)
        first = head_line(check_dir / name)
        if first is None:
            flaw.append(f"{name} — 머리 첫 줄을 못 읽었다")
            continue
        flaw += [f"{name} — {w}" for w in _flaws(first)]
        got = lines[i].split("|")[CELL].strip()
        want = cell_of(first)
        if got != want:
            gaps.append(f"{name} — 칸 「{got}」 ↔ 머리 「{want}」")
    return seated, gaps, flaw


def write_cells(check_dir):
    """파생 칸을 머리 첫 줄에서 다시 쓴다 — 갈아 앉힌 줄 수를 돌려준다."""
    path = check_dir / MAP
    lines = path.read_text(encoding="utf-8").split("\n")
    hit = 0
    for i in row_lines(lines):
        name = _row_head(lines[i])
        first = head_line(check_dir / name) if name else None
        if not first:
            continue
        made = set_cell(lines[i], cell_of(first))
        if made != lines[i]:
            lines[i] = made
            hit += 1
    if hit:
        path.write_text("\n".join(lines), encoding="utf-8", newline="")
    return hit


# ── 자기 이빨 — 손댄 사본으로 이 판정이 정말 무는지 본다

def _plant(files, map_text):
    """검사 이름만 빈 파일로 세운 임시 나무 — 지도는 준 글자 그대로."""
    root = Path(tempfile.mkdtemp(prefix="map-check-"))
    (root / MAP).write_text(map_text, encoding="utf-8")
    for name in files:
        (root / name).write_text("", encoding="utf-8")
    return root


def _drop_row(text):
    """첫 검사 줄 하나를 지운 지도 — (지운 지도, 지운 이름)."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        name = _row_head(line)
        if name:
            return "".join(lines[:i] + lines[i + 1:]), name
    return text, None


def _survey(root):
    return compare(scan_files(root), scan_map((root / MAP).read_text(encoding="utf-8")))


def _copy(check_dir):
    """검사 파일과 지도만 뜬 사본 — 하위 폴더(검체·기록)는 안 뜬다.

    ③ 의 이빨은 **실물 글자**를 읽으므로 빈 파일로 세운 나무(`_plant`)로는 안 물린다.
    """
    root = Path(tempfile.mkdtemp(prefix="map-cell-"))
    shutil.copy2(check_dir / MAP, root / MAP)
    for p in check_dir.iterdir():
        if p.is_file() and _is_check(p.name):
            shutil.copy2(p, root / p.name)
    return root


def _first_seat(root):
    """사본에서 파생 칸이 앉는 첫 줄 — (줄 번호, 검사 이름, 그 머리 첫 줄)."""
    lines = (root / MAP).read_text(encoding="utf-8").split("\n")
    for i in row_lines(lines):
        name = _row_head(lines[i])
        first = head_line(root / name) if name else None
        if first:
            return i, name, first
    return None, None, None


def _bend_head(root):
    """사본의 머리 첫 줄 하나를 손댄다 — 그 검사 이름을 돌려준다."""
    _, name, first = _first_seat(root)
    if not name:
        return None
    p = root / name
    text = p.read_text(encoding="utf-8-sig")
    p.write_text(text.replace(first, "머리를 손댄 " + first, 1), encoding="utf-8", newline="")
    return name


def _bend_cell(root):
    """사본의 지도에서 파생 칸 하나를 손으로 고친다 — 그 검사 이름을 돌려준다."""
    i, name, _ = _first_seat(root)
    if not name:
        return None
    path = root / MAP
    lines = path.read_text(encoding="utf-8").split("\n")
    lines[i] = set_cell(lines[i], "손으로 고친 칸")
    path.write_text("\n".join(lines), encoding="utf-8", newline="")
    return name


def main(argv):
    args = [a for a in argv[1:] if a not in ("--write", "--gates")]
    write = "--write" in argv[1:]
    gates = "--gates" in argv[1:]
    check_dir = Path(args[0]).resolve() if args else HERE
    map_path = check_dir / MAP

    if not map_path.is_file():
        print(f"⚠ 지도가 없다 — {map_path}", file=sys.stderr)
        return EXIT_UNMEASURED

    map_text = map_path.read_text(encoding="utf-8")
    if gates:                      # 태울 목록만 내고 나간다 — 판정은 안 낸다
        return print_gates(map_text, {**NEEDS_ARG, **_needs_arg(check_dir)})
    files, rows = scan_files(check_dir), scan_map(map_text)
    marks = sum(1 for line in map_text.split("\n") if line.strip() == MARK)

    # 양쪽이 빈손이면 차집합도 비어 **아무것도 안 재고 초록이 난다.** 그 자리를 먼저 막는다.
    if not files or not rows:
        print(f"⚠ 못 쟀다 — 실물 {len(files)}개 · 표 줄 {len(rows)}개. "
              f"둘 중 하나가 비면 차집합은 늘 0 이라 판정이 안 선다.", file=sys.stderr)
        return EXIT_UNMEASURED

    # 표식이 없으면 ③ 은 **셀 것이 없어 조용히 초록**이 된다. 같은 자리를 막는다.
    if not row_lines(map_text.split("\n")):
        print(f"⚠ 못 쟀다 — 표식이 이끄는 표가 한 자리도 없다 (표식 {marks}개). "
              f"칸을 어디서 낼지 모르므로 ③ 이 안 선다.", file=sys.stderr)
        return EXIT_UNMEASURED

    print("--- ① 실물 대조")
    unlisted, ghost = compare(files, rows)
    report("표에 없는 검사가 없다 — 파일마다 제 줄이 있다", not unlisted,
           [f"{n} — 파일은 사는데 {MAP} 에 줄이 없다" for n in unlisted])
    report("실물 없는 줄이 없다 — 줄마다 그 파일이 산다", not ghost,
           [f"{n} — {MAP} 에 줄은 있는데 파일이 없다" for n in ghost])
    edge(f"쟀다: 실물 {len(files)}개 ↔ 표 줄 {len(rows)}개 (첫 칸 기준)")

    parts = sorted(p.name for p in check_dir.iterdir()
                   if p.is_file() and p.name.startswith(PART) and p.suffix in SUFFIXES)
    edge("일부러 뺐다 — 공용 부품 " + (" · ".join(parts) if parts else "이 나무에는 없다"))
    edge("일부러 뺐다 — 하위 폴더(검체·기록)와 `_check/` 밖의 검사. 까닭은 이 파일 머리말")

    print("\n--- ③ 「무엇을 재나」 칸이 머리 첫 줄에서 나오나")
    seated, gaps, flaw = cell_gap(check_dir)
    report("머리 첫 줄이 계약을 지킨다 — 길이 안에 들고 한 문장으로 닫힌다", not flaw, flaw)
    if write:
        hit = write_cells(check_dir)
        _, gaps, _ = cell_gap(check_dir)
        report(f"칸을 갈아 앉혔다 — {hit}줄 · 다시 재니 어긋남 {len(gaps)}건", not gaps, gaps)
    else:
        report(f"칸이 머리 첫 줄과 같다 — 파생 {len(seated)}줄", not gaps, gaps)

    # 표식 밖에 사는 검사 줄은 이 자가 **통째로 못 본다** — 세는 자리를 센티널로 세운다.
    stray = sorted(rows - set(seated))
    report("검사 줄이 전부 표식이 이끄는 표 안에 산다", not stray,
           [f"{n} — 표식 밖의 줄이라 칸이 생성도 대조도 안 된다" for n in stray])
    edge(f"쟀다: 표식 {marks}개 · 파생 칸 {len(seated)}개 (진본은 그 파일의 머리 첫 줄)")
    edge("안 잰 것 — 그 문장이 **맞는 말인가** · 「언제 돌리나」 칸 · 어느 갈래 절에 앉나. 사람이 든다")

    if write:
        print(f"\n✅ 갈아 앉혔다 — 판정 {len(passes())}건 (자기 이빨은 `--write` 에서 안 돈다)")
        return EXIT_MISMATCH if fails() else EXIT_OK

    print("\n--- ② 자기 이빨 — 손댄 사본이 정말 빨강을 내나")
    # ⚠ **사본의 파일 목록은 `rows` 로 세운다 — `files` 가 아니다.** 실물에서 뜨면 ①이
    #   빨간 날 사본도 같이 빨개져, 「손댄 탓」과 「원래 어긋나 있던 탓」이 안 갈린다.
    #   표에서 세우면 ㉮ 가 **짜임으로** 초록이라, 아래 셋의 빨강은 손댄 것만 가리킨다.
    #   지도 글자는 실물 그대로 쓴다 — 표 읽개가 진짜 표 모양에 물리는지도 같이 재려는 것이다.
    tmps = []
    try:
        # ㉮ 양성 대조 — 안 건드린 사본은 초록이라야 한다. 이게 없으면 아래 빨강이
        #    「손댄 탓」인지 「사본이 애초에 깨진 탓」인지 안 갈린다.
        base = _plant(rows, map_text); tmps.append(base)
        report("㉮ 안 건드린 사본은 초록이다 (양성 대조)", _survey(base) == ([], []))

        # ㉯ 표 줄 하나를 지운다 → 그 검사가 「표에 없는 검사」로 서야 한다
        dropped_text, dropped = _drop_row(map_text)
        cut = _plant(rows, dropped_text); tmps.append(cut)
        report(f"㉯ 표 줄을 하나 지우면 빨강이다 ({dropped})",
               _survey(cut) == ([dropped], []) if dropped else False,
               [f"실측 {_survey(cut)} — 기대 ([{dropped!r}], [])"])

        # ㉰ 가짜 검사 파일을 심는다 → 같은 갈래로 서야 한다
        fake = "zzz_planted_check.py"
        planted = _plant(rows | {fake}, map_text); tmps.append(planted)
        report(f"㉰ 가짜 검사를 심으면 빨강이다 ({fake})",
               _survey(planted) == ([fake], []),
               [f"실측 {_survey(planted)} — 기대 ([{fake!r}], [])"])

        # ㉱ 파일 하나를 지운다 → **다른 갈래**(실물 없는 줄)가 서야 한다.
        #    ㉯㉰ 는 둘 다 같은 갈래를 무므로, 이것이 없으면 둘째 갈래는 이빨이 없다.
        gone = sorted(rows)[0]
        holed = _plant(rows - {gone}, map_text); tmps.append(holed)
        report(f"㉱ 파일을 하나 지우면 다른 갈래로 빨강이다 ({gone})",
               _survey(holed) == ([], [gone]),
               [f"실측 {_survey(holed)} — 기대 ([], [{gone!r}])"])

        # ㉲㉳㉴ — ③ 의 이빨. 앞의 넷은 **빈 파일**로 세운 나무라 머리 첫 줄이 없어
        #   칸 축이 통째로 안 물린다. 그래서 여기부터는 실물 사본을 뜬다.
        keep = _copy(check_dir); tmps.append(keep)
        report("㉲ 안 건드린 사본은 칸도 초록이다 (양성 대조)", cell_gap(keep)[1:] == ([], []))

        # ㉳ 진본 쪽을 손댄다 → 칸이 어긋나야 한다
        bent = _copy(check_dir); tmps.append(bent)
        hurt = _bend_head(bent)
        report(f"㉳ 머리 첫 줄을 바꾸면 칸이 빨강이다 ({hurt})",
               bool(hurt) and any(str(hurt) in g for g in cell_gap(bent)[1]),
               [f"실측 {cell_gap(bent)[1] or '어긋남 없음'} — {hurt} 가 서야 한다"])

        # ㉴ 문서 쪽을 손댄다 → **반대 방향**이다. ㉳ 만 있으면 「사람이 칸을 고친 자리」는
        #    이빨이 없다 — 손사본을 끊자는 것이 이 축의 본론이라 그쪽이 더 값이 크다.
        hand = _copy(check_dir); tmps.append(hand)
        touched = _bend_cell(hand)
        report(f"㉴ 칸을 손으로 고치면 빨강이다 ({touched})",
               bool(touched) and any(str(touched) in g for g in cell_gap(hand)[1]),
               [f"실측 {cell_gap(hand)[1] or '어긋남 없음'} — {touched} 가 서야 한다"])
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    bad = fails()
    if bad:
        print(f"\n❌ {len(bad)}건 실패 — {' · '.join(bad)}", file=sys.stderr)
        return EXIT_MISMATCH
    print(f"\n✅ 지도와 실물이 맞는다 — 판정 {len(passes())}건 "
          f"(실물 {len(files)} ↔ 표 줄 {len(rows)} · 파생 칸 {len(seated)} · 자기 이빨 일곱 포함)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
