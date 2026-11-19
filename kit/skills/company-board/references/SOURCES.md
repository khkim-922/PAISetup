# 출처 — 게시판 스킬

밖의 표준을 빌리지 않았다 — 사내 게시판(Posco Family Groupware 의 XClick U14)은 사내 앱이라 공개 스킬 · 명세가 없다. 화면의 자리와 꼴은
게시판이 내려 주는 화면(HTML · `common/js/xclick.js` · `urlsecure.js` · `bbs/js/articlelist.js` · `articlewrite.js`)에서 읽고, 회사 PC 에서
실물로 쟀다. 짓는 손이 Edge 에 붙는 줄은 형제 스킬 ep-login 의 `edge_cdp.js` 다 — company-mail 의 `draft_send.js`(임시보관함에 저장한 뒤
화면을 띄우는 손)와 함께 싣는다.

## 회사 PC 에서 잰 것 (2026-11-16)

- 들어가기 — 사내 세션(ep-login 의 세션 파일)만으로 SSO 넘김(`redirectSMSP.jsp?redir_url=…dispatcherSubmitSSO.jsp?menu=BBS_ALL`) →
  dispatcherSubmitSSO.jsp 에 POST(게시판 JSESSIONID 가 심긴다 · `plainTxt = "id=…"` 가 온다) → 그 글을 뒤섞어 cefDispatcherSSO.jsp 에
  `_xcsparam` 으로 POST 하면 선다. 리다이렉트는 없다. 세션 파일에 남은 낡은 게시판 쿠키만으로는 안 선다(로그인 창 한 줄)
  — 그 뒤는 `XClickController` 에 폼 꼴 POST 로 묻고, 끊긴 세션은 「openMiniLoginPop」 한 줄을 낸다
- 뒤섞기 — `urlsecure.js` 의 jQuery.encrypt(열쇠 `xclick6` · delta 123 · 세 번). 파이썬 판이 화면과 같은 글자를 냈다(표본 셋 ·
  설정 저장소 `_check/skills/company-board/check_board.py` 의 기대값)
- 게시판 나무 — `treeBBSSub` 를 뿌리(BBS85 · BBS_ALL_00001)부터 묶음마다 내려가면 8 번에 0.4 ~ 0.8 초 · 24 곳. `authMode=WRITE` 는 쓸 수 있는
  곳만(「일반사항」 이 빠졌다). 같은 이름이 둘 이상이다(「기타」 둘 · 「안전환경 > 안전환경」)
- 찾기 — `listArticle` 에 `bbsId`(뿌리면 모든 게시판 · 묶음이면 그 아래) · `srchKeyword` · `srchChkConditionList`(칸 이름을 `\x0c` 로
  잇는다) · `srchStartDate` · `srchEndDate` 를 주면 칸마다 다른 수가 왔다(「안전」 제목 513 · 내용 260 · 넷 693). 한 번(가운데 값)은 처음부터 넷 2.9 · 제목만 2.5 초, 6 개월 넷 0.45 · 제목만 0.35 초 — 기간이 가르고 칸은 거의 안 가른다.
  끝 날을 비우면 1 년만 본다. 상세검색(`listSearchArticle`)은 제외할 단어를 줄 때만 쓴다 — 아래 2026-11-19 줄
- 고정 공지 — 쪽마다 맨 위에 서고 낱말과 상관없이 온다. `총 N 건` 에 안 든다
- 목록 줄 — 칸의 차례가 목록 꼴(게시판 · 모든 게시판)마다 다르다. 고름 칸의 JSON 이 글 id · 게시판 id · 제목을 든다
- 글 읽기 — `viewArticle` 은 `transaction_yn=Y` 면 조회수가 하나 오르고 `N` 이면 안 올랐다(같은 글로 견줌). 게시판 id 없이는 본문 칸이 없다
- 첨부 — `common/fileattach/download.jsp?refId=<글 id>` 의 `_fileArr.push` 가 파일 id · 이름 · 크기를 든다. `DownController?fileId=` 로
  받는다. 문서함 첨부는 메일과 같은 쪽지(`<!--@!ECM!@ … <objectId>doc<16 hex>` )였다
