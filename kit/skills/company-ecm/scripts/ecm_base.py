"""문서함 손의 바탕 — 서버 · 에이전트 · 패스 · 명령이 함께 기대는 이름 붙은 값 · 예외 · 기록의 꼴과 서버 없이 값을 가리는 손가락을 든다.

값은 회사 ECM 화면에서 잰 꼴 그대로다(``references/SOURCES.md`` 「사내 ECM 에서 잰 것」). 형제 스킬 ep-login 의 ``ep_command`` ·
``ep_session``(종료 값 표 · ECM 주소) 과 drm-office-read 의 ``places.json``(받는 자리)을 여기서 싣는다 — 못 읽으면 실리지 않는다.
"""

from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

SKILLS_HOME = pathlib.Path(__file__).resolve().parents[2]   # 스킬 홈 — 형제 스킬이 나란히 깔린다(도구 홈마다 · 설정 저장소에서도)
EP_LOGIN_SCRIPTS = SKILLS_HOME / "ep-login" / "scripts"     # 형제 스킬 — 세션 파일을 읽는 자리
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_command  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다
import ep_session  # noqa: E402

DEFAULT_URL = ep_session.ECM_URL
DEFAULT_AGENT = "ws://localhost:8383/"
DRM_READ_SCRIPTS = SKILLS_HOME / "drm-office-read" / "scripts"   # 형제 스킬 — 글자를 뽑는 손과 받는 자리의 값 파일
# 에이전트가 받은 파일을 두는 자리의 원본 — 등급 문을 세우는 읽는 손 · 뜨는 손 · DRM 길잡이 훅이 함께 읽는 값 파일 하나다. 그 스킬이
# 어느 도구 홈에나 깔려 이 스킬이 없는 홈에서도 문이 같은 자리에 선다
DRM_PLACES_FILE = DRM_READ_SCRIPTS / "places.json"
try:
    DEFAULT_DOCS_ROOT = json.loads(DRM_PLACES_FILE.read_text(encoding="utf-8"))["ecm_docs_root"]
except (OSError, ValueError, KeyError) as _exc:
    raise ImportError(f"문서함 받는 자리의 값 파일을 못 읽었다: {DRM_PLACES_FILE} ({_exc}) — 스킬 drm-office-read 가 이 스킬 곁에 "
                      "깔렸는지 본다(설치를 다시 돌린다)") from _exc
DOCS_ROOT_ENV = "ECM_DOCS_ROOT"
DEFAULT_READER = DRM_READ_SCRIPTS / "read-drm.ps1"
# 읽는 손이 받는 확장자 — 그 손의 값 파일(handler.json)이 원본이다. 읽는 손은 받는 꼴마다 글 맨 위에 목차를 둔다
try:
    READER_SUFFIXES = frozenset(json.loads((DRM_READ_SCRIPTS / "handler.json").read_text(encoding="utf-8"))["handler"])
except (OSError, ValueError, KeyError) as _exc:
    raise ImportError(f"읽는 손의 확장자 표를 못 읽었다: {DRM_READ_SCRIPTS / 'handler.json'} ({_exc}) — 스킬 drm-office-read 가 이 스킬 곁에 "
                      "깔렸는지 본다") from _exc
# 읽는 손 · 뜨는 손이 받는 자리 밑의 파일을 여는 깃발 — 그 손은 이 깃발 없이는 문서함 받은 파일을 안 연다. 이 손은 등급 문을 지난 뒤에만 준다
READER_GATE_FLAG = "-EcmGated"
CLOSE_SCRIPT = pathlib.Path(__file__).resolve().parent / "close_view.ps1"
ACROBAT_CLOSE_SCRIPT = pathlib.Path(__file__).resolve().parent / "close_acrobat.ps1"
CHECKIN_SCRIPT = pathlib.Path(__file__).resolve().parent / "checkin_window.ps1"
CHANGE_SCRIPT = pathlib.Path(__file__).resolve().parent / "change_doc.ps1"

HTTP_TIMEOUT = 30.0
AGENT_TIMEOUT = 60.0      # 에이전트가 OK 를 낼 때까지
FILE_TIMEOUT = 120.0      # OK 뒤 받은 파일이 다 생길 때까지
WINDOW_WAIT = 30.0        # 받은 파일을 띄운 창이 오피스에 잡힐 때까지
CHECKIN_WAIT = 60.0       # 오피스가 끝난 뒤 에이전트의 편집완료 창이 뜰 때까지
CHECKIN_ATTACH_TRIES = 4  # 편집완료 창의 칸을 못 읽었을 때 새 프로세스로 다시 붙는 판 수(첫 판 포함)
CHECKIN_REATTACH_WAIT = 10.0  # 다시 붙는 판이 창을 찾는 시한 — 창은 이미 떠 있다
UNCHANGED_WAIT = 3.0      # 오피스가 끝난 뒤 고친 것 없는 판의 잠금이 풀리기를 보는 시한
CANCEL_WAIT = 10.0        # 편집취소를 보낸 뒤 잠금이 풀리기를 보는 시한 — 쟀을 때는 곧바로 풀렸다
CANCEL_FIND_WAIT = 3.0    # 편집취소 앞에서 편집 창을 찾는 시한 — 창이 없으면 바로 넘어간다
VERSION_WAIT = 60.0       # 편집완료를 누른 뒤 문서 정보의 최종 버전이 바뀔 때까지
VERSION_POLL = 3.0
FIND_ONLY_DESC = "find-only"   # 찾기만 할 때의 자리 글 — 「-」 하나는 PowerShell 이 인자 이름으로 읽어 부름이 진다
READ_TIMEOUT = 600.0      # 읽는 손 한 판
CHANGE_TIMEOUT = 300.0    # 고치는 손 한 판 — 문서를 찾는 시한 뒤에 더한다(큰 덱 · 시트를 옮기는 데 든다)
POLL = 0.5

# 명령줄의 종료 값 — 사내 앱 명령이 함께 쓰는 한 표(ep_command)를 그대로 쓴다. 뜻은 머리말 「무엇을 내나」
EXIT_OK, EXIT_FAIL, EXIT_ARGS, EXIT_SESSION = ep_command.EXIT_OK, ep_command.EXIT_TOOL, ep_command.EXIT_ARGS, ep_command.EXIT_SESSION
EXIT_STALE, EXIT_DEFAULT_APP, EXIT_CLASSIFIED = ep_command.EXIT_STALE, ep_command.EXIT_DEFAULT_APP, ep_command.EXIT_CLASSIFIED
# 명령줄이 내는 종료 값의 범례(맨 위 --help) — 뜻은 ep_command 의 한 표. 까닭은 JSON 이 아니라 표준 오류에 선다(report)
EXITS = ep_command.exit_legend((EXIT_OK, EXIT_FAIL, EXIT_ARGS, EXIT_SESSION, EXIT_STALE, EXIT_DEFAULT_APP, EXIT_CLASSIFIED),
                               {EXIT_CLASSIFIED: "사람이 AI 로 보내도 된다고 답한 뒤에만 --ai-ok"},
                               said="0 이 아니면 표준 오류의 말이 까닭과 다음 걸음을 든다")

AJAX = "/ajaxAction.do"
MAIN_PAGE = ep_session.ECM_MAIN_PAGE
MY_DOCS = "F_LIST_MYDOC"
DEPT_DOCS = "F_LIST_MYDEPT"   # 부서 · 프로젝트 문서함 — listKey 는 <문서함 열쇠>_<문서함 열쇠>(화면의 왼쪽 메뉴)
PROPERTY_PAGE = "/docProperty_simple.do"
PROPERTY_QUERY = {"ServiceName": "DocPropertyHtml-service", "basicinfo": "true", "getType": "user"}   # + DOCID
# 메인 화면이 든 그 사람의 문서함 — <option id="MENU_DEPT|MENU_PROJECT" value='cab…'>이름</option> · 제 부서 열쇠
CABINET_OPTION = re.compile(r"""<option\s+id=["'](MENU_DEPT|MENU_PROJECT)["']\s+value=["'](cab[0-9a-f]+)["']\s*>([^<]+)</option>""",
                            re.IGNORECASE)
