# 메일함 스캔의 설계

메일함 스캔 스킬의 코드를 고치는 사람이 읽는다. 무엇이 어떻게 도는지 — 조각의 지도, 판 하나가 흐르는 길, 프로그램과 다른 스킬이
기대는 약속, 하지 않는 것 — 을 이 글 하나에서 읽게 한다. 쓰는 법은 `SKILL.md` 가, 명령마다 부르는 꼴 · 내는 것 · 종료 값은 그 스크립트의
머리말이 든다.

## 무엇을 하나 — 사람이 보는 것

작업 스케줄러가 몇 분마다 사람 없이 스캔 한 판을 띄운다. 판은 회사 메일 손의 읽는 명령으로 메일함의 메일 머리를 받아 사용자 폴더
`mailbox-scan/` 에 쌓고, 지난 모습과 견줘 새 메일과 사람이 한 일(연 · 옮긴 · 지운 메일)을 적는다. 메일함 · 본문 · 모델에는 안 닿는다.

스캔은 이 일 하나만 한다 — 모델도 보고도 창도 모르고, 다른 프로그램이 청할 때 한 판을 돌려 주고 지금 모습을 읽게 내줄 뿐이다(아래 「약속」의
두 문). 정한 시각에 보고를 띄우는 쪽이 메일함을 새로 읽어야 하면 그 두 문으로 한 판을 청해 읽는다.

사람이 보는 것은 둘이다.

- **status** — 대화에서 「스캔 어때」 하시면 `scan.py status` 가 작업이 걸렸나 · 마지막 판 · 멈췄으면 까닭과 다음 걸음을 말한다
- **읽기** — 일일 보고 · 메일함 정리 · 대화가 쌓인 것을 `reader.py` 로 잘라 읽는다(지난번 뒤 온 메일 · 그 사이 사람이 한 일)

## 조각의 지도

손은 손가락을 차례로 엮기만 하고 손가락은 일 하나를 한다. 싣는 방향은 위에서 아래 한쪽이다 — 조각끼리 고리도, 함수 안에서 늦게 싣는
조각도 없다(함수 안에서 싣는 것은 표준 라이브러리 · 윈도 전용 모듈뿐이다). 이 스킬의 코드는 표준 라이브러리와 제 폴더 밖을 싣지 않는다 —
회사 메일 손은 명령으로 부르고, 다른 스킬의 파일은 사내 세션 파일 하나만 읽는다. 여러 손이 옆으로 함께 쓰는 것은 어느 손의 밑에도 안 두고
바탕에 둔다. 말을 짓는 조각(`scan_words`)은 파일 · 프로세스를 읽는 조각을 싣지 않고, 셈한 것을 받아 말만 짓는다.

아래는 코드에서 뽑은 지도다 — 모듈 표와 입구에서 내려가는 나무. 줄의 문장은 그 조각 머리말의 첫 문장이라, 문장을 고치려면 머리말을 고치고
다시 짓는다. 판이 어떤 차례로 엮이나(잠금 → 판 준비 → 판 하기 → 판 맺기)는 나무의 `scan_round.cmd_run` 아래가 든다.

<!-- drawn:piece-map · 손으로 고치지 않는다 — scripts/skill-map.py 가 짓는다 -->
| 조각 | 맡은 일 | 싣는 곁 조각 | 다른 스킬에서 싣는 것 |
|---|---|---|---|
| `scan.py` · 입구 | 메일함 스캔 — 회사 메일 손을 명령으로 불러 메일함의 지금을 사용자 폴더에 쌓고, 그 스캔을 작업 스케줄러에 걸고 · 보고 · 끈다. | `scan_const` · `scan_round` · `scan_setup` | — |
| `reader.py` · 입구 | 메일함 스캔이 쌓은 것을 잘라 읽는 명령 — 일일 보고 · 메일함 정리 · 대화가 스캔 파일을 직접 열지 않고 이것만 쓴다. | `hand_lines` · `scan_const` · `scan_diff` · `scan_store` · `scan_time` | — |
| `scan_round.py` | 스캔 한 판 — 잠금 쥐기 → 판 준비 → (세션을 기다리는 주기면 판 맺기로) 판 하기 → 판 맺기. | `hand_lines` · `scan_const` · `scan_diff` · `scan_hand` · `scan_identity` · `scan_store` · `scan_time` · `scan_words` · `session_login` | — |
| `scan_identity.py` | 보낸 분에 신원 붙이기 — 스캔이 쌓은 받은 메일의 보낸 분 주소마다 주소록 스킬의 신원 명령이 지은 신원을 지금 모습에 적는다. | `proc_base` · `scan_const` · `scan_diff` · `scan_time` | — |
| `scan_diff.py` | 두 지금 모습을 견주어 바뀜을 짓고, 그 바뀜을 누가 했나(사람 · 비서 · 모름)를 정리 스킬의 기록에 대어 가른다. | `scan_const` · `scan_store` · `scan_time` | — |
| `scan_setup.py` | 걸기 · 보기 · 끄기 · 다시 겨누기 — `scan.py register · status · unregister · adopt` 의 손. 작업 스케줄러의 작업 하나(`scan_task`)를 걸고 · 보이고 · 지우고 · 이 홈으로 다시 건다. | `scan_const` · `scan_hand` · `scan_store` · `scan_task` · `scan_time` · `scan_words` · `task_base` | — |
| `scan_hand.py` | 회사 메일 손 이음 — 손(스킬 company-mail 의 `scripts/mail.py`)을 찾고 명령으로 부른다. | `hand_lines` · `proc_base` · `scan_const` | — |
| `scan_store.py` | 스캔 파일의 자리와 쓰는 법 — 사용자 폴더 · 시각 · 한 번에 바꾸는 쓰기 · 덧붙이는 기록 · 한 판만 도는 잠금. | `scan_const` · `scan_time` | — |
| `scan_words.py` | 스캔 한 판의 말 — 판 끝 한 줄 · 판의 갈래와 끝 낱말 · 세션을 기다리는 주기의 말. 바깥에 안 닿고 셈은 안 한다. | `scan_const` · `scan_time` | — |
| `hand_lines.py` | 회사 메일 손의 글 풀기 — 손(스킬 company-mail 의 `scripts/mail.py`)이 찍은 사람용 글을 메일 머리 · 폴더 · 규칙으로 푼다. | `scan_const` | — |
| `scan_task.py` | 작업 스케줄러 손 — 작업 하나(`TASK_NAME`)가 몇 분마다 `scan.py run` 을 창 없이(pythonw) 부르게 정의를 짓고, 걸린 정의의 인자 · 간격을 거는 꼴로 되읽는다. | `scan_const` · `task_base` | — |
| `scan_time.py` | 스캔의 시각 — 저장은 UTC ISO 8601(사전순이 시간순이다), 보이기는 서울(+09:00 고정 — `zoneinfo` 는 윈도에서 `tzdata` 가 따로 들어 안 쓴다). 파일 · 프로세스에 안 닿는다. | `scan_const` | — |
| `session_login.py` | 사내 세션 파일의 자리 — 회사 메일 손이 쓰는 세션 파일이 어디 있나를 댄다. | `scan_const` | — |
| `scan_const.py` | 메일함 스캔의 이름 붙은 값 — 자리 · 파일 이름 · 상한 · 주기. 스캔 스크립트가 다 여기서 읽는다. | `hand_facts` | — |
| `hand_facts.py` | 메일함 스캔이 기대는 형제 스킬의 사실 — 회사 메일 손의 자리 · 종료 값 · 시한, 로그인이 사는 스킬, 사내 세션의 답 낱말, 세션이 끊겼을 때 사람에게 이를 다음 걸음. | — | — |
| `proc_base.py` | 프로세스 바탕 — 곁의 파이썬 손(회사 메일 손 · 형제 스킬의 입구)을 창 없이 · UTF-8 로 띄우는 한 자리. | — | — |
| `task_base.py` | 작업 스케줄러 바탕 — 비서의 작업 하나를 schtasks · PowerShell 로 걸고 · 묻고 · 지우고 · 정의를 받나 묻고, 그 답을 푼다. | — | — |

**입구에서 내려가는 나무** — 줄마다 조각과 그 머리말 첫 문장. 한 조각은 처음 닿은 자리에서만 펴고 다시 닿으면 `↑` 로 가리킨다. 클래스는 메서드를 그 아래에 든다. `←` 뒤는 그 조각을 부르는 다른 스킬이다. 인스턴스를 거친 부름은 이어지지 않는다.

