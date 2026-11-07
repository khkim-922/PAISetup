"""사내 메일함(Lotus Notes · HCL Domino 웹메일)을 읽는 손과, 메일함을 바꾸는 이름 붙은 손 둘 — 표준 라이브러리만 쓰는 파일 하나.

무엇을 하나
    받은편지함 · 쓰는 사람이 지은 폴더 · 보낸편지함의 목록, 모든편지함의 받는 꼴 · 중요도, 받는 사람 목록 보기, 본문(HTML ·
    평문), 첨부, 사내 주소록 찾기, 세션 확인을 받는다. 이 길(읽기 길)은 **메일의 읽음 표시를 바꾸지 않는다** — 읽음을 안
    바꾸는 것으로 잰 주소 꼴만 묻고, 그 밖의 주소는 서버에 닿기 전에 ``ChangeRefused`` 로 막는다. 사람이 웹메일에서 열기
    전까지 그 메일은 「안 읽음」으로 남는다.

    메일함을 바꾸는 손은 읽음으로(``mark_read``) · 안 읽음으로(``mark_unread``) 둘뿐이고, 이름 붙은 함수 하나씩이다.
    읽기 길은 이 둘을 부르지 않는다.

어떻게 부르나
    로그인은 이 파일이 하지 않는다. 스킬 ep-login 의 받는 손(``edge_session.js``)이
    사내 SSO 를 넘은 세션 쿠키를 파일로 남기면(Playwright 저장 상태 꼴 ``{"cookies": [...]}`` — 다른 손이 같은 꼴로 남겨도 된다),
    이 파일은 그 쿠키로 메일 서버에 묻는다. 쿠키는 보낼 주소의 호스트에 맞는 것만 실린다 — 파일에 다른 사내 앱의 쿠키가 함께
    들어 있어도 된다::

        import inbox

        box = inbox.Mailbox.from_env()                  # 설정이 틀리면 여기서 MailboxConfigError
        for mail in box.list(count=20):                 # 받은편지함 — 새것부터
            if mail.unread:
                html = box.body(mail)                   # HTML 본문 — 꼴과 상관없이 한 길 · 없거나 서버가 안 주면 None
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

    주소 · 쿠키 파일을 환경변수 대신 바로 줄 때는 ``inbox.Mailbox(url, cookies_file)`` 다. 메일함 주소를 모르면 세션으로
    받는다 — ``inbox.discover_mailbox("http://<메일 서버>", cookies_file)`` 가 그 세션 주인의 ``…/<번호>.nsf`` 를 낸다.

무엇을 내나
    목록은 ``Entry`` · ``SentEntry`` 를, 폴더는 ``Folder`` 를, 모든편지함은 ``Marks`` 를, 받는 사람 목록은 ``Recipient``
    묶음을, 주소록은 ``DirectoryPerson`` 을 낸다. 보낸 사람은 ``Sender``(이름 · 주소 · 영문 이름), 첨부 이름은
    ``AttachmentName`` 이다. 시각은 메일함이 준 글자 그대로 낸다 — 시각으로 푸는 일은 부르는 쪽이 한다. ``body`` 는 글자,
    ``attachment`` 는 bytes, ``ecm_key`` 는 문서함 문서의 열쇠(16 hex 글자)를 낸다.

    세션이 끊겼으면 ``SessionExpired`` — 스킬 ep-login 으로 다시 로그인해 쿠키를 새로 남기라는 뜻이다. 읽기 길이 메일함을 바꿀 주소(또는
    읽기 전용으로 잰 꼴 밖의 주소)를 지으려 하면 ``ChangeRefused``. 설정 · 인자가 틀리면 ``MailboxConfigError``, 서버가
    답을 안 주면 ``MailboxError``(셋 다 이것의 갈래다). 무엇을 했는지는 ``logging`` 으로 남긴다(로거 이름은 이 모듈
    이름) — 셈과 방향만 싣고 본문 · 제목 · 이름 · 주소 · 첨부 이름은 안 싣는다.

메일함을 바꾸는 손 둘 — 언제 부르나는 부르는 쪽이 정한다
    ``mark_read`` · ``mark_unread`` 는 쓰는 사람의 메일함을 바꾼다. 사람이 그 메일 하나를 두고 「읽음으로 · 안 읽음으로」를
    분명히 고른 뒤에만 부른다 — 회차 · 예약 작업 · 모델의 판단이 스스로 부르면 사람이 새 메일을 못 알아본다. 이 파일은
    그 확인을 대신하지 않는다. 손 하나는 메일 하나만 바꾸고, 그 두 꼴 밖의 주소는 ``ChangeRefused`` 로 막는다.

환경변수(``from_env``)
    ``MAILBOX_URL``              메일함 주소 — 웹메일 주소창의 ``…/<번호>.nsf`` 까지(그 뒤는 버린다). 꼭 준다
    ``MAILBOX_COOKIES``          세션 쿠키 파일                 기본 ``~/.mailbox-session.json``
    ``MAILBOX_VIEW``             받은편지함 보기 이름           기본 ``XML_Inbox``
    ``MAILBOX_TIMEOUT_SECONDS``  응답 시한(초)                  기본 ``30``

사내 메일함에서 잰 것 — 어기면 조용히 망가진다. 바탕 사실의 원본은 사내 환경 기록(``~/.claude/posco/ENV-posco.md``
「네트워크 접근」)이고, 주소 · 꼴마다 잰 판(셈 · 못 잰 까닭)은 그 앱 저장소(mail-secretary)의 ``docs/company-facts.md`` 와
회사 확인 대장(그 저장소 이슈 #9)이 든다 — 줄 끝 괄호가 그 대장의 줄이다
    * IMAP · POP3 는 닫혀 있다. 열린 길은 웹(80 · 443)뿐이고, 앞에 사내 SSO 가 선다
    * ⚠ **문서를 여는 주소(``?OpenDocument`` · ``?EditDocument``)를 부르면 그 메일이 읽음으로 바뀌고, ``ag_read_cancel`` 은
      안 읽음으로 바꾼다.** 목록(``?ReadViewEntries``) · 본문(``/0/<unid>/Body?OpenField`` · 조각 ``/Body/M…?OpenElement``) ·
      첨부(``/$FILE/``) · 보기 목록 · 주소록 · 세션 확인은 안 바꾼다. 그래서 읽기 길은 그 꼴(``_read_only``)에 맞는 주소만
      묻는다 — 닫힌 목록이라, 새 꼴은 읽음을 안 바꾸는 것을 잰 뒤 여기에 더해야 묻는다 (A · A2)
    * 세션이 끊기면 서버가 오류 대신 **200 에 SSO 로 보내는 HTML** 을 준다 — 상태 코드로는 못 가린다. 답의 꼴(XML · JSON ·
      기대한 형식)과 SSO 로 보내는 스크립트로 가린다. 낱말 「swpsso」만으로는 안 가른다 — 본문에 SSO 주소를 적은 사내 안내를
      끊긴 세션으로 읽는다. 리다이렉트는 따라가지 않는다 — 따라가면 쿠키가 SSO 에 실린다
    * 받은편지함 목록의 ``read`` 열 — ``ico-nomail`` 이 안 읽음이다(되돌린 메일은 ``z^ico-nomail``). ``ico-okmail`` 읽음 ·
      ``ico-post`` 회신함 · ``ico-remail`` 전달함은 다 읽은 것이다 (A · D)
    * 보낸 사람 열 ``xname`` — 사내 메일은 ``<이름>-=spl=-<이름> &lt;<주소>&gt;-ENG-<영문>-=spl=-<영문>&lt;<주소>&gt;`` 이
      XML 안에서 한 번 더 이스케이프돼(``&amp;lt;``) 온다. 밖의 메일 · 시스템은 주소만 온다 (A)
    * 받는 꼴 열 ``xrtype`` — ``T`` 받는사람 · ``C`` 참조 · ``G`` 받는 사람 목록 밖의 그룹 · 배포 목록 (A)
    * 받은 메일의 받는 사람은 받은편지함 목록에 없고(``SendTo?OpenField`` 는 501) 보기 ``!전체목록추출용`` 의 ``$102``
      열이 든다 — 받는사람과 참조를 합친 한 글줄이고 사람마다 Notes 이름 · ``<이름> <주소>`` · ``<ID>(<약칭>)`` · 주소만
      꼴이 섞인다. 기본 정렬이 날짜순이 아니라 ``&ResortDescending=1`` 로 날짜 내림차순을 받는다. 보기의 unid 는
      ``/api/data/collections`` 에서 제목으로 찾는다 — 이 보기 이름은 한 메일함으로만 쟀다 (A)
    * 본문 ``/0/<unid>/Body?OpenField`` 는 조각 꼴(평문만 · 평문+HTML · ``multipart/related``)과 상관없이 HTML 본문을 한 번에
      준다. 이 주소에 HTTP 501 을 내는 메일이 있다(폴더에 든 한 통 · 첨부 없음 · 보낸 이 이름 없음 — 무엇이 501 을 내는지는
      모른다) — 404 와 같이 「본문 없음」(None)으로 낸다. 오류로 올리면 메일함을 훑는 회차가 그 한 통에 통째로 진다 (N-가). 조각 ``/Body/M1.1?OpenElement`` 는 평문 · HTML 둘을 든 메일의 평문이다. 다른 꼴(``multipart/related`` 는 본문이
      ``M1.1.1``)의 ``M1.1`` 은 안 쟀다 — 그 자리에 ``text/plain`` 이 아닌 것이 오면 평문 조각은 없는 것으로 낸다 (A)
    * 첨부 이름은 ``attachment`` 열에 ``{}`` 로 이어 온다. 큰 첨부는 ECM 을 가리키는 ``<원래 이름>(<확장자>_<크기>KB).html``
      이다. 그 html 은 문서가 아니라 쪽지다 — 같은 ``$FILE`` 주소로 받아지고, 맨 앞 주석 ``<!--@!ECM!@ … -->`` 안의
      ``<objectId>doc<16 hex></objectId>`` 에서 ``doc`` 을 뗀 값이 문서함이 문서를 여는 열쇠다(``MS_OBJECT_ID`` · 받은편지함
      ECM 첨부 29 통 모두 머리가 있었고 pptx · xlsx 23 편이 그 열쇠로 열렸다 · 남의 문서함 문서도 · mail-secretary#28 셋째 판).
      본문 링크의 ``OBJECTID`` 는 6/29 가 이 값과 달라 열쇠로 쓰지 않는다
    * 받은편지함 보기(``XML_Inbox``)는 받은편지함만 든다 — 쓰는 사람의 규칙이 하위 폴더로 옮긴 메일은 그 폴더의 보기에만 있다 (A2)
    * 폴더 목록은 보기 목록(``/api/data/collections``)의 ``@folder: true`` 항목이다. 시스템 폴더(``($Inbox)`` · ``($Trash)`` ·
      ``(Drafts)`` · ``(Sent)`` · ``($Alarms)`` · ``(TrashBackup)`` · ``(규칙)`` · ``(폴더템플릿)``)는 제목이 ``(`` 로 시작한다.
      쓰는 사람이 지은 폴더의 제목(``@title``)은 ``부모\\자식`` 꼴로 경로를 다 든다 — 쉼표 · 점이 든 이름이 있다. 보기 목록에는
      제목이 겹치는 항목도 있어(폴더는 아니었다) 보기를 제목으로 찾을 때는 폴더를 뺀다 (A2)
    * 폴더마다의 보기는 **unid 로만 열린다**(``/<unid>?ReadViewEntries`` — 제목을 넣으면 0줄). 기본 정렬이 날짜 내림차순이고
      ``count`` 는 1000에서 잘린다. 열이 받은편지함과 달라 받는 꼴(``xrtype``) · 중요도(``xImportance``) · 관련 문서
      (``xrelatedid``)가 없고 ``nh_read`` · ``LOCALSAVE`` · ``Security`` 가 있다 — 받는 꼴 · 중요도는 모든편지함에서 unid 로 채운다 (A2)
    * 폴더 보기의 칸 꼴은 받은편지함과 다르다. 보낸 사람 열 ``xname`` 은 ``<이름>-ENG-<영문>`` 이라 ``-=spl=-`` 도 주소도 없다 —
      보낸 분 주소는 모든편지함에서 unid 로 채운다. 읽음 열 ``read`` 는 낱말이 아니라 HTML 조각
      ``<div  id='<unid>'><a href='#' class='mail_21'></a>…</div>`` 이고, class 는 ``mail_21`` 안 읽음 · ``mail_22`` 읽음 둘뿐이라
      회신함 · 전달함을 못 가린다 — 그 표시도 모든편지함의 ``read`` 에서 채운다. ``nh_read`` 는 읽음 표지로 안 쓴다 (A5 · K2)
    * 모든편지함(``XML_모든편지함`` — 이 보기 이름은 한 메일함으로만 쟀다)은 받은 것 · 보낸 것 · 폴더를 다 든다. 정렬 없이
      부르면 이미 날짜 내림차순이다. ``&ResortDescending=1`` 을 붙이면 내림차순 두 덩이가 이어 붙어 와(가장 새 메일이 뒤 덩이
      머리) 창에서 끊으면 새 메일을 놓친다 — 무엇이 두 덩이를 가르는지는 모른다. ``xname`` · ``read`` 는 받은편지함과 같은 꼴이다 (A2 · A4)
    * ⚠ **모든편지함의 폴더 열 ``xfoldername`` 은 폴더의 진본이 아니다** — 하위 폴더는 끝 이름만 오고, 어느 폴더 보기에도 없는
      메일이 폴더 이름을 들고 있고, 받은편지함 메일이 폴더 이름을 들기도 한다. 그래서 그 열은 안 읽는다 — 폴더는 폴더 보기가 든다 (A2)
    * 보낸편지함 보기 ``XML_Sent`` 는 받은편지함과 같은 ``?ReadViewEntries`` 이고, 그 보기의 ``xname`` 열이 수신인이다
    * 메일 서버 첫 화면(``/``)은 세션 주인의 메일 파일 경로를 ``var mailfile = "<경로>.nsf"`` 로 들고 받은편지함으로 넘긴다 —
      웹메일 주소를 사람에게 안 물어도 된다. 끊긴 세션은 그 줄이 없는 화면이다
    * 임시보관함은 보기 ``XML임시편지함`` 이다(``?ReadViewEntries`` · 열은 받은편지함과 같은 꼴 · 보낸 사람 열이 쓰는 사람 자신)
    * 검색은 웹메일 검색 창이 부르는 ``/<db>/ag_detail_search_mailbox?open&…`` 이고 JSON(``total`` · ``page`` · ``data``)을 준다.
      ``stype=chatbot`` 에 칸 ``ssbj`` 제목 · ``sbdy`` 본문 · ``satt`` 첨부 이름과 범위 ``mbox``(``all`` · ``inbox`` · ``sent`` ·
      ``draft`` · ``star`` · ``unread`` · ``trash``)를 준다 — 그 꼴이 아닌 칸만 주면 빈 답(0 바이트)이다. 칸을 여럿 주면 그 칸을
      다 든 메일만 온다(「제목 또는 본문」이 아니다). ``all`` 은 임시보관함을 안 든다. 줄의 폴더는 ``category`` 의 ``[이름]``
      (임시보관함 · 휴지통은 빈 칸 · 받은편지함은 ``[${INBOX}]`` · 보낸편지함은 ``[${SENT}]`` — 메일함마다 같은 시스템 표지다),
      시각은 UTC 다. 낱말은 고른 말 그대로 맞춘다 — 「워크샵」과 「워크숍」은 다른 말이다
    * 주소록 ``/common/profile.nsf/ag_org_search_json?OpenAgent`` 는 이름 · 메일 · 사번으로 찾고 밖의 주소는 0건이다.
      답은 ``{dept, user, total}`` 이다. ``company`` 는 조직도 고름 상자의 값(``<회사>(<코드>)``)이고 메일함마다 다르다.
      ``key`` 가 그 사람의 Notes 이름이다 — 주소로 찾은 40 / 40 · ``CN=`` 이름으로 찾은 30 / 30 이 맞았다. 부서 이름을
      ``search_key`` 로 주면 사람은 0 명이고 이름이 든 부서들만 ``dept`` 에 온다. 직급 · 직책 이름으로는 0 건이다
    * 조직도는 웹메일 받는 사람 고름 창의 손 둘이다(``orgtree.js``). ``ag_tree_dept_json`` 은 ``dept=<부서 코드>`` 의 바로 아래
      부서들(``result[]`` · ``key`` 가 코드 · ``depth`` · ``has_child`` · 부서 메일 주소)이고 ``dept`` 에 회사 값을 주면 맨 위
      부서다. ``ag_tree_user_json`` 은 그 부서에 바로 든 사람이다(하위 부서는 안 든다 · 칸은 주소록 찾기와 같고 ``dept_code`` ·
      퇴직 칸이 없다 · 비면 ``type`` 이 ``nothing`` 인 한 줄). 본부장은 「임원」과 제 본부에 함께 든다. 전사 189 부서 ·
      3,388 명을 받는 데 15 초다(2026-11-07)
    * 배포그룹은 ``ag_org_search_json`` 의 ``type=group`` · ``group_type`` (직책 · 직급 · 지역)이 목록(``group[]`` · ``key`` 는
      ``[02:직책]리더(02)`` 꼴)을, ``/common/lib_f.nsf/agGetDistribute?openagent&groupname=<key>`` 가 구성원(``memberlist[]``
      — 이름 · 직급 · 부서 · 메일)을 준다. 개인 주소록은 ``type=private`` 이다(이 메일함은 비었다)
    * 세션 확인 ``/common/lib_f.nsf/checksessionstatus?Openpage`` → ``{"status":"login"}`` — 웹메일이 수십 초마다 부르는
      주소이고 메일을 안 건드린다. 세션이 끊긴 때의 이 주소의 답은 안 쟀다 — 그 꼴이 아니면 다 「끊겼다」로 본다 (C)
    * 읽음으로는 ``/<db>/XML_Inbox/<unid>?OpenDocument``, 안 읽음으로는 ``/<db>/ag_read_cancel?OpenAgent&docid=<unid>&imapuser=0``
      (200 · 빈 HTML)이다. 받은편지함 메일로만 쟀다 — 폴더에만 있는 메일에 읽음으로의 주소가 먹는지는 안 쟀다 (D · A3)
"""

