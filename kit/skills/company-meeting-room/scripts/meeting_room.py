"""회의실 예약 스킬의 얇은 명령 — 곁의 손(``mrs.py``)으로 회의실 · 빈 곳 · 예약 현황 · 내 예약을 보고, 예약 한 건을 넣고 · 고치고 ·
본떠 넣고 · 취소한다.

부르는 꼴::

    python -X utf8 -I meeting_room.py --help     # 지도 — 출발 × 바꿀 것 × 끝 · 읽기. 아래 표(STARTS · CHANGES · ENDS · READS)에서 짓는다
    python -X utf8 -I meeting_room.py rooms [말 …]
    python -X utf8 -I meeting_room.py free  --start S --end E [--minutes N] [--where 말 …] [--people N]
    python -X utf8 -I meeting_room.py day   [말 …] [--date 오늘|내일|YYYY-MM-DD]
    python -X utf8 -I meeting_room.py mine  [오늘|YYYY-MM-DD] [끝 날]
    python -X utf8 -I meeting_room.py preview [--id 예약 | --copy 예약] [--room R] [--title T] [--start S] [--end E] [--note N]
                                              [--to 메일 …] [--to-file 파일 …] [--people-file people.json …]
                                              [--add-to 메일 …] [--add-to-file 파일 …] [--drop-to 메일 …]
    python -X utf8 -I meeting_room.py book    [--copy 예약] …preview 와 같은 값… --confirm <preview 의 key>   # ⚠ 넣는다
    python -X utf8 -I meeting_room.py change  --id 예약 …preview 와 같은 값… --confirm <preview 의 key>       # ⚠ 고친다
    python -X utf8 -I meeting_room.py cancel  --id 예약 --confirm <mine 이 낸 그 줄의 key>                    # ⚠ 취소한다

    시각은 다 서울 벽시계 ``YYYY-MM-DD HH:MM`` 이고, 답의 ``start`` · ``end`` 도 그 꼴이라 그대로 다음 명령(이 스킬 · 회사 일정)에 준다.
    참석자는 메일 주소로 준다 — 사람은 스킬 company-directory 의 find 로 정하고, 그 --out 이 쓴 주소 파일(한 줄에 하나 · ``#`` 뒤는 버린다)을
    ``--to-file`` 로, 주소록이 쓴 사람 파일(people.json)은 ``--people-file`` 로 그대로 준다.

한 번 부름이 예약 한 건을 한 번 다룬다 — 출발 하나(새 예약 · 내 예약 한 건 · 본뜰 예약)에 바꿀 것을 아무 조합으로 주고 끝 하나로
맺는다. 넣기 · 고치기 · 취소는 참석자에게 회사 메일로 안내가 가 되돌릴 수 없어, 한 건을 여러 번에 나눠 바꾸지 않는다(부를 때마다
안내가 간다). 없는 손가락을 주면 그 일을 어디서 하는지 대며 종료 2 로 멈춘다.

하는 일 — 형제 스킬 ep-login 의 ``ep_session.session_first`` 로 사내 세션을 쥐고(보기는 있는 파일부터, 바꾸기는 늘 받는 손부터
한 번만), 그 세션으로 회의실 예약 앱의 출입증을 받아 부른다. 판단(무엇을 넣을까 · 사람이 확인했나)은 여기 없다 — 바꾸는 명령은
사람이 그 한 건을 확인한 뒤에만 부르고, 열쇠가 그 확인을 손 안에서 지킨다: preview 와 넣기 · 고치기는 같은 판(``plan``)을 짓고 그
해시가 key 라, 보인 뒤 무엇이든 달라졌으면 안 바꾼다. 취소의 key 는 mine 이 보인 그 줄의 해시다. 앱의 미리 검사는 정책만 보아,
겹침 · 지난 시각은 여기서 가린다.

내는 것 — 표준 출력에 JSON 하나. 종료 값과 그 뜻은 맨 위 ``--help`` 의 범례(``EXITS`` — ``ep_command.exit_legend``)가 낸다.
preview 는 ``state``(ready · blocked) · ``blocks``(못 하는 까닭) · ``notes``(할 수는 있으나 사람이 알아야 할 것) ·
``key`` 를, 바꾸는 명령은 ``state`` 와 사람에게 할 말 · 다음 걸음이 든 ``state_word`` 를 낸다. 예약 줄의 ``attendees`` 는 이름과 메일
주소, ``teams`` 는 Teams 링크 · 회의 ID · 암호(현황 ``day`` 의 남의 줄은 붙었다는 것만)다. 취소 ``key`` 는 내가 주관한 줄(mine ·
day · preview 의 was · 넣기 · 고치기의 답)에만 선다.
"""

from __future__ import annotations

import argparse
import functools
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    from ep_command import (DAY_HELP, EXIT_ARGS, EXIT_OK, EXIT_SESSION, EXIT_TOOL, OUT_BYTES, SEOUL as KST, STAMP_HELP, WEEKDAYS, Change, NotYet,
                            Start, Stop, day_of, gaps_of, given, load, size, stamp, stamp_of as kst)   # 시각의 꼴은 일정 손과 한 벌 — 일정의 show --free 답을 free · preview 가 받는다
