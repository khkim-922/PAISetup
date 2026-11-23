# ECM 손의 짜임 — 차례와 막는 까닭

`scripts/` 의 손을 고치기 전에 읽는다. 부르는 꼴 · 내는 것 · 종료 값은 `ecm.py` 머리말과 `--help` 가, 서버의 주소와 꼴은 `SOURCES.md`
「사내 ECM 에서 잰 것」이, 파일마다 무엇을 드나는 `scripts/README.md` 가 든다.

## 조각의 지도

부르는 방향은 위에서 아래 하나다 — 층은 이렇게 선다.

- `company_ecm.py` — 대화의 명령. 인자를 한 번 가리고 세션을 맞춘 뒤 `ecm.run` 을 부른다
- `ecm.py` — 입구(`checked_args` · `run` · `main`) · 손가락의 표 · 명령의 몸 · 패스마다의 일 손(보기 · 편집 · 등록 · 권한 · 속성 ·
  편집취소). 남이 싣는 이름(서버 · 에이전트 · 바탕의 것까지)을 이 파일 이름으로 그대로 내놓는다
- `ecm_server.py` · `ecm_agent.py` — 서버 이음 · 에이전트 이음. 서로 안 싣는다
- `ecm_base.py` — 위가 다 함께 기대는 바탕: 이름 붙은 값 · 예외 · 기록의 꼴 · 서버 없이 값을 가리는 손가락. 형제 스킬 ep-login 의
  종료 값 · ECM 주소와 drm-office-read 의 받는 자리 값을 여기서 싣는다
- `default_app.py` 와 PowerShell 다섯은 따로 선다(일 손이 싣거나 프로세스로 띄운다)

아래는 코드에서 뽑은 지도다 — 줄의 문장은 그 조각 머리말의 첫 문장이라, 문장을 고치려면 머리말을 고치고 다시 짓는다. 입구
`company_ecm.main` 은 세션을 맞춘 뒤 `ecm.run` 으로 이어진다. PowerShell 손은 이 지도에 안 선다 — 이 손은 파이썬만 읽는다.

<!-- drawn:piece-map · 손으로 고치지 않는다 — scripts/skill-map.py 가 짓는다 -->
| 조각 | 맡은 일 | 싣는 곁 조각 | 다른 스킬에서 싣는 것 |
|---|---|---|---|
| `company_ecm.py` · 입구 | 스킬 company-ecm 의 얇은 명령 — 스킬 ep-login 의 붙는 손으로 사내 세션을 맞춘 뒤, 곁의 ECM 손(``ecm.py``)을 그대로 부른다. | `ecm` | — |
| `ecm.py` · 입구 | 사내 문서함(ECM)에서 문서를 찾고 읽고, 사람이 확인한 한 편은 편집해 다음 판으로 올리거나 새 문서로 올리고, 문서의 권한을 주고 거두는 손. 표준 라이브러리와 곁의 ``ecm_base.py``(값 · 예외 · 기록의 꼴) · ``ecm_server.py``(서버 이음) · ``ecm_agent.py``(에이전트 이음) · ``default_app.py`` · ``office_doc.ps1``(``close_view.ps1`` · ``change_doc.ps1`` 이 싣는다) · ``close_acrobat.ps1`` · ``checkin_window.ps1``, 형제 스킬 ep-login 의 ``ep_session.py``(스킬 홈에 나란히 깔린 ``../../ep-login/scripts/``)를 쓴다. | `default_app` · `ecm_agent` · `ecm_base` · `ecm_server` | ep-login 의 `ep_command` · `ep_session` |
| `ecm_agent.py` | PC 의 ECM 에이전트와 주고받는 손 — 웹소켓 한 줄로 받기 · 편집취소 · 올림을 맡기고 받은 파일이 다 쓰이기를 기다린다. | `ecm_base` | — |
| `ecm_server.py` | ECM 서버 하나와 주고받는 손 — 요청마다 서버에 닿기 전에 잰 꼴에 대어 막고(읽기 ``guard`` · 바꾸는 GET ``_guard_edit`` · POST ``POST_SHAPES``), 보내고, 답을 푼다. | `ecm_base` | ep-login 의 `ep_session` |
| `default_app.py` | 확장자의 기본 앱(Windows 「항상 이 앱 사용」)을 보고, 비어 있을 때만 깔린 앱으로 채우는 손 — 표준 라이브러리만 쓰는 파일 하나. | — | — |
| `ecm_base.py` | 문서함 손의 바탕 — 서버 · 에이전트 · 패스 · 명령이 함께 기대는 이름 붙은 값 · 예외 · 기록의 꼴과 서버 없이 값을 가리는 손가락을 든다. | — | ep-login 의 `ep_command` · `ep_session` |

**입구에서 내려가는 나무** — 줄마다 조각과 그 머리말 첫 문장. 한 조각은 처음 닿은 자리에서만 펴고 다시 닿으면 `↑` 로 가리킨다. 클래스는 메서드를 그 아래에 든다. `←` 뒤는 그 조각을 부르는 다른 스킬이다. 인스턴스를 거친 부름은 이어지지 않는다.

