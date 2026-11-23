# 사규 손의 짜임 — 검사가 무는 까닭

`scripts/regulation.py` · `scripts/cbsop.py` 를 고치기 전에 읽는다. 부르는 꼴 · 내는 것은 `regulation.py --help`(그 파일의 표에서 선다)가, 손이 맞물리는 계약은 그 파일 머리말이, 앱의 자리와 꼴은
`SOURCES.md` 가 든다.

## 손가락 — 사람이 누르는 단위와 한 부름

결정 0255 의 선대로 새 화면 기능은 명령이 아니라 있는 명령의 칸으로 든다 — 사규는 읽기뿐이라 출발이 문서 하나(`read`)와 찾기 하나(`search`)다.

| 사람이 화면에서 누르는 것 | 모델의 한 부름 |
|---|---|
| 문서 창의 「개정이력」 단추 | `read <번호> --history` |
| 개정이력의 판 번호 → 지난 판 창 | `read <번호> --rev <판>`(함께 서는 칸은 짝의 표) |
| 개정이력의 전후대비표 [보기] | `read <번호> --rev <판> --changes`(지금 판은 `--changes`) |
| 주요 개정 내용 → 결재 경과 창 | `read <번호> --rev <판> --trail` |
| 담당 · 검토 · 승인 이름 → 사람 창(셋을 차례로) | `read <번호> --contacts`(한 부름에 셋) |
| 상세검색의 구분 · 첨부파일명 | `search <말> --in <범주> --files` |
| 「최근 사용 표준」 · 「접근 가능한 표준」 메뉴 | `search --used` · `search --access <등급>` |

본문을 내는 보기는 다 `opened` 한 길을 지나 화면이 막는 등급 문서를 안 연다 — 지난 판 · 전후대비 · 결재 경과 · 사람 창도 같다.

보기 칸이 무엇과 함께 서나는 `regulation.py` 의 짝의 표 한 장(`VIEW_PAIRS`)이 든다 — 세션 전의 거름과 `read --help` 의 짝 표가 다
거기서 나온다. 안 서는 짝에 그 짝만의 까닭 · 말이 붙으면 곁의 `PAIR_TAIL` · `PAIR_WHY` 가 짝마다 든다. 짝을 걷을 때는 그 표 한 줄을
고치고, 걷은 짝에 맞는 까닭이 있으면 `PAIR_TAIL` 에 더한다. 짝을 더할 때는 그 두 칸의 `PAIR_TAIL` · `PAIR_WHY` 줄을 걷고, `read` 의
보기 갈래가 그 두 칸을 함께 다루게도 고친다 — 안 그러면 거름은 지나는데 한 칸이 말없이 빠진다.

## 조각의 지도

사규 손은 얇은 명령(`regulation.py`)과 사규관리 앱의 손(`cbsop.py`) 둘이다 — 명령은 인자를 가리고 손을 엮기만 하고, 망에 닿는 것은 손이다.
`handout.py` 는 다른 스킬(주소록의 전화)이 싣는 이름을 내주는 한 자리다.

아래는 코드에서 뽑은 지도다 — 줄의 문장은 그 조각 머리말의 첫 문장이라, 문장을 고치려면 머리말을 고치고 다시 짓는다.

<!-- drawn:piece-map · 손으로 고치지 않는다 — scripts/skill-map.py 가 짓는다 -->
| 조각 | 맡은 일 | 싣는 곁 조각 | 다른 스킬에서 싣는 것 |
|---|---|---|---|
| `regulation.py` · 입구 | 사규 스킬의 얇은 명령 — 곁의 손(``cbsop.py``)으로 사규관리 앱의 목록을 받아 두고, 거기서 찾고, 앱에 검색하고, 한 건을 읽는다. | `cbsop` | ep-login 의 `ep_command` · `ep_session` |
| `cbsop.py` | 사내 사규관리 앱(cbsop)의 손 — EP 세션으로 앱에 들어가, 범주 · 전체 목록 · 검색 · 문서 한 건을 읽는다. | — | ep-login 의 `ep_session` |
| `handout.py` | 사규 손이 다른 스킬에 내주는 이름의 한 자리 — 이 폴더의 파일 → 다른 스킬이 그 파일에서 실어 쓰는 이름. | — | — |