- 글쓰기 — 화면의 글쓰기 창(`writeArticle` → windowOpenMain.jsp)에서 `jQuery.setDivisionSelect` 로 게시판 · 편집기(DEXT5)의 `setContent`
  로 본문 · 첨부 틀의 숨은 파일 칸으로 첨부를 넣고 `articleSave('TEMP')` 하면 임시보관함에 섰다. 「저장 하시겠습니까?」 를 묻는다
  - 게시판을 고르면 본문 틀을 다시 싣는다 — 본문을 먼저 넣으면 빈 본문(`<p>&nbsp;</p>`)으로 저장됐다. 게시판 → 4 초 → 본문 차례로 섰다
  - 굵게 · 색 · 표 · data URI 그림 · 평문의 꺾쇠 이스케이프가 저장된 본문에 그대로 들었다. 첨부 하나가 글에 묶였다
  - 묶음 게시판(일반사항)에 쓰면 「폴더형태의 게시판에는 게시물을 등록할 수 없습니다.」 로 막았다
  - 저장 뒤 화면이 창을 닫으려 한다. 닫히는 창에 붙으면 손이 멈췄다 — 닫힘을 기다린 뒤 편집 창을 새로 연다
  - 임시 글의 편집 창(`writeGbn=EDIT · menuGbn=TEMP · articleId`)은 제목 · 게시판 · 본문 · 첨부 · 상태(IMSISAVE)를 그대로 들었다
- 시험 글 — 업무정보 > 기타(BBS455)에 「[테스트] 게시 스킬 …」 임시 글 열두 개를 지었다가 임시보관함에서 다 지웠다(`delArticleListAdmin`)
- ep-login 의 Edge 는 다른 세션(메일 스킬 손)과 한 벌이다 — 그쪽이 잡은 동안 그 Edge 의 탭들이 디버깅 명령에 답을 안 했고(새 탭은 답했다),
  입구를 새 탭으로 열어 선 게시판 탭으로는 저장이 섰다. 새로 로그인하면 그쪽 세션이 끊기니 짓는 손은 로그인하지 않는다
- 첨부 둘을 한 번에 넣으면 틀이 하나씩 줄에 세웠다 — 둘 다 선 뒤에 저장해 글에 둘이 묶였다. 앞뒤 빈칸이 든 제목은 걷혀 저장됐다
- 들어가기(SSO 세 걸음)는 가운데 0.16 초 — 찾기 한 번보다 작아 게시판 쿠키를 남겨 건너뛰지 않는다
- 받아 둔 나무 — 첫 `list` 가 나무를 한 번 받아 파일로 남기고, 둘째 판은 안 받았다(2.6 → 2.0 초)
- 고정 공지 — 찾기 · 목록 첫 쪽 24 줄 가운데 4 건(제목 322 바이트). 낱말이 제목에 든 고정 공지는 찾은 줄에 같은 id 로 안 들었다 —
  그래서 `pinned_notices` 가 id · 게시판을 싣는다
- 목록 줄 날짜 — 새 글 · 2024 년 끝까지의 찾기 모두 `YYYY-MM-DD HH:MM` 꼴로 해가 왔다
- 본문 그림 — 식단정보 새 글 20 건 가운데 17 건이 그림뿐(표 틀 안에 그림), 업무공지 20 건 가운데 10 건이 그림뿐. 그림 주소는 거의
  `DownController.do?fileId=` 상대 주소고, 사내 세션으로 받으면 PNG 바이트가 왔다(Content-Type 은 `application/smnet`)
