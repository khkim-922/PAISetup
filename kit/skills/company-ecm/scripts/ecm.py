"""사내 문서함(ECM)에서 문서를 찾고 읽고, 사람이 확인한 한 편은 편집해 다음 판으로 올리거나 새 문서로 올리는 손. 표준 라이브러리만 쓴다(곁의
``default_app.py`` · ``close_view.ps1`` · ``close_acrobat.ps1`` · ``checkin_window.ps1`` 을 함께 쓴다).

무엇을 하나
    문서함의 목록 · 찾기 · 건수를 받는다 — 내 문서함, 그리고 그 사람이 볼 수 있는 부서 · 프로젝트 문서함(``Ecm.cabinets`` ·
    ``Ecm.list(cabinet=…)`` · ``Ecm.count``). 문서 하나를 PC 의 ECM 에이전트로 받아 보기로 열고(``open_document``), 에이전트가 띄운
    창(오피스 · Acrobat)을 닫은 뒤 받은 파일의 글자를 스킬 drm-office-read 의 읽는 손으로 뽑는다(``read_document``).

    편집은 화면과 같은 차례다 — ``edit_document`` 가 서버에서 잠그고 에이전트로 읽기 쓰기로 열며, 고친 뒤 ``checkin_document`` 가
    그 문서만 저장해 닫고 에이전트의 편집완료 창에서 **늘 다음 판**을 골라 수정 내용과 함께 올린 뒤 문서 정보의 최종 버전이
    바뀌었나 본다. 새 문서는 ``register_document`` 가 화면의 「컨텐츠 등록」 차례로 올린다 — 그 폴더에 같은 이름이 있나 묻고, 에이전트가
    파일을 서버 임시 자리에 올리고, 등록한 뒤 목록에서 다시 읽어 폴더 · 보안등급이 고른 값인가 본다. 바꾸는 요청은 편집 열기
    (``Ecm.checkout``)와 등록 화면의 두 POST(``Ecm._post`` — 같은 이름 찾기 · 등록)만 짓는다 — 그 밖의 바꾸는 꼴(올리기 요청 · 편집취소 ·
    지우기)과 잰 꼴 밖의 주소는 서버에 닿기 전에 ``Refused`` 로 막는다. 왜 이렇게 짓나는 결정 0223 · 0224 가 든다.

    에이전트는 받은 파일을 그 확장자의 기본 앱으로 **화면에 띄운다.** 그래서 이 손은 사람이 보는 대화에서만 쓰고, 편집은 사람이
    그 문서를 확인한 뒤에만 부른다 — 편집 열기는 동료도 쓰는 문서를 서버에서 잠근다.

어떻게 부르나::

        import ecm

        box = ecm.Ecm.from_env()                         # 세션 파일에 ECM 쿠키가 없으면 SessionMissing
        docs = box.list(search="보고서")                  # 내 문서함 — Doc 목록
        dept = box.cabinets()[0]                          # 제 부서 문서함이 맨 앞
        docs = box.list(search="계획", cabinet=dept.key)  # 부서 문서함
        got = ecm.read_document(box, ecm.Agent.from_env(), docs[0].object_id)
        print(got.text)                                  # 글자 · got.summary 는 읽는 손의 한 줄(「글 밖」 셈)

        top = box.folders(dept.key)                       # 문서함의 폴더 한 층 — 아래는 folders(dept.key, top[0].id)
        new = ecm.register_document(box, ecm.Agent.from_env(), path, cabinet=dept.key, folder=top[0].id,
                                    security="2A", open_flag="F")   # 보안 짝은 사람이 확인한 값
        opened = ecm.edit_document(box, ecm.Agent.from_env(), docs[0].object_id)   # 잠그고 읽기 쓰기로 연다
        # … 오피스 COM 으로 opened.path 의 문서를 고친다(저장은 다음 걸음이 한다) …
        done = ecm.checkin_document(box, opened.path, docs[0].object_id, "고친 내용 한 줄")
        print(done.version_before, "→", done.version_after)

    명령줄은 ``python -X utf8 ecm.py [--session <세션 파일>] <명령>`` 이다 — ``session`` · ``cabinets`` · ``list`` · ``count`` ·
    ``version`` · ``open`` · ``read`` · ``edit`` · ``checkin`` · ``folders`` · ``register`` · ``default-app``. 각 명령의 인자는 ``--help`` 가 든다.

무엇을 내나
    목록은 ``Doc``, 문서함은 ``Cabinet``, 열기 · 편집 열기는 ``Opened``(받은 파일 경로 · 문서 표 · 기본 앱), 읽기는 ``ReadResult``,
    올리기는 ``CheckedIn``(앞 판 · 뒤 판 · 고른 판), 폴더는 ``Folder``, 새 문서는 ``Registered``(열쇠 · 이름 · 판)이다. 명령줄의 종료 값은 0 됨 · 1 실패(메시지 그대로 알린다) · 3 세션이 없거나
    끊겼다(스킬 ep-login 으로 다시 받는다) · 4 사람이 그 확장자의 기본 앱을 한 번 골라야 한다(메시지가 할 일을 든다). 갈래 예외는
    ``EcmError`` 아래에 선다 — ``SessionMissing`` · ``SessionExpired`` · ``Refused`` · ``AgentError`` · ``ReadError``, 그리고
    ``default_app.DefaultAppNeeded``.

받은 파일은 어떻게 되나
    에이전트가 ``<받는 자리>\\<계정>\\VIEW\\<시각 번호>\\``(보기) · ``…\\CHECKOUT\\<시각 번호>\\``(편집)에 둔 파일은 **지우지도
    옮기지도 않는다.** 그 폴더는 에이전트의 것이고(ECM 화면에서 사람이 열어도 같은 자리에 같은 꼴로 쌓인다), 파일은 DRM 에 감긴 채라
    그 PC 의 오피스 밖에서는 안 열린다. 비우는 일은 에이전트의 정리 프로그램 몫이다. 읽는 손이 뽑은 평문은 이 손이 지은 임시
    폴더에 잠시 놓였다가 글자를 읽자마자 그 폴더째 지운다 — 평문은 디스크에 남지 않고 부르는 쪽에만 간다.

환경변수(``from_env``)
    ``ECM_URL``           ECM 주소 — ``…/ECM`` 까지                         기본 ``http://swpecm.posco.net:7091/ECM``
    ``MAILBOX_COOKIES``   세션 파일(Playwright 저장 상태) — ``--session`` · 인자를 안 줄 때만. 기본 자리는 없다 — 세션
                          파일의 자리는 그것을 남기는 받는 손(스킬 ep-login)이 정하고, 부르는 쪽이 그 자리를 넘긴다
    ``ECM_AGENT_URL``     ECM 에이전트 웹소켓                               기본 ``ws://localhost:8383/``
    ``ECM_DOCS_ROOT``     에이전트가 받은 파일을 두는 자리                   기본 ``C:\\Rayful2_Docs``
    ``ECM_DRM_READER``    글자를 뽑는 손                                     기본 ``~/.claude/skills/drm-office-read/scripts/read-drm.ps1``
    문서함 열쇠 · 계정은 환경변수로 받지 않는다 — 그 사람의 ECM 메인 화면과 에이전트의 폴더에서 읽는다.

사내 ECM 에서 잰 것 — 어기면 조용히 망가진다
    * 세션은 ``swpecm.posco.net`` 쿠키(``JSESSIONID``)다. 세션 파일에는 다른 호스트의 쿠키도 들어 있다 — 그 호스트에 맞는
      쿠키만 싣는다(도메인 · 경로 · 시한 · ``secure``). 세션 없이 열면 ``302 → /ECM/logout.jsp`` 가 온다 — 리다이렉트는 따라가지
      않고 「끊겼다」로 읽는다(따라가면 쿠키가 다른 주소로 실린다)
    * 목록 · 건수 · 열기는 다 ``GET /ECM/ajaxAction.do?ServiceName=…`` 이다. 답은 ``text/xml`` 로 오지만 몸은 앞에 빈 줄이 붙은
      JSON 이다. 성공은 ``MB_RTN_VALUE``, 까닭은 ``MS_MSG_CODE`` · ``MS_MSG_DESC``
    * 목록은 ``DocList-service&getDocList=true`` 의 ``ML_DOC_LIST[]``, 건수는 ``&getDocCount=true`` 의 ``MI_DOC_COUNT`` 다. 내
      문서함은 ``formId=F_LIST_MYDOC`` · 화면의 기본은 ``docCntPerPage=15`` · ``searchPeriod=6M`` · ``fileType=ALL_FORMAT`` ·
      ``sortDirection=desc``. 기간 ``searchPeriod`` 는 화면 기간 필터의 일곱 값(``1M`` · ``6M`` · ``12M`` · ``24M`` · ``36M`` ·
      ``60M`` · ``ALL``)만 뜻대로 선다 — ``1Y`` 는 ``MSG_E_0056`` 으로 거절되고, ``1W`` 는 거절 없이 1M 보다 많은 건수가 온다
    * 부서 · 프로젝트 문서함은 화면 왼쪽 「내 부서 컨텐츠」와 같은 ``formId=F_LIST_MYDEPT`` · ``listKey=<문서함 열쇠>_<문서함 열쇠>`` 다.
      그 사람의 문서함은 메인 화면의 ``<option id="MENU_DEPT|MENU_PROJECT" value='cab…'>이름</option>`` 이, 제 부서는
      ``s_UserDeptCabinetId`` 가 든다. 부서 문서는 내 문서함 찾기에 안 걸린다
    * 열기는 두 걸음이다 — ``OpenContents-service&view=true&MS_OBJECT_ID=<16 hex>&formId=F_LIST_MYDOC`` 가 ``MS_DOC_ID`` ·
      ``MS_OBJECT_ID`` · ``MS_FILE_NAME`` 을 주고(파일 바이트는 안 준다 · 부서 문서도 같은 ``formId`` 로 선다), 그 값을 에이전트
      웹소켓에 한 줄 ``Download␈<MS_DOC_ID>␈<MS_OBJECT_ID>␈VIEW␈<MS_FILE_NAME>␈ECM``(``␈`` = ``\\x08``)로 보내면 ``OK`` 가 온다.
      에이전트가 파일을 새 폴더에 받고 기본 앱으로 연다
    * 편집 열기는 ``CheckOutCheckIn-service&checkout=true&MS_OBJECT_ID=<16 hex>`` 가 서버에서 잠그고 같은 세 값을 준다(``MB_RTN_VALUE``
      가 참이면 실패 코드가 같이 와도 선다). 줄의 셋째 값이 ``EDIT_NOCHECKIN`` 이면 에이전트가 ``CHECKOUT`` 아래에 받아 읽기 쓰기로
      연다. 받은 이름 끝에 열쇠 · 계정이 한 번 더 붙을 수 있다 — 이름을 짓지 않고 새로 생긴 파일을 집는다
    * 편집완료 창은 **오피스 프로세스가 끝나야** 뜬다(문서를 닫기만 해서는 안 뜬다). 창 속은 웹 화면이고 판 라디오
      ``choice_version`` 의 기본은 지금 판(덮어쓰기)이다 — 마지막 값이 다음 판이다. 수정 내용 칸은 ``version_desc`` · 저장은 그 화면의
      ``fn_save()`` · 올리기는 에이전트가 한다. 판은 문서 정보 화면(``docProperty_simple.do?ServiceName=DocPropertyHtml-service&basicinfo=true
      &DOCID=<16 hex>&getType=user``)의 「최종 버전」 칸이 든다
    * 폴더 나무는 ``GetSubNaviMenu-service&menuType=<MENU_DEPT|MENU_PROJECT>&upperKey=<문서함>`` (문서함 바로 아래) ·
      ``menuType=F_LIST_FOLDER&upperKey=<문서함>_<폴더>`` (폴더 아래)다. 답 ``ML_MENU_LIST[]`` 의 ``MS_MENU_ID`` 가 ``<문서함>_<폴더>``,
      ``MS_HAS_SUB`` 가 아래 폴더 수다. ``upperKey`` 에 폴더 열쇠만 주면 「폴더 경로를 조회하는데 실패」가 온다
    * 새 문서 등록은 화면의 「컨텐츠 등록」 저장과 같다 — ① ``POST ajaxAction.do?ServiceName=CheckDuplicatedDoc-service&checkDup=true``
      (몸 ``folderID`` · ``title`` · ``fileExt``)가 같은 이름을 ``ML_DUPLICATED_LIST`` 로 낸다 ② 에이전트 웹소켓에 한 줄
      ``uploadfilecreatedoc␈contentName_1|<PC 경로>`` 를 보내면 에이전트가 파일을 ``EcmUploadCreateServlet`` 으로 올리고
      ``{"LISTID","SERVERFILE","SERVERPATH":"/WAS/ECMTEMP/<uuid>.<확장자>"}`` 를 답한다 ③ ``POST ajaxAction.do?isHTML=T`` 의 몸이
      ``register=register`` · ``ServiceName=RegisterContents-service`` · 파일 줄 XML(``fileList``) · ``ecm_folder_id`` ·
      ``ecm_security_level`` · ``ecm_open_flag`` 따위다 — 화면처럼 칸마다 인코딩하지 않고 이어 붙이고, 이름만 ``encodeURIComponent``
      한다. 답의 ``MS_OBJECT_ID`` 가 새 문서 열쇠이고 판은 0.0 이다. 보안 짝은 화면의 단추 여섯(``SECURITY_PAIRS``)뿐이다.
      감긴 파일도 그대로 올라가고 받은 문서는 감긴 채다. 화면은 설정에 따라 올린 로컬 파일을 지우지만(``filedelete``) 이 손은 안 지운다
    * ⚠ 같은 서비스 모음에 편집취소 · 올리기 요청 · 지우기가 있다 — 이 손은 짓지 않고, 지으려 하면 서버에 닿기 전에 막는다. 잰 꼴 밖의
      서비스 · 칸 · 값도 같이 막는다(닫힌 목록 ``READS`` · 편집 열기 문 ``_guard_edit``)
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import hashlib
import html
import json
import logging
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import default_app  # noqa: E402 — 곁의 파일이다

DEFAULT_URL = "http://swpecm.posco.net:7091/ECM"
DEFAULT_AGENT = "ws://localhost:8383/"
DEFAULT_DOCS_ROOT = r"C:\Rayful2_Docs"
DEFAULT_READER = "~/.claude/skills/drm-office-read/scripts/read-drm.ps1"
CLOSE_SCRIPT = pathlib.Path(__file__).resolve().parent / "close_view.ps1"
ACROBAT_CLOSE_SCRIPT = pathlib.Path(__file__).resolve().parent / "close_acrobat.ps1"
CHECKIN_SCRIPT = pathlib.Path(__file__).resolve().parent / "checkin_window.ps1"

HTTP_TIMEOUT = 30.0
AGENT_TIMEOUT = 60.0      # 에이전트가 OK 를 낼 때까지
FILE_TIMEOUT = 120.0      # OK 뒤 받은 파일이 다 생길 때까지
WINDOW_WAIT = 30.0        # 받은 파일을 띄운 창이 오피스에 잡힐 때까지
CHECKIN_WAIT = 60.0       # 오피스가 끝난 뒤 에이전트의 편집완료 창이 뜰 때까지
VERSION_WAIT = 60.0       # 편집완료를 누른 뒤 문서 정보의 최종 버전이 바뀔 때까지
VERSION_POLL = 3.0
FIND_ONLY_DESC = "find-only"   # 찾기만 할 때의 자리 글 — 「-」 하나는 PowerShell 이 인자 이름으로 읽어 부름이 진다
READ_TIMEOUT = 600.0      # 읽는 손 한 판
POLL = 0.5

# 명령줄의 종료 값 — 머리말 「무엇을 내나」
EXIT_OK, EXIT_FAIL, EXIT_SESSION, EXIT_DEFAULT_APP = 0, 1, 3, 4

AJAX = "/ajaxAction.do"
MAIN_PAGE = "/jsp/main/ecmMain.jsp"
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
# 읽기로 잰 요청 — 서비스 이름 → (참이어야 하는 갈래 칸 하나, 실을 수 있는 칸). 닫힌 목록이라 새 꼴은 읽기임을 잰 뒤 여기 더해야 묻는다
READS = {
    "DocList-service": (("getDocList", "getDocCount"),
                        {"isHTML", "formId", "listKey", "searchValue", "pageNumber", "docCntPerPage", "searchPeriod",
                         "wfStatusType", "fileType", "orderBy", "sortDirection", "isIncludeCntQry"}),
    "OpenContents-service": (("view",), {"MS_OBJECT_ID", "formId"}),
}
READ_FORMS = (MY_DOCS, DEPT_DOCS)    # formId 로 잰 값
# 문서함을 바꾸는 요청 — 편집 열기와 새 문서 등록 둘만 짓는다. 읽기 길(guard)은 이것도 막고, Ecm.checkout · Ecm.register 만 그 꼴을 연다
EDIT_SERVICE, EDIT_FLAG = "CheckOutCheckIn-service", "checkout"
# 폴더 나무 — 문서함 열쇠 아래 첫 층(menuType = 문서함 갈래), 폴더 아래(menuType = F_LIST_FOLDER · upperKey = <문서함>_<폴더>)
FOLDER_SERVICE = "GetSubNaviMenu-service"
FOLDER_ROOT_TYPES = ("MENU_DEPT", "MENU_PROJECT")
FOLDER_TYPE = "F_LIST_FOLDER"
FOLDER_ID = re.compile(r"^fdr[0-9A-Fa-f]+$")
FOLDER_KEY = re.compile(r"^(cab[0-9A-Fa-f]+)_(fdr[0-9A-Fa-f]+)$")
# 등록 화면의 두 POST — 같은 이름 찾기(읽기)와 등록(바꾼다). 몸은 화면의 getData · checkDocDuplication 이 짓는 꼴 그대로다
DUP_QUERY = {"ServiceName": "CheckDuplicatedDoc-service", "checkDup": "true"}
REGISTER_QUERY = {"isHTML": "T"}
REGISTER_SERVICE = "RegisterContents-service"
REGISTER_ROW = "contentName_1"          # 화면이 첫 파일 줄에 붙이는 이름 — 에이전트 올림 · 등록 몸이 같은 이름으로 잇는다
AGENT_UPLOAD = "uploadfilecreatedoc"    # 에이전트가 파일을 서버 임시 자리(/WAS/ECMTEMP)에 올리고 그 이름을 JSON 으로 답한다
# 보안등급 · 공개 — 등록 화면의 단추 여섯이 짓는 짝만 받는다(기밀은 비공개만 · 일반은 공개만)
SECURITY_PAIRS = {("1A", "F"): "기밀", ("2A", "F"): "사외비A/비공개", ("2A", "T"): "사외비A",
                  ("2B", "F"): "사외비B/비공개", ("2B", "T"): "사외비B", ("3A", "T"): "일반"}
DOC_TYPE_GENERAL = "1"                  # 화면의 「컨텐츠 등록」이 기본으로 두는 문서 유형
DOC_STATUS_DRAFT = "0"
NO_DUE_DATE = "0001-01-01"
TITLE_MAX = 125                         # 화면의 addFile — 이름(확장자 뺀) 125 자 · 한글은 3 바이트로 세어 250 까지
TITLE_BYTES_MAX = 250
TITLE_BAD = re.compile(r'[\\/:*?"<>|`]')
SERVER_NAME = re.compile(r"^[/\w.\-]+$")   # 에이전트가 준 서버 임시 자리 · 파일 이름의 글자 — 몸의 칸을 가르는 & · = · + · % 가 없게
LIST_DEFAULTS = {"isHTML": "T", "formId": MY_DOCS, "wfStatusType": "", "fileType": "ALL_FORMAT", "orderBy": "",
                 "sortDirection": "desc"}
DEFAULT_PERIOD = "6M"
# 화면 기간 필터의 값 그대로 — 밖의 값은 MSG_E_0056 으로 거절되거나(1Y · 2Y) 거절 없이 틀린 목록이 온다(1W)
PERIODS = ("1M", "6M", "12M", "24M", "36M", "60M", "ALL")
DEFAULT_PER_PAGE = 15
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
CLOSE_EXIT = {0: "closed", 2: "not-found", 3: "not-front"}
# 보기를 거절한 코드 — 사람에게 서버 글 대신 할 일을 낸다. 권한이 없어 문서함 화면에도 안 보이던 문서가 이 코드였다
VIEW_DENIED = "MSG_E_0035"
OFFICE_BY_EXT = {".docx": "Word", ".doc": "Word", ".xlsx": "Excel", ".xls": "Excel", ".xlsm": "Excel",
                 ".pptx": "PPT", ".ppt": "PPT"}

log = logging.getLogger(__name__)


class EcmError(Exception):
    """ECM 일을 못 했다. 메시지가 사유다."""


class SessionMissing(EcmError):
    """세션 파일이 없거나 그 안에 ECM 호스트의 쿠키가 없다 — 스킬 ep-login 으로 받는다."""


class SessionExpired(EcmError):
    """ECM 이 세션을 안 받았다(``302 → /ECM/logout.jsp`` 따위) — 스킬 ep-login 으로 다시 받는다."""


class Refused(EcmError):
    """읽기로 잰 꼴 밖의 요청을 지었다 — 서버에 닿기 전에 막았다."""


class AgentError(EcmError):
    """PC 의 ECM 에이전트가 안 돌거나, 거절했거나, 받은 파일이 안 생겼다."""


class ReadError(EcmError):
    """받은 파일에서 글자를 못 뽑았다."""


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
    object_id: str
    title: str
    version: str           # 목록에서 다시 읽은 판 — 새 문서는 0.0 이다


@dataclass(frozen=True)
class Ticket:
    """열기 첫 걸음의 답 — 에이전트에 보낼 세 값."""
    doc_id: str
    object_id: str
    file_name: str

    @property
    def ext(self) -> str:
        return pathlib.PurePath(self.file_name).suffix.lower()


@dataclass(frozen=True)
class Opened:
    path: pathlib.Path
    ticket: Ticket
    progid: str            # 연 확장자의 기본 앱 — 사람이 고르는 창으로 갔으면 빈 글자일 수 있다
    app_written: bool      # 이번에 기본 앱을 적었나


@dataclass(frozen=True)
class ReadResult:
    text: str
    summary: str           # 읽는 손이 낸 한 줄 — 글자 수 · 「글 밖」 셈
    opened: Opened
    window: str            # closed · not-found · not-front · not-office


# ── 세션 ─────────────────────────────────────────────────────────────────

def session_path() -> pathlib.Path:
    """환경변수 ``MAILBOX_COOKIES`` 의 세션 파일 자리. 비었으면 ``SessionMissing`` — 자리는 스킬 ep-login 의 받는 손이 정한다."""
    raw = os.environ.get("MAILBOX_COOKIES", "").strip()
    if not raw:
        raise SessionMissing("세션 파일 자리를 안 받았다 — 받는 손이 남긴 자리를 --session 이나 MAILBOX_COOKIES 로 준다(스킬 ep-login)")
    return pathlib.Path(raw).expanduser()


def _domain_matches(host: str, domain: str) -> bool:
    domain = domain.lstrip(".").lower()
    return bool(domain) and (host == domain or host.endswith("." + domain))


def cookie_header(session_file: pathlib.Path, url: str, *, now: float | None = None) -> str:
    """세션 파일(Playwright 저장 상태)에서 ``url`` 에 실릴 쿠키만 골라 ``Cookie`` 머리 글로 낸다. 없으면 빈 글자."""
    if not session_file.exists():
        raise SessionMissing(f"세션 파일이 없다: {session_file} — 스킬 ep-login 으로 받는다")
    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SessionMissing(f"세션 파일이 깨졌다({exc}) — 스킬 ep-login 으로 다시 받는다") from exc
    cookies = data.get("cookies") if isinstance(data, dict) else None
    if not isinstance(cookies, list):
        raise SessionMissing(f"세션 파일에 쿠키 목록이 없다: {session_file} — 스킬 ep-login 으로 받는다")
    parts = urllib.parse.urlsplit(url)
    host, path, secure = (parts.hostname or "").lower(), parts.path or "/", parts.scheme == "https"
    now = time.time() if now is None else now
    picked = []
    for item in cookies:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        expires = item.get("expires", -1)
        if isinstance(expires, (int, float)) and expires not in (-1,) and 0 <= expires < now:
            continue
        cookie_path = item.get("path") or "/"
        if not _domain_matches(host, str(item.get("domain", ""))):
            continue
        if not (path == cookie_path or path.startswith(cookie_path.rstrip("/") + "/")):
            continue
        if item.get("secure") and not secure:
            continue
        picked.append((len(cookie_path), f"{item['name']}={item.get('value', '')}"))
    picked.sort(key=lambda p: -p[0])
    return "; ".join(text for _, text in picked)


class _Redirected(Exception):
    def __init__(self, location: str):
        super().__init__(location)
        self.location = location


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise _Redirected(newurl)


# ── 서버 ─────────────────────────────────────────────────────────────────

class Ecm:
    """ECM 서버 하나. 손은 다 읽기다 — ``_fetch`` 가 모든 요청을 ``guard`` 에 먼저 댄다."""

    def __init__(self, url: str = DEFAULT_URL, session_file=None, *, timeout: float = HTTP_TIMEOUT):
        match = re.match(r"^(https?://[^/?#]+)(/[^?#]*?)/?$", url.strip(), re.IGNORECASE)
        if not match or not match.group(2):
            raise EcmError(f"ECM 주소(…/ECM)가 아니다: {url!r}")
        self.server, self.context = match.group(1), match.group(2)
        self.timeout = timeout
        self.session_file = pathlib.Path(session_file).expanduser() if session_file else session_path()
        self._cookie = cookie_header(self.session_file, self.server + self.context + "/")
        if not self._cookie:
            raise SessionMissing(f"세션 파일에 {urllib.parse.urlsplit(self.server).hostname} 의 쿠키가 없다 — 스킬 ep-login 으로 받는다")
        self._opener = urllib.request.build_opener(_NoRedirect())

    @classmethod
    def from_env(cls) -> "Ecm":
        return cls(os.environ.get("ECM_URL", "").strip() or DEFAULT_URL, session_path())

    # 막기 — 이 판이 지은 주소를 다시 풀어 닫힌 목록에 댄다
    def guard(self, method: str, url: str) -> None:
        parts = urllib.parse.urlsplit(url)
        if method != "GET":
            raise Refused(f"읽기 길은 GET 만 보낸다: {method} {url}")
        if f"{parts.scheme}://{parts.netloc}".lower() != self.server.lower():
            raise Refused(f"ECM 서버 밖의 주소라 묻지 않는다: {url}")
        if parts.path == self.context + MAIN_PAGE and not parts.query:
            return
        if parts.path == self.context + AJAX and _is_folder_query(parts.query, url):
            return
        if parts.path == self.context + PROPERTY_PAGE:
            query = _single_query(parts.query, url)
            docid = query.pop("DOCID", "")
            if query == PROPERTY_QUERY and OBJECT_ID.match(docid):
                return
            raise Refused(f"문서 정보의 잰 꼴이 아니라 묻지 않는다: {url}")
        if parts.path != self.context + AJAX:
            raise Refused(f"읽기로 잰 주소가 아니라 묻지 않는다: {url}")
        pairs = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
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

    def _fetch(self, url: str, *, edit: bool = False) -> tuple[bytes, str]:
        if edit:
            self._guard_edit(url)
        else:
            self.guard("GET", url)
        request = urllib.request.Request(url, headers={"Cookie": self._cookie, "X-Requested-With": "XMLHttpRequest"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except _Redirected as exc:
            raise SessionExpired(f"ECM 이 세션을 안 받았다(→ {exc.location}) — 스킬 ep-login 으로 다시 받는다") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise SessionExpired(f"ECM 이 거절했다(HTTP {exc.code}) — 스킬 ep-login 으로 다시 받는다") from exc
            raise EcmError(f"ECM 이 HTTP {exc.code} 를 냈다: {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise EcmError(f"ECM 에 못 닿았다: {exc}") from exc

    # 편집 열기 하나만 여는 문 — 서비스 · 갈래 · 칸 하나(MS_OBJECT_ID)가 정확히 그 꼴일 때만 보낸다
    def _guard_edit(self, url: str) -> None:
        parts = urllib.parse.urlsplit(url)
        query = _single_query(parts.query, url)
        object_id = query.pop("MS_OBJECT_ID", "")
        if (f"{parts.scheme}://{parts.netloc}".lower() != self.server.lower() or parts.path != self.context + AJAX
                or query != {"ServiceName": EDIT_SERVICE, EDIT_FLAG: "true"} or not OBJECT_ID.match(object_id)):
            raise Refused(f"편집 열기의 잰 꼴이 아니라 묻지 않는다: {url}")

    def _post(self, query: dict, body: bytes) -> tuple[bytes, str]:
        """등록 화면의 두 POST 만 보낸다 — 질의가 같은 이름 찾기 · 등록의 꼴 그대로이고, 몸의 서비스가 그 질의와 맞을 때만."""
        fields = dict(urllib.parse.parse_qsl(body.decode("utf-8"), keep_blank_values=True))
        if not ((query == DUP_QUERY and set(fields) == {"folderID", "title", "fileExt"})
                or (query == REGISTER_QUERY and fields.get("ServiceName") == REGISTER_SERVICE
                    and fields.get("register") == "register")):
            raise Refused(f"등록 화면의 잰 꼴이 아니라 보내지 않는다: {query}")
        url = f"{self.server}{self.context}{AJAX}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, data=body, method="POST", headers={
            "Cookie": self._cookie, "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except _Redirected as exc:
            raise SessionExpired(f"ECM 이 세션을 안 받았다(→ {exc.location}) — 스킬 ep-login 으로 다시 받는다") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise SessionExpired(f"ECM 이 거절했다(HTTP {exc.code}) — 스킬 ep-login 으로 다시 받는다") from exc
            raise EcmError(f"ECM 이 HTTP {exc.code} 를 냈다: {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise EcmError(f"ECM 에 못 닿았다: {exc}") from exc

    def _ajax(self, service: str, flag: str, params: dict, *, edit: bool = False) -> dict:
        query = urllib.parse.urlencode({"ServiceName": service, flag: "true", **params})
        return _answer(*self._fetch(f"{self.server}{self.context}{AJAX}?{query}", edit=edit))

    def folders(self, cabinet: str, parent: str = "") -> list[Folder]:
        """문서함의 폴더 한 층 — ``parent`` 를 비우면 문서함 바로 아래, 주면 그 폴더(``fdr…``) 아래. 등록 화면의 폴더 나무와 같다."""
        if not CABINET_ID.match(cabinet):
            raise EcmError(f"문서함 열쇠(cab…)가 아니다: {cabinet!r} — cabinets 가 낸 열쇠를 준다")
        if parent and not FOLDER_ID.match(parent):
            raise EcmError(f"폴더 열쇠(fdr…)가 아니다: {parent!r} — folders 가 낸 열쇠를 준다")
        if parent:
            menu, upper = FOLDER_TYPE, f"{cabinet}_{parent}"
        else:
            kind = next((c.kind for c in self.cabinets() if c.key == cabinet), "")
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

    def duplicates(self, folder: str, title: str, ext: str) -> list[str]:
        """그 폴더에 같은 이름 · 확장자의 문서가 있나 — 화면이 등록 전에 묻는 같은 요청. 걸린 이름들을 낸다."""
        body = urllib.parse.urlencode({"folderID": folder, "title": title, "fileExt": ext}).encode("utf-8")
        data = _answer(*self._post(DUP_QUERY, body))
        return [f"{d.get('MS_DOC_TITLE', '')}.{d.get('MS_DOC_EXT', '')}" for d in data.get("ML_DUPLICATED_LIST") or []
                if str(d.get("MS_DOC_TITLE", "")).strip()]

    def register(self, *, folder: str, title: str, ext: str, size: int, server_path: str, server_file: str,
                 security: str, open_flag: str) -> str:
        """에이전트가 임시 자리에 올린 파일을 그 폴더의 새 문서로 등록한다 — 화면의 「컨텐츠 등록」 저장과 같은 몸. 문서 열쇠를 낸다."""
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
        body = "&".join(f"{k}={v}" for k, v in fields).encode("utf-8")
        data = _answer(*self._post(REGISTER_QUERY, body))
        object_id = str(data.get("MS_OBJECT_ID", ""))
        if not OBJECT_ID.match(object_id):
            raise EcmError(f"등록 답에 문서 열쇠가 없다 — ECM 화면에서 그 폴더를 본다: {data.get('MS_MSG_DESC', '')}")
        return object_id

    def session_alive(self) -> bool:
        """메인 화면이 200 이면 산 세션이다 — ``302 → logout.jsp`` 면 거짓. 문서를 건드리지 않는다."""
        try:
            self._fetch(f"{self.server}{self.context}{MAIN_PAGE}")
            return True
        except SessionExpired:
            return False

    @staticmethod
    def _list_params(search: str, period: str, folder: str, cabinet: str = "") -> dict:
        if period not in PERIODS:
            raise EcmError(f"기간(--period)은 화면의 값만 받는다: {' · '.join(PERIODS)} — 받은 값 {period!r}")
        if cabinet:
            if not CABINET_ID.match(cabinet):
                raise EcmError(f"문서함 열쇠(cab…)가 아니다: {cabinet!r} — cabinets 가 낸 열쇠를 준다")
            return {**LIST_DEFAULTS, "formId": DEPT_DOCS, "listKey": f"{cabinet}_{cabinet}", "searchValue": search,
                    "searchPeriod": period}
        return {**LIST_DEFAULTS, "listKey": folder, "searchValue": search, "searchPeriod": period}

    def cabinets(self) -> list["Cabinet"]:
        """그 사람이 볼 수 있는 부서 · 프로젝트 문서함 — 메인 화면이 든 목록 그대로. 제 부서가 맨 앞이다."""
        body, _ = self._fetch(f"{self.server}{self.context}{MAIN_PAGE}")
        page = body.decode("utf-8", "replace")
        own = OWN_CABINET.search(page)
        found, seen = [], set()
        for kind, key, name in CABINET_OPTION.findall(page):
            if key not in seen:
                seen.add(key)
                found.append(Cabinet(key, html.unescape(name).strip(), CABINET_KIND.get(kind.upper(), kind),
                                     bool(own and own.group(1) == key)))
        return sorted(found, key=lambda c: not c.own)

    def version(self, object_id: str) -> str:
        """문서 정보 화면의 「최종 버전」 — 판을 올린 뒤 다음 판이 섰나 본다. 못 읽으면 빈 글자."""
        object_id = _object_id(object_id)
        query = urllib.parse.urlencode({**PROPERTY_QUERY, "DOCID": object_id})
        body, _ = self._fetch(f"{self.server}{self.context}{PROPERTY_PAGE}?{query}")
        return property_value(body.decode("utf-8", "replace"), PROPERTY_VERSION)

    def checkout(self, object_id: str) -> "Ticket":
        """편집 열기 첫 걸음 — 서버가 그 문서를 이 사람 이름으로 잠근다. 에이전트에 넘길 세 값을 낸다.

        ``MB_RTN_VALUE`` 가 참이면 실패 코드(``MS_MSG_CODE``)가 같이 와도 선다 — 화면도 그 값만 본다."""
        object_id = _object_id(object_id)
        data = self._ajax(EDIT_SERVICE, EDIT_FLAG, {"MS_OBJECT_ID": object_id}, edit=True)
        name = urllib.parse.unquote(str(data.get("MS_FILE_NAME", "") or data.get("MS_CLIENT_FILE_NAME", "")))
        ticket = Ticket(str(data.get("MS_DOC_ID", "")), str(data.get("MS_OBJECT_ID", "")), name)
        if not (ticket.doc_id and ticket.object_id and ticket.file_name):
            raise EcmError("편집 열기 답에 MS_DOC_ID · MS_OBJECT_ID · 파일 이름이 다 없다 — ECM 화면에서 그 문서를 「편집취소」한다")
        return ticket

    def list(self, *, search: str = "", page: int = 1, per_page: int = DEFAULT_PER_PAGE, period: str = DEFAULT_PERIOD,
             folder: str = "", cabinet: str = "") -> list[Doc]:
        """문서함의 한 쪽 — 새것부터. 비우면 내 문서함, ``cabinet`` 이면 그 부서 · 프로젝트 문서함(``cabinets`` 의 열쇠).
        ``folder`` 는 내 문서함 목록 줄의 ``folder_id``."""
        if page < 1 or per_page < 1:
            raise EcmError("쪽 번호 · 쪽마다 건수는 1 이상이다")
        params = {**self._list_params(search, period, folder, cabinet), "pageNumber": str(page),
                  "docCntPerPage": str(per_page)}
        data = self._ajax("DocList-service", "getDocList", params)
        rows = data.get("ML_DOC_LIST") or []
        log.info("목록 %d 건 (쪽 %d)", len(rows), page)
        return [_doc(row) for row in rows if isinstance(row, dict)]

    def count(self, *, search: str = "", period: str = DEFAULT_PERIOD, folder: str = "", cabinet: str = "") -> int:
        params = {**self._list_params(search, period, folder, cabinet), "isIncludeCntQry": "T"}
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


def _answer(body: bytes, kind: str) -> dict:
    """ECM 의 답(앞에 빈 줄이 붙은 JSON)을 푼다 — ``MB_RTN_VALUE`` 가 참이 아니면 그 까닭으로 진다."""
    charset = (re.search(r"charset=([\w-]+)", kind, re.IGNORECASE) or [None, "utf-8"])[1]
    try:
        data = json.loads(body.decode(charset).strip())
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


def _is_folder_query(query: str, url: str) -> bool:
    """폴더 나무 한 층의 잰 꼴인가 — 문서함 바로 아래(MENU_DEPT · MENU_PROJECT + cab…) 또는 폴더 아래(F_LIST_FOLDER + cab…_fdr…)."""
    q = _single_query(query, url)
    if q.get("ServiceName") != FOLDER_SERVICE or set(q) != {"ServiceName", "menuType", "upperKey"}:
        return False
    if q["menuType"] in FOLDER_ROOT_TYPES:
        return bool(CABINET_ID.match(q["upperKey"]))
    return q["menuType"] == FOLDER_TYPE and bool(FOLDER_KEY.match(q["upperKey"]))


def _size_label(size: int) -> str:
    """화면의 byteToKB — 등록 몸의 크기 칸은 「15KB 」 꼴이다(끝에 빈칸 하나)."""
    if size <= 0:
        return "0KB "
    return f"{max(1, round(size / 1024)):,}KB "


def check_title(title: str) -> str:
    """등록할 이름(확장자 뺀) — 화면의 addFile 이 막는 것을 먼저 막는다. 다듬은 이름을 낸다."""
    title = title.strip()
    if not title or title.lower() == "null":
        raise EcmError("등록할 이름이 비었다")
    if TITLE_BAD.search(title):
        raise EcmError('이름에 \\ / : * ? " < > | ` 는 못 쓴다')
    if len(title) > TITLE_MAX or sum(3 if ord(c) > 255 else 1 for c in title) > TITLE_BYTES_MAX:
        raise EcmError(f"이름이 길다 — {TITLE_MAX} 자(한글은 3 바이트로 세어 {TITLE_BYTES_MAX}) 까지")
    return title


def _single_query(query: str, url: str) -> dict:
    """질의를 칸 → 값으로 푼다. 같은 칸이 두 번 들면 막는다 — 서버는 첫 값을, 견주는 쪽은 끝 값을 읽어 다른 요청이 나간다."""
    pairs = urllib.parse.parse_qsl(query, keep_blank_values=True)
    if len(pairs) != len({k for k, _ in pairs}):
        raise Refused(f"같은 칸이 두 번 든 주소라 묻지 않는다: {url}")
    return dict(pairs)


def _object_id(value: str) -> str:
    value = value.strip()
    if not OBJECT_ID.match(value):
        raise EcmError(f"문서 열쇠(MS_OBJECT_ID · 16 자리 hex)가 아니다: {value!r}")
    return value


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


def _doc(row: dict) -> Doc:
    def get(*names: str) -> str:
        for name in names:
            value = row.get(name)
            if value not in (None, ""):
                return str(value)
        return ""
    return Doc(get("MS_OBJECT_ID"), get("MS_DOC_ID"), get("MS_OBJECT_NAME"), get("MS_DOC_EXTENSION"), get("MS_FILE_SIZE"),
               get("MS_DOC_VERSION"), get("MS_REG_DATE"), get("MS_MODIFY_DATE_EXT", "MS_MODIFY_DATE"), get("MS_FOLDER_PATH"),
               get("MS_FOLDER_ID"), get("MS_OWNER_NAME"), get("MS_SECURITY_LEVEL"), get("MS_LOCK_USER_ID"))


# ── 에이전트 ─────────────────────────────────────────────────────────────

def _ws_frame(payload: bytes, opcode: int) -> bytes:
    head = bytes([0x80 | opcode])
    size = len(payload)
    if size < 126:
        head += bytes([0x80 | size])
    elif size < 1 << 16:
        head += bytes([0x80 | 126]) + size.to_bytes(2, "big")
    else:
        head += bytes([0x80 | 127]) + size.to_bytes(8, "big")
    mask = os.urandom(4)
    return head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))


class _Reader:
    def __init__(self, sock: socket.socket, buffered: bytes = b""):
        self.sock, self.buf = sock, buffered

    def take(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise AgentError("ECM 에이전트가 답 없이 연결을 닫았다")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out


def ws_exchange(url: str, text: str, *, timeout: float = AGENT_TIMEOUT) -> str:
    """웹소켓 하나를 열어 글 한 줄을 보내고 첫 글 답을 낸다(RFC 6455 의 쓰는 몫만)."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "ws" or not parts.hostname:
        raise AgentError(f"에이전트 주소(ws://…)가 아니다: {url}")
    port = parts.port or 80
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (f"GET {parts.path or '/'} HTTP/1.1\r\nHost: {parts.hostname}:{port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
    try:
        sock = socket.create_connection((parts.hostname, port), timeout=timeout)
    except OSError as exc:
        raise AgentError(f"ECM 에이전트에 못 닿았다({url}) — 이 PC 에서 ECM 에이전트(트레이의 Rayful)가 도는지 본다: {exc}") from exc
    with sock:
        try:
            sock.sendall(request.encode("ascii"))
            head = b""
            while b"\r\n\r\n" not in head:
                chunk = sock.recv(4096)
                if not chunk:
                    raise AgentError("ECM 에이전트가 웹소켓 머리 없이 닫았다")
                head += chunk
            head, rest = head.split(b"\r\n\r\n", 1)
            lines = head.decode("latin-1").split("\r\n")
            if " 101 " not in lines[0] + " ":
                raise AgentError(f"ECM 에이전트가 웹소켓을 안 받았다: {lines[0]}")
            accept = base64.b64encode(hashlib.sha1((key + WS_GUID).encode("ascii")).digest()).decode("ascii")
            headers = {k.strip().lower(): v.strip() for k, v in (l.split(":", 1) for l in lines[1:] if ":" in l)}
            if headers.get("sec-websocket-accept") != accept:
                raise AgentError("ECM 에이전트의 웹소켓 답 열쇠가 틀렸다")
            sock.sendall(_ws_frame(text.encode("utf-8"), 0x1))
            reader = _Reader(sock, rest)
            while True:
                b0, b1 = reader.take(2)
                size = b1 & 0x7F
                if size == 126:
                    size = int.from_bytes(reader.take(2), "big")
                elif size == 127:
                    size = int.from_bytes(reader.take(8), "big")
                mask = reader.take(4) if b1 & 0x80 else b""
                payload = reader.take(size)
                if mask:
                    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
                opcode = b0 & 0x0F
                if opcode == 0x9:
                    sock.sendall(_ws_frame(payload, 0xA))
                elif opcode == 0x8:
                    raise AgentError("ECM 에이전트가 답 없이 웹소켓을 닫았다")
                elif opcode in (0x1, 0x2):
                    try:
                        sock.sendall(_ws_frame(b"", 0x8))
                    except OSError:
                        pass
                    return payload.decode("utf-8", "replace")
        except socket.timeout as exc:
            raise AgentError(f"ECM 에이전트가 {timeout:.0f} 초 안에 답하지 않았다") from exc
        except OSError as exc:
            raise AgentError(f"ECM 에이전트와 주고받다 끊겼다: {exc}") from exc


class Agent:
    """PC 의 ECM 에이전트 — 받은 파일을 기본 앱으로 연다."""

    def __init__(self, url: str = DEFAULT_AGENT, docs_root=DEFAULT_DOCS_ROOT):
        self.url = url
        self.docs_root = pathlib.Path(docs_root)

    @classmethod
    def from_env(cls) -> "Agent":
        return cls(os.environ.get("ECM_AGENT_URL", "").strip() or DEFAULT_AGENT,
                   os.environ.get("ECM_DOCS_ROOT", "").strip() or DEFAULT_DOCS_ROOT)

    def _received(self, folder: str) -> set[pathlib.Path]:
        """``<받는 자리>\\<계정>\\<folder>\\<시각 번호>\\`` 아래 받은 파일들(잠금 파일 ``~$`` 은 뺀다)."""
        found: set[pathlib.Path] = set()
        if not self.docs_root.is_dir():
            return found
        for account in self.docs_root.iterdir():
            place = account / folder
            if not place.is_dir():
                continue
            for stamp in place.iterdir():
                if stamp.is_dir():
                    found.update(f for f in stamp.iterdir() if f.is_file() and not f.name.startswith(LOCK_PREFIX))
        return found

    def _download(self, ticket: Ticket, action: str, folder: str, file_timeout: float) -> pathlib.Path:
        """에이전트에 받기 한 줄을 보내고, ``folder`` 아래 새로 생긴 받은 파일이 다 쓰일 때까지 기다려 그 경로를 낸다.
        받은 파일 이름은 짓지 않는다 — 편집 열기는 이름 끝에 열쇠 · 계정을 한 번 더 붙여 받는다."""
        fields = (ticket.doc_id, ticket.object_id, ticket.file_name)
        if any(ch < " " for f in fields for ch in f):
            raise AgentError("열기 답의 값에 제어 글자가 들어 있어 에이전트에 보내지 않는다")
        line = AGENT_FIELD_SEPARATOR.join(("Download", ticket.doc_id, ticket.object_id, action, ticket.file_name, AGENT_SYSTEM))
        before = self._received(folder)
        answer = ws_exchange(self.url, line)
        if answer.strip().strip('"') != AGENT_OK:
            raise AgentError(f"ECM 에이전트가 OK 대신 이렇게 답했다: {answer[:200]}")
        deadline = time.monotonic() + file_timeout
        last: tuple[pathlib.Path, int] | None = None
        while time.monotonic() < deadline:
            fresh = sorted(self._received(folder) - before, key=lambda f: (f.name != ticket.file_name, f.name))
            if fresh:
                target = fresh[0]
                try:
                    size = target.stat().st_size
                except OSError:
                    size = -1
                if size > 0 and last == (target, size):
                    return target
                last = (target, size)
            time.sleep(POLL)
        raise AgentError(f"ECM 에이전트가 OK 를 냈는데 {file_timeout:.0f} 초 안에 {self.docs_root} 아래 {folder} 에 받은 파일이 안 생겼다")

    def download_view(self, ticket: Ticket, *, file_timeout: float = FILE_TIMEOUT) -> pathlib.Path:
        """보기로 받는다 — 읽기 전용으로 뜬다."""
        return self._download(ticket, AGENT_ACTION_VIEW, VIEW_FOLDER, file_timeout)

    def download_edit(self, ticket: Ticket, *, file_timeout: float = FILE_TIMEOUT) -> pathlib.Path:
        """편집으로 받는다 — ``Ecm.checkout`` 으로 잠근 뒤에만 부른다. 읽기 쓰기로 뜬다."""
        return self._download(ticket, AGENT_ACTION_EDIT, CHECKOUT_FOLDER, file_timeout)

    def upload_new(self, path: pathlib.Path) -> tuple[str, str]:
        """새 문서로 올릴 파일을 서버 임시 자리에 올린다 — 화면의 등록 저장이 먼저 부르는 줄. (서버 자리, 서버 파일 이름)을 낸다.
        로컬 파일은 지우지 않는다(화면은 설정에 따라 지운다 — 이 손은 그 걸음을 안 한다)."""
        text = str(path)
        if any(ch < " " or ch == "|" for ch in text):
            raise AgentError("올릴 파일 경로에 제어 글자나 「|」가 들어 에이전트에 보내지 않는다")
        answer = ws_exchange(self.url, AGENT_UPLOAD + AGENT_FIELD_SEPARATOR + REGISTER_ROW + "|" + text)
        try:
            got = json.loads(answer)
        except json.JSONDecodeError as exc:
            raise AgentError(f"ECM 에이전트가 올림 답 대신 이렇게 답했다: {answer[:200]}") from exc
        server_path, server_file = str(got.get("SERVERPATH", "")), str(got.get("SERVERFILE", ""))
        if got.get("LISTID") != REGISTER_ROW or not server_path or not server_file:
            raise AgentError(f"ECM 에이전트의 올림 답에 서버 자리가 없다: {answer[:200]}")
        return server_path, server_file


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


def _close(path: pathlib.Path, app: str, wait: float, save: bool) -> tuple[str, dict]:
    if app == ACROBAT:     # 보기 전용 — 저장할 것이 없다
        args = [str(ACROBAT_CLOSE_SCRIPT), "-Path", str(path), "-WaitSeconds", str(int(wait))]
    else:
        args = [str(CLOSE_SCRIPT), "-Path", str(path), "-App", app, "-WaitSeconds", str(int(wait)), *(["-Save"] if save else [])]
    proc = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", *args],
                          capture_output=True, timeout=wait + 60)
    out = proc.stdout.decode("utf-8", "replace").strip()
    if proc.returncode in CLOSE_EXIT:
        try:
            said = json.loads(out.splitlines()[-1]) if out else {}
        except json.JSONDecodeError:
            said = {}
        return CLOSE_EXIT[proc.returncode], said
    raise EcmError(f"창 닫는 손이 실패했다(종료 {proc.returncode}): {out or proc.stderr.decode('utf-8', 'replace').strip()}")