**입구에서 내려가는 나무** — 줄마다 조각과 그 머리말 첫 문장. 한 조각은 처음 닿은 자리에서만 펴고 다시 닿으면 `↑` 로 가리킨다. 클래스는 메서드를 그 아래에 든다. `←` 뒤는 그 조각을 부르는 다른 스킬이다. 인스턴스를 거친 부름은 이어지지 않는다.

- `main` — 명령 입구 — 인자를 읽고, 거른 뒤, 받아 둔 목록으로 서면 세션 없이 · 아니면 세션 바퀴 안에서 run 을 돌려 답 하나와 종료 값을 낸다.
  - `parser` — 명령줄의 꼴 — 명령 여섯과 인자를 세우고, 명령마다의 설명 · 맨 위 지도를 도움말 표(``reads`` · ``top_map``)에서 붙인다.
    - `reads` — 명령마다 (한 줄 — 맨 위 --help 의 지도와 명령 목록, 그 명령의 --help 에 덧붙는 설명 · 답의 칸). --help 는 이 표와 argparse 에서만 선다.
      - `pairs_help` — read --help 의 「함께 서는 짝」 — 보기 칸마다 함께 줄 수 있는 칸과, 짝마다의 뜻(짝의 표에서).
        - `partners` — 보기 칸 하나와 함께 서는 칸 — ``VIEW_FLAGS`` 차례로.
          - `stands` — 두 보기 칸이 함께 서나 — 짝의 표(``VIEW_PAIRS``)에 든 짝만 선다.
    - `image_most` — --images 가 받는 장 수의 위 — 그림을 받는 손의 값(``body_images.MAX_IMAGES``) 그대로. 이름으로 바로 싣는다 — 손을 대역으로 바꾼 판에도 도움말은 선다.
    - `top_map` — 맨 위 --help 의 지도 — reads · NOT_HERE · EXITS 에서 짓는다.
    - `grade_names` — --access 가 받는 등급 이름 — 앱 손의 등급 표(``cbsop.GRADES``) 그대로. 이름으로 바로 싣는다 — 손을 대역으로 바꾼 판에도 도움말은 선다.
  - `gate` — 세션 · 목록 받기 전의 거름 — 명령의 거름(``REFUSALS``)이 막거나 --access 의 등급이 앱 손의 표에 없으면 Stop(인자).
    - `find_refusal` — find 가 거르기를 하나도 안 받았으면 그 까닭 — 서면 빈 글자. 목록을 새로 받기 전에 가린다.
      - `keys_of` — 사람이 준 말 → 견주는 열쇠 — 낱말마다 ``squash`` 한 것 가운데 빈 것을 뺀다.
    - `search_refusal` — search 의 칸이 함께 설 수 없으면 그 까닭 — 내 목록(--used · --access)은 말 · 찾는 칸을 안 받고, 찾기는 말을 받는다.
      - ↑ `keys_of`
    - `view_refusal` — read 의 보기 칸이 함께 설 수 없으면 그 까닭 — 서면 빈 글자. 안 먹는 칸을 말없이 버리면 물음에 걸린 자리가 빠진 답이 「됐다」로 나간다.
      - `views_on` — read 에 준 보기 칸 — 짝의 표(``VIEW_FLAGS``) 차례로. 켜지 않은 칸은 argparse 의 기본값(None · False)이다.
      - ↑ `stands`
      - `pair_value` — 짝마다의 표에서 flag 와 안 서는 칸들 가운데 처음 걸린 짝의 값 — 짝의 두 칸 차례는 안 가린다.
      - `pair_said` — 안 서는 짝의 말 — 함께 못 쓰는 칸 · 그 칸의 짝 · 끝에 붙는 까닭 · 다음 길.
      - ↑ `partners`
      - `flag_tail` — 보기 칸의 두루 쓰는 다음 길(``VIEW_FLAGS`` 의 셋째 칸).
    - `grade_of` — --access 의 등급 이름 → 앱의 등급 코드. 표에 없는 이름이면 Stop(인자) — 표는 앱 손의 것이라 세션 없이 가린다(main 이 먼저 부른다).
  - `usable_index` — 이 명령이 그대로 쓸 받아 둔 목록 — refresh 는 늘 없고, 최근 시행을 묻는 판(``wants_fresh``)은 RECENT_FRESH_DAYS 안에 받은 것만.
    - `cached_index` — INDEX_DAYS 안에 받은 같은 꼴의 목록 — 없거나 낡았거나 깨졌으면 None.
      - `index_path` — 받아 둔 목록의 자리 — ``REGULATION_INDEX_DIR`` 이 있으면 그 폴더, 없으면 홈 아래 ``INDEX_DIR``.
    - `wants_fresh` — 최근 시행을 묻는 판인가 — 받아 둔 뒤에 시행된 것을 놓치지 않게 RECENT_FRESH_DAYS 안의 목록만 쓴다.
  - `run` — 명령 하나를 그 명령의 손에 넘긴다 — 앱 손과, 목록 명령이면 받아 둔 목록과 답 머리를 앞에 한 번 세운다.
    - `find` — find 명령 — 받아 둔 목록을 말 × 범주(어느 깊이든) × 기간으로 거른다 → 차례를 세운다 → 쪽으로 넘긴다.
      - `pool` — find · recent 가 거르는 줄 — --abolished 면 폐지 문서, 아니면 공개된 문서.
      - ↑ `keys_of`
      - `since_of` — 시행일이 최근 days 일 안인가를 가르는 앱 꼴의 날 — 그날부터(그날 포함) 든다.
      - `ordered` — find 답의 차례 — 기간을 주었으면 새 시행일부터, 아니면 제목에 말이 다 든 것부터 경로 · 이름 차례.
        - `newest_first` — 줄을 시행일이 새것부터 — 같은 날은 받은 차례 그대로.
      - `matched` — find · recent 의 거르기 — 범주(어느 깊이든) × 시행일 since 부터 × 말이 다 든 줄. 받은 차례 그대로 — 차례는 부르는 쪽이 정한다.
        - `under_category` — 범주 말(「작업표준」 · 「기초 > 작업표준」)이 경로의 어느 깊이에서든 이어진 칸들에 든 줄 — 칸마다 그 깊이 범주 이름의 일부면 된다.
      - `page` — head 에 줄을 start 부터 most 줄 싣는다 — 답이 OUT_BYTES 를 넘으면 줄을 던다.
      - `find_hint` — 0 건인 find · recent 의 ``next`` — 무엇으로 찾았나와, 거르기마다 풀어 볼 길. recent 는 말이 없다(``keys`` 가 빈다). ``category`` 는 ``category_state``, ``gone`` 은 같은 조건에 걸리는 폐지 문서 수, ``days_optional`` 은 기간을 빼고 찾을 수 있는 명령인가(find).
      - `category_state` — 범주 말의 상태 — 말이 없으면 None, 있으면 그 범주 아래 줄이 목록에 있나.
        - ↑ `under_category`
      - `gone_left` — 같은 거르기에 걸리는 폐지 문서 수 — 폐지 문서를 따로 안 견주는 find --abolished 는 gone 이 None 이라 0, 폐지 문서가 없어도 0.
        - ↑ `matched`
    - `recent` — recent 명령 — 범주 안에서 시행일이 최근 N 일 안인 줄을 새 시행일부터 낸다.
      - ↑ `since_of`
      - ↑ `pool`
      - ↑ `newest_first`
      - ↑ `matched`
      - ↑ `page`
      - ↑ `find_hint`
      - ↑ `category_state`
    - `refresh` — refresh 명령 — 방금 받은 목록의 머리에 맨 위 범주와 폐지 문서 수를 단다.
    - `tree` — tree 명령 — 경로로 거른다 → 그 아래 나무를 짓는다 → 맨 아래 칸에 닿았으면 그 칸의 문서를 쪽으로 넘긴다.
      - `under_path` — 경로 말(「기초 > 작업표준 > 포항화성」)의 칸마다 그 깊이의 범주 이름에 든 줄과, 맞춘 깊이 수.
      - `branches` — (경로의 depth 칸 아래 나무 — 칸마다 count · under, 경로가 맨 아래 칸에 닿은 줄 — 이름순).
      - ↑ `page`
    - `need_index` — (목록, 방금 받았나, 받은 목록을 PC 에 못 남긴 까닭) — 못 남겨도 받은 목록으로 답한다.
      - ↑ `usable_index`
      - `build_index` — 앱의 전체 목록(공개된 문서) — rows, 폐지된 문서 — gone. 전체 목록에는 폐지 문서가 안 든다(``references/SOURCES.md``).
        - `is_folder` — 앱의 전체 목록에는 범주 자리 줄이 섞인다 — 제 이름이 제 층의 범주 이름과 같은 줄이다.
        - `row_of` — 앱의 전체 목록 줄 → 받아 둔 줄 — ``ROW_KEYS`` 칸 · 범주 경로 · 있으면 관련 이름 · 표준번호 · 유효기간 끝.
          - `path_of` — 앱 줄의 범주 칸(categoriName0..3) 가운데 빈 것을 뺀 경로.
          - `with_number` — 줄에 표준번호(txtIdx)와 인증서의 유효기간 끝(toDate)을 단다 — 있는 줄에만.
        - `gone_of` — 폐지 문서의 줄 — 앱의 「최근 변경된 표준」(삭제) 줄을 받아 둔 줄의 꼴로. 경로는 그 줄의 구분 칸(type1 · 2 · 3)이고, 판은 폐지다.
          - ↑ `with_number`
      - ↑ `index_path`
    - `index_head` — 목록 명령의 답 머리 — 받은 때 · 방금 받았나 · 전체 수, 폐지 문서를 거르는 판이면 그 수, 목록을 못 남겼으면 그 말.
      - `stamp_word` — 받아 둔 목록을 받은 시각 — 「YYYY-MM-DD HH:MM」.
    - `read` — read 명령 — 문서를 연다 → 판을 고른다 → 보기 하나로 답한다.
      - `opened` — (앱의 답, 그 문서의 메타) — 사람의 화면이 그 문서를 열 때만. 앱의 JSON 길은 화면이 막는 등급 문서의 본문도 내주므로(``references/SOURCES.md`` 「등급 문서」), 등급이 「일반」이 아니거나 등급을 못 읽은 문서는 화면의 문서 창에 먼저 묻고(``cbsop.App.screen_allows``) 막으면 본문 · 바뀐 자리 · 지난 판 · 첨부를 하나도 안 내고 멈춘다.
      - `head_of` — 보기마다 답의 맨 앞 — 문서 번호와 이름.
      - `history_view` — --history 보기 — 지금 판 · 등급과 개정이력의 줄, 지난 판으로 가는 길.
        - `history_rows` — 화면 「개정이력」 의 줄 — 새 판부터. summary 는 주요 개정 내용(없으면 개정 내용)이다.
      - `contacts_view` — --contacts 보기 — 담당 · 검토 · 승인 가운데 사번이나 이름이 있는 사람마다 사람 창.
        - `card` — 화면에서 이름을 누르면 뜨는 사람 창 — 퇴사자는 창이 비어 이름만 낸다.
      - `revision` — 개정이력의 한 판 — 판 이름(「13」 · 「폐지」)이 꼭 같은 줄. 없으면 있는 판을 대며 종료 2.
      - `trail_view` — --trail 보기 — 고른 판(없으면 지금 판)의 결재 경과. 비었으면 그렇다는 note.
        - `trail_rows` — 한 개정의 결재 경과 — 걸음마다 때 · 걸음 · 올린 사람 · 받은 사람 · 의견.
      - `edition` — 판 고르기 — (바뀐 자리를 든 앱의 답, 본문을 든 줄). 지금 판이면 받은 그대로, 지난 판이면 바뀐 자리는 그 개정의 전후대비표로, 본문은 그 판의 것으로 바꾼다.
      - `page_of` — 본문을 든 줄 → 본문을 푼 꼴(``visible`` 의 글자 · 그림 주소 · 숨긴 덩이 수). 본문이 없는 판은 None.
        - `reader` — 형제 스킬 company-mail 의 ``visible`` — 본문 HTML 을 글자로 푸는 한 손. 사람 눈에 안 보이는 글(숨긴 요소 · 바탕색 글 · 스크립트 · 머리 · 폭 없는 문자)을 걷고 표를 한 행 한 줄로 낸다.
      - `brief_of` — 본문 쪽 보기의 머리 — 고른 판 · 그 시행일 · 등급에, 본문이 있으면 글자 수 · 그림 수 · 숨긴 덩이 수, 지난 판이면 지금 판.
      - `images_view` — --images 보기 — 본문 그림을 받아 둔 파일의 줄.
        - `save_images` — 본문 그림을 형제 스킬 company-mail 의 ``body_images`` 로 받는다 — 묻는 것은 앱 손(``cbsop.App.image``)이 가린다.
          - `cbsop.SessionExpired` — 사내 세션이 끊겼거나 앱이 안 들였다 — 받는 손을 다시 부를 자리다.
          - `cbsop.SessionMissing` — 세션 파일이 없거나 못 읽는다 — 받는 손(스킬 ep-login)을 부를 자리다.
          - `cbsop.AppError` — 사규 앱의 손이 낸 실패 — 앱이 거절했거나 답이 꼴이 아니거나 앱에 못 닿았다.
      - `changes_view` — --changes 보기 — 바뀐 자리를 답의 크기 안에서(낱말을 주면 그 낱말이 든 자리만). 지난 판에 전후대비표가 없으면 그렇다는 note.
        - `with_changes` — 바뀐 자리를 답 out 에 싣는다 — 낱말로 거른다 → room 바이트 안에 싣는다 → 센 수를 말로 단다.
          - `changes_hit` — 바뀐 자리 가운데 열쇠(하나라도)가 까닭 · 전 · 후 어디에 든 것 — 줄마다 why · before · after(한쪽 CHANGE_SIDE 자까지) · 있으면 kind. 열쇠가 없으면 다.
            - `tobe_of` — 앱의 답에 든 바뀐 자리(전후대비)의 줄 — 없으면 빈 목록.
            - `plain` — 앱의 HTML 조각 → 읽을 글자. ``numbered`` 가 거짓이면(바뀐 자리의 전 · 후) 그림이 번호 없는 [그림] 이다 — 거기 번호를 달면 본문 그림의 번호로 읽힌다.
              - ↑ `reader`
            - `clip` — 글을 ``most`` 자까지 자르고 잘렸으면 전체 길이를 단다.
          - ↑ `keys_of`
          - `packed` — 줄을 차례로 room 바이트 안에 드는 데까지 싣는다 — (실은 줄, 못 실은 수). 첫 줄은 늘 싣고, 하나가 안 들면 그 뒤는 다 센다.
          - `changes_said` — 바뀐 자리 답의 말 — 낱말로 걸러 0 건이면 next, 못 실은 것이 있으면 changes_more.
        - ↑ `tobe_of`
      - `grep` — 대목 보기 — 낱말이 든 줄을 찾는다 → 짧은 이웃 줄 · 표의 첫 행과 함께 대목으로 묶는다 → 답의 크기 안에 싣는다 → 남은 것을 말로.
        - `lines_of` — 본문의 빈 줄 아닌 줄마다 (그 줄이 시작하는 글자 자리, 줄).
        - ↑ `reader`
        - `hit_lines` — 열쇠(하나라도)가 든 줄의 차례 번호 — 글자 자리 start 부터의 줄만.
        - ↑ `keys_of`
        - `fit_passages` — 대목을 차례로 out 의 hits 에 싣되 답이 OUT_BYTES 를 넘으면 멈춘다(첫 대목은 늘) — 못 실은 첫 대목의 걸린 줄 글자 자리, 다 실었으면 None.
        - `passages` — 걸린 줄마다 대목을 지어 겹치거나 맞닿은 것을 잇는다 — [첫 줄, 끝 줄, 표의 첫 행(없으면 None), 걸린 첫 줄]의 목록.
          - `widened` — 걸린 줄 i 의 대목 — (첫 줄, 끝 줄). 앞뒤로 GREP_AROUND 줄까지, 이웃 글자 합이 GREP_AROUND_CHARS 안인 짧은 줄만 붙인다.
          - `table_top` — 걸린 줄 i 가 표의 행이면 그 표의 첫 행 — 대목 안에 이미 들었거나 표의 행이 아니면 None.
        - `grep_said` — 대목 답의 말 — 못 실은 대목이 있으면 그 자리로 잇는 more, 하나도 안 걸렸으면 next.
      - `start_of` — 본문을 읽거나 찾기 시작하는 글자 자리 — --from, 없거나 음수면 0.
      - `continue_view` — 이어 읽기 보기 — 본문을 --from 자리부터 --max 와 답의 크기 안에서.
        - ↑ `start_of`
        - `read_most` — 본문을 읽는 판이 한 번에 싣는 글자 수의 위 — --max, 없으면 READ_MAX.
        - `more_text` — 본문이 남은 답의 ``more`` — 이어 읽을 자리 end 를 든 말.
      - `first_view` — 첫 답 보기 — 메타 → 관련 → 첨부 → 짧은 본문이면 바뀐 자리 · 긴 본문이면 읽는 길 → 본문 앞머리.
        - `meta_of` — 첫 답의 메타 — 경로 · 다음 검토일 · 담당 · 검토 · 승인 · 마지막 개정, 있으면 표준번호 · 인증서의 유효기간.
        - `related_of` — 화면 「관련표준」 의 줄 — 줄마다 processIdx · name · menu · deptnm.
        - `files_of` — 앱의 답에 든 첨부 파일 이름.
        - `long_next` — 긴 본문의 첫 답에 붙는 것 — 바뀐 자리가 있으면 그 수와, 읽는 길.
          - ↑ `tobe_of`
        - ↑ `with_changes`
        - ↑ `read_most`
        - ↑ `more_text`
    - `search` — search 명령 — 내 목록이면 그 목록, 아니면 칸 고르기 → 범주 → 앱 묻기 → 줄 모으기.
      - `access_list` — search --access — 화면 「접근 가능한 표준」 의 그 등급 문서를 경로 · 이름 차례로.
        - `mine_row` — 내 목록(최근 사용 · 접근 가능)의 앱 줄 → 답의 줄. 최근 사용 줄은 시행일을 reRegDate 에 들고(SOURCES.md), 등급 이름은 securityGradeN 이다.
        - ↑ `grade_of`
        - ↑ `page`
      - `used_list` — search --used — 화면 「최근 사용 표준」 의 최근 N 일을 앱의 차례 그대로(줄은 연 날을 안 든다).
        - ↑ `mine_row`
        - ↑ `page`
      - `search_fields` — search 가 앱에 묻는 칸 — 표준명에 --body 본문 · --owner 담당 · 부서 · --files 첨부 이름을 더한다.
      - `top_menu` — search --in 의 범주 — 앱의 통합 검색은 맨 위 범주 하나(menuId)로만 좁힌다.
      - `search_rows` — 앱의 통합 검색 답 → 답의 줄 — 범주마다의 결과 칸(``SEARCH_HIT_PREFIX``)을 칸 이름 차례로 잇는다.
      - ↑ `page`
  - ↑ `cbsop.SessionExpired`
  - ↑ `cbsop.SessionMissing`

