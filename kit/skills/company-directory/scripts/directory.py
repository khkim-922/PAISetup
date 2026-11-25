"""사내 주소록 · 조직도에서 사람을 찾는 얇은 명령이자, 사람을 받는 다른 손이 불러 쓰는 한 자리.

무엇을 하나
    출처 아무 조합(``SOURCES`` — 합친다) × 거르기 아무 조합(``SIEVES`` — 합친 명단 전체에) → 사람이 볼 수 · 표와, ``--out`` 이면 그 폴더에
    칸마다 주소 파일 · 사람 파일 둘(``people.txt`` 「이름/메일ID」 · ``people.json`` 기계가 읽는 꼴)을 쓴다. 보기(``VIEWS``)는 사람 대신
    목록(부서 나무 · 배포그룹)을 낸다. 주소록 · 메일함 어디도 안 바꾼다.

    사람 파일 ``people.json`` 은 ``{"format": 꼴 번호, "people": [{…}, …]}`` — 사람마다 칸이 다 들고 모르는 값은 빈 글자다. 꼴 번호와 칸 ·
    그 차례는 읽는 자리(형제 스킬 ep-login 의 ``ep_command.PEOPLE_FORMAT`` · ``PEOPLE_KEYS``)가 든다.
    조직 · 사외 주소는 사람이 아니라 안 든다. 주소 파일과 ``people.txt`` 는 같은 명단에서 뽑는다. 다른 손(일정 · 회의실 · 문서함)이
    ``--people-file`` 로 받고, 메일 저장은 칸마다 주소 파일을 받는다.

    사내 주소록 · 조직도는 메일 서버가 낸다 — 묻는 손은 형제 스킬 company-mail 의 ``inbox.py``(``Mailbox`` 의 주소록 · 조직도 손)이고,
    세션으로 메일함을 여는 자리(``mail_open``), 받아 둔 조직도 · 회사 값(``mail_kept``), 주소를 사람으로 잇는 자 · 배포그룹 고르기 · 사람
    한 줄의 꼴(``mail_people``), 명령을 멈추는 꼴(``mail_stop``)도 그 스킬이 내준 이름만 싣는다. 지난 메일 출처(``--last``)는 메일 한 통을
    번호로 찾기(``mail_find``)와 그 메일의 받는 사람 명단(``mail_recipients`` · ``Mailbox.sent_people``)을 받아 이 스킬의 꼴(사람 · 조직 ·
    따로 둔 줄)로 짓는다 — 내주는 이름의 한 자리는 그 스킬의 ``handout.py`` 다. 그 스킬의 명령 파일(``mail.py``)은 안 싣는다. 전화는
    형제 스킬 company-regulation 의 사람 창(``cbsop.App.person``)이 사번으로 낸다 — 그 스킬이 내준 이름(그 스킬의 ``handout.py``)만 싣는다.

어떻게 부르나
    python -X utf8 -I directory.py [--url 메일함] find <출처 · 거르기 · 보기 …>

    인자의 지도는 ``find --help`` 가 이 파일의 표에서 낸다. 인자의 꼴이 틀리면 세션을 받기 전에 종료 2 로 멈춘다(``check_args``).
    조직도만 쓰는 판(부서 · 조직 하나 · 회사 전체 · 나무)은 받아 둔 조직도로 세션 없이 선다(``asks_box`` 가 표의 ``box`` 칸에서 가른다).

받아 둔 조직도
    자리 · 꼴 · 쓰는 날 · 회사 값의 차례는 형제 스킬 company-mail 의 ``mail_kept`` 머리말이 든다 — 메일의 임시저장과 같은 판을 쓴다.

무엇을 내나
    사람이 읽을 글줄을 표준 출력에 낸다. 종료 값마다의 뜻은 맨 위 ``--help`` 의 범례(사내 앱 명령의 한 표 ``ep_command``)가 든다.
    「⚠ 따로 둔 것」(동명이인 · 못 찾은 이름 · 여럿 걸린 부서 · 못 거른 조직)은 파일에 안 든다 — 고르는 것은 사람이다. ``--out`` 의
    찾기에 이름으로 댄 것 가운데 안 선 줄(``Ask`` — 동명이인 · 못 찾은 이름 · 여럿 걸린 부서)이 있으면 파일을 안 쓰고 종료 2 로
    끝난다(``HELD_STOP``) — 이은 다음 손도 따로 부른 손도 빠진 명단으로 돌지 않게. 무리의 구성원이 안 선 줄 · 알림 줄은 파일을 쓰고 0
    이다(선 사람이 없으면 받는 손이 빈 파일에서 멈춘다).
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import functools
import json
import logging
import pathlib
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

HERE = pathlib.Path(__file__).resolve().parent
SKILLS = HERE.parents[1]                              # 형제 스킬은 스킬 홈에 나란히 깔린다
EP_LOGIN_SCRIPTS = SKILLS / "ep-login" / "scripts"
MAIL_SCRIPTS = SKILLS / "company-mail" / "scripts"
REGULATION_SCRIPTS = SKILLS / "company-regulation" / "scripts"
for _where in (EP_LOGIN_SCRIPTS, MAIL_SCRIPTS, HERE):
    if str(_where) not in sys.path:
        sys.path.insert(0, str(_where))               # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    import inbox
    from mail_find import DEFAULT_SCAN, DRAFTS, SENT, find_mail, unid_shape
    from mail_kept import DEFAULT_COMPANY, cached_org, company_of, load_org
    from mail_open import MAILFILE_NUMBER, given_url, open_mailbox, stops_from_mail
    from mail_people import (DEPT_WORD, DRAFT_AS_IS, FIELD_WORDS, GROUP_KIND_WORDS, SHOWN, address_people, can_receive, chart_book,
                             group_lists, one_group, person_line, split_kind)
    from mail_recipients import BCC_UNKNOWN, field_of, person_word, received_together, together_why
    from mail_stop import Stop, from_ep
    import findpeople
except ImportError as _missing:                       # 형제 스킬이 곁에 없다 — 주소록을 물을 손이 없어 어느 명령도 못 돈다
    print(f"형제 스킬(ep-login · company-mail)이나 이 스킬의 사람찾기 손이 곁에 없다({_missing}) — 설치를 다시 돌린다")
    sys.exit(1)

EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION = ep_command.EXIT_OK, ep_command.EXIT_TOOL, ep_command.EXIT_ARGS, ep_command.EXIT_SESSION
HELD_SHOWN = 10               # 따로 둔 줄 하나 아래 늘어놓는 후보(동명이인 · 그 글자가 든 사람 · 여럿 걸린 부서)의 수 — 넘으면 좁혀 다시 달라고 한다
TALLY_TOP = 15                # 부서별 수가 보이는 부서의 수 — 넘는 부서는 한 덩이로 접는다
NAME_SPLIT = re.compile(r"[,;·ㆍ、]")   # --name 한 값에 여럿을 이은 가름 — 사람이 말한 「김철수 · 이영희」 를 그대로 넘겨도 된다
WHO_FILE = "{field}.txt"      # --out 폴더 안의 칸마다 주소 파일 — 메일 draft 의 --to-file · --cc-file · --bcc-file 이 읽는 꼴(한 줄에 주소 하나 · # 뒤는 버린다)
# --out 폴더 안의 사람 파일 — 칸 셋을 합친 사람마다 「이름/메일ID」 한 줄(# 로 시작하는 줄은 주석). 스킬 company-ecm 의 권한 칸이
# 사람 하나를 받는 꼴이고, 메일 ID 는 주소의 @ 앞이다(문서함의 메일 ID 는 메일 주소록의 그 사람과 같다 — 그 스킬의 SOURCES.md)
PEOPLE_FILE = "people.txt"
PEOPLE_JSON = "people.json"   # 같은 폴더의 기계가 읽는 사람 파일 — 사람을 받는 손이 --people-file 로 받는다. 꼴은 읽는 자리(ep_command)가 든다
PHONE_MOST = 10               # --phone 이 사람 창을 묻는 사람 수의 위 — 사람마다 사규 앱에 한 번씩 묻는다
DETAIL_MOST = 10              # --detail 이 사람찾기 상세를 묻는 사람 수의 위 — 사람마다 한 번(0.3 초)씩 묻는다
# --detail 이 줄에 다는 상세의 칸 — 주소록 · 목록에 없는 것만. 칸 차림이 회사마다 달라 없는 칸은 건너뛴다(references/SOURCES.md)
DETAIL_FIELDS = ("직무", "근무형태", "근무현황", "원소속", "팩스", "휴대전화")
# 사람찾기 출처의 회사 말 → 회사 값 — 앱의 회사 고름 상자 이름 · 값 말고 사람이 흔히 하는 말. 「내 회사」 는 앱이 댄 쓰는 사람의 회사다
SCOPE_WORDS = {"홀딩스": "poscoinc", "지주사": "poscoinc", "그룹사": findpeople.GROUP, "국내그룹사": findpeople.GROUP}
OWN_WORDS = ("내회사", "우리회사", "회사")
DEFAULT_SCOPES = ("own", "poscoinc", findpeople.GROUP)   # 회사를 안 대면 — 내 회사 → 홀딩스 → 국내그룹사 묶음(내 회사 · 홀딩스는 묶음에 안 든다)
SEEN_NOTE = ("다른 회사 사람 {n} — 찾기만 했다. 사람 파일 · 주소 파일에 안 든다(메일 · 회의 · 결재선에 넘기지 않는다 — 사용자가 정했다)")
CUT_NOTE = ("{scope} 「{word}」 — 앱이 {total} 건이라 했는데 답이 커서 앞 {rows} 줄만 읽었다(사람찾기는 쪽을 안 나눈다). 다음: 회사를 "
            "좁히거나(--in) 말을 늘리거나 갈래를 준다(담당업무:… · 이름:…)")
# --out 의 찾기에서 이름으로 댄 것이 안 섰을 때의 끝 말(종료 2) — 그때 쓴 파일은 사람이 말한 명단의 일부다. 받는 손(임시저장 · 일정 ·
# 회의실 · 문서함)은 파일에 없는 사람을 몰라 답에도 안 세우니, 파일을 안 써야 이은 걸음도 따로 부른 걸음도 그 일부로 말없이 돌지 않는다.
# 이름 하나하나는 고르거나 빼서 다시 줄 수 있어 안 써도 막히는 길이 없다. 고르는 것은 사람이다
HELD_STOP = ("⚠ 파일을 안 썼다 — 이름으로 댄 것 가운데 한 사람 · 한 부서로 안 선 {n} 줄(위 「⚠ 따로 둔 것」)이 있다. 쓰면 그 파일을 받는 "
             "손(임시저장 · 일정 · 회의실 · 문서함)이 그 사람 없이 돌고 답에도 그 사람을 안 세운다. 다음: 그 줄을 사람에게 묻고 고른 꼴로 같은 "
             "명령을 다시 부른다. 사람이 그 사람은 빼라고 하면 그 이름 없이 다시 부른다 — 어느 쪽이든 그때 다 든 파일이 선다")
HELD_LEGEND = ("--out 의 찾기에서 이름으로 댄 사람 · 부서가 한 사람 · 한 부서로 안 섰다(동명이인 · 못 찾은 이름 · 여럿 걸린 부서) — "
               "파일을 안 썼다. 사람에게 묻고 고른 꼴로(빼라면 그 이름 없이) 다시 부른다")   # 맨 위 --help 범례의 덧말
FILE_COMMENT = "#"            # --from-file 글 파일의 주석 — 주소 파일과 같이 그 뒤는 버린다
PICK_FORM = re.compile(r"^\s*([^\[\]]+?)\s*\[([^\[\]]+)\]\s*$")   # 「이름[부서]」 — 동명이인 가운데 그 부서의 사람(괄호 () 는 ID 꼴이 쓴다)
# 지난 메일 출처에 임시메일을 준 판의 말 — 임시메일의 받는 사람은 메일 손의 read 가 보인다
LAST_DRAFT = ("임시보관함의 메일이다 — --last 는 보낸 메일 · 받은 메일을 받는다. 이 임시메일의 받는 사람은 스킬 company-mail 의 "
              'read {unid} --folder "{drafts}" 로 본다')
TITLE = "사람 찾기"            # 찾기의 답 첫 줄
RECENT_MAIL_SCAN = 300        # 동명이인 후보마다 최근 주고받은 메일을 셀 때 받은편지함 · 보낸편지함에서 받는 새것의 수 — 한 쪽씩이다
ORG, OUTSIDE, PERSON = "org", "outside", "person"   # 보낸 메일의 받는 사람 줄 하나의 꼴 — 조직(부서 주소) · 사외 주소 · 주소록에서 이을 사람
# 이름 한 줄(``resolve``)의 상태 — 한 사람으로 섰다 · 「이름[부서]」 의 부서 말이 안 맞는다 · 동명이인 · 퇴직 · 못 찾았다
STOOD, DEPT_MISS, HOMONYM, RETIRED, NOT_FOUND = "stood", "dept_miss", "homonym", "retired", "not_found"
NO_OUT, HELD, WRITE = "no_out", "held", "write"   # 파일을 써도 되나 — --out 을 안 줬다 · 이름으로 댄 것이 안 섰다 · 쓴다
# 사람마다 전화를 물은 답의 꼴(사람 창의 답 dict 가 아닐 때) — 주소록에 사번이 없다 · 사규 앱이 멈췄다 · 사람 창이 비었다
NO_EMPNO, CUT, BLANK = "no_empno", "cut", "blank"
TOO_MANY, NO_HAND = "too_many", "no_hand"   # 전화를 아무에게도 안 물은 까닭 — 명단이 너무 길다 · 사규 스킬의 앱 손을 못 실었다
NO_ADDRESS = "「{handle}」 — 주소록의 그 사람에게 메일 주소 · Notes 이름이 없어 받는 사람으로 못 넣는다: {line}"
NO_OUT_HINT = ("— 받는 사람으로 쓰려면 같은 명령에 --out <저장소 밖 폴더> — 칸마다 주소 파일을 쓰고 draft 에 그대로 줄 인자를 댄다"
               "(주소를 옮겨 적지 않는다)")
FOLDED = ("명단은 {n} 줄이라 안 실었다 — 수를 묻는 물음은 위의 수로 답한다. 다음: 좁히려면 거르기(--grade · --title · "
          "--at-least · --match), 명단을 보려면 같은 명령에 --list")
NOBODY_FILED = "— 파일에 넣을 받는 사람이 없다 — draft 인자를 안 낸다"
OUT_UNWRITTEN = "--out 폴더에 주소 파일을 못 썼다({why}) — 쓸 수 있는 저장소 밖 폴더를 준다"
BOOK_FAILED = "주소록 · 조직도에서 못 받았다: {why}"   # 메일함 손이 답을 못 받은 판 — 그 밖의 세션 · 메일함 멈춤의 말은 메일 손이 든다


# ── 한 판 ─────────────────────────────────────────────────────────────────

class Keys(NamedTuple):
    """사람을 가르는 두 열쇠 — Notes 이름의 열쇠(``inbox.notes_key`` · 없으면 빈 글자)와 주소(빈칸을 떼고 대소문자를 안 가린다)."""
    notes: str
    email: str


def keys_of(notes: str, email: str) -> Keys:
    """Notes 이름 · 주소 → 사람을 가르는 두 열쇠(``Keys``) — 사람을 견주는 자리는 다 이 열쇠로 견준다."""
    return Keys(inbox.notes_key(notes) if notes.strip() else "", email.strip().casefold())


def same_person(a, b) -> bool:
    """주소록의 두 줄이 한 사람인가 — 두 열쇠(``keys_of``)로, Notes 이름이 둘 다 있으면 그것으로, 아니면 주소로. 주소 하나를 여럿이
    함께 쓰는 줄이 한 사람으로 서지 않게 Notes 이름이 먼저다."""
    ka, kb = keys_of(a.notes, a.email), keys_of(b.notes, b.email)
    if ka.notes and kb.notes:
        return ka.notes == kb.notes
    return bool(ka.email) and ka.email == kb.email


def shares_key(a: Keys, b: Keys) -> bool:
    """두 열쇠 가운데 하나라도 같은가 — Notes 이름 열쇠든 주소든 둘 다 있고 같으면 참."""
    return bool(a.notes and a.notes == b.notes) or bool(a.email and a.email == b.email)


def rows_fit(rows: list[str], start: int) -> tuple[list[str], int | None]:
    """번호 붙인 줄 가운데 ``start`` 째부터 답 크기(``OUT_BYTES``) 안에 드는 것 — (낼 줄, 남았으면 다음 ``--start`` 값 · 다 들면 None).
    첫 줄은 커도 낸다."""
    start, room, out = max(0, start), ep_session.OUT_BYTES, []
    for i, row in enumerate(rows[start:], start + 1):
        line = f"{i}. {row}"
        room -= len(line.encode("utf-8")) + 1
        if room < 0 and i > start + 1:
            return out, i - 1
        out.append(line)
    return out, None


def show_rows(rows: list[str], start: int = 0) -> None:
    """번호 붙인 줄을 ``start`` 째부터 답 크기 안에서 보이고(``rows_fit``), 남으면 남은 수와 다음 ``--start`` 를 댄다."""
    lines, rest = rows_fit(rows, start)
    for line in lines:
        print(line)
    if rest is not None:
        print(f"… 남은 {len(rows) - rest} 명 — 다음: 같은 명령에 --start {rest}")


def counts_by(people, field: str) -> dict[str, int]:
    """사람들의 그 칸 값별 수 — 빈 값은 「(빈 값)」 한 덩이."""
    counts: dict[str, int] = {}
    for p in people:
        key = getattr(p, field) or "(빈 값)"
        counts[key] = counts.get(key, 0) + 1
    return counts


def branch_counts(chart, code, company: str, picked) -> dict[str, int]:
    """고른 사람의 그 조직 바로 아래 부서별 수 — 그 조직에 바로 든 사람은 「(바로)」, 그 조직 밖은 「(그 밖)」."""
    branch = {}
    for top in [d for d in chart.depts.values() if d.parent == (code or company)]:
        for d in chart.subtree(top.code):
            branch[d.code] = top.name
    counts: dict[str, int] = {}
    for p in picked:
        key = branch.get(p.dept_code) or ("(바로)" if p.dept_code == code else "(그 밖)")
        counts[key] = counts.get(key, 0) + 1
    return counts


def ranked(counts: dict[str, int]) -> list[tuple[str, int]]:
    """값별 수를 많은 것부터(같으면 값 차례로) 줄 세운다."""
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def ranked_words(rows: list[tuple[str, int]], top: int | None = None) -> str:
    """줄 세운 값별 수를 한 줄로 — ``top`` 을 주면 그만큼만 보이고 나머지는 「그 밖 N 곳 M」 한 덩이로 접는다."""
    rest = rows[top:] if top else []
    return " · ".join(f"{k} {n}" for k, n in rows[:top]) + (f" · 그 밖 {len(rest)} 곳 {sum(n for _, n in rest)}" if rest else "")


@dataclasses.dataclass(frozen=True)
class Pick:
    """찾은 사람 하나 — 주소록의 한 사람(``person``) · 조직 하나(``org`` — 부서 주소 하나로 들어 보내는 순간의 구성원에게 간다) ·
    사외 주소(둘 다 아니다 — 임시보관함 길이 못 싣는다) 가운데 하나다. ``field`` 는 든 칸이다."""
    field: str
    person: object = None    # inbox.DirectoryPerson
    name: str = ""           # 조직 · 사외의 이름
    email: str = ""          # 조직 · 사외의 주소
    org: bool = False

    @property
    def mail(self) -> str:
        """보낼 메일 주소 — 사람이면 그 사람의 것, 아니면 받은 주소."""
        return (self.person.email if self.person is not None else self.email).strip()

    @property
    def label(self) -> str:
        """보일 이름 — 사람이면 그 사람의 것, 아니면 받은 이름."""
        return (self.person.name if self.person is not None else self.name).strip()

    @property
    def outside(self) -> bool:
        """사외 주소인가 — 사람도 조직도 아니다."""
        return self.person is None and not self.org

    def line(self) -> str:
        """사람에게 보일 한 줄 — 사람 · 조직 · 사외마다 제 꼴."""
        if self.person is not None:
            return person_line(self.person)
        if self.org:
            return f"{self.name}{DEPT_WORD} · {self.email}"
        return f"{self.email} (사외 — 임시보관함 길이 못 싣는다)"


class Ask(str):
    """따로 둘 줄 가운데 사람이 이름으로 댄 것이 한 사람으로 안 선 줄 — 동명이인 · 못 찾은 이름 · 퇴직 · 주소 없는 사람 · 못 찾았거나 여럿
    걸린 부서. 사람이 고르거나 빼서 다시 줄 수 있어, ``--out`` 의 찾기는 이 줄이 하나라도 서면 파일을 안 쓰고 2 로 멈춘다(``HELD_STOP``).
    무리의 구성원(배포그룹 · 지난 메일 · 파일 · 거르기)이 한 사람으로 안 선 줄과 알림 줄(못 가린 「나」 · 맨 위의 장 · 숨은참조를 모른다)은
    보통 글자다 — 다시 불러도 안 갈려 알리기만 한다."""


@dataclasses.dataclass
class Haul:
    """출처 값 하나가 데려온 것 — ``said`` 는 출처 줄의 사람 말, ``held`` 는 파일에 안 넣고 사람에게 물을 줄이다. ``branch`` 는 부서별
    수를 그 조직 바로 아래로 셀 때의 뿌리((부서 코드,) · 회사 전체면 (None,))다. ``seen`` 은 찾기만 하고 안 넘기는 다른 회사 사람
    (``findpeople.Row``), ``cut`` 은 사람찾기 답이 커서 앞만 읽었다는 말(안 잘렸으면 빈 글자)이다."""
    said: str
    picks: list
    held: list
    branch: tuple = ()
    seen: list = dataclasses.field(default_factory=list)
    cut: str = ""


class Run:
    """찾기 한 판의 메모리 — 메일함 · 조직도는 그 출처가 처음 부를 때 한 번만 열고, 「나」 와 최근 주고받은 메일은 한 번만 묻는다
    (조직도만 쓰는 판은 세션 없이 선다)."""

    def __init__(self, args, session_file):
        """한 판을 연다 — 인자 · 세션 파일 · 회사 값을 들고, 메일함 · 조직도 · 「나」 · 최근 메일은 아직 안 받는다."""
        self.args, self.session_file = args, session_file
        self.company = company_of(args.company)
        self._opened = self._chart = None
        self._book_when = ""        # 주소로 사람을 이을 때 쓴 받아 둔 조직도의 날짜 — 이 판에 조직도를 안 받았을 때
        self._me = self._recent = False
        self._finder = None

    @property
    def finder(self):
        """이 판의 사람찾기 앱 손 — 처음 부를 때 세션 파일로 세운다(들어가기는 첫 찾기가 한다)."""
        if self._finder is None:
            self._finder = findpeople.App(self.session_file)
        return self._finder

    @property
    def box(self):
        """이 판의 메일함 — 처음 부를 때 세션으로 연다(``open_mailbox``)."""
        if self._opened is None:
            self._opened = open_mailbox(self.args.url, self.session_file, inbox)
        return self._opened.box

    @property
    def mailbox_url(self) -> str:
        """이 판의 메일함 주소 — 메일함을 연 뒤에 선다(메일 손이 고른 주소). 열기 전이면 빈 글자."""
        return self._opened.url if self._opened is not None else ""

    def chart(self):
        """(OrgChart, 받은 시각 글자) — 받아 둔 판이 있으면 그것, 없거나 --fresh 면 새로 받아 둔다."""
        if self._chart is None:
            self._chart = load_org(self.company, self.args.fresh, lambda: self.box)   # 이 판의 메일함 하나로 받는다 — 또 열지 않는다
        return self._chart

    def leaned(self):
        """이 판이 기대는 조직도 — (OrgChart, 받은 시각 글자). 이 판에 받은 판이 있으면 그것, 없으면 받아 둔 판이고 새로 받지 않는다.
        둘 다 없으면 None."""
        return self._chart or cached_org(self.company)

    @property
    def when(self) -> str:
        """이 판이 기댄 조직도의 날짜 — 받은 판이 없고 받아 둔 판으로 주소를 잇지도 않았으면 빈 글자."""
        return self._chart[1] if self._chart else self._book_when

    def people_of(self, mails: list[str]) -> dict:
        """주소 → 주소록의 그 한 사람(``address_people``) — 이 판이 기대는 조직도(``leaned``)를 먼저 보고 거기 없는 주소만 묻는다."""
        got = self.leaned()
        book = chart_book(got[0]) if got else {}
        if not self._chart:
            self._book_when = got[1] if got else ""
        return address_people(self.box if any(a.casefold() not in book for a in mails) else None, mails, self.company, book)

    def me(self):
        """쓰는 사람(이 메일함의 주인) — 한 판에 한 번만 묻는다(``owner_person``)."""
        if self._me is False:
            self._me = owner_person(self)
        return self._me

    def recent(self) -> list | None:
        """최근 주고받은 메일의 줄 — 한 판에 한 번만 받는다(``recent_counts`` · 못 받았으면 None)."""
        if self._recent is False:
            self._recent = recent_counts(self)
        return self._recent


def split_field(value: str, default: str | None = "to") -> tuple[str | None, str]:
    """출처 값 앞의 칸 머리(``cc:`` · ``bcc:`` · ``to:``)를 뗀다 — (칸, 나머지). 머리가 없으면 ``default``."""
    head, sep, rest = value.partition(":")
    if sep and head.strip().lower() in FIELD_WORDS:
        return head.strip().lower(), rest.strip()
    return default, value.strip()


def bullets(rows: list[str], most: int = HELD_SHOWN, more: str = "") -> str:
    """따로 둔 줄 아래의 후보들 — ``most`` 개까지, 넘으면 남은 수와 ``more``(좁히는 법)를 댄다."""
    out = "".join(f"\n      · {r}" for r in rows[:most])
    return out + (f"\n      … 외 {len(rows) - most}{' — ' + more if more else ''}" if len(rows) > most else "")


def one_dept(chart, words: str):
    """부서 이름 · 코드 → (그 부서, 빈 글자) 또는 (None, 따로 둘 줄 — ``dept_miss``). 걸린 부서(``chart.find_depts``)가 꼭 하나일 때만
    고른다."""
    hits = chart.find_depts(words)
    return (hits[0], "") if len(hits) == 1 else (None, dept_miss(words, [dept_line(chart, d) for d in hits]))


def dept_line(chart, d) -> str:
    """부서 하나의 후보 줄 — 부서 길과 괄호 속 부서 코드(사람이 고르면 그 코드로 다시 준다)."""
    return f"{' > '.join(x.name for x in chart.path(d.code))} ({d.code})"


def dept_miss(words: str, rows: list[str]) -> str:
    """부서 하나로 안 선 까닭의 따로 둘 줄(``Ask``) — 걸린 부서의 후보 줄(``rows``)이 없으면 「못 찾은 부서」, 여럿이면 「여럿 걸린 부서」."""
    if not rows:
        return Ask(f"못 찾은 부서 「{words}」 — 조직도에 그 이름 · 코드가 든 부서가 없다. 이름을 줄여 다시 주거나 --tree 로 나무를 본다")
    return Ask(f"여럿 걸린 부서 「{words}」 {len(rows)} 곳 — 고르지 않는다. 사람이 고른 줄의 괄호 속 부서 코드로 다시 준다:"
               + bullets(rows, more="이름을 길게 주어 좁힌다"))


def home_dept(chart, p):
    """그 사람이 든 부서 — 조직도에서 그 사람이 바로 든 부서들 가운데 주소록의 부서 코드(괄호 앞) · 부서 이름이 맞는 것, 없으면 첫
    부서. 조직도에 그 사람이 없으면 주소록의 부서 코드가 맞는 부서다. 한 사람이 둘 넘는 부서에 들 수 있다(본부장이 「임원」과 제
    본부에 함께 든다)."""
    base = p.dept_code.split("(", 1)[0].strip().casefold()
    codes = [c for c, ms in chart.members.items() if c in chart.depts and any(same_person(m, p) for m in ms)]
    codes = codes or [c for c in chart.depts if base and c.split("(", 1)[0].casefold() == base]
    for c in codes:
        if base and c.split("(", 1)[0].casefold() == base:
            return chart.depts[c]
    for c in codes:
        if p.dept.strip() and inbox.squash(chart.depts[c].name) == inbox.squash(p.dept):
            return chart.depts[c]
    return chart.depts[codes[0]] if codes else None


def boss_above(chart, p, dept) -> tuple[object, str]:
    """그 사람의 윗사람 — (장, 빈 글자) 또는 (None, 까닭). 장들을 찾아(``bosses_above``) 꼭 하나면 그 사람, 아니면 그 까닭(``boss_miss``)."""
    where, bosses = bosses_above(chart, p, dept)
    return (bosses[0], "") if len(bosses) == 1 else (None, boss_miss(where, bosses))


def bosses_above(chart, p, dept) -> tuple[str, list]:
    """그 사람 위의 장들 — (그 장들이 든 부서 이름, 장들). 그 부서의 장이고, 장이 없거나 본인이 그 부서의 장(장이 여럿인 부서의 한
    사람이어도)이면 위 부서로 올라간다 — 같은 부서의 다른 장은 윗사람이 아니다. 맨 위까지 없으면 (빈 글자, [])."""
    code = dept.code
    while code in chart.depts:
        here = [m for m in chart.members.get(code, []) if m.is_boss and not m.retired]
        if any(same_person(m, p) for m in here):
            code = chart.depts[code].parent
            continue
        bosses = list({m.notes or m.email: m for m in here}.values())
        if bosses:
            return chart.depts[code].name, bosses
        code = chart.depts[code].parent
    return "", []


def boss_miss(where: str, bosses: list) -> str:
    """윗사람이 한 사람으로 안 선 까닭 — 장이 여럿이면 그 부서와 장들, 없으면 맨 위 부서의 장이라는 말."""
    if bosses:
        return f"{where} 에 장이 {len(bosses)} 명이라 고르지 않는다:" + bullets([person_line(b) for b in bosses])
    return "조직도에서 그 위의 장을 못 찾았다 — 맨 위 부서의 장이다"


# ── 출처 ─────────────────────────────────────────────────────────────────

def split_pick(handle: str) -> tuple[str, str]:
    """「이름[부서]」 → (이름, 부서 말) — 동명이인 가운데 그 부서의 사람을 고른 꼴이다. 꼴이 아니면 (그대로, 빈 글자)."""
    found = PICK_FORM.match(handle)
    return (found.group(1).strip(), found.group(2).strip()) if found else (handle, "")


def dept_path(got, p) -> str:
    """그 사람의 부서 길(「맨 위 > … > 그 부서」) — 조직도 한 판(``got`` — (OrgChart, 받은 시각) 또는 None)에서 짓는다. 판이 없거나 그
    사람이 조직도에 없으면 주소록의 부서 이름이다."""
    d = home_dept(got[0], p) if got else None
    return " > ".join(x.name for x in got[0].path(d.code)) if d is not None else p.dept


def dept_paths(run, people) -> dict:
    """사람마다 부서 길(``dept_path``) — 이 판이 기대는 조직도(``leaned`` — 새로 받지 않는다)를 한 번 골라 짓는다. 열쇠는 ``id(사람)``."""
    got = run.leaned()
    return {id(p): dept_path(got, p) for p in people}


def recent_counts(run) -> list | None:
    """최근 주고받은 메일의 (받은 · 보낸, 상대 주소, 날짜) 줄 — 받은편지함 · 보낸편지함의 새것 ``RECENT_MAIL_SCAN`` 통을 한 번씩 받는다.
    못 받으면 None(끊긴 세션은 그대로 올린다)."""
    try:
        got = run.box.list(count=RECENT_MAIL_SCAN)
        sent = run.box.list_sent(count=RECENT_MAIL_SCAN)
    except inbox.SessionExpired:
        raise
    except inbox.MailboxError:
        return None
    return [("받은", e.sender.addr, e.date) for e in got] + [("보낸", r.addr, s.date) for s in sent for r in s.recipients]


def recent_tally(lines: list | None, people) -> dict | None:
    """주소 → 그 사람과 최근 주고받은 셈({"받은": 수, "보낸": 수, "last": 마지막 날짜}) — 사람마다 하나, 주고받은 것이 없으면 None 값.
    줄을 못 받았으면(``lines`` 가 None) None."""
    if lines is None:
        return None
    want = {p.email.casefold() for p in people if p.email}
    marks: dict = dict.fromkeys(want)
    for kind, addr, when in lines:
        a = (addr or "").casefold()
        if a in want:
            m = marks[a] = marks[a] or {"받은": 0, "보낸": 0, "last": ""}
            m[kind] += 1
            m["last"] = max(m["last"], when or "")
    return marks


def recent_words(marks: dict | None) -> dict:
    """주소 → 최근 메일을 주고받은 말(「최근 메일 받은 2 · 보낸 1 · 마지막 11-03」 · 없으면 「최근 메일 없음(…)」). 동명이인을 사람이 가를
    실마리다. 셈을 못 했으면 빈 표다(후보 줄은 그 말 없이 선다)."""
    return {a: (f"최근 메일 받은 {m['받은']} · 보낸 {m['보낸']} · 마지막 {m['last'][5:10]}" if m
                else f"최근 메일 없음(받은 · 보낸 새것 {RECENT_MAIL_SCAN}통에서)") for a, m in (marks or {}).items()}


def pick_tokens(name: str, live) -> list[str]:
    """동명이인 후보마다 고르면 다음 부름에 그대로 줄 꼴 — 그 후보의 부서가 후보 가운데 하나뿐이면 「이름[부서]」, 아니면 주소."""
    leaves = [inbox.squash(p.dept) for p in live]
    return [f"{name}[{p.dept}]" if p.dept.strip() and leaves.count(leaf) == 1 else p.email for p, leaf in zip(live, leaves)]


def homonym_lines(name: str, live, paths: dict, recent: dict) -> list[str]:
    """동명이인 후보 줄 — 직급 · 직책 · 주소 · 부서 길(``paths``) · 최근 주고받은 메일(``recent``)과 고르면 줄 꼴(``pick_tokens``).
    「이름[부서]」 는 한 글자 틀려도 다른 사람이 아니라 아무도 안 선다."""
    return [" · ".join(x for x in (person_line(p, dept=False), paths[id(p)], recent.get(p.email.casefold(), "")) if x)
            + f"  → 고르면 --name \"{pick}\"" for p, pick in zip(live, pick_tokens(name, live))]


def ask_book(run, asks) -> list:
    """(칸, 말) 여럿을 주소록에 함께 묻는다 — 줄마다 (이름, 부서 말, 질의, 주소록의 답). 「이름[부서]」 는 이름으로 묻는다(``split_pick``).
    질의가 하나도 안 서면 메일함을 안 연다."""
    picks = [split_pick(h) for _, h in asks]
    queries = [inbox.directory_query(base) for base, _ in picks]
    box = run.box if any(queries) else None
    with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
        answers = list(pool.map(lambda q: box.find_people(q[0], run.company) if q else [], queries))
    return [(base, where, q, every) for (base, where), q, every in zip(picks, queries, answers)]


def matches(q, every) -> tuple[list, list]:
    """주소록의 답 가운데 질의의 꼴이 꼭 같은 사람 — (같은 사람 모두, 그 가운데 퇴직 안 한 사람)."""
    same = [p for p in every if q and q[1](p)]
    return same, [p for p in same if not p.retired]


def line_state(where: str, every, same, live, paths: dict) -> tuple[str, list]:
    """이름 한 줄의 상태와 그 사람들 — ``STOOD``(그 한 사람) · ``DEPT_MISS``(부서 말에 맞는 사람이 없다 — 이름의 사람들) · ``HOMONYM``
    (후보들) · ``RETIRED``(퇴직한 사람들) · ``NOT_FOUND``(그 글자가 든 살아 있는 사람들). 「이름[부서]」 면 부서 말이 주소록의 부서
    이름 · 부서 길(``paths``)에 든 사람으로 좁힌다."""
    if where and live:
        narrowed = [p for p in live if inbox.squash(where) in inbox.squash(f"{p.dept} {paths[id(p)]}")]
        if not narrowed:
            return DEPT_MISS, live
        live = narrowed
    if len(live) == 1:
        return STOOD, live
    if len(live) > 1:
        return HOMONYM, live
    if same:
        return RETIRED, same
    return NOT_FOUND, [p for p in every if not p.retired]


def held_words(state: str, handle: str, base: str, where: str, people, rows: list[str]) -> str:
    """이름 한 줄의 상태 → 따로 둘 줄(``Ask``) — 섰으면 빈 글자. ``rows`` 는 동명이인 후보 줄(``homonym_lines``)이다."""
    if state == STOOD:
        return ""
    if state == DEPT_MISS:
        return Ask(f"「{handle}」 — {base} 가운데 부서 길에 「{where}」 가 든 사람이 없다. 고르지 않는다:" + bullets(rows))
    if state == HOMONYM:
        return Ask(f"동명이인 「{handle}」 {len(people)} 명 — 고르지 않는다. 누구인지 묻고, 사람이 고른 줄의 「고르면」 꼴을 다음 부름에 "
                   "그대로 준다(주소를 옮겨 적지 않는다):" + bullets(rows, more="부서 · 직급을 대며 묻는다"))
    if state == RETIRED:
        return Ask(f"「{handle}」 — 퇴직한 사람이다:" + bullets([person_line(p) for p in people]))
    near = [person_line(p) for p in people]
    return Ask(f"못 찾은 이름 「{handle}」 — 주소록에 그 이름 · 주소 · 사번이 꼭 같은 사람이 없다"
               + (" · 그 글자가 든 사람:" + bullets(near, more="더 길게 주어 좁힌다") if near else ""))


def resolve(run, asks) -> list:
    """(칸, 이름 · 주소 · 사번 · Notes 이름 · ID · 「이름[부서]」) 여럿 → 줄마다 (칸, 그 말, 그 한 사람 또는 None, 따로 둘 줄) — 주소록에
    함께 묻고(``ask_book``) 줄마다 상태를 셈해(``line_state``) 안 선 줄의 말을 짓는다(``held_words``). 동명이인 후보 줄에 달 부서 길 ·
    최근 메일은 후보 줄이 설 때만 묻는다(최근 메일은 한 판에 한 번 — ``Run.recent``). 고르는 것은 사람이다."""
    out = []
    for (field, handle), (base, where, q, every) in zip(asks, ask_book(run, asks)):
        same, live = matches(q, every)
        paths = dept_paths(run, live) if where and live else {}
        state, people = line_state(where, every, same, live, paths)
        rows = []
        if state in (DEPT_MISS, HOMONYM):
            rows = homonym_lines(base, people, paths or dept_paths(run, people), recent_words(recent_tally(run.recent(), people)))
        out.append((field, handle, people[0] if state == STOOD else None, held_words(state, handle, base, where, people, rows)))
    return out


def name_picks(run, asks) -> tuple[list, list]:
    """``resolve`` 의 줄 → (받는 사람이 될 사람, 따로 둘 줄). 받는 사람으로 못 서는 사람(``can_receive``)은 따로 둔다."""
    picks, held = [], []
    for field, handle, p, why in resolve(run, asks):
        if p is not None and can_receive(p):
            picks.append(Pick(field, person=p))
        elif p is not None:
            held.append(Ask(NO_ADDRESS.format(handle=handle, line=person_line(p))))
        else:
            held.append(why)
    return picks, held


def from_names(run, values) -> list:
    """이름 · 주소 · 사번 · Notes 이름 · ID 여럿 — 주소록에 하나씩(함께) 묻는다(``resolve``)."""
    asks = [split_field(h) for v in values for h in NAME_SPLIT.split(v) if h.strip()]
    picks, held = name_picks(run, asks)
    return [Haul(f"이름 {len(asks)} 개(선 사람 {len(picks)})", picks, held)]


def from_depts(run, values) -> list:
    """부서의 사람 — 그 부서에 바로 든 사람, ``--sub`` 면 하위 조직까지. 받아 둔 조직도로 선다."""
    chart, _ = run.chart()
    out = []
    for v in values:
        field, words = split_field(v)
        d, why = one_dept(chart, words)
        if d is None:
            out.append(Haul(f"부서 「{words}」(못 섰다)", [], [why]))
            continue
        out.append(dept_haul(run, chart, d, field, "부서"))
    return out


def dept_haul(run, chart, d, field: str, word: str) -> Haul:
    """부서 하나의 사람 — ``--sub`` 면 하위 조직까지."""
    people = chart.people(d.code, deep=run.args.sub)
    scope = "하위 조직까지" if run.args.sub else "그 부서만"
    return Haul(f"{word} {' > '.join(x.name for x in chart.path(d.code))}({scope}) {len(people)} 명",
                [Pick(field, person=p) for p in people], [], (d.code,) if run.args.sub else ())


def from_orgs(run, values) -> list:
    """부서를 조직 하나로 — 그 부서의 주소 하나가 든다(웹메일 고름 창에서 조직을 체크한 것). 부서원으로 풀지 않는다."""
    chart, _ = run.chart()
    out = []
    for v in values:
        field, words = split_field(v)
        d, why = one_dept(chart, words)
        if d is not None and not d.email:
            d, why = None, Ask(f"부서 {d.name} 에 부서 주소가 없어 조직 하나로 못 넣는다 — 부서원으로 넣으려면 --dept")
        if d is None:
            out.append(Haul(f"조직 「{words}」(못 섰다)", [], [why]))
            continue
        out.append(Haul(f"조직 {' > '.join(x.name for x in chart.path(d.code))}(조직 하나로)",
                        [Pick(field, name=d.name, email=d.email, org=True)], []))
    return out


def from_all(run, on) -> list:
    """회사 전체의 사람 — 받아 둔 조직도로 선다."""
    chart, _ = run.chart()
    people = chart.people()
    return [Haul(f"회사 전체({run.company}) {len(people)} 명", [Pick("to", person=p) for p in people], [], (None,))]


def from_groups(run, values) -> list:
    """배포그룹의 구성원 — 그룹을 고르고(``pick_groups``) 구성원을 받아(``group_rosters``) 주소로 주소록의 한 사람에 이은 뒤(``people_of``)
    그룹마다 출처 한 줄로 낸다(``roster_haul``). 이어야 거르기가 직책 · 등급까지 걸리고 draft 가 그 주소를 받는다. 그룹 자체를 한 받는
    사람으로 넣지 않는다. 못 선 그룹의 줄이 먼저다."""
    missing, picked = pick_groups(run, [(field, *split_kind(rest)) for field, rest in (split_field(v) for v in values)])
    found = group_rosters(run.box, picked)
    people = run.people_of(roster_addresses(found))
    return missing + [roster_haul(people, *f) for f in found]


def pick_groups(run, wants) -> tuple[list, list]:
    """찾을 그룹들(``wants`` — (칸, 갈래들, 이름))을 갈래마다의 목록(``group_lists``)에서 하나씩 고른다 — (못 선 그룹의 출처 줄들,
    선 그룹의 (칸, 갈래, 열쇠, 이름)들)."""
    lists = group_lists(run.box, run.company, wants)
    out, found = [], []
    for field, ks, name in wants:
        hit = one_group(lists, ks, name, missing_next=" — 갈래마다의 목록은 --groups")
        if isinstance(hit, str):
            out.append(Haul(f"배포그룹 「{name}」(못 섰다)", [], [hit]))
            continue
        kind, key, title = hit
        found.append((field, kind, key, title))
    return out, found


def group_rosters(box, picked) -> list:
    """고른 그룹마다 구성원 — (칸, 갈래, 이름, 구성원 줄들). 구성원 줄은 (이름, 직급, 부서, 주소)다."""
    return [(field, kind, title, box.group_members(key)) for field, kind, key, title in picked]


def roster_addresses(found) -> list[str]:
    """구성원 줄들의 주소 — 주소가 없는 줄은 뺀다."""
    return [m[3].strip() for *_, members in found for m in members if m[3].strip()]


def roster_haul(people: dict, field: str, kind: str, title: str, members) -> Haul:
    """그룹 하나의 구성원 → 출처 한 줄. 주소록의 한 사람으로 선 구성원은 그 칸에 들고, 안 선 구성원은 따로 둔다(``lost_members_line``)."""
    picks, lost = [], []
    for name, grade, dept, email in members:
        p = people.get(email.strip()) if email.strip() else None
        if p is None:
            lost.append(" · ".join(x for x in (name, dept, grade, email) if x))
        else:
            picks.append(Pick(field, person=p))
    return Haul(f"배포그룹 {GROUP_KIND_WORDS[kind]} 「{title}」 {len(members)} 명", picks, [lost_members_line(title, lost)] if lost else [])


def lost_members_line(title: str, lost: list[str]) -> str:
    """그룹 구성원 가운데 주소록에서 한 사람으로 안 선 사람들의 따로 둘 줄."""
    return (f"배포그룹 「{title}」 구성원 가운데 주소록에서 한 사람으로 안 선 {len(lost)} 명(주소 없음 · 퇴직 · 주소록에 없음) — "
            "웹메일에서 본다:" + bullets(lost))


def owner_person(run):
    """쓰는 사람(이 메일함의 주인) — 메일함 파일 번호가 사번이라(``MAILFILE_NUMBER``) 주소록에 그 사번으로 묻는다. 꼭 한 사람이 아니면 None."""
    box = run.box                                   # 메일함을 열어야 그 주소(run.mailbox_url)가 선다
    number = MAILFILE_NUMBER.search(run.mailbox_url)
    if not number:
        return None
    hits = [p for p in box.find_exact(number.group(1), run.company) if p.empno.strip() == number.group(1) and not p.retired]
    return hits[0] if len(hits) == 1 else None


NO_ME = "쓰는 사람을 주소록에서 못 가렸다 — 메일함 파일 번호(사번)로 찾은 사람이 꼭 하나가 아니다. 이름 · 주소를 --name 으로 준다"


def from_me(run, on) -> list:
    """쓰는 사람 자신."""
    me = run.me()
    if me is None:
        return [Haul("나(못 섰다)", [], [NO_ME])]
    return [Haul(f"나 — {me.name}", [Pick("to", person=me)], [])]


def from_my_dept(run, on) -> list:
    """쓰는 사람의 부서 — 그 부서에 바로 든 사람, ``--sub`` 면 하위 조직까지. 쓰는 사람도 든다(빼려면 --except)."""
    me = run.me()
    if me is None:
        return [Haul("내 부서(못 섰다)", [], [NO_ME])]
    chart, _ = run.chart()
    d = home_dept(chart, me)
    if d is None:
        return [Haul("내 부서(못 섰다)", [], [f"조직도에서 {me.name} 의 부서를 못 찾았다 — 조직도가 낡았으면 --fresh, 아니면 --dept <부서> 로 준다"])]
    return [dept_haul(run, chart, d, "to", "내 부서")]


def from_bosses(run, values) -> list:
    """그 사람의 윗사람 — 그 사람을 주소록에서 찾고(``resolve``), 조직도에서 그 사람 부서의 장을 낸다. 본인이 장이거나 장이 없는
    부서면 위 부서의 장이다(``boss_above``)."""
    asks = [split_field(v) for v in values]
    chart = run.chart()[0] if asks else None
    out = []
    for field, handle, p, why in resolve(run, asks):
        if p is None:
            out.append(Haul(f"「{handle}」 의 윗사람(못 섰다)", [], [why]))
            continue
        d = home_dept(chart, p)
        boss, why = boss_above(chart, p, d) if d is not None else (None, "조직도에서 그 사람의 부서를 못 찾았다 — 조직도가 낡았으면 --fresh")
        if boss is None:
            out.append(Haul(f"{p.name} 의 윗사람(못 섰다)", [], [f"{person_line(p)} — {why}"]))
            continue
        out.append(Haul(f"{p.name} 의 윗사람 — {boss.name}({boss.dept or chart.dept_name(boss.dept_code)})", [Pick(field, person=boss)], []))
    return out


def file_handles(name: str, forced: str | None) -> list[tuple[str | None, str]]:
    """사람을 든 파일 하나 → (칸, 이름 · 주소 · 사번 · Notes 이름) 여럿 — 글을 읽고(``file_text``) 꼴에 맞춰 줄을 뽑는다(JSON 이면
    ``json_handles``, 아니면 ``text_handles``). 값 앞의 칸 머리(``forced``)가 있으면 모두 그 칸, 칸을 모르는 줄은 받는 사람이다."""
    text = file_text(name)
    found = json_handles(name, text) if looks_json(text) else text_handles(text)
    return [(forced or field or "to", handle) for field, handle in found]


def file_text(name: str) -> str:
    """``--from-file`` 의 파일 하나의 글 — 못 읽으면 Stop(로그인 스킬의 글 파일 읽기가 정한 종료 값과 말 그대로)."""
    try:
        return ep_command.text_file(name, "--from-file 의 파일")
    except ep_command.Stop as exc:
        raise from_ep(exc) from exc


def looks_json(text: str) -> bool:
    """파일의 글이 JSON 인가 — 빈칸 뒤 첫 글자가 ``{`` · ``[`` 이면."""
    return text.lstrip()[:1] in ("{", "[")


def json_handles(name: str, text: str) -> list[tuple[str | None, str]]:
    """JSON 파일의 (칸 또는 None, 말) 줄 — 꼴을 골라(``json_rows``) 줄마다 사람 하나를 뽑는다(``json_handle``). 못 읽거나 사람이 없으면
    Stop."""
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise Stop(EXIT_ARGS, f"--from-file 의 JSON 을 못 읽었다: {name} ({exc})") from exc
    found = [h for h in map(json_handle, json_rows(data)) if h is not None]
    if not found:
        raise Stop(EXIT_ARGS, f"--from-file 의 JSON 에 사람이 없다: {name} — 사람 파일(people) · 손의 답(attendees 줄) · 이름 목록을 준다")
    return found


def json_handle(x) -> tuple[str | None, str] | None:
    """JSON 의 줄 하나 → (칸 또는 None, 말) — 이름 글자이거나 ``email`` 에 주소가 든 객체(``field`` 가 받는 칸이면 그 칸). 아니면 None."""
    if isinstance(x, str) and x.strip():
        return None, x.strip()
    if isinstance(x, dict) and isinstance(x.get("email"), str) and "@" in x["email"]:
        return (x.get("field") if x.get("field") in FIELD_WORDS else None), x["email"].strip()
    return None


def json_rows(data) -> list:
    """JSON 의 사람 줄들 — 세 꼴만 읽는다. 사람 파일이면 ``people`` 목록, 맨 위가 사람을 든 목록(이름 글자 · ``email`` 객체)이면 그 목록,
    아니면 손의 답에서 가장 얕은 자리의 ``attendees`` 목록(``attendee_rows``)."""
    if isinstance(data, dict) and isinstance(data.get("people"), list):
        return data["people"]
    if isinstance(data, list) and any(json_handle(x) for x in data):
        return data
    return attendee_rows(data)


def attendee_rows(data) -> list:
    """손의 답에서 가장 얕은 자리의 ``attendees`` 목록들의 줄 — 회의실 미리 보기의 새 참석자 · 일정 한 건의 참석자. 한 깊이에서 찾으면 더
    안 내려간다(더 깊은 ``was`` · ``body`` 의 옛 참석자 · ``leaving`` · ``references`` 는 안 든다)."""
    rows, level = [], [data]
    while level and not rows:
        rows = [x for node in level if isinstance(node, dict) and isinstance(node.get("attendees"), list) for x in node["attendees"]]
        level = [v for node in level for v in (node.values() if isinstance(node, dict) else node if isinstance(node, list) else ())]
    return rows


def text_handles(text: str) -> list[tuple[None, str]]:
    """글 파일의 (None, 말) 줄 — 한 줄에 하나, ``#`` 뒤는 버리고 빈 줄은 뺀다."""
    found = [(None, line.split(FILE_COMMENT, 1)[0].strip()) for line in text.splitlines()]
    return [x for x in found if x[1]]


def from_files(run, values) -> list:
    """다른 손이 낸 사람(일정의 참석자 · 메일의 받는 사람 · 회의실 예약의 참석자 · 앞서 쓴 사람 파일)에서 — 주소는 받아 둔 조직도 ·
    주소록으로 잇고(``people_of``), 이름 · 사번 · Notes 이름은 주소록에 묻는다(``resolve``). 한 사람으로 안 선 것은 따로 둔다."""
    return [file_haul(run, name, file_handles(name, forced)) for forced, name in (split_field(v, None) for v in values)]


def file_haul(run, name: str, asks) -> Haul:
    """파일 하나의 (칸, 말) 줄 → 출처 한 줄 — 주소는 ``people_of`` 로 잇고(``address_picks``) 이름 · 사번 · Notes 이름은 주소록에
    묻는다(``name_picks``). 이름으로 선 사람이 먼저고, 안 선 주소는 따로 둔다(``lost_addresses_line``)."""
    mails = [(f, h) for f, h in asks if "@" in h]
    people = run.people_of([h for _, h in mails]) if mails else {}
    picks, held = name_picks(run, [(f, h) for f, h in asks if "@" not in h])
    more, lost = address_picks(mails, people)
    picks += more
    held += [lost_addresses_line(name, lost)] if lost else []
    return Haul(f"파일 {pathlib.Path(name).name} {len(asks)} 개(선 사람 {len(picks)})", picks, held)


def address_picks(mails, people: dict) -> tuple[list, list[str]]:
    """(칸, 주소) 줄들을 이은 사람(``people`` — 주소 → 그 한 사람 또는 None)에 대 본다 — (선 사람의 Pick 들, 안 선 주소들)."""
    picks, lost = [], []
    for field, handle in mails:
        p = people.get(handle)
        if p is None:
            lost.append(handle)
        else:
            picks.append(Pick(field, person=p))
    return picks, lost


def lost_addresses_line(name: str, lost: list[str]) -> str:
    """파일의 주소 가운데 주소록에서 한 사람으로 안 선 주소들의 따로 둘 줄."""
    return (f"파일 {pathlib.Path(name).name} 의 주소 가운데 주소록에서 한 사람으로 안 선 {len(lost)} — 사외 주소 · 부서 주소 · 틀린 주소다:"
            + bullets(lost))


def from_last(run, values) -> list:
    """지난 메일의 받는 사람 — 메일마다 출처 한 줄. 값 앞에 칸 머리를 주면 모두 그 칸으로. 사람은 주소록의 한 사람에, 사외 주소는 사외로 든다.

    보낸 메일은 받는 사람 · 참조 · 숨은참조를 칸 그대로, 고름 창에서 체크한 조직은 조직 하나로 든다 — 「지난번과 같이」 다. 받은 메일은
    메일 손의 ``read`` 가 보이는 「함께 받은 사람」 명단이다 — 받는 사람과 참조를 합친 명단이라 모두 받는 사람 칸에 들고, 쓰는 사람
    자신은 뺀다(제게 보내는 사본 · 제가 여는 회의의 참석자가 되지 않게). 보낸 분은 받는 사람이 아니라 안 든다."""
    got = [last_mail(run, *split_field(v, None)) for v in values]
    sent, received = [x for x in got if x.sent], [x for x in got if not x.sent]
    people = run.people_of(sent_addresses([r for x in sent for r in x.rows]))
    heard = handle_people(run, [r for x in received for r in x.rows])
    me = run.me() if received else None
    return [sent_haul(x, people) if x.sent else received_haul(x, heard, me) for x in got]


class Last(NamedTuple):
    """지난 메일 한 통 — 칸 머리(``forced`` — 없으면 None) · 목록 줄 · 받는 사람 줄 · 보낸 메일인가(받은 메일이면 거짓)."""
    forced: str | None
    entry: object
    rows: tuple
    sent: bool


def last_mail(run, forced: str | None, unid: str) -> Last:
    """번호의 지난 메일과 그 받는 사람 줄. 보낸편지함을 끝까지 먼저 훑고 없으면 받은편지함 · 폴더 · 임시보관함 차례로 찾는다(메일 손의 한
    찾기 — 보기마다 한 번씩. 못 찾으면 훑은 자리를 대고 멈춘다). 임시메일이면 Stop. 보낸 메일인가는 여기서 한 번 가르고, 줄은 보낸 메일이면 칸 그대로(``sent_rows``), 받은
    메일이면 함께 받은 사람(``received_rows``)이다."""
    e = find_mail(run.box, inbox, unid, None, DEFAULT_SCAN, first=SENT)
    if e.folder == DRAFTS:
        raise Stop(EXIT_ARGS, LAST_DRAFT.format(unid=e.unid.upper(), drafts=DRAFTS))
    sent = e.folder == SENT
    return Last(forced, e, sent_rows(run.box, e) if sent else received_rows(run.box, e), sent)


def sent_rows(box, e) -> tuple:
    """보낸 메일 한 통의 받는 사람 칸(``Mailbox.sent_people``) — 못 읽었거나 비었으면 Stop. 빈 명단으로 이으면 「지난번과 같이」가 아무도
    없이 선다."""
    try:
        rows = box.sent_people(e.unid)
    except inbox.SessionExpired:
        raise                                       # 끊긴 세션은 명령 전체가 다시 세운다 — 「못 읽었다」로 낮추지 않는다
    except inbox.MailboxError as exc:
        raise Stop(EXIT_TOOL, f"그 메일의 받는 사람을 다 읽지 못했다({exc}) — 웹메일에서 그 메일을 열어 받는 사람을 본다") from exc
    if not rows:
        raise Stop(EXIT_TOOL, f"그 메일({e.subject})의 받는 사람 칸이 비었다 — 웹메일에서 그 메일을 열어 받는 사람을 본다")
    return rows


def received_rows(box, e) -> tuple:
    """받은 메일 한 통의 함께 받은 사람(``received_together``) — 못 찾았거나 비었으면 까닭을 대고 Stop. 빈 명단을 「아무도 없다」로 잇지
    않는다."""
    try:
        got = received_together(box, e.unid)
    except inbox.SessionExpired:
        raise
    except inbox.MailboxError as exc:
        raise Stop(EXIT_TOOL, f"그 메일의 받는 사람을 못 읽었다({exc}) — 웹메일에서 그 메일을 열어 받는 사람을 본다") from exc
    if got.state:
        raise Stop(EXIT_TOOL, f"받은 메일 「{e.subject}」 의 받는 사람을 못 읽었다 — {together_why(got)}. "
                              "웹메일에서 그 메일을 열어 받는 사람을 보고 --name 으로 준다")
    return got.rows


def sent_addresses(rows) -> list[str]:
    """보낸 메일의 받는 사람 줄 가운데 주소록의 사람으로 이을 주소 — 조직(부서 주소) · 사외 주소 줄은 빼고, 주소가 없는 줄도 뺀다."""
    return [r.addr.strip() for r in rows if r.addr.strip() and sent_row_kind(r) == PERSON]


def sent_row_kind(r) -> str:
    """보낸 메일의 받는 사람 줄 하나의 꼴 — 조직(부서 주소 · ``ORG``) · 사외 주소(``OUTSIDE``) · 주소록에서 이을 사람(``PERSON``)."""
    return {inbox.DEPT_TYPE: ORG, inbox.EMAIL_TYPE: OUTSIDE}.get(r.kind, PERSON)


def sent_haul(last: Last, people: dict) -> Haul:
    """보낸 메일 한 통의 받는 사람 → 출처 한 줄. 칸 그대로(칸 머리를 줬으면 모두 그 칸), 조직은 조직 하나 · 사외 주소는 사외로, 주소록에서
    한 사람으로 안 선 줄은 따로 둔다. 숨은참조 칸이 비면 있었는지 모른다고 댄다."""
    forced, e, rows = last.forced, last.entry, last.rows
    picks, lost = [], []
    for r in rows:
        field, addr, kind = forced or field_of(r), r.addr.strip(), sent_row_kind(r)
        if addr and kind != PERSON:
            picks.append(Pick(field, name=r.name, email=addr, org=kind == ORG))
        elif addr and people.get(addr) is not None:
            picks.append(Pick(field, person=people[addr]))
        else:
            lost.append(person_word(r))
    held = [lost_sent_line(e.subject, lost)] if lost else []
    if not any(field_of(r) == "bcc" for r in rows):
        held.append(BCC_UNKNOWN)
    return Haul(f"지난 메일 「{e.subject}」({e.date[:10]}) 받는 사람 {len(rows)}", picks, held)


def lost_sent_line(subject: str, lost: list[str]) -> str:
    """보낸 메일의 받는 사람 가운데 주소록에서 한 사람으로 안 선 줄들의 따로 둘 줄."""
    return f"지난 메일 「{subject}」 의 받는 사람 가운데 주소록에서 한 사람으로 안 선 {len(lost)} — 웹메일에서 더한다:" + bullets(lost)


def handle_people(run, rows) -> dict:
    """받은 메일의 받는 사람 줄 → 주소록의 그 한 사람(``id(줄)`` 열쇠 · 못 서면 None). 줄은 주소 · Notes 이름 · ``<ID>(<약칭>)`` 이 섞인다 —
    주소는 draft 와 같은 자(``people_of``)로, Notes 이름은 이 판이 기대는 조직도(``leaned`` · ``notes_index``)에서 먼저 잇고
    (``known_people``), 나머지는 주소록에 그 꼴로 묻는다(``ask_exact``)."""
    if not rows:
        return {}
    out, ask = known_people(rows, run.people_of(row_addresses(rows)), notes_index(run.leaned()))
    return {**out, **dict(zip(map(id, ask), ask_exact(run, ask)))}


def row_addresses(rows) -> list[str]:
    """받는 사람 줄들의 주소 — 주소가 없는 줄은 뺀다."""
    return [r.addr.strip() for r in rows if r.addr.strip()]


def notes_index(got) -> dict:
    """조직도 한 판(``got`` — (OrgChart, 받은 시각) 또는 None)의 Notes 이름 열쇠 → 사람 — 퇴직하지 않고 받는 사람으로 서는(``can_receive``)
    사람만."""
    return {keys_of(p.notes, "").notes: p for p in (got[0].people() if got else ()) if can_receive(p) and not p.retired}


def known_people(rows, by_addr: dict, known: dict) -> tuple[dict, list]:
    """받는 사람 줄들 가운데 묻지 않고 서는 것 — ({id(줄): 사람 또는 None}, 주소록에 물을 줄들). 주소가 있는 줄은 주소로 이은 사람
    (``by_addr``), Notes 이름이 조직도의 열쇠(``known``)에 있는 줄은 그 사람이다."""
    out, ask = {}, []
    for r in rows:
        if r.addr.strip():
            out[id(r)] = by_addr.get(r.addr.strip())
        elif (key := keys_of(row_notes(r), "").notes) and key in known:
            out[id(r)] = known[key]
        else:
            ask.append(r)
    return out, ask


def ask_exact(run, rows) -> list:
    """받는 사람 줄마다 그 Notes 이름 · 이름 꼴로 주소록에 함께 묻는다(``find_exact``) — 줄마다 그 한 사람(``one_receiver``) 또는 None.
    물을 줄이 없으면 메일함을 안 연다."""
    box = run.box if rows else None
    with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
        return [one_receiver(every) for every in pool.map(lambda r: box.find_exact(r.notes or r.name, run.company), rows)]


def one_receiver(every) -> object:
    """주소록의 답 가운데 받는 사람이 될 꼭 한 사람 — 퇴직자를 빼고 하나이고 받는 사람으로 서면(``can_receive``) 그 사람, 아니면 None."""
    live = [p for p in every if not p.retired]
    return live[0] if len(live) == 1 and can_receive(live[0]) else None


def row_is_me(r, p, me) -> bool:
    """받은 메일의 받는 사람 줄 하나가 쓰는 사람인가 — 그 줄에 이은 사람(``p``)이나 줄 자체의 주소 · Notes 이름이 쓰는 사람과 열쇠
    하나라도 같으면(``keys_of`` · ``shares_key``) 참이다. 쓰는 사람을 못 가렸으면(``me`` 가 None) 거짓.
    하나라도 같으면 빼는 까닭 — 이 명단은 제가 받은 메일이라 늘 저를 들고, 남기면 새 메일 · 회의의 받는 사람에 제가 든다."""
    if me is None:
        return False
    mine = keys_of(me.notes, me.email)
    return (p is not None and shares_key(keys_of("", p.email), mine)) or shares_key(keys_of(row_notes(r), r.addr or ""), mine)


def row_notes(r) -> str:
    """받은 메일의 받는 사람 줄의 Notes 이름 — 그 칸이 Notes 이름 꼴(``inbox.is_notes_name``)일 때만, 아니면 빈 글자(``<ID>(<약칭>)`` ·
    이름 글자는 Notes 이름이 아니다)."""
    return r.notes if r.notes and inbox.is_notes_name(r.notes) else ""


def received_haul(last: Last, heard: dict, me) -> Haul:
    """받은 메일 한 통의 받는 사람 → 출처 한 줄. 쓰는 사람은 빼고, 주소록에서 한 사람으로 안 선 줄은 따로 둔다."""
    forced, e, rows = last.forced, last.entry, last.rows
    picks, lost, mine = [], [], 0
    for r in rows:
        p = heard.get(id(r))
        if row_is_me(r, p, me):
            mine += 1
        elif p is not None:
            picks.append(Pick(forced or "to", person=p))
        else:
            lost.append(person_word(r))
    held = [lost_received_line(e.subject, lost)] if lost else []
    me_word = "쓰는 사람은 뺐다" if mine else ("쓰는 사람이 명단에 없다" if me is not None else "쓰는 사람을 못 가려 명단 그대로다")
    return Haul(f"받은 메일 「{e.subject}」({e.date[:10]}) 받는 사람 · 참조 {len(rows)}"
                f"(두 칸을 합친 명단이라 {FIELD_WORDS[forced or 'to']} 칸으로 · {me_word} · 보낸 분은 안 든다)", picks, held)


def lost_received_line(subject: str, lost: list[str]) -> str:
    """받은 메일의 받는 사람 가운데 주소록에서 한 사람으로 안 선 줄들의 따로 둘 줄."""
    return (f"받은 메일 「{subject}」 의 받는 사람 가운데 주소록에서 한 사람으로 안 선 {len(lost)} — 사외 주소 · 주소록에 없는 사람이다. "
            "넣을 사람이면 주소 · 이름을 --name 으로 다시 준다:" + bullets(lost))


def show_tree(run, words: str) -> None:
    """부서 나무 보기 — 조직도를 받아(``chart``) 뿌리를 고르고(``tree_root``) 부서 줄을 지어(``tree_rows``) 보인다(``show_tree_rows``).
    부서를 주면 그 아래만, 안 주면 회사 전체."""
    chart, when = run.chart()
    code = tree_root(chart, words)
    show_tree_rows([x.name for x in chart.path(code)] if code else [], run.company, when, tree_rows(chart, code, run.company))


def tree_root(chart, words: str):
    """부서 나무의 뿌리 부서 코드 — 부서 말을 안 줬으면 None(회사 전체). 그 말이 부서 하나로 안 서면 Stop."""
    if not words:
        return None
    d, why = one_dept(chart, words)
    if d is None:
        raise Stop(EXIT_ARGS, why)
    return d.code


def tree_rows(chart, code, company: str) -> list[tuple[int, str, int, int, str]]:
    """부서 나무의 줄 — 부서마다 (뿌리에서 깊이, 이름, 하위 조직까지 인원, 바로 든 인원, 부서 주소). 뿌리를 주면 그 아래, 아니면 회사
    바로 아래 부서들부터."""
    top = chart.depts[code].depth if code else 1
    return [(x.depth - top, x.name, len(chart.people(x.code)), len(chart.members.get(x.code, [])), x.email)
            for root in (chart.subtree(code) if code else [d for d in chart.depts.values() if d.parent == company])
            for x in (chart.subtree(root.code) if code is None else [root])]


def show_tree_rows(path: list[str], company: str, when: str, rows) -> None:
    """부서 나무를 보인다 — 머리(뿌리의 부서 길 · 없으면 회사 전체)와 조직도의 날짜, 부서마다 한 줄, 다음 걸음."""
    print(f"{' > '.join(path) if path else f'회사 전체({company})'} — 조직도 {when} 판")
    for depth, name, total, direct, email in rows:
        print(f"{'  ' * depth}- {name} · {total} 명(바로 {direct}) · {email}")
    print("— 부서원은 --dept <부서>(하위 조직까지는 --sub), 조직 하나로 보내려면 --org <부서>")


def show_groups(run, kind: str) -> None:
    """배포그룹 목록 보기 — 물을 갈래를 고르고(``asked_kinds``) 갈래마다 목록을 받아(``group_lists``) 보인다(``show_group_lists``)."""
    kinds = asked_kinds(kind)
    show_group_lists(kinds, group_lists(run.box, run.company, [(None, kinds, "")]))


def asked_kinds(kind: str) -> tuple:
    """보일 배포그룹 갈래 — 갈래를 주면 그 하나, 안 주면 셋 다(화면 차례). 모르는 갈래면 Stop."""
    kinds, _ = split_kind(f"{kind}:") if kind else (tuple(GROUP_KIND_WORDS), "")
    if kind and len(kinds) != 1:
        raise Stop(EXIT_ARGS, f"배포그룹 갈래는 {' · '.join(f'{k}({w})' for k, w in GROUP_KIND_WORDS.items())} 가운데 하나다: {kind!r}")
    return kinds


def show_group_lists(kinds: tuple, lists: dict) -> None:
    """갈래마다의 배포그룹 목록을 그 차례로 보이고 다음 걸음을 댄다."""
    for k in kinds:
        print(f"배포그룹 — {GROUP_KIND_WORDS[k]} {len(lists[k])} 개")
        for _, name in lists[k]:
            print(f"- {name}")
    print("— 구성원은 --group <이름>(갈래가 겹치면 「직책:<이름>」)")


# ── 사람찾기 — 그룹사 사람 · 담당업무 ─────────────────────────────────────────

def from_finder(run, values) -> list:
    """사람찾기 앱에서 — 말마다(``finder_ask``) 고른 회사마다(``finder_scopes``) 찾아(``findpeople.App.search``) 출처 한 줄로 낸다
    (``finder_haul``). 내 회사 사람은 주소록의 한 사람에 이어 넘기고, 다른 회사 사람은 찾기만 한다."""
    scopes = finder_scopes(run.finder, run.args.scope or ())
    hauls = []
    for value in values:
        field, kind, word = finder_ask(value)
        for company in scopes:
            hauls.append(finder_haul(run, field, kind, word, company, run.finder.search(findpeople.KINDS[kind], word, company)))
    return hauls


def finder_ask(value: str) -> tuple[str, str, str]:
    """``--finder`` 값 하나 → (칸, 갈래, 말) — 칸 머리(``cc:``)를 떼고, 앞에 갈래 머리(``담당업무:`` · ``이름:`` …)가 있으면 그 갈래, 없으면
    「전체」(이름 · 담당업무 글을 함께 본다)."""
    field, rest = split_field(value)
    head, sep, tail = rest.partition(":")
    return (field, head.strip(), tail.strip()) if sep and head.strip() in findpeople.KINDS else (field, "전체", rest.strip())


def finder_given(value: str) -> None:
    """``--finder`` 값 하나 — 갈래 머리를 뗀 말을 사람찾기 화면이 안 받으면 Stop(세션 앞에서)."""
    why = findpeople.word_problem(finder_ask(value)[2])
    if why:
        raise Stop(EXIT_ARGS, f"--finder 「{value}」 — {why}")


def finder_scopes(app, words) -> list[str]:
    """찾을 회사 값들 — 말을 안 주면 내 회사 · 홀딩스 · 국내그룹사 묶음(``DEFAULT_SCOPES``), 주면 말마다 회사 하나(``scope_of``)."""
    if not words:
        return list(dict.fromkeys(app_own(app) if w == "own" else w for w in DEFAULT_SCOPES))   # 홀딩스 사람이면 내 회사가 홀딩스다
    return list(dict.fromkeys(scope_of(app, w) for chunk in words for w in NAME_SPLIT.split(chunk) if w.strip()))


def app_own(app) -> str:
    """쓰는 사람의 회사 값 — 앱이 들일 때 댄 값. 들어가기 전이면 들어간다."""
    if not app.own:
        app.login()
    return app.own


def scope_of(app, word: str) -> str:
    """회사 말 하나 → 회사 값 — 「내 회사」 · 흔한 말(``SCOPE_WORDS``) · 앱의 회사 이름 · 회사 값. 안 서면 앱이 아는 회사를 대고 Stop."""
    key = inbox.squash(word)
    if key in OWN_WORDS:
        return app_own(app)
    if key in SCOPE_WORDS:
        return SCOPE_WORDS[key]
    app_own(app)   # 회사 이름표는 들어가야 선다
    hits = [v for v, n in app.names.items() if key in (inbox.squash(n), v.casefold())]
    if len(hits) == 1:
        return hits[0]
    raise Stop(EXIT_ARGS, f"--in 「{word}」 — 사람찾기가 아는 회사가 아니다. 다음: 이 가운데 하나(이름이나 값)로 준다 — 홀딩스 · 그룹사 · "
                          + " · ".join(f"{n}({v})" for v, n in app.names.items()))


def scope_word(app, company: str) -> str:
    """회사 값 → 사람 말 — 묶음은 「국내그룹사」, 그 밖은 앱의 회사 이름."""
    return "국내그룹사" if company == findpeople.GROUP else app.names.get(company, company)


def finder_haul(run, field: str, kind: str, word: str, company: str, found) -> Haul:
    """찾기 한 판의 답 → 출처 한 줄 — 내 회사 사람은 주소로 주소록의 한 사람에 잇고(``own_picks``), 다른 회사 사람은 ``seen`` 에 둔다. 답이
    잘렸으면 그 말을 ``cut`` 에 든다. 주소록에서 안 선 내 회사 사람은 따로 둔다(보통 글자 — 다시 불러도 안 갈린다)."""
    said = f"사람찾기 {scope_word(run.finder, company)} {kind} 「{word}」 {found.total} 건"
    own = run.finder.own
    picks, lost = own_picks(run, field, [r for r in found.rows if r.company == own])
    cut = CUT_NOTE.format(scope=scope_word(run.finder, company), word=word, total=found.total, rows=len(found.rows)) if found.cut else ""
    held = []
    if lost:
        held.append(f"{said} 가운데 주소록에서 한 사람으로 안 선 내 회사 사람 {len(lost)} — 찾기만 했다:" + bullets([seen_line(r) for r in lost]))
    return Haul(said, picks, held, seen=[r for r in found.rows if r.company != own], cut=cut)


def own_picks(run, field: str, rows) -> tuple[list, list]:
    """내 회사 사람의 줄 → (주소록의 한 사람으로 선 Pick 들, 안 선 줄들) — 메일 주소로 잇는다(받아 둔 조직도 · 주소록, ``people_of``)."""
    mails = [r.email for r in rows if r.email]
    people = run.people_of(mails) if mails else {}
    picks, lost = [], []
    for r in rows:
        person = people.get(r.email)
        if person is None:
            lost.append(r)
        else:
            picks.append(Pick(field, person))
    return picks, lost


def seen_line(r) -> str:
    """찾기만 한 사람 한 줄 — 이름 · 회사 · 소속 · 직급 · 직책 · 회사 전화 · 담당업무 · 주소."""
    return " · ".join(x for x in (r.name, r.company_name, r.dept, r.grade, r.job_title, r.office, r.duty, r.email) if x)


def merge_seen(hauls) -> list:
    """출처마다 찾기만 한 사람을 한 명단으로 — 한 사람은 (회사, 직번) 쌍이라 그 쌍으로 한 번이다(직번은 회사마다 따로 매긴다)."""
    return list({(r.company, r.empno): r for h in hauls for r in h.seen}.values())


def detail_book(run, picks: list, seen: list) -> dict:
    """사람마다 사람찾기 상세 — {(회사, 직번): 상세의 칸}. 명단이 ``DETAIL_MOST`` 를 넘으면 아무에게도 안 묻고 {None: 까닭}을 낸다. 주소록의
    사람은 내 회사의 같은 직번으로 묻는다(직번 셋이 같은 값이다 — ``references/SOURCES.md``). 앱이 한 번 멈추면 뒤에는 안 묻고 {None: 까닭}을
    더한다."""
    keys = [(None, p.empno.strip()) for p in people_in(picks) if p.empno.strip()] + [(r.company, r.empno) for r in seen]
    if len(keys) > DETAIL_MOST:
        return {None: f"상세는 {DETAIL_MOST} 명까지만 묻는다 — 명단이 {len(keys)} 명이다. 좁혀 다시 --detail"}
    out = {}
    try:
        own = app_own(run.finder)
        for company, empno in keys:
            out[(company or own, empno)] = run.finder.detail(company or own, empno)
    except findpeople.SessionExpired:
        raise                          # 끊긴 세션은 세션 손이 한 번 다시 받는다 — 상세만 못 물은 것으로 덮지 않는다
    except findpeople.AppError as exc:
        out[None] = f"상세를 다 못 물었다(사람찾기 — {exc}) — 명단은 그대로다"
    return out


def detail_said(book: dict) -> dict:
    """상세를 물은 판 → {(회사, 직번): 줄에 달 말} — 까닭 줄(``None``)은 그대로 든다."""
    return {k: v if k is None else detail_words(v) for k, v in book.items()}


def detail_words(fields: dict) -> str:
    """상세의 칸 → 줄에 달 말 — ``DETAIL_FIELDS`` 가운데 그 회사 상세에 있고 빈 것이 아닌 칸만(직무는 「직책/직무」 의 뒤)."""
    duty = fields.get("직책/직무", "").partition("/")[2].strip()
    got = {**fields, "직무": duty}
    return " · ".join(f"{k} {got[k]}" for k in DETAIL_FIELDS if got.get(k, "").strip() and got[k].strip() != "/")


# ── 표 ───────────────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Source:
    """찾기의 출처 하나 — 사람을 데려오는 자리다."""
    takes: str        # many — 값을 여러 번(값 앞에 cc: · bcc: 를 붙이면 그 칸) · none — 켜기만
    metavar: str
    word: str         # 사람 말 — --help 의 지도
    box: bool         # 메일함(세션)에 묻나 — 거짓이면 받아 둔 조직도만으로 선다
    gather: object    # (Run, 인자 값) → [Haul]
    switch: tuple = ()   # 이 출처에 붙는 켜기 — (인자, 사람 말). 같은 켜기를 여러 출처가 함께 받는다
    check: object = None   # 값 하나의 꼴을 세션 앞에서 거른다 — 값 → 틀리면 Stop


@dataclasses.dataclass(frozen=True)
class Sieve:
    """찾기의 거르기 하나 — 모든 출처를 합친 명단의 사람에게 건다."""
    takes: str        # many · one · none
    metavar: str
    word: str
    keep: object      # (inbox.DirectoryPerson, 인자 값) → 남기나
    said: object      # 인자 값 → 거르기 줄의 사람 말


@dataclasses.dataclass(frozen=True)
class View:
    """찾기의 보기 하나 — 사람 대신 목록을 낸다. 출처 · 거르기 · --out 과 함께 안 받는다."""
    metavar: str
    word: str
    box: bool
    show: object      # (Run, 값) → None


def file_given(value: str) -> None:
    """``--from-file`` 값 하나 — 칸 머리를 뗀 파일이 없으면 Stop."""
    path = pathlib.Path(split_field(value, None)[1]).expanduser()
    if not path.is_file():
        raise Stop(EXIT_ARGS, f"--from-file 의 파일이 없다: {path}")


def unid_given(value: str) -> None:
    """``--last`` 값 하나 — 칸 머리를 뗀 것이 메일 열쇠(unid 32자리)의 꼴이 아니면 Stop."""
    unid_shape(split_field(value, None)[1])


def match_keys(words) -> list[str]:
    """``--match`` 낱말을 견줄 열쇠로 — 빈칸 · 가운뎃점 · 괄호를 빼고 대소문자를 접은 꼴(``inbox.squash``), 빈 것은 뺀다."""
    return [k for k in (inbox.squash(w) for w in words or ()) if k]


SUB = ("sub", "하위 조직의 사람까지 — 사람이 「하위 조직까지 · 산하 전체」라고 할 때만")
# 찾기의 손가락 — 출처 아무 조합(합친다) × 거르기 아무 조합(합친 명단 전체에) → 표와 칸마다 주소 파일 · 사람 파일. 출처 · 거르기를 더하거나
# 빼는 일은 이 표의 줄과 그 일을 하는 손 하나다. 인자 · 거름 · --help 의 지도가 다 이 표에서 선다
SOURCES = {
    "name": Source("many", "이름|주소|사번", "이름 · 주소 · 사번 · Notes 이름 · ID 여럿(쉼표 · 가운뎃점으로 이어도 된다) — 그 꼴이 꼭 같은 "
                   "사람이 하나일 때만 든다. 동명이인 · 못 찾은 이름은 후보와 함께 따로 둔다", True, from_names),
    "dept": Source("many", "부서", "부서의 사람 — 그 부서에 바로 든 사람. 이름 일부 · 부서 코드도 된다", False, from_depts, SUB),
    "org": Source("many", "부서", "부서를 조직 하나로 — 부서 주소 하나가 들어 보내는 순간의 구성원에게 간다(부서원으로 안 푼다)", False,
                  from_orgs),
    "all": Source("none", "", "회사 전체의 사람", False, from_all),
    "group": Source("many", "[갈래:]이름", "배포그룹(직책 · 직급 · 지역)의 구성원 — 갈래가 겹치면 「직책:팀장」 꼴", True, from_groups),
    "me": Source("none", "", "나 — 이 세션의 메일함을 쓰는 사람(메일함 파일 번호가 사번이다)", True, from_me),
    "my_dept": Source("none", "", "내 부서의 사람 — 내가 바로 든 부서. 나도 든다(빼려면 --except)", True, from_my_dept, SUB),
    "boss_of": Source("many", "이름|주소|사번", "그 사람의 윗사람 — 그 사람 부서의 장. 본인이 장이거나 장이 없는 부서면 위 부서의 장", True,
                      from_bosses),
    "from_file": Source("many", "파일", "다른 손이 낸 사람 — 사람 파일(people.json) · 손의 JSON 답의 참석자(가장 얕은 attendees — 일정 한 "
                        "건 · 회의실 미리 보기) · 이름 목록 · 한 줄에 이름이나 주소 하나인 글 파일(# 뒤는 버린다)", True, from_files,
                        check=file_given),
    "last": Source("many", "UNID", "지난 메일의 받는 사람 — 보낸 메일은 받는 사람 · 참조 · 숨은참조를 칸 그대로, 조직은 조직 하나로(「지난번과 "
                   "같이」). 받은 메일은 받는 사람 · 참조를 합친 명단(메일 read 의 「함께 받은 사람」)을 받는 사람 칸으로 — 쓰는 사람 자신과 "
                   "보낸 분은 안 든다", True, from_last, check=unid_given),
    "finder": Source("many", "[갈래:]말", "그룹사 사람찾기 앱에서 — 담당업무 · 이름 · 조직 · 직번 · 전화 · 메일(갈래 머리 " + " · ".join(
                     f"{k}:" for k in findpeople.KINDS if k != "전체") + ", 없으면 전체). 회사는 --in(없으면 내 회사 · 홀딩스 · 국내그룹사). "
                     "내 회사 사람은 주소록의 사람으로 넘기고, 다른 회사 사람은 찾기만 한다(파일에 안 든다)", True, from_finder,
                     check=finder_given),
}
SIEVES = {
    "grade": Sieve("many", "직급", "이 직급만(여러 번) — 과장 · 차장 같은 직급 이름", lambda p, v: p.grade.strip() in {x.strip() for x in v},
                   lambda v: f"직급 {'/'.join(v)}"),
    "title": Sieve("many", "직책", "이 직책만(여러 번) — 리더 · 그룹장 같은 직책 이름", lambda p, v: p.job_title.strip() in {x.strip() for x in v},
                   lambda v: f"직책 {'/'.join(v)}"),
    "boss": Sieve("none", "", "조직의 장만", lambda p, v: p.is_boss, lambda v: "조직의 장"),
    "at_least": Sieve("one", "P5", "이 인사 등급 이상만(P5 · E3 꼴 — 같은 갈래끼리) — 등급이 없는 사람은 빠진다",
                      lambda p, v: inbox.level_at_least(p.level, v), lambda v: f"{v.upper()} 이상"),
    "match": Sieve("many", "말", "이름 · 부서 · 직급 · 직책 · 근무지 · 담당 업무 · 주소에 이 말이 든 사람만(여러 번 주면 다 든 사람)",
                   lambda p, v: all(k in inbox.squash("|".join((p.name, p.dept, p.grade, p.job_title, p.location, p.duty, p.email)))
                                    for k in match_keys(v)),
                   lambda v: " · ".join(f"「{w}」 이 든" for w in v)),
}
VIEWS = {
    "tree": View("부서", "부서 나무 · 부서마다 인원 · 부서 주소 — 부서를 주면 그 아래만", False, show_tree),
    "groups": View("갈래", "배포그룹 목록 — 갈래(jobtitle · grade · location)를 주면 그 갈래만", True, show_groups),
}


def flag_of(dest: str) -> str:
    """표의 칸 이름을 인자 이름으로 — ``boss_of`` → ``--boss-of``."""
    return "--" + dest.replace("_", "-")


def given_of(args, table: dict) -> list[str]:
    """그 표에서 값이 든 줄 — 켜기는 참, 값은 빈 것이 아닐 때."""
    return [k for k in table if getattr(args, k, None) not in (None, [], False, "")]


def view_of(args) -> list[str]:
    """준 보기 — 보기는 값 없이도(빈 글자) 준 것이다."""
    return [k for k in VIEWS if getattr(args, k, None) is not None]


def asks_box(args) -> bool:
    """이 판이 메일함(세션)에 묻나 — 준 출처 · 보기 가운데 하나라도 메일함에 묻거나, 조직도를 새로 받거나, 전화 · 상세를 물을 때. 거짓이면
    받아 둔 조직도로 선다."""
    return bool(getattr(args, "fresh", False) or getattr(args, "phone", False) or getattr(args, "detail", False)
                or any(SOURCES[k].box for k in given_of(args, SOURCES))
                or any(VIEWS[k].box for k in view_of(args)))


def check_args(args) -> None:
    """출처 · 거르기 · 보기가 표에 맞나 — 세션 · 메일함 · 조직도에 닿기 전에 가린다."""
    given, views = given_of(args, SOURCES), view_of(args)
    narrowing = (given_of(args, SIEVES) + (["except"] if args.without else []) + (["out"] if args.out else [])
                 + (["phone"] if args.phone else []) + (["detail"] if args.detail else []))
    if len(views) > 1:
        raise Stop(EXIT_ARGS, "보기(--tree · --groups)는 한 번에 하나다")
    if views and (given or narrowing):
        raise Stop(EXIT_ARGS, f"--{views[0]} 는 목록을 보이는 보기라 출처 · 거르기 · 빼기 · --out · --phone 과 함께 안 받는다 — 사람을 찾으려면 "
                              "--name · --dept 같은 출처만 준다")
    if not views and not given:
        raise Stop(EXIT_ARGS, "찾을 출처가 없다 — --help 의 지도에서 출처(" + " · ".join(flag_of(k) for k in SOURCES) + ")를 하나 넘게 준다")
    for switch in {s.switch for s in SOURCES.values() if s.switch}:
        takers = [k for k, s in SOURCES.items() if s.switch == switch]
        if getattr(args, switch[0], False) and not set(takers) & set(given):
            raise Stop(EXIT_ARGS, f"{flag_of(switch[0])} 는 {' · '.join(flag_of(k) for k in takers)} 에 붙는다 — {switch[1]}")
    if args.scope and "finder" not in given:
        raise Stop(EXIT_ARGS, "--in 은 --finder 에 붙는다 — 사람찾기에서 찾을 회사(홀딩스 · 그룹사 · 회사 이름)")
    for k in given:
        for v in getattr(args, k) if SOURCES[k].check else ():
            SOURCES[k].check(v)
    if args.at_least:
        try:
            inbox.level_at_least("", args.at_least)
        except inbox.MailboxConfigError as exc:
            raise Stop(EXIT_ARGS, f"--at-least — {exc}") from exc


def find_map() -> str:
    """--help 의 지도 — 출처 · 거르기 · 보기 표에서 짓는다."""
    def head(k, takes, metavar):
        return flag_of(k) + (f" <{metavar}>" if takes != "none" else "")
    lines = ["출처 — 한 부름에 아무 조합이나 준다(값은 여러 번). 값 앞에 cc: · bcc: 를 붙이면 그 칸으로, 없으면 받는 사람"]
    for k, s in SOURCES.items():
        lines.append(f"  {head(k, s.takes, s.metavar)}" + (f"  [{flag_of(s.switch[0])}]" if s.switch else ""))
        lines.append(f"      {s.word}" + (f" · {flag_of(s.switch[0])} 는 {s.switch[1]}" if s.switch else "")
                     + (" (세션)" if s.box else " (받아 둔 조직도 — 세션 없이도)"))
    lines += ["", "거르기 — 모든 출처를 합친 명단의 사람에게 건다. 조직 · 사외 주소는 못 걸러 파일에서 빼고 따로 둔다"]
    lines += [f"  {head(k, s.takes, s.metavar)}\n      {s.word}" for k, s in SIEVES.items()]
    lines += ["", "빼기 — 거르기 앞에서 명단의 꼭 한 사람을 뺀다. 안 서면 아무 파일도 안 쓰고 멈춘다", "  --except <주소|이름>",
              "", "보기 — 사람 대신 목록. 출처 · 거르기 · --out 과 함께 안 받는다"]
    lines += [f"  {flag_of(k)} [{v.metavar}]\n      {v.word}" + (" (세션)" if v.box else " (받아 둔 조직도)") for k, v in VIEWS.items()]
    lines += ["", f"내는 꼴 — 늘: 출처 · 거르기 · 칸마다 수 · 등급별 · 직급별 · 직책별 수와 {SHOWN} 줄까지의 명단(넘으면 부서별 수 · --list),",
              "  따로 둔 것(동명이인 · 못 찾은 이름 · 여럿 걸린 부서 · 못 거른 조직 — 파일에 안 든다).",
              "  --out <폴더> 면 칸마다 주소 파일을 쓰고 메일 draft 에 그대로 줄 인자(--to-file … )를 댄다 — 주소를 옮겨 적지 않는다.",
              "  이름으로 댄 것이 안 서 따로 두면(동명이인 · 못 찾은 이름 · 여럿 걸린 부서) 파일을 안 쓰고 종료 2 다 — 고른 꼴로(빼라면 그",
              "  이름 없이) 다시 부르면 다 든 파일이 선다. 무리의 구성원(배포그룹 · 지난 메일 · 파일)이 안 선 줄은 알리기만 하고 0 이다.",
              f"  같은 폴더에 사람 파일 둘 — {PEOPLE_JSON}(일정 · 회의실 · 문서함이 --people-file 로 받는다 — 문서함 권한은 --people-as 와 함께)과 {PEOPLE_FILE}(한 줄에 "
              "「이름/메일ID」 — 문서함 권한). 조직 · 사외 주소는 안 든다.",
              f"  --phone 이면 명단의 사람({PHONE_MOST} 명까지)마다 사규 앱의 사람 창에 사번으로 물어 회사 전화 · 휴대 전화를 줄에 단다(세션).",
              "  --finder 가 찾은 다른 회사 사람은 「찾기만 한 사람」 으로 따로 보이고(거르기는 걸린다) 어느 파일에도 안 든다.",
              f"  --detail 이면 명단의 사람({DETAIL_MOST} 명까지)마다 사람찾기 상세의 칸(직무 · 근무형태 · 근무현황 …)을 줄에 단다(세션)"]
    return "\n".join(lines)


def add_find_args(q: argparse.ArgumentParser) -> None:
    """찾기의 인자를 단다 — 출처 · 거르기 · 보기 표와 내는 꼴의 인자."""
    switches = set()
    for k, s in SOURCES.items():
        if s.takes == "none":
            q.add_argument(flag_of(k), dest=k, action="store_true", help=s.word)
        else:
            q.add_argument(flag_of(k), dest=k, action="append", metavar=s.metavar, help=s.word)
        if s.switch and s.switch[0] not in switches:
            switches.add(s.switch[0])
            takers = " · ".join(flag_of(x) for x, t in SOURCES.items() if t.switch == s.switch)
            q.add_argument(flag_of(s.switch[0]), dest=s.switch[0], action="store_true", help=f"{takers} 에 붙어 {s.switch[1]}")
    for k, s in SIEVES.items():
        how = {"none": {"action": "store_true"}, "one": {"default": "", "metavar": s.metavar},
               "many": {"action": "append", "metavar": s.metavar}}[s.takes]
        q.add_argument(flag_of(k), dest=k, help=s.word, **how)
    q.add_argument("--except", dest="without", action="append", metavar="주소|이름",
                   help="명단에서 이 사람을 뺀다(여러 번) — 거르기 앞에서. 명단의 꼭 한 사람에 안 서면 아무 파일도 안 쓰고 멈춘다")
    for k, v in VIEWS.items():
        q.add_argument(flag_of(k), dest=k, nargs="?", const="", default=None, metavar=v.metavar, help=v.word)
    q.add_argument("--out", default="", metavar="폴더",
                   help="칸마다 주소 파일(" + " · ".join(WHO_FILE.format(field=f) for f in FIELD_WORDS) + ")을 이 폴더에 쓰고 "
                        f"draft 에 그대로 줄 인자를 댄다. 칸 셋을 합친 사람 파일({PEOPLE_JSON} — 사람을 받는 손의 --people-file · "
                        f"{PEOPLE_FILE} — 한 줄에 「이름/메일ID」 · 문서함 권한이 받는 꼴)도 쓴다 — 저장소 밖 폴더")
    q.add_argument("--list", action="store_true", help=f"명단이 {SHOWN} 줄을 넘어도 낸다(끊어 낸다) — 없으면 수만 낸다")
    q.add_argument("--start", type=int, default=0, help="명단을 이 줄 다음부터 — 답이 잘렸을 때 댄 값")
    q.add_argument("--fresh", action="store_true", help="받아 둔 조직도를 버리고 새로 받는다")
    q.add_argument("--phone", action="store_true",
                   help=f"명단의 사람({PHONE_MOST} 명까지)마다 회사 전화 · 휴대 전화 — 사규 앱의 사람 창에 사번으로 묻는다")
    q.add_argument("--in", dest="scope", action="append", metavar="회사",
                   help="--finder 에 붙어 찾을 회사(여러 번 · 쉼표로) — 홀딩스 · 그룹사(국내그룹사 묶음) · 내 회사 · 사람찾기의 회사 이름 · "
                        "값. 없으면 내 회사 → 홀딩스 → 국내그룹사")
    q.add_argument("--detail", action="store_true",
                   help=f"명단의 사람({DETAIL_MOST} 명까지 · 찾기만 한 사람도)마다 사람찾기 상세 — 직무 · 근무형태 · 근무현황 · 원소속 · 팩스 · "
                        "휴대 전화(칸은 회사마다 다르다)")
    q.add_argument("--company", default="", help=f"회사 값 — 없으면 MAIL_COMPANY, 그것도 없으면 {DEFAULT_COMPANY}")


# ── 합치기 · 거르기 · 내기 ──────────────────────────────────────────────────

def merge_picks(hauls) -> tuple[list, list[str]]:
    """출처마다 데려온 것을 한 명단으로 — 같은 주소는 한 번이고 칸이 다르면 앞 칸(받는 사람 · 참조 · 숨은참조 차례)이 선다. 주소가 없는
    사람은 따로 둔다."""
    rank = {f: i for i, f in enumerate(FIELD_WORDS)}
    kept: dict[str, Pick] = {}
    bare = []
    for h in hauls:
        for p in h.picks:
            if not p.mail:
                bare.append(p.line())
            elif (have := kept.get(p.mail.casefold())) is None:
                kept[p.mail.casefold()] = p
            elif rank[p.field] < rank[have.field]:
                kept[p.mail.casefold()] = dataclasses.replace(have, field=p.field)
    picks = sorted(kept.values(), key=lambda p: rank[p.field])   # 칸 차례로 — 같은 칸 안은 데려온 차례 그대로
    return picks, ([bare_line(bare)] if bare else [])


def bare_line(bare: list[str]) -> str:
    """주소가 없어 받는 사람으로 못 넣는 사람들의 따로 둘 줄."""
    return f"주소가 없어 받는 사람으로 못 넣는 {len(bare)}:" + bullets(bare)


def without_picks(picks: list, words) -> tuple[list, list]:
    """명단에서 뺄 사람(주소나 이름)을 뺀다 — (남은 것, 뺀 것). 뺄 말이 명단의 꼭 하나에 안 서면 Stop — 못 뺀 채 나가면 빼려던 사람에게
    메일이 간다. 거르기 앞에서 빼니 거르기에 걸려 나갈 사람을 빼라 해도 선다."""
    gone = []
    for word in [w.strip() for chunk in words or () for w in chunk.split(",") if w.strip()]:
        hits = [p for p in picks if word.casefold() == p.mail.casefold() or word == p.label]
        if len(hits) != 1:
            why = "명단에 없다" if not hits else f"명단에 {len(hits)} 명이다 — 주소로 준다: " + ", ".join(p.mail for p in hits)
            raise Stop(EXIT_ARGS, f"--except 「{word}」 — {why}. 아무 파일도 안 썼다")
        gone.append(hits[0])
        picks = [p for p in picks if p is not hits[0]]
    return picks, gone


def sieve_picks(args, picks: list) -> tuple[list, int, list[str], list[str]]:
    """준 거르기를 모든 출처를 합친 명단에 건다 — (남은 것, 걸러 나간 사람 수, 거르기 줄의 말, 따로 둘 줄). 조직 · 사외 주소는 직급 ·
    직책이 없어 거르지 못하니 파일에 넣지 않고 따로 둔다 — 넣으면 거르기 밖의 사람에게 간다."""
    given = [(SIEVES[k], getattr(args, k)) for k in given_of(args, SIEVES)]
    if not given:
        return picks, 0, [], []
    kept, dropped, unjudged = [], 0, []
    for p in picks:
        if p.person is None:
            unjudged.append(p)
        elif all(s.keep(p.person, v) for s, v in given):
            kept.append(p)
        else:
            dropped += 1
    return kept, dropped, [s.said(v) for s, v in given], ([unjudged_line(unjudged)] if unjudged else [])


def unjudged_line(unjudged: list) -> str:
    """거르기가 못 거는 조직 · 사외 주소의 따로 둘 줄."""
    return (f"거르기가 못 거는 받는 사람 {len(unjudged)} — 조직 · 사외 주소는 직급 · 직책이 없어 파일에서 뺐다. 조직을 사람으로 풀어 "
            "거르려면 --dept <부서>:" + bullets([p.line() for p in unjudged]))


def write_who_files(folder: str, picks: list, head: str) -> list[tuple[str, pathlib.Path, int]]:
    """칸마다 주소 파일을 쓴다 — 칸 셋을 다 쓰고(빈 칸은 머리 줄만 · 앞 판의 파일이 남지 않게) 사람이 든 칸만 (칸, 경로, 주소 수)로 낸다.
    사외 주소는 저장 명령이 못 실어 주석으로만 둔다 — 칸의 파일을 그대로 줘도 저장이 선다."""
    root = pathlib.Path(folder).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    head = " ".join(head.split())   # 머리는 한 줄이다 — 출처 말(제목 · 부서 이름)에 줄바꿈이 섞이면 그 뒤가 주소 줄로 읽힌다
    out = []
    for field, word in FIELD_WORDS.items():
        rows = [p for p in picks if p.field == field]
        inside = [p.mail for p in rows if not p.outside]
        path = root / WHO_FILE.format(field=field)
        path.write_bytes(("\n".join([f"# who · {word} · {head}", *inside,
                                     *(f"# 사외 주소 — 저장 명령이 못 싣는다: {p.mail}" for p in rows if p.outside)]) + "\n").encode("utf-8"))
        if inside:
            out.append((field, path, len(inside)))
    return out


def people_only(picks: list) -> list:
    """명단의 사람만 — 같은 주소는 한 번(앞 칸의 줄)이다. 조직 · 사외 주소는 사람이 아니다."""
    return list({p.mail.casefold(): p for p in reversed(picks) if p.person is not None}.values())[::-1]


def write_people_file(folder: str, picks: list, head: str) -> tuple[pathlib.Path, int, list, list]:
    """칸 셋을 합친 사람마다 「이름/메일ID」 한 줄의 사람 파일을 쓴다(``PEOPLE_FILE``) — (경로, 사람 수, 안 넣은 조직, 안 넣은 사외 주소).
    조직은 메일 조직도의 부서 코드가 문서함의 것과 같은지 안 재서, 사외 주소는 한 사람의 「이름/메일ID」 로 안 서서 주석으로만 둔다."""
    path = pathlib.Path(folder).expanduser().resolve() / PEOPLE_FILE
    people = people_only(picks)
    orgs, outside = [p for p in picks if p.org], [p for p in picks if p.outside]
    path.write_bytes(("\n".join([f"# who · 사람 · {' '.join(head.split())}", "# 한 줄에 「이름/메일ID」 — 스킬 company-ecm 의 권한 칸이 받는 꼴",
                                 *(f"{p.label}/{p.mail.split('@', 1)[0]}" for p in people),
                                 *(f"# 조직 — 안 넣었다: {p.name} · {p.mail}" for p in orgs),
                                 *(f"# 사외 주소 — 안 넣었다: {p.mail}" for p in outside)]) + "\n").encode("utf-8"))
    return path, len(people), orgs, outside


def person_record(p: Pick) -> dict:
    """사람 파일(``PEOPLE_JSON``)의 한 사람 — 읽는 자리의 칸(``ep_command.PEOPLE_KEYS``)을 그 차례로 다 든다. 모르는 값은 빈 글자다.
    칸마다의 값은 주소록의 한 사람에서 짓는다 — 칸이 늘었는데 값이 없으면 ``KeyError`` 로 멈춘다."""
    d = p.person
    value = {"name": d.name.strip(), "email": d.email.strip(), "mail_id": d.email.strip().split("@", 1)[0], "empno": d.empno.strip(),
             "dept": d.dept.strip(), "dept_code": d.dept_code.strip(), "grade": d.grade.strip(), "job_title": d.job_title.strip(),
             "is_boss": bool(d.is_boss), "notes": d.notes.strip(), "field": p.field}
    return {k: value[k] for k in ep_command.PEOPLE_KEYS}


def write_people_json(folder: str, picks: list) -> tuple[pathlib.Path, int]:
    """기계가 읽는 사람 파일을 쓴다(``PEOPLE_JSON`` — UTF-8 · BOM 없이) — (경로, 사람 수). ``people.txt`` 와 같은 명단에서 뽑는다."""
    path = pathlib.Path(folder).expanduser().resolve() / PEOPLE_JSON
    rows = [person_record(p) for p in people_only(picks)]
    path.write_bytes(json.dumps({"format": ep_command.PEOPLE_FORMAT, "people": rows}, ensure_ascii=False, indent=1).encode("utf-8"))
    return path, len(rows)


class Phones(NamedTuple):
    """전화를 물은 판 — 아무에게도 안 물었으면 그 까닭(``TOO_MANY`` · ``NO_HAND``)과 말감(명단 수 · 못 실은 까닭), 물었으면 빈 글자 · 사람마다의
    답(주소 → 사람 창의 답 dict 또는 ``NO_EMPNO`` · ``CUT`` · ``BLANK``) · 사규 앱이 멈춘 까닭(멈추지 않았으면 빈 글자)."""
    unasked: str
    why: str
    cards: dict
    broke: str


def phone_book(run, people: list) -> Phones:
    """사람마다 사규 앱의 사람 창(형제 스킬 company-regulation 의 ``cbsop.App.person``)에 사번으로 묻는다 — 명단이 ``PHONE_MOST`` 를
    넘거나 그 앱 손을 못 실으면 아무에게도 안 묻는다. 사규 앱이 한 번 멈추면(앱 고장 · 끊긴 세션 · 없는 세션 파일) 뒤의 사람에게는 안
    묻는다 — 메일 서버의 주소록은 이미 답했으니 사람을 로그인으로 보낼 까닭이 아니다."""
    if len(people) > PHONE_MOST:
        return Phones(TOO_MANY, str(len(people)), {}, "")
    try:
        cbsop = ep_command.load("cbsop", REGULATION_SCRIPTS)
    except ep_command.Stop as exc:
        return Phones(NO_HAND, str(exc), {}, "")
    cards, broke = {}, ""
    try:
        app = cbsop.App(run.session_file)
    except cbsop.AppError as exc:
        broke = str(exc)
    for p in people:
        if not p.empno.strip():
            cards[p.email.casefold()] = NO_EMPNO
            continue
        if not broke:
            try:
                got = app.person(p.empno.strip())
            except cbsop.AppError as exc:      # 끊긴 세션 · 없는 세션 파일도 이 갈래다
                broke = str(exc)
        cards[p.email.casefold()] = CUT if broke else (got or BLANK)
    return Phones("", "", cards, broke)


def phone_words(phones: Phones) -> tuple[dict, str]:
    """전화를 물은 판 → (주소 → 줄에 달 말, 따로 댈 말). 사람 창의 답은 회사 전화(``officePhone``) · 휴대 전화(``handpon``)를 단다."""
    if phones.unasked == TOO_MANY:
        return {}, f"전화는 {PHONE_MOST} 명까지만 묻는다 — 명단이 {phones.why} 명이다. 좁혀 다시 --phone"
    if phones.unasked == NO_HAND:
        return {}, f"전화를 못 물었다 — {phones.why}"
    said = {NO_EMPNO: "전화 — 주소록에 사번이 없다", CUT: "전화 — 못 물었다(아래 ⚠)",
            BLANK: "전화 — 사람 창이 비었다(퇴직이거나 사규 앱에 그 사번이 없다)"}
    out = {}
    for addr, card in phones.cards.items():
        if isinstance(card, str):
            out[addr] = said[card]
            continue
        office, mobile = (card.get("officePhone") or "").strip(), (card.get("handpon") or "").strip()
        out[addr] = " · ".join(x for x in (f"회사 {office}" if office else "", f"휴대 {mobile}" if mobile else "") if x) \
            or "전화 — 사람 창에 번호가 없다"
    return out, (f"전화를 못 물었다(사규 앱 — {phones.broke}) — 명단은 주소록의 것 그대로다. 사규 앱 화면에서 그 사람 이름을 눌러 본다"
                 if phones.broke else "")


def find(args, session_file) -> None:
    """찾기 한 판 — 보기면 목록을 내고, 아니면 출처마다 데려와(``gather``) 합치고 · 빼고 · 걸러 (``--phone``) 전화를 물은 뒤 명단을
    보이고(``show_found``) 파일을 넘긴다(``hand_on``). 아무것도 안 바꾼다. 인자의 꼴은 ``check_args`` 가 세션 앞에서 이미 봤다.
    ``session_file`` 은 이 판의 세션 파일이다(받아 둔 조직도로 서는 판이면 None)."""
    run = Run(args, session_file)
    if views := view_of(args):
        VIEWS[views[0]].show(run, getattr(args, views[0]))
        return
    hauls = gather(run)
    picks, bare = merge_picks(hauls)
    seen = merge_seen(hauls)
    picks, gone = without_picks(picks, args.without)
    picks, dropped, sieved, unjudged = sieve_picks(args, picks)
    seen, seen_dropped = sieve_seen(args, seen)
    held = held_lines(hauls, bare, unjudged)
    phones, phone_note = phone_words(phone_book(run, people_in(picks))) if args.phone else ({}, "")
    details = detail_said(detail_book(run, picks, seen)) if args.detail else {}
    shown = shown_of(run, hauls, picks, with_details(phones, details, picks, run))
    show_found(run.when, hauls, gone, dropped + seen_dropped, sieved, held, shown, phone_note, args.start)
    show_seen([h.cut for h in hauls if h.cut], seen, details)
    hand_on(run, hauls, picks, sieved, held, shown.outside, seen)


def sieve_seen(args, seen: list) -> tuple[list, int]:
    """준 거르기를 찾기만 한 사람에게도 건다 — (남은 줄, 걸러 나간 수). 줄의 칸 이름이 주소록의 사람과 같아 같은 거르기가 선다(등급 ·
    장 여부는 이 앱에 없어 ``--at-least`` · ``--boss`` 는 다 걸러 낸다)."""
    given = [(SIEVES[k], getattr(args, k)) for k in given_of(args, SIEVES)]
    kept = [r for r in seen if all(s.keep(r, v) for s, v in given)]
    return kept, len(seen) - len(kept)


def with_details(phones: dict, details: dict, picks: list, run) -> dict:
    """줄에 달 말(주소 → 말) — 전화 말 뒤에 그 사람의 사람찾기 상세 말을 잇는다. 상세를 안 물었으면 전화 말 그대로다."""
    if not details:
        return phones
    own = run.finder.own
    out = dict(phones)
    for p in people_in(picks):
        said = details.get((own, p.empno.strip()), "")
        if said:
            key = p.email.casefold()
            out[key] = " · ".join(x for x in (out.get(key, ""), said) if x)
    return out


def show_seen(cuts: list, seen: list, details: dict) -> None:
    """찾기만 한 다른 회사 사람을 보인다 — 잘린 답의 말 · 상세를 못 물은 말, 회사별 수와 줄(``SHOWN`` 줄까지 — 넘으면 수만). 파일에 안
    든다고 댄다."""
    for line in cuts:
        print(f"⚠ {line}")
    if None in details:
        print(f"⚠ {details[None]}")
    if not seen:
        return
    print(SEEN_NOTE.format(n=len(seen)))
    print("회사별: " + ranked_words(ranked(counts_by(seen, "company_name")), TALLY_TOP))
    if len(seen) > SHOWN:
        print(f"찾기만 한 사람은 {len(seen)} 줄이라 안 실었다 — 회사(--in) · 거르기(--match · --grade · --title)로 좁힌다")
        return
    for r in seen:
        said = details.get((r.company, r.empno), "")
        print(f"  - {seen_line(r)}" + (f" · {said}" if said else ""))


def gather(run) -> list:
    """준 출처마다 데려온 것(``Haul``) — 출처 표(``SOURCES``)의 차례로, 그 줄의 ``gather`` 칸이 데려온다."""
    return [h for k in given_of(run.args, SOURCES) for h in SOURCES[k].gather(run, getattr(run.args, k))]


def held_lines(hauls, bare: list, unjudged: list) -> list:
    """따로 둘 줄 모두 — 출처마다의 것, 주소 없는 사람, 거르기가 못 거는 조직 · 사외 주소의 차례로."""
    return [x for h in hauls for x in h.held] + bare + unjudged


def people_in(picks: list) -> list:
    """명단의 사람(주소록의 한 사람) — 조직 · 사외 주소는 뺀다."""
    return [p.person for p in picks if p.person is not None]


class Shown(NamedTuple):
    """보일 명단의 셈 — 칸마다 수(조직 · 사외 포함) · 명단의 사람 · 조직 수 · 사외 수 · 둘 넘는 칸에 들었나 · 등급별 · 직급별 · 직책별
    순위(``ranked``) · 줄마다 (Pick, 전화 말) · 명단을 접나 · 접을 때의 부서별 순위와 보일 부서 수(None 이면 다)."""
    fields: dict
    people: list
    orgs: int
    outside: int
    several: bool
    levels: list
    grades: list
    titles: list
    rows: list
    folded: bool
    branches: list
    branch_top: int | None


def shown_of(run, hauls, picks: list, phones: dict) -> Shown:
    """명단을 보일 셈을 한다 — 명단이 ``SHOWN`` 을 넘고 ``--list`` · ``--start`` 가 없으면 접고 부서별로 센다. 출처가 하나이고 그 출처가
    조직 아래로 세는 뿌리(``Haul.branch``)를 들면 그 조직 바로 아래 부서별(이 판에 받은 조직도로), 아니면 주소록의 부서 이름별이다."""
    people = people_in(picks)
    fields = {f: sum(p.field == f for p in picks) for f in FIELD_WORDS}
    folded = len(picks) > SHOWN and not run.args.list and not run.args.start
    branch = hauls[0].branch if folded and len(hauls) == 1 else ()
    branches, top = ((ranked(branch_counts(run.chart()[0], branch[0], run.company, people)), None) if branch
                     else (ranked(counts_by(people, "dept")), TALLY_TOP) if folded else ([], None))
    return Shown(fields, people, sum(p.org for p in picks), sum(p.outside for p in picks), sum(n > 0 for n in fields.values()) > 1,
                 ranked(counts_by(people, "level")), ranked(counts_by(people, "grade")), ranked(counts_by(people, "job_title")),
                 [(p, phones.get(p.mail.casefold(), "") if p.person is not None else "") for p in picks], folded, branches, top)


def row_words(p, phone: str, several: bool) -> str:
    """명단의 한 줄 — 둘 넘는 칸에 사람이 들었으면 칸 이름표, 그 사람 줄(``Pick.line``), 전화를 물었으면 그 말."""
    return (f"[{FIELD_WORDS[p.field]}] " if several else "") + p.line() + (f" · {phone}" if phone else "")


def show_found(when: str, hauls, gone, dropped: int, sieved: list, held: list, shown: Shown, phone_note: str, start: int) -> None:
    """찾은 명단을 보인다 — 머리 · 출처 · 거르기 · 뺀 사람 · 칸마다 수 · 등급별 · 직급별 · 직책별은 늘, 명단(접으면 부서별 수와 좁히는
    법) · 전화를 못 물은 말 · 따로 둔 것은 늘 다 댄다."""
    print(TITLE + (f" — 조직도 {when} 판" if when else ""))
    print("출처: " + " · ".join(h.said for h in hauls))
    if sieved:
        print(f"거르기: {' · '.join(sieved)} — 걸러 나간 사람 {dropped} 명")
    for p in gone:
        print(f"뺐다(--except): {p.line()}")
    counts = " · ".join(f"{FIELD_WORDS[f]} {n}" for f, n in shown.fields.items() if n or f == "to")
    print(f"{counts} — 사람 {len(shown.people)} 명" + (f" · 조직 {shown.orgs}" if shown.orgs else "")
          + (f" · 사외 {shown.outside}" if shown.outside else "") + " (같은 주소는 한 번 · 칸이 겹치면 앞 칸)")
    if shown.people:
        print(f"등급별: {ranked_words(shown.levels)}")
        print(f"직급별: {ranked_words(shown.grades)}")
        print(f"직책별: {ranked_words(shown.titles)}")
    if shown.folded:
        print("부서별: " + ranked_words(shown.branches, shown.branch_top))
        print(FOLDED.format(n=len(shown.rows)))
    else:
        show_rows([row_words(p, phone, shown.several) for p, phone in shown.rows], start)
    if phone_note:
        print(f"⚠ {phone_note}")
    if held:
        print(f"⚠ 따로 둔 것 {len(held)} — 파일에 안 넣었다. 고르지 말고 사람에게 묻고, 고른 것을 줄마다 댄 꼴로 다시 준다:")
        for line in held:
            print(f"  - {line}")


def hand_on(run, hauls, picks: list, sieved: list, held: list, outside: int, seen: list) -> None:
    """찾은 명단을 다음 손에 넘긴다 — ``--out`` 을 안 줬으면 그 길을 대고, 이름으로 댄 것이 안 섰으면 파일을 안 쓰고 멈추고(``HELD_STOP``
    — 앞 판이 쓴 파일도 그대로다), 아니면 파일 셋을 쓰고(``write_files``) 다음 손에 줄 인자를 댄다(``show_hand_on``)."""
    state, asks = file_state(run.args.out, held)
    if state == NO_OUT:
        if picks or not seen:   # 찾기만 한 사람뿐이면 넘길 사람이 없다 — 파일 길을 대지 않는다
            show_no_out()
        return
    if state == HELD:
        raise Stop(EXIT_ARGS, HELD_STOP.format(n=asks), stepped=True)
    show_hand_on(write_files(run.args.out, picks, file_head(hauls, sieved, run.when)), outside)


def show_no_out() -> None:
    """``--out`` 을 안 준 판의 끝 줄 — 받는 사람으로 쓰는 길을 댄다."""
    print(NO_OUT_HINT)


def file_state(out: str, held: list) -> tuple[str, int]:
    """파일을 써도 되나 — (``NO_OUT`` 폴더를 안 줬다 · ``HELD`` 이름으로 댄 것 가운데 안 선 줄(``Ask``)이 있다 · ``WRITE`` 쓴다, 안 선 줄의
    수)."""
    asks = sum(isinstance(x, Ask) for x in held)
    return (NO_OUT if not out else HELD if asks else WRITE), asks


def file_head(hauls, sieved: list, when: str) -> str:
    """파일 머리 줄에 적을 이 찾기의 말 — 출처 · 거르기 · 조직도의 날짜."""
    return (" · ".join(h.said for h in hauls) + (f" · 거르기 {' · '.join(sieved)}" if sieved else "")
            + (f" · 조직도 {when} 판" if when else ""))


class Written(NamedTuple):
    """``--out`` 폴더에 쓴 것 — 사람이 든 칸의 주소 파일((칸, 경로, 주소 수)) · 「이름/메일ID」 사람 파일의 경로 · 사람 수 · 안 넣은 조직 ·
    안 넣은 사외 주소 · 기계가 읽는 사람 파일의 경로."""
    who: list
    sheet: pathlib.Path
    persons: int
    orgs: list
    outside: list
    records: pathlib.Path


def write_files(out: str, picks: list, head: str) -> Written:
    """``--out`` 폴더에 파일 셋을 쓴다 — 칸마다 주소 파일 · 「이름/메일ID」 사람 파일 · 기계가 읽는 사람 파일. 못 쓰면 Stop."""
    try:
        who = write_who_files(out, picks, head)
        sheet, persons, orgs, outside = write_people_file(out, picks, head)
        records, _ = write_people_json(out, picks)
    except OSError as exc:
        raise Stop(EXIT_ARGS, OUT_UNWRITTEN.format(why=exc)) from exc
    return Written(who, sheet, persons, orgs, outside, records)


def show_hand_on(written: Written, outside: int) -> None:
    """쓴 파일과 다음 손에 줄 인자를 댄다 — 주소 파일 · draft 에 그대로 줄 인자 · 사외 주소 · 두 사람 파일과 받는 손 · 사람 파일에 안 넣은
    것. 파일에 넣을 받는 사람이 없으면 그렇다고만 댄다."""
    if not written.who:
        print(NOBODY_FILED)
        return
    print("주소 파일: " + " · ".join(f"{FIELD_WORDS[f]} {n} 개 → {path}" for f, path, n in written.who))
    print(f"{DRAFT_AS_IS} " + " ".join(f'--{f}-file "{path}"' for f, path, _ in written.who))
    if outside:
        print(f"사외 주소 {outside} 개는 파일에 주석으로만 뒀다 — 저장한 뒤 웹메일에서 더하라고 이른다")
    print(f"사람 파일: {written.persons} 명 → {written.sheet} — 한 줄에 「이름/메일ID」(칸 셋을 합쳤다). 문서함(company-ecm) 권한에 그 파일을 "
          "그대로 준다")
    print(f"사람 파일(JSON): {written.persons} 명 → {written.records} — 일정 · 회의실 · 문서함에 --people-file \"{written.records}\" 로 그대로 "
          "준다(문서함 권한은 --people-as edit · copy · read 를 함께). 메일 저장은 위의 draft 인자다")
    if written.orgs or written.outside:
        print("사람 파일에 안 넣은 것 — "
              + " · ".join(x for x in (
                  f"조직 {len(written.orgs)}({', '.join(p.name for p in written.orgs)} — 메일 조직도의 부서 코드가 문서함의 것과 같은지 안 "
                  "쟀다. 부서는 문서함 쪽에서 부서 이름으로 준다)" if written.orgs else "",
                  f"사외 주소 {len(written.outside)}({', '.join(p.mail for p in written.outside)} — 한 사람의 이름/메일ID 로 안 선다)"
                  if written.outside else "") if x))


# ── 명령 ─────────────────────────────────────────────────────────────────

NOT_DONE = (
    ("주소록 · 조직도 고치기", "인사 시스템이 한다 — 이 손은 읽기만 한다"),
    ("동명이인 · 여럿 걸린 부서 가운데 고르기", "사람이 고른다 — 손은 후보를 대고 파일에 안 넣는다"),
    ("일정함을 공유하지 않은 사람의 빈 때", "그 사람에게 묻는다 — 스킬 company-calendar 는 공유받은 일정함만 본다"),
)


def parser() -> argparse.ArgumentParser:
    """명령의 인자 표 — 하위 명령 ``find`` 와 그 인자(``add_find_args`` — 표에서), 종료 값 범례와 사람이 하는 자리를 --help 에 단다."""
    lines = ["명령", "  find  사람 찾기 — 출처 아무 조합 × 거르기 → 표와 칸마다 주소 파일 · 사람 파일(인자의 지도는 find --help)", "",
             ep_command.exit_legend((EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION), {EXIT_ARGS: HELD_LEGEND},
                                    said="0 이 아니면 끝 줄이 까닭과 다음 걸음을 든다"),
             "", "안 하는 것 — 사람이 하는 자리", *(f"  {what}: {where}" for what, where in NOT_DONE)]
    p = argparse.ArgumentParser(prog="directory.py", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="\n".join(lines),
                                description="사내 주소록 · 조직도 · 배포그룹에서 사람과 부서를 찾는다 — 읽기만 한다")
    p.add_argument("--url", default="", help="메일함 주소 …/<번호>.nsf — 없으면 MAILBOX_URL, 그것도 없으면 세션이 댄다(주소록은 메일 서버가 낸다)")
    sub = p.add_subparsers(dest="command", required=True, metavar="<명령>")
    q = sub.add_parser("find", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=find_map(),
                       description="사람을 찾는다 — 출처 아무 조합을 합치고 거르기를 그 명단 전체에 건다. 사람이 볼 수 · 표와 (--out) 칸마다 "
                                   "주소 파일 · 사람 파일을 낸다. 아무것도 안 바꾼다")
    add_find_args(q)
    return p


def main(argv=None) -> int:
    """명령 입구 — 출력의 꼴을 세우고 인자를 받아 거른 뒤(``check_args`` — 세션 · 메일함에 닿기 전에) 찾기 한 판을 고른 세션으로 돌린다
    (``choose_session``). 메일 손 · 세션의 예외는 메일 손의 한 자리(``stops_from_mail``)가 멈춤으로 옮기고, 멈춤은 그 말과 종료 값으로
    끝낸다(``stopped``)."""
    set_up_output()
    args = parser().parse_args(argv)
    try:
        check_args(args)
        with stops_from_mail(inbox, failed=BOOK_FAILED), stops_from_finder():
            choose_session(args)
    except Stop as stop:
        return stopped(stop)
    return EXIT_OK


@contextlib.contextmanager
def stops_from_finder():
    """그 안에서 난 사람찾기 손의 예외를 멈춤으로 옮긴다 — 세션이 끊겼거나 세션 파일이 없으면 3, 앱이 거절했거나 꼴이 아니면 1."""
    try:
        yield
    except (findpeople.SessionExpired, findpeople.SessionMissing) as exc:
        raise Stop(EXIT_SESSION, f"사람찾기 앱에 못 들어갔다 — {exc}") from exc
    except findpeople.AppError as exc:
        raise Stop(EXIT_TOOL, f"사람찾기 앱에서 못 받았다 — {exc}") from exc


def set_up_output() -> None:
    """출력의 꼴을 세운다 — 표준 출력 · 오류는 UTF-8, 경고 기록은 「경고: 」 한 줄."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.WARNING, format="경고: %(message)s")


def choose_session(args) -> None:
    """찾기 한 판(``find``)을 고른 세션으로 돌린다 — 받아 둔 조직도로 서는 판이면 세션 없이, 아니면 사내 세션을 받아(끊기면 한 번 다시
    받는다 — ``ep_session.session_first``)."""
    if stands_on_kept(args):
        find(args, None)
    else:
        ep_session.session_first(functools.partial(find, args), expired=(inbox.SessionExpired, findpeople.SessionExpired),
                                 env=session_env(args))


def stands_on_kept(args) -> bool:
    """이 판이 받아 둔 조직도로 서나 — 메일함(세션)에 묻지 않는 판(``asks_box``)이고 그 회사 값의 받아 둔 조직도가 있으면. 세션 파일이
    없어도 답한다."""
    return not asks_box(args) and bool(cached_org(company_of(args.company)))


def session_env(args) -> dict | None:
    """세션 손에 넘길 환경 — 사람 · 설정이 메일함 주소를 줬으면(메일 손의 ``given_url``) 그 주소를 ``MAILBOX_URL`` 로. 안 줬으면 None."""
    url = given_url(args.url)
    return {"MAILBOX_URL": url} if url else None


def stopped(stop: Stop) -> int:
    """멈춘 말(``Stop.said`` — 다음 걸음까지)을 표준 출력에 내고 그 종료 값을 낸다."""
    print(stop.said())
    return stop.code


if __name__ == "__main__":
    sys.exit(main())
