# 출처 — 사규 스킬

밖의 표준을 빌리지 않았다 — 사규관리 앱은 사내 앱이라 공개 스킬 · 명세가 없다. 앱의 자리와 꼴은 앱이 내려 주는 화면(HTML ·
`resources/js/common.js`)에서 읽고, 회사 PC 에서 실물로 쟀다.

## 회사 PC 에서 잰 것 (2026-11-12)

- 사내 세션(ep-login 의 세션 파일 · .posco.net 쿠키)만으로 SSO 넘김(`redirectSMSP.jsp`) → 앱 뿌리에 POST → `test_login.do?aes=` →
  `main.do` 로 들어간다. 앱 세션 쿠키는 앱 호스트(poscofuturem.com)에 살아 세션 파일에는 안 든다
- 전체 목록(`getProcessListAll.do` · 맨 위 범주마다)은 범주 자리 줄을 섞어 낸다 — 제 이름이 제 층의 범주 이름과 같은 줄이다. 큰
  범주는 한 번에 30 초 남짓, 여섯 범주를 다 받는 데 80 초쯤 걸렸고 문서는 3 천 건 남짓이었다
- 통합 검색(`searchListCnt.do`)은 `searchText2` 가 비면 본문 검색(`content`)이 늘 0 건이다 — 화면처럼 같은 검색어를 두 칸에 다 준다.
  흔한 낱말의 본문 검색은 17 초쯤 걸렸다
- 문서를 화면으로 열면 화면이 `insertSopConnHis.do`(열람 기록)를 따로 부른다. `selectProcessInfo.do` 만 부르면 그 기록 주소는 안 불린다
- 합친 칸(rowspan · colspan)이 든 실물 표(여비관리기준의 국내 · 국외 여비 기준표)를 `read` 로 읽으면 한 행이 한 줄이고, 합친 칸은
  자리마다 채워져 한 표 안에서 줄마다 칸 수가 같았다
- `last_change`(`mainContent`) · 바뀐 자리의 `why`(`note`) · `before` · `after` 는 HTML 이 아니라 글자로 온다
- 윈도를 로그오프한 뒤 첫 `read` 는 종료 3(「다음: 스킬 ep-login」)을 냈고, ep-login 이 Edge 를 다시 띄워 세션을 세운 뒤 같은 명령이
  섰다
- 본문 1 만 ~ 2 만 자 문서의 `read` 는 한 판이 23 KB 남짓으로 끊겨 두세 판에 다 읽혔다(문서 하나 합 28 ~ 52 KB)
- 제목 줄은 꼴로 가릴 수 없다 — 긴 문서(본문 4 천 자 넘음) 42 건의 줄을 조문 꼴(「제 N 조(…)」)과 번호 꼴(「1. 목적」)로 가렸을 때
  실제 제목과 맞은 것은 23 건이다. 11 건은 쪽번호(`1 / 49`) · 쪽마다 되풀이되는 머리 · 표와 그림 안의 번호가 제목으로 잡혔고(기초소재
  작업 · 시험표준 일곱 건 가운데 여섯), 8 건은 제목이 하나도 안 잡혔다(표 꼴 업무지침 · `1.목적` 처럼 점 뒤에 빈칸이 없는 문서).
  그래서 `read` 는 목차를 안 낸다
- `read --grep` 은 실물 긴 문서에서 낱말이 든 대목을 자리와 함께 낸다(한 문서에서 36 곳)
- 경로 없는 `tree` 의 답은 5 KB 남짓이다(문서 3174 건) — `OUT_BYTES` 에 든다

## 회사 PC 에서 잰 것 — 본문 그림 (2026-11-16)

- 범주(맨 위 둘째 칸까지) 37 곳에서 고른 30 건 가운데 18 건의 본문에 그림이 들었고, 그림은 196 장이었다 — 작업표준 · 지침 · 기술기준 ·
  규정 · 매뉴얼에 고루 섰다
- 그림 주소는 두 꼴뿐이었다 — 155 장은 앱 호스트의 `/uploads/output/<달>/<열쇠>/media/image<N>.(png|jpeg|jpg)`(물음표 없음), 41 장은
  본문에 박힌 `data:image/jpeg`. 남의 호스트 · 상대 주소는 없었다
- 앱 호스트의 그림은 사내 세션 · 앱 세션 없이도 200 으로 받아진다. Content-Type 은 `application/octet-stream` 이라 꼴은 바이트 머리로 가린다
- 치수는 300 ~ 860 px 남짓(한 문서 일곱 장) — 줄이기 눈금 안쪽이다. `read --images` 로 받은 그림을 그림 파일로 열어 공정 사진 흐름도를 읽었다

