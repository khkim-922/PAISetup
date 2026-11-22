"""사내 주소록 · 조직도에서 사람을 찾는 얇은 명령이자, 사람을 받는 다른 손이 불러 쓰는 한 자리.

무엇을 하나
    출처 아무 조합(``SOURCES`` — 합친다) × 거르기 아무 조합(``SIEVES`` — 합친 명단 전체에) → 사람이 볼 수 · 표와, ``--out`` 이면 그 폴더에
    칸마다 주소 파일 · 사람 파일 둘(``people.txt`` 「이름/메일ID」 · ``people.json`` 기계가 읽는 꼴)을 쓴다. 보기(``VIEWS``)는 사람 대신
    목록(부서 나무 · 배포그룹)을 낸다. 주소록 · 메일함 어디도 안 바꾼다.

    사람 파일 ``people.json`` 은 ``{"format": 1, "people": [{…}, …]}`` — 사람마다 ``PEOPLE_KEYS`` 의 칸이 다 들고 모르는 값은 빈 글자다.
    조직 · 사외 주소는 사람이 아니라 안 든다. 주소 파일과 ``people.txt`` 는 같은 명단에서 뽑는다. 다른 손(일정 · 회의실 · 문서함)이
    ``--people-file`` 로 받고, 메일 저장은 칸마다 주소 파일을 받는다.

    사내 주소록 · 조직도는 메일 서버가 낸다 — 묻는 손은 형제 스킬 company-mail 의 ``inbox.py``(``Mailbox`` 의 주소록 · 조직도 손)이고,
    세션으로 메일함을 여는 자리는 그 스킬의 ``mail.py`` 의 ``open_mailbox`` 다. 전화는 형제 스킬 company-regulation 의 사람 창
    (``cbsop.App.person``)이 사번으로 낸다.

어떻게 부르나
    python -X utf8 -I directory.py [--url 메일함] find <출처 · 거르기 · 보기 …>

    인자의 지도는 ``find --help`` 가 이 파일의 표에서 낸다. 인자의 꼴이 틀리면 세션을 받기 전에 종료 2 로 멈춘다(``check_args``).
    조직도만 쓰는 판(부서 · 조직 하나 · 회사 전체 · 나무)은 받아 둔 조직도로 세션 없이 선다(``asks_box`` 가 표의 ``box`` 칸에서 가른다).

    불러 쓰는 꼴 — 형제 스킬 company-mail 의 ``mail.py who`` 는 이 표에 지난 메일 출처 하나를 더해 ``find`` 를 부른다. 임시메일의 받는
    사람 잇기는 ``address_people`` · ``kept_book`` · ``dept_book`` 을, 배포그룹 넣기는 ``split_kind`` · ``group_lists`` · ``one_group`` 을 부른다.

받아 둔 조직도
    ``MAIL_ORG_CACHE_DIR`` 이 있으면 그 폴더, 없으면 홈 아래 ``ORG_CACHE_DIR`` 에 회사 값마다 한 파일 — ``ORG_CACHE_DAYS`` 동안 쓴다.
    회사 값은 ``--company`` · ``MAIL_COMPANY`` · ``DEFAULT_COMPANY`` 순이다.

무엇을 내나
    사람이 읽을 글줄을 표준 출력에 낸다. 종료 값마다의 뜻은 맨 위 ``--help`` 의 범례(사내 앱 명령의 한 표 ``ep_command``)가 든다.
    「⚠ 따로 둔 것」(동명이인 · 못 찾은 이름 · 여럿 걸린 부서 · 못 거른 조직)은 파일에 안 든다 — 고르는 것은 사람이다. ``--out`` 의
    찾기에 이름으로 댄 것 가운데 안 선 줄(``Ask`` — 동명이인 · 못 찾은 이름 · 여럿 걸린 부서)이 있으면 파일을 안 쓰고 종료 2 로
    끝난다(``HELD_STOP``) — 이은 다음 손도 따로 부른 손도 빠진 명단으로 돌지 않게. 무리의 구성원이 안 선 줄 · 알림 줄은 파일을 쓰고 0
    이다(선 사람이 없으면 받는 손이 빈 파일에서 멈춘다).
"""

from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.modules.setdefault("directory", sys.modules["__main__"])   # 불려 쓰일 때와 한 모듈 — mail.py 가 같은 이름으로 싣는다

import argparse
import dataclasses
import json
import logging
import os
import pathlib
import re
import time
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
SKILLS = HERE.parents[1]                              # 형제 스킬은 스킬 홈에 나란히 깔린다
EP_LOGIN_SCRIPTS = SKILLS / "ep-login" / "scripts"
MAIL_SCRIPTS = SKILLS / "company-mail" / "scripts"
REGULATION_SCRIPTS = SKILLS / "company-regulation" / "scripts"
for _where in (EP_LOGIN_SCRIPTS, MAIL_SCRIPTS):
    if str(_where) not in sys.path:
        sys.path.insert(0, str(_where))               # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
try:
    import ep_command
    import ep_session
    import inbox
except ImportError as _missing:                       # 형제 스킬이 곁에 없다 — 주소록을 물을 손이 없어 어느 명령도 못 돈다
    print(f"형제 스킬(ep-login · company-mail)이 이 스킬 곁에 없다({_missing}) — 설치를 다시 돌린다")
    sys.exit(1)

EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION = ep_command.EXIT_OK, ep_command.EXIT_TOOL, ep_command.EXIT_ARGS, ep_command.EXIT_SESSION
DEFAULT_COMPANY = "poscochem(02)"   # 주소록의 회사 값 — 조직도 고름 상자의 값(메일함마다 다르다)
ORG_CACHE_DAYS = 30           # 받아 둔 조직도를 다시 받지 않고 쓰는 날 — 전사를 받는 데 오래 걸리고 인사는 드물게 바뀐다. 그 사이는 --fresh
ORG_CACHE_DIR = ".company-mail"   # 받아 둔 조직도 · 메일함 주소의 자리 — 홈 아래(임시 폴더는 정리 도구가 지운다)
ORG_CACHE_FORMAT = 3          # 캐시 파일의 꼴 번호 — DirectoryPerson · Dept 칸이나 받아 두는 칸이 바뀌면 올린다
ORG_CACHE_BLANK = ("user_id", "name_eng")   # 받아 둘 때 비우는 칸 — 받아 둔 판을 읽는 손이 안 쓰는 ID · 영문 이름(사번은 사람 파일 · 전화가 쓴다)
SHOWN = 40                    # 명단에서 이름을 보이는 수 — 넘으면 수만 댄다(명단은 --list · 파일)
HELD_SHOWN = 10               # 따로 둔 줄 하나 아래 늘어놓는 후보(동명이인 · 그 글자가 든 사람 · 여럿 걸린 부서)의 수 — 넘으면 좁혀 다시 달라고 한다
TALLY_TOP = 15                # 부서별 수가 보이는 부서의 수 — 넘는 부서는 한 덩이로 접는다
NAME_SPLIT = re.compile(r"[,;·ㆍ、]")   # --name 한 값에 여럿을 이은 가름 — 사람이 말한 「김철수 · 이영희」 를 그대로 넘겨도 된다
WHO_FILE = "{field}.txt"      # --out 폴더 안의 칸마다 주소 파일 — 메일 draft 의 --to-file · --cc-file · --bcc-file 이 읽는 꼴(한 줄에 주소 하나 · # 뒤는 버린다)
# --out 폴더 안의 사람 파일 — 칸 셋을 합친 사람마다 「이름/메일ID」 한 줄(# 로 시작하는 줄은 주석). 스킬 company-ecm 의 권한 칸이
# 사람 하나를 받는 꼴이고, 메일 ID 는 주소의 @ 앞이다(문서함의 메일 ID 는 메일 주소록의 그 사람과 같다 — 그 스킬의 SOURCES.md)
PEOPLE_FILE = "people.txt"
PEOPLE_JSON = "people.json"   # 같은 폴더의 기계가 읽는 사람 파일 — 사람을 받는 손이 --people-file 로 받는다
PEOPLE_FORMAT = 1             # 그 파일의 꼴 번호 — 칸을 바꾸면 올리고, 받는 쪽(ep-login 의 읽는 자리)이 같은 번호만 읽는다
PEOPLE_KEYS = ("name", "email", "mail_id", "empno", "dept", "dept_code", "grade", "job_title", "is_boss", "notes", "field")
FIELD_WORDS = {"to": "받는 사람", "cc": "참조", "bcc": "숨은참조"}   # 받는 사람 칸 → 사람 말 — 사람 파일의 field 값이기도 하다
GROUP_KIND_WORDS = {"jobtitle": "직책", "grade": "직급", "location": "지역"}   # 배포그룹 갈래 → 화면의 이름
DEPT_MAIL = re.compile(r"^dept_[^@\s]+@", re.IGNORECASE)   # 조직도의 부서 주소 꼴(dept_<회사>_<부서 코드>@) — 이 꼴만 부서로 찾는다
DEPT_WORD = "(조직)"          # 사람이 아니라 조직 하나일 때 이름 뒤에 붙이는 표지
MAILFILE_NUMBER = re.compile(r"/(\d+)\.nsf$", re.IGNORECASE)   # 메일함 파일 번호 = 그 메일함을 쓰는 사람의 사번(<사번>.nsf)
PHONE_MOST = 10               # --phone 이 사람 창을 묻는 사람 수의 위 — 사람마다 사규 앱에 한 번씩 묻는다
NEXT_MARK = "다음:"           # 멈춘 말이 다음 걸음을 드는 표지
# 「다음:」 이 빠진 멈춤에 붙는 걸음 — 종료 값마다 하나. 멈추는 자리가 제 걸음을 대면 그 말이 앞선다(``Stop.said``)
NEXT_WORDS = {
    EXIT_TOOL: "다음: 이 말을 그대로 사람에게 알린다 — 같은 명령을 되풀이하지 않는다. 웹메일 화면에서 할 일이면 사람이 웹메일에서 한다",
    EXIT_ARGS: "다음: 위 말이 짚은 값을 고쳐 다시 부른다 — 같은 인자로 되풀이하지 않는다(인자의 꼴은 <명령> --help)",
    EXIT_SESSION: ep_command.NEXT_EP_LOGIN,
    ep_command.EXIT_STALE: "다음: 미리 보기(preview-…)를 다시 불러 지금 판을 사람에게 보이고 확인받는다",
}
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
RECENT_MAIL_SCAN = 300        # 동명이인 후보마다 최근 주고받은 메일을 셀 때 받은편지함 · 보낸편지함에서 받는 새것의 수 — 한 쪽씩이다

log = logging.getLogger("company-directory")