def close_window(path: pathlib.Path, app: str, *, wait: float = WINDOW_WAIT) -> str:
    """에이전트가 띄운 그 문서만 닫는다 — 그 앱에 남은 문서가 없을 때만 앱을 끈다. closed · not-found · not-front(Acrobat 에서 다른
    pdf 가 앞 탭이라 안 건드렸다) · not-office 를 낸다."""
    if not app:
        return "not-office"
    return _close(path, app, wait, save=False)[0]


# ── 편집 — 잠그고 열기 · 저장하고 다음 판으로 올리기 ─────────────────────

@dataclass(frozen=True)
class CheckedIn:
    version_before: str
    version_after: str
    picked: str            # 편집완료 창에서 고른 판


def checkin_pending(object_id: str) -> bool:
    """그 문서의 편집완료 창이 이미 떠 있나 — 사람이 오피스를 먼저 끈 판. 창을 찾기만 하고 누르지 않는다."""
    proc = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(CHECKIN_SCRIPT),
                           "-ObjectId", object_id, "-Desc", FIND_ONLY_DESC, "-Current", "0", "-WaitSeconds", "2",
                           "-FindOnly"],
                          capture_output=True, timeout=60)
    return proc.returncode == 0


def edit_document(ecm: Ecm, agent: Agent, object_id: str) -> Opened:
    """편집으로 연다 — 서버가 그 문서를 이 사람 이름으로 잠그고, 에이전트가 읽기 쓰기로 띄운다. 기본 앱이 없으면 멈춘다
    (``DefaultAppNeeded``) — 고르는 창이 뜬 채로 잠그면 사람이 모르는 잠금이 남는다. 잠근 뒤 받기가 안 서면 그 말을 낸다."""
    ticket = ecm.view(object_id)                    # 확장자 · 이름을 먼저 본다 — 잠그기 전에 기본 앱을 세운다
    ensured = default_app.ensure(ticket.ext)
    locked = ecm.checkout(object_id)
    try:
        path = agent.download_edit(locked)
    except AgentError as exc:
        raise AgentError(f"{exc} — 문서는 서버에서 잠겼다. ECM 화면에서 그 문서를 「편집취소」해 잠금을 푼다") from exc
    return Opened(path, locked, ensured.progid, ensured.written)


