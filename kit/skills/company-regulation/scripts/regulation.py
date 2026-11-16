"""사규 스킬의 얇은 명령 — 곁의 손(``cbsop.py``)으로 사규관리 앱의 목록을 받아 두고, 거기서 찾고, 앱에 검색하고, 한 건을 읽는다.

부르는 꼴::

    python -X utf8 -I regulation.py find   <말 …> [--in 범주] [--from N] [--most N]   # 받아 둔 목록에서 — 표준명 · 경로 · 담당 · 부서에 말이 다 든 것
    python -X utf8 -I regulation.py tree   ["경로"] [--from N] [--most N]            # 받아 둔 목록의 구조 · 맨 아래 칸이면 그 칸의 문서
    python -X utf8 -I regulation.py recent [--days N] [--in 범주] [--from N] [--most N]   # 받아 둔 목록에서 시행일이 최근 N 일 안인 것
    python -X utf8 -I regulation.py search <말> [--body] [--owner] [--from N] [--most N]  # 앱에 묻는다 — 기본은 표준명, --body 는 본문까지, --owner 는 담당자 · 부서 이름까지
    python -X utf8 -I regulation.py read   <processIdx>                      # 문서 한 건 — 짧으면 본문 통째로, 길면 앞머리와 이어 읽는 길
    python -X utf8 -I regulation.py read   <processIdx> --images             # 본문 그림을 파일로 받아 낸다(앞 body_images.MAX_IMAGES 장까지)
    python -X utf8 -I regulation.py read   <processIdx> --grep <낱말 …>      # 그 낱말(하나라도)이 든 대목만
    python -X utf8 -I regulation.py read   <processIdx> --from N [--max N]   # 본문을 N 째 글자부터
    python -X utf8 -I regulation.py read   <processIdx> --changes            # 최근 개정의 바뀐 자리만
    python -X utf8 -I regulation.py refresh                                  # 목록을 지금 다시 받는다(1 분 남짓)

``find`` · ``tree`` · ``recent`` 는 받아 둔 목록(INDEX_DAYS 안 · recent 는 RECENT_FRESH_DAYS 안)을 읽고, 없거나 낡았으면 먼저 새로
받는다 — 그 판만 1 분 남짓 걸린다. 받아 둔 목록으로 서는 판은 세션 파일 없이 답한다.
``find`` 의 말과 ``범주`` · ``tree`` 의 경로 · ``--grep`` 의 낱말은 빈칸 · 가운뎃점 · 괄호 · 대소문자를 안 보고 견준다(「여비관리」 = 「여비
관리」 · 「안전환경」 = 「안전 · 환경」). ``범주`` 는 맨 위 범주 이름의 일부(정관 · 전사공통 · 에너지소재 · 기초소재 · 안전 · 인증). ``tree`` 의
경로는 칸을 「>」 로 가르고 칸마다 그 깊이 범주 이름의 일부면 된다(「기초 > 작업표준 > 포항화성」). 셸이 「>」 를 쓰기로 읽으니 경로는
따옴표로 감싼다. 경로가 맨 아래 칸에 닿으면 그 칸의 문서를 이름순으로 낸다.

``read`` 는 물음만큼만 읽게 낸다. 낱말 없이 부르면 메타와 본문의 앞 READ_FIRST 자를 낸다 — 본문이 그 안이면 통째로 오고 바뀐
자리가 함께 온다. 넘으면 ``more`` 가 다음 ``--from`` 을, ``next`` 가 읽는 길(낱말은 ``--grep`` · 통째로는 ``more`` 를 따라)을 든다.
목차는 내지 않는다 — 사규 · 작업표준은 제목 줄의 꼴이 문서마다 달라, 꼴로 뽑은 목차에는 쪽번호 · 쪽마다 되풀이되는 머리 · 표 안의
번호가 제목으로 섞인다.
``--grep`` 은 낱말이 든 줄을 앞뒤의 짧은 줄(GREP_AROUND 줄까지)과 함께 대목으로 묶어 자리 ``at`` 을 붙여 낸다 — 표의 행이
걸리면 그 표의 첫 행(머리)도 함께 온다. 본문은 글자만이다: 표는 한 행이 한 줄이고 칸을 「 | 」 로 가르며, 합친 칸은 차지한 자리마다 같은
글자를 되풀이한다. 그림은 ``[그림 N]`` 이다 — N 은 본문에 나온 차례고, ``--images`` 가 받은 그림의 ``no`` 와 같다. 그림은 흔하다
(작업표준 · 지침의 흐름도 · 설비 사진 — ``references/SOURCES.md``). 그림이 든 문서의 답은 ``images_count`` 를 든다.
본문 HTML 은 형제 스킬 company-mail 의 ``visible`` 이 푼다(메일 · 게시판과 한 손) — 사람 눈에 안 보이는 글(숨긴 요소 · 바탕색 글 ·
스크립트)은 걷히고, 걷은 덩이가 있으면 답이 그 수를 ``hidden`` 에 든다. 답의 글자는 어느 칸이든 폭 없는 문자 · 방향 뒤집기 문자를 걷고 나간다.

답 하나는 OUT_BYTES 를 안 넘는다 — 넘을 줄 · 본문 · 대목은 덜어 내고 답의 ``more`` 가 다음 ``--from`` 을 든다.

하는 일 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 로 사내 세션을 쥐고(있는 파일부터 · 거절되면 받는 손으로 한 번 더)
앱에 들어가 읽는다. 앱에 아무것도 쓰지 않는다 — 열람 기록 주소도 안 부른다(``cbsop.py`` 머리말). 받은 본문 글자는 PC 에 남기지 않는다 —
``--images`` 의 그림만 임시 폴더 아래 IMAGES_ROOT/<processIdx> 에 남는다(받는 손은 형제 스킬 company-mail 의 ``body_images``).

내는 것 — 표준 출력에 JSON 하나. 종료 값: 0 됐다 · 1 도구 · 앱 고장(그대로 알린다) · 2 인자가 틀렸다 · 3 사내 세션이 없다 ·
끊겼다(스킬 ep-login). 0 이 아니면 ``message`` 가 까닭과 「다음: …」 을 든다.
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
INDEX_DAYS = 30                # 받아 둔 목록을 다시 안 받고 쓰는 날 — 사규는 드물게 바뀌고 받는 데 1 분 남짓 든다. 그 사이는 refresh
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
APP_DATE = "%Y.%m.%d"          # 앱이 시행일을 적는 꼴(잰 것)
SEARCH_HIT_PREFIX = "searchMenuInList"   # 통합 검색 답에서 범주마다의 결과가 든 칸의 머리
INDEX_ONLY = ("find", "tree", "recent")   # 받아 둔 목록이 서 있으면 앱을 안 부르는 명령
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


def in_menu(rows: list, word: str | None) -> list:
    key = squash(word)
    return [r for r in rows if key in squash(r["path"].split(PATH_SEP)[0])] if key else rows


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


def changes_of(got: dict, room: int) -> tuple[list, int]:
    """최근 개정의 바뀐 자리 — room 바이트 안에 드는 데까지와, 못 실은 건수. 첫 건은 늘 싣는다."""
    out, used, left = [], 0, 0
    for c in got.get("searchTobe") or []:
        one = {"why": c.get("note"), "before": clip(plain(c.get("oldContent"), False), CHANGE_SIDE),
               "after": clip(plain(c.get("toContent"), False), CHANGE_SIDE)}
        if left or (out and used + size(one) > room):
            left += 1
            continue
        used += size(one)
        out.append(one)
    return out, left


def with_changes(out: dict, got: dict, room: int) -> None:
    changes, left = changes_of(got, room)
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
def usable_index(args) -> dict | None:
    """이 명령이 그대로 쓸 받아 둔 목록 — refresh 는 늘 없고, recent 는 RECENT_FRESH_DAYS 안에 받은 것만."""
    got = None if args.command == "refresh" else cached_index()
    if got is not None and args.command == "recent" and time.time() - got["stamp"] >= RECENT_FRESH_DAYS * DAY_SECONDS:
        return None
    return got


def need_index(app, args) -> tuple[dict, bool, str]:
    """(목록, 방금 받았나, 받은 목록을 PC 에 못 남긴 까닭) — 못 남겨도 받은 목록으로 답한다. 다음 판이 다시 받을 뿐이다."""
    got = usable_index(args)
    if got is not None:
        return got, False, ""
    fresh = build_index(app)
    return fresh, True, ep_command.keep(index_path(), fresh)


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
    if args.images and (args.grep or args.changes or args.start is not None):
        raise Stop(EXIT_ARGS, "args", "--images 는 --grep · --changes · --from 과 함께 못 쓴다 — 다음: 그림과 글자를 따로 부른다")
    if args.images:
        out = dict(brief)
        out["images"] = save_images(app, args.idx, list(page_.images)) if page_.images else []
        return out
    if args.changes:
        out = dict(brief)
        with_changes(out, got, OUT_BYTES - size(brief) - 1000)
        return out
    if args.grep:
        return grep(brief, body, args.grep, max(0, args.start or 0))
    if args.start is not None:                           # 본문을 짚은 자리부터 — 메타는 되풀이하지 않는다
        out = {**brief, "from": max(0, args.start)}
        fit_text(out, body, out["from"], max(1, args.max))
        return out
    out = {**brief, "path": info.get("processPath"), "next_review": info.get("examineDate"),
           "owner": f"{info.get('hname')}({info.get('deptnm')})", "reviewer": info.get("reviewer"),
           "approver": info.get("approval"), "last_change": info.get("mainContent")}
    related = [r.get("processName") for r in got.get("relationList") or got.get("searchRelationList") or [] if isinstance(r, dict)]
    if related:
        out["related"] = related
    files = [f.get("fileName") or f.get("orgFileName") for f in got.get("searchProcessFileList") or [] if isinstance(f, dict)]
    if files:
        out["files"] = files
    if len(body) > READ_FIRST:                           # 긴 문서 — 앞머리만 싣고 읽을 길을 댄다. 바뀐 자리는 수만 센다
        changed = len(got.get("searchTobe") or [])
        if changed:
            out["changes_count"] = changed
        out["next"] = NEXT_READ + (" · 바뀐 자리는 --changes" if changed else "")
    else:
        with_changes(out, got, CHANGES_BYTES)
    out["from"] = 0
    fit_text(out, body, 0, min(max(1, args.max), READ_FIRST))
    return out


def run(args, session: pathlib.Path | None) -> dict:
    """session 이 None 이면 받아 둔 목록만으로 답하는 판이다(main 이 가린다)."""
    app = None if session is None else load("cbsop", HERE).App(session)
    if args.command in INDEX_ONLY + ("refresh",):
        index, fresh, unkept = need_index(app, args)
        head = {"index_at": stamp_word(index), "fresh": fresh, "total": len(index["rows"])}
        if unkept:
            head["index_note"] = f"받은 목록을 PC 에 못 남겼다({unkept}) — 다음 판도 목록을 새로 받는다(1 분 남짓)"
        rows = index["rows"] if args.command == "tree" else in_menu(index["rows"], getattr(args, "inside", None))
        if args.command == "refresh":
            return {**head, "menus": index["menus"]}
        if args.command == "find":
            keys = [k for k in (squash(w) for w in args.words) if k]
            hit = [r for r in rows if all(k in squash("|".join(str(r.get(c) or "") for c in FIND_KEYS)) for k in keys)]
            hit.sort(key=lambda r: (not all(k in squash(r["processName"]) for k in keys), r["path"], r["processName"]))
            return page(head, hit, args.start, args.most)
        if args.command == "tree":
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
        since = (date.today() - timedelta(days=args.days)).strftime(APP_DATE)
        hit = sorted((r for r in rows if (r["enforcementDate"] or "") >= since), key=lambda r: r["enforcementDate"], reverse=True)
        return page({**head, "since": since}, hit, args.start, args.most)
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


def parser() -> argparse.ArgumentParser:
    shown = {"description": __doc__, "formatter_class": argparse.RawDescriptionHelpFormatter}   # --help 는 어디서 불러도 머리말을 낸다
    p = argparse.ArgumentParser(prog="regulation.py", **shown)
    sub = p.add_subparsers(dest="command", required=True)

    def paged(cmd: argparse.ArgumentParser, most: int) -> None:
        cmd.add_argument("--most", type=int, default=most)
        cmd.add_argument("--from", dest="start", type=int, default=0)

    f = sub.add_parser("find", **shown)
    f.add_argument("words", nargs="+")
    f.add_argument("--in", dest="inside")
    paged(f, MOST_FIND)
    t = sub.add_parser("tree", **shown)
    t.add_argument("inside", nargs="*", help="경로 — 「기초 > 작업표준 > 포항화성」 처럼 칸을 > 로 가른다")
    paged(t, MOST_FIND)
    r = sub.add_parser("recent", **shown)
    r.add_argument("--days", type=int, default=RECENT_DAYS)
    r.add_argument("--in", dest="inside")
    paged(r, MOST_RECENT)
    s = sub.add_parser("search", **shown)
    s.add_argument("words", nargs="+")
    s.add_argument("--body", action="store_true")
    s.add_argument("--owner", action="store_true")
    paged(s, MOST_SEARCH)
    d = sub.add_parser("read", **shown)
    d.add_argument("idx", type=int)
    d.add_argument("--from", dest="start", type=int, default=None)
    d.add_argument("--max", type=int, default=READ_MAX)
    d.add_argument("--grep", nargs="+", metavar="낱말")
    d.add_argument("--changes", action="store_true")
    d.add_argument("--images", action="store_true", help="본문 그림을 파일로 받아 낸다 — 본문 글자는 안 싣는다")
    sub.add_parser("refresh", **shown)
    return p


def main() -> int:
    args = parser().parse_args()

    def work(cbsop) -> dict:
        if args.command in INDEX_ONLY and usable_index(args) is not None:
            return run(args, None)                       # 받아 둔 목록으로 선다 — 세션 파일이 없어도 답한다
        return ep_session.session_first(lambda f: run(args, f), expired=(cbsop.SessionExpired, cbsop.SessionMissing))

    return ep_command.finish(lambda cbsop: reader().shown(work(cbsop)), "cbsop", HERE)


if __name__ == "__main__":
    sys.exit(main())
