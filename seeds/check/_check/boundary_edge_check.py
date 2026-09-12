"""외곽과 동일값으로 녹은 카드 행이 노출 모서리 처리를 실었나 — 인자로 준 HTML.

좌표 — 이 자가 난 자리는 아뜰리에 결정 0157(2026-08-24 실측)이다. 규칙의 진본은 **받는
저장소의 지면 지시문**이고 여기는 그 규칙의 결정론 갈래만 든다. 판정 손과 종료코드 계약은
곁 `_verdict.py` 가, 계약의 뜻은 곁 `README.md` §종료코드 가 든다.

    python -X utf8 _check/boundary_edge_check.py                        # 자검만
    python -X utf8 _check/boundary_edge_check.py --width 840 <html…>    # 자검 + 파일 판정
    BOUNDARY_CARD_WIDTH=840 python -X utf8 _check/boundary_edge_check.py <html…>

**무엇을 재나.** HTML 에서 **외곽 배경과 동일값인 카드 직계 행**을 찾아, 그 행이 외곽과
맞닿는 노출 모서리(첫 행: 위·좌·우 / 끝 행: 아래·좌·우 / 중간 행: 좌·우)에 border 를
실었는지, 또는 카드 `<table>` 자체가 outline/border 를 실었는지 잰다.

**왜 코드가 재나.** 이 결함은 눈 없는 자체 점검이 설계상 못 본다 — 그림을 안 싣기 때문이다.
동일값 비교는 의미 판단이 아니라 결정론이라 코드 몫이다. 난 자리의 실측에서는 카드 첫 행이
외곽과 같은 값인데 선이 **아래** 모서리에만 실려, 정작 외곽과 만나는 위·좌·우가 비어 그
행이 지면에 통째로 녹았다. 자리 이름마다 모서리를 배정하는 열거식이 틀린 모서리를 짚은 것이다.

**받는 저장소가 무엇을 줘야 도나 — 카드 폭 하나다.** 카드 `<table>` 을 집는 유일한 열쇠가
`width` 속성값이라, 그 값만 `--width` 나 환경변수 `BOUNDARY_CARD_WIDTH` 로 받으면 나머지는
메일 HTML 일반의 것이다. 폭을 박아 두지 않는 까닭은 그 값이 저장소마다 다른 유일한 자리이기
때문이다 — 박으면 이 파일이 그 저장소의 것이 된다.

⚠ **인자 없이 돌면 자검만 돌고 초록이다** — 검출 논리가 사는지를 잰 것이고 파일은 0장 판정이다.
  초록 줄이 잰 파일 수를 파생으로 찍으므로 그 초록이 한 장도 안 잰 판을 덮지 않는다.
⚠ **파일을 주고 폭을 안 주면 「못 쟀다」(2)로 나간다.** 폭이 없으면 어느 파일이든 카드를 못
  집어 「구조를 못 찾았다」가 되는데, 그 침묵은 초록과 구별이 안 된다 — 일반화가 새로 낸
  사고라 이 갈래와 아래 센티널이 함께 문다.
⚠ **양성 대조가 실물 판정보다 먼저 선다.** §1 이 일부러 어긋난 검체로 검출이 실제로 무는지
  보이고, §2 가 처방이 선 검체와 **폭이 안 맞는 판**(센티널)을 안 무는지 보인다.

**안 재는 것** — 인접 톤(동일값이 아닌 이웃 값)은 안 잰다. 그 층은 눈이 드는 자리라 사람
몫이다 · 배경 없는 행(카드 바탕이 비치는 행)은 동일값 후보가 아니라 안 잰다 · `background`
축약형·이미지 배경은 안 읽는다(`background-color` 와 `bgcolor` 만) · 카드 `<table>` 이 여럿이면
**처음 만난 하나만** 본다 · 선의 **색**이 대비를 이루는가는 안 잰다(그 값은 지시문이 든다) ·
실제로 브라우저가 그 선을 그리나는 안 잰다 — 원문의 꼴까지다.

토큰도 망도 브라우저도 안 쓴다.
"""
import os
import re
import sys
from pathlib import Path