class Stop(Exception):
    """명령을 멈춘다 — ``code`` 가 종료 값, 메시지가 사람에게 낼 글이다. 이 손을 불러 쓰는 메일 명령도 같은 꼴을 쓴다."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code

    def said(self) -> str:
        """사람에게 낼 글 — 「다음: …」 이 없으면 종료 값의 걸음(``NEXT_WORDS``)을 붙인다. 0 이 아닌 끝은 늘 다음 걸음을 든다."""
        text = str(self)
        step = NEXT_WORDS.get(self.code)
        return text if NEXT_MARK in text or not step else f"{text}\n{step}"


def load_mail():
    """형제 스킬 company-mail 의 명령 ``mail`` — 세션으로 메일함을 여는 자리(``open_mailbox``)를 이 명령이 홀로 돌 때만 싣는다."""
    try:
        return ep_command.load("mail", MAIL_SCRIPTS)
    except ep_command.Stop as exc:
        raise Stop(EXIT_TOOL, str(exc)) from exc


# ── 받아 둔 조직도 ────────────────────────────────────────────────────────

def cache_dir() -> pathlib.Path:
    """받아 둔 것(조직도 · 메일함 주소)의 자리 — ``MAIL_ORG_CACHE_DIR`` 이 있으면 그 폴더, 없으면 홈 아래 ``ORG_CACHE_DIR``."""
    root = os.environ.get("MAIL_ORG_CACHE_DIR", "").strip()
    return pathlib.Path(root) if root else pathlib.Path.home() / ORG_CACHE_DIR


def company_of(args) -> str:
    """주소록의 회사 값 — ``--company`` · ``MAIL_COMPANY`` · ``DEFAULT_COMPANY`` 순."""
    return (getattr(args, "company", "") or os.environ.get("MAIL_COMPANY", "").strip() or DEFAULT_COMPANY).strip()


def org_cache_path(company: str) -> pathlib.Path:
    """회사 값 하나의 받아 둔 조직도 파일 — 이름에 못 쓰는 글자는 첨부 가름 손(company-mail 의 ``attachments``)의 자로 바꾼다."""
    try:
        unsafe = ep_command.load("attachments", MAIL_SCRIPTS).UNSAFE_NAME
    except ep_command.Stop as exc:
        raise Stop(EXIT_TOOL, str(exc)) from exc
    return cache_dir() / f"org-{unsafe.sub('_', company)}.json"


def cached_org(company: str):
    """받아 둔 조직도 — ``ORG_CACHE_DAYS`` 안에 받은 판이 있으면 (OrgChart, 받은 시각 글자), 없거나 낡았거나 깨졌으면 None.
    서버에 묻지 않는다. 한 프로세스 안에서는 같은 파일(쓴 시각까지)을 한 번만 읽는다 — 한 판이 여러 자리(세션 가름 · 주소 잇기 ·
    출처마다)에서 묻는다."""
    path = org_cache_path(company)
    try:
        mark = (str(path), path.stat().st_mtime_ns)
    except OSError:
        return None
    if mark not in _READ:
        _READ.clear()
        _READ[mark] = _read_org(path)
    return _READ[mark]


_READ: dict = {}   # 이 프로세스가 읽은 받아 둔 조직도 — (경로, 쓴 시각) → cached_org 의 답


def _read_org(path: pathlib.Path):
    got = ep_command.kept(path, ORG_CACHE_FORMAT, ORG_CACHE_DAYS, by_mtime=True)
    if not got:
        return None
    raw, stamp = got
    try:
        chart = inbox.OrgChart(
            company=raw["company"],
            depts={c: inbox.Dept(**d) for c, d in raw["depts"].items()},
            members={c: [inbox.DirectoryPerson(**p) for p in ps] for c, ps in raw["members"].items()})
    except (ValueError, KeyError, TypeError, AttributeError):
        return None   # 칸이 안 맞는 캐시 — 없는 것으로 친다
    return chart, time.strftime("%m-%d %H:%M", time.localtime(stamp))


def load_org(args, company: str, open_box):
    """회사 조직 한 판 — 받아 둔 판(``cached_org``)이 있으면 그것을, 없거나 ``--fresh`` 면 조직도에서 새로 받아 둔다.
    내는 것 (OrgChart, 받은 시각 글자). ``open_box(args)`` 가 세션으로 연 메일함이다. 받은 판을 PC 에 못 남겨도 받은 것으로
    답한다 — 그때는 경고 한 줄을 낸다."""
    got = None if getattr(args, "fresh", False) else cached_org(company)
    if got:
        return got
    chart = open_box(args).org_snapshot(company)
    blank = dict.fromkeys(ORG_CACHE_BLANK, "")
    unkept = ep_command.keep(org_cache_path(company), {
        "format": ORG_CACHE_FORMAT, "company": chart.company,
        "depts": {c: dataclasses.asdict(d) for c, d in chart.depts.items()},
        "members": {c: [dataclasses.asdict(p) | blank for p in ps] for c, ps in chart.members.items()}})
    if unkept:
        log.warning("받은 조직도를 PC 에 못 남겼다(%s) — 다음 판도 조직도에서 새로 받는다", unkept)
    return chart, "방금"


def chart_book(chart) -> dict:
    """조직도 한 판의 주소 → 사람들(퇴직자 빼고) — 주소로 사람을 잇는 표다."""
    book: dict[str, list] = {}
    for p in chart.people():
        if p.email and not p.retired:
            book.setdefault(p.email.casefold(), []).append(p)
    return book


def kept_book(company: str) -> tuple[dict, str]:
    """받아 둔 조직도의 주소 → 사람들(``chart_book``)과 그 판의 날짜. 받아 둔 판이 없으면 빈 표 · 빈 날짜다 — 전사를 받는 데 오래
    걸려 새로 받지 않는다."""
    got = cached_org(company)
    return (chart_book(got[0]), got[1]) if got else ({}, "")


def dept_book(args, company: str, open_box) -> dict:
    """부서 주소 → 그 부서(``inbox.Dept``) — 받아 둔 조직도로, 없으면 조직도를 받아 둔 뒤. 조직 하나를 받는 사람으로 넣는 자리다
    (부서원을 풀지 않는다 — 보내는 순간의 구성원에게 간다)."""
    chart, _ = load_org(args, company, open_box)
    return {d.email.casefold(): d for d in chart.depts.values() if d.email}


def address_people(box, mails: list[str], company: str, book: dict) -> dict:
    """주소 → 그 주소의 주소록 사람(퇴직자 빼고)이 꼭 하나이고 Notes 이름이 있으면 그 사람, 아니면 None. 메일의 임시메일 받는 사람
    잇기와 사람 찾기가 이 한 자를 쓴다 — 찾기가 파일에 넣은 주소는 메일 draft 가 받는다.

    받아 둔 조직도(``book``)에 있는 주소는 거기서 잇고, 없는 주소만 주소록에 함께(``inbox.ORG_WORKERS`` 만큼) 묻는다 — 그때만
    ``box`` 가 쓰인다. 웹메일 화면은 받는 사람을 Notes 이름으로 다시 연다. 그래서 주소록에 없는 주소(사외 · 부서 주소)는 사람으로 안
    선다.
    """
    def ask(a: str) -> list:
        return [p for p in box.find_exact(a, company) if p.email.casefold() == a.casefold() and not p.retired]
    unknown = list(dict.fromkeys(a for a in mails if a.casefold() not in book))
    with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
        asked = dict(zip(unknown, pool.map(ask, unknown)))
    found = {}
    for a in mails:
        people = book.get(a.casefold()) or asked.get(a, [])
        found[a] = people[0] if len(people) == 1 and people[0].notes else None
    return found


# ── 한 판 ─────────────────────────────────────────────────────────────────

def person_line(p, dept: bool = True) -> str:
    """사람 한 줄 — 이름 · 부서 · 직급(인사 등급) · 직책 · 장 · 근무지 · 담당 업무 · 주소. ``dept`` 가 거짓이면 부서를 뺀다."""
    marks = [m for m, on in (("장", p.is_boss), ("퇴직", p.retired)) if on]
    grade = f"{p.grade}({p.level})" if p.grade and p.level else p.grade
    return " · ".join(x for x in (p.name, p.dept if dept else "", grade, p.job_title, *marks, p.location, p.duty, p.email) if x)


def same_person(a, b) -> bool:
    """주소록의 두 줄이 한 사람인가 — Notes 이름이 둘 다 있으면 그것으로, 아니면 주소로."""
    if a.notes.strip() and b.notes.strip():
        return inbox.notes_key(a.notes) == inbox.notes_key(b.notes)
    return bool(a.email.strip()) and a.email.strip().casefold() == b.email.strip().casefold()


def show_rows(rows: list[str], start: int = 0) -> None:
    """번호 붙인 줄을 start 째부터 낸다 — 답이 OUT_BYTES 를 넘기 전까지. 남으면 남은 수와 다음 --start 를 댄다."""
    start, room = max(0, start), ep_session.OUT_BYTES
    for i, row in enumerate(rows[start:], start + 1):
        line = f"{i}. {row}"
        room -= len(line.encode("utf-8")) + 1
        if room < 0 and i > start + 1:
            print(f"… 남은 {len(rows) - i + 1} 명 — 다음: 같은 명령에 --start {i - 1}")
            return
        print(line)


def tally(people, field: str, top: int | None = None) -> str:
    """사람들의 그 칸 값별 수 — 많은 것부터. ``top`` 을 주면 그만큼만 보이고 나머지는 한 덩이로 접는다."""
    counts: dict[str, int] = {}
    for p in people:
        key = getattr(p, field) or "(빈 값)"
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    rest = ranked[top:] if top else []
    return " · ".join(f"{k} {n}" for k, n in ranked[:top]) + (f" · 그 밖 {len(rest)} 곳 {sum(n for _, n in rest)}" if rest else "")


def by_branch(chart, code, company: str, picked) -> str:
    """고른 사람을 그 조직 바로 아래 부서별로 센다 — 그 조직에 바로 든 사람은 「(바로)」. 많은 것부터."""
    branch = {}
    for top in [d for d in chart.depts.values() if d.parent == (code or company)]:
        for d in chart.subtree(top.code):
            branch[d.code] = top.name
    counts: dict[str, int] = {}
    for p in picked:
        key = branch.get(p.dept_code) or ("(바로)" if p.dept_code == code else "(그 밖)")
        counts[key] = counts.get(key, 0) + 1
    return " · ".join(f"{k} {n}" for k, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


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
        return (self.person.email if self.person is not None else self.email).strip()

    @property
    def label(self) -> str:
        return (self.person.name if self.person is not None else self.name).strip()

    @property
    def outside(self) -> bool:
        return self.person is None and not self.org

    def line(self) -> str:
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
    수를 그 조직 바로 아래로 셀 때의 뿌리((부서 코드,) · 회사 전체면 (None,))다."""
    said: str
    picks: list
    held: list
    branch: tuple = ()


class Run:
    """찾기 한 판 — 메일함 · 조직도는 그 출처가 처음 부를 때 한 번만 연다(조직도만 쓰는 판은 세션 없이 선다). ``open_box(args)`` 는
    세션으로 메일함을 여는 자리다(메일 명령의 ``open_mailbox``)."""

    def __init__(self, args, open_box):
        self.args, self.inbox, self.company, self.open_box = args, inbox, company_of(args), open_box
        self._box = self._chart = None
        self._book_when = ""        # 주소로 사람을 이을 때 쓴 받아 둔 조직도의 날짜 — 이 판에 조직도를 안 받았을 때
        self._me = False

    @property
    def box(self):
        if self._box is None:
            self._box = self.open_box(self.args)
        return self._box

    def chart(self):
        """(OrgChart, 받은 시각 글자) — 받아 둔 판이 있으면 그것, 없거나 --fresh 면 새로 받아 둔다."""
        if self._chart is None:
            self._chart = load_org(self.args, self.company, self.open_box)
        return self._chart

    @property
    def when(self) -> str:
        """이 판이 기댄 조직도의 날짜 — 받은 판이 없고 받아 둔 판으로 주소를 잇지도 않았으면 빈 글자."""
        return self._chart[1] if self._chart else self._book_when

    def people_of(self, mails: list[str]) -> dict:
        """주소 → 주소록의 그 한 사람(``address_people``) — 이 판에 받은 조직도가 있으면 그것을, 없으면 받아 둔 판을 먼저 본다."""
        if self._chart:
            book = chart_book(self._chart[0])
        else:
            book, self._book_when = kept_book(self.company)
        return address_people(self.box if any(a.casefold() not in book for a in mails) else None, mails, self.company, book)

    def me(self):
        """쓰는 사람(이 메일함의 주인) — 한 판에 한 번만 묻는다(``owner_person``)."""
        if self._me is False:
            self._me = owner_person(self)
        return self._me