- `read --images` — 식단 글의 그림(1499×1069 PNG)을 받아 그림 파일로 열었고, 그 순간 그림 문이 치수를 쟀다
- 본문 그림 주소의 꼴 — 게시판 15 곳의 글 45 건(38 건에 그림 · 125 장): 97 장이 게시판 호스트 · 포트의 `DownController.do?fileId=`
  하나(상대 84 · 절대 13)고, 28 장은 남의 호스트(사외 이미지 서버 · 지도 타일 · 지도 표지)였다. 다른 꼴은 없었다. 그래서 `App.image` 는
  그 꼴만 묻고 나머지는 「화면에서 본다」로 낸다. 좁힌 뒤에도 업무 글의 그림 둘(574×822 · 578×823 PNG)이 받아졌다
- 글쓰기 창은 화면의 `writeArticle` 로 열면 목록 칸의 카테고리를 읽어, 그 칸이 빈 판에 「카테고리가 존재하지 않는다」 경고에 창이 멈췄다 —
  그래서 카테고리(`BBS_ALL`) · 게시판 id 를 직접 줘 연다. 그 길로 첨부 → 본문 차례의 임시저장에 본문 글 · 그림 · 첨부가 다 들었다
- 문서함 쪽지 15 개 — 머리 열쇠 · 링크 열쇠가 다 있었고 3 개는 둘이 달랐다. 갈리는 쪽지의 링크 쪽 열쇠로 company-ecm `read` 가 문서를
  열었다 — 그래서 `attachment` 는 메일과 같은 가름(company-mail `inbox.ecm_note_key`)을 부른다

## 회사 PC 에서 잰 것 (2026-11-19 · 화면에 있는데 손가락이 없던 것)

- 찾은 글이 없는 목록 — 「총 N 건」 줄이 안 서고 고정 공지만 온다. 그 판에 손이 고정 공지 수를 찾은 수로 냈다(업무공지 · 제목 「안전」 · 10 월부터:
  찾은 글 0, 손의 total 3). 화면 상세검색은 같은 물음에 1 건을 냈는데, 그 1 건은 낱말이 든 고정 공지였다 — 목록 찾기는 고정 공지를 낱말과
  따로 세워 찾은 줄에 안 넣는다(`pinned_notices`)
- 상세검색(`listSearchArticle`) — `srchBBSId` · `bbsId` 에 게시판, `srchTargetCurMap=N` 이 화면의 「하위포함」이다(Y 면 묶음에서 0 건 — 화면이
  뜻을 거꾸로 쓴다). 그 꼴이면 목록 찾기와 같은 줄을 내고, 낱말이 든 고정 공지 하나가 더 든다(뿌리 · 제목 「안전」 · 6 개월: 30 ↔ 29).
  제외할 단어 `srchExceptWord` 는 이 명령에서만 걸린다(경조사 · 「결혼」 2025 년 162 → 「자녀」 빼고 140). 목록 찾기(`listArticle`)는 그 칸을
  버린다. 줄 날짜는 해가 없는 `MM-DD HH:MM` 이고, 고름 칸 JSON 이 제목의 큰따옴표를 안 감싸 와 그 줄은 JSON 으로 안 풀린다
- 부서명 칸 — `//condition-searchCondition-deptname` 이 목록 찾기에서 걸린다(「지속가능」 5 건 · 없는 말 0 건)
- 거르기 — `notifyYn=true` 는 고정 공지를 뺀다. `unreadArticleYn=true` 는 안 읽은 글만(11 월 56 건). `myArticleYn=true` 는 내 글만이다 — 양성
  대조: 이 계정이 쓴 글 2 건(경조사 > 조사, 「내글반응」 화면과 같은 id)이 그대로 서고, 그 위에 고정 공지 셋이 늘 같이 선다(그래서 첫 조사가 남의
  글로 읽었다)
- 의견 — 글 화면(`viewArticle` · `transaction_yn=N`)의 `_commentScope<글 id>` 안에 다 온다(43 건 한 번에 · 쪽 없음). 줄마다 `c_name`(이름 ·
  직함 / 부서) · `c_date`(초까지) · `c_text` · 말머리 그림(title 기타 · 질문 · 의견 · 답변) · 답글이면 `icon_reply`. 목록 줄 제목 끝의
  `<font style='color:#f26522'>[N]</font>` 가 의견 수다
