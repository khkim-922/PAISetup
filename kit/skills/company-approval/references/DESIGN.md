# 결재 손의 짜임

`scripts/` 를 고치기 전에 읽는다. 부르는 꼴 · 내는 것 · 종료 값은 `approval.py --help`(그 파일과 `approval_table.py` 의 표에서 선다)가,
손이 맞물리는 계약은 각 파일 머리말이 든다. 잰 사실은 `SOURCES.md` 다.

## 층

입구 `approval.py` 가 손가락 표로 인자를 세션 전에 거르고 세션을 받은 뒤 손 셋 가운데 하나에 넘긴다 — 읽기 `approval_read.py`(양식 ·
결재함 · 문서) · 쓰기 `approval_write.py`(미리 보기 · 임시저장 · 지우기) · 창 `approval_open.py`. 손 셋은 서로 안 부르고 입구도 안 싣는다 —
셋이 함께 쓰는 것은 아래 둘이 든다.

- `approval_table.py` — 출발 · 바꿀 것 · 끝 · 읽기 명령 · 결재함 · 보안 · 보존 표. 입구의 도움말과 손이 같은 표를 읽는다
- `iams.py` — 결재 앱에 닿는 바탕. 거래 · 화면 · 저장 짐 보내기, 문서 열쇠의 꼴 하나(`key_of` · `doc_of`), 앱 안 주소, 결재함의 기간과
  조회 칸, 부서 나무, 사람의 Edge 에 창을 띄우는 길(`browser` · `launch` — 띄우기는 형제 스킬 ep-login 의 `open_ordinary` 가 한다)

## 지키는 것

- **사람이 누를 단추는 손에 없다** — `iams.FORBIDDEN` 의 낱말이 든 주소는 앱에 닿기 전에 `Refused` 로 멈춘다. 상신 · 승인 · 반려 · 회수 ·
  접수 · 결재 메일 · 설정 저장이 그 자리다
- **미리 보기와 저장은 같은 판을 그린다** — 열쇠는 보낼 문서의 값(제목 · 본문 · 결재선 · 참조 · 배포 · 관련 문서 · 보안 · 보존)으로만
  짓는다. 다시 쓰기의 미리 보기는 [재사용] 창을 열 수 없어(여는 순간 임시저장이 선다) 보기 화면에 [재사용] 창이 하는 일(지금 없는 배포
  부서 빼기 · 다단결재 여부는 같은 양식의 새 문서 창에서)을 같게 해서 짓는다
- **다시 쓰기 창이 세운 임시저장은 말없이 안 남긴다** — 창의 씨앗 열쇠와 그 앞뒤 임시저장 목록으로 가린다. 저장이 안 선 길(앱의 거절 ·
  보내기 전 끊김 · 연 뒤의 멈춤)은 지우고, 섰는지 모르는 길(보낸 뒤 끊김 · 꼴 아닌 답)은 지우지 않고 그 열쇠를 답에 싣는다. 사람이 같은
  때 세웠을 수 있는 다른 줄은 안 지운다

<!-- drawn:piece-map · 손으로 고치지 않는다 — scripts/skill-map.py 가 짓는다 -->
| 조각 | 맡은 일 | 싣는 곁 조각 | 다른 스킬에서 싣는 것 |
|---|---|---|---|
| `approval.py` · 입구 | 전자결재 스킬의 얇은 명령 — 곁의 손으로 결재함을 읽고, 결재 문서를 임시저장까지 짓고, 그 문서 창을 사람의 Edge 에 띄운다. | `approval_table` · `iams` | ep-login 의 `ep_command` · `ep_session` |
| `approval_open.py` | 전자결재 스킬의 창 띄우기 손 — open. 문서 하나의 창 주소를 짓고 사람의 평소 Edge 에 새 탭으로 연다. | `approval_table` · `iams` | ep-login 의 `ep_command` |
| `approval_read.py` | 전자결재 스킬의 읽기 손 — forms · form · box · read. 결재 앱에 묻기만 하고 아무것도 바꾸지 않는다. | `approval_table` · `iams` | ep-login 의 `ep_command` |
| `approval_write.py` | 전자결재 스킬의 쓰기 손 — preview · save · discard. 출발 하나(새 문서 · 지난 문서 다시 쓰기 · 임시저장)의 화면 씨앗을 읽고, 바꿀 것을 넣은 판을 지어 보이고(열쇠), 보인 판 그대로일 때만 임시저장한 뒤 임시저장 목록에서 다시 읽어 맺는다. | `approval_table` · `iams` | ep-login 의 `ep_command` |
| `approval_table.py` | 전자결재 스킬의 표 — 출발 × 바꿀 것 × 끝(``STARTS`` · ``CHANGES`` · ``NOT_YET`` · ``ENDS``) · 읽기(``READS``) · 결재함(``BOXES``) · 화면의 코드 값(``GRADES`` · ``KEEPS``). 입구(approval.py)와 손 셋이 함께 읽는 한 자리라 입구 밑 · 손 밑에 산다 — 아무 손도 입구를 싣지 않는다. | — | ep-login 의 `ep_command` |
| `iams.py` | 사내 전자결재 앱(IAMS)의 손 — 손 셋(읽기 · 쓰기 · 창)의 바탕. EP 세션으로 결재 앱의 거래를 부르고, 화면을 받고, 임시저장 짐을 보낸다. | — | ep-login 의 `ep_command` · `ep_session` |

