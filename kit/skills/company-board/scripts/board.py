"""게시판 스킬의 얇은 명령 — 곁의 손(``xclick.py`` 읽기 · ``draft_board.js`` 짓기)으로 사내 게시판을 찾고 읽고, 글을 임시저장한다.

부르는 꼴 · 명령마다의 인자 · 답의 칸 · 종료 값은 ``--help`` 가 낸다 — 그 글은 이 파일의 표(``READS`` · ``WRITE_STARTS`` ·
``WRITE_CHANGES`` · ``NOT_HERE`` · ``EXITS``)와 argparse 에서 서고, 이 머리말은 고치는 사람이 읽는 계약만 든다.

- 세션 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 가 쥔다. ``save`` 의 인자 · 파일 · 표에 없는 조합(``write_plan``), ``list`` · ``search`` 의
  기간 · 제외할 말(``list_scope``)은 세션 전에 다 가린다
- 읽기 — 게시판에 아무것도 안 남긴다(조회수를 안 올리는 길은 ``xclick.py`` 머리말). 게시판 나무는 홈에 받아 두고(``TREE_DAYS``) ``boards`` 는
  늘 새로 받는다
- 본문 · 첨부 — 본문은 형제 스킬 company-mail 의 ``visible`` 이, 본문 그림은 ``body_images`` 가, 첨부 이름과 저장은 ``attachments`` 가, 문서함
  쪽지의 꼴과 열쇠는 ``inbox`` 가 든다. 꼴과 까닭은 ``references/DESIGN.md``
- 짓기 — ``save`` · ``show`` 는 짓는 손을 node 로 부르고 그 손의 종료 값을 이 명령의 것으로 옮긴다(``hand``). 출발마다 꼭 받는 것과 바꿀
  것마다의 이름 · 받는 출발은 짓는 손과 함께 읽는 표 파일(``FINGERS_FILE``) 한 벌이 든다 — ``WRITE_STARTS`` 위의 주석
- 내는 것 — 표준 출력에 JSON 하나 · ``OUT_BYTES`` 를 안 넘는다(``ep_command.finish`` · ``fit_text``)
"""

from __future__ import annotations

import argparse
import base64
import contextlib
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
FINGERS_FILE = "write_fingers.json"   # 글 짓기 손가락 표의 한 벌 — 이 파일 곁 · 짓는 손과 함께 읽는다
DRAFT_HAND_SECONDS = 330          # 그 손 한 판의 시한 — 대화 도구의 명령 시한보다 짧아야 끊겨도 답이 온다
SAVE_ROOT = "company-board"       # 첨부를 받는 기본 자리 — 임시 폴더 아래
IMAGES_DIR = "body-images"        # read --images 가 본문 그림을 받는 자리 — 그 글의 첨부 자리 아래
FIELDS = ("title", "contents", "writer", "filename", "deptname")   # 찾는 칸 — 화면의 검색조건(넷과 「조건더보기」 의 부서명)
DEFAULT_FIELDS = FIELDS[:4]       # 칸을 안 주면 — 제목 · 내용 · 작성자 · 첨부 이름
LIST_COUNT = 20                   # list · search 한 쪽의 줄 수
TREE_DAYS = 7                     # 받아 둔 게시판 나무를 다시 안 받고 쓰는 날 — 게시판은 드물게 생기고, 받으려면 묶음마다 한 번씩 물어야 한다
TREE_DIR = ".company-board"       # 받아 둔 나무의 자리 — 홈 아래(임시 폴더는 정리 도구가 지운다)
TREE_FILE = "boards.json"
TREE_FORMAT = 1                   # 받아 둔 파일의 꼴 번호 — 나무 줄의 칸이 바뀌면 올린다
ROW_FLAGS = ("notice", "files")   # 목록 줄에서 참일 때만 싣는 칸
READER_COUNT = 100                # readers 한 쪽의 줄 수
FORM_HTML_FILE = "form.html"      # form 이 저장된 본문 HTML 을 남기는 파일 이름 — 글 일부 바꾸기(--swap)의 조각을 여기서 고른다
READ_MAX = 12000                  # read 가 한 번에 내는 본문 글자 수 — 한글 본문은 OUT_BYTES 가 먼저 끊는다
SAVED_TEXT_FILE = "article.txt"   # read 가 본문 글자 전부를 남기는 파일 이름 — 긴 글은 이 파일을 나눠 읽는다
# 그 글의 받는 자리(article_dir)에 이 스킬이 첨부 말고 따로 쓰는 이름 전부 — 첨부의 저장 이름이 이것들과 안 겹치게 가른다(save_names).
# 그 자리에 쓰는 길은 다 own_path 를 지나고, 여기 없는 이름은 거기서 멈춘다
OWN_NAMES = (SAVED_TEXT_FILE, FORM_HTML_FILE, IMAGES_DIR)
PATH_SEP = " > "
ALL_BOARDS = "모든 게시판"         # 게시판을 안 준 목록 · 찾기의 머리 — 앱 손이 나무의 뿌리로 묻는다
# 화면 필터 칸 → (낱말, --help) — 낱말이 인자 이름(no_pinned 는 --no-pinned)이자 답의 filters 낱말이다. 거르기를 더하는 일은 이 표의 한 줄이다
FILTERS = {"notifyYn": ("no_pinned", "고정 공지를 뺀다(화면 [필터링 > 공지감추기])"),
           "unreadArticleYn": ("unread", "내가 안 읽은 글만(화면 [필터링 > 안읽은게시물만])"),
           "myArticleYn": ("mine", "내가 쓴 글만(화면 [필터링 > 내게시물만]) — 고정 공지는 그대로 맨 위에 선다")}
COMMENTS_NEXT = "의견 {} 건 — comments {} --board {} 로 읽는다"   # read 답의 comments_next — 의견 수 · 글 id · 게시판 id
IMAGES_NOTE = ("본문 그림 {} 장 — 글의 [그림 N] 자리다. 그림뿐인 공지 · 식단이 흔하니, 그림에 든 것이 물음에 걸리면"
               " 같은 명령에 --images 로 받아 그림 파일로 연다")                   # read 가 그림을 안 받은 답의 note — 그림 수
COPY_FORM_NOTE = "재활용은 원글의 첨부를 안 가져온다 — 저장하면 새 임시글이 하나 선다(원글은 그대로)"   # form --of copy 의 note
FORM_MORE = "본문 글자 전부는 html_file 을 연다"                                   # form 본문이 답 한도에 걸렸을 때의 more
SAVE_NEXT = "받으려면 --save <번호> 나 --save all"                                # attachment 목록 답의 next
ECM_NEXT = "스킬 company-ecm 의 read {} 로 연다"                                  # 문서함 쪽지 줄의 next — 문서 열쇠
SAVED_WORD = "임시보관함에 저장했다(아직 게시 안 됨)"                            # save 답의 saved
SAVE_NEXT_STEP = "사람이 띄운 편집 창에서 보고 [등록]을 누르면 게시된다 — 더 고칠 것은 save --start draft --id {} 로"   # save 답의 next — 글 id
COPY_NO_FILES = "원글의 첨부는 안 따라온다 — 필요하면 attachment 로 받아 save --start draft --file 로 붙인다"   # 재활용 save 의 note
FORKED_NOTE = ("임시글 {} 은 그대로 남고 고친 판이 새 임시글로 저장됐다 — 임시보관함에 둘이 있다. 띄운 창(새 글)을 보고"
               " [등록]하도록 이른다")                                              # 임시글이 갈라진 save 의 note — 옛 글 id