- 열람내역 — `listArticleReadUser`(`paging_listcnt` 로 한 쪽 100 줄) · 줄마다 순서 · 읽은 시각 · 이름 · 부서 · 직함 · 사번. 쓴 사람이 아니어도
  열린다. 안 읽은 글(식단정보)의 열람내역을 연 앞 · 뒤로 열람자 수(25 → 25) · 그 글의 안 읽음(그대로)이 안 바뀌었다
- 게시판 옵션(`getBBSOptionAjax`) — 읽을 수 있는 17 곳 모두 `readHistoryYn=Y` · `commentYn=Y` · `recommYn=N` · `pointYn=N` · `voteYn=N` ·
  `headerYn=N`. `termModifyYn=N` 은 안전환경 > 안전환경 · 교육 · 지속가능경영 > 자료 · 실천활동 넷이다. 추천 · 점수 내역은 쓸 곳이 없어 안 지었다
- 글 링크 — 화면 「URL복사」 의 식 `ssoURL + encodeURIComponent(articleURL + "menu=" + 카테고리 + "&bbsid=" + … + "&articleid=" + …)` 의 두 값
  (`viewSystemValue · xclick-cef · //articleURL/…`)이 `xclick.LINK_SSO` · `LINK_ARTICLE` 과 같았다
- 편집 · 재활용 창의 폼 — GET 한 번에 숨은 `content` 칸이 저장된 본문 HTML 전문(`<html>…<body id="dext_body">…`)을, `endDate` · `notifyDate` 가
  게시기한을 든다. 재활용(`articleCopyYn=Y` · `orgArticleId` · 빈 `articleId`)은 원글 제목 · 본문 · 게시기한을 들고 첨부는 안 든다
- 임시글 편집 창에는 게시판 고름이 없다 — 「게시판 위치」 칸이 이름 글자뿐이고 `bbsSelect` 칸이 없어 고르기가 안 섰다(시험 임시글)
- 시험 임시글(업무정보 > 기타 · 「[테스트] 고치기 2」)의 저장 네 판 — 글 일부(`--swap`) + 게시기한(`--end 2027-05-31`) 한 판 · 첨부 빼기
  (`--drop att2.txt`) 한 판 · 되돌리기(`--swap` · `--end 2031-11-17` · `--file att2.txt`) 한 판이 다 같은 글을 고쳤고(갈라지지 않음) 손이
  「섰다」로 가렸다. 저장마다 글 화면의 게시 시각(분)이 바뀌고 임시보관함 줄의 날짜(하루 단위)는 안 바뀌었다 — 그래서 저장을 가리는 판이
  그 글의 모습(제목 · 게시 시각 · 게시기한 · 본문 글자 · 첨부 이름)을 본다. 게시판 옮기기는 고름이 없어 저장 전에 멈췄다. 끝에 그 글은 제목 ·
  본문 · 게시기한 · 첨부 두 이름이 처음과 같고, 게시 시각과 다시 붙인 att2.txt 의 파일 id 만 바뀌었다

## 화면에 있는데 손가락을 안 지은 것 — 자리와 까닭 (2026-11-19 · 잰 것과 코드에서만 읽은 것을 가른다)

화면 코드는 `articlelist.js · articleview.js · articlewrite.js · bbsRibbonCtrl.js · userContents.jsp(리본) · html5uploader · DEXT5 index.jsp` 에서
읽었다. 「잼」 은 회사 PC 에서 GET 으로 답을 본 것, 「코드」 는 화면 코드만 읽은 것이다.