**입구에서 내려가는 나무** — 줄마다 조각과 그 머리말 첫 문장. 한 조각은 처음 닿은 자리에서만 펴고 다시 닿으면 `↑` 로 가리킨다. 클래스는 메서드를 그 아래에 든다. `←` 뒤는 그 조각을 부르는 다른 스킬이다. 인스턴스를 거친 부름은 이어지지 않는다.

- `main` — 명령 입구 — 인자를 읽고 앱 손을 실어 ``work`` 의 답을 JSON 하나로 찍는다(종료 값은 ``ep_command.finish``).
  - `parser` — 명령의 인자 표 — 하위 명령과 인자를 표(``STARTS`` · ``CHANGES`` · ``ENDS`` · ``READS`` · ``NOT_YET``)에서 세우고 지도 · 종료 값 범례를 --help 에 단다.
    - `finger_map` — --help 의 지도 — 표 다섯에서 짓는다.
  - `work` — 명령 하나 — 세션 앞 거름(쓰기 명령은 ``fingers``)을 지난 뒤 세션을 쥐고 그 명령의 손을 돈다.
    - `fingers` — 부른 명령의 출발을 고르고 표에 대 본다 — 아직 없는 손가락 · 출발에 없는 끝 · 출발에 없는 손가락 · 바꿀 것을 안 받는 끝 · 빠진 값을 차례로 거른다(저마다 그 일을 어디서 하는지 대며 Stop(인자)). 출발을 낸다.
      - `end_of` — 부른 명령이 맺는 끝 — preview 는 그 출발의 끝 가운데 바꿀 것을 받는 것(save)이다.
      - `iams.doc_of` — 문서 열쇠 → 앱이 문서를 받는 칸 넷. 꼴이 아니면 Stop(인자) — ``flag`` 는 그 값을 받은 인자의 이름.

**어디서도 안 닿는 조각** — 표 · 인스턴스를 거쳐 부르거나 아무도 안 부른다.

- `approval_open.row_in` — 함 하나의 목록에서 그 문서(열쇠 넷이 다 같은 줄)의 줄과 어디까지 봤나의 말 — 없으면 (None, 말). 기간을 꼭 받는 함은 그 함의 기본 기간만 본다.
  - `iams.period` — 함이 받는 기간 (앞 · 뒤 — 안 준 쪽은 None). 기간이 없는 함에 주면 Stop(인자). 꼭 받는 함은 안 준 쪽을 채운다(앞은 뒤에서 한 달 전 · 뒤는 오늘)고 6 달을 넘으면 Stop(인자). 꼭 받지 않는 함은 준 쪽만 — 안 준 쪽을 지어내지 않는다.
    - `months_after` — ``day`` 에서 ``months`` 달 뒤의 같은 날 — 그 달에 없는 날이면 그 달 끝날.
  - `iams.key_of` — 앱의 줄(목록 · 문서 화면 · 저장 답) → 문서 열쇠 ``APPR_DOC_ID.OVN.AVN.APVN``. 칸 하나라도 비면 None — 못 여는 열쇠를 안 낸다.
  - `iams.box_query` — 함 하나의 조회 칸(``paramMap``) — 화면의 ``onSearch`` 가 싣는 꼴 그대로(PROG_KIND · NO_WAIT · LEGACY_ID · 준 기간 · 제목).
