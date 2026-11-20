"""사내 메일함(Lotus Notes · HCL Domino 웹메일)을 읽는 손과, 메일함을 바꾸는 이름 붙은 손들. 표준 라이브러리와 형제 스킬 ep-login 의
``ep_session``(세션 파일 → 쿠키 통)만 쓴다 — ``../../ep-login/scripts/`` 에서 싣고, 그 자리가 없으면(이 파일만 옮겨 쓸 때)
``ep_session.py`` 와 ``places.json`` 을 이 파일 곁에 둔다.

무엇을 하나
    읽기 길 — 받은편지함 · 폴더 · 보낸편지함 · 임시보관함 · 휴지통의 목록, 모든편지함의 받는 꼴 · 중요도, 받는 사람 목록, 검색, 본문 ·
    첨부, 사내 주소록 · 조직도, 폴더 나무 · 규칙 목록, 세션 확인. ⚠ **읽기 길은 메일의 읽음 표시를 바꾸지 않는다** — 읽음을 안 바꾸는
    것으로 잰 주소 꼴(``read_only_patterns``)만 묻고, 그 밖은 서버에 닿기 전에 ``ChangeRefused`` 로 막는다.

    메일함을 바꾸는 손은 이름 붙은 함수 하나씩이다 — ``mark_read`` · ``mark_unread`` · ``create_folder`` · ``delete_folder`` ·
    ``move_mails`` · ``trash_mails`` · ``restore_from_trash`` · ``restore_mails`` · ``save_rule`` · ``delete_rule`` · ``save_draft``.
    사람이 그 대상을 보고 고른 뒤에만 부른다 — 이 파일은 그 확인을 대신하지 않는다. 손마다 제 주소 꼴만 보내고, 서버의 답을 믿지 않고
    보기로 다시 봐서 안 섰으면 ``MailboxError`` 다. 규칙의 자동전달 칸은 늘 비워 보내고 자동전달 규칙은 고치지 않는다(지우기는 된다).

    회사 메일함 · 웹메일 화면에서 잰 주소 · 칸 · 꼴은 ``references/SOURCES.md`` 「inbox.py」가(주소록 · 조직도 · 배포그룹 · 직급 등급은
    그것을 쓰는 형제 스킬 company-directory 의 ``references/SOURCES.md`` 가) 든다 — 회사 PC 에서 다시 재기 전에는
    바꾸지 않는다(집의 검사는 그 꼴을 흉내 낸 가짜라 초록인 채 실물에서 깨진다).

어떻게 부르나
    로그인은 이 파일이 하지 않는다. 스킬 ep-login 의 받는 손이 남긴 세션 쿠키 파일(Playwright 저장 상태 꼴 ``{"cookies": [...]}``)로
    묻는다. 쿠키는 보낼 주소의 호스트에 맞는 것만 실린다 — 다른 사내 앱의 쿠키가 함께 들어 있어도 된다::

        import inbox

        box = inbox.Mailbox.from_env()                  # 설정이 틀리면 여기서 MailboxConfigError
        for mail in box.list(count=20):                 # 받은편지함 — 새것부터
            if mail.unread:
                html = box.body(mail)                   # HTML 본문 — 없거나 서버가 안 주면 None
                text = box.body(mail, "text")           # 평문 조각 — 없으면 None
                for a in mail.attachments:
                    if a.ecm:                           # 문서함(ECM)을 가리키는 쪽지 — 문서는 문서함에 있다
                        key = box.ecm_key(mail, a)      # 문서 열쇠(16 hex) — 스킬 company-ecm 이 연다
                    else:
                        data = box.attachment(mail, a)  # bytes

        for folder in box.folders():                    # 쓰는 사람이 지은 폴더 — 시스템 폴더는 안 낸다
            got = box.list_folder(folder, count=200)    # 그 폴더 — 새것부터 · 줄마다 folder 에 경로
        marks = box.list_all(count=200)                 # 모든편지함의 받는 꼴 · 중요도 — 보기가 없으면 None
        sent = box.list_sent(count=100)                 # 보낸편지함 — 받는 사람은 그 목록의 수신인 열
        drafts = box.list_drafts(count=30)              # 임시보관함 — 보기가 없으면 None
        total, rows = box.search("워크샵", scope="all", field="subject")   # 웹메일 검색 — (모두 건수, 이 쪽의 Found)
        lists = box.recipient_lists(count=600)          # unid → 받는 사람 목록 · 보기가 없으면 None
        people = box.find_people("me@company.com", "<회사>(<코드>)")   # 사내 주소록 — 밖의 주소는 빈 목록
        one = box.find_exact("CN=홍길동/OU=…/O=…", "<회사>(<코드>)")    # 그 주소 · Notes 이름 · ID 의 사람만 — 하나면 그 사람
        raw = box.directory_answer("홍길동", "<회사>(<코드>)")         # 주소록 답 그대로(dict) — 꼴을 재는 자리
        chart = box.org_snapshot("<회사>(<코드>)")                     # 회사 조직 전체(OrgChart) — 부서 나무 · 부서마다 사람
        team = chart.people(chart.find_depts("소재사업실")[0].code)    # 그 부서와 하위 조직의 사람
        groups = box.org_groups("<회사>(<코드>)", "jobtitle")          # 배포그룹(직책) — (열쇠, 이름)
        members = box.group_members(groups[0][0])                     # 그 배포그룹의 (이름, 직급, 부서, 메일)
        box.session_alive()                             # 메일을 안 건드리는 세션 확인

        # 아래는 메일함을 바꾼다 — 사람이 확인한 뒤에만
        made = box.create_folder("검토", parent="프로젝트")   # FolderNode — 다시 봐서 선 것
        box.move_mails([mail.unid], made.path)          # 빈 글자면 받은편지함 — 다시 봐서 다 든 것
        box.trash_mails([mail.unid])                    # 휴지통으로 — 다시 봐서 다 든 것
        box.restore_mails([mail.unid])                  # 되살린다 — 받은편지함에 안 돌아온 unid 를 낸다
        box.delete_folder(made.path)                    # 빈 폴더만 · 이전메일함 짝까지
        rules = box.rules()                             # Rule — 조건 · 갈래 · 폴더 · 자동전달인가
        uid = box.save_rule(inbox.Rule(unid="", box="inbox", action="move_folder", folder="프로젝트",
                                       conditions={"subject": "[주간]"}))   # unid 를 주면 고친다
        box.delete_rule(uid)

    주소 · 쿠키 파일을 환경변수 대신 바로 줄 때는 ``inbox.Mailbox(url, cookies_file)`` 다. 메일함 주소를 모르면
    ``inbox.discover_mailbox("http://<메일 서버>", cookies_file)`` 가 그 세션에 로그인한 사람의 ``…/<번호>.nsf`` 를 낸다.

무엇을 내나
    목록은 ``Entry`` · ``SentEntry`` · ``Found`` 를, 폴더는 ``Folder`` · ``FolderNode`` 를, 모든편지함은 ``Marks`` 를, 받는 사람은
    ``Recipient`` 묶음을, 주소록은 ``DirectoryPerson`` · ``OrgChart`` 를, 규칙은 ``Rule`` 을 낸다. 시각은 메일함이 준 글자 그대로다 —
    시각으로 푸는 일은 부르는 쪽이 한다. ``body`` 는 글자, ``attachment`` 는 bytes, ``ecm_key`` 는 문서함 문서의 열쇠(16 hex)다.

    오류는 다 ``MailboxError`` 의 갈래다 — 세션이 끊겼으면 ``SessionExpired``(스킬 ep-login 으로 다시 로그인한다), 읽기 길이 잰 꼴
    밖의 주소를 지으려 하면 ``ChangeRefused``, 설정 · 인자가 틀리면 ``MailboxConfigError``(세션 파일이 없거나 못 읽거나 비었으면 그
    갈래인 ``SessionMissing``), 조직도가 그 회사 값으로 부서를 하나도 안 주면 ``DirectoryGap``, 서버가 답을 안 주면 ``MailboxError``.
    무엇을 했는지는 ``logging``(로거 이름은 모듈 이름)으로 셈과 방향만 남긴다 — 본문 · 제목 · 이름 · 주소 · 첨부 이름은 안 싣는다.

환경변수(``from_env``)
    ``MAILBOX_URL``              메일함 주소 — 웹메일 주소창의 ``…/<번호>.nsf`` 까지(그 뒤는 버린다). 꼭 준다
    ``MAILBOX_COOKIES``          세션 쿠키 파일                 기본 ``DEFAULT_COOKIES``
    ``MAILBOX_VIEW``             받은편지함 보기 이름           기본 ``INBOX_VIEW``
    ``MAILBOX_TIMEOUT_SECONDS``  응답 시한(초)                  기본 ``DEFAULT_TIMEOUT``
"""

from __future__ import annotations

import html
import json
import logging
import os
import pathlib
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

EP_LOGIN_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent.parent / "ep-login" / "scripts"   # 형제 스킬 — 세션 파일을 읽는 자리
if str(EP_LOGIN_SCRIPTS) not in sys.path:
    sys.path.append(str(EP_LOGIN_SCRIPTS))
import ep_session  # noqa: E402 — 형제 스킬의 자리를 넣은 뒤에 싣는다

DEFAULT_COOKIES = ep_session.DEFAULT_FILE
DEFAULT_TIMEOUT = 30.0
HTTP_NOT_SERVED = 501             # 본문 주소에 이 답을 내는 메일이 있다 — 「본문 없음」으로 받는다
VIEW_PAGE_MOST = 1000             # 보기 한 번(``?ReadViewEntries``)이 내는 줄의 위 — 서버가 count 를 여기서 자른다. 끝까지 훑는 쪽은 이만큼씩 받는다

# 보기 이름(받은편지함 · 보낸편지함 · 받는 사람 목록 · 모든편지함)
INBOX_VIEW = "XML_Inbox"
SENT_VIEW = "XML_Sent"
RECIPIENT_VIEW_TITLE = "!전체목록추출용"
ALL_VIEW_TITLE = "XML_모든편지함"
DRAFT_VIEW_TITLE = "XML임시편지함"
DRAFTS_FOLDER = "(Drafts)"          # 임시보관함 줄의 folder — 시스템 폴더 이름 그대로
SENT_FOLDER = "(Sent)"              # 보낸편지함 줄의 folder — 같은 꼴
TRASH_FOLDER = "($Trash)"           # 휴지통 줄의 folder — 같은 꼴
# 검색 손이 시스템 편지함을 가리키는 표지(``category`` 의 ``[${…}]`` · 메일함마다 같다) → 줄의 folder
SEARCH_SYSTEM_BOXES = {"${INBOX}": "", "${SENT}": SENT_FOLDER}
# 검색 — 웹메일 검색 창이 부르는 손(목록 JSON). 범위는 그 창의 고름 상자 값이고, 「전체」는 임시보관함을 안 든다
SEARCH_AGENT = "ag_detail_search_mailbox"
SEARCH_SCOPES = ("all", "inbox", "sent", "draft", "star", "unread", "trash")
SEARCH_SLOTS = {"subject": "ssbj", "body": "sbdy", "attachment": "satt"}   # 제목 · 본문 · 첨부 이름 → 검색 손의 칸
SEARCH_FIELDS = tuple(SEARCH_SLOTS)
SEARCH_PAGE_MOST = 100
# 메일 서버 첫 화면 — 세션에 로그인한 사람의 메일함 경로를 든다(그 화면이 받은편지함으로 넘기는 스크립트의 값)
MAILFILE_IN_ROOT = re.compile(r'var\s+mailfile\s*=\s*"([^"]+\.nsf)"', re.IGNORECASE)
SYSTEM_FOLDER_MARK = "("          # 시스템 폴더의 제목은 이 글자로 시작한다
FOLDER_SEPARATOR = "\\"           # 폴더 제목의 부모 · 자식 가름

# 받은편지함 목록 열
COLUMN_SUBJECT, COLUMN_FROM, COLUMN_DATE, COLUMN_DATE_SORT = "xsubject", "xname", "xdate", "$91"
COLUMN_SIZE, COLUMN_IMPORTANCE, COLUMN_ROLE = "xsize", "xImportance", "xrtype"
COLUMN_ATTACHMENTS, COLUMN_READ, COLUMN_RELATED = "attachment", "read", "xrelatedid"
# 보낸편지함 목록 열 — 이 보기의 xname 은 수신인이다
SENT_COLUMN_TO = "xname"
# 보낸 메일 한 통의 받는 사람 칸 — 웹메일 편집 화면이 저장할 때 받는 사람 · 참조(한 칸)와 숨은참조를 「열쇠 ITEM JSON」 을 SEP 로 이어 쓴다
SENT_PEOPLE_FIELDS = ("ToCcUserInfoJson", "BccUserInfoJson")
PEOPLE_ITEM, PEOPLE_SEP = "-=-ITEM-=-", "-=-SEP-=-"
# 그 칸의 받는 사람 갈래(type) · 칸(field) — 숨은참조 칸의 항목은 field 가 비어 온다
PERSON_TYPE, DEPT_TYPE, GROUP_TYPE, EMAIL_TYPE = "user", "dept", "group", "email"
PEOPLE_FIELD_OF = {"send_to": "to", "copy_to": "cc", "bcopy_to": "bcc"}
# 받는 사람 목록 보기의 열 — 날짜 · 수/발신 · 수신인 · 발신인
VIEW_COLUMN_DATE, VIEW_COLUMN_DIRECTION, VIEW_COLUMN_TO, VIEW_COLUMN_FROM = "$101", "$91", "$102", "$103"

UNREAD_MARK = "ico-nomail"
# 폴더 보기 읽음 열의 HTML 조각 — class 둘뿐이다(안 읽음 · 읽음)
FOLDER_UNREAD_CLASS = "mail_21"
FOLDER_READ_CLASS = re.compile(r"class='(mail_2[12])'")
ATTACHMENT_SEPARATOR = "{}"
SPLIT_MARK, ENG_MARK = "-=spl=-", "-ENG-"
# ECM 을 가리키는 큰 첨부 — <원래 이름>(<확장자>_<크기>KB).html
# 목록의 한 칸에 든 줄바꿈 글자 — 목록은 메일 한 통이 한 줄이라, 이 글자가 제목 · 이름에 남으면 줄로 읽는 쪽이 한 통을 두 줄로 가른다
LINE_BREAKS = re.compile("[\n\r\x0b\x0c\x1c-\x1e\x85\u2028\u2029]+")
ECM_ATTACHMENT = re.compile(r"^(?P<name>.+)\((?P<ext>[0-9A-Za-z]+)_(?P<kb>\d+)KB\)\.html$", re.IGNORECASE)
# 그 쪽지 맨 앞의 기계가 읽는 머리와, 그 안의 문서 열쇠 — 열쇠는 ``doc`` 뒤의 16 hex 다
ECM_HEAD = re.compile(r"<!--@!ECM!@(?P<head>.*?)-->", re.DOTALL)
ECM_OBJECT = re.compile(r"<objectId>\s*doc(?P<key>[0-9A-Fa-f]{16})\s*</objectId>")
# 쪽지 본문 링크(화면이 누르면 여는 주소)의 OBJECTID — 문서 열쇠 16 hex 글자를 ASCII 16진으로 적은 32 글자다
ECM_LINK = re.compile(r"swp_interface\.jsp\?ACTID=viewlink&(?:amp;)?OBJECTID=(?P<hex>[0-9A-Fa-f]{32})&")

# 본문 — HTML 은 꼴과 상관없는 한 길, 평문은 조각 하나
BODY_KINDS = ("html", "text")
BODY_TEXT_PART = "M1.1"

