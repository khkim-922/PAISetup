"""사내 문서함(ECM)에서 문서를 찾고 읽고, 사람이 확인한 한 편은 편집해 다음 판으로 올리거나 새 문서로 올리고, 문서의 권한을
주고 거두는 손. 표준 라이브러리와 곁의 ``ecm_base.py``(값 · 예외 · 기록의 꼴) · ``ecm_server.py``(서버 이음) ·
``ecm_agent.py``(에이전트 이음) · ``default_app.py`` · ``office_doc.ps1``(``close_view.ps1`` · ``change_doc.ps1`` 이 싣는다) ·
``close_acrobat.ps1`` · ``checkin_window.ps1``, 형제 스킬 ep-login 의 ``ep_session.py``(스킬 홈에 나란히 깔린 ``../../ep-login/scripts/``)를
쓴다. 차례와 막는 까닭은 ``references/DESIGN.md``, 서버의 주소와 꼴은 ``references/SOURCES.md`` 「사내 ECM 에서 잰 것」이 든다.

⚠ 에이전트는 받은 파일을 기본 앱으로 **화면에 띄우고**, 편집 열기는 동료도 쓰는 문서를 서버에서 잠근다 — 사람이 보는 대화에서만
쓰고, 편집은 사람이 그 문서를 확인한 뒤에만 부른다. 바꾸는 요청은 편집 열기 · 편집취소 · 등록 · 속성(권한 · 이름 · 태그 · 완료일) 저장만 짓고 그 밖은 서버에 닿기 전에
``Refused`` 로 막는다. 되돌리기 어려운 끝(등록 · 판 올리기 · 권한 · 속성 저장)은 미리 보기가 낸 확인 열쇠로만 간다.

어떻게 부르나::

        import ecm

        box = ecm.Ecm.from_env()                         # 세션 파일에 ECM 쿠키가 없으면 SessionMissing
        docs = box.list(search="보고서")                  # 내 문서함 — Doc 목록
        dept = box.cabinets()[0]                          # 제 부서 문서함이 맨 앞
        docs = box.list(search="계획", cabinet=dept.key)  # 부서 문서함
        got = ecm.read_document(box, ecm.Agent.from_env(), docs[0].object_id)
        print(got.text)                                  # 글자 · got.summary 는 읽는 손의 한 줄(「글 밖」 셈)

        folder = box.resolve_folder(dept.key, "기획 > 보고")   # 폴더 경로(화면의 꼴) → (경로, Folder)
        plan = ecm.plan_register(box, path, cabinet=dept.key, folder=folder[1].id, security="2A", open_flag="F")
        new = ecm.register_document(box, ecm.Agent.from_env(), path, cabinet=dept.key, folder=folder[1].id,
                                    security="2A", open_flag="F", confirm=plan.token)   # 사람이 미리 보기를 확인한 열쇠로만
        changes = ecm.Changes(replace=(("120 억", "150 억"),))
        opened = ecm.edit_document(box, ecm.Agent.from_env(), docs[0].object_id, changes=changes)   # 바꿀 것을 잠그기 전에 가린다
        ecm.change_document(opened.path, ecm.OFFICE_BY_EXT[opened.ticket.ext], changes)   # 열린 창에서 고치고 저장한다
        pending = ecm.prepare_checkin(box, opened.path, docs[0].object_id, "고친 내용 한 줄")   # 서버를 안 바꾼다 — 열쇠를 낸다
        done = ecm.checkin_document(box, opened.path, docs[0].object_id, "고친 내용 한 줄", confirm=pending.token)
        print(done.version_before, "→", done.version_after)

        plan = ecm.plan_access(box, docs[0].object_id, grant=[("read", "org:T90001"), ("copy", "홍길동/gdhong")],
                               revoke=["김철수"])               # 서버를 안 바꾼다 — plan.added · removed · moved 를 사람에게 보인다
        got = ecm.apply_access(box, plan, plan.token)       # 사람이 확인한 열쇠로만 · 다시 읽은 명단을 낸다

    명령줄은 ``python -X utf8 ecm.py [--session <세션 파일>] <명령>`` 이다. 명령은 손가락의 표(``FINGERS``)가 든다 — 인자 · 세션이
    드나 · 바꾸는가 · ``--help`` 의 지도가 다 그 표에서 선다(``python -X utf8 ecm.py --help``).

    깔린 자리에서 이 파일을 싣는 앱(메일 비서)이 부르는 이름 — ``Ecm``(``view`` · ``security``) · ``Agent``(``download_view``) ·
    ``Security.ask_before_ai`` · ``close_window`` · ``viewer_of`` · ``default_app`` · ``url_from_env`` · ``kept_text`` · ``keep_text`` ·
    ``TEXT_SPLIT`` · 예외 ``EcmError`` · ``SessionMissing`` · ``SessionExpired`` · ``AgentError``. 이 이름과 꼴을 바꾸면 그 앱이 싣는
    자리에서 멈춘다.

무엇을 내나
    목록은 ``Doc``, 문서함은 ``Cabinet``, 문서 하나의 속성 화면은 ``DocState``(판 · 잠금 · 등급 · 이름), 열기 · 편집 열기는
    ``Opened``(받은 파일 경로 · 문서 표 · 기본 앱), 읽기는 ``ReadResult``, 고치기는 ``Changed``(고친 것 · 저장했나), 올리기 미리
    보기는 ``CheckinPlan``, 올리기는 ``CheckedIn``(앞 판 · 뒤 판 · 고른 판), 폴더는 ``Folder``, 새 문서 미리 보기는 ``RegisterPlan``,
    새 문서는 ``Registered``(열쇠 · 이름 · 판), 보안등급은 ``Security``(등급 · 공개 · 핵심기술 · 이름 · 물어야 하나), 권한은
    ``Grant`` · ``Person`` · ``Organ`` · ``AccessPlan``(앞 명단 · 뒤 명단 · 더함 · 뺌 · 옮김 · 확인 열쇠)이다. 미리 보기의 ``token`` 이
    확인 열쇠다 — 그 사이 문서 · 명단 · 파일이 바뀌면 열쇠가 달라져 바꾸는 끝이 안 나간다.

    명령줄의 종료 값은 사내 앱 명령이 함께 쓰는 한 표다 — 값은 형제 스킬 ep-login 의 ``ep_command`` 가 들고, 뜻은 이렇다:
    ``EXIT_OK`` 됨 · ``EXIT_FAIL`` 실패(메시지 그대로 알린다) · ``EXIT_ARGS`` 준 값이 틀렸거나 아무것도 가리키지 않는다(argparse 와
    ``ArgsError`` — 아무것도 안 건드렸다. 메시지대로 고쳐 다시 부른다. 서버 없이 가릴 수 있는 값은 ``precheck`` 가 세션보다 먼저
    가린다) · ``EXIT_SESSION`` 세션이 없거나 끊겼다(스킬 ep-login 으로 다시
    받는다) · ``EXIT_STALE`` 확인 열쇠가 지금과 다르다(``Stale`` — 미리 본 뒤 바뀌어 아무것도 안 바꿨다. 미리 보기를 다시 사람에게
    보인다) · ``EXIT_DEFAULT_APP`` 사람이 그 확장자의 기본 앱을 한 번 골라야 한다(메시지가 할 일을 든다) · ``EXIT_CLASSIFIED`` 기밀 ·
    핵심기술 문서이거나 등급을 못 읽어 사람에게 묻기 전에 멈췄다(메시지가 물을 것을 든다 — 답을 받은 뒤에만 ``--ai-ok``).

    갈래 예외는 ``EcmError`` 아래에 선다 — ``SessionMissing`` · ``SessionExpired`` · ``Refused`` · ``AgentError`` · ``ReadError`` ·
    ``Classified`` · ``SecurityUnread`` · ``ArgsError`` · ``Stale``. ``default_app.DefaultAppNeeded`` · ``ValueError``(확장자 꼴) ·
    ``OSError`` · ``subprocess.TimeoutExpired`` 는 그 아래가 아니다 — 명령줄은 따로 잡아 ``EXIT_DEFAULT_APP`` · ``EXIT_FAIL`` 로 내고,
    손으로 부르는 쪽도 따로 잡아야 한다.

    부작용 — 에이전트가 받은 파일(``ECM_DOCS_ROOT`` 아래)은 지우지도 옮기지도 않는다. 명령줄의 ``read`` 는 뽑은 글자를
    ``text_dir()`` 에 문서 열쇠마다 한 장(``.md``)으로 남기고, 같은 열쇠는 그 장으로 답하며, 남긴 장을 지우지 않는다.

환경변수(``from_env``)
    ``ECM_URL``           ECM 주소 — ``…/ECM`` 까지                         기본 ``DEFAULT_URL``(ep-login ``places.json``)
    ``MAILBOX_COOKIES``   세션 파일(Playwright 저장 상태) — ``--session`` 을 안 줄 때만. 기본 자리는 없다 — 받는 손(스킬
                          ep-login)이 정하고 부르는 쪽이 넘긴다
    ``ECM_AGENT_URL``     ECM 에이전트 웹소켓                               기본 ``ws://localhost:8383/``
    ``ECM_DOCS_ROOT``     에이전트가 받은 파일을 두는 자리                   기본 ``DEFAULT_DOCS_ROOT``(곁의 스킬 drm-office-read 의
                                                                             ``scripts/places.json`` 의 ``ecm_docs_root``)
    ``ECM_DRM_READER``    글자를 뽑는 손                                     기본 ``DEFAULT_READER``(곁의 스킬 drm-office-read 의
                                                                             ``scripts/read-drm.ps1``)
    ``ECM_TEXT_DIR``      read 가 뽑은 글자를 남기는 자리                    기본 ``~/.company-ecm-text``
    문서함 열쇠 · 계정은 환경변수로 받지 않는다 — 그 사람의 ECM 메인 화면과 에이전트의 폴더에서 읽는다.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import default_app  # noqa: E402 — 곁의 파일이다
from ecm_base import (ACCESS_OF_WORD, ACCESS_ROLES, ACROBAT, ACROBAT_CLOSE_SCRIPT, ACROBAT_PROGID, AGENT_FILE_SUFFIX, AI_OK_FLAG,
    ASK_BEFORE_AI, AUDIENCE, AgentError, ArgsError, BOXES, CANCEL_FIND_WAIT, CANCEL_NEXT, CANCEL_WAIT, CHANGE_DONE, CHANGE_NOT_FOUND,
    CHANGE_REFUSED, CHANGE_SCRIPT, CHANGE_TIMEOUT, CHECKIN_ATTACH_TRIES, CHECKIN_REATTACH_WAIT, CHECKIN_SCRIPT, CHECKIN_WAIT,
    CHECKOUT_FOLDER, CLOSE_EXIT, CLOSE_SCRIPT, Cabinet, Classified, DATE_TEXT, DEFAULT_PERIOD, DEFAULT_PER_PAGE, DEFAULT_READER, Doc, EXITS, EXIT_ARGS, EXIT_CLASSIFIED, EXIT_DEFAULT_APP, EXIT_FAIL, EXIT_OK, EXIT_SESSION, EXIT_STALE, EcmError, FILE_TYPES,
    FIND_ONLY_DESC, FOLDER_SEP, GATE_EDIT, GATE_RECEIVE, Grant, HISTORY_PER_PAGE, INSERT_FAMILY, KEPT_SOURCE_WORD, KEPT_WHEN_WORD,
    LINE_BREAK, NOT_HERE, OBJECT_ID, OFFICE_BY_EXT, OFFICE_OF_PROGID, Opened, Organ, PERIODS, POLL, Person,
    PropChange, PropertyPage, READER_GATE_FLAG, READ_TIMEOUT, ReadError, ReadResult, Registered, SCREEN_NO_DUE, SEARCH_COMPANY,
    SEARCH_DATE_FIELDS, SEARCH_MINE, SECURITY_PAIRS, SORTS, SearchQuery, Security, SecurityUnread, SessionExpired, SessionMissing, Stale,
    TAG_MAX, TAG_WORD, TEXT_DIR, TEXT_DIR_ENV, TEXT_EXT, TEXT_SPLIT, UNCHANGED_WAIT, VERSION_POLL, VERSION_WAIT, WINDOW_WAIT,
    WORD_FIND_MAX, _object_id, agent_docs_root, cabinet_key, check_person_spec, check_search, check_search_page, check_title, folder_key,
    folder_name, grants_key, level_name, organ_name, outside_roles, path_word, refuse_box_with_place, person_name, session_path, spec_kind, token, url_from_env, SPEC_CODE, SPEC_ORGAN,
    SPEC_PERSON)
from ecm_base import AJAX as AJAX
from ecm_base import CONTEXT_QUERY as CONTEXT_QUERY
from ecm_base import FOLDER_FIND_QUERY as FOLDER_FIND_QUERY
from ecm_base import JSON_READ as JSON_READ
from ecm_base import Refused as Refused
from ecm_base import SEARCH_QUERY as SEARCH_QUERY
from ecm_server import Ecm, page_tags
from ecm_agent import Agent
# 이 파일 이름으로 싣는 쪽이 써 온 이름 — 자리를 옮긴 것도 여기서 그대로 내놓는다(이 파일은 안 쓴다)
from ecm_base import (NAME_MIN as NAME_MIN, ORG_PREFIX as ORG_PREFIX, ABSENT_FIELD as ABSENT_FIELD, AGENT_ACTION_EDIT as AGENT_ACTION_EDIT, AGENT_ACTION_VIEW as AGENT_ACTION_VIEW,
    AGENT_CANCEL as AGENT_CANCEL, AGENT_FIELD_SEPARATOR as AGENT_FIELD_SEPARATOR, AGENT_OK as AGENT_OK, AGENT_SYSTEM as AGENT_SYSTEM,
    AGENT_TIMEOUT as AGENT_TIMEOUT, AGENT_UPLOAD as AGENT_UPLOAD, CABINET_ID as CABINET_ID, CABINET_KIND as CABINET_KIND,
    CABINET_OPTION as CABINET_OPTION, CANCEL_FLAG as CANCEL_FLAG, CLASSIFIED_LEVELS as CLASSIFIED_LEVELS, COMPANY_ID as COMPANY_ID,
    CORE_VAR as CORE_VAR, DEFAULT_AGENT as DEFAULT_AGENT, DEFAULT_DOCS_ROOT as DEFAULT_DOCS_ROOT, DEFAULT_URL as DEFAULT_URL,
    DEPT_CABINETS as DEPT_CABINETS, DEPT_CODE as DEPT_CODE, DEPT_DOCS as DEPT_DOCS, DOCS_ROOT_ENV as DOCS_ROOT_ENV,
    DOC_STATUS_DRAFT as DOC_STATUS_DRAFT, DOC_TYPE_GENERAL as DOC_TYPE_GENERAL, DRM_PLACES_FILE as DRM_PLACES_FILE,
    DRM_READ_SCRIPTS as DRM_READ_SCRIPTS, DUP_QUERY as DUP_QUERY, DocState as DocState, EDIT_FLAG as EDIT_FLAG,
    EDIT_SERVICE as EDIT_SERVICE, ELEMENT_ID as ELEMENT_ID, EP_LOGIN_SCRIPTS as EP_LOGIN_SCRIPTS, FAVORITE_QUERY as FAVORITE_QUERY,
    FILE_TIMEOUT as FILE_TIMEOUT, FOLDER_DOCS as FOLDER_DOCS, FOLDER_ID as FOLDER_ID, FOLDER_KEY as FOLDER_KEY,
    FOLDER_ROOT_TYPES as FOLDER_ROOT_TYPES, FOLDER_SERVICE as FOLDER_SERVICE, FOLDER_TYPE as FOLDER_TYPE,
    FOLDER_WALK_MAX as FOLDER_WALK_MAX, Folder as Folder, HISTORY_PER_PAGE_MAX as HISTORY_PER_PAGE_MAX, HISTORY_QUERY as HISTORY_QUERY,
    HTTP_TIMEOUT as HTTP_TIMEOUT, Hit as Hit, LIST_DEFAULTS as LIST_DEFAULTS, LOCK_PREFIX as LOCK_PREFIX, MAIN_PAGE as MAIN_PAGE,
    MEASURED_FRAME as MEASURED_FRAME, MEASURED_PAGE as MEASURED_PAGE, MEASURED_VARS as MEASURED_VARS, MY_DOCS as MY_DOCS,
    NOTICE_WORDS as NOTICE_WORDS, NO_DUE_DATE as NO_DUE_DATE, OPEN_FIELD as OPEN_FIELD, ORGAN_FIND as ORGAN_FIND,
    ORGAN_SERVICE as ORGAN_SERVICE, ORGAN_SUBS as ORGAN_SUBS, ORGAN_USERS as ORGAN_USERS, OWN_CABINET as OWN_CABINET,
    PAGE_VAR as PAGE_VAR, PEOPLE_QUERY as PEOPLE_QUERY, PERSONAL_OPTION as PERSONAL_OPTION, PERSON_ID as PERSON_ID,
    PROPERTY_LOCK as PROPERTY_LOCK, PROPERTY_PAGE as PROPERTY_PAGE, PROPERTY_QUERY as PROPERTY_QUERY,
    PROPERTY_SAVE_QUERY as PROPERTY_SAVE_QUERY, PROPERTY_VERSION as PROPERTY_VERSION, RAW_BAD as RAW_BAD, READS as READS,
    READ_FORMS as READ_FORMS, REGISTER_QUERY as REGISTER_QUERY, REGISTER_ROW as REGISTER_ROW, REGISTER_SERVICE as REGISTER_SERVICE,
    ROLE_FRAME as ROLE_FRAME, ROLE_ORDER as ROLE_ORDER, ROLE_QUERY as ROLE_QUERY, SAVE_ENCODED as SAVE_ENCODED,
    SAVE_FROM_PAGE as SAVE_FROM_PAGE, SAVE_OPTIONAL as SAVE_OPTIONAL, SAVE_TAIL_FROM_PAGE as SAVE_TAIL_FROM_PAGE,
    SAVE_WORKFLOW_FROM_PAGE as SAVE_WORKFLOW_FROM_PAGE, SEARCH_FIELDS as SEARCH_FIELDS, SEARCH_PER_PAGE_MAX as SEARCH_PER_PAGE_MAX,
    SEARCH_WORD_BAD as SEARCH_WORD_BAD, SECURITY_FIELD as SECURITY_FIELD, SECURITY_LOG_QUERY as SECURITY_LOG_QUERY,
    SERVER_NAME as SERVER_NAME, SKILLS_HOME as SKILLS_HOME, TITLE_BAD as TITLE_BAD, TITLE_BYTES_MAX as TITLE_BYTES_MAX,
    TITLE_MAX as TITLE_MAX, TOKEN_LENGTH as TOKEN_LENGTH, Ticket as Ticket, UNMEASURED_CHECKS as UNMEASURED_CHECKS,
    USE_QUERY as USE_QUERY, USE_WORDS as USE_WORDS, VIEW_DENIED as VIEW_DENIED, VIEW_FOLDER as VIEW_FOLDER, Version as Version,
    WS_GUID as WS_GUID, log as log, property_value as property_value)
from ecm_server import (ROLE_ROW as ROLE_ROW, cookie_header as cookie_header, parse_hits as parse_hits,
    property_save_body as property_save_body, search_body as search_body)
from ecm_agent import (ws_exchange as ws_exchange)
import ep_command  # noqa: E402
import ep_session  # noqa: E402


# ── 열기 · 닫기 · 읽기 ────────────────────────────────────────────────────

def office_of(progid: str) -> str:
    """ProgId → 닫는 손이 붙을 오피스 앱 이름(Word · Excel · PPT). 오피스가 아니면 빈 글자."""
    low = progid.lower()
    return next((app for head, app in OFFICE_OF_PROGID.items() if low.startswith(head)), "")


def viewer_of(progid: str) -> str:
    """ProgId → 보기 창을 닫는 손이 붙을 앱 이름 — 오피스 셋에 Acrobat(Reader 포함)을 더한다. 닫을 줄 모르면 빈 글자."""
    return office_of(progid) or (ACROBAT if progid.lower().startswith(ACROBAT_PROGID) else "")


def open_document(ecm: Ecm, agent: Agent, object_id: str, *, allow_picker: bool = False) -> Opened:
    """문서 하나를 에이전트로 받아 연다 — 열기 전에 그 확장자의 기본 앱을 세운다.

    기본 앱을 사람이 골라야 하면 ``DefaultAppNeeded`` 로 멈춘다. ``allow_picker`` 면 멈추지 않고 열어, 사람이 Windows 의
    고르는 창에서 고르게 둔다(사람에게 그 일을 먼저 알린 뒤에만 준다).
    """
    ticket = ecm.view(object_id)
    try:
        ensured = default_app.ensure(ticket.ext)
        progid, written = ensured.progid, ensured.written
    except default_app.DefaultAppNeeded:
        if not allow_picker:
            raise
        progid, written = "", False
    path = agent.download_view(ticket)
    if not progid:
        progid = default_app.state(ticket.ext).progid
    return Opened(path, ticket, progid, written)


def _powershell(script: pathlib.Path, *args: str, timeout: float) -> subprocess.CompletedProcess:
    """PowerShell 손 하나를 띄워 끝까지 기다린다 — 프로필 없이, 실행 정책은 그 프로세스에서만 푼다. 표준 출력 · 오류는 바이트로 잡아
    돌려주고(푸는 것은 부르는 쪽), 시한을 넘기면 ``subprocess.TimeoutExpired`` 가 그대로 올라간다."""
    return subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args],
                          capture_output=True, timeout=timeout)


def _last_json(out: str) -> dict:
    """손이 표준 출력 끝 줄에 낸 JSON — 출력이 비었거나 끝 줄이 JSON 이 아니면 빈 dict."""
    try:
        return json.loads(out.splitlines()[-1]) if out else {}
    except json.JSONDecodeError:
        return {}


def _close(path: pathlib.Path, app: str, wait: float, require_clean: bool) -> tuple[str, dict]:
    """그 문서만 닫는다 — 저장하지 않는다. ``require_clean`` 이면 저장 안 된 고침이 있을 때 안 닫고 "dirty" 를 낸다."""
    if app == ACROBAT:     # 보기 전용 — 저장할 것이 없다
        script, args = ACROBAT_CLOSE_SCRIPT, ["-Path", str(path), "-WaitSeconds", str(int(wait))]
    else:
        script, args = CLOSE_SCRIPT, ["-Path", str(path), "-App", app, "-WaitSeconds", str(int(wait)),
                                      *(["-RequireClean"] if require_clean else [])]
    proc = _powershell(script, *args, timeout=wait + 60)
    out = proc.stdout.decode("utf-8", "replace").strip()
    if proc.returncode in CLOSE_EXIT:
        return CLOSE_EXIT[proc.returncode], _last_json(out)
    raise EcmError(f"창 닫는 손이 실패했다(종료 {proc.returncode}): {out or proc.stderr.decode('utf-8', 'replace').strip()}")


def close_window(path: pathlib.Path, app: str, *, wait: float = WINDOW_WAIT) -> str:
    """에이전트가 띄운 그 문서만 닫는다 — 그 앱에 남은 문서가 없을 때만 앱을 끈다. closed · not-found · not-front(Acrobat 에서 다른
    pdf 가 앞 탭이라 안 건드렸다) · not-office 를 낸다."""
    if not app:
        return "not-office"
    return _close(path, app, wait, require_clean=False)[0]


# ── 편집 — 잠그고 열기 · 열린 창에서 고치기 · 미리 보고 다음 판으로 올리기 ─────────

@dataclass(frozen=True)
class Changes:
    """편집 패스의 바꿀 것 — 한 부름에 아무 조합으로 묶는다. ``replace`` 는 (옛 조각, 새 조각) 들, ``insert`` 는 옮길 평문 파일들,
    ``after`` 는 파워포인트 장 · 엑셀 시트 번호(그 뒤에 넣는다 · None 이면 끝)다. 무엇을 받나는 ``EDIT_CHANGES`` 표가 든다."""
    replace: tuple[tuple[str, str], ...] = ()
    insert: tuple[pathlib.Path, ...] = ()
    after: int | None = None

    def empty(self) -> bool:
        """고칠 조각도 넣을 파일도 없나."""
        return not self.replace and not self.insert


@dataclass(frozen=True)
class Changed:
    """열린 문서를 고친 한 판의 결과 — 고친 것들과 이 판에 저장했나."""
    applied: tuple[dict, ...]   # 고친 것 — {"op", "where", …}
    saved: bool                  # 이 판에 저장했나(고친 것이 없고 창의 판이 이미 저장돼 있으면 거짓)


def check_change_shape(changes: Changes) -> None:
    """바꿀 것 가운데 문서의 꼴을 몰라도 가릴 수 있는 것 — 빈 조각 · 줄바꿈 · 같은 글 · 조각끼리 겹침 · 넣을 파일이 있나 · 자리
    (``--after``). 서버 · 문서 없이 돌아 명령줄이 세션보다 먼저 부른다(``precheck``). 못 할 까닭이 있으면 ``ArgsError``."""
    olds = [old.strip() for old, _ in changes.replace]
    for (old, new), bare in zip(changes.replace, olds):
        if not bare:
            raise ArgsError("바꿀 조각이 비었다")
        if LINE_BREAK.search(bare):
            raise ArgsError(f"「{bare}」 에 줄바꿈이 들었다 — 한 문단 · 한 칸 안의 조각을 준다(문단마다 따로 준다)")
        if bare == new:
            raise ArgsError(f"「{bare}」 를 같은 글로 바꾸라고 했다")
    # 조각끼리 겹치면 앞 조각을 바꾼 판에서 뒤 조각이 다른 자리에 걸린다 — 문서를 한 번만 세는 손은 그 차례를 못 가린다
    for i, a in enumerate(olds):
        for j, b in enumerate(olds):
            if i != j and a in b:
                raise ArgsError(f"조각 「{a}」 가 다른 조각 「{b}」 안에 든다 — 한 부름에 하나씩 준다")
        for j, (_, new) in enumerate(changes.replace):
            if i != j and a in new:
                raise ArgsError(f"조각 「{a}」 가 다른 조각의 새 글 「{new}」 안에 든다 — 한 부름에 하나씩 준다")
    for file in changes.insert:
        file = pathlib.Path(file)
        if not file.is_file() or file.stat().st_size == 0:
            raise ArgsError(f"넣을 파일이 없거나 비었다: {file}")
    if changes.after is not None:
        if not changes.insert:
            raise ArgsError("--after 는 --insert-from 과 함께만 준다")
        if changes.after < 0:
            raise ArgsError("--after 는 0(맨 앞)부터다")


def check_changes(changes: Changes, app: str) -> None:
    """바꿀 것을 문서를 건드리기 전에 가린다(잠그기 전에도 부른다) — 못 할 까닭이 있으면 ``EcmError``. 어느 앱이 어느 바꿀 것을
    받나는 ``EDIT_CHANGES`` 의 ``apps`` 칸이 든다. 문서 안에서 조각이 몇 번 나오나는 열린 창에서만 셀 수 있어 고치는
    손(change_doc.ps1)이 다시 가린다."""
    if app not in EDITABLE_APPS:
        raise EcmError(f"이 꼴의 문서는 고치지 못한다({app or '모름'}) — {' · '.join(sorted(EDITABLE_APPS))} 만")
    for key, given in (("replace", changes.replace), ("insert", changes.insert)):
        if given and app not in EDIT_CHANGES[key].apps:
            raise ArgsError(f"이 문서({app})에는 바꿀 것 {key} 를 못 한다 — {' · '.join(EDIT_CHANGES[key].apps)} 만 받는다")
    check_change_shape(changes)
    for old, _ in changes.replace:
        if app == "Word" and len(old.strip()) > WORD_FIND_MAX:
            raise ArgsError(f"워드는 {WORD_FIND_MAX} 자가 넘는 조각을 못 찾는다 — 더 짧은 조각을 준다")
    for file in changes.insert:
        if pathlib.Path(file).suffix.lower() not in INSERT_FAMILY[app]:
            raise ArgsError(f"넣을 파일의 꼴({pathlib.Path(file).suffix})이 이 문서({app})에 안 맞는다 — {' · '.join(INSERT_FAMILY[app])} 만 넣는다")
    if changes.after is not None and app == "Word":
        raise ArgsError("워드는 본문 끝에만 넣는다 — --after 를 빼고 준다")


def change_document(path: pathlib.Path, app: str, changes: Changes, *, wait: float = WINDOW_WAIT) -> Changed:
    """편집으로 열린 그 문서를 창 안에서 고치고 저장한다(창은 남긴다). 바꿀 것이 비면 저장 안 된 고침이 있을 때만 저장한다.

    못 할 까닭이 있으면 아무것도 안 고치고 ``EcmError``(조각이 0 번 · 여러 번 · 수식 칸 · 넣을 자리 밖 · 그 문서가 안 떴다). 고치다
    멈추면 고친 것까지 대고 ``EcmError`` — 그 판은 저장하지 않아 창에만 남는다."""
    check_changes(changes, app)
    spec = {"replace": [{"old": old.strip(), "new": new} for old, new in changes.replace],
            "insert": [str(pathlib.Path(f).resolve()) for f in changes.insert], "after": changes.after}
    work = pathlib.Path(tempfile.mkdtemp(prefix="ecm-change-"))
    try:
        ops = work / "ops.json"
        ops.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        proc = _powershell(CHANGE_SCRIPT, "-Path", str(path), "-App", app, "-Ops", str(ops), "-WaitSeconds", str(int(wait)),
                           timeout=wait + CHANGE_TIMEOUT)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    out = proc.stdout.decode("utf-8", "replace").strip()
    got = _last_json(out)
    applied = tuple(got.get("applied") or ())
    if proc.returncode == CHANGE_DONE:
        return Changed(applied, bool(got.get("saved")))
    if proc.returncode == CHANGE_NOT_FOUND:
        raise EcmError(f"{wait:.0f} 초 안에 열린 그 문서를 못 찾았다 — 아무것도 안 고쳤다. 문서가 닫혔으면 edit 로 다시 연다")
    if proc.returncode == CHANGE_REFUSED:
        raise EcmError(f"{got.get('why') or '못 고칠 까닭이 있다'} — 아무것도 안 고쳤다")
    done = "; ".join(f"{a.get('where')} {a.get('op')}" for a in applied) or "없음"
    raise EcmError(f"{got.get('why') or out or proc.stderr.decode('utf-8', 'replace').strip()} — 고친 것: {done}. 저장하지 않았다 — "
                   "창에 그 판이 떠 있으니 사람이 보고 되돌리거나(Ctrl+Z) 그대로 둔다")


def save_window(path: pathlib.Path) -> bool:
    """편집으로 열린 그 문서 창의 저장 안 된 고침만 저장한다 — 저장했으면 참. 고치는 손을 바꿀 것 없이 한 판 돌린다(그 손은 바꿀 것이
    비면 저장만 한다). 문서가 안 떴으면 ``EcmError``."""
    return change_document(path, OFFICE_BY_EXT[path.suffix.lower()], Changes()).saved


def checkout_file(path: pathlib.Path, object_id: str, docs_root=None) -> pathlib.Path:
    """에이전트가 그 문서를 편집으로 받은 파일인가 — <받는 자리>\\<계정>\\CHECKOUT\\<시각 번호>\\<이름에 그 문서 열쇠>. 아니면
    ``EcmError``. 편집 패스는 여러 부름을 건너므로 모델이 이 경로를 들고 다닌다 — 손이 부를 때마다 다시 잰다."""
    path = pathlib.Path(path)
    root = pathlib.Path(docs_root) if docs_root else agent_docs_root()
    try:
        inside = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        inside = ()
    if len(inside) != 4 or inside[1].lower() != CHECKOUT_FOLDER.lower() or object_id.lower() not in path.name.lower():
        raise ArgsError(f"그 문서({object_id})를 편집으로 받은 파일(…\\{CHECKOUT_FOLDER}\\…)이 아니다: {path} — edit 가 낸 경로를 그대로 준다")
    if path.suffix.lower() not in OFFICE_BY_EXT:
        raise EcmError(f"이 꼴({path.suffix})은 오피스로 고쳐 올리지 못한다 — ECM 화면에서 편집완료를 누른다")
    return path


@dataclass(frozen=True)
class CheckedIn:
    """올리기의 끝 — 앞 판 · 뒤 판(고친 것 없이 풀렸으면 같다) · 고른 판, 판이 올랐으면 새 판의 열쇠(못 받았으면 그 까닭)."""
    version_before: str
    version_after: str
    picked: str            # 편집완료 창에서 고른 판
    new_key: str = ""      # 판이 오른 뒤 지금 판의 열쇠 — 옛 열쇠가 그대로 나오면 빈 글자
    key_why: str = ""      # 새 판의 열쇠를 못 가린 까닭

    @property
    def unchanged(self) -> bool:
        """고친 것 없이 풀려 판이 그대로인가."""
        return self.version_after == self.version_before


@dataclass(frozen=True)
class CheckinPlan:
    """올리기 미리 보기 — 서버를 안 바꾼다. ``token`` 이 확인 열쇠다(문서 · 지금 판 · 수정 내용 · 미리 본 때 디스크의 그 파일 판)."""
    object_id: str
    name: str
    version: str
    desc: str
    path: pathlib.Path
    stamp: tuple[int, int]   # 미리 본 때 그 파일의 (고친 시각 ns, 크기) — 올릴 때 다시 재어 견준다
    saved: bool              # 이 미리 보기가 창의 고침을 저장했나
    closed: bool             # 문서 창이 이미 닫혀 편집완료 창이 떠 있나(사람이 먼저 닫았다)

    @property
    def token(self) -> str:
        """확인 열쇠 — 문서 · 지금 판 · 수정 내용 · 파일 · 미리 본 때 그 파일 판의 지문(``checkin_token``)."""
        return checkin_token(self.object_id, self.version, self.desc, self.path, self.stamp)


def file_stamp(path: pathlib.Path) -> tuple[int, int]:
    """디스크의 그 파일 판 — (고친 시각 ns, 크기). 오피스가 쥔 감긴 파일은 바이트를 못 읽어 시각 · 크기로 잰다."""
    stat = pathlib.Path(path).stat()
    return stat.st_mtime_ns, stat.st_size


def checkin_token(object_id: str, version: str, desc: str, path: pathlib.Path, stamp: tuple[int, int]) -> str:
    """올리기의 확인 열쇠 — 판이 바뀌거나, 그 파일이 다시 저장되거나(사람 · change), 수정 내용 글이 다르면 달라진다."""
    return token("checkin", object_id.lower(), version, desc.strip(), str(pathlib.Path(path).resolve()).lower(), *stamp)


def checkin_pending(object_id: str) -> bool:
    """그 문서의 편집완료 창이 이미 떠 있나 — 사람이 오피스를 먼저 끈 판. 창을 찾기만 하고 누르지 않는다."""
    proc = _powershell(CHECKIN_SCRIPT, "-ObjectId", object_id, "-Desc", FIND_ONLY_DESC, "-Current", "0", "-WaitSeconds", "2",
                       "-FindOnly", timeout=60)
    return proc.returncode == 0


def edit_document(ecm: Ecm, agent: Agent, object_id: str, *, ai_ok: bool = False, changes: Changes | None = None) -> Opened:
    """편집으로 연다 — 서버가 그 문서를 이 사람 이름으로 잠그고, 에이전트가 읽기 쓰기로 띄운다. ``Opened`` 를 낸다.

    잠그기 전에 멈추는 것 — 등급(``check_readable``) · ``OFFICE_BY_EXT`` 밖의 꼴(``EcmError``) · 그 꼴에 못 할 바꿀 것
    (``check_changes``) · 기본 앱 없음(``DefaultAppNeeded``). 끝까지 못 가는 판에 잠그면 사람이 모르는 잠금이 남는다. 잠근 뒤 받기가
    안 서면 「편집취소」를 이르는 ``AgentError``. 바꿀 것은 가리기만 한다 — 고치는 일은 ``change_document`` 가 한다."""
    check_readable(ecm, object_id, ai_ok=ai_ok)
    ticket = ecm.view(object_id)                    # 확장자 · 이름을 먼저 본다 — 읽기라 잠그지 않는다
    refuse_uneditable(ticket)
    if changes is not None and not changes.empty():
        check_changes(changes, OFFICE_BY_EXT[ticket.ext])
    ensured = default_app.ensure(ticket.ext)
    locked = ecm.checkout(object_id)
    try:
        path = agent.download_edit(locked)
    except AgentError as exc:
        raise AgentError(locked_but_not_received_word(exc, object_id)) from exc
    return Opened(path, locked, ensured.progid, ensured.written)


def refuse_uneditable(ticket: Ticket) -> None:
    """보기 첫 걸음의 표가 편집으로 열어 올릴 수 있는 꼴(오피스 셋)인가 — 아니면 잠그기 전에 ``EcmError``."""
    if ticket.ext not in OFFICE_BY_EXT:
        raise EcmError(f"이 꼴({ticket.ext or '확장자 없음'})은 편집으로 열어 올리지 못한다 — checkin 은 워드 · 엑셀 · 파워포인트만 "
                       "올린다. 잠그지 않았다 — 고치려면 사람이 ECM 화면에서 편집한다")


def locked_but_not_received_word(exc: Exception, object_id: str) -> str:
    """잠근 뒤 받기가 안 섰을 때의 말 — 서버에서 잠겼으니 편집취소를 이른다."""
    return f"{exc} — 문서는 서버에서 잠겼다. {CANCEL_NEXT.format(object_id=object_id)}"


DESC_EMPTY_PREVIEW = "동료가 판 이력에서 읽을 한 줄을 적는다"   # 수정 내용이 빈 판의 말 — 미리 보기
DESC_EMPTY_CHECKIN = "무엇을 고쳤나를 한 줄 적는다"              # 같은 판의 말 — 올리기


def checkin_inputs(path, object_id: str, desc: str, empty_why: str, docs_root=None) -> tuple[str, str, pathlib.Path]:
    """올리기 · 그 미리 보기의 값 가운데 서버 없이 가릴 수 있는 것 — 문서 열쇠 · 수정 내용 · 그 문서를 편집으로 받은 파일인가.
    (열쇠, 다듬은 수정 내용, 받은 파일)을 낸다. 명령줄은 세션보다 먼저 부른다(``precheck``)."""
    object_id = _object_id(object_id)
    desc = desc.strip()
    if not desc:
        raise ArgsError(f"수정 내용(--desc)이 비었다 — {empty_why}")
    return object_id, desc, checkout_file(path, object_id, docs_root)


def prepare_checkin(ecm: Ecm, path: pathlib.Path, object_id: str, desc: str, *, ai_ok: bool = False,
                    docs_root=None) -> CheckinPlan:
    """올리기를 미리 본다 — 창의 고침을 저장하고(저장 안 된 고침이 있을 때만) 지금 판 · 잠금을 읽어 확인 열쇠를 낸다. 서버를 안
    바꾼다. 문서가 잠겨 있지 않거나(편집이 취소됐다) 판을 못 읽거나 문서 창도 편집완료 창도 없으면 ``EcmError``.

    창을 건드리기 전에 등급 문(``gate``)을 지난다 — 미리 보기는 고친 자리를 찍어 보이라는 말을 내고, 사람이 ECM 화면에서 편집으로 연
    파일을 이어받은 판은 앞 걸음(``edit_document``)의 문이 없다. 등급은 이미 읽는 속성 화면(``doc_state``)의 것이다."""
    object_id, desc, path = checkin_inputs(path, object_id, desc, DESC_EMPTY_PREVIEW, docs_root)
    state = ecm.doc_state(object_id)
    gate(state.security, ai_ok=ai_ok, stopped=GATE_EDIT)
    refuse_unpreviewable(state)
    saved, closed = save_or_already_closed(path, object_id)
    return CheckinPlan(object_id, AGENT_FILE_SUFFIX.sub("", path.name), state.version, desc, path, file_stamp(path), saved, closed)


def refuse_unpreviewable(state: DocState) -> None:
    """올리기를 미리 볼 수 있는 문서인가 — 지금 판을 못 읽었거나 편집 잠금이 없으면(취소됐거나 이미 올라갔다) ``EcmError``."""
    if not state.version:
        raise EcmError("문서 정보에서 지금 판을 못 읽었다 — 다음 판을 가릴 수 없어 올리기를 미리 보지 않는다")
    if state.locked is False:
        raise EcmError("문서가 편집으로 잠겨 있지 않다 — 편집이 취소됐거나 이미 올라갔다. 고치려면 edit 로 다시 연다")


def save_or_already_closed(path: pathlib.Path, object_id: str) -> tuple[bool, bool]:
    """창의 판을 저장하고 (저장했나, 사람이 이미 닫았나)를 낸다 — 창이 없는데 편집완료 창이 떠 있으면 사람이 먼저 닫은 것이다(디스크의
    판이 올라간다). 창도 편집완료 창도 없으면 저장 손의 ``EcmError`` 그대로."""
    try:
        return save_window(path), False
    except EcmError:
        if not checkin_pending(object_id):
            raise
        return False, True


def _released_unchanged(ecm: Ecm, object_id: str, before: str, *, wait: float = UNCHANGED_WAIT) -> bool:
    """고친 것 없이 닫혀 에이전트가 편집완료 창 없이 잠금만 풀었나 — 잠금이 풀리고 판이 그대로면 참. 고친 판이면 편집완료 창이
    뜰 때까지 잠금이 남으니, 잠긴 채 ``wait`` 초가 지나면 거짓이다. 한 번 볼 때 속성 화면을 한 번 읽는다."""
    deadline = time.monotonic() + wait
    while True:
        state = ecm.doc_state(object_id)
        if state.locked is False:
            return state.version == before
        if time.monotonic() >= deadline:
            return False
        time.sleep(POLL)


def checkin_document(ecm: Ecm, path: pathlib.Path, object_id: str, desc: str, *, confirm: str, docs_root=None) -> CheckedIn:
    """미리 본 그대로 올린다 — 확인 열쇠가 지금 판 · 디스크의 그 파일 · 수정 내용과 맞고 창에 저장 안 된 고침이 없을 때만 문서를
    닫고, 에이전트의 편집완료 창에서 늘 다음 판 · 수정 내용으로 올린 뒤 판이 올랐나 본다.

    ``CheckedIn`` 을 낸다 — 고친 것 없이 닫혀 에이전트가 잠금만 풀었으면 앞 판 · 뒤 판이 같다. 열쇠가 다르거나 창에 고침이 남았으면
    아무것도 안 닫고 ``EcmError``. 사람의 다른 문서는 안 닫고, 창이 시한 안에 안 뜨면 남은 문서 이름을 대고 ``EcmError`` 로 멈춘다 —
    그 문서들을 닫은 뒤 다시 부르면 창에서 이어 간다."""
    object_id, desc, path = checkin_inputs(path, object_id, desc, DESC_EMPTY_CHECKIN, docs_root)
    before = ecm.version(object_id)
    if not before:
        raise EcmError(CHECKIN_NO_VERSION)
    if confirm != checkin_token(object_id, before, desc, path, file_stamp(path)):
        raise Stale(CHECKIN_KEY_STALE)
    window, said = _close(path, OFFICE_BY_EXT[path.suffix.lower()], WINDOW_WAIT, require_clean=True)
    if window == "dirty":
        raise Stale(CHECKIN_WINDOW_DIRTY)
    left = said.get("left", -1)
    state = checkin_state_after_close(ecm, object_id, before, window, left)
    got, detail = {}, ""
    if state == CHECKIN_PRESS:
        rc, got, detail = press_checkin(object_id, desc, before)
        state = checkin_state_after_press(ecm, object_id, before, rc, got, window, left)
    if state == CHECKIN_UNCHANGED:
        return CheckedIn(before, before, "")
    if state != CHECKIN_PRESSED:
        raise EcmError(checkin_stop_word(state, left, shown_names(said.get("others") or []), detail))
    after = wait_new_version(ecm, object_id, before)
    new_key, key_why = superseded(ecm, object_id)
    return CheckedIn(before, after, str(got.get("picked", "")), new_key, key_why)


# 올리기 손이 문 앞에서 멈출 때의 말 — 아무것도 안 닫았다
CHECKIN_NO_VERSION = "문서 정보에서 지금 판을 못 읽었다 — 다음 판을 가릴 수 없어 올리지 않는다"
CHECKIN_KEY_STALE = ("확인 열쇠가 지금과 다르다 — 미리 본 뒤 문서가 다시 저장됐거나(사람 · change) 판이 바뀌었거나 수정 내용 글이 "
                     "다르다. 아무것도 안 닫았다. preview-checkin 으로 다시 보이고 그 열쇠로 올린다")
CHECKIN_WINDOW_DIRTY = ("창의 문서에 미리 본 뒤 고친 것(저장 안 됨)이 있다 — 아무것도 안 닫았다. preview-checkin 으로 그 판을 저장해 "
                        "다시 보이고 그 열쇠로 올린다")
# 올리기의 상태 — 창을 닫은 뒤와 편집완료 창 손이 끝난 뒤, 셈은 이 가운데 하나를 낸다
CHECKIN_UNCHANGED = "unchanged"      # 고친 것 없이 풀렸다 — 에이전트가 편집완료 창 없이 잠금만 풀었다
CHECKIN_NO_WINDOW = "no-window"      # 문서 창도 편집완료 창도 없다
CHECKIN_PRESS = "press"              # 편집완료 창을 누르러 간다
CHECKIN_OTHERS_LEFT = "others-left"  # 같은 앱에 다른 문서가 남아 편집완료 창이 안 떴다
CHECKIN_UNCOUNTED = "uncounted"      # 같은 앱에 남은 문서를 못 세어 앱을 안 껐고 편집완료 창이 안 떴다
CHECKIN_STILL_LOCKED = "still-locked"   # 편집완료 창이 안 떴고 문서는 아직 잠겨 있다
CHECKIN_SAVED_OPEN = "saved-open"    # 편집완료의 저장은 보냈는데 창이 안 닫혔다
CHECKIN_NOT_PRESSED = "not-pressed"  # 편집완료 창을 누르지 않았다
CHECKIN_PRESSED = "pressed"          # 눌렀고 창이 닫혔다


def checkin_state_after_close(ecm: Ecm, object_id: str, before: str, window: str, left: int) -> str:
    """문서 창을 닫은 뒤 올리기가 설 자리를 낸다 — 고친 것 없이 풀렸다(``CHECKIN_UNCHANGED``) · 문서 창도 편집완료 창도 없다
    (``CHECKIN_NO_WINDOW``) · 편집완료 창을 누르러 간다(``CHECKIN_PRESS``). 앱에 남은 문서가 없이 닫혔을 때만 잠금을 다시 읽는다."""
    if window == "closed" and left == 0 and _released_unchanged(ecm, object_id, before):
        return CHECKIN_UNCHANGED
    if window == "not-found" and not checkin_pending(object_id):
        return CHECKIN_NO_WINDOW
    # 같은 앱에 사람의 다른 문서가 남아 앱을 안 껐어도 편집완료 창은 문서를 닫으면 뜰 수 있다 — 멈추지 않고 창을 기다린다
    return CHECKIN_PRESS


def press_checkin(object_id: str, desc: str, before: str) -> tuple[int, dict, str]:
    """편집완료 창 손을 띄워 다음 판 · 수정 내용으로 누르게 하고 (종료 값, 끝 줄 JSON, 출력 또는 오류의 글)을 낸다 — 칸을 못 읽고 나오면
    새 프로세스로 다시 붙는다."""
    # 창이 다 실리기 전에 붙은 프로세스는 칸을 끝내 못 읽는다(checkin_window.ps1 머리) — 칸을 못 읽고 나오면(아무것도 안 보냈다)
    # 새 프로세스로 다시 붙는다. 창이 뜨기를 기다리는 시한은 첫 판에만 쓴다
    wait = CHECKIN_WAIT
    for _ in range(CHECKIN_ATTACH_TRIES):
        proc = _powershell(CHECKIN_SCRIPT, "-ObjectId", object_id, "-Desc", desc, "-Current", before, "-WaitSeconds", str(int(wait)),
                           timeout=wait + 90)
        out = proc.stdout.decode("utf-8", "replace").strip()
        got = _last_json(out)
        if not (proc.returncode == 1 and got.get("found") and not got.get("choices") and not got.get("saved")):
            break
        wait = CHECKIN_REATTACH_WAIT
    return proc.returncode, got, out or proc.stderr.decode("utf-8", "replace").strip()


def checkin_state_after_press(ecm: Ecm, object_id: str, before: str, rc: int, got: dict, window: str, left: int) -> str:
    """편집완료 창 손의 끝을 올리기의 상태 하나로 셈한다 — 창이 안 떴으면(종료 2) 잠금을 다시 읽어 고친 것 없이 풀렸나 · 다른 문서가
    남았나 · 아직 잠겼나를 가르고, 그 밖은 저장은 보냈는데 안 닫힘 · 안 누름 · 눌렀음이다."""
    if rc == 2:
        if _released_unchanged(ecm, object_id, before, wait=0):
            return CHECKIN_UNCHANGED
        if window == "closed" and left != 0:
            return CHECKIN_OTHERS_LEFT if left > 0 else CHECKIN_UNCOUNTED
        return CHECKIN_STILL_LOCKED
    if rc != 0 and got.get("saved"):
        return CHECKIN_SAVED_OPEN
    return CHECKIN_NOT_PRESSED if rc != 0 else CHECKIN_PRESSED


def shown_names(others: list) -> str:
    """닫는 손이 댄 남은 문서 이름들을 사람에게 보일 꼴로 — 받은 파일의 꼬리(열쇠 · 계정)를 떼고 잇는다."""
    return " · ".join(AGENT_FILE_SUFFIX.sub("", str(n)) for n in others)


def checkin_stop_word(state: str, left: int, names: str, detail: str) -> str:
    """올리지 못한 상태 하나를 사람에게 할 말로 옮긴다 — 다음 걸음까지. ``names`` 는 같은 앱에 남은 문서 이름(``shown_names``),
    ``detail`` 은 편집완료 창 손이 낸 글이다."""
    if state == CHECKIN_NO_WINDOW:
        return (f"{WINDOW_WAIT:.0f} 초 안에 열린 그 문서도 편집완료 창도 못 찾았다 — 올리지 않았다. 문서가 떠 있으면 그대로 두고 "
                "같은 명령을 다시 부르고, 사람이 이미 올렸으면 doc 으로 판을 본다")
    if state in (CHECKIN_OTHERS_LEFT, CHECKIN_UNCOUNTED):
        what = f"다른 문서 {left} 개가 열려 있어" if state == CHECKIN_OTHERS_LEFT else "남은 문서를 못 세어"
        return (f"닫았는데 {CHECKIN_WAIT:.0f} 초 안에 편집완료 창이 안 떴다. 같은 앱에 {what} 앱을 끄지 않았다"
                f"{f'({names})' if names else ''} — 사람이 그 문서들을 닫은 뒤(또는 앱을 끈 뒤) 같은 명령을 다시 부른다. "
                "고친 것은 저장돼 있다")
    if state == CHECKIN_STILL_LOCKED:
        return (f"{CHECKIN_WAIT:.0f} 초 안에 편집완료 창이 안 떴고 문서는 아직 잠겨 있다 — 오피스가 아직 떠 있으면 사람이 끄고 같은 "
                "명령을 다시 부른다")
    if state == CHECKIN_SAVED_OPEN:
        return "편집완료의 저장은 보냈는데 창이 시한 안에 안 닫혔다 — 다시 누르지 말고 잠시 뒤 doc 으로 판이 올랐나 본다"
    return f"편집완료 창을 누르지 않았다 — 창이 떠 있으면 사람이 「새로운 버전」을 고르고 누른다: {detail}"


def wait_new_version(ecm: Ecm, object_id: str, before: str) -> str:
    """편집완료를 누른 뒤 문서 정보의 최종 버전이 ``before`` 에서 오르기를 기다려 오른 판을 낸다 — 시한 안에 안 오르면 ``EcmError``."""
    after, deadline = before, time.monotonic() + VERSION_WAIT
    while time.monotonic() < deadline and after == before:
        time.sleep(VERSION_POLL)
        after = ecm.version(object_id)
    if after == before:
        raise EcmError(f"편집완료는 눌렀는데 {VERSION_WAIT:.0f} 초 안에 최종 버전이 {before} 그대로다 — ECM 화면에서 판을 본다")
    return after


# ── 새 문서 등록 — 미리 보기 → 확인 열쇠 → 올리기 → 다시 읽기 ─────────────

@dataclass(frozen=True)
class RegisterPlan:
    """새 문서 등록의 미리 보기 — 서버를 안 바꾼다(같은 이름 찾기만 묻는다). ``token`` 이 확인 열쇠다."""
    path: pathlib.Path
    title: str
    ext: str
    size: int
    cabinet: str
    cabinet_name: str
    folder: str
    folder_path: tuple[str, ...]
    security: str
    open_flag: str
    digest: str            # 올릴 파일 바이트의 지문 — 미리 본 뒤 파일이 바뀌면 열쇠가 달라진다

    @property
    def token(self) -> str:
        """확인 열쇠 — 올릴 파일 바이트 · 문서함 · 폴더 · 보안 짝 · 이름의 지문."""
        return token("register", self.digest, self.cabinet, self.folder, self.security, self.open_flag, self.title)


def register_inputs(path, *, folder: str, folder_path: str, security: str, open_flag: str, title: str) -> tuple[pathlib.Path, str, str]:
    """등록할 값 가운데 서버 없이 가릴 수 있는 것 — 파일 · 보안 짝 · 폴더를 하나로 줬나 · 폴더 열쇠의 꼴 · 확장자 · 이름. (풀어 둔 파일
    경로, 확장자, 다듬은 이름)을 낸다. 명령줄은 세션보다 먼저 부른다(``precheck``). 못 할 까닭이 있으면 ``ArgsError``."""
    path = pathlib.Path(path).resolve()       # 에이전트는 다른 프로세스라 상대 경로를 제 자리에서 푼다
    if not path.is_file() or path.stat().st_size == 0:
        raise ArgsError(f"올릴 파일이 없거나 비었다: {path}")
    if (security, open_flag) not in SECURITY_PAIRS:
        raise ArgsError("보안등급 · 공개 짝이 화면의 여섯 가운데 하나가 아니다 — " +
                       " · ".join(f"{s}/{o}={n}" for (s, o), n in SECURITY_PAIRS.items()))
    if bool(folder) == bool(folder_path):
        raise ArgsError("폴더는 --folder(열쇠) 와 --folder-path(경로) 가운데 하나로 준다")
    if folder:
        folder_key(folder)
    ext = path.suffix.lstrip(".").lower()
    if not ext or not ext.isalnum():
        raise ArgsError(f"확장자가 없는 파일은 화면도 안 받는다: {path.name}")
    return path, ext, check_title(title or path.stem)


def plan_register(ecm: Ecm, path: pathlib.Path, *, cabinet: str, folder: str = "", folder_path: str = "", security: str,
                  open_flag: str, title: str = "") -> RegisterPlan:
    """새 문서로 올리기 전에 못 할 까닭을 다 가리고 ``RegisterPlan`` 을 낸다 — 파일 · 문서함 · 보안 짝 · 폴더가 그 문서함의 것인가
    (폴더 열쇠면 나무에서 찾고, 경로면 꼭 맞는 이름으로 따라간다) · 이름 · 그 폴더의 같은 이름. 서버를 안 바꾼다."""
    path, ext, name = register_inputs(path, folder=folder, folder_path=folder_path, security=security, open_flag=open_flag,
                                      title=title)
    cabinet_key(cabinet)                      # 올린 뒤에 지면 올라간 문서를 「실패」로 알리게 된다 — 서버에 닿기 전에 본다
    folder, where = register_folder(ecm, cabinet, folder, folder_path)
    refuse_duplicate(ecm, folder, name, ext)
    return RegisterPlan(path, name, ext, path.stat().st_size, cabinet, ecm.cabinet_name(cabinet), folder, where, security, open_flag,
                        file_digest(path))


def register_folder(ecm: Ecm, cabinet: str, folder: str, folder_path: str) -> tuple[str, tuple[str, ...]]:
    """올릴 폴더가 그 문서함의 것인가를 폴더 나무로 보고 (폴더 열쇠, 이름 경로)를 낸다 — 경로면 꼭 맞는 이름으로 따라가고, 열쇠면
    나무에서 찾는다. 없으면 ``ArgsError``."""
    # 등록 뒤의 목록 견줌만으로는 남의 문서함에 이미 올라간 문서를 「실패」로 알리게 된다 — 폴더가 그 문서함의 것인가를 먼저 본다
    if folder_path:
        where, found = ecm.resolve_folder(cabinet, folder_path)
        return found.id, where
    else:
        where = ecm.folder_path(cabinet, folder)
        if where is None:
            raise ArgsError(f"그 폴더({folder})가 문서함 {cabinet} 에 없다 — 아무것도 안 올렸다. folders {cabinet} 가 낸 폴더를 준다")
        return folder, where


def refuse_duplicate(ecm: Ecm, folder: str, name: str, ext: str) -> None:
    """그 폴더에 같은 이름 · 확장자의 문서가 있으면 올리지 않고 ``EcmError`` — 다음 판은 편집 패스의 몫이다."""
    clash = ecm.duplicates(folder, name, ext)
    if clash:
        raise EcmError(f"그 폴더에 같은 이름의 문서가 있다({', '.join(clash)}) — 고쳐 올리려면 edit · checkin 으로 다음 판을 올리고, "
                       "새 문서면 --title 로 이름을 바꾼다")


def file_digest(path: pathlib.Path) -> str:
    """올릴 파일 바이트의 지문 — 미리 본 뒤 파일이 바뀌면 확인 열쇠가 달라진다."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


