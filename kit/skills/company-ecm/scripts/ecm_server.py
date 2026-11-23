"""ECM 서버 하나와 주고받는 손 — 요청마다 서버에 닿기 전에 잰 꼴에 대어 막고(읽기 ``guard`` · 바꾸는 GET ``_guard_edit`` · POST
``POST_SHAPES``), 보내고, 답을 푼다. 값과 기록의 꼴은 바탕(``ecm_base``)이 든다.
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

from ecm_base import (AGENT_SYSTEM, AJAX, ArgsError, BOXES, CABINET_ID, CABINET_KIND, CABINET_OPTION, CANCEL_FLAG,
    CANCEL_NEXT, COMPANY_ID, COMPANY_VAR, CONTEXT_QUERY, Cabinet, DEFAULT_PERIOD, DEFAULT_PER_PAGE, DEFAULT_URL, DEPT_CABINETS, DEPT_CODE,
    DEPT_DOCS, DOC_STATUS_DRAFT, DOC_TYPE_GENERAL, DUP_QUERY, Doc, DocState, EDIT_FLAG, EDIT_SERVICE, EcmError, FAVORITE_QUERY, FILE_TYPES,
    FOLDER_DOCS, FOLDER_FIND_QUERY, FOLDER_ID, FOLDER_KEY, FOLDER_ROOT_TYPES, FOLDER_SEP, FOLDER_SERVICE, FOLDER_TYPE, FOLDER_WALK_MAX,
    Folder, Grant, HISTORY_PER_PAGE, HISTORY_PER_PAGE_MAX, HISTORY_QUERY, HTTP_TIMEOUT, Hit, JSON_READ, LIST_DEFAULTS, MAIN_PAGE, MY_DOCS,
    NAME_MIN, NOTICE_WORDS, NO_DUE_DATE, OBJECT_ID, ORGAN_FIND, ORGAN_SERVICE, ORGAN_SUBS, ORGAN_USERS, OWN_CABINET, Organ, PEOPLE_QUERY,
    PERIODS, PERSONAL_OPTION, PERSON_ID, PROPERTY_LOCK, PROPERTY_PAGE, PROPERTY_QUERY, PROPERTY_SAVE_QUERY, PROPERTY_VERSION, Person,
    PropChange, PropertyPage, RAW_BAD, READS, READ_FORMS, REGISTER_QUERY, REGISTER_ROW, REGISTER_SERVICE, ROLE_ORDER, ROLE_QUERY, Refused,
    SAVE_ENCODED, SAVE_FROM_PAGE, SAVE_TAIL_FROM_PAGE, SAVE_WORKFLOW_FROM_PAGE, SCREEN_NO_DUE, SEARCH_DATE_FIELDS, SEARCH_FIELDS,
    SEARCH_MINE, SEARCH_QUERY, SECURITY_FIELD, SECURITY_LOG_QUERY, SECURITY_PAIRS, SERVER_NAME, SORTS, SearchQuery, Security,
    SecurityUnread, SessionExpired, SessionMissing, Ticket, USE_QUERY, USE_WORDS, VIEW_DENIED, Version, _dept_code, _loose, _object_id,
    cabinet_key, check_search, check_search_page, folder_key, folder_name, log, organ_name, refuse_box_with_place, outside_roles, path_word, person_name, property_value, session_path,
    url_from_env)
import ep_session  # noqa: E402 — 바탕(ecm_base)이 형제 스킬 ep-login 의 자리를 sys.path 에 넣은 뒤에 싣는다


def cookie_header(session_file: pathlib.Path, url: str) -> str:
    """세션 파일에서 ``url`` 에 실릴 쿠키만 골라 ``Cookie`` 머리 글로 낸다 — 없으면 빈 글자. 고르기(도메인 · 경로 · secure · 포트를
    뗀 호스트)는 쿠키 통(``ep_session.load_jar``)이 한다. 파일이 없거나 못 읽거나 비었으면 ``SessionMissing``."""
    request = urllib.request.Request(url)
    ep_session.load_jar(session_file, missing=SessionMissing).add_cookie_header(request)
    return request.get_header("Cookie") or ""


class Ecm:
    """ECM 서버 하나. 모든 요청을 서버에 닿기 전에 잰 꼴에 댄다 — 읽기는 ``guard``(닫힌 목록), 편집 열기 · 편집취소는
    ``_guard_edit``, 잰 POST 여섯(``POST_SHAPES``)은 ``_post`` 가 든다."""

    def __init__(self, url: str = DEFAULT_URL, session_file=None, *, timeout: float = HTTP_TIMEOUT):
        match = re.match(r"^(https?://[^/?#]+)(/[^?#]*?)/?$", url.strip(), re.IGNORECASE)
        if not match or not match.group(2):
            raise ArgsError(f"ECM 주소(…/ECM)가 아니다: {url!r}")
        self.server, self.context = match.group(1), match.group(2)
        self.timeout = timeout
        self.session_file = pathlib.Path(session_file).expanduser() if session_file else session_path()
        self._cookie = cookie_header(self.session_file, self.server + self.context + "/")
        if not self._cookie:
            raise SessionMissing(f"세션 파일에 {urllib.parse.urlsplit(self.server).hostname} 의 쿠키가 없다 — 스킬 ep-login 으로 받는다")
        self._opener = ep_session.opener()   # 쿠키는 머리로 싣고 · 리다이렉트는 안 따라간다
        self._main: str | None = None        # 메인 화면 — 한 판(명령 한 번) 안에서는 한 번만 받는다(문서함 · 회사 열쇠가 든다)

    @classmethod
    def from_env(cls) -> "Ecm":
        """환경변수의 ECM 주소(``url_from_env``)와 세션 파일 자리(``session_path``)로 서버 하나를 짓는다."""
        return cls(url_from_env(), session_path())

    # 막기 — 이 판이 지은 주소를 다시 풀어 닫힌 목록에 댄다
    def guard(self, method: str, url: str) -> None:
        """읽기 주소가 잰 꼴인가를 서버에 닿기 전에 가린다 — 아니면 ``Refused``. 꼴(메인 · json.do · 폴더 나무 · 속성 화면 · ajax 읽기)을
        주소의 자리로 가르고 꼴마다의 판정은 제 손가락이 든다."""
        parts = urllib.parse.urlsplit(url)
        if method != "GET":
            raise Refused(f"읽기 길은 GET 만 보낸다: {method} {url}")
        if f"{parts.scheme}://{parts.netloc}".lower() != self.server.lower():
            raise Refused(f"ECM 서버 밖의 주소라 묻지 않는다: {url}")
        if parts.path == self.context + MAIN_PAGE and not parts.query:
            return
        if parts.path == self.context + JSON_READ:
            if _is_json_read(_single_query(parts.query, url)):
                return
            raise Refused(f"권한 화면이 묻는 잰 읽기가 아니라 묻지 않는다: {url}")
        if parts.path == self.context + AJAX and _is_folder_query(parts.query, url):
            return
        if parts.path == self.context + PROPERTY_PAGE:
            if _is_property_read(_single_query(parts.query, url)):
                return
            raise Refused(f"문서 정보의 잰 꼴이 아니라 묻지 않는다: {url}")
        if parts.path != self.context + AJAX:
            raise Refused(f"읽기로 잰 주소가 아니라 묻지 않는다: {url}")
        _refuse_unmeasured_ajax(parts.query, url)

    def _fetch(self, url: str, *, edit: str = "") -> tuple[bytes, str]:
        """GET 하나를 그 길의 문에 대고 보낸다 — ``edit`` 은 바꾸는 GET 의 갈래 하나(``EDIT_FLAG`` · ``CANCEL_FLAG``)로 그 갈래 하나만
        열고, 비우면 읽기 길(``guard``)이다."""
        if edit:
            self._guard_edit(url, edit)
        else:
            self.guard("GET", url)
        return self._send(urllib.request.Request(url, headers={"Cookie": self._cookie, "X-Requested-With": "XMLHttpRequest"}))

    def _send(self, request: urllib.request.Request) -> tuple[bytes, str]:
        """막는 문을 지난 요청 하나를 보내 (답의 바이트, ``Content-Type``)을 낸다 — 리다이렉트 · 401 · 403 은 ``SessionExpired``, 그 밖의
        HTTP 오류 · 못 닿음은 ``EcmError`` 로 옮긴다. 쿠키는 머리로 싣고 리다이렉트는 안 따라간다(``ep_session.opener``)."""
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except ep_session.Redirected as exc:
            raise SessionExpired(f"ECM 이 세션을 안 받았다(→ {exc.location}) — 스킬 ep-login 으로 다시 받는다") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise SessionExpired(f"ECM 이 거절했다(HTTP {exc.code}) — 스킬 ep-login 으로 다시 받는다") from exc
            raise EcmError(f"ECM 이 HTTP {exc.code} 를 냈다: {request.full_url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise EcmError(f"ECM 에 못 닿았다: {exc}") from exc

    # 편집 열기 · 편집취소 둘만 여는 문 — 서비스 · 갈래 · 칸 하나(MS_OBJECT_ID)가 정확히 그 꼴일 때만 보낸다
    def _guard_edit(self, url: str, flag: str) -> None:
        """편집 열기 · 편집취소의 GET 이 잰 꼴(ECM 서버 · ajax 자리 · 그 서비스와 갈래 하나 · 문서 열쇠 하나)인가를 서버에 닿기 전에 가린다 — 아니면 ``Refused``."""
        parts = urllib.parse.urlsplit(url)
        query = _single_query(parts.query, url)
        object_id = query.pop("MS_OBJECT_ID", "")
        if (f"{parts.scheme}://{parts.netloc}".lower() != self.server.lower() or parts.path != self.context + AJAX
                or flag not in (EDIT_FLAG, CANCEL_FLAG) or query != {"ServiceName": EDIT_SERVICE, flag: "true"}
                or not OBJECT_ID.match(object_id)):
            raise Refused(f"편집 열기 · 편집취소의 잰 꼴이 아니라 묻지 않는다: {url}")

    def _post(self, query: dict, body: bytes, *, path: str = AJAX) -> tuple[bytes, str]:
        """잰 POST 만 보낸다 — 등록 화면의 둘(같은 이름 찾기 · 등록) · 속성 저장(권한 · 이름 · 태그 · 완료일)과, 조회지만 POST 인
        셋(우클릭 메뉴 · 전사 검색 · 폴더 이름 찾기). 질의가 그 꼴 그대로이고 몸의 칸이 그 질의와 맞을 때만."""
        fields = dict(urllib.parse.parse_qsl(body.decode("utf-8"), keep_blank_values=True))
        if not any(path == at and query == want and shape(fields) for at, want, shape in POST_SHAPES):
            raise Refused(f"잰 POST 의 꼴이 아니라 보내지 않는다: {path} {query}")
        url = f"{self.server}{self.context}{path}?{urllib.parse.urlencode(query)}"
        return self._send(urllib.request.Request(url, data=body, method="POST", headers={
            "Cookie": self._cookie, "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}))

    def _ajax(self, service: str, flag: str, params: dict, *, edit: bool = False) -> dict:
        """``edit`` 이면 ``flag`` 갈래 하나만 여는 바꾸는 문(``_guard_edit``)으로 보낸다."""
        query = urllib.parse.urlencode({"ServiceName": service, flag: "true", **params})
        return _answer(*self._fetch(f"{self.server}{self.context}{AJAX}?{query}", edit=flag if edit else ""))

    def folders(self, cabinet: str, parent: str = "") -> list[Folder]:
        """문서함의 폴더 한 층 — ``parent`` 를 비우면 문서함 바로 아래, 주면 그 폴더(``fdr…``) 아래. 등록 화면의 폴더 나무와 같다."""
        cabinet_key(cabinet)
        if parent:
            folder_key(parent)
        if parent:
            menu, upper = FOLDER_TYPE, f"{cabinet}_{parent}"
        else:
            kind = getattr(self.cabinet_by_key(cabinet), "kind", "")
            menu = "MENU_PROJECT" if kind == CABINET_KIND["MENU_PROJECT"] else "MENU_DEPT"
            upper = cabinet
        query = urllib.parse.urlencode({"ServiceName": FOLDER_SERVICE, "menuType": menu, "upperKey": upper})
        data = _answer(*self._fetch(f"{self.server}{self.context}{AJAX}?{query}"))
        found = []
        for row in data.get("ML_MENU_LIST") or []:
            key = FOLDER_KEY.match(str(row.get("MS_MENU_ID", "")))
            if key and row.get("MS_FORM_ID") == FOLDER_TYPE:
                found.append(Folder(key.group(1), key.group(2), str(row.get("MS_MENU_NAME", "")).strip(),
                                    str(row.get("MS_HAS_SUB", "0")) not in ("0", "")))
        return found

    def walk_folders(self, cabinet: str):
        """문서함의 폴더 나무를 문서함 바로 아래부터 한 층씩 훑으며 (이름 경로, Folder) 를 낸다 — 읽기만 하고, 아래 폴더가 있는 폴더만
        연다. 부르는 쪽이 찾으면 거기서 멈춘다(늦게 연다). 요청이 ``FOLDER_WALK_MAX`` 를 넘으면 ``EcmError``."""
        layer, asked = [((f.name,), f) for f in self.folders(cabinet)], 1
        while layer:
            below = []
            for path, f in layer:
                yield path, f
                if f.has_sub:
                    if asked >= FOLDER_WALK_MAX:
                        raise EcmError(f"문서함 {cabinet} 의 폴더가 많아 {FOLDER_WALK_MAX} 번 넘게 물어야 한다 — 다 훑지 않았다. "
                                       f"폴더 경로(이름 {FOLDER_SEP} 이름)로 준다")
                    asked += 1
                    below.extend((path + (s.name,), s) for s in self.folders(cabinet, f.id))
            layer = below

    def folder_path(self, cabinet: str, folder: str) -> tuple[str, ...] | None:
        """그 폴더(``fdr…``)의 이름 경로 — 그 문서함의 폴더 나무에 없으면 None. 찾으면 거기서 훑기를 멈춘다."""
        folder_key(folder)
        return next((path for path, f in self.walk_folders(cabinet) if f.id == folder), None)

    def match_folders(self, cabinet: str, name: str) -> tuple[list[tuple[tuple[str, ...], Folder]], list[tuple[tuple[str, ...], Folder]]]:
        """나무를 한 번 끝까지 훑어 (이름이 꼭 맞는 폴더, 이름에 그 글이 든 폴더)를 낸다 — 뒤엣것은 대소문자 · 빈칸을 안 가리고, 앞엣것과
        겹치지 않는다. 고르지 않는다 — 꼭 맞는 것이 없을 때 사람에게 보일 후보다."""
        name = name.strip()
        if not name:
            raise ArgsError("찾을 폴더 이름이 비었다")
        want = _loose(name)
        exact, near = [], []
        for path, f in self.walk_folders(cabinet):
            if f.name == name:
                exact.append((path, f))
            elif want in _loose(f.name):
                near.append((path, f))
        return exact, near

    def resolve_folder(self, cabinet: str, path_text: str) -> tuple[tuple[str, ...], Folder]:
        """폴더 경로(「이름 > 이름」 — 화면의 꼴)를 한 층씩 꼭 맞는 이름으로 따라가 (이름 경로, Folder) 를 낸다. 경로 첫 마디가 그
        문서함 이름이면 뗀다(목록 줄 · 속성 화면의 폴더 칸은 문서함 이름부터 든다). 한 층에 같은 이름이 둘이거나 없으면 ``EcmError``."""
        parts = [p.strip() for p in path_text.split(FOLDER_SEP) if p.strip()]
        own = self.cabinet_name(cabinet)
        if parts and own and parts[0] == own:
            parts = parts[1:]
        if not parts:
            raise ArgsError(f"폴더 경로가 비었다 — 「이름 {FOLDER_SEP} 이름」 꼴로 준다")
        layer, here, folder = self.folders(cabinet), (), None
        for i, part in enumerate(parts):
            hit = [f for f in layer if f.name == part]
            if len(hit) != 1:
                raise ArgsError(folder_miss_word(here + (part,), len(hit), layer))
            folder, here = hit[0], here + (part,)
            if i + 1 < len(parts):
                layer = self.folders(cabinet, folder.id) if folder.has_sub else []
        return here, folder

    def duplicates(self, folder: str, title: str, ext: str) -> list[str]:
        """그 폴더에 같은 이름 · 확장자의 문서가 있나 — 화면이 등록 전에 묻는 같은 요청. 걸린 이름들을 낸다."""
        body = urllib.parse.urlencode({"folderID": folder, "title": title, "fileExt": ext}).encode("utf-8")
        data = _answer(*self._post(DUP_QUERY, body))
        return [f"{d.get('MS_DOC_TITLE', '')}.{d.get('MS_DOC_EXT', '')}" for d in data.get("ML_DUPLICATED_LIST") or []
                if str(d.get("MS_DOC_TITLE", "")).strip()]

    def register(self, *, folder: str, title: str, ext: str, size: int, server_path: str, server_file: str,
                 security: str, open_flag: str) -> str:
        """에이전트가 임시 자리에 올린 파일을 그 폴더의 새 문서로 등록하고(몸은 ``register_body``) 답의 문서 열쇠를 낸다."""
        body = register_body(folder=folder, title=title, ext=ext, size=size, server_path=server_path, server_file=server_file,
                             security=security, open_flag=open_flag)
        data = _answer(*self._post(REGISTER_QUERY, body))
        object_id = str(data.get("MS_OBJECT_ID", ""))
        if not OBJECT_ID.match(object_id):
            raise EcmError(f"등록 답에 문서 열쇠가 없다 — ECM 화면에서 그 폴더를 본다: {data.get('MS_MSG_DESC', '')}")
        return object_id


    def _main_page(self) -> str:
        """메인 화면 — 한 판에 한 번만 받는다. 문서함 목록 · 제 부서 · 회사 열쇠가 들고, 명령 한 번 사이에는 안 바뀐다."""
        if self._main is None:
            body, _ = self._fetch(f"{self.server}{self.context}{MAIN_PAGE}")
            self._main = body.decode("utf-8", "replace")
        return self._main

    def session_alive(self) -> bool:
        """메인 화면이 200 이면 산 세션이다 — ``302 → logout.jsp`` 면 거짓. 문서를 건드리지 않는다."""
        try:
            self._main_page()
            return True
        except SessionExpired:
            return False

    @staticmethod
    def _list_params(search: str, period: str, folder: str, cabinet: str = "", *, box: str = "", sort: str = "",
                     direction: str = "desc", file_type: str = "") -> dict:
        """목록 · 건수 질의의 칸을 화면의 값에 대어 가려 짓는다 — 내 문서함 · 문서함 · 그 안 폴더 · 왼쪽 메뉴 목록 가운데 하나의 꼴이고, 못 쓸 값이면 ``ArgsError``."""
        if period not in PERIODS:
            raise ArgsError(f"기간(--period)은 화면의 값만 받는다: {' · '.join(PERIODS)} — 받은 값 {period!r}")
        if sort and sort not in SORTS:
            raise ArgsError(f"정렬(--sort)은 화면의 머리 글만 받는다: {' · '.join(SORTS)} — 받은 값 {sort!r}")
        if direction not in ("asc", "desc"):
            raise ArgsError(f"정렬 방향은 asc · desc 다 — 받은 값 {direction!r}")
        if file_type and file_type not in FILE_TYPES:   # 모르는 값은 서버가 거절 없이 0 건을 낸다 — 「없다」로 읽게 된다
            raise ArgsError(f"꼴(--type)은 화면의 모아보기만 받는다: {' · '.join(FILE_TYPES)} — 받은 값 {file_type!r}")
        shape = {"orderBy": SORTS.get(sort, ""), "sortDirection": direction, "fileType": FILE_TYPES.get(file_type, "ALL_FORMAT")}
        if box:
            if box not in BOXES:
                raise ArgsError(f"목록(--box)은 왼쪽 메뉴의 것만 받는다: {' · '.join(BOXES)} — 받은 값 {box!r}")
            refuse_box_with_place(box, cabinet, folder)
            return {**LIST_DEFAULTS, **shape, "formId": BOXES[box][0], "listKey": "", "searchValue": search, "searchPeriod": period}
        if cabinet:
            cabinet_key(cabinet)
            if folder:   # 문서함 안 폴더 — 왼쪽 나무에서 폴더를 누른 꼴(F_LIST_FOLDER · <문서함>_<폴더>). 그 폴더에 바로 든 문서만 온다
                folder_key(folder)
                return {**LIST_DEFAULTS, **shape, "formId": FOLDER_DOCS, "listKey": f"{cabinet}_{folder}", "searchValue": search,
                        "searchPeriod": period}
            return {**LIST_DEFAULTS, **shape, "formId": DEPT_DOCS, "listKey": f"{cabinet}_{cabinet}", "searchValue": search,
                    "searchPeriod": period}
        return {**LIST_DEFAULTS, **shape, "listKey": folder, "searchValue": search, "searchPeriod": period}

    def cabinets(self) -> list["Cabinet"]:
        """그 사람이 볼 수 있는 부서 · 프로젝트 문서함 — 메인 화면이 든 목록 그대로. 제 부서가 맨 앞이다."""
        page = self._main_page()
        own = OWN_CABINET.search(page)
        found, seen = [], set()
        for kind, key, name in CABINET_OPTION.findall(page):
            if key not in seen:
                seen.add(key)
                found.append(Cabinet(key, html.unescape(name).strip(), CABINET_KIND.get(kind.upper(), kind),
                                     bool(own and own.group(1) == key)))
        return sorted(found, key=lambda c: not c.own)

    def cabinet_by_key(self, key: str) -> Cabinet | None:
        """그 사람이 볼 수 있는 문서함 가운데 열쇠가 ``key`` 인 것 — 없으면 None."""
        return next((c for c in self.cabinets() if c.key == key), None)

    def cabinet_name(self, key: str) -> str:
        """그 열쇠의 문서함 이름 — 볼 수 있는 문서함에 없으면 빈 글자."""
        return getattr(self.cabinet_by_key(key), "name", "")

    def cabinet_of(self, text: str) -> Cabinet:
        """문서함 열쇠(``cab…``) 또는 이름으로 문서함 하나 — 열쇠는 그대로 받고(목록을 안 묻는다), 이름은 ``cabinets`` 에서 꼭 맞는
        이름을 먼저, 없으면 이름에 그 글이 든 것을 찾는다(대소문자 · 빈칸을 안 가린다). 여럿이 걸리거나 없으면 고르지 않고 후보를
        다 보이며 ``ArgsError`` — 엉뚱한 문서함에 올리거나 그 목록을 그 부서의 것으로 읽게 된다."""
        text = text.strip()
        if CABINET_ID.match(text):
            return Cabinet(text, "", "", False)
        if not text:
            raise ArgsError("문서함 이름이 비었다 — 이름(일부) · 열쇠(cab…) 가운데 하나를 준다")
        every = self.cabinets()
        hit = match_cabinets(text, every)
        if len(hit) == 1:
            return hit[0]
        raise ArgsError(cabinet_miss_word(text, hit, every))

    def version(self, object_id: str) -> str:
        """문서 정보 화면의 「최종 버전」 — 판을 올린 뒤 다음 판이 섰나 본다. 못 읽으면 빈 글자."""
        return self.doc_state(object_id).version

    def doc_state(self, object_id: str) -> DocState:
        """속성 화면을 한 번 읽어 판 · 잠금 · 보안등급 · 이름을 낸다 — 늘 새로 읽는다(판을 올린 뒤 바뀌기를 보는 자리가 부른다).
        등급 칸을 못 읽으면 ``security`` 가 None 이다 — 그 판정은 ``security`` · ``check_readable`` 이 든다."""
        raw = self._property_page(object_id)
        page = PropertyPage.parse(raw)
        lock = PROPERTY_LOCK.search(raw)
        security = page.security()
        title = page.inputs.get("MS_DOC_TITLE", "").strip()
        ext = page.inputs.get("MS_DOC_EXTENSION", "").strip()
        return DocState(property_value(raw, PROPERTY_VERSION), None if not lock else lock.group(1) == "T",
                        page.frame.get("lockOwnerName", ""), security, f"{title}.{ext}" if title and ext else title)

    def _property_page(self, object_id: str) -> str:
        """문서의 속성 화면 HTML 을 읽기 문을 지나는 GET 하나로 받는다."""
        object_id = _object_id(object_id)
        query = urllib.parse.urlencode({**PROPERTY_QUERY, "DOCID": object_id})
        body, _ = self._fetch(f"{self.server}{self.context}{PROPERTY_PAGE}?{query}")
        return body.decode("utf-8", "replace")

    def checkout(self, object_id: str) -> "Ticket":
        """편집 열기 첫 걸음 — 서버가 그 문서를 이 사람 이름으로 잠근다. 에이전트에 넘길 세 값을 낸다.

        ``MB_RTN_VALUE`` 가 참이면 실패 코드(``MS_MSG_CODE``)가 같이 와도 선다 — 화면도 그 값만 본다."""
        object_id = _object_id(object_id)
        data = self._ajax(EDIT_SERVICE, EDIT_FLAG, {"MS_OBJECT_ID": object_id}, edit=True)
        name = urllib.parse.unquote(str(data.get("MS_FILE_NAME", "") or data.get("MS_CLIENT_FILE_NAME", "")))
        ticket = Ticket(str(data.get("MS_DOC_ID", "")), str(data.get("MS_OBJECT_ID", "")), name)
        if not (ticket.doc_id and ticket.object_id and ticket.file_name):
            raise EcmError(f"편집 열기 답에 MS_DOC_ID · MS_OBJECT_ID · 파일 이름이 다 없다 — {CANCEL_NEXT.format(object_id=object_id)}")
        return ticket

    def cancel_checkout(self, object_id: str) -> None:
        """편집취소의 서버 걸음 — 화면이 에이전트 줄 앞에 보내는 요청. 이것만으로는 잠금이 안 풀렸다(쟀다) — ``cancel_edit`` 가 잇는다."""
        self._ajax(EDIT_SERVICE, CANCEL_FLAG, {"MS_OBJECT_ID": _object_id(object_id)}, edit=True)

    def list(self, *, search: str = "", page: int = 1, per_page: int = DEFAULT_PER_PAGE, period: str = DEFAULT_PERIOD,
             folder: str = "", cabinet: str = "", box: str = "", sort: str = "", direction: str = "desc", file_type: str = "") -> list[Doc]:
        """문서함의 한 쪽 — 새것부터. 비우면 내 문서함, ``cabinet`` 이면 그 부서 · 프로젝트 문서함(``cabinets`` 의 열쇠) · 거기에
        ``folder`` 까지 주면 그 폴더에 바로 든 문서, ``box`` 면 왼쪽 메뉴의 다른 목록(``BOXES``). 내 문서함만이면 ``folder`` 는
        목록 줄의 ``folder_id``. ``sort`` · ``file_type`` 은 화면의 머리 글 · 모아보기(``SORTS`` · ``FILE_TYPES``)."""
        if page < 1 or per_page < 1:
            raise ArgsError("쪽 번호 · 쪽마다 건수는 1 이상이다")
        params = {**self._list_params(search, period, folder, cabinet, box=box, sort=sort, direction=direction, file_type=file_type),
                  "pageNumber": str(page), "docCntPerPage": str(per_page)}
        data = self._ajax("DocList-service", "getDocList", params)
        rows = data.get("ML_DOC_LIST") or []
        log.info("목록 %d 건 (쪽 %d)", len(rows), page)
        return [_doc(row) for row in rows if isinstance(row, dict)]

    def count(self, *, search: str = "", period: str = DEFAULT_PERIOD, folder: str = "", cabinet: str = "", box: str = "",
              file_type: str = "") -> int:
        """목록과 같은 칸으로 건수(``MI_DOC_COUNT``)를 받는다 — 수가 아니면 ``EcmError``."""
        params = {**self._list_params(search, period, folder, cabinet, box=box, file_type=file_type), "isIncludeCntQry": "T"}
        data = self._ajax("DocList-service", "getDocCount", params)
        try:
            return int(str(data.get("MI_DOC_COUNT", "")).strip())
        except ValueError as exc:
            raise EcmError("건수(MI_DOC_COUNT)가 수가 아니다") from exc

    def view(self, object_id: str) -> Ticket:
        """열기 첫 걸음 — 에이전트에 보낼 값을 받는다. 파일은 아직 안 온다."""
        object_id = _object_id(object_id)
        data = self._ajax("OpenContents-service", "view", {"MS_OBJECT_ID": object_id, "formId": MY_DOCS})
        ticket = Ticket(str(data.get("MS_DOC_ID", "")), str(data.get("MS_OBJECT_ID", "")), str(data.get("MS_FILE_NAME", "")))
        if not (ticket.doc_id and ticket.object_id and ticket.file_name):
            raise EcmError("열기 답에 MS_DOC_ID · MS_OBJECT_ID · MS_FILE_NAME 이 다 없다")
        return ticket

    def current_key(self, object_id: str) -> str:
        """판이 오른 문서의 옛 열쇠 → 지금 판의 열쇠 — 화면의 「보기(최신버전)」와 같은 보기 첫 걸음(``MS_CURRENT_YN=T``). 파일은
        안 온다. 옛 열쇠는 옛 판을 가리키고 저절로 새 열쇠가 되지 않는다 — 메일 · 게시판에 남은 열쇠가 그렇다."""
        object_id = _object_id(object_id)
        data = self._ajax("OpenContents-service", "view", {"MS_OBJECT_ID": object_id, "formId": MY_DOCS, "MS_CURRENT_YN": "T"})
        now = str(data.get("MS_OBJECT_ID", ""))
        if not OBJECT_ID.match(now):
            raise EcmError("지금 판을 묻는 답에 문서 열쇠가 없다 — ECM 화면에서 그 문서를 연다")
        return now

    def history(self, object_id: str, *, page: int = 1, per_page: int = HISTORY_PER_PAGE, doc_key: str = "") -> tuple[int, list["Version"]]:
        """판 이력 — 속성 화면 「변경이력」 탭과 같은 두 읽기(건수 · 한 쪽). (모든 판의 수, 이 쪽의 판들 — 새 판부터). 문서 쪽 열쇠
        (``doc…``)로 묻는다 — 문서 열쇠(판마다 다르다)로 물으면 0 판이 온다."""
        if page < 1 or not 1 <= per_page <= HISTORY_PER_PAGE_MAX:
            raise ArgsError(f"쪽은 1 부터 · 쪽마다 판 수는 1 ~ {HISTORY_PER_PAGE_MAX}")
        key = doc_key or self.doc_key(object_id)
        return self._history_total(key, per_page), self._history_page(key, page, per_page)

    def _history_total(self, key: str, per_page: int) -> int:
        """판 이력의 건수 읽기 — 그 문서의 모든 판의 수(못 읽으면 0)."""
        head = self._json({**HISTORY_QUERY, "R_OBJECT_ID": key, "isIncludeCntQry": "T", "pageNumber": "0", "docCntPerPage": str(per_page)})
        return int((head or [{}])[0].get("MI_COUNT") or 0) if isinstance(head, list) else 0

    def _history_page(self, key: str, page: int, per_page: int) -> list["Version"]:
        """판 이력의 한 쪽 읽기 — 새 판부터. 답이 목록이 아니면 ``EcmError``."""
        rows = self._json({**HISTORY_QUERY, "R_OBJECT_ID": key, "isIncludeCntQry": "F", "pageNumber": str(page),
                           "docCntPerPage": str(per_page)}) or []
        if not isinstance(rows, list):
            raise EcmError(f"판 이력의 답이 목록이 아니다: {str(rows)[:200]}")
        return [Version(str(r.get("MS_OBJECT_ID", "")), str(r.get("MS_VERSION_LABEL", "")), r.get("MS_IS_CURRENT") == "CURRENT",
                        str(r.get("MS_CREATOR_NAME", "")), str(r.get("MS_CREATOR_DEPT_NAME", "")),
                        str(r.get("MS_CREATION_DATE", "")), str(r.get("MS_VERSION_DESC") or "").strip(),
                        str(r.get("MS_CONTENT_SIZE", ""))) for r in rows if isinstance(r, dict)]

    def security_log(self, object_id: str, doc_key: str = "") -> list[tuple[str, str, str, str]]:
        """보안등급 변경 이력 — (때, 바꾼 이, 앞 등급 이름, 뒤 등급 이름). 「변경이력」 탭의 보안등급 표와 같은 읽기."""
        key = doc_key or self.doc_key(object_id)
        rows = self._json({**SECURITY_LOG_QUERY, "ECM_DOC_ID": key, "isIncludeCntQry": "F", "pageNumber": "1",
                           "docCntPerPage": str(HISTORY_PER_PAGE_MAX)}) or []
        return [(str(r.get("MS_EVENT_DATE", "")), str(r.get("MS_USER_INFO", "")), str(r.get("MS_BEFORE_VALUE_DD", "")),
                 str(r.get("MS_AFTER_VALUE_DD", ""))) for r in rows if isinstance(r, dict)]

    def use_counts(self, object_id: str, doc_key: str = "") -> dict:
        """활용 건수 — 「활용」 탭의 첨부 · 열람 · 복사 · 추천 수."""
        rows = self._json({**USE_QUERY, "ECM_DOC_ID": doc_key or self.doc_key(object_id)}) or [{}]
        row = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
        return {word: row.get(field, "?") for field, word in USE_WORDS}

    def menu(self, object_id: str) -> list[tuple[str, bool]]:
        """그 문서에 지금 할 수 있는 것 — 우클릭 메뉴의 (이름, 켜졌나). 화면이 문서를 누를 때 묻는 조회 POST 하나다."""
        body = urllib.parse.urlencode({"formId": MY_DOCS, "itemObjIds": _object_id(object_id), "IsChorme": "T"}).encode("utf-8")
        data = _answer(*self._post(CONTEXT_QUERY, body))
        return [(str(m.get("MS_DD_VALUE", "")), m.get("MB_IS_ENABLED") in (True, "true"))
                for m in data.get("ML_MENU_LIST") or [] if isinstance(m, dict) and m.get("MS_DD_VALUE")]

    def checked_out_by_me(self, object_id: str) -> bool:
        """잠근 이가 나인가 — 편집취소 화면이 먼저 묻는 읽기(``checkuser``). 안 잠긴 문서도 거짓이다."""
        data = self._ajax(EDIT_SERVICE, "checkuser", {"MS_OBJECT_ID": _object_id(object_id)})
        return data.get("MS_IS_CHECKOUT_EQUAL") == "T"

    def notices(self) -> list[tuple[str, int]]:
        """왼쪽 「ECM 알림」 숫자 — 받은 · 보낸 권한 · 보안등급 · 검토 요청."""
        data = self._ajax("GetDashboardCount-service", "getNoticeCount", {})
        return [(word, int(data.get(field) or 0)) for field, word in NOTICE_WORDS]

    def personal_key(self) -> str:
        """내 사람 열쇠(``usr…``) — 메인 화면이 든다. 폴더 이름 찾기가 싣는다."""
        found = PERSONAL_OPTION.search(self._main_page())
        if not found:
            raise EcmError("메인 화면에서 내 사람 열쇠를 못 읽었다 — ECM 화면이 바뀌었을 수 있다")
        return found.group(1)

    def folders_named(self, name: str) -> list[tuple[str, str, str, str]]:
        """볼 수 있는 모든 문서함에서 이름에 그 글이 든 폴더 — 상세검색의 「폴더 검색」과 같은 요청 하나. (문서함 열쇠, 폴더 열쇠, 폴더
        이름, 서버가 준 경로 — 「문서함/폴더/…」). 경로는 가르지 않는다 — 문서함 · 폴더 이름에 / 가 들 수 있다(「관세/외국환…」)."""
        name = folder_name(name)
        body = urllib.parse.urlencode({"companyId": "", "userId": self.personal_key(), "value": name}).encode("utf-8")
        raw, kind = self._post(FOLDER_FIND_QUERY, body, path=JSON_READ)
        try:
            data = json.loads(json_text(raw, kind) or "{}")
        except json.JSONDecodeError as exc:
            raise EcmError("폴더 찾기의 답이 JSON 이 아니다 — 세션이 끊겼을 수 있다. 스킬 ep-login 으로 다시 받는다") from exc
        rows = data.get("jsonList") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise EcmError(f"폴더 찾기의 답에 jsonList 가 없다: {str(data)[:200]}")
        return [(str(r.get("MS_CABINET_ID", "")), str(r.get("MS_OBJECT_ID", "")), str(r.get("MS_FOLDER_NAME2", "")).strip(),
                 str(r.get("MS_FOLDER_NAME", "")).strip())
                for r in rows if isinstance(r, dict) and FOLDER_ID.match(str(r.get("MS_OBJECT_ID", "")))
                and CABINET_ID.match(str(r.get("MS_CABINET_ID", "")))]

    def search_all(self, query: "SearchQuery", *, page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> tuple[int, list["Hit"]]:
        """전사 검색 · 본문 검색 — 상세검색의 검색엔진 요청(``getDocListEcmEsSearch``) 하나. (모두 몇 건, 이 쪽의 줄). 내가 볼 수
        있는 문서만 온다."""
        check_search_page(page, per_page)
        docbox = ""
        if query.scope == SEARCH_MINE:
            found = DEPT_CABINETS.search(self._main_page())
            if not found:
                raise EcmError("메인 화면에서 내 문서함 목록(s_deptCabinets)을 못 읽었다 — ECM 화면이 바뀌었을 수 있다")
            docbox = found.group(1)
        body = search_body(query, docbox, page, per_page)
        data = _answer_search(*self._post(SEARCH_QUERY, body))
        return parse_hits(data)

    # ── 권한 — 속성 화면이 묻는 읽기와 그 화면의 저장 하나 ──

    def _json(self, query: dict):
        """``json.do`` 읽기 하나 — 답은 앞에 빈 줄이 붙은 JSON 배열(없으면 ``null``)이다."""
        body, kind = self._fetch(f"{self.server}{self.context}{JSON_READ}?{urllib.parse.urlencode(query)}")
        text = json_text(body, kind)
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise EcmError("ECM 의 답이 JSON 이 아니다 — 세션이 끊겼을 수 있다. 스킬 ep-login 으로 다시 받는다") from exc

    def company(self) -> str:
        """그 사람의 회사 열쇠(``com…``) — 메인 화면이 든다. 사람 · 조직 찾기가 싣는다."""
        found = COMPANY_VAR.search(self._main_page())
        if not found:
            raise EcmError("메인 화면에서 회사 열쇠를 못 읽었다 — ECM 화면이 바뀌었을 수 있다")
        return found.group(1)

    def property_page(self, object_id: str) -> "PropertyPage":
        """문서의 속성 화면 — 저장 몸이 실을 숨은 칸 · 화면의 갈래 값 · 권한 iframe 의 갈래 값."""
        return PropertyPage.parse(self._property_page(object_id))

    def security(self, object_id: str) -> Security:
        """문서의 보안등급 — 속성 화면 읽기 하나(파일을 안 받는다). 칸이 없거나 모르는 등급이면 ``SecurityUnread``. 세션이 끊긴 것과
        문서 열쇠의 꼴이 틀린 것(``ArgsError`` — 서버에 안 갔다)은 그대로 올린다 — 세션 · 열쇠를 고치면 읽히는 자리다."""
        try:
            page = self.property_page(object_id)
        except (SessionMissing, SessionExpired, ArgsError):
            raise
        except EcmError as exc:
            raise SecurityUnread(f"속성 화면을 못 읽었다 — {exc}") from exc
        security = page.security()
        if security is None:
            level = page.security_level()
            what = "없다" if not level else f"모르는 값 {level!r} 이다"
            raise SecurityUnread(f"속성 화면의 보안등급 칸({SECURITY_FIELD})이 {what} — 이 문서의 속성을 볼 수 없는 사람이거나 화면이 바뀌었다")
        return security

    def doc_key(self, object_id: str) -> str:
        """문서 열쇠(판마다 바뀐다)의 문서 쪽 열쇠(``doc…`` — 판이 올라도 같다) — 속성 화면의 숨은 칸 ``MS_DOC_ID``. 판이 오른 문서는
        ``"doc" + 문서 열쇠`` 가 아니다 — 그 꼴로 물으면 역할 목록이 빈 답(null)으로 와 권한 저장이 걸려 있던 명단을 지운다."""
        key = self.property_page(object_id).value("MS_DOC_ID")
        if not (key.startswith("doc") and OBJECT_ID.match(key[3:])):
            raise EcmError(f"속성 화면의 MS_DOC_ID 가 doc 열쇠 꼴이 아니다({key!r}) — ECM 화면이 바뀌었을 수 있다")
        return key

    def roles(self, object_id: str, doc_key: str = "") -> list["Grant"]:
        """그 문서에 걸린 역할 전부 — 권한 iframe 이 처음 그리는 그 목록(소유자는 안 든다). ``doc_key`` 는 속성 화면의 ``MS_DOC_ID`` —
        안 주면 속성 화면을 한 번 더 읽어 받는다."""
        rows = self._json({**ROLE_QUERY, "ECM_DOC_ID": doc_key or self.doc_key(object_id)})
        if rows is None:
            return []
        if not isinstance(rows, list):
            # 빈 명단으로 읽으면 저장이 걸려 있던 권한을 다 지운다 — 목록이 아닌 답은 읽기 실패다
            raise EcmError(f"역할 목록의 답이 목록이 아니다 — 지금 명단을 몰라 권한을 안 바꾼다: {str(rows)[:200]}")
        return [Grant(str(r.get("MS_ROLE", "")), str(r.get("MS_OBJECT_ID", "")), str(r.get("MS_USER_CLASS", "")),
                      str(r.get("MS_USER_NAME", "")), str(r.get("MS_DEPT_NAME", "")), str(r.get("MS_EMAIL_ID", "")),
                      str(r.get("MS_EMPLOYEE_NUMBER", ""))) for r in rows if isinstance(r, dict)]

    def favorites(self, object_id: str, doc_key: str = "") -> str:
        """그 문서가 든 즐겨찾기 폴더 — 화면이 저장 몸의 ``favFolderList`` 에 쉼표로 이어 싣는다."""
        rows = self._json({**FAVORITE_QUERY, "ECM_DOC_ID": doc_key or self.doc_key(object_id)}) or []
        return ",".join(str(r.get("MS_FAV_FOLDER_ID", "")) for r in rows if isinstance(r, dict) and r.get("MS_FAV_FOLDER_ID"))

    def people(self, name: str, company: str) -> list["Person"]:
        """이름(일부)으로 사람을 찾는다 — 권한 화면의 성명 탭과 같은 요청. 메일 ID · 사번으로는 안 찾는다(서버가 이름만 본다)."""
        name = person_name(name)
        rows = self._json({**PEOPLE_QUERY, "companyId": company, "value": name}) or []
        return [Person(str(r.get("MS_OBJECT_ID", "")), str(r.get("MS_NAME", "")), str(r.get("MS_DEPT_INFO", "")),
                       str(r.get("MS_DEPT", "")), str(r.get("MS_EMAIL_ID", "")), str(r.get("MS_EMPLOYEE_NUMBER", "")))
                for r in rows if isinstance(r, dict) and PERSON_ID.match(str(r.get("MS_OBJECT_ID", "")))]

    def organs(self, name: str, company: str) -> list["Organ"]:
        """부서 이름(일부)으로 부서를 찾는다 — 권한 화면의 조직 탭 찾기."""
        name = organ_name(name)
        rows = self._json({"ServiceName": ORGAN_SERVICE, "language": "ko", "companyId": company, **ORGAN_FIND,
                           "value": name}) or []
        return [_organ(r) for r in rows if isinstance(r, dict) and DEPT_CODE.match(str(r.get("MS_OBJECT_ID", "")))]

    def sub_organs(self, code: str, company: str) -> list["Organ"]:
        """그 부서 바로 아래 부서."""
        rows = self._json({"ServiceName": ORGAN_SERVICE, "language": "ko", "companyId": company, **ORGAN_SUBS,
                           "deptId": _dept_code(code)}) or []
        return [_organ(r) for r in rows if isinstance(r, dict) and DEPT_CODE.match(str(r.get("MS_OBJECT_ID", "")))]

    def members(self, code: str, company: str) -> list["Person"]:
        """그 부서에 바로 든 사람 — 화면이 조직을 칸에 옮길 때 펼치는 그 명단."""
        code = _dept_code(code)
        rows = self._json({"ServiceName": ORGAN_SERVICE, "language": "ko", "companyId": company, **ORGAN_USERS,
                           "deptId": code}) or []
        return [Person(str(r.get("MS_OBJECT_ID", "")), str(r.get("MS_NAME", "")),
                       str(r.get("MS_COMPANY_NAME", "")).split(" - ")[0].strip(), str(r.get("ECM_DEPT_CODE", "") or code),
                       str(r.get("MS_EMAIL_ID", "")), str(r.get("MS_EMPLOYEE_NUMBER", "")), str(r.get("MS_POSITION_NAME", "")))
                for r in rows if isinstance(r, dict) and PERSON_ID.match(str(r.get("MS_OBJECT_ID", "")))]

    def save_access(self, page: "PropertyPage", favorites: str, grants: list["Grant"], company: str) -> None:
        """속성 화면의 「수정하기」와 같은 저장 — 속성 칸은 화면이 실을 값 그대로, 권한은 ``grants`` 전체로 바꾼다."""
        self._save(page, property_save_body(page, favorites, company, grants, roles_changed=True), "권한")

    def save_props(self, page: "PropertyPage", favorites: str, grants: list["Grant"], company: str, props: "PropChange") -> None:
        """속성 화면의 「수정하기」와 같은 저장 — 이름 · 태그 · 완료일만 ``props`` 로 바꾸고, 권한 명단은 지금 그대로 싣는다."""
        self._save(page, property_save_body(page, favorites, company, grants, roles_changed=False, props=props), "속성")

    def _save(self, page: "PropertyPage", body: bytes, what: str) -> None:
        """속성 저장 POST 하나를 보내고 답의 문서 열쇠가 그 화면의 것인가 본다 — 다르면 ``what``(권한 · 속성)을 화면에서 보라고 진다."""
        data = _answer(*self._post(PROPERTY_SAVE_QUERY, body))
        if str(data.get("MS_OBJECT_ID", "")) != page.value("MS_OBJECT_ID"):
            raise EcmError(f"저장 답의 문서 열쇠가 다르다 — ECM 화면에서 그 문서의 {what}을 본다: {data.get('MS_MSG_DESC', '')}")


def charset_of(kind: str) -> str:
    """답의 ``Content-Type`` 이 든 문자셋 — 없으면 utf-8."""
    return (re.search(r"charset=([\w-]+)", kind, re.IGNORECASE) or [None, "utf-8"])[1]


def match_cabinets(text: str, every: list[Cabinet]) -> list[Cabinet]:
    """문서함 이름으로 걸리는 문서함들 — 꼭 맞는 이름이 먼저, 없으면 이름에 그 글이 든 것(대소문자 · 빈칸을 안 가린다)."""
    return [c for c in every if c.name == text] or [c for c in every if _loose(text) in _loose(c.name)]


def cabinet_miss_word(text: str, hit: list[Cabinet], every: list[Cabinet]) -> str:
    """문서함 하나로 안 풀린 이름의 말 — 여럿이 걸렸으면 그 후보를, 없으면 볼 수 있는 문서함을 다 보인다."""
    seen = "\n".join(f"  {c.name} · {c.kind}{' · 내 부서' if c.own else ''} · 열쇠 {c.key}" for c in (hit or every))
    if hit:
        return f"「{text}」 가 문서함 {len(hit)} 곳에 걸린다 — 고르지 않는다. 이름을 더 주거나 열쇠로 다시 준다:\n{seen}"
    return f"「{text}」 문서함이 없다 — 이 사람이 볼 수 있는 문서함:\n{seen or '  (없다)'}"


def json_text(raw: bytes, kind: str) -> str:
    """json.do 의 답 바이트를 글로 푼다 — ``Content-Type`` 의 문자셋으로(못 푸는 바이트는 바꿔) 앞뒤 빈 줄을 뗀다. 빈 답의 뜻은 읽는 쪽이 정한다."""
    return raw.decode(charset_of(kind), "replace").strip()


def folder_miss_word(path: tuple[str, ...], found: int, layer: list[Folder]) -> str:
    """폴더 경로의 한 마디가 그 층에 꼭 하나로 안 걸렸을 때의 말 — 몇 개였나(0 이면 없다)와 그 층의 폴더들."""
    seen = " · ".join(f.name for f in layer) or "(아래 폴더 없음)"
    what = "없다" if not found else f"{found} 개다"
    return f"「{path_word(path)}」 폴더가 그 자리에 {what} — 그 층의 폴더: {seen}"


def _answer(body: bytes, kind: str) -> dict:
    """ECM 의 답(앞에 빈 줄이 붙은 JSON)을 푼다 — ``MB_RTN_VALUE`` 가 참이 아니면 그 까닭으로 진다."""
    try:
        data = json.loads(body.decode(charset_of(kind)).strip())
    except (UnicodeDecodeError, LookupError, json.JSONDecodeError) as exc:
        raise EcmError(f"ECM 의 답이 JSON 이 아니다({kind or '꼴 모름'}) — 세션이 끊겼을 수 있다. 스킬 ep-login 으로 다시 받고 "
                       "그래도 같으면 이 말을 그대로 알린다") from exc
    if not isinstance(data, dict):
        raise EcmError("ECM 의 답이 JSON 객체가 아니다")
    if data.get("MB_RTN_VALUE") not in (True, "true"):
        code, desc = str(data.get("MS_MSG_CODE", "")), str(data.get("MS_MSG_DESC", ""))
        if code == VIEW_DENIED:
            raise EcmError(f"이 문서를 볼 권한이 없는 것 같다(ECM: {code} {desc}) — 문서함 화면에도 안 보이면 올린 사람에게 공유를 청한다")
        raise EcmError(f"ECM 이 거절했다: {code} {desc}".strip())
    return data


def _is_json_read(q: dict) -> bool:
    """속성 · 권한 화면이 묻는 json.do 읽기의 잰 꼴인가 — 판 이력 · 보안등급 변경 이력 · 활용 건수 · 역할 목록 · 즐겨찾기 · 이름 찾기 ·
    부서 찾기 · 하위 부서 · 부서원 아홉."""
    def same(base: dict, extra: set, checks: dict) -> bool:
        if set(q) != set(base) | extra or any(q.get(k) != v for k, v in base.items()):
            return False
        return all(check(q.get(k, "")) for k, check in checks.items())
    doc_key = lambda v: v.startswith("doc") and bool(OBJECT_ID.match(v[3:]))
    company = lambda v: bool(COMPANY_ID.match(v))
    named = lambda v: len(v.strip()) >= NAME_MIN
    dept = lambda v: bool(DEPT_CODE.match(v))
    organ = {"ServiceName": ORGAN_SERVICE, "language": "ko"}
    flag = lambda v: v in ("T", "F")
    digits = lambda v: v.isdigit() and len(v) <= 4
    paged = {"isIncludeCntQry": flag, "pageNumber": digits, "docCntPerPage": digits}
    return (same(HISTORY_QUERY, {"R_OBJECT_ID", *paged}, {"R_OBJECT_ID": doc_key, **paged})
            or same(SECURITY_LOG_QUERY, {"ECM_DOC_ID", *paged}, {"ECM_DOC_ID": doc_key, **paged})
            or same(USE_QUERY, {"ECM_DOC_ID"}, {"ECM_DOC_ID": doc_key})
            or same(ROLE_QUERY, {"ECM_DOC_ID"}, {"ECM_DOC_ID": doc_key})
            or same(FAVORITE_QUERY, {"ECM_DOC_ID"}, {"ECM_DOC_ID": doc_key})
            or same(PEOPLE_QUERY, {"companyId", "value"}, {"companyId": company, "value": named})
            or same({**organ, **ORGAN_FIND}, {"companyId", "value"}, {"companyId": company, "value": named})
            or same({**organ, **ORGAN_SUBS}, {"companyId", "deptId"}, {"companyId": company, "deptId": dept})
            or same({**organ, **ORGAN_USERS}, {"companyId", "deptId"}, {"companyId": company, "deptId": dept}))


ROLE_ROW = re.compile(r"<row><cell></cell><cell>([RSV])</cell><cell></cell><cell></cell><cell></cell><cell>(usr[0-9A-Fa-f]+)</cell>"
                      r"<cell>U</cell><cell>(com[0-9A-Fa-f]+)</cell></row>")


def _is_property_save(fields: dict) -> bool:
    """속성 저장 몸이 이 손이 잰 꼴인가 — 칸 이름이 화면의 것 그대로이고, 권한을 바꾸면(``isChangeRoleInfo=TRUE``) 명단은 권한 셋의
    사람 줄만 든다(안 바꾸는 저장도 화면처럼 지금 명단을 싣는다). 이 손이 바꾸는 이름 · 태그 · 완료일은 ``plan_props`` 가 먼저
    가리고, 바꾸지 않는 칸은 화면이 든 값 그대로 간다 — 여기서 다시 거르면 화면 밖에서 단 태그 하나가 그 문서의 권한 저장까지 막는다."""
    want = ({k for k, _ in SAVE_FROM_PAGE} | {k for k, _ in SAVE_TAIL_FROM_PAGE} | {k for k, _ in SAVE_WORKFLOW_FROM_PAGE}
            | {"SYSID", "isChangeRoleInfo", "roleList", "ecm_security_approve", "ecm_workflow_type", "tagList", "favFolderList",
               "ecm_auto_grant_flag", "ecm_ai_search_flag", "ecm_ori_ai_search_flag"})
    if set(fields) != want or fields.get("isChangeRoleInfo") not in ("TRUE", "F") or fields.get("sViewStatus") != "EDIT":
        return False
    roles = fields.get("roleList", "")
    head, tail = "<?xml version='1.0'?><rows>", "</rows>"
    if not (roles.startswith(head) and roles.endswith(tail)):
        return False
    middle = roles[len(head):len(roles) - len(tail)]
    return ROLE_ROW.sub("", middle) == "" and OBJECT_ID.match(fields.get("MS_OBJECT_ID", "")) is not None


def property_save_body(page: PropertyPage, favorites: str, company: str, grants: list[Grant], *, roles_changed: bool,
                       props: "PropChange | None" = None) -> bytes:
    """속성 화면의 getDocInfoData 가 짓는 몸 — 속성 칸은 그 화면의 값, 권한 명단은 ``grants`` 전체다. 화면은 권한 탭을 안 건드린
    저장에도 그 탭의 지금 명단을 싣고 ``isChangeRoleInfo`` 만 ``F`` 로 둔다 — ``roles_changed`` 가 그 칸이다. ``props`` 가 이름 · 태그 ·
    완료일을 바꾼다. 화면처럼 칸을 인코딩 없이 이어 붙이고 이름 둘만 encodeURIComponent 한다. 이어 붙이는 값에 칸을 가르는 글자(& · % · +)가
    들면 보내지 않는다."""
    if not COMPANY_ID.match(company):
        raise Refused(f"회사 열쇠 꼴이 아니다: {company!r}")
    outside = outside_roles(grants)
    bad = [g for g in grants if g in outside or not PERSON_ID.match(g.id)]
    if bad:
        raise Refused(f"권한 셋의 사람 줄만 싣는다 — 그 밖: {', '.join(f'{g.role}:{g.id}:{g.cls}' for g in bad)}")
    rows = "".join(f"<row><cell></cell><cell>{g.role}</cell><cell></cell><cell></cell><cell></cell><cell>{g.id}</cell>"
                   f"<cell>U</cell><cell>{company}</cell></row>"
                   for g in sorted(grants, key=lambda g: ROLE_ORDER.index(g.role)))
    title = props.title if props and props.title is not None else page.value("MS_DOC_TITLE")
    tags = props.tags if props and props.tags is not None else page_tags(page)
    # 완료일 — 바꾸면 그 값. 권한만 바꾸는 저장은 화면처럼 고르는 칸(ecm_EndDate · 늘 0001/01/01)을 싣고, 속성 저장은 지금 값(MS_DUE_DATE)을
    # 그대로 싣는다. 0001/01/01 을 실은 저장은 서버가 완료일을 안 바꾼다(쟀다 — SOURCES.md)
    due = (props.due if props.due is not None else (page.inputs.get("MS_DUE_DATE", "").strip() or SCREEN_NO_DUE)) if props \
        else page.value("ecm_EndDate")
    changed = {"MS_DOC_TITLE": title}
    if props and props.tags is not None:   # 화면은 태그를 tagList 로 싣고 숨은 칸 MS_TAG_LIST 는 그 화면의 옛 값이다 — 둘이 다르게 가지 않게 맞춘다
        changed["MS_TAG_LIST"] = ",".join(tags)
    pairs = [("SYSID", AGENT_SYSTEM)]
    for sent, field in SAVE_FROM_PAGE:
        value = changed.get(sent, page.value(field))
        pairs.append((sent, urllib.parse.quote(value, safe="-_.!~*'()") if sent in SAVE_ENCODED else value))   # 값은 파서가 이미 풀었다
    pairs.append(("isChangeRoleInfo", "TRUE" if roles_changed else "F"))
    pairs += [(sent, due if sent == "MS_DUE_DATE" else page.value(field)) for sent, field in SAVE_TAIL_FROM_PAGE]
    pairs.append(("roleList", f"<?xml version='1.0'?><rows>{rows}</rows>"))
    pairs += [(sent, page.value(field)) for sent, field in SAVE_WORKFLOW_FROM_PAGE]
    pairs += [("ecm_security_approve", page.value("ecm_security_approve")), ("ecm_workflow_type", page.value("ecm_workflow_type")),
              ("tagList", ",".join(tags)), ("favFolderList", favorites), ("ecm_auto_grant_flag", "F"), ("ecm_ai_search_flag", "F"),
              ("ecm_ori_ai_search_flag", "F")]
    raw = [k for k, v in pairs if k not in SAVE_ENCODED and RAW_BAD.search(v)]
    if raw:
        raise Refused(f"이어 붙일 칸({', '.join(raw)})에 칸을 가르는 글자(& · % · +)가 들어 보내지 않는다 — 사람이 화면에서 한다")
    return "&".join(f"{k}={v}" for k, v in pairs).encode("utf-8")


def page_tags(page: PropertyPage) -> tuple[str, ...]:
    """속성 화면이 든 태그 — 스크립트 갈래 값 ``sTagList``(쉼표로 이은 글 · 없으면 빈 글자나 "null")."""
    raw = page.vars.get("sTagList", "")
    return tuple(t.strip() for t in raw.split(",") if t.strip()) if raw and raw != "null" else ()


def search_body(query: SearchQuery, docbox: str, page: int, per_page: int) -> bytes:
    """화면의 검색 몸 — ``q=posmeta:{…}`` · 쪽 · 건수. 등급은 화면처럼 쉼표로 잇고 끝에도 쉼표를 붙인다."""
    check_search(query)
    meta = dict.fromkeys(SEARCH_FIELDS, "")
    meta.update(reqsysid="ecm", adv_search_type="b", sort="D", subfolder_yn="Y", docbox=docbox,
                subject=query.title.strip(), allintext=query.text.strip(), owner=query.owner.strip(), creator=query.creator.strip(),
                format=query.file_ext.strip().lower(), security="".join(f"{lv}," for lv in query.security))
    if meta["subject"]:
        meta["subject_operator"] = "OR" if query.any_word else "AND"
    if query.since:
        meta[SEARCH_DATE_FIELDS[query.date_field]] = f"{query.since}..{query.until}"
    q = "posmeta:" + json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
    return urllib.parse.urlencode({"q": q, "page_idx": str(page), "num": str(per_page), "backCategory": "doc",
                                   "sysId": "ecm"}).encode("utf-8")


def _is_search_body(fields: dict) -> bool:
    """전사 검색 몸의 잰 꼴인가 — 칸 다섯 · posmeta 의 칸 이름이 화면의 것."""
    if set(fields) != {"q", "page_idx", "num", "backCategory", "sysId"} or fields["backCategory"] != "doc" or fields["sysId"] != "ecm":
        return False
    if not (fields["page_idx"].isdigit() and fields["num"].isdigit() and fields["q"].startswith("posmeta:")):
        return False
    try:
        meta = json.loads(fields["q"][len("posmeta:"):])
    except json.JSONDecodeError:
        return False
    return isinstance(meta, dict) and set(meta) <= set(SEARCH_FIELDS) and meta.get("reqsysid") == "ecm"


def _is_dup_body(fields: dict) -> bool:
    """등록 화면의 같은 이름 찾기 몸인가 — 칸 셋 그대로."""
    return set(fields) == {"folderID", "title", "fileExt"}


def _is_register_body(fields: dict) -> bool:
    """등록 화면의 저장 몸인가 — 서비스와 갈래 칸. 몸의 값은 ``register_body`` 가 짓기 전에 가린다."""
    return fields.get("ServiceName") == REGISTER_SERVICE and fields.get("register") == "register"


def _is_context_body(fields: dict) -> bool:
    """우클릭 메뉴 묻기 몸인가 — 칸 셋 · 내 문서함 · 문서 열쇠 하나."""
    return (set(fields) == {"formId", "itemObjIds", "IsChorme"}
            and fields["formId"] == MY_DOCS and OBJECT_ID.match(fields["itemObjIds"]) is not None)


def _is_folder_find_body(fields: dict) -> bool:
    """폴더 이름 찾기 몸인가 — 칸 셋 · 사람 열쇠 · 두 글자부터."""
    return (set(fields) == {"companyId", "userId", "value"} and PERSON_ID.match(fields["userId"]) is not None
            and len(fields["value"].strip()) >= NAME_MIN)


def _answer_search(body: bytes, kind: str) -> dict:
    """검색 답 — ``MB_RTN_VALUE`` 가 없고 ``gsa_error_key`` 가 까닭을 든다(빈 글자면 됐다)."""
    try:
        data = json.loads(body.decode(charset_of(kind), "replace").strip())
    except json.JSONDecodeError as exc:
        raise EcmError("검색 답이 JSON 이 아니다 — 세션이 끊겼을 수 있다. 스킬 ep-login 으로 다시 받는다") from exc
    if not isinstance(data, dict):
        raise EcmError("검색 답이 JSON 객체가 아니다")
    error = str(data.get("gsa_error_key") or "")
    if error == "NO_AUTH":
        raise EcmError("검색 시스템 사용 권한이 없다고 ECM 이 답했다 — 사람이 ECM 화면의 검색에서 찾는다")
    if error:
        raise EcmError(f"검색 시스템이 거절했다: {error}")
    return data


def parse_hits(data: dict) -> tuple[int, list[Hit]]:
    """검색 답의 ``gsa_data_key``(XML 글) → (모두 몇 건, 줄들). 줄의 칸은 ``<MT N="이름" V="값"/>`` 이다."""
    raw = str(data.get("gsa_data_key") or "")
    total = re.search(r"<M>(\d+)</M>", raw)
    hits = []
    for row in re.findall(r"<R\b[^>]*>(.*?)</R>", raw, re.S):
        meta = {n: html.unescape(v) for n, v in re.findall(r'<MT\s+N="(\w+)"\s+V="([^"]*)"\s*/>', row)}
        if OBJECT_ID.match(meta.get("R_OBJECT_ID", "")):
            hits.append(Hit(meta["R_OBJECT_ID"], meta.get("TITLE", ""), meta.get("ECM_FILE_FORMAT", ""), meta.get("AUTHOR", ""),
                            meta.get("ECM_DEPT_NAME", ""), meta.get("ECM_SECURITY_LEVEL", ""), meta.get("ECM_MODIFY_DATE", "")))
    return (int(total.group(1)) if total else 0), hits


def _organ(row: dict) -> Organ:
    """조직 답의 줄 하나 → ``Organ`` — 수 칸이 수가 아니면 0 으로 둔다."""
    def num(name):
        try:
            return int(str(row.get(name, 0)).strip() or 0)
        except ValueError:
            return 0
    return Organ(str(row.get("MS_OBJECT_ID", "")), str(row.get("MS_DEPT_NAME", "")), str(row.get("MS_UPPER_DEPT_NAME", "")),
                 str(row.get("MS_CABINET_ID", "")), num("MS_USER_ID"), num("MS_CHILD_ID"))


def _is_property_read(query: dict) -> bool:
    """속성 화면 읽기의 잰 꼴인가 — 질의가 ``PROPERTY_QUERY`` 그대로에 문서 열쇠(``DOCID``) 하나."""
    rest = dict(query)
    docid = rest.pop("DOCID", "")
    return rest == PROPERTY_QUERY and OBJECT_ID.match(docid) is not None


def _refuse_unmeasured_ajax(query_text: str, url: str) -> None:
    """ajax 읽기 질의가 닫힌 목록(``READS``)의 잰 꼴이 아니면 그 까닭으로 ``Refused`` — 서비스 · 갈래 하나 · 실을 수 있는 칸 ·
    문서함(formId) · 폴더 열쇠 · 지금 판 갈래 · 문서 열쇠 꼴."""
    pairs = urllib.parse.parse_qsl(query_text, keep_blank_values=True)
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise Refused(f"같은 칸이 두 번 든 주소라 묻지 않는다: {url}")
    query = dict(pairs)
    service = query.pop("ServiceName", None)
    if service not in READS:
        raise Refused(f"읽기로 잰 서비스가 아니라 묻지 않는다({service}): {url}")
    flags, allowed = READS[service]
    chosen = [f for f in flags if f in query]
    if len(chosen) != 1 or query.pop(chosen[0]) != "true":
        raise Refused(f"그 서비스의 읽기 갈래가 하나로 서지 않아 묻지 않는다: {url}")
    extra = set(query) - allowed
    if extra:
        raise Refused(f"읽기로 잰 칸 밖의 칸({', '.join(sorted(extra))})이 들어 묻지 않는다: {url}")
    if "formId" in query and query["formId"] not in READ_FORMS:
        raise Refused(f"잰 문서함(formId) 밖이라 묻지 않는다({query['formId']}): {url}")
    if query.get("formId") == FOLDER_DOCS and not FOLDER_KEY.match(query.get("listKey", "")):
        raise Refused(f"폴더 목록(F_LIST_FOLDER)은 listKey 가 <문서함>_<폴더> 꼴일 때만 묻는다: {url}")
    if "MS_CURRENT_YN" in query and (service != "OpenContents-service" or query["MS_CURRENT_YN"] != "T"):
        raise Refused(f"MS_CURRENT_YN 은 보기 갈래의 T 하나만 잰 꼴이다: {url}")
    if "MS_OBJECT_ID" in query and not OBJECT_ID.match(query["MS_OBJECT_ID"]):
        raise Refused(f"문서 열쇠 꼴이 아니라 묻지 않는다: {url}")


def _is_folder_query(query: str, url: str) -> bool:
    """폴더 나무 한 층의 잰 꼴인가 — 문서함 바로 아래(MENU_DEPT · MENU_PROJECT + cab…) 또는 폴더 아래(F_LIST_FOLDER + cab…_fdr…)."""
    q = _single_query(query, url)
    if q.get("ServiceName") != FOLDER_SERVICE or set(q) != {"ServiceName", "menuType", "upperKey"}:
        return False
    if q["menuType"] in FOLDER_ROOT_TYPES:
        return bool(CABINET_ID.match(q["upperKey"]))
    return q["menuType"] == FOLDER_TYPE and bool(FOLDER_KEY.match(q["upperKey"]))


# 잰 POST — (경로, 질의, 몸의 꼴). 등록 화면의 둘 · 속성 저장 · 조회지만 POST 인 셋(우클릭 메뉴 · 전사 검색 · 폴더 이름 찾기)
POST_SHAPES = ((AJAX, DUP_QUERY, _is_dup_body), (AJAX, REGISTER_QUERY, _is_register_body),
               (AJAX, PROPERTY_SAVE_QUERY, _is_property_save), (AJAX, CONTEXT_QUERY, _is_context_body),
               (AJAX, SEARCH_QUERY, _is_search_body), (JSON_READ, FOLDER_FIND_QUERY, _is_folder_find_body))


def _size_label(size: int) -> str:
    """화면의 byteToKB — 등록 몸의 크기 칸은 「15KB 」 꼴이다(끝에 빈칸 하나)."""
    if size <= 0:
        return "0KB "
    return f"{max(1, round(size / 1024)):,}KB "


def register_body(*, folder: str, title: str, ext: str, size: int, server_path: str, server_file: str, security: str,
                  open_flag: str) -> bytes:
    """화면의 「컨텐츠 등록」 저장 몸을 짓는다 — 값이 잰 꼴(폴더 열쇠 · 보안 짝 · 확장자 · 서버 임시 자리) 밖이면 ``Refused``."""
    name = urllib.parse.quote(title.replace("&", "&amp;"), safe="-_.!~*'()")   # 화면의 encodeURIComponent
    row = (f"<?xml version='1.0'?><rows><row><cell>1</cell><cell>{name}</cell><cell>{ext}</cell>"
           f"<cell>{_size_label(size)}</cell><cell>{REGISTER_ROW}</cell><cell>{REGISTER_ROW}</cell>"
           f"<cell>{server_path}</cell><cell>{server_file}</cell></row></rows>")
    fields = [("register", "register"), ("fileList", row), ("roleList", ""), ("ServiceName", REGISTER_SERVICE),
              ("SYSID", ""), ("ACTID", ""), ("ecm_doc_type", DOC_TYPE_GENERAL), ("ecm_folder_id", folder),
              ("ecm_folder_name", ""), ("ecm_security_level", security), ("ecm_open_flag", open_flag),
              ("ecm_retention_period", ""), ("ecm_doc_status", DOC_STATUS_DRAFT), ("ecm_due_date", NO_DUE_DATE),
              ("ecm_workflow_Process", "F"), ("ecm_workflowApproveUserId", ""), ("ecm_workflowRequestComment", ""),
              ("favFolderList", ""), ("s_DocuType", ""), ("tagList", ""), ("reCall", "0"),
              ("ecm_auto_grant_flag", "F"), ("ecm_ai_search_flag", "F")]
    # 화면은 이 몸을 칸마다 인코딩하지 않고 이어 붙여 보낸다(서버가 그 꼴을 받는다) — 그래서 이름은 위에서 인코딩하고, 나머지 값은
    # 꼴을 잰 열쇠 · 짝 · 상수만 든다. 에이전트가 준 서버 자리에 & · + · % 가 들면 칸이 갈리거나 풀리므로 막는다
    if not (FOLDER_ID.match(folder) and (security, open_flag) in SECURITY_PAIRS and ext.isalnum()
            and SERVER_NAME.match(server_path) and SERVER_NAME.match(server_file)):
        raise Refused("등록 몸의 값이 잰 꼴(폴더 열쇠 · 보안 짝 · 확장자 · 서버 임시 자리) 밖이다 — 보내지 않는다")
    return "&".join(f"{k}={v}" for k, v in fields).encode("utf-8")


def _single_query(query: str, url: str) -> dict:
    """질의를 칸 → 값으로 푼다. 같은 칸이 두 번 들면 막는다 — 서버는 첫 값을, 견주는 쪽은 끝 값을 읽어 다른 요청이 나간다."""
    pairs = urllib.parse.parse_qsl(query, keep_blank_values=True)
    if len(pairs) != len({k for k, _ in pairs}):
        raise Refused(f"같은 칸이 두 번 든 주소라 묻지 않는다: {url}")
    return dict(pairs)


def _doc(row: dict) -> Doc:
    """목록 답의 줄 하나 → ``Doc`` — 칸마다 앞에 댄 이름부터 찬 값을 쓴다."""
    def get(*names: str) -> str:
        for name in names:
            value = row.get(name)
            if value not in (None, ""):
                return str(value)
        return ""
    # 안 잠긴 줄의 MS_LOCK_USER_ID 는 빈칸 하나(" ")로 온다 — 다듬지 않으면 모든 줄이 잠긴 것으로 보인다
    return Doc(get("MS_OBJECT_ID"), get("MS_DOC_ID"), get("MS_OBJECT_NAME"), get("MS_DOC_EXTENSION"), get("MS_FILE_SIZE"),
               get("MS_DOC_VERSION"), get("MS_REG_DATE"), get("MS_MODIFY_DATE_EXT", "MS_MODIFY_DATE"), get("MS_FOLDER_PATH"),
               get("MS_FOLDER_ID"), get("MS_OWNER_NAME"), get("MS_SECURITY_LEVEL"),
               get("MS_LOCK_OWNER_NAME", "MS_LOCK_USER_ID").strip(), get("MS_CABINET_NAME"), get("MS_SHARED_USER_NAME"),
               get("MS_ROLE") if row.get("MS_SHARED_USER_NAME") else "", get("MS_REQUEST_USER_NAME"), get("MS_REQUEST_DATE"),
               get("MS_WORKFLOW_STATUS") if row.get("MS_REQUEST_USER_NAME") else "", get("MS_DELETE_DATE"), get("MS_EVENT_DATE"))
