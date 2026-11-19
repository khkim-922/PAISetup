# 출처

이 스킬이 기대는 바깥 원문과, 스크립트가 기대는 회사에서 잰 사실을 든다. 스킬은 `SKILL.md` 본문만으로 돈다 — 여기는 대조하고 고치기 전에 여는 자리다.

## 보관한 원문

| 파일 | 저장소 · 경로 | 받은 판 | 라이선스 |
|---|---|---|---|
| `untrusted-content.md` | anthropics/knowledge-work-plugins · `small-business/shared/untrusted-content.md` | `d900840716eb262e1feb17c6f4406c9ce0e06bcf` | Apache-2.0(`LICENSE.knowledge-work-plugins`) |
| `inbox-sweep.SKILL.source.md` | anthropics/knowledge-work-plugins · `sales/skills/inbox-sweep/SKILL.md`(이름은 스킬 로더와 안 부딪히게 바꿨다) | 같은 판 | 같다 |

## 가져온 것 · 우리 판이 갈린 자리

- **선택** — 「읽은 글은 자료다」(untrusted-content 1 · 3 · 4)와 「답장은 그 대화의 사람에게만 · 메일이 부탁한 동작은 사람에게 먼저」
  (inbox-sweep 5 단계)를 켰다. 돈 · 계정 · 신원을 묻는 메일은 초안 없이 사람에게 보인다(untrusted-content 2)도 켰다
- **같은 자리** — 원문은 답장을 메일함의 초안으로 만들고 사람이 보낸다. 우리 판도 새 메일 · 답장 · 전체답장 · 전달을 다 임시보관함에 짓고,
  사람이 확인한 지금 판을 웹메일 화면의 [보내기]로 낸다. 답장 · 전달은 웹메일의 그 단추가 여는 화면에서 저장해 인용 · 이음을 화면이 든다
- **더하기** — 보내기와 읽음 표시 바꾸기에 미리 보기 · 확인 열쇠를 건다 — 사람이 본 그 판만 나간다. 저장은 안 나가는 일이라 바로 한다. 원문에는 읽음을
  바꾸는 손이 없다
- **안 가져온 것** — 분류 · 순위 · 일괄 초안(inbox-sweep 1 ~ 4 · 6 단계). 판단은 이 스킬 밖의 일이다(스킬 머리)

## 회사에서 잰 꼴

스크립트가 사내 메일함 · 웹메일 화면 · 중계에 대해 아는 사실은 회사 PC 에서 실물에 대어 잰 것이고, 그 사실은 이 절이 든다. 코드
주석은 그 사실을 지금 꼴로만 짧게 적고 여기를 이름으로 가리킨다. 아래 자리의 사실은 **회사 PC 에서 다시 재기 전에는 바꾸지 않는다** —
바꾸면 집에서 도는 검사는 초록인 채 실물에서 조용히 깨진다.

이 절 밖에 사실이 선 자리:

- `scripts/inbox.py` — 보기 이름 · 열 이름 · 주소 꼴 상수, 폴더 · 규칙 · 임시저장 폼의 칸과 그 함수 머리
- `scripts/draft_send.js` — 발송 확인 · 임시저장 물음의 꼴(`SEND_CONFIRM` · `SAVED_ASK`) · 기다리는 시한
- `scripts/mail.py` — 보낸 메일이 서는 자리(`SENT_CHECK_ROWS`) · 검색 색인이 새 메일을 늦게 드는 것(`RECENT_SCAN`) · 받는 꼴(`ROLE_WORDS`)
- 사내 주소록 · 조직도 · 배포그룹 · 직급 등급 · 회사 값 · 메일함 파일 번호가 사번이라는 것 · 부서 주소 꼴 — 묻는 손은 `scripts/inbox.py` 지만
  사실은 형제 스킬 company-directory 의 `references/SOURCES.md` 「회사에서 잰 꼴」 이 든다
- `scripts/body_images.py` — 본문 아이콘 크기(`ICON_EDGE`)
- 설정 저장소의 `_check/skills/company-mail/check_inbox.py` · `check_mail.py` · `check_mailer.py` — 가짜 메일함 · 중계는 이 절의 꼴을 흉내 낸다. 실물에서 꼴이 달라졌으면
  가짜를 먼저 실물에 맞추고 손을 고친다

### inbox.py

#### inbox.py · 메일함 · 세션

어기면 조용히 망가진다. 바탕 사실의 원본은 사내 환경 기록(``~/.claude/posco/ENV-posco.md`` 「네트워크 접근」)이다.

- IMAP · POP3 는 닫혀 있다. 열린 길은 웹(80 · 443)뿐이고, 앞에 사내 SSO 가 선다
- ⚠ **문서를 여는 주소(``?OpenDocument`` · ``?EditDocument``)를 부르면 그 메일이 읽음으로 바뀌고, ``ag_read_cancel`` 은 안 읽음으로
  바꾼다.** 목록(``?ReadViewEntries``) · 본문(``/0/<unid>/Body?OpenField`` · 조각 ``/Body/M…?OpenElement``) · 첨부(``/$FILE/``) ·
  보기 목록 · 주소록 · 세션 확인은 안 바꾼다. 그래서 읽기 길은 그 꼴(``read_only_patterns``)에 맞는 주소만 묻는다 — 닫힌 목록이라,
  새 꼴은 읽음을 안 바꾸는 것을 잰 뒤 거기에 더해야 묻는다
- 세션이 끊기면 서버가 오류 대신 **200 에 SSO 로 보내는 HTML** 을 준다 — 상태 코드로는 못 가린다. 답의 꼴(XML · JSON · 기대한 형식)과
  SSO 로 보내는 스크립트(``_looks_like_login``)로 가린다. 낱말 「swpsso」만으로는 안 가른다 — 본문에 SSO 주소를 적은 사내 안내를 끊긴
  세션으로 읽는다. 리다이렉트는 따라가지 않는다 — 따라가면 쿠키가 SSO 에 실린다
