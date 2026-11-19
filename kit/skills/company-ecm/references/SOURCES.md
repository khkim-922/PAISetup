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

## 집 PC 에서 잰 것 — 편집 패스의 고치는 손 (2026-11-18)

`change_doc.ps1` 과 `close_view.ps1 -RequireClean` 을 감기지 않은 평문 덱 · 통합 문서로, 에이전트처럼 실행 파일에 파일을 줘 띄운
파워포인트 · 엑셀(Microsoft 365 · 16.0)에 붙어 쟀다. DRM 과 ECM 에이전트는 없는 자리다.

- 파워포인트 — 두 장에 나오는 조각 · 없는 조각 · 장 수 밖 자리는 아무것도 안 고치고 파일이 그대로였다. 한 번 나오는 조각 둘(하나는
  빈칸 둘이 든 원문을 빈칸 하나로 준 조각)과 덱 끼워 넣기(1 장 뒤)가 한 부름에 서고 저장됐다. 저장 안 된 고침이 있는 창은
  `-RequireClean` 이 안 닫았다(종료 4)
- 엑셀 — 수식 칸에 걸린 조각은 안 고쳤다. 숫자 칸의 조각은 고친 뒤 숫자로 섰고, 시트 끼워 넣기(0 = 맨 앞)가 섰다
- 이 PC 의 워드는 COM 저장이 멈춰 고치는 손의 워드 갈래(조각 바꾸기 · 본문 끝 끼워 넣기 · 저장)를 안 쟀다
- 이 PC 에서 `New-Object -ComObject PowerPoint.Application` 은 `CO_E_SERVER_EXEC_FAILURE` 로 지고 창 없는 프로세스가 남았다 — 시험
  덱은 python-pptx 로 짓는다(검사의 `_make_decks`)

## 회사에서 잴 것 — 편집 패스의 고치는 손

- 에이전트가 띄운 **감긴** 문서 창을 `office_doc.ps1` 이 전체 경로로 찾고, `change_doc.ps1` 이 그 창에서 조각을 바꾸고 끼워 넣고 저장하나
  (Fasoo 아래의 Save · 평문 덱 · 시트를 감긴 문서로 옮기기)
- 워드 문서 — 조각 바꾸기 · 본문 끝 끼워 넣기 · 저장
- 미리 보기가 저장한 뒤 올리기가 **저장 없이** 닫았을 때(`-RequireClean`) 에이전트의 편집완료 창이 뜨나 — 잰 것은 「고친 문서를 저장해
  닫으면 뜬다」이고, 저장과 닫기를 두 부름으로 나눈 판은 안 쟀다
- 아무것도 안 고친 채 `preview-checkin`(저장 안 함) → `checkin` 하면 에이전트가 창 없이 잠금만 푸나
- 감긴 문서의 `Saved` 표시가 고침을 따라가나 — 틀리면 `-RequireClean` 이 고침이 없는 창을 「고친 것이 있다」로 막는다(그때는
  `preview-checkin` 을 다시 부르면 저장해 맞춘다)
- 감긴 덱 · 통합 문서에서 편집취소(`cancel-edit`) — 잰 것은 평문 워드 문서 하나다

## 회사에서 잴 것 — 찾기 · 권한

- 전사 검색 줄의 `ECM_MODIFY_DATE` 와 목록 줄의 고친 날이 늘 같은가 — 검색엔진은 등록 뒤 곧바로 걸렸다(잰 한 판)
- 태그로 전사 검색(`ecmtaglist`) · 결재 문서 거르기(`approval`) — 칸은 아래 「읽기지만 안 지은 것」 줄에 있다. 안 보냈다
- 권한 사람 줄의 `MS_EMAIL_ID` 가 메일 ID(@ 앞)만 드나 — 손은 ID · 온 주소를 다 받아 견준다
- `link` 가 열쇠만으로 지은 링크(아래 「URL 복사」의 꼴)가 회사 Edge 에서 열리나 — 16진 글자의 대소문자 · 화면이 내는 링크와 글자째
  같은가를 화면의 「URL 복사」 한 번과 견준다. 그 링크가 다음 판이 오른 뒤에도 문서를 여나(지금 판을 여나 · 그 판을 여나)