def checkin_document(ecm: Ecm, path: pathlib.Path, object_id: str, desc: str, *, app: str = "",
                     docs_root=None) -> CheckedIn:
    """편집으로 연 문서를 저장해 닫고, 에이전트의 편집완료 창에서 다음 판 · 수정 내용으로 올린 뒤 판이 올랐나 본다.

    에이전트는 오피스 프로세스가 끝나야 편집완료 창을 띄운다. 같은 앱에 사람의 다른 문서가 남아 있으면 앱을 끄지 않고 멈춘다 —
    사람이 그 문서들을 닫으면(또는 저장하고 앱을 끄면) 창이 뜨고, 같은 명령을 다시 부르면 창에서 이어 간다."""
    object_id = _object_id(object_id)
    desc = desc.strip()
    if not desc:
        raise EcmError("수정 내용(--desc)이 비었다 — 무엇을 고쳤나를 한 줄 적는다")
    path = pathlib.Path(path)
    root = pathlib.Path(docs_root or os.environ.get("ECM_DOCS_ROOT", "").strip() or DEFAULT_DOCS_ROOT)
    try:
        inside = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        inside = ()
    # 에이전트가 편집으로 받은 그 문서만 — <받는 자리>\<계정>\CHECKOUT\<시각 번호>\<이름에 그 문서 열쇠>
    if len(inside) != 4 or inside[1].lower() != CHECKOUT_FOLDER.lower() or object_id.lower() not in path.name.lower():
        raise EcmError(f"그 문서({object_id})를 편집으로 받은 파일(…\\{CHECKOUT_FOLDER}\\…)이 아니다: {path} — edit 가 낸 경로를 그대로 준다")
    app = app or OFFICE_BY_EXT.get(path.suffix.lower(), "")
    if not app:
        raise EcmError(f"이 꼴({path.suffix})은 오피스로 저장해 닫지 못한다 — ECM 화면에서 편집완료를 누른다")
    before = ecm.version(object_id)
    if not before:
        raise EcmError("문서 정보에서 지금 판을 못 읽었다 — 다음 판을 가릴 수 없어 올리지 않는다")
    window, said = _close(path, app, WINDOW_WAIT, save=True)
    left = said.get("left", -1)
    if window == "not-found" and not checkin_pending(object_id):
        raise EcmError(f"{WINDOW_WAIT:.0f} 초 안에 열린 그 문서를 못 찾았다 — 저장된 것이 고친 판인지 모르니 올리지 않는다. 문서가 떠 있으면 "
                       "그대로 두고 같은 명령을 다시 부르고, 사람이 이미 저장해 닫았으면 ECM 화면에서 편집완료를 누른다")
    if window == "closed" and left != 0:
        what = f"다른 문서 {left} 개가 열려 있어" if left > 0 else "남은 문서를 못 세어"
        raise EcmError(f"저장해 닫았다. 같은 앱에 {what} 앱을 끄지 않았다 — 에이전트는 앱이 끝나야 편집완료 창을 띄운다. 사람이 그 "
                       "문서들을 저장해 닫은 뒤(또는 앱을 끈 뒤) 같은 명령을 다시 부른다")
    proc = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(CHECKIN_SCRIPT),
                           "-ObjectId", object_id, "-Desc", desc, "-Current", before, "-WaitSeconds", str(int(CHECKIN_WAIT))],
                          capture_output=True, timeout=CHECKIN_WAIT + 90)
    out = proc.stdout.decode("utf-8", "replace").strip()
    try:
        got = json.loads(out.splitlines()[-1]) if out else {}
    except json.JSONDecodeError:
        got = {}
    if proc.returncode == 2:
        raise EcmError(f"{CHECKIN_WAIT:.0f} 초 안에 편집완료 창이 안 떴다 — 오피스가 아직 떠 있으면 사람이 끄고 같은 명령을 다시 부른다")
    if proc.returncode != 0 and got.get("saved"):
        raise EcmError("편집완료의 저장은 보냈는데 창이 시한 안에 안 닫혔다 — 다시 누르지 말고 잠시 뒤 version 으로 판이 올랐나 본다")
    if proc.returncode != 0:
        raise EcmError(f"편집완료 창을 누르지 않았다 — 창이 떠 있으면 사람이 「새로운 버전」을 고르고 누른다: "
                       f"{out or proc.stderr.decode('utf-8', 'replace').strip()}")
    after, deadline = before, time.monotonic() + VERSION_WAIT
    while time.monotonic() < deadline and after == before:
        time.sleep(VERSION_POLL)
        after = ecm.version(object_id)
    if after == before:
        raise EcmError(f"편집완료는 눌렀는데 {VERSION_WAIT:.0f} 초 안에 최종 버전이 {before} 그대로다 — ECM 화면에서 판을 본다")
    return CheckedIn(before, after, str(got.get("picked", "")))


