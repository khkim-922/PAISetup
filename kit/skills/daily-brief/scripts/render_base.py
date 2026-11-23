"""창과 메일 한 장이 함께 쓰는 그림 바탕 — 줄 안의 꼴을 읽는 한 걸음(`inline_walk` — 겉만 바꿔 끼운다), 지은 때의 꼴, 시각 없는 모임의 말.
파일을 읽지 않고 망에 닿지 않는다.
"""

from __future__ import annotations

import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_inline.py — `-I` 로 돌아도 싣는다
from brief_inline import INLINE, UNID  # noqa: E402

DATELINE = "{:%Y-%m-%d}({}) {:%H:%M} 지음"
NO_TIME_SAID = "메일에 시각이 없어 넣지 못합니다 — 시각을 정해 대화에서 「그 약속 ○시로 넣어 줘」 하시면 넣습니다."


def inline_walk(text: str, skin) -> str:
    """줄 안의 꼴을 왼쪽부터 읽어 겉(`skin` — 창 · 메일)으로 짓는다: 고정 글자 · 메일 링크 · 사람 · 회의실 · 표지 · 굵게. 꼴 밖의 글과 꼴이
    아닌 표시(번호가 아닌 mail: · 빈 표지)는 이스케이프해 쓴 그대로 둔다. 링크 글 속은 겉의 `inside()` 로 한 번 더 읽는다."""
    out, at = [], 0
    for m in INLINE.finditer(text):
        out.append(html.escape(text[at:m.start()], quote=True))
        at = m.end()
        if m.group("code") is not None:
            out.append(skin.code(m.group("code")))
        elif m.group("ref") is not None:
            ref, label = m.group("ref"), m.group("label")
            if not UNID.match(ref):
                skin.bad_ref()
                out.append(html.escape(m.group(0), quote=True))
                continue
            inner = inline_walk(label, skin.inside()) if label.strip() else html.escape(ref.upper(), quote=True)
            out.append(skin.mail(inner, ref))
        elif m.group("pref") is not None:
            out.append(skin.person(inline_walk(m.group("plabel"), skin.inside()), m.group("pref").strip()))
        elif m.group("rref") is not None:
            out.append(skin.room(inline_walk(m.group("rlabel"), skin.inside()), m.group("rref")))
        elif m.group("sref") is not None:              # 절의 종류 표지 — 사람에게는 이름만 선다
            out.append(inline_walk(m.group("slabel"), skin))
        elif m.group("pill") is not None:
            words = m.group("pill").strip()
            out.append(skin.pill(words, bool(m.group("over"))) if words else html.escape(m.group(0), quote=True))
        else:
            out.append(skin.bold(inline_walk(m.group("bold"), skin)))
    out.append(html.escape(text[at:], quote=True))
    return "".join(out)