TITLE_EMPTY = "--title 이 비었다"   # 짓는 손에 넘길 제목이 빈 판의 거절 말 — 준 제목이든 재활용 원글의 제목이든
UNMEASURED = "회사에서 안 쟀다"     # 회사에서 안 잰 채 지은 출발 · 손가락에 --help 가 붙이는 말
BODY_STYLE = "font-family:'맑은 고딕','Malgun Gothic',sans-serif;font-size:10pt;line-height:1.6"   # 평문 글을 싸는 모양 — 게시판 편집기의 기본 글꼴


@dataclasses.dataclass(frozen=True)
class Flag:
    """바꿀 것 하나가 받는 인자 하나."""
    option: str          # 인자 — 「--html-file」
    meta: str            # --help 의 자리 말
    many: bool = False   # 여러 번 준다
    pair: bool = False   # 둘씩 받아 여러 번 준다(옛 조각 · 새 조각)

    @property
    def dest(self) -> str:
        """argparse 가 값을 싣는 이름 — 인자에서 앞의 「-」 를 떼고 「-」 를 「_」 로 바꾼 것."""
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
    place: object = None   # 그 출발의 자리를 정하는 손가락 — (앱 손, 인자, 가린 판) → Place. 아래 「출발의 자리」


@dataclasses.dataclass(frozen=True)
class Change:
    """글 짓기의 바꿀 것 하나 — 손가락 하나다."""
    flags: tuple     # 받는 인자(Flag)
    starts: tuple    # 받는 출발
    name: str        # 사람 말 이름 — 표 파일의 name
    about: str       # 이름 뒤에 붙는 이 명령의 말 — --help 의 지도
    elsewhere: str = ""   # 받지 않는 출발에서 그 일을 어디서 하나 — 명령이 멈추며 댄다
    unmeasured: str = ""  # 회사에서 저장까지 안 잰 손가락이면 안 잰 것 — --help 의 지도가 「회사에서 안 쟀다」로 낸다

    @property
    def word(self) -> str:
        """--help 의 지도에 서는 그 손가락의 말 — 이름과 이 명령의 말."""
        return f"{self.name} — {self.about}"


@dataclasses.dataclass(frozen=True)
class Place:
    """글 짓기 출발이 정한 자리 — 짓는 손에 줄 출발 인자 · 그 글의 게시판 id · 게시판 이름 · 손에 넘길 제목 · 답에 붙일 출발의 말."""
    args: list
    at: str
    board_name: str
    title: str | None
    notes: tuple = ()


# ── 출발의 자리 — 출발마다 손가락 하나(WRITE_STARTS 의 place) ─────────────────
def new_place(app, args, plan) -> Place:
    """새 글 출발의 자리 — 쓸 수 있는 게시판 나무에서 묶음이 아닌 게시판 하나를 고른다. 아니면 Stop(인자)."""
    where = resolve(app.tree(write=True), args.board, leaf=True)
    if where is None or where["folder"]:
        raise Stop(EXIT_ARGS, "args", "글은 묶음이 아닌 게시판 하나에 쓴다 — boards --write 로 고른다")
    return Place(["--board", where["id"]], where["id"], PATH_SEP.join(where["path"]), plan.title)


def draft_place(app, args, plan) -> Place:
    """임시글 출발의 자리 — 임시보관함 첫 쪽에서 그 글의 게시판을 찾는다(없으면 Stop(인자)). 이름은 받아 둔 나무로 댄다 — 없으면 id 다."""
    row = next((r for r in app.drafts()["rows"] if r["id"] == args.id), None)
    if row is None:
        raise Stop(EXIT_ARGS, "args", f"임시보관함 첫 쪽에 {args.id} 가 없다 — drafts 로 임시글 id 를 본다")
    return Place(["--id", args.id, "--at", row["board"]], row["board"], board_names(kept_tree() or []).get(row["board"], row["board"]), plan.title)


def copy_place(app, args, plan) -> Place:
    """재활용 출발의 자리 — 원글의 게시판을 고르고, 화면을 열기 전에 재활용 창이 그 글로 서나를 GET 으로 본다(아무것도 안 생긴다). 제목을 안
    줬으면 원글의 제목이다. 원글 게시판이 아니거나 그 제목이 비었으면 Stop(인자) — 창이 그 글로 안 서는 앱 손의 NotFound 는 main 의 끝(``ep_command.finish``)이 종료 2 로 옮긴다."""
    _, origin, _ = pick_board(app, args.from_board)
    if origin is None or origin["folder"]:
        raise Stop(EXIT_ARGS, "args", "재활용은 --from-board 로 원글의 게시판(목록 줄의 board)을 받는다")
    form = app.copy_form(origin["id"], args.id)
    title = form["title"].strip() if plan.title is None else plan.title
    if not title:
        raise Stop(EXIT_ARGS, "args", TITLE_EMPTY)
    return Place(["--id", args.id, "--at", origin["id"]], origin["id"], PATH_SEP.join(origin["path"]), title, (COPY_NO_FILES,))


# 글 짓기의 손가락 — 출발 하나 × 바꿀 것 아무 조합 → [임시저장]. 출발마다 꼭 받는 것과 바꿀 것마다의 이름 · 받는 출발은 곁의 표 파일
# (FINGERS_FILE) 한 벌이 들고 짓는 손(draft_board.js)도 그것을 읽는다. 여기 두 표는 그 위에 이 명령의 말 · 인자 · 자리 손가락을 붙인다 —
# 인자 · 거르기 · save --help 의 지도가 다 여기서 선다. 손가락을 더하는 일은 표 파일의 한 줄 · 이 표의 한 줄 · 짓는 손의 STARTS · CHANGES 의
# 한 줄(화면 함수)이다
FINGERS = json.loads((HERE / FINGERS_FILE).read_text(encoding="utf-8"))


def needs_of(start: str) -> tuple:
    """표 파일에서 그 출발이 꼭 받는 바꿀 것의 이름."""
    return tuple(FINGERS["starts"][start]["needs"])


def finger(key: str, flags: tuple, rest: str, **more) -> tuple[str, Change]:
    """(이름, 바꿀 것) — 표 파일의 바꿀 것 한 줄(사람 말 이름 · 받는 출발)에 이 명령의 인자와 말을 붙인다."""
    row = FINGERS["changes"][key]
    return key, Change(flags, tuple(row["starts"]), row["name"], rest, **more)