- `main` — 명령 한 판 — 인자를 한 번 가리고, 세션이 드는 줄이면 받는 손의 바퀴(``session_first``)로 세션을 맞춰 ``ecm.run`` 을 돈다.
  - `ecm.checked_args` — 명령줄을 풀고 서버 없이 가릴 수 있는 값을 가린 인자를 낸다 — ``--help`` · 틀린 인자는 ``SystemExit``, 틀린 값은 ``REPORTED`` 가운데 하나로 멈춘다.
    - `parser` — 명령줄 — 손가락의 표에서 짓는다.
      - `help_map` — --help 의 지도 — 패스마다 출발 → 손가락 → 끝 · 지키는 선, 편집 패스의 바꿀 것, 안 하는 것, 종료 값. 표에서 짓는다.
        - `Pass` — 화면 패스 하나 — 사람이 웹 앱에서 화면 하나를 열고 칸을 바꾸고 끝 단추를 누르는 단위.
        - `Finger` — 손가락 하나 — 명령 하나다.
        - `_pre_change` — change 의 값 — (바꿀 것, 그 문서를 편집으로 받은 파일). cmd_change 도 이것으로 받는다.
          - `changes_of` — 명령줄의 바꿀 것 → ``Changes``. 조각 파일은 ``ep_command.text_file`` 로 읽는다 — UTF-8 · 앞의 BOM 과 끝 줄바꿈은 걷는다(파워셸이 붙인 BOM 이 새 판의 글에 안 보이는 글자로 실리지 않게). 없거나 UTF-8 이 아니면 ``ArgsError``.
            - `ecm_base.ArgsError` — 준 값이 틀렸거나 아무것도 가리키지 않는다 — 아무것도 안 건드렸다.
            - `Changes` — 편집 패스의 바꿀 것 — 한 부름에 아무 조합으로 묶는다.
              - `Changes.empty` — 고칠 조각도 넣을 파일도 없나.
          - ↑ `ecm_base.ArgsError`
          - `check_change_shape` — 바꿀 것 가운데 문서의 꼴을 몰라도 가릴 수 있는 것 — 빈 조각 · 줄바꿈 · 같은 글 · 조각끼리 겹침 · 넣을 파일이 있나 · 자리 (``--after``). 서버 · 문서 없이 돌아 명령줄이 세션보다 먼저 부른다(``precheck``). 못 할 까닭이 있으면 ``ArgsError``.
            - ↑ `ecm_base.ArgsError`
          - `checkout_file` — 에이전트가 그 문서를 편집으로 받은 파일인가 — <받는 자리>\<계정>\CHECKOUT\<시각 번호>\<이름에 그 문서 열쇠>. 아니면 ``EcmError``. 편집 패스는 여러 부름을 건너므로 모델이 이 경로를 들고 다닌다 — 손이 부를 때마다 다시 잰다.
            - `ecm_base.agent_docs_root` — 에이전트가 받은 파일을 두는 자리 — 환경변수 ``ECM_DOCS_ROOT``, 비었으면 ``DEFAULT_DOCS_ROOT``(``DRM_PLACES_FILE``). 스킬 drm-office-read 의 읽는 부품(``Get-EcmDocsRoot``)과 DRM 길잡이 훅이 같은 차례 · 같은 값 파일로 읽어 그 자리 밑의 파일을 등급 문 밖에서 안 연다.
            - ↑ `ecm_base.ArgsError`
            - `ecm_base.EcmError` — ECM 일을 못 했다.
          - `ecm_base._object_id` — 문서 열쇠(16 자리 hex)의 꼴을 가려 다듬은 값을 낸다 — 아니면 ``ArgsError``.
            - ↑ `ArgsError`
        - `_pre_edit` — edit 의 바꿀 것을 서버 없이 가린다(``check_change_shape``).
          - ↑ `check_change_shape`
          - ↑ `changes_of`
        - `_pre_find_folder` — find-folder 의 이름을 서버 없이 가린다 — 두 글자부터.
          - `ecm_base.folder_name` — 폴더 이름 찾기에 줄 이름(일부) — 화면처럼 두 글자부터. 다듬은 이름을 낸다.
            - ↑ `ArgsError`
        - `_pre_folders` — folders 의 값을 서버 없이 가린다 — all 이나 ``--find`` 와 ``--parent`` 를 함께 주면 ``ArgsError``.
          - `_no_all` — 문서함 하나에서만 하는 명령에 all 을 주면 ``ArgsError``.
            - ↑ `ecm_base.ArgsError`
          - ↑ `ecm_base.ArgsError`
        - `_pre_list` — list · count 의 값을 서버 없이 가린다 — 왼쪽 메뉴 목록과 자리 · all 과 폴더 · 문서함 안 폴더 열쇠의 꼴.
          - `ecm_base.refuse_box_with_place` — 왼쪽 메뉴의 목록(``--box``)은 문서함 · 폴더와 함께 안 받는다 — 그 목록은 문서함을 가리지 않는다.
            - ↑ `ArgsError`
          - ↑ `ecm_base.ArgsError`
          - `ecm_base.folder_key` — 폴더 열쇠(fdr…)의 꼴을 가린다 — 아니면 ``ArgsError``.
            - ↑ `ArgsError`
        - `_pre_props` — 속성 바꾸기의 값을 서버 없이 가린다 — 함께 못 주는 깃발 · 바꿀 것 없음 · 이름 · 태그 · 완료일의 꼴, 못 쓸 값이면 ``ArgsError``.
          - ↑ `ecm_base.ArgsError`
          - `ecm_base.check_title` — 등록할 이름(확장자 뺀) — 화면의 addFile 이 막는 것을 먼저 막는다.
            - ↑ `ArgsError`
          - `check_tags` — 태그 말들을 서버 없이 가린다 — 화면의 태그 칸과 같다(한글 · 영문 · 숫자 · 겹침 없음). 앞의 # 는 뗀다.
            - ↑ `ecm_base.ArgsError`
          - `check_due` — 완료일 — YYYY-MM-DD. 없애는 길은 없다 — 저장 몸에 화면의 「없음」(0001/01/01)을 실으면 서버는 그 칸을 안 바꾼다(쟀다).
            - ↑ `ecm_base.ArgsError`
        - `_pre_register` — 등록 · 등록 미리 보기의 값을 서버 없이 가린다 — all · 파일 · 보안 짝 · 폴더 · 이름(``register_inputs``).
          - ↑ `_no_all`
          - `register_inputs` — 등록할 값 가운데 서버 없이 가릴 수 있는 것 — 파일 · 보안 짝 · 폴더를 하나로 줬나 · 폴더 열쇠의 꼴 · 확장자 · 이름. (풀어 둔 파일 경로, 확장자, 다듬은 이름)을 낸다.
            - ↑ `ecm_base.ArgsError`
            - ↑ `ecm_base.folder_key`
            - ↑ `ecm_base.check_title`
        - `_pre_search` — search 의 칸과 쪽을 서버 없이 가린다.
          - `ecm_base.check_search` — 전사 검색의 칸을 서버 없이 가린다 — 못 쓸 값이면 ``ArgsError``. 다 빈 판 · 꼴이 깨지는 글자 · 날짜 꼴 · 등급 · 범위.
            - ↑ `ArgsError`
          - `_search_query` — 명령줄 → 전사 검색의 칸 — 자리 낱말과 ``--title`` 을 제목 낱말 하나로 잇는다.
            - `ecm_base.SearchQuery` — 전사 검색의 칸 — 상세검색 화면의 칸과 같다.
          - `ecm_base.check_search_page` — 전사 검색의 쪽 번호 · 쪽마다 건수를 가린다 — 범위 밖이면 ``ArgsError``.
            - ↑ `ArgsError`
        - `access_specs` — 명령줄의 권한 말과 사람 파일을 모아(``gather_access_specs``) 서버 없이 가린다(``check_access_specs``). 세션보다 먼저 돌고 (``precheck``), 미리 보기 · 보내기가 같은 것을 다시 모은다 — 손가락 표의 몸은 세션 전 가리기 없이도 홀로 선다.
          - `gather_access_specs` — 명령줄의 권한 말과 사람 파일(``--<칸>-file`` · 주소록의 사람 파일)을 말 목록 · 「파일:줄」 · 파일마다의 한 줄로 모은다 — 사람 파일을 못 읽거나 칸 짝이 틀리거나 아무 말도 없으면 ``ArgsError``.
            - `read_people_file` — 사람 파일 하나 → [(「파일:줄」, 사람 말)] — 한 줄에 사람 말 하나(「이름」 · 「이름/메일ID」 · 「이름/메일 주소」 · 「org:…」), ``PEOPLE_COMMENT`` 뒤와 빈 줄은 버린다.
              - ↑ `ecm_base.ArgsError`
            - ↑ `ecm_base.ArgsError`
            - `people_specs` — 주소록의 사람 파일(people.json — ``ep_command.people_of``) → [(「파일:몇째」, 사람 말)]. ECM 은 이름으로만 사람을 찾으니 말은 「이름/메일ID」(없으면 「이름/메일 주소」 · 「이름」)다 — 동명이인은 메일 쪽으로 가른다.
              - ↑ `ecm_base.ArgsError`
            - `AccessSpecs` — 명령줄 · 사람 파일에서 모은 권한 말 — ``grant`` 는 (edit|copy|read, 사람 말), ``origins`` 는 파일에서 온 말 → 「파일:줄」, ``files`` 는 사람에게 보일 파일마다의 한 줄.
          - `check_access_specs` — 모은 권한 말과 거둘 말을 서버 없이 가린다 — 못 쓸 말(두 글자가 안 되는 이름 · 주소만 준 말)은 「파일:줄」 과 함께 다 대며 ``ArgsError``.
            - `ecm_base.check_person_spec` — 권한에 줄 사람 말 하나를 서버 없이 가린다 — 「org:코드|부서 이름」 · 「이름[/메일ID|/메일 주소]」. 이름 없이 주소만 준 말은 ECM 이 못 찾는다(이름으로만 찾는다). 못 쓸 말이면 ``ArgsError``.
              - `spec_kind` — 사람 말 하나를 (갈래, 값)으로 가른다 — 「org:」 뒤가 부서 코드면 ``SPEC_CODE``, 부서 이름이면 ``SPEC_ORGAN``(값은 「org:」 를 뗀 글), 아니면 ``SPEC_PERSON``(값은 말 그대로).
              - `organ_name` — 부서 찾기에 줄 이름(일부) — 두 글자부터. 다듬은 이름을 낸다.
                - ↑ `ArgsError`
              - ↑ `ArgsError`
              - `person_name` — 사람 찾기에 줄 이름 — 화면의 checkValue 처럼 두 글자부터. 다듬은 이름을 낸다.
                - ↑ `ArgsError`
            - ↑ `ecm_base.ArgsError`
        - `checkin_inputs` — 올리기 · 그 미리 보기의 값 가운데 서버 없이 가릴 수 있는 것 — 문서 열쇠 · 수정 내용 · 그 문서를 편집으로 받은 파일인가. (열쇠, 다듬은 수정 내용, 받은 파일)을 낸다.
          - ↑ `ecm_base._object_id`
          - ↑ `ecm_base.ArgsError`
          - ↑ `checkout_file`
        - `cmd_access` — 문서의 권한 명단을 읽어 말한다.
          - `_print_grants` — 권한 명단의 말 — 편집 · 복사 · 읽기 역할마다 사람 수와 사람, 그 밖의 역할은 줄마다.
        - `cmd_apply_access` — 미리 본 그대로 권한을 바꾸고 다시 읽은 명단을 말한다.
          - `_access_plan` — 명령줄 · 사람 파일의 권한 말로 권한 한 판을 짓는다 — 사람 파일마다의 한 줄을 덧붙인 말 앞에 단다.
            - ↑ `access_specs`
            - `plan_access` — 권한 한 판을 짓는다 — 서버를 바꾸지 않는다.
              - ↑ `ecm_base._object_id`
              - `document_gate` — 속성 화면의 저장을 손으로 보내도 되는 꼴의 문서인가를 가르고 (속성 화면, 지금 권한 명단)을 낸다 — 이 손이 잰 꼴이 아니면 그 까닭과 ``what``(권한 · 속성)을 대며 ``EcmError``. 권한 · 속성 패스의 미리 보기와 보내기가 다 이 문을 지난다.
                - ↑ `ecm_base.EcmError`
              - `refuse_unhandled_grants` — 지금 명단이 이 손이 다루는 꼴인가 — 권한 셋 밖의 역할이 걸렸거나 한 사람에게 역할이 둘 넘으면 사람이 화면에서 하라고 ``EcmError``.
                - `ecm_base.outside_roles` — 권한 셋(편집 · 복사 · 읽기)의 사람 줄 밖의 역할 — 이 손이 주고 거두지 않고, 그런 줄이 걸린 문서의 저장은 안 잰 꼴이다.
                - ↑ `ecm_base.EcmError`
              - `AccessDraft` — 권한 명단의 뒤 모습을 짓는 판(지금 모습) — 지금 명단 · 지킬 줄에서 시작해 말마다 얹고 빼고, 사람에게 보일 말을 모은다.
                - `AccessDraft.start` — 지금 명단에서 판을 연다 — ``clear`` 면 지킬 줄만 남기고 시작한다.
                - `AccessDraft.put` — 사람들을 그 칸으로 뒤 명단에 얹는다 — 지킬 줄은 건너뛰고(말을 남긴다), 같은 층에서 이미 다른 칸을 받은 사람이면 멈춘다.
                  - `is_org_spec` — 사람 말이 조직(「org:」)을 짚었나 — 갈래는 ``spec_kind`` 가 가른다.
                    - ↑ `ecm_base.spec_kind`
                  - ↑ `ecm_base.ArgsError`
                  - `_grant_of` — ECM 사람 하나에 역할을 붙인 사람 권한 줄(``Grant``).
                    - `ecm_base.Grant` — 문서에 걸린 역할 하나 — ``role`` 은 R(편집/복사/읽기/인쇄) · S(복사/읽기/인쇄) · V(읽기/인쇄) 따위, ``id`` 는 사람 열쇠(usr…).
                      - `Grant.label` — 사람이 읽는 꼴 — 「이름/메일ID · 부서」.
                - `AccessDraft.take` — 뒤 명단에서 그 사람들을 뺀다 — 조직으로 들어갈 참이던 사람을 사람으로 빼면 그렇다고 말을 남긴다.
                - `AccessDraft.named` — 「이름」 · 「이름/메일」 로 지금 · 뒤 명단에서 꼭 한 사람을 고른다 — 여럿 · 없음 · 지킬 줄이면 ``ArgsError``.
                  - `same_mail` — 사람 말의 메일 칸(「메일ID」 · 「메일ID@도메인」)이 ECM 사람 줄의 메일 칸과 같은 사람인가 — ECM 의 사람 줄은 메일 ID(@ 앞)를 든다(``Grant.email``). 사람 줄이 온 주소를 들면 온 주소끼리, ID 만 들면 @ 앞끼리 견준다(대소문자는 안 가린다).
                  - ↑ `ecm_base.ArgsError`
                - `AccessDraft.note_staying` — 준 칸에 이미 든 사람을 한 줄로 말에 더한다(그대로 둔다).
                - `AccessDraft.changes` — 지금 명단과 뒤 명단의 더함 · 뺌 · 옮김(앞, 뒤).
              - `kept_ids` — 이 손이 칸을 안 바꾸는 줄 — 소유자 · 본인. 공동 편집자인 본인이 제 편집 권한을 지우면 되돌릴 길이 없다.
              - `ecm_base.Person` — ECM 이 아는 사람 하나 — ``id`` 가 권한 칸에 드는 열쇠다.
                - `Person.label` — 사람이 읽는 꼴 — 「이름/메일ID · 부서 · 직위」.
              - ↑ `is_org_spec`
              - `try_spec` — 말 하나를 풀다 멈추면 그 까닭을(온 자리 「파일:줄」 을 앞에 붙여) 모아 두고 다음 말로 간다 — 다 모은 뒤 한 번에 멈춘다.
                - `run` — 가린 인자로 그 줄의 손을 부르고 멈춘 까닭을 종료 값으로 옮긴다 — 세션이 드는 줄이면 서버 하나를 세운다.
                  - ↑ `Finger`
                  - ↑ `_pre_change`
                  - ↑ `_pre_edit`
                  - ↑ `_pre_find_folder`
                  - ↑ `_pre_folders`
                  - ↑ `_pre_list`
                  - ↑ `_pre_props`
                  - ↑ `_pre_register`
                  - ↑ `_pre_search`
                  - ↑ `access_specs`
                  - ↑ `checkin_inputs`
                  - ↑ `cmd_access`
                  - ↑ `cmd_apply_access`
                  - `cmd_apply_props` — 미리 본 그대로 속성을 바꾸고 다시 읽은 속성을 말한다.
                    - `plan_props` — 속성 한 판을 짓는다 — 서버를 바꾸지 않는다.
                      - ↑ `ecm_base._object_id`
                      - `_props_gate` — 속성을 손으로 바꿔도 되는 문서인가 — 권한 패스와 같은 문(``document_gate``)에 권한 셋 밖의 역할을 더 막는다.
                        - ↑ `document_gate`
                        - ↑ `ecm_base.outside_roles`
                        - ↑ `ecm_base.EcmError`
                      - `_props_now` — 속성 화면이 든 지금 이름 · 태그 · 완료일. 완료일은 숨은 칸 ``MS_DUE_DATE``(YYYY-MM-DD)다 — 고르는 칸 ``ecm_EndDate`` 는 화면이 늘 ``0001/01/01`` 로 그린다(쟀다). 등록하면 서버가 등록일 + 14 일을 넣는다.
                        - `ecm_base.PropChange` — 바꿀 속성 — ``None`` 인 칸은 그대로 둔다.
                          - `PropChange.empty` — 바꿀 칸이 하나도 없나.
                        - `ecm_server.page_tags` — 속성 화면이 든 태그 — 스크립트 갈래 값 ``sTagList``(쉼표로 이은 글 · 없으면 빈 글자나 "null").
                      - `_tags_after` — 태그 말들 → 뒤의 태그 전체. 아무 태그 말도 없으면 None(그대로).
                        - ↑ `ecm_base.ArgsError`
                      - ↑ `check_tags`
                      - ↑ `ecm_base.PropChange`
                      - ↑ `ecm_base.check_title`
                      - ↑ `check_due`
                      - ↑ `ecm_base.ArgsError`
                      - `PropsPlan` — 속성 한 판 — 지금과 뒤(이름 · 태그 · 완료일 셋 다 찬다)와 지금 권한 명단의 지문. ``token`` 이 확인 열쇠다.
                        - ↑ `ecm_base.PropChange`
                        - `PropsPlan.token` — 확인 열쇠 — 문서 · 지금과 뒤의 속성 · 지금 권한 명단의 지문.
                          - `ecm_base.token` — 확인 열쇠 — 미리 보기가 사람에게 보인 판의 지문. 같은 판이면 같은 열쇠가 다시 선다.
                      - `ecm_base.grants_key` — 권한 명단의 지문 — 줄마다 「역할:사람 열쇠」 를 늘어놓은 차례 없는 모습. 미리 본 뒤 바뀌었나 · 보낸 뒤 바란 대로인가를 다 이것으로 견준다.
                    - `_props_args` — 명령줄 → plan_props 의 칸. --tag 는 뒤의 태그 전체(여러 번), --clear-tags 는 다 빼고 시작, --add-tag · --drop-tag 는 지금에서.
                    - `props_done_words` — 속성을 바꾼 뒤의 말 — 다시 읽은 이름 · 태그 · 완료일.
                    - `apply_props` — 미리 본 한 판을 보낸다 — 열쇠가 맞고 그 사이 속성 · 명단이 그대로일 때만. 보낸 뒤 이름 · 태그 · 완료일과 다른 칸(보안등급 · 공개 · 폴더 · 소유자 · 권한 명단)을 다시 읽어 바란 그대로인가 본다.
                      - ↑ `ecm_base.token`
                      - `ecm_base.Stale` — 확인 열쇠가 지금과 다르다 — 미리 본 뒤 문서 · 파일 · 명단이 바뀌어 아무것도 안 바꿨다.
                      - ↑ `_props_gate`
                      - ↑ `_props_now`
                      - ↑ `ecm_base.grants_key`
                      - `watch` — 저장을 보내기 전에 지켜볼 칸의 지금 값을 쥔다.
                      - ↑ `ecm_base.EcmError`
                      - `props_read_back_word` — 속성을 보낸 뒤 다시 읽은 값이 바란 것과 다를 때의 말 — 다시 읽은 이름 · 태그 · 완료일을 댄다.
                      - `drifted` — 보낸 뒤 다시 읽은 속성 화면에서 쥐어 둔 값과 달라진 칸 — 쥔 차례대로.
                      - `stop_on_drift` — 보낸 뒤 흔들린 칸이 있으면 ``head`` 로 시작하는 말로 멈춘다 — 사람이 화면에서 바로 되돌린다.
                        - ↑ `ecm_base.EcmError`
                  - `cmd_cabinets` — 볼 수 있는 문서함을 읽어 말한다.
                    - `cabinet_words` — 문서함마다 한 줄 — 이름 · 갈래 · 내 부서인가 · 열쇠.
                  - `cmd_can` — 문서의 잠금 상태와 지금 할 수 있는 것을 읽어 말한다.
                    - `can_head_words` — 할 수 있는 것의 머리 한 줄 — 이름 · 판 · 잠금 상태.
                    - `lock_state` — 속성 화면의 잠금을 상태 하나로 — 못 읽음 · 안 잠김 · 나 · 남. 잠겼을 때만 잠근 이가 나인가를 묻는다.
                    - `menu_words` — 우클릭 메뉴의 켜진 것 · 꺼진 것.
                  - `cmd_cancel_edit` — 편집취소하고 그 끝을 말한다.
                    - `cancelled_words` — 편집취소의 말 — 창을 닫았나, 편집완료 창이 남았으면 사람에게 이를 말.
                    - `cancel_edit` — 화면의 「편집취소」와 같은 차례 — 잠근 이가 나인가(``checkuser``)를 보고, 편집으로 받은 그 문서의 창이 떠 있으면 닫은 뒤 서버 걸음(``cancelcheckout``)과 에이전트 한 줄(``cancelcheckout␈<열쇠>``)을 보내고 다시 읽어 풀렸나 본다.
                      - ↑ `ecm_base._object_id`
                      - `refuse_unless_mine` — 내가 편집으로 잠근 문서가 아니면 아무것도 안 보내고 ``EcmError`` — 안 잠겼거나 · 잠금을 못 읽었거나 · 남이 잠갔다.
                        - ↑ `ecm_base.EcmError`
                      - `close_edit_window` — 편집으로 받은 그 문서의 가장 새 창을 닫고 창의 상태(closed · not-found)를 낸다 — 저장 안 된 고침이 있으면 ``discard`` 없이는 아무것도 안 보내고 ``EcmError``.
                        - `_close` — 그 문서만 닫는다 — 저장하지 않는다.
                          - `_powershell` — PowerShell 손 하나를 띄워 끝까지 기다린다 — 프로필 없이, 실행 정책은 그 프로세스에서만 푼다.
                          - `_last_json` — 손이 표준 출력 끝 줄에 낸 JSON — 출력이 비었거나 끝 줄이 JSON 이 아니면 빈 dict.
                          - ↑ `ecm_base.EcmError`
                        - ↑ `ecm_base.EcmError`
                      - `wait_unlocked` — 편집취소를 보낸 뒤 다시 읽은 잠금이 풀릴 때까지 기다린다 — 시한 안에 안 풀리면 에이전트 답을 대고 ``EcmError``.
                        - ↑ `ecm_base.EcmError`
                      - `Cancelled` — 편집취소 한 판의 결과 — 편집 창을 닫은 형편 · 에이전트의 답 · 편집완료 창이 남았나.
                      - `checkin_pending` — 그 문서의 편집완료 창이 이미 떠 있나 — 사람이 오피스를 먼저 끈 판. 창을 찾기만 하고 누르지 않는다.
                        - ↑ `_powershell`
                    - `ecm_agent.Agent` — PC 의 ECM 에이전트 — 받은 파일을 기본 앱으로 열고(보기 · 편집), 새 문서로 올릴 파일을 서버 임시 자리에 올린다.
                      - `Agent.from_env` — 환경변수 ``ECM_AGENT_URL``(비면 ``DEFAULT_AGENT``)과 받는 자리(``agent_docs_root``)로 에이전트 하나를 짓는다.
                        - ↑ `ecm_base.agent_docs_root`
                      - `Agent._received` — ``<받는 자리>\<계정>\<folder>\<시각 번호>\`` 아래 받은 파일들(잠금 파일 ``~$`` 은 뺀다).
                      - `Agent.newest_edit_file` — 편집으로 받은 그 문서의 가장 새 파일(오피스 꼴) — 지금 잠금은 가장 새로 받은 판의 것이다.
                        - ↑ `Agent._received`
                      - `Agent._download` — 에이전트에 받기 한 줄을 보내고, ``folder`` 아래 새로 생긴 받은 파일이 다 쓰일 때까지 기다려 그 경로를 낸다.
                        - `download_line` — 받기 한 줄을 짓는다 — 열기 표의 값에 제어 글자가 들면 보내지 않고 ``AgentError``.
                          - `ecm_base.AgentError` — PC 의 ECM 에이전트가 안 돌거나, 거절했거나, 받은 파일이 안 생겼다.
                        - ↑ `Agent._received`
                        - `ws_exchange` — 웹소켓 하나를 열어 글 한 줄을 보내고 첫 글 답을 낸다(RFC 6455 의 쓰는 몫만).
                          - ↑ `ecm_base.AgentError`
                          - `_ws_frame` — 보내는 쪽 웹소켓 틀 하나 — FIN · ``opcode`` 에 길이를 달고 바이트를 무작위 가리개로 덮는다.
                          - `_Reader` — 웹소켓 답을 바라는 바이트 수만큼씩 꺼내는 받기 버퍼 — 머리 뒤에 이미 받은 몫(``buffered``)부터 쓴다.
                            - `_Reader.take` — ``n`` 바이트가 찰 때까지 소켓에서 받아 앞의 ``n`` 바이트를 낸다 — 그 전에 연결이 닫히면 ``AgentError``.
                              - ↑ `ecm_base.AgentError`
                          - `ecm_base.AgentTimeout` — ECM 에이전트가 시한 안에 답하지 않았다 — 어느 줄에서든. 받기에서는 메일 첨부의 머리 열쇠가 흔한 까닭이다(그 말은 받는 쪽이 든다).
                        - ↑ `ecm_base.AgentTimeout`
                        - ↑ `ecm_base.AgentError`
                        - `no_answer_word` — 받기 줄에 에이전트가 말이 없을 때의 말 — 메일 첨부에서 온 열쇠면 다시 받는 길을 이른다.
                        - `Agent._wait_received` — ``folder`` 아래 ``before`` 에 없던 받은 파일이 생겨 크기가 두 번 같게 볼 때까지 기다려 그 경로를 낸다 — 시한을 넘기면 ``AgentError``. 이름이 표의 파일 이름과 같은 것을 먼저 고른다.
                          - ↑ `Agent._received`
                          - ↑ `ecm_base.AgentError`
                      - ↑ `Agent._wait_received`
                      - `Agent.download_view` — 보기로 받는다 — 읽기 전용으로 뜬다.
                        - ↑ `Agent._download`
                      - `Agent.download_edit` — 편집으로 받는다 — ``Ecm.checkout`` 으로 잠근 뒤에만 부른다.
                        - ↑ `Agent._download`
                      - `Agent.cancel` — 편집취소의 에이전트 한 줄 — 잠금을 풀고 편집으로 받은 자리를 정리한다.
                        - ↑ `ws_exchange`
                        - ↑ `ecm_base._object_id`
                      - `Agent.upload_new` — 새 문서로 올릴 파일을 서버 임시 자리에 올린다 — 화면의 등록 저장이 먼저 부르는 줄. (서버 자리, 서버 파일 이름)을 낸다.
                        - ↑ `ecm_base.AgentError`
                        - ↑ `ws_exchange`
                  - `cmd_change` — 이미 편집으로 받은 파일을 등급 문에 대어 본 뒤 고치고, ``--desc`` 가 있으면 올리기 미리 보기까지 낸다.
                    - ↑ `_pre_change`
                    - `check_readable` — 속성 화면을 읽어(``Ecm.security``) 등급 문(``gate``)을 지난다 — ``Security`` 를 낸다.
                      - `ecm_base.SecurityUnread` — 속성 화면에서 보안등급을 못 읽어 사람에게 묻기 전에 멈췄다 — AI 로 보내도 된다고 답하면 ``ai_ok`` 로 넘긴다.
                      - `gate` — 등급 문의 판정 하나 — 문서의 글자 · 그림을 대화로 들이는 손가락(읽기 · 편집 열기 · 고치기 · 올리기 미리 보기)이 다 이것을 지난다.
                        - ↑ `ecm_base.SecurityUnread`
                        - `ecm_base.Classified` — 기밀 · 핵심기술 문서라 사람에게 묻기 전에 멈췄다 — AI 로 보내도 된다고 답하면 ``ai_ok`` 로 넘긴다.
                    - `_change_and_maybe_plan` — 열린 그 문서를 고치고(바꿀 것이 있으면), ``--desc`` 가 있으면 올리기 미리 보기와 열쇠까지 낸다.
                      - `_print_changed` — 고친 뒤의 말 — 고친 것 · 넣은 것마다 한 줄과 저장했나.
                      - `change_document` — 편집으로 열린 그 문서를 창 안에서 고치고 저장한다(창은 남긴다). 바꿀 것이 비면 저장 안 된 고침이 있을 때만 저장한다.
                        - `check_changes` — 바꿀 것을 문서를 건드리기 전에 가린다(잠그기 전에도 부른다) — 못 할 까닭이 있으면 ``EcmError``. 어느 앱이 어느 바꿀 것을 받나는 ``EDIT_CHANGES`` 의 ``apps`` 칸이 든다.
                          - ↑ `ecm_base.EcmError`
                          - `Change` — 편집 패스의 바꿀 것 하나.
                          - ↑ `ecm_base.ArgsError`
                          - ↑ `check_change_shape`
                        - ↑ `_powershell`
                        - ↑ `_last_json`
                        - `Changed` — 열린 문서를 고친 한 판의 결과 — 고친 것들과 이 판에 저장했나.
                        - ↑ `ecm_base.EcmError`
                      - ↑ `ecm_base.EcmError`
                      - `change_failed_word` — 방금 편집으로 연 문서를 못 고쳤을 때의 말 — 잠겼으니 다시 고치거나 편집취소하는 길.
                      - `_print_checkin_plan` — 올리기 미리 보기의 말 — 문서 · 판 · 수정 내용 · 올라갈 판 · 확인 열쇠와 다음 걸음.
                      - `prepare_checkin` — 올리기를 미리 본다 — 창의 고침을 저장하고(저장 안 된 고침이 있을 때만) 지금 판 · 잠금을 읽어 확인 열쇠를 낸다.
                        - ↑ `checkin_inputs`
                        - ↑ `gate`
                        - `refuse_unpreviewable` — 올리기를 미리 볼 수 있는 문서인가 — 지금 판을 못 읽었거나 편집 잠금이 없으면(취소됐거나 이미 올라갔다) ``EcmError``.
                          - ↑ `ecm_base.EcmError`
                        - `save_or_already_closed` — 창의 판을 저장하고 (저장했나, 사람이 이미 닫았나)를 낸다 — 창이 없는데 편집완료 창이 떠 있으면 사람이 먼저 닫은 것이다(디스크의 판이 올라간다). 창도 편집완료 창도 없으면 저장 손의 ``EcmError`` 그대로.
                          - `save_window` — 편집으로 열린 그 문서 창의 저장 안 된 고침만 저장한다 — 저장했으면 참. 고치는 손을 바꿀 것 없이 한 판 돌린다(그 손은 바꿀 것이 비면 저장만 한다). 문서가 안 떴으면 ``EcmError``.
                            - ↑ `change_document`
                            - ↑ `Changes`
                          - ↑ `ecm_base.EcmError`
                          - ↑ `checkin_pending`
                        - `CheckinPlan` — 올리기 미리 보기 — 서버를 안 바꾼다.
                          - `CheckinPlan.token` — 확인 열쇠 — 문서 · 지금 판 · 수정 내용 · 파일 · 미리 본 때 그 파일 판의 지문(``checkin_token``).
                            - `checkin_token` — 올리기의 확인 열쇠 — 판이 바뀌거나, 그 파일이 다시 저장되거나(사람 · change), 수정 내용 글이 다르면 달라진다.
                              - ↑ `ecm_base.token`
                        - `file_stamp` — 디스크의 그 파일 판 — (고친 시각 ns, 크기). 오피스가 쥔 감긴 파일은 바이트를 못 읽어 시각 · 크기로 잰다.
                      - `next_change_words` — 고친 뒤 올리기를 아직 안 볼 때의 다음 걸음.
                  - `cmd_checkin` — 미리 본 그대로 올리고 그 끝을 말한다.
                    - `checked_in_words` — 올리기의 끝의 말 — 고친 것 없이 풀렸으면 그렇다고, 올랐으면 앞 판 → 뒤 판과 새 판의 열쇠(못 받았으면 그 까닭).
                    - `checkin_document` — 미리 본 그대로 올린다 — 확인 열쇠가 지금 판 · 디스크의 그 파일 · 수정 내용과 맞고 창에 저장 안 된 고침이 없을 때만 문서를 닫고, 에이전트의 편집완료 창에서 늘 다음 판 · 수정 내용으로 올린 뒤 판이 올랐나 본다.
                      - ↑ `checkin_inputs`
                      - ↑ `ecm_base.EcmError`
                      - ↑ `checkin_token`
                      - ↑ `file_stamp`
                      - ↑ `ecm_base.Stale`
                      - ↑ `_close`
                      - `checkin_state_after_close` — 문서 창을 닫은 뒤 올리기가 설 자리를 낸다 — 고친 것 없이 풀렸다(``CHECKIN_UNCHANGED``) · 문서 창도 편집완료 창도 없다 (``CHECKIN_NO_WINDOW``) · 편집완료 창을 누르러 간다(``CHECKIN_PRESS``). 앱에 남은 문서가 없이 닫혔을 때만 잠금을 다시 읽는다.
                        - `_released_unchanged` — 고친 것 없이 닫혀 에이전트가 편집완료 창 없이 잠금만 풀었나 — 잠금이 풀리고 판이 그대로면 참. 고친 판이면 편집완료 창이 뜰 때까지 잠금이 남으니, 잠긴 채 ``wait`` 초가 지나면 거짓이다.
                        - ↑ `checkin_pending`
                      - `press_checkin` — 편집완료 창 손을 띄워 다음 판 · 수정 내용으로 누르게 하고 (종료 값, 끝 줄 JSON, 출력 또는 오류의 글)을 낸다 — 칸을 못 읽고 나오면 새 프로세스로 다시 붙는다.
                        - ↑ `_powershell`
                        - ↑ `_last_json`
                      - `checkin_state_after_press` — 편집완료 창 손의 끝을 올리기의 상태 하나로 셈한다 — 창이 안 떴으면(종료 2) 잠금을 다시 읽어 고친 것 없이 풀렸나 · 다른 문서가 남았나 · 아직 잠겼나를 가르고, 그 밖은 저장은 보냈는데 안 닫힘 · 안 누름 · 눌렀음이다.
                        - ↑ `_released_unchanged`
                      - `CheckedIn` — 올리기의 끝 — 앞 판 · 뒤 판(고친 것 없이 풀렸으면 같다) · 고른 판, 판이 올랐으면 새 판의 열쇠(못 받았으면 그 까닭).
                        - `CheckedIn.unchanged` — 고친 것 없이 풀려 판이 그대로인가.
                      - `checkin_stop_word` — 올리지 못한 상태 하나를 사람에게 할 말로 옮긴다 — 다음 걸음까지. ``names`` 는 같은 앱에 남은 문서 이름(``shown_names``), ``detail`` 은 편집완료 창 손이 낸 글이다.
                      - `shown_names` — 닫는 손이 댄 남은 문서 이름들을 사람에게 보일 꼴로 — 받은 파일의 꼬리(열쇠 · 계정)를 떼고 잇는다.
                      - `wait_new_version` — 편집완료를 누른 뒤 문서 정보의 최종 버전이 ``before`` 에서 오르기를 기다려 오른 판을 낸다 — 시한 안에 안 오르면 ``EcmError``.
                        - ↑ `ecm_base.EcmError`
                      - `superseded` — 준 열쇠가 지난 판이면 지금 판의 열쇠 — (지금 판의 열쇠 · 지금 판이면 빈 글자, 못 가렸으면 그 까닭). ``current_key`` 의 보기 첫 걸음이라 받는 요청보다 먼저(등급 문 앞) 부르지 않는다.
                        - ↑ `ecm_base.EcmError`
                        - `older_key` — 준 열쇠가 지금 판의 열쇠(``current_key`` 의 답)와 다른가 — 다르면 준 열쇠는 지난 판이다.
                  - `cmd_count` — 문서함 하나(또는 왼쪽 메뉴의 목록)의 건수를, all 이면 문서함마다의 건수와 합을 말한다.
                    - `_places` — --cabinet 값 → ([(문서함 열쇠 · 내 문서함은 빈 글자, 목록의 머리)], 상한을 넘어 안 물은 문서함). 열쇠로 준 문서함의 머리는 「문서함 <열쇠>」 그대로이고, 이름 · all 로 푼 문서함은 머리에 이름을 붙인다.
                    - `count_words` — 문서함 하나의 건수 — 수만.
                    - `_list_kwargs` — 명령줄 → 목록 · 건수가 함께 받는 칸(찾는 말 · 기간 · 폴더 · 왼쪽 메뉴 목록 · 꼴).
                    - `count_line_words` — 문서함 하나의 건수 한 줄.
                    - `count_total_words` — 건수의 합 한 줄.
                    - `_tell_skipped` — all 의 상한을 넘어 안 물은 문서함이 있으면 그 이름들을 댄다.
                  - `cmd_default_app` — 확장자의 기본 앱 상태와 이 PC 의 해시 셈을 읽어 말한다 — 쓰지 않는다.
                    - `default_app.normalize` — 확장자를 점 하나로 시작하는 소문자로 다듬는다 — 확장자 꼴이 아니면 ``ValueError``.
                    - `default_app.state` — 그 확장자의 지금 고름 — 쓰지 않는다.
                      - ↑ `normalize`
                      - `_read_value` — HKCU 의 그 키에서 값 하나를 글자로 — 키나 값이 없으면 빈 글자.
                      - `Choice` — 그 확장자의 지금 고름. ``progid`` 가 빈 글자면 안 정해졌다.
                    - `default_app.preflight` — 이 PC 의 UserChoice 마다 키의 마지막 쓴 시각으로 해시를 다시 지어 Windows 가 적은 값과 견준다 — 읽기만 한다.
                      - `user_sid` — 이 프로세스를 돌리는 사용자의 SID(소문자) — 토큰에서 읽는다.
                      - `user_experience` — shell32.dll 이 든 「User Choice set via Windows User Experience {…}」 글. 못 찾으면 알려진 값.
                      - `Preflight` — 이 PC 에 Windows 가 적어 둔 UserChoice 를 우리 계산으로 다시 지은 셈 — ``total`` 중 ``matched`` 가 같았다.
                        - `Preflight.algorithm_differs` — 하나도 안 맞으면 이 PC 의 Windows 는 다른 계산을 쓴다.
                      - `minute_stamp` — FILETIME(100 ns · 1601 기준)을 분으로 내려 16 자리 소문자 hex 로.
                      - `choice_hash` — UserChoice 의 ``Hash`` 값(base64 여덟 바이트). ``stamp`` 는 키를 쓴 분의 FILETIME 16 자리 hex 다.
                        - `_words` — ``offset`` 자리의 리틀엔디언 부호 없는 32 비트 한 낱.
                        - `_pass_one` — 해시의 첫 셈 — 두 낱씩 차례로 섞어 (마지막 carry, 누적 합)을 낸다.
                          - ↑ `_words`
                          - `_hi` — 32 비트로 자른 값의 위 16 비트.
                        - `_pass_two` — 해시의 둘째 셈 — 첫 셈과 다른 곱수로 두 낱씩 차례로 섞어 (마지막 carry, 누적 합)을 낸다.
                          - ↑ `_words`
                          - ↑ `_hi`
                    - `default_app_words` — 기본 앱 상태의 말 — 지금 고름 · Windows 가 푸는 앱 · 고를 앱 · 해시 셈이 맞은 수.
                    - `default_app.resolved_progid` — Windows 가 지금 그 확장자를 어느 ProgId 로 푸는가(``AssocQueryStringW`` · ASSOCSTR_PROGID). 못 풀면 빈 글자.
                    - `default_app.pick_progid` — 그 확장자에 깔린 앱의 ProgId — 표의 앞에 선 것부터. 깔린 것이 없으면 빈 글자.
                      - ↑ `normalize`
                      - `_progid_installed` — HKCR 에 그 ProgId 키가 있으면 깔린 앱으로 본다.
                  - `cmd_doc` — 속성 화면을 한 번 읽어 판 · 잠금 · 보안등급 · 이름을 말한다.
                    - `doc_words` — 속성 화면 한 번 읽기의 말 — 이름 · 판 · 잠금 · 보안(물어야 하면 그 길).
                  - `cmd_edit` — 문서를 잠가 편집으로 열고, 바꿀 것이 있으면 고친 뒤 ``--desc`` 가 있으면 올리기 미리 보기까지 낸다.
                    - ↑ `changes_of`
                    - `edit_document` — 편집으로 연다 — 서버가 그 문서를 이 사람 이름으로 잠그고, 에이전트가 읽기 쓰기로 띄운다.
                      - ↑ `check_readable`
                      - `refuse_uneditable` — 보기 첫 걸음의 표가 편집으로 열어 올릴 수 있는 꼴(오피스 셋)인가 — 아니면 잠그기 전에 ``EcmError``.
                        - ↑ `ecm_base.EcmError`
                      - ↑ `check_changes`
                      - `default_app.ensure` — 그 확장자의 기본 앱이 서 있게 한다 — 있으면 그대로 두고, 없으면 깔린 앱으로 적은 뒤 Windows 가 받았나 본다.
                        - ↑ `normalize`
                        - `_ensure_choice` — 그 확장자에 고름이 없으면 깔린 앱으로 적고 Windows 가 받았나 본다 — 이미 있으면 그대로 두고, 사람이 골라야 하면 ``DefaultAppNeeded``.
                          - ↑ `state`
                          - `Ensured` — ``ensure`` 의 답 — ``progid`` 는 선 기본 앱이고, ``written`` 이 참이면 이번에 적었다.
                          - ↑ `pick_progid`
                          - `DefaultAppNeeded` — 사람이 그 확장자의 기본 앱을 한 번 골라야 한다.
                          - `app_name` — ProgId 의 사람이 읽는 앱 이름(``AssocQueryStringW`` · ASSOCSTR_FRIENDLYAPPNAME) — 고르는 창에 보이는 그 이름. 못 얻으면 ProgId.
                          - ↑ `preflight`
                          - `write_choice` — UserChoice 를 ProgId · Hash 한 벌로 적고, 키의 시각으로 다시 지어 맞을 때까지 고쳐 쓴다.
                            - ↑ `normalize`
                            - ↑ `user_sid`
                            - ↑ `user_experience`
                            - ↑ `minute_stamp`
                            - `now_filetime` — 지금 시각을 FILETIME(100 ns · 1601 기준)으로.
                            - ↑ `choice_hash`
                          - `_notify_assoc_changed` — 탐색기에 파일 연결이 바뀌었다고 알린다(``SHChangeNotify`` · SHCNE_ASSOCCHANGED).
                          - ↑ `resolved_progid`
                          - `_remove_choice` — 그 확장자의 UserChoice 키를 지운다 — 없으면 그대로 둔다.
                        - `quiet_new_apps` — 그 확장자에 등록된 앱 가운데 「보였다」 값이 없는 앱만 값을 더한다 — 더한 값 이름을 낸다.
                          - ↑ `normalize`
                          - `registered_progids` — 그 확장자를 열 수 있다고 등록된 앱의 ProgId(``HKCR\.<확장자>\OpenWithProgids`` 의 값 이름) — 읽기만 한다.
                            - ↑ `normalize`
                      - ↑ `ecm_base.AgentError`
                      - `locked_but_not_received_word` — 잠근 뒤 받기가 안 섰을 때의 말 — 서버에서 잠겼으니 편집취소를 이른다.
                      - `ecm_base.Opened` — 받은 파일을 연 결과 — 받은 파일 · 열기 표 · 그 확장자의 기본 앱 · 이번에 기본 앱을 적었나.
                        - `Ticket` — 열기 첫 걸음의 답 — 에이전트에 보낼 세 값.
                          - `Ticket.ext` — 받을 파일 이름의 확장자(점을 붙인 소문자).
                    - ↑ `ecm_agent.Agent`
                    - `edit_opened_words` — 편집으로 연 문서의 말 — 받은 파일 줄(등급 문을 지났다) · 기본 앱 · 잠갔다.
                      - `_describe_open` — 받은 파일과 기본 앱의 두 줄 — 받은 파일 줄은 등급 문을 지났나(``gated``)에 따라 그 파일을 drm-office-read 로 열어도 되나를 든다.
                    - ↑ `_change_and_maybe_plan`
                  - `cmd_find_folder` — 모든 문서함에서 이름에 그 글이 든 폴더를 찾아 문서함 이름과 함께 말한다.
                    - ↑ `ecm_base.ArgsError`
                    - `no_named_folder_word` — 이름에 그 글이 든 폴더가 하나도 없을 때의 말.
                    - `named_folder_words` — 이름으로 찾은 폴더의 말 — 서버가 준 경로 · 폴더 열쇠 · 문서함 이름(``names``: 열쇠 → 이름).
                  - `cmd_folders` — 문서함의 폴더 한 층을, ``--find`` 면 나무 전체에서 이름으로 찾은 폴더를 말한다.
                    - `found_folder_words` — 이름으로 찾은 폴더의 말 — 꼭 맞는 것, 없으면 이름에 그 글이 든 후보(고르지 않는다). 둘 다 없으면 ``ArgsError``.
                      - ↑ `ecm_base.ArgsError`
                      - `ecm_base.path_word` — 폴더의 이름 경로를 화면의 꼴(「기획 > 보고」)로.
                    - `folder_layer_words` — 폴더 한 층의 말 — 이름 · 열쇠 · 아래 폴더가 있나.
                  - `cmd_latest` — 옛 열쇠의 지금 판 열쇠(지난 판이면 그 판까지)를 읽어 말한다.
                    - ↑ `older_key`
                    - `latest_words` — 지금 판의 열쇠의 말 — ``version`` 이 있으면 준 열쇠가 지난 판이었다.
                  - `cmd_link` — 지금 판의 열쇠로 보기 링크를 짓고 말한다(준 열쇠가 지난 판이면 그렇다고).
                    - ↑ `older_key`
                    - `older_link_words` — 준 열쇠가 지난 판이라 지금 판의 링크를 짓는다는 머리.
                    - `link_words` — 보기 링크와 열리는 사람의 말.
                    - `doc_link` — 문서의 보기 링크 — 화면의 「URL 복사」 가 내는 꼴(문서 열쇠 · doc 열쇠 · 시스템 이름을 글자째 16진으로)을 열쇠만으로 짓는다.
                  - `cmd_list` — 문서함마다(또는 왼쪽 메뉴의 목록) 한 쪽을 받아 말이나 JSON 줄로 내고, 안 물은 문서함을 댄다.
                    - ↑ `_places`
                    - ↑ `_list_kwargs`
                    - `json_lines_words` — 목록 줄마다 JSON 한 줄(``doc_json``).
                      - `doc_json` — 목록 줄 하나의 JSON — ``cabinet`` 을 주면(여러 문서함을 한 판에 낸 줄) 어느 문서함인가를 덧붙인다(내 문서함은 빈 글자).
                    - `_print_docs` — 목록 한 쪽의 말 — 머리(자리 · 문서함 안 폴더 ``folder``)와 줄마다 한 줄. ``mixed`` 면(여러 문서함이 섞인 왼쪽 메뉴의 목록) 줄마다 그 문서가 든 문서함을 댄다.
                      - `ecm_base.level_name` — 등급 글자(``1A`` …)의 이름 — 공개 짝과 무관한 앞 이름(기밀 · 사외비A · 사외비B · 일반). 모르는 글자는 그대로.
                    - ↑ `_tell_skipped`
                  - `cmd_notices` — ECM 알림 숫자를 읽어 말한다.
                    - `notice_words` — 알림 숫자마다 한 줄과 목록을 보는 길.
                  - `cmd_open` — 문서를 받아 화면에 띄우고 받은 파일 줄을 말한다(등급 문을 안 지난 사람의 창이다).
                    - `opened_words` — 화면에 띄운 문서의 말 — 받은 파일 줄(등급 문을 안 지났다)과 기본 앱.
                      - ↑ `_describe_open`
                    - `open_document` — 문서 하나를 에이전트로 받아 연다 — 열기 전에 그 확장자의 기본 앱을 세운다.
                      - ↑ `default_app.ensure`
                      - ↑ `default_app.DefaultAppNeeded`
                      - ↑ `default_app.state`
                      - ↑ `ecm_base.Opened`
                    - ↑ `ecm_agent.Agent`
                  - `cmd_preview_access` — 권한 바꾸기를 미리 보고 확인 열쇠를 말한다 — 서버를 안 바꾼다.
                    - `_print_plan` — 권한 미리 보기의 말 — 지금 → 뒤 사람 수 · 덧붙인 말 · 더함 · 뺌 · 옮김 · 뒤 명단 · 확인 열쇠와 다음 걸음.
                      - ↑ `_print_grants`
                    - ↑ `_access_plan`
                  - `cmd_preview_checkin` — 올리기 미리 보기와 확인 열쇠를 말한다 — 창에 저장 안 된 고침이 있으면 저장하고, 서버는 안 바꾼다.
                    - ↑ `_print_checkin_plan`
                    - ↑ `prepare_checkin`
                  - `cmd_preview_props` — 속성 바꾸기를 미리 보고 확인 열쇠를 말한다 — 서버를 안 바꾼다.
                    - `_print_props` — 속성 미리 보기의 말 — 지금과 뒤의 이름 · 태그 · 완료일 · 확인 열쇠와 다음 걸음.
                    - ↑ `plan_props`
                    - ↑ `_props_args`
                  - `cmd_preview_register` — 새 문서 등록을 미리 보고 확인 열쇠를 말한다 — 서버에도 에이전트에도 안 보낸다.
                    - `_print_register_plan` — 등록 미리 보기의 말 — 파일 · 이름 · 자리 · 보안 · 확인 열쇠와 다음 걸음.
                      - ↑ `ecm_base.path_word`
                    - `plan_register` — 새 문서로 올리기 전에 못 할 까닭을 다 가리고 ``RegisterPlan`` 을 낸다 — 파일 · 문서함 · 보안 짝 · 폴더가 그 문서함의 것인가 (폴더 열쇠면 나무에서 찾고, 경로면 꼭 맞는 이름으로 따라간다) · 이름 · 그 폴더의 같은 이름. 서버를 안 바꾼다.
                      - ↑ `register_inputs`
                      - `ecm_base.cabinet_key` — 문서함 열쇠(cab…)의 꼴을 가린다 — 아니면 ``ArgsError``.
                        - ↑ `ArgsError`
                      - `register_folder` — 올릴 폴더가 그 문서함의 것인가를 폴더 나무로 보고 (폴더 열쇠, 이름 경로)를 낸다 — 경로면 꼭 맞는 이름으로 따라가고, 열쇠면 나무에서 찾는다.
                        - ↑ `ecm_base.ArgsError`
                      - `refuse_duplicate` — 그 폴더에 같은 이름 · 확장자의 문서가 있으면 올리지 않고 ``EcmError`` — 다음 판은 편집 패스의 몫이다.
                        - ↑ `ecm_base.EcmError`
                      - `RegisterPlan` — 새 문서 등록의 미리 보기 — 서버를 안 바꾼다(같은 이름 찾기만 묻는다). ``token`` 이 확인 열쇠다.
                        - `RegisterPlan.token` — 확인 열쇠 — 올릴 파일 바이트 · 문서함 · 폴더 · 보안 짝 · 이름의 지문.
                          - ↑ `ecm_base.token`
                      - `file_digest` — 올릴 파일 바이트의 지문 — 미리 본 뒤 파일이 바뀌면 확인 열쇠가 달라진다.
                    - `_register_args` — 명령줄 → 등록 손의 칸 — 문서함 이름 · 열쇠는 여기서 한 번 열쇠로 푼다(``Ecm.cabinet_of``). 등록 손은 열쇠만 받는다.
                  - `cmd_read` — 문서의 글자를 말한다 — ``--fresh`` 가 아니고 남긴 글자가 있으면 그것을, 아니면 새로 받아 뽑은 것을 내고, 준 열쇠가 지난 판이면 그렇다고 이른다.
                    - `read_kept` — 남겨 둔 글자가 있으면 등급 문(``check_readable``)을 지난 뒤 그 파일을 낸다 — 없으면 None. 문서는 받지 않는다.
                      - `kept_text` — 그 문서 열쇠로 남겨 둔 글자 파일 — 없으면 None. 판이 오르면 열쇠가 바뀌므로 열쇠가 같으면 같은 판의 글자다.
                        - `text_dir` — read 가 뽑은 글자를 남기는 자리 — 환경변수 ``ECM_TEXT_DIR``, 비었으면 ``TEXT_DIR``.
                      - ↑ `check_readable`
                    - `tell_superseded` — 읽기의 머리 한 줄 — 준 열쇠가 지난 판이면 그렇다고 지금 판의 열쇠와 함께 말한다(읽기는 준 열쇠의 판 그대로다). 지금 판이면 말이 없다.
                    - `superseded_version` — 준 열쇠가 지난 판이면 (지금 판의 열쇠, 그 판 · 못 읽으면 ?, 빈 글자), 못 가렸으면 (빈 글자, 빈 글자, 까닭), 지금 판이면 빈 글자 셋.
                      - ↑ `superseded`
                    - `tell_kept` — 남겨 둔 글자로 답한다 — 남긴 파일을 풀고(``read_kept_file``) 받은 파일이 아직 있나 본 뒤(``still_received``) 말한다(``kept_words``).
                      - `read_kept_file` — 남긴 글자 파일을 (머리, 글자, 받은 파일의 자리 · 머리에 없으면 None)으로 푼다 — 쓰는 쪽(``keep_text``)과 같은 낱말 (``TEXT_SPLIT`` · ``KEPT_SOURCE_WORD`` · ``KEPT_WHEN_WORD``)로 읽는다.
                      - `kept_words` — 남긴 글자로 한 답의 말 — 문서를 받지 않았다는 것과 다시 받아야 하는 자리. ``received`` 는 아직 있는 받은 파일이다.
                        - `_tell_text` — 머리와 글자를 낸다 — 한 답(``ep_session.OUT_BYTES``)에 드는 글자는 화면에, 안 드는 글자는(``as_file`` 이면 짧아도) 남긴 파일의 경로만. 화면에 찍으면 통째로 실리거나 잘리고, 파일이면 모델이 나눠 읽고 찾는다.
                      - `still_received` — 남긴 글자가 가리키는 받은 파일이 아직 디스크에 있으면 그 자리 — 에이전트가 비웠으면 None.
                    - `read_document` — 보안등급을 보고(``check_readable``) → 열고 → 에이전트가 띄운 창을 닫고 → 받은 파일에서 글자를 뽑아 ``ReadResult`` 를 낸다.
                      - ↑ `check_readable`
                      - ↑ `open_document`
                      - `close_window` — 에이전트가 띄운 그 문서만 닫는다 — 그 앱에 남은 문서가 없을 때만 앱을 끈다.
                        - ↑ `_close`
                      - `viewer_of` — ProgId → 보기 창을 닫는 손이 붙을 앱 이름 — 오피스 셋에 Acrobat(Reader 포함)을 더한다.
                        - `office_of` — ProgId → 닫는 손이 붙을 오피스 앱 이름(Word · Excel · PPT). 오피스가 아니면 빈 글자.
                      - `extract_text` — 받은 파일을 drm-office-read 의 읽는 손에 넘겨 (글자, 그 손의 한 줄)을 낸다.
                        - `reader_path` — 글자를 뽑는 손(read-drm.ps1)의 자리 — 환경변수 ``ECM_DRM_READER``, 비었으면 ``DEFAULT_READER``.
                        - `ecm_base.ReadError` — 받은 파일에서 글자를 못 뽑았다.
                        - ↑ `_powershell`
                      - ↑ `ecm_base.ReadError`
                      - `ecm_base.ReadResult` — 읽기 한 판의 결과 — 뽑은 글자 · 읽는 손의 한 줄 · 연 결과 · 그 창을 닫은 형편.
                        - ↑ `Opened`
                    - ↑ `ecm_agent.Agent`
                    - `tell_read` — 읽은 결과로 답한다 — 글자를 늘 파일로 남기고(``keep_text``) 그 파일과 함께 말한다(``read_words``).
                      - `read_words` — 읽은 결과의 말 — 머리(읽는 손의 한 줄 · 받은 파일 · 창)와 글자를 ``_tell_text`` 의 갈래로 낸다.
                        - ↑ `_describe_open`
                        - ↑ `_tell_text`
                      - `keep_text` — 뽑은 글자를 ``text_dir()`` 에 남기고 그 경로를 낸다 — 이름은 받은 파일의 이름과 문서 열쇠, 머리는 읽는 손의 한 줄과 열쇠 · 받은 파일의 자리 · 뽑은 때다.
                        - ↑ `text_dir`
                  - `cmd_register` — 미리 본 그대로 새 문서로 올리고 새 문서의 열쇠 · 링크를 말한다.
                    - `register_document` — 미리 본 그대로 새 문서로 올리고 ``Registered`` 를 낸다 — 화면의 「컨텐츠 등록」과 같은 차례다.
                      - ↑ `plan_register`
                      - ↑ `ecm_base.Stale`
                      - `check_registered` — 올린 문서를 그 문서함 목록에서 다시 읽어 폴더 · 보안등급이 미리 본 값인가 보고 ``Registered`` 를 낸다 — 못 찾거나 다르면 다시 올리지 말라는 ``EcmError``.
                        - ↑ `ecm_base.EcmError`
                        - `ecm_base.Registered` — 새 문서로 올린 결과 — 문서 열쇠 · 이름과, 그 문서함 목록에서 다시 읽은 판.
                    - ↑ `ecm_agent.Agent`
                    - ↑ `_register_args`
                    - `registered_words` — 새 문서를 올린 뒤의 말 — 이름 · 판 · 보안 · 열쇠와 링크.
                    - ↑ `doc_link`
                  - `cmd_search` — 전사 검색을 돌려 그 쪽의 줄과 0 건의 넓힐 길을 말한다.
                    - ↑ `_search_query`
                    - `search_words` — 전사 검색 한 쪽의 말 — 범위와 건수, 0 건이면 넓힐 길, 줄마다 이름 · 올린 이 · 부서 · 보안 · 고침 · 열쇠.
                      - `search_widen` — 0 건일 때 넓힐 다음 걸음 — 이 칸 · 이 범위로 못 찾았다는 뜻이지 그런 문서가 없다는 뜻이 아니다.
                      - ↑ `ecm_base.level_name`
                  - `cmd_session` — ECM 세션이 살았나를 보고 말한다 — 끊겼으면 세션 종료 값.
                    - `session_words` — 세션이 살았나의 말.
                  - `cmd_versions` — 판 이력 한 쪽을 말하고(준 열쇠가 지난 판이면 지금 판의 열쇠도), ``--more`` 면 보안등급 변경 이력 · 활용 건수까지 말한다.
                    - ↑ `older_key`
                    - `history_words` — 판 이력 한 쪽의 말 — 머리(판 수 · 쪽 · 준 열쇠가 지난 판이면 지금 판의 열쇠 ``now``)와 판마다 한 줄.
                    - `security_log_words` — 보안등급 변경 이력의 말 — 몇 번과 줄마다 때 · 바꾼 이 · 앞 → 뒤.
                    - `use_count_words` — 활용 건수 한 줄.
                    - `versions_tail_words` — 판 이력의 끝 줄 — 지난 판을 여는 길.
                  - `cmd_who` — 찾는 말의 갈래대로 부서(아래 부서 · 부서원) · 부서 이름 · 사람을 찾아 말한다.
                    - ↑ `ecm_base.spec_kind`
                    - `sub_organ_words` — 바로 아래 부서마다 한 줄.
                    - `member_words` — 부서에 바로 든 사람마다 한 줄.
                    - `organ_words` — 이름으로 찾은 부서마다 한 줄 — 위 부서 > 이름 · 사람 수 · 아래 부서 수 · 코드.
                    - `people_words` — 이름으로 찾은 사람마다 한 줄 — 이름/메일 · 부서 · 사번.
                  - ↑ `kept_text`
                  - `ecm_server.Ecm` — ECM 서버 하나. 모든 요청을 서버에 닿기 전에 잰 꼴에 댄다 — 읽기는 ``guard``(닫힌 목록), 편집 열기 · 편집취소는 ``_guard_edit``, 잰 POST 여섯(``POST_SHAPES``)은 ``_post`` 가 든다.
                    - ↑ `ecm_base.ArgsError`
                    - `ecm_base.session_path` — 환경변수 ``MAILBOX_COOKIES`` 의 세션 파일 자리. 비었으면 ``SessionMissing`` — 자리는 스킬 ep-login 의 받는 손이 정한다.
                      - `SessionMissing` — 세션 파일이 없거나 그 안에 ECM 호스트의 쿠키가 없다 — 스킬 ep-login 으로 받는다.
                    - `cookie_header` — 세션 파일에서 ``url`` 에 실릴 쿠키만 골라 ``Cookie`` 머리 글로 낸다 — 없으면 빈 글자. 고르기(도메인 · 경로 · secure · 포트를 뗀 호스트)는 쿠키 통(``ep_session.load_jar``)이 한다.
                      - ↑ `ecm_base.SessionMissing`
                    - ↑ `ecm_base.SessionMissing`
                    - `Ecm.from_env` — 환경변수의 ECM 주소(``url_from_env``)와 세션 파일 자리(``session_path``)로 서버 하나를 짓는다.
                      - `ecm_base.url_from_env` — ECM 주소 — 환경변수 ``ECM_URL``, 비었으면 ``DEFAULT_URL``. 세션 파일 없이 주소만 드는 자리(이 손을 깔린 자리에서 싣는 앱)도 이것을 부른다.
                      - ↑ `ecm_base.session_path`
                    - `Ecm.guard` — 읽기 주소가 잰 꼴인가를 서버에 닿기 전에 가린다 — 아니면 ``Refused``. 꼴(메인 · json.do · 폴더 나무 · 속성 화면 · ajax 읽기)을 주소의 자리로 가르고 꼴마다의 판정은 제 손가락이 든다.
                      - `ecm_base.Refused` — 잰 꼴 밖의 요청을 지었다 — 읽기 · 편집 열기 · 등록 POST 어느 길이든 서버에 닿기 전에 막았다.
                      - `_is_json_read` — 속성 · 권한 화면이 묻는 json.do 읽기의 잰 꼴인가 — 판 이력 · 보안등급 변경 이력 · 활용 건수 · 역할 목록 · 즐겨찾기 · 이름 찾기 · 부서 찾기 · 하위 부서 · 부서원 아홉.
                      - `_single_query` — 질의를 칸 → 값으로 푼다.
                        - ↑ `ecm_base.Refused`
                      - `_is_folder_query` — 폴더 나무 한 층의 잰 꼴인가 — 문서함 바로 아래(MENU_DEPT · MENU_PROJECT + cab…) 또는 폴더 아래(F_LIST_FOLDER + cab…_fdr…).
                        - ↑ `_single_query`
                      - `_is_property_read` — 속성 화면 읽기의 잰 꼴인가 — 질의가 ``PROPERTY_QUERY`` 그대로에 문서 열쇠(``DOCID``) 하나.
                      - `_refuse_unmeasured_ajax` — ajax 읽기 질의가 닫힌 목록(``READS``)의 잰 꼴이 아니면 그 까닭으로 ``Refused`` — 서비스 · 갈래 하나 · 실을 수 있는 칸 · 문서함(formId) · 폴더 열쇠 · 지금 판 갈래 · 문서 열쇠 꼴.
                        - ↑ `ecm_base.Refused`
                    - `Ecm._fetch` — GET 하나를 그 길의 문에 대고 보낸다 — ``edit`` 은 바꾸는 GET 의 갈래 하나(``EDIT_FLAG`` · ``CANCEL_FLAG``)로 그 갈래 하나만 열고, 비우면 읽기 길(``guard``)이다.
                      - `Ecm._guard_edit` — 편집 열기 · 편집취소의 GET 이 잰 꼴(ECM 서버 · ajax 자리 · 그 서비스와 갈래 하나 · 문서 열쇠 하나)인가를 서버에 닿기 전에 가린다 — 아니면 ``Refused``.
                        - ↑ `_single_query`
                        - ↑ `ecm_base.Refused`
                      - ↑ `Ecm.guard`
                      - `Ecm._send` — 막는 문을 지난 요청 하나를 보내 (답의 바이트, ``Content-Type``)을 낸다 — 리다이렉트 · 401 · 403 은 ``SessionExpired``, 그 밖의 HTTP 오류 · 못 닿음은 ``EcmError`` 로 옮긴다.
                        - `ecm_base.SessionExpired` — ECM 이 세션을 안 받았다(``302 → /ECM/logout.jsp`` 따위) — 스킬 ep-login 으로 다시 받는다.
                        - ↑ `ecm_base.EcmError`
                    - ↑ `Ecm._send`
                    - ↑ `Ecm._guard_edit`
                    - `Ecm._post` — 잰 POST 만 보낸다 — 등록 화면의 둘(같은 이름 찾기 · 등록) · 속성 저장(권한 · 이름 · 태그 · 완료일)과, 조회지만 POST 인 셋(우클릭 메뉴 · 전사 검색 · 폴더 이름 찾기). 질의가 그 꼴 그대로이고 몸의 칸이 그 질의와 맞을 때만.
                      - `_is_context_body` — 우클릭 메뉴 묻기 몸인가 — 칸 셋 · 내 문서함 · 문서 열쇠 하나.
                      - `_is_dup_body` — 등록 화면의 같은 이름 찾기 몸인가 — 칸 셋 그대로.
                      - `_is_folder_find_body` — 폴더 이름 찾기 몸인가 — 칸 셋 · 사람 열쇠 · 두 글자부터.
                      - `_is_property_save` — 속성 저장 몸이 이 손이 잰 꼴인가 — 칸 이름이 화면의 것 그대로이고, 권한을 바꾸면(``isChangeRoleInfo=TRUE``) 명단은 권한 셋의 사람 줄만 든다(안 바꾸는 저장도 화면처럼 지금 명단을 싣는다). 이 손이 바꾸는 이름 · 태그 · 완료일은 ``plan_props`` 가 먼저 가리고, 바꾸지 않는 칸은 화면이 든 값 그대로 간다 — 여기서 다시 거르면 화면 밖에서 단 태그 하나가 그 문서의 권한 저장까지 막는다.
                      - `_is_register_body` — 등록 화면의 저장 몸인가 — 서비스와 갈래 칸. 몸의 값은 ``register_body`` 가 짓기 전에 가린다.
                      - `_is_search_body` — 전사 검색 몸의 잰 꼴인가 — 칸 다섯 · posmeta 의 칸 이름이 화면의 것.
                      - ↑ `ecm_base.Refused`
                      - ↑ `Ecm._send`
                    - `Ecm._ajax` — ``edit`` 이면 ``flag`` 갈래 하나만 여는 바꾸는 문(``_guard_edit``)으로 보낸다.
                      - `_answer` — ECM 의 답(앞에 빈 줄이 붙은 JSON)을 푼다 — ``MB_RTN_VALUE`` 가 참이 아니면 그 까닭으로 진다.
                        - `charset_of` — 답의 ``Content-Type`` 이 든 문자셋 — 없으면 utf-8.
                        - ↑ `ecm_base.EcmError`
                      - ↑ `Ecm._fetch`
                    - `Ecm.folders` — 문서함의 폴더 한 층 — ``parent`` 를 비우면 문서함 바로 아래, 주면 그 폴더(``fdr…``) 아래. 등록 화면의 폴더 나무와 같다.
                      - ↑ `ecm_base.cabinet_key`
                      - ↑ `ecm_base.folder_key`
                      - `Ecm.cabinet_by_key` — 그 사람이 볼 수 있는 문서함 가운데 열쇠가 ``key`` 인 것 — 없으면 None.
                        - `Ecm.cabinets` — 그 사람이 볼 수 있는 부서 · 프로젝트 문서함 — 메인 화면이 든 목록 그대로. 제 부서가 맨 앞이다.
                          - `Ecm._main_page` — 메인 화면 — 한 판에 한 번만 받는다.
                            - ↑ `Ecm._fetch`
                          - `ecm_base.Cabinet` — 부서 · 프로젝트 문서함 하나 — ``key`` 를 ``list --cabinet`` 에 준다.
                      - ↑ `_answer`
                      - ↑ `Ecm._fetch`
                      - `ecm_base.Folder` — 문서함 안의 폴더 하나 — ``id`` 를 ``register --folder`` 에, ``id`` 를 다시 ``folders --parent`` 에 준다.
                    - `Ecm.walk_folders` — 문서함의 폴더 나무를 문서함 바로 아래부터 한 층씩 훑으며 (이름 경로, Folder) 를 낸다 — 읽기만 하고, 아래 폴더가 있는 폴더만 연다.
                      - ↑ `Ecm.folders`
                      - ↑ `ecm_base.EcmError`
                    - `Ecm.folder_path` — 그 폴더(``fdr…``)의 이름 경로 — 그 문서함의 폴더 나무에 없으면 None. 찾으면 거기서 훑기를 멈춘다.
                      - ↑ `ecm_base.folder_key`
                      - ↑ `Ecm.walk_folders`
                    - `Ecm.match_folders` — 나무를 한 번 끝까지 훑어 (이름이 꼭 맞는 폴더, 이름에 그 글이 든 폴더)를 낸다 — 뒤엣것은 대소문자 · 빈칸을 안 가리고, 앞엣것과 겹치지 않는다.
                      - ↑ `ecm_base.ArgsError`
                      - `ecm_base._loose` — 이름 일부를 견줄 꼴 — 대소문자 · 빈칸을 안 가린다(「월간보고」 · 「월간 보고」가 같다).
                      - ↑ `Ecm.walk_folders`
                    - `Ecm.resolve_folder` — 폴더 경로(「이름 > 이름」 — 화면의 꼴)를 한 층씩 꼭 맞는 이름으로 따라가 (이름 경로, Folder) 를 낸다.
                      - `Ecm.cabinet_name` — 그 열쇠의 문서함 이름 — 볼 수 있는 문서함에 없으면 빈 글자.
                        - ↑ `Ecm.cabinet_by_key`
                      - ↑ `ecm_base.ArgsError`
                      - ↑ `Ecm.folders`
                      - `folder_miss_word` — 폴더 경로의 한 마디가 그 층에 꼭 하나로 안 걸렸을 때의 말 — 몇 개였나(0 이면 없다)와 그 층의 폴더들.
                        - ↑ `ecm_base.path_word`
                    - `Ecm.duplicates` — 그 폴더에 같은 이름 · 확장자의 문서가 있나 — 화면이 등록 전에 묻는 같은 요청. 걸린 이름들을 낸다.
                      - ↑ `_answer`
                      - ↑ `Ecm._post`
                    - `Ecm.register` — 에이전트가 임시 자리에 올린 파일을 그 폴더의 새 문서로 등록하고(몸은 ``register_body``) 답의 문서 열쇠를 낸다.
                      - `register_body` — 화면의 「컨텐츠 등록」 저장 몸을 짓는다 — 값이 잰 꼴(폴더 열쇠 · 보안 짝 · 확장자 · 서버 임시 자리) 밖이면 ``Refused``.
                        - `_size_label` — 화면의 byteToKB — 등록 몸의 크기 칸은 「15KB 」 꼴이다(끝에 빈칸 하나).
                        - ↑ `ecm_base.Refused`
                      - ↑ `_answer`
                      - ↑ `Ecm._post`
                      - ↑ `ecm_base.EcmError`
                    - ↑ `Ecm._main_page`
                    - `Ecm.session_alive` — 메인 화면이 200 이면 산 세션이다 — ``302 → logout.jsp`` 면 거짓. 문서를 건드리지 않는다.
                      - ↑ `Ecm._main_page`
                      - ↑ `ecm_base.SessionExpired`
                    - `Ecm._list_params` — 목록 · 건수 질의의 칸을 화면의 값에 대어 가려 짓는다 — 내 문서함 · 문서함 · 그 안 폴더 · 왼쪽 메뉴 목록 가운데 하나의 꼴이고, 못 쓸 값이면 ``ArgsError``.
                      - ↑ `ecm_base.ArgsError`
                      - ↑ `ecm_base.refuse_box_with_place`
                      - ↑ `ecm_base.cabinet_key`
                      - ↑ `ecm_base.folder_key`
                    - ↑ `Ecm.cabinets`
                    - ↑ `Ecm.cabinet_by_key`
                    - ↑ `Ecm.cabinet_name`
                    - `Ecm.cabinet_of` — 문서함 열쇠(``cab…``) 또는 이름으로 문서함 하나 — 열쇠는 그대로 받고(목록을 안 묻는다), 이름은 ``cabinets`` 에서 꼭 맞는 이름을 먼저, 없으면 이름에 그 글이 든 것을 찾는다(대소문자 · 빈칸을 안 가린다). 여럿이 걸리거나 없으면 고르지 않고 후보를 다 보이며 ``ArgsError`` — 엉뚱한 문서함에 올리거나 그 목록을 그 부서의 것으로 읽게 된다.
                      - ↑ `ecm_base.Cabinet`
                      - ↑ `ecm_base.ArgsError`
                      - ↑ `Ecm.cabinets`
                      - `match_cabinets` — 문서함 이름으로 걸리는 문서함들 — 꼭 맞는 이름이 먼저, 없으면 이름에 그 글이 든 것(대소문자 · 빈칸을 안 가린다).
                        - ↑ `ecm_base._loose`
                      - `cabinet_miss_word` — 문서함 하나로 안 풀린 이름의 말 — 여럿이 걸렸으면 그 후보를, 없으면 볼 수 있는 문서함을 다 보인다.
                    - `Ecm.version` — 문서 정보 화면의 「최종 버전」 — 판을 올린 뒤 다음 판이 섰나 본다.
                      - `Ecm.doc_state` — 속성 화면을 한 번 읽어 판 · 잠금 · 보안등급 · 이름을 낸다 — 늘 새로 읽는다(판을 올린 뒤 바뀌기를 보는 자리가 부른다). 등급 칸을 못 읽으면 ``security`` 가 None 이다 — 그 판정은 ``security`` · ``check_readable`` 이 든다.
                        - `Ecm._property_page` — 문서의 속성 화면 HTML 을 읽기 문을 지나는 GET 하나로 받는다.
                          - ↑ `ecm_base._object_id`
                          - ↑ `Ecm._fetch`
                        - `ecm_base.PropertyPage` — 문서의 속성 화면 — 저장 몸이 실을 숨은 칸(``inputs``), 화면 스크립트의 갈래 값(``vars``), 권한 iframe 주소의 갈래 값(``frame``).
                          - `PropertyPage.parse` — 속성 화면 HTML 에서 숨은 칸 · 스크립트 변수 · 요소 id · 권한 iframe 주소의 갈래 값을 읽어 한 판을 짓는다.
                          - `PropertyPage.value` — 저장 몸에 실을 숨은 칸 하나의 값 — 없어도 되는 칸이 없으면 화면이 싣는 ``ABSENT_FIELD``, 그 밖의 칸이 없으면 ``EcmError``.
                            - ↑ `EcmError`
                          - `PropertyPage.security` — 화면의 숨은 등급 칸 둘과 핵심기술 표시로 짓는 보안등급 — 등급 칸이 없거나 모르는 값이면 None.
                            - `PropertyPage.security_level` — 화면의 숨은 등급 칸(``SECURITY_FIELD``)이 든 글자 그대로 — 없으면 빈 글자.
                            - `Security` — 문서의 보안등급 · 공개 — 속성 화면의 숨은 칸 그대로. ``core`` 는 핵심기술 표시(``CORE_VAR``)다.
                              - `Security.name` — 등급 · 공개 짝의 화면 이름 — 화면에 없는 짝이면 등급 이름 뒤에 그 짝을 붙인다.
                                - ↑ `level_name`
                              - `Security.classified` — 기밀 등급(``CLASSIFIED_LEVELS``)인가.
                              - `Security.ask_before_ai` — 글자를 대화로 들이기 전에 사람에게 물어야 하나 — 기밀이거나 핵심기술 문서다.
                                - ↑ `Security.classified`
                          - ↑ `PropertyPage.security_level`
                          - `PropertyPage.has_element` — 화면에 그 id 의 요소가 있나.
                          - `PropertyPage.unmeasured` — 이 손이 잰 문서의 꼴이 아니면 그 까닭 — 맞으면 빈 글자. 어긋난 자리는 ``unmeasured_part`` 가, 말은 ``unmeasured_reason`` 이 든다.
                            - `PropertyPage.unmeasured_part` — 이 손이 잰 꼴과 어긋난 첫 자리 — (어디: frame · page · vars · check, 칸, 그 값) 또는 None. 권한 칸이 없으면 ("frame", "", "").
                              - ↑ `PropertyPage.has_element`
                            - `unmeasured_reason` — 잰 꼴과 어긋난 자리(``PropertyPage.unmeasured_part``)를 사람에게 할 까닭으로 옮긴다.
                          - ↑ `PropertyPage.unmeasured_part`
                        - `ecm_base.DocState` — 문서 하나의 속성 화면 한 번 읽기 — 판 · 잠금 · 보안등급 · 이름. 못 읽은 칸은 빈 글자 · ``None`` 이다.
                        - `ecm_base.property_value` — 문서 정보 화면의 표에서 머리 칸 ``label`` 아래 값 — 머리 줄 하나 · 값 줄 하나의 표다.
                    - ↑ `Ecm.doc_state`
                    - ↑ `Ecm._property_page`
                    - `Ecm.checkout` — 편집 열기 첫 걸음 — 서버가 그 문서를 이 사람 이름으로 잠근다.
                      - ↑ `ecm_base._object_id`
                      - ↑ `Ecm._ajax`
                      - ↑ `ecm_base.Ticket`
                      - ↑ `ecm_base.EcmError`
                    - `Ecm.cancel_checkout` — 편집취소의 서버 걸음 — 화면이 에이전트 줄 앞에 보내는 요청. 이것만으로는 잠금이 안 풀렸다(쟀다) — ``cancel_edit`` 가 잇는다.
                      - ↑ `Ecm._ajax`
                      - ↑ `ecm_base._object_id`
                    - `Ecm.list` — 문서함의 한 쪽 — 새것부터. 비우면 내 문서함, ``cabinet`` 이면 그 부서 · 프로젝트 문서함(``cabinets`` 의 열쇠) · 거기에 ``folder`` 까지 주면 그 폴더에 바로 든 문서, ``box`` 면 왼쪽 메뉴의 다른 목록(``BOXES``). 내 문서함만이면 ``folder`` 는 목록 줄의 ``folder_id``. ``sort`` · ``file_type`` 은 화면의 머리 글 · 모아보기(``SORTS`` · ``FILE_TYPES``).
                      - ↑ `ecm_base.ArgsError`
                      - ↑ `Ecm._list_params`
                      - ↑ `Ecm._ajax`
                      - `_doc` — 목록 답의 줄 하나 → ``Doc`` — 칸마다 앞에 댄 이름부터 찬 값을 쓴다.
                        - `ecm_base.Doc` — 목록의 문서 한 줄. ``object_id`` 가 여는 열쇠다.
                    - `Ecm.count` — 목록과 같은 칸으로 건수(``MI_DOC_COUNT``)를 받는다 — 수가 아니면 ``EcmError``.
                      - ↑ `Ecm._list_params`
                      - ↑ `Ecm._ajax`
                      - ↑ `ecm_base.EcmError`
                    - `Ecm.view` — 열기 첫 걸음 — 에이전트에 보낼 값을 받는다.
                      - ↑ `ecm_base._object_id`
                      - ↑ `Ecm._ajax`
                      - ↑ `ecm_base.Ticket`
                      - ↑ `ecm_base.EcmError`
                    - `Ecm.current_key` — 판이 오른 문서의 옛 열쇠 → 지금 판의 열쇠 — 화면의 「보기(최신버전)」와 같은 보기 첫 걸음(``MS_CURRENT_YN=T``). 파일은 안 온다.
                      - ↑ `ecm_base._object_id`
                      - ↑ `Ecm._ajax`
                      - ↑ `ecm_base.EcmError`
                    - `Ecm.history` — 판 이력 — 속성 화면 「변경이력」 탭과 같은 두 읽기(건수 · 한 쪽). (모든 판의 수, 이 쪽의 판들 — 새 판부터). 문서 쪽 열쇠 (``doc…``)로 묻는다 — 문서 열쇠(판마다 다르다)로 물으면 0 판이 온다.
                      - ↑ `ecm_base.ArgsError`
                      - `Ecm.doc_key` — 문서 열쇠(판마다 바뀐다)의 문서 쪽 열쇠(``doc…`` — 판이 올라도 같다) — 속성 화면의 숨은 칸 ``MS_DOC_ID``. 판이 오른 문서는 ``"doc" + 문서 열쇠`` 가 아니다 — 그 꼴로 물으면 역할 목록이 빈 답(null)으로 와 권한 저장이 걸려 있던 명단을 지운다.
                        - `Ecm.property_page` — 문서의 속성 화면 — 저장 몸이 실을 숨은 칸 · 화면의 갈래 값 · 권한 iframe 의 갈래 값.
                          - ↑ `ecm_base.PropertyPage`
                          - ↑ `Ecm._property_page`
                        - ↑ `ecm_base.EcmError`
                      - `Ecm._history_total` — 판 이력의 건수 읽기 — 그 문서의 모든 판의 수(못 읽으면 0).
                        - `Ecm._json` — ``json.do`` 읽기 하나 — 답은 앞에 빈 줄이 붙은 JSON 배열(없으면 ``null``)이다.
                          - ↑ `Ecm._fetch`
                          - `json_text` — json.do 의 답 바이트를 글로 푼다 — ``Content-Type`` 의 문자셋으로(못 푸는 바이트는 바꿔) 앞뒤 빈 줄을 뗀다.
                            - ↑ `charset_of`
                          - ↑ `ecm_base.EcmError`
                      - `Ecm._history_page` — 판 이력의 한 쪽 읽기 — 새 판부터. 답이 목록이 아니면 ``EcmError``.
                        - ↑ `Ecm._json`
                        - ↑ `ecm_base.EcmError`
                        - `ecm_base.Version` — 판 이력의 한 줄 — ``object_id`` 는 그 판의 열쇠(read · open 이 받는다). 지금 판이면 ``current``.
                    - ↑ `Ecm._history_total`
                    - ↑ `Ecm._history_page`
                    - `Ecm.security_log` — 보안등급 변경 이력 — (때, 바꾼 이, 앞 등급 이름, 뒤 등급 이름). 「변경이력」 탭의 보안등급 표와 같은 읽기.
                      - ↑ `Ecm.doc_key`
                      - ↑ `Ecm._json`
                    - `Ecm.use_counts` — 활용 건수 — 「활용」 탭의 첨부 · 열람 · 복사 · 추천 수.
                      - ↑ `Ecm._json`
                      - ↑ `Ecm.doc_key`
                    - `Ecm.menu` — 그 문서에 지금 할 수 있는 것 — 우클릭 메뉴의 (이름, 켜졌나). 화면이 문서를 누를 때 묻는 조회 POST 하나다.
                      - ↑ `ecm_base._object_id`
                      - ↑ `_answer`
                      - ↑ `Ecm._post`
                    - `Ecm.checked_out_by_me` — 잠근 이가 나인가 — 편집취소 화면이 먼저 묻는 읽기(``checkuser``). 안 잠긴 문서도 거짓이다.
                      - ↑ `Ecm._ajax`
                      - ↑ `ecm_base._object_id`
                    - `Ecm.notices` — 왼쪽 「ECM 알림」 숫자 — 받은 · 보낸 권한 · 보안등급 · 검토 요청.
                      - ↑ `Ecm._ajax`
                    - `Ecm.personal_key` — 내 사람 열쇠(``usr…``) — 메인 화면이 든다.
                      - ↑ `Ecm._main_page`
                      - ↑ `ecm_base.EcmError`
                    - `Ecm.folders_named` — 볼 수 있는 모든 문서함에서 이름에 그 글이 든 폴더 — 상세검색의 「폴더 검색」과 같은 요청 하나. (문서함 열쇠, 폴더 열쇠, 폴더 이름, 서버가 준 경로 — 「문서함/폴더/…」). 경로는 가르지 않는다 — 문서함 · 폴더 이름에 / 가 들 수 있다(「관세/외국환…」).
                      - ↑ `ecm_base.folder_name`
                      - ↑ `Ecm.personal_key`
                      - ↑ `Ecm._post`
                      - ↑ `json_text`
                      - ↑ `ecm_base.EcmError`
                    - `Ecm.search_all` — 전사 검색 · 본문 검색 — 상세검색의 검색엔진 요청(``getDocListEcmEsSearch``) 하나. (모두 몇 건, 이 쪽의 줄). 내가 볼 수 있는 문서만 온다.
                      - ↑ `ecm_base.check_search_page`
                      - ↑ `Ecm._main_page`
                      - ↑ `ecm_base.EcmError`
                      - `search_body` — 화면의 검색 몸 — ``q=posmeta:{…}`` · 쪽 · 건수. 등급은 화면처럼 쉼표로 잇고 끝에도 쉼표를 붙인다.
                        - ↑ `ecm_base.check_search`
                      - `_answer_search` — 검색 답 — ``MB_RTN_VALUE`` 가 없고 ``gsa_error_key`` 가 까닭을 든다(빈 글자면 됐다).
                        - ↑ `charset_of`
                        - ↑ `ecm_base.EcmError`
                      - ↑ `Ecm._post`
                      - `parse_hits` — 검색 답의 ``gsa_data_key``(XML 글) → (모두 몇 건, 줄들). 줄의 칸은 ``<MT N="이름" V="값"/>`` 이다.
                        - `ecm_base.Hit` — 전사 검색의 한 줄 — ``object_id`` 는 지금 판의 열쇠다(read · open 이 받는다).
                    - ↑ `Ecm._json`
                    - `Ecm.company` — 그 사람의 회사 열쇠(``com…``) — 메인 화면이 든다.
                      - ↑ `Ecm._main_page`
                      - ↑ `ecm_base.EcmError`
                    - ↑ `Ecm.property_page`
                    - `Ecm.security` — 문서의 보안등급 — 속성 화면 읽기 하나(파일을 안 받는다). 칸이 없거나 모르는 등급이면 ``SecurityUnread``. 세션이 끊긴 것과 문서 열쇠의 꼴이 틀린 것(``ArgsError`` — 서버에 안 갔다)은 그대로 올린다 — 세션 · 열쇠를 고치면 읽히는 자리다.
                      - ↑ `Ecm.property_page`
                      - ↑ `ecm_base.SessionMissing`
                      - ↑ `ecm_base.SessionExpired`
                      - ↑ `ecm_base.ArgsError`
                      - ↑ `ecm_base.EcmError`
                      - ↑ `ecm_base.SecurityUnread`
                    - ↑ `Ecm.doc_key`
                    - `Ecm.roles` — 그 문서에 걸린 역할 전부 — 권한 iframe 이 처음 그리는 그 목록(소유자는 안 든다). ``doc_key`` 는 속성 화면의 ``MS_DOC_ID`` — 안 주면 속성 화면을 한 번 더 읽어 받는다.
                      - ↑ `Ecm._json`
                      - ↑ `Ecm.doc_key`
                      - ↑ `ecm_base.EcmError`
                      - ↑ `ecm_base.Grant`
                    - `Ecm.favorites` — 그 문서가 든 즐겨찾기 폴더 — 화면이 저장 몸의 ``favFolderList`` 에 쉼표로 이어 싣는다.
                      - ↑ `Ecm._json`
                      - ↑ `Ecm.doc_key`
                    - `Ecm.people` — 이름(일부)으로 사람을 찾는다 — 권한 화면의 성명 탭과 같은 요청. 메일 ID · 사번으로는 안 찾는다(서버가 이름만 본다).
                      - ↑ `ecm_base.person_name`
                      - ↑ `Ecm._json`
                      - ↑ `ecm_base.Person`
                    - `Ecm.organs` — 부서 이름(일부)으로 부서를 찾는다 — 권한 화면의 조직 탭 찾기.
                      - ↑ `ecm_base.organ_name`
                      - ↑ `Ecm._json`
                      - `_organ` — 조직 답의 줄 하나 → ``Organ`` — 수 칸이 수가 아니면 0 으로 둔다.
                        - `ecm_base.Organ` — ECM 조직도의 부서 하나 — ``code`` 를 ``org:<코드>`` 로 준다.
                    - `Ecm.sub_organs` — 그 부서 바로 아래 부서.
                      - ↑ `Ecm._json`
                      - `ecm_base._dept_code` — 부서 코드의 꼴을 가려 다듬은 값을 낸다 — 아니면 ``ArgsError``.
                        - ↑ `ArgsError`
                      - ↑ `_organ`
                    - `Ecm.members` — 그 부서에 바로 든 사람 — 화면이 조직을 칸에 옮길 때 펼치는 그 명단.
                      - ↑ `ecm_base._dept_code`
                      - ↑ `Ecm._json`
                      - ↑ `ecm_base.Person`
                    - `Ecm.save_access` — 속성 화면의 「수정하기」와 같은 저장 — 속성 칸은 화면이 실을 값 그대로, 권한은 ``grants`` 전체로 바꾼다.
                      - `Ecm._save` — 속성 저장 POST 하나를 보내고 답의 문서 열쇠가 그 화면의 것인가 본다 — 다르면 ``what``(권한 · 속성)을 화면에서 보라고 진다.
                        - ↑ `_answer`
                        - ↑ `Ecm._post`
                        - ↑ `ecm_base.EcmError`
                      - `property_save_body` — 속성 화면의 getDocInfoData 가 짓는 몸 — 속성 칸은 그 화면의 값, 권한 명단은 ``grants`` 전체다.
                        - ↑ `ecm_base.Refused`
                        - ↑ `ecm_base.outside_roles`
                        - ↑ `page_tags`
                    - `Ecm.save_props` — 속성 화면의 「수정하기」와 같은 저장 — 이름 · 태그 · 완료일만 ``props`` 로 바꾸고, 권한 명단은 지금 그대로 싣는다.
                      - ↑ `Ecm._save`
                      - ↑ `property_save_body`
                    - ↑ `Ecm._save`
                  - ↑ `ecm_base.url_from_env`
                  - ↑ `ecm_base.session_path`
                  - `report` — 명령이 멈춘 까닭을 표준 오류에 내고 종료 값을 낸다 — 뜻은 머리말 「무엇을 내나」. 부르는 쪽(company_ecm.py)도 같은 표로 낸다.
                    - ↑ `default_app.DefaultAppNeeded`
                    - ↑ `ecm_base.SessionMissing`
                    - ↑ `ecm_base.SessionExpired`
                    - ↑ `ecm_base.Classified`
                    - ↑ `ecm_base.SecurityUnread`
                    - ↑ `ecm_base.Stale`
                    - ↑ `ecm_base.ArgsError`
                - ↑ `ecm_base.ArgsError`
              - `grant_spec` — 줄 말 하나를 사람들로 풀어(조직은 그 순간의 부서원으로 펼치고, 사람은 꼭 한 사람을 골라) 그 칸으로 뒤 명단에 얹는다.
                - ↑ `is_org_spec`
                - `_expand_organ` — 부서를 사람으로 펼친다 — 화면처럼 바로 든 사람만, ``with_subs`` 면 아래 부서를 다 내려간다.
                - `_pick_organ` — 「org:부서코드」 또는 「org:부서 이름」 하나를 부서 하나로 — 이름이 여럿에 걸리면 코드와 함께 다 보이며 멈춘다.
                  - ↑ `ecm_base.spec_kind`
                  - ↑ `ecm_base.Organ`
                  - ↑ `ecm_base.ArgsError`
                - ↑ `ecm_base.ArgsError`
                - `_pick_person` — 「이름」 · 「이름/메일ID」 · 「이름/메일 주소」 하나를 사람 하나로 — 여럿이면 고르지 않고 후보를 다 보이며 멈춘다.
                  - ↑ `same_mail`
                  - ↑ `ecm_base.ArgsError`
              - `revoke_spec` — 거둘 말 하나를 사람 열쇠들로 풀어(조직은 부서원으로 펼치고 지킬 줄은 빼며, 사람은 명단에서 꼭 한 사람) 뒤 명단에서 뺀다.
                - ↑ `is_org_spec`
                - ↑ `_expand_organ`
                - ↑ `_pick_organ`
                - ↑ `ecm_base.ArgsError`
              - `stop_on_problems` — 못 푼 말이 있으면 일부만 짓지 않고 그 말들을 다 대며 ``ArgsError`` 로 멈춘다.
                - ↑ `ecm_base.ArgsError`
              - `AccessPlan` — 권한을 바꾸는 한 판 — 지금 명단 · 바뀔 명단과, 사람에게 보일 더함 · 뺌 · 옮김. ``token`` 이 확인 열쇠다.
                - ↑ `ecm_base.Grant`
                - `AccessPlan.token` — 확인 열쇠 — 문서와 지금 · 바뀔 명단의 지문(``access_token``).
                  - `access_token` — 지금 명단과 바뀔 명단의 지문 — 미리 본 뒤 누가 명단을 바꿨거나 바랄 명단이 달라지면 열쇠가 달라진다.
                    - ↑ `ecm_base.token`
                    - ↑ `ecm_base.grants_key`
          - `access_done_words` — 권한을 바꾼 뒤의 말 — 더함 · 뺌 · 옮김 수와 다시 읽은 명단.
            - ↑ `_print_grants`
          - `apply_access` — 미리 본 한 판을 보낸다 — 열쇠가 맞고 그 사이 명단이 그대로일 때만. 보낸 뒤 명단과 속성(보안등급 · 공개 · 폴더 · 이름)을 다시 읽어 바란 그대로인가 본다.
            - ↑ `ecm_base.token`
            - ↑ `ecm_base.Stale`
            - ↑ `document_gate`
            - ↑ `access_token`
            - ↑ `watch`
            - ↑ `ecm_base.grants_key`
            - ↑ `ecm_base.EcmError`
            - ↑ `stop_on_drift`
            - ↑ `drifted`
        - ↑ `cmd_apply_props`
        - ↑ `cmd_cabinets`
        - ↑ `cmd_can`
        - ↑ `cmd_cancel_edit`
        - ↑ `cmd_change`
        - ↑ `cmd_checkin`
        - ↑ `cmd_count`
        - ↑ `cmd_default_app`
        - ↑ `cmd_doc`
        - ↑ `cmd_edit`
        - ↑ `cmd_find_folder`
        - ↑ `cmd_folders`
        - ↑ `cmd_latest`
        - ↑ `cmd_link`
        - ↑ `cmd_list`
        - ↑ `cmd_notices`
        - ↑ `cmd_open`
        - ↑ `cmd_preview_access`
        - ↑ `cmd_preview_checkin`
        - ↑ `cmd_preview_props`
        - ↑ `cmd_preview_register`
        - ↑ `cmd_read`
        - ↑ `cmd_register`
        - ↑ `cmd_search`
        - ↑ `cmd_session`
        - ↑ `cmd_versions`
        - ↑ `cmd_who`
        - ↑ `kept_text`
        - ↑ `Change`
        - `unmeasured_word` — 안 잰 앱의 바꿀 것을 한 줄로 — 표의 unmeasured 칸에서 짓는다.
          - ↑ `Change`
      - ↑ `Finger`
      - ↑ `_pre_change`
      - ↑ `_pre_edit`
      - ↑ `_pre_find_folder`
      - ↑ `_pre_folders`
      - ↑ `_pre_list`
      - ↑ `_pre_props`
      - ↑ `_pre_register`
      - ↑ `_pre_search`
      - ↑ `access_specs`
      - ↑ `checkin_inputs`
      - ↑ `cmd_access`
      - ↑ `cmd_apply_access`
      - ↑ `cmd_apply_props`
      - ↑ `cmd_cabinets`
      - ↑ `cmd_can`
      - ↑ `cmd_cancel_edit`
      - ↑ `cmd_change`
      - ↑ `cmd_checkin`
      - ↑ `cmd_count`
      - ↑ `cmd_default_app`
      - ↑ `cmd_doc`
      - ↑ `cmd_edit`
      - ↑ `cmd_find_folder`
      - ↑ `cmd_folders`
      - ↑ `cmd_latest`
      - ↑ `cmd_link`
      - ↑ `cmd_list`
      - ↑ `cmd_notices`
      - ↑ `cmd_open`
      - ↑ `cmd_preview_access`
      - ↑ `cmd_preview_checkin`
      - ↑ `cmd_preview_props`
      - ↑ `cmd_preview_register`
      - ↑ `cmd_read`
      - ↑ `cmd_register`
      - ↑ `cmd_search`
      - ↑ `cmd_session`
      - ↑ `cmd_versions`
      - ↑ `cmd_who`
      - ↑ `kept_text`
      - ↑ `unmeasured_word`
    - `precheck` — 서버 없이 가릴 수 있는 값을 세션보다 먼저 가린다 — 칸 하나는 ``ARG_CHECKS``, 칸 여럿은 그 손가락의 ``check``. 못 쓸 값이면 ``ArgsError``(조각 파일이 없거나 UTF-8 이 아닐 때도 · 받은 파일이 오피스 꼴이 아니면 ``EcmError``). 아무것도 안 건드린다.
      - ↑ `Finger`
      - ↑ `_pre_change`
      - ↑ `_pre_edit`
      - ↑ `_pre_find_folder`
      - ↑ `_pre_folders`
      - ↑ `_pre_list`
      - ↑ `_pre_props`
      - ↑ `_pre_register`
      - ↑ `_pre_search`
      - ↑ `access_specs`
      - ↑ `checkin_inputs`
      - ↑ `cmd_access`
      - ↑ `cmd_apply_access`
      - ↑ `cmd_apply_props`
      - ↑ `cmd_cabinets`
      - ↑ `cmd_can`
      - ↑ `cmd_cancel_edit`
      - ↑ `cmd_change`
      - ↑ `cmd_checkin`
      - ↑ `cmd_count`
      - ↑ `cmd_default_app`
      - ↑ `cmd_doc`
      - ↑ `cmd_edit`
      - ↑ `cmd_find_folder`
      - ↑ `cmd_folders`
      - ↑ `cmd_latest`
      - ↑ `cmd_link`
      - ↑ `cmd_list`
      - ↑ `cmd_notices`
      - ↑ `cmd_open`
      - ↑ `cmd_preview_access`
      - ↑ `cmd_preview_checkin`
      - ↑ `cmd_preview_props`
      - ↑ `cmd_preview_register`
      - ↑ `cmd_read`
      - ↑ `cmd_register`
      - ↑ `cmd_search`
      - ↑ `cmd_session`
      - ↑ `cmd_versions`
      - ↑ `cmd_who`
      - ↑ `kept_text`
      - `_dest` — ARGS 의 열쇠 → argparse 가 그 값을 두는 이름 — ``dest`` 를 안 줬으면 첫 깃발에서 짓는다.
      - `_check_query` — who 의 찾는 말 — 이름(일부)은 두 글자부터, org: 뒤는 부서 코드이거나 두 글자부터.
        - ↑ `ecm_base.spec_kind`
        - ↑ `ecm_base.organ_name`
        - ↑ `ecm_base.person_name`
  - ↑ `ecm.report`
  - `load_ep_session` — 형제 스킬 ep-login 의 ``ep_session`` 을 싣는다 — 받는 손을 돌리는 한 자리다.
  - `ecm.uses_agent` — 이 명령 한 판이 문서함 에이전트를 부르나 — 손가락 표의 ``agent`` 가 값이면 그 값, 함수면 그 인자로 가린다(read 는 남긴 글자가 있으면 에이전트를 안 부른다).
  - `ordinary_ready` — 이 로그온에 평소 EP 로그인이 있다고 볼 수 있나 — 형제 스킬 ep-login 의 읽기만 하는 답(``ep_session.ordinary_login``)을 받는다.
  - ↑ `ecm.run`
  - `SessionGone` — ecm.py 가 EXIT_SESSION 으로 끝났다 — session_first 의 expired 로 옮기는 신호. 메시지는 그 판의 ecm.py 가 표준 오류에 내려던 말이다.
  - `tell_no_session` — 받는 손이 세션을 못 세운 갈래(``got.code``)를 사람에게 할 말과 종료 값으로 옮긴다 — 로그인 끊김 · Edge 없음 · ECM 넘김은 ``EXIT_SESSION``, 받는 손의 고장은 ``EXIT_FAIL``.