from _verdict import (EXIT_MISMATCH, EXIT_OK, EXIT_UNMEASURED, Unmeasured,
                      edge, fails, passes, report, unmeasured, unmeasureds)

ENV_WIDTH = "BOUNDARY_CARD_WIDTH"   # 카드 폭을 주는 두 번째 길 — `--width` 와 같은 값이다
SIDES = ("top", "bottom", "left", "right")

_TAG = re.compile(r"<(/?)(table|tr|td)\b[^>]*>", re.I)


# ── 검출 ──────────────────────────────────────────────────────────────────────

def _norm(color):
    """색 글자를 한 꼴로 — 소문자 · 세 자리 축약은 여섯 자리로 편다(`#EEE` 와 `#eeeeee` 는 같다)."""
    c = color.strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", c):
        c = "#" + "".join(ch * 2 for ch in c[1:])
    return c


def _bg(tag):
    """한 태그의 배경색 — `bgcolor` 속성 또는 style 의 `background-color`. 없으면 None."""
    m = re.search(r'bgcolor\s*=\s*["\']?([#\w]+)', tag, re.I)
    if m:
        return _norm(m.group(1))
    m = re.search(r'background-color\s*:\s*([^;"\']+)', tag, re.I)
    return _norm(m.group(1)) if m else None


def _borders(tag):
    """태그 style 에 선 처방이 선 모서리들 — `border`·`outline` 축약형은 네 모서리 전부다."""
    style = (re.search(r'style\s*=\s*"([^"]*)"', tag, re.I) or
             re.search(r"style\s*=\s*'([^']*)'", tag, re.I))
    if not style:
        return set()
    s = style.group(1).lower()
    if re.search(r"(?:^|;)\s*(?:border|outline)\s*:", s):
        return set(SIDES)
    return {side for side in SIDES if re.search(rf"(?:^|;)\s*border-{side}\s*:", s)}


def _card_rows(html, width):
    """(카드 table 태그, 카드 직계 행들의 첫 `<td>` 태그 목록) — 못 찾으면 (None, [])."""
    card_at = None
    for m in re.finditer(r"<table\b[^>]*>", html, re.I):
        if re.search(rf'width\s*=\s*["\']?{re.escape(width)}\b', m.group(0)):
            card_at = m
            break
    if not card_at:
        return None, []
    depth, in_row, rows = 0, False, []
    for m in _TAG.finditer(html, card_at.start()):
        close, name = m.group(1) == "/", m.group(2).lower()
        if name == "table":
            depth += -1 if close else 1
            if depth == 0:
                break
        elif depth == 1 and name == "tr":
            in_row = not close
        elif depth == 1 and name == "td" and not close and in_row:
            rows.append(m.group(0))
            in_row = False          # 직계 행의 첫 칸만 — 나머지 칸은 같은 행이다
    return card_at.group(0), rows


def check(html, width):
    """빨강 목록을 돌려준다 — 비면 초록. **구조를 못 찾으면 None**(초록이 아니라 못 잰 것이다)."""
    outer = None
    m = re.search(r"<table\b[^>]*>", html, re.I)
    if m:
        outer = _bg(m.group(0))
    if not outer:
        m = re.search(r"<body\b[^>]*>", html, re.I)
        outer = _bg(m.group(0)) if m else None
    card, rows = _card_rows(html, width)
    if not outer or not card or not rows:
        return None
    if _borders(card):              # 카드 outline/border — 카드 폭을 세우는 처방이 이미 섰다
        return []
    bad = []
    last = len(rows) - 1
    for i, td in enumerate(rows):
        if _bg(td) != outer:
            continue
        need = ({"top", "left", "right"} if i == 0 else
                {"bottom", "left", "right"} if i == last else
                {"left", "right"})
        missing = need - _borders(td)
        if missing:
            spot = "첫 행" if i == 0 else "끝 행" if i == last else f"{i + 1}행"
            bad.append(f"{spot} 배경이 외곽과 동일값({outer})인데 "
                       f"노출 모서리 {'·'.join(sorted(missing))} 에 선이 없다")
    return bad