OWN_CABINET = re.compile(r"\bs_UserDeptCabinetId\s*=\s*'(cab[0-9a-f]+)'", re.IGNORECASE)
CABINET_KIND = {"MENU_DEPT": "부서", "MENU_PROJECT": "프로젝트"}
CABINET_ID = re.compile(r"^cab[0-9A-Fa-f]+$")
PROPERTY_VERSION = "최종 버전"
# 문서 정보 화면이 권한 칸 주소에 싣는 잠금 상태 — 편집으로 잠겼으면 T. 고친 것 없이 닫으면 에이전트가 편집완료 창 없이 바로 푼다
PROPERTY_LOCK = re.compile(r"[?&;]lockStatus=([TF])\b")
# 에이전트가 받은 파일 이름에 붙이는 꼬리 — <이름>_<문서 열쇠>_<사람 열쇠>.<확장자>. 사람에게 보일 때는 뗀다
AGENT_FILE_SUFFIX = re.compile(r"_[0-9A-Fa-f]{16}_[^_]+(?=\.[^.]+$)")
# 읽기로 잰 요청 — 서비스 이름 → (참이어야 하는 갈래 칸 하나, 실을 수 있는 칸). 닫힌 목록이라 새 꼴은 읽기임을 잰 뒤 여기 더해야 묻는다
READS = {
    "DocList-service": (("getDocList", "getDocCount"),
                        {"isHTML", "formId", "listKey", "searchValue", "pageNumber", "docCntPerPage", "searchPeriod",
                         "wfStatusType", "fileType", "orderBy", "sortDirection", "isIncludeCntQry"}),
    "OpenContents-service": (("view",), {"MS_OBJECT_ID", "formId", "MS_CURRENT_YN"}),   # MS_CURRENT_YN=T — 옛 판 열쇠가 지금 판을 낸다
    "CheckOutCheckIn-service": (("checkuser",), {"MS_OBJECT_ID"}),     # 잠근 이가 나인가 — 편집취소 화면이 먼저 묻는 읽기
    "GetDashboardCount-service": (("getNoticeCount",), set()),          # 왼쪽 「ECM 알림」 숫자
}
FOLDER_DOCS = "F_LIST_FOLDER"   # 부서 · 프로젝트 문서함 안 폴더의 목록 — listKey 는 <문서함>_<폴더>(왼쪽 나무에서 폴더를 누른 꼴)
# 왼쪽 메뉴의 다른 목록 — 낱말 → (formId, 사람에게 보일 이름). 같은 DocList-service 에 formId 만 바꾸고 listKey 는 빈 글자다
BOXES = {"recent": ("F_LIST_RECENT_ACCESS", "최근 활용 컨텐츠"), "new": ("F_LIST_RECENT_REGIST", "최신 컨텐츠"),
         "shared": ("F_LIST_SHARED_DOC", "공유받은 컨텐츠"), "co-edit": ("F_LIST_CORESPONSIBLE", "공동작성 컨텐츠"),
         "important": ("F_LIST_FAVFOLDER", "중요 컨텐츠"), "editing": ("F_LIST_CHECKOUT", "편집 중 컨텐츠"),
         "trash": ("F_LIST_RCB", "휴지통"), "asked-me": ("F_LIST_GRANT", "권한 받은 요청"),
         "i-asked": ("F_LIST_REQUESTED_GRANT", "권한 보낸 요청")}
READ_FORMS = (MY_DOCS, DEPT_DOCS, FOLDER_DOCS, *(f for f, _ in BOXES.values()))    # formId 로 잰 값
# 목록 머리 글 누르기(정렬) — 낱말 → orderBy. ms_reg_date 는 서버가 거절했다(MB_RTN_VALUE 거짓) — 등록일 정렬은 없다
SORTS = {"modified": "ms_modify_date", "title": "ms_title", "size": "ms_file_size", "owner": "ms_owner_name",
         "security": "ms_security_level", "version": "ms_doc_version"}
# 목록 위 확장자 모아보기 — 낱말 → fileType. 모르는 값은 거절 없이 0 건이 온다(GATHER_NOPE 로 쟀다)
FILE_TYPES = {"ppt": "GATHER_POWERPOINT", "excel": "GATHER_EXCEL", "word": "GATHER_WORD", "pdf": "GATHER_PDF",
              "hwp": "GATHER_HWP", "image": "GATHER_IMAGE"}
NOTICE_WORDS = (("APP_PERMIT", "받은 권한 요청"), ("REQ_PERMIT", "보낸 권한 요청"), ("APP_SECURITY", "받은 보안등급 요청"),
                ("REQ_SECURITY", "보낸 보안등급 요청"), ("APP_REVIEW", "받은 검토 요청"), ("REQ_REVIEW", "보낸 검토 요청"))
# 조회지만 POST 인 셋 — (질의, 몸의 칸들). 몸은 화면이 보내는 꼴 그대로이고 이 손은 그 밖의 POST 를 읽기로 안 보낸다
CONTEXT_QUERY = {"ServiceName": "GetContextMenu-service", "isHTML": "T"}                   # 몸 formId · itemObjIds · IsChorme
SEARCH_QUERY = {"ServiceName": "DocList-service", "getDocListEcmEsSearch": "true"}        # 몸 q · page_idx · num · backCategory · sysId
FOLDER_FIND_QUERY = {"ServiceName": "searchFolder-service", "search_html": "true", "isHTML": "T", "deptExceptFlag": ""}   # json.do · 몸 companyId · userId · value
# 판 이력 · 보안등급 변경 이력 · 활용 건수 — 속성 화면의 변경이력 · 활용 탭이 묻는 json.do 읽기
HISTORY_QUERY = {"ServiceName": "DocPropertyHtml-service", "history": "true", "pageType": "user", "isMinorManagement": "F"}   # + R_OBJECT_ID=doc… · isIncludeCntQry · pageNumber · docCntPerPage
SECURITY_LOG_QUERY = {"ServiceName": "DocPropertyHtml-service", "security": "true", "pageType": "user"}   # + ECM_DOC_ID · isIncludeCntQry · pageNumber · docCntPerPage
USE_QUERY = {"ServiceName": "DocPropertyHtml-service", "useinfo": "true", "pageType": "user"}            # + ECM_DOC_ID
SCREEN_NO_DUE = "0001/01/01"            # 속성 화면이 완료예정일 없음으로 드는 값 — 저장 몸도 그대로 싣는다
TAG_MAX = 10                             # 화면의 태그 칸 — 10 개까지 · 한글 · 영문 · 숫자만
TAG_WORD = re.compile(r"^[가-힣a-zA-Z0-9]+$")
HISTORY_PER_PAGE, HISTORY_PER_PAGE_MAX = 10, 100   # 판 이력 한 쪽 — 화면의 기본 10
USE_WORDS = (("ECM_VIEW", "열람"), ("ECM_ATTACH", "첨부"), ("ECM_COPY", "복사"), ("ECM_RECOMMEND", "추천"))
# 전사 검색 — 화면이 짓는 posmeta 칸 그대로(searchProperty_both.jsp). 이 손이 채우는 칸만 값이 들고 나머지는 빈 글자다
SEARCH_FIELDS = ("reqsysid", "adv_search_type", "subject", "subject_operator", "allintext", "ecmtaglist", "ecmtaglist_operator",
                 "owner", "creator", "udaterange", "cdaterange", "format", "approval", "security", "docbox", "folderbox", "sort",
                 "subfolder_yn")
