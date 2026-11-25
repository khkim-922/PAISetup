"""같은 보고 글에서 휴대폰 너비의 메일 한 장을 짓는다(`mail_sheet`) — 자리 밖에서 보기. 창과 같은 꼴 읽기(`brief_text` · 곁의 `brief_*`)와 같은 줄 안의 걸음
(`render_base.inline_walk`)을 메일의 겉으로 쓴다. 파일을 쓰거나 사용자 폴더를 읽지 않고 망에 닿지 않는다 — 짓는 글만 낸다.
"""

from __future__ import annotations

import datetime as dt
import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 손가락들 — `-I` 로 돌아도 싣는다
from brief_const import WEEKDAYS  # noqa: E402
from brief_cards import card_head  # noqa: E402
from brief_inline import plain  # noqa: E402
from brief_sections import is_empty_done  # noqa: E402
from brief_tasks import asks_time, card_shaped, dated_card, take_card  # noqa: E402
from brief_text import DASH, Block, Item, parse  # noqa: E402
from render_base import DATELINE, NO_TIME_SAID, inline_walk  # noqa: E402
from task_kinds import VIA_NONE, VIA_TALK  # noqa: E402


# ── 메일 한 장 — 자리 밖에서 보기 ─────────────────────────────────────────────
# 같은 보고 글에서 휴대폰 너비의 메일 한 장을 짓는다. 메일 프로그램은 <style> · 스크립트 · 바깥 글꼴을 거르므로 꾸밈은 다 줄마다의 style
# 속성에 든다. 누름 단추가 없고, 링크도 없다 — 근거 메일은 보고 글이 쓴 그 글(보낸 분 · 날짜 · 제목)로 선다(사내 웹메일 링크가 휴대폰 메일
# 앱에서 열리는지 안 쟀다). 글은 다 이스케이프한다 — 창과 같다.
MAIL_TAG = "[메일 비서]"
SUBJECT_MAX = 140                              # 제목의 글자 수 — 메일 목록에서 잘리는 만큼보다 넉넉히, 한 줄을 넘는 머리말은 자른다
# 맡길 일이 든 절의 머리에 서는 한 줄 — 메일에서는 누를 수 없어 어디서 맡기나를 댄다. 카드의 할 일은 줄의 글로만 선다
MAIL_TASK_INTRO = "맡기시려면 PC 의 보고 창에서 누르세요 — 메일에서는 맡기실 수 없습니다."
MAIL_TASK_BAD = "적힌 꼴이 틀려 창에서도 맡기실 수 없습니다 — 대화에서 말씀해 주세요"
MAIL_META = "{slot} 사람 없이 지은 보고 · PC 의 보고 창에 같은 보고가 떠 있습니다"
MAIL_FOOT = ("「자리 밖에서 보기」를 켜 두셔서 보내 드렸습니다 — 이 메일은 본인에게만 갑니다. 그만 받으시려면 PC 의 보고 창 끝 「보고 맞추기」에서 "
             "끄시거나, 대화에서 「보고 메일 그만 보내」 하세요.")
