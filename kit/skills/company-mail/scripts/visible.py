"""보이는 글 — 사내 앱의 본문 HTML(메일 · 게시글 · 사규)에서 사람 눈에 안 보이는 것을 걷고 읽을 글자로 푼다. 모델에게 글을 내기 전에
지나는 자리라, 숨긴 지시가 대화로 넘어가지 않는다. 이 스킬의 명령 · 형제 스킬 company-board · company-regulation · 이 손을 싣는 앱이
함께 쓰는 한 벌이다.

부르는 꼴::

    v = visible.parse(html)                # Visible(text, hidden, comments, images) — HTML 에서 그려지는 글만
    v = visible.parse(html, quotes=True)   # 인용(`blockquote`) 안의 줄 머리에 `> ` — 인용을 경계로 읽는 쪽이 쓴다
    v = visible.parse(html, tables=True)   # 표 꼴 — 표의 한 행이 한 줄이고 칸을 `TABLE_SEP` 로 가른다(게시글 · 사규 본문)
    v = visible.parse(html, tables=True, numbered=False)   # 그림을 번호 없는 「[그림]」 으로 — 받을 길이 없는 조각(사규의 바뀐 자리)
    v = visible.body(html)                 # 표 꼴로 풀고 글에서 보이지 않는 문자까지 걷은 것 — JSON 으로 답하는 명령의 본문
    text, n = visible.invisible(text)      # 폭 없는 문자 · 방향 뒤집기 · 태그 문자 · 제어 문자를 걷고 그 수

`parse` 는 안 그리는 태그 · 주석 · 숨긴 요소 · 바탕과 같은 색의 글을 걷는다. 그려진 화면이 아니라 마크업 · 스타일(요소의 `style` 과
`<style>` 의 단순 선택자 규칙)로 가르고, 못 닫은 숨긴 요소는 브라우저처럼 문서 끝까지 숨긴다. 무엇을 걷나는 어느 꼴로 부르든 같다.

`Visible` — `text` 는 그려진 꼴의 줄이고, 그림은 그 자리에 「[그림 N]」 으로 서며 주소는 `images` 의 N 번째다. `hidden` 은 걷은 숨긴 덩이의
수, `comments` 는 걷은 주석의 글이다 — 주석을 숨긴 덩이로 셀지는 부르는 쪽이 가른다. 폭 없는 문자는 `parse` 가 안 걷는다 — HTML 아닌
글(제목 · 이름 · 평문)에도 들어 `invisible` 이 따로 걷는다.

표 꼴(`tables=True`) — 표의 한 행이 한 줄이고 칸을 `TABLE_SEP` 로 가른다. 합친 칸은 차지한 자리마다 같은 글자를 되풀이하고 숨긴 칸은
글자만 빠져, 줄마다 칸 수가 같다. 칸 안에 든 표는 행을 `ROW_SEP` 로 잇는다. `quotes` 는 표 꼴에 안 건다. 표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

_NAMED_COLORS = {"white": (255, 255, 255), "snow": (255, 250, 250), "ivory": (255, 255, 240),
                 "whitesmoke": (245, 245, 245), "ghostwhite": (248, 248, 255), "floralwhite": (255, 250, 240),
                 "azure": (240, 255, 255), "mintcream": (245, 255, 250), "honeydew": (240, 255, 240),
                 "aliceblue": (240, 248, 255), "seashell": (255, 245, 238), "lavenderblush": (255, 240, 245),
                 "oldlace": (253, 245, 230), "linen": (250, 240, 230), "cornsilk": (255, 248, 220),
                 "lightyellow": (255, 255, 224), "beige": (245, 245, 220), "black": (0, 0, 0), "red": (255, 0, 0),
                 "silver": (192, 192, 192), "gray": (128, 128, 128), "grey": (128, 128, 128), "navy": (0, 0, 128),
                 "blue": (0, 0, 255)}
_TRANSPARENT = "transparent"
_IMPORTANT = re.compile(r"!\s*important\s*$", re.IGNORECASE)
_PAGE_BG = (255, 255, 255)     # 메일 프로그램의 기본 바탕 — 흰 글씨는 바탕을 안 정했으면 흰 바탕 위에 선다
_COLOR_NEAR = 24               # 글자색과 바탕이 채널마다 이만큼 안이면 안 보인다고 본다
_SKIP_TAGS = frozenset({"script", "style", "head", "title", "noscript", "template", "svg", "object",
                        "iframe", "xml", "meta", "link", "embed", "applet", "audio", "video", "canvas"})
_RUNS = frozenset({"script", "noscript", "template", "iframe", "object"})   # 걷으면 숨긴 덩이로 세는 안 그리는 태그
_SELF_CLOSED = frozenset({"svg"})   # 안 그리는 태그 가운데 `<svg/>` 꼴로 제 자리에서 닫히는 것 — 안 닫으면 그 뒤의 글이 문서 끝까지 걷힌다
_VOID_TAGS = frozenset({"br", "img", "hr", "meta", "link", "input", "wbr", "col", "area", "base",
                        "source", "track", "embed", "param", "keygen"})
_BLOCK_TAGS = frozenset({"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol",
                         "blockquote", "hr", "section", "article", "header", "footer", "pre", "dl", "dt", "dd",
                         "center", "form", "fieldset", "address", "body", "html"})
_CLOSES_P = _BLOCK_TAGS - {"br", "body", "html"}
IMAGE_WORD = "그림"             # 글 안에서 그려지는 그림의 자리 — 「[그림 N]」, N 은 ``Visible.images`` 의 차례
QUOTE_MARK = "> "              # 인용 안의 줄 머리 — 인용을 경계로 읽는 쪽이 이 꼴(`>`)을 읽는다
TABLE_SEP = " | "              # 표 꼴에서 한 행의 칸을 가르는 자리 — 표의 행인가를 이 글자로 가리는 쪽도 이 이름을 읽는다
ROW_SEP = " / "                # 표 꼴에서 칸 안에 든 표의 행을 잇는 자리
_SPAN_MAX = 200                # colspan · rowspan 으로 받는 가장 큰 수 — 깨진 값이 한 줄을 끝없이 늘리지 않게
# 표 꼴에서 앞뒤로 줄을 가르는 블록 — 줄만 긋는 것(br · hr)과 표의 뼈대(tr · table)는 그 꼴이 따로 다룬다
_PARA_TAGS = _BLOCK_TAGS - {"br", "hr", "tr", "table"}


@dataclass(frozen=True)
class Visible:
    """본문 HTML 을 푼 결과 — 보이는 글 · 걷은 숨긴 덩이 수 · 주석 글 · 그림 주소(꼴은 머리말)."""
    text: str
    hidden: int = 0                       # 걷은 숨긴 덩이
    comments: tuple[str, ...] = ()        # 걷은 주석의 글(빈 주석 빼고)
    images: tuple[str, ...] = ()          # 그려지는 그림의 주소 — 본문 차례 · 글의 「[그림 N]」 의 N 번째(1 부터)


def _color(value: str) -> tuple[int, int, int] | str | None:
    """CSS 색 값 → (R, G, B) · 「transparent」 · 모르면 None — 이름 몇 · #hex · rgb()/rgba() 만 읽고, 거의 투명한 rgba 는 투명이다."""
    v = (value or "").strip().lower().replace("!important", "").strip()
    if not v:
        return None
    if v == _TRANSPARENT:
        return _TRANSPARENT
    if v in _NAMED_COLORS:
        return _NAMED_COLORS[v]
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    m = re.fullmatch(r"rgba?\(\s*(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\d+)\s*(?:[,/]\s*([\d.]+)\s*)?\)", v)
    if m:
        if m.group(4) is not None and float(m.group(4)) <= 0.05:
            return _TRANSPARENT
        return tuple(min(255, int(m.group(i))) for i in (1, 2, 3))  # type: ignore[return-value]
    return None