def split_field(value: str, default: str | None = "to") -> tuple[str | None, str]:
    """출처 값 앞의 칸 머리(``cc:`` · ``bcc:`` · ``to:``)를 뗀다 — (칸, 나머지). 머리가 없으면 ``default``."""
    head, sep, rest = value.partition(":")
    if sep and head.strip().lower() in FIELD_WORDS:
        return head.strip().lower(), rest.strip()
    return default, value.strip()


def split_kind(value: str) -> tuple[tuple, str]:
    """배포그룹 값 앞의 갈래 머리(``직책:`` · ``jobtitle:`` …)를 뗀다 — (찾을 갈래들, 그룹 이름). 머리가 없으면 갈래 셋 다다."""
    head, sep, rest = value.partition(":")
    names = {**{k: k for k in GROUP_KIND_WORDS}, **{w: k for k, w in GROUP_KIND_WORDS.items()}}
    kind = names.get(head.strip().lower()) if sep else None
    return ((kind,), rest.strip()) if kind else (tuple(GROUP_KIND_WORDS), value.strip())


def bullets(rows: list[str], most: int = HELD_SHOWN, more: str = "") -> str:
    """따로 둔 줄 아래의 후보들 — ``most`` 개까지, 넘으면 남은 수와 ``more``(좁히는 법)를 댄다."""
    out = "".join(f"\n      · {r}" for r in rows[:most])
    return out + (f"\n      … 외 {len(rows) - most}{' — ' + more if more else ''}" if len(rows) > most else "")


def one_dept(chart, words: str):
    """부서 이름 · 코드 → (그 부서, 빈 글자) 또는 (None, 따로 둘 줄) — 못 찾았거나 여럿 걸리면 고르지 않는다."""
    hits = chart.find_depts(words)
    if len(hits) == 1:
        return hits[0], ""
    if not hits:
        return None, Ask(f"못 찾은 부서 「{words}」 — 조직도에 그 이름 · 코드가 든 부서가 없다. 이름을 줄여 다시 주거나 --tree 로 나무를 본다")
    paths = [f"{' > '.join(x.name for x in chart.path(d.code))} ({d.code})" for d in hits]
    return None, Ask(f"여럿 걸린 부서 「{words}」 {len(hits)} 곳 — 고르지 않는다. 사람이 고른 줄의 괄호 속 부서 코드로 다시 준다:"
                     + bullets(paths, more="이름을 길게 주어 좁힌다"))


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
    """그 사람의 윗사람 — 그 부서의 장이고, 장이 없거나 본인이 그 부서의 장(장이 여럿인 부서의 한 사람이어도)이면 위 부서로 올라간다 —
    같은 부서의 다른 장은 윗사람이 아니다. (장, 빈 글자) 또는 (None, 까닭)."""
    code = dept.code
    while code in chart.depts:
        here = [m for m in chart.members.get(code, []) if m.is_boss and not m.retired]
        if any(same_person(m, p) for m in here):
            code = chart.depts[code].parent
            continue
        bosses = list({m.notes or m.email: m for m in here}.values())
        if len(bosses) == 1:
            return bosses[0], ""
        if bosses:
            return None, (f"{chart.depts[code].name} 에 장이 {len(bosses)} 명이라 고르지 않는다:" + bullets([person_line(b) for b in bosses]))
        code = chart.depts[code].parent
    return None, "조직도에서 그 위의 장을 못 찾았다 — 맨 위 부서의 장이다"


# ── 출처 ─────────────────────────────────────────────────────────────────

def split_pick(handle: str) -> tuple[str, str]:
    """「이름[부서]」 → (이름, 부서 말) — 동명이인 가운데 그 부서의 사람을 고른 꼴이다. 꼴이 아니면 (그대로, 빈 글자)."""
    found = PICK_FORM.match(handle)
    return (found.group(1).strip(), found.group(2).strip()) if found else (handle, "")


def dept_path(run, p) -> str:
    """그 사람의 부서 길(「맨 위 > … > 그 부서」) — 이 판에 받은 조직도나 받아 둔 판으로만 짓고 새로 받지 않는다. 판이 없거나 그 사람이
    조직도에 없으면 주소록의 부서 이름이다."""
    got = run._chart or cached_org(run.company)
    d = home_dept(got[0], p) if got else None
    return " > ".join(x.name for x in got[0].path(d.code)) if d is not None else p.dept


def recent_mail(run, people) -> dict:
    """주소 → 최근 메일을 주고받은 말(「최근 메일 받은 2 · 보낸 1 · 마지막 11-03」) — 받은편지함 · 보낸편지함의 새것 ``RECENT_MAIL_SCAN``
    통을 한 번씩 받아 센다. 동명이인을 사람이 가를 실마리다. 못 받으면 빈 표다(후보 줄은 그 말 없이 선다)."""
    want = {p.email.casefold() for p in people if p.email}
    try:
        got = run.box.list(count=RECENT_MAIL_SCAN)
        sent = run.box.list_sent(count=RECENT_MAIL_SCAN)
    except inbox.SessionExpired:
        raise
    except inbox.MailboxError:
        return {}
    marks: dict = {}
    for kind, addr, when in [("받은", e.sender.addr, e.date) for e in got] + [("보낸", r.addr, s.date) for s in sent for r in s.recipients]:
        a = (addr or "").casefold()
        if a in want:
            m = marks.setdefault(a, {"받은": 0, "보낸": 0, "last": ""})
            m[kind] += 1
            m["last"] = max(m["last"], when or "")
    out = {a: f"최근 메일 받은 {m['받은']} · 보낸 {m['보낸']} · 마지막 {m['last'][5:10]}" for a, m in marks.items()}
    return {a: out.get(a, f"최근 메일 없음(받은 · 보낸 새것 {RECENT_MAIL_SCAN}통에서)") for a in want}


def homonym_lines(run, name: str, live) -> list[str]:
    """동명이인 후보 줄 — 부서 길 · 직급 · 직책 · 주소 · 최근 주고받은 메일과, 고르면 다음 부름에 그대로 줄 꼴(「이름[부서]」 — 부서가
    후보마다 다를 때. 같으면 주소). 「이름[부서]」 는 한 글자 틀려도 다른 사람이 아니라 아무도 안 선다."""
    recent = recent_mail(run, live)
    leaves = [inbox.squash(p.dept) for p in live]
    rows = []
    for p, leaf in zip(live, leaves):
        pick = f"{name}[{p.dept}]" if p.dept.strip() and leaves.count(leaf) == 1 else p.email
        mark = recent.get(p.email.casefold(), "")
        rows.append(" · ".join(x for x in (person_line(p, dept=False), dept_path(run, p), mark) if x) + f"  → 고르면 --name \"{pick}\"")
    return rows