MS_SERIF = "font-family:'Noto Serif KR','Nanum Myeongjo',Batang,serif;"
MS = {
    "body": "margin:0;padding:0;background:#FAFAF9;",
    "sheet": ("max-width:600px;margin:0 auto;padding:16px;font-family:'Malgun Gothic','맑은 고딕','Noto Sans KR',sans-serif;font-size:15px;"
              "line-height:1.65;color:#1C1917;word-break:keep-all;overflow-wrap:anywhere;"),
    "eyebrow": "margin:0;font-size:11px;letter-spacing:0.08em;color:#78716C;font-weight:600;",
    "h1": f"margin:4px 0 6px;{MS_SERIF}font-size:26px;line-height:1.25;font-weight:600;",
    "lede": "margin:0;font-size:16px;color:#57534E;",
    "meta": "margin:8px 0 0;font-size:13px;color:#78716C;",
    "clock": "margin:20px 0 0;padding:14px 16px;background:#F5F5F4;border:1px solid #D6D3D1;border-radius:12px;",
    "clock_label": "margin:0 0 8px;font-size:13px;font-weight:600;color:#57534E;",
    "clock_row": "margin:4px 0 0;",
    "clock_t": "font-size:18px;",
    "aside": "color:#57534E;font-size:13px;",
    "h2": f"margin:28px 0 10px;padding-bottom:8px;border-bottom:1px solid #D6D3D1;{MS_SERIF}font-size:20px;font-weight:600;",
    "h3": "margin:18px 0 8px;font-size:16px;font-weight:600;",
    "intro": "margin:0 0 10px;font-size:14px;color:#57534E;",
    "card": "margin:0 0 10px;padding:14px 16px;background:#F5F5F4;border:1px solid #D6D3D1;border-radius:12px;",
    "card_appt": "margin:0 0 10px;padding:14px 16px;background:#F5F5F4;border:1px solid #D6D3D1;border-left:4px solid #C2410C;border-radius:12px;",
    "card_title": "margin:0;font-weight:600;font-size:16px;",
    "card_when": "margin:2px 0 0;font-size:14px;color:#57534E;",
    "point": "margin:6px 0 0;font-size:14px;",
    "facts": "margin:8px 0 0;font-size:13px;color:#57534E;",
    "put": "margin:8px 0 0;font-size:13px;color:#57534E;",
    "put_said": "margin:4px 0 0;font-size:13px;color:#78716C;",
    "row": "margin:0 0 6px;font-size:14px;",
    "para": "margin:0 0 10px;font-size:14px;",
    "caution": "margin:0 0 10px;padding:12px 14px;border:1px solid #F59E0B;border-radius:12px;background:#FFFBEB;font-size:14px;",
    "pill": "display:inline-block;padding:0 8px;border-radius:9999px;background:#E7E5E4;color:#57534E;font-size:12px;line-height:1.8;",
    "pill_over": "display:inline-block;padding:0 8px;border-radius:9999px;background:#DC2626;color:#FAFAF9;font-size:12px;line-height:1.8;",
    "foot": "margin:28px 0 0;padding-top:12px;border-top:1px solid #D6D3D1;font-size:12px;color:#78716C;line-height:1.7;",
}


class MailSkin:
    """메일의 겉 — 메일 프로그램은 <style> 을 거르므로 꾸밈은 줄마다의 style 속성에 든다. 고정 글자는 글만, 메일 링크는 그 글만(링크 없이 —
    글 없는 링크는 창처럼 메일 번호로 선다), 사람은 이름만(주소는 메일 한 장에 안 싣는다), 회의실도 방 이름만, 결재 문서도 그 글만, 굵게는 <b>."""

    def inside(self) -> MailSkin:
        """링크 글 속에 쓸 겉 — 메일의 겉은 링크가 없어 그대로다."""
        return self

    def code(self, words: str) -> str:
        """고정 글자 — 글만."""
        return html.escape(words, quote=True)

    def bad_ref(self) -> None:
        """꼴이 틀린 메일 표시를 안 센다 — 메일 한 장은 그 수를 안 댄다."""
        pass

    def mail(self, inner: str, unid: str) -> str:
        """메일 표시 — 링크 없이 그 글만."""
        return inner

    def person(self, inner: str, addr: str) -> str:
        """사람 — 이름만."""
        return inner

    def room(self, inner: str, rid: str) -> str:
        """회의실 — 방 이름만."""
        return inner

    def bad_approval(self) -> None:
        """꼴이 틀린 결재 문서 표시를 안 센다 — 메일 한 장은 그 수를 안 댄다."""
        pass

    def approval(self, inner: str, doc: str) -> str:
        """결재 문서 — 이름만(창을 띄우는 단추는 PC 의 보고 창에만 선다)."""
        return inner

    def pill(self, words: str, over: bool) -> str:
        """표지 — 줄마다의 style 속성으로 지은 둥근 표(`over` 면 넘친 표)."""
        return f'<span style="{MS["pill_over" if over else "pill"]}">{html.escape(words, quote=True)}</span>'

    def bold(self, inner: str) -> str:
        """굵게 — <b> 로."""
        return f"<b>{inner}</b>"


def mail_inline(text: str) -> str:
    """줄 안 — 메일의 겉(`MailSkin`)으로. 창과 같은 걸음(`inline_walk`)이 같은 꼴을 읽는다."""
    return inline_walk(text, MailSkin())


