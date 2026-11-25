"""보낸 사람 신원 — 주소 하나 → 그 사람의 신원 한 줄(이름 · 회사 · 부서 경로 · 직급 · 직책 · 장 · 사번 · 근무지 · 담당업무)을 코드가 짓는 손.

부르는 꼴::

    python -X utf8 -I identity.py lookup [--most N] < 주소들(한 줄에 하나)   # 신원 JSON 한 장을 표준 출력에 — 사람 없이 도는 쪽(스캔)이 부른다
    python -X utf8 -I identity.py show <주소> …                                          # 사람이 읽을 한 줄씩
    python -X utf8 -I identity.py pull [--unattended]                        # 미리 받을 조직도 가운데 낡은 것을 받는다(사람 없이는 한 번에 한 회사)

무엇을 하나
    신원 표의 주인은 이 스킬이다 — 메일함 스캔 · 다른 스킬은 이 명령이 낸 신원만 싣는다. 찾는 차례는 받아 둔 조직도(나의 회사 · 포스코홀딩스 ·
    포스코 — 사람까지 받은 판) → 이 표(주소마다 앞서 지은 신원 · ``TABLE_DAYS`` 안) → 주소록 찾기(고름 넷을 ``BRANCHES`` 차례로 — 처음 걸린 데서
    멈춘다)다. 부서 경로는 그 회사의 부서 나무(미리 그려 두는 것)에서 짓고, 찾은 사람의 부서가 그 나무에 없으면 그 회사 나무만 다시 받는다.
    한 주소에 사람이 여럿이면 고르지 않고 「여럿」 · 후보 수로 둔다. 서버에 묻는 주소의 수는 한 번에 ``--most`` 까지 — 나머지와 묻다 못 받은
    주소는 「모름」 으로 내고 다음 부름이 다시 묻는다(표에 안 남긴다).

내는 것 — ``lookup`` 은 ``{"format", "session", "asked", "people": {주소(소문자): 신원}}``. 신원의 칸은 ``FIELDS`` 의 주석이 든다.
종료 값 — 0 냈다 · 1 ``pull`` 이 회사 하나를 못 받았다(받은 것은 받았다) · 2 인자가 틀렸다 · 3 사내 세션이 없다 · 끊겼다(그때도 ``lookup`` 은 표로 선 신원을 다 내고 나머지는 「모름」 이다).
``lookup`` 은 세션 파일을 있는 그대로만 쓴다(로그인 손을 안 띄운다) — 사람 없이 도는 쪽이 부르는 문이다. ``show`` · ``pull`` 은 대화에서
부르는 문이라 세션이 끊겼으면 다른 사내 앱 명령처럼 다시 받는다.
읽기만 한다 — 주소록 · 메일함을 안 바꾸고, 사람찾기의 보내기 · 문자 · 알림 주소를 안 부른다. 전화 · 휴대 전화 · 사진은 어디에도 안 쓴다.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
for _where in (SKILLS / "ep-login" / "scripts", SKILLS / "company-mail" / "scripts", HERE):
    if str(_where) not in sys.path:
        sys.path.insert(0, str(_where))               # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
import ep_command  # noqa: E402
import ep_session  # noqa: E402
import inbox  # noqa: E402
from mail_kept import cache_dir, cached_org, company_of, load_org, tree_newer  # noqa: E402
from mail_open import open_mailbox  # noqa: E402
from mail_stop import Stop  # noqa: E402
import findpeople  # noqa: E402

EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION = ep_command.EXIT_OK, ep_command.EXIT_TOOL, ep_command.EXIT_ARGS, ep_command.EXIT_SESSION
IDENTITY_FORMAT = 1            # 신원 JSON(``lookup`` 의 답)과 표 파일의 꼴 번호 — 칸의 이름이나 뜻을 바꾸면 올린다(읽는 쪽이 모르는 꼴을 안 읽게)
TABLE_FILE = "identity.json"   # 이 표의 자리 — 받아 둔 조직도와 같은 사용자 자리(``mail_kept.cache_dir``)
PULL_TRIED_FILE = "identity-pull.json"   # 미리 받다 진 회사와 그 때 — 다음 받기가 그 회사를 뒤로 민다
TOPS_FILE = "org-tops-{tree}.json"   # 고름 하나의 맨 위 회사들(회사 코드 → 나무의 회사 값) — 그룹사 사람의 나무를 고르는 표
TABLE_DAYS = 7                 # 표의 신원 · 미리 받은 조직도를 다시 묻지 않고 쓰는 날 — 부서는 개편 때나 바뀌고, 사람의 자리는 한 주면 다시 본다
LOOKUP_MOST = 20               # 한 부름이 서버에 묻는 주소의 위 — 주소 하나에 고름 넷까지(0.2 초씩) · 담당업무 채우기 한 번(0.6 초). 스캔 한 판이
                               # 몇 초 안에 끝나게 하고, 처음 쌓을 때 몰린 주소는 다음 판들이 나눠 묻는다
LOOKUP_WORKERS = 4             # 주소를 함께 묻는 수 — 사람이 웹메일을 여는 정도의 부담을 넘지 않게 조직도 손(``inbox.ORG_WORKERS``)보다 적게
PULL_UNATTENDED_MOST = 1       # 사람 없이 도는 ``pull`` 한 번이 받는 회사의 수 — 가장 큰 포스코 한 회사가 1 분 안쪽이라, 스캔 한 판이 한 회사 값만 더 쓴다

# D1 고름 표 — 고름 넷이 같은 손가락을 쓴다. 차례가 주소록 찾기의 차례다(처음 걸린 데서 멈춘다)
@dataclasses.dataclass(frozen=True)
class Branch:
    """고름 하나 — 사람 말 · 조직도와 주소록 찾기의 type · 무엇을 미리 받나(``people`` 사람까지 · ``tree`` 부서 나무만 · ``none`` 안 받는다)."""
    word: str
    tree: str
    ahead: str


OWN, GROUP, PARTNER, OTHER = "나의 회사", "그룹사", "협력사", "기타공급사"
BRANCHES = (Branch(OWN, inbox.ORG_TREE_TYPE, "people"), Branch(GROUP, "org_family", "tree"),
            Branch(PARTNER, "partner", "none"), Branch(OTHER, "etc", "none"))
GROUP_FULL = ("poscoinc(77)", "posco(30)")   # 그룹사 가운데 사람까지 받는 회사(나무의 회사 값) — 포스코홀딩스 · 포스코(사용자가 정했다)

# 신원 한 줄의 상태 — 섰다 · 한 주소에 사람이 여럿 · 고름 넷 어디에도 없다 · 아직 모른다(못 물었다 — 다음 부름이 다시 묻는다)
FOUND, SEVERAL, ABSENT, UNKNOWN = "섰다", "여럿", "없음", "모름"
DUTY_MAIL, DUTY_FINDER = "메일", "사람찾기"   # 담당업무의 출처 — 사람이 적은 글이라 낡았을 수 있다
PATH_SEP = " › "
# 신원의 칸 — 상태가 「섰다」 일 때 찬다. 협력사 · 기타공급사는 주소록 찾기가 열 칸만 줘서 ``blank`` 의 칸이 빈다(비었다는 사실이다)
FIELDS = ("name", "name_eng", "company", "company_code", "branch", "dept", "dept_code", "path", "grade", "grade_code", "level",
          "job_title", "job_title_code", "is_boss", "empno", "retired", "location", "duty", "duty_from")
ADDR_BLANK = ("name_eng", "grade", "grade_code", "level", "job_title", "job_title_code", "is_boss", "location", "duty", "dept_code")


# ── 표 — 주소마다 앞서 지은 신원(사용자 자리) ─────────────────────────────────────────

def table_path() -> pathlib.Path:
    """이 표의 파일 — 받아 둔 조직도와 같은 사용자 자리."""
    return cache_dir() / TABLE_FILE


def read_table() -> tuple[dict, dict]:
    """(주소(소문자) → 앞서 지은 신원(지은 시각 ``at`` 을 든다), 나무 밖으로 확인한 부서 → 확인한 시각). ``TABLE_DAYS`` 를 넘은 부서는
    걷는다. 없거나 꼴이 다르거나 깨졌으면 빈 표 — 서버에서 다시 지으면 된다."""
    try:
        raw = json.loads(table_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, {}
    if not isinstance(raw, dict) or raw.get("format") != IDENTITY_FORMAT:
        return {}, {}
    people, outside = raw.get("people"), raw.get("outside")
    edge = time.time() - TABLE_DAYS * ep_command.DAY_SECONDS
    return (people if isinstance(people, dict) else {},
            {k: v for k, v in outside.items() if isinstance(v, (int, float)) and v > edge} if isinstance(outside, dict) else {})


def fresh_in(table: dict, addr: str, now: float) -> dict | None:
    """표의 그 주소 신원이 ``TABLE_DAYS`` 안에 지은 것이면 그것, 아니면 None."""
    got = table.get(addr)
    if not isinstance(got, dict) or got.get("duty_pending"):
        return None
    return got if now - float(got.get("at") or 0) < TABLE_DAYS * ep_command.DAY_SECONDS else None


def save_table(table: dict, outside: dict) -> str:
    """표를 남긴다 — 못 남긴 까닭(남겼으면 빈 글자). 못 남겨도 이 부름의 답은 그대로다(다음 부름이 다시 짓는다)."""
    return ep_command.keep(table_path(), {"format": IDENTITY_FORMAT, "people": table, "outside": outside})


# ── D4 신원 짓기 — 사람 줄 + 부서 나무 → 신원 한 줄(바깥 없음) ─────────────────────────────

def tree_code(p, chart) -> str:
    """사람의 부서를 그 회사 나무의 부서 코드로 — 조직도 줄은 이미 나무 꼴이고, 주소록 찾기 줄은 괄호 없는 코드라 회사 코드를 붙인다.
    나무에 없으면 빈 글자(나무가 낡았다)."""
    code = p.dept_code.strip()
    for c in (code, f"{code}({p.company_code})" if code and p.company_code else ""):
        if c and chart is not None and c in chart.depts:
            return c
    return ""


def dept_path(company: str, chart, code: str, dept: str) -> str:
    """회사 › 본부 › … › 부서 — 나무에서 그 부서까지의 길. 나무에 없으면 회사 › 부서 이름이다."""
    names = [d.name for d in chart.path(code)] if chart is not None and code else [dept]
    return PATH_SEP.join(x for x in (company, *names) if x)


def identity_of(p, branch: Branch, chart, own_code: str) -> dict:
    """사람 줄 하나 → 신원 한 줄(상태 「섰다」). 직급 등급은 나의 회사 코드표라 나의 회사 사람에게만 단다. 주소록 찾기가 열 칸만 준
    협력사 · 기타공급사 사람은 ``ADDR_BLANK`` 칸이 빈다."""
    code = tree_code(p, chart)
    out = {"state": FOUND, "name": p.name, "name_eng": p.name_eng, "company": p.company, "company_code": p.company_code,
           "branch": branch.word, "dept": p.dept, "dept_code": code or p.dept_code, "path": dept_path(p.company, chart, code, p.dept),
           "grade": p.grade, "grade_code": p.grade_code, "level": p.level if p.company_code == own_code else "",
           "job_title": p.job_title, "job_title_code": p.job_title_code, "is_boss": p.is_boss, "empno": p.empno,
           "retired": p.retired, "location": p.location, "duty": p.duty, "duty_from": DUTY_MAIL if p.duty else ""}
    if branch.ahead == "none":
        out.update(dict.fromkeys(ADDR_BLANK, ""), is_boss=False)
    return out


def several_of(people, branch: Branch) -> dict:
    """한 주소에 사람이 여럿 — 고르지 않고 후보 수와 그들의 회사만 단다."""
    return {"state": SEVERAL, "branch": branch.word, "candidates": len(people),
            "company": " · ".join(dict.fromkeys(p.company for p in people if p.company))}


def one_person(people) -> list:
    """같은 주소의 사람 줄 → 서로 다른 사람들 — 한 사람이 둘 넘는 부서에 든 줄은 (회사, 사번) 으로 한 번이다."""
    return list({(p.company_code or p.company, p.empno or p.notes or p.name): p for p in people}.values())


# ── D2 조직 받기 · D3 처음 보는 주소 찾기 — 한 부름의 메모리 ───────────────────────────────

class Book:
    """한 부름이 쥐는 것 — 메일함(처음 물을 때 연다) · 고름마다 맨 위 회사 · 받은 나무 · 사람찾기 앱 · 서버에 물은 주소 수.
    ``live`` 가 거짓이면(세션이 끊겼다) 더 묻지 않는다."""

    def __init__(self, session_file, most: int):
        self.session_file, self.most = session_file, most
        self.own = company_of("")
        self._box = self._finder = None
        self.tops: dict = {}
        self.charts: dict = {}
        self.renewed: set = set()
        self.asked = 0
        self.live = True
        self.finder_down = False         # 사람찾기에 못 들어갔다 — 이 부름에서는 다시 안 들어가 본다(주소마다 SSO 를 두드리지 않게)
        self.lock = threading.RLock()   # 주소를 함께 물을 때 나무 · 맨 위 회사 · 셈 · 메일함 · 앱을 한 번만 세운다

    @property
    def box(self):
        """이 부름의 메일함 — 처음 부를 때 세션으로 연다."""
        with self.lock:
            if self._box is None:
                self._box = open_mailbox("", self.session_file, inbox).box
            return self._box

    @property
    def finder(self):
        """이 부름의 사람찾기 앱 — 처음 부를 때 세운다(들어가기는 첫 찾기가 한다)."""
        with self.lock:
            if self._finder is None:
                self._finder = findpeople.App(self.session_file)
                self._finder.login()
            return self._finder

    def top_of(self, branch: Branch, company_code: str) -> str:
        """그 고름의 회사 코드 → 나무의 회사 값(``poscoinc(77)`` 꼴) — 나의 회사는 회사 값, 다른 고름은 맨 위 회사들(``tops_of``)에서."""
        if branch.tree == inbox.ORG_TREE_TYPE:
            return self.own
        with self.lock:
            if branch.tree not in self.tops:
                self.tops[branch.tree] = tops_of(self, branch.tree)
            return self.tops[branch.tree].get(company_code, "")

    def chart(self, tree: str, company: str, *, fresh: bool = False):
        """그 회사의 나무(OrgChart) — 받아 둔 판(사람까지든 나무만이든)이 ``TABLE_DAYS`` 안이면 그것, 아니면 부서 나무만 새로 받는다
        (한 회사 2 초 안쪽 — 사람까지 받기는 포스코 한 회사가 1 분이라 찾는 부름에서 안 한다). 나무만 받은 판은 사람까지의 판을 덮지 않는다
        (``mail_kept`` 의 곁 파일).
        ``fresh`` 면 이 부름에 한 번만 새로 받는다(찾은 사람의 부서가 나무에 없었다 — 나무가 낡았다)."""
        key = (tree, company)
        with self.lock:
            if fresh and key not in self.renewed:
                self.renewed.add(key)
                self.charts.pop(key, None)
            else:
                fresh = False
            if key not in self.charts:
                self.charts[key] = load_org(company, fresh, lambda: self.box, tree=tree, days=TABLE_DAYS, people=False)[0]
            return self.charts[key]

    def take(self) -> bool:
        """서버에 한 번 물을 몫을 쥔다 — 이 부름의 몫(``most``)이 남았으면 참."""
        with self.lock:
            if self.asked >= self.most:
                return False
            self.asked += 1
            return True


def tops_of(book: Book, tree: str) -> dict:
    """고름 하나의 맨 위 회사들 — 회사 코드(괄호 안) → 나무의 회사 값. ``TABLE_DAYS`` 동안 받아 둔 표를 쓴다."""
    path = cache_dir() / TOPS_FILE.format(tree=tree)
    got = ep_command.kept(path, IDENTITY_FORMAT, TABLE_DAYS, by_mtime=True)
    if got:
        return got[0]["tops"]
    tops = {d.code.rsplit("(", 1)[-1].rstrip(")"): d.code for d in book.box.org_children("/", book.own, tree) if "(" in d.code}
    ep_command.keep(path, {"format": IDENTITY_FORMAT, "tops": tops})
    return tops


def kept_index(book: Book) -> dict:
    """사람까지 받아 둔 조직도(나의 회사 · ``GROUP_FULL``)의 주소 → (고름, 사람들, 그 나무). 받아 둔 판만 본다 — 서버에 안 묻는다."""
    index: dict = {}
    for branch, company in ((BRANCHES[0], book.own), *((BRANCHES[1], c) for c in GROUP_FULL)):
        got = cached_org(company, tree=branch.tree, days=TABLE_DAYS)
        if not got:
            continue
        for p in got[0].people():
            if p.email:
                index.setdefault(p.email.strip().casefold(), (branch, [], got[0]))[1].append(p)
    return index


def ask_address(book: Book, addr: str) -> tuple:
    """주소 하나를 주소록 찾기에 고름 차례로 묻는다 — (고름, 그 주소가 꼭 같은 사람들). 어디에도 없으면 (None, [])."""
    for branch in BRANCHES:
        people = [p for p in book.box.find_people(addr, book.own, tree=branch.tree) if p.email.strip().casefold() == addr]
        if people:
            return branch, people
    return None, []


# ── D4 · D5 — 주소 하나의 신원을 짓는 손 ───────────────────────────────────────────

def code_of(value: str) -> str:
    """회사 값(``poscochem(02)``)의 회사 코드(``02``)."""
    return value.rsplit("(", 1)[-1].rstrip(")") if "(" in value else value


def chart_for(book: Book, branch: Branch, p, kept_chart=None):
    """그 사람의 부서 나무와 나무의 고름 — 사람까지 받아 둔 판에서 왔으면 그 판, 아니면 그 회사의 부서 나무(나의 회사 고름에서 걸린 다른
    회사 사람 — 파견 · 겸직 — 은 그룹사 나무). 나무를 못 고르면 (None, 고름)."""
    if kept_chart is not None:
        return kept_chart, branch.tree
    if branch.ahead == "none":
        return None, branch.tree
    tree = branch.tree if p.company_code == code_of(book.own) or branch.tree != inbox.ORG_TREE_TYPE else BRANCHES[1].tree
    top = book.own if tree == inbox.ORG_TREE_TYPE else book.top_of(BRANCHES[1], p.company_code)
    return (book.chart(tree, top) if top else None), tree


def with_tree(book: Book, branch: Branch, p, outside: dict, kept_chart=None) -> dict:
    """사람 줄 하나 → 신원 — 나무에서 경로를 짓고, 부서가 그 나무에 없으면 그 회사 나무만 한 번 다시 받아 짓는다(나무가 낡았다). 다시
    받은 나무에도 없는 부서는 나무 밖의 부서(파견 · 임시조직)다 — ``outside`` 에 적어 그 부서로는 ``TABLE_DAYS`` 동안 다시 안 받는다."""
    chart, tree = chart_for(book, branch, p, kept_chart)
    if chart is not None and p.dept_code and not tree_code(p, chart) and kept_chart is None:
        mark = f"{tree}|{chart.company}|{p.dept_code}"
        if mark not in outside:
            chart = book.chart(tree, chart.company, fresh=True)
            if not tree_code(p, chart):
                outside[mark] = time.time()
    return identity_of(p, branch, chart, code_of(book.own))


def with_duty(book: Book, got: dict, paid: bool) -> dict:
    """메일 쪽이 담당업무를 비운 사람만 사람찾기에서 채운다 — 메일 주소로 그 회사에서 찾아 같은 주소의 한 사람일 때만. 사람찾기의 회사
    값은 메일 나무의 회사 값 괄호 앞과 같다(나의 회사는 앱이 댄 값). 이 부름의 묻기 몫(``most``)이 다 찼으면 안 묻고 ``duty_pending`` 을
    달아 둔다 — 표가 그 신원을 다음 부름에 다시 짓는다. 주소록 찾기로 몫을 이미 쥔 주소(``paid``)는 그 몫으로 함께 묻는다. 앱이 못 답하면
    비운 그대로다(메일 쪽 신원은 섰다)."""
    if got["state"] != FOUND or got["duty"] or got["branch"] not in (OWN, GROUP):
        return got
    if book.finder_down or not (paid or book.take()):
        return {**got, "duty_pending": True}
    try:
        company = (book.finder.own if got["company_code"] == code_of(book.own)
                   else book.top_of(BRANCHES[1], got["company_code"]).split("(")[0])
        rows = [r for r in book.finder.search(findpeople.KINDS["메일"], got["addr"], company).rows
                if r.email.strip().casefold() == got["addr"] and r.duty.strip()] if company else []
    except findpeople.SessionExpired:
        book.finder_down = True
        return {**got, "duty_pending": True}    # 사람찾기만 못 들어갔다 — 메일 쪽 신원은 섰고, 담당업무는 다음 부름이 다시 묻는다
    except (findpeople.AppError, OSError):
        return got
    return {**got, "duty": rows[0].duty.strip(), "duty_from": DUTY_FINDER} if len(rows) == 1 else got


def build(book: Book, addr: str, index: dict, outside: dict) -> dict:
    """주소 하나 → 신원 — 사람까지 받아 둔 판(``index``)에 있으면 거기서, 없으면 주소록 찾기(``ask_address``)로. 퇴직 안 한 사람이
    있으면 그들만 본다. 여럿이면 「여럿」, 어디에도 없으면 「없음」."""
    branch, people, kept_chart = index.get(addr, (None, [], None))
    paid = not people
    if paid:
        branch, people = ask_address(book, addr)
    if branch is None:
        return {"state": ABSENT, "addr": addr}
    people = one_person([p for p in people if not p.retired] or people)
    if len(people) > 1:
        return {**several_of(people, branch), "addr": addr}
    return with_duty(book, {**with_tree(book, branch, people[0], outside, kept_chart), "addr": addr}, paid)


def identities(book: Book, addrs: list[str]) -> dict:
    """주소들 → {주소: 신원}. 표의 것은 그대로, 받아 둔 판에 있는 주소는 서버 없이, 그 밖의 주소는 ``book.most`` 까지만 묻고 나머지는
    「모름」. 세션이 끊기면 그 뒤는 다 「모름」 이고, 주소 하나가 못 받은 것은 그 주소만 「모름」 이다. 「모름」 은 표에 안 남긴다."""
    now, (table, outside) = time.time(), read_table()
    wanted = list(dict.fromkeys(a.strip().casefold() for a in addrs if "@" in a))
    index = kept_index(book) if any(fresh_in(table, a, now) is None for a in wanted) else {}
    out = {a: fresh_in(table, a, now) for a in wanted}
    todo = [a for a in wanted if out[a] is None and book.live and (a in index or book.take())]   # 찾기에 물을 주소만 몫을 쥔다

    def one(addr: str):
        """주소 하나 — 지은 신원, 못 지었으면 None(세션이 끊겼으면 그 뒤로 안 묻는다)."""
        if not book.live:
            return None
        try:
            return {**build(book, addr, index, outside), "at": now}
        except (inbox.SessionExpired, findpeople.SessionExpired, Stop):
            book.live = False
        except (inbox.MailboxError, findpeople.AppError, OSError, ValueError):
            pass
        return None
    with ThreadPoolExecutor(LOOKUP_WORKERS) as pool:
        for addr, got in zip(todo, pool.map(one, todo)):
            if got is not None:
                table[addr] = out[addr] = got
    out = {a: v or {"state": UNKNOWN, "addr": a} for a, v in out.items()}
    if any(v.get("at") == now for v in out.values()):
        save_table(table, outside)
    return out


# ── 미리 받기 — 사람까지 받는 회사 셋(``pull``) ──────────────────────────────────────

def ahead_list(book: Book) -> list[tuple[str, str]]:
    """사람까지 미리 받는 (고름 type, 나무의 회사 값) — 나의 회사와 ``GROUP_FULL``. 그 밖의 그룹사 나무는 처음 쓸 때 받는다(한 회사 1 초 안쪽)."""
    return [(inbox.ORG_TREE_TYPE, book.own), *((BRANCHES[1].tree, c) for c in GROUP_FULL)]


def stale_ahead(book: Book) -> list[tuple[str, str]]:
    """사람까지 미리 받는 판 가운데 ``TABLE_DAYS`` 를 넘었거나 없거나, 그 뒤에 부서 나무를 새로 받은 것(``tree_newer`` — 찾은 사람의 부서가
    나무에 없었다) — 서버에 안 묻는다. 앞서 받다 진 회사는 뒤로 민다(``PULL_TRIED_FILE``) — 한 회사가 늘 지면 뒤 회사가 영영 안 받힌다."""
    tried = ep_command.kept(cache_dir() / PULL_TRIED_FILE, IDENTITY_FORMAT, TABLE_DAYS, by_mtime=True)
    failed = (tried[0].get("failed") or {}) if tried else {}
    stale = [(t, c) for t, c in ahead_list(book) if not cached_org(c, tree=t, days=TABLE_DAYS) or tree_newer(c, t)]
    return sorted(stale, key=lambda tc: failed.get(f"{tc[0]}|{tc[1]}", 0))


def pull(book: Book, most: int | None = None) -> tuple[list, list]:
    """낡은 미리 받는 판(``stale_ahead``)을 받는다 — ``most`` 를 주면 그 수까지만(사람 없이 도는 판이 한 번에 한 회사씩 나눠 받는다). 회사
    하나가 지면(세션 밖의 메일 손 오류) 그 회사를 진 때와 함께 적고 다음 회사로 간다. 내는 것 — (받은 (고름, 회사 값), 진 (고름, 회사 값, 까닭))."""
    done, failed = [], []
    path = cache_dir() / PULL_TRIED_FILE
    tried = ep_command.kept(path, IDENTITY_FORMAT, TABLE_DAYS, by_mtime=True)
    marks = dict((tried[0].get("failed") or {}) if tried else {})
    for tree, company in stale_ahead(book)[:most]:
        try:
            load_org(company, True, lambda: book.box, tree=tree)
        except inbox.SessionExpired:
            raise
        except inbox.MailboxError as exc:
            failed.append((tree, company, str(exc)))
            marks[f"{tree}|{company}"] = time.time()
            continue
        marks.pop(f"{tree}|{company}", None)
        done.append((tree, company))
    ep_command.keep(path, {"format": IDENTITY_FORMAT, "failed": marks})
    return done, failed


# ── 사람이 읽는 줄 · 명령 ──────────────────────────────────────────────────────────

def identity_line(got: dict) -> str:
    """신원 한 줄 — 사람이 읽는 꼴. 담당업무는 출처를 단다."""
    state = got.get("state")
    if state == SEVERAL:
        return f"{got['addr']} — 여럿({got['candidates']} 명 · {got.get('company') or got.get('branch')}) — 고르지 않았다"
    if state != FOUND:
        return f"{got['addr']} — {state}"
    grade = f"{got['grade']}({got['level']})" if got.get("level") else got.get("grade")
    duty = f"담당 {got['duty']}({got['duty_from']})" if got.get("duty") else ""
    marks = [m for m, on in (("장", got.get("is_boss")), ("퇴직", got.get("retired"))) if on]
    return " · ".join(x for x in (got["addr"], got["name"], got["path"], grade, got.get("job_title"), *marks, got.get("location"), duty,
                                  got["branch"]) if x)


def read_addresses() -> list[str]:
    """표준 입력의 주소들 — 한 줄에 하나, 빈 줄 · # 뒤는 버린다."""
    return [line.split("#", 1)[0].strip() for line in sys.stdin.read().splitlines() if line.split("#", 1)[0].strip()]


