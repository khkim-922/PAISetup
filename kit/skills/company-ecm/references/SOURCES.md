# 출처

이 스킬은 참조 없이 섰다 — 사내 ECM 과 그 PC 에이전트를 다루는 공개 표준 · 공개 스킬이 없다.

- 본 후보 — 공식 스킬 저장소(anthropics/skills) · 스킬 등록소에 문서 관리 시스템(ECM · DMS) 스킬이 없다. 상용 ECM(SharePoint ·
  OpenText · Documentum)의 공개 API 스킬은 그 제품의 REST 를 부르는 것이라 서버가 파일을 안 주고 PC 에이전트가 받는 이 자리와 꼴이 다르다
- 회사 ECM 의 꼴 — 아래 「사내 ECM 에서 잰 것」이 든다. 그 꼴로 지은 차례와 막는 까닭은 `DESIGN.md`
- 기본 앱 해시의 계산 — 아래 「Windows 기본 앱」이 출처(공개 저장소 · 커밋)를 든다. 그 저장소는 라이선스 표시가 없어
  원문을 여기 보관하지 않는다

## 회사에서 잰 것 — 남긴 글자 (2026-11-16)

`read` 가 글자를 문서 열쇠로 남기고 다시 읽을 때 받지 않는 길(결정 0231)을 회사 PC 의 진짜 ECM · 에이전트로 쟀다. 사외비 등급 덱
한 건(메일의 문서함 첨부가 댄 열쇠)을 네 번 읽었다.

- 첫 판 22.9 초 — 에이전트가 받아 파워포인트로 읽었다. 둘째 판부터 2.2 ~ 2.4 초 — 파워포인트가 안 뜨고 에이전트 폴더에 새 받은 폴더가
  안 섰다(7 → 7). 답은 남긴 글자 자리와 함께 「받은 파일이 남아 있다」로 에이전트 폴더의 그 파일 경로를 댔다. 그 경로로 drm-office-read
  가 찍은 장은 다음 부름에 남긴 그림으로 왔다

## 회사에서 잴 것 — 남긴 글자

- 받은 파일을 에이전트가 비운 뒤 다시 `read` 하면 「--fresh 로 다시 받는다」 쪽 답이 오나
- 판이 오른 문서의 옛 열쇠로 속성 화면(등급 읽기)이 무엇을 답하나 — 지금은 옛 판의 글자와 「list 로 새 열쇠를 받는다」를 낸다

## 사내 ECM 에서 잰 것 — 어기면 조용히 망가진다

- 보안등급은 속성 화면의 숨은 칸 `ecm_security_level` · `ecm_open_flag` 가 든다(`Ecm.security`) — 내 문서와 메일로 받기만
  한 문서 모두에서 칸이 든다. 기밀로 바꾼 문서는 소유자에게도 목록 · 화면에서 빠지지만 속성 화면은 열쇠로 그대로 읽힌다.
  그 화면을 읽는 것이 열람으로 남는지는 안 쟀다. Fasoo 로 감긴 파일 머리에는 등급이 없다 — 등급의 원본은 이 화면뿐이다
- 세션은 `swpecm.posco.net` 쿠키(`JSESSIONID`)다. 세션 파일에는 다른 호스트의 쿠키도 들어 있다 — 그 호스트에 맞는
  쿠키만 싣는다(도메인 · 경로 · 시한 · `secure`). 세션 없이 열면 `302 → /ECM/logout.jsp` 가 온다 — 리다이렉트는 따라가지
  않고 「끊겼다」로 읽는다(따라가면 쿠키가 다른 주소로 실린다)
- 목록 · 건수 · 열기는 다 `GET /ECM/ajaxAction.do?ServiceName=…` 이다. 답은 `text/xml` 로 오지만 몸은 앞에 빈 줄이 붙은
  JSON 이다. 성공은 `MB_RTN_VALUE`, 까닭은 `MS_MSG_CODE` · `MS_MSG_DESC`