from __future__ import annotations

import html
import http.cookiejar
import json
import logging
import os
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

DEFAULT_COOKIES = "~/.mailbox-session.json"
DEFAULT_TIMEOUT = 30.0
HTTP_NOT_SERVED = 501             # 본문 주소에 이 답을 내는 메일이 있다 — 「본문 없음」으로 받는다

# 보기 — 이름은 실측(받은편지함 · 보낸편지함 · 받는 사람 목록 · 모든편지함)
INBOX_VIEW = "XML_Inbox"
SENT_VIEW = "XML_Sent"
RECIPIENT_VIEW_TITLE = "!전체목록추출용"
ALL_VIEW_TITLE = "XML_모든편지함"
DRAFT_VIEW_TITLE = "XML임시편지함"
DRAFTS_FOLDER = "(Drafts)"          # 임시보관함 줄의 folder — 시스템 폴더 이름 그대로
SENT_FOLDER = "(Sent)"              # 보낸편지함 줄의 folder — 같은 꼴
# 검색 손이 시스템 편지함을 가리키는 표지(``category`` 의 ``[${…}]`` · 메일함마다 같다) → 줄의 folder
SEARCH_SYSTEM_BOXES = {"${INBOX}": "", "${SENT}": SENT_FOLDER}
# 검색 — 웹메일 검색 창이 부르는 손(목록 JSON). 범위는 그 창의 고름 상자 값이고, 「전체」는 임시보관함을 안 든다(머리말)
SEARCH_AGENT = "ag_detail_search_mailbox"
SEARCH_SCOPES = ("all", "inbox", "sent", "draft", "star", "unread", "trash")
SEARCH_SLOTS = {"subject": "ssbj", "body": "sbdy", "attachment": "satt"}   # 제목 · 본문 · 첨부 이름 → 검색 손의 칸
SEARCH_FIELDS = tuple(SEARCH_SLOTS)
SEARCH_PAGE_MOST = 100
# 메일 서버 첫 화면 — 세션의 주인 메일함 경로를 든다(그 화면이 받은편지함으로 넘기는 스크립트의 값)
MAILFILE_IN_ROOT = re.compile(r'var\s+mailfile\s*=\s*"([^"]+\.nsf)"', re.IGNORECASE)
SYSTEM_FOLDER_MARK = "("          # 시스템 폴더의 제목은 이 글자로 시작한다
FOLDER_SEPARATOR = "\\"           # 폴더 제목의 부모 · 자식 가름

