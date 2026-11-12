"""regulation.py 가 대화에 내는 답의 꼴을 앱 없이 잰다 — 표본 HTML · 가짜 목록 · 가짜 앱 손으로. 사내로도 밖으로도 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 이 스킬의 답은 사람이 회사 규정으로 믿고 움직이는 말이 된다. 표의 열이 밀리면 한도 금액이 엉뚱한 구분에
붙고, 답이 대화 도구의 출력 한도를 넘으면 모델은 앞머리만 보고 답하고, 낡은 목록으로 「요즘 바뀐 것」을 답하면 「바뀐 것 없음」이 된다.
낱말 찾기가 조 하나를 빠뜨리면 「그런 조항은 없다」가 된다.
남기는 까닭(check-design §1 넷) — 길이 분명하다(합친 칸 · 긴 본문 · 하루 넘은 목록은 흔하다. 셋 다 실제로 났다. 긴 문서는 앞머리만
오고 나머지는 이어 읽거나 낱말로 찾는 길이 기본이라 그 길의 빠뜨림이 곧 답의 빠뜨림이다) · 깨지면 조용하다(명령은 종료 0 을 내고 답이
그럴듯하다) · 크게 다친다(규정을 틀리게 알린다) · 다른 무엇도 안 잡는다(실물 앱은 회사 PC 에서만 닿고 거기서도 눈으로 봐야 안다).

판정 여섯 —
  1. 표의 한 행은 한 줄이다 — 소스의 줄바꿈 · 칸 안의 문단이 행을 쪼개지 않는다
  2. 합친 칸(rowspan · colspan)은 차지한 자리마다 같은 글자가 든다 — 줄마다 칸 수가 같다
  3. 낱말 없는 read 의 첫 답부터 more 의 --from 을 따라 읽으면 쪽마다 도구 출력 한도(TOOL_CAP) 밑이고, 쪽을 이으면 본문이 빠짐도
     겹침도 없다. 바뀐 자리는 안 딸려 온다
  4. 줄을 내는 답(recent)도 쪽마다 한도 밑이고, 쪽을 이으면 줄이 빠짐도 겹침도 없다
  5. recent 는 하루 넘은 목록을 그대로 안 쓴다(find 는 쓴다)
  6. read --grep 은 낱말(띄어쓰기가 달라도)이 든 조를 빠짐없이, 안 든 조 없이 낸다. 표의 행이 걸리면 그 표의 첫 행이 함께 온다

기대값은 계약에서 온다 — TOOL_CAP 은 대화 도구에서 잰 한도(``references/SOURCES.md``)이고, 조의 글자와 낱말이 든 조는 이 검사가
지은 가짜 문서에서 온다. 재이는 코드의 상수 · 답을 기대값으로 읽지 않는다.

물림 — 판정마다 그 계약을 푼 사본(글자 치환)에 같은 판정을 대어 빨강을 본다(매번 돈다). 치환할 글자가 코드에 없으면 「못 쟀다 —
물림을 다시 지을 일」로 알리고 통과 · 종료 값에는 안 센다.

돌리는 법::  python -X utf8 -I check_regulation.py

판정 — 끝 줄이 「통과 N/N」이면 종료 0, 어긋나면 1.

언제 걷나 — regulation.py 가 사라지거나, 본문을 글자로 푸는 일 · 답을 끊는 일이 다른 자리로 옮겨 가 거기서 재이면.

여기서 못 재는 것 — 실물 SSO · 앱에 들어가는 길 · 앱이 내는 HTML 과 JSON 의 실물 꼴 · 세션 받는 손(ep-login 의 검사가 잰다) ·
Codex · agy 의 출력 한도.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import time
import types
from datetime import date

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE / "regulation.py"
TOOL_CAP = 30000               # 대화 도구가 출력을 파일로 빼기 시작하는 크기(바이트 · 잰 것)
ARTICLES = 900                 # 쪽 넘기기를 재는 가짜 문서의 조 수 — 본문이 한도의 몇 배가 되게
ROWS = 400                     # 가짜 목록의 줄 수 — recent 의 기본 쪽(80 줄)이 한도를 넘게
LAW = 60                       # 낱말 찾기를 재는 가짜 규정의 조 수
WITH_WORD = (7, 23, 41)        # 가짜 규정에서 「숙박비」 가 든 조

SPLIT_TABLE = ("<table>\n<tbody>\n<tr>\n\t<td>구분</td>\n\t<td>국내</td>\n\t<td>해외</td>\n</tr>\n<tr>\n\t<td>\n\t<p>숙박비</p>\n\t<p>(1 박)</p>\n\t</td>\n"
               "\t<td>7만원<br>이내</td>\n\t<td>실비</td>\n</tr>\n</tbody>\n</table>")
SPLIT_WANT = ["구분 | 국내 | 해외", "숙박비 (1 박) | 7만원 이내 | 실비"]
MERGED_TABLE = ('<table><tr><td rowspan="2"><p>구분</p></td><td colspan="2">숙박비</td></tr><tr><td>국내</td><td>해외</td></tr>'
                '<tr><td rowspan="2">임원</td><td>10만원</td><td>실비</td></tr><tr><td>12만원</td><td>실비</td></tr>'
                "<tr><td>직원</td><td>7만원</td><td>$150</td></tr></table>")
MERGED_WANT = ["구분 | 숙박비 | 숙박비", "구분 | 국내 | 해외", "임원 | 10만원 | 실비", "임원 | 12만원 | 실비", "직원 | 7만원 | $150"]

MUTANTS = (   # (이름, 푸는 글자, 바꿀 글자, 빨개져야 하는 판정 번호)
    ("칸 안의 줄바꿈을 안 접는다", 're.sub(r"\\s+", " ", "".join(buf)).strip()', '"".join(buf).strip()', 1),
    ("세로로 합친 칸을 안 채운다", "if rowspan > 1:", "if rowspan > 10 ** 6:", 2),
    ("답의 크기를 안 맞춘다", "OUT_BYTES = load(\"ep_session\", EP_LOGIN_SCRIPTS).OUT_BYTES", "OUT_BYTES = 10 ** 9", 3),
    ("첫 답이 본문의 앞머리를 건너뛴다", "fit_text(out, body, 0, min(", "fit_text(out, body, READ_FIRST, min(", 3),
    ("답의 크기를 안 맞춘다", "OUT_BYTES = load(\"ep_session\", EP_LOGIN_SCRIPTS).OUT_BYTES", "OUT_BYTES = 10 ** 9", 4),
    ("recent 가 낡은 목록을 쓴다", "RECENT_FRESH_DAYS = 1 ", "RECENT_FRESH_DAYS = 99 ", 5),
    ("걸린 표의 첫 행을 안 붙인다", "top = top if top < first else None", "top = None", 6),
)


def module(old: str | None = None, new: str = "") -> types.ModuleType | None:
    """regulation.py 를 싣는다 — old 를 주면 그 글자를 new 로 바꾼 사본을. old 가 코드에 없으면 None."""
    source = SOURCE.read_text(encoding="utf-8")
    if old is not None:
        if old not in source:
            return None
        source = source.replace(old, new)
    mod = types.ModuleType("regulation_under_check")
    mod.__file__ = str(SOURCE)
    sys.modules[mod.__name__] = mod
    exec(compile(source, str(SOURCE), "exec"), mod.__dict__)   # noqa: S102 — 재일 코드를 사본째 싣는다
    return mod


def sized(out: dict) -> int:
    return len((json.dumps(out, ensure_ascii=False) + "\n").encode("utf-8"))


def write_index(r, rows: list, age_days: float = 0.0) -> None:
    path = pathlib.Path(os.environ["REGULATION_INDEX_DIR"]) / "index.json"
    index = {"format": r.INDEX_FORMAT, "stamp": time.time() - age_days * 86400, "menus": ["전사공통"], "rows": rows}
    path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def read(r, doc: dict, *flags: str) -> dict:
    """가짜 앱 손에 doc 을 물리고 ``read 1 <flags>`` 의 답을 받는다."""
    r.load = lambda name, where: types.SimpleNamespace(App=lambda session: types.SimpleNamespace(info=lambda idx: doc))
    return r.run(r.parser().parse_args(["read", "1", *flags]), pathlib.Path("unused"))


def article(n: int) -> str:
    """가짜 규정의 n 조 — 한 문단의 글자. WITH_WORD 의 조에만 「숙박비」 가 들고, 23 조는 띄어 쓴다."""
    word = {7: "숙박비는 실비로 지급한다. ", 23: "숙박 비의 한도는 아래 표와 같다. ", 41: "숙박비 정산은 귀임 뒤 7 일 안에 한다. "}.get(n, "")
    return f"제{n}조(제목{n}) {word}" + "이 조는 검사가 지은 본문이다. 출장의 승인과 여비의 정산 절차를 정한다. " * 8


def law(count: int = LAW) -> dict:
    """가짜 규정 — 조마다 한 문단. 23 조 뒤에는 머리 행에서 먼 행에 낱말이 든 표가 붙는다."""
    rows = "".join(f"<tr><td>{'임원 숙박비' if k == 9 else f'{k} 급지 일비'}</td><td>{k}만원</td><td>실비</td></tr>" for k in range(1, 13))
    table = f"<table><tr><td>구분</td><td>국내</td><td>해외</td></tr>{rows}</table>"
    body = "".join(f"<p>{article(n).strip()}</p>" + (table if n == 23 else "") for n in range(1, count + 1))
    return {"ProcessInfo": [{"processIdx": 1, "processName": "시험 규정", "content": body}],
            "searchTobe": [{"note": "시험", "oldContent": "<p>전</p>", "toContent": "<p>후</p>"}]}


# ── 판정 — 맞으면 None, 어긋나면 그 까닭 ─────────────────────────────────
def split_rows(r) -> str | None:
    got = r.plain(SPLIT_TABLE).split("\n")
    return None if got == SPLIT_WANT else f"행이 쪼개졌다: {got}"


def merged_cells(r) -> str | None:
    got = r.plain(MERGED_TABLE).split("\n")
    return None if got == MERGED_WANT else f"열이 밀렸다: {got}"


def read_pages(r) -> str | None:
    body = "".join(f"<p>제{n}조(시험) 이 조는 검사가 지은 본문이다. 출장비와 숙박비의 한도를 정한다.</p>" for n in range(1, ARTICLES + 1))
    side = "개정 전후의 글자 " * 300
    doc = {"ProcessInfo": [{"processIdx": 1, "processName": "시험 지침", "content": body}],
           "searchTobe": [{"note": "시험", "oldContent": f"<p>{side}</p>", "toContent": f"<p>{side}</p>"} for _ in range(30)]}
    text, flags = "", ()                                 # 첫 판은 낱말도 자리도 없이 — 그 답의 more 가 다음 판의 자리다
    for turn in range(500):
        out = read(r, doc, *flags)
        if sized(out) > TOOL_CAP:
            return f"{turn + 1} 째 쪽이 {sized(out)} 바이트다 — 한도 {TOOL_CAP}"
        if "changes" in out:
            return f"{turn + 1} 째 쪽에 바뀐 자리가 딸려 왔다"
        text += out["text"]
        if "more" not in out:
            break
        start = out["from"] + len(out["text"])
        if str(start) not in out["more"]:
            return f"more 가 다음 자리 {start} 를 안 든다: {out['more']}"
        flags = ("--from", str(start))
    else:
        return "쪽이 안 끝난다"
    seen = [text.count(f"제{n}조(") for n in range(1, ARTICLES + 1)]
    return None if seen == [1] * ARTICLES else f"쪽을 이은 본문에서 조가 빠지거나 겹쳤다 — 한 번씩이 아닌 조 {sum(1 for c in seen if c != 1)} 개"


def row_pages(r) -> str | None:
    today = date.today().strftime("%Y.%m.%d")
    rows = [{"processIdx": n, "processName": f"검사가 지은 긴 이름의 작업표준 문서 {n:04d} — 포항 화성부 3 코크스공장 원료 장입 · 건류 · 압출 · 소화 작업",
             "enforcementDate": today, "hname": "홍길동", "deptnm": "화성부 3 코크스공장 건류계", "version": "12",
             "path": "기초소재 > 작업표준 > 포항화성 > 3 코크스공장 > 원료 장입 · 건류 · 압출 · 소화 작업 표준"} for n in range(ROWS)]
    write_index(r, rows)
    got, start = [], 0
    for turn in range(500):
        out = r.run(r.parser().parse_args(["recent", "--from", str(start)]), None)
        if sized(out) > TOOL_CAP:
            return f"{turn + 1} 째 쪽이 {sized(out)} 바이트다 — 한도 {TOOL_CAP}"
        got += [x["processIdx"] for x in out["rows"]]
        if "more" not in out:
            break
        start = out["from"] + len(out["rows"])
    else:
        return "쪽이 안 끝난다"
    return None if sorted(got) == list(range(ROWS)) else f"쪽을 이은 줄이 {len(got)} 줄이다 — {ROWS} 줄이 한 번씩이어야 한다"


def recent_freshness(r) -> str | None:
    write_index(r, [], age_days=2)
    if r.usable_index(r.parser().parse_args(["recent"])) is not None:
        return "recent 가 이틀 된 목록을 그대로 쓴다"
    return None if r.usable_index(r.parser().parse_args(["find", "말"])) is not None else "find 가 이틀 된 목록을 안 쓴다"


def grep_whole(r) -> str | None:
    out = read(r, law(), "--grep", "숙박비")
    texts = [h["text"] for h in out["hits"]]
    got = [n for n in range(1, LAW + 1) if any(f"제{n}조(제목{n})" in text for text in texts)]
    if got != list(WITH_WORD):
        return f"낱말이 든 조와 답의 조가 다르다 — 답: {got}"
    row = next((text for text in texts if "임원 숙박비 | 9만원 | 실비" in text), None)
    if row is None:
        return "낱말이 든 표의 행이 안 왔다"
    return None if "구분 | 국내 | 해외" in row else "걸린 표의 첫 행(머리)이 함께 안 왔다"


CHECKS = ((1, "표의 한 행은 한 줄", split_rows), (2, "합친 칸은 자리마다 채운다", merged_cells),
          (3, "read 는 첫 답부터 쪽마다 한도 밑 · 빠짐없이", read_pages), (4, "줄 답도 쪽마다 한도 밑 · 빠짐없이", row_pages),
          (5, "recent 는 하루 넘은 목록을 안 쓴다", recent_freshness), (6, "--grep 은 낱말이 든 조를 빠짐없이", grep_whole))


def main() -> int:
    passed = total = 0
    with tempfile.TemporaryDirectory() as temp:
        os.environ["REGULATION_INDEX_DIR"] = temp
        for number, name, check in CHECKS:
            why = check(module())
            total += 1
            passed += why is None
            print(f"{'맞다' if why is None else '어긋났다'} — {number}. {name}" + ("" if why is None else f": {why}"))
        for name, old, new, number in MUTANTS:
            mutant = module(old, new)
            if mutant is None:
                print(f"못 쟀다 — 물림 「{name}」: 치환할 글자가 코드에 없다. 물림을 다시 지을 일")
                continue
            bitten = next(check for n, _, check in CHECKS if n == number)(mutant) is not None
            total += 1
            passed += bitten
            print(f"{'물었다' if bitten else '못 물었다'} — 물림 「{name}」 → 판정 {number}")
    print(f"통과 {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
