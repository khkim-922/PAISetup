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
  `check_board.py` 의 기대값)
- 게시판 나무 — `treeBBSSub` 를 뿌리(BBS85 · BBS_ALL_00001)부터 묶음마다 내려가면 8 번에 0.4 ~ 0.8 초 · 24 곳. `authMode=WRITE` 는 쓸 수 있는
  곳만(「일반사항」 이 빠졌다). 같은 이름이 둘 이상이다(「기타」 둘 · 「안전환경 > 안전환경」)
- 찾기 — `listArticle` 에 `bbsId`(뿌리면 모든 게시판 · 묶음이면 그 아래) · `srchKeyword` · `srchChkConditionList`(칸 이름을 `\x0c` 로
  잇는다) · `srchStartDate` · `srchEndDate` 를 주면 칸마다 다른 수가 왔다(「안전」 제목 513 · 내용 260 · 넷 693). 한 번(가운데 값)은 처음부터 넷 2.9 · 제목만 2.5 초, 6 개월 넷 0.45 · 제목만 0.35 초 — 기간이 가르고 칸은 거의 안 가른다.
  끝 날을 비우면 1 년만 본다. `listSearchArticle` 은 `bbsId` 를 안 먹었다 — 그래서 안 쓴다
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

## 회사에서 아직 안 잰 것

- 받아 둔 것에 없는 게시판 이름을 줬을 때 새로 받아 가리는 길
- 띄운 편집 창에서 사람이 [등록]을 누를 때 임시 글이 그대로 게시되는지 — 전사 게시판이라 시험으로 게시하지 않았다
- 말머리가 있는 게시판 · 익명(필명) 게시판 · 비공개 게시판에 쓰는 길
- 크게(수 MB) 든 그림을 data URI 로 넣을 때 게시판이 받는 한도 · 25 MB 첨부 한도 근처
- 게시판 탭이 없을 때 입구를 새 탭으로 여는 길(잰 판에는 게시판 탭이 늘 있었다)
- 묶음 · 이름이 겹치는 게시판의 「같은 이름이면 묶음째」 고름이 사람의 뜻과 맞는지