# 받은편지함 목록 열
COLUMN_SUBJECT, COLUMN_FROM, COLUMN_DATE, COLUMN_DATE_SORT = "xsubject", "xname", "xdate", "$91"
COLUMN_SIZE, COLUMN_IMPORTANCE, COLUMN_ROLE = "xsize", "xImportance", "xrtype"
COLUMN_ATTACHMENTS, COLUMN_READ, COLUMN_RELATED = "attachment", "read", "xrelatedid"
# 보낸편지함 목록 열 — 이 보기의 xname 은 수신인이다
SENT_COLUMN_TO = "xname"
# 받는 사람 목록 보기의 열 — 날짜 · 수/발신 · 수신인 · 발신인
VIEW_COLUMN_DATE, VIEW_COLUMN_DIRECTION, VIEW_COLUMN_TO, VIEW_COLUMN_FROM = "$101", "$91", "$102", "$103"

UNREAD_MARK = "ico-nomail"
# 폴더 보기 읽음 열의 HTML 조각 — class 둘뿐이다(안 읽음 · 읽음)
FOLDER_UNREAD_CLASS = "mail_21"
FOLDER_READ_CLASS = re.compile(r"class='(mail_2[12])'")
ATTACHMENT_SEPARATOR = "{}"
SPLIT_MARK, ENG_MARK = "-=spl=-", "-ENG-"
# ECM 을 가리키는 큰 첨부 — <원래 이름>(<확장자>_<크기>KB).html
ECM_ATTACHMENT = re.compile(r"^(?P<name>.+)\((?P<ext>[0-9A-Za-z]+)_(?P<kb>\d+)KB\)\.html$", re.IGNORECASE)
# 그 쪽지 맨 앞의 기계가 읽는 머리와, 그 안의 문서 열쇠 — 열쇠는 ``doc`` 뒤의 16 hex 다
ECM_HEAD = re.compile(r"<!--@!ECM!@(?P<head>.*?)-->", re.DOTALL)
ECM_OBJECT = re.compile(r"<objectId>\s*doc(?P<key>[0-9A-Fa-f]{16})\s*</objectId>")