- `approval_open.box_for` — 창을 고를 함 · 그 함의 줄 · 어디까지 봤나(함과 기간). ``--box`` 를 줬으면 그 함 — 함의 줄에 따라 창이 갈리는 함(``by_type`` — 결재하기의 참조 줄)이면 그 줄을 찾아 함께 낸다.
  - ↑ `row_in`
  - `iams.doc_row` — 문서 화면(보기 · 새 문서 · 임시저장 · 재사용 · 저장 답)이 심은 문서 한 줄(``apprDocDS``) — 없으면 None.
    - `dataset` — 화면에 박힌 데이터셋 ``name`` 의 줄들 — 없으면 빈 목록.
  - `iams.at` — 문서를 받는 주소 하나 — 열쇠 칸 넷을 주소에 싸서 넣는다.
- `approval_open.window` — 함 · 문서 열쇠 · 그 줄 → 앱의 문서 창 주소(앱 안 경로). 함이 없으면 보기만 하는 창.
  - ↑ `iams.at`
- `approval_open.open_doc` — open — 문서 하나의 창. 열쇠 → 함 고르기 → 창 주소 → SSO 넘김 주소 → 띄우기.
  - ↑ `iams.doc_of`
  - ↑ `box_for`
  - ↑ `window`
  - `iams.browser` — 앱 안 경로 → 사람의 브라우저가 여는 주소 — SSO 넘김 화면의 ``redir_url`` 로 싼 앱의 온 주소(이 손이 토큰을 받는 길과 같다).
  - `iams.launch` — 주소를 사람의 평소 Edge 에 새 탭으로 연다 — ep-login 이 EP 포털을 여는 그 손(``ep_session.open_ordinary``)으로. 어디에 열었나의 말을 낸다.
    - `sunk` — 시험장의 대역 — 띄우지 않고 ``sink`` 파일에 연 주소를 한 줄 적는다.
  - ↑ `iams.key_of`
- `approval_open.run` — 명령 하나 — open 의 손.
  - ↑ `open_doc`
- `approval_read.first` — 줄에서 ``keys`` 의 차례로 처음 찬 칸의 값.
- `approval_read.box_line` — 앱의 목록 줄 → 답의 줄 — 문서 열쇠 · 제목 · 요청자와 부서 · 때 · 상태 · 시스템과 업무 · 문서 번호. 빈 칸은 안 싣는다.
  - ↑ `iams.key_of`
  - ↑ `first`
  - `box` — box — 함 하나의 줄. 표에서 함을 고르고 → 기간 · 조회 칸 → 거래 하나 → 줄 꼴 → 답 크기에 맞춘다.
    - ↑ `iams.period`
    - ↑ `box_line`
    - ↑ `iams.box_query`
    - `again_args` — 이어 보는 부름의 인자 — 같은 함 · 같은 기간(기본 기간도 그날로 박는다 — 날이 바뀌어도 같은 줄이 이어진다 · 안 준 쪽은 안 싣는다) · 같은 제목 말.
    - `page_rows` — 답 ``out`` 의 ``rows`` 칸에 ``start`` 째 줄부터 ``OUT_BYTES`` 안에 드는 만큼 싣고, 남으면 ``more(다음 자리)`` 를 단다.
- `approval_read.jobs` — 새 문서 창의 업무들 — 「전체」(열쇠 없는 줄)는 뺀다.
- `approval_read.job_forms` — 업무 하나의 양식 줄 — FORM_ID · 이름 · 비고.
- `approval_read.forms` — forms — 업무마다 양식. 업무 목록 → 업무마다 양식 목록(새 문서 창의 두 칸과 같은 차례).
  - ↑ `job_forms`
  - ↑ `jobs`
- `approval_read.seed_of` — 화면에 박힌 문서 한 줄(``iams.doc_row``) — 없거나 양식(FORM_ID)이 비면 Stop(인자). ``what`` 은 무엇을 열었나(멈추는 말).
  - ↑ `iams.doc_row`