- 찾기의 「3 대 1」 — 같은 낱말 · 칸 · 게시판 · 기간에 목록 찾기 3 · 상세검색 1 로 갈린 것은 범위 차이가 아니다. 3 은 낱말과 상관없이 오는 고정
  공지 셋(찾은 글 0 · 「총」 줄 없음)이고, 1 은 그 가운데 낱말이 든 고정 공지 하나를 상세검색이 찾은 줄로 낸 것이다(잼). 위 2026-11-19 줄의 고침
- 내 글 목록(`listArticleMy` · `nextpage=/bbs/articleMyList.jsp` · `menuGbn=LISTMY` · 화면 「내글반응」) — 내 글 줄을 냈다(잼). 줄 꼴이 목록과 달라
  (칸마다 안쪽 표 · 의견 수 · 의견 창 단추) 따로 풀어야 한다. `myArticleYn=true` 거르기가 같은 글을 내 안 지었다
- 쓰기 창의 게시판 옮기기 — 편집 · 재활용 창에 고름이 없다(잼 · 위 줄). 새 글 창에서 고르면 `setBBSConf` → `getBBSOptionAjax` 뒤
  `setBBSOption` 끝에서 편집기 틀을 다시 싣고(`editor1 … location.reload()` · `setBbsTemplate()` 는 주석), 다시 선 편집기는 `getInitContent` 로 폼의
  숨은 `content` 를 읽은 뒤 `setEditorTemplate` 이 새 글(`articleId` 빈 값)일 때만 게시판 틀(`CefBbsFacade.getBbsTempalte`)을 싣는다(코드). 틀이
  있는 게시판은 `viewSystemValue · xclick-cef · //cef/bbs/templateBbsId` 에 든 몇 곳뿐이다(경사 · 조사가 든다 · 잼)
- 게시기한의 기본값 — `getEndDateAjax(notifyDate, dispPeriod=5Y|1Y|ZZ)` 가 5 년 · 1 년 · 2999-12-31 을 낸다(잼). 게시판을 고를 때 화면이 이 값으로
  `endDate` 를 채운다(코드)
- 말머리 — 폼 `headerCd`, 찾기 `srchHrdCd`, 값 목록 `AjaxController?facade=BBSFacade&command=listBBSHearderAjax&bbsId=`. 읽을 수 있는 17 곳 모두
  `headerYn=N` 이라 칸이 숨고 목록이 비었다(잼) — 쓸 곳이 없어 안 지었다
- 익명 · 필명 · 비밀번호 · 알림 · 캡처 허용 — 폼 `anonymousYn` · `nnuy` · `passWd`(`passwdYn=Y` 일 때) · `replyAlarmYn` · `commentAlarmYn` · `alarmType` ·
  `captureYn`(DRM 게시판 목록 `xclick-cef //bbs/drmBbs` 에 든 곳만). 쓸 수 있는 곳 모두 그 칸이 안 뜨는 값이었다(잼 · 옵션) — 안 지었다
- 공개 범위 · 예약 게시 — 폼 `publicYn` · `dtAuthListDataArr`(틀 `DtAuthCatalogFacade.viewDtAuthCatalog`), 예약은 `bookYn · timeZone · date · hour · min` 과
  검사 `CommonFacade.chkBookDateAjax`, 저장은 `writeGbn=TEMP`(코드). 비공개형(`bbsType=PRI`) 게시판에서만 권한 칸이 뜬다. 열람 권한 · 예약은
  「안 하는 것」 이라 안 지었다
- 답글(응답) — 쓰기 창 `writeGbn=RE`, 저장 때 `copyFileIdLists` 로 원글 첨부를 옮긴다(코드). 쓸 수 있는 곳은 `replyYn=Y` 다. 출발로 더할지는 정하지
  않았다 — 지금은 「아직 없는 손가락」