REGISTER_KEY_STALE = ("확인 열쇠가 지금과 다르다 — 미리 본 뒤 파일 · 폴더 · 보안등급 · 이름 가운데 무엇이 바뀌었다. 아무것도 안 올렸다. "
                      "preview-register 로 다시 보이고 그 열쇠로 올린다")


def register_document(ecm: Ecm, agent: Agent, path: pathlib.Path, *, cabinet: str, folder: str = "", folder_path: str = "",
                      security: str, open_flag: str, title: str = "", confirm: str) -> Registered:
    """미리 본 그대로 새 문서로 올리고 ``Registered`` 를 낸다 — 화면의 「컨텐츠 등록」과 같은 차례다.

    올리기 전에 미리 보기의 가림을 다시 다 돌린다(그 사이 같은 이름이 섰거나 파일이 바뀌었으면 열쇠가 달라진다). 열쇠가 다르면
    에이전트에도 서버 등록에도 안 가고 ``EcmError``. 보안등급 · 공개는 사람이 미리 보기에서 확인한 짝이다 — 잘못 고르면 동료 전체에 보인다."""
    plan = plan_register(ecm, path, cabinet=cabinet, folder=folder, folder_path=folder_path, security=security,
                         open_flag=open_flag, title=title)
    if confirm != plan.token:
        raise Stale(REGISTER_KEY_STALE)
    server_path, server_file = agent.upload_new(plan.path)
    object_id = ecm.register(folder=plan.folder, title=plan.title, ext=plan.ext, size=plan.size, server_path=server_path,
                             server_file=server_file, security=security, open_flag=open_flag)
    return check_registered(ecm, plan, object_id)