def register_document(ecm: Ecm, agent: Agent, path: pathlib.Path, *, cabinet: str, folder: str, security: str,
                      open_flag: str, title: str = "") -> Registered:
    """PC 의 파일 하나를 그 문서함 폴더의 새 문서로 올린다 — 화면의 「컨텐츠 등록」과 같은 차례: 같은 이름 찾기 → 에이전트가 서버
    임시 자리에 올림 → 등록 → 목록에서 다시 읽어 섰나 본다. 보안등급 · 공개는 사람이 대화에서 확인한 짝만 준다 — 잘못 고르면
    동료 전체에 보인다. 같은 이름이 그 폴더에 있으면 올리지 않는다(다음 판은 edit · checkin 의 몫이다)."""
    path = pathlib.Path(path).resolve()       # 에이전트는 다른 프로세스라 상대 경로를 제 자리에서 푼다
    if not path.is_file() or path.stat().st_size == 0:
        raise EcmError(f"올릴 파일이 없거나 비었다: {path}")
    if not CABINET_ID.match(cabinet):         # 올린 뒤에 지면 올라간 문서를 「실패」로 알리게 된다 — 서버에 닿기 전에 본다
        raise EcmError(f"문서함 열쇠(cab…)가 아니다: {cabinet!r} — cabinets 가 낸 열쇠를 준다")
    if (security, open_flag) not in SECURITY_PAIRS:
        raise EcmError("보안등급 · 공개 짝이 화면의 여섯 가운데 하나가 아니다 — " +
                       " · ".join(f"{s}/{o}={n}" for (s, o), n in SECURITY_PAIRS.items()))
    if not FOLDER_ID.match(folder):
        raise EcmError(f"폴더 열쇠(fdr…)가 아니다: {folder!r} — folders 가 낸 열쇠를 준다")
    ext = path.suffix.lstrip(".").lower()
    if not ext or not ext.isalnum():
        raise EcmError(f"확장자가 없는 파일은 화면도 안 받는다: {path.name}")
    name = check_title(title or path.stem)
    if (name + "." + ext) != path.name and title:
        log.info("등록 이름을 파일 이름과 달리 둔다: %s", name)
    clash = ecm.duplicates(folder, name, ext)
    if clash:
        raise EcmError(f"그 폴더에 같은 이름의 문서가 있다({', '.join(clash)}) — 고쳐 올리려면 edit · checkin 으로 다음 판을 올리고, "
                       "새 문서면 이름을 바꾼다")
    server_path, server_file = agent.upload_new(path)
    object_id = ecm.register(folder=folder, title=name, ext=ext, size=path.stat().st_size, server_path=server_path,
                             server_file=server_file, security=security, open_flag=open_flag)
    listed = [d for d in ecm.list(search=name, cabinet=cabinet) if d.object_id == object_id]
    if not listed:
        raise EcmError(f"등록은 됐는데(문서 {object_id}) 그 문서함 목록에서 못 찾았다 — 폴더가 그 문서함 것이 아닐 수 있다. "
                       "다시 올리지 말고 ECM 화면에서 그 폴더를 본다")
    if listed[0].folder_id != folder or listed[0].security != security:
        raise EcmError(f"올린 문서({object_id})의 폴더 · 보안등급이 고른 값과 다르다(폴더 {listed[0].folder_id} · 보안 "
                       f"{listed[0].security}) — ECM 화면에서 그 문서의 속성을 본다")
    return Registered(object_id, name, listed[0].version)


