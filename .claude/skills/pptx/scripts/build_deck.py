# -*- coding: utf-8 -*-
"""임원 보고용 덱을 데이터(JSON) 또는 원자 부품(Atomic Primitives)으로 빌드하는 레이아웃 엔진.

두 가지 방식으로 사용할 수 있습니다:
1. [상위 레시피] 데이터(JSON)를 넘겨 8대 표준 슬라이드를 즉시 생성
   python build_deck.py deck.json -o out.pptx

2. [원자 부품 조립 (Atomic Primitives)] 레고 블록처럼 원하는 부품을 1장 안에서 자유롭게 합성
   from build_deck import Deck, Card, Grid, Split, MetricBox, Badge, KickerHeader, StepCard, TableBox, CalloutBanner, FormField

   deck = Deck()
   slide = deck.add_slide()
   top = KickerHeader(slide, kicker="2026 전략", title="핵심 추진 과제", lead="상반기 중점 실행 로드맵")
   split = Split(MARGIN, top, deck.cw, deck.H - MARGIN - top, direction='h', ratios=[0.4, 0.6], gap=0.3)

   # 좌측: 지표 2개 (Grid + Card + MetricBox)
   grid_left = Grid(*split[0], rows=2, cols=1, gap_y=0.2)
   card1 = Card(grid_left[0], slide=slide)
   MetricBox(card1, "98.5%", "공정 가동률", "전월 대비 2.1%p 상승")
   card2 = Card(grid_left[1], slide=slide)
   MetricBox(card2, "0 건", "중대 재해", "365일 무재해 달성")

   # 우측: 3단계 카드 (Grid + Card + StepCard)
   grid_right = Grid(*split[1], rows=3, cols=1, gap_y=0.15)
   for i, st in enumerate([("1단계", ["요건 정의"]), ("2단계", ["실증 검증"]), ("3단계", ["전사 확산"])]):
       card_s = Card(grid_right[i], slide=slide)
       StepCard(card_s, step_no=i+1, title=st[0], items=st[1])

설계 규약:
- 상단 헤더 바 · 측면 스트라이프 · 제목 밑줄을 그리지 않는다.
- 카드 구분은 은은한 테두리와 그림자가 들고, 강조는 큰 숫자와 원형 배지가 든다.
- 넘치는 글은 엔진이 먼저 줄인다(자동 축소).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from typing import Any

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

# ---------------------------------------------------------------- 지면 규격
PAGE_SIZES = {
    "a4-landscape": (11.693, 8.268),   # 297 x 210 mm
    "16:9": (13.333, 7.5),
    "4:3": (10.0, 7.5),
}
DEFAULT_PAGE = "a4-landscape"

MARGIN = 0.6           # 최소 여백
GAP = 0.3              # 블록 사이 간격
PAD = 0.3              # 카드 내부 패딩

SHADOW_XML = (
    '<a:outerShdw xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'blurRad="63500" dist="19050" dir="5400000" rotWithShape="0">'
    '<a:srgbClr val="0F172A"><a:alpha val="10000"/></a:srgbClr></a:outerShdw>'
)


@dataclass
class Theme:
    """색과 글꼴. 한 색이 지배하고(dark/primary), 보조 하나, 악센트 하나."""

    dark: str = "0B192C"            # 표지·마무리 배경 (지배색)
    dark_panel: str = "0F2036"      # 다크 카드
    dark_line: str = "1F3A5C"       # 다크 위 테두리·모티프
    primary: str = "0B192C"         # 라이트 위 제목·강조
    secondary: str = "2F4A6D"       # 보조
    accent: str = "E65100"          # 악센트 (라이트 배경)
    accent_on_dark: str = "FFA726"  # 악센트 (다크 배경)
    light_bg: str = "F8FAFC"
    card: str = "FFFFFF"
    border: str = "E2E8F0"
    tint: str = "F1F5F9"            # 카드 안 강조 블록
    text: str = "1E293B"
    muted: str = "64748B"
    dim: str = "94A3B8"
    on_dark: str = "FFFFFF"
    on_dark_muted: str = "A8BBD4"
    ok: str = "2E7D32"
    warn: str = "E8A000"
    bad: str = "C62828"
    font: str = "맑은 고딕"

    @classmethod
    def from_dict(cls, data):
        known = set(cls.__dataclass_fields__)
        unknown = set(data or {}) - known
        if unknown:
            raise ValueError("theme 에 모르는 키: %s" % ", ".join(sorted(unknown)))
        return cls(**(data or {}))


# ------------------------------------------------------------ 글 높이 어림
_CJK_RANGES = ((0x1100, 0x11FF), (0x2E80, 0xA4CF), (0xAC00, 0xD7A3),
               (0xF900, 0xFAFF), (0xFE30, 0xFE4F), (0xFF00, 0xFF60))


def _is_wide(ch):
    o = ord(ch)
    return any(lo <= o <= hi for lo, hi in _CJK_RANGES)


def _line_count(text, width_in, size_pt):
    """폭 안에서 몇 줄로 접히는지 어림한다 (전각 1.0 · 반각 0.52 기준)."""
    if not text:
        return 1
    total = 0
    for raw in str(text).split("\n"):
        if not raw:
            total += 1
            continue
        units = sum(1.0 if _is_wide(c) else 0.52 for c in raw)
        per_line = max(1.0, width_in * 0.95 / (size_pt / 72.0))
        total += max(1, int(math.ceil(units / per_line)))
    return total


def _block_height(paras, width_in, scale=1.0):
    """문단 목록이 차지하는 높이(인치)를 어림한다."""
    h = 0.0
    for p in paras:
        size = p["size"] * scale
        lines = _line_count(p["text"], width_in, size)
        h += lines * (size / 72.0) * p.get("line", 1.2) * 1.15
        h += p.get("before", 0) / 72.0
    return h


# ------------------------------------------------- 로우레벨 PPTX 스타일 및 렌더 도구
def _style_run(run, size, bold, color, italic=False, spacing=None, font="맑은 고딕"):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = font
    f.color.rgb = RGBColor.from_string(color)
    rPr = f._rPr
    rPr.set("lang", "ko-KR")
    rPr.set("altLang", "en-US")
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", font)
    if spacing is not None:
        rPr.set("spc", str(int(spacing * 100)))


def _textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    return tf


def _write_tf(tf, paras, scale=1.0, font="맑은 고딕", text_color="1E293B"):
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        para.space_before = Pt(p.get("before", 0))
        para.space_after = Pt(0)
        if p.get("line"):
            para.line_spacing = p["line"]
        para._pPr.set("eaLnBrk", "0")
        para._pPr.set("hangingPunct", "1")
        run = para.add_run()
        run.text = str(p["text"])
        _style_run(run, p["size"] * scale, p.get("bold", False),
                   p.get("color", text_color), p.get("italic", False),
                   p.get("spacing"), font=font)


def _flow_box(slide, x, y, w, avail_h, paras, min_scale=0.78, where="",
              font="맑은 고딕", text_color="1E293B", warnings=None):
    paras = [p for p in paras if str(p.get("text", "")) != ""]
    if not paras:
        return 0.0
    scale = 1.0
    while scale > min_scale and _block_height(paras, w, scale) > avail_h:
        scale -= 0.04
    used = _block_height(paras, w, scale)
    if used > avail_h * 1.02 and warnings is not None:
        warnings.append(
            "넘침: %s (필요 %.2f\" > 자리 %.2f\") — 글을 줄이거나 항목 수를 낮출 것"
            % (where or "블록", used, avail_h))
    tf = _textbox(slide, x, y, w, max(avail_h, used))
    _write_tf(tf, paras, scale, font=font, text_color=text_color)
    return used


def _create_shape(slide, kind, x, y, w, h, fill=None, line=None,
                  line_w=0.75, shadow=False, radius=None):
    s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = RGBColor.from_string(line)
        s.line.width = Pt(line_w)
    else:
        s.line.fill.background()
    if radius is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if shadow:
        spPr = s._element.spPr
        effect = spPr.find(qn("a:effectLst"))
        if effect is None:
            effect = spPr.makeelement(qn("a:effectLst"), {})
            spPr.append(effect)
        effect.append(parse_xml(SHADOW_XML))
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return s


def _status_color(key, theme=None):
    t = theme or Theme()
    mapping = {
        "ok": t.ok, "green": t.ok,
        "warn": t.warn, "yellow": t.warn,
        "bad": t.bad, "red": t.bad,
        "primary": t.primary,
        "secondary": t.secondary,
        "accent": t.accent,
        "accent_on_dark": t.accent_on_dark,
        "muted": t.muted,
        "dim": t.dim,
        "tint": t.tint,
        "dark": t.dark,
        "dark_panel": t.dark_panel,
    }
    return mapping.get(str(key).lower(), key or t.muted)


def _split_ratios(total, weights, gap):
    weights = [float(w) if w else 1.0 for w in weights]
    room = total - gap * (len(weights) - 1)
    unit = room / sum(weights) if sum(weights) > 0 else room / len(weights)
    out, pos = [], 0.0
    for w in weights:
        size = unit * w
        out.append((pos, size))
        pos += size + gap
    return out


def _input_box(slide, x, y, w, h, spec, theme=None):
    t = theme or Theme()
    caption = spec.get("caption")
    if caption:
        tf = _textbox(slide, x, y, w, 0.24)
        _write_tf(tf, [{"text": caption, "size": 8.5, "bold": True,
                        "color": t.primary, "align": PP_ALIGN.CENTER}], font=t.font)
        y += 0.26
        h -= 0.26
    box = _create_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, max(0.22, h),
                        fill=t.light_bg, line=t.border, radius=0.06)
    tf = box.text_frame
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = tf.margin_bottom = Inches(0.06)
    placeholder = spec.get("placeholder", "")
    size = spec.get("size", 9.5)
    while size > 7.5 and _block_height([{"text": placeholder, "size": size,
                                         "line": 1.3}], w - 0.2) > h - 0.12:
        size -= 0.5
    _write_tf(tf, [{"text": placeholder, "size": size, "color": t.dim, "line": 1.3}], font=t.font)
    return box


# ==============================================================================
# 1. 지면 구획 / 컨테이너 프리미티브 (Containers)
# ==============================================================================

class Rect:
    """기하 사각형 (x, y, w, h). 언패킹과 슬라이스 인덱싱을 지원한다."""

    def __init__(self, x: float, y: float, w: float, h: float,
                 slide: Any = None, theme: Theme | None = None, deck: Any = None):
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)
        self.slide = slide
        self.theme = theme
        self.deck = deck

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def center_x(self) -> float:
        return self.x + self.w / 2.0

    @property
    def center_y(self) -> float:
        return self.y + self.h / 2.0

    def pad(self, pad_x: float, pad_y: float | None = None) -> Rect:
        py = pad_x if pad_y is None else pad_y
        return Rect(self.x + pad_x, self.y + py,
                    max(0.0, self.w - 2 * pad_x),
                    max(0.0, self.h - 2 * py),
                    slide=self.slide, theme=self.theme, deck=self.deck)

    def with_slide(self, slide: Any) -> Rect:
        return Rect(self.x, self.y, self.w, self.h,
                    slide=slide, theme=self.theme, deck=self.deck)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.w
        yield self.h

    def __getitem__(self, idx: int) -> float:
        return (self.x, self.y, self.w, self.h)[idx]

    def __repr__(self) -> str:
        return f"Rect(x={self.x:.2f}, y={self.y:.2f}, w={self.w:.2f}, h={self.h:.2f})"


class Cell(Rect):
    """Grid 또는 Split 에서 분할된 개별 셀."""

    def __init__(self, x: float, y: float, w: float, h: float,
                 row: int = 0, col: int = 0, index: int = 0,
                 slide: Any = None, theme: Theme | None = None, deck: Any = None):
        super().__init__(x, y, w, h, slide=slide, theme=theme, deck=deck)
        self.row = row
        self.col = col
        self.index = index

    def card(self, bg_color: str | None = None, border_color: str | None = None,
             shadow: bool = True, radius: float = 0.035, dark: bool = False,
             slide: Any = None) -> Card:
        s = slide or self.slide
        return Card(self.x, self.y, self.w, self.h, bg_color=bg_color,
                    border_color=border_color, shadow=shadow, radius=radius,
                    dark=dark, slide=s, theme=self.theme, deck=self.deck)


class Grid:
    """지면 격자 구획기 (행 × 열 자동 배치 및 내부 셀 좌표 계산)."""

    def __init__(self, x: float, y: float, w: float, h: float,
                 rows: int = 1, cols: int = 1,
                 gap_x: float = GAP, gap_y: float = GAP,
                 slide: Any = None, theme: Theme | None = None, deck: Any = None):
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)
        self.rows = max(1, int(rows))
        self.cols = max(1, int(cols))
        self.gap_x = float(gap_x)
        self.gap_y = float(gap_y)
        self.slide = slide
        self.theme = theme
        self.deck = deck
        self.cells = self._compute_cells()

    def _compute_cells(self) -> list[Cell]:
        cw = (self.w - self.gap_x * (self.cols - 1)) / self.cols
        ch = (self.h - self.gap_y * (self.rows - 1)) / self.rows
        cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                cx = self.x + c * (cw + self.gap_x)
                cy = self.y + r * (ch + self.gap_y)
                idx = r * self.cols + c
                cells.append(Cell(cx, cy, cw, ch, row=r, col=c, index=idx,
                                  slide=self.slide, theme=self.theme, deck=self.deck))
        return cells

    def __getitem__(self, key: int | tuple[int, int]) -> Cell:
        if isinstance(key, tuple):
            r, c = key
            return self.cells[r * self.cols + c]
        return self.cells[key]

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def __repr__(self) -> str:
        return f"Grid({self.rows}x{self.cols}, x={self.x:.2f}, y={self.y:.2f}, w={self.w:.2f}, h={self.h:.2f})"


class Split:
    """비율 분할기 (가로 'h' 또는 세로 'v' 2분할/3분할 구획기)."""

    def __init__(self, x: float, y: float, w: float, h: float,
                 direction: str = 'h',
                 ratios: list[float] | None = None,
                 gap: float = GAP,
                 slide: Any = None, theme: Theme | None = None, deck: Any = None):
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)
        self.direction = str(direction).lower()
        self.ratios = [float(r) for r in (ratios or [0.5, 0.5])]
        self.gap = float(gap)
        self.slide = slide
        self.theme = theme
        self.deck = deck
        self.cells = self._compute_cells()

    def _compute_cells(self) -> list[Cell]:
        weights = [max(0.0001, float(w)) for w in self.ratios]
        total_span = self.w if self.direction == 'h' else self.h
        room = total_span - self.gap * (len(weights) - 1)
        unit = room / sum(weights) if sum(weights) > 0 else room / len(weights)

        cells = []
        pos = 0.0
        for i, w in enumerate(weights):
            size = unit * w
            if self.direction == 'h':
                cell = Cell(self.x + pos, self.y, size, self.h, row=0, col=i, index=i,
                            slide=self.slide, theme=self.theme, deck=self.deck)
            else:
                cell = Cell(self.x, self.y + pos, self.w, size, row=i, col=0, index=i,
                            slide=self.slide, theme=self.theme, deck=self.deck)
            cells.append(cell)
            pos += size + self.gap
        return cells

    def __getitem__(self, idx: int) -> Cell:
        return self.cells[idx]

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self):
        return iter(self.cells)

    def __repr__(self) -> str:
        return f"Split({self.direction}, ratios={self.ratios}, x={self.x:.2f}, y={self.y:.2f})"


class Card(Rect):
    """카드 컨테이너 — 둥근 모서리 + 은은한 테두리 + 그림자."""

    def __init__(self, *args, **kwargs):
        slide = kwargs.get("slide")
        theme = kwargs.get("theme")
        deck = kwargs.get("deck")
        bg_color = kwargs.get("bg_color")
        border_color = kwargs.get("border_color")
        shadow = kwargs.get("shadow")
        radius = kwargs.get("radius", 0.035)
        dark = kwargs.get("dark", False)
        line_w = kwargs.get("line_w", 0.75)

        if len(args) > 0:
            if hasattr(args[0], "shapes"):  # Card(slide, x, y, w, h, ...)
                slide = args[0]
                x, y, w, h = args[1:5]
                if len(args) > 5:
                    bg_color = args[5]
                if len(args) > 6:
                    border_color = args[6]
                if len(args) > 7:
                    shadow = args[7]
            elif isinstance(args[0], Rect):  # Card(cell, ...)
                cell = args[0]
                x, y, w, h = cell.x, cell.y, cell.w, cell.h
                slide = slide or cell.slide
                theme = theme or cell.theme
                deck = deck or cell.deck
                if len(args) > 1:
                    bg_color = args[1]
                if len(args) > 2:
                    border_color = args[2]
                if len(args) > 3:
                    shadow = args[3]
            else:  # Card(x, y, w, h, ...)
                x, y, w, h = args[0:4]
                if len(args) > 4:
                    bg_color = args[4]
                if len(args) > 5:
                    border_color = args[5]
                if len(args) > 6:
                    shadow = args[6]
        else:
            x = kwargs.get("x", MARGIN)
            y = kwargs.get("y", MARGIN)
            w = kwargs.get("w", 5.0)
            h = kwargs.get("h", 3.0)

        t = theme or (deck.theme if deck else Theme())
        if dark:
            bg_color = bg_color or t.dark_panel
            border_color = border_color or t.dark_line
            if shadow is None:
                shadow = False
        else:
            bg_color = bg_color or t.card
            border_color = border_color or t.border
            if shadow is None:
                shadow = True

        super().__init__(x, y, w, h, slide=slide, theme=t, deck=deck)
        self.bg_color = bg_color
        self.border_color = border_color
        self.shadow = shadow
        self.radius = radius
        self.dark = dark
        self.shape = None

        if self.slide is not None:
            self.shape = _create_shape(self.slide, MSO_SHAPE.ROUNDED_RECTANGLE,
                                       self.x, self.y, self.w, self.h,
                                       fill=self.bg_color, line=self.border_color,
                                       line_w=line_w, shadow=self.shadow,
                                       radius=self.radius)

    def render(self, slide: Any) -> Any:
        self.slide = slide
        self.shape = _create_shape(self.slide, MSO_SHAPE.ROUNDED_RECTANGLE,
                                   self.x, self.y, self.w, self.h,
                                   fill=self.bg_color, line=self.border_color,
                                   line_w=0.75, shadow=self.shadow,
                                   radius=self.radius)
        return self.shape


def _resolve_target(parent: Any, slide: Any = None, theme: Theme | None = None, deck: Any = None):
    px, py, pw, ph = 0.0, 0.0, 0.0, 0.0
    pslide, ptheme, pdeck = slide, theme, deck

    if isinstance(parent, Rect):
        px, py, pw, ph = parent.x, parent.y, parent.w, parent.h
        pslide = pslide or parent.slide
        ptheme = ptheme or parent.theme
        pdeck = pdeck or parent.deck
    elif isinstance(parent, (list, tuple)):
        if len(parent) == 5:
            pslide, px, py, pw, ph = parent
        elif len(parent) == 4:
            px, py, pw, ph = parent
        elif len(parent) == 2:
            pslide, rect = parent
            px, py, pw, ph = rect.x, rect.y, rect.w, rect.h
    elif hasattr(parent, "shapes"):  # Slide
        pslide = parent
        px, py = MARGIN, MARGIN
        pw = (pdeck.cw if pdeck else 10.0)
        ph = (pdeck.H - 2 * MARGIN if pdeck else 6.0)

    if ptheme is None:
        ptheme = pdeck.theme if pdeck else Theme()

    return pslide, float(px), float(py), float(pw), float(ph), ptheme, pdeck


# ==============================================================================
# 2. 시각 원자 부품 (Content Atoms)
# ==============================================================================

class HeaderResult(float):
    """헤더가 차지한 바닥 Y 좌표 (float로 바로 산술 연산 가능)."""

    def __new__(cls, val, y=None, bottom=None):
        obj = super().__new__(cls, val)
        obj.y = y if y is not None else val
        obj.bottom = bottom if bottom is not None else val
        return obj


def KickerHeader(slide: Any, kicker: str | None = None, title: Any = "",
                 subtitle: str | None = None, lead: str | None = None,
                 note: Any = None, dark: bool = False,
                 theme: Theme | None = None, title_w: float | None = None,
                 pad: float | None = None, deck: Any = None,
                 title_size: float | None = None, title_y: float | None = None) -> HeaderResult:
    """타이포 계층 헤더 (카테고리 kicker + 메인 title + subtitle/lead + 우상단 note)."""
    t = theme or (deck.theme if deck else Theme())
    w_val = deck.W if deck else (slide.prs.slide_width.inches if hasattr(slide, "prs") else 11.693)
    cw = deck.cw if deck else (w_val - 2 * MARGIN)
    accent = t.accent_on_dark if dark else t.accent
    head = t.on_dark if dark else t.primary
    sub = t.on_dark_muted if dark else t.muted
    pad_x = pad if pad is not None else MARGIN

    note_w = cw * 0.40 if note else 0.0
    head_w = cw - note_w - (0.3 if note else 0)
    eff_title_w = title_w or min(head_w, cw * 0.80)

    # 1. 우상단 안내 배지 (note)
    if note:
        lines = note if isinstance(note, (list, tuple)) else [note]
        nh = 0.22 * len(lines) + 0.20
        _create_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, w_val - MARGIN - note_w, 0.46,
                      note_w, nh, fill=t.dark_panel if dark else t.tint, radius=0.18)
        _flow_box(slide, w_val - MARGIN - note_w + 0.16, 0.46 + 0.10,
                  note_w - 0.32, nh - 0.16,
                  [{"text": ln, "size": 9, "bold": i == 0,
                    "color": t.on_dark_muted if dark else t.muted,
                    "align": PP_ALIGN.CENTER, "before": 2 if i else 0}
                   for i, ln in enumerate(lines)], where="안내 배지",
                  font=t.font, text_color=t.muted, warnings=deck.warnings if deck else None)

    # 2. 카테고리 태그 (kicker)
    if kicker:
        ky = 0.46 if pad is None else (0.62 if subtitle is None and dark else 0.72)
        k_size = 11.5 if (pad is not None and subtitle is not None) else 11
        tf = _textbox(slide, pad_x, ky, head_w, 0.28)
        _write_tf(tf, [{"text": kicker, "size": k_size, "bold": True,
                        "color": accent, "spacing": 1.2}], font=t.font)

    # 3. 메인 타이틀 (title) & 서브타이틀
    lines = title if isinstance(title, (list, tuple)) else [title]
    if pad is not None and dark and subtitle is not None:
        # 다크 표지 스타일
        size = title_size or (33 if len(lines) <= 2 else 27)
        paras = [{"text": ln, "size": size, "bold": True, "color": t.on_dark, "line": 1.18}
                 for ln in lines]
        paras.append({"text": subtitle, "size": 15.5, "color": t.accent_on_dark, "before": 10})
        y = 1.18
        used = _flow_box(slide, pad_x, y, eff_title_w, 2.4, paras, where="표지 제목",
                         font=t.font, text_color=t.on_dark, warnings=deck.warnings if deck else None)
        bottom = y + max(used, 1.0) + 0.24
        if lead:
            used = _flow_box(slide, pad_x, bottom, eff_title_w - 0.3, 1.4,
                             [{"text": lead, "size": 12.5, "color": t.on_dark_muted, "line": 1.42}],
                             where="표지 리드", font=t.font, text_color=t.on_dark_muted,
                             warnings=deck.warnings if deck else None)
            bottom += used + 0.3
        return HeaderResult(bottom)
    elif pad is not None and dark and subtitle is None:
        # 다크 마무리 스타일
        ty = title_y or 0.95
        size = title_size or 30
        title_box_w = min(eff_title_w, cw * 0.82)
        paras = [{"text": ln, "size": size, "bold": True, "color": t.on_dark, "line": 1.05}
                 for ln in lines]
        used = _flow_box(slide, pad_x, ty, title_box_w, 1.2, paras, where="마무리 제목",
                         font=t.font, text_color=t.on_dark, warnings=deck.warnings if deck else None)
        bottom = ty + max(used, 0.55)
        if lead:
            _flow_box(slide, pad_x, bottom + 0.1, cw * 0.86, 0.6,
                      [{"text": lead, "size": 12, "color": t.on_dark_muted, "line": 1.3}],
                      where="마무리 리드", font=t.font, text_color=t.on_dark_muted,
                      warnings=deck.warnings if deck else None)
            bottom += 0.7
        return HeaderResult(bottom)
    else:
        # 일반 헤딩
        ty = title_y or 0.76
        if title_size is not None:
            size = title_size
        else:
            size = 28 if len(lines) == 1 else 24
            while size > 21 and sum(_line_count(ln, eff_title_w, size) for ln in lines) > len(lines):
                size -= 1
        wrapped = sum(_line_count(ln, eff_title_w, size) for ln in lines)
        tf = _textbox(slide, pad_x, ty, eff_title_w, 0.52 * wrapped)
        _write_tf(tf, [{"text": ln, "size": size, "bold": True, "color": head, "line": 1.08}
                       for ln in lines], font=t.font)
        bottom = ty + 0.52 * wrapped
        if lead:
            lead_lines = _line_count(lead, cw, 12)
            lead_h = 0.24 * lead_lines + 0.06
            tf = _textbox(slide, pad_x, bottom + 0.08, cw, lead_h)
            _write_tf(tf, [{"text": lead, "size": 12, "color": sub, "line": 1.25}], font=t.font)
            return HeaderResult(bottom + 0.08 + 0.24 * lead_lines + 0.06)
        return HeaderResult(bottom + 0.28)


def MetricBox(parent: Any, value: Any, label: str = "", desc: str | None = None,
              color: str | None = None, layout: str = "auto",
              value_size: float | None = None, label_size: float | None = None,
              desc_size: float | None = None, dark: bool = False,
              theme: Theme | None = None, slide: Any = None,
              deck: Any = None, bg_color: str | None = None) -> Rect:
    """대형 숫자 + 캡션 지표 (가로 배치 side_by_side 또는 상하 적층 stacked)."""
    s, x, y, w, h, t, d = _resolve_target(parent, slide=slide, theme=theme, deck=deck)
    num_str = str(value if value is not None else "")
    v_color = color or (t.accent_on_dark if dark else t.accent)
    warnings = d.warnings if d else None

    if bg_color:
        _create_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=bg_color, radius=0.06)

    if layout == "auto":
        layout = "side_by_side" if (w >= 2.4 and (w / max(0.1, h)) >= 1.6) else "stacked"

    if layout == "side_by_side":
        cal_wide = w >= 2.9
        if bg_color:
            paras = [{"text": str(label), "size": label_size or 10.5, "bold": True,
                      "color": t.primary, "line": 1.1}]
            if desc:
                paras.append({"text": str(desc), "size": desc_size or 9.0, "color": t.muted,
                              "before": 2, "line": 1.15})
            if cal_wide:
                tf = _textbox(s, x + 0.24, y + 0.14, 1.15, 0.55)
                _write_tf(tf, [{"text": num_str, "size": value_size or 30,
                                "bold": True, "color": v_color, "line": 0.95}], font=t.font)
                _flow_box(s, x + 1.42, y + 0.2, w - 1.5, 0.6,
                          paras, where="좌측 콜아웃", font=t.font, warnings=warnings)
            else:
                tf = _textbox(s, x + 0.2, y + 0.12, w - 0.4, 0.5)
                _write_tf(tf, [{"text": num_str, "size": value_size or 28,
                                "bold": True, "color": v_color, "line": 0.95}], font=t.font)
                _flow_box(s, x + 0.2, y + 0.58, w - 0.4, h - 0.7,
                          paras, where="좌측 콜아웃", font=t.font, warnings=warnings)
        else:
            # Dark cover stat style
            v_sz = value_size or (40 if len(num_str) <= 2 else (30 if len(num_str) == 3 else 24))
            _flow_box(s, x + 0.35, y + 0.3, 1.02, 0.62,
                      [{"text": num_str, "size": v_sz, "bold": True,
                        "color": v_color, "line": 0.9}], where="지표 값",
                      font=t.font, warnings=warnings)
            paras = [{"text": str(label), "size": label_size or 12.5, "bold": True,
                      "color": t.on_dark if dark else t.primary, "line": 1.1}]
            if desc:
                paras.append({"text": str(desc), "size": desc_size or 9.5,
                              "color": t.on_dark_muted if dark else t.muted,
                              "before": 4, "line": 1.25})
            _flow_box(s, x + 1.45, y + 0.34, w - 1.7, h - 0.5, paras,
                      where="지표 라벨/설명", font=t.font, warnings=warnings)
    else:
        # Stacked layout (e.g. executive dashboard)
        v_sz = value_size or (36 if len(num_str) <= 3 else 28)
        tf = _textbox(s, x, y, w - 0.04, 0.62)
        _write_tf(tf, [{"text": num_str, "size": v_sz, "bold": True,
                        "color": v_color, "line": 0.92}], font=t.font)
        val_h = v_sz / 72.0 * 1.14
        paras = [{"text": str(label), "size": label_size or 9.5,
                  "color": t.on_dark_muted if dark else t.muted, "line": 1.15}]
        if desc:
            paras.append({"text": str(desc), "size": desc_size or 8.5,
                          "color": t.on_dark_muted if dark else t.muted,
                          "before": 2, "line": 1.15})
        _flow_box(s, x, y + val_h, w - 0.1, max(0.4, h - val_h), paras,
                  where="지표 라벨", font=t.font, warnings=warnings)

    return Rect(x, y, w, h, slide=s, theme=t, deck=d)


def Badge(parent: Any, text: str = "", color: str | None = None,
          icon: str | None = None, size: float = 11,
          text_color: str | None = None, dark: bool = False,
          theme: Theme | None = None, x: float | None = None,
          y: float | None = None, d: float | None = None,
          slide: Any = None, deck: Any = None) -> Any:
    """상태/신호등/순번 원형 배지."""
    s, px, py, pw, ph, t, dk = _resolve_target(parent, slide=slide, theme=theme, deck=deck)
    bx = x if x is not None else px
    by = y if y is not None else py
    bd = d if d is not None else (min(pw, ph, 0.34) if (pw > 0 and ph > 0) else 0.34)

    fill = _status_color(color, t) if color else (t.accent_on_dark if dark else t.primary)
    t_color = text_color or (t.dark if (dark and fill == t.accent_on_dark) else t.on_dark)
    badge_text = str(text if text != "" else (icon or ""))

    shape = _create_shape(s, MSO_SHAPE.OVAL, bx, by, bd, bd, fill=fill)
    tf = shape.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    _write_tf(tf, [{"text": badge_text, "size": size, "bold": True,
                    "color": t_color, "align": PP_ALIGN.CENTER}], font=t.font)
    return shape


def StepCard(parent: Any, step_no: Any = None, title: str = "",
             items: list[str] | None = None, status_tag: str | None = None,
             period: str | None = None, output: str | None = None,
             criteria: str | None = None,
             activities_label: str = "핵심 활동", output_label: str = "산출물",
             criteria_label: str = "통과 기준", accent: str | None = None,
             dark: bool = False, theme: Theme | None = None,
             slide: Any = None, deck: Any = None) -> Rect:
    """단계별 프로세스 카드 (순번 배지 + 타이틀 + 활동 불릿 + 산출물/통과기준 박스)."""
    s, x, y, w, h, t, d = _resolve_target(parent, slide=slide, theme=theme, deck=deck)
    warnings = d.warnings if d else None
    act_col = accent or (t.accent_on_dark if dark else t.primary)

    # 1. Badge / Tag
    tag = status_tag if status_tag is not None else (str(step_no) if step_no is not None else "")
    tight = h < 3.0
    curr_y = y + 0.28
    if tag:
        Badge(s, text=tag, color=act_col, size=13,
              x=x + 0.3, y=curr_y, d=0.5, dark=dark, theme=t, deck=d)
        curr_y += 0.58 if tight else 0.65

    # 2. Title & Period
    paras = [{"text": title, "size": 14, "bold": True,
              "color": t.on_dark if dark else t.primary, "line": 1.05}]
    if period:
        paras.append({"text": period, "size": 9.5, "bold": True,
                      "color": act_col, "before": 3})
    curr_y += max(_flow_box(s, x + 0.3, curr_y, w - 0.6, 0.72, paras,
                            where="단계 머리글", font=t.font, warnings=warnings), 0.4) + 0.12

    # 3. Activities / items
    has_box = bool(output or criteria)
    box_h = (min(0.92, max(0.62, h * (0.22 if tight else 0.26))) if has_box else 0.0)
    acts = list(items or [])
    if acts:
        paras = [{"text": "· " + a, "size": 10, "color": t.on_dark if dark else t.text,
                  "before": 3, "line": 1.2} for a in acts]
        room = y + h - PAD - box_h - curr_y - (0.12 if box_h else 0)
        if room >= _block_height(paras, w - 0.6) + 0.22:
            paras.insert(0, {"text": activities_label, "size": 9, "bold": True,
                             "color": t.dim, "spacing": 0.6})
        _flow_box(s, x + 0.3, curr_y, w - 0.6, room, paras, where="단계 활동",
                  font=t.font, warnings=warnings)

    # 4. Output / criteria box
    if box_h:
        by = y + h - PAD + 0.1 - box_h
        _create_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x + 0.3, by, w - 0.6, box_h,
                      fill=t.dark_panel if dark else t.tint, radius=0.08)
        paras = []
        if output:
            paras.append({"text": output_label, "size": 8.5, "bold": True,
                          "color": t.dim, "spacing": 0.6})
            paras.append({"text": output, "size": 9.5, "bold": True,
                          "color": t.on_dark if dark else t.text, "before": 1, "line": 1.15})
        if criteria:
            paras.append({"text": criteria_label + "  " + criteria, "size": 8.5,
                          "color": t.on_dark_muted if dark else t.muted, "before": 3, "line": 1.15})
        _flow_box(s, x + 0.46, by + 0.1, w - 0.92, box_h - 0.18, paras,
                  where="단계 산출물", font=t.font, warnings=warnings)

    return Rect(x, y, w, h, slide=s, theme=t, deck=d)


def TableBox(parent: Any, headers: list[Any] | None = None,
             rows: list[Any] | None = None,
             col_widths: list[float] | None = None,
             status_label: str = "상태", title: str | None = None,
             dark: bool = False, theme: Theme | None = None,
             slide: Any = None, deck: Any = None) -> Rect:
    """행 묶음 표 (헤더 + 줄무늬 데이터 행 + 상태 배지)."""
    s, x, y, w, h, t, d = _resolve_target(parent, slide=slide, theme=theme, deck=deck)
    columns = list(headers or [])
    data_rows = list(rows or [])
    has_status = any(isinstance(r, dict) and r.get("status") for r in data_rows)

    if title:
        tf = _textbox(s, x + PAD, y + 0.25, w - 2 * PAD, 0.28)
        _write_tf(tf, [{"text": title, "size": 13, "bold": True,
                        "color": t.on_dark if dark else t.primary}], font=t.font)

    table_w = w - 2 * PAD
    status_w = 1.0 if has_status else 0.0
    avail_w = table_w - status_w

    if col_widths and len(col_widths) == len(columns):
        total_w = sum(col_widths)
        computed_widths = [avail_w * (cw / total_w) for cw in col_widths]
    else:
        col_w = avail_w / max(1, len(columns))
        computed_widths = [col_w] * len(columns)

    head_y = y + (0.65 if title else 0.3)
    curr_col_x = x + PAD
    for i, (col, cw_val) in enumerate(zip(columns, computed_widths)):
        label = col if isinstance(col, str) else col.get("label", "")
        align = PP_ALIGN.LEFT if i == 0 else PP_ALIGN.CENTER
        tf = _textbox(s, curr_col_x, head_y, cw_val, 0.24)
        _write_tf(tf, [{"text": label, "size": 9, "bold": True, "color": t.dim,
                        "align": align, "spacing": 0.6}], font=t.font)
        curr_col_x += cw_val

    if has_status:
        tf = _textbox(s, curr_col_x, head_y, status_w, 0.24)
        _write_tf(tf, [{"text": status_label, "size": 9, "bold": True, "color": t.dim,
                        "align": PP_ALIGN.CENTER, "spacing": 0.6}], font=t.font)

    row_h = min(0.38, (y + h - 0.28 - (head_y + 0.3)) / max(1, len(data_rows)))
    for ri, row_data in enumerate(data_rows):
        row_y = head_y + 0.3 + ri * row_h
        if ri % 2 == 0:
            _create_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x + PAD - 0.1, row_y - 0.04,
                          table_w + 0.2, row_h - 0.02,
                          fill=t.dark_panel if dark else t.tint, radius=0.12)

        if isinstance(row_data, dict):
            cells = row_data.get("cells") or []
            status = row_data.get("status")
            status_txt = row_data.get("status_label") or (str(status).title() if status else "")
        else:
            cells = list(row_data)
            status = None
            status_txt = ""

        cell_x = x + PAD
        for ci, (cell_val, cw_val) in enumerate(zip(cells, computed_widths)):
            align = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER
            color = t.text if ci == 0 else (t.primary if ci == len(cells) - 1 else t.muted)
            size = 10.0
            while size > 8.0 and _line_count(cell_val, cw_val - 0.08, size) > 1:
                size -= 0.5
            tf = _textbox(s, cell_x, row_y + 0.04, cw_val, 0.26)
            _write_tf(tf, [{"text": str(cell_val), "size": size, "bold": ci == 0,
                            "color": color, "align": align}], font=t.font)
            cell_x += cw_val

        if status:
            color = _status_color(status, t)
            status_col_x = x + PAD + sum(computed_widths)
            Badge(s, text="", color=color, x=status_col_x + 0.08, y=row_y + 0.06, d=0.22,
                  slide=s, theme=t, deck=d)
            tf = _textbox(s, status_col_x + 0.34, row_y + 0.04, status_w - 0.34, 0.26)
            _write_tf(tf, [{"text": status_txt, "size": 9.5, "bold": True, "color": color}],
                      font=t.font)

    return Rect(x, y, w, h, slide=s, theme=t, deck=d)


def CalloutBanner(slide: Any, text: str = "", rule_type: str | None = None,
                  label: str | None = None, x: float | None = None,
                  y: float | None = None, w: float | None = None,
                  h: float = 0.56, dark: bool = False,
                  theme: Theme | None = None, deck: Any = None) -> Any:
    """하단 안내/판정 규칙 배너."""
    t = theme or (deck.theme if deck else Theme())
    w_val = deck.W if deck else (slide.prs.slide_width.inches if hasattr(slide, "prs") else 11.693)
    h_val = deck.H if deck else (slide.prs.slide_height.inches if hasattr(slide, "prs") else 8.268)
    bx = MARGIN if x is None else x
    by = (h_val - MARGIN - h) if y is None else y
    bw = (deck.cw if deck else (w_val - 2 * MARGIN)) if w is None else w

    shape = _create_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, bx, by, bw, h,
                          fill=t.dark_panel if dark else t.tint, radius=0.14)
    tag_label = label or rule_type
    tx = bx + 0.3
    if tag_label:
        tf = _textbox(slide, tx, by + 0.18, 2.2, 0.26)
        _write_tf(tf, [{"text": tag_label, "size": 10, "bold": True,
                        "color": t.accent_on_dark if dark else t.accent,
                        "spacing": 0.6}], font=t.font)
        tx += 2.3

    _flow_box(slide, tx, by + 0.17, bx + bw - 0.3 - tx, h - 0.24,
              [{"text": text, "size": 11, "bold": True,
                "color": t.on_dark if dark else t.primary, "line": 1.2}],
              where="하단 배너", font=t.font, warnings=deck.warnings if deck else None)
    return shape


def FormField(parent: Any, label: str = "", placeholder: str = "",
              flex: float = 1.0, inputs: list[dict] | None = None,
              hint: str | None = None, num: Any = None,
              layout: str = "row", dark: bool = False,
              theme: Theme | None = None, slide: Any = None,
              deck: Any = None) -> Rect:
    """작성용 양식 입력 필드 (순번 배지 + 라벨 + 힌트 + 1개 이상의 입력 박스)."""
    s, x, y, w, h, t, d = _resolve_target(parent, slide=slide, theme=theme, deck=deck)

    # Card background if not already present
    card_shape = getattr(parent, "shape", None)
    if card_shape is None:
        _create_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h,
                      fill=t.dark_panel if dark else t.card,
                      line=t.dark_line if dark else t.border,
                      shadow=not dark, radius=0.035)

    # Number badge
    if num is not None:
        badge_str = str(num)
        Badge(s, text=badge_str, color=t.secondary, size=8.5,
              x=x + 0.22, y=y + 0.17, d=0.3, slide=s, theme=t, deck=d)

    # Label + Hint
    label_x = x + 0.60 if num is not None else x + PAD
    label_w = w - 0.82 - (3.05 if hint else 0)
    tf = _textbox(s, label_x, y + 0.16, max(1.0, label_w), 0.3)
    _write_tf(tf, [{"text": label, "size": 11, "bold": True,
                    "color": t.on_dark if dark else t.primary}], font=t.font)
    if hint:
        tf = _textbox(s, x + w - 3.0, y + 0.19, 2.78, 0.26)
        _write_tf(tf, [{"text": hint, "size": 8.5,
                        "color": t.on_dark_muted if dark else t.muted,
                        "align": PP_ALIGN.RIGHT}], font=t.font)

    # Inputs inside field
    ix, iy = x + 0.22, y + 0.52
    iw, ih = w - 0.44, h - 0.52 - 0.16
    input_specs = inputs or ([{"placeholder": placeholder, "flex": flex}] if placeholder else [{}])
    input_gap = 0.12

    if layout == "row" and len(input_specs) > 1:
        spans = _split_ratios(iw, [b.get("flex", 1) for b in input_specs], input_gap)
        for (bx, bw), box in zip(spans, input_specs):
            _input_box(s, ix + bx, iy, bw, ih, box, theme=t)
    else:
        spans = _split_ratios(ih, [1] * len(input_specs), 0.08)
        for (by, bh), box in zip(spans, input_specs):
            _input_box(s, ix, iy + by, iw, bh, box, theme=t)

    return Rect(x, y, w, h, slide=s, theme=t, deck=d)


# ==============================================================================
# 3. Deck 클래스 및 상위 레시피 (Convenience Helpers)
# ==============================================================================

class Deck:
    """슬라이드를 쌓는 판. 원자 부품(Primitives)과 상위 레시피(Recipes)를 모두 제공한다."""

    def __init__(self, theme=None, font=None, page=DEFAULT_PAGE):
        self.theme = theme if isinstance(theme, Theme) else Theme.from_dict(theme or {})
        if font:
            self.theme.font = font
        if isinstance(page, str):
            if page not in PAGE_SIZES:
                raise ValueError("모르는 지면: %r (가능: %s)"
                                 % (page, ", ".join(PAGE_SIZES)))
            self.W, self.H = PAGE_SIZES[page]
        else:
            self.W, self.H = float(page[0]), float(page[1])
        self.cw = self.W - 2 * MARGIN
        self.prs = Presentation()
        self.prs.slide_width = Inches(self.W)
        self.prs.slide_height = Inches(self.H)
        self.warnings = []
        self.current_slide = None

    # ------------------------------------------------------------ 슬라이드 및 프리미티브 헬퍼
    def _slide(self, bg):
        s = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = RGBColor.from_string(bg)
        self.current_slide = s
        return s

    def add_slide(self, bg=None):
        """새 슬라이드를 추가하고 현재 슬라이드로 지정한다."""
        return self._slide(bg or self.theme.light_bg)

    def _style(self, run, size, bold, color, italic=False, spacing=None):
        _style_run(run, size, bold, color, italic=italic, spacing=spacing, font=self.theme.font)

    def _textbox(self, slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
        return _textbox(slide, x, y, w, h, anchor=anchor)

    def _write(self, tf, paras, scale=1.0):
        _write_tf(tf, paras, scale=scale, font=self.theme.font, text_color=self.theme.text)

    def _flow(self, slide, x, y, w, avail_h, paras, min_scale=0.78, where=""):
        return _flow_box(slide, x, y, w, avail_h, paras, min_scale=min_scale, where=where,
                         font=self.theme.font, text_color=self.theme.text, warnings=self.warnings)

    def _shape(self, slide, kind, x, y, w, h, fill=None, line=None,
               line_w=0.75, shadow=False, radius=None):
        return _create_shape(slide, kind, x, y, w, h, fill=fill, line=line,
                             line_w=line_w, shadow=shadow, radius=radius)

    def _card(self, slide, x, y, w, h, dark=False):
        return Card(slide, x, y, w, h, dark=dark, theme=self.theme, deck=self).shape

    def _badge(self, slide, x, y, d, text, fill, color=None, size=11):
        return Badge(slide, text=text, color=fill, size=size, text_color=color,
                     x=x, y=y, d=d, theme=self.theme, deck=self)

    def _motif(self, slide):
        """다크 슬라이드에 반복되는 모티프 — 가장자리로 흘러나가는 얇은 원."""
        c = self.theme.dark_line
        self._shape(slide, MSO_SHAPE.OVAL, self.W - 3.03, -1.5, 4.6, 4.6,
                    fill=None, line=c, line_w=1.0)
        self._shape(slide, MSO_SHAPE.OVAL, self.W - 1.73, self.H - 2.9, 3.4, 3.4,
                    fill=None, line=c, line_w=1.0)

    def _heading(self, slide, kicker, title, lead=None, dark=False, title_w=None, note=None):
        return KickerHeader(slide, kicker=kicker, title=title, lead=lead, note=note,
                            dark=dark, theme=self.theme, title_w=title_w, deck=self)

    def _columns(self, n, x0=MARGIN, total=None, gap=GAP):
        n = max(1, n)
        total = self.cw if total is None else total
        w = (total - gap * (n - 1)) / n
        return [(x0 + i * (w + gap), w) for i in range(n)]

    @staticmethod
    def _split(total, weights, gap):
        return _split_ratios(total, weights, gap)

    def _status_color(self, key):
        return _status_color(key, self.theme)

    def _input_box(self, slide, x, y, w, h, spec):
        return _input_box(slide, x, y, w, h, spec, theme=self.theme)

    def _banner(self, slide, y, spec, h=0.56):
        label = spec.get("label") if isinstance(spec, dict) else None
        text = spec.get("text") if isinstance(spec, dict) else spec
        return CalloutBanner(slide, text=text, label=label, y=y, h=h, theme=self.theme, deck=self)

    # ------------------------------------------------------------ 원자 부품 빌더 메서드
    def card(self, *args, **kwargs) -> Card:
        kwargs.setdefault("deck", self)
        kwargs.setdefault("slide", getattr(self, "current_slide", None))
        return Card(*args, **kwargs)

    def grid(self, *args, **kwargs) -> Grid:
        kwargs.setdefault("deck", self)
        kwargs.setdefault("slide", getattr(self, "current_slide", None))
        return Grid(*args, **kwargs)

    def split(self, *args, **kwargs) -> Split:
        kwargs.setdefault("deck", self)
        kwargs.setdefault("slide", getattr(self, "current_slide", None))
        return Split(*args, **kwargs)

    def kicker_header(self, *args, **kwargs) -> HeaderResult:
        kwargs.setdefault("deck", self)
        if "slide" not in kwargs and len(args) == 0:
            kwargs["slide"] = getattr(self, "current_slide", None)
        return KickerHeader(*args, **kwargs)

    def metric_box(self, *args, **kwargs) -> Rect:
        kwargs.setdefault("deck", self)
        return MetricBox(*args, **kwargs)

    def badge(self, *args, **kwargs) -> Any:
        kwargs.setdefault("deck", self)
        return Badge(*args, **kwargs)

    def step_card(self, *args, **kwargs) -> Rect:
        kwargs.setdefault("deck", self)
        return StepCard(*args, **kwargs)

    def table_box(self, *args, **kwargs) -> Rect:
        kwargs.setdefault("deck", self)
        return TableBox(*args, **kwargs)

    def callout_banner(self, *args, **kwargs) -> Any:
        kwargs.setdefault("deck", self)
        return CalloutBanner(*args, **kwargs)

    def form_field(self, *args, **kwargs) -> Rect:
        kwargs.setdefault("deck", self)
        return FormField(*args, **kwargs)

    # ------------------------------------------------------- 레이아웃 1 · 표지
    def add_dark_cover(self, title, subtitle=None, quote=None, stats=None,
                       kicker=None, lead=None, footer=None):
        """다크 표지 — 제목 · 인용 패널 · 큰 숫자 지표 콜아웃."""
        t = self.theme
        s = self._slide(t.dark)
        self._motif(s)
        pad = MARGIN + 0.1

        stats = list(stats or [])
        stat_w = max(3.5, self.cw * 0.34)
        stat_x = self.W - MARGIN - stat_w
        title_w = (stat_x - pad - 0.4) if stats else (self.cw - 0.8)

        KickerHeader(s, kicker=kicker, title=title, subtitle=subtitle, lead=lead,
                     dark=True, theme=t, deck=self, pad=pad, title_w=title_w)

        if quote:
            lines = title if isinstance(title, (list, tuple)) else [title]
            size = 33 if len(lines) <= 2 else 27
            paras = [{"text": ln, "size": size, "bold": True, "color": t.on_dark, "line": 1.18}
                     for ln in lines]
            if subtitle:
                paras.append({"text": subtitle, "size": 15.5, "color": t.accent_on_dark, "before": 10})
            y = 1.18 + max(_block_height(paras, title_w), 1.0) + 0.24
            if lead:
                y += _block_height([{"text": lead, "size": 12.5, "line": 1.42}], title_w - 0.3) + 0.3
            qh = 1.32
            top = min(max(y, self.H * 0.58), self.H - MARGIN - qh - 0.5)
            Card(s, pad, top, title_w, qh, dark=True, theme=t, deck=self)
            tf = self._textbox(s, pad + 0.28, top + 0.17, 0.6, 0.6)
            self._write(tf, [{"text": "\u201c", "size": 44, "bold": True,
                              "color": t.accent_on_dark, "line": 0.8}])
            paras = [{"text": quote.get("text", ""), "size": 14, "bold": True,
                      "color": t.on_dark, "italic": True, "line": 1.25}]
            if quote.get("source"):
                paras.append({"text": quote["source"], "size": 10.5,
                              "color": t.accent_on_dark, "before": 6})
            self._flow(s, pad + 0.92, top + 0.27, title_w - 1.2, qh - 0.4, paras,
                       where="표지 인용")

        if stats:
            stat_top = self.H * 0.16
            room = self.H - stat_top - MARGIN - 0.9
            gap = 0.15
            stat_h = min(1.6, (room - gap * (len(stats) - 1)) / len(stats))
            if stat_h < 1.1:
                self.warnings.append("표지 지표가 너무 많다 — 3개까지가 읽힌다")
            for i, st in enumerate(stats):
                top = stat_top + i * (stat_h + gap)
                card = Card(s, stat_x, top, stat_w, stat_h, dark=True, theme=t, deck=self)
                MetricBox(card, value=st.get("value", ""), label=st.get("label", ""),
                          desc=st.get("desc"), layout="side_by_side", dark=True, theme=t, deck=self)

        foot = footer or {}
        foot_y = self.H - 0.98
        if foot.get("left"):
            tf = self._textbox(s, pad, foot_y, self.cw * 0.62, 0.3)
            self._write(tf, [{"text": foot["left"], "size": 10.5, "color": t.dim}])
        if foot.get("right"):
            tf = self._textbox(s, self.W - MARGIN - 3.2, foot_y, 3.1, 0.3)
            self._write(tf, [{"text": foot["right"], "size": 10.5, "bold": True,
                              "color": t.accent_on_dark, "align": PP_ALIGN.RIGHT}])
        return s

    # -------------------------------------------------- 레이아웃 2 · 비교 카드
    def add_comparison_cards(self, title, left_card, right_card, bottom_summary=None,
                             kicker=None, lead=None, note=None):
        """좌우 비교 카드(라벨/값 행) + 하단 요약 카드 줄."""
        t = self.theme
        s = self._slide(t.light_bg)
        top = KickerHeader(s, kicker=kicker, title=title, lead=lead, note=note,
                           dark=False, theme=t, deck=self)

        bottom_items = (bottom_summary or {}).get("items") or []
        summary_h = 1.0 if bottom_items else 0.0
        summary_head = 0.34 if (bottom_summary or {}).get("title") else 0.0
        summary_gap = 0.10
        card_h = self.H - MARGIN - top - (summary_h + summary_head + summary_gap
                                          if bottom_items else 0)

        split = Split(MARGIN, top, self.cw, card_h, direction='h', ratios=[1.0, 1.0], gap=0.33,
                      slide=s, theme=t, deck=self)

        for cell, data, accent in zip(split, [left_card, right_card], [t.primary, t.accent]):
            data = data or {}
            card = Card(cell, slide=s, theme=t, deck=self)
            head_y = top + 0.32
            text_x = card.x + PAD
            if data.get("mark"):
                Badge(card, text=data["mark"], color=accent, size=16,
                      x=card.x + 0.35, y=head_y, d=0.52, slide=s, theme=t, deck=self)
                text_x = card.x + 1.02
            paras = [{"text": data.get("title", ""), "size": 16, "bold": True,
                      "color": t.primary, "line": 1.05}]
            if data.get("subtitle"):
                paras.append({"text": data["subtitle"], "size": 9, "bold": True,
                              "color": accent, "before": 4, "spacing": 1.0})
            self._flow(s, text_x, head_y + 0.04, card.x + card.w - text_x - PAD, 0.68, paras,
                       where="비교 카드 머리글")
            rows = []
            for i, row in enumerate(data.get("rows") or []):
                rows.append({"text": row.get("label", ""), "size": 9, "bold": True,
                             "color": accent, "before": 0 if i == 0 else 8, "spacing": 0.6})
                rows.append({"text": row.get("value", ""), "size": 11, "color": t.text,
                             "before": 2, "line": 1.28})
            body_y = head_y + 0.72
            self._flow(s, card.x + PAD + 0.05, body_y, card.w - 2 * PAD - 0.1,
                       top + card_h - PAD - body_y, rows, where="비교 카드 본문")

        if bottom_items:
            y = top + card_h + summary_gap
            if (bottom_summary or {}).get("title"):
                tf = self._textbox(s, MARGIN, y, 9.0, 0.28)
                self._write(tf, [{"text": bottom_summary["title"], "size": 12.5,
                                  "bold": True, "color": t.primary}])
                y += summary_head
            grid_b = Grid(MARGIN, y, self.cw, summary_h, rows=1, cols=len(bottom_items),
                          gap_x=0.34, slide=s, theme=t, deck=self)
            for i, item in enumerate(bottom_items):
                cell = grid_b[i]
                card = Card(cell, slide=s, theme=t, deck=self)
                tag = item.get("tag") or "%02d" % (i + 1)
                Badge(card, text=tag, color=t.secondary, size=9,
                      x=cell.x + 0.26, y=y + 0.2, d=0.34, slide=s, theme=t, deck=self)
                tx = cell.x + 0.70
                paras = [{"text": item.get("title", ""), "size": 11.5, "bold": True,
                          "color": t.primary, "line": 1.05}]
                if item.get("desc"):
                    paras.append({"text": item["desc"], "size": 9.5, "color": t.muted,
                                  "before": 3, "line": 1.25})
                self._flow(s, tx, y + 0.18, cell.x + cell.w - tx - 0.24, summary_h - 0.3, paras,
                           where="하단 요약")
        return s

    # ------------------------------------------------ 레이아웃 3 · 헌장 그리드
    def add_charter_grid(self, title, table_fields, key_principles=None,
                         kicker=None, lead=None, note=None):
        """표준 양식 1-Pager — 좌측 원칙·콜아웃 + 우측 항목 그리드."""
        t = self.theme
        s = self._slide(t.light_bg)
        top = KickerHeader(s, kicker=kicker, title=title, lead=lead, note=note,
                           dark=False, theme=t, deck=self)
        body_h = self.H - MARGIN - top

        grid_x, grid_w = MARGIN, self.cw
        if key_principles:
            side_w = max(2.9, self.cw * 0.28)
            split = Split(MARGIN, top, self.cw, body_h, direction='h',
                          ratios=[side_w, self.cw - side_w - 0.23], gap=0.23,
                          slide=s, theme=t, deck=self)
            card = Card(split[0], slide=s, theme=t, deck=self)
            y = top + 0.3
            if key_principles.get("title"):
                tf = self._textbox(s, MARGIN + PAD, y, side_w - 2 * PAD, 0.3)
                self._write(tf, [{"text": key_principles["title"], "size": 13.5,
                                  "bold": True, "color": t.primary}])
                y += 0.5
            items = key_principles.get("items") or []
            callout = key_principles.get("callout")
            cal_w = side_w - 2 * PAD
            cal_wide = cal_w >= 2.9
            cal_h = 0.95 if cal_wide else 1.25
            room = top + body_h - PAD - y - (cal_h + 0.2 if callout else 0)
            slot = room / max(1, len(items))
            for i, item in enumerate(items):
                tag = item.get("tag") or "%02d" % (i + 1)
                Badge(card, text=tag, color=t.primary, size=9,
                      x=MARGIN + PAD, y=y + 0.02, d=0.34, slide=s, theme=t, deck=self)
                paras = [{"text": item.get("title", ""), "size": 11.5, "bold": True,
                          "color": t.text, "line": 1.05}]
                if item.get("desc"):
                    paras.append({"text": item["desc"], "size": 9.5, "color": t.muted,
                                  "before": 3, "line": 1.3})
                self._flow(s, MARGIN + PAD + 0.44, y, side_w - 2 * PAD - 0.44, slot - 0.08,
                           paras, where="작성 원칙")
                y += slot
            if callout:
                cy = top + body_h - PAD - cal_h
                MetricBox(Rect(MARGIN + PAD, cy, cal_w, cal_h, slide=s, theme=t, deck=self),
                          value=callout.get("value", ""), label=callout.get("title", ""),
                          desc=callout.get("caption"), layout="auto", bg_color=t.tint,
                          slide=s, theme=t, deck=self)
            grid_x = split[1].x
            grid_w = split[1].w

        fields = list(table_fields or [])
        if not fields:
            return s
        cols = 2 if len(fields) > 4 else 1
        rows = int(math.ceil(len(fields) / cols))
        gx, gy = 0.21, 0.155
        grid_f = Grid(grid_x, top, grid_w, body_h, rows=rows, cols=cols,
                      gap_x=gx, gap_y=gy, slide=s, theme=t, deck=self)
        for i, fd in enumerate(fields):
            cell = grid_f[i]
            card = Card(cell, slide=s, theme=t, deck=self)
            tag = fd.get("tag") or "%02d" % (i + 1)
            Badge(card, text=tag, color=t.secondary, size=9.5,
                  x=cell.x + 0.26, y=cell.y + 0.24, d=0.36, slide=s, theme=t, deck=self)
            paras = [{"text": fd.get("title", ""), "size": 12, "bold": True,
                      "color": t.primary, "line": 1.05}]
            if fd.get("desc"):
                paras.append({"text": fd["desc"], "size": 9.5, "color": t.muted,
                              "before": 4, "line": 1.3})
            self._flow(s, cell.x + 0.72, cell.y + 0.22, cell.w - 0.98, cell.h - 0.4, paras,
                       where="양식 항목")
        return s

    # ------------------------------------------- 레이아웃 4 · Gate 프로세스
    def add_process_gates(self, title, steps, status_legend=None, kicker=None, lead=None,
                          note=None, banner=None):
        """단계 카드(가로 흐름) + 하단 신호등·체크리스트 + 선택 배너."""
        t = self.theme
        s = self._slide(t.light_bg)
        top = KickerHeader(s, kicker=kicker, title=title, lead=lead, note=note,
                           dark=False, theme=t, deck=self)

        legend_items = (status_legend or {}).get("items") or []
        legend_gap = 0.16
        legend_head = 0.36 if legend_items else 0.0
        legend_h = 0.0
        legend_paras = []
        if legend_items:
            lw = (self.cw - 0.34 * (len(legend_items) - 1)) / len(legend_items)
            text_w = lw - 0.98
            for item in legend_items:
                level = item.get("level") or item.get("color")
                color = self._status_color(level) if level else (
                    t.secondary if item.get("tag") else t.muted)
                paras = [{"text": item.get("title", ""), "size": 12, "bold": True,
                          "color": t.primary, "line": 1.05}]
                if item.get("condition"):
                    paras.append({"text": item["condition"], "size": 9.5, "color": t.text,
                                  "before": 4, "line": 1.25})
                if item.get("action"):
                    paras.append({"text": item["action"], "size": 9.5, "bold": True,
                                  "color": color, "before": 3, "line": 1.25})
                legend_paras.append((item, color, paras))
            need = max(_block_height(p, text_w) for _, _, p in legend_paras)
            legend_h = min(2.05, max(1.15, need + 0.50))
        banner_h = 0.56 if banner else 0.0
        banner_gap = 0.14 if banner else 0.0
        steps = list(steps or [])

        room = self.H - MARGIN - top - banner_h - banner_gap
        step_w = self._columns(len(steps))[0][1] if steps else self.cw
        step_need = 0.0
        for st in steps:
            head = [{"text": st.get("title", ""), "size": 14, "line": 1.05}]
            if st.get("period"):
                head.append({"text": st["period"], "size": 9.5, "before": 3})
            need = 0.28 + (0.65 if st.get("tag") else 0.0)
            need += max(_block_height(head, step_w - 0.6), 0.4) + 0.12
            acts = st.get("activities") or []
            if acts:
                need += _block_height([{"text": "· " + a, "size": 10, "before": 3,
                                        "line": 1.2} for a in acts], step_w - 0.6)
            if st.get("output") or st.get("criteria"):
                need += 0.12 + 0.80
            step_need = max(step_need, need + PAD)

        if legend_items:
            legend_room = room - step_need - legend_head - legend_gap
            legend_h = max(1.15, min(legend_h, legend_room))
            card_h = room - (legend_h + legend_head + legend_gap)
        else:
            card_h = room

        split_st = Split(MARGIN, top, self.cw, card_h, direction='h',
                         ratios=[1.0] * max(1, len(steps)), gap=GAP,
                         slide=s, theme=t, deck=self)
        for i, st in enumerate(steps):
            cell = split_st[i]
            card = Card(cell, slide=s, theme=t, deck=self)
            accent = t.accent if i >= len(steps) / 2 else t.primary
            StepCard(card, step_no=st.get("tag"), title=st.get("title", ""),
                     items=st.get("activities"), period=st.get("period"),
                     output=st.get("output"), criteria=st.get("criteria"),
                     activities_label=st.get("activities_label", "핵심 활동"),
                     output_label=st.get("output_label", "산출물"),
                     criteria_label=st.get("criteria_label", "통과 기준"),
                     accent=accent, dark=False, theme=t, slide=s, deck=self)
            if i < len(steps) - 1:
                tri = self._shape(s, MSO_SHAPE.ISOSCELES_TRIANGLE, cell.x + cell.w + 0.085,
                                  top + card_h / 2 - 0.1, 0.14, 0.2, fill=t.dim)
                tri.rotation = 90

        if legend_items:
            y = top + card_h + legend_gap
            if (status_legend or {}).get("title"):
                tf = self._textbox(s, MARGIN, y, 4.6, 0.28)
                self._write(tf, [{"text": status_legend["title"], "size": 12.5,
                                  "bold": True, "color": t.primary}])
            if (status_legend or {}).get("note"):
                note_w = self.cw * 0.52
                tf = self._textbox(s, self.W - MARGIN - note_w, y + 0.04, note_w, 0.26)
                self._write(tf, [{"text": status_legend["note"], "size": 10,
                                  "color": t.muted, "align": PP_ALIGN.RIGHT}])
            y += legend_head
            grid_l = Grid(MARGIN, y, self.cw, legend_h, rows=1, cols=len(legend_items),
                          gap_x=0.34, slide=s, theme=t, deck=self)
            for i, (item, color, paras) in enumerate(legend_paras):
                cell = grid_l[i]
                card = Card(cell, slide=s, theme=t, deck=self)
                tag = item.get("tag")
                if tag:
                    Badge(card, text=tag, color=color, size=9.5,
                          x=cell.x + 0.26, y=cell.y + 0.26, d=0.34, slide=s, theme=t, deck=self)
                else:
                    Badge(card, text="", color=color,
                          x=cell.x + 0.28, y=cell.y + 0.28, d=0.3, slide=s, theme=t, deck=self)
                text_x = cell.x + 0.70
                self._flow(s, text_x, cell.y + 0.24, cell.x + cell.w - text_x - 0.28, legend_h - 0.4,
                           paras, where="범례 · 체크리스트")

        if banner:
            CalloutBanner(s, text=(banner.get("text") if isinstance(banner, dict) else banner),
                          label=(banner.get("label") if isinstance(banner, dict) else None),
                          y=self.H - MARGIN - banner_h, h=banner_h, theme=t, deck=self)
        return s

    # --------------------------------------------- 레이아웃 5 · 임원 대시보드
    def add_executive_dashboard(self, title, kpi_summary, top_items, matrix_data,
                                decisions_ask, kicker=None, note=None):
        """2×2 사분면 — 지표 / 핵심 항목 / 현황 매트릭스 / 의사결정 요청."""
        t = self.theme
        s = self._slide(t.light_bg)
        kpi_summary = kpi_summary or {}
        top_items = top_items or {}
        matrix_data = matrix_data or {}
        decisions_ask = decisions_ask or {}

        KickerHeader(s, kicker=kicker, title=title, note=note, dark=False, theme=t, deck=self)

        col_gap, row_gap = GAP, 0.25
        lx, lw = MARGIN, (self.cw - col_gap) * 0.524
        rx, rw = MARGIN + lw + col_gap, (self.cw - col_gap) * 0.476
        ty = 1.52
        room = self.H - MARGIN - ty - row_gap
        th = room * 0.505
        by, bh = ty + th + row_gap, room - th

        # 좌상 — 지표 콜아웃
        Card(s, lx, ty, lw, th, theme=t, deck=self)
        tf = self._textbox(s, lx + PAD, ty + 0.28, lw - 2 * PAD, 0.28)
        self._write(tf, [{"text": kpi_summary.get("title", ""), "size": 13, "bold": True,
                          "color": t.primary}])
        stats = kpi_summary.get("stats") or []
        banner = kpi_summary.get("banner")
        if stats:
            sw = (lw - 2 * PAD) / len(stats)
            colors = [t.primary, t.secondary, t.accent, t.primary, t.secondary]
            for i, st in enumerate(stats):
                x = lx + PAD + i * sw
                MetricBox(Rect(x, ty + 0.72, sw, th - 0.72, slide=s, theme=t, deck=self),
                          value=st.get("value", ""), label=st.get("label", ""),
                          color=st.get("color") or colors[i % len(colors)],
                          layout="stacked", slide=s, theme=t, deck=self)
        if banner:
            self._shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, lx + PAD, ty + th - 0.74,
                        lw - 2 * PAD, 0.54, fill=t.tint, radius=0.14)
            self._flow(s, lx + PAD + 0.2, ty + th - 0.60, lw - 2 * PAD - 0.4, 0.34,
                       [{"text": banner, "size": 11, "bold": True, "color": t.primary}],
                       where="대시보드 배너")

        # 우상 — 핵심 항목
        card_tr = Card(s, rx, ty, rw, th, theme=t, deck=self)
        tf = self._textbox(s, rx + PAD, ty + 0.28, rw - 2 * PAD, 0.28)
        self._write(tf, [{"text": top_items.get("title", ""), "size": 13, "bold": True,
                          "color": t.primary}])
        items = top_items.get("items") or []
        slot = (th - 0.85) / max(1, len(items))
        for i, item in enumerate(items):
            y = ty + 0.70 + i * slot
            Badge(card_tr, text=item.get("tag") or str(i + 1), color=t.accent, size=9.5,
                  x=rx + PAD, y=y + 0.04, d=0.32, slide=s, theme=t, deck=self)
            paras = [{"text": item.get("title", ""), "size": 11.5, "bold": True,
                      "color": t.text, "line": 1.05}]
            if item.get("desc"):
                paras.append({"text": item["desc"], "size": 9.5, "color": t.muted,
                              "before": 3, "line": 1.15})
            self._flow(s, rx + PAD + 0.42, y, rw - 2 * PAD - 0.42, slot - 0.04, paras,
                       where="대시보드 핵심 항목")

        # 좌하 — 현황 매트릭스
        card_bl = Card(s, lx, by, lw, bh, theme=t, deck=self)
        TableBox(card_bl, headers=matrix_data.get("columns", []),
                 rows=matrix_data.get("rows", []),
                 status_label=matrix_data.get("status_label", "상태"),
                 title=matrix_data.get("title", ""),
                 slide=s, theme=t, deck=self)

        # 우하 — 의사결정 요청
        card_br = Card(s, rx, by, rw, bh, theme=t, deck=self)
        tf = self._textbox(s, rx + PAD, by + 0.25, rw - 2 * PAD, 0.28)
        self._write(tf, [{"text": decisions_ask.get("title", ""), "size": 13, "bold": True,
                          "color": t.primary}])
        asks = decisions_ask.get("items") or []
        slot = (bh - 0.8) / max(1, len(asks))
        for i, ask in enumerate(asks):
            y = by + 0.67 + i * slot
            Badge(card_br, text=ask.get("tag") or str(i + 1), color=t.accent, size=9.5,
                  x=rx + PAD, y=y + 0.04, d=0.32, slide=s, theme=t, deck=self)
            paras = [{"text": ask.get("title", ""), "size": 11.5, "bold": True,
                      "color": t.text, "line": 1.05}]
            if ask.get("desc"):
                paras.append({"text": ask["desc"], "size": 9.5, "color": t.muted,
                              "before": 3, "line": 1.2})
            self._flow(s, rx + PAD + 0.42, y, rw - 2 * PAD - 0.42, slot - 0.04, paras,
                       where="의사결정 요청")
        return s

    # ------------------------------------------------ 레이아웃 6 · 다크 마무리
    def add_dark_closing(self, title, timeline_steps, action_items=None,
                         kicker=None, lead=None, footer=None):
        """다크 마무리 — 가로 타임라인 + 협조/액션 카드."""
        t = self.theme
        s = self._slide(t.dark)
        self._shape(s, MSO_SHAPE.OVAL, -1.6, 4.4, 4.4, 4.4, fill=None,
                    line=t.dark_line, line_w=1.0)
        self._shape(s, MSO_SHAPE.OVAL, 11.2, -1.2, 3.6, 3.6, fill=None,
                    line=t.dark_line, line_w=1.0)

        pad = MARGIN + 0.1
        KickerHeader(s, kicker=kicker, title=title, lead=lead, dark=True,
                     theme=t, deck=self, pad=pad)

        steps = list(timeline_steps or [])
        items = (action_items or {}).get("items") or []

        foot_y = self.H - 0.82
        action_bottom = (foot_y - 0.12) if footer else (self.H - MARGIN)
        action_head = 0.34 if (action_items or {}).get("title") else 0.0
        action_h = min(1.7, max(1.42, (action_bottom - 4.3 - action_head) * 0.62)) if items else 0.0
        action_y = action_bottom - action_h - action_head if items else action_bottom

        line_y = max(2.5, min(self.H * 0.35, action_y - 1.9))
        if steps:
            self._shape(s, MSO_SHAPE.RECTANGLE, 2.0, line_y, self.W - 4.0, 0.014,
                        fill=t.dark_line)
            split_tm = Split(MARGIN, line_y, self.cw, 1.5, direction='h',
                             ratios=[1.0] * len(steps), gap=GAP,
                             slide=s, theme=t, deck=self)
            for i, st in enumerate(steps):
                cell = split_tm[i]
                cx = cell.x + cell.w / 2 - 0.22
                half = len(steps) / 2.0
                fill = t.accent_on_dark if i < half else t.dark_panel
                color = t.dark if i < half else t.on_dark
                b = Badge(s, text=st.get("tag") or str(i + 1), color=fill, text_color=color,
                          size=12, x=cx, y=line_y - 0.22, d=0.44, dark=True, theme=t, deck=self)
                if i >= half:
                    b.line.color.rgb = RGBColor.from_string(t.accent_on_dark)
                    b.line.width = Pt(1.0)
                paras = []
                if st.get("date"):
                    paras.append({"text": st["date"], "size": 10.5, "bold": True,
                                  "color": t.accent_on_dark, "align": PP_ALIGN.CENTER,
                                  "spacing": 0.6})
                paras.append({"text": st.get("title", ""), "size": 15, "bold": True,
                              "color": t.on_dark, "before": 4, "align": PP_ALIGN.CENTER,
                              "line": 1.1})
                if st.get("desc"):
                    paras.append({"text": st["desc"], "size": 10, "color": t.on_dark_muted,
                                  "before": 5, "align": PP_ALIGN.CENTER, "line": 1.3})
                text_y = line_y + 0.44
                self._flow(s, cell.x, text_y, cell.w, action_y - text_y - 0.16, paras,
                           where="타임라인")

        if items:
            y = action_y
            if action_head:
                tf = self._textbox(s, MARGIN, y, self.cw * 0.75, 0.28)
                self._write(tf, [{"text": action_items["title"], "size": 13, "bold": True,
                                  "color": t.on_dark}])
                y += action_head
            grid_act = Grid(MARGIN, y, self.cw, action_h, rows=1, cols=len(items),
                            gap_x=0.34, slide=s, theme=t, deck=self)
            for i, item in enumerate(items):
                cell = grid_act[i]
                Card(cell, dark=True, slide=s, theme=t, deck=self)
                paras = []
                if item.get("tag"):
                    paras.append({"text": item["tag"], "size": 10, "bold": True,
                                  "color": t.accent_on_dark, "spacing": 0.6})
                paras.append({"text": item.get("title", ""), "size": 12.5, "bold": True,
                              "color": t.on_dark, "before": 3, "line": 1.05})
                if item.get("desc"):
                    paras.append({"text": item["desc"], "size": 9.5,
                                  "color": t.on_dark_muted, "before": 4, "line": 1.25})
                self._flow(s, cell.x + PAD, y + 0.24, cell.w - 2 * PAD, action_h - 0.42, paras,
                           where="액션 카드")
        if footer:
            tf = self._textbox(s, MARGIN, foot_y, self.cw, 0.28)
            self._write(tf, [{"text": footer, "size": 10, "color": t.dim,
                              "align": PP_ALIGN.CENTER}])
        return s

    # ------------------------------------------------ 레이아웃 7 · 작성용 양식
    def add_charter_form(self, title, rows, kicker=None, note=None, footer=None):
        """실무자가 클릭해 바로 타이핑하는 빈 양식."""
        t = self.theme
        s = self._slide(t.light_bg)
        KickerHeader(s, kicker=kicker, title=title, note=note, dark=False, theme=t, deck=self,
                     title_size=22, title_y=0.66)

        body_top = 1.12
        body_h = (self.H - 0.86 if footer else self.H - MARGIN) - body_top
        row_gap, field_gap = 0.16, 0.16
        rows = list(rows or [])
        num = 0

        split_rows = Split(MARGIN, body_top, self.cw, body_h, direction='v',
                           ratios=[r.get("weight", 1) for r in rows], gap=row_gap,
                           slide=s, theme=t, deck=self)

        for row_cell, row in zip(split_rows, rows):
            fields = row.get("fields") or []
            split_fields = Split(row_cell.x, row_cell.y, row_cell.w, row_cell.h, direction='h',
                                 ratios=[f.get("flex", 1) for f in fields], gap=field_gap,
                                 slide=s, theme=t, deck=self)
            for field_cell, fd in zip(split_fields, fields):
                num += 1
                FormField(field_cell, label=fd.get("label", ""), hint=fd.get("hint"),
                          num=fd.get("num") or "%02d" % num,
                          inputs=fd.get("inputs"), layout=fd.get("layout", "row"),
                          slide=s, theme=t, deck=self)

        if footer:
            tf = self._textbox(s, MARGIN, self.H - 0.78, self.cw, 0.28)
            self._write(tf, [{"text": footer, "size": 9.5, "color": t.muted,
                              "align": PP_ALIGN.CENTER}])
        return s

    # 별칭 (호환성 유지)
    charter_form = add_charter_form

    # -------------------------------------------------- 레이아웃 8 · 판정 기준
    def add_decision_matrix(self, title, criteria, options, rule=None,
                            kicker=None, lead=None, note=None):
        """기준 × 선택지 매트릭스 — 읽는 사람이 스스로 판정하는 체크 표다."""
        t = self.theme
        s = self._slide(t.light_bg)
        top = KickerHeader(s, kicker=kicker, title=title, lead=lead, note=note,
                           dark=False, theme=t, deck=self)

        options = list(options or [])
        criteria = list(criteria or [])
        accents = [t.primary, t.accent, t.secondary]
        rule_h = 0.56 if rule else 0.0
        rule_gap = 0.14 if rule else 0.0
        head_h = 0.42
        row_gap = 0.14
        body = self.H - MARGIN - top - rule_h - rule_gap
        row_h = (body - head_h - row_gap * len(criteria)) / max(1, len(criteria))

        label_w = self.cw * 0.25
        spans = self._split(self.cw - label_w - 0.16, [1] * max(1, len(options)), 0.16)

        tf = self._textbox(s, MARGIN + 0.22, top, label_w - 0.36, 0.3)
        self._write(tf, [{"text": "판정 기준", "size": 9.5, "bold": True, "color": t.dim,
                          "spacing": 0.8}])
        for i, opt in enumerate(options):
            ox, ow = spans[i]
            ox += MARGIN + label_w + 0.16
            paras = [{"text": opt.get("title", ""), "size": 12.5, "bold": True,
                      "color": accents[i % len(accents)], "align": PP_ALIGN.CENTER}]
            if opt.get("subtitle"):
                paras[0]["text"] += "  " + opt["subtitle"]
            self._flow(s, ox, top, ow, head_h - 0.06, paras, where="판정 열 머리글")

        grid_crit = Grid(MARGIN, top + head_h, self.cw, body - head_h,
                         rows=len(criteria), cols=1, gap_y=row_gap,
                         slide=s, theme=t, deck=self)
        for r, c in enumerate(criteria):
            cell = grid_crit[r]
            card = Card(cell, slide=s, theme=t, deck=self)
            tag = c.get("tag") or "%d" % (r + 1)
            Badge(card, text=tag, color=t.secondary, size=9.5,
                  x=cell.x + 0.24, y=cell.y + 0.22, d=0.32, slide=s, theme=t, deck=self)
            paras = [{"text": c.get("name", ""), "size": 11.5, "bold": True,
                      "color": t.primary, "line": 1.05}]
            if c.get("desc"):
                paras.append({"text": c["desc"], "size": 9, "color": t.muted,
                              "before": 3, "line": 1.2})
            self._flow(s, cell.x + 0.66, cell.y + 0.20, label_w - 0.9, row_h - 0.36, paras,
                       where="판정 기준 이름")
            for i, value in enumerate(c.get("values") or []):
                if i >= len(spans):
                    break
                ox, ow = spans[i]
                ox += MARGIN + label_w + 0.16
                self._shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, ox, cell.y + 0.16, ow,
                            row_h - 0.32, fill=t.tint, radius=0.08)
                box = self._shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, ox + 0.18,
                                  cell.y + row_h / 2 - 0.11, 0.22, 0.22,
                                  fill=t.card, line=accents[i % len(accents)],
                                  line_w=1.0, radius=0.15)
                box.shadow.inherit = False
                self._flow(s, ox + 0.52, cell.y + 0.26, ow - 0.72, row_h - 0.52,
                           [{"text": value, "size": 10, "color": t.text, "line": 1.25}],
                           where="판정 칸")

        if rule:
            CalloutBanner(s, text=(rule.get("text") if isinstance(rule, dict) else rule),
                          label=(rule.get("label") if isinstance(rule, dict) else None),
                          y=self.H - MARGIN - rule_h, h=rule_h, theme=t, deck=self)
        return s

    # 별칭 (호환성 유지)
    decision_matrix = add_decision_matrix

    # ------------------------------------------------------------------ 출력
    def add_notes(self, slide, text):
        slide.notes_slide.notes_text_frame.text = text

    def save(self, path):
        self.prs.save(path)
        return path


# --------------------------------------------------------------- 키의 진본
LAYOUTS = {
    "dark_cover": {
        "method": "add_dark_cover",
        "required": ["title (문자열 또는 줄 목록)"],
        "optional": ["kicker", "subtitle", "lead", "quote{text,source}",
                     "stats[{value,label,desc}] — 3개까지", "footer{left,right}", "notes"],
    },
    "comparison_cards": {
        "method": "add_comparison_cards",
        "required": ["title", "left_card{title,rows[{label,value}]}",
                     "right_card{title,rows[{label,value}]}"],
        "optional": ["kicker", "lead", "note (우상단 안내 배지)", "left_card.mark",
                     "left_card.subtitle",
                     "bottom_summary{title,items[{tag,title,desc}]}", "notes"],
    },
    "charter_grid": {
        "method": "add_charter_grid",
        "required": ["title", "table_fields[{title,desc}] — 8개 안팎"],
        "optional": ["kicker", "lead", "note (우상단 안내 배지)", "table_fields[].tag",
                     "key_principles{title,items[{tag,title,desc}],"
                     "callout{value,title,caption}}", "notes"],
    },
    "process_gates": {
        "method": "add_process_gates",
        "required": ["title", "steps[{title}] — 3~5개"],
        "optional": ["kicker", "lead", "note (우상단 안내 배지)",
                     "steps[].tag / period / activities[] / output / criteria",
                     "status_legend{title,note,"
                     "items[{tag|level(ok|warn|bad),title,condition,action}]}",
                     "banner (문자열 또는 {label,text})", "notes"],
    },
    "executive_dashboard": {
        "method": "add_executive_dashboard",
        "required": ["title", "kpi_summary{title,stats[{value,label}]}",
                     "top_items{title,items[{title,desc}]}",
                     "matrix_data{title,columns[],rows[{cells[],status,status_label}]}",
                     "decisions_ask{title,items[{title,desc}]}"],
        "optional": ["kicker", "note (문자열 또는 줄 목록)", "kpi_summary.banner",
                     "matrix_data.status_label", "notes"],
    },
    "dark_closing": {
        "method": "add_dark_closing",
        "required": ["title", "timeline_steps[{title}] — 3~5개"],
        "optional": ["kicker", "lead", "timeline_steps[].tag / date / desc",
                     "action_items{title,items[{tag,title,desc}]}", "footer", "notes"],
    },
    "charter_form": {
        "method": "add_charter_form",
        "required": ["title",
                     "rows[{weight,fields[{label,flex,inputs[{placeholder,flex,caption}]}]}]"],
        "optional": ["kicker", "note (문자열 또는 줄 목록)", "footer",
                     "fields[].num / hint / layout(row|stack)", "inputs[].size", "notes"],
    },
    "decision_matrix": {
        "method": "add_decision_matrix",
        "required": ["title", "options[{title,subtitle}] — 2~3개",
                     "criteria[{name,desc,values[]}] — values 는 options 와 같은 수"],
        "optional": ["kicker", "lead", "note (우상단 안내 배지)", "criteria[].tag",
                     "rule (문자열 또는 {label,text} · 하단 판정 규칙)", "notes"],
    },
}


def build(data):
    """{page?, theme?, font?, slides:[{layout, ...}]} → Deck."""
    deck = Deck(theme=data.get("theme"), font=data.get("font"),
                page=data.get("page", DEFAULT_PAGE))
    for i, spec in enumerate(data.get("slides") or [], start=1):
        spec = dict(spec)
        layout = spec.pop("layout", None)
        if layout not in LAYOUTS:
            raise ValueError("%d번째 슬라이드의 layout 이 모르는 값: %r (가능: %s)"
                             % (i, layout, ", ".join(LAYOUTS)))
        note = spec.pop("notes", None)
        method = getattr(deck, LAYOUTS[layout]["method"])
        try:
            slide = method(**spec)
        except TypeError as exc:
            raise ValueError("%d번째 슬라이드(%s) 키가 맞지 않는다: %s\n  필수 키: %s"
                             % (i, layout, exc,
                                ", ".join(LAYOUTS[layout]["required"]))) from exc
        if note:
            deck.add_notes(slide, note)
    return deck


def _print_schema():
    print("레이아웃과 키 (이 목록이 진본이다)\n")
    for name, spec in LAYOUTS.items():
        print("%s  →  Deck.%s()" % (name, spec["method"]))
        print("  필수 : " + ", ".join(spec["required"]))
        print("  선택 : " + ", ".join(spec["optional"]))
        print()
    print("theme 키 : " + ", ".join(asdict(Theme())))
    print("page : " + ", ".join("%s (%.3f x %.3f in)" % (k, v[0], v[1])
                                for k, v in PAGE_SIZES.items())
          + "  — 기본 " + DEFAULT_PAGE + ", [가로, 세로] 로 직접 줄 수도 있다")


def main(argv=None):
    ap = argparse.ArgumentParser(description="데이터(JSON)로 임원 보고용 덱을 만든다.")
    ap.add_argument("data", nargs="?", help="슬라이드 데이터 JSON 경로")
    ap.add_argument("-o", "--out", help="출력 .pptx 경로")
    ap.add_argument("--schema", action="store_true", help="레이아웃·키 목록을 찍고 끝낸다")
    args = ap.parse_args(argv)

    if args.schema or not args.data:
        _print_schema()
        return 0
    if not args.out:
        ap.error("-o 출력 경로가 필요하다")

    with open(args.data, encoding="utf-8") as fp:
        data = json.load(fp)
    deck = build(data)
    deck.save(args.out)
    for w in deck.warnings:
        print("경고: " + w, file=sys.stderr)
    print("%s — 슬라이드 %d장" % (args.out, len(deck.prs.slides._sldIdLst)))
    return 1 if deck.warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