## 회사 PC 에서 잰 것 — 등급 문서 (2026-11-19)

- 앱의 JSON 길(`selectProcessInfo.do`)은 쓰는 사람의 화면이 막는 등급 문서의 본문도 통째로 내준다 — 사외비A · 기밀 · 사외비A/비공개
  문서 한 건씩에서 본문 HTML 이 왔고, 같은 문서의 화면 창(`/main/goProcessInfoPop.do?processIdx=<n>`)은 「권한이 없습니다. 권한신청
  하시겠습니까?」 스크립트 하나(132 바이트)로 막았다. 그래서 `read` 는 등급이 「일반」이 아니거나 등급을 못 읽은 문서마다 그 화면 창을
  먼저 GET 해, 막으면 본문 · 바뀐 자리 · 그림을 하나도 안 내고 종료 2(`error: denied`)로 [권한신청]을 권한다
- 화면이 여는 문서의 창은 32 KB 남짓의 화면이고 그 안에 `var processIdx = "<n>"` 이 든다 — 막는 말도 이 꼴도 없으면 손은 가리지 못한
  것으로 보고 멈춘다(여는 쪽으로 안 넘긴다)
- 잰 판 — 읽기 권한 목록에 든 사외비A/비공개 · 사외비B 문서 하나씩은 창이 열렸고 `read` 가 본문을 냈다. 목록에 안 든 사외비A · 기밀 ·
  사외비A/비공개 문서 하나씩은 `read` 가 denied 로 멈췄다(본문은 찍지도 남기지도 않았다). 「일반」 문서는 창에 안 묻는다
- 창을 GET 해도 「최근 사용 표준」 은 안 바뀌었다 — 세 문서의 창을 받기 전 · 뒤 그 목록은 22 건 그대로였고 셋 다 없었다. 창의
  스크립트를 안 돌리니 화면이 여는 순간 부르는 열람 기록(`insertSopConnHis.do`)은 안 간다. 서버가 창 GET 을 따로 적는지는 관리자
  화면(「표준 조회이력」)을 이 계정이 못 봐 못 쟀다
- 폐지된 문서(`deleteYn=Y` · 판이 「폐지」)도 창이 연다 — 폐지 문서 하나의 창이 그 문서 번호를 든 화면으로 왔다

## 회사 PC 에서 잰 것 — 관련 표준 · 폐지 문서 (2026-11-19)

- `selectProcessInfo.do` 의 답 맨 위 칸은 searchTobe · reviewerList · ProcessInfo · searchRelationSite · searchProcessFileList · processIdx
  뿐이다 — 관련 표준은 거기 없고 화면의 「관련표준」 표가 따로 부르는 `selectRelationProcessList.do`(processIdx)의 `relationProcessList`
  다(줄마다 processIdx · processName · menuName · reDeptnm · hname · regDate · stateNm). 관련 표준이 든 문서 셋에서 줄의 processIdx 가
  받아 둔 목록의 같은 이름 문서를 가리켰다. 한 문서는 제 자신을 관련 표준으로 들었다 — 앱의 데이터 그대로 낸다
- 첨부 칸은 `searchProcessFileList[]` 의 orgFileName · newFileName · filePath · fileIdx 다
- 전체 목록(`getProcessListAll.do`)에는 폐지(삭제)된 문서가 안 든다. 폐지 문서는 화면 「최근 변경된 표준」 의 `getChangedProcessList.do`
  (fromDate · toDate 를 YYYY.MM.DD 로 · state 「삭제」 · searchText)가 낸다 — 기간을 2000.01.01 부터 주면 1043 건(2016.07.01 ~ 2026.11.09)이
  18 초에 왔고, 기간을 비우면 JSON 이 아닌 답이 온다. 줄의 경로는 type1 · type2 · type3(구분 이름)이고, 날짜는 그 문서의 시행일(폐지
  판의 시행일)이다 — 폐지 문서를 읽으면 판이 「폐지」, `deleteYn=Y` 다
- 그래서 목록을 받을 때 폐지 문서를 함께 받는다 — 여섯 범주와 폐지 문서를 다 받는 `refresh` 가 98 초 걸렸다(공개 3183 · 폐지 1043).
  `recent --abolished --days 31` 이 화면의 같은 달 「삭제된 표준」 84 건과 같은 수를 냈다