def resolve(run, asks) -> list:
    """(칸, 이름 · 주소 · 사번 · Notes 이름 · ID · 「이름[부서]」) 여럿 → 줄마다 (칸, 그 말, 그 한 사람 또는 None, 따로 둘 줄). 주소록에
    함께 묻고, 그 꼴이 꼭 같은 살아 있는 사람이 하나일 때만 선다. 「이름[부서]」 는 그 이름의 사람 가운데 부서(주소록의 부서 이름 ·
    조직도의 부서 길)에 그 말이 든 사람이다.
    동명이인 · 못 찾은 이름 · 퇴직은 후보와 함께 따로 둘 줄이다 — 고르는 것은 사람이다."""
    picks = [split_pick(h) for _, h in asks]
    queries = [inbox.directory_query(base) for base, _ in picks]
    box = run.box if any(queries) else None
    with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
        answers = list(pool.map(lambda q: box.find_people(q[0], run.company) if q else [], queries))
    out = []
    for (field, handle), (base, where), q, every in zip(asks, picks, queries, answers):
        same = [p for p in every if q and q[1](p)]
        live = [p for p in same if not p.retired]
        if where and live:
            narrowed = [p for p in live if inbox.squash(where) in inbox.squash(f"{p.dept} {dept_path(run, p)}")]
            if not narrowed:
                out.append((field, handle, None, f"「{handle}」 — {base} 가운데 부서 길에 「{where}」 가 든 사람이 없다. 고르지 않는다:"
                            + bullets(homonym_lines(run, base, live))))
                continue
            live = narrowed
        if len(live) == 1:
            out.append((field, handle, live[0], ""))
        elif len(live) > 1:
            out.append((field, handle, None, f"동명이인 「{handle}」 {len(live)} 명 — 고르지 않는다. 누구인지 묻고, 사람이 고른 줄의 "
                        "「고르면」 꼴을 다음 부름에 그대로 준다(주소를 옮겨 적지 않는다):"
                        + bullets(homonym_lines(run, base, live), more="부서 · 직급을 대며 묻는다")))
        elif same:
            out.append((field, handle, None, f"「{handle}」 — 퇴직한 사람이다:" + bullets([person_line(p) for p in same])))
        else:
            near = [person_line(p) for p in every if not p.retired]
            out.append((field, handle, None, f"못 찾은 이름 「{handle}」 — 주소록에 그 이름 · 주소 · 사번이 꼭 같은 사람이 없다"
                        + (" · 그 글자가 든 사람:" + bullets(near, more="더 길게 주어 좁힌다") if near else "")))
    return [(f, h, p, Ask(why) if p is None else why) for f, h, p, why in out]


def name_picks(run, asks) -> tuple[list, list]:
    """``resolve`` 의 줄 → (받는 사람이 될 사람, 따로 둘 줄). 주소 · Notes 이름이 없는 사람은 받는 사람으로 못 넣어 따로 둔다."""
    picks, held = [], []
    for field, handle, p, why in resolve(run, asks):
        if p is not None and p.email and p.notes:
            picks.append(Pick(field, person=p))
        elif p is not None:
            held.append(Ask(f"「{handle}」 — 주소록의 그 사람에게 메일 주소 · Notes 이름이 없어 받는 사람으로 못 넣는다: {person_line(p)}"))
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


def group_lists(box, company: str, wants) -> dict:
    """찾을 그룹들(``wants`` — (칸, 갈래들, 이름))이 걸친 갈래마다의 배포그룹 목록 — 갈래 → [(열쇠, 이름)]. 함께 묻는다."""
    kinds = sorted({k for _, ks, _ in wants for k in ks})
    with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
        return dict(zip(kinds, pool.map(lambda k: box.org_groups(company, k), kinds)))


def one_group(lists: dict, kinds: tuple, name: str) -> tuple[str, str, str] | str:
    """갈래들(``kinds``)의 목록에서 이름이 같은 배포그룹 하나 — (갈래, 열쇠, 이름). 꼭 하나로 안 서면 그 까닭 글을 낸다. 이름이 꼭
    같은 것이 먼저고, 없으면 빈칸 · 괄호를 안 보고(``inbox.squash``) 견준다. 찾기의 ``--group`` 과 메일 draft 의 ``--to-group`` 이 이
    한 자를 쓴다."""
    hits = ([(k, key, n) for k in kinds for key, n in lists[k] if n.strip() == name]
            or [(k, key, n) for k in kinds for key, n in lists[k] if inbox.squash(n) == inbox.squash(name)])
    hits = list({key: (k, key, n) for k, key, n in hits}.values())   # 그룹은 열쇠가 하나다 — 갈래마다 같은 열쇠로 오면 한 그룹이다
    if not hits:
        return f"없는 배포그룹 「{name}」 — 갈래마다의 목록은 --groups"
    if len(hits) > 1:
        return (f"배포그룹 「{name}」 이 {' · '.join(GROUP_KIND_WORDS[k] for k, _, _ in hits)} 갈래에 다 있다 — 고르지 않는다. "
                f"「{GROUP_KIND_WORDS[hits[0][0]]}:{name}」 꼴로 갈래를 붙여 다시 준다")
    return hits[0]


def from_groups(run, values) -> list:
    """배포그룹의 구성원 — 갈래(직책 · 직급 · 지역)마다의 목록에서 이름이 같은 그룹 하나를 찾아 구성원을 받고, 구성원은 주소로 주소록의
    한 사람에 잇는다(그래야 거르기가 직책 · 등급까지 걸리고 draft 가 그 주소를 받는다). 그룹 자체를 한 받는 사람으로 넣지 않는다."""
    wants = [(field, *split_kind(rest)) for field, rest in (split_field(v) for v in values)]
    box = run.box
    lists = group_lists(box, run.company, wants)
    out, found = [], []
    for field, ks, name in wants:
        hit = one_group(lists, ks, name)
        if isinstance(hit, str):
            out.append(Haul(f"배포그룹 「{name}」(못 섰다)", [], [hit]))
            continue
        kind, key, title = hit
        found.append((field, kind, title, box.group_members(key)))
    people = run.people_of([m[3].strip() for *_, members in found for m in members if m[3].strip()])
    for field, kind, title, members in found:
        picks, lost = [], []
        for name, grade, dept, email in members:
            p = people.get(email.strip()) if email.strip() else None
            if p is None:
                lost.append(" · ".join(x for x in (name, dept, grade, email) if x))
            else:
                picks.append(Pick(field, person=p))
        held = [f"배포그룹 「{title}」 구성원 가운데 주소록에서 한 사람으로 안 선 {len(lost)} 명(주소 없음 · 퇴직 · 주소록에 없음) — "
                "웹메일에서 본다:" + bullets(lost)] if lost else []
        out.append(Haul(f"배포그룹 {GROUP_KIND_WORDS[kind]} 「{title}」 {len(members)} 명", picks, held))
    return out