- 메일 서버 첫 화면(``/``)은 세션에 로그인한 사람의 메일 파일 경로를 ``var mailfile = "<경로>.nsf"`` 로 들고 받은편지함으로 넘긴다 —
  웹메일 주소를 사람에게 안 물어도 된다. 끊긴 세션은 그 줄이 없는 화면이다
- 세션 확인 ``/common/lib_f.nsf/checksessionstatus?Openpage`` → ``{"status":"login"}`` — 웹메일이 수십 초마다 부르는 주소이고
  메일을 안 건드린다. 세션이 끊긴 때의 이 주소의 답은 안 쟀다 — 그 꼴이 아니면 다 「끊겼다」로 본다
- 읽음으로는 ``/<db>/XML_Inbox/<unid>?OpenDocument``, 안 읽음으로는 ``/<db>/ag_read_cancel?OpenAgent&docid=<unid>&imapuser=0``
  (200 · 빈 HTML)이다. 받은편지함 메일로만 쟀다 — 폴더에만 있는 메일에 읽음으로의 주소가 먹는지는 안 쟀다

#### inbox.py · 받은편지함 · 보낸편지함 · 임시보관함

- 받은편지함 목록의 ``read`` 열 — ``ico-nomail`` 이 안 읽음이다(되돌린 메일은 ``z^ico-nomail``). ``ico-okmail`` 읽음 · ``ico-post``
  회신함 · ``ico-remail`` 전달함은 다 읽은 것이다
- 보낸 사람 열 ``xname`` — 사내 메일은 ``<이름>-=spl=-<이름> &lt;<주소>&gt;-ENG-<영문>-=spl=-<영문>&lt;<주소>&gt;`` 이 XML 안에서
  한 번 더 이스케이프돼(``&amp;lt;``) 온다. 밖의 메일 · 시스템은 주소만 온다
- 받는 꼴 열 ``xrtype`` — ``T`` 받는사람 · ``C`` 참조 · ``G`` 받는 사람 목록 밖의 그룹 · 배포 목록
- 받은편지함 보기(``XML_Inbox``)는 받은편지함만 든다 — 쓰는 사람의 규칙이 하위 폴더로 옮긴 메일은 그 폴더의 보기에만 있다
- 보낸편지함 보기 ``XML_Sent`` 는 받은편지함과 같은 ``?ReadViewEntries`` 이고, 그 보기의 ``xname`` 열이 수신인이다
- 임시보관함은 보기 ``XML임시편지함`` 이다(``?ReadViewEntries`` · 열은 받은편지함과 같은 꼴 · 보낸 사람 열이 쓰는 사람 자신)
- 보기 한 번(``?ReadViewEntries``)의 ``count`` 는 서버가 1000 에서 자른다(``VIEW_PAGE_MOST``)

#### inbox.py · 받는 사람

- 받은 메일의 받는 사람은 받은편지함 목록에 없고(``SendTo?OpenField`` 는 501) 보기 ``!전체목록추출용`` 의 ``$102`` 열이 든다 —
  받는사람과 참조를 합친 한 글줄이고 사람마다 Notes 이름 · ``<이름> <주소>`` · ``<ID>(<약칭>)`` · 주소만 꼴이 섞인다. 기본 정렬이
  날짜순이 아니라 ``&ResortDescending=1`` 로 날짜 내림차순을 받는다. 보기의 unid 는 ``/api/data/collections`` 에서 제목으로 찾는다 —
  이 보기 이름은 한 메일함으로만 쟀다
- 보낸 메일의 받는 사람은 보낸편지함 목록 열(``xname``)에 첫 사람만 들고, 한 통의 ``SendTo?OpenField`` 는 501 이다. 다 드는 자리는
  그 메일의 ``ToCcUserInfoJson``(받는 사람 · 참조) · ``BccUserInfoJson``(숨은참조) 칸이다 — 편집 화면이 저장할 때 받는
  사람마다 ``<열쇠>-=-ITEM-=-<JSON>`` 을 ``-=-SEP-=-`` 로 이어 쓴 글이다. JSON 의 ``type`` 이 ``user``(열쇠는 Notes 이름) ·
  ``dept``(웹메일 고름 창에서 조직을 체크한 것 · 열쇠는 ``<부서 코드>(<회사 약칭>)`` · 부서 이름 · 부서 주소가 든다) · ``email``
  (사외 주소)이고 ``field`` 가 ``send_to`` · ``copy_to`` 다. 숨은참조 칸의 항목은 ``field`` 가 비어 온다. 숨은참조 칸은 임시메일에만 남는다 — 보낸 뒤에는 숨은참조를 넣어 보낸 메일도 404, 넣지 않은 메일 대부분은 501 이라(보낸편지함 40 통 · 2026-11-18 회사에서 잼) 보낸 메일의 숨은참조는 못 읽는다. 새 메일 화면으로 지은 임시메일은 받는 사람 칸까지 501 이다. 보기 ``!전체목록추출용`` 의
  ``$102`` 는 보낸 메일 대부분에 줄이 없고, 든 줄도 마지막 사람들이 마침표로 붙어 온다 — 보낸 메일의 받는 사람으로 쓰지 않는다

#### inbox.py · 본문 · 첨부

- 본문 ``/0/<unid>/Body?OpenField`` 는 조각 꼴(평문만 · 평문+HTML · ``multipart/related``)과 상관없이 HTML 본문을 한 번에 준다.
  이 주소에 HTTP 501 을 내는 메일이 있다(무엇이 501 을 내는지는 모른다) — 404 와 같이 「본문 없음」(None)으로 낸다
- 조각 ``/Body/M1.1?OpenElement`` 는 평문 · HTML 둘을 든 메일의 평문이다. 다른 꼴(``multipart/related`` 는 본문이 ``M1.1.1``)의
  ``M1.1`` 은 안 쟀다 — 그 자리에 ``text/plain`` 이 아닌 것이 오면 평문 조각은 없는 것으로 낸다
