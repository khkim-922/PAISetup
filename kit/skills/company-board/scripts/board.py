"""게시판 스킬의 얇은 명령 — 곁의 손(``xclick.py`` 읽기 · ``draft_board.js`` 짓기)으로 사내 게시판을 찾고 읽고, 글을 임시저장한다.

부르는 꼴::

    python -X utf8 -I board.py boards [--write]                              # 게시판 나무 — --write 는 글을 쓸 수 있는 곳만
    python -X utf8 -I board.py list   [게시판] [--since 날] [--until 날] [--page N]
    python -X utf8 -I board.py search <말> [--in 게시판] [--field title|contents|writer|filename …] [--since 날] [--until 날] [--page N]
    python -X utf8 -I board.py read   <글 id> --board <게시판 id> [--from N] [--images]   # 글 한 건 — 본문 글자 · 첨부 목록 · --images 면 본문 그림 파일. 조회수는 안 올린다
    python -X utf8 -I board.py attachment <글 id> [--save 번호|all] [--out 폴더]
    python -X utf8 -I board.py drafts                                        # 임시 · 예약보관함
    python -X utf8 -I board.py save --board <게시판> --title <제목> (--html-file 파일 | --text-file 파일) [--image 그림 …] [--file 첨부 …]
    python -X utf8 -I board.py show <글 id> --board <게시판 id>              # 임시보관함 글을 편집 창으로 띄운다

``게시판`` 은 id(BBS…)나 이름의 일부(「식단」 · 「업무공지」 · 「일반사항 > 기타」)다 — 이름이 여럿에 걸리면 종료 2 가 후보를 든다.
묶음 게시판(「일반사항」)을 주면 그 아래 게시판을 다 본다. 안 주면 모든 게시판이다. 기간을 안 주면 처음부터 오늘까지다 — 화면의 기본(6
개월 · 1 년)보다 넓다. ``search`` 의 기본 칸은 제목 · 내용 · 작성자 · 첨부 이름 넷이다.

``save`` 는 쓰는 사람의 Edge 화면(디버깅 포트)에서 [글쓰기] 창을 열어 넣고 [임시저장]만 누른다 — 등록은 안 한다. 저장한 글을 편집 창으로
띄워 두니 사람이 그 창에서 보고 [등록]을 누른다. 글은 HTML 파일이나 평문 파일이고, ``--image`` 의 그림은 본문 끝에 차례로 붙는다(data URI —
게시판이 그대로 저장한다 · 잰 것). 묶음 게시판에는 못 쓴다 — 게시판이 막는다.

받은 첨부 — 문서함(ECM) 쪽지(「이름(확장자_NKB).html」)는 파일로 안 남기고 문서 열쇠를 낸다(스킬 company-ecm 의 read 로 연다). 그 밖은
``--out``(기본 임시 폴더 아래 SAVE_ROOT/<글 id>)에 받고, 오피스 · PDF 가 DRM 에 감겼으면 ``note`` 가 그렇다고 말한다 — 읽는 손(스킬
drm-office-read)이 받는 꼴이면 그 스킬로 넘기고, 안 받는 꼴(한글 · docm …)이면 못 읽는다고 말한다. 저장 이름과 그 가름은 형제 스킬
company-mail 의 ``attachments`` 가 든다(메일 첨부와 한 가름) — 이름이 서로 다르면 그 이름 그대로, 겹치면 「<번호>-」 를 붙인다.

본문 — ``read`` 의 글자는 형제 스킬 company-mail 의 ``visible`` 이 푼다(메일 · 사규와 한 손). 사람 눈에 안 보이는 글(숨긴 요소 · 바탕색 글 ·
스크립트)은 걷히고, 걷은 덩이가 있으면 답이 그 수를 ``hidden`` 에 든다. 표는 한 행이 한 줄이고 칸을 「 | 」 로 가르며, 합친 칸은 차지한
자리마다 같은 글자를 되풀이한다. 그림은 「[그림 N]」 이다 — N 은 ``--images`` 가 받은 그림의 ``no`` 와 같다. 답의 글자는 어느 칸이든(제목 ·
작성자 · 첨부 이름도) 폭 없는 문자 · 방향 뒤집기 문자를 걷고 나간다.

하는 일 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 로 사내 세션을 쥐고 게시판에 들어가 읽는다. 읽기는 게시판에 아무것도 안
남긴다(조회수도 안 올린다 · ``xclick.py`` 머리말). 게시판 나무는 홈에 받아 두고(TREE_DAYS) ``list`` · ``search`` 가 그것으로 이름을
가린다 — 받아 둔 것에 없는 게시판을 만나면 그 판에 새로 받고, ``boards`` 는 늘 새로 받아 남긴다.

내는 것 — 표준 출력에 JSON 하나. 답 하나는 OUT_BYTES 를 안 넘는다 — 넘을 줄 · 본문은 덜고(본문은 줄 끝에서 끊는다) ``more`` 가 다음 ``--from`` 이나 ``--page`` 를
든다. 목록 줄은 ``id`` · ``title`` · ``writer`` · ``date`` 에, 참일 때만 ``notice``(고정 공지) · ``files``(첨부가 있다)를 든다. 줄의 게시판
(``board`` · ``board_name``)은 머리의 ``board_id``(게시판 하나만 본 답)와 다를 때만 든다. 종료 값: 0 됐다 · 1 도구 · 앱 고장(그대로 알린다) · 2 인자가 틀렸다(글 id 와 게시판 id 가 안 맞는 것도) · 게시판이 저장을 막았다 · 3 사내 세션이 없다 · 끊겼다(스킬 ep-login).
0 이 아니면 ``message`` 가 까닭과 「다음: …」 을 든다.
"""