def check_registered(ecm: Ecm, plan: RegisterPlan, object_id: str) -> Registered:
    """올린 문서를 그 문서함 목록에서 다시 읽어 폴더 · 보안등급이 미리 본 값인가 보고 ``Registered`` 를 낸다 — 못 찾거나 다르면
    다시 올리지 말라는 ``EcmError``."""
    listed = [d for d in ecm.list(search=plan.title, cabinet=plan.cabinet) if d.object_id == object_id]
    if not listed:
        raise EcmError(f"등록은 됐는데(문서 {object_id}) 그 문서함 목록에서 못 찾았다 — 폴더가 그 문서함 것이 아닐 수 있다. "
                       "다시 올리지 말고 ECM 화면에서 그 폴더를 본다")
    if listed[0].folder_id != plan.folder or listed[0].security != plan.security:
        raise EcmError(f"올린 문서({object_id})의 폴더 · 보안등급이 고른 값과 다르다(폴더 {listed[0].folder_id} · 보안 "
                       f"{listed[0].security}) — ECM 화면에서 그 문서의 속성을 본다")
    return Registered(object_id, plan.title, listed[0].version)


# ── 권한 — 주고 거두기(미리 보기 → 확인 열쇠 → 저장 → 다시 읽기) ──────────


@dataclass(frozen=True)
class AccessPlan:
    """권한을 바꾸는 한 판 — 지금 명단 · 바뀔 명단과, 사람에게 보일 더함 · 뺌 · 옮김. ``token`` 이 확인 열쇠다."""
    object_id: str
    title: str
    before: tuple[Grant, ...]
    after: tuple[Grant, ...]
    added: tuple[Grant, ...]
    removed: tuple[Grant, ...]
    moved: tuple[tuple[Grant, Grant], ...]   # (앞, 뒤)
    notes: tuple[str, ...]                   # 펼친 조직 · 뺀 본인 따위 — 사람이 읽을 말

    @property
    def token(self) -> str:
        """확인 열쇠 — 문서와 지금 · 바뀔 명단의 지문(``access_token``)."""
        return access_token(self.object_id, self.before, self.after)


def access_token(object_id: str, before, after) -> str:
    """지금 명단과 바뀔 명단의 지문 — 미리 본 뒤 누가 명단을 바꿨거나 바랄 명단이 달라지면 열쇠가 달라진다."""
    return token(object_id, grants_key(before), grants_key(after))


def _grant_of(person: Person, role: str) -> Grant:
    """ECM 사람 하나에 역할을 붙인 사람 권한 줄(``Grant``)."""
    return Grant(role, person.id, "U", person.name, person.dept, person.email, person.employee)


def same_mail(given: str, held: str) -> bool:
    """사람 말의 메일 칸(「메일ID」 · 「메일ID@도메인」)이 ECM 사람 줄의 메일 칸과 같은 사람인가 — ECM 의 사람 줄은 메일 ID(@ 앞)를
    든다(``Grant.email``). 사람 줄이 온 주소를 들면 온 주소끼리, ID 만 들면 @ 앞끼리 견준다(대소문자는 안 가린다)."""
    given, held = given.strip().lower(), held.strip().lower()
    if "@" in held:
        return given == held
    return given.partition("@")[0] == held


def _pick_person(ecm: Ecm, spec: str, company: str) -> Person:
    """「이름」 · 「이름/메일ID」 · 「이름/메일 주소」 하나를 사람 하나로 — 여럿이면 고르지 않고 후보를 다 보이며 멈춘다."""
    name, _, email = spec.partition("/")
    found = ecm.people(name, company)
    # 이름이 꼭 맞는 사람만 받는다 — 일부만 맞은 사람에게 주면 엉뚱한 사람이 권한을 받는다
    exact = [p for p in found if p.name == name.strip()]
    if email.strip():
        exact = [p for p in exact if same_mail(email, p.email)]
    if len(exact) == 1:
        return exact[0]
    if not exact:
        near = "".join(f"\n  {p.label()}" for p in found)
        raise ArgsError(f"「{spec}」 인 사람을 ECM 에서 못 찾았다 — 이름이 꼭 맞아야 준다. ECM 은 이름으로만 찾는다(메일 ID · 사번은 안 걸린다). "
                       "이름을 모르면 스킬 company-directory 의 find --name 으로 이름부터 받는다" + (f". 이름 일부가 걸린 사람:{near}" if near else ""))
    raise ArgsError(f"「{spec}」 가 {len(exact)} 명이다 — 고르지 않는다. 이름/메일ID 로 다시 준다:\n" +
                   "\n".join(f"  {p.label()}" for p in exact))


def _pick_organ(ecm: Ecm, spec: str, company: str) -> Organ:
    """「org:부서코드」 또는 「org:부서 이름」 하나를 부서 하나로 — 이름이 여럿에 걸리면 코드와 함께 다 보이며 멈춘다."""
    kind, value = spec_kind(spec)
    if kind == SPEC_CODE:
        return Organ(value, "", "", "", 0, 0)
    found = ecm.organs(value, company)
    # 이름이 꼭 맞는 부서만 받는다 — 일부만 맞은 부서를 펼치면 엉뚱한 명단이 권한을 받는다
    exact = [o for o in found if o.name == value]
    if len(exact) == 1:
        return exact[0]
    if not exact:
        near = "".join(f"\n  {o.upper} > {o.name} · 코드 {o.code}" for o in found)
        raise ArgsError(f"「{value}」 부서를 ECM 조직도에서 못 찾았다 — 이름이 꼭 맞거나 org:<코드> 여야 준다. 스킬 company-directory 의 find --tree 로 "
                       "이름을 본다" + (f". 이름 일부가 걸린 부서:{near}" if near else ""))
    raise ArgsError(f"「{value}」 가 부서 {len(exact)} 곳에 걸린다 — 고르지 않는다. org:<코드> 로 다시 준다:\n" +
                   "\n".join(f"  {o.upper} > {o.name} · 바로 {o.members} 명 · 아래 부서 {o.subs} · 코드 {o.code}" for o in exact))


def _expand_organ(ecm: Ecm, organ: Organ, company: str, with_subs: bool) -> tuple[list[Person], list[str]]:
    """부서를 사람으로 펼친다 — 화면처럼 바로 든 사람만, ``with_subs`` 면 아래 부서를 다 내려간다. (사람, 펼친 부서 말)."""
    people, said, layer, seen = [], [], [organ.code], set()
    while layer:
        below = []
        for code in layer:
            if code in seen:
                continue
            seen.add(code)
            got = ecm.members(code, company)
            people += got
            dept = got[0].dept if got else code
            said.append(f"{dept}({code}) {len(got)} 명")
            if with_subs:
                below += [o.code for o in ecm.sub_organs(code, company)]
        layer = below
    unique = list({p.id: p for p in people}.values())
    return unique, said


def refuse_unhandled_grants(before: list[Grant]) -> None:
    """지금 명단이 이 손이 다루는 꼴인가 — 권한 셋 밖의 역할이 걸렸거나 한 사람에게 역할이 둘 넘으면 사람이 화면에서 하라고 ``EcmError``."""
    other = outside_roles(before)
    if other:
        raise EcmError("권한 셋(편집 · 복사 · 읽기)의 사람 밖의 역할이 걸린 문서다(" +
                       ", ".join(f"{g.role}/{g.cls} {g.name or g.id}" for g in other) +
                       ") — 화면이 그 역할을 다른 칸으로 옮겨 그리므로 손으로 안 바꾼다. 사람이 화면의 「컨텐츠 속성」에서 한다")
    twice = sorted({g.id for g in before if [h.id for h in before].count(g.id) > 1})
    if twice:
        raise EcmError(f"한 사람에게 역할이 둘 넘게 걸린 문서다({', '.join(twice)}) — 한 줄로 합치면 하나가 말없이 사라지므로 손으로 안 바꾼다. "
                       "사람이 화면의 「컨텐츠 속성」에서 한다")


def kept_ids(page: PropertyPage) -> set[str]:
    """이 손이 칸을 안 바꾸는 줄 — 소유자 · 본인. 공동 편집자인 본인이 제 편집 권한을 지우면 되돌릴 길이 없다."""
    return {page.value("MS_OWNER_NAME"), page.vars.get("userId", "")} - {""}


def is_org_spec(spec: str) -> bool:
    """사람 말이 조직(「org:」)을 짚었나 — 갈래는 ``spec_kind`` 가 가른다."""
    return spec_kind(spec)[0] != SPEC_PERSON


@dataclass
class AccessDraft:
    """권한 명단의 뒤 모습을 짓는 판(지금 모습) — 지금 명단 · 지킬 줄에서 시작해 말마다 얹고 빼고, 사람에게 보일 말을 모은다."""
    current: dict
    after: dict
    keep: set
    notes: list = dataclasses.field(default_factory=list)
    given: dict = dataclasses.field(default_factory=lambda: {"org": {}, "person": {}})   # 층마다 사람 열쇠 → (역할, 말)
    staying: list = dataclasses.field(default_factory=list)   # 준 칸에 이미 든 사람 — 더함에 안 서니 따로 보인다

    @classmethod
    def start(cls, before: list[Grant], keep: set[str], clear: bool) -> "AccessDraft":
        """지금 명단에서 판을 연다 — ``clear`` 면 지킬 줄만 남기고 시작한다."""
        current = {g.id: g for g in before}
        return cls(current, {i: g for i, g in current.items() if i in keep} if clear else dict(current), keep)

    def put(self, people: list[Person], role: str, spec: str) -> None:
        """사람들을 그 칸으로 뒤 명단에 얹는다 — 지킬 줄은 건너뛰고(말을 남긴다), 같은 층에서 이미 다른 칸을 받은 사람이면 멈춘다."""
        # 같은 층(조직끼리 · 사람끼리)에서 한 사람에게 다른 칸을 주면 어느 쪽인지 고르지 않는다
        layer = self.given["org" if is_org_spec(spec) else "person"]
        for p in people:
            if p.id in self.keep:
                self.notes.append(f"{p.name} 은 소유자 · 본인이라 이 손이 칸을 안 바꾼다")
                continue
            prior = layer.get(p.id)
            if prior and prior[0] != role:
                raise ArgsError(f"{p.label()} 에게 「{prior[1]}」 로 {ACCESS_ROLES[prior[0]]}, 「{spec}」 로 {ACCESS_ROLES[role]} 를 함께 준다 — "
                               "어느 쪽인지 고르지 않는다. 그 사람을 사람으로 따로 짚거나(사람의 말이 조직의 말을 이긴다) 하나를 뺀다")
            layer[p.id] = (role, spec)
            self.after[p.id] = _grant_of(p, role)
            if p.id in self.current and self.current[p.id].role == role:
                self.staying.append(f"{ACCESS_ROLES[role]} · {p.label()}")

    def take(self, ids: set[str], *, org: bool) -> None:
        """뒤 명단에서 그 사람들을 뺀다 — 조직으로 들어갈 참이던 사람을 사람으로 빼면 그렇다고 말을 남긴다."""
        for i in ids:
            gone = self.after.pop(i, None)
            if not org and gone and i not in self.current:
                self.notes.append(f"{gone.label()} 은 조직으로 들어갈 참이었는데 빼라고 해서 안 넣는다")

    def named(self, spec: str) -> Grant:
        """「이름」 · 「이름/메일」 로 지금 · 뒤 명단에서 꼭 한 사람을 고른다 — 여럿 · 없음 · 지킬 줄이면 ``ArgsError``."""
        name, _, email = spec.partition("/")
        pool = {**self.current, **self.after}
        hit = [g for g in pool.values() if g.name == name.strip() and (not email.strip() or same_mail(email, g.email))]
        if len(hit) > 1:
            raise ArgsError(f"「{spec}」 가 명단에 {len(hit)} 명이다 — 이름/메일ID 로 다시 준다:\n" +
                           "\n".join(f"  {g.label()}" for g in hit))
        if not hit:
            raise ArgsError(f"「{spec}」 는 이 문서의 권한 명단에 없다 — 뺄 것이 없다")
        if hit[0].id in self.keep:
            raise ArgsError(f"「{spec}」 는 소유자 · 본인이라 이 손이 칸을 안 바꾼다 — 제 권한은 사람이 화면의 「컨텐츠 속성」에서 바꾼다")
        return hit[0]

    def note_staying(self) -> None:
        """준 칸에 이미 든 사람을 한 줄로 말에 더한다(그대로 둔다)."""
        if self.staying:
            self.notes.append(f"준 칸에 이미 든 사람 {len(self.staying)} 명(그대로 둔다) — " + " · ".join(dict.fromkeys(self.staying)))

    def changes(self) -> tuple[tuple[Grant, ...], tuple[Grant, ...], tuple[tuple[Grant, Grant], ...]]:
        """지금 명단과 뒤 명단의 더함 · 뺌 · 옮김(앞, 뒤)."""
        added = tuple(g for i, g in self.after.items() if i not in self.current)
        removed = tuple(g for i, g in self.current.items() if i not in self.after)
        moved = tuple((self.current[i], g) for i, g in self.after.items() if i in self.current and self.current[i].role != g.role)
        return added, removed, moved


def grant_spec(ecm: Ecm, draft: AccessDraft, word: str, spec: str, company: str, with_subs: bool, picked: dict) -> None:
    """줄 말 하나를 사람들로 풀어(조직은 그 순간의 부서원으로 펼치고, 사람은 꼭 한 사람을 골라) 그 칸으로 뒤 명단에 얹는다."""
    role = ACCESS_OF_WORD[word]
    if is_org_spec(spec):
        people, said = _expand_organ(ecm, _pick_organ(ecm, spec, company), company, with_subs)
        if not people:
            raise ArgsError(f"「{spec}」 에 든 사람이 없다 — 아래 부서에만 사람이 있으면 --with-subs 로 준다")
        draft.notes.append(f"{ACCESS_ROLES[role]} 조직 — {' · '.join(said)}" + ("" if with_subs else " (바로 든 사람만 · 아래 부서는 --with-subs)"))
    else:
        if spec not in picked:
            picked[spec] = _pick_person(ecm, spec, company)
        people = [picked[spec]]
    draft.put(people, role, spec)