- 「보기(최신버전)」 걸음(`OpenContents-service&view=true&…&MS_CURRENT_YN=T`)이 활용 건수의 열람을 하나 올리나 — `read` · `checkin` ·
  `link` 가 그 걸음으로 지금 판을 묻는다. `versions --more` 의 열람 수를 앞뒤로 본다

## 회사에서 잰 것 — 화면에 있는데 손가락이 없던 것 (2026-11-19 · #292 B)

화면 코드(`ecmMain.js` · `docList.js` · `contents_new.js` · 속성 · 이력 · 상세검색 화면)에서 사용자 쪽 요청을 뽑아 손이 안 부르던 것을
쟀다. 바꾸는 측정은 사람이 고른 시험 문서 하나(사람의 개인폴더 · 사외비A/비공개 · 권한 없음)에서만 했고 끝에 이름 · 태그 · 완료일을
되돌렸다. 시험 문서는 지우지 않았다(지우기는 손가락이 아니다).

- **판 이력** — `json.do?ServiceName=DocPropertyHtml-service&history=true&pageType=user&R_OBJECT_ID=<doc 열쇠>&isIncludeCntQry=T|F
  &pageNumber=<0=건수 · 1…>&docCntPerPage=<n>&isMinorManagement=F`. 건수 답 `[{MI_COUNT}]` · 줄 `MS_OBJECT_ID`(그 판의 열쇠) ·
  `MS_IS_CURRENT`(CURRENT · NOT) · `MS_VERSION_LABEL` · `MS_CREATOR_NAME` · `MS_CREATOR_DEPT_NAME` · `MS_CREATION_DATE` ·
  `MS_VERSION_DESC`(수정 내용 — 빈칸 하나로 오기도 한다) · `MS_CONTENT_SIZE`. `R_OBJECT_ID` 는 **doc 열쇠**다 — 문서 열쇠로 물으면 0 판
- **문서 열쇠와 doc 열쇠** — 문서 열쇠(`MS_OBJECT_ID`)는 판마다 바뀌고, doc 열쇠(`MS_DOC_ID` · `doc…`)는 판이 올라도 같다. 첫 판(0.0)은
  `doc` + 문서 열쇠지만 판이 오른 문서는 다르다 — 그 문서의 역할 목록을 `doc` + 문서 열쇠로 물으면 빈 답(`null`)이 왔다. doc 열쇠는 속성
  화면의 숨은 칸 `MS_DOC_ID` 가 든다. ⚠ 빈 답을 빈 명단으로 읽고 권한을 저장하면 걸린 명단이 다 지워진다 — 손은 늘 `MS_DOC_ID` 로 묻는다
- **옛 열쇠 → 지금 판** — 옛 열쇠는 옛 판을 가리키고 저절로 새 열쇠가 되지 않는다(보기 첫 걸음은 옛 판을 준다). 화면의 「보기(최신버전)」
  처럼 `OpenContents-service&view=true&MS_OBJECT_ID=<옛 열쇠>&formId=F_LIST_MYDOC&MS_CURRENT_YN=T` 가 지금 판의 `MS_OBJECT_ID` 를 준다.
  옛 열쇠로 속성 화면을 열면 지금 판의 화면이 온다
- **보안등급 변경 이력 · 활용 건수** — 같은 `json.do` 에 `&security=true&pageType=user&ECM_DOC_ID=<doc 열쇠>&isIncludeCntQry&pageNumber&
  docCntPerPage`(줄 `MS_EVENT_DATE` · `MS_USER_INFO` · `MS_BEFORE_VALUE_DD` · `MS_AFTER_VALUE_DD`) · `&useinfo=true&pageType=user&
  ECM_DOC_ID=<doc 열쇠>`(`ECM_VIEW` · `ECM_ATTACH` · `ECM_COPY` · `ECM_RECOMMEND`). 속성 저장 한 번이 등급이 그대로여도 보안등급 변경
  이력에 한 줄(같은 등급 → 같은 등급)을 남겼다
- **우클릭 메뉴(지금 할 수 있는 것)** — `POST ajaxAction.do?ServiceName=GetContextMenu-service&isHTML=T` 몸 `formId=F_LIST_MYDOC&
  itemObjIds=<열쇠>&IsChorme=T` → `ML_MENU_LIST[{MS_DD_VALUE, MB_IS_ENABLED}]`. 조회다. 잠긴 판에는 편집 꺼짐 · 편집완료 · 편집취소 켜짐