def owner_person(run):
    """쓰는 사람(이 메일함의 주인) — 메일함 파일 번호가 사번이라(``MAILFILE_NUMBER``) 주소록에 그 사번으로 묻는다. 꼭 한 사람이 아니면 None."""
    box = run.box                                   # 메일함을 열어야 그 주소(args.mailbox_url)가 선다
    number = MAILFILE_NUMBER.search(getattr(run.args, "mailbox_url", "") or "")
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
    """사람을 든 파일 하나 → (칸, 이름 · 주소 · 사번 · Notes 이름) 여럿. 값 앞의 칸 머리(``forced``)가 있으면 모두 그 칸이다.

    JSON 은 세 꼴만 읽는다 — 사람 파일(``people`` 목록 · 사람마다 ``field`` 의 칸으로), 손의 답에서 가장 얕은 자리의 ``attendees`` 목록
    (회의실 미리 보기의 새 참석자 · 일정 한 건의 참석자 — 더 깊은 ``was`` · ``body`` 의 옛 참석자 · ``leaving`` · ``references`` 는 안
    든다), 맨 위 목록(이름 글자 · ``email`` 객체). 글 파일은 한 줄에 하나(``#`` 뒤는 버린다)."""
    try:
        text = ep_command.text_file(name, "--from-file 의 파일")
    except ep_command.Stop as exc:
        raise Stop(exc.code, str(exc)) from exc
    if text.lstrip()[:1] in ("{", "["):
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise Stop(EXIT_ARGS, f"--from-file 의 JSON 을 못 읽었다: {name} ({exc})") from exc

        def one(x) -> tuple[str | None, str] | None:
            if isinstance(x, str) and x.strip():
                return None, x.strip()
            if isinstance(x, dict) and isinstance(x.get("email"), str) and "@" in x["email"]:
                return (x.get("field") if x.get("field") in FIELD_WORDS else None), x["email"].strip()
            return None

        if isinstance(data, dict) and isinstance(data.get("people"), list):
            rows = data["people"]
        elif isinstance(data, list) and any(one(x) for x in data):
            rows = data
        else:
            rows, level = [], [data]
            while level and not rows:          # 가장 얕은 자리의 attendees 목록들 — 한 깊이에서 찾으면 더 안 내려간다
                rows = [x for node in level if isinstance(node, dict) and isinstance(node.get("attendees"), list) for x in node["attendees"]]
                level = [v for node in level for v in (node.values() if isinstance(node, dict) else node if isinstance(node, list) else ())]
        found = [h for h in map(one, rows) if h is not None]
        if not found:
            raise Stop(EXIT_ARGS, f"--from-file 의 JSON 에 사람이 없다: {name} — 사람 파일(people) · 손의 답(attendees 줄) · 이름 목록을 준다")
    else:
        found = [(None, line.split(FILE_COMMENT, 1)[0].strip()) for line in text.splitlines()]
        found = [x for x in found if x[1]]
    return [(forced or field or "to", handle) for field, handle in found]


def from_files(run, values) -> list:
    """다른 손이 낸 사람(일정의 참석자 · 메일의 받는 사람 · 회의실 예약의 참석자 · 앞서 쓴 사람 파일)에서 — 주소는 받아 둔 조직도 ·
    주소록으로 잇고(``people_of``), 이름 · 사번 · Notes 이름은 주소록에 묻는다(``resolve``). 한 사람으로 안 선 것은 따로 둔다."""
    out = []
    for v in values:
        forced, name = split_field(v, None)
        asks = file_handles(name, forced)
        mails = [(f, h) for f, h in asks if "@" in h]
        people = run.people_of([h for _, h in mails]) if mails else {}
        picks, held = name_picks(run, [(f, h) for f, h in asks if "@" not in h])
        lost = []
        for field, handle in mails:
            p = people.get(handle)
            if p is None:
                lost.append(handle)
            else:
                picks.append(Pick(field, person=p))
        if lost:
            held.append(f"파일 {pathlib.Path(name).name} 의 주소 가운데 주소록에서 한 사람으로 안 선 {len(lost)} — 사외 주소 · 부서 주소 · "
                        "틀린 주소다:" + bullets(lost))
        out.append(Haul(f"파일 {pathlib.Path(name).name} {len(asks)} 개(선 사람 {len(picks)})", picks, held))
    return out


def show_tree(run, words: str) -> None:
    """부서 나무 — 부서마다 인원(하위 조직까지 · 바로 든 사람)과 부서 주소. 부서를 주면 그 아래만, 안 주면 회사 전체."""
    chart, when = run.chart()
    code = None
    if words:
        d, why = one_dept(chart, words)
        if d is None:
            raise Stop(EXIT_ARGS, why)
        code = d.code
    print(f"{' > '.join(x.name for x in chart.path(code)) if code else f'회사 전체({run.company})'} — 조직도 {when} 판")
    top = chart.depts[code].depth if code else 1
    for root in (chart.subtree(code) if code else [d for d in chart.depts.values() if d.parent == run.company]):
        for x in (chart.subtree(root.code) if code is None else [root]):
            print(f"{'  ' * (x.depth - top)}- {x.name} · {len(chart.people(x.code))} 명"
                  f"(바로 {len(chart.members.get(x.code, []))}) · {x.email}")
    print("— 부서원은 --dept <부서>(하위 조직까지는 --sub), 조직 하나로 보내려면 --org <부서>")


def show_groups(run, kind: str) -> None:
    """배포그룹 목록 — 갈래를 주면 그 갈래만, 안 주면 셋 다."""
    kinds, _ = split_kind(f"{kind}:") if kind else (tuple(GROUP_KIND_WORDS), "")
    if kind and len(kinds) != 1:
        raise Stop(EXIT_ARGS, f"배포그룹 갈래는 {' · '.join(f'{k}({w})' for k, w in GROUP_KIND_WORDS.items())} 가운데 하나다: {kind!r}")
    box = run.box
    with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
        lists = list(pool.map(lambda k: box.org_groups(run.company, k), kinds))
    for k, groups in zip(kinds, lists):
        print(f"배포그룹 — {GROUP_KIND_WORDS[k]} {len(groups)} 개")
        for _, name in groups:
            print(f"- {name}")
    print("— 구성원은 --group <이름>(갈래가 겹치면 「직책:<이름>」)")


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


def match_keys(words) -> list[str]:
    return [k for k in (inbox.squash(w) for w in words or ()) if k]


SUB = ("sub", "하위 조직의 사람까지 — 사람이 「하위 조직까지 · 산하 전체」라고 할 때만")
# 찾기의 손가락 — 출처 아무 조합(합친다) × 거르기 아무 조합(합친 명단 전체에) → 표와 칸마다 주소 파일 · 사람 파일. 출처 · 거르기를 더하거나
# 빼는 일은 이 표의 줄과 그 일을 하는 손 하나다. 인자 · 거름 · --help 의 지도가 다 이 표에서 선다. 불러 쓰는 명령은 이 표에 제 출처를 더한다
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
                        "건 · 회의실 미리 보기) · 이름 목록 · 한 줄에 이름이나 주소 하나인 글 파일(# 뒤는 버린다)", True, from_files),
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
    return "--" + dest.replace("_", "-")


def given_of(args, table: dict) -> list[str]:
    """그 표에서 값이 든 줄 — 켜기는 참, 값은 빈 것이 아닐 때."""
    return [k for k in table if getattr(args, k, None) not in (None, [], False, "")]


def view_of(args) -> list[str]:
    """준 보기 — 보기는 값 없이도(빈 글자) 준 것이다."""
    return [k for k in VIEWS if getattr(args, k, None) is not None]


def asks_box(args, sources: dict = SOURCES) -> bool:
    """이 판이 메일함(세션)에 묻나 — 준 출처 · 보기 가운데 하나라도 메일함에 묻거나, 조직도를 새로 받거나, 전화를 물을 때. 거짓이면
    받아 둔 조직도로 선다."""
    return bool(getattr(args, "fresh", False) or getattr(args, "phone", False)
                or any(sources[k].box for k in given_of(args, sources))
                or any(VIEWS[k].box for k in view_of(args)))