def reader_path() -> pathlib.Path:
    return pathlib.Path(os.environ.get("ECM_DRM_READER", "").strip() or DEFAULT_READER).expanduser()


def extract_text(path: pathlib.Path, *, reader: pathlib.Path | None = None) -> tuple[str, str]:
    """받은 파일을 drm-office-read 의 읽는 손에 넘겨 (글자, 그 손의 한 줄)을 낸다. 평문은 임시 폴더째 바로 지운다."""
    reader = reader or reader_path()
    if not reader.exists():
        raise ReadError(f"글자를 뽑는 손이 없다: {reader} — 스킬 drm-office-read 가 깔렸는지 본다")
    out_dir = pathlib.Path(tempfile.mkdtemp(prefix="ecm-read-"))
    try:
        proc = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(reader),
                               str(path), "-OutDir", str(out_dir)], capture_output=True, timeout=READ_TIMEOUT)
        lines = [l for l in proc.stdout.decode("utf-8", "replace").splitlines() if l.strip()]
        summary = next((l for l in lines if l.startswith("[")), "")
        texts = sorted(out_dir.glob("*.txt"))
        if proc.returncode == 0 and not texts and not summary:
            raise ReadError(f"이 꼴({path.suffix})은 읽는 손이 글자로 뽑지 않는다 — 화면에서 보려면 open 으로 연다")
        if proc.returncode != 0 or not texts:
            why = summary or (lines[-1] if lines else proc.stderr.decode("utf-8", "replace").strip()[-300:])
            raise ReadError(f"읽는 손이 글자를 못 냈다 — {why or '까닭 없음'}")
        return texts[0].read_text(encoding="utf-8-sig"), summary
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def read_document(ecm: Ecm, agent: Agent, object_id: str, *, allow_picker: bool = False,
                  reader: pathlib.Path | None = None) -> ReadResult:
    """열고 → 에이전트가 띄운 창을 닫고 → 받은 파일에서 글자를 뽑는다.

    닫는 것이 먼저다 — 오피스가 그 파일을 쥐고 있으면 읽는 손이 파일 머리를 못 읽는다(「다른 프로세스가 사용 중」). 받은 파일은
    닫은 뒤에도 그 자리에 남는다. 화면에 띄워 두고 보려면 ``open_document`` 를 쓴다.
    """
    opened = open_document(ecm, agent, object_id, allow_picker=allow_picker)
    window = close_window(opened.path, viewer_of(opened.progid))
    try:
        text, summary = extract_text(opened.path, reader=reader)
    except ReadError as exc:
        raise ReadError(f"{exc} — 받은 파일: {opened.path}") from exc
    return ReadResult(text, summary, opened, window)