- **잠근 이가 나인가** — `CheckOutCheckIn-service&checkuser=true&MS_OBJECT_ID=` → `MS_IS_CHECKOUT_EQUAL` T|F. 안 잠긴 문서도 F
- **편집취소** — 화면의 차례는 서버 걸음 `CheckOutCheckIn-service&cancelcheckout=true&MS_OBJECT_ID=`(성공 답 · `MS_CHECKOUT_PATH` ·
  `MS_CANCEL_CHECKOUT_FOLDER`)과 에이전트 웹소켓 한 줄 `cancelcheckout␈<열쇠>` 다. **잠금을 푸는 것은 에이전트 줄이다** — 서버 걸음만
  보낸 뒤 속성 화면 · `checkuser` 는 잠긴 채였다. 편집 창이 떠 있으면 에이전트는 `현재 파일을 사용 중입니다.` 로 안 풀었고, 창을 닫은 뒤
  `OK` 로 풀었다. 안 잠긴 문서에는 `java.lang.Exception: CancelCheckOut` 을 답했다. 고친 것 없이 연 창을 닫으면 에이전트가 창 없이
  잠금을 푼다. ⚠ 저장된 고침이 있는 창을 닫으면 에이전트의 「편집완료」 창이 뜨고, 편집취소 뒤에도 그 창은 남는다 — 그 창의 저장을
  누르면 버린 고침이 새 판으로 올라간다. 동시편집 문서의 `officecancelcheckout` 은 안 쟀다
- **속성 저장(이름 · 태그 · 완료일)** — 권한과 같은 `ModifyDocProperty-service` 몸이다. 화면은 권한 탭을 안 건드린 저장에도 그 탭의 지금
  명단을 싣고 `isChangeRoleInfo=F` 로 둔다. 이름은 `MS_DOC_TITLE`(encodeURIComponent) · 태그는 `tagList`(쉼표로 이음 · 한글 · 영문 ·
  숫자 · 10 개) · 완료일은 `MS_DUE_DATE`(YYYY-MM-DD). 지금 완료일은 숨은 칸 `MS_DUE_DATE` 가 든다 — 고르는 칸 `ecm_EndDate` 는 늘
  `0001/01/01` 로 그려진다. 저장 몸의 완료일이 `0001/01/01` 이면 서버는 완료일을 안 바꿨다 — 완료일을 없애는 길은 없다. 새로 등록한
  문서의 완료일은 서버가 등록일 + 14 일로 넣었다
- **이름의 #** — 등록 이름의 `#` 는 서버가 말없이 뗐다(「[테스트] #292 …」 → 「[테스트] 292 …」). 속성 화면은 `%` 와 작은따옴표 꼴을 막는다
- **문서함 안 폴더의 목록** — 왼쪽 나무에서 폴더를 누른 꼴 `DocList-service&getDocList|getDocCount=true&formId=F_LIST_FOLDER&
  listKey=<문서함>_<폴더>` 다. 그 폴더에 바로 든 문서만 온다(아래 폴더는 안 든다). `F_LIST_MYDEPT` 에 폴더 열쇠를 주면 30 초 시한을
  넘겼다. ⚠ 문서함 열쇠를 틀리게 붙여도 같은 폴더의 목록이 온다 — 서버는 폴더 열쇠만 본다
- **왼쪽 메뉴의 다른 목록** — 같은 `DocList-service` 에 `formId` 만 바꾸고 `listKey` 는 빈 글자다: `F_LIST_RECENT_ACCESS`(최근 활용 ·
  `MS_EVENT_DATE`) · `F_LIST_RECENT_REGIST` · `F_LIST_SHARED_DOC`(공유받은 · `MS_SHARED_USER_NAME` · `MS_ROLE`) · `F_LIST_CORESPONSIBLE` ·
  `F_LIST_FAVFOLDER`(중요) · `F_LIST_CHECKOUT`(편집 중) · `F_LIST_RCB`(휴지통 · `MS_DELETE_DATE`) · `F_LIST_GRANT` · `F_LIST_REQUESTED_GRANT`
  (`MS_REQUEST_USER_NAME` · `MS_REQUEST_DATE` · `MS_WORKFLOW_STATUS`). 목록 줄의 잠금 칸 `MS_LOCK_USER_ID` 는 안 잠긴 줄에도 빈칸 하나(" ")로
  온다 — 다듬지 않으면 모든 줄이 잠긴 것으로 읽힌다