def mail_plain(text: str) -> str:
    """평문 짝의 한 줄 — 꼴 표시를 걷은 맨글자(메일 링크는 그 글만)."""
    return " ".join(plain(text).split())


def mail_item(it: Item, html_out: list[str], text_out: list[str]) -> None:
    """줄 하나 — 점 · 칸 · 맡길 일이 딸리면 카드, 아니면 한 줄. 맡길 일은 종류와 사람이 읽는 줄(창의 줄과 같은 글)로 선다 — 어디서 누르나는 그
    절의 머리에 선 한 줄이 댄다(`MAIL_TASK_INTRO`)."""
    tasks, points, facts, no_time = take_card(it)
    if not card_shaped(points, tasks, no_time):
        tail = "".join(f" ({mail_inline(k)}: {mail_inline(v)})" for k, v in facts)
        html_out.append(f'<p style="{MS["row"]}">{mail_inline(it.text)}{tail}</p>')
        text_out.append("- " + mail_plain(it.text) + "".join(f" ({mail_plain(k)}: {mail_plain(v)})" for k, v in facts))
        return
    head, rest = card_head(it.text)
    parts = [f'<p style="{MS["card_title"]}">{mail_inline(head)}</p>']
    text_out.append("- " + mail_plain(head) + (f" — {mail_plain(rest)}" if rest else ""))
    if rest:
        parts.append(f'<p style="{MS["card_when"]}">{mail_inline(rest)}</p>')
    parts += [f'<p style="{MS["point"]}">{mail_inline(p)}</p>' for p in points]
    text_out += [f"  · {mail_plain(p)}" for p in points]
    if facts:
        parts.append(f'<p style="{MS["facts"]}">' + "<br>".join(f"<b>{mail_inline(k)}</b> {mail_inline(v)}" for k, v in facts) + "</p>")
        text_out += [f"  {mail_plain(k)}: {mail_plain(v)}" for k, v in facts]
    for t in tasks:
        what = (f"{t.field}: {t.written} — {MAIL_TASK_BAD}" if t.row.via == VIA_NONE else f"{t.kind} — 「{t.line}」"
                if t.row.via == VIA_TALK else f"{t.kind} — {t.line}")
        parts.append(f'<p style="{MS["put_said" if t.row.via == VIA_NONE else "put"]}">{html.escape(what)}</p>')
        text_out.append(f"  {what}")
    if asks_time(tasks, no_time):
        parts.append(f'<p style="{MS["put_said"]}">{html.escape(NO_TIME_SAID)}</p>')
        text_out.append(f"  {NO_TIME_SAID}")
    html_out.append(f'<div style="{MS["card_appt" if dated_card(tasks, no_time) else "card"]}">' + "".join(parts) + "</div>")


def mail_blocks(blocks: list[Block], html_out: list[str], text_out: list[str]) -> None:
    """덩이를 차례대로 — 문단 · 줄 · 작은 절 · 주의 상자 · 시간줄."""
    for b in blocks:
        if b.kind == "para":
            words = " ".join(b.lines)
            html_out.append(f'<p style="{MS["intro"]}">{mail_inline(words)}</p>')
            text_out.append(mail_plain(words))
        elif b.kind == "sub":
            html_out.append(f'<p style="{MS["h3"]}">{mail_inline(b.lines[0])}</p>')
            text_out.append(f"[{mail_plain(b.lines[0])}]")
        elif b.kind == "list":
            for it in b.lines:
                mail_item(it, html_out, text_out)
        elif b.kind == "quote":
            words = [x for x in b.lines if x.strip()]
            html_out.append(f'<div style="{MS["caution"]}">' + "<br>".join(mail_inline(x) for x in words) + "</div>")
            text_out += [f"> {mail_plain(x)}" for x in words]
        elif b.kind == "clock":
            rows = []
            for line in b.lines:
                mark, desc, note = (DASH.split(line, maxsplit=2) + ["", ""])[:3]
                rows.append(f'<p style="{MS["clock_row"]}"><b style="{MS["clock_t"]}">{mail_inline(mark.strip())}</b> {mail_inline(desc.strip())}'
                            + (f' <span style="{MS["aside"]}">— {mail_inline(note.strip())}</span>' if note.strip() else "") + "</p>")
                text_out.append(" — ".join(mail_plain(x) for x in (mark, desc, note) if x.strip()))
            label = f'<p style="{MS["clock_label"]}">{mail_inline(" ".join(b.label))}</p>' if b.label else ""
            html_out.append(f'<div style="{MS["clock"]}">{label}' + "".join(rows)
                            + "".join(f'<p style="{MS["meta"]}">{mail_inline(a)}</p>' for a in b.after) + "</div>")