- `main` — 명령줄 한 판 — 인자를 가리고(``checked_args``) 그 줄의 손을 부른다(``run``).
  - ↑ `checked_args`
  - ↑ `report`
  - ↑ `run`
<!-- /drawn:piece-map -->

## 손가락의 표 — 시나리오가 아니라 화면 패스

명령은 부탁 종류마다 짓지 않는다. 사람이 웹 앱에서 하는 단위 — **화면 하나를 열고 → 칸을 바꾸고 → 끝 단추를 누른다** — 를 패스로
삼고, 패스마다 출발 · 바꿀 것 · 끝을 손가락으로 연다. 모델은 `--help` 의 지도를 보고 그 자리에서 손가락을 잇는다 — 표에 없던 조합
(「메일로 온 문서 고쳐서 다시 올려」 = 메일의 열쇠 → `edit` + 바꿀 것 → `checkin`)도 새 명령 없이 선다.

- **한 사실은 한 표에** — 손가락의 표(`FINGERS` · `ARGS` · `EDIT_CHANGES` · `PASSES`)에서 명령줄 인자 · 세션이 드나 · 바꾸는가
  (`company_ecm.py` 가 세션 손을 먼저 받는 명령) · `--help` 의 지도가 다 선다. 안 하는 것과 사람이 어디서 하나는 `NOT_HERE` 하나가
  들고, 멈추는 말과 지도가 같은 줄을 읽는다. 회사에서 새 화면 동작을 재면 표의 한 줄과 그 일을 하는 손 하나를 더하고, 그 동작이
  `NOT_HERE` 에 있었으면 그 줄을 걷는다