# 본문 — HTML 은 꼴과 상관없는 한 길, 평문은 조각 하나
BODY_KINDS = ("html", "text")
BODY_TEXT_PART = "M1.1"

# 주소록의 예 · 아니오 칸(퇴직 · 장 여부)이 참인 값
DIRECTORY_YES = ("Y", "1", "TRUE")
# 직급 코드(``grade_code``) → 인사 등급. P 는 직원 · 임원 1–10, E 는 현장 직군 1–7 — 같은 글자 안에서만 위아래가 선다.
# 원본은 사람이 준 인사 등급표(직급명 · 직책명 · 직급명칭명)이고, 코드와의 짝은 2026-11-07 전사 조직도에서 직급명칭명 ·
# 직책 구성이 표와 맞는 것으로 맞췄다. 29 · 30(둘 다 「임원」)과 34 · 35(둘 다 「과장」)의 차례는 직책 구성과 코드 차례로 고른 것이다.
# 연구직(45–49) · 소장(44) · 이사(10) · 고문 · 외주직은 표에 없어 등급이 없다
GRADE_LEVELS = {
    "24": "P1", "23": "P2", "22": "P3", "21": "P4", "26": "P5", "27": "P6", "28": "P7", "29": "P8", "30": "P9", "31": "P10",
    "43": "E1", "42": "E2", "36": "E3", "35": "E4", "34": "E5", "33": "E6", "32": "E7",
}
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
ORG_WORKERS = 8                  # 나무 · 구성원을 함께 묻는 수 — 전사 189 부서 · 3,388 명이 17 초다
DUTY_SEPARATOR = "||"            # 업무 칸은 「업무||근무 꼴||휴무」 — 앞 조각이 업무다
# 받는 사람 목록이 사람을 드는 꼴 — Notes 이름(``CN=…/OU=…`` 또는 약식 ``이름/OU/O``) · ID(``<영문ID>(<약칭>)``)
NOTES_MARK = "CN="
ID_FORM = re.compile(r"^\s*([^\s()/@]+)\s*\(([^()]+)\)\s*$")

