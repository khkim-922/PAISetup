"""받는 사람 잇기 — 주소를 주소록의 꼭 한 사람으로 잇는 자 · 배포그룹 하나 고르기 · 사람 한 줄의 꼴과 받는 사람 칸의 이름.

부르는 꼴::

    import mail_people
    book, when = mail_people.kept_book(company)                        # 받아 둔 조직도의 주소 → 사람들 · 그 판의 날짜
    found = mail_people.address_people(box, mails, company, book)      # 주소 → 그 한 사람 또는 None
    mail_people.can_receive(person)                                    # 주소록의 한 사람이 받는 사람으로 서나
    lists = mail_people.group_lists(box, company, wants)               # 갈래마다의 배포그룹 목록
    hit = mail_people.one_group(lists, kinds, name, missing_next=" — …")   # (갈래, 열쇠, 이름) 또는 못 선 까닭 글

이 스킬의 임시메일(받는 사람 칸 · 배포그룹 칸)과 형제 스킬 company-directory 의 찾기가 이 한 자를 쓴다 — 찾기가 파일에 넣은 주소를
저장이 다른 사람으로 세우지 않고, 찾기의 ``--group`` 과 저장의 ``--to-group`` 이 같은 그룹을 고른다. 웹메일 화면은 받는 사람을 Notes
이름으로 다시 연다 — 그래서 주소록에 없는 주소(사외 · 부서 주소)는 사람으로 안 선다.
"""

from __future__ import annotations

import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
for _where in (HERE, EP_LOGIN_SCRIPTS):
    if str(_where) not in sys.path:
        sys.path.insert(0, str(_where))             # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
import inbox  # noqa: E402 — 자리를 넣은 뒤에 싣는다
import mail_kept  # noqa: E402
from ep_command import PEOPLE_FIELDS  # noqa: E402

SHOWN = 40                    # 명단에서 이름을 보이는 수 — 넘으면 수만 댄다(명단은 --list · 파일). 받는 사람 한 칸 · 함께 받은 사람도 같은 수다
# 받는 사람 칸 → 사람 말 — 칸 값과 그 차례는 사람 파일의 꼴을 든 한 자리(형제 스킬 ep-login 의 PEOPLE_FIELDS)가 든다
FIELD_WORDS = dict(zip(PEOPLE_FIELDS, ("받는 사람", "참조", "숨은참조"), strict=True))
GROUP_KIND_WORDS = {"jobtitle": "직책", "grade": "직급", "location": "지역"}   # 배포그룹 갈래 → 화면의 이름
DEPT_WORD = "(조직)"          # 사람이 아니라 조직 하나일 때 이름 뒤에 붙이는 표지
DRAFT_AS_IS = "draft 에 그대로:"   # 주소록 찾기(--out)의 끝 줄 머리 — 그 뒤가 임시메일 짓기(draft)에 그대로 줄 주소 파일 인자다
NO_GROUP = "없는 배포그룹 「{name}」"   # 사실만 — 갈래마다의 목록을 어디서 보나는 부르는 명령이 제 걸음으로 붙인다(one_group 의 missing_next)
MANY_GROUPS = "배포그룹 「{name}」 이 {kinds} 갈래에 다 있다 — 고르지 않는다. 「{first}:{name}」 꼴로 갈래를 붙여 다시 준다"


def person_line(p, dept: bool = True) -> str:
    """사람 한 줄 — 이름 · 부서 · 직급(인사 등급) · 직책 · 장 · 근무지 · 담당 업무 · 주소. ``dept`` 가 거짓이면 부서를 뺀다."""
    marks = [m for m, on in (("장", p.is_boss), ("퇴직", p.retired)) if on]
    grade = f"{p.grade}({p.level})" if p.grade and p.level else p.grade
    return " · ".join(x for x in (p.name, p.dept if dept else "", grade, p.job_title, *marks, p.location, p.duty, p.email) if x)


def can_receive(p) -> bool:
    """주소록의 한 사람이 받는 사람으로 서나 — 메일 주소와 Notes 이름이 다 있어야 한다(웹메일 화면은 받는 사람을 Notes 이름으로 다시 연다)."""
    return bool(p.email and p.notes)


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
    got = mail_kept.cached_org(company)
    return (chart_book(got[0]), got[1]) if got else ({}, "")