- `approval_read.person` — 결재선 · 참조의 한 사람 — 이름 · 부서 · 직책 · 구분 · 상태 · 때 · 의견 · 퇴직. 빈 칸은 안 싣는다.
  - `plain_value` — 남이 쓴 값 하나(XML 자료의 칸 · 결재 의견) → (보이는 글, 숨긴 덩이 수). HTML 조각이면 ``visible`` 이 풀고, 아니면 보이지 않는 문자만 걷는다.
    - `reader` — 형제 스킬 company-mail 의 ``visible`` — 본문 HTML 을 글자로 푸는 한 손(숨긴 글 · 스크립트 · 보이지 않는 문자를 걷고 표는 한 행 한 줄).
  - ↑ `first`
- `approval_read.line_of` — 결재선 — 차례(APPR_LINE_SEQ · 합의는 같은 차례의 APPR_LINE_ORDR)대로.
  - ↑ `person`
- `approval_read.defaults_of` — 문서 줄의 보안 등급 · 공개 · 보존 기한 — 코드와 사람 말.
- `approval_read.template_path` — 양식 틀을 남기는 파일 — 임시 폴더 아래 ``FORM_DIR/form_<FORM_ID>.html``.
- `approval_read.save_template` — 양식 틀 HTML 을 파일로 남기고 그 경로 — 쓰기 명령의 ``--body-file`` 은 이 파일을 고친 사본을 받는다.
  - ↑ `template_path`
- `approval_read.form` — form — 양식 하나의 틀. 새 문서 창(열어도 서버에 안 남는다) → 씨앗 · 다단 → 그 씨앗의 기본 결재선 · 본문 틀 → 틀을 파일로.
  - ↑ `seed_of`
  - `iams.details` — 문서 한 건의 결재선 · 의견 · 참조 · 배포 · 첨부 · 관련 문서 · 본문 — 문서 화면이 뜨며 보내는 거래 그대로(그 화면의 문서 줄을 싣는다).
  - `iams.cascade_of` — 그 업무가 결재자 여럿(다단)을 받나 — 문서 창(request.ex)이 결재선 지정 창에 넘기는 값. 화면에 그 값이 없으면 None. 보기 창(document.ex)은 이 값을 안 든다고 읽는다 — 다단을 가를 때는 같은 양식의 새 문서 창(``NEW_DOC`` — 서버에 안 남는다)을 연다.
  - ↑ `defaults_of`
  - ↑ `line_of`
  - ↑ `save_template`
  - `fit_preview` — 틀의 글자 앞 ``TEMPLATE_TEXT`` 자 — 넘으면 줄임표를 단다.
  - ↑ `reader`
- `approval_read.head_of` — 문서 화면의 문서 줄 → 답의 머리 — 열쇠 · 제목 · 상태 · 문서 번호 · 시스템과 업무 · 양식 · 보안 · 공개 · 보존.
  - ↑ `iams.key_of`
  - ↑ `defaults_of`
- `approval_read.ai_text` — 시스템 연계 문서의 XML 자료 → (「이름: 값」 줄, 숨긴 덩이 수). 값을 든 잎 칸마다 한 줄이고, 그 위 묶음(DS_…)이 바뀌면 머리 줄 하나 · 같은 묶음의 줄(row)마다 빈 줄로 가른다(깊이는 안 가린다). PC 주소 칸은 안 낸다.
  - ↑ `reader`
  - ↑ `plain_value`
- `approval_read.body_of` — 본문 → (글자, 숨긴 덩이 수). HTML · MIME 은 ``visible`` 이 풀고, AI 는 XML 자료를 줄로 푼다.
  - ↑ `ai_text`
  - ↑ `reader`
- `approval_read.attach_of` — 첨부 — 이름 · 확장자 · 크기만(받지 않는다).
  - ↑ `first`
- `approval_read.refs_of` — 참조 — 사람마다 이름 · 부서 · 직책 · 상태 · 때 · 참조 의견.
  - ↑ `person`
- `approval_read.dist_of` — 배포 — 부서 · 사람의 이름과 꼴.
- `approval_read.related_of` — 관련 문서 — 열쇠 · 제목 · 문서 번호 · 상태. 열쇠는 read · open 이 그대로 받는다.
  - `iams.ref_key_of` — 관련 문서 줄(REF_APPR_DOC_ID · REF_OVN · REF_AVN · REF_APVN) → 그 문서의 열쇠. 칸이 비면 None.
    - ↑ `key_of`