# ⚠ 읽음 표시를 바꾸는 명령 — 읽기 길은 이 주소를 짓지 않고, 지으려 하면 서버에 닿기 전에 막는다
MARKS_AS_READ = re.compile(r"[?&](opendocument|editdocument)\b", re.IGNORECASE)
# 메일함을 바꾸는 주소 전부 — 읽음으로 · 안 읽음으로(되돌리기)
CHANGES_MAILBOX = re.compile(r"[?&](opendocument|editdocument)\b|/ag_read_cancel\b", re.IGNORECASE)
_UNID = re.compile(r"^[0-9A-Fa-f]{32}$")
_HEX32 = r"[0-9A-Fa-f]{32}"

log = logging.getLogger(__name__)


class MailboxError(Exception):
    """메일함을 못 읽었다. 메시지가 사유다."""


class MailboxConfigError(MailboxError):
    """설정이 틀렸다 — 주소 · 쿠키 파일 · 인자. 묻기 전에 잡힌다."""


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
    """서버가 그 주소를 안 준다(HTTP 501) — 본문 주소에 501 을 내는 메일이 있다(머리말 「사내 메일함에서 잰 것」)."""


@dataclass(frozen=True)
class Sender:
    """보낸 사람 열 하나를 푼 것. 밖의 메일은 주소만 차고 이름 · 영문 이름이 빈다."""
    name: str
    addr: str
    name_eng: str = ""