- 목록은 `DocList-service&getDocList=true` 의 `ML_DOC_LIST[]`, 건수는 `&getDocCount=true` 의 `MI_DOC_COUNT` 다. 내
  문서함은 `formId=F_LIST_MYDOC` · 화면의 기본은 `docCntPerPage=15` · `searchPeriod=6M` · `fileType=ALL_FORMAT` ·
  `sortDirection=desc`. 기간 `searchPeriod` 는 화면 기간 필터의 일곱 값(`1M` · `6M` · `12M` · `24M` · `36M` ·
  `60M` · `ALL`)만 뜻대로 선다 — `1Y` 는 `MSG_E_0056` 으로 거절되고, `1W` 는 거절 없이 1M 보다 많은 건수가 온다
- 부서 · 프로젝트 문서함은 화면 왼쪽 「내 부서 컨텐츠」와 같은 `formId=F_LIST_MYDEPT` · `listKey=<문서함 열쇠>_<문서함 열쇠>` 다.
  그 사람의 문서함은 메인 화면의 `<option id="MENU_DEPT|MENU_PROJECT" value='cab…'>이름</option>` 이, 제 부서는
  `s_UserDeptCabinetId` 가 든다. 부서 문서는 내 문서함 찾기에 안 걸린다
- 열기는 두 걸음이다 — `OpenContents-service&view=true&MS_OBJECT_ID=<16 hex>&formId=F_LIST_MYDOC` 가 `MS_DOC_ID` ·
  `MS_OBJECT_ID` · `MS_FILE_NAME` 을 주고(파일 바이트는 안 준다 · 부서 문서도 같은 `formId` 로 선다), 그 값을 에이전트
  웹소켓에 한 줄 `Download␈<MS_DOC_ID>␈<MS_OBJECT_ID>␈VIEW␈<MS_FILE_NAME>␈ECM`(`␈` = `\x08`)로 보내면 `OK` 가 온다.
  에이전트가 파일을 새 폴더에 받고 기본 앱으로 연다
- 편집 열기는 `CheckOutCheckIn-service&checkout=true&MS_OBJECT_ID=<16 hex>` 가 서버에서 잠그고 같은 세 값을 준다(`MB_RTN_VALUE`
  가 참이면 실패 코드가 같이 와도 선다). 줄의 셋째 값이 `EDIT_NOCHECKIN` 이면 에이전트가 `CHECKOUT` 아래에 받아 읽기 쓰기로
  연다. 받은 이름은 `<이름>_<문서 열쇠>_<계정>.<꼴>` 이다 — `checkin_document` 가 이름 속 열쇠로 그 문서를 알아본다.
  받을 때는 이름을 짓지 않고 새로 생긴 파일을 집는다(xlsx 로 쟀다 · docx · pptx 는 안 쟀다)
- 편집완료 창은 고친 문서를 저장해 닫으면 뜬다 — 같은 앱에 사람의 다른 문서가 남아 앱이 떠 있어도 뜬다. 고친 것 없이 닫으면 창 없이
  잠금만 풀린다. 창 속은 웹 화면이고 판 라디오
  `choice_version` 의 기본은 지금 판(덮어쓰기)이다 — 지금 판보다 큰 값이 꼭 하나일 때만 그것을 고르고, 아니면 아무것도 안 누른다. 수정 내용 칸은 `version_desc` · 저장은 그 화면의
  `fn_save()` · 올리기는 에이전트가 한다. 판은 문서 정보 화면(`docProperty_simple.do?ServiceName=DocPropertyHtml-service&basicinfo=true
  &DOCID=<16 hex>&getType=user`)의 「최종 버전」 칸이 든다
- 폴더 나무는 `GetSubNaviMenu-service&menuType=<MENU_DEPT|MENU_PROJECT>&upperKey=<문서함>` (문서함 바로 아래) ·
  `menuType=F_LIST_FOLDER&upperKey=<문서함>_<폴더>` (폴더 아래)다. 답 `ML_MENU_LIST[]` 의 `MS_MENU_ID` 가 `<문서함>_<폴더>`,
  `MS_HAS_SUB` 가 아래 폴더 수다. `upperKey` 에 폴더 열쇠만 주면 「폴더 경로를 조회하는데 실패」가 온다