- **인자와 값을 세션보다 먼저 한 번 가린다** — `company_ecm.py` 는 `ecm.checked_args`(명령줄 풀기 · `precheck`)로 서버 없이 가릴 수
  있는 값(열쇠의 꼴 · 파일 · 짝 · 사람 파일)을 가려 `--help` · 틀린 인자 · 틀린 값을 세션 없이 끝내고, 가린 인자를 `ecm.run` 에 넘긴다. 세션을 먼저 받으면 세션이 없는
  PC 에서 `--help` 가 「Edge 에 못 붙었다」로 끝나고, 열쇠 하나를 잘못 친 사람이 로그인을 다시 하고 나서야 그 말을 듣는다. 칸 하나는
  `ARG_CHECKS`, 칸 여럿은 손가락의 `check` 가 들고, 말은 손 안의 같은 함수가 내 세션 뒤의 말과 같다
- 깔린 자리에서 이 파일을 싣는 앱(메일 비서)이 부르는 이름은 머리말에 적었다 — 표를 고쳐도 그 이름 · 꼴은 그대로 둔다

## 세분의 선 — 사람의 누름과 모델의 부름

| 사람이 웹 앱에서 | 누름 | 모델의 부름 | 어디서 묶고 어디서 뗐나 |
|---|---|---|---|
| 찾기 칸에 낱말 · 기간 → 목록 | 3 ~ 5 | `list`(부서는 `--cabinet <이름>` · 모르면 `all`) | 거르기 · 문서함 고르기는 인자로 — 한 부름 |
| 폴더 나무를 펼쳐 폴더를 고른다 | 깊이 + 1 | `folders --find` · 등록의 `--folder-path` | 나무 훑기를 손 안에서 — 층마다 부르지 않는다 |
| 보기 → 읽기 → 창 닫기 | 2 ~ 3 | `read` | 띄우기 · 닫기 · 뽑기를 한 부름에 — 떼면 모델이 열린 창을 들고 「그 문서만 닫는다」를 지켜야 한다 |
| 편집 → 오피스에서 고침 k 개 → 저장 · 닫기 → 편집완료(다음 판 · 수정 내용) | k + 5 | `edit`(+ 바꿀 것 · `--desc`) → `checkin --confirm` | 열기와 고침 k 개를 한 부름에, 올리기는 떼어 열쇠 뒤에 |
| 컨텐츠 등록 → 폴더 → 파일 → 보안 단추 → 저장 | 깊이 + 4 | `preview-register` → `register --confirm` | 칸은 한 부름에, 끝은 열쇠 뒤에 |
| 컨텐츠 속성 → 권한 칸에 n 명 → 수정하기 | 2n + 4 | `preview-access` → `apply-access --confirm` | n 명을 한 부름에 — 사람마다 부르면 속성 화면 · 명단 · 회사 열쇠를 n 번 다시 읽는다 |
| 컨텐츠 속성 → 이름 · 태그 k 개 · 완료일 → 수정하기 | k + 4 | `preview-props` → `apply-props --confirm` | 셋을 한 부름에 — 권한 패스와 같은 저장이라 같은 문을 지난다 |
| 우클릭 → 편집취소 → 확인 | 3 | `cancel-edit` | 열린 편집 창 닫기 · 서버 걸음 · 에이전트 줄 · 다시 읽기를 한 부름에 — 떼면 서버 걸음만 가고 잠금이 남는다 |
| 상세검색 → 칸 k 개 → 검색 | k + 2 | `search` | 칸은 인자로 — 한 부름 · 한 요청 |
| 컨텐츠 속성 → 변경이력 탭 · 활용 탭 | 2 ~ 4 | `versions`(`--more`) | 두 탭을 한 부름에 |