**어디서도 안 닿는 조각** — 표 · 인스턴스를 거쳐 부르거나 아무도 안 부른다.

- `cbsop.Refused` — 잰 꼴 밖의 주소라 묻지 않았다.
- `cbsop.App` — 사규 앱 한 판 — 사내 세션의 쿠키로 들어가 앱의 JSON 자리와 화면을 읽는다.
  - ↑ `SessionMissing`
  - `App._get` — 주소 하나를 (``data`` 를 주면 폼 POST 로) 열어 받은 글자 — 넘김 · 거절 · 못 닿음은 그대로 올리고 손의 예외로 옮기는 것은 부르는 쪽이다.
  - `App.login` — 앱에 들어간다 — SSO 넘김 화면의 토큰을 앱 뿌리에 넘겨 EP 열쇠를 받고, 그 열쇠로 ``test_login.do`` 가 첫 화면(``LANDING``)으로 넘기면 들어간 것이다.
    - ↑ `App._get`
    - ↑ `SessionExpired`
    - ↑ `AppError`
  - `App.screen` — 앱의 한 자리를 들어간 세션으로 받아 글자 그대로 — data 가 있으면 폼 POST, 없으면 GET. 끊긴 세션 · 거절 · 못 닿음을 손의 예외로.
    - ↑ `App.login`
    - ↑ `App._get`
    - ↑ `SessionExpired`
    - ↑ `AppError`
  - `App.call` — 앱의 JSON 자리 하나를 폼 POST 로 부르고 답 JSON 을 낸다 — 답이 JSON 이 아니면 AppError.
    - ↑ `App.screen`
    - ↑ `AppError`
  - `App.menus` — 맨 위 범주 — [{menuIdx, menuName, openYn, …}].
    - ↑ `App.call`
  - `App.all_in` — 한 범주 아래 문서 전부(화면의 「EXCEL」 이 받는 목록) — [{processIdx, processName, categoriName0..3, …}].
    - ↑ `App.call`
  - `App.search` — 앱의 통합 검색 — fields 는 subject · content · file_name · user_name · team_name 을 쉼표로. 화면처럼 검색어를 한 번 싸서 searchText · searchText2 둘에 다 준다 — searchText2 가 비면 본문 검색이 늘 0 건이다.
    - ↑ `App.call`
  - `App.image` — 본문 ``<img src>`` 하나 — 앱 호스트의 잰 꼴(IMAGE_PATH · 물음표 없이)만 묻고, 그 밖이면 묻지 않고 ``Refused``. 그림은 앱 세션 없이도 받아진다 — 그래서 들어가기를 안 거친다.
    - ↑ `Refused`
    - ↑ `AppError`
  - `App.info` — 문서 한 건 — ProcessInfo\[0\](메타 · 본문 HTML) · searchTobe(최근 개정의 바뀐 자리) · searchProcessFileList(첨부) · reviewerList · searchRelationSite. 관련 표준은 여기 없다 — ``related``.
    - ↑ `App.call`
  - `App.related` — 화면 「관련표준」 표 — [{processIdx, processName, menuName, reDeptnm, hname, regDate, stateNm, …}].
    - ↑ `App.call`
  - `App.screen_allows` — 사람의 화면이 이 문서를 여나 — 화면의 문서 창(``goProcessInfoPop.do``)을 GET 해 가린다.
    - ↑ `App.screen`
    - ↑ `AppError`
  - `App.changed` — 화면 「최근 변경된 표준」 — 날은 앱 꼴(YYYY.MM.DD), state 는 공개 · 삭제 · 빈 글자(전체).
    - ↑ `App.call`
  - `App.history` — 화면 「개정이력」 — 판마다 [{version, enforcementDate, mainContent | revisedContent, hname, reHname, workIdx, processHisIdx, …}]. 새 판부터.
    - ↑ `App.call`
  - `App.past` — 지난 판 한 건 — ProcessHisInfo\[0\](메타 · 본문 HTML) · 첨부 · 관련사이트.
    - ↑ `App.call`
  - `App.tobe` — 한 개정의 전후대비표 — [{tobeGubunNm, oldContent, toContent, note}].
    - ↑ `App.call`
  - `App.trail` — 한 개정의 결재 경과 — [{apRegDate, codeName, reHname, apHname, opinion}].
    - ↑ `App.call`
  - `App.person` — 화면에서 이름을 누르면 뜨는 사람 창 — {hname, deptcdDisp, jikwicdDisp, jikckcdDisp, responsibility, officePhone, handpon, email}. 퇴사자면 None.
    - ↑ `App.call`
  - `App.me` — 쓰는 사람의 사번 — 앱은 내 목록 화면에 그 값을 박아 둔다(``empcd : "…"``). 이 판 동안 한 번만 받는다.
    - ↑ `App.screen`
    - ↑ `AppError`
  - `App.used` — 화면 「최근 사용 표준」(내가 화면에서 연 문서) — [{processIdx, processName, menuName1..3, reDeptnm, hname, reRegDate, txtIdx}].
    - ↑ `App.call`
    - ↑ `App.me`
  - `App.access` — 화면 「접근 가능한 표준」 의 한 등급(읽기 범위) — 등급 코드는 ``GRADES``. 빈 등급(전체)은 1 분 가까이 걸려 안 받는다.
    - ↑ `Refused`
    - ↑ `App.call`
    - ↑ `App.me`