- **정렬 · 꼴 모아보기** — `orderBy` 는 `ms_modify_date` · `ms_title` · `ms_file_size` · `ms_owner_name` · `ms_security_level` ·
  `ms_doc_version` 이 먹었고 `ms_reg_date` 는 `MB_RTN_VALUE` 거짓이었다. `fileType` 은 `GATHER_POWERPOINT|EXCEL|WORD|PDF|HWP|IMAGE` ·
  `ALL_FORMAT` — 모르는 값은 거절 없이 0 건이다
- **알림 숫자** — `GetDashboardCount-service&getNoticeCount=true` → `APP_PERMIT` · `REQ_PERMIT` · `APP_SECURITY` · `REQ_SECURITY` ·
  `APP_REVIEW` · `REQ_REVIEW`
- **전사 검색 · 본문 검색** — `POST ajaxAction.do?ServiceName=DocList-service&getDocListEcmEsSearch=true` 몸 `q=posmeta:{…}&page_idx&num&
  backCategory=doc&sysId=ecm`. posmeta 칸은 화면이 짓는 것 그대로(`reqsysid` · `adv_search_type=b` · `subject` · `subject_operator` AND|OR ·
  `allintext`(본문) · `owner` · `creator` · `udaterange|cdaterange`(`YYYY-MM-DD..YYYY-MM-DD`) · `format` · `security` · `docbox` · `folderbox` ·
  `sort` · `subfolder_yn`). 답은 `MB_RTN_VALUE` 없이 `gsa_data_key`(XML — `<M>` 총 건수 · `<R>` 줄의 `<MT N= V=>` 칸 · `R_OBJECT_ID` 가
  지금 판의 열쇠) · `gsa_error_key`(빈 글자면 됐다 · `NO_AUTH`). `docbox` 가 비면 전사(볼 수 있는 문서)이고, 메인 화면의
  `s_deptCabinets`(제 부서는 부서 코드 · 프로젝트는 cab 열쇠 · 끝 쉼표)를 그대로 주면 **볼 수 있는 문서함 전부를 한 요청으로** 찾는다.
  `security` 는 `2A,` 처럼 쉼표로 끝나야 걸리고 `docbox` 가 비면 늘 0 건이었다. 등록한 문서는 곧바로 걸렸다
- **폴더 이름 찾기** — `POST json.do?ServiceName=searchFolder-service&search_html=true&isHTML=T&deptExceptFlag=` 몸 `companyId=&userId=
  <내 사람 열쇠>&value=<두 글자부터>` → `{jsonList:[{MS_OBJECT_ID(fdr…), MS_CABINET_ID, MS_FOLDER_NAME(「문서함/폴더/…」), MS_FOLDER_NAME2}]}`.
  볼 수 있는 모든 문서함을 한 요청으로 찾는다. 내 사람 열쇠는 메인 화면의 `<option id="MENU_PERSONAL" value='usr…'>` 가 든다.
  경로의 `/` 는 이름 안에도 든다(「관세/외국환…」) — 가르지 않는다
- **개인컨텐츠함** — 메인 화면에 `MENU_PERSONAL` 이 있지만 왼쪽 메뉴에는 안 보이고, 등록 길은 문서함(`cab…`)만 받는다. 사람의 개인 문서는
  부서 문서함 안 「개인폴더 > 이름」 에 든다
- **URL 복사(`InterfaceAttachURLGet-service`)는 순수 조회가 아니다** — 아래 「서버에 파일을 짓는 동작」 줄

## 화면 코드에서 읽은 것 · 쟀으나 안 지은 것 — 다음에 다시 훑지 않게 (2026-11-19 · #292 B)

손가락으로 안 지은 화면 동작의 요청 꼴이다. 「읽음」은 화면 코드(`ecmMain.js` · `docList.js` · `contents_new.js` · 속성 · 이력 · 상세검색
화면 · `popups/*.jsp`)에서 꼴만 읽고 서버에 안 보낸 것, 「쟀다」는 읽기로 한 번 보낸 것이다. 칸 값이 서버에서 받아들여지는지는 「읽음」
줄에서는 모른다. 짓기 전에 그 줄의 바꾸는 요청을 사람이 고른 시험 문서로 한 번 잰다. 안 지은 까닭은 줄 끝에 적었다 — 「사람이 화면에서
한다」의 말은 `ecm.py` 의 `NOT_HERE` 가 든다.

