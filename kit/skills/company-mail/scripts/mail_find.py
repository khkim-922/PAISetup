"""메일을 번호(unid)로 찾는 자리 — 받은편지함 · 폴더 · 임시보관함 · 보낸편지함의 보기를 훑어 목록 줄을 내고, 폴더 줄의 빈 칸은 모든편지함에서 채운다.

부르는 꼴::

    import mail_find
    mail_find.unid_shape(value)                                       # 꼴이 아니면 mail_stop.Stop(종료 2) — 세션 앞의 거름
    e = mail_find.find_mail(box, inbox, unid, folder, scan)           # 목록 줄(inbox.Entry) 하나 — 없으면 mail_find.NotFound
    e = mail_find.find_mail(box, inbox, unid, None, scan, first=SENT) # 보낸편지함을 끝까지 먼저 · 나머지 보기는 그 뒤에 한 번씩
    rows = mail_find.find_mails(box, inbox, unids, folder, scan)      # 준 차례대로
    f = mail_find.user_folder(box, path)                              # 폴더 경로 → 폴더(inbox.Folder) — 없으면 Stop(종료 2)

``box`` 는 열린 메일함 손(``mail_open.open_mailbox``), ``inbox`` 는 곁의 메일함 손 모듈이다. ``folder`` 를 주면 그 폴더(``DRAFTS`` ·
``SENT`` 도)에서만, ``None`` 이면 받은편지함 · 폴더 · 임시보관함 · 보낸편지함 차례로 찾는다(``views_of``). ``first`` 를 주면 그 보기를
끝까지 먼저 훑고 못 찾은 것만 나머지 보기에서 찾는다 — 보기는 어느 쪽이든 한 번씩만 훑는다. 휴지통은 안 훑는다. 이 스킬의 명령(읽기 ·
첨부 · 짓기 · 바꾸기)과 형제 스킬 company-directory 의 「지난 메일」 출처가 같은 자리로 찾는다 — 훑는 차례와 멈추는 자리는
``references/DESIGN.md`` 「mail_find.py · 메일 찾기」 · 「mail_find.py · 모든편지함으로 채우기」 가 든다.
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
EP_LOGIN_SCRIPTS = HERE.parents[1] / "ep-login" / "scripts"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
for _where in (HERE, EP_LOGIN_SCRIPTS):
    if str(_where) not in sys.path:
        sys.path.insert(0, str(_where))             # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
import inbox  # noqa: E402 — 자리를 넣은 뒤에 싣는다
from ep_command import EXIT_ARGS  # noqa: E402
from mail_stop import Stop  # noqa: E402

DEFAULT_SCAN = 300           # 메일 하나를 unid 로 찾을 때 첫 판에 보기마다 훑는 새것의 줄 수 — 없으면 그 보기들을 끝까지 훑는다
FILL_SCAN = 5000              # 폴더 줄을 채우거나 list --since 가 상자 밖 메일을 세려고 모든편지함을 새것부터 훑는 줄의 상한 — 흔한 메일함을
                              # 통째로 덮는다. 넘는 메일함은 못 채운 줄을 끝 줄이 센다
STAMP_CHARS = 15              # 보기의 시각 칸($91 · YYYYMMDDTHHMMSS,cc+09)에서 초까지의 글자 수 — 두 보기의 시각을 견주는 몫
TRASH_WORD = "휴지통"
DRAFTS = inbox.DRAFTS_FOLDER   # read · attachment 의 --folder 로 주면 임시보관함에서만 찾는다 — 그 줄의 folder 값 그대로
SENT = inbox.SENT_FOLDER       # 같은 꼴 — 보낸편지함에서만 찾는다
SYSTEM_BOXES = {DRAFTS: "임시보관함", SENT: "보낸편지함"}   # 시스템 편지함의 사람 이름 — 웹메일 화면의 이름
DEEP_PAGE = inbox.VIEW_PAGE_MOST   # 끝까지 훑을 때 한 번에 받는 줄 — 서버가 보기 한 번에 내는 줄의 위
NO_FOLDER = "그런 폴더가 없다: {path!r} — folders 명령으로 이름을 본다"   # ⚠ 머리를 메일함 스캔(scan_hand)이 읽는다 — 머리는 그대로 둔다
# 찾을 자리의 이름 — 받은편지함 · 쓰는 사람이 지은 폴더 모두. 시스템 편지함처럼 「(」 로 시작해 쓰는 사람의 폴더 경로와 안 겹친다
INBOX_PLACE, FOLDERS_PLACE = "($Inbox)", "(Folders)"
EVERY_VIEW = (INBOX_PLACE, FOLDERS_PLACE, DRAFTS, SENT)   # --folder 를 안 준 찾기가 훑는 자리와 그 차례


class NotFound(Stop):
    """찾는 메일이 훑은 보기에 없다(``find_mails``) — 부르는 명령이 제 말을 덧붙일 수 있게 가른 Stop."""


def unid_shape(value: str, what: str = "메일") -> None:
    """메일 · 규칙의 열쇠(unid)의 꼴(``inbox.is_unid``)인가 — 아니면 Stop. 꼴이 아닌 번호의 멈춤 말은 이 한 자리가 든다 — 세션 앞의 거름과
    찾는 손(``find_mails`` · 휴지통 찾기)이 같은 말로 멈춘다."""
    if not inbox.is_unid((value or "").strip()):
        raise Stop(EXIT_ARGS, f"{what} 열쇠(unid 32자리)가 아니다: {value!r} — 목록 · 검색 · 규칙 줄 끝의 32자리를 그대로 넘긴다")


def deep_hit(fetch, hit, start: int):
    """보기 하나를 ``start`` 줄부터 끝까지 ``DEEP_PAGE`` 줄씩 받으며(``inbox.Pages``) ``hit`` 이 참을 낸 쪽에서 그 값을 낸다 — 끝까지
    없으면 None."""
    for rows in inbox.Pages(fetch, start, lambda seen: DEEP_PAGE):
        found = hit(rows)
        if found:
            return found
    return None


def find_mail(box, inbox, unid: str, folder: str | None, scan: int, *, first: str = ""):
    """unid 한 통의 목록 줄(Entry) — ``find_mails`` 의 한 통 꼴."""
    return find_mails(box, inbox, [unid], folder, scan, first=first)[0]


def find_mails(box, inbox, unids, folder: str | None, scan: int, *, first: str = "") -> list:
    """unid 들의 목록 줄(Entry)을 준 차례대로 찾는다 — ``--folder`` 를 주면 그 폴더(``(Drafts)`` · ``(Sent)`` 도), 아니면
    받은편지함 · 폴더 · 임시보관함 · 보낸편지함 차례로(``sweep_order`` 의 무리마다 ``sweep_views``). ``first`` 는 그 보기들 가운데 끝까지
    먼저 훑을 하나다 — 거기서 찾은 메일은 그 보기의 줄로 선다. 하나라도 없으면 Stop.
    폴더 줄의 보낸 분 주소 · 받는 꼴은 ``AllMail`` 이 모든편지함에서 채운다.
    """
    wanted = [u.strip().upper() for u in unids]
    for unid in wanted:
        unid_shape(unid)
    got, left = swept(box, inbox, wanted, folder, scan, first=first)
    if left:
        missing = ", ".join(u for u in dict.fromkeys(wanted) if u in left)
        raise NotFound(EXIT_ARGS, f"메일을 못 찾았다: {missing} — {searched_word(folder)} 없다. "
                                  f"{TRASH_WORD}은 안 훑는다 — 지운 메일이면 {TRASH_WORD}에 있을 수 있고, 그 본문은 웹메일에서 연다")
    return fill_found(box, got, wanted)[0]


def fill_found(box, got: dict, wanted: list[str]) -> tuple[list, AllMail]:
    """보기에서 찾은 줄(``sweep_views`` 의 ``got``)을 준 차례(``wanted``)대로 모아 폴더 줄을 모든편지함에서 채운다 — (채운 줄들, 채운
    ``AllMail``). 못 찾은 번호는 건너뛴다 — 못 찾음을 멈춤으로 낼지는 부르는 쪽이 채우기 앞에서 가른다(``find_mails``)."""
    filled = AllMail(box)
    return filled.fill([got[u] for u in wanted if u in got]), filled


def swept(box, inbox, wanted: list[str], folder: str | None, scan: int, *, first: str = "") -> tuple[dict, set]:
    """unid(32자리 대문자)들의 목록 줄을 찾을 자리의 무리마다(``sweep_order``) 훑는다 — (찾은 unid → 목록 줄, 못 찾은 unid). 앞 무리에서
    다 찾으면 뒤 무리는 안 훑는다. 폴더 줄은 안 채운다 — 한 통 찾기(``find_mails``)와 여러 통 읽기가 이 한 자리로 훑는다."""
    got, left = {}, set(wanted)
    for views in sweep_order(folder, first):
        found, left = sweep_views(box, inbox, [u for u in wanted if u in left], views, scan)
        got.update(found)
        if not left:
            break
    return got, left


def views_of(folder: str | None) -> tuple:
    """찾을 자리들 — ``--folder`` 를 안 줬으면(None) ``EVERY_VIEW``, 줬으면 그 폴더(``(Drafts)`` · ``(Sent)`` 도) 하나."""
    return EVERY_VIEW if folder is None else (folder,)


def sweep_order(folder: str | None, first: str) -> list[tuple]:
    """찾을 자리(``views_of``)를 훑을 무리로 — ``first`` 를 주면 그 보기 하나가 앞 무리, 나머지가 뒤 무리다. 보기는 한 무리에만 든다."""
    views = views_of(folder)
    return [(first,), tuple(v for v in views if v != first)] if first else [views]


def searched_word(folder: str | None) -> str:
    """``sweep_views`` 가 훑은 자리를 사람 말로 — 훑은 보기만 댄다. 안 훑은 자리를 「없다」에 넣지 않는다."""
    return ("받은편지함 · 폴더 · 임시보관함 · 보낸편지함 어디에도" if folder is None
            else f"{SYSTEM_BOXES.get(folder) or f'폴더 {folder}'}에")


def sweep_views(box, inbox, wanted: list[str], views: tuple, scan: int) -> tuple[dict, set]:
    """unid(32자리 대문자)들의 목록 줄을 찾을 자리들(``views`` — ``EVERY_VIEW`` 의 이름 · 쓰는 사람의 폴더 경로)에서 찾는다 — (찾은
    unid → 목록 줄, 못 찾은 unid). 폴더 줄은 채우지 않은 채 낸다. 휴지통은 안 찾는다. 보기는 통 수와 상관없이 한 번씩만 훑고, 맨 앞
    자리 뒤의 보기들은 함께 받는다(DESIGN.md 「mail_find.py · 메일 찾기」).
    """
    left = set(wanted)
    got: dict = {}

    def fetchers(place) -> list:
        """찾을 자리 하나의 보기들 — 하나는 (count, start) → 줄. 폴더 모두면 폴더 나무를 묻고, 쓰는 사람의 폴더 경로면 그 폴더(``user_folder``)."""
        if place == INBOX_PLACE:
            return [lambda n, s: box.list(count=n, start=s)]
        if place == DRAFTS:
            return [lambda n, s: box.list_drafts(count=n, start=s) or []]
        if place == SENT:
            return [lambda n, s: box.list_sent_mail(count=n, start=s)]
        folders = box.folders() if place == FOLDERS_PLACE else [user_folder(box, place)]
        return [lambda n, s, f=f: box.list_folder(f, count=n, start=s) for f in folders]

    def hit(rows) -> bool:
        """이 쪽에서 찾은 줄을 담고, 다 찾았으면 참 — 먼저 훑은 보기의 줄이 선다."""
        for e in rows:
            unid = e.unid.upper()
            if unid in left:
                left.discard(unid)
                got[unid] = e
        return not left

    def first_pages(fetches) -> bool:
        """보기들의 새것 scan 통을 함께 받아 보기 차례대로 담는다 — 다 찾았으면 참."""
        with ThreadPoolExecutor(inbox.ORG_WORKERS) as pool:
            for rows in pool.map(lambda fetch: fetch(scan, 1), fetches):   # 답은 보기 차례대로 온다 — 먼저 선 보기의 줄이 선다
                hit(rows)
        return not left

    # 첫 판은 보기마다 새것 scan 통 — 맨 앞 자리(대개 받은편지함)가 먼저 혼자다. 없으면 뒤 자리들을 함께 받고, 그래도 없으면 같은
    # 보기들을 그 뒤부터 끝까지 훑는다(검색이 찾은 옛 메일). 뒤 자리의 보기(폴더 나무)는 맨 앞에서 못 찾았을 때만 묻는다
    seen = fetchers(views[0])
    if not first_pages(seen):
        later = [fetch for place in views[1:] for fetch in fetchers(place)]
        seen += later
        first_pages(later)
    for fetch in seen if left else []:
        if deep_hit(fetch, hit, scan + 1):
            break
    return got, left


def folder_of(box, path: str):
    """쓰는 사람이 지은 폴더 가운데 경로가 ``path`` 인 것(``inbox.Folder``) — 없으면 None. 폴더 나무를 한 번 묻는다."""
    return next((f for f in box.folders() if f.path == path), None)


def user_folder(box, path: str):
    """경로가 ``path`` 인 폴더(``folder_of``) — 없으면 Stop(2). 「그런 폴더가 없다」 의 말은 이 한 자리다(메일함 스캔이 그 머리를 읽는다)."""
    found = folder_of(box, path)
    if found is None:
        raise Stop(EXIT_ARGS, NO_FOLDER.format(path=path))
    return found


def folder_row(e) -> bool:
    """쓰는 사람이 지은 폴더의 보기에서 온 줄인가 — 그 보기에는 보낸 분 주소와 받는 꼴 칸이 없다. 받은편지함 · 시스템 편지함
    (이름이 ``(`` 로 시작한다)의 줄은 아니다."""
    return bool(e.folder) and not e.folder.startswith(inbox.SYSTEM_FOLDER_MARK)


class AllMail:
    """폴더 줄에 없는 칸(보낸 분 주소 · 받는 꼴)을 모든편지함 줄에서 unid 로 채운다 — 모든편지함은 찾는 줄이 남은 동안만 새것부터 이어
    받는다(``FILL_SCAN`` 까지 · 멈추는 자리는 DESIGN.md 「mail_find.py · 모든편지함으로 채우기」). 받은 줄은 명령 하나 동안 든다 — 한 통 찾기
    (``find_mails``)와 목록 · 세기가 함께 쓰고, 그 시각까지 받는 쪽(명령의 ``list --since``)은 ``reach_date`` 로 같은 장을 잇는다.

    못 찾은 줄은 폴더 줄 그대로 두고 ``missed`` 에 든다 — 빈 주소를 주소인 것처럼 안 낸다. 모든편지함 보기가 없으면 ``absent`` 가
    참이다.
    """

    def __init__(self, box):
        self.box = box
        self.marks: dict = {}       # unid → inbox.Marks — 보기 차례(새것부터)대로 든다
        self.seen = 0               # 받은 모든편지함 줄 수
        self.oldest = ""            # 받은 줄 가운데 가장 옛 시각(YYYYMMDDTHHMMSS) — 빈 글자는 아직 시각을 못 받았다
        self.oldest_date = ""       # 같은 것을 보기의 xdate 꼴(YYYY-MM-DD HH:MM:SS)로 — 상자 보기들과 같은 시계로 견주는 자리
        self.ended = False          # 더 받을 것이 없다 — 보기 끝 · 상한 · start 를 안 따름 · 보기 없음
        self.whole = False          # 보기 끝(빈 쪽)까지 받았다
        self.absent = False         # 이 메일함에 모든편지함 보기가 없다
        self.missed: set = set()    # 채울 폴더 줄인데 모든편지함에서 못 찾은 unid
        self._pages = inbox.Pages(self._fetch, 1, lambda seen: min(DEEP_PAGE, FILL_SCAN - seen))   # 이어 받는 장 — 한 쪽씩 꺼낸다
        self._next = iter(self._pages)

    def fill(self, rows) -> list:
        """줄들 가운데 폴더 줄의 받는 꼴 · 보낸 분을 채워 같은 차례로 낸다 — 다른 줄은 그대로다."""
        wanted = {e.unid.upper(): e.date_sort[:STAMP_CHARS] for e in rows if folder_row(e)}
        self._reach(wanted)
        out = []
        for e in rows:
            unid = e.unid.upper()
            mark = self.marks.get(unid) if unid in wanted else None
            if mark is not None:
                self.missed.discard(unid)
                e = dataclasses.replace(e, role=mark.role, sender=mark.sender if mark.sender.addr else e.sender)
            elif unid in wanted:
                self.missed.add(unid)
            out.append(e)
        return out

    def _reach(self, wanted: dict) -> None:
        """찾는 줄(unid → 시각)이 받은 줄에 아직 없고 더 옛 쪽에 있을 수 있는 동안 모든편지함을 다음 쪽까지 받는다."""
        def settled() -> bool:
            left = [stamp for unid, stamp in wanted.items() if unid not in self.marks]
            return not left or bool(self.oldest and all(stamp > self.oldest for stamp in left))
        self._page_until(settled)

    def reach_date(self, since: str) -> bool:
        """받은 시각(xdate)이 ``since`` 보다 옛 줄이 설 때까지 이어 받는다 — 그 시각까지 다 받았나(옛 줄이 섰거나 보기 끝)를 낸다.
        상한 · 보기 없음 · start 를 안 따름으로 멈췄으면 거짓이다. 받은 장은 같은 명령의 ``fill`` 이 함께 쓴다."""
        def passed() -> bool:
            return bool(self.oldest_date and self.oldest_date < since)
        self._page_until(passed)
        return passed() or self.whole

    def _page_until(self, done) -> None:
        """``done()`` 이 참이 되거나 더 받을 것이 없을 때까지(``ended``) 모든편지함을 한 쪽씩 받는다."""
        while not self.ended and not done():
            self._page()

    def _fetch(self, count: int, start: int) -> list:
        """모든편지함 한 쪽 — 이 메일함에 그 보기가 없으면(``list_all`` 이 None) ``absent`` 를 세우고 빈 쪽으로 끝낸다."""
        page = self.box.list_all(count=count, start=start)
        if page is None:
            self.absent = True
        return page or []

    def _page(self) -> None:
        """모든편지함의 다음 쪽(``Pages`` — 상한 ``FILL_SCAN`` · 빈 쪽 · 서버가 start 를 안 따름에서 멈춘다)을 받아 든다. 멈췄으면 끝낸다 —
        보기가 있고 빈 쪽으로 멈췄을 때만 보기 끝까지 받은 것이다."""
        page = next(self._next, None)
        if page is None:
            self.ended = True
            self.whole = self._pages.end == self._pages.EMPTY and not self.absent
            return
        self.seen = self._pages.seen
        for m in page:
            self.marks.setdefault(m.unid.upper(), m)
        stamps = [s for s in (m.date_sort[:STAMP_CHARS] for m in page) if s]
        if stamps:
            self.oldest = min(stamps + ([self.oldest] if self.oldest else []))
        dates = [m.date for m in page if m.date]
        if dates:
            self.oldest_date = min(dates + ([self.oldest_date] if self.oldest_date else []))