@dataclass(frozen=True)
class Recipient:
    """받는 사람 목록의 한 사람. 주소 없이 오는 사람은 ``notes`` 가 열쇠다 — Notes 이름(``CN=…/O=…``)이나 ``<ID>(<약칭>)``."""
    name: str
    addr: str
    notes: str = ""


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
    """받은편지함 · 폴더 목록의 한 줄. ``unid`` 가 그 메일의 열쇠다. 시각은 메일함이 준 글자 그대로다.

    ``folder`` 는 받은편지함이면 빈 글자, 폴더 보기에서 왔으면 그 폴더의 경로(``부모\\자식``)다. 폴더 줄은 받는 꼴 · 중요도 ·
    관련 문서가 빈다 — 그 보기에 열이 없다. 보낸 분 주소도 빈다. ``read_mark`` 는 읽음 열의 class(``mail_21`` · ``mail_22``)라
    회신함 · 전달함을 못 가린다 — 셋 다 ``Mailbox.list_all`` 로 채운다.
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
class Marks:
    """모든편지함 한 줄에서 폴더 보기가 못 드는 칸 — 받는 꼴(``xrtype``) · 중요도(``xImportance``) · 보낸 분(``xname`` 을 푼 것) ·
    읽음 열 글자 그대로(``ico-post`` 회신함 · ``ico-remail`` 전달함 …). 시각은 창에서 끊는 데만 쓴다.

    폴더는 안 든다 — 이 보기의 폴더 열(``xfoldername``)은 경로가 아니다(머리말 「사내 메일함에서 잰 것」).
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
    """검색이 낸 한 줄. ``folder`` 는 검색 손이 준 폴더 이름(``[...]`` 를 벗긴 것 · 받은편지함 · 임시보관함은 빈 글자 · 보낸편지함은
    ``SENT_FOLDER``)이고,
    ``draft`` 는 임시 저장된 메일이다. 시각은 검색 손이 준 글자 그대로(UTC ``YYYYMMDDTHHMMSS,cc Z``)다."""
    unid: str
    subject: str
    sender: str
    date: str
    folder: str
    attached: bool
    unread: bool
    draft: bool


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
        """인사 등급(``P5`` · ``E3`` …) — 표에 없는 직급이면 빈 글자."""
        return GRADE_LEVELS.get(self.grade_code, "")


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