def task_section(blocks: list[Block]) -> bool:
    """맡길 일이 든 절인가 — 그 절의 머리에 어디서 맡기나를 한 줄 세운다."""
    return any(take_card(it)[0] for b in blocks for it in (b.lines if b.kind == "list" else ()))


def mail_sheet(text: str, made: dt.datetime, slot: str, slot_day: dt.date | None = None) -> dict:
    """보고 글 한 장 → 메일 한 장 {subject, html, text}. 창과 같은 글을 같은 꼴 읽기(`parse`)로 읽어 같은 사실을 다 싣고, 빈 「끝났다고 하신 것」은
    창처럼 뺀다. 제목은 「[메일 비서] 칸의 날 M/D(요일) 칸의 시각 보고 — 머리말」 — 머리말이 없으면 제목 줄이다. 칸의 날(`slot_day`)이 없으면
    지은 날이다. 끝의 「… 지음」은 늘 지은 때(`made`)다 — 저녁 칸의 보고가 자정 뒤에 지어지면 제목은 그 칸의 날, 지음은 다음 날이다."""
    rep = parse(text)
    head = list(rep.sections[0].blocks)
    lede = " ".join(head.pop(0).lines) if head and head[0].kind == "para" else ""
    on = slot_day or made.date()
    day = f"{on.month}/{on.day}({WEEKDAYS[on.weekday()]})"
    subject = " ".join(f"{MAIL_TAG} {day} {slot} 보고 — {mail_plain(lede or rep.title or '')}".split())
    subject = subject if len(subject) <= SUBJECT_MAX else subject[:SUBJECT_MAX - 1] + "…"
    h = [f'<p style="{MS["eyebrow"]}">메일 비서</p>', f'<h1 style="{MS["h1"]}">{mail_inline(rep.title or "")}</h1>']
    t = [mail_plain(rep.title or "")]
    if lede:
        h.append(f'<p style="{MS["lede"]}">{mail_inline(lede)}</p>')
        t.append(mail_plain(lede))
    meta = MAIL_META.format(slot=slot)
    h.append(f'<p style="{MS["meta"]}">{html.escape(meta)}</p>')
    t.append(meta)
    mail_blocks(head, h, t)
    for sec in rep.sections[1:]:
        if is_empty_done(sec):
            continue
        h.append(f'<h2 style="{MS["h2"]}">{mail_inline(sec.title or "")}</h2>')
        t += ["", f"■ {mail_plain(sec.title or '')}"]
        blocks = sec.blocks
        if task_section(blocks):                     # 머리말(첫 줄 앞의 문단) 뒤에 — 모델이 쓴 머리말은 그대로 두고 어디서 맡기나를 댄다
            lead = next((i for i, b in enumerate(blocks) if b.kind != "para"), len(blocks))
            mail_blocks(blocks[:lead], h, t)
            h.append(f'<p style="{MS["intro"]}">{html.escape(MAIL_TASK_INTRO)}</p>')
            t.append(MAIL_TASK_INTRO)
            blocks = blocks[lead:]
        mail_blocks(blocks, h, t)
    dateline = DATELINE.format(made, WEEKDAYS[made.weekday()], made)
    h.append(f'<p style="{MS["foot"]}">{html.escape(MAIL_FOOT)}<br>{html.escape(dateline)}</p>')
    t += ["", MAIL_FOOT, dateline]
    page = ('<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(subject)}</title></head><body style="{MS["body"]}"><div style="{MS["sheet"]}">' + "".join(h) + "</div></body></html>")
    return {"subject": subject, "html": page, "text": "\n".join(t) + "\n"}