- `main` — 읽는 명령의 입구 — 스캔을 열어 하위 명령에 나눈다.
  - `parser` — 명령줄의 꼴 — 하위 명령 · 인자 · 도움말.
    - `span_word` — 몇 시간 전의 한 구절 — 하루 단위면 「N일쯤 전」.
  - `moment` — 「YYYY-MM-DD HH:MM」 · 「YYYY-MM-DD」(서울) → 시각. 없으면 `default`. 꼴이 틀리면 argparse 의 오류로 나간다.
  - `scan_time.now` — 지금(UTC).
  - `open_scan` — 읽는 명령 한 번이 쥘 스캔 — 스캔 파일이 없거나 못 읽으면 그렇다고 찍고 종료 값 3.
    - `scan_store.load_state` — 지금 모습 한 장 — (판, 깨진 까닭). 파일이 없으면 (None, ""), 글이 깨졌거나 꼴 번호가 다르면 (None, 까닭) — 메일함에서 다시 지어도 되는 판. 있는데 못 읽었으면(다른 손이 쥐었다) `Unreadable` 이 그대로 나간다 — 그 판을 깨진 것으로 읽어 다시 지으면 그날 띄운 보고 · 보낸 메일의 기록이 사라져 두 번 띄우고 두 번 보낸다.
      - `read_json` — 스캔 자리의 JSON 파일 한 장 — 답은 셋이다: 없으면 None · 읽었으면 그 dict · 있는데 못 읽었으면 `Unreadable`. 꼴 번호는 부르는 쪽이 본다.
        - `_read_bytes` — 파일 그대로 — 없으면 FileNotFoundError, 있는데 못 읽으면 `Unreadable`. ⚠ 윈도에서는 다른 프로세스가 그 파일을 새 판으로 바꿔 끼우는 그 순간 읽기가 PermissionError 로 진다 — 쓰는 쪽(`_swap`)이 기다리는 것과 같은 수만큼 기다려 다시 읽는다.
          - `Unreadable` — 파일은 있는데 못 읽었다 — 「없다」가 아니다.
        - ↑ `Unreadable`
      - ↑ `Unreadable`
    - `scan_store.scan_dir` — 사용자 폴더 안의 스캔 자리 — `make` 면 없을 때 만든다.
      - `home` — 사용자 폴더 — `MAIL_SECRETARY_HOME` 이 있으면 그 자리, 없으면 `%LOCALAPPDATA%\mail-secretary`(이름의 원본과 사본은 scan_const 「자리」).
    - ↑ `scan_store.Unreadable`
    - `Scan` — 읽는 명령 한 번이 쥐는 것 — 지금 모습 · 지금.
    - ↑ `scan_time.now`
  - `cmd_status` — status — 최근 하루의 판 수 · 건너뛴 주기 · 마지막 판 다섯의 값을 보인다.
    - `scan_store.read_jsonl` — 덧붙인 기록 전부(옛것부터)와 못 읽은 줄의 수 — 반쯤 써진 끝 줄 · 깨진 줄은 건너뛴다.
      - ↑ `_read_bytes`
    - ↑ `scan_store.scan_dir`
    - `scan_time.stamp` — 저장할 글자 — UTC ISO 8601. 사전순이 시간순이다.
    - `scan_time.seoul` — 시각을 서울 글자로 — 없으면 빈 글.
    - `scan_time.parse` — 저장된 글자 · 시간대가 붙은 ISO 글자(정리 스킬의 기록)를 시각으로. 못 읽거나 시간대가 없으면 None.
    - `framed` — 머리 · 스캔의 때와 상태 · 자료 구역 안의 몸 · 꼬리를 찍는다 — 메일함의 글은 자료 구역 안에만 선다.
      - `state_lines` — 스캔의 때와 지금 상태 — 읽는 쪽이 낡음을 가르고, 멈췄으면 그 까닭과 때를 사용자께 말씀드린다.
        - `ago` — 때와 지금으로부터 얼마 전인가의 한 구절 — 없으면 「없다」.
          - ↑ `scan_time.seoul`
        - ↑ `scan_time.parse`
        - ↑ `scan_time.seoul`
        - `place_name` — 자리를 손의 말로 — 받은편지함 · 보낸편지함 · 「폴더 <경로>」.
  - `cmd_new` — new — 그 시각 뒤 새 메일(때나 스캔이 처음 본 때가 그 뒤)을 지금 자리 · 읽음과 함께 새것부터 보인다.
    - ↑ `moment`
    - ↑ `scan_store.read_jsonl`
    - ↑ `scan_store.scan_dir`
    - `scan_time.mail_time` — 메일의 때(서울 글자) → 시각. 그 꼴이 아니면 None — 때를 모르는 메일이다.
    - ↑ `scan_time.parse`
    - `newest_first` — 메일을 새것부터(때 · 번호 차례) 늘어놓는다.
    - `mail_line` — 메일 한 줄 — 손의 목록 줄과 같은 꼴. `extra` 는 메일 번호 앞에 붙이는 이 스킬의 말이다.
      - ↑ `place_name`
      - `person_of` — 메일 한 통의 사람 칸 — 받은 메일은 보낸 분(「이름 <주소>」 · 주소 · 이름), 보낸 메일은 받는 분.
      - `identity_words` — 보낸 분 신원의 한 구절 — 회사 › 부서 경로 · 직급(등급) · 직책 · 장 · 퇴직 · 근무지 · 담당업무(출처) · 고름. 여럿이면 후보 수, 고름 넷 어디에도 없으면 「주소록에 없음」, 아직 모르면 「신원 모름」. 주소가 없는 메일은 빈 글자다.
    - ↑ `scan_time.seoul`
    - `count_word` — 메일 묶음의 수 한 구절 — 받은 메일이 들면 안 읽음 수도.
    - ↑ `framed`
    - `paged` — 한 쪽 — `skip` 뒤 `most` 줄과, 잘렸으면 이어 받을 `--skip` 값을 대는 끝 줄.
  - `cmd_now` — 지금 모습 — 상자마다 · 보낸 분마다 · 제목 말머리마다 · 규칙의 보기를 차례로 엮는다.
    - ↑ `scan_time.seoul`
    - ↑ `scan_time.parse`
    - `box_lines` — 상자마다 수 · 안 읽음 — 받은편지함 · 폴더 목록 차례 · 보낸편지함 · 새 메일로 처음 선 폴더, 그리고 휴지통 · 못 채운 보낸 분.
      - ↑ `place_name`
      - ↑ `count_word`
    - `by_place` — 메일을 자리(상자 · 폴더)마다 묶는다.
      - `scan_diff.place` — 메일 한 통의 자리 — (상자, 폴더 경로).
    - `sender_lines` — 보낸 분마다(받은 메일) 셈 — 많은 차례로 `top` 곳(그 신원과 함께), 나머지는 한 줄.
      - ↑ `person_of`
      - ↑ `newest_first`
      - ↑ `identity_words`
      - ↑ `count_word`
      - `when_word` — 메일의 때 글자를 분까지 — 없으면 「때 모름」.
    - `head_lines` — 제목 말머리마다(`HEAD_MIN` 통 이상) 셈 — 많은 차례로 `top` 개.
      - ↑ `count_word`
    - `rule_lines` — 메일 규칙 — 마지막 판에서 못 읽었으면 그 앞 판의 것이라고 댄다.
    - ↑ `framed`
  - `cmd_changes` — changes — 그 시각 뒤 바뀜을 바꾼 이와 함께 새것부터 보인다.
    - ↑ `moment`
    - ↑ `scan_store.read_jsonl`
    - ↑ `scan_store.scan_dir`
    - ↑ `scan_time.parse`
    - `event_line` — 바뀜 한 줄 — 때 · 무엇 · 바꾼 이, 메일의 바뀜이면 그 메일 줄.
      - ↑ `scan_time.seoul`
      - ↑ `scan_time.parse`
      - ↑ `place_name`
      - ↑ `mail_line`
    - ↑ `scan_time.seoul`
    - ↑ `framed`
    - ↑ `paged`
  - `cmd_mails` — mails — 고르기(자리 · 보낸 분 · 제목 · 안 읽음 · 때 범위)에 다 맞는 메일을 새것부터 보인다.
    - ↑ `person_of`
    - ↑ `moment`
    - ↑ `scan_time.mail_time`
    - ↑ `newest_first`
    - ↑ `count_word`
    - ↑ `framed`
    - ↑ `paged`
    - ↑ `mail_line`
  - `cmd_signals` — 정리 신호의 재료 — 받은편지함 지금 · 흐름 · 규칙이 채우는 폴더 · 폴더마다 가장 새 때의 보기를 차례로 엮는다(수와 때만).
    - ↑ `scan_store.read_jsonl`
    - ↑ `scan_store.scan_dir`
    - ↑ `by_place`
    - ↑ `ago`
    - ↑ `scan_time.parse`
    - ↑ `count_word`
    - `flow_lines` — 받은편지함 흐름 — 메일함 전체를 다 본 판마다 센 수에서 가장 늦은 판 · 하루쯤 전 · 이레쯤 전 · 기록이 닿는 데.
      - ↑ `ago`
      - ↑ `span_word`
      - ↑ `scan_time.seoul`
    - `full_counts` — 판 기록에서 메일함 전체를 다 본 판마다 센 받은편지함 \[통 수, 안 읽음\](옛것부터) — 스캔(`scan_round.inbox_count`)이 그 판에 실은 셈이다.
      - ↑ `scan_time.parse`
    - `rule_target_lines` — 규칙이 채우는 폴더 — 폴더로 옮기는 규칙의 폴더마다 수 · 지금 폴더 목록에 있나 · 규칙 수.
      - `hand_lines.rule_folder` — 규칙 글(`parse_rules` 의 text) → 그 규칙이 메일을 옮기는 폴더의 경로. 폴더로 옮기지 않는 규칙이면 None. 동작 칸은 조건 뒤에 서므로 마지막 표지에서 자른다 — 조건 값에 그 낱말이 들어도 안 헷갈린다.
      - ↑ `place_name`
      - ↑ `count_word`
    - `folder_age_lines` — 폴더마다 가장 새 메일의 때 — 옛것부터, 메일 없는 폴더가 맨 앞.
      - ↑ `scan_time.mail_time`
      - ↑ `scan_time.seoul`
      - ↑ `place_name`
      - ↑ `count_word`
    - ↑ `framed`