def _load_cookies(path: pathlib.Path) -> http.cookiejar.CookieJar:
    """로그인 손이 남긴 Playwright 저장 상태(``{"cookies": [...]}``)를 쿠키 통으로 읽는다. 시한이 지난 쿠키는 버린다."""
    if not path.exists():
        raise MailboxConfigError(f"쿠키 파일이 없다: {path} — 로그인해 세션 쿠키를 먼저 남긴다")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MailboxConfigError(f"쿠키 파일이 깨졌다: {exc}") from exc
    cookies = data.get("cookies") if isinstance(data, dict) else None
    if not isinstance(cookies, list) or not cookies:
        raise MailboxConfigError(f"쿠키 파일에 쿠키가 없다: {path}")

    jar = http.cookiejar.CookieJar()
    now = time.time()
    for item in cookies:
        expires = item.get("expires", -1)
        if expires not in (-1, None) and expires < now:
            continue
        domain = item["domain"]
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name=item["name"], value=item["value"], port=None, port_specified=False,
            domain=domain, domain_specified=True, domain_initial_dot=domain.startswith("."),
            path=item.get("path", "/"), path_specified=True, secure=bool(item.get("secure")),
            expires=None if expires in (-1, None) else int(expires), discard=expires in (-1, None),
            comment=None, comment_url=None, rest={}))
    return jar


def discover_mailbox(server: str, cookies_file, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """그 세션의 주인 메일함 주소(``<서버>/<경로>.nsf``)를 메일 서버 첫 화면에서 받는다 — 사람에게 묻지 않는다.

    첫 화면은 세션 주인의 메일 파일 경로를 들고 받은편지함으로 넘긴다(머리말). 그 경로가 없으면(끊긴 세션의 SSO 화면)
    ``SessionExpired``, 서버에 못 닿으면 ``MailboxError``. 읽음 표시를 안 바꾼다.
    """
    root = server.strip().rstrip("/")
    if not re.match(r"^https?://[^/]+$", root, re.IGNORECASE):
        raise MailboxConfigError(f"메일 서버 주소(http://<호스트>)가 아니다: {server!r}")
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_load_cookies(pathlib.Path(cookies_file).expanduser())),
                                         _NoRedirect())
    try:
        with opener.open(root + "/", timeout=timeout) as response:
            text = response.read().decode(_charset(response.headers.get("Content-Type", "")), errors="replace")
    except _Redirected as exc:
        raise SessionExpired(f"세션이 끊겼다(→ {exc.location}) — 다시 로그인한다") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise MailboxError(f"메일 서버에 못 닿았다: {exc}") from exc
    found = MAILFILE_IN_ROOT.search(text)
    if not found:
        raise SessionExpired("메일 서버 첫 화면에 메일 파일 경로가 없다 — 세션이 끊겼다(다시 로그인한다)")
    return f"{root}/{found.group(1).lstrip('/')}"