def revoke_spec(ecm: Ecm, draft: AccessDraft, spec: str, company: str, with_subs: bool) -> None:
    """거둘 말 하나를 사람 열쇠들로 풀어(조직은 부서원으로 펼치고 지킬 줄은 빼며, 사람은 명단에서 꼭 한 사람) 뒤 명단에서 뺀다."""
    if is_org_spec(spec):
        people, said = _expand_organ(ecm, _pick_organ(ecm, spec, company), company, with_subs)
        if not people:
            raise ArgsError(f"「{spec}」 에 든 사람이 없다 — 뺄 것이 없다. 부서 코드 · 이름을 본다(아래 부서에만 사람이 있으면 --with-subs)")
        draft.notes.append(f"뺄 조직 — {' · '.join(said)}")
        if any(p.id in draft.keep for p in people):
            draft.notes.append("소유자 · 본인은 조직으로 빼도 칸을 안 바꾼다")
        draft.take({p.id for p in people} - draft.keep, org=True)
    else:
        draft.take({draft.named(spec).id}, org=False)


def try_spec(problems: list[str], origins: dict[str, str] | None, spec: str, run, *args) -> None:
    """말 하나를 풀다 멈추면 그 까닭을(온 자리 「파일:줄」 을 앞에 붙여) 모아 두고 다음 말로 간다 — 다 모은 뒤 한 번에 멈춘다."""
    try:
        run(*args)
    except ArgsError as exc:
        where = (origins or {}).get(spec)
        problems.append(f"{where}: {exc}" if where else str(exc))


def stop_on_problems(problems: list[str]) -> None:
    """못 푼 말이 있으면 일부만 짓지 않고 그 말들을 다 대며 ``ArgsError`` 로 멈춘다."""
    if len(problems) == 1:
        raise ArgsError(problems[0])
    if problems:
        raise ArgsError(f"못 푼 말이 {len(problems)} 개라 아무것도 짓지 않았다 — 다 고쳐 다시 부른다:\n" + "\n".join(f"- {p}" for p in problems))


def plan_access(ecm: Ecm, object_id: str, *, grant: list[tuple[str, str]] = (), revoke: list[str] = (),
                clear: bool = False, with_subs: bool = False, origins: dict[str, str] | None = None) -> AccessPlan:
    """권한 한 판을 짓는다 — 서버를 바꾸지 않는다. ``grant`` 는 (edit|copy|read, 사람 말) 들, ``revoke`` 는 뺄 사람 말 들.
    사람 말은 「이름」 · 「이름/메일ID」 · 「이름/메일 주소」 · 「org:부서코드」 · 「org:부서 이름」. 조직은 그 순간의 부서원으로
    펼치고(화면과 같다), ``with_subs`` 면 아래 부서까지. 이미 다른 칸에 든 사람에게 주면 그 칸으로 옮긴다. 소유자 · 본인의 줄은 주기 ·
    거두기 · 비우기 어느 것도 안 바꾼다. 같은 층에서 한 사람에게 다른 칸을 주면 멈춘다.
    못 푼 말(없는 사람 · 동명이인 · 여러 부서)이 하나라도 있으면 일부만 짓지 않고, 못 푼 말을 다 대며 ``ArgsError`` 로 멈춘다 —
    ``origins`` 는 사람 말 → 그 말이 온 자리(「파일:줄」)로, 그 말 앞에 붙인다.
    안 잰 꼴의 문서면 ``EcmError`` 로 멈춘다."""
    object_id = _object_id(object_id)
    page, before = document_gate(ecm, object_id, "권한")
    refuse_unhandled_grants(before)
    company = ecm.company()
    draft = AccessDraft.start(before, kept_ids(page), clear)
    picked: dict[str, Person] = {}   # 같은 사람 말이 여러 칸 · 파일에 들어도 ECM 에 한 번만 묻는다
    # 못 푼 말은 모아 한 번에 낸다 — 첫 말에서 멈추면 사람이 한 줄씩 고치며 여러 번 부르고, 건너뛰면 일부만 권한을 받는다
    problems: list[str] = []
    # 조직 → 사람 차례로 둔다 — 사람으로 짚은 말(「조직은 읽기, 그중 ○○ 님은 복사」 · 「조직은 주되 ○○ 님은 빼」)이 조직의 말을 이긴다
    for org in (True, False):
        for word, spec in grant:
            if is_org_spec(spec) == org:
                try_spec(problems, origins, spec, grant_spec, ecm, draft, word, spec, company, with_subs, picked)
        for spec in revoke:
            if is_org_spec(spec) == org:
                try_spec(problems, origins, spec, revoke_spec, ecm, draft, spec, company, with_subs)
    stop_on_problems(problems)
    draft.note_staying()
    added, removed, moved = draft.changes()
    title = page.value("MS_DOC_TITLE") + "." + page.value("MS_DOC_EXTENSION")
    return AccessPlan(object_id, title, tuple(before), tuple(draft.after.values()), added, removed, moved,
                      tuple(dict.fromkeys(draft.notes)))


# 속성 저장이 안 바꿔야 하는 칸 — 보낸 뒤 다시 읽어 흔들렸나 본다. 권한 저장은 이름도 안 바꾼다(속성 저장은 이름을 바꾼다)
SAVE_WATCHED = ("ecm_security_level", "ecm_open_flag", "ecm_folder_id", "MS_OWNER_NAME")
ACCESS_WATCHED = (*SAVE_WATCHED[:3], "MS_DOC_TITLE", *SAVE_WATCHED[3:])


# 권한 · 속성 저장이 멈출 때의 말
SAVE_KEY_STALE = "확인 열쇠가 이 판과 다르다 — 미리 보기를 다시 돌려 사람에게 보인 뒤 그 열쇠로 보낸다"
ACCESS_MOVED = "미리 본 뒤 이 문서의 권한 명단이 바뀌었다 — 아무것도 안 보냈다. 미리 보기를 다시 돌린다"
PROPS_MOVED = "미리 본 뒤 이 문서의 속성이나 권한 명단이 바뀌었다 — 아무것도 안 보냈다. 미리 보기를 다시 돌린다"
ACCESS_READ_BACK = "저장은 됐다는데 다시 읽은 권한 명단이 바란 것과 다르다 — 다시 보내지 말고 ECM 화면의 「컨텐츠 속성」에서 본다"


def props_read_back_word(got: PropChange) -> str:
    """속성을 보낸 뒤 다시 읽은 값이 바란 것과 다를 때의 말 — 다시 읽은 이름 · 태그 · 완료일을 댄다."""
    return (f"저장은 됐다는데 다시 읽은 속성이 바란 것과 다르다(이름 {got.title!r} · 태그 {list(got.tags or ())} · 완료일 "
            f"{got.due}) — 다시 보내지 말고 ECM 화면의 「컨텐츠 속성」에서 본다")


def stop_on_drift(drift: list[str], head: str) -> None:
    """보낸 뒤 흔들린 칸이 있으면 ``head`` 로 시작하는 말로 멈춘다 — 사람이 화면에서 바로 되돌린다."""
    if drift:
        raise EcmError(f"{head}({', '.join(drift)})이 바뀌었다 — ECM 화면의 「컨텐츠 속성」에서 바로 되돌린다")


def watch(page: PropertyPage, fields) -> dict[str, str]:
    """저장을 보내기 전에 지켜볼 칸의 지금 값을 쥔다."""
    return {f: page.value(f) for f in fields}


def drifted(again: PropertyPage, kept: dict[str, str]) -> list[str]:
    """보낸 뒤 다시 읽은 속성 화면에서 쥐어 둔 값과 달라진 칸 — 쥔 차례대로."""
    return [f for f in kept if again.value(f) != kept[f]]


def document_gate(ecm: Ecm, object_id: str, what: str) -> tuple[PropertyPage, list[Grant]]:
    """속성 화면의 저장을 손으로 보내도 되는 꼴의 문서인가를 가르고 (속성 화면, 지금 권한 명단)을 낸다 — 이 손이 잰 꼴이 아니면 그
    까닭과 ``what``(권한 · 속성)을 대며 ``EcmError``. 권한 · 속성 패스의 미리 보기와 보내기가 다 이 문을 지난다."""
    page = ecm.property_page(object_id)
    why = page.unmeasured()
    if why:
        raise EcmError(f"이 문서의 {what}은 손으로 안 바꾼다 — {why}")
    return page, ecm.roles(object_id, page.value("MS_DOC_ID"))


def apply_access(ecm: Ecm, plan: AccessPlan, token: str) -> list[Grant]:
    """미리 본 한 판을 보낸다 — 열쇠가 맞고 그 사이 명단이 그대로일 때만. 보낸 뒤 명단과 속성(보안등급 · 공개 · 폴더 · 이름)을 다시
    읽어 바란 그대로인가 본다. 다시 읽은 명단을 낸다."""
    if token != plan.token:
        raise Stale(SAVE_KEY_STALE)
    page, now = document_gate(ecm, plan.object_id, "권한")
    doc_key = page.value("MS_DOC_ID")
    if access_token(plan.object_id, now, plan.after) != token:
        raise Stale(ACCESS_MOVED)
    kept = watch(page, ACCESS_WATCHED)
    ecm.save_access(page, ecm.favorites(plan.object_id, doc_key), list(plan.after), ecm.company())
    got = ecm.roles(plan.object_id, doc_key)
    if grants_key(got) != grants_key(plan.after):
        raise EcmError(ACCESS_READ_BACK)
    stop_on_drift(drifted(ecm.property_page(plan.object_id), kept), "권한은 섰는데 다른 속성")
    return got


# ── 속성 — 이름 · 태그 · 완료일(미리 보기 → 확인 열쇠 → 저장 → 다시 읽기) ─────────


@dataclass(frozen=True)
class PropsPlan:
    """속성 한 판 — 지금과 뒤(이름 · 태그 · 완료일 셋 다 찬다)와 지금 권한 명단의 지문. ``token`` 이 확인 열쇠다."""
    object_id: str
    ext: str
    before: PropChange
    after: PropChange
    grants: tuple[str, ...]     # 역할:사람 — 저장 몸이 지금 명단을 그대로 다시 싣는다

    @property
    def token(self) -> str:
        """확인 열쇠 — 문서 · 지금과 뒤의 속성 · 지금 권한 명단의 지문."""
        return token("props", self.object_id, self.before, self.after, self.grants)


def check_tags(tags) -> tuple[str, ...]:
    """태그 말들을 서버 없이 가린다 — 화면의 태그 칸과 같다(한글 · 영문 · 숫자 · 겹침 없음). 앞의 # 는 뗀다."""
    got = tuple(t.strip().lstrip("#") for t in tags if t.strip().lstrip("#"))
    bad = [t for t in got if not TAG_WORD.match(t)]
    if bad:
        raise ArgsError(f"태그는 한글 · 영문 · 숫자만 된다(빈칸 · 기호 없이 — 화면과 같다): {bad}")
    if len(set(got)) != len(got):
        raise ArgsError("같은 태그를 두 번 줬다")
    return got


def check_due(due: str) -> str:
    """완료일 — YYYY-MM-DD. 없애는 길은 없다 — 저장 몸에 화면의 「없음」(0001/01/01)을 실으면 서버는 그 칸을 안 바꾼다(쟀다)."""
    if not DATE_TEXT.match(due):
        raise ArgsError(f"완료일은 YYYY-MM-DD 꼴이다: {due!r} — 완료일을 없애는 길은 화면에도 없다")
    return due


def _tags_after(now: tuple[str, ...], *, set_to, add, drop, clear) -> tuple[str, ...] | None:
    """태그 말들 → 뒤의 태그 전체. 아무 태그 말도 없으면 None(그대로)."""
    if set_to is None and not add and not drop and not clear:
        return None
    base = [] if clear else list(set_to if set_to is not None else now)
    base += [t for t in add if t not in base]
    missing = [t for t in drop if t not in base]
    if missing:
        raise ArgsError(f"뺄 태그가 그 문서에 없다: {missing} — 지금 태그: {', '.join(now) or '(없음)'}")
    after = tuple(t for t in base if t not in drop)
    if len(after) > TAG_MAX:
        raise ArgsError(f"태그는 {TAG_MAX} 개까지다(화면과 같다) — 뒤에 {len(after)} 개가 된다")
    return after


def _props_now(page: PropertyPage) -> PropChange:
    """속성 화면이 든 지금 이름 · 태그 · 완료일. 완료일은 숨은 칸 ``MS_DUE_DATE``(YYYY-MM-DD)다 — 고르는 칸 ``ecm_EndDate`` 는 화면이 늘
    ``0001/01/01`` 로 그린다(쟀다). 등록하면 서버가 등록일 + 14 일을 넣는다."""
    return PropChange(page.value("MS_DOC_TITLE"), page_tags(page), page.inputs.get("MS_DUE_DATE", "").strip() or SCREEN_NO_DUE)


def _props_gate(ecm: Ecm, object_id: str) -> tuple[PropertyPage, list[Grant]]:
    """속성을 손으로 바꿔도 되는 문서인가 — 권한 패스와 같은 문(``document_gate``)에 권한 셋 밖의 역할을 더 막는다. 저장 몸이 속성 칸
    전부와 지금 권한 명단을 다시 싣기 때문이다."""
    page, grants = document_gate(ecm, object_id, "속성")
    if outside_roles(grants):
        raise EcmError("권한 셋(편집 · 복사 · 읽기)의 사람 밖의 역할이 걸린 문서다 — 저장 몸이 그 명단을 다시 싣는 꼴은 안 쟀다. "
                       "사람이 화면의 「컨텐츠 속성」에서 한다")
    return page, grants


def plan_props(ecm: Ecm, object_id: str, *, title: str | None = None, tags=None, add_tags=(), drop_tags=(),
               clear_tags: bool = False, due: str | None = None) -> PropsPlan:
    """속성 한 판을 짓는다 — 서버를 바꾸지 않는다. ``tags`` 는 뒤의 태그 전체, ``add_tags`` · ``drop_tags`` · ``clear_tags`` 는 지금
    태그에서 더하고 빼기. 지금과 같으면 ``ArgsError``."""
    object_id = _object_id(object_id)
    page, grants = _props_gate(ecm, object_id)
    before = _props_now(page)
    after_tags = _tags_after(before.tags, set_to=check_tags(tags) if tags is not None else None, add=check_tags(add_tags),
                             drop=check_tags(drop_tags), clear=clear_tags)
    after = PropChange(check_title(title) if title is not None else before.title,
                       after_tags if after_tags is not None else before.tags,
                       check_due(due) if due is not None else before.due)
    if after == before:
        raise ArgsError("바꿀 속성이 지금과 같다 — 아무것도 안 짓는다")
    return PropsPlan(object_id, page.value("MS_DOC_EXTENSION"), before, after, grants_key(grants))


def apply_props(ecm: Ecm, plan: PropsPlan, token: str) -> PropChange:
    """미리 본 한 판을 보낸다 — 열쇠가 맞고 그 사이 속성 · 명단이 그대로일 때만. 보낸 뒤 이름 · 태그 · 완료일과 다른 칸(보안등급 ·
    공개 · 폴더 · 소유자 · 권한 명단)을 다시 읽어 바란 그대로인가 본다. 다시 읽은 속성을 낸다."""
    if token != plan.token:
        raise Stale(SAVE_KEY_STALE)
    page, grants = _props_gate(ecm, plan.object_id)
    if _props_now(page) != plan.before or grants_key(grants) != plan.grants:
        raise Stale(PROPS_MOVED)
    doc_key = page.value("MS_DOC_ID")
    kept = watch(page, SAVE_WATCHED)
    ecm.save_props(page, ecm.favorites(plan.object_id, doc_key), grants, ecm.company(), plan.after)
    again = ecm.property_page(plan.object_id)
    got = _props_now(again)
    if got != plan.after:
        raise EcmError(props_read_back_word(got))
    drift = drifted(again, kept) + (["권한 명단"] if grants_key(ecm.roles(plan.object_id, doc_key)) != plan.grants else [])
    stop_on_drift(drift, "속성은 섰는데 다른 칸")
    return got


# ── 편집취소 — 잠근 이가 나인 문서의 잠금을 푼다(편집 중 고친 것은 버린다) ─────────

@dataclass(frozen=True)
class Cancelled:
    """편집취소 한 판의 결과 — 편집 창을 닫은 형편 · 에이전트의 답 · 편집완료 창이 남았나."""
    closed: str             # 편집으로 받은 그 문서의 창 — closed · not-found
    agent: str              # 에이전트의 답(OK 따위) — 판정은 다시 읽은 잠금으로 한다
    window_left: bool       # 에이전트의 편집완료 창이 남았나 — 저장된 고침이 있던 창을 닫으면 뜨고, 편집취소 뒤에도 안 닫힌다(쟀다)


def cancel_edit(ecm: Ecm, agent: "Agent", object_id: str, *, discard: bool = False, wait: float = CANCEL_WAIT) -> Cancelled:
    """화면의 「편집취소」와 같은 차례 — 잠근 이가 나인가(``checkuser``)를 보고, 편집으로 받은 그 문서의 창이 떠 있으면 닫은 뒤
    서버 걸음(``cancelcheckout``)과 에이전트 한 줄(``cancelcheckout␈<열쇠>``)을 보내고 다시 읽어 풀렸나 본다. 잠금을 푸는 것은
    에이전트 줄이다 — 서버 걸음만으로는 잠금이 남았고, 창이 떠 있으면 에이전트는 「현재 파일을 사용 중입니다.」로 안 풀었다(쟀다).

    창에 저장 안 된 고침이 있으면 ``discard`` 없이는 아무것도 안 보내고 멈춘다. 안 잠긴 문서 · 남이 잠근 문서도 아무것도 안
    보낸다 — 남의 편집을 버리게 된다."""
    object_id = _object_id(object_id)
    refuse_unless_mine(ecm, object_id)
    closed = close_edit_window(agent, object_id, discard)
    ecm.cancel_checkout(object_id)
    answer = agent.cancel(object_id)
    wait_unlocked(ecm, object_id, answer, wait)
    return Cancelled(closed, answer, checkin_pending(object_id))   # 사람이 먼저 오피스를 닫았어도 그 창은 뜬다


def refuse_unless_mine(ecm: Ecm, object_id: str) -> None:
    """내가 편집으로 잠근 문서가 아니면 아무것도 안 보내고 ``EcmError`` — 안 잠겼거나 · 잠금을 못 읽었거나 · 남이 잠갔다."""
    state = ecm.doc_state(object_id)
    if state.locked is not True:
        raise EcmError(f"이 문서는 편집으로 잠겨 있지 않다(잠금 {'못 읽었다' if state.locked is None else '없음'}) — 풀 것이 없다")
    if not ecm.checked_out_by_me(object_id):
        raise EcmError(f"이 문서는 다른 사람({state.lock_owner or '누군가'})이 편집 중이다 — 편집취소하면 그 사람이 고친 것이 사라져 이 "
                       "손은 안 푼다. 그 사람에게 편집완료 · 편집취소를 청한다")


def close_edit_window(agent: "Agent", object_id: str, discard: bool) -> str:
    """편집으로 받은 그 문서의 가장 새 창을 닫고 창의 상태(closed · not-found)를 낸다 — 저장 안 된 고침이 있으면 ``discard`` 없이는
    아무것도 안 보내고 ``EcmError``."""
    path = agent.newest_edit_file(object_id)
    if path is None:
        return "not-found"
    got, _ = _close(path, OFFICE_BY_EXT[path.suffix.lower()], CANCEL_FIND_WAIT, require_clean=not discard)
    if got == "dirty":
        raise EcmError("편집 창에 저장 안 된 고침이 있다 — 아무것도 안 보냈다. 버려도 되는지 사람에게 물은 뒤 --discard 로 다시 "
                       "부르고, 남기려면 preview-checkin 으로 올린다")
    return got


def wait_unlocked(ecm: Ecm, object_id: str, answer: str, wait: float) -> None:
    """편집취소를 보낸 뒤 다시 읽은 잠금이 풀릴 때까지 기다린다 — 시한 안에 안 풀리면 에이전트 답을 대고 ``EcmError``."""
    deadline = time.monotonic() + wait
    while ecm.doc_state(object_id).locked is not False:
        if time.monotonic() >= deadline:
            raise EcmError(f"편집취소를 보냈는데(에이전트 답 {answer!r}) 문서가 아직 잠겨 있다 — 사람이 ECM 화면에서 「편집취소」를 누른다")
        time.sleep(POLL)


def reader_path() -> pathlib.Path:
    """글자를 뽑는 손(read-drm.ps1)의 자리 — 환경변수 ``ECM_DRM_READER``, 비었으면 ``DEFAULT_READER``."""
    return pathlib.Path(os.environ.get("ECM_DRM_READER", "").strip() or DEFAULT_READER).expanduser()


READER_UNREADABLE = "[못 읽는 꼴]"   # 읽는 손(read-drm.ps1)이 받는 확장자가 아닌 파일에 다는 줄 머리 — 그 꼴은 화면(open)으로 넘긴다


def extract_text(path: pathlib.Path, *, reader: pathlib.Path | None = None) -> tuple[str, str]:
    """받은 파일을 drm-office-read 의 읽는 손에 넘겨 (글자, 그 손의 한 줄)을 낸다. 평문은 임시 폴더째 바로 지운다.

    ``-NoKeep`` 을 준다 — 읽는 손이 제 자리에 한 벌 더 남기면 등급 문을 안 지나는 사본이 생긴다."""
    reader = reader or reader_path()
    if not reader.exists():
        raise ReadError(f"글자를 뽑는 손이 없다: {reader} — 스킬 drm-office-read 가 깔렸는지 본다")
    out_dir = pathlib.Path(tempfile.mkdtemp(prefix="ecm-read-"))
    try:
        proc = _powershell(reader, str(path), "-OutDir", str(out_dir), "-NoKeep", READER_GATE_FLAG, timeout=READ_TIMEOUT)
        lines = [l for l in proc.stdout.decode("utf-8", "replace").splitlines() if l.strip()]
        summary = next((l for l in lines if l.startswith("[")), "")
        texts = sorted(out_dir.glob(f"*{TEXT_EXT}"))
        if summary.startswith(READER_UNREADABLE):
            raise ReadError(f"이 꼴({path.suffix})은 읽는 손이 글자로 뽑지 않는다 — 화면에서 보려면 open 으로 연다")
        if proc.returncode != 0 or not texts:
            why = summary or (lines[-1] if lines else proc.stderr.decode("utf-8", "replace").strip()[-300:])
            raise ReadError(f"읽는 손이 글자를 못 냈다 — {why or '까닭 없음'}")
        return texts[0].read_text(encoding="utf-8-sig"), summary
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def text_dir() -> pathlib.Path:
    """read 가 뽑은 글자를 남기는 자리 — 환경변수 ``ECM_TEXT_DIR``, 비었으면 ``TEXT_DIR``."""
    return pathlib.Path(os.environ.get(TEXT_DIR_ENV, "").strip() or TEXT_DIR).expanduser()


def kept_text(object_id: str) -> pathlib.Path | None:
    """그 문서 열쇠로 남겨 둔 글자 파일 — 없으면 None. 판이 오르면 열쇠가 바뀌므로 열쇠가 같으면 같은 판의 글자다."""
    if not OBJECT_ID.match(object_id):
        return None
    found = sorted(text_dir().glob(f"*-{object_id.lower()}{TEXT_EXT}"))
    return found[0] if found else None


def keep_text(text: str, summary: str, source: pathlib.Path, object_id: str) -> pathlib.Path:
    """뽑은 글자를 ``text_dir()`` 에 남기고 그 경로를 낸다 — 이름은 받은 파일의 이름과 문서 열쇠, 머리는 읽는 손의 한 줄과
    열쇠 · 받은 파일의 자리 · 뽑은 때다. 같은 열쇠를 다시 받으면(``--fresh``) 같은 이름이라 그 장을 덮어쓴다."""
    folder = text_dir()
    folder.mkdir(parents=True, exist_ok=True)
    key = object_id.lower()
    name = re.sub(r"[^\w.\-]+", "_", source.stem)[:80].strip("_") or "document"
    path = folder / f"{name}-{key}{TEXT_EXT}"
    head = f"{summary}\n문서 열쇠 {key}{KEPT_SOURCE_WORD}{source}{KEPT_WHEN_WORD}{time.strftime('%Y-%m-%d %H:%M')}"
    path.write_text(head + TEXT_SPLIT + text, encoding="utf-8")
    return path


def read_kept_file(path: pathlib.Path) -> tuple[str, str, pathlib.Path | None]:
    """남긴 글자 파일을 (머리, 글자, 받은 파일의 자리 · 머리에 없으면 None)으로 푼다 — 쓰는 쪽(``keep_text``)과 같은 낱말
    (``TEXT_SPLIT`` · ``KEPT_SOURCE_WORD`` · ``KEPT_WHEN_WORD``)로 읽는다. 가르는 줄이 없는 파일은 통째로 글자다."""
    head, split, text = path.read_text(encoding="utf-8").partition(TEXT_SPLIT)
    if not split:
        head, text = "[읽음]", head
    _, _, rest = head.partition(KEPT_SOURCE_WORD)
    return head, text, (pathlib.Path(rest.partition(KEPT_WHEN_WORD)[0]) if rest else None)