- `main` — 명령 입구 — 받은 하위 명령을 그 손에 나눈다.
  - `parser` — 명령줄의 꼴 — 하위 명령 · 인자 · 도움말.
  - `scan_round.cmd_run` — 한 판(`scan.py run`) — 판 하나의 잠금을 쥐고(`--wait` 면 그 초 안에서 앞 판을 기다려) 판을 맡긴다(`play`). 못 쥐면 「건너뛰었다」를 판 기록에 적고, 판이 기대는 파일을 못 읽으면 판 기록에만 적고 멈춘다(`unread`). 종료 값 — 0 됐다(앞 판이 돌아 건너뛴 것도) · 1 멈췄다.
    - ↑ `scan_store.scan_dir`
    - `scan_store.Lock` — 도는 판 하나의 잠금(O_EXCL) — `LOCK_STALE_S` 보다 오래된 잠금은 푼다.
      - `Lock.take` — 쥔다 — (잠금, 풀어 준 옛 잠금). 도는 판이 있으면 (None, 그 판의 잠금).
        - `held_since` — 잠금 파일 하나(`{started, …}`) — 없으면 None. 있는데 못 읽으면 `{"started": 그 파일의 고친 때}` 로 낸다(그 때로 낡음을 잰다). 고친 때도 못 보면 지금으로 낸다 — 그 잠금을 도는 판의 것으로 둔다.
          - ↑ `read_json`
          - ↑ `Unreadable`
          - ↑ `scan_time.now`
          - ↑ `scan_time.stamp`
        - ↑ `scan_time.parse`
        - ↑ `scan_time.stamp`
      - `Lock.wait` — 도는 판이 있으면 `seconds` 초 안에서 그 잠금이 풀리기를 기다렸다 쥔다 — 사이(`LOCK_WAIT_POLL_S`)마다 잠들었다 `take` 로 다시 쥐어 본다.
        - ↑ `scan_time.now`
        - ↑ `Lock.take`
      - `Lock.owns` — 이 판이 아직 잠금을 쥐었나 — 잠금 파일의 열쇠가 제 열쇠인가.
        - ↑ `held_since`
      - `Lock.release` — 제 잠금이면 푼다.
        - ↑ `Lock.owns`
    - `scan_store.append` — 줄을 덧붙인다 — 있는 줄은 안 고친다.
    - `busy_record` — 앞 판이 돌아 건너뛴 주기의 기록 한 줄 — 앞 판의 시작 때를 함께 적고, 기다렸으면(`--wait`) 기다린 초를 메모로 단다.
      - ↑ `scan_time.stamp`
      - `scan_words.waited_note` — 판 기록의 메모 — 앞 판의 잠금이 풀리기를 기다린 초(`run --wait`).
    - ↑ `scan_time.parse`
    - `scan_words.gave_up_words` — 앞 판을 준 시한만큼 기다렸는데 안 끝나 이번 판을 그만둔 한 줄(`run --wait`) — 앞 판의 시작 때 · 기다린 초와 함께.
      - ↑ `scan_time.seoul`
    - `scan_words.busy_words` — 앞 판이 돌아 이번 주기를 건너뛴 한 줄 — 앞 판의 시작 때와 함께.
      - ↑ `scan_time.seoul`
    - `play` — 판 하나를 엮는다 — 지금 모습 · 손 · 손의 능력을 갖추고, 세션을 기다리는 주기면 판 없이 맺고, 아니면 판을 하고 맺는다.
      - `ready_state` — 판이 고칠 지금 모습 — 글이 깨진 판은 `.broken` 으로 옮겨 두고 새로 시작한다.
        - ↑ `scan_store.load_state`
        - ↑ `scan_words.waited_note`
        - ↑ `scan_time.seoul`
        - ↑ `scan_time.parse`
        - `fresh_state` — 지금 모습이 없을 때의 빈 판.
      - `note_full_every` — 준 전체 주기(`--full-every`)를 지금 모습에 적는다 — 걸린 작업의 판은 늘 그 값을 주므로, 주기를 안 준 판(정한 시각의 시계가 청한 판 · 대화의 판)이 그 PC 가 건 주기를 읽는다(`full_every_of`). 안 줬으면 아무것도 안 한다.
      - `scan_hand.find_hand` — 손 `mail.py` 의 자리 — `--hand` → `MAILBOX_SCAN_HAND` → 스킬 뿌리들 차례. 어디에도 없으면 `HandMissing`.
        - `HandMissing` — 회사 메일 손을 못 찾았다 — 글자가 어디를 봤는지 말한다.
        - `skill_roots` — 볼 스킬 뿌리 — `SECRETARY_SKILLS` 가 있으면 그것 하나, 없으면 도구 홈 셋.
      - ↑ `scan_hand.HandMissing`
      - `finish` — 판을 맺는다 — 판 기록을 짓고, 잠금을 잃었으면(풀린 판이 깨어났다) 아무것도 안 쓰고, 아니면 바뀜 · 지금 모습 · 판 기록을 쓰고 판 끝 한 줄을 낸다.
        - `round_record` — 판 기록 한 줄 — 때 · 갈래 · 끝 · 손 부르기 · 줄 · 초 · 새 메일과 바뀜의 수 · 판 값 · 메모, 메일함 전체를 다 본 판은 받은편지함 셈.
          - ↑ `scan_time.stamp`
          - ↑ `scan_time.now`
          - `inbox_count` — 받은편지함의 [통 수, 안 읽음] — 자리를 확인 중인 메일은 뺀다.
        - `save_round` — 판을 쓴다 — 바뀜마다 판의 때를 달고, 지금 모습에 마지막 판을 적고, 바뀜 → 접기 → 지금 모습 → 판 기록 차례로 쓴다.
          - ↑ `scan_store.append`
          - `compact` — 오래된 새 메일 · 바뀜 · 판 기록을 접고 사라진 메일의 기억을 덜어 낸다 — 하루에 한 번. 지금 모습은 늘 한 장이다.
            - ↑ `scan_time.parse`
            - ↑ `scan_time.stamp`
            - ↑ `scan_store.read_jsonl`
            - ↑ `scan_store.Unreadable`
            - `scan_store.rewrite_jsonl` — 기록을 새로 쓴다(오래된 줄을 접을 때) — 새 파일에 다 쓴 뒤 바꿔 끼운다.
              - `_temp_of` — 쓰는 쪽마다 따로인 새 파일 — 두 프로세스가 같은 파일을 함께 쓰면(스캔 판과 창 곁의 손) 한 이름의 새 파일을 서로 비우고 옮겨, 반쯤 써진 판이 제자리에 서거나 한쪽이 FileNotFoundError 로 진다.
              - `_swap` — 다 쓴 새 파일을 제자리에 바꿔 끼운다.
                - `SwapFailed` — 새 판을 다 썼는데 바꿔 끼우지 못했다 — 읽는 쪽이 오래 쥐고 있다.
          - `scan_store.write_json` — 새 파일에 다 쓰고 디스크에 내린 뒤 한 번에 바꿔 끼운다(`_swap`) — 반쯤 써진 판은 어디에도 안 선다.
            - ↑ `_temp_of`
            - ↑ `_swap`
          - ↑ `scan_store.SwapFailed`
        - `scan_words.summary` — 판 끝의 한 줄 — 수와 때만(메일의 글은 안 싣는다).
      - `Ended` — 한 판의 끝 — 판의 갈래 · 끝 낱말 · 바뀜 · 판 값(판 기록에 싣는다).
      - `session_back` — 세션이 끊긴 뒤 이번 주기에 두드려도 되나 — (돈다, 끊긴 때, 다음 두드림). 세션 파일이 끊긴 뒤 새로 쓰였거나 다음 두드림 때가 왔거나 `--now` 면 돈다.
        - ↑ `scan_time.parse`
        - `session_login.session_file` — 손이 쓰는 세션 파일의 자리 — `MAILBOX_COOKIES`, 없으면 형제 스킬 ep-login 의 받는 손 곁 `places.json` 의 기본 자리. 모르면 None.
      - `scan_words.waiting_words` — 세션이 끊겨 이번 주기를 안 도는 까닭과 다음 걸음.
        - ↑ `scan_time.seoul`
      - `read` — 판 하기 한 번 — 손의 능력을 보고, 「list --since」 없는 옛 손이면 판을 안 하고, 아니면 판을 한다(`sweep`). `since` 는 시간의 상한을 잴 시작이다(`Run`). 내는 것 — (판의 끝, 그 셈).
        - `hand_probe` — 손이 받는 명령(`list --since` · `serve`) — 손 파일이 바뀌었을 때만 손에 묻고 지금 모습에 적는다.
          - `scan_hand.has_since` — 「list --since」를 받는 판인가 — 손의 `list --help` 에 그 깃발이 서나로 묻는다(그 깃발이 없는 옛 판의 손이 깔린 PC 도 있다).
            - `call` — 손 한 번 — 종료 값 · 표준 출력의 줄 · 0 이 아닐 때의 까닭. 표준 오류(손의 경고)는 안 읽는다.
              - `proc_base.run_python` — 곁의 파이썬 스크립트 한 번 — 창 없이 · UTF-8 로 띄워 출력을 받는다.
                - `python_argv` — 곁의 파이썬 스크립트를 지금 파이썬으로 부르는 명령줄 — `-X utf8 -I`(UTF-8 · 사용자 자리의 모듈을 안 싣는다).
                - `utf8_env` — 띄운 파이썬이 출력을 UTF-8 로 내게 하는 환경 — 지금 환경에 `PYTHONIOENCODING` 만 얹는다.
                - `quiet` — 창 없는 실행(작업 스케줄러의 pythonw)에서 띄운 손 · 손이 띄우는 node 가 콘솔 창을 안 띄우게 하는 `subprocess` 인자 — 창 없는 콘솔을 준다.
              - `_timed_out` — 시한을 넘긴 손의 답 — 손의 종료 1 과 같게, 까닭은 시한이다.
                - `Called` — 손 한 번의 답 — 종료 값 · 표준 출력의 줄 · 0 이 아닐 때의 까닭 · 물은 명령.
              - `_called` — 손의 종료 값 · 표준 출력 → `Called`. 출력을 UTF-8 로 못 풀면 `ShapeError`.
                - `hand_lines.ShapeError` — 손의 글이 이 파일이 아는 꼴이 아니다 — 메일의 글은 싣지 않고 어느 명령의 몇째 줄인지만 댄다.
                - ↑ `Called`
          - `scan_hand.has_serve` — 명령 여럿을 한 프로세스로 받는 판인가(`serve`) — 없는 옛 판의 손이면 명령마다 `call` 로 부른다.
            - ↑ `call`
        - `Run` — 한 판의 셈 — 손 부르기 · 받은 줄 · 시간의 상한. 손이 `serve` 를 받으면 판 내내 손 하나에 잇달아 묻고(`H.Served`), 옛 판의 손이면 명령마다 띄운다(`H.call`) — 어느 쪽이든 메일함에 가는 요청과 그 차례는 같다.
          - `scan_hand.Served` — 손 하나(`mail.py serve`)를 판 내내 띄워 두고 명령을 하나씩 묻는다 — 명령마다 파이썬을 새로 안 띄운다.
            - `Served._start` — 손 하나를 `serve` 로 띄우고 그 답을 큐로 받는 일꾼을 세운다.
              - ↑ `proc_base.python_argv`
              - ↑ `proc_base.utf8_env`
              - ↑ `proc_base.quiet`
              - `_read_answers` — 손의 답을 하나씩 큐에 넣는다 — (머리, 몸) · 답 머리가 아닌 줄이 오면 그 줄부터 끝까지의 바이트 · 끝(답이 다 오기 전의 끝 포함)이면 None.
            - `Served._drop` — 손을 거둔다 — 그 손의 종료 값(거둬서 끝났으면 그 값).
            - `Served.ask` — 띄워 둔 손에 명령 하나를 묻는다 — 답의 꼴과 뜻은 `call` 과 같다.
              - ↑ `Served._drop`
              - ↑ `Served._start`
              - ↑ `Called`
              - ↑ `_timed_out`
              - ↑ `_called`
              - ↑ `hand_lines.ShapeError`
            - `Served.close` — 표준 입력을 닫아 손이 스스로 끝나게 한다 — 안 끝나면 거둔다.
          - ↑ `scan_time.now`
          - `Run.over_budget` — 한 판의 시간 상한(`RUN_BUDGET_S`)을 넘었나.
          - `Run.hand` — 손에 명령 하나를 묻고 셈한다 — 세션 없음(종료 3)이면 `SessionLost`.
            - ↑ `scan_hand.call`
            - `SessionLost` — 손이 종료 3 을 냈다 — 사내 세션이 없다 · 끊겼다.
          - `Run.close` — 띄워 둔 손을 거둔다.
          - `Run.seconds` — 이 셈을 세운 뒤 지난 초 — 판 하기(손 부르기 · 풀기 · 견주기)가 다 든다.
        - ↑ `Ended`
        - `sweep` — 판을 골라(전체 · 새 메일) 돌리고 손을 거둔 뒤, 손이 멈춘 까닭을 끝 낱말로 바꾼다.
          - `wants_full` — 이 판이 메일함 전체를 봐야 하나 — `--full` · 지금 모습이 없다 · 전체 판을 해 본 적이 없다 · 전체 주기(`full_every_of`)가 지났다(`--new` 가 아니면).
            - ↑ `scan_time.parse`
            - `full_every_of` — 이 판의 전체 주기(분) — 준 것(`--full-every`), 없으면 걸린 작업의 판이 마지막으로 준 것(`note_full_every`), 그것도 없으면 기본.
          - `run_full` — 메일함 전체 판 — 폴더 · 규칙을 받고, 이어 볼 상자를 잇고, 상자를 돌고, 덜 봤으면 다 본 상자를 남기고(그 새 메일은 적는다), 다 봤으면 한 모습으로 합쳐 지난 모습과 견주고 새 지금 모습을 짓는다.
            - `mailbox_frame` — 폴더 목록과 규칙을 손에서 받는다 — 규칙을 못 받으면 지난 모습의 규칙을 그대로 쓴다.
              - `HandFailed` — 손이 0 · 3 밖의 종료 값을 냈다 — `said` 가 손의 말이다.
              - `hand_lines.parse_folders` — 폴더 목록(`folders`) → 폴더 경로들 — 끝 줄이 댄 수와 줄 수를 견준다.
                - `_bad` — 손의 글이 꼴이 아닌 자리 — 어느 명령의 몇째 줄인지와 까닭만 실은 `ShapeError`.
                  - ↑ `ShapeError`
              - `hand_lines.parse_rules` — 메일 규칙 목록(`rules`) → [{unid, text}] — 끝 줄이 댄 수와 줄 수를 견준다.
                - ↑ `_bad`
              - `Frame` — 전체 판의 틀 — 폴더 목록 · 규칙 · 규칙을 이번에 읽었나 · 볼 상자들.
            - `resume` — 이어 볼 상자들 — 다 못 본 판이 남긴 다 본 상자. 폴더 목록이 그 사이 바뀌었으면 버리고 처음부터 본다.
              - `load_pending` — 다 못 본 판의 다 본 상자들 — 없거나 못 읽으면 None(메일함에서 다시 읽으면 되는 이음 자료라 처음부터 본다). 기한(`PENDING_MAX_MIN`)을 넘은 상자 그림은 버린다.
                - ↑ `scan_store.read_json`
                - ↑ `scan_store.Unreadable`
                - ↑ `scan_time.parse`
            - `walk_boxes` — 다 본 상자(`done`)를 건너 상자마다 끝까지 읽어 `done` 에 더한다 — 판의 시간 상한을 넘으면 남은 상자는 덜 본 자리다.
              - `scan_diff.box_key` — 상자의 열쇠 — 폴더면 「folder:<경로>」, 아니면 상자 이름.
              - `sweep_box` — 상자 하나를 끝까지 읽는다 — 끝을 가르는 법은 `references/DESIGN.md` 「상자 하나를 끝까지」. 내는 것 — {mails, complete, why, said, unfilled, read_at, paged — 한 번에 다 못 받은 상자인가(쪽이 찼거나 둘째 쪽에 줄이 왔다)}.
                - ↑ `scan_time.stamp`
                - ↑ `scan_time.now`
                - `hand_lines.parse_list` — 상자 하나의 한 쪽(`list` · `list --folder` · `list --sent` 에 --count · --start) → 메일 머리와 수.
                  - ↑ `_bad`
                  - `Listed` — 한 상자의 한 쪽 — 메일 머리 · 끝 줄이 댄 수 · 보낸 분을 못 채운 폴더 메일 수.
                  - `_sent` — 보낸편지함 줄 → 메일 머리. 받는 분은 손의 목록이 준 첫 사람(들)이다.
                    - `_date` — 손이 찍은 때 → 쌓는 꼴(초까지). 분까지인 꼴(폴더 줄)은 「:00」 을 붙여 맞춘다.
                  - `_received` — 받은편지함 · 폴더 줄(`entry_line`) → 메일 머리. 꼴이 아니면 None.
                    - `_split_place` — 「자리 · 나머지」 → (상자, 폴더 경로, 나머지). 폴더 경로는 아는 폴더 가운데 가장 긴 것부터 맞추고, 없으면 첫 가름에서 끊는다.
                    - ↑ `_date`
                    - `_sender` — 손의 보낸 분 칸(`who_sent`) → 이름 · 주소 · 못 채움.
            - ↑ `SessionLost`
            - ↑ `scan_time.stamp`
            - `save_pending` — 다 본 상자들을 이어 볼 파일에 남긴다 — 다음 판이 잇는다.
              - ↑ `scan_store.write_json`
            - `scan_diff.Journal` — 정리 스킬의 기록(`rows` · 옛것부터)과 잡아 둔 채인 바꿈(`held`). 묻는 쪽이 그 바뀜이 일어났을 수 있는 때의 처음(`since`)을 준다 — 그 뒤의 기록만 댄다.
              - `Journal.load` — 정리 스킬의 기록을 읽는다 — 있는데 못 읽으면 `st.Unreadable` 이 그대로 나간다(판이 멈춘다): 잡아 둔 바꿈을 빈 것으로 읽으면 비서가 하는 중인 옮김을 사람이 한 일로 바뀜 기록에 굳힌다.
                - ↑ `scan_store.read_jsonl`
                - ↑ `scan_store.read_json`
                - ↑ `scan_store.Unreadable`
              - `Journal._within` — `since` 뒤의 기록 — 때를 못 읽은 기록은 남긴다(사람 탓으로 안 돌린다). `since` 가 없으면 다.
                - ↑ `scan_time.parse`
              - `Journal._target` — 그 바꿈이 메일을 보낸 자리 — 옮기기는 받은편지함이나 그 폴더, 휴지통으로는 None(목록에서 사라진다).
              - `Journal._touches` — 정리 기록 한 줄이 그 메일에 닿았나.
              - `Journal.mail_by` — 메일 한 통의 바뀜(옮겨짐 `to` · 사라짐 `to=None` · 다시 나타남)을 누가 했나.
                - ↑ `Journal._touches`
                - ↑ `Journal._within`
                - ↑ `Journal._target`
              - `Journal.folder_by` — 폴더 하나의 생김 · 없어짐을 누가 했나.
                - ↑ `Journal._within`
              - `Journal.rule_by` — 규칙 하나의 생김 · 바뀜 · 없어짐을 누가 했나.
                - ↑ `Journal._within`
            - ↑ `scan_store.home`
            - `add_new` — 처음 보는 메일을 지금 모습에 더하고 그 바뀜을 낸다 — 아는 메일은 안 건드린다(바뀜은 전체 판의 견주기가 낸다).
              - ↑ `scan_time.stamp`
              - ↑ `scan_time.parse`
              - `scan_diff.new_mail` — 처음 보는 메일 하나 → (지금 모습에 넣을 줄, 바뀜). 사라졌다고 적은 메일이면 「다시 나타남」이다.
                - ↑ `place`
                - ↑ `scan_time.parse`
                - `head` — 바뀜에 실어 두는 메일 머리 — 사라진 뒤에도 읽는 명령이 그 메일을 말할 수 있게.
                - `opened_before_seen` — 처음 보는 받은 메일이 이미 읽음이고, 지난번 본 때 뒤에 온 메일인가 — 사람이 스캔보다 먼저 연 것이다.
                  - ↑ `scan_time.mail_time`
            - `one_picture` — 다 본 상자들을 메일함 한 모습으로 합친다 — 두 상자에 선 메일은 나중에 읽은 상자가 지금 자리다(읽는 사이 옮겨졌다). 내는 것 — (상자마다 읽은 때, 메일 번호마다 메일).
              - ↑ `scan_diff.box_key`
            - `compare_picture` — 다 본 메일함을 지난 모습과 견줘 메일 · 폴더 · 규칙의 바뀜을 내고 지금 모습의 메일을 고친다 — 지난 모습이 없으면 바닥만 적는다(첫 판). 내는 것 — (끝 낱말, 바뀜).
              - ↑ `scan_time.stamp`
              - ↑ `scan_time.parse`
              - `scan_diff.compare_folders` — 폴더 목록의 바뀜(생김 · 없어짐)과 바꾼 이를 낸다.
              - `scan_diff.compare_rules` — 메일 규칙의 바뀜(생김 · 바뀜 · 없어짐)과 바꾼 이를 낸다.
              - `scan_diff.compare` — 앞 모습(`prev` · 그 판을 보기 시작한 때 `prev_started`)과 이번에 다 본 상자들(`seen` — 메일 번호 → 머리 · `read_at[상자 열쇠]`)을 견준다.
                - ↑ `new_mail`
                - ↑ `scan_time.parse`
                - ↑ `place`
                - ↑ `head`
                - `recalled` — 보낸 메일을 회수했나 — 수신상태 낱말에 「회수」가 든다.
                - ↑ `box_key`
            - `new_picture` — 다 본 판의 새 지금 모습 — 메일함의 그림(때 · 폴더 · 규칙 · 상자마다 읽은 때) · 이음점 · 다 본 때를 적는다.
              - ↑ `scan_time.stamp`
              - ↑ `scan_time.now`
              - `latest_cursor` — 다 본 메일함에서 다시 잡은 이음점 — 자리를 확인 중이 아닌 메일 가운데 가장 늦은 때(지금보다 뒤면 지금). 때 있는 메일이 없으면 None.
                - `not_ahead` — 메일의 때 글자를 지금보다 뒤가 아니게 — 앞날의 때를 단 메일 하나가 이음점을 앞질러 보내 그 사이 메일을 놓치지 않게.
                  - ↑ `scan_time.seoul`
            - `drop_pending` — 다 본 판이 이어 볼 파일을 걷는다.
          - `run_new` — 새 메일 판 — 「이 시각 뒤」 쪽을 다 받고, 다 봤나를 가르고, 처음 보는 메일을 더하고, 다 봤으면 이음점을 옮긴다.
            - `cursor_date` — 「이 시각 뒤」의 시각 — 이음점(가장 늦은 메일의 때)이고, 지금보다 뒤면 지금이다(앞날의 때를 단 메일 하나가 이음점을 앞질러 보내지 않게).
              - ↑ `scan_time.seoul`
              - ↑ `scan_time.parse`
              - ↑ `not_ahead`
            - `since_pages` — 「이 시각 뒤」 목록을 끝까지(--start 로 이어) 받는다 — 쪽 수의 안전 상한에 닿으면 다 못 본 것이다.
              - `SincePages` — 「이 시각 뒤」 목록을 끝까지 이어 받은 것 — 메일(번호마다 처음 것) · 쪽마다 댄 총수 · 다 봤나 · 못 내려간 자리 · 가장 늦은 메일.
              - ↑ `HandFailed`
              - `hand_lines.parse_since` — 「이 시각 뒤」 목록(`list --since … --start N`) 한 쪽 → 메일 머리 · 끝 줄들이 댄 것. 메일 줄 수를 끝 줄의 차례와 견준다.
                - `Since` — 「이 시각 뒤」 목록 한 쪽.
                - ↑ `_bad`
                - ↑ `_sent`
                - ↑ `_received`
            - `saw_all` — 「이 시각 뒤」 목록을 다 봤나 — 손이 다 봤다고 했고, 못 내려간 자리가 없고, 쪽마다 댄 총수가 하나다(받는 사이 목록이 안 바뀌었다).
            - ↑ `add_new`
            - ↑ `scan_diff.Journal`
            - ↑ `scan_store.home`
            - ↑ `scan_time.mail_time`
            - ↑ `not_ahead`
            - ↑ `scan_time.stamp`
            - `since_short` — 새 메일 판이 덜 본 자리 — 손이 훑는 상한에 닿은 상자마다, 그런 상자 없이 덜 봤으면 받은편지함 하나(목록이 바뀌었나 · 안전 상한).
              - ↑ `scan_diff.box_key`
          - ↑ `SessionLost`
          - `mark_session_lost` — 끊긴 세션을 적는다 — 다음 두드림 때를 두 배씩(상한까지) 늘린다.
            - ↑ `scan_time.stamp`
          - ↑ `Ended`
          - ↑ `HandFailed`
          - ↑ `hand_lines.ShapeError`
          - `settle` — 손이 답한 판의 지금 모습 — 세션 기다림을 걷고, 다 본 판이면 본 때를 적는다.
            - ↑ `scan_time.stamp`
          - `identity_info` — 손이 답한 판의 끝에 보낸 분 신원을 붙인다(`scan_identity.attach`) — 판 값의 이름을 판 기록의 칸으로 옮긴다.
            - `scan_identity.attach` — 물을 주소(`wanted`)의 신원을 신원 명령으로 받아 지금 모습의 `senders` 에 적는다 — 「모름」 은 안 적는다.
              - `wanted` — 신원을 물을 주소 — 받은 메일(보낸편지함 밖)의 보낸 분 모두, 새 메일의 보낸 분이 먼저다.
              - `find_identity` — 신원 명령의 자리 — `MAILBOX_SCAN_IDENTITY` → 회사 메일 손과 같은 스킬 뿌리. 없으면 None.
              - `call` — 신원 명령 한 번 — (답, 못 받은 까닭). 답이 꼴이 아니면 (None, 까닭).
                - ↑ `proc_base.run_python`
              - ↑ `scan_time.stamp`
    - ↑ `scan_store.Unreadable`
    - `unread` — 판이 기대는 파일을 못 읽어 멈춘다 — 지금 모습 · 바뀜 · 보고는 안 건드리고(빈 것으로 읽어 덮으면 그 기록이 사라진다) 판 기록에만 적는다.
      - `unread_record` — 못 읽어 멈춘 판의 기록 한 줄 — 손을 안 불렀고 아무것도 안 바꿨다.
        - ↑ `scan_time.stamp`
        - ↑ `scan_time.now`
      - ↑ `scan_store.append`
      - ↑ `scan_words.summary`
  - `scan_setup.cmd_register` — 스캔을 작업 스케줄러에 건다 — 손을 확인하고, 작업 정의를 지어(보이기만 · 받나만 묻기도) 건다.
    - `usable_hand` — 작업에 굳힐 회사 메일 손 — 찾고, 「list --since」 가 있는 판인가를 묻는다.
      - ↑ `scan_hand.find_hand`
      - ↑ `scan_hand.HandMissing`
      - ↑ `scan_hand.has_since`
    - `scan_task.task_xml` — 등록할 작업 정의(XML) — 바탕의 틀(`task_base.definition`)에 주기 · 손 · 입구 · 켜짐을 채운다.
      - `task_base.definition` — 등록할 작업 정의(XML) — 틀(`DEFINITION`)에 설명 · 주기(분) · 첫 판의 때 · 로그온 뒤 첫 판(분) · 한 판의 시한(분) · 창 없는 파이썬이 받을 인자 · 작업 폴더 · 켜짐을 채운다.
        - `user_id` — 작업을 돌릴 사용자 — 「도메인\이름」(도메인이 없으면 이름).
        - `windowless_python` — 창 없는 파이썬(pythonw.exe) — 지금 도는 파이썬 곁. 없으면 지금 파이썬(창이 뜬다 — 부르는 쪽이 알린다).
      - `run_arguments` — 작업이 부르는 명령의 인자 — 틀(`RUN_ARGUMENTS`)에 입구 · 손 · 전체 주기를 채운다.
    - ↑ `scan_store.scan_dir`
    - ↑ `task_base.windowless_python`
    - `show_register_plan` — 걸지 않고 보이기(`--dry-run`) — 걸면 무엇을 얼마마다 읽나 · 작업 스케줄러에 거는 명령 · 작업 정의.
      - `task_base.shown` — 사람에게 보일 명령줄 — 빈칸이 든 인자는 따옴표에 싼다.
      - `task_base.register_command` — 정의 파일로 작업을 거는 schtasks 명령줄.
    - `task_base.write_xml` — schtasks /XML 이 받는 꼴로 쓴다 — UTF-16(BOM).
    - `validate_task` — 작업 스케줄러가 지은 정의를 받나만 묻는다(등록 안 함) — 받으면 0, 거절하면 그 말과 1.
      - `task_base.ask` — 작업 스케줄러(schtasks) · PowerShell 을 한 번 띄워 답을 받는다 — 출력은 물을 때 `decode` 로 푼다.
        - `Answer` — 작업 스케줄러 · PowerShell 한 번의 답 — 종료 값과 받은 그대로의 표준 출력 · 표준 오류. 글자(`out` · `err`)는 읽는 쪽이 물을 때만 푼다 — 종료 값만 보는 쪽이 못 푸는 출력에 넘어지지 않게.
          - `Answer.out` — 표준 출력을 푼 글자.
            - `decode` — 작업 스케줄러 · PowerShell 의 출력 — UTF-16(BOM · 0 바이트)이나 UTF-8, 아니면 콘솔의 OEM 코드 페이지(한글 윈도는 949)다.
          - `Answer.err` — 표준 오류를 푼 글자.
            - ↑ `decode`
      - `task_base.validate_command` — 작업 스케줄러가 정의를 받나만 묻는 PowerShell 명령줄(등록 안 함) — 정의 파일의 자리는 환경변수 `env` 로 받는다.
      - `task_base.validate_env` — 정의를 받나 묻는 PowerShell 의 환경 — 지금 환경에 정의 파일의 자리를 `env` 라는 이름으로 얹는다.
      - `task_base.accepted` — 정의를 받나 물은 답(`validate_command`)이 「받는다」인가 — 종료 0 이고 끝 글이 `VALIDATE_OK` 다.
    - ↑ `task_base.ask`
    - ↑ `task_base.register_command`
  - `scan_setup.cmd_status` — 걸린 작업 · 마지막 판을 보인다 — 작업 스케줄러에 묻고(`--dry-run` 이면 안 묻는다) 지금 모습을 읽은 뒤 그 줄들을 찍는다.
    - `status_json` — 걸린 작업 · 마지막 판을 프로그램이 읽는 JSON 한 줄로 낸다(`status --json`) — 작업 스케줄러에 묻고(`--dry-run` 이면 안 묻는다) 지금 모습을 읽어 칸을 짓는다.
      - `asked_task` — 작업 스케줄러에 걸린 작업을 묻는다 — (답 · 안 물었으면 None, 걸렸나 · 안 물었으면 None, 걸렸으면 그 정의). 사람의 줄과 JSON 이 이 한 자리로 가른다.
        - ↑ `task_base.ask`
        - `task_base.query_command` — 걸린 작업의 정의를 묻는 schtasks 명령줄.
        - `task_base.read_definition` — 작업 스케줄러가 돌려준 정의(XML)에서 사람에게 말할 것 — 간격 · 켜짐 · 한 번에 하나 · 부르는 인자.
      - `read_state` — 지금 모습 — (읽은 것 · 없으면 None, 못 읽었으면 그 말).
        - ↑ `scan_store.load_state`
        - ↑ `scan_store.scan_dir`
        - ↑ `scan_store.Unreadable`
      - `status_record` — `status --json` 의 한 장 — 꼴 번호 · 사용자 폴더 · 스캔 자리 · 걸린 작업 · 마지막 판.
        - ↑ `scan_store.home`
        - ↑ `scan_store.scan_dir`
        - `task_record` — 걸린 작업의 칸 — 걸렸나(안 물었으면 null) · 걸렸으면 주기(분) · 손 · 부르는 프로그램과 인자 그대로 · 이 스캔의 입구를 부르나. 인자가 거는 꼴이 아니면(손으로 고쳤다) 거기서 읽는 칸은 null 이다.
          - `scan_task.arguments_parts` — 걸린 작업의 인자를 틀의 칸(입구 `scan_py` · 손 `hand` · 전체 주기 `full_every`)으로 되읽는다 — 그 틀로 지은 글이 아니면 None.
          - `scan_task.interval_minutes` — 작업 정의의 간격(ISO 8601 기간)을 분으로 — 기간의 꼴이 아니거나 분으로 안 떨어지면 None.
          - `task_base.same_path` — 두 경로가 같은 자리인가 — 윈도의 대소문자 · 사이 글자(`/` · `\`) · `..` 를 고른 뒤 견준다.
        - `last_run_record` — 마지막 판의 칸 — 시작 · 끝(UTC ISO 8601) · 끝 낱말 · 그 판의 사내 세션 답(`RUN_SESSION_ANSWER` — 판 맺기와 같은 표). 판이 없거나 지금 모습을 못 읽었으면 None.
    - ↑ `asked_task`
    - `task_lines` — 걸린 작업의 줄 — 안 물었으면(`done` 이 None) 물을 명령, 없거나 못 읽었으면 그 답, 걸렸으면 정의(`d`)의 간격 · 켜짐 · 부르는 것.
      - ↑ `task_base.shown`
      - ↑ `task_base.query_command`
    - ↑ `read_state`
    - `last_run_lines` — 마지막 판의 줄 — 판의 때 · 갈래 · 끝, 판이 없으면 못 읽은 말이나 「스캔한 적이 없다」.
      - ↑ `scan_time.seoul`
      - ↑ `scan_time.parse`
  - `scan_setup.cmd_unregister` — 작업을 지운다 — 쌓인 스캔 파일은 그대로다.
    - ↑ `task_base.shown`
    - `task_base.delete_command` — 작업을 지우는 schtasks 명령줄.
    - ↑ `task_base.ask`
  - `scan_setup.cmd_adopt` — 걸린 스캔 작업을 이 홈으로 다시 겨눈다(`adopt` — 설치가 업데이트 때 한 홈에서 부른다) — 걸린 작업이 이 홈의 입구와 이 홈의 회사 메일 손을 안 부르면 그 작업의 주기 · 전체 주기 · 켜짐을 지켜 이 홈의 것으로 다시 건다.
    - ↑ `asked_task`
    - `held_task` — 걸린 정의에서 사람이 고른 것을 거는 꼴로 되읽는다 — 입구 · 손 · 주기 · 전체 주기 · 켜짐. 안 걸렸거나 인자 · 간격이 거는 꼴이 아니면 None.
      - ↑ `scan_task.arguments_parts`
      - ↑ `scan_task.interval_minutes`
      - `task_base.is_enabled` — 걸린 정의(`read_definition`)가 켜진 작업인가 — 작업 스케줄러가 「꺼짐」으로 적은 것만 거짓(칸이 없으면 켜짐이 기본이다).
    - `adopt_skip` — 다시 겨누기를 건너뛸 까닭 — "unregistered" 안 걸렸다 · "foreign" 손으로 고친 꼴이다 · "here" 이미 이 홈의 입구와 손을 부른다 · "" 다시 건다.
      - ↑ `task_base.same_path`
    - ↑ `usable_hand`
    - `reregister` — 지킨 설정으로 이 홈의 입구 · 손을 부르는 작업을 다시 건다 — 정의를 쓰고 작업 스케줄러에 건 뒤 그 줄을 낸다.
      - ↑ `scan_task.task_xml`
      - ↑ `scan_store.scan_dir`
      - ↑ `task_base.write_xml`
      - ↑ `task_base.ask`
      - ↑ `task_base.register_command`

**어디서도 안 닿는 조각** — 표 · 인스턴스를 거쳐 부르거나 아무도 안 부른다.

- `task_base.template_pattern` — `str.format` 틀을 그 틀로 지은 글을 되읽는 정규식으로 — 글자는 그대로, 칸마다 `forms` 의 꼴을 이름 붙은 묶음으로 잡는다.
<!-- /drawn:piece-map -->

## 흐름

### 스캔 한 판 — `scan.py run` → `scan_round`

```
작업 스케줄러 ─▶ scan.py run ─▶ scan_round: 잠금(scan_store.Lock) ─▶ 새 메일 판 | 메일함 전체 판(scan_hand 로 상자마다 끝까지 ·
   hand_lines 로 풀기) ─▶ scan_diff ─▶ 판 맺기 ─▶ events.jsonl · state.json · runs.jsonl
```

- **한 번에 하나** — 잠금을 못 쥐면 그 주기를 건너뛰고 판 기록에 적는다. 잠 · 꺼짐이 남긴 잠금은 그 판의 시각으로 푼다(아래 「잠금」).
  다른 프로그램이 청한 판(`run --wait`)은 건너뛰지 않고 앞 판이 끝나기를 그 시한 안에서 기다렸다 돈다(아래 「잠금」)
- **덜 본 판은 견주지 않는다** — 세션이 끊기거나 시간 상한 · 손 오류로 상자를 다 못 본 판은 바뀜을 안 낸다. 다 본 상자는 `pending.json`
  에 남겨 다음 판이 잇는다. 시간 상한 · 상자 하나의 손 오류로 덜 본 판은 다 본 상자에 처음 보는 메일을 새 메일로 적고(첫 판이
  아니면), 세션이 끊긴 판은 새 메일도 안 적는다. 폴더 목록이 바뀐 판은 이어 볼 상자를 버리고 처음부터 본다. 닿지 못한 상자가 있으면 이음점을 안 옮긴다.
  잇는 기한(`PENDING_MAX_MIN`)을 넘은 상자 그림은 버린다 — 그래서 메일함 전체 주기는 그 기한보다 짧아야 걸린다. 같거나 길면 큰 메일함은
  덜 본 상자가 늘 버려져 끝내 다 못 본다
- **세션이 끊기면 멈춘다** — 그 때를 적고, 그 뒤로는 간격을 두 배씩 늘려(상한 `BACKOFF_MAX_MIN`) 두드린다. 세션 파일이 끊긴 뒤 새로
  쓰였으면(대화에서 EP 로그인을 했다) 다음 주기에 바로 돈다. 스캔 판은 EP 로그인을 하지 않는다 — 그 로그인은 사람이
  대화에서 하거나, 정한 시각의 보고가 제 앞에서 한다
- **손이 없거나 「list --since」 없는 옛 판이면** 그렇다고 적고 멈춘다. 손의 글 꼴이 바뀌었으면 시끄럽게 멈추고, 메일의 글은 안 적는다
- **새 메일 판은 아는 메일을 안 건드린다** — 「이 시각 뒤」 목록을 `--start` 로 끝까지 이어 받아 처음 보는 메일만 더한다. 읽음 · 자리의
  바뀜은 메일함 전체를 본 판만 낸다. 그래서 판 기록의 받은편지함 셈(`inbox_count`)도 전체를 다 본 판에만 싣는다
- **이음점** — 「이 시각 뒤」의 시각은 가장 늦은 메일의 때이고, 지금보다 뒤면 지금이다. 앞날의 때를 단 메일 하나가 이음점을 앞질러
  보내 그 사이 메일을 놓치지 않게 한다
- **손이 무엇을 받나**(`list --since` · `serve`)는 지금 모습에 적어 두고, 손 파일(자리 · 고친 때 · 크기)이 바뀌었을 때만 다시 묻는다
- **손은 판마다 하나** — 손이 `serve` 를 받으면 판 내내 손 하나를 띄워 두고 명령을 하나씩 묻는다. 명령마다 파이썬을 새로 띄우면
  메일함 전체 판 하나에 상자 수의 두 배 넘게 뜬다(상자마다 끝을 확인하는 빈 쪽까지). 상자 차례 · 끝을 가르는 법 · 시간 상한은 그대로
  스캔이 쥐고 손은 물은 것만 답하므로, 메일함에 가는 요청과 그 차례는 명령마다 띄울 때와 같다. 한 상자에서 손이 답 없이 지거나 시한을
  넘기면 그 손을 거두고 그 상자만 덜 본 것으로 적으며, 뒤 상자는 새 손이 읽는다. `serve` 없는 옛 판의 손이면 명령마다 띄운다
- **상자 하나를 끝까지** — 빈 쪽이 와야 끝이다. 덜 찬 쪽을 끝으로 읽지 않는다. 새 줄 없이 이미 받은 줄만 온 쪽은, 마지막에 받은 그 한
  줄뿐이면 끝이고(그 사이 새 메일이 와 한 칸 밀렸다) 그 밖이면 서버가 자리를 안 따른 답이라 끝으로 읽지 않는다(`repeated`)
- **남기는 것** — 지금 모습 `state.json` 은 새 파일에 다 쓴 뒤 바꿔 끼운다. 메일 머리(번호 · 때 · 자리 · 보낸 분 · 받는 분 · 제목 · 안
  읽음 · 첨부 수)만 들고 본문은 안 든다. 오래된 새 메일 · 바뀜 · 판 기록은 하루에 한 번 접는다
- **「없다」와 「못 읽었다」는 다른 답이다** — 스캔 자리의 파일은 한 자리(`scan_store.read_json`)로 읽고, 답은 셋이다: 없다 · 읽었다 · 있는데
  못 읽었다. 같은 파일을 여러 프로세스가 쓴다(스캔 판 · 대화) — 윈도에서는 남이 바꿔 끼우는 그 순간의
  읽기가 지므로, 쓰는 쪽이 기다리는 만큼 기다려 다시 읽는다. 그래도 못 읽은 파일은 빈 것으로 읽어 그 위에 쓰지 않는다 — 판은 지금 모습 ·
  정리 스킬의 잡아 둔 바꿈을 못 읽으면 아무것도 안 쓰고 판 기록에만 적는다(`unreadable`). 글이 깨진 지금 모습만 `.broken` 으로 옮겨 두고 메일함에서 다시 짓는다. 새 파일의 이름은 쓰는 쪽마다 따로다 —
  한 이름이면 두 프로세스가 서로의 새 파일을 비우고 옮긴다

#### 바뀜을 견주는 법 — `scan_diff.py`

- **읽음 바뀜** — 앞 모습의 안 읽음과 지금 목록이 다르면 사람이 메일함에서 바꾼 것이다. 처음 보는 메일이 이미 읽음이고 그 메일이 지난번
  본 때 뒤에 왔으면 사람이 먼저 연 것이다 — 메일은 안 읽음으로 온다
- **옮겨짐 · 사라짐 · 다시 나타남** — 자리가 다르면 옮겨짐, 어느 상자 목록에도 없으면 사라짐, 사라졌던 메일이 다시 서면 다시 나타남이다.
  다 본 모습끼리만 견준다 — 끝까지 못 본 판으로는 사라짐을 안 낸다
- **누가** — 비서가 정리의 바꿈으로 그 자리에 둔 메일은 사람이 옮긴 것이 아니다. 기록을 못 맺은 바꿈(잡아 둔 채 · 결과 모름)이 닿은 메일은
  누가 옮겼는지 모른다 — 모르는 것은 사람이 한 일로 세지 않는다. 앞 모습을 본 때 뒤의 기록만 댄다 — 그 전 기록이 둔 자리로 사람이 나중에
  다시 옮긴 것을 비서의 일로 읽지 않게. 확인 중이던 메일은 그 전 판(`seen_until`)부터 댄다. 때를 못 읽은 기록은 남긴다(사람 탓으로 안
  돌린다)
- **폴더 · 규칙의 바뀜** — 메일함 전체 판은 폴더 목록과 메일 규칙도 견줘 더해짐 · 빠짐 · 바뀜을 내고, 메일처럼 정리의 기록에 대어 누가를
  가른다. 규칙은 앞뒤를 다 읽었을 때만 견준다 — 규칙을 못 받은 판은 앞의 규칙을 그대로 둔다
- **사라진 메일은 `GONE_KEEP_DAYS` 동안 기억한다** — 그 안에 다시 서야 「다시 나타남」이고, 그 뒤에 서면 새 메일이다
- **한 판 안에서 옮겨진 메일** — 두 번 보이면 나중에 읽은 상자가 지금 자리다. 안 보이면 그 메일이 있던 상자보다 먼저 읽은 상자로 옮겨졌을
  수 있다 — 그 상자가 이번 판에서 가장 먼저 읽은 상자가 아니면 사라짐을 다음 판으로 미뤄 가른다(「자리를 확인 중」). 가장 먼저 읽은
  상자라도 한 번에 다 못 받았으면(쪽이 찼거나 둘째 쪽에 줄이 왔다) 미룬다 — 쪽을 받는 사이 앞쪽 메일이 빠지면 뒤 쪽의 첫 줄이 한 칸 당겨져 안 보인다

## 바탕

### 작업 스케줄러의 작업 — `scan_task.py`

작업 하나가 정해진 간격으로 되풀이되고, 로그온한 그 사람의 세션에서만(InteractiveToken · 최소 권한) 창 없이(pythonw) 돈다. 앞 판이 도는
동안 온 주기는 새로 안 띄운다(`IgnoreNew`) — 「한 번에 하나」의 첫 겹이고 스캔의 잠금이 둘째 겹이다. 배터리에서도 돌고, 놓친 주기는 깨어난
뒤 한 번 돌며, 한 판에 시한이 있다. 로그온 뒤 잠시 있다 한 번 돌고, 걸고 나서 잠시 있다 첫 판이 돈다. 손의 자리는 명령줄에 굳힌다 — 작업은 대화의 환경변수를 안 물려받는다. 정의는 UTF-16(BOM)으로 쓴다 —
`schtasks /XML` 이 그 꼴을 받는다. 작업이 부르는 인자는 틀 하나(`RUN_ARGUMENTS`)에서 짓고, `status --json` 은 걸린 작업의 인자를 같은
틀로 되읽어 손 · 입구를 낸다 — 틀 밖의 글(손으로 고친 작업)이면 그 칸은 모른다(null). `validate` 는 작업 스케줄러 COM 에 정의를 넣어 보기만 하고 등록하지 않는다. `unregister` 는 이 작업만 내린다 — 쌓인 파일은 그대로 둔다.

위 칸들을 든 정의의 틀(`DEFINITION` — 작업마다 다른 설명 · 주기 · 시작 때 · 시한 · 인자 · 작업 폴더 · 켜짐만 받는다)과 걸린 정의를 되읽는 몸(틀로 지은 인자를 칸으로 · 켜짐 · 경로 견주기), schtasks · PowerShell 을 띄우고 그 출력을 푸는 몸과 스캔 작업의 로그온 뒤 첫 판(`SCAN_LOGON_DELAY_MIN`)은 곁의 `task_base.py` 가, 곁의 파이썬 손을
창 없이 · UTF-8 로 띄우는 몸은 `proc_base.py` 가, 회사 메일 손의 자리 · 종료 값 · 시한 · 로그인이 사는 스킬 · 사내 세션의 답 낱말(`status --json` 이
낸다) · 세션이 끊겼을 때의 다음 걸음은 `hand_facts.py` 가 든다. 셋은 이 스킬에 원본이 서고, 같은 몸이 필요한 위 스킬은 바이트째 베껴 든다 —
스킬끼리 코드를 싣지 않고, 이 스킬은 누가 베끼는지 모른다. 원본만 고치고 베낀다.

### 잠금 — `scan_store.Lock`

잠금 파일을 새로 만들 수 있는 판(O_EXCL)이 도는 판 하나다. 파일에는 그 판의 열쇠와 시작 시각을 적는다. 잠 · 꺼짐 · 멈춘 판이 남긴 잠금은
그 시각으로 푼다(`LOCK_STALE_S`) — 한 판은 제 상한(`RUN_BUDGET_S`)과 손 한 번의 시한 안에 끝나므로 그보다 오래된 잠금은 도는 판의 것이
아니다. 풀린 판이 나중에 깨어나도 쓰기 전에 `owns` 로 제 열쇠를 다시 보고 물러난다. 못 읽은 잠금(막 지은 판이 아직 안 적었다 · 꺼짐이
빈 잠금을 남겼다)은 그 파일의 고친 때로 낡음을 잰다 — 못 읽었다고 낡은 것으로 풀면 도는 판 둘이 겹친다.

**기다리는 판** — 작업 스케줄러의 판은 앞 판이 돌면 그 주기를 건너뛴다(다음 주기가 곧 온다). 다른 프로그램이 지금 한 판을 청할 때(정한
시각에 보고를 띄우는 쪽이 메일함을 새로 읽으려 할 때)는 건너뛰면 그 청이 헛것이 된다 — 잠든 PC 가 깨면 놓친 주기들이 한 순간에 서서, 시작 때를
어긋나게 걸어 둔 두 작업도 겹친다. 그래서 `run --wait 초` 는 잠금을 못 쥐면 `LOCK_WAIT_POLL_S` 마다 잠들었다 다시 쥐어 보고(`Lock.wait`), 앞 판이
끝나 풀린 첫 사이에 쥐어 돈다. 쥐어 볼 때마다 그 때로 쥐어 잠금의 시작 때는 기다린 뒤의 때다 — 낡음의 셈 · 판의 시간 상한이 기다림만큼
줄지 않는다. 낡은 잠금은 기다림 없이 그 자리에서 푼다(`take` 그대로). 시한이 지나도 못 쥐면 건너뛴 주기로 적고(메모가 기다린 초를 든다)
종료 0 으로 끝난다 — 청한 쪽은 `status --json` 의 마지막 판이 청한 뒤에 시작했나로 돌았나를 가른다. 기다리다 돈 판은 판 기록의 메모가 기다린
초를 든다.

시각은 UTC ISO 8601 로 저장하고(사전순이 시간순이다) 서울(+09:00 고정)로 보인다. `zoneinfo` 는 윈도에서 표준 라이브러리 밖 `tzdata` 가
들어 안 쓴다. 메일함의 때(`xdate`)는 서울 시각 글자다.

## 약속 — 다른 스킬이 기대는 것

같은 사실을 두 자리에 손으로 적지 않는다 — 아래 「원본」이 그 사실을 들고, 기대는 쪽은 거기를 가리키거나 그 명령의 답을 받는다. 스킬은
서로의 코드를 싣지 않는다.

| 무엇 | 원본 | 기대는 쪽 |
|---|---|---|
| 스캔 파일의 자리 · 이름 · 꼴 | `scan_const.py` · `scan_store.py` — 읽는 길은 `reader.py` | 일일 보고 · 메일함 정리 · 대화(파일을 직접 열지 않는다) |
| 프로그램이 읽는 스캔의 지금(`scan.py status --json`) · 앞 판을 기다렸다 도는 한 판(`scan.py run --wait`) | 아래 「status --json · run --wait」 | 정한 시각에 보고를 띄우는 프로그램 |
| 걸린 작업을 이 홈으로 다시 겨누는 문(`scan.py adopt`) — 끝 줄 · 종료 값 | 아래 「다시 겨누기 — adopt」 | 설치(업데이트 때 한 홈에서 부른다) |
| 쌓인 메일의 글을 내는 꼴 — 메일함의 글은 표지(`DATA_OPEN` · `DATA_CLOSE`) 사이에, 따를 지시가 아니라는 머리와 함께 | `reader.py` | 읽는 모델 모두 |
| 회사 메일 손의 명령 · 글 꼴 | 스킬 company-mail 의 `mail.py` 머리말 | `scan_hand.py`(명령 · `serve` 답) · `hand_lines.py`(글 꼴) |
| 정리 스킬의 기록(`TIDY_LOG_FILE` · `TIDY_HELD_FILE`) | 스킬 mailbox-tidy | `scan_diff.py`(읽기만 — 누가를 가른다) |
| 사내 세션 파일의 자리 | 스킬 ep-login(`places.json`) | `session_login.py`(읽기만) |
| 보낸 분 신원(주소 → 회사 · 부서 경로 · 직급 · 직책 · 담당업무)의 꼴과 짓는 법 | 스킬 company-directory 의 `scripts/identity.py`(명령 `lookup` · `pull --unattended`) · 그 스킬 `references/DESIGN.md` 「신원 한 줄의 꼴」 | `scan_identity.py`(명령으로 부른다 · 상태와 지은 때만 본다) · `reader.py`(메일 줄에 붙인다) |

### status --json · run --wait — 프로그램이 기대는 꼴(원본)

정한 시각에 보고를 띄우는 프로그램은 스캔의 코드를 싣지 않고 이 두 명령으로 스캔에 한 판을 청하고 그 판을 읽는다. 칸의 이름과 뜻을 바꾸면
`STATUS_FORMAT` 을 올린다.

| 명령 | 내는 것 | 종료 값 |
|---|---|---|
| `scan.py run --wait <초> [run 의 다른 인자]` | 판 끝 한 줄(사람의 말) — 앞 판의 잠금이 그 초 안에 풀리면 그 뒤 돈 판의 줄, 끝내 안 풀리면 건너뛴 줄. 낡은 잠금은 기다리지 않고 풀고 돈다. `--full-every` 를 안 주면 걸린 작업의 판이 마지막으로 준 전체 주기를 따른다(`full_every_of` — 그것도 없으면 기본) | `run` 그대로 — 0 됐다 · 건너뛰었다 · 1 멈췄다 · 2 인자(초가 1 보다 작다) |
| `scan.py status --json [--dry-run]` | 아래 한 장(JSON 한 줄). `--dry-run` 이면 작업 스케줄러에 안 묻는다 — 걸렸나는 null | 0 |

| 칸 | 꼴 | 뜻 |
|---|---|---|
| `format` | 1 | 꼴 번호(`STATUS_FORMAT`) |
| `home` | 경로 | 사용자 폴더 — 메일 비서 스킬이 함께 쓰는 자리 |
| `folder` | 경로 | 그 안의 스캔 자리(`mailbox-scan`) |
| `task.registered` | 참 · 거짓 · null | 작업 스케줄러에 스캔 작업(`scan_task.TASK_NAME`)이 걸렸나 — 안 물었으면 null |
| `task.every_min` | 수 · null | 걸린 작업의 주기(분) — 안 걸렸거나 간격이 분으로 안 읽히면 null |
| `task.hand` | 경로 · null | 걸린 작업이 명령줄에 굳힌 회사 메일 손 |
| `task.command` · `task.arguments` | 글 · null | 걸린 작업이 부르는 프로그램과 인자 그대로 |
| `task.calls_this_scan` | 참 · 거짓 · null | 걸린 작업이 이 `scan.py`(답하는 그 스캔)를 부르나 — 도구 홈이 여럿이면 그 작업을 건 홈의 스캔만 참이다. 인자가 거는 꼴이 아니면 null |
| `last_run` | 객체 · null | 지금 모습에 적힌 마지막 판 — 판을 한 적이 없거나 지금 모습을 못 읽었으면 null. 건너뛴 주기 · 못 읽어 멈춘 판 · 세션을 기다리는 주기는 지금 모습에 안 적혀 여기 안 선다 |
| `last_run.started` · `.ended` | UTC ISO 8601 | 그 판의 시작(잠금을 쥔 때) · 끝 |
| `last_run.outcome` | 끝 낱말 | `done` · `first` · `partial` · `session` · `hand-missing` · `hand-old` · `hand-error` · `shape`(`scan_const` 의 `RUN_*`) |
| `last_run.session` | `live` · `lost` · null | 그 판이 손에서 받은 사내 세션의 답 — 손이 답한 판은 살았다, 세션 없음으로 멈춘 판은 없다, 그 밖은 null. 판 맺기가 `evidence_of` 가 판의 끝 낱말과 손의 답에서 셈한다 |

### 다시 겨누기 — `adopt`(원본)

작업은 걸 때 한 홈의 입구(`scan.py`)와 회사 메일 손의 절대 경로를 명령줄에 굳힌다. 도구 홈이 여럿 깔린 PC 에서 업데이트가 작업을 건 홈을 못
고쳤거나 그 홈이 걷히면, 작업은 옛 코드를 부르거나 아무것도 못 부른 채 조용히 돈다. `scan.py adopt` 는 걸린 작업을 지금 판의 한 홈으로 다시
겨눈다. 인자는 없다.

- **누가 · 언제** — 설치가 업데이트 때 깐 홈 가운데 정해진 차례의 첫째 한 홈에서만 부르고, 일일 보고의 `clock.py adopt` 보다 **먼저** 부른다.
  홈마다 부르면 홈끼리 서로 다시 겨눈다. 스캔이 먼저 옮겨 앉아야 시계 쪽의 「이 홈의 스캔이 건 작업인가」가 선다
- **이 홈을 부르나** — 걸린 작업의 인자를 거는 틀(`RUN_ARGUMENTS`)로 되읽어, 입구가 이 `scan.py` 이고 손이 이 홈(같은 스킬 뿌리)의 company-mail
  `scripts/mail.py` 일 때만 이 홈을 부른다고 본다. 경로는 윈도의 대소문자 · 사이 글자를 고른 뒤 견준다. 손을 따로 보는 까닭 — 대화에서 걸 때 손은
  도구 홈 차례의 첫 홈에서 찾아, 입구는 이 홈이어도 손은 다른 홈 것일 수 있다
- **지키는 것** — 사람이 고른 주기(정의의 간격) · 전체 주기(`--full-every`) · 켜짐(작업 스케줄러에서 꺼 둔 작업은 끈 채로 다시 건다). 손은 이 홈의
  것으로 새로 정한다
- **안 건드리는 것** — 안 걸린 작업(새로 걸지 않는다 — 스캔은 사람이 대화에서 고른 것이다) · 인자나 간격이 거는 꼴이 아닌 작업(손으로 고친 것이다) ·
  이미 이 홈을 부르는 작업. 여러 번 불러도 같다

| 끝 줄(늘 한 줄 — 부르는 쪽은 마지막 비지 않은 줄을 읽는다) | 언제 | 종료 값 |
|---|---|---|
| `[예약 — 이 홈으로 다시 걸었다: {n}분마다 · 메일함 전체는 {m}분마다{ · 꺼 둔 채로}]` | 다른 홈의 입구나 손을 부르던 작업을 다시 걸었다 | 0 |
| `[예약 — 이미 이 홈의 스캔과 회사 메일 손을 부른다]` | 이미 이 홈을 부른다 | 0 |
| `[예약 — 다시 겨눌 것이 없다: 메일함 스캔이 안 걸려 있다]` | 안 걸렸다 | 0 |
| `[예약 — 건드리지 않았다: 걸린 작업의 명령줄 · 간격이 거는 꼴이 아니다(손으로 고친 작업이다)]` | 인자나 간격이 거는 꼴이 아니다 | 0 |
| `[예약 — 작업 스케줄러가 거절했다: {끝 400자}]` | 다시 걸기를 거절했다 — 작업은 옛 홈을 부르는 채다 | 1 |
| `[예약 — 다시 겨누지 않았다: {까닭}. 다음: …]` | 이 홈의 회사 메일 손이 없거나 「list --since」 없는 옛 판이다 — 작업은 그대로다 | 1 |

## 하지 않는 것

- **메일함을 바꾸지 않는다** — 판은 손의 목록 명령만 부른다. 본문을 받지 않고, 열거나 옮기지 않는다
- **로그인하지 않는다** — 판과 살펴보기는 로그인 화면 · 창 · 탭을 안 연다. 세션이 끊기면 멈추고, 사람이 대화에서 EP 로그인을 하면 다음
  주기에 바로 돈다
- **모델을 부르지 않고 메일을 보내지 않는다** — 판은 손의 읽는 명령과 제 파일만 쓴다
- **신원을 짓지 않는다** — 보낸 분 신원은 주소록 스킬의 신원 명령이 짓고, 스캔은 손이 답한 판의 끝에 그 명령을 불러 주소마다 지금 모습의
  `senders` 에 적을 뿐이다(메일마다 베끼지 않는다). 그 명령이 없거나 · 지거나 · 시한(`IDENTITY_TIMEOUT_S`)을 넘기면 신원만 안 고치고 판 기록의
  `identity_note` 에 적는다 — 판은 그대로 맺는다. 「모름」 은 안 적어 다음 판이 다시 묻는다. 판은 받은 메일의 보낸 분을 다 주고, 다시 짓는 날 ·
  한 부름이 서버에 묻는 몫은 신원 명령이 제 표로 가른다(표로 선 주소는 서버에 안 닿는다). 잠금의 낡음(`LOCK_STALE_S`)은 두 명령의 시한을 든다.
  메일함 전체 판은 미리 받는 조직도 가운데 낡은 것 하나를 받게 한다
- **판단을 하지 않는다** — 청함인가 · 기한 · 누구 차례 · 무엇이 중요한가는 읽는 쪽(모델)의 몫이다. 「지울 만하다 · 죽은 폴더」 같은 딱지도 안
  붙인다 — 셈은 색인이다. 휴지통의 수는 손에 목록 명령이 없어 모른다
- **보고 · 보고 창 · 맡긴 일을 모른다** — 스캔의 코드는 그것들의 이름을 싣지 않는다. 정한 시각의 보고와 맡긴 일의 실행은 다른 스킬이 들고, 이 스킬은
  그쪽이 청할 때 한 판을 돌려 주고 지금 모습을 읽게 내줄 뿐이다

## 검사가 남는 까닭 — 설정 저장소의 `_check/skills/mailbox-scan/check_scan.py`

곁의 회사 메일 손을 가짜 메일함(설정 저장소 `_check/skills/company-mail/check_inbox.py` 의 `FakeDomino` — 회사 메일함 꼴의 흉내는 거기 한 벌이다)에
대어 진짜로 부르고, 비서의 바꿈은 메일함 정리 스킬의 기록(`mailbox-tidy/scripts/journal.py`)을 손의 미리 보기 · 실행 글로 진짜로 맺는다.
여기는 그 가짜 위에 한 판 안의 옮김 · 폴더 줄의 때 꼴만 얹는다. 기대값은 스킬 글과 이 문서의 문장, 판마다 심은 메일에서 낸다.

판정마다 check-design 1 절의 넷(길 · 조용하다 · 다친다 · 다른 무엇도 안 잰다):

| 판정 | 길 | 다친다 |
|---|---|---|
| 첫 판은 바닥만 · 새 메일이 쌓인다 | 판을 고를 때마다(첫 판 · 새 메일 판 · 이음점) | 첫 판이 메일함 전체를 「새 메일」로 내면 보고가 수천 통을 새로 읽고, 새 메일을 놓치면 보고가 메일을 빼먹는다 |
| 메일함을 안 바꾼다(손의 목록 명령만) | 손 부르기를 더할 때마다(본문 받기 · 열기) | 읽음이 바뀌면 사람이 새 메일을 못 알아본다 |
| 사람이 한 일이 바뀜으로 선다 | 견주기를 고칠 때마다 | 보고의 「보셨다」가 틀린다 |
| 비서가 한 일 · 모름 | 정리 스킬의 기록 꼴이 바뀌거나 견주기를 고칠 때 | 비서가 옮긴 것을 사람이 한 일로 센다 |
| 덜 본 판 · 한 판 안의 옮김 | 세션이 끊기거나 보기 하나가 지는 판은 회사에서 늘 난다 | 거짓 「사라짐」이 보고와 정리에 선다 |
| 세션이 끊기면 멈추고 안 두드린다 | 밤마다 세션이 끊길 수 있다 | 사람 없는 밤에 사내 인증을 몇 분마다 두드린다 |
| 겹쳐 안 돈다 · 남은 잠금이 풀린다 | 작업 둘이 같은 때에 돌 수 있고, 잠 · 꺼짐이 잠금을 남긴다 | 겹치면 기록이 엇갈리고, 남은 잠금은 스캔을 영영 멈춘다 |
| 기다리는 판 — 앞 판이 끝나면 돌고, 시한이 지나면 건너뛴 주기로 적고 그만둔다 | 잠든 PC 가 깨면 놓친 스캔 주기와 정한 시각의 청함이 한 순간에 선다 · 판을 쥐는 자리(`cmd_run`)는 판 맺기를 고칠 때 함께 고쳐진다 | 청한 판이 건너뛰어 그날 첫 보고가 메일함을 새로 안 읽은 채 늦거나 빠지고, 시한을 안 지키면 청한 프로그램이 멈춘다 |
| status --json — 칸 이름 · 마지막 판 · 세션 답 | 정한 시각의 보고를 띄우는 프로그램이 다른 스킬에 살아 이 칸 이름에 기댄다 · 걸기 · 보기 손을 고칠 때 함께 고쳐진다 | 칸 하나가 바뀌면 그 프로그램은 오류 없이 「세션 모름」으로 읽어 보고가 날마다 말없이 안 뜬다 |
| 손 하나에 잇달아 묻는다 · 한 상자에서 손이 지면 그 상자만 · 옛 손은 명령마다 | 손이 시한을 넘기거나 지는 판 · `serve` 없는 옛 손이 깔린 PC · 묻는 길을 고칠 때마다 | 손 하나의 고장이 뒤 상자를 다 못 읽게 해 메일함 전체 판이 영영 안 맺고, 옛 손의 PC 는 스캔이 날마다 멈추며, 요청의 꼴이 집에서 못 잰 꼴로 바뀐다 |
| 손의 글 꼴이 바뀌면 멈춘다 | 손의 끝 줄 꼴은 손을 고칠 때마다 바뀔 수 있다 | 잘못 푼 줄이 그럴듯하게 쌓여 보고와 정리에 선다 |
| 읽는 명령이 잘라 낸다 | 읽는 명령을 고칠 때마다 | 보고가 지난 보고 앞의 메일을 다시 새 메일로 말한다 |
| 예약 — 한 번에 하나 · 주기 · 손 | 작업 정의를 고칠 때 | 겹쳐 돌거나 손을 못 찾아 아무것도 안 쌓는다 |
| 예약 — 기본 주기 · 전체 주기의 상한 | 기본값을 고칠 때마다(사용자가 정한 값이다) | 촘촘하면 메일 서버를 하루 내내 두드리고, 전체 주기가 잇는 기한을 넘으면 큰 메일함은 끝내 다 못 본다 |
| 다시 겨누기 — 다른 홈을 부르는 작업은 주기 · 전체 주기를 지켜 이 홈의 입구 · 손으로 다시 걸고, 안 걸린 작업 · 이미 이 홈을 부르는 작업은 안 건드린다(가짜 작업 스케줄러 위에서) | 도구 홈이 여럿 깔린 PC 의 업데이트마다 · 작업을 건 홈이 걷힌 PC | 작업이 옛 홈의 코드를 부르거나 아무것도 못 부른 채 조용히 돌아 메일함이 옛 판으로 쌓이거나 안 쌓이고, 안 걸린 PC 에 걸면 사람이 고르지 않은 스캔이 몇 분마다 메일함을 읽는다 |
| 홀로 선다(표준 라이브러리와 제 폴더뿐 — 예외 없음) | 스킬에 코드를 더할 때마다 — 손 · 다른 스킬의 코드를 싣는 것이 가장 가까운 길이다 | 손이 바뀔 때마다 스킬이 깨진다 |
| 폴더 메일의 때 꼴 — 분까지여도 풀리고, 꼴이 둘 밖이면 멈춘다 | 손의 폴더 줄은 받은편지함과 때 꼴이 다르고, 손을 고칠 때마다 바뀔 수 있다 | 폴더에 바로 든 새 메일이 보고에서 빠지거나, 잘못 푼 때가 그럴듯하게 쌓인다 |
| 정리 신호의 재료 | 읽는 명령 · 판 기록을 고칠 때마다 | 정리 권유가 설 날에 안 서거나 안 설 날에 서서 헛 권유를 날마다 받는다 |
| 보낸 분 신원 — 지은 신원은 주소마다 적혀 메일 줄에 붙고 「모름」 은 안 적힌다 · 신원 명령이 지거나 없어도 판은 됐다로 맺는다(신원 명령은 대역) | 신원 명령은 사내 주소록 · 사람찾기에 닿아 세션 · 앱이 지는 판이 회사에서 난다 · 판 맺기를 고칠 때마다 | 신원 명령 하나가 지면 스캔이 멈춰 새 메일이 안 쌓이고, 「모름」 을 적으면 그 보낸 분은 한 주 동안 신원 없이 보고에 선다 |

모두 사람 없이 돌거나 틀린 셈도 그럴듯하게 서서 조용하고, 다른 무엇도 안 잰다.

**물림 표본만 심기** — `--plant` 는 판정을 안 돌리고 물림 표본이 지금 줄에 다 심기나만 본다(커밋 문 조각 `skill-plant`).

**물림의 꼴** — `--teeth` 는 판정마다 그 판정이 지키는 한 줄을 끈 사본을 지어 같은 판을 돌린다. 먼저 끄지 않은 스크립트로 판을 다 돌려,
거기서 초록이 아닌 판정의 물림은 못 쟀다로 둔다 — 늘 지는 판정 앞에서는 끈 사본도 「잡혔다」로 센다. 사본을 못 심으면(스크립트의 그
줄이 바뀌었다) 그 물림이 빨갛다 — 물림을 다시 지을 일이다.

**여기서 못 재는 것** — `status --json` 의 걸린 작업 칸(주기 · 손 · 이 스캔을 부르나 — 작업 스케줄러에 물어야 서서 이 PC 의 작업에 따라
답이 달라진다. 견줌 도구 `same-bytes` 의 `wait_lock` 이 흉내 낸 작업 스케줄러로 잰다) · 작업 스케줄러가 돌려주는 간격의 꼴(거는 꼴 `PT{분}M` 을
그대로 돌려주나) · 회사 메일함의 한 판 값(요청 수 · 초)과 기본 주기가 회사 서버에 맞나 · 밤을 넘긴 세션 · 작업 스케줄러가 실제로
띄운 판(`--dry-run` 의 정의만 잰다) · 다시 겨누기가 진짜 작업 스케줄러에 거나(가짜 작업 스케줄러 위에서만 잰다 — 꺼 둔 작업을 끈 채 다시 걸고 ·
거절에 1 을 내고 · 손으로 고친 꼴을 두는 갈래는 한 번 확인했다) · 화면이 잠긴 채 · 손의 칸이 늘거나 자리가 바뀐 꼴(끝 줄이 같고 칸만 밀리면 사람용 글로는 못 가른다 —
손의 JSON 꼴이 걷는다) · 손이 「상한에 막혔다」를 내는 판(아주 큰 상자).