# 주소록의 예 · 아니오 칸(퇴직 · 장 여부)이 참인 값
DIRECTORY_YES = ("Y", "1", "TRUE")
# 직급 코드(``grade_code``) → 인사 등급. P 는 직원 · 임원, E 는 현장 직군 — 같은 글자 안에서만 위아래가 선다. 표에 없는 직급은
# 등급이 없는 것이 맞다 — 짝을 맞춘 근거와 빠진 직급은 형제 스킬 company-directory 의 SOURCES.md 「직급 등급」
GRADE_LEVELS = {
    "24": "P1", "23": "P2", "22": "P3", "21": "P4", "26": "P5", "27": "P6", "28": "P7", "29": "P8", "30": "P9", "31": "P10",
    "43": "E1", "42": "E2", "36": "E3", "35": "E4", "34": "E5", "33": "E6", "32": "E7",
}
# 직급 코드가 위 표에 없을 때 직급 이름으로 주는 등급. 고문은 임원급인데 임원 사이의 차례를 몰라 임원의 낮은 쪽을 준다 —
# 「임원 이상」 거르기에 들되 다른 임원 위에 서지 않는다
GRADE_NAME_LEVELS = {"고문": "P8"}
LEVEL_FORM = re.compile(r"^([A-Z])(\d+)$")
DIRECTORY_PATH = "/common/profile.nsf/ag_org_search_json?OpenAgent"
# 조직도 — 웹메일 받는 사람 고름 창이 부르는 손(orgtree.js · org_mail.js). 나무는 부서 코드 → 자식 부서, 구성원은 부서 코드 →
# 그 부서에 바로 든 사람, 배포그룹은 그룹 열쇠 → 구성원이다
ORG_DEPT_PATH = "/common/profile.nsf/ag_tree_dept_json?OpenAgent"
ORG_USER_PATH = "/common/profile.nsf/ag_tree_user_json?OpenAgent"
DISTRIBUTE_PATH = "/common/lib_f.nsf/agGetDistribute?openagent"
ORG_TREE_TYPE = "org"            # 고름 창의 「내 조직」 — 패밀리사 · 파트너사는 안 든다
ORG_EMPTY = "nothing"            # 구성원이 없는 부서의 답은 이 type 한 줄이다
GROUP_KINDS = ("jobtitle", "grade", "location")   # 배포그룹 탭의 고름 상자 값 — 직책 · 직급 · 지역(이 회사 코드의 꼴)
ORG_WORKERS = 8                  # 나무 · 구성원 · 보기를 함께 묻는 수 — 하나씩 물으면 전사 조직도가 부서 수만큼 기다린다
DUTY_SEPARATOR = "||"            # 업무 칸은 「업무||근무 꼴||휴무」 — 앞 조각이 업무다
# 받는 사람 목록이 사람을 드는 꼴 — Notes 이름(``CN=…/OU=…`` 또는 약식 ``이름/OU/O``) · ID(``<영문ID>(<약칭>)``)
NOTES_MARK = "CN="
ID_FORM = re.compile(r"^\s*([^\s()/@]+)\s*\(([^()]+)\)\s*$")

# ⚠ 읽음 표시를 바꾸는 명령 — 읽기 길은 이 주소를 짓지 않고, 지으려 하면 서버에 닿기 전에 막는다
MARKS_AS_READ = re.compile(r"[?&](opendocument|editdocument)\b", re.IGNORECASE)
# 메일함을 바꾸는 주소 전부 — 읽음으로 · 안 읽음으로(되돌리기) · 폴더 만들기 · 지우기 · 메일 옮기기 · 휴지통으로 · 되살리기 · 규칙
CHANGES_MAILBOX = re.compile(r"[?&](opendocument|editdocument)\b|/ag_read_cancel\b|/agt_mail_folder_save\b|/folder2\b"
                             r"|/trashdoc\b|/delete_view\b|/mailrule\b|/memo\b|/xam_upload\b", re.IGNORECASE)

# 폴더 나무 — 웹메일 화면이 폴더 고름 상자를 채우는 보기(JSON). 열은 경로 · 폴더 열쇠 · 부모 열쇠
FOLDER_TREE_VIEW = "fdd_folder_fullpath"
TREE_COLUMN_PATH, TREE_COLUMN_NODE, TREE_COLUMN_PARENT = "$6", "NodeUnid", "ParentID"
FOLDER_NODE = re.compile(r"^newNode\d{1,9}$")   # 폴더 열쇠 — 만드는 쪽이 짓고 서버가 그대로 쓴다
TOP_PARENT = "nofolder"                          # 맨 위 폴더를 만들 때의 부모 값 — 나무의 부모 열은 ``nodeATag<n>`` 이다
INBOX_NODE = "inbox"                             # 옮기기의 받는 자리 — 받은편지함
FOLDER_NAME_BANNED = re.compile(r"[\\\"'|_<>]")  # 화면이 막는 글자(mail_posco.js folder_add)
SYSTEM_FOLDER_NAMES = ("inbox", "sent", "draft", "drafts", "trash", "junk")   # 화면이 막는 이름 — 앞뒤 꾸밈(``$`` · ``imap`` · 괄호)까지
FOLDER_SAVE_AGENT = "agt_mail_folder_save"
MOVE_FORM = "folder2"
TRASH_AGENT = "TrashDoc"
TRASH_SEND_AGENT = "delete_view"                 # 웹메일 목록의 [삭제] — type 을 비우면 휴지통으로(type=remove 는 영구삭제라 안 짓는다)
TRASH_VIEW = "XML_Trash"                         # 휴지통 보기 — 보내기 뒤 다시 보는 자리

# 메일 규칙(받은 · 보낸 메일을 서버가 스스로 옮기는 기준) — 목록 보기 · 규칙 문서 · 저장 폼(fmmailrule.js)
RULE_VIEW = "XML_Rule"
RULE_FORM = "Mailrule"
RULE_BOXES = ("inbox", "sent")                         # 받은 메일 · 보낸 메일
RULE_ACTIONS = ("move_folder", "move_trash", "delete")  # 폴더로 이동 · 휴지통으로 · 영구삭제
RULE_FIELDS = ("from", "to", "cc", "subject", "attach")  # 보낸 사람 · 받는 사람 · 참조 · 제목 · 첨부 이름 — 폼 칸은 rule_<이것>
# 임시저장(웹메일 쓰기 화면의 [임시저장] 단추가 보내는 것 — fmmail_new.js saveDoc · xam_handler.js uploadFile)
MEMO_FORM = "Memo"                                  # 쓰기 화면 폼 — ``/<db>/Memo?openform`` 이 빈 폼, 같은 폼의 POST 가 저장
SAVE_AGENT_DRAFT = "wSave"                          # 저장 칸 SaveAgent 의 값 — 임시저장. ⚠ ``wSend`` 면 그 자리에서 발송된다
UPLOAD_DB = "upload/fileupload{digit}.nsf"          # 첨부 업로드 DB — 쓰는 사람 사번 끝자리로 나뉜다
UPLOAD_AGENT = "xam_upload?open"
DRAFT_COMPANY_CODE = "02"                           # 첨부 열쇠 가운데 회사 코드 — 쓰기 화면의 add_code
DRAFT_ATTACH_MOST = 20                              # 쓰기 화면의 첨부 개수 상한(attach_limit_count)
DRAFT_ATTACH_BIG = 20 * 1024 * 1024                 # 이보다 크면 웹메일이 대용량 전환한다(BigFileUserTransSize) — 임시저장은 대용량을 안 든다
DRAFT_UPLOAD_TIMEOUT = 180.0                        # 첨부 하나를 올리는 시한 — 대용량 상한(DRAFT_ATTACH_BIG) 안쪽 파일을 넉넉히 덮는다
# 메일속성 — 쓰기 화면의 체크 칸이 저장에 싣는 칸과 켠 값(saveDoc). 끈 값은 빈 글자, 긴급만 끈 값이 「2」다
DRAFT_URGENT = ("Importance", "1", "2")             # 긴급메일 — (칸, 켠 값, 끈 값)
DRAFT_NO_FORWARD = "Forward_Deny"                   # 전달불가 — 켜면 「1」
DRAFT_ONE_BY_ONE = "IndividualSend"                 # 한명씩 발송 — 켜면 「1」
DRAFT_SEND_AT = ("ReservationOpt", "SDay", "SHour", "SMin")   # 예약발송 — 켬 「1」 · 날짜(YYYY-MM-DD) · 시(두 자리) · 분(두 자리)
SEND_AT_STEP_IN_PAGE = re.compile(r'var\s+Reservation_Interval\s*=\s*"(\d+)"')   # 예약발송 분의 눈금 — 쓰기 화면의 분 고름 상자가 이 값으로 선다
# 서명 — 쓰기 화면의 설정 JSON 칸(fmmail_new.js getSignature)
SIGNATURE_ON = re.compile(r'"signatueYN"\s*:\s*"(\w*)"')              # 서명 쓰기 — 칸 이름 철자는 웹메일 그대로
SIGNATURE_ADD_LINE = re.compile(r'"signatue_add1line"\s*:\s*"(\w*)"')  # 서명 앞 빈 줄
SIGNATURE_UNID = re.compile(r'"signatureUnid"\s*:\s*"([0-9A-Fa-f]{32})"')
BLANK_LINE = "<p>&nbsp;</p>"                                          # 웹메일 편집기의 빈 줄
_UNID = re.compile(r"^[0-9A-Fa-f]{32}$")
_HEX32 = r"[0-9A-Fa-f]{32}"

log = logging.getLogger(__name__)


class MailboxError(Exception):
    """메일함을 못 읽었다. 메시지가 사유다."""


class MailboxConfigError(MailboxError):
    """설정이 틀렸다 — 주소 · 쿠키 파일 · 인자. 묻기 전에 잡힌다."""


class SessionMissing(MailboxConfigError):
    """세션(쿠키) 파일이 없거나 · 못 읽거나 · 쿠키가 하나도 없다 — 주소 · 인자를 고칠 일이 아니라 사내 세션을 다시 받을
    일이다(스킬 ep-login)."""


class SessionExpired(MailboxError):
    """세션이 끊겼다 — 다시 로그인해 쿠키 파일을 새로 남긴다(스킬 ep-login)."""


class DirectoryGap(MailboxError):
    """조직도가 물은 것을 못 줬다 — 회사 값으로 부서가 하나도 안 왔다. 빈 조직이 아니라 묻는 꼴이 틀린 쪽이다(조직도는 회사
    부서를 다 든다)."""


class ChangeRefused(MailboxError):
    """읽기 길이 메일함을 바꿀 주소(또는 읽기 전용으로 잰 꼴 밖의 주소)를 지었다 — 서버에 닿기 전에 막았다."""


class _Missing(MailboxError):
    """그 주소에 아무것도 없다(HTTP 404) — 본문 · 조각이 없는 메일."""


class _NotServed(MailboxError):
    """서버가 그 주소를 안 준다(HTTP 501) — 본문 주소에 501 을 내는 메일이 있다."""


@dataclass(frozen=True)
class Sender:
    """보낸 사람 열 하나를 푼 것. 밖의 메일은 주소만 차고 이름 · 영문 이름이 빈다."""
    name: str
    addr: str
    name_eng: str = ""


@dataclass(frozen=True)
class Recipient:
    """받는 사람 목록의 한 사람. 주소 없이 오는 사람은 ``notes`` 가 열쇠다 — Notes 이름(``CN=…/O=…``)이나 ``<ID>(<약칭>)``.

    ``kind`` 는 받는 사람 갈래(``PERSON_TYPE`` · ``DEPT_TYPE`` · ``GROUP_TYPE`` · ``EMAIL_TYPE`` · 모르면 빈 글자), ``field`` 는
    든 칸(``to`` · ``cc`` · ``bcc`` · 모르면 빈 글자)이다 — 보낸 메일 한 통의 받는 사람 칸(``Mailbox.sent_people``)만 채운다."""
    name: str
    addr: str
    notes: str = ""
    kind: str = ""
    field: str = ""


@dataclass(frozen=True)
class AttachmentName:
    """목록의 첨부 이름 하나. ECM 첨부면 ``ecm`` 이 참이고 원래 이름 · 확장자 · 크기를 이름에서 뽑는다 — 문서는 문서함에 있고
    ``Mailbox.ecm_key`` 가 그 열쇠를 꺼낸다.

    ``listed`` 는 목록이 준 글자 그대로다 — ``Mailbox.attachment`` 에는 이 값이나 이것 자체를 넘긴다.
    """
    listed: str
    name: str
    ext: str = ""
    size_kb: int | None = None
    ecm: bool = False


@dataclass(frozen=True)
class Entry:
    """받은편지함 · 폴더 목록의 한 줄. ``unid`` 가 그 메일의 열쇠다. ``folder`` 는 받은편지함이면 빈 글자, 폴더 보기면 그 경로
    (``부모\\자식``)다. 폴더 줄은 그 보기에 열이 없어 받는 꼴 · 중요도 · 관련 문서 · 보낸 분 주소가 비고 ``read_mark`` 가 회신함 ·
    전달함을 못 가린다 — ``Mailbox.list_all`` 로 채운다.
    """
    unid: str
    subject: str
    sender: Sender
    date: str              # xdate — YYYY-MM-DD HH:MM:SS (서울)
    date_sort: str         # $91 — YYYYMMDDTHHMMSS,cc+09
    size: str
    importance: str
    role: str              # xrtype — T · C · G · 빈 글자
    attachments: tuple[AttachmentName, ...]
    unread: bool
    read_mark: str
    related: str = ""
    folder: str = ""


@dataclass(frozen=True)
class Folder:
    """쓰는 사람이 지은 폴더 하나. ``path`` 는 보기 목록의 제목 그대로(``부모\\자식``) — 보기는 ``unid`` 로만 열린다."""
    unid: str
    path: str


@dataclass(frozen=True)
class FolderNode:
    """폴더 나무의 한 마디 — 바꾸는 손(만들기 · 옮기기 · 지우기)이 쓰는 열쇠. ``node`` 는 ``newNode<숫자>`` 꼴이고, ``path`` 는
    ``Folder.path`` 와 같은 ``부모\\자식`` 경로라 그 폴더의 보기(``Folder``)는 경로로 잇는다. ``parent`` 는 부모의 ``node`` —
    맨 위 폴더는 ``nodeATag<n>`` 이다."""
    node: str
    path: str
    parent: str


@dataclass(frozen=True)
class Rule:
    """메일 규칙 하나 — 서버가 들어오는(보내는) 메일에 스스로 적용한다. ``conditions`` 는 ``RULE_FIELDS`` 의 칸 → 글자
    (빈 칸은 안 든다), ``exact_from`` · ``exact_to`` 는 보낸 · 받는 사람 칸이 「일치」인가(거짓이면 「포함」)다. ``folder`` 는
    옮길 폴더의 경로(``move_folder`` 만), ``forwards`` 는 남에게 자동전달하는 규칙인가다."""
    unid: str
    box: str
    action: str
    folder: str
    conditions: dict
    exact_from: bool = False
    exact_to: bool = False
    forwards: bool = False


@dataclass(frozen=True)
class Marks:
    """모든편지함 한 줄에서 폴더 보기가 못 드는 칸 — 받는 꼴 · 중요도 · 보낸 분 · 읽음 열 글자 그대로. 시각은 창에서 끊는 데만 쓴다.
    폴더는 안 든다 — 이 보기의 폴더 열(``xfoldername``)은 폴더의 진본이 아니다.
    """
    unid: str
    date: str
    date_sort: str
    role: str
    importance: str
    sender: Sender
    read_mark: str


@dataclass(frozen=True)
class SentEntry:
    """보낸편지함 목록의 한 줄. 받는 사람은 그 목록의 수신인 열을 푼 것이다."""
    unid: str
    subject: str
    recipients: tuple[Recipient, ...]
    date: str


@dataclass(frozen=True)
class Found:
    """검색이 낸 한 줄. ``folder`` 는 검색 손이 준 폴더 이름(``[...]`` 를 벗긴 것 · 받은편지함 · 임시보관함 · 휴지통은 빈 글자 ·
    보낸편지함은 ``SENT_FOLDER``), ``draft`` 는 임시 저장된 메일이다. 시각은 검색 손이 준 글자 그대로(UTC)다. ``sender_eng`` 는
    보낸 사람 칸의 ``-ENG-`` 뒤(영문 이름) — 없으면 빈 글자다."""
    unid: str
    subject: str
    sender: str
    date: str
    folder: str
    attached: bool
    unread: bool
    draft: bool
    sender_eng: str = ""


@dataclass(frozen=True)
class DraftPerson:
    """임시메일의 받는 사람 하나 — ``notes`` 는 Notes 이름(SendTo 칸), ``email`` · ``name`` 은 InetSendTo 칸. ``notes`` 를 비우면
    웹메일 화면이 다시 열 때 사람으로 안 선다. ``dept`` 면 조직 하나다 — ``notes`` 는 부서 코드, ``email`` · ``name`` 은 부서 주소 · 이름.
    ``group`` 이면 배포그룹 하나다 — ``notes`` 는 그룹 열쇠, ``name`` 은 그룹 이름, ``email`` 은 빈 글자(보내는 순간의 구성원에게 간다).
    """
    notes: str
    email: str
    name: str
    dept: bool = False
    group: bool = False