def check_args(args, sources: dict = SOURCES) -> None:
    """출처 · 거르기 · 보기가 표에 맞나 — 세션 · 메일함 · 조직도에 닿기 전에 가린다."""
    given, views = given_of(args, sources), view_of(args)
    narrowing = (given_of(args, SIEVES) + (["except"] if args.without else []) + (["out"] if args.out else [])
                 + (["phone"] if args.phone else []))
    if len(views) > 1:
        raise Stop(EXIT_ARGS, "보기(--tree · --groups)는 한 번에 하나다")
    if views and (given or narrowing):
        raise Stop(EXIT_ARGS, f"--{views[0]} 는 목록을 보이는 보기라 출처 · 거르기 · 빼기 · --out · --phone 과 함께 안 받는다 — 사람을 찾으려면 "
                              "--name · --dept 같은 출처만 준다")
    if not views and not given:
        raise Stop(EXIT_ARGS, "찾을 출처가 없다 — --help 의 지도에서 출처(" + " · ".join(flag_of(k) for k in sources) + ")를 하나 넘게 준다")
    for switch in {s.switch for s in sources.values() if s.switch}:
        takers = [k for k, s in sources.items() if s.switch == switch]
        if getattr(args, switch[0], False) and not set(takers) & set(given):
            raise Stop(EXIT_ARGS, f"{flag_of(switch[0])} 는 {' · '.join(flag_of(k) for k in takers)} 에 붙는다 — {switch[1]}")
    for v in getattr(args, "from_file", None) or ():
        path = pathlib.Path(split_field(v, None)[1]).expanduser()
        if not path.is_file():
            raise Stop(EXIT_ARGS, f"--from-file 의 파일이 없다: {path}")
    if args.at_least:
        try:
            inbox.level_at_least("", args.at_least)
        except inbox.MailboxConfigError as exc:
            raise Stop(EXIT_ARGS, f"--at-least — {exc}") from exc


def find_map(sources: dict = SOURCES) -> str:
    """--help 의 지도 — 출처 · 거르기 · 보기 표에서 짓는다."""
    def head(k, takes, metavar):
        return flag_of(k) + (f" <{metavar}>" if takes != "none" else "")
    lines = ["출처 — 한 부름에 아무 조합이나 준다(값은 여러 번). 값 앞에 cc: · bcc: 를 붙이면 그 칸으로, 없으면 받는 사람"]
    for k, s in sources.items():
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
              f"  --phone 이면 명단의 사람({PHONE_MOST} 명까지)마다 사규 앱의 사람 창에 사번으로 물어 회사 전화 · 휴대 전화를 줄에 단다(세션)"]
    return "\n".join(lines)


def add_find_args(q: argparse.ArgumentParser, sources: dict = SOURCES) -> None:
    """찾기의 인자를 단다 — 출처 · 거르기 · 보기 표와 내는 꼴의 인자. 불러 쓰는 명령(메일 who)도 이 자리로 단다."""
    switches = set()
    for k, s in sources.items():
        if s.takes == "none":
            q.add_argument(flag_of(k), dest=k, action="store_true", help=s.word)
        else:
            q.add_argument(flag_of(k), dest=k, action="append", metavar=s.metavar, help=s.word)
        if s.switch and s.switch[0] not in switches:
            switches.add(s.switch[0])
            takers = " · ".join(flag_of(x) for x, t in sources.items() if t.switch == s.switch)
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
    return picks, ([f"주소가 없어 받는 사람으로 못 넣는 {len(bare)}:" + bullets(bare)] if bare else [])


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
    held = [f"거르기가 못 거는 받는 사람 {len(unjudged)} — 조직 · 사외 주소는 직급 · 직책이 없어 파일에서 뺐다. 조직을 사람으로 풀어 "
            "거르려면 --dept <부서>:" + bullets([p.line() for p in unjudged])] if unjudged else []
    return kept, dropped, [s.said(v) for s, v in given], held


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
    """사람 파일(``PEOPLE_JSON``)의 한 사람 — ``PEOPLE_KEYS`` 의 칸을 다 든다. 모르는 값은 빈 글자다."""
    d = p.person
    return {"name": d.name.strip(), "email": d.email.strip(), "mail_id": d.email.strip().split("@", 1)[0], "empno": d.empno.strip(),
            "dept": d.dept.strip(), "dept_code": d.dept_code.strip(), "grade": d.grade.strip(), "job_title": d.job_title.strip(),
            "is_boss": bool(d.is_boss), "notes": d.notes.strip(), "field": p.field}


def write_people_json(folder: str, picks: list) -> tuple[pathlib.Path, int]:
    """기계가 읽는 사람 파일을 쓴다(``PEOPLE_JSON`` — UTF-8 · BOM 없이) — (경로, 사람 수). ``people.txt`` 와 같은 명단에서 뽑는다."""
    path = pathlib.Path(folder).expanduser().resolve() / PEOPLE_JSON
    rows = [person_record(p) for p in people_only(picks)]
    path.write_bytes(json.dumps({"format": PEOPLE_FORMAT, "people": rows}, ensure_ascii=False, indent=1).encode("utf-8"))
    return path, len(rows)


def phone_book(run, people: list) -> tuple[dict, str]:
    """사람마다 전화 — 사규 앱의 사람 창(형제 스킬 company-regulation 의 ``cbsop.App.person``)에 사번으로 묻는다. (주소 → 줄에 달 말, 따로
    댈 말). 사번이 없거나 창이 비면 그 말을 단다. 사규 앱이 안 받으면(앱 고장 · 그 앱만 세션을 안 받음) 찾은 명단은 그대로 내고 전화만
    못 물었다고 댄다 — 메일 서버의 주소록은 이미 답했으니 사람을 로그인으로 보낼 까닭이 아니다."""
    if len(people) > PHONE_MOST:
        return {}, f"전화는 {PHONE_MOST} 명까지만 묻는다 — 명단이 {len(people)} 명이다. 좁혀 다시 --phone"
    try:
        cbsop = ep_command.load("cbsop", REGULATION_SCRIPTS)
    except ep_command.Stop as exc:
        return {}, f"전화를 못 물었다 — {exc}"
    out, broke = {}, ""
    try:
        app = cbsop.App(run.args.session_file)
    except cbsop.AppError as exc:
        broke = str(exc)
    for p in people:
        if not p.empno.strip():
            out[p.email.casefold()] = "전화 — 주소록에 사번이 없다"
            continue
        if not broke:
            try:
                got = app.person(p.empno.strip())
            except cbsop.AppError as exc:      # 끊긴 세션 · 없는 세션 파일도 이 갈래다
                broke = str(exc)
        if broke:
            out[p.email.casefold()] = "전화 — 못 물었다(아래 ⚠)"
            continue
        if not got:
            out[p.email.casefold()] = "전화 — 사람 창이 비었다(퇴직이거나 사규 앱에 그 사번이 없다)"
            continue
        office, mobile = (got.get("officePhone") or "").strip(), (got.get("handpon") or "").strip()
        out[p.email.casefold()] = " · ".join(x for x in (f"회사 {office}" if office else "", f"휴대 {mobile}" if mobile else "") if x) \
            or "전화 — 사람 창에 번호가 없다"
    return out, (f"전화를 못 물었다(사규 앱 — {broke}) — 명단은 주소록의 것 그대로다. 사규 앱 화면에서 그 사람 이름을 눌러 본다" if broke else "")


def find(args, open_box, sources: dict = SOURCES, title: str = "사람 찾기") -> None:
    """사람을 찾는다 — 출처(``sources``) 아무 조합을 합치고 거르기(``SIEVES``)를 그 명단 전체에 건 뒤, 사람이 볼 수 · 표와 (``--out``
    이면) 칸마다 주소 파일 · 사람 파일을 낸다. 보기(``VIEWS``)는 사람 대신 목록을 낸다. 아무것도 안 바꾼다. 인자의 꼴은
    ``check_args`` 가 세션 앞에서 이미 봤다. ``args.session_file`` 이 이 판의 세션 파일이다(전화가 쓴다)."""
    run = Run(args, open_box)
    if views := view_of(args):
        VIEWS[views[0]].show(run, getattr(args, views[0]))
        return
    hauls = [h for k in given_of(args, sources) for h in sources[k].gather(run, getattr(args, k))]
    picks, bare = merge_picks(hauls)
    picks, gone = without_picks(picks, args.without)
    picks, dropped, sieved, unjudged = sieve_picks(args, picks)
    held = [x for h in hauls for x in h.held] + bare + unjudged
    show(run, title, hauls, picks, gone, dropped, sieved, held)