- `approval_read.read` — read — 문서 하나. 보기 창 화면(_MENU_ACTION_ NONE — 단추를 안 세우는 보기)에서 머리 → 결재선 · 의견 · 참조 · 배포 · 첨부 · 관련 문서 · 본문(거래 하나) → 본문을 글자로 → 답 크기에 맞춘다.
  - ↑ `iams.doc_of`
  - ↑ `seed_of`
  - ↑ `iams.at`
  - ↑ `iams.details`
  - ↑ `body_of`
  - ↑ `head_of`
  - ↑ `line_of`
  - ↑ `refs_of`
  - ↑ `dist_of`
  - ↑ `attach_of`
  - ↑ `related_of`
- `approval_read.run` — 명령 하나 — 그 명령의 손에 넘긴다(나눔만).
  - ↑ `box`
  - ↑ `form`
  - ↑ `forms`
  - ↑ `read`
- `approval_write.opt` — 부른 명령의 인자 하나 — 그 명령이 안 받는 인자(discard 는 바꿀 것을 안 받는다)는 None.
- `approval_write.draft_rows` — 임시저장 목록의 줄들 — 앱의 답 그대로.
- `approval_write.draft_row` — 임시저장 목록에서 그 열쇠(넷 다 같은)의 줄 — 없으면 None.
  - ↑ `draft_rows`
  - ↑ `iams.key_of`
- `approval_write.opened` — 출발의 화면 글자 — 새 문서는 양식의 새 창, 임시저장은 그 다시 열기 창, 지난 문서는 미리 보기면 그 문서의 보기 창 · 저장이면 [재사용] 창(``making`` — 서버에 임시저장이 선다 · 연 뒤 ``made`` 가 가린다). 문서가 없으면 None.
  - ↑ `opt`
  - ↑ `iams.doc_of`
  - ↑ `draft_row`
  - ↑ `iams.key_of`
  - ↑ `iams.at`
  - ↑ `iams.doc_row`
  - `reuse_blocks` — 지난 문서를 다시 쓸 수 있나 — 화면의 [재사용]이 막는 문서.
- `approval_write.live_dist` — 지난 문서의 배포처 → (지금 있는 것 · 뺀 부서 이름). [재사용] 창은 결재 앱의 지금 부서 나무에 없는 부서를 배포처에서 뺀다(잰 것 — 배포 부서 10 곳 가운데 나무에 없는 5 곳이 빠졌다) — 미리 보기가 같은 거르기를 해야 미리 보기와 저장의 열쇠가 같다.
  - `iams.live_depts` — 결재 앱이 지금 쓰는 부서 코드들 — 배포처 지정 창이 그리는 부서 나무 그대로.
- `approval_write.cascade_for` — 그 업무가 다단결재를 받나 — 새 문서 · 임시저장은 연 창(request.ex)의 값, 다시 쓰기는 그 양식의 새 문서 창(열어도 안 남는다 · WRITE-MAP 2 절)의 값. 미리 보기와 저장이 같은 자리에서 읽어 열쇠가 같다.
  - ↑ `iams.cascade_of`
- `approval_write.app_person` — 사번 하나 → 결재 앱의 사람 줄(결재선 지정 창의 사번 검색 그대로). 없으면 None.
- `approval_write.people_rows` — 사람 파일들 → (앱의 사람 줄들 · 막는 까닭 · 알릴 것). 한 사람은 한 번, 준 차례 그대로.
  - ↑ `app_person`
- `approval_write.person_line` — 앱의 사람 줄 → 결재선 · 참조 줄 하나(결재형태는 결재선 짓기가 매긴다).
- `approval_write.built_line` — 요청자 줄 + 결재자들(차례대로) + 합의자들 → 결재선 지정 창이 돌려주는 꼴. 마지막은 결재, 그 사이는 요청자와 같은 부서면 검토 · 남의 부서면 협조(창의 getAction 은 요청자의 부서와 견준다). 합의는 마지막 결재 바로 앞에 한 차례(SEQ)로 모여 선다(마지막이 결재가 아니면 창이 안 받는다). SEQ 는 0 부터, 합의는 같은 SEQ 에 ORDR 0, 1 …(창의 createReturnApprLine).
- `approval_write.requester_line` — 결재선의 요청자 줄 — 화면이 이름을 「이름[사번]」 으로 바꿔 싣는 꼴(잰 저장이 그렇게 실었다).
- `approval_write.with_doc` — 새로 지은 줄에 문서 열쇠(APPR_DOC_ID · OVN · AVN · APVN)를 단다 — 창이 요청자 줄의 값을 그대로 단다.
- `approval_write.body_of` — 본문 HTML — --body-file 을 주면 그 글, 아니면 출발의 본문(새 양식이면 틀). 화면처럼 「&quot;」 를 「'」 로 바꿔 싣는다.
  - ↑ `opt`