- **더 묶지 않는 자리** — 편집 패스는 ECM 화면 · 오피스 · 에이전트의 편집완료 창을 건너 한 부름에 못 든다. 잠금은 패스의 처음에
  서고, 올리기는 사람이 고친 자리를 본 뒤에 선다. 그 사이 모델이 드는 상태는 문서 열쇠와 받은 파일 경로 둘이고, 손이 부를 때마다
  그 경로가 그 문서를 편집으로 받은 파일인가를 다시 잰다(`checkout_file`)
- **모델이 부르는 단위를 더 쪼개지 않는 자리** — 클릭 단위 손가락(단추 하나 · 칸 하나)은 짓지 않는다. 열린 화면의 상태를 모델이 들고 다니게 되고, 끝 단추의
  문(열쇠 · 다음 판 고정 · 사람 문서 안 닫기)이 모델 손으로 넘어간다

## 찾고 읽기

목록 · 찾기 · 건수는 내 문서함과, 그 사람이 볼 수 있는 부서 · 프로젝트 문서함에서 받는다(`Ecm.cabinets` · `Ecm.list(cabinet=…)` ·
`Ecm.count`). 부서 · 프로젝트 문서함 목록 요청은 폴더 칸을 안 싣는다 — 그래서 `--cabinet` 과 `--folder` 를 함께 주면 멈춘다(그대로
보내면 문서함 전체가 그 폴더의 목록인 듯 온다). 메인 화면(문서함 목록 · 회사 열쇠)은 명령 한 번에 한 번만 받는다.

