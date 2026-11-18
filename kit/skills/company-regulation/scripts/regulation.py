"""사규 스킬의 얇은 명령 — 곁의 손(``cbsop.py``)으로 사규관리 앱의 목록을 받아 두고, 거기서 찾고, 앱에 검색하고, 한 건을 읽는다.

부르는 꼴 · 명령마다의 인자 · 답의 칸 · 종료 값은 ``--help`` 가 낸다 — 그 글은 이 파일의 표(``READS`` · ``NOT_HERE`` · ``EXITS``)와 argparse
에서 서고, 이 머리말은 고치는 사람이 읽는 계약만 든다.

- 세션 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 가 쥔다(있는 파일부터 · 거절되면 받는 손으로 한 번 더). 함께 못 서는 인자
  (``refusal``)는 세션 · 목록 받기 전에 종료 2 로 멈춘다
- 받아 둔 목록 — ``find`` · ``tree`` · ``recent`` 는 홈의 목록(``index_path``)으로 답하고 앱을 안 부른다. ``INDEX_DAYS`` 가 지나거나, 최근
  시행을 묻는 판(``wants_fresh``)에 ``RECENT_FRESH_DAYS`` 가 지나면 먼저 새로 받는다
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
INDEX_FORMAT = 1               # 받아 둔 파일의 꼴 번호 — 줄의 칸이 바뀌면 올린다
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
SEARCH_HIT_PREFIX = "searchMenuInList"   # 통합 검색 답에서 범주마다의 결과가 든 칸의 머리
INDEX_ONLY = ("find", "tree", "recent")   # 받아 둔 목록이 서 있으면 앱을 안 부르는 명령
FRESH_ONLY = ("recent",)       # 늘 RECENT_FRESH_DAYS 안의 목록을 쓰는 명령 — find 는 --days 를 받았을 때만 그렇다
NEXT_READ = "다음: 물음에 낱말이 있으면 --grep <낱말 …> 로 그 대목만 · 통째로는 more 의 --from 을 따라 끝까지 읽는다"
ROW_KEYS = ("processIdx", "processName", "enforcementDate", "hname", "deptnm", "version")
FIND_KEYS = ("processName", "path", "hname", "deptnm")   # find 가 말을 견주는 칸


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


def row_of(raw: dict) -> dict:
    out = {k: raw.get(k) for k in ROW_KEYS}
    out["path"] = PATH_SEP.join(path_of(raw))
    if raw.get("relationName"):
        out["related"] = raw["relationName"]
    return out


def build_index(app) -> dict:
    menus = [m for m in app.menus() if m.get("openYn", "Y") == "Y"]
    rows, seen = [], set()
    for m in menus:
        for raw in app.all_in(m["menuIdx"]):
            if is_folder(raw) or raw.get("processIdx") in seen:
                continue
            seen.add(raw.get("processIdx"))
            rows.append(row_of(raw))
    return {"format": INDEX_FORMAT, "stamp": time.time(), "menus": [m["menuName"] for m in menus], "rows": rows}


def cached_index() -> dict | None:
    """INDEX_DAYS 안에 받은 같은 꼴의 목록 — 없거나 낡았거나 깨졌으면 None."""
    got = ep_command.kept(index_path(), INDEX_FORMAT, INDEX_DAYS)
    return got[0] if got and isinstance(got[0].get("rows"), list) else None


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
    if any(squash(w) for w in args.words) or squash(args.inside) or args.days is not None:
        return ""
    return "find 는 말 · --in · --days 가운데 하나는 받는다 — 다음: 구조는 tree, 최근 시행은 recent 로 본다"


def find(head: dict, rows: list, args) -> dict:
    """받아 둔 목록을 말 × 범주(어느 깊이든) × 기간으로 거른다. 기간을 주면 새 시행일부터, 아니면 제목에 말이 다 든 것부터 경로 · 이름
    차례. 0 건이면 ``next`` 가 무엇을 찾았고 무엇을 풀어 볼지를 든다."""
    keys = [k for k in (squash(w) for w in args.words) if k]
    scoped = under_category(rows, args.inside)
    if args.days is not None:
        head = {**head, "since": since_of(args.days)}
        scoped = [r for r in scoped if (r["enforcementDate"] or "") >= head["since"]]
    hit = [r for r in scoped if all(k in squash("|".join(str(r.get(c) or "") for c in FIND_KEYS)) for k in keys)]
    if args.days is not None:
        hit.sort(key=lambda r: r["enforcementDate"] or "", reverse=True)
    else:
        hit.sort(key=lambda r: (not all(k in squash(r["processName"]) for k in keys), r["path"], r["processName"]))
    out = page(head, hit, args.start, args.most)
    if not hit:
        out["next"] = find_hint(rows, args, keys, head.get("since"))
    return out


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
    return ""


def read(app, args) -> dict:
    got = app.info(args.idx)
    info = (got.get("ProcessInfo") or [None])[0]
    if not info:
        raise Stop(EXIT_ARGS, "args", f"문서 {args.idx} 가 없다 — 다음: find · search 로 processIdx 를 찾는다")
    page_ = reader().body(info.get("content"))
    body = page_.text
    brief = {"processIdx": info.get("processIdx"), "name": info.get("processName"), "rev": info.get("version"),
             "enforced": info.get("enforcementDate"), "security": info.get("securityGradeName"), "length": len(body)}
    if page_.images:
        brief["images_count"] = len(page_.images)
    if page_.hidden:
        brief["hidden"] = page_.hidden
    most = READ_MAX if args.max is None else max(1, args.max)
    if args.images:
        out = dict(brief)
        out["images"] = save_images(app, args.idx, list(page_.images)) if page_.images else []
        return out
    if args.changes:                                     # --grep 을 주면 그 낱말이 든 바뀐 자리만
        out = dict(brief)
        with_changes(out, got, OUT_BYTES - size(brief) - 1000, args.grep)
        return out
    if args.grep:
        return grep(brief, body, args.grep, max(0, args.start or 0))
    if args.start is not None:                           # 본문을 짚은 자리부터 — 메타는 되풀이하지 않는다
        out = {**brief, "from": max(0, args.start)}
        fit_text(out, body, out["from"], most)
        return out
    out = {**brief, "path": info.get("processPath"), "next_review": info.get("examineDate"),
           "hname": info.get("hname"), "deptnm": info.get("deptnm"), "reviewer": info.get("reviewer"),
           "approver": info.get("approval"), "last_change": info.get("mainContent")}
    related = [r.get("processName") for r in got.get("relationList") or got.get("searchRelationList") or [] if isinstance(r, dict)]
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
        if unkept:
            head["index_note"] = f"받은 목록을 PC 에 못 남겼다({unkept}) — 다음 판도 목록을 새로 받는다(1 분 남짓)"
        if args.command == "refresh":
            return {**head, "menus": index["menus"]}
        if args.command == "find":
            return find(head, index["rows"], args)
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
        rows = under_category(index["rows"], args.inside)
        hit = sorted((r for r in rows if (r["enforcementDate"] or "") >= since), key=lambda r: r["enforcementDate"], reverse=True)
        out = page({**head, "since": since}, hit, args.start, args.most)
        if not hit:
            out["next"] = find_hint(index["rows"], args, [], since)
        return out
    if args.command == "search":
        fields = ["subject"] + (["content"] if args.body else []) + (["user_name", "team_name"] if args.owner else [])
        got = app.search(" ".join(args.words), ",".join(fields))
        hits = []
        for key, value in sorted(got.items()):
            if key.startswith(SEARCH_HIT_PREFIX) and isinstance(value, list):
                for x in value:
                    hits.append({"processIdx": x.get("processIdx"), "processName": x.get("processName"),
                                 "path": x.get("processPath"), "enforcementDate": x.get("enforcementDate"),
                                 "hname": x.get("hname"), "deptnm": x.get("deptnm")})
        out = page({"fields": fields}, hits, args.start, args.most)
        out["count"] = got.get("searchListCnt", len(hits))
        return out
    return read(app, args)


NOT_HERE = ("개정 · 폐지 · 신규 제정 · 인계인수 · 이슈 등록 · 검토 · 승인 · 첨부 받기 · 화면 조작 — 손에 없다. 사람에게 사규 화면에서 하도록 "
            "권하고 찾은 문서의 이름 · 경로를 대 준다. 앱에 아무것도 쓰지 않는다(열람 기록도 안 남긴다)")
EXITS = ("0 됐다 · 1 도구 · 앱 고장(그대로 알리고 다시 부르지 않는다) · 2 인자가 틀렸다(함께 못 서는 인자도 — 세션 전에 멈춘다) · 3 사내 세션이 "
         "없다 · 끊겼다(스킬 ep-login 을 부른 뒤 같은 명령을 다시). 0 이 아니면 message 가 까닭과 「다음: …」 을 든다")


def reads() -> dict:
    """명령마다 (한 줄 — 맨 위 --help 의 지도와 명령 목록, 그 명령의 --help 에 덧붙는 설명 · 답의 칸). --help 는 이 표와 argparse 에서만 선다."""
    images = ep_command.load("body_images", MAIL_SCRIPTS).MAX_IMAGES   # 그림 수의 위는 받는 손의 값 그대로 — 손을 대역으로 바꾼 판에도 도움말은 선다
    rows = "답: index_at(목록을 받은 때) · fresh(이 판에 새로 받았나) · total(목록 전체 건수) · count(걸린 건수) · from · rows(줄마다 processIdx · " \
           "processName · enforcementDate · hname(담당) · deptnm(부서) · version · path) · more(다음 --from)"
    return {
        "find": ("받아 둔 목록에서 찾기 — 말 × 범주(어느 깊이든) × 기간을 아무 조합으로 한 부름에(하나는 준다)",
                 "말은 표준명 · 경로 · 담당 · 부서에 다 든 것이다 — 사람의 말에서 제목에 들 낱말을 짧게 뽑는다(「해외 출장 숙박비」 → 출장). "
                 "「요즘 바뀐 출장 규정」 은 find 출장 --days 90 한 번이다. 안 나오면 search <말> --body\n\n"
                 f"{rows}. --days 를 주면 since 를 들고 새 시행일부터, 0 건이면 next 가 찾은 조건과 풀어 볼 길을 든다"),
        "tree": ("받아 둔 목록의 구조와 건수 — 경로를 주면 그 아래, 맨 아래 칸에 닿으면 그 칸의 문서",
                 "경로 없이 부르면 맨 위 범주부터 나무와 건수가 온다. 칸을 골라 「기초 > 작업표준」 → 「기초 > 작업표준 > 포항화성」 처럼 내려간다\n\n"
                 f"답: index_at · fresh · total · paths(걸린 경로 — {MOST_FIND} 개까지) · tree(칸마다 count · under). 맨 아래 칸이면 그 칸의 문서를 "
                 "이름순으로 rows · count · from · more 로 낸다. 걸리는 칸이 없으면 종료 2"),
        "recent": ("받아 둔 목록에서 시행일이 최근 N 일 안인 것 — 새 시행일부터(말로 거르려면 find --days)",
                   f"늘 받은 지 {RECENT_FRESH_DAYS} 일 안의 목록을 쓴다 — 낡았으면 먼저 새로 받는다\n\n{rows} · since. 0 건이면 next"),
        "search": ("앱에 묻는 찾기 — 기본은 표준명, --body 는 본문까지, --owner 는 담당자 · 부서 이름까지",
                   "흔한 낱말의 본문 찾기는 17 초쯤 걸린다 — 뜻이 좁은 낱말을 고른다\n\n"
                   "답: fields(찾은 칸) · count(앱이 센 수) · from · rows(줄마다 processIdx · processName · path · enforcementDate · hname · deptnm) · more"),
        "read": ("문서 한 건 — 물음만큼만: 낱말이면 --grep, 바뀐 것이면 --changes, 그림이면 --images",
                 f"낱말 없이 부르면 메타(판 · 시행일 · 다음 검토일 · 담당 · 검토 · 승인 · 보안등급)와 본문 앞 {READ_FIRST} 자가 온다 — 본문이 그 안이면 "
                 "통째로 오고 바뀐 자리(changes)도 함께 온다. 넘으면 more 가 다음 --from 을, next 가 읽는 길을 든다. 목차는 안 낸다(제목 줄의 꼴이 "
                 "문서마다 달라 틀린 조를 가리킨다)\n\n"
                 "함께 서는 짝 — --grep 은 본문에서도(--from 은 찾기 시작 자리) 바뀐 자리에서도(--changes) 거른다. --from · --max 는 본문을 읽는 판에만, "
                 "--images 는 혼자만 든다. 안 서는 짝은 세션 전에 종료 2 다\n\n"
                 "답: processIdx · name · rev · enforced · security · length(본문 글자 수) · path · next_review · hname · deptnm(받는 사람 찾기 — "
                 "company-mail 의 who --name <hname>, 동명이인이면 deptnm 으로 고른다) · reviewer · approver · last_change · related · files · "
                 "text · from · more · next. --grep 은 hits(대목마다 at — 그 자리부터 --from 으로 둘레를 더 읽는다 · text) · count, --changes 는 "
                 "changes(why · before · after) · changes_more, 긴 문서의 첫 답은 changes_count. 본문은 글자만이다 — 표는 한 행 한 줄 · 칸 사이 「 | 」 · 합친 칸은 자리마다 같은 "
                 "글자, 그림은 「[그림 N]」(images_count 가 그 수). 사람 눈에 안 보이게 감춘 글은 걷히고 그 덩이 수가 hidden 이다 — 찾는 대목이 "
                 f"안 나오는데 hidden 이 서면 「규정에 없다」고 하지 않는다. --images 는 앞 {images} 장까지 받아 images(no · path · 안 받은 그림은 "
                 "skipped)를 낸다"),
        "refresh": ("목록을 지금 다시 받는다 — 1 분 넘게 걸린다. 「방금 올라온 것」이 안 나올 때만",
                    "답: index_at · fresh · total · menus(받은 맨 위 범주)"),
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
    out.append(f"종료 값 — {EXITS}")
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

    category = "경로의 어느 깊이든 이 범주 아래 — 「작업표준」 · 「기초 > 작업표준」 · 맨 위 범주(정관 · 전사공통 · 에너지소재 · 기초소재 · 안전 · 인증)"
    f = command("find")
    f.add_argument("words", nargs="*", metavar="말", help="표준명 · 경로 · 담당 · 부서에 다 든 말 — 안 주면 --in · --days 로만 거른다")
    f.add_argument("--in", dest="inside", metavar="범주", help=category)
    f.add_argument("--days", type=int, default=None, metavar="N", help="시행일이 최근 N 일 안인 것만 — 새 시행일부터 낸다")
    paged(f, MOST_FIND)
    t = command("tree")
    t.add_argument("inside", nargs="*", metavar="경로", help="「기초 > 작업표준 > 포항화성」 처럼 칸을 > 로 가른다 — 안 주면 맨 위부터")
    paged(t, MOST_FIND)
    r = command("recent")
    r.add_argument("--days", type=int, default=RECENT_DAYS, metavar="N", help=f"시행일이 최근 N 일 안인 것(기본 {RECENT_DAYS})")
    r.add_argument("--in", dest="inside", metavar="범주", help=category)
    paged(r, MOST_RECENT)
    s = command("search")
    s.add_argument("words", nargs="+", metavar="말", help="찾을 말 — 여러 낱말은 한 검색어로 이어 묻는다")
    s.add_argument("--body", action="store_true", help="본문까지 찾는다 — 흔한 낱말이면 오래 걸린다")
    s.add_argument("--owner", action="store_true", help="담당자 · 부서 이름까지 찾는다")
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
    command("refresh")
    return p


def main() -> int:
    args = parser().parse_args()

    def work(cbsop) -> dict:
        refused = refusal(args)
        if refused:
            raise Stop(EXIT_ARGS, "args", refused)
        if args.command in INDEX_ONLY and usable_index(args) is not None:
            return run(args, None)                       # 받아 둔 목록으로 선다 — 세션 파일이 없어도 답한다
        return ep_session.session_first(lambda f: run(args, f), expired=(cbsop.SessionExpired, cbsop.SessionMissing))

    return ep_command.finish(work, "cbsop", HERE)


if __name__ == "__main__":
    sys.exit(main())