<!-- /drawn:piece-map -->

## 검사 — 설정 저장소의 `_check/skills/company-regulation/check_regulation.py` 를 남기는 까닭(check-design §1 넷)

이 스킬의 답은 사람이 회사 규정으로 믿고 움직이는 말이 된다. 표의 열이 밀리면 한도 금액이 엉뚱한 구분에 붙고, 답이 대화 도구의 출력
한도를 넘으면 모델은 앞머리만 보고 답하고, 낡은 목록으로 「요즘 바뀐 것」을 답하면 「바뀐 것 없음」이 된다. 낱말 찾기가 조 하나를
빠뜨리면 「그런 조항은 없다」가 된다. 본문 그림 번호가 어긋나면 모델이 엉뚱한 그림을 읽고 규정을 답한다. 바뀐 자리를 낱말로 거르지
않거나 함께 준 보기 칸을 말없이 버리면, 걸린 자리가 답의 크기에 덜어 낸 쪽으로 빠져 「그 대목은 안 바뀌었다」가 된다. `find` · `recent`
의 범주가 맨 위 범주만 보면 「작업표준」 아래의 문서가 0 건 · 종료 0 으로 나와 「그런 작업표준은 없다」 · 「요즘 바뀐 작업표준은 없다」가
되고, 기간을 낡은 목록에 걸면 「요즘 바뀐 것 없다」가 된다. 앱의 전체 목록에 폐지 문서가 안 들어 폐지 문서를 따로 안 받으면
「폐지된 지침」 이 0 건 · 종료 0 으로 「그런 지침은 없었다」가 된다 — 목록은 폐지 문서를 `gone` 에 따로 들고, `--abolished` 만 거기서
찾는다(공개 문서의 답에 폐지 문서를 섞지 않는다). 두 명령의 `--in` 은 한 함수(`under_category`)로 같은 뜻이다.