### 바꾸는 동작 — 읽음

- **복사** — 확인 `CopyDoc-service&checkValid=true&obj_id=` → 복사 `CopyDoc-service&obj_id=&formId=&favFolderId=&copyRoleFlag=T|F`(역할자를
  같이 복사하나). 폴더를 고르는 팝업은 `&folder_id=&cabinet_id=` 를 더한다. 이력 화면의 「새 컨텐츠로 복사」도 같은 서비스다. 새 문서가 선다
- **폴더 이동** — `MoveDoc-service&obj_id=<열쇠,…>&folder_id=<fdr…>`(미분류로는 `&isUnclassified=T`). 문서함 사이 이동은 다른 주소
  `moveDocToCabinet_new.do?ServiceName=MoveDocToCabinet-service`
- **삭제 · 휴지통** — 휴지통으로 `DeleteRCB-service&obj_id=` · 판을 골라 지우기 `DeleteDoc-service&obj_id=&deleteflag=&<deleteflag>=true` ·
  되살리기 `RestoreRCB-service&obj_id=&isAdmin=` · 완전삭제 `CompleteDelete-service&obj_id=&isAdmin=` · 즉시 삭제 `&delFlag=now` · 휴지통
  비우기 `&delFlag=all`. 휴지통 목록 읽기는 손가락이 있다(`list --box trash`). 되돌리기 어려워 안 지었다
- **소유권 변경** — `ChangeOwner-service&mode=self&fbflag=f&objIds=`(`popups/changeOwnerMyself.jsp`). 속성 저장 몸의 `isChangeOwner` ·
  `MS_NEW_OWNER` 갈래도 있다 — 이 손은 그 칸이 `F` · 빈 글자인 문서만 저장한다(`MEASURED_PAGE`)
- **보안등급 변경** — `POST ChangeSecurityLevel-service` 몸 `user=true&MS_OBJ_ID=<열쇠,…>&MS_SELECTED_LEVEL=&MS_SELECTED_OPEN_FLAG=&
  MS_AUTO_GRANT_FLAG=&MS_ECM_AI_SEARCH_FLAG=`(`popups/changeScrtLevel.jsp`). 기밀을 낮추는 판은 승인 차례(`ecm_security_approve` ·
  `ecm_workflow_type=secuLevel`)가 붙는다. 동료에게 보이는 범위가 바뀌어 사람이 화면에서 한다
- **태그 일괄** — `POST RegisterTags-service` 몸 `MS_OBJ_ID=<열쇠,…>&MS_TAG_LIST=<태그,…>&MS_REGISTER_TYPE=A(더하기)|R(갈아 끼우기)`
  (`popups/registerHashTags.jsp`). 한 문서의 태그는 속성 저장(`apply-props`)이 든다 — 여러 문서를 한 번에 바꾸는 말이 오면 이 꼴을 잰다
- **즐겨찾기** — 더하기 `POST AddFavLinkDoc-service&add=true`(몸 `obj_id` …) · 옮기기 `&move=true` · 빼기
  `DeleteFavoriteLinkInfo-service&delete_link=true&removeType=LR&objIDs=` · 즐겨찾기 폴더 목록 `GetSubNaviMenu-service&
  menuType=F_LIST_FAVORITE_FOLDER`. 즐겨찾는 사람 · 폴더 차례는 `ModifyPriorityFavor-service`. 속성 화면의 `favorite_info` 읽기와 저장 몸의
  `favFolderList` 는 손이 이미 쓴다. 왼쪽 「즐겨찾기 링크」 목록은 `F_LIST_FAV_LINK`(건수 읽기를 쟀다)
- **참조하기 · 공유하기(추천)** — 참조 `FavoriteDoc-service&add=true&obj_id=` · 해제 `&remove=true&favObjId=&targetType=F|R` · 추천
  `json.do?ServiceName=FavoriteDoc-service&recommendAdd=true&ObjectID=&saveFlag=F`(`popups/addRecommendDoc.jsp` — 받는 사람 칸은 팝업 몸이라
  안 읽었다). 남에게 알림이 간다. 읽기 범위를 남에게 주는 일은 권한 패스가 든다