def cmd_lookup(args) -> int:
    """lookup — 표준 입력의 주소들의 신원 JSON 한 장. 세션 파일은 있는 그대로만 쓴다(로그인 손을 안 띄운다)."""
    book = Book(ep_session.known_file(), args.most)
    book.live = book.session_file is not None
    people = identities(book, read_addresses())
    print(json.dumps({"format": IDENTITY_FORMAT, "session": book.live, "asked": book.asked, "people": people}, ensure_ascii=False))
    return EXIT_OK if book.live or all(v["state"] != UNKNOWN for v in people.values()) else EXIT_SESSION


def cmd_show(args) -> int:
    """show — 준 주소들의 신원을 한 줄씩. 세션이 끊겼으면 다시 받는다."""
    def once(session_file):
        book = Book(session_file, args.most)
        got = identities(book, args.addr)
        if not book.live:
            raise inbox.SessionExpired("사내 세션이 끊겼다")
        for v in got.values():
            print(identity_line(v))
    ep_session.session_first(once, expired=(inbox.SessionExpired, findpeople.SessionExpired))
    return EXIT_OK


def cmd_pull(args) -> int:
    """pull — 사람까지 미리 받는 판 가운데 낡은 것을 받는다. ``--unattended`` 면 세션 파일을 있는 그대로만 쓰고(로그인 손을 안 띄운다),
    아니면 세션이 끊겼을 때 다시 받는다."""
    failed: list = []

    def once(session_file):
        done, failed[:] = pull(Book(session_file, 0), PULL_UNATTENDED_MOST if args.unattended else None)
        print("받았다: " + (" · ".join(f"{c}({t})" for t, c in done) if done else "없음"))
        for tree, company, why in failed:
            print(f"못 받았다: {company}({tree}) — {why}")
    if args.unattended:
        file = ep_session.known_file()
        if file is None:
            print("사내 세션 파일이 없다 — 사람 없이 도는 판은 로그인하지 않는다\n다음: 대화에서 스킬 ep-login 으로 EP 로그인을 한다")
            return EXIT_SESSION
        once(file)
    else:
        ep_session.session_first(once, expired=(inbox.SessionExpired,))
    return EXIT_TOOL if failed else EXIT_OK