# ── 검체 — 씨앗 안에 글자로 굽는다(폴더에 파일을 안 둔다) ──────────────────────

SELF_WIDTH = "640"      # 자검 검체가 제 안에서만 쓰는 폭 — 실물의 폭과 아무 상관이 없다
OUTER = "#eeeeee"       # 외곽 배경
CARD = "#ffffff"        # 카드 배경 — 외곽과 달라야 동일값 후보에서 빠진다
BAND = "#223344"        # 반전 밴드 — 동일값도 아니고 노출 모서리도 아닌 대조군
LINE = "#556677"        # 선 색 — 이 자는 색의 대비를 안 잰다. 서 있나만 본다


def _page(hero_td, tail="", card_extra=""):
    """외곽 → 감싼 표 → 카드 표 → 행들. `hero_td` 는 여는 `<td …>` 만 준다."""
    return (f'<body style="background-color:{OUTER};">'
            f'<table style="background-color:{OUTER};"><tr><td align="center">'
            f'<table width="{SELF_WIDTH}" style="{card_extra}background-color:{CARD};">'
            f'<tr>{hero_td}본문</td></tr>'
            f'<tr><td style="background-color:{BAND};">밴드</td></tr>'
            f'{tail}</table></td></tr></table></body>')


RED = [
    ("첫 행 동일값 + 아래 선만 → 빨강 (난 자리의 실측 재현 모양)",
     _page(f'<td style="background-color:{OUTER}; border-bottom:1px solid {LINE};">'), 1),
    ("끝 행 동일값 + 처리 없음 → 빨강",
     _page(f'<td style="background-color:{CARD};">',
           f'<tr><td style="background-color:{OUTER};">동일값 끝 행</td></tr>'), 1),
    ("`bgcolor` 속성 · 세 자리 축약 · 대문자도 같은 값으로 읽는다",
     _page('<td bgcolor="#EEE">'), 1),
]

GREEN = [
    ("첫 행 동일값 + 위·좌·우 선 → 초록",
     _page(f'<td style="background-color:{OUTER}; border-top:1px solid {LINE};'
           f' border-left:1px solid {LINE}; border-right:1px solid {LINE};">')),
    ("첫 행이 외곽과 다른 값 → 발동 안 함",
     _page(f'<td style="background-color:{CARD};">')),
    ("동일값이어도 카드 outline 이 서면 → 초록 (카드 폭을 세우는 처방)",
     _page(f'<td style="background-color:{OUTER};">', card_extra=f"border:1px solid {LINE}; ")),
]

WRONG_WIDTH = "9999"    # 어느 검체에도 없는 폭 — 센티널이 이 값으로 「못 찾음」을 확인한다


def positive_control():
    """검체가 실제로 그 꼴인지부터 묻는다 — 이 절이 빨강이면 아래 파일 판정의 초록은 뜻이 없다."""
    print(f"--- §1 양성 대조 — 일부러 어긋난 검체 {len(RED)}이 정말 빨개지나")
    for name, html, want in RED:
        got = check(html, SELF_WIDTH)
        report(name, got is not None and len(got) == want,
               [f"실측 {got!r} ← 기대 빨강 {want}건"])

    print(f"\n--- §2 음성 대조 — 처방이 선 검체 {len(GREEN)}과 폭이 안 맞는 판은 안 문다")
    for name, html in GREEN:
        got = check(html, SELF_WIDTH)
        report(name, got == [], [f"실측 {got!r} ← 기대 빨강 없음"])
    # 센티널 — 일반화가 새로 낸 사고다. 폭이 틀리면 카드를 못 집는데, 그 자리가 빈 목록을
    # 돌려주면 **어느 파일이든 조용히 초록**이 되어 「안 걸렸다」와 「안 쟀다」가 한 칸에
    # 뭉개진다. None 이라야 아래 `survey` 가 그 판을 「못 쟀다」로 내보낸다.
    report("폭이 안 맞으면 초록이 아니라 「못 찾음」이다 (센티널)",
           check(GREEN[0][1], WRONG_WIDTH) is None)