- 첨부 이름은 ``attachment`` 열에 ``{}`` 로 이어 온다. 큰 첨부는 ECM 을 가리키는 ``<원래 이름>(<확장자>_<크기>KB).html`` 이다.
  그 html 은 문서가 아니라 쪽지다 — 같은 ``$FILE`` 주소로 받아지고, 맨 앞 주석 ``<!--@!ECM!@ … -->`` 안의
  ``<objectId>doc<16 hex></objectId>`` 는 원래 문서의 열쇠고, 본문 링크(``swp_interface.jsp?ACTID=viewlink&OBJECTID=<hex>``)의
  ``OBJECTID`` 를 ASCII 로 푼 16 hex 는 사람이 첨부를 누를 때 화면이 여는 문서의 열쇠다. 둘은 대개 같지만 다를 때가 있고, 다르면
  머리 값으로는 열기 표(``OpenContents``)는 와도 에이전트가 답하지 않는다 — 그래서 링크 값을 먼저 쓴다(메일 · 게시판 둘 다)

#### inbox.py · 폴더 보기 · 모든편지함

- 폴더 목록은 보기 목록(``/api/data/collections``)의 ``@folder: true`` 항목이다. 시스템 폴더(``($Inbox)`` · ``($Trash)`` ·
  ``(Drafts)`` · ``(Sent)`` · ``($Alarms)`` · ``(TrashBackup)`` · ``(규칙)`` · ``(폴더템플릿)``)는 제목이 ``(`` 로 시작한다. 쓰는
  사람이 지은 폴더의 제목(``@title``)은 ``부모\\자식`` 꼴로 경로를 다 든다 — 쉼표 · 점이 든 이름이 있다. 보기 목록에는 제목이
  겹치는 항목도 있어 보기를 제목으로 찾을 때는 폴더를 뺀다
- 폴더마다의 보기는 **unid 로만 열린다**(``/<unid>?ReadViewEntries`` — 제목을 넣으면 0줄). 기본 정렬이 날짜 내림차순이고 ``count``
  는 1000 에서 잘린다. 열이 받은편지함과 달라 받는 꼴(``xrtype``) · 중요도(``xImportance``) · 관련 문서(``xrelatedid``)가 없고
  ``nh_read`` · ``LOCALSAVE`` · ``Security`` 가 있다 — 받는 꼴 · 중요도는 모든편지함에서 unid 로 채운다
- 폴더 보기의 칸 꼴은 받은편지함과 다르다. 보낸 사람 열 ``xname`` 은 ``<이름>-ENG-<영문>`` 이라 ``-=spl=-`` 도 주소도 없다 — 보낸 분
  주소는 모든편지함에서 unid 로 채운다. 읽음 열 ``read`` 는 낱말이 아니라 HTML 조각
  ``<div  id='<unid>'><a href='#' class='mail_21'></a>…</div>`` 이고, class 는 ``mail_21`` 안 읽음 · ``mail_22`` 읽음 둘뿐이라
  회신함 · 전달함을 못 가린다 — 그 표시도 모든편지함의 ``read`` 에서 채운다. ``nh_read`` 는 읽음 표지로 안 쓴다
- 모든편지함(``XML_모든편지함`` — 이 보기 이름은 한 메일함으로만 쟀다)은 받은 것 · 보낸 것 · 폴더를 다 든다. 정렬 없이 부르면 이미
  날짜 내림차순이다. ``&ResortDescending=1`` 을 붙이면 내림차순 두 덩이가 이어 붙어 와(가장 새 메일이 뒤 덩이 머리) 창에서 끊으면
  새 메일을 놓친다 — 무엇이 두 덩이를 가르는지는 모른다. ``xname`` · ``read`` 는 받은편지함과 같은 꼴이다
- ⚠ **모든편지함의 폴더 열 ``xfoldername`` 은 폴더의 진본이 아니다** — 하위 폴더는 끝 이름만 오고, 어느 폴더 보기에도 없는 메일이
  폴더 이름을 들고 있고, 받은편지함 메일이 폴더 이름을 들기도 한다. 그래서 그 열은 안 읽는다 — 폴더는 폴더 보기가 든다

#### inbox.py · 검색

- 검색은 웹메일 검색 창이 부르는 ``/<db>/ag_detail_search_mailbox?open&…`` 이고 JSON(``total`` · ``page`` · ``data``)을 준다.
  ``stype=chatbot`` 에 칸 ``ssbj`` 제목 · ``sbdy`` 본문 · ``satt`` 첨부 이름과 범위 ``mbox``(``all`` · ``inbox`` · ``sent`` ·
  ``draft`` · ``star`` · ``unread`` · ``trash``)를 준다 — 그 꼴이 아닌 칸만 주면 빈 답(0 바이트)이다
- 칸을 여럿 주면 그 칸을 다 든 메일만 온다(「제목 또는 본문」이 아니다). ``all`` 은 임시보관함을 안 든다
- 줄의 폴더는 ``category`` 의 ``[이름]`` 이다 — 임시보관함 · 휴지통은 빈 칸, 받은편지함은 ``[${INBOX}]``, 보낸편지함은 ``[${SENT}]``
  (메일함마다 같은 시스템 표지). 그래서 ``Found.folder`` 로는 휴지통 줄과 받은편지함 줄을 못 가린다. 하위 폴더는 끝 이름만 온다
- 시각은 UTC 다. 낱말은 고른 말 그대로 맞춘다 — 「워크샵」과 「워크숍」은 다른 말이다

#### inbox.py · 주소록 · 조직도 · 배포그룹 · 직급 등급

형제 스킬 company-directory 의 `references/SOURCES.md` 「회사에서 잰 꼴」 이 든다 — 사람을 찾는 스킬이 그 사실의 자리다.

#### inbox.py · 폴더 손

꼴은 웹메일 화면 스크립트 ``mail_posco.js`` 그대로다.

- 폴더 나무는 ``/<db>/fdd_folder_fullpath?ReadViewEntries&outputformat=json&count=-1`` 이다 — 열 ``$6`` 경로 · ``NodeUnid`` 폴더
  열쇠(``newNode<숫자>``) · ``ParentID`` 부모(맨 위는 ``nodeATag2``). 칸 값은 ``{"text": {"0": 값}}`` 꼴이다. 폴더 보기의 unid
  (``folders``)와는 다른 열쇠이고 둘은 경로로 잇는다. 같은 보기가 이전메일함 쪽 짝도 들어, 지운 폴더가 짝이 남은 동안 나무에 남는다 —
  짝을 고르면 서버는 OK 를 내고 아무것도 안 한다
- 만들기는 **GET** ``agt_mail_folder_save?OpenAgent&ulan=kor&act=create&…&pfcode=<부모 열쇠 · 맨 위는 nofolder>&nodeid=<열쇠>`` —
  열쇠는 만드는 쪽이 지어 보내고 서버가 그대로 쓴다. 하위 폴더도 같은 주소이고 경로는 ``부모\\자식`` 이다
- 옮기기는 **POST** ``folder2?OpenForm`` · ``Action=mailmove_action`` · ``nodeUNID=<폴더 열쇠 · 받은편지함은 inbox>`` ·
  ``UNIDs=<unid,…>`` — ``ParaView`` · ``owner`` 를 비워도 옮겨졌다. 읽음 표시는 그대로다. ⚠ 모르는 열쇠 · 빈 열쇠에도 ``OK`` 를
  낸다 — 옮겼다는 증거가 아니다
- 지우기는 **GET** ``agt_mail_folder_save?OpenAgent&ulan=kor&act=delete_action&nodeid=<열쇠>&…&nodefrom=mail`` 에 같은 주소의
  ``afdelete=Y&nodefrom=archive`` 를 한 번 더 — 앞의 것만이면 폴더 보기에선 사라지고 나무에 이전메일함 짝이 남는다. 메일이 든 채
  지우면 그 메일이 휴지통으로 간다. 없는 폴더를 가리킨 규칙이 새 메일을 어떻게 하나는 안 쟀다
- 휴지통으로 보내기(웹메일 목록의 [삭제])는 **GET** ``delete_view?OpenAgent&docid=<unid,…>&folderkey=&type=&paraview=&imapuser=&owner=``
  → 200 · 빈 답이다. 받은편지함 · 폴더 · 보낸편지함 · 임시보관함 메일이 다 같은 주소로 휴지통(``XML_Trash``)에 가고, 여러 통을
  쉼표로 한 번에 보내도 되며, 읽음 표시는 그대로다. ``paraview`` · ``owner`` 를 비워도 같다. 답이 비어 휴지통 보기로 다시 본다.
  ``type=remove`` 는 영구삭제라 짓지 않는다
- 휴지통에서 되살리기는 **GET** ``TrashDoc?OpenAgent&docid=<unid>&imapuser=&owner=&type=recovery`` → ``{ "result":true }`` 이고
  받은 메일은 받은편지함으로 안 읽음 그대로 돌아온다. 임시보관함에 있던 메일은 임시보관함으로 읽음 그대로 돌아온다. 보낸편지함 ·
  폴더에 있던 메일이 어디로 돌아오는지는 안 쟀다. 휴지통 보기(``XML_Trash``)의 열은 받은편지함과 같은 꼴이다(제목 · 보낸 분)
- 폴더 이름은 화면처럼 역슬래시 · 따옴표 · ``| _ < >`` 와 시스템 폴더 이름(``inbox`` · ``$trash`` · ``(drafts)`` …)을 막는다

#### inbox.py · 메일 규칙

꼴은 화면 스크립트 ``fmmailrule.js`` 그대로다.

- 목록은 보기 ``XML_Rule``(``?ReadViewEntries``)이고, 한 건은 그 규칙 문서의 편집 화면 ``/<db>/0/<unid>?EditDocument`` 다 — 규칙
  문서라 메일 읽음과 무관하지만 ``EditDocument`` 는 읽기 길 목록 밖이라 규칙 목록이 낸 unid 로만 연다. 갈래 · 폴더는 화면 머리
  ``new FormJS({…})`` 의 ``form``(``rules`` · ``folder_id``)과 ``folders``(``<경로>|<열쇠>^``)가, 조건 · 맞춤 · 받은/보낸은 입력
  칸의 값이 든다
- 넣기는 **POST** ``Mailrule?OpenForm&Seq=1&viewname=(%24webrule)``, 고치기는 **POST** ``/<db>/0/<unid>?EditDocument&Seq=1``,
  지우기는 **POST** ``Mailrule?OpenForm&Seq=1`` · ``SubmitAction=delete`` · ``ProcessUNID`` — 답은 JSON ``{"result":true, "unid":…}``
  (지우기의 ``unid`` 는 그 규칙이 아니다). 넣은 규칙은 그 뒤 받은 메일에 서버가 곧바로 썼다
- 갈래 ``rules`` 는 ``move_folder`` · ``move_trash`` · ``delete``(화면의 ``copy_folder`` 는 꺼져 있다)이고, 맞춤
  ``rule_fromType2`` · ``rule_toType2`` 는 화면의 「일치 · 포함」 차례로 1 · 0 이다 — 「일치」로 넣었을 때 서버가 어떻게 맞추나는 안 쟀다
- ``AllFwdOpt`` 는 옮기기 규칙에도 1 로 남아 있는 일이 있다 — 자동전달의 표지로 안 쓴다
- 안 잰 것 — 보낸 메일 규칙 · 조건 여럿의 이음(그리고 · 또는) · 규칙의 차례 · 이미 받은 메일에 규칙을 거꾸로 다는 길

#### inbox.py · 임시저장 · 서명

꼴은 쓰기 화면 스크립트 ``fmmail_new.js``(``saveDoc`` · ``getSignature``) · ``xam_handler.js``(``uploadFile``) · 편집기 ``editor.js`` 그대로다.

- 빈 쓰기 화면은 ``/<db>/Memo?openform&opentype=popup`` 이고, 같은 폼(``_Memo``)의 POST 가 저장이다. 저장 칸 ``SaveAgent`` 가
  ``wSave`` 면 임시저장, ``wSend`` 면 그 자리에서 발송된다. 본문은 ``MIMEBody`` 칸에 MIME 머리와 함께 싣는다 — ``Body`` 칸만 채우면
  본문이 비어 저장된다. 답은 JSON 비슷한 글이다(``message_func`` 칸에 함수가 든다)
- 받는 사람은 ``SendTo``(Notes 이름 — 웹메일 화면이 다시 열 때 이 이름으로 사람을 세운다. 주소만 주면 화면에 사람으로 안 선다) ·
  ``InetSendTo``(``"이름" <주소>``) 짝으로 싣는다. 조직은 Notes 이름 자리에 부서 코드, 주소 자리에 부서 주소가 든다
- 첨부는 업로드 DB ``upload/fileupload<사번 끝자리>.nsf`` 의 ``xam_upload?open`` 에 먼저 올리고, 저장 폼에 그 열쇠
  (``<unid>_<unique>_<회사 코드>_<사번>``)를 싣는다. 첨부는 20 개까지, 20MB 를 넘으면 웹메일이 대용량으로 돌려 임시저장이 안 든다
- 서명은 쓰기 화면의 설정 JSON(``signatueYN`` · ``signatue_add1line`` · ``signatureUnid`` — 철자는 웹메일 그대로)이 켜고, 빈 쓰기
  화면은 서명을 안 든다 — 화면 스크립트가 뜬 뒤에 서명 문서의 본문을 따로 받아 편집기에 넣는다. 서명 문서의 본문은 읽기 길의 본문
  꼴(``/0/<unid>/Body?OpenField``)로 받는다. 편집기는 서명을 넣을 때 html · head · title · meta · style · body 태그를 벗긴다 —
  서명의 style 이 남으면 메일 전체 글꼴을 덮는다. 새 메일의 차례는 넣은 글 · (빈 줄) · 서명 · 빈 줄이다
- 메일속성은 쓰기 화면의 체크 칸이고 ``saveDoc`` 이 저장 칸으로 싣는다 — 긴급메일 ``Importance``(켬 ``1`` · 끔 ``2``) · 전달불가
  ``Forward_Deny`` · 한명씩 발송 ``IndividualSend``(켬 ``1`` · 끔 빈 글자) · 예약발송 ``ReservationOpt`` · ``SDay``(``YYYY-MM-DD``) ·
  ``SHour`` · ``SMin``(두 자리). 저장 폼에 그 값을 실으면 저장되고 편집 화면을 다시 열면 체크가 선다(회사에서 시험 임시글로 쟀다).
  예약의 분 고름은 ``Reservation_Interval``(10) 눈금이고, 지난 시각은 [보내기] 때 서버 시각(``agGetServerTime``)과 견줘 막는다 —
  임시저장은 안 막는다. 전달불가는 DRM 복호화 발송(``decryptiondrm``)과 함께 못 고른다(``duplicate_chk``)
- 다른 이름으로 발송(``preferrednameOption`` · ``InetFrom`` 고름)은 프로필의 ``PreferredNameList`` 가 비면 이름이 하나뿐이라 고를 것이
  없다. 회신요청 · 사외제한 · 보고메일 · PWP 등록은 쓰기 화면의 켬 값(``useRemind`` · ``useUnopened`` · ``useBriefing`` ·
  ``UseTaskManagement``)이 ``0`` 인 계정에는 안 선다. 팀즈문서 링크 공유는 따로 뜨는 고름 창(``frmTeamsAttachFileManager``)이다 · 안 쟀다
- 배포그룹 하나를 받는 사람으로 넣으면 ``SendTo`` 계열 칸에 그룹 열쇠(``[<회사 코드>:<갈래 말>]<이름>(<회사 코드>)``), ``InetSendTo``
  계열에 그룹 이름이 들고(``checkUser``), ``ToCcUserInfoJson`` · ``BccUserInfoJson`` 에 「열쇠 ``-=-ITEM-=-`` {type: group, key,
  group_name}」 이 ``-=-SEP-=-`` 로 이어 든다(``ORG_JSONTOTEXT``). 그 꼴로 저장한 임시메일은 편집 화면을 다시 열어도 그룹 토큰 하나로 선다
  — 사람으로 안 풀린다(회사에서 쟀다). 정보 칸이 없으면 화면이 열쇠를 「기타」 토큰으로 세운다

### mailer.py

기본 중계에서 잰 것 — 어기면 조용히 망가진다. 바탕 사실의 원본은 사내 환경 기록(`~/.claude/posco/ENV-posco.md` 「네트워크 접근」)이다.

- 인증 없이 25 번으로 받는다. 사내망 밖에서는 닿지 않는다
- STARTTLS 를 광고하지만 핸드셰이크에서 서버가 연결을 끊는다. 그래서 기본은 「시도 → 끊기면 새 연결로 평문」이고 물러난 사실을 경고로
  남긴다 — 본문이 평문으로 사내망을 지난다는 뜻이다
- 일부 수신자만 거절되면 `smtplib` 은 예외 없이 거절 목록만 돌려준다. 그것을 성공으로 세면 누군가 조용히 못 받는다 — 그래서 하나라도
  거절되면 `MailRefused`
- bcc 는 봉투(RCPT)에만 싣고 머리(헤더)에는 쓰지 않는다
- 사내 중계로 보낸 메일은 보낸 사람의 웹메일 보낸편지함에 안 남는다 — 보낸 흔적은 제 주소로 받은 사본뿐이다. 나에게 보낸 사본은 몇 초
  안에 받은편지함에 받는 꼴 `T` 로 오고, 발신자를 주소만으로 주면 보낸 사람 열도 주소만 든다. 남에게 보내며 나를 bcc 에 넣은 사본의 꼴은
  안 쟀다

### draft_send.js

- 답장 · 전달 화면은 웹메일의 단추와 같은 길이다 — `process_doc` 이 원래 메일에 이어진 새 문서를 짓고 편집 화면을 열면, 화면이 제목
  머리(Re: · Fwd:) · 받는 사람 · 서명 · 인용 · (전달이면) 원래 첨부를 채운다. 전달은 받는 사람을 비워 연다
- 편집 화면 주소(`/0/<원래 unid>?EditDocument&type=Reply`)를 바로 열면 머리 · 인용 · 원래 메일과의 이음이 빠진 원래 메일 자체가 열린다.
  저장 전에 멈추면 `process_doc` 이 지은 문서는 임시보관함에 안 서고 남는다(웹메일에서 창을 닫은 것과 같다)
- 저장은 화면의 `saveDoc`(`SaveAgent=wSave`)이다. 임시저장이 끝나면 화면이 「임시저장이 완료되었습니다」 로 창을 유지할지 묻는다
- 한 임시메일을 두 화면에서 열어 저장하면 저장 번호가 어긋나 뒤 화면의 다음 저장이 새 임시메일로 갈라진다(`wSendCheck`)
- 받는 사람 넣기는 화면의 「비서 참조자 자동추가」와 같은 길이다(`ag_org_search_json` → `tokenInput` · `duplicate_list`). 주소록 찾기는
  부서를 `type=org` 에만 내고(`type=memo` 는 부서 0 곳) 부서 주소로는 안 내고 부서 이름으로 낸다
- 웹메일은 보내기 전에 「메일을 발송 하시겠습니까?」 를 묻고, 첨부가 없으면 그 앞에 「첨부 문서가 없는 메일 입니다.」 안내 줄이 붙는다.
  사외 결재 · 경고 같은 다른 물음이 그 앞에 뜰 수 있다
- 서명 그림 주소는 저장 전엔 서명 문서를, 저장 뒤엔 새 임시메일 자신을 가리킨다(`…nsf/0/<unid>/Body/…`)
- 편집기 · 받는 사람 칸 · 첨부 칸은 화면이 뜬 뒤에 늦게 서고, 편집기의 `setBodyValue` 는 늦게 그려진다
- 웹메일 [재사용]은 읽기 화면의 `_form.copyEdit('Resend')` 다 — 답장 · 전달(`copyEdit('Reply' · 'AllReply' · 'Forward')`)과 같은 함수가
  `process_doc?openagent&action=Resend` 로 원래 메일에 이어진 새 문서를 짓고 편집 화면(`?editdocument&type=Resend&UNID=<원래>`)을 연다
- [재사용]은 보낸 메일의 읽기 화면에만 있다(`_form.info.isSent` 가 참) — 받은 메일에는 [답장] · [전체답장] · [전달]뿐이다
- [재사용] 화면은 원래 메일의 받는 사람 · 제목(머리 없이) · 본문 HTML(서명 그대로 · 본문의 `<style>` · 표 · 넣은 글 표지 `TEXT_MARK` 까지)
  · 첨부를 그대로 채운다. 인용 머리(「원본 메시지」)와 서명을 하나 더 붙이지 않는다. 본문 그림 주소는 새 문서를 가리키게 바뀐다
- [재사용] 화면에서 [임시저장]하면 새 임시메일이 서고 원래 보낸 메일은 보낸편지함에 그대로 남는다 — 저장 물음은 답장과 같은
  「임시저장이 완료되었습니다」 하나다
- 답장 · 전달 · 재사용(`copyEdit`) 앞의 알림은 막지 않고 알리기만 한다 — 대용량 첨부 메일은 「다운로드 가능기간 ~ 까지」(답장 둘은 안 뜬다),
  기간이 지났으면 「기간이 경과한 대용량 파일」, 결재취소(반려)된 대용량 메일은 「재사용하실 수 없습니다」다. 전달 금지 메일은 [재사용] 앞에서
  안 막고, 원 발신자가 나인 전달불가 회신 메일만 「답장할 수 없습니다」로 막는다(``Forward_Deny_Type``) — 화면 스크립트로 읽었다 · 알림을
  띄운 메일로는 안 쟀다
- 편집 화면의 메일속성은 체크(``important_check`` · ``notforward`` · ``OnePost`` · ``chbox_reservation``)를 바꾸면 [임시저장]이 그 체크에서
  칸을 싣는다. 예약은 체크 뒤 ``_form.drawTimeList()`` 가 시 · 분 고름(``shour`` · ``smin``)을 그려야 값이 들고, 날짜는 ``SDay`` 칸이다.
  끄고 저장하면 ``Importance`` 2 · ``ReservationOpt`` 0 · ``SDay`` 빈 글자로 선다(회사에서 쟀다)
- 편집 화면에 배포그룹을 더하는 것은 고름 창의 [배포그룹] 탭과 같은 토큰(``{type: group, key, group_name}``)을 ``duplicate_list`` 와
  칸의 ``tokenInput('add')`` 에 넣고 ``setRecipients`` 하는 길이다 — 저장한 판을 다시 열면 그룹 토큰 하나로 선다(회사에서 쟀다)
- 본문 편집기는 DEXT5 다. `_PWEC` 는 `init · isReady · setValue · setBodyValue · getHTML · getMIME · dext5DecodeMime · destroy · isEmpty`
  와 글꼴 · 포커스 · 안내 글 함수만 내는 얇은 덮개고(일부 고치기 함수가 없다), 일부를 고치는 길은 전역 `DEXT5` 에 있다 —
  `getDext5DocumentDom` · `getDext5BodyDom`(편집기 문서 · body 를 그대로) · `replaceText` · `replaceTextAll` · `findWord` · `setElementInnerHTML`
  · `getSelectedContent` · `isDirty` 따위
- 편집기 문서는 편집 화면 안 `iframe#dext_frame_WEC` 안의 `iframe#dext5_design_WEC` 이고 같은 출처라 손이 바로 닿는다. body 는
  `contenteditable`(`designMode` 는 off)이고 id 는 `dext_body` 다
- 화면의 [임시저장] `saveDoc` 은 `_PWEC.getMIME()` 으로 편집기 문서에서 그 자리에서 본문을 짓는다 — 편집기 body 를 바로 고쳐도(글자 마디 하나)
  `isDirty` 가 참이 되고 `getHTML` · 저장에 실린다. 그 길과 `getHTML` → 조각 바꾸기 → `setBodyValue` 의 길은 저장한 본문이 바이트째 같고,
  두 길 다 고친 조각 밖은 그대로다(문서 번호를 빼고 견줘서)
- ⚠ 편집기는 메일을 열 때 메일 본문의 `<style>` 을 버린다 — head 에 있든(문서 꼴) body 맨 앞에 있든(조각 꼴). `getHTML` 의 head 에는
  편집기 제 서식(`<style data-destyle="deDefaultStyle">`) 하나만 든다. 그래서 아무것도 안 고치고 [임시저장]만 해도 저장한 본문에서
  메일의 `<style>` 이 사라진다. `setBodyValue` 로 다시 넣은 `<style>` 도 버린다. 편집기 문서의 head(또는 body)에 `<style>` 요소를 바로
  달면 `getHTML` · 저장에 실리고, 저장한 본문에 남는다. 다음에 편집으로 열면 또 버린다
- 저장된 본문 HTML 은 편집 화면 프레임에서 `fetch('<문서 주소>/Body?OpenField')` 로 같은 출처로 읽힌다 — 메일의 `<style>` 이 든 그대로고,
  편집기 제 서식은 `data-destyle` 이 달려 가려진다
- 본문의 `data:` 그림은 첫 저장에서 그 임시메일의 본문 조각(`…nsf/0/<unid>/Body/M1.N?OpenElement`)으로 바뀐다. 서명 그림의 조각 번호는
  그 뒤로 밀린다. 한 번 저장된 뒤에는 다시 저장해도 그림 · 서명 주소가 그대로다
- 웹메일에서 직접 쓴 임시메일은 저장된 본문에 메일 `<style>` 이 없다(편집기가 지은 그대로) — 그 메일에서는 잃을 서식이 없다
- 첨부 칸은 편집 화면 안 `iframe#KAM`(`fileupload/XAM_upload.html`, jQuery-fileupload 위의 XAM)이다. `am_handler.xam.g.getFileList()` 가
  `{name, size, status}` 를 내고 status 는 `complete`(저장된 것) · `ready`(올릴 것) · `remove`(뺄 것)다
- 첨부 더하기는 KAM 의 파일 입력(`input[name="%%File"]`, multiple)에 `DOM.setFileInputFiles` 로 파일을 주면 [추가]로 고른 것과 같다 —
  곧 `ready` 로 서고, [임시저장]이 올려 저장된 첨부가 된다. 물음은 안 뜬다
- 첨부 빼기는 웹메일의 [삭제/취소] 단추(`#btn_delete`)다 — KAM 의 `#file_list` 에서 그 줄에 `click-on` 을 달고 단추를 누르면 줄에 `remove` 가
  붙어 status 가 `remove` 가 되고, [임시저장]하면 그 첨부가 빠진다. 다시 누르면 「삭제 취소」다
- 첨부 칸은 칸에 이미 있는 이름의 파일을 안 받는다 — `remove` 로 고른 파일과 같은 이름이어도 「이미 첨부된 파일이 존재합니다. 중복된 파일 :
  <이름>」 을 띄운다. 같은 이름으로 갈려면 빼서 저장한 뒤 다시 붙인다
- 저장한 본문 HTML(`Body?OpenField`)에는 첨부마다 서버가 지은 표(`/icons/medoc.gif` · Type · Name)가 끝에 붙는다 — 편집기 판(`getHTML`)에는
  안 든다
- 편집 화면은 열려 있는 동안 웹메일이 1 분쯤마다 저절로 저장한다(`_autoSaveRequest` — `_form.isAutosaveCancel` 이 `'Y'` 면 멈춘다).
  다른 화면이 같은 임시메일을 저장해 저장 번호가 어긋난 화면은 그 자동저장마다 새 임시메일을 하나씩 갈라 세운다

### mail.py

#### mail.py · 웹메일 화면이 채우는 것

- 답장 · 전체답장 · 전달 화면은 받는 사람 · 제목 머리 · 서명 · 인용 · (전달이면) 원래 첨부를 채운다. 제가 보낸 메일에 답장하면 화면이
  그 메일의 받는 분들을 채운다
- 웹메일은 받는 사람 칸을 Notes 이름 · 부서 코드로 다시 연다 — 주소록에 없는 주소(사외)는 임시보관함 길로 못 싣는다
- 대용량 첨부는 웹메일 임시저장이 안 든다
- ``--html-file`` 로 실은 ``<style>`` 블록까지 웹메일이 그린다(회사에서 한 통으로 잰 것)

#### mail.py · 걸리는 시간

- 모든편지함 보기 한 장은 1 초 안쪽이라 ``FILL_SCAN`` 줄을 끝까지 받아도 몇 초다
- 한글 메일 한 통은 머리까지 1 KB 안팎이라, ``PEEK_CHARS`` 기본으로 답 하나(``OUT_BYTES``)에 20 통 안팎이 든다

### body_images.py

- 게시판은 그림에 `application/smnet` Content-Type 을 댄다 — 그래서 확장자를 파일 머리로 가른다
- 메일 본문에는 첨부 아이콘 · 글머리 점 같은 작은 그림이 흔하다(`ICON_EDGE` 아래는 안 남긴다)

### check_inbox.py

가짜 메일함(`FakeDomino`)은 사내 메일함에서 잰 주소 · 꼴을 흉내 낸다. 실물에서 꼴이 달라졌으면 가짜를 먼저 실물에 맞추고 손을 고친다.

- 여는 주소(`?OpenDocument` · `?EditDocument`)를 부르면 그 메일이 읽음이 되고, `ag_read_cancel` 은 안 읽음(`z^ico-nomail`)으로 되돌린다
- 쿠키가 없거나 세션이 끊긴 판이면 200 에 SSO 로 보내는 HTML 을 준다
- 받은편지함 보기는 받은편지함 메일만 낸다. 폴더 보기는 unid 로만 열리고(제목으로 열면 0줄), 받는 사람 목록 보기는 기본 정렬이 날짜순이 아니다
- 본문 주소에 501 을 내는 메일이 있다(`unserved`)
- 폴더 보기의 보낸 사람 열은 `<이름>-ENG-<영문>`(주소 없음)이고, 읽음 열은 HTML 조각(`class='mail_21'` 안 읽음 · `mail_22` 읽음)이다
- 모든편지함은 받은 · 폴더 · 보낸 메일을 들고 정렬 없이 날짜 내림차순이다. `ResortDescending=1` 이면 내림차순 두 덩이다
- 폴더 손은 늘 「OK」를 낸다(모르는 열쇠면 아무것도 안 옮긴다). 메일이 든 폴더를 지우면 그 메일을 휴지통으로 보내고, 메일 쪽을 지워도 이전메일함 짝이 나무에 남는다
- 규칙은 저장 폼을 그대로 들고 편집 화면(`new FormJS` 머리 · 입력 칸)으로 돌려준다
- 쓰기 화면은 손이 읽는 꼴(폼 `_Memo` · 숨은 칸 · 화면 정보의 unid)만 든다. 저장 POST 는 저장 칸이 `wSave` 면 임시보관함에 넣고 `wSend` 면 「그 자리에서 나갔다」로 따로 센다 — 답은 실물처럼 JSON 이 아닌 글(함수 칸)이다
- 업로드 DB 는 받은 파일 이름을 낸다

가짜가 실물에서 안 재 지어낸 값은 `check_inbox.py` 머리말 「여기서 못 재는 것」 이 든다.

## 회사에서 잴 것 — 아직 없는 손가락을 세우려면

잰 판이 서면 `scripts/mail.py` 의 표에 한 줄과 그 일을 하는 손 하나로 더한다(`DESIGN.md` 「mail.py · 받는 사람 찾기」).

- 배포그룹 하나로 보낸 메일이 받는 쪽에서 구성원 낱낱에게 가나 — 저장 꼴은 쟀다(「inbox.py · 임시저장 · 서명」), 보낸 판은 안 쟀다
- 팀즈문서 링크 공유 — 고름 창(`frmTeamsAttachFileManager`)이 무엇을 골라 본문 · 첨부 칸에 넣나(`insertTeamsAttachFileTable`)
- 표에 「회사에서 안 쟀다」 로 선 손가락(`mail.py` 의 `DRAFT_STARTS` · `DRAFT_CHANGES` 의 `unmeasured`) — [재사용] 화면에서 원래 보낸 메일의
  저장된 본문 `<style>` 을 받아(`STORED_STYLES`) 편집기 head 에 되달아 저장하면 서식이 남나 · [답장] · [전체답장] · [전달] · [재사용] 화면의
  첨부 칸에 파일을 줘 [임시저장]하면 붙나 · 편집 화면에서 저장된 첨부를 이름으로 골라 빼면(`DETACH`) [임시저장]에 빠지나. 한 번씩 돌려
  저장한 판이 바란 대로면 그 `unmeasured` 칸에서 뺀다
- 새 메일(`draft new`)을 저장한 뒤 손이 그 임시메일을 편집 화면으로 다시 연다(`show_on_screen`). 편집기는 열 때 메일의 `<style>` 을 버리고
  1 분쯤마다 저절로 저장한다(위 「draft_send.js」) — 서식 있는 새 메일이 그 창이 열린 채 자동저장되면 서식 없이 나가나, 그때 `draft` 가 낸
  판으로 `send-draft` 하면 종료 4 가 나나
- 답장 · 전달 화면을 여는 `process_doc` 에 손은 `forward_deny_type` 을 빈 값으로 준다(`draft_send.js` 의 `openReplyEditor`) — 「전달 금지」
  메일 · 대용량 첨부 메일이 그래도 전달 화면으로 열리나, 웹메일의 `copyEdit` 이 띄우는 알림과 같은 길로 막히나
- 답장 · 전달 화면을 여는 것(`process_doc`)이 안 읽은 원본을 읽음으로 바꾸나 — 바꾸면 `draft reply` · `all` · `forward` 가 읽음을 지키는
  선을 넘는다

## 본 후보와 탈락

- GitHub `SKILL.md` 코드 검색 「Lotus Notes」 · 「Domino」 — Domino 웹메일을 다루는 스킬은 없다. LotusScript 개발 · Notes 이전
  분석 스킬뿐이라 축이 다르다
- 안쪽 원본 — 메일함의 주소 · 꼴 · 읽음을 안 바꾸는 길은 아래 「inbox.py」, 웹메일 화면에서 저장 · 보내는 길은 「draft_send.js」 가
  든다(이 파일의 「회사에서 잰 꼴」). 스킬 본문은 그것을 옮겨 적지 않는다