@dataclass(frozen=True)
class DraftOptions:
    """임시메일의 메일속성 — 쓰기 화면의 체크 칸. ``send_at`` 은 예약발송 시각(``YYYY-MM-DD HH:MM`` · 분은 쓰기 화면의 눈금
    ``SEND_AT_STEP_IN_PAGE`` — ``save_draft`` 가 그 화면에서 읽어 가린다) · 빈 글자면 예약하지 않는다. 화면 손에 넘기는 ops 의 ``options`` 도 이 칸 이름 그대로다."""
    urgent: bool = False
    no_forward: bool = False
    one_by_one: bool = False
    send_at: str = ""

    def form(self) -> dict:
        """저장 폼에 실을 칸 — 쓰기 화면의 saveDoc 이 싣는 값 그대로다."""
        field, on, off = DRAFT_URGENT
        opt, day, hour, minute = DRAFT_SEND_AT
        out = {field: on if self.urgent else off, DRAFT_NO_FORWARD: "1" if self.no_forward else "",
               DRAFT_ONE_BY_ONE: "1" if self.one_by_one else "", opt: "", day: "", hour: "", minute: ""}
        if self.send_at:
            d, _, hm = self.send_at.partition(" ")
            h, _, m = hm.partition(":")
            out |= {opt: "1", day: d, hour: h, minute: m}
        return out


def people_info(fields: dict) -> str:
    """받는 사람 칸(``SENT_PEOPLE_FIELDS``) 하나의 글 — ``fields`` 는 칸(to · cc · bcc) → 받는 사람들. 배포그룹만 싣는다. 사람 · 조직은
    화면이 Notes 이름 · 부서 코드로 다시 세우지만, 배포그룹은 이 글이 없으면 열쇠만 남은 「기타」로 선다. 웹메일 화면이 짓는 꼴(열쇠
    ITEM {type, key, group_name, field})과 같다 — ``field`` 가 있어야 다시 읽을 때(``parse_sent_people``) 받는 사람 · 참조가 갈린다."""
    screen = {v: k for k, v in PEOPLE_FIELD_OF.items()}
    return PEOPLE_SEP.join(p.notes + PEOPLE_ITEM + json.dumps({"type": GROUP_TYPE, "key": p.notes, "group_name": p.name,
                                                               "field": screen[f]}, ensure_ascii=False)
                           for f, people in fields.items() for p in people if p.group)


@dataclass(frozen=True)
class DraftFile:
    """임시메일에 붙일 파일 하나 — 이름과 바이트."""
    name: str
    data: bytes


@dataclass(frozen=True)
class DirectoryPerson:
    """사내 주소록의 한 사람. ``notes`` 는 Notes 이름(``key``) — 받는 사람 목록에서 그 사람을 알아보는 열쇠다.

    ``dept_code`` · ``grade_code`` · ``job_title_code`` 는 주소록이 준 글자 그대로, ``is_boss`` 는 주소록의 장 여부다.
    ``grade`` 는 직급(차장 · 상무보 …), ``job_title`` 은 직책(일반 · 리더 · 그룹장 …)이다.
    """
    email: str
    name: str
    name_eng: str
    notes: str
    user_id: str
    empno: str
    dept: str
    grade: str
    job_title: str
    company: str
    retired: bool
    dept_code: str = ""
    grade_code: str = ""
    is_boss: bool = False
    job_title_code: str = ""
    location: str = ""
    duty: str = ""

    @property
    def level(self) -> str:
        """인사 등급(``P5`` · ``E3`` …) — 직급 코드의 표가 먼저이고, 코드가 표에 없으면 직급 이름의 표를 본다. 둘 다 없으면 빈 글자."""
        return GRADE_LEVELS.get(self.grade_code) or GRADE_NAME_LEVELS.get(self.grade.strip(), "")


def level_at_least(level: str, floor: str) -> bool:
    """``level`` 이 ``floor`` 와 같은 갈래(P · E)이고 그 이상인가. 등급이 없으면 거짓이다."""
    a, b = LEVEL_FORM.match(level or ""), LEVEL_FORM.match(floor.strip().upper())
    if not b:
        raise MailboxConfigError(f"등급은 P5 · E3 꼴이다: {floor!r}")
    return bool(a) and a.group(1) == b.group(1) and int(a.group(2)) >= int(b.group(2))


@dataclass(frozen=True)
class Dept:
    """조직도의 한 부서. ``code`` 는 ``<코드>(<회사 약칭>)`` 꼴의 열쇠, ``parent`` 는 위 부서의 코드(맨 위 부서는 회사 값)다.
    ``email`` 은 그 부서 자체로 가는 주소다."""
    code: str
    name: str
    depth: int
    parent: str
    has_child: bool
    email: str


# ── 세션 ─────────────────────────────────────────────────────────────────

