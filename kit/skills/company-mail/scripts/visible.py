"""보이는 글 — 메일 글에서 사람 눈에 안 보이는 것을 걷는 한 손. 메일을 모델이 읽게 내기 전에 지난다 — 받는 사람 눈에는 안 보이는데
모델에게만 읽히는 글(숨긴 지시)이 그대로 넘어가지 않게. 이 스킬의 명령(``mail.py``)과, 깔린 자리에서 이 손을 싣는 앱이 함께 쓴다.

부르는 꼴::

    v = visible.parse(html)                # Visible(text, hidden, comments) — HTML 에서 그려지는 글만
    v = visible.parse(html, quotes=True)   # 인용(`blockquote`) 안의 줄 머리에 `> ` — 인용을 경계로 읽는 쪽이 쓴다
    text, n = visible.invisible(text)      # 폭 없는 문자 · 방향 뒤집기 · 태그 문자 · 제어 문자를 걷고 그 수

`parse` 가 걷는 것 — 안 그리는 태그(스크립트 · 스타일 · 머리 · 개체 …) · 주석 · 숨긴 요소(`hidden` 속성 · display:none · visibility ·
투명 · 글자 크기 1.5px 이하 · 잘린 0 높이 · 화면 밖으로 민 글) · 바탕과 같은 색의 글. 스타일은 요소의 `style` 과
`<style>` 의 단순 선택자(태그 · .클래스 · #아이디) 규칙을 함께 본다. 그려진 화면이 아니라 마크업 · 스타일로 가른다. 깨진 HTML 도
끝까지 읽는다 — 못 닫은 숨긴 요소는 문서 끝까지 숨긴 것으로 본다(브라우저가 그렇게 그린다).

`parse` 가 내는 것 — `Visible`. 글은 그려진 꼴의 줄이다 — 블록 경계가 줄을 가르고, 마크업 안의 줄바꿈 · 겹친 빈칸은 한 빈칸이다(`<pre>`
밖). `hidden` 은 걷은 숨긴 덩이(실행 태그 · 숨긴 요소 · 바탕색 글)의 수, `comments` 는 걷은 주석의 글이다 — 주석은 어느 메일
프로그램도 안 그리는 글이라 걷기만 하고, 숨긴 덩이로 셀지는 부르는 쪽이 가른다(Outlook 의 조건부 주석은 거의 모든 메일에 있다).
폭 없는 문자는 `parse` 가 안 걷는다 — HTML 이 아닌 글(제목 · 이름 · 평문 본문)에도 들어 `invisible` 이 따로 걷는다.
표준 라이브러리만 쓴다.
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
_PAGE_BG = (255, 255, 255)     # 메일 프로그램의 기본 바탕 — 흰 글씨는 바탕을 안 정했으면 흰 바탕 위에 선다
_COLOR_NEAR = 24               # 글자색과 바탕이 채널마다 이만큼 안이면 안 보인다고 본다
_SKIP_TAGS = frozenset({"script", "style", "head", "title", "noscript", "template", "svg", "object",
                        "iframe", "xml", "meta", "link", "embed", "applet", "audio", "video", "canvas"})
_RUNS = frozenset({"script", "noscript", "template", "iframe", "object"})   # 걷으면 숨긴 덩이로 세는 안 그리는 태그
_VOID_TAGS = frozenset({"br", "img", "hr", "meta", "link", "input", "wbr", "col", "area", "base",
                        "source", "track", "embed", "param", "keygen"})
_BLOCK_TAGS = frozenset({"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol",
                         "blockquote", "hr", "section", "article", "header", "footer", "pre", "dl", "dt", "dd",
                         "center", "form", "fieldset", "address", "body", "html"})
_CLOSES_P = _BLOCK_TAGS - {"br", "body", "html"}
QUOTE_MARK = "> "              # 인용 안의 줄 머리 — 인용을 경계로 읽는 쪽이 이 꼴(`>`)을 읽는다


@dataclass(frozen=True)
class Visible:
    text: str
    hidden: int = 0                       # 걷은 숨긴 덩이
    comments: tuple[str, ...] = ()        # 걷은 주석의 글(빈 주석 빼고)


def _color(value: str) -> tuple[int, int, int] | str | None:
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
    # rgb(255,255,255) · rgb(255 255 255) · rgb(255 255 255 / 0.5) 를 다 받는다
    m = re.fullmatch(r"rgba?\(\s*(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\d+)\s*(?:[,/]\s*([\d.]+)\s*)?\)", v)
    if m:
        if m.group(4) is not None and float(m.group(4)) <= 0.05:
            return _TRANSPARENT
        return tuple(min(255, int(m.group(i))) for i in (1, 2, 3))  # type: ignore[return-value]
    return None


def _decls(style: str) -> dict[str, str]:
    out = {}
    for part in (style or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip().lower()
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
    """그 요소와 아래가 통째로 안 보이나 — 스타일 · 속성으로만 가른다(그려진 화면이 아니라). 잣대는 쓰는 사람이 메일을 여는
    웹메일(브라우저)이다 — Outlook 만 안 그리는 `mso-hide:all` · 흰 바탕이 아닌 곳의 흰 글씨 · 넘침을 안 자른 0 높이는 그 화면에
    그려지므로 숨긴 글이 아니다."""
    if "hidden" in attrs:
        return True
    if d.get("display", "").startswith("none") or d.get("visibility", "") in ("hidden", "collapse"):
        return True
    try:
        if "opacity" in d and float(d["opacity"].split()[0]) <= 0.05:
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


class _Parser(HTMLParser):
    """HTML → 보이는 글. 요소마다 (숨김 · 글자색 · 바탕) 을 쌓아 내려 보낸다."""

    def __init__(self, quotes: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.quotes = quotes
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool, Any, Any, bool]] = []   # (태그, 숨김, 글자색, 바탕, 줄바꿈을 그리나)
        self.skip = 0
        self.hidden = 0
        self.comments: list[str] = []
        self.rules: dict[str, dict[str, str]] = {}           # 단순 선택자 → 선언
        self._style_buf: list[str] | None = None
        self._counted: set[int] = set()
        self.pre = 0

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

    # 상태
    def _top(self) -> tuple[bool, Any, Any]:
        if self.stack:
            _, hid, col, bg, _ = self.stack[-1]
            return hid, col, bg
        return False, None, _PAGE_BG

    def _rules_for(self, tag: str, attrs: Mapping[str, str]) -> dict[str, str]:
        d: dict[str, str] = {}
        classes = (attrs.get("class") or "").split()
        keys = [tag] + [f".{c}" for c in classes] + [f"{tag}.{c}" for c in classes]
        if attrs.get("id"):
            keys += [f"#{attrs['id']}", f"{tag}#{attrs['id']}"]
        for k in keys:
            d.update(self.rules.get(k.lower(), {}))
        return d

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        if tag == "style":
            self._style_buf = []
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
        if tag == "br":
            self.parts.append("\n")
        elif tag in _BLOCK_TAGS:
            self._break()
        if tag == "pre":
            self.pre += 1
        if tag in ("td", "th"):
            self.parts.append(" ")
        if tag in _VOID_TAGS:
            return
        d = {**self._rules_for(tag, attrs), **_decls(attrs.get("style", ""))}
        hid, col, bg = self._top()
        if attrs.get("bgcolor"):
            d.setdefault("background-color", attrs["bgcolor"])
        if tag == "font" and attrs.get("color"):
            d.setdefault("color", attrs["color"])
        own_bg = _color(d.get("background-color", "")) or _color(d.get("background", "").split(" ")[0])
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
        self.handle_starttag(tag, attrs_list)
        if tag.lower() not in _VOID_TAGS and tag.lower() not in _SKIP_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            if tag == "style" and self._style_buf is not None:
                self._load_rules("".join(self._style_buf))
                self._style_buf = None
            self.skip = max(0, self.skip - 1)
            return
        if tag in _BLOCK_TAGS and tag != "br":
            self._break()
        if tag == "pre":
            self.pre = max(0, self.pre - 1)
        if any(t == tag for t, *_ in self.stack):
            while self.stack:
                t = self.stack.pop()[0]
                if t == tag:
                    break

    def handle_data(self, data: str) -> None:
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
        # 마크업 안의 줄바꿈은 그려지면 빈칸이다(`<pre>` 밖) — 안 그러면 `<br>` 뒤의 줄바꿈이 빈 줄로 서서 문단이 쪼개진다
        data = data if self.pre or (self.stack and self.stack[-1][4]) else data.replace("\n", " ")
        if self.quotes and data.strip() and any(t == "blockquote" for t, *_ in self.stack):
            if self._line_open():
                self.parts.append(QUOTE_MARK)
            data = data.replace("\n", "\n" + QUOTE_MARK)
        self.parts.append(data)

    def handle_comment(self, data: str) -> None:
        # 주석은 메일 프로그램도 안 그리고 LLM 에도 안 간다 — 글만 넘기고, 숨긴 글로 셀지는 부르는 쪽이 가른다
        if data.strip():
            self.comments.append(data)

    def _load_rules(self, css: str) -> None:
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            d = _decls(body)
            for one in sel.split(","):
                one = one.strip().lower()
                if re.fullmatch(r"[a-z0-9]*(?:[.#][\w-]+)?", one) and one:
                    self.rules.setdefault(one, {}).update(d)


def parse(html: str, *, quotes: bool = False) -> Visible:
    """HTML 한 편 → `Visible`. `quotes` 면 인용 안의 글 줄 머리에 `QUOTE_MARK` 를 단다. 예외를 안 올린다 — `html.parser` 가
    넘어지면 받은 데까지 쓴다."""
    p = _Parser(quotes)
    try:
        p.feed(html or "")
        p.close()
    except Exception:   # noqa: BLE001 — html.parser 는 거의 안 넘어지지만 넘어지면 받은 데까지 쓴다
        pass
    lines = [" ".join(x.split()) for x in "".join(p.parts).split("\n")]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return Visible(text, p.hidden, tuple(p.comments))


def invisible(text: str) -> tuple[str, int]:
    """(걷은 글, 걷은 수). 서식 문자(폭 없는 문자 · 방향 뒤집기 · 태그 문자)와 줄바꿈 · 탭 밖의 제어 문자를 걷는다 — 낱말을 쪼개
    눈에 안 띄게 하거나 파일 확장자를 뒤집어 보이는 수를 막는다. 글자를 바꾸지는 않는다(호환 글자 고르기는 부르는 쪽 몫)."""
    out, gone = [], 0
    for ch in (text or "").replace("\r\n", "\n").replace("\r", "\n"):
        cat = unicodedata.category(ch)
        if cat == "Cf" or (cat == "Cc" and ch not in "\n\t"):
            gone += 1
            continue
        out.append(ch)
    return "".join(out), gone