# ── 실물 판정 ─────────────────────────────────────────────────────────────────

def split_args(argv):
    """(폭, 파일들) — `--width N`·`--width=N`, 없으면 환경변수. 둘 다 없으면 폭은 None."""
    width, files, i = None, [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--width" and i + 1 < len(argv):
            width, i = argv[i + 1], i + 2
            continue
        if a.startswith("--width="):
            width, i = a.split("=", 1)[1], i + 1
            continue
        files.append(a)
        i += 1
    return (width or os.environ.get(ENV_WIDTH) or None), files


def survey(files, width):
    """파일들을 재고 판정을 세운다 — 잰 장수를 돌려준다. 못 잰 자리는 `unmeasured()` 가 든다."""
    judged = 0
    for arg in files:
        try:
            html = Path(arg).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            unmeasured(arg, f"못 읽었다 — {type(exc).__name__}: {exc}")
            continue
        got = check(html, width)
        if got is None:
            unmeasured(arg, f"외곽 배경이나 폭 {width} 의 카드 <table> 을 못 찾았다")
            continue
        judged += 1
        report(arg, not got, got)
    return judged


def main(argv):
    width, files = split_args(argv)
    positive_control()

    print("\n--- §3 실물 판정 — 인자로 준 HTML")
    if files and not width:
        raise Unmeasured(
            f"[안 잼] 파일 {len(files)}장을 받았는데 카드 폭을 안 줬다 — 폭이 없으면 카드 "
            "<table> 을 못 집어 어느 파일이든 「못 찾음」이 된다. 어떻게 주나: "
            f"`--width <폭>` 또는 `{ENV_WIDTH}=<폭>`. 그 값은 받는 저장소의 지면 지시문이 든다")
    judged = survey(files, width)
    if not files:
        edge("**파일을 안 받았다** — 이 판이 잰 것은 검출 논리뿐이고 실물은 한 장도 없다. "
             "아래 초록 줄이 그 장수를 파생으로 찍는다")

    edge("**인접 톤은 안 잰다** — 동일값만 문다. `background` 축약형·이미지 배경도 안 읽는다 "
         "(`background-color` 와 `bgcolor` 만)")
    edge("**선의 색과 대비는 안 잰다** — 서 있나까지다. 그 값은 받는 저장소의 지시문이 든다")
    edge("**브라우저가 실제로 그리나는 안 잰다** — 원문의 꼴까지다. 띄워 보지 않는다")
    if width:
        edge(f"잰 범위 — 카드 폭 `{width}` 의 `<table>` **처음 하나**와 그 직계 행들. "
             "카드가 여럿인 지면의 둘째부터는 안 든다")

    print()
    if fails():
        # 어긋남이 「못 쟀다」보다 앞선다 — 한 장이라도 실제로 어긋났으면 그것이 이 판의 말이고,
        # 못 잰 자리는 위 `[?  ]` 줄과 이 곁말이 든다. 갈래가 뭉개지지 않게 함께 찍는다.
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        if unmeasureds():
            print(f"  ⚠ 그 밖에 {len(unmeasureds())}장은 못 쟀다 — {' · '.join(unmeasureds())}")
        return EXIT_MISMATCH
    if unmeasureds():
        print(f"{len(unmeasureds())}장 못 쟀다 — {' · '.join(unmeasureds())}")
        return EXIT_UNMEASURED
    print(f"전부 통과 (판정 {len(passes())}건 — 양성 {len(RED)} · 음성 {len(GREEN)} · "
          f"센티널 하나 · 파일 {judged}장)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
