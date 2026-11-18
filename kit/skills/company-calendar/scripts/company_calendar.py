"""회사 일정 스킬의 얇은 명령 — 곁의 일정 손(``agenda.py``)을 불러 보기 · 넣기 · 지우기를 한다.

부르는 꼴::

    python -X utf8 -I company_calendar.py --help      # 지도 — 출발 × 바꿀 것 × 끝 · 읽기. 아래 표(STARTS · CHANGES · ENDS · READS)에서 짓는다
    python -X utf8 -I company_calendar.py show [오늘|내일|모레|YYYY-MM-DD] [끝 날] [--shared] [--who 이름 …] [--free 분 [--hours HH:MM-HH:MM]]
    python -X utf8 -I company_calendar.py calendars
    python -X utf8 -I company_calendar.py preview --title T --start "YYYY-MM-DD HH:MM" --end "…" [--note N]   # 안 바꾼다 · key 를 낸다
    python -X utf8 -I company_calendar.py add     …preview 와 같은 값… --confirm <preview 의 key>               # ⚠ 바꾼다
    python -X utf8 -I company_calendar.py delete  --handle <show 의 handle>                                    # ⚠ 바꾼다
    python -X utf8 -I company_calendar.py remember "<일정 화면 주소창의 주소>"                                # 주소를 재 보고 남긴다

    공통 — ``--url``(없으면 ``CALENDAR_URL`` → 남긴 주소 → 잰 기본 ``agenda.DEFAULT_APP_URL``). 시각은 다 서울 벽시계 ``YYYY-MM-DD HH:MM``
    이고, 답의 ``start`` · ``end`` 도 그 꼴이라 그대로 다음 명령(이 스킬 · 회의실 예약)에 준다.

한 번 부름이 일정 한 건을 한 번 다룬다 — 출발 하나(새 일정 · show 가 보인 내 일정 한 건)에 바꿀 것을 아무 조합으로 주고 끝 하나로 맺는다.
없는 손가락을 주면 그 일을 어디서 하는지 대며 종료 2 로 멈춘다. ⚠ 넣기 · 지우기는 사람이 그 한 건을 확인한 뒤에만 부른다 — 열쇠가 그
확인을 손 안에서 지킨다: ``add`` 는 preview 를 다시 지어 그 ``key``(보인 값 · 겹침 · 이미 있나)가 다르면 안 넣고, ``delete`` 의
``handle`` 은 보인 줄의 지문이라 그 줄이 바뀌었으면 안 지운다.

세션 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 가 쥔다: 보기는 있는 세션 파일로 먼저 돌고, 넣기 · 지우기(``MUTATING``)는
늘 쓰는 사람의 Edge 에서 받는다(까닭은 그 함수의 머리말). 판단(무엇을 넣을까 · 지워도 되나)은 여기 없다.

내는 것 — 표준 출력에 JSON 하나. 종료 값: 0 됐다 · 1 도구 고장(그대로 알린다) · 2 인자가 틀렸다(없는 손가락 · 빠진 값 — ``message`` 가
다음 걸음을 든다) · 3 세션이 없다 · 끊겼다(스킬 ep-login) · 8 일정 앱 주소가 틀렸거나 잰 기본 주소로 내 일정함이 안 읽힌다. 0 이 아니면
``message`` 가 까닭과 「다음: …」 을 든다. 일정 줄 — ``day`` · ``weekday`` · ``when`` · ``start`` · ``end`` · ``handle``(지우기의 열쇠 ·
사람에게 안 보인다) · ``pending``(참석 답을 안 한 받은 초대) · ``keep`` 이 차면 지우지 않는 줄이고 ``keep_word`` 가 사람에게 할 말이다 ·
기본 밖 내 일정함 · 공유 줄은 ``calendar``(어느 일정함) · 공유 줄은 ``private``(일정함을 가진 사람이 비공개로 든 것). 시각을 못 읽어
뺀 줄이 있으면 show 가 ``unread_rows``(일정함 · 줄 수)를 단다. ``--free`` 를 주면 show 가 ``free`` 를 더 낸다 — 읽은 일정함 전부가
그 분 이상 함께 비는 때(``slots``)와 시각을 짐작해 센 줄(``assumed``) · 사람에게 할 말(``word``). 어느 줄을 어떻게 세나는
``free_of``. preview 는 ``state``(ready · already) · ``key`` 를, 넣기 · 지우기는 ``state`` 와 사람에게 할 말 · 다음 걸음이 든
``state_word`` 를 낸다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
SAVED_URL = "~/.company-calendar.json"   # 남긴 일정 앱 주소 — 저장소 밖 · 비밀이 없다(사번 · 쿠키가 안 든다)
INDENT = 1                               # 답(JSON)을 찍는 들여쓰기 — 답의 크기도 이 꼴로 센다
KEY_LENGTH = 16                          # 열쇠(보인 판의 해시)의 길이 — 16진 글자
STAMP_HELP = "YYYY-MM-DD HH:MM(서울)"
# 사람이 회사 일정 화면을 여는 길 — 화면 주소는 사람마다 서버 · 번호가 달라 길로 댄다(references/SOURCES.md 「사내 일정 앱에서 잰 것」)
MENU = "Edge 에서 메일을 열고 위의 일정 메뉴"
SCREEN = f"회사 일정 화면({MENU}로 연다)"
NEXT_URL = f"다음: 사람에게 「{MENU}를 눌러, 열린 일정 화면의 주소창 주소를 그대로 붙여 주세요」 하고, 받은 주소로 remember 를 부른다"
UNMEASURED = "회사에서 안 쟀다"
# 모두 비는 때(show --free) — 회사의 근무 시간은 안 쟀다. 사람이 때를 말했으면(「오후에」 · 「3시에 되나」) --hours 로 그 구간을 준다
WORK_HOURS = "09:00-18:00"
HOURS_FORM = re.compile(r"^\s*(\d{1,2}:\d{2})\s*[-~–]\s*(\d{1,2}:\d{2})\s*$")
WEEKEND = (5, 6)                          # date.weekday() 의 토 · 일 — 모두 비는 때를 안 찾는 날
SLOT_STEP_MINUTES = 10                    # 오늘의 비는 때는 지금 뒤 이 분 단위의 첫 눈금부터 — 잘린 분 · 초 때문에 회의실 손이 「지난 시각」으로 막지 않게
MY_BOOK = "내 기본 일정함"                 # 기본 일정함을 부르는 이름 — 일정함 목록에 그 줄의 이름이 안 온다


# ── 손가락의 표 — 출발 × 바꿀 것 × 끝. 손가락을 더하거나 빼는 일은 이 표의 줄과 그 일을 하는 손 하나다 ─────────────────
@dataclass(frozen=True)
class Start:
    """출발 하나 — 일정 앱의 화면 하나."""
    word: str        # 사람 말
    screen: str      # 그 화면이 무엇인가 — --help 의 지도
    takes: str = ""  # 그 출발을 고르는 인자 — 빈 글자면 아무것도 안 주면 이 출발이다

    @property
    def dest(self) -> str:
        return self.takes.lstrip("-").replace("-", "_")


@dataclass(frozen=True)
class Change:
    """바꿀 것 하나 — 손가락 하나."""
    flags: tuple             # ((인자, argparse 의 덧값), …)
    starts: tuple            # 받는 출발
    word: str                # 사람 말 — 「 — 」 앞이 이름이다
    elsewhere: str = ""      # 받지 않는 출발에서 그 일을 어디서 하나 — 명령이 멈추며 댄다
    need: tuple = ()         # 이 손가락이 꼭 드는 출발


@dataclass(frozen=True)
class NotYet:
    """아직 없는 손가락 하나 — 회사에서 안 잰 화면 동작이라 짓지 않았다. 인자가 있으면 받아 두었다가 세션 전에 멈추며 어디서 하나를 댄다."""
    word: str                # 무엇을 못 하나
    where: str               # 사람이 어디서 하나
    flags: tuple = ()        # ((인자, argparse 의 덧값), …) — 모델이 짐작해 줄 만한 인자. 비면 --help 의 지도에만 선다


@dataclass(frozen=True)
class End:
    """끝 하나 — 누르는 단추. 다 회사 일정을 바꾼다."""
    word: str
    starts: tuple
    key: str                 # 무엇이 사람의 확인을 지키나 — --help 의 지도
    confirm: bool            # --confirm 으로 preview 의 key 를 받나(아니면 출발의 인자가 곧 열쇠다)


STARTS = {
    "new": Start("새 일정", "빠른 등록 화면 — 내 기본 일정함에 한 건. 참석자 · 참조 칸은 늘 비워 누구에게도 알림이 안 간다"),
    "event": Start("내 일정 한 건", "show 가 보인 일정 줄 — 그 줄의 handle", "--handle"),
}
EDIT_LATER = (f"일정 고치기 · 옮기기는 회사에서 아직 안 잰 손가락이다 — 사람에게 {SCREEN}에서 고치시라 권한다(손수 든 단건이면 "
              "지우고 새로 넣는 길도 있다 — 확인을 두 번 받는다)")
CHANGES = {
    "title": Change((("--title", {}),), ("new",), "제목 — 60 자에서 자르고 줄바꿈 · 안 보이는 글자를 걷는다", EDIT_LATER, ("new",)),
    "start": Change((("--start", {"help": STAMP_HELP}),), ("new",), "시작", EDIT_LATER, ("new",)),
    "end": Change((("--end", {"help": STAMP_HELP}),), ("new",), "끝 — 사람이 끝을 안 말했으면 지어 넣지 말고 묻는다", EDIT_LATER, ("new",)),
    "note": Change((("--note", {}),), ("new",), "설명 — 80 자에서 자른다", EDIT_LATER),
}
# 아직 없는 손가락 — 회사에서 그 화면 동작을 재 오면 이 줄을 걷고 CHANGES 한 줄과 register 의 그 칸을 더한다
ON_SCREEN = f"사람에게 {SCREEN}에서 하시라 권한다"
NOT_YET = {
    "all_day": NotYet("하루 종일로 넣기", f"등록 화면의 하루 종일 칸을 회사에서 아직 안 쟀다. {ON_SCREEN} — 시각을 정해 넣을 것이면 --all-day 없이 부른다",
                      (("--all-day", {"action": "store_true"}),)),
    "private": NotYet("비공개로 넣기", f"비공개를 고른 판의 값을 회사에서 아직 안 쟀다. {ON_SCREEN} — 여기서 넣으면 공개로 들어가 다른 분이 제목을 본다",
                      (("--private", {"action": "store_true"}),)),
    "repeat": NotYet("반복 일정 넣기", f"반복 칸을 회사에서 아직 안 쟀다. {ON_SCREEN} — 한 번만 넣을 것이면 --repeat 없이 부른다",
                     (("--repeat", {"metavar": "주기"}),)),
    "invite": NotYet("참석자 부르기", "이 손은 참석자 칸을 늘 비워 누구에게도 알림이 안 간다. 사람들과 만나는 회의는 스킬 company-meeting-room 으로 "
                     f"회의실과 함께 잡는다(참석자에게 안내가 간다). 회의실 없이 초대만 보낼 것이면 {ON_SCREEN}",
                     (("--to", {"nargs": "*", "metavar": "메일"}),)),
    "shared": NotYet("공유받은 일정함에 넣기 · 지우기", f"공유받은 일정함은 읽기만 한다. {ON_SCREEN}", (("--who", {"action": "append", "metavar": "이름"}),)),
    "reply": NotYet("참석 답(수락 · 거절)", f"초대 메일이나 {SCREEN}에서 사람이 한다"),
    "detail": NotYet("일정 한 건의 장소 · 참석자 · 설명 읽기", f"일정 줄에 그 칸이 안 온다. {ON_SCREEN}(그 일정을 열어 본다)"),
}
ENDS = {
    "add": End("넣기", ("new",), "--confirm <preview 의 key> — 보인 값(제목 · 날 · 시각 · 설명 · 공개 범위)과 내 일정함 전부의 겹침 · "
               "이미 있나. 다시 지은 판이 다르면 안 넣는다", True),
    "delete": End("지우기", ("event",), "--handle 이 곧 열쇠 — 보인 줄의 지문(제목 · 시작 · 끝)이라 그 줄이 바뀌었으면 안 지운다. "
                  "손수 든 단건만 지운다(keep 이 빈 줄)", False),
}
READS = {
    "show": "일정 — 날 하나나 구간(기본 오늘 · 내일). 내 일정함(기본 · Teams)은 늘 들고, --who 이름(여럿)은 그 공유 일정함을 곁에, "
            f"--shared 는 공유 일정함 전부를 곁에. --free 분 은 읽은 일정함 전부가 그 분 이상 함께 비는 때(평일 · 기본 {WORK_HOURS} · "
            "--hours 로 구간을 준다 — 사람이 고른 한 때가 되나도 그 구간을 주어 본다)",
    "calendars": "공유받은 일정함 목록 — 누가 있나는 사람마다 달라 --who 의 이름을 여기서 본다",
}
MUTATING = tuple(ENDS)                   # 회사 일정을 바꾼다 — 세션 손부터 받아 한 번만 돈다

# 지우지 않는 줄 — 사람에게 할 말. 까닭은 agenda.Event.keep_reason 이 가른다
KEEP_WORDS = {
    "invite": "받은 회의 초대입니다 — 지우면 곧 참석 답이 됩니다. 참석 답은 초대 메일이나 회사 일정 화면에서 해 주세요",
    "meeting": "회의로 든 일정입니다 — 지우면 참석하실 분께 알림이 갈 수 있어 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "repeat": "반복 일정입니다 — 지우기가 그날 하나만 걷는지 아직 확인하지 않아 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "all_day": "하루 종일 일정입니다 — 지우기를 아직 확인하지 않아 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "locked": "고칠 수 있는 일정으로 읽히지 않았습니다 — 일정 앱이 막은 것인지 그 표시를 못 알아본 것인지 가리지 못해 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "shared": "다른 일정함(공유받은 것 · Teams)의 일정입니다 — 여기서는 읽기만 합니다",
}
# 넣기 · 지우기의 끝 — 낱말 하나가 뜻 하나다(형제 스킬 company-meeting-room 의 같은 낱말과도 같은 뜻)
STATE_WORDS = {
    "added": "넣었습니다(다시 읽어 확인했습니다). 다음: 이 줄의 handle 을 들고 있다가 「방금 것 지워 줘」 에 delete --handle 로 쓴다",
    "already": "같은 일정(제목 · 시작 · 끝)이 이미 있어 넣지 않았습니다",
    "moved": "보여 드린 뒤 달라진 것이 있어 하지 않았습니다. 다음: 답의 preview · event(지금 판)를 보이고 다시 묻는다 — 답에 없으면 "
             "preview · show 로 다시 읽어 보인다",
    "deleted": "지웠습니다(다시 읽어 사라진 것을 확인했습니다)",
    "gone": "그날 일정에 없습니다 — 이미 지워졌거나 다른 날로 옮겨졌습니다",
    "refused": "여기서는 하지 않습니다 — 답의 reason 에 맞는 말을 그대로 전한다",
    "unsure": "됐는지 확인하지 못했습니다. 다음: 다시 부르지 말고 show 로 그날을 읽어 보인다",
}
# 손(agenda)의 끝 낱말 → 이 명령의 낱말 — 손의 clashed(확인 뒤 새 겹침) · changed(보인 뒤 바뀐 줄)는 다 「보인 판과 다르다」다
ADDED_STATE = {"added": "added", "already": "already", "clashed": "moved", "unsure": "unsure"}
REMOVED_STATE = {"deleted": "deleted", "gone": "gone", "changed": "moved", "unsure": "unsure"}


if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    from ep_command import DAY_COUNT, DAY_WORDS, EXIT_ARGS, EXIT_URL, OUT_BYTES, WEEKDAYS, Stop, day_of, gaps_of, load, size
except ImportError:                             # 형제 스킬 ep-login 이 곁에 없다 — 답의 꼴(JSON 하나 · 종료 1)은 지킨다
    print(json.dumps({"error": "tool", "message": f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"}, ensure_ascii=False))
    sys.exit(1)


# ── 표에서 짓는 것 — 지도 · 인자 거르기 ────────────────────────────────────────────────────────────
def finger_map() -> str:
    """--help 의 지도 — 표 넷에서 짓는다."""
    names = list(STARTS)
    lines = ["지도 — 출발 하나 × 바꿀 것 아무 조합 × 끝 하나. 한 번 부름이 일정 한 건을 한 번 다룬다", "", "출발"]
    lines += [f"  {k:<7} {s.takes + ' <…>' if s.takes else '(인자 없음)':<14} {s.word} — {s.screen}" for k, s in STARTS.items()]
    lines += ["", "바꿀 것 (● 꼭 든다 · ○ 받는다 · — 없다)"]
    elsewhere: dict[str, list[str]] = {}
    for c in CHANGES.values():
        marks = " ".join(f"{k}{'●' if k in c.need else '○' if k in c.starts else '—'}" for k in names)
        lines.append(f"  {' · '.join(f for f, _ in c.flags):<10} {marks}   {c.word}")
        if c.elsewhere:
            elsewhere.setdefault(c.elsewhere, []).append(c.flags[0][0])
    lines += [f"  — 의 자리({' · '.join(flags)}): {text}" for text, flags in elsewhere.items()]
    lines += ["", "끝 (⚠ 회사 일정을 바꾼다 — 사람이 그 한 건을 보고 「네」 한 뒤에만)"]
    lines += [f"  {k:<7} 출발 {' · '.join(e.starts):<6} {e.word} — 열쇠: {e.key}" for k, e in ENDS.items()]
    lines += ["", "읽기"] + [f"  {k:<10} {w}" for k, w in READS.items()]
    lines += ["", "아직 없는 손가락 (인자를 주면 세션 전에 사람이 어디서 하나를 대며 종료 2 로 멈춘다)"]
    lines += [f"  {' · '.join(f for f, _ in n.flags):<10} {n.word} — {n.where}" for n in NOT_YET.values()]
    return "\n".join(lines)


def dest(flag: str) -> str:
    """인자의 argparse 이름 — ``--all-day`` → ``all_day``."""
    return flag.lstrip("-").replace("-", "_")


def given(args, change) -> bool:
    return any(getattr(args, dest(f), None) is not None for f, _ in change.flags)


def fingers(args) -> str:
    """부른 명령의 출발을 고르고 표에 대 본다 — 아직 없는 손가락 · 출발에 없는 끝 · 손가락, 빠진 값은 그 일을 어디서 하는지 대며
    Stop(인자). 출발을 낸다."""
    for n in NOT_YET.values():
        if given(args, n):
            raise Stop(EXIT_ARGS, "args", f"「{n.word}」 손가락은 아직 없다. 다음: {n.where}")
    start = next((k for k, s in STARTS.items() if s.takes and getattr(args, s.dest, None) is not None),
                 next(k for k, s in STARTS.items() if not s.takes))
    word = STARTS[start].word
    ends = [k for k, e in ENDS.items() if start in e.starts]
    # 손가락을 끝보다 먼저 본다 — 「내 일정 한 건」을 고치려는 부름(preview --handle --start)이 「미리 보기가 없다 · 그 끝(지우기)으로」가
    # 아니라 고치기를 어디서 하나를 받게
    for c in CHANGES.values():
        if given(args, c) and start not in c.starts:
            raise Stop(EXIT_ARGS, "args", f"「{word}」에는 「{c.word.split(' — ')[0]}」 손가락이 없다. 다음: {c.elsewhere}")
    end = args.command
    if end == "preview":
        end = next((k for k in ends if ENDS[k].confirm), "")
        if not end:
            raise Stop(EXIT_ARGS, "args", f"「{word}」의 끝({' · '.join(ends)})은 미리 보기가 없다 — "
                                          f"{' · '.join(ENDS[k].key for k in ends)}. 다음: 사람에게 그 줄을 보이고 그 끝으로 부른다")
    if start not in ENDS[end].starts:
        raise Stop(EXIT_ARGS, "args", f"「{word}」에서는 {end}({ENDS[end].word})를 못 한다 — 이 출발의 끝: "
                                      f"{' · '.join(ends)}. 다음: 출발을 바꾸거나({' · '.join(s.takes or k for k, s in STARTS.items())}) 끝을 바꾼다")
    missing = [c.flags[0][0] for c in CHANGES.values() if start in c.need and not given(args, c)]
    if missing:
        raise Stop(EXIT_ARGS, "args", f"「{word}」에는 {' · '.join(missing)} 가 든다")
    return start


def key_of(view: dict) -> str:
    """보인 판의 열쇠 — 판(보인 값과 그 둘레) 전체의 해시. 같은 판이면 늘 같은 글자다."""
    blob = json.dumps(view, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:KEY_LENGTH]


# ── 일정 앱 주소 ────────────────────────────────────────────────────────────────────────────────
def saved_url() -> str:
    try:
        data = json.loads(pathlib.Path(SAVED_URL).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(data.get("calendar_url") or "") if isinstance(data, dict) else ""


def resolve(args, default: str) -> tuple[str, bool]:
    """일정 앱 주소와 그것이 기본값인가 — ``--url`` → ``CALENDAR_URL`` → 남긴 주소 → 잰 기본(``agenda.DEFAULT_APP_URL``)."""
    given_url = (args.url or os.environ.get("CALENDAR_URL", "") or saved_url()).strip()
    return (given_url, False) if given_url else (default, True)


# ── 답의 꼴 ────────────────────────────────────────────────────────────────────────────────────
def weekday_of(day: date) -> str:
    return WEEKDAYS[day.weekday()]


def stamp(agenda, t: datetime) -> str:
    """서울 벽시계 ``YYYY-MM-DD HH:MM`` — 명령이 받는 꼴 그대로."""
    return t.astimezone(agenda.KST).strftime(agenda.STAMP_FORM)


def row(agenda, e) -> dict:
    out = {"day": e.day.isoformat(), "weekday": weekday_of(e.day), "when": e.when(), "start": stamp(agenda, e.start),
           "end": stamp(agenda, e.end), "title": e.title, "handle": agenda.Seen.of(e).handle, "keep": e.keep_reason,
           "pending": e.response == agenda.RESPONSE_PENDING, "meeting": e.meeting, "repeat": e.repeat, "all_day": e.all_day}
    if e.keep_reason:
        out["keep_word"] = KEEP_WORDS.get(e.keep_reason, e.keep_reason)
    if e.calendar:                       # 기본 밖 내 일정함 · 공유받은 일정함의 줄 — 어느 일정함인가. 지우는 손잡이는 없다
        out["calendar"] = e.calendar
        del out["handle"]
    return out


def shared_row(agenda, e) -> dict:
    out = row(agenda, e)
    out["private"] = e.private           # 일정함을 가진 사람이 비공개로 든 것
    del out["pending"]                   # 참석 답은 그 일정함을 가진 사람의 것이라 내 초대로 읽히지 않게 뺀다
    return out


def fit_days(out: dict, last: date, again: str) -> None:
    """보기의 답이 OUT_BYTES 를 넘으면 뒤 날짜의 줄부터 덜어 낸다 — 하루를 가운데서 끊지 않는다(그날이 비어 보이면 그날에 일정을
    겹쳐 잡는다). 덜었으면 ``more`` 가 이어 볼 구간을 든다. 하루치만으로 넘치면 그 하루는 그대로 낸다."""
    lists = [k for k in ("events", "shared") if k in out]
    days = sorted({r["day"] for k in lists for r in out[k]})
    while len(days) > 1 and size(out, INDENT) > OUT_BYTES:
        cut = days.pop()
        for k in lists:
            out[k] = [r for r in out[k] if r["day"] < cut]
        out["more"] = f"다음: {cut} 부터는 안 실었다 — show {cut} {last.isoformat()}{again} 로 이어 본다"


def shared_books(reader, who: list | None) -> list:
    """공유받은 일정함 — ``who`` 를 주면 이름에 그 글자 가운데 하나가 든 것만. 하나도 안 걸리는 글자가 있으면 인자가 틀린 것이다."""
    books = reader.shared_books()
    if not who:
        return books
    names = [w.strip() for w in who if w.strip()]
    lost = [w for w in names if not any(w in b.name for b in books)]
    if lost:
        have = ", ".join(b.name for b in books) or "없음"
        raise Stop(EXIT_ARGS, "args", f"공유받은 일정함에 「{', '.join(lost)}」가 없다 — 있는 것: {have}")
    return [b for b in books if any(w in b.name for w in names)]


def want_of(args, agenda):
    w = agenda.Want(args.title, agenda.kst(args.start), agenda.kst(args.end), args.note or "").cleaned()
    if not w.title or w.end <= w.start:
        raise Stop(EXIT_ARGS, "args", "제목이 비었거나 끝이 시작보다 앞이다")
    return w


def plan_new(args, agenda, reader) -> tuple[dict, object, list]:
    """새 일정 한 건의 판 — (보일 판 · 넣을 것 · 겹친 줄). 바꾸지 않는다. preview 와 add 가 같은 판을 짓고, 판 전체의 해시가 key 다 —
    값이든 겹침이든 이미 있나든 보인 뒤 달라졌으면 key 가 달라진다."""
    w = want_of(args, agenda)
    mine, side_failed = reader.mine_between(w.day, agenda.kst_day(w.end))   # 겹침은 내 일정함 전부(기본 · Teams)에서 본다
    same = next((e for e in mine if not e.calendar and agenda.same_event(e, w)), None)   # 이미 있나는 넣을 자리(기본 일정함)에서만
    clash = [e for e in mine if e.overlaps(w.start, w.end) and e is not same]
    view = {"state": "already" if same else "ready", "title": w.title, "note": w.note, "day": w.day.isoformat(),
            "weekday": weekday_of(w.day), "when": f"{w.start.astimezone(agenda.KST):%H:%M}–{w.end.astimezone(agenda.KST):%H:%M}",
            "start": stamp(agenda, w.start), "end": stamp(agenda, w.end), "visibility": agenda.VISIBILITY,
            "already": row(agenda, same) if same else None, "clash": [row(agenda, e) for e in clash]}
    if side_failed:
        view["shared_failed"] = [{"calendar": n, "message": m} for n, m in side_failed]
    view["key"] = key_of(view)
    return view, w, clash


def show_days(args, today: date) -> tuple[date, date]:
    """show 의 첫날 · 끝날 — 첫날을 안 주면 오늘 · 내일, 첫날만 주면 그 하루. 꼴이 아니거나 끝날이 첫날보다 앞이면 Stop(인자)."""
    try:
        first = day_of(args.first or "오늘", today)
        last = day_of(args.last, today) if args.last else (first + timedelta(days=1) if not args.first else first)
    except Stop as exc:
        raise Stop(EXIT_ARGS, "args", f"{exc}. 다음: {DAY_COUNT}") from exc
    if last < first:
        raise Stop(EXIT_ARGS, "args", f"끝날({last})이 첫날({first})보다 앞이다 — show <첫날> <끝날> 차례로 준다")
    return first, last


# ── 모두 비는 때 ────────────────────────────────────────────────────────────────────────────────
def free_window(args) -> tuple[time, time] | None:
    """show 의 --free · --hours — (하루의 처음, 끝) 이나 --free 가 없으면 None. 틀렸으면 Stop(인자)."""
    if args.free is None:
        if args.hours:
            raise Stop(EXIT_ARGS, "args", "--hours 는 --free 와 함께 준다 — 다음: show … --free <분> --hours HH:MM-HH:MM")
        return None
    if args.free <= 0:
        raise Stop(EXIT_ARGS, "args", "--free 는 1 분 이상으로 준다")
    found = HOURS_FORM.match(args.hours or WORK_HOURS)
    try:
        lo, hi = (datetime.strptime(t, "%H:%M").time() for t in found.groups()) if found else (None, None)
    except ValueError:
        lo = hi = None
    if lo is None or hi <= lo:
        raise Stop(EXIT_ARGS, "args", f"--hours 는 「HH:MM-HH:MM」(서울 · 앞이 뒤보다 이르게)으로 준다: {args.hours!r}")
    return lo, hi


def busy_of(agenda, e) -> tuple[tuple[datetime, datetime] | None, str]:
    """일정 줄 하나를 모두 비는 때의 셈에 어떻게 넣나 — (바쁜 구간이나 None, 시각을 짐작했으면 그 까닭). 줄이 실제로 드는 것만
    쓴다(``references/SOURCES.md``): 시각이 온 줄은 그 시각대로 — 참석 답 전 초대 · Teams · 비공개로 든 남의 일정(제목 · 시각이 그대로
    온다)도 바쁘다. 하루 종일 · 여러 날 줄의 꼴은 안 쟀다 — 그날(들) · 시작부터 끝까지 내내 바쁜 것으로 세고 까닭을 단다. 끝이 시작과
    같은 줄은 길이를 몰라 안 세고 까닭을 단다 — 셈에서 말없이 빠지지 않게."""
    if e.all_day:
        first, last = agenda.kst_day(e.start), agenda.kst_day(e.end)
        if e.end > e.start and e.end.astimezone(agenda.KST).time() == time(0):
            last -= timedelta(days=1)                      # 다음 날 0 시에 끝나는 꼴 — 그 날은 안 든다
        last = max(first, last)
        span = (datetime.combine(first, time(0), agenda.KST), datetime.combine(last + timedelta(days=1), time(0), agenda.KST))
        return span, f"하루 종일 일정이다 — 줄의 시각 꼴을 {UNMEASURED}. 그날 내내 바쁜 것으로 셌다"
    if e.end <= e.start:
        return None, "끝이 시작과 같은 줄이다 — 길이를 몰라 바쁜 때로 안 셌다"
    if agenda.kst_day(e.start) != agenda.kst_day(e.end - timedelta(microseconds=1)):
        return (e.start, e.end), f"여러 날에 걸친 일정이다 — 줄의 꼴을 {UNMEASURED}. 시작부터 끝까지 내내 바쁜 것으로 셌다"
    return (e.start, e.end), ""


def next_step(t: datetime) -> datetime:
    """``t`` 뒤(같으면 그대로)의 첫 ``SLOT_STEP_MINUTES`` 눈금 — 초가 남으면 다음 분부터 센다."""
    whole = t.replace(second=0, microsecond=0)
    if whole < t:
        whole += timedelta(minutes=1)
    return whole + timedelta(minutes=-whole.minute % SLOT_STEP_MINUTES)


def free_of(agenda, events: list, first: date, last: date, minutes: int, hours: tuple[time, time], now: datetime,
            counted: list, failed: list, unread: list) -> dict:
    """읽은 일정함 전부가 ``minutes`` 분 이상 함께 비는 때 — 평일마다 ``hours`` 안에서, 지난 시각은 빼고. 바쁜 구간은 ``busy_of`` 가
    정하고 틈은 ``ep_command.gaps_of`` 가 센다. 시각을 짐작한 줄 · 못 읽은 일정함 · 시각을 못 읽어 뺀 줄은 답에 달고 ``word`` 가 사람에게
    그렇다고 말하라 이른다 — 셈에서 말없이 「빈다」로 넘어가지 않게."""
    spans, doubt = [], []
    for e in events:
        span, why = busy_of(agenda, e)
        if span:
            spans.append(span)
        if why:
            doubt.append((e, span, why))
    windows, weekend = [], []
    day = first
    while day <= last:
        if day.weekday() in WEEKEND:
            weekend.append(day.isoformat())
        else:
            lo = max(datetime.combine(day, hours[0], agenda.KST), next_step(now.astimezone(agenda.KST)))
            hi = datetime.combine(day, hours[1], agenda.KST)
            if lo < hi:
                windows.append((lo, hi))
        day += timedelta(days=1)
    need = timedelta(minutes=minutes)
    slots = [g for lo, hi in windows for g in gaps_of(spans, lo, hi, need)]
    out = {"minutes": minutes, "hours": f"{hours[0]:%H:%M}–{hours[1]:%H:%M}", "counted": counted,
           "slots": [{"day": a.astimezone(agenda.KST).date().isoformat(), "weekday": weekday_of(a.astimezone(agenda.KST).date()),
                      "when": f"{a.astimezone(agenda.KST):%H:%M}–{b.astimezone(agenda.KST):%H:%M}", "start": stamp(agenda, a),
                      "end": stamp(agenda, b), "minutes": int((b - a).total_seconds() // 60)} for a, b in slots]}

    def touches(e, span) -> bool:
        a, b = span or (e.start, e.start)
        return any((a < hi and lo < b) if span else lo <= a < hi for lo, hi in windows)
    assumed = [{**{k: v for k, v in row(agenda, e).items() if k in ("day", "when", "title", "calendar")}, "why": why}
               for e, span, why in doubt if touches(e, span)]
    if assumed:
        out["assumed"] = assumed
    if weekend:
        out["weekend"] = weekend
    said = [f"{', '.join(counted)} 의 일정을 견줘 평일 {out['hours']} 안에서 {minutes} 분 이상 함께 비는 때 {len(slots)} 곳"
            + ("" if slots else " — 그 구간에 모두 비는 때가 없다") + "(주말 · 지난 시각은 뺐다)."]
    if failed:
        said.append(f"못 읽은 일정함({', '.join(f['calendar'] for f in failed)})은 셈에 없다 — 그분의 일정은 안 견줬다고 말한다.")
    if unread:
        said.append("시각을 못 읽어 뺀 줄이 있다(unread_rows) — 그 일정함에 셈에 없는 일정이 있을 수 있다고 말한다.")
    if assumed:
        said.append("assumed 의 줄은 시각을 짐작해 셌다 — 그 줄과 까닭을 함께 말하고 사람이 바로잡게 한다.")
    said.append("다음: 사람에게 고르게 하고, 고른 때의 start · end 로 회의실을 찾는다(스킬 company-meeting-room 의 free --start --end).")
    out["word"] = " ".join(said)
    return out


def run(args, session: pathlib.Path) -> dict:
    agenda = load("agenda", HERE)
    url, by_default = resolve(args, agenda.DEFAULT_APP_URL)
    today = datetime.now(agenda.KST).date()
    if args.command == "remember":
        url = (args.address or "").strip()
    found = agenda.APP_URL.match(url)
    if not found:
        raise Stop(EXIT_URL, "url", "일정 앱 주소(…/calperson<NN>.nsf)가 든 주소가 아니다")
    url = found.group(1) + found.group(2)
    reader = agenda.Reader(url, session)
    if args.command == "remember":
        try:
            reader.book()                # 이 주소로 내 일정함이 읽히나 — 읽혀야 남긴다
        except agenda.SessionExpired:
            raise
        except agenda.CalendarError as exc:
            raise Stop(EXIT_URL, "url", f"이 주소로 내 일정함을 못 읽었다({exc}) — 일정 화면의 주소인지 본다") from exc
        place = pathlib.Path(SAVED_URL).expanduser()
        place.write_text(json.dumps({"calendar_url": url}, ensure_ascii=False), encoding="utf-8")
        return {"saved": str(place), "url": url}
    if by_default:
        try:
            reader.book()                # 잰 기본 주소가 이 사람의 일정함을 드나 — 다른 서버에 일정이 있는 사람은 주소를 받는다
        except agenda.SessionExpired:
            raise
        except agenda.CalendarError as exc:
            raise Stop(EXIT_URL, "url", f"기본 일정 앱 주소({url})로 내 일정함이 안 읽힌다({exc}) — 일정 DB 가 다른 서버에 있는 사람이다. {NEXT_URL}") from exc
    if args.command == "calendars":
        return {"shared": [{"name": b.name, "kind": b.kind} for b in reader.shared_books()]}
    if args.command == "show":
        first, last = show_days(args, today)
        out = {"today": today.isoformat(), "today_weekday": weekday_of(today), "first": first.isoformat(), "last": last.isoformat()}
        hours = free_window(args)
        mine, side_failed = reader.mine_between(first, last)
        out["events"] = [row(agenda, e) for e in mine]
        failed = [{"calendar": n, "message": m} for n, m in side_failed]
        counted = [MY_BOOK] + [b.name for b in reader.side_books() if b.name not in {n for n, _ in side_failed}]
        shared = []
        if args.shared or args.who:
            for b in shared_books(reader, args.who):
                try:
                    shared += reader.between(first, last, b)
                    counted.append(b.name)
                except agenda.CalendarError as exc:   # 한 일정함이 안 읽혀도 나머지는 보인다 — 못 읽은 것은 이름으로 알린다
                    # 그 서버의 「끊긴 세션」 꼴도 여기 든다 — 방금 같은 세션으로 목록을 읽었으니 공유가 풀렸거나 그 서버가 안 받는
                    # 것이다. ep-login 으로 보내면 같은 끝을 되풀이한다
                    failed.append({"calendar": b.name, "message": str(exc)})
            shared.sort(key=lambda e: (e.start, e.end, e.calendar))
            out["shared"] = [shared_row(agenda, e) for e in shared]
        if failed:
            out["shared_failed"] = failed
        if reader.unread:
            out["unread_rows"] = [{"calendar": n or MY_BOOK, "rows": k} for n, k in reader.unread]
        if hours:
            out["free"] = free_of(agenda, mine + shared, first, last, args.free, hours, datetime.now(agenda.KST), counted, failed,
                                  reader.unread)
        fit_days(out, last, (" --shared" if args.shared else "") + "".join(f" --who {w}" for w in args.who or ()))
        return out
    start = fingers(args)
    if start == "new":
        view, w, clash = plan_new(args, agenda, reader)
        if args.command == "preview":
            return view
        if view["key"] != args.confirm:
            return {"state": "moved", "state_word": STATE_WORDS["moved"], "preview": view}
        if view["already"]:
            return {"state": "already", "state_word": STATE_WORDS["already"], "event": view["already"]}
        got = agenda.register(url, session, w, reader=reader, shown_clash={agenda.event_ref(e) for e in clash})
        state = ADDED_STATE[got.state]
        return {"state": state, "state_word": STATE_WORDS[state], "event": row(agenda, got.event) if got.event else None}
    try:
        got = agenda.delete(url, session, agenda.Seen.parse(args.handle), reader=reader)
    except agenda.ChangeRefused as exc:
        return {"state": "refused", "reason": exc.reason, "state_word": KEEP_WORDS.get(exc.reason) or str(exc)}
    state = REMOVED_STATE[got.state]
    return {"state": state, "state_word": STATE_WORDS[state], "event": row(agenda, got.event) if got.event else None}


def parser() -> argparse.ArgumentParser:
    raw = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(description="회사 일정 — 보기 · 넣기 · 지우기", epilog=finger_map(), formatter_class=raw)
    p.add_argument("--url", help="일정 앱 주소(…/calperson<NN>.nsf) — 없으면 CALENDAR_URL · 남긴 주소 · 잰 기본")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("remember", help="일정 앱 주소를 재 보고 남긴다")
    r.add_argument("address")
    s = sub.add_parser("show", help=READS["show"])
    s.add_argument("first", nargs="?", metavar="첫날", help=f"{' · '.join(DAY_WORDS)} · YYYY-MM-DD(안 주면 오늘 · 내일). {DAY_COUNT}")
    s.add_argument("last", nargs="?", metavar="끝날", help="첫날과 같은 꼴 — 주면 첫날부터 그날까지(둘 다 든다), 안 주면 첫날 하루")
    s.add_argument("--shared", action="store_true", help="공유받은 일정함 전부를 곁에")
    s.add_argument("--who", action="append", help="공유받은 일정함 가운데 이름에 이 글자가 든 것을 곁에(여럿이면 거듭 준다)")
    s.add_argument("--free", type=int, metavar="분", help="읽은 일정함 전부가 이 분 이상 함께 비는 때를 낸다(주말 · 지난 시각은 뺀다)")
    s.add_argument("--hours", metavar="HH:MM-HH:MM", help=f"--free 가 찾는 하루의 구간(기본 {WORK_HOURS})")
    sub.add_parser("calendars", help=READS["calendars"])
    for name in ("preview", *ENDS):
        a = sub.add_parser(name, help="넣을 꼴 미리 보기 · key(바꾸지 않는다)" if name == "preview" else f"⚠ {ENDS[name].word}",
                           epilog=finger_map(), formatter_class=raw)
        for s_ in STARTS.values():
            if s_.takes:
                a.add_argument(s_.takes, default=None, help=f"출발 — {s_.word}")
        for c in CHANGES.values():
            for flag, extra in c.flags:
                a.add_argument(flag, default=None, **{"help": c.word, **extra})
        for n in NOT_YET.values():
            for flag, extra in n.flags:
                a.add_argument(flag, default=None, **{"help": f"아직 없다 — {n.word}", **extra})
        if name in ENDS and ENDS[name].confirm:
            a.add_argument("--confirm", required=True, help="preview 의 key — 사람이 본 판")
    return p


def main() -> int:
    args = parser().parse_args()

    def work(agenda):
        if args.command in ("preview", *ENDS):
            fingers(args)                # 없는 손가락 · 빠진 값은 세션을 받기 전에 멈춘다
        if args.command == "show":
            show_days(args, datetime.now(agenda.KST).date())   # 날이 틀렸으면 세션을 받기 전에 멈춘다
            free_window(args)            # --free · --hours 가 틀렸으면 세션을 받기 전에 멈춘다
        return ep_session.session_first(lambda f: run(args, f), expired=(agenda.SessionExpired, agenda.SessionMissing),
                                        file_first=args.command not in MUTATING)

    return ep_command.finish(work, "agenda", HERE, indent=INDENT, app_error="CalendarError",
                             args_errors=("CalendarConfigError",))   # 설정 · 인자가 틀린 것은 2


if __name__ == "__main__":
    sys.exit(main())
