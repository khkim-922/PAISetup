"""보고 맞춤 파일 — 사용자가 보고 창이나 대화에서 「이런 건 안 올려도 됨」 · 「내일 다시」 하신 것을 사람이 읽는 글로 든다. 그 파일의 꼴 ·
읽기 · 쓰기 · 줄 고치기. 파일은 사용자 폴더의 `daily-brief-prefs.md` 하나다(업무 파일 곁 · 쓰는 손은 대화의 명령 `prefs.py` · 보고 창 표시를
거두는 `ticks.py` · 옛 꼴을 옮기는 `finish.py`). 무엇을 지키고 왜 그런가는 `references/DESIGN.md` 「보고 맞춤」이 든다.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import pathlib
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 store.py · brief_sections.py — `-I` 로 돌아도 싣는다
import store  # noqa: E402
from brief_inline import UNID_HEX  # noqa: E402
from brief_sections import NONE_ROW  # noqa: E402
from old_forms import declined_old  # noqa: E402

FILE_NAME = "daily-brief-prefs.md"
TITLE = "# 일일 보고 — 사용자께 맞춘 것"
INTRO = "보고 창에서 누르시거나 대화에서 말씀하신 것을 보고가 날마다 읽습니다. 줄을 지우시면 그대로 따릅니다."
QUIET = "올리지 않을 것"           # 사용자가 올리지 말라고 하신 일의 보기 — 보고는 같은 갈래의 일을 올리지 않는다
LATER = "내일 다시 볼 것"          # 「내일 다시」 하신 일 — 돌아오는 날의 첫 보고에 다시 선다
BACK = "다시 올린 것"              # 돌아오는 날이 와 보고에 다시 댄 일 — 그 뒤에 보고 글이 지어지면 걷는다(그 전에는 다시 거둬도 또 댄다)
DECLINED = "걸지 않기로 하신 것"   # 처음 보고 때 여쭌 메일함 스캔 · 아침 보고를 마다하신 것 — 있으면 다시 여쭙지 않는다
EMPTY = NONE_ROW
MAIL_LINK = re.compile(rf"\(mail:({UNID_HEX})\)")   # 줄에 단 메일 링크 — 그 번호가 줄의 열쇠다(`key` · `unid_of`)
DUE = re.compile(r"`(\d{4}-\d{2}-\d{2})`")
BACK_MARK = " · `{at}` 보고에 다시 올렸습니다"
BACK_AT = re.compile(r" · `(\d{4}-\d{2}-\d{2} \d{2}:\d{2})` 보고에 다시 올렸습니다$")
STAMP = "%Y-%m-%d %H:%M"           # 다시 올린 때 — 이 PC 의 시각(보고 글의 이름과 같은 바탕이라 둘을 견준다)
TITLE_MAX = 80
NUMBERISH = re.compile(rf"\(?mail:[^\s)]*\)?|\b{UNID_HEX}\b")   # 이름 속 메일 번호 꼴 — 다음 보고가 그 번호를 이 일의 메일로 읽는다

QUIET_FROM_WINDOW = "- 「{title}」 같은 일 — {when} 보고 창에서 「이런 건 안 올려도 됨」 하셨습니다 [보기 메일](mail:{unid})"
QUIET_FROM_TALK = "- {words} — {when} 대화에서 말씀하셨습니다"
LATER_LINE = "- {title} — `{due}` 첫 보고에 다시 올립니다 · {when} {where} 「내일 다시」 하셨습니다 [근거 메일](mail:{unid})"
DECLINED_LINE = "- 메일함 스캔 · 아침 보고 — `{day}` {where} 걸지 않기로 하셨습니다"
LEGACY_WHERE = "지난 보고 글에 남은 말씀대로"   # 옛 꼴의 말씀(`old_forms.declined_old`)을 읽어 들인 줄이 대는 자리


@dataclass
class Prefs:
    """보고 맞춤 파일 한 장 — 올리지 않을 것 · 내일 다시 볼 것 · 다시 올린 것 · 걸지 않기로 하신 것과 읽은 꼴."""
    quiet: list[str] = field(default_factory=list)
    later: list[str] = field(default_factory=list)
    back: list[str] = field(default_factory=list)       # 다시 올린 줄 — 「내일 다시」 줄 끝에 다시 올린 때(`BACK_MARK`)가 붙는다
    declined: list[str] = field(default_factory=list)   # 걸지 않기로 하신 것 — 한 줄(`DECLINED_LINE`)
    unread: bool = False            # 있는데 못 읽었다 — 보이는 쪽이 「없습니다」 대신 그렇다고 말한다(쓰는 쪽은 strict 로 읽어 멈춘다)
    legacy: bool = False            # 걸지 않기로 하신 것을 지난 보고 글의 옛 꼴에서 읽어 들였다 — 아직 이 파일에 안 적혔다


def path_of(folder: pathlib.Path) -> pathlib.Path:
    """사용자 폴더의 보고 맞춤 파일 자리."""
    return folder / FILE_NAME


def lines_of(text: str, name: str) -> list[str]:
    """절 `name`(「## 」 머리) 아래 「- 」 줄 — 「없음」은 뺀다."""
    out, inside = [], False
    for row in text.splitlines():
        if row.startswith("## "):
            inside = row[3:].strip().startswith(name)
            continue
        if inside and row.startswith("- ") and row.strip() != EMPTY:
            out.append(row.rstrip())
    return out


Unreadable = store.Unreadable                  # 맞춤 파일이 있는데 못 읽었다 — 빈 것으로 읽고 그 위에 쓰면 사람이 감추고 미룬 일이 다 사라진다


def read(folder: pathlib.Path, strict: bool = False) -> Prefs:
    """맞춤 파일 — 없으면 빈 것. 있는데 못 읽으면 `strict`(읽은 뒤 쓰는 자리)는 `Unreadable`, 보이기만 하는 자리는 빈 것에 못 읽었다는 표
    (`unread`)를 단다 — 보이는 쪽이 「없습니다」 대신 못 읽었다고 말한다. 그 절이 없는 옛 파일이면 옛 꼴의 말씀을 읽어 들인다(`with_legacy`)."""
    text = file_text(folder, strict)
    return Prefs(unread=True) if text is None else with_legacy(prefs_of(text), text, folder)


def file_text(folder: pathlib.Path, strict: bool) -> str | None:
    """맞춤 파일의 글 — 없으면 빈 글. 있는데 못 읽으면 `strict` 는 `Unreadable`, 아니면 None."""
    try:
        raw = store.read_bytes(path_of(folder))
    except Unreadable:
        if strict:
            raise
        return None
    return raw.decode("utf-8-sig", errors="replace") if raw is not None else ""


def prefs_of(text: str) -> Prefs:
    """맞춤 파일의 글 → 네 절의 줄. 사람이 손으로 고친 파일도 「- 」 줄만 읽는다."""
    return Prefs(lines_of(text, QUIET), lines_of(text, LATER), lines_of(text, BACK), lines_of(text, DECLINED))


def with_legacy(prefs: Prefs, text: str, folder: pathlib.Path) -> Prefs:
    """그 절(「걸지 않기로 하신 것」)을 쓰기 전의 파일이고 가장 늦은 보고 글이 옛 꼴로 그 말씀을 들었으면 한 줄로 읽어 들이고 아직 안 적혔다는
    표(`legacy`)를 단다 — 창을 짓는 손의 마무리가 맞춤 파일에 옮긴다."""
    if f"## {DECLINED}" not in text and declined_old(folder):
        prefs.declined, prefs.legacy = [DECLINED_LINE.format(day=dt.date.today().isoformat(), where=LEGACY_WHERE)], True
    return prefs


def write(folder: pathlib.Path, prefs: Prefs) -> None:
    """맞춤 파일을 곁의 임시 파일에 다 쓴 뒤 바꿔 끼운다 — 다시 올린 것은 줄이 있을 때만 선다. 「걸지 않기로 하신 것」은 늘 선다(줄이 없으면
    「없음」) — 그 절이 있는 파일은 옛 꼴의 말씀을 다시 읽어 들이지 않는다(사용자가 줄을 지우시면 그대로 따른다). 쓰지 못하면 OSError."""
    body = [TITLE, "", INTRO, "", f"## {QUIET}", *(prefs.quiet or [EMPTY]), "", f"## {LATER}", *(prefs.later or [EMPTY]), ""]
    body += [f"## {BACK}", *prefs.back, ""] if prefs.back else []
    body += [f"## {DECLINED}", *(prefs.declined or [EMPTY]), ""]
    store.replace(path_of(folder), "\n".join(body).encode("utf-8"))


def key(line: str) -> str:
    """줄의 열쇠 — 메일 번호(`unid_of`)가 있으면 그 번호, 없으면 글에서 낸 짧은 지문(「w」 + 10자리). 보고 창의 「다시 올리기」가 이 열쇠로 그 줄을 짚는다."""
    return unid_of(line) or "w" + hashlib.sha1(line.encode("utf-8")).hexdigest()[:10]


def unid_of(line: str) -> str | None:
    """줄에 단 첫 메일 링크(`MAIL_LINK`)의 번호(대문자) — 없으면 None."""
    m = MAIL_LINK.search(line)
    return m.group(1).upper() if m else None


def due_of(line: str) -> dt.date | None:
    """「내일 다시」 줄이 돌아오는 날 — 꼴이 아니면 None(그런 줄은 바로 돌아온 것으로 본다)."""
    m = DUE.search(line)
    try:
        return dt.date.fromisoformat(m.group(1)) if m else None
    except ValueError:
        return None


def clean(words: str) -> str:
    """줄에 들일 글 — 줄바꿈 · 꼴 표시 · 메일 번호 꼴을 걷고 줄인다. 창의 칸이나 대화에서 온 글이라 절 머리 · 링크로 서지 못하게 한다."""
    words = " ".join(str(words or "").split())
    words = re.sub(r"[\[\]{}`*#<>]", "", NUMBERISH.sub("", words)).strip(" -—")
    return (words[:TITLE_MAX - 1].rstrip() + "…") if len(words) > TITLE_MAX else words


def put_quiet(prefs: Prefs, line: str) -> None:
    """「올리지 않을 것」에 한 줄 — 같은 열쇠의 줄은 바꾼다. 그 메일이 「내일 다시」에 있으면 걷는다(뒤에 누르신 것이 이긴다)."""
    k, u = key(line), unid_of(line)
    prefs.quiet = [x for x in prefs.quiet if key(x) != k] + [line]
    prefs.later = [x for x in prefs.later if unid_of(x) != u or u is None]
    prefs.back = [x for x in prefs.back if unid_of(x) != u or u is None]


def put_later(prefs: Prefs, line: str) -> None:
    """「내일 다시 볼 것」에 한 줄 — 같은 메일의 줄(다시 올린 것도)은 바꾸고, 그 메일의 「올리지 않을 것」 줄은 걷는다."""
    u = unid_of(line)
    prefs.later = [x for x in prefs.later if unid_of(x) != u] + [line]
    prefs.back = [x for x in prefs.back if unid_of(x) != u]
    prefs.quiet = [x for x in prefs.quiet if unid_of(x) != u]


def drop_unid(prefs: Prefs, unid: str) -> bool:
    """그 메일의 줄을 세 절(올리지 않을 것 · 내일 다시 볼 것 · 다시 올린 것)에서 다 걷는다 — 걷은 것이 있으면 True."""
    before = len(prefs.quiet) + len(prefs.later) + len(prefs.back)
    prefs.quiet = [x for x in prefs.quiet if unid_of(x) != unid]
    prefs.later = [x for x in prefs.later if unid_of(x) != unid]
    prefs.back = [x for x in prefs.back if unid_of(x) != unid]
    return len(prefs.quiet) + len(prefs.later) + len(prefs.back) != before


def forget(prefs: Prefs, k: str) -> str | None:
    """「올리지 않을 것」에서 열쇠 `k` 의 줄을 걷는다 — 걷은 줄이나 None."""
    for line in prefs.quiet:
        if key(line) == k:
            prefs.quiet.remove(line)
            return line
    return None


def back_at(line: str) -> dt.datetime | None:
    """다시 올린 줄의 그 때(이 PC 의 시각) — 꼴이 아니면 None."""
    m = BACK_AT.search(line)
    try:
        return dt.datetime.strptime(m.group(1), STAMP) if m else None
    except ValueError:
        return None


def take_due(prefs: Prefs, now: dt.datetime, made: list[dt.datetime]) -> tuple[list[str], list[str]]:
    """(돌아온 줄, 아직 미룬 줄) — 돌아오는 날이 오늘이거나 지난 줄(날이 꼴이 아닌 줄도 — 미룬 채 잊히지 않게)은 「다시 올린 것」으로 옮기고
    그 때를 붙인다. 다시 올린 줄은 그 때나 그 뒤에 지은 보고 글(`made` — 보고 글 이름의 때 · 분까지)이 있으면 그 보고가 실었으니 걷고, 없으면 또
    돌아온 줄로 낸다 — 거두기만 하고 보고가 안 지어진 판(세션이 끊겼다 · 맡긴 쪽이 멈췄다)에도 그 일이 사라지지 않는다. 돌아온 줄은 붙인
    때를 뗀 글이다."""
    stamp = now.strftime(STAMP)
    kept = [x if back_at(x) else BACK_AT.sub("", x) + BACK_MARK.format(at=stamp)   # 때가 지워진 줄(손으로 고친 파일)은 지금 때로
            for x in prefs.back if not (back_at(x) and any(m >= back_at(x) for m in made))]
    wait = []
    for line in prefs.later:
        due = due_of(line)
        if due is None or due <= now.date():
            kept.append(line + BACK_MARK.format(at=stamp))
        else:
            wait.append(line)
    prefs.back, prefs.later = kept, wait
    return [BACK_AT.sub("", x) for x in kept], wait