- 새 문서 등록은 화면의 「컨텐츠 등록」 저장과 같다 — ① `POST ajaxAction.do?ServiceName=CheckDuplicatedDoc-service&checkDup=true`
  (몸 `folderID` · `title` · `fileExt`)가 같은 이름을 `ML_DUPLICATED_LIST` 로 낸다 ② 에이전트 웹소켓에 한 줄
  `uploadfilecreatedoc␈contentName_1|<PC 경로>` 를 보내면 에이전트가 파일을 `EcmUploadCreateServlet` 으로 올리고
  `{"LISTID","SERVERFILE","SERVERPATH":"/WAS/ECMTEMP/<uuid>.<확장자>"}` 를 답한다 ③ `POST ajaxAction.do?isHTML=T` 의 몸이
  `register=register` · `ServiceName=RegisterContents-service` · 파일 줄 XML(`fileList`) · `ecm_folder_id` ·
  `ecm_security_level` · `ecm_open_flag` 따위다 — 화면처럼 칸마다 인코딩하지 않고 이어 붙이고, 이름만 `encodeURIComponent`
  한다. 답의 `MS_OBJECT_ID` 가 새 문서 열쇠이고 판은 0.0 이다. 보안 짝은 화면의 단추 여섯(`SECURITY_PAIRS`)뿐이다.
  감긴 파일도 그대로 올라가고 받은 문서는 감긴 채다. 화면은 설정에 따라 올린 로컬 파일을 지우지만(`filedelete`) 이 손은 안 지운다
- 권한 칸은 속성 화면의 iframe `roleAssignEdit.jsp` 이고 셋이다 — 편집/복사/읽기/인쇄(공동 R · 역할 `R`) · 복사/읽기/인쇄(`S`) ·
  읽기/인쇄(`V`). 지금 명단은 `json.do?ServiceName=DocPropertyHtml-service&role=true&pageType=user&ECM_DOC_ID=doc<16 hex>` 의
  배열(`MS_ROLE` · `MS_OBJECT_ID` · `MS_USER_CLASS` …)이고 소유자는 안 든다. 그 밖의 역할(승인 `A` · 검토 `C` · 조회 `I` ·
  배포 `D`)은 화면이 그릴 때 `S` · `V` 칸으로 옮겨 그린다 — 그대로 되보내면 역할이 바뀌므로 그런 문서는 안 바꾼다
- 사람 찾기는 `json.do?ServiceName=searchPeople-service&kind=name&value=<이름>` — **이름으로만** 찾는다(메일 ID · 사번은 빈
  답). 답에 메일 ID · 사번 · 부서가 들고, 메일 주소록의 그 사람과 같다. 조직은 `searchOrgan2-service` 의 `search=1`(부서 이름) ·
  `getDept=1&kind=dept&deptId=`(바로 아래 부서) · `getUser=1&deptId=`(바로 든 사람). 회사 열쇠 `companyId` 는 메인 화면이 든다
- 화면이 조직을 칸에 옮기면 부서가 아니라 **그 순간 바로 든 부서원 개인**으로 펼친다(아래 부서는 안 든다). 부서 줄(`D`)을 명단에
  넣고 저장하면 「저장 되었습니다」가 오고 아무것도 안 남는다
- 저장은 `POST ajaxAction.do?ServiceName=ModifyDocProperty-service` 하나 — 몸은 화면의 `getDocInfoData` 꼴이다: 속성 화면의 숨은
  칸(폴더는 `ecm_folder_id` · 보안은 `ecm_security_level` · 완료일은 `ecm_EndDate` 에서) · `isChangeRoleInfo=TRUE` · 권한
  **전체** 명단 XML(`roleList` — 줄마다 칸 여덟, 역할 · 사람 열쇠 · `U` · 회사 열쇠만 차고 나머지는 빈 칸) · 즐겨찾기
  (`favorite_info` 의 폴더들) · 체크 칸 셋(화면에 체크 칸이 없으면 `F`). 화면처럼 칸을 인코딩 없이 이어 붙이고 이름 둘만
  `encodeURIComponent` 한다. 거두기는 그 사람을 뺀 명단을 보내는 것이다. 성공은 `MSG_I_0147`
