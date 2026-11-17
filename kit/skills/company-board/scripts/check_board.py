"""xclick.py 의 뒤섞기 · 본문 그림 손과 board.py 의 ``read`` 를 잰다 — 사내로도 밖으로도 안 나간다.

층 — 쓰는 사람의 계약. 판정 넷(판정마다 걸린 check-design §1 넷의 근거는 ``references/DESIGN.md`` 「검사」):

1. 뒤섞기 — 표본 글마다 ``scramble``(글)이 기대값과 같다. 한 글자라도 다르면 게시판이 안 들이고 명령은 세션 끊김으로 읽어 스킬
   전체가 멈춘다. 기대값은 회사 PC 에서 게시판 화면의 jQuery.encrypt 로 뽑은 글자다 — 재이는 코드에서 읽지 않는다
2. 본문 그림 — 잰 꼴(게시판 호스트 · 포트의 ``DownController.do?fileId=`` · 상대 주소도)은 묻고, 그 밖은 서버에 닿기 전에 ``Refused`` 다
3. 읽은 글 — ``read`` 의 본문 · 남긴 글 파일에 화면에서 안 보이는 글이 안 들고 보이는 글은 다 들며, 걷은 수가 ``hidden`` 에 선다.
   「[그림 N]」 은 ``--images`` 가 받는 N 번째 주소고 그 주소는 ``src`` 속성이다(``data-src`` 가 앞에 서도). 기대값은 표본이 정한다
4. 글 화면의 본문 — ``parse_article`` 의 ``html`` 을 ``visible.body`` 에 넣으면 글의 표가 한 행 한 줄 · 칸은 ``TABLE_SEP`` 다

물림 — 판정 1 은 열쇠의 없는 칸을 0 대신 되돌려 쓰는 사본, 판정 2 는 호스트만 보고 길을 안 보는 사본, 판정 3 은 숨긴 요소를 안 가리는
사본 · 폭 없는 문자를 안 걷는 사본 · 그림 주소를 ``data-src`` 에서 먼저 읽는 사본, 판정 4 는 감싸개를 안 벗기는 사본(글자 치환)에 같은
판정을 대어 빨강을 본다(매번 돈다). 치환할 글자가 없으면 「못 쟀다 — 물림을 다시 지을 일」로 알리고 통과 · 종료 값에는 안 센다.

돌리는 법::  python -X utf8 -I check_board.py

판정 — 끝 줄이 「통과 N/N」이면 종료 0, 어긋나면 1.

언제 걷나 — 판정 1 은 게시판이 뒤섞기 없이 들이거나 xclick.py 가 뒤섞기를 화면에서 돌려 받게 되면. 판정 2 는 본문 그림을 받는 손이
사라지거나 그림을 세션 없이 받게 되면. 판정 3 은 board.py 의 ``read`` 가 사라지거나, 본문을 푸는 손 곁의 검사가 표 꼴의 숨긴 글
걷기와 이 명령의 배선을 함께 재게 되면. 판정 4 는 글 화면이 본문을 감싸개 없이 내거나, 본문을 푸는 손이 화면의 틀을 스스로 가르게 되면.

여기서 못 재는 것 — 실물 SSO · 게시판의 화면 꼴(목록 · 글 · 첨부) · 짓는 손(draft_board.js)의 화면 조작 — 회사 PC 에서 시험 글 하나를
임시저장 · 읽기 · 지우기로 잰다.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
HAND = HERE / "xclick.py"
BOARD = HERE / "board.py"
VISIBLE = HERE.parents[1] / "company-mail" / "scripts" / "visible.py"   # 본문을 푸는 손 — board.py 가 표 꼴로 부른다

# 게시판 화면의 jQuery.encrypt(글) — 회사 PC 의 Edge 에서 뽑은 값
EXPECTED = {
    "a": "/gjDar/qSD8!",
    "id=kh.kim": "2+eVhFIwq8zVLzh2",
    "facade=BBSArticleFacade&command=listArticle&srchKeyword=%EC%95%88%EC%A0%84":
        "+v11IY0YWnUNG3mrwhNv61rL+d7J5eJGildnHJtfr4959rlKlyFLLctNKr2sG8dk/rQekxFrUuCST9TBpqdIO+V5BIcldzFypm9Smw!!",
}
MUTANT = ("kv = k[idx] if idx < len(k) else 0", "kv = k[idx % len(k)]")   # 열쇠의 없는 칸을 0 이 아니라 되돌려 쓴다 — 옮기다 흔히 틀리는 자리

# 본문 그림 주소 — 회사 PC 에서 본 꼴 그대로(열쇠 글자만 바꿨다)
IMAGE_ASKED = ("/U14/U14010/DownController.do?fileId=QF_1",
               "http://swpappr.posco.net:7070/U14/U14010/DownController.do?fileId=QF_2")
IMAGE_REFUSED = ("https://img.ccworkshop.kr/variants/x/gallery/y_w1920.webp",            # 본문에 든 남의 호스트
                 "https://t1.kakaocdn.net/mapjsapi/images/2x/marker.png",
                 "http://swpappr.posco.net:7070/U14/U14010/XClickController?facade=BBSArticleFacade&command=deleteArticle",
                 "http://swpappr.posco.net:8080/U14/U14010/DownController.do?fileId=QF_3",
                 "https://swpappr.posco.net:7070/U14/U14010/DownController.do?fileId=QF_5",
                 "/U14/U14010/DownController.do?fileId=QF_4&down_filename=f")
IMAGE_MUTANT = (' or parts.path != IMAGE_PATH or keys != ["fileId"]', "")   # 호스트만 보고 길 · 칸을 안 본다

# 읽은 글의 표본 — 보이는 문단 둘 · 숨긴 요소 하나 · 바탕(흰색)과 같은 색의 글 하나 · 폭 없는 문자 · 표 틀 안의 그림(식단 글의 꼴)
ZERO_WIDTH = "​"
READ_IMAGE = "/U14/U14010/DownController.do?fileId=QF_1"
READ_BODY = ('<p>11월 3주 식단 안내입니다.</p><div style="display:none">숨긴요소의글</div>'
             '<p><span style="color:#ffffff">흰바탕흰글</span></p>' f"<p>문의는 총무{ZERO_WIDTH}그룹으로.</p>"
             f'<table><tr><td><img data-src="/lazy/blank.gif" src="{READ_IMAGE}"></td></tr></table>')
READ_SEEN = ("11월 3주 식단 안내입니다.", "문의는 총무그룹으로.")
READ_UNSEEN = ("숨긴요소의글", "흰바탕흰글", ZERO_WIDTH)
READ_HIDDEN = 2                   # 걷은 덩이 — 숨긴 요소 하나 · 바탕색 글 하나
READ_MUTANTS = (   # (이름, 치환할 코드, 푸는 글자, 바꿀 글자)
    ("숨긴 요소를 안 가린다", VISIBLE, "now_hidden = hid or _hard_hidden(d, attrs)", "now_hidden = hid"),
    ("폭 없는 문자를 안 걷는다", BOARD, '.body(a["html"])', '.parse(a["html"], tables=True)'),
    ("그림 주소를 data-src 에서 먼저 읽는다", VISIBLE, 'src = attrs.get("src", "").strip()',
     'src = (attrs.get("data-src") or attrs.get("src", "")).strip()'),
)

# 글 화면의 표본 — 본문 칸 · 그 안의 한 행 한 칸 감싸개 표(화면의 주석까지) · 그 안의 글(문단 하나와 두 행 두 칸의 표). 글자는 지은 것이다
FRAME_BODY = '<p>교육 안내입니다.</p><table><tr><td>일자</td><td>링크</td></tr><tr><td>11월 10일</td><td>https://example.invalid/a</td></tr></table>'
FRAME_PAGE = ('<div id="contentArea_QF_1" class="v_content"><table style="table-layout:auto;width:100%;">\n<tr>\n<!-- 화면의 주석 -->\n'
              "<td style='min-height:100px; font-size:10pt;' valign=\"top\">" f"{FRAME_BODY}&nbsp;\n</td>\n</tr>\n</table>\n</div></td></tr></table>")
FRAME_ROWS = ("일자 | 링크", "11월 10일 | https://example.invalid/a")   # 한 행 한 줄 — 칸 사이는 visible.TABLE_SEP
FRAME_MUTANT = ('"html": unwrap(body.group(1))', '"html": body.group(1)')   # 감싸개를 안 벗긴다


def load(source: str, name: str):
    mod = types.ModuleType(name)
    mod.__file__ = str(HAND)
    sys.modules[name] = mod
    exec(compile(source, str(HAND), "exec"), mod.__dict__)
    return mod


def judge(mod) -> list[str]:
    return [f"{plain[:30]!r}: {mod.scramble(plain)!r} ≠ {want!r}" for plain, want in EXPECTED.items() if mod.scramble(plain) != want]


def judge_image(mod) -> list[str]:
    """App.image 를 세션 · 네트워크 없이 부른다 — 묻는 자리(_raw)를 적는 손으로 바꿔 끼운다."""
    app = object.__new__(mod.App)
    app._in, asked = True, []
    app._raw = lambda url, data=None: asked.append(url) or b"\x89PNG"
    wrong = []
    for src in IMAGE_ASKED:
        try:
            app.image(src)
        except mod.Refused as exc:
            wrong.append(f"잰 꼴을 막았다: {src} — {exc}")
    before = len(asked)
    for src in IMAGE_REFUSED:
        try:
            app.image(src)
            wrong.append(f"막을 주소를 받았다: {src}")
        except mod.Refused:
            pass
    if len(asked) != before:
        wrong.append(f"막을 주소가 서버에 닿았다: {asked[before:]}")
    return wrong


def judge_frame(mod) -> list[str]:
    """글 화면 표본을 ``parse_article`` 에 넣고 낸 ``html`` 을 본문을 푸는 손으로 푼다 — 표의 행마다 제 줄이 서야 한다."""
    hand = types.ModuleType("visible_for_frame")
    hand.__file__ = str(VISIBLE)
    sys.modules[hand.__name__] = hand
    exec(compile(VISIBLE.read_text(encoding="utf-8"), str(VISIBLE), "exec"), hand.__dict__)   # noqa: S102
    lines = hand.body(mod.parse_article(FRAME_PAGE)["html"]).text.splitlines()
    return [f"표의 행이 제 줄이 아니다: {row!r} — 낸 글 {lines!r}" for row in FRAME_ROWS if row not in lines]


def board(old: str | None = None, new: str = "", where: pathlib.Path = BOARD) -> types.ModuleType | None:
    """board.py 를 싣는다 — old 를 주면 ``where``(board.py 나 본문을 푸는 손 ``visible.py``)의 그 글자를 new 로 바꾼 사본으로. old 가
    그 코드에 없으면 None. 바꾸지 않은 본문 푸는 손은 board.py 가 제 길(형제 스킬의 자리)로 싣는다."""
    sources = {path: path.read_text(encoding="utf-8") for path in (BOARD, VISIBLE)}
    if old is not None:
        if old not in sources[where]:
            return None
        sources[where] = sources[where].replace(old, new)
    mod = types.ModuleType("board_under_check")
    mod.__file__ = str(BOARD)
    sys.modules[mod.__name__] = mod
    exec(compile(sources[BOARD], str(BOARD), "exec"), mod.__dict__)   # noqa: S102 — 재일 코드를 사본째 싣는다
    mod.hands = {}                                       # 대역으로 바꿔 끼울 손 — 이름 → 모듈
    if old is not None and where == VISIBLE:
        hand = types.ModuleType("visible_mutant")
        hand.__file__ = str(VISIBLE)
        sys.modules[hand.__name__] = hand                # dataclass 가 제 모듈을 이름으로 찾는다
        exec(compile(sources[VISIBLE], str(VISIBLE), "exec"), hand.__dict__)   # noqa: S102
        mod.hands["visible"] = hand
    real = mod.load
    mod.load = lambda name, folder: mod.hands[name] if name in mod.hands else real(name, folder)
    return mod


def judge_read(mod) -> list[str]:
    """``read`` 를 게시판 없이 부른다 — 앱 손은 표본 글을 내는 대역이고, 그림 받는 손은 넘겨받은 주소를 적는 대역이다."""
    app = types.SimpleNamespace(article=lambda board_id, article_id: {"html": READ_BODY, "title": "식단", "writer": "총무", "posted": "", "period": ""},
                                files=lambda article_id: [])
    mod.hands["body_images"] = types.SimpleNamespace(save=lambda srcs, fetch, out: [{"no": n, "src": s} for n, s in enumerate(srcs, 1)])
    wrong = []
    with tempfile.TemporaryDirectory() as temp:
        mod.article_dir = lambda article_id: pathlib.Path(temp)   # 글 파일 · 그림을 이 판의 임시 자리에만 남긴다
        out = mod.cmd_read(app, types.SimpleNamespace(id="A1", board="BBS1", start=0, images=False))
        texts = {"본문": out.get("body", ""), "글 파일": pathlib.Path(out["text_file"]).read_text(encoding="utf-8")}
        for where, text in texts.items():
            wrong += [f"{where}에 안 보이는 글이 들었다: {word!r}" for word in READ_UNSEEN if word in text]
            wrong += [f"{where}에 보이는 글이 빠졌다: {word!r}" for word in READ_SEEN if word not in text]
            if text.count("[그림 1]") != 1 or "[그림 2]" in text:
                wrong.append(f"{where}의 그림 자리가 [그림 1] 하나가 아니다: {text!r}")
        if out.get("hidden") != READ_HIDDEN:
            wrong.append(f"hidden 이 {out.get('hidden')!r} 다 — 걷은 덩이는 {READ_HIDDEN}")
        got = mod.cmd_read(app, types.SimpleNamespace(id="A1", board="BBS1", start=0, images=True)).get("images")
        if got != [{"no": 1, "src": READ_IMAGE}]:
            wrong.append(f"--images 가 넘긴 주소가 그림 태그의 src 가 아니다: {got!r}")
    return wrong


def main() -> int:
    source = HAND.read_text(encoding="utf-8")
    passed, total = 0, 4
    wrong = judge_read(board())
    if wrong:
        print("어긋났다 — 읽은 글이 화면에서 보이는 글과 다르다:\n  " + "\n  ".join(wrong))
    else:
        passed += 1
        print("맞다 — 읽은 글에 안 보이는 글이 없고 그림 번호가 주소와 맞다")
    for name, where, old, new in READ_MUTANTS:
        mutant = board(old, new, where)
        if mutant is None:
            print(f"못 쟀다 — 물림을 다시 지을 일: 「{name}」 의 치환할 글자가 {where.name} 에 없다")
        elif judge_read(mutant):
            print(f"물림 — {name} 사본에 빨강을 봤다")
        else:
            print(f"물림이 안 문다 — 읽은 글 판정이 「{name}」 을 못 잡는다. 표본을 늘린다")
            total += 1
    wrong = judge(load(source, "xclick_under_check"))
    if wrong:
        print("어긋났다 — 뒤섞기가 화면과 다르다(게시판이 로그인 창을 낼 것이다):\n  " + "\n  ".join(wrong))
    else:
        passed += 1
        print("맞다 — 뒤섞기가 화면의 jQuery.encrypt 와 같다")
    wrong = judge_image(load(source, "xclick_under_check"))
    if wrong:
        print("어긋났다 — 본문 그림 손이 잰 꼴 밖을 묻는다:\n  " + "\n  ".join(wrong))
    else:
        passed += 1
        print("맞다 — 본문 그림 손이 잰 꼴만 묻는다")
    old, new = IMAGE_MUTANT
    if old not in source:
        print("못 쟀다 — 물림을 다시 지을 일: 그림 손의 치환할 글자가 xclick.py 에 없다")
    elif judge_image(load(source.replace(old, new, 1), "xclick_mutant")):
        print("물림 — 길을 안 보는 그림 손 사본에 빨강을 봤다")
    else:
        print("물림이 안 문다 — 그림 판정이 그 결함을 못 잡는다. 표본을 늘린다")
        total += 1
    wrong = judge_frame(load(source, "xclick_under_check"))
    if wrong:
        print("어긋났다 — 글 화면에서 꺼낸 본문의 표가 한 행 한 줄로 안 풀린다:\n  " + "\n  ".join(wrong))
    else:
        passed += 1
        print("맞다 — 글 화면에서 꺼낸 본문의 표가 한 행 한 줄이다")
    old, new = FRAME_MUTANT
    if old not in source:
        print("못 쟀다 — 물림을 다시 지을 일: 감싸개 벗기기의 치환할 글자가 xclick.py 에 없다")
    elif judge_frame(load(source.replace(old, new, 1), "xclick_mutant")):
        print("물림 — 감싸개를 안 벗기는 사본에 빨강을 봤다")
    else:
        print("물림이 안 문다 — 글 화면 판정이 그 결함을 못 잡는다. 표본을 늘린다")
        total += 1
    old, new = MUTANT
    if old not in source:
        print("못 쟀다 — 물림을 다시 지을 일: 치환할 글자가 xclick.py 에 없다")
    elif judge(load(source.replace(old, new, 1), "xclick_mutant")):
        print("물림 — 열쇠의 없는 칸을 되돌려 쓴 사본에 빨강을 봤다")
    else:
        print("물림이 안 문다 — 판정이 그 결함을 못 잡는다. 표본을 늘린다")
        total += 1
    print(f"통과 {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