- `approval_write.link_rows` — 관련 문서로 줄 지난 문서들 → (연계문서 줄들 · 막는 까닭). 문서마다 그 보기 창의 씨앗에서 제목과 판을 읽는다.
  - ↑ `iams.doc_of`
  - ↑ `iams.doc_row`
  - ↑ `iams.at`
- `approval_write.joined` — 화면이 보이는 칸(배포처 · 연계문서)에 이어 적는 이름들 — 「, 」 로 잇는다.
- `approval_write.new_line` — 결재선을 다시 짓는다 — (줄들 · 막는 까닭 · 알릴 것). --approvers 를 주면 결재자를 통째로 갈고, 안 주면 출발의 결재자들 그대로. --agree 를 주면 합의를 갈고, 안 주면 출발의 합의 그대로. ``fresh_requester`` 면 요청자 줄을 결재 앱의 지금 내 줄로 다시 받는다 — 지난 문서의 결재선은 그때의 부서 · 직급을 든다.
  - ↑ `people_rows`
  - ↑ `opt`
  - ↑ `app_person`
  - ↑ `person_line`
  - ↑ `built_line`
- `approval_write.grade_code` — 직급 코드(「P4」 · 「E7」 · 「P10」) → (직군 글자, 숫자). 비었거나 꼴이 아니면 None.
- `approval_write.self_approval` — 화면의 selfApproval — 요청자가 결재선 뒤에 또 서면 막는다.
  - ↑ `grade_code`
- `approval_write.plain` — 화면이 직책 없음(「일반」)으로 읽는 직책인가.
- `approval_write.position_check` — 화면의 positionCodeCheck — 결재(APPROVAL) 줄마다 요청자와 직군 · 직급 · 직책을 견준다.
  - ↑ `grade_code`
  - ↑ `plain`
- `approval_write.level_order` — 결재선 지정 창의 checkApprovalLevel — 같은 부서의 앞줄보다 뒷줄의 결재 단계 숫자가 크면 막는다(단계가 빈 줄은 안 본다).
  - `level` — 결재 단계 — 숫자가 아니거나 비었으면 None(화면도 그 줄은 안 본다).
- `approval_write.line_blocks` — 결재선이 화면의 규칙에 걸리나 — (막는 까닭 · 알릴 것).
  - ↑ `self_approval`
  - ↑ `position_check`
  - ↑ `level_order`
  - `gone` — 그 문서가 없다는 답.
- `approval_write.unmeasured_notes` — 받되 회사에서 안 잰 손가락을 받았으면 그렇다고 알린다 — 표(``approval_table.CHANGES``)의 △ 그대로.
- `approval_write.body_text` — 본문 HTML 의 앞 글자 — 사람에게 보일 만큼만, 태그를 걷고 빈칸을 접는다.
- `approval_write.who` — 결재선 · 참조 줄 하나의 사람 말 — 결재형태 · 이름 · 부서 · 직급 · 직책.
  - ↑ `plain`
- `approval_write.plan` — 출발의 화면(``opened`` 가 연 것)에 바꿀 것을 넣은 문서 한 건의 꼴 · 막는 까닭 · 알릴 것 · 열쇠, 그리고 앱에 보낼 짐(``payload``). 바꾸지 않는다.
  - ↑ `iams.doc_row`
  - ↑ `iams.details`
  - ↑ `reuse_blocks`
  - ↑ `unmeasured_notes`
  - ↑ `opt`
  - ↑ `new_line`
  - ↑ `people_rows`
  - ↑ `person_line`
  - ↑ `link_rows`
  - ↑ `live_dist`
  - ↑ `body_of`
  - ↑ `joined`
  - ↑ `line_blocks`
  - ↑ `cascade_for`
  - ↑ `with_doc`
  - ↑ `requester_line`
  - `source_of` — 출발을 고른 값 — 양식 · 지난 문서 · 임시저장의 id(사람이 준 그대로).
    - ↑ `opt`
  - ↑ `body_text`
  - ↑ `who`