읽기는 문서 하나를 PC 의 ECM 에이전트로 받아 보기로 열고(`open_document`), 에이전트가 띄운 창(오피스 · Acrobat)을 닫은 뒤 받은
파일의 글자를 스킬 drm-office-read 의 읽는 손으로 뽑는다(`read_document`). 닫는 것이 먼저다 — 오피스가 그 파일을 쥐고 있으면 읽는
손이 파일 머리를 못 읽는다. 에이전트는 받은 파일을 그 확장자의 기본 앱으로 **화면에 띄운다** — 이 손은 사람이 보는 대화에서만 쓴다.

폴더 나무는 문서함 바로 아래부터 한 층씩 내려가며 훑는다(`walk_folders`) — 아래 폴더가 있는 폴더만 열고, 찾으면 거기서 멈추며, 요청이
`FOLDER_WALK_MAX` 를 넘으면 경로로 달라고 멈춘다. 경로(`resolve_folder`)는 층마다 이름이 꼭 맞는 폴더 하나만 따라간다 — 일부만 맞는
폴더를 고르면 엉뚱한 폴더에 올린다. `folders --find` 는 나무를 한 번 끝까지 훑어 꼭 맞는 이름을 먼저 내고, 없을 때만 이름에 그 글이
든 폴더를 후보로 낸다(`match_folders` — 대소문자 · 빈칸을 안 가린다). 후보는 고르지 않는다 — 사람이 고른 열쇠 · 경로로 간다.