- 의견 쓰기 · 지우기 — `BBSCommentFacade.addComment` · `delComment`(코드). 남에게 보이는 글이라 안 한다
- 추천 · 찬반 · 점수 — `addRecommAjax` · `addVoteAjax` · `savePoint`, 내역 `listArticleRecomm`(`/bbs/pop/bbsRecommListPop.jsp` · 빈 글에서 「조회된 데이터가
  없습니다」 · 잼) · `listArticlePoint`(코드). 17 곳 모두 `recommYn` · `pointYn` · `voteYn` 이 N 이라 쓸 곳이 없다
- 읽음 표시 바꾸기 — `editMultiArticleReadYnAjax`(화면 리본 `editReadYn`)(코드). 내 읽음 기록을 바꿔 안 한다 — 읽기 손이 읽음을 안 남기는 까닭과 같다
- 즐겨찾기 · 구독 — 더하기 `AjaxController?facade=BBSArticleFacade&command=addFavoriteAjax`(폼 직렬화 GET) · 빼기 `cancelFavorite` · 목록 거르기
  `favorite_yn=Y`(0 건만 봤다 · 잼) · 구독 `BBSFacade.subscribeAjax`(코드). 내 계정 설정이 바뀌어 안 지었다
- PC 저장(글 + 첨부 묶음) — `pcSaveArticle` · `nextpage=/bbs/bbsBackupFileDownload.jsp` · `backupTarget=ONE` · `backupType=ZIP`(`ZipDownController`)(코드).
  `transaction_yn=Y` 로 폼을 보내 조회수가 오를 수 있어 안 쟀다. `read` + `attachment --save` 가 같은 것을 낸다
- 메일전달 — 글 화면 · 목록 「메일전달」 → `CefBbsMailBroker.writeMail`(코드). 본문 · 첨부 링크(`contentFileId` · `refId`)를 메일 쓰기 창에 싣는다.
  메일은 스킬 company-mail 몫이라 안 지었다
- 할 일 · 인쇄 · 목록 설정 — `addTodoList`(일정 앱의 할 일) · `openPrintArticlePop`(`articlePrintPop.jsp`) · `editUserConfig`(타임존 · 목록 꼴 · 미리보기)
  (코드). 다른 앱 몫 · 사람이 보는 창 · 화면 취향이라 안 지었다
- 관리 — `BBSADMIN` · `ARTICLEADMIN` · `listArticleAdmin` · `delArticleListAdmin`. 이 계정은 17 곳 모두 관리자가 아니다(잼). 시험 글을 지운 길(위
  2026-11-16 줄)은 임시보관함의 내 글에만 섰다
- 목록 꼴 — 게시판 옵션 `dfltBbsListType` 과 목록 폼의 `bbsListType`(화면 「리스트형태」 · 바꾸면 `chgListType` 이 다시 묻는다)이 꼴을 든다(코드).
  `getMovePage` 는 메뉴(찾기 · 임시 · 내 글)로만 `nextpage` 를 가르고 꼴로는 안 가른다. 읽은 곳은 다 일반형으로 왔고 `bbsListType=ALBUM_LIST` 를
  줘도 줄이 같았다(잼). 앨범 · 블로그 · 사용자정의 꼴의 줄은 안 봤다
- 찾기의 정렬 · 쪽 크기 — `sort_column` · `sort_cond` · `paging_listcnt`. `sort_column=title` 은 순서가 안 바뀐 것으로 보였다(확정 못 함 · 잼)

## 회사에서 아직 안 잰 것

- 새 글(`save --start new`)의 한 판 — 위에서 잰 뒤 짓는 손 안의 세 걸음이 바뀌었다(저장 앞 임시보관함 목록을 게시판 탭에서 읽기 · 첨부 뒤에
  제목 넣기 · 첨부 수를 틀에 있던 수 위로 늘어난 만큼으로 세기). 시험 글 하나를 첨부와 함께 임시저장 · 읽기 · 지우기로 한 판 다시 본다