## 회사 PC 에서 잰 것 — 화면에 있는데 손가락이 없던 것 (2026-11-19 · #292 B)

화면이 부르는 주소와 칸은 앱이 내려 준 화면 코드(문서 창 · 개정이력 창 · 목록 화면)에서 읽고 한 번씩 불러 쟀다. 다 읽는 요청이다.

- 개정이력 — `selectRevisionHistoryInfo.do`(processIdx)의 `revisionHistoryInfo[]`(version · enforcementDate · mainContent | revisedContent ·
  hname · reHname · workIdx · processHisIdx), 새 판부터. 한 문서에서 5 판이 왔고 맨 위가 지금 판이다. 옮겨 온 첫 판은 workIdx 가 0 이고
  mainContent 가 비어 revisedContent 에 글이 든다
- 지난 판 본문 — `selectProcessHisInfo.do`(processHisIdx)의 `ProcessHisInfo[0].content`(HTML). 지난 판 둘에서 본문이 지금 판과 같은 꼴로
  풀렸다(3 천 · 7 만 자)
- 판마다의 전후대비표 — `/myProcessList/searchTobeList.do`(workIdx)의 `searchTobeList[]`(tobeGubunNm · oldContent · toContent · note) — 글자로
  온다. 지금 판의 workIdx 로 부르면 `selectProcessInfo` 의 `searchTobe` 와 같은 수가 왔다. workIdx 0 인 판은 부르지 않는다
- 결재 경과 — `selectRevisionHistoryDetailInfo.do`(workIdx)의 `revisionHistoryDetailInfo[]`(apRegDate · codeName · reHname · apHname · opinion).
  한 개정에서 검토요청 → 승인요청 → 검토승인 → 검토완료 → 승인완료 다섯 걸음이 왔다. 앞의 두 판은 0 걸음으로 왔다
- 표준번호 · 인증서 유효기간 — 전체 목록 줄과 `selectProcessInfo` 에 `txtIdx` · `fromDate` · `toDate` 가 이미 온다. 공개 3185 건 가운데 2785 건이
  번호를 들었고, `toDate` 는 인증 범주에만(16 건 가운데 14 건) 든다. 화면은 인증 범주(menuIdx 6)에서 시행일 자리에 「유효기간 시작 ~ 끝」 을
  적는다. 받아 둔 목록의 번호 셋을 `find <번호>` 로 찾으니 셋 다 그 문서 하나가 걸렸다
- 통합 검색의 범주 · 첨부 이름 — 같은 `searchListCnt.do` 에 `menuId`(맨 위 범주의 menuIdx)와 `searchConditionPram` 의 `file_name`.
  「지침」 을 전사공통으로 좁히니 113 건, 「pdf」 를 첨부 이름으로 찾으니 111 건 · 2 초 남짓
- 사람 창 — `/cmmn/ajax/getEmpInfo.do`(empcd)의 `empInfo`(hname · deptcdDisp · jikwicdDisp · jikckcdDisp · responsibility · officePhone ·
  handpon · email). 퇴사자 · 없는 사번은 `empInfo` 가 빈다. 담당 · 검토 · 승인의 사번은 `selectProcessInfo` 의 empcd · reviewerCd · approvalCd
  다. 회사 메일의 `who` 는 이름 · 부서 · 직급 · 직책 · 근무지 · 담당 업무 · 주소를 내고 전화는 안 낸다 — 그래서 사규의 사람 창을 따로 낸다
- 쓰는 사람의 사번 — 내 목록 화면(`/myProcessList/oftenUseProcess.do`)이 `empcd : "…"` 로 박아 둔다(한 값 두 번)
- 최근 사용 표준 — `/myProcessList/searchOftenUseProcessList.do`(fromDate · toDate · empcd)의 `OftenUseProcessList[]`(processIdx · processName ·
  menuName1..3 · reDeptnm · hname · reRegDate · txtIdx). 30 일에 21 건 · 이틀에 0 건. 줄의 reRegDate 는 연 날이 아니라 그 문서의 시행일과
  같았다(여섯 줄) — 기간은 서버가 연 날로 거르는 것으로 보이나 줄은 연 날을 안 든다. 이 손의 `read` · 화면 창 GET 은 이 목록에 안 남는다