from __future__ import annotations

import argparse
import base64
import html as html_lib
import json
import mimetypes
import os
import pathlib
import re
import sys
import tempfile
import time

HERE =pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
# 형제 스킬 — 본문을 푸는 손(``visible``) · 본문 그림을 받는 손(``body_images``) · 첨부 가름(``attachments``) · ECM 쪽지의 꼴과 열쇠(``inbox``)가 사는 자리
MAIL_SCRIPTS = HERE.parents[1] / "company-mail" / "scripts"
DRAFT_HAND = "draft_board.js"     # 글을 화면에서 짓는 손 — 이 파일 곁
DRAFT_HAND_SECONDS = 330          # 그 손 한 판의 시한 — 흔한 판은 30 초 안쪽이고, 대화 도구의 시한(스킬 본문의 6 분)보다 짧아야 끊겨도 답이 온다
SAVE_ROOT = "company-board"       # 첨부를 받는 기본 자리 — 임시 폴더 아래
IMAGES_DIR = "body-images"        # read --images 가 본문 그림을 받는 자리 — 그 글의 첨부 자리 아래
FIELDS = ("title", "contents", "writer", "filename")   # 찾는 칸 — 화면의 검색조건 넷
LIST_COUNT = 20                   # list · search 한 쪽의 줄 수
TREE_DAYS = 7                     # 받아 둔 게시판 나무를 다시 안 받고 쓰는 날 — 게시판은 드물게 생기고, 받으려면 묶음마다 한 번씩 물어야 한다
TREE_DIR = ".company-board"       # 받아 둔 나무의 자리 — 홈 아래(임시 폴더는 정리 도구가 지운다)
TREE_FILE = "boards.json"
TREE_FORMAT = 1                   # 받아 둔 파일의 꼴 번호 — 나무 줄의 칸이 바뀌면 올린다
ROW_FLAGS = ("notice", "files")   # 목록 줄에서 참일 때만 싣는 칸
READ_MAX = 12000                  # read 가 한 번에 내는 본문 글자 수 — 한글 본문은 OUT_BYTES 가 먼저 끊는다
SAVED_TEXT_FILE = "article.txt"   # read 가 본문 글자 전부를 남기는 파일 이름 — 긴 글은 이 파일을 나눠 읽는다
PATH_SEP = " > "
BODY_STYLE = "font-family:'맑은 고딕','Malgun Gothic',sans-serif;font-size:10pt;line-height:1.6"   # 평문 글을 싸는 모양 — 게시판 편집기의 기본 글꼴