def address_people(box, mails: list[str], company: str, book: dict) -> dict:
    """주소 → 그 주소의 주소록 사람(퇴직자 빼고)이 꼭 하나이고 받는 사람으로 서면(``can_receive``) 그 사람, 아니면 None.

    받아 둔 조직도(``book``)에 있는 주소는 거기서 잇고, 없는 주소만 주소록에 함께(``inbox.ORG_WORKERS`` 만큼) 묻는다 — 그때만
    ``box`` 가 쓰인다.
    """
    def ask(a: str) -> list:
        return [p for p in box.find_exact(a, company) if p.email.casefold() == a.casefold() and not p.retired]
    unknown = list(dict.fromkeys(a for a in mails if a.casefold() not in book))
    with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
        asked = dict(zip(unknown, pool.map(ask, unknown)))
    found = {}
    for a in mails:
        people = book.get(a.casefold()) or asked.get(a, [])
        found[a] = people[0] if len(people) == 1 and can_receive(people[0]) else None
    return found


def split_kind(value: str) -> tuple[tuple, str]:
    """배포그룹 값 앞의 갈래 머리(``직책:`` · ``jobtitle:`` …)를 뗀다 — (찾을 갈래들, 그룹 이름). 머리가 없으면 갈래 셋 다다."""
    head, sep, rest = value.partition(":")
    names = {**{k: k for k in GROUP_KIND_WORDS}, **{w: k for k, w in GROUP_KIND_WORDS.items()}}
    kind = names.get(head.strip().lower()) if sep else None
    return ((kind,), rest.strip()) if kind else (tuple(GROUP_KIND_WORDS), value.strip())


def group_lists(box, company: str, wants) -> dict:
    """찾을 그룹들(``wants`` — (칸, 갈래들, 이름))이 걸친 갈래마다의 배포그룹 목록 — 갈래 → [(열쇠, 이름)]. 함께 묻는다."""
    kinds = sorted({k for _, ks, _ in wants for k in ks})
    with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
        return dict(zip(kinds, pool.map(lambda k: box.org_groups(company, k), kinds)))


def one_group(lists: dict, kinds: tuple, name: str, *, missing_next: str) -> tuple[str, str, str] | str:
    """갈래들(``kinds``)의 목록에서 이름이 같은 배포그룹 하나 — (갈래, 열쇠, 이름)(``group_hits``). 꼭 하나로 안 서면 그 까닭 글을
    낸다(``group_miss``). ``missing_next`` 는 어느 갈래에도 없을 때 부르는 명령이 사실 뒤에 붙이는 제 걸음이다(「 — 」 부터)."""
    hits = group_hits(lists, kinds, name)
    return hits[0] if len(hits) == 1 else group_miss(name, [k for k, _, _ in hits], missing_next)


def group_hits(lists: dict, kinds: tuple, name: str) -> list[tuple[str, str, str]]:
    """갈래들(``kinds``)의 목록에서 이름이 같은 배포그룹들 — [(갈래, 열쇠, 이름)]. 이름이 꼭 같은 것이 먼저고, 없으면 빈칸 · 괄호를
    안 보고(``inbox.squash``) 견준다. 갈래마다 같은 열쇠로 온 줄은 한 그룹이다."""
    hits = ([(k, key, n) for k in kinds for key, n in lists[k] if n.strip() == name]
            or [(k, key, n) for k in kinds for key, n in lists[k] if inbox.squash(n) == inbox.squash(name)])
    return list({key: (k, key, n) for k, key, n in hits}.values())   # 그룹은 열쇠가 하나다


def group_miss(name: str, kinds: list[str], missing_next: str) -> str:
    """배포그룹 하나로 안 선 까닭 — 걸린 갈래(``kinds``)가 없으면 「없다」에 부르는 쪽의 걸음(``missing_next``)을, 여럿이면 갈래를 붙여
    다시 달라고 한다."""
    if not kinds:
        return NO_GROUP.format(name=name) + missing_next
    return MANY_GROUPS.format(name=name, kinds=" · ".join(GROUP_KIND_WORDS[k] for k in kinds), first=GROUP_KIND_WORDS[kinds[0]])