def read_kept(ecm: Ecm, object_id: str, *, ai_ok: bool = False) -> pathlib.Path | None:
    """남겨 둔 글자가 있으면 등급 문(``check_readable``)을 지난 뒤 그 파일을 낸다 — 없으면 None. 문서는 받지 않는다.

    등급 문이 여기서도 서는 까닭 — 남긴 뒤 기밀 · 핵심기술이 된 문서를 막는다."""
    path = kept_text(object_id)
    if path is None:
        return None
    check_readable(ecm, object_id, ai_ok=ai_ok)
    return path


def _tell_text(head: str, text: str, path: pathlib.Path, *, as_file: bool) -> None:
    """머리와 글자를 낸다 — 한 답(``ep_session.OUT_BYTES``)에 드는 글자는 화면에, 안 드는 글자는(``as_file`` 이면 짧아도) 남긴
    파일의 경로만. 화면에 찍으면 통째로 실리거나 잘리고, 파일이면 모델이 나눠 읽고 찾는다."""
    whole = f"{head}\n글자를 남겼다: {path} — 이 문서를 다시 보려면 같은 열쇠로 read 를 부른다(다시 받지 않고 이 파일로 답한다)\n---\n{text}\n"
    if as_file or len(whole.encode("utf-8")) > ep_session.OUT_BYTES:
        print(head)
        print(f"글자 {len(text)} 자는 파일에 있다: {path} — 머리 두 줄과 --- 아래가 글자다. 앞에서부터 나눠 읽거나 낱말로 찾아 필요한 "
              "대목만 본다(통째로 읽지 않는다). 이 문서를 다시 보려면 같은 열쇠로 read 를 부른다(다시 받지 않고 이 파일로 답한다)")
        return
    print(whole, end="")


def tell_read(got: ReadResult, object_id: str, *, as_file: bool = False) -> None:
    """읽은 결과로 답한다 — 글자를 늘 파일로 남기고(``keep_text``) 그 파일과 함께 말한다(``read_words``)."""
    summary = got.summary or "[읽음]"
    read_words(got, summary, keep_text(got.text, summary, pathlib.Path(got.opened.path), object_id), as_file=as_file)


def read_words(got: ReadResult, summary: str, path: pathlib.Path, *, as_file: bool) -> None:
    """읽은 결과의 말 — 머리(읽는 손의 한 줄 · 받은 파일 · 창)와 글자를 ``_tell_text`` 의 갈래로 낸다."""
    head = "\n".join([summary, *_describe_open(got.opened, gated=True), f"창: {WINDOW_WORD[got.window]}"])
    _tell_text(head, got.text, path, as_file=as_file)


def tell_kept(path: pathlib.Path, *, as_file: bool = False) -> None:
    """남겨 둔 글자로 답한다 — 남긴 파일을 풀고(``read_kept_file``) 받은 파일이 아직 있나 본 뒤(``still_received``) 말한다(``kept_words``)."""
    head, text, received = read_kept_file(path)
    kept_words(head, text, path, still_received(received), as_file=as_file)


def still_received(received: pathlib.Path | None) -> pathlib.Path | None:
    """남긴 글자가 가리키는 받은 파일이 아직 디스크에 있으면 그 자리 — 에이전트가 비웠으면 None."""
    return received if received is not None and received.is_file() else None


def kept_words(head: str, text: str, path: pathlib.Path, received: pathlib.Path | None, *, as_file: bool) -> None:
    """남긴 글자로 한 답의 말 — 문서를 받지 않았다는 것과 다시 받아야 하는 자리. ``received`` 는 아직 있는 받은 파일이다."""
    if received is not None:   # 에이전트가 아직 안 비웠다 — 그림은 그 파일로 뜨고, 앞서 뜬 것이면 뜨는 손이 알아본다
        visuals = (f"받은 파일이 남아 있다: {received} — {RECEIVED_GATED}(앞서 뜬 그림이면 앱을 안 띄운다). 글자가 이상하면 --fresh "
                   "로 다시 받는다")
    else:
        visuals = "표 · 그림을 떠야 하거나(받은 파일이 있어야 한다) 글자가 이상하면 --fresh 로 다시 받는다"
    note = f"남긴 글자다 — 문서를 다시 받지 않았다(창도 안 떴다). 다음: {visuals}"
    _tell_text(f"{head}\n{note}", text, path, as_file=as_file)


def gate(security: Security | None, *, ai_ok: bool, stopped: str, unread: str = "") -> Security | None:
    """등급 문의 판정 하나 — 문서의 글자 · 그림을 대화로 들이는 손가락(읽기 · 편집 열기 · 고치기 · 올리기 미리 보기)이 다 이것을
    지난다. 기밀 · 핵심기술 문서면 ``Classified``, 등급을 못 읽었으면(``security`` 가 None) ``SecurityUnread`` 로 멈추고, 그 말이
    멈춘 자리(``stopped``)와 사람에게 물을 것(``ASK_BEFORE_AI``)을 든다. ``unread`` 는 못 읽은 까닭이다.

    ``ai_ok`` 는 사람이 그 문서를 AI 로 보내도 된다고 답한 뒤에만 준다 — 그때는 묻는 문서도 넘긴다(못 읽은 판은 None)."""
    if security is None:
        if ai_ok:
            return None
        raise SecurityUnread(f"보안등급을 못 읽어({unread or '속성 화면에 등급 칸이 없다'}) {stopped}. {ASK_BEFORE_AI}")
    if security.ask_before_ai and not ai_ok:
        what = " · ".join(w for w, on in ((security.name, security.classified), ("핵심기술", security.core)) if on)
        raise Classified(f"{what} 문서라 {stopped}. {ASK_BEFORE_AI}")
    return security


def check_readable(ecm: Ecm, object_id: str, *, ai_ok: bool = False, stopped: str = GATE_RECEIVE) -> Security | None:
    """속성 화면을 읽어(``Ecm.security``) 등급 문(``gate``)을 지난다 — ``Security`` 를 낸다.

    ⚠ 받는 요청보다 먼저 부른다 — 받은 뒤 막으면 감긴 파일이 이미 PC 에 와 있다."""
    try:
        security = ecm.security(object_id)
    except SecurityUnread as exc:
        return gate(None, ai_ok=ai_ok, stopped=stopped, unread=str(exc))
    return gate(security, ai_ok=ai_ok, stopped=stopped)


def read_document(ecm: Ecm, agent: Agent, object_id: str, *, allow_picker: bool = False,
                  reader: pathlib.Path | None = None, ai_ok: bool = False) -> ReadResult:
    """보안등급을 보고(``check_readable``) → 열고 → 에이전트가 띄운 창을 닫고 → 받은 파일에서 글자를 뽑아 ``ReadResult`` 를 낸다.

    닫는 것이 먼저다 — 오피스가 그 파일을 쥐고 있으면 읽는 손이 파일 머리를 못 읽는다. 받은 파일은 그 자리에 남는다.
    """
    check_readable(ecm, object_id, ai_ok=ai_ok)
    opened = open_document(ecm, agent, object_id, allow_picker=allow_picker)
    window = close_window(opened.path, viewer_of(opened.progid))
    try:
        text, summary = extract_text(opened.path, reader=reader)
    except ReadError as exc:
        raise ReadError(f"{exc} — 받은 파일: {opened.path}") from exc
    return ReadResult(text, summary, opened, window)


# ── 명령줄 ───────────────────────────────────────────────────────────────

# 받은 파일 줄의 뒤 — 에이전트 폴더의 파일을 drm-office-read 로 열어도 된다는 말은 등급 문을 지난 답만 낸다(그 스킬이 이 말을 따른다)
RECEIVED_GATED = (f"등급 문을 지났다: 표 · 그림은 이 경로로 스킬 drm-office-read 의 그림 뜨기를 {READER_GATE_FLAG} 를 붙여 부른다"
                  "(그 손은 이 깃발 없이는 문서함 받은 파일을 안 연다)")
RECEIVED_SHOWN = ("사람이 보는 창이라 등급 문을 안 지났다: 이 파일은 스킬 drm-office-read 로 열지 않는다 — 글자 · 표 · 그림이 필요하면 "
                  "read {object_id} 로 받는다")
WINDOW_WORD = {"closed": "닫았다", "not-found":f"{WINDOW_WAIT:.0f} 초 안에 못 찾았다 — 떠 있으면 사람이 닫는다",
               "not-front": "다른 pdf 가 앞 탭이라 안 건드렸다 — 다 봤으면 사람이 그 탭을 닫는다",
               "not-office": "닫을 줄 아는 앱(오피스 · Acrobat)이 아니라 안 닫았다 — 다 봤으면 사람이 닫는다"}


def _print_docs(docs: list[Doc], page: int, where: str = "내 문서함", *, mixed: bool = False, folder: str = "") -> None:
    """목록 한 쪽의 말 — 머리(자리 · 문서함 안 폴더 ``folder``)와 줄마다 한 줄. ``mixed`` 면(여러 문서함이 섞인 왼쪽 메뉴의 목록) 줄마다
    그 문서가 든 문서함을 댄다."""
    print(f"{where}{f' · 폴더 {folder}' if folder else ''} — {len(docs)} 건 (쪽 {page})")
    for i, d in enumerate(docs, 1):
        bits = [f"{d.name}" + (f".{d.ext}" if d.ext and not d.name.lower().endswith("." + d.ext.lower()) else ""),
                f"크기 {d.size}" if d.size else "", f"고침 {d.modified}" if d.modified else "",
                f"판 {d.version}" if d.version else "", f"올린 이 {d.owner}" if d.owner else "",
                f"폴더 {d.folder_path}" if d.folder_path else "", f"보안 {level_name(d.security)}" if d.security else "",
                f"잠금 {d.locked_by}" if d.locked_by else "",
                f"문서함 {d.cabinet_name}" if d.cabinet_name and mixed else "",
                f"공유한 이 {d.shared_by} · 역할 {ACCESS_ROLES.get(d.role, d.role)}" if d.shared_by else "",
                f"요청한 이 {d.requester} · 요청 {d.requested} · 상태 {d.request_status}" if d.requester else "",
                f"지운 날 {d.deleted}" if d.deleted else "", f"쓴 때 {d.used}" if d.used else "",
                f"id {d.object_id}"]
        print(f"{i:>3}. " + " · ".join(b for b in bits if b))


def _print_grants(grants) -> None:
    """권한 명단의 말 — 편집 · 복사 · 읽기 역할마다 사람 수와 사람, 그 밖의 역할은 줄마다."""
    if not grants:
        print("  (소유자 말고는 권한 명단이 비었다)")
    for role in ("R", "S", "V"):
        mine = [g for g in grants if g.role == role]
        if mine:
            print(f"  {ACCESS_ROLES[role]} — {len(mine)} 명")
            for g in mine:
                print(f"    {g.label()}")
    for g in (g for g in grants if g.role not in ACCESS_ROLES):
        print(f"  역할 {g.role}/{g.cls} — {g.label()}")


def _print_plan(plan: "AccessPlan") -> None:
    """권한 미리 보기의 말 — 지금 → 뒤 사람 수 · 덧붙인 말 · 더함 · 뺌 · 옮김 · 뒤 명단 · 확인 열쇠와 다음 걸음."""
    print(f"{plan.title} (id {plan.object_id}) — 지금 {len(plan.before)} 명 → 뒤 {len(plan.after)} 명")
    for note in plan.notes:
        print(f"  · {note}")
    for title, rows in (("더함", plan.added), ("뺌", plan.removed)):
        print(f"{title} {len(rows)} 명")
        for g in rows:
            print(f"  {ACCESS_ROLES.get(g.role, g.role)} · {g.label()}")
    print(f"옮김 {len(plan.moved)} 명")
    for old, new in plan.moved:
        print(f"  {old.label()} — {ACCESS_ROLES[old.role]} → {ACCESS_ROLES[new.role]}")
    print("뒤 명단:")
    _print_grants(plan.after)
    print(f"확인 열쇠 {plan.token}")
    print("사람이 이 명단 그대로 바꾸자고 하면 같은 인자에 apply-access · --confirm <열쇠> 로 보낸다.")


def _describe_open(opened: Opened, *, gated: bool, object_id: str = "") -> list[str]:
    """받은 파일과 기본 앱의 두 줄 — 받은 파일 줄은 등급 문을 지났나(``gated``)에 따라 그 파일을 drm-office-read 로 열어도 되나를 든다."""
    app = f"기본 앱 {opened.progid or '사람이 고르는 창'}" + (" (이번에 적었다)" if opened.app_written else "")
    after = RECEIVED_GATED if gated else RECEIVED_SHOWN.format(object_id=object_id)
    return [f"받은 파일: {opened.path} — {after}", app]


def _print_changed(done: Changed) -> None:
    """고친 뒤의 말 — 고친 것 · 넣은 것마다 한 줄과 저장했나."""
    for a in done.applied:
        if a.get("op") == "replace":
            print(f"고침 · {a.get('where')}: 「{a.get('old')}」 → 「{a.get('new')}」")
        else:
            print(f"넣음 · {a.get('where')}: {pathlib.Path(str(a.get('file', ''))).name}")
    print("저장했다 — 창은 그대로 떠 있다" if done.saved else "저장할 고침이 없었다 — 창의 판이 디스크의 판이다")


def _print_checkin_plan(plan: CheckinPlan) -> None:
    """올리기 미리 보기의 말 — 문서 · 판 · 수정 내용 · 올라갈 판 · 확인 열쇠와 다음 걸음."""
    print(f"올리기 미리 보기 — {plan.name} (id {plan.object_id})")
    print(f"지금 판 {plan.version} → 다음 판(편집완료 창의 지금보다 큰 판 — 지금 판을 덮어쓰지 않는다)")
    print(f"수정 내용: {plan.desc}")
    print("올라갈 판: " + ("사람이 문서 창을 닫았다 — 디스크에 저장된 판" if plan.closed else
                       "창의 그 문서 — 방금 저장했다" if plan.saved else "창의 그 문서 — 이미 저장돼 있다"))
    print(f"확인 열쇠 {plan.token}")
    print(f"다음: 고친 자리를 스킬 drm-office-read 로 {READER_GATE_FLAG} 를 붙여 찍어 사람에게 보이고(받은 파일: {plan.path}), 사람이 이대로 올리자고 하면 "
          f"checkin {plan.object_id} <받은 파일> --desc <같은 글> --confirm <열쇠>. 그 사이 문서를 고치거나 저장하면 열쇠가 바뀐다 — "
          f"그만두려면 {CANCEL_NEXT.format(object_id=plan.object_id)}")


def _print_register_plan(plan: RegisterPlan) -> None:
    """등록 미리 보기의 말 — 파일 · 이름 · 자리 · 보안 · 확인 열쇠와 다음 걸음."""
    pair = (plan.security, plan.open_flag)
    print(f"등록 미리 보기 — {plan.path.name} ({plan.size:,} 바이트)")
    print(f"이름: {plan.title}.{plan.ext}")
    print(f"자리: {plan.cabinet_name or plan.cabinet} {FOLDER_SEP} {path_word(plan.folder_path)} (폴더 {plan.folder})")
    print(f"보안: {SECURITY_PAIRS[pair]} ({plan.security}/{plan.open_flag})" + (f" — {AUDIENCE[pair]}" if pair in AUDIENCE else ""))
    print(f"확인 열쇠 {plan.token}")
    print("다음: 사람이 이 자리 · 보안등급 그대로 올리자고 하면 같은 인자에 register · --confirm <열쇠>. 파일을 다시 지었으면 열쇠가 바뀐다")


AI_OK_HELP = "기밀 · 핵심기술 · 등급을 못 읽은 문서를 받는다 — 사람이 그 문서를 AI 로 보내도 된다고 답한 뒤에만 준다"
DEFAULT_APP_NEXT = ("다음: 사람이 「열 때 뜨는 창에서 고르겠다」 하면 open · read 에 --allow-picker 를 붙이되 그 창에서 「항상 이 앱 사용」을 "
                    "누르라고 먼저 알린다 — edit 는 기본 앱을 골라 둔 뒤에만 연다")


def changes_of(args) -> Changes:
    """명령줄의 바꿀 것 → ``Changes``. 조각 파일은 ``ep_command.text_file`` 로 읽는다 — UTF-8 · 앞의 BOM 과 끝 줄바꿈은 걷는다(파워셸이
    붙인 BOM 이 새 판의 글에 안 보이는 글자로 실리지 않게). 없거나 UTF-8 이 아니면 ``ArgsError``."""
    def read(name: str) -> str:
        try:
            return ep_command.text_file(name, "--replace-file 의 파일")
        except ep_command.Stop as exc:
            raise ArgsError(str(exc)) from exc

    pairs = [(old, new) for old, new in args.replace or ()]
    for old_file, new_file in args.replace_file or ():
        pairs.append((read(old_file), read(new_file)))
    return Changes(tuple(pairs), tuple(pathlib.Path(p) for p in args.insert_from or ()), args.after)


# ── 손가락의 구현 — (명령줄 인자, ECM 서버 | None) → 종료 값 ─────────────

def cmd_session(args, ecm: Ecm) -> int:
    """ECM 세션이 살았나를 보고 말한다 — 끊겼으면 세션 종료 값."""
    alive = ecm.session_alive()
    session_words(alive)
    return EXIT_OK if alive else EXIT_SESSION


def session_words(alive: bool) -> None:
    """세션이 살았나의 말."""
    print("ECM 세션이 살았다" if alive else "ECM 세션이 끊겼다 — 스킬 ep-login 으로 다시 받는다")


def cmd_cabinets(args, ecm: Ecm) -> int:
    """볼 수 있는 문서함을 읽어 말한다."""
    cabinet_words(ecm.cabinets())
    return EXIT_OK


def cabinet_words(cabinets: list[Cabinet]) -> None:
    """문서함마다 한 줄 — 이름 · 갈래 · 내 부서인가 · 열쇠."""
    for c in cabinets:
        print(f"{c.name} · {c.kind}{' · 내 부서' if c.own else ''} · 열쇠 {c.key}")


def cmd_folders(args, ecm: Ecm) -> int:
    """문서함의 폴더 한 층을, ``--find`` 면 나무 전체에서 이름으로 찾은 폴더를 말한다."""
    cabinet = ecm.cabinet_of(args.cabinet).key
    if args.find:
        hits, near = ecm.match_folders(cabinet, args.find)
        found_folder_words(args.find, cabinet, hits, near)
        return EXIT_OK
    folder_layer_words(ecm.folders(cabinet, args.parent))
    return EXIT_OK


def found_folder_words(name: str, cabinet: str, hits: list, near: list) -> None:
    """이름으로 찾은 폴더의 말 — 꼭 맞는 것, 없으면 이름에 그 글이 든 후보(고르지 않는다). 둘 다 없으면 ``ArgsError``."""
    if not hits and not near:
        raise ArgsError(f"「{name}」 폴더가 문서함 {cabinet} 에 없다 — 이름이 꼭 맞거나 이름에 그 글이 든 폴더가 없다. "
                        f"folders {cabinet} 로 첫 층을 본다")
    if not hits:
        print(f"「{name}」 와 이름이 꼭 맞는 폴더는 없다 — 이름에 그 글이 든 폴더 {len(near)} 개다. 고르지 않았다 — 사람에게 "
              "보이고 고른 폴더의 열쇠(--folder)나 경로(--folder-path)로 간다:")
    for path, f in hits or near:
        print(f"{path_word(path)} · 열쇠 {f.id}{' · 아래 폴더 있음' if f.has_sub else ''}")


def folder_layer_words(folders: list[Folder]) -> None:
    """폴더 한 층의 말 — 이름 · 열쇠 · 아래 폴더가 있나."""
    for f in folders:
        print(f"{f.name} · 열쇠 {f.id}{' · 아래 폴더 있음' if f.has_sub else ''}")


CABINET_ALL = "all"       # --cabinet 의 「모든 문서함」 — 한 요청으로 다 묻는 꼴은 안 쟀다. 내 문서함과 볼 수 있는 문서함을 하나씩 묻는다
CABINET_ALL_MAX = 20      # all 이 묻는 문서함의 상한(내 문서함 빼고) — 제 부서가 맨 앞이다. 넘는 문서함은 이름을 대고 안 묻는다


def _places(ecm: Ecm, cabinet: str) -> tuple[list[tuple[str, str]], list[Cabinet]]:
    """--cabinet 값 → ([(문서함 열쇠 · 내 문서함은 빈 글자, 목록의 머리)], 상한을 넘어 안 물은 문서함). 열쇠로 준 문서함의 머리는
    「문서함 <열쇠>」 그대로이고, 이름 · all 로 푼 문서함은 머리에 이름을 붙인다."""
    if not cabinet:
        return [("", "내 문서함")], []
    if cabinet == CABINET_ALL:
        every = ecm.cabinets()
        asked = every[:CABINET_ALL_MAX]
        return [("", "내 문서함")] + [(c.key, f"문서함 {c.key} 「{c.name}」") for c in asked], every[CABINET_ALL_MAX:]
    found = ecm.cabinet_of(cabinet)
    return [(found.key, f"문서함 {found.key}" + (f" 「{found.name}」" if found.name else ""))], []


def _tell_skipped(skipped: list[Cabinet]) -> None:
    """all 의 상한을 넘어 안 물은 문서함이 있으면 그 이름들을 댄다."""
    if skipped:
        print(f"문서함이 많아 앞 {CABINET_ALL_MAX} 곳까지만 물었다 — 안 물은 {len(skipped)} 곳은 --cabinet <이름> 으로 묻는다: "
              + " · ".join(c.name for c in skipped))


def _list_kwargs(args) -> dict:
    """명령줄 → 목록 · 건수가 함께 받는 칸(찾는 말 · 기간 · 폴더 · 왼쪽 메뉴 목록 · 꼴)."""
    return dict(search=args.search, period=args.period, folder=args.folder, box=args.box, file_type=args.type)


def cmd_list(args, ecm: Ecm) -> int:
    """문서함마다(또는 왼쪽 메뉴의 목록) 한 쪽을 받아 말이나 JSON 줄로 내고, 안 물은 문서함을 댄다."""
    places, skipped = _places(ecm, args.cabinet) if not args.box else ([("", BOXES[args.box][1])], [])
    for key, where in places:
        docs = ecm.list(page=args.page, per_page=args.per_page, cabinet=key, sort=args.sort, direction=args.direction,
                        **_list_kwargs(args))
        if args.json:
            json_lines_words(docs, key if args.cabinet == CABINET_ALL else None)
        else:
            _print_docs(docs, args.page, where, mixed=bool(args.box), folder=args.folder if key else "")
    _tell_skipped(skipped)
    return EXIT_OK


def cmd_count(args, ecm: Ecm) -> int:
    """문서함 하나(또는 왼쪽 메뉴의 목록)의 건수를, all 이면 문서함마다의 건수와 합을 말한다."""
    places, skipped = _places(ecm, args.cabinet) if not args.box else ([("", BOXES[args.box][1])], [])
    if args.cabinet != CABINET_ALL:
        count_words(ecm.count(cabinet=places[0][0], **_list_kwargs(args)))
        return EXIT_OK
    counts = []
    for key, where in places:   # 한 곳씩 세는 대로 말한다 — 뒤의 문서함에서 멈춰도 앞서 센 줄은 남는다
        counts.append(ecm.count(cabinet=key, **_list_kwargs(args)))
        count_line_words(where, counts[-1])
    count_total_words(sum(counts))
    _tell_skipped(skipped)
    return EXIT_OK


def json_lines_words(docs: list[Doc], cabinet: str | None) -> None:
    """목록 줄마다 JSON 한 줄(``doc_json``)."""
    for d in docs:
        print(doc_json(d, cabinet))


def count_words(n: int) -> None:
    """문서함 하나의 건수 — 수만."""
    print(n)


def count_line_words(where: str, n: int) -> None:
    """문서함 하나의 건수 한 줄."""
    print(f"{where}: {n}")


def count_total_words(total: int) -> None:
    """건수의 합 한 줄."""
    print(f"합 {total}")


def doc_json(doc: Doc, cabinet: str | None) -> str:
    """목록 줄 하나의 JSON — ``cabinet`` 을 주면(여러 문서함을 한 판에 낸 줄) 어느 문서함인가를 덧붙인다(내 문서함은 빈 글자)."""
    row = dataclasses.asdict(doc)
    if cabinet is not None:
        row["cabinet"] = cabinet
    return json.dumps(row, ensure_ascii=False)