WRITE_STARTS = {
    "new": Start("새 글", "[글쓰기] 창 — 빈 창에 게시판 · 제목 · 글을 넣는다", "", needs_of("new"),
                 "임시보관함에 그 제목의 새 글이 서면 섰다", place=new_place),
    "draft": Start("임시글", "임시보관함 글의 편집 창 — 저장된 제목 · 게시판 · 본문 · 첨부가 든 채 열린다. 쓰는 사람이 그 글을 열어 두었으면 "
                   "그 창에서 고친다(둘째 창을 안 연다 · 그 창에서 사람이 고치던 것도 함께 저장된다)", "임시글 id(drafts 의 id)", needs_of("draft"),
                   "그 글의 모습(제목 · 게시 시각 · 게시기한 · 본문 글자 · 첨부 이름)이 바뀌고 요청한 것이 다 들면 섰다. 아니면 「못 가렸다」(종료 1)고 "
                   "편집 창을 띄워 둔다. 답이 「섰다」여도 사람에게 띄운 창에서 보고 확인받는다", place=draft_place),
    "copy": Start("재활용", "글 화면 [재활용]의 창 — 원글의 제목 · 본문 · 게시판 · 게시기한이 든 새 글 창. 원글은 안 바뀐다. 첨부는 안 따라온다"
                  "(사람에게 그렇게 말한다 — 필요하면 attachment 로 받아 --file 로 붙인다)", "원글 id(목록 줄의 id)", needs_of("copy"),
                  "임시보관함에 그 제목의 새 글이 서면 섰다(new 와 같다)",
                  "재활용 창의 [임시저장] — 새 임시글이 하나 서나 · 원글이 그대로인가 · 본문의 그림(상대 주소)이 새 글에서 보이나", place=copy_place),
}
WRITE_CHANGES = dict([
    finger("board", (Flag("--board", "게시판"),), "묶음이 아닌 게시판 하나(id 나 이름의 일부 · boards --write)",
           elsewhere="임시글 · 재활용 창에는 게시판 고름이 없다(「게시판 위치」 는 글자뿐) — 다른 게시판이면 save --start new 로 새로 짓는다"),
    finger("title", (Flag("--title", "제목"),), "앞뒤 빈칸은 걷힌다"),
    finger("body", (Flag("--html-file", "파일"), Flag("--text-file", "파일"), Flag("--image", "그림", many=True)),
           "통째로. HTML 조각이나 평문 파일 하나 · --image 의 그림은 그 글 끝에 차례로 붙는다. 임시글은 있던 글 · 그림이 다 이 글로 간다"),
    finger("files", (Flag("--file", "첨부", many=True),), "파일을 더한다. 있던 첨부는 그대로다"),
    finger("drop", (Flag("--drop", "첨부 이름", many=True),), "있던 첨부를 이름으로(read 의 attachments 이름 그대로)"),
    finger("end", (Flag("--end", "YYYY-MM-DD"),), "게시종료일. 그 게시판이 기한을 바꾸게 할 때만(안 되면 명령이 화면 전에 멈춘다)"),
    finger("swap", (Flag("--swap", "옛조각 새조각", pair=True), Flag("--swap-file", "옛파일 새파일", pair=True)),
           "지금 본문의 보이는 글자에서 꼭 한 번 나오는 조각만 바꾼다. 서식 · 그림 · 표는 그대로"),
])
WRITE_END = "[임시저장]만 누르고 그 글의 편집 창을 띄워 둔다. [등록](게시)은 사람이 그 창에서 보고 누른다"
WRITE_NOT_YET = ("말머리 · 익명 · 비밀번호 · 알림 · 캡처 허용(쓸 수 있는 게시판 어디에도 그 칸이 안 뜬다) · 공개 범위 · 예약 게시 · 답글(응답) "
                 "— 손가락이 없다. 띄운 편집 창에서 사람이 한다")
NOT_HERE = ("[등록](게시) · 게시된 글 고치기 · 지우기 · 의견(댓글) · 추천 · 열람 권한(비공개 · 대상자) · 예약 게시 — 손에 없다. 사람이 띄운 편집 "
            "창 · 게시판 화면에서 한다. 사람이 「바로 게시해」라고 해도 임시저장과 창 띄우기까지다")


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

# 이 명령이 내는 종료 값 — 뜻은 ep_command 의 한 표, 여기는 이 손이 덧붙일 말만
EXITS = ep_command.exit_legend((ep_command.EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION),
                               {EXIT_TOOL: "임시글의 저장이 섰는지 못 가렸을 때도 1 이다(편집 창은 띄워 둔다)",
                                EXIT_ARGS: "게시판 이름이 여럿에 걸리면 후보를 든다 · 글 id 와 게시판 id 가 안 맞음 · 그 출발이 안 받는 바꿀 것 · "
                                           "게시판이 저장을 막았다"})


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
    """게시판 id → 「 > 」 로 이은 경로 이름의 표."""
    return {b["id"]: PATH_SEP.join(b["path"]) for b in boards}


# ── 받아 둔 나무 ─────────────────────────────────────────────────────────
def tree_path() -> pathlib.Path:
    """받아 둔 게시판 나무 파일의 자리 — 홈 아래 ``TREE_DIR`` 의 ``TREE_FILE``."""
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


def body_of(html: str):
    """본문 HTML → 보이는 글자와 그림 주소(형제 스킬 company-mail 의 ``visible.body``) — 글자의 [그림 N] 이 주소들의 N 번째다. 누구나 쓰는 글이라
    숨긴 글 · 폭 없는 문자는 걷힌다."""
    return load("visible", MAIL_SCRIPTS).body(html)


def own_path(article_id: str, name: str) -> pathlib.Path:
    """그 글의 받는 자리에서 이 스킬이 쓰는 이름(``OWN_NAMES``)의 경로 — 거기 없는 이름이면 ValueError(첨부의 저장 이름과 겹칠 수 있다)."""
    if name not in OWN_NAMES:
        raise ValueError(f"{name} 이 OWN_NAMES 에 없다 — 첨부의 저장 이름과 겹치지 않게 거기 더한다")
    return article_dir(article_id) / name