- ⚠ 같은 서비스 모음에 편집취소 · 올리기 요청 · 지우기가 있다 — 이 손은 짓지 않고, 지으려 하면 서버에 닿기 전에 막는다. 잰 꼴 밖의
  서비스 · 칸 · 값도 같이 막는다(닫힌 목록 `READS` · 편집 열기 문 `_guard_edit`)

## Windows 기본 앱 — 받아 주는 값 · 어기면 조용히 망가진다

`scripts/default_app.py` 가 기댄다.

- `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.<확장자>\UserChoice` 의 `ProgId` 와
  `Hash` 둘이 한 벌이다. 해시가 틀리면 Windows 는 그 키를 지우고 고르는 창으로 돌아간다 — 오류는 안 낸다
- 해시의 재료는 `확장자 + 사용자 SID + ProgId + 그 키를 마지막으로 쓴 시각(분으로 내림 · FILETIME 16 자리 hex)
  + shell32.dll 이 든 「User Choice set via Windows User Experience {…}」 글` 을 소문자로 이은 것이다. 그래서 키를 쓴
  분과 해시의 분이 같아야 한다 — 분 경계 직전이면 기다렸다 쓰고, 쓴 뒤 키의 시각으로 다시 지어 맞춘다
- 계산의 꼴은 DanysysTeam/PS-SFTA 의 `SFTA.ps1` `Get-Hash` (커밋 22a32292e576afc976a1167d92b50741ef523066)가 공개한
  것을 따랐다. 그 저장소는 라이선스 표시가 없어 코드는 옮기지 않았다 — 같은 셈을 부호 없는 32 비트 산술로 우리가 다시 지었다
- UserChoice 보호 드라이버(UCPD)는 일부 확장자(`.pdf` 로 알려짐)의 이 키 쓰기를 막는다. 막히면 `PermissionError` 가
  나고, 그 확장자는 사람이 한 번 「항상 이 앱 사용」을 고르게 이끈다
- 적은 뒤 Windows 가 그 확장자를 정말 그 ProgId 로 푸는지 `AssocQueryStringW` 로 묻는다 — 안 받았으면 이번에 적은
  키를 걷고 `DefaultAppNeeded` 를 낸다

### 기본 앱이 서 있어도 고르는 창이 뜨는 자리

- 그 확장자를 열 수 있다고 등록된 앱(`HKCR\.<확장자>\OpenWithProgids`) 가운데 `HKCU\…\ApplicationAssociationToasts` 에
  `<ProgId>_<확장자>` 값이 없는 앱이 있으면, Windows 는 그 앱을 새로 깔린 앱으로 보고 그 확장자를 열 때 「이 파일을 열 때
  사용할 앱」 창을 한 번 띄운다(새 앱 옆에 「새로 만들기」가 붙는다). 그 창이 떠 있는 동안 문서는 안 열린다
- 그래서 `ensure` 는 기본 앱이 선 확장자에서, 빠진 앱의 값만 DWORD 0 으로 더한다 — Windows 가 그 앱을 보인 뒤 적는 값과
  같은 꼴이다. 해시가 없는 키라 Windows 가 막지 않는다. 있는 값과 기본 앱은 건드리지 않는다. 그 확장자에서 「새 앱이
  깔렸다」 알림만 안 보이게 된다

## Adobe Reader · Acrobat — pdf 탭 닫기

`scripts/close_acrobat.ps1` 이 기댄다.

- Reader DC 는 문서 목록을 주는 COM 이 없고, DDE(`AcroViewR21`)는 붙기는 해도 명령을 다 거절한다(`DMLERR_NOTPROCESSED` · Reader DC
  21.11 에서 잰 것). 탭도 UI Automation 에 안 드러난다
- 에이전트는 받은 파일을 마지막에 띄우므로 읽기 판에서는 받은 pdf 가 앞 탭이다. 닫은 뒤 제목에 문서 이름이 없으면(「Adobe Acrobat
  Reader DC …」) 남은 문서가 0 이다
- 받은 파일을 셸로 다시 열면 떠 있는 Reader 에 파일을 넘기는 길이 DDE 라 Reader 가 「Acrobat failed to send a DDE command」 오류 창을
  띄우고 멈췄다