- `approval_write.shown` — 사람에게 보일 판 — 앱에 보낼 짐과 지은 임시저장 표시는 뺀다.
- `approval_write.saved` — 짐 하나를 임시저장한다 — 답 화면의 문서 줄(새 APPR_DOC_ID · 판). 앱이 안 받았다고 말하면 ``iams.Rejected``, 답 화면에 열쇠가 없으면 ``iams.AppError``(섰는지 모른다).
  - ↑ `iams.doc_row`
  - ↑ `iams.key_of`
  - `iams.AppError` — 결재 앱의 손이 낸 실패 — 앱이 거절했거나 답이 꼴이 아니거나 앱에 못 닿았다.
- `approval_write.settled` — 저장한 뒤의 끝 — 임시저장 목록에서 그 문서를 다시 읽는다.
  - ↑ `draft_row`
- `approval_write.shown_window` — 임시저장한 문서의 고치는 창을 사람의 Edge 에 띄운다(open --box drafts 와 같은 창) — 창 주소 · 사람의 Edge 가 여는 주소 · 어디에 열었나. 못 띄우면 그 까닭과 주소만 낸다 — 저장은 이미 섰다.
  - ↑ `iams.at`
  - ↑ `iams.doc_of`
  - ↑ `iams.browser`
  - ↑ `iams.launch`
- `approval_write.discarded` — 임시저장 한 건을 지운다 — 목록 줄 그대로에 지움 표시를 달아 보내고, 목록에서 사라졌나를 낸다.
  - ↑ `draft_row`
  - ↑ `iams.key_of`
- `approval_write.made_by` — [재사용] 창이 세운 임시저장 — (거둘 줄 · 거두지 않고 알릴 열쇠). 거둘 줄은 창의 씨앗(``page`` 의 문서 줄 — 지난 문서 ``source`` 와 다른 열쇠)과 같은 열쇠의 목록 줄 하나뿐이다.
  - ↑ `iams.key_of`
  - ↑ `iams.doc_row`
  - ↑ `draft_rows`
- `approval_write.undo_made` — 다시 쓰기 창이 세운 임시저장을 거둔다 — 사람에게 할 말(``cleanup``)과 남은 열쇠(``left`` — 못 지웠거나 거두지 않고 알린 것). 거둘 것도 알릴 것도 없으면 빈 dict. 목록에서 이미 사라진 줄은 지웠다고 하지 않는다.
  - ↑ `iams.key_of`
  - ↑ `draft_row`
  - ↑ `discarded`
  - `said` — 사람에게 덧붙일 말 한 칸 — 없으면 빈 dict.