# ── 명령줄 ───────────────────────────────────────────────────────────────

WINDOW_WORD = {"closed": "닫았다", "not-found":f"{WINDOW_WAIT:.0f} 초 안에 못 찾았다 — 떠 있으면 사람이 닫는다",
               "not-front": "다른 pdf 가 앞 탭이라 안 건드렸다 — 다 봤으면 사람이 그 탭을 닫는다",
               "not-office": "닫을 줄 아는 앱(오피스 · Acrobat)이 아니라 안 닫았다 — 다 봤으면 사람이 닫는다"}


def _print_docs(docs: list[Doc], page: int, where: str = "내 문서함") -> None:
    print(f"{where} — {len(docs)} 건 (쪽 {page})")
    for i, d in enumerate(docs, 1):
        bits = [f"{d.name}" + (f".{d.ext}" if d.ext and not d.name.lower().endswith("." + d.ext.lower()) else ""),
                f"크기 {d.size}" if d.size else "", f"고침 {d.modified}" if d.modified else "",
                f"판 {d.version}" if d.version else "", f"올린 이 {d.owner}" if d.owner else "",
                f"폴더 {d.folder_path}" if d.folder_path else "", f"잠금 {d.locked_by}" if d.locked_by else "",
                f"id {d.object_id}"]
        print(f"{i:>3}. " + " · ".join(b for b in bits if b))


