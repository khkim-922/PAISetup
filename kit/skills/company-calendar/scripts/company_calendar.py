"""회사 일정 스킬의 얇은 명령 — 곁의 일정 손(``agenda.py``)을 불러 보기 · 넣기 · 지우기를 한다.

부르는 꼴::

    python -X utf8 -I company_calendar.py --help      # 지도 — 출발 × 바꿀 것 × 끝 · 읽기. 아래 표(STARTS · CHANGES · ENDS · READS)에서 짓는다
    python -X utf8 -I company_calendar.py show [오늘|내일|모레|YYYY-MM-DD] [끝 날] [--shared] [--who 이름 …] [--people-file people.json …]
                                               [--free 분 [--hours HH:MM-HH:MM]]
    python -X utf8 -I company_calendar.py calendars
    python -X utf8 -I company_calendar.py preview --title T --start "YYYY-MM-DD HH:MM" --end "…" [--note N]   # 안 바꾼다 · key 를 낸다
    python -X utf8 -I company_calendar.py preview --title T --due "<날>[ HH:MM]" [--alongside "시작|끝|제목" …]   # 기한 알림 자리를 손이 찾는다
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

내는 것 — 표준 출력에 JSON 하나. 종료 값과 그 뜻은 맨 위 ``--help`` 의 범례(``EXITS`` — ``ep_command.exit_legend``)가 낸다. 일정 줄 — ``day`` · ``weekday`` · ``when`` · ``start`` · ``end`` · ``handle``(지우기의 열쇠 ·
사람에게 안 보인다) · ``pending``(참석 답을 안 한 받은 초대) · ``keep`` 이 차면 지우지 않는 줄이고 ``keep_word`` 가 사람에게 할 말이다 ·
기본 밖 내 일정함 · 공유 줄은 ``calendar``(어느 일정함) · 공유 줄은 ``private``(일정함을 가진 사람이 비공개로 든 것). 시각을 못 읽어
뺀 줄이 있으면 show 가 ``unread_rows``(일정함 · 줄 수)를 단다. ``--free`` 를 주면 show 가 ``free`` 를 더 낸다 — 읽은 일정함 전부가
그 분 이상 함께 비는 때(``slots``)와 시각을 짐작해 센 줄(``assumed``) · 일정함을 못 본 사람(``unseen``) · 사람에게 할 말(``word``).
어느 줄을 어떻게 세나는 ``free_of``. ``--people-file`` 을 주면 show 가 ``people``(그 일정함으로 본 사람 ``seen`` · 공유받지 않아 못 본
사람 ``unseen`` · 할 말)을 더 낸다 — 사람을 일정함에 잇는 법은 ``people_books``. preview 는 ``state``(ready · already) · ``key`` 를, 넣기 · 지우기는 ``state`` 와 사람에게 할 말 · 다음 걸음이 든
``state_word`` 를 낸다.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EP_LOGIN_SCRIPTS))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    from ep_command import (DAY_HELP, EXIT_ARGS, EXIT_OK, EXIT_SESSION, EXIT_TOOL, EXIT_URL, OUT_BYTES, STAMP_HELP, WEEKDAYS, Change, NotYet,
                            Start, Stop, day_of, gaps_of, given, load, size, stamp)
except ImportError:                             # 형제 스킬 ep-login 이 곁에 없다 — 답의 꼴(JSON 하나 · 종료 1)은 지킨다
    print(json.dumps({"error": "tool", "message": f"스킬 ep-login 이 이 스킬 곁에 없다: {EP_LOGIN_SCRIPTS} — 설치를 다시 돌린다"}, ensure_ascii=False))
    sys.exit(1)

SAVED_URL = "~/.company-calendar.json"   # 남긴 일정 앱 주소 — 저장소 밖 · 비밀이 없다(사번 · 쿠키가 안 든다)
INDENT = 1                               # 답(JSON)을 찍는 들여쓰기 — 답의 크기도 이 꼴로 센다
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
ROOM_BOOKING = "[회의실 예약]"            # 회의실 예약 앱이 Teams 일정함에 저절로 넣는 줄의 제목 머리(references/SOURCES.md)
# 기한 알림(preview --due) — 시각이 있는 기한은 그 시각에 끝나는 알림, 시각이 없는 기한은 그날 근무 구간(WORK_HOURS)의 첫 빈 자리
REMINDER_MINUTES = 15
ALONG_SPLIT = "|"                         # --alongside 「시작|끝|제목」 — preview 답의 alongside 가 이 꼴 그대로다


# ── 손가락의 표 — 출발 × 바꿀 것 × 끝. 손가락을 더하거나 빼는 일은 이 표의 줄과 그 일을 하는 손 하나다(칸의 꼴은 ep_command) ──────
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
ON_SCREEN = f"사람에게 {SCREEN}에서 하시라 권한다"
EDIT_ON_SCREEN = f"한 건 고치기는 제목 · 장소 · 시각만 받는다(일정 화면의 미리 보기 [저장] · 끌어 옮기기와 같은 크기). {ON_SCREEN}(그 일정의 [상세보기])"
NEW_ONLY = f"넣을 때만 고른다 — 넣은 일정의 이 칸은 {SCREEN}의 [상세보기]에서 고친다"
CHANGES = {
    "title": Change((("--title", {}),), ("new", "event"), "제목 — 60 자에서 자르고 줄바꿈 · 안 보이는 글자를 걷는다", "", ("new",)),
    "start": Change((("--start", {"help": f"{STAMP_HELP} — 하루 종일이면 YYYY-MM-DD(첫날)"}),), ("new", "event"),
                    "시작 — 한 건 고치기에서 시작만 주면 길이를 지켜 옮긴다", "", ("new",)),
    "end": Change((("--end", {"help": f"{STAMP_HELP} — 하루 종일이면 YYYY-MM-DD(끝날 · 그날도 든다)"}),), ("new", "event"),
                  "끝 — 사람이 끝을 안 말했으면 지어 넣지 말고 묻는다", "", ("new",)),
    "place": Change((("--place", {}),), ("new", "event"), "장소 — 60 자에서 자른다. 회의실 예약은 아니다(스킬 company-meeting-room)", ""),
    "note": Change((("--note", {}),), ("new",), "설명 — 80 자에서 자른다", EDIT_ON_SCREEN),
    "private": Change((("--private", {"action": "store_const", "const": True}),), ("new",),
                      "비공개 — 다른 분께 제목이 안 보이고 바쁜 때로만 선다", NEW_ONLY),
    "all_day": Change((("--all-day", {"action": "store_const", "const": True}),), ("new",),
                      "하루 종일 — --start · --end 를 날짜(YYYY-MM-DD · 끝날도 든다)로 준다", NEW_ONLY),
    "important": Change((("--important", {"action": "store_const", "const": True}),), ("new",), "중요 표시", NEW_ONLY),
    "due": Change((("--due", {"metavar": "날[ HH:MM]"}),), ("new",),
                  f"기한 알림 — --start · --end 대신. 시각이 있으면 그 시각에 끝나는 {REMINDER_MINUTES}분, 없으면 그날 {WORK_HOURS} 의 첫 빈 "
                  f"{REMINDER_MINUTES}분(빈 곳이 없으면 첫 자리 · 겹침은 clash)을 손이 찾는다. preview 만 받는다 — add 는 답의 start · end 로",
                  "기한 알림은 새로 넣을 때만 — 있던 일정은 --start · --end 로 옮긴다"),
    "alongside": Change((("--alongside", {"action": "append", "metavar": "시작|끝|제목"}),), ("new",),
                        "함께 넣는 일정 — 같은 확인에서 사람이 함께 고른 다른 건의 preview 답 alongside 를 그대로(여럿이면 거듭). 그 건을 겹침에 "
                        "「planned」 로 보이고 기한 알림이 그 자리를 피한다 — 그 건을 먼저 넣어도 이 건의 key 가 그대로다. preview · add 에 같게 준다",
                        "함께 넣는 일정은 새로 넣을 때만 받는다"),
}
# 아직 없는 손가락 — 회사에서 그 화면 동작을 재 오면 이 줄을 걷고 CHANGES 한 줄과 손의 그 칸을 더한다. 안 짓는 것은 까닭을 든다
NOT_YET = {
    "repeat": NotYet("반복 일정 넣기 · 회차 지우기", f"반복은 상세 화면에만 있고 회사에서 아직 안 쟀다. {ON_SCREEN} — 한 번만 넣을 것이면 --repeat 없이 부른다",
                     (("--repeat", {"metavar": "주기"}),)),
    "remind": NotYet("알림(메일 · 팝업) 걸기", f"알림은 상세 화면에만 있고 회사에서 아직 안 쟀다(울리는 것은 그 시각이 와야 잰다). {ON_SCREEN}",
                     (("--remind", {"metavar": "분"}),)),
    "invite": NotYet("참석자 부르기", "이 손은 참석자 칸을 늘 비워 누구에게도 알림이 안 간다. 사람들과 만나는 회의는 스킬 company-meeting-room 으로 "
                     f"회의실과 함께 잡는다(참석자에게 안내가 간다). 회의실 없이 초대만 보낼 것이면 {ON_SCREEN}",
                     (("--to", {"nargs": "*", "metavar": "메일"}),)),
    "shared": NotYet("공유받은 일정함에 넣기 · 지우기", f"공유받은 일정함은 읽기만 한다. {ON_SCREEN}", (("--who", {"action": "append", "metavar": "이름"}),)),
    "reply": NotYet("참석 답(수락 · 거절)", f"답하면 초대한 분께 알림이 가 회사에서 아직 안 쟀다. 초대 메일이나 {SCREEN}에서 사람이 한다"),
    "copy": NotYet("일정 복사 · 여러 건 한꺼번에 지우기 · 지난 일정 한꺼번에 지우기",
                   f"한 번 부름은 일정 한 건이다 — 복사는 새로 넣기(preview → add)로, 지우기는 건마다 delete 로 한다. 한꺼번에는 {ON_SCREEN}"),
    "notice": NotYet("참석자 · 참조자 부르기 · 메일 알림 · PC 영상회의 만들기",
                     "남에게 메일이 가는 일이다 — 사람들과 만나는 회의는 스킬 company-meeting-room 이 회의실 · 참석자 · Teams 링크와 함께 잡는다"),
    "settings": NotYet("일정함 색 · 보임 · 공유 일정함 더하기 · 환경설정", f"일정 내용이 아니라 화면 설정이다. {ON_SCREEN}"),
}
ENDS = {
    "add": End("넣기", ("new",), "--confirm <preview 의 key> — 보인 값(제목 · 날 · 시각 · 장소 · 설명 · 공개 범위 · 하루 종일 · 중요)과 "
               "내 일정함 전부의 겹침 · 이미 있나. 다시 지은 판이 다르면 안 넣는다", True),
    "edit": End("고치기", ("event",), "--confirm <preview --handle 의 key> — 지금 값과 바뀔 값 · 새 시각의 겹침. 보인 뒤 그 줄이 바뀌었으면 "
                "안 고친다. 손수 든 단건이고 참석자 · 참조자가 없는 것만 고친다", True),
    "delete": End("지우기", ("event",), "--handle 이 곧 열쇠 — 보인 줄의 지문(제목 · 시작 · 끝)이라 그 줄이 바뀌었으면 안 지운다. "
                  "손수 든 단건만 지운다(keep 이 빈 줄)", False),
}
READS = {
    "show": "일정 — 날 하나나 구간(기본 오늘 · 내일). 내 일정함(기본 · Teams)은 늘 들고, --who 이름(여럿)은 그 공유 일정함을 곁에, "
            "--people-file(주소록의 people.json)은 사람마다 그 사람의 공유 일정함을 곁에(공유받지 않은 사람은 이름으로 따로 선다), "
            f"--shared 는 공유 일정함 전부를 곁에. --free 분 은 읽은 일정함 전부가 그 분 이상 함께 비는 때(평일 · 기본 {WORK_HOURS} · "
            "--hours 로 구간을 준다 — 사람이 고른 한 때가 되나도 그 구간을 주어 본다)",
    "calendars": "공유받은 일정함 목록 — 누가 있나는 사람마다 달라 --who 의 이름을 여기서 본다",
    "event": "일정 한 건 — show · find 의 줄의 id 로 장소 · 설명 · 참석자와 응답 · 참조자 · Teams 링크(내 일정함 · Teams 의 줄만)",
    "find": "찾기 — --text 낱말(제목 · 설명 · 장소 어디든 · 기간 없이) 이나 --title · --place · --note · --attendee(함께 건다 · "
            "--from · --to 기간, 기본 앞뒤 1 년). 내 기본 일정함과 Teams 일정함(회의실 예약이 드는 곳 — 제목으로만 · 칸 조건이면 그 기간, "
            "--text 면 오늘 앞뒤 1 년)",
}
MUTATING = tuple(ENDS)                   # 회사 일정을 바꾼다 — 세션 손부터 받아 한 번만 돈다
# 이 명령이 내는 종료 값 — 뜻은 ep_command 의 한 표, 여기는 이 손이 덧붙일 말만. 「보인 판과 다르다」는 종료 값이 아니라 0 의 state moved 다
EXITS = ep_command.exit_legend((EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION, EXIT_URL),
                               {EXIT_OK: "넣기 · 고치기 · 지우기가 보인 판과 달라 안 했으면 0 에 state moved — 답의 지금 판을 다시 보인다",
                                EXIT_ARGS: "없는 손가락 · 빠진 값이면 어디서 하나나 받는 꼴을 댄다"})

# 지우지 않는 줄 — 사람에게 할 말. 까닭은 agenda.Event.keep_reason 이 가른다
KEEP_WORDS = {
    "invite": "받은 회의 초대입니다 — 지우면 곧 참석 답이 됩니다. 참석 답은 초대 메일이나 회사 일정 화면에서 해 주세요",
    "meeting": "회의로 든 일정입니다 — 지우면 참석하실 분께 알림이 갈 수 있어 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "repeat": "반복 일정입니다 — 지우기가 그날 하나만 걷는지 아직 확인하지 않아 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "all_day": "하루 종일 일정입니다 — 시각을 옮기거나 시각 있는 일정으로 바꾸는 것은 여기서 하지 않습니다(제목 · 장소 고치기 · 지우기는 합니다). 회사 일정 화면에서 해 주세요",
    "locked": "고칠 수 있는 일정으로 읽히지 않았습니다 — 일정 앱이 막은 것인지 그 표시를 못 알아본 것인지 가리지 못해 여기서는 지우지 않습니다. 회사 일정 화면에서 지워 주세요",
    "shared": "다른 일정함(공유받은 것 · Teams)의 일정입니다 — 여기서는 읽기만 합니다",
    "no_doc": "일정 줄에 문서 열쇠가 없어 그 일정을 열어 보지 못했습니다 — 참석자가 있는지 몰라 여기서는 고치지 않습니다. 회사 일정 화면에서 고쳐 주세요",
    "guests": "참석자 · 참조자가 든 일정입니다 — 고치거나 지우면 그분들께 알림이 갈 수 있어 여기서는 하지 않습니다. 회사 일정 화면에서 해 주세요",
}
# 넣기 · 지우기의 끝 — 낱말 하나가 뜻 하나다(형제 스킬 company-meeting-room 의 같은 낱말과도 같은 뜻)
STATE_WORDS = {
    "added": "넣었습니다(다시 읽어 확인했습니다). 다음: 이 줄의 handle 을 들고 있다가 「방금 것 지워 줘」 에 delete --handle 로 쓴다",
    "already": "같은 일정(제목 · 시작 · 끝)이 이미 있어 넣지 않았습니다",
    "moved": "보여 드린 뒤 달라진 것이 있어 하지 않았습니다. 다음: 답의 preview · event(지금 판)를 보이고 다시 묻는다 — 답에 없으면 "
             "preview · show 로 다시 읽어 보인다",
    "deleted": "지웠습니다(다시 읽어 사라진 것을 확인했습니다)",
    "edited": "고쳤습니다(다시 읽어 바뀐 값을 확인했습니다). 다음: 답의 event 의 handle 이 새 손잡이다 — 옛 handle 은 안 맞는다",
    "gone": "그날 일정에 없습니다 — 이미 지워졌거나 다른 날로 옮겨졌습니다",
    "refused": "여기서는 하지 않습니다 — 답의 reason 에 맞는 말을 그대로 전한다",
    "unsure": "됐는지 확인하지 못했습니다. 다음: 다시 부르지 말고 show 로 그날을 읽어 보인다",
}
# 손(agenda)의 끝 낱말 → 이 명령의 낱말 — 손의 clashed(확인 뒤 새 겹침) · changed(보인 뒤 바뀐 줄)는 다 「보인 판과 다르다」다
ADDED_STATE = {"added": "added", "already": "already", "clashed": "moved", "unsure": "unsure"}
REMOVED_STATE = {"deleted": "deleted", "gone": "gone", "changed": "moved", "unsure": "unsure"}
EDITED_STATE = {"edited": "edited", "gone": "gone", "changed": "moved", "unsure": "unsure"}



# ── 표에서 짓는 것 — 지도 · 인자 거르기 ────────────────────────────────────────────────────────────
def common_steps() -> str:
    """맨 위 --help 의 머리 — 자주 쓰는 길을 그대로 칠 수 있는 꼴로, 그리고 오늘과 날짜 표. 요일로 말한 날을 모델이 고르는 자리다."""
    return "\n".join([
        f"회사 일정 — 보기 · 넣기 · 지우기. {ep_command.today_word()}", "",
        "자주 쓰는 길 — 그대로 쳐서 쓴다(<…> 만 갈아 끼운다)",
        "  여럿이 다 비는 때  show <날> [<끝날>] --who <이름> --free <분> [--hours HH:MM-HH:MM]   (주소록의 사람이면 --people-file <people.json>)",
        "  새 일정            preview --title <제목> --start \"<날> HH:MM\" --end \"<날> HH:MM\"  →  add …같은 값… --confirm <key>",
        "  기한 알림          preview --title <제목> --due \"<날>[ HH:MM]\"  →  add --title <제목> --start <답의 start> --end <답의 end> --confirm <key>",
        "  여러 건을 함께     둘째 건부터 preview · add 에 --alongside <앞 건 preview 답의 alongside> — 앞 건을 넣어도 뒤 건의 key 가 그대로다",
        "  한 건 옮기기       show <날> 의 그 줄 handle → preview --handle <handle> --start \"<날> HH:MM\"  →  edit …같은 값… --confirm <key>",
        "  한 건 지우기       delete --handle <show 의 handle>",
        f"  날은 {DAY_HELP} · 시각은 \"<날> HH:MM\"(「내일 15:00」) — 답의 day · weekday 로 사람이 바로잡게 보인다",
        f"  요일로 말한 날은 어느 날인지 정해 날짜로 준다(손이 고르지 않는다) — 날짜 표: {ep_command.weeks_word(datetime.now(ep_command.SEOUL).date())}"])


def finger_map() -> str:
    """--help 의 지도 — 표 넷에서 짓는다."""
    names = list(STARTS)
    lines = ["지도 — 출발 하나 × 바꿀 것 아무 조합 × 끝 하나. 한 번 부름이 일정 한 건을 한 번 다룬다", "", "출발"]
    lines += [f"  {k:<7} {s.takes + ' <…>' if s.takes else '(인자 없음)':<14} {s.word} — {s.screen}" for k, s in STARTS.items()]
    lines += ["", "바꿀 것 (● 꼭 든다 · ○ 받는다 · — 없다)"] + ep_command.change_lines(CHANGES, names, 12)
    lines += ["", "끝 (⚠ 회사 일정을 바꾼다 — 사람이 그 한 건을 보고 「네」 한 뒤에만)"]
    lines += [f"  {k:<7} 출발 {' · '.join(e.starts):<6} {e.word} — 열쇠: {e.key}" for k, e in ENDS.items()]
    lines += ["", "읽기"] + [f"  {k:<10} {w}" for k, w in READS.items()]
    lines += ["", "아직 없는 손가락 (인자를 주면 세션 전에 사람이 어디서 하나를 대며 종료 2 로 멈춘다)"]
    lines += ep_command.not_yet_lines(NOT_YET, CHANGES, 10)
    return "\n".join(lines)


def fingers(args) -> str:
    """부른 명령의 출발을 고르고 표에 대 본다 — 아직 없는 손가락 · 출발에 없는 끝 · 손가락, 빠진 값은 그 일을 어디서 하는지 대며
    Stop(인자). 출발을 낸다."""
    ep_command.refuse_not_yet(args, NOT_YET, CHANGES)
    start = ep_command.pick_start(args, STARTS)
    word = STARTS[start].word
    ends = [k for k, e in ENDS.items() if start in e.starts]
    # 손가락을 끝보다 먼저 본다 — 「내 일정 한 건」을 고치려는 부름(preview --handle --start)이 「미리 보기가 없다 · 그 끝(지우기)으로」가
    # 아니라 고치기를 어디서 하나를 받게
    ep_command.refuse_foreign(args, CHANGES, start, word)
    if getattr(args, "due", None) is not None:
        if args.command != "preview":
            raise Stop(EXIT_ARGS, "args", f"--due 는 preview 만 받는다. 다음: {args.command} 에는 preview 답의 start · end 를 --start · --end 로 준다")
        if args.start is not None or args.end is not None or args.all_day:
            raise Stop(EXIT_ARGS, "args", "--due 는 --start · --end · --all-day 와 함께 주지 않는다 — 손이 알림 자리를 찾는다. 다음: 셋을 빼고 "
                                          "--due 만 주거나, 시각을 정했으면 --due 없이 --start · --end 로 준다")
    end = args.command
    if end == "preview":
        end = next((k for k in ends if ENDS[k].confirm), "")
        if not end:
            raise Stop(EXIT_ARGS, "args", f"「{word}」의 끝({' · '.join(ends)})은 미리 보기가 없다 — "
                                          f"{' · '.join(ENDS[k].key for k in ends)}. 다음: 사람에게 그 줄을 보이고 그 끝으로 부른다")
    if start not in ENDS[end].starts:
        raise Stop(EXIT_ARGS, "args", f"「{word}」에서는 {end}({ENDS[end].word})를 못 한다 — 이 출발의 끝: "
                                      f"{' · '.join(ends)}. 다음: 출발을 바꾸거나({' · '.join(s.takes or k for k, s in STARTS.items())}) 끝을 바꾼다")
    timed = (CHANGES["start"], CHANGES["end"])
    ep_command.refuse_missing(args, CHANGES, start, word, lambda c: c in timed and getattr(args, "due", None) is not None)
    changing = [c.flags[0][0] for c in CHANGES.values() if given(args, c)]
    if not ENDS[end].confirm and changing:
        raise Stop(EXIT_ARGS, "args", f"{end}({ENDS[end].word})는 바꿀 것({' · '.join(changing)})을 안 받는다. 다음: 바꾸려면 preview --handle … 로 "
                                      "고칠 판을 보이고 edit 로 부른다")
    if start != "new" and ENDS[end].confirm and not changing:
        raise Stop(EXIT_ARGS, "args", f"「{word}」을 고치려면 바꿀 것이 하나는 든다. 다음: --title · --place · --start · --end 가운데 바꿀 것을 "
                                      "더해 다시 부른다")
    return start


def key_of(view: dict) -> str:
    """보인 판의 열쇠 — 판(보인 값과 그 둘레) 전체의 해시(``ep_command.fingerprint``). 같은 판이면 늘 같은 글자다."""
    return ep_command.fingerprint(view)


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


def row(agenda, e) -> dict:
    out = {"day": e.day.isoformat(), "weekday": weekday_of(e.day), "when": e.when(), "start": stamp(e.start),
           "end": stamp(e.end), "title": e.title, "handle": agenda.Seen.of(e).handle, "keep": e.keep_reason,
           "pending": e.response == agenda.RESPONSE_PENDING, "meeting": e.meeting, "repeat": e.repeat, "all_day": e.all_day}
    if e.important:                      # 「중요」 표시 — 켠 줄에만 싣는다(답의 꼴을 늘리지 않게)
        out["important"] = True
    if e.unid:                           # 한 건 읽기(event <id>)의 열쇠 — 내 일정함(기본 · Teams)의 줄
        out["id"] = e.unid
    if e.keep_reason:
        out["keep_word"] = KEEP_WORDS.get(e.keep_reason, e.keep_reason)
    if e.calendar:                       # 기본 밖 내 일정함 · 공유받은 일정함의 줄 — 어느 일정함인가. 지우는 손잡이는 없다
        out["calendar"] = e.calendar
        del out["handle"]
        if e.title.strip().startswith(ROOM_BOOKING):
            out["room_booking"] = True   # 회의실 예약이 저절로 든 줄 — 회의실 · 참석자 · 취소는 스킬 company-meeting-room 의 mine
    return out


def shared_row(agenda, e) -> dict:
    out = row(agenda, e)
    out["private"] = e.private           # 일정함을 가진 사람이 비공개로 든 것
    del out["pending"]                   # 참석 답은 그 일정함을 가진 사람의 것이라 내 초대로 읽히지 않게 뺀다
    out.pop("id", None)                  # 남의 서버 · DB 의 문서라 한 건 읽기가 안 묻는다
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
        raise Stop(EXIT_ARGS, "args", f"공유받은 일정함에 「{', '.join(lost)}」가 없다 — 있는 것: {have}. 다음: 있는 이름의 일부로 다시 준다 — "
                                      f"공유받지 않은 분이면 주소록의 사람 파일을 {ep_command.PEOPLE_FLAG} 로 주어 못 본 분으로 이름을 댄다")
    return [b for b in books if any(w in b.name for w in names)]


# 줄의 칸이 보장하는 것 — 이 말로 다시 묻지 않게 한다(meeting 이 회의실을 뜻하나 · 회의실 예약이 일정에 섰나)
SHOW_WORD = ("meeting 은 일정 앱의 회의 꼴(참석자를 부른 일정)일 뿐 회의실과 무관하다. 회의실 예약은 Teams 일정함에 「[회의실 예약] 제목」 줄로 "
             "저절로 서고(calendar · room_booking 이 붙는다) 취소하면 함께 사라진다 — 회의실 · 참석자 · Teams 링크는 스킬 company-meeting-room 의 "
             "mine. handle 이 있는 줄만 고치기 · 지우기를 받고, keep 이 찬 줄은 keep_word 를 전한다")
NOT_SHARED = "일정함을 공유받지 않았다"
NO_NOTES = "주소록에 Notes 이름이 없어 일정함을 못 맞췄다 — 이름으로 맞추면 동명이인을 엉뚱한 일정함에 잇는다. --who 로 일정함을 고른다"
UNSEEN_WORD = ("일정함을 못 본 분({who})은 셈에 없다 — 그분이 그때 비는지는 모른다고 사람에게 말하고 그분께 직접 여쭙게 한다(공유하지 않은 "
               "일정함의 빈 때를 보는 길은 회사에서 안 쟀다).")


def unseen_word(unseen: list) -> str:
    """일정함을 못 본 사람들을 사람에게 할 말 하나로 — 동명이인이 갈리게 부서를 붙인다."""
    return UNSEEN_WORD.format(who=", ".join(" · ".join(filter(None, (u.get("name"), u.get("dept")))) for u in unseen))


def people_books(reader, people) -> tuple[list, list, list]:
    """사람 파일의 사람마다 그 사람의 일정함 — (곁에 읽을 공유 일정함, 본 사람, 못 본 사람). 사람은 Notes 이름으로만 일정함에 잇는다 —
    공유 일정함 줄의 일정함을 가진 사람(``Book.owner``)이 그것이고, 이름은 동명이인이 갈라지지 않는다. 쓰는 사람 자신은 내 일정함이다.
    공유받지 않은 사람 · Notes 이름이 빈 사람은 못 본 사람으로 까닭과 함께 낸다 — 셈에서 말없이 「빈다」로 넘어가지 않게."""
    mine = ep_command.notes_key(reader.book().owner)
    by_owner: dict[str, list] = {}
    for b in reader.shared_books():                  # 한 사람이 일정함을 둘 이상 공유했으면 다 읽는다
        by_owner.setdefault(ep_command.notes_key(b.owner), []).append(b)
    books, seen, unseen = [], [], []
    for p in people:
        key = ep_command.notes_key(p.notes)
        who = {k: v for k, v in (("name", p.name), ("dept", p.dept), ("grade", p.grade)) if v}
        if key and key == mine:
            seen.append({**who, "calendar": MY_BOOK})
        elif key in by_owner:
            for b in by_owner[key]:
                seen.append({**who, "calendar": b.name})
                if b not in books:
                    books.append(b)
        else:
            unseen.append({**who, "why": NO_NOTES if not key else NOT_SHARED})
    return books, seen, unseen


def whole_day_of(text: str) -> date:
    """하루 종일의 첫날 · 끝날 — 날 말 · 요일 말 · YYYY-MM-DD(``day_of``)."""
    try:
        return day_of(text, datetime.now(ep_command.SEOUL).date())
    except Stop as exc:
        raise Stop(EXIT_ARGS, "args", f"하루 종일은 --start · --end 를 날로 준다 — {exc}") from exc


def want_of(args, agenda):
    if args.all_day:
        start, end = agenda.whole_days(whole_day_of(args.start), whole_day_of(args.end))
    else:
        start, end = agenda.kst(args.start), agenda.kst(args.end)
    w = agenda.Want(args.title, start, end, args.note or "", place=args.place or "", private=bool(args.private),
                    all_day=bool(args.all_day), important=bool(args.important)).cleaned()
    if not w.title:
        raise Stop(EXIT_ARGS, "args", "제목이 비었다(보이지 않는 글자만 들었다). 다음: 사람에게 보일 제목을 --title 로 준다")
    if w.end <= w.start:
        raise Stop(EXIT_ARGS, "args", f"끝({stamp(w.end)})이 시작({stamp(w.start)})보다 앞이거나 같다. 다음: 끝을 시작 뒤로 준다 — 사람이 끝을 "
                                      "안 말했으면 지어 넣지 말고 묻는다")
    return w


@dataclass(frozen=True)
class Along:
    """같은 확인에서 사람이 함께 고른 다른 한 건(``--alongside``) — 겹침에 「planned」 로 서고, 그 건이 먼저 들어 일정에 서도 이 건의
    판은 같다."""
    title: str
    start: datetime
    end: datetime

    def word(self) -> str:
        return ALONG_SPLIT.join((stamp(self.start), stamp(self.end), self.title))


def alongs_of(args, agenda) -> list:
    """``--alongside`` 들 — 「시작|끝|제목」(preview 답의 alongside 그대로). 꼴이 아니면 Stop(인자) — 세션 전에 가린다."""
    out = []
    for text in getattr(args, "alongside", None) or ():
        parts = (text or "").split(ALONG_SPLIT, 2)
        if len(parts) != 3:
            raise Stop(EXIT_ARGS, "args", f"--alongside 는 「시작{ALONG_SPLIT}끝{ALONG_SPLIT}제목」 꼴이다: {text!r}. 다음: 함께 넣는 건의 preview 답 "
                                          "alongside 를 손대지 않고 준다")
        a, b = (ep_command.stamp_of(p) for p in parts[:2])
        title = agenda.clean_title(parts[2])
        if not title or b <= a:
            raise Stop(EXIT_ARGS, "args", f"--alongside 의 제목이 비었거나 끝이 시작보다 앞이다: {text!r}. 다음: preview 답 alongside 를 그대로 준다")
        out.append(Along(title, a, b))
    return out


def along_row(a: Along) -> dict:
    """겹침에 서는 함께 넣는 건 — 일정 줄과 같은 칸에 「planned」."""
    return {"day": a.start.date().isoformat(), "weekday": weekday_of(a.start.date()), "when": f"{a.start:%H:%M}–{a.end:%H:%M}",
            "start": stamp(a.start), "end": stamp(a.end), "title": a.title, "planned": True}


def landed_of(agenda, mine: list, alongs: list) -> list:
    """함께 넣는 건 가운데 이미 기본 일정함에 선 줄 — 제목 · 시작 · 끝이 같은 것만(``agenda.same_event``). 시각만 겹치는 줄을 여기 넣으면
    사람이 못 본 일정이 겹침에서 말없이 빠져 그 위에 넣는다."""
    return [e for e in mine if not e.calendar and any(agenda.same_event(e, agenda.Want(a.title, a.start, a.end)) for a in alongs)]


def plan_new(args, agenda, reader) -> tuple[dict, object, list]:
    """새 일정 한 건의 판 — (보일 판 · 넣을 것 · 확인에 보인 겹침의 일정 줄). 바꾸지 않는다. preview 와 add 가 같은 판을 짓고, 판 전체의
    해시가 key 다 — 값이든 겹침이든 이미 있나든 보인 뒤 달라졌으면 key 가 달라진다. 함께 넣는 건(``--alongside``)은 일정에 섰든 안 섰든
    겹침에 「planned」 한 줄로 서서, 그 건을 먼저 넣어도 이 판이 그대로다 — 그 건과 겹친다는 것은 확인 때 이미 보였다."""
    w = want_of(args, agenda)
    alongs = alongs_of(args, agenda)
    mine, side_failed = reader.mine_between(w.day, w.last_day)   # 겹침은 내 일정함 전부(기본 · Teams)에서 본다
    same = next((e for e in mine if not e.calendar and agenda.same_event(e, w)), None)   # 이미 있나는 넣을 자리(기본 일정함)에서만
    landed = landed_of(agenda, mine, alongs)
    clash =[e for e in mine if e.overlaps(w.start, w.end) and e is not same and e not in landed]
    planned = [a for a in alongs if a.start < w.end and w.start < a.end]
    when = (f"하루 종일({w.day.isoformat()}" + (f" ~ {w.last_day.isoformat()})" if w.last_day != w.day else ")") if w.all_day
            else f"{w.start.astimezone(agenda.KST):%H:%M}–{w.end.astimezone(agenda.KST):%H:%M}")
    view = {"state": "already" if same else "ready", "title": w.title, "note": w.note, "day": w.day.isoformat(),
            "weekday": weekday_of(w.day), "when": when,
            "start": w.day.isoformat() if w.all_day else stamp(w.start),
            "end": w.last_day.isoformat() if w.all_day else stamp(w.end),
            "visibility": agenda.PRIVATE if w.private else agenda.VISIBILITY,
            "already": row(agenda, same) if same else None, "clash": [row(agenda, e) for e in clash] + [along_row(a) for a in planned]}
    for k, v in (("place", w.place), ("all_day", w.all_day), ("important", w.important)):
        if v:
            view[k] = v
    if w.all_day:
        view["last_day"], view["last_weekday"] = w.last_day.isoformat(), weekday_of(w.last_day)
    if side_failed:
        view["shared_failed"] = [{"calendar": n, "message": m} for n, m in side_failed]
    view["key"] = key_of(view)
    if not w.all_day:                    # 판 밖의 덧말 — 같은 확인에서 함께 넣을 다음 건의 --alongside 에 그대로 준다
        view["alongside"] = Along(w.title, w.start.astimezone(ep_command.SEOUL), w.end.astimezone(ep_command.SEOUL)).word()
    return view, w, clash + [e for e in landed if e.overlaps(w.start, w.end)]


def change_of(args, agenda):
    return agenda.Change(title=args.title, place=args.place, start=agenda.kst(args.start) if args.start else None,
                         end=agenda.kst(args.end) if args.end else None).cleaned()


def plan_edit(args, agenda, reader) -> dict:
    """내 일정 한 건을 고칠 판 — 지금 값 · 바뀔 값 · 새 시각의 겹침 · 고칠 수 있나. 바꾸지 않는다. preview 와 edit 가 같은 판을 짓고
    그 해시가 key 다 — 보인 뒤 그 줄 · 장소 · 겹침이 바뀌었으면 key 가 달라진다."""
    seen = agenda.Seen.parse(args.handle)
    state, hit = agenda.locate(reader, reader.book(), seen)
    if state:
        state = EDITED_STATE[state]
        return {"state": state, "event": row(agenda, hit) if hit else None}
    c = change_of(args, agenda)
    doc = reader.detail(hit.unid) if hit.unid else None
    start = c.start or hit.start
    end = c.end or (start + (hit.end - hit.start) if c.start else hit.end)
    if end <= start:
        raise Stop(EXIT_ARGS, "args", f"옮길 끝({stamp(end)})이 시작({stamp(start)})보다 앞이거나 같다. 다음: 시작만 주면 길이를 지켜 옮긴다 — "
                                      "끝을 주려면 시작 뒤로 준다")
    if c.title is not None and not c.title:
        raise Stop(EXIT_ARGS, "args", "제목을 비울 수는 없다. 다음: 바꿀 제목을 --title 로 준다 — 제목을 안 바꾸면 --title 을 뺀다")
    refuse = hit.keep_reason
    if not refuse and hit.all_day and c.moves:
        refuse = agenda.KEEP_ALL_DAY
    if not refuse and (doc is None or doc.guests):
        refuse = agenda.KEEP_GUESTS if doc is not None else "no_doc"
    was = {"title": agenda.clean_title(hit.title), "place": doc.place if doc else "", "when": hit.when(), "start": stamp(hit.start),
           "end": stamp(hit.end), "day": hit.day.isoformat(), "weekday": weekday_of(hit.day)}
    new_day = agenda.kst_day(start)
    becomes = {"title": c.title if c.title is not None else was["title"], "place": c.place if c.place is not None else was["place"],
               "when": hit.when() if hit.all_day else f"{start.astimezone(agenda.KST):%H:%M}–{end.astimezone(agenda.KST):%H:%M}",
               "start": stamp(start), "end": stamp(end), "day": new_day.isoformat(), "weekday": weekday_of(new_day)}
    view = {"state": "refused" if refuse else "ready", "was": was, "becomes": becomes, "clash": []}
    if refuse:
        view["reason"], view["state_word"] = refuse, KEEP_WORDS.get(refuse, refuse)
    elif c.moves:
        mine, side_failed = reader.mine_between(new_day, agenda.kst_day(end - timedelta(microseconds=1)))
        view["clash"] = [row(agenda, e) for e in mine if e.overlaps(start, end) and e.event_id != hit.event_id]
        if side_failed:
            view["shared_failed"] = [{"calendar": n, "message": m} for n, m in side_failed]
    view["key"] = key_of(view)
    return view


def detail_of(agenda, reader, unid: str) -> dict:
    """일정 한 건의 답 — 줄에 안 오는 칸. 사람 칸은 이름 · 메일 · 응답 · 한마디."""
    d = reader.detail(unid)
    people = lambda xs: [{k: v for k, v in {"name": x.name, "email": x.email, "response": x.response,   # noqa: E731
                                            "comment": x.comment}.items() if v} for x in xs]
    out = {"id": d.unid, "title": d.title, "place": d.place, "note": d.note, "attendees": people(d.attendees),
           "references": people(d.references), "meeting_url": d.meeting_url, "organizer": d.organizer,
           "private": d.visibility == agenda.PRIVATE}
    pending = [x.name for x in d.attendees if x.response == agenda.RESPONSE_PENDING]
    out["word"] = (f"참석자 {len(d.attendees)} 명(답 전 {len(pending)})" if d.attendees else "참석자 없음") + \
        (f" · 참조 {len(d.references)} 명" if d.references else "") + (" · Teams 링크가 있다" if d.meeting_url else "") + \
        ". 참석 답 · 참석자 바꾸기는 여기서 하지 않는다"
    return out


FIND_SPAN_DAYS = 366                      # 찾기의 기본 기간 — 오늘 앞뒤로 이만큼(화면 상세검색은 올해 하나다)


def find_span(args, today: date) -> tuple[date, date] | None:
    """찾기의 인자 — 본문 낱말(--text)이면 None, 칸 조건이면 (첫날, 끝날). 세션 없이 가린다 — 섞인 조건 · 빈 조건 · 틀린 날 · 거꾸로 선
    기간은 Stop(인자)."""
    if args.text:
        if any((args.title, args.place, args.note, args.attendee, args.since, args.until)):
            raise Stop(EXIT_ARGS, "args", "--text 는 홀로 준다(칸 조건 · 기간과 섞지 않는다). 다음: 낱말로 찾으면 --text 만, 칸 · 기간으로 찾으면 "
                                          "--title · --place · --note · --attendee · --from · --to 만 준다")
        return None
    if not any((args.title, args.place, args.note, args.attendee)):
        raise Stop(EXIT_ARGS, "args", "찾을 것이 없다. 다음: --text 낱말 · --title · --place · --note · --attendee 가운데 하나는 준다")
    try:
        first = day_of(args.since, today) if args.since else today - timedelta(days=FIND_SPAN_DAYS)
        last = day_of(args.until, today) if args.until else today + timedelta(days=FIND_SPAN_DAYS)
    except Stop as exc:
        raise Stop(EXIT_ARGS, "args", f"찾기의 기간 — {exc}") from exc
    if last < first:
        raise Stop(EXIT_ARGS, "args", f"--to({last})가 --from({first})보다 앞이다. 다음: 둘을 맞바꿔 --from <첫날> --to <끝날> 차례로 준다")
    return first, last


TEAMS_SKIPPED = ("Teams 일정함(회의실 예약이 드는 곳)은 줄에 장소 · 설명 · 참석자 칸이 안 와 이 조건으로는 안 봤다 — 회의실 예약은 스킬 "
                 "company-meeting-room 의 mine 이 회의실 · 참석자와 함께 낸다. ")


def side_found(args, agenda, reader, span, today: date) -> tuple[list, list, bool]:
    """찾기의 Teams 일정함 쪽 — 찾기 화면은 그 일정함을 안 찾아(회사에서 잼 · 0 건), show · preview 가 겹침을 볼 때 읽는 일정 목록을
    기간째 읽고 제목으로 거른다. 줄에 장소 · 설명 · 참석자가 안 와 그 조건이 들면 안 읽는다. (걸린 줄, 못 읽은 일정함, 읽었나)."""
    if any((args.place, args.note, args.attendee)):
        return [], [], False
    word = agenda.clean_title(args.text or args.title or "").casefold()
    if not word:
        return [], [], False
    first, last = span or (today - timedelta(days=FIND_SPAN_DAYS), today + timedelta(days=FIND_SPAN_DAYS))
    hits, failed, books = [], [], reader.side_books()
    for b in books:
        try:
            rows = reader.between(first, last, b)
        except agenda.SessionExpired:
            raise
        except agenda.CalendarError as exc:      # 한 일정함이 안 읽혀도 기본 일정함의 찾기는 낸다 — 못 읽은 것은 이름으로 알린다
            failed.append({"calendar": b.name, "message": str(exc)})
            continue
        hits += [e for e in rows if word in agenda.clean_title(e.title).casefold()]
    return hits, failed, bool(books)


def find_of(args, agenda, reader, today: date) -> dict:
    """찾기 — 본문 낱말(--text) 이나 칸 조건(--title · --place · --note · --attendee · 기간). 내 기본 일정함과, 제목으로는 Teams
    일정함(``side_found``)도."""
    span = find_span(args, today)
    if span is None:
        got, how = reader.search_text(args.text), "text"
    else:
        got = reader.search(title=args.title or "", place=args.place or "", note=args.note or "", attendee=args.attendee or "",
                            first=span[0], last=span[1])
        how = "fields"
    side, failed, side_read = side_found(args, agenda, reader, span, today)
    have = {agenda.event_key(e) for e in got}
    rows = []
    for e in sorted(got + [e for e in side if agenda.event_key(e) not in have], key=lambda e: (e.start, e.title)):
        r = {"day": e.day.isoformat(), "weekday": weekday_of(e.day), "start": stamp(e.start), "title": e.title,
             "id": e.unid, "meeting": e.meeting, "repeat": e.repeat, "all_day": e.all_day,
             "pending": e.response == agenda.RESPONSE_PENDING}
        if (how == "text" or e.calendar) and e.end > e.start:   # Teams 일정함의 줄은 일정 목록에서 와 끝 시각이 든다
            r["end"] = stamp(e.end)
        if e.calendar:
            r["calendar"] = e.calendar
        rows.append(r)
    out = {"found": rows, "count": len(rows),
           "word": ("본문 낱말로 찾았다 — 지난 해 일정도 든다. " if how == "text" else
                    "칸 조건으로 찾았다 — 기본 일정함의 줄은 끝 시각이 안 온다(시각은 event 나 show 그날로 본다). ") +
                   ((f"Teams 일정함(회의실 예약이 드는 곳)은 제목으로 {'오늘 앞뒤 1 년' if span is None else '같은 기간'} 안에서 찾았다 — 그 줄은 "
                     "calendar 가 붙는다. " if side_read else TEAMS_SKIPPED if reader.side_books() else "")) +
                   "다음: 장소 · 참석자는 event <id>, 고치기 · 지우기는 show <그날> 의 handle 로"}
    if failed:
        out["shared_failed"] = failed
    return out


def holidays_of(reader, agenda, first: date, last: date) -> tuple[dict, str]:
    """공휴일 {날: 이름} 과 못 읽은 까닭 — 못 읽어도 보기는 선다(끊긴 세션은 올린다)."""
    try:
        return reader.holidays(first, last), ""
    except agenda.CalendarError as exc:   # 끊김 꼴(공용 DB 가 다른 곳으로 보냄)도 — 일정은 이미 읽혔으니 보기를 막지 않는다
        return {}, str(exc)


def show_days(args, today: date) -> tuple[date, date]:
    """show 의 첫날 · 끝날 — 첫날을 안 주면 오늘 · 내일, 첫날만 주면 그 하루. 꼴이 아니거나 끝날이 첫날보다 앞이면 Stop(인자)."""
    try:
        first = day_of(args.first or "오늘", today)
        last = day_of(args.last, today) if args.last else (first + timedelta(days=1) if not args.first else first)
    except Stop as exc:
        raise Stop(EXIT_ARGS, "args", f"show 의 날 — {exc}") from exc
    if last < first:
        raise Stop(EXIT_ARGS, "args", f"끝날({last})이 첫날({first})보다 앞이다. 다음: show <첫날> <끝날> 차례로 준다")
    return first, last


# ── 모두 비는 때 ────────────────────────────────────────────────────────────────────────────────
def free_window(args) -> tuple[time, time] | None:
    """show 의 --free · --hours — (하루의 처음, 끝) 이나 --free 가 없으면 None. 틀렸으면 Stop(인자)."""
    if args.free is None:
        if args.hours:
            raise Stop(EXIT_ARGS, "args", "--hours 는 --free 와 함께 준다 — 다음: show … --free <분> --hours HH:MM-HH:MM")
        return None
    if args.free <= 0:
        raise Stop(EXIT_ARGS, "args", "--free 는 1 분 이상으로 준다. 다음: 함께 비어야 할 길이(분 — 회의 한 시간이면 60)를 준다")
    found = HOURS_FORM.match(args.hours or WORK_HOURS)
    try:
        lo, hi = (datetime.strptime(t, "%H:%M").time() for t in found.groups()) if found else (None, None)
    except ValueError:
        lo = hi = None
    if lo is None or hi <= lo:
        raise Stop(EXIT_ARGS, "args", f"--hours 는 「HH:MM-HH:MM」(서울 · 앞이 뒤보다 이르게)으로 준다: {args.hours!r}. 다음: 오후면 13:00-18:00 처럼 준다")
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
        if first == last:                                  # 하루짜리는 그날 00:00:30 ~ 23:59:59 로 온다(회사에서 잼) — 그날 내내 바쁘다
            return span, ""
        return span, f"여러 날 하루 종일 일정이다 — 줄의 꼴을 {UNMEASURED}. 그날들 내내 바쁜 것으로 셌다"
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
            counted: list, failed: list, unread: list, holidays: dict | None = None, holidays_failed: str = "",
            unseen: list | None = None) -> dict:
    """읽은 일정함 전부가 ``minutes`` 분 이상 함께 비는 때 — 평일마다 ``hours`` 안에서, 지난 시각은 빼고. 바쁜 구간은 ``busy_of`` 가
    정하고 틈은 ``ep_command.gaps_of`` 가 센다. 시각을 짐작한 줄 · 못 읽은 일정함 · 시각을 못 읽어 뺀 줄 · 일정함을 못 본 사람(``unseen`` —
    ``people_books``)은 답에 달고 ``word`` 가 사람에게 그렇다고 말하라 이른다 — 셈에서 말없이 「빈다」로 넘어가지 않게."""
    spans, doubt = [], []
    for e in events:
        span, why = busy_of(agenda, e)
        if span:
            spans.append(span)
        if why:
            doubt.append((e, span, why))
    weekend, off, open_days = [], [], []
    holidays = holidays or {}
    day = first
    while day <= last:
        if day.weekday() in WEEKEND:
            weekend.append(day.isoformat())
        elif day in holidays:
            off.append({"day": day.isoformat(), "weekday": weekday_of(day), "name": holidays[day]})
        else:
            open_days.append(day)
        day += timedelta(days=1)

    def windows_of(span: tuple[time, time]) -> list:
        out_ = []
        for d in open_days:
            lo = max(datetime.combine(d, span[0], agenda.KST), next_step(now.astimezone(agenda.KST)))
            hi = datetime.combine(d, span[1], agenda.KST)
            if lo < hi:
                out_.append((lo, hi))
        return out_

    def slot_rows(found: list) -> list:
        return [{"day": a.astimezone(agenda.KST).date().isoformat(), "weekday": weekday_of(a.astimezone(agenda.KST).date()),
                 "when": f"{a.astimezone(agenda.KST):%H:%M}–{b.astimezone(agenda.KST):%H:%M}", "start": stamp(a),
                 "end": stamp(b), "minutes": int((b - a).total_seconds() // 60)} for a, b in found]

    windows = windows_of(hours)
    need = timedelta(minutes=minutes)
    slots = [g for lo, hi in windows for g in gaps_of(spans, lo, hi, need)]
    out = {"minutes": minutes, "hours": f"{hours[0]:%H:%M}–{hours[1]:%H:%M}", "counted": counted, "slots": slot_rows(slots)}
    # 고른 구간에 없으면 같은 날(들)의 근무 구간 안 다른 비는 때 — 사람이 「없다」 뒤에 바로 다른 때를 고르게. 짓는 것은 없다: 같은 셈을 넓은 구간에
    wide = tuple(datetime.strptime(t, "%H:%M").time() for t in HOURS_FORM.match(WORK_HOURS).groups())
    nearby = []
    if not slots and (wide[0] < hours[0] or hours[1] < wide[1]):
        nearby = [g for lo, hi in windows_of(wide) for g in gaps_of(spans, lo, hi, need)]
        out["nearby"] = slot_rows(nearby)

    def touches(e, span) -> bool:
        a, b = span or (e.start, e.start)
        return any((a < hi and lo < b) if span else lo <= a < hi for lo, hi in windows)
    assumed = [{**{k: v for k, v in row(agenda, e).items() if k in ("day", "when", "title", "calendar")}, "why": why}
               for e, span, why in doubt if touches(e, span)]
    if assumed:
        out["assumed"] = assumed
    if weekend:
        out["weekend"] = weekend
    if off:
        out["holidays"] = off
    said = [f"{', '.join(counted)} 의 일정을 견줘 평일 {out['hours']} 안에서 {minutes} 분 이상 함께 비는 때 {len(slots)} 곳"
            + ("" if slots else " — 그 구간에 모두 비는 때가 없다") + "(주말 · 공휴일 · 지난 시각은 뺐다)."]
    if nearby:
        said.append(f"같은 날 근무 구간({WORK_HOURS}) 안의 다른 비는 때 {len(nearby)} 곳이 nearby 에 있다 — 「없다」 와 함께 사람에게 보이고 고르게 한다.")
    elif not slots:
        said.append("다음: 날을 넓혀(show <첫날> <끝날> … --free) 다시 보거나, 길이(--free 분)를 줄여도 되는지 사람에게 여쭌다 — 비는 때를 짓지 않는다.")
    if off:
        said.append(f"공휴일({', '.join(h['day'] + ' ' + h['name'] for h in off)})은 뺐다 — 사람에게 그렇다고 말한다.")
    if holidays_failed:
        said.append("공휴일 목록을 못 읽어 공휴일을 안 뺐다 — 고른 날이 공휴일인지 사람에게 확인받는다.")
    if failed:
        said.append(f"못 읽은 일정함({', '.join(f['calendar'] for f in failed)})은 셈에 없다 — 그분의 일정은 안 견줬다고 말한다.")
    if unseen:
        out["unseen"] = unseen
        said.append(unseen_word(unseen))
    if unread:
        said.append("시각을 못 읽어 뺀 줄이 있다(unread_rows) — 그 일정함에 셈에 없는 일정이 있을 수 있다고 말한다.")
    if assumed:
        said.append("assumed 의 줄은 시각을 짐작해 셌다 — 그 줄과 까닭을 함께 말하고 사람이 바로잡게 한다.")
    said.append("다음: 사람에게 고르게 하고, 고른 때의 start · end 로 회의실을 찾는다(스킬 company-meeting-room 의 free --start --end).")
    out["word"] = " ".join(said)
    return out


def due_of(text: str, today: date) -> tuple[date, datetime | None]:
    """--due 의 (날, 마감 시각이나 None) — 「<날> HH:MM」 이면 시각이 있는 기한, 날만이면 없는 기한. 꼴이 아니면 Stop(인자) — 세션 전에 가린다."""
    try:
        at = ep_command.stamp_of(text)
        return at.date(), at
    except Stop:
        pass
    try:
        return day_of(text, today), None
    except Stop as exc:
        raise Stop(EXIT_ARGS, "args", f"--due 는 날이나 「<날> HH:MM」 으로 준다 — {exc}") from exc


def due_span(args, agenda, reader, now: datetime) -> tuple[datetime, datetime, str]:
    """기한 알림의 (시작, 끝, 어떻게 골랐나). 시각이 있는 기한은 그 시각에 끝나는 ``REMINDER_MINUTES`` 분이다. 시각이 없는 기한은 그날
    ``WORK_HOURS`` 안(오늘이면 지금 뒤 첫 눈금부터)에서 내 일정함 전부와 함께 넣는 건(``--alongside``)이 비운 첫 ``REMINDER_MINUTES`` 분이고,
    빈 곳이 없으면 그 구간의 첫 자리다 — 겹침은 판의 clash 가 보인다. 하루 종일 알림으로 넣지 않는다 — 하루 종일 줄은 다 비는 때의 셈에서
    그날을 통째로 막는다(``busy_of``)."""
    day, at = due_of(args.due, now.astimezone(agenda.KST).date())
    length = timedelta(minutes=REMINDER_MINUTES)
    if at is not None:
        return at - length, at, f"마감 시각에 끝나는 {REMINDER_MINUTES}분 알림"
    lo_t, hi_t = (datetime.strptime(t, "%H:%M").time() for t in HOURS_FORM.match(WORK_HOURS).groups())
    lo, hi = datetime.combine(day, lo_t, ep_command.SEOUL), datetime.combine(day, hi_t, ep_command.SEOUL)
    if day == now.astimezone(agenda.KST).date():
        lo = max(lo, next_step(now.astimezone(ep_command.SEOUL)))
    if day < now.astimezone(agenda.KST).date() or lo + length > hi:
        raise Stop(EXIT_ARGS, "args", f"{day.isoformat()}({weekday_of(day)})의 근무 구간({WORK_HOURS})이 이미 지났다 — 알림 자리가 없다. "
                                      "다음: 사람에게 알림을 언제 둘지 여쭙고 --start · --end 로 준다")
    mine, _failed = reader.mine_between(day, day)
    spans = [s for s in (busy_of(agenda, e)[0] for e in mine) if s] + [(a.start, a.end) for a in alongs_of(args, agenda)]
    gaps = gaps_of(spans, lo, hi, length)
    if gaps:
        return gaps[0][0], gaps[0][0] + length, f"마감 시각이 없어 그날 {WORK_HOURS} 의 첫 빈 {REMINDER_MINUTES}분"
    return lo, lo + length, f"마감 시각이 없고 그날 {WORK_HOURS} 에 빈 {REMINDER_MINUTES}분이 없어 첫 자리 — 겹치는 일정은 clash 를 보인다"


def run(args, session: pathlib.Path) -> dict:
    agenda = load("agenda", HERE)
    url, by_default = resolve(args, agenda.DEFAULT_APP_URL)
    today = datetime.now(agenda.KST).date()
    if args.command == "remember":
        url = (args.address or "").strip()
    found = agenda.APP_URL.match(url)
    if not found:
        raise Stop(EXIT_URL, "url", f"일정 앱 주소(…/calperson<NN>.nsf)가 든 주소가 아니다. {NEXT_URL}")
    url = found.group(1) + found.group(2)
    reader = agenda.Reader(url, session)
    if args.command == "remember":
        try:
            reader.book()                # 이 주소로 내 일정함이 읽히나 — 읽혀야 남긴다
        except agenda.SessionExpired:
            raise
        except agenda.CalendarError as exc:
            raise Stop(EXIT_URL, "url", f"이 주소로 내 일정함을 못 읽었다({exc}). {NEXT_URL}") from exc
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
    if args.command == "event":
        return detail_of(agenda, reader, args.id)
    if args.command == "find":
        return find_of(args, agenda, reader, today)
    if args.command == "show":
        first, last = show_days(args, today)
        out = {"today": today.isoformat(), "today_weekday": weekday_of(today), "first": first.isoformat(), "last": last.isoformat()}
        hours = free_window(args)
        mine, side_failed = reader.mine_between(first, last)
        out["events"] = [row(agenda, e) for e in mine]
        out["word"] = SHOW_WORD
        failed = [{"calendar": n, "message": m} for n, m in side_failed]
        counted = [MY_BOOK] + [b.name for b in reader.side_books() if b.name not in {n for n, _ in side_failed}]
        shared = []
        picked = shared_books(reader, args.who) if args.shared or args.who else []
        seen, unseen = [], []
        if args.people_file:
            books, seen, unseen = people_books(reader, ep_command.distinct(ep_command.people_of(args.people_file)))
            picked += [b for b in books if b not in picked]
        if picked or args.shared or args.who:
            for b in picked:
                try:
                    shared += reader.between(first, last, b)
                    counted.append(b.name)
                except agenda.CalendarError as exc:   # 한 일정함이 안 읽혀도 나머지는 보인다 — 못 읽은 것은 이름으로 알린다
                    # 그 서버의 「끊긴 세션」 꼴도 여기 든다 — 방금 같은 세션으로 목록을 읽었으니 공유가 풀렸거나 그 서버가 안 받는
                    # 것이다. ep-login 으로 보내면 같은 끝을 되풀이한다
                    failed.append({"calendar": b.name, "message": str(exc)})
            shared.sort(key=lambda e: (e.start, e.end, e.calendar))
            out["shared"] = [shared_row(agenda, e) for e in shared]
        if args.people_file:
            lost = {f["calendar"] for f in failed}       # 일정함을 골랐어도 못 읽은 분은 본 분이 아니다
            unseen += [{**{k: v for k, v in s.items() if k != "calendar"}, "why": f"일정함({s['calendar']})을 못 읽었다 — shared_failed"}
                       for s in seen if s["calendar"] in lost]
            seen = [s for s in seen if s["calendar"] not in lost]
            out["people"] = {"seen": seen, "unseen": unseen,
                             "word": (unseen_word(unseen) + " " if unseen else "") + "본 분의 일정은 그 일정함(seen 의 calendar)으로 읽었다"}
        if failed:
            out["shared_failed"] = failed
        if reader.unread:
            out["unread_rows"] = [{"calendar": n or MY_BOOK, "rows": k} for n, k in reader.unread]
        holidays, holidays_failed = holidays_of(reader, agenda, first, last)
        if holidays:
            out["holidays"] = [{"day": d.isoformat(), "weekday": weekday_of(d), "name": n} for d, n in sorted(holidays.items())]
        if holidays_failed:
            out["holidays_failed"] = holidays_failed
        if hours:
            out["free"] = free_of(agenda, mine + shared, first, last, args.free, hours, datetime.now(agenda.KST), counted, failed,
                                  reader.unread, holidays, holidays_failed, unseen)
        fit_days(out, last, (" --shared" if args.shared else "") + "".join(f" --who {w}" for w in args.who or ())
                 + "".join(f' {ep_command.PEOPLE_FLAG} "{f}"' for f in args.people_file or ()))
        return out
    start = fingers(args)
    if start == "new":
        how = ""
        if getattr(args, "due", None) is not None:   # 손이 알림 자리를 고른 뒤 그 시각의 판을 짓는다 — add 가 같은 start · end 로 같은 판을 짓는다
            a, b, how = due_span(args, agenda, reader, datetime.now(agenda.KST))
            args.start, args.end = stamp(a), stamp(b)
        view, w, clash = plan_new(args, agenda, reader)
        if args.command == "preview":
            if how:                      # 판 밖의 덧말이라 key 에 안 든다
                view["due"] = {"how": how, "then": "넣을 때는 이 답의 title · start · end 를 add 의 --title · --start · --end 로 준다(add 는 "
                                                   "--due 를 안 받는다)"}
            return view
        if view["key"] != args.confirm:
            return {"state": "moved", "state_word": STATE_WORDS["moved"], "preview": view}
        if view["already"]:
            return {"state": "already", "state_word": STATE_WORDS["already"], "event": view["already"]}
        got = agenda.register(url, session, w, reader=reader, shown_clash={agenda.event_ref(e) for e in clash})
        state = ADDED_STATE[got.state]
        return {"state": state, "state_word": STATE_WORDS[state], "event": row(agenda, got.event) if got.event else None}
    if args.command in ("preview", "edit"):
        view = plan_edit(args, agenda, reader)
        if args.command == "preview" or view["state"] in ("moved", "gone"):
            return view if args.command == "preview" else {**view, "state_word": STATE_WORDS[view["state"]]}
        if view["key"] != args.confirm:
            return {"state": "moved", "state_word": STATE_WORDS["moved"], "preview": view}
        if view["state"] == "refused":
            return {"state": "refused", "reason": view["reason"], "state_word": view["state_word"]}
        try:
            got = agenda.edit(url, session, agenda.Seen.parse(args.handle), change_of(args, agenda), reader=reader)
        except agenda.ChangeRefused as exc:
            return {"state": "refused", "reason": exc.reason, "state_word": KEEP_WORDS.get(exc.reason) or str(exc)}
        state = EDITED_STATE[got.state]
        out = {"state": state, "state_word": STATE_WORDS[state], "event": row(agenda, got.event) if got.event else None}
        if got.place is not None:
            out["place"] = got.place
        if got.notice:
            out["notice"] = "일정 앱이 「참석자께 알릴까」를 물었다 — 알림은 안 보냈다"
        return out
    try:
        got = agenda.delete(url, session, agenda.Seen.parse(args.handle), reader=reader)
    except agenda.ChangeRefused as exc:
        return {"state": "refused", "reason": exc.reason, "state_word": KEEP_WORDS.get(exc.reason) or str(exc)}
    state = REMOVED_STATE[got.state]
    return {"state": state, "state_word": STATE_WORDS[state], "event": row(agenda, got.event) if got.event else None}


def parser() -> argparse.ArgumentParser:
    raw = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(description=common_steps(), epilog=f"{finger_map()}\n\n{EXITS}", formatter_class=raw)
    p.add_argument("--url", help="일정 앱 주소(…/calperson<NN>.nsf) — 없으면 CALENDAR_URL · 남긴 주소 · 잰 기본")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("remember", help="일정 앱 주소를 재 보고 남긴다")
    r.add_argument("address")
    s = sub.add_parser("show", help=READS["show"])
    s.add_argument("first", nargs="?", metavar="첫날", help=f"{DAY_HELP}(안 주면 오늘 · 내일)")
    s.add_argument("last", nargs="?", metavar="끝날", help="첫날과 같은 꼴 — 주면 첫날부터 그날까지(둘 다 든다), 안 주면 첫날 하루")
    s.add_argument("--shared", action="store_true", help="공유받은 일정함 전부를 곁에")
    s.add_argument("--who", action="append", help="공유받은 일정함 가운데 이름에 이 글자가 든 것을 곁에(여럿이면 거듭 준다)")
    ep_command.add_people_file(s, "사람마다 그 사람의 공유 일정함을 곁에. 공유받지 않은 사람은 답의 people.unseen 에 이름으로 선다")
    s.add_argument("--free", type=int, metavar="분", help="읽은 일정함 전부가 이 분 이상 함께 비는 때를 낸다(주말 · 지난 시각은 뺀다)")
    s.add_argument("--hours", metavar="HH:MM-HH:MM", help=f"--free 가 찾는 하루의 구간(기본 {WORK_HOURS})")
    sub.add_parser("calendars", help=READS["calendars"])
    e = sub.add_parser("event", help=READS["event"])
    e.add_argument("id", help="show · find 의 줄의 id")
    f = sub.add_parser("find", help=READS["find"])
    f.add_argument("--text", help="본문 낱말 — 제목 · 설명 · 장소 어디든(다른 조건과 섞지 않는다)")
    f.add_argument("--title", help="제목에 든 글자")
    f.add_argument("--place", help="장소에 든 글자")
    f.add_argument("--note", help="설명에 든 글자")
    f.add_argument("--attendee", help="참석자 이름에 든 글자")
    f.add_argument("--from", dest="since", metavar="첫날", help=f"기간의 첫날({DAY_HELP} · 기본 1 년 전)")
    f.add_argument("--to", dest="until", metavar="끝날", help="기간의 끝날(기본 1 년 뒤)")
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
            start = fingers(args)        # 없는 손가락 · 빠진 값은 세션을 받기 전에 멈춘다
            try:                         # 날 · 시각의 꼴도 세션을 받기 전에 — 넣기 · 고치기는 손부터 받는 길이다
                if start == "new" and getattr(args, "due", None) is not None:
                    due_of(args.due, datetime.now(agenda.KST).date())
                elif start == "new":
                    want_of(args, agenda)
                else:
                    agenda.Seen.parse(args.handle), change_of(args, agenda)
                alongs_of(args, agenda)
            except agenda.CalendarConfigError as exc:
                raise Stop(EXIT_ARGS, "args", str(exc)) from exc
        if args.command == "show":
            show_days(args, datetime.now(agenda.KST).date())   # 날이 틀렸으면 세션을 받기 전에 멈춘다
            free_window(args)            # --free · --hours 가 틀렸으면 세션을 받기 전에 멈춘다
            ep_command.people_of(args.people_file)   # 사람 파일이 없거나 꼴이 아니면 세션을 받기 전에 멈춘다
        if args.command == "find":
            find_span(args, datetime.now(agenda.KST).date())   # 섞인 조건 · 틀린 날도 세션을 받기 전에 — 로그인을 청할 일이 아니다
        return ep_session.session_first(lambda f: run(args, f), expired=(agenda.SessionExpired, agenda.SessionMissing),
                                        file_first=args.command not in MUTATING)

    return ep_command.finish(work, "agenda", HERE, indent=INDENT, app_error="CalendarError",
                             args_errors=("CalendarConfigError",))   # 설정 · 인자가 틀린 것은 2


if __name__ == "__main__":
    sys.exit(main())