문서함 안 폴더의 목록은 `--cabinet` 과 `--folder`(폴더 열쇠)를 함께 받아 화면의 나무 클릭 꼴(`F_LIST_FOLDER`)로 묻는다 — 그 폴더에 바로
든 문서만 온다. 서버는 폴더 열쇠만 보므로 문서함은 사람에게 보일 머리일 뿐이다. 왼쪽 메뉴의 다른 목록(`--box`)은 문서함을 안 가린다.

전사 검색(`search`)은 상세검색의 검색엔진 요청 하나다. 사람은 문서를 이름으로 말하므로 자리 인자로 준 낱말이 제목 낱말이 된다 — 따옴표
없이 셸이 갈라 여럿으로 와도, `--title` 값 곁에 남아도 한 제목 낱말로 잇는다. 0 건이면 「이 칸 · 이 범위로 못 찾았다」 와 아직 안 쓴 넓힐
길(낱말 하나만 · 본문 · 전사)을 댄다(`search_widen`) — 0 건을 「없다」 로 옮기지 않게. 기본 범위는 「내 문서함들」 — 메인 화면의 `s_deptCabinets` 를 그대로 실어 볼 수
있는 문서함 전부를 한 요청으로 찾는다. 「전사」는 그 칸을 비운다. 보안등급 거르기는 문서함 칸이 비면 서버가 늘 0 건을 내므로 전사
범위에서는 세션 전에 멈춘다 — 0 건을 「없다」로 읽게 된다. 폴더 이름 찾기는 둘이다 — `find-folder` 는 모든 문서함에서 요청 하나로 이름
일부를 찾아 후보를 내고, `folders --find` 는 문서함 하나의 나무를 훑어 꼭 맞는 이름을 먼저 낸다(등록 경로 `--folder-path` 가 그
나무 길을 쓴다). 둘 다 고르지 않는다.

판이 오른 문서의 옛 열쇠는 옛 판을 가리킨다. `latest` 는 화면의 「보기(최신버전)」 꼴로 지금 판의 열쇠를 받고, `versions` 는 판 이력을
doc 열쇠(속성 화면의 `MS_DOC_ID` — 판이 올라도 같다)로 묻는다. 역할 목록 · 즐겨찾기도 그 열쇠로 묻는다 — `doc` + 문서 열쇠는 첫 판에만
맞고, 판이 오른 문서에서는 빈 명단이 와 권한 저장이 걸린 명단을 지운다.

한 손이 낸 열쇠를 다음 손이 그대로 받게 한다. 옛 열쇠로 읽기(`read` — 남긴 글자도)는 준 판 그대로 읽되 등급 문을 지난 뒤 같은
「보기(최신버전)」 걸음으로 지금 판을 물어, 지난 판이면 머리 한 줄로 지금 판의 열쇠를 댄다(`tell_superseded`) — 말없이 옛 판을 지금
판으로 읽게 두지 않는다. 그 걸음은 받는 요청과 같은 꼴이라 등급 문 앞에 안 선다. 올리기(`checkin`)는 판이 오른 뒤 같은 걸음으로 새
판의 열쇠를, 등록(`register`)은 서버가 답한 새 문서의 열쇠를 낸다. 문서 링크(`link`)는 화면의 「URL 복사」 가 내는 꼴을 열쇠만으로
짓는다(`doc_link`) — 그 화면 동작은 부를 때마다 서버에 임시 파일을 지어 부르지 않는다. 지금 판의 열쇠와 속성 화면의 doc 열쇠로 짓고,
새 문서는 첫 판의 doc 열쇠(`doc` + 문서 열쇠)라 묻지 않는다.

`--cabinet` 은 열쇠 · 이름 · `all` 을 받는다(`Ecm.cabinet_of`). 이름은 꼭 맞는 것을 먼저, 없으면 이름에 그 글이 든 것을 찾고, 여럿이
걸리면 고르지 않고 후보를 다 보이며 멈춘다 — 엉뚱한 문서함에 올리거나 그 목록을 그 부서의 것으로 읽게 된다. 문서함 전부를 한 요청으로
묻는 꼴은 안 쟀다 — `all` 은 내 문서함과 메인 화면이 든 문서함을 하나씩 묻고(`CABINET_ALL_MAX` 곳까지 · 제 부서가 맨 앞), 넘는
문서함은 이름을 대고 안 묻는다. 열쇠로 준 문서함의 목록 머리는 열쇠 그대로이고, 이름 · `all` 로 푼 것만 이름을 붙인다.

## 편집 — 잠그고 열기 · 열린 창에서 고치기 · 미리 보고 다음 판으로

`edit_document` 는 워드 · 엑셀 · 파워포인트 문서(`OFFICE_BY_EXT`)만 서버에서 잠그고 에이전트로 읽기 쓰기로 연다. 잠그기 전에 등급 ·
꼴 · 바꿀 것(`check_changes` — 그 꼴에 넣을 수 있는 파일인가 · 조각에 줄바꿈이 없나 · 조각끼리 겹치지 않나) · 기본 앱을 본다 — 끝까지
못 가는 판에 잠그면 사람이 모르는 잠금이 남는다.

고치기는 모델이 오피스 COM 을 짓지 않고 손이 한다(`change_document` → `change_doc.ps1`). 손은 에이전트가 띄운 그 창의 문서를 전체
경로로 찾는다(`office_doc.ps1` — 셸이 띄운 오피스는 포커스를 잃기 전까지 ROT 에 안 올라, 창마다 `AccessibleObjectFromWindow` 로 앱을
받는다). 같은 파일을 한 벌 더 열지 않고, 문서를 닫거나 앱을 끄지 않는다 — 올리기가 닫는다.

- **조각은 꼭 한 번** — 문서 글자 전체(파워포인트는 장마다 글 칸 · 표 칸 · 묶음 안, 워드는 이야기 모두, 엑셀은 값 칸)에서 세어 0 번 ·
  여러 번이면 고르지 않는다. 엑셀의 수식 칸에 걸리면 안 고친다. 빈칸 · 탭의 수는 너그럽게 맞추고 줄은 안 건넌다 — 추출한 글자와
  문서의 빈칸이 달라도 같은 조각을 찾는다
- **하나라도 못 고치면 하나도 안 고친다** — 조각 · 넣을 자리 · 파일을 다 가린 뒤에야 문서를 건드린다. 조각 바꾸기가 먼저고 끼워 넣기가
  뒤다 — 조각은 원래 문서를 가리키는 말이다
- **어느 앱이 어느 바꿀 것을 받나는 표가 든다** — `EDIT_CHANGES` 의 `apps` 칸을 `check_changes` 가 읽는다. 받되 어느 PC 에서도 안
  잰 앱은 `unmeasured` 칸이 들고 `--help` 가 「회사에서 안 쟀다」로 낸다 — 워드 갈래는 그 칸에 있다. 잠근 뒤 고치는 손이 멈추면 잠금은
  사람이 화면의 「편집취소」로만 풀어(그 요청은 안 쟀다), 고치기 전에 사람이 그 값을 안다
- **편집취소는 그 문서를 잠근 이가 나일 때만** — `cancel_edit` 은 `checkuser` 로 잠근 이를 보고(남의 편집은 버리지 않는다), 편집으로
  받은 그 문서의 창을 `-RequireClean` 으로 닫은 뒤(저장 안 된 고침이 있으면 `--discard` 없이 멈춘다) 서버 걸음과 에이전트 줄을 보내고
  다시 읽은 잠금으로 판정한다. 잠금을 푸는 것은 에이전트 줄이고, 창이 떠 있으면 에이전트는 「사용 중」으로 안 푼다 — 그래서 닫기가
  먼저다. 저장된 고침이 있던 창을 닫으면 에이전트의 편집완료 창이 뜨고 편집취소 뒤에도 남는다 — 손은 그 창을 누르지 않고 사람에게
  닫으라고 알린다