def _describe_open(opened: Opened) -> list[str]:
    app = f"기본 앱 {opened.progid or '사람이 고르는 창'}" + (" (이번에 적었다)" if opened.app_written else "")
    return [f"받은 파일: {opened.path}", app]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ecm.py", description="사내 문서함(ECM) — 찾고 읽고, 사람이 확인한 문서는 편집해 다음 판으로 올린다")
    parser.add_argument("--session", help="세션 파일(Playwright 저장 상태) — 안 주면 MAILBOX_COOKIES")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("session", help="ECM 세션이 살았나 본다")
    sub.add_parser("cabinets", help="볼 수 있는 부서 · 프로젝트 문서함과 그 열쇠")
    for name in ("list", "count"):
        p = sub.add_parser(name, help="문서함 목록" if name == "list" else "문서함 건수")
        p.add_argument("--search", default="", help="찾을 낱말(화면의 찾기 칸)")
        p.add_argument("--period", default=DEFAULT_PERIOD, choices=PERIODS,
                       help=f"기간 — 화면의 기간 필터 값(1년은 12M · 전체는 ALL). 기본 {DEFAULT_PERIOD}")
        p.add_argument("--folder", default="", help="내 문서함의 폴더 키(목록 줄의 folder_id)")
        p.add_argument("--cabinet", default="", help="부서 · 프로젝트 문서함 열쇠(cabinets 의 cab…) — 안 주면 내 문서함")
        if name == "list":
            p.add_argument("--page", type=int, default=1)
            p.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE)
            p.add_argument("--json", action="store_true", help="줄마다 JSON 으로 낸다")
    for name in ("open", "read"):
        p = sub.add_parser(name, help="문서를 받아 연다(창이 남는다)" if name == "open" else "문서를 받아 글자를 뽑고 창을 닫는다")
        p.add_argument("object_id", help="목록의 id(MS_OBJECT_ID · 16 자리 hex)")
        p.add_argument("--allow-picker", action="store_true", help="기본 앱이 없어도 열어 사람이 고르는 창에서 고르게 둔다")
    p = sub.add_parser("version", help="문서의 최종 버전")
    p.add_argument("object_id")
    p = sub.add_parser("edit", help="편집으로 연다 — 서버가 그 문서를 잠근다. 사람이 확인한 뒤에만 부른다")
    p.add_argument("object_id")
    p = sub.add_parser("checkin", help="편집으로 연 문서를 저장해 닫고 다음 판 · 수정 내용으로 올린다")
    p.add_argument("object_id")
    p.add_argument("path", help="edit 가 낸 받은 파일")
    p.add_argument("--desc", required=True, help="수정 내용 — 편집완료 창의 글칸에 적힌다")
    p = sub.add_parser("default-app", help="확장자의 기본 앱 상태와 이 PC 의 해시 계산을 본다 — 쓰지 않는다")
    p.add_argument("ext")
    p = sub.add_parser("folders", help="문서함의 폴더 한 층과 열쇠 — 새 문서를 둘 자리를 고른다")
    p.add_argument("cabinet", help="cabinets 의 문서함 열쇠(cab…)")
    p.add_argument("--parent", default="", help="이 폴더(fdr…) 아래 층 — 안 주면 문서함 바로 아래")
    p = sub.add_parser("register", help="PC 의 파일 하나를 새 문서로 올린다 — 폴더 · 보안등급 · 공개를 사람이 확인한 뒤에만 부른다")
    p.add_argument("path", help="올릴 파일")
    p.add_argument("--cabinet", required=True, help="문서함 열쇠(cab…)")
    p.add_argument("--folder", required=True, help="폴더 열쇠(fdr…) — folders 가 낸다")
    p.add_argument("--security", required=True, choices=sorted({s for s, _ in SECURITY_PAIRS}),
                   help="보안등급 — 1A 기밀 · 2A 사외비A · 2B 사외비B · 3A 일반")
    p.add_argument("--open", required=True, choices=["T", "F"], dest="open_flag", help="공개(T) · 비공개(F) — 1A 는 F, 3A 는 T 만")
    p.add_argument("--title", default="", help="등록 이름(확장자 뺀) — 안 주면 파일 이름")
    args = parser.parse_args(argv)

    try:
        if args.command == "default-app":
            ext = default_app.normalize(args.ext)
            now, check = default_app.state(ext), default_app.preflight()
            print(f"{ext} — 지금 {now.progid or '안 정해짐'}{f' ({now.where})' if now.where else ''} · Windows 가 푸는 앱 "
                  f"{default_app.resolved_progid(ext) or '없음'} · 고를 앱 {default_app.pick_progid(ext) or '없음'}")
            print(f"이 PC 의 해시 계산 — Windows 가 적은 {check.total} 개 중 {check.matched} 개가 같다")
            return EXIT_OK
        ecm = Ecm(os.environ.get("ECM_URL", "").strip() or DEFAULT_URL, args.session or session_path())
        if args.command == "session":
            alive = ecm.session_alive()
            print("ECM 세션이 살았다" if alive else "ECM 세션이 끊겼다 — 스킬 ep-login 으로 다시 받는다")
            return EXIT_OK if alive else EXIT_SESSION
        if args.command == "cabinets":
            for c in ecm.cabinets():
                print(f"{c.name} · {c.kind}{' · 내 부서' if c.own else ''} · 열쇠 {c.key}")
            return EXIT_OK
        if args.command == "list":
            docs = ecm.list(search=args.search, page=args.page, per_page=args.per_page, period=args.period, folder=args.folder,
                            cabinet=args.cabinet)
            if args.json:
                for d in docs:
                    print(json.dumps(dataclasses.asdict(d), ensure_ascii=False))
            else:
                _print_docs(docs, args.page, f"문서함 {args.cabinet}" if args.cabinet else "내 문서함")
            return EXIT_OK
        if args.command == "count":
            print(ecm.count(search=args.search, period=args.period, folder=args.folder, cabinet=args.cabinet))
            return EXIT_OK
        if args.command == "version":
            print(ecm.version(args.object_id) or "못 읽었다")
            return EXIT_OK
        if args.command == "folders":
            for f in ecm.folders(args.cabinet, args.parent):
                print(f"{f.name} · 열쇠 {f.id}{' · 아래 폴더 있음' if f.has_sub else ''}")
            return EXIT_OK
        if args.command == "register":
            done = register_document(ecm, Agent.from_env(), pathlib.Path(args.path), cabinet=args.cabinet, folder=args.folder,
                                     security=args.security, open_flag=args.open_flag, title=args.title)
            print(f"올렸다 — {done.title} · 판 {done.version} · 보안 {SECURITY_PAIRS[(args.security, args.open_flag)]} · id {done.object_id}")
            return EXIT_OK
        if args.command == "checkin":
            done = checkin_document(ecm, pathlib.Path(args.path), args.object_id, args.desc)
            print(f"올렸다 — 판 {done.version_before} → {done.version_after} · 고른 판 {done.picked or '?'}")
            return EXIT_OK
        agent = Agent.from_env()
        if args.command == "edit":
            opened = edit_document(ecm, agent, args.object_id)
            print("\n".join([*_describe_open(opened), "편집으로 열었다 — 서버가 잠갔다. 고친 뒤 checkin 으로 올리거나, 그만두면 ECM 화면에서 「편집취소」한다"]))
            return EXIT_OK
        if args.command == "open":
            opened = open_document(ecm, agent, args.object_id, allow_picker=args.allow_picker)
            print("\n".join(_describe_open(opened)))
            return EXIT_OK
        got = read_document(ecm, agent, args.object_id, allow_picker=args.allow_picker)
        print("\n".join([got.summary or "[읽음]", *_describe_open(got.opened), f"창: {WINDOW_WORD[got.window]}", "---"]))
        print(got.text)
        return EXIT_OK
    except (SessionMissing, SessionExpired) as exc:
        print(exc, file=sys.stderr)
        return EXIT_SESSION
    except default_app.DefaultAppNeeded as exc:
        print(exc, file=sys.stderr)
        return EXIT_DEFAULT_APP
    except (EcmError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(exc, file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