def show(run, title, hauls, picks, gone, dropped, sieved, held) -> None:
    """찾은 명단을 보이고 --out 이면 파일을 쓴다 — 수 · 등급별 · 직급별 · 직책별(많으면 부서별)은 늘, 명단은 SHOWN 까지(넘으면
    --list), 따로 둔 것은 늘 다 댄다."""
    args = run.args
    people = [p.person for p in picks if p.person is not None]
    fields = {f: sum(p.field == f for p in picks) for f in FIELD_WORDS}
    phones, phone_note = phone_book(run, people) if args.phone else ({}, "")
    print(title + (f" — 조직도 {run.when} 판" if run.when else ""))
    print("출처: " + " · ".join(h.said for h in hauls))
    if sieved:
        print(f"거르기: {' · '.join(sieved)} — 걸러 나간 사람 {dropped} 명")
    for p in gone:
        print(f"뺐다(--except): {p.line()}")
    counts = " · ".join(f"{FIELD_WORDS[f]} {n}" for f, n in fields.items() if n or f == "to")
    orgs, outside = sum(p.org for p in picks), sum(p.outside for p in picks)
    print(f"{counts} — 사람 {len(people)} 명" + (f" · 조직 {orgs}" if orgs else "") + (f" · 사외 {outside}" if outside else "")
          + " (같은 주소는 한 번 · 칸이 겹치면 앞 칸)")
    if people:
        print(f"등급별: {tally(people, 'level')}")
        print(f"직급별: {tally(people, 'grade')}")
        print(f"직책별: {tally(people, 'job_title')}")
    several = sum(n > 0 for n in fields.values()) > 1
    rows = [(f"[{FIELD_WORDS[p.field]}] " if several else "") + p.line()
            + (f" · {phones[p.mail.casefold()]}" if p.person is not None and p.mail.casefold() in phones else "") for p in picks]
    if len(rows) > SHOWN and not args.list and not args.start:
        branch = hauls[0].branch if len(hauls) == 1 else ()
        print("부서별: " + (by_branch(run.chart()[0], branch[0], run.company, people) if branch
                            else tally(people, "dept", TALLY_TOP)))
        print(f"명단은 {len(rows)} 줄이라 안 실었다 — 수를 묻는 물음은 위의 수로 답한다. 다음: 좁히려면 거르기(--grade · --title · "
              "--at-least · --match), 명단을 보려면 같은 명령에 --list")
    else:
        show_rows(rows, args.start)
    if phone_note:
        print(f"⚠ {phone_note}")
    if held:
        print(f"⚠ 따로 둔 것 {len(held)} — 파일에 안 넣었다. 고르지 말고 사람에게 묻고, 고른 것을 줄마다 댄 꼴로 다시 준다:")
        for line in held:
            print(f"  - {line}")
    if not args.out:
        print("— 받는 사람으로 쓰려면 같은 명령에 --out <저장소 밖 폴더> — 칸마다 주소 파일을 쓰고 draft 에 그대로 줄 인자를 댄다"
              "(주소를 옮겨 적지 않는다)")
        return
    if asks := [x for x in held if isinstance(x, Ask)]:
        raise Stop(EXIT_ARGS, HELD_STOP.format(n=len(asks)))   # 파일을 안 쓴다 — 앞 판이 쓴 파일도 그대로다(빼기가 안 선 판과 같다)
    head = f"{' · '.join(h.said for h in hauls)}" + (f" · 거르기 {' · '.join(sieved)}" if sieved else "") + (
        f" · 조직도 {run.when} 판" if run.when else "")
    try:
        written = write_who_files(args.out, picks, head)
        sheet, persons, kept_orgs, kept_outside = write_people_file(args.out, picks, head)
        records, _ = write_people_json(args.out, picks)
    except OSError as exc:
        raise Stop(EXIT_ARGS, f"--out 폴더에 주소 파일을 못 썼다({exc}) — 쓸 수 있는 저장소 밖 폴더를 준다") from exc
    if not written:
        print("— 파일에 넣을 받는 사람이 없다 — draft 인자를 안 낸다")
        return
    print("주소 파일: " + " · ".join(f"{FIELD_WORDS[f]} {n} 개 → {path}" for f, path, n in written))
    print("draft 에 그대로: " + " ".join(f'--{f}-file "{path}"' for f, path, _ in written))
    if outside:
        print(f"사외 주소 {outside} 개는 파일에 주석으로만 뒀다 — 저장한 뒤 웹메일에서 더하라고 이른다")
    print(f"사람 파일: {persons} 명 → {sheet} — 한 줄에 「이름/메일ID」(칸 셋을 합쳤다). 문서함(company-ecm) 권한에 그 파일을 그대로 준다")
    print(f"사람 파일(JSON): {persons} 명 → {records} — 일정 · 회의실 · 문서함에 --people-file \"{records}\" 로 그대로 준다"
          "(문서함 권한은 --people-as edit · copy · read 를 함께). 메일 저장은 위의 draft 인자다")
    if kept_orgs or kept_outside:
        print("사람 파일에 안 넣은 것 — "
              + " · ".join(x for x in (
                  f"조직 {len(kept_orgs)}({', '.join(p.name for p in kept_orgs)} — 메일 조직도의 부서 코드가 문서함의 것과 같은지 안 쟀다. "
                  "부서는 문서함 쪽에서 부서 이름으로 준다)" if kept_orgs else "",
                  f"사외 주소 {len(kept_outside)}({', '.join(p.mail for p in kept_outside)} — 한 사람의 이름/메일ID 로 안 선다)"
                  if kept_outside else "") if x))


# ── 명령 ─────────────────────────────────────────────────────────────────

NOT_DONE = (
    ("주소록 · 조직도 고치기", "인사 시스템이 한다 — 이 손은 읽기만 한다"),
    ("동명이인 · 여럿 걸린 부서 가운데 고르기", "사람이 고른다 — 손은 후보를 대고 파일에 안 넣는다"),
    ("일정함을 공유하지 않은 사람의 빈 때", "그 사람에게 묻는다 — 스킬 company-calendar 는 공유받은 일정함만 본다"),
)


def parser() -> argparse.ArgumentParser:
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
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.WARNING, format="경고: %(message)s")
    args = parser().parse_args(argv)
    try:
        check_args(args)                                 # 인자의 꼴 — 세션 · 메일함에 닿기 전에 멈춘다(종료 2)
        url = (args.url or os.environ.get("MAILBOX_URL", "")).strip()

        def open_box(a):
            return load_mail().open_mailbox(a, inbox)

        def once(file):
            args.session_file = file
            find(args, open_box)

        try:
            if not asks_box(args) and cached_org(company_of(args)):
                once(None)                               # 받아 둔 조직도로 선다 — 세션 파일이 없어도 답한다
            else:
                ep_session.session_first(once, expired=(inbox.SessionExpired,), env={"MAILBOX_URL": url} if url else None)
        except ep_session.NoSession as exc:
            why = ep_command.no_session(exc.got)
            raise Stop(why.code, str(why)) from exc
        except inbox.SessionExpired as exc:
            raise Stop(EXIT_SESSION, f"메일 서버 세션이 끊겼다({exc}). {ep_command.NEXT_EP_LOGIN}") from exc
        except inbox.ChangeRefused as exc:
            raise Stop(EXIT_TOOL, f"메일함을 바꿀 주소라 묻지 않았다(inbox.py 의 막기): {exc}") from exc
        except inbox.MailboxConfigError as exc:
            raise Stop(EXIT_ARGS, str(exc)) from exc
        except inbox.MailboxError as exc:
            raise Stop(EXIT_TOOL, f"주소록 · 조직도에서 못 받았다: {exc}") from exc
    except Stop as stop:
        print(stop.said())
        return stop.code
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