if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    from ep_command import EXIT_ARGS, EXIT_SESSION, EXIT_TOOL, NEXT_EP_LOGIN, OUT_BYTES, Stop, load, size
except ImportError:                             # 형제 스킬 ep-login 이 곁에 없다 — 답의 꼴(JSON 하나 · 종료 1)은 지킨다
    print(json.dumps({"error": "tool", "message": f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"}, ensure_ascii=False))
    sys.exit(1)
from ep_session import squash  # noqa: E402 — 이름을 견주기 꼴로 누른다


class NoSuchBoard(Stop):
    """그 id · 이름의 게시판이 나무에 없다 — 받아 둔 나무였으면 새로 받아 한 번 더 가릴 까닭이다(여럿에 걸린 것과 가른다)."""


# ── 게시판 고르기 ─────────────────────────────────────────────────────────
def resolve(boards: list, word: str | None, *, leaf: bool = False) -> dict | None:
    """게시판 id 나 이름의 일부 → 나무의 한 줄. 「>」 로 가르면 칸마다 그 깊이의 이름 일부다. 여럿이면 Stop(인자)이 후보를 든다."""
    if not word:
        return None
    if re.fullmatch(r"BBS\d+", word):
        hit = [b for b in boards if b["id"] == word]
        if not hit:
            raise NoSuchBoard(EXIT_ARGS, "args", f"게시판 {word} 이 나무에 없다 — boards 로 id 를 본다")
        return hit[0]
    parts = [squash(p) for p in word.split(">") if p.strip()]
    hits = [b for b in boards if len(b["path"]) >= len(parts)
            and all(p in squash(n) for p, n in zip(parts, b["path"][-len(parts):]))]
    if leaf:
        hits = [b for b in hits if not b["folder"]] or hits
    exact = [b for b in hits if squash(b["name"]) == parts[-1]]
    pick = exact if exact else hits
    nested = [b for b in pick if not any(o is not b and b["path"][:len(o["path"])] == o["path"] for o in pick)]
    if len(pick) > 1 and len(nested) == 1 and not leaf:
        pick = nested                     # 묶음과 그 아래의 같은 이름(「안전환경 > 안전환경」) — 찾기는 묶음째 본다
    if len(pick) == 1:
        return pick[0]
    if not pick:
        raise NoSuchBoard(EXIT_ARGS, "args", f"「{word}」 에 걸리는 게시판이 없다 — boards 로 이름을 본다")
    names = " · ".join(f"{PATH_SEP.join(b['path'])}({b['id']})" for b in pick[:12])
    raise Stop(EXIT_ARGS, "args", f"「{word}」 가 게시판 여럿에 걸린다 — {names}. 다음: 하나를 id 로 다시 준다")


def board_names(boards: list) -> dict:
    return {b["id"]: PATH_SEP.join(b["path"]) for b in boards}


# ── 받아 둔 나무 ─────────────────────────────────────────────────────────
def tree_path() -> pathlib.Path:
    return pathlib.Path.home() / TREE_DIR / TREE_FILE


def kept_tree() -> list | None:
    """TREE_DAYS 안에 받은 같은 꼴의 나무 — 없거나 낡았거나 깨졌으면 None."""
    got = ep_command.kept(tree_path(), TREE_FORMAT, TREE_DAYS)
    boards = got[0].get("boards") if got else None
    return boards if isinstance(boards, list) and boards else None


def fresh_tree(app) -> list:
    """읽을 수 있는 게시판 나무를 게시판에서 받아 홈에 남기고 낸다 — 못 남겨도 받은 것은 낸다(다음 판이 다시 받을 뿐이다)."""
    boards = app.tree()
    ep_command.keep(tree_path(), {"format": TREE_FORMAT, "stamp": time.time(), "boards": boards})
    return boards


def pick_board(app, word: str | None) -> tuple[list, dict | None, bool]:
    """(나무, 고른 게시판, 나무가 받아 둔 것인가) — 받아 둔 나무로 먼저 가리고, 거기 없는 게시판이면 새로 받아 한 번 더 가린다.
    이름이 여럿에 걸린 것은 새로 안 받는다 — 후보를 대면 사람이 id 로 고른다."""
    boards = kept_tree()
    if boards is None:
        boards = fresh_tree(app)
        return boards, resolve(boards, word), False
    try:
        return boards, resolve(boards, word), True
    except NoSuchBoard:                   # 받아 둔 뒤에 생기거나 이름이 바뀐 게시판일 수 있다
        boards = fresh_tree(app)
        return boards, resolve(boards, word), False


# ── 본문 · 받는 자리 ──────────────────────────────────────────────────────
def article_dir(article_id: str) -> pathlib.Path:
    """그 글의 것(본문 글자 · 본문 그림 · 첨부)을 받는 기본 자리 — 임시 폴더 아래 SAVE_ROOT/<글 id>."""
    return pathlib.Path(tempfile.gettempdir()) / SAVE_ROOT / load("attachments", MAIL_SCRIPTS).UNSAFE_NAME.sub("_", article_id)


def ecm_note(name: str) -> bool:
    """문서함(ECM) 쪽지의 이름 꼴인가 — 꼴은 형제 스킬 company-mail 의 ``inbox`` 가 든다(메일 첨부와 한 가름 · 잰 것)."""
    return bool(load("inbox", MAIL_SCRIPTS).ECM_ATTACHMENT.match(name))


def compose(args) -> str:
    """save 의 본문 — HTML 파일은 그대로, 평문은 줄바꿈을 살려 싸고, 그림은 끝에 data URI 로 붙인다."""
    if bool(args.html_file) == bool(args.text_file):
        raise Stop(EXIT_ARGS, "args", "글은 --html-file 이나 --text-file 하나로 준다")
    src = pathlib.Path(args.html_file or args.text_file).expanduser()
    if not src.is_file():
        raise Stop(EXIT_ARGS, "args", f"글 파일이 없다: {src}")
    raw = src.read_text(encoding="utf-8").strip()
    if not raw:
        raise Stop(EXIT_ARGS, "args", "글 파일이 비었다")
    body = raw if args.html_file else f'<div style="{BODY_STYLE}">' + html_lib.escape(raw).replace("\n", "<br>") + "</div>"
    for img in args.image or []:
        p = pathlib.Path(img).expanduser()
        kind = mimetypes.guess_type(p.name)[0] or ""
        if not p.is_file() or not kind.startswith("image/"):
            raise Stop(EXIT_ARGS, "args", f"그림 파일이 아니다: {p}")
        body += f'<p><img src="data:{kind};base64,{base64.b64encode(p.read_bytes()).decode()}" alt="{html_lib.escape(p.stem)}"></p>'
    return body


# ── 명령 ────────────────────────────────────────────────────────────────
def row_out(r: dict, names: dict, shared: str | None) -> dict:
    """목록 한 줄 — 게시판 칸은 머리의 board_id(``shared``)와 다를 때만, ROW_FLAGS 는 참일 때만 싣는다."""
    out = {"id": r["id"]}
    if r["board"] != shared:
        out.update(board=r["board"], board_name=names.get(r["board"], r["board"]))
    out.update(title=r["title"], writer=r["writer"], date=r["date"], **{k: True for k in ROW_FLAGS if r[k]})
    return out


def page_rows(head: dict, rows: list, names: dict, next_page: int | None) -> dict:
    out = dict(head, rows=[row_out(r, names, head.get("board_id")) for r in rows])
    while out["rows"] and size(out) > OUT_BYTES:
        out["rows"].pop()
        out["more"] = f"줄이 답 한도에 걸려 {len(out['rows'])} 줄만 실었다 — 남은 줄은 같은 쪽에 있으니 낱말 · 기간으로 좁혀 다시 찾는다"
    if next_page:
        out["next"] = f"--page {next_page}"
    return out


def cmd_boards(app, args) -> dict:
    boards = app.tree(write=True) if args.write else fresh_tree(app)
    return {"boards": [{"id": b["id"], "path": PATH_SEP.join(b["path"]), **({"group": True} if b["folder"] else {})} for b in boards]}


def cmd_list(app, args, words: str = "", fields: tuple = ()) -> dict:
    boards, where, kept = pick_board(app, args.board if not words else args.within)
    got = app.articles(where["id"] if where else "BBS85", words=words, fields=fields, since=args.since,
                       until=args.until or "", page=args.page, count=LIST_COUNT)
    if kept and not {r["board"] for r in got["rows"]} <= set(board_names(boards)):
        boards = fresh_tree(app)          # 받아 둔 나무에 없는 게시판의 글이 왔다 — 이름을 대려면 새로 받는다
    head = {"board": PATH_SEP.join(where["path"]) if where else "모든 게시판", "total": got["total"], "page": args.page}
    if where and not where["folder"]:
        head["board_id"] = where["id"]    # 게시판 하나만 본 답 — 줄마다 되풀이하지 않고 여기 한 번 싣는다
    if words:
        head.update(words=words, fields=list(fields))
    more = args.page if got["total"] > args.page * LIST_COUNT else None
    rows = got["rows"]
    if words:   # 고정 공지는 쪽마다 맨 위에 서고 낱말과 상관없이 온다 — total 에도 안 든다(잰 것). 찾은 것과 가른다
        pinned = [{"id": r["id"], "board": r["board"], "title": r["title"]} for r in rows if r["notice"]]   # 낱말이 든 고정 공지는 찾은 줄에 안 든다(잰 것) — read 로 열 수 있게 id 를 싣는다
        rows = [r for r in rows if not r["notice"]]
        if pinned and args.page == 1:
            head["pinned_notices"] = pinned
    elif args.page > 1:
        rows = [r for r in rows if not r["notice"]]   # 고정 공지는 첫 쪽에만 싣는다
    return page_rows(head, rows, board_names(boards), more and args.page + 1)


def cmd_search(app, args) -> dict:
    fields = tuple(args.field or FIELDS)
    return cmd_list(app, args, args.words, fields)


def keep_text(article_id: str, text: str) -> pathlib.Path:
    folder = article_dir(article_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / SAVED_TEXT_FILE
    path.write_text(text, encoding="utf-8")
    return path


def cmd_read(app, args) -> dict:
    a = app.article(args.board, args.id)
    # 글자와 그림 주소가 한 번의 풀기에서 나온다 — 글자의 [그림 N] 이 주소들의 N 번째다. 누구나 쓰는 글이라 숨긴 글 · 폭 없는 문자는 걷힌다
    page = load("visible", MAIL_SCRIPTS).body(a["html"])
    text, srcs = page.text, list(page.images)
    files = app.files(args.id)
    out = {"id": args.id, "board": args.board, "title": a["title"], "writer": a["writer"], "posted": a["posted"],
           "period": a["period"], "chars": len(text), "text_file": str(keep_text(args.id, text)),
           "attachments": [{"no": i + 1, "name": f["name"], **({"ecm": True} if ecm_note(f["name"]) else {})}
                           for i, f in enumerate(files)]}
    if page.hidden:
        out["hidden"] = page.hidden
    last = {}                             # 본문 뒤에 실을 칸 — 본문을 맞출 때 그 몫을 먼저 뺀다
    if srcs and args.images:
        last["images"] = save_images(app, args.id, srcs)
    elif srcs:
        last["note"] = (f"본문 그림 {len(srcs)} 장 — 글의 [그림 N] 자리다. 그림뿐인 공지 · 식단이 흔하니, 그림에 든 것이 물음에 걸리면"
                        " 같은 명령에 --images 로 받아 그림 파일로 연다")
    ep_command.fit_text(out, "body", text, args.start, READ_MAX, lambda end: f"--from {end}", OUT_BYTES - size(last))
    out.update(last)
    return out


def save_images(app, article_id: str, srcs: list[str]) -> list[dict]:
    """본문 그림을 형제 스킬 company-mail 의 ``body_images`` 로 받는다 — 묻는 것은 앱 손(``xclick.App.image``)이 가린다."""
    images = load("body_images", MAIL_SCRIPTS)

    def fetch(src: str) -> bytes:
        xclick = sys.modules["xclick"]
        try:
            return app.image(src)
        except (xclick.SessionExpired, xclick.SessionMissing):
            raise                          # 끊긴 세션은 명령 전체가 다시 세운다 — 「안 받았다」로 낮추지 않는다
        except xclick.AppError as exc:     # 게시판 밖 · 거절 · 못 닿음 — 그 그림만 안 받는다
            raise images.Refused(str(exc)) from exc

    return images.save(srcs, fetch, article_dir(article_id) / IMAGES_DIR)


def cmd_attachment(app, args) -> dict:
    files = app.files(args.id)
    notes = [ecm_note(f["name"]) for f in files]      # 문서함 쪽지인가 — 첨부 차례대로
    rows = [{"no": i + 1, "name": f["name"], "bytes": f["size"], **({"ecm": True} if notes[i] else {})}
            for i, f in enumerate(files)]
    if not args.save:
        return {"id": args.id, "attachments": rows, **({"next": "받으려면 --save <번호> 나 --save all"} if rows else {})}
    if args.save == "all":
        picks = list(range(len(files)))
    elif args.save.isdigit() and 1 <= int(args.save) <= len(files):
        picks = [int(args.save) - 1]
    else:
        raise Stop(EXIT_ARGS, "args", f"첨부 번호가 아니다: {args.save!r} — 1 부터 {len(files)} 까지")
    out_dir = pathlib.Path(args.out).expanduser() if args.out else article_dir(args.id)
    hand = load("attachments", MAIL_SCRIPTS)
    # 저장 이름은 이 글에서 파일로 남길 첨부 전부를 두고 가른다 — 같은 이름 · 이 자리에 따로 쓰는 본문 파일 · 그림 폴더와 안 겹친다
    names = hand.file_names({i + 1: f["name"] for i, f in enumerate(files) if not notes[i]}, reserved=(SAVED_TEXT_FILE, IMAGES_DIR))
    got = []
    for i in picks:
        f = files[i]
        data = app.download(f["id"])
        if notes[i]:
            k = load("inbox", MAIL_SCRIPTS).ecm_note_key(data.decode("utf-8", "replace"))   # 화면이 여는 링크 쪽 열쇠 — 메일과 한 가름
            if not k:
                raise Stop(EXIT_TOOL, "tool", f"문서함 쪽지에 문서 열쇠가 없다: {f['name']} — 쪽지 꼴이 잰 것과 다르다")
            got.append({"no": i + 1, "name": f["name"], "ecm_key": k, "next": f"스킬 company-ecm 의 read {k} 로 연다"})
            continue
        path, note = hand.keep(out_dir, names[i + 1], f["name"], data)
        got.append({"no": i + 1, "name": f["name"], "path": str(path), "bytes": len(data), **({"note": note} if note else {})})
    return {"id": args.id, "saved": got}


def cmd_drafts(app, args) -> dict:
    return app.drafts()


def hand(verb: str, *extra: str) -> dict:
    """짓는 손(``draft_board.js``)을 부른다 — 쓰는 사람의 Edge 에서 게시판 화면을 다룬다. 손의 종료 값을 이 명령의 것으로 옮긴다."""
    script = os.environ.get("DRAFT_BOARD_HAND", "").strip() or str(HERE / DRAFT_HAND)   # 대역은 검사만 세운다
    try:
        ran = ep_session.run_hand(script, [verb, *extra], timeout=DRAFT_HAND_SECONDS)
    except ep_session.NoNode as exc:
        raise Stop(EXIT_TOOL, "tool", "node 가 없다 — 짓는 손은 node 로 돈다. 설치를 다시 돌린다") from exc
    except ep_session.TimedOut as exc:
        raise Stop(EXIT_TOOL, "tool", f"짓는 손이 {DRAFT_HAND_SECONDS} 초 안에 안 끝났다 — drafts 로 섰는지 본다") from exc
    if ran.code == 0:
        return ran.answer
    word = ran.said or "짓는 손이 까닭 없이 멈췄다"
    if ran.code == EXIT_SESSION:
        raise Stop(EXIT_SESSION, "session", f"{word}. {NEXT_EP_LOGIN}")
    raise Stop(EXIT_ARGS if ran.code == EXIT_ARGS else EXIT_TOOL, "args" if ran.code == EXIT_ARGS else "tool", word)


def cmd_save(app, args) -> dict:
    where = resolve(app.tree(write=True), args.board, leaf=True)
    if where is None or where["folder"]:
        raise Stop(EXIT_ARGS, "args", "글은 묶음이 아닌 게시판 하나에 쓴다 — boards --write 로 고른다")
    files = [str(pathlib.Path(f).expanduser().resolve()) for f in args.file or []]
    for f in files:
        if not pathlib.Path(f).is_file():
            raise Stop(EXIT_ARGS, "args", f"첨부 파일이 없다: {f}")
    body = compose(args)
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tmp:
        tmp.write(body)
    try:
        extra = ["--board", where["id"], "--title", args.title, "--body-file", tmp.name]
        for f in files:
            extra += ["--file", f]
        got = hand("save", *extra)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    return dict(got, board_name=PATH_SEP.join(where["path"]), saved="임시보관함에 저장했다(아직 게시 안 됨)",
                next="사람이 띄운 편집 창에서 보고 [등록]을 누르면 게시된다 — 고칠 것이 있으면 그 창에서 고친다")


def cmd_show(app, args) -> dict:
    return hand("show", args.id, "--board", args.board)


COMMANDS = {"boards": cmd_boards, "list": cmd_list, "search": cmd_search, "read": cmd_read, "attachment": cmd_attachment,
            "drafts": cmd_drafts, "save": cmd_save, "show": cmd_show}
NEEDS_APP = set(COMMANDS) - {"show"}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="board.py", description="사내 게시판을 찾고 읽고, 글을 임시저장한다")
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("boards")
    b.add_argument("--write", action="store_true")
    for name in ("list", "search"):
        s = sub.add_parser(name)
        if name == "list":
            s.add_argument("board", nargs="?")
        else:
            s.add_argument("words")
            s.add_argument("--in", dest="within")
            s.add_argument("--field", action="append", choices=FIELDS)
        s.add_argument("--since", default="1990-01-01")
        s.add_argument("--until")
        s.add_argument("--page", type=int, default=1)
    r = sub.add_parser("read")
    r.add_argument("id")
    r.add_argument("--board", required=True)
    r.add_argument("--from", dest="start", type=int, default=0)
    r.add_argument("--images", action="store_true")
    a = sub.add_parser("attachment")
    a.add_argument("id")
    a.add_argument("--save")
    a.add_argument("--out")
    sub.add_parser("drafts")
    s = sub.add_parser("save")
    s.add_argument("--board", required=True)
    s.add_argument("--title", required=True)
    s.add_argument("--html-file")
    s.add_argument("--text-file")
    s.add_argument("--image", action="append")
    s.add_argument("--file", action="append")
    w = sub.add_parser("show")
    w.add_argument("id")
    w.add_argument("--board", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    if args.command == "list":
        args.within = None
    run = COMMANDS[args.command]

    def work(xclick) -> dict:
        if args.command not in NEEDS_APP:
            return run(None, args)
        return ep_session.session_first(lambda f: run(xclick.App(f), args), expired=(xclick.SessionExpired, xclick.SessionMissing))

    def shown(xclick) -> dict:
        """게시판에서 온 글이 어느 칸으로 나가든 보이지 않는 문자(폭 없는 문자 · 방향 뒤집기)를 걷는다 — 나가는 문 하나."""
        return load("visible", MAIL_SCRIPTS).shown(work(xclick))

    return ep_command.finish(shown, "xclick", HERE, args_errors=("NotFound",))   # 글 id 와 게시판 id 가 안 맞는 것은 인자가 틀린 것이다


if __name__ == "__main__":
    sys.exit(main())