def _search_query(args) -> SearchQuery:
    """명령줄 → 전사 검색의 칸 — 자리 낱말과 ``--title`` 을 제목 낱말 하나로 잇는다."""
    # 자리 낱말은 사람이 말한 문서 이름이다 — 셸이 빈칸에서 갈라 여러 인자로 와도, --title 의 값 곁에 남아도 제목 낱말 하나로 잇는다
    title = " ".join(w for w in (args.title, *args.words) if w.strip())
    return (SearchQuery(title, args.any_word, args.text, args.owner, args.creator, args.since, args.until,
                                    args.date_by, args.file_ext, tuple(args.security_in or ()), args.scope))


def search_widen(query: SearchQuery) -> str:
    """0 건일 때 넓힐 다음 걸음 — 이 칸 · 이 범위로 못 찾았다는 뜻이지 그런 문서가 없다는 뜻이 아니다. 아직 안 쓴 넓히기만 든다."""
    steps = []
    if len(query.title.split()) > 1 and not query.any_word:
        steps.append("제목 낱말 가운데 하나만 맞아도 — 같은 부름에 --any-word")
    if query.title and not query.text:
        steps.append(f"문서 안의 글로 — 제목 낱말 대신 --text \"{query.title}\"")
    if query.scope == SEARCH_MINE:
        steps.append(f"볼 수 있는 전사 문서로 — 같은 부름에 --scope {SEARCH_COMPANY}")
    head = "이 칸 · 이 범위로 못 찾았다는 뜻이지 그런 문서가 없다는 뜻이 아니다 — 사람에게도 그렇게 말한다"
    return head + (". 넓히는 길: " + " · ".join(steps) if steps else "")


def cmd_search(args, ecm: Ecm) -> int:
    """전사 검색을 돌려 그 쪽의 줄과 0 건의 넓힐 길을 말한다."""
    query = _search_query(args)
    total, hits = ecm.search_all(query, page=args.page, per_page=args.per_page)
    search_words(query, total, hits, args.page, args.per_page)
    return EXIT_OK


def search_words(query: SearchQuery, total: int, hits: list[Hit], page: int, per_page: int) -> None:
    """전사 검색 한 쪽의 말 — 범위와 건수, 0 건이면 넓힐 길, 줄마다 이름 · 올린 이 · 부서 · 보안 · 고침 · 열쇠."""
    where = "볼 수 있는 전사 문서" if query.scope == SEARCH_COMPANY else "내 문서함들(제 부서 · 프로젝트)"
    print(f"{where}에서 {total} 건 — 쪽 {page} · {len(hits)} 줄 (내가 볼 수 있는 문서만 온다)")
    if not total:
        print(search_widen(query))
    for i, h in enumerate(hits, (page - 1) * per_page + 1):
        bits = [h.title + (f".{h.ext}" if h.ext else ""), f"올린 이 {h.author}" if h.author else "",
                f"부서 {h.dept}" if h.dept else "", f"보안 {level_name(h.security)}" if h.security else "",
                f"고침 {h.modified}" if h.modified else "", f"id {h.object_id}"]
        print(f"{i:>3}. " + " · ".join(b for b in bits if b))


def cmd_find_folder(args, ecm: Ecm) -> int:
    """모든 문서함에서 이름에 그 글이 든 폴더를 찾아 문서함 이름과 함께 말한다."""
    found = ecm.folders_named(args.name)
    if not found:
        raise ArgsError(no_named_folder_word(args.name))
    named_folder_words(args.name, found, {c.key: c.name for c in ecm.cabinets()})
    return EXIT_OK


def no_named_folder_word(name: str) -> str:
    """이름에 그 글이 든 폴더가 하나도 없을 때의 말."""
    return f"「{name}」 가 이름에 든 폴더가 내가 볼 수 있는 문서함에 없다"


def named_folder_words(name: str, found: list, names: dict[str, str]) -> None:
    """이름으로 찾은 폴더의 말 — 서버가 준 경로 · 폴더 열쇠 · 문서함 이름(``names``: 열쇠 → 이름)."""
    print(f"「{name}」 가 이름에 든 폴더 {len(found)} 개 — 고르지 않았다. 사람이 고른 폴더의 열쇠를 --folder 로 준다:")
    for cab, key, _, path in found:
        print(f"{path} · 폴더 {key} · 문서함 {names.get(cab, cab)} ({cab})")


def cmd_versions(args, ecm: Ecm) -> int:
    """판 이력 한 쪽을 말하고(준 열쇠가 지난 판이면 지금 판의 열쇠도), ``--more`` 면 보안등급 변경 이력 · 활용 건수까지 말한다."""
    now = ecm.current_key(args.object_id)
    older = older_key(args.object_id, now)
    key = ecm.doc_key(args.object_id)   # 한 번 받아 세 읽기에 같이 준다
    total, rows = ecm.history(args.object_id, page=args.page, per_page=args.per_page, doc_key=key)
    history_words(total, args.page, now if older else "", rows)
    if args.more:   # 판 이력을 말한 뒤 묻는다 — 뒤의 읽기에서 멈춰도 판 이력은 남는다
        security_log_words(ecm.security_log(args.object_id, key))
        use_count_words(ecm.use_counts(args.object_id, key))
    versions_tail_words()
    return EXIT_OK


def history_words(total: int, page: int, now: str, rows: list[Version]) -> None:
    """판 이력 한 쪽의 말 — 머리(판 수 · 쪽 · 준 열쇠가 지난 판이면 지금 판의 열쇠 ``now``)와 판마다 한 줄."""
    head = f"판 {total} 개 — 쪽 {page}"
    if now:
        head += f" · 준 열쇠는 지난 판이다 — 지금 판의 열쇠는 {now}"
    print(head)
    for v in rows:
        bits = [f"판 {v.label}" + (" (지금)" if v.current else ""), f"{v.creator} · {v.dept}" if v.creator else "", v.created,
                f"크기 {v.size}" if v.size else "", f"수정 내용 「{v.desc}」" if v.desc else "", f"id {v.object_id}"]
        print("  " + " · ".join(b for b in bits if b))


def security_log_words(log_rows: list) -> None:
    """보안등급 변경 이력의 말 — 몇 번과 줄마다 때 · 바꾼 이 · 앞 → 뒤."""
    print(f"보안등급 변경 {len(log_rows)} 번" + ("" if log_rows else " — 바뀐 적 없다"))
    for when, who, was, became in log_rows:
        print(f"  {when} · {who} · {was} → {became}")


def versions_tail_words() -> None:
    """판 이력의 끝 줄 — 지난 판을 여는 길."""
    print("지난 판은 그 줄의 id 로 read · open 한다 — 고치기(edit)는 지금 판만 받는다")


def use_count_words(counts: dict) -> None:
    """활용 건수 한 줄."""
    print("활용 건수 — " + " · ".join(f"{k} {v}" for k, v in counts.items()))


def cmd_latest(args, ecm: Ecm) -> int:
    """옛 열쇠의 지금 판 열쇠(지난 판이면 그 판까지)를 읽어 말한다."""
    now = ecm.current_key(args.object_id)
    older = older_key(args.object_id, now)
    latest_words(now, (ecm.version(now) or "?") if older else "")
    return EXIT_OK


def latest_words(now: str, version: str) -> None:
    """지금 판의 열쇠의 말 — ``version`` 이 있으면 준 열쇠가 지난 판이었다."""
    if not version:
        print(f"이 열쇠가 지금 판이다 — id {now}")
    else:
        print(f"준 열쇠는 지난 판이다 — 지금 판의 열쇠는 {now} (판 {version})")

LINK_PAGE = "/swp_interface.jsp"   # 화면의 「URL 복사」 가 내는 보기 링크의 자리 — 잰 꼴(SOURCES 「URL 복사」)
LINK_SYSTEM = "ECM"
LINK_RIGHTS = ("링크는 그 문서를 볼 권한이 있는 사람에게만 열린다(화면의 말 「타시스템 첨부 시 역할자에 추가하시기 바랍니다」) — 받을 분이 "
               "권한 명단에 없으면 preview-access 로 읽기를 먼저 준다")


def doc_link(ecm: Ecm, object_id: str, doc_key: str) -> str:
    """문서의 보기 링크 — 화면의 「URL 복사」 가 내는 꼴(문서 열쇠 · doc 열쇠 · 시스템 이름을 글자째 16진으로)을 열쇠만으로 짓는다.
    서버에 묻지 않는다 — 그 화면 동작은 부를 때마다 서버에 임시 파일을 짓는다."""
    query = "&".join(f"{k}={v.encode('ascii').hex()}" for k, v in (("OBJECTID", object_id), ("DOCID", doc_key), ("SYSID", LINK_SYSTEM)))
    return f"{ecm.server}{ecm.context}{LINK_PAGE}?ACTID=viewlink&{query}"


def older_key(given: str, now: str) -> bool:
    """준 열쇠가 지금 판의 열쇠(``current_key`` 의 답)와 다른가 — 다르면 준 열쇠는 지난 판이다. 대소문자 · 앞뒤 빈칸은 안 가린다."""
    return now.lower() != given.strip().lower()


def superseded(ecm: Ecm, object_id: str) -> tuple[str, str]:
    """준 열쇠가 지난 판이면 지금 판의 열쇠 — (지금 판의 열쇠 · 지금 판이면 빈 글자, 못 가렸으면 그 까닭). ``current_key`` 의 보기
    첫 걸음이라 받는 요청보다 먼저(등급 문 앞) 부르지 않는다. 읽기 · 올리기가 끝난 뒤에 붙는 물음이라 세션이 끊겨도 올리지 않고 까닭으로
    낸다 — 올리면 이미 받은 글자 · 이미 올린 판이 「실패」로 읽힌다."""
    try:
        now = ecm.current_key(object_id)
    except EcmError as exc:
        return "", f"지금 판인지 못 가렸다({exc}) — latest {object_id} 로 다시 본다"
    return (now if older_key(object_id, now) else ""), ""


def superseded_version(ecm: Ecm, object_id: str) -> tuple[str, str, str]:
    """준 열쇠가 지난 판이면 (지금 판의 열쇠, 그 판 · 못 읽으면 ?, 빈 글자), 못 가렸으면 (빈 글자, 빈 글자, 까닭), 지금 판이면 빈 글자 셋."""
    now, why = superseded(ecm, object_id)
    return now, ((ecm.version(now) or "?") if now else ""), why


def tell_superseded(object_id: str, now: str, version: str, why: str) -> None:
    """읽기의 머리 한 줄 — 준 열쇠가 지난 판이면 그렇다고 지금 판의 열쇠와 함께 말한다(읽기는 준 열쇠의 판 그대로다). 지금 판이면 말이 없다."""
    if now:
        print(f"⚠ 준 열쇠 {object_id} 는 지난 판이다 — 아래는 그 지난 판의 글자다. 지금 판의 열쇠는 {now}(판 {version}) — "
              f"사람에게 어느 판을 읽었는지 말하고, 지금 판이 필요하면 read {now}")
    elif why:
        print(f"⚠ {why}")


def cmd_link(args, ecm: Ecm) -> int:
    """지금 판의 열쇠로 보기 링크를 짓고 말한다(준 열쇠가 지난 판이면 그렇다고)."""
    now = ecm.current_key(args.object_id)
    if older_key(args.object_id, now):   # 머리를 말한 뒤 doc 열쇠를 묻는다 — 뒤에서 멈춰도 지난 판이라는 말은 남는다
        older_link_words(now)
    link_words(doc_link(ecm, now, ecm.doc_key(now)))
    return EXIT_OK


def older_link_words(now: str) -> None:
    """준 열쇠가 지난 판이라 지금 판의 링크를 짓는다는 머리."""
    print(f"준 열쇠는 지난 판이다 — 지금 판({now})의 링크를 짓는다")


def link_words(link: str) -> None:
    """보기 링크와 열리는 사람의 말."""
    print(f"링크: {link}")
    print(LINK_RIGHTS)


LOCK_UNREAD, LOCK_FREE, LOCK_MINE, LOCK_OTHER = "unread", "free", "mine", "other"   # 잠금의 상태 — lock_state 가 낸다


def lock_state(ecm: Ecm, object_id: str, state: DocState) -> str:
    """속성 화면의 잠금을 상태 하나로 — 못 읽음 · 안 잠김 · 나 · 남. 잠겼을 때만 잠근 이가 나인가를 묻는다."""
    if state.locked is None:
        return LOCK_UNREAD
    if not state.locked:
        return LOCK_FREE
    return LOCK_MINE if ecm.checked_out_by_me(object_id) else LOCK_OTHER


def can_head_words(state: DocState, object_id: str, lock: str) -> None:
    """할 수 있는 것의 머리 한 줄 — 이름 · 판 · 잠금 상태."""
    word = {LOCK_UNREAD: "못 읽었다", LOCK_FREE: "안 잠겼다", LOCK_MINE: "내가 편집 중이다"}.get(
        lock, f"다른 사람({state.lock_owner or '누군가'})이 편집 중이다")
    print(f"{state.title or object_id} · 판 {state.version or '?'} · 잠금: {word}")


def menu_words(menu: list[tuple[str, bool]]) -> None:
    """우클릭 메뉴의 켜진 것 · 꺼진 것."""
    print("지금 할 수 있는 것: " + (" · ".join(n for n, on in menu if on) or "(없음)"))
    print("꺼진 것: " + (" · ".join(n for n, on in menu if not on) or "(없음)"))


def cmd_can(args, ecm: Ecm) -> int:
    """문서의 잠금 상태와 지금 할 수 있는 것을 읽어 말한다."""
    state = ecm.doc_state(args.object_id)
    can_head_words(state, args.object_id, lock_state(ecm, args.object_id, state))
    menu_words(ecm.menu(args.object_id))
    return EXIT_OK


def cmd_notices(args, ecm: Ecm) -> int:
    """ECM 알림 숫자를 읽어 말한다."""
    notice_words(ecm.notices())
    return EXIT_OK


def notice_words(notices: list[tuple[str, int]]) -> None:
    """알림 숫자마다 한 줄과 목록을 보는 길."""
    for word, n in notices:
        print(f"{word} {n}")
    print("목록은 list --box asked-me(받은 권한 요청) · i-asked(보낸 권한 요청) — 승인 · 반려는 사람이 화면에서 한다")


def cmd_cancel_edit(args, ecm: Ecm) -> int:
    """편집취소하고 그 끝을 말한다."""
    cancelled_words(cancel_edit(ecm, Agent.from_env(), args.object_id, discard=args.discard))
    return EXIT_OK


def cancelled_words(done: Cancelled) -> None:
    """편집취소의 말 — 창을 닫았나, 편집완료 창이 남았으면 사람에게 이를 말."""
    shut = {"closed": "편집 창을 닫았다 · ", "not-found": ""}.get(done.closed, "")
    print(f"편집취소했다 — {shut}잠금이 풀렸다(다시 읽었다). 편집 중 고친 것은 올라가지 않았다 — 판은 그대로다")
    if done.window_left:
        print("⚠ 에이전트의 「편집완료」 창이 화면에 남았다 — 사람에게 그 창을 X 로 닫으라고 이른다. 「저장」을 누르면 버린 고침이 새 판으로 "
              "올라간다(손은 그 창을 누르지 않는다)")


def _props_args(args) -> dict:
    """명령줄 → plan_props 의 칸. --tag 는 뒤의 태그 전체(여러 번), --clear-tags 는 다 빼고 시작, --add-tag · --drop-tag 는 지금에서."""
    return dict(title=args.rename, tags=args.tag or None, add_tags=args.add_tag, drop_tags=args.drop_tag, clear_tags=args.clear_tags,
                due=args.due or None)


def _pre_props(args) -> None:
    """속성 바꾸기의 값을 서버 없이 가린다 — 함께 못 주는 깃발 · 바꿀 것 없음 · 이름 · 태그 · 완료일의 꼴, 못 쓸 값이면 ``ArgsError``."""
    if args.tag and args.clear_tags:
        raise ArgsError("--tag(태그 전체) 와 --clear-tags 는 함께 안 준다 — --tag 가 이미 지금 태그를 갈아 끼운다")
    if args.rename is None and not (args.tag or args.add_tag or args.drop_tag or args.clear_tags or args.due):
        raise ArgsError("바꿀 속성(--rename · --tag · --add-tag · --drop-tag · --clear-tags · --due)을 하나는 준다")
    if args.rename is not None:
        check_title(args.rename)
    for tags in (args.tag, args.add_tag, args.drop_tag):   # 말마다 따로 — 「--add-tag A --drop-tag A」 는 겹친 말이 아니다
        check_tags(tags)
    if args.due:
        check_due(args.due)


def _print_props(plan: PropsPlan) -> None:
    """속성 미리 보기의 말 — 지금과 뒤의 이름 · 태그 · 완료일 · 확인 열쇠와 다음 걸음."""
    show = lambda p: (f"이름 「{p.title}.{plan.ext}」 · 태그 {', '.join('#' + t for t in p.tags) or '(없음)'} · 완료일 "
                      f"{'(없음)' if p.due == SCREEN_NO_DUE else p.due}")
    print(f"속성 미리 보기 — id {plan.object_id}")
    print(f"지금: {show(plan.before)}")
    print(f"뒤:   {show(plan.after)}")
    print(f"확인 열쇠 {plan.token}")
    print("다음: 사람이 이대로 바꾸자고 하면 같은 인자에 apply-props · --confirm <열쇠>. 권한 · 보안등급 · 폴더는 그대로 다시 싣는다")


def cmd_preview_props(args, ecm: Ecm) -> int:
    """속성 바꾸기를 미리 보고 확인 열쇠를 말한다 — 서버를 안 바꾼다."""
    _print_props(plan_props(ecm, args.object_id, **_props_args(args)))
    return EXIT_OK


def cmd_apply_props(args, ecm: Ecm) -> int:
    """미리 본 그대로 속성을 바꾸고 다시 읽은 속성을 말한다."""
    plan = plan_props(ecm, args.object_id, **_props_args(args))
    props_done_words(apply_props(ecm, plan, args.confirm), plan.ext)
    return EXIT_OK


def props_done_words(got: PropChange, ext: str) -> None:
    """속성을 바꾼 뒤의 말 — 다시 읽은 이름 · 태그 · 완료일."""
    print(f"바꿨다 — 다시 읽은 속성: 이름 「{got.title}.{ext}」 · 태그 {', '.join('#' + t for t in got.tags or ()) or '(없음)'} · "
          f"완료일 {'(없음)' if got.due == SCREEN_NO_DUE else got.due}. 권한 · 보안등급 · 폴더는 그대로다")


def cmd_doc(args, ecm: Ecm) -> int:
    """속성 화면을 한 번 읽어 판 · 잠금 · 보안등급 · 이름을 말한다."""
    doc_words(ecm.doc_state(args.object_id))
    return EXIT_OK


def doc_words(state: DocState) -> None:
    """속성 화면 한 번 읽기의 말 — 이름 · 판 · 잠금 · 보안(물어야 하면 그 길)."""
    if state.title:
        print(f"이름: {state.title}")
    print(f"판: {state.version or '못 읽었다'}")
    print("잠금: " + ("못 읽었다" if state.locked is None else
                    f"편집으로 잠겨 있다({state.lock_owner or '누군가'})" if state.locked else "안 잠겼다"))
    if state.security is None:
        print("보안: 못 읽었다 — read · edit 는 사람에게 AI 로 보내도 되는지 물은 뒤 --ai-ok 로만 받는다")
    else:
        s = state.security
        print(f"보안: {s.name} ({s.level}/{s.open_flag})" + (" · 핵심기술" if s.core else "")
              + (f" — read · edit 는 사람에게 AI 로 보내도 되는지 물은 뒤 {AI_OK_FLAG} 로만 받는다" if s.ask_before_ai else ""))


def cmd_access(args, ecm: Ecm) -> int:
    """문서의 권한 명단을 읽어 말한다."""
    _print_grants(ecm.roles(args.object_id))
    return EXIT_OK


def cmd_who(args, ecm: Ecm) -> int:
    """찾는 말의 갈래대로 부서(아래 부서 · 부서원) · 부서 이름 · 사람을 찾아 말한다."""
    company = ecm.company()
    kind, value = spec_kind(args.query)
    if kind == SPEC_CODE:   # 아래 부서를 말한 뒤 부서원을 묻는다 — 차례는 화면과 같다
        sub_organ_words(ecm.sub_organs(value, company))
        member_words(ecm.members(value, company))
    elif kind == SPEC_ORGAN:
        organ_words(ecm.organs(value, company))
    else:
        people_words(ecm.people(args.query, company))
    return EXIT_OK


def sub_organ_words(organs: list[Organ]) -> None:
    """바로 아래 부서마다 한 줄."""
    for s in organs:
        print(f"  아래 부서 {s.name} · 바로 {s.members} 명 · 아래 부서 {s.subs} · 코드 {s.code}")


def member_words(people: list[Person]) -> None:
    """부서에 바로 든 사람마다 한 줄."""
    for m in people:
        print(f"  {m.label()}")


def organ_words(organs: list[Organ]) -> None:
    """이름으로 찾은 부서마다 한 줄 — 위 부서 > 이름 · 사람 수 · 아래 부서 수 · 코드."""
    for o in organs:
        print(f"{o.upper} > {o.name} · 바로 {o.members} 명 · 아래 부서 {o.subs} · 코드 {o.code}")


def people_words(people: list[Person]) -> None:
    """이름으로 찾은 사람마다 한 줄 — 이름/메일 · 부서 · 사번."""
    for m in people:
        print(f"{m.label()} · 사번 {m.employee}")


def cmd_open(args, ecm: Ecm) -> int:
    """문서를 받아 화면에 띄우고 받은 파일 줄을 말한다(등급 문을 안 지난 사람의 창이다)."""
    opened_words(open_document(ecm, Agent.from_env(), args.object_id, allow_picker=args.allow_picker), args.object_id)
    return EXIT_OK


def opened_words(opened: Opened, object_id: str) -> None:
    """화면에 띄운 문서의 말 — 받은 파일 줄(등급 문을 안 지났다)과 기본 앱."""
    print("\n".join(_describe_open(opened, gated=False, object_id=object_id)))


def cmd_read(args, ecm: Ecm) -> int:
    """문서의 글자를 말한다 — ``--fresh`` 가 아니고 남긴 글자가 있으면 그것을, 아니면 새로 받아 뽑은 것을 내고, 준 열쇠가 지난 판이면 그렇다고 이른다."""
    if not args.fresh:
        kept = read_kept(ecm, args.object_id, ai_ok=args.ai_ok)
        if kept is not None:
            tell_superseded(args.object_id, *superseded_version(ecm, args.object_id))   # 등급 문을 지난 뒤 — 지난 판의 남긴 글자를 지금 판으로 읽지 않게
            tell_kept(kept, as_file=args.as_file)
            return EXIT_OK
    got = read_document(ecm, Agent.from_env(), args.object_id, allow_picker=args.allow_picker, ai_ok=args.ai_ok)
    tell_superseded(args.object_id, *superseded_version(ecm, args.object_id))
    tell_read(got, args.object_id, as_file=args.as_file)
    return EXIT_OK


def _change_and_maybe_plan(ecm: Ecm, args, path: pathlib.Path, changes: Changes, *, opened_now: bool) -> int:
    """열린 그 문서를 고치고(바꿀 것이 있으면), ``--desc`` 가 있으면 올리기 미리 보기와 열쇠까지 낸다."""
    if not changes.empty():
        try:
            _print_changed(change_document(path, OFFICE_BY_EXT[path.suffix.lower()], changes))
        except EcmError as exc:
            if opened_now:
                raise EcmError(change_failed_word(exc, args.object_id)) from exc
            raise
    if args.desc:
        _print_checkin_plan(prepare_checkin(ecm, path, args.object_id, args.desc, ai_ok=args.ai_ok))
    else:
        next_change_words(args.object_id)
    return EXIT_OK


def change_failed_word(exc: Exception, object_id: str) -> str:
    """방금 편집으로 연 문서를 못 고쳤을 때의 말 — 잠겼으니 다시 고치거나 편집취소하는 길."""
    return (f"{exc} — 문서는 편집으로 열려 있고 서버에서 잠겼다. 조각을 고쳐 change {object_id} <받은 파일> 로 "
            f"다시 부르거나, 그만두면 {CANCEL_NEXT.format(object_id=object_id)}")


def next_change_words(object_id: str) -> None:
    """고친 뒤 올리기를 아직 안 볼 때의 다음 걸음."""
    print(f"다음: 더 고치려면 change {object_id} <받은 파일> … (사람이 창에서 고쳐도 된다), 다 고쳤으면 preview-checkin "
          f"{object_id} <받은 파일> --desc <수정 내용> 으로 올리기를 미리 본다(그 자리에서 change 에 --desc 를 줘도 된다)")


