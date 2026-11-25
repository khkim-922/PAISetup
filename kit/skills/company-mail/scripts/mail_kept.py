"""받아 두는 것 — 받아 둔 것의 자리 · 주소록의 회사 값 · 회사 값마다 받아 둔 조직도(읽기 · 새로 받기 · 남기기).

부르는 꼴::

    import mail_kept
    mail_kept.cache_dir()                                 # 받아 둔 것(조직도 · 메일함 주소)의 자리
    company = mail_kept.company_of(given)                 # 준 값(--company) · MAIL_COMPANY · DEFAULT_COMPANY 순
    mail_kept.cached_org(company)                         # 받아 둔 판 (OrgChart, 받은 시각 글자) 또는 None — 서버에 안 묻는다
    mail_kept.load_org(company, fresh, open_box)          # 받아 둔 판, 없거나 fresh 면 open_box() 의 메일함으로 새로 받아 남긴다
    mail_kept.cached_org(company, tree="org_family", days=7)                    # 다른 고름의 나무 · 쓰는 날을 따로 준 판
    mail_kept.load_org(company, fresh, open_box, tree="org_family", people=False)   # 부서 나무만 받는 판

자리는 ``MAIL_ORG_CACHE_DIR`` 이 있으면 그 폴더, 없으면 홈 아래 ``ORG_CACHE_DIR`` 이다 — 임시 폴더는 정리 도구가 지운다. 조직도는 회사
값마다 한 파일(``org-<회사>.json`` · 꼴 번호 ``ORG_CACHE_FORMAT``)이고 ``ORG_CACHE_DAYS`` 동안 쓴다. 나의 회사(``org``) 밖의 고름 나무는
고름 · 회사마다 따로 한 파일(``org-<고름>-<회사>.json``)이고, 부서 나무만 받은 판은 곁의 파일(``….tree.json``)에 따로 산다 — 나무만 받은
판이 사람까지 받은 판을 덮지 않는다. 칸은 메일함 손(``inbox``)의
``DirectoryPerson`` · ``Dept`` 꼴을 그대로 받아 두고 아무도 안 읽는 칸(``ORG_CACHE_BLANK``)만 비운다. 이 스킬의 명령과 형제 스킬
company-directory 의 찾기가 같은 자리 · 같은 판을 쓴다.
"""

from __future__ import annotations

import dataclasses
import logging
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
for _where in (HERE, EP_LOGIN_SCRIPTS):
    if str(_where) not in sys.path:
        sys.path.insert(0, str(_where))             # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
import attachments  # noqa: E402 — 자리를 넣은 뒤에 싣는다
import ep_command  # noqa: E402
import inbox  # noqa: E402

DEFAULT_COMPANY = "poscochem(02)"   # 주소록의 회사 값 — 조직도 고름 상자의 값(메일함마다 다르다)
ORG_CACHE_DAYS = 30           # 받아 둔 조직도를 다시 받지 않고 쓰는 날 — 전사를 받는 데 오래 걸리고 인사는 드물게 바뀐다. 그 사이는 --fresh
ORG_CACHE_DIR = ".company-mail"   # 받아 둔 조직도 · 메일함 주소의 자리 — 홈 아래(임시 폴더는 정리 도구가 지운다)
ORG_CACHE_FORMAT = 4          # 캐시 파일의 꼴 번호 — DirectoryPerson · Dept 칸이나 받아 두는 칸이 바뀌면 올린다
ORG_CACHE_BLANK = ("user_id", "name_eng")   # 받아 둘 때 비우는 칸 — 받아 둔 판을 읽는 손이 안 쓰는 ID · 영문 이름(사번은 사람 파일 · 전화가 쓴다)
FRESH_WORD = "방금"           # 이 판에 새로 받은 조직도의 「받은 시각」 — 받아 둔 판은 파일을 쓴 시각이다
STAMP_FORM = "%m-%d %H:%M"    # 받아 둔 판의 「받은 시각」 꼴 — 명령이 「조직도 ○○ 판」 으로 낸다
ORG_UNKEPT = "받은 조직도를 PC 에 못 남겼다(%s) — 다음 판도 조직도에서 새로 받는다"

log = logging.getLogger("company-mail")


def cache_dir() -> pathlib.Path:
    """받아 둔 것(조직도 · 메일함 주소)의 자리 — ``MAIL_ORG_CACHE_DIR`` 이 있으면 그 폴더, 없으면 홈 아래 ``ORG_CACHE_DIR``."""
    root = os.environ.get("MAIL_ORG_CACHE_DIR", "").strip()
    return pathlib.Path(root) if root else pathlib.Path.home() / ORG_CACHE_DIR


def company_of(given: str) -> str:
    """주소록의 회사 값 — 준 값(``--company``) · ``MAIL_COMPANY`` · ``DEFAULT_COMPANY`` 순."""
    return (given or os.environ.get("MAIL_COMPANY", "").strip() or DEFAULT_COMPANY).strip()


def org_cache_path(company: str, tree: str = inbox.ORG_TREE_TYPE, people: bool = True) -> pathlib.Path:
    """고름 · 회사 값 하나의 받아 둔 조직도 파일 — 나의 회사 고름은 ``org-<회사>.json``, 다른 고름은 ``org-<고름>-<회사>.json``, 부서 나무만
    받은 판은 그 곁의 ``….tree.json``. 이름에 못 쓰는 글자는 첨부 가름 손(``attachments``)의 자로 바꾼다."""
    branch = "" if tree == inbox.ORG_TREE_TYPE else f"{tree}-"
    return cache_dir() / f"org-{branch}{attachments.UNSAFE_NAME.sub('_', company)}{'' if people else '.tree'}.json"