class Mailbox:
    """메일함 하나. 읽기 길의 손은 다 읽기 전용이다 — 메일함을 바꾸는 손은 ``mark_read`` · ``mark_unread`` 둘뿐이다."""

    def __init__(self, url: str, cookies_file, *, view: str = INBOX_VIEW, timeout: float = DEFAULT_TIMEOUT):
        """``url`` 은 ``…/<이름>.nsf`` 까지 든 메일함 주소(그 뒤는 버린다), ``view`` 는 ``list`` 가 읽는 받은편지함 보기다.

        주소 · 쿠키 파일이 틀리면 묻기 전에 ``MailboxConfigError``.
        """
        match = re.match(r"^(https?://[^/]+)(/.+?\.nsf)", url.strip(), re.IGNORECASE)
        if not match:
            raise MailboxConfigError(f"메일함 주소(…/이름.nsf)가 아니다: {url!r}")
        self.server, self.db_path = match.group(1), match.group(2)
        self.base = self.server + self.db_path
        self.view = view
        self.timeout = timeout
        self._collections: list[dict] | None = None
        jar = _load_cookies(pathlib.Path(cookies_file).expanduser())
        # 리다이렉트를 따라가지 않는다 — 끊긴 세션은 SSO 로 보내는데, 따라가면 쿠키가 SSO 에 실린다
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar), _NoRedirect())
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

    def _open(self, url: str) -> tuple[bytes, str]:
        try:
            with self._opener.open(url, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except _Redirected as exc:
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

        한 번에 한 칸이다 — 검색 손은 칸을 여럿 주면 그 칸을 다 든 메일만 낸다(머리말). 여러 칸 · 여러 범위를 합치는 일은
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

    def ecm_key(self, mail: Entry | str, name: AttachmentName | str) -> str:
        """ECM 첨부 하나가 가리키는 문서함 문서의 열쇠(16 hex 글자)를 낸다 — 쪽지를 받아 그 머리에서 꺼낸다.

        ECM 첨부가 아니면 ``MailboxConfigError``. 쪽지에 머리나 열쇠가 없으면 ``MailboxError`` — 꼴이 바뀌었거나 다른 쪽지다.
        """
        listed = name.listed if isinstance(name, AttachmentName) else name
        if not ECM_ATTACHMENT.match(listed):
            raise MailboxConfigError(f"ECM 첨부가 아니다 — attachment 로 받는다: {listed!r}")
        # 머리를 먼저 본다 — 쪽지는 다른 주소로 넘기는 스크립트 페이지라, 로그인 화면 판정은 머리가 없을 때만 한다
        data, _ = self._get(f"/0/{_unid(mail)}/$FILE/{urllib.parse.quote(listed)}")
        text = data.decode("utf-8", "replace")
        head = ECM_HEAD.search(text)
        found = ECM_OBJECT.search(head.group("head")) if head else None
        if not found:
            if _looks_like_login(text):
                raise SessionExpired("ECM 첨부 대신 로그인 페이지가 왔다 — 다시 로그인한다")
            raise MailboxError("ECM 첨부의 머리에 문서 열쇠(objectId)가 없다 — 쪽지 꼴이 잰 것과 다르다")
        log.info("ECM 첨부: 열쇠를 꺼냈다")
        return found.group("key")

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
        웹메일이 빈 값으로 보내는 칸이다(무엇을 가르나는 안 쟀다). 답이 dict 가 아니면 ``MailboxError``.
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

    # ── 메일함을 바꾸는 손 — 사람이 그 메일 하나를 분명히 고른 뒤에만 부른다(머리말) ──────────────

    def mark_read(self, mail: Entry | str) -> None:
        """⚠ 메일함을 바꾼다 — 그 메일 하나를 읽음으로. 읽기 길은 이 손을 부르지 않는다.

        받은편지함 메일로만 쟀다 — 폴더에만 있는 메일에 먹는지는 안 쟀다. 끊긴 세션이면 ``SessionExpired``(반영되지 않았다).
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


# ── 풀기 ─────────────────────────────────────────────────────────────────

def read_only_patterns(db_path: str) -> tuple[re.Pattern, ...]:
    """읽기 길이 물을 수 있는 주소 꼴(서버 뿌리부터의 경로 · 질의) — 다 읽음을 안 바꾸는 것으로 잰 꼴이다. 닫힌 목록이라 새 꼴은
    여기에 더해야 묻는다. ``directory_survey.py`` 가 웹메일에서 잡은 요청을 이 목록에 대 본다."""
    db = re.escape(db_path)
    return tuple(re.compile(p, re.IGNORECASE) for p in (
        rf"^{db}/[^/?]+\?ReadViewEntries(&[\w$%.=-]*)*$",
        rf"^{db}/api/data/collections$",
        rf"^{db}/0/{_HEX32}/Body\?OpenField$",
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
        """이름 · 코드가 그 말과 같은 부서 — 같은 것이 없으면 이름에 그 말이 든 부서다. 띄어쓰기 · 대소문자는 안 가린다."""
        want = _squash(words)
        if not want:
            return []
        exact = [d for d in self.depts.values() if want in (_squash(d.name), _squash(d.code))]
        return exact or [d for d in self.depts.values() if want in _squash(d.name)]

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


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text or "").casefold()


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
            return " ".join(t.strip() for t in data.itertext() if t.strip())
    return ""


def _is_folder(view: dict) -> bool:
    return str(view.get("@folder")).casefold() == "true"


def folder_order(path: str) -> tuple:
    """폴더 경로의 차례 — 부모 · 자식 마디마다 견준다(「부모 2」가 「부모」와 「부모\\자식」 사이에 끼지 않게)."""
    return tuple(part.casefold() for part in path.split(FOLDER_SEPARATOR)), path


def _found(row: dict) -> Found:
    """검색 손의 한 줄(JSON)을 푼다. 폴더 칸은 ``[이름]`` 꼴이고, 시스템 편지함 표지는 ``SEARCH_SYSTEM_BOXES`` 로 푼다."""
    category = str(row.get("category") or "").strip()
    folder = category[1:-1] if category.startswith("[") and category.endswith("]") else category
    folder = SEARCH_SYSTEM_BOXES.get(folder, folder)
    who = str(row.get("from") or "")
    return Found(unid=str(row.get("unid") or "").upper(), subject=html.unescape(str(row.get("subject") or "")),
                 sender=who.split(ENG_MARK, 1)[0].strip() or who.strip(), date=str(row.get("date") or ""),
                 folder=folder, attached=str(row.get("attach") or "") == "T",
                 unread=UNREAD_MARK in str(row.get("icon") or ""), draft=str(row.get("isdraft") or "") == "Y")


def _entry(entry: ET.Element, *, folder: str = "") -> Entry:
    mark = _column(entry, COLUMN_READ)
    unread = UNREAD_MARK in mark
    found = FOLDER_READ_CLASS.search(mark) if folder else None
    if found:   # 폴더 보기의 읽음 열은 HTML 조각이다 — class 가 안 읽음 · 읽음을 가른다(머리말)
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


class _Redirected(Exception):
    def __init__(self, location: str):
        super().__init__(location)
        self.location = location


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise _Redirected(newurl)