def keep_file(article_id: str, name: str, text: str) -> pathlib.Path:
    """그 글의 받는 자리(``own_path``)에 글 파일 하나를 남기고 그 경로를 낸다."""
    path = own_path(article_id, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def end_editable(options: dict) -> bool:
    """그 게시판이 게시기한(게시종료일)을 바꾸게 하나 — 화면은 옵션 ``termModifyYn`` 이 Y 일 때만 날짜 칸을 켠다(N 이면 기본 기간 고정)."""
    return options.get("termModifyYn") == "Y"


def ecm_note(name: str) -> bool:
    """문서함(ECM) 쪽지의 이름 꼴인가 — 꼴은 형제 스킬 company-mail 의 ``inbox`` 가 든다(메일 첨부와 한 가름)."""
    return bool(load("inbox", MAIL_SCRIPTS).ECM_ATTACHMENT.match(name))


def file_notes(files: list) -> list[bool]:
    """첨부마다 문서함(ECM) 쪽지인가 — read 와 attachment 가 한 번씩 센다."""
    return [ecm_note(f["name"]) for f in files]


def listed_file(i: int, f: dict, note: bool, **more) -> dict:
    """첨부 목록의 한 줄 — no · name, 그 답이 더하는 칸(``more``), 문서함 쪽지면 ecm."""
    return {"no": i + 1, "name": f["name"], **more, **({"ecm": True} if note else {})}


def compose(args) -> str:
    """save 의 본문 — HTML 파일은 그대로, 평문은 줄바꿈을 살려 싸고, 그림은 끝에 data URI 로 붙인다."""
    if bool(args.html_file) == bool(args.text_file):
        raise Stop(EXIT_ARGS, "args", "글은 --html-file 이나 --text-file 하나로 준다 — --image 의 그림은 그 글 끝에 붙는다")
    raw = ep_command.text_file(args.html_file or args.text_file, "글 파일").strip()   # 파워셸이 붙인 BOM 이 글 첫머리에 안 실리게
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
    out.update(title=r["title"], writer=r["writer"], date=r["date"], **{k: True for k in ROW_FLAGS if r[k]},
               **({"comments": r["comments"]} if r.get("comments") else {}))
    return out


def page_rows(head: dict, rows: list, names: dict, next_page: int | None) -> dict:
    """목록 · 찾기 답의 한 쪽 — 머리에 줄을 싣고, 답 한도(``OUT_BYTES``)를 넘으면 뒤 줄부터 덜고 more 를, 다음 쪽이 있으면 next 를 단다."""
    out = dict(head, rows=[row_out(r, names, head.get("board_id")) for r in rows])
    while out["rows"] and size(out) > OUT_BYTES:
        out["rows"].pop()
        out["more"] = f"줄이 답 한도에 걸려 {len(out['rows'])} 줄만 실었다 — 남은 줄은 같은 쪽에 있으니 낱말 · 기간으로 좁혀 다시 찾는다"
    if next_page:
        out["next"] = f"--page {next_page}"
    return out


def cmd_boards(app, args) -> dict:
    """게시판 나무 손 — 읽을 수 있는 게시판(받아 홈에 남긴다)이나 ``--write`` 면 쓸 수 있는 게시판의 id · 경로 · 묶음 표시."""
    boards = app.tree(write=True) if args.write else fresh_tree(app)
    return {"boards": [{"id": b["id"], "path": PATH_SEP.join(b["path"]), **({"group": True} if b["folder"] else {})} for b in boards]}


@dataclasses.dataclass(frozen=True)
class ListScope:
    """list · search 의 물음을 세션 전에 가린 값 — 게시판 말 · 찾을 말 · 찾는 칸 · 기간(YYYY-MM-DD · 빈 글자는 앱 손의 기본) · 화면의
    필터 칸 · 제외할 말(걷은 글자). list 는 찾을 말이 빈 글자다."""
    board: str | None
    words: str
    fields: tuple
    since: str
    until: str
    filters: frozenset
    without: str


def filter_option(word: str) -> str:
    """화면 필터 낱말의 인자 — no_pinned 는 --no-pinned."""
    return "--" + word.replace("_", "-")


def list_scope(args) -> ListScope:
    """list · search 의 물음을 가린 값 — 기간 · 제외할 말이 틀렸거나 함께 못 서면 Stop(인자). 세션 없이 가린다(명령 표의 가림 칸)."""
    since = ep_command.date_of(args.since, "--since 는") if args.since else None
    until = ep_command.date_of(args.until, "--until 은") if args.until else None
    if since and until and until < since:
        raise Stop(EXIT_ARGS, "args", f"--until({until})이 --since({since})보다 앞이다 — 기간을 차례로 준다")
    filters = frozenset(flag for flag, (word, _) in FILTERS.items() if getattr(args, word))
    without = (args.without or "").strip()
    if args.without and len(without) < 2:
        raise Stop(EXIT_ARGS, "args", "--without 은 두 글자 이상이다(화면의 「제외할 단어」 와 같다)")
    if without and filters:
        raise Stop(EXIT_ARGS, "args", f"--without 은 화면의 상세검색으로 묻는데, 그 검색은 {' · '.join(filter_option(w) for w, _ in FILTERS.values())} 를 안 받는다 — 하나만 준다")
    return ListScope(args.board, args.words, tuple(args.field or DEFAULT_FIELDS) if args.words else (),
                     since.isoformat() if since else "", until.isoformat() if until else "", filters, without)


def list_ask(scope: ListScope, where: dict | None, page: int) -> dict:
    """앱 손 ``articles`` 에 줄 인자 — 게시판 · 기간을 안 주면 앱 손의 기본(나무의 뿌리 · 처음부터)이다. 한 쪽은 LIST_COUNT 줄이다."""
    asked = {"bbs_id": where["id"]} if where else {}
    if scope.since:
        asked["since"] = scope.since
    return dict(asked, words=scope.words, fields=scope.fields, until=scope.until, page=page, count=LIST_COUNT, filters=set(scope.filters),
                without=scope.without)


def naming_tree(app, boards: list, kept: bool, rows: list) -> list:
    """목록 줄의 게시판마다 이름을 댈 나무 — 받아 둔 나무에 없는 게시판의 글이 왔으면 새로 받는다(``fresh_tree``)."""
    if kept and not {r["board"] for r in rows} <= set(board_names(boards)):
        return fresh_tree(app)
    return boards


def split_pinned(scope: ListScope, rows: list, page: int) -> tuple[list, list]:
    """(찾은 줄, 머리에 따로 실을 고정 공지) — 고정 공지는 쪽마다 맨 위에 서고 낱말과 상관없이 오며 total 에도 안 든다. 찾기는 그것을
    찾은 줄과 가르고(첫 쪽에만 머리에 싣는다 — read 로 열 수 있게 id 를 든다), 목록은 첫 쪽에만 싣는다. 상세검색(제외할 말)은 고정 공지를
    따로 안 세워 그대로 둔다."""
    if scope.without:
        return rows, []
    kept = [r for r in rows if not r["notice"]]
    if scope.words:
        pinned = [{"id": r["id"], "board": r["board"], "title": r["title"]} for r in rows if r["notice"]]
        return kept, pinned if page == 1 else []
    return (kept, []) if page > 1 else (rows, [])


def list_head(scope: ListScope, where: dict | None, total: int, page: int, pinned: list) -> dict:
    """목록 답의 머리 — 본 게시판 · 센 수 · 쪽, 게시판 하나만 본 답이면 board_id(줄마다 되풀이하지 않는다), 찾은 말 · 칸 · 제외할 말 ·
    필터 · 따로 실은 고정 공지."""
    head = {"board": PATH_SEP.join(where["path"]) if where else ALL_BOARDS, "total": total, "page": page}
    if where and not where["folder"]:
        head["board_id"] = where["id"]
    if scope.words:
        head.update(words=scope.words, fields=list(scope.fields))
    if scope.without:
        head["without"] = scope.without
    if scope.filters:
        head["filters"] = [FILTERS[f][0] for f in sorted(scope.filters)]
    if pinned:
        head["pinned_notices"] = pinned
    return head


def next_page(total: int, page: int) -> int | None:
    """다음 쪽 번호 — 이 쪽 뒤에 줄이 남았을 때만. 쪽 번호가 0 이면 없다(쪽은 1 부터다)."""
    return page + 1 if page and total > page * LIST_COUNT else None


def cmd_list(app, args, scope: ListScope) -> dict:
    """목록 · 찾기 손 — 게시판 고르기 → 앱 묻기 → 이름 댈 나무 → 고정 공지 가르기 → 머리 → 쪽."""
    boards, where, kept = pick_board(app, scope.board)
    got = app.articles(**list_ask(scope, where, args.page))
    boards = naming_tree(app, boards, kept, got["rows"])
    rows, pinned = split_pinned(scope, got["rows"], args.page)
    return page_rows(list_head(scope, where, got["total"], args.page, pinned), rows, board_names(boards), next_page(got["total"], args.page))


def read_head(args, a: dict, page, files: list, notes: list, text_file: pathlib.Path) -> dict:
    """read 답의 머리 — 글의 칸 · 글자 수 · 남긴 글 파일 · 첨부 목록(``notes`` 가 선 첨부면 ecm) · 걷은 덩이 수(있을 때만)."""
    out = {"id": args.id, "board": args.board, "title": a["title"], "writer": a["writer"], "posted": a["posted"],
           "period": a["period"], "link": a["link"], "chars": len(page.text), "text_file": str(text_file),
           "attachments": [listed_file(i, f, notes[i]) for i, f in enumerate(files)]}
    if page.hidden:
        out["hidden"] = page.hidden
    out["comments"] = a["comments"]["total"]
    return out


def read_tail(app, args, comments: int, srcs: list) -> dict:
    """본문 뒤에 실을 칸 손 — 의견이 있으면 읽는 길, 그림이 있으면 받은 그림(``--images``)이나 그 수를 알리는 말."""
    tail = {"comments_next": COMMENTS_NEXT.format(comments, args.id, args.board)} if comments else {}
    if srcs and args.images:
        tail["images"] = save_images(app, args.id, srcs)
    elif srcs:
        tail["note"] = IMAGES_NOTE.format(len(srcs))
    return tail


def cmd_read(app, args) -> dict:
    """글 한 건 손 — 글 묻기 → 본문 풀기 → 첨부 목록 → 글 파일 남기기 → 머리 → 의견 · 그림 칸 → 답 한도에 본문 맞추기."""
    a = app.article(args.board, args.id)
    page = body_of(a["html"])
    files = app.files(args.id)
    text_file = keep_file(args.id, SAVED_TEXT_FILE, page.text)
    out = read_head(args, a, page, files, file_notes(files), text_file)
    tail = read_tail(app, args, a["comments"]["total"], list(page.images))   # 본문을 맞출 때 그 몫을 먼저 뺀다
    ep_command.fit_text(out, "body", page.text, args.start, READ_MAX, lambda end: f"--from {end}", OUT_BYTES - size(tail))
    out.update(tail)
    return out


COMMENT_MAX = 200                 # comments 가 한 번에 싣는 의견 수 — 넘으면 답 한도가 먼저 끊는다


def cmd_comments(app, args) -> dict:
    """글의 의견 — 글 화면(viewArticle · 조회수를 안 올린다)에 함께 오는 칸을 푼다. 새 요청이 없다."""
    said = app.article(args.board, args.id)["comments"]
    out = {"id": args.id, "board": args.board, "total": said["total"], "rows": said["rows"][args.skip:args.skip + COMMENT_MAX]}
    while out["rows"] and size(out) > OUT_BYTES:
        out["rows"].pop()
    shown = args.skip + len(out["rows"])
    if shown < len(said["rows"]):
        out["more"] = f"--skip {shown}"
    return out


def cmd_readers(app, args) -> dict:
    """글의 열람내역(화면의 조회수 링크) — 읽은 시각 · 이름 · 부서 · 직함. 사번은 안 싣는다."""
    got = app.readers(args.board, args.id, page=args.page, count=READER_COUNT)
    out = {"id": args.id, "board": args.board, "total": got["total"], "page": args.page, "rows": got["rows"]}
    while out["rows"] and size(out) > OUT_BYTES:
        out["rows"].pop()
        out["more_on_page"] = "줄이 답 한도에 걸려 덜었다 — 부서 · 사람을 물으면 그 말로 좁혀 답한다"
    if got["total"] > args.page * READER_COUNT:
        out["next"] = f"--page {args.page + 1}"
    return out


def cmd_form(app, args) -> dict:
    """쓰기 창이 열 칸 손 — 임시글(draft) · 재활용(copy)의 폼을 GET 으로 묻기 → 본문 풀기 → HTML 파일 남기기 → 게시판 옵션 → 맞추기.
    창을 안 띄우고 아무것도 안 바꾼다. 본문은 글자와 HTML 파일 둘."""
    form = app.draft_form(args.board, args.id) if args.of == "draft" else app.copy_form(args.board, args.id)
    page = body_of(form["html"])
    html_file = keep_file(args.id, FORM_HTML_FILE, form["html"])
    out = {"id": args.id, "of": args.of, "board": form["board"], "title": form["title"], "end_date": form["end_date"],
           "posted_on": form["notify_date"], "html_file": str(html_file), "chars": len(page.text),
           "end_editable": end_editable(app.options(form["board"])), **({"note": COPY_FORM_NOTE} if args.of == "copy" else {})}
    ep_command.fit_text(out, "body", page.text, 0, READ_MAX, lambda end: FORM_MORE, OUT_BYTES)
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

    return images.save(srcs, fetch, own_path(article_id, IMAGES_DIR))


def attachment_list(article_id: str, files: list, notes: list) -> dict:
    """첨부 목록 답 — 줄마다 no · name · bytes, 문서함 쪽지면 ecm. 첨부가 있으면 받는 길을 든다."""
    rows = [listed_file(i, f, notes[i], bytes=f["size"]) for i, f in enumerate(files)]
    return {"id": article_id, "attachments": rows, **({"next": SAVE_NEXT} if rows else {})}


def picked(save: str, count: int) -> list[int]:
    """--save 의 값 → 받을 첨부의 자리(0 부터) — 번호 하나나 all. 아니면 Stop(인자)."""
    if save == "all":
        return list(range(count))
    if save.isdigit() and 1 <= int(save) <= count:
        return [int(save) - 1]
    raise Stop(EXIT_ARGS, "args", f"첨부 번호가 아니다: {save!r} — 1 부터 {count} 까지")


def save_dir(args) -> pathlib.Path:
    """첨부를 받을 폴더 — --out, 안 주면 그 글의 받는 자리(``article_dir``)."""
    return pathlib.Path(args.out).expanduser() if args.out else article_dir(args.id)


def save_names(files: list, notes: list) -> dict:
    """번호 → 저장 이름(형제 company-mail 의 ``attachments.file_names``) — 이 글에서 파일로 남길 첨부 전부를 두고 가른다: 같은 이름 · 이 자리에
    이 스킬이 따로 쓰는 이름(``OWN_NAMES``)과 안 겹친다. 문서함 쪽지는 파일로 안 남아 안 든다."""
    return load("attachments", MAIL_SCRIPTS).file_names({i + 1: f["name"] for i, f in enumerate(files) if not notes[i]}, reserved=OWN_NAMES)


def note_row(no: int, name: str, data: bytes) -> dict:
    """문서함 쪽지 한 건의 줄 — 화면이 여는 링크 쪽 문서 열쇠(형제 company-mail 의 ``inbox.ecm_note_key`` · 메일과 한 가름). 열쇠가 없으면 Stop(도구)."""
    k = load("inbox", MAIL_SCRIPTS).ecm_note_key(data.decode("utf-8", "replace"))
    if not k:
        raise Stop(EXIT_TOOL, "tool", f"문서함 쪽지에 문서 열쇠가 없다: {name} — 쪽지 꼴이 잰 것과 다르다")
    return {"no": no, "name": name, "ecm_key": k, "next": ECM_NEXT.format(k)}


def file_row(no: int, name: str, file_name: str, data: bytes, out_dir: pathlib.Path) -> dict:
    """첨부 한 건을 파일로 남긴 줄(형제 company-mail 의 ``attachments.keep``) — path · bytes, DRM 이면 note 가 다음 손을 말한다."""
    path, note = load("attachments", MAIL_SCRIPTS).keep(out_dir, file_name, name, data)
    return {"no": no, "name": name, "path": str(path), "bytes": len(data), **({"note": note} if note else {})}


def fetch_one(app, f: dict, no: int, is_note: bool, file_name: str | None, out_dir: pathlib.Path) -> dict:
    """첨부 한 건 손 — 받아서 쪽지면 문서 열쇠 줄, 아니면 파일로 남긴 줄."""
    data = app.download(f["id"])
    return note_row(no, f["name"], data) if is_note else file_row(no, f["name"], file_name, data, out_dir)


def cmd_attachment(app, args) -> dict:
    """첨부 손 — 목록 묻기 → (목록만이면 그 답) 고르기 → 받을 폴더 → 저장 이름 → 한 건씩 받기."""
    files = app.files(args.id)
    notes = file_notes(files)
    if not args.save:
        return attachment_list(args.id, files, notes)
    picks = picked(args.save, len(files))
    out_dir = save_dir(args)
    names = save_names(files, notes)
    return {"id": args.id, "saved": [fetch_one(app, files[i], i + 1, notes[i], names.get(i + 1), out_dir) for i in picks]}


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


def write_fingers(args) -> list[str]:
    """이 부름이 받은 바꿀 것의 이름 — 출발이 안 받는 것 · 꼭 받을 것이 빠진 것 · --id 의 있고 없음이 출발과 안 맞는 것은 게시판도 화면도
    부르기 전에 Stop(인자)."""
    start = WRITE_STARTS[args.start]
    got = [name for name, ch in WRITE_CHANGES.items() if any(getattr(args, f.dest) not in (None, []) for f in ch.flags)]
    for name in got:
        ch = WRITE_CHANGES[name]
        if args.start not in ch.starts:
            raise Stop(EXIT_ARGS, "args", f"{start.word} 출발에는 「{ch.name}」 손가락이 없다. {ch.elsewhere}")
    missing = [WRITE_CHANGES[n].name for n in start.needs if n not in got]
    if missing:
        raise Stop(EXIT_ARGS, "args", f"{start.word} 출발에 꼭 줄 것이 빠졌다: {' · '.join(missing)} — save --help 의 지도를 본다")
    if not got:
        raise Stop(EXIT_ARGS, "args", f"{start.word} 출발은 바꿀 것을 하나는 받는다 — 편집 창을 띄우기만 하려면 show")
    if start.takes and not args.id:
        raise Stop(EXIT_ARGS, "args", f"{start.word} 출발은 --id 로 {start.takes} 를 받는다")
    if not start.takes and args.id:
        raise Stop(EXIT_ARGS, "args", f"{start.word} 출발은 --id 를 안 받는다")
    if (args.start == "copy") != bool(args.from_board):
        raise Stop(EXIT_ARGS, "args", "--from-board(원글의 게시판)는 재활용(copy) 출발만 받고, 재활용은 꼭 받는다")
    return got


def write_map() -> str:
    """save --help 의 지도 — 두 표에서 짓는다."""
    out = ["출발(--start) — 화면 하나를 연다"]
    for name, s in WRITE_STARTS.items():
        takes = f" · --id 로 {s.takes}" if s.takes else ""
        needs = f" · 꼭 받는다: {' · '.join(WRITE_CHANGES[n].name for n in s.needs)}" if s.needs else ""
        out.append(f"  {name:6} {s.word}: {s.screen}{takes}{needs}\n         저장을 가리는 법: {s.proof}")
        if s.unmeasured:
            out.append(f"         {UNMEASURED}: {s.unmeasured}")
    out.append("바꿀 것 — 한 부름에 아무 조합을 한 화면에 넣는다")
    for ch in WRITE_CHANGES.values():
        flags = " | ".join(f.option for f in ch.flags)
        out.append(f"  {flags}  [{' · '.join(ch.starts)}]  {ch.word}")
        if ch.unmeasured:
            out.append(f"         {UNMEASURED}(저장): {ch.unmeasured}")
    out.append(f"끝 — {WRITE_END}")
    out.append(f"아직 없는 손가락 — {WRITE_NOT_YET}")
    return "\n".join(out)


@dataclasses.dataclass(frozen=True)
class WritePlan:
    """세션 · 게시판 · 화면을 부르기 전에 가린 글 짓기 — 받은 바꿀 것 · 걷은 제목 · 첨부의 절대 경로 · 지은 본문(없으면 None) · 글 일부 ·
    게시종료일(YYYY-MM-DD · 안 줬으면 None)."""
    changes: list
    title: str | None
    files: list
    body: str | None
    swaps: list = dataclasses.field(default_factory=list)
    end: str | None = None


def swaps_of(args) -> list[list[str]]:
    """--swap · --swap-file 의 [옛 조각, 새 조각] — 파일 쌍은 UTF-8 글 둘(조각이 길거나 따옴표가 들 때 · BOM 과 앞뒤 줄바꿈은 걷는다)."""
    pairs = [list(p) for p in args.swap or ()]
    for old_file, new_file in args.swap_file or ():
        pairs.append([ep_command.text_file(f, "--swap-file 의 파일").lstrip("\r\n") for f in (old_file, new_file)])
    if any(not old.strip() for old, _ in pairs):
        raise Stop(EXIT_ARGS, "args", "바꿀 옛 조각이 비었다")
    return pairs


def title_of(args) -> str | None:
    """--title 의 앞뒤 빈칸을 걷은 글자 — 안 줬으면 None. 게시판이 걷어 저장하니 같은 글자로 넘긴다."""
    return None if args.title is None else args.title.strip()


def end_of(args) -> str | None:
    """--end 의 날 — 앞뒤 빈칸을 걷은 YYYY-MM-DD(``ep_command.date_of``). 안 줬으면 None. 칸 꼴 가림(``refuse_fields``)이 먼저 있는 날인가를 본다."""
    return None if args.end is None else ep_command.date_of(args.end, "--end 는").isoformat()


def attached(args) -> list[str]:
    """--file 마다의 절대 경로."""
    return [str(pathlib.Path(f).expanduser().resolve()) for f in args.file or []]


def refuse_fields(args, got: list, title: str | None, files: list) -> None:
    """save 의 칸 꼴이 틀렸으면 Stop(인자) — 빈 제목 · 글 통째와 일부를 함께 · 없는 날의 게시기한 · 빈 빼기 · 같은 이름을 빼고 더하기 · 없는
    첨부를 이 차례로 보고 첫 하나를 댄다."""
    if title == "":
        raise Stop(EXIT_ARGS, "args", TITLE_EMPTY)
    if "body" in got and "swap" in got:
        raise Stop(EXIT_ARGS, "args", "글 통째(--html-file · --text-file)와 글 일부(--swap)는 한 부름에 같이 안 준다 — 통째로 줄 글에 고침을 담는다")
    if args.end is not None:
        ep_command.date_of(args.end, "--end 는")   # 꼴만이 아니라 있는 날인가도 — 없는 날(2026-13-45)은 게시판 화면에 닿기 전에 멈춘다
    if any(not d.strip() for d in args.drop or []):
        raise Stop(EXIT_ARGS, "args", "--drop 이 비었다")
    same = {pathlib.Path(f).name for f in args.file or []} & set(args.drop or [])
    if same:
        raise Stop(EXIT_ARGS, "args", f"같은 이름을 빼고 더하는 것({' · '.join(sorted(same))})은 한 부름에 안 한다 — --drop 한 번 · --file 한 번으로 나눠 부른다")
    for f in files:
        if not pathlib.Path(f).is_file():
            raise Stop(EXIT_ARGS, "args", f"첨부 파일이 없다: {f}")


def write_plan(args) -> WritePlan:
    """save 의 인자를 다 가린 판 손 — 손가락 거르기 → 제목 · 첨부 경로 → 칸 꼴 → 본문 · 글 일부. 하나라도 걸리면 Stop(인자). 세션도 게시판도
    안 부른다."""
    got = write_fingers(args)
    title, files = title_of(args), attached(args)
    refuse_fields(args, got, title, files)
    return WritePlan(got, title, files, compose(args) if "body" in got else None, swaps_of(args), end_of(args))


def refuse_locked_end(app, place: Place) -> None:
    """그 게시판이 게시기한을 못 바꾸게 하면 Stop(인자) — 게시판 옵션을 묻는다(화면은 그때 게시종료일 칸을 잠근다)."""
    opt = app.options(place.at)
    if not end_editable(opt):
        raise Stop(EXIT_ARGS, "args", f"{place.board_name} 게시판은 게시기한을 못 바꾼다(기본 {opt.get('dispPeriod', '?')} 고정)")


def hand_args(args, plan: WritePlan, place: Place) -> list[str]:
    """짓는 손 save 의 인자 — 출발 · 자리 · 게시기한 · 뺄 첨부 · 제목 · 더할 첨부(본문 · 글 일부의 파일은 ``handed_files`` 가 붙인다)."""
    extra = ["--start", args.start, *place.args]
    if plan.end is not None:
        extra += ["--end", plan.end]
    for d in args.drop or []:
        extra += ["--drop", d]
    if place.title is not None:
        extra += ["--title", place.title]
    for f in plan.files:
        extra += ["--file", f]
    return extra


@contextlib.contextmanager
def handed_files(plan: WritePlan):
    """본문 · 글 일부를 임시 파일로 남겨 짓는 손의 인자(--body-file · --swap-file)로 내고, 그 블록이 끝나면 걷는다."""
    extra, temps = [], []
    for flag, data in (("--body-file", plan.body), ("--swap-file", json.dumps(plan.swaps, ensure_ascii=False) if plan.swaps else None)):
        if data is not None:
            with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as tmp:
                tmp.write(data)
            temps.append(tmp.name)
            extra += [flag, tmp.name]
    try:
        yield extra
    finally:
        for t in temps:
            pathlib.Path(t).unlink(missing_ok=True)


def save_words(out: dict, place: Place) -> dict:
    """짓는 손의 답에 사람에게 갈 말을 붙인다 — 게시판 이름 · 저장했다 · 다음 길, 그리고 출발의 말과 임시글이 갈라졌을 때의 말."""
    out.update(board_name=place.board_name, saved=SAVED_WORD, next=SAVE_NEXT_STEP.format(out.get("id")))
    notes = list(place.notes) + ([FORKED_NOTE.format(out["forked_from"])] if out.get("forked_from") else [])
    if notes:
        out["note"] = " · ".join(notes)
    return out


def cmd_save(app, args, plan: WritePlan) -> dict:
    """글 짓기 손 — 출발의 자리 → 게시기한 잠금 → 손 인자 · 본문 파일 → 짓는 손 → 답의 말. 가린 판(``plan``)은 명령 표의 세션 전 가림
    (``write_plan``)이 낸다."""
    place = WRITE_STARTS[args.start].place(app, args, plan)
    if plan.end is not None:
        refuse_locked_end(app, place)
    with handed_files(plan) as files:
        out = hand("save", *hand_args(args, plan, place), *files)
    return save_words(out, place)


def board_word() -> str:
    """게시판 인자의 말 — list · search · save 가 함께 쓴다."""
    return "게시판 id(BBS…)나 이름의 일부(「식단」 · 「업무공지」 · 「일반사항 > 기타」) — 묶음이면 그 아래를 다 본다. 이름이 여럿에 걸리면 종료 2 가 후보를 든다"


# 명령마다 (한 줄 — 맨 위 --help 의 지도와 명령 목록, 그 명령의 --help 에 덧붙는 답의 칸). --help 는 이 표와 글 짓기의 두 표에서만 선다
READS = {
    "boards": ("게시판 나무 — id · 경로 · 묶음(group). --write 는 글을 쓸 수 있는 곳만(늘 게시판에서 새로 받는다)",
               "답: boards — 줄마다 id · path, 묶음 게시판이면 group"),
    "list": ("새 글부터 목록 — 게시판 · 기간으로 좁힌다(기간을 안 주면 처음부터 오늘까지)",
             f"답: board(본 게시판) · page · total(다 센 수) · rows(한 쪽 {LIST_COUNT} 줄 — id · title · writer · date, 참일 때만 notice(고정 공지) · files(첨부 있음) · comments(의견 수)) · "
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
    "comments": ("글의 의견(댓글) — 글 화면에 함께 오는 칸(조회수를 안 올린다)",
                 f"답: total · rows(줄마다 who(이름 · 직함 / 부서 — 화면 글자) · at · text, 남의 의견에 단 답글이면 reply, 말머리가 있으면 kind) · "
                 f"more(다음 --skip). 한 번에 {COMMENT_MAX} 건까지"),
    "readers": ("글의 열람내역 — 누가 언제 읽었나(화면의 조회수 링크). 여는 것으로 내 읽음 · 조회수는 안 바뀐다",
                f"답: total · page · rows(한 쪽 {READER_COUNT} 줄 — at · name · dept · title) · next(다음 --page). 사번은 안 싣는다"),
    "form": ("쓰기 창이 열릴 칸 — 임시글(--of draft)의 저장된 본문 · 게시기한, 또는 재활용(--of copy)이 가져올 제목 · 본문. 창을 안 띄운다",
             "답: title · board · end_date · end_editable(이 게시판이 게시기한을 바꾸게 하나) · posted_on · body(보이는 글자) · html_file(본문 HTML 전문 — "
             "--swap 의 조각을 여기서 고른다) · chars. copy 면 note(첨부는 안 따라온다)"),
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
    out += [f"  {name:11} {READS[name][0]}" for name in ("boards", "list", "search", "read", "comments", "readers", "attachment", "drafts", "form")]
    out.append(f"\n글 짓기 — save 한 번이 게시판 화면 한 판: 출발 하나 × 바꿀 것 아무 조합 → {WRITE_END}. 바꿀 것이 여럿이면 한 번에 준다")
    out.append("출발(--start)")
    for name, st in WRITE_STARTS.items():
        takes = f" · --id <{st.takes}>" if st.takes else ""
        out.append(f"  {name:6} {st.word}{takes} — {st.screen}" + (f" · {UNMEASURED}" if st.unmeasured else ""))
    out.append(f"바꿀 것 (● 꼭 든다 · ○ 받는다 · △ 받되 {UNMEASURED} · — 없다)")
    for key, ch in WRITE_CHANGES.items():
        marks = " ".join(f"{name}{'●' if key in st.needs else ('—' if name not in ch.starts else ('△' if st.unmeasured or ch.unmeasured else '○'))}"
                         for name, st in WRITE_STARTS.items())
        out.append(f"  {' · '.join(f.option for f in ch.flags):38} {marks:12} {ch.word}")
    out += [f"  — 의 자리({ch.name}): {ch.elsewhere}" for ch in WRITE_CHANGES.values() if ch.elsewhere]
    out.append(f"아직 없는 손가락 — {WRITE_NOT_YET}")
    out.append("\n창 띄우기 — 저장한 임시글을 사람이 보고 [등록]하게")
    out.append(f"  {'show':11} {READS['show'][0]}")
    out.append(f"\n안 하는 것 — {NOT_HERE}")
    out.append(EXITS)
    out.append("답은 표준 출력의 JSON 하나다. 명령마다의 인자와 답의 칸은 <명령> --help")
    return "\n".join(out)


@dataclasses.dataclass(frozen=True)
class Command:
    """명령 하나 — 몸((앱 손, 인자[, 가린 값]) → 답) · 세션 전 가림(인자 → 몸에 넘길 값 — 틀렸으면 Stop) · 앱 손이 드나."""
    run: object
    guard: object = None
    app: bool = True


# 명령마다 몸과 세션 전 가림 — 가림은 세션도 게시판도 안 부르고 틀린 인자 · 파일 · 표에 없는 조합을 멈춘다(로그인을 청할 일이 아니다).
# drafts 는 앱 손의 임시보관함을, show 는 짓는 손을 그대로 부른다
COMMANDS = {"boards": Command(cmd_boards), "list": Command(cmd_list, list_scope), "search": Command(cmd_list, list_scope),
            "read": Command(cmd_read), "comments": Command(cmd_comments), "readers": Command(cmd_readers), "attachment": Command(cmd_attachment),
            "drafts": Command(lambda app, args: app.drafts()), "form": Command(cmd_form), "save": Command(cmd_save, write_plan),
            "show": Command(lambda app, args: hand("show", args.id, "--board", args.board), app=False)}


def parser() -> argparse.ArgumentParser:
    """board.py 의 인자 해석기 — 명령마다 하위 해석기와 인자를 달고, 맨 위 지도와 글 짓기 지도를 --help 에 붙인다."""
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
            s.set_defaults(words="", field=None, without=None)   # 목록은 찾을 말 없는 찾기다 — 한 손(cmd_list)이 둘을 다 받는다
        else:
            s.add_argument("words", metavar="말", help="찾을 말 — 빈칸이 든 말은 따옴표로 한 덩이")
            s.add_argument("--in", dest="board", metavar="게시판", help=board_word() + ". 안 주면 모든 게시판")
            s.add_argument("--field", action="append", choices=FIELDS, help="찾는 칸 — 여러 번 준다. 안 주면 앞의 넷. 부서가 올린 글이면 deptname, 사람 이름이면 writer, "
                                                                           "양식 · 파일이면 filename, 제목에 들 말이면 title")
        for word, say in FILTERS.values():
            s.add_argument(filter_option(word), action="store_true", help=say)
        if name == "search":
            s.add_argument("--without", metavar="말", help="이 말이 든 글을 뺀다(두 글자 이상 · 화면 상세검색의 제외할 단어). 상세검색으로 묻는다 — "
                                                          "고정 공지도 낱말이 들면 찾은 줄로 서고, 줄 날짜에 해가 없다")
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
    for name in ("comments", "readers"):
        c = command(name)
        c.add_argument("id", metavar="글_id", help="목록 줄의 id")
        c.add_argument("--board", required=True, metavar="게시판_id", help="게시판 id — 목록 줄의 board, 없으면 답 머리의 board_id")
        if name == "comments":
            c.add_argument("--skip", type=int, default=0, metavar="N", help="앞의 N 건을 건너뛴다 — 답의 more 가 댄다")
        else:
            c.add_argument("--page", type=int, default=1, metavar="N", help=f"쪽 — 한 쪽 {READER_COUNT} 줄(기본 1)")
    command("drafts")
    f = command("form")
    f.add_argument("id", metavar="글_id", help="draft: drafts 의 id · copy: 원글의 id")
    f.add_argument("--board", required=True, metavar="게시판_id", help="그 글의 게시판 id")
    f.add_argument("--of", required=True, choices=("draft", "copy"), help="draft: 임시글의 편집 창 · copy: 재활용 창")
    s = command("save", epilog=write_map())
    s.add_argument("--start", required=True, choices=list(WRITE_STARTS),
                   help=" · ".join(f"{name}: {st.word}" for name, st in WRITE_STARTS.items()) + " — 아래 지도")
    s.add_argument("--id", help=" · ".join(f"{name}: {st.takes}" for name, st in WRITE_STARTS.items() if st.takes))
    s.add_argument("--from-board", metavar="게시판", help="copy: 원글의 게시판 — 목록 줄의 board(id 나 이름의 일부)")
    for change in WRITE_CHANGES.values():
        for flag in change.flags:
            s.add_argument(flag.option, dest=flag.dest, metavar=tuple(flag.meta.split()) if flag.pair else flag.meta,
                           nargs=2 if flag.pair else None, action="append" if flag.many or flag.pair else "store",
                           help=change.name + (" — 여러 번 준다" if flag.many or flag.pair else "")
                           + (f" · {UNMEASURED}" if change.unmeasured else ""))
    w = command("show")
    w.add_argument("id", metavar="글_id", help="drafts 의 id")
    w.add_argument("--board", required=True, metavar="게시판_id", help="그 글의 게시판 id — drafts 줄의 board")
    return p


def main() -> int:
    """명령 하나 — 인자를 풀고, 앱 손을 실은 뒤(``ep_command.finish``) 세션 전 가림 → 세션 바퀴(``ep_session.session_first``) 안의 몸."""
    args = parser().parse_args()
    command = COMMANDS[args.command]

    def work(xclick) -> dict:
        given = (command.guard(args),) if command.guard else ()     # 세션 전에 가린 값 — 틀렸으면 세션도 안 받고 멈춘다
        if not command.app:
            return command.run(None, args, *given)
        return ep_session.session_first(lambda f: command.run(xclick.App(f), args, *given), expired=(xclick.SessionExpired, xclick.SessionMissing))

    return ep_command.finish(work, "xclick", HERE, args_errors=("NotFound",))   # 글 id 와 게시판 id 가 안 맞는 것은 인자가 틀린 것이다


if __name__ == "__main__":
    sys.exit(main())