SEARCH_COMPANY, SEARCH_MINE = "company", "mine"     # 전사 — docbox 빈 글자 · 내 문서함들 — 메인 화면의 s_deptCabinets 그대로
SEARCH_PER_PAGE_MAX = 100
SEARCH_DATE_FIELDS = {"modified": "udaterange", "registered": "cdaterange"}
SEARCH_WORD_BAD = re.compile(r'["\\{}]')            # 화면은 posmeta 를 글자 이어 붙이기로 짓는다 — 이 글자가 들면 꼴이 깨진다
DATE_TEXT = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PERSONAL_OPTION = re.compile(r"""<option\s+id=["']MENU_PERSONAL["']\s+value=["'](usr[0-9a-f]+)["']""", re.IGNORECASE)   # 메인 화면이 든 내 사람 열쇠
COMPANY_VAR = re.compile(r"\bcompanyId\s*=\s*['\"](com[0-9A-Fa-f]+)['\"]")   # 메인 화면 — 그 사람의 회사 열쇠(사람 · 조직 찾기가 싣는다)
DEPT_CABINETS = re.compile(r"\bs_deptCabinets\s*=\s*'([^']*)'")   # 메인 화면 — 전사 검색의 docbox 값(제 부서는 부서 코드 · 프로젝트는 cab 열쇠)
# 문서함을 바꾸는 요청 — 편집 열기와 새 문서 등록 둘만 짓는다. 읽기 길(guard)은 이것도 막고, Ecm.checkout · Ecm.register 만 그 꼴을 연다
EDIT_SERVICE, EDIT_FLAG = "CheckOutCheckIn-service", "checkout"
CANCEL_FLAG = "cancelcheckout"          # 편집취소의 서버 걸음 — 같은 문(_guard_edit)이 갈래 둘만 연다
AGENT_CANCEL = "cancelcheckout"         # 편집취소의 에이전트 한 줄 — cancelcheckout␈<문서 열쇠>. 잠금을 푸는 것은 이 줄이다(SOURCES.md)
# 폴더 나무 — 문서함 열쇠 아래 첫 층(menuType = 문서함 갈래), 폴더 아래(menuType = F_LIST_FOLDER · upperKey = <문서함>_<폴더>)
FOLDER_SERVICE = "GetSubNaviMenu-service"
FOLDER_ROOT_TYPES = ("MENU_DEPT", "MENU_PROJECT")
FOLDER_TYPE = "F_LIST_FOLDER"
FOLDER_ID = re.compile(r"^fdr[0-9A-Fa-f]+$")
FOLDER_KEY = re.compile(r"^(cab[0-9A-Fa-f]+)_(fdr[0-9A-Fa-f]+)$")
FOLDER_SEP = ">"                        # 폴더 경로의 마디 — 화면이 보이는 꼴(「기획그룹 > 기타」) 그대로 받고 낸다
FOLDER_WALK_MAX = 200                   # 폴더 나무를 훑는 한 판의 요청 상한 — 넘으면 멈추고 경로로 달라고 한다(큰 문서함을 끝없이 안 묻는다)
# 등록 화면의 두 POST — 같은 이름 찾기(읽기)와 등록(바꾼다). 몸은 화면의 getData · checkDocDuplication 이 짓는 꼴 그대로다
DUP_QUERY = {"ServiceName": "CheckDuplicatedDoc-service", "checkDup": "true"}
REGISTER_QUERY = {"isHTML": "T"}
REGISTER_SERVICE = "RegisterContents-service"
REGISTER_ROW = "contentName_1"          # 화면이 첫 파일 줄에 붙이는 이름 — 에이전트 올림 · 등록 몸이 같은 이름으로 잇는다
AGENT_UPLOAD = "uploadfilecreatedoc"    # 에이전트가 파일을 서버 임시 자리(/WAS/ECMTEMP)에 올리고 그 이름을 JSON 으로 답한다
# 보안등급 · 공개 — 등록 화면의 단추 여섯이 짓는 짝만 받는다(기밀은 비공개만 · 일반은 공개만)
SECURITY_PAIRS = {("1A", "F"): "기밀", ("2A", "F"): "사외비A/비공개", ("2A", "T"): "사외비A",
                  ("2B", "F"): "사외비B/비공개", ("2B", "T"): "사외비B", ("3A", "T"): "일반"}
# 공개 짝이 누구에게 보이나 — 등록 미리 보기가 사람에게 그대로 보인다(잘못 고르면 동료 전체에 보인다)
AUDIENCE = {("2A", "T"): "부서원이 본다", ("2B", "T"): "전 직원이 검색으로 본다", ("3A", "T"): "전 직원이 본다"}
CLASSIFIED_LEVELS = ("1A",)              # 기밀 — 이 등급의 문서는 사람에게 묻기 전에 받아 글자를 뽑거나 편집으로 열지 않는다
CORE_VAR = "sIsDocTypeCore"               # 속성 화면의 핵심기술 표시(스크립트 갈래 값) — "T" 면 핵심기술 문서다
AI_OK_FLAG = "--ai-ok"
ASK_BEFORE_AI = (f"사람에게 문서 이름과 등급을 밝히고, 국가핵심기술이나 특허처럼 독점적 성격을 띤 정보는 AI 모델에 보내지 않도록 "
                 f"주의를 당부한 뒤 이 문서를 AI 로 보내도 되는지 묻는다. 된다고 답한 뒤에만 같은 명령에 {AI_OK_FLAG} 를 붙이고, 안 된다고 하면 "
                 "사람이 ECM 화면에서 직접 연다")
