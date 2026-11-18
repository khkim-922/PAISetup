"""회의실 예약 스킬의 얇은 명령 — 곁의 손(``mrs.py``)으로 회의실 · 빈 곳 · 예약 현황 · 내 예약을 보고, 예약 한 건을 넣고 · 고치고 ·
본떠 넣고 · 취소한다.

부르는 꼴::

    python -X utf8 -I meeting_room.py --help     # 지도 — 출발 × 바꿀 것 × 끝 · 읽기. 아래 표(STARTS · CHANGES · ENDS · READS)에서 짓는다
    python -X utf8 -I meeting_room.py rooms [말 …]
    python -X utf8 -I meeting_room.py free  --start S --end E [--minutes N] [--where 말 …] [--people N]
    python -X utf8 -I meeting_room.py day   [말 …] [--date 오늘|내일|YYYY-MM-DD]
    python -X utf8 -I meeting_room.py mine  [오늘|YYYY-MM-DD] [끝 날]
    python -X utf8 -I meeting_room.py preview [--id 예약 | --copy 예약] [--room R] [--title T] [--start S] [--end E] [--note N]
                                              [--to 메일 …] [--to-file 파일 …] [--add-to 메일 …] [--add-to-file 파일 …] [--drop-to 메일 …]
    python -X utf8 -I meeting_room.py book    [--copy 예약] …preview 와 같은 값… --confirm <preview 의 key>   # ⚠ 넣는다
    python -X utf8 -I meeting_room.py change  --id 예약 …preview 와 같은 값… --confirm <preview 의 key>       # ⚠ 고친다
    python -X utf8 -I meeting_room.py cancel  --id 예약 --confirm <mine 이 낸 그 줄의 key>                    # ⚠ 취소한다

    시각은 다 서울 벽시계 ``YYYY-MM-DD HH:MM`` 이고, 답의 ``start`` · ``end`` 도 그 꼴이라 그대로 다음 명령(이 스킬 · 회사 일정)에 준다.
    참석자는 메일 주소로 준다 — 사람은 스킬 company-mail 의 who 로 정하고, 그 --out 이 쓴 주소 파일(한 줄에 하나 · ``#`` 뒤는 버린다)을
    ``--to-file`` 로 그대로 준다.

한 번 부름이 예약 한 건을 한 번 다룬다 — 출발 하나(새 예약 · 내 예약 한 건 · 본뜰 예약)에 바꿀 것을 아무 조합으로 주고 끝 하나로
맺는다. 넣기 · 고치기 · 취소는 참석자에게 회사 메일로 안내가 가 되돌릴 수 없어, 한 건을 여러 번에 나눠 바꾸지 않는다(부를 때마다
안내가 간다). 없는 손가락을 주면 그 일을 어디서 하는지 대며 종료 2 로 멈춘다.

하는 일 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 로 사내 세션을 쥐고(보기는 있는 파일부터, 바꾸기는 늘 받는 손부터
한 번만), 그 세션으로 회의실 예약 앱의 출입증을 받아 부른다. 판단(무엇을 넣을까 · 사람이 확인했나)은 여기 없다 — 바꾸는 명령은
사람이 그 한 건을 확인한 뒤에만 부르고, 열쇠가 그 확인을 손 안에서 지킨다: preview 와 넣기 · 고치기는 같은 판(``plan``)을 짓고 그
해시가 key 라, 보인 뒤 무엇이든 달라졌으면 안 바꾼다. 취소의 key 는 mine 이 보인 그 줄의 해시다. 앱의 미리 검사는 정책만 보아,
겹침 · 지난 시각은 여기서 가린다.

내는 것 — 표준 출력에 JSON 하나. 종료 값: 0 됐다 · 1 도구 · 앱 고장(그대로 알린다) · 2 인자가 틀렸다(없는 손가락 · 빠진 값 · 회의실이
여럿 걸림 — ``message`` 가 후보와 다음 걸음을 든다) · 3 사내 세션이 없다 · 끊겼다(스킬 ep-login). 0 이 아니면 ``message`` 가 까닭과
「다음: …」 을 든다. preview 는 ``state``(ready · blocked) · ``blocks``(못 하는 까닭) · ``notes``(할 수는 있으나 사람이 알아야 할 것) ·
``key`` 를, 바꾸는 명령은 ``state`` 와 사람에게 할 말 · 다음 걸음이 든 ``state_word`` 를 낸다. 예약 줄의 ``attendees`` 는 이름과 메일
주소, ``teams`` 는 Teams 링크 · 회의 ID · 암호(현황 ``day`` 의 남의 줄은 붙었다는 것만)다. 취소 ``key`` 는 내가 주관한 줄(mine ·
day · preview 의 was · 넣기 · 고치기의 답)에만 선다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
KST = timezone(timedelta(hours=9))
STAMP = "%Y-%m-%d %H:%M"                  # 서울 벽시계 — 받는 꼴이자 답의 start · end 꼴
STAMP_HELP = "YYYY-MM-DD HH:MM(서울)"
MINE_DAYS = 14                            # mine 의 기본 구간 — 오늘부터 두 주
MOST_ROOMS = 60                           # rooms 답에 싣는 회의실 수 — count 는 다 센 수다
MOST_FREE = 40                            # free 답에 싣는 빈 회의실 수
MOST_GRID = 30                            # day 답에 싣는 회의실 수 — 한 회의실의 그날 예약이 한 묶음이다
MOST_CANDIDATES = 15                      # 회의실이 여럿 걸릴 때 message 에 보이는 후보 수
KEY_LENGTH = 16                           # 열쇠(보인 판의 해시)의 길이 — 16진 글자
LIVE = ("confirmed", "pending_approval")  # 회의실을 쥔 예약의 상태 — cancelled · rejected 는 비운 것이다
STATUS_WORDS = {"confirmed": "확정", "pending_approval": "승인 대기", "cancelled": "취소됨", "rejected": "거절됨"}
INDENT = 1
TEAMS_FIELDS = {"link": "join_url", "meeting_id": "meeting_id", "passcode": "meeting_password"}   # 답의 이름 → 예약 줄 teams_meeting 의 칸
SERIES_ID = "recurring_id"                # 반복의 회차를 묶는 칸
WEEKEND = 5                               # weekday() 가 이 값부터 토 · 일이다 — 반복 회차는 그 앞 날에만 선다
MOST_OCCURRENCES = 120                    # 반복 미리 보기가 회차마다 겹침을 보는 수 — 넘으면 막고 끝 날을 당기라 한다
# 주소를 가르는 글자 — 빈칸 · 쉼표 · 쌍반점. 주소 파일은 회사 메일 스킬이 쓰는 꼴(한 줄에 하나 · # 뒤는 버린다 · 앞에 BOM 이 올 수 있다)
ADDRESS_SPLIT = re.compile(r"[,;\s]+")
UNKNOWN_NEXT = ("회의 참석자는 사람 한 명씩이다 — 부서 주소(dept_…)면 스킬 company-mail 의 who --dept <부서> --out <폴더> 로 부서원 주소 파일을 받아 "
                "--to-file · --add-to-file 로 주고, 사외 주소는 여기서 넣지 않는다")
SCREEN = "https://mrs.posco.net/scheduler"   # 사람이 쓰는 회의실 예약 화면 — 아직 없는 손가락을 거기서 하시라 권한다
UNMEASURED = "회사에서 안 쟀다"             # 지은 손가락 가운데 회사에서 그 판을 아직 안 잰 자리의 표시 — --help 와 preview 의 notes 가 같은 말을 쓴다


# ── 손가락의 표 — 출발 × 바꿀 것 × 끝. 손가락을 더하거나 빼는 일은 이 표의 줄과 그 일을 하는 손 하나다 ─────────────────
@dataclass(frozen=True)
class Start:
    """출발 하나 — 예약 앱의 창 하나."""
    word: str        # 사람 말
    screen: str      # 그 창이 무엇을 채우나 — --help 의 지도
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
    unmeasured: tuple = ()   # 받되 회사에서 그 판을 아직 안 잰 출발 — --help 가 표시하고 preview 가 notes 로 알린다


@dataclass(frozen=True)
class NotYet:
    """아직 없는 손가락 하나 — 회사에서 안 잰 화면 동작이라 짓지 않았다. 인자가 있으면 받아 두었다가 세션 전에 멈추며 어디서 하나를 댄다."""
    word: str                # 무엇을 못 하나
    where: str               # 사람이 어디서 하나
    flags: tuple = ()        # ((인자, argparse 의 덧값), …) — 모델이 짐작해 줄 만한 인자. 비면 --help 의 지도에만 선다
    again: str = ""          # 거듭 주면 이 손가락을 바란 것으로 읽는 바꿀 것(CHANGES 의 열쇠 · 그 인자는 Again 으로 받는다)


class Again(argparse.Action):
    """한 번만 받는 칸 — 거듭 주면 ``<dest>_again`` 을 세워 거름이 멈추게 한다. argparse 기본은 뒤 값만 남겨 앞 값을 말없이 버린다."""

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            setattr(namespace, f"{self.dest}_again", True)
        setattr(namespace, self.dest, values)


@dataclass(frozen=True)
class End:
    """끝 하나 — 누르는 단추. 다 참석자에게 안내가 가고 되돌릴 수 없다."""
    word: str
    starts: tuple
    key: str                 # 무엇이 사람의 확인을 지키나 — --help 의 지도
    changes: bool = True     # 바꿀 것을 받나 — 안 받는 끝에 주면 멈춘다


STARTS = {
    "new": Start("새 예약", "예약 창을 빈 칸에서 연다"),
    "booking": Start("내 예약 한 건", "예약 고치기 창 — 내가 주관한 예약(반복 예약은 빼고). mine 의 id", "--id"),
    "copy": Start("예약 본뜨기", "예약 창을 그 예약의 회의실 · 제목 · 설명 · 참석자로 채워 새로 연다 — 원래 예약은 그대로다. mine 의 id",
                  "--copy"),
    "series": Start("반복 예약 전체", "반복의 모든 회차를 한 번에 — 내가 주관한 반복의 회차 id 하나(mine 의 줄의 series)로 고른다. "
                    f"첫 회차가 지난 반복은 안 다룬다(그 판은 {UNMEASURED})", "--series"),
}
ALL = tuple(STARTS)
ONE = ("new", "booking", "copy")          # 예약 한 건의 창 — 반복 전체는 시각 · 회의실을 안 바꾼다(그 판은 회사에서 안 쟀다)
HELD = ("booking", "copy", "series")      # 있던 예약에서 출발한다 — 참석자를 더하고 뺄 것이 있다
SERIES_FIXED = "반복 전체의 시각 · 회의실 바꾸기는 아직 안 쟀다 — 사람에게 회의실 예약 화면에서 하시라 권한다"
NEW_EMPTY = "새 예약은 참석자가 비어 있다 — --to · --to-file 로 준다"
CHANGES = {
    "room": Change((("--room", {"action": Again}),), ONE, "회의실 — id 나 이름 · 지역 · 건물 · 층의 일부(한 곳만 걸려야 한다)", SERIES_FIXED,
                   need=("new",), unmeasured=("booking",)),
    "title": Change((("--title", {}),), ALL, "제목", need=("new",)),
    "start": Change((("--start", {"help": STAMP_HELP}),), ONE, "시작 — 있던 예약 · 본뜨기에 시작만 주면 길이를 그대로 둔다", SERIES_FIXED,
                    need=("new", "copy")),
    "end": Change((("--end", {"help": STAMP_HELP}),), ONE, "끝 — 사람이 끝을 안 말했으면 지어 넣지 말고 묻는다", SERIES_FIXED, need=("new",)),
    "until": Change((("--until", {"metavar": "YYYY-MM-DD"}),), ("new", "copy"),
                    "반복 — 이 날까지 업무일(주말 · 공휴일 빼고)마다 같은 시각에 한 회차씩. 공휴일은 앱이 뺀다",
                    "반복은 새로 넣을 때만 정한다 — 있던 예약을 반복으로 바꾸지 않는다. 반복 전체는 --series 로 고친다"),
    "note": Change((("--note", {}),), ALL, "설명"),
    "to": Change((("--to", {"nargs": "*"}), ("--to-file", {"nargs": "*"})), ALL,
                 "참석자 — 메일 주소(빈칸 · 쉼표로 여럿, 파일은 한 줄에 하나). 있던 예약 · 본뜨기의 참석자를 이 사람들로 통째로 간다"),
    "add_to": Change((("--add-to", {"nargs": "*"}), ("--add-to-file", {"nargs": "*"})), HELD,
                     "참석자 더하기 — 있던 참석자는 그대로 두고 더한다", NEW_EMPTY),
    "drop_to": Change((("--drop-to", {"nargs": "*"}),), HELD, "참석자 빼기 — 지금 참석자의 메일 주소(mine · preview 의 attendees)", NEW_EMPTY),
    "group": Change((("--group", {}),), ALL, "참석자 그룹 더하기 — 내 참석자 그룹(prefs 의 groups) 이름. 있던 참석자는 그대로 두고 그 사람들을 더한다"),
}
# 아직 없는 손가락 — 회사에서 그 화면 동작을 재 오면 이 줄을 걷고 CHANGES 한 줄과 그 일을 하는 손 하나를 더한다
ON_SCREEN = f"사람에게 회의실 예약 화면({SCREEN})에서 하시라 권한다"
NOT_YET = {
    "repeat": NotYet("주기를 고른 반복(매주 · 격주 · 매달)", "회의실 예약 앱의 반복은 업무일마다 하나뿐이다 — 날마다면 --until 로 넣는다. "
                     f"주기가 있으면 {ON_SCREEN.replace('사람에게 ', '')}", (("--repeat", {"metavar": "주기"}),)),
    "rooms": NotYet("여러 회의실 묶어 잡기", f"--room 은 한 곳만 받는다. {ON_SCREEN} — 한 곳씩 따로 잡으면 참석자에게 안내가 따로 간다",
                    again="room"),
    "approve": NotYet("승인하기 · 승인 요청 보기", ON_SCREEN),
    "reply": NotYet("참석 답(수락 · 거절)", "회의 안내 메일이나 회의실 예약 화면에서 사람이 한다"),
}
ENDS = {
    "book": End("넣기", ("new", "copy"), "--confirm <preview 의 key>"),
    "change": End("고치기", ("booking", "series"), "--confirm <preview --id · --series 의 key>"),
    "cancel": End("취소", ("booking", "series"), "--confirm <그 줄의 key> — mine 과 preview --id 의 was 가 내가 주관한 줄마다 낸다. "
                  "반복 전체는 preview --series 의 was 의 key", changes=False),
}
READS = {
    "rooms": "회의실 찾기 — 이름 · 지역 · 건물 · 층의 일부(빈칸으로 여럿, 다 든 곳)",
    "free": "그 시각에 빈 회의실 — --start · --end 내내 빈 곳. --minutes N 을 주면 그 구간 안에서 N 분 넘게 비는 곳과 비는 때",
    "day": "예약 현황 — 낱말에 걸린 회의실들의 그날 예약(회의실마다 한 묶음). 날은 --date. 내가 주관한 줄에 참석자 · 취소 key",
    "mine": "내 예약 — 내가 주관한 것과 나를 부른 것(기본 오늘부터 두 주). 줄마다 Teams 링크 · 회의 ID · 암호, 내가 주관한 줄에 취소 key",
    "prefs": "내 설정 — 즐겨찾는 회의실과 참석자 그룹(그룹마다 사람 이름 · 메일)",
}
# 내 설정 바꾸기 — 하나씩. 남에게 알림이 안 가지만 남이 든 그룹을 짓는 일이라 예약과 같은 열쇠로 지킨다
PREF_ACTIONS = {
    "favorite": ("--favorite", "즐겨찾는 회의실에 넣기 — 회의실 id 나 이름 · 지역 · 건물 · 층의 일부"),
    "unfavorite": ("--unfavorite", "즐겨찾는 회의실에서 빼기 — 같은 꼴"),
    "save_group": ("--save-group", "참석자 그룹 짓기 · 갈기 — 그룹 이름. 사람은 --to · --to-file(메일 주소). 같은 이름이 있으면 그 사람들로 통째로 간다"),
    "drop_group": ("--drop-group", "참석자 그룹 지우기 — 그룹 이름"),
}
MUTATING = (*ENDS, "pref")

# 바꾸는 명령의 끝 — 낱말 하나가 뜻 하나다(형제 스킬 company-calendar 의 같은 낱말과도 같은 뜻)
STATE_WORDS = {
    "booked": "예약했습니다(내 예약에서 다시 읽어 확인했습니다). 참석자께는 회의 안내가 회사 메일로 갑니다 — 조금 걸릴 수 있습니다. "
              "다음: 이 줄의 id · key 를 들고 있다가 「방금 것 취소 · 시간 바꿔 줘」에 쓴다",
    "pending": "넣었지만 이 회의실은 승인이 필요해 「승인 대기」입니다 — 승인되면 확정됩니다",
    "updated": "고쳤습니다(다시 읽어 확인했습니다). 참석자께는 바뀐 안내가 갑니다",
    "cancelled": "취소했습니다(내 예약에서 사라진 것을 확인했습니다). 참석자께는 취소 안내가 갑니다",
    "gone": "내 예약에 그 예약이 없습니다 — 이미 취소됐거나 id 가 틀렸습니다. 다음: mine 으로 내 예약을 읽어 보인다",
    "refused": "여기서는 하지 않습니다 — 답의 reason 에 맞는 말을 그대로 전한다",
    "moved": "보여 드린 뒤 그 사이에 바뀐 것이 있어 하지 않았습니다. 다음: 답의 preview · booking(지금 판)을 보이고 다시 묻는다",
    "blocked": "할 수 없습니다 — 답의 blocks 를 그대로 전한다",
    "unsure": "됐는지 확인하지 못했습니다. 다음: 다시 부르지 말고 mine 으로 읽어 보인다",
    "saved": "내 설정을 바꿨습니다(앱이 낸 설정에서 확인했습니다). 남에게 가는 알림은 없습니다",
}
REFUSE_WORDS = {
    "not_mine": "내가 주관한 예약이 아니라 고치거나 취소하지 않습니다 — 주관하신 분께 부탁하거나 회의실 예약 화면에서 해 주세요. "
                "같은 사람들로 새로 잡으려면 --copy 로 본뜬다",
    "series": "반복 예약의 회차입니다 — 회차 하나만 고치거나 취소하는 길은 아직 안 쟀습니다. 반복 전체는 --series <이 id> 로 하고, "
              "회차 하나만은 회의실 예약 화면에서 해 주세요",
    "single": "반복 예약이 아닙니다 — 한 건은 --id 로 고치고 취소한다",
}


if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    from ep_command import DAY_COUNT, DAY_WORDS, EXIT_ARGS, OUT_BYTES, WEEKDAYS, Stop, day_of, gaps_of, load, size
except ImportError:                             # 형제 스킬 ep-login 이 곁에 없다 — 답의 꼴(JSON 하나 · 종료 1)은 지킨다
    print(json.dumps({"error": "tool", "message": f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"}, ensure_ascii=False))
    sys.exit(1)


# ── 표에서 짓는 것 — 지도 · 인자 거르기 ────────────────────────────────────────────────────────────
def finger_map() -> str:
    """--help 의 지도 — 표 넷에서 짓는다."""
    names = list(STARTS)
    lines = ["지도 — 출발 하나 × 바꿀 것 아무 조합 × 끝 하나. 한 번 부름이 예약 한 건을 한 번 다룬다", "", "출발"]
    lines += [f"  {k:<8} {s.takes + ' <id>' if s.takes else '(인자 없음)':<12} {s.word} — {s.screen}" for k, s in STARTS.items()]
    lines += ["", f"바꿀 것 (● 꼭 든다 · ○ 받는다 · △ 받되 {UNMEASURED} · — 없다)"]
    elsewhere: dict[str, list[str]] = {}
    for c in CHANGES.values():
        marks = " ".join(f"{k}{'●' if k in c.need else '△' if k in c.unmeasured else '○' if k in c.starts else '—'}" for k in names)
        lines.append(f"  {' · '.join(f for f, _ in c.flags):<28} {marks}   {c.word}")
        if c.elsewhere:
            elsewhere.setdefault(c.elsewhere, []).append(c.flags[0][0])
    lines += [f"  — 의 자리({' · '.join(flags)}): {text}" for text, flags in elsewhere.items()]
    lines += [f"  △ 의 자리({c.flags[0][0]} · {' · '.join(c.unmeasured)}): 그 판은 {UNMEASURED} — preview 의 notes 로 사람에게 알리고, 고친 뒤 "
              f"다시 읽어 그대로 섰는지 본다" for c in CHANGES.values() if c.unmeasured]
    lines += ["", "끝 (⚠ 참석자에게 회사 메일로 안내가 가고 되돌릴 수 없다 — 사람이 그 한 건을 보고 「네」 한 뒤에만)"]
    lines += [f"  {k:<7} 출발 {' · '.join(e.starts):<12} {e.word} — 열쇠: {e.key}" + ("" if e.changes else " · 바꿀 것은 안 받는다")
              for k, e in ENDS.items()]
    lines += ["", "읽기"] + [f"  {k:<6} {w}" for k, w in READS.items()]
    lines += ["", "아직 없는 손가락 (인자를 주면 세션 전에 사람이 어디서 하나를 대며 종료 2 로 멈춘다)"]
    lines += [f"  {not_yet_flags(n):<14} {n.word} — {n.where}" for n in NOT_YET.values()]
    return "\n".join(lines)


def not_yet_flags(n: NotYet) -> str:
    """아직 없는 손가락을 부르는 인자 — --help 의 지도에 보인다."""
    if n.again:
        return f"{CHANGES[n.again].flags[0][0]} 거듭"
    return " · ".join(f for f, _ in n.flags)


def dest(flag: str) -> str:
    """인자의 argparse 이름 — ``--add-to`` → ``add_to``."""
    return flag.lstrip("-").replace("-", "_")


def given(args, change: Change) -> bool:
    return any(getattr(args, dest(f), None) is not None for f, _ in change.flags)


def fingers(args) -> str:
    """부른 명령의 출발을 고르고 표에 대 본다 — 아직 없는 손가락 · 출발에 없는 끝 · 손가락, 빠진 값은 그 일을 어디서 하는지 대며
    Stop(인자). 출발을 낸다."""
    for n in NOT_YET.values():
        asked = any(getattr(args, dest(f), None) is not None for f, _ in n.flags)
        if asked or (n.again and getattr(args, f"{dest(CHANGES[n.again].flags[0][0])}_again", False)):
            raise Stop(EXIT_ARGS, "args", f"「{n.word}」 손가락은 아직 없다. 다음: {n.where}")
    picked = [k for k, s in STARTS.items() if s.takes and getattr(args, s.dest, None) is not None]
    if len(picked) > 1:
        raise Stop(EXIT_ARGS, "args", f"출발은 하나다 — {' · '.join(STARTS[k].takes for k in picked)} 가운데 하나만 준다")
    start = picked[0] if picked else next(k for k, s in STARTS.items() if not s.takes)
    word = STARTS[start].word
    ends = [k for k, e in ENDS.items() if start in e.starts]
    end = args.command if args.command != "preview" else next(k for k in ends if ENDS[k].changes)
    if start not in ENDS[end].starts:
        raise Stop(EXIT_ARGS, "args", f"「{word}」에서는 {end}({ENDS[end].word})를 못 한다 — 이 출발의 끝: {' · '.join(ends)}. "
                                      f"다음: 출발을 바꾸거나({' · '.join(s.takes or k for k, s in STARTS.items())}) 끝을 바꾼다")
    for c in CHANGES.values():
        if given(args, c) and start not in c.starts:
            raise Stop(EXIT_ARGS, "args", f"「{word}」에는 「{c.word.split(' — ')[0]}」 손가락이 없다. 다음: {c.elsewhere}")
        if given(args, c) and not ENDS[end].changes:
            raise Stop(EXIT_ARGS, "args", f"{end}({ENDS[end].word})는 바꿀 것을 안 받는다. 다음: 고치려면 change 로 부른다")
    missing = [c.flags[0][0] for c in CHANGES.values() if start in c.need and not given(args, c)]
    if missing:
        raise Stop(EXIT_ARGS, "args", f"「{word}」에는 {' · '.join(missing)} 가 든다")
    return start


def fingerprint(*parts) -> str:
    """보인 판의 열쇠 — 사람이 본 것과 바꿀 때의 판(값 · 겹침 · 출발 예약의 꼴)이 같은지 가린다."""
    blob = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:KEY_LENGTH]


# ── 시각 ────────────────────────────────────────────────────────────────
def kst(text: str) -> datetime:
    try:
        t = datetime.strptime(text.strip(), STAMP)
    except ValueError as exc:
        raise Stop(EXIT_ARGS, "args", f"시각은 「YYYY-MM-DD HH:MM」(서울)으로 준다: {text!r}") from exc
    return t.replace(tzinfo=KST)


def iso(t: datetime) -> str:
    return t.astimezone(KST).isoformat(timespec="seconds")


def stamp(t: datetime) -> str:
    return t.astimezone(KST).strftime(STAMP)


def utc(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def parse_app(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(KST)


def day_span(first: date, last: date) -> tuple[str, str]:
    """서울 하루(들)의 처음과 끝을 앱이 받는 UTC 로 — 앱은 날짜만 주면 UTC 하루로 읽는다."""
    a = datetime.combine(first, datetime.min.time(), KST)
    b = datetime.combine(last + timedelta(days=1), datetime.min.time(), KST) - timedelta(milliseconds=1)
    return utc(a), b.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.999Z")


def when(start: datetime, end: datetime) -> str:
    s, e = start.astimezone(KST), end.astimezone(KST)
    head = f"{s:%m월 %d일}({WEEKDAYS[s.weekday()]}) {s:%H:%M}"
    return f"{head}–{e:%H:%M}" if s.date() == e.date() else f"{head} – {e:%m월 %d일}({WEEKDAYS[e.weekday()]}) {e:%H:%M}"


# ── 회의실 ──────────────────────────────────────────────────────────────
class Places:
    """층 id → 「지역 건물 층」 과 회사 id. ``rooms`` 의 회의실에는 층 · 건물의 이름이 없어 나무에서 받는다."""

    def __init__(self, hierarchy: list):
        self.where, self.company = {}, {}
        for co in hierarchy:
            for loc in co.get("locations", []):
                for b in loc.get("buildings", []):
                    for f in b.get("floors", []):
                        self.where[f["id"]] = f"{loc.get('name', '')} {b.get('name', '')} {f.get('name', '')}".strip()
                        self.company[f["id"]] = co.get("id", "")

    def of(self, room: dict) -> str:
        return self.where.get(room.get("floor_id"), "")


def room_row(room: dict, places: Places) -> dict:
    perm = (room.get("policy") or {}).get("reservation_permission") or {}
    teams = (room.get("policy") or {}).get("teams_integration") or {}
    return {"id": room["id"], "name": room["name"], "where": places.of(room), "capacity": room.get("capacity"),
            "type": room.get("room_type"), "approval": bool(perm.get("require_approval")),
            "bookable": bool(perm.get("user_can_reserve", True)) and bool(room.get("is_active", True)),
            "teams_link": bool(teams.get("meeting_link"))}


def find_rooms(rooms: list, places: Places, word) -> list:
    """이름 · 지역 · 건물 · 층에 낱말이 다 든 회의실 — 낱말은 문자열이나 그 목록이다."""
    keys = (" ".join(word) if isinstance(word, (list, tuple)) else (word or "")).lower().split()
    if not keys:
        return rooms
    return [r for r in rooms if all(k in f"{places.of(r)} {r['name']}".lower() for k in keys)]


def one_room(rooms: list, places: Places, word: str) -> dict:
    exact = [r for r in rooms if r["id"] == word]
    got = exact or find_rooms(rooms, places, word)
    if len(got) == 1:
        return got[0]
    if not got:
        raise Stop(EXIT_ARGS, "args", f"「{word}」에 걸리는 회의실이 없다. 다음: rooms 로 찾아 보인다")
    named = [r for r in got if r["name"] == word]
    if len(named) == 1:
        return named[0]
    listed = "; ".join(f"{places.of(r)} {r['name']} ({r['id']})" for r in got[:MOST_CANDIDATES])
    raise Stop(EXIT_ARGS, "args", f"「{word}」에 회의실이 {len(got)} 곳 걸린다 — {listed}. 다음: 사람에게 고르게 하고 그 id 로 다시 부른다")


def cross_company(room: dict, places: Places, me: dict) -> bool:
    """남의 회사 회의실인데 그 회사가 타사 예약을 안 받는다 — 앱의 미리 검사도 같은 까닭으로 막는다."""
    owner = places.company.get(room.get("floor_id"))
    allow = ((room.get("policy") or {}).get("reservation_restrictions") or {}).get("allow_cross_tenant_reservation")
    return bool(owner) and owner != me.get("company_id") and not allow


# ── 예약 ────────────────────────────────────────────────────────────────
def live(r: dict) -> bool:
    return r.get("status") in LIVE


def overlaps(r: dict, start: datetime, end: datetime) -> bool:
    return parse_app(r["start_time"]) < end and start < parse_app(r["end_time"])


def person(p) -> str:
    if isinstance(p, dict):
        return p.get("display_name") or p.get("name") or p.get("email") or ""
    return str(p or "")


def mine_to_change(r: dict, me_id: str) -> bool:
    """내가 주관한 예약인가 — 앱의 ``isOrganizer`` 가 있으면 그것, 없으면 주관자 id 를 견준다. 모르면 거짓이다."""
    if "isOrganizer" in r:
        return r["isOrganizer"] is True
    org = r.get("organizer_id")
    return bool(me_id) and (org.get("id") if isinstance(org, dict) else org) == me_id


def is_series(r: dict) -> bool:
    """반복 예약의 회차인가 — 회차는 ``recurring_id`` 하나로 묶인다. 회차 줄의 ``is_recurring`` · ``recurring_end_date`` 는 비어
    온다(넣을 때만 보내는 칸)."""
    return bool(r.get(SERIES_ID)) or bool(r.get("is_recurring")) or bool(r.get("recurring_end_date"))


def refusal(r: dict, me_id: str, start: str = "booking") -> str:
    """고치기 · 취소를 안 하는 까닭(``REFUSE_WORDS`` 의 열쇠) — 빈 글자면 한다. 한 건(``booking``)은 회차를, 반복 전체(``series``)는
    회차가 아닌 예약을 거절한다."""
    if not mine_to_change(r, me_id):
        return "not_mine"
    if start == "booking" and is_series(r):
        return "series"
    if start == "series" and not r.get(SERIES_ID):
        return "single"
    return ""


def series_rows(app, r: dict) -> list:
    """그 회차와 같은 반복의 살아 있는 회차 — 내 예약에서 시작 차례로."""
    sid = r.get(SERIES_ID)
    return sorted((x for x in app.mine() if x.get(SERIES_ID) == sid and live(x)), key=lambda x: x["start_time"])


def series_key(rows: list) -> str:
    """반복 전체의 열쇠 — 회차마다의 줄 열쇠를 묶는다. 보인 뒤 회차 하나라도 바뀌거나 늘고 줄면 달라진다."""
    return fingerprint([row_key(x) for x in rows])


def workdays(first: date, last: date) -> list:
    """첫 날부터 끝 날까지의 업무일(월 ~ 금) — 앱은 여기서 공휴일을 더 뺀다."""
    out, d = [], first
    while d <= last:
        if d.weekday() < WEEKEND:
            out.append(d)
        d += timedelta(days=1)
    return out


def until_day(text: str) -> date:
    """``--until`` 의 날 — 꼴이 틀리면 Stop(인자)."""
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise Stop(EXIT_ARGS, "args", f"--until 은 YYYY-MM-DD 로 준다: {text!r}") from None


def series_took(app, rid: str, body: dict) -> bool:
    """반복 전체 고치기가 회차마다 섰나 — 살아 있는 회차 모두의 제목 · 설명 · 참석자가 보낸 몸통과 같다. 앱이 센 수가 아니라 다시
    읽은 줄로 가린다."""
    base = reread(app, rid)
    if base is None:
        return False
    want = ((body["title"] or "").strip(), body["user_description"] or "", sorted(a["email"].casefold() for a in body["attendees"]))
    return all(((x.get("title") or "").strip(), x.get("user_description") or "",
                sorted(a["email"].casefold() for a in kept_attendees(x))) == want for x in series_rows(app, base))


def kept_attendees(r: dict) -> list:
    out = []
    for a in r.get("attendees") or []:
        emp = a.get("employee_id")
        row = {"email": a.get("email") or "", "name": person(emp) or a.get("email") or ""}
        if isinstance(emp, dict) and emp.get("id"):
            row["employee_id"] = emp["id"]
        elif isinstance(emp, str) and emp:
            row["employee_id"] = emp
        out.append(row)
    return out


def row_key(r: dict) -> str:
    """예약 줄의 열쇠 — 그 줄이 보인 것(제목 · 시각 · 회의실 · 참석자 · 상태 · 설명)의 해시. 취소가 지금의 줄과 견준다. 앱이 저절로
    고치는 칸(Teams 링크 · 고친 시각)은 안 싣는다 — 넣은 직후 링크가 붙어도 열쇠가 그대로다."""
    return fingerprint(r.get("id"), r.get("title"), r.get("start_time"), r.get("end_time"), sorted(r.get("room_ids") or []),
                       sorted(a["email"].casefold() for a in kept_attendees(r)), r.get("status"), r.get("user_description"))


def teams_of(r: dict) -> dict:
    """예약 줄의 Teams 회의 — 들어가는 링크 · 회의 ID · 암호. 링크가 없으면 빈 dict."""
    t = r.get("teams_meeting") or {}
    if not t.get("join_url"):
        return {}
    return {k: t[src] for k, src in TEAMS_FIELDS.items() if t.get(src)}


def booking_row(r: dict, me_id: str = "", names: dict | None = None, *, people: bool = True, keyed: bool = True) -> dict:
    """사람에게 보일 예약 한 줄. ``people`` 이면 참석자(이름 · 메일)와 Teams 링크 · 회의 ID · 암호를, 아니면 Teams 가 붙었다는 것만
    싣는다 — 남의 회의까지 보이는 현황에 남의 회의 링크를 내지 않는다. ``keyed`` 면 내가 주관한 줄에 취소 key 를 싣는다 — 예약
    조회의 줄과 내 예약의 줄은 key 가 싣는 칸이 같아, 어느 줄에서 지어도 취소가 다시 읽은 줄과 맞는다."""
    s, e = parse_app(r["start_time"]), parse_app(r["end_time"])
    out = {"id": r["id"], "title": r.get("title", ""), "day": s.date().isoformat(), "when": when(s, e), "start": stamp(s), "end": stamp(e),
           "rooms": r.get("room_names") or [x.get("name") for x in r.get("rooms", [])] or [(names or {}).get(i, i) for i in r.get("room_ids", [])],
           "status": STATUS_WORDS.get(r.get("status"), r.get("status")), "organizer": person(r.get("organizer_id")),
           "mine": mine_to_change(r, me_id)}
    if people and r.get("attendees"):
        out["attendees"] = [{"name": a["name"], "email": a["email"]} for a in kept_attendees(r)]
    teams = teams_of(r)
    if teams:
        out["teams"] = teams if people else True
    if is_series(r):
        out["series"] = True              # 반복의 회차 — 전체를 다루려면 이 id 를 --series 로 준다
    if keyed and out["mine"]:
        out["key"] = row_key(r)
    return out


def reread(app, rid: str):
    """내 예약에서 그 id 의 살아 있는 예약 — 취소 · 거절된 줄은 없는 것으로 본다."""
    return next((r for r in app.mine() if r["id"] == rid and live(r)), None)


def addresses(values, files) -> list[str]:
    """``--to`` 같은 칸의 주소들 — 빈칸 · 쉼표 · 쌍반점으로 나눈 것도 받고, 파일은 한 줄에 하나(``#`` 뒤는 버린다). 같은 주소는 한 번."""
    chunks = list(values or ())
    for f in files or ():
        path = pathlib.Path(f).expanduser()
        if not path.is_file():
            raise Stop(EXIT_ARGS, "args", f"주소 파일이 없다: {path}")
        chunks += [line.split("#", 1)[0] for line in path.read_text(encoding="utf-8-sig").splitlines()]
    out, seen = [], set()
    for chunk in chunks:
        for a in ADDRESS_SPLIT.split(chunk):
            if a and a.casefold() not in seen:
                seen.add(a.casefold())
                out.append(a)
    return out


class Directory:
    """앱의 사람 목록 — 한 부름에서 한 번만 받는다(전사 목록이라 크다)."""

    def __init__(self, app):
        self.app, self.by_mail = app, None

    def resolve(self, emails: list[str]) -> tuple[list, list]:
        """메일 → 앱의 참석자 꼴과 못 찾은 주소. 같은 주소(대소문자 무시)의 한 사람만 잇는다."""
        if not emails:
            return [], []
        if self.by_mail is None:
            self.by_mail = {}
            for u in self.app.directory():
                self.by_mail.setdefault(str(u.get("email", "")).casefold(), u)
        got, missing = [], []
        for m in emails:
            u = self.by_mail.get(m.casefold())
            if u:
                got.append({"employee_id": u["id"], "email": u["email"], "name": person(u)})
            else:
                missing.append(m)
        return got, missing


def find_group(prefs: dict, name: str) -> dict:
    """내 참석자 그룹 하나 — 이름이 같은 것, 없으면 이름에 그 말이 든 것이 하나일 때. 없거나 여럿이면 Stop(인자)."""
    groups = prefs.get("attendee_groups") or []
    got = [g for g in groups if g.get("name") == name] or [g for g in groups if name.casefold() in str(g.get("name", "")).casefold()]
    if len(got) == 1:
        return got[0]
    have = " · ".join(str(g.get("name")) for g in groups) or "없다"
    many = "없다" if not got else f"{len(got)} 개 걸린다"
    raise Stop(EXIT_ARGS, "args", f"참석자 그룹 「{name}」이 {many} — 내 그룹: {have}. 다음: prefs 로 보인다")


def group_row(g: dict, book: Directory) -> dict:
    """사람에게 보일 그룹 — 사람마다 이름과 메일. 앱의 사람 목록에 없는 주소는 이름 없이 둔다."""
    emails = [m.get("email") or "" for m in g.get("members") or []]
    got, _ = book.resolve([e for e in emails if e])
    names = {a["email"].casefold(): a["name"] for a in got}
    return {"name": g.get("name", ""), "members": [{"name": names.get(e.casefold(), ""), "email": e} for e in emails]}


def attendees_plan(args, start: str, base: dict | None, me: dict, book: Directory) -> tuple[list, list, list]:
    """참석자 — (새 참석자, 막는 까닭, 알릴 것). 있던 예약 · 본뜨기의 참석자에서 출발해 --to 로 갈고, --add-to 로 더하고, --drop-to 로
    뺀다. 본뜨기는 나를 참석자에서 뺀다(새 예약의 주관자다)."""
    current = kept_attendees(base) if base else []
    blocks, notes = [], []
    if start == "copy":
        current = [a for a in current if a.get("employee_id") != me.get("id")]
        if not mine_to_change(base, me.get("id", "")):
            notes.append(f"원래 주관자({person(base.get('organizer_id'))})는 참석자에 안 든다 — 함께 부르려면 --add-to 로 그분 주소를 준다")
    unknown = []
    if args.to is not None or args.to_file is not None:
        current, lost = book.resolve(addresses(args.to, args.to_file))
        unknown += lost
    adds = addresses(getattr(args, "add_to", None), getattr(args, "add_to_file", None))
    if getattr(args, "group", None):
        members = [m.get("email") for m in find_group(book.app.prefs(), args.group).get("members") or [] if m.get("email")]
        adds += [m for m in members if m.casefold() != str(me.get("email", "")).casefold()]   # 주관자인 나는 참석자로 안 넣는다
    adds = list({a.casefold(): a for a in adds}.values())   # 따로 준 주소와 그룹이 같은 사람을 들면 한 번만 넣는다
    if adds:
        got, lost = book.resolve(adds)
        unknown += lost
        have = {a["email"].casefold() for a in current}
        current = current + [a for a in got if a["email"].casefold() not in have]
    drops = {d.casefold(): d for d in addresses(getattr(args, "drop_to", None), None)}
    if drops:
        have = {a["email"].casefold() for a in current}
        absent = [d for k, d in drops.items() if k not in have]
        if absent:
            blocks.append("지금 참석자에 없는 주소라 뺄 수 없다: " + ", ".join(absent) + " — mine · preview 의 attendees 주소를 준다")
        current = [a for a in current if a["email"].casefold() not in drops]
    if unknown:
        blocks.append("회의실 예약 앱의 사람 목록에 없는 주소: " + ", ".join(dict.fromkeys(unknown)) + f" — {UNKNOWN_NEXT}")
    return current, blocks, notes


def times(args, base: dict | None) -> tuple[datetime, datetime]:
    """시작 · 끝 — 있던 예약 · 본뜨기에 시작만 주면 길이를 그대로 두고, 끝만 주면 시작을 그대로 둔다."""
    s = kst(args.start) if args.start else None
    e = kst(args.end) if args.end else None
    if base is not None:
        bs, be = parse_app(base["start_time"]), parse_app(base["end_time"])
        if s is None and e is None:
            s, e = bs, be
        elif e is None:
            e = s + (be - bs)
        elif s is None:
            s = bs
    return s, e


def body_of(me: dict, room_ids: list, title: str, note: str, start: datetime, end: datetime, attendees: list, *,
            company: str = "", status: str = "confirmed", teams: str = "private") -> dict:
    """앱의 화면이 넣기 · 고치기에 보내는 꼴 그대로. 참석자는 ``employee_id`` · ``email`` 만 싣는다."""
    return {"company_id": company or me["company_id"], "organizer_id": me["id"], "title": title,
            "user_description": note, "start_time": iso(start), "end_time": iso(end),
            "attendees": [{k: a[k] for k in ("employee_id", "email") if a.get(k)} for a in attendees],
            "room_ids": room_ids, "status": status, "teams_link_visibility": teams}


# ── 판 — 미리 보기와 넣기 · 고치기가 같은 판을 다시 짓는다 ─────────────────────
def plan(app, args, me: dict, now: datetime, start: str) -> dict:
    """출발 하나에 바꿀 것을 넣은 한 건의 꼴과 막는 까닭 · 알릴 것 · 열쇠. 바꾸지 않는다."""
    rooms, places = app.rooms(), Places(app.hierarchy())
    base = None
    rid = getattr(args, STARTS[start].dest, None) if STARTS[start].takes else None
    if rid:
        base = reread(app, rid)
        if base is None:
            return {"state": "gone"}
        why = refusal(base, me["id"], start) if start in ("booking", "series") else ""
        if why:
            return {"state": "refused", "reason": why}
    rows = series_rows(app, base) if start == "series" else []
    if rows:
        base = rows[0]                    # 반복 전체는 첫 회차의 꼴로 짓는다 — 앱의 화면도 그 회차에서 연다
    room = one_room(rooms, places, args.room) if args.room else None
    room_ids = [room["id"]] if room else list(base.get("room_ids") or [])
    s, e = times(args, base)
    title = (args.title if args.title is not None else (base or {}).get("title", "")).strip()
    note = args.note if args.note is not None else (base or {}).get("user_description", "")
    attendees, blocks, notes = attendees_plan(args, start, base, me, Directory(app))
    if not title:
        blocks.append("제목이 비었다")
    if e <= s:
        blocks.append("끝이 시작보다 앞이다")
    if s < now and start != "series":
        blocks.append("지난 시각이다 — 회의실 예약 앱은 지난 시각도 받지만 여기서는 넣지 않는다")
    if start == "series" and any(parse_app(x["start_time"]) < now for x in rows):
        blocks.append("지난 회차가 든 반복이다 — 지난 회차까지 함께 바뀌는지 안 쟀다. 사람에게 회의실 예약 화면에서 하시라 권한다")
    days = []                             # 반복으로 넣을 회차의 날 — 비면 한 건이다
    if getattr(args, "until", None):
        last = until_day(args.until)
        days = workdays(s.date(), last)
        if s.date().weekday() >= WEEKEND:
            blocks.append("반복의 첫 날이 주말이다 — 앱은 업무일에만 회차를 세운다. 첫 업무일로 --start 를 준다")
        if last <= s.date():
            blocks.append("--until 이 첫 날보다 뒤여야 반복이다 — 한 번만이면 --until 없이 부른다")
        elif len(days) > MOST_OCCURRENCES:
            blocks.append(f"회차가 {len(days)} 개다 — {MOST_OCCURRENCES} 개를 넘으면 여기서 안 넣는다. --until 을 당기거나 화면에서 한다")
        else:
            notes.append(f"반복 — {len(days)} 회차(업무일). 공휴일에 걸린 회차는 앱이 빼서 실제로는 더 적을 수 있다")
    if start in ("booking", "series") and (title, note, s, e, room_ids, sorted(a["email"].casefold() for a in attendees)) == (
            base.get("title", "").strip(), base.get("user_description", ""), parse_app(base["start_time"]), parse_app(base["end_time"]),
            list(base.get("room_ids") or []), sorted(a["email"].casefold() for a in kept_attendees(base))):
        blocks.append("바뀐 것이 없다 — 고치면 참석자께 바뀐 안내만 간다")
    by_id = {r["id"]: r for r in rooms}
    for room_id in room_ids:
        r = by_id.get(room_id)
        if r is None:
            blocks.append(f"회의실 {room_id} 가 목록에 없다")
            continue
        row = room_row(r, places)
        if not row["bookable"]:
            blocks.append(f"{row['name']}: 일반 사용자가 예약할 수 없는 회의실이다")
        if cross_company(r, places, me):
            blocks.append(f"{row['name']}: 다른 회사 회의실이라 예약할 수 없다")
        if row["approval"]:
            notes.append(f"{row['name']}: 승인이 필요한 회의실 — 넣으면 「승인 대기」로 들어간다")
        if row["capacity"] and len(attendees) + 1 > row["capacity"]:
            notes.append(f"{row['name']}: 정원 {row['capacity']} 명인데 참석자가 주관자 포함 {len(attendees) + 1} 명이다")
        if row["teams_link"]:
            notes.append(f"{row['name']}: 이 회의실 정책으로 Teams 회의 링크가 저절로 붙는다")
    editing = args.id if start == "booking" else None
    own = {x["id"] for x in rows}       # 반복 전체를 고칠 때 제 회차는 겹침이 아니다
    spans = [(datetime.combine(d, s.timetz()), datetime.combine(d, s.timetz()) + (e - s)) for d in days] or [(s, e)]
    clash = []
    if e > s and start != "series":   # 반복 전체는 시각 · 회의실을 안 바꿔 새 겹침이 없다
        clash = [x for x in app.between(utc(spans[0][0]), utc(spans[-1][1])) if live(x) and x["id"] != editing and x["id"] not in own
                 and set(x.get("room_ids", [])) & set(room_ids) and any(overlaps(x, a, b) for a, b in spans)]
        for x in clash:
            blocks.append(f"그 시각에 이미 예약이 있다 — {when(parse_app(x['start_time']), parse_app(x['end_time']))} "
                          f"「{x.get('title', '')}」({person(x.get('organizer_id'))})")
        if not blocks:
            v = app.validate(room_ids, iso(s), iso(e), editing)
            blocks += [err.get("message", str(err)) for err in v.get("errors", [])]
            if v.get("approvalRequiredRoomIds") and not any("승인" in n for n in notes):
                notes.append("승인이 필요한 회의실이 들었다 — 넣으면 「승인 대기」로 들어간다")
    if not attendees:
        notes.append("참석자가 없다 — 회의실만 잡히고 누구에게도 안내가 안 간다")
    notes += [f"{c.word.split(' — ')[0]} 바꾸기는 {UNMEASURED} — 고친 뒤 다시 읽어 그대로 섰는지 보고, 아니면 「확인 못 했다」로 낸다"
              for c in CHANGES.values() if start in c.unmeasured and given(args, c)]
    held = base or {}
    body = body_of(me, room_ids, title, note, s, e, attendees, company=held.get("company_id", ""),
                   status=held.get("status", "confirmed") if start in ("booking", "series") else "confirmed",
                   teams=held.get("teams_link_visibility") or "private")
    if days:
        body.update(is_recurring=True, recurring_end_date=days[-1].isoformat())
    if rows:                              # 반복 전체 고치기 — 앱의 화면처럼 반복 칸을 첫 회차 ~ 끝 회차로 다시 싣는다
        body.update(is_recurring=True, recurring_end_date=parse_app(rows[-1]["start_time"]).date().isoformat())
    names = [f"{places.of(by_id[r])} {by_id[r]['name']}".strip() for r in room_ids if r in by_id]
    shown = [{"name": a["name"], "email": a["email"]} for a in attendees]
    view = {"state": "ready" if not blocks else "blocked", "ok": not blocks, "from": start, "title": title, "note": note,
            "day": s.date().isoformat(), "when": when(s, e), "start": stamp(s), "end": stamp(e), "rooms": names,
            "attendees": shown, "blocks": blocks, "notes": notes, "body": body}
    if days:
        view["occurrences"] = [f"{d:%m월 %d일}({WEEKDAYS[d.weekday()]})" for d in days]
    if rows:
        view["series"] = {"count": len(rows), "days": [booking_row(x, me["id"], keyed=False)["when"] for x in rows]}
    if start in ("booking", "series"):
        before = [{"name": a["name"], "email": a["email"]} for a in kept_attendees(base)]
        had, keeps = {a["email"].casefold() for a in before}, {a["email"].casefold() for a in shown}
        view["was"] = booking_row(base, me["id"])
        if rows:
            view["was"]["key"] = series_key(rows)   # 반복 전체 취소의 열쇠
        view["joining"] = [a for a in shown if a["email"].casefold() not in had]       # 새로 회의 안내가 가는 분
        view["leaving"] = [a for a in before if a["email"].casefold() not in keeps]    # 취소 안내가 가는 분
    if start == "copy":
        view["template"] = booking_row(base, me["id"], keyed=False)
    view["key"] = fingerprint(start, body, sorted(x["id"] + x.get("updated_at", "") for x in clash), held.get("updated_at"),
                              [x["id"] + x.get("updated_at", "") for x in rows])
    return view


def shown(p: dict) -> dict:
    """사람에게 보일 판 — 앱에 보낼 몸통(``body``)은 뺀다."""
    return {k: v for k, v in p.items() if k != "body" and v not in (None, [], "")}


def fit(out: dict, key: str, group, more) -> None:
    """답이 OUT_BYTES 를 넘으면 ``out[key]`` 의 뒤 무리부터 덜어 낸다 — 무리(``group``)를 가운데서 안 끊는다. 덜었으면 ``more(덜어 낸
    첫 무리)`` 가 이어 볼 길을 든다. 무리 하나만으로 넘치면 그 무리는 그대로 낸다."""
    groups = list(dict.fromkeys(group(x) for x in out[key]))
    while len(groups) > 1 and size(out, INDENT) > OUT_BYTES:
        cut = groups.pop()
        out[key] = [x for x in out[key] if group(x) != cut]
        out["cut"] = True
        out["more"] = more(cut)


def asked_day(text, today: date) -> date:
    """사람이 준 날 하나 — ``day_of`` 에 요일 · 「다음 주」를 어떻게 줄지를 덧붙여 Stop(인자)."""
    try:
        return day_of(text, today)
    except Stop as exc:
        raise Stop(EXIT_ARGS, "args", f"{exc}. 다음: {DAY_COUNT}") from exc


def mine_days(args, today: date) -> tuple[date, date]:
    """mine 의 첫날 · 끝날 — 첫날을 안 주면 오늘, 끝날을 안 주면 첫날부터 ``MINE_DAYS`` 날. 끝날이 첫날보다 앞이면 Stop(인자)."""
    first = asked_day(args.first, today)
    last = asked_day(args.last, today) if args.last else first + timedelta(days=MINE_DAYS)
    if last < first:
        raise Stop(EXIT_ARGS, "args", f"끝날({last})이 첫날({first})보다 앞이다 — mine <첫날> <끝날> 차례로 준다")
    return first, last


def favorites_only(app, args, rooms: list) -> list:
    """``--favorites`` 면 즐겨찾는 회의실만 — 즐겨찾기가 비었으면 Stop(인자)."""
    if not getattr(args, "favorites", False):
        return rooms
    fav = set(app.prefs().get("favorite_rooms") or [])
    if not fav:
        raise Stop(EXIT_ARGS, "args", "즐겨찾는 회의실이 없다. 다음: --favorites 없이 부르거나 pref --favorite <회의실> 로 넣는다")
    return [r for r in rooms if r["id"] in fav]


# ── 내 설정 바꾸기 ────────────────────────────────────────────────────────
def pref(app, args) -> dict:
    """내 설정 하나를 미리 보이거나(``--confirm`` 없음) 그 열쇠로 바꾼다. 열쇠는 할 일 · 보낼 몸통 · 지금 설정의 고친 시각의 해시라,
    보인 뒤 설정이 바뀌었으면 ``moved`` 로 안 바꾼다. 바꾼 뒤는 앱이 낸 설정 전체에서 섰나를 가린다."""
    picked = [k for k in PREF_ACTIONS if getattr(args, k, None) is not None]
    if len(picked) != 1:
        raise Stop(EXIT_ARGS, "args", f"pref 는 하나씩 한다 — {' · '.join(f for f, _ in PREF_ACTIONS.values())} 가운데 하나")
    action, value = picked[0], getattr(args, picked[0])
    prefs, book = app.prefs(), Directory(app)
    if action in ("favorite", "unfavorite"):
        places = Places(app.hierarchy())
        room = one_room(app.rooms(), places, value)
        on = action == "favorite"
        if (room["id"] in (prefs.get("favorite_rooms") or [])) == on:
            return {"state": "blocked", "state_word": STATE_WORDS["blocked"],
                    "blocks": [f"{room['name']} 은 이미 즐겨찾기에 {'있다' if on else '없다'}"]}
        view = {"do": PREF_ACTIONS[action][1].split(" — ")[0], "room": room_row(room, places)}
        body = room["id"]

        def work():
            return app.favorite(room["id"], on)

        def check(got):
            return (room["id"] in (got.get("favorite_rooms") or [])) == on
    elif action == "save_group":
        got, lost = book.resolve(addresses(args.to, args.to_file))
        if lost:
            raise Stop(EXIT_ARGS, "args", "회의실 예약 앱의 사람 목록에 없는 주소: " + ", ".join(lost) + f" — {UNKNOWN_NEXT}")
        if not got:
            raise Stop(EXIT_ARGS, "args", "그룹에 넣을 사람을 --to · --to-file 로 준다")
        old = next((g for g in prefs.get("attendee_groups") or [] if g.get("name") == value), None)
        body = {"name": value, "members": [{"employee_id": a["employee_id"], "email": a["email"]} for a in got]}
        view = {"do": "참석자 그룹 고치기" if old else "참석자 그룹 짓기",
                "group": {"name": value, "members": [{"name": a["name"], "email": a["email"]} for a in got]}}
        if old:
            view["was"] = group_row(old, book)
        want = sorted(a["email"].casefold() for a in got)

        def work():
            return app.put_group(old["id"], body) if old else app.add_group(body)

        def check(back):
            return any(g.get("name") == value and sorted(m.get("email", "").casefold() for m in g.get("members") or []) == want
                       for g in back.get("attendee_groups") or [])
    else:
        g = find_group(prefs, value)
        body = g.get("id")
        view = {"do": "참석자 그룹 지우기", "group": group_row(g, book)}

        def work():
            return app.drop_group(g["id"])

        def check(back):
            return all(x.get("id") != g["id"] for x in back.get("attendee_groups") or [])
    key = fingerprint(action, body, prefs.get("updated_at"))
    if args.confirm is None:
        return {"state": "ready", "ok": True, **view, "key": key}
    if args.confirm != key:
        return {"state": "moved", "state_word": STATE_WORDS["moved"], "preview": {**view, "key": key}}
    back = work()
    state = "saved" if isinstance(back, dict) and check(back) else "unsure"
    return {"state": state, "state_word": STATE_WORDS[state], **view}


# ── 읽기 ────────────────────────────────────────────────────────────────
def read(app, args, now: datetime) -> dict:
    today = now.date()
    if args.command == "prefs":
        prefs, book = app.prefs(), Directory(app)
        places = Places(app.hierarchy())
        by_id = {r["id"]: r for r in app.rooms()}
        return {"favorites": [room_row(by_id[i], places) if i in by_id else {"id": i, "name": "(목록에 없는 회의실)"}
                              for i in prefs.get("favorite_rooms") or []],
                "groups": [group_row(g, book) for g in prefs.get("attendee_groups") or []]}
    if args.command == "rooms":
        places = Places(app.hierarchy())
        got = [room_row(r, places) for r in favorites_only(app, args, find_rooms(app.rooms(), places, args.word))]
        return {"count": len(got), "rooms": got[:MOST_ROOMS], "cut": len(got) > MOST_ROOMS}
    me = app.me()
    if args.command == "free":
        start, end = kst(args.start), kst(args.end)
        if end <= start:
            raise Stop(EXIT_ARGS, "args", "끝이 시작보다 앞이다")
        places = Places(app.hierarchy())
        cand = [r for r in favorites_only(app, args, find_rooms(app.rooms(), places, args.where))
                if room_row(r, places)["bookable"] and not cross_company(r, places, me)
                and (not args.people or (r.get("capacity") or 0) >= args.people)]
        booked = [x for x in app.between(utc(start), utc(end)) if live(x) and overlaps(x, start, end)]
        if not args.minutes:
            busy = {rid for x in booked for rid in x.get("room_ids", [])}
            free = [room_row(r, places) for r in cand if r["id"] not in busy]
            out = {"when": when(start, end), "count": len(free), "rooms": free[:MOST_FREE], "cut": len(free) > MOST_FREE}
        else:
            lo = max(start, now)          # 지난 시각은 비었어도 잡지 않는다
            rows = []
            for r in cand:
                held = [(parse_app(x["start_time"]), parse_app(x["end_time"])) for x in booked if r["id"] in x.get("room_ids", [])]
                gaps = gaps_of(held, lo, end, timedelta(minutes=args.minutes)) if lo < end else []
                if gaps:
                    rows.append({**room_row(r, places), "gaps": [{"start": stamp(a), "end": stamp(b), "when": when(a, b)} for a, b in gaps]})
            rows.sort(key=lambda x: (x["gaps"][0]["start"], x["name"]))
            out = {"within": when(start, end), "minutes": args.minutes, "count": len(rows), "rooms": rows[:MOST_FREE],
                   "cut": len(rows) > MOST_FREE}
        fit(out, "rooms", lambda x: x["id"], lambda _: "다음: 뒤의 회의실은 안 실었다 — --where 낱말을 좁혀 다시 부른다")
        return out
    if args.command == "day":
        d = asked_day(args.date, today)
        places = Places(app.hierarchy())
        hit = find_rooms(app.rooms(), places, args.words)
        if not hit:
            raise Stop(EXIT_ARGS, "args", f"「{' '.join(args.words)}」에 걸리는 회의실이 없다(날은 --date 로 준다). 다음: rooms 로 찾아 보인다")
        a, b = day_span(d, d)
        lo, hi = datetime.combine(d, datetime.min.time(), KST), datetime.combine(d + timedelta(days=1), datetime.min.time(), KST)
        booked = sorted((x for x in app.between(a, b) if live(x) and overlaps(x, lo, hi)), key=lambda x: x["start_time"])
        def cell(x: dict, r: dict) -> dict:   # 내가 주관한 줄만 참석자 · 취소 key 를 싣는다 — 취소 확인에 참석자를 보인다
            own = mine_to_change(x, me["id"])
            return booking_row(x, me["id"], {r["id"]: r["name"]}, people=own, keyed=own)

        grid = [{**room_row(r, places), "bookings": [cell(x, r) for x in booked if r["id"] in x.get("room_ids", [])]}
                for r in hit[:MOST_GRID]]
        out = {"day": d.isoformat(), "weekday": WEEKDAYS[d.weekday()], "count": len(hit), "rooms": grid, "cut": len(hit) > MOST_GRID}
        fit(out, "rooms", lambda x: x["id"], lambda _: "다음: 뒤의 회의실은 안 실었다 — 낱말을 좁혀(지역 · 건물 · 층 · 이름) 다시 부른다")
        return out
    first, last = mine_days(args, today)
    lo = datetime.combine(first, datetime.min.time(), KST)
    hi = datetime.combine(last + timedelta(days=1), datetime.min.time(), KST)
    rows = sorted((x for x in app.mine() if overlaps(x, lo, hi)), key=lambda x: x["start_time"])
    out = {"today": today.isoformat(), "today_weekday": WEEKDAYS[today.weekday()], "first": first.isoformat(),
           "last": last.isoformat(), "bookings": [booking_row(x, me["id"]) for x in rows]}
    fit(out, "bookings", lambda x: x["day"], lambda cut: f"다음: {cut} 부터는 안 실었다 — mine {cut} {last.isoformat()} 로 이어 본다")
    return out


# ── 바꾸기 ──────────────────────────────────────────────────────────────
def cancel(app, args, me: dict, start: str) -> dict:
    rid = args.series if start == "series" else args.id
    base = reread(app, rid)
    if base is None:
        return {"state": "gone", "state_word": STATE_WORDS["gone"]}
    why = refusal(base, me["id"], start)
    if why:
        return {"state": "refused", "reason": why, "state_word": REFUSE_WORDS[why]}
    if start == "series":
        return cancel_series(app, args, me, base)
    if row_key(base) != args.confirm:
        return {"state": "moved", "state_word": STATE_WORDS["moved"], "booking": booking_row(base, me["id"])}
    app.delete(args.id)
    try:
        state = "cancelled" if reread(app, args.id) is None else "unsure"
    except Exception:  # noqa: BLE001 — 지운 뒤라 어떤 실패도 다시 부를 까닭이 아니다
        state = "unsure"
    return {"state": state, "state_word": STATE_WORDS[state], "booking": booking_row(base, me["id"], keyed=False)}


def cancel_series(app, args, me: dict, base: dict) -> dict:
    """반복 전체 취소 — 보인 판(회차 모두의 열쇠)과 같을 때만 지우고, 그 반복의 회차가 내 예약에서 다 사라졌나 다시 읽어 가린다."""
    rows = series_rows(app, base)
    head = booking_row(rows[0], me["id"], keyed=False)
    if series_key(rows) != args.confirm:
        return {"state": "moved", "state_word": STATE_WORDS["moved"], "booking": {**head, "key": series_key(rows)},
                "series": {"count": len(rows)}}
    if any(parse_app(x["start_time"]) < datetime.now(KST) for x in rows):
        return {"state": "blocked", "state_word": STATE_WORDS["blocked"],
                "blocks": ["지난 회차가 든 반복이다 — 지난 회차까지 함께 지워지는지 안 쟀다. 사람에게 회의실 예약 화면에서 하시라 권한다"]}
    got = app.delete_series(base["id"]) or {}
    try:
        left = series_rows(app, base)
    except Exception:  # noqa: BLE001 — 지운 뒤라 어떤 실패도 다시 부를 까닭이 아니다
        left = None
    state = "cancelled" if left == [] else "unsure"
    return {"state": state, "state_word": STATE_WORDS[state], "booking": head,
            "series": {"count": len(rows), "deleted": got.get("deletedCount"), "left": None if left is None else len(left)}}


def settle(app, start: str, me: dict, rid: str | None, rooms: list | None = None) -> dict:
    """바꾼 뒤의 끝 — 앱이 받은 뒤라 다시 읽기가 무엇으로 지든 「모른다」다. 세션 · 도구 오류로 올리면 다시 부르라는 말이 되어 두 번 든다.
    고치기는 보낸 회의실(``rooms``)이 다시 읽은 줄에 섰는지도 본다 — 고치기에서 회의실을 바꾸는 판은 회사에서 안 쟀다."""
    try:
        back = reread(app, rid) if rid else None
    except Exception:  # noqa: BLE001 — 바꾼 뒤라 어떤 실패도 다시 부를 까닭이 아니다
        back = None
    if back is None:
        return {"state": "unsure", "state_word": STATE_WORDS["unsure"]}
    if start == "booking" and rooms is not None and sorted(back.get("room_ids") or []) != sorted(rooms):
        return {"state": "unsure", "state_word": STATE_WORDS["unsure"], "booking": booking_row(back, me["id"])}
    state = "updated" if start in ("booking", "series") else ("pending" if back.get("status") == "pending_approval" else "booked")
    return {"state": state, "state_word": STATE_WORDS[state], "booking": booking_row(back, me["id"])}


def run(args, session: pathlib.Path) -> dict:
    mrs = load("mrs", HERE)
    app = mrs.App(session)
    now = datetime.now(KST)
    if args.command in READS:
        return read(app, args, now)
    if args.command == "pref":
        return pref(app, args)
    start = fingers(args)
    me = app.me()
    if args.command == "cancel":
        return cancel(app, args, me, start)
    p = plan(app, args, me, now, start)
    if p["state"] == "gone":
        return {"state": "gone", "state_word": STATE_WORDS["gone"]}
    if p["state"] == "refused":
        return {"state": "refused", "reason": p["reason"], "state_word": REFUSE_WORDS[p["reason"]]}
    if args.command == "preview":
        return shown(p)
    if p["key"] != args.confirm:
        return {"state": "moved", "state_word": STATE_WORDS["moved"], "preview": shown(p)}
    if not p["ok"]:
        return {"state": "blocked", "state_word": STATE_WORDS["blocked"], "blocks": p["blocks"]}
    held = args.series if start == "series" else args.id if start == "booking" else None
    try:
        if start == "series":
            got = app.update_series(held, p["body"])
        else:
            got = app.update(held, p["body"]) if start == "booking" else app.create(p["body"])
    except mrs.AppError as exc:
        if exc.status is not None:   # 앱이 답으로 거절했다 — 안 바뀌었다
            raise
        # 답 전에 끊겼다 — 들어갔을 수 있어 다시 부르지 않고 읽어 본다
        return settle(app, start, me, held, p["body"]["room_ids"])
    got = got if isinstance(got, dict) else {}
    made = got.get("reservations")        # 반복 넣기의 답은 회차들을 감싼다 · 한 건은 예약 그대로다
    first = made[0] if made else got
    out = settle(app, start, me, first.get("id") or held, p["body"]["room_ids"])
    if made is not None:
        out["series"] = {"asked": len(p.get("occurrences") or []), "made": len(made)}
    if start == "series":
        out["series"] = {"count": p["series"]["count"], "updated": got.get("updatedCount")}
        if out["state"] == "updated":
            try:
                took = series_took(app, held, p["body"])
            except Exception:  # noqa: BLE001 — 바꾼 뒤라 어떤 실패도 다시 부를 까닭이 아니다
                took = False
            if not took:
                out.update(state="unsure", state_word=STATE_WORDS["unsure"])
    return out


def parser() -> argparse.ArgumentParser:
    raw = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(description="회의실 예약 — 보기 · 넣기 · 고치기 · 본떠 넣기 · 취소", epilog=finger_map(), formatter_class=raw)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("rooms", help=READS["rooms"])
    r.add_argument("word", nargs="*", help="이름 · 지역 · 건물 · 층의 일부(빈칸으로 여럿)")
    r.add_argument("--favorites", action="store_true", help="즐겨찾는 회의실만")
    f = sub.add_parser("free", help=READS["free"])
    f.add_argument("--start", required=True, help=STAMP_HELP)
    f.add_argument("--end", required=True, help=STAMP_HELP)
    f.add_argument("--minutes", type=int, help="이만큼 넘게 비는 때를 그 구간 안에서 찾는다")
    f.add_argument("--where", nargs="*", help="지역 · 건물 · 층 · 이름의 일부")
    f.add_argument("--people", type=int, help="주관자 포함 인원 — 정원이 이보다 작은 곳은 뺀다")
    f.add_argument("--favorites", action="store_true", help="즐겨찾는 회의실만")
    d = sub.add_parser("day", help=READS["day"])
    d.add_argument("words", nargs="*", help="지역 · 건물 · 층 · 이름의 일부(다 든 회의실들)")
    d.add_argument("--date", help=f"{' · '.join(DAY_WORDS)} · YYYY-MM-DD(기본 오늘). {DAY_COUNT}")
    m = sub.add_parser("mine", help=READS["mine"])
    m.add_argument("first", nargs="?", metavar="첫날", help=f"{' · '.join(DAY_WORDS)} · YYYY-MM-DD(기본 오늘). {DAY_COUNT}")
    m.add_argument("last", nargs="?", metavar="끝날", help=f"첫날과 같은 꼴 — 주면 첫날부터 그날까지(둘 다 든다), 안 주면 첫날부터 {MINE_DAYS} 날")
    sub.add_parser("prefs", help=READS["prefs"])
    pr = sub.add_parser("pref", help="⚠ 내 설정 하나 바꾸기 — --confirm 없이 부르면 미리 보기 · key, 그 key 로 다시 부르면 바꾼다")
    for k, (flag, word) in PREF_ACTIONS.items():
        pr.add_argument(flag, dest=k, default=None, help=word)
    pr.add_argument("--to", nargs="*", default=None, help="그룹의 사람 — 메일 주소(빈칸 · 쉼표로 여럿)")
    pr.add_argument("--to-file", nargs="*", default=None, help="그룹의 사람 — 주소 파일(한 줄에 하나)")
    pr.add_argument("--confirm", default=None, help="미리 본 key — 주면 바꾼다")
    for name in ("preview", *ENDS):
        a = sub.add_parser(name, help="넣을 · 고칠 꼴 미리 보기 · key(바꾸지 않는다)" if name == "preview" else f"⚠ {ENDS[name].word}",
                           epilog=finger_map(), formatter_class=raw)
        for s in STARTS.values():
            if s.takes:
                a.add_argument(s.takes, default=None, help=f"출발 — {s.word}")
        if name == "preview" or ENDS[name].changes:
            for c in CHANGES.values():
                for flag, extra in c.flags:
                    a.add_argument(flag, default=None, **{"help": c.word, **extra})
            for n in NOT_YET.values():
                for flag, extra in n.flags:
                    a.add_argument(flag, default=None, **{"help": f"아직 없다 — {n.word}", **extra})
        if name != "preview":
            a.add_argument("--confirm", required=True, help=ENDS[name].key)
    return p


def main() -> int:
    args = parser().parse_args()

    def work(mrs):
        today = datetime.now(KST).date()
        if args.command == "mine":
            mine_days(args, today)       # 날이 틀렸으면 세션을 받기 전에 멈춘다
        if args.command == "day":
            asked_day(args.date, today)
        if args.command in ("preview", *ENDS):
            fingers(args)                # 없는 손가락 · 빠진 값은 세션을 받기 전에 멈춘다
            if getattr(args, "until", None):
                until_day(args.until)
        return ep_session.session_first(lambda f: run(args, f), expired=(mrs.SessionExpired, mrs.SessionMissing),
                                        file_first=args.command not in MUTATING)

    return ep_command.finish(work, "mrs", HERE, indent=INDENT)


if __name__ == "__main__":
    sys.exit(main())