등급 문서는 사람의 화면이 여는 만큼만 읽는다. 앱의 JSON 길은 화면이 막는 문서의 본문도 내주므로, 본문 글자를 내는 손가락은 다
`opened` 한 길로 문서를 열고 그 길이 「일반」 밖의 문서마다 화면 창에 묻는다. 이 문이 빠지거나 가리지 못한 창을 여는 쪽으로 넘기면,
권한이 없는 사람에게 사외비 · 기밀 본문이 종료 0 으로 나가 되돌릴 수 없다 — 실물에서 났고(`SOURCES.md` 「등급 문서」) 검사 판정 11 · 12 가
문다.

- 길이 분명하다 — 합친 칸 · 긴 본문 · 하루 넘은 목록은 흔하고, 셋 다 실제로 났다. 긴 문서는 앞머리만 오고 나머지는 이어 읽거나
  낱말로 찾는 길이 기본이라 그 길의 빠뜨림이 곧 답의 빠뜨림이다. 둘째 깊이의 범주(작업표준)로 좁힌 `find` · `recent` 가 그 아래 문서를
  0 건 · 종료 0 으로 낸 것은 받아 둔 목록 꼴의 가짜로 재현됐다
- 깨지면 조용하다 — 명령은 종료 0 을 내고 답이 그럴듯하다
- 크게 다친다 — 규정을 틀리게 알린다
- 다른 무엇도 안 잡는다 — 실물 앱은 회사 PC 에서만 닿고 거기서도 눈으로 봐야 안다