def cached_org(company: str, *, tree: str = inbox.ORG_TREE_TYPE, days: float = ORG_CACHE_DAYS, people: bool = True):
    """받아 둔 조직도 — ``days`` 안에 받은 판이 있으면 (OrgChart, 받은 시각 글자), 없거나 낡았거나 깨졌으면 None. ``people`` 이면
    사람까지 받은 판만, 아니면 사람까지 받은 판과 부서 나무만 받은 판 가운데 나중에 받은 것을 본다 — 나무만 받은 판을 사람이 없는 회사로
    읽지 않고, 나무가 낡아 새로 받은 나무를 옛 사람의 판이 가리지 않게. 서버에 묻지 않는다. 한 프로세스 안에서는 같은 파일(쓴 시각까지)을
    한 번만 읽는다 — 한 판이 여러 자리(세션 가름 · 주소 잇기 · 출처마다)에서 묻는다."""
    paths = [org_cache_path(company, tree)] if people else sorted(
        (org_cache_path(company, tree), org_cache_path(company, tree, False)), key=written_at, reverse=True)
    for path in paths:
        try:
            mark = (str(path), path.stat().st_mtime_ns, days)
        except OSError:
            continue
        if mark not in _READ:
            for old in [k for k in _READ if k[0] == mark[0]]:
                del _READ[old]            # 그 파일의 옛 판 — 다시 쓰인 파일을 읽을 때마다 옛 조직도가 쌓이지 않게
            _READ[mark] = _read_org(path, days)
        if _READ[mark]:
            return _READ[mark]
    return None


def written_at(path: pathlib.Path) -> float:
    """파일을 쓴 시각 — 없으면 0."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def tree_newer(company: str, tree: str = inbox.ORG_TREE_TYPE) -> bool:
    """부서 나무만 받은 판이 사람까지 받은 판보다 나중인가 — 사람까지의 판이 그 사이 낡았다(찾은 사람의 부서가 그 나무에 없어 나무를 새로
    받았다). 사람까지 다시 받을 때다."""
    return written_at(org_cache_path(company, tree, False)) > written_at(org_cache_path(company, tree))


_READ: dict = {}   # 이 프로세스가 읽은 받아 둔 조직도 — (경로, 쓴 시각, 쓰는 날) → cached_org 의 답


def _read_org(path: pathlib.Path, days: float):
    """받아 둔 파일 하나를 조직도로 되살린다 — (OrgChart, 받은 시각 글자). 없거나 낡았거나 칸이 안 맞으면 None."""
    got = ep_command.kept(path, ORG_CACHE_FORMAT, days, by_mtime=True)
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
    return chart, time.strftime(STAMP_FORM, time.localtime(stamp))


def load_org(company: str, fresh: bool, open_box, *, tree: str = inbox.ORG_TREE_TYPE, days: float = ORG_CACHE_DAYS, people: bool = True):
    """회사 조직 한 판 — 받아 둔 판(``cached_org``)이 있으면 그것을, 없거나 ``fresh`` 면 조직도에서 새로 받아 남긴다(``fetch_org``).
    내는 것 (OrgChart, 받은 시각 글자). ``open_box()`` 가 세션으로 연 메일함이고, 받아 둔 판으로 서면 부르지 않는다. 사람까지 받은 판은
    부서 나무만 청하는 쪽(``people`` 거짓)에도 선다."""
    got = None if fresh else cached_org(company, tree=tree, days=days, people=people)
    return got or fetch_org(company, open_box(), tree=tree, people=people)


def fetch_org(company: str, box, *, tree: str = inbox.ORG_TREE_TYPE, people: bool = True):
    """조직도에서 회사 조직 한 판을 새로 받아 남긴다 — (OrgChart, ``FRESH_WORD``). 못 남겨도 받은 것으로 답한다(``keep_org``)."""
    chart = box.org_snapshot(company, tree, people=people)
    keep_org(company, chart, tree=tree, people=people)
    return chart, FRESH_WORD


def org_record(chart) -> dict:
    """조직도 한 판의 받아 두는 꼴 — 꼴 번호 · 회사 · 부서 · 사람(``ORG_CACHE_BLANK`` 칸은 비운다)."""
    blank = dict.fromkeys(ORG_CACHE_BLANK, "")
    return {"format": ORG_CACHE_FORMAT, "company": chart.company,
            "depts": {c: dataclasses.asdict(d) for c, d in chart.depts.items()},
            "members": {c: [dataclasses.asdict(p) | blank for p in ps] for c, ps in chart.members.items()}}


def keep_org(company: str, chart, *, tree: str = inbox.ORG_TREE_TYPE, people: bool = True) -> None:
    """조직도 한 판을 그 고름 · 회사 값의 파일에 남긴다 — 못 남기면 경고 한 줄을 내고 그대로 간다(다음 판이 새로 받는다)."""
    unkept = ep_command.keep(org_cache_path(company, tree, people), org_record(chart))
    if unkept:
        log.warning(ORG_UNKEPT, unkept)