- 접근 가능한 표준 — `/myProcessList/getMyAuthProcessList.do`(empcd · securityGrade · authRange r)의 `myProcessList[]`. 등급 하나씩은 수 초
  (사외비A/비공개 99 건 2.3 초 · 사외비B 423 건 8.6 초 · 사외비A 775 건 13.6 초), 빈 등급(전체)은 2691 건 · 54.6 초라 손이 안 받는다

## 회사 PC 에서 잰 것 — 짓지 않은 화면 기능

- 첨부 받기(`/file/fileDownload.do` · newFileName · filePath · orgFileName) — 일반 등급 인증서 PDF 한 건을 받으니 DRM(Fasoo)이 감싼 파일이었다.
  받기가 서버에 기록을 남기는지는 못 가렸다(관리자 화면 「표준 조회이력」 을 이 계정이 못 본다) — 그래서 안 짓는다. 잴 길: 관리자 계정으로 그
  화면을 열어 받기 한 번 전 · 뒤를 견준다. 기록이 안 남으면 받아서 스킬 drm-office-read 로 넘기는 손가락으로 짓는다
- 본문 PDF 받기(`/file/docDown.do` · processIdx · widthSize) — 같은 까닭(기록 여부를 못 가렸다)으로 안 짓는다. 본문은 `read` 가 글자로 읽는다
- 부서별 통계(표준현황 · 승인현황 · 윤독현황 — `/stdrevision/ajax/selectStdRevisionList.do` 따위 JSON 본문 POST) — 부서 셋으로 쟀고, 윤독현황은
  날짜를 주면 SQL 오류 화면이 온다. 대화로 묻는 일이 드물고 부서 나무(150 곳 남짓)를 함께 다뤄야 해 이번 판에 안 짓는다
- 윤독 현황 · 윤독 완료 · 열람 기록 · 권한 신청 · 개정 · 폐지 · 관리자 화면 — 쓰는 요청이거나 결재 흐름이라 안 짓는다. 윤독 완료
  (`completeReading.do`)와 열람 기록(`insertSopConnHis.do`)은 손이 부르지 않는다
- 윤독 현황 — `/myProcessList/getReadingList.do`(empcd · processName · type · readingType DT/NT · fromDate · toDate · offset · limit)의
  `readingList[]` · `totalCnt`, 명단은 `/myProcessList/goReadingEmpList.do?param=<readingIdx>` 창. 잰 계정은 0 건(제 몫의 윤독만 온다)이라 줄 꼴은 못 쟀다
- 부서별 통계의 칸 — 부서 나무는 `/statis/api/getStdDeptList.do` · `getApprovalDeptList.do` · `getReadingDeptList.do`, 본조회는 JSON 본문
  `{deptParams:[부서 코드…], fromDt, toDt}` 를 `/stdrevision/ajax/selectStdRevisionList.do` · `/approval/ajax/selectApprovalList.do` ·
  `/reading/ajax/selectReadingList.do` 에 POST. 답 칸은 표준현황 create_cnt · revision_cnt · delay_cnt · disposal_cnt, 승인현황 exap · exre · apcm ·
  apre, 윤독 y_cnt · n_cnt. 윤독만 날짜를 비워야 선다
- 변경진행목록(`changeprolist.do`)의 일곱 탭 — searchExReqList · searchRlReqList · searchReadList · searchApReqList · searchIsReqList ·
  searchTrReqList · selectRegisterPlan. 주소만 화면 코드에서 뽑았고 안 불렀다(잰 계정에 결재 대기 0 건)
- 전사 표준 현황(`/myProcessList/enterpriseProcessStatus.do` · 창 `goDeptTypeProcessListPop.do?param=<deptcd>,<menuIdx>`) — 화면 메뉴에서
  주석으로 빠져 있다. 안 불렀다
- 본문 PDF 받기의 너비 칸 `widthSize` 는 화면의 「다운로드(보기)」 가 준다 — 안 불렀다

## 회사 PC 에서 잰 것 — 손가락이 필요 없는 화면 기능 (2026-11-19 · #292 B)

- 통합 검색은 범주마다 잘리지 않는다 — 화면의 「더보기」(범주당 세 건 → 전체)는 화면이 보이는 규칙이고, 답의 `searchMenuInList1..7` 은
  다 오며 그 합이 `searchListCnt` 와 같았다(질의 다섯). `menuId` 를 주면 `menuAllSearchTF` 가 false 로 그 범주만 온다. 일곱째 목록은
  화면의 구분 칸(여섯)에 이름이 없고 잰 질의에서 늘 0 건이었다