def _decls(style: str) -> dict[str, str]:
    """선언 글 → {속성: 값}. 값의 `!important` 는 뗀다 — 남기면 `visibility:hidden !important` 같은 값이 숨김 판정에 안 걸린다."""
    out = {}
    for part in (style or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = _IMPORTANT.sub("", v).strip().lower()
    return out


def _length(v: str) -> float | None:
    """CSS 길이를 px 로 어림 — 모르는 단위는 None. 0 은 단위와 상관없이 0 이다."""
    m = re.match(r"^\s*(-?[\d.]+)\s*(px|pt|em|rem|%|)?", v or "")
    if not m:
        return None
    n = float(m.group(1))
    unit = m.group(2) or "px"
    return n if n == 0 else {"px": n, "pt": n * 4 / 3, "em": n * 16, "rem": n * 16, "%": n * 0.16}.get(unit)


def _hard_hidden(d: Mapping[str, str], attrs: Mapping[str, str]) -> bool:
    """그 요소와 아래가 통째로 안 보이나 — 스타일 · 속성으로 가른다. 잣대는 메일을 여는 웹메일(브라우저)이라, Outlook 만 안 그리는
    `mso-hide:all` · 넘침을 안 자른 0 높이는 숨긴 글이 아니다."""
    if "hidden" in attrs:
        return True
    if d.get("display", "").startswith("none") or d.get("visibility", "") in ("hidden", "collapse"):
        return True
    opacity = d.get("opacity", "").split()[:1]
    try:
        if opacity and float(opacity[0].rstrip("%")) / (100 if opacity[0].endswith("%") else 1) <= 0.05:   # `0%` 꼴도 투명이다
            return True
    except ValueError:
        pass
    size = _length(d.get("font-size", ""))
    if size is not None and size <= 1.5:
        return True
    clipped = "hidden" in d.get("overflow", "") or "hidden" in d.get("overflow-y", "")
    for k in ("height", "max-height", "width", "max-width"):
        n = _length(d.get(k, ""))
        if n is not None and n <= 1 and clipped:
            return True
    n = _length(d.get("text-indent", ""))
    if n is not None and n <= -500:
        return True
    if d.get("position", "") in ("absolute", "fixed"):
        for k in ("left", "top"):
            n = _length(d.get(k, ""))
            if n is not None and n <= -500:
                return True
    return False


def _span(raw) -> int:
    """colspan · rowspan 값 — 수가 아니거나 1 보다 작으면 1."""
    try:
        return max(1, min(int(raw), _SPAN_MAX))
    except (TypeError, ValueError):
        return 1


class _Table:
    """표 하나 — 행을 칸 목록으로 모아 한 줄씩 낸다. 합친 칸은 차지한 자리마다 같은 글자를 채운다(줄마다 열이 맞게)."""

    def __init__(self):
        self.lines: list[str] = []
        self.row: list[str] | None = None
        self.in_cell = False
        self.carry: dict[int, tuple[int, str]] = {}   # 열 → (아래로 더 채울 행 수, 글자) — 세로로 합친 칸

    def _fill(self) -> None:
        """지금 행의 다음 자리가 위에서 세로로 합친 칸이면 그 글자로 채워 나간다."""
        while len(self.row) in self.carry:
            left, text = self.carry.pop(len(self.row))
            if left > 1:
                self.carry[len(self.row)] = (left - 1, text)
            self.row.append(text)

    def cell(self, text: str, colspan: int, rowspan: int) -> None:
        """칸 하나를 지금 행에 넣는다 — 가로로 합친 수만큼 되풀이하고, 세로로 합쳤으면 아래 행에 채울 글자로 남긴다."""
        if self.row is None:
            self.row = []
        for _ in range(colspan):
            self._fill()
            if rowspan > 1:
                self.carry[len(self.row)] = (rowspan - 1, text)
            self.row.append(text)

    def close_row(self) -> None:
        """지금 행을 닫아 칸을 TABLE_SEP 로 이은 한 줄로 낸다 — 빈 행은 안 내고, 이 행이 안 닿은 세로 합친 칸도 한 행을 센다."""
        if self.row is None:
            return
        self._fill()
        for col in [c for c in self.carry if c >= len(self.row)]:   # 이 행이 안 닿은 자리의 합친 칸 — 행 수만 센다
            left, text = self.carry.pop(col)
            if left > 1:
                self.carry[col] = (left - 1, text)
        if any(self.row):
            self.lines.append(TABLE_SEP.join(self.row))
        self.row = None


class _Parser(HTMLParser):
    """HTML → 보이는 글. 요소마다 (숨김 · 글자색 · 바탕) 을 쌓아 내려 보낸다. 무엇이 보이나는 이 클래스가 가르고, 보이는 것을 어떤 줄로
    적나는 갈고리 넷(`_open` · `_close` · `_image` · `_text`)과 `text` 가 든다 — 여기 것은 그려진 꼴의 줄이다."""

    def __init__(self, quotes: bool, numbered: bool = True) -> None:
        super().__init__(convert_charrefs=True)
        self.quotes = quotes
        self.numbered = numbered
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool, Any, Any, bool]] = []   # (태그, 숨김, 글자색, 바탕, 줄바꿈을 그리나)
        self.skip = 0
        self.head = 0       # 안 닫힌 `<head>` 의 수 — `</head>` 는 빼도 되는 태그라, `<body>` 가 오면 브라우저처럼 거기서 닫는다
        self.hidden = 0
        self.comments: list[str] = []
        self.rules: dict[str, dict[str, str]] = {}           # 단순 선택자 → 선언
        self._style_buf: list[str] | None = None
        self._counted: set[int] = set()
        self.pre = 0
        self.images: list[str] = []

    def _break(self) -> None:
        """블록 경계 — 글 없이 잇단 경계는 한 줄바꿈이다. 빈 블록(`<p>&nbsp;</p>`)만 빈 줄을 낸다 — 빈 줄이 문단을 가른다."""
        j = len(self.parts) - 1
        while j >= 0 and self.parts[j] != "\n" and not self.parts[j].strip(" \t\r\n"):
            j -= 1          # 마크업 사이의 줄바꿈 · 빈칸은 글이 아니다 — `&nbsp;` 는 글이다
        if j < 0 or self.parts[j] == "\n":
            return
        self.parts.append("\n")

    def _line_open(self) -> bool:
        """지금 쓰는 자리가 줄 머리인가 — 앞에 글 없이 줄바꿈(또는 문서 머리)만 있다."""
        for p in reversed(self.parts):
            if p.endswith("\n"):
                return True
            if p.strip(" \t\r\n"):
                return False
        return True

    # 줄 — 그려진 꼴
    def _open(self, tag: str, attrs: Mapping[str, str]) -> None:
        """여는 태그가 긋는 줄 경계."""
        if tag == "br":
            self.parts.append("\n")
        elif tag in _BLOCK_TAGS:
            self._break()
        if tag == "pre":
            self.pre += 1
        if tag in ("td", "th"):
            self.parts.append(" ")

    def _close(self, tag: str) -> None:
        """닫는 태그가 긋는 줄 경계."""
        if tag in _BLOCK_TAGS and tag != "br":
            self._break()
        if tag == "pre":
            self.pre = max(0, self.pre - 1)

    def _image(self, mark: str) -> None:
        """그려지는 그림의 자리 표지를 적는다."""
        self.parts.append(mark)

    def _text(self, data: str) -> None:
        """보이는 글 한 조각을 적는다."""
        # 마크업 안의 줄바꿈은 그려지면 빈칸이다(`<pre>` 밖) — 안 그러면 `<br>` 뒤의 줄바꿈이 빈 줄로 서서 문단이 쪼개진다
        data = data if self.pre or (self.stack and self.stack[-1][4]) else data.replace("\n", " ")
        if self.quotes and data.strip() and any(t == "blockquote" for t, *_ in self.stack):
            if self._line_open():
                self.parts.append(QUOTE_MARK)
            data = data.replace("\n", "\n" + QUOTE_MARK)
        self.parts.append(data)

    def text(self) -> str:
        """다 읽은 뒤의 글 — 줄마다 겹친 빈칸을 하나로, 잇단 빈 줄을 하나로."""
        lines = [" ".join(x.split()) for x in "".join(self.parts).split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

    # 상태
    def _top(self) -> tuple[bool, Any, Any]:
        """지금 요소의 (숨김, 글자색, 바탕) — 쌓인 것이 없으면 안 숨김 · 색 없음 · 흰 바탕."""
        if self.stack:
            _, hid, col, bg, _ = self.stack[-1]
            return hid, col, bg
        return False, None, _PAGE_BG

    def _rules_for(self, tag: str, attrs: Mapping[str, str]) -> dict[str, str]:
        """`<style>` 에서 모은 단순 선택자 규칙 가운데 이 요소(태그 · 클래스 · id)에 걸리는 선언을 합친다."""
        d: dict[str, str] = {}
        classes = (attrs.get("class") or "").split()
        keys = [tag] + [f".{c}" for c in classes] + [f"{tag}.{c}" for c in classes]
        if attrs.get("id"):
            keys += [f"#{attrs['id']}", f"{tag}#{attrs['id']}"]
        for k in keys:
            d.update(self.rules.get(k.lower(), {}))
        return d

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        """여는 태그 하나 — 안 그리는 태그는 건너뛸 깊이로 세고, 그 밖은 줄 경계와 그림 자리를 적은 뒤 규칙 · 스타일로 가린 (숨김 · 글자색 · 바탕) 을 쌓는다."""
        tag = tag.lower()
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        if tag == "style":
            self._style_buf = []
        if tag == "head":
            self.head += 1
        elif tag == "body" and self.head:
            self.skip, self.head = max(0, self.skip - self.head), 0
        if tag in _SKIP_TAGS:
            if tag not in _VOID_TAGS:
                self.skip += 1
            self.hidden += tag in _RUNS
            return
        if tag in _CLOSES_P and any(t == "p" for t, *_ in self.stack):
            while self.stack and self.stack[-1][0] != "p":
                self.stack.pop()
            if self.stack:
                self.stack.pop()
        self._open(tag, attrs)
        # 그림의 숨김도 `<style>` 규칙과 제 `style` 을 함께 본다 — 제 `style` 만 보면 클래스로 숨긴 그림이 글에 서고 파일로 받아진다
        if (tag == "img" and not self.skip and not self._top()[0]
                and not _hard_hidden({**self._rules_for(tag, attrs), **_decls(attrs.get("style", ""))}, attrs)):
            src = attrs.get("src", "").strip()
            if src:
                self.images.append(src)
                self._image(f"[{IMAGE_WORD} {len(self.images)}]" if self.numbered else f"[{IMAGE_WORD}]")
        if tag in _VOID_TAGS:
            return
        d = {**self._rules_for(tag, attrs), **_decls(attrs.get("style", ""))}
        hid, col, bg = self._top()
        if attrs.get("bgcolor"):
            d.setdefault("background-color", attrs["bgcolor"])
        if tag == "font" and attrs.get("color"):
            d.setdefault("color", attrs["color"])
        # 줄임 꼴 `background` 의 색은 어느 자리에도 선다(`url(…) #000`) — 첫 낱말만 보면 어두운 바탕의 흰 글씨를 숨긴 글로 걷는다
        own_bg = _color(d.get("background-color", "")) or next(
            (c for c in map(_color, d.get("background", "").split()) if c is not None), None)
        if own_bg is not None and own_bg != _TRANSPARENT:
            bg = own_bg
        own_col = _color(d.get("color", ""))
        if own_col is not None:
            col = own_col
        now_hidden = hid or _hard_hidden(d, attrs)
        if now_hidden and not hid:
            self.hidden += 1
        # `white-space: pre · pre-wrap · pre-line · break-spaces` 는 마크업 안의 줄바꿈을 그린다 — 브라우저처럼 물려받고, 다른 값이 끊는다
        ws = d.get("white-space", "").strip().lower()
        keeps = (ws.startswith("pre") or ws == "break-spaces") if ws else bool(self.stack and self.stack[-1][4])
        self.stack.append((tag, now_hidden, col, bg, keeps))

    def handle_startendtag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        """`<tag/>` 꼴 — 여는 태그로 받고, 브라우저가 그 자리에서 닫는 요소만 곧바로 닫는다."""
        self.handle_starttag(tag, attrs_list)
        tag = tag.lower()
        # HTML 요소의 `/>` 는 브라우저가 닫음으로 안 받는다(`<script/>` 는 열린 채다) — 바깥 요소(`_SELF_CLOSED`)만 그 자리에서 닫힌다
        if tag not in _VOID_TAGS and (tag not in _SKIP_TAGS or tag in _SELF_CLOSED):
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        """닫는 태그 하나 — 안 그리는 태그면 건너뛸 깊이를 풀고(`<style>` 이면 모은 규칙을 싣고), 그 밖은 줄 경계를 긋고 그 요소까지 쌓인 것을 걷는다."""
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            if tag == "head":
                if not self.head:
                    return      # `<body>` 가 이미 닫은 머리 — 다시 빼면 본문의 다른 숨김이 풀린다
                self.head -= 1
            if tag == "style" and self._style_buf is not None:
                self._load_rules("".join(self._style_buf))
                self._style_buf = None
            self.skip = max(0, self.skip - 1)
            return
        self._close(tag)
        if any(t == tag for t, *_ in self.stack):
            while self.stack:
                t = self.stack.pop()[0]
                if t == tag:
                    break

    def handle_data(self, data: str) -> None:
        """글 조각 하나 — 안 그리는 태그 · 숨긴 요소 안이면 버리고, 바탕과 같은 색이면 걷어 숨긴 덩이로 세고, 보이면 적는다."""
        if self._style_buf is not None:
            self._style_buf.append(data)
        if self.skip:
            return
        hid, col, bg = self._top()
        if hid:
            return
        if col is not None and (col == _TRANSPARENT
                                or all(abs(a - b) <= _COLOR_NEAR for a, b in zip(col, bg))):
            if data.strip():
                key = id(self.stack[-1]) if self.stack else -1
                if key not in self._counted:
                    self._counted.add(key)
                    self.hidden += 1
            return
        self._text(data)

    def handle_comment(self, data: str) -> None:
        """빈 주석이 아니면 그 글을 `comments` 에 모으고 본문에는 안 적는다."""
        # 주석은 메일 프로그램도 안 그리고 LLM 에도 안 간다 — 글만 넘기고, 숨긴 글로 셀지는 부르는 쪽이 가른다
        if data.strip():
            self.comments.append(data)

    def _load_rules(self, css: str) -> None:
        """`<style>` 글에서 단순 선택자(태그 · .클래스 · #id 와 그 짝)의 규칙만 골라 `rules` 에 더한다."""
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            d = _decls(body)
            for one in sel.split(","):
                one = one.strip().lower()
                if re.fullmatch(r"[a-z0-9]*(?:[.#][\w-]+)?", one) and one:
                    self.rules.setdefault(one, {}).update(d)


class _TableParser(_Parser):
    """HTML → 표 꼴의 줄. 무엇이 보이나는 `_Parser` 그대로고 줄을 적는 갈고리만 다르다 — 숨긴 요소 안에서도 표의 뼈대는 따라가
    열이 안 밀리게 한다. 안 그리는 태그(`skip`) 안의 뼈대는 안 본다."""

    def __init__(self, numbered: bool) -> None:
        super().__init__(False, numbered)
        self.tables: list[_Table] = []                   # 열린 표 — 겹치면 여럿
        self.cells: list[tuple[list, int, int]] = []     # 열린 칸 — (글자 통, colspan, rowspan)

    def _write(self, piece: str) -> None:
        """글 조각을 열린 칸이 있으면 그 칸에, 없으면 본문에 적는다."""
        (self.cells[-1][0] if self.cells else self.parts).append(piece)

    def _close_cell(self, table: _Table) -> None:
        """열린 칸이 있으면 모은 글자를 한 줄로 접어 표에 넣고 닫는다."""
        if table.in_cell:
            buf, colspan, rowspan = self.cells.pop()
            table.cell(re.sub(r"\s+", " ", "".join(buf)).strip(), colspan, rowspan)
            table.in_cell = False

    def _close_table(self) -> None:
        """맨 안쪽 표를 닫아 그 줄들을 내놓는다 — 칸 안에 든 표면 ROW_SEP 로 이어 그 칸에, 아니면 본문에 줄로 적는다."""
        table = self.tables[-1]
        self._close_cell(table)
        table.close_row()
        self.tables.pop()
        if self.cells:                                   # 칸 안에 든 표 — 그 칸의 한 줄에 잇는다
            self._write(" " + ROW_SEP.join(table.lines) + " ")
        else:
            self._write("\n" + "\n".join(table.lines) + "\n")

    def _open(self, tag: str, attrs: Mapping[str, str]) -> None:
        """여는 태그가 표의 뼈대(표 · 행 · 칸)를 열거나 줄을 가른다 — 안 그리는 태그 안에서는 안 본다."""
        if self.skip:
            return
        table = self.tables[-1] if self.tables else None
        if tag == "table":
            self.tables.append(_Table())
        elif tag == "tr" and table:
            self._close_cell(table)
            table.close_row()
            table.row = []
        elif tag in ("td", "th") and table:
            self._close_cell(table)
            self.cells.append(([], _span(attrs.get("colspan")), _span(attrs.get("rowspan"))))
            table.in_cell = True
        elif tag in _PARA_TAGS or tag in ("br", "hr", "tr", "td", "th"):
            self._write("\n")

    def _close(self, tag: str) -> None:
        """닫는 태그가 칸 · 행 · 표를 닫거나 줄을 가른다 — 안 그리는 태그 안에서는 안 본다."""
        if self.skip:
            return
        table = self.tables[-1] if self.tables else None
        if tag in ("td", "th") and table:
            self._close_cell(table)
        elif tag == "tr" and table:
            self._close_cell(table)
            table.close_row()
        elif tag == "table" and table:
            self._close_table()
        elif tag in _PARA_TAGS:
            self._write("\n")

    def _image(self, mark: str) -> None:
        """그림 자리 표지를 앞뒤 빈칸과 함께 지금 칸이나 본문에 적는다."""
        self._write(f" {mark} ")

    def _text(self, data: str) -> None:
        """보이는 글 한 조각을 적는다 — 표 안 · 칸 밖의 글자(표 제목)는 표의 한 줄로 따로 세운다."""
        data = data.replace("\xa0", " ")
        table = self.tables[-1] if self.tables else None
        if table and not table.in_cell:                  # 표 안 · 칸 밖 — 태그 사이의 줄바꿈은 버리고 글자(표 제목)는 한 줄로
            word = re.sub(r"\s+", " ", data).strip()
            if word:
                table.lines.append(word)
            return
        self._write(data)

    def text(self) -> str:
        """다 읽은 뒤의 표 꼴 글 — 안 닫힌 표를 모은 데까지 닫고, 줄마다 겹친 빈칸을 하나로, 잇단 빈 줄을 하나로."""
        while self.tables:                               # 안 닫힌 표 — 모은 데까지 낸다
            self._close_table()
        lines = [re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in "".join(self.parts).split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def parse(html: str, *, quotes: bool = False, tables: bool = False, numbered: bool = True) -> Visible:
    """HTML 한 편 → `Visible`(꼴은 머리말). `numbered` 가 거짓이면 그림 자리가 번호 없는 「[그림]」 이고 주소는 그대로 `images` 에 든다.
    예외를 안 올린다 — `html.parser` 가 넘어지면 받은 데까지 쓴다."""
    p = _TableParser(numbered) if tables else _Parser(quotes, numbered)
    try:
        p.feed(html or "")
        p.close()
    except Exception:   # noqa: BLE001 — html.parser 는 거의 안 넘어지지만 넘어지면 받은 데까지 쓴다
        pass
    return Visible(p.text(), p.hidden, tuple(p.comments), tuple(p.images))


def body(html: str | None, *, numbered: bool = True) -> Visible:
    """본문 HTML 한 편 → JSON 으로 답하는 명령이 실을 `Visible` — 표 꼴로 풀고 보이지 않는 문자까지 걷은 글이다. 이어 읽기의 자리 ·
    글자 수는 이 글로 센다 — 그래야 답에 실린 글과 맞는다."""
    v = parse(html or "", tables=True, numbered=numbered)
    return Visible(invisible(v.text)[0], v.hidden, v.comments, v.images)


def invisible(text: str) -> tuple[str, int]:
    """(걷은 글, 걷은 수). 서식 문자(폭 없는 문자 · 방향 뒤집기 · 태그 문자)와 줄바꿈 · 탭 밖의 제어 문자를 걷는다. 글자를 바꾸지는
    않는다 — 호환 글자 고르기는 부르는 쪽 몫이다."""
    out, gone = [], 0
    for ch in (text or "").replace("\r\n", "\n").replace("\r", "\n"):
        cat = unicodedata.category(ch)
        if cat == "Cf" or (cat == "Cc" and ch not in "\n\t"):
            gone += 1
            continue
        out.append(ch)
    return "".join(out), gone