- 같은 편집기(DEXT5)를 메일 쪽에서 잰 사실이 게시판 편집 창에서도 그런가(company-mail `references/SOURCES.md` 의 편집기 · 첨부 칸 줄) —
  - 서식(`<style>`) — 메일 편집기는 글을 열 때 본문의 `<style>` 을 버려 아무것도 안 고치고 저장해도 서식이 빠졌다. 게시판의 임시글 편집
    창을 열고 [임시저장]하면 `--html-file` 로 넣은 `<style>` 이 남나, 새 글의 `setContent` 는 `<style>` 을 지키나
  - 본문으로 HTML 문서 통째(`<html><head>…<body>`)를 `setContent` 에 주면 무엇이 남나 — 지금은 받은 파일을 그대로 넣는다
  - 같은 이름 첨부 — 메일 첨부 칸은 칸에 이미 있는 이름의 파일을 「이미 첨부된 파일이 존재합니다」 로 안 받았다. 게시판 첨부 틀
    (html5uploader)이 임시글에 이미 있는 이름을 받나 · 막나 · 어떤 알림을 띄우나
  - 첨부를 넣는 동안 알림 · 물음 창이 뜨나 — 지금 짓는 손은 [임시저장] 뒤의 물음만 다룬다
  - 열린 편집 창의 자동 저장 — 메일 편집 화면은 1 분쯤마다 저절로 저장했고, 저장 번호가 어긋난 화면은 그때마다 새 임시메일을 갈랐다.
    게시판 편집 창도 저절로 저장하나 · 쓰는 사람이 연 창에서 손이 고친 뒤 그 창이 새 임시글을 가르나
- 찾기의 조건 겹치기 — `listArticle` 이 칸마다 다른 낱말(작성자 「홍길동」 + 제목 「안전」)을 한 번에 받나. 지금 `search` 는 낱말 하나를
  고른 칸들에 걸어(칸끼리는 「또는」) 「홍길동이 쓴 안전 공지」 는 한 부름에 안 선다
- 받아 둔 것에 없는 게시판 이름을 줬을 때 새로 받아 가리는 길
- 띄운 편집 창에서 사람이 [등록]을 누를 때 임시 글이 그대로 게시되는지 — 전사 게시판이라 시험으로 게시하지 않았다
- 말머리가 있는 게시판 · 익명(필명) 게시판 · 비공개 게시판에 쓰는 길
- 크게(수 MB) 든 그림을 data URI 로 넣을 때 게시판이 받는 한도 · 25 MB 첨부 한도 근처
- 게시판 탭이 없을 때 입구를 새 탭으로 여는 길(잰 판에는 게시판 탭이 늘 있었다)
- 묶음 · 이름이 겹치는 게시판의 「같은 이름이면 묶음째」 고름이 사람의 뜻과 맞는지
- 임시글 편집 창의 [임시저장] — 어떤 물음 · 알림이 뜨나, 저장 뒤 창을 닫으려 하나
- 쓰는 사람이 열어 둔 편집 창에서 손이 고쳐 저장할 때 그 창이 닫히나 · 남나 · 같은 글의 창 둘에서 차례로 저장하면 어떻게 되나
- 편집 창에서 첨부를 더할 때 본문에 큰 data URI 그림이 든 임시글에서 창의 DOM 을 통째로 받는 첨부 넣기가 Edge 의 답 시한 안에 서나
- 재활용(`save --start copy`)의 저장 — 새 임시글이 하나 서나 · 원글이 그대로인가 · 본문의 상대 주소 그림(`DownController.do?fileId=`)이 새 글에서
  보이나. 사용자가 실물 서버에서 새 글을 짓지 말라 해 GET(폼)까지만 쟀다
- 글 일부(`--swap`)를 서식 · 표 · 그림이 든 본문에 — 잰 판은 평문 한 줄이었다
- 의견이 수백 건인 글 — 43 건까지 한 번에 왔다. 열람내역 쪽 넘김(`--page 2`)
- 상세검색의 한 쪽 줄 수 — 목록 찾기와 같은 20 줄로 물었다. 고정 공지 셋이 늘 서는 거르기(`--mine`)의 둘째 쪽