def discover_mailbox(server: str, cookies_file, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """그 세션에 로그인한 사람의 메일함 주소(``<서버>/<경로>.nsf``)를 메일 서버 첫 화면에서 받는다 — 사람에게 묻지 않는다.

    첫 화면에 메일 파일 경로가 없으면(끊긴 세션의 SSO 화면) ``SessionExpired``, 서버에 못 닿으면 ``MailboxError``. 읽음 표시를 안 바꾼다.
    """
    root = server.strip().rstrip("/")
    if not re.match(r"^https?://[^/]+$", root, re.IGNORECASE):
        raise MailboxConfigError(f"메일 서버 주소(http://<호스트>)가 아니다: {server!r}")
    jar = ep_session.load_jar(cookies_file, missing=SessionMissing)
    opener = ep_session.opener(jar)
    try:
        with opener.open(root + "/", timeout=timeout) as response:
            text = response.read().decode(_charset(response.headers.get("Content-Type", "")), errors="replace")
    except ep_session.Redirected as exc:
        raise SessionExpired(f"세션이 끊겼다(→ {exc.location}) — 다시 로그인한다") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise MailboxError(f"메일 서버에 못 닿았다: {exc}") from exc
    found = MAILFILE_IN_ROOT.search(text)
    if not found:
        raise SessionExpired("메일 서버 첫 화면에 메일 파일 경로가 없다 — 세션이 끊겼다(다시 로그인한다)")
    return f"{root}/{found.group(1).lstrip('/')}"


class Mailbox:
    """메일함 하나. 읽기 길의 손은 다 읽기 전용이다 — 메일함을 바꾸는 손은 머리말 「무엇을 하나」 의 이름 붙은 함수들뿐이다."""

    def __init__(self, url: str, cookies_file, *, view: str = INBOX_VIEW, timeout: float = DEFAULT_TIMEOUT):
        """``url`` 은 ``…/<이름>.nsf`` 까지 든 메일함 주소(그 뒤는 버린다), ``view`` 는 ``list`` 가 읽는 받은편지함 보기다.

        주소가 틀리면 묻기 전에 ``MailboxConfigError``, 쿠키 파일이 없거나 못 읽거나 비었으면 그 갈래인 ``SessionMissing``.
        """
        match = re.match(r"^(https?://[^/]+)(/.+?\.nsf)", url.strip(), re.IGNORECASE)
        if not match:
            raise MailboxConfigError(f"메일함 주소(…/이름.nsf)가 아니다: {url!r}")
        self.server, self.db_path = match.group(1), match.group(2)
        self.base = self.server + self.db_path
        self.view = view
        self.timeout = timeout
        self._collections: list[dict] | None = None
        jar = ep_session.load_jar(cookies_file, missing=SessionMissing)
        self._opener = ep_session.opener(jar)   # 리다이렉트는 안 따라간다 — 따라가면 쿠키가 SSO 에 실린다
        self._read_only = read_only_patterns(self.db_path)

    @classmethod
    def from_env(cls) -> Mailbox:
        """환경변수로 세운다(머리말 「환경변수」). 틀린 값이면 MailboxConfigError."""
        url = os.environ.get("MAILBOX_URL", "").strip()
        if not url:
            raise MailboxConfigError("MAILBOX_URL 이 비어 있다 — 웹메일 주소의 …/이름.nsf 까지 준다")
        timeout_raw = os.environ.get("MAILBOX_TIMEOUT_SECONDS", "").strip() or str(DEFAULT_TIMEOUT)
        try:
            timeout = float(timeout_raw)
        except ValueError:
            timeout = 0.0
        if timeout <= 0:
            raise MailboxConfigError(f"MAILBOX_TIMEOUT_SECONDS 가 양수가 아니다: {timeout_raw!r}")
        return cls(url, os.environ.get("MAILBOX_COOKIES", "").strip() or DEFAULT_COOKIES,
                   view=os.environ.get("MAILBOX_VIEW", "").strip() or INBOX_VIEW, timeout=timeout)

    # ── 묻기 ────────────────────────────────────────────────────────────

    def _get(self, path: str) -> tuple[bytes, str]:
        """읽기 길의 GET — 메일함 안의 ``path``(``/`` 로 시작한다). 서버 뿌리 아래(주소록 · 세션 확인)는 ``_get_server``.

        내는 것 — (본문, content-type). 읽기 전용으로 잰 꼴이 아니면 묻지 않고 ``ChangeRefused``.
        """
        return self._fetch_read_only(self.db_path + path)

    def _get_server(self, path: str) -> tuple[bytes, str]:
        """읽기 길의 GET — 메일함 밖, 같은 서버의 ``path``(주소록 · 세션 확인)."""
        return self._fetch_read_only(path)

    def _fetch_read_only(self, path: str) -> tuple[bytes, str]:
        url = self.server + path
        if MARKS_AS_READ.search(path):
            raise ChangeRefused(f"읽음 표시를 바꾸는 주소라 묻지 않는다: {url}")
        if CHANGES_MAILBOX.search(path):
            raise ChangeRefused(f"메일함을 바꾸는 주소라 묻지 않는다: {url}")
        if not any(p.match(path) for p in self._read_only):
            raise ChangeRefused(f"읽기 전용으로 잰 주소 꼴이 아니라 묻지 않는다: {url}")
        return self._open(url)

    def _open(self, url: str | urllib.request.Request) -> tuple[bytes, str]:
        request, url = url, url.full_url if isinstance(url, urllib.request.Request) else url
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except ep_session.Redirected as exc:
            raise SessionExpired(f"세션이 끊겼다(→ {exc.location}) — 다시 로그인한다") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise SessionExpired(f"메일 서버가 거절했다(HTTP {exc.code}) — 다시 로그인한다") from exc
            if exc.code == 404:
                raise _Missing(url) from exc
            if exc.code == HTTP_NOT_SERVED:
                raise _NotServed(f"메일 서버가 HTTP {exc.code} 를 냈다: {url}") from exc
            raise MailboxError(f"메일 서버가 HTTP {exc.code} 를 냈다: {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise MailboxError(f"메일 서버에 못 닿았다: {exc}") from exc

    def _view(self, name_or_unid: str, count: int, start: int, *, descending: bool = False) -> ET.Element:
        query = f"?ReadViewEntries&count={int(count)}&start={int(start)}" + ("&ResortDescending=1" if descending else "")
        body, kind = self._get(f"/{urllib.parse.quote(name_or_unid)}{query}")
        if "xml" not in kind.lower():
            raise SessionExpired(f"목록 대신 {kind or '알 수 없는 꼴'} 가 왔다 — 세션이 끊긴 것이다")
        try:
            return ET.fromstring(body)
        except ET.ParseError as exc:
            raise MailboxError(f"목록 XML 을 못 읽었다: {exc}") from exc

    def list(self, count: int = 30, start: int = 1) -> list[Entry]:
        """받은편지함을 새것부터 ``count`` 통. ``start`` 는 1 부터 센 자리. 하위 폴더로 옮긴 메일은 안 든다(``list_folder``)."""
        root = self._view(self.view, count, start)
        entries = [_entry(e) for e in root.iter("viewentry")]
        log.info("받은편지함 목록: %d통 · 안 읽음 %d", len(entries), sum(e.unread for e in entries))
        return entries

    def list_sent(self, count: int = 30, start: int = 1) -> list[SentEntry]:
        """보낸편지함을 ``count`` 통. 받는 사람은 그 목록의 수신인 열을 푼다."""
        root = self._view(SENT_VIEW, count, start)
        entries = [SentEntry(unid=e.get("unid", ""), subject=_column(e, COLUMN_SUBJECT),
                             recipients=parse_people(_column(e, SENT_COLUMN_TO)), date=_column(e, COLUMN_DATE))
                   for e in root.iter("viewentry")]
        log.info("보낸편지함 목록: %d통", len(entries))
        return entries

    def sent_people(self, unid: str) -> tuple[Recipient, ...]:
        """보낸 메일 한 통의 받는 사람 · 참조 · 숨은참조 모두 — 웹메일이 넣은 차례대로, 조직은 조직 하나로(``kind`` 가 ``dept``).

        그 메일의 받는 사람 칸(``SENT_PEOPLE_FIELDS``)을 푼다. 숨은참조 칸은 보내면 웹메일이 걷어 404 · 501 로 오니, 숨은참조가 든
        것은 그 칸이 남은 메일뿐이고 빈 숨은참조는 「없었다」가 아니라 「모른다」다. 받는 사람 · 참조 칸이 없으면(404 · 501) 이 꼴로
        저장되지 않은 메일이라 ``MailboxError`` — 빈 명단으로 내면 「지난번과 같이」가 아무도 없이 선다.
        """
        out: list[Recipient] = []
        for name in SENT_PEOPLE_FIELDS:
            try:
                body, kind = self._get(f"/0/{_unid(unid)}/{name}?OpenField")
            except (_Missing, _NotServed) as exc:
                if name == SENT_PEOPLE_FIELDS[0]:
                    raise MailboxError(f"그 메일에 받는 사람 칸({name})이 없다 — 웹메일 편집 화면으로 쓴 메일이 아니다: {unid}") from exc
                continue
            text = body.decode(_charset(kind), errors="replace")
            if _looks_like_login(text):
                raise SessionExpired("받는 사람 칸 대신 로그인 페이지가 왔다 — 다시 로그인한다")
            out += parse_sent_people(text, default_field="bcc" if name == SENT_PEOPLE_FIELDS[1] else "")
        log.info("보낸 메일의 받는 사람: %d", len(out))
        return tuple(out)

    def _view_list(self) -> list[dict]:
        """보기 목록(``/api/data/collections``) — 이 메일함 손이 사는 동안 한 번만 받는다."""
        if self._collections is None:
            body, kind = self._get("/api/data/collections")
            text = body.decode(_charset(kind), errors="replace")
            try:
                views = json.loads(text)
            except json.JSONDecodeError as exc:
                if _looks_like_login(text):
                    raise SessionExpired("보기 목록 대신 로그인 페이지가 왔다 — 다시 로그인한다") from exc
                raise MailboxError(f"보기 목록 JSON 을 못 읽었다: {exc}") from exc
            if not isinstance(views, list):
                raise MailboxError("보기 목록이 배열이 아니다")
            self._collections = [v for v in views if isinstance(v, dict)]
        return self._collections

    def view_unid(self, title: str) -> str | None:
        """보기 제목으로 그 보기의 unid 를 찾는다 — 메일함마다 다를 수 있어 보기 목록에서 받는다. 없으면 None.

        폴더는 뺀다 — 쓰는 사람이 보기와 같은 이름의 폴더를 지어도 그 폴더를 보기로 읽지 않게.
        """
        unid = next((str(v.get("@unid") or "") for v in self._view_list()
                     if v.get("@title", "") == title and not _is_folder(v)), "")
        return unid if _UNID.match(unid) else None

    def folders(self) -> list[Folder]:
        """쓰는 사람이 지은 폴더 — 보기 목록의 폴더 가운데 시스템 폴더(제목이 ``(`` 로 시작)를 뺀 것, 경로 차례로."""
        found: dict[str, Folder] = {}
        for v in self._view_list():
            title, unid = str(v.get("@title") or ""), str(v.get("@unid") or "")
            if _is_folder(v) and title.strip() and not title.startswith(SYSTEM_FOLDER_MARK) and _UNID.match(unid):
                found.setdefault(unid, Folder(unid=unid, path=title))
        folders = sorted(found.values(), key=lambda f: folder_order(f.path))
        log.info("폴더: %d개", len(folders))
        return folders

    def list_folder(self, folder: Folder, count: int = 30, start: int = 1) -> list[Entry]:
        """그 폴더를 새것부터 ``count`` 통 — 줄마다 ``folder`` 에 그 폴더의 경로를 싣는다. 받는 꼴 · 중요도 · 보낸 분 주소 · 회신함 ·
        전달함 표시는 빈다(``list_all``) · 안 읽음은 읽음 열의 class 로 선다."""
        if not _UNID.match(folder.unid or ""):
            raise MailboxConfigError("폴더 보기는 unid 로만 연다 — 제목으로 열면 0줄이 온다")
        root = self._view(folder.unid, count, start)
        entries = [_entry(e, folder=folder.path) for e in root.iter("viewentry")]
        log.info("폴더 목록: %d통 · 안 읽음 %d", len(entries), sum(e.unread for e in entries))
        return entries

    def list_sent_mail(self, count: int = 30, start: int = 1) -> list[Entry]:
        """보낸편지함을 받은편지함과 같은 ``Entry`` 꼴로 — 줄의 ``folder`` 는 ``SENT_FOLDER``, ``sender`` 는 그 보기의 수신인 열
        (받는 사람)이다. 메일 한 통을 unid 로 찾아 읽는 쪽이 쓴다 — 받는 사람을 갈라 보려면 ``list_sent``."""
        root = self._view(SENT_VIEW, count, start)
        return [_entry(e, folder=SENT_FOLDER) for e in root.iter("viewentry")]

    def list_trash(self, count: int = 30, start: int = 1) -> list[Entry]:
        """휴지통(``XML_Trash``)을 ``count`` 통 — 줄의 ``folder`` 는 ``TRASH_FOLDER`` 다. 열은 받은편지함과 같은 꼴이다(제목 · 보낸 분)."""
        root = self._view(TRASH_VIEW, count, start)
        entries = [_entry(e, folder=TRASH_FOLDER) for e in root.iter("viewentry")]
        log.info("휴지통 목록: %d통", len(entries))
        return entries

    def list_drafts(self, count: int = 30, start: int = 1) -> list[Entry] | None:
        """임시보관함을 새것부터 ``count`` 통 — 줄의 ``folder`` 는 ``(Drafts)`` 다. 보기가 이 메일함에 없으면 None.

        보낸 사람 열은 쓰는 사람 자신이다(받은편지함과 같은 꼴). 받는 꼴 · 첨부 열은 그 보기가 안 든다.
        """
        unid = self.view_unid(DRAFT_VIEW_TITLE)
        if unid is None:
            log.warning("임시보관함 보기가 이 메일함에 없다")
            return None
        root = self._view(unid, count, start)
        entries = [_entry(e, folder=DRAFTS_FOLDER) for e in root.iter("viewentry")]
        log.info("임시보관함 목록: %d통", len(entries))
        return entries

    def search(self, words: str, *, scope: str = "all", field: str = "subject",
               count: int = 30, page: int = 1) -> tuple[int, list[Found]]:
        """웹메일 검색 창과 같은 검색 — ``field``(제목 · 본문 · 첨부 이름) 한 칸에 ``words`` 가 든 메일. 내는 것 — (서버가 센
        모두 건수, 이 쪽의 줄). 읽음 표시를 안 바꾼다.

        한 번에 한 칸이다 — 검색 손은 칸을 여럿 주면 그 칸을 다 든 메일만 낸다. 여러 칸 · 여러 범위를 합치는 일은
        부르는 쪽이 unid 로 한다. ``scope`` 는 ``SEARCH_SCOPES`` 의 하나 — ``all`` 은 임시보관함을 안 든다. 줄은 새것부터다.
        """
        if scope not in SEARCH_SCOPES:
            raise MailboxConfigError(f"검색 범위가 아니다: {scope!r} — {', '.join(SEARCH_SCOPES)}")
        if field not in SEARCH_FIELDS:
            raise MailboxConfigError(f"검색 칸이 아니다: {field!r} — {', '.join(SEARCH_FIELDS)}")
        if not words.strip():
            raise MailboxConfigError("검색어가 비었다")
        count = max(1, min(int(count), SEARCH_PAGE_MOST))
        query = {"page": str(max(1, int(page))), "count": str(count), "mbox": scope, "stype": "chatbot",
                 SEARCH_SLOTS[field]: words.strip()}
        body, kind = self._get(f"/{SEARCH_AGENT}?open&" + urllib.parse.urlencode(query, quote_via=urllib.parse.quote))
        text = body.decode(_charset(kind) if "charset" in kind.lower() else "utf-8", errors="replace")
        if not text.strip():
            return 0, []    # 검색 손은 받은 칸이 없거나 맞는 꼴이 아니면 빈 답을 준다
        try:
            answer = json.loads(text)
        except json.JSONDecodeError as exc:
            if _looks_like_login(text):
                raise SessionExpired("검색 대신 로그인 페이지가 왔다 — 다시 로그인한다") from exc
            raise MailboxError(f"검색 답 JSON 을 못 읽었다: {exc}") from exc
        rows = answer.get("data") if isinstance(answer, dict) else None
        if not isinstance(rows, list):
            raise MailboxError("검색 답에 목록이 없다")
        found = [_found(r) for r in rows if isinstance(r, dict) and _UNID.match(str(r.get("unid") or ""))]
        total = int(answer.get("total") or 0) if str(answer.get("total") or "0").isdigit() else len(found)
        log.info("검색: 범위 %s · 모두 %d건 · 이 쪽 %d줄", scope, total, len(found))
        return total, found

    def list_all(self, count: int = 30, start: int = 1) -> list[Marks] | None:
        """모든편지함을 정렬 없이 ``count`` 줄 — 그 꼴이 날짜 내림차순이다. 받는 꼴 · 중요도 · 보낸 분 · 읽음 열을 낸다. 보기가 이
        메일함에 없으면 None."""
        unid = self.view_unid(ALL_VIEW_TITLE)
        if unid is None:
            log.warning("모든편지함 보기가 이 메일함에 없다 — 폴더 메일의 받는 꼴 · 중요도 · 보낸 분 주소 없이 돈다")
            return None
        root = self._view(unid, count, start)
        marks = [Marks(unid=e.get("unid", ""), date=_column(e, COLUMN_DATE), date_sort=_column(e, COLUMN_DATE_SORT),
                       role=_column(e, COLUMN_ROLE).upper(), importance=_column(e, COLUMN_IMPORTANCE),
                       sender=parse_sender(_column(e, COLUMN_FROM)), read_mark=_column(e, COLUMN_READ))
                 for e in root.iter("viewentry")]
        log.info("모든편지함: %d줄", len(marks))
        return marks

    def recipient_lists(self, count: int) -> dict[str, tuple[Recipient, ...]] | None:
        """받는 사람 목록 보기를 날짜 내림차순으로 한 장(``count`` 줄) 받아 unid → 받는 사람 목록을 낸다.

        보기가 이 메일함에 없으면 None — 부르는 쪽은 목록 없이 돈다. 받은 것 · 보낸 것이 섞여 오고 둘 다 낸다.
        """
        unid = self.view_unid(RECIPIENT_VIEW_TITLE)
        if unid is None:
            log.warning("받는 사람 목록 보기가 이 메일함에 없다 — 목록 없이 돈다")
            return None
        root = self._view(unid, count, 1, descending=True)
        lists = {e.get("unid", ""): parse_people(_column(e, VIEW_COLUMN_TO)) for e in root.iter("viewentry")}
        log.info("받는 사람 목록: %d줄", len(lists))
        return lists

    def body(self, mail: Entry | str, kind: str = "html") -> str | None:
        """본문 — ``kind`` 는 "html"(기본 · 조각 꼴과 상관없는 한 길) · "text"(평문 조각). 그 꼴의 본문이 없거나 서버가 그 주소를
        안 주면(501) None.

        끊긴 세션의 로그인 화면이 오면 어느 꼴이든 ``SessionExpired`` 다 — 「본문 없음」으로 낮추지 않는다.
        """
        if kind not in BODY_KINDS:
            raise MailboxConfigError(f"본문 꼴은 {' · '.join(BODY_KINDS)} 가운데 하나다: {kind!r}")
        unid = _unid(mail)
        path = f"/0/{unid}/Body?OpenField" if kind == "html" else f"/0/{unid}/Body/{BODY_TEXT_PART}?OpenElement"
        try:
            data, content_type = self._get(path)
        except _Missing:
            return None
        except _NotServed:
            log.warning("본문 주소에 서버가 501 을 냈다 — 그 메일은 본문 없이 둔다")
            return None
        text = data.decode(_charset(content_type), errors="replace")
        if _looks_like_login(text):
            raise SessionExpired("본문 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        if kind == "text" and "text/plain" not in content_type.lower():
            return None   # 평문 조각 자리에 다른 꼴이 왔다 — multipart/related 처럼 평문 조각이 없는 메일
        return text

    def attachment(self, mail: Entry | str, name: AttachmentName | str) -> bytes:
        """메일에 바로 붙은 첨부 하나를 바이트 그대로 받는다. ``name`` 은 ``AttachmentName`` 이나 목록이 준 이름 그대로다.

        ECM 첨부(``AttachmentName.ecm``)는 문서가 아니라 문서함을 가리키는 쪽지라 바이트로 내지 않는다 — ``MailboxConfigError``.
        그 문서는 ``ecm_key`` 가 꺼낸 열쇠로 연다.
        """
        listed = name.listed if isinstance(name, AttachmentName) else name
        if ECM_ATTACHMENT.match(listed):
            raise MailboxConfigError("ECM 첨부는 문서함을 가리키는 쪽지다 — ecm_key 로 문서 열쇠를 꺼내 문서함에서 연다")
        data, content_type = self._get(f"/0/{_unid(mail)}/$FILE/{urllib.parse.quote(listed)}")
        if "text/html" in content_type.lower() and _looks_like_login(data.decode("utf-8", "replace")):
            raise SessionExpired("첨부 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        log.info("첨부: %d bytes", len(data))
        return data

    def body_image(self, src: str) -> bytes:
        """본문 ``<img src>`` 하나를 받는다 — 이 메일 서버의 읽기 전용으로 잰 주소(본문 조각 ``Body/M…?OpenElement`` 등)만 묻는다.
        다른 호스트 · 잰 꼴 밖의 주소면 묻지 않고 ``ChangeRefused``. 로그인 화면이 오면 ``SessionExpired``."""
        url = urllib.parse.urljoin(self.server + self.db_path + "/", src.strip())
        parts = urllib.parse.urlsplit(url)
        if f"{parts.scheme}://{parts.netloc}".lower() != self.server.lower():
            raise ChangeRefused(f"메일 서버 밖의 그림이라 묻지 않는다: {parts.hostname}")
        if any(seg in (".", "..") for seg in urllib.parse.unquote(parts.path).split("/")):
            # 잰 꼴의 머리만 맞추고 「..」 로 다른 문서 · 다른 DB 로 올라가는 주소 — 서버가 풀면 울타리 밖을 묻게 된다
            raise ChangeRefused("경로에 「..」 이 든 그림 주소라 묻지 않는다")
        data, content_type = self._fetch_read_only(parts.path + (f"?{parts.query}" if parts.query else ""))
        if "text/html" in content_type.lower() and _looks_like_login(data.decode("utf-8", "replace")):
            raise SessionExpired("그림 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        return data

    def ecm_key(self, mail: Entry | str, name: AttachmentName | str) -> str:
        """ECM 첨부 하나가 가리키는 문서함 문서의 열쇠(16 hex 글자)를 낸다(``ecm_note_key``). ECM 첨부가 아니면
        ``MailboxConfigError``, 쪽지에 머리나 열쇠가 없으면 ``MailboxError`` — 꼴이 바뀌었거나 다른 쪽지다.
        """
        listed = name.listed if isinstance(name, AttachmentName) else name
        if not ECM_ATTACHMENT.match(listed):
            raise MailboxConfigError(f"ECM 첨부가 아니다 — attachment 로 받는다: {listed!r}")
        # 머리를 먼저 본다 — 쪽지는 다른 주소로 넘기는 스크립트 페이지라, 로그인 화면 판정은 머리가 없을 때만 한다
        data, _ = self._get(f"/0/{_unid(mail)}/$FILE/{urllib.parse.quote(listed)}")
        text = data.decode("utf-8", "replace")
        key = ecm_note_key(text)
        if not key:
            if _looks_like_login(text):
                raise SessionExpired("ECM 첨부 대신 로그인 페이지가 왔다 — 다시 로그인한다")
            raise MailboxError("ECM 첨부의 머리에 문서 열쇠(objectId)가 없다 — 쪽지 꼴이 잰 것과 다르다")
        log.info("ECM 첨부: 열쇠를 꺼냈다")
        return key

    def session_alive(self) -> bool:
        """메일을 안 건드리고 세션이 살아 있나 묻는다 — 웹메일이 수십 초마다 부르는 주소다. 살아 있으면 참.

        서버에 못 닿으면 ``MailboxError`` — 「끊겼다」와 「못 물었다」를 가른다.
        """
        try:
            data, kind = self._get_server("/common/lib_f.nsf/checksessionstatus?Openpage")
        except (SessionExpired, _Missing):
            return False
        try:
            answer = json.loads(data.decode(_charset(kind), errors="replace"))
        except json.JSONDecodeError:
            return False
        return isinstance(answer, dict) and answer.get("status") == "login"

    def directory_answer(self, search_key: str, company: str, *, category: str = "") -> dict:
        """사내 주소록의 답을 그대로 낸다(``{dept, user, total}``) — 주소록에 묻는 한 길이고, 안 잰 꼴을 회사에서 재는 자리다.

        ``company`` 는 조직도 고름 상자의 값(``<회사>(<코드>)``)이고 메일함마다 다르다 — 부르는 쪽이 설정에서 넘긴다. ``category`` 는
        웹메일이 빈 값으로 보내는 칸이다. 답이 dict 가 아니면 ``MailboxError``.
        """
        if not search_key.strip() or not company.strip():
            raise MailboxConfigError("주소록 찾기에는 찾을 말과 회사 값이 다 있어야 한다")
        query = urllib.parse.urlencode({
            "type": "org", "dbpath": self.db_path.lstrip("/"), "company": company, "category": category,
            "search_key": search_key, "date": str(int(time.time() * 1000))}, safe="()")
        data, kind = self._get_server(f"{DIRECTORY_PATH}&{query}")
        text = data.decode(_charset(kind), errors="replace")
        try:
            answer = json.loads(text)
        except json.JSONDecodeError as exc:
            if _looks_like_login(text):
                raise SessionExpired("주소록 대신 로그인 페이지가 왔다 — 다시 로그인한다") from exc
            raise MailboxError(f"주소록 JSON 을 못 읽었다: {exc}") from exc
        if not isinstance(answer, dict):
            raise MailboxError(f"주소록 답이 {{dept, user, total}} 꼴이 아니다: {type(answer).__name__}")
        return answer

    def find_people(self, search_key: str, company: str, *, category: str = "") -> list[DirectoryPerson]:
        """사내 주소록에서 이름 · 메일 · 사번으로 찾는다. 밖의 주소는 빈 목록이다 — 「사내 사람인가」로도 쓴다."""
        users = self.directory_answer(search_key, company, category=category).get("user") or []
        return [_person(u) for u in users if isinstance(u, dict)]

    def find_exact(self, handle: str, company: str) -> list[DirectoryPerson]:
        """받는 사람 목록 · 보낸 사람의 한 꼴로 그 사람만 찾는다 — 주소면 메일이, Notes 이름이면 ``key`` 의 견줄 꼴이, ID
        (``<영문ID>(<약칭>)``)면 ``user_id`` 가 같은 사람만 낸다. 하나면 그 사람이고, 둘 넘게면 잇지 않는다(부르는 쪽이 가른다).
        이름 · 사번은 그 글자가 같은 사람이다 — 같은 이름이 여럿이면 다 낸다. 찾을 말을 못 짓는 꼴이면 빈 목록이다.

        이름 찾기의 답에는 이름이 같은 다른 사람과 이름에 그 글자가 든 사람이 섞여 온다 — 이 걸러내기 없이 첫 줄을 쓰면 다른
        사람에게 간다.
        """
        query = directory_query(handle)
        if query is None:
            return []
        word, same = query
        return [p for p in self.find_people(word, company) if same(p)]

    # ── 조직도 — 웹메일 고름 창의 나무 · 구성원 · 배포그룹 ───────────────────────────────

    def _org_json(self, path: str, **query: str):
        """조직도 손 하나에 묻고 JSON 을 낸다. 로그인 화면이면 ``SessionExpired``, JSON 이 아니면 ``MailboxError``."""
        query["date"] = str(int(time.time() * 1000))
        data, kind = self._get_server(f"{path}&{urllib.parse.urlencode(query, safe='()')}")
        text = data.decode(_charset(kind), errors="replace")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            if _looks_like_login(text):
                raise SessionExpired("조직도 대신 로그인 페이지가 왔다 — 다시 로그인한다") from exc
            raise MailboxError(f"조직도 JSON 을 못 읽었다({path}): {exc}") from exc

    def org_children(self, dept: str, company: str) -> list[Dept]:
        """그 부서 바로 아래 부서들 — ``dept`` 에 회사 값을 주면 맨 위 부서들이다. 답의 꼴이 다르면 ``MailboxError``."""
        answer = self._org_json(ORG_DEPT_PATH, company=company, root=company, dept=dept, type=ORG_TREE_TYPE)
        rows = answer.get("result") if isinstance(answer, dict) else None
        if not isinstance(rows, list):
            raise MailboxError(f"조직도 나무 답이 {{result: [...]}} 꼴이 아니다: {str(answer)[:200]}")
        return [Dept(code=r.get("key") or "", name=r.get("dept_name") or "", depth=int(r.get("depth") or 0),
                     parent=dept, has_child=str(r.get("has_child") or "").upper() in DIRECTORY_YES,
                     email=r.get("email") or "")
                for r in rows if isinstance(r, dict) and r.get("type") == "dept"]

    def org_members(self, dept: str) -> list[DirectoryPerson]:
        """그 부서에 바로 든 사람(하위 부서 사람은 안 든다) — 조직도에서 부서를 누를 때의 명단이다. 사람의 ``dept_code`` 는
        이 부서 코드다. 구성원이 없는 부서는 빈 목록이다(답은 ``type`` 이 ``ORG_EMPTY`` 인 한 줄)."""
        answer = self._org_json(ORG_USER_PATH, dept=dept, type=ORG_TREE_TYPE)
        rows = answer.get("result") if isinstance(answer, dict) else None
        if not isinstance(rows, list):
            raise MailboxError(f"조직도 구성원 답이 {{result: [...]}} 꼴이 아니다: {str(answer)[:200]}")
        return [_person({**r, "dept_code": dept}) for r in rows if isinstance(r, dict) and r.get("type") == "user"]

    def org_snapshot(self, company: str) -> OrgChart:
        """회사 조직 전체 — 나무를 층마다 펼치고 부서마다 구성원을 받는다(``ORG_WORKERS`` 만큼 함께). 부서가 하나도 안 오면
        ``DirectoryGap`` — 회사 값이 틀린 쪽이다."""
        depts: dict[str, Dept] = {}
        frontier = [company]
        with ThreadPoolExecutor(ORG_WORKERS) as pool:
            while frontier:
                found = [d for kids in pool.map(lambda c: self.org_children(c, company), frontier) for d in kids
                         if d.code and d.code not in depts]
                depts.update((d.code, d) for d in found)
                frontier = [d.code for d in found if d.has_child]
            if not depts:
                raise DirectoryGap(f"조직도가 회사 「{company}」 의 부서를 하나도 안 줬다 — 회사 값을 확인한다")
            members = dict(zip(depts, pool.map(self.org_members, depts)))
        return OrgChart(company=company, depts=depts, members=members)

    def org_groups(self, company: str, kind: str) -> list[tuple[str, str]]:
        """배포그룹 목록 — ``kind`` 는 ``GROUP_KINDS`` 가운데 하나. (그룹 열쇠, 이름) 을 낸다."""
        if kind not in GROUP_KINDS:
            raise MailboxConfigError(f"배포그룹 갈래는 {GROUP_KINDS} 가운데 하나다: {kind!r}")
        answer = self._org_json(DIRECTORY_PATH, type="group", company=company, group_type=kind, group_text=kind)
        rows = answer.get("group") if isinstance(answer, dict) else None
        if not isinstance(rows, list):
            raise MailboxError(f"배포그룹 답이 {{group: [...]}} 꼴이 아니다: {str(answer)[:200]}")
        return [(r.get("key") or "", r.get("group_name") or "") for r in rows if isinstance(r, dict)]

    def group_members(self, group_key: str) -> list[tuple[str, str, str, str]]:
        """배포그룹 하나의 구성원 — (이름, 직급, 부서, 메일). 답이 ``ok`` 가 아니면 ``MailboxError``."""
        answer = self._org_json(DISTRIBUTE_PATH, groupname=group_key)
        if not isinstance(answer, dict) or answer.get("result") != "ok":
            raise MailboxError(f"배포그룹 「{group_key}」 구성원을 못 받았다: {str(answer)[:200]}")
        return [(m.get("name") or "", m.get("grade") or "", m.get("deptname") or "", m.get("email") or "")
                for m in answer.get("memberlist") or [] if isinstance(m, dict)]

    # ── 메일함을 바꾸는 손 — 사람이 그 메일 하나를 분명히 고른 뒤에만 부른다 ──────────────

    def mark_read(self, mail: Entry | str) -> None:
        """⚠ 메일함을 바꾼다 — 그 메일 하나를 읽음으로. 읽기 길은 이 손을 부르지 않는다.

        폴더에만 있는 메일에 먹는지는 안 쟀다. 끊긴 세션이면 ``SessionExpired``(반영되지 않았다).
        """
        self._send_change(f"{self.db_path}/{INBOX_VIEW}/{_unid(mail)}?OpenDocument")

    def mark_unread(self, mail: Entry | str) -> None:
        """⚠ 메일함을 바꾼다 — 그 메일 하나를 안 읽음으로(읽음의 되돌리기). 부르는 자리는 ``mark_read`` 와 같다."""
        self._send_change(f"{self.db_path}/ag_read_cancel?OpenAgent&docid={_unid(mail)}&imapuser=0")

    def _send_change(self, path: str) -> None:
        """메일함을 바꾸는 주소를 부른다 — 위 두 손의 꼴만 받는다. 끊긴 세션의 로그인 페이지는 ``SessionExpired``."""
        db = re.escape(self.db_path)
        if not (re.fullmatch(rf"{db}/{INBOX_VIEW}/{_HEX32}\?OpenDocument", path)
                or re.fullmatch(rf"{db}/ag_read_cancel\?OpenAgent&docid={_HEX32}&imapuser=0", path)):
            raise ChangeRefused(f"메일함을 바꾸는 손 둘의 꼴이 아니다: {path}")
        data, kind = self._open(self.server + path)
        if _looks_like_login(data.decode(_charset(kind), errors="replace")):
            raise SessionExpired("메일함을 바꾸는 요청에 로그인 페이지가 왔다 — 반영되지 않았다")
        log.info("메일함을 바꿨다: %s", "읽음으로" if path.endswith("?OpenDocument") else "안 읽음으로")

    # ── 폴더 — 나무 읽기는 읽기 길, 만들기 · 옮기기 · 지우기는 바꾸는 손이다 ──────────────

    def folder_tree(self) -> list[FolderNode]:
        """폴더 나무 — 쓰는 사람이 지은 폴더마다 열쇠 · 경로 · 부모. 바꾸는 손이 이 열쇠를 쓴다. 읽음 표시를 안 바꾼다.

        같은 보기가 이전메일함 쪽 짝도 들어, 지운 폴더가 짝이 남은 동안 여기 남을 수 있다 — 지금 있는 폴더는 ``folders`` 가 든다.
        """
        body, kind = self._get(f"/{FOLDER_TREE_VIEW}?ReadViewEntries&outputformat=json&count=-1")
        text = body.decode(_charset(kind), errors="replace")
        try:
            answer = json.loads(text)
        except json.JSONDecodeError as exc:
            if _looks_like_login(text):
                raise SessionExpired("폴더 나무 대신 로그인 페이지가 왔다 — 다시 로그인한다") from exc
            raise MailboxError(f"폴더 나무 JSON 을 못 읽었다: {exc}") from exc
        nodes = []
        for row in (answer.get("viewentry") or []) if isinstance(answer, dict) else []:
            cols = {c.get("@name"): _json_cell(c) for c in row.get("entrydata") or [] if isinstance(c, dict)}
            node = cols.get(TREE_COLUMN_NODE, "")
            if FOLDER_NODE.match(node) and cols.get(TREE_COLUMN_PATH):
                nodes.append(FolderNode(node=node, path=cols[TREE_COLUMN_PATH], parent=cols.get(TREE_COLUMN_PARENT, "")))
        log.info("폴더 나무: %d마디", len(nodes))
        return nodes

    def folder_node(self, path: str, *, node: str = "") -> FolderNode | None:
        """경로가 같은 폴더의 마디 — 지금 있는 폴더(``folders``)만. 없으면 None.

        나무는 지운 폴더의 이전메일함 짝을 같은 경로로 들 수 있어, 그 경로의 줄이 둘 넘으면 고르지 않고 ``MailboxError`` 다 —
        짝을 고르면 서버는 OK 를 내고 아무것도 안 한다. ``node`` 를 주면(방금 지은 열쇠) 그 줄만 본다.
        """
        if path not in {f.path for f in self._fresh_folders()}:
            return None
        rows = [n for n in self.folder_tree() if n.path == path and (not node or n.node == node)]
        if len(rows) > 1:
            raise MailboxError(f"폴더 나무에 같은 경로가 {len(rows)} 줄이다(지운 폴더의 짝일 수 있다) — 웹메일에서 고른다: {path!r}")
        return rows[0] if rows else None

    def create_folder(self, name: str, parent: str = "") -> FolderNode:
        """⚠ 메일함을 바꾼다 — 폴더 하나를 만든다. ``parent`` 는 부모 폴더의 경로(비면 맨 위)다. 만든 폴더의 마디를 낸다.

        이름은 웹메일 화면과 같은 글자를 막고, 같은 자리에 같은 이름이 있으면 만들지 않는다(``MailboxConfigError``). 서버의 ``OK`` 를
        믿지 않고 보기로 다시 봐서 안 섰으면 ``MailboxError``.
        """
        name = name.strip()
        _check_folder_name(name)
        path = f"{parent}{FOLDER_SEPARATOR}{name}" if parent else name
        if any(f.path.casefold() == path.casefold() for f in self._fresh_folders()):
            raise MailboxConfigError(f"같은 폴더가 이미 있다: {path!r}")
        if parent:
            up = self.folder_node(parent)
            if up is None:
                raise MailboxConfigError(f"부모 폴더가 없다: {parent!r}")
            parent_node = up.node
        else:
            parent_node = TOP_PARENT
        node = f"newNode{secrets.randbelow(10 ** 8)}"
        query = urllib.parse.urlencode({"ulan": "kor", "act": "create", "fid": "", "fname": name, "fcode": "",
                                        "pfname": "", "pfcode": parent_node, "nodeid": node}, quote_via=urllib.parse.quote)
        self._send_folder(f"{self.db_path}/{FOLDER_SAVE_AGENT}?OpenAgent&{query}", "폴더를 만들었다")
        made = self.folder_node(path, node=node)
        if made is None:
            raise MailboxError(f"폴더 만들기 요청은 OK 였는데 다시 보니 안 섰다: {path!r}")
        return made

    def move_mails(self, unids, to: str) -> None:
        """⚠ 메일함을 바꾼다 — 메일들을 폴더 ``to``(경로)로, ``to`` 가 빈 글자면 받은편지함으로 옮긴다. 읽음 표시는 그대로다.

        서버는 못 옮겨도 ``OK`` 를 내서 옮긴 뒤 받는 자리의 보기로 다시 본다 — 안 든 메일이 있으면 ``MailboxError``.
        """
        ids = [_unid(u) for u in unids]
        if not ids:
            raise MailboxConfigError("옮길 메일이 없다")
        if to:
            node = self.folder_node(to)
            if node is None:
                raise MailboxConfigError(f"그런 폴더가 없다: {to!r}")
            target = node.node
        else:
            target = INBOX_NODE
        form = {"__Click": "0", "Action": "mailmove_action", "nodeUNID": target, "folderName": "",
                "UNIDs": ",".join(ids), "ParaView": "", "imapuser": "", "owner": ""}
        self._send_folder(f"{self.db_path}/{MOVE_FORM}?OpenForm", "메일을 옮겼다", form=form)
        landed = self._landed(to, ids)
        missing = [u for u in ids if u.upper() not in landed]
        if missing:
            raise MailboxError(f"옮기기 요청은 OK 였는데 {len(missing)}/{len(ids)} 통이 {to or '받은편지함'}에 없다")

    def delete_folder(self, path: str) -> None:
        """⚠ 메일함을 바꾼다 — 빈 폴더 하나를 지운다. 메일이나 하위 폴더가 든 폴더는 지우지 않는다(``MailboxConfigError``) —
        메일이 든 채 지우면 그 메일이 휴지통으로 간다. 이전메일함 쪽 짝까지 두 번 보내 나무에서도 지운다."""
        node = self.folder_node(path)
        if node is None:
            raise MailboxConfigError(f"그런 폴더가 없다: {path!r}")
        current = self.folders()   # folder_node 가 방금 새로 받은 목록이다 — 다시 받지 않는다
        if any(f.path.startswith(path + FOLDER_SEPARATOR) for f in current):
            raise MailboxConfigError(f"하위 폴더가 든 폴더라 지우지 않는다: {path!r}")
        folder = next(f for f in current if f.path == path)
        if self._view(folder.unid, 1, 1).find("viewentry") is not None:
            raise MailboxConfigError(f"메일이 든 폴더라 지우지 않는다 — 먼저 옮긴다(든 채 지우면 휴지통으로 간다): {path!r}")
        pointing = [r for r in self.rules() if r.action == "move_folder" and r.folder == path]
        if pointing:
            raise MailboxConfigError(f"규칙 {len(pointing)}개가 이 폴더로 메일을 옮긴다 — 그 규칙을 먼저 고치거나 지운다"
                                     f"(없는 폴더를 가리킨 규칙이 새 메일을 어떻게 하나는 안 쟀다): {path!r}")
        for side, both in (("mail", ""), ("archive", "Y")):
            query = urllib.parse.urlencode({"ulan": "kor", "act": "delete_action", "nodeid": node.node, "imapuser": "",
                                            "power": "", "afdelete": both, "nodefrom": side})
            self._send_folder(f"{self.db_path}/{FOLDER_SAVE_AGENT}?OpenAgent&{query}", "폴더를 지웠다")
        if any(f.path == path for f in self._fresh_folders()):
            raise MailboxError(f"폴더 지우기 요청은 OK 였는데 다시 보니 남았다: {path!r}")

    def trash_mails(self, unids) -> None:
        """⚠ 메일함을 바꾼다 — 메일들을 휴지통으로 보낸다(웹메일 목록의 [삭제]). 받은편지함 · 폴더 · 보낸편지함 · 임시보관함 어디의
        메일이든 같고 읽음 표시는 그대로다. 영구삭제는 하지 않는다 — 되살리기는 ``restore_mails``.

        서버의 답이 비어 증거가 못 되므로 보낸 뒤 휴지통 보기로 다시 본다 — 안 든 메일이 있으면 ``MailboxError``.
        """
        ids = [_unid(u) for u in unids]
        if not ids:
            raise MailboxConfigError("휴지통으로 보낼 메일이 없다")
        self._send_folder(f"{self.db_path}/{TRASH_SEND_AGENT}?OpenAgent&docid={','.join(ids)}"
                          "&folderkey=&type=&paraview=&imapuser=&owner=", "메일을 휴지통으로 보냈다", ok=None)
        landed = self._in_trash(ids)
        missing = [u for u in ids if u.upper() not in landed]
        if missing:
            raise MailboxError(f"휴지통으로 보내는 요청은 받았는데 {len(missing)}/{len(ids)} 통이 휴지통에 없다")

    def _in_trash(self, ids: list[str]) -> set[str]:
        """휴지통 보기에 든 ``ids`` — 다 찾거나 보기가 끝날 때까지 ``VIEW_PAGE_MOST`` 줄씩(``_landed`` 와 같은 꼴)."""
        want, found, start, first = {u.upper() for u in ids}, set(), 1, None
        while want - found:
            rows = [e.get("unid", "").upper() for e in self._view(TRASH_VIEW, VIEW_PAGE_MOST, start).iter("viewentry")]
            if not rows or rows[0] == first:
                break
            found |= want & set(rows)
            first, start = rows[0], start + len(rows)
        return found

    def restore_from_trash(self, mail: Entry | Found | str) -> None:
        """⚠ 메일함을 바꾼다 — 휴지통의 메일 하나를 되살린다(받은 메일은 받은편지함으로). 답이 ``result`` 참이 아니면 ``MailboxError``."""
        unid = _unid(mail.unid if isinstance(mail, Found) else mail)
        data = self._send_folder(f"{self.db_path}/{TRASH_AGENT}?OpenAgent&docid={unid}&imapuser=&owner=&type=recovery",
                                 "휴지통에서 되살렸다", ok=None)
        try:
            answer = json.loads(data)
        except json.JSONDecodeError as exc:
            raise MailboxError(f"되살리기 답이 JSON 이 아니다: {data[:80]!r}") from exc
        if not (isinstance(answer, dict) and answer.get("result") is True):
            raise MailboxError(f"되살리기가 서지 않았다: {data[:80]!r}")

    def restore_mails(self, unids) -> list[str]:
        """⚠ 메일함을 바꾼다 — 휴지통의 메일들을 한 통씩 ``restore_from_trash`` 로 되살린다. 받은 메일은 받은편지함으로 읽음 표시
        그대로 돌아온다.

        되살린 뒤 휴지통 보기로 다시 봐서 남은 메일이 있으면 ``MailboxError``, 도중에 지면 몇 통을 되살린 뒤 멎었나를 같은 갈래의
        오류로 낸다. 내는 것 — 휴지통에서는 빠졌는데 받은편지함에 안 든 unid(되살린 자리를 모르는 메일).
        """
        ids = [_unid(u) for u in unids]
        if not ids:
            raise MailboxConfigError("되살릴 메일이 없다")
        for done, u in enumerate(ids):
            try:
                self.restore_from_trash(u)
            except MailboxError as exc:
                raise type(exc)(f"{done}/{len(ids)} 통을 되살린 뒤 멎었다 — {exc}") from exc
        left = self._in_trash(ids)
        if left:
            raise MailboxError(f"되살리기 요청은 받았는데 {len(left)}/{len(ids)} 통이 아직 휴지통에 있다")
        home = self._landed("", ids)
        return [u for u in ids if u.upper() not in home]

    # ── 메일 규칙 — 목록 · 읽기는 읽기 길, 넣기 · 고치기 · 지우기는 바꾸는 손이다 ──────────────

    def rules(self) -> list[Rule]:
        """메일 규칙 전부 — 목록 보기의 unid 마다 그 규칙 문서를 연다(규칙 문서라 메일의 읽음과 무관하다). 읽기만 한다."""
        unids = self._rule_unids()
        with ThreadPoolExecutor(max_workers=ORG_WORKERS) as pool:
            got = list(pool.map(self._rule_by_unid, unids))
        log.info("메일 규칙: %d개", len(got))
        return got

    def rule(self, unid: str) -> Rule:
        """규칙 하나 — 규칙 목록에 없는 unid 면 ``MailboxConfigError``(메일 문서를 규칙으로 열지 않게)."""
        unid = _unid(unid).upper()
        if unid not in self._rule_unids():
            raise MailboxConfigError(f"그런 규칙이 없다: {unid}")
        return self._rule_by_unid(unid)

    def save_rule(self, rule: Rule) -> str:
        """⚠ 메일함을 바꾼다 — 규칙을 넣거나(``unid`` 가 빈 글자) 고친다. 규칙 unid 를 낸다. 서버가 그 규칙을 바로 쓴다.

        자동전달 칸은 늘 비워 보낸다 — 남에게 메일이 나가는 규칙은 이 손이 짓지도 고치지도 않는다.
        """
        form = self._rule_form(rule)
        if rule.unid:
            if self.rule(rule.unid).forwards:
                raise MailboxConfigError("자동전달 규칙은 이 손이 고치지 않는다 — 웹메일에서 고친다")
            path = f"{self.db_path}/0/{_unid(rule.unid).lower()}?EditDocument&Seq=1"
        else:
            path = f"{self.db_path}/{RULE_FORM}?OpenForm&Seq=1&viewname=(%24webrule)"
        answer = self._send_rule(path, form, "규칙을 " + ("고쳤다" if rule.unid else "넣었다"))
        unid = str(answer.get("unid") or "").upper()
        if unid not in self._rule_unids():
            raise MailboxError("규칙 저장 답은 참이었는데 목록에 그 규칙이 없다")
        return unid

    def delete_rule(self, unid: str) -> None:
        """⚠ 메일함을 바꾼다 — 규칙 하나를 지운다. 자동전달 규칙도 지울 수는 있다(남에게 나가는 길을 닫는 쪽이다)."""
        unid = self.rule(unid).unid
        self._send_rule(f"{self.db_path}/{RULE_FORM}?OpenForm&Seq=1",
                        {"__Click": "0", "%%PostCharset": "UTF-8", "SubmitAction": "delete", "SAResponse": "json",
                         "ProcessUNID": unid}, "규칙을 지웠다")
        if unid in self._rule_unids():
            raise MailboxError("규칙 지우기 답은 참이었는데 목록에 남았다")

    def _rule_form(self, rule: Rule) -> dict:
        """규칙 → 저장 폼의 칸(fmmailrule.js save). 조건 없는 규칙 · 모르는 칸 · 없는 폴더는 묻기 전에 막는다."""
        if rule.box not in RULE_BOXES or rule.action not in RULE_ACTIONS:
            raise MailboxConfigError(f"규칙 갈래가 아니다: {rule.box!r} · {rule.action!r}")
        unknown = set(rule.conditions) - set(RULE_FIELDS)
        if unknown:
            raise MailboxConfigError(f"모르는 조건 칸: {sorted(unknown)}")
        cond = {k: str(rule.conditions.get(k) or "").strip() for k in RULE_FIELDS}
        if not any(cond.values()):
            raise MailboxConfigError("조건이 하나도 없다 — 모든 메일에 걸리는 규칙은 짓지 않는다")
        node = None
        if rule.action == "move_folder":
            node = self.folder_node(rule.folder) if rule.folder else None
            if node is None:
                raise MailboxConfigError(f"옮길 폴더가 없다: {rule.folder!r}")
        form = {"__Click": "0", "%%PostCharset": "UTF-8", "SubmitAction": "save", "SAResponse": "json",
                "%%Surrogate_expRule": "1", "expRule": rule.box, "%%Surrogate_rules": "1", "rules": rule.action,
                "%%Surrogate_select_folder": "1", "select_folder": node.node if node else "", "new_folder": "",
                "folder_id": node.node if node else "",
                "folder_name": node.path.rsplit(FOLDER_SEPARATOR, 1)[-1] if node else "",
                "%%Surrogate_rule_fromType2": "1", "rule_fromType2": "1" if rule.exact_from else "0",
                "%%Surrogate_rule_toType2": "1", "rule_toType2": "1" if rule.exact_to else "0",
                # 자동전달 칸 — 늘 비우고 끈다(남에게 나가는 길)
                "forward_list": "", "AllFwdOpt": "0", "MydeptFwdOpt": "0",
                "%%Surrogate_rule_fromType1": "1", "rule_fromType1": "0"}
        form |= {f"rule_{k}": v for k, v in cond.items()} | {f"rule_{k}_1": "" for k in RULE_FIELDS}
        return form

    def _send_rule(self, path: str, form: dict, done: str) -> dict:
        """규칙을 바꾸는 POST — 위 손들의 꼴만 받고, 자동전달 칸이 찬 폼은 보내지 않는다. 답(JSON)의 ``result`` 가 참이어야 한다."""
        db = re.escape(self.db_path)
        if not (re.fullmatch(rf"{db}/{RULE_FORM}\?OpenForm&Seq=1(&viewname=\(%24webrule\))?", path)
                or re.fullmatch(rf"{db}/0/{_HEX32}\?EditDocument&Seq=1", path)):
            raise ChangeRefused(f"규칙을 바꾸는 손의 꼴이 아니다: {path}")
        if form.get("forward_list") or form.get("AllFwdOpt", "0") != "0" or form.get("MydeptFwdOpt", "0") != "0":
            raise ChangeRefused("자동전달 칸이 찬 규칙은 보내지 않는다")
        request = urllib.request.Request(self.server + path, data=urllib.parse.urlencode(form).encode(), method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        data, kind = self._open(request)
        text = data.decode(_charset(kind), errors="replace")
        if _looks_like_login(text):
            raise SessionExpired("규칙을 바꾸는 요청에 로그인 페이지가 왔다 — 반영되지 않았다")
        try:
            answer = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MailboxError(f"규칙 답이 JSON 이 아니다: {text.strip()[:80]!r}") from exc
        if not (isinstance(answer, dict) and answer.get("result") is True):
            raise MailboxError(f"메일함이 규칙을 안 받았다: {text.strip()[:80]!r}")
        log.info("메일함을 바꿨다: %s", done)
        return answer

    def _rule_unids(self) -> list[str]:
        root = self._view(RULE_VIEW, VIEW_PAGE_MOST, 1)
        return [e.get("unid", "").upper() for e in root.iter("viewentry") if _UNID.match(e.get("unid", ""))]

    def _rule_by_unid(self, unid: str) -> Rule:
        """규칙 문서의 편집 화면을 받아 푼다 — ``EditDocument`` 는 읽기 길 목록 밖이라, 규칙 목록이 낸 unid 로 이 자리에서만 연다."""
        data, kind = self._open(f"{self.server}{self.db_path}/0/{_unid(unid).lower()}?EditDocument")
        page = data.decode(_charset(kind), errors="replace")
        if _looks_like_login(page):
            raise SessionExpired("규칙 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        return parse_rule_page(unid, page)

    # ── 임시저장 — 웹메일 쓰기 화면의 [임시저장] 단추와 같은 요청 ────────────────────

    def save_draft(self, subject: str, to: list[DraftPerson], *, cc: list[DraftPerson] = (), bcc: list[DraftPerson] = (),
                   html_body: str, files: list[DraftFile] = (), empno: str, options: DraftOptions = DraftOptions()) -> str:
        """⚠ 메일함을 바꾼다 — 새 임시메일 하나를 임시보관함에 저장하고 그 unid 를 낸다. **보내지 않는다.**

        ``empno`` 는 쓰는 사람 사번(메일함 파일 번호) — 첨부 업로드 DB 와 첨부 열쇠가 그것으로 선다. 첨부가 있으면 먼저 업로드 DB 에
        올리고 저장 폼에 그 열쇠를 싣는다. 대용량(``DRAFT_ATTACH_BIG`` 넘음)은 웹메일 임시저장이 안 들어 묻기 전에 막는다.
        ``options`` 는 메일속성(긴급 · 전달불가 · 한명씩 · 예약)이다 — 예약해도 저장만 한다(나가는 것은 [보내기] 뒤 그 시각이다).
        저장 칸 SaveAgent 는 늘 ``wSave`` 다 — 다른 값이면 서버가 그 자리에서 발송한다. 저장 뒤 임시보관함 보기에 그 unid 가 서야 낸다.
        """
        if not to:
            raise MailboxConfigError("받는 사람이 없다")
        if len(files) > DRAFT_ATTACH_MOST:
            raise MailboxConfigError(f"첨부가 {len(files)} 개다 — 웹메일은 {DRAFT_ATTACH_MOST} 개까지 든다")
        big = [f.name for f in files if len(f.data) > DRAFT_ATTACH_BIG]
        if big:
            raise MailboxConfigError(f"대용량 첨부는 임시저장이 안 든다(웹메일이 지운다): {', '.join(big)} — 웹메일에서 붙인다")
        form, action, unid, page = self._blank_memo()
        if options.send_at:
            step = SEND_AT_STEP_IN_PAGE.search(page)
            if not step:
                raise MailboxError("쓰기 화면에 예약발송 분 눈금(Reservation_Interval)이 없다 — 웹메일 화면이 바뀌었다. 예약 없이 저장하거나 화면에서 넣는다")
            if int(options.send_at[-2:]) % int(step.group(1)):
                raise MailboxConfigError(f"예약발송의 분은 {step.group(1)} 분 눈금이다(웹메일 화면의 고름 상자) — {options.send_at} 를 눈금에 맞춰 다시 준다")
        html_body = with_signature(html_body, self._signature(page))
        if files:
            form |= self._upload_draft_files(unid, empno, files)
        else:
            form |= {"NoAttach": "T", "am_attachment": "", "$attachpath": "", "$attachkey": ""}
        form |= {"__Click": "0", "%%PostCharset": "UTF-8", "SAResponse": "json", "SaveAgent": SAVE_AGENT_DRAFT,
                 "SendOptions": "2", "docMode": "", "nh_Type": "", "ECMCheck": "", **options.form(),
                 "Subject": subject, "Body": "", "MIMEBody": _mime_html(html_body),
                 "TransBigFile": "0", "BigFileOnlyECM": "0", "FileKey": "", "BigFileNameList": "",
                 "AllAttachFileNameList": "\n".join(f.name for f in files),
                 "AllAttachFileSize": ",".join(str(len(f.data)) for f in files)}
        for field, inet, people in (("SendTo", "InetSendTo", to), ("CopyTo", "InetCopyTo", cc),
                                    ("BlindCopyTo", "InetBlindCopyTo", bcc)):
            form[field] = "; ".join(p.notes for p in people)
            form[inet] = "; ".join(p.name if p.group else f'"{p.name}" <{p.email}>' if p.name else p.email for p in people)
        form[SENT_PEOPLE_FIELDS[0]] = people_info({"to": to, "cc": cc})
        form[SENT_PEOPLE_FIELDS[1]] = people_info({"bcc": bcc})
        answer = self._post_memo(action, form)
        saved = str(answer.get("unid") or "").upper()
        if not _UNID.match(saved):
            raise MailboxError(f"임시저장 답에 unid 가 없다: {answer!r:.80}")
        if saved not in {e.unid.upper() for e in (self.list_drafts(count=50) or [])}:
            raise MailboxError("임시저장 답은 참이었는데 임시보관함에 그 메일이 없다")
        log.info("메일함을 바꿨다: 임시메일을 저장했다 · 받는 사람 %d · 첨부 %d", len(to) + len(cc) + len(bcc), len(files))
        return saved

    def _blank_memo(self) -> tuple[dict, str, str, str]:
        """빈 쓰기 화면을 받아 (폼 칸, 저장 주소, 이 쓰기의 unid, 화면 HTML) — 화면이 숨은 칸에 든 기본값을 그대로 물려받는다."""
        data, kind = self._open(f"{self.base}/{MEMO_FORM}?openform&opentype=popup")
        page = data.decode(_charset(kind), errors="replace")
        if _looks_like_login(page):
            raise SessionExpired("쓰기 화면 대신 로그인 페이지가 왔다 — 다시 로그인한다")
        return (*parse_memo_form(page, self.db_path), page)

    def _signature(self, page: str) -> Signature | None:
        """쓰는 사람의 서명 — 쓰기 화면의 설정이 서명을 켰으면 서명 문서의 본문을 받아 낸다. 꺼졌거나 못 받으면 ``None``(경고만 낸다).

        빈 쓰기 화면은 서명을 안 들고 화면 스크립트가 뜬 뒤에 따로 넣는다 — 이 손은 그 스크립트를 안 돌리니 같은 일을 여기서 한다."""
        found = parse_signature_settings(page)
        if not found:
            return None
        sig_unid, add_line = found
        try:
            data, kind = self._get(f"/0/{sig_unid}/Body?OpenField")
        except MailboxError as exc:
            log.warning("서명을 못 받아 서명 없이 저장한다: %s", exc)
            return None
        body = signature_fragment(data.decode(_charset(kind), errors="replace"))
        if not body:
            log.warning("서명 문서의 본문이 비어 서명 없이 저장한다")
            return None
        return Signature(html=body, add_line=add_line)

    def _upload_draft_files(self, unid: str, empno: str, files: list[DraftFile]) -> dict:
        """첨부를 업로드 DB 에 올리고 저장 폼에 실을 칸을 낸다. 업로드 답에 그 파일이 다 서야 낸다."""
        digit = empno[-1:] if empno[-1:].isdigit() else "0"
        upload_db = UPLOAD_DB.format(digit=digit)
        unique = secrets.token_hex(8)
        key = f"{unid}_{unique}_{DRAFT_COMPANY_CODE}_{empno}"
        for f in files:
            fields = {"__Click": "0", "Body": "", "unique": unique, "unid": unid, "attachKey": key, "idx": "0",
                      "lastModified": "", "total_size": str(len(f.data))}
            body, boundary = _multipart(fields, "%%File", f)
            request = urllib.request.Request(f"{self.server}/{upload_db}/{UPLOAD_AGENT}", data=body, method="POST")
            request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
            data, kind = self._open_long(request)
            text = data.decode(_charset(kind), errors="replace")
            if _looks_like_login(text):
                raise SessionExpired("첨부 업로드에 로그인 페이지가 왔다 — 저장하지 않았다")
            try:
                got = [g.get("name") for g in json.loads(text).get("files", [])]
            except (json.JSONDecodeError, AttributeError) as exc:
                raise MailboxError(f"첨부 업로드 답이 JSON 이 아니다: {text.strip()[:80]!r}") from exc
            if f.name not in got:
                raise MailboxError(f"업로드 DB 가 첨부를 안 받았다: {f.name}")
        return {"NoAttach": "F", "am_attachment": "-spl-".join(f.name for f in files),
                "$attachpath": upload_db, "$attachkey": key}

    def _open_long(self, request: urllib.request.Request) -> tuple[bytes, str]:
        """첨부처럼 오래 걸리는 요청 — 시한만 길고 ``_open`` 과 같다."""
        kept, self.timeout = self.timeout, max(self.timeout, DRAFT_UPLOAD_TIMEOUT)
        try:
            return self._open(request)
        finally:
            self.timeout = kept

    def _post_memo(self, action: str, form: dict) -> dict:
        """쓰기 폼의 저장 POST — 쓰기 화면의 저장 주소 꼴만 받는다. 답(JSON 비슷한 글)의 ``result`` 가 참이어야 한다."""
        db = re.escape(self.db_path)
        if not re.fullmatch(rf"{db}/{MEMO_FORM}\?OpenForm&Seq=1&opentype=popup", action):
            raise ChangeRefused(f"임시저장 손의 꼴이 아니다: {action}")
        request = urllib.request.Request(self.server + action, data=urllib.parse.urlencode(form).encode(), method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        data, kind = self._open_long(request)
        text = data.decode(_charset(kind), errors="replace")
        if _looks_like_login(text):
            raise SessionExpired("임시저장 요청에 로그인 페이지가 왔다 — 저장되지 않았다")
        return parse_save_answer(text)

    def _fresh_folders(self) -> list[Folder]:
        """보기 목록을 새로 받아 지금의 폴더 — 바꾸는 손 앞뒤에는 받아 둔 목록이 낡는다."""
        self._collections = None
        return self.folders()

    def _landed(self, to: str, ids: list[str]) -> set[str]:
        """옮긴 자리(폴더 경로 · 빈 글자는 받은편지함)에 든 ``ids`` — 옛 메일은 새것 창 밖에 서므로 다 찾거나 보기가 끝날 때까지
        ``VIEW_PAGE_MOST`` 줄씩 받는다. 서버가 start 를 안 따라 같은 쪽을 다시 주면 거기서 멈춘다."""
        folder = next((f for f in self._fresh_folders() if f.path == to), None) if to else None
        if to and folder is None:
            return set()
        want, found, start, first = {u.upper() for u in ids}, set(), 1, None
        while want - found:
            rows = (self.list(count=VIEW_PAGE_MOST, start=start) if not to
                    else self.list_folder(folder, count=VIEW_PAGE_MOST, start=start))
            if not rows or rows[0].unid == first:
                break
            found |= want & {e.unid.upper() for e in rows}
            first, start = rows[0].unid, start + len(rows)
        return found

    def _send_folder(self, path: str, done: str, *, form: dict | None = None, ok: str | None = "ok") -> str:
        """폴더 · 휴지통의 바꾸는 주소를 부른다 — 위 손들의 꼴만 받는다. 답 글자를 낸다. ``ok`` 가 있으면 답이 그 낱말이어야 한다."""
        db = re.escape(self.db_path)
        if not (re.fullmatch(rf"{db}/{FOLDER_SAVE_AGENT}\?OpenAgent&ulan=kor&act=(create|delete_action)&[\w%.=&-]+", path)
                or (form is not None and path == f"{self.db_path}/{MOVE_FORM}?OpenForm")
                or re.fullmatch(rf"{db}/{TRASH_AGENT}\?OpenAgent&docid={_HEX32}&imapuser=&owner=&type=recovery", path)
                or re.fullmatch(rf"{db}/{TRASH_SEND_AGENT}\?OpenAgent&docid={_HEX32}(,{_HEX32})*"
                                "&folderkey=&type=&paraview=&imapuser=&owner=", path)):
            raise ChangeRefused(f"폴더를 바꾸는 손의 꼴이 아니다: {path}")
        body = urllib.parse.urlencode(form).encode() if form is not None else None
        request = urllib.request.Request(self.server + path, data=body, method="POST" if form is not None else "GET")
        if body is not None:
            request.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        data, kind = self._open(request)
        text = data.decode(_charset(kind), errors="replace")
        if _looks_like_login(text):
            raise SessionExpired("메일함을 바꾸는 요청에 로그인 페이지가 왔다 — 반영되지 않았다")
        if ok is not None and text.strip().lower() != ok:
            raise MailboxError(f"메일함이 바꾸기를 안 받았다: {text.strip()[:80]!r}")
        log.info("메일함을 바꿨다: %s", done)
        return text.strip()


# ── 풀기 ─────────────────────────────────────────────────────────────────

def read_only_patterns(db_path: str) -> tuple[re.Pattern, ...]:
    """읽기 길이 물을 수 있는 주소 꼴(서버 뿌리부터의 경로 · 질의) — 다 읽음을 안 바꾸는 것으로 잰 꼴이다. 닫힌 목록이라 새 꼴은
    여기에 더해야 묻는다. ``directory_survey.py`` 가 웹메일에서 잡은 요청을 이 목록에 대 본다."""
    db = re.escape(db_path)
    return tuple(re.compile(p, re.IGNORECASE) for p in (
        rf"^{db}/[^/?]+\?ReadViewEntries(&[\w$%.=-]*)*$",
        rf"^{db}/api/data/collections$",
        rf"^{db}/0/{_HEX32}/Body\?OpenField$",
        rf"^{db}/0/{_HEX32}/({'|'.join(SENT_PEOPLE_FIELDS)})\?OpenField$",
        rf"^{db}/0/{_HEX32}/Body/M\d+(\.\d+)*\?OpenElement$",
        rf"^{db}/0/{_HEX32}/\$FILE/[^?#]+$",
        rf"^{db}/{SEARCH_AGENT}\?open(&[\w$%.()+=-]*)*$",
        r"^/common/lib_f\.nsf/checksessionstatus\?Openpage$",
        r"^/common/profile\.nsf/ag_org_search_json\?OpenAgent(&[\w$%.()+=-]*)*$",
        r"^/common/profile\.nsf/ag_tree_(dept|user)_json\?OpenAgent(&[\w$%.()+=-]*)*$",
        r"^/common/lib_f\.nsf/agGetDistribute\?openagent(&[\w$%.()+=-]*)*$",
    ))


# ── 조직 전체 — 받아 둔 조직도를 이 PC 에서 거른다 ─────────────────────────────

@dataclass
class OrgChart:
    """회사 조직 한 판. ``depts`` 는 코드 → 부서, ``members`` 는 코드 → 그 부서에 바로 든 사람이다. 한 사람이 둘 넘는 부서에
    들 수 있다(본부장이 「임원」과 제 본부에 함께 든다)."""
    company: str
    depts: dict
    members: dict

    def find_depts(self, words: str) -> list[Dept]:
        """이름 · 코드(회사 약칭 괄호는 붙여도 떼도 된다)가 그 말과 같은 부서 — 같은 것이 없으면 이름에 그 말이 든 부서다. 띄어쓰기 ·
        가운뎃점 · 대소문자는 안 가린다."""
        want = squash(words)
        if not want:
            return []
        exact = [d for d in self.depts.values() if want in (squash(d.name), squash(d.code), squash(d.code.split("(", 1)[0]))]
        return exact or [d for d in self.depts.values() if want in squash(d.name)]

    def path(self, code: str) -> list[Dept]:
        """맨 위 부서부터 그 부서까지."""
        chain = []
        while code in self.depts:
            chain.append(self.depts[code])
            code = self.depts[code].parent
        return chain[::-1]

    def subtree(self, code: str) -> list[Dept]:
        """그 부서와 그 아래 부서 전부 — 나무 차례(위 부서 먼저)."""
        kids: dict[str, list[str]] = {}
        for d in self.depts.values():
            kids.setdefault(d.parent, []).append(d.code)
        out, stack = [], [code]
        while stack:
            c = stack.pop()
            if c in self.depts:
                out.append(self.depts[c])
            stack.extend(reversed(kids.get(c, [])))
        return out

    def people(self, code: str | None = None, *, deep: bool = True) -> list[DirectoryPerson]:
        """그 부서의 사람(``deep`` 이면 하위 부서까지) — ``code`` 가 없으면 회사 전원. 한 사람은 한 번만, 먼저 만난 부서로 낸다."""
        if code is None:
            codes = list(self.depts)
        else:
            codes = [d.code for d in self.subtree(code)] if deep else [code]
        seen, out = set(), []
        for c in codes:
            for p in self.members.get(c, []):
                if p.notes not in seen:
                    seen.add(p.notes)
                    out.append(p)
        return out

    def dept_name(self, code: str) -> str:
        d = self.depts.get(code)
        return d.name if d else code


squash = ep_session.squash    # 견주기 꼴 — 빈칸 · 가운뎃점 · 괄호 · 대소문자를 안 본다(사내 앱 스킬이 함께 쓰는 한 자리)


# ── 주소록의 한 사람 ─────────────────────────────────────────────────────

def _person(u: dict) -> DirectoryPerson:
    return DirectoryPerson(
        email=u.get("email") or "", name=u.get("user_name") or "", name_eng=u.get("user_name_eng") or "",
        notes=u.get("key") or "", user_id=u.get("user_id") or "", empno=str(u.get("empno") or ""),
        dept=u.get("dept_name") or "", grade=u.get("grade") or "", job_title=u.get("job_title") or "",
        company=u.get("company_name") or "", retired=str(u.get("is_retire") or "").upper() in DIRECTORY_YES,
        dept_code=u.get("dept_code") or "", grade_code=u.get("grade_code") or "",
        is_boss=str(u.get("is_boss") or "").upper() in DIRECTORY_YES, job_title_code=u.get("job_title_code") or "",
        location=u.get("location") or "", duty=(u.get("job_name") or "").split(DUTY_SEPARATOR, 1)[0].strip())


def notes_key(text: str) -> str:
    """Notes 이름의 견줄 꼴 — ``CN=`` · ``OU=`` · ``O=`` 표지를 떼고 대소문자를 접는다(약식 ``이름/OU/O`` 와 같게)."""
    return "/".join(part.split("=", 1)[-1].strip() for part in text.split("/")).casefold()


def is_notes_name(text: str) -> bool:
    t = text.strip()
    return t.upper().startswith(NOTES_MARK) or ("/" in t and "@" not in t)


def directory_query(handle: str):
    """한 꼴 → (주소록에 물을 말, 답 가운데 그 사람을 고르는 자). 못 짓는 꼴(빈 글자)이면 None.

    주소는 그 주소로 묻고 메일이 같은 사람, Notes 이름은 ``CN`` 의 이름으로 묻고 ``key`` 의 견줄 꼴이 같은 사람, ID 는 약칭으로
    묻고 ``user_id`` 가 같은 사람, 그 밖(이름 · 사번)은 그 글자로 묻고 이름이나 사번이 같은 사람이다.
    """
    h = handle.strip()
    if not h:
        return None
    if "@" in h:
        addr = h.casefold()
        return h, (lambda d: d.email.strip().casefold() == addr)
    if is_notes_name(h):
        want = notes_key(h)
        first = h.split("/", 1)[0]
        return (first.split("=", 1)[1] if "=" in first else first).strip(), \
            (lambda d: bool(d.notes.strip()) and notes_key(d.notes) == want)
    found = ID_FORM.match(h)
    if found:
        ident = found.group(1).casefold()
        return found.group(2).strip(), (lambda d: d.user_id.strip().casefold() == ident)
    return h, (lambda d: h in (d.name.strip(), d.empno.strip()))


def _column(entry: ET.Element, name: str) -> str:
    for data in entry.iter("entrydata"):
        if data.get("name") == name:
            return one_line(" ".join(t.strip() for t in data.itertext() if t.strip()))
    return ""


def one_line(text: str) -> str:
    """목록 한 칸의 글 — 안에 든 줄바꿈 글자를 빈칸 하나로 접는다."""
    return LINE_BREAKS.sub(" ", text).strip()


_RULE_INFO = re.compile(r"new FormJS\((\{.*?\})\);", re.DOTALL)
_INPUT = re.compile(r"<input\b[^>]*>", re.IGNORECASE)
_ATTR = re.compile(r"""(?<![\w-])(\w+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""")


def parse_rule_page(unid: str, page: str) -> Rule:
    """규칙 편집 화면 → ``Rule``. 갈래 · 폴더는 화면 머리의 ``new FormJS({…})``, 조건 · 맞춤 · 자동전달은 입력 칸의 값이 든다.

    머리가 없거나 못 읽거나 갈래가 모르는 값이면 ``MailboxError`` — 빈 규칙으로 읽으면 자동전달 규칙을 조용히 숨긴다.
    """
    found = _RULE_INFO.search(page)
    try:
        info = json.loads(found.group(1)) if found else None
    except json.JSONDecodeError:
        info = None
    form = info.get("form") if isinstance(info, dict) else None
    if not isinstance(form, dict) or str(form.get("rules") or "") not in (*RULE_ACTIONS, "forward"):
        raise MailboxError(f"규칙 화면의 꼴이 잰 것과 다르다(머리 · 갈래를 못 읽었다): {unid}")
    paths = {}
    for item in info.get("folders") or []:
        path, _, rest = str(item).rpartition("|")
        paths[rest.split("^", 1)[0]] = path
    values: dict[str, str] = {}
    checked: dict[str, str] = {}
    for tag in _INPUT.findall(page):
        attrs = {m.group(1).lower(): html.unescape(next((g for g in m.groups()[1:] if g is not None), ""))
                 for m in _ATTR.finditer(tag)}
        name = attrs.get("name", "")
        if attrs.get("type", "").lower() == "radio":
            if re.search(r"\bchecked\b", tag, re.IGNORECASE):
                checked[name] = attrs.get("value", "")
        elif name:
            values.setdefault(name, attrs.get("value", ""))
    conditions = {k: values[f"rule_{k}"].replace("\u200b", "").strip()
                  for k in RULE_FIELDS if values.get(f"rule_{k}", "").replace("\u200b", "").strip()}
    action = str(form.get("rules") or "")
    folder_id = str(form.get("folder_id") or "")
    # 자동전달은 규칙 갈래(``forward``)나 받는 사람 목록이 든다. ``AllFwdOpt`` 는 옮기기 규칙에도 1 로 남아 있는 일이 있어 표지로 안 쓴다
    forwards = action == "forward" or bool(values.get("forward_list", "").strip())
    return Rule(unid=unid, box=checked.get("expRule", ""), action=action,
                folder=paths.get(folder_id, str(form.get("folder_name") or "")) if action == "move_folder" else "",
                conditions=conditions, exact_from=checked.get("rule_fromType2") == "1",
                exact_to=checked.get("rule_toType2") == "1", forwards=forwards)


def _json_cell(cell: dict) -> str:
    """JSON 보기의 칸 하나 → 글자. 칸은 ``{"text": {"0": 값}}`` 꼴이다 — 값 묶음이면 첫 값."""
    for key, value in cell.items():
        if key.startswith("@"):
            continue
        while isinstance(value, (dict, list)):
            value = (value.get("0") if isinstance(value, dict) else value[0]) if value else ""
        return str(value or "")
    return ""


def _check_folder_name(name: str) -> None:
    """폴더 이름을 웹메일 화면과 같은 자로 거른다 — 빈 이름 · 막는 글자 · 시스템 폴더 이름(꾸밈까지)."""
    if not name:
        raise MailboxConfigError("폴더 이름이 비었다")
    if FOLDER_NAME_BANNED.search(name):
        raise MailboxConfigError(f"폴더 이름에 못 쓰는 글자가 있다(역슬래시 · 따옴표 · | _ < >): {name!r}")
    low = name.casefold()
    for base in SYSTEM_FOLDER_NAMES:
        if low in {base, f"imap{base}", f"(imap{base})", f"${base}", f"(${base})", f"({base})"}:
            raise MailboxConfigError(f"시스템 폴더 이름이라 못 쓴다: {name!r}")


def _is_folder(view: dict) -> bool:
    return str(view.get("@folder")).casefold() == "true"


def folder_order(path: str) -> tuple:
    """폴더 경로의 차례 — 부모 · 자식 마디마다 견준다(「부모 2」가 「부모」와 「부모\\자식」 사이에 끼지 않게)."""
    return tuple(part.casefold() for part in path.split(FOLDER_SEPARATOR)), path


def ecm_note_key(text: str) -> str | None:
    """ECM 쪽지(첨부 「이름(확장자_NKB).html」의 글) → 문서 열쇠 16 hex 글자. 본문 링크의 ``OBJECTID`` 를 먼저, 없으면 머리의
    ``objectId`` 를 낸다 — 둘이 다르면 머리 값으로는 문서가 안 열린다. 머리에 열쇠가 없으면 None — ECM 쪽지가 아니다. 스킬
    company-board 도 부른다."""
    head = ECM_HEAD.search(text)
    found = ECM_OBJECT.search(head.group("head")) if head else None
    if not found:
        return None
    link = ECM_LINK.search(text)
    return (_link_key(link.group("hex")) if link else None) or found.group("key")


def _link_key(hexed: str) -> str | None:
    """링크 ``OBJECTID``(ASCII 16진) → 문서 열쇠 16 hex 글자. 풀어서 16 hex 가 아니면 None — 머리 값으로 간다."""
    try:
        key = bytes.fromhex(hexed).decode("ascii")
    except (ValueError, UnicodeDecodeError):
        return None
    return key if re.fullmatch(r"[0-9A-Fa-f]{16}", key) else None


def _found(row: dict) -> Found:
    """검색 손의 한 줄(JSON)을 푼다. 폴더 칸은 ``[이름]`` 꼴이고, 시스템 편지함 표지는 ``SEARCH_SYSTEM_BOXES`` 로 푼다."""
    category = str(row.get("category") or "").strip()
    folder = category[1:-1] if category.startswith("[") and category.endswith("]") else category
    folder = SEARCH_SYSTEM_BOXES.get(folder, folder)
    who = str(row.get("from") or "")
    ko, _, eng = who.partition(ENG_MARK)
    return Found(unid=str(row.get("unid") or "").upper(), subject=one_line(html.unescape(str(row.get("subject") or ""))),
                 sender=ko.strip() or who.strip(), date=str(row.get("date") or ""),
                 folder=folder, attached=str(row.get("attach") or "") == "T",
                 unread=UNREAD_MARK in str(row.get("icon") or ""), draft=str(row.get("isdraft") or "") == "Y",
                 sender_eng=eng.split(SPLIT_MARK, 1)[0].strip())


def _entry(entry: ET.Element, *, folder: str = "") -> Entry:
    mark = _column(entry, COLUMN_READ)
    unread = UNREAD_MARK in mark
    found = FOLDER_READ_CLASS.search(mark) if folder else None
    if found:   # 폴더 보기의 읽음 열은 HTML 조각이다 — class 가 안 읽음 · 읽음을 가른다
        mark = found.group(1)
        unread = mark == FOLDER_UNREAD_CLASS
    return Entry(
        unid=entry.get("unid", ""),
        subject=_column(entry, COLUMN_SUBJECT),
        sender=parse_sender(_column(entry, COLUMN_FROM)),
        date=_column(entry, COLUMN_DATE),
        date_sort=_column(entry, COLUMN_DATE_SORT),
        size=_column(entry, COLUMN_SIZE),
        importance=_column(entry, COLUMN_IMPORTANCE),
        role=_column(entry, COLUMN_ROLE).upper(),
        attachments=tuple(parse_attachment(n) for n in _column(entry, COLUMN_ATTACHMENTS).split(ATTACHMENT_SEPARATOR)
                          if n.strip()),
        unread=unread,
        read_mark=mark,
        related=_column(entry, COLUMN_RELATED),
        folder=folder,
    )


_ANGLE = re.compile(r"<\s*([^<>\s]+@[^<>\s]+)\s*>")
_BARE = re.compile(r"^[^@\s<>,;\"]+@[^@\s<>,;\"]+$")


def parse_sender(raw: str) -> Sender:
    """보낸 사람 열을 푼다 — 사내 ``-=spl=-`` · ``-ENG-`` 꼴, 밖의 주소만, 그 밖의 ``이름 <주소>`` 꼴."""
    text = html.unescape(raw).strip()
    if SPLIT_MARK in text or ENG_MARK in text:
        ko, _, en = text.partition(ENG_MARK)
        name, addr = _spl_part(ko)
        name_eng, addr_eng = _spl_part(en)
        return Sender(name=name, addr=addr or addr_eng, name_eng=name_eng)
    person = parse_person(text)
    return Sender(name=person.name, addr=person.addr)


def _spl_part(part: str) -> tuple[str, str]:
    display, _, rest = part.partition(SPLIT_MARK)
    found = _ANGLE.search(rest or display)
    name = display.strip() if rest else (display[:found.start()] if found else display).strip()
    return name.strip('"').strip(), found.group(1) if found else ""


def parse_people(raw: str) -> tuple[Recipient, ...]:
    """받는 사람 글줄(쉼표로 이은 사람들)을 푼다. 따옴표 · 꺾쇠 안의 쉼표는 가름이 아니다."""
    text = html.unescape(raw or "")
    people, depth, quoted, token = [], 0, False, []
    for ch in text:
        if ch == '"':
            quoted = not quoted
        elif ch == "<" and not quoted:
            depth += 1
        elif ch == ">" and not quoted and depth:
            depth -= 1
        if ch == "," and not quoted and not depth:
            people.append("".join(token))
            token = []
        else:
            token.append(ch)
    people.append("".join(token))
    return tuple(p for p in (parse_person(t) for t in people) if p.name or p.addr or p.notes)


def parse_sent_people(text: str, default_field: str = "") -> list[Recipient]:
    """보낸 메일의 받는 사람 칸 글(``<열쇠>-=-ITEM-=-<JSON>`` 을 ``-=-SEP-=-`` 로 이은 것 · HTML 이스케이프)을 푼다.

    ``field`` 는 JSON 의 칸이 앞서고, 비었으면 ``default_field`` 다. JSON 이 깨진 항목은 버리지 않고 열쇠만 든 사람으로 둔다 —
    버리면 함께 받은 사람 수가 조용히 준다."""
    out = []
    for chunk in html.unescape(text or "").split(PEOPLE_SEP):
        key, _, raw = chunk.strip().partition(PEOPLE_ITEM)
        key = key.strip()
        if not key:
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            item = {}
        if not isinstance(item, dict):
            item = {}
        kind = str(item.get("type") or "")
        name = str((item.get("dept_name") if kind == DEPT_TYPE else item.get("group_name") if kind == GROUP_TYPE
                    else item.get("user_name") or item.get("name")) or "")
        addr = str(item.get("email") or "")
        field = PEOPLE_FIELD_OF.get(str(item.get("field") or ""), default_field)
        out.append(Recipient(name=name, addr=addr, notes=key, kind=kind, field=field))
    return out


def parse_person(token: str) -> Recipient:
    """사람 하나 — ``이름 <주소>``(공백 · 탭 · 없음) · ``"이름" <주소>`` · 주소만 · Notes 이름 · ``<ID>(<약칭>)``.

    모르는 꼴은 버리지 않고 ``notes`` 에 그대로 둔다 — 버리면 함께 받은 사람 수가 조용히 준다.
    """
    t = token.strip().strip(";").strip()
    if not t:
        return Recipient("", "")
    found = _ANGLE.search(t)
    if found:
        return Recipient(name=t[:found.start()].strip().strip('"').strip(), addr=found.group(1))
    if _BARE.match(t):
        return Recipient(name="", addr=t)
    if t.upper().startswith("CN=") or ("/" in t and "@" not in t):
        first = t.split("/", 1)[0]
        return Recipient(name=first.split("=", 1)[1] if "=" in first else first, addr="", notes=t)
    # <ID>(<약칭>) 과 모르는 꼴 — 이름 · 주소 없이 글자 그대로가 열쇠다
    return Recipient(name="", addr="", notes=t)


def parse_attachment(listed: str) -> AttachmentName:
    """첨부 이름 하나 — ECM 꼴이면 원래 이름 · 확장자 · 크기를 뽑는다."""
    listed = listed.strip()
    found = ECM_ATTACHMENT.match(listed)
    if found:
        ext = found.group("ext").lower()
        return AttachmentName(listed=listed, name=f"{found.group('name').strip()}.{ext}", ext=ext,
                              size_kb=int(found.group("kb")), ecm=True)
    ext = listed.rsplit(".", 1)[1].lower() if "." in listed else ""
    return AttachmentName(listed=listed, name=listed, ext=ext)


_MEMO_TAG = re.compile(r'<textarea\b([^>]*)>(.*?)</textarea>|<input\b([^>]*)>', re.IGNORECASE | re.DOTALL)
_MEMO_ATTR = {k: re.compile(rf'\b{k}\s*=\s*"([^"]*)"', re.IGNORECASE) for k in ("name", "value", "type")}
_MEMO_SKIP_TYPES = ("file", "radio", "checkbox")     # 화면이 고름으로만 채우는 칸 — 기본값을 물려받지 않는다


def parse_memo_form(page: str, db_path: str) -> tuple[dict, str, str]:
    """쓰기 화면(``Memo?openform``) → (숨은 칸의 기본값, 저장 주소, 이 쓰기의 unid). 폼 ``_Memo`` 가 없으면 ``MailboxError``."""
    form = re.search(r'<form\b[^>]*name="_Memo"[^>]*>(.*?)</form>', page, re.IGNORECASE | re.DOTALL)
    action = re.search(r'<form\b[^>]*action="([^"]*)"[^>]*name="_Memo"', page, re.IGNORECASE)
    unid = re.search(r'"unid"\s*:\s*"([0-9A-Fa-f]{32})"', page)
    if not (form and action and unid):
        raise MailboxError("쓰기 화면에 폼 _Memo · 저장 주소 · unid 가 없다 — 웹메일 화면이 바뀌었다")
    fields: dict = {}
    for tag in _MEMO_TAG.finditer(form.group(1)):
        is_area = tag.group(1) is not None
        attrs = tag.group(1) if is_area else tag.group(3)
        name = _MEMO_ATTR["name"].search(attrs)
        kind = (_MEMO_ATTR["type"].search(attrs) or re.search(r"\btype\s*=\s*([a-z]+)", attrs, re.IGNORECASE))
        if not name or (kind and kind.group(1).lower() in _MEMO_SKIP_TYPES):
            continue
        if is_area:
            value = tag.group(2) or ""
        else:
            found = _MEMO_ATTR["value"].search(attrs)
            value = found.group(1) if found else ""
        fields.setdefault(html.unescape(name.group(1)), html.unescape(value))
    return fields, html.unescape(action.group(1)), unid.group(1).upper()


@dataclass(frozen=True)
class Signature:
    """쓰는 사람의 서명 — ``html`` 은 문서 껍데기(html · head · body)를 벗긴 조각, ``add_line`` 은 서명 앞에 빈 줄을 두라는 설정."""
    html: str
    add_line: bool


def parse_signature_settings(page: str) -> tuple[str, bool] | None:
    """쓰기 화면 → (서명 문서 unid, 서명 앞 빈 줄) — 설정이 서명을 껐거나 서명 문서가 없으면 ``None``. 칸 이름의 철자(signatue)는
    웹메일 그대로다."""
    on = SIGNATURE_ON.search(page)
    unid = SIGNATURE_UNID.search(page)
    if not (on and on.group(1).lower() == "y" and unid):
        return None
    line = SIGNATURE_ADD_LINE.search(page)
    return unid.group(1).upper(), bool(line and line.group(1).lower() == "y")


def signature_fragment(doc: str) -> str:
    """서명 문서의 본문 HTML → 본문에 넣을 조각. 웹메일 편집기(editor.js)가 서명을 넣을 때 벗기는 것(html · head · title · meta ·
    style · body 태그)을 똑같이 벗긴다 — 서명의 style 이 남으면 메일 전체 글꼴을 덮는다."""
    for tag in ("head", "title", "style"):
        doc = re.sub(rf"<{tag}\b.*?</{tag}\s*>", "", doc, flags=re.IGNORECASE | re.DOTALL)
    doc = re.sub(r"</?(html|body|meta)\b[^>]*>", "", doc, flags=re.IGNORECASE)
    return doc.strip()


def with_signature(html_body: str, sig: Signature | None) -> str:
    """넣은 글 뒤에 서명을 붙인다 — 웹메일 쓰기 화면이 새 메일에 짓는 차례(빈 줄 · 서명 · 빈 줄)와 같다. 문서 꼴(``<body>`` 가 든
    것)은 ``</body>`` 앞에 붙인다. ``sig`` 가 없으면 그대로다."""
    if sig is None:
        return html_body
    tail = (BLANK_LINE if sig.add_line else "") + sig.html + BLANK_LINE
    end = list(re.finditer(r"</body\s*>", html_body, re.IGNORECASE))
    if end:
        at = end[-1].start()
        return html_body[:at] + tail + html_body[at:]
    return html_body + tail


def parse_save_answer(text: str) -> dict:
    """저장 답 → 칸들. 답은 JSON 비슷한 글이라(``message_func`` 칸에 함수가 든다) ``result`` · ``unid`` 만 뽑는다."""
    result = re.search(r'"result"\s*:\s*(true|false)', text)
    if not result:
        raise MailboxError(f"임시저장 답의 꼴이 아니다: {text.strip()[:80]!r}")
    if result.group(1) != "true":
        message = re.search(r'"message"\s*:\s*"([^"]*)"', text)
        raise MailboxError("메일함이 임시저장을 안 받았다" + (f": {message.group(1)}" if message else ""))
    unid = re.search(r'"unid"\s*:\s*"([0-9A-Fa-f]{32})"', text)
    return {"result": True, "unid": unid.group(1) if unid else ""}


def _mime_html(html_body: str) -> str:
    """본문 HTML → 쓰기 화면 편집기가 MIMEBody 칸에 싣는 꼴(머리 + 빈 줄 + HTML). Body 칸만 채우면 본문이 비어 저장된다."""
    return ('MIME-Version: 1.0\r\nContent-Type: text/html; charset="UTF-8"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'
            + html_body)


def _multipart(fields: dict, file_field: str, f: DraftFile) -> tuple[bytes, str]:
    """업로드 한 판의 multipart 몸 — (바이트, 경계). 칸은 업로드 화면이 싣는 것 그대로다."""
    boundary = "----company-mail-" + secrets.token_hex(12)
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()]
    head = (f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{f.name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n")
    parts.append(head.encode() + f.data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def _unid(mail: Entry | str) -> str:
    unid = mail.unid if isinstance(mail, Entry) else mail
    if not _UNID.match(unid or ""):
        raise MailboxConfigError(f"메일 열쇠(unid)가 아니다: {unid!r}")
    return unid


def _charset(content_type: str) -> str:
    match = re.search(r"charset=([\w-]+)", content_type, re.IGNORECASE)
    return match.group(1) if match else "utf-8"


def _looks_like_login(text: str) -> bool:
    """끊긴 세션이 200 으로 준 SSO 화면인가 — 인증 쿠키를 지우거나 SSO 로그인으로 보내는 스크립트로 가른다. 낱말
    「swpsso」만으로는 안 가른다 — 본문에 SSO 주소를 적은 사내 안내를 끊긴 세션으로 읽는다."""
    return "EP_CERTIFY" in text or bool(_LOGIN_JUMP.search(text))


_LOGIN_JUMP = re.compile(r"location(?:\.href)?\s*=\s*[\"'][^\"']*swpsso[^\"']*login", re.IGNORECASE)
