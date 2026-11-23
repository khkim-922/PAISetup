"""일정에 넣을 값 한 칸을 읽는다 — 칸의 값 → `Put`(`put_of`) · 두 시각을 사람이 읽는 때로(`span_words`) · 「시각: 메일에 없음」 칸 떼기(`no_time_of`).
파일 · 망에 닿지 않는다. 꼴의 원본은 스킬 폴더의 `lane.md` 「보고 글의 꼴」이다.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_const.py · brief_inline.py — `-I` 로 돌아도 싣는다
from brief_const import SEOUL, WEEKDAYS  # noqa: E402
from brief_inline import plain  # noqa: E402

# 일정에 없는 약속 — 「일정 넣기」 · 옛 「넣을 일정」의 값은 일정 손 preview 답의 값을 손대지 않고 옮긴 것이고, 열쇠는 창을 지을 때 스크립트가
# 그 값의 미리 보기에서 받아 붙인다(`finish.py`):
#   <start> | <end> | <title> | 곳 <place> | <visibility> [| 열쇠 <key>]   (곳은 없으면 뺀다)
# 「 | 」는 맡길 일 한 칸의 값을 가르는 자이기도 하다(`brief_tasks.task_of`)
NO_TIME_FIELD, NO_TIME_VALUE = "시각", "메일에 없음"   # 날은 있고 시각이 없는 모임 — 단추 대신 대화로 가는 말을 단다
PUT_SPLIT, PLACE_MARK, KEY_MARK = " | ", "곳 ", "열쇠 "
VISIBILITY = {"public": False, "공개": False, "private": True, "비공개": True}   # preview 의 visibility(앞) · 사람 말(뒤) → 비공개인가
PUT_KEY = re.compile(r"^[0-9a-f]{8,64}$")      # 일정 손의 key(판의 해시 · 16진) — 길이는 그 손이 정한다
# 일정 손의 시각 꼴(서울 벽시계) — 글로 거르는 자(두 자리 · 시의 범위)와 읽는 꼴이 한 짝이다. 거른 것만 읽는다(`put_moment`)
PUT_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2} (?:[01]\d|2[0-3]):[0-5]\d$")
PUT_FORMAT = "%Y-%m-%d %H:%M"                  # 창의 스크립트도 이 꼴을 읽는다(`assets/report.js` 의 `startOf`)
VIS_WORDS = {False: "공개 — 다른 분이 제목을 볼 수 있습니다", True: "비공개 — 다른 분께는 바쁜 때로만 보입니다"}


@dataclass(frozen=True)
class Put:
    """카드 하나가 넣을 일정 — 창이 사람에게 보이는 글과 거두는 손이 일정 손에 주는 값이 다 이것에서 나온다."""
    start: str
    end: str
    title: str
    place: str
    private: bool
    key: str

    def words(self) -> str:
        """사람이 읽는 「무엇을 넣나」 — 날 · 요일 · 시각 · 제목 · 곳. 공개 범위는 따로(`VIS_WORDS`)."""
        return " · ".join(filter(None, (span_words(self.start, self.end), self.title, self.place)))


def span_words(start: str, end: str) -> str:
    """「11월 26일(목) 14:00–16:00」 — 서울 벽시계 두 시각(`PUT_STAMP` 꼴)을 사람이 읽는 때로. 날을 넘기면 끝의 날도 댄다."""
    a, b = (put_moment(s) for s in (start, end))
    day = f"{a.month}월 {a.day}일({WEEKDAYS[a.weekday()]})"
    return (f"{day} {a:%H:%M}–{b:%H:%M}" if a.date() == b.date()
            else f"{day} {a:%H:%M} – {b.month}월 {b.day}일({WEEKDAYS[b.weekday()]}) {b:%H:%M}")


def put_moment(stamp: str) -> dt.datetime:
    """일정 손의 시각(`PUT_STAMP` 꼴 — 거른 글만 준다) → 서울 시간대가 붙은 때. 꼴이 아니면 ValueError."""
    return dt.datetime.strptime(stamp, PUT_FORMAT).replace(tzinfo=SEOUL)


def put_of(value: str) -> Put | None:
    """「일정 넣기」 칸의 값 → Put. 꼴이 아니면 None — 시각 둘 · 제목 · (곳) · 공개 범위 · (열쇠). 제목에 「 | 」가 들어도 끝에서부터 읽는다.
    열쇠는 창을 지을 때 일정 손의 미리 보기에서 받아 붙인다(`finish.py`) — 모델이 쓴 글에는 없고, 붙이기 전이나 못 받았으면 빈 글이다."""
    parts = [p.strip() for p in value.strip().strip("`").split(PUT_SPLIT)]
    key = parts.pop()[len(KEY_MARK):].strip() if parts and parts[-1].startswith(KEY_MARK) else ""
    if len(parts) < 4 or parts[-1] not in VISIBILITY or (key and not PUT_KEY.match(key)):
        return None
    start, end, middle = parts[0], parts[1], parts[2:-1]
    place = middle.pop()[len(PLACE_MARK):].strip() if len(middle) > 1 and middle[-1].startswith(PLACE_MARK) else ""
    title = PUT_SPLIT.join(middle).strip()
    if not (PUT_STAMP.match(start) and PUT_STAMP.match(end) and start < end and title):
        return None
    return Put(start, end, title, place, VISIBILITY[parts[-1]], key)


def no_time_of(facts: list[tuple[str, str]]) -> tuple[bool, list[tuple[str, str]]]:
    """끝의 칸에서 「시각: 메일에 없음」을 떼어 낸다 — (시각 없는 모임인가, 남은 칸)."""
    hit = [f for f in facts if f[0] == NO_TIME_FIELD and plain(f[1]).strip().startswith(NO_TIME_VALUE)]
    return bool(hit), [f for f in facts if f not in hit]