- **편집 예약** — `CheckoutReservationDoc-service&docId=<doc 열쇠>`. 남이 편집 중일 때만 켜진다
- **완료(편집불가)** — `CompleteDoc-service&docObjIds=`. 완료한 문서 목록은 `F_LIST_COMPLETE`(건수 읽기를 쟀다)
- **2 년 연장보관** — `DocKeepExtend-service&obj_id=`. 보존연한이 지난 목록은 `F_LIST_UNUSED_1YEAR`(건수 읽기를 쟀다). 속성 화면은 보존연한을
  안 바꾼다(저장 몸에도 없다)
- **편집권한 · 공유권한 반납** — `DeleteRolePermit-service&docId=&roleType=R|S`. 내 권한이 빠져 되돌릴 길이 없다
- **권한 요청 · 승인 · 반려** — 요청 `POST RequestAuthority-service`(몸은 `popups/requestPermission_multi.jsp` 가 짓는다 — 안 읽었다) · 받은
  요청 목록 `RequestAuthority-service&getDocList=true` · 응답 `&response=true`(`popups/approvePermission.jsp`) · 보안등급 요청 취소
  `RequestSecurityLevel-service&cancel=true&wfId=`. 목록 읽기는 손가락이 있다(`list --box asked-me · i-asked` · `notices`). 남에게 가는
  결재 흐름이라 사람이 한다
- **검토 요청 · 검토 의견** — 요청 `DocCoaching-service&requestCoaching=true&docObjId=` · 의견 목록 `&getCommentList=true&docId=`. 의견 목록을
  문서 열쇠 · doc 열쇠 둘로 보냈더니 둘 다 `MSG_E_0232`(조회 실패)였다 — 열쇠 종류 탓인지 의견이 없어서인지는 못 갈랐다
- **동시편집 취소** — `CheckOutCheckIn-service&officecancelcheckout=true&MS_OBJECT_ID=`. 화면은 「Teams 에 등록된 문서는 삭제된다」를 묻는다.
  Teams 쪽 문서가 지워져 안 지었다 — `cancel-edit` 은 이 갈래를 막는다
- **지난 판으로 되돌리기 · 판 지우기 · 중간버전** — 되돌리기 `RecoverContentVersion-service&view=true&MS_OBJECT_ID=&CURRENT_VERSION_ID=` ·
  판 지우기 `DeleteDoc-service` · 중간버전 `DocPropertyHtml-service&minor_manage|update_minor_manage|delete_minor_manage`. 지난 판 읽기는
  손가락이 있다(`versions` → `read <그 판의 열쇠>`)
- **자동열람** — `DocAutoGrant-service&docId=&revokeFlag=T|F`. 속성 저장 몸의 `ecm_auto_grant_flag` 와 화면의 체크 칸 `id_setAutoGrant` 가
  짝이다 — 손은 그 칸이 선 문서를 안 저장한다(`UNMEASURED_CHECKS`)
- **편집권한 일괄 · 부서 밖 편집권한 회수** — `CoresponUser-service&DOC_OBJECT_ID=` · `DeleteCoresponUser-service&ecmObjId=` ·
  `GrantCoresponUser-service`
- **임원보고 · 복호화(사외 반출) · 구글 공동작성** — 결재 팝업 `jsp/decryption/decryption.jsp`(`ECM_WORKFLOW_TYPE=mailAttach|htmlAttach|google`
  — 팝업 몸을 안 읽었다) · 구글 `DocShereToGoogle-service&googleUploadDoc|googleCancelDoc|googleDownloadDoc=true&wfId=&docObjId=`
- **보기 환경** — `userRegistSeting-service&setThumbNailUserConfig=true` · `&setCountPerPage=true&countPerPage=` — 사람의 화면 설정이다

### 서버에 파일을 짓는 동작 — 쟀다 · 읽음

