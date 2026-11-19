"""사규 스킬의 얇은 명령 — 곁의 손(``cbsop.py``)으로 사규관리 앱의 목록을 받아 두고, 거기서 찾고, 앱에 검색하고, 한 건을 읽는다.

부르는 꼴 · 명령마다의 인자 · 답의 칸 · 종료 값은 ``--help`` 가 낸다 — 그 글은 이 파일의 표(``READS`` · ``NOT_HERE`` · ``EXITS``)와 argparse
에서 서고, 이 머리말은 고치는 사람이 읽는 계약만 든다.

- 세션 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 가 쥔다(있는 파일부터 · 거절되면 받는 손으로 한 번 더). 함께 못 서는 인자
  (``refusal``) · 없는 등급(``grade_of``)은 세션 · 목록 받기 전에 종료 2 로 멈춘다
- 받아 둔 목록 — ``find`` · ``tree`` · ``recent`` 는 홈의 목록(``index_path``)으로 답하고 앱을 안 부른다. ``INDEX_DAYS`` 가 지나거나, 최근
  시행을 묻는 판(``wants_fresh``)에 ``RECENT_FRESH_DAYS`` 가 지나면 먼저 새로 받는다
- 등급 문서는 사람의 화면이 여는 만큼만 — 본문 글자를 내는 손가락은 다 ``opened`` 로 문서를 연다
- 앱에 아무것도 쓰지 않는다 — 열람 기록 주소도 안 부른다(``cbsop.py`` 머리말). 받은 본문 글자는 PC 에 안 남기고, ``--images`` 의 그림만
  임시 폴더 아래 ``IMAGES_ROOT/<processIdx>`` 에 남는다
- 본문 — 형제 스킬 company-mail 의 ``visible`` 이 푼다(표는 한 행 한 줄 · 사람 눈에 안 보이는 글은 걷고 그 수를 ``hidden`` 에). 그림은
  ``body_images`` 가 받는다. 목차를 안 내는 까닭과 잰 사실은 ``references/SOURCES.md``
- 내는 것 — 표준 출력에 JSON 하나 · ``OUT_BYTES`` 를 안 넘는다(``page`` · ``fit_text`` · ``grep``)
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import tempfile
import time
from datetime import date, datetime, timedelta

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
MAIL_SCRIPTS = HERE.parents[1] / "company-mail" / "scripts"    # 형제 스킬 — 본문을 푸는 손(``visible``) · 본문 그림을 받는 손(``body_images``)이 사는 자리
IMAGES_ROOT = "company-regulation"   # read --images 가 그림을 받는 자리 — 임시 폴더 아래 <processIdx>
INDEX_DAYS = 30                # 받아 둔 목록을 다시 안 받고 쓰는 날 — 사규는 드물게 바뀌고 다시 받기는 오래 걸린다. 그 사이는 refresh
INDEX_DIR = ".company-regulation"   # 받아 둔 목록의 자리 — 홈 아래(임시 폴더는 정리 도구가 지운다)
INDEX_FILE = "index.json"
INDEX_FORMAT = 3               # 받아 둔 파일의 꼴 번호 — 줄의 칸이 바뀌면 올린다(2 — 폐지 문서 gone · 3 — 줄의 number · valid_to)
PATH_SEP = " > "               # 받아 둔 줄의 경로 칸을 잇는 자리 — 사람이 tree 에 주는 경로도 「>」 로 가른다
MOST_FIND = 40                 # find · tree 답에 싣는 줄 수 — count 는 다 센 수다
MOST_SEARCH = 60               # search 답에 싣는 줄 수
MOST_RECENT = 80               # recent 답에 싣는 줄 수
READ_FIRST = 4000              # 낱말 없는 read 가 싣는 본문 글자 수 — 본문이 이 안이면 통째로 오고, 넘으면 앞 이만큼과 읽는 길이 온다
READ_MAX = 20000               # read 가 한 번에 내는 본문 글자 수의 위 — 한글 본문은 OUT_BYTES 가 먼저 끊는다
GREP_AROUND = 2                # --grep 이 걸린 줄의 앞뒤로 함께 내는 줄 수 — 짧은 줄(표의 행 · 항목)만
GREP_AROUND_CHARS = 200        # 앞 · 뒤로 함께 내는 줄의 글자 수 합 — 긴 문단이 이웃이면 걸린 줄만 낸다
CHANGES_BYTES = 8000           # 짧은 문서의 답에 바뀐 자리(changes)를 함께 실을 때 내주는 몫 — 넘는 항목은 수만 센다
CHANGE_SIDE = 1200             # 바뀐 자리 한쪽(전 · 후)의 글자 수 — 넘으면 자르고 온 길이를 적는다
RECENT_DAYS = 30
RECENT_FRESH_DAYS = 1          # recent 는 이보다 오래된 목록이면 먼저 새로 받는다 — 받아 둔 뒤에 시행된 것을 못 본다
APP_DATE = "%Y.%m.%d"          # 앱이 시행일을 적는 꼴
GONE_SINCE = "2000.01.01"      # 폐지 문서를 받는 기간의 첫날 — 앱의 「최근 변경된 표준」 은 기간을 꼭 받는다(빈 날이면 JSON 이 아니다). 앱의 폐지 기록 전부가 이 뒤다
GONE_STATE = "삭제"            # 그 화면의 상태 칸 — 폐지(삭제)된 표준
GONE_REV = "폐지"              # 폐지 문서의 판 — 앱이 폐지된 문서를 읽을 때 판 칸에 적는 말
SEARCH_HIT_PREFIX = "searchMenuInList"   # 통합 검색 답에서 범주마다의 결과가 든 칸의 머리
INDEX_ONLY = ("find", "tree", "recent")   # 받아 둔 목록이 서 있으면 앱을 안 부르는 명령
FRESH_ONLY = ("recent",)       # 늘 RECENT_FRESH_DAYS 안의 목록을 쓰는 명령 — find 는 --days 를 받았을 때만 그렇다
NEXT_READ = "다음: 물음에 낱말이 있으면 --grep <낱말 …> 로 그 대목만 · 통째로는 more 의 --from 을 따라 끝까지 읽는다"
ROW_KEYS = ("processIdx", "processName", "enforcementDate", "hname", "deptnm", "version")
FIND_KEYS = ("processName", "path", "hname", "deptnm", "number")   # find 가 말을 견주는 칸 — number 는 표준번호(앱 검색도 번호를 받는다)
USED_DAYS = 30                 # search --used 의 기본 기간 — 화면 「최근 사용 표준」 이 처음 여는 기간과 같다


if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    from ep_command import DAY_SECONDS, EXIT_ARGS, Stop, load, size
except ImportError:                             # 형제 스킬 ep-login 이 곁에 없다 — 답의 꼴(JSON 하나 · 종료 1)은 지킨다
    print(json.dumps({"error": "tool", "message": f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"}, ensure_ascii=False))
    sys.exit(1)
from ep_session import squash  # noqa: E402 — 견주기 꼴: 빈칸 · 가운뎃점 · 괄호 · 대소문자를 안 본다

OUT_BYTES = ep_command.OUT_BYTES   # 답 하나(JSON)의 크기 — 수가 사는 자리와 까닭은 형제 스킬 ep-login 의 ep_session


# ── 받아 둔 목록 ─────────────────────────────────────────────────────────
def index_path() -> pathlib.Path:
    """받아 둔 목록의 자리 — ``REGULATION_INDEX_DIR`` 이 있으면 그 폴더, 없으면 홈 아래 ``INDEX_DIR``."""
    root = os.environ.get("REGULATION_INDEX_DIR", "").strip()
    return (pathlib.Path(root) if root else pathlib.Path.home() / INDEX_DIR) / INDEX_FILE


def path_of(row: dict) -> list:
    return [row.get(f"categoriName{i}") for i in range(4) if row.get(f"categoriName{i}")]


def is_folder(row: dict) -> bool:
    """앱의 전체 목록에는 범주 자리 줄이 섞인다 — 제 이름이 제 층의 범주 이름과 같은 줄이다."""
    return row.get("processName") == row.get(f"categoriName{row.get('level', -1)}")


def with_number(out: dict, raw: dict) -> dict:
    """줄에 표준번호(txtIdx)와 인증서의 유효기간 끝(toDate)을 단다 — 있는 줄에만."""
    if raw.get("txtIdx"):
        out["number"] = raw["txtIdx"]
    if raw.get("toDate"):
        out["valid_to"] = raw["toDate"]
    return out


def row_of(raw: dict) -> dict:
    out = {k: raw.get(k) for k in ROW_KEYS}
    out["path"] = PATH_SEP.join(path_of(raw))
    if raw.get("relationName"):
        out["related"] = raw["relationName"]
    return with_number(out, raw)


def gone_of(raw: dict) -> dict:
    """폐지 문서의 줄 — 앱의 「최근 변경된 표준」(삭제) 줄을 받아 둔 줄의 꼴로. 경로는 그 줄의 구분 칸(type1 · 2 · 3)이고, 판은 폐지다."""
    out = {k: raw.get(k) for k in ROW_KEYS}
    out["version"] = GONE_REV
    out["path"] = PATH_SEP.join(raw.get(k) for k in ("type1", "type2", "type3") if raw.get(k))
    return with_number(out, raw)


def build_index(app) -> dict:
    """앱의 전체 목록(공개된 문서) — rows, 폐지된 문서 — gone. 전체 목록에는 폐지 문서가 안 든다(``references/SOURCES.md``)."""
    menus = [m for m in app.menus() if m.get("openYn", "Y") == "Y"]
    rows, seen = [], set()
    for m in menus:
        for raw in app.all_in(m["menuIdx"]):
            if is_folder(raw) or raw.get("processIdx") in seen:
                continue
            seen.add(raw.get("processIdx"))
            rows.append(row_of(raw))
    gone = [gone_of(raw) for raw in app.changed(GONE_SINCE, date.today().strftime(APP_DATE), GONE_STATE)
            if raw.get("processIdx") not in seen]
    return {"format": INDEX_FORMAT, "stamp": time.time(), "menus": [m["menuName"] for m in menus], "rows": rows, "gone": gone}


def cached_index() -> dict | None:
    """INDEX_DAYS 안에 받은 같은 꼴의 목록 — 없거나 낡았거나 깨졌으면 None."""
    got = ep_command.kept(index_path(), INDEX_FORMAT, INDEX_DAYS)
    return got[0] if got and isinstance(got[0].get("rows"), list) and isinstance(got[0].get("gone"), list) else None


def stamp_word(index: dict) -> str:
    return datetime.fromtimestamp(index["stamp"]).strftime("%Y-%m-%d %H:%M")


def under_path(rows: list, words: list) -> tuple[list, int]:
    """경로 말(「기초 > 작업표준 > 포항화성」)의 칸마다 그 깊이의 범주 이름에 든 줄과, 맞춘 깊이 수."""
    segs = [squash(s) for s in " ".join(words).split(">") if squash(s)]
    hit = [r for r in rows
           if len(r["path"].split(PATH_SEP)) >= len(segs)
           and all(seg in squash(part) for seg, part in zip(segs, r["path"].split(PATH_SEP)))]
    return hit, len(segs)


def under_category(rows: list, word: str | None) -> list:
    """범주 말(「작업표준」 · 「기초 > 작업표준」)이 경로의 어느 깊이에서든 이어진 칸들에 든 줄 — 칸마다 그 깊이 범주 이름의 일부면
    된다. 말이 없으면 줄 그대로."""
    segs = [squash(s) for s in (word or "").split(">") if squash(s)]
    if not segs:
        return rows

    def hit(row: dict) -> bool:
        parts = [squash(p) for p in row["path"].split(PATH_SEP)]
        return any(all(seg in parts[at + i] for i, seg in enumerate(segs)) for at in range(len(parts) - len(segs) + 1))

    return [r for r in rows if hit(r)]


def since_of(days: int) -> str:
    """시행일이 최근 days 일 안인가를 가르는 앱 꼴의 날 — 그날부터(그날 포함) 든다."""
    return (date.today() - timedelta(days=days)).strftime(APP_DATE)


def page(head: dict, rows: list, start: int, most: int) -> dict:
    """head 에 줄을 start 부터 most 줄 싣는다 — 답이 OUT_BYTES 를 넘으면 줄을 던다. 남으면 「다음」 을 단다. count 는 다 센 수다."""
    start, most = max(0, start), max(1, most)
    while True:
        out = {**head, "count": len(rows), "from": start, "rows": rows[start:start + most]}
        if start + most < len(rows):
            out["more"] = f"다음: --from {start + most} 로 이어 본다"
        if most <= 1 or size(out) <= OUT_BYTES:
            return out
        most -= max(1, most // 8)


# ── 본문 글자 ────────────────────────────────────────────────────────────
def reader():
    """형제 스킬 company-mail 의 ``visible`` — 본문 HTML 을 글자로 푸는 한 손. 사람 눈에 안 보이는 글(숨긴 요소 · 바탕색 글 · 스크립트 ·
    머리 · 폭 없는 문자)을 걷고 표를 한 행 한 줄로 낸다. 푸는 법과 줄의 꼴은 그 손의 머리말(「표 꼴의 줄」)이 든다."""
    return load("visible", MAIL_SCRIPTS)


def plain(fragment: str | None, numbered: bool = True) -> str:
    """앱의 HTML 조각 → 읽을 글자. ``numbered`` 가 거짓이면(바뀐 자리의 전 · 후) 그림이 번호 없는 [그림] 이다 — 거기 번호를 달면
    본문 그림의 번호로 읽힌다."""
    return reader().body(fragment, numbered=numbered).text


def save_images(app, idx: int, srcs: list[str]) -> list[dict]:
    """본문 그림을 형제 스킬 company-mail 의 ``body_images`` 로 받는다 — 묻는 것은 앱 손(``cbsop.App.image``)이 가린다."""
    images = load("body_images", MAIL_SCRIPTS)
    cbsop = sys.modules["cbsop"]

    def fetch(src: str) -> bytes:
        try:
            return app.image(src)
        except (cbsop.SessionExpired, cbsop.SessionMissing):
            raise                          # 끊긴 세션은 명령 전체가 다시 세운다
        except cbsop.AppError as exc:      # 잰 꼴 밖 · 거절 · 못 닿음 — 그 그림만 안 받는다
            raise images.Refused(str(exc)) from exc

    return images.save(srcs, fetch, pathlib.Path(tempfile.gettempdir()) / IMAGES_ROOT / str(idx))


def clip(text: str, most: int) -> str:
    return text if len(text) <= most else f"{text[:most]} …(잘림 · 전체 {len(text)} 자)"


def changes_of(got: dict, room: int, words: list | None = None) -> tuple[list, int, int]:
    """최근 개정의 바뀐 자리 — (room 바이트 안에 드는 데까지, 못 실은 건수, 걸린 건수). ``words`` 를 주면 까닭 · 전 · 후 어디에 그 낱말
    (하나라도 · ``squash`` 로 견준다)이 든 자리만 센다 — 덜어 내기 전에 거른다. 첫 건은 늘 싣는다."""
    keys = [k for k in (squash(w) for w in words or []) if k]
    out, used, left, hit = [], 0, 0, 0
    for c in got.get("searchTobe") or []:
        before, after = plain(c.get("oldContent"), False), plain(c.get("toContent"), False)
        if keys and not any(k in squash(f"{c.get('note') or ''}|{before}|{after}") for k in keys):
            continue
        hit += 1
        one = {"why": c.get("note"), "before": clip(before, CHANGE_SIDE), "after": clip(after, CHANGE_SIDE)}
        if c.get("tobeGubunNm"):                         # 판마다의 전후대비표는 구분(변경 · 신설 · 삭제)을 든다
            one["kind"] = c["tobeGubunNm"]
        if left or (out and used + size(one) > room):
            left += 1
            continue
        used += size(one)
        out.append(one)
    return out, left, hit


def with_changes(out: dict, got: dict, room: int, words: list | None = None) -> None:
    changes, left, hit = changes_of(got, room, words)
    if words:
        out.update(grep=words, count=hit)
        if not hit:
            out["next"] = "다음: 낱말을 짧게 바꿔 다시 찾거나, --changes 만으로 바뀐 자리를 다 본다"
    if changes:
        out["changes"] = changes
    if left:
        out["changes_more"] = f"바뀐 자리 {left} 건은 못 실었다 — 사규 화면에서 본다"


def fit_text(out: dict, body: str, start: int, most: int) -> None:
    """본문을 start 부터 most 자까지 ``text`` 칸에 싣되 답이 OUT_BYTES 를 안 넘게 끝을 당긴다 — 남으면 ``more`` 가 다음 자리를
    든다. 줄 끝에서 끊는 법은 ``ep_command.fit_text`` 가 든다."""
    ep_command.fit_text(out, "text", body, start, most, lambda end: f"다음: --from {end} 로 이어 읽는다", OUT_BYTES)


def lines_of(body: str) -> list[tuple[int, str]]:
    """본문의 빈 줄 아닌 줄마다 (그 줄이 시작하는 글자 자리, 줄)."""
    out, at = [], 0
    for line in body.split("\n"):
        if line:
            out.append((at, line))
        at += len(line) + 1
    return out


def grep(head: dict, body: str, words: list, start: int) -> dict:
    """본문에서 낱말(하나라도)이 든 줄을 앞뒤의 짧은 줄과 함께 대목으로 묶어 낸다 — start 자리부터 찾고, 답이 OUT_BYTES 를
    넘으면 남은 대목의 자리를 ``more`` 로 댄다. 표의 행이 걸리면 그 표의 첫 행을 대목 머리에 붙인다."""
    keys = [k for k in (squash(w) for w in words) if k]
    lines = lines_of(body)
    table_sep = reader().TABLE_SEP                      # 표의 행인가는 본문을 푼 손이 칸을 가른 그 글자로 가린다
    hits = [i for i, (at, line) in enumerate(lines) if at >= start and any(k in squash(line) for k in keys)]
    spans: list[list] = []                               # [첫 줄, 끝 줄, 표의 첫 행(없으면 None), 걸린 첫 줄]
    for i in hits:
        first, last, top = i, i, None
        room = GREP_AROUND_CHARS
        while first > 0 and i - first < GREP_AROUND and len(lines[first - 1][1]) <= room:
            first -= 1
            room -= len(lines[first][1])
        room = GREP_AROUND_CHARS
        while last < len(lines) - 1 and last - i < GREP_AROUND and len(lines[last + 1][1]) <= room:
            last += 1
            room -= len(lines[last][1])
        if table_sep in lines[i][1]:
            top = i
            while top > 0 and table_sep in lines[top - 1][1]:
                top -= 1
            top = top if top < first else None
        if spans and first <= spans[-1][1] + 1:
            spans[-1][1] = last
        else:
            spans.append([first, last, top, i])
    out = {**head, "grep": words, "count": len(hits), "hits": []}
    for first, last, top, hit in spans:
        text = "\n".join(line for _, line in lines[first:last + 1])
        out["hits"].append({"at": lines[first][0], "text": text if top is None else f"{lines[top][1]}\n…\n{text}"})
        if len(out["hits"]) > 1 and size(out) > OUT_BYTES:
            out["hits"].pop()
            out["more"] = f"다음: --grep {' '.join(words)} --from {lines[hit][0]} 로 남은 대목을 본다"
            break
    if not hits:
        out["next"] = "다음: 낱말을 짧게 바꿔 다시 찾거나, --from 0 부터 more 를 따라 본문을 읽는다"
    return out


# ── 명령 ────────────────────────────────────────────────────────────────
def wants_fresh(args) -> bool:
    """최근 시행을 묻는 판인가 — 받아 둔 뒤에 시행된 것을 놓치지 않게 RECENT_FRESH_DAYS 안의 목록만 쓴다."""
    return args.command in FRESH_ONLY or (args.command == "find" and args.days is not None)


def usable_index(args) -> dict | None:
    """이 명령이 그대로 쓸 받아 둔 목록 — refresh 는 늘 없고, 최근 시행을 묻는 판(``wants_fresh``)은 RECENT_FRESH_DAYS 안에 받은 것만."""
    got = None if args.command == "refresh" else cached_index()
    if got is not None and wants_fresh(args) and time.time() - got["stamp"] >= RECENT_FRESH_DAYS * DAY_SECONDS:
        return None
    return got


def find_refusal(args) -> str:
    """find 가 거르기를 하나도 안 받았으면 그 까닭 — 서면 빈 글자. 목록을 새로 받기 전에 가린다."""
    if any(squash(w) for w in args.words) or squash(args.inside) or args.days is not None or args.abolished:
        return ""
    return "find 는 말 · --in · --days · --abolished 가운데 하나는 받는다 — 다음: 구조는 tree, 최근 시행은 recent 로 본다"


def pool(index: dict, args) -> list:
    """find · recent 가 거르는 줄 — --abolished 면 폐지 문서, 아니면 공개된 문서."""
    return index["gone"] if args.abolished else index["rows"]


def find(head: dict, rows: list, args, gone: list | None = None) -> dict:
    """받아 둔 목록을 말 × 범주(어느 깊이든) × 기간으로 거른다. 기간을 주면 새 시행일부터, 아니면 제목에 말이 다 든 것부터 경로 · 이름
    차례. 0 건이면 ``next`` 가 무엇을 찾았고 무엇을 풀어 볼지를 든다."""
    keys = [k for k in (squash(w) for w in args.words) if k]
    if args.days is not None:
        head = {**head, "since": since_of(args.days)}
    hit = matched(rows, args, keys, head.get("since"))
    if args.days is not None:
        hit.sort(key=lambda r: r["enforcementDate"] or "", reverse=True)
    else:
        hit.sort(key=lambda r: (not all(k in squash(r["processName"]) for k in keys), r["path"], r["processName"]))
    out = page(head, hit, args.start, args.most)
    if not hit:
        out["next"] = find_hint(rows, args, keys, head.get("since"))
        if gone:                                         # 공개된 문서에 없으면 — 폐지된 문서에 같은 거르기가 걸리나
            left = len(matched(gone, args, keys, head.get("since")))
            if left:
                out["next"] += f" · 같은 조건에 폐지된 문서 {left} 건이 걸린다 — --abolished 로 본다"
    return out


def matched(rows: list, args, keys: list, since: str | None) -> list:
    """find 의 거르기 — 범주(어느 깊이든) × 시행일 since 부터 × 말이 다 든 줄. 차례는 부르는 쪽이 정한다."""
    scoped = under_category(rows, args.inside)
    if since is not None:
        scoped = [r for r in scoped if (r["enforcementDate"] or "") >= since]
    return [r for r in scoped if all(k in squash("|".join(str(r.get(c) or "") for c in FIND_KEYS)) for k in keys)]


def find_hint(rows: list, args, keys: list, since: str | None) -> str:
    """0 건인 find · recent 의 ``next`` — 무엇으로 찾았나와, 거르기마다 풀어 볼 길. recent 는 말이 없다(``keys`` 가 빈다)."""
    searched, tries = [], []
    if keys:
        searched.append(f"말 「{' '.join(args.words)}」(표준명 · 경로 · 담당 · 부서)")
    if squash(args.inside):
        searched.append(f"범주 「{args.inside}」 아래(어느 깊이든)")
        tries.append("--in 을 빼고 모든 범주에서 찾는다" if under_category(rows, args.inside)
                     else f"범주 「{args.inside}」 에 걸리는 칸이 목록에 없다 — tree 로 범주 이름을 보고 고친다")
    if since:
        searched.append(f"시행일 {since} 이후")
        tries.append("--days 를 늘리거나 빼고 찾는다" if args.command == "find" else "--days 를 늘려 찾는다")
    if keys:
        tries.append("말을 짧게 · 다른 말로 바꾼다(「해외 출장 숙박비」 → 「출장」) · 그래도 없으면 search <말> --body 로 앱이 본문까지 찾는다")
    return f"0 건 — 받아 둔 목록에서 찾은 조건: {' × '.join(searched)}. 다음: {' · '.join(tries)}"


def need_index(app, args) -> tuple[dict, bool, str]:
    """(목록, 방금 받았나, 받은 목록을 PC 에 못 남긴 까닭) — 못 남겨도 받은 목록으로 답한다. 다음 판이 다시 받을 뿐이다."""
    got = usable_index(args)
    if got is not None:
        return got, False, ""
    fresh = build_index(app)
    return fresh, True, ep_command.keep(index_path(), fresh)


def view_refusal(args) -> str:
    """read 의 보기 칸이 함께 설 수 없으면 그 까닭 — 서면 빈 글자. 안 먹는 칸을 말없이 버리면 물음에 걸린 자리가 빠진 답이 「됐다」로 나간다.
    --grep 은 본문에서도(--from 은 찾기 시작 자리) 바뀐 자리에서도(--changes) 거른다. --from · --max 는 본문 글자의 자리라 본문을 읽는 판에만 든다."""
    alone = [f for f, on in (("--history", args.history), ("--contacts", args.contacts)) if on]
    if alone and (len(alone) > 1 or args.rev is not None or args.trail or args.images or args.grep or args.changes
                  or args.start is not None or args.max is not None):
        return f"{alone[0]} 는 혼자만 든다 — 다음: 따로 부른다"
    if args.trail and (args.images or args.grep or args.changes or args.start is not None or args.max is not None):
        return "--trail 은 --rev 하고만 함께 든다 — 다음: 따로 부른다"
    if args.rev is not None and args.images:
        return "--images 는 지금 판의 그림만 받는다 — 지난 판의 그림은 사규 화면의 개정이력에서 본다"
    if args.images and (args.grep or args.changes or args.start is not None or args.max is not None):
        return "--images 는 --grep · --changes · --from · --max 와 함께 못 쓴다 — 다음: 그림과 글자를 따로 부른다"
    if args.changes and (args.start is not None or args.max is not None):
        return "--changes 는 --from · --max 와 함께 못 쓴다 — 바뀐 자리는 본문의 글자 자리가 아니다. 다음: 따로 부른다(낱말로 거르려면 --grep)"
    if args.grep and args.max is not None:
        return "--grep 은 --max 와 함께 못 쓴다 — 대목은 답의 크기까지 다 온다. 다음: --max 를 빼고 부른다"
    return ""


def refusal(args) -> str:
    """함께 못 서는 인자의 까닭 — 서면 빈 글자. 세션도 목록 받기도 부르기 전에 main 이 종료 2 로 멈춘다."""
    if args.command == "find":
        return find_refusal(args)
    if args.command == "read":
        return view_refusal(args)
    if args.command == "search":
        return search_refusal(args)
    return ""


def search_refusal(args) -> str:
    """search 의 칸이 함께 설 수 없으면 그 까닭 — 내 목록(--used · --access)은 말 · 찾는 칸을 안 받고, 찾기는 말을 받는다."""
    lists = [f for f, on in (("--used", args.used is not None), ("--access", bool(args.access))) if on]
    if lists:
        if len(lists) > 1 or args.words or args.body or args.owner or args.files or args.inside:
            return f"{lists[0]} 는 말 · --body · --owner · --files · --in 과 함께 못 쓴다 — 내 목록은 화면의 표 그대로다. 다음: 따로 부른다"
        return ""
    if not any(squash(w) for w in args.words):
        return "search 는 말을 받는다 — 다음: search <말>, 내 목록은 --used · --access <등급>"
    return ""


def opened(app, idx: int) -> tuple[dict, dict]:
    """(앱의 답, 그 문서의 메타) — 사람의 화면이 그 문서를 열 때만. 앱의 JSON 길은 화면이 막는 등급 문서의 본문도 내주므로(``references/SOURCES.md``
    「등급 문서」), 등급이 「일반」이 아니거나 등급을 못 읽은 문서는 화면의 문서 창에 먼저 묻고(``cbsop.App.screen_allows``) 막으면
    본문 · 바뀐 자리 · 지난 판 · 첨부를 하나도 안 내고 멈춘다. 본문 글자를 내는 손가락은 다 이 길로 문서를 연다."""
    got = app.info(idx)
    info = (got.get("ProcessInfo") or [None])[0]
    if not info:
        raise Stop(EXIT_ARGS, "args", f"문서 {idx} 가 없다 — 다음: find · search 로 processIdx 를 찾는다")
    grade = info.get("securityGradeName")
    if grade != ep_command.load("cbsop", HERE).OPEN_GRADE and not app.screen_allows(idx):
        raise Stop(EXIT_ARGS, "denied", f"「{info.get('processName')}」({grade or '등급 모름'})은 쓰는 사람의 사규 화면에서 권한이 없어 열리지 "
                                        "않는다 — 본문 · 바뀐 자리 · 지난 판 · 첨부를 안 낸다. 다음: 사람에게 그렇다고 말하고, 사규 화면에서 그 문서를 "
                                        "열어 [권한신청]을 하시도록 권한다(이름 · 경로는 find 의 줄로 대 준다)")
    return got, info


def revision(app, idx: int, rev: str) -> dict:
    """개정이력의 한 판 — 판 이름(「13」 · 「폐지」)이 꼭 같은 줄. 없으면 있는 판을 대며 종료 2."""
    hist = app.history(idx)
    for one in hist:
        if str(one.get("version")) == rev:
            return one
    raise Stop(EXIT_ARGS, "args", f"문서 {idx} 에 판 「{rev}」 이 없다 — 있는 판: {' · '.join(str(h.get('version')) for h in hist) or '없음'}. "
                                  "다음: read <번호> --history 로 판을 본다")


def history_rows(hist: list) -> list:
    """화면 「개정이력」 의 줄 — 새 판부터. summary 는 주요 개정 내용(없으면 개정 내용)이다."""
    return [{"rev": h.get("version"), "enforced": h.get("enforcementDate"), "summary": h.get("mainContent") or h.get("revisedContent"),
             "hname": h.get("hname"), "by": h.get("reHname")} for h in hist]


def trail_rows(rows: list) -> list:
    """한 개정의 결재 경과 — 걸음마다 때 · 걸음 · 올린 사람 · 받은 사람 · 의견."""
    return [{"at": t.get("apRegDate"), "step": t.get("codeName"), "from": t.get("reHname"), "to": t.get("apHname"),
             "opinion": t.get("opinion") or None} for t in rows]


def card(role: str, got: dict | None, name: str | None) -> dict:
    """화면에서 이름을 누르면 뜨는 사람 창 — 퇴사자는 창이 비어 이름만 낸다."""
    if not got:
        return {"role": role, "name": name, "note": "사람 창이 비었다(퇴사자 · 사번 없음)"}
    return {"role": role, "name": got.get("hname"), "dept": got.get("deptcdDisp"), "grade": got.get("jikwicdDisp"),
            "title": got.get("jikckcdDisp"), "duty": got.get("responsibility"), "office": got.get("officePhone"),
            "mobile": got.get("handpon"), "email": got.get("email")}


def read(app, args) -> dict:
    got, info = opened(app, args.idx)                    # 화면이 막는 등급 문서면 여기서 멈춘다 — 아래 보기는 다 그 뒤다
    head = {"processIdx": info.get("processIdx"), "name": info.get("processName")}
    if args.history:
        return {**head, "rev": info.get("version"), "security": info.get("securityGradeName"), "history": history_rows(app.history(args.idx)),
                "next": "다음: 지난 판 본문은 --rev <판>, 그 개정의 전후대비는 --rev <판> --changes, 결재 경과는 --rev <판> --trail"}
    if args.contacts:
        people = (("담당", "empcd", "hname"), ("검토", "reviewerCd", "reviewer"), ("승인", "approvalCd", "approval"))
        return {**head, "contacts": [card(role, app.person(info[code]) if info.get(code) else None, info.get(name))
                                     for role, code, name in people if info.get(code) or info.get(name)]}
    one = revision(app, args.idx, args.rev) if args.rev is not None else None
    if args.trail:
        work = one.get("workIdx") if one else info.get("workIdx")
        out = {**head, "rev": one.get("version") if one else info.get("version"), "trail": trail_rows(app.trail(work)) if work else []}
        if not out["trail"]:
            out["note"] = "이 판에는 결재 경과가 없다(첫 판 · 옮겨 온 판은 비어 온다)"
        return out
    src = info
    if one is not None:                                  # 지난 판 — 본문 · 바뀐 자리를 그 판의 것으로 바꿔 아래 보기를 그대로 건다
        if args.changes:
            got = {"searchTobe": app.tobe(one["workIdx"]) if one.get("workIdx") else []}
        else:
            src = (app.past(one["processHisIdx"]).get("ProcessHisInfo") or [None])[0] or {}
    page_ = None if args.changes and one is not None else reader().body(src.get("content"))
    body = page_.text if page_ else ""
    brief = {**head, "rev": one.get("version") if one else info.get("version"),
             "enforced": one.get("enforcementDate") if one else info.get("enforcementDate"),
             "security": info.get("securityGradeName")}
    if page_:
        brief["length"] = len(body)
    if one is not None:
        brief["current_rev"] = info.get("version")
    if page_ and page_.images:
        brief["images_count"] = len(page_.images)
    if page_ and page_.hidden:
        brief["hidden"] = page_.hidden
    most = READ_MAX if args.max is None else max(1, args.max)
    if args.images:
        out = dict(brief)
        out["images"] = save_images(app, args.idx, list(page_.images)) if page_.images else []
        return out
    if args.changes:                                     # --grep 을 주면 그 낱말이 든 바뀐 자리만
        out = dict(brief)
        with_changes(out, got, OUT_BYTES - size(brief) - 1000, args.grep)
        if one is not None and not got["searchTobe"]:
            out["note"] = "이 판에는 전후대비표가 없다(첫 판 · 옮겨 온 판은 비어 온다)"
        return out
    if args.grep:
        return grep(brief, body, args.grep, max(0, args.start or 0))
    if args.start is not None or one is not None:        # 본문을 짚은 자리부터 · 지난 판 — 지금 판의 메타는 되풀이하지 않는다
        out = {**brief, "from": max(0, args.start or 0)}
        fit_text(out, body, out["from"], most)
        return out
    out = {**brief, "path": info.get("processPath"), "next_review": info.get("examineDate"),
           "hname": info.get("hname"), "deptnm": info.get("deptnm"), "reviewer": info.get("reviewer"),
           "approver": info.get("approval"), "last_change": info.get("mainContent")}
    if info.get("txtIdx"):
        out["number"] = info["txtIdx"]
    if info.get("fromDate") or info.get("toDate"):       # 인증서 — 화면은 시행일 자리에 유효기간을 적는다
        out["valid"] = f"{info.get('fromDate') or ''} ~ {info.get('toDate') or ''}"
    related = [{"processIdx": r.get("processIdx"), "name": r.get("processName"), "menu": r.get("menuName"), "deptnm": r.get("reDeptnm")}
               for r in app.related(args.idx) if isinstance(r, dict)]
    if related:
        out["related"] = related
    files = [f.get("fileName") or f.get("orgFileName") for f in got.get("searchProcessFileList") or [] if isinstance(f, dict)]
    if files:
        out["files"] = files
    if len(body) > READ_FIRST:
        changed = len(got.get("searchTobe") or [])
        if changed:
            out["changes_count"] = changed
        out["next"] = NEXT_READ + (" · 바뀐 자리는 --changes" if changed else "")
    else:
        with_changes(out, got, CHANGES_BYTES)
    out["from"] = 0
    fit_text(out, body, 0, min(most, READ_FIRST))
    return out


def run(args, session: pathlib.Path | None) -> dict:
    """session 이 None 이면 받아 둔 목록만으로 답하는 판이다(main 이 가린다)."""
    app = None if session is None else load("cbsop", HERE).App(session)
    if args.command in INDEX_ONLY + ("refresh",):
        index, fresh, unkept = need_index(app, args)
        head = {"index_at": stamp_word(index), "fresh": fresh, "total": len(index["rows"])}
        if args.command != "tree" and getattr(args, "abolished", False):
            head["abolished"] = len(index["gone"])        # 거른 것이 폐지 문서다 — total 은 공개된 문서의 수 그대로
        if unkept:
            head["index_note"] = f"받은 목록을 PC 에 못 남겼다({unkept}) — 다음 판도 목록을 새로 받는다(1 분 남짓)"
        if args.command == "refresh":
            return {**head, "menus": index["menus"], "abolished": len(index["gone"])}
        if args.command == "find":
            return find(head, pool(index, args), args, None if args.abolished else index["gone"])
        if args.command == "tree":
            rows = index["rows"]
            hit, depth = under_path(rows, args.inside)
            if not hit:
                raise Stop(EXIT_ARGS, "args", f"「{' '.join(args.inside)}」에 걸리는 칸이 없다 — 다음: 경로 없이 tree 로 범주 이름을 본다")
            tree: dict = {}
            leaf = []
            for r in hit:
                parts = r["path"].split(PATH_SEP)[depth:]
                if not parts:
                    leaf.append(r)
                    continue
                node = tree
                for p in parts:
                    node = node.setdefault(p, {"count": 0, "under": {}})
                    node["count"] += 1
                    node = node["under"]
            out = {**head, "paths": sorted({r["path"] for r in hit})[:MOST_FIND]} if depth else {**head}
            if tree:
                out["tree"] = tree
            if leaf:                                       # 경로가 맨 아래 칸에 닿았다 — 그 칸의 문서를 넘겨 본다
                leaf.sort(key=lambda r: r["processName"])
                return page(out, leaf, args.start, args.most)
            return out
        since = since_of(args.days)
        rows = under_category(pool(index, args), args.inside)
        hit = sorted((r for r in rows if (r["enforcementDate"] or "") >= since), key=lambda r: r["enforcementDate"], reverse=True)
        out = page({**head, "since": since}, hit, args.start, args.most)
        if not hit:
            out["next"] = find_hint(pool(index, args), args, [], since)
        return out
    if args.command == "search":
        if args.used is not None or args.access:
            return mine(app, args)
        fields = (["subject"] + (["content"] if args.body else []) + (["user_name", "team_name"] if args.owner else [])
                  + (["file_name"] if args.files else []))
        menu = top_menu(app, args.inside) if args.inside else None
        got = app.search(" ".join(args.words), ",".join(fields), menu["menuIdx"] if menu else "")
        hits = []
        for key, value in sorted(got.items()):
            if key.startswith(SEARCH_HIT_PREFIX) and isinstance(value, list):
                for x in value:
                    hits.append({"processIdx": x.get("processIdx"), "processName": x.get("processName"),
                                 "path": x.get("processPath"), "enforcementDate": x.get("enforcementDate"),
                                 "hname": x.get("hname"), "deptnm": x.get("deptnm")})
        out = page({"fields": fields, **({"in": menu["menuName"]} if menu else {})}, hits, args.start, args.most)
        out["count"] = got.get("searchListCnt", len(hits))
        return out
    return read(app, args)


def top_menu(app, word: str) -> dict:
    """search --in 의 범주 — 앱의 통합 검색은 맨 위 범주 하나(menuId)로만 좁힌다. 말이 꼭 한 범주 이름에 들어야 선다."""
    menus = [m for m in app.menus() if m.get("openYn", "Y") == "Y"]
    hit = [m for m in menus if squash(word) in squash(m.get("menuName"))]
    if len(hit) != 1:
        raise Stop(EXIT_ARGS, "args", f"search --in 「{word}」 이 맨 위 범주 하나에 안 선다({len(hit)} 곳) — 앱 검색은 맨 위 범주로만 좁힌다: "
                                      f"{' · '.join(m['menuName'] for m in menus)}. 깊은 범주는 find --in 으로 본다")
    return hit[0]


def grade_of(grades: dict, word: str) -> str:
    """--access 의 등급 이름 → 앱의 등급 코드. 표에 없는 이름이면 Stop(인자) — 표는 앱 손의 것이라 세션 없이 가린다(main 이 먼저 부른다)."""
    code = next((v for k, v in grades.items() if squash(k) == squash(word)), None)
    if code is None:
        raise Stop(EXIT_ARGS, "args", f"등급 「{word}」 이 없다 — 다음: {' · '.join(grades)} 가운데 하나")
    return code


def mine(app, args) -> dict:
    """내 목록 — 화면 「최근 사용 표준」(--used) · 「접근 가능한 표준」(--access 등급)."""
    def line(x: dict) -> dict:
        out = {"processIdx": x.get("processIdx"), "processName": x.get("processName"),
               "path": PATH_SEP.join(x.get(k) for k in ("menuName1", "menuName2", "menuName3") if x.get(k)),
               "hname": x.get("hname"), "deptnm": x.get("reDeptnm") or x.get("deptnm")}
        for key, raw in (("number", "txtIdx"), ("enforcementDate", "enforcementDate"), ("enforcementDate", "reRegDate"),
                         ("security", "securityGradeN"), ("state", "stateNm")):
            if x.get(raw) and key not in out:            # 최근 사용 줄은 시행일을 reRegDate 에 든다(SOURCES.md) · 등급 이름은 securityGradeN
                out[key] = x[raw]
        return out

    if args.access:
        rows = [line(x) for x in app.access(grade_of(app.GRADES, args.access))]
        rows.sort(key=lambda r: (r["path"], r["processName"] or ""))
        return page({"access": args.access, "range": "읽기"}, rows, args.start, args.most)
    until = date.today()
    since = until - timedelta(days=max(0, args.used))
    rows = [line(x) for x in app.used(since.strftime(APP_DATE), until.strftime(APP_DATE))]   # 앱의 차례 그대로 — 줄은 연 날을 안 든다
    return page({"used_since": since.strftime(APP_DATE)}, rows, args.start, args.most)


NOT_HERE = ("개정 · 폐지 · 신규 제정 · 인계인수 · 이슈 등록 · 검토 · 승인 · 윤독 완료 · 첨부 받기 · 본문 PDF 받기 · 화면 조작 — 손에 없다. 사람에게 사규 화면에서 하도록 "
            "권하고 찾은 문서의 이름 · 경로를 대 준다. 앱에 아무것도 쓰지 않는다(열람 기록도 안 남긴다)")
# 이 명령이 내는 종료 값 — 뜻은 ep_command 의 한 표, 여기는 이 손이 덧붙일 말만
EXITS = ep_command.exit_legend((ep_command.EXIT_OK, ep_command.EXIT_TOOL, EXIT_ARGS, ep_command.EXIT_SESSION),
                               {EXIT_ARGS: "함께 못 서는 인자 · 없는 등급(세션 전에 멈춘다) · 문서가 없다 · 쓰는 사람의 화면이 그 문서를 막는다(error 가 "
                                           "denied — 본문은 안 왔다. 사규 화면의 [권한신청]을 권한다)"})


def reads() -> dict:
    """명령마다 (한 줄 — 맨 위 --help 의 지도와 명령 목록, 그 명령의 --help 에 덧붙는 설명 · 답의 칸). --help 는 이 표와 argparse 에서만 선다."""
    images = ep_command.load("body_images", MAIL_SCRIPTS).MAX_IMAGES   # 그림 수의 위는 받는 손의 값 그대로 — 손을 대역으로 바꾼 판에도 도움말은 선다
    rows = "답: index_at(목록을 받은 때) · fresh(이 판에 새로 받았나) · total(목록 전체 건수) · count(걸린 건수) · from · rows(줄마다 processIdx · " \
           "processName · enforcementDate · hname(담당) · deptnm(부서) · version · path · 있으면 number(표준번호) · valid_to(인증서 유효기간 끝)) · " \
           "more(다음 --from)"
    return {
        "find": ("받아 둔 목록에서 찾기 — 말 × 범주(어느 깊이든) × 기간을 아무 조합으로 한 부름에(하나는 준다)",
                 "말은 표준명 · 경로 · 담당 · 부서 · 표준번호에 다 든 것이다 — 사람의 말에서 제목에 들 낱말을 짧게 뽑는다(「해외 출장 숙박비」 → 출장). "
                 "「요즘 바뀐 출장 규정」 은 find 출장 --days 90 한 번이다. 안 나오면 search <말> --body\n\n"
                 f"{rows}. --days 를 주면 since 를 들고 새 시행일부터, 0 건이면 next 가 찾은 조건과 풀어 볼 길을 든다(같은 조건에 폐지된 문서가 걸리면 그 수도). "
                 "「폐지된 ○○ 지침」 은 find ○○ --abolished — 그 답은 abolished(받아 둔 폐지 문서 수)를 든다"),
        "tree": ("받아 둔 목록의 구조와 건수 — 경로를 주면 그 아래, 맨 아래 칸에 닿으면 그 칸의 문서",
                 "경로 없이 부르면 맨 위 범주부터 나무와 건수가 온다. 칸을 골라 「기초 > 작업표준」 → 「기초 > 작업표준 > 포항화성」 처럼 내려간다\n\n"
                 f"답: index_at · fresh · total · paths(걸린 경로 — {MOST_FIND} 개까지) · tree(칸마다 count · under). 맨 아래 칸이면 그 칸의 문서를 "
                 "이름순으로 rows · count · from · more 로 낸다. 걸리는 칸이 없으면 종료 2"),
        "recent": ("받아 둔 목록에서 시행일이 최근 N 일 안인 것 — 새 시행일부터(말로 거르려면 find --days)",
                   f"늘 받은 지 {RECENT_FRESH_DAYS} 일 안의 목록을 쓴다 — 낡았으면 먼저 새로 받는다. 「요즘 폐지된 것」 은 recent --abolished(날은 폐지 시행일)\n\n"
                   f"{rows} · since. 0 건이면 next"),
        "search": ("앱에 묻는 찾기 — 기본은 표준명, --body 본문 · --owner 담당자 · 부서 · --files 첨부 이름까지, --in 맨 위 범주로. 내 목록은 --used · --access",
                   "흔한 낱말의 본문 찾기는 17 초쯤 걸린다 — 뜻이 좁은 낱말을 고른다. 찾는 칸 · 범주는 한 부름에 아무 조합으로 건다\n\n"
                   "내 목록 — 말 없이 부른다. --used [N] 은 화면 「최근 사용 표준」(내가 사규 화면에서 연 문서 · 이 손의 read 는 안 남는다), "
                   "기간은 연 날로 거르지만 줄은 연 날을 안 든다(앱의 차례 그대로) — "
                   "--access <등급> 은 화면 「접근 가능한 표준」 의 그 등급(읽기). 등급을 안 고른 「전체」 는 앱이 1 분 가까이 걸려 안 받는다 — "
                   "등급을 하나씩 부른다(수 초)\n\n"
                   "답: fields(찾은 칸) · in(좁힌 범주) · count(앱이 센 수) · from · rows(줄마다 processIdx · processName · path · enforcementDate · hname · "
                   "deptnm) · more. 내 목록의 줄은 processIdx · processName · path · hname · deptnm · 있으면 number · enforcementDate · "
                   "security · state, 머리는 used_since 나 access"),
        "read": ("문서 한 건 — 물음만큼만: 낱말이면 --grep, 바뀐 것이면 --changes, 그림이면 --images, 지난 판이면 --history · --rev, 사람이면 --contacts",
                 f"낱말 없이 부르면 메타(판 · 시행일 · 다음 검토일 · 담당 · 검토 · 승인 · 보안등급)와 본문 앞 {READ_FIRST} 자가 온다 — 본문이 그 안이면 "
                 "통째로 오고 바뀐 자리(changes)도 함께 온다. 넘으면 more 가 다음 --from 을, next 가 읽는 길을 든다. 목차는 안 낸다(제목 줄의 꼴이 "
                 "문서마다 달라 틀린 조를 가리킨다)\n\n"
                 "함께 서는 짝 — --grep 은 본문에서도(--from 은 찾기 시작 자리) 바뀐 자리에서도(--changes) 거른다. --from · --max 는 본문을 읽는 판에만, "
                 "--images 는 혼자만 든다. 안 서는 짝은 세션 전에 종료 2 다\n\n"
                 "개정이력 — --history 가 판마다 rev · enforced · summary · hname · by 를 낸다. --rev <판> 은 그 지난 판을 지금 판처럼 읽는다(본문 · "
                 "--grep · --from · --max) — 답은 rev · current_rev(지금 판) · text. --rev <판> --changes 는 그 개정의 전후대비표(changes 의 줄마다 "
                 "kind 가 변경 · 신설 · 삭제), --trail 은 그 개정의 결재 경과(trail — at · step · from · to · opinion). --history · --contacts 는 혼자만 든다\n\n"
                 "사람 — --contacts 가 담당 · 검토 · 승인의 사람 창(contacts — role · name · dept · grade · title · duty · office · mobile · email)을 낸다. "
                 "메일을 보내려면 company-mail 의 who --name <name> 으로 받는 사람 파일을 짓는다\n\n"
                 "등급 문서 — 「일반」 이 아닌 문서는 쓰는 사람의 사규 화면이 여는지 먼저 묻는다. 막으면 어느 보기든 본문 없이 종료 2(error: denied)\n\n"
                 "답: processIdx · name · rev · enforced · security · length(본문 글자 수) · path · next_review · hname · deptnm(받는 사람 찾기 — "
                 "company-mail 의 who --name <hname>, 동명이인이면 deptnm 으로 고른다) · reviewer · approver · last_change · related(화면 「관련표준」 — 줄마다 processIdx · name · menu · deptnm) · files · "
                 "number(표준번호) · valid(인증서의 유효기간 — 시작 ~ 끝) · text · from · more · next. --grep 은 hits(대목마다 at — 그 자리부터 --from 으로 둘레를 더 읽는다 · text) · count, --changes 는 "
                 "changes(why · before · after) · changes_more, 긴 문서의 첫 답은 changes_count. 본문은 글자만이다 — 표는 한 행 한 줄 · 칸 사이 「 | 」 · 합친 칸은 자리마다 같은 "
                 "글자, 그림은 「[그림 N]」(images_count 가 그 수). 사람 눈에 안 보이게 감춘 글은 걷히고 그 덩이 수가 hidden 이다 — 찾는 대목이 "
                 f"안 나오는데 hidden 이 서면 「규정에 없다」고 하지 않는다. --images 는 앞 {images} 장까지 받아 images(no · path · 안 받은 그림은 "
                 "skipped)를 낸다"),
        "refresh": ("목록을 지금 다시 받는다 — 1 분 넘게 걸린다. 「방금 올라온 것」이 안 나올 때만",
                    "답: index_at · fresh · total · menus(받은 맨 위 범주) · abolished(함께 받은 폐지 문서 수)"),
    }


def top_map(table: dict) -> str:
    """맨 위 --help 의 지도 — reads · NOT_HERE · EXITS 에서 짓는다."""
    out = [f"받아 둔 목록 — find · tree · recent 는 홈에 받아 둔 문서 목록으로 답하고 앱을 안 부른다. 받은 지 {INDEX_DAYS} 일이 지났거나 "
           f"recent · --days 를 준 find 에 {RECENT_FRESH_DAYS} 일이 지났으면 먼저 새로 받는다 — 그 판은 1 분 넘게 걸리니 시한을 3 분으로 준다",
           "찾기"]
    out += [f"  {name:8} {table[name][0]}" for name in ("find", "tree", "recent", "search")]
    out.append("읽기")
    out += [f"  {name:8} {table[name][0]}" for name in ("read", "refresh")]
    out.append("\n견주기 — 말 · 범주 · 경로 · 낱말은 빈칸 · 가운뎃점 · 괄호 · 대소문자를 안 본다(「여비관리」 = 「여비 관리」). 범주와 경로는 칸을 「>」 로 "
               "가르고 칸마다 그 깊이 범주 이름의 일부면 된다 — 셸이 「>」 를 파일 쓰기로 읽으니 따옴표로 감싼다")
    out.append(f"답 — 표준 출력의 JSON 하나 · 한 답은 {OUT_BYTES} 바이트를 안 넘는다. 남은 줄 · 본문 · 대목은 more 의 --from 으로 잇는다")
    out.append(f"안 하는 것 — {NOT_HERE}")
    out.append(EXITS)
    out.append("명령마다의 인자와 답의 칸은 <명령> --help")
    return "\n".join(out)


def parser() -> argparse.ArgumentParser:
    raw = argparse.RawDescriptionHelpFormatter
    table = reads()
    p = argparse.ArgumentParser(prog="regulation.py", description="사내 사규관리 앱 — 사규 · 표준 · 지침 · 작업표준 · 검사기준 · 인증서를 찾고 읽는다(읽기만)",
                                epilog=top_map(table), formatter_class=raw)
    sub = p.add_subparsers(dest="command", required=True, metavar="<명령>")

    def command(name: str) -> argparse.ArgumentParser:
        line, more = table[name]
        # help 를 안 준다 — 명령마다의 한 줄은 맨 위 지도(epilog)가 묶음째 내고, 여기서도 주면 같은 줄이 두 번 찍힌다
        return sub.add_parser(name, description=f"{line}\n\n{more}", formatter_class=raw)

    def paged(cmd: argparse.ArgumentParser, most: int) -> None:
        cmd.add_argument("--most", type=int, default=most, metavar="N", help=f"한 답에 싣는 줄 수(기본 {most}) — count 는 다 센 수다")
        cmd.add_argument("--from", dest="start", type=int, default=0, metavar="N", help="N 째 줄부터 — 답의 more 가 댄다(기본 0)")

    abolished = ("공개된 문서 대신 폐지된 문서에서 — 줄의 version 은 「폐지」, path 는 앱이 그 줄에 적은 구분, enforcementDate 는 앱이 그 줄에 적은 날이다. "
                 "폐지 문서는 전체 목록(tree)에 안 든다")
    category = "경로의 어느 깊이든 이 범주 아래 — 「작업표준」 · 「기초 > 작업표준」 · 맨 위 범주(정관 · 전사공통 · 에너지소재 · 기초소재 · 안전 · 인증)"
    f = command("find")
    f.add_argument("words", nargs="*", metavar="말", help="표준명 · 경로 · 담당 · 부서에 다 든 말 — 안 주면 --in · --days 로만 거른다")
    f.add_argument("--in", dest="inside", metavar="범주", help=category)
    f.add_argument("--days", type=int, default=None, metavar="N", help="시행일이 최근 N 일 안인 것만 — 새 시행일부터 낸다")
    f.add_argument("--abolished", action="store_true", help=abolished)
    paged(f, MOST_FIND)
    t = command("tree")
    t.add_argument("inside", nargs="*", metavar="경로", help="「기초 > 작업표준 > 포항화성」 처럼 칸을 > 로 가른다 — 안 주면 맨 위부터")
    paged(t, MOST_FIND)
    r = command("recent")
    r.add_argument("--days", type=int, default=RECENT_DAYS, metavar="N", help=f"시행일이 최근 N 일 안인 것(기본 {RECENT_DAYS})")
    r.add_argument("--in", dest="inside", metavar="범주", help=category)
    r.add_argument("--abolished", action="store_true", help=abolished)
    paged(r, MOST_RECENT)
    s = command("search")
    s.add_argument("words", nargs="*", metavar="말", help="찾을 말 — 여러 낱말은 한 검색어로 이어 묻는다(--used · --access 는 말 없이)")
    s.add_argument("--body", action="store_true", help="본문까지 찾는다 — 흔한 낱말이면 오래 걸린다")
    s.add_argument("--owner", action="store_true", help="담당자 · 부서 이름까지 찾는다")
    s.add_argument("--files", action="store_true", help="첨부 파일 이름까지 찾는다(별지 서식 · 인증서 파일)")
    s.add_argument("--in", dest="inside", metavar="범주", help="맨 위 범주 하나로 좁힌다(정관 · 전사공통 · 에너지소재 · 기초소재 · 안전 · 인증) — "
                   "앱 검색은 그 깊이로만 좁힌다")
    s.add_argument("--used", nargs="?", type=int, const=USED_DAYS, default=None, metavar="N",
                   help=f"내가 사규 화면에서 최근 N 일(기본 {USED_DAYS})에 연 문서 — 화면 「최근 사용 표준」. 이 손의 read 는 안 남는다")
    s.add_argument("--access", metavar="등급", help="내가 읽을 수 있는 그 등급의 문서 — 화면 「접근 가능한 표준」(등급 하나씩 · 수 초). "
                   + " · ".join(ep_command.load("cbsop", HERE).GRADES))
    paged(s, MOST_SEARCH)
    d = command("read")
    d.add_argument("idx", type=int, metavar="processIdx", help="find · tree · recent · search 줄의 processIdx")
    d.add_argument("--from", dest="start", type=int, default=None, metavar="N",
                   help="본문을 N 째 글자부터 — more 가 댄다. --grep 과 함께면 찾기를 시작하는 자리")
    d.add_argument("--max", type=int, default=None, metavar="N", help=f"본문을 읽는 판의 글자 수 위(기본 {READ_MAX})")
    d.add_argument("--grep", nargs="+", metavar="낱말",
                   help=f"그 낱말(하나라도)이 든 대목만 — 걸린 줄과 앞뒤의 짧은 줄 {GREP_AROUND} 줄까지, 표의 행이면 그 표의 첫 행도 함께")
    d.add_argument("--changes", action="store_true", help="최근 개정의 바뀐 자리 — --grep 을 함께 주면 그 낱말이 든 자리만")
    d.add_argument("--images", action="store_true", help="본문 그림을 파일로 받아 낸다 — 본문 글자는 안 싣는다")
    d.add_argument("--history", action="store_true", help="개정이력 — 판마다 rev · enforced · summary(주요 개정 내용) · hname · by(올린 사람)")
    d.add_argument("--rev", metavar="판", help="지난 판 하나(--history 의 rev) — 본문 · --grep · --from · --max 가 그 판에 걸린다. "
                   "--changes 는 그 개정의 전후대비표, --trail 은 그 개정의 결재 경과")
    d.add_argument("--trail", action="store_true", help="개정의 결재 경과(검토 · 승인의 걸음 · 때 · 사람 · 의견) — 없으면 지금 판")
    d.add_argument("--contacts", action="store_true", help="담당 · 검토 · 승인의 사람 창(부서 · 직급 · 직책 · 담당 업무 · 회사 전화 · 휴대 전화 · 메일)")
    command("refresh")
    return p


def main() -> int:
    args = parser().parse_args()

    def work(cbsop) -> dict:
        refused = refusal(args)
        if refused:
            raise Stop(EXIT_ARGS, "args", refused)
        if args.command == "search" and args.access:
            grade_of(cbsop.GRADES, args.access)          # 없는 등급도 세션 전에 — 로그인을 청할 일이 아니다
        if args.command in INDEX_ONLY and usable_index(args) is not None:
            return run(args, None)                       # 받아 둔 목록으로 선다 — 세션 파일이 없어도 답한다
        return ep_session.session_first(lambda f: run(args, f), expired=(cbsop.SessionExpired, cbsop.SessionMissing))

    return ep_command.finish(work, "cbsop", HERE)


if __name__ == "__main__":
    sys.exit(main())