def parser() -> argparse.ArgumentParser:
    """명령의 인자 표."""
    p = argparse.ArgumentParser(prog="identity.py", description="주소 → 보낸 사람 신원(회사 · 부서 경로 · 직급 · 직책 · 담당업무) — 읽기만 한다")
    sub = p.add_subparsers(dest="command", required=True, metavar="<명령>")
    q = sub.add_parser("lookup", help="표준 입력의 주소들(한 줄에 하나) → 신원 JSON — 사람 없이 도는 쪽이 부른다")
    q.add_argument("--most", type=int, default=LOOKUP_MOST, help=f"서버에 묻는 주소의 위(기본 {LOOKUP_MOST}) — 나머지는 「모름」, 다음 부름이 묻는다")
    q.set_defaults(fn=cmd_lookup)
    q = sub.add_parser("show", help="주소들의 신원을 한 줄씩")
    q.add_argument("addr", nargs="+")
    q.add_argument("--most", type=int, default=LOOKUP_MOST)
    q.set_defaults(fn=cmd_show)
    q = sub.add_parser("pull", help="사람까지 미리 받는 조직도(나의 회사 · 포스코홀딩스 · 포스코) 가운데 한 주가 넘은 것을 받는다")
    q.add_argument("--unattended", action="store_true", help="사람 없이 도는 쪽이 부를 때 — 로그인 손을 안 띄우고, 세션이 없으면 3")
    q.set_defaults(fn=cmd_pull)
    return p


def main(argv=None) -> int:
    """명령 입구 — 인자를 받아 하위 명령에 넘긴다. 세션을 못 받으면 3."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    if getattr(args, "most", 0) < 0:
        print("--most 는 0 이상이다")
        return EXIT_ARGS
    try:
        return args.fn(args)
    except (ep_session.NoSession, inbox.SessionExpired, findpeople.SessionExpired) as exc:
        print(f"사내 세션이 없다 · 끊겼다 — {exc}\n다음: 대화에서 스킬 ep-login 으로 EP 로그인을 한다")
        return EXIT_SESSION
    except Stop as stop:
        print(stop.said())
        return stop.code


if __name__ == "__main__":
    sys.exit(main())