# 등급 문에서 멈춘 자리 — 무엇을 안 했고 무엇이 모델로 가나(멈춘 말의 앞)
GATE_RECEIVE = "받지 않았다 — 글자가 대화의 모델로 간다"
GATE_EDIT = "창의 문서를 건드리지 않았다 — 편집 패스는 고친 자리를 찍어 대화의 모델로 보인다"
SECURITY_FIELD, OPEN_FIELD = "ecm_security_level", "ecm_open_flag"   # 속성 화면의 숨은 칸 — 편집 화면이 지금 등급을 싣는 자리
DOC_TYPE_GENERAL = "1"                  # 화면의 「컨텐츠 등록」이 기본으로 두는 문서 유형
DOC_STATUS_DRAFT = "0"
NO_DUE_DATE = "0001-01-01"
TITLE_MAX = 125                         # 화면의 addFile 이 거는 한도 — 이름은 확장자를 빼고, 바이트는 한글을 3 으로 센다
TITLE_BYTES_MAX = 250
TITLE_BAD = re.compile(r'[\\/:*?"<>|`%#\'‘’＇｀´′]')   # 화면이 막는 글자 + # (서버가 등록 때 말없이 뗐다 — 쟀다)
SERVER_NAME = re.compile(r"^[/\w.\-]+$")   # 에이전트가 준 서버 임시 자리 · 파일 이름의 글자 — 몸의 칸을 가르는 & · = · + · % 가 없게
# 권한 — 속성 화면의 저장 하나(ModifyDocProperty-service)와 그 화면 · 권한 iframe 이 묻는 json.do 읽기들
JSON_READ = "/json.do"
PROPERTY_SAVE_QUERY = {"ServiceName": "ModifyDocProperty-service"}
ROLE_QUERY = {"ServiceName": "DocPropertyHtml-service", "role": "true", "pageType": "user"}            # + ECM_DOC_ID
FAVORITE_QUERY = {"ServiceName": "DocPropertyHtml-service", "favorite_info": "true", "pageType": "user"}  # + ECM_DOC_ID
PEOPLE_QUERY = {"ServiceName": "searchPeople-service", "language": "ko", "isHTML": "T", "searchKind": "single", "kind": "name"}
ORGAN_SERVICE = "searchOrgan2-service"
ORGAN_FIND = {"search": "1", "searchKind": "role"}           # + value — 부서 이름(일부)
ORGAN_SUBS = {"getDept": "1", "kind": "dept"}                # + deptId — 바로 아래 부서
ORGAN_USERS = {"getUser": "1"}                               # + deptId — 그 부서에 바로 든 사람
# 화면의 권한 칸 셋 — 이 손이 주고 거두는 역할. 그 밖의 역할(승인 A · 검토 C · 조회 I · 배포 D · 승인 대기 W)이 걸린 문서는 안 잰다
ACCESS_ROLES = {"R": "편집/복사/읽기/인쇄", "S": "복사/읽기/인쇄", "V": "읽기/인쇄"}
ACCESS_OF_WORD = {"edit": "R", "copy": "S", "read": "V"}
ROLE_ORDER = "WRCAIDSV"                                      # 화면의 getTabPageRoleSerialize 가 싣는 차례
PERSON_ID = re.compile(r"^usr[0-9A-Fa-f]+$")
COMPANY_ID = re.compile(r"^com[0-9A-Fa-f]+$")
DEPT_CODE = re.compile(r"^[A-Z][0-9A-Z]{4,9}$")
NAME_MIN = 2                                                 # 화면의 checkValue — 검색어는 두 글자부터
# 저장 몸 — (보낼 칸, 속성 화면의 숨은 칸). 화면의 getDocInfoData 차례 그대로이고 값은 그 화면이 든 값이다. 이름 둘만 encodeURIComponent 한다
SAVE_FROM_PAGE = (("sViewStatus", "sViewStatus"), ("MS_ORI_DOC_TITLE", "MS_ORI_DOC_TITLE"),
                  ("MS_ORI_SECURITY_LEVEL", "MS_ORI_SECURITY_LEVEL"), ("MS_ORI_RETENTION_PERIOD", "MS_ORI_RETENTION_PERIOD"),
                  ("MS_OBJECT_ID", "MS_OBJECT_ID"), ("MS_DOC_ID", "MS_DOC_ID"), ("MS_COPY_FLAG", "MS_COPY_FLAG"),
                  ("MS_COPY_DOC_SECURITY_LEVEL", "MS_COPY_DOC_SECURITY_LEVEL"), ("MS_DOC_TITLE", "MS_DOC_TITLE"),
                  ("MS_DOC_EXTENSION", "MS_DOC_EXTENSION"), ("MS_PROCESS_CODE", "MS_PROCESS_CODE"),
                  ("MS_FOLDER_ID", "ecm_folder_id"), ("MS_FOLDER_PATH", "MS_FOLDER_PATH"), ("MS_TAG_LIST", "MS_TAG_LIST"),
                  ("MS_SECURITY_LEVEL", "ecm_security_level"), ("MS_OPEN_FLAG", "ecm_open_flag"),
                  ("MS_DOC_STATUS", "MS_DOC_STATUS"), ("MS_DOC_TYPE", "ecm_doc_type"), ("MS_OWNER_NAME", "MS_OWNER_NAME"),
                  ("MS_CABINET_NAME", "MS_CABINET_NAME"), ("MS_REG_DATE", "MS_REG_DATE"),
                  ("MS_CREATE_USER_NAME", "MS_CREATE_USER_NAME"), ("MS_CONTENT_SOURCE", "MS_CONTENT_SOURCE"),
                  ("ecm_review_status", "ecm_review_status"), ("ecm_approve_status", "ecm_approve_status"),
                  ("ecm_approve_cnt", "ecm_approve_cnt"), ("ecm_seculevel_cnt", "ecm_seculevel_cnt"),
                  ("ecm_protected_cnt", "ecm_protected_cnt"), ("ecm_unprotect_cnt", "ecm_unprotect_cnt"))
SAVE_ENCODED = ("MS_ORI_DOC_TITLE", "MS_DOC_TITLE")
SAVE_TAIL_FROM_PAGE = (("isChangeOwner", "isChangeOwner"), ("MS_NEW_OWNER", "MS_NEW_OWNER"), ("MS_DUE_DATE", "ecm_EndDate"))
SAVE_WORKFLOW_FROM_PAGE = (("ecm_workflow_Process", "ecm_workflow_Process"),
                           ("ecm_workflowApproveUserId", "ecm_workflowApproveUserId"),
                           ("ecm_workflowRequestComment", "ecm_workflowRequestComment"),
                           ("ecm_workflowNewUserId", "ecm_workflowNewUserId"))