- **URL 복사** — 쟀다(한 번): `InterfaceAttachURLGet-service&MS_OBJECT_ID=<열쇠>&ACTID=COPYURL&SYSID=ECM` → `MSG_I_0228` · `COPY_URL_INFO`
  (`/ECM/swp_interface.jsp?ACTID=viewlink&OBJECTID=<문서 열쇠의 ASCII hex>&DOCID=<doc 열쇠의 ASCII hex>&SYSID=<"ECM" 의 hex>`) ·
  `SERVER_FILE_NAME`(`/WAS/ECMTEMP/<월>/<일>/<년>/<부서>/<문서 열쇠>_<사람 열쇠>_<시각>_A.html`) · `CLIENT_FILE_ORG`(PC 쪽 바로가기
  html 이름 `<문서 이름>(<꼴>_<크기>KB).html`). 서버가 부를 때마다 임시 html 을 짓는 것으로 보인다 — 메일의 「이름(확장자_NKB).html」 첨부가
  이것이다. 링크 글은 열쇠만으로 지을 수 있는 꼴이지만 서버 기록(사용 로그 · 임시 파일)을 안 가렸다.
  잴 것 — 시험 문서로 두 번 불러 `SERVER_FILE_NAME` 의 시각 마디가 매번 새로 서나 보고, 그 링크를 다른 사람이 열 때 권한 검사를 받나
  (역할자에 없는 사람)를 본다. 화면의 답 글이 「타시스템 첨부 시 역할자에 추가하시기 바랍니다」 다 — 링크만으로는 안 열린다
- **메일로 첨부하기** — 읽음: 문서마다 `InterfaceContentAttachFile-service&mailAttachHtml=true&MS_OBJECT_ID=&SYSID=pcpma|pcfma&ACTID=attach` →
  `SERVER_FILE_NAME` 들을 모아 `&mailAttach=true&ServerFullPath=` → 답 `url`(웹메일 쓰기 창)을 연다 · 사용 로그
  `CreateLog-service&eventType=ATTACH…`. 받는 사람 · 본문은 company-mail 이 든다 — 두 스킬 사이 어디서 잇나는 부모가 정한다
- **PC 에 저장(작업방 내리기)** — 읽음: `DownWorkPlace-service&MS_OBJECT_ID=<열쇠>[&isDecrypt=T]` 뒤 에이전트 웹소켓. `read` 가 이미
  에이전트로 받는다(`VIEW`) — 다른 점은 받은 파일이 사람의 PC 작업방에 남는 것이다. 다운로드 로그가 남는다

### 읽기지만 안 지은 것 — 쟀다 · 읽음

- **상세검색(DB · 「실시간 컨텐츠명 검색」)** — 쟀다: `DocList-service&getDocList|getDocCount=true&isHTML=T&formId=F_LIST_DB_SEARCH&search=true&
  formType=DB&conditionType=AND|OR&conditionTagType=&searchTagVal=&conditionDate=srchModifyDate|srchRegistDate&ownerName=&registerName=&
  secretLevel='2A','2B'&fromInputDateVal=&toInputDateVal=&listKey=ALLCABINET_<cab>|<폴더>&childCheck=T&cabinetId=&folderId=&
  wfStatusType=searchProperty&etcVar=&selCabinetType=MENU_DEPT&searchValue=<제목>&fileType=&approval=`. 줄은 목록 줄과 같은 칸이다. 전사
  검색(`search`)이 같은 칸(소유자 · 등록자 · 보안등급 · 기간 · 꼴)을 한 요청으로 받아 안 지었다 — 문서함 하나 안에서만 찾고, 검색엔진에
  아직 안 걸린 새 문서를 찾아야 할 때 이 길을 잰다
- **태그 · 결재 문서로 전사 검색** — 읽음: posmeta 의 `ecmtaglist`(빈칸으로 이은 태그) · `ecmtaglist_operator` AND|OR · `approval=Y`(결재
  문서만). 안 보냈다
- **문서의 폴더 경로** — 쟀다: `GetDocFolderPath-service&docId=<doc 열쇠>` → `MS_FOLDER_ID` · `MS_FOLDER_PATH` · `MS_CABINET_ID` ·
  `MS_CABINET_NAME` · `MS_CABINET_TYPE`. 문서 열쇠로 물으면 「폴더 경로를 조회하는데 실패」. 목록 줄의 `MS_FOLDER_PATH` 와 속성 화면의
  `MS_FOLDER_PATH` 가 이미 답해 안 지었다
- **이력 탭의 다른 칸** — 쟀다(0 줄): 인수 이력 `DocPropertyHtml-service&handover=true` · 유통 DRM `&swpdrm=true` · 복합컨텐츠 하위
  `&subdoc=true&s_DocId=`. 읽음: 활용 상세 `&usedetail=true&EVENT_CODE=<코드>`. 시험한 문서에 줄이 없어 줄의 꼴을 못 봤다
