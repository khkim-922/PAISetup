"""게시판 스킬의 얇은 명령 — 곁의 손(``xclick.py`` 읽기 · ``draft_board.js`` 짓기)으로 사내 게시판을 찾고 읽고, 글을 임시저장한다.

부르는 꼴 · 명령마다의 인자 · 답의 칸 · 종료 값은 ``--help`` 가 낸다 — 그 글은 이 파일의 표(``READS`` · ``WRITE_STARTS`` ·
``WRITE_CHANGES`` · ``NOT_HERE`` · ``EXITS``)와 argparse 에서 서고, 이 머리말은 고치는 사람이 읽는 계약만 든다.

- 세션 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 가 쥔다. ``save`` 의 인자 · 파일 · 표에 없는 조합은 세션 전에 다 가린다(``write_plan``)
- 읽기 — 게시판에 아무것도 안 남긴다(조회수를 안 올리는 길은 ``xclick.py`` 머리말). 게시판 나무는 홈에 받아 두고(``TREE_DAYS``) ``boards`` 는
  늘 새로 받는다
- 본문 · 첨부 — 본문은 형제 스킬 company-mail 의 ``visible`` 이, 본문 그림은 ``body_images`` 가, 첨부 이름과 저장은 ``attachments`` 가, 문서함
  쪽지의 꼴과 열쇠는 ``inbox`` 가 든다. 꼴과 까닭은 ``references/DESIGN.md``
- 짓기 — ``save`` · ``show`` 는 짓는 손을 node 로 부르고 그 손의 종료 값을 이 명령의 것으로 옮긴다(``hand``). 두 표가 같아야 하는 까닭은
  ``WRITE_STARTS`` 위의 주석
- 내는 것 — 표준 출력에 JSON 하나 · ``OUT_BYTES`` 를 안 넘는다(``ep_command.finish`` · ``fit_text``)
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import html as html_lib
import json
import mimetypes
import os
import pathlib
import re
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
# 형제 스킬 — 본문을 푸는 손(``visible``) · 본문 그림을 받는 손(``body_images``) · 첨부 가름(``attachments``) · ECM 쪽지의 꼴과 열쇠(``inbox``)가 사는 자리
MAIL_SCRIPTS = HERE.parents[1] / "company-mail" / "scripts"
DRAFT_HAND = "draft_board.js"     # 글을 화면에서 짓는 손 — 이 파일 곁
DRAFT_HAND_SECONDS = 330          # 그 손 한 판의 시한 — 대화 도구의 명령 시한보다 짧아야 끊겨도 답이 온다
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


@dataclasses.dataclass(frozen=True)
class Flag:
    """바꿀 것 하나가 받는 인자 하나."""
    option: str          # 인자 — 「--html-file」
    meta: str            # --help 의 자리 말
    many: bool = False   # 여러 번 준다

    @property
    def dest(self) -> str:
        return self.option.lstrip("-").replace("-", "_")


@dataclasses.dataclass(frozen=True)
class Start:
    """글 짓기의 출발 하나 — 게시판의 화면 하나다."""
    word: str        # 사람 말
    screen: str      # 그 화면이 무엇을 든 채 열리나 — --help 의 지도
    takes: str       # --id 로 받는 것의 말 — 빈 글자면 --id 를 안 받는다
    needs: tuple     # 꼭 받는 바꿀 것의 이름 — 빈 화면이면 다 준다
    proof: str       # 저장이 섰나를 무엇으로 가리나
    unmeasured: str = ""   # 회사에서 안 잰 채 지은 출발이면 안 잰 것 — save --help 의 지도가 「회사에서 안 쟀다」로 낸다


@dataclasses.dataclass(frozen=True)
class Change:
    """글 짓기의 바꿀 것 하나 — 손가락 하나다."""
    flags: tuple     # 받는 인자(Flag)
    starts: tuple    # 받는 출발
    word: str        # 사람 말 — 「 — 」 앞이 이름이다
    elsewhere: str = ""   # 받지 않는 출발에서 그 일을 어디서 하나 — 명령이 멈추며 댄다


# 글 짓기의 손가락 — 출발 하나 × 바꿀 것 아무 조합 → [임시저장]. 손가락을 더하거나 빼는 일은 이 두 표의 줄과 짓는 손(draft_board.js)의
# STARTS · CHANGES 의 줄 하나다. 인자 · 거르기 · save --help 의 지도가 다 이 표에서 선다.
# ⚠ 출발 이름 · 바꿀 것 이름 · 출발마다 받는 것(starts)과 꼭 받는 것(needs)은 짓는 손의 표와 같아야 한다 — 한쪽에만 더하면 이 명령이 받은
# 손가락을 짓는 손이 거절하거나 그 반대다. 설정 저장소의 게시판 검사가 두 표를 맞춰 본다
WRITE_STARTS = {
    "new": Start("새 글", "[글쓰기] 창 — 빈 창에 게시판 · 제목 · 글을 넣는다", "", ("board", "title", "body"),
                 "임시보관함에 그 제목의 새 글이 서면 섰다"),
    "draft": Start("임시글", "임시보관함 글의 편집 창 — 저장된 제목 · 게시판 · 본문 · 첨부가 든 채 열린다. 쓰는 사람이 그 글을 열어 두었으면 "
                   "그 창에서 고친다(둘째 창을 안 연다 · 그 창에서 사람이 고치던 것도 함께 저장된다)", "임시글 id(drafts 의 id)", (),
                   "임시보관함의 그 글 줄(제목 · 날짜)이 바뀌면 섰다. 줄이 안 바뀌면 「못 가렸다」(종료 1)고 편집 창을 띄워 둔다",
                   "편집 창에서 고쳐 [임시저장]하는 한 판 — 같은 글이 고쳐지나 · 새 임시글로 갈라지나 · 더한 첨부가 묶이나 · 쓰는 사람이 연 창이 "
                   "어떻게 되나. 답이 「섰다」여도 사람에게 띄운 창에서 보고 확인받는다"),
}
WRITE_CHANGES = {
    "board": Change((Flag("--board", "게시판"),), ("new",),
                    "게시판 — 묶음이 아닌 게시판 하나(id 나 이름의 일부 · boards --write)",
                    "임시글의 게시판은 띄운 편집 창에서 사람이 고른다 — 고르면 화면이 본문 틀을 다시 실어 본문이 지워진다"),
    "title": Change((Flag("--title", "제목"),), ("new", "draft"), "제목 — 앞뒤 빈칸은 걷힌다"),
    "body": Change((Flag("--html-file", "파일"), Flag("--text-file", "파일"), Flag("--image", "그림", many=True)), ("new", "draft"),
                   "글 — 통째로. HTML 조각이나 평문 파일 하나 · --image 의 그림은 그 글 끝에 차례로 붙는다. 임시글은 있던 글 · 그림이 다 이 글로 간다"),
    "files": Change((Flag("--file", "첨부", many=True),), ("new", "draft"), "첨부 — 파일을 더한다. 있던 첨부는 그대로다"),
}
WRITE_END = "[임시저장]만 누르고 그 글의 편집 창을 띄워 둔다. [등록](게시)은 사람이 그 창에서 보고 누른다"
WRITE_NOT_YET = ("글 일부 바꾸기 · 첨부 빼기 · 임시글의 게시판 바꾸기 · 말머리 · 게시기한 · 공개 범위 · 다른 글 재사용 — 회사에서 안 잰 화면 "
                 "동작이라 손가락이 없다. 띄운 편집 창에서 사람이 한다")
NOT_HERE = ("[등록](게시) · 게시된 글 고치기 · 지우기 · 의견(댓글) · 추천 · 열람 권한(비공개 · 대상자) · 예약 게시 — 손에 없다. 사람이 띄운 편집 "
            "창 · 게시판 화면에서 한다. 사람이 「바로 게시해」라고 해도 임시저장과 창 띄우기까지다")
EXITS = ("0 됐다 · 1 도구 · 앱 고장 · 임시글의 저장이 섰는지 못 가렸다(그대로 알리고 다시 부르지 않는다) · 2 인자가 틀렸다(게시판 이름이 여럿에 "
         "걸리면 후보를 든다 · 글 id 와 게시판 id 가 안 맞음 · 그 출발이 안 받는 바꿀 것) · 게시판이 저장을 막았다 · 3 사내 세션이 없다 · 끊겼다"
         "(스킬 ep-login 을 부른 뒤 같은 명령을 다시). 0 이 아니면 message 가 까닭과 「다음: …」 을 든다")


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
    """문서함(ECM) 쪽지의 이름 꼴인가 — 꼴은 형제 스킬 company-mail 의 ``inbox`` 가 든다(메일 첨부와 한 가름)."""
    return bool(load("inbox", MAIL_SCRIPTS).ECM_ATTACHMENT.match(name))


def compose(args) -> str:
    """save 의 본문 — HTML 파일은 그대로, 평문은 줄바꿈을 살려 싸고, 그림은 끝에 data URI 로 붙인다."""
    if bool(args.html_file) == bool(args.text_file):
        raise Stop(EXIT_ARGS, "args", "글은 --html-file 이나 --text-file 하나로 준다 — --image 의 그림은 그 글 끝에 붙는다")
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
    scope = {"bbs_id": where["id"]} if where else {}          # 안 주면 앱 손의 기본 — 나무의 뿌리(모든 게시판)
    if args.since:
        scope["since"] = args.since                            # 안 주면 앱 손의 기본 — 처음부터
    got = app.articles(**scope, words=words, fields=fields, until=args.until or "", page=args.page, count=LIST_COUNT)
    if kept and not {r["board"] for r in got["rows"]} <= set(board_names(boards)):
        boards = fresh_tree(app)          # 받아 둔 나무에 없는 게시판의 글이 왔다 — 이름을 대려면 새로 받는다
    head = {"board": PATH_SEP.join(where["path"]) if where else "모든 게시판", "total": got["total"], "page": args.page}
    if where and not where["folder"]:
        head["board_id"] = where["id"]    # 게시판 하나만 본 답 — 줄마다 되풀이하지 않고 여기 한 번 싣는다
    if words:
        head.update(words=words, fields=list(fields))
    more = args.page if got["total"] > args.page * LIST_COUNT else None
    rows = got["rows"]
    if words:   # 고정 공지는 쪽마다 맨 위에 서고 낱말과 상관없이 온다 — total 에도 안 든다. 찾은 것과 가른다
        pinned = [{"id": r["id"], "board": r["board"], "title": r["title"]} for r in rows if r["notice"]]   # 낱말이 든 고정 공지는 찾은 줄에 안 든다 — read 로 열 수 있게 id 를 싣는다
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
    notes = [ecm_note(f["name"]) for f in files]
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


def change_name(change: Change) -> str:
    return change.word.split(" — ")[0]


def write_fingers(args) -> list[str]:
    """이 부름이 받은 바꿀 것의 이름 — 출발이 안 받는 것 · 꼭 받을 것이 빠진 것 · --id 의 있고 없음이 출발과 안 맞는 것은 게시판도 화면도
    부르기 전에 Stop(인자)."""
    start = WRITE_STARTS[args.start]
    got = [name for name, ch in WRITE_CHANGES.items() if any(getattr(args, f.dest) not in (None, []) for f in ch.flags)]
    for name in got:
        ch = WRITE_CHANGES[name]
        if args.start not in ch.starts:
            raise Stop(EXIT_ARGS, "args", f"{start.word} 출발에는 「{change_name(ch)}」 손가락이 없다. {ch.elsewhere}")
    missing = [change_name(WRITE_CHANGES[n]) for n in start.needs if n not in got]
    if missing:
        raise Stop(EXIT_ARGS, "args", f"{start.word} 출발에 꼭 줄 것이 빠졌다: {' · '.join(missing)} — save --help 의 지도를 본다")
    if not got:
        raise Stop(EXIT_ARGS, "args", f"{start.word} 출발은 바꿀 것을 하나는 받는다 — 편집 창을 띄우기만 하려면 show")
    if start.takes and not args.id:
        raise Stop(EXIT_ARGS, "args", f"{start.word} 출발은 --id 로 {start.takes} 를 받는다")
    if not start.takes and args.id:
        raise Stop(EXIT_ARGS, "args", f"{start.word} 출발은 --id 를 안 받는다")
    return got


def write_map() -> str:
    """save --help 의 지도 — 두 표에서 짓는다."""
    out = ["출발(--start) — 화면 하나를 연다"]
    for name, s in WRITE_STARTS.items():
        takes = f" · --id 로 {s.takes}" if s.takes else ""
        needs = f" · 꼭 받는다: {' · '.join(change_name(WRITE_CHANGES[n]) for n in s.needs)}" if s.needs else ""
        out.append(f"  {name:6} {s.word}: {s.screen}{takes}{needs}\n         저장을 가리는 법: {s.proof}")
        if s.unmeasured:
            out.append(f"         회사에서 안 쟀다: {s.unmeasured}")
    out.append("바꿀 것 — 한 부름에 아무 조합을 한 화면에 넣는다")
    for ch in WRITE_CHANGES.values():
        flags = " | ".join(f.option for f in ch.flags)
        out.append(f"  {flags}  [{' · '.join(ch.starts)}]  {ch.word}")
    out.append(f"끝 — {WRITE_END}")
    out.append(f"아직 없는 손가락 — {WRITE_NOT_YET}")
    return "\n".join(out)


@dataclasses.dataclass(frozen=True)
class WritePlan:
    """세션 · 게시판 · 화면을 부르기 전에 가린 글 짓기 — 받은 바꿀 것 · 걷은 제목 · 첨부의 절대 경로 · 지은 본문(없으면 None)."""
    changes: list
    title: str | None
    files: list
    body: str | None


def write_plan(args) -> WritePlan:
    """save 의 인자를 다 가린다 — 하나라도 걸리면 Stop(인자). 세션도 게시판도 안 부른다."""
    got = write_fingers(args)
    title = None if args.title is None else args.title.strip()
    if title == "":
        raise Stop(EXIT_ARGS, "args", "--title 이 비었다")
    files = [str(pathlib.Path(f).expanduser().resolve()) for f in args.file or []]
    for f in files:
        if not pathlib.Path(f).is_file():
            raise Stop(EXIT_ARGS, "args", f"첨부 파일이 없다: {f}")
    return WritePlan(got, title, files, compose(args) if "body" in got else None)


def cmd_save(app, args, plan: WritePlan | None = None) -> dict:
    plan = plan or write_plan(args)
    title, files, body = plan.title, plan.files, plan.body
    extra = ["--start", args.start]
    if args.start == "draft":
        row = next((r for r in app.drafts()["rows"] if r["id"] == args.id), None)
        if row is None:
            raise Stop(EXIT_ARGS, "args", f"임시보관함 첫 쪽에 {args.id} 가 없다 — drafts 로 임시글 id 를 본다")
        extra += ["--id", args.id, "--at", row["board"]]
        board_name = board_names(kept_tree() or []).get(row["board"], row["board"])
    else:
        where = resolve(app.tree(write=True), args.board, leaf=True)
        if where is None or where["folder"]:
            raise Stop(EXIT_ARGS, "args", "글은 묶음이 아닌 게시판 하나에 쓴다 — boards --write 로 고른다")
        extra += ["--board", where["id"]]
        board_name = PATH_SEP.join(where["path"])
    if title is not None:
        extra += ["--title", title]
    for f in files:
        extra += ["--file", f]
    tmp = None
    if body is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tmp:
            tmp.write(body)
        extra += ["--body-file", tmp.name]
    try:
        out = hand("save", *extra)
    finally:
        if tmp is not None:
            pathlib.Path(tmp.name).unlink(missing_ok=True)
    out.update(board_name=board_name, saved="임시보관함에 저장했다(아직 게시 안 됨)",
               next=f"사람이 띄운 편집 창에서 보고 [등록]을 누르면 게시된다 — 더 고칠 것은 save --start draft --id {out.get('id')} 로")
    if out.get("forked_from"):
        out["note"] = (f"임시글 {out['forked_from']} 은 그대로 남고 고친 판이 새 임시글로 저장됐다 — 임시보관함에 둘이 있다. 띄운 창(새 글)을 보고"
                       " [등록]하도록 이른다")
    return out


def cmd_show(app, args) -> dict:
    return hand("show", args.id, "--board", args.board)


def board_word() -> str:
    """게시판 인자의 말 — list · search · save 가 함께 쓴다."""
    return "게시판 id(BBS…)나 이름의 일부(「식단」 · 「업무공지」 · 「일반사항 > 기타」) — 묶음이면 그 아래를 다 본다. 이름이 여럿에 걸리면 종료 2 가 후보를 든다"


# 명령마다 (한 줄 — 맨 위 --help 의 지도와 명령 목록, 그 명령의 --help 에 덧붙는 답의 칸). --help 는 이 표와 글 짓기의 두 표에서만 선다
READS = {
    "boards": ("게시판 나무 — id · 경로 · 묶음(group). --write 는 글을 쓸 수 있는 곳만(늘 게시판에서 새로 받는다)",
               "답: boards — 줄마다 id · path, 묶음 게시판이면 group"),
    "list": ("새 글부터 목록 — 게시판 · 기간으로 좁힌다(기간을 안 주면 처음부터 오늘까지)",
             f"답: board(본 게시판) · page · total(다 센 수) · rows(한 쪽 {LIST_COUNT} 줄 — id · title · writer · date, 참일 때만 notice(고정 공지) · files(첨부 있음)) · "
             "next(다음 --page) · more(답 한도에 걸려 줄을 덜었다). 게시판 하나만 본 답은 머리에 board_id 를 한 번 싣고, 줄의 board · board_name 은 "
             "그와 다를 때만 든다. 고정 공지는 첫 쪽에만 싣는다"),
    "search": ("낱말 찾기 — 기본 칸은 제목 · 내용 · 작성자 · 첨부 이름 넷(칸끼리는 「또는」)",
               f"답: list 와 같다 — total · rows(한 쪽 {LIST_COUNT} 줄) · next · more · words · fields. pinned_notices 는 쪽마다 맨 위에 고정된 "
               "공지라 찾은 것이 아니다 — 낱말이 든 고정 공지는 rows 에 안 드니 그 id 로 read 한다"),
    "read": ("글 한 건 — 본문 글자 · 첨부 목록(조회수를 안 올린다). --images 면 본문 그림 파일",
             f"답: title · writer · posted · period · attachments(no · name, 문서함 쪽지면 ecm) · body(한 번에 {READ_MAX} 자까지 · 줄 끝에서 "
             "끊는다) · more(다음 --from) · text_file(본문 글자 전부 — 긴 글은 이 파일을 나눠 읽어도 된다) · chars. 사람 눈에 안 보이게 감춘 글은 "
             "걷히고 그 덩이 수가 hidden 이다. 그림 자리는 「[그림 N]」 이고, 그림이 있으면 note 가 그 수를 든다. --images 면 images — 줄마다 no(「[그림 "
             "N]」 의 N) · path(큰 그림은 줄여 받는다 · note 가 서면 못 줄인 것), 안 받은 그림은 skipped 에 까닭(게시판 밖 · 아이콘 · 못 읽는 꼴), "
             "같은 그림은 same_as"),
    "attachment": ("첨부 목록 · 받기 — 문서함(ECM) 쪽지는 파일 대신 문서 열쇠",
                   f"답: --save 없이는 attachments(no · name · bytes · ecm). --save 면 saved — 파일은 path · bytes(DRM 이면 note 가 다음 손을 "
                   f"말한다), 문서함 쪽지는 ecm_key(스킬 company-ecm 의 read 로 연다). --out 을 안 주면 임시 폴더 아래 {SAVE_ROOT}/<글 id> 에 받는다"),
    "drafts": ("임시 · 예약보관함 — save --start draft 의 --id 와 show 의 글 id · 게시판 id",
               "답: rows — 첫 쪽(50 줄)의 줄마다 id · board(게시판 id) · title · date · state"),
    "save": ("⚠ 글 짓기 — 출발 화면 하나를 열고 바꿀 것을 아무 조합으로 넣어 [임시저장]만 한다(등록은 안 한다)",
             "답: id · start · board · board_name · title · files(더한 첨부 수) · where(띄운 창) · saved · next. reused 가 서면 쓰는 사람이 연 창에서 고쳤다 — 그 창에서 "
             "사람이 고치던 것도 함께 저장됐다. forked_from 이 서면 임시글이 새 임시글로 갈라졌다(옛 글은 남는다 · note 를 그대로 전한다)"),
    "show": ("임시보관함 글을 편집 창으로 띄운다 — 이미 열린 창이 있으면 앞으로 올린다",
             "답: id · board · where(쓰는 사람이 연 창 · 새 창)"),
}


def top_map() -> str:
    """맨 위 --help 의 지도 — READS · 글 짓기의 두 표 · NOT_HERE · EXITS 에서 짓는다."""
    out = ["읽기 — 게시판에 아무것도 안 남긴다(조회수도 안 올린다)"]
    out += [f"  {name:11} {READS[name][0]}" for name in ("boards", "list", "search", "read", "attachment", "drafts")]
    out.append(f"\n글 짓기 — save 한 번이 게시판 화면 한 판: 출발 하나 × 바꿀 것 아무 조합 → {WRITE_END}. 바꿀 것이 여럿이면 한 번에 준다")
    out.append("출발(--start)")
    for name, st in WRITE_STARTS.items():
        takes = f" · --id <{st.takes}>" if st.takes else ""
        out.append(f"  {name:6} {st.word}{takes} — {st.screen}" + (" · 회사에서 안 쟀다" if st.unmeasured else ""))
    out.append("바꿀 것 (● 꼭 든다 · ○ 받는다 · △ 받되 회사에서 안 쟀다 · — 없다)")
    for key, ch in WRITE_CHANGES.items():
        marks = " ".join(f"{name}{'●' if key in st.needs else ('—' if name not in ch.starts else ('△' if st.unmeasured else '○'))}"
                         for name, st in WRITE_STARTS.items())
        out.append(f"  {' · '.join(f.option for f in ch.flags):38} {marks:12} {ch.word}")
    out += [f"  — 의 자리({change_name(ch)}): {ch.elsewhere}" for ch in WRITE_CHANGES.values() if ch.elsewhere]
    out.append(f"아직 없는 손가락 — {WRITE_NOT_YET}")
    out.append("\n창 띄우기 — 저장한 임시글을 사람이 보고 [등록]하게")
    out.append(f"  {'show':11} {READS['show'][0]}")
    out.append(f"\n안 하는 것 — {NOT_HERE}")
    out.append(f"종료 값 — {EXITS}")
    out.append("답은 표준 출력의 JSON 하나다. 명령마다의 인자와 답의 칸은 <명령> --help")
    return "\n".join(out)


COMMANDS = {"boards": cmd_boards, "list": cmd_list, "search": cmd_search, "read": cmd_read, "attachment": cmd_attachment,
            "drafts": cmd_drafts, "save": cmd_save, "show": cmd_show}
NEEDS_APP = set(COMMANDS) - {"show"}


def parser() -> argparse.ArgumentParser:
    raw = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(prog="board.py", description="사내 게시판 — 찾기 · 읽기 · 첨부 받기 · 글 임시저장(등록은 사람이)",
                                epilog=top_map(), formatter_class=raw)
    sub = p.add_subparsers(dest="command", required=True, metavar="<명령>")

    def command(name: str, **extra) -> argparse.ArgumentParser:
        line, answer = READS[name]
        # help 를 안 준다 — 명령마다의 한 줄은 맨 위 지도(epilog)가 묶음째 내고, 여기서도 주면 같은 줄이 두 번 찍힌다
        return sub.add_parser(name, description=f"{line}\n\n{answer}", formatter_class=raw, **extra)

    b = command("boards")
    b.add_argument("--write", action="store_true", help="글을 쓸 수 있는 게시판만")
    for name in ("list", "search"):
        s = command(name)
        if name == "list":
            s.add_argument("board", nargs="?", metavar="게시판", help=board_word() + ". 안 주면 모든 게시판")
        else:
            s.add_argument("words", metavar="말", help="찾을 말 — 빈칸이 든 말은 따옴표로 한 덩이")
            s.add_argument("--in", dest="within", metavar="게시판", help=board_word() + ". 안 주면 모든 게시판")
            s.add_argument("--field", action="append", choices=FIELDS, help="찾는 칸 — 여러 번 준다. 안 주면 넷 다. 사람 이름이면 writer, "
                                                                           "양식 · 파일이면 filename, 제목에 들 말이면 title")
        s.add_argument("--since", metavar="YYYY-MM-DD", help="이날부터 — 안 주면 처음부터(처음부터 찾기는 3 초 남짓, 6 개월이면 0.5 초 안쪽)")
        s.add_argument("--until", metavar="YYYY-MM-DD", help="이날까지 — 안 주면 오늘까지")
        s.add_argument("--page", type=int, default=1, metavar="N", help=f"쪽 — 한 쪽 {LIST_COUNT} 줄 · 답의 next 가 다음 쪽을 댄다(기본 1)")
    r = command("read")
    r.add_argument("id", metavar="글_id", help="목록 줄의 id")
    r.add_argument("--board", required=True, metavar="게시판_id", help="게시판 id — 목록 줄의 board, 없으면 답 머리의 board_id")
    r.add_argument("--from", dest="start", type=int, default=0, metavar="N", help="본문을 N 째 글자부터 — 답의 more 가 댄다(기본 0)")
    r.add_argument("--images", action="store_true", help="본문 그림을 파일로 받아 낸다 — 그림뿐인 공지 · 식단이 흔하다")
    a = command("attachment")
    a.add_argument("id", metavar="글_id", help="목록 줄의 id")
    a.add_argument("--save", metavar="번호|all", help="받을 첨부 — attachments 의 no 하나나 all. 안 주면 목록만")
    a.add_argument("--out", metavar="폴더", help=f"받을 폴더 — 안 주면 임시 폴더 아래 {SAVE_ROOT}/<글 id>")
    command("drafts")
    s = command("save", epilog=write_map())
    s.add_argument("--start", required=True, choices=list(WRITE_STARTS),
                   help=" · ".join(f"{name}: {st.word}" for name, st in WRITE_STARTS.items()) + " — 아래 지도")
    s.add_argument("--id", help=" · ".join(f"{name}: {st.takes}" for name, st in WRITE_STARTS.items() if st.takes))
    for change in WRITE_CHANGES.values():
        for flag in change.flags:
            s.add_argument(flag.option, dest=flag.dest, metavar=flag.meta, action="append" if flag.many else "store",
                           help=change_name(change) + (" — 여러 번 준다" if flag.many else ""))
    w = command("show")
    w.add_argument("id", metavar="글_id", help="drafts 의 id")
    w.add_argument("--board", required=True, metavar="게시판_id", help="그 글의 게시판 id — drafts 줄의 board")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.command == "list":
        args.within = None
    run = COMMANDS[args.command]

    def work(xclick) -> dict:
        if args.command not in NEEDS_APP:
            return run(None, args)
        extra = (write_plan(args),) if args.command == "save" else ()   # 표에 없는 조합 · 없는 파일은 세션도 안 받고 멈춘다
        return ep_session.session_first(lambda f: run(xclick.App(f), args, *extra), expired=(xclick.SessionExpired, xclick.SessionMissing))

    return ep_command.finish(work, "xclick", HERE, args_errors=("NotFound",))   # 글 id 와 게시판 id 가 안 맞는 것은 인자가 틀린 것이다


if __name__ == "__main__":
    sys.exit(main())