- `approval_write.run` — 명령 하나 — preview 는 판을 보이고, save 는 보인 판 그대로일 때만 임시저장해 맺고 창을 띄우고, discard 는 보인 임시저장을 지운다.
  - `discard` — 임시저장 지우기 — 목록에서 그 줄을 읽어 preview --draft 와 같은 판의 열쇠를 견주고, 같을 때만 지운다.
    - ↑ `iams.key_of`
    - ↑ `iams.doc_of`
    - ↑ `opt`
    - ↑ `draft_row`
    - ↑ `gone`
    - ↑ `plan`
    - ↑ `opened`
    - `stale` — 보인 판과 지금 판이 다르다는 멈춤(종료 4) — 지금 판의 열쇠와 막는 까닭을 말에 싣는다.
    - ↑ `discarded`
    - `iams.SessionExpired` — 사내 세션이 끊겼거나 앱이 안 들였다 — 받는 손을 다시 부를 자리다.
    - ↑ `iams.AppError`
  - ↑ `plan`
  - ↑ `opened`
  - ↑ `gone`
  - ↑ `shown`
  - `save` — save — 출발 열기(다시 쓰기는 연 창의 씨앗과 그 앞뒤 임시저장 목록으로 창이 세운 것을 가린다) → 판 → 열쇠 견주기 → 임시저장 → 맺기 → 창. 창이 세운 임시저장은 저장이 서지 않은 모든 길(멈춤 · 끊김 포함)에서 거두고, 못 거뒀거나 섰는지 모르면 그 열쇠를 답에 싣는다.
    - ↑ `iams.key_of`
    - ↑ `iams.doc_of`
    - ↑ `opt`
    - ↑ `draft_rows`
    - ↑ `opened`
    - ↑ `made_by`
    - ↑ `plan`
    - ↑ `gone`
    - ↑ `undo_made`
    - ↑ `stale`
    - `left_behind` — 저장 앞에서 멈췄는데 다시 쓰기 창이 세운 임시저장을 거뒀거나 못 거뒀다 — 그 말을 덧붙인 멈춤. 멈춤(``Stop``)은 그 값 그대로, 세션이 끊겼으면 종료 3, 그 밖은 도구 고장(종료 1).
      - ↑ `iams.SessionExpired`
      - `iams.SessionMissing` — 세션 파일이 없거나 못 읽는다 — 받는 손(스킬 ep-login)을 부를 자리다.
    - `after_save` — 임시저장을 보내고 맺고 창을 띄운다.
      - ↑ `iams.key_of`
      - ↑ `saved`
      - `iams.Rejected` — 앱이 답 화면에서 그 짐을 안 받았다고 말했다(``_FLAG_`` 가 「S」 가 아니다) — 서버에 아무것도 안 섰다.
      - ↑ `undo_made`
      - ↑ `left_behind`
      - ↑ `settled`
      - ↑ `shown_window`
- `iams.Refused` — 이 손이 안 부르는 자리라 묻지 않았다(``FORBIDDEN``).
- `iams.uri_component` — 화면의 ``encodeURIComponent`` 와 같은 글자 — dict · list 는 JSON 으로 옮긴 뒤 싼다.
- `iams.decoded` — 앱의 답 바이트 → 글자 — 거래 · 화면은 utf-8 이고, 옛 화면 몇은 cp949 다.
- `iams.App` — 결재 앱 한 판 — 부를 때마다 SSO 토큰을 새로 받아 거래 · 화면 · 임시저장을 묻는다.
  - ↑ `SessionMissing`
  - `App._token` — ``path`` 로 넘기는 SSO 토큰 칸(``SSO_FIELDS``) — 토큰이 없으면 SessionExpired. 있다고 세션이 산 것은 아니다(``_answer`` 가 가린다).
    - ↑ `browser`
    - ↑ `decoded`
    - ↑ `SessionExpired`
    - ↑ `AppError`
  - `App._answer` — 요청 하나를 보내 답 바이트 — 앱이 오류 화면으로 넘기면 그 말로 SessionExpired(끊긴 세션) · AppError(그 밖), 거절 · 못 닿음은 AppError.
    - ↑ `SessionExpired`
    - ↑ `AppError`
  - `App._post` — 토큰 칸과 ``fields``(값은 ``uri_component`` 로 싼다)를 폼 POST 로 — 안 부르는 자리면 묻기 전에 Refused.
    - ↑ `Refused`
    - ↑ `App._token`
    - ↑ `uri_component`
    - ↑ `App._answer`
  - `App.tx` — 거래 하나 — ``fields`` 는 칸 이름 → 값(조회 조건 ``paramMap`` · 데이터셋 ``…VO``). 답 JSON. JSON 이 아니면 AppError.
    - ↑ `App._post`
    - ↑ `AppError`
    - ↑ `decoded`
  - `App.page` — 화면 하나 — 사람의 브라우저가 여는 꼴(폼 POST)로 받은 글자.
    - ↑ `decoded`
    - ↑ `App._post`
  - `App.save` — [임시저장] 한 판 — ``datasets``(``apprDocVO`` · ``apprLineVO`` · …, 한 줄이면 dict · 여럿이면 list, 빈 것은 안 준다)를 화면처럼 multipart 로 ``SAVE_PATH`` 에 보낸다.
    - ↑ `uri_component`
    - ↑ `App._token`
    - ↑ `AppError`
    - ↑ `decoded`
    - ↑ `App._answer`
    - ↑ `Rejected`
<!-- /drawn:piece-map -->