- 본문 검색 줄의 `content` 는 걸린 대목이 아니라 본문 앞부분이다(9 천 ~ 9 만 자) — 화면이 첫 매치 앞을 스크립트로 자른다. 대목은
  `read --grep` 이 낸다
- 부서 표준(`getMyDeptProcessList.do` · deptcd)과 나의 표준(`getMyProcessList.do` · empcd)은 `find <부서 · 이름>` 과 같은 답이다 — 부서
  표준 8 건이 받아 둔 목록의 같은 부서 8 건과 같았다
- 관련사이트(`selectProcessInfo` 의 `searchRelationSite[]` · siteName · siteUrl)는 표본 40 건 가운데 한 건에만 있었고 그것도 빈 이름이었다
- 목록 EXCEL 받기(`fnExcelReport`)는 서버 기능이 아니라 브라우저가 화면 표를 .xls 로 만든다
- 다운사이징 설정(`saveDownsizingValue.do` · `loadDownsizingValue.do`)은 화면에서도 숨긴 칸이다(`#tr_downsizing{display:none}`)
- 관리자 화면(`/admin/*`)은 일반 계정에 오류 화면을 낸다. 사진 올리기 폼 · `testFunction.do` · AI 범주 콤보는 화면 코드에만 남은 것이다
- 화면 메뉴는 `getMyMenuList.do` 가 내는데 그 답은 안 받았다 — 위 기능 목록은 목록 화면 열둘 · 문서 창 · 개정이력 창 셋에서 뽑은 것까지다

## 대화 도구에서 잰 것 (2026-11-12 · Claude Code)

- 명령의 출력이 30 KB 를 넘으면 도구가 파일로 빼고 모델에게는 앞 2 KB 만 싣는다 — 글자 수가 아니라 바이트로 건다(한글 1 만 400 자 ·
  31 KB 가 걸렸다). 그래서 답 하나를 `OUT_BYTES` 안에 맞춘다

## 회사에서 아직 안 잰 것

- 열람 기록이 `selectProcessInfo.do` 쪽에서도 · 화면 창 GET 쪽에서도 남는지 — 앱 안의 기록 화면(「표준 조회이력」)을 이 손으로 볼 권한이 없다
- 세션 파일만 낡고 Edge 의 세션은 살아 있을 때 `session_first` 의 둘째 판(받는 손이 말없이 새 파일을 받아 한 번 더)이 서는지 —
  로그오프로는 Edge 째 사라져 첫 판의 종료 3 으로 끝났다
- 여섯 범주를 동시에 받을 수 있는지 — 한 세션의 동시 요청을 앱이 받으면 새로 받기가 가장 큰 범주 하나(30 초 남짓)로 준다
- Codex · agy 의 출력 한도 — Claude Code 의 것만 쟀다
- 첨부 받기 · 본문 PDF 받기가 서버에 기록을 남기는지 — 위 「짓지 않은 화면 기능」 의 잴 길
- `find --in` · `recent --in` 이 경로의 어느 깊이에서든 범주 이름의 일부로 걸 때 실물 목록에서 얼마나 넓어지나 — 맨 위 범주 이름(「안전」 · 「인증」)이
  다른 범주 이름 안에도 들면 맨 위 범주 하나로 좁히던 부름이 넓어진다. 받아 둔 실물 목록에서 맨 위 범주 여섯의 이름이 둘째 깊이 아래에도
  드는지 · `find <말> --in 안전` 의 건수가 `tree 안전` 의 건수를 넘는지를 본다

## 들어가는 길 — `scripts/cbsop.py` 가 기댄다

1. 사내 세션 쿠키(.posco.net)를 싣고 SSO 넘김 화면(SSO_PAGE)을 GET — 200 에 숨은 칸 폼(ssoToken · …)이 온다.
   세션이 끊겼으면 그 칸이 없다
2. 그 칸을 앱 뿌리(APP_ROOT)에 POST — 앱이 `var epId = encodeURIComponent('…')` 로 열쇠를 든 화면을 낸다
3. `/test/test_login.do?aes=<열쇠>` 를 GET — 302 → `/main/main.do` 면 선 것. 앱은 그때 제 세션(JSESSIONID)을 심는다
4. 그 뒤 `/main/ajax/…` 를 폼 꼴 POST 로 부른다. 끊긴 앱 세션은 302 → `/test/closePage.do` 다

앱의 세션 쿠키는 앱 호스트에 살아 받는 손이 남기는 세션 파일(회사 도메인 쿠키)에는 안 든다. 들어가기는 한 번에 1 초 안쪽이었다.