def cmd_edit(args, ecm: Ecm) -> int:
    """문서를 잠가 편집으로 열고, 바꿀 것이 있으면 고친 뒤 ``--desc`` 가 있으면 올리기 미리 보기까지 낸다."""
    changes = changes_of(args)
    opened = edit_document(ecm, Agent.from_env(), args.object_id, ai_ok=args.ai_ok, changes=changes)
    edit_opened_words(opened)
    return _change_and_maybe_plan(ecm, args, opened.path, changes, opened_now=True)


def edit_opened_words(opened: Opened) -> None:
    """편집으로 연 문서의 말 — 받은 파일 줄(등급 문을 지났다) · 기본 앱 · 잠갔다."""
    print("\n".join([*_describe_open(opened, gated=True), "편집으로 열었다 — 서버가 잠갔다"]))


def cmd_change(args, ecm: Ecm) -> int:
    """이미 편집으로 받은 파일을 등급 문에 대어 본 뒤 고치고, ``--desc`` 가 있으면 올리기 미리 보기까지 낸다."""
    changes, path = _pre_change(args)
    check_readable(ecm, args.object_id, ai_ok=args.ai_ok, stopped=GATE_EDIT)   # 사람이 화면에서 편집으로 연 파일은 edit 의 문을 안 지났다
    return _change_and_maybe_plan(ecm, args, path, changes, opened_now=False)


def cmd_preview_checkin(args, ecm: Ecm) -> int:
    """올리기 미리 보기와 확인 열쇠를 말한다 — 창에 저장 안 된 고침이 있으면 저장하고, 서버는 안 바꾼다."""
    _print_checkin_plan(prepare_checkin(ecm, pathlib.Path(args.path), args.object_id, args.desc, ai_ok=args.ai_ok))
    return EXIT_OK


def cmd_checkin(args, ecm: Ecm) -> int:
    """미리 본 그대로 올리고 그 끝을 말한다."""
    checked_in_words(checkin_document(ecm, pathlib.Path(args.path), args.object_id, args.desc, confirm=args.confirm), args.object_id)
    return EXIT_OK


def checked_in_words(done: CheckedIn, object_id: str) -> None:
    """올리기의 끝의 말 — 고친 것 없이 풀렸으면 그렇다고, 올랐으면 앞 판 → 뒤 판과 새 판의 열쇠(못 받았으면 그 까닭)."""
    if done.unchanged:
        print(f"고친 것이 없어 올리지 않았다 — 에이전트가 편집완료 창 없이 잠금을 풀었고 판은 {done.version_before} 그대로다")
        return
    print(f"올렸다 — 판 {done.version_before} → {done.version_after} · 고른 판 {done.picked or '?'}. 판이 오르면 문서 열쇠가 바뀐다")
    if done.new_key:
        print(f"새 판의 열쇠: {done.new_key} — 다시 읽기 · 고치기 · 권한 · 링크는 이 열쇠로 부른다(옛 열쇠 {object_id} 는 지난 판을 가리킨다)")
    else:
        print(f"새 판의 열쇠를 못 받았다 — {done.key_why or '지금 판을 묻는 답이 옛 열쇠를 냈다'}. latest {object_id} 로 받는다")


def _register_args(args, ecm: Ecm) -> dict:
    """명령줄 → 등록 손의 칸 — 문서함 이름 · 열쇠는 여기서 한 번 열쇠로 푼다(``Ecm.cabinet_of``). 등록 손은 열쇠만 받는다."""
    return dict(cabinet=ecm.cabinet_of(args.cabinet).key, folder=args.folder, folder_path=args.folder_path, security=args.security, open_flag=args.open_flag,
                title=args.title)


def cmd_preview_register(args, ecm: Ecm) -> int:
    """새 문서 등록을 미리 보고 확인 열쇠를 말한다 — 서버에도 에이전트에도 안 보낸다."""
    _print_register_plan(plan_register(ecm, pathlib.Path(args.path), **_register_args(args, ecm)))
    return EXIT_OK


def cmd_register(args, ecm: Ecm) -> int:
    """미리 본 그대로 새 문서로 올리고 새 문서의 열쇠 · 링크를 말한다."""
    done = register_document(ecm, Agent.from_env(), pathlib.Path(args.path), **_register_args(args, ecm), confirm=args.confirm)
    # 첫 판의 doc 열쇠는 「doc」 + 문서 열쇠다(SOURCES 「문서 열쇠와 doc 열쇠」) — 묻지 않고 링크를 짓는다
    registered_words(done, SECURITY_PAIRS[(args.security, args.open_flag)], doc_link(ecm, done.object_id, "doc" + done.object_id))
    return EXIT_OK


def registered_words(done: Registered, security: str, link: str) -> None:
    """새 문서를 올린 뒤의 말 — 이름 · 판 · 보안 · 열쇠와 링크."""
    print(f"올렸다 — {done.title} · 판 {done.version} · 보안 {security} · id {done.object_id}")
    print(f"새 문서의 열쇠: {done.object_id} — 읽기 · 고치기 · 권한은 이 열쇠로 부른다")
    print(f"링크: {link} — {LINK_RIGHTS}")


PEOPLE_COMMENT = "#"      # 사람 파일에서 이 글자 뒤는 버린다 — company-directory 의 find --out 이 쓰는 꼴과 같다


@dataclass(frozen=True)
class AccessSpecs:
    """명령줄 · 사람 파일에서 모은 권한 말 — ``grant`` 는 (edit|copy|read, 사람 말), ``origins`` 는 파일에서 온 말 → 「파일:줄」,
    ``files`` 는 사람에게 보일 파일마다의 한 줄."""
    grant: tuple[tuple[str, str], ...]
    origins: dict
    files: tuple[str, ...]


def read_people_file(path: str) -> list[tuple[str, str]]:
    """사람 파일 하나 → [(「파일:줄」, 사람 말)] — 한 줄에 사람 말 하나(「이름」 · 「이름/메일ID」 · 「이름/메일 주소」 · 「org:…」),
    ``PEOPLE_COMMENT`` 뒤와 빈 줄은 버린다. 못 읽거나 사람 말이 한 줄도 없으면 ``ArgsError``."""
    file = pathlib.Path(path)
    try:
        lines = file.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise ArgsError(f"사람 파일을 못 읽었다: {file} ({exc}) — UTF-8 글 파일을 준다") from exc
    got = [(f"{file.name}:{n}", line.split(PEOPLE_COMMENT, 1)[0].strip()) for n, line in enumerate(lines, 1)]
    got = [(where, spec) for where, spec in got if spec]
    if not got:
        raise ArgsError(f"사람 파일에 사람이 한 줄도 없다: {file}")
    return got


def people_specs(paths) -> list[tuple[str, str]]:
    """주소록의 사람 파일(people.json — ``ep_command.people_of``) → [(「파일:몇째」, 사람 말)]. ECM 은 이름으로만 사람을 찾으니 말은
    「이름/메일ID」(없으면 「이름/메일 주소」 · 「이름」)다 — 동명이인은 메일 쪽으로 가른다. 꼴이 아니면 ``ArgsError``."""
    try:
        people = ep_command.distinct(ep_command.people_of(paths))
    except ep_command.Stop as exc:
        raise ArgsError(str(exc)) from exc
    return [(p.where, f"{p.name}/{p.mail_id or p.email}" if p.mail_id or p.email else p.name) for p in people]


def access_specs(args) -> AccessSpecs:
    """명령줄의 권한 말과 사람 파일을 모아(``gather_access_specs``) 서버 없이 가린다(``check_access_specs``). 세션보다 먼저 돌고
    (``precheck``), 미리 보기 · 보내기가 같은 것을 다시 모은다 — 손가락 표의 몸은 세션 전 가리기 없이도 홀로 선다."""
    specs = gather_access_specs(args)
    check_access_specs(specs, args.revoke)
    return specs


def gather_access_specs(args) -> AccessSpecs:
    """명령줄의 권한 말과 사람 파일(``--<칸>-file`` · 주소록의 사람 파일)을 말 목록 · 「파일:줄」 · 파일마다의 한 줄로 모은다 — 사람
    파일을 못 읽거나 칸 짝이 틀리거나 아무 말도 없으면 ``ArgsError``."""
    grant: list[tuple[str, str]] = []
    origins: dict[str, str] = {}
    files: list[str] = []
    for word, role in ACCESS_OF_WORD.items():
        grant += [(word, spec) for spec in getattr(args, word)]
        for path in getattr(args, f"{word}_file"):
            got = read_people_file(path)
            files.append(f"{ACCESS_ROLES[role]} 로 줄 파일 {pathlib.Path(path).name} — 사람 말 {len(got)} 줄")
            for where, spec in got:
                grant.append((word, spec))
                origins.setdefault(spec, where)
    if args.people_file and not args.people_as:
        raise ArgsError(f"{ep_command.PEOPLE_FLAG} 는 줄 칸과 함께 준다 — --people-as edit · copy · read 가운데 하나")
    if args.people_as and not args.people_file:
        raise ArgsError(f"--people-as 는 {ep_command.PEOPLE_FLAG} 와 함께 준다")
    for where, spec in people_specs(args.people_file):
        grant.append((args.people_as, spec))
        origins.setdefault(spec, where)
    if args.people_file:
        files.append(f"{ACCESS_ROLES[ACCESS_OF_WORD[args.people_as]]} 로 줄 사람 파일 "
                     f"{' · '.join(pathlib.Path(p).name for p in args.people_file)}")
    if not (grant or args.revoke or args.clear):
        raise ArgsError(f"줄 사람(--edit · --copy · --read · 그 -file · {ep_command.PEOPLE_FLAG}) · 거둘 사람(--revoke) · --clear 가운데 하나는 준다")
    return AccessSpecs(tuple(grant), origins, tuple(files))


def check_access_specs(specs: AccessSpecs, revoke) -> None:
    """모은 권한 말과 거둘 말을 서버 없이 가린다 — 못 쓸 말(두 글자가 안 되는 이름 · 주소만 준 말)은 「파일:줄」 과 함께 다 대며
    ``ArgsError``."""
    problems = []
    for spec in [s for _, s in specs.grant] + list(revoke):
        try:
            check_person_spec(spec)
        except ArgsError as exc:
            problems.append(f"{specs.origins[spec]}: {exc}" if spec in specs.origins else str(exc))
    problems = list(dict.fromkeys(problems))
    if len(problems) == 1:
        raise ArgsError(problems[0])
    if problems:
        raise ArgsError(f"못 쓸 말이 {len(problems)} 개라 아무것도 묻지 않았다 — 다 고쳐 다시 부른다:\n" + "\n".join(f"- {p}" for p in problems))


def _access_plan(args, ecm: Ecm) -> "AccessPlan":
    """명령줄 · 사람 파일의 권한 말로 권한 한 판을 짓는다 — 사람 파일마다의 한 줄을 덧붙인 말 앞에 단다."""
    specs = access_specs(args)
    plan = plan_access(ecm, args.object_id, grant=list(specs.grant), revoke=args.revoke, clear=args.clear, with_subs=args.with_subs,
                       origins=specs.origins)
    return dataclasses.replace(plan, notes=specs.files + plan.notes) if specs.files else plan


def cmd_preview_access(args, ecm: Ecm) -> int:
    """권한 바꾸기를 미리 보고 확인 열쇠를 말한다 — 서버를 안 바꾼다."""
    _print_plan(_access_plan(args, ecm))
    return EXIT_OK


def cmd_apply_access(args, ecm: Ecm) -> int:
    """미리 본 그대로 권한을 바꾸고 다시 읽은 명단을 말한다."""
    plan = _access_plan(args, ecm)
    access_done_words(plan, apply_access(ecm, plan, args.confirm))
    return EXIT_OK


def access_done_words(plan: AccessPlan, got: list[Grant]) -> None:
    """권한을 바꾼 뒤의 말 — 더함 · 뺌 · 옮김 수와 다시 읽은 명단."""
    print(f"바꿨다 — {plan.title} · 더함 {len(plan.added)} · 뺌 {len(plan.removed)} · 옮김 {len(plan.moved)} · 다시 읽은 명단:")
    _print_grants(got)


def cmd_default_app(args, ecm: None) -> int:
    """확장자의 기본 앱 상태와 이 PC 의 해시 셈을 읽어 말한다 — 쓰지 않는다."""
    ext = default_app.normalize(args.ext)
    now, check = default_app.state(ext), default_app.preflight()
    default_app_words(ext, now, default_app.resolved_progid(ext), default_app.pick_progid(ext), check)
    return EXIT_OK


def default_app_words(ext: str, now, resolved: str, pick: str, check) -> None:
    """기본 앱 상태의 말 — 지금 고름 · Windows 가 푸는 앱 · 고를 앱 · 해시 셈이 맞은 수."""
    print(f"{ext} — 지금 {now.progid or '안 정해짐'}{f' ({now.where})' if now.where else ''} · Windows 가 푸는 앱 "
          f"{resolved or '없음'} · 고를 앱 {pick or '없음'}")
    print(f"이 PC 의 해시 계산 — Windows 가 적은 {check.total} 개 중 {check.matched} 개가 같다")


# ── 세션 전에 가리기 — 서버 없이 가릴 수 있는 값은 세션을 받기 전에 멈춘다 ──────────────
# 틀린 열쇠 하나로 사람이 로그인을 다시 하고 나서야 「열쇠가 틀렸다」를 듣지 않게 한다. 말은 손 안의 같은 함수가 내니 세션 뒤의 말과
# 같다 — 손을 바로 부르는 쪽(라이브러리)도 그 함수들을 그대로 지난다

def _check_query(value: str) -> None:
    """who 의 찾는 말 — 이름(일부)은 두 글자부터, org: 뒤는 부서 코드이거나 두 글자부터."""
    kind, rest = spec_kind(value)
    if kind == SPEC_ORGAN:
        organ_name(rest)
    elif kind == SPEC_PERSON:
        person_name(value)


def _no_all(args) -> None:
    """문서함 하나에서만 하는 명령에 all 을 주면 ``ArgsError``."""
    if args.cabinet.strip() == CABINET_ALL:
        raise ArgsError(f"{args.command} 는 문서함 하나에서만 한다 — {CABINET_ALL} 대신 이름이나 열쇠(cab…)로 준다")


def _pre_folders(args) -> None:
    """folders 의 값을 서버 없이 가린다 — all 이나 ``--find`` 와 ``--parent`` 를 함께 주면 ``ArgsError``."""
    _no_all(args)
    if args.find and args.parent:
        raise ArgsError("--find 와 --parent 는 함께 안 준다 — --find 는 문서함 나무 전체에서 찾는다")


def _pre_list(args) -> None:
    """list · count 의 값을 서버 없이 가린다 — 왼쪽 메뉴 목록과 자리 · all 과 폴더 · 문서함 안 폴더 열쇠의 꼴."""
    refuse_box_with_place(args.box, args.cabinet, args.folder)
    if args.cabinet.strip() == CABINET_ALL and args.folder:
        raise ArgsError(f"--folder 는 문서함 하나와만 받는다 — {CABINET_ALL} 대신 그 폴더가 든 문서함을 준다")
    if args.cabinet and args.folder:
        folder_key(args.folder)   # 문서함 안 폴더는 열쇠(fdr…)로만 — 내 문서함 목록 줄의 folder_id 꼴과 같다


def _pre_search(args) -> None:
    """search 의 칸과 쪽을 서버 없이 가린다."""
    check_search(_search_query(args))
    check_search_page(args.page, args.per_page)


def _pre_find_folder(args) -> None:
    """find-folder 의 이름을 서버 없이 가린다 — 두 글자부터."""
    folder_name(args.name)


def _pre_edit(args) -> None:
    """edit 의 바꿀 것을 서버 없이 가린다(``check_change_shape``)."""
    check_change_shape(changes_of(args))


def _pre_change(args) -> tuple[Changes, pathlib.Path]:
    """change 의 값 — (바꿀 것, 그 문서를 편집으로 받은 파일). cmd_change 도 이것으로 받는다."""
    changes = changes_of(args)
    if changes.empty() and not args.desc:
        raise ArgsError("바꿀 것(--replace · --replace-file · --insert-from)을 하나는 준다 — 올리기만 보려면 preview-checkin")
    check_change_shape(changes)
    return changes, checkout_file(args.path, _object_id(args.object_id))


def _pre_register(args) -> None:
    """등록 · 등록 미리 보기의 값을 서버 없이 가린다 — all · 파일 · 보안 짝 · 폴더 · 이름(``register_inputs``)."""
    _no_all(args)
    register_inputs(args.path, folder=args.folder, folder_path=args.folder_path, security=args.security, open_flag=args.open_flag,
                    title=args.title)


ARG_CHECKS = {        # ARGS 의 열쇠 → 그 칸 하나를 서버 없이 가리는 손(빈 값은 안 본다)
    "object_id": _object_id,
    "parent": folder_key,
    "reg_folder": folder_key,
    "query": _check_query,
}


def _dest(key: str) -> str:
    """ARGS 의 열쇠 → argparse 가 그 값을 두는 이름 — ``dest`` 를 안 줬으면 첫 깃발에서 짓는다."""
    flags, kw = ARGS[key]
    return kw.get("dest") or flags[0].lstrip("-").replace("-", "_")


def precheck(args) -> None:
    """서버 없이 가릴 수 있는 값을 세션보다 먼저 가린다 — 칸 하나는 ``ARG_CHECKS``, 칸 여럿은 그 손가락의 ``check``. 못 쓸 값이면
    ``ArgsError``(조각 파일이 없거나 UTF-8 이 아닐 때도 · 받은 파일이 오피스 꼴이 아니면 ``EcmError``). 아무것도 안 건드린다."""
    finger = FINGERS[args.command]
    for key in finger.args:
        value = getattr(args, _dest(key), None)
        if key in ARG_CHECKS and isinstance(value, str) and value.strip():
            ARG_CHECKS[key](value)
    if finger.check:
        finger.check(args)


# ── 손가락의 표 — 명령 하나가 한 줄이다 ───────────────────────────────────
# 손가락을 더하거나 빼는 일은 이 표의 줄(과 필요하면 ARGS · EDIT_CHANGES 의 줄)과 그 일을 하는 손 하나다. 명령줄의 인자 · 세션이
# 드나 · 바꾸는가(company_ecm.py 가 세션 손부터 받아 한 번만 돈다) · --help 의 지도가 다 이 표에서 선다

@dataclass(frozen=True)
class Pass:
    """화면 패스 하나 — 사람이 웹 앱에서 화면 하나를 열고 칸을 바꾸고 끝 단추를 누르는 단위."""
    start: str       # 출발 — 무엇에서 시작하나
    end: str         # 끝 — 무엇으로 끝나나
    guard: str = ""  # 손이 지키는 선 — 끝이 되돌리기 어려우면 열쇠


@dataclass(frozen=True)
class Finger:
    """손가락 하나 — 명령 하나다."""
    pass_name: str           # PASSES 의 열쇠
    word: str                # 무엇을 하나 — --help 의 한 줄
    args: tuple[str, ...]    # ARGS 의 열쇠들
    run: object              # (명령줄 인자, Ecm | None) → 종료 값
    session: bool = True     # 사내 세션이 드나
    mutating: bool = False   # 문서함을 바꾸나(잠금 · 판 · 새 문서 · 권한)
    agent: object = False    # 이 PC 의 문서함 에이전트를 부르나 — 참 · 거짓, 또는 (명령줄 인자) → 참 · 거짓. 그 에이전트는 이 로그온에 평소 EP
                             # 로그인이 있어야 문서를 연다(명령 틀이 먼저 묻는다 — uses_agent)
    check: object = None     # (명령줄 인자) → 없음 — 칸 여럿에 걸친 값을 서버 없이 가린다(precheck). 칸 하나는 ARG_CHECKS 가 든다


def uses_agent(finger: "Finger", args) -> bool:
    """이 명령 한 판이 문서함 에이전트를 부르나 — 손가락 표의 ``agent`` 가 값이면 그 값, 함수면 그 인자로 가린다(read 는 남긴 글자가 있으면
    에이전트를 안 부른다)."""
    return finger.agent(args) if callable(finger.agent) else bool(finger.agent)


@dataclass(frozen=True)
class Change:
    """편집 패스의 바꿀 것 하나."""
    flags: tuple[str, ...]   # ARGS 의 열쇠들
    apps: tuple[str, ...]    # 받는 앱 — check_changes 가 이 칸으로 가린다
    word: str
    unmeasured: tuple[str, ...] = ()   # 받되 어느 PC 에서도 안 잰 앱 — --help 가 「회사에서 안 쟀다」를 낸다


PASSES = {
    "찾기": Pass("내 문서함 · 부서 · 프로젝트 문서함 · 그 안 폴더 · 왼쪽 메뉴의 목록 · 전사 검색 · 폴더 나무", "읽기만"),
    "문서": Pass("문서 열쇠", "읽기만 — 속성 화면 · 판 이력 · 지금 할 수 있는 것 · 권한 명단 · 사람 찾기"),
    "보기": Pass("문서 열쇠", "에이전트가 받아 화면에 띄운다 — read 는 창을 닫고 글자를 남긴다",
                 "기밀 · 핵심기술 · 등급 모름은 받기 전에 멈춘다(사람에게 물은 뒤 --ai-ok)"),
    "편집": Pass("문서 열쇠(잠그고 연다) → 그 받은 파일", "checkin --confirm — 늘 다음 판으로 올린다 · 그만두면 cancel-edit",
                 "잠그기 전에 못 할 까닭을 가린다 · 기밀 · 핵심기술 · 등급 모름은 걸음마다 멈춘다(--ai-ok) · 올리기는 미리 보기의 "
                 "열쇠로만 · 창에 고침이 남으면 안 닫는다"),
    "등록": Pass("PC 의 파일", "register --confirm — 새 문서 0.0 판", "폴더가 그 문서함의 것 · 같은 이름이면 안 올린다 · 열쇠로만"),
    "권한": Pass("문서 열쇠", "apply-access --confirm — 속성 화면의 저장 하나",
                 "명단을 사람까지 풀어 보이고 열쇠로만 · 소유자 · 본인 줄은 안 바꾼다 · 안 잰 꼴의 문서는 멈춘다"),
    "속성": Pass("문서 열쇠", "apply-props --confirm — 속성 화면의 저장 하나(이름 · 태그 · 완료일)",
                 "미리 보기의 열쇠로만 · 권한 · 보안등급 · 폴더는 그대로 다시 싣고 다시 읽어 본다 · 안 잰 꼴의 문서는 멈춘다"),
    "손질": Pass("이 PC", "읽기만"),
}