- **목록을 엑셀로** — 읽음: `POST DocList-service&getDocExcelExport=true` 몸 `formId · selectedEcmObjId …`. 화면이 답으로 파일을 짓는다 —
  대화는 `list --json` 으로 같은 줄을 받는다
- **빠른 보기(퀵뷰)** — 읽음: `OpenContents-service&quickview=true&MS_OBJECT_ID=&formId=` → `MS_QUICKVIEW_URL` 로 form POST. 그 앞에
  에이전트 웹소켓의 `getssologininfo` 로 SSO 토큰을 받는다. `read` 가 글자를 든다
- **챗봇 검색** — `ecmChatbotMain` · `F_LIST_CHATBOT_SEARCH`(`chatbot_searchlist-service`). 대화의 모델이 이미 그 자리다

### 대화로 시킬 일이 아니어서 안 지은 것

- 핵심기술 설정 · 해제(`A_CC_CORE_CONFIG` · `A_CC_CORE_RELEASE` · `popups/requestProtectedRelease.jsp`) · 집중 보호기술 · RAI — 보안 결재가
  붙는다. 손은 그런 문서를 「안 잰 꼴」로 멈춘다(`MEASURED_VARS`)
- 관리자 화면(`adminMain.jsp` · `AdminIfSystemMgmt-service` · `GetAdminManual-service` · 개인별 일괄 회수 · 정리 대상 비우기) — 관리자에게만
  보인다
- 승인 · 반려 · 복호화 승인(`A_CC_APPROVE_REJECT` …) · 사외 반출 요청 · 그룹사 유통 권한 회수 — 결재 흐름이다
- POSTalk · Teams 로 공유(`A_CC_SEND_POSTALK` · `A_CC_SEND_TEAMSBOT` · `grantCoresponUser.jsp?…posTalkSahredDoc=T`) — 받는 사람을 팝업에서
  사람이 고른다. 메일 · 권한 손과 겹친다
- 구글 공동작성 · 동시편집(`A_CC_START_GOOGLEDOCS` · `A_CC_COEDIT` · `A_CC_INSERT_COEDIT`) — 바깥 편집기 창을 연다
- 본문 첨부 이미지 임시 보관(`F_LIST_TEMP` · `TempFileDoc-service` · `TempDocCopy-service` · `F_LIST_TEMPDOC`) — 메일 본문 그림용이라 문서함
  문서가 아니다
- 개인 컨텐츠(`F_LIST_PERSONALFOLDER` · `A_PC_*` · `PersonalFolder-service`) — 위 「개인컨텐츠함」 줄
- 목록의 알림 설정 · 보기 설정 · 썸네일 · 팁(`goTip`) — 화면 모양이다

### 손이 안 부르는 화면 줄 — 빈자리가 아니다

- 전사 검색을 누르면 화면이 따로 부르는 검색 로그(`createESSearchLog`) — 결과에 안 든다. 손은 안 부르고, 그 꼴은 검색 POST 문이 막는다
- 우클릭 메뉴의 「편집 · 편집완료 · 컨텐츠 속성 · 보기」 — 손가락 `edit` · `checkin` · `doc`/`preview-props` · `open`/`read` 가 든다
- 「부서 컨텐츠함」 탭 하나로 부서 · 프로젝트 문서를 한꺼번에 — `search` 의 기본 범위(`s_deptCabinets`)가 같은 일이다
- 「최신버전으로 보기」 — `latest`
- 메인 화면 휴지통 고르기 칸(`F_LIST_RCB` option) — `list --box trash`

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
- 편집완료 창은 고친 문서를 저장해 닫으면 뜬다(저장과 닫기를 한 손이 이어 한 판) — 같은 앱에 사람의 다른 문서가 남아 앱이 떠 있어도
  뜬다. 고친 것 없이 닫으면 창 없이 잠금만 풀린다. 창 속은 웹 화면이고 판 라디오
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
- ⚠ 같은 서비스 모음에 올리기 요청 · 지우기 · 동시편집 취소가 있다 — 이 손은 짓지 않고, 지으려 하면 서버에 닿기 전에 막는다. 잰 꼴 밖의
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