ABSENT_FIELD = "undefined"                                   # 화면에 없는 칸을 jQuery 가 싣는 값 — ecm_security_approve 만 없을 수 있다
SAVE_OPTIONAL = ("ecm_security_approve",)
# 이 손이 잰 문서의 꼴 — 이 값이 아니면 화면이 다른 칸 · 다른 차례를 더하므로 보내기 전에 멈춘다
MEASURED_PAGE = {"sViewStatus": "EDIT", "isChangeOwner": "F", "MS_NEW_OWNER": "", "ecm_workflow_Process": "F"}
MEASURED_VARS = {"sIsDocTypeCore": "F", "s_IsUseRai": "F"}
MEASURED_FRAME = {"sIsDocTypeProtected": "F", "lockStatus": "F"}
UNMEASURED_CHECKS = ("id_setAutoGrant", "id_AiExclusionFlag")   # 화면에 이 체크 칸이 서면 그 값을 싣는다 — 안 쟀다
RAW_BAD = re.compile(r"[&%+]")                              # 화면은 이 칸들을 인코딩 없이 이어 붙인다 — 이 글자가 들면 칸이 갈린다
ELEMENT_ID = re.compile(r"<[a-z]+\b[^>]*?\bid\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
PAGE_VAR = re.compile(r"\bvar\s+(\w+)\s*=\s*[\"']([^\"']*)[\"']")
ROLE_FRAME = re.compile(r"roleAssignEdit\.jsp\?([^\"']*)")
TOKEN_LENGTH = 12
LIST_DEFAULTS = {"isHTML": "T", "formId": MY_DOCS, "wfStatusType": "", "fileType": "ALL_FORMAT", "orderBy": "",
                 "sortDirection": "desc"}
DEFAULT_PERIOD = "6M"
# 화면 기간 필터의 값 그대로 — 밖의 값은 거절되거나 거절 없이 틀린 목록이 온다
PERIODS = ("1M", "6M", "12M", "24M", "36M", "60M", "ALL")
DEFAULT_PER_PAGE = 15
# 이 손이 안 하는 것 — 열쇠 → 사람에게 할 말(어디서 하나). 멈추는 말과 --help 의 지도가 이 표 하나를 읽는다. 안 잰 화면 동작이
# 회사에서 잰 꼴이 되면 그 줄을 걷고 손가락 하나(표의 한 줄과 그 일을 하는 손)를 더한다
NOT_HERE = {
    "cancel_other": "남이 잠근 문서의 편집취소 — 그 사람이 고친 것이 사라진다. 그 사람에게 편집완료 · 편집취소를 청한다",
    "delete": "지우기 · 옮기기 · 복사 · 휴지통에서 되살리기 — 사람이 ECM 화면에서 한다",
    "owner": "소유자 · 보안등급 바꾸기 · 완료(편집불가) 처리 · 보관 연장 — 사람이 화면의 「컨텐츠 속성」 · 우클릭 메뉴에서 한다",
    "version_restore": "지난 판으로 되돌리기 · 판 지우기 — 사람이 화면의 「컨텐츠 속성 → 변경이력」에서 한다(지난 판을 읽는 것은 versions · read)",
    "requests": "권한 요청 · 승인 · 반려 · 검토 요청 — 남에게 알림이 가는 결재 흐름이라 사람이 화면에서 한다(목록은 list --box asked-me · i-asked)",
    "favorite": "즐겨찾기 · 공유하기(추천) · 편집 예약 — 사람이 우클릭 메뉴에서 한다",
    "mail_link": "문서함 문서를 메일 첨부(문서함 쪽지)로 보내기 — 그 화면은 서버에 임시 파일을 짓는다(안 쟀다). 사람이 ECM · 웹메일 화면에서 "
                 "붙인다. 메일 본문에 넣을 링크는 link 가 낸다",
    "save_pc": "PC 에 저장(작업방 내리기) · 목록 엑셀로 · 퀵뷰 — 사람이 화면에서 한다. 읽기는 read 가 한다",
}
CANCEL_NEXT = ("사람이 그만두자고 하면 cancel-edit {object_id} 로 잠금을 푼다(편집 창의 고침은 버린다 — 저장 안 된 고침이 있으면 "
               "사람에게 확인한 뒤 --discard)")
TEXT_DIR = "~/.company-ecm-text"       # read 가 뽑은 글자를 남기는 자리 — 홈 아래(저장소 밖 · 임시 폴더 정리에 안 걸린다)
TEXT_DIR_ENV = "ECM_TEXT_DIR"
KEPT_SOURCE_WORD = " · 받은 파일 "      # 남긴 글자의 머리 둘째 줄에서 받은 파일의 자리를 여는 말 — keep_text 가 쓰고 read_kept_file 이 읽는다
KEPT_WHEN_WORD = " · 뽑은 때 "         # 같은 줄에서 그 자리를 닫는 말
TEXT_EXT = ".md"                     # 글자 파일의 꼴 — 읽는 손(-OutDir)이 내는 것도 여기 남기는 것도. Fasoo 가 .txt · .csv 는 감싸고 .md 는 평문으로 둔다
TEXT_SPLIT = "\n---\n"                 # 남긴 파일에서 머리(읽는 손의 한 줄 · 열쇠와 뽑은 때)와 글자를 가르는 줄
OBJECT_ID = re.compile(r"^[0-9A-Fa-f]{16}$")
AGENT_FIELD_SEPARATOR = "\x08"
AGENT_ACTION_VIEW = "VIEW"
AGENT_ACTION_EDIT = "EDIT_NOCHECKIN"   # 편집 열기 — 편집완료는 에이전트의 창이 맡는다
CHECKOUT_FOLDER = "CHECKOUT"
AGENT_SYSTEM = "ECM"
AGENT_OK = "OK"
VIEW_FOLDER = "VIEW"
LOCK_PREFIX = "~$"
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
# 오피스 앱 — ProgId 의 앞머리 → 닫는 손이 붙을 앱(이름은 drm-office-read 의 앱 이름과 같다)
OFFICE_OF_PROGID = {"word.": "Word", "excel.": "Excel", "powerpoint.": "PPT"}
# pdf 보기 앱 — 이 ProgId 면 close_acrobat.ps1 이 그 탭을 닫는다. 그 밖의 앱(Edge 따위)은 안 닫는다
ACROBAT = "Acrobat"
ACROBAT_PROGID = "acroexch."
# 닫는 손(close_view.ps1 · close_acrobat.ps1)의 종료 값 → 창의 상태. 그 밖의 값은 실패다
CLOSE_EXIT = {0: "closed", 2: "not-found", 3: "not-front", 4: "dirty"}
# 고치는 손(change_doc.ps1)의 종료 값 — 0 고치고 저장했다 · 2 그 문서가 안 떴다 · 3 아무것도 안 고쳤다(까닭) · 그 밖은 고치다 멈췄다
CHANGE_DONE, CHANGE_NOT_FOUND, CHANGE_REFUSED = 0, 2, 3
# 끼워 넣을 평문 파일의 꼴 — 받는 앱마다(파워포인트는 장, 엑셀은 시트, 워드는 본문)
INSERT_FAMILY = {"PPT": (".pptx", ".ppt"), "Excel": (".xlsx", ".xls", ".xlsm"), "Word": (".docx", ".doc")}
WORD_FIND_MAX = 255                     # 워드 찾기가 받는 글자 수 — 조각이 길면 워드가 못 찾는다
LINE_BREAK = re.compile(r"[\r\n\v]")
# 보기를 거절한 코드 — 사람에게 서버 글 대신 할 일을 낸다. 볼 권한이 없는 문서(문서함 화면에도 안 보인다)에 ECM 이 내는 코드다
VIEW_DENIED = "MSG_E_0035"
OFFICE_BY_EXT = {".docx": "Word", ".doc": "Word", ".xlsx": "Excel", ".xls": "Excel", ".xlsm": "Excel",
                 ".pptx": "PPT", ".ppt": "PPT"}

log = logging.getLogger("ecm")   # 기록 이름은 명령 이름 그대로


class EcmError(Exception):
    """ECM 일을 못 했다. 메시지가 사유다."""


class SessionMissing(EcmError):
    """세션 파일이 없거나 그 안에 ECM 호스트의 쿠키가 없다 — 스킬 ep-login 으로 받는다."""


class SessionExpired(EcmError):
    """ECM 이 세션을 안 받았다(``302 → /ECM/logout.jsp`` 따위) — 스킬 ep-login 으로 다시 받는다."""


class Refused(EcmError):
    """잰 꼴 밖의 요청을 지었다 — 읽기 · 편집 열기 · 등록 POST 어느 길이든 서버에 닿기 전에 막았다."""


class AgentError(EcmError):
    """PC 의 ECM 에이전트가 안 돌거나, 거절했거나, 받은 파일이 안 생겼다."""


class AgentTimeout(AgentError):
    """ECM 에이전트가 시한 안에 답하지 않았다 — 어느 줄에서든. 받기에서는 메일 첨부의 머리 열쇠가 흔한 까닭이다(그 말은 받는 쪽이 든다)."""


class ReadError(EcmError):
    """받은 파일에서 글자를 못 뽑았다."""


class Classified(EcmError):
    """기밀 · 핵심기술 문서라 사람에게 묻기 전에 멈췄다 — AI 로 보내도 된다고 답하면 ``ai_ok`` 로 넘긴다."""


class SecurityUnread(EcmError):
    """속성 화면에서 보안등급을 못 읽어 사람에게 묻기 전에 멈췄다 — AI 로 보내도 된다고 답하면 ``ai_ok`` 로 넘긴다."""


class ArgsError(EcmError):
    """준 값이 틀렸거나 아무것도 가리키지 않는다 — 아무것도 안 건드렸다. 메시지대로 인자를 고쳐 다시 부른다."""


class Stale(EcmError):
    """확인 열쇠가 지금과 다르다 — 미리 본 뒤 문서 · 파일 · 명단이 바뀌어 아무것도 안 바꿨다. 미리 보기를 다시 사람에게 보인다."""


@dataclass(frozen=True)
class Security:
    """문서의 보안등급 · 공개 — 속성 화면의 숨은 칸 그대로. ``core`` 는 핵심기술 표시(``CORE_VAR``)다."""
    level: str
    open_flag: str
    core: bool = False

    @property
    def name(self) -> str:
        """등급 · 공개 짝의 화면 이름 — 화면에 없는 짝이면 등급 이름 뒤에 그 짝을 붙인다."""
        return (SECURITY_PAIRS.get((self.level, self.open_flag))
                or f"{level_name(self.level)}(화면에 없는 짝 {self.level}/{self.open_flag})")

    @property
    def classified(self) -> bool:
        """기밀 등급(``CLASSIFIED_LEVELS``)인가."""
        return self.level in CLASSIFIED_LEVELS

    @property
    def ask_before_ai(self) -> bool:
        """글자를 대화로 들이기 전에 사람에게 물어야 하나 — 기밀이거나 핵심기술 문서다."""
        return self.classified or self.core


def level_name(level: str) -> str:
    """등급 글자(``1A`` …)의 이름 — 공개 짝과 무관한 앞 이름(기밀 · 사외비A · 사외비B · 일반). 모르는 글자는 그대로."""
    return next((n.split("/")[0] for (lv, _), n in SECURITY_PAIRS.items() if lv == level), level)


@dataclass(frozen=True)
class Doc:
    """목록의 문서 한 줄. ``object_id`` 가 여는 열쇠다. 시각 · 크기는 ECM 이 준 글자 그대로다."""
    object_id: str
    doc_id: str
    name: str
    ext: str
    size: str
    version: str
    registered: str
    modified: str
    folder_path: str
    folder_id: str
    owner: str
    security: str
    locked_by: str
    cabinet_name: str = ""     # 그 문서가 든 문서함 — 공유받은 · 최근 활용 목록처럼 여러 문서함이 섞인 목록에서 쓴다
    shared_by: str = ""        # 공유받은 목록 — 공유한 사람 · 받은 역할(R · S · V)
    role: str = ""
    requester: str = ""        # 권한 받은 · 보낸 요청 목록 — 요청한 사람 · 요청한 날 · 처리 상태(MS_WORKFLOW_STATUS 그대로)
    requested: str = ""
    request_status: str = ""
    deleted: str = ""          # 휴지통 — 지운 날
    used: str = ""             # 최근 활용 — 마지막으로 쓴 때


@dataclass(frozen=True)
class Version:
    """판 이력의 한 줄 — ``object_id`` 는 그 판의 열쇠(read · open 이 받는다). 지금 판이면 ``current``."""
    object_id: str
    label: str
    current: bool
    creator: str
    dept: str
    created: str
    desc: str              # 수정 내용 — 판을 올린 이가 적은 한 줄
    size: str


@dataclass(frozen=True)
class Hit:
    """전사 검색의 한 줄 — ``object_id`` 는 지금 판의 열쇠다(read · open 이 받는다)."""
    object_id: str
    title: str
    ext: str
    author: str
    dept: str
    security: str
    modified: str


@dataclass(frozen=True)
class SearchQuery:
    """전사 검색의 칸 — 상세검색 화면의 칸과 같다. 빈 칸은 안 거른다."""
    title: str = ""
    any_word: bool = False   # 제목 낱말 여럿 가운데 하나만 맞아도(OR) — 기본은 다 맞아야(AND)
    text: str = ""           # 본문 낱말
    owner: str = ""          # 소유자 이름
    creator: str = ""        # 등록자 이름
    since: str = ""          # YYYY-MM-DD
    until: str = ""
    date_field: str = "modified"
    file_ext: str = ""       # xlsx 따위
    security: tuple[str, ...] = ()
    scope: str = "mine"      # company · mine


@dataclass(frozen=True)
class Cabinet:
    """부서 · 프로젝트 문서함 하나 — ``key`` 를 ``list --cabinet`` 에 준다."""
    key: str
    name: str
    kind: str              # 부서 · 프로젝트
    own: bool              # 제 부서 문서함인가


@dataclass(frozen=True)
class Folder:
    """문서함 안의 폴더 하나 — ``id`` 를 ``register --folder`` 에, ``id`` 를 다시 ``folders --parent`` 에 준다."""
    cabinet: str
    id: str
    name: str
    has_sub: bool


@dataclass(frozen=True)
class Registered:
    """새 문서로 올린 결과 — 문서 열쇠 · 이름과, 그 문서함 목록에서 다시 읽은 판."""
    object_id: str
    title: str
    version: str           # 목록에서 다시 읽은 판 — 새 문서는 0.0 이다


@dataclass(frozen=True)
class DocState:
    """문서 하나의 속성 화면 한 번 읽기 — 판 · 잠금 · 보안등급 · 이름. 못 읽은 칸은 빈 글자 · ``None`` 이다."""
    version: str
    locked: bool | None    # 편집 잠금 — 못 읽으면 None
    lock_owner: str
    security: "Security | None"
    title: str


@dataclass(frozen=True)
class Grant:
    """문서에 걸린 역할 하나 — ``role`` 은 R(편집/복사/읽기/인쇄) · S(복사/읽기/인쇄) · V(읽기/인쇄) 따위, ``id`` 는 사람 열쇠(usr…)."""
    role: str
    id: str
    cls: str = "U"         # U 사람 · D 부서 · P 프로젝트
    name: str = ""
    dept: str = ""
    email: str = ""        # 메일 ID(@ 앞)
    employee: str = ""

    def label(self) -> str:
        """사람이 읽는 꼴 — 「이름/메일ID · 부서」."""
        return f"{self.name}/{self.email}" + (f" · {self.dept}" if self.dept else "")


@dataclass(frozen=True)
class Person:
    """ECM 이 아는 사람 하나 — ``id`` 가 권한 칸에 드는 열쇠다. 메일 ID · 사번은 메일 주소록의 그 사람과 같다."""
    id: str
    name: str
    dept: str
    dept_code: str
    email: str
    employee: str
    position: str = ""

    def label(self) -> str:
        """사람이 읽는 꼴 — 「이름/메일ID · 부서 · 직위」."""
        return f"{self.name}/{self.email}" + (f" · {self.dept}" if self.dept else "") + (f" · {self.position}" if self.position else "")


@dataclass(frozen=True)
class Organ:
    """ECM 조직도의 부서 하나 — ``code`` 를 ``org:<코드>`` 로 준다. ``members`` 는 바로 든 사람 수 · ``subs`` 는 바로 아래 부서 수."""
    code: str
    name: str
    upper: str
    cabinet: str
    members: int
    subs: int


class PropertyPage:
    """문서의 속성 화면 — 저장 몸이 실을 숨은 칸(``inputs``), 화면 스크립트의 갈래 값(``vars``), 권한 iframe 주소의 갈래 값(``frame``)."""

    def __init__(self, inputs: dict, vars_: dict, frame: dict):
        self.inputs, self.vars, self.frame = inputs, vars_, frame

    @classmethod
    def parse(cls, page: str) -> "PropertyPage":
        """속성 화면 HTML 에서 숨은 칸 · 스크립트 변수 · 요소 id · 권한 iframe 주소의 갈래 값을 읽어 한 판을 짓는다."""
        import html.parser

        inputs: dict[str, str] = {}

        class Inputs(html.parser.HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag == "input":
                    a = dict(attrs)
                    if a.get("id") and a["id"] not in inputs:
                        inputs[a["id"]] = a.get("value") or ""

            handle_startendtag = handle_starttag

        Inputs(convert_charrefs=True).feed(page)
        vars_: dict[str, str] = {}
        for name, value in PAGE_VAR.findall(page):
            vars_.setdefault(name, value)
        frame_match = ROLE_FRAME.search(page)
        frame = dict(urllib.parse.parse_qsl(html.unescape(frame_match.group(1)), keep_blank_values=True)) if frame_match else {}
        ids = set(ELEMENT_ID.findall(page))
        return cls(inputs, {**vars_, "__ids__": ids}, frame)

    def value(self, field: str) -> str:
        """저장 몸에 실을 숨은 칸 하나의 값 — 없어도 되는 칸이 없으면 화면이 싣는 ``ABSENT_FIELD``, 그 밖의 칸이 없으면 ``EcmError``."""
        if field in self.inputs:
            return self.inputs[field]
        if field in SAVE_OPTIONAL:
            return ABSENT_FIELD
        raise EcmError(f"속성 화면에 {field} 칸이 없다 — ECM 화면이 바뀌었을 수 있어 권한을 안 보낸다. 사람이 화면의 「컨텐츠 속성」에서 한다")

    def security(self) -> "Security | None":
        """화면의 숨은 등급 칸 둘과 핵심기술 표시로 짓는 보안등급 — 등급 칸이 없거나 모르는 값이면 None."""
        level = self.security_level()
        if not any(level == lv for lv, _ in SECURITY_PAIRS):
            return None
        return Security(level, self.inputs.get(OPEN_FIELD, "").strip(), self.vars.get(CORE_VAR) == "T")

    def security_level(self) -> str:
        """화면의 숨은 등급 칸(``SECURITY_FIELD``)이 든 글자 그대로 — 없으면 빈 글자."""
        return self.inputs.get(SECURITY_FIELD, "").strip()

    def has_element(self, element_id: str) -> bool:
        """화면에 그 id 의 요소가 있나."""
        return element_id in self.vars["__ids__"]

    def unmeasured(self) -> str:
        """이 손이 잰 문서의 꼴이 아니면 그 까닭 — 맞으면 빈 글자. 어긋난 자리는 ``unmeasured_part`` 가, 말은 ``unmeasured_reason`` 이 든다."""
        part = self.unmeasured_part()
        return unmeasured_reason(part, self.frame.get("lockOwnerName", "")) if part else ""

    def unmeasured_part(self) -> tuple[str, str, object] | None:
        """이 손이 잰 꼴과 어긋난 첫 자리 — (어디: frame · page · vars · check, 칸, 그 값) 또는 None. 권한 칸이 없으면 ("frame", "", "")."""
        if not self.frame:
            return ("frame", "", "")
        for where, have, measured in (("page", self.inputs, MEASURED_PAGE), ("vars", self.vars, MEASURED_VARS),
                                      ("frame", self.frame, MEASURED_FRAME)):
            for field, want in measured.items():
                if have.get(field) != want:
                    return (where, field, have.get(field))
        for element in UNMEASURED_CHECKS:
            if self.has_element(element):
                return ("check", element, "")
        return None


def unmeasured_reason(part: tuple[str, str, object], lock_owner: str) -> str:
    """잰 꼴과 어긋난 자리(``PropertyPage.unmeasured_part``)를 사람에게 할 까닭으로 옮긴다."""
    where, field, value = part
    if where == "frame" and not field:
        return "속성 화면에 권한 칸(roleAssignEdit)이 없다 — 이 문서의 권한을 바꿀 수 없는 사람이거나 화면이 바뀌었다"
    if where == "page":
        if field == "sViewStatus":
            return "이 문서의 속성을 고칠 수 없다(편집 화면이 아니다) — 소유자 · 공동 편집자만 권한을 바꾼다"
        return f"속성 화면의 {field} 가 {value!r} 다 — 소유자 바꾸기 · 승인 차례가 걸린 문서라 안 잰 꼴이다"
    if where == "vars":
        return f"핵심기술 · RAI 가 걸린 문서다({field}={value!r}) — 화면이 승인 차례를 더하므로 안 잰 꼴이다"
    if where == "frame":
        if field == "lockStatus":
            return f"문서가 편집으로 잠겨 있다({lock_owner or '누군가'}) — 편집완료 뒤에 준다"
        return f"집중보호 문서다({field}={value!r}) — 화면이 승인 대기 칸을 쓰므로 안 잰 꼴이다"
    return f"속성 화면에 체크 칸({field})이 있다 — 그 값을 싣는 꼴은 안 쟀다"


@dataclass(frozen=True)
class Ticket:
    """열기 첫 걸음의 답 — 에이전트에 보낼 세 값."""
    doc_id: str
    object_id: str
    file_name: str

    @property
    def ext(self) -> str:
        """받을 파일 이름의 확장자(점을 붙인 소문자)."""
        return pathlib.PurePath(self.file_name).suffix.lower()


@dataclass(frozen=True)
class Opened:
    """받은 파일을 연 결과 — 받은 파일 · 열기 표 · 그 확장자의 기본 앱 · 이번에 기본 앱을 적었나."""
    path: pathlib.Path
    ticket: Ticket
    progid: str            # 연 확장자의 기본 앱 — 사람이 고르는 창으로 갔으면 빈 글자일 수 있다
    app_written: bool      # 이번에 기본 앱을 적었나


@dataclass(frozen=True)
class ReadResult:
    """읽기 한 판의 결과 — 뽑은 글자 · 읽는 손의 한 줄 · 연 결과 · 그 창을 닫은 형편."""
    text: str
    summary: str           # 읽는 손이 낸 한 줄 — 글자 수 · 「글 밖」 셈
    opened: Opened
    window: str            # closed · not-found · not-front · not-office


def url_from_env() -> str:
    """ECM 주소 — 환경변수 ``ECM_URL``, 비었으면 ``DEFAULT_URL``. 세션 파일 없이 주소만 드는 자리(이 손을 깔린 자리에서 싣는 앱)도 이것을 부른다."""
    return os.environ.get("ECM_URL", "").strip() or DEFAULT_URL


def agent_docs_root() -> pathlib.Path:
    """에이전트가 받은 파일을 두는 자리 — 환경변수 ``ECM_DOCS_ROOT``, 비었으면 ``DEFAULT_DOCS_ROOT``(``DRM_PLACES_FILE``). 스킬
    drm-office-read 의 읽는 부품(``Get-EcmDocsRoot``)과 DRM 길잡이 훅이 같은 차례 · 같은 값 파일로 읽어 그 자리 밑의 파일을 등급 문
    밖에서 안 연다."""
    return pathlib.Path(os.environ.get(DOCS_ROOT_ENV, "").strip() or DEFAULT_DOCS_ROOT)


def session_path() -> pathlib.Path:
    """환경변수 ``MAILBOX_COOKIES`` 의 세션 파일 자리. 비었으면 ``SessionMissing`` — 자리는 스킬 ep-login 의 받는 손이 정한다."""
    raw = os.environ.get("MAILBOX_COOKIES", "").strip()
    if not raw:
        raise SessionMissing("세션 파일 자리를 안 받았다 — 받는 손이 남긴 자리를 --session 이나 MAILBOX_COOKIES 로 준다(스킬 ep-login)")
    return pathlib.Path(raw).expanduser()


def check_search(query: SearchQuery) -> SearchQuery:
    """전사 검색의 칸을 서버 없이 가린다 — 못 쓸 값이면 ``ArgsError``. 다 빈 판 · 꼴이 깨지는 글자 · 날짜 꼴 · 등급 · 범위."""
    words = {"제목": query.title, "본문": query.text, "소유자": query.owner, "등록자": query.creator, "꼴": query.file_ext}
    if not any(v.strip() for v in (query.title, query.text, query.owner, query.creator)):
        raise ArgsError("찾을 것(문서 이름 낱말 · --text · --owner · --creator)을 하나는 준다 — 다 비우면 전사의 모든 문서가 온다")
    bad = [k for k, v in words.items() if SEARCH_WORD_BAD.search(v)]
    if bad:
        raise ArgsError(f"{' · '.join(bad)} 칸에 따옴표 · 역빗금 · 중괄호는 못 쓴다 — 검색 몸의 꼴이 깨진다")
    for when in (query.since, query.until):
        if when and not DATE_TEXT.match(when):
            raise ArgsError(f"날짜는 YYYY-MM-DD 꼴이다: {when!r}")
    if bool(query.since) != bool(query.until):
        raise ArgsError("기간은 --since 와 --until 을 함께 준다(화면도 한쪽만은 안 거른다)")
    if query.date_field not in SEARCH_DATE_FIELDS:
        raise ArgsError(f"기간의 기준은 {' · '.join(SEARCH_DATE_FIELDS)} 다")
    if query.scope not in (SEARCH_COMPANY, SEARCH_MINE):
        raise ArgsError(f"범위(--scope)는 {SEARCH_COMPANY} · {SEARCH_MINE} 다")
    unknown = [lv for lv in query.security if lv not in {s for s, _ in SECURITY_PAIRS}]
    if unknown:
        raise ArgsError(f"보안등급은 {' · '.join(sorted({s for s, _ in SECURITY_PAIRS}))} 가운데서 준다: {unknown}")
    if query.security and query.scope == SEARCH_COMPANY:   # 쟀다 — 문서함 칸이 비면 등급 거르기는 늘 0 건이다(「없다」로 읽게 된다)
        raise ArgsError(f"보안등급 거르기는 --scope {SEARCH_MINE}(내 문서함들)에서만 선다 — 전사 범위에서는 서버가 늘 0 건을 낸다")
    if query.file_ext and not query.file_ext.isalnum():
        raise ArgsError(f"꼴은 확장자 하나(xlsx 따위)다: {query.file_ext!r}")
    return query


def check_search_page(page: int, per_page: int) -> None:
    """전사 검색의 쪽 번호 · 쪽마다 건수를 가린다 — 범위 밖이면 ``ArgsError``."""
    if page < 1 or not 1 <= per_page <= SEARCH_PER_PAGE_MAX:
        raise ArgsError(f"쪽은 1 부터 · 쪽마다 건수는 1 ~ {SEARCH_PER_PAGE_MAX}")


def grants_key(grants) -> tuple[str, ...]:
    """권한 명단의 지문 — 줄마다 「역할:사람 열쇠」 를 늘어놓은 차례 없는 모습. 미리 본 뒤 바뀌었나 · 보낸 뒤 바란 대로인가를 다 이것으로 견준다."""
    return tuple(sorted(f"{g.role}:{g.id}" for g in grants))


def outside_roles(grants) -> list:
    """권한 셋(편집 · 복사 · 읽기)의 사람 줄 밖의 역할 — 이 손이 주고 거두지 않고, 그런 줄이 걸린 문서의 저장은 안 잰 꼴이다."""
    return [g for g in grants if g.role not in ACCESS_ROLES or g.cls != "U"]


def spec_kind(spec: str) -> tuple[str, str]:
    """사람 말 하나를 (갈래, 값)으로 가른다 — 「org:」 뒤가 부서 코드면 ``SPEC_CODE``, 부서 이름이면 ``SPEC_ORGAN``(값은 「org:」 를 뗀
    글), 아니면 ``SPEC_PERSON``(값은 말 그대로)."""
    if spec.startswith(ORG_PREFIX):
        value = spec[len(ORG_PREFIX):].strip()
        return (SPEC_CODE if DEPT_CODE.match(value) else SPEC_ORGAN), value
    return SPEC_PERSON, spec


def folder_name(name: str) -> str:
    """폴더 이름 찾기에 줄 이름(일부) — 화면처럼 두 글자부터. 다듬은 이름을 낸다."""
    name = name.strip()
    if len(name) < NAME_MIN:
        raise ArgsError(f"폴더 이름은 {NAME_MIN} 글자부터 찾는다(화면과 같다)")
    return name


def refuse_box_with_place(box: str, cabinet: str, folder: str) -> None:
    """왼쪽 메뉴의 목록(``--box``)은 문서함 · 폴더와 함께 안 받는다 — 그 목록은 문서함을 가리지 않는다."""
    if box and (cabinet or folder):
        raise ArgsError("--box 는 --cabinet · --folder 와 함께 안 받는다 — 왼쪽 메뉴의 그 목록은 문서함을 가리지 않는다")


def person_name(name: str) -> str:
    """사람 찾기에 줄 이름 — 화면의 checkValue 처럼 두 글자부터. 다듬은 이름을 낸다."""
    name = name.strip()
    if len(name) < NAME_MIN:
        raise ArgsError(f"이름은 {NAME_MIN} 글자부터 찾는다(화면과 같다): {name!r}")
    return name


def organ_name(name: str) -> str:
    """부서 찾기에 줄 이름(일부) — 두 글자부터. 다듬은 이름을 낸다."""
    name = name.strip()
    if len(name) < NAME_MIN:
        raise ArgsError(f"부서 이름은 {NAME_MIN} 글자부터 찾는다: {name!r}")
    return name


def check_person_spec(spec: str) -> None:
    """권한에 줄 사람 말 하나를 서버 없이 가린다 — 「org:코드|부서 이름」 · 「이름[/메일ID|/메일 주소]」. 이름 없이 주소만 준 말은
    ECM 이 못 찾는다(이름으로만 찾는다). 못 쓸 말이면 ``ArgsError``."""
    kind, value = spec_kind(spec)
    if kind == SPEC_ORGAN:
        organ_name(value)
    if kind != SPEC_PERSON:
        return
    name, _, _ = spec.partition("/")
    if "@" in name:
        raise ArgsError(f"「{spec}」 — 메일 주소만으로는 ECM 이 사람을 못 찾는다(이름으로만 찾는다). 「이름/메일 주소」 로 준다 — 이름은 "
                        "스킬 company-directory 의 find 가 낸다")
    person_name(name)


def _dept_code(value: str) -> str:
    """부서 코드의 꼴을 가려 다듬은 값을 낸다 — 아니면 ``ArgsError``."""
    value = value.strip()
    if not DEPT_CODE.match(value):
        raise ArgsError(f"부서 코드 꼴이 아니다: {value!r} — 조직 찾기가 낸 코드를 준다")
    return value


def check_title(title: str) -> str:
    """등록할 이름(확장자 뺀) — 화면의 addFile 이 막는 것을 먼저 막는다. 다듬은 이름을 낸다."""
    title = title.strip()
    if not title or title.lower() == "null":
        raise ArgsError("등록할 이름이 비었다")
    if TITLE_BAD.search(title):
        raise ArgsError('이름에 \\ / : * ? " < > | ` % # 와 작은따옴표는 못 쓴다 — # 는 서버가 말없이 떼어 다른 이름으로 선다')
    if len(title) > TITLE_MAX or sum(3 if ord(c) > 255 else 1 for c in title) > TITLE_BYTES_MAX:
        raise ArgsError(f"이름이 길다 — {TITLE_MAX} 자(한글은 3 바이트로 세어 {TITLE_BYTES_MAX}) 까지")
    return title


def _object_id(value: str) -> str:
    """문서 열쇠(16 자리 hex)의 꼴을 가려 다듬은 값을 낸다 — 아니면 ``ArgsError``."""
    value = value.strip()
    if not OBJECT_ID.match(value):
        raise ArgsError(f"문서 열쇠(MS_OBJECT_ID · 16 자리 hex)가 아니다: {value!r}")
    return value


def cabinet_key(value: str) -> str:
    """문서함 열쇠(cab…)의 꼴을 가린다 — 아니면 ``ArgsError``."""
    if not CABINET_ID.match(value):
        raise ArgsError(f"문서함 열쇠(cab…)가 아니다: {value!r} — cabinets 가 낸 열쇠를 준다")
    return value


def folder_key(value: str) -> str:
    """폴더 열쇠(fdr…)의 꼴을 가린다 — 아니면 ``ArgsError``."""
    if not FOLDER_ID.match(value):
        raise ArgsError(f"폴더 열쇠(fdr…)가 아니다: {value!r} — folders 가 낸 열쇠를 준다")
    return value


def _loose(text: str) -> str:
    """이름 일부를 견줄 꼴 — 대소문자 · 빈칸을 안 가린다(「월간보고」 · 「월간 보고」가 같다)."""
    return re.sub(r"\s+", "", text).casefold()


def path_word(path) -> str:
    """폴더의 이름 경로를 화면의 꼴(「기획 > 보고」)로."""
    return f" {FOLDER_SEP} ".join(path)


def token(*parts) -> str:
    """확인 열쇠 — 미리 보기가 사람에게 보인 판의 지문. 같은 판이면 같은 열쇠가 다시 선다."""
    raw = json.dumps(parts, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:TOKEN_LENGTH]


def property_value(page: str, label: str) -> str:
    """문서 정보 화면의 표에서 머리 칸 ``label`` 아래 값 — 머리 줄 하나 · 값 줄 하나의 표다. 없으면 빈 글자."""
    for table in re.findall(r"<table\b.*?</table>", page, re.S | re.I):
        heads = [re.sub(r"<[^>]+>|\s+", " ", h).strip() for h in re.findall(r"<th\b[^>]*>(.*?)</th>", table, re.S | re.I)]
        if label not in heads:
            continue
        body = re.search(r"<tbody\b[^>]*>(.*?)</tbody>", table, re.S | re.I)
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", body.group(1) if body else "", re.S | re.I)
        index = heads.index(label)
        if index < len(cells):
            return html.unescape(re.sub(r"<[^>]+>", "", cells[index])).strip()
    return ""


ORG_PREFIX = "org:"
SPEC_CODE, SPEC_ORGAN, SPEC_PERSON = "code", "organ", "person"   # 사람 말의 갈래 — spec_kind 가 낸다


@dataclass(frozen=True)
class PropChange:
    """바꿀 속성 — ``None`` 인 칸은 그대로 둔다. ``tags`` 는 태그 전체(뒤의 모습) · ``due`` 는 YYYY-MM-DD."""
    title: str | None = None
    tags: tuple[str, ...] | None = None
    due: str | None = None

    def empty(self) -> bool:
        """바꿀 칸이 하나도 없나."""
        return self.title is None and self.tags is None and self.due is None