ARGS = {
    "object_id": (("object_id",), dict(help="문서 열쇠(16 자리 hex) — list · 메일 · 게시판의 문서함 첨부가 낸다")),
    "search": (("--search",), dict(default="", help="찾을 낱말(화면의 찾기 칸)")),
    "period": (("--period",), dict(default=DEFAULT_PERIOD, choices=PERIODS,
                                   help=f"기간 — 화면의 기간 필터 값(1년은 12M · 전체는 ALL). 기본 {DEFAULT_PERIOD}")),
    "folder_mine": (("--folder",), dict(default="", help="폴더 — 내 문서함이면 목록 줄의 folder_id, --cabinet 과 함께면 그 문서함 안 "
                                                       "폴더 열쇠(fdr… — folders · find-folder 가 낸다 · 그 폴더에 바로 든 문서만)")),
    "box": (("--box",), dict(default="", choices=list(BOXES), help="왼쪽 메뉴의 다른 목록 — " +
                                                                  " · ".join(f"{k} {n}" for k, (_, n) in BOXES.items()))),
    "sort": (("--sort",), dict(default="", choices=list(SORTS),
                               help="정렬 — 목록 머리 글(등록일 정렬은 서버가 안 받는다). 안 주면 고친 날 새것부터")),
    "direction": (("--direction",), dict(default="desc", choices=["asc", "desc"], help="정렬 방향 — 기본 desc")),
    "type": (("--type",), dict(default="", choices=list(FILE_TYPES), help="꼴 모아보기 — 목록 위 아이콘과 같다")),
    "s_words": (("words",), dict(nargs="*", default=[], metavar="낱말",
                                 help="사람이 말한 문서 이름 그대로 — 따옴표 없이 여럿이어도 된다. 제목 낱말로 찾는다(--title 에 더한다)")),
    "s_title": (("--title",), dict(default="", help="제목 낱말(빈칸으로 여럿 — 기본은 다 맞아야)")),
    "any_word": (("--any-word",), dict(action="store_true", help="제목 낱말 가운데 하나만 맞아도")),
    "s_text": (("--text",), dict(default="", help="본문 낱말 — 문서 안의 글로 찾는다")),
    "s_owner": (("--owner",), dict(default="", help="소유자 이름")),
    "s_creator": (("--creator",), dict(default="", help="등록자 이름")),
    "since": (("--since",), dict(default="", help="기간 시작 YYYY-MM-DD(--until 과 함께)")),
    "until": (("--until",), dict(default="", help="기간 끝 YYYY-MM-DD")),
    "date_by": (("--date-by",), dict(default="modified", choices=list(SEARCH_DATE_FIELDS), help="기간의 기준 — 고친 날 · 등록일")),
    "s_ext": (("--ext",), dict(default="", dest="file_ext", help="꼴(확장자 하나 — xlsx 따위)")),
    "security_in": (("--security",), dict(action="append", choices=sorted({s for s, _ in SECURITY_PAIRS}), dest="security_in",
                                         help="보안등급(여러 번) — --scope mine 에서만 선다")),
    "scope": (("--scope",), dict(default=SEARCH_MINE, choices=[SEARCH_MINE, SEARCH_COMPANY],
                                 help="mine 내 문서함들(제 부서 · 프로젝트 · 기본) · company 볼 수 있는 전사 문서")),
    "s_per_page": (("--per-page",), dict(type=int, default=DEFAULT_PER_PAGE)),
    "name": (("name",), dict(help="폴더 이름(일부 · 두 글자부터)")),
    "h_per_page": (("--per-page",), dict(type=int, default=HISTORY_PER_PAGE)),
    "more": (("--more",), dict(action="store_true", help="보안등급 변경 이력과 활용 건수(열람 · 첨부 · 복사 · 추천)도")),
    "discard": (("--discard",), dict(action="store_true",
                                     help="편집 창에 저장 안 된 고침이 있어도 버리고 푼다 — 사람이 버려도 된다고 한 뒤에만")),
    "rename": (("--rename",), dict(default=None, help="새 이름(확장자 뺀)")),
    "tag": (("--tag",), dict(action="append", default=[], help="태그 전체를 이것들로(여러 번) — 한글 · 영문 · 숫자 · 10 개까지")),
    "add_tag": (("--add-tag",), dict(action="append", default=[], help="태그 하나 더하기(여러 번)")),
    "drop_tag": (("--drop-tag",), dict(action="append", default=[], help="태그 하나 빼기(여러 번)")),
    "clear_tags": (("--clear-tags",), dict(action="store_true", help="태그를 다 뺀다(--add-tag 와 함께면 그것만 남는다)")),
    "due": (("--due",), dict(default="", help="완료예정일 YYYY-MM-DD")),
    "confirm_props": (("--confirm",), dict(required=True, help="preview-props 가 낸 확인 열쇠")),
    "cabinet_opt": (("--cabinet",), dict(default="", help="부서 · 프로젝트 문서함 — 열쇠(cab…) · 이름(일부 · 여럿이 걸리면 후보를 내고 "
                                                          "멈춘다) · all(내 문서함과 볼 수 있는 문서함을 하나씩 — 앞 "
                                                          f"{CABINET_ALL_MAX} 곳까지). 안 주면 내 문서함")),
    "page": (("--page",), dict(type=int, default=1)),
    "per_page": (("--per-page",), dict(type=int, default=DEFAULT_PER_PAGE)),
    "json": (("--json",), dict(action="store_true", help="줄마다 JSON 으로 낸다")),
    "cabinet": (("cabinet",), dict(help="문서함 — cabinets 의 열쇠(cab…) · 이름(일부 · 여럿이 걸리면 후보를 내고 멈춘다)")),
    "parent": (("--parent",), dict(default="", help="이 폴더(fdr…) 아래 층 — 안 주면 문서함 바로 아래")),
    "find": (("--find",), dict(default="", help="이름이 꼭 맞는 폴더를 나무 전체에서 찾아 경로와 열쇠를 낸다 — 없으면 이름에 그 글이 "
                                                "든 폴더를 후보로 낸다(고르지 않는다)")),
    "query": (("query",), dict(help="이름(일부) · 또는 org:부서 이름(일부) · org:부서코드(부서원까지)")),
    "allow_picker": (("--allow-picker",), dict(action="store_true", help="기본 앱이 없어도 열어 사람이 고르는 창에서 고르게 둔다")),
    "ai_ok": ((AI_OK_FLAG,), dict(action="store_true", help=AI_OK_HELP)),
    "as_file": (("--as-file",), dict(action="store_true",
                                     help="짧은 문서도 글자를 대화에 싣지 않고 남긴 파일의 경로만 낸다 — 긴 문서는 이 깃발 없이도 그렇게 된다")),
    "fresh": (("--fresh",), dict(action="store_true",
                                 help="남겨 둔 글자가 있어도 문서를 다시 받는다 — 표 · 그림을 뜨려고 받은 파일이 있어야 하거나 남긴 글자가 이상할 때")),
    "path": (("path",), dict(help="edit 가 낸 받은 파일")),
    "replace": (("--replace",), dict(nargs=2, action="append", default=[], metavar=("옛조각", "새조각"),
                                     help="문서 글자에 꼭 한 번 나오는 조각을 바꾼다(여러 번)")),
    "replace_file": (("--replace-file",), dict(nargs=2, action="append", default=[], metavar=("옛파일", "새파일"),
                                               help="조각이 길거나 따옴표가 들 때 — UTF-8 파일 둘")),
    "insert_from": (("--insert-from",), dict(action="append", default=[], metavar="파일",
                                             help="평문 파일(대화에서 지은 덱 · 통합 문서 · 문서)을 열린 문서로 옮긴다(여러 번 · 준 차례로)")),
    "after": (("--after",), dict(type=int, default=None, help="파워포인트 장 · 엑셀 시트 번호 — 그 뒤에 넣는다(0 은 맨 앞 · 안 주면 끝)")),
    "desc_opt": (("--desc",), dict(default="", help="수정 내용 — 주면 고친 뒤 올리기 미리 보기와 확인 열쇠까지 낸다")),
    "desc": (("--desc",), dict(required=True, help="수정 내용 — 편집완료 창의 글칸 · 동료가 판 이력에서 읽을 한 줄")),
    "confirm_checkin": (("--confirm",), dict(required=True, help="preview-checkin(또는 --desc 를 준 edit · change)이 낸 확인 열쇠")),
    "file": (("path",), dict(help="올릴 PC 의 파일")),
    "reg_cabinet": (("--cabinet",), dict(required=True, help="문서함 — 열쇠(cab…) · 이름(일부 · 여럿이 걸리면 후보를 내고 멈춘다)")),
    "reg_folder": (("--folder",), dict(default="", help="폴더 열쇠(fdr…) — folders 가 낸다")),
    "reg_folder_path": (("--folder-path",), dict(default="", help=f"폴더 경로 — 「이름 {FOLDER_SEP} 이름」(화면 · 목록 줄의 꼴)")),
    "security": (("--security",), dict(required=True, choices=sorted({s for s, _ in SECURITY_PAIRS}),
                                       help="보안등급 — 1A 기밀 · 2A 사외비A · 2B 사외비B · 3A 일반")),
    "open": (("--open",), dict(required=True, choices=["T", "F"], dest="open_flag", help="공개(T) · 비공개(F) — 1A 는 F, 3A 는 T 만")),
    "title": (("--title",), dict(default="", help="등록 이름(확장자 뺀) — 안 주면 파일 이름")),
    "confirm_register": (("--confirm",), dict(required=True, help="preview-register 가 낸 확인 열쇠")),
    **{f"grant_{word}": ((f"--{word}",), dict(action="append", default=[], metavar="사람",
                                              help=f"{ACCESS_ROLES[role]} 로 준다 — 이름 · 이름/메일ID · 이름/메일 주소 · org:부서코드 · "
                                                   "org:부서 이름 (여러 번)"))
       for word, role in ACCESS_OF_WORD.items()},
    **{f"grant_{word}_file": ((f"--{word}-file",), dict(action="append", default=[], metavar="파일",
                                                        help=f"{ACCESS_ROLES[role]} 로 줄 사람 파일 — 줄마다 --{word} 에 줄 말 하나 · "
                                                             f"{PEOPLE_COMMENT} 뒤는 버린다(company-directory 의 find --out 이 쓰는 "
                                                             "people.txt 그대로). 한 줄이라도 못 풀면 아무것도 안 짓는다 (여러 번)"))
       for word, role in ACCESS_OF_WORD.items()},
    "people_file": ((ep_command.PEOPLE_FLAG,), dict(dest="people_file", action="append", default=None, metavar="파일",
                                                    help=f"{ep_command.PEOPLE_HELP} — 사람마다 「이름/메일ID」 로 찾아 --people-as 의 칸으로 준다. "
                                                         "한 사람이라도 못 풀면 아무것도 안 짓는다")),
    "people_as": (("--people-as",), dict(default=None, choices=list(ACCESS_OF_WORD),
                                         help=f"{ep_command.PEOPLE_FLAG} 의 사람에게 줄 칸 — " +
                                              " · ".join(f"{w} {ACCESS_ROLES[r]}" for w, r in ACCESS_OF_WORD.items()))),
    "revoke": (("--revoke",), dict(action="append", default=[], metavar="사람",
                                   help="권한을 거둔다 — 이름 · 이름/메일ID · 이름/메일 주소 · org:… (여러 번)")),
    "clear": (("--clear",), dict(action="store_true", help="지금 명단을 다 비우고 시작한다(소유자 · 본인 줄은 남는다)")),
    "with_subs": (("--with-subs",), dict(action="store_true", help="org: 를 아래 부서까지 펼친다(안 주면 화면처럼 바로 든 사람만)")),
    "confirm_access": (("--confirm",), dict(required=True, help="preview-access 가 낸 확인 열쇠")),
    "ext": (("ext",), dict(help="확장자(.docx 꼴)")),
}

EDIT_CHANGES = {
    "replace": Change(("replace", "replace_file"), ("Word", "Excel", "PPT"),
                      "글 일부 — 문서 글자에 꼭 한 번 나오는 조각만(한 문단 · 한 칸 안, 빈칸 수는 너그럽게). 바꾼 글은 그 자리의 서식을 "
                      "따른다. 엑셀은 수식 칸을 안 고친다", unmeasured=("Word",)),
    "insert": Change(("insert_from", "after"), ("Word", "Excel", "PPT"),
                     "끼워 넣기 — 평문 파일의 장(파워포인트) · 시트(엑셀)를 --after 뒤에, 본문(워드)을 끝에 옮긴다. 옮긴 장은 받는 덱의 "
                     "디자인을 따른다", unmeasured=("Word",)),
}
EDITABLE_APPS = frozenset(app for c in EDIT_CHANGES.values() for app in c.apps)   # 편집 패스가 고치는 앱 — 표의 apps 칸에서
EDIT_CHANGE_ARGS = tuple(a for c in EDIT_CHANGES.values() for a in c.flags)
APP_WORD = {"Word": "워드", "Excel": "엑셀", "PPT": "파워포인트"}   # --help 가 앱 이름을 사람 말로 낼 때


def unmeasured_word() -> str:
    """안 잰 앱의 바꿀 것을 한 줄로 — 표의 unmeasured 칸에서 짓는다. 없으면 빈 글자. --help 의 지도와 편집 명령의 --help 가 낸다."""
    by_app: dict[str, list[str]] = {}
    for key, c in EDIT_CHANGES.items():
        for app in c.unmeasured:
            by_app.setdefault(app, []).append(key)
    return " · ".join(
        f"{APP_WORD.get(app, app)} 문서의 바꿀 것({' · '.join(keys)})은 회사에서 안 쟀다 — 고치다 멈추면 문서는 서버에 잠긴 채 남아 사람이 "
        "cancel-edit 로 풀어야 한다(창에 저장된 고침은 버려진다). 고치기 전에 사람에게 이 말을 한다" for app, keys in by_app.items())
PROPS_ARGS = ("object_id", "rename", "tag", "add_tag", "drop_tag", "clear_tags", "due")
REGISTER_ARGS = ("file", "reg_cabinet", "reg_folder", "reg_folder_path", "security", "open", "title")
ACCESS_ARGS = ("object_id", *(f"grant_{w}" for w in ACCESS_OF_WORD), *(f"grant_{w}_file" for w in ACCESS_OF_WORD), "people_file",
               "people_as", "revoke", "clear", "with_subs")

FINGERS = {
    "cabinets": Finger("찾기", "볼 수 있는 부서 · 프로젝트 문서함과 그 열쇠 — 제 부서가 맨 앞", (), cmd_cabinets),
    "folders": Finger("찾기", "문서함의 폴더 한 층과 열쇠 — --find 면 나무 전체에서 이름으로 찾아 경로를 낸다(꼭 맞는 것이 없으면 "
                      "이름에 그 글이 든 후보)", ("cabinet", "parent", "find"), cmd_folders, check=_pre_folders),
    "list": Finger("찾기", "문서 목록 · 찾기 — 줄마다 판 · 올린 이 · 폴더 · 보안 · 잠금 · 문서 열쇠. 문서함 안 폴더 · 왼쪽 메뉴의 목록"
                   "(--box) · 정렬 · 꼴 모아보기", ("search", "period", "folder_mine", "cabinet_opt", "box", "sort", "direction", "type",
                                                  "page", "per_page", "json"), cmd_list, check=_pre_list),
    "count": Finger("찾기", "문서 건수 — --cabinet all 이면 문서함마다와 합", ("search", "period", "folder_mine", "cabinet_opt", "box",
                                                                         "type"), cmd_count, check=_pre_list),
    "search": Finger("찾기", "전사 검색 · 본문 검색 — 제목 · 본문 · 소유자 · 등록자 · 기간 · 꼴 · 보안등급으로. 내가 볼 수 있는 문서만",
                     ("s_words", "s_title", "any_word", "s_text", "s_owner", "s_creator", "since", "until", "date_by", "s_ext", "security_in",
                      "scope", "page", "s_per_page"), cmd_search, check=_pre_search),
    "find-folder": Finger("찾기", "볼 수 있는 모든 문서함에서 이름에 그 글이 든 폴더와 열쇠 — 요청 하나(문서함 하나의 나무를 다 훑으려면 "
                          "folders --find)", ("name",), cmd_find_folder, check=_pre_find_folder),
    "doc": Finger("문서", "문서 하나의 판 · 잠금 · 보안등급 · 이름 — 속성 화면 한 번 읽기(파일을 안 받는다)", ("object_id",), cmd_doc),
    "versions": Finger("문서", "판 이력 — 판마다 올린 이 · 때 · 수정 내용 · 그 판의 열쇠(지난 판을 read · open 한다). --more 면 보안등급 "
                       "변경 · 활용 건수도", ("object_id", "page", "h_per_page", "more"), cmd_versions),
    "latest": Finger("문서", "옛 열쇠(메일 · 게시판에 남은 지난 판) → 지금 판의 열쇠", ("object_id",), cmd_latest),
    "link": Finger("문서", "문서의 보기 링크 — 화면의 「URL 복사」 꼴을 지금 판의 열쇠로 짓는다(서버에 임시 파일을 안 짓는다). 권한이 있는 "
                   "사람에게만 열린다", ("object_id",), cmd_link),
    "can": Finger("문서", "그 문서에 지금 할 수 있는 것 — 잠금(누가) · 우클릭 메뉴의 켜진 것 · 꺼진 것", ("object_id",), cmd_can),
    "notices": Finger("문서", "ECM 알림 숫자 — 받은 · 보낸 권한 · 보안등급 · 검토 요청", (), cmd_notices),
    "access": Finger("문서", "문서에 걸린 권한(편집 · 복사 · 읽기) 명단", ("object_id",), cmd_access),
    "who": Finger("문서", "ECM 이 아는 사람 · 부서 — 권한에 줄 사람을 고른다", ("query",), cmd_who),
    "open": Finger("보기", "문서를 받아 화면에 띄운다(창이 남는다 · 사람이 보는 창이라 등급 문을 안 지난다 — 글자 · 그림은 read 로)",
                   ("object_id", "allow_picker"), cmd_open, agent=True),
    "read": Finger("보기", "문서를 받아 글자를 뽑고 창을 닫는다 — 글자는 문서 열쇠로 남고, 같은 열쇠는 남긴 글자로 답한다",
                   ("object_id", "allow_picker", "ai_ok", "as_file", "fresh"), cmd_read, agent=lambda a: a.fresh or kept_text(a.object_id) is None),
    "edit": Finger("편집", "잠그고 읽기 쓰기로 연다 — 바꿀 것을 주면 열린 창에서 고쳐 저장하고, --desc 면 올리기 미리 보기까지",
                   ("object_id", "ai_ok", *EDIT_CHANGE_ARGS, "desc_opt"), cmd_edit, mutating=True, check=_pre_edit, agent=True),
    "change": Finger("편집", "편집으로 열린 그 문서를 창 안에서 고쳐 저장한다(창은 남긴다) — --desc 면 올리기 미리 보기까지",
                     ("object_id", "path", "ai_ok", *EDIT_CHANGE_ARGS, "desc_opt"), cmd_change, check=_pre_change),
    "preview-checkin": Finger("편집", "올리기 미리 보기 — 창의 고침을 저장하고 지금 판 · 수정 내용 · 확인 열쇠를 낸다(서버를 안 바꾼다)",
                              ("object_id", "path", "desc", "ai_ok"), cmd_preview_checkin,
                              check=lambda a: checkin_inputs(a.path, a.object_id, a.desc, DESC_EMPTY_PREVIEW)),
    "checkin": Finger("편집", "미리 본 그대로 다음 판으로 올린다 — 열쇠가 맞고 창에 고침이 안 남았을 때만",
                      ("object_id", "path", "desc", "confirm_checkin"), cmd_checkin, mutating=True,
                      check=lambda a: checkin_inputs(a.path, a.object_id, a.desc, DESC_EMPTY_CHECKIN)),
    "cancel-edit": Finger("편집", "편집취소 — 내가 잠근 문서의 잠금을 푼다(편집 창을 닫고 고친 것은 버린다 · 판은 그대로)",
                          ("object_id", "discard"), cmd_cancel_edit, mutating=True, agent=True),
    "preview-register": Finger("등록", "새 문서 등록 미리 보기 — 자리 · 이름 · 보안 · 확인 열쇠(올리지 않는다)", REGISTER_ARGS,
                               cmd_preview_register, check=_pre_register),
    "register": Finger("등록", "미리 본 그대로 새 문서로 올린다 — 열쇠가 맞을 때만", (*REGISTER_ARGS, "confirm_register"), cmd_register,
                       mutating=True, check=_pre_register, agent=True),
    "preview-access": Finger("권한", "권한 바꾸기 미리 보기 — 더함 · 뺌 · 옮김 · 뒤 명단 · 확인 열쇠(안 바꾼다)", ACCESS_ARGS,
                             cmd_preview_access, check=access_specs),
    "apply-access": Finger("권한", "미리 본 그대로 권한을 바꾸고 다시 읽는다 — 열쇠가 맞을 때만", (*ACCESS_ARGS, "confirm_access"),
                           cmd_apply_access, mutating=True, check=access_specs),
    "preview-props": Finger("속성", "이름 · 태그 · 완료일 바꾸기 미리 보기 — 지금 · 뒤 · 확인 열쇠(안 바꾼다)", PROPS_ARGS, cmd_preview_props,
                            check=_pre_props),
    "apply-props": Finger("속성", "미리 본 그대로 이름 · 태그 · 완료일을 바꾸고 다시 읽는다 — 열쇠가 맞을 때만",
                          (*PROPS_ARGS, "confirm_props"), cmd_apply_props, mutating=True, check=_pre_props),
    "session": Finger("손질", "ECM 세션이 살았나 본다", (), cmd_session),
    "default-app": Finger("손질", "확장자의 기본 앱 상태와 이 PC 의 해시 계산을 본다 — 쓰지 않는다(기본 앱이 안 서는 PC 를 들여다볼 때만)",
                          ("ext",), cmd_default_app, session=False),
}


def help_map() -> str:
    """--help 의 지도 — 패스마다 출발 → 손가락 → 끝 · 지키는 선, 편집 패스의 바꿀 것, 안 하는 것, 종료 값. 표에서 짓는다."""
    lines = ["할 수 있는 것의 지도 — 패스(사람이 화면 하나를 열고 칸을 바꾸고 끝 단추를 누르는 단위)마다 출발 → 손가락 → 끝.",
             "되돌리기 어려운 끝(등록 · 판 올리기 · 권한 · 속성 저장)은 미리 보기가 낸 확인 열쇠로만 간다. 인자는 <명령> --help."]
    for name, ps in PASSES.items():
        lines.append(f"\n{name} — 출발: {ps.start} · 끝: {ps.end}" + (f"\n  지키는 선: {ps.guard}" if ps.guard else ""))
        lines += [f"  {cmd:<17}{f.word}" for cmd, f in FINGERS.items() if f.pass_name == name]
        if name == "편집":
            lines += [f"  바꿀 것 {key:<9}{c.word}" for key, c in EDIT_CHANGES.items()]
            if unmeasured_word():
                lines.append(f"  ⚠ {unmeasured_word()}")
    lines.append("\n안 하는 것 — 사람이 화면에서 한다")
    lines += [f"  {w}" for w in NOT_HERE.values()]
    lines.append("\n" + EXITS)
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    """명령줄 — 손가락의 표에서 짓는다. 부르는 쪽(company_ecm.py)도 이것으로 인자를 먼저 가린다(--help 는 세션 없이 끝난다)."""
    p = argparse.ArgumentParser(description="사내 문서함(ECM) — 찾고 읽고, 사람이 확인한 문서는 고쳐 다음 판으로 올리고, "
                                "새 문서로 올리고, 권한을 주고 거둔다", epilog=help_map(), formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--session", help="세션 파일(Playwright 저장 상태) — 안 주면 MAILBOX_COOKIES")
    sub = p.add_subparsers(dest="command", required=True)
    for name, finger in FINGERS.items():
        changes_here = any(a in EDIT_CHANGE_ARGS for a in finger.args)
        q = sub.add_parser(name, help=finger.word, description=f"{finger.pass_name} — {finger.word}",
                           epilog=f"⚠ {unmeasured_word()}" if changes_here and unmeasured_word() else None)
        for key in finger.args:
            flags, kw = ARGS[key]
            q.add_argument(*flags, **kw)
    return p


REPORTED = (EcmError, default_app.DefaultAppNeeded, ValueError, OSError, subprocess.TimeoutExpired)   # report 가 종료 값으로 옮기는 것


def report(exc: BaseException) -> int:
    """명령이 멈춘 까닭을 표준 오류에 내고 종료 값을 낸다 — 뜻은 머리말 「무엇을 내나」. 부르는 쪽(company_ecm.py)도 같은 표로 낸다."""
    if isinstance(exc, default_app.DefaultAppNeeded):
        print(f"{exc}\n{DEFAULT_APP_NEXT}", file=sys.stderr)
        return EXIT_DEFAULT_APP
    print(exc, file=sys.stderr)
    for kinds, code in (((SessionMissing, SessionExpired), EXIT_SESSION), ((Classified, SecurityUnread), EXIT_CLASSIFIED),
                        ((Stale,), EXIT_STALE), ((ArgsError,), EXIT_ARGS)):
        if isinstance(exc, kinds):
            return code
    return EXIT_FAIL


def checked_args(argv: list[str] | None) -> argparse.Namespace:
    """명령줄을 풀고 서버 없이 가릴 수 있는 값을 가린 인자를 낸다 — ``--help`` · 틀린 인자는 ``SystemExit``, 틀린 값은 ``REPORTED``
    가운데 하나로 멈춘다. 한 판에 한 번만 돈다 — 부르는 쪽(company_ecm.py)도 이것을 부르고 가린 인자를 ``run`` 에 넘긴다."""
    args = parser().parse_args(argv)
    precheck(args)
    return args


def run(args: argparse.Namespace) -> int:
    """가린 인자로 그 줄의 손을 부르고 멈춘 까닭을 종료 값으로 옮긴다 — 세션이 드는 줄이면 서버 하나를 세운다."""
    finger = FINGERS[args.command]
    try:
        ecm = Ecm(url_from_env(), args.session or session_path()) if finger.session else None
        return finger.run(args, ecm)
    except REPORTED as exc:
        return report(exc)


def main(argv: list[str] | None = None) -> int:
    """명령줄 한 판 — 인자를 가리고(``checked_args``) 그 줄의 손을 부른다(``run``)."""
    try:
        args = checked_args(argv)
    except REPORTED as exc:
        return report(exc)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