except ImportError:                             # 형제 스킬 ep-login 이 곁에 없다 — 답의 꼴(JSON 하나 · 종료 1)은 지킨다
    print(json.dumps({"error": "tool", "message": f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"}, ensure_ascii=False))
    sys.exit(1)

MINE_DAYS = 14                            # mine 의 기본 구간 — 오늘부터 두 주
MOST_ROOMS = 60                           # rooms 답에 싣는 회의실 수 — count 는 다 센 수다
MOST_FREE = 40                            # free 답에 싣는 빈 회의실 수
# free --minutes 의 비는 때는 방의 것뿐이다 — 이 손은 누구의 일정도 안 보니, 때를 고르는 쪽이 사람들의 비는 때와 견줄 자리를 함께 댄다
ROOM_GAPS_ONLY = ("gaps 는 방이 비는 때뿐이다 — 사용자 본인과 참석자의 일정은 이 손이 안 본다. 때를 고르려면 스킬 company-calendar 의 "
                  "show <날> --who <참석자> --free <분> --hours <구간>(본인 일정도 함께 센다)의 비는 때와 견줘 둘 다 비는 때를 고른다")
MOST_GRID = 30                            # day 답에 싣는 회의실 수 — 한 회의실의 그날 예약이 한 묶음이다
MOST_CANDIDATES = 15                      # 회의실이 여럿 걸릴 때 message 에 보이는 후보 수
LIVE = ("confirmed", "pending_approval")  # 회의실을 쥔 예약의 상태 — cancelled · rejected 는 비운 것이다
STATUS_WORDS = {"confirmed": "확정", "pending_approval": "승인 대기", "cancelled": "취소됨", "rejected": "거절됨"}
INDENT = 1
TEAMS_FIELDS = {"link": "join_url", "meeting_id": "meeting_id", "passcode": "meeting_password"}   # 답의 이름 → 예약 줄 teams_meeting 의 칸
SERIES_ID = "recurring_id"                # 반복의 회차를 묶는 칸
WEEKEND = 5                               # weekday() 가 이 값부터 토 · 일이다 — 반복 회차는 그 앞 날에만 선다
MOST_OCCURRENCES = 120                    # 반복 미리 보기가 회차마다 겹침을 보는 수 — 넘으면 막고 끝 날을 당기라 한다
# 주소를 가르는 글자 — 빈칸 · 쉼표 · 쌍반점. 주소 파일은 회사 메일 스킬이 쓰는 꼴(한 줄에 하나 · # 뒤는 버린다 · 앞에 BOM 이 올 수 있다)
ADDRESS_SPLIT = re.compile(r"[,;\s]+")
UNKNOWN_NEXT = ("회의 참석자는 사람 한 명씩이다 — 부서 주소(dept_…)면 스킬 company-directory 의 find --dept <부서> --out <폴더> 로 부서원 주소 파일을 받아 "
                "--to-file · --add-to-file 로 주고, 사외 주소는 여기서 넣지 않는다")
SCREEN = "https://mrs.posco.net/scheduler"   # 사람이 쓰는 회의실 예약 화면 — 아직 없는 손가락을 거기서 하시라 권한다
UNMEASURED = "회사에서 안 쟀다"             # 지은 손가락 가운데 회사에서 그 판을 아직 안 잰 자리의 표시 — --help 와 preview 의 notes 가 같은 말을 쓴다


# ── 손가락의 표 — 출발 × 바꿀 것 × 끝. 손가락을 더하거나 빼는 일은 이 표의 줄과 그 일을 하는 손 하나다(칸의 꼴은 ep_command) ──────
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
IN_PLACE = ("booking", "series")          # 있던 예약을 그 자리에서 다룬다(고치기 · 취소의 출발) — 새 예약이 서지 않는다
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
    "to": Change((("--to", {"nargs": "*"}), ("--to-file", {"nargs": "*"}),
                  (ep_command.PEOPLE_FLAG, {"action": "append", "metavar": "파일",
                                            "help": f"{ep_command.PEOPLE_HELP} — 사람마다 그 메일 주소로 참석자에 넣는다(주관자인 나는 뺀다)"})), ALL,
                 "참석자 — 메일 주소(빈칸 · 쉼표로 여럿, 파일은 한 줄에 하나) · 주소록의 사람 파일. 있던 예약 · 본뜨기의 참석자를 이 사람들로 "
                 "통째로 간다"),
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
    "change": End("고치기", IN_PLACE, "--confirm <preview --id · --series 의 key>"),
    "cancel": End("취소", IN_PLACE, "--confirm <그 줄의 key> — mine 과 preview --id 의 was 가 내가 주관한 줄마다 낸다. "
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
# 이 명령이 내는 종료 값 — 뜻은 ep_command 의 한 표, 여기는 이 손이 덧붙일 말만. 「보인 판과 다르다」는 종료 값이 아니라 0 의 state moved 다
EXITS = ep_command.exit_legend((EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION),
                               {EXIT_OK: "넣기 · 고치기 · 취소 · 내 설정 바꾸기가 보인 판과 달라 안 했으면 0 에 state moved — 답의 지금 판을 다시 보인다",
                                EXIT_ARGS: "없는 손가락 · 빠진 값이면 어디서 하나나 받는 꼴을, 회의실이 여럿 걸리면 후보를 댄다"})

# 바꾸는 명령의 끝 — 낱말 하나가 뜻 하나다(형제 스킬 company-calendar 의 같은 낱말과도 같은 뜻)
STATE_WORDS = {
    "booked": "예약했습니다(내 예약에서 다시 읽어 확인했습니다). 참석자께는 회의 안내가 회사 메일로 갑니다 — 조금 걸릴 수 있습니다. "
              "회사 일정의 Teams 일정함에도 「[회의실 예약] 제목」 줄이 저절로 든다 — 일정 손으로 따로 넣거나 확인하지 않는다. "
              "다음: 이 줄의 id · key 를 들고 있다가 「방금 것 취소 · 시간 바꿔 줘」에 쓴다",
    "pending": "넣었지만 이 회의실은 승인이 필요해 「승인 대기」입니다 — 승인되면 확정됩니다",
    "updated": "고쳤습니다(다시 읽어 확인했습니다). 참석자께는 바뀐 안내가 갑니다",
    "cancelled": "취소했습니다(내 예약에서 사라진 것을 확인했습니다). 참석자께는 취소 안내가 갑니다. 회사 일정의 Teams 일정함의 "
                 "「[회의실 예약]」 줄도 함께 사라진다 — 일정 손으로 따로 지우거나 확인하지 않는다",
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



# ── 표에서 짓는 것 — 지도 · 인자 거르기 ────────────────────────────────────────────────────────────
def common_steps() -> str:
    """맨 위 --help 의 머리 — 자주 쓰는 길을 그대로 칠 수 있는 꼴로, 그리고 오늘과 날짜 표. 요일로 말한 날을 모델이 고르는 자리다."""
    return "\n".join([
        f"회의실 예약 — 보기 · 넣기 · 고치기 · 본떠 넣기 · 취소. {ep_command.today_word()}", "",
        "자주 쓰는 길 — 그대로 쳐서 쓴다(<…> 만 갈아 끼운다)",
        "  비는 회의실   free --start \"<날> HH:MM\" --end \"<날> HH:MM\" [--where <건물 · 층>] [--people <인원>] [--favorites]",
        "  때가 뭉뚱그려졌으면  free … --minutes <분> — 그 구간 안에서 그만큼 비는 방과 때(사람들의 일정은 company-calendar 의 show --free)",
        "  잡기          preview --room <free 의 id> --title <제목> --start … --end … --people-file <people.json>  →  book …같은 값… --confirm <key>",
        "  옮기기        mine 의 id → preview --id <id> --start \"<날> HH:MM\"  →  change …같은 값… --confirm <key>",
        "  더하고 빼기   preview --id <id> --add-to <메일> --drop-to <메일>  →  change …같은 값… --confirm <key>",
        "  취소          cancel --id <id> --confirm <mine 의 그 줄 key>",
        f"  날은 {DAY_HELP} · 시각은 \"<날> HH:MM\"(「내일 15:00」) — 답의 when 으로 사람이 바로잡게 보인다",
        f"  요일로 말한 날은 어느 날인지 정해 날짜로 준다(손이 고르지 않는다) — 날짜 표: {ep_command.weeks_word(datetime.now(ep_command.SEOUL).date())}",
        "  넣은 · 취소한 예약은 회사 일정의 Teams 일정함에 저절로 서고 사라진다 — 일정 손으로 따로 넣거나 확인하지 않는다"])


def finger_map() -> str:
    """--help 의 지도 — 표 넷에서 짓는다."""
    names = list(STARTS)
    lines = ["지도 — 출발 하나 × 바꿀 것 아무 조합 × 끝 하나. 한 번 부름이 예약 한 건을 한 번 다룬다", "", "출발"]
    lines += [f"  {k:<8} {s.takes + ' <id>' if s.takes else '(인자 없음)':<12} {s.word} — {s.screen}" for k, s in STARTS.items()]
    lines += ["", f"바꿀 것 (● 꼭 든다 · ○ 받는다 · △ 받되 {UNMEASURED} · — 없다)"]
    lines += ep_command.change_lines(CHANGES, names, 28, f"그 판은 {UNMEASURED} — preview 의 notes 로 사람에게 알리고, 고친 뒤 "
                                                         "다시 읽어 그대로 섰는지 본다")
    lines += ["", "끝 (⚠ 참석자에게 회사 메일로 안내가 가고 되돌릴 수 없다 — 사람이 그 한 건을 보고 「네」 한 뒤에만)"]
    lines += [f"  {k:<7} 출발 {' · '.join(e.starts):<12} {e.word} — 열쇠: {e.key}" + ("" if e.changes else " · 바꿀 것은 안 받는다")
              for k, e in ENDS.items()]
    lines += ["", "읽기"] + [f"  {k:<6} {w}" for k, w in READS.items()]
    lines += ["", "아직 없는 손가락 (인자를 주면 세션 전에 사람이 어디서 하나를 대며 종료 2 로 멈춘다)"]
    lines += ep_command.not_yet_lines(NOT_YET, CHANGES, 14)
    return "\n".join(lines)


# 표에 대 본 부름을 멈추는 말 — 까닭과 다음 걸음. 표(STARTS · ENDS)의 낱말은 멈추는 손가락이 채운다
END_ELSEWHERE = "「{word}」에서는 {end}({end_word})를 못 한다 — 이 출발의 끝: {ends}. 다음: 출발을 바꾸거나({starts}) 끝을 바꾼다"
END_TAKES_NONE = "{end}({end_word})는 바꿀 것을 안 받는다. 다음: 고치려면 change 로 부른다"


def fingers(args) -> str:
    """부른 명령의 출발을 고르고 표에 대 본다 — 아직 없는 손가락 · 출발에 없는 끝 · 출발에 없는 손가락 · 바꿀 것을 안 받는 끝 · 빠진
    값을 차례로 거른다(저마다 그 일을 어디서 하는지 대며 Stop(인자)). 출발을 낸다."""
    ep_command.refuse_not_yet(args, NOT_YET, CHANGES)
    start = ep_command.pick_start(args, STARTS)
    end = end_of(args, start)
    ep_command.refuse_foreign(args, CHANGES, start, STARTS[start].word)
    refuse_changes(args, end)
    ep_command.refuse_missing(args, CHANGES, start, STARTS[start].word)
    return start


def end_of(args, start: str) -> str:
    """부른 명령이 맺는 끝 — preview 는 그 출발의 끝 가운데 바꿀 것을 받는 것이다. 그 끝이 그 출발에 없으면 Stop(인자)."""
    ends = [k for k, e in ENDS.items() if start in e.starts]
    end = args.command if args.command != "preview" else next(k for k in ends if ENDS[k].changes)
    if start not in ENDS[end].starts:
        raise Stop(EXIT_ARGS, "args", END_ELSEWHERE.format(word=STARTS[start].word, end=end, end_word=ENDS[end].word, ends=" · ".join(ends),
                                                           starts=" · ".join(s.takes or k for k, s in STARTS.items())))
    return end


def refuse_changes(args, end: str) -> None:
    """바꿀 것을 안 받는 끝(취소)에 바꿀 것을 주었으면 Stop(인자)."""
    if not ENDS[end].changes and any(given(args, c) for c in CHANGES.values()):
        raise Stop(EXIT_ARGS, "args", END_TAKES_NONE.format(end=end, end_word=ENDS[end].word))


# ── 시각 ────────────────────────────────────────────────────────────────
def iso(t: datetime) -> str:
    """시각을 서울 시간대가 붙은 ISO 글자로 쓴다."""
    return t.astimezone(KST).isoformat(timespec="seconds")


def utc(t: datetime) -> str:
    """서울 시각을 앱이 받는 UTC 글자로 쓴다."""
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def parse_app(text: str) -> datetime:
    """앱이 쓰는 UTC 글자를 서울 시각으로 읽는다."""
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(KST)


def day_bounds(first: date, last: date) -> tuple[datetime, datetime]:
    """서울 하루(들)의 처음(첫날 0 시)과 끝(끝날 다음 날 0 시) — 그 날들에 걸친 예약을 가리는 구간이다."""
    return datetime.combine(first, datetime.min.time(), KST), datetime.combine(last + timedelta(days=1), datetime.min.time(), KST)


def day_span(first: date, last: date) -> tuple[str, str]:
    """서울 하루(들)의 처음과 끝을 앱이 받는 UTC 로 — 앱은 날짜만 주면 UTC 하루로 읽는다."""
    a, b = day_bounds(first, last)
    return utc(a), (b - timedelta(milliseconds=1)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.999Z")


def when(start: datetime, end: datetime) -> str:
    """사람에게 보일 때 한 마디 — 「11월 13일(금) 15:00–16:00」, 날을 넘으면 끝 날까지."""
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
        """회의실 하나의 「지역 건물 층」 — 나무에 없는 층이면 빈 글자."""
        return self.where.get(room.get("floor_id"), "")


def room_row(room: dict, places: Places) -> dict:
    """사람에게 보일 회의실 한 줄 — id · 이름 · 자리 · 정원 · 승인 대기 · 예약할 수 있나 · Teams 링크가 붙나."""
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
    """낱말 하나로 회의실 하나를 고른다 — id · 낱말이 다 든 곳 · 이름이 꼭 같은 곳 차례로, 없거나 여럿이면 Stop(인자)."""
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
    """살아 있는 예약인가 — 상태가 ``LIVE`` 에 든다."""
    return r.get("status") in LIVE


def overlaps(r: dict, start: datetime, end: datetime) -> bool:
    """예약 줄이 ``start`` ~ ``end`` 에 겹치나."""
    return parse_app(r["start_time"]) < end and start < parse_app(r["end_time"])


def person(p) -> str:
    """앱의 사람 칸(사람 dict 나 글자)에서 보일 이름 — 이름이 없으면 메일 주소."""
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


def start_id(args, start: str, among: tuple = ALL) -> str | None:
    """이 출발이 가리키는 예약의 id(그 출발의 인자 값) — 인자가 없는 출발(새 예약)이거나 ``among`` 밖의 출발이면 None. 출발 예약 읽기 ·
    취소 · 보내기 · 겹침에서 저 자신 빼기가 다 이것으로 받는다."""
    return getattr(args, STARTS[start].dest, None) if STARTS[start].takes and start in among else None


def series_rows(app, r: dict) -> list:
    """그 회차와 같은 반복의 살아 있는 회차 — 내 예약에서 시작 차례로."""
    sid = r.get(SERIES_ID)
    return sorted((x for x in app.mine() if x.get(SERIES_ID) == sid and live(x)), key=lambda x: x["start_time"])


def series_key(rows: list) -> str:
    """반복 전체의 열쇠 — 회차마다의 줄 열쇠를 묶는다. 보인 뒤 회차 하나라도 바뀌거나 늘고 줄면 달라진다."""
    return ep_command.fingerprint([[row_key(x) for x in rows]])


def workdays(first: date, last: date) -> list:
    """첫 날부터 끝 날까지의 업무일(월 ~ 금) — 앱은 여기서 공휴일을 더 뺀다."""
    out, d = [], first
    while d <= last:
        if d.weekday() < WEEKEND:
            out.append(d)
        d += timedelta(days=1)
    return out


def until_day(text: str) -> date:
    """``--until`` 의 날 — 날 말 · 요일 말 · YYYY-MM-DD(``day_of``). 꼴이 틀리면 Stop(인자)."""
    try:
        return day_of(text, datetime.now(KST).date())
    except Stop as exc:
        raise Stop(EXIT_ARGS, "args", f"--until 은 반복의 끝 날이다 — {exc}") from exc


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
    """예약 줄의 참석자를 앱의 꼴 그대로 메일 · 이름 · 사번으로 옮긴다 — 더하기 · 빼기가 있던 참석자를 이 꼴로 둔다."""
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
    return ep_command.fingerprint([r.get("id"), r.get("title"), r.get("start_time"), r.get("end_time"), sorted(r.get("room_ids") or []),
                                   sorted(a["email"].casefold() for a in kept_attendees(r)), r.get("status"), r.get("user_description")])


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
    """``--to`` 같은 칸의 주소들 — 칸의 값 뒤에 주소 파일의 줄을 이어 나눈다."""
    return split_addresses([*(values or ()), *address_lines(files)])


ADDRESS_FILE_MISSING = "주소 파일이 없다: {path}. 다음: 스킬 company-directory 의 find --out 이 끝 줄에 댄 파일 경로를 그대로 준다"


def address_lines(files) -> list[str]:
    """주소 파일들의 줄 — 파일 차례대로 한 줄에 하나(``#`` 뒤는 버린다). 없는 파일은 Stop(인자)."""
    lines = []
    for f in files or ():
        path = pathlib.Path(f).expanduser()
        if not path.is_file():
            raise Stop(EXIT_ARGS, "args", ADDRESS_FILE_MISSING.format(path=path))
        lines += [line.split("#", 1)[0] for line in path.read_text(encoding="utf-8-sig").splitlines()]
    return lines


def split_addresses(chunks: list[str]) -> list[str]:
    """글 조각들의 주소 — 빈칸 · 쉼표 · 쌍반점으로 나누고, 같은 주소(대소문자 무시)는 처음 것 한 번."""
    out, seen = [], set()
    for chunk in chunks:
        for a in ADDRESS_SPLIT.split(chunk):
            if a and a.casefold() not in seen:
                seen.add(a.casefold())
                out.append(a)
    return out


def people_addresses(files) -> tuple[list[str], list[str]]:
    """사람 파일(``ep_command.people_of``)의 사람들 → (메일 주소, 주소가 없는 사람의 말 「이름 · 부서(파일:몇째)」). 회의실 앱은 사람을
    메일 주소로 안다."""
    emails, no_mail = [], []
    for p in ep_command.distinct(ep_command.people_of(files)):
        if p.email:
            emails.append(p.email)
        else:
            no_mail.append(f"{p.label()}({p.where})")
    return emails, no_mail


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


def member_emails(g: dict) -> list[str]:
    """그룹 한 벌의 사람 메일 — 멤버 차례대로, 메일이 없는 멤버는 빈 글자."""
    return [m.get("email") or "" for m in g.get("members") or []]


def member_names(groups: list, book: Directory) -> dict:
    """그룹들의 사람 메일(소문자) → 앱의 사람 목록의 이름. 앱의 사람 목록에 없는 주소는 안 든다."""
    got, _ = book.resolve([e for g in groups for e in member_emails(g) if e])
    return {a["email"].casefold(): a["name"] for a in got}


def group_row(g: dict, names: dict) -> dict:
    """사람에게 보일 그룹 — 사람마다 이름과 메일. 이름을 모르는 주소는 이름 없이 둔다."""
    return {"name": g.get("name", ""), "members": [{"name": names.get(e.casefold(), ""), "email": e} for e in member_emails(g)]}


NO_MAIL_BLOCK = "사람 파일에 메일 주소가 없는 분이 있어 참석자로 못 넣는다: {who} — 주소록으로 그분을 다시 찾거나 사람에게 주소를 받아 --to 로 준다"
ABSENT_BLOCK = "지금 참석자에 없는 주소라 뺄 수 없다: {who} — mine · preview 의 attendees 주소를 준다"
UNKNOWN_BLOCK = "회의실 예약 앱의 사람 목록에 없는 주소: {who} — " + UNKNOWN_NEXT
COPY_ORGANIZER = "원래 주관자({who})는 참석자에 안 든다 — 함께 부르려면 --add-to 로 그분 주소를 준다"
ME_DROPPED = "사람 파일에 든 나(주관자)는 참석자로 안 넣었다 — 주관자는 참석자로 안 넣어도 회의에 든다"


def attendees_plan(app, args, start: str, base: dict | None, me: dict) -> tuple[list, list, list]:
    """참석자 — (새 참석자, 막는 까닭, 알릴 것). 있던 예약 · 본뜨기의 참석자에서 출발해 --to 로 갈고, --add-to · 그룹으로 더하고,
    --drop-to 로 뺀 뒤, 앱의 사람 목록에 없는 주소를 막는다."""
    book = Directory(app)
    current, notes = start_attendees(start, base, me)
    no_mail, replace_lost = [], []
    if given(args, CHANGES["to"]):
        current, no_mail, me_notes, replace_lost = replaced_attendees(args, me, book)
        notes += me_notes
    current, add_lost = with_added(current, added_addresses(app, args, me), book)
    current, absent = without_dropped(current, dropped_addresses(args))
    return current, attendee_blocks(no_mail, absent, once([*replace_lost, *add_lost])), notes


def once(items: list) -> list:
    """같은 것은 처음 한 번만 — 차례는 그대로."""
    return list(dict.fromkeys(items))


def attendee_blocks(no_mail: list, absent: list, unknown: list) -> list:
    """참석자를 막는 말 — 메일 주소가 없는 사람 파일의 사람 · 지금 참석자에 없어 못 뺀 주소 · 앱의 사람 목록에 없는 주소, 그 차례로 있는 것만."""
    return [said.format(who=", ".join(who)) for said, who in ((NO_MAIL_BLOCK, no_mail), (ABSENT_BLOCK, absent), (UNKNOWN_BLOCK, unknown)) if who]


def start_attendees(start: str, base: dict | None, me: dict) -> tuple[list, list]:
    """출발 예약의 참석자와 알릴 것 — 본뜨기는 나를 빼고(새 예약의 주관자다), 남이 주관한 예약을 본뜨면 원래 주관자가 안 든다고 알린다."""
    current = kept_attendees(base) if base else []
    notes = []
    if start == "copy":
        current = [a for a in current if a.get("employee_id") != me.get("id")]
        if not mine_to_change(base, me.get("id", "")):
            notes.append(COPY_ORGANIZER.format(who=person(base.get("organizer_id"))))
    return current, notes


def replaced_attendees(args, me: dict, book: Directory) -> tuple[list, list, list, list]:
    """--to · --to-file · 사람 파일로 통째로 갈 참석자 — (참석자, 메일 주소가 없는 사람 파일의 사람, 알릴 것, 앱에 없는 주소).
    주소 파일은 한 번 읽는다. 주소는 --to · 사람 파일 · --to-file 의 차례다(그 차례가 보낼 몸통과 열쇠에 든다)."""
    from_people, no_mail = people_addresses(getattr(args, "people_file", None))
    lines = address_lines(args.to_file)
    current, lost = book.resolve(to_addresses(args.to, from_people, lines))
    current, notes = without_me(current, me, to_addresses(args.to, [], lines))
    return current, no_mail, notes, lost


def to_addresses(to, from_people: list[str], lines: list[str]) -> list[str]:
    """--to 줄(``--to`` · 사람 파일 · ``--to-file``)이 가리키는 주소 — 그 차례로 나눠 같은 주소는 한 번. 참석자 갈기와 그룹 짓기가 함께 쓴다."""
    return split_addresses([*(to or ()), *from_people, *lines])


def without_me(current: list, me: dict, typed: list[str]) -> tuple[list, list]:
    """사람 파일에서 든 나(주관자)를 뺀 참석자와 알릴 것 — 「나와 ○○ 님」으로 찾은 파일이 흔하다. 나는 앱의 사람 열쇠로 가리고(주관자 칸의
    값), 주소로 직접 준 나는 둔다."""
    listed = {a.casefold() for a in typed}
    mine = [a for a in current if a.get("employee_id") == me.get("id") and a["email"].casefold() not in listed]
    if not mine:
        return current, []
    return [a for a in current if a not in mine], [ME_DROPPED]


def added_addresses(app, args, me: dict) -> list[str]:
    """더할 주소 — --add-to · --add-to-file 과 참석자 그룹의 사람(주관자인 나는 빼고). 따로 준 주소와 그룹이 같은 사람을 들면 한 번만."""
    adds = addresses(getattr(args, "add_to", None), getattr(args, "add_to_file", None))
    group = group_addresses(app, args.group, me) if getattr(args, "group", None) else []
    return distinct_addresses([*adds, *group])


def group_addresses(app, name: str, me: dict) -> list[str]:
    """내 참석자 그룹 하나(앱의 설정)의 사람 메일 — 주관자인 나는 뺀다. 그룹이 없거나 여럿 걸리면 Stop(인자)."""
    mine = str(me.get("email", "")).casefold()
    return [e for e in member_emails(find_group(app.prefs(), name)) if e and e.casefold() != mine]


def distinct_addresses(adds: list[str]) -> list[str]:
    """같은 주소(대소문자 무시)는 한 번 — 처음 나온 자리에, 마지막 철자로."""
    return list({a.casefold(): a for a in adds}.values())


def dropped_addresses(args) -> dict:
    """뺄 주소 — ``--drop-to`` 의 주소, 소문자 → 준 철자."""
    return {d.casefold(): d for d in addresses(getattr(args, "drop_to", None), None)}


def with_added(current: list, adds: list[str], book: Directory) -> tuple[list, list]:
    """있던 참석자는 그대로 두고 더한 주소의 사람을 뒤에 — (참석자, 앱에 없는 주소). 더할 주소가 없으면 그대로."""
    if not adds:
        return current, []
    got, lost = book.resolve(adds)
    have = {a["email"].casefold() for a in current}
    return current + [a for a in got if a["email"].casefold() not in have], lost


def without_dropped(current: list, drops: dict) -> tuple[list, list]:
    """준 주소의 사람만 뺀다 — (참석자, 지금 참석자에 없어 못 뺀 주소). 뺄 주소가 없으면 그대로."""
    if not drops:
        return current, []
    have = {a["email"].casefold() for a in current}
    absent = [d for k, d in drops.items() if k not in have]
    return [a for a in current if a["email"].casefold() not in drops], absent


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
NO_TITLE = "제목이 비었다 — --title 로 준다"
BACKWARDS = "끝({end})이 시작({start})보다 앞이거나 같다 — 끝을 시작 뒤로 준다(있던 예약 · 본뜨기에 시작만 주면 길이를 둔다)"
PAST_TIME = "지난 시각이다 — 회의실 예약 앱은 지난 시각도 받지만 여기서는 넣지 않는다"
PAST_SERIES_CHANGE = "지난 회차가 든 반복이다 — 지난 회차까지 함께 바뀌는지 안 쟀다. 사람에게 회의실 예약 화면에서 하시라 권한다"
PAST_SERIES_CANCEL = "지난 회차가 든 반복이다 — 지난 회차까지 함께 지워지는지 안 쟀다. 사람에게 회의실 예약 화면에서 하시라 권한다"
SERIES_WEEKEND = "반복의 첫 날이 주말이다 — 앱은 업무일에만 회차를 세운다. 첫 업무일로 --start 를 준다"
SERIES_SHORT = "--until 이 첫 날보다 뒤여야 반복이다 — 한 번만이면 --until 없이 부른다"
SERIES_LONG = "회차가 {n} 개다 — {most} 개를 넘으면 여기서 안 넣는다. --until 을 당기거나 화면에서 한다"
SERIES_NOTE = "반복 — {n} 회차(업무일). 공휴일에 걸린 회차는 앱이 빼서 실제로는 더 적을 수 있다"
NOTHING_CHANGED = "바뀐 것이 없다 — 고치면 참석자께 바뀐 안내만 간다"
ROOM_MISSING = "회의실 {rid} 가 목록에 없다"
ROOM_CLOSED = "{name}: 일반 사용자가 예약할 수 없는 회의실이다"
ROOM_FOREIGN = "{name}: 다른 회사 회의실이라 예약할 수 없다"
ROOM_APPROVAL = "{name}: 승인이 필요한 회의실 — 넣으면 「승인 대기」로 들어간다"
ROOM_FULL = "{name}: 정원 {capacity} 명인데 참석자가 주관자 포함 {n} 명이다"
ROOM_TEAMS = "{name}: 이 회의실 정책으로 Teams 회의 링크가 저절로 붙는다"
CLASH = "그 시각에 이미 예약이 있다 — {when} 「{title}」({who})"
APPROVAL_ANY = "승인이 필요한 회의실이 들었다 — 넣으면 「승인 대기」로 들어간다"
NO_ATTENDEES = "참석자가 없다 — 회의실만 잡히고 누구에게도 안내가 안 간다"
UNMEASURED_CHANGE = "{what} 바꾸기는 " + UNMEASURED + " — 고친 뒤 다시 읽어 그대로 섰는지 보고, 아니면 「확인 못 했다」로 낸다"


def plan(app, args, me: dict, now: datetime, start: str) -> dict:
    """출발 하나에 바꿀 것을 넣은 한 건의 꼴과 막는 까닭 · 알릴 것 · 열쇠. 바꾸지 않는다."""
    rooms, places = room_book(app)
    base, rows, stop = plan_start(app, args, me, start)
    if stop:
        return stop
    room_ids, s, e, title, note = plan_values(args, base, rooms, places)
    attendees, blocks, notes = attendees_plan(app, args, start, base, me)
    blocks += value_blocks(title, s, e, now, start, rows)
    days, more_blocks, more_notes = series_days(args, s)
    blocks += more_blocks
    notes += more_notes
    if start in IN_PLACE and nothing_changed(base, title, note, s, e, room_ids, attendees):
        blocks.append(NOTHING_CHANGED)
    by_id = {r["id"]: r for r in rooms}
    more_blocks, more_notes, approval_noted = room_policy(room_ids, by_id, places, me, len(attendees))
    blocks += more_blocks
    notes += more_notes
    editing = start_id(args, start, ("booking",))   # 고치는 그 한 건 — 겹침과 앱의 미리 검사가 저 자신을 뺀다
    clash = []
    if e > s and start != "series":   # 반복 전체는 시각 · 회의실을 안 바꿔 새 겹침이 없다
        clash = clashes(app, room_ids, s, e, days, editing, {x["id"] for x in rows})
        blocks += clash_blocks(clash)
        if not blocks:
            more_blocks, more_notes = app_check(app, room_ids, s, e, editing, approval_noted)
            blocks += more_blocks
            notes += more_notes
    notes += late_notes(args, start, attendees)
    body = plan_body(me, start, base, rows, days, room_ids, title, note, s, e, attendees)
    view = plan_view(me, start, base, rows, days, places, by_id, room_ids, title, note, s, e, attendees, blocks, notes, body)
    view["key"] = ep_command.fingerprint([start, body, sorted(x["id"] + x.get("updated_at", "") for x in clash),
                                          (base or {}).get("updated_at"), [x["id"] + x.get("updated_at", "") for x in rows]])
    return view


def room_book(app) -> tuple[list, Places]:
    """앱의 회의실 목록과 자리 나무 — 한 부름에 회의실이 드는 손이 다 이것으로 받는다."""
    places = Places(app.hierarchy())
    return app.rooms(), places


def plan_start(app, args, me: dict, start: str) -> tuple[dict | None, list, dict | None]:
    """출발 예약 — (출발 예약, 반복 전체면 그 회차들, 멈출 답). 내 예약에서 다시 읽어 없으면 gone, 고치지 않는 까닭이 있으면 refused 를
    멈출 답으로 낸다. 반복 전체는 첫 회차의 꼴로 짓는다 — 앱의 화면도 그 회차에서 연다."""
    base = None
    rid = start_id(args, start)
    if rid:
        base = reread(app, rid)
        if base is None:
            return None, [], {"state": "gone"}
        why = refusal(base, me["id"], start) if start in IN_PLACE else ""
        if why:
            return None, [], {"state": "refused", "reason": why}
    rows = series_rows(app, base) if start == "series" else []
    return (rows[0] if rows else base), rows, None


def plan_values(args, base: dict | None, rooms: list, places: Places) -> tuple[list, datetime, datetime, str, str]:
    """넣을 회의실 · 시각 · 제목 · 설명 — 안 준 것은 출발 예약의 값이다."""
    room = one_room(rooms, places, args.room) if args.room else None
    room_ids = [room["id"]] if room else list(base.get("room_ids") or [])
    s, e = times(args, base)
    title = (args.title if args.title is not None else (base or {}).get("title", "")).strip()
    note = args.note if args.note is not None else (base or {}).get("user_description", "")
    return room_ids, s, e, title, note


def has_past(rows: list, now: datetime) -> bool:
    """반복의 회차 가운데 지난 것이 있나 — 고칠 판과 반복 전체 취소가 이것 하나로 본다."""
    return any(parse_app(x["start_time"]) < now for x in rows)


def value_blocks(title: str, s: datetime, e: datetime, now: datetime, start: str, rows: list) -> list:
    """값이 막는 까닭 — 빈 제목 · 거꾸로 선 시각 · 지난 시각(한 건) · 지난 회차가 든 반복."""
    blocks = []
    if not title:
        blocks.append(NO_TITLE)
    if e <= s:
        blocks.append(BACKWARDS.format(end=stamp(e), start=stamp(s)))
    if s < now and start != "series":
        blocks.append(PAST_TIME)
    if start == "series" and has_past(rows, now):
        blocks.append(PAST_SERIES_CHANGE)
    return blocks


def series_days(args, s: datetime) -> tuple[list, list, list]:
    """반복으로 넣을 회차의 날 — (날들, 막는 까닭, 알릴 것). ``--until`` 이 없으면 한 건이라 날이 빈다."""
    if not getattr(args, "until", None):
        return [], [], []
    last = until_day(args.until)
    days = workdays(s.date(), last)
    blocks, notes = [], []
    if s.date().weekday() >= WEEKEND:
        blocks.append(SERIES_WEEKEND)
    if last <= s.date():
        blocks.append(SERIES_SHORT)
    elif len(days) > MOST_OCCURRENCES:
        blocks.append(SERIES_LONG.format(n=len(days), most=MOST_OCCURRENCES))
    else:
        notes.append(SERIES_NOTE.format(n=len(days)))
    return days, blocks, notes


def nothing_changed(base: dict, title: str, note: str, s: datetime, e: datetime, room_ids: list, attendees: list) -> bool:
    """고칠 값이 출발 예약과 다 같은가 — 제목 · 설명 · 시각 · 회의실 · 참석자 주소."""
    return (title, note, s, e, room_ids, sorted(a["email"].casefold() for a in attendees)) == (
        base.get("title", "").strip(), base.get("user_description", ""), parse_app(base["start_time"]), parse_app(base["end_time"]),
        list(base.get("room_ids") or []), sorted(a["email"].casefold() for a in kept_attendees(base)))


def room_policy(room_ids: list, by_id: dict, places: Places, me: dict, guests: int) -> tuple[list, list, bool]:
    """회의실 정책 — (막을 것: 목록에 없음 · 예약 못 함 · 남의 회사, 알릴 것: 승인 · 정원 · Teams, 승인이 드는 회의실을 알렸나)."""
    blocks, notes, approval = [], [], False
    for room_id in room_ids:
        r = by_id.get(room_id)
        if r is None:
            blocks.append(ROOM_MISSING.format(rid=room_id))
            continue
        row = room_row(r, places)
        if not row["bookable"]:
            blocks.append(ROOM_CLOSED.format(name=row["name"]))
        if cross_company(r, places, me):
            blocks.append(ROOM_FOREIGN.format(name=row["name"]))
        if row["approval"]:
            notes.append(ROOM_APPROVAL.format(name=row["name"]))
            approval = True
        if row["capacity"] and guests + 1 > row["capacity"]:
            notes.append(ROOM_FULL.format(name=row["name"], capacity=row["capacity"], n=guests + 1))
        if row["teams_link"]:
            notes.append(ROOM_TEAMS.format(name=row["name"]))
    return blocks, notes, approval


def clashes(app, room_ids: list, s: datetime, e: datetime, days: list, editing: str | None, own: set) -> list:
    """그 회의실 · 시각(반복이면 회차마다)에 이미 선 살아 있는 예약 — 고치는 그 예약과 반복 전체의 제 회차는 겹침이 아니다."""
    spans = [(datetime.combine(d, s.timetz()), datetime.combine(d, s.timetz()) + (e - s)) for d in days] or [(s, e)]
    return [x for x in app.between(utc(spans[0][0]), utc(spans[-1][1])) if live(x) and x["id"] != editing and x["id"] not in own
            and set(x.get("room_ids", [])) & set(room_ids) and any(overlaps(x, a, b) for a, b in spans)]


def clash_blocks(clash: list) -> list:
    """겹친 예약마다 막는 까닭 한 줄 — 그 예약의 때 · 제목 · 주관자."""
    return [CLASH.format(when=when(parse_app(x["start_time"]), parse_app(x["end_time"])), title=x.get("title", ""),
                         who=person(x.get("organizer_id"))) for x in clash]


def app_check(app, room_ids: list, s: datetime, e: datetime, editing: str | None, approval_noted: bool) -> tuple[list, list]:
    """앱의 미리 검사 — (막을 것: 앱이 낸 오류, 알릴 것: 승인이 드는데 회의실 정책에서 아직 안 알렸으면)."""
    v = app.validate(room_ids, iso(s), iso(e), editing)
    more = [APPROVAL_ANY] if v.get("approvalRequiredRoomIds") and not approval_noted else []
    return [err.get("message", str(err)) for err in v.get("errors", [])], more


def late_notes(args, start: str, attendees: list) -> list:
    """판 끝의 알릴 것 — 참석자 없음 · 회사에서 안 잰 바꾸기."""
    notes = [] if attendees else [NO_ATTENDEES]
    return notes + [UNMEASURED_CHANGE.format(what=c.word.split(" — ")[0]) for c in CHANGES.values() if start in c.unmeasured and given(args, c)]


def plan_body(me: dict, start: str, base: dict | None, rows: list, days: list, room_ids: list, title: str, note: str, s: datetime,
              e: datetime, attendees: list) -> dict:
    """앱에 보낼 몸통 — 화면이 보내는 꼴(``body_of``)에 반복 칸. 반복 전체 고치기는 앱의 화면처럼 반복 칸을 첫 회차 ~ 끝 회차로 다시 싣는다."""
    held = base or {}
    body = body_of(me, room_ids, title, note, s, e, attendees, company=held.get("company_id", ""),
                   status=held.get("status", "confirmed") if start in IN_PLACE else "confirmed",
                   teams=held.get("teams_link_visibility") or "private")
    if days:
        body.update(is_recurring=True, recurring_end_date=days[-1].isoformat())
    if rows:
        body.update(is_recurring=True, recurring_end_date=parse_app(rows[-1]["start_time"]).date().isoformat())
    return body


def plan_view(me: dict, start: str, base: dict | None, rows: list, days: list, places: Places, by_id: dict, room_ids: list, title: str,
              note: str, s: datetime, e: datetime, attendees: list, blocks: list, notes: list, body: dict) -> dict:
    """사람에게 보일 판 — 값 · 막는 까닭 · 알릴 것 · 몸통, 반복의 회차, 있던 예약이면 지금 꼴 · 새로 안내가 갈 분 · 취소 안내가 갈 분,
    본뜨기면 본뜬 예약. 열쇠는 아직 없다. ``attendees`` 는 맨 위에 선다 — 주소록의 ``--from-file`` 이 가장 얕은 그 칸을 읽는다."""
    names = [f"{places.of(by_id[r])} {by_id[r]['name']}".strip() for r in room_ids if r in by_id]
    shown_ = [{"name": a["name"], "email": a["email"]} for a in attendees]
    view = {"state": "ready" if not blocks else "blocked", "ok": not blocks, "from": start, "title": title, "note": note,
            "day": s.date().isoformat(), "when": when(s, e), "start": stamp(s), "end": stamp(e), "rooms": names,
            "attendees": shown_, "blocks": blocks, "notes": notes, "body": body}
    if days:
        view["occurrences"] = [f"{d:%m월 %d일}({WEEKDAYS[d.weekday()]})" for d in days]
    if rows:
        view["series"] = {"count": len(rows), "days": [booking_row(x, me["id"], keyed=False)["when"] for x in rows]}
    if start in IN_PLACE:
        before = [{"name": a["name"], "email": a["email"]} for a in kept_attendees(base)]
        had, keeps = {a["email"].casefold() for a in before}, {a["email"].casefold() for a in shown_}
        view["was"] = booking_row(base, me["id"])
        if rows:
            view["was"]["key"] = series_key(rows)   # 반복 전체 취소의 열쇠
        view["joining"] = [a for a in shown_ if a["email"].casefold() not in had]       # 새로 회의 안내가 가는 분
        view["leaving"] = [a for a in before if a["email"].casefold() not in keeps]    # 취소 안내가 가는 분
    if start == "copy":
        view["template"] = booking_row(base, me["id"], keyed=False)
    return view


def shown(p: dict) -> dict:
    """사람에게 보일 판 — 앱에 보낼 몸통(``body``)은 뺀다."""
    return {k: v for k, v in p.items() if k != "body" and v not in (None, [], "")}


def fit(out: dict, key: str, group: str, more: str, **said) -> dict:
    """답이 OUT_BYTES 를 넘으면 ``out[key]`` 의 뒤 무리부터 덜어 낸다 — 줄의 ``group`` 칸이 같은 것이 한 무리이고 무리를 가운데서 안
    끊는다. 덜었으면 ``more``(이어 볼 길의 말 — ``{cut}`` 에 덜어 낸 첫 무리, 나머지 칸은 ``said``)를 단다. 무리 하나만으로 넘치면 그
    무리는 그대로 낸다. 그 답을 낸다."""
    groups = list(dict.fromkeys(x[group] for x in out[key]))
    while len(groups) > 1 and size(out, INDENT) > OUT_BYTES:
        cut = groups.pop()
        out[key] = [x for x in out[key] if x[group] != cut]
        out["cut"] = True
        out["more"] = more.format(cut=cut, **said)
    return out


def free_span(args) -> tuple[datetime, datetime]:
    """free 의 --start · --end — 꼴이 아니거나 끝이 시작보다 앞이면 Stop(인자). 세션 없이 가린다."""
    start, end = kst(args.start), kst(args.end)
    if end <= start:
        raise Stop(EXIT_ARGS, "args", f"--end({stamp(end)})가 --start({stamp(start)})보다 앞이거나 같다. 다음: 끝을 시작 뒤로 준다 — "
                                      "사람이 끝을 안 말했으면 지어 넣지 말고 묻는다")
    return start, end


def asked_day(text, today: date) -> date:
    """사람이 준 날 하나 — ``day_of`` 의 멈춤(받는 꼴 · 요일 말이면 날짜 표)을 이 손의 Stop(인자)으로 낸다."""
    try:
        return day_of(text, today)
    except Stop as exc:
        raise Stop(EXIT_ARGS, "args", str(exc)) from exc


def mine_days(args, today: date) -> tuple[date, date]:
    """mine 의 첫날 · 끝날 — 첫날을 안 주면 오늘, 끝날을 안 주면 첫날부터 ``MINE_DAYS`` 날. 끝날이 첫날보다 앞이면 Stop(인자)."""
    first = asked_day(args.first, today)
    last = asked_day(args.last, today) if args.last else first + timedelta(days=MINE_DAYS)
    if last < first:
        raise Stop(EXIT_ARGS, "args", f"끝날({last})이 첫날({first})보다 앞이다. 다음: mine <첫날> <끝날> 차례로 준다")
    return first, last


NO_FAVORITES = "즐겨찾는 회의실이 없어 모든 회의실에서 찾았다 — 즐겨찾기는 사람이 바라면 pref --favorite <회의실> 로 넣는다"


def favorites_only(app, args, rooms: list) -> tuple[list, str]:
    """``--favorites`` 면 즐겨찾는 회의실만 — (회의실들, 사람에게 할 말). 즐겨찾기가 비었으면 모든 회의실에서 찾고 그렇다고 말한다 —
    「늘 쓰던 회의실」 은 즐겨찾기가 없는 사람에게도 나오는 말이라, 멈추면 같은 찾기를 한 번 더 부르게 된다."""
    if not getattr(args, "favorites", False):
        return rooms, ""
    fav = set(app.prefs().get("favorite_rooms") or [])
    if not fav:
        return rooms, NO_FAVORITES
    return [r for r in rooms if r["id"] in fav], ""


# ── 보인 판 지킴 · 바꾼 뒤 다시 읽기 — 바꾸는 끝이 다 이것을 쓴다 ─────────────────────────────────────
def shown_changed(key: str, confirm: str | None) -> bool:
    """사람이 본 판과 지금 판이 다른가 — 지금 지은 열쇠가 받은 ``--confirm`` 과 다르면 참. 넣기 · 고치기 · 취소 · 내 설정이 이것 하나로 본다."""
    return key != confirm


CUT = object()                            # 바꾸는 요청의 답이 오기 전에 끊겼다 — 들어갔을 수 있다


def sent(mrs, request):
    """바꾸는 요청 하나 — 앱의 답. 답 전에 끊겼으면 ``CUT``(들어갔을 수 있어 다시 보내지 않는다 — 부른 쪽이 다시 읽어 맺는다). 앱이 답으로
    거절했으면 안 바뀌었으니 그대로 올린다."""
    try:
        return request()
    except mrs.AppError as exc:
        if exc.status is not None:
            raise
        return CUT


def after_write(read, failed):
    """바꾼 뒤 다시 읽는다 — ``read()`` 의 값, 지면 무엇으로 지든 ``failed``. 앱이 받은 뒤라 세션 · 도구 오류로 올리면 다시 부르라는 말이
    되어 두 번 든다."""
    try:
        return read()
    except Exception:  # noqa: BLE001 — 바꾼 뒤라 어떤 실패도 다시 부를 까닭이 아니다
        return failed


def word_answer(state: str, **more) -> dict:
    """끝 낱말과 그 말의 답."""
    return {"state": state, "state_word": STATE_WORDS[state], **more}


def refused_answer(why: str) -> dict:
    """고치거나 취소하지 않는 답 — 까닭과 사람에게 할 말."""
    return {"state": "refused", "reason": why, "state_word": REFUSE_WORDS[why]}


# ── 내 설정 바꾸기 ────────────────────────────────────────────────────────
PREF_ONE = f"pref 는 하나씩 한다. 다음: {' · '.join(f for f, _ in PREF_ACTIONS.values())} 가운데 하나만 주어 부르고, 다음 것은 따로 부른다"
FAVORITE_ALREADY = "{name} 은 이미 즐겨찾기에 {where}"
GROUP_NO_MAIL = "사람 파일에 메일 주소가 없는 분이 있다: {who}. 다음: 주소록으로 그분을 다시 찾거나 사람에게 주소를 받아 --to 로 준다"
GROUP_UNKNOWN = "회의실 예약 앱의 사람 목록에 없는 주소: {who}. 다음: " + UNKNOWN_NEXT
GROUP_EMPTY = f"그룹에 넣을 사람이 없다. 다음: --to · --to-file · {ep_command.PEOPLE_FLAG} 로 준다"


@dataclass(frozen=True)
class PrefPlan:
    """내 설정 하나의 판 — 보일 판 · 열쇠에 드는 몸통 · 바꾸기(앱 → 앱의 답) · 섰나(앱의 답 → 참 · 거짓) · 막는 까닭(있으면 안 바꾼다)."""
    view: dict
    body: object
    apply: object
    took: object
    blocks: list = field(default_factory=list)


def pref(app, mrs, args) -> dict:
    """내 설정 하나를 미리 보이거나(``--confirm`` 없음) 그 열쇠로 바꾼다. 보인 뒤 설정이 바뀌었으면 ``moved`` 로 안 바꾼다. 바꾼 뒤는
    앱이 낸 설정 전체에서 섰나를 가린다."""
    action, value = pref_action(args)
    prefs = app.prefs()
    p = PREF_PLANS[action](app, args, prefs, Directory(app), action, value)
    if p.blocks:
        return word_answer("blocked", blocks=p.blocks)
    key = pref_key(action, p, prefs)
    if args.confirm is None:
        return ready_answer(keyed_view(p, key))
    if shown_changed(key, args.confirm):
        return word_answer("moved", preview=keyed_view(p, key))
    back = settled_prefs(app, sent(mrs, lambda: p.apply(app)))
    return word_answer(pref_state(p, back), **p.view)


def pref_key(action: str, p: PrefPlan, prefs: dict) -> str:
    """내 설정 판의 열쇠 — 할 일 · 보낼 몸통 · 지금 설정의 고친 시각의 해시."""
    return ep_command.fingerprint([action, p.body, prefs.get("updated_at")])


def keyed_view(p: PrefPlan, key: str) -> dict:
    """열쇠를 단 보일 판."""
    return {**p.view, "key": key}


def ready_answer(view: dict) -> dict:
    """바꿀 수 있는 미리 보기의 답."""
    return {"state": "ready", "ok": True, **view}


def settled_prefs(app, back):
    """바꾼 뒤의 설정 — 앱의 답, 답 전에 끊겼으면(``CUT``) 다시 보내지 않고 지금 설정을 읽는다(그 읽기가 지면 ``None``)."""
    return after_write(app.prefs, None) if back is CUT else back


def pref_state(p: PrefPlan, back) -> str:
    """바꾼 뒤의 끝 낱말 — 앱이 낸 설정에 바란 대로 섰으면 saved, 아니거나 못 읽었으면 unsure."""
    return "saved" if isinstance(back, dict) and p.took(back) else "unsure"


def pref_action(args) -> tuple[str, str]:
    """고른 내 설정 하나 — (할 일, 값). 하나가 아니면 Stop(인자)."""
    picked = [k for k in PREF_ACTIONS if getattr(args, k, None) is not None]
    if len(picked) != 1:
        raise Stop(EXIT_ARGS, "args", PREF_ONE)
    return picked[0], getattr(args, picked[0])


def favorite_plan(app, args, prefs: dict, book: Directory, action: str, value: str) -> PrefPlan:
    """즐겨찾기 넣기 · 빼기의 판 — 이미 그렇게 서 있으면 막는 까닭만 든 판."""
    rooms, places = room_book(app)
    room = one_room(rooms, places, value)
    on = action == "favorite"
    if (room["id"] in (prefs.get("favorite_rooms") or [])) == on:
        return PrefPlan({}, None, None, None, [FAVORITE_ALREADY.format(name=room["name"], where="있다" if on else "없다")])
    return PrefPlan({"do": PREF_ACTIONS[action][1].split(" — ")[0], "room": room_row(room, places)}, room["id"],
                    functools.partial(favorite_apply, room_id=room["id"], on=on), functools.partial(favorite_took, room_id=room["id"], on=on))


def favorite_apply(app, *, room_id: str, on: bool):
    """즐겨찾기를 바꾼다 — 앱의 답(바뀐 뒤의 설정)."""
    return app.favorite(room_id, on)


def favorite_took(back: dict, *, room_id: str, on: bool) -> bool:
    """즐겨찾기가 섰나 — 앱이 낸 설정에 그 회의실이 바란 대로 있나."""
    return (room_id in (back.get("favorite_rooms") or [])) == on


def group_save_plan(app, args, prefs: dict, book: Directory, action: str, value: str) -> PrefPlan:
    """참석자 그룹 짓기 · 갈기의 판 — 사람은 --to · --to-file · 사람 파일. 주소 없는 사람 · 앱에 없는 주소 · 빈 그룹은 Stop(인자)."""
    got = group_members(args, book)
    old = next((g for g in prefs.get("attendee_groups") or [] if g.get("name") == value), None)
    body = {"name": value, "members": [{"employee_id": a["employee_id"], "email": a["email"]} for a in got]}
    view = {"do": "참석자 그룹 고치기" if old else "참석자 그룹 짓기",
            "group": {"name": value, "members": [{"name": a["name"], "email": a["email"]} for a in got]}}
    if old:
        view["was"] = group_row(old, member_names([old], book))
    return PrefPlan(view, body, functools.partial(group_save_apply, old=old, body=body),
                    functools.partial(group_save_took, name=value, want=sorted(a["email"].casefold() for a in got)))


def group_members(args, book: Directory) -> list:
    """그룹에 넣을 사람 — --to · --to-file · 사람 파일의 주소를 앱의 사람에 잇는다. 주소 없는 사람 · 앱에 없는 주소 · 빈 그룹은
    Stop(인자)."""
    from_people, no_mail = people_addresses(args.people_file)
    if no_mail:
        raise Stop(EXIT_ARGS, "args", GROUP_NO_MAIL.format(who=", ".join(no_mail)))
    got, lost = book.resolve(to_addresses(args.to, from_people, address_lines(args.to_file)))
    if lost:
        raise Stop(EXIT_ARGS, "args", GROUP_UNKNOWN.format(who=", ".join(lost)))
    if not got:
        raise Stop(EXIT_ARGS, "args", GROUP_EMPTY)
    return got


def group_save_apply(app, *, old: dict | None, body: dict):
    """그룹을 짓거나 간다 — 앱의 답."""
    return app.put_group(old["id"], body) if old else app.add_group(body)


def group_save_took(back: dict, *, name: str, want: list) -> bool:
    """그룹이 섰나 — 앱이 낸 설정에 그 이름의 그룹이 바란 사람들로 있나."""
    return any(g.get("name") == name and sorted(m.get("email", "").casefold() for m in g.get("members") or []) == want
               for g in back.get("attendee_groups") or [])


def group_drop_plan(app, args, prefs: dict, book: Directory, action: str, value: str) -> PrefPlan:
    """참석자 그룹 지우기의 판."""
    g = find_group(prefs, value)
    return PrefPlan({"do": "참석자 그룹 지우기", "group": group_row(g, member_names([g], book))}, g.get("id"),
                    functools.partial(group_drop_apply, group=g), functools.partial(group_drop_took, group=g))


def group_drop_apply(app, *, group: dict):
    """그룹을 지운다 — 앱의 답. 그룹 열쇠는 바꿀 때 읽는다(미리 보기는 열쇠 없는 그룹도 보인다)."""
    return app.drop_group(group["id"])


def group_drop_took(back: dict, *, group: dict) -> bool:
    """그룹이 사라졌나."""
    return all(x.get("id") != group["id"] for x in back.get("attendee_groups") or [])


PREF_PLANS = {"favorite": favorite_plan, "unfavorite": favorite_plan, "save_group": group_save_plan, "drop_group": group_drop_plan}


# ── 읽기 ────────────────────────────────────────────────────────────────
NOT_IN_LIST = "(목록에 없는 회의실)"
FREE_ROOMS_CUT = "다음: 뒤의 회의실은 안 실었다 — --where 낱말을 좁혀 다시 부른다"
DAY_ROOMS_CUT = "다음: 뒤의 회의실은 안 실었다 — 낱말을 좁혀(지역 · 건물 · 층 · 이름) 다시 부른다"
DAY_NONE = "「{words}」에 걸리는 회의실이 없다(날은 --date 로 준다). 다음: rooms 로 찾아 보인다"
MINE_CUT = "다음: {cut} 부터는 안 실었다 — mine {cut} {last} 로 이어 본다"


def live_within(app, first: str, last: str, lo: datetime, hi: datetime) -> list:
    """앱의 예약 조회(``first`` ~ ``last`` — 앱이 받는 UTC 글자)에서 살아 있고 ``lo`` ~ ``hi`` 에 겹치는 예약 — 빈 방 · 현황이 이것으로 받는다."""
    return [x for x in app.between(first, last) if live(x) and overlaps(x, lo, hi)]


def prefs_of(app, args, now: datetime) -> dict:
    """prefs 의 답 — 즐겨찾는 회의실과 참석자 그룹."""
    prefs = app.prefs()
    rooms, places = room_book(app)
    by_id = {r["id"]: r for r in rooms}
    favorites = [room_row(by_id[i], places) if i in by_id else {"id": i, "name": NOT_IN_LIST} for i in prefs.get("favorite_rooms") or []]
    groups = prefs.get("attendee_groups") or []
    names = member_names(groups, Directory(app))
    return {"favorites": favorites, "groups": [group_row(g, names) for g in groups]}


def rooms_of(app, args, now: datetime) -> dict:
    """rooms 의 답 — 낱말이 다 든 회의실(즐겨찾기만도)."""
    rooms, places = room_book(app)
    picked, note = favorites_only(app, args, find_rooms(rooms, places, args.word))
    got = [room_row(r, places) for r in picked]
    out = {"count": len(got), "rooms": got[:MOST_ROOMS], "cut": len(got) > MOST_ROOMS}
    if note:
        out["note"] = note
    return out


def free_rooms(app, args, now: datetime) -> dict:
    """free 의 답 — 후보 회의실 → 그 시각의 예약 → 빈 방(구간 내내) 또는 방의 비는 때(--minutes) → 덧말 → 답 크기."""
    me = app.me()
    start, end = free_span(args)
    rooms, places = room_book(app)
    picked, note = favorites_only(app, args, find_rooms(rooms, places, args.where))
    cand = candidate_rooms(picked, places, me, args.people)
    booked = live_within(app, utc(start), utc(end), start, end)
    out = room_gaps(args, cand, booked, places, start, end, now) if args.minutes else whole_free(cand, booked, places, start, end)
    return fit(free_said(out, note, args.minutes), "rooms", "id", FREE_ROOMS_CUT)


def candidate_rooms(picked: list, places: Places, me: dict, people: int | None) -> list:
    """빈 방을 찾을 후보 — 고른 회의실 가운데 내가 예약할 수 있고(예약 가능 · 남의 회사가 막지 않음) 정원이 인원(주었으면)을 받는 곳."""
    return [r for r in picked if room_row(r, places)["bookable"] and not cross_company(r, places, me)
            and (not people or (r.get("capacity") or 0) >= people)]


def free_said(out: dict, note: str, minutes: int | None) -> dict:
    """빈 방의 답에 덧말을 단다 — 즐겨찾기가 비어 전부에서 찾았으면 그 말(``note``), 하나도 없으면 넓힐 길(없다로 끝내지 않는다 —
    비는 곳을 짓지 않는다)."""
    if note:
        out["note"] = note
    if not out["count"]:
        out["word"] = free_none_word(minutes)
    return out


def whole_free(cand: list, booked: list, places: Places, start: datetime, end: datetime) -> dict:
    """구간 내내 빈 회의실의 답."""
    busy = {rid for x in booked for rid in x.get("room_ids", [])}
    free = [room_row(r, places) for r in cand if r["id"] not in busy]
    return {"when": when(start, end), "count": len(free), "rooms": free[:MOST_FREE], "cut": len(free) > MOST_FREE}


def room_gaps(args, cand: list, booked: list, places: Places, start: datetime, end: datetime, now: datetime) -> dict:
    """구간 안에서 ``--minutes`` 분 넘게 비는 회의실과 그 비는 때의 답 — 지난 시각은 비었어도 잡지 않는다."""
    lo = max(start, now)
    rows = []
    for r in cand:
        held = [(parse_app(x["start_time"]), parse_app(x["end_time"])) for x in booked if r["id"] in x.get("room_ids", [])]
        gaps = gaps_of(held, lo, end, timedelta(minutes=args.minutes)) if lo < end else []
        if gaps:
            rows.append({**room_row(r, places), "gaps": [{"start": stamp(a), "end": stamp(b), "when": when(a, b)} for a, b in gaps]})
    rows.sort(key=lambda x: (x["gaps"][0]["start"], x["name"]))
    return {"within": when(start, end), "minutes": args.minutes, "count": len(rows), "rooms": rows[:MOST_FREE],
            "cut": len(rows) > MOST_FREE, "word": ROOM_GAPS_ONLY}


def free_none_word(minutes: int | None) -> str:
    """빈 방이 없을 때의 말 — 넓힐 길을 댄다."""
    return (f"그 구간 안에 {minutes} 분 넘게 비는 회의실이 없다. 다음: 구간을 넓히거나 --where 를 넓혀 다시 본다" if minutes else
            "그 시각 내내 빈 회의실이 없다. 다음: --minutes <분> 을 더해 그 구간 안에서 비는 때를 보거나 --where 를 넓혀 다시 본다")


def day_grid(app, args, now: datetime) -> dict:
    """day 의 답 — 낱말에 걸린 회의실들 → 그날의 예약 → 회의실마다 한 묶음 → 답 크기."""
    me = app.me()
    d = asked_day(args.date, now.date())
    rooms, places = room_book(app)
    hit = day_rooms(rooms, places, args.words)
    return fit(day_answer(d, hit, day_bookings(app, d), places, me), "rooms", "id", DAY_ROOMS_CUT)


def day_rooms(rooms: list, places: Places, words: list) -> list:
    """현황을 볼 회의실 — 낱말이 다 든 곳. 하나도 안 걸리면 Stop(인자)."""
    hit = find_rooms(rooms, places, words)
    if not hit:
        raise Stop(EXIT_ARGS, "args", DAY_NONE.format(words=" ".join(words)))
    return hit


def day_bookings(app, d: date) -> list:
    """그날(서울)에 걸친 살아 있는 예약 — 시작 차례로."""
    return sorted(live_within(app, *day_span(d, d), *day_bounds(d, d)), key=lambda x: x["start_time"])


def day_answer(d: date, hit: list, booked: list, places: Places, me: dict) -> dict:
    """현황의 답 — 그날 · 걸린 회의실 수 · 회의실마다 그 방의 예약 묶음(앞의 ``MOST_GRID`` 곳만 싣는다)."""
    grid = [{**room_row(r, places), "bookings": [day_cell(x, r, me) for x in booked if r["id"] in x.get("room_ids", [])]}
            for r in hit[:MOST_GRID]]
    return {"day": d.isoformat(), "weekday": WEEKDAYS[d.weekday()], "count": len(hit), "rooms": grid, "cut": len(hit) > MOST_GRID}


def day_cell(x: dict, r: dict, me: dict) -> dict:
    """현황의 예약 한 칸 — 내가 주관한 줄만 참석자 · 취소 key 를 싣는다(취소 확인에 참석자를 보인다)."""
    own = mine_to_change(x, me["id"])
    return booking_row(x, me["id"], {r["id"]: r["name"]}, people=own, keyed=own)


def mine_of(app, args, now: datetime) -> dict:
    """mine 의 답 — 구간 → 그 구간의 내 예약 → 답(내가 주관한 줄에 취소 key) → 답 크기."""
    me = app.me()
    first, last = mine_days(args, now.date())
    out = mine_answer(now.date(), first, last, mine_within(app, first, last), me)
    return fit(out, "bookings", "day", MINE_CUT, last=last.isoformat())


def mine_within(app, first: date, last: date) -> list:
    """내 예약 가운데 첫날 ~ 끝날(서울)에 걸친 것 — 시작 차례로. 취소 · 거절된 줄도 든다(상태로 보인다)."""
    lo, hi = day_bounds(first, last)
    return sorted((x for x in app.mine() if overlaps(x, lo, hi)), key=lambda x: x["start_time"])


def mine_answer(today: date, first: date, last: date, rows: list, me: dict) -> dict:
    """내 예약의 답 — 오늘 · 구간 · 예약 줄."""
    return {"today": today.isoformat(), "today_weekday": WEEKDAYS[today.weekday()], "first": first.isoformat(),
            "last": last.isoformat(), "bookings": [booking_row(x, me["id"]) for x in rows]}


READ_HANDS = {"prefs": prefs_of, "rooms": rooms_of, "free": free_rooms, "day": day_grid, "mine": mine_of}   # 읽는 명령 → 그 손


# ── 바꾸기 ──────────────────────────────────────────────────────────────
FAILED = object()                         # 바꾼 뒤 다시 읽기가 진 것 — 「없다」(None)와 가른다


def cancel(app, mrs, args, me: dict, start: str) -> dict:
    """한 건 취소 — 다시 읽고 거절 까닭을 보고, 반복 전체면 넘기고, 보인 판과 같을 때만 지우고, 다시 읽어 맺는다."""
    rid = start_id(args, start)
    base = reread(app, rid)
    if base is None:
        return word_answer("gone")
    why = refusal(base, me["id"], start)
    if why:
        return refused_answer(why)
    if start == "series":
        return cancel_series(app, mrs, args, me, base)
    if shown_changed(row_key(base), args.confirm):
        return word_answer("moved", booking=booking_row(base, me["id"]))
    sent(mrs, lambda: app.delete(rid))   # 답 전에 끊겨도 다시 보내지 않는다 — 아래 다시 읽기가 맺는다
    back = after_write(lambda: reread(app, rid), FAILED)
    return word_answer("cancelled" if back is None else "unsure", booking=booking_row(base, me["id"], keyed=False))


def cancel_series(app, mrs, args, me: dict, base: dict) -> dict:
    """반복 전체 취소 — 보인 판(회차 모두의 열쇠)과 같을 때만 지우고, 그 반복의 회차가 내 예약에서 다 사라졌나 다시 읽어 가린다."""
    rows = series_rows(app, base)
    head = booking_row(rows[0], me["id"], keyed=False)
    now_key = series_key(rows)
    if shown_changed(now_key, args.confirm):
        return word_answer("moved", booking={**head, "key": now_key}, series={"count": len(rows)})
    if has_past(rows, datetime.now(KST)):
        return word_answer("blocked", blocks=[PAST_SERIES_CANCEL])
    got = sent(mrs, lambda: app.delete_series(base["id"]))
    got = {} if got is CUT else got or {}   # 답 전에 끊겼으면 지운 수를 모른다 — 아래 다시 읽기가 맺는다
    left = after_write(lambda: series_rows(app, base), None)
    return word_answer("cancelled" if left == [] else "unsure", booking=head,
                       series={"count": len(rows), "deleted": got.get("deletedCount"), "left": None if left is None else len(left)})


def settle(app, start: str, me: dict, rid: str | None, rooms: list | None = None) -> dict:
    """바꾼 뒤의 끝 — 다시 읽어 끝 낱말 하나(모름 · 고침 · 승인 대기 · 넣음)를 낸다. 다시 읽기가 무엇으로 지든 「모른다」다(``after_write``).
    고치기는 보낸 회의실(``rooms``)이 다시 읽은 줄에 섰는지도 본다 — 고치기에서 회의실을 바꾸는 판은 회사에서 안 쟀다."""
    back = after_write(lambda: reread(app, rid), None) if rid else None
    if back is None:
        return word_answer("unsure")
    if start == "booking" and rooms is not None and sorted(back.get("room_ids") or []) != sorted(rooms):
        return word_answer("unsure", booking=booking_row(back, me["id"]))
    state = "updated" if start in IN_PLACE else ("pending" if back.get("status") == "pending_approval" else "booked")
    return word_answer(state, booking=booking_row(back, me["id"]))


def run(args, session: pathlib.Path) -> dict:
    """명령 하나의 판 — 앱 손을 세우고 그 명령의 손에 넘긴다. 세션은 부른 쪽이 쥐어 준다."""
    mrs = load("mrs", HERE)
    app = mrs.App(session)
    now = datetime.now(KST)
    if args.command in READS:
        return READ_HANDS[args.command](app, args, now)
    if args.command == "pref":
        return pref(app, mrs, args)
    start = fingers(args)
    me = app.me()
    if args.command == "cancel":
        return cancel(app, mrs, args, me, start)
    return write(app, mrs, args, me, now, start)


def write(app, mrs, args, me: dict, now: datetime, start: str) -> dict:
    """넣기 · 고치기 · 반복 고치기와 그 미리 보기 — 판을 짓고, 없음 · 거절 · 미리 보기 · 바뀜 · 막힘을 가르고, 보내고, 맺는다."""
    p = plan(app, args, me, now, start)
    if p["state"] == "gone":
        return word_answer("gone")
    if p["state"] == "refused":
        return refused_answer(p["reason"])
    if args.command == "preview":
        return shown(p)
    if shown_changed(p["key"], args.confirm):
        return word_answer("moved", preview=shown(p))
    if not p["ok"]:
        return word_answer("blocked", blocks=p["blocks"])
    held = start_id(args, start, IN_PLACE)
    got = sent(mrs, lambda: send(app, start, held, p["body"]))
    if got is CUT:
        return settle(app, start, me, held, p["body"]["room_ids"])
    return sent_answer(app, start, me, held, p, got)


def send(app, start: str, held: str | None, body: dict):
    """판의 몸통을 보낸다 — 반복 전체 고치기 · 한 건 고치기 · 새로 넣기(본뜨기 · 반복 넣기도). 앱의 답."""
    if start == "series":
        return app.update_series(held, body)
    return app.update(held, body) if start == "booking" else app.create(body)


def sent_answer(app, start: str, me: dict, held: str | None, p: dict, got) -> dict:
    """보낸 뒤의 답 — 다시 읽어 맺고(``settle``), 반복 넣기면 청한 · 선 회차 수, 반복 고치기면 고친 수와 회차마다 섰나를 단다."""
    got, first, made = unwrapped(got)
    out = settle(app, start, me, first.get("id") or held, p["body"]["room_ids"])
    if made is not None:
        out["series"] = {"asked": len(p.get("occurrences") or []), "made": len(made)}
    if start == "series":
        out["series"] = {"count": p["series"]["count"], "updated": got.get("updatedCount")}
        if out["state"] == "updated":
            out = series_checked(app, held, p["body"], out)
    return out


def unwrapped(got) -> tuple[dict, dict, list | None]:
    """앱이 보낸 뒤 낸 답 — (답, 첫 예약, 반복 넣기면 선 회차들 · 아니면 None). 반복 넣기의 답은 회차들을 감싸고 한 건은 예약 그대로다."""
    got = got if isinstance(got, dict) else {}
    made = got.get("reservations")
    first = made[0] if made else got
    return got, first, made


def series_checked(app, held: str, body: dict, out: dict) -> dict:
    """반복 고치기가 회차마다 섰나 — 다시 읽어(``after_write``) 다 섰으면 그 답 그대로, 아니면 「확인 못 했다」."""
    took = after_write(lambda: series_took(app, held, body), False)
    if took:
        return out
    return {**out, **word_answer("unsure")}


def parser() -> argparse.ArgumentParser:
    """명령의 인자 표 — 하위 명령과 인자를 표 넷(``STARTS`` · ``CHANGES`` · ``ENDS`` · ``READS``)에서 세우고, 머리 · 지도 · 종료 값 범례를 --help 에 단다."""
    raw = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(description=common_steps(), epilog=f"{finger_map()}\n\n{EXITS}", formatter_class=raw)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("rooms", help=READS["rooms"])
    r.add_argument("word", nargs="*", help="이름 · 지역 · 건물 · 층의 일부(빈칸으로 여럿)")
    r.add_argument("--favorites", action="store_true", help="즐겨찾는 회의실만(즐겨찾기가 없으면 전부에서 찾고 note 로 말한다)")
    f = sub.add_parser("free", help=READS["free"])
    f.add_argument("--start", required=True, help=STAMP_HELP)
    f.add_argument("--end", required=True, help=STAMP_HELP)
    f.add_argument("--minutes", type=int, help="이만큼 넘게 비는 때를 그 구간 안에서 찾는다")
    f.add_argument("--where", nargs="*", help="지역 · 건물 · 층 · 이름의 일부")
    f.add_argument("--people", type=int, help="주관자 포함 인원 — 정원이 이보다 작은 곳은 뺀다")
    f.add_argument("--favorites", action="store_true", help="즐겨찾는 회의실만(즐겨찾기가 없으면 전부에서 찾고 note 로 말한다)")
    d = sub.add_parser("day", help=READS["day"])
    d.add_argument("words", nargs="*", help="지역 · 건물 · 층 · 이름의 일부(다 든 회의실들)")
    d.add_argument("--date", help=f"{DAY_HELP}(기본 오늘)")
    m = sub.add_parser("mine", help=READS["mine"])
    m.add_argument("first", nargs="?", metavar="첫날", help=f"{DAY_HELP}(기본 오늘)")
    m.add_argument("last", nargs="?", metavar="끝날", help=f"첫날과 같은 꼴 — 주면 첫날부터 그날까지(둘 다 든다), 안 주면 첫날부터 {MINE_DAYS} 날")
    sub.add_parser("prefs", help=READS["prefs"])
    pr = sub.add_parser("pref", help="⚠ 내 설정 하나 바꾸기 — --confirm 없이 부르면 미리 보기 · key, 그 key 로 다시 부르면 바꾼다")
    for k, (flag, word) in PREF_ACTIONS.items():
        pr.add_argument(flag, dest=k, default=None, help=word)
    pr.add_argument("--to", nargs="*", default=None, help="그룹의 사람 — 메일 주소(빈칸 · 쉼표로 여럿)")
    pr.add_argument("--to-file", nargs="*", default=None, help="그룹의 사람 — 주소 파일(한 줄에 하나)")
    ep_command.add_people_file(pr, "그룹의 사람 — 사람마다 그 메일 주소")
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


def guard_change(args, today: date) -> None:
    """미리 보기 · 넣기 · 고치기 · 취소의 세션 앞 거름 — 표에 없는 손가락 · 빠진 값(``fingers``), 시각의 꼴(차례는 있던 예약의 시각을 읽어야
    가려 판의 blocks 가 든다), 반복 끝 날, 사람 파일. 틀리면 Stop(인자)."""
    fingers(args)
    for given_at in (getattr(args, "start", None), getattr(args, "end", None)):
        if given_at:
            kst(given_at)
    if getattr(args, "until", None):
        until_day(args.until)
    ep_command.people_of(getattr(args, "people_file", None))


GUARDS = {   # 명령 → 세션 앞 거름. 날 · 시각의 꼴과 사람 파일이 틀렸으면 세션을 받기 전에 Stop(인자) — 로그인을 청할 일이 아니다
    "mine": lambda args, today: mine_days(args, today),
    "day": lambda args, today: asked_day(args.date, today),
    "free": lambda args, today: free_span(args),
    "pref": lambda args, today: ep_command.people_of(getattr(args, "people_file", None)),
    **{name: guard_change for name in ("preview", *ENDS)},
}


def work(args, mrs) -> dict:
    """명령 하나 — 세션 앞 거름을 지난 뒤 세션을 쥐고 판을 돈다."""
    if args.command in GUARDS:
        GUARDS[args.command](args, datetime.now(KST).date())
    return ep_session.session_first(lambda f: run(args, f), expired=(mrs.SessionExpired, mrs.SessionMissing),
                                    file_first=args.command not in MUTATING)


def main() -> int:
    """명령 입구 — 인자를 읽고 앱 손을 실어 ``work`` 의 답을 JSON 하나로 찍는다(종료 값은 ``ep_command.finish``)."""
    args = parser().parse_args()
    return ep_command.finish(lambda mrs: work(args, mrs), "mrs", HERE, indent=INDENT)


if __name__ == "__main__":
    sys.exit(main())