- **고친 판은 저장하되 창은 둔다** — 저장 안 된 고침이 없으면 저장하지 않는다(파워포인트는 고친 것 없이도 다시 쓴다). 아무것도 안
  고친 문서를 닫으면 에이전트가 판을 올리지 않고 잠금만 푼다

올리기는 두 부름이다. `prepare_checkin` 이 창의 고침을 저장하고 지금 판 · 잠금을 읽어 확인 열쇠를 낸다 — 열쇠는 문서 · 지금 판 · 수정
내용 · 미리 본 때 디스크의 그 파일 판(고친 시각 · 크기 — 오피스가 쥔 감긴 파일은 바이트를 못 읽는다)의 지문이다. `checkin_document`
는 열쇠를 다시 재어 맞을 때만 문서를 닫는데, 닫는 손(`close_view.ps1 -RequireClean`)은 창에 저장 안 된 고침이 있으면 닫지 않는다 —
미리 본 뒤 사람이 창에서 고친 것이 몰래 올라가지 않게. 닫은 뒤 에이전트의 편집완료 창에서 **늘 다음 판**을 골라 수정 내용과 함께
올리고 문서 정보의 최종 버전이 바뀌었나 본다. 같은 앱에 사람의 다른 문서가 남아 있으면 앱은 끄지 않고 그 문서만 닫는다 — 창이 시한
안에 안 뜨면 남은 문서 이름을 대고 멈추고, 사람이 그 문서들을 닫은 뒤 같은 명령을 다시 부르면 창에서 이어 간다.

## 새 문서 등록 — 미리 보기 · 확인 열쇠 · 올리기 · 다시 읽기

`plan_register` 가 못 할 까닭을 다 가린다 — 파일 · 문서함 · 보안 짝 · 그 폴더가 그 문서함의 것인가(나무에서 찾는다) · 이름 · 그 폴더의
같은 이름. 서버를 안 바꾸고(같은 이름 찾기 POST 는 읽기다) 확인 열쇠를 낸다 — 열쇠는 파일 바이트의 지문 · 자리 · 보안 짝 · 이름이다.
`register_document` 는 그 가림을 다시 다 돌려(그 사이 같은 이름이 섰을 수 있다) 열쇠가 맞을 때만 에이전트가 파일을 서버 임시 자리에
올리고 등록한 뒤, 목록에서 다시 읽어 폴더 · 보안등급이 고른 값인가 본다. 폴더를 등록 앞에서 보는 까닭 — 등록 뒤의 목록 견줌만으로는
남의 문서함에 이미 올라간 문서를 「실패」로 알리게 된다. 같은 이름이 있으면 올리지 않는다(다음 판은 편집의 몫이다).

## 바꾸는 요청은 닫힌 문으로만

바꾸는 요청은 편집 열기(`Ecm.checkout`) · 편집취소의 서버 걸음(`Ecm.cancel_checkout`)과 등록 화면의 두 POST · 속성 저장
POST(`Ecm._post` — 같은 이름 찾기 · 등록 · 권한 · 이름 · 태그 · 완료일 저장)만 짓는다. 같은 서비스 모음에 올리기 요청 · 지우기 · 동시편집
취소가 섞여 있어, 그 밖의 바꾸는 꼴과 잰 꼴 밖의 주소는 서버에 닿기 전에 `Refused` 로 막는다 — 읽기는 닫힌 목록(`READS` · json.do 의
`_is_json_read`), 편집 열기 · 편집취소는 부를 때 갈래 하나를 대야 여는 `_guard_edit` 가 든다. 조회지만 POST 인 셋(우클릭 메뉴 · 전사
검색 · 폴더 이름 찾기)도 `_post` 가 몸의 칸까지 그 꼴일 때만 보낸다 — 같은 자리의 이웃 POST 가 태그 일괄 · 보안등급 바꾸기다. 덮어쓰기 · 사람 문서 닫기 · 모르는 잠금이
구조상 안 나게 하려는 것이다.

확인 열쇠는 「미리 본 판 그대로 간다」를 손 안에서 지킨다. 사람이 「예」 했는지는 손이 모른다 — 미리 보기를 사람에게 보이고 답을
받는 일은 대화의 몫이고, 스킬 본문이 든다.

## 권한 — 미리 보기 · 확인 열쇠 · 저장 · 다시 읽기

권한(편집 · 복사 · 읽기)은 화면의 「컨텐츠 속성 → 수정하기」와 같은 저장 하나로 주고 거둔다. `plan_access` 가 지금 명단을 읽고
사람 · 조직을 ECM 검색으로 사람 열쇠까지 풀어 바뀔 명단과 확인 열쇠를 짓고(서버를 안 바꾼다), `apply_access` 가 그 열쇠가 맞고
그 사이 명단이 그대로일 때만 속성 저장 POST 하나(`Ecm.save_access`)를 보낸 뒤 명단과 다른 속성을 다시 읽어 본다. 저장 몸은 문서의
속성 칸 전부를 다시 싣기에 그 문서의 속성 화면이 든 값을 그대로 받고, 손이 바꾸는 칸은 권한 명단뿐이다. 안 잰 꼴의 문서(핵심기술 ·
집중보호 · 잠김 · 권한 셋 밖의 역할)는 보내기 전에 멈춘다.

- 이름 · 부서는 꼭 맞는 것만 받는다 — 일부만 맞은 사람 · 부서에 주면 엉뚱한 명단이 권한을 받는다
- 조직 → 사람 차례로 둔다 — 사람으로 짚은 말(「조직은 읽기, 그중 ○○ 님은 복사」)이 조직의 말을 이긴다
- 소유자 · 본인의 줄은 안 바꾼다 — 공동 편집자인 본인이 제 편집 권한을 지우면 되돌릴 길이 없다
- 못 푼 말이 하나라도 있으면 아무것도 짓지 않고 못 푼 말을 다 댄다 — 건너뛰면 명단의 일부만 권한을 받고, 그 빈자리는 미리 보기에
  안 보인다. 사람 파일(`--<칸>-file` — company-directory 의 `find --out` 이 쓰는 `people.txt` 꼴)의 줄은 「파일:줄」을 붙여 댄다. 주소록의
  사람 파일(`--people-file` people.json · 줄 칸은 `--people-as`)은 사람마다 「이름/메일ID」 말로 같은 길을 지난다(`people_specs` —
  읽기는 형제 스킬 ep-login 의 `ep_command.people_of` 한 벌)
- 사람 말의 메일 칸은 메일 ID 와 온 주소를 다 받는다(`same_mail`) — ECM 의 사람 줄은 메일 ID(@ 앞)를 들어, 메일 쪽이 낸 온 주소로
  동명이인을 가를 수 있게 한다

## 이름 · 태그 · 완료일 — 미리 보기 · 확인 열쇠 · 저장 · 다시 읽기

권한과 같은 「컨텐츠 속성 → 수정하기」 저장 하나다(`property_save_body` — 권한 몸과 한 함수). 화면처럼 권한 명단을 지금 그대로 싣고
`isChangeRoleInfo=F` 로 둔다 — 빈 명단을 실으면 걸린 권한이 지워진다. `plan_props` 는 권한 패스와 같은 문(안 잰 꼴의 문서 · 권한 셋
밖의 역할)을 지난 문서만 짓고, 열쇠는 지금 · 뒤 속성과 지금 명단의 지문이다. `apply_props` 는 그 사이 바뀌었으면 안 보내고, 보낸 뒤
이름 · 태그 · 완료일과 다른 칸(보안등급 · 공개 · 폴더 · 소유자 · 권한 명단)을 다시 읽는다 — 서버는 받지 않은 칸을 말없이 버린다
(완료일 「없음」이 그랬다).

## 기밀 · 핵심기술 문서는 묻고 받는다

`read_document` · `edit_document` 는 받기 전에 `check_readable` 로 속성 화면(`Ecm.security` — 읽기 하나 · 파일을 안 받는다)의
보안등급과 핵심기술 표시를 읽어, 기밀(`CLASSIFIED_LEVELS`)이거나 핵심기술 문서면 `Classified` 로, 등급을 못 읽으면 `SecurityUnread`
로 멈춘다. 뽑은 글자와 고치는 문서는 대화의 모델로 가기 때문이다. 문은 받는 요청보다 먼저 선다 — 받은 뒤 막으면 감긴 파일이
이미 PC 에 와 있다. 멈춘 말은 사람에게 물을 것(`ASK_BEFORE_AI`)을 들고, 사람이 그 문서를 AI 로 보내도 된다고 답한 뒤에만 `ai_ok`
로 넘긴다. 판정은 `gate` 하나이고 문서의 글자 · 그림을 대화로 들이는 손가락이 다 그것을 지난다:

- 남긴 글자로 답하는 `read_kept` — 남긴 뒤 기밀이 된 문서를 막는다
- 편집 패스의 뒤 걸음(`change` · `prepare_checkin`) — 사람이 ECM 화면에서 편집으로 연 파일을 이어받으면 앞 걸음(`edit`)의 문이
  없는데, 미리 보기는 고친 자리를 찍어 보이라고 이른다(그림이 모델로 간다). 미리 보기는 이미 읽는 속성 화면(`doc_state`)의 등급으로
  가르고, 창을 건드리기 전에 멈춘다. 올리기(`checkin`)는 미리 보기의 열쇠 뒤라 따로 안 묻는다

화면에 띄우기만 하는 `open_document` 는 막지 않는다(사람이 보는 창이다). 사람이 메일 첨부 · ECM 화면을 눌러 연 길도 이 문을 안
지난다 — 사람이 보는 창이다. 그래서 문을 안 지난 받은 파일은 모델로 안 간다: 「물어야 하나」를 가르는 자리는 `ecm.py` 의 `gate` 하나이고,
등급을 모르는 스킬 drm-office-read 는 에이전트 폴더(`ECM_DOCS_ROOT`)의 파일 가운데 이 손의 답이 그 스킬로 열라고 한 경로만 연다.
그 말(`RECEIVED_GATED` · 올리기 미리 보기의 「다음」 줄)은 문을 지난 답(`read` · 남긴 글자 · `edit` · 올리기 미리 보기)만 낸다. `open` 의 답(`RECEIVED_SHOWN`)은
「그 파일을 열지 않고 `read` 로 받는다」를, 에이전트가 말이 없을 때의 답은 「사람이 첨부를 눌러 연 파일은 열지 않는다」를 낸다.

그 말이 글에만 서지 않게 drm-office-read 의 읽는 손 · 뜨는 손은 받는 자리 밑의 파일을 깃발(`READER_GATE_FLAG` = `-EcmGated`) 없이는
앱을 띄우기 전에 거절하고 `read <열쇠>` 를 다음 걸음으로 낸다. 깃발은 문을 지난 그 말과 이 손이 제 읽기에서 읽는 손을 부를 때만
붙는다. 받는 자리는 `agent_docs_root`(환경변수, 없으면 `DEFAULT_DOCS_ROOT`) 하나이고, 그 손과 DRM 길잡이 훅은 같은 차례로 읽는다 —
기본값은 스킬 drm-office-read 의 값 파일(`scripts/places.json`)이 들고 셋이 다 그 파일을 읽는다. 그 스킬은 어느 도구 홈에나 깔려,
이 손이 없는 홈에서도 문이 같은 자리에 선다. 글자를 뽑는 손도 곁에 깔린 그 스킬의 것이다(`DEFAULT_READER`). 사람이 그 폴더의 감긴 파일을 글에 붙이면 길잡이는 읽는 명령 대신 `read <열쇠>` 를 댄다.

## 평소 EP 로그인을 묻는 자리 — 에이전트를 부르기 전에

이 PC 의 문서함 에이전트(파수에 물린 받기 · 올리기)는 그 윈도 로그온에 사람이 평소 Edge 로 한 EP 로그인이 있어야 문서를 연다(스킬 ep-login 의
`references/SOURCES.md` 「잰 것」 — 사람이 겪어 알린 것). 로그인 스킬의 입구는 메일 · 일정만 쓰는 부름에서 평소 Edge 를 안 보므로, 그 로그인을
챙기는 자리는 그것을 쓰는 이 손이다. 에이전트를 부르는 손가락(손가락 표의 `agent` — open · read · edit · register · cancel-edit, 코드에서
`Agent.from_env` 를 부르는 명령)은 세션을 맞추기 전에 ep-login 이 빌려 주는 읽기만 하는 답(`ep_session.ordinary_login`)을 받는다 — 「없다」면
에이전트 · 받는 손에 닿지 않고 세션 없음(3)과 「입구를 `ecm` 으로」로 멈추고, 「해 봤다」(섰는지 모른다)면 사람이 할 일을 한 줄 말하고 잇는다.
이 손은 입구를 대신 부르지 않는다 — 하위 에이전트 안에서 창을 띄우면 창이 둘 서고 SSO 가 서로를 끊는다. 읽기만 하는 명령(찾기 · 목록 ·
속성 · 판 이력)은 안 묻는다.

## 받은 파일과 남긴 글자

에이전트가 `<받는 자리>\<계정>\VIEW\<시각 번호>\`(보기) · `…\CHECKOUT\<시각 번호>\`(편집)에 둔 파일은 **지우지도 옮기지도 않는다.**
그 폴더는 에이전트의 것이고(ECM 화면에서 사람이 열어도 같은 자리에 같은 꼴로 쌓인다), 파일은 DRM 에 감긴 채라 그 PC 의 오피스
밖에서는 안 열린다. 비우는 일은 에이전트의 정리 프로그램 몫이다.

읽는 손이 뽑은 평문은 이 손이 지은 임시 폴더(`ecm-read-…`)에 잠시 놓였다가 글자를 읽자마자 그 폴더째 지우고 부르는 쪽에만 간다 —
지우기가 실패해도 말없이 넘어가므로(`ignore_errors`) 그때는 그 폴더에 남는다. 읽는 손에는 `-NoKeep` 을 준다 — 읽는 손이 제 자리에
한 벌 더 남기면 등급 문을 안 지나는 사본이 생긴다.

명령줄의 `read` 는 뽑은 글자를 늘 `text_dir()`(홈 아래 · 저장소 밖)에 문서 열쇠마다 한 장으로 남긴다 — `.md`(Fasoo 가 감싸지 않는
꼴)이고, 머리 두 줄(읽는 손의 한 줄 · 열쇠와 받은 파일의 자리와 뽑은 때) 뒤 `---` 아래가 글자다. 같은 열쇠를 다시 읽으면 등급 문만
지나 그 파일로 답하고 문서를 받지 않는다(`read_kept`) — 받을 때마다 에이전트가 내려받고 오피스 창이 뜨는 값을 한 번만 치른다. 판이
오르면 열쇠가 바뀌므로 열쇠가 같으면 같은 판의 글자다 — 그 판이 지난 판이면 머리 한 줄(`tell_superseded`)이 지금 판의 열쇠를 댄다. 글자가 답 하나의 크기(`ep_session.OUT_BYTES`)에 안 들면 — `--as-file` 을
주면 짧아도 — 화면에는 그 파일의 경로만 낸다. 남긴 파일은 이 손이 지우지 않는다 — 치우는 것은 사람이다.

## 검사 — 설정 저장소의 `_check/skills/company-ecm/check_ecm.py` 를 남기는 까닭

check-design §1 의 넷이 다 걸린다.

- 길이 분명하다 — 같은 서비스 모음에 문서를 잠그는 편집 열기가 있고 손을 고칠 때마다 막는 목록이 흔들린다. 등록 · 판 올리기는 동료가
  보는 문서함을 바꾸고 미리 본 판과 다르게 갈 길(열쇠를 안 보거나, 미리 본 뒤 파일 · 창이 바뀐 것을 못 보는 손)이 고칠 때마다 선다.
  조각 바꾸기는 여러 번 나오는 조각을 고르면 엉뚱한 자리를 고친다. 기본 앱 손은 사람이 이미 고른 확장자에서 늘 불리며, 파워포인트는
  사람의 앱에 붙는다. 권한 저장은 문서의 속성 칸 전부를 다시 싣고, 읽기 · 편집 열기가 받은 글자는 대화의 모델로 간다
- 깨지면 조용하거나 되돌릴 수 없다 — 서버의 잠금 · checkin 이 못 올리는 꼴에 남은 잠금 · 미리 본 판과 다르게 올라간 판 · 「실패」로
  알려진 채 남의 문서함에 올라간 문서 · 볼 수 없어야 할 동료에게 열린 문서 · 권한을 주다 바뀐 보안등급 · 엉뚱한 자리가 고쳐진 채
  올라간 문서 · 사람에게 묻지 않고 대화로 들어간 기밀 · 핵심기술 문서의 글자 · 바뀐 기본 앱 · 닫힌 사람의 문서 · 사람 파일의 일부나
  동명이인에게만 열린 권한 · 이름이 겹친 다른 부서 문서함에 선 새 문서
- 쓰는 사람의 문서함 · 설정 · 문서를 잃는다
- 다른 무엇도 안 잡는다 — 회사 ECM 은 회사 PC 에서만 닿는다

창 닫기 · 고치기 묶음(`--office`)이 재는 까닭 — 워드와 파워포인트는 사용자 하나에 하나만 떠 사람의 앱에 들어가고, Acrobat · Reader 는
창 하나에 탭으로 들어 Ctrl+W 가 앞 탭을 닫는다. 앞 탭이 사람의 pdf 면 닫는 손이 키를 안 보내야 한다. 고치는 손은 실물 앱의 문서
모델(장 · 글 칸 · 표 · 시트 · 수식)에서 조각을 센다 — 가짜로는 못 잰다. 앱은 셸이 띄우듯 실행 파일에 파일을 줘서 띄운다.
